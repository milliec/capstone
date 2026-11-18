"""Stores a stage's progress and outputs, and moves the run when the stage ends (SAD rule 9).

Rule 9 (DL-43, DL-46, DL-51): a stage stores its outputs ONCE, when it ends, in ONE transaction,
and only when every unit is valid. Before it writes anything, the store checks that the run is
still ACTIVE, in that stage's `*_RUNNING` phase, and on the same stage attempt. If not (the stage
failed, the run ended, or a retry started since), the outputs are DISCARDED: nothing reaches a
business table, and one audit entry says so. A failed stage therefore stores nothing, and a retry
starts clean.

Unit lines (`add_units`, `mark_unit`) are progress only, so run status can show them one by one.
"""

import sqlite3

from backend.services.audit import now_utc, write_audit

NEXT_GATE = {"A": "AT_G1", "B": "AT_G2", "C": "AT_G3"}


def add_units(conn: sqlite3.Connection, run: dict, stage: str,
              units: list[tuple[str, str]]) -> None:
    """Add one 'waiting' line per unit of this stage attempt."""
    conn.executemany(
        """INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status)
           VALUES (?, ?, ?, ?, ?, ?, 'waiting')""",
        [(run["run_id"], stage, run["stage_attempt"], unit_id, run["fund_id"], label)
         for unit_id, label in units],
    )
    conn.commit()


def mark_unit(conn: sqlite3.Connection, run: dict, stage: str, unit_id: str, status: str,
              failure_reason: str | None = None) -> None:
    """Set one unit's status (and reason, if it failed)."""
    attempts_add = 1 if status in ("done", "failed") else 0
    conn.execute(
        """UPDATE units SET status = ?, failure_reason = ?, attempts = attempts + ?
           WHERE run_id = ? AND stage = ? AND stage_attempt = ? AND unit_id = ?""",
        (status, failure_reason, attempts_add, run["run_id"], stage, run["stage_attempt"],
         unit_id),
    )
    conn.commit()


def _is_current(conn: sqlite3.Connection, run_id: str, stage: str, stage_attempt: int) -> dict | None:
    """The run row if it is still ACTIVE, in this stage's phase and on this attempt, else None."""
    row = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if (row and row["status"] == "ACTIVE" and row["phase"] == f"{stage}_RUNNING"
            and row["stage_attempt"] == stage_attempt):
        return dict(row)
    return None


def _discard(conn: sqlite3.Connection, run_id: str, fund_id: str, stage: str,
             stage_attempt: int, what: str) -> None:
    """Record that output arrived too late and was not stored. (Its cost still counts, B3.)"""
    write_audit(conn, fund_id=fund_id, actor=f"stage {stage}", event_type="system", run_id=run_id,
                subject_id=run_id,
                reason=f"{what} from stage {stage} attempt {stage_attempt} discarded: the stage "
                       "had already failed, the review had ended, or a retry had started")
    conn.commit()


def store_stage_outputs(conn: sqlite3.Connection, *, run_id: str, fund_id: str, stage: str,
                        stage_attempt: int, outputs: dict) -> bool:
    """Rule 9: store the stage's outputs and move the run to the next gate, all or nothing.

    Returns True when stored. Returns False when the output was late (see the module note): then
    nothing is stored and the run is left as it is. If anything goes wrong while storing, the whole
    transaction is rolled back and the error is raised, so there is never half a stage.
    """
    conn.commit()   # nothing of ours is pending; BEGIN IMMEDIATE needs no open transaction
    conn.execute("BEGIN IMMEDIATE")   # the write lock: no other request changes the run meanwhile
    try:
        run = _is_current(conn, run_id, stage, stage_attempt)
        if run is None:
            conn.rollback()
            _discard(conn, run_id, fund_id, stage, stage_attempt, "Output")
            return False
        unfinished = conn.execute(
            "SELECT COUNT(*) FROM units WHERE run_id = ? AND stage = ? AND stage_attempt = ? "
            "AND status != 'done'", (run_id, stage, stage_attempt)).fetchone()[0]
        if unfinished:
            raise ValueError(f"stage {stage} cannot store: {unfinished} unit(s) are not done")

        _STORERS[stage](conn, run, outputs)

        if stage == "C":    # one complete calendar per run (rule 9, CR-011)
            conn.execute(
                """INSERT INTO calendar_versions (calendar_id, run_id, fund_id, version,
                                                  generated_at) VALUES (?, ?, ?, 1, ?)""",
                (f"CAL-{run_id}", run_id, fund_id, now_utc()))
            _store_entries(conn, run, outputs["entries"])
        conn.execute("UPDATE runs SET phase = ? WHERE run_id = ?", (NEXT_GATE[stage], run_id))
        write_audit(conn, fund_id=fund_id, actor=f"stage {stage}", event_type="system",
                    run_id=run_id, subject_id=run_id, reason=f"Stage {stage} finished (stand-in)")
        conn.commit()
        return True
    except BaseException:
        conn.rollback()
        raise


def _store_a(conn: sqlite3.Connection, run: dict, outputs: dict) -> None:
    """Stage A: the paragraphs loaded, the rows drafted, and each row's quote check and flags."""
    for p in outputs["paragraphs"]:
        conn.execute("INSERT INTO paragraphs (run_id, paragraph_id, fund_id, document_id, "
                     "paragraph_text) VALUES (?, ?, ?, ?, ?)",
                     (run["run_id"], p["paragraph_id"], run["fund_id"], p["document_id"],
                      p["text"]))
    for r in outputs["rows"]:
        # `offset` is stored as JSON text (B3 step 5): B4's date engine reads it as data, and the
        # pages turn it into words (backend/domain/wording.py).
        conn.execute(
            """INSERT INTO rows (row_id, run_id, fund_id, source_paragraph_id, obligation_name,
                                 frequency, anchor, "offset", recipient_code, responsible_role,
                                 applicability_rule, business_day_rule, quote, origin)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (r["row_id"], run["run_id"], run["fund_id"], r["source_paragraph_id"],
             r["obligation_name"], r["frequency"], r["anchor"], r["offset"], r["recipient_code"],
             r["responsible_role"], r.get("applicability_rule"), r["business_day_rule"],
             r["quote"], r["origin"]))
        conn.execute("INSERT INTO quote_checks (row_id, fund_id, result, mismatch) "
                     "VALUES (?, ?, ?, ?)",
                     (r["row_id"], run["fund_id"], r["quote_check"], r.get("mismatch")))
        for f in r.get("flags", []):
            conn.execute(
                """INSERT INTO flags (row_id, run_id, fund_id, flag_type, explanation, field,
                                      row_value, quote_says, other_paragraph_id, other_quote)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["row_id"], run["run_id"], run["fund_id"], f["flag_type"], f["explanation"],
                 f.get("field"), f.get("row_value"), f.get("quote_says"),
                 f.get("other_paragraph_id"), f.get("other_quote")))


def _store_b(conn: sqlite3.Connection, run: dict, outputs: dict) -> None:
    """Stage B: one verdict per approved row."""
    for v in outputs["verdicts"]:
        conn.execute(
            """INSERT INTO verdicts (verdict_id, row_id, fund_id, verdict, reasoning,
                                     cited_fact_ids, missing_information)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (v["verdict_id"], v["row_id"], run["fund_id"], v["verdict"], v["reasoning"],
             v["cited_fact_ids"], v.get("missing_information")))


def _store_c(conn: sqlite3.Connection, run: dict, outputs: dict) -> None:
    """Stage C's entries are stored right after the calendar version exists (see above)."""


def _store_entries(conn: sqlite3.Connection, run: dict, entries: list[dict]) -> None:
    for e in entries:
        conn.execute(
            """INSERT INTO calendar_entries (calendar_id, entry_id, row_id, fund_id, period,
                                             unadjusted_date, due_date, business_day_rule, moved,
                                             precautionary, open_question_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"CAL-{run['run_id']}", e["entry_id"], e["row_id"], run["fund_id"], e["period"],
             e["unadjusted_date"], e["due_date"], e["business_day_rule"], int(e["moved"]),
             int(e["precautionary"]), e["open_question_id"]))


_STORERS = {"A": _store_a, "B": _store_b, "C": _store_c}


def fail_stage(conn: sqlite3.Connection, run: dict, stage: str, unit_id: str,
               failure_reason: str) -> bool:
    """A unit failed: the run becomes FAILED and keeps its phase (DL-46). Stores nothing (rule 9).
    Returns True if it failed the run, False if the run had already moved on.

    Like the store, it first checks that the run is still ACTIVE in this stage and attempt; a
    failure that arrives after a retry started must not fail the new attempt. Since B3 step 6 the
    check and the change are ONE locked transaction (BEGIN IMMEDIATE), because the stage timer
    calls this from its own thread: without the lock, the timer could see "still running", the
    stage could then store and open its gate, and the timer would fail a run that had finished.
    If the run has moved on, nothing changes (not even the unit line) and one audit entry says so.
    """
    conn.commit()
    conn.execute("BEGIN IMMEDIATE")
    try:
        if _is_current(conn, run["run_id"], stage, run["stage_attempt"]) is None:
            conn.rollback()
            _discard(conn, run["run_id"], run["fund_id"], stage, run["stage_attempt"],
                     f"A failure ({failure_reason})")
            return False
        conn.execute(
            """UPDATE units SET status = 'failed', failure_reason = ?, attempts = attempts + 1
               WHERE run_id = ? AND stage = ? AND stage_attempt = ? AND unit_id = ?""",
            (failure_reason, run["run_id"], stage, run["stage_attempt"], unit_id))
        conn.execute("UPDATE runs SET status = 'FAILED' WHERE run_id = ?", (run["run_id"],))
        write_audit(conn, fund_id=run["fund_id"], actor=f"stage {stage}", event_type="system",
                    run_id=run["run_id"], subject_id=unit_id, reason=failure_reason)
        conn.commit()
        return True
    except BaseException:
        conn.rollback()
        raise
