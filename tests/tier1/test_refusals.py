"""The shared refusal object (H-036 V-12): sentences, status codes, audit entry, no other change."""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID
from backend.services.audit import list_audit
from backend.services.refusals import (HTTP_STATUS, SENTENCES, Refusal, Refused, refuse,
                                       sentence)


def test_every_code_has_a_status_and_at_least_one_sentence():
    """The SAD's 17 codes each have an HTTP status, and a sentence in ux.md §5 wording."""
    assert len(HTTP_STATUS) == 17
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
