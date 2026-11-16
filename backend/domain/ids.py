"""Identifier schemes (SAD §4 "Identifiers and versions"). Deterministic code, no model client.

App shell: only the run ID. B2/B3 add ROW- and ENT- here.
"""

import sqlite3
from datetime import date


def new_run_id(conn: sqlite3.Connection, today: date) -> str:
    """RUN-<yyyymmdd>-<n>, where n counts the runs already started that day, plus one."""
    prefix = f"RUN-{today:%Y%m%d}-"
    (count,) = conn.execute(
        "SELECT COUNT(*) FROM runs WHERE run_id LIKE ?", (prefix + "%",)
    ).fetchone()
    return f"{prefix}{count + 1}"


def run_id_from_child(child_id: str) -> str:
    """ROW-RUN-20261116-1-3 → RUN-20261116-1 (also VER-, CAL-). The run is in the middle."""
    _, _, rest = child_id.partition("-")      # drop the "ROW" / "VER" / "CAL" prefix
    if rest.count("-") >= 3:                  # RUN-yyyymmdd-n-k: drop the trailing "-k"
        rest = rest.rsplit("-", 1)[0]
    return rest
