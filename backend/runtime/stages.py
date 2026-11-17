"""STUB — replace in B3 (stand-in part) and B13a. Runs one stage of a review in the background.

What it does, so the pages can show the running, done and failed states:
1. Adds one 'waiting' unit line per unit of the stage.
2. Runs the units one at a time: 'running', then the stand-in pause, then 'done'.
3. Failure demo (DL-52, rule 11): if the switch is on, stage A's FIRST unit on the FIRST stage
   attempt fails with 'demo failure', and the other units stay 'waiting'.
4. When every unit is done, builds the stage's outputs and gives them to the store, which saves
   them all or nothing and moves the run to the next gate (rule 9, stage_store.store_stage_outputs).

The outputs are fixed stand-in data (backend/stand_in/shell_data.py); B3 replaces them with the
stand-in fixtures. Not here yet: the stage timer (DL-43), trace and cost (CR-017, CR-018).
"""

from backend.db.connection import connect
from backend.runtime import agents
from backend.services import runs as runs_service
from backend.services import stage_store
from backend.settings import Settings
from backend.stand_in import shell_data


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
    """The (unit_id, label) pairs for one stage of a run. Stage B has one per approved rule."""
    if stage == "A":
        return list(shell_data.STAGE_A_UNITS)
    if stage == "B":
        return [(r["row_id"], r["obligation_name"]) for r in _approved_rows(conn, run["run_id"])]
    return [("CALENDAR", "Calendar")]


def stand_in_outputs(conn, run: dict, stage: str) -> dict:
    """The fixed stand-in outputs of a stage (B3 replaces them with the stand-in fixtures)."""
    run_id = run["run_id"]
    if stage == "A":
        source = list(shell_data.ROWS) + ([shell_data.DEMO_ROW] if run["demo_planted_row"] else [])
        paragraphs = [{"paragraph_id": f"SRC-STUB-P{n}", "document_id": f"DOC-STUB-{min(n, 5)}",
                       "text": f"Placeholder paragraph text for SRC-STUB-P{n}."}
                      for n in range(1, 7) if n != 4 or run["demo_planted_row"]]
        rows = [{**r, "row_id": f"ROW-{run_id}-{r['n']}", "quote_check": "pass"} for r in source]
        return {"paragraphs": paragraphs, "rows": rows}
    if stage == "B":
        by_n = {v["n"]: v for v in shell_data.VERDICTS}
        return {"verdicts": [{**by_n[_row_n(r["row_id"])], "row_id": r["row_id"],
                              "verdict_id": f"VER-{run_id}-{_row_n(r['row_id'])}"}
                             for r in _approved_rows(conn, run_id)
                             if _row_n(r["row_id"]) in by_n]}
    # Stage C: one entry for every rule whose final answer at G2 is "applies".
    dates = {e["row_n"]: e for e in shell_data.ENTRIES}
    entries = []
    for d in conn.execute(
            """SELECT r.*, vd.decision AS g2_decision, vd.final_value, rd.business_day_rule AS chosen
               FROM verdict_decisions vd JOIN verdicts v ON v.verdict_id = vd.verdict_id
               JOIN rows r ON r.row_id = v.row_id
               JOIN row_decisions rd ON rd.row_id = r.row_id
               WHERE r.run_id = ? AND vd.final_value = 'applies' ORDER BY r.rowid""", (run_id,)):
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
    return {"entries": entries}


def run_stage(settings: Settings, run_id: str, stage: str) -> None:
    """Run stage A, B or C for one run. Called as a background task, with only the run ID."""
    conn = connect(settings.database_path)
    try:
        run = runs_service.get_run(conn, run_id)
        units = stage_units(conn, run, stage)
        stage_store.add_units(conn, run, stage, units)

        for index, (unit_id, _label) in enumerate(units):
            stage_store.mark_unit(conn, run, stage, unit_id, "running")

            is_demo_failure = (stage == "A" and index == 0 and run["demo_fail_step1"]
                               and run["stage_attempt"] == 1
                               and settings.agents_mode == "stand_in")
            if is_demo_failure:
                agents.unit_pause(settings)  # so unit 1 shows 'running' for a moment first
                stage_store.fail_stage(conn, run, stage, unit_id, "demo failure")
                return

            agents.run_unit(settings, stage, unit_id)
            stage_store.mark_unit(conn, run, stage, unit_id, "done")

        stage_store.store_stage_outputs(
            conn, run_id=run_id, fund_id=run["fund_id"], stage=stage,
            stage_attempt=run["stage_attempt"], outputs=stand_in_outputs(conn, run, stage))
    finally:
        conn.close()
