"""Opens the SQLite file at DATABASE_PATH and applies the schema on first start (SAD §5)."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


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
        conn.commit()
    finally:
        conn.close()
