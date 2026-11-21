"""The stage A golden set is read from the answer key at grade time (operator, 2026-11-21).

No model. Checks that the loader reads what the key says (6 rows, their quotes, C-1, C-2, the
clean OBL-01, I-1, the 7 uncited paragraphs) and stops loudly when the key changes shape.
"""

import pytest

from backend.domain import quote_check, sources
from backend.evaluation import golden


@pytest.fixture(scope="module")
def key():
    return golden.load_golden_set()


def test_six_rows_in_the_keys_order(key):
    assert [r.code for r in key.rows] == [f"OBL-0{n}" for n in range(1, 7)]


def test_each_golden_quote_is_in_its_paragraph(key):
    paragraphs = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    for row in key.rows:
        assert quote_check.check_quote(row.quote, row.source_paragraph_id, paragraphs).passed, \
            row.code


def test_fields_are_translated_into_the_apps_vocabulary(key):
    obl_05 = key.row("OBL-05")
    assert (obl_05.frequency, obl_05.anchor, obl_05.recipient_code) == (
        "on_occurrence", "event_awareness", "LBR")
    assert key.row("OBL-06").offset == {"unit": "fixed_day_month", "day": 31, "month": 10,
                                        "year_shift": 1}
    assert key.row("OBL-03").offset == {"unit": "months", "amount": 6}
    assert key.row("OBL-04").responsible_role == "Local reporting agent (Spain)"
    assert key.row("OBL-06").obligation_name == "Annual VAT return"     # "(decoy)" is not the name


def test_the_expected_flags(key):
    assert [(f.flag_id, f.row_code, f.other_paragraph_id) for f in key.cross_source_flags] == [
        ("C-1", "OBL-03", "SRC-PRACT-P1"), ("C-2", "OBL-05", "SRC-PRACT-P2")]
    assert key.clean_row_codes == ("OBL-01",)
    assert key.internal_case == ("OBL-02", "offset", {"unit": "calendar_days", "amount": 30})


def test_the_seven_uncited_paragraphs_are_derived_not_copied(key):
    assert set(key.uncited_paragraph_ids) == {
        "SRC-UCILAW-P1", "SRC-CSSF15627-P1", "SRC-CSSF15627-P3", "SRC-CNMV-P2",
        "SRC-PRACT-P1", "SRC-PRACT-P2", "SRC-PRACT-P3"}
    assert not set(key.uncited_paragraph_ids) & {r.source_paragraph_id for r in key.rows}


def test_a_changed_key_stops_the_load(tmp_path, monkeypatch):
    text = golden.KEY_FILE.read_text(encoding="utf-8")
    broken = tmp_path / "key.md"
    broken.write_text(text.replace("| Month-end |", "| Fortnightly |"), encoding="utf-8")
    monkeypatch.setattr(golden, "KEY_FILE", broken)
    with pytest.raises(golden.GoldenSetError, match="Fortnightly"):
        golden.load_golden_set()


def test_the_expected_verdicts_and_their_facts(key):
    """KEY §2, read at grade time. OBL-04 is "unsure": a confident "applies" is the error to catch."""
    assert [(v.code, v.verdict) for v in key.verdicts] == [
        ("OBL-01", "applies"), ("OBL-02", "applies"), ("OBL-03", "applies"),
        ("OBL-04", "unsure"), ("OBL-05", "applies"), ("OBL-06", "does_not_apply")]
    assert key.verdict("OBL-04").fact_ids == ("FACT-03", "FACT-04")
    assert key.verdict("OBL-05").fact_ids == ("FACT-06", "EVT-01")
    assert key.verdict("OBL-06").fact_ids == ("FACT-05",)


def test_every_fact_the_key_names_exists_in_the_fund_profile(key):
    from backend.domain.fund_facts import load_fund_facts
    facts = load_fund_facts()
    existing = {f["fact_id"] for f in facts["facts"]} | {e["event_id"] for e in facts["events"]}
    for v in key.verdicts:
        assert set(v.fact_ids) <= existing, v.code


def test_a_changed_verdict_word_stops_the_load(tmp_path, monkeypatch):
    text = golden.KEY_FILE.read_text(encoding="utf-8")
    broken = tmp_path / "key.md"
    broken.write_text(text.replace("**Unsure**", "**Perhaps**"), encoding="utf-8")
    monkeypatch.setattr(golden, "KEY_FILE", broken)
    with pytest.raises(golden.GoldenSetError, match="Perhaps"):
        golden.load_golden_set()
