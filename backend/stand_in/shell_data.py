"""STUB — placeholder calendar dates for stage C, until B4 (the date engine) works them out.

Since B3 step 5 the rows, flags and verdicts are the real stand-in answers (extractor.yaml,
verifier.yaml, judge.yaml). Only stage C still uses this file (operator, 2026-11-18): the dates
below attach to the review's rules 1, 2 and 4, whatever those rules are, so until B4 the calendar
shows real rule names with placeholder dates that do not follow from the rules.

Why rules 1, 2 and 4: rule 4 is the stand-in "AI can't tell" rule, so when the specialist adds it
at G2 its entry carries the "May not be required" mark, and rule 2's entry carries the "moved off
a weekend" mark. The calendar keeps showing both marks until B4.

Rules this file follows:
- Generic placeholders, not copied from project-context/1.define/mock-data/.
- No answer-key IDs (no OBL-, C-1, I-1 or AMD- identifiers), so it cannot leak the key (CR-016).
- Never read by a prompt.
"""

# Calendar entries for rules 1, 2 and 4 (stage C is code only; the date engine is B4).
ENTRIES = [
    {"row_n": 1, "period": "FY2026", "due_date": "2027-04-30", "moved": False,
     "precautionary": False, "open_question_id": None},
    # Moved off a weekend: due Sunday 18 Apr 2027, so the following working day (Monday 19 Apr).
    {"row_n": 2, "period": "2027-03", "due_date": "2027-04-19", "moved": True,
     "moved_from": "2027-04-18", "precautionary": True, "open_question_id": None},
    {"row_n": 4, "period": "2027-01", "due_date": "2027-02-10", "moved": False,
     "precautionary": False, "open_question_id": None},
]
