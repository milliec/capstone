"""The guardrails of the three agent steps (CR-003, sad.md §2 agent cards). Plain code, no model.

Each guardrail takes the agent's raw output and the context the agent was given, and returns a
GuardrailResult: the parsed output, or the reason it was refused. A refusal fails the unit and the
run ends FAILED with "invalid output"; the model is never asked again (D5,
guardrail_max_retries: 0). The invalid output is kept in the trace only (CR-003, B3 step 6).

These functions are plain on purpose, so they run in tests with no CrewAI object. B3 step 7 wraps
them in the (TaskOutput) -> (bool, value) form CrewAI's Task.guardrail expects.

What each card's guardrail checks:
  extractor  shape and vocabulary; every source_paragraph_id is in THIS document; recipient_code
             is in the configured list; no date-shaped value. NOT the quote: the quote check runs
             afterwards (W-04), so a misquoted row reaches G1 blocked and visible.
  verifier   shape; field is one of the three checked fields; other_paragraph_id exists;
             quote_says is word for word in the row's quote and other_quote in its paragraph (QN-1).
  judge      shape; verdict in the set; at least one cited ID, each one from the input;
             missing_information exactly when unsure; no date-shaped value.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from backend.domain.quote_check import check_quote, normalise
from backend.domain.schemas import ExtractionResult, VerificationResult, Verdict


@dataclass(frozen=True)
class GuardrailResult:
    """`parsed` is the validated output when `ok`; `error` says why it was refused otherwise."""

    ok: bool
    parsed: BaseModel | None = None
    error: str | None = None


def _refuse(error: str) -> GuardrailResult:
    return GuardrailResult(ok=False, error=error)


def _parse(model: type[BaseModel], raw: Any) -> BaseModel:
    """Raw output may arrive as a JSON string or as an already-decoded dict."""
    if isinstance(raw, (str, bytes)):
        return model.model_validate_json(raw)
    return model.model_validate(raw)


# --- "No date-shaped value" -------------------------------------------------------------------

_MONTH = (r"(?:January|February|March|April|May|June|July|August|September|October|November|"
          r"December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.?")
_DAY = r"\d{1,2}(?:st|nd|rd|th)?"
_DATE_SHAPES = re.compile(
    r"\b\d{4}-\d{1,2}-\d{1,2}\b"                     # 2027-01-10
    r"|\b\d{1,2}[/.]\d{1,2}[/.]\d{2,4}\b"            # 10/01/2027, 10.01.27
    rf"|\b{_DAY}\s+{_MONTH}(?:\s+\d{{4}})?\b"        # 10 January, 10 January 2027
    rf"|\b{_MONTH}\s+{_DAY}(?:,?\s+\d{{4}})?\b")     # January 10, January 10, 2027
# Case-sensitive on purpose: month names are capitalised in English, and ignoring case would read
# ordinary words as months ("rule 3 may apply" would look like "3 May").


def _strings(value: Any):
    """Every piece of text inside an output, however deeply nested."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def find_date_shaped(output: BaseModel, given_text: str) -> str | None:
    """The first date-shaped value the agent WROTE, or None.

    A date-shaped value that is copied word for word from the material the agent was given is
    not counted: it is part of the source, not a date the agent worked out. This is what lets the
    extractor quote "by 31 October of the year following ..." and name the "Law of 17 December
    2010", while a due date the agent computed ("11 January 2027") is refused.
    """
    given = normalise(given_text)
    for text in _strings(output.model_dump()):
        for match in _DATE_SHAPES.finditer(text):
            if normalise(match.group(0)) not in given:
                return match.group(0)
    return None


# --- Card 1: extractor ------------------------------------------------------------------------

def check_extraction(raw: Any, *, document_id: str, paragraphs: dict[str, str],
                     recipient_codes: list[str]) -> GuardrailResult:
    """`paragraphs` is THIS document's paragraphs only ({paragraph_id: text})."""
    try:
        result = _parse(ExtractionResult, raw)
    except (ValidationError, ValueError) as e:
        return _refuse(f"Output does not fit the extractor's schema: {e}")
    for n, row in enumerate(result.rows, start=1):
        if row.source_paragraph_id not in paragraphs:
            return _refuse(f"Row {n} cites {row.source_paragraph_id}, which is not a paragraph "
                           f"of {document_id}.")
        if row.recipient_code not in recipient_codes:
            return _refuse(f"Row {n} has recipient code {row.recipient_code!r}, which is not "
                           "in the configured list.")
    date = find_date_shaped(result, "\n".join(paragraphs.values()))
    if date:
        return _refuse(f"Output contains a date-shaped value not in the source: {date!r}.")
    return GuardrailResult(ok=True, parsed=result)


# --- Card 2: verifier -------------------------------------------------------------------------

def check_verification(raw: Any, *, row_quote: str,
                       paragraphs: dict[str, str]) -> GuardrailResult:
    """`paragraphs` is every loaded paragraph (the verifier's <sources>)."""
    try:
        result = _parse(VerificationResult, raw)
    except (ValidationError, ValueError) as e:
        return _refuse(f"Output does not fit the verifier's schema: {e}")
    for n, flag in enumerate(result.flags, start=1):
        if flag.flag_type == "internal":
            # QN-1 reused: the evidence must be real words of the row's own quote.
            if not check_quote(flag.quote_says, "ROW", {"ROW": row_quote}).passed:
                return _refuse(f"Flag {n}: quote_says is not word for word in the row's quote.")
        else:
            if flag.other_paragraph_id not in paragraphs:
                return _refuse(f"Flag {n} cites {flag.other_paragraph_id}, which is not a "
                               "loaded paragraph.")
            if not check_quote(flag.other_quote, flag.other_paragraph_id, paragraphs).passed:
                return _refuse(f"Flag {n}: other_quote is not word for word in "
                               f"{flag.other_paragraph_id}.")
    return GuardrailResult(ok=True, parsed=result)


# --- Card 3: judge ----------------------------------------------------------------------------

def check_verdict(raw: Any, *, input_ids: set[str], given_text: str) -> GuardrailResult:
    """`input_ids` are the fact and event IDs the judge was given; `given_text` is its whole input
    (row, facts and events), used by the date check."""
    try:
        result = _parse(Verdict, raw)
    except (ValidationError, ValueError) as e:
        return _refuse(f"Output does not fit the judge's schema: {e}")
    unknown = [i for i in result.cited_fact_ids if i not in input_ids]
    if unknown:
        return _refuse(f"The verdict cites IDs that were not in its input: {unknown}.")
    date = find_date_shaped(result, given_text)
    if date:
        return _refuse(f"Output contains a date-shaped value not in the input: {date!r}.")
    return GuardrailResult(ok=True, parsed=result)


def to_json(result: GuardrailResult) -> str | None:
    """The parsed output as JSON, for the trace's parsed_output column (B3 step 6)."""
    return json.dumps(result.parsed.model_dump(), ensure_ascii=False) if result.parsed else None
