"""T-SPIKE-8 (Tier 1): the spike's READ-ONLY tally, `--tally` (B3 spike PR 4, PR 2).
Fake OpenAI only: no real key, no real model, no paid call. The tally sends nothing at all.

What the tally promises, and what these tests pin down:
  * It is READ-ONLY. The database file is byte-for-byte the same afterwards, no side file appears, a
    missing database is not created, and it needs no key, no real mode and no network.
  * It counts what happened: slots (one per request), calls (units), and the kinds of line, including a
    line that was not a model call (the first call's pre-flight).
  * It decides CAUGHT / MISSED / CLEAN / FALSE ALARM with the SAME code as the live printout.
  * A MISS is only counted on a valid answer: an invalid answer or a failed call is not a miss.
  * It re-prices the judge's model, run as a verifier, at the judge's prices, and leaves an estimate, a
    failed request and an unknown model as recorded.
  * It decides nothing: DL-26 is printed as information, and the operator decides.
"""

import hashlib
import json
import socket
import subprocess
import sys

import pytest

from backend.db.connection import connect
from backend.domain.schemas import Flag
from backend.runtime import crews, harness, model_settings, spike, spike_tally
from backend.settings import ROOT, load_settings
from tests.fake_openai import TEST_API_KEY, Reply
from tests.tier1.test_spike_cases import cross, internal

MODELS = {"extract": "m-ext", "verify": "m-ver", "judge": "m-jdg"}      # the roles' models in .env
ENV = {"LLM_MODEL_EXTRACT": MODELS["extract"], "LLM_MODEL_VERIFY": MODELS["verify"],
       "LLM_MODEL_JUDGE": MODELS["judge"]}                              # a tally needs no key, no real mode
RUN_ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY, **ENV}
ROLE_OF = {"extract_rows": "extract", "check_conflicts": "verify", "judge_applicability": "judge"}
ROW = {"C-1": "SRC-UCILAW-P3", "C-2": "SRC-RBELAW-P1", "I-1": "SRC-UCILAW-P2", "OK-1": "SRC-CSSF15627-P2"}
GOOD_JUDGE = {"verdict": "applies", "cited_fact_ids": ["FACT-01"], "reasoning": "r", "missing_information": ""}


class Db:
    """A spike database with lines we choose, so every number the tally prints is a number we chose."""

    def __init__(self, tmp_path):
        self.path = tmp_path / "data" / "spike.db"
        self.run_id = spike.open_spike_run(load_settings(RUN_ENV), self.path)
        self.n = 0

    def add(self, step, unit, attempt, model, *, raw=None, tin=0, tout=0, cost=None, invalid=None,
            error=None, estimated=0, ms=4000):
        """One trace line. `cost` defaults to what the runner records: the STEP's role's prices."""
        if cost is None:
            cost = 0.0 if error or estimated else model_settings.call_cost_usd(ROLE_OF[step], tin, tout)
        conn = connect(self.path)
        conn.execute(
            "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
            "prompt_version, model, input_hash, raw_output, validation_error, tokens_in, tokens_out, "
            "cost_usd, duration_ms, spend_activity, stop_reason, provider_error, cost_estimated, "
            "request_path) VALUES (?, 'FND-DEMO-01', ?, 1, ?, ?, 'now', 'v', ?, 'h', ?, ?, ?, ?, ?, ?, "
            "'spike', 'stop', ?, ?, '/v1/chat/completions')",
            (self.run_id, step, unit, attempt, model, raw, invalid, tin, tout, cost, ms, error, estimated))
        conn.commit()
        conn.close()

    def verify(self, case, n, model, flags, *, tin=1000, tout=300, **kw):
        self.add("check_conflicts", f"{ROW[case]}#{n}", 1, model,
                 raw=json.dumps({"flags": flags}), tin=tin, tout=tout, **kw)

    def judge(self, n, answer, model=MODELS["judge"]):
        self.add("judge_applicability", f"SRC-UCILAW-P3#{n}", 1, model, raw=json.dumps(answer), tin=1000, tout=100)

    def tally(self, exclude=()):
        return spike_tally.collect(self.path, MODELS, set(exclude))

    def digest(self):
        return hashlib.sha256(self.path.read_bytes()).hexdigest()


@pytest.fixture
def db(tmp_path):
    return Db(tmp_path)


def run_tally(db_path, argv=(), env=None):
    printed = []
    code = spike.main(["--tally", *argv], env=ENV if env is None else env, spike_db=db_path, out=printed.append)
    return code, "\n".join(printed)


def verifier_rows(tally, model):
    """{case: grouped counts} for one model's counted verifier units."""
    units = [u for u in tally.units if u.step == "check_conflicts" and u.model == model and not u.excluded]
    return {case: spike_tally._group([u for u in units if u.case_id == case])
            for case in [*spike.CASES, ""] if any(u.case_id == case for u in units)}


# --- Read-only ----------------------------------------------------------------------------------

def test_the_tally_leaves_the_database_byte_for_byte_the_same_and_adds_no_file(db):
    db.verify("C-2", 1, MODELS["verify"], [cross("SRC-PRACT-P2")])
    before, listing = db.digest(), sorted(p.name for p in db.path.parent.iterdir())
    mtime = db.path.stat().st_mtime_ns
    code, text = run_tally(db.path)
    assert code == 0 and "SPIKE TALLY (read-only" in text
    assert db.digest() == before and db.path.stat().st_mtime_ns == mtime
    assert sorted(p.name for p in db.path.parent.iterdir()) == listing      # no -journal, no -wal


def test_our_code_opens_every_database_read_only(db, monkeypatch):
    """Watch how the tally itself opens files: the guarantee is the connection mode, so a change that
    opened ANY file for writing would fail here even if no write happened to be made. (It opens each
    database more than once: to count the real calls, and to read the lines.)"""
    import sqlite3
    db.judge(1, GOOD_JUDGE)                      # set up first: this helper opens its own (writing) connection
    opened = []
    real_connect = sqlite3.connect

    def spy(*args, **kwargs):
        opened.append((args, kwargs))
        return real_connect(*args, **kwargs)
    monkeypatch.setattr(spike_tally.sqlite3, "connect", spy)
    monkeypatch.setattr(harness.sqlite3, "connect", spy)
    run_tally(db.path)                           # from here on, only the tally opens anything
    assert opened, "the tally opened nothing?"
    for (uri,), kwargs in opened:
        assert uri.startswith("file:") and uri.endswith("?mode=ro") and kwargs.get("uri") is True, uri
    # ...and what that mode means, shown directly: a write through such a connection is refused.
    conn = real_connect(uri, uri=True)
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        conn.execute("DELETE FROM runs")
    conn.close()


def test_a_missing_database_is_reported_and_not_created(tmp_path):
    missing = tmp_path / "data" / "spike.db"
    code, text = run_tally(missing)
    assert code == 0 and "there is no spike database yet" in text and "nothing has been sent" in text
    assert not missing.exists() and not missing.parent.exists()


def test_it_needs_no_key_no_real_mode_and_no_network(db, fake_openai, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the tally tried to open a network connection")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", refuse)
    db.judge(1, GOOD_JUDGE)
    code, text = run_tally(db.path, env={})                # no key, no model IDs, stand-in mode
    assert code == 0 and "JUDGE" in text and fake_openai.requests == []
    assert TEST_API_KEY not in text


def test_importing_the_tally_loads_no_model_code():
    code = ("import sys, backend.runtime.spike_tally; "
            "bad = [m for m in sys.modules if m == 'crewai' or m.startswith('crewai.') "
            "or m in ('backend.runtime.crews', 'backend.runtime.agents', 'backend.services.runs')]; "
            "print(bad); sys.exit(1 if bad else 0)")
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=False)
    assert done.returncode == 0, done.stdout + done.stderr


@pytest.mark.parametrize("argv,reason", [(["--go"], "cannot be combined with --go"),
                                         ])
def test_it_cannot_be_combined_with_sending(db, argv, reason):
    printed = []
    code = spike.main(["--tally", *argv], env=ENV, spike_db=db.path, out=printed.append)
    assert code == 2 and reason in "\n".join(printed)


def test_exclude_without_tally_is_refused(db):
    printed = []
    code = spike.main(["--exclude", "SRC-UCILAW-P3#1"], env=ENV, spike_db=db.path, out=printed.append)
    assert code == 2 and "--exclude is only for --tally" in "\n".join(printed)


# --- Counting -----------------------------------------------------------------------------------

def test_slots_calls_and_the_kinds_of_line(db):
    # The first call's shape: a pre-flight line (not a model call), then the model's answer.
    db.add("extract_rows", "SRC-UCILAW#1", 1, MODELS["extract"], cost=0.0011, estimated=1, ms=1500)
    db.add("extract_rows", "SRC-UCILAW#1", 2, MODELS["extract"], raw=json.dumps({"rows": []}), tin=1500, tout=360, ms=4400)
    db.verify("C-2", 1, MODELS["verify"], [cross("SRC-PRACT-P2")])
    db.add("check_conflicts", "SRC-RBELAW-P1#2", 1, MODELS["verify"], error="HTTP 503", estimated=1, cost=0.02)
    db.add("check_conflicts", "SRC-RBELAW-P1#3", 1, MODELS["verify"],
           error="refused before sending: GET /v1/x is not a chat completion")
    t = db.tally()
    conn = connect(db.path)
    try:
        assert t.slots_used == harness.real_calls_made(conn, "spike") == 5
    finally:
        conn.close()
    assert t.line_kinds == {"not a model call": 1, "model answer": 2, "no answer": 1, "refused (never sent)": 1}
    assert len(t.units) == 4
    first = next(u for u in t.units if u.unit_id == "SRC-UCILAW#1")
    assert (first.lines, first.status) == (2, "valid") and first.seconds == pytest.approx(5.9)   # 1.5 + 4.4
    text = run_tally(db.path)[1]
    assert "Slots used     : 5 of 70 (65 left)" in text and "Calls          : 4" in text


def test_the_last_line_decides_what_a_call_was(db):
    db.add("check_conflicts", "SRC-RBELAW-P1#1", 1, MODELS["verify"], error="HTTP 503", estimated=1, cost=0.02)
    db.add("check_conflicts", "SRC-RBELAW-P1#1", 2, MODELS["verify"],
           raw=json.dumps({"flags": [cross("SRC-PRACT-P2")]}), tin=1000, tout=300)            # the retry answered
    db.add("check_conflicts", "SRC-RBELAW-P1#2", 1, MODELS["verify"], error="HTTP 503", estimated=1, cost=0.02)
    db.add("check_conflicts", "SRC-RBELAW-P1#2", 2, MODELS["verify"], error="HTTP 503", estimated=1, cost=0.02)
    db.add("check_conflicts", "SRC-RBELAW-P1#3", 1, MODELS["verify"], raw=json.dumps({"flags": [{"bad": 1}]}),
           tin=1000, tout=300, invalid="Output does not fit the verifier's schema")
    statuses = {u.unit_id: u.status for u in db.tally().units}
    assert statuses == {"SRC-RBELAW-P1#1": "valid", "SRC-RBELAW-P1#2": "no_answer", "SRC-RBELAW-P1#3": "invalid"}


# --- What each case came to ---------------------------------------------------------------------

def test_caught_missed_clean_and_false_alarm_per_case(db):
    m = MODELS["verify"]
    db.verify("C-2", 1, m, [cross("SRC-PRACT-P2")])                                  # caught
    db.verify("C-2", 2, m, [cross("SRC-PRACT-P2"), internal("anchor", "x", "within one month")])   # caught + false alarm
    db.verify("C-2", 3, m, [])                                                       # MISSED
    db.verify("C-2", 4, m, [cross("SRC-PRACT-P1")])                                  # MISSED (wrong paragraph)
    db.verify("I-1", 1, m, [internal()])                                             # caught
    db.verify("I-1", 2, m, [internal("frequency", "monthly", "each calendar quarter")])   # MISSED + false alarm
    db.verify("I-1", 3, m, [cross("SRC-PRACT-P2")])                                  # MISSED
    db.verify("OK-1", 1, m, [])                                                      # clean
    db.verify("OK-1", 2, m, [cross("SRC-PRACT-P3")])                                 # false alarm
    db.verify("OK-1", 3, m, [internal("offset", "10 days", "no later than 10 calendar days")])   # false alarm
    rows = verifier_rows(db.tally(), m)
    assert (rows["C-2"]["valid"], rows["C-2"]["good"], rows["C-2"]["bad"], rows["C-2"]["false_alarm"]) == (4, 2, 2, 1)
    assert (rows["I-1"]["valid"], rows["I-1"]["good"], rows["I-1"]["bad"], rows["I-1"]["false_alarm"]) == (3, 1, 2, 1)
    assert (rows["OK-1"]["valid"], rows["OK-1"]["good"], rows["OK-1"]["bad"]) == (3, 1, 2)


def test_an_invalid_answer_or_a_failed_call_is_never_counted_as_a_miss(db):
    m = MODELS["verify"]
    db.verify("C-1", 1, m, [cross("SRC-PRACT-P1") | {"field": "offset", "row_value": "6 months"}],
              invalid="Output does not fit the verifier's schema")                   # the first real call
    db.verify("C-1", 2, m, [cross("SRC-PRACT-P1")])
    db.add("check_conflicts", "SRC-UCILAW-P3#3", 1, m, error="HTTP 503", estimated=1, cost=0.02)
    row = verifier_rows(db.tally(), m)["C-1"]
    assert (row["calls"], row["valid"], row["invalid"], row["no_answer"]) == (3, 1, 1, 1)
    assert (row["good"], row["bad"]) == (1, 0)                                       # no miss anywhere
    assert "0 MISSED in 1 valid planted run(s)" in run_tally(db.path)[1]


def test_models_are_counted_apart(db):
    db.verify("C-2", 1, MODELS["verify"], [cross("SRC-PRACT-P2")])
    db.verify("C-2", 2, MODELS["judge"], [])                                         # candidate 2 misses
    t = db.tally()
    assert verifier_rows(t, MODELS["verify"])["C-2"]["good"] == 1
    assert verifier_rows(t, MODELS["judge"])["C-2"]["bad"] == 1
    text = run_tally(db.path)[1]
    assert f"model {MODELS['verify']} (the verify model in .env)" in text
    assert f"model {MODELS['judge']} (the judge model in .env)" in text


def test_the_judge_and_the_extractor(db):
    db.judge(1, GOOD_JUDGE)
    db.judge(2, GOOD_JUDGE | {"verdict": "unsure", "missing_information": "x"})
    db.add("extract_rows", "SRC-UCILAW#1", 1, MODELS["extract"],
           raw=json.dumps({"rows": json.loads(json.dumps(_two_rows()))}), tin=1500, tout=360)
    t = db.tally()
    judges = [u for u in t.units if u.step == "judge_applicability"]
    assert [u.good for u in judges] == [True, False]
    assert next(u for u in t.units if u.step == "extract_rows").rows == 2
    text = run_tally(db.path)[1]
    assert "CORRECT 1, WRONG 1" in text and "rows per valid answer (mean) 2.0" in text


def _two_rows():
    return [spike._lookup_row("SRC-UCILAW-P3"), spike._lookup_row("SRC-CSSF15627-P2")]


def test_an_answer_that_can_no_longer_be_read_is_counted_apart_and_not_judged(db):
    db.add("check_conflicts", "SRC-RBELAW-P1#1", 1, MODELS["verify"], raw="not json at all", tin=1000, tout=300)
    row = verifier_rows(db.tally(), MODELS["verify"])["C-2"]
    assert (row["valid"], row["unreadable"], row["good"], row["bad"]) == (1, 1, 0, 0)
    assert "could not be read back as flags" in run_tally(db.path)[1]


def test_a_verifier_unit_on_an_unplanned_row_is_listed_as_other(db):
    db.add("check_conflicts", "SRC-NOPE-P9#1", 1, MODELS["verify"], raw=json.dumps({"flags": []}), tin=1000, tout=300)
    assert "" in verifier_rows(db.tally(), MODELS["verify"])           # no case: the row is not planned
    assert "\n    other " in run_tally(db.path)[1]                     # ...and the table says so


# --- Re-pricing ---------------------------------------------------------------------------------

def test_the_judges_model_run_as_a_verifier_is_re_priced_at_the_judges_prices(db):
    db.verify("C-2", 1, MODELS["verify"], [cross("SRC-PRACT-P2")], tin=1000, tout=400)
    db.verify("C-2", 2, MODELS["judge"], [cross("SRC-PRACT-P2")], tin=1000, tout=400)   # recorded at VERIFY prices
    t = db.tally()
    one, two = (next(u for u in t.units if u.model == m) for m in (MODELS["verify"], MODELS["judge"]))
    verify_cost = (1000 * 2.00 + 400 * 12.00) / 1e6        # 0.0068
    judge_cost = (1000 * 1.00 + 400 * 5.00) / 1e6          # 0.0030
    assert one.recorded == pytest.approx(verify_cost) and one.repriced == pytest.approx(verify_cost)
    assert one.priced_as == "verify"
    assert two.recorded == pytest.approx(verify_cost)      # what the trace says: too high
    assert two.repriced == pytest.approx(judge_cost) and two.priced_as == "judge"
    assert t.recorded_total == pytest.approx(2 * verify_cost)
    assert t.repriced_total == pytest.approx(verify_cost + judge_cost)
    text = run_tally(db.path)[1]
    assert "US$0.0136 recorded; US$0.0098 when each line is priced for the model that ran" in text


def test_an_estimate_a_failed_request_and_an_unknown_model_are_left_as_recorded(db):
    db.add("check_conflicts", "SRC-RBELAW-P1#1", 1, MODELS["judge"], raw=json.dumps({"flags": []}),
           tin=0, tout=0, estimated=1, cost=0.0111)                                 # no usage data: an estimate
    db.add("check_conflicts", "SRC-RBELAW-P1#2", 1, MODELS["judge"], error="HTTP 503", estimated=1, cost=0.0222)
    db.verify("C-2", 3, "some-other-model", [], tin=1000, tout=400)                  # matches no role in .env
    t = db.tally()
    by_id = {u.unit_id: u for u in t.units}
    assert by_id["SRC-RBELAW-P1#1"].repriced == pytest.approx(0.0111) and by_id["SRC-RBELAW-P1#1"].priced_as == ""
    assert by_id["SRC-RBELAW-P1#2"].repriced == pytest.approx(0.0222)
    unknown = by_id["SRC-RBELAW-P1#3"]
    assert unknown.repriced == unknown.recorded and unknown.priced_as == ""
    assert t.repriced_total == pytest.approx(t.recorded_total)


@pytest.mark.parametrize("model,step_role,expected", [
    ("m-ver", "verify", "verify"), ("m-jdg", "verify", "judge"), ("m-jdg", "judge", "judge"),
    ("m-ext", "verify", "extract"), ("nothing", "verify", ""), ("", "verify", ""),
])
def test_which_role_s_prices_apply(model, step_role, expected):
    assert spike_tally.priced_as(model, step_role, MODELS) == expected


def test_when_one_model_serves_two_roles_the_steps_own_role_wins():
    same = {"extract": "m", "verify": "m", "judge": "m"}
    assert spike_tally.priced_as("m", "verify", same) == "verify"
    assert spike_tally.priced_as("m", "judge", same) == "judge"


# --- Excluding a call sent before a fix ---------------------------------------------------------

def test_exclude_removes_a_verifier_unit_from_the_counts_and_lists_it(db):
    m = MODELS["verify"]
    db.verify("C-1", 1, m, [cross("SRC-PRACT-P1") | {"field": "offset", "row_value": "6 months"}],
              invalid="Output does not fit the verifier's schema")
    db.verify("C-1", 2, m, [cross("SRC-PRACT-P1")])
    db.judge(1, GOOD_JUDGE)                                                          # also named SRC-UCILAW-P3#1
    t = db.tally(exclude={"SRC-UCILAW-P3#1"})
    assert verifier_rows(t, m)["C-1"]["calls"] == 1
    assert next(u for u in t.units if u.step == "judge_applicability").excluded is False   # the judge is untouched
    code, text = run_tally(db.path, ["--exclude", "SRC-UCILAW-P3#1"])
    assert code == 0 and f"Excluded by --exclude (not in the counts above): SRC-UCILAW-P3#1 ({m}, invalid)" in text
    assert "CORRECT 1" in text                                                       # the judge's call still counted


# --- What it says about DL-26: information, never a decision ------------------------------------

def test_dl_26_is_read_out_and_never_decided(db):
    m = MODELS["verify"]
    db.verify("C-2", 1, m, [cross("SRC-PRACT-P2")])
    text = run_tally(db.path)[1]
    assert "DL-26 reading (information, not a decision): 0 MISSED in 1 valid planted run(s)" in text
    assert "C-2 4 more" in text and "C-1 5 more" in text and "OK-1 5 more" in text
    assert "switches" not in text                              # no miss, so nothing is said about switching
    db.verify("C-2", 2, m, [])
    text = run_tally(db.path)[1]
    assert "1 MISSED in 2 valid planted run(s)" in text
    assert "by DL-26 the verifier switches to the judge's model, if the operator decides so" in text


def test_five_valid_runs_of_a_case_leave_no_runs_needed_for_it(db):
    for n in range(1, 6):
        db.verify("C-2", n, MODELS["verify"], [cross("SRC-PRACT-P2")])
    text = run_tally(db.path)[1]
    assert "C-2 " not in text.split("valid runs still needed for 5 of each case:")[1].splitlines()[0]
    assert "5/5" in text


def test_the_cost_of_a_full_run_is_the_mean_valid_call_times_seven(db):
    db.verify("C-2", 1, MODELS["verify"], [], tin=1000, tout=100)     # (1000*2 + 100*12) / 1e6 = 0.0032
    db.verify("C-2", 2, MODELS["verify"], [], tin=1000, tout=300)     # (1000*2 + 300*12) / 1e6 = 0.0056
    text = run_tally(db.path)[1]
    assert f"about {spike_tally._money(0.0044 * 7)} for this model (mean valid call US$0.0044)" in text


# --- The tally agrees with the live printout ----------------------------------------------------

@pytest.mark.parametrize("case_id,flags", [
    ("C-1", []), ("C-1", [cross("SRC-PRACT-P1")]), ("C-2", [cross("SRC-PRACT-P1")]), ("C-2", [cross("SRC-PRACT-P2")]),
    ("I-1", []), ("I-1", [internal()]), ("I-1", [internal("anchor", "x", "within 20 calendar days")]),
    ("OK-1", []), ("OK-1", [cross("SRC-PRACT-P3")]),
])
def test_the_one_decision_is_shared_by_the_live_printout_and_the_tally(case_id, flags):
    case = spike.CASES[case_id]
    flag_objects = [Flag.model_validate(f) for f in flags]
    outcome = spike.classify_case(case, flag_objects)
    text = "\n".join(spike.assess_case(case, flag_objects))
    assert ("CAUGHT" in text or "CLEAN" in text) is outcome.good
    assert ("MISSED" in text or "FALSE ALARM" in text) is (not outcome.good)


def test_a_settings_problem_does_not_stop_a_read_only_summary(db):
    db.judge(1, GOOD_JUDGE)
    code, text = run_tally(db.path, env={"AGENTS_MODE": "real"})      # real mode with no SPEND_ACTIVITY: settings refuse
    assert code == 0 and "the role models in .env could not be read" in text and "JUDGE" in text


# --- End to end: what the real runner writes, the tally reads -----------------------------------

def test_the_tally_reads_what_the_runner_actually_wrote(db, fake_openai, as_openai, monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)
    env = {**RUN_ENV, "LLM_MODEL_VERIFY": "gpt-6-test-v"}                 # names CrewAI recognises
    env2 = {**RUN_ENV, "LLM_MODEL_VERIFY": "gpt-6-test-j", "LLM_MODEL_JUDGE": "gpt-6-test-j"}
    fake_openai.script(Reply({"flags": [cross("SRC-PRACT-P2")]}, tokens_in=1000, tokens_out=400),
                       Reply({"flags": [cross("SRC-PRACT-P2")]}, tokens_in=1000, tokens_out=400),
                       Reply({"flags": []}, tokens_in=1000, tokens_out=50))
    path = db.path.parent / "e2e.db"

    def go(case, environment, model):
        spike.main(["--step", "verify", "--case", case, "--go"], env=environment, spike_db=path,
                   out=lambda _: None, read_line=lambda prompt: f"verify {case} {model}")
    go("C-2", env, "gpt-6-test-v")
    go("C-2", env2, "gpt-6-test-j")
    go("OK-1", env, "gpt-6-test-v")
    role_models = {"extract": "", "verify": "gpt-6-test-v", "judge": "gpt-6-test-j"}
    t = spike_tally.collect(path, role_models)
    conn = connect(path)
    try:
        assert t.slots_used == harness.real_calls_made(conn, "spike") == 3
    finally:
        conn.close()
    one, two, ok = t.units
    assert (one.case_id, one.good, one.priced_as) == ("C-2", True, "verify")
    assert (two.case_id, two.good, two.priced_as) == ("C-2", True, "judge")     # the other candidate, re-priced
    assert two.repriced < two.recorded
    assert (ok.case_id, ok.good) == ("OK-1", True)
    assert t.repriced_total < t.recorded_total
