"""The source loader (W-02) keeps paragraph text only (CR-016, DL-39).

This is the loader half of T-LEAK-1. The prompt half (every rendered task prompt is free of the
answers) comes with the task templates in B3 step 7.
"""

import re

from backend.domain import sources
from backend.settings import ROOT

MOCK_FILE = ROOT / "project-context/1.define/mock-data/mock-regulatory-sources.md"


def _all_text(paragraphs):
    return "\n".join(p["text"] for p in paragraphs)


def test_loads_13_paragraphs_from_6_documents_in_order():
    paragraphs = sources.load_paragraphs()
    ids = [p["paragraph_id"] for p in paragraphs]
    assert ids == [
        "SRC-CSSF15627-P1", "SRC-CSSF15627-P2", "SRC-CSSF15627-P3",
        "SRC-UCILAW-P1", "SRC-UCILAW-P2", "SRC-UCILAW-P3",
        "SRC-CNMV-P1", "SRC-CNMV-P2",
        "SRC-RBELAW-P1",
        "SRC-VATLAW-P1",
        "SRC-PRACT-P1", "SRC-PRACT-P2", "SRC-PRACT-P3",
    ]
    assert all(p["document_id"] == p["paragraph_id"].rsplit("-P", 1)[0] for p in paragraphs)


def test_documents_five_primary_one_secondary():
    docs = sources.list_documents()
    assert [d["type"] for d in docs].count("primary") == 5
    assert [d["id"] for d in docs if d["type"] == "secondary"] == ["SRC-PRACT"]
    assert all(d["title"] for d in docs)


def test_paragraph_text_is_the_source_wording():
    by_id = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    # Line breaks are kept as in the file; the quote check (QN-1) collapses whitespace later.
    assert " ".join(by_id["SRC-UCILAW-P3"].split()) == (
        "An undertaking for collective investment subject to Part II of this law shall publish an "
        "audited annual report and file it with the CSSF within six months of the end of the "
        "period to which it relates.")
    assert by_id["SRC-PRACT-P3"] == "The monthly U1.1 report is due 10 calendar days after month-end."


def test_no_note_warning_or_answer_reaches_the_paragraphs():
    text = _all_text(sources.load_paragraphs())
    # T-LEAK-1 (a) and (d): the phrases and answer-key IDs, matched as written in the mock files.
    for phrase in ("Test note", "Planted conflict", "correct verdict", "MOCK DATA", "OBL-", "AMD-",
                   "C-1", "C-2", "I-1", "FACT-", "Decides"):
        assert phrase not in text, phrase


def test_no_blockquote_text_reaches_the_paragraphs():
    """T-LEAK-1 (c): the text of every blockquote in the mock file is absent."""
    text = " ".join(_all_text(sources.load_paragraphs()).split())
    quoted = [re.sub(r"[>*_`]", "", line).strip()
              for line in MOCK_FILE.read_text(encoding="utf-8").splitlines()
              if line.lstrip().startswith(">")]
    quoted = [q for q in quoted if len(q) > 15]  # skip near-empty lines like ">"
    assert quoted, "the mock file should have blockquotes to check against"
    for q in quoted:
        assert q not in text, q


def test_amendments_are_never_loaded():
    paragraphs = sources.load_paragraphs()
    assert "SRC-UCILAW-P4" not in [p["paragraph_id"] for p in paragraphs]
    assert "within five months" not in _all_text(paragraphs)  # AMD-01's changed wording


def test_a_note_without_a_blank_line_is_not_glued_onto_the_paragraph():
    md = "**SRC-X-P1**\nReal text.\n> *Test note: the answer.*\nStray line after the note.\n"
    assert sources.parse_paragraphs(md) == [
        {"paragraph_id": "SRC-X-P1", "document_id": "SRC-X", "text": "Real text."}]


def test_a_paragraph_for_an_unlisted_document_is_refused(monkeypatch):
    original = sources.load_regulation_config()
    monkeypatch.setattr(sources, "load_regulation_config",
                        lambda: {**original, "documents": original["documents"][:-1]})
    try:
        sources.load_paragraphs()
    except sources.SourceFileError as e:
        assert "SRC-PRACT" in str(e)
    else:
        raise AssertionError("expected SourceFileError")
