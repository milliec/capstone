"""Rule 9 (SAD run-state rule 9, DL-43, DL-46, DL-51): a stage stores its outputs once, when it ends,
in one transaction, only when every unit is valid, and only if the run is still ACTIVE, in that
stage's phase and on the same stage attempt. Anything else is discarded and stores nothing."""

import pytest

from backend.db.connection import connect, init_db
from backend.runtime import stages
from backend.services import FUND_ID, runs, stage_store
from tests import flow

def stand_in_outputs(conn, settings, run):
    """Stage A's outputs, built the way the stage builds them but not stored (B3 step 5).
    It also adds stage A's unit lines, all done, as a finished stage would have them."""
    return stages._stage_a(conn, settings, run)


TABLES = ("paragraphs", "rows", "quote_checks", "verdicts", "calendar_versions", "calendar_entries")


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _counts(conn):
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}


def _running_stage_a(conn, settings, **switches):
    """A review with stage A running: units added and done, nothing stored yet."""
    run_id = runs.start_run(conn, settings, lambda *a, **k: None, fund_id=FUND_ID,
                            started_by="specialist-1", demo_planted_row=switches.get("demo", False),
                            demo_fail_step1=False)
    run = runs.get_run(conn, run_id)
    stage_store.add_units(conn, run, "A", [("DOC-STUB-1", "Doc 1")])
    stage_store.mark_unit(conn, run, "A", "DOC-STUB-1", "done")
    return run


def test_a_stage_stores_everything_together_and_moves_to_the_gate(conn, settings):
    run = _running_stage_a(conn, settings)
    assert _counts(conn)["rows"] == 0                     # nothing is stored while the stage runs
    stored = stage_store.store_stage_outputs(
        conn, run_id=run["run_id"], fund_id=FUND_ID, stage="A", stage_attempt=1,
        outputs=stand_in_outputs(conn, settings, run))
    assert stored is True
    counts = _counts(conn)
    assert counts["rows"] == 6 and counts["quote_checks"] == 6 and counts["paragraphs"] == 13
    assert runs.get_run(conn, run["run_id"])["phase"] == "AT_G1"


def test_if_anything_fails_midway_nothing_is_stored(conn, settings):
    """All or nothing: a bad second row rolls back the paragraphs and the first row too."""
    run = _running_stage_a(conn, settings)
    outputs = stand_in_outputs(conn, settings, run)
    outputs["rows"][1]["row_id"] = outputs["rows"][0]["row_id"]        # duplicate row ID
    with pytest.raises(Exception):
        stage_store.store_stage_outputs(conn, run_id=run["run_id"], fund_id=FUND_ID, stage="A",
                                        stage_attempt=1, outputs=outputs)
    assert all(count == 0 for count in _counts(conn).values())
    assert runs.get_run(conn, run["run_id"])["phase"] == "A_RUNNING"   # and the run did not move


def test_a_stage_with_an_unfinished_unit_stores_nothing(conn, settings):
    run = _running_stage_a(conn, settings)
    # The unit list already has one finished unit; add one that never finished.
    conn.execute("INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status) "
                 "VALUES (?, 'A', 1, 'DOC-STUB-2', ?, 'Doc 2', 'waiting')", (run["run_id"], FUND_ID))
    conn.commit()
    with pytest.raises(ValueError):
        stage_store.store_stage_outputs(conn, run_id=run["run_id"], fund_id=FUND_ID, stage="A",
                                        stage_attempt=1, outputs=stand_in_outputs(conn, settings, run))
    assert all(count == 0 for count in _counts(conn).values())


@pytest.mark.parametrize("change", [
    "UPDATE runs SET status = 'FAILED'",                   # the stage already failed
    "UPDATE runs SET status = 'ABANDONED'",                # the review ended
    "UPDATE runs SET stage_attempt = 2",                   # a retry started since (DL-51)
    "UPDATE runs SET phase = 'AT_G1'",                     # the run moved on
])
def test_late_output_is_discarded_and_stores_nothing(conn, settings, change):
    run = _running_stage_a(conn, settings)
    outputs = stand_in_outputs(conn, settings, run)
    conn.execute(change)
    conn.commit()
    before = runs.get_run(conn, run["run_id"])
    stored = stage_store.store_stage_outputs(conn, run_id=run["run_id"], fund_id=FUND_ID,
                                             stage="A", stage_attempt=1, outputs=outputs)
    assert stored is False
    assert all(count == 0 for count in _counts(conn).values())
    after = runs.get_run(conn, run["run_id"])
    assert (after["status"], after["phase"], after["stage_attempt"]) == \
        (before["status"], before["phase"], before["stage_attempt"])        # the run was not touched
    note = conn.execute("SELECT reason FROM audit_log WHERE event_type = 'system' "
                        "ORDER BY audit_id DESC LIMIT 1").fetchone()[0]
    assert "discarded" in note and "attempt 1" in note


def test_a_failure_from_an_old_attempt_does_not_fail_the_new_one(conn, settings):
    run = _running_stage_a(conn, settings)
    conn.execute("UPDATE runs SET stage_attempt = 2")      # a retry is under way
    conn.commit()
    stage_store.fail_stage(conn, run, "A", "DOC-STUB-1", "model service")   # attempt-1 news
    assert runs.get_run(conn, run["run_id"])["status"] == "ACTIVE"


def test_a_failed_stage_stores_nothing(settings, specialist_client, db):
    """The failure demo: unit 1 fails, so no rule, quote check or paragraph is ever stored."""
    specialist_client.post("/specialist/runs", data={"demo_fail_step1": "true"})
    run = runs.list_runs(db, FUND_ID)[0]
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")
    assert all(count == 0 for count in _counts(db).values())


def test_stage_b_makes_verdicts_only_for_approved_rules_and_c_entries_only_for_applies(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    flow.approve_rule(conn, run_id, 1)
    flow.reject_rule(conn, run_id, 2)
    for n in (3, 4, 5, 6):
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    verdicts = [r[0] for r in conn.execute("SELECT verdict_id FROM verdicts ORDER BY rowid")]
    assert verdicts == [f"VER-{run_id}-{n}" for n in (1, 3, 4, 5, 6)]   # rule 2 was rejected
    flow.answer(conn, run_id, 1, "confirm", "applies")
    flow.answer(conn, run_id, 3, "confirm", "applies")
    flow.answer(conn, run_id, 4, "decide", "applies", "Registered after all")
    flow.answer(conn, run_id, 5, "confirm", "applies")
    flow.answer(conn, run_id, 6, "override", "applies", "Applies after all")
    flow.finish_g2(conn, settings, run_id)
    # Every rule whose final answer is "applies" has entries (B4); rule 2 was rejected at G1.
    entries = [r[0] for r in conn.execute("SELECT row_id FROM calendar_entries")]
    assert sorted({_n for _n in (int(e.rsplit("-", 1)[1]) for e in entries)}) == [1, 3, 4, 5, 6]
    assert len(entries) == 12 + 1 + 4 + 1 + 1     # monthly, annual, quarterly, event, fixed day
    assert conn.execute("SELECT COUNT(*) FROM calendar_versions").fetchone()[0] == 1
