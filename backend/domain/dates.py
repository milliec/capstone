"""The date engine (W-13, B4): approved rules → calendar entries. Plain code; no model ever
computes a date (SD MN-005, the Build card's Never row).

For each approved rule whose final answer at G2 is "applies":
  1. ANCHORS. month_end: every month end; quarter_end: 31 Mar, 30 Jun, 30 Sep, 31 Dec;
     financial_year_end: the fund's year end each year; event_awareness / event_occurrence: the
     date each logged event became known / happened. Anchors run from the year before the horizon
     to its end, so a deadline that falls early in the horizon is found.
  2. OFFSET. calendar_days: anchor + n days (D-1). months from a period end: the last day of the
     target month (D-2: 30 June + 2 months = 31 August). months from an event: the same day of the
     month, moved back to the month's last day if it does not exist (D-3: 31 January + 1 month =
     28 February). fixed_day_month: that day and month, in the anchor's year or the next.
  3. ROLL (D-4, D-7: after the offset). roll_forward: the next business day; roll_backward: the
     previous one; no_roll: unchanged. A business day is Monday to Friday and not a holiday in the
     config. There is NO default: a rule without one of the three stops generation (fail closed,
     DL-19; D-6 is retired), so the engine can never guess a roll (T-W13-2).
  4. KEEP the entry if its calendar due date (after the roll) is inside the fund's horizon.
  5. MARKS. moved: the roll changed the date. precautionary: the specialist added the rule at G2
     although AI could not tell. open_question_id: the rule's paragraph and recipient match an open
     convention in the config (CR-027; OQ-7 → SRC-UCILAW-P2, AED).
  6. ID. ENT-<fund>-<paragraph_id>-<recipient>-<period>, where period is the anchor's month
     (YYYY-MM) for a month or quarter end, FY<year> for a financial year end, or the event ID for
     an event. The ID does not depend on the due date, so the same occurrence has the same ID in
     every run (T-ID-2, EC-008). Two rules that give the same ID stop generation, naming both
     (DL-35).
The result is sorted by due date, then entry ID: the same inputs always give the same list.
"""

import calendar
from dataclasses import dataclass
from datetime import date, timedelta

PERIOD_END_ANCHORS = ("month_end", "quarter_end", "financial_year_end")
EVENT_ANCHORS = {"event_awareness": "aware", "event_occurrence": "occurred"}
ROLLS = ("roll_forward", "roll_backward", "no_roll")


class CalendarError(Exception):
    """Generation stopped: nothing is stored and the run fails with "calendar generation" (CR-011)."""


@dataclass(frozen=True)
class Rule:
    """One approved rule, as the engine needs it. `business_day_rule` is the specialist's G1 choice."""

    row_id: str
    source_paragraph_id: str
    recipient_code: str
    anchor: str
    offset: dict
    business_day_rule: str | None
    precautionary: bool = False


@dataclass(frozen=True)
class Entry:
    entry_id: str
    row_id: str
    period: str
    unadjusted_date: str     # anchor + offset, before the roll (ISO)
    due_date: str            # the calendar due date (ISO)
    business_day_rule: str
    moved: bool
    precautionary: bool
    open_question_id: str | None


@dataclass(frozen=True)
class Calendar:
    """What the engine needs besides the rules, all from config and the fund profile."""

    fund_id: str
    year_end_month: int
    year_end_day: int
    horizon_start: date
    horizon_end: date
    holidays: frozenset
    events: tuple            # ({event_id, occurred, aware} with ISO dates), ...
    open_conventions: tuple  # ({question_id, source_paragraph_id, recipient_code}), ...


def _month_end(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _add_months(day: date, months: int, *, to_month_end: bool) -> date:
    total = day.month - 1 + months
    year, month = day.year + total // 12, total % 12 + 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, last if to_month_end else min(day.day, last))


def _anchors(rule: Rule, cal: Calendar) -> list[tuple[date, str]]:
    """(anchor date, period) pairs for one rule."""
    years = range(cal.horizon_start.year - 1, cal.horizon_end.year + 1)
    if rule.anchor == "month_end":
        return [(d, f"{d:%Y-%m}") for y in years for m in range(1, 13)
                for d in [_month_end(y, m)]]
    if rule.anchor == "quarter_end":
        return [(d, f"{d:%Y-%m}") for y in years for m in (3, 6, 9, 12)
                for d in [_month_end(y, m)]]
    if rule.anchor == "financial_year_end":
        return [(date(y, cal.year_end_month, cal.year_end_day), f"FY{y}") for y in years]
    if rule.anchor in EVENT_ANCHORS:
        key = EVENT_ANCHORS[rule.anchor]
        return [(date.fromisoformat(e[key]), e["event_id"]) for e in cal.events]
    raise CalendarError(f"{rule.row_id}: unknown anchor {rule.anchor!r}")


def _apply_offset(anchor: date, rule: Rule) -> date:
    o = rule.offset
    if o["unit"] == "calendar_days":                                         # D-1
        return anchor + timedelta(days=o["amount"])
    if o["unit"] == "months":                                                # D-2, D-3
        return _add_months(anchor, o["amount"], to_month_end=rule.anchor in PERIOD_END_ANCHORS)
    if o["unit"] == "fixed_day_month":
        return date(anchor.year + o["year_shift"], o["month"], o["day"])
    raise CalendarError(f"{rule.row_id}: unknown offset unit {o['unit']!r}")


def is_business_day(day: date, holidays: frozenset) -> bool:
    return day.weekday() < 5 and day not in holidays


def roll(day: date, rule_name: str | None, holidays: frozenset, row_id: str = "") -> date:
    """D-4: move a date off weekends and holidays as the rule says. No default (T-W13-2)."""
    if rule_name not in ROLLS:
        raise CalendarError(f"{row_id}: no business-day rule was chosen at G1 "
                            f"({rule_name!r}); the calendar cannot be generated (DL-19)")
    if rule_name == "no_roll":
        return day
    step = timedelta(days=1 if rule_name == "roll_forward" else -1)
    while not is_business_day(day, holidays):
        day += step
    return day


def generate(rules: list[Rule], cal: Calendar) -> list[Entry]:
    """Every entry for the approved rules, or CalendarError (all or nothing, CR-011)."""
    open_marks = {(c["source_paragraph_id"], c["recipient_code"]): c["question_id"]
                  for c in cal.open_conventions}
    entries: dict[str, Entry] = {}
    for rule in rules:
        if rule.business_day_rule not in ROLLS:          # fail closed before any date (T-W13-2)
            roll(cal.horizon_start, rule.business_day_rule, cal.holidays, rule.row_id)
        for anchor, period in _anchors(rule, cal):
            unadjusted = _apply_offset(anchor, rule)
            due = roll(unadjusted, rule.business_day_rule, cal.holidays, rule.row_id)
            if not cal.horizon_start <= due <= cal.horizon_end:
                continue
            entry_id = (f"ENT-{cal.fund_id}-{rule.source_paragraph_id}-{rule.recipient_code}-"
                        f"{period}")
            if entry_id in entries:
                raise CalendarError(f"Two approved rules give the same calendar entry {entry_id}: "
                                    f"{entries[entry_id].row_id} and {rule.row_id} (DL-35)")
            entries[entry_id] = Entry(
                entry_id=entry_id, row_id=rule.row_id, period=period,
                unadjusted_date=unadjusted.isoformat(), due_date=due.isoformat(),
                business_day_rule=rule.business_day_rule, moved=due != unadjusted,
                precautionary=rule.precautionary,
                open_question_id=open_marks.get((rule.source_paragraph_id, rule.recipient_code)))
    return sorted(entries.values(), key=lambda e: (e.due_date, e.entry_id))


def calendar_from_config(fund_id: str) -> Calendar:
    """The engine's settings from config/regulation/lu-part2.yaml (holidays, open conventions),
    config/fund/<fund>.yaml (year end, horizon) and the fund profile's event log (dates)."""
    from backend.domain.fund_facts import load_event_dates
    from backend.domain.sources import load_regulation_config
    from backend.services.fund import load_fund

    regulation, fund = load_regulation_config(), load_fund(fund_id)
    as_date = lambda v: v if isinstance(v, date) else date.fromisoformat(str(v))
    return Calendar(
        fund_id=fund_id,
        year_end_month=fund["financial_year_end"]["month"],
        year_end_day=fund["financial_year_end"]["day"],
        horizon_start=as_date(fund["calendar_horizon"]["start"]),
        horizon_end=as_date(fund["calendar_horizon"]["end"]),
        holidays=frozenset(as_date(h) for h in regulation["holidays"]),
        events=tuple(load_event_dates(fund_id)),
        open_conventions=tuple(regulation["open_conventions"]))
