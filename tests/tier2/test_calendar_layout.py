"""Page 7's display-only layout (backend/web/calendar_view.py): month grouping and the two-month
week grid, from the entries the server already sends. "Today" is passed in, so these never drift."""

from datetime import date

from backend.web.calendar_view import calendar_dots, calendar_layout, calendar_month, calendar_year

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


def test_the_flags_pass_through_unchanged():
    layout = calendar_layout(ENTRIES, today=date(2027, 1, 1))
    flagged = [e for m in layout["months"] for e in m["entries"] if e["precautionary"]]
    assert [e["obligation_name"] for e in flagged] == ["Quarterly return"]


def test_due_next_is_the_first_entry_on_or_after_today_or_none():
    assert calendar_layout(ENTRIES, today=date(2027, 4, 25))["due_next"] == "2027-04-30"
    assert calendar_layout(ENTRIES, today=date(2027, 4, 20))["due_next"] == "2027-04-20"  # due today counts
    assert calendar_layout(ENTRIES, today=date(2028, 1, 1))["due_next"] is None
    assert calendar_month(ENTRIES, today=date(2028, 1, 1))["label"] == "April 2027"  # then: first month


def test_mixed_years_have_no_single_year_and_group_across_the_year_end():
    entries = [{"due_date": "2027-12-31", "obligation_name": "A", "precautionary": False},
               {"due_date": "2028-01-15", "obligation_name": "B", "precautionary": False}]
    layout = calendar_layout(entries, today=date(2027, 12, 1))
    assert [m["label"] for m in layout["months"]] == ["December 2027", "January 2028"]
    assert layout["year"] is None


def test_no_entries_gives_an_empty_layout():
    assert calendar_layout([], today=date(2027, 1, 1)) == {"year": None, "months": [], "due_next": None}


# --- B12 (operator, 2026-11-17): Month view, Year view and dot chart -------------------------


def test_month_view_defaults_to_the_next_due_month_and_pages():
    m = calendar_month(ENTRIES, today=date(2027, 4, 25))
    assert m["label"] == "April 2027" and m["count"] == 2
    assert (m["prev"]["ym"], m["next"]["ym"]) == ("2027-03", "2027-05")
    june = calendar_month(ENTRIES, "2027-06", today=date(2027, 4, 25))
    assert june["label"] == "June 2027" and june["count"] == 1
    assert calendar_month(ENTRIES, "not-a-month", today=date(2027, 4, 25))["label"] == "April 2027"
    assert calendar_month(ENTRIES, "2027-12", today=date(2027, 4, 25))["next"]["label"] == "January 2028"


def test_year_view_has_one_row_per_obligation_and_a_column_per_month():
    y = calendar_year(ENTRIES, today=date(2027, 4, 25))
    assert y["year"] == 2027 and len(y["months"]) == 12 and y["now_month"] == 4
    assert [r["name"] for r in y["rows"]] == ["Quarterly return", "Annual report", "Monthly report"]
    quarterly = y["rows"][0]["cells"]
    assert quarterly[3] == [{"iso": "2027-04-20", "day": 20, "weekday": "Tue",
                             "precautionary": True, "is_due_next": False}]
    assert all(c == [] for i, c in enumerate(quarterly) if i != 3)


def test_dot_chart_counts_only_the_entries_and_their_flag():
    dots = calendar_dots(ENTRIES, today=date(2027, 1, 1))
    assert dots["year"] == 2027 and dots["total"] == 3 and dots["may_not_be_required"] == 1
    assert dots["months"][3]["dots"] == [True, False]  # 20 Apr (hollow) before 30 Apr
    assert dots["months"][5]["dots"] == [False] and dots["tallest"] == 2
