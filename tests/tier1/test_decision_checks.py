"""B2 decision checks at G1 (rules) and G2 (answers). Each refusal gives its code, writes exactly
one audit entry, and stores nothing (no decision line, no phase or version change)."""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, decisions, runs
from backend.services.refusals import NotFound, Refused
from tests import flow

ACTOR = "specialist-1"


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


@pytest.fixture
def g1(conn, settings):
    return flow.start_to_g1(conn, settings)


def _state(conn):
    return (conn.execute("SELECT COUNT(*) FROM row_decisions").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM verdict_decisions").fetchone()[0],
            [tuple(r) for r in conn.execute("SELECT run_id, status, phase, run_version FROM runs")])


def refused(conn, function, code, **expected):
    """Call `function`; it must refuse with `code`, audit once, and change nothing."""
    before, audits = _state(conn), conn.execute(
        "SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal'").fetchone()[0]
    with pytest.raises(Refused) as caught:
        function()
    refusal = caught.value.refusal
    assert refusal.code == code
    for name, value in expected.items():
        assert getattr(refusal, name) == value, name
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal'"
                        ).fetchone()[0] == audits + 1
    assert _state(conn) == before
    return refusal


def row(conn, run_id, n, **fields):
    args = dict(row_id=f"ROW-{run_id}-{n}", version=1, decision="approve",
                business_day_rule="roll_forward", who_files="AIFM", approve_reason=None,
                reject_reason=None, actor=ACTOR)
    args.update(fields)
    return lambda: decisions.decide_row(conn, **args)


# --- G1 ------------------------------------------------------------------------------------------

def test_an_approve_and_a_reject_are_stored_once(conn, g1):
    flow.approve_rule(conn, g1, 1)
    flow.reject_rule(conn, g1, 2, "  Wrong quote ")
    stored = {r["row_id"]: dict(r) for r in conn.execute("SELECT * FROM row_decisions")}
    approved, rejected = stored[f"ROW-{g1}-1"], stored[f"ROW-{g1}-2"]
    assert (approved["decision"], approved["business_day_rule"], approved["who_files"]) == \
        ("approve", "roll_forward", "AIFM")
    assert (rejected["decision"], rejected["reason"], rejected["business_day_rule"]) == \
        ("reject", "Wrong quote", None)
    assert approved["row_version"] == 1 and approved["decided_by"] == ACTOR and approved["decided_at"]


def test_a_rule_can_only_be_decided_once(conn, g1):
    flow.approve_rule(conn, g1, 1)
    r = refused(conn, row(conn, g1, 1, decision="reject", reject_reason="Changed my mind"),
                "ALREADY_DECIDED", anchor="row-1", target_label="rule 1")
    assert r.sentence.startswith("This rule was already decided")


def test_reject_needs_a_reason_and_keeps_what_was_typed(conn, g1):
    r = refused(conn, row(conn, g1, 3, decision="reject", reject_reason="   "), "REASON_REQUIRED",
                anchor="row-3", target_label="rule 3")
    assert r.sentence == "Write a reason to reject this rule."
    assert r.typed["reject_reason"] == "   "


def test_no_answer_chosen_is_validation(conn, g1):
    for chosen in ("", "maybe"):
        refused(conn, row(conn, g1, 1, decision=chosen), "VALIDATION", anchor="row-1")


def test_approve_needs_a_failed_quote_check_to_pass(conn, g1):
    conn.execute("UPDATE quote_checks SET result = 'fail' WHERE row_id = ?", (f"ROW-{g1}-2",))
    conn.commit()
    r = refused(conn, row(conn, g1, 2), "QUOTE_CHECK_FAILED", anchor="row-2")
    assert "paragraph SRC-STUB-P2" in r.sentence
    flow.reject_rule(conn, g1, 2, "Failed the check")      # rejecting is still allowed


@pytest.mark.parametrize("rule", [None, "", "not_confirmed", "sometimes"])
def test_approve_needs_a_real_business_day_rule(conn, g1, rule):
    refused(conn, row(conn, g1, 2, business_day_rule=rule), "BUSINESS_DAY_RULE_REQUIRED",
            anchor="row-2")


def test_approve_needs_a_filing_party_when_the_source_is_silent(conn, g1):
    refused(conn, row(conn, g1, 1, who_files=None), "WHO_FILES_REQUIRED", anchor="row-1")
    refused(conn, row(conn, g1, 1, who_files="  "), "WHO_FILES_REQUIRED")
    refused(conn, row(conn, g1, 1, who_files="Somebody else"), "VALIDATION",
            anchor="row-1")                                  # a value the page never offered
    flow.approve_rule(conn, g1, 2, who=None)                 # rule 2 names its filer: not asked
    assert conn.execute("SELECT who_files FROM row_decisions WHERE row_id = ?",
                        (f"ROW-{g1}-2",)).fetchone()[0] is None


def test_approve_over_a_flag_needs_a_reason(conn, g1):
    conn.execute("INSERT INTO flags (row_id, run_id, fund_id, flag_type, explanation, row_value, "
                 "quote_says) VALUES (?, ?, ?, 'internal', 'x', '+20 days', '+30 days')",
                 (f"ROW-{g1}-2", g1, FUND_ID))
    conn.commit()
    refused(conn, row(conn, g1, 2), "REASON_REQUIRED", anchor="row-2")
    flow.approve_rule(conn, g1, 2, reason="The source is the later one")
    assert decisions.get_g1_view(conn, runs.get_run(conn, g1))["rows"][1]["has_flag"] is True


def test_the_other_answers_fields_are_ignored(conn, g1):
    """DL-48: CSS hides the field of the answer not chosen but the browser still sends it."""
    flow.approve_rule(conn, g1, 2)
    decisions.decide_row(conn, row_id=f"ROW-{g1}-1", version=1, decision="approve",
                         business_day_rule="no_roll", who_files="AIFM", approve_reason="ok",
                         reject_reason="", actor=ACTOR)
    decisions.decide_row(conn, row_id=f"ROW-{g1}-3", version=1, decision="reject",
                         business_day_rule="roll_forward", who_files="AIFM", approve_reason="x",
                         reject_reason="No", actor=ACTOR)
    third = conn.execute("SELECT * FROM row_decisions WHERE row_id = ?", (f"ROW-{g1}-3",)).fetchone()
    assert (third["business_day_rule"], third["who_files"], third["reason"]) == (None, None, "No")


def test_decisions_are_refused_when_the_review_is_not_at_g1(conn, g1):
    conn.execute("UPDATE runs SET phase = 'B_RUNNING'")
    conn.commit()
    r = refused(conn, row(conn, g1, 1), "RUN_STAGE_RUNNING")
    assert "AI is still working on step 3" in r.sentence
    conn.execute("UPDATE runs SET phase = 'AT_G2'")
    conn.commit()
    r = refused(conn, row(conn, g1, 1), "RUN_STAGE_RUNNING")
    assert r.sentence.startswith("This step is not open for decisions")
    conn.execute("UPDATE runs SET status = 'ABANDONED', phase = 'AT_G1'")
    conn.commit()
    r = refused(conn, row(conn, g1, 1), "RUN_NOT_ACTIVE")
    assert "(Abandoned)" in r.sentence


def test_an_unknown_rule_is_not_found(conn, g1):
    with pytest.raises(NotFound):
        row(conn, g1, 99)()


# --- G2 ------------------------------------------------------------------------------------------

@pytest.fixture
def g2(conn, settings, g1):
    for n in (1, 2, 3):
        flow.approve_rule(conn, g1, n)
    flow.finish_g1(conn, settings, g1)
    return g1


def verdict(conn, run_id, n, **fields):
    args = dict(verdict_id=f"VER-{run_id}-{n}", version=1, decision="confirm", value="applies",
                confirm_reason=None, override_reason=None, decide_reason=None, actor=ACTOR)
    args.update(fields)
    return lambda: decisions.decide_verdict(conn, **args)


def test_each_kind_of_answer_is_stored(conn, g2):
    flow.answer(conn, g2, 1, "confirm", "applies")
    flow.answer(conn, g2, 2, "decide", "does_not_apply", "Leave it off")
    flow.answer(conn, g2, 3, "override", "applies", "It applies")
    stored = {r["verdict_id"]: dict(r) for r in conn.execute("SELECT * FROM verdict_decisions")}
    assert [(d["decision"], d["final_value"]) for d in stored.values()] == \
        [("confirm", "applies"), ("decide", "does_not_apply"), ("override", "applies")]
    assert stored[f"VER-{g2}-1"]["reason"] is None and stored[f"VER-{g2}-3"]["reason"] == "It applies"


def test_an_answer_can_only_be_given_once(conn, g2):
    flow.answer(conn, g2, 1, "confirm", "applies")
    r = refused(conn, verdict(conn, g2, 1, decision="override", value="does_not_apply",
                              override_reason="no"), "ALREADY_DECIDED", anchor="verdict-1")
    assert r.sentence.startswith("This answer was already decided")


def test_no_answer_or_an_answer_that_does_not_fit_is_validation(conn, g2):
    refused(conn, verdict(conn, g2, 1, decision=""), "VALIDATION", anchor="verdict-1")
    refused(conn, verdict(conn, g2, 1, value="applies", decision="override", override_reason="x"),
            "VALIDATION")                                    # overrule must give the opposite
    refused(conn, verdict(conn, g2, 1, value="does_not_apply"), "VALIDATION")   # confirm must repeat
    refused(conn, verdict(conn, g2, 1, decision="decide", decide_reason="x"), "VALIDATION")  # AI did tell
    refused(conn, verdict(conn, g2, 2, decision="confirm", value="applies"), "VALIDATION")    # AI can't tell
    refused(conn, verdict(conn, g2, 2, decision="decide", value="maybe", decide_reason="x"), "VALIDATION")


def test_overrule_and_decide_need_a_reason_worded_for_the_answer(conn, g2):
    r = refused(conn, verdict(conn, g2, 1, decision="override", value="does_not_apply",
                              override_reason=" "), "REASON_REQUIRED", anchor="verdict-1")
    assert "General Partner will not see it" in r.sentence
    assert r.typed["override_reason"] == " "
    r = refused(conn, verdict(conn, g2, 2, decision="decide", value="applies"), "REASON_REQUIRED")
    assert "will read it as the explanation" in r.sentence
    flow.answer(conn, g2, 1, "confirm", "applies")           # confirm needs no reason


def test_answers_are_refused_when_the_review_is_not_at_g2(conn, g2):
    conn.execute("UPDATE runs SET phase = 'AT_G1'")
    conn.commit()
    refused(conn, verdict(conn, g2, 1), "RUN_STAGE_RUNNING")
    conn.execute("UPDATE runs SET status = 'DECLINED', phase = 'AT_G2'")
    conn.commit()
    refused(conn, verdict(conn, g2, 1), "RUN_NOT_ACTIVE")
