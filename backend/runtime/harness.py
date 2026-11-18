"""The role harness's call caps (CR-030, EC-R10, B3 step 7a).

Real model calls are allowed for five activities only. Two of them have a call cap: the spike
(at most 70 real calls) and tuning (at most 60). The harness counts the real calls already made for
an activity FROM THE TRACE (every real call writes a line with its `spend_activity`, late calls
included, because they were paid for) and refuses the next call once the cap is reached.

Only the check is built here. The harness that runs one role's call on the demo inputs (the spike's
"5 times per role", tuning) is built with the spike, after the first green path and DL-40; it calls
`check_call_allowed` before every call. No real call can happen in this build: the agent functions
refuse real mode, and no model ID is set.
"""

import sqlite3

CALL_CAPS = {"spike": 70, "tuning": 60}   # EC-R9, EC-R10; the other three activities have none


class CallCapReached(Exception):
    """The activity has used all its real calls (EC-R10). Spending more is an operator decision."""


def real_calls_made(conn: sqlite3.Connection, activity: str) -> int:
    """How many real calls the trace records for an activity, across all runs."""
    return conn.execute("SELECT COUNT(*) FROM trace WHERE spend_activity = ?",
                        (activity,)).fetchone()[0]


def check_call_allowed(conn: sqlite3.Connection, activity: str) -> None:
    """Refuse the next real call if the activity is at its cap. Activities without a cap pass."""
    cap = CALL_CAPS.get(activity)
    if cap is None:
        return
    made = real_calls_made(conn, activity)
    if made >= cap:
        raise CallCapReached(f"{activity}: {made} of {cap} real calls used (EC-R10). "
                             "A further call needs a recorded operator decision.")
