"""H-091 part 4 (P-5, DL-58): the web path stops at the real-call cap, reason `call limit`. Tier 1.

Before this, only the spike command checked the 70-call cap (EC-R10); a review run through the web app could
spend past it. Now `_run_unit` counts the activity's real calls over BOTH database files (the spike's and the
app's, `harness.count_real_calls`) before each real call, and at or over the cap it fails the unit with
`call limit` and starts no call.

No real call, no key, no real database: the app database and the spike database here are throwaway files
(tests/conftest.py also points the stages away from the real data/spike.db), and every request goes to the
fake OpenAI. Seeding uses `make_db` from test_call_count.py, the same helper that tests the count itself.
"""

from pathlib import Path

import pytest

from backend.db.connection import connect
from backend.runtime import harness, spike, stages
from backend.services import FUND_ID, runs
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY
from tests.tier1.test_call_count import make_db
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key

REAL_COUNTING_DATABASES = stages._counting_databases        # taken at import: before any fixture patches it

CALL_LIMIT = "The limit on real model calls for this kind of review was reached, so no further call was made"


def _settings(tmp_path, activity="spike"):
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": activity, "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": MODELS["extract"], "LLM_MODEL_VERIFY": MODELS["verify"],
        "LLM_MODEL_JUDGE": MODELS["judge"], "SESSION_SECRET": "test-only",
        "DATABASE_PATH": str(tmp_path / "app.db")})


def _seed(tmp_path, activity, in_app, in_spike):
    """Throwaway app and spike databases holding that many real-call lines of `activity`. Returns
    (settings, connection to the app database); the seeded spike run is set aside so a review can start."""
    settings = _settings(tmp_path, activity)
    app_db, spike_db = tmp_path / "app.db", tmp_path / "spike.db"
    make_db(app_db, **{activity: in_app})
    if in_spike:
        make_db(spike_db, **{activity: in_spike})
    conn = connect(app_db)
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")     # test set-up
    conn.commit()
    return settings, conn


def _review(conn, settings):
    return runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID, started_by=flow.SPECIALIST,
                          demo_planted_row=False, demo_fail_step1=False)


@pytest.fixture(autouse=True)
def count_this_tests_spike_file(tmp_path, monkeypatch):
    """The conftest points every test at an empty spike file. Here the spike file is the one `_seed` writes
    (tmp_path/spike.db); the real function still composes the list, as in production."""
    monkeypatch.setattr(stages, "_counting_databases",
                        lambda settings: spike.counted_databases(settings, tmp_path / "spike.db"))


@pytest.fixture
def fake(as_openai):
    as_openai.answer_with(the_answer_key)
    return as_openai


def _units(conn, run_id):
    return [(u["status"], u["failure_reason"]) for u in runs.list_units(conn, run_id)]


# --- the cap stops the next call -----------------------------------------------------------------------

@pytest.mark.parametrize("in_app, in_spike", [(35, 35), (70, 0), (0, 70), (20, 55)])
def test_at_70_the_first_unit_fails_with_call_limit_and_nothing_is_sent(tmp_path, fake, in_app, in_spike):
    """70 lines, however they split across the two files: the counts ADD, and no request is sent."""
    settings, conn = _seed(tmp_path, "spike", in_app, in_spike)
    run_id = _review(conn, settings)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")
    assert _units(conn, run_id) == [("failed", "call limit")] + [("waiting", None)] * 4
    assert fake.requests == []                                             # the fake recorded zero requests
    assert run["failure"]["reason_sentence"] == CALL_LIMIT
    assert conn.execute("SELECT COUNT(*) FROM trace WHERE run_id = ?", (run_id,)).fetchone()[0] == 0


def test_at_69_the_call_is_made_and_the_next_unit_is_refused(tmp_path, fake):
    settings, conn = _seed(tmp_path, "spike", 35, 34)                       # 69 in all
    run_id = _review(conn, settings)
    units = _units(conn, run_id)
    assert units[0] == ("done", None)                                       # the 70th call was allowed
    assert units[1] == ("failed", "call limit")                             # the 71st was not
    sent = len(fake.requests)
    assert sent >= 1
    assert runs.get_run(conn, run_id)["status"] == "FAILED"
    assert len(fake.requests) == sent                                       # nothing was sent after the refusal


def test_the_tuning_cap_is_60(tmp_path, fake):
    settings, conn = _seed(tmp_path, "tuning", 30, 30)
    run_id = _review(conn, settings)
    assert _units(conn, run_id)[0] == ("failed", "call limit") and fake.requests == []


def test_the_cap_table_holds_spike_tuning_and_evaluation():
    """H-096 PR 3, DL-59 (SOQ-36): evaluation has its own cap of 63, beside spike 70 and tuning 60."""
    assert harness.CALL_CAPS == {"spike": 70, "tuning": 60, "evaluation": 63}


@pytest.mark.parametrize("in_app, in_spike", [(63, 0), (0, 63), (30, 33)])
def test_at_63_an_evaluation_unit_fails_with_call_limit_and_nothing_is_sent(tmp_path, fake, in_app, in_spike):
    """63 evaluation lines, however they split across the two files: the counts add, no request is sent."""
    settings, conn = _seed(tmp_path, "evaluation", in_app, in_spike)
    run_id = _review(conn, settings)
    assert _units(conn, run_id)[0] == ("failed", "call limit") and fake.requests == []
    assert runs.get_run(conn, run_id)["failure"]["reason_sentence"] == CALL_LIMIT


def test_at_62_an_evaluation_call_is_made_and_the_next_unit_is_refused(tmp_path, fake):
    settings, conn = _seed(tmp_path, "evaluation", 31, 31)                  # 62 in all
    run_id = _review(conn, settings)
    units = _units(conn, run_id)
    assert units[0] == ("done", None) and units[1] == ("failed", "call limit")


def test_another_activitys_lines_do_not_count_towards_the_evaluation_cap(tmp_path, fake):
    settings, conn = _seed(tmp_path, "evaluation", 0, 0)
    make_db(tmp_path / "spike.db", spike=70)                                # spike is full; evaluation is empty
    run_id = _review(conn, settings)
    assert runs.get_run(conn, run_id)["phase"] == "AT_G1"


@pytest.mark.parametrize("activity", ["rehearsal", "demo"])
def test_activities_without_a_cap_are_never_refused(tmp_path, fake, activity):
    settings, conn = _seed(tmp_path, activity, 100, 100)                    # 200 lines: far past any cap
    run_id = _review(conn, settings)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("ACTIVE", "AT_G1")
    assert {status for status, _ in _units(conn, run_id)} == {"done"}


def test_stand_in_mode_never_checks(conn_standin, settings, monkeypatch):
    """Stand-in makes no real call, so it must not even look at the databases."""
    def must_not_be_called(*args, **kwargs):
        raise AssertionError("stand-in mode counted real calls")
    monkeypatch.setattr(harness, "count_real_calls", must_not_be_called)
    run_id = flow.start_to_g1(conn_standin, settings)
    assert runs.get_run(conn_standin, run_id)["phase"] == "AT_G1"


@pytest.fixture
def conn_standin(settings):
    from backend.db.connection import init_db
    init_db(settings.database_path)
    connection = connect(settings.database_path)
    yield connection
    connection.close()


# --- it fails closed, and the pinned cost cap is untouched ----------------------------------------------

@pytest.mark.parametrize("activity", ["spike", "tuning", "evaluation"])
def test_a_database_that_cannot_be_read_fails_the_unit_with_call_limit_and_sends_nothing(tmp_path, fake, activity):
    """Fail closed (DL-59): a count that quietly said 0 would let the cap be passed, and a count that cannot be
    read is treated as the cap reached. No request is sent; the reason is `call limit` (not `unexpected error`).
    This applies to every capped activity, spike and tuning included (operator, SOQ-36)."""
    settings, conn = _seed(tmp_path, activity, 0, 0)
    (tmp_path / "spike.db").write_bytes(b"this is not a database" * 100)
    run_id = _review(conn, settings)
    assert _units(conn, run_id)[0] == ("failed", "call limit") and fake.requests == []
    assert runs.get_run(conn, run_id)["status"] == "FAILED"


@pytest.mark.parametrize("activity", ["rehearsal", "demo"])
def test_an_activity_without_a_cap_never_reads_the_count(tmp_path, fake, activity):
    """No cap, no look: an unreadable file cannot stop a rehearsal or a demo."""
    settings, conn = _seed(tmp_path, activity, 0, 0)
    (tmp_path / "spike.db").write_bytes(b"this is not a database" * 100)
    run_id = _review(conn, settings)
    assert runs.get_run(conn, run_id)["phase"] == "AT_G1"


def test_the_pinned_cost_cap_is_not_changed(tmp_path):
    assert _settings(tmp_path).run_cost_cap_usd == 2.50          # US$2.50 (CR-017); this change leaves it


def test_the_checked_databases_are_the_real_spike_file_and_the_app_file(tmp_path):
    """The conftest patches `_counting_databases` away from data/spike.db for every test; this checks the
    real function (taken at import) still names both files, as the spike command does."""
    settings = _settings(tmp_path)
    assert REAL_COUNTING_DATABASES(settings) == [spike.SPIKE_DB, Path(settings.database_path)]
