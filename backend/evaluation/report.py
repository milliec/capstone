"""The Stage A and Stage B reports: readable text, and saved files that are never overwritten (US-013 c5).

One report per grading, keyed by run ID: `<out>/<run_id>/stage-<a|b>-report-<n>.json` and `.md`, with n
counting up from 1, separately for each stage. Grading the same run again makes report 2, never an edit of report 1 (EC-R1a:
every report is kept). The export of the trace is separate (D4) and not built yet.
"""

import json
from pathlib import Path

from backend.settings import ROOT

DEFAULT_OUT = ROOT / "project-context" / "2.build" / "logs"

_WORDS = {"pass": "PASS", "miss": "MISS", "incomplete": "INCOMPLETE (nothing missed, part not tested)",
          "not_tested": "NOT TESTED", "for_operator": "FOR THE OPERATOR"}


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict) -> str:
    run = report["run"]
    stage = report["report"].removeprefix("stage-").upper()
    lines = [f"# Stage {stage} report", ""]
    if not report["counts_for_cycle"]:
        lines += [f"> **{reason}**" for reason in report["does_not_count_because"]] + [""]
    mode = f"- Agents mode: `{run['agents_mode']}`; spend activity: "
    mode += f"{run['spend_activity'] or '(none)'}; planted-row switch: "
    mode += f"{'ON' if run['demo_planted_row'] else 'off'} (EC-R7)"
    if stage == "A":
        rows = f"- Rows drafted by the extractor: {report['rows_drafted_by_the_extractor']}; "
        rows += f"demo rows not graded: {report['demo_rows_not_graded']}"
    else:
        rows = f"- Rows approved at G1: {report['rows_approved_at_g1']}; verdicts stored: "
        rows += f"{report['verdicts_stored']}; model calls in the trace: {report['trace_calls']}"
    counts = "yes" if report["counts_for_cycle"] else "no"
    lines += [
        (f"- Run: `{run['run_id']}` ({run['fund_id']}), status {run['status']}, "
         f"phase {run['phase']}"),
        mode, rows, f"- Counts towards the evaluation cycle: **{counts}**",
        f"- Made: {report['generated_at']}",
        "- One run only. A criterion passes only on 3 of 3 consecutive runs of one commit (EC-R1).",
        "", "## Results", "", "| ID | Criterion | Result | Detail |", "|---|---|---|---|"]
    for c in report["criteria"]:
        lines.append(f"| {c['id']} | {_cell(c['name'])} | {_WORDS[c['status']]} | "
                     f"{_cell(c['summary'])} |")
    for c in report["criteria"]:
        lines += ["", f"### {c['id']}: {c['name']}", "", f"Threshold: {c['threshold']}", ""]
        lines += [f"- {_WORDS[k['status']]}: {k['label']}" + (f" ({k['note']})" if k["note"] else "")
                  for k in c["checks"]]
        if c["findings"]:
            lines += ["", "| Subject | What | Expected | Actual |", "|---|---|---|---|"]
            lines += [f"| {_cell(f['subject'])} | {_cell(f['what'])} | {_cell(f['expected'])} | "
                      f"{_cell(f['actual'])} |" for f in c["findings"]]
    if "copy_cases" in report:
        lines += ["", "## Copy cases (code only, on copies of OBL-01's quote)", "",
                  "| Case | What | Scored under | QN-1 must | Did | OK |", "|---|---|---|---|---|---|"]
        lines += [f"| {c['case_id']} | {_cell(c['description'])} | {c['scored_under']} | "
                  f"{c['expected']} | {c['actual']} | {'yes' if c['ok'] else '**NO**'} |"
                  for c in report["copy_cases"]]
    lines += ["", "## Not in this slice", ""] + [f"- {item}" for item in report["not_in_this_slice"]]
    return "\n".join(lines) + "\n"


def save_report(report: dict, out_dir: Path = DEFAULT_OUT) -> tuple[Path, Path]:
    """Write the JSON and Markdown files for this run, as the next free number. Exclusive
    creation ("x"): if a file somehow exists, the next number is tried; nothing is overwritten."""
    folder = Path(out_dir) / report["run"]["run_id"]
    folder.mkdir(parents=True, exist_ok=True)
    text = render_markdown(report)
    n = 1
    while True:
        json_path = folder / f"{report['report']}-report-{n}.json"
        md_path = folder / f"{report['report']}-report-{n}.md"
        try:
            with open(json_path, "x", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2, ensure_ascii=False)
            with open(md_path, "x", encoding="utf-8") as handle:
                handle.write(text)
        except FileExistsError:
            n += 1
            continue
        return json_path, md_path
