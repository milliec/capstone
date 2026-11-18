"""B3 step 4: the fund facts loader, the stand-in answers and the three agent functions. No model.

The stand-in answers go through the same guardrails as a real model's output, so these tests
also prove the fixed answers are valid. Not wired into the stages yet (B3 step 5).
"""

import pytest

from backend.domain import sources
from backend.domain.fund_facts import load_fund_facts
from backend.domain.quote_check import check_quote
from backend.runtime import agents
from backend.settings import load_settings

STAND_IN_FILES = ["extractor.yaml", "verifier.yaml", "judge.yaml"]


@pytest.fixture(scope="module")
def paragraphs():
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


def _document_paragraphs(paragraphs, document_id):
    return {pid: text for pid, text in paragraphs.items() if pid.startswith(document_id + "-P")}


@pytest.fixture
def all_rows(settings, paragraphs):
    """Every stand-in row, as stage A will produce them (one call per primary document)."""
    codes = list(sources.list_recipients())
    rows = []
    for doc in sources.list_documents():
        if doc["type"] == "primary":
            rows += agents.extract_rows(
                settings, document_id=doc["id"],
                paragraphs=_document_paragraphs(paragraphs, doc["id"]), recipient_codes=codes)
    return [r.model_dump() for r in rows]


# --- The fund facts loader (W-10, CR-016) ---------------------------------------------------

def test_fund_facts_keep_only_id_fact_and_value():
    loaded = load_fund_facts()
    assert [f["fact_id"] for f in loaded["facts"]] == [f"FACT-0{n}" for n in range(1, 8)]
    assert all(set(f) == {"fact_id", "fact", "value"} for f in loaded["facts"])
    assert loaded["events"] == [{"event_id": "EVT-01", "event": (
        "A new investor's holding crossed the 25% beneficial-ownership threshold")}]
    assert {f["fact_id"]: f["value"] for f in loaded["facts"]}["FACT-05"] == "No"  # bold removed


def test_fund_facts_leak_no_answers():
    text = str(load_fund_facts())
    # The "Decides" column's values and the test note's content.
    for leaked in ("Decides", "→", "unsure", "does not apply", "Spain A01", "U1.1", "RBE",
                   "Test note", "awareness", "2027", "**"):
        assert leaked not in text, leaked


def test_recipient_codes_have_display_names():
    assert sources.list_recipients() == {
        "CSSF": "CSSF", "AED": "Administration de l'enregistrement, des domaines et de la TVA",
        "CNMV": "CNMV", "LBR": "Luxembourg Business Registers"}


# --- The stand-in answers ----------------------------------------------------------------

def test_stand_in_files_carry_no_answer_key_content():
    """CR-016: no answer-key IDs, no test notes, no reference to the key file."""
    for name in STAND_IN_FILES:
        text = (agents.STAND_IN_DIR / name).read_text(encoding="utf-8")
        for banned in ("OBL-", "AMD-", "C-1", "C-2", "I-1", "Test note", "Planted conflict",
                       "expected-obligation-library"):
            assert banned not in text, f"{banned} in {name}"


def test_extractor_gives_six_rows_whose_quotes_pass_the_quote_check(all_rows, paragraphs):
    assert len(all_rows) == 6
    for row in all_rows:
        assert check_quote(row["quote"], row["source_paragraph_id"], paragraphs).passed, row


def test_verifier_gives_exactly_one_flag(settings, all_rows, paragraphs):
    flags = {}
    for row in all_rows:
        result = agents.check_conflicts(
            settings, row=row, quote_check=check_quote(row["quote"], row["source_paragraph_id"],
                                                       paragraphs),
            sources=paragraphs)
        if result:
            flags[row["source_paragraph_id"]] = result
    assert list(flags) == ["SRC-UCILAW-P3"]
    assert flags["SRC-UCILAW-P3"][0].other_paragraph_id == "SRC-PRACT-P1"


def test_verifier_gives_no_flags_for_a_row_it_has_no_answer_for(settings, paragraphs):
    row = {"source_paragraph_id": "SRC-UCILAW-P1", "quote": "financial year-end"}
    assert agents.check_conflicts(settings, row=row, quote_check=None, sources=paragraphs) == []


def test_judge_gives_one_verdict_per_row_with_exactly_one_unsure(settings, all_rows):
    facts = load_fund_facts()
    verdicts = [agents.judge_applicability(settings, row=row, fund_facts=facts).verdict
                for row in all_rows]
    assert len(verdicts) == 6
    assert verdicts.count("unsure") == 1
    assert verdicts.count("does_not_apply") == 1


# --- Failures and real mode ---------------------------------------------------------------

def test_a_stand_in_answer_that_fails_its_guardrail_raises_invalid_output(settings, paragraphs,
                                                                          monkeypatch):
    bad = {"SRC-VATLAW": [{"obligation_name": "Due 2027-10-31"}]}
    monkeypatch.setattr(agents, "_stand_in", lambda name: bad)
    with pytest.raises(agents.InvalidOutput):
        agents.extract_rows(settings, document_id="SRC-VATLAW",
                            paragraphs=_document_paragraphs(paragraphs, "SRC-VATLAW"),
                            recipient_codes=["AED"])


def test_a_gap_in_the_stand_in_files_is_loud(settings):
    with pytest.raises(agents.MissingStandInOutput):
        agents.extract_rows(settings, document_id="SRC-PRACT", paragraphs={}, recipient_codes=[])
    with pytest.raises(agents.MissingStandInOutput):
        agents.judge_applicability(settings, row={"source_paragraph_id": "SRC-X-P1"},
                                   fund_facts=load_fund_facts())


def test_real_mode_is_refused_by_all_three_functions():
    real = load_settings({"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike"})
    with pytest.raises(agents.RealAgentsNotBuilt):
        agents.extract_rows(real, document_id="SRC-VATLAW", paragraphs={}, recipient_codes=[])
    with pytest.raises(agents.RealAgentsNotBuilt):
        agents.check_conflicts(real, row={}, quote_check=None, sources={})
    with pytest.raises(agents.RealAgentsNotBuilt):
        agents.judge_applicability(real, row={}, fund_facts={})
