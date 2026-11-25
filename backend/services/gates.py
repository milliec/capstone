"""The gate service: G1/G2 completion and starting the next stage (SAD §4).

Finishing a gate is checked BEFORE anything changes, in this order: the review has ended
(RUN_NOT_ACTIVE) → it is not at this gate (RUN_STAGE_RUNNING) → the page is stale
(VERSION_MISMATCH) → something is still undecided (GATE_INCOMPLETE). A refusal is audited and
changes nothing. Otherwise the phase moves, the run version goes up by one, and the next stage
starts.
"""

import sqlite3
from collections.abc import Callable

from backend.services import guards
from backend.services.audit import write_audit
from backend.services.refusals import NotFound, refuse
from backend.settings import Settings


def start_stage(settings: Settings, schedule: Callable, run_id: str, stage: str) -> None:
    """Start stage A, B or C as a background task, passing only the run ID (SAD §4).

    `schedule` is FastAPI's BackgroundTasks.add_task: the task runs after the page responds.
    The import is inside the function because runtime.stages also imports the services.
    """
    from backend.runtime.stages import run_stage

    schedule(run_stage, settings, run_id, stage)


def _complete_gate(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
                   run_id: str, run_version: int, actor: str, gate: str, next_phase: str,
                   next_stage: str) -> None:
    # Imported here: decisions imports runs, and runs imports this module.
    from backend.services import decisions, runs

    run = runs.get_run(conn, run_id)
    if run is None:
        raise NotFound(run_id)
    where = {"subject_id": run_id}
    guards.require_decidable_by(conn, run, actor, **where)     # DL-61: first, after the role check
    guards.require_active(conn, run, actor, **where)
    guards.require_phase(conn, run, f"AT_{gate}", actor, **where)
    guards.require_version(conn, run, run_version, actor, **where)
    undecided, unsure = decisions.count_undecided(conn, run_id, gate)
    if undecided:
        one = "_one" if undecided == 1 else ""
        refuse(conn, "GATE_INCOMPLETE", ("g1" if gate == "G1" else "g2") + one, actor=actor,
               fund_id=run["fund_id"], run_id=run_id, subject_id=run_id, x=undecided, u=unsure)
    conn.execute("UPDATE runs SET phase = ?, run_version = run_version + 1, stage_attempt = 1 "
                 "WHERE run_id = ?", (next_phase, run_id))
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="gate_event",
                run_id=run_id, subject_id=run_id, subject_version=run_version,
                reason=f"{gate} completed")
    conn.commit()
    start_stage(settings, schedule, run_id, next_stage)


def complete_g1(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
                run_id: str, run_version: int, actor: str) -> None:
    """Finish checking the rules: AT_G1 → B_RUNNING, then stage B. Every rule must be decided."""
    _complete_gate(conn, settings, schedule, run_id=run_id, run_version=run_version,
                   actor=actor, gate="G1", next_phase="B_RUNNING", next_stage="B")


def complete_g2(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
                run_id: str, run_version: int, actor: str) -> None:
    """Finish confirming: AT_G2 → C_RUNNING, then stage C (code only). Every answer decided."""
    _complete_gate(conn, settings, schedule, run_id=run_id, run_version=run_version,
                   actor=actor, gate="G2", next_phase="C_RUNNING", next_stage="C")
