"""Refusal codes, their sentences, and the shared refusal object (SAD §4 "Refusals", H-036 V-12).

A service refuses a request by calling `refuse(...)`. That does three things, in this order:
  1. writes one `refusal` entry to the audit log and commits it (every refusal is audited, CR-001);
  2. builds the shared refusal object the pages read (`Refusal`: code, sentence, anchor, ...);
  3. raises `Refused`, which stops the service function BEFORE it changes anything else.

So a refusal never changes data except for its own audit entry. The caller must run every check
before its first write.

The sentences are ux.md §5, word for word. A few sentences ux.md does not give (marked PROPOSED
below) are the persona's own plain wording, listed in backend.md Open Questions.
"""

from dataclasses import dataclass, field
from typing import NoReturn

HTTP_STATUS = {
    "FORBIDDEN": 403,
    "VALIDATION": 422,
    "REASON_REQUIRED": 422,
    "ALREADY_DECIDED": 409,
    "VERSION_MISMATCH": 409,
    "GATE_INCOMPLETE": 409,
    "QUOTE_CHECK_FAILED": 409,
    "WHO_FILES_REQUIRED": 422,
    "BUSINESS_DAY_RULE_REQUIRED": 422,
    "DEMO_ROW_NOT_APPROVABLE": 409,
    "ACK_REQUIRED": 409,
    "RUN_ACTIVE": 409,
    "RUN_NOT_ACTIVE": 409,
    "RUN_STAGE_RUNNING": 409,
    "RUN_NOT_FAILED": 409,
    "RETRY_LIMIT_REACHED": 409,
    "RETRY_NOT_ALLOWED": 409,
    "EVALUATION_NOT_DECIDABLE": 409,    # DL-61, H-105
}

# (code, context) → sentence. `{…}` are values the service fills in. The context is "" when a
# code has one sentence.
SENTENCES = {
    ("FORBIDDEN", ""): ("This page is for the compliance specialist. You are signed in as the "
                        "General Partner, so you can view the published calendar only."),
    ("DEMO_ROW_NOT_APPROVABLE", ""): (
        "This rule can't be approved. The quote is genuine, but it doesn't say what this rule "
        "claims, so there's no legal basis for it. Reject it and add a short reason, for example "
        "\"Quote doesn't support the rule\". Your attempt has been recorded in the audit trail."),
    ("QUOTE_CHECK_FAILED", ""): (
        "This rule failed the quote check: its quote does not appear word for word in paragraph "
        "{para_id}. It cannot be approved. Reject it with a reason."),
    ("ALREADY_DECIDED", "rule"): ("This rule was already decided, so your decision was not "
                                  "recorded. The page now shows the decision that stands."),
    ("ALREADY_DECIDED", "answer"): ("This answer was already decided, so your decision was not "
                                    "recorded. The page now shows the decision that stands."),
    ("REASON_REQUIRED", "reject_rule"): "Write a reason to reject this rule.",
    ("REASON_REQUIRED", "approve_flag"): ("The AI checker flagged this rule. Write a reason to "
                                          "approve it despite the flag."),
    ("REASON_REQUIRED", "g2_applies"): ("Write a reason. The General Partner will read it as the "
                                        "explanation for this entry."),
    ("REASON_REQUIRED", "g2_does_not_apply"): ("Write a reason. It is kept in the audit log; the "
                                               "General Partner will not see it."),
    ("REASON_REQUIRED", "abandon"): "Write a reason to abandon this review.",
    ("REASON_REQUIRED", "decline"): ("Write what needs to change before this calendar can be "
                                     "published."),
    ("BUSINESS_DAY_RULE_REQUIRED", ""): (
        "Choose what happens if the deadline falls on a weekend or holiday to approve this rule: "
        "move to the following working day, move to the preceding working day, or keep the date."),
    ("WHO_FILES_REQUIRED", ""): ("The source does not say who files this. Choose a filing party, "
                                 "or 'Not known', to approve the rule."),
    ("GATE_INCOMPLETE", "g1"): ("{x} rules are still undecided. Decide every rule before you "
                                "finish checking."),
    # PROPOSED: ux.md gives only the plural; these two are the same sentence for one item.
    ("GATE_INCOMPLETE", "g1_one"): ("1 rule is still undecided. Decide every rule before you "
                                    "finish checking."),
    ("GATE_INCOMPLETE", "g2"): ("{x} answers are still undecided, {u} of them where AI can't "
                                "tell. Decide every answer before you finish."),
    ("GATE_INCOMPLETE", "g2_one"): ("1 answer is still undecided, {u} of them where AI can't "
                                    "tell. Decide every answer before you finish."),
    ("ACK_REQUIRED", "unticked"): ("Tick the box to confirm you have read the rejected rules and "
                                   "the unused paragraphs. Then publish again."),
    ("ACK_REQUIRED", "changed"): ("The lists of rejected rules or unused paragraphs are not the "
                                  "ones shown when you ticked the box. Read the lists above and "
                                  "tick the box again."),
    ("VERSION_MISMATCH", ""): ("This review has moved on since the page was opened. The page now "
                               "shows where it is. Check it, then try again if you still need "
                               "to."),
    ("RUN_ACTIVE", ""): ("Review {n} is still in progress, so a new review can't start. Finish "
                         "it, or abandon it at its step, first."),
    ("RUN_NOT_ACTIVE", ""): ("This review has ended ({status}), so it cannot take more "
                             "decisions. Start a new review from Filing rules."),
    ("RUN_STAGE_RUNNING", "working"): ("AI is still working on step {k}, so this cannot be done "
                                       "yet. It finishes by itself; follow it on the review "
                                       "status page."),
    ("RUN_STAGE_RUNNING", "dates"): ("The dates are still being worked out, so this cannot be "
                                     "done yet. It finishes by itself; follow it on the review "
                                     "status page."),
    # PROPOSED: ux.md covers only "AI is still working". This is the other case in the SAD's
    # code meaning: the review is at a different gate from the one the request belongs to.
    ("RUN_STAGE_RUNNING", "other_gate"): ("This step is not open for decisions right now. The "
                                          "review status page shows where the review is."),
    ("RUN_NOT_FAILED", ""): ("This review has not failed, so there is nothing to retry. The page "
                             "now shows where it is."),
    ("RETRY_LIMIT_REACHED", ""): ("Step {k} has already been tried again once and failed again. "
                                  "Start a new review from Filing rules."),
    # RETRY_NOT_ALLOWED has five sentences, one per reason (ux.md §5; H-094). The context is the
    # reason: three are the stored failure reasons, two are not failures (an evaluation run, a newer
    # run). Retry (B13b) is not built, so nothing calls these yet; B13b passes the context.
    # The first four end by sending the specialist to a new review. `call limit` must NOT: the call
    # limit counts an activity's real calls across both databases (EC-R10), so a new review would
    # reach the same limit and the usual advice would send the specialist in a circle.
    ("RETRY_NOT_ALLOWED", "cost cap"): (
        "This step can't be tried again, because the review reached its cost limit. Start a new "
        "review from Filing rules."),
    ("RETRY_NOT_ALLOWED", "calendar generation"): (
        "This step can't be tried again, because the dates could not be worked out, and trying "
        "again would give the same result. Start a new review from Filing rules."),
    ("RETRY_NOT_ALLOWED", "evaluation run"): (
        "This step can't be tried again, because this is an evaluation run. Start a new review "
        "from Filing rules."),
    ("RETRY_NOT_ALLOWED", "newer run"): (
        "This step can't be tried again, because a newer review has been started. Start a new "
        "review from Filing rules."),
    ("RETRY_NOT_ALLOWED", "call limit"): (
        "This step can't be tried again, because the limit on real model calls was reached. A new "
        "review would reach the same limit. Ask the operator to review the limit."),
    # DL-61 (H-105): a person decides, finishes a gate, publishes or declines on an evaluation review.
    # ux.md §5, final (2026-11-24). One sentence, in this one place. No internal terms in it.
    ("EVALUATION_NOT_DECIDABLE", ""): (
        "This review is part of the evaluation. The evaluation script makes its decisions, so it can't "
        "be decided here. Nothing was saved."),
    ("VALIDATION", "no_answer"): "Choose an answer first, then use its button. Nothing was saved.",
    ("VALIDATION", "field"): ("Part of this form was not valid ({field}), so nothing was saved. "
                              "Check the form and try again."),
}


def sentence(code: str, context: str = "", **values) -> str:
    """The plain sentence for a refusal, with `{…}` values filled in."""
    return SENTENCES[(code, context)].format(**values)


@dataclass(frozen=True)
class Refusal:
    """The shared refusal object every page reads (H-036 V-12, frontend.md §10.1).

    `anchor` says where on the page the refusal belongs ("row-3", "verdict-2", "start", "ack",
    "decline-reason", "decision", "abandon"), or is None for a refusal about the whole page.
    `typed` holds the text the person typed, by form field name, so the page can show it again.
    """
    code: str
    sentence: str
    anchor: str | None = None
    target_label: str | None = None         # "rule 3"
    short: str | None = None                # the short top line (RUN_ACTIVE)
    link_text: str | None = None            # the link under it (RUN_ACTIVE)
    typed: dict = field(default_factory=dict)

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.code]


class Refused(Exception):
    """Raised by `refuse`. The web layer shows the same page again with `refusal` on it."""

    def __init__(self, refusal: Refusal):
        super().__init__(refusal.code)
        self.refusal = refusal


class NotFound(Exception):
    """A review, rule, answer or calendar that does not exist: the web layer shows the 404 page."""


def refuse(conn, code: str, context: str = "", *, actor: str, fund_id: str, run_id: str | None = None,
           subject_id: str | None = None, anchor: str | None = None,
           target_label: str | None = None, short: str | None = None,
           link_text: str | None = None, typed: dict | None = None, **values) -> NoReturn:
    """Audit the refusal, then raise `Refused`. Call this BEFORE the first write of a request."""
    from backend.services.audit import write_audit  # here: audit stays free of this module

    text = sentence(code, context, **values)
    write_audit(conn, fund_id=fund_id, actor=actor, event_type="refusal", run_id=run_id,
                subject_id=subject_id, refusal_code=code,
                reason=f"{context}: {text}" if context else text)
    conn.commit()
    raise Refused(Refusal(code=code, sentence=text, anchor=anchor, target_label=target_label,
                          short=short, link_text=link_text, typed=dict(typed or {})))
