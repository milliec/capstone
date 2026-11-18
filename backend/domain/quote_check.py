"""The quote check (W-04, rule QN-1 in sad.md): is a row's quote word for word in its paragraph?

Plain code, no model. A string comparison is a fact, not an opinion, so code decides it and a
model can never overrule it (DM-04, T-W04-6). A failed check blocks approval of the row with no
override (CR-005); that refusal is already in services/decisions.py (QUOTE_CHECK_FAILED, B2).

QN-1, the whole rule:
  1. Trim whitespace at the start and end.
  2. Replace every run of whitespace (spaces, tabs, line breaks) with one space.
     Reason: the mock paragraphs wrap mid-sentence, while a quote is written on one line.
  3. Nothing else. Case-sensitive. Punctuation, typographic quotes, dashes and Unicode forms are
     NOT normalised: any difference in them fails.
  4. A row with no paragraph ID, or an ID that matches no loaded paragraph, fails.
The quote must then occur as one unbroken piece of the paragraph.
"""

import re
from dataclasses import dataclass

# QN-1 step 2 names spaces, tabs and line breaks. Written out on purpose instead of "\s", because
# Python's "\s" also matches Unicode spaces such as a non-breaking space, and step 3 says Unicode
# forms are not normalised.
_WHITESPACE_RUN = re.compile(r"[ \t\r\n\f\v]+")


@dataclass(frozen=True)
class QuoteCheck:
    """The result for one row. `mismatch` says why it failed (None when it passed)."""

    passed: bool
    mismatch: str | None = None

    @property
    def result(self) -> str:
        """'pass' or 'fail', the values the quote_checks table stores."""
        return "pass" if self.passed else "fail"


def normalise(text: str) -> str:
    """QN-1 steps 1 and 2: trim, then collapse every whitespace run to one space."""
    return _WHITESPACE_RUN.sub(" ", text.strip(" \t\r\n\f\v"))


def check_quote(quote: str | None, paragraph_id: str | None,
                paragraphs: dict[str, str]) -> QuoteCheck:
    """Check one row's quote against the loaded paragraphs ({paragraph_id: text}).

    The order of the failures is only about which reason is shown; any one of them fails the row.
    """
    if not paragraph_id:
        return QuoteCheck(False, "The row cites no paragraph ID.")
    if paragraph_id not in paragraphs:
        return QuoteCheck(False, f"The row cites {paragraph_id}, which is not a loaded paragraph.")
    wanted = normalise(quote or "")
    if not wanted:
        # Not named in QN-1, but an empty string is "in" every paragraph, so without this an
        # empty quote would pass. A row with no quote is unsourced (CR-005).
        return QuoteCheck(False, "The row has no quote.")
    if wanted not in normalise(paragraphs[paragraph_id]):
        return QuoteCheck(False, f"The quote is not word for word in {paragraph_id}.")
    return QuoteCheck(True)
