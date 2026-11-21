"""The Stage B graders (sad.md §9: EC-004, EC-010, EC-012).

Pure functions on what stage B stored (StageBOutput) and what stage A stored (StageAOutput, used
only to find which key row each verdict is about). No database, no model. Same statuses and the
same rule as grade.py: a miss shows expected and actual; "not tested" is never shown as "pass".

EC-010 and EC-012 are measured from the trace (CR-018). On a STAND-IN run they are NOT TESTED: a
stand-in call costs nothing and takes milliseconds, so "under US$2" and "under 5 minutes" would be
true and say nothing. The measured numbers are still shown.
"""

from dataclasses import dataclass, field

from backend.evaluation import grade
from backend.evaluation.golden import GoldenSet
from backend.evaluation.grade import (
    MISS,
    NOT_TESTED,
    PASS,
    Check,
    Criterion,
    Finding,
    _criterion,
    match_rows,
)

# EC-004 names the fact IDs these two verdicts must cite. For the other rows the SAD asks only for
# "at least one existing fact ID", so the key's other "facts used" are not enforced. They are
# reported as a NOTE that never changes the result (operator, 2026-11-21, qa.md question 4).
SAD_REQUIRED_CITATIONS = ("OBL-04", "OBL-05")

MAX_AGENT_SECONDS = 300.0      # EC-010: under 5 minutes (strictly)
MAX_COST_USD = 2.00            # EC-012: under US$2 (strictly)


@dataclass
class StoredVerdict:
    verdict_id: str
    row_id: str
    verdict: str                     # applies | does_not_apply | unsure
    cited_fact_ids: list[str]
    reasoning: str = ""
    missing_information: str = ""


@dataclass
class TraceSummary:
    """Every trace line of the run, late calls and copy cases included: they ran and were paid for
    (DL-43, DL-45)."""
    calls: int = 0
    late_calls: int = 0
    copy_case_calls: int = 0
    duration_ms: int = 0
    cost_usd: float = 0.0
    late_duration_ms: int = 0        # the part of duration_ms spent in late calls (still counted)
    late_cost_usd: float = 0.0       # the part of cost_usd spent in late calls (still counted)
    run_cost_count: float = 0.0      # runs.cost_so_far, which the trace must add up to


@dataclass
class StageBOutput:
    verdicts: list[StoredVerdict]
    approved_row_ids: set[str]       # rows the specialist approved at G1: the only ones stage B judges
    existing_fact_ids: set[str]      # the fund's fact and event IDs
    trace: TraceSummary = field(default_factory=TraceSummary)


# --- EC-004: applicability verdicts against KEY §2 ---------------------------------------------

def grade_ec004(out_a: grade.StageAOutput, out_b: StageBOutput, key: GoldenSet) -> Criterion:
    matched, _ = match_rows(out_a, key)
    by_row = {v.row_id: v for v in out_b.verdicts}
    checks, findings, notes = [], [], []
    for g in key.rows:
        want = key.verdict(g.code)
        label = f"{g.code} {g.obligation_name}"
        row = matched.get(g.code)
        if row is None:
            checks.append(Check(label, MISS, "the row was not extracted, so it has no verdict"))
            findings.append(Finding(label, "verdict", want.verdict, "no row, so no verdict"))
            continue
        got = by_row.get(row.row_id)
        if got is None:
            if row.row_id not in out_b.approved_row_ids:
                checks.append(Check(label, NOT_TESTED, "not approved at G1, so stage B did not judge it"))
            else:
                checks.append(Check(label, MISS, "approved, but no verdict was stored"))
                findings.append(Finding(label, "verdict", want.verdict, "no verdict"))
            continue
        problems = []
        if got.verdict != want.verdict:
            confident = want.verdict == "unsure" and got.verdict == "applies"
            what = "verdict (a confident error: the key says unsure)" if confident else "verdict"
            problems.append(Finding(label, what, want.verdict, got.verdict))
        cited = set(got.cited_fact_ids)
        if not cited:
            problems.append(Finding(label, "cited fact IDs", "at least one", "none"))
        elif cited - out_b.existing_fact_ids:
            problems.append(Finding(label, "cited fact IDs", "only existing fact IDs",
                                    ", ".join(sorted(cited - out_b.existing_fact_ids))
                                    + " do not exist"))
        if g.code in SAD_REQUIRED_CITATIONS and not set(want.fact_ids) <= cited:
            problems.append(Finding(label, "cited fact IDs", ", ".join(want.fact_ids),
                                    ", ".join(got.cited_fact_ids) or "none"))
        missing_key_facts = [f for f in want.fact_ids if f not in cited]
        if g.code not in SAD_REQUIRED_CITATIONS and missing_key_facts:
            notes.append(f"{label}: the key's facts not cited: {', '.join(missing_key_facts)} "
                         "(for information; the SAD does not require them, so this is not a miss)")
        findings += problems
        checks.append(Check(label, MISS if problems else PASS,
                            "; ".join(p.what for p in problems)))
    right = sum(1 for c in checks if c.status == PASS)
    return _criterion(
        "EC-004", "Applicability verdicts against the answer key",
        "6 of 6: OBL-01, 02, 03, 05 applies; OBL-04 unsure; OBL-06 does not apply; every verdict "
        "cites an existing fact ID; OBL-04 cites FACT-03 and FACT-04; OBL-05 cites FACT-06 and EVT-01",
        f"{right} of {len(key.rows)} verdicts correct", checks, findings, notes)


# --- EC-010 and EC-012: time and cost, from the trace ------------------------------------------

def _trace_note(t: TraceSummary) -> str:
    extra = []
    if t.late_calls:
        extra.append(f"{t.late_calls} late")
    if t.copy_case_calls:
        extra.append(f"{t.copy_case_calls} copy-case")
    return f"{t.calls} calls" + (f" ({', '.join(extra)})" if extra else "")


def _late_note(t: TraceSummary) -> str:
    """Late calls stay in the time and the cost (operator, 2026-11-21); the report says how much
    of each they are, so nobody has to guess."""
    if not t.late_calls:
        return ""
    return (f"; of this, LATE calls: {t.late_calls} calls, {t.late_duration_ms / 1000:.1f} s, "
            f"US${t.late_cost_usd:.4f} (counted: a user waits for them)")


def grade_ec010(t: TraceSummary, *, stand_in: bool) -> Criterion:
    seconds = t.duration_ms / 1000
    note = f"{seconds:.1f} s over {_trace_note(t)}{_late_note(t)}"
    if stand_in:
        check = Check("agent time under 5 minutes", NOT_TESTED,
                      f"{note}. Stand-in run: no model call, so this measures nothing")
    elif t.calls == 0:
        check = Check("agent time under 5 minutes", NOT_TESTED, "the trace holds no call")
    else:
        check = Check("agent time under 5 minutes",
                      PASS if seconds < MAX_AGENT_SECONDS else MISS, note)
    findings = ([Finding("agent time", "seconds over all model steps, retries included",
                         f"under {MAX_AGENT_SECONDS:.0f} s", f"{seconds:.1f} s")]
                if check.status == MISS else [])
    return _criterion("EC-010", "Agent time per run",
                      "under 5 minutes on each run (all model steps, retries included, not counting "
                      "time waiting for the specialist)", note, [check], findings)


def grade_ec012(t: TraceSummary, *, stand_in: bool) -> Criterion:
    note = f"US${t.cost_usd:.4f} over {_trace_note(t)}{_late_note(t)}"
    if stand_in:
        under = Check("cost under US$2", NOT_TESTED,
                      f"{note}. Stand-in run: no model call, so this measures nothing")
    elif t.calls == 0:
        under = Check("cost under US$2", NOT_TESTED, "the trace holds no call")
    else:
        under = Check("cost under US$2", PASS if t.cost_usd < MAX_COST_USD else MISS, note)
    consistent = round(t.cost_usd, 6) == round(t.run_cost_count, 6)
    same = Check("the trace adds up to the run's own cost count", PASS if consistent else MISS,
                 f"trace US${t.cost_usd:.4f}; run US${t.run_cost_count:.4f}")
    findings = []
    if under.status == MISS:
        findings.append(Finding("model cost", "US$ per run from the trace, retries included",
                                f"under US${MAX_COST_USD:.2f}", f"US${t.cost_usd:.4f}"))
    if not consistent:
        findings.append(Finding("cost count", "trace total against the run's cost count",
                                f"US${t.run_cost_count:.4f}", f"US${t.cost_usd:.4f}"))
    return _criterion("EC-012", "Model cost per run",
                      "under US$2 on each run (provider usage data, retries included); US$2.50 is the "
                      "hard stop", note, [under, same], findings)


def grade_stage_b(out_a: grade.StageAOutput, out_b: StageBOutput, key: GoldenSet, *,
                  stand_in: bool) -> list[Criterion]:
    return [grade_ec004(out_a, out_b, key), grade_ec010(out_b.trace, stand_in=stand_in),
            grade_ec012(out_b.trace, stand_in=stand_in)]
