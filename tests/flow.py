"""Helpers that drive a review through its real steps, as a person would (B2).

Since B2 the server refuses a gate that has an undecided item, and a publish whose lists do not
match its own. So a test that needs a published calendar must decide everything first. These
helpers do that over HTTP (`*_http`, for page tests) or by calling the services (for service tests).
"""

import re

from backend.runtime.stages import run_stage
from backend.services import FUND_ID, decisions, gates, publishing, runs

SPECIALIST = "specialist-1"


def run_now(function, *args, **kwargs):
    """Stands in for FastAPI's background task: runs the stage at once, in this thread."""
    return function(*args, **kwargs)


# --- Over HTTP (page tests) ---------------------------------------------------------------------

def approve_rule_http(client, run_id, n, rule="roll_forward", who="AIFM"):
    return client.post(f"/specialist/rows/ROW-{run_id}-{n}/decision", follow_redirects=False,
                       data={"version": 1, "decision": "approve", "business_day_rule": rule,
                             "who_files": who})


def reject_rule_http(client, run_id, n, reason="Test"):
    return client.post(f"/specialist/rows/ROW-{run_id}-{n}/decision", follow_redirects=False,
                       data={"version": 1, "decision": "reject", "reject_reason": reason})


def decide_every_rule_http(client, run_id, demo=False):
    """Approve rules 1 to 3; reject the demo rule (4) when it is on."""
    for n in (1, 2, 3):
        approve_rule_http(client, run_id, n)
    if demo:
        reject_rule_http(client, run_id, 4, "Quote doesn't support the rule")


def answer_every_verdict_http(client, run_id):
    """Rule 1: confirm applies. Rule 2 (AI can't tell): add it. Rule 3: confirm doesn't apply."""
    post = lambda n, **data: client.post(f"/specialist/verdicts/VER-{run_id}-{n}/decision",
                                         data={"version": 1, **data}, follow_redirects=False)
    post(1, decision="confirm", value="applies")
    post(2, decision="decide", value="applies", decide_reason="Not confirmed in fund records yet")
    post(3, decision="confirm", value="does_not_apply")


def publish_http(client, run_id, run_version=3):
    """Publish with the two lists exactly as the page shows them (hidden fields), ticked."""
    html = client.get(f"/specialist/runs/{run_id}/g3").text
    data = {"run_version": run_version, "decision": "publish", "acknowledged": "true",
            "rejected_row_ids": re.findall(r'name="rejected_row_ids" value="([^"]+)"', html),
            "uncited_paragraph_ids": re.findall(r'name="uncited_paragraph_ids" value="([^"]+)"', html)}
    return client.post(f"/specialist/calendars/CAL-{run_id}/publish", data=data,
                       follow_redirects=False)


def publish_everything_http(client, run_id, demo=False):
    """Decide every rule, finish G1, answer every verdict, finish G2, publish."""
    decide_every_rule_http(client, run_id, demo)
    client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    answer_every_verdict_http(client, run_id)
    client.post(f"/specialist/runs/{run_id}/g2/complete", data={"run_version": 2})
    return publish_http(client, run_id)


# --- Through the services (service tests) ------------------------------------------------------

def start_to_g1(conn, settings, demo=False):
    """Start a review and let stage A finish, so the rules are stored and G1 is open."""
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")   # test set-up
    conn.commit()
    return runs.start_run(conn, settings, run_now, fund_id=FUND_ID, started_by=SPECIALIST,
                          demo_planted_row=demo, demo_fail_step1=False)


def approve_rule(conn, run_id, n, rule="roll_forward", who="AIFM", reason=None):
    return decisions.decide_row(
        conn, row_id=f"ROW-{run_id}-{n}", version=1, decision="approve", business_day_rule=rule,
        who_files=who, approve_reason=reason, reject_reason=None, actor=SPECIALIST)


def reject_rule(conn, run_id, n, reason="Test"):
    return decisions.decide_row(
        conn, row_id=f"ROW-{run_id}-{n}", version=1, decision="reject", business_day_rule=None,
        who_files=None, approve_reason=None, reject_reason=reason, actor=SPECIALIST)


def answer(conn, run_id, n, decision, value, reason=None):
    return decisions.decide_verdict(
        conn, verdict_id=f"VER-{run_id}-{n}", version=1, decision=decision, value=value,
        confirm_reason=None, override_reason=reason if decision == "override" else None,
        decide_reason=reason if decision == "decide" else None, actor=SPECIALIST)


def finish_g1(conn, settings, run_id):
    gates.complete_g1(conn, settings, run_now, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=SPECIALIST)


def finish_g2(conn, settings, run_id):
    gates.complete_g2(conn, settings, run_now, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=SPECIALIST)


def to_g3(conn, settings, demo=False):
    """A review at G3: rules 1 to 3 approved, answers given (1 applies, 2 added, 3 doesn't
    apply), so the calendar has two entries. Returns the run ID."""
    run_id = start_to_g1(conn, settings, demo)
    for n in (1, 2, 3):
        approve_rule(conn, run_id, n)
    if demo:
        reject_rule(conn, run_id, 4, "Quote doesn't support the rule")
    finish_g1(conn, settings, run_id)
    answer(conn, run_id, 1, "confirm", "applies")
    answer(conn, run_id, 2, "decide", "applies", "Not confirmed in fund records yet")
    answer(conn, run_id, 3, "confirm", "does_not_apply")
    finish_g2(conn, settings, run_id)
    return run_id


def publish(conn, run_id, actor=SPECIALIST):
    """Publish with the server's own lists."""
    run = runs.get_run(conn, run_id)
    return publishing.publish_calendar(
        conn, calendar_id=f"CAL-{run_id}", run_version=run["run_version"], acknowledged=True,
        rejected_row_ids=[r["row_id"] for r in decisions.rejected_rows(conn, run)],
        uncited_paragraph_ids=[p["paragraph_id"] for p in decisions.unused_paragraphs(conn, run)],
        actor=actor)
