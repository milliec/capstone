"""T-REQ-2 (Tier 1): only `POST .../chat/completions` is ever sent (spike fix, step D). Fake OpenAI only.

The first real spike call sent a request nobody expected: CrewAI's own pre-flight token count. Step A
switched that off. Step D is the safety net for the NEXT surprise: every request goes through the
interceptor (backend/runtime/crews.py), and one that is not a chat completion is stopped BEFORE it is
sent, costs nothing, and still gets a trace line saying what was stopped and which path it was for.

The `as_openai` fixture makes CrewAI behave as if it were on api.openai.com (see tests/conftest.py).
"""

import pytest

from backend.db.connection import connect
from backend.runtime import crews, harness, model_settings, spike
from backend.runtime.attempts import AttemptLog, is_chat_completion
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY, Reply
from tests.tier1.test_one_request import CHAT, COUNT, extract, good_answer, paths


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def real(as_openai):
    return load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                          "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e"})


@pytest.fixture
def preflight_back_on(monkeypatch):
    """Put CrewAI's pre-flight back (the thing step A switched off), so a non-chat request is tried."""
    build = crews.build_crew

    def build_with_the_preflight(*args, **kwargs):
        crew = build(*args, **kwargs)
        for agent in crew.agents:
            agent.respect_context_window = True
        return crew
    monkeypatch.setattr(crews, "build_crew", build_with_the_preflight)


def rows(path, sql):
    conn = connect(path)
    try:
        return [dict(r) for r in conn.execute(sql)]
    finally:
        conn.close()


# --- The rule -----------------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,allowed", [
    ("POST", "/v1/chat/completions", True),
    ("post", "/v1/chat/completions", True),
    ("POST", "/openai/v1/chat/completions/", True),            # behind a proxy, a trailing slash
    ("POST", "/v1/responses/input_tokens", False),              # the pre-flight the first call sent
    ("POST", "/v1/responses", False),
    ("POST", "/v1/embeddings", False),
    ("GET", "/v1/chat/completions", False),                     # right path, wrong method
    ("GET", "/v1/models", False),
    ("POST", "/v1/chat/completions/extra", False),              # only STARTS like it
    ("POST", "/v1/chat/completionsX", False),
    ("POST", "", False),                                        # no path known: not allowed
])
def test_only_a_post_to_chat_completions_is_allowed(method, path, allowed):
    assert is_chat_completion(method, path) is allowed


def test_the_log_remembers_which_request_it_was_and_a_refusal_costs_nothing():
    log = AttemptLog()
    attempt = log.begin(b"{}", method="POST", path="/v1/responses/input_tokens")
    assert (attempt.method, attempt.path, attempt.refused) == ("POST", "/v1/responses/input_tokens", False)
    reason = log.refuse(attempt)
    assert attempt.refused and attempt.finished and attempt.kind == "refused"
    assert "refused before sending" in reason and "/v1/responses/input_tokens" in reason
    # Whatever its size, a request that was never sent costs 0 and is not an estimate.
    assert model_settings.attempt_cost_usd("extract", kind=attempt.kind, tokens_in=0, tokens_out=0,
                                           request_bytes=10_000_000, max_completion_tokens=2000) == (0.0, False)


# --- A non-chat request is stopped before it is sent, and costs nothing -------------------------

def test_a_stopped_request_never_reaches_the_server_and_costs_nothing(
        real, as_openai, preflight_back_on, tmp_path):
    """CrewAI tries its pre-flight; the guard stops it; CrewAI falls back to its own estimate and
    makes the real call. The server saw ONE request, the run was charged for ONE, and the stopped
    request has its own line: cost 0, not estimated, not 'off the pinned setting'."""
    as_openai.script(Reply(good_answer(), tokens_in=1500, tokens_out=360))
    db = tmp_path / "spike.db"
    result = spike.run_first_call(real, spike_db=db)

    assert result.ok
    assert paths(as_openai) == [CHAT]                           # the count request never left
    stopped, answered = rows(db, "SELECT * FROM trace ORDER BY trace_id")
    assert stopped["request_path"] == COUNT
    assert stopped["provider_error"].startswith("refused before sending")
    assert (stopped["cost_usd"], stopped["cost_estimated"], stopped["tokens_in"],
            stopped["off_pinned_setting"]) == (0.0, 0, 0, 0)
    assert answered["request_path"] == CHAT and answered["provider_error"] is None
    (run,) = rows(db, "SELECT cost_so_far FROM runs")
    assert run["cost_so_far"] == pytest.approx(answered["cost_usd"])        # only the real call was paid for
    # A stopped request is still a line in the trace, so it still takes one of the 70 slots.
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 2
    finally:
        conn.close()


def test_every_trace_line_records_the_path_it_was_sent_to(real, as_openai, tmp_path):
    as_openai.script(Reply(good_answer()))
    db = tmp_path / "spike.db"
    spike.run_first_call(real, spike_db=db)
    (line,) = rows(db, "SELECT request_path FROM trace")
    assert line["request_path"] == CHAT


# --- A refusal that is not swallowed: the unit fails, once, with nothing sent -------------------

def test_a_refused_chat_request_fails_the_unit_without_a_retry_and_sends_nothing(
        real, as_openai, monkeypatch):
    """Make the guard refuse EVERYTHING, so the one request that matters is stopped. That must not
    look like a provider failure: no DL-43 retry (it would only be stopped again), nothing sent,
    nothing charged, and a reason that is ours rather than CrewAI's generic 'connection error'."""
    monkeypatch.setattr(crews, "is_chat_completion", lambda method, path: False)
    as_openai.script(Reply(good_answer()))
    lines = []
    with pytest.raises(crews.ModelServiceError, match="refused before sending") as caught:
        extract(real, record=lines.append)
    assert paths(as_openai) == [] and as_openai.unused() == 1   # nothing reached the server
    assert len(caught.value.attempts) == 1                      # one try, not two: no retry
    (line,) = lines
    assert (line.cost_usd, line.cost_estimated, line.tokens_in) == (0.0, False, 0)
    assert line.request_path == CHAT and line.provider_error.startswith("refused before sending")
    assert not line.off_pinned_setting


def test_the_spike_reports_a_refused_request_in_words_and_charges_nothing(
        real, as_openai, monkeypatch, tmp_path):
    monkeypatch.setattr(crews, "is_chat_completion", lambda method, path: False)
    db = tmp_path / "spike.db"
    printed: list[str] = []
    code = spike.main(["--go"], env={
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": "gpt-6-test-e"}, spike_db=db, out=printed.append,
        read_line=lambda prompt: spike.FIRST_CALL_DOCUMENT)
    text = "\n".join(printed)
    assert code == 1 and "NOT USABLE - model service: refused before sending" in text
    assert "Path         : /v1/chat/completions" in text and "Cost         : US$0.0000" in text
    assert paths(as_openai) == []
    assert rows(db, "SELECT cost_so_far FROM runs")[0]["cost_so_far"] == 0


def test_a_normal_call_is_untouched_by_the_guard(real, as_openai):
    """The guard must not change a good call: one chat request, one line, the usual numbers."""
    as_openai.script(Reply(good_answer(), tokens_in=1500, tokens_out=360))
    lines = []
    extract(real, record=lines.append)
    (line,) = lines
    assert paths(as_openai) == [CHAT] and line.request_path == CHAT
    assert (line.tokens_in, line.tokens_out, line.stop_reason, line.provider_error) == (
        1500, 360, "stop", None)
