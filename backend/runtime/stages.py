"""The stage functions: run one stage of a review in the background (sad.md §2 "Runtime shape").

The backend starts a stage with the run ID and the stage name only; the stage reads everything
else from the database and the configuration. It runs its steps in a fixed order, and when every
unit is done it hands the outputs to the store, which saves them all or nothing and moves the run
to the next gate (rule 9, stage_store.store_stage_outputs). A stage never decides gate status.

B3 step 5 (stand-in part):
  Stage A  load the paragraphs (code) → extract_rows per PRIMARY document → add the demo rule if
           the switch is on (code, CR-029) → quote check per row (code, W-04) → check_conflicts
           per row. Units: one per document ("drafting"), then one per row ("checking_drafts").
  Stage B  load the fund facts (code) → judge_applicability per approved row.
  Stage C  the date engine (B4, backend/domain/dates.py) on every approved rule whose final
           answer is "applies"; a generation error fails the run with "calendar generation".
The units run one after another: in stand-in mode the per-unit pause makes them fill in one by one
(DL-54). A unit whose output fails its guardrail fails the stage with "invalid output" (D5).
Failure demo (DL-52, rule 11): stage A's first unit, first stage attempt, stand-in mode only.

B3 step 6:
  Trace and cost  every agent call writes one trace line, adds its cost to the run and writes an
                  audit entry pointing at it (services/trace.py, CR-017, CR-018).
  Cost cap        before each call: at RUN_COST_CAP_USD or above, the unit fails with "cost cap"
                  and no further call starts. A call already running finishes (CR-017).
  Stage timer     the backend's own timer around the whole stage (rule 6, DL-43): when the stage
                  passes STAGE_TIME_LIMIT_<stage>, the running unit fails with "stage time limit".
                  There is no cancel: a call still running finishes, its output is LATE, goes to
                  the trace only (its cost counts), and nothing from the stage is stored (rule 9).
"""

import json
import sqlite3
import threading
from functools import partial

import yaml

from backend.db.connection import connect
from backend.domain import dates, sources
from backend.domain.fund_facts import load_fund_facts
from backend.domain.quote_check import check_quote
from backend.domain.schemas import Row
from backend.runtime import agents
from backend.services import audit, stage_store, trace
from backend.services import runs as runs_service
from backend.settings import ROOT, Settings

# The planted demo row (CR-029, B7): see the file's own note. Not a stand-in answer: code adds it
# in both modes when the run's switch is on, so it lives in config/, not backend/stand_in/.
DEMO_ROW_FILE = ROOT / "config" / "demo" / "planted-row.yaml"

# What a unit's output can fail with, short of a crash: a guardrail refusal, or a gap in the
# stand-in files. Both end the stage as "invalid output" (failure reason 4).
_UNIT_FAILURES = (agents.InvalidOutput, agents.MissingStandInOutput)


class _StageStopped(Exception):
    """A unit failed and fail_stage has recorded it: stop the stage, store nothing (rule 9)."""


def _approved_rows(conn, run_id: str) -> list[dict]:
    """The rows the specialist approved at G1, in the order they were drafted."""
    rows = conn.execute(
        """SELECT r.* FROM rows r JOIN row_decisions d ON d.row_id = r.row_id
           WHERE r.run_id = ? AND d.decision = 'approve' ORDER BY r.rowid""", (run_id,))
    return [dict(r) for r in rows]


def _row_n(row_id: str) -> int:
    """ROW-RUN-20261117-1-3 → 3."""
    return int(row_id.rsplit("-", 1)[1])


def stage_units(conn, run: dict, stage: str) -> list[tuple[str, str]]:
    """The (unit_id, label) pairs a stage starts with. Stage A's per-row checking units are added
    once the rows exist, so they are not in this list."""
    if stage == "A":   # one per primary document, labelled with its title (DL-53)
        return [(d["id"], d["title"]) for d in sources.list_documents() if d["type"] == "primary"]
    if stage == "B":
        return [(r["row_id"], r["obligation_name"]) for r in _approved_rows(conn, run["run_id"])]
    return [("CALENDAR", "Calendar")]


def _still_current(conn, run: dict, stage: str) -> bool:
    """Is the run still ACTIVE in this stage, on this stage attempt? (The timer may have failed it,
    or the specialist abandoned it, while the previous unit ran.)"""
    now = runs_service.get_run(conn, run["run_id"])
    return (now["status"] == "ACTIVE" and now["phase"] == f"{stage}_RUNNING"
            and now["stage_attempt"] == run["stage_attempt"])


def _run_unit(conn, settings: Settings, run: dict, stage: str, unit_id: str, call):
    """Run one unit: check it may start, call the agent, trace the call, mark the unit.

    `call(record=...)` runs the agent function with the trace recorder (a functools.partial
    with the unit's own inputs already bound, so a loop variable can never leak in). In order:
      1. the stage stopped meanwhile (timer, abandon)  → stop, start no call;
      2. the run reached its cost cap (CR-017)         → fail with "cost cap", start no call;
      3. call the agent; its trace line, cost and audit entry are written as it returns (CR-018);
         a call whose trace line cannot be written counts as failed ("invalid output");
      4. the output came LATE (rule 9, DL-43)          → stop: it is in the trace only;
      5. the output failed its guardrail                → fail with "invalid output" (D5);
      6. otherwise mark the unit done and return the output.
    """
    if not _still_current(conn, run, stage):
        raise _StageStopped
    if trace.cost_so_far(conn, run["run_id"]) >= settings.run_cost_cap_usd:
        stage_store.fail_stage(conn, run, stage, unit_id, "cost cap")
        raise _StageStopped
    stage_store.mark_unit(conn, run, stage, unit_id, "running")

    late = []

    def record(call_record):
        spend = settings.spend_activity if settings.agents_mode == "real" else None
        late.append(trace.record_call(conn, run=run, stage=stage, unit_id=unit_id,
                                      call=call_record, spend_activity=spend))

    try:
        result = call(record=record)
    except agents.DemoFailure:
        # The failure demo (B13a, rule 11): the stand-in extractor failed on purpose.
        stage_store.fail_stage(conn, run, stage, unit_id, "demo failure")
        raise _StageStopped
    except agents.ModelServiceError:
        # The provider gave no answer (timeout, rate limit, error). One attempt until B3 step 7b
        # PR 5 adds DL-43's single retry around the call. Nothing was traced: no answer came.
        stage_store.fail_stage(conn, run, stage, unit_id, "model service")
        raise _StageStopped
    except _UNIT_FAILURES:
        if late and late[0]:
            raise _StageStopped          # late AND invalid: the trace has it; nothing else to do
        stage_store.fail_stage(conn, run, stage, unit_id, "invalid output")
        raise _StageStopped
    except sqlite3.Error:
        # CR-018: the trace line could not be written, so the call counts as failed.
        stage_store.fail_stage(conn, run, stage, unit_id, "invalid output")
        raise _StageStopped
    if late and late[0]:
        raise _StageStopped              # rule 9: arrived after the stage failed or the run ended
    stage_store.mark_unit(conn, run, stage, unit_id, "done")
    return result


# --- Stage A --------------------------------------------------------------------------------

def _demo_row() -> dict:
    """The planted demo row (CR-029), checked against the row schema like any row (it is code's,
    not a model's, so it skips the extractor's guardrail). The quote check and the verifier then
    run on it like on every other row (SOQ-22)."""
    return Row.model_validate(yaml.safe_load(DEMO_ROW_FILE.read_text(encoding="utf-8"))).model_dump()


def _stage_a(conn, settings: Settings, run: dict) -> dict:
    paragraph_list = sources.load_paragraphs()
    paragraphs = {p["paragraph_id"]: p["text"] for p in paragraph_list}
    codes = list(sources.list_recipients())

    documents = stage_units(conn, run, "A")
    stage_store.add_units(conn, run, "A", documents)

    drafted = []
    for index, (document_id, _title) in enumerate(documents):
        # The failure demo (rule 11, CR-033): stage A's FIRST unit, FIRST stage attempt, stand-in
        # mode only, through the stand-in extractor hook. The units run one by one, so units 2 to
        # 5 never start and stay "waiting".
        demo_fail = (index == 0 and bool(run["demo_fail_step1"]) and run["stage_attempt"] == 1
                     and settings.agents_mode == "stand_in")
        own = {pid: text for pid, text in paragraphs.items() if pid.startswith(document_id + "-P")}
        rows = _run_unit(conn, settings, run, "A", document_id, partial(
            agents.extract_rows, settings, document_id=document_id, paragraphs=own,
            recipient_codes=codes, demo_fail=demo_fail))
        drafted += [{**r.model_dump(), "origin": "model"} for r in rows]

    if run["demo_planted_row"]:   # added by code, after the model rows (CR-029)
        drafted.append({**_demo_row(), "origin": "demo"})

    checks = {}
    for n, row in enumerate(drafted, start=1):
        row["row_id"] = f"ROW-{run['run_id']}-{n}"
        # W-04 is code, and its result is stored as code decided it: the verifier is shown it
        # for information and nothing it returns can change it (T-W04-6).
        checks[row["row_id"]] = check_quote(row["quote"], row["source_paragraph_id"], paragraphs)
        row["quote_check"] = checks[row["row_id"]].result
        row["mismatch"] = checks[row["row_id"]].mismatch

    stage_store.add_units(conn, run, "A", [(r["row_id"], r["obligation_name"]) for r in drafted])
    for row in drafted:
        flags = _run_unit(conn, settings, run, "A", row["row_id"], partial(
            agents.check_conflicts, settings, row=row, quote_check=checks[row["row_id"]],
            sources=paragraphs))
        row["flags"] = [f.model_dump() for f in flags]
        row["offset"] = json.dumps(row["offset"])   # stored as JSON text (stage_store)

    return {"paragraphs": paragraph_list, "rows": drafted}


# --- Stage B --------------------------------------------------------------------------------

_JUDGE_FIELDS = ("obligation_name", "frequency", "anchor", "offset", "recipient_code",
                 "applicability_rule", "business_day_rule", "source_paragraph_id", "quote")


def _stage_b(conn, settings: Settings, run: dict) -> dict:
    facts = load_fund_facts(run["fund_id"])
    units = stage_units(conn, run, "B")
    stage_store.add_units(conn, run, "B", units)
    by_id = {r["row_id"]: r for r in _approved_rows(conn, run["run_id"])}
    verdicts = []
    for row_id, _label in units:
        # The judge sees the row's fields and quote only (sad.md "Model and Context Strategy").
        row = {k: by_id[row_id][k] for k in _JUDGE_FIELDS}
        verdict = _run_unit(conn, settings, run, "B", row_id, partial(
            agents.judge_applicability, settings, row=row, fund_facts=facts))
        verdicts.append({
            "verdict_id": f"VER-{run['run_id']}-{_row_n(row_id)}", "row_id": row_id,
            "verdict": verdict.verdict, "reasoning": verdict.reasoning,
            "cited_fact_ids": ", ".join(verdict.cited_fact_ids),
            "missing_information": verdict.missing_information or None})
    return {"verdicts": verdicts}


# --- Stage C (placeholder dates until B4) ---------------------------------------------------

def _stage_c(conn, settings: Settings, run: dict) -> dict:
    """Stage C (W-13, B4): the date engine on every approved rule whose final answer at G2 is
    "applies", with the business-day rule the specialist chose at G1 and the precautionary mark
    when the specialist added a rule AI could not decide. Code only, no model. If generation
    stops (a rule with no business-day rule, two rules giving one entry ID), the unit fails with
    "calendar generation" and nothing is stored (CR-011, rule 9)."""
    units = stage_units(conn, run, "C")
    stage_store.add_units(conn, run, "C", units)
    unit_id = units[0][0]
    stage_store.mark_unit(conn, run, "C", unit_id, "running")
    rules = [dates.Rule(row_id=d["row_id"], source_paragraph_id=d["source_paragraph_id"],
                        recipient_code=d["recipient_code"], anchor=d["anchor"],
                        offset=json.loads(d["offset"]), business_day_rule=d["chosen"],
                        precautionary=d["g2_decision"] == "decide")
             for d in conn.execute(
                 """SELECT r.*, vd.decision AS g2_decision, rd.business_day_rule AS chosen
                    FROM verdict_decisions vd JOIN verdicts v ON v.verdict_id = vd.verdict_id
                    JOIN rows r ON r.row_id = v.row_id
                    JOIN row_decisions rd ON rd.row_id = r.row_id
                    WHERE r.run_id = ? AND vd.final_value = 'applies' ORDER BY r.rowid""",
                 (run["run_id"],))]
    try:
        entries = dates.generate(rules, dates.calendar_from_config(run["fund_id"]))
    except dates.CalendarError as error:
        stage_store.fail_stage(conn, run, "C", unit_id, "calendar generation")
        audit.write_audit(conn, fund_id=run["fund_id"], actor="stage C", event_type="system",
                          run_id=run["run_id"], subject_id=unit_id, reason=str(error))
        conn.commit()
        raise _StageStopped
    stage_store.mark_unit(conn, run, "C", unit_id, "done")
    return {"entries": [vars(e) for e in entries]}


_STAGES = {"A": _stage_a, "B": _stage_b, "C": _stage_c}


def _on_stage_time_limit(settings: Settings, run: dict, stage: str) -> None:
    """The stage timer went off (rule 6). Runs on the timer's own thread, with its own connection.

    Fails the unit that is running (else the next waiting one, else the last one) with
    "stage time limit". fail_stage checks, under the write lock, that the stage is still running;
    if it already finished or failed, nothing changes.
    """
    conn = connect(settings.database_path)
    try:
        unit = conn.execute(
            """SELECT unit_id FROM units WHERE run_id = ? AND stage = ? AND stage_attempt = ?
               ORDER BY CASE status WHEN 'running' THEN 0 WHEN 'waiting' THEN 1 ELSE 2 END,
                        CASE status WHEN 'waiting' THEN rowid ELSE -rowid END
               LIMIT 1""", (run["run_id"], stage, run["stage_attempt"])).fetchone()
        stage_store.fail_stage(conn, run, stage, unit["unit_id"] if unit else stage,
                               "stage time limit")
    finally:
        conn.close()


def run_stage(settings: Settings, run_id: str, stage: str) -> None:
    """Run stage A, B or C for one run. Called as a background task, with only the run ID.

    The stage runs inside the backend's own timer (rule 6, DL-43); see the module note.
    """
    conn = connect(settings.database_path)
    timer = None
    try:
        run = runs_service.get_run(conn, run_id)
        timer = threading.Timer(settings.stage_time_limits[stage], _on_stage_time_limit,
                                args=(settings, run, stage))
        timer.daemon = True     # never keeps the app from shutting down
        timer.start()
        try:
            outputs = _STAGES[stage](conn, settings, run)
        except _StageStopped:
            return   # the failure is recorded (or the run moved on); nothing is stored (rule 9)
        stage_store.store_stage_outputs(
            conn, run_id=run_id, fund_id=run["fund_id"], stage=stage,
            stage_attempt=run["stage_attempt"], outputs=outputs)
    finally:
        if timer is not None:
            timer.cancel()
        conn.close()
