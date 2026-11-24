"""Grade one finished run from the command line:

    .venv/bin/python -m backend.evaluation RUN-20261121-1            # stage A, and B if it finished
    .venv/bin/python -m backend.evaluation RUN-20261121-1 --stage b  # stage B only
    .venv/bin/python -m backend.evaluation RUN-20261121-1 --no-save  # print only
    .venv/bin/python -m backend.evaluation export RUN-20261121-1     # the trace export (D4)
    .venv/bin/python -m backend.evaluation run                       # the evaluation run starter (plan only)

Reads the database in DATABASE_PATH (the app's own). Starts nothing, calls no model. A miss is a
result, not an error: the exit code is 0 for any report (DL-34: evaluations report, never block).
"""

import argparse
import sys

from backend.db.connection import connect
from backend.evaluation import run_starter, trace_export
from backend.evaluation.report import DEFAULT_OUT, render_markdown, save_report
from backend.evaluation.stage_a import NotGradable, evaluate_stage_a
from backend.evaluation.stage_b import evaluate_stage_b
from backend.settings import load_settings


def _grade(conn, args) -> list[dict]:
    """The reports asked for. With --stage all, stage B is added only when the run finished it;
    otherwise it is skipped with a note (stage A alone is a normal state at G1)."""
    reports = []
    if args.stage in ("a", "all"):
        reports.append(evaluate_stage_a(conn, args.run_id))
    if args.stage == "b":
        reports.append(evaluate_stage_b(conn, args.run_id))
    elif args.stage == "all":
        try:
            reports.append(evaluate_stage_b(conn, args.run_id))
        except NotGradable as error:
            print(f"Stage B skipped: {error}", file=sys.stderr)
    return reports


def _export(argv: list[str]) -> int:
    """`export RUN-ID`: write the run's trace export (D4), then check it against the store.
    Exit 0: written and matching. Exit 1: the run's export is missing or off (the run is reported
    failed, and why is printed). Exit 2: nothing to export (no database, or no such run)."""
    parser = argparse.ArgumentParser(prog="python -m backend.evaluation export",
                                     description="Write a run's trace export (sad.md D4).")
    parser.add_argument("run_id")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="folder for the export")
    parser.add_argument("--off", action="store_true",
                        help="switch the export off: write nothing and report the run failed")
    args = parser.parse_args(argv)
    settings = load_settings()
    if not settings.database_path.exists():
        print(f"Nothing to export: there is no database at {settings.database_path}.",
              file=sys.stderr)
        return 2
    conn = connect(settings.database_path)
    try:
        result = trace_export.export_trace(conn, args.run_id, args.out, enabled=not args.off,
                                           secrets=[settings.openai_api_key])
        check = trace_export.check_export(conn, args.run_id, args.out)
    except NotGradable as error:
        print(f"Nothing to export: {error}", file=sys.stderr)
        return 2
    finally:
        conn.close()
    if check.failed:
        reason = result.why or check.why
        print(f"RUN REPORTED FAILED: {reason}.", file=sys.stderr)
        return 1
    print(f"Exported {result.records} records, secrets removed: {result.folder}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["export"]:
        return _export(argv[1:])
    if argv[:1] == ["run"]:                      # PR 4a: the evaluation run starter
        return run_starter.main(argv[1:])
    parser = argparse.ArgumentParser(prog="python -m backend.evaluation", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_id")
    parser.add_argument("--stage", choices=("a", "b", "all"), default="all",
                        help="all (default): stage A, then stage B if the run finished it")
    parser.add_argument("--no-save", action="store_true", help="print the report, save nothing")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="folder for saved reports")
    args = parser.parse_args(argv)
    database = load_settings().database_path
    if not database.exists():   # connect() would quietly create an empty file
        print(f"Nothing to grade: there is no database at {database}.", file=sys.stderr)
        return 2
    conn = connect(database)
    try:
        reports = _grade(conn, args)
    except NotGradable as error:
        print(f"Nothing to grade: {error}", file=sys.stderr)
        return 2
    finally:
        conn.close()
    for report in reports:
        print(render_markdown(report))
        if not args.no_save:
            json_path, md_path = save_report(report, args.out)
            print(f"Saved: {json_path}\n       {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
