"""The void rule (EC-R8) and the report for a run that did not finish (H-097, PR 5).

The rule was written before any evaluation run existed, so that it cannot be bent to discard an
unwelcome result. These tests pin it down word for word:
  * voided ONLY when the run is FAILED and EVERY failed unit's reason is `model service` or
    `stage time limit`;
  * every other reason (and an unknown cause) is a finding, never voided;
  * a voided run is re-run once, only with the operator's recorded decision; without it the report
    says the cycle has fewer than three runs and every criterion is INCOMPLETE;
  * a replacement that also fails for a model-service reason is a MISS, "model service", not re-run;
  * voided runs are listed with reasons and cost.

Safety (H-097 checks): no model, no fake server, no real database. Each test builds a tiny run in a
temporary SQLite file with the app's own schema, and reports are written to a temporary folder.
"""

import json

import pytest

from backend.db.connection import connect, init_db
from backend.evaluation import void_rule
from backend.evaluation.report import render_markdown
from backend.services import FUND_ID

# The nine failure reasons the units table allows (schema.sql), and which are model-service failures.
ALL_REASONS = ("model service", "stage time limit", "invalid output", "cost cap", "service restarted",
               "calendar generation", "demo failure", "unexpected error", "call limit")
VOIDABLE = {"model service", "stage time limit"}


@pytest.fixture
def conn(tmp_path):
    path = tmp_path / "t.db"
    init_db(path)
    connection = connect(path)
    yield connection
    connection.close()


def make_run(conn, run_id="RUN-1", status="FAILED", reasons=(), cost=0.0123, calls=3):
    conn.execute("INSERT INTO runs (run_id, fund_id, status, phase, agents_mode, started_by, started_at,"
                 " spend_activity, cost_so_far) VALUES (?, ?, ?, 'A_RUNNING', 'real', 'specialist-eval',"
                 " 'now', 'evaluation', ?)", (run_id, FUND_ID, status, cost))
    for i, reason in enumerate(reasons):
        conn.execute("INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status,"
                     " attempts, failure_reason) VALUES (?, 'A', 1, ?, ?, ?, 'failed', 2, ?)",
                     (run_id, f"U{i}", FUND_ID, f"unit {i}", reason))
    for i in range(calls):
        conn.execute("INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at,"
                     " prompt_version, input_hash, spend_activity) VALUES (?, ?, 'extract_rows', 1, ?, 1,"
                     " 'now', 'v', 'h', 'evaluation')", (run_id, FUND_ID, f"U{i}"))
    conn.commit()
    return run_id


# --- The classification --------------------------------------------------------------------------------

@pytest.mark.parametrize("reason", sorted(VOIDABLE))
def test_a_failed_run_whose_only_reason_is_a_model_service_failure_is_voided(conn, reason):
    outcome = void_rule.classify(conn, make_run(conn, reasons=[reason]))
    assert outcome.kind == void_rule.VOIDED and outcome.reasons == (reason,)


def test_every_failed_unit_must_be_a_model_service_failure(conn):
    outcome = void_rule.classify(conn, make_run(conn, reasons=["model service", "stage time limit", "model service"]))
    assert outcome.kind == void_rule.VOIDED and outcome.failed_units == 3


@pytest.mark.parametrize("reason", [r for r in ALL_REASONS if r not in VOIDABLE])
def test_no_other_reason_ever_voids_a_run(conn, reason):
    outcome = void_rule.classify(conn, make_run(conn, reasons=[reason]))
    assert outcome.kind == void_rule.FINDING and reason in outcome.why


@pytest.mark.parametrize("other", [r for r in ALL_REASONS if r not in VOIDABLE])
def test_one_unit_with_another_reason_stops_the_whole_run_being_voided(conn, other):
    outcome = void_rule.classify(conn, make_run(conn, reasons=["model service", other, "model service"]))
    assert outcome.kind == void_rule.FINDING


def test_a_failed_run_with_no_failed_unit_recorded_is_not_voided(conn):
    outcome = void_rule.classify(conn, make_run(conn, reasons=[]))
    assert outcome.kind == void_rule.FINDING and "cause is unknown" in outcome.why


def test_a_failed_unit_with_no_reason_recorded_is_not_voided(conn):
    run_id = make_run(conn, reasons=["model service"])
    conn.execute("INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status,"
                 " attempts) VALUES (?, 'B', 1, 'X', ?, 'x', 'failed', 1)", (run_id, FUND_ID))
    conn.commit()
    assert void_rule.classify(conn, run_id).kind == void_rule.FINDING


def test_failed_units_from_every_stage_attempt_count(conn):
    run_id = make_run(conn, reasons=["model service"])
    conn.execute("INSERT INTO units (run_id, stage, stage_attempt, unit_id, fund_id, label, status,"
                 " attempts, failure_reason) VALUES (?, 'A', 2, 'U0', ?, 'x', 'failed', 1, 'invalid output')",
                 (run_id, FUND_ID))
    conn.commit()
    assert void_rule.classify(conn, run_id).kind == void_rule.FINDING      # the stricter reading


@pytest.mark.parametrize("status,kind", [("COMPLETED", "completed"), ("ACTIVE", "active"),
                                         ("ABANDONED", "abandoned"), ("DECLINED", "abandoned")])
def test_only_a_failed_run_can_be_voided(conn, status, kind):
    outcome = void_rule.classify(conn, make_run(conn, status=status, reasons=["model service"]))
    assert outcome.kind == kind


def test_a_run_that_does_not_exist_is_an_error_not_a_void(conn):
    with pytest.raises(LookupError):
        void_rule.classify(conn, "RUN-NOPE")


def test_the_outcome_carries_the_run_cost_and_the_number_of_calls(conn):
    outcome = void_rule.classify(conn, make_run(conn, reasons=["model service"], cost=0.5, calls=4))
    assert (outcome.cost_usd, outcome.calls) == (0.5, 4)


# --- What follows ------------------------------------------------------------------------------------

def voided(conn, run_id="RUN-V"):
    return void_rule.classify(conn, make_run(conn, run_id, reasons=["model service"]))


def test_a_voided_run_is_not_replaced_without_a_recorded_decision(conn):
    step = void_rule.next_step(voided(conn))
    assert step.action == void_rule.NEEDS_DECISION and step.criteria_status == "incomplete"
    assert "fewer than three runs" in step.sentence and "not a pass" in step.sentence
    assert "63" in step.sentence


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_a_blank_decision_is_no_decision(conn, blank):
    assert void_rule.next_step(voided(conn), decision=blank).action == void_rule.NEEDS_DECISION


def test_a_recorded_decision_allows_exactly_one_rerun(conn):
    step = void_rule.next_step(voided(conn), decision="D-9: spend 21 calls")
    assert step.action == void_rule.RE_RUN and "D-9: spend 21 calls" in step.sentence


def test_a_replacement_that_fails_again_is_a_miss_with_reason_model_service_and_is_not_rerun(conn):
    step = void_rule.next_step(voided(conn), is_replacement=True, decision="D-9")
    assert (step.action, step.criteria_status, step.miss_reason) == (void_rule.MISS, "miss", "model service")
    assert "not re-run again" in step.sentence


def test_a_replacement_is_never_rerun_even_for_a_stage_time_limit(conn):
    outcome = void_rule.classify(conn, make_run(conn, "RUN-T", reasons=["stage time limit"]))
    assert void_rule.next_step(outcome, is_replacement=True, decision="D-9").miss_reason == "model service"


def test_a_finding_is_a_miss_with_its_own_reason_and_is_never_rerun(conn):
    outcome = void_rule.classify(conn, make_run(conn, "RUN-F", reasons=["invalid output"]))
    step = void_rule.next_step(outcome, decision="D-9")            # a decision cannot turn a finding into a void
    assert (step.action, step.criteria_status) == (void_rule.NOTHING, "miss")


def test_a_finished_run_needs_nothing(conn):
    step = void_rule.next_step(void_rule.classify(conn, make_run(conn, status="COMPLETED")))
    assert step.action == void_rule.NOTHING and step.criteria_status is None


# --- The cycle: voided runs are listed with reasons and cost -----------------------------------------

def test_the_cycle_lists_each_voided_run_with_its_reasons_and_cost(conn):
    outcomes = [void_rule.classify(conn, make_run(conn, "RUN-1", status="COMPLETED", cost=0.1)),
                void_rule.classify(conn, make_run(conn, "RUN-2", reasons=["model service"], cost=0.25)),
                void_rule.classify(conn, make_run(conn, "RUN-3", reasons=["stage time limit"], cost=0.5))]
    note = void_rule.cycle_note(outcomes)
    assert [o.run_id for o in note.voided] == ["RUN-2", "RUN-3"]
    assert note.voided_cost_usd == pytest.approx(0.75)               # voided runs count towards spend
    assert note.runs_in_cycle == 1 and "fewer than three runs" in note.sentence


def test_three_counted_runs_make_a_full_cycle(conn):
    outcomes = [void_rule.classify(conn, make_run(conn, f"RUN-{n}", status="COMPLETED")) for n in (1, 2, 3)]
    note = void_rule.cycle_note(outcomes)
    assert note.runs_in_cycle == 3 and "fewer" not in note.sentence and note.voided == []


# --- The report -----------------------------------------------------------------------------------------

def test_the_report_of_a_voided_run_marks_every_model_criterion_incomplete_never_a_pass(conn):
    report = void_rule.evaluate_failed_run(conn, make_run(conn, reasons=["model service"]))
    assert report["outcome"] == "voided" and report["next_step"] == "needs_decision"
    assert [c["id"] for c in report["criteria"]] == list(void_rule.MODEL_CRITERIA)
    assert {c["status"] for c in report["criteria"]} == {"incomplete"}
    assert report["counts_for_cycle"] is False and report["cost_usd"] == pytest.approx(0.0123)


def test_the_report_of_a_finding_marks_every_model_criterion_a_miss_with_the_reason(conn):
    report = void_rule.evaluate_failed_run(conn, make_run(conn, reasons=["cost cap"]))
    assert {c["status"] for c in report["criteria"]} == {"miss"} and report["miss_reason"] == "cost cap"
    assert report["counts_for_cycle"] is True                        # a finding is a result, not a discard


def test_the_report_of_a_failed_replacement_is_a_miss_for_model_service(conn):
    report = void_rule.evaluate_failed_run(conn, make_run(conn, reasons=["stage time limit"]),
                                           is_replacement=True, decision="D-9")
    assert report["miss_reason"] == "model service" and {c["status"] for c in report["criteria"]} == {"miss"}


def test_a_finished_run_report_has_no_criteria_to_mark(conn):
    report = void_rule.evaluate_failed_run(conn, make_run(conn, status="COMPLETED"))
    assert report["criteria"] == []


def test_the_markdown_names_the_outcome_the_reasons_the_cost_and_what_follows(conn):
    text = render_markdown(void_rule.evaluate_failed_run(conn, make_run(conn, reasons=["model service"])))
    for word in ("VOIDED", "model service", "US$0.0123", "fewer than three runs", "INCOMPLETE"):
        assert word in text


# --- The command --------------------------------------------------------------------------------------

@pytest.fixture
def command(tmp_path, monkeypatch):
    path = tmp_path / "app.db"
    init_db(path)
    connection = connect(path)
    make_run(connection, "RUN-C", reasons=["model service"])
    connection.close()
    monkeypatch.setenv("DATABASE_PATH", str(path))
    monkeypatch.setenv("AGENTS_MODE", "stand_in")
    return tmp_path / "logs"


def test_the_command_prints_and_saves_a_report_in_the_folder_it_is_given(command):
    lines = []
    assert void_rule.main(["RUN-C", "--out", str(command)], out=lines.append) == 0
    saved = json.loads((command / "RUN-C" / "failed-run-report-1.json").read_text())
    assert saved["outcome"] == "voided" and "VOIDED" in lines[0]


def test_the_command_never_overwrites_an_earlier_report(command):
    void_rule.main(["RUN-C", "--out", str(command)], out=lambda _: None)
    void_rule.main(["RUN-C", "--out", str(command), "--decision", "D-9"], out=lambda _: None)
    assert sorted(p.name for p in (command / "RUN-C").glob("*.json")) == \
        ["failed-run-report-1.json", "failed-run-report-2.json"]


def test_the_command_says_so_when_the_run_does_not_exist(command, capsys):
    assert void_rule.main(["RUN-NOPE", "--out", str(command)], out=lambda _: None) == 2
    assert "There is no run RUN-NOPE" in capsys.readouterr().err


def test_the_command_does_not_create_a_database_that_is_not_there(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "missing.db"))
    assert void_rule.main(["RUN-C", "--out", str(tmp_path)], out=lambda _: None) == 2
    assert not (tmp_path / "missing.db").exists()


def test_the_cli_routes_the_word_void_to_the_rule(command):
    from backend.evaluation import __main__ as cli
    assert cli.main(["void", "RUN-C", "--no-save"]) == 0
