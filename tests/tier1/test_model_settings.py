"""B3 step 7b, PR 2: per-role model settings and the per-call token limits (CR-017, DL-40, DL-43).

No model, no CrewAI, no network. The important test is the last group: it adds up the most a
whole run could cost if EVERY call filled its output limit and every call were retried once, and
fails if that could pass the US$2.50 hard stop. So raising a token limit too far fails a test
instead of surprising the operator's bill.
"""

import json

import pytest

from backend.runtime import model_settings as ms
from backend.settings import ROLES, SettingsError, load_settings
from tests.tier1.test_prompt_leak import _rendered_prompts

STAND_IN = {"AGENTS_MODE": "stand_in", "STAND_IN_UNIT_PAUSE_S": "0"}
IDS = {"LLM_MODEL_EXTRACT": "model-e", "LLM_MODEL_VERIFY": "model-v", "LLM_MODEL_JUDGE": "model-j"}


def settings_with(**extra):
    return load_settings({**STAND_IN, **extra})


# --- Reading the settings -------------------------------------------------------------------

def test_defaults_match_the_sad_and_no_model_id_is_set():
    s = settings_with()
    assert s.llm_models == {"extract": "", "verify": "", "judge": ""}
    assert s.call_timeouts == {"extract": 90.0, "verify": 60.0, "judge": 60.0}   # SAD stage table
    assert s.max_completion_tokens == {"extract": 2000, "verify": 2000, "judge": 4000}


def test_the_names_in_the_environment_are_the_sads():
    s = settings_with(LLM_MODEL_JUDGE="model-j", LLM_MAX_TOKENS_EXTRACT="1500", CALL_TIMEOUT_VERIFY="45")
    assert s.llm_models["judge"] == "model-j"
    assert s.max_completion_tokens["extract"] == 1500
    assert s.call_timeouts["verify"] == 45.0


@pytest.mark.parametrize("name,value", [("LLM_MAX_TOKENS_JUDGE", "0"), ("LLM_MAX_TOKENS_JUDGE", "-5"),
                                        ("LLM_MAX_TOKENS_JUDGE", "lots"), ("LLM_MAX_TOKENS_JUDGE", "1.5"),
                                        ("CALL_TIMEOUT_EXTRACT", "0"), ("CALL_TIMEOUT_EXTRACT", "soon")])
def test_a_bad_limit_or_timeout_refuses_to_start(name, value):
    with pytest.raises(SettingsError, match=name):
        settings_with(**{name: value})


def test_a_missing_model_id_does_not_stop_the_app_in_either_mode():
    """The ID is checked where a call is made, so stand-in mode and the existing real-mode refusal
    keep working with no ID set."""
    load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike"})
    settings_with()


# --- One role's call settings ---------------------------------------------------------------

def test_every_role_gets_its_dl_40_sampling_settings():
    s = settings_with(**IDS)
    extract, verify, judge = (ms.role_settings(s, r) for r in ROLES)
    assert extract.sent_to_provider() == {"reasoning_effort": "none", "temperature": 0.0,
                                          "max_completion_tokens": 2000}
    assert verify.sent_to_provider() == {"reasoning_effort": "low", "max_completion_tokens": 2000}
    assert judge.sent_to_provider() == {"reasoning_effort": "medium", "max_completion_tokens": 4000}
    assert (extract.model, verify.model, judge.model) == ("model-e", "model-v", "model-j")


def test_the_judge_and_the_verifier_send_no_temperature_at_all():
    """A reasoning model may refuse one (DL-40), so it is left out, not sent as null."""
    s = settings_with(**IDS)
    for role in ("verify", "judge"):
        assert "temperature" not in ms.role_settings(s, role).sent_to_provider()


def test_the_http_timeout_is_a_few_seconds_below_the_call_timeout():
    s = settings_with(**IDS)
    for role in ROLES:
        r = ms.role_settings(s, role)
        assert r.http_timeout_s == r.call_timeout_s - 5.0
    tiny = ms.role_settings(settings_with(CALL_TIMEOUT_JUDGE="3", **IDS), "judge")
    assert tiny.http_timeout_s == 1.0 and tiny.http_timeout_s < tiny.call_timeout_s


def test_no_model_id_means_no_call_for_that_role():
    s = settings_with(LLM_MODEL_EXTRACT="model-e")
    assert ms.role_settings(s, "extract").model == "model-e"
    with pytest.raises(ms.ModelNotSet, match="LLM_MODEL_JUDGE"):
        ms.role_settings(s, "judge")
    with pytest.raises(ValueError):
        ms.role_settings(s, "nonsense")


def test_the_trace_text_is_what_was_sent():
    logged = json.loads(ms.role_settings(settings_with(**IDS), "extract").logged())
    assert logged == {"reasoning_effort": "none", "temperature": 0.0, "max_completion_tokens": 2000}


def test_every_step_has_a_role():
    assert set(ms.STEP_ROLE.values()) == set(ROLES)


# --- Cost: one call, and a whole run, against the cap (CR-017) ------------------------------

def test_a_call_costs_its_tokens_at_the_roles_prices():
    assert ms.call_cost_usd("verify", 1_000_000, 0) == pytest.approx(2.00)
    assert ms.call_cost_usd("verify", 0, 1_000_000) == pytest.approx(12.00)
    assert ms.call_cost_usd("extract", 10_000, 2_000) == pytest.approx(0.002)
    assert ms.call_cost_usd("judge", 0, 0) == 0


def _biggest_input_tokens():
    """The largest real prompt of each role, in tokens. A token is never less than one character,
    so the number of characters is a ceiling on tokens (the real count is about a quarter of it)."""
    biggest = dict.fromkeys(ROLES, 0)
    for step, _unit, prompt in _rendered_prompts(settings_with()):
        role = ms.STEP_ROLE[step]
        biggest[role] = max(biggest[role], len("\n".join(prompt.values())))
    return biggest


def test_one_call_can_never_pass_the_cost_cap():
    s = settings_with()
    for role, tokens in _biggest_input_tokens().items():
        assert ms.worst_case_call_cost_usd(s, role, tokens) < s.run_cost_cap_usd / 10


def test_a_generous_run_at_every_limit_and_retried_stays_under_the_cap():
    """12 rows (the demo has 6, plus the planted one), 5 extractions, every call at its output limit
    and every call retried once (DL-43): the most a run could possibly spend."""
    s = settings_with()
    rows = 12
    calls = {"extract": 5 * 2, "verify": rows * 2, "judge": rows * 2}
    worst = ms.worst_case_run_cost_usd(s, input_tokens=_biggest_input_tokens(), calls=calls)
    assert worst < s.run_cost_cap_usd, f"worst case US${worst:.2f} could pass the US$2.50 hard stop"


def test_the_check_really_fails_when_a_limit_is_raised_too_far():
    """Proof the test above can fail: a judge limit of 100,000 tokens busts the cap."""
    s = settings_with(LLM_MAX_TOKENS_JUDGE="100000")
    calls = {"extract": 10, "verify": 24, "judge": 24}
    worst = ms.worst_case_run_cost_usd(s, input_tokens=_biggest_input_tokens(), calls=calls)
    assert worst > s.run_cost_cap_usd
