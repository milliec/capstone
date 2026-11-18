"""H-036 V-1, V-2, V-7: the fields every run carries, so no page works them out (ux.md §1.2)."""

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, runs
from tests import flow


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
    # Counted from what the stages stored (B3 step 5): 6 rules, 1 "can't tell", and stage C's
    # 3 placeholder dates (B4 replaces them).
    at_g3 = flow.to_g3(conn, settings)
    assert runs.get_run(conn, at_g3)["counts"] == {"rules": 6, "unsure": 1, "dates": 3}
    run_id = _run_at(conn, settings, "ACTIVE", "AT_G1")
    assert runs.get_run(conn, run_id)["counts"] == {"rules": 0, "unsure": 0, "dates": 0}
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
    run_id = flow.start_to_g1(conn, settings)
    run = runs.get_run(conn, run_id)
    view = decisions.get_g1_view(conn, run)
    assert view["stage"] == "at" and view["summary"] == {"flags": 1}
    assert [p["paragraph_id"] for p in view["unused_paragraphs"]] == \
        ["SRC-CSSF15627-P1", "SRC-CSSF15627-P3", "SRC-UCILAW-P1", "SRC-CNMV-P2",
         "SRC-PRACT-P1", "SRC-PRACT-P2", "SRC-PRACT-P3"]
    first, second, third = view["rows"][0], view["rows"][1], view["rows"][2]
    assert first["status"] == "To decide" and first["status_tone"] == "action"
    assert first["quote_check"] == {"passed": True} and first["flags"] == [] and first["decided"] is None
    assert first["needs_who_files"] is False and second["needs_who_files"] is True
    assert first["filing_parties"][-1] == ["not known", "Not known"]
    assert first["paragraph"]["document"] == "CSSF Circular 15/627"
    # Codes become words (B3 step 5), and the recipient's name comes from the config.
    assert (first["frequency"], first["anchor"], first["offset"], first["recipient_name"]) == \
        ("monthly", "month end", "10 calendar days", "CSSF")
    assert third["has_flag"] and third["flags"][0]["other_paragraph_id"] == "SRC-PRACT-P1"

    flow.approve_rule(conn, run_id, 2, who="AIFM")
    flow.reject_rule(conn, run_id, 1, "Wrong quote")
    rows = {r["n"]: r for r in decisions.get_g1_view(conn, run)["rows"]}
    a, b = rows[2], rows[1]
    assert (a["status"], a["status_tone"]) == ("Approved", "success")
    assert a["decided"]["by_label"] == "Compliance specialist (mock)"
    assert a["decided"]["business_day_rule"] == "roll_forward" and a["decided"]["who_files"] == "AIFM"
    assert (b["status"], b["status_tone"]) == ("Rejected", "problem")
    assert b["decided"]["reason"] == "Wrong quote" and b["decided"]["business_day_rule"] is None
    # A rejected rule stops using its paragraph, so the paragraph joins the unused list.
    assert "SRC-CSSF15627-P2" in [p["paragraph_id"]
                                  for p in decisions.get_g1_view(conn, run)["unused_paragraphs"]]


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
    run_id = flow.start_to_g1(conn, settings)
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    run = runs.get_run(conn, run_id)
    view = decisions.get_g2_view(conn, run)
    assert view["stage"] == "at"
    by_n = {v["n"]: v for v in view["verdicts"]}
    applies, unsure, no = by_n[1], by_n[flow.UNSURE_N], by_n[flow.DOES_NOT_APPLY_N]
    # Each cited fact shows its text and value from the fund profile (B3 step 5).
    assert applies["cited_facts"] == [{"fact_id": "FACT-01", "value": "Yes",
                                       "label": "Subject to Part II of the Law of 17 December 2010"}]
    assert applies["decided"] is None
    assert applies["approved_rule"]["paragraph_id"] == "SRC-CSSF15627-P2" and applies["approved_rule"]["quote"]
    assert (applies["overrule_value"], no["overrule_value"]) == ("does_not_apply", "applies")
    assert unsure["overrule_value"] is None
    assert unsure["missing_fact"] == "Whether the fund is registered with the CNMV for marketing in Spain."
    assert applies["missing_fact"] is None

    flow.answer(conn, run_id, 1, "override", "does_not_apply", "Not for this fund")
    flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "I checked")
    after = {v["n"]: v for v in decisions.get_g2_view(conn, run)["verdicts"]}
    d1, d2 = after[1]["decided"], after[flow.UNSURE_N]["decided"]
    assert d1["outcome"] == "Overruled: doesn't apply" and d1["reason"] == "Not for this fund"
    assert d2["outcome"] == "Added, marked 'May not be required'" and d2["reason"] == "I checked"
    assert d1["by_label"] == "Compliance specialist (mock)" and d1["at"]


def test_g3_view_publish_outcome_and_previous_publication(settings):
    """V-10, V-11, and V-6 `published_at`: lists, entry words, outcome, previous publication."""
    from backend.services import calendar, publishing

    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    flow.approve_rule(conn, run_id, 1)
    flow.approve_rule(conn, run_id, 2, who="Auditor")
    flow.reject_rule(conn, run_id, 3, "Wrong quote")
    for n in (4, 5, 6):
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    for n in (1, 2, 5):
        flow.answer(conn, run_id, n, "confirm", "applies")
    flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "I checked")
    flow.answer(conn, run_id, flow.DOES_NOT_APPLY_N, "confirm", "does_not_apply")
    flow.finish_g2(conn, settings, run_id)
    first = runs.get_run(conn, run_id)

    view = calendar.get_g3_view(conn, first)
    assert view["stage"] == "at" and view["outcome"] is None and view["previous_publication_at"] is None
    row3 = f"ROW-{run_id}-3"
    assert view["rejected_rows"] == [{"row_id": row3, "label": "Audited annual report",
                                      "reason": "Wrong quote", "is_demo": False}]
    assert view["rejected_row_ids"] == [row3]
    assert view["uncited_paragraph_ids"] == [
        "SRC-CSSF15627-P1", "SRC-CSSF15627-P3", "SRC-UCILAW-P1", "SRC-UCILAW-P3", "SRC-CNMV-P2",
        "SRC-PRACT-P1", "SRC-PRACT-P2", "SRC-PRACT-P3"]
    assert [e["due_date"] for e in view["entries"]] == ["2027-02-10", "2027-04-19", "2027-04-30"]
    by_row = {e["row_id"]: e for e in view["entries"]}
    e1, e2, e4 = (by_row[f"ROW-{run_id}-{n}"] for n in (1, 2, 4))
    assert e1["who_files_label"] == "Fund administrator"     # the source names the filer
    assert e2["who_files_label"] == "Auditor"                # chosen at G1
    assert e1["marks"]["moved"] is None
    assert e1["why"] == "Monthly rule: due 10 calendar days after month end."
    assert e1["source_paragraph_id"] == "SRC-CSSF15627-P2" and e1["recipient_name"] == "CSSF"
    assert e2["marks"]["moved"] == {"from_date": "2027-04-18", "to_date": "2027-04-19",
                                    "direction": "following working day"}
    # Rule 4 was "AI can't tell" and the specialist added it, so its entry is precautionary.
    assert (e1["precautionary"], e2["precautionary"], e4["precautionary"]) == (False, False, True)

    flow.publish(conn, run_id)
    published = runs.get_run(conn, run_id)
    assert published["status"] == "COMPLETED" and published["published_at"]
    after = calendar.get_g3_view(conn, published)
    assert after["stage"] == "after" and after["outcome"]["at"] == published["published_at"]
    live = calendar.get_published_calendar(conn, published["fund_id"])
    assert live["entries"][0]["quote"] and live["entries"][0]["source_document"]

    second = flow.to_g3(conn, settings)
    assert calendar.get_g3_view(conn, runs.get_run(conn, second))["previous_publication_at"] \
        == published["published_at"]
    publishing.decline_calendar(conn, calendar_id=f"CAL-{second}", run_version=3,
                                decline_reason="Dates look off", actor="specialist-1")
    declined = calendar.get_g3_view(conn, runs.get_run(conn, second))
    assert declined["outcome"]["reason"] == "Dates look off" and declined["outcome"]["at"]


def test_every_paragraph_names_its_document_by_title(settings):
    """DL-53: titles come from the config, so the secondary guide (never extracted, so it has no
    stage A unit) is named by its title too, not by its bare ID."""
    from backend.services import decisions

    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run = runs.get_run(conn, flow.start_to_g1(conn, settings))
    by_id = {p["paragraph_id"]: p["document"]
             for p in decisions.get_g1_view(conn, run)["unused_paragraphs"]}
    assert by_id["SRC-PRACT-P1"] == "Practitioner guide to Luxembourg fund filings"
    assert by_id["SRC-CSSF15627-P1"] == "CSSF Circular 15/627"
