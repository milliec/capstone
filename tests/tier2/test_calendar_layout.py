"""Page 7's display-only layout (backend/web/calendar_view.py): month grouping and the two-month
week grid, from the entries the server already sends. "Today" is passed in, so these never drift."""

from datetime import date

from backend.web.calendar_view import calendar_layout

ENTRIES = [
    {"due_date": "2027-04-30", "obligation_name": "Annual report", "precautionary": False},
    {"due_date": "2027-04-20", "obligation_name": "Quarterly return", "precautionary": True},
    {"due_date": "2027-06-10", "obligation_name": "Monthly report", "precautionary": False},
]


def test_months_group_entries_in_date_order():
    layout = calendar_layout(ENTRIES, today=date(2027, 1, 1))
    assert [m["label"] for m in layout["months"]] == ["April 2027", "June 2027"]
    assert [e["obligation_name"] for e in layout["months"][0]["entries"]] == ["Quarterly return", "Annual report"]
    assert layout["year"] == 2027


def test_grid_is_two_months_from_the_next_due_date_monday_first():
    layout = calendar_layout(ENTRIES, today=date(2027, 4, 25))
    assert layout["due_next"] == "2027-04-30"
    assert [m["label"] for m in layout["grid"]] == ["April 2027", "May 2027"]
    april = layout["grid"][0]["weeks"]
    assert all(len(week) == 7 for week in april)
    assert date.fromisoformat(april[0][0]["iso"]).weekday() == 0  # Monday first
    cells = {c["iso"]: c for week in april for c in week}
    assert cells["2027-04-30"]["is_due_next"] and cells["2027-04-30"]["entries"][0]["obligation_name"] == "Annual report"
    assert cells["2027-04-20"]["entries"] and not cells["2027-04-20"]["is_due_next"]  # past, still shown
    assert sum(c["is_due_next"] for c in cells.values()) == 1


def test_days_outside_the_month_carry_no_entries():
    layout = calendar_layout(ENTRIES, today=date(2027, 4, 1))
    may = layout["grid"][1]["weeks"]
    outside = [c for week in may for c in week if not c["in_month"]]
    assert outside and all(c["entries"] == [] for c in outside)


def test_the_flags_pass_through_unchanged():
    layout = calendar_layout(ENTRIES, today=date(2027, 1, 1))
    flagged = [e for m in layout["months"] for e in m["entries"] if e["precautionary"]]
    assert [e["obligation_name"] for e in flagged] == ["Quarterly return"]


def test_all_entries_in_the_past_mark_nothing_and_start_at_the_first_month():
    layout = calendar_layout(ENTRIES, today=date(2028, 1, 1))
    assert layout["due_next"] is None
    assert layout["grid"][0]["label"] == "April 2027"
    assert not any(c["is_due_next"] for m in layout["grid"] for w in m["weeks"] for c in w)


def test_year_end_rolls_into_january_and_mixed_years_have_no_single_year():
    entries = [{"due_date": "2027-12-31", "obligation_name": "A", "precautionary": False},
               {"due_date": "2028-01-15", "obligation_name": "B", "precautionary": False}]
    layout = calendar_layout(entries, today=date(2027, 12, 1))
    assert [m["label"] for m in layout["grid"]] == ["December 2027", "January 2028"]
    assert layout["year"] is None


def test_no_entries_gives_an_empty_layout():
    assert calendar_layout([], today=date(2027, 1, 1)) == {"year": None, "months": [], "due_next": None, "grid": []}
