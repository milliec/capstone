"""H-091 part 3 (E-11, DL-58): an error nobody listed ends the review as Failed, reason `unexpected error`.

Before this, run_stage handled only the listed failures. Any other error (a missing model ID, a bug, a full
disk) escaped the background task and left the review on "AI is drafting the rules" until a restart.

Tier 1, no real call and no key. Real mode appears only against the fake OpenAI, with a dummy key and a
temporary database. The tests check, for every stage:
  * the review ends FAILED, keeping its phase (DL-46); the running unit is the one named;
  * no gate opens and nothing is stored (rule 9);
  * the audit entry holds the error's CLASS NAME and never its message; the page shows only the sentence;
  * a failure that was already recorded is not overwritten, and the stage timer is still cancelled.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.db.connection import connect, init_db
from backend.main import create_app
from backend.runtime import agents, stages
from backend.services import FUND_ID, runs, stage_store
from backend.services.audit import list_audit
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY

UNEXPECTED = ("Something went wrong that the app did not expect, so this step was stopped and nothing "
              "from it was saved")
SECRET = "secret-detail-must-never-be-shown"      # the message of every error these tests raise


def _boom(*args, **kwargs):
    raise RuntimeError(SECRET)


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    connection = connect(settings.database_path)
    yield connection
    connection.close()


def _everything_audited(conn, run_id):
    """Every audit entry of the run, flattened to one string, to search for words that must not be there."""
    return " | ".join(str(value) for entry in list_audit(conn, run_id) for value in entry.values())


def _failed_units(conn, run_id):
    return [(u["unit_id"], u["failure_reason"]) for u in runs.list_units(conn, run_id)
            if u["status"] == "failed"]


def _assert_ended_as_unexpected_error(conn, run_id, phase):
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", phase)         # it keeps its phase, no gate opens
    failed = _failed_units(conn, run_id)
    assert len(failed) == 1 and failed[0][1] == "unexpected error"    # one unit is named
    assert run["failure"]["reason_sentence"] == UNEXPECTED
    assert run["ended_because"] == UNEXPECTED
    audited = _everything_audited(conn, run_id)
    assert "RuntimeError" in audited                                   # the class name is recorded ...
    assert SECRET not in audited                                       # ... and never the message
    return failed[0][0]


# --- (a) real mode, fake OpenAI, the model ID is not set ---------------------------------------------

@pytest.fixture
def no_model_settings(tmp_path, as_openai):
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": "", "LLM_MODEL_VERIFY": "gpt-6-test-v", "LLM_MODEL_JUDGE": "gpt-6-test-j",
        "SESSION_SECRET": "test-only", "DATABASE_PATH": str(tmp_path / "real.db")})


def test_a_missing_model_id_ends_the_review_as_failed_and_a_new_one_can_start(no_model_settings, as_openai):
    client = TestClient(create_app(no_model_settings))
    client.post("/sign-in", data={"identity_id": "specialist-1"})
    db = connect(no_model_settings.database_path)

    assert client.post("/specialist/runs", data={}, follow_redirects=False).status_code == 303
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    unit = _assert_ended_as_unexpected_error_class(db, run_id, "ModelNotSet")
    assert unit == runs.list_units(db, run_id)[0]["unit_id"]           # the first document is the one named
    assert [u["status"] for u in runs.list_units(db, run_id)] == ["failed"] + ["waiting"] * 4
    assert as_openai.requests == []                                     # no call was sent
    assert db.execute("SELECT COUNT(*) FROM paragraphs WHERE run_id = ?", (run_id,)).fetchone()[0] == 0

    page = client.get(f"/specialist/runs/{run_id}").text
    assert UNEXPECTED in " ".join(page.split()) and "LLM_MODEL_EXTRACT" not in page

    # The failure does not block the next review.
    assert client.post("/specialist/runs", data={}, follow_redirects=False).status_code == 303
    assert len(runs.list_runs(db, FUND_ID)) == 2
    db.close()


def _assert_ended_as_unexpected_error_class(conn, run_id, class_name):
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")
    failed = _failed_units(conn, run_id)
    assert len(failed) == 1 and failed[0][1] == "unexpected error"
    assert run["failure"]["reason_sentence"] == UNEXPECTED
    audited = _everything_audited(conn, run_id)
    assert class_name in audited and "LLM_MODEL_EXTRACT" not in audited and "DL-40" not in audited
    return failed[0][0]


# --- (b) a stand-in agent raises, in each stage ------------------------------------------------------

def _start(conn, settings):
    return runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID, started_by=flow.SPECIALIST,
                          demo_planted_row=False, demo_fail_step1=False)


def _until_g1_completes(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n])
    return run_id


def _answer_g2(conn, run_id):
    for n in flow.APPLIES_NS:
        flow.answer(conn, run_id, n, "confirm", "applies")
    flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "Not confirmed in fund records yet")
    flow.answer(conn, run_id, flow.DOES_NOT_APPLY_N, "confirm", "does_not_apply")


def test_b_an_error_in_stage_a_ends_the_review_as_failed(conn, settings, monkeypatch):
    monkeypatch.setattr(agents, "extract_rows", _boom)
    run_id = _start(conn, settings)
    unit = _assert_ended_as_unexpected_error(conn, run_id, "A_RUNNING")
    assert unit == runs.list_units(conn, run_id)[0]["unit_id"]
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0


def test_b_an_error_in_stage_b_ends_the_review_as_failed(conn, settings, monkeypatch):
    run_id = _until_g1_completes(conn, settings)
    monkeypatch.setattr(agents, "judge_applicability", _boom)
    flow.finish_g1(conn, settings, run_id)
    unit = _assert_ended_as_unexpected_error(conn, run_id, "B_RUNNING")
    assert unit == f"ROW-{run_id}-1"                                   # the judge unit that was running
    assert conn.execute("SELECT COUNT(*) FROM verdicts").fetchone()[0] == 0


def test_b_an_error_in_stage_c_ends_the_review_as_failed(conn, settings, monkeypatch):
    run_id = _until_g1_completes(conn, settings)
    flow.finish_g1(conn, settings, run_id)
    _answer_g2(conn, run_id)
    monkeypatch.setattr(stages.dates, "generate", _boom)
    flow.finish_g2(conn, settings, run_id)
    assert _assert_ended_as_unexpected_error(conn, run_id, "C_RUNNING") == "CALENDAR"
    assert conn.execute("SELECT COUNT(*) FROM calendar_versions").fetchone()[0] == 0


def test_an_error_while_storing_also_ends_the_review_as_failed(conn, settings, monkeypatch):
    """The store is all or nothing and re-raises; before this fix that also left the review hanging."""
    def fail_to_store(*args, **kwargs):
        raise sqlite3.OperationalError(SECRET)
    monkeypatch.setattr(stages.stage_store, "store_stage_outputs", fail_to_store)
    run_id = _start(conn, settings)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")
    assert [reason for _unit, reason in _failed_units(conn, run_id)] == ["unexpected error"]
    audited = _everything_audited(conn, run_id)
    assert "OperationalError" in audited and SECRET not in audited


# --- (c) what the fix must NOT do --------------------------------------------------------------------

def test_a_failure_already_recorded_is_not_overwritten(conn, settings, monkeypatch):
    """The stage timer (or anything else) failed the stage first; the error that follows changes nothing."""
    def fail_then_raise(settings_, *, document_id, **kwargs):
        other = connect(settings.database_path)
        try:
            run = runs.get_run(other, runs.list_runs(other, FUND_ID)[0]["run_id"])
            assert stage_store.fail_stage(other, run, "A", document_id, "stage time limit") is True
        finally:
            other.close()
        raise RuntimeError(SECRET)
    monkeypatch.setattr(agents, "extract_rows", fail_then_raise)
    run_id = _start(conn, settings)
    assert runs.get_run(conn, run_id)["status"] == "FAILED"
    assert [reason for _unit, reason in _failed_units(conn, run_id)] == ["stage time limit"]
    assert SECRET not in _everything_audited(conn, run_id)


def test_the_failure_demo_still_ends_as_demo_failure(conn, settings):
    """_StageStopped is not swallowed or re-labelled: a failure already recorded stays what it was."""
    run_id = runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID, started_by=flow.SPECIALIST,
                            demo_planted_row=False, demo_fail_step1=True)
    assert [reason for _unit, reason in _failed_units(conn, run_id)] == ["demo failure"]


def test_the_stage_timer_is_still_cancelled_after_an_error(conn, settings, monkeypatch):
    made = []

    class RecordingTimer:
        def __init__(self, interval, function, args=()):
            self.cancelled, self.daemon = False, False
            made.append(self)

        def start(self):
            pass

        def cancel(self):
            self.cancelled = True

    monkeypatch.setattr(stages.threading, "Timer", RecordingTimer)
    monkeypatch.setattr(agents, "extract_rows", _boom)
    _start(conn, settings)
    assert len(made) == 1 and made[0].cancelled is True
