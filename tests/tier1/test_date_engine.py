"""The date engine (W-13, block B4). No model.

EC-007 (Tier 1, the date test): a whole stand-in review, decided as the demo does, gives exactly the
answer key's 22 entries (KEY §4, read from the key file here: tests may read it, prompts and
run-time fixtures never do, CR-016). EC-008 and T-ID-2: identical on every generation. T-W13-1 and
T-W13-2: the open-question mark, and no default business-day rule. Plus the conventions' edge cases,
holidays, events, the ID collision and the "calendar generation" failure.
"""

import re
from dataclasses import replace
from datetime import date

import pytest

from backend.db.connection import connect, init_db
from backend.domain import dates
from backend.runtime import stages
from backend.services import calendar as calendar_service
from backend.services import decisions, runs
from backend.settings import ROOT
from tests import flow

KEY = ROOT / "project-context/1.define/mock-data/expected-obligation-library.md"
CAL = dates.calendar_from_config("FND-DEMO-01")


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _key_entries():
    """KEY §4 as [(paragraph_id, calculated date, calendar due date, open question)]."""
    text = KEY.read_text(encoding="utf-8")
    para_of = dict(re.findall(r"^\| `(OBL-\d+)` \|.*\| `(SRC-[A-Z0-9]+-P\d+)` \|$", text, re.M))
    section = text.split("## 4.", 1)[1].split("## 5.", 1)[0]
    rows = []
    for line in section.splitlines():
        m = re.match(r"^\| `(OBL-\d+)` \|[^|]*\| ([^|]*)\|[^|]*\| ([^|]*)\| ([^|]*)\|$", line)
        if m:
            calc, due = (re.search(r"\d{4}-\d{2}-\d{2}", c).group(0) for c in m.group(2, 3))
            rows.append((para_of[m.group(1)], calc, due, "OQ-7" if "OQ-7" in m.group(4) else None))
    return rows


def _stored_entries(conn, run_id):
    return [dict(r) for r in conn.execute(
        """SELECT e.*, r.source_paragraph_id FROM calendar_entries e
           JOIN calendar_versions c ON c.calendar_id = e.calendar_id
           JOIN rows r ON r.row_id = e.row_id WHERE c.run_id = ?""", (run_id,))]


# --- EC-007: the 22 entries ----------------------------------------------------------------

def test_ec_007_a_demo_review_gives_exactly_the_answer_keys_22_entries(conn, settings):
    expected = _key_entries()
    assert len(expected) == 22                       # the test reads the key, it cannot read nothing
    run_id = flow.to_g3(conn, settings, demo=True)
    got = [(e["source_paragraph_id"], e["unadjusted_date"], e["due_date"], e["open_question_id"])
           for e in _stored_entries(conn, run_id)]
    assert sorted(got) == sorted(expected)
    entries = _stored_entries(conn, run_id)
    assert all(date.fromisoformat(e["due_date"]).weekday() < 5 for e in entries)   # no weekend
    assert sum(e["moved"] for e in entries) == 6                                    # 4 fwd, 2 back
    assert sum(e["precautionary"] for e in entries) == 4                            # the 4 A01 dates


# --- EC-008, T-ID-2: identical every time ---------------------------------------------------

def _rule(n=1, **changes):
    base = dates.Rule(row_id=f"ROW-X-{n}", source_paragraph_id="SRC-CSSF15627-P2",
                      recipient_code="CSSF", anchor="month_end",
                      offset={"unit": "calendar_days", "amount": 10},
                      business_day_rule="roll_forward")
    return replace(base, **changes)


def test_ec_008_two_generations_from_the_same_inputs_are_identical(conn, settings):
    rules = [_rule(), _rule(2, source_paragraph_id="SRC-CNMV-P1", recipient_code="CNMV",
                            anchor="quarter_end", offset={"unit": "months", "amount": 2},
                            business_day_rule="roll_backward")]
    assert dates.generate(rules, CAL) == dates.generate(list(reversed(rules)), CAL)
    # And end to end: two reviews give the same entry IDs and dates (T-ID-2).
    first = flow.to_g3(conn, settings)
    second = flow.to_g3(conn, settings)
    pick = lambda run_id: sorted((e["entry_id"], e["due_date"]) for e in _stored_entries(conn, run_id))
    assert pick(first) == pick(second)
    assert "ENT-FND-DEMO-01-SRC-CSSF15627-P2-CSSF-2026-12" in dict(pick(first))


def test_id_2_the_entry_id_does_not_depend_on_the_due_date():
    forward = dates.generate([_rule()], CAL)
    backward = dates.generate([_rule(business_day_rule="roll_backward")], CAL)
    assert [e.entry_id for e in forward] == [e.entry_id for e in backward]
    assert forward[0].due_date != backward[0].due_date                  # Sun 10 Jan: Mon 11 / Fri 8


def test_two_rules_giving_the_same_entry_stop_generation_and_name_both():
    with pytest.raises(dates.CalendarError, match="ROW-X-1 and ROW-X-2"):
        dates.generate([_rule(1), _rule(2)], CAL)


# --- T-W13-1, T-W13-2: the open question, and no default rule -------------------------------

def test_w13_1_the_open_question_marks_every_subscription_tax_entry_and_nothing_else(
        conn, settings, specialist_client, gp_client):
    run_id = flow.to_g3(conn, settings)
    marked = [e for e in _stored_entries(conn, run_id) if e["open_question_id"]]
    assert len(marked) == 4 and {e["open_question_id"] for e in marked} == {"OQ-7"}
    assert {e["source_paragraph_id"] for e in marked} == {"SRC-UCILAW-P2"}
    tax = _rule(source_paragraph_id="SRC-UCILAW-P2", recipient_code="AED", anchor="quarter_end",
                offset={"unit": "calendar_days", "amount": 20})
    no_roll = [e.due_date for e in dates.generate([replace(tax, business_day_rule="no_roll")], CAL)]
    roll_fwd = [e.due_date for e in dates.generate([tax], CAL)]
    assert no_roll == roll_fwd                          # the open question changes no date here
    # G1 says so on that rule only; G3 shows the mark; publishing is not blocked; the GP never sees it.
    g1 = decisions.get_g1_view(conn, runs.get_run(conn, run_id))["rows"]
    assert [r["n"] for r in g1 if r["open_question"]] == [2] and g1[1]["open_question"] == "OQ-7"
    g3 = calendar_service.get_g3_view(conn, runs.get_run(conn, run_id))
    assert sum(1 for e in g3["entries"] if e["open_question_id"]) == 4
    flow.publish(conn, run_id)
    assert runs.get_run(conn, run_id)["status"] == "COMPLETED"
    for view in ("", "?view=list", "?view=month", "?view=year"):
        assert "OQ-7" not in gp_client.get("/calendar" + view).text, view


@pytest.mark.parametrize("missing", [None, "", "not_confirmed", "sometimes"])
def test_w13_2_there_is_no_default_business_day_rule(missing):
    with pytest.raises(dates.CalendarError, match="no business-day rule"):
        dates.generate([_rule(business_day_rule=missing)], CAL)


def test_a_generation_error_fails_the_run_and_stores_nothing(conn, settings, monkeypatch):
    def broken(rules, cal):
        raise dates.CalendarError("Two approved rules give the same calendar entry: test")

    monkeypatch.setattr(stages.dates, "generate", broken)
    run_id = flow.to_g3(conn, settings)
    run = runs.get_run(conn, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "C_RUNNING")
    unit = [u for u in runs.list_units(conn, run_id) if u["stage"] == "C"][0]
    assert unit["failure_reason"] == "calendar generation"
    assert conn.execute("SELECT COUNT(*) FROM calendar_versions").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE reason LIKE 'Two approved rules%'"
                        ).fetchone()[0] == 1                                # the detail is kept


# --- The conventions, holidays and events --------------------------------------------------

def _dates_of(rule):
    return [(e.unadjusted_date, e.due_date) for e in dates.generate([rule], CAL)]


def test_d2_period_end_plus_months_lands_on_the_month_end():
    rule = _rule(anchor="quarter_end", offset={"unit": "months", "amount": 2},
                 business_day_rule="no_roll")
    assert ("2027-08-31", "2027-08-31") in _dates_of(rule)                 # 30 Jun + 2 = 31 Aug
    annual = _rule(anchor="financial_year_end", offset={"unit": "months", "amount": 6})
    assert _dates_of(annual) == [("2027-06-30", "2027-06-30")]             # 31 Dec + 6 = 30 Jun


def test_d3_event_plus_months_keeps_the_day_or_the_month_end():
    aware = _rule(anchor="event_awareness", offset={"unit": "months", "amount": 1},
                  business_day_rule="roll_backward")
    assert _dates_of(aware) == [("2027-02-28", "2027-02-26")]              # 31 Jan + 1 → Fri 26
    occurred = replace(aware, anchor="event_occurrence")
    assert _dates_of(occurred) == [("2027-02-20", "2027-02-19")]           # 20 Jan + 1 → Fri 19
    assert dates.generate([aware], CAL)[0].period == "EVT-01"


def test_rolls_skip_holidays_as_well_as_weekends():
    holidays = CAL.holidays
    assert dates.roll(date(2027, 3, 29), "roll_forward", holidays) == date(2027, 3, 30)   # Easter Mon
    assert dates.roll(date(2027, 5, 17), "roll_backward", holidays) == date(2027, 5, 14)  # Whit Mon
    # 31 Oct 2027 is a Sunday; Mon 1 Nov is All Saints, so forward lands on Tue 2 Nov.
    assert dates.roll(date(2027, 10, 31), "roll_forward", holidays) == date(2027, 11, 2)
    assert dates.roll(date(2027, 10, 31), "no_roll", holidays) == date(2027, 10, 31)


def test_a_fixed_day_deadline_falls_in_the_following_year():
    vat = _rule(anchor="financial_year_end", business_day_rule="no_roll",
                offset={"unit": "fixed_day_month", "day": 31, "month": 10, "year_shift": 1})
    [entry] = dates.generate([vat], CAL)
    assert (entry.period, entry.due_date, entry.moved) == ("FY2026", "2027-10-31", False)


def test_only_due_dates_inside_the_horizon_are_kept():
    monthly = dates.generate([_rule()], CAL)
    assert len(monthly) == 12
    assert monthly[0].period == "2026-12" and monthly[-1].period == "2027-11"   # Dec 27 → 2028


def test_the_why_line_names_each_kind_of_rule_in_plain_words(conn, settings):
    why = {e["why"] for e in calendar_service.get_g3_view(
        conn, runs.get_run(conn, flow.to_g3(conn, settings)))["entries"]}
    assert why == {
        "Monthly rule: due 10 calendar days after month end.",
        "Quarterly rule: due 20 calendar days after quarter end.",
        "Annual rule: due 6 months after financial year end.",
        "Quarterly rule: due 2 months after quarter end.",
        "Event-triggered rule: due 1 month after becoming aware of the event.",
    }
