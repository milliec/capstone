"""T-PAUSE-1 (DL-54): real mode never pauses; stand-in pauses by the set amount per unit.
Plus the default-mode part of T-MODE-1: an unset AGENTS_MODE means stand-in.

No test here sleeps for real: a fake `sleep` records what it was asked to do.
"""

import pytest

from backend.runtime import agents
from backend.services import FUND_ID
from backend.services import runs as runs_service
from backend.settings import SettingsError, load_settings


class FakeSleep:
    def __init__(self):
        self.calls = []

    def __call__(self, seconds):
        self.calls.append(seconds)


# --- T-MODE-1 (default-mode part) -----------------------------------------------------------

def test_agents_mode_defaults_to_stand_in():
    assert load_settings({}).agents_mode == "stand_in"
    assert load_settings({"AGENTS_MODE": ""}).agents_mode == "stand_in"


def test_real_mode_without_a_spend_activity_refuses_to_start():
    with pytest.raises(SettingsError):
        load_settings({"AGENTS_MODE": "real"})


# --- T-PAUSE-1 -----------------------------------------------------------------------------

def test_real_mode_never_reads_the_pause_setting():
    """Even a nonsense value is ignored in real mode, which shows it is never read."""
    s = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                       "STAND_IN_UNIT_PAUSE_S": "not-a-number"})
    assert s.stand_in_unit_pause_s == 0


def test_real_mode_never_pauses():
    s = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                       "STAND_IN_UNIT_PAUSE_S": "5"})
    sleep = FakeSleep()
    agents.unit_pause(s, sleep=sleep)
    assert sleep.calls == []


def test_stand_in_pauses_by_the_set_amount():
    s = load_settings({"STAND_IN_UNIT_PAUSE_S": "2.5"})
    sleep = FakeSleep()
    agents.unit_pause(s, sleep=sleep)
    assert sleep.calls == [2.5]


def test_stand_in_pauses_once_per_unit_during_a_stage(specialist_client, settings, db,
                                                     monkeypatch):
    """Start a review with a 1-second pause: stage A sleeps once per unit, 1 second each."""
    sleep = FakeSleep()
    monkeypatch.setattr(agents.time, "sleep", sleep)
    specialist_client.app.state.settings = settings.__class__(
        **{**settings.__dict__, "stand_in_unit_pause_s": 1.0})

    specialist_client.post("/specialist/runs", data={})

    run = runs_service.list_runs(db, FUND_ID)[0]
    # Stage A's units since B3 step 5: one per primary document, then one check per drafted rule.
    unit_lines = [u for u in runs_service.list_units(db, run["run_id"]) if u["stage"] == "A"]
    assert len(unit_lines) == 5 + 6
    assert sleep.calls == [1.0] * len(unit_lines)
    assert run["phase"] == "AT_G1"
