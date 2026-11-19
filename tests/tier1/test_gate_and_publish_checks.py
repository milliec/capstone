"""B2 checks on finishing a gate (GATE_INCOMPLETE, VERSION_MISMATCH, ...) and on publish/decline
(ACK_REQUIRED, ...). Each refusal gives its code, writes one audit entry, and changes nothing."""

import re

import pytest

from backend.db.connection import connect, init_db
from backend.services import decisions, gates, publishing, runs
from backend.services.refusals import Refused
from tests import flow

ACTOR = "specialist-1"


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _state(conn):
    return [tuple(r) for r in conn.execute("SELECT run_id, status, phase, run_version FROM runs")], \
        conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]


def refused(conn, function, code):
    before = _state(conn)
    audits = conn.execute("SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal'").fetchone()[0]
    with pytest.raises(Refused) as caught:
        function()
    assert caught.value.refusal.code == code
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal'"
                        ).fetchone()[0] == audits + 1
    assert _state(conn) == before
    return caught.value.refusal


def finish_g1(conn, settings, run_id, version=None):
    version = version if version is not None else runs.get_run(conn, run_id)["run_version"]
    return lambda: gates.complete_g1(conn, settings, flow.run_now, run_id=run_id,
                                     run_version=version, actor=ACTOR)


def finish_g2(conn, settings, run_id, version=None):
    version = version if version is not None else runs.get_run(conn, run_id)["run_version"]
    return lambda: gates.complete_g2(conn, settings, flow.run_now, run_id=run_id,
                                     run_version=version, actor=ACTOR)


# --- Finishing G1 and G2 -------------------------------------------------------------------------

def test_g1_cannot_finish_with_an_undecided_rule(conn, settings):
    run_id = flow.start_to_g1(conn, settings, demo=True)       # six rules and the demo rule
    flow.approve_rule(conn, run_id, 1)
    r = refused(conn, finish_g1(conn, settings, run_id), "GATE_INCOMPLETE")
    assert r.sentence == "6 rules are still undecided. Decide every rule before you finish checking."
    for n in (2, 3, 4, 5, 6):
        flow.approve_rule(conn, run_id, n)
    r = refused(conn, finish_g1(conn, settings, run_id), "GATE_INCOMPLETE")
    assert r.sentence.startswith("1 rule is still undecided.")
    flow.reject_rule(conn, run_id, flow.DEMO_N)
    finish_g1(conn, settings, run_id)()                          # now it works
    run = runs.get_run(conn, run_id)
    assert (run["phase"], run["run_version"]) == ("AT_G2", 2)   # stage B ran at once in this test


def test_g2_cannot_finish_with_an_undecided_answer_and_counts_the_cant_tells(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    flow.answer(conn, run_id, 1, "confirm", "applies")
    r = refused(conn, finish_g2(conn, settings, run_id), "GATE_INCOMPLETE")
    assert r.sentence == ("5 answers are still undecided, 1 of them where AI can't tell. "
                          "Decide every answer before you finish.")
    for n in (2, 3, 5):
        flow.answer(conn, run_id, n, "confirm", "applies")
    flow.answer(conn, run_id, flow.DOES_NOT_APPLY_N, "confirm", "does_not_apply")
    r = refused(conn, finish_g2(conn, settings, run_id), "GATE_INCOMPLETE")     # "can't tell" is left
    assert r.sentence.startswith("1 answer is still undecided, 1 of them")
    flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "Added")
    finish_g2(conn, settings, run_id)()
    assert runs.get_run(conn, run_id)["phase"] == "AT_G3"


def test_finishing_a_gate_is_refused_for_a_stale_page_the_wrong_phase_and_an_ended_review(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    refused(conn, finish_g1(conn, settings, run_id, version=9), "VERSION_MISMATCH")
    refused(conn, finish_g2(conn, settings, run_id), "RUN_STAGE_RUNNING")      # G2 is not open yet
    conn.execute("UPDATE runs SET phase = 'B_RUNNING'")
    conn.commit()
    refused(conn, finish_g1(conn, settings, run_id), "RUN_STAGE_RUNNING")
    conn.execute("UPDATE runs SET status = 'FAILED', phase = 'AT_G1'")
    conn.commit()
    refused(conn, finish_g1(conn, settings, run_id), "RUN_NOT_ACTIVE")


def test_each_stage_gets_a_fresh_attempt_counter(conn, settings):
    """rule 10: stage_attempt goes back to 1 when the next stage starts after a gate."""
    run_id = flow.start_to_g1(conn, settings)
    conn.execute("UPDATE runs SET stage_attempt = 2")
    conn.commit()
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n)
    flow.finish_g1(conn, settings, run_id)
    assert runs.get_run(conn, run_id)["stage_attempt"] == 1


# --- Publish and decline -------------------------------------------------------------------------

@pytest.fixture
def g3(conn, settings):
    return flow.to_g3(conn, settings, demo=True)               # demo rule 7 rejected, so the lists are not empty


def publish(conn, run_id, **fields):
    run = runs.get_run(conn, run_id)
    args = {"calendar_id": f"CAL-{run_id}", "run_version": run["run_version"], "acknowledged": True,
                "rejected_row_ids": [r["row_id"] for r in decisions.rejected_rows(conn, run)],
                "uncited_paragraph_ids": [p["paragraph_id"] for p in decisions.unused_paragraphs(conn, run)],
                "actor": ACTOR}
    args.update(fields)
    return lambda: publishing.publish_calendar(conn, **args)


def test_publish_needs_the_box_ticked_and_the_servers_own_lists(conn, g3):
    r = refused(conn, publish(conn, g3, acknowledged=False), "ACK_REQUIRED")
    assert (r.anchor, r.sentence.startswith("Tick the box")) == ("ack", True)
    r = refused(conn, publish(conn, g3, rejected_row_ids=[]), "ACK_REQUIRED")      # list changed
    assert r.sentence.startswith("The lists of rejected rules or unused paragraphs are not")
    refused(conn, publish(conn, g3, uncited_paragraph_ids=["SRC-PRACT-P1"]), "ACK_REQUIRED")
    refused(conn, publish(conn, g3, rejected_row_ids=["ROW-OTHER-1"]), "ACK_REQUIRED")


def test_publish_is_refused_for_a_stale_page_and_a_review_not_at_g3(conn, g3):
    refused(conn, publish(conn, g3, run_version=1), "VERSION_MISMATCH")
    conn.execute("UPDATE runs SET phase = 'AT_G2'")
    conn.commit()
    refused(conn, publish(conn, g3), "RUN_STAGE_RUNNING")
    conn.execute("UPDATE runs SET status = 'DECLINED', phase = 'AT_G3'")
    conn.commit()
    refused(conn, publish(conn, g3), "RUN_NOT_ACTIVE")


def test_a_matching_publish_works_once_and_records_what_was_acknowledged(conn, g3):
    publish(conn, g3)()
    stored = conn.execute("SELECT * FROM publications").fetchone()
    assert stored["acknowledged_rejected_row_ids"] == f'["ROW-{g3}-{flow.DEMO_N}"]'
    assert "SRC-PRACT-P1" in stored["acknowledged_uncited_paragraph_ids"]
    refused(conn, publish(conn, g3), "RUN_NOT_ACTIVE")         # a second publish is refused


def test_decline_needs_a_reason_and_the_right_state(conn, g3):
    def decline(**fields):
        args = {"calendar_id": f"CAL-{g3}", "run_version": runs.get_run(conn, g3)["run_version"],
                    "decline_reason": "Dates look off", "actor": ACTOR}
        args.update(fields)
        return lambda: publishing.decline_calendar(conn, **args)

    r = refused(conn, decline(decline_reason="  "), "REASON_REQUIRED")
    assert (r.anchor, r.typed) == ("decline-reason", {"decline_reason": "  "})
    refused(conn, decline(run_version=1), "VERSION_MISMATCH")
    decline()()
    assert runs.get_run(conn, g3)["status"] == "DECLINED"
    refused(conn, decline(), "RUN_NOT_ACTIVE")


# --- Through the pages -----------------------------------------------------------------------

def test_g1_page_comes_back_with_the_refusal_the_typed_text_and_the_status(specialist_client):
    html = specialist_client.post("/specialist/runs", data={}).text
    run_id = re.search(r"RUN-\d{8}-\d+", html).group(0)
    page = specialist_client.post(f"/specialist/rows/ROW-{run_id}-3/decision",
                                  data={"version": 1, "decision": "reject", "reject_reason": " "})
    assert page.status_code == 422
    assert "<title>Not done: " in page.text
    assert page.text.count("Write a reason to reject this rule.") >= 1
    assert "Not done. The reason is shown beside rule 3." in page.text
    assert 'href="#row-3"' in page.text


def test_text_typed_on_a_refused_answer_is_shown_again(specialist_client):
    html = specialist_client.post("/specialist/runs", data={}).text
    run_id = re.search(r"RUN-\d{8}-\d+", html).group(0)
    flow.decide_every_rule_http(specialist_client, run_id)
    specialist_client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    # Rule 1: AI says "applies", so an overrule must give "doesn't apply". This one does not.
    page = specialist_client.post(
        f"/specialist/verdicts/VER-{run_id}-1/decision",
        data={"version": 1, "decision": "override", "value": "applies",
              "override_reason": "keep this text"})
    assert page.status_code == 422
    assert "Part of this form was not valid (the answer), so nothing was saved." in page.text
    assert re.search(r"<textarea[^>]*>keep this text</textarea>", page.text)


def test_finishing_g1_early_shows_the_page_level_sentence(specialist_client):
    html = specialist_client.post("/specialist/runs", data={}).text
    run_id = re.search(r"RUN-\d{8}-\d+", html).group(0)
    page = specialist_client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    assert page.status_code == 409
    assert "6 rules are still undecided. Decide every rule before you finish checking." in page.text


def test_the_g3_form_must_say_which_answer_and_match_its_button(specialist_client, settings):
    html = specialist_client.post("/specialist/runs", data={}).text
    run_id = re.search(r"RUN-\d{8}-\d+", html).group(0)
    flow.decide_every_rule_http(specialist_client, run_id)
    specialist_client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    flow.answer_every_verdict_http(specialist_client, run_id)
    specialist_client.post(f"/specialist/runs/{run_id}/g2/complete", data={"run_version": 2})
    url = f"/specialist/calendars/CAL-{run_id}"
    none = specialist_client.post(f"{url}/publish", data={"run_version": 3})
    assert none.status_code == 422 and "Choose an answer first" in none.text
    wrong = specialist_client.post(f"{url}/publish", data={"run_version": 3, "decision": "decline"})
    assert wrong.status_code == 422 and "Part of this form was not valid" in wrong.text
    wrong = specialist_client.post(f"{url}/decline", data={"run_version": 3, "decision": "publish"})
    assert wrong.status_code == 422
    ok = flow.publish_http(specialist_client, run_id)
    assert ok.status_code == 303
