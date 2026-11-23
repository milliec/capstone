"""T-SPIKE-7 (Tier 1): the verifier bake-off's four cases, `--step verify --case C-1|C-2|I-1|OK-1`
(B3 spike PR 4, PR 1). Fake OpenAI only: no real key, no real model, no paid call. CrewAI is made to
behave as if it were on api.openai.com (the `as_openai` fixture).

The operator's decisions of 2026-11-23, and what these tests pin down:
  * Four cases, each on a fixed answer-key row: C-1 and C-2 (a planted conflict between sources),
    I-1 (an injected conflict INSIDE the row: its offset changed to 30 days, its quote still 20) and
    OK-1 (a row that should get NO flag, the false-alarm check).
  * The verifier's settings for both candidates: reasoning_effort low, 2000 tokens, no temperature.
    Candidate 2 differs only by `LLM_MODEL_VERIFY` on the command line.
  * The typed words name the case AND the model (`verify C-2 gpt-5.6-terra`), so a forgotten override
    cannot quietly run the wrong candidate.
  * The result says CAUGHT or MISSED (planted cases) and CLEAN or FALSE ALARM (OK-1). A miss is a
    finding, not a failure; a cut-off, an invalid answer or a refused request are the failures.
  * The first call's `--row SRC-UCILAW-P3` path is unchanged.
"""

import json

import pytest

from backend.db.connection import connect
from backend.domain import sources
from backend.domain.quote_check import check_quote
from backend.domain.schemas import Flag, VerificationResult
from backend.runtime import agents, crews, harness, model_settings, spike
from backend.runtime.wire_schema import wire_schema
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_one_request import CHAT

MODEL = "gpt-6-test-v"                    # "candidate 1" in these tests
MODEL_2 = "gpt-6-test-v2"                 # "candidate 2": only LLM_MODEL_VERIFY differs
ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
       "LLM_MODEL_VERIFY": MODEL}
PARAGRAPHS = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


def words(case, model=MODEL):
    return f"verify {case} {model}"


@pytest.fixture(autouse=True)
def aimed_at_the_fake_as_openai(as_openai, monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)
    return as_openai


def command(argv, db, *, typed=None, env=None):
    printed, prompts = [], []

    def read_line(prompt):
        prompts.append(prompt)
        if isinstance(typed, BaseException):
            raise typed
        return typed
    code = spike.main(argv, env=env or ENV, spike_db=db, out=printed.append, read_line=read_line)
    return code, "\n".join(printed), prompts


def go(case, db, *, model=MODEL, typed=None):
    """Run one case the way the operator does: --go, then type the words."""
    env = {**ENV, "LLM_MODEL_VERIFY": model}
    return command(["--step", "verify", "--case", case, "--go"], db,
                   typed=words(case, model) if typed is None else typed, env=env)


def rows(db, sql):
    conn = connect(db)
    try:
        return [dict(r) for r in conn.execute(sql)]
    finally:
        conn.close()


def quote_of(paragraph, n=6):
    """The first n words of a paragraph: a quote that is word for word in it."""
    return " ".join(PARAGRAPHS[paragraph].split()[:n])


def cross(paragraph, explanation="A different rule."):
    return {"flag_type": "cross_source", "explanation": explanation,
            "other_paragraph_id": paragraph, "other_quote": quote_of(paragraph)}


def internal(field="offset", row_value="30 calendar days", quote_says="within 20 calendar days"):
    return {"flag_type": "internal", "explanation": "The row disagrees with its quote.",
            "field": field, "row_value": row_value, "quote_says": quote_says}


# --- The cases are plain data -------------------------------------------------------------------

def test_the_four_cases_and_the_rows_they_run_on():
    assert {k: (c.row_id, c.expects) for k, c in spike.CASES.items()} == {
        "C-1": ("SRC-UCILAW-P3", "cross_source"), "C-2": ("SRC-RBELAW-P1", "cross_source"),
        "I-1": ("SRC-UCILAW-P2", "internal"), "OK-1": ("SRC-CSSF15627-P2", "nothing")}
    # Each row is used by ONE case, so a trace unit's name tells which case a line belongs to.
    assert len({c.row_id for c in spike.CASES.values()}) == 4


@pytest.mark.parametrize("case_id", ["C-1", "C-2", "I-1", "OK-1"])
def test_every_case_row_passes_the_codes_own_quote_check(case_id):
    row = spike.case_row(spike.CASES[case_id])
    assert check_quote(row["quote"], row["source_paragraph_id"], PARAGRAPHS).passed


def test_the_injected_row_changes_the_offset_and_nothing_else_and_never_the_answer_key():
    plain = spike._lookup_row("SRC-UCILAW-P2")
    injected = spike.case_row(spike.CASES["I-1"])
    assert plain["offset"] == {"unit": "calendar_days", "amount": 20}
    assert injected["offset"] == {"unit": "calendar_days", "amount": 30}
    assert {k: v for k, v in injected.items() if k != "offset"} == {k: v for k, v in plain.items() if k != "offset"}
    assert injected["quote"] == "within 20 calendar days following the end of each calendar quarter"
    assert spike._lookup_row("SRC-UCILAW-P2")["offset"]["amount"] == 20      # the change was on a copy


# --- The dry-run: what would be sent ------------------------------------------------------------

@pytest.mark.parametrize("case_id,must_say", [
    ("C-1", ["Planted conflict C-1", "SRC-PRACT-P1 disagrees with SRC-UCILAW-P3", "cross-source flag citing SRC-PRACT-P1"]),
    ("C-2", ["Planted conflict C-2", "SRC-PRACT-P2 disagrees with SRC-RBELAW-P1", "cross-source flag citing SRC-PRACT-P2"]),
    ("I-1", ["Planted conflict I-1", "OFFSET CHANGED to 30 calendar days", "its quote still says 20",
             "an internal flag naming the field 'offset'"]),
    ("OK-1", ["No conflict is planted", "A good answer: NO flag"]),
])
def test_the_dry_run_says_which_case_what_row_and_what_a_good_answer_is(
        fake_openai, tmp_path, case_id, must_say):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(["--step", "verify", "--case", case_id], db)
    assert code == 0 and "SPIKE DRY-RUN: nothing was sent" in text
    for expected in (f"Case           : {case_id}", "check_conflicts (Stage B verifier, ONE call)",
                     f"Model          : {MODEL}", "0 of 70 used", *must_say,
                     (f"--step verify --case {case_id} --go. You will be asked to type exactly: "
                      f"{words(case_id)}")):
        assert expected in text, expected
    # Both candidates get the verifier's settings: low, 2000, and NO temperature.
    assert '"reasoning_effort": "low"' in text and '"max_completion_tokens": 2000' in text
    assert '"temperature"' not in text and "Temperature    : NOT sent" in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()
    assert TEST_API_KEY not in text


# --- The typed words name the case AND the model ------------------------------------------------

def test_typing_the_case_and_the_model_sends_one_request_with_the_verifiers_settings(
        fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [cross("SRC-PRACT-P2")]}, tokens_in=1900, tokens_out=300))
    db = tmp_path / "spike.db"
    code, text, prompts = go("C-2", db)
    assert code == 0 and len(prompts) == 1 and words("C-2") in prompts[0]
    assert [r.path for r in fake_openai.requests] == [CHAT] and fake_openai.unscripted == []
    body = fake_openai.requests[0].body
    assert body["model"] == MODEL
    assert body["reasoning_effort"] == "low" and body["max_completion_tokens"] == 2000
    assert "temperature" not in body
    assert body["response_format"] == wire_schema(VerificationResult)
    sent = "\n".join(m["content"] for m in body["messages"])
    assert "SRC-RBELAW-P1" in sent and "SRC-PRACT-P2" in sent
    for pid in PARAGRAPHS:                                     # EVERY loaded paragraph, as Stage B does
        assert pid in sent
    for expected in ("Case           : C-2 (SRC-RBELAW-P1)", "Unit           : SRC-RBELAW-P1#1",
                     "Planted C-2   : CAUGHT (a cross-source flag cites SRC-PRACT-P2)",
                     "False alarms     : none", "Path         : /v1/chat/completions"):
        assert expected in text, expected
    (line,) = rows(db, "SELECT * FROM trace")
    assert (line["step"], line["unit_id"], line["model"]) == ("check_conflicts", "SRC-RBELAW-P1#1", MODEL)


@pytest.mark.parametrize("typed", [
    "", "verify C-2", "verify SRC-RBELAW-P1", "C-2 " + MODEL, "verify c-2 " + MODEL,
    f"verify C-2  {MODEL} x", "verify C-2 gpt-6.1-terra",          # the wrong model
    words("C-1"), words("I-1"), words("OK-1"),                      # another case's words
    "judge SRC-UCILAW-P3", "verify SRC-UCILAW-P3",
])
def test_anything_but_the_exact_case_and_model_cancels(fake_openai, tmp_path, typed):
    db = tmp_path / "data" / "spike.db"
    code, text, _ = go("C-2", db, typed=typed)
    assert code == 2 and "NOT CONFIRMED: nothing was sent." in text
    assert fake_openai.requests == [] and not db.exists()


@pytest.mark.parametrize("closed", [EOFError(), OSError("no terminal")])
def test_nobody_to_ask_counts_as_not_confirmed(fake_openai, tmp_path, closed):
    code, text, _ = go("C-2", tmp_path / "spike.db", typed=closed)
    assert code == 2 and "NOT CONFIRMED" in text and fake_openai.requests == []


def test_a_forgotten_model_override_is_caught_by_the_typed_words(fake_openai, tmp_path):
    """The operator means candidate 2 but forgot LLM_MODEL_VERIFY on the command line: the plan shows
    candidate 1's model, the operator types candidate 2's, and nothing is sent."""
    code, text, _ = command(["--step", "verify", "--case", "I-1", "--go"], tmp_path / "spike.db",
                            typed=words("I-1", MODEL_2))                # env still names MODEL
    assert code == 2 and f"Model          : {MODEL}" in text and "NOT CONFIRMED" in text
    assert fake_openai.requests == []


def test_candidate_2_is_the_same_command_with_another_model_and_nothing_else_changes(
        fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [cross("SRC-PRACT-P2")]}), Reply({"flags": [cross("SRC-PRACT-P2")]}))
    db = tmp_path / "spike.db"
    assert go("C-2", db, model=MODEL)[0] == 0
    assert go("C-2", db, model=MODEL_2)[0] == 0
    first, second = (r.body for r in fake_openai.requests)
    assert (first["model"], second["model"]) == (MODEL, MODEL_2)
    for key in ("reasoning_effort", "max_completion_tokens", "response_format", "messages"):
        assert first[key] == second[key], key                     # the same settings, schema and prompt
    assert "temperature" not in first and "temperature" not in second
    lines = rows(db, "SELECT unit_id, model, settings_json, cost_usd, tokens_in, tokens_out FROM trace ORDER BY trace_id")
    assert [(r["unit_id"], r["model"]) for r in lines] == [("SRC-RBELAW-P1#1", MODEL), ("SRC-RBELAW-P1#2", MODEL_2)]
    assert lines[0]["settings_json"] == lines[1]["settings_json"]
    # Priced at the VERIFIER's prices whichever model ran: the tally re-prices the other candidate.
    for r in lines:
        assert r["cost_usd"] == pytest.approx(model_settings.call_cost_usd("verify", r["tokens_in"], r["tokens_out"]))


# --- What each case's request carries -----------------------------------------------------------

def test_the_injected_case_sends_the_changed_offset_and_the_unchanged_quote(fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": [internal()]}))
    go("I-1", tmp_path / "spike.db")
    sent = "\n".join(m["content"] for m in fake_openai.requests[0].body["messages"])
    assert '"amount": 30' in sent and "calendar_days" in sent
    assert "within 20 calendar days following the end of each calendar quarter" in sent
    assert "passed" in sent                                       # the code's quote check passes it


def test_the_clean_case_sends_a_row_that_its_other_source_agrees_with(fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": []}))
    go("OK-1", tmp_path / "spike.db")
    sent = "\n".join(m["content"] for m in fake_openai.requests[0].body["messages"])
    assert "SRC-CSSF15627-P2" in sent and "SRC-PRACT-P3" in sent and '"amount": 10' in sent


# --- What the result says, per case -------------------------------------------------------------

@pytest.mark.parametrize("case_id,flags,must_say,must_not_say", [
    ("C-2", [cross("SRC-PRACT-P2")], ["Planted C-2   : CAUGHT (a cross-source flag cites SRC-PRACT-P2)", "False alarms     : none"], ["MISSED"]),
    ("C-2", [], ["Planted C-2   : MISSED (no cross-source flag cites SRC-PRACT-P2)", "DL-26"], ["CAUGHT"]),
    ("C-2", [cross("SRC-PRACT-P1")], ["Planted C-2   : MISSED", "Other flags      : cross-source on SRC-PRACT-P1 (not the planted conflict: read it)"], ["CAUGHT"]),
    ("C-2", [cross("SRC-PRACT-P2"), internal("anchor", "event_awareness", "within one month")],
     ["CAUGHT", "False alarms     : 1 internal flag(s) on a row whose fields match its quote"], []),
    ("I-1", [internal()], ["Planted I-1   : CAUGHT (an internal flag names the field 'offset')", "False alarms     : none"], ["MISSED"]),
    ("I-1", [], ["Planted I-1   : MISSED (no internal flag names the field 'offset')", "DL-26"], ["CAUGHT"]),
    ("I-1", [internal("frequency", "monthly", "each calendar quarter")],
     ["Planted I-1   : MISSED", "False alarms     : 1 internal flag(s) on a field that matches its quote: frequency"], ["CAUGHT"]),
    ("I-1", [cross("SRC-PRACT-P2")], ["Planted I-1   : MISSED", "Other flags      : cross-source on SRC-PRACT-P2 (not the injected conflict: read it)"], ["CAUGHT"]),
    ("OK-1", [], ["Correct row      : CLEAN (no flag)"], ["FALSE ALARM", "DL-26"]),
    ("OK-1", [cross("SRC-PRACT-P3")], ["Correct row      : FALSE ALARM (1 flag(s) on a row the answer key says needs none)"], ["CLEAN"]),
    ("OK-1", [internal("offset", "10 days", "no later than 10 calendar days")], ["Correct row      : FALSE ALARM (1 flag(s)"], ["CLEAN"]),
])
def test_the_result_says_caught_or_missed_and_clean_or_false_alarm(
        fake_openai, tmp_path, case_id, flags, must_say, must_not_say):
    fake_openai.script(Reply({"flags": flags}))
    code, text, _ = go(case_id, tmp_path / "spike.db")
    assert code == 0                                     # a usable answer, whatever it says: a miss is a finding
    assert f"Answer         : VALID ({len(flags)} flag(s) passed the guardrail)" in text
    for expected in must_say:
        assert expected in text, expected
    for unexpected in must_not_say:
        assert unexpected not in text, unexpected


def test_assess_case_agrees_with_the_first_steps_assess_verification_for_c_1():
    flags = [Flag.model_validate(f) for f in agents._stand_in("verifier")["SRC-UCILAW-P3"]]
    flags.append(Flag.model_validate(internal("anchor", "x", "within six months")))
    assert spike.assess_verification("SRC-UCILAW-P3", flags) == spike.assess_case(spike.CASES["C-1"], flags)


# --- When it goes wrong: said plainly, nothing repeated -----------------------------------------

def test_an_answer_that_does_not_fit_the_schema_stops_the_case_and_is_not_asked_for_again(
        fake_openai, tmp_path):
    mixed = cross("SRC-PRACT-P2") | {"field": "offset", "row_value": "1 month"}   # the first real call's mistake
    fake_openai.script(Reply({"flags": [mixed]}))
    code, text, _ = go("C-2", tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE - invalid output" in text and "Stopped. Nothing was repeated" in text
    assert len(fake_openai.requests) == 1 and fake_openai.unscripted == []


def test_two_failed_requests_are_reported_and_both_are_billed(fake_openai, tmp_path):
    fake_openai.script(Failure(503, "Overloaded"), Failure(503, "Overloaded"))
    code, text, _ = go("I-1", tmp_path / "spike.db")
    assert code == 1 and "NOT USABLE - model service" in text and "ESTIMATED" in text
    assert len(fake_openai.requests) == 2


# --- Counting, units and the one shared run -----------------------------------------------------

def test_cases_and_both_candidates_share_one_run_and_one_count_and_number_their_own_units(
        fake_openai, tmp_path):
    db = tmp_path / "spike.db"
    c1 = agents._stand_in("verifier")["SRC-UCILAW-P3"]
    fake_openai.script(Reply({"flags": c1}), Reply({"flags": c1}), Reply({"flags": [cross("SRC-PRACT-P2")]}),
                       Reply({"flags": [cross("SRC-PRACT-P2")]}), Reply({"flags": [internal()]}),
                       Reply({"flags": []}))
    legacy = command(["--step", "verify", "--go"], db, typed="verify SRC-UCILAW-P3")   # the first step's path
    assert legacy[0] == 0
    assert go("C-1", db)[0] == 0
    assert go("C-2", db)[0] == 0
    assert go("C-2", db, model=MODEL_2)[0] == 0
    assert go("I-1", db)[0] == 0
    assert go("OK-1", db)[0] == 0
    units = [(r["unit_id"], r["model"]) for r in rows(db, "SELECT unit_id, model FROM trace ORDER BY trace_id")]
    assert units == [("SRC-UCILAW-P3#1", MODEL), ("SRC-UCILAW-P3#2", MODEL),     # --row, then --case C-1
                     ("SRC-RBELAW-P1#1", MODEL), ("SRC-RBELAW-P1#2", MODEL_2),
                     ("SRC-UCILAW-P2#1", MODEL), ("SRC-CSSF15627-P2#1", MODEL)]
    assert len(rows(db, "SELECT * FROM runs")) == 1
    conn = connect(db)
    try:
        assert harness.real_calls_made(conn, "spike") == 6
    finally:
        conn.close()
    _, text, _ = command(["--step", "verify", "--case", "OK-1"], db)
    assert "6 of 70 used" in text


# --- Refusals come before the prompt ------------------------------------------------------------

@pytest.mark.parametrize("env,argv,reason", [
    ({**ENV, "AGENTS_MODE": "stand_in"}, ["--step", "verify", "--case", "C-2", "--go"], "AGENTS_MODE"),
    ({**ENV, "SPEND_ACTIVITY": "tuning"}, ["--step", "verify", "--case", "C-2", "--go"], "SPEND_ACTIVITY"),
    ({**ENV, "OPENAI_API_KEY": ""}, ["--step", "verify", "--case", "C-2", "--go"], "OPENAI_API_KEY"),
    ({**ENV, "LLM_MODEL_VERIFY": ""}, ["--step", "verify", "--case", "I-1", "--go"], "LLM_MODEL_VERIFY"),
    (ENV, ["--step", "judge", "--case", "C-2", "--go"], "--case is only for --step verify"),
    (ENV, ["--case", "C-2", "--go"], "--case is only for --step verify"),
    (ENV, ["--step", "verify", "--case", "C-2", "--row", "SRC-RBELAW-P1", "--go"], "not both"),
    # The first step's --row path still allows only C-1.
    (ENV, ["--step", "verify", "--row", "SRC-RBELAW-P1", "--go"], "not a row this step plans"),
    (ENV, ["--step", "verify", "--row", "SRC-UCILAW-P2", "--go"], "not a row this step plans"),
])
def test_a_refusal_comes_before_the_prompt(fake_openai, tmp_path, env, argv, reason):
    db = tmp_path / "data" / "spike.db"
    code, text, prompts = command(argv, db, typed="anything", env=env)
    assert code == 2 and text.startswith("REFUSED:") and reason in text
    assert prompts == [] and fake_openai.requests == [] and not db.exists()


def test_an_unknown_case_is_refused_by_the_command_line_itself(fake_openai, tmp_path):
    with pytest.raises(SystemExit):
        command(["--step", "verify", "--case", "C-9", "--go"], tmp_path / "spike.db")
    assert fake_openai.requests == []


def test_the_70_call_cap_refuses_a_case_before_any_request(fake_openai, tmp_path):
    db = tmp_path / "spike.db"
    run_id = spike.open_spike_run(spike.load_settings(ENV), db)
    conn = connect(db)
    for n in range(70):
        conn.execute(
            "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
            "prompt_version, input_hash, spend_activity) "
            "VALUES (?, 'FND-DEMO-01', 'check_conflicts', 1, ?, 1, 'now', 'v', 'h', 'spike')",
            (run_id, f"X{n}"))
    conn.commit()
    conn.close()
    code, text, prompts = go("C-2", db)
    assert code == 2 and "70 of 70" in text and prompts == [] and fake_openai.requests == []


def test_the_first_steps_row_path_still_works_unchanged(fake_openai, tmp_path):
    fake_openai.script(Reply({"flags": agents._stand_in("verifier")["SRC-UCILAW-P3"]}))
    code, text, _ = command(["--step", "verify", "--go"], tmp_path / "spike.db",
                            typed="verify SRC-UCILAW-P3")
    assert code == 0 and "Planted C-1   : CAUGHT" in text and "Case           :" not in text
    assert "SRC-PRACT-P1" in json.dumps(fake_openai.requests[0].body["messages"])
