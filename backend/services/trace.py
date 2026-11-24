"""The trace: one append-only line per model call attempt (CR-018), and the run's cost count (CR-017).

Since B3 step 7b PR 5 an "attempt" is one HTTP request: a retry (DL-43) is a second line, and a
request that got no answer (a timeout, a 500) is a line too, so its cost counts towards the cap.

`record_call` does four things in ONE transaction, so they always agree:
  1. decides whether the output is LATE: it arrived after its stage failed, the run ended, or a
     retry started (rule 9, DL-43). A late output is kept in the trace only; the stage stores
     nothing from it;
  2. inserts the trace line (with `late` set);
  3. adds the call's cost to the run's `cost_so_far`. A late call's cost still counts (DL-43);
  4. writes one `agent_output` audit entry whose `trace_ref` is the record key, so any row,
     verdict or entry can be traced back to its call (CR-018).

Stand-in calls write a line too (cost 0, no model), so all of this works the same before any real
call. "A call whose trace line cannot be written counts as failed" (CR-018): the stage treats an
error from here as a failed unit.
"""

import sqlite3
from dataclasses import dataclass

from backend.services.audit import write_audit


@dataclass(frozen=True)
class CallRecord:
    """What one agent call reports about itself. The stage adds where it belongs (run, unit)."""

    step: str                       # extract_rows, check_conflicts or judge_applicability
    at: str                         # when the call started, ISO 8601 UTC
    prompt_version: str             # hash of the agent and task content used
    input_hash: str
    raw_output: str | None
    parsed_output: str | None       # or validation_error, never both
    validation_error: str | None
    duration_ms: int
    model: str = ""                 # empty in stand-in mode
    model_returned: str = ""
    settings_json: str = "{}"
    max_tokens: int | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    attempt_n: int = 1              # which HTTP request of the unit this is: 1, 2, ... (PR 5)
    # B3 step 7b PR 5. The defaults are what a stand-in call holds, so a stand-in line is unchanged.
    stop_reason: str = ""           # the API's finish reason; empty when no answer came
    provider_error: str | None = None   # why this attempt got no answer; None when it did
    cost_estimated: bool = False    # True: no usage data came, so the worst case was charged
    off_pinned_setting: bool = False    # True: the request did not carry the pinned settings (DL-40)
    # Spike fix, step D. The URL path of the request ("/v1/chat/completions"); empty for a stand-in
    # line and for a line written before this column existed.
    request_path: str = ""


def record_key(run_id: str, step: str, stage_attempt: int, unit_id: str, attempt_n: int) -> str:
    """The trace record key as the audit entry stores it (CR-018, "Identifiers and versions")."""
    return f"{run_id}·{step}·{stage_attempt}·{unit_id}·{attempt_n}"


def _is_late(conn: sqlite3.Connection, run: dict, stage: str) -> bool:
    """True when the run is no longer ACTIVE in this stage's phase on this stage attempt."""
    now = conn.execute("SELECT status, phase, stage_attempt FROM runs WHERE run_id = ?",
                       (run["run_id"],)).fetchone()
    return not (now["status"] == "ACTIVE" and now["phase"] == f"{stage}_RUNNING"
                and now["stage_attempt"] == run["stage_attempt"])


def record_call(conn: sqlite3.Connection, *, run: dict, stage: str, unit_id: str,
                call: CallRecord, spend_activity: str | None = None,
                eval_case: str | None = None) -> bool:
    """Write the call's trace line, cost and audit entry together. Returns True if it was late.

    `eval_case` (H-096, DL-45) labels a call that belongs to an evaluation copy case:
    'altered_quote', 'I-1' or 'injection'. None (the default) is an ordinary call. This code does
    not check the value: the trace column's CHECK refuses anything else, and the whole
    transaction is then rolled back (no line, no cost, no audit entry)."""
    conn.commit()                      # nothing of ours is pending
    conn.execute("BEGIN IMMEDIATE")    # the write lock: the run cannot change under us
    try:
        # A copy-case call belongs to no stage, so it can never be "late" for one (PR 6, DL-45). Without
        # this, a call made while the run waits at a gate would be stamped late and skew EC-010.
        late = False if eval_case else _is_late(conn, run, stage)
        conn.execute(
            """INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at,
                                  prompt_version, model, model_returned, settings_json, max_tokens,
                                  input_hash, raw_output, parsed_output, validation_error,
                                  tokens_in, tokens_out, cost_usd, duration_ms, spend_activity,
                                  late, stop_reason, provider_error, cost_estimated,
                                  off_pinned_setting, request_path, eval_case)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?)""",
            (run["run_id"], run["fund_id"], call.step, run["stage_attempt"], unit_id,
             call.attempt_n, call.at, call.prompt_version, call.model, call.model_returned,
             call.settings_json, call.max_tokens, call.input_hash, call.raw_output,
             call.parsed_output, call.validation_error, call.tokens_in, call.tokens_out,
             call.cost_usd, call.duration_ms, spend_activity or None, int(late),
             call.stop_reason, call.provider_error, int(call.cost_estimated),
             int(call.off_pinned_setting), call.request_path, eval_case or None))
        conn.execute("UPDATE runs SET cost_so_far = cost_so_far + ? WHERE run_id = ?",
                     (call.cost_usd, run["run_id"]))
        key = record_key(run["run_id"], call.step, run["stage_attempt"], unit_id, call.attempt_n)
        if call.provider_error:
            outcome = "no answer (provider error)"     # the attempt is traced; there is no output
        else:
            outcome = "invalid output" if call.validation_error else "output"
        write_audit(conn, fund_id=run["fund_id"], actor=f"stage {stage}", event_type="agent_output",
                    run_id=run["run_id"], subject_id=unit_id, trace_ref=key,
                    reason=f"{call.step} {outcome}" + (" (late: kept in the trace only)" if late
                                                        else ""))
        conn.commit()
        return late
    except BaseException:
        conn.rollback()
        raise


def cost_so_far(conn: sqlite3.Connection, run_id: str) -> float:
    """The run's model cost so far, in US dollars (retries and late calls included)."""
    return conn.execute("SELECT cost_so_far FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0]


def list_trace(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Every trace line of a run, oldest first."""
    return [dict(r) for r in conn.execute(
        "SELECT * FROM trace WHERE run_id = ? ORDER BY trace_id", (run_id,))]
