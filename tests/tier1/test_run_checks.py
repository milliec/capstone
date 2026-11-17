"""B2 run-level checks: start (RUN_ACTIVE, VALIDATION) and abandon (RUN_NOT_ACTIVE,
RUN_STAGE_RUNNING, VERSION_MISMATCH, REASON_REQUIRED). Each refusal is audited and changes nothing."""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, runs
from backend.services.refusals import Refused
from backend.settings import load_settings


def _no_schedule(*args, **kwargs):
    """Stands in for FastAPI's background task: these tests look at the run, not at stage A."""


def _start(conn, settings):
    return runs.start_run(conn, settings, _no_schedule, fund_id=FUND_ID, started_by="specialist-1",
                          demo_planted_row=False, demo_fail_step1=False)


def _refusals(conn):
    return [dict(r) for r in conn.execute(
        "SELECT * FROM audit_log WHERE event_type = 'refusal' ORDER BY audit_id")]


def _snapshot(conn):
    return [tuple(r) for r in conn.execute("SELECT * FROM runs ORDER BY rowid")]


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def test_second_start_is_refused_run_active_and_nothing_changes(conn, settings):
    first = _start(conn, settings)
    before = _snapshot(conn)
    with pytest.raises(Refused) as caught:
        _start(conn, settings)
    r = caught.value.refusal
    assert (r.code, r.http_status, r.anchor) == ("RUN_ACTIVE", 409, "start")
    assert r.sentence.startswith("Review 1 is still in progress, so a new review can't start.")
    assert r.short == "Not done. A new review can't start while review 1 is in progress."
    assert r.link_text == "Go to 'Start a new review'"
    assert _snapshot(conn) == before                       # no second run
    refusal = _refusals(conn)[0]
    assert refusal["refusal_code"] == "RUN_ACTIVE" and refusal["run_id"] == first


def test_start_is_allowed_again_once_the_review_ended(conn, settings):
    first = _start(conn, settings)
    conn.execute("UPDATE runs SET status = 'COMPLETED' WHERE run_id = ?", (first,))
    conn.commit()
    assert _start(conn, settings) != first


def test_failure_demo_is_refused_outside_stand_in_mode(tmp_path):
    real = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "SESSION_SECRET": "x",
                          "DATABASE_PATH": str(tmp_path / "real.db")})
    init_db(real.database_path)
    conn = connect(real.database_path)
    with pytest.raises(Refused) as caught:
        runs.start_run(conn, real, _no_schedule, fund_id=FUND_ID, started_by="specialist-1",
                       demo_planted_row=False, demo_fail_step1=True)
    assert caught.value.refusal.code == "VALIDATION" and conn.execute(
        "SELECT COUNT(*) FROM runs").fetchone()[0] == 0


def _at_gate(conn, settings):
    run_id = _start(conn, settings)
    conn.execute("UPDATE runs SET phase = 'AT_G1' WHERE run_id = ?", (run_id,))
    conn.commit()
    return run_id


def test_abandon_at_a_gate_works_and_keeps_the_phase(conn, settings):
    run_id = _at_gate(conn, settings)
    runs.abandon_run(conn, run_id=run_id, run_version=1, reason="  Wrong source  ",
                     actor="specialist-1")
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"], run["run_version"]) == ("ABANDONED", "AT_G1", 2)
    assert run["ended"]["reason"] == "Wrong source"
    assert _refusals(conn) == []


def test_abandon_refusals_each_audited_and_change_nothing(conn, settings):
    running = _start(conn, settings)                       # A_RUNNING
    before = _snapshot(conn)
    with pytest.raises(Refused) as caught:
        runs.abandon_run(conn, run_id=running, run_version=1, reason="x", actor="specialist-1")
    assert caught.value.refusal.code == "RUN_STAGE_RUNNING"
    assert "AI is still working on step 1" in caught.value.refusal.sentence
    assert _snapshot(conn) == before

    conn.execute("UPDATE runs SET phase = 'C_RUNNING' WHERE run_id = ?", (running,))
    with pytest.raises(Refused) as caught:
        runs.abandon_run(conn, run_id=running, run_version=1, reason="x", actor="specialist-1")
    assert caught.value.refusal.sentence.startswith("The dates are still being worked out")

    conn.execute("UPDATE runs SET phase = 'AT_G2' WHERE run_id = ?", (running,))
    conn.commit()
    before = _snapshot(conn)
    with pytest.raises(Refused) as caught:                  # stale page
        runs.abandon_run(conn, run_id=running, run_version=7, reason="x", actor="specialist-1")
    assert caught.value.refusal.code == "VERSION_MISMATCH"
    with pytest.raises(Refused) as caught:                  # blank reason, typed text kept
        runs.abandon_run(conn, run_id=running, run_version=1, reason="   ", actor="specialist-1")
    r = caught.value.refusal
    assert (r.code, r.anchor, r.typed) == ("REASON_REQUIRED", "abandon", {"reason": "   "})
    assert _snapshot(conn) == before

    runs.abandon_run(conn, run_id=running, run_version=1, reason="done", actor="specialist-1")
    with pytest.raises(Refused) as caught:                  # already ended
        runs.abandon_run(conn, run_id=running, run_version=2, reason="again", actor="specialist-1")
    assert caught.value.refusal.code == "RUN_NOT_ACTIVE"
    assert "(Abandoned)" in caught.value.refusal.sentence
    codes = [r["refusal_code"] for r in _refusals(conn)]
    assert codes == ["RUN_STAGE_RUNNING", "RUN_STAGE_RUNNING", "VERSION_MISMATCH",
                     "REASON_REQUIRED", "RUN_NOT_ACTIVE"]


def test_the_page_is_shown_again_with_the_refusal_and_its_status(specialist_client):
    """End to end: the form's page comes back with the sentence, 409, and the "Not done" title."""
    first = specialist_client.post("/specialist/runs", data={}, follow_redirects=False)
    assert first.status_code == 303
    second = specialist_client.post("/specialist/runs", data={}, follow_redirects=False)
    assert second.status_code == 409
    assert "<title>Not done: " in second.text
    assert "Review 1 is still in progress, so a new review can&#39;t start" in second.text \
        or "Review 1 is still in progress, so a new review can't start" in second.text
    assert "Go to &#39;Start a new review&#39;" in second.text or "Go to 'Start a new review'" in second.text

    # The stand-in stage finished while the test client waited, so the review is at G1, version 1.
    # A blank reason: 422, the reason sentence shows, and the page is the review status page.
    run_id = first.headers["location"].rsplit("/", 1)[1]
    page = specialist_client.post(f"/specialist/runs/{run_id}/abandon",
                                  data={"run_version": "1", "reason": ""})
    assert page.status_code == 422
    assert "Write a reason to abandon this review." in page.text
    assert "Abandon this review" in page.text
