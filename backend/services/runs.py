"""Runs: start, list, abandon, retry, and the run states (SAD §4, "Transitions and guards").

Most functions here are STUBS. They move status and phase so the pages can be clicked through,
but hold NO check: no one-active-run rule (RUN_ACTIVE), no phase guard (RUN_STAGE_RUNNING), no
version check, no reason check, and no refusal of the failure demo in real mode. B2 adds them.
"""

import sqlite3
from datetime import date
from typing import Callable

from backend.domain.ids import new_run_id
from backend.services import gates
from backend.services.audit import now_utc, write_audit
from backend.services.auth import IDENTITIES
from backend.settings import Settings

# ux.md §1.5: a status is always words first. Keyed by (status, phase); terminal statuses ignore
# the phase.
STATUS_WORDS = {
    ("ACTIVE", "A_RUNNING"): "AI is drafting the rules",
    ("ACTIVE", "AT_G1"): "Your turn: check the rules",
    ("ACTIVE", "B_RUNNING"): "AI is checking what applies",
    ("ACTIVE", "AT_G2"): "Your turn: confirm what applies",
    ("ACTIVE", "C_RUNNING"): "Working out the dates",
    ("ACTIVE", "AT_G3"): "Your turn: publish the calendar",
    "FAILED": "Failed",
    "ABANDONED": "Abandoned",
    "DECLINED": "Closed without publishing",
    "COMPLETED": "Published",
}

# ux.md §10.1: the four review states the workflow names.
WORKFLOW_STATE = {"ACTIVE": "running", "FAILED": "failed", "ABANDONED": "done",
                  "DECLINED": "done", "COMPLETED": "done"}


# ux.md §1.5 tones (H-036 V-2). An ACTIVE run's tone follows its phase; an ended run's follows
# its status. The page uses the value as sent and never works the tone out itself.
TONE_ACTIVE = {"A_RUNNING": "info", "AT_G1": "action", "B_RUNNING": "info",
               "AT_G2": "action", "C_RUNNING": "info", "AT_G3": "action"}
TONE_ENDED = {"FAILED": "problem", "ABANDONED": "neutral", "DECLINED": "neutral",
              "COMPLETED": "success"}


def _review_number(conn: sqlite3.Connection, run: dict) -> int:
    """H-036 V-1. The review's number: its place among the fund's runs, oldest = 1.

    Runs are never deleted (the audit trail needs them), so a number never changes once given.
    The SAD does not define the number; this is the simplest rule and is flagged in backend.md.
    """
    (count,) = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE fund_id = ? AND rowid <= "
        "(SELECT rowid FROM runs WHERE run_id = ?)", (run["fund_id"], run["run_id"])).fetchone()
    return count


def _started_by_label(started_by: str) -> str:
    """H-036 V-7. 'Compliance specialist (mock)': the sign-in label, marked as a demo identity."""
    identity = IDENTITIES.get(started_by)
    return f"{identity.label} (mock)" if identity else started_by


def _describe(conn: sqlite3.Connection, run: dict) -> dict:
    """Add the words and flags a page needs, so no template works anything out (ux.md §1.2)."""
    status, phase = run["status"], run["phase"]
    run["status_words"] = STATUS_WORDS.get((status, phase)) or STATUS_WORDS.get(status, status)
    run["workflow_state"] = WORKFLOW_STATE[status]
    run["is_working"] = status == "ACTIVE" and phase.endswith("_RUNNING")
    run["is_at_gate"] = status == "ACTIVE" and phase.startswith("AT_G")
    # H-036 view fields (placeholder-safe in stand-in mode)
    run["review_number"] = _review_number(conn, run)                                # V-1
    run["status_tone"] = (TONE_ACTIVE.get(phase, "neutral") if status == "ACTIVE"
                          else TONE_ENDED.get(status, "neutral"))                   # V-2
    run["started_by_label"] = _started_by_label(run["started_by"])                   # V-7
    return run


def get_run(conn: sqlite3.Connection, run_id: str) -> dict | None:
    """One run with its display words, or None if there is no such run."""
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    return _describe(conn, dict(row)) if row else None


def list_runs(conn: sqlite3.Connection, fund_id: str) -> list[dict]:
    """Every run for the fund, newest first (scaffold-plan.md §5 names this function)."""
    rows = conn.execute(
        "SELECT * FROM runs WHERE fund_id = ? ORDER BY started_at DESC, rowid DESC", (fund_id,)
    ).fetchall()   # fetched first: _describe runs more queries on the same connection
    return [_describe(conn, dict(r)) for r in rows]


def get_active_run(conn: sqlite3.Connection, fund_id: str) -> dict | None:
    """The fund's ACTIVE run, if any. None means the 'idle' state (ux.md §10.1)."""
    row = conn.execute(
        "SELECT * FROM runs WHERE fund_id = ? AND status = 'ACTIVE' ORDER BY rowid DESC LIMIT 1",
        (fund_id,),
    ).fetchone()
    return _describe(conn, dict(row)) if row else None


def _unit_group(unit: dict) -> str:
    """H-036 V-4. Which card of the review status page a unit belongs to (the page never decides).

    Step 1 (stage A) splits in two: one unit per source document ("drafting") and one per drafted
    rule ("checking_drafts"). Stage B is step 3 ("applies"); stage C is step 4 ("dates").
    The stand-in stage A makes only the document units; B3 adds the per-rule checking units.
    """
    stage = unit["stage"]
    if stage == "A":
        return "checking_drafts" if unit["unit_id"].startswith("ROW-") else "drafting"
    return {"B": "applies", "C": "dates"}[stage]


def list_units(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """The run's unit lines, in the order they were added, each with its `group` (V-4)."""
    rows = conn.execute("SELECT * FROM units WHERE run_id = ? ORDER BY rowid", (run_id,))
    return [{**dict(r), "group": _unit_group(dict(r))} for r in rows]


def start_run(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
              fund_id: str, started_by: str, demo_planted_row: bool,
              demo_fail_step1: bool) -> str:
    """STUB — replace in B2 (and B13a for the failure-demo refusal). Start a review.

    Creates the run in ACTIVE · A_RUNNING, audits the start and each switch that is on, then
    starts stage A in the background. Returns the new run ID.
    B2 adds: RUN_ACTIVE (one active run per fund), VALIDATION for demo_fail_step1 in real mode.
    """
    run_id = new_run_id(conn, date.today())
    conn.execute(
        """INSERT INTO runs (run_id, fund_id, status, phase, run_version, demo_planted_row,
                             agents_mode, cost_so_far, started_by, started_at, demo_fail_step1,
                             stage_attempt, spend_activity)
           VALUES (?, ?, 'ACTIVE', 'A_RUNNING', 1, ?, ?, 0, ?, ?, ?, 1, ?)""",
        (run_id, fund_id, int(demo_planted_row), settings.agents_mode, started_by, now_utc(),
         int(demo_fail_step1), settings.spend_activity or None),
    )
    write_audit(conn, fund_id=fund_id, actor=started_by, event_type="gate_event", run_id=run_id,
                subject_id=run_id, subject_version=1, reason="Review started")
    if demo_planted_row:
        write_audit(conn, fund_id=fund_id, actor=started_by, event_type="system", run_id=run_id,
                    subject_id=run_id, reason="Demo rule switch on")
    if demo_fail_step1:
        write_audit(conn, fund_id=fund_id, actor=started_by, event_type="system", run_id=run_id,
                    subject_id=run_id, reason="Failure demo switch on")
    conn.commit()
    gates.start_stage(settings, schedule, run_id, "A")
    return run_id


def abandon_run(conn: sqlite3.Connection, *, run_id: str, run_version: int, reason: str,
                actor: str) -> None:
    """STUB — replace in B2. Abandon a review; it ends ABANDONED and keeps its phase (DL-46).

    B2 adds: only in AT_G1/AT_G2/AT_G3 (RUN_STAGE_RUNNING), VERSION_MISMATCH, REASON_REQUIRED.
    """
    conn.execute("UPDATE runs SET status = 'ABANDONED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (run_id,))
    run = get_run(conn, run_id)
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="gate_event",
                run_id=run_id, subject_id=run_id, subject_version=run_version,
                reason=reason or "(stub: no reason given)")
    conn.commit()


def retry_run(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
              run_id: str, run_version: int, actor: str) -> str:
    """STUB — replace in B13b (Retry, DL-51). Not built in the shell: changes nothing.

    Returns the sentence the page shows. B13b adds the transition out of FAILED, stage_attempt 2,
    RUN_NOT_FAILED, RETRY_LIMIT_REACHED and RETRY_NOT_ALLOWED.
    """
    return "Retry is not built yet (block B13b). Start a new review from Filing rules."
