"""The calendar: G3 page data and the published calendar the General Partner reads (CR-012).

STUBS for the entries: the date engine is B4, so the entries are placeholders. The published
calendar lookup is real: the newest publications row for the fund is the live one (DL-50 item 5).
"""

import sqlite3

from backend.stand_in import shell_data


def _placeholder_entries(run_id: str) -> list[dict]:
    names = {r["n"]: r["obligation_name"] for r in shell_data.ROWS}
    return [{**e, "row_id": f"ROW-{run_id}-{e['row_n']}",
             "obligation_name": names[e["row_n"]]} for e in shell_data.ENTRIES]


def get_g3_view(conn: sqlite3.Connection, run: dict) -> dict:
    """STUB — replace in B2/B4. The calendar to check and publish at G3 (placeholder entries)."""
    cal = conn.execute("SELECT calendar_id FROM calendar_versions WHERE run_id = ?",
                       (run["run_id"],)).fetchone()
    return {
        "calendar_id": cal["calendar_id"] if cal else None,
        "entries": _placeholder_entries(run["run_id"]) if cal else [],
        "rejected_row_ids": [],        # B2: rows with a reject decision
        "uncited_paragraph_ids": [],   # B3: paragraphs no non-rejected row cites
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
    pub["entries"] = _placeholder_entries(pub["run_id"])  # STUB: B4 reads calendar_entries
    return pub
