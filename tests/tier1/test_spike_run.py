"""T-SPIKE-2 (Tier 1): the spike's own run row (B3 spike PR 2a).

A trace line has to belong to a run, so the spike needs one run row in its own database
(data/spike.db). These tests protect three promises: the row is made once and only once, it is
made in the spike database and never the app's, and making it sends nothing and loads no model code.
"""

import socket
import subprocess
import sys

import pytest

from backend.db.connection import connect
from backend.runtime import harness, spike
from backend.services import trace
from backend.services.trace import CallRecord
from backend.settings import ROOT, load_settings
from tests.fake_openai import TEST_API_KEY

REAL_ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
            "LLM_MODEL_EXTRACT": "model-e"}


@pytest.fixture
def no_network(monkeypatch):
    """Any attempt to open a network connection fails the test."""
    def refuse(*args, **kwargs):
        raise AssertionError("opening the spike run tried to open a network connection")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


def rows(path, sql, *args):
    conn = connect(path)
    try:
        return [dict(r) for r in conn.execute(sql, args)]
    finally:
        conn.close()


def test_the_run_is_created_in_the_spike_database(fake_openai, no_network, tmp_path):
    db = tmp_path / "data" / "spike.db"             # the folder does not exist yet: it is made
    run_id = spike.open_spike_run(load_settings(REAL_ENV), db)
    (run,) = rows(db, "SELECT * FROM runs")
    assert run["run_id"] == run_id and run_id.startswith("RUN-")
    assert (run["status"], run["phase"], run["stage_attempt"]) == ("ACTIVE", "A_RUNNING", 1)
    assert (run["agents_mode"], run["spend_activity"], run["cost_so_far"]) == ("real", "spike", 0)
    assert run["fund_id"] == "FND-DEMO-01" and run["started_by"] == "spike-runner"
    assert fake_openai.requests == []               # nothing was sent


def test_it_is_audited(tmp_path):
    db = tmp_path / "spike.db"
    run_id = spike.open_spike_run(load_settings(REAL_ENV), db)
    (entry,) = rows(db, "SELECT * FROM audit_log")
    assert entry["run_id"] == run_id and entry["actor"] == "spike-runner"
    assert entry["event_type"] == "system" and "Spike run created" in entry["reason"]


def test_asking_again_finds_the_same_run_and_adds_nothing(tmp_path):
    db = tmp_path / "spike.db"
    first = spike.open_spike_run(load_settings(REAL_ENV), db)
    second = spike.open_spike_run(load_settings(REAL_ENV), db)
    assert first == second
    assert len(rows(db, "SELECT * FROM runs")) == 1
    assert len(rows(db, "SELECT * FROM audit_log")) == 1


@pytest.mark.parametrize("env", [
    {**REAL_ENV, "AGENTS_MODE": "stand_in"},
    {**REAL_ENV, "SPEND_ACTIVITY": "tuning"},
])
def test_a_wrong_setting_refuses_and_creates_no_file(tmp_path, env):
    db = tmp_path / "data" / "spike.db"
    with pytest.raises(spike.SpikeRefused):
        spike.open_spike_run(load_settings(env), db)
    assert not db.exists() and not db.parent.exists()


def test_the_default_file_is_not_the_apps_database():
    settings = load_settings(REAL_ENV)
    assert spike.SPIKE_DB != settings.database_path
    assert spike.SPIKE_DB.name == "spike.db" and spike.SPIKE_DB.parent == ROOT / "data"


def test_a_trace_line_can_belong_to_the_run_and_the_cap_counts_it(tmp_path):
    """The reason the run exists: a real call's trace line is written against it, is not 'late',
    adds its cost to the run, and counts towards the 70-call cap."""
    db = tmp_path / "spike.db"
    settings = load_settings(REAL_ENV)
    run_id = spike.open_spike_run(settings, db)
    conn = connect(db)
    try:
        run = dict(conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone())
        late = trace.record_call(
            conn, run=run, stage="A", unit_id="SRC-UCILAW", spend_activity="spike",
            call=CallRecord(step="extract_rows", at="now", prompt_version="v", input_hash="h",
                            raw_output=None, parsed_output=None, validation_error=None,
                            duration_ms=1, model="model-e", cost_usd=0.003))
        assert late is False
        assert harness.real_calls_made(conn, "spike") == 1
        assert trace.cost_so_far(conn, run_id) == pytest.approx(0.003)
    finally:
        conn.close()


def test_importing_the_spike_loads_no_model_code():
    """In a fresh Python process, so what other tests imported cannot hide a problem."""
    code = ("import sys, backend.runtime.spike; "
            "bad = [m for m in sys.modules if m == 'crewai' or m.startswith('crewai.') "
            "or m in ('backend.runtime.crews', 'backend.runtime.agents', 'backend.services.runs')]; "
            "print(bad); sys.exit(1 if bad else 0)")
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
                          check=False)     # the next line checks the exit code and shows the output
    assert done.returncode == 0, done.stdout + done.stderr
