"""The golden set for stage A: read from the answer key at grade time, never copied (operator,
2026-11-21). The key is the only source, so it cannot drift from a second copy.

What is read (answer key = expected-obligation-library.md):
  §1  the 6 expected rows and the 6 verbatim quotes  → EC-001, EC-003
  §3  the expected verifier flags (C-1, C-2, the clean OBL-01, I-1) → EC-005, EC-006
  The 7 paragraphs no row may cite = the loaded paragraphs minus the 6 rows' paragraphs → EC-009
Not read: §2 (stage B verdicts) and §4 (the 22 entries, stage C: EC-007 is already a Tier 1 test).

The key writes its values in words ("Month-end", "+10 calendar days"). The tables below translate
those words into the app's own vocabulary (schemas.py). A word the tables do not know stops the
load with an error: a changed key is noticed, never guessed at.
"""

import re
from dataclasses import dataclass

from backend.domain import sources
from backend.settings import ROOT

KEY_FILE = ROOT / "project-context/1.define/mock-data/expected-obligation-library.md"

_FREQUENCY = {"Monthly": "monthly", "Quarterly": "quarterly", "Annually": "annually",
              "On occurrence": "on_occurrence"}
_ANCHOR = {"Month-end": "month_end", "Calendar quarter-end": "quarter_end",
           "Financial year-end": "financial_year_end",
           "Date the entity became aware of the event": "event_awareness"}
_MONTHS = {name: n for n, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September",
     "October", "November", "December"], start=1)}

NOT_CONFIRMED = "not_confirmed"   # every row's expected business-day rule (EC-003)


class GoldenSetError(Exception):
    """The answer key does not look the way this loader expects."""


@dataclass(frozen=True)
class GoldenRow:
    code: str                    # OBL-01 … OBL-06
    obligation_name: str
    frequency: str
    anchor: str
    offset: dict
    recipient_code: str
    responsible_role: str        # the profile's party name, or "not stated in source"
    applicability_rule: str
    source_paragraph_id: str
    quote: str


@dataclass(frozen=True)
class GoldenFlag:
    flag_id: str                 # C-1, C-2
    row_code: str
    other_paragraph_id: str      # the secondary paragraph that disagrees


@dataclass(frozen=True)
class GoldenSet:
    rows: tuple[GoldenRow, ...]
    cross_source_flags: tuple[GoldenFlag, ...]
    clean_row_codes: tuple[str, ...]          # rows the verifier must not flag (OBL-01)
    internal_case: tuple[str, str, dict]      # I-1: row code, field, the changed offset
    uncited_paragraph_ids: tuple[str, ...]    # paragraphs no row may cite (7)

    def row_for_paragraph(self, paragraph_id: str) -> GoldenRow | None:
        return next((r for r in self.rows if r.source_paragraph_id == paragraph_id), None)

    def row(self, code: str) -> GoldenRow:
        return next(r for r in self.rows if r.code == code)


# --- Reading the key's markdown tables --------------------------------------------------------

def _section(text: str, start: str, end: str) -> str:
    return text[text.index(start): text.index(end, text.index(start))]


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _bare(cell: str) -> str:
    """`OBL-01` → OBL-01 (drop the backticks, asterisks and spaces)."""
    return cell.strip("`* ")


def _lookup(table: dict, word: str, what: str) -> str:
    if word not in table:
        raise GoldenSetError(f"The answer key has an unknown {what}: {word!r}")
    return table[word]


def _parse_offset(text: str) -> dict:
    """'+10 calendar days' → {calendar_days, 10}; '+6 months'; '31 October of the following year'."""
    if match := re.fullmatch(r"\+(\d+) calendar days?", text):
        return {"unit": "calendar_days", "amount": int(match.group(1))}
    if match := re.fullmatch(r"\+(\d+) months?", text):
        return {"unit": "months", "amount": int(match.group(1))}
    if match := re.fullmatch(r"(\d{1,2}) (\w+) of the following year", text):
        return {"unit": "fixed_day_month", "day": int(match.group(1)),
                "month": _lookup(_MONTHS, match.group(2), "month"), "year_shift": 1}
    raise GoldenSetError(f"The answer key has an unknown offset: {text!r}")


def _recipient_code(word: str) -> str:
    """The key writes some recipients as a code ("AED") and one as a name; accept either."""
    recipients = sources.list_recipients()
    if word in recipients:
        return word
    return _lookup({name: code for code, name in recipients.items()}, word, "recipient")


def _quotes(section_1: str) -> dict[str, str]:
    """The 'Expected verbatim quotes' table: {OBL code: quote}."""
    quotes = {}
    for line in section_1.splitlines():
        cells = _cells(line) if line.startswith("| `OBL-") else []
        if len(cells) == 2:
            quotes[_bare(cells[0])] = cells[1].strip('"')
    return quotes


def _rows(section_1: str) -> list[GoldenRow]:
    quotes = _quotes(section_1)
    rows = []
    for line in section_1.splitlines():
        cells = _cells(line) if line.startswith("| `OBL-") else []
        if len(cells) != 10:
            continue
        code, name, _pattern, frequency, anchor, offset, recipient, role, rule, paragraph = cells
        code = _bare(code)
        rows.append(GoldenRow(
            code=code, obligation_name=name.replace(" *(decoy)*", ""),
            frequency=_lookup(_FREQUENCY, frequency, "frequency"),
            anchor=_lookup(_ANCHOR, anchor, "anchor"), offset=_parse_offset(offset),
            recipient_code=_recipient_code(recipient), responsible_role=role,
            applicability_rule=rule, source_paragraph_id=_bare(paragraph),
            quote=quotes[code]))
    if len(rows) != 6:
        raise GoldenSetError(f"Expected 6 rows in answer key section 1, found {len(rows)}")
    return rows


def _flags(section_3: str, rows: list[GoldenRow]):
    """C-1 and C-2 (cross-source), the clean row, and I-1 (the injected internal case)."""
    by_code = {r.code: r for r in rows}
    cross, clean, internal = [], [], None
    for line in section_3.splitlines():
        cells = _cells(line) if line.startswith("| ") else []
        if len(cells) < 5:
            continue
        flag, kind, row_cell, report = _bare(cells[0]), cells[1], _bare(cells[2]), cells[3]
        if flag in ("C-1", "C-2"):
            own = by_code[row_cell].source_paragraph_id
            others = [p for p in re.findall(r"SRC-[A-Z0-9]+-P\d+", report) if p != own]
            if len(others) != 1:
                raise GoldenSetError(f"{flag}: cannot tell which paragraph disagrees")
            cross.append(GoldenFlag(flag, row_cell, others[0]))
        elif kind == "No flag":
            clean.append(row_cell)
        elif flag == "I-1":
            changed = re.search(r'"(\+\d+ calendar days?)"', report)
            if not changed:
                raise GoldenSetError("I-1: cannot find the changed offset")
            internal = (row_cell, "offset", _parse_offset(changed.group(1)))
    if len(cross) != 2 or not clean or internal is None:
        raise GoldenSetError("Answer key section 3 does not hold C-1, C-2, a clean row and I-1")
    return tuple(cross), tuple(clean), internal


def load_golden_set() -> GoldenSet:
    """Parse the answer key now. Cheap (one small file), so it is not cached: a test that edits a
    copy of the key sees the change."""
    text = KEY_FILE.read_text(encoding="utf-8")
    rows = _rows(_section(text, "## 1.", "## 2."))
    cross, clean, internal = _flags(_section(text, "## 3.", "## 4."), rows)
    cited = {r.source_paragraph_id for r in rows}
    uncited = tuple(p["paragraph_id"] for p in sources.load_paragraphs()
                    if p["paragraph_id"] not in cited)
    return GoldenSet(rows=tuple(rows), cross_source_flags=cross, clean_row_codes=clean,
                     internal_case=internal, uncited_paragraph_ids=uncited)
