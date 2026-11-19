"""T-DEMOFAIL-1 (CR-033, DL-52, DL-54, rule 11; Tier 1, block B13a). No model.

  1. Switch off → stage A runs normally.
  2. Switch on (stand-in) → the run is FAILED at stage A, unit 1 has "demo failure", the other
     units are "waiting", and the switch has one audit entry.
  3. Real mode with the field sent → VALIDATION, no run started.
  4. The General Partner's calendar never contains "Failure demo".
Plus: the failure goes through the stand-in extractor hook, and the failed page offers only a new
review (Retry is B13b), with the "Failure demo on" label on specialist pages only.
"""

import pytest

from backend.db.connection import connect, init_db
from backend.runtime import agents
from backend.services import FUND_ID, runs, trace
from backend.services.refusals import Refused
from backend.settings import load_settings
from tests import flow


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _start(conn, settings, *, demo_fail):
    return runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID,
                          started_by=flow.SPECIALIST, demo_planted_row=False,
                          demo_fail_step1=demo_fail)


def _switch_entries(conn, run_id):
    return conn.execute("SELECT COUNT(*) FROM audit_log WHERE run_id = ? AND reason = ?",
                        (run_id, "Failure demo switch on")).fetchone()[0]


def test_demofail_1_switch_off_stage_a_runs_normally(conn, settings):
    run_id = _start(conn, settings, demo_fail=False)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("ACTIVE", "AT_G1")
    assert {u["status"] for u in runs.list_units(conn, run_id)} == {"done"}
    assert _switch_entries(conn, run_id) == 0


def test_demofail_1_switch_on_fails_unit_1_and_leaves_the_rest_waiting(conn, settings):
    run_id = _start(conn, settings, demo_fail=True)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")
    units = runs.list_units(conn, run_id)
    assert [(u["status"], u["failure_reason"]) for u in units] == \
        [("failed", "demo failure")] + [("waiting", None)] * 4
    assert _switch_entries(conn, run_id) == 1
    # Nothing was stored (rule 9) and no output was produced, so there is no trace line.
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0
    assert trace.list_trace(conn, run_id) == []
    failure = run["failure"]
    assert failure["step"] == 1 and failure["unit_label"] == "CSSF Circular 15/627"
    assert failure["reason_sentence"].startswith("This step failed on purpose")


def test_demofail_1_unit_1_runs_alone_first(conn, settings, monkeypatch):
    """Rule 11: the stage starts unit 1 alone, so its failure ends the stage before any other
    unit starts. Seen from inside unit 1's pause: every other unit is still waiting."""
    seen = []

    def watching_pause(s, sleep=None):
        seen.append([u["status"] for u in runs.list_units(conn, runs.list_runs(conn, FUND_ID)[0]["run_id"])])

    monkeypatch.setattr(agents, "unit_pause", watching_pause)
    _start(conn, settings, demo_fail=True)
    assert seen == [["running", "waiting", "waiting", "waiting", "waiting"]]


def test_demofail_1_real_mode_refuses_the_field_and_starts_nothing(settings):
    real = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                          "DATABASE_PATH": str(settings.database_path)})
    init_db(real.database_path)
    conn = connect(real.database_path)
    with pytest.raises(Refused) as caught:
        _start(conn, real, demo_fail=True)
    assert caught.value.refusal.code == "VALIDATION"
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE refusal_code = 'VALIDATION'"
                        ).fetchone()[0] == 1


def test_demofail_1_the_extractor_hook_refuses_real_mode():
    """The hook lives in the stand-in extractor; real mode is refused before it is reached."""
    real = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike"})
    with pytest.raises(agents.RealAgentsNotBuilt):
        agents.extract_rows(real, document_id="SRC-CSSF15627", paragraphs={}, recipient_codes=[],
                            demo_fail=True)


def test_demofail_1_pages_label_it_for_the_specialist_and_never_for_the_gp(
        specialist_client, gp_client, settings, db):
    specialist_client.post("/specialist/runs", data={"demo_fail_step1": "true"})
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    page = specialist_client.get(f"/specialist/runs/{run_id}").text
    assert "Failure demo on" in page and "This review failed" in page
    assert "Start a new review" in page and ">Retry" not in page        # Without Retry (B13b)
    # A later review is published, so the GP has a calendar to look at: still no "Failure demo".
    flow.publish_everything_http(specialist_client, flow.start_to_g1(db, settings))
    for view in ("", "?view=list", "?view=month", "?view=year"):
        assert "Failure demo" not in gp_client.get("/calendar" + view).text, view
