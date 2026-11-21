"""Grade one finished stage A run from the command line:

    .venv/bin/python -m backend.evaluation RUN-20261121-1            # print and save
    .venv/bin/python -m backend.evaluation RUN-20261121-1 --no-save  # print only

Reads the database in DATABASE_PATH (the app's own). Starts nothing, calls no model. A miss is a
result, not an error: the exit code is 0 for any report (DL-34: evaluations report, never block).
"""

import argparse
import sys

from backend.db.connection import connect
from backend.evaluation.report import DEFAULT_OUT, render_markdown, save_report
from backend.evaluation.stage_a import NotGradable, evaluate_stage_a
from backend.settings import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.evaluation", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_id")
    parser.add_argument("--no-save", action="store_true", help="print the report, save nothing")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="folder for saved reports")
    args = parser.parse_args(argv)
    database = load_settings().database_path
    if not database.exists():   # connect() would quietly create an empty file
        print(f"Nothing to grade: there is no database at {database}.", file=sys.stderr)
        return 2
    conn = connect(database)
    try:
        report = evaluate_stage_a(conn, args.run_id)
    except NotGradable as error:
        print(f"Nothing to grade: {error}", file=sys.stderr)
        return 2
    finally:
        conn.close()
    print(render_markdown(report))
    if not args.no_save:
        json_path, md_path = save_report(report, args.out)
        print(f"Saved: {json_path}\n       {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
