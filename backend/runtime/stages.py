"""STUB — replace in B3 (stand-in part) and B13a. Runs one stage of a review in the background.

What the stub does, so the pages can show the running, done and failed states:
1. Adds one 'waiting' unit line per unit of the stage.
2. Runs the units one at a time: 'running', then the stand-in pause, then 'done'.
3. Failure demo (DL-52, rule 11): if the switch is on, stage A's FIRST unit on the FIRST stage
   attempt fails with 'demo failure', and the other units stay 'waiting'.
4. When every unit is done, moves the run to the next gate.

Not in the stub: the stage timer (DL-43), trace and cost (CR-017, CR-018), storing outputs (rule 9).
"""

from backend.db.connection import connect
from backend.runtime import agents
from backend.services import runs as runs_service
from backend.services import stage_store
from backend.settings import Settings
from backend.stand_in import shell_data


def stage_units(run: dict, stage: str) -> list[tuple[str, str]]:
    """The (unit_id, label) pairs for one stage of a run."""
    if stage == "A":
        return list(shell_data.STAGE_A_UNITS)
    if stage == "B":
        return [(f"ROW-{run['run_id']}-{r['n']}", r["obligation_name"]) for r in shell_data.ROWS]
    return [("CALENDAR", "Calendar")]


def run_stage(settings: Settings, run_id: str, stage: str) -> None:
    """Run stage A, B or C for one run. Called as a background task, with only the run ID."""
    conn = connect(settings.database_path)
    try:
        run = runs_service.get_run(conn, run_id)
        units = stage_units(run, stage)
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

        stage_store.finish_stage(conn, run, stage)
    finally:
        conn.close()
