"""T-SPIKE-3 (Tier 1): the spike's one live call, against the FAKE OpenAI only (B3 spike PR 2b).

`spike.run_first_call` is the one function in the repository that can spend money. These tests run
it against tests/fake_openai.py: a small server on this machine that plays the provider. No real
model, no real key, no outside connection. What they protect:
  * the call is what the dry-run described: ONE request, the DL-40 settings, a checked answer;
  * every HTTP request has a trace line, and its cost counts, even when it got no answer;
  * a bad answer is reported and NOT asked for again (D5); a failed request gets DL-43's one retry;
  * every refusal happens BEFORE a request is sent;
  * the command's `--go` is still refused, and the key is never written anywhere.
"""

import copy
import socket

import pytest

from backend.db.connection import connect
from backend.runtime import agents, crews, spike
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY, Failure, Reply

DOC = spike.FIRST_CALL_DOCUMENT


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def real(fake_openai, monkeypatch):
    """Real mode, pointed at the fake server. This is the only way a request can leave the test."""
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    return load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                          "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e"})


@pytest.fixture
def local_only(monkeypatch):
    """Any connection to an address other than this machine fails the test."""
    original = socket.socket.connect

    def guarded(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError(f"a test tried to reach {address}")
        return original(self, address, *args, **kwargs)
    monkeypatch.setattr(socket.socket, "connect", guarded)


def good_answer():
    """A valid answer for the first call's document: the stand-in file's, as a model would send it.
    A COPY, because the stand-in files are cached."""
    return {"rows": copy.deepcopy(agents._stand_in("extractor")[DOC])}


def rows(path, sql, *args):
    conn = connect(path)
    try:
        return [dict(r) for r in conn.execute(sql, args)]
    finally:
        conn.close()


# --- A good call --------------------------------------------------------------------------------

def test_a_good_call_sends_one_request_and_writes_one_trace_line(real, fake_openai, local_only,
                                                                 tmp_path):
    fake_openai.script(Reply(good_answer(), tokens_in=900, tokens_out=300))
    db = tmp_path / "data" / "spike.db"
    result = spike.run_first_call(real, spike_db=db)

    assert result.ok and result.failure is None and result.row_count >= 1
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    body = fake_openai.requests[0].body
    assert body["model"] == "gpt-6-test-e"                        # the DL-40 settings, as the dry-run said
    assert (body["reasoning_effort"], body["temperature"], body["max_completion_tokens"]) == (
        "none", 0.0, 2000)

    (line,) = rows(db, "SELECT * FROM trace")
    assert (line["step"], line["unit_id"], line["attempt_n"]) == ("extract_rows", f"{DOC}#1", 1)
    assert result.unit_id == f"{DOC}#1"
    assert (line["spend_activity"], line["late"], line["model"]) == ("spike", 0, "gpt-6-test-e")
    assert (line["tokens_in"], line["tokens_out"], line["stop_reason"]) == (900, 300, "stop")
    assert line["validation_error"] is None and line["provider_error"] is None
    assert line["off_pinned_setting"] == 0
    (run,) = rows(db, "SELECT * FROM runs")
    assert run["run_id"] == result.run_id
    assert line["cost_usd"] > 0
    assert run["cost_so_far"] == pytest.approx(line["cost_usd"])
    assert result.run_cost_usd == pytest.approx(run["cost_so_far"])


def test_two_calls_share_the_one_spike_run(real, fake_openai, tmp_path):
    fake_openai.script(Reply(good_answer()), Reply(good_answer()))
    db = tmp_path / "spike.db"
    first = spike.run_first_call(real, spike_db=db)
    second = spike.run_first_call(real, spike_db=db)
    assert first.run_id == second.run_id
    assert (first.unit_id, second.unit_id) == (f"{DOC}#1", f"{DOC}#2")   # each call is its own unit
    assert len(rows(db, "SELECT * FROM runs")) == 1 and len(rows(db, "SELECT * FROM trace")) == 2
    assert second.run_cost_usd == pytest.approx(rows(db, "SELECT SUM(cost_usd) c FROM trace")[0]["c"])


# --- A bad answer, and a failed request ---------------------------------------------------------

def test_a_bad_answer_is_reported_and_not_asked_for_again(real, fake_openai, tmp_path):
    fake_openai.script(Reply({"rows": [{"nonsense": 1}]}))       # one reply only: a second request
    db = tmp_path / "spike.db"                                   # would be "unscripted"
    result = spike.run_first_call(real, spike_db=db)
    assert not result.ok and result.failure.startswith("invalid output:") and result.row_count == 0
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    (line,) = rows(db, "SELECT * FROM trace")
    assert line["validation_error"] and line["cost_usd"] > 0     # the bad answer was billed


def test_a_failed_request_is_retried_once_and_both_are_traced(real, fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Reply(good_answer()))
    db = tmp_path / "spike.db"
    result = spike.run_first_call(real, spike_db=db)
    assert result.ok and len(fake_openai.requests) == 2
    first, second = rows(db, "SELECT * FROM trace ORDER BY trace_id")
    assert (first["attempt_n"], second["attempt_n"]) == (1, 2)
    assert first["provider_error"] and first["cost_estimated"] == 1 and first["cost_usd"] > 0
    assert second["provider_error"] is None and second["validation_error"] is None


def test_two_failed_requests_are_reported_and_both_are_billed(real, fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Failure(503, "Overloaded"))
    db = tmp_path / "spike.db"
    result = spike.run_first_call(real, spike_db=db)
    assert not result.ok and result.failure.startswith("model service:")
    assert len(fake_openai.requests) == 2                        # DL-43: the one retry, then stop
    lines = rows(db, "SELECT * FROM trace ORDER BY trace_id")
    assert [line["attempt_n"] for line in lines] == [1, 2]
    assert all(line["provider_error"] and line["cost_usd"] > 0 for line in lines)
    assert rows(db, "SELECT cost_so_far c FROM runs")[0]["c"] == pytest.approx(
        sum(line["cost_usd"] for line in lines))


# --- Every refusal comes BEFORE a request -------------------------------------------------------

@pytest.mark.parametrize("overrides", [
    {"AGENTS_MODE": "stand_in"},
    {"SPEND_ACTIVITY": "tuning"},
    {"OPENAI_API_KEY": ""},
    {"LLM_MODEL_EXTRACT": ""},
])
def test_a_missing_condition_refuses_before_any_request(fake_openai, monkeypatch, tmp_path,
                                                        overrides):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    env = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
           "LLM_MODEL_EXTRACT": "gpt-6-test-e", **overrides}
    db = tmp_path / "data" / "spike.db"
    with pytest.raises(spike.REFUSALS):
        spike.run_first_call(load_settings(env), spike_db=db)
    assert fake_openai.requests == [] and not db.exists()        # nothing sent, nothing created


def test_a_document_that_is_not_primary_refuses_before_any_request(real, fake_openai, tmp_path):
    with pytest.raises(spike.SpikeRefused):
        spike.run_first_call(real, document_id="SRC-PRACT", spike_db=tmp_path / "spike.db")
    assert fake_openai.requests == []


def test_the_70_call_cap_refuses_before_any_request(real, fake_openai, tmp_path):
    db = tmp_path / "spike.db"
    run_id = spike.open_spike_run(real, db)
    conn = connect(db)
    for n in range(70):
        conn.execute(
            "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
            "prompt_version, input_hash, spend_activity) "
            "VALUES (?, 'FND-DEMO-01', 'extract_rows', 1, ?, 1, 'now', 'v', 'h', 'spike')",
            (run_id, f"S{n}"))
    conn.commit()
    conn.close()
    with pytest.raises(spike.REFUSALS):
        spike.run_first_call(real, spike_db=db)
    assert fake_openai.requests == []


def test_a_call_that_could_pass_the_cost_cap_refuses_before_any_request(real, fake_openai, tmp_path):
    db = tmp_path / "spike.db"
    run_id = spike.open_spike_run(real, db)
    conn = connect(db)
    conn.execute("UPDATE runs SET cost_so_far = 2.499 WHERE run_id = ?", (run_id,))
    conn.commit()
    conn.close()
    with pytest.raises(spike.SpikeRefused, match="cap"):
        spike.run_first_call(real, spike_db=db)
    assert fake_openai.requests == []


# --- The command, and the key -------------------------------------------------------------------

def test_the_command_go_is_still_refused_and_sends_nothing(fake_openai, monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    env = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
           "LLM_MODEL_EXTRACT": "gpt-6-test-e"}
    printed: list[str] = []
    db = tmp_path / "data" / "spike.db"
    code = spike.main(["--go"], env=env, spike_db=db, out=printed.append)
    assert code == 2 and "not available" in " ".join(printed)
    assert fake_openai.requests == [] and not db.exists()


def test_the_key_is_not_in_the_result_or_the_database(real, fake_openai, tmp_path):
    fake_openai.script(Reply(good_answer()))
    db = tmp_path / "spike.db"
    result = spike.run_first_call(real, spike_db=db)
    assert TEST_API_KEY not in repr(result)
    assert db.read_bytes().find(TEST_API_KEY.encode()) == -1
