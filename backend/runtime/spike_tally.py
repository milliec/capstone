"""The spike's TALLY: a read-only summary of what the spike database holds (B3 spike PR 4, PR 2).

    .venv/bin/python -m backend.runtime.spike --tally [--exclude SRC-UCILAW-P3#1]

It exists so that nobody has to copy thirty-odd printouts into a table. It reads the trace the runner
already writes (`data/spike.db`) and says, per model and per verifier case: how many calls, how many
answers passed the schema on the first try, how many planted conflicts were CAUGHT or MISSED, how many
false alarms, the tokens, the time and the cost.

What it does NOT do, by design:
  * It sends nothing and calls no model. It needs no API key and no `AGENTS_MODE=real`. It imports no
    CrewAI (a test checks it in a fresh process).
  * It writes nothing. The database is opened read-only (`mode=ro`), it is never created, and a test
    compares the file's bytes before and after.
  * It decides nothing. It prints what DL-26 says a miss means; the operator makes the choice.

How a line becomes a call. A "call" is a UNIT (`SRC-RBELAW-P1#2`): one or more trace lines, one per HTTP
request. The LAST line is the request that answered. A unit is `valid` (the answer passed its
guardrail), `invalid` (it was billed but failed the guardrail), `no answer` (every request failed) or
`not a call` (no model answered, for example the first call's pre-flight line, which was not a model
call at all). A MISS is only ever counted on a valid answer: an invalid answer is a schema failure.

How a line is re-priced. The trace prices a line at the prices of the ROLE that ran (the DL-40 prices are
per role). The bake-off runs the judge's model as a verifier, so its lines are recorded at the verifier's
prices, which overstates them. The tally finds the role whose model ID (in `.env`) is the model that ran
and prices the line at that role's prices. A line with no usage data (an estimate), a refused or failed
request, or a model that matches no role is NOT re-priced: its recorded cost stays, and it is counted.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from backend.domain.schemas import ExtractionResult, Flag, Verdict
from backend.runtime import harness, model_settings, spike

RUNS_PER_CASE = 5               # the SAD asks for each role's call on the demo inputs 5 times (EC-R10)
FULL_RUN_VERIFIER_CALLS = 7     # a full run drafts 7 rows (6 genuine and the planted demo row), each verified
STEP_TITLES = {"extract_rows": "EXTRACTOR", "check_conflicts": "VERIFIER", "judge_applicability": "JUDGE"}
CASE_BY_ROW = {case.row_id: case for case in spike.CASES.values()}


@dataclass
class Unit:
    """One call of the spike: every trace line that shares a step and a unit name."""
    step: str
    unit_id: str
    model: str
    status: str                       # valid, invalid, no_answer or not_a_call
    lines: int
    tokens_in: int                    # of the request that answered
    tokens_out: int
    seconds: float                    # every request of the unit added up
    recorded: float                   # what the trace says it cost
    repriced: float                   # what it cost at the prices of the role that ran the model
    priced_as: str = ""               # that role, "" when the line was left as recorded
    estimated_lines: int = 0          # lines whose cost is an estimate (left as recorded)
    case_id: str = ""                 # verifier only: the bake-off case this unit ran
    good: bool | None = None          # verifier: CAUGHT or CLEAN; judge: CORRECT; None when not judged
    false_alarm: bool = False         # verifier: a planted case also drew a false-alarm flag
    unreadable: bool = False          # a valid answer that can no longer be read as its class
    rows: int = 0                     # extractor: rows returned
    excluded: bool = False


@dataclass
class Tally:
    path: Path
    exists: bool = True
    slots_used: int = 0
    slot_cap: int = 70
    line_kinds: dict = field(default_factory=dict)
    units: list = field(default_factory=list)
    recorded_total: float = 0.0
    repriced_total: float = 0.0
    role_models: dict = field(default_factory=dict)
    note: str = ""
    count: object = None              # harness.CallCount: the real calls in EVERY database that can hold them


# --- Reading -------------------------------------------------------------------------------------

def read_lines(path: Path) -> list[dict] | None:
    """Every trace line, oldest first. None when the file does not exist (it is NOT created)."""
    if not path.exists():
        return None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)       # read-only: a write would fail
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM trace ORDER BY trace_id")]
    except sqlite3.OperationalError as error:
        if "no such table" in str(error):
            return []
        raise
    finally:
        conn.close()


def line_kind(line: dict) -> str:
    """What a trace line is, in words, for the slot count."""
    error = line.get("provider_error")
    if error:
        return "refused (never sent)" if str(error).startswith("refused before sending") else "no answer"
    return "model answer" if line.get("raw_output") is not None else "not a model call"


def priced_as(model: str, step_role: str, role_models: dict) -> str:
    """The role whose prices apply to a model: the step's own role if it uses this model, else the
    first other role that does (the judge's model run as a verifier), else "" (unknown)."""
    if role_models.get(step_role) == model:
        return step_role
    for role in ("judge", "verify", "extract"):
        if model and role_models.get(role) == model:
            return role
    return ""


def reprice(line: dict, step_role: str, role_models: dict) -> tuple[float, str]:
    """(cost, the role priced as). A line is only re-priced when it has real usage data."""
    recorded = float(line["cost_usd"])
    if line["cost_estimated"] or line.get("provider_error"):
        return recorded, ""
    role = priced_as(line["model"], step_role, role_models)
    if not role:
        return recorded, ""
    return model_settings.call_cost_usd(role, line["tokens_in"], line["tokens_out"]), role


# --- Building units --------------------------------------------------------------------------------

def build_units(lines: list[dict], role_models: dict, exclude: set) -> list[Unit]:
    grouped: dict[tuple, list] = {}
    for line in lines:
        grouped.setdefault((line["step"], line["unit_id"]), []).append(line)
    units = []
    for (step, unit_id), group in grouped.items():
        final = group[-1]
        role = model_settings.STEP_ROLE.get(step, "")
        if final.get("provider_error"):
            status = "no_answer"
        elif final.get("raw_output") is None:
            status = "not_a_call"
        else:
            status = "invalid" if final.get("validation_error") else "valid"
        priced = [reprice(line, role, role_models) for line in group]
        unit = Unit(
            step=step, unit_id=unit_id, model=final["model"], status=status, lines=len(group),
            tokens_in=final["tokens_in"], tokens_out=final["tokens_out"],
            seconds=sum(line["duration_ms"] for line in group) / 1000,
            recorded=sum(float(line["cost_usd"]) for line in group),
            repriced=sum(cost for cost, _ in priced),
            priced_as=next((r for _, r in reversed(priced) if r), ""),
            estimated_lines=sum(1 for line in group if line["cost_estimated"]),
            excluded=(step == "check_conflicts" and unit_id in exclude))
        if step == "check_conflicts":
            # Each row belongs to one case, so the unit's name says which case it ran, even when the
            # call failed or its answer was refused (an invalid answer still counts as a call of its case).
            case = CASE_BY_ROW.get(unit_id.rpartition("#")[0])
            unit.case_id = case.case_id if case else ""
        if status == "valid":
            _judge_the_answer(unit, final)
        units.append(unit)
    return units


def _judge_the_answer(unit: Unit, final: dict) -> None:
    """Fill in what the stored answer amounts to. Uses the SAME decision as the live printout."""
    row_id = unit.unit_id.rpartition("#")[0]
    try:
        answer = json.loads(final["raw_output"])
        if unit.step == "check_conflicts":
            case = CASE_BY_ROW.get(row_id)
            flags = [Flag.model_validate(f) for f in answer["flags"]]
            if case:
                outcome = spike.classify_case(case, flags)
                unit.good = outcome.good
                unit.false_alarm = bool(outcome.false_alarms) and case.expects != "nothing"
        elif unit.step == "judge_applicability":
            verdict = Verdict.model_validate(answer)
            expected = spike.EXPECTED_VERDICTS.get(row_id)
            if expected:
                unit.good = verdict.verdict == expected[0] and expected[1] in verdict.cited_fact_ids
        elif unit.step == "extract_rows":
            unit.rows = len(ExtractionResult.model_validate(answer).rows)
    except (ValidationError, ValueError, KeyError, TypeError):
        unit.unreadable = True


# --- The tally -------------------------------------------------------------------------------------

def collect(path: Path, role_models: dict | None = None, exclude: set | None = None,
            other_databases=()) -> Tally:
    """Read the database and work out everything the printout shows. Sends nothing, writes nothing.

    `other_databases` are further files that can hold real spike calls (the web app's `data/app.db`):
    they count toward the 70 and are shown in the breakdown. The per-model tables read `path` only."""
    role_models = role_models or {}
    tally = Tally(path=path, slot_cap=harness.CALL_CAPS["spike"], role_models=role_models)
    tally.count = harness.count_real_calls("spike", [path, *other_databases])
    tally.slots_used = tally.count.total
    lines = read_lines(path)
    if lines is None:
        tally.exists = False
        return tally
    for line in lines:
        kind = line_kind(line)
        tally.line_kinds[kind] = tally.line_kinds.get(kind, 0) + 1
    tally.units = build_units(lines, role_models, exclude or set())
    tally.recorded_total = sum(float(line["cost_usd"]) for line in lines)
    tally.repriced_total = sum(unit.repriced for unit in tally.units)
    return tally


def _mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _money(value: float) -> str:
    return f"US${value:.4f}"


def _group(units: list[Unit]) -> dict:
    """Counts for a set of units."""
    valid = [u for u in units if u.status == "valid"]
    answered = [u for u in units if u.status in ("valid", "invalid")]
    return {
        "calls": len(units), "valid": len(valid),
        "invalid": sum(1 for u in units if u.status == "invalid"),
        "no_answer": sum(1 for u in units if u.status == "no_answer"),
        "not_a_call": sum(1 for u in units if u.status == "not_a_call"),
        "good": sum(1 for u in valid if u.good is True),
        "bad": sum(1 for u in valid if u.good is False),
        "false_alarm": sum(1 for u in valid if u.false_alarm),
        "unreadable": sum(1 for u in valid if u.unreadable),
        "tokens_in": _mean(u.tokens_in for u in answered), "tokens_out": _mean(u.tokens_out for u in answered),
        "seconds": _mean(u.seconds for u in answered),
        "recorded": sum(u.recorded for u in units), "repriced": sum(u.repriced for u in units),
        "estimated": sum(u.estimated_lines for u in units),
        "rows": _mean(u.rows for u in valid),
        "valid_cost": _mean(u.repriced for u in valid),
    }


def _models_in_order(units: list[Unit]) -> list[str]:
    seen: list[str] = []
    for unit in units:
        if unit.model not in seen:
            seen.append(unit.model)
    return seen


def _role_label(model: str, role_models: dict) -> str:
    roles = [role for role, m in role_models.items() if m and m == model]
    return f" (the {' and '.join(roles)} model in .env)" if roles else ""


# --- The printout ----------------------------------------------------------------------------------

def format_tally(tally: Tally) -> str:
    if not tally.exists:
        missing = ("SPIKE TALLY (read-only): there is no spike database yet, so nothing has been sent.\n"
                   f"Looked for: {tally.path}")
        if tally.count is not None and tally.slots_used:     # ...but another database has real calls
            missing = ("SPIKE TALLY (read-only): there is no spike database yet, so the spike runner has sent "
                       f"nothing.\nLooked for: {tally.path}\nReal calls elsewhere: {tally.slots_used} of "
                       f"{tally.slot_cap} ({tally.count.breakdown_with_cost()})")
        return missing
    out = ["SPIKE TALLY (read-only: nothing was sent, nothing was written, no model was called)", ""]
    kinds = ", ".join(f"{kind}: {n}" for kind, n in sorted(tally.line_kinds.items())) or "none"
    out += [f"Database       : {tally.path}",
            (f"Slots used     : {tally.slots_used} of {tally.slot_cap} "
             f"({tally.slot_cap - tally.slots_used} left); one slot per request (EC-R10)"),
            *([f"Counted in     : {tally.count.breakdown_with_cost()}"] if tally.count else []),
            f"The lines are  : {kinds}",
            f"Calls          : {len(tally.units)} (a call is one or more requests)",
            (f"Run cost       : {_money(tally.recorded_total)} recorded; {_money(tally.repriced_total)} "
             "when each line is priced for the model that ran")]
    if tally.note:
        out.append(f"Note           : {tally.note}")
    for step in ("extract_rows", "check_conflicts", "judge_applicability"):
        units = [u for u in tally.units if u.step == step]
        if units:
            out += [""] + _section(step, units, tally)
    out += ["", "Cost is in US dollars. Prices are the DL-40 prices in model_settings.py, per role."]
    return "\n".join(out)


def _section(step: str, units: list[Unit], tally: Tally) -> list[str]:
    title = {"extract_rows": "EXTRACTOR (extract_rows)", "check_conflicts": "VERIFIER BAKE-OFF (check_conflicts)",
             "judge_applicability": "JUDGE (judge_applicability)"}[step]
    out = [title]
    excluded = [u for u in units if u.excluded]
    counted = [u for u in units if not u.excluded]
    for model in _models_in_order(counted):
        mine = [u for u in counted if u.model == model]
        out.append(f"  model {model}{_role_label(model, tally.role_models)}")
        if step == "check_conflicts":
            out += _verifier_table(mine)
            out += _dl26(model, mine)
        else:
            g = _group(mine)
            good_word = "CORRECT" if step == "judge_applicability" else "-"
            out.append(f"    calls {g['calls']}, valid {g['valid']}/{g['calls']} on the first try "
                       f"({g['invalid']} invalid, {g['no_answer']} no answer"
                       + (f", {g['not_a_call']} not a model call" if g["not_a_call"] else "") + ")")
            if step == "judge_applicability":
                out.append(f"    {good_word} {g['good']}, WRONG {g['bad']} (against the answer key: applies, citing FACT-01)")
            else:
                out.append(f"    rows per valid answer (mean) {g['rows']:.1f}")
            out.append(f"    tokens in/out (mean) {g['tokens_in']:.0f}/{g['tokens_out']:.0f}; "
                       f"time (mean) {g['seconds']:.1f} s; cost {_money(g['recorded'])} recorded, "
                       f"{_money(g['repriced'])} priced for this model")
    if excluded:
        out.append("  Excluded by --exclude (not in the counts above): " + ", ".join(
            f"{u.unit_id} ({u.model}, {u.status.replace('_', ' ')})" for u in excluded))
    return out


def _verifier_table(units: list[Unit]) -> list[str]:
    out = ["    case  calls  valid  invalid  no-ans  good  bad  +FA  tokens in/out   secs  recorded  priced-for-model"]
    for case_id in [*spike.CASES, ""]:                    # the four cases, then any other row
        mine = [u for u in units if u.case_id == case_id]
        if not mine:
            continue
        g = _group(mine)
        label = case_id or "other"
        bad_word = "-" if g["valid"] == 0 else str(g["bad"])
        fa = "-" if case_id == "OK-1" else str(g["false_alarm"])
        out.append(f"    {label:<5} {g['calls']:>5}  {g['valid']:>3}/{RUNS_PER_CASE}  {g['invalid']:>7}  "
                   f"{g['no_answer']:>6}  {g['good']:>4}  {bad_word:>3}  {fa:>3}  "
                   f"{g['tokens_in']:>6.0f}/{g['tokens_out']:<5.0f} {g['seconds']:>5.1f}  "
                   f"{_money(g['recorded']):>9}  {_money(g['repriced']):>9}")
    g = _group(units)
    out.append(f"    all   {g['calls']:>5}  {g['valid']:>5}  {g['invalid']:>7}  {g['no_answer']:>6}  {g['good']:>4}  "
               f"{g['bad']:>3}  {g['false_alarm']:>3}  {g['tokens_in']:>6.0f}/{g['tokens_out']:<5.0f} {g['seconds']:>5.1f}  "
               f"{_money(g['recorded']):>9}  {_money(g['repriced']):>9}")
    out.append("    good = CAUGHT (C-1, C-2, I-1) or CLEAN (OK-1); bad = MISSED, or FALSE ALARM for OK-1; "
               "+FA = a planted run that also drew a false-alarm flag")
    if g["unreadable"]:
        out.append(f"    {g['unreadable']} valid answer(s) could not be read back as flags (not counted as good or bad)")
    return out


def _dl26(model: str, units: list[Unit]) -> list[str]:
    """What DL-26 says about the counts so far. Information only: the operator decides."""
    planted = [u for u in units if u.status == "valid" and u.case_id in ("C-1", "C-2", "I-1")]
    misses = [u for u in planted if u.good is False]
    out = [f"    DL-26 reading (information, not a decision): {len(misses)} MISSED in {len(planted)} valid planted run(s)"]
    needed = []
    for case_id in ("C-1", "C-2", "I-1", "OK-1"):
        have = sum(1 for u in units if u.status == "valid" and u.case_id == case_id)
        if have < RUNS_PER_CASE:
            needed.append(f"{case_id} {RUNS_PER_CASE - have} more")
    out.append("    valid runs still needed for 5 of each case: " + (", ".join(needed) or "none"))
    if misses:
        out.append("    A miss: by DL-26 the verifier switches to the judge's model, if the operator decides so "
                   "(the other candidate should first be seen to catch it).")
    valid = [u for u in units if u.status == "valid"]
    if valid:
        mean = _mean(u.repriced for u in valid)
        out.append(f"    A full run (the verifier on {FULL_RUN_VERIFIER_CALLS} rows) would cost about "
                   f"{_money(mean * FULL_RUN_VERIFIER_CALLS)} for this model (mean valid call {_money(mean)})")
    return out
