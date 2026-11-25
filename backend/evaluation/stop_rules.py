"""The evaluation script's STOP RULES (H-097, PR 4a and 4b; sad.md EC-R2, EC-R10, DL-43).

The script is a machine that decides at the three gates for the run it started. Before it takes any
step it asks one question: "Is everything still as it should be?" If not, it stops, the run is ended
with the reason written in the audit log, and the command says why. It never decides past a problem.

What makes the script stop (each one is a finding to report, never something to hide):
  1. A 400 from the provider in the run's trace (including one CrewAI's silent repeat got past, which
     shows as a 400 line followed by an answered one).
  2. A `length` stop: the answer was cut off.
  3. An invalid answer: the model's reply failed the schema.
  4. A failed unit (any reason: model service, stage time limit, call limit, unexpected error ...).
  5. The run is not ACTIVE any more, or is not at the gate the script expects.
Other provider errors (429, 5xx, timeouts) are NOT a stop here: the DL-43 retry owns them, and a unit
that still fails after the retry is rule 4.

(PR 4b adds three more stops in scripted_gates.py, because they come from the gate decisions and not
from the trace: no row approved at G1, a gate step the service refused, and an unexpected error.)
"""

import re
import sqlite3

from backend.services import runs

_HTTP_400 = re.compile(r"^HTTP 400\b")


def stop_reasons(conn: sqlite3.Connection, run_id: str) -> list[str]:
    """Rules 1 to 3: what in the run's trace means "stop"."""
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


def failed_unit_reasons(conn: sqlite3.Connection, run_id: str) -> list[str]:
    """Rule 4: a unit that failed, with its stored reason."""
    return [f"{u['unit_id']} failed: {u['failure_reason']}" for u in conn.execute(
        "SELECT unit_id, failure_reason FROM units WHERE run_id = ? AND status = 'failed'", (run_id,))]


def problems(conn: sqlite3.Connection, run_id: str, *, expect_phase: str | None = None) -> list[str]:
    """Every reason to stop right now. An empty list means "go on".

    `expect_phase` is the gate the script is about to act at (for example "AT_G2"). The run state is
    only reported when nothing more specific is known, so a failed unit says why it failed instead of
    just "the run is FAILED"."""
    found = failed_unit_reasons(conn, run_id) + stop_reasons(conn, run_id)
    run = runs.get_run(conn, run_id)
    if found:
        return found
    if run["status"] != "ACTIVE":
        return [f"the run is {run['status']}, not ACTIVE"]
    if expect_phase and run["phase"] != expect_phase:
        return [f"the run is at {run['phase']}, but the script expected {expect_phase}"]
    return []
