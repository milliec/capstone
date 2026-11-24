"""T-D4-1 (Tier 2): the trace export of an evaluation run (sad.md D4, H-097 PR 2).

The rule: every evaluation run exports its trace to `project-context/2.build/logs/<run_id>/`, one
record per model call attempt, secrets removed. With the export switched off or deleted the run is
reported failed, and the report says why. With it present, it matches the trace store.

How these tests stay safe:
  * The run is made in REAL mode against the fake OpenAI (tests/fake_openai.py): a server on this
    machine, the dummy key `test-key-not-a-real-key`, a temporary database. No real call.
  * Every export goes to a temporary folder (`tmp_path`), never to `project-context/2.build/logs/`.
  * The trace table is append-only, so a test that needs a line with a secret in it ADDS a line, the
    way the app does. Nothing is edited.
"""

import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.db.connection import connect
from backend.evaluation import __main__ as cli
from backend.evaluation import trace_export
from backend.evaluation.report import DEFAULT_OUT
from backend.evaluation.stage_a import NotGradable
from backend.main import create_app
from backend.services import FUND_ID, runs
from backend.settings import load_settings
from tests.fake_openai import TEST_API_KEY
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key

# A made-up key in the shape real keys have. It is not a real key.
LOOKS_LIKE_A_KEY = "sk-proj-AAAAbbbbCCCCdddd1234567890"


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    from backend.runtime import crews
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def real_settings(tmp_path, as_openai):
    as_openai.answer_with(the_answer_key)
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": MODELS["extract"], "LLM_MODEL_VERIFY": MODELS["verify"],
        "LLM_MODEL_JUDGE": MODELS["judge"], "SESSION_SECRET": "test-only",
        "DATABASE_PATH": str(tmp_path / "real.db")})


@pytest.fixture
def run_id(real_settings):
    """A real-mode run (against the fake) that has made its stage A calls: 11 trace lines."""
    client = TestClient(create_app(real_settings))
    client.post("/sign-in", data={"identity_id": "specialist-1"})
    assert client.post("/specialist/runs", data={}, follow_redirects=False).status_code == 303
    conn = connect(real_settings.database_path)
    try:
        return runs.list_runs(conn, FUND_ID)[0]["run_id"]
    finally:
        conn.close()


@pytest.fixture
def conn(real_settings, run_id):
    connection = connect(real_settings.database_path)
    yield connection
    connection.close()


@pytest.fixture
def out(tmp_path):
    return tmp_path / "logs"


def add_line_with_secrets(conn, run_id):
    """One more trace line whose text carries two secrets, as a provider's error text might."""
    conn.execute(
        "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
        "prompt_version, input_hash, raw_output, provider_error) "
        "VALUES (?, ?, 'extract_rows', 1, 'SRC-SECRET', 1, 'now', 'v', 'h', ?, ?)",
        (run_id, FUND_ID, f"Incorrect API key provided: {TEST_API_KEY}.",
         f"401 Authorization: Bearer {LOOKS_LIKE_A_KEY}"))
    conn.commit()


def exported_lines(out, run_id):
    text = (out / run_id / "trace.jsonl").read_text()
    return [json.loads(line) for line in text.splitlines()]


# --- With the export present: one record per attempt, matching the store ------------------------

def test_the_export_holds_one_record_per_model_call_attempt(conn, run_id, out, as_openai):
    stored = conn.execute("SELECT COUNT(*) FROM trace WHERE run_id = ?", (run_id,)).fetchone()[0]
    assert stored == len(as_openai.requests) == 11           # 5 extractions + 6 verifications

    result = trace_export.export_trace(conn, run_id, out)

    assert result.exported and result.records == stored
    records = exported_lines(out, run_id)
    assert len(records) == stored
    keys = {(r["step"], r["stage_attempt"], r["unit_id"], r["attempt_n"]) for r in records}
    assert len(keys) == stored                               # no record twice
    assert {r["run_id"] for r in records} == {run_id}
    assert {"raw_output", "parsed_output", "cost_usd", "request_path", "eval_case", "late"} <= set(records[0])
    assert trace_export.check_export(conn, run_id, out).ok


def test_the_export_matches_the_trace_store_line_by_line(conn, run_id, out):
    trace_export.export_trace(conn, run_id, out)
    stored = [dict(r) for r in conn.execute("SELECT * FROM trace WHERE run_id = ? ORDER BY trace_id",
                                            (run_id,))]
    assert exported_lines(out, run_id) == stored             # no secret here yet, so identical


def test_exporting_changes_nothing_in_the_database(conn, run_id, out):
    before = conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0], \
        conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    trace_export.export_trace(conn, run_id, out)
    after = conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0], \
        conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    assert after == before


# --- Secrets removed ----------------------------------------------------------------------------

def test_secrets_are_removed_from_every_exported_file(conn, run_id, out):
    add_line_with_secrets(conn, run_id)
    trace_export.export_trace(conn, run_id, out, secrets=[TEST_API_KEY])

    for path in (out / run_id).iterdir():
        text = path.read_text()
        assert TEST_API_KEY not in text and LOOKS_LIKE_A_KEY not in text, path.name
        assert not re.search(r"sk-[A-Za-z0-9_-]{8,}", text), path.name
    line = next(r for r in exported_lines(out, run_id) if r["unit_id"] == "SRC-SECRET")
    assert "[removed]" in line["raw_output"] and "[removed]" in line["provider_error"]
    assert "Incorrect API key provided" in line["raw_output"]       # only the secret goes, not the text


def test_a_removed_secret_still_leaves_a_record_that_matches_the_store(conn, run_id, out):
    add_line_with_secrets(conn, run_id)
    trace_export.export_trace(conn, run_id, out, secrets=[TEST_API_KEY])
    assert trace_export.check_export(conn, run_id, out).ok          # same count, same keys


# --- Switched off or deleted: the run is reported failed, and says why --------------------------

def test_with_the_export_switched_off_nothing_is_written_and_the_run_is_reported_failed(
        conn, run_id, out):
    result = trace_export.export_trace(conn, run_id, out, enabled=False)

    assert not result.exported and "switched off" in result.why
    assert not (out / run_id).exists()
    check = trace_export.check_export(conn, run_id, out)
    assert not check.ok and check.failed
    assert "trace export" in check.why and "missing" in check.why and run_id in check.why


def test_with_the_export_deleted_the_run_is_reported_failed(conn, run_id, out):
    trace_export.export_trace(conn, run_id, out)
    (out / run_id / "trace.jsonl").unlink()
    check = trace_export.check_export(conn, run_id, out)
    assert not check.ok and "missing" in check.why


def test_an_export_that_lost_a_record_is_reported_failed_with_the_counts(conn, run_id, out):
    trace_export.export_trace(conn, run_id, out)
    path = out / run_id / "trace.jsonl"
    path.write_text("\n".join(path.read_text().splitlines()[:-1]) + "\n")
    check = trace_export.check_export(conn, run_id, out)
    assert not check.ok and "10" in check.why and "11" in check.why


def test_an_export_with_a_record_that_is_not_in_the_store_is_reported_failed(conn, run_id, out):
    trace_export.export_trace(conn, run_id, out)
    path = out / run_id / "trace.jsonl"
    lines = path.read_text().splitlines()
    forged = json.loads(lines[0])
    forged["unit_id"] = "SRC-NOT-IN-THE-STORE"
    path.write_text("\n".join([json.dumps(forged)] + lines[1:]) + "\n")
    check = trace_export.check_export(conn, run_id, out)
    assert not check.ok and "does not match" in check.why


def test_a_new_trace_line_after_the_export_makes_the_check_fail(conn, run_id, out):
    trace_export.export_trace(conn, run_id, out)
    add_line_with_secrets(conn, run_id)                      # the store now has 12
    check = trace_export.check_export(conn, run_id, out)
    assert not check.ok and "11" in check.why and "12" in check.why


def test_an_unknown_run_cannot_be_exported_or_checked(conn, out):
    with pytest.raises(NotGradable):
        trace_export.export_trace(conn, "RUN-NOPE", out)
    with pytest.raises(NotGradable):
        trace_export.check_export(conn, "RUN-NOPE", out)


# --- The command --------------------------------------------------------------------------------

def test_the_command_writes_and_checks_the_export(real_settings, run_id, out, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_PATH", str(real_settings.database_path))
    monkeypatch.setenv("OPENAI_API_KEY", TEST_API_KEY)
    code = cli.main(["export", run_id, "--out", str(out)])
    printed = capsys.readouterr().out
    assert code == 0 and "11 records" in printed and (out / run_id / "trace.jsonl").exists()


def test_the_command_with_the_export_off_exits_1_and_says_why(
        real_settings, run_id, out, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_PATH", str(real_settings.database_path))
    code = cli.main(["export", run_id, "--out", str(out), "--off"])
    captured = capsys.readouterr()
    assert code == 1 and "switched off" in captured.err and not (out / run_id).exists()


def test_the_command_for_an_unknown_run_exits_2(real_settings, run_id, out, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_PATH", str(real_settings.database_path))
    assert cli.main(["export", "RUN-NOPE", "--out", str(out)]) == 2
    assert "RUN-NOPE" in capsys.readouterr().err


def test_the_command_still_grades_a_run_with_the_old_form(real_settings, run_id, monkeypatch, capsys):
    """`python -m backend.evaluation RUN-ID` is unchanged by the new `export` word."""
    monkeypatch.setenv("DATABASE_PATH", str(real_settings.database_path))
    code = cli.main([run_id, "--stage", "a", "--no-save"])
    assert code == 0 and "Stage A report" in capsys.readouterr().out


# --- Nothing here touches the real logs folder --------------------------------------------------

def test_the_default_folder_is_the_real_logs_folder_and_these_tests_never_use_it(out):
    assert DEFAULT_OUT.parts[-3:] == ("project-context", "2.build", "logs")
    assert DEFAULT_OUT not in out.parents and out != DEFAULT_OUT
    assert isinstance(DEFAULT_OUT, Path)
