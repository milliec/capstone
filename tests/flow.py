"""Helpers that drive a review through its real steps, as a person would (B2).

Since B2 the server refuses a gate that has an undecided item, and a publish whose lists do not
match its own. So a test that needs a published calendar must decide everything first. These
helpers do that over HTTP (`*_http`, for page tests) or by calling the services (for service tests).
"""

import re

from backend.services import FUND_ID, decisions, gates, publishing, runs

SPECIALIST = "specialist-1"

# The stand-in review since B3 step 5 (backend/stand_in/*.yaml): stage A drafts 6 rules, in
# document order; the demo rule, when switched on, is rule 7. Stage B's answers: rule 4 is
# "AI can't tell" (unsure), rule 6 "doesn't apply", the others "applies". Rule 3 has the one flag.
RULES = (1, 2, 3, 4, 5, 6)
DEMO_N = 7
UNSURE_N = 4
DOES_NOT_APPLY_N = 6
APPLIES_NS = (1, 2, 3, 5)
FLAGGED_N = 3

# The specialist's demo choices at G1 (B4), as the answer key's §5 expects them, so a whole review
# gives exactly the demo calendar (KEY §4: 22 entries). Business-day rule per rule, and "who files"
# for the rules whose source is silent (rules 1 and 4 name their filer). Single-decision helpers
# below keep their simple defaults.
DEMO_RULES = {1: "roll_forward", 2: "no_roll", 3: "roll_forward", 4: "roll_backward",
              5: "roll_backward", 6: "no_roll"}
DEMO_WHO = {1: None, 2: "Fund administrator", 3: "Fund administrator", 4: None, 5: "AIFM",
            6: "Tax advisor"}


def run_now(function, *args, **kwargs):
    """Stands in for FastAPI's background task: runs the stage at once, in this thread."""
    return function(*args, **kwargs)


# --- Over HTTP (page tests) ---------------------------------------------------------------------

# Approving over a checker flag needs a written reason (B2), so the flagged rule gets one.
FLAG_REASON = "Checked: the law itself sets the deadline"


def approve_rule_http(client, run_id, n, rule="roll_forward", who="AIFM", reason=None):
    reason = reason or (FLAG_REASON if n == FLAGGED_N else None)
    return client.post(f"/specialist/rows/ROW-{run_id}-{n}/decision", follow_redirects=False,
                       data={"version": 1, "decision": "approve", "business_day_rule": rule,
                             **({"who_files": who} if who else {}),
                             **({"approve_reason": reason} if reason else {})})


def reject_rule_http(client, run_id, n, reason="Test"):
    return client.post(f"/specialist/rows/ROW-{run_id}-{n}/decision", follow_redirects=False,
                       data={"version": 1, "decision": "reject", "reject_reason": reason})


def decide_every_rule_http(client, run_id, demo=False):
    """Approve rules 1 to 6 with the demo's choices; reject the demo rule (7) when it is on."""
    for n in RULES:
        approve_rule_http(client, run_id, n, rule=DEMO_RULES[n], who=DEMO_WHO[n])
    if demo:
        reject_rule_http(client, run_id, DEMO_N, "Quote doesn't support the rule")


def answer_every_verdict_http(client, run_id):
    """Confirm every "applies"; add the "AI can't tell" rule (4); confirm "doesn't apply" (6)."""
    post = lambda n, **data: client.post(f"/specialist/verdicts/VER-{run_id}-{n}/decision",
                                         data={"version": 1, **data}, follow_redirects=False)
    for n in APPLIES_NS:
        post(n, decision="confirm", value="applies")
    post(UNSURE_N, decision="decide", value="applies",
         decide_reason="Not confirmed in fund records yet")
    post(DOES_NOT_APPLY_N, decision="confirm", value="does_not_apply")


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


def approve_rule(conn, run_id, n, rule="roll_forward", who="AIFM", reason=None, actor=SPECIALIST):
    reason = reason or (FLAG_REASON if n == FLAGGED_N else None)
    return decisions.decide_row(
        conn, row_id=f"ROW-{run_id}-{n}", version=1, decision="approve", business_day_rule=rule,
        who_files=who, approve_reason=reason, reject_reason=None, actor=actor)


def reject_rule(conn, run_id, n, reason="Test"):
    return decisions.decide_row(
        conn, row_id=f"ROW-{run_id}-{n}", version=1, decision="reject", business_day_rule=None,
        who_files=None, approve_reason=None, reject_reason=reason, actor=SPECIALIST)


def answer(conn, run_id, n, decision, value, reason=None, actor=SPECIALIST):
    return decisions.decide_verdict(
        conn, verdict_id=f"VER-{run_id}-{n}", version=1, decision=decision, value=value,
        confirm_reason=None, override_reason=reason if decision == "override" else None,
        decide_reason=reason if decision == "decide" else None, actor=actor)


def finish_g1(conn, settings, run_id, actor=SPECIALIST):
    gates.complete_g1(conn, settings, run_now, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=actor)


def finish_g2(conn, settings, run_id, actor=SPECIALIST):
    gates.complete_g2(conn, settings, run_now, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=actor)


def to_g3(conn, settings, demo=False):
    """A review at G3: rules 1 to 6 approved with the demo's G1 choices (the demo rule rejected),
    every answer given as `answer_every_verdict_http` does. The date engine (B4) then gives the
    demo calendar: 22 entries (rule 6, VAT, does not apply). Returns the run ID."""
    run_id = start_to_g1(conn, settings, demo)
    for n in RULES:
        approve_rule(conn, run_id, n, rule=DEMO_RULES[n], who=DEMO_WHO[n])
    if demo:
        reject_rule(conn, run_id, DEMO_N, "Quote doesn't support the rule")
    finish_g1(conn, settings, run_id)
    for n in APPLIES_NS:
        answer(conn, run_id, n, "confirm", "applies")
    answer(conn, run_id, UNSURE_N, "decide", "applies", "Not confirmed in fund records yet")
    answer(conn, run_id, DOES_NOT_APPLY_N, "confirm", "does_not_apply")
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
