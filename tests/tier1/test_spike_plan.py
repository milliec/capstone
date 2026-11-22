"""T-SPIKE-1 (Tier 1): the spike runner's DRY-RUN plans the first real call and sends nothing
(B3 spike PR 1).

What these tests protect: nobody can spend money by accident. Every test passes its own settings
(a plain dict), so the real .env and the real key are never read. The fake OpenAI is running in
most tests, and every one of them checks it saw ZERO requests. Every network connection is also
blocked while the runner runs, so a request could not leave this machine even by mistake.
"""

import hashlib
import socket

import pytest

from backend.db.connection import connect, init_db
from backend.runtime import harness, model_settings, spike
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY

DISTINCT_KEY = "sk-test-DISTINCT-SECRET-0123456789"   # to prove the key is never printed


def real_env(**overrides) -> dict[str, str]:
    """A complete, valid environment for a spike dry-run. Pass a name=None to remove it."""
    env = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
           "LLM_MODEL_EXTRACT": "model-e"}
    env.update(overrides)
    return {name: value for name, value in env.items() if value is not None}


@pytest.fixture
def no_network(monkeypatch):
    """Any attempt to open a network connection fails the test."""
    def refuse(*args, **kwargs):
        raise AssertionError("the spike dry-run tried to open a network connection")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)


def run_command(argv=None, *, env=None, spike_db):
    """Run the command as the operator would, capturing what it prints."""
    lines: list[str] = []
    code = spike.main(argv or [], env=env if env is not None else real_env(),
                      spike_db=spike_db, out=lines.append)
    return code, "\n".join(lines)


def make_spike_db(settings, *, spike_calls: int, tuning_calls: int = 0):
    """A database holding that many real-call trace lines. Same method as the harness cap test."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    insert = ("INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
              "prompt_version, input_hash, spend_activity) "
              "VALUES (?, 'FND-DEMO-01', 'extract_rows', 1, ?, 1, 'now', 'v', 'h', ?)")
    for n in range(spike_calls):
        conn.execute(insert, (run_id, f"S{n}", "spike"))
    for n in range(tuning_calls):
        conn.execute(insert, (run_id, f"T{n}", "tuning"))
    conn.commit()
    conn.close()
    return settings.database_path


# --- The plan -----------------------------------------------------------------------------------

def test_the_dry_run_prints_a_plan_and_sends_nothing(fake_openai, no_network, tmp_path):
    code, text = run_command(spike_db=tmp_path / "spike.db")
    assert code == 0
    assert "nothing was sent" in text
    assert "SRC-UCILAW" in text and "model-e" in text and "0 of 70 used" in text
    assert fake_openai.requests == [] and fake_openai.unscripted == []


def test_the_module_has_no_path_to_the_network():
    # It must not import the code that makes real calls (crews, agents) or CrewAI itself.
    for forbidden in ("crews", "agents", "crewai"):
        assert not hasattr(spike, forbidden), f"spike.py imports {forbidden}"


def test_the_plan_describes_one_extractor_call_with_the_dl40_settings(tmp_path):
    plan = spike.plan_first_call(load_settings(real_env()), spike_db=tmp_path / "spike.db")
    assert plan.document_id == "SRC-UCILAW" and plan.paragraph_count == 3
    assert plan.sent_settings == {"reasoning_effort": "none", "temperature": 0.0,
                                  "max_completion_tokens": 2000}


def test_the_worst_case_matches_the_price_table_and_stays_small(tmp_path):
    plan = spike.plan_first_call(load_settings(real_env()), spike_db=tmp_path / "spike.db")
    expected = model_settings.call_cost_usd("extract", plan.input_tokens_estimate, 2000)
    assert plan.worst_case_usd == pytest.approx(expected)
    assert plan.worst_case_with_retry_usd == pytest.approx(2 * expected)
    # A guard on the first call's size: a prompt that grew out of hand would fail here, not at
    # the till. One cent is about eight times today's figure.
    assert plan.worst_case_with_retry_usd < 0.01


def test_the_key_is_never_printed(no_network, tmp_path):
    code, text = run_command(env=real_env(OPENAI_API_KEY=DISTINCT_KEY), spike_db=tmp_path / "x.db")
    assert code == 0 and DISTINCT_KEY not in text and "DISTINCT" not in text
    assert "set (never shown)" in text


# --- Refusals: each condition stops the plan, with a reason -------------------------------------

@pytest.mark.parametrize("env,reason", [
    (real_env(AGENTS_MODE="stand_in"), "AGENTS_MODE"),
    (real_env(AGENTS_MODE=None), "AGENTS_MODE"),                  # missing means stand-in
    (real_env(SPEND_ACTIVITY="tuning"), "SPEND_ACTIVITY"),
    (real_env(SPEND_ACTIVITY=None), "SPEND_ACTIVITY"),            # real mode refuses to start
    (real_env(OPENAI_API_KEY=None), "OPENAI_API_KEY"),
    (real_env(OPENAI_API_KEY="REPLACE-ME-with-your-key"), "OPENAI_API_KEY"),
    (real_env(LLM_MODEL_EXTRACT=None), "LLM_MODEL_EXTRACT"),
])
def test_each_missing_condition_refuses(fake_openai, no_network, tmp_path, env, reason):
    code, text = run_command(env=env, spike_db=tmp_path / "spike.db")
    assert code == 2 and text.startswith("REFUSED:") and reason in text
    assert fake_openai.requests == []


@pytest.mark.parametrize("document", ["SRC-PRACT", "SRC-NOPE"])
def test_only_a_primary_document_can_be_planned(tmp_path, document):
    code, text = run_command(["--document", document], spike_db=tmp_path / "spike.db")
    assert code == 2 and "not a primary source document" in text


def test_go_with_nobody_to_confirm_sends_nothing(fake_openai, no_network, tmp_path):
    # Since PR 2c `--go` asks for a typed confirmation. Here nothing can be typed (pytest has no
    # keyboard), which must count as "not confirmed". The full command tests are in T-SPIKE-4.
    code, text = run_command(["--go"], spike_db=tmp_path / "spike.db")
    assert code == 2 and "NOT CONFIRMED" in text and "nothing was sent" in text
    assert fake_openai.requests == []


# --- The 70-call cap, counted from the spike database -------------------------------------------

def test_calls_already_made_are_counted_and_only_spike_calls(settings, tmp_path):
    db_path = make_spike_db(settings, spike_calls=69, tuning_calls=60)   # tuning must not count
    code, text = run_command(spike_db=db_path)
    assert code == 0 and "69 of 70 used" in text


def test_at_the_cap_the_plan_is_refused(settings):
    db_path = make_spike_db(settings, spike_calls=harness.CALL_CAPS["spike"])
    code, text = run_command(spike_db=db_path)
    assert code == 2 and "70 of 70" in text and "EC-R10" in text


def test_a_missing_spike_database_is_not_created(tmp_path):
    missing = tmp_path / "data" / "spike.db"
    code, _ = run_command(spike_db=missing)
    assert code == 0 and not missing.exists() and not missing.parent.exists()


def test_the_dry_run_does_not_change_an_existing_database(settings):
    db_path = make_spike_db(settings, spike_calls=3)
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    code, _ = run_command(spike_db=db_path)
    assert code == 0 and hashlib.sha256(db_path.read_bytes()).hexdigest() == before
