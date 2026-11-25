"""The void rule (EC-R8) and the report for a run that did not finish (H-097, PR 5).

    .venv/bin/python -m backend.evaluation void RUN_ID                  # classify, print, save a report
    .venv/bin/python -m backend.evaluation void RUN_ID --replacement    # this run was the one re-run
    .venv/bin/python -m backend.evaluation void RUN_ID --decision "..." # the operator's recorded decision

READ-ONLY on the database and it calls no model. It only DECIDES what a failed run is; it starts nothing.

THE RULE, written before any evaluation run existed so that it cannot be used to throw away an unwelcome
result (EC-R8):
  * A run is VOIDED only if it ended FAILED and EVERY failed unit's reason is `model service` or
    `stage time limit` (the provider's fault, after the one automatic retry, DL-43).
  * Every other reason is a FINDING, never voided: invalid output, cost cap, service restarted,
    calendar generation, unexpected error, call limit (DL-58, DL-59). So are demo failure and a run that
    FAILED with no failed unit recorded at all: when the cause is unknown the rule does not void.
  * All failed units count, from every stage attempt. The strict reading voids less, which is the safe
    side for a rule that must not look like it was bent.
  * A voided run is re-run ONCE on the same commit, but only after the operator has recorded a decision
    to spend the calls (DL-59: the voided run's calls stay in the 63). Without that decision the run is
    not replaced and the report says the cycle has fewer than three runs, every criterion INCOMPLETE.
  * If the replacement also fails for a model-service reason it is a MISS with the reason
    "model service", and it is not re-run again.
  * Every voided run is listed with its reasons and its cost; voided runs count towards model spend.
  * The `I-1` and injection copy cases are not units, so this rule never sees them (EC-R8 point 6, PR 6).
"""

import argparse
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from backend.db.connection import connect
from backend.evaluation.report import DEFAULT_OUT, save_report
from backend.settings import load_settings

VOIDABLE_REASONS = frozenset({"model service", "stage time limit"})
# The model-dependent criteria of one run (EC-R1). A run that did not finish measured none of them.
MODEL_CRITERIA = ("EC-001", "EC-002", "EC-003", "EC-004", "EC-005", "EC-006", "EC-007",
                  "EC-010", "EC-012", "EC-021")

# What a run is, once classified.
COMPLETED, ACTIVE, ABANDONED, VOIDED, FINDING = "completed", "active", "abandoned", "voided", "finding"
# What to do about it.
NOTHING, RE_RUN, NEEDS_DECISION, MISS = "nothing", "re_run", "needs_decision", "miss"


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    status: str                  # the run's own status
    kind: str                    # completed | active | abandoned | voided | finding
    reasons: tuple[str, ...]     # the distinct failure reasons of the failed units, sorted
    failed_units: int
    cost_usd: float
    calls: int
    why: str                     # one sentence, for the report


@dataclass(frozen=True)
class Next:
    action: str                  # nothing | re_run | needs_decision | miss
    sentence: str
    criteria_status: str | None  # "incomplete" or "miss" for each model criterion; None when graded normally
    miss_reason: str | None = None


@dataclass
class CycleNote:
    """What the cycle report says about the runs that did not finish."""
    voided: list[RunOutcome] = field(default_factory=list)
    voided_cost_usd: float = 0.0
    runs_in_cycle: int = 0
    sentence: str = ""


def classify(conn: sqlite3.Connection, run_id: str) -> RunOutcome:
    run = conn.execute("SELECT status, cost_so_far FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if run is None:
        raise LookupError(f"There is no run {run_id}.")
    reasons = sorted({r["failure_reason"] or "(none recorded)" for r in conn.execute(
        "SELECT failure_reason FROM units WHERE run_id = ? AND status = 'failed'", (run_id,))})
    failed = conn.execute("SELECT COUNT(*) FROM units WHERE run_id = ? AND status = 'failed'",
                          (run_id,)).fetchone()[0]
    calls = conn.execute("SELECT COUNT(*) FROM trace WHERE run_id = ?", (run_id,)).fetchone()[0]
    status, cost = run["status"], float(run["cost_so_far"] or 0)

    def outcome(kind, why):
        return RunOutcome(run_id, status, kind, tuple(reasons), failed, cost, calls, why)

    if status == "COMPLETED":
        return outcome(COMPLETED, "the run went through G3")
    if status == "ACTIVE":
        return outcome(ACTIVE, "the run is still in progress: nothing to classify yet")
    if status != "FAILED":                       # ABANDONED or DECLINED: a person or the script ended it
        return outcome(ABANDONED, f"the run ended {status}, not FAILED: this rule does not apply")
    if not failed:
        return outcome(FINDING, "the run FAILED but no failed unit is recorded, so the cause is unknown "
                                "and the rule does not void it")
    other = [r for r in reasons if r not in VOIDABLE_REASONS]
    if other:
        return outcome(FINDING, "the run FAILED and not only for a model-service reason ("
                                + ", ".join(other) + "): a finding, never voided (EC-R8 point 2)")
    return outcome(VOIDED, "every failed unit failed for a model-service reason ("
                           + ", ".join(reasons) + "): voided (EC-R8 point 1)")


def next_step(outcome: RunOutcome, *, is_replacement: bool = False, decision: str | None = None) -> Next:
    """What follows from the classification. `decision` is the operator's recorded decision to spend
    the calls on a replacement (DL-59); `is_replacement` says this run was already the re-run."""
    if outcome.kind in (COMPLETED, ACTIVE, ABANDONED):
        return Next(NOTHING, outcome.why, None)
    if outcome.kind == FINDING:
        return Next(NOTHING, "Reported as a finding: every model criterion it could not measure is a "
                    "MISS with the failure reason.", "miss")
    if is_replacement:
        return Next(MISS, "The replacement also failed for a model-service reason: it counts as a MISS "
                    "with the reason \"model service\" and is not re-run again (EC-R8 point 3).",
                    "miss", "model service")
    if not (decision or "").strip():
        return Next(NEEDS_DECISION, "Voided. It is NOT replaced: a replacement is a call beyond the "
                    "cap of 63 and needs the operator's recorded decision first (DL-59, EC-R10 point 3). "
                    "The cycle has fewer than three runs, and every criterion is INCOMPLETE, not a pass.",
                    "incomplete")
    return Next(RE_RUN, "Voided. Re-run it ONCE on the same commit; the operator's decision is "
                f"recorded: {decision.strip()}", "incomplete")


def cycle_note(outcomes: list[RunOutcome], *, wanted: int = 3) -> CycleNote:
    """The runs of one cycle, in order, as outcomes. Lists the voided ones with reasons and cost."""
    note = CycleNote(voided=[o for o in outcomes if o.kind == VOIDED])
    note.voided_cost_usd = sum(o.cost_usd for o in note.voided)
    note.runs_in_cycle = sum(1 for o in outcomes if o.kind in (COMPLETED, FINDING))
    note.sentence = (f"{note.runs_in_cycle} of {wanted} runs count in this cycle."
                     + (" The cycle has fewer than three runs: every criterion is incomplete, not a pass."
                        if note.runs_in_cycle < wanted else ""))
    return note


def evaluate_failed_run(conn: sqlite3.Connection, run_id: str, *, is_replacement: bool = False,
                        decision: str | None = None) -> dict:
    """The report for a run that did not finish, as plain data. Never raises for a failed run."""
    outcome = classify(conn, run_id)
    step = next_step(outcome, is_replacement=is_replacement, decision=decision)
    run = dict(conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone())
    status = step.criteria_status
    return {
        "report": "failed-run",
        "run": {k: run[k] for k in ("run_id", "fund_id", "status", "phase", "agents_mode",
                                    "spend_activity", "demo_planted_row", "started_at")},
        "counts_for_cycle": outcome.kind == FINDING,
        "does_not_count_because": [] if outcome.kind == FINDING else [outcome.why],
        "outcome": outcome.kind,
        "why": outcome.why,
        "failure_reasons": list(outcome.reasons),
        "failed_units": outcome.failed_units,
        "cost_usd": outcome.cost_usd,
        "calls_in_trace": outcome.calls,
        "next_step": step.action,
        "next_step_sentence": step.sentence,
        "miss_reason": step.miss_reason or (outcome.reasons[0] if status == "miss" and outcome.reasons else None),
        "criteria": [{"id": c, "status": status} for c in MODEL_CRITERIA] if status else [],
    }


def render_markdown(report: dict) -> str:
    run = report["run"]
    lines = ["# Report for a run that did not finish", "",
             f"- Run: `{run['run_id']}` ({run['fund_id']}), status {run['status']}, phase {run['phase']}",
             f"- Outcome: **{report['outcome'].upper()}**: {report['why']}",
             (f"- Failure reasons: {', '.join(report['failure_reasons']) or '(none recorded)'} "
              f"({report['failed_units']} failed units)"),
             (f"- Cost: US${report['cost_usd']:.4f} over {report['calls_in_trace']} trace lines "
              "(counts towards model spend, EC-R6)"),
             f"- What follows: {report['next_step_sentence']}"]
    if report["miss_reason"] and report["criteria"] and report["criteria"][0]["status"] == "miss":
        lines.append(f"- Reason shown with each miss: `{report['miss_reason']}`")
    if report["criteria"]:
        lines += ["", "| Criterion | Status |", "|---|---|"]
        lines += [f"| {c['id']} | {c['status'].upper()} |" for c in report["criteria"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, *, out=print) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.evaluation void", description=__doc__.split("\n")[0])
    parser.add_argument("run_id")
    parser.add_argument("--replacement", action="store_true", help="this run was itself the re-run of a voided one")
    parser.add_argument("--decision", default=None, help="the operator's recorded decision to spend the calls")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)
    database = load_settings().database_path
    if not Path(database).exists():                 # connect() would quietly create an empty file
        print(f"Nothing to classify: there is no database at {database}.", file=sys.stderr)
        return 2
    conn = connect(database)
    try:
        report = evaluate_failed_run(conn, args.run_id, is_replacement=args.replacement, decision=args.decision)
    except LookupError as error:
        print(f"Nothing to classify: {error}", file=sys.stderr)
        return 2
    finally:
        conn.close()
    out(render_markdown(report))
    if not args.no_save:
        json_path, md_path = save_report(report, args.out)
        out(f"Saved: {json_path}\n       {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
