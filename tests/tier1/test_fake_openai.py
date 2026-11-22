"""The fake OpenAI (tests/fake_openai.py) behaves like the real thing where it matters (B3 step 7b,
PR 3; Tier 1). It is checked with the real `openai` client, the one CrewAI uses, so PR 4 and PR 5
can trust it: answers parse, errors raise the right error, a slow answer times out, a refused setting
is refused, and above all **the count of requests is exact**.

No real model, no real key, no outside connection: everything goes to 127.0.0.1.
"""

import json

import openai
import pytest

from tests.fake_openai import TEST_API_KEY, Failure, Reply


def client(fake, *, max_retries=0, timeout=5.0):
    """The client as step 7b sets it (H-065): its own retries are OFF."""
    return openai.OpenAI(api_key=TEST_API_KEY, base_url=fake.base_url, max_retries=max_retries,
                         timeout=timeout)


def ask(c, **extra):
    return c.chat.completions.create(model="some-model", messages=[{"role": "user", "content": "hi"}],
                                     **extra)


# --- It answers ---------------------------------------------------------------------------

def test_a_scripted_answer_comes_back_with_its_text_and_token_counts(fake_openai):
    fake_openai.script(Reply({"rows": []}, tokens_in=900, tokens_out=40))
    done = ask(client(fake_openai))
    assert json.loads(done.choices[0].message.content) == {"rows": []}
    assert (done.usage.prompt_tokens, done.usage.completion_tokens) == (900, 40)
    assert done.choices[0].finish_reason == "stop" and done.model == "some-model"


def test_the_model_string_the_api_returns_can_differ_from_the_one_asked_for(fake_openai):
    fake_openai.script(Reply("ok", model="some-model-2026-01"))
    assert ask(client(fake_openai)).model == "some-model-2026-01"


def test_a_cut_off_answer_can_be_played(fake_openai):
    fake_openai.script(Reply("half an ans", finish_reason="length"))
    assert ask(client(fake_openai)).choices[0].finish_reason == "length"


def test_the_requests_body_is_kept_whole_so_a_test_can_check_what_was_sent(fake_openai):
    fake_openai.script(Reply("ok"))
    schema = {"type": "json_schema", "json_schema": {"name": "rows", "strict": True,
                                                       "schema": {"type": "object"}}}
    ask(client(fake_openai), max_completion_tokens=2000, reasoning_effort="none", temperature=0,
        response_format=schema)
    [seen] = fake_openai.requests
    assert seen.path == "/v1/chat/completions" and seen.model == "some-model"
    assert seen.body["max_completion_tokens"] == 2000 and seen.body["temperature"] == 0
    assert seen.body["response_format"] == schema and seen.body["reasoning_effort"] == "none"


# --- It fails, as the provider does -------------------------------------------------------

@pytest.mark.parametrize("failure,error", [
    (Failure(429, "Rate limit", "rate_limit_exceeded"), openai.RateLimitError),
    (Failure(500), openai.InternalServerError),
    (Failure(503, "Overloaded"), openai.InternalServerError),
    (Failure(401, "Bad key", "invalid_request_error"), openai.AuthenticationError),
])
def test_a_scripted_failure_raises_the_matching_client_error(fake_openai, failure, error):
    fake_openai.script(failure)
    with pytest.raises(error):
        ask(client(fake_openai))
    assert len(fake_openai.requests) == 1


def test_a_slow_answer_times_out_in_the_client_and_is_still_counted(fake_openai):
    fake_openai.script(Reply("too late", delay_s=0.6))
    with pytest.raises(openai.APITimeoutError):
        ask(client(fake_openai, timeout=0.2))
    assert len(fake_openai.requests) == 1


def test_a_setting_the_model_refuses_is_refused_and_still_counted(fake_openai):
    fake_openai.reject_params = frozenset({"reasoning_effort"})
    fake_openai.script(Reply("never reached"))
    with pytest.raises(openai.BadRequestError) as caught:
        ask(client(fake_openai), reasoning_effort="low")
    assert caught.value.param == "reasoning_effort" and caught.value.code == "unsupported_parameter"
    assert len(fake_openai.requests) == 1 and fake_openai.unused() == 1   # the answer was kept
    ask(client(fake_openai))                                              # without it: fine
    assert fake_openai.unused() == 0


# --- It counts, exactly -------------------------------------------------------------------

def test_every_request_is_counted_in_order(fake_openai):
    fake_openai.script(Reply("a"), Reply("b"), Reply("c"))
    c = client(fake_openai)
    for _ in range(3):
        ask(c)
    assert len(fake_openai.requests) == 3 and fake_openai.unused() == 0
    assert fake_openai.unscripted == []


def test_a_request_nobody_scripted_fails_and_is_written_down(fake_openai):
    with pytest.raises(openai.InternalServerError):
        ask(client(fake_openai))
    assert len(fake_openai.requests) == 1 and len(fake_openai.unscripted) == 1


def test_a_client_that_retries_on_its_own_makes_the_hidden_requests_visible(fake_openai):
    """Why this fake exists (H-065): the client's own retries would be a second request nobody
    sees. With max_retries=1 a failing call is TWO requests, and the count shows it."""
    fake_openai.script(Failure(500), Failure(500))
    with pytest.raises(openai.InternalServerError):
        ask(client(fake_openai, max_retries=1))
    assert len(fake_openai.requests) == 2


def test_with_the_clients_retries_off_a_failing_call_is_exactly_one_request(fake_openai):
    fake_openai.script(Failure(500), Failure(500))
    with pytest.raises(openai.InternalServerError):
        ask(client(fake_openai, max_retries=0))
    assert len(fake_openai.requests) == 1 and fake_openai.unused() == 1


# --- It is safe ---------------------------------------------------------------------------

def test_it_listens_on_this_machine_only_and_sees_only_the_placeholder_key(fake_openai):
    assert fake_openai.base_url.startswith("http://127.0.0.1:")
    fake_openai.script(Reply("ok"))
    ask(client(fake_openai))
    assert fake_openai.requests[0].api_key == TEST_API_KEY
