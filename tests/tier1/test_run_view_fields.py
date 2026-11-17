"""H-036 V-1, V-2, V-7: the fields every run carries, so no page works them out (ux.md §1.2)."""

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, runs


def _start(conn, settings):
    # schedule is a no-op: we only look at the run row, not at stage A
    return runs.start_run(conn, settings, lambda *a, **k: None, fund_id=FUND_ID,
                          started_by="specialist-1", demo_planted_row=False,
                          demo_fail_step1=False)


def test_runs_are_numbered_oldest_first_and_carry_tone_and_starter(settings):
    init_db(settings.database_path)   # creates the tables in the temporary test database
    conn = connect(settings.database_path)
    first = _start(conn, settings)
    runs.abandon_run(conn, run_id=first, run_version=1, reason="x", actor="specialist-1")
    second = _start(conn, settings)

    assert runs.get_run(conn, first)["review_number"] == 1
    assert runs.get_run(conn, second)["review_number"] == 2
    assert runs.get_run(conn, first)["status_tone"] == "neutral"   # abandoned
    assert runs.get_run(conn, second)["status_tone"] == "info"     # AI is drafting
    assert runs.get_run(conn, second)["started_by_label"] == "Compliance specialist (mock)"
