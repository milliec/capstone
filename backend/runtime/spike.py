"""The spike runner, PR 1: a DRY-RUN that plans the first real call and sends nothing.

The measurement spike (sad.md §2 "Measurement spike", EC-R10) is the first time the app calls a real
model. This file is the safe front door to it. In this PR it can only PLAN ONE call: the extractor
on ONE document (SRC-UCILAW by default). It prints what would be sent and what it could cost at
most, and it refuses, with a plain reason, whenever a safety condition is not met.

What this file deliberately does NOT do (the safety design, kept for every later spike PR):
  - Importing this file loads no CrewAI, no `crews.py`, no `agents.py` (T-SPIKE-2 checks it in a
    fresh process). The dry-run (`plan_first_call`) has no path to the network; T-SPIKE-1 blocks
    every socket while it runs.
  - Since spike PR 2b, ONE function can send: `run_first_call`. It imports the real-mode code only
    when it is called, and it is tested against the fake OpenAI only (T-SPIKE-3).
  - It never prints or logs the API key. It says only whether a key is set.
  - The command's `--go` (spike PR 2c) sends nothing until the operator TYPES the document ID.
    Every refusal comes first; closed or piped input counts as "not confirmed".

Why a separate spike database (data/spike.db, git-ignored):
  A real call writes a trace line, and `record_call` (backend/services/trace.py) needs a `runs` row
  for that line to belong to. Spike calls get their own database so they never mix with the demo
  data, and so the 70-call cap (backend/runtime/harness.py) counts spike calls and nothing else.
  The dry-run (PR 1) only READS that file (read-only, and it does not create it). Spike PR 2a adds
  `open_spike_run`, which creates the file and the ONE run row that every spike call belongs to.
  Nothing calls it yet: `--go` stays refused until PR 2b.

Run it (needs AGENTS_MODE=real, SPEND_ACTIVITY=spike, the key and LLM_MODEL_EXTRACT in .env):
    .venv/bin/python -m backend.runtime.spike
"""

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

# These imports are deliberately the "light" ones (they use only sqlite3 and datetime).
# Do NOT import backend.services.runs here: it pulls in the stage code, and with it the code that
# can make a real call. A test (T-SPIKE-2) checks that importing this file loads no CrewAI.
from backend.db.connection import connect, init_db
from backend.domain import sources
from backend.domain.ids import new_run_id
from backend.domain.schemas import ExtractionResult
from backend.runtime import harness, model_settings, prompts
from backend.runtime.wire_schema import wire_schema
from backend.services import FUND_ID, trace
from backend.services.audit import now_utc, write_audit
from backend.settings import ROOT, Settings, SettingsError, load_settings

SPIKE_DB = ROOT / "data" / "spike.db"          # `data/` is git-ignored, so this is never committed
FIRST_CALL_DOCUMENT = "SRC-UCILAW"             # operator's choice (the largest primary document)
STEP, ROLE = "extract_rows", "extract"         # the first live step is ONE Stage A extractor call


class SpikeRefused(Exception):
    """A safety condition for a spike call is not met. The message says which, in plain words."""


@dataclass(frozen=True)
class SpikePlan:
    """Everything the dry-run knows about the first call. Plain data: printing it sends nothing."""
    document_id: str
    document_title: str
    paragraph_count: int
    model: str
    sent_settings: dict            # exactly what would go to the provider besides the prompt
    input_tokens_estimate: int
    worst_case_usd: float          # one request: the whole input, and an answer filling the limit
    worst_case_with_retry_usd: float   # the first request fails but is billed, and so is the retry
    calls_used: int                # real spike calls already in the trace
    call_cap: int                  # EC-R10


def _calls_used(spike_db: Path) -> int:
    """Real spike calls in the spike database. 0 if the file does not exist (it is NOT created).

    Opened read-only (`mode=ro`), so a dry-run cannot change or create anything.
    """
    if not spike_db.exists():
        return 0
    conn = sqlite3.connect(f"file:{spike_db}?mode=ro", uri=True)
    try:
        return harness.real_calls_made(conn, "spike")
    except sqlite3.OperationalError as error:
        if "no such table" in str(error):      # a file with no trace table has made no calls
            return 0
        raise
    finally:
        conn.close()


SPIKE_ACTOR = "spike-runner"       # who the audit log names for what this file does


def open_spike_run(settings: Settings, spike_db: Path = SPIKE_DB) -> str:
    """Create the spike database if needed and return the ID of THE spike run. Sends nothing.

    A trace line must belong to a run (trace.record_call), so every spike call needs a run row.
    There is ONE spike run: the first call creates it, later calls find it again. That way
    `runs.cost_so_far` adds up the whole spike's spend in one place.

    The run is ACTIVE in phase A_RUNNING, which is how the trace knows a call is not "late"
    (trace._is_late). No unit rows and no stage are started: this is not a review.
    """
    # Same two conditions as the dry-run. Checked FIRST, so a wrong setting never creates a file.
    if settings.agents_mode != "real" or settings.spend_activity != "spike":
        raise SpikeRefused("A spike run needs AGENTS_MODE=real and SPEND_ACTIVITY=spike.")
    init_db(spike_db)                     # makes the folder and tables; safe to repeat
    conn = connect(spike_db)
    try:
        # BEGIN IMMEDIATE takes the write lock BEFORE looking, so two commands started together
        # cannot both find "no run" and both create one: the second waits, then finds the first.
        conn.execute("BEGIN IMMEDIATE")
        found = conn.execute(
            "SELECT run_id FROM runs WHERE agents_mode = 'real' AND spend_activity = 'spike' "
            "AND status = 'ACTIVE' ORDER BY rowid LIMIT 1").fetchone()
        if found:
            conn.rollback()
            return found["run_id"]
        run_id = new_run_id(conn, date.today())
        conn.execute(
            """INSERT INTO runs (run_id, fund_id, status, phase, run_version, demo_planted_row,
                                 agents_mode, cost_so_far, started_by, started_at,
                                 demo_fail_step1, stage_attempt, spend_activity)
               VALUES (?, ?, 'ACTIVE', 'A_RUNNING', 1, 0, 'real', 0, ?, ?, 0, 1, 'spike')""",
            (run_id, FUND_ID, SPIKE_ACTOR, now_utc()))
        write_audit(conn, fund_id=FUND_ID, actor=SPIKE_ACTOR, event_type="system", run_id=run_id,
                    subject_id=run_id, reason="Spike run created (B3 spike, EC-R10)")
        conn.commit()
        return run_id
    finally:
        conn.close()


def plan_first_call(settings: Settings, *, document_id: str = FIRST_CALL_DOCUMENT,
                    spike_db: Path = SPIKE_DB) -> SpikePlan:
    """Check every condition, in a fixed order, then describe the one call. Sends nothing.

    Each check raises on failure, so the first problem is the one reported."""
    # 1. Real mode only. In stand-in mode no model is ever called (T-MODE-1).
    if settings.agents_mode != "real":
        raise SpikeRefused("AGENTS_MODE is not 'real'. The spike is the one place real mode is "
                           "meant for; stand-in mode never calls a model.")
    # 2. The spend label must be exactly "spike" (the other four activities are not this runner's).
    if settings.spend_activity != "spike":
        raise SpikeRefused(f"SPEND_ACTIVITY is {settings.spend_activity!r}; the spike runner "
                           "needs it to be 'spike'.")
    # 3 and 4. A model ID for the extractor, and a usable key. Same checks the real call makes.
    call = model_settings.role_settings(settings, ROLE)      # raises ModelNotSet
    model_settings.require_api_key(settings)                 # raises KeyNotSet

    # 5. A PRIMARY document only: the extractor never reads the secondary one (sad.md Stage A).
    documents = {d["id"]: d for d in sources.list_documents()}
    document = documents.get(document_id)
    if document is None or document["type"] != "primary":
        raise SpikeRefused(f"{document_id!r} is not a primary source document; "
                           f"choose one of {[i for i, d in documents.items() if d['type'] == 'primary']}.")

    # 6. The call cap, counted from the trace (EC-R10). At the cap, no further call is planned.
    used = _calls_used(spike_db)
    cap = harness.CALL_CAPS["spike"]
    if used >= cap:
        raise harness.CallCapReached(f"spike: {used} of {cap} real calls used (EC-R10). "
                                     "A further call needs a recorded operator decision.")

    # What the call would carry: this document's paragraphs only, as stages.py passes them.
    own = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()
           if p["document_id"] == document_id}
    inputs = prompts.extractor_inputs(document_id=document_id, document_title=document["title"],
                                      paragraphs=own, recipient_codes=list(sources.list_recipients()))
    rendered = prompts.render(STEP, inputs)
    # The request also carries the strict answer schema (wire_schema.py). Count its text too.
    request_text = "".join(rendered.values()) + json.dumps(wire_schema(ExtractionResult))
    tokens = len(request_text) // model_settings.CHARS_PER_TOKEN + 1   # rough: 4 characters a token

    one_request = model_settings.worst_case_call_cost_usd(settings, ROLE, tokens)
    return SpikePlan(
        document_id=document_id, document_title=document["title"], paragraph_count=len(own),
        model=call.model, sent_settings=call.sent_to_provider(), input_tokens_estimate=tokens,
        worst_case_usd=one_request, worst_case_with_retry_usd=2 * one_request,
        calls_used=used, call_cap=cap)


@dataclass(frozen=True)
class SpikeResult:
    """What one live call did. Plain data, so the command (PR 2c) can print it and a test can read it."""
    run_id: str
    document_id: str
    unit_id: str                   # the trace's name for this call: the document ID, "#", the call number
    ok: bool                       # True: the answer passed the guardrail
    row_count: int                 # rows the extractor returned (0 when not ok)
    failure: str | None            # the reason, in words, when not ok
    lines: tuple                   # one CallRecord per HTTP request sent, in the order sent
    run_cost_usd: float            # the spike run's cost so far, including this call


def run_first_call(settings: Settings, *, document_id: str = FIRST_CALL_DOCUMENT,
                   spike_db: Path = SPIKE_DB) -> SpikeResult:
    """Make the ONE real extractor call the dry-run described, and trace every request it sends.

    ⚠ THIS IS THE FUNCTION THAT CAN SPEND MONEY. Only two things call it: the command's `--go`
    (`_go`, behind a typed confirmation) and the tests (against the fake OpenAI). Keep it so.

    Order, and why: (1) every dry-run check, so a wrong setting, a missing key or model ID, a
    non-primary document or the 70-call cap stops us before anything is created; (2) the spike run
    row; (3) the cost cap, counted from the run's own cost so far PLUS this call's worst case with
    its one retry; (4) the call, through the same real-mode path the app uses (DL-43: once, and
    once more if the first request failed in a way a retry can fix). A bad ANSWER is never asked
    for again (D5). On a failure we report it and stop; nothing here repeats a call.
    """
    plan = plan_first_call(settings, document_id=document_id, spike_db=spike_db)   # (1)
    run_id = open_spike_run(settings, spike_db)                                    # (2)

    # The real-mode code is imported only now, never when this file is imported (T-SPIKE-2).
    from backend.runtime import agents

    conn = connect(spike_db)
    try:
        run = dict(conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone())
        spent = trace.cost_so_far(conn, run_id)
        if spent + plan.worst_case_with_retry_usd > settings.run_cost_cap_usd:      # (3)
            raise SpikeRefused(
                f"US${spent:.4f} is spent and this call could cost up to "
                f"US${plan.worst_case_with_retry_usd:.4f} more: that passes the "
                f"US${settings.run_cost_cap_usd:.2f} cap (CR-017).")

        # The trace refuses two lines with the same (run, step, stage attempt, unit, attempt_n). A
        # review has one unit per document, but the spike calls the same document again and again
        # (after a failure, with a changed prompt). So each CALL is its own unit: SRC-X#1, SRC-X#2.
        (earlier,) = conn.execute(
            "SELECT COUNT(DISTINCT unit_id) FROM trace WHERE run_id = ? AND unit_id LIKE ?",
            (run_id, f"{document_id}#%")).fetchone()
        unit_id = f"{document_id}#{earlier + 1}"

        lines: list = []

        def record(call) -> None:
            """Called by the agent once per HTTP request; writes the trace line at once, so the
            cost is counted even when the request got no answer."""
            lines.append(call)
            trace.record_call(conn, run=run, stage="A", unit_id=unit_id, call=call,
                              spend_activity="spike")

        own = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()
               if p["document_id"] == document_id}
        row_count, failure = 0, None
        try:                                                                       # (4)
            rows = agents.extract_rows(settings, document_id=document_id, paragraphs=own,
                                       recipient_codes=list(sources.list_recipients()),
                                       record=record)
            row_count = len(rows)
        except agents.InvalidOutput as error:
            failure = f"invalid output: {error}"
        except agents.ModelServiceError as error:
            failure = f"model service: {error}"
        return SpikeResult(run_id=run_id, document_id=document_id, unit_id=unit_id,
                           ok=failure is None,
                           row_count=row_count, failure=failure, lines=tuple(lines),
                           run_cost_usd=trace.cost_so_far(conn, run_id))
    finally:
        conn.close()


def format_plan(plan: SpikePlan, *, live: bool = False) -> str:
    """The text the operator reads. It never contains the API key.

    `live` is False for the dry-run (nothing will be sent) and True when `--go` is about to ask
    for the typed confirmation (nothing has been sent YET)."""
    heading = ("SPIKE PLAN: nothing has been sent yet."
               if live else "SPIKE DRY-RUN: nothing was sent, nothing was written, no model was called.")
    closing = ("" if live else
               "To make this call, run it again with --go. You will be asked to type the document ID first.")
    lines = [
        heading,
        "",
        f"Step           : {STEP} (Stage A extractor, ONE call)",
        f"Document       : {plan.document_id} - {plan.document_title} ({plan.paragraph_count} paragraphs)",
        f"Model          : {plan.model}",
        f"Settings sent  : {json.dumps(plan.sent_settings, sort_keys=True)}",
        "API key        : set (never shown)",
        (f"Input estimate : about {plan.input_tokens_estimate} tokens (4 characters a token, "
         "an upper bound)"),
        (f"Worst case     : US${plan.worst_case_usd:.4f} for one request; "
         f"US${plan.worst_case_with_retry_usd:.4f} if the first request is billed and the one retry is too"),
        f"Spike calls    : {plan.calls_used} of {plan.call_cap} used (EC-R10)",
    ]
    if live:
        lines.append(f"Endpoint       : {endpoint_description()}")
    return "\n".join(lines + ["", closing] if closing else lines)


def endpoint_description() -> str:
    """Where the request would go, so a stray OPENAI_BASE_URL in your shell cannot surprise you.

    The OpenAI client reads OPENAI_BASE_URL from the process environment. Only the scheme, host and
    port are shown: a URL can carry a password, and this text must never hold a secret."""
    url = os.environ.get("OPENAI_BASE_URL", "").strip()
    if not url:
        return "OpenAI's default (api.openai.com)"
    parts = urlparse(url)
    port = f":{parts.port}" if parts.port else ""
    return f"{parts.scheme}://{parts.hostname}{port} (set by OPENAI_BASE_URL)"


def format_result(result: SpikeResult) -> str:
    """What the call did, one block per HTTP request, in words. The answer itself is not printed:
    it is in the trace (data/spike.db), where the spike report reads it."""
    lines = ["", "SPIKE RESULT: a request WAS sent.", ""]
    if result.ok:
        lines.append(f"Answer         : VALID ({result.row_count} rows passed the guardrail)")
    else:
        lines.append(f"Answer         : NOT USABLE - {result.failure}")
    lines.append(f"Unit           : {result.unit_id} (run {result.run_id})")
    for call in result.lines:
        got = "no answer" if call.provider_error else "answered"
        lines += [
            "",
            f"Request {call.attempt_n}      : {got}",
            f"  Path         : {call.request_path or '(not recorded)'}",
            f"  Tokens       : {call.tokens_in} in, {call.tokens_out} out",
            f"  Cost         : US${call.cost_usd:.4f}"
            + (" (ESTIMATED, no usage data came back; the worst case was charged)"
               if call.cost_estimated else ""),
            f"  Stop reason  : {call.stop_reason or '(none)'}",
            f"  Model        : asked {call.model}, answered {call.model_returned or '(none)'}",
            f"  Off pinned setting : {'YES - this request did not carry the pinned settings'
                                      if call.off_pinned_setting else 'no'}",
        ]
        if call.provider_error:
            lines.append(f"  Provider error: {call.provider_error}")
        if call.validation_error:
            lines.append(f"  Guardrail    : {call.validation_error}")
    lines += ["", f"Run cost so far: US${result.run_cost_usd:.4f} (cap US$2.50)"]
    if not result.ok:
        lines.append("Stopped. Nothing was repeated except the built-in retry (DL-43).")
    return "\n".join(lines)


# What a normal, expected refusal looks like. Anything else is a bug and is allowed to crash loudly.
REFUSALS = (SpikeRefused, SettingsError, model_settings.ModelNotSet, model_settings.KeyNotSet,
            harness.CallCapReached)


def _go(env, document_id: str, spike_db: Path, out, read_line) -> int:
    """`--go`: every refusal first, then the plan, then a typed confirmation, then the one call.

    Returns 0 for a usable answer, 1 when the call was made but the answer was not usable, 2 when
    nothing was sent (a refusal, or the confirmation was not given)."""
    try:
        settings = load_settings(env)
        plan = plan_first_call(settings, document_id=document_id, spike_db=spike_db)
    except REFUSALS as refusal:
        out(f"REFUSED: {refusal}")                  # before the prompt: never ask to confirm a refusal
        return 2
    out(format_plan(plan, live=True))
    out("")
    out("THIS WILL SEND ONE REAL REQUEST TO THE ENDPOINT ABOVE AND MAY COST MONEY.")
    try:
        typed = read_line(f"To send it, type the document ID ({plan.document_id}) and press Enter; "
                          "anything else cancels: ")
    except (EOFError, OSError):                     # no one to ask (piped input, a script): no
        typed = ""
    if typed.strip() != plan.document_id:
        out("NOT CONFIRMED: nothing was sent.")
        return 2
    out("Sending one request now...")
    try:
        result = run_first_call(settings, document_id=document_id, spike_db=spike_db)
    except REFUSALS as refusal:                     # the cost cap is checked inside the call
        out(f"REFUSED: {refusal}")
        return 2
    out(format_result(result))
    return 0 if result.ok else 1


def main(argv: list[str] | None = None, *, env: dict[str, str] | None = None,
         spike_db: Path = SPIKE_DB, out=print, read_line=input) -> int:
    """The command. Returns 0 for a plan or a usable answer, 1 for a call whose answer was not
    usable, 2 when it refused or was not confirmed. `env`, `spike_db`, `out` and `read_line` exist
    so tests can supply their own values; the real command uses the defaults."""
    parser = argparse.ArgumentParser(prog="python -m backend.runtime.spike", description=__doc__.split("\n")[0])
    parser.add_argument("--document", default=FIRST_CALL_DOCUMENT,
                        help=f"a primary document ID (default {FIRST_CALL_DOCUMENT})")
    parser.add_argument("--go", action="store_true",
                        help="make the real call, after you type the document ID to confirm")
    args = parser.parse_args(argv)

    if args.go:
        return _go(env, args.document, spike_db, out, read_line)
    try:
        plan = plan_first_call(load_settings(env), document_id=args.document, spike_db=spike_db)
    except REFUSALS as refusal:
        out(f"REFUSED: {refusal}")
        return 2
    out(format_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
