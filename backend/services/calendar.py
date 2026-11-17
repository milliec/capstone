"""The calendar: G3 page data and the published calendar the General Partner reads (CR-012).

STUBS for the entries: the date engine is B4, so the entries are placeholders. The published
calendar lookup is real: the newest publications row for the fund is the live one (DL-50 item 5).
"""

import sqlite3

from backend.services import decisions, runs
from backend.stand_in import shell_data


def _entries(conn: sqlite3.Connection, run: dict) -> list[dict]:
    """The run's calendar entries with the fields the pages read (H-036 V-10, V-11). STUB: B4.

    Each entry is a placeholder date joined to its rule (as G1 shows it) and to what the
    specialist chose there. The page prints these words as sent and works nothing out.
    """
    g1 = {r["n"]: r for r in decisions.get_g1_view(conn, run)["rows"]}
    entries = []
    for e in shell_data.ENTRIES:
        row = g1[e["row_n"]]
        chosen = row["decided"]["who_files"] if row["decided"] else None
        silent = row["needs_who_files"]
        offset = row["offset"].lstrip("+")
        entries.append({
            **e, "row_id": row["row_id"], "obligation_name": row["obligation_name"],
            "who_files_label": chosen or ("Not known" if silent else row["responsible_role"].capitalize()),
            "recipient_name": row["recipient_name"],
            "why": f"{row['frequency'].capitalize()} rule: due {offset} after {row['anchor']}.",
            "source_paragraph_id": row["source_paragraph_id"],
            "source_document": row["paragraph"]["document"],
            "quote": row["quote"],
            "marks": {"moved": ({"from_date": e["moved_from"], "to_date": e["due_date"],
                                 "direction": "following working day"} if e["moved"] else None)},
        })
    return entries


def _previous_publication_at(conn: sqlite3.Connection, run: dict) -> str | None:
    """When the calendar the General Partner saw before this run's was published, if any."""
    row = conn.execute(
        """SELECT p.published_at FROM publications p
           JOIN calendar_versions c ON c.calendar_id = p.calendar_id
           WHERE p.fund_id = ? AND c.run_id != ? ORDER BY p.publication_id DESC LIMIT 1""",
        (run["fund_id"], run["run_id"])).fetchone()
    return row["published_at"] if row else None


def get_g3_view(conn: sqlite3.Connection, run: dict) -> dict:
    """STUB — replace in B2/B4. The calendar to check and publish at G3 (placeholder entries).

    H-036 V-10: stage, the two lists with their words, the previous publication and the outcome
    of an ended review. The two ID lists are what the publish form posts back (CR-028).
    """
    cal = conn.execute("SELECT calendar_id FROM calendar_versions WHERE run_id = ?",
                       (run["run_id"],)).fetchone()
    rejected = decisions.rejected_rows(conn, run)
    unused = decisions.stub_unused_paragraphs()
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
        "unused_paragraphs": unused,                                      # B3: from the loader
        "uncited_paragraph_ids": [p["paragraph_id"] for p in unused],
        "previous_publication_at": _previous_publication_at(conn, run),
        "outcome": outcome,
    }


def get_published_calendar(conn: sqlite3.Connection, fund_id: str) -> dict | None:
    """The live calendar (newest publication for the fund), or None: 'being prepared'."""
    pub = conn.execute(
        """SELECT p.*, c.run_id, r.agents_mode FROM publications p
           JOIN calendar_versions c ON c.calendar_id = p.calendar_id
           JOIN runs r ON r.run_id = c.run_id
           WHERE p.fund_id = ? ORDER BY p.publication_id DESC LIMIT 1""", (fund_id,)).fetchone()
    if pub is None:
        return None
    pub = dict(pub)
    pub["entries"] = _entries(conn, runs.get_run(conn, pub["run_id"]))  # STUB: B4 reads calendar_entries
    return pub
