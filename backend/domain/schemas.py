"""The output shapes of the three agent steps (sad.md §2, agent cards and "Shared output vocabulary").

Each model step returns one of these, and nothing is stored until the output fits its shape and
passes its guardrail (backend/domain/guardrails.py, CR-003). Plain code, no model.

`extra="forbid"` everywhere: a field the card does not list is refused, so an agent cannot slip in
something extra (for example a computed date in a field of its own).
"""

import calendar
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- The shared vocabulary (sad.md §2) -------------------------------------------------------

Frequency = Literal["monthly", "quarterly", "annually", "on_occurrence"]
Anchor = Literal["month_end", "quarter_end", "financial_year_end", "event_awareness",
                 "event_occurrence"]
BusinessDayRule = Literal["roll_forward", "roll_backward", "no_roll", "not_confirmed"]
FlagType = Literal["internal", "cross_source"]
VerdictValue = Literal["applies", "does_not_apply", "unsure"]

# The three fields the verifier's internal check compares with the quote (card 2, step 1).
CHECKED_FIELDS = ("frequency", "anchor", "offset")

NOT_STATED = "not stated in source"

Text = Field(min_length=1)  # a required piece of text that may not be empty


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Offset: a period rule, or a fixed day and month (never a calendar date) -----------------

class PeriodOffset(_Strict):
    """{unit, amount}, e.g. 10 calendar days or 6 months after the anchor."""

    unit: Literal["calendar_days", "months"]
    amount: int = Field(ge=1)


class FixedDayMonthOffset(_Strict):
    """A fixed deadline such as "31 October of the following year": day 31, month 10, shift 1."""

    unit: Literal["fixed_day_month"]
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year_shift: Literal[0, 1]

    @model_validator(mode="after")
    def _real_day(self):
        # 2028 is a leap year, so 29 February is allowed; 31 April never is.
        if self.day > calendar.monthrange(2028, self.month)[1]:
            raise ValueError(f"day {self.day} does not exist in month {self.month}")
        return self


Offset = PeriodOffset | FixedDayMonthOffset


# --- Card 1: extractor ------------------------------------------------------------------------

class Row(_Strict):
    obligation_name: str = Text
    frequency: Frequency
    anchor: Anchor
    offset: Offset = Field(discriminator="unit")
    recipient_code: str = Text           # checked against the configured list by the guardrail
    recipient_name: str = Text
    responsible_role: str = Text         # the party as written, or exactly "not stated in source"
    applicability_rule: str = Text
    business_day_rule: BusinessDayRule
    source_paragraph_id: str = Text      # checked against this document by the guardrail
    quote: str = Text                    # checked by the quote check (W-04) AFTER, not here


class ExtractionResult(_Strict):
    rows: list[Row]


# --- Card 2: verifier -------------------------------------------------------------------------

class Flag(_Strict):
    flag_type: FlagType
    explanation: str = Text
    # internal only
    field: Literal["frequency", "anchor", "offset"] | None = None
    row_value: str | None = None
    quote_says: str | None = None
    # cross_source only
    other_paragraph_id: str | None = None
    other_quote: str | None = None

    @model_validator(mode="after")
    def _fields_match_the_type(self):
        internal = (self.field, self.row_value, self.quote_says)
        cross = (self.other_paragraph_id, self.other_quote)
        if self.flag_type == "internal":
            if not all(internal) or any(cross):
                raise ValueError("an internal flag needs field, row_value and quote_says, "
                                 "and no other_paragraph_id or other_quote")
        elif not all(cross) or any(internal):
            raise ValueError("a cross_source flag needs other_paragraph_id and other_quote, "
                             "and no field, row_value or quote_says")
        return self


class VerificationResult(_Strict):
    flags: list[Flag]


# --- Card 3: judge ----------------------------------------------------------------------------

class Verdict(_Strict):
    verdict: VerdictValue
    cited_fact_ids: list[str] = Field(min_length=1)
    reasoning: str = Text
    missing_information: str = ""

    @model_validator(mode="after")
    def _missing_information_exactly_when_unsure(self):
        if (self.verdict == "unsure") != bool(self.missing_information.strip()):
            raise ValueError("missing_information is required when the verdict is unsure, "
                             "and must be empty otherwise")
        return self
