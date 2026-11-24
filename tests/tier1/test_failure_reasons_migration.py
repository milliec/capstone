"""H-091 part 2: an EXISTING database learns the two new failure reasons (DL-58). Tier 1.

The problem: `units.failure_reason` carries a CHECK, and CREATE TABLE IF NOT EXISTS leaves an old table
alone, so an old database would refuse 'unexpected error' and 'call limit'. `upgrade_failure_reasons`
fixes that at start-up, from create_app (NOT from init_db, which the spike runner also calls, so
data/spike.db is never changed).

Every database here is a temporary COPY-LIKE file made in the test's own folder. No test opens
data/app.db or data/spike.db (tests/conftest.py also points the default path somewhere else).

  A. the normal way: rewrite the stored table text (rows are not touched);
  B. the fallback, when a SQLite build refuses A: rebuild the table.
"""

import sqlite3

import pytest

from backend.db import connection
from backend.db.connection import SchemaNotAsExpected, connect, init_db, upgrade_failure_reasons
from backend.main import create_app
from backend.services import runs
from tests import flow

NEW_LINES = ("'demo failure',\n                        'unexpected error', 'call limit')),"
             "   -- the last two: DL-58, H-092")
OLD_LINES = "'demo failure')),"


def _old_schema_text():
    text = connection.SCHEMA.read_text()
    assert NEW_LINES in text, "schema.sql no longer has the lines this test takes back out"
    return text.replace(NEW_LINES, OLD_LINES)


@pytest.fixture
def old_db(settings):
    """A database made BEFORE the change (old CHECK), with a stand-in review and a demo-failure review."""
    path = settings.database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(path)
    raw.executescript(_old_schema_text())
    raw.commit()
    raw.close()
    init_db(path)                                   # adds nothing to `units`: the old table stays
    conn = connect(path)
    flow.start_to_g1(conn, settings)
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")
    conn.commit()
    runs.start_run(conn, settings, flow.run_now, fund_id=flow.FUND_ID, started_by=flow.SPECIALIST,
                   demo_planted_row=False, demo_fail_step1=True)
    conn.close()
    return path


def _units_sql(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT sql FROM sqlite_master WHERE name = 'units'").fetchone()[0]
    finally:
        conn.close()


def _digest(path):
    """Every table's rows in rowid order, plus the names of every table, index and trigger."""
    conn = sqlite3.connect(path)
    try:
        names = conn.execute("SELECT type, name FROM sqlite_master ORDER BY type, name").fetchall()
        tables = [n for t, n in names if t == "table" and not n.startswith("sqlite_")]
        data = {t: conn.execute(f"SELECT rowid, * FROM {t} ORDER BY rowid").fetchall() for t in tables}
        return names, data
    finally:
        conn.close()


def _insert_unit_with(path, reason):
    conn = connect(path)
    try:
        run = conn.execute("SELECT run_id, fund_id FROM runs LIMIT 1").fetchone()
        conn.execute("INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status, "
                     "failure_reason) VALUES (?, 'B', 1, ?, ?, 'x', 'failed', ?)",
                     (run["run_id"], f"U-{reason}", run["fund_id"], reason))
        conn.commit()
    finally:
        conn.close()


def _healthy(path):
    conn = sqlite3.connect(path)
    try:
        assert conn.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conn.close()


def test_the_old_database_really_refuses_the_new_reasons_first(old_db):
    assert "'call limit'" not in _units_sql(old_db)
    with pytest.raises(sqlite3.IntegrityError):
        _insert_unit_with(old_db, "call limit")


def test_a_rewrites_the_definition_and_leaves_every_row_alone(old_db):
    before = _digest(old_db)
    conn = connect(old_db)
    try:
        assert upgrade_failure_reasons(conn) == "rewrote the table definition"
    finally:
        conn.close()
    assert _digest(old_db) == before                      # every row, in the same order; same triggers
    _healthy(old_db)
    _insert_unit_with(old_db, "unexpected error")
    _insert_unit_with(old_db, "call limit")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_unit_with(old_db, "banana")


def test_after_a_the_stored_text_is_the_same_as_a_fresh_database(old_db, tmp_path):
    conn = connect(old_db)
    upgrade_failure_reasons(conn)
    conn.close()
    fresh = tmp_path / "fresh.db"
    init_db(fresh)
    assert _units_sql(old_db) == _units_sql(fresh)


def test_a_second_run_does_nothing(old_db, tmp_path):
    conn = connect(old_db)
    upgrade_failure_reasons(conn)
    once = _units_sql(old_db)
    assert upgrade_failure_reasons(conn) == "nothing to do"
    conn.close()
    assert _units_sql(old_db) == once


def test_a_fresh_database_needs_nothing(settings):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    try:
        assert upgrade_failure_reasons(conn) == "nothing to do"
    finally:
        conn.close()


def test_a_table_that_is_not_what_was_expected_is_refused_and_left_alone(old_db):
    """No `'demo failure')),` exactly once in the stored text → stop, change nothing."""
    raw = sqlite3.connect(old_db)
    raw.execute("PRAGMA writable_schema = ON")
    raw.execute("UPDATE sqlite_master SET sql = replace(sql, ?, ?) WHERE name = 'units'",
                (OLD_LINES, "'demo failure', 'surprise')),"))
    raw.commit()
    raw.close()
    before = _digest(old_db), _units_sql(old_db)
    conn = connect(old_db)
    try:
        with pytest.raises(SchemaNotAsExpected):
            upgrade_failure_reasons(conn)
    finally:
        conn.close()
    assert (_digest(old_db), _units_sql(old_db)) == before


def test_b_rebuilds_the_table_when_the_build_refuses_a(old_db, monkeypatch):
    def refuse(conn, new_sql):
        raise sqlite3.DatabaseError("table sqlite_master may not be modified")
    monkeypatch.setattr(connection, "_rewrite_definition", refuse)
    before_names, before_data = _digest(old_db)
    conn = connect(old_db)
    try:
        assert upgrade_failure_reasons(conn) == "rebuilt the table"
    finally:
        conn.close()
    after_names, after_data = _digest(old_db)
    assert after_names == before_names                    # same tables, indexes and triggers
    assert after_data == before_data                      # same rows, same row numbers
    _healthy(old_db)
    _insert_unit_with(old_db, "call limit")
    with pytest.raises(sqlite3.IntegrityError):
        _insert_unit_with(old_db, "banana")
    conn = connect(old_db)
    try:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1     # switched back on
    finally:
        conn.close()


def test_create_app_upgrades_an_old_database_at_start_up(old_db, settings):
    create_app(settings)
    assert "'call limit'" in _units_sql(old_db)
    _insert_unit_with(old_db, "unexpected error")


def test_init_db_alone_does_not_migrate(old_db):
    """The spike runner calls init_db on data/spike.db; that file must keep the old list on purpose."""
    init_db(old_db)
    assert "'call limit'" not in _units_sql(old_db)
