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


def test_units_carry_the_group_the_page_shows_them_under(settings):
    """V-4: the backend assigns the group; the page never works it out."""
    from backend.services import stage_store

    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = _start(conn, settings)
    run = runs.get_run(conn, run_id)
    stage_store.add_units(conn, run, "A", [("DOC-1", "Source one"), ("ROW-X-1", "A drafted rule")])
    stage_store.add_units(conn, run, "B", [("ROW-X-1", "Rule one")])
    stage_store.add_units(conn, run, "C", [("CALENDAR", "Calendar")])

    groups = {(u["stage"], u["unit_id"]): u["group"] for u in runs.list_units(conn, run_id)}
    assert groups == {("A", "DOC-1"): "drafting", ("A", "ROW-X-1"): "checking_drafts",
                      ("B", "ROW-X-1"): "applies", ("C", "CALENDAR"): "dates"}
