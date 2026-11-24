"""The evaluation run starter, PR 4a (H-097): `python -m backend.evaluation run`.

What PR 4a does: every refusal, the plan, the typed confirmation, then starts an evaluation run as
`specialist-eval` and lets Stage A finish. It also checks Stage A's trace and ends the run if a request
got a 400 (even one CrewAI's silent repeat got past), a length stop, or an invalid answer. (Since PR 4b
the run then goes on through the scripted gates: those tests are in test_evaluation_scripted_gates.py.)

How these tests stay safe (H-097 checks):
  * Real mode against the fake OpenAI on this machine, the dummy key, temporary databases, a temporary
    spike database and a temporary report/export folder. No real call; no file under `data/` is touched.
  * `SPIKE_DB` (the real data/spike.db) is pointed at a file that does not exist, for every test.
"""

import sqlite3

import pytest

from backend.db.connection import connect
from backend.evaluation import __main__ as cli
from backend.evaluation import run_starter, trace_export
from backend.runtime import crews
from backend.services import FUND_ID, runs
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY, Reply
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key

COMMIT = "abc1234"
CONFIRM = f"evaluate {COMMIT} 21"


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def spike_db(tmp_path, monkeypatch):
    """A spike database that does not exist (it counts as 0 and is never created). The real one is
    never named by any test."""
    nowhere = tmp_path / "spike" / "spike.db"
    monkeypatch.setattr(run_starter, "SPIKE_DB", nowhere)
    return nowhere


def make_env(tmp_path, **changes):
    env = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "evaluation", "OPENAI_API_KEY": TEST_API_KEY,
           "LLM_MODEL_EXTRACT": MODELS["extract"], "LLM_MODEL_VERIFY": MODELS["verify"],
           "LLM_MODEL_JUDGE": MODELS["judge"], "SESSION_SECRET": "test-only",
           "DATABASE_PATH": str(tmp_path / "app.db")}
    env.update(changes)
    return env


class Console:
    """What the command printed, and what the 'operator' types."""

    def __init__(self, typed=CONFIRM):
        self.lines, self.typed, self.asked = [], typed, []

    def out(self, text=""):
        self.lines.append(str(text))

    def read_line(self, prompt):
        self.asked.append(prompt)
        if isinstance(self.typed, Exception):
            raise self.typed
        return self.typed

    @property
    def text(self):
        return "\n".join(self.lines)


@pytest.fixture
def fake(as_openai):
    as_openai.answer_with(the_answer_key)
    return as_openai


@pytest.fixture
def env(tmp_path):
    return make_env(tmp_path)


def start(env, spike_db, tmp_path, console, *args):
    code = run_starter.main(list(args), env=env, spike_db=spike_db, out=console.out,
                            read_line=console.read_line, commit=COMMIT, report_dir=tmp_path / "logs")
    return code


def app_db(env):
    return connect(env["DATABASE_PATH"])


def add_spike_lines(spike_db, n):
    """n real evaluation trace lines in a throwaway spike database (what earlier calls would leave)."""
    from backend.db.connection import init_db
    spike_db.parent.mkdir(parents=True, exist_ok=True)
    init_db(spike_db)
    conn = connect(spike_db)
    conn.execute("INSERT INTO runs (run_id, fund_id, status, phase, agents_mode, started_by, started_at,"
                 " spend_activity) VALUES ('RUN-X', ?, 'FAILED', 'AT_G1', 'real', 'x', 'now', 'evaluation')",
                 (FUND_ID,))
    for i in range(n):
        conn.execute("INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at,"
                     " prompt_version, input_hash, spend_activity) VALUES ('RUN-X', ?, 'extract_rows', 1,"
                     " ?, 1, 'now', 'v', 'h', 'evaluation')", (FUND_ID, f"U{i}"))
    conn.commit()
    conn.close()


# --- The plan (no --go): sends nothing, creates nothing -----------------------------------------------

def test_the_plan_shows_the_commit_models_projected_calls_and_the_cap(env, spike_db, tmp_path, fake):
    console = Console()
    code = start(env, spike_db, tmp_path, console)
    assert code == 0 and console.asked == []
    text = console.text
    assert COMMIT in text and all(model in text for model in MODELS.values())
    assert "19 calls expected" in text and "21 at most" in text           # (5 + 6 + 6) + 2 copy cases; the most seen + 2
    assert "0 of 63" in text and "--go" in text
    assert fake.requests == []                                              # nothing sent
    assert not (tmp_path / "app.db").exists() and not spike_db.exists()     # nothing created


def test_the_projected_calls_come_from_the_documents_and_the_answer_key():
    assert run_starter.expected_calls() == 17      # 5 documents + 6 verifications + 6 judgements
    assert run_starter.WORST_CASE_CALLS == 21 and run_starter.HARNESS_CALLS == 2


# --- Refusals come first, before any prompt, and send nothing ------------------------------------------

REFUSAL_CASES = [
    ("stand-in mode", {"AGENTS_MODE": "stand_in"}, "stand-in"),
    ("not an evaluation activity", {"SPEND_ACTIVITY": "spike"}, "evaluation"),
    ("no key", {"OPENAI_API_KEY": ""}, "OPENAI_API_KEY"),
    ("a model not set", {"LLM_MODEL_JUDGE": ""}, "LLM_MODEL_JUDGE"),
]


@pytest.mark.parametrize("name,change,word", REFUSAL_CASES, ids=[c[0] for c in REFUSAL_CASES])
def test_a_refusal_is_printed_before_any_prompt_and_nothing_is_sent_or_created(
        name, change, word, tmp_path, spike_db, fake):
    env = make_env(tmp_path, **change)
    console = Console()
    assert start(env, spike_db, tmp_path, console, "--go") == 2
    assert "REFUSED" in console.text and word in console.text
    assert console.asked == [] and fake.requests == []
    assert not (tmp_path / "app.db").exists()


def test_the_planted_row_switch_is_refused(env):
    settings = load_settings(env)
    with pytest.raises(run_starter.StarterRefused, match="planted row"):
        run_starter.build_plan(settings, spike_db=None, commit=COMMIT, demo_planted_row=True)


def test_there_is_no_command_line_way_to_turn_the_planted_row_on(env, spike_db, tmp_path, capsys):
    with pytest.raises(SystemExit):
        start(env, spike_db, tmp_path, Console(), "--planted-row")


@pytest.mark.parametrize("used,allowed", [(42, True), (43, False), (63, False)])
def test_the_run_must_fit_under_the_63_call_cap_counting_the_worst_case(
        used, allowed, env, tmp_path, spike_db, fake):
    add_spike_lines(spike_db, used)
    console = Console()
    code = start(env, spike_db, tmp_path, console, "--go")
    if allowed:
        assert code == 0 and "REFUSED" not in console.text
    else:
        assert code == 2 and "REFUSED" in console.text and f"{used} of 63" in console.text
        assert fake.requests == [] and console.asked == []


def test_a_call_count_that_cannot_be_read_is_a_refusal(env, tmp_path, spike_db, fake):
    spike_db.parent.mkdir(parents=True)
    spike_db.write_bytes(b"this is not a database file at all" * 20)
    console = Console()
    assert start(env, spike_db, tmp_path, console, "--go") == 2
    assert "REFUSED" in console.text and "cannot be read" in console.text and fake.requests == []


# --- The typed confirmation ----------------------------------------------------------------------------

@pytest.mark.parametrize("typed", ["", "yes", "evaluate abc1234", "evaluate abc1234 19", "evaluate other 21",
                                   EOFError(), OSError()], ids=str)
def test_anything_but_the_exact_words_cancels_and_sends_nothing(typed, env, tmp_path, spike_db, fake):
    console = Console(typed=typed)
    assert start(env, spike_db, tmp_path, console, "--go") == 2
    assert "NOT CONFIRMED" in console.text and fake.requests == []
    assert not (tmp_path / "app.db").exists()
    assert CONFIRM in console.asked[0]                  # the prompt names the exact words


# --- Confirmed: a run starts as specialist-eval (PR 4b: and goes through the scripted gates) -----------

def test_a_confirmed_run_starts_as_specialist_eval_in_real_mode_with_the_planted_row_off(
        env, tmp_path, spike_db, fake):
    console = Console()
    assert start(env, spike_db, tmp_path, console, "--go") == 0
    conn = app_db(env)
    run = runs.list_runs(conn, FUND_ID)[0]
    row = dict(conn.execute("SELECT * FROM runs WHERE run_id = ?", (run["run_id"],)).fetchone())
    assert (row["started_by"], row["spend_activity"], row["agents_mode"], row["demo_planted_row"]) == \
        ("specialist-eval", "evaluation", "real", 0)
    assert runs.is_evaluation_run(row)
    assert (tmp_path / "logs" / run["run_id"]).is_dir()  # the reports were saved here, not in the repo


def test_a_second_start_while_a_review_is_in_progress_is_refused_before_the_prompt(
        env, tmp_path, spike_db, fake):
    from backend.db.connection import init_db
    from tests import flow
    stand_in = load_settings({"AGENTS_MODE": "stand_in", "DATABASE_PATH": env["DATABASE_PATH"],
                              "SESSION_SECRET": "test-only", "STAND_IN_UNIT_PAUSE_S": "0"})
    init_db(stand_in.database_path)
    flow.start_to_g1(connect(stand_in.database_path), stand_in)      # an ordinary review, waiting at G1
    console = Console()
    assert start(env, spike_db, tmp_path, console, "--go") == 2
    assert "REFUSED" in console.text and "in progress" in console.text
    assert console.asked == [] and fake.requests == []


# --- Stopping: a 400, a length stop, an invalid answer -------------------------------------------------

def test_a_400_that_crewai_repeats_past_still_stops_the_run(env, tmp_path, spike_db, fake):
    fake.reject_params = frozenset({"reasoning_effort"})  # the provider refuses a setting; CrewAI repeats
    console = Console()
    code = start(env, spike_db, tmp_path, console, "--go")
    conn = app_db(env)
    run = runs.list_runs(conn, FUND_ID)[0]
    assert code == 1 and "STOPPED" in console.text and "400" in console.text
    assert run["status"] == "ABANDONED"                   # the script ended it; no gate was reached
    reason = conn.execute("SELECT actor, reason FROM audit_log WHERE run_id = ? AND event_type = 'gate_event'"
                          " ORDER BY audit_id DESC", (run["run_id"],)).fetchone()
    assert reason["actor"] == "specialist-eval" and "400" in reason["reason"]
    assert conn.execute("SELECT COUNT(*) FROM row_decisions").fetchone()[0] == 0


def test_an_invalid_answer_fails_the_run_and_the_command_reports_it(env, tmp_path, spike_db, fake):
    bad = []

    def one_bad_answer(body):
        if body["model"] == MODELS["extract"] and not bad:
            bad.append(1)                                  # the first extraction only
            return Reply("this is not the schema")
        return the_answer_key(body)
    fake.answer_with(one_bad_answer)
    console = Console()
    code = start(env, spike_db, tmp_path, console, "--go")
    run = runs.list_runs(app_db(env), FUND_ID)[0]
    assert code == 1 and run["status"] == "FAILED" and "STOPPED" in console.text
    assert "invalid output" in console.text.lower()


def test_a_stopped_run_still_exports_its_trace_and_the_export_matches(env, tmp_path, spike_db, fake):
    fake.reject_params = frozenset({"reasoning_effort"})
    start(env, spike_db, tmp_path, Console(), "--go")
    conn = app_db(env)
    run_id = runs.list_runs(conn, FUND_ID)[0]["run_id"]
    assert trace_export.check_export(conn, run_id, tmp_path / "logs").ok


# --- The stop check on its own: what counts as a stop --------------------------------------------------

def line(conn, run_id, n, **columns):
    names = ", ".join(["run_id", "fund_id", "step", "stage_attempt", "unit_id", "attempt_n", "at",
                       "prompt_version", "input_hash"] + list(columns))
    marks = ", ".join("?" * (9 + len(columns)))
    conn.execute(f"INSERT INTO trace ({names}) VALUES ({marks})",
                 (run_id, FUND_ID, "extract_rows", 1, f"U{n}", 1, "now", "v", "h", *columns.values()))
    conn.commit()


@pytest.fixture
def quiet_run(env, tmp_path, spike_db, fake):
    start(env, spike_db, tmp_path, Console(), "--go")
    conn = app_db(env)
    return conn, runs.list_runs(conn, FUND_ID)[0]["run_id"]


def test_a_clean_stage_a_has_no_stop_reason(quiet_run):
    conn, run_id = quiet_run
    assert run_starter.stop_reasons(conn, run_id) == []


@pytest.mark.parametrize("columns,word", [
    ({"provider_error": "HTTP 400 invalid_request_error: Unsupported parameter"}, "400"),
    ({"stop_reason": "length"}, "length"),
    ({"validation_error": "the answer does not match the schema"}, "invalid"),
], ids=["a 400", "a length stop", "an invalid answer"])
def test_each_of_these_trace_lines_is_a_stop(columns, word, quiet_run):
    conn, run_id = quiet_run
    line(conn, run_id, 99, **columns)
    reasons = run_starter.stop_reasons(conn, run_id)
    assert len(reasons) == 1 and word in reasons[0] and "U99" in reasons[0]


def test_other_provider_errors_are_not_this_check(quiet_run):
    """A 429 or a 500 is the DL-43 retry's business, and a unit that fails for it already ends the run."""
    conn, run_id = quiet_run
    line(conn, run_id, 98, provider_error="HTTP 429 rate_limit: slow down")
    line(conn, run_id, 97, provider_error="HTTP 500 server_error: oops")
    assert run_starter.stop_reasons(conn, run_id) == []


# --- The command word, and nothing else changed --------------------------------------------------------

def test_the_run_word_is_handed_to_the_starter(monkeypatch):
    seen = []
    monkeypatch.setattr(run_starter, "main", lambda argv: seen.append(argv) or 0)
    assert cli.main(["run", "--go"]) == 0 and seen == [["--go"]]


def test_the_starter_never_opens_the_real_spike_database_by_default(spike_db):
    assert run_starter.SPIKE_DB == spike_db and not str(spike_db).endswith("data/spike.db")


def test_the_trace_table_is_still_append_only(quiet_run):
    conn, run_id = quiet_run
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM trace WHERE run_id = ?", (run_id,))
