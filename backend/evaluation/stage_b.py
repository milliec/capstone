"""Grade a finished stage B run, read from the database (operator decision, 2026-11-21).

Same approach as stage A (stage_a.py): the app makes the run; this only reads it. It starts no run,
calls no model and writes nothing. Stage B is "finished" when it stored its verdicts, which the app
does only when every unit is done (rule 9). A run that stopped earlier has nothing to grade here:
failed runs (cost cap, time limit, model service) belong to the rest of B8 and the void rule (EC-R8).

EC-010 and EC-012 read the whole trace of the run, late calls and copy cases included. They sit in
this report because every model step is in the trace once stage B has stored: stage C is code.
"""

import sqlite3
from datetime import UTC, datetime

from backend.domain.fund_facts import load_fund_facts
from backend.evaluation import golden, grade_b
from backend.evaluation.stage_a import NotGradable, cycle_stamp, load_stage_a

NOT_IN_THIS_SLICE = (
    "EC-007, EC-008: stage C (already Tier 1 tests); EC-011: review time, on the rehearsal run",
    "I-1 and the injection case (EC-005, EC-021): they need the agents (model calls); see the stage A report",
    "The run starter: evaluation-run type, scripted gates, EC-R7 refusal (B8, after the spike)",
    "The trace export (D4, T-D4-1) and the void rule (EC-R8); a failed run is not graded here",
    "The verdict reasoning is free text: it is not graded (the key's reasoning is not read)",
    "EC-R1: this is ONE run; a criterion passes only on 3 of 3 consecutive runs of one commit",
)


def load_stage_b(conn: sqlite3.Connection, run: dict) -> grade_b.StageBOutput:
    """What stage B stored for the run, the rows approved at G1 and the trace totals."""
    run_id = run["run_id"]
    units = [r["status"] for r in conn.execute(
        """SELECT status FROM units WHERE run_id = ? AND stage = 'B' AND stage_attempt =
           (SELECT MAX(stage_attempt) FROM units WHERE run_id = ? AND stage = 'B')""",
        (run_id, run_id))]
    if not units:
        raise NotGradable(f"Stage B never started for {run_id} (status {run['status']}, phase "
                          f"{run['phase']}): nothing to grade.")
    if any(status != "done" for status in units):
        raise NotGradable(f"Stage B did not finish for {run_id} (status {run['status']}, phase "
                          f"{run['phase']}): nothing to grade.")
    verdicts = [grade_b.StoredVerdict(
        verdict_id=v["verdict_id"], row_id=v["row_id"], verdict=v["verdict"],
        cited_fact_ids=[f.strip() for f in v["cited_fact_ids"].split(",") if f.strip()],
        reasoning=v["reasoning"], missing_information=v["missing_information"] or "")
        for v in conn.execute(
            """SELECT v.* FROM verdicts v JOIN rows r ON r.row_id = v.row_id
               WHERE r.run_id = ? ORDER BY v.rowid""", (run_id,))]
    approved = {r["row_id"] for r in conn.execute(
        """SELECT d.row_id FROM row_decisions d JOIN rows r ON r.row_id = d.row_id
           WHERE r.run_id = ? AND d.decision = 'approve'""", (run_id,))}
    facts = load_fund_facts(run["fund_id"])
    existing = {f["fact_id"] for f in facts["facts"]} | {e["event_id"] for e in facts["events"]}
    t = conn.execute(
        """SELECT COUNT(*) AS calls, COALESCE(SUM(late), 0) AS late,
                  COALESCE(SUM(eval_case IS NOT NULL), 0) AS copies,
                  COALESCE(SUM(duration_ms), 0) AS ms, COALESCE(SUM(cost_usd), 0) AS cost,
                  COALESCE(SUM(CASE WHEN late THEN duration_ms END), 0) AS late_ms,
                  COALESCE(SUM(CASE WHEN late THEN cost_usd END), 0) AS late_cost
           FROM trace WHERE run_id = ?""", (run_id,)).fetchone()
    trace = grade_b.TraceSummary(calls=t["calls"], late_calls=t["late"], copy_case_calls=t["copies"],
                                 duration_ms=t["ms"], cost_usd=t["cost"],
                                 late_duration_ms=t["late_ms"], late_cost_usd=t["late_cost"],
                                 run_cost_count=run["cost_so_far"])
    return grade_b.StageBOutput(verdicts=verdicts, approved_row_ids=approved,
                                existing_fact_ids=existing, trace=trace)


def evaluate_stage_b(conn: sqlite3.Connection, run_id: str, *, now: datetime | None = None) -> dict:
    """The stage B report for one run, as plain data (JSON-ready). Raises NotGradable."""
    run, out_a = load_stage_a(conn, run_id)       # which key row each verdict is about
    out_b = load_stage_b(conn, run)
    key = golden.load_golden_set()
    counts, reasons = cycle_stamp(run)
    criteria = grade_b.grade_stage_b(out_a, out_b, key, stand_in=run["agents_mode"] == "stand_in")
    return {
        "report": "stage-b",
        "generated_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "run": {k: run[k] for k in ("run_id", "fund_id", "status", "phase", "agents_mode",
                                    "spend_activity", "demo_planted_row", "started_at")},
        "counts_for_cycle": counts,
        "does_not_count_because": reasons,
        "verdicts_stored": len(out_b.verdicts),
        "rows_approved_at_g1": len(out_b.approved_row_ids),
        "trace_calls": out_b.trace.calls,
        "criteria": [_plain(c) for c in criteria],
        "not_in_this_slice": list(NOT_IN_THIS_SLICE),
    }


def _plain(criterion) -> dict:
    return {"id": criterion.id, "name": criterion.name, "threshold": criterion.threshold,
            "status": criterion.status, "summary": criterion.summary,
            "checks": [vars(c) for c in criterion.checks],
            "findings": [vars(f) for f in criterion.findings],
            "notes": list(criterion.notes)}

