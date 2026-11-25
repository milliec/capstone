"""Checks several services share (SAD §4 "Transitions and guards").

Each one refuses with the shared refusal object (refusals.refuse) or returns quietly. They are
called BEFORE a service writes anything, in this order: a person decides on an evaluation review
(EVALUATION_NOT_DECIDABLE, DL-61: first, straight after the role check, so the sentence is the same in
every state), the run has ended (RUN_NOT_ACTIVE), the phase is wrong (RUN_STAGE_RUNNING), the page is
stale (VERSION_MISMATCH). The first that applies wins, because it is the most useful thing to tell the
person.

`**where` is the refusal's place on the page (anchor, target_label, subject_id, typed).
"""

from backend.services.auth import EVALUATION_ACTOR
from backend.services.refusals import refuse


def require_decidable_by(conn, run: dict, actor: str, **where) -> None:
    """EVALUATION_NOT_DECIDABLE (DL-61, H-105): on an evaluation run only `specialist-eval` may decide.

    Used by the six requests that change a review's decisions: the row decision, G1 complete, the
    verdict decision, G2 complete, publish and decline. NOT by abandon, and not by reading a page.

    It keys on the ACTOR, never on the route or the page: the scripted gates call these same service
    functions as `specialist-eval` and must pass, and nobody can sign in as `specialist-eval`.
    The role check (FORBIDDEN) is the web layer's and has already run; this is the first check a
    service makes.
    """
    from backend.services.runs import is_evaluation_run  # here: runs imports this module

    if is_evaluation_run(run) and actor != EVALUATION_ACTOR:
        refuse(conn, "EVALUATION_NOT_DECIDABLE", actor=actor, fund_id=run["fund_id"],
               run_id=run["run_id"], **where)


def require_active(conn, run: dict, actor: str, **where) -> None:
    """RUN_NOT_ACTIVE: any decision, abandon, publish or decline on an ended run (rule 4)."""
    if run["status"] != "ACTIVE":
        refuse(conn, "RUN_NOT_ACTIVE", actor=actor, fund_id=run["fund_id"], run_id=run["run_id"],
               status=run["status_words"], **where)


def require_phase(conn, run: dict, phase: str, actor: str, **where) -> None:
    """RUN_STAGE_RUNNING: the run is not at the gate this request belongs to (DL-46).

    While AI or code works, the sentence says so; at a different gate it says the step is not
    open for decisions (a PROPOSED sentence, see refusals.py).
    """
    if run["phase"] == phase:
        return
    from backend.services.runs import STOPPED_STEP  # here: runs imports this module

    if run["phase"].endswith("_RUNNING"):
        context = "dates" if run["phase"] == "C_RUNNING" else "working"
        refuse(conn, "RUN_STAGE_RUNNING", context, actor=actor, fund_id=run["fund_id"],
               run_id=run["run_id"], k=STOPPED_STEP[run["phase"]], **where)
    refuse(conn, "RUN_STAGE_RUNNING", "other_gate", actor=actor, fund_id=run["fund_id"],
           run_id=run["run_id"], **where)


def require_at_a_gate(conn, run: dict, actor: str, **where) -> None:
    """RUN_STAGE_RUNNING for abandon: allowed only in AT_G1, AT_G2 or AT_G3 (rule 8)."""
    if run["phase"].startswith("AT_G"):
        return
    require_phase(conn, run, "AT_G1", actor, **where)   # always refuses: the phase is *_RUNNING


def require_version(conn, run: dict, run_version: int, actor: str, **where) -> None:
    """VERSION_MISMATCH: the run has moved on since the page was shown."""
    if run_version != run["run_version"]:
        refuse(conn, "VERSION_MISMATCH", actor=actor, fund_id=run["fund_id"],
               run_id=run["run_id"], **where)
