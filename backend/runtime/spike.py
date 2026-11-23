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
  - Spike PR 3, step 1: `--step verify` plans or makes ONE Stage B verifier call on the answer-key
    row of SRC-UCILAW-P3, where the planted conflict C-1 sits (SRC-PRACT-P1 says four months, the
    row says six). Same safety design; the operator types `verify SRC-UCILAW-P3`. The result says
    CAUGHT or MISSED, and counts any internal flag as a false alarm.
  - Spike PR 4 (the verifier bake-off, DL-26), PR 1: `--step verify --case C-1|C-2|I-1|OK-1` plans or
    makes ONE verifier call on one of the four bake-off cases. The operator types the case AND the
    model ID (`verify C-2 gpt-5.6-terra`), so a forgotten model override cannot quietly run the wrong
    candidate. `--row SRC-UCILAW-P3` still works for C-1, as before.
  - Spike PR 4, PR 2: `--tally` is a READ-ONLY summary of data/spike.db (backend/runtime/spike_tally.py):
    per model and per verifier case, the calls, schema-pass, CAUGHT / MISSED, false alarms, tokens, time
    and cost, with the judge's model re-priced at the judge's prices. It sends nothing, needs no key, and
    is refused together with `--go`.
  - Spike PR 3, step 2: `--step judge` plans or makes ONE Stage B judge call on the same answer-key
    row. The operator types `judge SRC-UCILAW-P3`. The result says whether the verdict matches the
    answer key (applies, citing FACT-01).

Why a separate spike database (data/spike.db, git-ignored):
  A real call writes a trace line, and `record_call` (backend/services/trace.py) needs a `runs` row
  for that line to belong to. Spike calls get their own database so they never mix with the demo
  data, and so the 70-call cap (backend/runtime/harness.py) counts spike calls and nothing else.
  The dry-run (PR 1) only READS that file (read-only, and it does not create it). Spike PR 2a adds
  `open_spike_run`, which creates the file and the ONE run row that every spike call belongs to.
  Nothing calls it yet: `--go` stays refused until PR 2b.

Run it (needs AGENTS_MODE=real, SPEND_ACTIVITY=spike, the key and the role's model ID in .env):
    .venv/bin/python -m backend.runtime.spike                   # the extractor, dry-run
    .venv/bin/python -m backend.runtime.spike --step verify     # the verifier, dry-run
    .venv/bin/python -m backend.runtime.spike --step judge      # the judge, dry-run
"""

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

# These imports are deliberately the "light" ones (they use only sqlite3 and datetime).
# Do NOT import backend.services.runs here: it pulls in the stage code, and with it the code that
# can make a real call. A test (T-SPIKE-2) checks that importing this file loads no CrewAI.
from backend.db.connection import connect, init_db
from backend.domain import fund_facts, sources
from backend.domain.ids import new_run_id
from backend.domain.quote_check import check_quote
from backend.domain.schemas import ExtractionResult, Row, Verdict, VerificationResult
from backend.runtime import harness, model_settings, prompts
from backend.runtime.wire_schema import wire_schema
from backend.services import FUND_ID, trace
from backend.services.audit import now_utc, write_audit
from backend.settings import ROOT, Settings, SettingsError, load_settings

SPIKE_DB = ROOT / "data" / "spike.db"          # `data/` is git-ignored, so this is never committed
FIRST_CALL_DOCUMENT = "SRC-UCILAW"             # operator's choice (the largest primary document)
STEP, ROLE = "extract_rows", "extract"         # the first live step is ONE Stage A extractor call
VERIFY_STEP, VERIFY_ROLE = "check_conflicts", "verify"   # spike PR 3: ONE Stage B verifier call
JUDGE_STEP, JUDGE_ROLE = "judge_applicability", "judge"   # spike PR 3, step 2: ONE Stage B judge call
KINDS = ("extract", "verify", "judge")
FIRST_JUDGE_ROW = "SRC-UCILAW-P3"
FIRST_VERIFY_ROW = "SRC-UCILAW-P3"             # the answer-key row that carries the planted conflict C-1

# The planted conflicts the verifier is measured on (expected-obligation-library.md, "planted
# conflicts"). Row's source paragraph -> (conflict ID, the OTHER paragraph a good flag must cite).
# Step 1 plans only C-1; C-2 and I-1 come with the bake-off.
PLANTED_CONFLICTS = {"SRC-UCILAW-P3": ("C-1", "SRC-PRACT-P1")}


@dataclass(frozen=True)
class VerifierCase:
    """One planted test of the verifier (the bake-off, DL-26): which answer-key row it runs on and what a
    good answer looks like. Plain data, so a test can read it. The four cases are the planted flags of
    expected-obligation-library.md section 3."""
    case_id: str                   # C-1, C-2, I-1 or OK-1
    row_id: str                    # the answer-key row's source paragraph; also the trace unit's name
    expects: str                   # "cross_source", "internal" or "nothing"
    other_paragraph: str = ""      # cross_source: the paragraph a good flag cites
    field: str = ""                # internal: the row field a good flag names
    inject: dict | None = None     # row fields this test CHANGES before sending (I-1 only)
    row_note: str = ""             # what the dry-run says about the row, when it is not the plain answer-key row


# Each row id is used by exactly ONE case, so the trace's unit name (the row id, "#", a number) tells
# the tally which case a line belongs to. In particular SRC-UCILAW-P2 in the verifier step is ALWAYS
# the injected copy (I-1): no un-injected verifier call is ever made on it.
CASES = {
    # C-1: SRC-PRACT-P1 says four months; the row (OBL-03) says six.
    "C-1": VerifierCase("C-1", "SRC-UCILAW-P3", "cross_source", other_paragraph="SRC-PRACT-P1"),
    # C-2: SRC-PRACT-P2 anchors on the date of the change; the row (OBL-05) anchors on becoming aware.
    "C-2": VerifierCase("C-2", "SRC-RBELAW-P1", "cross_source", other_paragraph="SRC-PRACT-P2"),
    # I-1: a copy of OBL-02 with the offset changed to 30 days while the quote still says 20. The quote
    # check alone would pass it; only the verifier's internal check can see it.
    "I-1": VerifierCase("I-1", "SRC-UCILAW-P2", "internal", field="offset",
                        inject={"offset": {"unit": "calendar_days", "amount": 30}},
                        row_note="the answer-key row with its OFFSET CHANGED to 30 calendar days; "
                                 "its quote still says 20; injected test I-1"),
    # OK-1: OBL-01, which SRC-PRACT-P3 agrees with. A good answer has NO flag (the false-alarm check).
    "OK-1": VerifierCase("OK-1", "SRC-CSSF15627-P2", "nothing"),
}

# What the answer key says the judge should decide for a row: (verdict, the fact it must cite). The row
# the fund is subject to: "subject to Part II of the Law" is FACT-01, and the fund is subject to it.
EXPECTED_VERDICTS = {"SRC-UCILAW-P3": ("applies", "FACT-01")}
ANSWER_KEY_ROWS = ROOT / "backend" / "stand_in" / "extractor.yaml"    # the answer key's rows, by document


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
    kind: str = "extract"          # "extract" or "verify"
    confirm_text: str = ""         # exactly what the operator must type to send; "" = the document ID
    sends: str = ""                # one line saying what the request carries (shown by `format_plan`)
    case_id: str = ""              # a verifier bake-off case (C-1, C-2, I-1, OK-1); "" for a plain step
    row_note: str = ""             # what to say about the row ("" = the answer-key row, unchanged)


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


def _check_ready(settings: Settings, role: str):
    """Checks 1 to 4, in this order, for the role this call uses. Returns that role's settings."""
    # 1. Real mode only. In stand-in mode no model is ever called (T-MODE-1).
    if settings.agents_mode != "real":
        raise SpikeRefused("AGENTS_MODE is not 'real'. The spike is the one place real mode is "
                           "meant for; stand-in mode never calls a model.")
    # 2. The spend label must be exactly "spike" (the other four activities are not this runner's).
    if settings.spend_activity != "spike":
        raise SpikeRefused(f"SPEND_ACTIVITY is {settings.spend_activity!r}; the spike runner "
                           "needs it to be 'spike'.")
    # 3 and 4. A model ID for THIS role, and a usable key. Same checks the real call makes.
    call = model_settings.role_settings(settings, role)      # raises ModelNotSet
    model_settings.require_api_key(settings)                 # raises KeyNotSet
    return call


def _check_cap(spike_db: Path) -> tuple[int, int]:
    """The call cap, counted from the trace (EC-R10). At the cap, no further call is planned."""
    used = _calls_used(spike_db)
    cap = harness.CALL_CAPS["spike"]
    if used >= cap:
        raise harness.CallCapReached(f"spike: {used} of {cap} real calls used (EC-R10). "
                                     "A further call needs a recorded operator decision.")
    return used, cap


def plan_first_call(settings: Settings, *, document_id: str = FIRST_CALL_DOCUMENT,
                    spike_db: Path = SPIKE_DB) -> SpikePlan:
    """Check every condition, in a fixed order, then describe the one call. Sends nothing.

    Each check raises on failure, so the first problem is the one reported."""
    call = _check_ready(settings, ROLE)                      # checks 1 to 4

    # 5. A PRIMARY document only: the extractor never reads the secondary one (sad.md Stage A).
    documents = {d["id"]: d for d in sources.list_documents()}
    document = documents.get(document_id)
    if document is None or document["type"] != "primary":
        raise SpikeRefused(f"{document_id!r} is not a primary source document; "
                           f"choose one of {[i for i, d in documents.items() if d['type'] == 'primary']}.")

    used, cap = _check_cap(spike_db)                         # check 6

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
        calls_used=used, call_cap=cap, kind="extract", confirm_text=document_id,
        sends="this document's paragraphs and the allowed recipient codes")


def answer_key_row(row_id: str, kind: str = "verify") -> dict:
    """The answer key's row for one source paragraph, as the code would hold it (a `Row` as a dict).

    The verifier and the judge are measured on a FIXED input, so every run and both candidate
    models see the same row (spike plan, 2026-11-22). Each step allows only the rows it plans: the
    verifier those that carry a planted conflict, the judge those the answer key has a verdict for."""
    planned = PLANTED_CONFLICTS if kind == "verify" else EXPECTED_VERDICTS
    label = "verifier" if kind == "verify" else "judge"
    if row_id not in planned:
        raise SpikeRefused(f"{row_id!r} is not a row this step plans a {label} call for; "
                           f"choose one of {sorted(planned)}.")
    return _lookup_row(row_id)


def _lookup_row(row_id: str, inject: dict | None = None) -> dict:
    """The answer key's row for a source paragraph, as a `Row` dict. `inject` changes some fields
    first (the I-1 test); the row is checked as a `Row` AFTER the change, and the answer-key file is
    never altered (the change is made on a copy)."""
    by_document = yaml.safe_load(ANSWER_KEY_ROWS.read_text(encoding="utf-8"))
    for rows in by_document.values():
        for row in rows:
            if row["source_paragraph_id"] == row_id:
                return Row.model_validate({**row, **(inject or {})}).model_dump()
    raise SpikeRefused(f"The answer key has no row for {row_id!r}.")


def case_row(case: VerifierCase) -> dict:
    """The row a bake-off case sends: the answer-key row, with the case's change if it has one."""
    return _lookup_row(case.row_id, case.inject)


def _verifier_inputs(row_id: str, case: VerifierCase | None = None):
    """Everything the verifier call carries, built the way Stage B builds it: the row, the code's
    own quote check, and EVERY loaded paragraph as `sources` (stages.py `_stage_a`)."""
    row = case_row(case) if case else answer_key_row(row_id)
    paragraphs = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    quote_check = check_quote(row["quote"], row["source_paragraph_id"], paragraphs)
    if not quote_check.passed:     # the planned input must be a row whose quote is real
        raise SpikeRefused(f"The answer-key row for {row_id} does not pass the code's quote check "
                           f"({quote_check.mismatch}); the planned input is wrong.")
    types = {d["id"]: d["type"] for d in sources.list_documents()}
    inputs = prompts.verifier_inputs(row=row, quote_check_passed=True, sources=paragraphs,
                                     document_types=types)
    return row, quote_check, paragraphs, inputs


def _case_sends(case: VerifierCase, n_paragraphs: int) -> str:
    """The one line of the dry-run that says what a bake-off case carries and what a good answer is."""
    carries = (f"the row and its quote, the code's quote check (passed), the cited paragraph, and all "
               f"{n_paragraphs} loaded paragraphs (primary and secondary)")
    if case.expects == "cross_source":
        return (f"{carries}. Planted conflict {case.case_id}: {case.other_paragraph} disagrees with "
                f"{case.row_id}. A good answer: a cross-source flag citing {case.other_paragraph}")
    if case.expects == "internal":
        return (f"{carries}. Planted conflict {case.case_id}: the row's {case.field} no longer matches "
                f"its quote, which the quote check cannot see. A good answer: an internal flag "
                f"naming the field {case.field!r}")
    return (f"{carries}. No conflict is planted: the other sources agree with this row. A good answer: "
            "NO flag")


def plan_verifier_call(settings: Settings, *, row_id: str = FIRST_VERIFY_ROW,
                       spike_db: Path = SPIKE_DB, case: VerifierCase | None = None) -> SpikePlan:
    """The same checks as the extractor's plan (for the VERIFIER's model), then describe the one
    verifier call on one answer-key row. Sends nothing. With a bake-off `case` (C-1, C-2, I-1 or
    OK-1) the row, the words to type and the expected answer come from the case."""
    call = _check_ready(settings, VERIFY_ROLE)               # checks 1 to 4, for the verify role
    if case:
        row_id = case.row_id
    row, _quote_check, paragraphs, inputs = _verifier_inputs(row_id, case)   # check 5: a planned row
    used, cap = _check_cap(spike_db)                         # check 6

    rendered = prompts.render(VERIFY_STEP, inputs)
    request_text = "".join(rendered.values()) + json.dumps(wire_schema(VerificationResult))
    tokens = len(request_text) // model_settings.CHARS_PER_TOKEN + 1
    one_request = model_settings.worst_case_call_cost_usd(settings, VERIFY_ROLE, tokens)
    if case:
        # The typed words name the case AND the model, so the operator cannot run the wrong candidate
        # by forgetting to override LLM_MODEL_VERIFY on the command line.
        return SpikePlan(
            document_id=row_id, document_title=row["obligation_name"],
            paragraph_count=len(paragraphs), model=call.model, sent_settings=call.sent_to_provider(),
            input_tokens_estimate=tokens, worst_case_usd=one_request,
            worst_case_with_retry_usd=2 * one_request, calls_used=used, call_cap=cap, kind="verify",
            confirm_text=f"verify {case.case_id} {call.model}",
            sends=_case_sends(case, len(paragraphs)), case_id=case.case_id, row_note=case.row_note)
    conflict, other = PLANTED_CONFLICTS[row_id]
    return SpikePlan(
        document_id=row_id, document_title=row["obligation_name"], paragraph_count=len(paragraphs),
        model=call.model, sent_settings=call.sent_to_provider(), input_tokens_estimate=tokens,
        worst_case_usd=one_request, worst_case_with_retry_usd=2 * one_request,
        calls_used=used, call_cap=cap, kind="verify", confirm_text=f"verify {row_id}",
        sends=(f"the row and its quote, the code's quote check (passed), the cited paragraph, and "
               f"all {len(paragraphs)} loaded paragraphs (primary and secondary). Planted conflict "
               f"{conflict}: {other} disagrees with {row_id}"))


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
    kind: str = "extract"          # "extract" or "verify"
    assessment: tuple = ()         # for a verifier call: CAUGHT / MISSED, false alarms (text lines)
    case_id: str = ""              # the verifier bake-off case, "" for a plain step


def _judge_inputs(row_id: str):
    """Everything the judge call carries, built the way Stage B builds it: the row as approved and the
    fund's facts (ID, fact, value) and events (ID, description). Never the "Decides" column, flags,
    G1 reasons or other verdicts (`prompts.judge_inputs`)."""
    row = answer_key_row(row_id, "judge")
    facts = fund_facts.load_fund_facts()
    return row, facts, prompts.judge_inputs(row=row, fund_facts=facts)


def plan_judge_call(settings: Settings, *, row_id: str = FIRST_JUDGE_ROW,
                    spike_db: Path = SPIKE_DB) -> SpikePlan:
    """The same checks as the other plans (for the JUDGE's model), then describe the one judge call
    on one answer-key row. Sends nothing."""
    call = _check_ready(settings, JUDGE_ROLE)                # checks 1 to 4, for the judge role
    row, facts, inputs = _judge_inputs(row_id)               # check 5: a planned row
    used, cap = _check_cap(spike_db)                         # check 6

    rendered = prompts.render(JUDGE_STEP, inputs)
    request_text = "".join(rendered.values()) + json.dumps(wire_schema(Verdict))
    tokens = len(request_text) // model_settings.CHARS_PER_TOKEN + 1
    one_request = model_settings.worst_case_call_cost_usd(settings, JUDGE_ROLE, tokens)
    verdict, fact = EXPECTED_VERDICTS[row_id]
    return SpikePlan(
        document_id=row_id, document_title=row["obligation_name"],
        paragraph_count=len(facts["facts"]), model=call.model, sent_settings=call.sent_to_provider(),
        input_tokens_estimate=tokens, worst_case_usd=one_request,
        worst_case_with_retry_usd=2 * one_request, calls_used=used, call_cap=cap, kind="judge",
        confirm_text=f"judge {row_id}",
        sends=(f"the approved row, {len(facts['facts'])} fund facts (ID, fact, value) and "
               f"{len(facts['events'])} event(s) (ID, description). Not the 'Decides' column, flags "
               f"or other verdicts. The answer key says: {verdict}, citing {fact}"))


def _plan_for(settings: Settings, kind: str, target: str, spike_db: Path,
              case_id: str = "") -> SpikePlan:
    """The dry-run plan for one kind of call. Every refusal comes from here, before anything is sent."""
    if kind == "verify":
        return plan_verifier_call(settings, row_id=target, spike_db=spike_db,
                                  case=CASES[case_id] if case_id else None)
    if kind == "judge":
        return plan_judge_call(settings, row_id=target, spike_db=spike_db)
    return plan_first_call(settings, document_id=target, spike_db=spike_db)


def assess_judgement(row_id: str, verdict) -> tuple[str, ...]:
    """What a judge's verdict says against the answer key, in words (plan, "Pass or fail").

    CORRECT: the verdict is the answer key's AND it cites the fact the key names. WRONG: anything else
    that passed the guardrail. A wrong verdict is a finding about the judge, not a mechanical failure."""
    expected, fact = EXPECTED_VERDICTS[row_id]
    cited = list(verdict.cited_fact_ids)
    right = verdict.verdict == expected and fact in cited
    lines = [f"Answer key       : {expected}, citing {fact}",
             f"Judge's verdict  : {verdict.verdict}, citing {', '.join(cited)} - "
             + ("CORRECT" if right else f"WRONG (the answer key says {expected}, citing {fact})")]
    if verdict.missing_information.strip():
        lines.append(f"Missing info     : {' '.join(verdict.missing_information.split())[:240]}")
    lines.append(f"Judge said       : {' '.join(verdict.reasoning.split())[:240]}")
    return tuple(lines)


def assess_verification(row_id: str, flags) -> tuple[str, ...]:
    """The C-1 assessment, kept under its first name: the planted conflict of one row (`--row`)."""
    return assess_case(CASES[PLANTED_CONFLICTS[row_id][0]], flags)


@dataclass(frozen=True)
class CaseOutcome:
    """What a verifier's flags amount to for one bake-off case. The ONE place that decides it: the live
    printout (`assess_case`) and the read-only tally (`spike_tally`) both read it, so they cannot disagree."""
    good: bool             # planted cases: CAUGHT. OK-1: CLEAN (no flag)
    false_alarms: list     # flags that are false alarms (see `classify_case`)
    extra: list            # flags of the other kind, which a person should read (not judged)


def classify_case(case: VerifierCase, flags) -> CaseOutcome:
    """Decide CAUGHT / MISSED / CLEAN / FALSE ALARM for one case. Plain code, no model.

    C-1 and C-2 (cross-source): good when a cross-source flag cites the other paragraph; any internal
    flag is a false alarm, because the answer-key row's fields match its quote.
    I-1 (internal): good when an internal flag names the changed field; an internal flag on another
    field is a false alarm. OK-1 (no conflict): good when there is no flag; any flag is a false alarm."""
    cross = [f for f in flags if f.flag_type == "cross_source"]
    internal = [f for f in flags if f.flag_type == "internal"]
    if case.expects == "nothing":
        return CaseOutcome(good=not flags, false_alarms=list(flags), extra=[])
    if case.expects == "cross_source":
        return CaseOutcome(
            good=any(f.other_paragraph_id == case.other_paragraph for f in cross),
            false_alarms=internal,
            extra=[f for f in cross if f.other_paragraph_id != case.other_paragraph])
    return CaseOutcome(
        good=any(f.field == case.field for f in internal),
        false_alarms=[f for f in internal if f.field != case.field],
        extra=cross)


def assess_case(case: VerifierCase, flags) -> tuple[str, ...]:
    """What a verifier's flags say about one bake-off case, in words (plan, "Pass or fail").

    MISSED means the verifier did not see a planted conflict (DL-26: a miss in any run switches the
    verifier to the reasoning model). A flag of another kind is not judged here: it is listed so that
    a person reads it. The decision itself is `classify_case`."""
    outcome = classify_case(case, flags)
    lines: list[str] = []
    if case.expects == "nothing":
        lines.append("Correct row      : CLEAN (no flag)" if outcome.good else
                     f"Correct row      : FALSE ALARM ({len(flags)} flag(s) on a row the answer key "
                     "says needs none)")
    else:
        if case.expects == "cross_source":
            what = f"a cross-source flag cites {case.other_paragraph}"
            missed = f"no cross-source flag cites {case.other_paragraph}"
            fa_note, extra_note = "on a row whose fields match its quote", "not the planted conflict"
        else:
            what = f"an internal flag names the field {case.field!r}"
            missed = f"no internal flag names the field {case.field!r}"
            fa_note, extra_note = "on a field that matches its quote", "not the injected conflict"
        lines.append(f"Planted {case.case_id}   : CAUGHT ({what})" if outcome.good else
                     f"Planted {case.case_id}   : MISSED ({missed}). DL-26: a miss in any run "
                     "switches the verifier to the reasoning model")
        if outcome.false_alarms:
            lines.append(f"False alarms     : {len(outcome.false_alarms)} internal flag(s) {fa_note}: "
                         + "; ".join(f"{f.field}: row says {f.row_value!r}, quote says {f.quote_says!r}"
                                     for f in outcome.false_alarms))
        else:
            lines.append("False alarms     : none")
        if outcome.extra:
            lines.append("Other flags      : " + "; ".join(
                f"{f.flag_type.replace('_', '-')} on {f.other_paragraph_id or f.field} "
                f"({extra_note}: read it)" for f in outcome.extra))
    for flag in flags:
        lines.append(f"Verifier said    : [{flag.flag_type}] {' '.join(flag.explanation.split())[:240]}")
    return tuple(lines)


def run_first_call(settings: Settings, *, document_id: str = FIRST_CALL_DOCUMENT,
                   spike_db: Path = SPIKE_DB) -> SpikeResult:
    """Make the ONE real extractor call the dry-run described (see `run_call`)."""
    return run_call(settings, kind="extract", target=document_id, spike_db=spike_db)


def run_call(settings: Settings, *, kind: str, target: str, spike_db: Path = SPIKE_DB,
             case_id: str = "") -> SpikeResult:
    """Make the ONE real call the dry-run described, and trace every request it sends.
    `kind` is "extract" (target: a primary document ID), "verify" or "judge" (target: an answer-key
    row's source paragraph ID). `case_id` (verify only) picks a bake-off case; `target` is then that
    case's row.

    ⚠ THIS IS THE FUNCTION THAT CAN SPEND MONEY. Only two things call it: the command's `--go`
    (`_go`, behind a typed confirmation) and the tests (against the fake OpenAI). Keep it so.

    Order, and why: (1) every dry-run check, so a wrong setting, a missing key or model ID, a
    non-primary document or the 70-call cap stops us before anything is created; (2) the spike run
    row; (3) the cost cap, counted from the run's own cost so far PLUS this call's worst case with
    its one retry; (4) the call, through the same real-mode path the app uses (DL-43: once, and
    once more if the first request failed in a way a retry can fix). A bad ANSWER is never asked
    for again (D5). On a failure we report it and stop; nothing here repeats a call.
    """
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, not {kind!r}")
    document_id = target
    plan = _plan_for(settings, kind, target, spike_db, case_id)                     # (1)
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
        step = {"extract": STEP, "verify": VERIFY_STEP, "judge": JUDGE_STEP}[kind]
        (earlier,) = conn.execute(
            "SELECT COUNT(DISTINCT unit_id) FROM trace WHERE run_id = ? AND step = ? "
            "AND unit_id LIKE ?", (run_id, step, f"{document_id}#%")).fetchone()
        unit_id = f"{document_id}#{earlier + 1}"

        lines: list = []

        def record(call) -> None:
            """Called by the agent once per HTTP request; writes the trace line at once, so the
            cost is counted even when the request got no answer."""
            lines.append(call)
            # Stage "A" for EVERY spike step: the spike run stays ACTIVE in A_RUNNING, and the
            # trace judges a line "late" by comparing the line's stage with the run's phase.
            trace.record_call(conn, run=run, stage="A", unit_id=unit_id, call=call,
                              spend_activity="spike")

        row_count, failure, assessment = 0, None, ()
        try:                                                                       # (4)
            if kind == "verify":
                case = CASES[case_id] if case_id else None
                row, quote_check, paragraphs, _inputs = _verifier_inputs(document_id, case)
                flags = agents.check_conflicts(settings, row=row, quote_check=quote_check,
                                               sources=paragraphs, record=record)
                row_count = len(flags)
                assessment = (assess_case(case, flags) if case
                              else assess_verification(document_id, flags))
            elif kind == "judge":
                row, facts, _inputs = _judge_inputs(document_id)
                verdict = agents.judge_applicability(settings, row=row, fund_facts=facts,
                                                     record=record)
                row_count = 1
                assessment = assess_judgement(document_id, verdict)
            else:
                own = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()
                       if p["document_id"] == document_id}
                rows = agents.extract_rows(settings, document_id=document_id, paragraphs=own,
                                           recipient_codes=list(sources.list_recipients()),
                                           record=record)
                row_count = len(rows)
        except agents.InvalidOutput as error:
            failure = f"invalid output: {error}"
        except agents.ModelServiceError as error:
            failure = f"model service: {error}"
        return SpikeResult(run_id=run_id, document_id=document_id, unit_id=unit_id,
                           ok=failure is None, row_count=row_count, failure=failure,
                           lines=tuple(lines), run_cost_usd=trace.cost_so_far(conn, run_id),
                           kind=kind, assessment=assessment, case_id=case_id)
    finally:
        conn.close()


def format_plan(plan: SpikePlan, *, live: bool = False) -> str:
    """The text the operator reads. It never contains the API key.

    `live` is False for the dry-run (nothing will be sent) and True when `--go` is about to ask
    for the typed confirmation (nothing has been sent YET)."""
    heading = ("SPIKE PLAN: nothing has been sent yet."
               if live else "SPIKE DRY-RUN: nothing was sent, nothing was written, no model was called.")
    verify = plan.kind in ("verify", "judge")       # both are measured on a fixed answer-key row
    confirm = plan.confirm_text or plan.document_id
    closing = ("" if live else
               (f"To make this call, run it again with --step {plan.kind}"
                + (f" --case {plan.case_id}" if plan.case_id else "")
                + f" --go. You will be asked to type exactly: {confirm}") if verify else
               "To make this call, run it again with --go. You will be asked to type the document ID first.")
    if verify:
        label = (f"{VERIFY_STEP} (Stage B verifier, ONE call)" if plan.kind == "verify"
                 else f"{JUDGE_STEP} (Stage B judge, ONE call)")
        what = [f"Step           : {label}",
                *([f"Case           : {plan.case_id}"] if plan.case_id else []),
                (f"Row            : {plan.document_id} - {plan.document_title} "
                 f"({plan.row_note or 'the answer-key row; the SAME input every run'})")]
    else:
        what = [f"Step           : {STEP} (Stage A extractor, ONE call)",
                (f"Document       : {plan.document_id} - {plan.document_title} "
                 f"({plan.paragraph_count} paragraphs)")]
    lines = [
        heading,
        "",
        *what,
        *([f"Sends          : {plan.sends}"] if verify else []),
        f"Model          : {plan.model}",
        f"Settings sent  : {json.dumps(plan.sent_settings, sort_keys=True)}",
        *([("Temperature    : NOT sent (DL-40 names none for the verifier; operator decision, 2026-11-22)"
            if plan.kind == "verify" else
            "Temperature    : NOT sent (DL-40: the judge runs with no temperature)")]
          if "temperature" not in plan.sent_settings else []),
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
    noun = {"extract": "rows", "verify": "flag(s)", "judge": "verdict(s)"}[result.kind]
    if result.ok:
        lines.append(f"Answer         : VALID ({result.row_count} {noun} passed the guardrail)")
    else:
        lines.append(f"Answer         : NOT USABLE - {result.failure}")
    if result.case_id:
        lines.append(f"Case           : {result.case_id} ({result.document_id})")
    lines.append(f"Unit           : {result.unit_id} (run {result.run_id})")
    lines += list(result.assessment)
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


def _go(env, kind: str, target: str, spike_db: Path, out, read_line, case_id: str = "") -> int:
    """`--go`: every refusal first, then the plan, then a typed confirmation, then the one call.

    Returns 0 for a usable answer, 1 when the call was made but the answer was not usable, 2 when
    nothing was sent (a refusal, or the confirmation was not given)."""
    try:
        settings = load_settings(env)
        plan = _plan_for(settings, kind, target, spike_db, case_id)
    except REFUSALS as refusal:
        out(f"REFUSED: {refusal}")                  # before the prompt: never ask to confirm a refusal
        return 2
    out(format_plan(plan, live=True))
    out("")
    out("THIS WILL SEND ONE REAL REQUEST TO THE ENDPOINT ABOVE AND MAY COST MONEY.")
    confirm = plan.confirm_text or plan.document_id
    ask = (f"To send it, type exactly '{confirm}' and press Enter; anything else cancels: "
           if kind != "extract" else
           f"To send it, type the document ID ({plan.document_id}) and press Enter; "
           "anything else cancels: ")
    try:
        typed = read_line(ask)
    except (EOFError, OSError):                     # no one to ask (piped input, a script): no
        typed = ""
    if typed.strip() != confirm:
        out("NOT CONFIRMED: nothing was sent.")
        return 2
    out("Sending one request now...")
    try:
        result = run_call(settings, kind=kind, target=target, spike_db=spike_db, case_id=case_id)
    except REFUSALS as refusal:                     # the cost cap is checked inside the call
        out(f"REFUSED: {refusal}")
        return 2
    out(format_result(result))
    return 0 if result.ok else 1


def _tally(env, spike_db: Path, out, exclude_text: str) -> int:
    """`--tally`: read the spike database and print the summary. Sends nothing, writes nothing."""
    from backend.runtime import spike_tally  # only `--tally` needs it
    role_models, note = {}, ""
    try:
        role_models = dict(load_settings(env).llm_models)
    except SettingsError as error:                   # a read-only summary should still work
        note = f"the role models in .env could not be read ({error}); no line was priced for another model"
    exclude = {unit.strip() for unit in exclude_text.split(",") if unit.strip()}
    tally = spike_tally.collect(spike_db, role_models, exclude)
    tally.note = note
    out(spike_tally.format_tally(tally))
    return 0


def main(argv: list[str] | None = None, *, env: dict[str, str] | None = None,
         spike_db: Path = SPIKE_DB, out=print, read_line=input) -> int:
    """The command. Returns 0 for a plan or a usable answer, 1 for a call whose answer was not
    usable, 2 when it refused or was not confirmed. `env`, `spike_db`, `out` and `read_line` exist
    so tests can supply their own values; the real command uses the defaults."""
    parser = argparse.ArgumentParser(prog="python -m backend.runtime.spike", description=__doc__.split("\n")[0])
    parser.add_argument("--step", choices=KINDS, default="extract",
                        help="which call: the Stage A extractor (default), the Stage B verifier "
                             "or the Stage B judge")
    parser.add_argument("--document", default=FIRST_CALL_DOCUMENT,
                        help=f"extract only: a primary document ID (default {FIRST_CALL_DOCUMENT})")
    parser.add_argument("--row", default=None,
                        help=f"verify and judge: the answer-key row's source paragraph (default "
                             f"{FIRST_VERIFY_ROW}). For the verifier this is the first call's C-1 "
                             "only; the bake-off uses --case")
    parser.add_argument("--case", choices=sorted(CASES), default=None,
                        help="verify only: a verifier bake-off case (DL-26): C-1 and C-2 (a planted "
                             "conflict between sources), I-1 (an injected conflict inside the row) "
                             "or OK-1 (a row that should get no flag)")
    parser.add_argument("--go", action="store_true",
                        help="make the real call, after you type the confirmation shown")
    parser.add_argument("--tally", action="store_true",
                        help="READ-ONLY: summarise data/spike.db (calls, schema-pass, CAUGHT/MISSED, "
                             "false alarms, tokens, time, cost per model and case). Sends nothing")
    parser.add_argument("--exclude", default="",
                        help="with --tally: verifier units to leave out of the bake-off counts, comma "
                             "separated, for example SRC-UCILAW-P3#1 (a call sent before a fix)")
    args = parser.parse_args(argv)

    if args.tally:
        if args.go:
            out("REFUSED: --tally only reads; it cannot be combined with --go.")
            return 2
        return _tally(env, spike_db, out, args.exclude)
    if args.exclude:
        out("REFUSED: --exclude is only for --tally.")
        return 2

    case_id = args.case or ""
    if case_id and args.step != "verify":
        out("REFUSED: --case is only for --step verify (the verifier bake-off).")
        return 2
    if case_id and args.row:
        out("REFUSED: give --case or --row, not both: a case names its own row.")
        return 2
    if case_id:
        target = CASES[case_id].row_id
    elif args.step == "extract":
        target = args.document
    else:
        target = args.row or FIRST_VERIFY_ROW
    if args.go:
        return _go(env, args.step, target, spike_db, out, read_line, case_id)
    try:
        settings = load_settings(env)
        plan = _plan_for(settings, args.step, target, spike_db, case_id)
    except REFUSALS as refusal:
        out(f"REFUSED: {refusal}")
        return 2
    out(format_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
