"""H-096 PR 3, parts (a) to (d): the guards for an evaluation run (DL-59, EC-R2, EC-R7, T-MODE-1). Tier 1.

  (a) A run is an evaluation run when `spend_activity` is `evaluation` AND `started_by` is
      `specialist-eval`. It is derived: no new column.
  (b) `specialist-eval` is an identity the scripted gates can act as, and it is NOT a sign-in choice
      (the sign-in tests are in test_sign_in.py).
  (c) An evaluation run refuses stand-in mode (T-MODE-1): it does not start, and the refusal is audited.
  (d) An evaluation run with `demo_planted_row` on does not start (EC-R7), and the refusal is audited.

Real-mode tests run against the fake OpenAI (dummy key, throwaway databases, `as_openai`). No real call,
no real key, no real database: tests/conftest.py also points the call count away from data/spike.db.
"""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, runs
from backend.services.auth import EVALUATION_ACTOR
from backend.services.refusals import Refused
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key


def _settings(tmp_path, *, mode, activity):
    env = {"AGENTS_MODE": mode, "SPEND_ACTIVITY": activity, "SESSION_SECRET": "test-only",
           "STAND_IN_UNIT_PAUSE_S": "0", "DATABASE_PATH": str(tmp_path / "app.db")}
    if mode == "real":
        env.update({"OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": MODELS["extract"],
                    "LLM_MODEL_VERIFY": MODELS["verify"], "LLM_MODEL_JUDGE": MODELS["judge"]})
    return load_settings(env)


def _start(settings, *, started_by=EVALUATION_ACTOR, planted=False):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    return conn, runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID, started_by=started_by,
                                demo_planted_row=planted, demo_fail_step1=False)


def _refusals(conn):
    return [dict(r) for r in conn.execute(
        "SELECT actor, refusal_code, reason FROM audit_log WHERE event_type = 'refusal'")]


@pytest.fixture
def fake(as_openai):
    as_openai.answer_with(the_answer_key)
    return as_openai


# --- (a) the run type is derived -----------------------------------------------------------------------

def test_the_actor_is_specialist_eval():
    assert EVALUATION_ACTOR == "specialist-eval"


def test_a_real_evaluation_run_started_by_specialist_eval_is_an_evaluation_run(tmp_path, fake):
    settings = _settings(tmp_path, mode="real", activity="evaluation")
    conn, run_id = _start(settings)
    run = runs.get_run(conn, run_id)
    assert (run["spend_activity"], run["started_by"]) == ("evaluation", "specialist-eval")
    assert runs.is_evaluation_run(run) is True
    assert (run["status"], run["phase"]) == ("ACTIVE", "AT_G1")               # it started and ran stage A


@pytest.mark.parametrize("activity, started_by", [
    ("evaluation", "specialist-1"),           # the right activity, a person
    ("spike", "specialist-eval"),             # the scripted identity, another activity
    ("", "specialist-eval"),                  # stand-in: no activity at all
])
def test_a_run_needs_both_to_be_an_evaluation_run(tmp_path, activity, started_by):
    settings = _settings(tmp_path, mode="stand_in", activity=activity)
    conn, run_id = _start(settings, started_by=started_by)
    assert runs.is_evaluation_run(runs.get_run(conn, run_id)) is False


def test_there_is_no_new_column_for_it(tmp_path):
    """DL-59: derived, so the schema (and the data/app.db hash baseline) does not move."""
    settings = _settings(tmp_path, mode="stand_in", activity="")
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    columns = {r["name"] for r in conn.execute("PRAGMA table_info(runs)")}
    assert not {c for c in columns if "eval" in c.lower() or "run_type" in c.lower()}


# --- (b) the identity ----------------------------------------------------------------------------------

def test_specialist_eval_has_a_readable_label_on_the_pages(tmp_path, fake):
    settings = _settings(tmp_path, mode="real", activity="evaluation")
    conn, run_id = _start(settings)
    assert runs.get_run(conn, run_id)["started_by_label"] == "Evaluation script (mock)"


# --- (c) stand-in mode is refused ----------------------------------------------------------------------

def test_an_evaluation_run_refuses_stand_in_mode_and_audits_it(tmp_path):
    settings = _settings(tmp_path, mode="stand_in", activity="evaluation")
    with pytest.raises(Refused) as caught:
        _start(settings)
    assert caught.value.refusal.code == "VALIDATION"
    conn = connect(settings.database_path)
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0          # it did not start
    (entry,) = _refusals(conn)
    assert entry["actor"] == "specialist-eval" and entry["refusal_code"] == "VALIDATION"
    assert "stand-in" in entry["reason"]


# --- (d) the planted row is refused --------------------------------------------------------------------

def test_an_evaluation_run_refuses_the_planted_row_and_audits_it(tmp_path, fake):
    settings = _settings(tmp_path, mode="real", activity="evaluation")
    with pytest.raises(Refused) as caught:
        _start(settings, planted=True)
    assert caught.value.refusal.code == "VALIDATION"
    conn = connect(settings.database_path)
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0
    (entry,) = _refusals(conn)
    assert entry["actor"] == "specialist-eval" and "planted row" in entry["reason"]
    assert fake.requests == []                                                   # refused before any call


def test_the_planted_row_is_still_allowed_outside_an_evaluation_run(tmp_path):
    """The guard is for evaluation runs only: the demo row switch works as before (CR-029)."""
    settings = _settings(tmp_path, mode="stand_in", activity="")
    conn, run_id = _start(settings, started_by="specialist-1", planted=True)
    assert runs.get_run(conn, run_id)["demo_planted_row"] == 1
    assert _refusals(conn) == []
