"""The scripted G1, G2 and G3 for an evaluation run, PR 4b (H-097, sad.md EC-R2, DL-60).

An evaluation run makes the three gate decisions BY SCRIPT, as the identity `specialist-eval`, through
the SAME service functions the pages call (`decisions.decide_row`, `gates.complete_g1`,
`decisions.decide_verdict`, `gates.complete_g2`, `publishing.publish_calendar`). No gate is skipped and
no service rule is bypassed: if a service refuses a step, the script stops (see stop_rules.py).

The decisions are the DEMO DECISIONS in `user-stories/README.md` and answer key §5, chosen so the
expected calendar is 22 entries. They are looked up by the answer key's row CODE (OBL-01 ... OBL-06),
found by the paragraph a row cites, never by the row's number: a real model may draft the rows in
another order.

  G1  an approved row gets the business-day rule of KEY §5, and "who files" only where the source is
      silent (DL-39). OBL-03 and OBL-05 are approved WITH A REASON (primary source wins over the
      secondary summary: conflicts C-1 and C-2). Any other row that carries a flag is approved with a
      short generic reason, because the service demands one. A row the key does not expect (an extra
      row), and a row whose quote check did not pass, is REJECTED with a reason: the service would
      refuse to approve the second kind, and G1 cannot finish while a row is undecided.
  G2  a verdict the agent was unsure about is resolved as "applies" (precautionary, design principle
      P-1); every other verdict is CONFIRMED as the agent gave it. The script never overrules the
      agent, so a wrong verdict stays visible for the grader (EC-004).
  G3  publishes, ticking the acknowledgement with exactly the two lists the page itself would show
      (the rejected rules and the paragraphs no rule cites). The publish is real (EC-R2) but is kept
      off the live calendar by the code that reads publications (DL-60, H-099).
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field

from backend.evaluation import golden, grade, stop_rules
from backend.evaluation.stage_a import load_stage_a
from backend.services import decisions, gates, publishing, runs
from backend.services.auth import EVALUATION_ACTOR
from backend.services.refusals import Refused

# KEY §5, "Business-day rule per obligation" and "Who files per obligation". Only OBL-02, 03, 05 and 06
# have a source that is silent about who files; OBL-01 and OBL-04 name their filer, so none is sent.
BUSINESS_DAY_RULE = {"OBL-01": "roll_forward", "OBL-02": "no_roll", "OBL-03": "roll_forward",
                     "OBL-04": "roll_backward", "OBL-05": "roll_backward", "OBL-06": "no_roll"}
WHO_FILES = {"OBL-02": "Fund administrator", "OBL-03": "Fund administrator",
             "OBL-05": "AIFM", "OBL-06": "Tax advisor"}

# The wording of each written reason (they go to the audit log, so they say it was the script).
APPROVE_REASON = {
    "OBL-03": "Primary source wins over the secondary summary (conflict C-1)",
    "OBL-05": "Primary source wins over the secondary summary (conflict C-2)",
}
APPROVE_FLAGGED_REASON = "Evaluation script: flag read, approved as in the demo decisions"
REJECT_EXTRA_REASON = "Evaluation script: this row is not in the answer key"
REJECT_QUOTE_REASON = "Evaluation script: the quote check did not pass"
UNSURE_REASON = {"OBL-04": "Treated as applicable until CNMV registration is confirmed"}
UNSURE_DEFAULT_REASON = "Treated as applicable until confirmed (precautionary, P-1)"


@dataclass
class GateResult:
    """What the script did. `stopped` is empty when the run went through G3."""
    stopped: list[str] = field(default_factory=list)
    approved: int = 0
    rejected: int = 0
    confirmed: int = 0
    resolved_unsure: int = 0
    published: bool = False

    @property
    def ok(self) -> bool:
        return not self.stopped


def decide_g1(conn: sqlite3.Connection, run_id: str) -> tuple[int, int]:
    """Decide every row at G1. Returns (approved, rejected)."""
    _, stored = load_stage_a(conn, run_id)
    matched, _extra = grade.match_rows(stored, golden.load_golden_set())
    code_of = {row.row_id: code for code, row in matched.items()}
    approved = rejected = 0
    for row in stored.rows:
        version = conn.execute("SELECT version FROM rows WHERE row_id = ?", (row.row_id,)).fetchone()[0]
        code = code_of.get(row.row_id)
        # Never approve what the service would refuse (a demo row, a failed quote check), and never
        # approve a row the key does not expect.
        if code is None or row.origin == "demo":
            reject_reason = REJECT_EXTRA_REASON
        elif row.quote_check != "pass":
            reject_reason = REJECT_QUOTE_REASON
        else:
            reject_reason = None
        if reject_reason:
            decisions.decide_row(conn, row_id=row.row_id, version=version, decision="reject",
                                 business_day_rule=None, who_files=None, approve_reason=None,
                                 reject_reason=reject_reason, actor=EVALUATION_ACTOR)
            rejected += 1
            continue
        reason = APPROVE_REASON.get(code) or (APPROVE_FLAGGED_REASON if row.flags else None)
        decisions.decide_row(conn, row_id=row.row_id, version=version, decision="approve",
                             business_day_rule=BUSINESS_DAY_RULE[code], who_files=WHO_FILES.get(code),
                             approve_reason=reason, reject_reason=None, actor=EVALUATION_ACTOR)
        approved += 1
    return approved, rejected


def decide_g2(conn: sqlite3.Connection, run_id: str) -> tuple[int, int]:
    """Answer every verdict at G2. Returns (confirmed, unsure ones resolved as applies)."""
    _, stored = load_stage_a(conn, run_id)
    matched, _extra = grade.match_rows(stored, golden.load_golden_set())
    code_of = {row.row_id: code for code, row in matched.items()}
    confirmed = resolved = 0
    for v in conn.execute("SELECT v.verdict_id, v.version, v.verdict, v.row_id FROM verdicts v "
                          "JOIN rows r ON r.row_id = v.row_id WHERE r.run_id = ? ORDER BY v.rowid",
                          (run_id,)).fetchall():
        if v["verdict"] == "unsure":
            reason = UNSURE_REASON.get(code_of.get(v["row_id"]), UNSURE_DEFAULT_REASON)
            decisions.decide_verdict(conn, verdict_id=v["verdict_id"], version=v["version"],
                                     decision="decide", value="applies", confirm_reason=None,
                                     override_reason=None, decide_reason=reason, actor=EVALUATION_ACTOR)
            resolved += 1
        else:
            decisions.decide_verdict(conn, verdict_id=v["verdict_id"], version=v["version"],
                                     decision="confirm", value=v["verdict"], confirm_reason=None,
                                     override_reason=None, decide_reason=None, actor=EVALUATION_ACTOR)
            confirmed += 1
    return confirmed, resolved


def publish_g3(conn: sqlite3.Connection, run_id: str) -> None:
    """Publish with the two lists the G3 page shows, and the acknowledgement ticked."""
    run = runs.get_run(conn, run_id)
    calendar = conn.execute("SELECT calendar_id FROM calendar_versions WHERE run_id = ? "
                            "ORDER BY rowid DESC", (run_id,)).fetchone()
    if calendar is None:
        raise LookupError(f"Stage C stored no calendar for {run_id}")
    publishing.publish_calendar(
        conn, calendar_id=calendar["calendar_id"], run_version=run["run_version"], acknowledged=True,
        rejected_row_ids=[r["row_id"] for r in decisions.rejected_rows(conn, run)],
        uncited_paragraph_ids=[p["paragraph_id"] for p in decisions.unused_paragraphs(conn, run)],
        actor=EVALUATION_ACTOR)


def end_run(conn: sqlite3.Connection, run_id: str, why: str) -> None:
    """Abandon a run the script is stopping, so no review is left waiting. A run that already ended
    (FAILED, for a failed unit) is left as it is: its reason is already stored."""
    run = runs.get_run(conn, run_id)
    if run["status"] == "ACTIVE":
        runs.abandon_run(conn, run_id=run_id, run_version=run["run_version"], actor=EVALUATION_ACTOR,
                         reason=("Stopped by the evaluation script: " + why)[:300])


def run_gates(conn: sqlite3.Connection, settings, run_id: str, schedule: Callable, out) -> GateResult:
    """Walk G1, G2 and G3. Before every step the stop rules are asked; on any stop the run is ended
    and the result says why. `schedule` runs a stage at once, in this thread (stage B calls the model)."""
    result = GateResult()
    try:
        _walk(conn, settings, run_id, schedule, out, result)
    except Refused as refusal:                                    # a service said no to a scripted step
        result.stopped = [f"a gate step was refused by the service: {refusal.refusal.sentence}"]
    except Exception as error:  # noqa: BLE001  nobody listed this one: it must still end the run and say so
        result.stopped = [f"unexpected error ({type(error).__name__}): {error}"]
    if result.stopped:
        end_run(conn, run_id, result.stopped[0])
    return result


def _walk(conn, settings, run_id, schedule, out, result: GateResult) -> None:
    def stop_if_needed(expect_phase: str) -> bool:
        result.stopped = stop_rules.problems(conn, run_id, expect_phase=expect_phase)
        return bool(result.stopped)

    if stop_if_needed("AT_G1"):
        return
    result.approved, result.rejected = decide_g1(conn, run_id)
    out(f"G1 by script: {result.approved} rules approved, {result.rejected} rejected.")
    if result.approved == 0:
        result.stopped = ["no rule was approved at G1, so there is nothing for Stage B to judge"]
        return
    gates.complete_g1(conn, settings, schedule, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=EVALUATION_ACTOR)
    if stop_if_needed("AT_G2"):                                   # stage B has run, in this thread
        return
    result.confirmed, result.resolved_unsure = decide_g2(conn, run_id)
    out(f"G2 by script: {result.confirmed} verdicts confirmed, "
        f"{result.resolved_unsure} unsure resolved as applies.")
    gates.complete_g2(conn, settings, schedule, run_id=run_id,
                      run_version=runs.get_run(conn, run_id)["run_version"], actor=EVALUATION_ACTOR)
    if stop_if_needed("AT_G3"):                                   # stage C (code only) has run
        return
    publish_g3(conn, run_id)
    result.published = runs.get_run(conn, run_id)["status"] == "COMPLETED"
    if not result.published:
        result.stopped = ["the publish did not complete the run"]
        return
    out("G3 by script: published (kept off the live calendar, DL-60).")
