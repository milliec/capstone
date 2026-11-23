"""T-SPIKE-6 (Tier 1): the spike's JUDGE call, `--step judge` (B3 spike PR 3, step 2).
Fake OpenAI only: no real key, no real model, no paid call. CrewAI is made to behave as if it were on
api.openai.com (the `as_openai` fixture), so the request is the one a real call would be.

What the plan promised, and what these tests pin down:
  * ONE Stage B judge call on the ANSWER-KEY row of SRC-UCILAW-P3, with the fund's facts and events.
    The answer key says: applies, citing FACT-01. Same input every run.
  * The DL-40 settings for the judge: reasoning_effort medium, max_completion_tokens 4000, and NO
    temperature.
  * It sends only when the operator types exactly `judge SRC-UCILAW-P3` (the verifier's words do not
    confirm it); every refusal comes first.
  * The result says CORRECT or WRONG against the answer key, and never calls a wrong verdict a
    mechanical failure. A cut-off, an invalid answer or a refused request are the failures.
  * It takes one trace line (one of the 70 call slots) per request, priced at the judge's prices.
"""

import copy
import json

import pytest

from backend.db.connection import connect
from backend.domain import fund_facts
from backend.domain.schemas import Verdict
from backend.runtime import agents, crews, harness, model_settings, spike
from backend.runtime.wire_schema import wire_schema
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_one_request import CHAT
from tests.tier1.test_spike_call import good_answer as extractor_answer

ROW = spike.FIRST_JUDGE_ROW                                    # SRC-UCILAW-P3
CONFIRM = f"judge {ROW}"
ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
       "LLM_MODEL_JUDGE": "gpt-6-test-j"}                      # only the judge's model is set


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


def key_answer():
    """The answer key's own verdict for this row, as a model would send it."""
    return copy.deepcopy(agents._stand_in("judge")[ROW])


def rows(db, sql):
    conn = connect(db)
    try:
        return [dict(r) for r in conn.execute(sql)]
    finally:
        conn.close()


# --- The dry-run: what would be sent ------------------------------------------------------------

def test_the_dry_run_plans_the_judge_call_and_sends_nothing(fake_openai, tmp_path):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(["--step", "judge"], db)
    facts = fund_facts.load_fund_facts()
    assert code == 0 and "SPIKE DRY-RUN: nothing was sent" in text
    for expected in ("judge_applicability (Stage B judge, ONE call)", f"Row            : {ROW} - ",
                     "the answer-key row", f"{len(facts['facts'])} fund facts",
                     f"{len(facts['events'])} event(s)", "The answer key says: applies, citing FACT-01",
                     "Model          : gpt-6-test-j", "Worst case", "0 of 70 used",
                     f"--step judge --go. You will be asked to type exactly: {CONFIRM}"):
        assert expected in text, expected
    # The settings the operator approved: reasoning_effort medium, 4000 tokens, NO temperature.
    assert '"reasoning_effort": "medium"' in text and '"max_completion_tokens": 4000' in text
    assert '"temperature"' not in text
    assert "Temperature    : NOT sent (DL-40: the judge runs with no temperature)" in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()
    assert TEST_API_KEY not in text


def test_the_judge_plans_only_the_row_the_answer_key_has_a_verdict_for():
    assert spike.answer_key_row(ROW, "judge")["source_paragraph_id"] == ROW
    with pytest.raises(spike.SpikeRefused, match="not a row this step plans a judge call for"):
        spike.answer_key_row("SRC-UCILAW-P2", "judge")


# --- Sending: only when the exact words are typed ----------------------------------------------

def test_typing_the_exact_words_sends_one_judge_request_with_the_pinned_settings(
        fake_openai, tmp_path):
    fake_openai.script(Reply(key_answer(), tokens_in=1000, tokens_out=700))
    db = tmp_path / "spike.db"
    code, text, prompts = command(["--step", "judge", "--go"], db)

    assert code == 0 and len(prompts) == 1 and CONFIRM in prompts[0]
    assert [r.path for r in fake_openai.requests] == [CHAT] and fake_openai.unscripted == []
    body = fake_openai.requests[0].body
    assert body["model"] == "gpt-6-test-j"
    assert body["reasoning_effort"] == "medium" and body["max_completion_tokens"] == 4000
    assert "temperature" not in body                               # not sent at all
    sent_schema = body["response_format"]
    assert sent_schema["json_schema"]["strict"] is True
    assert sent_schema == wire_schema(Verdict)                     # exactly the judge's wire schema
    assert "minItems" not in json.dumps(sent_schema)               # dropped before a real call

    sent = json.dumps(body["messages"], ensure_ascii=False)       # a long dash stays a long dash
    facts = fund_facts.load_fund_facts()
    for fact in facts["facts"]:                                    # every fact, as ID, fact and value
        assert fact["fact_id"] in sent and fact["value"] in sent
    for event in facts["events"]:
        assert event["event_id"] in sent
    assert "within six months of the end of the period" in sent    # the row, with its quote
    assert "Decides" not in sent                                   # the profile's answer column stays home

    for expected in ("SPIKE PLAN: nothing has been sent yet", "SPIKE RESULT: a request WAS sent",
                     "Answer         : VALID (1 verdict(s) passed the guardrail)",
                     "Answer key       : applies, citing FACT-01",
                     "Judge's verdict  : applies, citing FACT-01 - CORRECT",
                     f"Unit           : {ROW}#1", "Path         : /v1/chat/completions",
                     "Tokens       : 1000 in, 700 out", "Off pinned setting : no"):
        assert expected in text, expected
    assert TEST_API_KEY not in text

    (line,) = rows(db, "SELECT * FROM trace")
    assert (line["step"], line["unit_id"], line["model"]) == ("judge_applicability", f"{ROW}#1", "gpt-6-test-j")
    assert json.loads(line["settings_json"]) == {"max_completion_tokens": 4000, "reasoning_effort": "medium"}
    assert (line["request_path"], line["late"], line["cost_estimated"]) == (CHAT, 0, 0)
    assert line["cost_usd"] == pytest.approx(model_settings.call_cost_usd("judge", 1000, 700))
    assert line["cost_usd"] == pytest.approx((1000 * 1.00 + 700 * 5.00) / 1_000_000)   # judge prices
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 1
    finally:
        conn.close()


@pytest.mark.parametrize("typed", ["", ROW, "judge", f"judge {ROW.lower()}", f"verify {ROW}",
                                   "extract SRC-UCILAW", "SRC-UCILAW", f"judge  {ROW}x"])
def test_anything_but_the_exact_words_cancels_and_the_verifiers_words_do_not_count(
        fake_openai, tmp_path, typed):
    db = tmp_path / "data" / "spike.db"
    code, text, _ = command(["--step", "judge", "--go"], db, typed=typed)
    assert code == 2 and "NOT CONFIRMED: nothing was sent." in text
    assert fake_openai.requests == [] and not db.exists()


@pytest.mark.parametrize("closed", [EOFError(), OSError("no terminal")])
def test_nobody_to_ask_counts_as_not_confirmed(fake_openai, tmp_path, closed):
    code, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db", typed=closed)
    assert code == 2 and "NOT CONFIRMED" in text and fake_openai.requests == []


@pytest.mark.parametrize("env,argv,reason", [
    ({**ENV, "AGENTS_MODE": "stand_in"}, ["--step", "judge", "--go"], "AGENTS_MODE"),
    ({**ENV, "SPEND_ACTIVITY": "tuning"}, ["--step", "judge", "--go"], "SPEND_ACTIVITY"),
    ({**ENV, "OPENAI_API_KEY": ""}, ["--step", "judge", "--go"], "OPENAI_API_KEY"),
    ({**ENV, "LLM_MODEL_JUDGE": ""}, ["--step", "judge", "--go"], "LLM_MODEL_JUDGE"),
    # Neither the extractor's nor the verifier's model stands in for the judge's.
    ({**ENV, "LLM_MODEL_JUDGE": "", "LLM_MODEL_EXTRACT": "gpt-6-test-e", "LLM_MODEL_VERIFY": "gpt-6-test-v"},
     ["--step", "judge", "--go"], "LLM_MODEL_JUDGE"),
    (ENV, ["--step", "judge", "--go", "--row", "SRC-UCILAW-P2"], "not a row this step plans"),
    (ENV, ["--step", "judge", "--go", "--row", "SRC-NOPE"], "not a row this step plans"),
])
def test_a_refusal_comes_before_the_prompt(fake_openai, tmp_path, env, argv, reason):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(argv, db, env=env)
    assert code == 2 and text.startswith("REFUSED:") and reason in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()


# --- What the result says ----------------------------------------------------------------------

def test_a_different_verdict_is_called_wrong_but_it_is_not_a_failure(fake_openai, tmp_path):
    unsure = {"verdict": "unsure", "cited_fact_ids": ["FACT-01"],
              "reasoning": "The report's scope is not clear.",
              "missing_information": "Whether Part II covers this report."}
    fake_openai.script(Reply(unsure))
    code, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db")
    assert code == 0                                              # a usable answer, but not the key's
    assert "VALID (1 verdict(s)" in text
    assert "Judge's verdict  : unsure, citing FACT-01 - WRONG (the answer key says applies, citing FACT-01)" in text
    assert "Missing info     : Whether Part II covers this report." in text


def test_the_right_verdict_citing_the_wrong_fact_is_wrong(fake_openai, tmp_path):
    answer = key_answer() | {"cited_fact_ids": ["FACT-02"]}
    fake_openai.script(Reply(answer))
    code, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db")
    assert code == 0 and "applies, citing FACT-02 - WRONG" in text


def test_citing_the_right_fact_among_others_is_correct(fake_openai, tmp_path):
    answer = key_answer() | {"cited_fact_ids": ["FACT-02", "FACT-01"]}
    fake_openai.script(Reply(answer))
    _, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db")
    assert "applies, citing FACT-02, FACT-01 - CORRECT" in text


def test_assess_judgement_reads_the_verdict_not_the_prose():
    right = Verdict.model_validate(key_answer())
    assert "CORRECT" in spike.assess_judgement(ROW, right)[1]
    wrong = Verdict.model_validate({**key_answer(), "verdict": "does_not_apply"})
    assert "WRONG" in spike.assess_judgement(ROW, wrong)[1]


# --- When it goes wrong: said plainly, nothing repeated -----------------------------------------

@pytest.mark.parametrize("answer,reason", [
    (key_answer() | {"cited_fact_ids": ["FACT-99"]}, "not in its input"),               # an invented ID
    (key_answer() | {"cited_fact_ids": []}, "schema"),                                  # cites nothing
    (key_answer() | {"missing_information": "Something is unknown."}, "schema"),        # applies, yet 'missing'
    (key_answer() | {"reasoning": "Due by 2031-06-30."}, "date"),                       # an invented date
    ({"verdict": "applies"}, "schema"),                                                 # keys missing
])
def test_an_answer_the_guardrail_refuses_is_reported_and_not_asked_for_again(
        fake_openai, tmp_path, answer, reason):
    fake_openai.script(Reply(answer))
    db = tmp_path / "spike.db"
    code, text, _ = command(["--step", "judge", "--go"], db)
    assert code == 1 and "NOT USABLE - invalid output" in text and "Stopped. Nothing was repeated" in text
    assert reason in text
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []
    (line,) = rows(db, "SELECT validation_error, cost_usd FROM trace")
    assert line["validation_error"] and line["cost_usd"] > 0     # a bad answer is still billed


def test_an_answer_cut_off_by_the_token_limit_is_reported_with_its_stop_reason(fake_openai, tmp_path):
    """A reasoning model can use up max_completion_tokens before it writes an answer. The stop reason
    says so, and the operator's stop rule applies."""
    fake_openai.script(Reply("", tokens_in=1000, tokens_out=4000, finish_reason="length"))
    code, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE" in text
    assert "Stop reason  : length" in text and "Tokens       : 1000 in, 4000 out" in text


def test_a_failed_request_is_retried_once_and_both_are_traced(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Reply(key_answer()))
    db = tmp_path / "spike.db"
    code, _, _ = command(["--step", "judge", "--go"], db)
    assert code == 0 and len(fake_openai.requests) == 2
    first, second = rows(db, "SELECT * FROM trace ORDER BY trace_id")
    assert (first["attempt_n"], second["attempt_n"]) == (1, 2)
    assert first["provider_error"] and first["cost_estimated"] == 1 and second["provider_error"] is None


def test_two_failed_requests_are_reported_and_both_are_billed(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Failure(503, "Overloaded"))
    code, text, _ = command(["--step", "judge", "--go"], tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE - model service" in text and "ESTIMATED" in text
    assert len(fake_openai.requests) == 2


# --- Sharing one spike run with the other steps -------------------------------------------------

def test_each_step_numbers_its_own_calls_and_all_three_share_one_run_and_one_count(
        fake_openai, tmp_path):
    env = {**ENV, "LLM_MODEL_EXTRACT": "gpt-6-test-e", "LLM_MODEL_VERIFY": "gpt-6-test-v"}
    verifier_flags = agents._stand_in("verifier")[ROW]
    db = tmp_path / "spike.db"
    fake_openai.script(Reply(extractor_answer()), Reply({"flags": verifier_flags}),
                       Reply(key_answer()), Reply(key_answer()))
    assert command(["--go"], db, typed="SRC-UCILAW", env=env)[0] == 0                     # extractor
    assert command(["--step", "verify", "--go"], db, typed=f"verify {ROW}", env=env)[0] == 0
    assert command(["--step", "judge", "--go"], db, env=env)[0] == 0
    assert command(["--step", "judge", "--go"], db, env=env)[0] == 0
    units = [(r["step"], r["unit_id"]) for r in rows(db, "SELECT step, unit_id FROM trace ORDER BY trace_id")]
    assert units == [("extract_rows", "SRC-UCILAW#1"), ("check_conflicts", f"{ROW}#1"),
                     ("judge_applicability", f"{ROW}#1"), ("judge_applicability", f"{ROW}#2")]
    assert len(rows(db, "SELECT * FROM runs")) == 1                                       # ONE spike run
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 4                                # 4 of 70
    finally:
        conn.close()
    _, text, _ = command(["--step", "judge"], db, env=env)
    assert "4 of 70 used" in text
