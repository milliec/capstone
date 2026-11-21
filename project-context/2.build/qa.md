# QA: B8 Stage A grader slice (first QA pass)

Owner: `@qa.eng`. Branch `qa-eng/b8-stage-a-grader-slice`, 2026-11-21. Runtime `AAMAD_TARGET_RUNTIME=crewai`,
`AGENTS_MODE=stand_in` throughout: no model call, no real key, no paid call.

**Scope.** Only what exists in the MVP build today. This pass covers the one thing `@qa.eng` built:
the first slice of B8, the Stage A grader (`backend/evaluation/`), authorised by the operator on
2026-11-21 (handoff H-066: it starts before the B3 spike because it makes no model call). It grades
a **finished Stage A run read from the database**. The run starter (evaluation-run type, scripted
gates, EC-R7 refusal), the trace export (D4), the void rule (EC-R8) and the two copy cases that need
a model (`I-1`, the injection case) are the rest of B8 and are **not built, so not tested**.

Inputs read: `sad.md` (Build card, §9 evaluation criteria and run rules EC-R1 to EC-R11, DL-34,
DL-41, DL-45, D4), `backend.md`, `scaffold-plan.md`, `setup.md`, `US-013`, the answer key
`expected-obligation-library.md` and the mock sources. `ux.md`, `ux-review.md`, `frontend.md` and
`integration.md` were not used: **no page, template or stylesheet changed**.

## Unit tests (no model, no network)

| File | Tests | What it checks | Maps to |
|---|---|---|---|
| `tests/tier2/test_party_lookup.py` | 13 | **T-MAP-1** (a) the five mappings, (b) five texts that give "no match", (c) every target is a filing party in the profile or "not stated in source", (d) nothing under `backend/` outside `backend/evaluation/` names the lookup or imports the package (seen failing on a planted offender); the normal form does only what EC-R11 says | EC-R11, DL-41, US-013 c11 |
| `tests/tier2/test_evaluation_golden.py` | 6 | The golden set read from the key: 6 rows and quotes in the app's vocabulary, C-1, C-2, clean OBL-01, I-1, the 7 uncited paragraphs **derived** (13 loaded minus 6 cited); a changed key stops the load with an error | EC-001, EC-005, EC-009; operator decision 2026-11-21 (no second copy) |
| `tests/tier2/test_evaluation_stage_a.py` | 37 | The graders on a "perfect" output built from the key and then spoiled one way at a time (missing row, extra row, row on a forbidden paragraph, a twin row, each wrong field, truncated quote, role text that does not map, a wrong-party role, a business-day rule set, a computed date, a missed C-1 or C-2, a flag on the wrong paragraph or with a made-up quote, a false alarm on OBL-01, an internal flag) and on 10 code-only copy cases. **Free text is never matched by code** (H-068): a different applicability sentence is not an EC-001 miss and is listed for the operator in EC-002 (key against output, 12 items: 6 names and 6 sentences); a wrong offset still misses | EC-001, EC-002, EC-003, EC-005, EC-006, EC-009, EC-021; US-013 c1, c2, c4, c6, c11 |

**The graders were checked by breaking them.** Six deliberate breaks of `grade.py` (skip the quote
comparison, ignore extra rows, switch the date scan off, switch the clean-row check off, drop the
flag-paragraph check, grade the demo row) were each caught by at least one test. The first version of the
flag-paragraph test did **not** catch its break (the quote check caught it by accident); a case
that isolates the rule was added and the break is now caught.

**Code-only copy cases** (on copies of OBL-01's quote; the sources are never edited, US-013 c4):
`altered_quote` (the DL-45 case, scored under EC-005) plus nine ugly variants: extra spaces and breaks
(must pass), padding (must pass), different case, a non-breaking space, an added semicolon, a wrong
paragraph, an unknown paragraph, an empty quote (all must fail), and a **truncated** quote (must
**pass** the quote check, because it is still a verbatim piece; only EC-001 catches it against the
key). All 10 behave as QN-1 says. One expectation of mine was wrong at first (a trailing full stop
passes, because the paragraph itself ends with one); the case now uses a semicolon.

## Integration (database ↔ grader ↔ report)

| Check | Result |
|---|---|
| A real stand-in Stage A run, read from the database, graded and stamped `STAND-IN RUN: does not count towards the cycle` | Pass |
| The coverage list equals the app's own `decisions.unused_paragraphs` at G1 (7 paragraphs) | Pass |
| Grading writes nothing (row counts of 7 tables unchanged) | Pass |
| A run with the planted-row switch on: the demo row is not graded; the report is stamped (EC-R7 is recorded, **not enforced**) | Pass |
| A real-mode run counts only when labelled `evaluation` (EC-R6); `rehearsal` does not | Pass |
| Saved reports: JSON round-trips, report 2 never touches report 1, a taken number is skipped | Pass |
| The grader imports no agent function and no CrewAI | Pass |

## Smoke: the command line on a real stand-in run

`python -m backend.evaluation RUN-20261121-1` printed and saved the report; exit code 0 (a miss is a
result, DL-34). Stand-in result, **the same every time**: EC-001 PASS (every structured field matches on 6 of 6),
EC-002 for the operator (6 names and 6 applicability sentences, key against output), EC-003 PASS, EC-005 MISS (2 of 4 passed, `I-1` not tested), EC-006 MISS (1 cross-source flag
instead of 2), EC-009 PASS (7 listed), EC-021 NOT TESTED. These misses are about the stand-in answers, which
were written from the paragraphs and not from the key (CR-016). They show the graders work; they are
not an evaluation of the agents.

## Failure paths checked

Unknown run ID → "no run"; a run whose Stage A never stored output → "nothing to grade"; no database
file → "nothing to grade" and **no empty file is created**; a taken report number → the next is used;
a changed answer key → a loud error naming the word. Exit code 2 for "nothing to grade".

## Not tested (kept apart from passed)

- **Any real model output.** `AGENTS_MODE=real` is refused until step 7b PRs 2 to 6. Every result above is
  about stand-in answers or fabricated outputs.
- `I-1` (EC-005) and the injection case (EC-021): model calls. Shown as `NOT TESTED` in every report;
  EC-005 reads `INCOMPLETE`, never `PASS`, while `I-1` is open.
- EC-004, EC-007, EC-008 (stage B and C; EC-007 and EC-008 are already Tier 1 tests), EC-010 to EC-012 (whole-run time,
  review time, cost).
- The evaluation-run type, scripted gates, EC-R7 refusal, D4 trace export (T-D4-1), EC-R8 void rule.
- Accessibility, responsive behaviour, interface quality, visual regression: **no UI changed**, so not in
  scope. No visual snapshot was touched.
- Performance and load: out of scope (not scoped).

## Whole-repository test state

| Run | Result |
|---|---|
| `main` before this branch | 270 passed, 4 skipped, **1 failed** |
| This branch | 336 passed, **1 failed** (the same one). The 4 skips run here because `docs/prototype` exists on this machine |
| New tests | 62 (13 + 6 + 37 + 6 in `tests/tier2/`) |
| Lint | `ruff 0.17.3` clean |

The one failure is `tests/tier1/test_crewai_setup.py::test_loading_crewai_and_building_a_crew_opens_no_connection`:
`ModuleNotFoundError: No module named 'crewai'`. It fails the same way on a clean `main` checkout, so
it is **not caused by this change**. CrewAI is pinned in `pyproject.toml` and CI installs it; this
machine's `.venv` does not have it. Not fixed here (setup, not QA).

The evaluation tests sit in `tests/tier2/` because the SAD places T-MAP-1 there and lists the other
evaluation tests as "not yet tiered" (SOQ-29); Tier 2 runs in CI but does not block a merge. T-MAP-1
**must** pass before the first evaluation run (Build card): it does.

## Defects and findings

| ID | What | Severity | Owner |
|---|---|---|---|
| F-1 | **Resolved 2026-11-21 (H-068, operator: "judge it like the name").** EC-001 matched the applicability rule exactly, but it is a free sentence, so it could never pass (a stand-in run missed it on 6 of 6 rows while every other field matched). Now every structured field keeps its exact code check, and the sentence goes to the operator under EC-002 until a model judge is calibrated against the operator's marks. `sad.md` EC-001, EC-002 and EC-R5 wording changed at the operator's instruction (`@system.arch` to check); `US-013` c11 is H-069 | Was high for the evaluation's usefulness | Closed |
| F-2 | `crewai` missing from this machine's `.venv`: one Tier 1 test fails locally on `main` too | Low (environment) | Operator / `@project.mgr` |
| F-3 | `ruff` was in `requirements-dev.txt` but not installed in `.venv` (the hooks do not run it; CI does). Installed locally at the pinned 0.17.3 to lint before committing | Low (environment) | — |

## Future work (deferred tests, in order)

1. The run starter (B8 after the spike): evaluation-run type, scripted gates as `specialist-eval`
   (EC-R2), EC-R7 refusal with its test (T-DEMO-1 last line), `T-MODE-1` "an evaluation run refuses
   stand-in mode".
2. D4 trace export and T-D4-1; the void rule EC-R8 (never void on invalid output, wrong result, cost
   cap, calendar generation or restart).
3. The copy cases that need the agents: `I-1` (EC-005) and the injection case (EC-021), labelled
   `eval_case` in the trace (DL-45).
4. Graders for stage B (EC-004) and a runtime grader for EC-010 and EC-012; the three-run
   comparison (EC-R1, EC-R1a) over saved reports.
5. EC-R5, the match rules for EC-002 (the name **and** the applicability sentence), written by the operator before the first evaluation run. Later: a model judge for EC-002, with a judge model different from the model under test, **calibrated against the operator's marks** (agreement rate reported) before it replaces them.
6. `*verify-change` on the final branch, then the recommendation to `@security.eng` (SAD §9).

## Sources

`sad.md` (EC-001 to EC-021, EC-R1 to EC-R11, DL-34, DL-41, DL-45, D4, Build card); `backend.md`;
`US-013`; the answer key and the mock sources; `.cursor/agents/qa-eng.md`; `.cursor/skills/run-evals/SKILL.md`.

## Assumptions

- The operator's decisions of 2026-11-21 stand: grade a finished run; code-only cases; `backend/evaluation/`;
  the key is read at grade time; the 22 entries stay with Stage C; EC-R5 later. H-068 (same day): the applicability sentence is judged by the operator, not matched exactly.
- A drafted row is matched to a key row by its **source paragraph** (each key paragraph belongs to one key
  row). A second row on that paragraph is an extra row.
- The key's words ("Month-end", "+10 calendar days", …) are translated to the app's vocabulary by a small table in
  `golden.py`; an unknown word stops the load.
- `counts_for_cycle` is a stamp, not a gate: it refuses nothing.

## Open Questions

1. ~~F-1 / H-068~~ **Closed 2026-11-21:** the applicability sentence is judged by the operator with the name (EC-002). Still open on it: `US-013` c11 (H-069, `@product-mgr`).
2. **EC-R5:** the match rules for the name and for the applicability sentence are still to be written by the operator (EC-002 is shown "for the operator").
3. Should the evaluation tests be promoted to Tier 1 once the run starter exists (SOQ-29)?

## Audit

- 2026-11-21 · persona `qa-eng` · action `qa` (B8 Stage A grader slice; `test-unit`, `test-integration`,
  `log-defects`, `future-work`) · `AAMAD_TARGET_RUNTIME=crewai` · no model call. `*verify-change` and the
  `@security.eng` recommendation are **not** made yet: B8 is not finished.
- 2026-11-21 · persona `qa-eng` · action `update` (H-068, operator decision) · EC-001 no longer matches the applicability rule exactly; EC-002 lists it with the name for the operator; F-1 closed; counts updated (62 new tests). Tier placement unchanged (open question 3). `AAMAD_TARGET_RUNTIME=crewai` · no model call.
