"""The shared refusal object (H-036 V-12): sentences, status codes, audit entry, no other change."""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID
from backend.services.refusals import HTTP_STATUS, SENTENCES, Refusal, Refused, refuse, sentence


def test_every_code_has_a_status_and_at_least_one_sentence():
    """The SAD's 18 codes each have an HTTP status, and a sentence in ux.md §5 wording (18th: DL-61)."""
    assert len(HTTP_STATUS) == 18
    coded = {code for code, _ in SENTENCES}
    assert coded == set(HTTP_STATUS)


def test_sentences_fill_their_values_and_follow_ux_md():
    assert sentence("RUN_ACTIVE", n=4).startswith("Review 4 is still in progress")
    assert "paragraph SRC-X-P2." in sentence("QUOTE_CHECK_FAILED", para_id="SRC-X-P2")
    assert sentence("GATE_INCOMPLETE", "g2", x=3, u=1) == (
        "3 answers are still undecided, 1 of them where AI can't tell. "
        "Decide every answer before you finish.")
    assert sentence("RUN_NOT_ACTIVE", status="Abandoned").startswith("This review has ended (Abandoned)")
    assert sentence("VALIDATION", "no_answer") == (
        "Choose an answer first, then use its button. Nothing was saved.")
    assert "Your attempt has been recorded in the audit trail." in sentence("DEMO_ROW_NOT_APPROVABLE")


def test_status_by_code():
    assert Refusal("FORBIDDEN", "x").http_status == 403
    assert Refusal("VALIDATION", "x").http_status == 422
    assert Refusal("ALREADY_DECIDED", "x").http_status == 409


def test_refuse_audits_once_and_raises_the_shared_object(settings):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    with pytest.raises(Refused) as caught:
        refuse(conn, "REASON_REQUIRED", "reject_rule", actor="specialist-1", fund_id=FUND_ID,
               run_id=None, subject_id="ROW-X-3", anchor="row-3", target_label="rule 3",
               typed={"reject_reason": "  "})
    r = caught.value.refusal
    assert (r.code, r.anchor, r.target_label, r.http_status) == ("REASON_REQUIRED", "row-3",
                                                                 "rule 3", 422)
    assert r.sentence == "Write a reason to reject this rule."
    assert r.typed == {"reject_reason": "  "}
    audit = conn.execute("SELECT * FROM audit_log WHERE event_type = 'refusal'").fetchall()
    assert len(audit) == 1 and audit[0]["refusal_code"] == "REASON_REQUIRED"
    assert audit[0]["subject_id"] == "ROW-X-3" and audit[0]["actor"] == "specialist-1"


# --- RETRY_NOT_ALLOWED: five reasons, five sentences (H-094, ux.md §5) ---------------------------
# Retry (B13b) is not built, so nothing raises this refusal yet. These tests only check that the
# sentence is right for each reason, so B13b can pass the context and get the right words.

NEW_REVIEW_ENDING = "Start a new review from Filing rules."
RETRY_SENTENCES = {
    "cost cap": ("This step can't be tried again, because the review reached its cost limit. "
                 + NEW_REVIEW_ENDING),
    "calendar generation": ("This step can't be tried again, because the dates could not be "
                            "worked out, and trying again would give the same result. "
                            + NEW_REVIEW_ENDING),
    "evaluation run": ("This step can't be tried again, because this is an evaluation run. "
                       + NEW_REVIEW_ENDING),
    "newer run": ("This step can't be tried again, because a newer review has been started. "
                  + NEW_REVIEW_ENDING),
    "call limit": ("This step can't be tried again, because the limit on real model calls was "
                   "reached. A new review would reach the same limit. Ask the operator to review "
                   "the limit."),
}


@pytest.mark.parametrize("reason", sorted(RETRY_SENTENCES))
def test_retry_not_allowed_sentence_for_each_of_the_five_reasons(reason):
    """Word for word, as in ux.md §5."""
    assert sentence("RETRY_NOT_ALLOWED", reason) == RETRY_SENTENCES[reason]


def test_only_the_call_limit_sentence_leaves_out_the_new_review_advice():
    """A new review would reach the same call limit, so that one sentence must not send the
    specialist to start one. The other four still do."""
    for reason in RETRY_SENTENCES:
        text = sentence("RETRY_NOT_ALLOWED", reason)
        assert (NEW_REVIEW_ENDING in text) == (reason != "call limit"), reason


def test_retry_not_allowed_is_still_a_409_with_its_audit_entry(settings):
    """The wording changed; the code, its 409 and the audit entry did not."""
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    with pytest.raises(Refused) as caught:
        refuse(conn, "RETRY_NOT_ALLOWED", "call limit", actor="specialist-1", fund_id=FUND_ID)
    refusal = caught.value.refusal
    assert (refusal.code, refusal.http_status) == ("RETRY_NOT_ALLOWED", 409)
    assert refusal.sentence == RETRY_SENTENCES["call limit"]
    audit = conn.execute("SELECT * FROM audit_log WHERE event_type = 'refusal'").fetchall()
    assert len(audit) == 1 and audit[0]["refusal_code"] == "RETRY_NOT_ALLOWED"
