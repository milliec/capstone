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


def _run_at(conn, settings, status, phase):
    run_id = _start(conn, settings)
    conn.execute("UPDATE runs SET status = ?, phase = ? WHERE run_id = ?", (status, phase, run_id))
    conn.commit()
    return run_id


def test_steps_follow_the_ux_stepper_table(settings):
    """V-3: the four stepper items for an active, a completed and an ended review."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    at_g1 = runs.get_run(conn, _run_at(conn, settings, "ACTIVE", "AT_G1"))
    assert [s["state"] for s in at_g1["steps"]] == ["Done", "Your turn", "Not started", "Not started"]
    assert [s["href"] is not None for s in at_g1["steps"]] == [True, True, False, False]
    assert [s["current"] for s in at_g1["steps"]] == [False, True, False, False]
    assert at_g1["steps"][1]["href"].endswith("/g1")

    done = runs.get_run(conn, _run_at(conn, settings, "COMPLETED", "AT_G3"))
    assert [s["state"] for s in done["steps"]] == ["Done"] * 4

    # An ended review keeps its phase (DL-46): stopped at AT_G2 means step 3.
    ended = runs.get_run(conn, _run_at(conn, settings, "ABANDONED", "AT_G2"))
    assert [s["state"] for s in ended["steps"]] == ["Done", "Done", "Ended", "Not started"]
    failed = runs.get_run(conn, _run_at(conn, settings, "FAILED", "A_RUNNING"))
    assert [s["state"] for s in failed["steps"]] == ["Failed", "Not started", "Not started", "Not started"]


def test_ended_failure_and_counts(settings):
    """V-5, V-6: counts, the abandon reason and time, and the failure details."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = _run_at(conn, settings, "ACTIVE", "AT_G1")
    from backend.stand_in import shell_data
    assert runs.get_run(conn, run_id)["counts"] == {
        "rules": len(shell_data.ROWS), "unsure": 1, "dates": len(shell_data.ENTRIES)}
    assert runs.get_run(conn, run_id)["ended"] is None

    runs.abandon_run(conn, run_id=run_id, run_version=1, reason="Wrong source.\nMore detail",
                     actor="specialist-1")
    run = runs.get_run(conn, run_id)
    assert run["ended"]["reason"] == "Wrong source.\nMore detail" and run["ended"]["at"]
    assert run["ended_because"] == "Wrong source."
    assert run["failure"] is None and run["published_at"] is None

    failed_id = _run_at(conn, settings, "ACTIVE", "A_RUNNING")
    from backend.services import stage_store
    failed = runs.get_run(conn, failed_id)
    stage_store.add_units(conn, failed, "A", [("DOC-1", "Source one")])
    stage_store.fail_stage(conn, failed, "A", "DOC-1", "demo failure")
    failure = runs.get_run(conn, failed_id)["failure"]
    assert failure["step"] == 1 and failure["step_name"] == "AI drafts the rules"
    assert failure["unit_label"] == "Source one"
    assert failure["reason_sentence"].startswith("This step failed on purpose")
