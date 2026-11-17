"""Runs: start, list, abandon, retry, and the run states (SAD §4, "Transitions and guards").

B2: `start_run` and `abandon_run` hold their checks (RUN_ACTIVE, RUN_NOT_ACTIVE, RUN_STAGE_RUNNING,
VERSION_MISMATCH, REASON_REQUIRED, VALIDATION). `retry_run` is still a stub (B13b).
"""

import sqlite3
from datetime import date
from typing import Callable

from backend.domain.ids import new_run_id
from backend.services import gates, guards
from backend.services.audit import now_utc, write_audit
from backend.services.auth import IDENTITIES
from backend.services.refusals import NotFound, refuse
from backend.settings import Settings
from backend.stand_in import shell_data

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


def actor_label(started_by: str) -> str:
    """H-036 V-7, V-8. 'Compliance specialist (mock)': the sign-in label, marked as a demo identity."""
    identity = IDENTITIES.get(started_by)
    return f"{identity.label} (mock)" if identity else started_by


# Where a step page stands for each phase of an ACTIVE review: "before" (not reached yet), "at"
# (forms show), "after" (read-only). H-036 V-8 to V-10 `stage`.
PAGE_STAGE = {
    "g1": {"A_RUNNING": "before", "AT_G1": "at", "B_RUNNING": "after", "AT_G2": "after",
           "C_RUNNING": "after", "AT_G3": "after"},
    "g2": {"A_RUNNING": "before", "AT_G1": "before", "B_RUNNING": "before", "AT_G2": "at",
           "C_RUNNING": "after", "AT_G3": "after"},
    "g3": {"A_RUNNING": "before", "AT_G1": "before", "B_RUNNING": "before", "AT_G2": "before",
           "C_RUNNING": "before", "AT_G3": "at"},
}


def page_stage(run: dict, page: str) -> str:
    """H-036 V-8 to V-10. 'before', 'at', 'after' or 'ended_before' for a step page ('g1'...).

    An ended review never shows forms: a step it reached is read-only ('after'); a step it never
    reached is 'ended_before' (ux.md "Closed review").
    """
    stage = PAGE_STAGE[page][run["phase"]]
    if run["status"] == "ACTIVE":
        return stage
    if run["status"] == "COMPLETED":
        return "after"
    return "ended_before" if stage == "before" else "after"


# ux.md §1.4: the stepper, one row per server phase (H-036 V-3).
STEPS_ACTIVE = {
    "A_RUNNING": ["In progress", "Not started", "Not started", "Not started"],
    "AT_G1": ["Done", "Your turn", "Not started", "Not started"],
    "B_RUNNING": ["Done", "Done", "In progress", "Not started"],
    "AT_G2": ["Done", "Done", "Your turn", "Not started"],
    "C_RUNNING": ["Done", "Done", "Done", "In progress"],
    "AT_G3": ["Done", "Done", "Done", "Your turn"],
}
# The step a review stopped at, from runs.phase, which keeps its last value on an ended review
# (DL-46; ux.md §1.4).
STOPPED_STEP = {"A_RUNNING": 1, "AT_G1": 2, "B_RUNNING": 3, "AT_G2": 3, "C_RUNNING": 4, "AT_G3": 4}
STEP_NAMES = {1: "AI drafts the rules", 2: "You check the rules", 3: "You confirm what applies",
              4: "You publish the calendar"}
STEP_PATHS = {1: "", 2: "/g1", 3: "/g2", 4: "/g3"}
# ux.md page 3, "Failure reason sentences", keyed by the stored reason. No final full stop.
FAILURE_SENTENCES = {
    "model service": "The model service did not answer in time, or returned an error, twice",
    "stage time limit": "This step took longer than its time limit",
    "invalid output": "The AI returned output in the wrong format, so it was not used",
    "cost cap": "The review reached its cost limit of US$2.50",
    "service restarted": "The application restarted while AI was working",
    "calendar generation": "The dates could not be worked out into one complete calendar",
    "demo failure": ("This step failed on purpose, for the demo only, because \"Make step 1 fail "
                     "(demo)\" was ticked when the review started. Nothing else went wrong"),
}


def _steps(run: dict) -> list[dict]:
    """H-036 V-3. The four stepper items: {state, href, current}."""
    status, phase = run["status"], run["phase"]
    if status == "ACTIVE":
        states = STEPS_ACTIVE[phase]
    elif status == "COMPLETED":
        states = ["Done"] * 4
    else:   # stopped: earlier steps Done, the stopping step Ended/Failed, later ones Not started
        stop = STOPPED_STEP[phase]
        word = "Failed" if status == "FAILED" else "Ended"
        states = ["Done" if i < stop else word if i == stop else "Not started"
                  for i in range(1, 5)]
    return [{"state": st,
             "href": (f"/specialist/runs/{run['run_id']}{STEP_PATHS[i]}"
                      if st in ("Done", "Your turn") else None),
             "current": st in ("In progress", "Your turn", "Failed", "Ended")}
            for i, st in enumerate(states, start=1)]


def _counts(run: dict) -> dict:
    """H-036 V-5. The numbers in the status sentences. STUB: counted from the stand-in data."""
    rules = len(shell_data.ROWS) + (1 if run["demo_planted_row"] else 0)
    return {"rules": rules,
            "unsure": sum(1 for v in shell_data.VERDICTS if v["verdict"] == "unsure"),
            "dates": len(shell_data.ENTRIES)}


def _ended(conn: sqlite3.Connection, run: dict) -> dict | None:
    """H-036 V-6. When and why an abandoned or declined review ended: {at, reason}.

    There is no 'ended at' column; the abandon or decline writes a gate_event audit entry with
    the reason, so the review's last gate_event is it.
    """
    if run["status"] not in ("ABANDONED", "DECLINED"):
        return None
    row = conn.execute(
        "SELECT at, reason FROM audit_log WHERE run_id = ? AND event_type = 'gate_event' "
        "ORDER BY audit_id DESC LIMIT 1", (run["run_id"],)).fetchone()
    return {"at": row["at"], "reason": row["reason"]} if row else None


def _published_at(conn: sqlite3.Connection, run: dict) -> str | None:
    """H-036 V-6. When a COMPLETED review's calendar was published."""
    if run["status"] != "COMPLETED":
        return None
    row = conn.execute(
        "SELECT p.published_at FROM publications p JOIN calendar_versions c "
        "ON c.calendar_id = p.calendar_id WHERE c.run_id = ? ORDER BY p.publication_id DESC "
        "LIMIT 1", (run["run_id"],)).fetchone()
    return row["published_at"] if row else None


def _failure(conn: sqlite3.Connection, run: dict) -> dict | None:
    """H-036 V-6. For a FAILED review: {step, step_name, unit_label, reason_sentence}."""
    if run["status"] != "FAILED":
        return None
    step = STOPPED_STEP[run["phase"]]
    unit = conn.execute(
        "SELECT label, failure_reason FROM units WHERE run_id = ? AND status = 'failed' "
        "ORDER BY rowid LIMIT 1", (run["run_id"],)).fetchone()
    reason = unit["failure_reason"] if unit else None
    return {"step": step, "step_name": STEP_NAMES[step],
            "unit_label": unit["label"] if unit else None,
            "reason_sentence": FAILURE_SENTENCES.get(reason, reason)}


def _ended_because(run: dict) -> str | None:
    """H-036 V-6. The short 'why' on a Filing rules row: the failure sentence, or the first line
    of the abandon / decline reason."""
    if run["failure"]:
        return run["failure"]["reason_sentence"]
    if run["ended"] and run["ended"]["reason"]:
        return run["ended"]["reason"].splitlines()[0]
    return None


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
    run["started_by_label"] = actor_label(run["started_by"])                   # V-7
    run["steps"] = _steps(run)                                                       # V-3
    run["counts"] = _counts(run)                                                     # V-5
    run["ended"] = _ended(conn, run)                                                 # V-6
    run["published_at"] = _published_at(conn, run)                                   # V-6
    run["failure"] = _failure(conn, run)                                             # V-6
    run["ended_because"] = _ended_because(run)                                       # V-6
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
    """Start a review (CR-023, rule 5). Returns the new run ID.

    Refused, and audited, when: a run is already ACTIVE for the fund (RUN_ACTIVE); or the failure
    demo is asked for outside stand-in mode (VALIDATION, DL-52). Otherwise it creates the run in
    ACTIVE · A_RUNNING, audits the start and each switch that is on, and starts stage A.
    """
    # BEGIN IMMEDIATE takes the database's write lock now, so two quick clicks on "Start" cannot
    # both pass the check below: the second waits, then sees the first run and is refused.
    conn.execute("BEGIN IMMEDIATE")
    active = get_active_run(conn, fund_id)
    if active:
        n = active["review_number"]
        refuse(conn, "RUN_ACTIVE", actor=started_by, fund_id=fund_id, run_id=active["run_id"],
               anchor="start", target_label="Start a new review", n=n,
               short=f"Not done. A new review can't start while review {n} is in progress.",
               link_text="Go to 'Start a new review'")
    if demo_fail_step1 and settings.agents_mode != "stand_in":
        refuse(conn, "VALIDATION", "field", actor=started_by, fund_id=fund_id, anchor="start",
               target_label="Start a new review", field="the failure demo")
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
    """Abandon a review at a gate; it ends ABANDONED and keeps its phase (DL-46, rule 8).

    Refused, and audited, in this order: the review has ended (RUN_NOT_ACTIVE); AI or code is
    still working (RUN_STAGE_RUNNING); the page is stale (VERSION_MISMATCH); no written reason
    (REASON_REQUIRED). Nothing changes when it is refused.
    """
    run = get_run(conn, run_id)
    if run is None:
        raise NotFound(run_id)
    where = {"subject_id": run_id}
    guards.require_active(conn, run, actor, **where)
    guards.require_at_a_gate(conn, run, actor, **where)
    guards.require_version(conn, run, run_version, actor, **where)
    if not (reason or "").strip():
        refuse(conn, "REASON_REQUIRED", "abandon", actor=actor, fund_id=run["fund_id"],
               run_id=run_id, subject_id=run_id, anchor="abandon", target_label="abandon",
               typed={"reason": reason or ""})
    conn.execute("UPDATE runs SET status = 'ABANDONED', run_version = run_version + 1 "
                 "WHERE run_id = ?", (run_id,))
    write_audit(conn, fund_id=run["fund_id"], actor=actor, event_type="gate_event",
                run_id=run_id, subject_id=run_id, subject_version=run_version,
                reason=reason.strip())
    conn.commit()


def retry_run(conn: sqlite3.Connection, settings: Settings, schedule: Callable, *,
              run_id: str, run_version: int, actor: str) -> str:
    """STUB — replace in B13b (Retry, DL-51). Not built in the shell: changes nothing.

    Returns the sentence the page shows. B13b adds the transition out of FAILED, stage_attempt 2,
    RUN_NOT_FAILED, RETRY_LIMIT_REACHED and RETRY_NOT_ALLOWED.
    """
    return "Retry is not built yet (block B13b). Start a new review from Filing rules."
