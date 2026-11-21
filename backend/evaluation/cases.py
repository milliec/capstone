"""The code-only copy cases (DL-45, operator 2026-11-21): quote-check cases on COPIES of OBL-01's
quote. No model, nothing written to the run's tables, the mock sources never edited (US-013 c4).

`altered_quote` is the DL-45 case, scored under EC-005: one word of OBL-01's quote changed, which
must fail the quote check. The others are "ugly" variants, reported on their own line: each says
what QN-1 (quote_check.py) must do with it, and the case passes when the real check agrees.
`truncated` is the one to read twice: dropping the last word still gives a verbatim piece of the
paragraph, so the quote check PASSES it. Only the comparison with the answer key (EC-001) catches
it. Cases that need a model (`I-1`, the injection case) wait for the agents.
"""

from dataclasses import dataclass

from backend.domain.quote_check import check_quote
from backend.evaluation.golden import GoldenSet

ALTERED_QUOTE = "altered_quote"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    description: str
    scored_under: str          # "EC-005" or "reported only"
    expected: str              # "pass" or "fail": what QN-1 must do
    actual: str                # what the real quote check did
    ok: bool


def _cases(key: GoldenSet) -> list[tuple[str, str, str, str, str, str]]:
    """(case_id, description, scored_under, quote, paragraph_id, expected), all from OBL-01."""
    obl = key.row("OBL-01")
    q, p = obl.quote, obl.source_paragraph_id
    other = key.row("OBL-02").source_paragraph_id
    return [
        (ALTERED_QUOTE, "one word changed (\"later\" → \"earlier\")", "EC-005",
         q.replace("later", "earlier"), p, "fail"),
        ("extra_spaces_and_breaks", "double spaces, a tab and a line break inside the quote",
         "reported only", q.replace(" ", "  ", 1).replace(" ", "\t", 2).replace(" ", "\n", 3), p,
         "pass"),
        ("padded", "spaces, a tab and a line break around the quote", "reported only",
         f"  {q}\t\n", p, "pass"),
        ("different_case", "first letter capitalised", "reported only", q[0].upper() + q[1:], p,
         "fail"),
        ("non_breaking_space", "one ordinary space replaced by a non-breaking space",
         "reported only", q.replace(" ", " ", 1), p, "fail"),
        ("added_semicolon", "a semicolon added at the end (the paragraph has none there)",
         "reported only", q + ";", p, "fail"),
        ("truncated", ("last word dropped: still a verbatim piece, so the quote check passes "
                       "it (EC-001 catches it against the key)"),
         "reported only", q.rsplit(" ", 1)[0], p, "pass"),
        ("wrong_paragraph", "the right words, cited to another loaded paragraph",
         "reported only", q, other, "fail"),
        ("unknown_paragraph", "the right words, cited to a paragraph that is not loaded",
         "reported only", q, "SRC-NOPE-P9", "fail"),
        ("empty_quote", "an empty quote", "reported only", "", p, "fail"),
    ]


def run_copy_cases(key: GoldenSet, paragraphs: dict[str, str]) -> list[CaseResult]:
    """Run every case through the real quote check (`paragraphs` = {paragraph_id: text})."""
    results = []
    for case_id, description, scored_under, quote, paragraph_id, expected in _cases(key):
        actual = "pass" if check_quote(quote, paragraph_id, paragraphs).passed else "fail"
        results.append(CaseResult(case_id, description, scored_under, expected, actual,
                                  ok=actual == expected))
    return results
