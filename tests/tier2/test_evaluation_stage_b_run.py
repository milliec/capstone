"""Grading a finished stage B run read from the database, its report, and the command line.

Stand-in runs, no model. The trace is append-only (triggers refuse UPDATE), so a test that needs
"real" time and cost inserts extra trace lines, which is what the app does too.
"""

import json

import pytest

from backend.db.connection import connect, init_db
from backend.evaluation import __main__ as cli
from backend.evaluation import grade, report, stage_b
from backend.evaluation.stage_a import NotGradable
from tests import flow


@pytest.fixture
def conn(settings, monkeypatch):
    init_db(settings.database_path)
    connection = connect(settings.database_path)
    monkeypatch.setenv("DATABASE_PATH", str(settings.database_path))
    monkeypatch.setenv("AGENTS_MODE", "stand_in")
    yield connection
    connection.close()


def by_id(rep):
    return {c["id"]: c for c in rep["criteria"]}


def add_trace_line(conn, run_id, unit, *, ms, cost, eval_case=None, late=0):
    conn.execute(
        "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
        "prompt_version, input_hash, duration_ms, cost_usd, eval_case, late) "
        "VALUES (?, 'FND-DEMO-01', 'judge_applicability', 1, ?, 1, 'now', 'v', 'h', ?, ?, ?, ?)",
        (run_id, unit, ms, cost, eval_case, late))
    conn.commit()


def make_real(conn, run_id, activity="evaluation"):
    conn.execute("UPDATE runs SET agents_mode = 'real', spend_activity = ? WHERE run_id = ?",
                 (activity, run_id))
    conn.commit()


def set_cost_count(conn, run_id, cost):
    conn.execute("UPDATE runs SET cost_so_far = ? WHERE run_id = ?", (cost, run_id))
    conn.commit()


# --- A finished stand-in run ----------------------------------------------------------------

def test_a_stand_in_run_is_graded_and_stamped(conn, settings):
    run_id = flow.to_g3(conn, settings)
    rep = stage_b.evaluate_stage_b(conn, run_id)
    assert rep["report"] == "stage-b" and rep["counts_for_cycle"] is False
    assert rep["does_not_count_because"] == ["STAND-IN RUN: does not count towards the cycle"]
    assert (rep["verdicts_stored"], rep["rows_approved_at_g1"], rep["trace_calls"]) == (6, 6, 17)
    results = by_id(rep)
    assert results["EC-004"]["status"] == grade.PASS        # the stand-in verdicts equal the key's
    assert results["EC-010"]["status"] == grade.NOT_TESTED  # stand-in: measures nothing
    assert results["EC-012"]["status"] == grade.INCOMPLETE


def test_it_can_be_graded_as_soon_as_stage_b_has_stored_before_g2_is_done(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n])
    flow.finish_g1(conn, settings, run_id)                  # stage B runs; the run waits at G2
    assert stage_b.evaluate_stage_b(conn, run_id)["run"]["phase"] == "AT_G2"


def test_a_row_rejected_at_g1_is_not_tested_not_a_miss(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    for n in (1, 2, 3, 4, 5):
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n])
    flow.reject_rule(conn, run_id, 6, "Not for this fund")
    flow.finish_g1(conn, settings, run_id)
    rep = stage_b.evaluate_stage_b(conn, run_id)
    ec004 = by_id(rep)["EC-004"]
    assert ec004["status"] == grade.INCOMPLETE and rep["verdicts_stored"] == 5
    assert [c["status"] for c in ec004["checks"]].count(grade.NOT_TESTED) == 1
    assert "not approved at G1" in ec004["checks"][-1]["note"]


# --- Real-looking numbers (extra trace lines) -----------------------------------------------

def test_a_real_run_inside_both_limits_passes(conn, settings):
    run_id = flow.to_g3(conn, settings)
    add_trace_line(conn, run_id, "REAL-1", ms=120_000, cost=1.5)
    set_cost_count(conn, run_id, 1.5)
    make_real(conn, run_id)
    rep = stage_b.evaluate_stage_b(conn, run_id)
    assert rep["counts_for_cycle"] is True
    assert by_id(rep)["EC-010"]["status"] == by_id(rep)["EC-012"]["status"] == grade.PASS


def test_over_5_minutes_or_over_2_dollars_is_a_miss_with_the_numbers(conn, settings):
    run_id = flow.to_g3(conn, settings)
    add_trace_line(conn, run_id, "REAL-1", ms=200_000, cost=1.5)
    add_trace_line(conn, run_id, "REAL-2", ms=100_000, cost=0.6, late=1)
    set_cost_count(conn, run_id, 2.1)
    make_real(conn, run_id)
    results = by_id(stage_b.evaluate_stage_b(conn, run_id))
    assert results["EC-010"]["status"] == grade.MISS
    assert results["EC-010"]["findings"][0]["actual"] == "300.0 s"       # exactly 5 minutes: a miss
    assert "1 late" in results["EC-010"]["summary"]
    assert results["EC-012"]["status"] == grade.MISS
    assert results["EC-012"]["findings"][0]["actual"] == "US$2.1000"


def test_copy_case_calls_count_towards_the_runs_time_and_cost_and_are_named(conn, settings):
    run_id = flow.to_g3(conn, settings)
    add_trace_line(conn, run_id, "I-1-COPY", ms=5_000, cost=0.02, eval_case="I-1")
    set_cost_count(conn, run_id, 0.02)
    make_real(conn, run_id)
    ec012 = by_id(stage_b.evaluate_stage_b(conn, run_id))["EC-012"]
    assert "US$0.0200" in ec012["summary"] and "1 copy-case" in ec012["summary"]


def test_a_trace_that_does_not_add_up_to_the_run_cost_count_is_flagged(conn, settings):
    run_id = flow.to_g3(conn, settings)
    add_trace_line(conn, run_id, "REAL-1", ms=1_000, cost=0.5)
    set_cost_count(conn, run_id, 0.4)                         # the run says less than the trace
    make_real(conn, run_id)
    ec012 = by_id(stage_b.evaluate_stage_b(conn, run_id))["EC-012"]
    assert ec012["status"] == grade.MISS
    assert ec012["findings"][0]["what"] == "trace total against the run's cost count"


# --- Not gradable ---------------------------------------------------------------------------

def test_stage_b_not_started_or_not_finished_is_not_gradable(conn, settings):
    run_id = flow.start_to_g1(conn, settings)                 # at G1: stage B has not started
    with pytest.raises(NotGradable, match="Stage B never started"):
        stage_b.evaluate_stage_b(conn, run_id)
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")
    conn.commit()
    run_id = flow.to_g3(conn, settings)
    conn.execute("UPDATE units SET status = 'failed' WHERE run_id = ? AND stage = 'B' "
                 "AND rowid = (SELECT MIN(rowid) FROM units WHERE run_id = ? AND stage = 'B')",
                 (run_id, run_id))
    conn.commit()
    with pytest.raises(NotGradable, match="did not finish"):
        stage_b.evaluate_stage_b(conn, run_id)


def test_an_unknown_run_is_not_gradable(conn):
    with pytest.raises(NotGradable, match="no run RUN-NOPE"):
        stage_b.evaluate_stage_b(conn, "RUN-NOPE")


def test_grading_stage_b_writes_nothing(conn, settings):
    run_id = flow.to_g3(conn, settings)
    tables = ("runs", "rows", "verdicts", "flags", "audit_log", "trace", "units")
    count = lambda: [conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables]
    before = count()
    stage_b.evaluate_stage_b(conn, run_id)
    assert count() == before


# --- The report and the command line --------------------------------------------------------

def test_the_text_names_what_was_not_tested_and_never_calls_it_a_pass(conn, settings):
    run_id = flow.to_g3(conn, settings)
    text = report.render_markdown(stage_b.evaluate_stage_b(conn, run_id))
    assert text.startswith("# Stage B report")
    assert "| EC-004 | Applicability verdicts against the answer key | PASS |" in text
    assert "| EC-010 | Agent time per run | NOT TESTED |" in text
    assert "| EC-012 | Model cost per run | INCOMPLETE" in text
    assert "Stand-in run: no model call, so this measures nothing" in text
    assert "## Copy cases" not in text                          # that is a stage A section


def test_stage_a_and_b_reports_are_numbered_separately_and_never_overwritten(conn, settings,
                                                                           tmp_path):
    run_id = flow.to_g3(conn, settings)
    rep = stage_b.evaluate_stage_b(conn, run_id)
    first, _ = report.save_report(rep, tmp_path)
    second, _ = report.save_report(rep, tmp_path)
    assert (first.name, second.name) == ("stage-b-report-1.json", "stage-b-report-2.json")
    assert json.loads(first.read_text(encoding="utf-8")) == rep


def test_the_command_line_grades_both_stages_when_the_run_finished_stage_b(conn, settings, tmp_path,
                                                                          capsys):
    run_id = flow.to_g3(conn, settings)
    assert cli.main([run_id, "--out", str(tmp_path)]) == 0
    printed = capsys.readouterr().out
    assert "# Stage A report" in printed and "# Stage B report" in printed
    assert sorted(p.name for p in (tmp_path / run_id).iterdir()) == [
        "stage-a-report-1.json", "stage-a-report-1.md",
        "stage-b-report-1.json", "stage-b-report-1.md"]


def test_the_command_line_skips_stage_b_quietly_at_g1_but_not_when_asked_for_it(conn, settings,
                                                                               tmp_path, capsys):
    run_id = flow.start_to_g1(conn, settings)
    assert cli.main([run_id, "--out", str(tmp_path)]) == 0       # default: stage A, B skipped
    captured = capsys.readouterr()
    assert "# Stage A report" in captured.out and "Stage B skipped" in captured.err
    assert not list((tmp_path / run_id).glob("stage-b-*"))
    assert cli.main([run_id, "--stage", "b", "--out", str(tmp_path)]) == 2   # asked for: an error
    assert "Nothing to grade" in capsys.readouterr().err
