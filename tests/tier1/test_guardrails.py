"""The step schemas and guardrails (CR-003, sad.md §2 agent cards). No model.

The valid outputs are the agent cards' own worked examples (invented SRC-SAMPLE / SRC-ANNEX /
FACT-S data). Each test changes one thing and expects the guardrail to refuse it. The date tests
also use the real mock paragraphs, because the "no date-shaped value" rule must let the source's
own wording through.
"""

import copy
import json

import pytest

from backend.domain import guardrails, sources

# --- Card 1's worked example -----------------------------------------------------------------

SAMPLE_PARAGRAPHS = {
    "SRC-SAMPLE-P1": (
        "Each fund that falls within this circular is to send the liquidity return L-4 to the "
        "Sample Supervisory Authority by the fifteenth calendar day after the close of every "
        "quarter. If that day is not a business day, the return is due on the following business "
        "day."),
    "SRC-SAMPLE-P2": ("The Sample Supervisory Authority may publish aggregated figures drawn "
                      "from the returns it receives."),
}
ROW = {
    "obligation_name": "Liquidity return L-4",
    "frequency": "quarterly",
    "anchor": "quarter_end",
    "offset": {"unit": "calendar_days", "amount": 15},
    "recipient_code": "SSA",
    "recipient_name": "Sample Supervisory Authority",
    "responsible_role": "not stated in source",
    "applicability_rule": "The fund falls within the circular.",
    "business_day_rule": "roll_forward",
    "source_paragraph_id": "SRC-SAMPLE-P1",
    "quote": "by the fifteenth calendar day after the close of every quarter",
}


def _extract(rows, paragraphs=SAMPLE_PARAGRAPHS, codes=("SSA",)):
    return guardrails.check_extraction({"rows": rows}, document_id="SRC-SAMPLE",
                                       paragraphs=paragraphs, recipient_codes=list(codes))


def _row(**changes):
    row = copy.deepcopy(ROW)
    row.update(changes)
    return row


def test_extractor_worked_example_passes():
    result = _extract([ROW])
    assert result.ok, result.error
    assert result.parsed.rows[0].offset.amount == 15


def test_extractor_accepts_json_text_and_an_empty_list():
    assert guardrails.check_extraction(json.dumps({"rows": [ROW]}), document_id="SRC-SAMPLE",
                                       paragraphs=SAMPLE_PARAGRAPHS,
                                       recipient_codes=["SSA"]).ok
    assert _extract([]).ok  # card 1 step 5: a document with no duty gives an empty list


@pytest.mark.parametrize("change", [
    {"frequency": "weekly"},                                   # not in the vocabulary
    {"anchor": "event_date"},
    {"business_day_rule": "next_business_day"},
    {"offset": {"unit": "weeks", "amount": 2}},
    {"offset": {"unit": "calendar_days", "amount": 0}},
    {"offset": {"unit": "fixed_day_month", "day": 31, "month": 4, "year_shift": 1}},  # no 31 April
    {"offset": {"unit": "fixed_day_month", "day": 31, "month": 10, "year_shift": 2}},
    {"obligation_name": ""},
    {"due_date": "later"},                                     # a field the card does not list
])
def test_extractor_refuses_shape_and_vocabulary_errors(change):
    result = _extract([_row(**change)])
    assert not result.ok and "schema" in result.error


def test_extractor_refuses_a_missing_field():
    row = _row()
    del row["quote"]
    assert not _extract([row]).ok


def test_extractor_refuses_a_paragraph_of_another_document():
    result = _extract([_row(source_paragraph_id="SRC-ANNEX-P1")])
    assert not result.ok and "SRC-ANNEX-P1" in result.error


def test_extractor_refuses_an_unknown_recipient_code():
    result = _extract([_row(recipient_code="XYZ")])
    assert not result.ok and "XYZ" in result.error


def test_extractor_does_not_run_the_quote_check():
    """A misquoted row passes the guardrail; W-04 blocks it later, visibly, at G1."""
    assert _extract([_row(quote="by the twentieth day after every quarter")]).ok


# --- "No date-shaped value" -------------------------------------------------------------------

@pytest.mark.parametrize("written", [
    "2027-01-10", "10/01/2027", "11 January 2027", "11 January", "January 11, 2027", "Oct 31",
])
def test_a_date_the_agent_wrote_is_refused(written):
    result = _extract([_row(applicability_rule=f"Due {written}.")])
    assert not result.ok and written in result.error


def test_ordinary_words_are_not_read_as_months():
    assert _extract([_row(applicability_rule="Rule 3 may apply to the fund.")]).ok


def test_dates_copied_from_the_source_are_allowed():
    """The real mock wording: a fixed day-month deadline in the quote, a law's date in the rule."""
    by_doc = {}
    for p in sources.load_paragraphs():
        by_doc.setdefault(p["document_id"], {})[p["paragraph_id"]] = p["text"]
    vat = _row(source_paragraph_id="SRC-VATLAW-P1", recipient_code="AED",
               offset={"unit": "fixed_day_month", "day": 31, "month": 10, "year_shift": 1},
               quote="by 31 October of the year following the financial year concerned")
    assert _extract([vat], paragraphs=by_doc["SRC-VATLAW"], codes=["AED"]).ok
    cssf = _row(source_paragraph_id="SRC-CSSF15627-P2", recipient_code="CSSF",
                applicability_rule="The fund is subject to Part II of the Law of 17 December 2010.",
                quote="no later than 10 calendar days after the end of each month")
    assert _extract([cssf], paragraphs=by_doc["SRC-CSSF15627"], codes=["CSSF"]).ok


# --- Card 2's worked example -----------------------------------------------------------------

ALL_PARAGRAPHS = {
    **SAMPLE_PARAGRAPHS,
    "SRC-ANNEX-P1": ("Return L-4 is completed for each calendar month and sent for every month "
                     "of the year."),
    "SRC-ANNEX-P2": "Return L-7, on large exposures, is sent once a year.",
}
CROSS = {
    "flag_type": "cross_source",
    "other_paragraph_id": "SRC-ANNEX-P1",
    "other_quote": "completed for each calendar month and sent for every month of the year",
    "explanation": ("SRC-ANNEX-P1 describes return L-4 as sent every month; the row's source, "
                    "SRC-SAMPLE-P1, sets it once a quarter."),
}
INTERNAL = {
    "flag_type": "internal",
    "field": "offset",
    "row_value": "20 calendar days",
    "quote_says": "fifteenth calendar day",
    "explanation": "The row says 20 days; its quote says the fifteenth day.",
}


def _verify(flags):
    return guardrails.check_verification({"flags": flags}, row_quote=ROW["quote"],
                                         paragraphs=ALL_PARAGRAPHS)


def test_verifier_worked_example_and_no_flags_pass():
    assert _verify([CROSS]).ok
    assert _verify([INTERNAL]).ok
    assert _verify([]).ok


@pytest.mark.parametrize("flag", [
    {**INTERNAL, "field": "recipient_code"},            # not one of the three checked fields
    {**INTERNAL, "quote_says": None},                   # internal flag missing its evidence
    {**CROSS, "other_quote": None},
    {**CROSS, "field": "offset"},                       # mixes the two kinds
    {**CROSS, "flag_type": "conflict"},
])
def test_verifier_refuses_shape_errors(flag):
    assert not _verify([flag]).ok


def test_verifier_refuses_an_unknown_paragraph():
    result = _verify([{**CROSS, "other_paragraph_id": "SRC-ANNEX-P9"}])
    assert not result.ok and "SRC-ANNEX-P9" in result.error


def test_verifier_refuses_evidence_that_is_not_word_for_word():
    assert not _verify([{**CROSS, "other_quote": "completed for every calendar month"}]).ok
    assert not _verify([{**INTERNAL, "quote_says": "fifteenth business day"}]).ok


# --- Card 3's worked example -----------------------------------------------------------------

FACTS_TEXT = ("FACT-S1 Legal form: limited partnership\nFACT-S2 Domicile: Sampleland\n"
              "FACT-S3 Number of investors at the last count: 240")
FACT_IDS = {"FACT-S1", "FACT-S2", "FACT-S3"}
VERDICT = {
    "verdict": "applies",
    "cited_fact_ids": ["FACT-S3"],
    "reasoning": ("This summary is required from funds with more than 100 investors. The fund "
                  "had 240 investors at the last count, so the requirement applies."),
    "missing_information": "",
}


def _judge(**changes):
    return guardrails.check_verdict({**VERDICT, **changes}, input_ids=FACT_IDS,
                                    given_text=FACTS_TEXT)


def test_judge_worked_example_passes():
    assert _judge().ok


def test_judge_unsure_needs_missing_information():
    assert not _judge(verdict="unsure").ok
    assert _judge(verdict="unsure", missing_information="The number of investors.").ok
    assert not _judge(missing_information="Something.").ok  # only when unsure


@pytest.mark.parametrize("change", [
    {"verdict": "maybe"},
    {"cited_fact_ids": []},
    {"reasoning": ""},
])
def test_judge_refuses_shape_errors(change):
    assert not _judge(**change).ok


def test_judge_refuses_an_id_not_in_its_input():
    result = _judge(cited_fact_ids=["FACT-S3", "FACT-S9"])
    assert not result.ok and "FACT-S9" in result.error


def test_judge_refuses_a_date():
    result = _judge(reasoning="The fund had 240 investors on 31 December 2026, so it applies.")
    assert not result.ok and "31 December 2026" in result.error


def test_parsed_output_becomes_json_for_the_trace():
    assert json.loads(guardrails.to_json(_judge()))["cited_fact_ids"] == ["FACT-S3"]
    assert guardrails.to_json(_judge(verdict="maybe")) is None
