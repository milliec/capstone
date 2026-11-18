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
  Stage C  STILL PLACEHOLDER DATES until B4 (the date engine): one entry per approved rule whose
           final answer is "applies", for rules 1, 2 and 4 only (backend/stand_in/shell_data.py).
The units run one after another: in stand-in mode the per-unit pause makes them fill in one by one
(DL-54). A unit whose output fails its guardrail fails the stage with "invalid output" (D5).
Failure demo (DL-52, rule 11): stage A's first unit, first stage attempt, stand-in mode only.

Not here yet (B3 step 6): the stage timer (DL-43), the trace and the cost count (CR-017, CR-018).
"""

import json

import yaml

from backend.db.connection import connect
from backend.domain import sources
from backend.domain.fund_facts import load_fund_facts
from backend.domain.quote_check import check_quote
from backend.domain.schemas import Row
from backend.runtime import agents
from backend.services import runs as runs_service
from backend.services import stage_store
from backend.settings import Settings
from backend.stand_in import shell_data

# The temporary demo rule until B7 (operator, 2026-11-18): see the file's own note.
DEMO_ROW_FILE = agents.STAND_IN_DIR / "demo_row_temporary.yaml"

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


def _run_unit(conn, run: dict, stage: str, unit_id: str, work):
    """Mark a unit running, do its work, mark it done. A failed unit fails the stage."""
    stage_store.mark_unit(conn, run, stage, unit_id, "running")
    try:
        result = work()
    except _UNIT_FAILURES:
        stage_store.fail_stage(conn, run, stage, unit_id, "invalid output")
        raise _StageStopped
    stage_store.mark_unit(conn, run, stage, unit_id, "done")
    return result


# --- Stage A --------------------------------------------------------------------------------

def _demo_row() -> dict:
    """The temporary demo rule, checked against the row schema like any row (it is code's, not a
    model's, so it skips the extractor's guardrail)."""
    return Row.model_validate(yaml.safe_load(DEMO_ROW_FILE.read_text(encoding="utf-8"))).model_dump()


def _stage_a(conn, settings: Settings, run: dict) -> dict:
    paragraph_list = sources.load_paragraphs()
    paragraphs = {p["paragraph_id"]: p["text"] for p in paragraph_list}
    codes = list(sources.list_recipients())

    documents = stage_units(conn, run, "A")
    stage_store.add_units(conn, run, "A", documents)

    drafted = []
    for index, (document_id, _title) in enumerate(documents):
        if index == 0 and run["demo_fail_step1"] and run["stage_attempt"] == 1 \
                and settings.agents_mode == "stand_in":
            stage_store.mark_unit(conn, run, "A", document_id, "running")
            agents.unit_pause(settings)  # so unit 1 shows 'running' for a moment first
            stage_store.fail_stage(conn, run, "A", document_id, "demo failure")
            raise _StageStopped
        own = {pid: text for pid, text in paragraphs.items() if pid.startswith(document_id + "-P")}
        rows = _run_unit(conn, run, "A", document_id, lambda: agents.extract_rows(
            settings, document_id=document_id, paragraphs=own, recipient_codes=codes))
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
        flags = _run_unit(conn, run, "A", row["row_id"], lambda: agents.check_conflicts(
            settings, row=row, quote_check=checks[row["row_id"]], sources=paragraphs))
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
        verdict = _run_unit(conn, run, "B", row_id, lambda: agents.judge_applicability(
            settings, row=row, fund_facts=facts))
        verdicts.append({
            "verdict_id": f"VER-{run['run_id']}-{_row_n(row_id)}", "row_id": row_id,
            "verdict": verdict.verdict, "reasoning": verdict.reasoning,
            "cited_fact_ids": ", ".join(verdict.cited_fact_ids),
            "missing_information": verdict.missing_information or None})
    return {"verdicts": verdicts}


# --- Stage C (placeholder dates until B4) ---------------------------------------------------

def _stage_c(conn, settings: Settings, run: dict) -> dict:
    """STUB until B4: placeholder dates for rules 1, 2 and 4, if their answer is "applies"."""
    units = stage_units(conn, run, "C")
    stage_store.add_units(conn, run, "C", units)
    stage_store.mark_unit(conn, run, "C", units[0][0], "running")
    dates = {e["row_n"]: e for e in shell_data.ENTRIES}
    entries = []
    for d in conn.execute(
            """SELECT r.*, vd.decision AS g2_decision, vd.final_value, rd.business_day_rule AS chosen
               FROM verdict_decisions vd JOIN verdicts v ON v.verdict_id = vd.verdict_id
               JOIN rows r ON r.row_id = v.row_id
               JOIN row_decisions rd ON rd.row_id = r.row_id
               WHERE r.run_id = ? AND vd.final_value = 'applies' ORDER BY r.rowid""",
            (run["run_id"],)):
        n = _row_n(d["row_id"])
        if n not in dates:
            continue
        e = dates[n]
        entries.append({
            "entry_id": f"ENT-{run['fund_id']}-{d['source_paragraph_id']}-{d['recipient_code']}-{e['period']}",
            "row_id": d["row_id"], "period": e["period"], "due_date": e["due_date"],
            "unadjusted_date": e.get("moved_from"), "business_day_rule": d["chosen"],
            "moved": e["moved"], "precautionary": d["g2_decision"] == "decide",
            "open_question_id": e["open_question_id"]})
    stage_store.mark_unit(conn, run, "C", units[0][0], "done")
    return {"entries": entries}


_STAGES = {"A": _stage_a, "B": _stage_b, "C": _stage_c}


def run_stage(settings: Settings, run_id: str, stage: str) -> None:
    """Run stage A, B or C for one run. Called as a background task, with only the run ID."""
    conn = connect(settings.database_path)
    try:
        run = runs_service.get_run(conn, run_id)
        try:
            outputs = _STAGES[stage](conn, settings, run)
        except _StageStopped:
            return   # fail_stage has recorded the failure; nothing is stored (rule 9)
        stage_store.store_stage_outputs(
            conn, run_id=run_id, fund_id=run["fund_id"], stage=stage,
            stage_attempt=run["stage_attempt"], outputs=outputs)
    finally:
        conn.close()
