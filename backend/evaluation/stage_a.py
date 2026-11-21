"""Grade a finished stage A run, read from the database (operator decision, 2026-11-21).

The app makes the run; this only reads it (sad.md §2 "One route only"). It starts no run, calls no
model and writes nothing to the run's tables. Start of an evaluation run (the evaluation-run type,
scripted gates, the EC-R7 refusal) is the rest of B8.

`counts_for_cycle` is a STAMP, not a gate: it says whether this run could be one of the cycle's
three (EC-R1). A stand-in run never can (T-MODE-1: an evaluation run refuses stand-in mode). The
report is made either way, because a grader that only works on real runs cannot be tested.
"""

import json
import sqlite3
from datetime import UTC, datetime

from backend.evaluation import cases, golden, grade

STAND_IN_STAMP = "STAND-IN RUN: does not count towards the cycle"


class NotGradable(Exception):
    """There is nothing to grade: the run does not exist, or stage A never stored its rows."""


def load_stage_a(conn: sqlite3.Connection, run_id: str) -> tuple[dict, grade.StageAOutput]:
    """The run's row and what stage A stored for it (rows, quote checks, flags, paragraphs)."""
    run = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if run is None:
        raise NotGradable(f"There is no run {run_id}.")
    paragraphs = {r["paragraph_id"]: r["paragraph_text"] for r in conn.execute(
        "SELECT paragraph_id, paragraph_text FROM paragraphs WHERE run_id = ? ORDER BY rowid",
        (run_id,))}
    if not paragraphs:
        raise NotGradable(f"Stage A has not stored its output for {run_id} "
                          f"(status {run['status']}, phase {run['phase']}): nothing to grade.")
    rows = []
    for r in conn.execute("SELECT * FROM rows WHERE run_id = ? ORDER BY rowid", (run_id,)):
        check = conn.execute("SELECT result FROM quote_checks WHERE row_id = ?",
                             (r["row_id"],)).fetchone()
        flags = [dict(f) for f in conn.execute(
            "SELECT * FROM flags WHERE row_id = ? ORDER BY flag_id", (r["row_id"],))]
        rows.append(grade.StoredRow(
            row_id=r["row_id"], origin=r["origin"], source_paragraph_id=r["source_paragraph_id"],
            obligation_name=r["obligation_name"], frequency=r["frequency"], anchor=r["anchor"],
            offset=json.loads(r["offset"]), recipient_code=r["recipient_code"],
            responsible_role=r["responsible_role"], applicability_rule=r["applicability_rule"],
            business_day_rule=r["business_day_rule"], quote=r["quote"],
            quote_check=check["result"] if check else "", flags=flags))
    return dict(run), grade.StageAOutput(rows=rows, paragraphs=paragraphs)


def cycle_stamp(run: dict) -> tuple[bool, list[str]]:
    """(counts_for_cycle, reasons it does not). Marks only; it refuses nothing (EC-R7 is later)."""
    reasons = []
    if run["agents_mode"] == "stand_in":
        reasons.append(STAND_IN_STAMP)
    elif run["spend_activity"] != "evaluation":
        reasons.append(f"Real run labelled {run['spend_activity']!r}, not 'evaluation' (EC-R6)")
    if run["demo_planted_row"]:
        reasons.append("The planted-row switch was on (EC-R7): an evaluation run has it off")
    return not reasons, reasons


# What this slice leaves out, so a reader never takes silence for a pass.
NOT_IN_THIS_SLICE = (
    "EC-004, EC-007, EC-008: stage B and C (EC-007 and EC-008 are already Tier 1 tests)",
    "EC-010, EC-011, EC-012: whole-run time, review time and cost",
    "I-1 and the injection case (EC-005, EC-021): they need the agents (model calls)",
    "The run starter: evaluation-run type, scripted gates, EC-R7 refusal (B8, after the spike)",
    "The trace export (D4, T-D4-1) and the void rule (EC-R8)",
    "EC-R1: this is ONE run; a criterion passes only on 3 of 3 consecutive runs of one commit",
)


def evaluate_stage_a(conn: sqlite3.Connection, run_id: str, *, now: datetime | None = None) -> dict:
    """The stage A report for one run, as plain data (JSON-ready). Raises NotGradable."""
    run, out = load_stage_a(conn, run_id)
    key = golden.load_golden_set()
    copy_cases = cases.run_copy_cases(key, out.paragraphs)
    counts, reasons = cycle_stamp(run)
    criteria = grade.grade_stage_a(out, key, copy_cases)
    return {
        "report": "stage-a",
        "generated_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "run": {k: run[k] for k in ("run_id", "fund_id", "status", "phase", "agents_mode",
                                    "spend_activity", "demo_planted_row", "started_at")},
        "counts_for_cycle": counts,
        "does_not_count_because": reasons,
        "rows_drafted_by_the_extractor": len(grade.extracted_rows(out)),
        "demo_rows_not_graded": sum(1 for r in out.rows if r.origin == "demo"),
        "criteria": [_plain(c) for c in criteria],
        "copy_cases": [vars(c) for c in copy_cases],
        "not_in_this_slice": list(NOT_IN_THIS_SLICE),
    }


def _plain(criterion: grade.Criterion) -> dict:
    return {"id": criterion.id, "name": criterion.name, "threshold": criterion.threshold,
            "status": criterion.status, "summary": criterion.summary,
            "checks": [vars(c) for c in criterion.checks],
            "findings": [vars(f) for f in criterion.findings],
            "notes": list(criterion.notes)}
