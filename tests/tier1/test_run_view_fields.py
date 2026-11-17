"""H-036 V-1, V-2, V-7: the fields every run carries, so no page works them out (ux.md §1.2)."""

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, runs


def _start(conn, settings):
    # Test setup: close any earlier review directly (B2 allows only one ACTIVE review), and use a
    # no-op `schedule`, because these tests look at the run row and not at stage A.
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")
    conn.commit()
    return runs.start_run(conn, settings, lambda *a, **k: None, fund_id=FUND_ID,
                          started_by="specialist-1", demo_planted_row=False,
                          demo_fail_step1=False)


def test_runs_are_numbered_oldest_first_and_carry_tone_and_starter(settings):
    init_db(settings.database_path)   # creates the tables in the temporary test database
    conn = connect(settings.database_path)
    first = _start(conn, settings)
    conn.execute("UPDATE runs SET phase = 'AT_G1' WHERE run_id = ?", (first,))   # a gate: abandon ok
    conn.commit()
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


def test_g1_view_fields_and_decided_line(settings):
    """V-8: the rows carry status, evidence and the decided line; the view carries the stage."""
    from backend.services import decisions

    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run = runs.get_run(conn, _run_at(conn, settings, "ACTIVE", "AT_G1"))
    view = decisions.get_g1_view(conn, run)
    assert view["stage"] == "at" and view["summary"] == {"flags": 0}
    assert len(view["unused_paragraphs"]) == 2
    first, silent = view["rows"][0], view["rows"][1]
    assert first["status"] == "To decide" and first["status_tone"] == "action"
    assert first["quote_check"] == {"passed": True} and first["flags"] == [] and first["decided"] is None
    assert first["needs_who_files"] is True and silent["needs_who_files"] is False
    assert first["filing_parties"][-1] == ["not known", "Not known"]

    decisions.decide_row(conn, row_id=first["row_id"], version=1, decision="approve",
                         business_day_rule="roll_forward", who_files="AIFM",
                         approve_reason="Looks right", reject_reason=None, actor="specialist-1")
    decisions.decide_row(conn, row_id=silent["row_id"], version=1, decision="reject",
                         business_day_rule=None, who_files=None, approve_reason=None,
                         reject_reason="Wrong quote", actor="specialist-1")
    rows = {r["row_id"]: r for r in decisions.get_g1_view(conn, run)["rows"]}
    a, b = rows[first["row_id"]], rows[silent["row_id"]]
    assert (a["status"], a["status_tone"]) == ("Approved", "success")
    assert a["decided"]["by_label"] == "Compliance specialist (mock)"
    assert a["decided"]["business_day_rule"] == "roll_forward"
    assert a["decided"]["who_files"] == "AIFM" and a["decided"]["reason"] == "Looks right"
    assert (b["status"], b["status_tone"]) == ("Rejected", "problem")
    assert b["decided"]["reason"] == "Wrong quote" and b["decided"]["business_day_rule"] is None


def test_page_stage_before_at_after_and_ended(settings):
    """V-8 to V-10 `stage`: forms only at the gate; an ended review is read-only."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    for status, phase, g1, g3 in [("ACTIVE", "A_RUNNING", "before", "before"),
                                  ("ACTIVE", "AT_G1", "at", "before"),
                                  ("ACTIVE", "AT_G3", "after", "at"),
                                  ("COMPLETED", "AT_G3", "after", "after"),
                                  ("ABANDONED", "AT_G1", "after", "ended_before"),
                                  ("FAILED", "A_RUNNING", "ended_before", "ended_before")]:
        run = runs.get_run(conn, _run_at(conn, settings, status, phase))
        assert (runs.page_stage(run, "g1"), runs.page_stage(run, "g3")) == (g1, g3), (status, phase)


def test_g2_view_fields_and_decided_outcome(settings):
    """V-9: facts, approved rule, missing fact, overrule value, and the decided outcome words."""
    from backend.services import decisions

    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run = runs.get_run(conn, _run_at(conn, settings, "ACTIVE", "AT_G2"))
    view = decisions.get_g2_view(conn, run)
    assert view["stage"] == "at"
    applies, unsure, no = view["verdicts"]
    assert applies["cited_facts"][0]["fact_id"] == "FACT-STUB-1" and applies["decided"] is None
    assert applies["approved_rule"]["paragraph_id"] == "SRC-STUB-P1" and applies["approved_rule"]["quote"]
    assert (applies["overrule_value"], no["overrule_value"]) == ("does_not_apply", "applies")
    assert unsure["overrule_value"] is None and unsure["missing_fact"]
    assert applies["missing_fact"] is None

    for v, decision, value, reason in [(applies, "override", "does_not_apply", "Not for this fund"),
                                       (unsure, "decide", "applies", "I checked")]:
        decisions.decide_verdict(
            conn, verdict_id=v["verdict_id"], version=1, decision=decision, value=value,
            confirm_reason=None, override_reason=reason if decision == "override" else None,
            decide_reason=reason if decision == "decide" else None, actor="specialist-1")
    after = {v["verdict_id"]: v for v in decisions.get_g2_view(conn, run)["verdicts"]}
    d1, d2 = after[applies["verdict_id"]]["decided"], after[unsure["verdict_id"]]["decided"]
    assert d1["outcome"] == "Overruled: doesn't apply" and d1["reason"] == "Not for this fund"
    assert d2["outcome"] == "Added, marked 'May not be required'" and d2["reason"] == "I checked"
    assert d1["by_label"] == "Compliance specialist (mock)" and d1["at"]


def test_g3_view_publish_outcome_and_previous_publication(settings):
    """V-10, V-11, and V-6 `published_at`: lists, entry words, outcome, previous publication."""
    from backend.services import calendar, decisions, publishing, stage_store

    init_db(settings.database_path)
    conn = connect(settings.database_path)

    def to_g3(run_id):
        stage_store.finish_stage(conn, runs.get_run(conn, run_id), "C")   # makes the calendar
        return runs.get_run(conn, run_id)

    first = to_g3(_run_at(conn, settings, "ACTIVE", "C_RUNNING"))
    row3 = f"ROW-{first['run_id']}-3"
    decisions.decide_row(conn, row_id=row3, version=1, decision="reject", business_day_rule=None,
                         who_files=None, approve_reason=None, reject_reason="Wrong quote",
                         actor="specialist-1")
    decisions.decide_row(conn, row_id=f"ROW-{first['run_id']}-1", version=1, decision="approve",
                         business_day_rule="roll_forward", who_files="Auditor",
                         approve_reason=None, reject_reason=None, actor="specialist-1")
    view = calendar.get_g3_view(conn, first)
    assert view["stage"] == "at" and view["outcome"] is None and view["previous_publication_at"] is None
    assert view["rejected_rows"] == [{"row_id": row3, "label": "Stand-in rule 3: monthly report",
                                      "reason": "Wrong quote", "is_demo": False}]
    assert view["rejected_row_ids"] == [row3] and len(view["uncited_paragraph_ids"]) == 2
    e1, e2 = view["entries"]
    assert e1["who_files_label"] == "Auditor" and e1["marks"]["moved"] is None
    assert e1["why"] and e1["source_paragraph_id"] == "SRC-STUB-P1" and e1["recipient_name"]
    assert e2["marks"]["moved"] == {"from_date": "2027-04-18", "to_date": "2027-04-19",
                                    "direction": "following working day"}

    publishing.publish_calendar(conn, calendar_id=view["calendar_id"], run_version=1,
                                acknowledged=True, rejected_row_ids=[row3],
                                uncited_paragraph_ids=[], actor="specialist-1")
    published = runs.get_run(conn, first["run_id"])
    assert published["status"] == "COMPLETED" and published["published_at"]
    after = calendar.get_g3_view(conn, published)
    assert after["stage"] == "after" and after["outcome"]["at"] == published["published_at"]
    live = calendar.get_published_calendar(conn, published["fund_id"])
    assert live["entries"][0]["quote"] and live["entries"][0]["source_document"]

    second = to_g3(_run_at(conn, settings, "ACTIVE", "C_RUNNING"))
    assert calendar.get_g3_view(conn, second)["previous_publication_at"] == published["published_at"]
    publishing.decline_calendar(conn, calendar_id=f"CAL-{second['run_id']}", run_version=1,
                                decline_reason="Dates look off", actor="specialist-1")
    declined = calendar.get_g3_view(conn, runs.get_run(conn, second["run_id"]))
    assert declined["outcome"]["reason"] == "Dates look off" and declined["outcome"]["at"]
