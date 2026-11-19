"""The first green path (Build card, sad.md "First green path"; Tier 1). No model, no paid call.

With AGENTS_MODE=stand_in, one review passes END TO END, driven through the pages as the specialist
and the General Partner would:

  start run → stand-in stage A → G1, including the planted row (Approve refused by the server, then
  reject) → stand-in stage B → G2 → stage C dates → G3 with the acknowledgement → the GP view shows
  "being prepared" and then the published calendar → the audit log shows every step.

Until this passes, DL-40 is not pinned (SOQ-25) and no paid call is made, the B3 spike included.
The expected numbers are the demo's (answer key §1 and §4): 7 drafted → 6 approved → 6 checked →
5 apply → 22 dates.
"""

import re

from backend.services import FUND_ID, runs, trace
from backend.services.audit import list_audit
from tests import flow

DEMO_REASON = "Quote doesn't support the rule"


def _text(html: str) -> str:
    """The page's visible words, one space apart (tags removed)."""
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_the_first_green_path_end_to_end(settings, specialist_client, gp_client, db):
    assert settings.agents_mode == "stand_in"                                 # never a model

    # --- Before anything: the GP sees "being prepared" -------------------------------------
    assert "being prepared and checked" in gp_client.get("/calendar").text

    # --- Start the review with the demo rule; stand-in stage A runs --------------------------
    started = specialist_client.post("/specialist/runs", data={"demo_planted_row": "true"},
                                     follow_redirects=False)
    assert started.status_code == 303
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    run = runs.get_run(db, run_id)
    assert (run["status"], run["phase"], run["agents_mode"]) == ("ACTIVE", "AT_G1", "stand_in")
    status_page = _text(specialist_client.get(f"/specialist/runs/{run_id}").text)
    assert "Stand-in agents" in status_page and "Demo rule on" in status_page

    # --- G1: 7 rules; the planted row's approval is refused, then it is rejected -------------
    g1 = specialist_client.get(f"/specialist/runs/{run_id}/g1").text
    assert "Rule 7 of 7" in _text(g1)
    refused = flow.approve_rule_http(specialist_client, run_id, flow.DEMO_N)
    assert refused.status_code == 409
    assert "This rule can" in refused.text and "t be approved" in refused.text
    assert "Approval blocked" in specialist_client.get(f"/specialist/runs/{run_id}/g1").text
    flow.decide_every_rule_http(specialist_client, run_id)                    # rules 1 to 6
    assert flow.reject_rule_http(specialist_client, run_id, flow.DEMO_N,
                                 DEMO_REASON).status_code == 303
    done_g1 = specialist_client.post(f"/specialist/runs/{run_id}/g1/complete",
                                     data={"run_version": 1}, follow_redirects=False)
    assert done_g1.status_code == 303

    # --- Stand-in stage B ran; G2: answer all six, the "can't tell" one added ----------------
    assert runs.get_run(db, run_id)["phase"] == "AT_G2"
    g2 = _text(specialist_client.get(f"/specialist/runs/{run_id}/g2").text)
    assert "Statistical report A01" in g2
    flow.answer_every_verdict_http(specialist_client, run_id)
    done_g2 = specialist_client.post(f"/specialist/runs/{run_id}/g2/complete",
                                     data={"run_version": 2}, follow_redirects=False)
    assert done_g2.status_code == 303

    # --- Stage C dates; G3 shows the calendar; the GP still sees "being prepared" ------------
    run = runs.get_run(db, run_id)
    assert (run["phase"], run["counts"]) == ("AT_G3", {"rules": 7, "unsure": 1, "dates": 22})
    g3 = specialist_client.get(f"/specialist/runs/{run_id}/g3").text
    assert "Is this calendar ready for the General Partner?" in g3
    assert "being prepared and checked" in gp_client.get("/calendar").text    # not published yet

    # --- G3 with the acknowledgement: publish -------------------------------------------------
    published = flow.publish_http(specialist_client, run_id)
    assert published.status_code == 303
    assert runs.get_run(db, run_id)["status"] == "COMPLETED"

    # --- The GP now sees the published calendar: 22 dates, no specialist-only marks ---------
    gp = gp_client.get("/calendar?view=list").text
    gp_words = _text(gp)
    assert "being prepared" not in gp
    assert "Entries in 2027: 22" in gp_words and "May not be required 4" in gp_words
    assert "Due next Mon 11 Jan 2027" in gp_words
    assert "OQ-7" not in gp and "Moved off a weekend" not in gp_words and "Demo" not in gp_words
    assert "Made with stand-in agents" in gp_words

    # --- The audit log shows every step, in order -------------------------------------------
    audit = list_audit(db, run_id)
    milestones = [a["reason"] for a in audit if a["event_type"] in ("gate_event", "system")]
    expected_order = ["Review started", "Demo rule switch on", "Stage A finished (stand-in)",
                      "G1 completed", "Stage B finished (stand-in)", "G2 completed",
                      "Stage C finished (stand-in)"]
    assert [m for m in milestones if m in expected_order] == expected_order
    assert milestones[-1].startswith("Calendar published (acknowledged 1 rejected rules")

    kinds = [a["event_type"] for a in audit]
    assert kinds.count("agent_output") == 5 + 7 + 6        # extract per document, check per rule
    refusals = [a for a in audit if a["event_type"] == "refusal"]
    assert [a["refusal_code"] for a in refusals] == ["DEMO_ROW_NOT_APPROVABLE"]
    decisions = [a for a in audit if a["event_type"] == "decision"]
    assert len(decisions) == 7 + 6                          # 7 rules (one rejected), 6 answers
    assert any(a["subject_id"] == f"ROW-{run_id}-7" and a["reason"].startswith("reject")
               for a in decisions)

    # Every agent output points at its trace line; the stand-in trace shows no model and no cost.
    lines = trace.list_trace(db, run_id)
    assert len(lines) == 18 and {line["model"] for line in lines} == {""}
    assert runs.get_run(db, run_id)["cost_so_far"] == 0
    refs = {a["trace_ref"] for a in audit if a["event_type"] == "agent_output"}
    assert refs == {trace.record_key(run_id, t["step"], t["stage_attempt"], t["unit_id"],
                                     t["attempt_n"]) for t in lines}
