"""H-096 PR 1: `record_call` can label a trace line with an `eval_case` (DL-45, EC-R2).

The label marks a model call that belongs to an evaluation copy case (the altered quote, the I-1
copy, the injected paragraph) rather than to one of the run's units. The `trace.eval_case` column
and its CHECK already exist in the schema, so this PR adds no schema change.

Three things are tested:
  * a labelled call is stored with its label;
  * an ordinary call stores none (NULL), exactly as before;
  * a value outside the three allowed labels is refused by the column's CHECK.

No model and no key: the lines are made by hand, in a temporary database.
"""

import sqlite3

import pytest

from backend.db.connection import connect, init_db
from backend.services import runs, trace
from tests import flow


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


@pytest.fixture
def run(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    return runs.get_run(conn, run_id)


def _call(n: int = 1) -> trace.CallRecord:
    """A minimal call. `attempt_n` differs per line so the lines have distinct record keys."""
    return trace.CallRecord(
        step="check_conflicts", at="2026-11-24T10:00:00Z", prompt_version="pv", input_hash="h" * 64,
        raw_output="{}", parsed_output="[]", validation_error=None, duration_ms=1, attempt_n=n)


def _last_line(conn, run_id):
    return trace.list_trace(conn, run_id)[-1]


@pytest.mark.parametrize("label", ["altered_quote", "I-1", "injection"])
def test_a_labelled_call_is_stored_with_its_label(conn, run, label):
    trace.record_call(conn, run=run, stage="A", unit_id="COPY-1", call=_call(),
                      eval_case=label)
    assert _last_line(conn, run["run_id"])["eval_case"] == label


def test_an_ordinary_call_stores_no_label(conn, run):
    trace.record_call(conn, run=run, stage="A", unit_id="U-ORDINARY", call=_call())
    assert _last_line(conn, run["run_id"])["eval_case"] is None


def test_a_label_outside_the_three_is_refused_by_the_column(conn, run):
    before = len(trace.list_trace(conn, run["run_id"]))
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        trace.record_call(conn, run=run, stage="A", unit_id="COPY-X", call=_call(),
                          eval_case="made_up")
    # The refused call left nothing behind: no trace line, and the cost count did not move.
    assert len(trace.list_trace(conn, run["run_id"])) == before


def test_a_copy_case_call_is_never_late_even_when_the_run_waits_at_a_gate(conn, run):
    """The run is at G1, so an ordinary stage-A call written now is late. A copy-case call belongs to no
    stage and is not (PR 6): otherwise EC-010 would count it as time the run wasted."""
    trace.record_call(conn, run=run, stage="A", unit_id="U-ORDINARY", call=_call(1))
    trace.record_call(conn, run=run, stage="A", unit_id="COPY-1", call=_call(2), eval_case="I-1")
    ordinary, labelled = trace.list_trace(conn, run["run_id"])[-2:]
    assert (ordinary["late"], labelled["late"]) == (1, 0)
