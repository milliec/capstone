"""The gate service: G1/G2 completion and starting the next stage (SAD §4).

Gate completion functions are STUBS: they move the phase and raise the run version, with NO
check. B2 adds: the phase guard (RUN_STAGE_RUNNING), VERSION_MISMATCH, GATE_INCOMPLETE
(every row / verdict decided), RUN_NOT_ACTIVE.
"""

import sqlite3
from typing import Callable

from backend.services import FUND_ID
from backend.services.audit import write_audit
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
    conn.execute("UPDATE runs SET phase = ?, run_version = run_version + 1 WHERE run_id = ?",
                 (next_phase, run_id))
    write_audit(conn, fund_id=FUND_ID, actor=actor, event_type="gate_event",
                run_id=run_id, subject_id=run_id, subject_version=run_version,
                reason=f"{gate} completed")
    conn.commit()
    start_stage(settings, schedule, run_id, next_stage)


def complete_g1(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
                run_id: str, run_version: int, actor: str) -> None:
    """STUB — replace in B2. Finish checking the rules: AT_G1 → B_RUNNING, then stage B."""
    _complete_gate(conn, settings, schedule, run_id=run_id, run_version=run_version,
                   actor=actor, gate="G1", next_phase="B_RUNNING", next_stage="B")


def complete_g2(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
                run_id: str, run_version: int, actor: str) -> None:
    """STUB — replace in B2. Finish confirming: AT_G2 → C_RUNNING, then stage C (code only)."""
    _complete_gate(conn, settings, schedule, run_id=run_id, run_version=run_version,
                   actor=actor, gate="G2", next_phase="C_RUNNING", next_stage="C")
