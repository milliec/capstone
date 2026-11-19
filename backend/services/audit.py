"""The audit log: append-only (CR-013). The database triggers refuse UPDATE and DELETE."""

import sqlite3
from datetime import UTC, datetime


def now_utc() -> str:
    """The current time as an ISO 8601 string in UTC, used for every stored timestamp."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_audit(conn: sqlite3.Connection, *, fund_id: str, actor: str, event_type: str,
                run_id: str | None = None, subject_id: str | None = None,
                subject_version: int | None = None, refusal_code: str | None = None,
                reason: str | None = None, trace_ref: str | None = None) -> None:
    """Add one audit entry. The caller commits (so the entry lands with the change it records)."""
    conn.execute(
        """INSERT INTO audit_log (run_id, fund_id, at, actor, event_type, subject_id,
                                  subject_version, refusal_code, reason, trace_ref)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, fund_id, now_utc(), actor, event_type, subject_id, subject_version,
         refusal_code, reason, trace_ref),
    )


def list_audit(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Every audit entry for one run, oldest first."""
    rows = conn.execute("SELECT * FROM audit_log WHERE run_id = ? ORDER BY audit_id", (run_id,))
    return [dict(r) for r in rows]
