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


class SchemaNotAsExpected(RuntimeError):
    """The stored `units` table is not the one this code knows how to upgrade. Nothing was changed."""


# What the stored text of `units` ends its reason list with before the change, and with after it. The
# "after" text is the same, character for character, as schema.sql, so that an upgraded database and a
# new one store identical text (a test compares them).
_OLD_REASONS_END = "'demo failure')),"
_NEW_REASONS_END = ("'demo failure',\n                        'unexpected error', 'call limit')),"
                    "   -- the last two: DL-58, H-092")


def upgrade_failure_reasons(conn: sqlite3.Connection) -> str:
    """Let an EXISTING database accept the failure reasons 'unexpected error' and 'call limit' (DL-58).

    Why this is needed: the reasons are a CHECK on `units.failure_reason`. `CREATE TABLE IF NOT EXISTS`
    leaves an existing table alone, and SQLite cannot change a CHECK with ALTER TABLE. Without this, an old
    database would refuse the new reasons at the moment a review is already failing.

    Called from `create_app` only, NOT from `init_db`: the spike runner also calls `init_db`, on
    data/spike.db, and the spike never writes the new reasons, so that file keeps its old list on purpose.

    Returns what it did: "nothing to do", "rewrote the table definition" (way A, no row is touched) or
    "rebuilt the table" (way B, used only if this SQLite build refuses A). Raises SchemaNotAsExpected,
    having changed nothing, if the stored text is not the one expected.
    """
    conn.commit()                                       # no half-open transaction; the guards read first
    row = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'units'").fetchone()
    if row is None:
        return "nothing to do"                          # no table yet: init_db makes it, with the new list
    stored = row[0]
    if "'call limit'" in stored:
        return "nothing to do"
    if stored.count(_OLD_REASONS_END) != 1:
        raise SchemaNotAsExpected(
            "The `units` table in this database is not the one this version knows how to upgrade, so the "
            "app has not started and nothing was changed. Restore from a backup, or ask for help.")
    new_sql = stored.replace(_OLD_REASONS_END, _NEW_REASONS_END)
    try:
        _rewrite_definition(conn, new_sql)
        return "rewrote the table definition"
    except sqlite3.DatabaseError:                       # a defensive SQLite build refuses to edit sqlite_master
        conn.rollback()
        _rebuild_table(conn, new_sql)
        return "rebuilt the table"


def _rewrite_definition(conn: sqlite3.Connection, new_sql: str) -> None:
    """Way A: SQLite's documented way to LOOSEN a CHECK. Only the stored text of the table changes; no row
    is read or written. One transaction; the schema version is raised so that other connections reload."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        version = conn.execute("PRAGMA schema_version").fetchone()[0]
        conn.execute("PRAGMA writable_schema = ON")
        conn.execute("UPDATE sqlite_master SET sql = ? WHERE type = 'table' AND name = 'units'", (new_sql,))
        conn.execute(f"PRAGMA schema_version = {int(version) + 1}")
        conn.execute("PRAGMA writable_schema = OFF")
        # Rows are sqlite3.Row here (connect() sets row_factory), which never equals a plain tuple.
        if [tuple(r) for r in conn.execute("PRAGMA integrity_check")] != [("ok",)]:
            raise sqlite3.DatabaseError("integrity_check failed after rewriting the definition")
        conn.commit()
    except BaseException:
        conn.rollback()
        conn.execute("PRAGMA writable_schema = OFF")
        raise


def _rebuild_table(conn: sqlite3.Connection, new_sql: str) -> None:
    """Way B (fallback): new table, copy every row in rowid order, drop the old, rename. Foreign keys are
    off while it runs (SQLite requires that outside a transaction) and checked before COMMIT."""
    extras = [r[0] for r in conn.execute(     # indexes and triggers that live on `units` (none today)
        "SELECT sql FROM sqlite_master WHERE tbl_name = 'units' AND type IN ('index', 'trigger') "
        "AND sql IS NOT NULL")]
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute(new_sql.replace("CREATE TABLE units", "CREATE TABLE units_new", 1))
            conn.execute("INSERT INTO units_new SELECT * FROM units ORDER BY rowid")
            conn.execute("DROP TABLE units")
            conn.execute("ALTER TABLE units_new RENAME TO units")
            for sql in extras:
                conn.execute(sql)
            if conn.execute("PRAGMA foreign_key_check").fetchall():
                raise sqlite3.DatabaseError("foreign_key_check found a problem after rebuilding `units`")
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def _add_missing_trace_columns(conn: sqlite3.Connection) -> None:
    """Give an older database the trace columns added since (see TRACE_ADDED_COLUMNS). A database
    made from the current schema.sql already has them, so this does nothing there."""
    have = {row["name"] for row in conn.execute("PRAGMA table_info(trace)")}
    for name, definition in TRACE_ADDED_COLUMNS.items():
        if name not in have:
            conn.execute(f"ALTER TABLE trace ADD COLUMN {name} {definition}")
