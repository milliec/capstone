"""Publish and decline at G3 (CR-011, CR-028, SD FR-022).

Both are checked BEFORE anything changes, in this order: the review has ended (RUN_NOT_ACTIVE) →
it is not at G3 (RUN_STAGE_RUNNING) → the page is stale (VERSION_MISMATCH) → then, for publish,
the acknowledgement (ACK_REQUIRED) or, for decline, the written reason (REASON_REQUIRED). A
refusal is audited and changes nothing.

The acknowledgement must match the server's OWN lists of rejected rules and unused paragraphs
(CR-028), not just a ticked box. The check that the form's `decision` matches the route
(VALIDATION, DL-48) stays in the page handler, because these functions have no `decision`.
"""

import json
import sqlite3

from backend.services import decisions, guards, runs
from backend.services.audit import now_utc, write_audit
from backend.services.refusals import NotFound, refuse


def _run_for_calendar(conn: sqlite3.Connection, calendar_id: str) -> dict:
    row = conn.execute("SELECT run_id FROM calendar_versions WHERE calendar_id = ?",
                       (calendar_id,)).fetchone()
    if row is None:
        raise NotFound(calendar_id)
    return runs.get_run(conn, row["run_id"])


def publish_calendar(conn: sqlite3.Connection, *, calendar_id: str, run_version: int,
                     acknowledged: bool, rejected_row_ids: list[str],
                     uncited_paragraph_ids: list[str], actor: str) -> str:
    """Publish the whole calendar; the run ends COMPLETED. Returns the run ID."""
    run = _run_for_calendar(conn, calendar_id)
    where = {"subject_id": calendar_id}
    guards.require_active(conn, run, actor, **where)
    guards.require_phase(conn, run, "AT_G3", actor, **where)
    guards.require_version(conn, run, run_version, actor, **where)
    server_rejected = [r["row_id"] for r in decisions.rejected_rows(conn, run)]
    server_unused = [p["paragraph_id"] for p in decisions.unused_paragraphs(conn, run)]
    ack = {"actor": actor, "fund_id": run["fund_id"], "run_id": run["run_id"],
           "subject_id": calendar_id, "anchor": "ack", "target_label": "the box"}
    if not acknowledged:
        refuse(conn, "ACK_REQUIRED", "unticked", **ack)
    if (sorted(rejected_row_ids) != sorted(server_rejected)
            or sorted(uncited_paragraph_ids) != sorted(server_unused)):
        refuse(conn, "ACK_REQUIRED", "changed", **ack)
    conn.execute(
        """INSERT INTO publications (fund_id, calendar_id, acknowledged_rejected_row_ids,
                                     acknowledged_uncited_paragraph_ids, published_by,
                                     published_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (run["fund_id"], calendar_id, json.dumps(rejected_row_ids),
         json.dumps(uncited_paragraph_ids), actor, now_utc()))
    conn.execute("UPDATE runs SET status = 'COMPLETED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (run["run_id"],))
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="gate_event",
                run_id=run["run_id"], subject_id=calendar_id, subject_version=run_version,
                reason=f"Calendar published (acknowledged {len(server_rejected)} rejected rules "
                       f"and {len(server_unused)} unused paragraphs)")
    conn.commit()
    return run["run_id"]


def decline_calendar(conn: sqlite3.Connection, *, calendar_id: str, run_version: int,
                     decline_reason: str, actor: str) -> str:
    """Close without publishing; the run ends DECLINED. Returns the run ID."""
    run = _run_for_calendar(conn, calendar_id)
    where = {"subject_id": calendar_id}
    guards.require_active(conn, run, actor, **where)
    guards.require_phase(conn, run, "AT_G3", actor, **where)
    guards.require_version(conn, run, run_version, actor, **where)
    reason = (decline_reason or "").strip()
    if not reason:
        refuse(conn, "REASON_REQUIRED", "decline", actor=actor, fund_id=run["fund_id"],
               run_id=run["run_id"], subject_id=calendar_id, anchor="decline-reason",
               target_label="the reason", typed={"decline_reason": decline_reason or ""})
    conn.execute("UPDATE runs SET status = 'DECLINED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (run["run_id"],))
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="gate_event",
                run_id=run["run_id"], subject_id=calendar_id, subject_version=run_version,
                reason=reason)
    conn.commit()
    return run["run_id"]
