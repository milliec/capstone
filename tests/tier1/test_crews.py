"""B3 step 7b, PR 4: the CrewAI crews behind the three agent functions, tested against the fake
OpenAI (tests/fake_openai.py). Tier 1.

No real model, no real key, no outside connection: the fake runs on this machine and every key in
this file is a placeholder. The question every test asks is the one H-065 set: **how many requests
reached the provider, and what did each one say?** One unit sends exactly one request, whatever
the answer is (a good one, an invalid one, an error or a timeout): there is no re-ask and no hidden
retry in this PR. (The one retry DL-43 allows, and one trace line per attempt, are PR 5.)
"""

import copy
import json
import re

import pytest

from backend.db.connection import connect, init_db
from backend.domain import sources
from backend.domain.fund_facts import load_fund_facts
from backend.domain.quote_check import check_quote
from backend.domain.schemas import ExtractionResult, Verdict, VerificationResult
from backend.runtime import agents, crews, model_settings, prompts
from backend.runtime.wire_schema import wire_schema
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY, Failure, Reply

DOC = "SRC-CSSF15627"


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


@pytest.fixture
def real(fake_openai, monkeypatch):
    """Real mode, pointed at the fake: model IDs and a placeholder key, as the operator's .env would
    have them. CrewAI and the OpenAI client both read OPENAI_BASE_URL."""
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": "gpt-6-test-e", "LLM_MODEL_VERIFY": "gpt-6-test-v",
        "LLM_MODEL_JUDGE": "gpt-6-test-j", "DATABASE_PATH": "unused.db"})


@pytest.fixture(scope="module")
def paragraphs():
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


@pytest.fixture
def stand_in():
    return load_settings({"AGENTS_MODE": "stand_in", "STAND_IN_UNIT_PAUSE_S": "0"})


def _own(paragraphs, document_id=DOC):
    return {pid: t for pid, t in paragraphs.items() if pid.startswith(document_id + "-P")}


def _extract(settings, paragraphs, record=None):
    return agents.extract_rows(settings, document_id=DOC, paragraphs=_own(paragraphs),
                               recipient_codes=list(sources.list_recipients()), record=record)


def _good_answer(stand_in, paragraphs):
    """A valid answer for the extractor: the stand-in file's, as a model would send it. A COPY: the
    stand-in files are read once and cached, so a test that edits the answer must not edit them."""
    return {"rows": copy.deepcopy(agents._stand_in("extractor")[DOC])}


def _a_row(stand_in, paragraphs):
    row = _extract(stand_in, paragraphs)[0].model_dump()
    return row


def _sent(fake, n=0):
    return fake.requests[n].body


# --- The extractor: one request, the right settings, a checked answer ------------------------

def test_the_extractor_sends_one_request_with_its_dl_40_settings(real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Reply(_good_answer(stand_in, paragraphs)))
    rows = _extract(real, paragraphs)
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    body = _sent(fake_openai)
    assert body["model"] == "gpt-6-test-e"
    assert body["max_completion_tokens"] == 2000 and body["reasoning_effort"] == "none"
    assert body["temperature"] == 0
    assert fake_openai.requests[0].api_key == TEST_API_KEY
    # The answer went through the real guardrail and came back as rows, the same as stand-in.
    assert [r.model_dump() for r in rows] == [r.model_dump() for r in _extract(stand_in, paragraphs)]


def test_the_answers_shape_goes_as_a_strict_response_format(real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Reply(_good_answer(stand_in, paragraphs)))
    _extract(real, paragraphs)
    sent = _sent(fake_openai)["response_format"]
    assert sent == wire_schema(ExtractionResult)
    assert sent["type"] == "json_schema" and sent["json_schema"]["strict"] is True


def test_the_prompt_the_model_sees_is_the_rendered_prompt_and_holds_no_answer_key(
        real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Reply(_good_answer(stand_in, paragraphs)))
    _extract(real, paragraphs)
    text = "\n".join(m["content"] for m in _sent(fake_openai)["messages"])
    assert "Regulatory text extractor" in text and DOC in text
    for pid, paragraph in _own(paragraphs).items():
        assert pid in text and " ".join(paragraph.split())[:40] in text
    assert not re.search(r"OBL-|C-1|C-2|I-1|AMD-|Test note|Planted conflict", text)


def test_the_trace_line_says_what_was_sent_and_what_it_cost(real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Reply(_good_answer(stand_in, paragraphs), tokens_in=1200, tokens_out=300))
    lines = []
    _extract(real, paragraphs, record=lines.append)
    [line] = lines
    assert line.model == "gpt-6-test-e" and line.step == "extract_rows"
    assert json.loads(line.settings_json) == {"max_completion_tokens": 2000, "reasoning_effort": "none",
                                              "temperature": 0.0}
    assert line.max_tokens == 2000 and (line.tokens_in, line.tokens_out) == (1200, 300)
    assert line.cost_usd == pytest.approx(model_settings.call_cost_usd("extract", 1200, 300))
    assert line.prompt_version == prompts.prompt_version("extract_rows")     # no "+stand-in"
    assert line.validation_error is None and line.parsed_output and line.raw_output


# --- The verifier and the judge --------------------------------------------------------------

def test_the_verifier_sends_one_request_and_no_temperature(real, fake_openai, stand_in, paragraphs):
    row = _a_row(stand_in, paragraphs)
    quote_check = check_quote(row["quote"], row["source_paragraph_id"], paragraphs)
    fake_openai.script(Reply({"flags": []}))
    flags = agents.check_conflicts(real, row=row, quote_check=quote_check, sources=paragraphs)
    assert flags == [] and len(fake_openai.requests) == 1
    body = _sent(fake_openai)
    assert body["model"] == "gpt-6-test-v" and body["reasoning_effort"] == "low"
    assert body["max_completion_tokens"] == 2000 and "temperature" not in body
    assert body["response_format"] == wire_schema(VerificationResult)


def test_the_judge_sends_one_request_and_no_temperature(real, fake_openai, stand_in, paragraphs):
    row = _a_row(stand_in, paragraphs)
    facts = load_fund_facts()
    answer = {"verdict": "applies", "cited_fact_ids": [facts["facts"][0]["fact_id"]],
              "reasoning": "The fund meets the condition.", "missing_information": ""}
    fake_openai.script(Reply(answer))
    verdict = agents.judge_applicability(real, row=row, fund_facts=facts)
    assert verdict.verdict == "applies" and len(fake_openai.requests) == 1
    body = _sent(fake_openai)
    assert body["model"] == "gpt-6-test-j" and body["reasoning_effort"] == "medium"
    assert body["max_completion_tokens"] == 4000 and "temperature" not in body
    assert body["response_format"] == wire_schema(Verdict)


# --- A bad answer is final: one request, never a re-ask (D5, H-065) --------------------------

def test_an_answer_that_is_not_json_fails_the_unit_after_one_request(real, fake_openai, paragraphs):
    fake_openai.script(Reply("I could not find any rows, sorry."), Reply({"rows": []}))
    lines = []
    with pytest.raises(agents.InvalidOutput, match="not valid JSON"):
        _extract(real, paragraphs, record=lines.append)
    assert len(fake_openai.requests) == 1 and fake_openai.unused() == 1     # the model was not asked again
    assert lines[0].validation_error and lines[0].parsed_output is None and lines[0].raw_output


def test_an_answer_that_breaks_the_schema_fails_the_unit_after_one_request(real, fake_openai, paragraphs):
    fake_openai.script(Reply({"rows": [{"obligation_name": "Due 2027-01-10"}]}), Reply({"rows": []}))
    with pytest.raises(agents.InvalidOutput, match="schema"):
        _extract(real, paragraphs)
    assert len(fake_openai.requests) == 1 and fake_openai.unused() == 1


def test_an_answer_that_breaks_a_guardrail_fails_the_unit_after_one_request(
        real, fake_openai, stand_in, paragraphs):
    answer = _good_answer(stand_in, paragraphs)
    answer["rows"][0]["source_paragraph_id"] = "SRC-OTHER-P1"      # a paragraph of another document
    fake_openai.script(Reply(answer), Reply(_good_answer(stand_in, paragraphs)))
    with pytest.raises(agents.InvalidOutput):
        _extract(real, paragraphs)
    assert len(fake_openai.requests) == 1 and fake_openai.unused() == 1


# --- A provider failure is one attempt and one error (PR 5 adds the DL-43 retry) --------------

@pytest.mark.parametrize("failure", [Failure(500), Failure(503, "Overloaded"),
                                     Failure(429, "Rate limit", "rate_limit_exceeded"),
                                     Failure(400, "Bad request", "invalid_request_error")])
def test_a_provider_error_is_one_request_not_three(real, fake_openai, paragraphs, failure):
    """Left at CrewAI's defaults (agent `max_retry_limit` 2), a failing call is THREE requests."""
    fake_openai.script(failure, failure, failure, failure)
    with pytest.raises(crews.ModelServiceError):
        _extract(real, paragraphs)
    assert len(fake_openai.requests) == 1


def test_a_timeout_is_one_request_and_a_model_service_error(fake_openai, monkeypatch, paragraphs):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    # A 6 s call timeout puts the client's own timeout at 1 s (the call's minus 5 s, DL-43).
    settings = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                              "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e",
                              "CALL_TIMEOUT_EXTRACT": "6"})
    fake_openai.script(Reply({"rows": []}, delay_s=2.0), Reply({"rows": []}, delay_s=2.0))
    with pytest.raises(crews.ModelServiceError, match="timed out"):
        _extract(settings, paragraphs)
    assert len(fake_openai.requests) == 1


def test_a_provider_failure_writes_no_trace_line_yet(real, fake_openai, paragraphs):
    fake_openai.script(Failure(500))
    lines = []
    with pytest.raises(crews.ModelServiceError):
        _extract(real, paragraphs, record=lines.append)
    assert lines == []        # no answer came; PR 5 writes one line per attempt


# --- Refused before anything is sent ---------------------------------------------------------

def test_no_model_id_means_nothing_is_built_or_sent(fake_openai, monkeypatch, paragraphs):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    settings = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                              "OPENAI_API_KEY": TEST_API_KEY})
    with pytest.raises(model_settings.ModelNotSet):
        _extract(settings, paragraphs)
    assert fake_openai.requests == []


@pytest.mark.parametrize("key", ["", "sk-REPLACE-ME-placeholder-not-a-real-key"])
def test_no_key_or_the_placeholder_key_means_nothing_is_sent(fake_openai, monkeypatch, paragraphs, key):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    settings = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                              "OPENAI_API_KEY": key, "LLM_MODEL_EXTRACT": "gpt-6-test-e"})
    with pytest.raises(model_settings.KeyNotSet):
        _extract(settings, paragraphs)
    assert fake_openai.requests == []


def test_the_key_never_shows_when_the_settings_are_printed(real):
    assert TEST_API_KEY not in repr(real)


# --- The crew is built the way the SAD says (sad.md §2 settings table, H-065) ------------------

def test_the_crew_has_exactly_the_settings_the_sad_fixes(real, paragraphs):
    from crewai import Process
    inputs = prompts.extractor_inputs(document_id=DOC, document_title="t", paragraphs=_own(paragraphs),
                                      recipient_codes=["CSSF"])
    crew = crews.build_crew(real, "extract_rows", inputs)
    [agent], [task] = crew.agents, crew.tasks
    assert (agent.allow_delegation, agent.tools, agent.max_iter, agent.max_retry_limit) == (
        False, [], 1, 0)
    assert task.guardrail is None and task.output_pydantic is None and task.guardrail_max_retries == 0
    assert crew.process == Process.sequential and crew.max_rpm == 30 and not crew.memory
    llm = agent.llm
    assert llm.max_retries == 0 and llm.timeout == 85.0            # 90 s call timeout minus 5 s
    assert llm.max_completion_tokens == 2000 and llm.reasoning_effort == "none"
    assert llm.additional_params["response_format"] == wire_schema(ExtractionResult)


def test_all_three_agent_cards_say_max_iter_1():
    assert {name: card["max_iter"] for name, card in prompts.load_agents().items()} == {
        "extractor": 1, "verifier": 1, "judge": 1}


# --- CrewAI's own rate-limit retry is off ----------------------------------------------------

def test_crewais_own_rate_limit_retry_is_switched_to_one_attempt(real):
    """Found while building PR 4: CrewAI retries a 429 up to 3 times by itself, with waits and no
    setting for it. `load_crewai()` sets its attempt count to 1 (backend/runtime/crewai_setup.py).
    If a CrewAI upgrade renames that constant, `load_crewai()` stops the call and this fails."""
    from crewai.llms import retry
    crews.build_crew(real, "extract_rows", {"document_id": "d", "document_title": "t",
                                            "paragraphs": "p", "recipient_codes": "c"})
    assert retry._LLM_RATE_LIMIT_MAX_ATTEMPTS == 1


# --- The stage turns a provider failure into the run's "model service" reason -----------------

def test_a_provider_failure_fails_the_unit_as_model_service(conn, settings, monkeypatch):
    from backend.services import runs
    from tests import flow

    def provider_down(*args, **kwargs):
        raise crews.ModelServiceError("InternalServerError: Error code: 500")

    monkeypatch.setattr(agents, "extract_rows", provider_down)
    run_id = flow.start_to_g1(conn, settings)
    assert runs.get_run(conn, run_id)["status"] == "FAILED"
    reasons = {r["failure_reason"] for r in conn.execute(
        "SELECT failure_reason FROM units WHERE run_id = ? AND status = 'failed'", (run_id,))}
    assert reasons == {"model service"}
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0      # nothing stored (rule 9)


# --- Stand-in mode never reaches any of this (T-MODE-1) --------------------------------------

def test_stand_in_mode_sends_nothing_and_needs_no_model_id(fake_openai, stand_in, paragraphs):
    rows = _extract(stand_in, paragraphs)
    assert rows and fake_openai.requests == []
