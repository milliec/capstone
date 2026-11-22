"""T-SPIKE-4 (Tier 1): the spike COMMAND's `--go`, its typed confirmation and its printed result
(B3 spike PR 2c). Against the fake OpenAI only: no real key, no real model, no paid call.

The promise being protected: a real request starts ONLY when the operator types the document ID.
Anything else (a wrong word, an empty line, closed input, a refusal) sends nothing. What the
operator then reads must say, in words, whether the answer was usable and what it cost.
"""

import pytest

from backend.runtime import crews, spike
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_attempt_trace import _forget_what_crewai_learned
from tests.tier1.test_spike_call import good_answer

DOC = spike.FIRST_CALL_DOCUMENT
ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
       "LLM_MODEL_EXTRACT": "gpt-6-test-e"}


@pytest.fixture(autouse=True)
def aimed_at_the_fake(fake_openai, monkeypatch):
    """The only place a request can go in these tests is the fake server on this machine."""
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


def command(argv, db, *, typed=DOC, env=None):
    """Run the command as the operator would. `typed` is what they type at the prompt: a string, or
    an exception to raise (closed input). Returns the exit code, the printed text, the prompts."""
    printed, prompts = [], []

    def read_line(prompt):
        prompts.append(prompt)
        if isinstance(typed, BaseException):
            raise typed
        return typed
    code = spike.main(argv, env=env or ENV, spike_db=db, out=printed.append, read_line=read_line)
    return code, "\n".join(printed), prompts


# --- The confirmation ---------------------------------------------------------------------------

def test_typing_the_document_id_sends_one_request_and_prints_the_result(fake_openai, tmp_path):
    fake_openai.script(Reply(good_answer(), tokens_in=900, tokens_out=300))
    code, text, prompts = command(["--go"], tmp_path / "spike.db")
    assert code == 0 and len(prompts) == 1 and DOC in prompts[0]
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    for expected in ("SPIKE PLAN: nothing has been sent yet", "SPIKE RESULT: a request WAS sent",
                     "Answer         : VALID", "Tokens       : 900 in, 300 out", "Cost         : US$",
                     "Stop reason  : stop", "Off pinned setting : no", "Run cost so far: US$",
                     "Endpoint       : http://127.0.0.1", "(set by OPENAI_BASE_URL)"):
        assert expected in text, expected
    assert TEST_API_KEY not in text                       # the key is never printed


def test_the_plan_and_the_endpoint_are_shown_before_the_prompt(fake_openai, tmp_path):
    fake_openai.script(Reply(good_answer()))
    order = []

    def read_line(prompt):
        order.append("prompt")
        return DOC
    spike.main(["--go"], env=ENV, spike_db=tmp_path / "spike.db",
               out=lambda line: order.append(line), read_line=read_line)
    before_prompt = "\n".join(order[:order.index("prompt")])
    assert "Worst case" in before_prompt and "Endpoint" in before_prompt
    assert "MAY COST MONEY" in before_prompt


@pytest.mark.parametrize("typed", ["", "yes", "y", "go", DOC.lower(), DOC + "X", "SRC-PRACT"])
def test_anything_but_the_document_id_cancels(fake_openai, tmp_path, typed):
    db = tmp_path / "data" / "spike.db"
    code, text, _ = command(["--go"], db, typed=typed)
    assert code == 2 and "NOT CONFIRMED: nothing was sent." in text
    assert fake_openai.requests == [] and not db.exists()      # not even the database was made


@pytest.mark.parametrize("closed", [EOFError(), OSError("reading from stdin while output is captured")])
def test_nobody_to_ask_counts_as_not_confirmed(fake_openai, tmp_path, closed):
    code, text, _ = command(["--go"], tmp_path / "spike.db", typed=closed)
    assert code == 2 and "NOT CONFIRMED" in text and fake_openai.requests == []


def test_spaces_around_the_typed_id_are_forgiven(fake_openai, tmp_path):
    fake_openai.script(Reply(good_answer()))
    code, _, _ = command(["--go"], tmp_path / "spike.db", typed=f"  {DOC}  ")
    assert code == 0 and len(fake_openai.requests) == 1


# --- A refusal comes BEFORE the prompt: you are never asked to confirm something refused --------

@pytest.mark.parametrize("env,argv,reason", [
    ({**ENV, "AGENTS_MODE": "stand_in"}, ["--go"], "AGENTS_MODE"),
    ({**ENV, "SPEND_ACTIVITY": "tuning"}, ["--go"], "SPEND_ACTIVITY"),
    ({**ENV, "OPENAI_API_KEY": ""}, ["--go"], "OPENAI_API_KEY"),
    ({**ENV, "LLM_MODEL_EXTRACT": ""}, ["--go"], "LLM_MODEL_EXTRACT"),
    (ENV, ["--go", "--document", "SRC-PRACT"], "not a primary source document"),
])
def test_a_refusal_comes_before_the_prompt(fake_openai, tmp_path, env, argv, reason):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(argv, db, env=env)
    assert code == 2 and text.startswith("REFUSED:") and reason in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()


# --- What the operator reads when it goes wrong --------------------------------------------------

def test_an_unusable_answer_is_said_plainly_and_nothing_is_repeated(fake_openai, tmp_path):
    fake_openai.script(Reply({"rows": [{"nonsense": 1}]}))
    code, text, _ = command(["--go"], tmp_path / "spike.db")
    assert code == 1                                       # called, but not a usable answer
    assert "Answer         : NOT USABLE - invalid output" in text
    assert "Guardrail" in text and "Stopped. Nothing was repeated" in text
    assert len(fake_openai.requests) == 1


def test_a_provider_failure_shows_each_request_and_the_estimated_cost(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Failure(503, "Overloaded"))
    code, text, _ = command(["--go"], tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE - model service" in text
    assert "Request 1      : no answer" in text and "Request 2      : no answer" in text
    assert "Provider error" in text and "ESTIMATED" in text
    assert len(fake_openai.requests) == 2


def test_a_call_off_the_pinned_setting_is_flagged(fake_openai, tmp_path):
    """A model that refuses `reasoning_effort`: CrewAI repeats the call without it (H-064 c). The
    printout must say so, because such a run is not a clean run of the pinned settings."""
    fake_openai.reject_params = frozenset({"reasoning_effort"})
    _forget_what_crewai_learned()
    try:
        fake_openai.script(Reply(good_answer()))
        code, text, _ = command(["--go"], tmp_path / "spike.db")
    finally:
        _forget_what_crewai_learned()
    assert code == 0 and "Off pinned setting : YES" in text


# --- The dry-run is unchanged, and the endpoint text is safe ------------------------------------

def test_without_go_it_is_still_a_dry_run_and_never_asks(fake_openai, tmp_path):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command([], db)
    assert code == 0 and "SPIKE DRY-RUN: nothing was sent" in text and "--go" in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()


def test_the_endpoint_line_shows_no_password(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://user:hunter2@proxy.example:8443/v1?key=abc")
    text = spike.endpoint_description()
    assert "proxy.example:8443" in text and "hunter2" not in text and "abc" not in text


def test_with_no_base_url_the_endpoint_is_openais_own(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    assert "api.openai.com" in spike.endpoint_description()
