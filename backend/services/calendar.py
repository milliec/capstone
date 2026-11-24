"""The calendar: G3 page data and the published calendar the General Partner reads (CR-012).

The entries are the date engine's (B4, backend/domain/dates.py), stored by stage C. The published
calendar lookup: the newest publications row for the fund is the live one (DL-50 item 5), leaving out
a publication of an evaluation run (DL-60): see `_live_publication`.
"""

import sqlite3

from backend.services import decisions, runs

DIRECTION = {"roll_forward": "following working day", "roll_backward": "preceding working day"}

# The "why" line's first word, from the rule's frequency in words (B4: "Annually rule" and
# "On occurrence rule" did not read as English).
WHY_KIND = {"monthly": "Monthly", "quarterly": "Quarterly", "annually": "Annual",
            "on occurrence": "Event-triggered"}


def _entries(conn: sqlite3.Connection, run: dict) -> list[dict]:
    """The run's calendar entries, read from what stage C stored, with the fields the pages read
    (H-036 V-10, V-11). The dates are the date engine's (B4).

    Each entry is joined to its rule (as G1 shows it) and to what the specialist chose there. The
    page prints these words as sent and works nothing out.
    """
    g1 = {r["row_id"]: r for r in decisions.get_g1_view(conn, run)["rows"]}
    stored = conn.execute(
        """SELECT e.* FROM calendar_entries e JOIN calendar_versions c
           ON c.calendar_id = e.calendar_id WHERE c.run_id = ? ORDER BY e.due_date, e.rowid""",
        (run["run_id"],))
    entries = []
    for e in stored:
        row = g1[e["row_id"]]
        chosen = row["decided"]["who_files"] if row["decided"] else None
        moved = bool(e["moved"])
        entries.append({
            "entry_id": e["entry_id"], "row_id": e["row_id"], "period": e["period"],
            "due_date": e["due_date"], "moved": moved, "precautionary": bool(e["precautionary"]),
            "open_question_id": e["open_question_id"],
            "obligation_name": row["obligation_name"],
            "who_files_label": chosen or ("Not known" if row["needs_who_files"]
                                          else row["responsible_role"].capitalize()),
            "recipient_name": row["recipient_name"],
            "why": f"{WHY_KIND.get(row['frequency'], row['frequency'].capitalize())} rule: "
                   f"due {row['due']}.",
            "source_paragraph_id": row["source_paragraph_id"],
            "source_document": row["paragraph"]["document"],
            "quote": row["quote"],
            "marks": {"moved": ({"from_date": e["unadjusted_date"], "to_date": e["due_date"],
                                 "direction": DIRECTION.get(e["business_day_rule"], "next working day")}
                                if moved else None)},
        })
    return entries


def _live_publication(conn: sqlite3.Connection, fund_id: str, *,
                      not_run_id: str | None = None) -> dict | None:
    """THE rule for "the live publication" (DL-60, H-099): the newest `publications` row for the fund whose
    run is NOT an evaluation run. Page 7 and the "previous publication" line at G3 both ask here, so the
    rule lives in one place. An evaluation run still publishes (EC-R2); it is just never the live calendar.

    `is_evaluation_run` is the only definition of an evaluation run (DL-59), so it is called here, not
    copied into SQL. `not_run_id` leaves out one run (the run whose G3 page is being read).
    """
    rows = conn.execute(
        """SELECT p.*, c.run_id, r.agents_mode, r.spend_activity, r.started_by
           FROM publications p
           JOIN calendar_versions c ON c.calendar_id = p.calendar_id
           JOIN runs r ON r.run_id = c.run_id
           WHERE p.fund_id = ? ORDER BY p.publication_id DESC""", (fund_id,))
    for row in rows:
        pub = dict(row)
        if pub["run_id"] != not_run_id and not runs.is_evaluation_run(pub):
            for field in ("spend_activity", "started_by"):    # read only to apply the rule; not page data
                del pub[field]
            return pub
    return None


def _previous_publication_at(conn: sqlite3.Connection, run: dict) -> str | None:
    """When the calendar the General Partner saw before this run's was published, if any."""
    pub = _live_publication(conn, run["fund_id"], not_run_id=run["run_id"])
    return pub["published_at"] if pub else None


def get_g3_view(conn: sqlite3.Connection, run: dict) -> dict:
    """The calendar to check and publish at G3, read from what stage C stored (dates: STUB, B4).

    H-036 V-10: stage, the two lists with their words, the previous publication and the outcome
    of an ended review. The two ID lists are what the publish form posts back (CR-028).
    """
    cal = conn.execute("SELECT calendar_id FROM calendar_versions WHERE run_id = ?",
                       (run["run_id"],)).fetchone()
    rejected = decisions.rejected_rows(conn, run)
    unused = decisions.unused_paragraphs(conn, run)
    if run["status"] == "COMPLETED":
        outcome = {"at": run["published_at"], "reason": None}
    else:
        outcome = run["ended"] if run["status"] == "DECLINED" else None
    return {
        "calendar_id": cal["calendar_id"] if cal else None,
        "entries": _entries(conn, run) if cal else [],
        "stage": runs.page_stage(run, "g3"),
        "rejected_rows": rejected,
        "rejected_row_ids": [r["row_id"] for r in rejected],
        "unused_paragraphs": unused,
        "uncited_paragraph_ids": [p["paragraph_id"] for p in unused],
        "previous_publication_at": _previous_publication_at(conn, run),
        "outcome": outcome,
    }


def get_published_calendar(conn: sqlite3.Connection, fund_id: str) -> dict | None:
    """The live calendar (newest publication of a run that is not an evaluation run, DL-60), or None:
    'being prepared'. If only evaluation runs have published, that is still None (DL-27, EC-014)."""
    pub = _live_publication(conn, fund_id)
    if pub is None:
        return None
    pub["entries"] = _entries(conn, runs.get_run(conn, pub["run_id"]))
    return pub
