"""Plain words for a row's frequency, anchor and offset, so the pages print words, not codes.

A row stores the extractor's vocabulary (sad.md §2): `frequency` and `anchor` as codes, `offset`
as JSON. B4's date engine reads those values; the pages read the words made here. Plain code.
"""

import calendar
import json

FREQUENCY_WORDS = {"monthly": "monthly", "quarterly": "quarterly", "annually": "annually",
                   "on_occurrence": "on occurrence"}

ANCHOR_WORDS = {"month_end": "month end", "quarter_end": "quarter end",
                "financial_year_end": "financial year end",
                "event_awareness": "becoming aware of the event",
                "event_occurrence": "the event"}


def offset_words(offset: str | dict) -> str:
    """{"unit": "calendar_days", "amount": 10} → "10 calendar days"; months likewise;
    {"unit": "fixed_day_month", "day": 31, "month": 10, "year_shift": 1} →
    "31 October of the following year"."""
    o = json.loads(offset) if isinstance(offset, str) else offset
    if o["unit"] == "fixed_day_month":
        year = "of the following year" if o["year_shift"] else "of the same year"
        return f"{o['day']} {calendar.month_name[o['month']]} {year}"
    unit = {"calendar_days": "calendar day", "months": "month"}[o["unit"]]
    return f"{o['amount']} {unit}{'' if o['amount'] == 1 else 's'}"


def due_words(offset: str | dict, anchor: str) -> str:
    """When the rule falls due, in one phrase: "10 calendar days after month end", or for a fixed
    day "31 October of the following year" (the anchor only says which year it counts from)."""
    o = json.loads(offset) if isinstance(offset, str) else offset
    if o["unit"] == "fixed_day_month":
        return offset_words(o)
    return f"{offset_words(o)} after {ANCHOR_WORDS.get(anchor, anchor)}"
