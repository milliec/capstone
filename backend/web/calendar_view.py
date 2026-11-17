"""Display-only layout for page 7 · Calendar: month grouping, the Month and Year views, the dot chart.

Operator decisions (2026-11-17): the calendar is built DISPLAY-ONLY from the entries the server
already sends (no new backend fields), and laid out like docs/prototype/gp-calendar.html (B12, H-040).
This module only arranges those entries for the page: which month each belongs to, where each date
sits in a Monday-to-Sunday month, and how many there are. It decides nothing about the entries: no
dates are calculated, no entry is added, dropped or marked (the "May not be required" flag is passed
through as the server set it). It is web-layer plumbing like the date formats in deps.py
(frontend.md §10.2, W-5).

The one value that depends on today is which entry is "due next": the first entry on or after
today. If every entry is in the past, nothing is marked and the Month view opens on the first
entry's month (frontend.md §11).
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
    """Arrange published entries for page 7 (the two-month grid this once built was replaced by the
    Month view, operator 2026-11-17).

    Returns:
      year:     the year when every entry is in the same one, else None ("All entries for {year}")
      months:   [{label, entries}] in date order, for the grouped list
      due_next: the ISO date of the next due entry, or None
    """
    today = today or date.today()
    ordered = sorted(entries or [], key=lambda e: _day(e["due_date"]))
    if not ordered:
        return {"year": None, "months": [], "due_next": None}

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

    return {"year": years.pop() if len(years) == 1 else None, "months": months,
            "due_next": due_next.isoformat() if due_next else None}


# --- B12: Month view, Year view and the dot chart (operator, 2026-11-17; DL-49, H-040) ----------
# Same rule as above: these only arrange the entries the page already has. They count only what
# the viewer may already see (DL-49): the entries themselves and their "May not be required" flag.

SHORT_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _due_next(ordered, today):
    upcoming = [_day(e["due_date"]) for e in ordered if _day(e["due_date"]) >= today]
    return upcoming[0] if upcoming else None


def _parse_month(value):
    """'2027-04' → (2027, 4), or None if it is not a valid year-month (the page then uses its default)."""
    try:
        year, month = (int(part) for part in str(value).split("-"))
        return (year, month) if 1 <= month <= 12 and 1900 < year < 2200 else None
    except (TypeError, ValueError):
        return None


def calendar_month(entries, ym=None, today: date | None = None) -> dict:
    """One month for the Month view: the asked-for month ('YYYY-MM'), else the next due date's
    month, else the first entry's month. Weeks are Monday first."""
    today = today or date.today()
    ordered = sorted(entries or [], key=lambda e: _day(e["due_date"]))
    due_next = _due_next(ordered, today)
    default = due_next or (_day(ordered[0]["due_date"]) if ordered else today)
    year, month = _parse_month(ym) or (default.year, default.month)
    by_day = {}
    for entry in ordered:
        by_day.setdefault(_day(entry["due_date"]), []).append(entry)
    weeks = [[{"day": d.day, "iso": d.isoformat(), "weekday": WEEKDAYS[d.weekday()],
               "in_month": d.month == month, "is_due_next": d == due_next and d.month == month,
               "entries": by_day.get(d, []) if d.month == month else []}
              for d in week]
             for week in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)]
    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)
    return {"label": _month_label(year, month), "ym": f"{year:04d}-{month:02d}", "weeks": weeks,
            "count": sum(len(c["entries"]) for w in weeks for c in w),
            "prev": {"ym": f"{prev_y:04d}-{prev_m:02d}", "label": _month_label(prev_y, prev_m)},
            "next": {"ym": f"{next_y:04d}-{next_m:02d}", "label": _month_label(next_y, next_m)}}


def calendar_year(entries, today: date | None = None) -> dict:
    """The Year view: one row per obligation (in the order of its first date that year), a column
    per month, the dates in the cells. The year is the next due date's, else the first entry's."""
    today = today or date.today()
    ordered = sorted(entries or [], key=lambda e: _day(e["due_date"]))
    if not ordered:
        return {"year": None, "months": SHORT_MONTHS, "now_month": None, "rows": []}
    due_next = _due_next(ordered, today)
    year = (due_next or _day(ordered[0]["due_date"])).year
    rows, index = [], {}
    for entry in ordered:
        d = _day(entry["due_date"])
        if d.year != year:
            continue
        name = entry["obligation_name"]
        if name not in index:
            index[name] = len(rows)
            rows.append({"name": name, "who_files": entry.get("who_files_label"),
                         "cells": [[] for _ in range(12)]})
        rows[index[name]]["cells"][d.month - 1].append(
            {"iso": d.isoformat(), "day": d.day, "weekday": WEEKDAYS[d.weekday()],
             "precautionary": bool(entry.get("precautionary")), "is_due_next": d == due_next})
    return {"year": year, "months": SHORT_MONTHS, "rows": rows,
            "now_month": due_next.month if due_next and due_next.year == year else None}


def calendar_dots(entries, today: date | None = None) -> dict:
    """The dot chart: for the Year view's year, one dot per entry in each month, hollow where the
    entry is marked "May not be required". Also the two counts printed beside it."""
    year = calendar_year(entries, today)["year"]
    months = [{"label": SHORT_MONTHS[m][0], "dots": []} for m in range(12)]
    for entry in sorted(entries or [], key=lambda e: _day(e["due_date"])):  # dots in date order
        d = _day(entry["due_date"])
        if d.year == year:
            months[d.month - 1]["dots"].append(bool(entry.get("precautionary")))
    total = sum(len(m["dots"]) for m in months)
    hollow = sum(sum(m["dots"]) for m in months)
    return {"year": year, "months": months, "total": total, "may_not_be_required": hollow,
            "tallest": max([len(m["dots"]) for m in months] + [1])}
