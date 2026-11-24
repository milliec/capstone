"""H-091 part 1: the two new failure reasons, `unexpected error` and `call limit` (sad.md DL-58). Tier 1.

This file holds what is true of the REASONS themselves, apart from the code that raises them:
  * a database made from schema.sql accepts both, and still refuses a made-up one;
  * each has its sentence (the words are the ones in sad.md and integration.md 3.4), and the review
    page's failure box and the "ended because" line show that sentence, never an error's message.
No model is called. The tests that make a stage RAISE these reasons come in the next two pull requests.
"""

import sqlite3

import pytest

from backend.db.connection import connect, init_db
from backend.services import runs, stage_store
from tests import flow

UNEXPECTED = "Something went wrong that the app did not expect, so this step was stopped and nothing from it was saved"
CALL_LIMIT = "The limit on real model calls for this kind of review was reached, so no further call was made"


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _failed_run(conn, settings, reason):
    """A run that failed in stage A with `reason`, built the way test_run_view_fields.py builds one."""
    run_id = flow.start_to_g1(conn, settings)          # any ACTIVE run will do; then put it back to A_RUNNING
    conn.execute("UPDATE runs SET phase = 'A_RUNNING' WHERE run_id = ?", (run_id,))
    conn.execute("DELETE FROM units WHERE run_id = ?", (run_id,))
    conn.commit()
    run = runs.get_run(conn, run_id)
    stage_store.add_units(conn, run, "A", [("DOC-1", "Source one")])
    assert stage_store.fail_stage(conn, run, "A", "DOC-1", reason) is True
    return run_id


@pytest.mark.parametrize("reason", ["unexpected error", "call limit"])
def test_schema_accepts_the_new_reasons(conn, settings, reason):
    run_id = _failed_run(conn, settings, reason)
    assert [u["failure_reason"] for u in runs.list_units(conn, run_id)] == [reason]


def test_schema_still_refuses_a_made_up_reason(conn, settings):
    with pytest.raises(sqlite3.IntegrityError):
        _failed_run(conn, settings, "banana")


@pytest.mark.parametrize("reason, sentence", [("unexpected error", UNEXPECTED), ("call limit", CALL_LIMIT)])
def test_the_page_shows_the_sentence_and_ended_because_repeats_it(conn, settings, reason, sentence):
    run = runs.get_run(conn, _failed_run(conn, settings, reason))
    assert run["failure"]["reason_sentence"] == sentence
    assert run["ended_because"] == sentence
