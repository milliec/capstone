"""B3 step 7b, PR 5, step 3: ONE TRACE LINE PER HTTP REQUEST, and a failed attempt's cost counts
towards the cost cap (CR-017, CR-018, DL-43). Tier 1, against the fake OpenAI (tests/fake_openai.py):
no real model, no real key, no outside connection.

Two things to keep apart:
  * the CallRecord an agent function reports for each request (what the stage hands to the trace);
  * the trace table those records end up in, and the cost count of the run.
The first half of this file checks the first, the second half the second, and the last part checks
that a STAND-IN run's trace still looks exactly as it did before this step.
"""

import json
import re
import sqlite3

import pytest

from backend.db.connection import TRACE_ADDED_COLUMNS, connect, init_db
from backend.domain import sources
from backend.runtime import agents, crews, model_settings
from backend.runtime.attempts import AttemptLog
from backend.services import runs, trace
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_crews import _extract, _good_answer


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture(scope="module")
def paragraphs():
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


@pytest.fixture
def stand_in():
    return load_settings({"AGENTS_MODE": "stand_in", "STAND_IN_UNIT_PAUSE_S": "0"})


@pytest.fixture
def real(fake_openai, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": "gpt-6-test-e", "LLM_MODEL_VERIFY": "gpt-6-test-v",
        "LLM_MODEL_JUDGE": "gpt-6-test-j", "DATABASE_PATH": "unused.db"})


def _lines(settings, paragraphs):
    """Run one extraction; hand back the CallRecords it reported and the error it ended with."""
    lines, error = [], None
    try:
        _extract(settings, paragraphs, record=lines.append)
    except (crews.ModelServiceError, agents.InvalidOutput) as caught:
        error = caught
    return lines, error


# --- What the log reads off the wire ----------------------------------------------------------

def test_the_log_reads_an_answer_an_error_and_something_unreadable():
    log = AttemptLog()
    log.begin(json.dumps({"model": "m", "reasoning_effort": "low", "max_completion_tokens": 9,
                          "messages": []}).encode())
    log.finish(200, json.dumps({
        "model": "m-2026", "choices": [{"finish_reason": "length", "message": {"content": "{}"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 3}}).encode())
    log.begin(b"{}")
    log.finish(503, json.dumps({"error": {"message": "Overloaded", "type": "server_error"}}).encode())
    log.begin(b"{}")
    log.finish(200, b"<html>not json</html>")
    log.begin(b"{}")
    log.fail("ConnectionError: Request timed out.")

    answered, overloaded, unreadable, timed_out = log.attempts
    assert [a.n for a in log.attempts] == [1, 2, 3, 4]
    assert (answered.kind, answered.model_returned, answered.stop_reason) == ("answered", "m-2026", "length")
    assert (answered.tokens_in, answered.tokens_out, answered.text) == (12, 3, "{}")
    assert answered.sent_settings == {"max_completion_tokens": 9, "reasoning_effort": "low"}
    assert (overloaded.kind, overloaded.error) == ("unknown", "HTTP 503 server_error: Overloaded")
    assert unreadable.kind == "unknown" and "could not be read" in unreadable.error
    assert (timed_out.kind, timed_out.status_code) == ("unknown", None) and "timed out" in timed_out.error


def test_a_4xx_is_rejected_and_a_5xx_or_silence_is_unknown():
    log = AttemptLog()
    for status in (400, 401, 404, 429, 500, 502):
        log.begin(b"{}")
        log.finish(status, b'{"error": {"message": "x", "type": "t"}}')
    assert [a.kind for a in log.attempts] == ["rejected"] * 4 + ["unknown"] * 2


# --- What an attempt costs towards the cap ---------------------------------------------------

def test_an_answer_is_priced_from_its_usage_data_and_a_refusal_costs_nothing():
    answered = model_settings.attempt_cost_usd(
        "extract", kind="answered", tokens_in=1000, tokens_out=100, request_bytes=4000,
        max_completion_tokens=2000)
    assert answered == (pytest.approx(model_settings.call_cost_usd("extract", 1000, 100)), False)
    rejected = model_settings.attempt_cost_usd(
        "extract", kind="rejected", tokens_in=0, tokens_out=0, request_bytes=4000,
        max_completion_tokens=2000)
    assert rejected == (0.0, False)


def test_an_attempt_with_no_usage_data_is_charged_its_worst_case_and_marked_as_an_estimate():
    cost, estimated = model_settings.attempt_cost_usd(
        "verify", kind="unknown", tokens_in=0, tokens_out=0, request_bytes=40_000,
        max_completion_tokens=2000)
    # About 10,001 input tokens (one per four bytes) and an answer that fills its 2,000-token limit.
    assert estimated is True
    assert cost == pytest.approx(model_settings.call_cost_usd("verify", 10_001, 2000))
    assert cost < 0.05          # the ceiling of ONE call is a few US cents, far below the US$2.50 cap


def test_every_4xx_attempt_costs_nothing():
    """The rule the cost cap's safety rests on (H-073): a request the provider REFUSES (any 4xx) did
    no work and is not billed. CrewAI repeats a call only after such a refusal, so its repeat is
    the one billed request of that attempt."""
    for status in range(400, 500):
        log = AttemptLog()
        log.begin(b"{}" * 5000)                                      # a big request makes no difference
        log.finish(status, b'{"error": {"message": "refused", "type": "invalid_request_error"}}')
        [attempt] = log.attempts
        assert attempt.kind == "rejected", status
        assert model_settings.attempt_cost_usd(
            "judge", kind=attempt.kind, tokens_in=0, tokens_out=0,
            request_bytes=attempt.request_bytes, max_completion_tokens=4000) == (0.0, False), status


# --- One CallRecord per HTTP request ----------------------------------------------------------

def test_one_request_gives_one_line_with_what_the_api_returned(real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Reply(_good_answer(stand_in, paragraphs), tokens_in=1200, tokens_out=300,
                             model="gpt-6-test-e-returned", finish_reason="stop"))
    [line], error = _lines(real, paragraphs)
    assert error is None and len(fake_openai.requests) == 1
    assert line.model == "gpt-6-test-e" and line.model_returned == "gpt-6-test-e-returned"
    assert line.stop_reason == "stop" and line.attempt_n == 1
    assert (line.tokens_in, line.tokens_out) == (1200, 300)         # this request's own usage data
    assert line.cost_usd == pytest.approx(model_settings.call_cost_usd("extract", 1200, 300))
    assert line.cost_estimated is False and line.provider_error is None
    assert line.off_pinned_setting is False                         # it carried the pinned settings
    assert json.loads(line.settings_json) == {"max_completion_tokens": 2000,
                                              "reasoning_effort": "none", "temperature": 0.0}
    assert line.parsed_output and line.raw_output and line.validation_error is None


def test_a_cut_off_answer_shows_its_stop_reason(real, fake_openai, paragraphs):
    fake_openai.script(Reply('{"rows": [{"obligation_na', finish_reason="length"))
    [line], error = _lines(real, paragraphs)
    assert isinstance(error, agents.InvalidOutput) and len(fake_openai.requests) == 1
    assert line.stop_reason == "length" and line.validation_error and line.parsed_output is None


def test_a_failed_request_and_its_retry_are_two_lines(real, fake_openai, stand_in, paragraphs):
    fake_openai.script(Failure(503, "Overloaded"), Reply(_good_answer(stand_in, paragraphs)))
    [failed, answered], error = _lines(real, paragraphs)
    assert error is None and len(fake_openai.requests) == 2
    assert (failed.attempt_n, answered.attempt_n) == (1, 2)
    # The failed one: no output, no verdict, no usage data, the reason, and a charged estimate.
    assert failed.provider_error == "HTTP 503 server_error: Overloaded"
    assert failed.raw_output is None and failed.parsed_output is None and failed.validation_error is None
    assert (failed.tokens_in, failed.tokens_out, failed.model_returned, failed.stop_reason) == (0, 0, "", "")
    assert failed.cost_estimated is True and failed.cost_usd > 0
    # The one that answered: the output, the verdict, real usage data.
    assert answered.provider_error is None and answered.parsed_output and answered.cost_estimated is False
    assert answered.model_returned == "gpt-6-test-e" and answered.stop_reason == "stop"


def test_two_failures_are_two_lines_and_the_error_comes_after_them(real, fake_openai, paragraphs):
    fake_openai.script(Failure(500), Failure(500))
    lines, error = _lines(real, paragraphs)
    assert isinstance(error, crews.ModelServiceError) and len(fake_openai.requests) == 2
    assert [(line.attempt_n, line.cost_estimated) for line in lines] == [(1, True), (2, True)]
    assert all(line.provider_error.startswith("HTTP 500") for line in lines)


def test_a_refused_request_is_a_line_that_costs_nothing(real, fake_openai, paragraphs):
    fake_openai.script(Failure(400, "Bad request", "invalid_request_error"))
    [line], error = _lines(real, paragraphs)
    assert isinstance(error, crews.ModelServiceError) and len(fake_openai.requests) == 1
    assert line.provider_error == "HTTP 400 invalid_request_error: Bad request"
    assert (line.cost_usd, line.cost_estimated) == (0.0, False)


def test_a_rate_limited_request_and_its_retry_cost_nothing(real, fake_openai, paragraphs):
    fake_openai.script(Failure(429, "Rate limit", "rate_limit_exceeded"),
                       Failure(429, "Rate limit", "rate_limit_exceeded"))
    lines, error = _lines(real, paragraphs)
    assert isinstance(error, crews.ModelServiceError) and [line.cost_usd for line in lines] == [0.0, 0.0]


def test_a_timeout_is_a_line_with_no_response_and_a_charged_estimate(fake_openai, monkeypatch, paragraphs):
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    settings = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                              "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e",
                              "CALL_TIMEOUT_EXTRACT": "6"})              # client timeout 1 s (DL-43)
    fake_openai.script(Reply({"rows": []}, delay_s=2.0), Reply({"rows": []}, delay_s=2.0))
    lines, error = _lines(settings, paragraphs)
    assert isinstance(error, crews.ModelServiceError) and len(fake_openai.requests) == 2
    assert [line.attempt_n for line in lines] == [1, 2]
    for line in lines:
        assert "timed out" in line.provider_error and line.cost_estimated and line.cost_usd > 0
        assert line.model_returned == "" and line.duration_ms >= 900     # it waited out its 1 s


def test_a_bad_answer_after_a_retry_puts_the_verdict_on_the_last_line_only(
        real, fake_openai, paragraphs):
    fake_openai.script(Failure(500), Reply({"rows": [{"obligation_name": "Due 2027-01-10"}]}))
    [failed, answered], error = _lines(real, paragraphs)
    assert isinstance(error, agents.InvalidOutput)
    assert failed.validation_error is None and failed.provider_error
    assert answered.validation_error and answered.provider_error is None and answered.raw_output


# --- CrewAI's silent repeat without `reasoning_effort` (H-064 condition c), PR 5 step 4 ---------

def _forget_what_crewai_learned():
    crews.load_crewai()
    from crewai.llms.providers.openai import completion
    completion._LEARNED_NO_REASONING_EFFORT_MODELS.clear()


@pytest.fixture
def refuses_reasoning_effort(fake_openai):
    """A model that answers 400 "Unsupported parameter" to a request carrying `reasoning_effort`,
    as OpenAI does for a model that does not take it. Such a request is NOT taken from the script."""
    fake_openai.reject_params = frozenset({"reasoning_effort"})
    # CrewAI remembers a refusal for the rest of the process, keyed by the fake's URL. A later fake
    # could be given the same port by the operating system, so forget it before and after.
    forget = _forget_what_crewai_learned
    forget()
    yield fake_openai
    forget()


def test_crewai_repeats_a_refused_call_without_reasoning_effort_and_the_trace_shows_it(
        real, refuses_reasoning_effort, paragraphs):
    fake = refuses_reasoning_effort
    fake.script(Reply({"rows": []}))
    [refused, repeated], error = _lines(real, paragraphs)

    # CrewAI did it on its own: our code saw ONE call that worked, and the fake saw TWO requests.
    assert error is None and len(fake.requests) == 2
    assert "reasoning_effort" in fake.requests[0].body and "reasoning_effort" not in fake.requests[1].body

    # Line 1: what was refused. It carried the pinned settings, so it is not flagged; it cost nothing.
    assert refused.attempt_n == 1 and refused.provider_error.startswith("HTTP 400")
    assert "reasoning_effort" in refused.provider_error and refused.cost_usd == 0
    assert json.loads(refused.settings_json)["reasoning_effort"] == "none"
    assert refused.off_pinned_setting is False
    # Line 2: the repeat. It answered, WITHOUT the pinned reasoning effort, and the line says so.
    assert repeated.attempt_n == 2 and repeated.provider_error is None and repeated.parsed_output
    assert "reasoning_effort" not in json.loads(repeated.settings_json)
    assert repeated.off_pinned_setting is True


def test_crewai_then_leaves_reasoning_effort_out_of_every_later_call_and_each_is_flagged(
        real, refuses_reasoning_effort, paragraphs):
    """The quiet part: CrewAI remembers the refusal for the rest of the process. The next call is ONE
    request with no rejection to see, yet it is still off the pinned setting, and still flagged."""
    fake = refuses_reasoning_effort
    fake.script(Reply({"rows": []}), Reply({"rows": []}), Reply({"rows": []}))
    _lines(real, paragraphs)
    before = len(fake.requests)
    [later], error = _lines(real, paragraphs)
    assert error is None and len(fake.requests) - before == 1
    assert "reasoning_effort" not in fake.requests[-1].body
    assert later.attempt_n == 1 and later.provider_error is None and later.off_pinned_setting is True


def test_our_retry_plus_crewais_repeat_is_at_most_four_requests_and_four_lines(
        real, refuses_reasoning_effort, paragraphs):
    """Our bound is two attempts. Each can carry CrewAI's repeat, so four requests are possible. Here:
    refused, repeated and failed (500), then our retry: refused, repeated, answered."""
    fake = refuses_reasoning_effort
    fake.script(Failure(500), Reply({"rows": []}))
    lines, error = _lines(real, paragraphs)
    assert error is None and len(fake.requests) == 4 and fake.unscripted == []
    assert [line.attempt_n for line in lines] == [1, 2, 3, 4]
    assert [line.off_pinned_setting for line in lines] == [False, True, False, True]
    assert [bool(line.provider_error) for line in lines] == [True, True, True, False]


@pytest.mark.parametrize("script", [
    pytest.param([Failure(500), Reply({"rows": []})], id="500 then an answer"),
    pytest.param([Failure(500), Failure(500)], id="500 twice, final failure"),
    pytest.param([Reply({"rows": []}, delay_s=2.0), Reply({"rows": []})], id="timeout then an answer"),
])
def test_four_requests_bill_at_most_two(refuses_reasoning_effort, monkeypatch, paragraphs, script):
    """The worst case: CrewAI's repeat inside BOTH of our attempts. Four requests reach the model
    (refused, repeated, refused, repeated), but every refusal costs 0, so at most the bound of
    billed requests per unit (2) is charged, and the stage's cost count is exactly the sum of them."""
    monkeypatch.setenv("OPENAI_BASE_URL", refuses_reasoning_effort.base_url)
    settings = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike",
                              "OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": "gpt-6-test-e",
                              "CALL_TIMEOUT_EXTRACT": "6"})            # client timeout 1 s (DL-43)
    refuses_reasoning_effort.script(*script)
    lines, _ = _lines(settings, paragraphs)

    assert len(refuses_reasoning_effort.requests) == crews.MAX_REQUESTS_PER_UNIT == len(lines) == 4
    refused, billed = lines[0::2], lines[1::2]                      # each refusal, then CrewAI's repeat
    assert all(line.provider_error.startswith("HTTP 400") and line.cost_usd == 0 for line in refused)
    assert all(line.off_pinned_setting for line in billed)
    assert [line for line in lines if line.cost_usd > 0] == billed
    assert len(billed) <= crews.MAX_BILLED_REQUESTS_PER_UNIT


def test_the_cost_count_of_a_four_request_unit_is_the_two_billed_requests(real_db, refuses_reasoning_effort):
    settings, conn = real_db
    settings = settings.__class__(**{**settings.__dict__, "run_cost_cap_usd": 2.50})
    refuses_reasoning_effort.script(Failure(500), Reply({"rows": []}, tokens_in=1000, tokens_out=100),
                                    *[Reply({"rows": []})] * 4)
    run_id = flow.start_to_g1(conn, settings)
    first_unit = [t for t in trace.list_trace(conn, run_id) if t["unit_id"] == "SRC-CSSF15627"]
    assert [t["attempt_n"] for t in first_unit] == [1, 2, 3, 4]
    assert [t["cost_usd"] > 0 for t in first_unit] == [False, True, False, True]
    assert sum(t["cost_usd"] for t in first_unit) == pytest.approx(
        first_unit[1]["cost_usd"] + first_unit[3]["cost_usd"])
    assert runs.get_run(conn, run_id)["cost_so_far"] == pytest.approx(
        sum(t["cost_usd"] for t in trace.list_trace(conn, run_id)))


def test_a_call_that_stays_on_its_pinned_settings_is_never_flagged(real, fake_openai, paragraphs):
    fake_openai.script(Failure(500), Reply({"rows": []}))
    lines, error = _lines(real, paragraphs)
    assert error is None and [line.off_pinned_setting for line in lines] == [False, False]


def test_the_flag_reaches_the_trace_table_and_does_not_stop_the_run(real_db, refuses_reasoning_effort):
    """Stage A over five documents on a model that refuses `reasoning_effort`: the run is NOT failed
    by it. The first unit has the refused request and the repeat; the other four go straight to the
    repeat. Six lines, five flagged, and the cost count equals the trace."""
    settings, conn = real_db
    settings = settings.__class__(**{**settings.__dict__, "run_cost_cap_usd": 2.50})
    refuses_reasoning_effort.script(*[Reply({"rows": []}, tokens_in=1000, tokens_out=100)] * 5)
    run_id = flow.start_to_g1(conn, settings)

    lines = trace.list_trace(conn, run_id)
    assert runs.get_run(conn, run_id)["status"] == "ACTIVE"                 # at G1, not failed
    assert [(t["unit_id"] == lines[0]["unit_id"], t["attempt_n"], t["off_pinned_setting"])
            for t in lines][:2] == [(True, 1, 0), (True, 2, 1)]
    assert len(lines) == 6 and sum(t["off_pinned_setting"] for t in lines) == 5
    assert runs.get_run(conn, run_id)["cost_so_far"] == pytest.approx(sum(t["cost_usd"] for t in lines))


# --- The trace table and the cost cap ---------------------------------------------------------

@pytest.fixture
def real_db(fake_openai, monkeypatch, tmp_path):
    """A real-mode run against the fake, with a cost cap that is tiny: US$0.001."""
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    settings = load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": "gpt-6-test-e", "LLM_MODEL_VERIFY": "gpt-6-test-v",
        "LLM_MODEL_JUDGE": "gpt-6-test-j", "SESSION_SECRET": "test-only",
        "DATABASE_PATH": str(tmp_path / "real.db"), "RUN_COST_CAP_USD": "0.001"})
    init_db(settings.database_path)
    return settings, connect(settings.database_path)


def test_a_failed_attempts_cost_counts_towards_the_cap(real_db, fake_openai):
    """Unit 1: a 500, then a good answer that cost US$0.00015 by its own usage data. That alone is
    under the US$0.001 cap, so before this step unit 2 would have started. The failed attempt is
    charged its worst case (about US$0.0012), so the cap is reached and unit 2 never starts."""
    settings, conn = real_db
    fake_openai.script(Failure(500), Reply({"rows": []}, tokens_in=1000, tokens_out=100),
                       Reply({"rows": []}))
    run_id = flow.start_to_g1(conn, settings)

    run = runs.get_run(conn, run_id)
    units = runs.list_units(conn, run_id)
    assert (units[0]["status"], units[1]["status"], units[1]["failure_reason"]) == (
        "done", "failed", "cost cap")
    assert run["status"] == "FAILED" and len(fake_openai.requests) == 2      # unit 2 sent nothing
    failed, answered = trace.list_trace(conn, run_id)
    assert (failed["attempt_n"], answered["attempt_n"]) == (1, 2)
    assert failed["cost_estimated"] == 1 and failed["cost_usd"] > 0.001 - answered["cost_usd"]
    assert answered["cost_usd"] == pytest.approx(0.00015)
    assert run["cost_so_far"] == pytest.approx(failed["cost_usd"] + answered["cost_usd"])


def test_each_attempt_has_a_trace_line_a_cost_and_an_audit_entry(real_db, fake_openai):
    settings, conn = real_db
    fake_openai.script(Failure(500), Reply({"rows": []}, tokens_in=1000, tokens_out=100))
    run_id = flow.start_to_g1(conn, settings)
    lines = trace.list_trace(conn, run_id)
    refs = [r["trace_ref"] for r in conn.execute(
        "SELECT trace_ref FROM audit_log WHERE run_id = ? AND event_type = 'agent_output' "
        "ORDER BY audit_id", (run_id,))]
    assert refs == [trace.record_key(run_id, t["step"], t["stage_attempt"], t["unit_id"],
                                     t["attempt_n"]) for t in lines]
    reasons = [r["reason"] for r in conn.execute(
        "SELECT reason FROM audit_log WHERE run_id = ? AND event_type = 'agent_output' "
        "ORDER BY audit_id", (run_id,))]
    assert reasons == ["extract_rows no answer (provider error)", "extract_rows output"]


def test_a_unit_that_failed_for_good_still_has_its_attempts_traced(real_db, fake_openai):
    settings, conn = real_db
    fake_openai.script(Failure(500), Failure(500))
    run_id = flow.start_to_g1(conn, settings)
    assert runs.list_units(conn, run_id)[0]["failure_reason"] == "model service"
    lines = trace.list_trace(conn, run_id)
    assert [(t["attempt_n"], t["cost_estimated"]) for t in lines] == [(1, 1), (2, 1)]
    assert runs.get_run(conn, run_id)["cost_so_far"] == pytest.approx(sum(t["cost_usd"] for t in lines))


def test_output_that_arrives_late_is_judged_by_the_request_that_answered(real_db, fake_openai, monkeypatch):
    """The first request failed (not late), the retry answered after the stage had failed (late).
    The stage must go by the LAST trace line: this output is kept in the trace only."""
    settings, conn = real_db
    fake_openai.script(Failure(500), Reply({"rows": []}))
    real_record = trace.record_call
    calls = []

    def record_with_lateness(conn_, *, run, stage, unit_id, call, spend_activity=None):
        calls.append(call.attempt_n)
        late = real_record(conn_, run=run, stage=stage, unit_id=unit_id, call=call,
                           spend_activity=spend_activity)
        return late or call.attempt_n == 2      # as if the stage had failed while the retry ran

    monkeypatch.setattr(trace, "record_call", record_with_lateness)
    run_id = flow.start_to_g1(conn, settings)
    assert calls[:2] == [1, 2]
    assert conn.execute("SELECT COUNT(*) FROM rows").fetchone()[0] == 0     # nothing stored (rule 9)
    assert runs.list_units(conn, run_id)[1]["status"] == "waiting"           # no other unit started


# --- The table only grew: nothing dropped or renamed ------------------------------------------

ORIGINAL_TRACE_COLUMNS = [
    "trace_id", "run_id", "fund_id", "step", "stage_attempt", "unit_id", "attempt_n", "at",
    "prompt_version", "model", "model_returned", "settings_json", "max_tokens", "input_hash",
    "raw_output", "parsed_output", "validation_error", "tokens_in", "tokens_out", "cost_usd",
    "duration_ms", "spend_activity", "eval_case", "late"]


def _columns(conn):
    return [row["name"] for row in conn.execute("PRAGMA table_info(trace)")]


ADDED_TRACE_COLUMNS = ["stop_reason", "provider_error", "cost_estimated", "off_pinned_setting"]


def test_the_trace_table_kept_every_column_in_place_and_added_four_at_the_end(settings):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    assert _columns(conn) == ORIGINAL_TRACE_COLUMNS + ADDED_TRACE_COLUMNS
    assert list(TRACE_ADDED_COLUMNS) == ADDED_TRACE_COLUMNS


def test_a_database_made_before_this_step_gets_the_columns_and_keeps_its_lines(settings):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    before = [dict(t) for t in trace.list_trace(conn, run_id)]
    for name in TRACE_ADDED_COLUMNS:                    # make it look like an older database
        conn.execute(f"ALTER TABLE trace DROP COLUMN {name}")
    conn.commit()
    assert _columns(conn) == ORIGINAL_TRACE_COLUMNS
    conn.close()

    init_db(settings.database_path)                      # the next start migrates it
    conn = connect(settings.database_path)
    assert _columns(conn) == ORIGINAL_TRACE_COLUMNS + list(TRACE_ADDED_COLUMNS)
    after = [dict(t) for t in trace.list_trace(conn, run_id)]
    assert [{k: v for k, v in t.items() if k not in TRACE_ADDED_COLUMNS} for t in after] == [
        {k: v for k, v in t.items() if k not in TRACE_ADDED_COLUMNS} for t in before]
    assert all((t["stop_reason"], t["provider_error"], t["cost_estimated"], t["off_pinned_setting"])
               == ("", None, 0, 0) for t in after)
    init_db(settings.database_path)                      # and doing it twice is harmless


def test_the_trace_is_still_append_only_after_the_change(settings):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    flow.start_to_g1(conn, settings)
    with pytest.raises(sqlite3.DatabaseError, match="append-only"):
        conn.execute("UPDATE trace SET stop_reason = 'x'")


# --- A stand-in run's trace looks the same as before ------------------------------------------

def test_a_stand_in_runs_trace_looks_the_same_as_before(settings):
    """The 11 lines of a stand-in run to G1 (5 extractor units, 6 verifier units): every old column
    holds what it always held, and the three new ones hold their defaults. Nothing about a stand-in
    run is written differently, and the audit entries are the same and still 1 to 1."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    lines = trace.list_trace(conn, run_id)

    assert [t["step"] for t in lines] == ["extract_rows"] * 5 + ["check_conflicts"] * 6
    assert [t["attempt_n"] for t in lines] == [1] * 11
    for t in lines:
        assert (t["model"], t["model_returned"], t["settings_json"], t["max_tokens"]) == ("", "", "{}", None)
        assert (t["tokens_in"], t["tokens_out"], t["cost_usd"], t["late"]) == (0, 0, 0, 0)
        assert t["spend_activity"] is None and t["eval_case"] is None
        assert t["parsed_output"] and t["validation_error"] is None and t["raw_output"]
        assert re.fullmatch(r"[0-9a-f]{16}\+stand-in:[0-9a-f]{8}", t["prompt_version"])
        assert re.fullmatch(r"[0-9a-f]{64}", t["input_hash"]) and t["at"]
        # The three new columns: what a line that is not a real request holds.
        assert (t["stop_reason"], t["provider_error"], t["cost_estimated"],
                t["off_pinned_setting"]) == ("", None, 0, 0)

    audit = [(r["trace_ref"], r["reason"]) for r in conn.execute(
        "SELECT trace_ref, reason FROM audit_log WHERE run_id = ? AND event_type = 'agent_output' "
        "ORDER BY audit_id", (run_id,))]
    assert audit == [(trace.record_key(run_id, t["step"], t["stage_attempt"], t["unit_id"], 1),
                      f"{t['step']} output") for t in lines]
    assert runs.get_run(conn, run_id)["cost_so_far"] == 0


def test_a_stand_in_call_sends_nothing_and_never_builds_an_attempt_log(fake_openai, stand_in, paragraphs):
    lines = []
    _extract(stand_in, paragraphs, record=lines.append)
    [line] = lines
    assert fake_openai.requests == []
    assert (line.attempt_n, line.stop_reason, line.provider_error, line.cost_estimated,
            line.off_pinned_setting) == (1, "", None, False, False)
