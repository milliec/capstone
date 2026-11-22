"""Opens the SQLite file at DATABASE_PATH and applies the schema on first start (SAD §5)."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")

# Columns added to `trace` after the first release of the table (B3 step 7b PR 5; `request_path`,
# spike fix step D). `CREATE TABLE
# IF NOT EXISTS` leaves an existing table alone, so a database made before the change gets them
# here. ADDITIVE ONLY: a column is added with a default, never renamed or dropped.
TRACE_ADDED_COLUMNS = {
    "stop_reason": "TEXT NOT NULL DEFAULT ''",
    "provider_error": "TEXT",
    "cost_estimated": "INTEGER NOT NULL DEFAULT 0 CHECK (cost_estimated IN (0, 1))",
    "off_pinned_setting": "INTEGER NOT NULL DEFAULT 0 CHECK (off_pinned_setting IN (0, 1))",
    "request_path": "TEXT NOT NULL DEFAULT ''",      # spike fix, step D
}


def connect(database_path: Path) -> sqlite3.Connection:
    """Open one connection. Each request or background task opens its own and closes it.

    - row_factory = sqlite3.Row lets code read columns by name: row["status"].
    - foreign_keys is OFF by default in SQLite, so it is switched on for every connection.
    - check_same_thread=False: FastAPI may finish a request on a different thread.
    """
    conn = sqlite3.connect(database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(database_path: Path) -> None:
    """Create the folder and the tables if they do not exist yet. Safe to run every start."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(database_path)
    try:
        conn.executescript(SCHEMA.read_text())
        _add_missing_trace_columns(conn)
        conn.commit()
    finally:
        conn.close()


def _add_missing_trace_columns(conn: sqlite3.Connection) -> None:
    """Give an older database the trace columns added since (see TRACE_ADDED_COLUMNS). A database
    made from the current schema.sql already has them, so this does nothing there."""
    have = {row["name"] for row in conn.execute("PRAGMA table_info(trace)")}
    for name, definition in TRACE_ADDED_COLUMNS.items():
        if name not in have:
            conn.execute(f"ALTER TABLE trace ADD COLUMN {name} {definition}")
