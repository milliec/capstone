"""STUB — placeholder data for the app shell only. Replaced in B3 by the real stand-in fixtures
(extractor.yaml, verifier.yaml, judge.yaml) and stored rows.

Rules this file follows:
- Generic placeholders, clearly fake. Not copied from project-context/1.define/mock-data/.
- No answer-key IDs (no OBL-, C-1, I-1 or AMD- identifiers), so it cannot leak the key (CR-016).
- Never read by a prompt; there is no model call anywhere in the shell.
"""

# Stage A runs one unit per source document (SAD §4 `units`: label = the document's title).
STAGE_A_UNITS = [
    (f"DOC-STUB-{n}", f"Stand-in source document {n}") for n in range(1, 6)
]

# The rows stage A "drafts". Row IDs are built per run in the view stubs: ROW-<run>-<n>.
ROWS = [
    {"n": 1, "obligation_name": "Stand-in rule 1: annual report", "frequency": "annual",
     "anchor": "financial year end", "offset": "+4 months", "recipient_code": "STUB-REG",
     "responsible_role": "not stated in source", "business_day_rule": "not_confirmed",
     "source_paragraph_id": "SRC-STUB-P1", "quote": "Placeholder quote one.", "origin": "model"},
    {"n": 2, "obligation_name": "Stand-in rule 2: quarterly return", "frequency": "quarterly",
     "anchor": "quarter end", "offset": "+20 days", "recipient_code": "STUB-REG",
     "responsible_role": "central administration", "business_day_rule": "roll_forward",
     "source_paragraph_id": "SRC-STUB-P2", "quote": "Placeholder quote two.", "origin": "model"},
    {"n": 3, "obligation_name": "Stand-in rule 3: monthly report", "frequency": "monthly",
     "anchor": "month end", "offset": "+10 days", "recipient_code": "STUB-REG",
     "responsible_role": "central administration", "business_day_rule": "no_roll",
     "source_paragraph_id": "SRC-STUB-P3", "quote": "Placeholder quote three.", "origin": "model"},
]

# Added only when the "Add the demo rule" switch is on (CR-029). B7 replaces this with
# config/demo/planted-row.yaml.
DEMO_ROW = {
    "n": 4, "obligation_name": "Stand-in demo rule (placeholder)", "frequency": "annual",
    "anchor": "financial year end", "offset": "+1 month", "recipient_code": "STUB-REG",
    "responsible_role": "not stated in source", "business_day_rule": "not_confirmed",
    "source_paragraph_id": "SRC-STUB-P4", "quote": "Placeholder demo quote.", "origin": "demo",
}

# One verdict per model row (stage B). Verdict IDs: VER-<run>-<n> (placeholder scheme).
VERDICTS = [
    {"n": 1, "verdict": "applies", "reasoning": "Placeholder reasoning.",
     "cited_fact_ids": "FACT-STUB-1"},
    {"n": 2, "verdict": "unsure", "reasoning": "Placeholder reasoning.",
     "cited_fact_ids": "FACT-STUB-2", "missing_information": "Placeholder missing fact."},
    {"n": 3, "verdict": "does_not_apply", "reasoning": "Placeholder reasoning.",
     "cited_fact_ids": "FACT-STUB-3"},
]

# Calendar entries (stage C is code only; the date engine is B4).
ENTRIES = [
    {"row_n": 1, "period": "FY2026", "due_date": "2027-04-30", "moved": False,
     "precautionary": False, "open_question_id": None},
    # Moved off a weekend: due Sunday 18 Apr 2027, so the following working day (Monday 19 Apr).
    {"row_n": 2, "period": "2027-03", "due_date": "2027-04-19", "moved": True,
     "moved_from": "2027-04-18", "precautionary": True, "open_question_id": None},
]
