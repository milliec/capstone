"""No-model checks on the answer key (expected-obligation-library.md).

The answer key is the evaluation's ground truth, so it is checked before the first evaluation run
(H-024, H-025, H-029). These tests read the key's markdown tables and recompute every date from
first principles. They use no model, no network and only the Python standard library.

Run from the repository root:
    python3 -m unittest discover -s tests -v
"""

import calendar
import datetime as dt
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEY = ROOT / "project-context/1.define/mock-data/expected-obligation-library.md"
PROFILE = ROOT / "project-context/1.define/mock-data/mock-fund-profile.md"

# The mock Luxembourg public holidays for 2027, copied from answer key section 5.
# If the key's holiday list changes, change this list too.
HOLIDAYS_2027 = {
    dt.date(2027, m, d)
    for m, d in [(1, 1), (3, 29), (5, 1), (5, 6), (5, 9), (5, 17), (6, 23),
                 (8, 15), (11, 1), (12, 25), (12, 26)]
}

# How each obligation's offset works (answer key section 1 and conventions D-1 to D-3).
#   ("days", n)        anchor + n calendar days (D-1)
#   ("months_eom", n)  period-end anchor + n months, landing on the month's last day (D-2)
#   ("months_same", n) event anchor + n months, same day of month or the month's last day (D-3)
OFFSETS = {
    "OBL-01": ("days", 10),
    "OBL-02": ("days", 20),
    "OBL-03": ("months_eom", 6),
    "OBL-04": ("months_eom", 2),
    "OBL-05": ("months_same", 1),
}

# Business-day rule text in the key -> the internal rule name (SAD `business_day_rule`).
RULES = {"roll forward": "roll_forward", "roll backward": "roll_backward", "no roll": "no_roll"}

ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
WEEKDAY_NOTE = re.compile(r"(\d{4}-\d{2}-\d{2})\**\s*\((Mon|Tue|Wed|Thu|Fri|Sat|Sun)\)")


# ---------- small helpers ----------

def section(text, start_heading, end_heading):
    """Return the text between two '## ' headings."""
    start = text.index(start_heading)
    end = text.index(end_heading, start)
    return text[start:end]


def table_rows(block, first_cell_prefix="| `OBL-"):
    """Split each markdown table row that starts with an OBL code into its cells."""
    rows = []
    for line in block.splitlines():
        if line.startswith(first_cell_prefix):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def code_of(cell):
    return cell.strip("`* ")


def first_date(cell):
    return dt.date.fromisoformat(ISO_DATE.search(cell).group(0))


def last_day(year, month):
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def add_months(day, months, end_of_month):
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    if end_of_month:
        return last_day(year, month)
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def calculated_due(code, anchor):
    kind, n = OFFSETS[code]
    if kind == "days":
        return anchor + dt.timedelta(days=n)
    return add_months(anchor, n, end_of_month=(kind == "months_eom"))


def is_business_day(day):
    return day.weekday() < 5 and day not in HOLIDAYS_2027


def apply_rule(day, rule):
    step = {"roll_forward": 1, "roll_backward": -1}.get(rule)
    if step is None:  # no_roll keeps the date
        return day
    while not is_business_day(day):
        day += dt.timedelta(days=step)
    return day


# ---------- load the key once ----------

KEY_TEXT = KEY.read_text(encoding="utf-8")
CALENDAR = table_rows(section(KEY_TEXT, "## 4.", "## 5."))
SECTION_5 = section(KEY_TEXT, "## 5.", "## 6.")


def calendar_entries():
    """Each section 4 row as (code, anchor, calculated, rule, calendar due date, raw cells)."""
    entries = []
    for cells in CALENDAR:
        code, anchor, calc, rule_text, due = cells[:5]
        entries.append((code_of(code), first_date(anchor), first_date(calc),
                        # "No roll (tax)" -> "no roll": drop any bracketed note before looking up
                        RULES[rule_text.split("(")[0].strip("* ").lower()], first_date(due), cells))
    return entries


class CalendarTests(unittest.TestCase):
    """Answer key section 4: the expected 2027 calendar."""

    def test_22_entries(self):
        self.assertEqual(len(calendar_entries()), 22)

    def test_no_expected_entry_falls_on_a_saturday_or_sunday(self):
        weekend = [(code, due.isoformat(), due.strftime("%a"))
                   for code, _, _, _, due, _ in calendar_entries() if due.weekday() >= 5]
        self.assertEqual(weekend, [], "expected calendar entries on a weekend")

    def test_calculated_dates_match_anchor_plus_offset(self):
        for code, anchor, calc, _, _, _ in calendar_entries():
            with self.subTest(code=code, anchor=anchor.isoformat()):
                self.assertEqual(calc, calculated_due(code, anchor))

    def test_calendar_dates_match_the_business_day_rule(self):
        for code, anchor, calc, rule, due, _ in calendar_entries():
            with self.subTest(code=code, anchor=anchor.isoformat()):
                self.assertEqual(due, apply_rule(calc, rule))

    def test_six_moved_off_a_weekend_four_forward_two_back(self):
        moved = [(code, rule) for code, _, calc, rule, due, _ in calendar_entries() if due != calc]
        self.assertEqual(len(moved), 6)
        self.assertEqual(sum(rule == "roll_forward" for _, rule in moved), 4)
        self.assertEqual(sum(rule == "roll_backward" for _, rule in moved), 2)

    def test_both_28_feb_filings_move_to_fri_26_feb(self):
        sunday = dt.date(2027, 2, 28)
        moved = sorted(code for code, _, calc, _, due, _ in calendar_entries()
                       if calc == sunday and due == dt.date(2027, 2, 26))
        self.assertEqual(moved, ["OBL-04", "OBL-05"])

    def test_obl_05_counts_from_the_awareness_date(self):
        [entry] = [e for e in calendar_entries() if e[0] == "OBL-05"]
        self.assertEqual(entry[1], dt.date(2027, 1, 31))  # EVT-01 awareness, not 2027-01-20

    def test_no_entry_is_marked_rule_unconfirmed(self):
        for code, anchor, _, _, _, cells in calendar_entries():
            with self.subTest(code=code, anchor=anchor.isoformat()):
                row = " ".join(cells).lower()
                self.assertNotIn("unconfirmed", row)
                self.assertNotIn("not confirmed", row)

    def test_weekday_notes_in_the_table_are_right(self):
        for cells in CALENDAR:
            for date_text, weekday in WEEKDAY_NOTE.findall(" | ".join(cells)):
                with self.subTest(date=date_text):
                    self.assertEqual(dt.date.fromisoformat(date_text).strftime("%a"), weekday)

    def test_totals_line_says_22_and_6(self):
        block = section(KEY_TEXT, "## 4.", "## 5.")
        self.assertIn("22 calendar entries, none on a Saturday or Sunday", block)
        self.assertIn("6 are moved off a weekend", block)

    def test_moved_mark_is_specialist_only(self):
        block = section(KEY_TEXT, "## 4.", "## 5.")
        self.assertIn("specialist-only", block)
        self.assertIn("**no** moved mark is expected", block)


class OpenQuestionMarkTests(unittest.TestCase):
    """EC-007 and CR-027: the OQ-7 mark is on the 4 OBL-02 entries only, and is specialist-only."""

    def marks(self):
        # The 6th column of the section 4 table: "Open-question mark (specialist only)".
        return [(code_of(cells[0]), cells[5].strip("* ")) for cells in CALENDAR]

    def test_every_entry_has_a_mark_cell(self):
        for cells in CALENDAR:
            with self.subTest(row=" | ".join(cells[:2])):
                self.assertEqual(len(cells), 6)

    def test_all_four_obl_02_entries_carry_oq_7(self):
        obl_02 = [mark for code, mark in self.marks() if code == "OBL-02"]
        self.assertEqual(obl_02, ["OQ-7"] * 4)

    def test_no_other_entry_carries_the_mark(self):
        others = [(code, mark) for code, mark in self.marks() if code != "OBL-02" and mark]
        self.assertEqual(others, [])

    def test_key_says_the_mark_is_never_on_the_gp_view(self):
        block = section(KEY_TEXT, "## 4.", "## 5.")
        self.assertIn("Open-question mark *(specialist only)*", block)
        self.assertIn("it is **never** shown on the General Partner view", block)


PROTOTYPE = ROOT / "docs/prototype"
OQ_7_CHIP = "Depends on open question OQ-7"
OBL_02_NAME = "Subscription tax return and payment"


def entry_rows(page):
    """The calendar entry rows (<tr id="r-N">) of a mock-up page, as HTML strings."""
    html = (PROTOTYPE / page).read_text(encoding="utf-8")
    return re.findall(r'<tr id="r-\d+".*?</tr>', html, re.S)


class OpenQuestionMarkOnViewsTests(unittest.TestCase):
    """The OQ-7 mark on the two calendar views.

    No app is built yet, so these check the mock-ups in docs/prototype (the layout reference). When
    the real pages exist, SAD T-W13-1 checks them; keep the same two expectations.
    """

    def test_specialist_calendar_shows_the_mark_on_obl_02_rows_only(self):
        rows = entry_rows("calendar.html")
        self.assertTrue(any(OBL_02_NAME in row for row in rows), "no OBL-02 row on the page")
        for number, row in enumerate(rows):
            with self.subTest(row=number):
                self.assertEqual(OQ_7_CHIP in row, OBL_02_NAME in row)

    def test_g3_publish_page_marks_the_four_obl_02_entries_only(self):
        """H-031: at G3 every OBL-02 tile carries the mark, and no other tile does (SAD CR-027)."""
        html = (PROTOTYPE / "publish.html").read_text(encoding="utf-8")
        tiles = re.findall(r'<span class="day[^"]*" title="([^"]*)">', html)
        self.assertEqual(len(tiles), 22, "the year grid should show all 22 entries")
        marked = sorted(title.split(" · ")[0] for title in tiles if "OQ-7" in title)
        self.assertEqual(marked, ["Tue 20 Apr 2027", "Tue 20 Jul 2027", "Wed 20 Jan 2027", "Wed 20 Oct 2027"])
        # The same chip as on G1 and the specialist calendar, once, in the OBL-02 row label.
        self.assertEqual(html.count(f'<span class="chip plain">{OQ_7_CHIP}</span>'), 1)

    def test_g3_mark_does_not_block_publishing(self):
        html = (PROTOTYPE / "publish.html").read_text(encoding="utf-8")
        form = re.search(r'<form class="decision".*?</form>', html, re.S).group(0)
        publish_button = re.search(r'<button[^>]*>Publish calendar</button>', form)
        self.assertIsNotNone(publish_button, "no Publish calendar button")
        self.assertNotIn("disabled", publish_button.group(0))
        self.assertNotIn("OQ-7", form)  # the mark is information, not a condition on the form

    def test_gp_calendar_never_shows_the_mark(self):
        html = (PROTOTYPE / "gp-calendar.html").read_text(encoding="utf-8")
        # The GP page does list OBL-02 entries, so a missing mark is a real result, not an empty page.
        self.assertTrue(any(OBL_02_NAME in row for row in entry_rows("gp-calendar.html")))
        self.assertNotIn("OQ-7", html)
        self.assertNotIn("open question", html.lower())


class ConventionTests(unittest.TestCase):
    """Answer key section 5: conventions and the specialist's expected G1 settings."""

    def business_day_rules(self):
        block = SECTION_5.split("**Business-day rule per obligation**")[1].split("**Who files")[0]
        return {code_of(cells[0]): cells[2] for cells in table_rows(block)}

    def test_obl_04_and_obl_05_use_preceding_working_day(self):
        rules = self.business_day_rules()
        for code in ("OBL-04", "OBL-05"):
            with self.subTest(code=code):
                self.assertIn("Roll backward", rules[code])
                self.assertIn("preceding working day", rules[code])

    def test_no_obligation_rule_is_not_confirmed(self):
        for code, rule in self.business_day_rules().items():
            with self.subTest(code=code):
                self.assertNotIn("not confirmed", rule.lower())

    def test_d4_lists_roll_backward_and_d6_is_retired(self):
        d4 = next(line for line in SECTION_5.splitlines() if line.startswith("| `D-4`"))
        d6 = next(line for line in SECTION_5.splitlines() if line.startswith("| `D-6`"))
        self.assertIn("roll backward", d4.lower())
        self.assertIn("Retired", d6)


class WhoFilesTests(unittest.TestCase):
    """The specialist's expected "who files" settings at G1 use the exact profile labels."""

    EXPECTED = {
        "OBL-01": "Fund administrator",
        "OBL-02": "Fund administrator",
        "OBL-03": "Fund administrator",
        "OBL-04": "Local reporting agent (Spain)",
        "OBL-05": "AIFM",
        "OBL-06": "Tax advisor",
    }

    def who_files(self):
        block = SECTION_5.split("**Who files per obligation**")[1]
        return {code_of(cells[0]): cells[3] for cells in table_rows(block)}

    def filing_parties(self):
        parties = set()
        for line in PROFILE.read_text(encoding="utf-8").splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1] == "Yes":
                parties.add(cells[0])
        return parties

    def test_expected_values_use_exact_labels(self):
        self.assertEqual(self.who_files(), self.EXPECTED)

    def test_every_expected_value_is_a_filing_party_in_the_profile(self):
        parties = self.filing_parties()
        for code, value in self.who_files().items():
            with self.subTest(code=code):
                self.assertIn(value, parties)


class PlantedRowTests(unittest.TestCase):
    """Q2 / H-025: the planted row is counted and must be rejected."""

    def test_planted_row_line_and_counts(self):
        block = section(KEY_TEXT, "## 1.", "## 2.")
        self.assertIn("7 drafted, 6 genuine; the planted row must be rejected.", block)
        self.assertIn("7 drafted → 6 approved → 6 checked for\napplicability → 5 apply → 22 dates",
                      block)


if __name__ == "__main__":
    unittest.main()
