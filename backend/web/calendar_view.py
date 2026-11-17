"""Display-only layout for page 7 · Calendar: month grouping and the two-month week grid.

Operator decision (2026-11-17): the week grid is back in scope, DISPLAY-ONLY, built from the
calendar entries the server already sends (no new backend fields). This module only arranges those
entries for the page: which month each belongs to, and where each date sits in a Monday-to-Sunday
grid. It decides nothing about the entries themselves: no dates are calculated, no entry is added,
dropped or marked (the "May not be required" flag is passed through as the server set it). It is
web-layer plumbing like the date formats in deps.py (frontend.md §10.2).

The one value that depends on today is which entry is "due next": the first entry on or after
today. If every entry is in the past, nothing is marked and the grid starts at the first entry's
month (frontend.md §11).
"""

import calendar
from datetime import date

MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]


def _day(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def _month_label(year: int, month: int) -> str:
    return f"{MONTH_NAMES[month - 1]} {year}"


def calendar_layout(entries, today: date | None = None) -> dict:
    """Arrange published entries for page 7.

    Returns:
      year:     the year when every entry is in the same one, else None ("All entries for {year}")
      months:   [{label, entries}] in date order, for the grouped list
      due_next: the ISO date of the next due entry, or None
      grid:     two months from the next due date's month: [{label, weeks}], where weeks is a list
                of seven-day rows (Monday first) of {day, iso, in_month, is_due_next, entries}
    """
    today = today or date.today()
    ordered = sorted(entries or [], key=lambda e: _day(e["due_date"]))
    if not ordered:
        return {"year": None, "months": [], "due_next": None, "grid": []}

    months, by_day = [], {}
    for entry in ordered:
        d = _day(entry["due_date"])
        label = _month_label(d.year, d.month)
        if not months or months[-1]["label"] != label:
            months.append({"label": label, "entries": []})
        months[-1]["entries"].append(entry)
        by_day.setdefault(d, []).append(entry)

    years = {_day(e["due_date"]).year for e in ordered}
    upcoming = [_day(e["due_date"]) for e in ordered if _day(e["due_date"]) >= today]
    due_next = upcoming[0] if upcoming else None

    start = due_next or _day(ordered[0]["due_date"])
    grid, year, month = [], start.year, start.month
    weeks_of = calendar.Calendar(firstweekday=0).monthdatescalendar  # Monday first
    for _ in range(2):
        weeks = [[{"day": d.day, "iso": d.isoformat(), "in_month": d.month == month,
                   "is_due_next": d == due_next and d.month == month,
                   "entries": by_day.get(d, []) if d.month == month else []}
                  for d in week]
                 for week in weeks_of(year, month)]
        grid.append({"label": _month_label(year, month), "weeks": weeks})
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)

    return {"year": years.pop() if len(years) == 1 else None, "months": months,
            "due_next": due_next.isoformat() if due_next else None, "grid": grid}
