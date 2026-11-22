"""T-SPIKE-5 (Tier 1): the spike's VERIFIER call, `--step verify` (B3 spike PR 3, step 1).
Fake OpenAI only: no real key, no real model, no paid call. CrewAI is made to behave as if it were on
api.openai.com (the `as_openai` fixture), so the request is the one a real call would be.

What the plan promised, and what these tests pin down:
  * ONE Stage B verifier call on the ANSWER-KEY row of SRC-UCILAW-P3, where the planted conflict C-1
    sits (SRC-PRACT-P1 says four months, the row says six). Same input every run.
  * The DL-40 settings for the verifier: reasoning_effort low, max_completion_tokens 2000, and NO
    temperature (the operator's decision, 2026-11-22).
  * It sends only when the operator types exactly `verify SRC-UCILAW-P3`; every refusal comes first.
  * The result says CAUGHT or MISSED, and calls an internal flag a false alarm.
  * It takes one trace line (one of the 70 call slots) per request, priced at the verifier's prices.
"""

import copy
import json

import pytest

from backend.db.connection import connect
from backend.domain import sources
from backend.domain.schemas import Flag
from backend.runtime import agents, crews, harness, model_settings, spike
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_one_request import CHAT
from tests.tier1.test_spike_call import good_answer as extractor_answer

ROW = spike.FIRST_VERIFY_ROW                                   # SRC-UCILAW-P3
CONFIRM = f"verify {ROW}"
ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
       "LLM_MODEL_VERIFY": "gpt-6-test-v"}                     # only the verifier's model is set


@pytest.fixture(autouse=True)
def aimed_at_the_fake_as_openai(as_openai, monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)
    return as_openai


def command(argv, db, *, typed=CONFIRM, env=None):
    printed, prompts = [], []

    def read_line(prompt):
        prompts.append(prompt)
        if isinstance(typed, BaseException):
            raise typed
        return typed
    code = spike.main(argv, env=env or ENV, spike_db=db, out=printed.append, read_line=read_line)
    return code, "\n".join(printed), prompts


def caught_flag():
    """The answer key's own flag for this row: a cross-source flag citing SRC-PRACT-P1."""
    return copy.deepcopy(agents._stand_in("verifier")[ROW][0])


def rows(db, sql):
    conn = connect(db)
    try:
        return [dict(r) for r in conn.execute(sql)]
    finally:
        conn.close()


# --- The dry-run: what would be sent ------------------------------------------------------------

def test_the_dry_run_plans_the_verifier_call_and_sends_nothing(fake_openai, tmp_path):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(["--step", "verify"], db)
    n = len(sources.load_paragraphs())
    assert code == 0 and "SPIKE DRY-RUN: nothing was sent" in text
    for expected in ("check_conflicts (Stage B verifier, ONE call)", f"Row            : {ROW} - ",
                     "the answer-key row", f"all {n} loaded paragraphs", "Planted conflict C-1",
                     "Model          : gpt-6-test-v", "Worst case", "0 of 70 used",
                     f"exactly: {CONFIRM}"):
        assert expected in text, expected
    # The settings the operator approved: reasoning_effort low, 2000 tokens, NO temperature.
    assert '"reasoning_effort": "low"' in text and '"max_completion_tokens": 2000' in text
    assert '"temperature"' not in text
    assert "Temperature    : NOT sent" in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()
    assert TEST_API_KEY not in text


def test_the_answer_key_row_is_the_fixed_input():
    row = spike.answer_key_row(ROW)
    assert row["source_paragraph_id"] == ROW and row["offset"] == {"unit": "months", "amount": 6}
    assert row["quote"] == "within six months of the end of the period to which it relates"
    with pytest.raises(spike.SpikeRefused, match="not a row this step plans"):
        spike.answer_key_row("SRC-UCILAW-P2")


# --- Sending: only when the exact words are typed ----------------------------------------------

def test_typing_the_exact_words_sends_one_verifier_request_with_the_pinned_settings(
        fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [caught_flag()]}, tokens_in=1900, tokens_out=300))
    db = tmp_path / "spike.db"
    code, text, prompts = command(["--step", "verify", "--go"], db)

    assert code == 0 and len(prompts) == 1 and CONFIRM in prompts[0]
    assert [r.path for r in fake_openai.requests] == [CHAT] and fake_openai.unscripted == []
    body = fake_openai.requests[0].body
    assert body["model"] == "gpt-6-test-v"
    assert body["reasoning_effort"] == "low" and body["max_completion_tokens"] == 2000
    assert "temperature" not in body                               # not sent at all (the decision)
    assert "response_format" in body                               # the strict answer schema
    sent = json.dumps(body["messages"])
    for must_carry in ("SRC-PRACT-P1", "within four months", "within six months of the end of the period",
                       "passed"):
        assert must_carry in sent, must_carry
    for paragraph in sources.load_paragraphs():                    # EVERY loaded paragraph, as Stage B does
        assert paragraph["paragraph_id"] in sent

    for expected in ("SPIKE PLAN: nothing has been sent yet", "SPIKE RESULT: a request WAS sent",
                     "Answer         : VALID (1 flag(s) passed the guardrail)",
                     "Planted C-1   : CAUGHT", "False alarms     : none",
                     f"Unit           : {ROW}#1", "Path         : /v1/chat/completions",
                     "Tokens       : 1900 in, 300 out", "Off pinned setting : no"):
        assert expected in text, expected
    assert TEST_API_KEY not in text

    (line,) = rows(db, "SELECT * FROM trace")
    assert (line["step"], line["unit_id"], line["model"]) == ("check_conflicts", f"{ROW}#1", "gpt-6-test-v")
    assert json.loads(line["settings_json"]) == {"max_completion_tokens": 2000, "reasoning_effort": "low"}
    assert (line["request_path"], line["late"], line["cost_estimated"]) == (CHAT, 0, 0)
    assert line["cost_usd"] == pytest.approx(model_settings.call_cost_usd("verify", 1900, 300))
    assert line["cost_usd"] == pytest.approx((1900 * 2.00 + 300 * 12.00) / 1_000_000)   # verifier prices
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 1         # one request, one of the 70 slots
    finally:
        conn.close()


@pytest.mark.parametrize("typed", ["", ROW, "verify", f"verify {ROW.lower()}", f"verify  {ROW}x",
                                   "extract SRC-UCILAW", "SRC-UCILAW"])
def test_anything_but_the_exact_words_cancels(fake_openai, tmp_path, typed):
    db = tmp_path / "data" / "spike.db"
    code, text, _ = command(["--step", "verify", "--go"], db, typed=typed)
    assert code == 2 and "NOT CONFIRMED: nothing was sent." in text
    assert fake_openai.requests == [] and not db.exists()


@pytest.mark.parametrize("closed", [EOFError(), OSError("no terminal")])
def test_nobody_to_ask_counts_as_not_confirmed(fake_openai, tmp_path, closed):
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db", typed=closed)
    assert code == 2 and "NOT CONFIRMED" in text and fake_openai.requests == []


@pytest.mark.parametrize("env,argv,reason", [
    ({**ENV, "AGENTS_MODE": "stand_in"}, ["--step", "verify", "--go"], "AGENTS_MODE"),
    ({**ENV, "SPEND_ACTIVITY": "tuning"}, ["--step", "verify", "--go"], "SPEND_ACTIVITY"),
    ({**ENV, "OPENAI_API_KEY": ""}, ["--step", "verify", "--go"], "OPENAI_API_KEY"),
    ({**ENV, "LLM_MODEL_VERIFY": ""}, ["--step", "verify", "--go"], "LLM_MODEL_VERIFY"),
    # The EXTRACTOR's model does not stand in for the verifier's.
    ({**ENV, "LLM_MODEL_VERIFY": "", "LLM_MODEL_EXTRACT": "gpt-6-test-e"},
     ["--step", "verify", "--go"], "LLM_MODEL_VERIFY"),
    (ENV, ["--step", "verify", "--go", "--row", "SRC-UCILAW-P2"], "not a row this step plans"),
    (ENV, ["--step", "verify", "--go", "--row", "SRC-NOPE"], "not a row this step plans"),
])
def test_a_refusal_comes_before_the_prompt(fake_openai, tmp_path, env, argv, reason):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(argv, db, env=env)
    assert code == 2 and text.startswith("REFUSED:") and reason in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()


# --- What the result says ----------------------------------------------------------------------

def test_a_miss_is_said_plainly_and_points_at_dl_26(fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": []}))
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db")
    assert code == 0                                              # a usable answer, but the wrong one
    assert "VALID (0 flag(s)" in text and "Planted C-1   : MISSED" in text
    assert "DL-26" in text and "CAUGHT" not in text


def test_an_internal_flag_on_this_correct_row_is_a_false_alarm(fake_openai, tmp_path):
    internal = {"flag_type": "internal", "explanation": "The offset looks wrong.", "field": "offset",
                "row_value": "6 months", "quote_says": "within six months"}
    fake_openai.script(Reply({"flags": [caught_flag(), internal]}))
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db")
    assert code == 0 and "Planted C-1   : CAUGHT" in text
    assert "False alarms     : 1 internal flag(s)" in text and "offset: row says '6 months'" in text
    assert "Verifier said    : [internal] The offset looks wrong." in text


def test_a_flag_on_another_paragraph_does_not_count_as_catching_the_conflict(fake_openai, tmp_path):
    paragraphs = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    other = {"flag_type": "cross_source", "explanation": "Something else.",
             "other_paragraph_id": "SRC-PRACT-P2",
             "other_quote": " ".join(paragraphs["SRC-PRACT-P2"].split()[:5])}
    fake_openai.script(Reply({"flags": [other]}))
    _, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db")
    assert "Planted C-1   : MISSED" in text
    assert "Other flags      : cross-source on SRC-PRACT-P2 (not the planted conflict: read it)" in text


def test_assess_verification_reads_flags_not_prose():
    caught = Flag.model_validate(caught_flag())
    assert spike.assess_verification(ROW, [caught])[0].startswith("Planted C-1   : CAUGHT")
    assert spike.assess_verification(ROW, [])[0].startswith("Planted C-1   : MISSED")


# --- When it goes wrong: said plainly, nothing repeated -----------------------------------------

def test_an_answer_that_does_not_fit_the_schema_is_reported_and_not_asked_for_again(
        fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [{"nonsense": 1}]}))
    db = tmp_path / "spike.db"
    code, text, _ = command(["--step", "verify", "--go"], db)
    assert code == 1 and "NOT USABLE - invalid output" in text and "Stopped. Nothing was repeated" in text
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    (line,) = rows(db, "SELECT validation_error, cost_usd FROM trace")
    assert line["validation_error"] and line["cost_usd"] > 0     # a bad answer is still billed


def test_a_quote_that_is_not_word_for_word_is_refused_by_the_guardrail(fake_openai, tmp_path):
    bad = caught_flag() | {"other_quote": "within five months of nothing at all"}
    fake_openai.script(Reply({"flags": [bad]}))
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db")
    assert code == 1 and "not word for word" in text


def test_a_failed_request_is_retried_once_and_both_are_traced(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Reply({"flags": [caught_flag()]}))
    db = tmp_path / "spike.db"
    code, text, _ = command(["--step", "verify", "--go"], db)
    assert code == 0 and len(fake_openai.requests) == 2
    first, second = rows(db, "SELECT * FROM trace ORDER BY trace_id")
    assert (first["attempt_n"], second["attempt_n"]) == (1, 2)
    assert first["provider_error"] and first["cost_estimated"] == 1 and second["provider_error"] is None
    assert text.count("Path         : /v1/chat/completions") == 2


def test_two_failed_requests_are_reported_and_both_are_billed(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Failure(503, "Overloaded"))
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE - model service" in text and "ESTIMATED" in text
    assert len(fake_openai.requests) == 2


# --- Sharing one spike run with the extractor ---------------------------------------------------

def test_each_step_numbers_its_own_calls_and_all_share_one_run_and_one_count(fake_openai, tmp_path):
    env = {**ENV, "LLM_MODEL_EXTRACT": "gpt-6-test-e"}
    db = tmp_path / "spike.db"
    fake_openai.script(Reply(extractor_answer()), Reply({"flags": [caught_flag()]}),
                       Reply({"flags": []}))
    assert command(["--go"], db, typed="SRC-UCILAW", env=env)[0] == 0                  # the extractor
    assert command(["--step", "verify", "--go"], db, env=env)[0] == 0
    assert command(["--step", "verify", "--go"], db, env=env)[0] == 0
    units = [(r["step"], r["unit_id"]) for r in rows(db, "SELECT step, unit_id FROM trace ORDER BY trace_id")]
    assert units == [("extract_rows", "SRC-UCILAW#1"), ("check_conflicts", f"{ROW}#1"),
                     ("check_conflicts", f"{ROW}#2")]
    assert len(rows(db, "SELECT * FROM runs")) == 1                                    # ONE spike run
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 3                             # 3 of 70
    finally:
        conn.close()
    # The next dry-run shows the count, for either step.
    _, text, _ = command(["--step", "verify"], db, env=env)
    assert "3 of 70 used" in text
