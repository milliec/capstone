"""The stage A grader (B8 first slice). No model, no network.

Two kinds of input: a "perfect" output built from the answer key and then spoiled one way at a
time (the code-only ugly cases), and a real stand-in run read from the database. A grader that
cannot fail proves nothing, so most tests here make it fail on purpose.
"""

import copy

import pytest

from backend.db.connection import connect, init_db
from backend.domain import quote_check, sources
from backend.evaluation import cases, golden, grade, lookup
from backend.evaluation import stage_a as stage_a_module
from backend.services import decisions, runs
from tests import flow


@pytest.fixture(scope="module")
def key():
    return golden.load_golden_set()


@pytest.fixture(scope="module")
def paragraphs():
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


def _flag(paragraph_id, paragraphs, kind="cross_source"):
    words = quote_check.normalise(paragraphs[paragraph_id]).split()[:8]
    return {"flag_type": kind, "explanation": "They differ.", "field": None, "row_value": None,
            "quote_says": None, "other_paragraph_id": paragraph_id, "other_quote": " ".join(words)}


def perfect(key, paragraphs) -> grade.StageAOutput:
    """Exactly what the answer key says stage A should produce."""
    rows = []
    for g in key.rows:
        flags = [_flag(f.other_paragraph_id, paragraphs) for f in key.cross_source_flags
                 if f.row_code == g.code]
        rows.append(grade.StoredRow(
            row_id=f"ROW-X-{g.code}", origin="model", source_paragraph_id=g.source_paragraph_id,
            obligation_name=g.obligation_name, frequency=g.frequency, anchor=g.anchor,
            offset=dict(g.offset), recipient_code=g.recipient_code,
            responsible_role=g.responsible_role, applicability_rule=g.applicability_rule,
            business_day_rule="not_confirmed", quote=g.quote, quote_check="pass", flags=flags))
    return grade.StageAOutput(rows=rows, paragraphs=dict(paragraphs))


def grade_all(out, key):
    copy_cases = cases.run_copy_cases(key, out.paragraphs)
    return {c.id: c for c in grade.grade_stage_a(out, key, copy_cases)}


def row_of(out, code, key):
    return next(r for r in out.rows if r.source_paragraph_id == key.row(code).source_paragraph_id)


# --- The perfect output ---------------------------------------------------------------------

def test_a_perfect_output_passes_what_can_be_tested_and_says_what_cannot(key, paragraphs):
    result = grade_all(perfect(key, paragraphs), key)
    assert [result[i].status for i in ("EC-001", "EC-003", "EC-006", "EC-009")] == ["pass"] * 4
    assert result["EC-002"].status == grade.FOR_OPERATOR          # the operator judges names
    assert result["EC-021"].status == grade.NOT_TESTED
    # EC-005 has 4 parts; I-1 needs a model. 3 passed and 1 not tested is never shown as "pass".
    assert result["EC-005"].status == grade.INCOMPLETE
    assert [c.status for c in result["EC-005"].checks].count(grade.NOT_TESTED) == 1


# --- EC-001 ---------------------------------------------------------------------------------

def test_a_missing_row_is_a_miss_and_also_changes_the_coverage_view(key, paragraphs):
    out = perfect(key, paragraphs)
    out.rows = [r for r in out.rows if r.source_paragraph_id != "SRC-CNMV-P1"]
    result = grade_all(out, key)
    assert result["EC-001"].status == grade.MISS
    assert [(f.what, f.actual) for f in result["EC-001"].findings] == [("row", "no such row")]
    assert result["EC-009"].status == grade.MISS        # SRC-CNMV-P1 is now uncited
    assert result["EC-009"].findings[0].subject == "SRC-CNMV-P1"


def test_an_extra_row_on_a_paragraph_that_must_not_be_extracted(key, paragraphs):
    out = perfect(key, paragraphs)
    extra = copy.deepcopy(out.rows[0])
    extra.row_id, extra.source_paragraph_id = "ROW-X-9", "SRC-PRACT-P3"
    out.rows.append(extra)
    result = grade_all(out, key)["EC-001"]
    assert result.status == grade.MISS
    assert [c.status for c in result.checks[-2:]] == [grade.MISS, grade.MISS]   # extra + forbidden
    assert result.findings[0].what == "extra row"


def test_a_second_row_on_a_key_paragraph_is_extra_not_a_second_chance(key, paragraphs):
    out = perfect(key, paragraphs)
    twin = copy.deepcopy(out.rows[1])
    twin.row_id = "ROW-X-9"
    out.rows.append(twin)
    result = grade_all(out, key)["EC-001"]
    assert result.status == grade.MISS and "1 extra" in result.summary


def test_the_demo_row_is_not_the_extractors_and_is_never_graded(key, paragraphs):
    out = perfect(key, paragraphs)
    demo = copy.deepcopy(out.rows[0])
    demo.row_id, demo.origin, demo.source_paragraph_id = "ROW-X-7", "demo", "SRC-CSSF15627-P3"
    out.rows.append(demo)
    result = grade_all(out, key)
    assert result["EC-001"].status == grade.PASS and result["EC-009"].status == grade.PASS


@pytest.mark.parametrize("field,value,what", [
    ("offset", {"unit": "calendar_days", "amount": 30}, "offset"),          # the I-1 value
    ("frequency", "monthly", "frequency"),
    ("anchor", "month_end", "anchor"),
    ("recipient_code", "CSSF", "recipient"),
])
def test_a_wrong_field_is_a_miss_with_expected_and_actual(key, paragraphs, field, value, what):
    out = perfect(key, paragraphs)
    setattr(row_of(out, "OBL-02", key), field, value)
    finding = grade_all(out, key)["EC-001"].findings[0]
    assert finding.what == what and finding.subject.startswith("OBL-02")
    assert finding.expected != finding.actual


def test_the_applicability_sentence_is_never_matched_by_code_it_goes_to_the_operator(key, paragraphs):
    """H-068 (operator, 2026-11-21): free text is listed key against output, not exact-matched."""
    out = perfect(key, paragraphs)
    row_of(out, "OBL-02", key).applicability_rule = "The undertaking is established in Luxembourg."
    result = grade_all(out, key)
    assert result["EC-001"].status == grade.PASS             # structured fields still all match
    listed = [c for c in result["EC-002"].checks if c.label == "OBL-02 applicability rule"]
    assert [c.status for c in listed] == [grade.FOR_OPERATOR]
    assert "Fund is established in Luxembourg" in listed[0].note           # the key's sentence
    assert "The undertaking is established in Luxembourg." in listed[0].note   # the output's


def test_ec_002_lists_every_name_and_every_sentence_and_a_missing_row_too(key, paragraphs):
    out = perfect(key, paragraphs)
    out.rows = [r for r in out.rows if r.source_paragraph_id != "SRC-CNMV-P1"]
    checks = grade_all(out, key)["EC-002"].checks
    assert len(checks) == 12 and {c.status for c in checks} == {grade.FOR_OPERATOR}
    assert next(c.note for c in checks if c.label.startswith("OBL-04")).endswith(
        "no row extracted")


def test_the_structured_fields_stay_exact_after_the_change(key, paragraphs):
    """Only the sentence moved to the operator. A wrong offset or a missing row still misses."""
    out = perfect(key, paragraphs)
    row_of(out, "OBL-02", key).applicability_rule = "something else entirely"
    row_of(out, "OBL-02", key).offset = {"unit": "calendar_days", "amount": 30}
    findings = grade_all(out, key)["EC-001"].findings
    assert [f.what for f in findings] == ["offset"]


def test_the_quote_is_compared_under_qn_1(key, paragraphs):
    out = perfect(key, paragraphs)
    row = row_of(out, "OBL-01", key)
    row.quote = "  no later  than 10 calendar days\nafter the end of each month "   # same under QN-1
    assert grade_all(out, key)["EC-001"].status == grade.PASS
    row.quote = "no later than 10 calendar days after the end of each"             # truncated
    result = grade_all(out, key)["EC-001"]
    assert result.status == grade.MISS and result.findings[0].what == "quote (under QN-1)"
    # ...although the quote check alone still passes a truncated quote:
    assert quote_check.check_quote(row.quote, row.source_paragraph_id, paragraphs).passed


@pytest.mark.parametrize("text", [
    "the depositary", "administrator", "fund administrator (may transmit the report)",
    "Fund administrator or AIFM", ""])
def test_t_map_1_b_text_that_does_not_map_is_a_miss_that_shows_the_text(key, paragraphs, text):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-01", key).responsible_role = text      # the key expects "Fund administrator"
    findings = grade_all(out, key)["EC-001"].findings
    assert len(findings) == 1
    assert findings[0].what.startswith("responsible role")
    assert findings[0].expected == "Fund administrator"
    assert findings[0].actual == f"{text!r} → no match"


def test_a_mapped_role_that_is_the_wrong_party_is_a_miss(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-01", key).responsible_role = "the AIFM"
    finding = grade_all(out, key)["EC-001"].findings[0]
    assert finding.actual == "'the AIFM' → AIFM"


def test_a_role_written_in_the_sources_own_words_still_maps(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-04", key).responsible_role = "a local reporting agent"
    assert grade_all(out, key)["EC-001"].status == grade.PASS
    assert lookup.map_party("a local reporting agent") == "Local reporting agent (Spain)"


# --- EC-003 ---------------------------------------------------------------------------------

def test_ec_003_a_business_day_rule_the_source_does_not_state_is_a_miss(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-01", key).business_day_rule = "roll_forward"
    result = grade_all(out, key)["EC-003"]
    assert result.status == grade.MISS
    assert (result.findings[0].expected, result.findings[0].actual) == (
        "not_confirmed", "roll_forward")


def test_ec_003_a_computed_date_is_a_miss_but_a_date_copied_from_the_source_is_not(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-01", key).obligation_name = "Monthly report, due 2027-01-11"
    assert grade_all(out, key)["EC-003"].status == grade.MISS
    row_of(out, "OBL-01", key).obligation_name = "Monthly report"
    row_of(out, "OBL-01", key).applicability_rule = "Subject to the Law of 17 December 2010"
    assert "17 December 2010" in " ".join(paragraphs.values())   # the test reads a real source date
    assert grade_all(out, key)["EC-003"].status == grade.PASS


# --- EC-005 and EC-006 ----------------------------------------------------------------------

@pytest.mark.parametrize("code,flag_id", [("OBL-03", "C-1"), ("OBL-05", "C-2")])
def test_a_missed_cross_source_conflict_is_a_miss(key, paragraphs, code, flag_id):
    out = perfect(key, paragraphs)
    row_of(out, code, key).flags = []
    result = grade_all(out, key)
    assert result["EC-005"].status == grade.MISS
    assert flag_id in result["EC-005"].findings[0].subject
    assert result["EC-006"].status == grade.MISS        # only 1 cross-source flag is left


def test_a_flag_citing_the_wrong_paragraph_or_a_made_up_quote_does_not_count(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-03", key).flags = [_flag("SRC-PRACT-P2", paragraphs)]      # wrong paragraph
    assert grade_all(out, key)["EC-005"].status == grade.MISS
    out = perfect(key, paragraphs)
    row_of(out, "OBL-03", key).flags[0]["other_quote"] = "four months and a fortnight"
    assert grade_all(out, key)["EC-005"].status == grade.MISS
    # The right words but the wrong paragraph ID: the ID must be the expected one on its own
    # (the app's guardrail would refuse this flag; the grader must not depend on that).
    out = perfect(key, paragraphs)
    row_of(out, "OBL-03", key).flags[0]["other_paragraph_id"] = "SRC-PRACT-P2"
    assert grade_all(out, key)["EC-005"].status == grade.MISS


def test_false_alarms_on_the_clean_row_and_internal_flags_are_misses(key, paragraphs):
    out = perfect(key, paragraphs)
    row_of(out, "OBL-01", key).flags = [_flag("SRC-PRACT-P3", paragraphs)]
    result = grade_all(out, key)["EC-006"]
    assert result.status == grade.MISS
    assert [c.status for c in result.checks] == [grade.MISS, grade.PASS, grade.MISS]
    out = perfect(key, paragraphs)
    row_of(out, "OBL-02", key).flags = [_flag("SRC-PRACT-P1", paragraphs, kind="internal")]
    assert [c.status for c in grade_all(out, key)["EC-006"].checks][1] == grade.MISS


def test_a_broken_quote_check_makes_ec_005_miss(key, paragraphs, monkeypatch):
    """The altered quote must FAIL the check. If the check let it through, EC-005 must say so."""
    monkeypatch.setattr(cases, "check_quote",
                        lambda *a, **k: quote_check.QuoteCheck(True))
    out = perfect(key, paragraphs)
    result = grade_all(out, key)["EC-005"]
    assert result.status == grade.MISS
    assert result.findings[-1].subject == cases.ALTERED_QUOTE


# --- The copy cases -------------------------------------------------------------------------

def test_every_copy_case_behaves_as_qn_1_says(key, paragraphs):
    results = cases.run_copy_cases(key, paragraphs)
    assert len(results) == 10
    assert all(c.ok for c in results), [(c.case_id, c.expected, c.actual) for c in results
                                        if not c.ok]
    by_id = {c.case_id: c for c in results}
    assert by_id[cases.ALTERED_QUOTE].scored_under == "EC-005"
    assert by_id["truncated"].actual == "pass"            # still a verbatim piece
    assert by_id["non_breaking_space"].actual == "fail"   # Unicode forms are not normalised


def test_the_copy_cases_do_not_edit_the_sources(key, paragraphs):
    before = copy.deepcopy(paragraphs)
    cases.run_copy_cases(key, paragraphs)
    assert paragraphs == before


# --- A real stand-in run, read from the database --------------------------------------------

@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    connection = connect(settings.database_path)
    yield connection
    connection.close()


def test_a_stand_in_run_is_graded_and_stamped(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    report = stage_a_module.evaluate_stage_a(conn, run_id)
    assert report["counts_for_cycle"] is False
    assert report["does_not_count_because"] == [stage_a_module.STAND_IN_STAMP]
    assert report["rows_drafted_by_the_extractor"] == 6 and report["demo_rows_not_graded"] == 0
    by_id = {c["id"]: c for c in report["criteria"]}
    # The stand-in answers were written from the paragraphs, not from the key (CR-016), so the
    # result is a fixed, known one. Every structured field matches; the sentences go to the operator.
    assert by_id["EC-001"]["status"] == grade.PASS and by_id["EC-001"]["findings"] == []
    assert by_id["EC-002"]["status"] == grade.FOR_OPERATOR and len(by_id["EC-002"]["checks"]) == 12
    assert by_id["EC-003"]["status"] == grade.PASS
    assert by_id["EC-009"]["status"] == grade.PASS
    assert by_id["EC-005"]["status"] == grade.MISS        # the stand-in verifier makes 1 flag
    assert [f["subject"] for f in by_id["EC-005"]["findings"]] == ["C-2 caught on OBL-05"]


def test_the_coverage_list_equals_the_apps_own_coverage_view(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    run, out = stage_a_module.load_stage_a(conn, run_id)
    app_view = [p["paragraph_id"] for p in decisions.unused_paragraphs(conn, run)]
    assert grade.uncited_paragraphs(out) == app_view and len(app_view) == 7


def test_grading_writes_nothing_to_the_database(conn, settings):
    run_id = flow.start_to_g1(conn, settings)
    tables = ("runs", "rows", "quote_checks", "flags", "paragraphs", "audit_log", "trace")
    count = lambda: [conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables]
    before = count()
    stage_a_module.evaluate_stage_a(conn, run_id)
    assert count() == before


def test_a_run_with_the_planted_row_on_is_stamped_and_the_demo_row_is_not_graded(conn, settings):
    run_id = flow.start_to_g1(conn, settings, demo=True)
    report = stage_a_module.evaluate_stage_a(conn, run_id)
    assert report["demo_rows_not_graded"] == 1 and report["rows_drafted_by_the_extractor"] == 6
    assert any("planted-row" in reason for reason in report["does_not_count_because"])
    assert {c["id"]: c for c in report["criteria"]}["EC-009"]["status"] == grade.PASS


@pytest.mark.parametrize("activity,counts", [("evaluation", True), ("rehearsal", False)])
def test_a_real_run_counts_only_when_labelled_evaluation(conn, settings, activity, counts):
    run_id = flow.start_to_g1(conn, settings)
    conn.execute("UPDATE runs SET agents_mode = 'real', spend_activity = ? WHERE run_id = ?",
                 (activity, run_id))
    conn.commit()
    report = stage_a_module.evaluate_stage_a(conn, run_id)
    assert report["counts_for_cycle"] is counts
    assert (report["does_not_count_because"] == []) is counts


def test_a_run_without_stored_stage_a_output_is_not_gradable(conn, settings):
    with pytest.raises(stage_a_module.NotGradable, match="no run RUN-NOPE"):
        stage_a_module.evaluate_stage_a(conn, "RUN-NOPE")
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")
    conn.commit()
    run_id = runs.start_run(conn, settings, lambda *a, **k: None, fund_id=flow.FUND_ID,
                            started_by=flow.SPECIALIST, demo_planted_row=False,
                            demo_fail_step1=False)     # scheduled stage never runs: no output
    with pytest.raises(stage_a_module.NotGradable, match="nothing to grade"):
        stage_a_module.evaluate_stage_a(conn, run_id)


def test_the_grader_never_imports_the_agents_or_the_model_layer():
    """It reads stored output only: no agent function, no CrewAI (T-MODE-1 stays true)."""
    import pathlib
    source = "\n".join(p.read_text(encoding="utf-8") for p in
                       pathlib.Path(stage_a_module.__file__).parent.glob("*.py"))
    for forbidden in ("runtime.agents", "crewai", "extract_rows", "check_conflicts", "import openai"):
        assert forbidden not in source.replace("`extract_rows`", ""), forbidden
