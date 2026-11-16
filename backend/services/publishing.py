"""Publish and decline at G3 (CR-011, CR-028, SD FR-022).

STUBS. Publishing inserts the publications row and completes the run; declining ends it
DECLINED. NO check: B2 adds ACK_REQUIRED (the acknowledgement and the two lists compared with the
server's own), VERSION_MISMATCH, RUN_STAGE_RUNNING, REASON_REQUIRED on decline, and the
decision-must-match-route rule (VALIDATION, DL-48).
"""

import json
import sqlite3

from backend.services.audit import now_utc, write_audit


def _run_for_calendar(conn: sqlite3.Connection, calendar_id: str) -> dict:
    row = conn.execute("SELECT run_id, fund_id FROM calendar_versions WHERE calendar_id = ?",
                       (calendar_id,)).fetchone()
    return dict(row)


def publish_calendar(conn: sqlite3.Connection, *, calendar_id: str, run_version: int,
                     acknowledged: bool, rejected_row_ids: list[str],
                     uncited_paragraph_ids: list[str], actor: str) -> str:
    """STUB — replace in B2. Publish the whole calendar; the run ends COMPLETED. Returns run ID."""
    cal = _run_for_calendar(conn, calendar_id)
    conn.execute(
        """INSERT INTO publications (fund_id, calendar_id, acknowledged_rejected_row_ids,
                                     acknowledged_uncited_paragraph_ids, published_by,
                                     published_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (cal["fund_id"], calendar_id, json.dumps(rejected_row_ids),
         json.dumps(uncited_paragraph_ids), actor, now_utc()))
    conn.execute("UPDATE runs SET status = 'COMPLETED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (cal["run_id"],))
    write_audit(conn, fund_id=cal["fund_id"], actor=actor, event_type="gate_event",
                run_id=cal["run_id"], subject_id=calendar_id, subject_version=run_version,
                reason=f"Calendar published (acknowledged: {acknowledged})")
    conn.commit()
    return cal["run_id"]


def decline_calendar(conn: sqlite3.Connection, *, calendar_id: str, run_version: int,
                     decline_reason: str, actor: str) -> str:
    """STUB — replace in B2. Close without publishing; the run ends DECLINED. Returns run ID."""
    cal = _run_for_calendar(conn, calendar_id)
    conn.execute("UPDATE runs SET status = 'DECLINED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (cal["run_id"],))
    write_audit(conn, fund_id=cal["fund_id"], actor=actor, event_type="gate_event",
                run_id=cal["run_id"], subject_id=calendar_id, subject_version=run_version,
                reason=decline_reason or "(stub: no reason given)")
    conn.commit()
    return cal["run_id"]
