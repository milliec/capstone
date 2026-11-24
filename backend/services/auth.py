"""Mock sign-in and the role check (SAD §4 "Sign-in and secrets", CR-004, SD A-5).

Two fixed identities, no password. The signed session cookie holds only the identity ID; the role
is looked up here on every request. This is a demo mechanism, not access control (AM §3).

This file is real code, not a stub: the role check is a check, so it lives in the service layer.
"""

import sqlite3
from dataclasses import dataclass

from backend.services import FUND_ID
from backend.services.audit import write_audit
from backend.services.refusals import Refusal, sentence


@dataclass(frozen=True)
class Identity:
    identity_id: str   # stored in the cookie and written to the audit log as the actor
    role: str          # "specialist" or "gp"
    label: str         # ux.md §1.3 item 4
    line: str          # the small line under the label


IDENTITIES = {
    "specialist-1": Identity("specialist-1", "specialist", "Compliance specialist",
                             "Demo with mock data"),
    "gp-1": Identity("gp-1", "gp", "General Partner / Fund Manager",
                     "Bramblegate Partners · view only · demo with mock data"),
}

# The identity the scripted evaluation gates act as (EC-R2, DL-59, H-096 PR 3). It is kept OUT of
# IDENTITIES on purpose: the sign-in page lists IDENTITIES, and `sign_in` and the session cookie only
# accept IDENTITIES, so `specialist-eval` can never be chosen or forged from the browser. Only code
# that passes it as `started_by` / `actor` (the evaluation run starter) uses it.
EVALUATION_ACTOR = "specialist-eval"
SCRIPTED_IDENTITIES = {
    EVALUATION_ACTOR: Identity(EVALUATION_ACTOR, "specialist", "Evaluation script",
                               "Scripted gates · evaluation runs only"),
}


class Forbidden(Exception):
    """Raised when the signed-in role may not do this. The web layer shows the 403 page."""

    def __init__(self, identity: Identity, refusal: Refusal):
        super().__init__(refusal.code)
        self.identity = identity
        self.refusal = refusal


def sign_in(identity_id: str) -> Identity | None:
    """Return the identity for a sign-in choice, or None if it is not one of the two."""
    return IDENTITIES.get(identity_id)


def identity_from_session(session: dict) -> Identity | None:
    """Read the identity from the (already signature-checked) session cookie."""
    return IDENTITIES.get(session.get("identity_id", ""))


def require_role(conn: sqlite3.Connection, identity: Identity, role: str, path: str) -> None:
    """Refuse with FORBIDDEN, written to the audit log, unless `identity` has `role` (CR-004).

    Called BEFORE the page looks anything up, so a General Partner always gets 403 on a
    specialist address, whether or not that review exists (ux.md §1.7).
    """
    if identity.role == role:
        return
    refusal = Refusal("FORBIDDEN", sentence("FORBIDDEN"))
    write_audit(conn, fund_id=FUND_ID, actor=identity.identity_id, event_type="refusal",
                refusal_code=refusal.code, reason=f"{role} page: {path}")
    conn.commit()
    raise Forbidden(identity, refusal)
