"""The Stage B graders (EC-004, EC-010, EC-012). No model, no network.

Fabricated verdicts and traces, spoiled one way at a time. Includes the boundaries: "under 5
minutes" and "under US$2" are strict, so exactly 300 s and exactly US$2.00 are misses.
"""

import copy

import pytest

from backend.evaluation import golden, grade, grade_b
from backend.evaluation.grade_b import StageBOutput, StoredVerdict, TraceSummary
from tests.tier2.test_evaluation_stage_a import perfect, row_of

FACT_IDS = {f"FACT-0{n}" for n in range(1, 8)} | {"EVT-01"}


@pytest.fixture(scope="module")
def key():
    return golden.load_golden_set()


@pytest.fixture(scope="module")
def paragraphs():
    from backend.domain import sources
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


def perfect_b(out_a, key) -> StageBOutput:
    """Exactly what the key's section 2 says stage B should produce."""
    verdicts = []
    for g in key.rows:
        v = key.verdict(g.code)
        row = row_of(out_a, g.code, key)
        verdicts.append(StoredVerdict(
            verdict_id=f"VER-X-{g.code}", row_id=row.row_id, verdict=v.verdict,
            cited_fact_ids=list(v.fact_ids), reasoning="Because.",
            missing_information="A fact is not confirmed." if v.verdict == "unsure" else ""))
    return StageBOutput(
        verdicts=verdicts, approved_row_ids={r.row_id for r in out_a.rows},
        existing_fact_ids=set(FACT_IDS),
        trace=TraceSummary(calls=17, duration_ms=61_000, cost_usd=0.85, run_cost_count=0.85))


def ec004(out_a, out_b, key):
    return grade_b.grade_ec004(out_a, out_b, key)


def verdict_of(out_a, out_b, code, key) -> StoredVerdict:
    row = row_of(out_a, code, key)
    return next(v for v in out_b.verdicts if v.row_id == row.row_id)


# --- EC-004 ---------------------------------------------------------------------------------

def test_the_perfect_verdicts_pass(key, paragraphs):
    out_a = perfect(key, paragraphs)
    result = ec004(out_a, perfect_b(out_a, key), key)
    assert result.status == grade.PASS and "6 of 6" in result.summary
    assert result.findings == []


def test_unsure_answered_applies_is_the_named_confident_error(key, paragraphs):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    v = verdict_of(out_a, out_b, "OBL-04", key)
    v.verdict, v.missing_information = "applies", ""
    result = ec004(out_a, out_b, key)
    assert result.status == grade.MISS and "5 of 6" in result.summary
    finding = result.findings[0]
    assert finding.subject.startswith("OBL-04") and "confident error" in finding.what
    assert (finding.expected, finding.actual) == ("unsure", "applies")


@pytest.mark.parametrize("code,wrong", [("OBL-06", "applies"), ("OBL-01", "unsure"),
                                        ("OBL-03", "does_not_apply")])
def test_any_other_wrong_verdict_is_a_miss_with_expected_and_actual(key, paragraphs, code, wrong):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    verdict_of(out_a, out_b, code, key).verdict = wrong
    findings = ec004(out_a, out_b, key).findings
    assert [(f.what, f.actual) for f in findings] == [("verdict", wrong)]


@pytest.mark.parametrize("code,cited", [
    ("OBL-04", ["FACT-03"]), ("OBL-04", ["FACT-04"]), ("OBL-05", ["FACT-06"]),
    ("OBL-05", ["EVT-01"]), ("OBL-04", ["FACT-01"])])
def test_the_two_named_verdicts_must_cite_their_named_facts(key, paragraphs, code, cited):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    verdict_of(out_a, out_b, code, key).cited_fact_ids = cited
    result = ec004(out_a, out_b, key)
    assert result.status == grade.MISS and result.findings[0].what == "cited fact IDs"


def test_a_citation_that_does_not_exist_or_is_missing_is_a_miss(key, paragraphs):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    verdict_of(out_a, out_b, "OBL-01", key).cited_fact_ids = ["FACT-99"]
    assert "do not exist" in ec004(out_a, out_b, key).findings[0].actual
    out_b = perfect_b(out_a, key)
    verdict_of(out_a, out_b, "OBL-01", key).cited_fact_ids = []
    assert ec004(out_a, out_b, key).findings[0].actual == "none"


def test_the_sad_asks_only_for_an_existing_fact_on_the_other_rows(key, paragraphs):
    """EC-004 names the facts for OBL-04 and OBL-05 only. The key lists more, but the SAD is the
    contract, so a different existing fact on OBL-01 is not a miss, and extra citations are fine."""
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    verdict_of(out_a, out_b, "OBL-01", key).cited_fact_ids = ["FACT-02"]
    verdict_of(out_a, out_b, "OBL-04", key).cited_fact_ids = ["FACT-03", "FACT-04", "FACT-07"]
    assert ec004(out_a, out_b, key).status == grade.PASS


def test_a_row_that_was_not_extracted_has_no_verdict_and_misses(key, paragraphs):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    out_a.rows = [r for r in out_a.rows if r.source_paragraph_id != "SRC-VATLAW-P1"]
    result = ec004(out_a, out_b, key)
    assert result.status == grade.MISS
    assert (result.findings[0].expected, result.findings[0].actual) == (
        "does_not_apply", "no row, so no verdict")


def test_a_row_the_specialist_did_not_approve_is_not_tested_not_a_miss(key, paragraphs):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    gone = row_of(out_a, "OBL-06", key).row_id
    out_b.verdicts = [v for v in out_b.verdicts if v.row_id != gone]
    out_b.approved_row_ids.discard(gone)
    result = ec004(out_a, out_b, key)
    assert result.status == grade.INCOMPLETE          # nothing missed, one part not tested
    assert [c.status for c in result.checks].count(grade.NOT_TESTED) == 1
    # ...but an approved row with no verdict is a miss:
    out_b.approved_row_ids.add(gone)
    assert ec004(out_a, out_b, key).status == grade.MISS


def test_verdicts_on_rows_the_key_does_not_know_are_ignored(key, paragraphs):
    out_a = perfect(key, paragraphs)
    out_b = perfect_b(out_a, key)
    out_b.verdicts.append(copy.deepcopy(out_b.verdicts[0]))
    out_b.verdicts[-1].row_id, out_b.verdicts[-1].verdict_id = "ROW-X-EXTRA", "VER-X-EXTRA"
    assert ec004(out_a, out_b, key).status == grade.PASS


# --- EC-010 ---------------------------------------------------------------------------------

@pytest.mark.parametrize("ms,status", [(61_000, grade.PASS), (299_999, grade.PASS),
                                       (300_000, grade.MISS), (301_000, grade.MISS)])
def test_ec_010_under_5_minutes_is_strict(ms, status):
    t = TraceSummary(calls=17, duration_ms=ms)
    result = grade_b.grade_ec010(t, stand_in=False)
    assert result.status == status
    if status == grade.MISS:
        assert (result.findings[0].expected, "s" in result.findings[0].actual) == ("under 300 s", True)


def test_ec_010_counts_late_calls_and_says_so():
    t = TraceSummary(calls=18, late_calls=1, copy_case_calls=2, duration_ms=10_000)
    assert "1 late" in grade_b.grade_ec010(t, stand_in=False).summary
    assert "2 copy-case" in grade_b.grade_ec010(t, stand_in=False).summary


def test_ec_010_on_a_stand_in_run_is_not_tested_but_shows_the_numbers():
    result = grade_b.grade_ec010(TraceSummary(calls=17, duration_ms=40), stand_in=True)
    assert result.status == grade.NOT_TESTED and "0.0 s over 17 calls" in result.summary
    assert "measures nothing" in result.checks[0].note


def test_ec_010_with_no_call_in_the_trace_is_not_a_pass():
    assert grade_b.grade_ec010(TraceSummary(), stand_in=False).status == grade.NOT_TESTED


# --- EC-012 ---------------------------------------------------------------------------------

@pytest.mark.parametrize("cost,status", [(0.85, grade.PASS), (1.9999, grade.PASS),
                                         (2.00, grade.MISS), (2.50, grade.MISS)])
def test_ec_012_under_2_dollars_is_strict(cost, status):
    t = TraceSummary(calls=17, cost_usd=cost, run_cost_count=cost)
    result = grade_b.grade_ec012(t, stand_in=False)
    assert result.status == (grade.PASS if status == grade.PASS else grade.MISS)
    if status == grade.MISS:
        assert result.findings[0].expected == "under US$2.00"


def test_ec_012_the_trace_must_add_up_to_the_runs_own_cost_count():
    t = TraceSummary(calls=17, cost_usd=0.85, run_cost_count=0.80)
    result = grade_b.grade_ec012(t, stand_in=False)
    assert result.status == grade.MISS
    assert result.findings[0].what.startswith("trace total")


def test_ec_012_on_a_stand_in_run_is_incomplete_never_a_pass():
    result = grade_b.grade_ec012(TraceSummary(calls=17, cost_usd=0.0), stand_in=True)
    assert result.status == grade.INCOMPLETE
    assert [c.status for c in result.checks] == [grade.NOT_TESTED, grade.PASS]
