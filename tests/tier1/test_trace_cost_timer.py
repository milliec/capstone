"""B3 step 6: the trace (CR-018), the cost count and cap (CR-017), and the stage timer (rule 6,
DL-43): T-RUN-6 and T-RUN-8. No model: stand-in calls write trace lines too.

Two tests here wait for real (well under a second each): the stage timer is a real timer, and the
honest way to test it is to let it go off while a stand-in unit is pausing.
"""

import re
import sqlite3

import pytest

from backend.db.connection import connect, init_db
from backend.runtime import agents
from backend.services import FUND_ID, runs, stage_store, trace
from backend.settings import SettingsError, load_settings
from tests import flow


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _with(settings, **changes):
    return settings.__class__(**{**settings.__dict__, **changes})


def _unit(conn, run_id, unit_id):
    return dict(conn.execute("SELECT * FROM units WHERE run_id = ? AND unit_id = ?",
                             (run_id, unit_id)).fetchone())


# --- The trace (CR-018) -------------------------------------------------------------------

def test_every_stand_in_call_writes_one_trace_line(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    lines = trace.list_trace(conn, run_id)
    steps = [line["step"] for line in lines]
    assert steps == ["extract_rows"] * 5 + ["check_conflicts"] * 6
    for line in lines:
        assert line["model"] == "" and line["model_returned"] == ""   # stand-in: no model
        assert line["spend_activity"] is None and line["eval_case"] is None
        assert line["cost_usd"] == 0 and line["late"] == 0 and line["attempt_n"] == 1
        assert line["parsed_output"] and line["validation_error"] is None and line["raw_output"]
        assert line["prompt_version"].startswith("stand-in:")
        assert re.fullmatch(r"[0-9a-f]{64}", line["input_hash"]) and line["at"]

    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    assert [line["step"] for line in trace.list_trace(conn, run_id)][11:] == \
        ["judge_applicability"] * 6


def test_each_agent_output_audit_entry_points_at_its_trace_line(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    refs = [r["trace_ref"] for r in conn.execute(
        "SELECT trace_ref FROM audit_log WHERE run_id = ? AND event_type = 'agent_output' "
        "ORDER BY audit_id", (run_id,))]
    keys = [trace.record_key(run_id, line["step"], line["stage_attempt"], line["unit_id"],
                             line["attempt_n"]) for line in trace.list_trace(conn, run_id)]
    assert refs == keys and len(refs) == 11


def test_the_trace_is_append_only(conn, settings):
    flow.start_to_g1(conn, settings)
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("UPDATE trace SET cost_usd = 9")
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("DELETE FROM trace")


def test_invalid_output_is_traced_with_its_error_and_fails_the_run(conn, settings, monkeypatch):
    """CR-003: the invalid output lives in the trace only; the run ends FAILED, nothing stored."""
    real = agents._stand_in

    def broken(name):
        answers = dict(real(name))
        if name == "extractor":
            answers["SRC-CSSF15627"] = [{"obligation_name": "Due 2027-01-10"}]
        return answers

    monkeypatch.setattr(agents, "_stand_in", broken)
    run_id = flow.start_to_g1(conn, settings)
    run = runs.get_run(conn, run_id)
    assert run["status"] == "FAILED"
    assert _unit(conn, run_id, "SRC-CSSF15627")["failure_reason"] == "invalid output"
    [line] = trace.list_trace(conn, run_id)
    assert line["validation_error"] and line["parsed_output"] is None and line["raw_output"]
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0


# --- The cost count and the cost cap (CR-017) --------------------------------------------

def test_the_cost_cap_stops_further_calls(conn, settings, monkeypatch):
    """US$1 a call against a US$2.50 cap: calls 1 to 3 run (US$3, a little over, as CR-017 says
    for a call in flight), call 4 never starts and the run fails with "cost cap"."""
    monkeypatch.setattr(agents, "STAND_IN_COST_USD", 1.0)
    run_id = flow.start_to_g1(conn, _with(settings, run_cost_cap_usd=2.50))
    run = runs.get_run(conn, run_id)
    assert run["status"] == "FAILED" and run["cost_so_far"] == 3.0
    assert len(trace.list_trace(conn, run_id)) == 3
    fourth = runs.list_units(conn, run_id)[3]
    assert (fourth["status"], fourth["failure_reason"]) == ("failed", "cost cap")
    assert runs.list_units(conn, run_id)[4]["status"] == "waiting"


def test_cost_so_far_is_the_sum_of_the_trace(conn, settings, monkeypatch):
    monkeypatch.setattr(agents, "STAND_IN_COST_USD", 0.01)
    run_id = flow.start_to_g1(conn, settings)
    total = sum(line["cost_usd"] for line in trace.list_trace(conn, run_id))
    assert runs.get_run(conn, run_id)["cost_so_far"] == pytest.approx(total) == pytest.approx(0.11)


# --- The stage timer (rule 6, DL-43): T-RUN-6 and T-RUN-8 --------------------------------

def test_run_6_and_8_a_stage_past_its_limit_fails_and_late_output_is_traced_only(
        conn, settings, monkeypatch):
    """Each stand-in unit pauses 0.3 s; stage A's limit is 0.45 s. Unit 1 finishes at 0.3 s;
    the timer fails unit 2 at 0.45 s; unit 2's answer arrives at 0.6 s, LATE: it is in the trace,
    its cost counts, nothing is stored and no other unit starts."""
    monkeypatch.setattr(agents, "STAND_IN_COST_USD", 1.0)
    slow = _with(settings, stand_in_unit_pause_s=0.3,
                 stage_time_limits={**settings.stage_time_limits, "A": 0.45})
    run_id = flow.start_to_g1(conn, slow)

    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")          # T-RUN-6
    units = runs.list_units(conn, run_id)
    assert [u["status"] for u in units] == ["done", "failed", "waiting", "waiting", "waiting"]
    assert units[1]["failure_reason"] == "stage time limit"
    lines = trace.list_trace(conn, run_id)                                     # T-RUN-8
    assert [line["late"] for line in lines] == [0, 1]
    assert run["cost_so_far"] == 2.0                                           # the late one counts
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0] == 0


def test_a_stage_that_finishes_in_time_is_not_failed_later(conn, settings):
    """The timer is cancelled when the stage ends; even if it fired, the run has moved on."""
    run_id = flow.start_to_g1(conn, _with(settings, stage_time_limits={"A": 5, "B": 5, "C": 5}))
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("ACTIVE", "AT_G1")
    # A timer going off now (the race the lock prevents) changes nothing, not even a unit line.
    before = [u["status"] for u in runs.list_units(conn, run_id)]
    assert stage_store.fail_stage(conn, run, "A", "SRC-CSSF15627", "stage time limit") is False
    assert runs.get_run(conn, run_id)["status"] == "ACTIVE"
    assert [u["status"] for u in runs.list_units(conn, run_id)] == before


# --- Settings --------------------------------------------------------------------------------

def test_cost_cap_and_stage_limits_read_the_sad_names_with_defaults():
    defaults = load_settings({})
    assert defaults.run_cost_cap_usd == 2.50
    assert defaults.stage_time_limits == {"A": 375.0, "B": 150.0, "C": 30.0}
    custom = load_settings({"RUN_COST_CAP_USD": "1.5", "STAGE_TIME_LIMIT_B": "90"})
    assert custom.run_cost_cap_usd == 1.5 and custom.stage_time_limits["B"] == 90.0


@pytest.mark.parametrize("name,value", [("RUN_COST_CAP_USD", "0"), ("STAGE_TIME_LIMIT_A", "-1"),
                                        ("STAGE_TIME_LIMIT_C", "soon")])
def test_a_cap_or_limit_that_is_not_above_zero_refuses_to_start(name, value):
    with pytest.raises(SettingsError):
        load_settings({name: value})
