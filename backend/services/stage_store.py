"""STUB — replace in B3. Stores a stage's progress and moves the run when the stage ends.

B3 builds the real version (run-state rule 9): outputs stored in one transaction when the stage
ends with every unit valid, checked against the run, phase and stage attempt. The stub only
keeps the units table and the run's phase up to date, with no checks.
"""

import sqlite3

from backend.services.audit import now_utc, write_audit

NEXT_GATE = {"A": "AT_G1", "B": "AT_G2", "C": "AT_G3"}


def add_units(conn: sqlite3.Connection, run: dict, stage: str,
              units: list[tuple[str, str]]) -> None:
    """STUB — replace in B3. Add one 'waiting' line per unit of this stage attempt."""
    conn.executemany(
        """INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status)
           VALUES (?, ?, ?, ?, ?, ?, 'waiting')""",
        [(run["run_id"], stage, run["stage_attempt"], unit_id, run["fund_id"], label)
         for unit_id, label in units],
    )
    conn.commit()


def mark_unit(conn: sqlite3.Connection, run: dict, stage: str, unit_id: str, status: str,
              failure_reason: str | None = None) -> None:
    """STUB — replace in B3. Set one unit's status (and reason, if it failed)."""
    attempts_add = 1 if status in ("done", "failed") else 0
    conn.execute(
        """UPDATE units SET status = ?, failure_reason = ?, attempts = attempts + ?
           WHERE run_id = ? AND stage = ? AND stage_attempt = ? AND unit_id = ?""",
        (status, failure_reason, attempts_add, run["run_id"], stage, run["stage_attempt"],
         unit_id),
    )
    conn.commit()


def finish_stage(conn: sqlite3.Connection, run: dict, stage: str) -> None:
    """STUB — replace in B3. The stage ended with every unit done: move to the next gate.

    Stage C also creates the calendar version, so G3 has a calendar_id to publish (entries are B4).
    """
    if stage == "C":
        conn.execute(
            """INSERT INTO calendar_versions (calendar_id, run_id, fund_id, version, generated_at)
               VALUES (?, ?, ?, 1, ?)""",
            (f"CAL-{run['run_id']}", run["run_id"], run["fund_id"], now_utc()),
        )
    conn.execute("UPDATE runs SET phase = ? WHERE run_id = ?", (NEXT_GATE[stage], run["run_id"]))
    write_audit(conn, fund_id=run["fund_id"], actor=f"stage {stage}", event_type="system",
                run_id=run["run_id"], subject_id=run["run_id"],
                reason=f"Stage {stage} finished (stand-in)")
    conn.commit()


def fail_stage(conn: sqlite3.Connection, run: dict, stage: str, unit_id: str,
               failure_reason: str) -> None:
    """STUB — replace in B3. A unit failed: the run becomes FAILED and keeps its phase (DL-46)."""
    mark_unit(conn, run, stage, unit_id, "failed", failure_reason)
    conn.execute("UPDATE runs SET status = 'FAILED' WHERE run_id = ?", (run["run_id"],))
    write_audit(conn, fund_id=run["fund_id"], actor=f"stage {stage}", event_type="system",
                run_id=run["run_id"], subject_id=unit_id, reason=failure_reason)
    conn.commit()
