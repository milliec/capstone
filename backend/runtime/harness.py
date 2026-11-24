"""The role harness's call caps (CR-030, EC-R10, B3 step 7a).

Real model calls are allowed for five activities only. Three of them have a call cap: the spike
(at most 70 real calls), tuning (at most 60) and evaluation (at most 63, DL-59). The harness counts the real calls already made for
an activity FROM THE TRACE (every real call writes a line with its `spend_activity`, late calls
included, because they were paid for) and refuses the next call once the cap is reached.

Only the check is built here. The harness that runs one role's call on the demo inputs (the spike's
"5 times per role", tuning) is built with the spike, after the first green path and DL-40; it calls
`check_call_allowed` before every call. No real call can happen in this build: the agent functions
refuse real mode, and no model ID is set.
"""

import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

# EC-R9, EC-R10, DL-59 (SOQ-36). Evaluation is three runs of 21 calls: 19 requests for a run (the most
# seen) plus the 2 harness calls (`I-1` and injection). Rehearsal and demo have no cap.
CALL_CAPS = {"spike": 70, "tuning": 60, "evaluation": 63}


class CallCapReached(Exception):
    """The activity has used all its real calls (EC-R10). Spending more is an operator decision."""


def real_calls_made(conn: sqlite3.Connection, activity: str) -> int:
    """How many real calls the trace records for an activity, across all runs."""
    return conn.execute("SELECT COUNT(*) FROM trace WHERE spend_activity = ?",
                        (activity,)).fetchone()[0]


@dataclass(frozen=True)
class DatabaseCount:
    """The real-call lines of one activity in ONE database file."""
    label: str            # "data/spike.db": the folder and the file name, for printing
    lines: int            # trace lines whose `spend_activity` is the activity (one per request)
    cost_usd: float       # what those lines cost, as recorded
    exists: bool          # False: there is no such file (nothing was ever sent from it); it is NOT created


@dataclass(frozen=True)
class CallCount:
    """How many real calls an activity has made across EVERY database that can hold them."""
    activity: str
    databases: tuple      # DatabaseCount, one per distinct file

    @property
    def total(self) -> int:
        return sum(d.lines for d in self.databases)

    @property
    def cost_usd(self) -> float:
        return sum(d.cost_usd for d in self.databases)

    def breakdown_with_cost(self) -> str:
        """The same, with what each file's lines cost, for example "data/spike.db 6 (US$0.0164)"."""
        return ", ".join(f"{d.label} {d.lines} (US${d.cost_usd:.4f})" + ("" if d.exists else " (no file yet)")
                         for d in self.databases)

    def breakdown(self) -> str:
        """For example "data/spike.db 6, data/app.db 18". A file that does not exist says so."""
        return ", ".join(f"{d.label} {d.lines}" + ("" if d.exists else " (no file yet)")
                         for d in self.databases)


def count_real_calls(activity: str, database_paths: Iterable[Path]) -> CallCount:
    """Count an activity's real calls across SEVERAL database files, so that a call counts toward its
    cap whichever database it landed in (operator, 2026-11-23). The spike runner writes `data/spike.db`;
    the web app writes `data/app.db`. A per-file count would let the web app's calls go unseen.

    READ-ONLY: each file is opened with mode=ro, one that does not exist counts as 0 and is never
    created, and the same file reached by two paths is counted once. A file that exists but cannot be
    read RAISES (sqlite3.DatabaseError): a count that quietly said 0 would let the cap be passed."""
    seen: set[Path] = set()
    counts = []
    for given in database_paths:
        path = Path(given).resolve()
        if path in seen:
            continue
        seen.add(path)
        label = f"{path.parent.name}/{path.name}"
        if not path.exists():
            counts.append(DatabaseCount(label, 0, 0.0, exists=False))
            continue
        conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        try:
            lines, cost = conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(cost_usd), 0) FROM trace WHERE spend_activity = ?",
                (activity,)).fetchone()
        except sqlite3.OperationalError as error:
            if "no such table" not in str(error):         # a file with no trace table has made no calls
                raise
            lines, cost = 0, 0.0
        finally:
            conn.close()
        counts.append(DatabaseCount(label, lines, float(cost), exists=True))
    return CallCount(activity=activity, databases=tuple(counts))


def check_call_allowed(conn: sqlite3.Connection, activity: str) -> None:
    """Refuse the next real call if the activity is at its cap. Activities without a cap pass."""
    cap = CALL_CAPS.get(activity)
    if cap is None:
        return
    made = real_calls_made(conn, activity)
    if made >= cap:
        raise CallCapReached(f"{activity}: {made} of {cap} real calls used (EC-R10). "
                             "A further call needs a recorded operator decision.")
