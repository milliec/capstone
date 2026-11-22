"""T-REQ-1 (Tier 1): one unit sends exactly the requests we expect, and nothing else, even when
CrewAI believes it is talking to OpenAI itself (spike fix, step B). Fake OpenAI only.

Why this file exists. The first real spike call (RUN-20261122-1) sent TWO requests. The first was
not a model call at all: CrewAI's own pre-flight, `POST /v1/responses/input_tokens`, which counts the
prompt's tokens. CrewAI only does that when the server is OpenAI itself, so every earlier test (all
against a fake on 127.0.0.1) was blind to it. The `as_openai` fixture (tests/conftest.py) closes that
gap: CrewAI behaves as if it were on api.openai.com, and the fake answers the count endpoint.

These tests fail if the pre-flight comes back (step A, `respect_context_window=False` in
backend/runtime/crews.py).
"""

import copy

import pytest

from backend.db.connection import connect
from backend.domain import sources
from backend.runtime import agents, crews, harness, spike
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY, Failure, Reply

DOC = spike.FIRST_CALL_DOCUMENT           # SRC-UCILAW, the document of the first real call
CHAT = "/v1/chat/completions"
COUNT = "/v1/responses/input_tokens"


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def real(as_openai):
    """Real mode, pointed at the fake, with CrewAI believing the fake is OpenAI."""
    return load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                          "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e"})


def good_answer():
    return {"rows": copy.deepcopy(agents._stand_in("extractor")[DOC])}


def extract(settings, record=None):
    own = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()
           if p["document_id"] == DOC}
    return agents.extract_rows(settings, document_id=DOC, paragraphs=own,
                               recipient_codes=list(sources.list_recipients()), record=record)


def paths(fake):
    return [request.path for request in fake.requests]


def test_one_unit_is_one_request_even_when_crewai_thinks_it_is_openai(real, as_openai):
    as_openai.script(Reply(good_answer(), tokens_in=1500, tokens_out=360))
    lines = []
    extract(real, record=lines.append)
    assert paths(as_openai) == [CHAT]                       # no count request, nothing else
    (line,) = lines                                         # and so exactly one trace line
    assert line.attempt_n == 1 and not line.cost_estimated and not line.off_pinned_setting
    assert (line.tokens_in, line.tokens_out, line.stop_reason) == (1500, 360, "stop")


def test_the_fixture_is_not_an_empty_shell_crewai_still_tries_the_preflight_and_the_guard_stops_it(
        real, as_openai, monkeypatch):
    """Proof that the test above can fail. Put the pre-flight back and CrewAI DOES try it (so the
    fixture is real). Since spike fix step D that request is stopped before it is sent: the fake
    never sees it, CrewAI falls back to its own estimate and makes the real call, and the trace has
    a line for what was stopped (T-REQ-2 tests the guard in detail)."""
    build = crews.build_crew

    def with_the_preflight_back(*args, **kwargs):
        crew = build(*args, **kwargs)
        for agent in crew.agents:
            agent.respect_context_window = True             # CrewAI's default
        return crew
    monkeypatch.setattr(crews, "build_crew", with_the_preflight_back)
    as_openai.script(Reply(good_answer()))
    lines = []
    extract(real, record=lines.append)
    assert paths(as_openai) == [CHAT]                       # the count request never left
    stopped, answered = lines
    assert stopped.request_path == COUNT and "refused before sending" in stopped.provider_error
    assert answered.request_path == CHAT and answered.provider_error is None


def test_the_spike_call_is_one_request_one_trace_line_and_one_slot_of_the_70(real, as_openai,
                                                                             tmp_path):
    """The exact case that went wrong: it used 2 of the 70 call slots for one model call."""
    as_openai.script(Reply(good_answer(), tokens_in=1500, tokens_out=360))
    db = tmp_path / "spike.db"
    result = spike.run_first_call(real, spike_db=db)
    assert result.ok and paths(as_openai) == [CHAT]
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 1
        (line,) = [dict(r) for r in conn.execute("SELECT * FROM trace")]
    finally:
        conn.close()
    assert (line["cost_estimated"], line["off_pinned_setting"], line["model_returned"]) == (
        0, 0, "gpt-6-test-e")
    assert '"reasoning_effort": "none"' in line["settings_json"]       # the pinned settings were sent


def test_a_retry_adds_one_more_chat_request_and_still_no_count_request(real, as_openai):
    as_openai.script(Failure(503, "Overloaded"), Reply(good_answer()))
    extract(real)
    assert paths(as_openai) == [CHAT, CHAT]                 # DL-43: the call and its one retry
