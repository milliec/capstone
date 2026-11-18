"""The quote check (W-04, QN-1): T-W04-1 to T-W04-5, run with no model (SD NFR-011).

T-W04-6 (the verifier claims "quote ok" for a row the code failed; the code result stands) needs
the verifier's output, so it comes with the agent functions in B3 step 4 or 5. The approval
refusal for a failed check (QUOTE_CHECK_FAILED) is B2's and is tested in test_decision_checks.py.

T-W04-1 reads the answer key's quotes. That is allowed here: the answer key must never reach a
prompt or a run-time fixture (CR-016), and a test is neither.
"""

import re

import pytest

from backend.domain import sources
from backend.domain.quote_check import check_quote, normalise
from backend.settings import ROOT

KEY = ROOT / "project-context/1.define/mock-data/expected-obligation-library.md"


@pytest.fixture(scope="module")
def paragraphs():
    return {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}


def _answer_key_quotes():
    """[(OBL id, paragraph id, quote)] from answer key §1: the rows table and the quotes table."""
    text = KEY.read_text(encoding="utf-8")
    para_of = dict(re.findall(r"^\| `(OBL-\d+)` \|.*\| `(SRC-[A-Z0-9]+-P\d+)` \|$", text, re.M))
    quotes = re.findall(r'^\| `(OBL-\d+)` \| "(.+)" \|$', text, re.M)
    return [(obl, para_of[obl], q) for obl, q in quotes]


def test_w04_1_the_six_answer_key_quotes_pass(paragraphs):
    cases = _answer_key_quotes()
    assert len(cases) == 6
    for obl, para_id, quote in cases:
        assert check_quote(quote, para_id, paragraphs).passed, obl


def test_w04_2_one_word_changed_fails(paragraphs):
    obl, para_id, quote = _answer_key_quotes()[0]
    assert obl == "OBL-01" and "calendar" in quote
    result = check_quote(quote.replace("calendar", "business"), para_id, paragraphs)
    assert not result.passed and result.result == "fail"
    assert para_id in result.mismatch


def test_w04_3_whitespace_differences_pass(paragraphs):
    # SRC-UCILAW-P3 wraps in the file between "annual" and "report".
    quote = "publish an audited annual  report and file it with the CSSF "
    assert "annual\nreport" in paragraphs["SRC-UCILAW-P3"]  # the line break the quote spans
    assert check_quote(quote, "SRC-UCILAW-P3", paragraphs).passed
    assert check_quote("\tfile it with the CSSF\n", "SRC-UCILAW-P3", paragraphs).passed


@pytest.mark.parametrize("change", [
    lambda q: q.replace("'", "’"),   # straight apostrophe made typographic
    lambda q: q.replace("Administration", "administration"),  # one letter's case
])
def test_w04_4_typographic_or_case_changes_fail(paragraphs, change):
    quote = "the Administration de l'enregistrement"
    assert check_quote(quote, "SRC-UCILAW-P2", paragraphs).passed
    assert not check_quote(change(quote), "SRC-UCILAW-P2", paragraphs).passed


def test_w04_5_no_paragraph_id_or_an_unknown_one_fails(paragraphs):
    quote = "within six months of the end of the period to which it relates"
    assert not check_quote(quote, None, paragraphs).passed
    assert not check_quote(quote, "", paragraphs).passed
    unknown = check_quote(quote, "SRC-UCILAW-P9", paragraphs)
    assert not unknown.passed and "SRC-UCILAW-P9" in unknown.mismatch


def test_an_empty_quote_fails(paragraphs):
    assert not check_quote("", "SRC-UCILAW-P3", paragraphs).passed
    assert not check_quote("   \n", "SRC-UCILAW-P3", paragraphs).passed


def test_a_quote_from_another_paragraph_fails(paragraphs):
    """The quote must be in the CITED paragraph, not just somewhere in the sources."""
    quote = "within six months of the end of the period to which it relates"
    assert not check_quote(quote, "SRC-PRACT-P1", paragraphs).passed


def test_a_non_breaking_space_is_not_normalised():
    """QN-1 step 3: Unicode forms are not normalised, so a non-breaking space is a difference."""
    assert normalise("a b") == "a b"
    assert not check_quote("a b", "P", {"P": "a b"}).passed
