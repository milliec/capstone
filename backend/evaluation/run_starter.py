"""The evaluation run starter, PR 4a (H-097, sad.md EC-R2, EC-R7, EC-R10, DL-59).

    .venv/bin/python -m backend.evaluation run            # the plan only: sends nothing, creates nothing
    .venv/bin/python -m backend.evaluation run --go       # the plan, a typed confirmation, then the run

What 4a does, in order:
  1. EVERY REFUSAL FIRST, before any prompt. Stand-in mode (T-MODE-1), an activity other than
     `evaluation`, no key or no model ID, the planted row switched on (EC-R7), an unreadable call count,
     too little room under the 63-call cap, or a review already in progress.
  2. THE PLAN: the commit, the three models, the projected calls and what is used of the 63.
  3. THE TYPED CONFIRMATION: you type `evaluate <commit> <worst-case calls>` exactly. Anything else, or
     no one to ask (piped input), cancels and sends nothing.
  4. STARTS THE RUN as `specialist-eval` (the same `start_run` the page uses) and lets Stage A finish.
  5. CHECKS STAGE A'S TRACE, and ends the run if it finds a 400, a length stop or an invalid answer.
  6. GRADES STAGE A, EXPORTS THE TRACE (D4), and STOPS AT G1. It makes no gate decision: the scripted
     G1, G2 and G3 are PR 4b.

Exit codes follow the spike command: 0 the run reached G1 clean (or the plan was shown), 1 it was stopped
or failed, 2 it refused or was not confirmed.
"""

import argparse
import re
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from backend.db.connection import connect, init_db
from backend.domain import sources
from backend.evaluation import golden, trace_export
from backend.evaluation.report import DEFAULT_OUT, save_report
from backend.evaluation.stage_a import NotGradable, evaluate_stage_a
from backend.runtime import harness, model_settings, spike
from backend.services import FUND_ID, runs
from backend.services.auth import EVALUATION_ACTOR
from backend.services.refusals import Refused
from backend.settings import ROLES, ROOT, SettingsError, load_settings

SPIKE_DB = spike.SPIKE_DB        # a module name so a test can point it away from the real data/spike.db
ACTIVITY = "evaluation"
# The most requests one run has needed (19 in the first web-app run, DL-59). The plan is checked against
# the cap with this number, not with the expected one, because the cap has no room for a surprise.
WORST_CASE_CALLS = 19


class StarterRefused(Exception):
    """A normal, expected refusal: the plan could not be made, so nothing was sent."""


REFUSALS = (StarterRefused, SettingsError, model_settings.ModelNotSet, model_settings.KeyNotSet)


def expected_calls() -> int:
    """One extraction per PRIMARY source document (the secondary one is only read by the verifier), then one
    verification and one judgement per drafted row. A clean run drafts the answer key's rows (the planted
    row is off), so the key gives the count: 5 + 6 + 6."""
    primary = [d for d in sources.list_documents() if d["type"] == "primary"]
    return len(primary) + 2 * len(golden.load_golden_set().rows)


@dataclass(frozen=True)
class RunPlan:
    commit: str
    models: dict          # role -> model ID
    expected: int
    worst_case: int
    used: int             # real evaluation calls already counted, over both database files
    cap: int
    breakdown: str        # for example "spike/spike.db 0 (no file yet), data/app.db 0"

    @property
    def confirm_text(self) -> str:
        return f"evaluate {self.commit} {self.worst_case}"


def _active_review(settings) -> str | None:
    """The ID of a review already in progress in the app's database, read-only. A database that does not
    exist yet holds none, and is NOT created here."""
    path = Path(settings.database_path)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return None
    conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT run_id FROM runs WHERE fund_id = ? AND status = 'ACTIVE'",
                           (FUND_ID,)).fetchone()
    except sqlite3.OperationalError as error:
        if "no such table" not in str(error):
            raise
        return None
    finally:
        conn.close()
    return row[0] if row else None


def build_plan(settings, *, spike_db, commit: str, demo_planted_row: bool = False) -> RunPlan:
    """The plan, or a refusal. Reads only: no database is created and no model is called."""
    if demo_planted_row:                                                              # EC-R7
        raise StarterRefused("an evaluation run cannot start with the planted row switched on (EC-R7).")
    if settings.agents_mode != "real":                                                # T-MODE-1
        raise StarterRefused("stand-in mode: an evaluation run needs AGENTS_MODE=real, and none is "
                             "started in stand-in mode (T-MODE-1).")
    if settings.spend_activity != ACTIVITY:
        raise StarterRefused(f"SPEND_ACTIVITY must be '{ACTIVITY}' for an evaluation run; it is "
                             f"'{settings.spend_activity}'.")
    model_settings.require_api_key(settings)
    models = {role: model_settings.role_settings(settings, role).model for role in ROLES}
    try:
        count = harness.count_real_calls(ACTIVITY, spike.counted_databases(settings, Path(spike_db)))
    except (sqlite3.Error, OSError) as error:        # an unknown count is treated as "no room" (DL-59)
        raise StarterRefused(f"the real-call count cannot be read ({error}), so no run starts.") from error
    cap = harness.CALL_CAPS[ACTIVITY]
    if count.total + WORST_CASE_CALLS > cap:
        raise StarterRefused(f"{count.total} of {cap} evaluation calls are used ({count.breakdown()}); "
                             f"this run may need up to {WORST_CASE_CALLS}, which would pass the cap "
                             "(EC-R10). A further run needs a recorded operator decision.")
    active = _active_review(settings)
    if active:
        raise StarterRefused(f"review {active} is in progress. Finish or abandon it first.")
    return RunPlan(commit=commit, models=models, expected=expected_calls(), worst_case=WORST_CASE_CALLS,
                   used=count.total, cap=cap, breakdown=count.breakdown())


def format_plan(plan: RunPlan, *, go: bool) -> str:
    lines = [
        "EVALUATION RUN PLAN (PR 4a: starts Stage A and stops at G1)",
        f"  Commit         : {plan.commit}{_dirty_note()}",
        "  Models         : " + ", ".join(f"{role} {model}" for role, model in plan.models.items()),
        (f"  Projected calls: {plan.expected} calls expected, {plan.worst_case} at most "
         "(5 extractions + 6 verifications + 6 judgements; Stage A makes 11 of them)"),
        f"  Budget         : {plan.used} of {plan.cap} evaluation calls used ({plan.breakdown})",
        "  Acts as        : specialist-eval; the planted row is off; AGENTS_MODE real",
        "  Stops          : on a 400, a length stop or an invalid answer, and always at G1",
    ]
    lines.append("" if go else "To start, run it again with --go. You will be asked to type the "
                 f"confirmation: {plan.confirm_text}")
    return "\n".join(lines)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _commit() -> str:
    try:
        return _git("rev-parse", "--short", "HEAD")
    except (OSError, subprocess.CalledProcessError) as error:
        raise StarterRefused("the commit cannot be read, and EC-R1 needs it named.") from error


def _dirty_note() -> str:
    try:
        return "  (UNCOMMITTED CHANGES: a run on this code cannot be repeated on the same commit)" \
            if _git("status", "--porcelain") else ""
    except (OSError, subprocess.CalledProcessError):
        return ""


_HTTP_400 = re.compile(r"^HTTP 400\b")


def stop_reasons(conn: sqlite3.Connection, run_id: str) -> list[str]:
    """What in the run's trace means "stop": a 400 (including one CrewAI's silent repeat got past, which
    shows as a 400 line and then an answered one), a length stop, an invalid answer. Other provider errors
    (429, 5xx, timeouts) belong to the DL-43 retry, and a unit that still fails for them already ends the run."""
    reasons = []
    for t in conn.execute("SELECT unit_id, attempt_n, provider_error, stop_reason, validation_error "
                          "FROM trace WHERE run_id = ? ORDER BY trace_id", (run_id,)):
        where = f"{t['unit_id']} (request {t['attempt_n']})"
        if t["provider_error"] and _HTTP_400.match(t["provider_error"]):
            reasons.append(f"a 400 from the provider on {where}: {t['provider_error']}")
        if t["stop_reason"] == "length":
            reasons.append(f"a length stop on {where}: the answer was cut off")
        if t["validation_error"]:
            reasons.append(f"an invalid answer on {where}: {t['validation_error']}")
    return reasons


def _run_now(function, *args, **kwargs):
    """The stage runs here, in this thread, so the command waits for it (the page uses a background task)."""
    return function(*args, **kwargs)


def _failed_unit_reasons(conn: sqlite3.Connection, run_id: str) -> list[str]:
    return [f"{u['unit_id']} failed: {u['failure_reason']}" for u in conn.execute(
        "SELECT unit_id, failure_reason FROM units WHERE run_id = ? AND status = 'failed'", (run_id,))]


def _execute(settings, plan: RunPlan, out, report_dir: Path) -> int:
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    try:
        try:
            run_id = runs.start_run(conn, settings, _run_now, fund_id=FUND_ID, started_by=EVALUATION_ACTOR,
                                    demo_planted_row=False, demo_fail_step1=False)
        except Refused as refusal:
            out(f"REFUSED: {refusal.refusal.sentence}")
            return 2
        run = runs.get_run(conn, run_id)
        problems = _failed_unit_reasons(conn, run_id) + stop_reasons(conn, run_id)
        if run["status"] == "ACTIVE" and problems:
            runs.abandon_run(conn, run_id=run_id, run_version=run["run_version"], actor=EVALUATION_ACTOR,
                             reason="Stopped by the evaluation script: " + problems[0][:200])
        _grade(conn, run_id, report_dir, out)
        _export(conn, run_id, settings, report_dir, out)
        out(f"Run {run_id}: {run['status'] if problems else 'ACTIVE'} at {run['phase']}; "
            f"cost US${run['cost_so_far']:.4f}.")
        if problems:
            out("STOPPED, and the run was ended. Why:")
            out("\n".join(f"  - {p}" for p in problems))
            return 1
        out(f"Stopped at G1: PR 4a makes no gate decision (the scripted G1, G2 and G3 are PR 4b). "
            f"Review {run_id} waits at G1; abandon it from the page if you will not continue it.")
        return 0
    finally:
        conn.close()


def _grade(conn, run_id: str, report_dir: Path, out) -> None:
    try:
        json_path, md_path = save_report(evaluate_stage_a(conn, run_id), report_dir)
        out(f"Stage A report saved: {json_path}\n                      {md_path}")
    except NotGradable as error:
        out(f"Stage A was not graded: {error}")


def _export(conn, run_id: str, settings, report_dir: Path, out) -> None:
    result = trace_export.export_trace(conn, run_id, report_dir, secrets=[settings.openai_api_key])
    check = trace_export.check_export(conn, run_id, report_dir)
    out(f"Trace export: {result.records} records, secrets removed: {result.folder}" if check.ok
        else f"TRACE EXPORT FAILED, so the run is reported failed: {check.why}")


def main(argv: list[str] | None = None, *, env=None, spike_db=None, out=print, read_line=input,
         commit: str | None = None, report_dir=None) -> int:
    """The command. `env`, `spike_db`, `out`, `read_line`, `commit` and `report_dir` exist so tests can
    supply their own; the real command uses the defaults."""
    parser = argparse.ArgumentParser(prog="python -m backend.evaluation run", description=__doc__.split("\n")[0])
    parser.add_argument("--go", action="store_true", help="start the run, after you type the confirmation")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="folder for the Stage A report and the export")
    args = parser.parse_args(argv)
    report_dir = Path(report_dir or args.out)
    try:
        settings = load_settings(env)
        plan = build_plan(settings, spike_db=spike_db or SPIKE_DB, commit=commit or _commit())
    except REFUSALS as refusal:
        out(f"REFUSED: {refusal}")                        # before any prompt: never ask to confirm a refusal
        return 2
    out(format_plan(plan, go=args.go))
    if not args.go:
        return 0
    out("THIS WILL SEND UP TO "
        f"{plan.worst_case} REAL REQUESTS (Stage A: 11 expected) AND MAY COST MONEY.")
    try:
        typed = read_line(f"To start, type exactly '{plan.confirm_text}' and press Enter; "
                          "anything else cancels: ")
    except (EOFError, OSError):                            # no one to ask (piped input, a script): no
        typed = ""
    if typed.strip() != plan.confirm_text:
        out("NOT CONFIRMED: nothing was sent.")
        return 2
    out("Starting the run now...")
    return _execute(settings, plan, out, report_dir)


if __name__ == "__main__":
    raise SystemExit(main())
