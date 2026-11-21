"""The Stage A report: its text, its saved files (never overwritten) and the command line."""

import json

import pytest

from backend.db.connection import connect, init_db
from backend.evaluation import __main__ as cli
from backend.evaluation import report as report_module
from backend.evaluation import stage_a
from tests import flow


@pytest.fixture
def prepared(settings, monkeypatch):
    """A database holding one finished stand-in stage A run, and the env pointing at it."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    monkeypatch.setenv("DATABASE_PATH", str(settings.database_path))
    monkeypatch.setenv("AGENTS_MODE", "stand_in")
    yield conn, run_id
    conn.close()


def test_the_text_states_the_stamp_the_misses_and_what_was_not_tested(prepared):
    conn, run_id = prepared
    text = report_module.render_markdown(stage_a.evaluate_stage_a(conn, run_id))
    assert "STAND-IN RUN: does not count towards the cycle" in text
    assert "Counts towards the evaluation cycle: **no**" in text
    assert "| EC-001 |" in text and "MISS" in text
    # A miss shows expected and actual, never just a count (EC-R3):
    assert "Fund is subject to Part II of the Law of 17 December 2010" in text
    assert "The undertaking is subject to Part II of the Law of 17 December 2010." in text
    assert "NOT TESTED: I-1 flagged as internal on a copy of OBL-02" in text
    assert "FOR THE OPERATOR" in text
    assert "One run only" in text and "3 of 3" in text
    assert "## Not in this slice" in text


def test_reports_are_saved_with_the_run_id_and_never_overwritten(prepared, tmp_path):
    conn, run_id = prepared
    report = stage_a.evaluate_stage_a(conn, run_id)
    first_json, _ = report_module.save_report(report, tmp_path)
    assert first_json == tmp_path / run_id / "stage-a-report-1.json"
    first_text = first_json.read_text(encoding="utf-8")
    assert json.loads(first_text) == report                       # nothing lost in the file

    second_json, _ = report_module.save_report(report, tmp_path)  # grading the run again
    assert second_json.name == "stage-a-report-2.json"
    assert first_json.read_text(encoding="utf-8") == first_text   # report 1 is untouched

    (tmp_path / run_id / "stage-a-report-3.json").write_text("someone else's file")
    third_json, third_md = report_module.save_report(report, tmp_path)
    assert third_json.name == "stage-a-report-4.json"             # skipped the taken number
    assert (tmp_path / run_id / "stage-a-report-3.json").read_text() == "someone else's file"
    assert third_md.name == "stage-a-report-4.md"


def test_the_command_line_prints_and_saves_and_a_miss_is_not_an_error(prepared, tmp_path, capsys):
    _, run_id = prepared
    assert cli.main([run_id, "--out", str(tmp_path)]) == 0
    printed = capsys.readouterr().out
    assert "# Stage A report" in printed and "MISS" in printed
    assert (tmp_path / run_id / "stage-a-report-1.md").exists()


def test_the_command_line_can_print_without_saving(prepared, tmp_path, capsys):
    _, run_id = prepared
    out = tmp_path / "reports"          # (tmp_path also holds the test database)
    assert cli.main([run_id, "--no-save", "--out", str(out)]) == 0
    assert not out.exists()


def test_the_command_line_says_when_there_is_nothing_to_grade(prepared, tmp_path, capsys):
    assert cli.main(["RUN-NOPE", "--out", str(tmp_path)]) == 2
    assert "Nothing to grade" in capsys.readouterr().err


def test_the_command_line_does_not_create_a_database_that_is_not_there(tmp_path, monkeypatch,
                                                                         capsys):
    missing = tmp_path / "nope.db"
    monkeypatch.setenv("DATABASE_PATH", str(missing))
    monkeypatch.setenv("AGENTS_MODE", "stand_in")
    assert cli.main(["RUN-X"]) == 2
    assert not missing.exists()
