# QA: B8 grader slices (Stage A, then Stage B)

Owner: `@qa.eng`. Stage A: branch `qa-eng/b8-stage-a-grader-slice` (PR #142, merged). Stage B: branch `qa-eng/b8-stage-b-grader-slice`. Both 2026-11-21. Runtime `AAMAD_TARGET_RUNTIME=crewai`,
`AGENTS_MODE=stand_in` throughout: no model call, no real key, no paid call.

**Scope.** Only what exists in the MVP build today. This pass covers what `@qa.eng` built: two slices
of B8. **Slice 1, the Stage A grader** (`backend/evaluation/`), authorised by the operator on
2026-11-21 (handoff H-066: it starts before the B3 spike because it makes no model call). It grades
a **finished Stage A run read from the database**. The run starter (evaluation-run type, scripted
gates, EC-R7 refusal), the trace export (D4), the void rule (EC-R8) and the two copy cases that need
a model (`I-1`, the injection case) are the rest of B8 and are **not built, so not tested**.

**Slice 2, the Stage B grader** (operator, 2026-11-21, same approach): EC-004 (applicability verdicts
against KEY §2) and EC-010 and EC-012 (agent time and cost from the trace). It reads a finished Stage B
run (one that stored its verdicts) from the database; it starts no run and calls no model.

Inputs read: `sad.md` (Build card, §9 evaluation criteria and run rules EC-R1 to EC-R11, DL-34,
DL-41, DL-45, D4), `backend.md`, `scaffold-plan.md`, `setup.md`, `US-013`, the answer key
`expected-obligation-library.md` and the mock sources. `ux.md`, `ux-review.md`, `frontend.md` and
`integration.md` were not used: **no page, template or stylesheet changed**.

## Unit tests (no model, no network)

| File | Tests | What it checks | Maps to |
|---|---|---|---|
| `tests/tier2/test_party_lookup.py` | 13 | **T-MAP-1** (a) the five mappings, (b) five texts that give "no match", (c) every target is a filing party in the profile or "not stated in source", (d) nothing under `backend/` outside `backend/evaluation/` names the lookup or imports the package (seen failing on a planted offender); the normal form does only what EC-R11 says | EC-R11, DL-41, US-013 c11 |
| `tests/tier2/test_evaluation_golden.py` | 9 | The golden set read from the key: 6 rows and quotes in the app's vocabulary, C-1, C-2, clean OBL-01, I-1, the 7 uncited paragraphs **derived** (13 loaded minus 6 cited), and (slice 2) the 6 expected verdicts with their facts, every fact existing in the fund profile; a changed key stops the load with an error | EC-001, EC-004, EC-005, EC-009; operator decision 2026-11-21 (no second copy) |
| `tests/tier2/test_evaluation_stage_a.py` | 37 | The graders on a "perfect" output built from the key and then spoiled one way at a time (missing row, extra row, row on a forbidden paragraph, a twin row, each wrong field, truncated quote, role text that does not map, a wrong-party role, a business-day rule set, a computed date, a missed C-1 or C-2, a flag on the wrong paragraph or with a made-up quote, a false alarm on OBL-01, an internal flag) and on 10 code-only copy cases. **Free text is never matched by code** (H-068): a different applicability sentence is not an EC-001 miss and is listed for the operator in EC-002 (key against output, 12 items: 6 names and 6 sentences); a wrong offset still misses | EC-001, EC-002, EC-003, EC-005, EC-006, EC-009, EC-021; US-013 c1, c2, c4, c6, c11 |
| `tests/tier2/test_evaluation_stage_b.py` | 28 | The Stage B graders on fabricated verdicts and traces spoiled one way at a time: **unsure answered "applies" is named as the confident error**; every other wrong verdict; OBL-04 and OBL-05 missing a named fact; a made-up or missing fact ID; a different existing fact on the other rows is **not** a miss (the SAD names facts for two rows only); a row not extracted (miss); a row the specialist did not approve (**not tested**, not a miss); the boundaries **exactly 300 s and exactly US$2.00 are misses**; late and copy-case calls counted and named; a trace that does not add up to the run's cost count; zero calls is never a pass | EC-004, EC-010, EC-012; US-006 c2 to c5 |
| `tests/tier2/test_evaluation_stage_b_run.py` | 14 | A finished stand-in run read from the database (graded as soon as Stage B stores, before G2 is done); a row rejected at G1; "real" runs made with extra trace lines (the trace is append-only): inside both limits, over 5 minutes, over US$2, copy cases counted, a trace that disagrees with the run; stage B not started or not finished is not gradable; grading writes nothing; the report text; stage A and B reports numbered separately and never overwritten; the command line | EC-004, EC-010, EC-012; US-013 c1, c5, c6 |

**The graders were checked by breaking them.** Slice 2: nine deliberate breaks of `grade_b.py` (verdict not compared, named citations not required, unknown fact ID allowed, 5 minutes and US$2 not strict, cost consistency ignored, a not-approved row counted as a miss, the confident error unnamed, zero calls graded as a pass) and six of the loader `stage_b.py` (an unfinished stage graded, cost, time or copy cases not summed, a rejected row counted as approved, the consistency check made trivial) were each caught by at least one test; none survived. Slice 1: six deliberate breaks of `grade.py` (skip the quote
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
| Stage B: a finished stand-in run read from the database: 6 verdicts, 6 rows approved, 17 trace calls, stamped as stand-in | Pass |
| Stage B: EC-010 and EC-012 on a stand-in run are `NOT TESTED` / `INCOMPLETE` (it costs nothing and takes milliseconds), and on a run made to look real they pass, miss at the boundary, count late and copy-case calls and catch a trace that disagrees with the run | Pass |
| Stage B grading writes nothing (row counts of 7 tables unchanged) | Pass |

## Smoke: the command line on a real stand-in run

`python -m backend.evaluation RUN-20261121-1` printed and saved the report; exit code 0 (a miss is a
result, DL-34). Stand-in result, **the same every time**: EC-001 PASS (every structured field matches on 6 of 6),
EC-002 for the operator (6 names and 6 applicability sentences, key against output), EC-003 PASS, EC-005 MISS (2 of 4 passed, `I-1` not tested), EC-006 MISS (1 cross-source flag
instead of 2), EC-009 PASS (7 listed), EC-021 NOT TESTED. These misses are about the stand-in answers, which
were written from the paragraphs and not from the key (CR-016). They show the graders work; they are
not an evaluation of the agents.

**Stage B, a stand-in run at G3** (`--stage b`; the default `all` grades Stage A and also Stage B when the run
finished it, and skips Stage B with a note at G1): EC-004 PASS (6 of 6; the stand-in verdicts equal the key's),
EC-010 NOT TESTED (0.0 s over 17 calls: stand-in), EC-012 INCOMPLETE (US$0.0000 over 17 calls: stand-in; the
trace adds up to the run's cost count). A PASS on EC-010 or EC-012 here would be true and say nothing, so the report
never shows one for a stand-in run.

## Failure paths checked

Unknown run ID → "no run"; a run whose Stage A never stored output → "nothing to grade"; no database
file → "nothing to grade" and **no empty file is created**; a taken report number → the next is used;
a changed answer key → a loud error naming the word. Stage B: a run at G1 ("Stage B never started"), a run whose
stage B has a unit that did not finish ("did not finish") and an unknown run are all "nothing to grade"; with
`--stage all` a not-yet-finished stage B is skipped with a note, with `--stage b` it is exit 2. Exit code 2 for
"nothing to grade".

## Not tested (kept apart from passed)

- **Any real model output.** `AGENTS_MODE=real` is refused until step 7b PRs 2 to 6. Every result above is
  about stand-in answers or fabricated outputs.
- `I-1` (EC-005) and the injection case (EC-021): model calls. Shown as `NOT TESTED` in every report;
  EC-005 reads `INCOMPLETE`, never `PASS`, while `I-1` is open.
- **EC-010 and EC-012 on a real model run**: the graders exist and are tested on made-up traces, but no real call has
  been timed or priced (the spike is not done). **EC-004 on a real model**: only the stand-in's verdicts have been graded.
- A **failed** run (cost cap, time limit, model service): not graded; it belongs to the void rule (EC-R8) and the run starter.
- EC-007, EC-008 (stage C; already Tier 1 tests) and EC-011 (review time, measured on the rehearsal run, B10).
- The verdict **reasoning** is free text and is not graded (the key's reasoning column is not read).
- The evaluation-run type, scripted gates, EC-R7 refusal, D4 trace export (T-D4-1), EC-R8 void rule.
- Accessibility, responsive behaviour, interface quality, visual regression: **no UI changed**, so not in
  scope. No visual snapshot was touched.
- Performance and load: out of scope (not scoped).

## Whole-repository test state

| Run | Result |
|---|---|
| `main` before slice 1 | 270 passed, 4 skipped, **1 failed** |
| Slice 1 branch | 336 passed, **1 failed** (the same one) |
| `main` before slice 2 (slice 1 merged, plus others' changes) | 333 passed, 4 skipped, 0 failed (in a clean checkout, where `docs/prototype` is absent) |
| **Slice 2 branch** | **382 passed, 0 failed** (the 4 skips run here because `docs/prototype` exists on this machine); Tier 1 + answer key: 227 passed; Tier 2: 155 passed |
| New tests in slice 2 | 45 (3 + 28 + 14); evaluation tests in total 107 |
| Lint | `ruff 0.17.3` clean |

The one failure in slice 1 was `tests/tier1/test_crewai_setup.py::test_loading_crewai_and_building_a_crew_opens_no_connection`:
`ModuleNotFoundError: No module named 'crewai'`. It failed the same way on a clean `main` checkout, so it was **not
caused by that change**. `crewai` 1.15.35 was installed in this machine's `.venv` later the same day (not by `@qa.eng`),
and the test now passes, so slice 2 shows 0 failed. CI always had it installed.

The evaluation tests sit in `tests/tier2/` because the SAD places T-MAP-1 there and lists the other
evaluation tests as "not yet tiered" (SOQ-29); Tier 2 runs in CI but does not block a merge. T-MAP-1
**must** pass before the first evaluation run (Build card): it does.

## Defects and findings

| ID | What | Severity | Owner |
|---|---|---|---|
| F-1 | **Resolved 2026-11-21 (H-068, operator: "judge it like the name").** EC-001 matched the applicability rule exactly, but it is a free sentence, so it could never pass (a stand-in run missed it on 6 of 6 rows while every other field matched). Now every structured field keeps its exact code check, and the sentence goes to the operator under EC-002 until a model judge is calibrated against the operator's marks. `sad.md` EC-001, EC-002 and EC-R5 wording changed at the operator's instruction (`@system.arch` to check); `US-013` c11 was H-069 (done, PR #146) | Was high for the evaluation's usefulness | Closed |
| F-2 | `crewai` was missing from this machine's `.venv`: one Tier 1 test failed locally on `main` too | Low (environment) | **Closed 2026-11-21:** installed; 0 failed |
| F-3 | `ruff` was in `requirements-dev.txt` but not installed in `.venv` (the hooks do not run it; CI does). Installed locally at the pinned 0.17.3 to lint before committing | Low (environment) | — |

## Future work (deferred tests, in order)

1. The run starter (B8 after the spike): evaluation-run type, scripted gates as `specialist-eval`
   (EC-R2), EC-R7 refusal with its test (T-DEMO-1 last line), `T-MODE-1` "an evaluation run refuses
   stand-in mode".
2. D4 trace export and T-D4-1; the void rule EC-R8 (never void on invalid output, wrong result, cost
   cap, calendar generation or restart).
3. The copy cases that need the agents: `I-1` (EC-005) and the injection case (EC-021), labelled
   `eval_case` in the trace (DL-45).
4. ~~Graders for stage B (EC-004) and a runtime grader for EC-010 and EC-012~~ **Built (slice 2).** Still to do: grade
   a **failed** run (with the void rule, EC-R8) and the three-run comparison (EC-R1, EC-R1a) over saved reports.
5. EC-R5, the match rules for EC-002 (the name **and** the applicability sentence), written by the operator before the first evaluation run. Later: a model grader for EC-002, different from the model under test, **calibrated against the operator's marks** (agreement rate reported) before it replaces them.
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
- **EC-004 (slice 2).** A verdict is matched to a key row through its row's source paragraph. Only OBL-04 and OBL-05 must
  cite named facts (as the SAD says); any other row needs at least one **existing** fact ID, and extra citations are
  allowed. A key row with no extracted row is a miss; a row the specialist did not approve is **not tested**.
- **EC-010 and EC-012 (slice 2).** Measured over **every** trace line of the run: late calls and copy-case calls included
  (they ran and were paid for, DL-43, DL-45). Time is the sum of the calls' durations (units run one after another).
  Both limits are strict ("under"). On a **stand-in** run they are `NOT TESTED`: the numbers are shown but a stand-in
  call is not a model call. The trace must also add up to the run's own cost count, or EC-012 misses.
- **Decided by the operator, 2026-11-21 (open questions 4 and 5, closed):** EC-004 keeps the SAD rule as the pass mark and
  reports the key's missing facts on the other four verdicts as a non-failing note; EC-010 keeps late calls in the time
  and labels them as late (seconds and cost) in the report.
- Stage B is "finished" when its units are all done (the app stores the verdicts only then, rule 9).

## Open Questions

1. ~~F-1 / H-068~~ **Closed 2026-11-21:** the applicability sentence is judged by the operator with the name (EC-002). `US-013` c11 was updated too (H-069, `@product-mgr`, PR #146).
2. **EC-R5:** the match rules for the name and for the applicability sentence are still to be written by the operator (EC-002 is shown "for the operator").
3. Should the evaluation tests be promoted to Tier 1 once the run starter exists (SOQ-29)? (Left in Tier 2 for now, operator, 2026-11-21.)
4. ~~EC-004 citations~~ **Closed (operator, 2026-11-21):** the SAD rule stays the pass mark (named facts required for OBL-04 and
   OBL-05 only). For the other four verdicts, the key's facts that are not cited are listed as a **note** in the report
   ("information only, not a miss"). The note never changes the result and never fails the run.
5. ~~EC-010 late calls~~ **Closed (operator, 2026-11-21):** late calls stay in the time as well as the cost, so the time is what a
   user actually waits. The report labels them: "of this, LATE calls: N calls, X s, US$Y".

## Database hash baseline (H-091, set 2026-11-24)

`@backend.eng`'s H-091 (#212) adds `upgrade_failure_reasons`, which runs when the app starts (`create_app`, not
`init_db`) and rewrites the stored text of the `units` table so its `CHECK` accepts the two new failure reasons.
No row is touched. **So the first start of the app on this code changes `data/app.db`'s file hash, and that change is
expected, not a defect.** `data/spike.db` is not migrated; its hash must not change.

| File | SHA-1 now (2026-11-24, before the first start on the new code) | Expected after the first start |
|---|---|---|
| `data/app.db` | `29068e84…` (the full value is in the audit line below; same as the backup `data/app.db.bak-20261124`) | **Changes** (stored `units` text only). **Confirmed 2026-11-24: now `cfcd909e…`** (below) |
| `data/spike.db` | `32376900…` | **Must stay** `32376900…` |

**Compare table digests, not the file hash.** Recipe (read-only, `mode=ro`): the names of every table, index and trigger
(sorted), then every row of every table in `rowid` order, hashed with SHA-256. The stored `CREATE` text is left out on
purpose, because that is the one thing that changes. I read it from the backup copy, not from the real file:

- Objects: 14 tables, 4 triggers (`audit_log_no_delete`, `audit_log_no_update`, `trace_no_delete`, `trace_no_update`), no indexes.
- Row counts: `audit_log` 153, `calendar_entries` 40, `calendar_versions` 4, `flags` 6, `paragraphs` 39, `publications` 4,
  `quote_checks` 19, `row_decisions` 19, `rows` 19, `runs` 9, `trace` 52, `units` 93, `verdict_decisions` 18, `verdicts` 18.
- Digest of the names: `307b68b55d321f89`. Digest of all tables together: `e5624554c3c393d3`.

**What to check after the operator's first start** (done 2026-11-24, section below): (1) `app.db` has a new file hash;
record it. (2) The names digest and the all-tables digest are **unchanged**. (3) `spike.db` is still `32376900…`.
(4) If the app refuses to start with "not the one this version knows how to upgrade", nothing was changed: restore
from `data/app.db.bak-20261124`.

**After-start result (2026-11-24, after the operator's first start on `main` at `d7d667b`; server started in stub
mode, home page loaded, stopped, no review started). Read-only: file hashes, and `mode=ro&immutable=1` for the digests.**

| Check | Result |
|---|---|
| (1) `data/app.db` file hash | **Changed, as expected:** `29068e84…` to `cfcd909e8875fab8f054b31ad6ad8e15d622ba76`. The file size is the same (307200 bytes). |
| (2) Table digests | **Unchanged.** Names digest `307b68b55d321f89`, all-tables digest `e5624554c3c393d3`, and every per-table digest and row count equal the before-start values above (read from the real file this time, and from the backup again for the comparison). No row was added or changed. |
| (3) `data/spike.db` hash | **Unchanged:** `32376900d98eae2eaaaa5ed434610260fa820f0a`. Its `units` CHECK still has the old list (no `call limit`), as intended. |
| (4) Refusal to start | **Did not refuse:** the app started and served the home page (the operator's report); the stored `units` text now contains `'unexpected error'` and `'call limit'`, `PRAGMA integrity_check` is `ok`, and the backup still has the old text. |

So the migration ran once on the real file, took way A or B (I cannot tell which from the outside; both leave rows
alone, and the digests agree), and left every row as it was. The backup `data/app.db.bak-20261124` (`29068e84…`) is
untouched and can be kept or removed at the operator's choice.

**Seen, not understood:** a symlink `data/data` pointing back to `data/` appeared at 19:57, the time of the start. It is
git-ignored (`data/`), nothing reads it that I know of, and I did not remove it. It may be an artefact of how the app was
started; worth a look by `@backend.eng`. **Not tested:** a second start (the "nothing to do" path) on the real file, and
a review on the new code (so a real `unexpected error` or `call limit` ending was not seen; Tier 1 covers both against the
fake OpenAI).

**Closed 2026-11-24 (`@backend.eng`): the `data/data` symlink was gone when the operator checked on 24 Nov.** The
operator's listing of `capstone/data` showed only `app.db`, `app.db.bak-20261124` and `spike.db`. Nothing was removed by
this note and no database was opened. **Can the app start create it? No, by the code.** The start path
(`backend/db/connection.py`, `init_db`) only calls `mkdir(parents=True, exist_ok=True)` on the folder that holds the
database and then opens the file; no code under `backend/` or `scripts/` makes a link inside `data/`. The one place that
can is the manual run-folder loop in `backend.md` ("Before the operator's real clean run", step 1),
`for f in .venv reference .env data; do ln -s "$PROJECT/$f" "$f"; done`. Run a second time in a worktree whose `data` is
already a link to the real folder, `ln -s` follows that link and puts a new link called `data` inside the real `data/`,
pointing back at it (reproduced in a throwaway folder, no real files touched). That fits what was seen, but I cannot tell
from the files whether the loop was run twice, so this is the likely cause and not a proven one.

### Verification checklist

**Increment checked:** H-091 to H-094 (2026-11-24), the last code change on `main` (PRs #211 to #214, #216, #219, with
the sentence and wording changes of #218): two new failure reasons in the web path. `main` at `f31848f`. Runtime
`AAMAD_TARGET_RUNTIME=crewai`, `AGENTS_MODE=stand_in`. **This is a check of that increment only. It is not a
sign-off for B8, the MVP or Deliver:** the run starter, the trace export, the void rule and the model cases `I-1`
and the injection case are still not built (Future work 1 to 3), and the real-model evaluation cycle has not run.

The two new reasons have **no AC-* of their own**: they are a SAD edit (DL-58, E-11, H-092) and no user story was
changed. They are mapped to DL-58, E-11, EC-R10 and the "follow a run and recover" story (US-015, per-unit failure
rule). I did not invent an AC ID.

| Check | Result | AC / ref | Note |
|---|---|---|---|
| Correctness: unit | **Pass** (with one gap) | DL-58, E-11, EC-R10 | I ran Tier 1 on `main` at `f31848f`: **660 passed**, 1 warning (a pytest deprecation note), 0 failed. `ruff check backend tests`: clean. The tests for each fix were seen to fail first (author's statement; I did not re-run them against the old code). **Gap:** "a `call limit` failure cannot be retried" (H-091 4e) is **not tested**, because `retry_run` is still the B13b stub. It is an open item under B13b. |
| Correctness: integration / smoke | **Pass (stand-in and fake OpenAI only); not tested on the real database** | DL-58, E-11 | Real mode appears only against the fake OpenAI with a dummy key and temporary databases. The in-flight overshoot is a **known limit** (operator, 2026-11-24): a unit already in flight finishes, so the count can pass 70 by that unit's calls. **Not tested:** the first start of the app on the real `data/app.db`. The migration (`upgrade_failure_reasons`) was tested on temporary copies only. I have not seen it run on the real file (see "Database hash baseline"). No real call was made to test the cap, by design. The ux.md sentences (H-093, H-094) are text: I did not view any page. |
| Security: no new secrets; tools stay on the SAD allowlist | **Pass** | SAD allowlist, CLAUDE.md Never row | I read the diff of `backend/` from H-091's first commit to `main`. No new dependency, no new network or process call, no key or environment read, no new tool, memory, retry or re-ask. One `except Exception` (a `noqa: BLE001`, the repo's first), which is the point of E-11, with its reason written beside it. The audit entry holds the **class name only** and no traceback is logged (operator decision). The migration never touches `data/spike.db` (`create_app` only, not `init_db`) and refuses to start, changing nothing, if the stored table is not the expected one. `data/app.db` and `data/spike.db` were not opened for writing by `@backend.eng` or by me. **Not assessed:** this is a QA read, not the `@security.eng` assessment. |
| Maintainability: change stays inside the MVP and the recorded pattern | **Pass** | DL-58, Build card | One small PR per fix as asked; 16 files, mostly tests (945 lines added, 25 removed). Changes stay in the web path, the schema and the failure sentences. `rehearsal`, `demo`, `evaluation` and stand-in mode are never refused. `IFW-1` to `IFW-6` (parked) were not built. B13b (Retry) is not built. No agent loop, no live-state retrieval and no side-effecting tool appeared. The CHECK text in an upgraded database is the same as a fresh one (a test compares them). |
| Author explanation: what shipped and why it is safe to release | **Filled** (from `@backend.eng`'s H-091 Outcome and `backend.md`, as read by QA) | H-091 Outcome | A review that hits an error nobody listed now ends as **Failed** with the sentence "unexpected error", instead of sitting on "AI is drafting the rules" until a restart. The web path also stops before the 71st real call (reason `call limit`, counted over both databases, not retryable), and an existing `data/app.db` learns the two new values on its first start without any row changing. Safe to release as far as the stand-in path goes: the checks above pass, no real call or key is involved, and the migration refuses and changes nothing on any surprise. **Not yet safe to rely on:** the migration on the real file, until the operator's first start and the after-start checks are recorded. |

**UI changed?** Two sentences on the failed-review page and one in the refusal table (H-093, H-094). `ux-review.md` has no
entry for them and I did not run `*test-visual` for this check; a matching snapshot would not prove the wording
is good anyway. **Not tested, not passed.** `@ux.designer` owns that judgment.

**Model call?** The Pattern Decision includes a model call. `evals.md` status: **partial**, as its header says. Three real
runs are recorded (the third met the key's count with four cautions); nothing is graded for an EC criterion, and
`*run-evals` is not finished. This increment changes no prompt, card or model setting, so it does not change that status.

**Result of the checklist: pass for this increment, with three things left open:** (1) the first start on the real
`data/app.db`, with the new hash and after-start digests recorded; (2) the `call limit` retry test, with B13b;
(3) a look at the new sentences on a real page. **Update 2026-11-24: item (1) is closed** (the first start and the four after-start checks, section "Database hash baseline"); (2) and (3) stay open. **I am not recommending `@security.eng` yet:** B8 is not finished
and the evaluation cycle has not run (Future work 1 to 3), so a recommendation now would be early.

## Audit

- 2026-11-21 · persona `qa-eng` · action `qa` (B8 Stage A grader slice; `test-unit`, `test-integration`,
  `log-defects`, `future-work`) · `AAMAD_TARGET_RUNTIME=crewai` · no model call. `*verify-change` and the
  `@security.eng` recommendation are **not** made yet: B8 is not finished.
- 2026-11-21 · persona `qa-eng` · action `update` (H-068, operator decision) · EC-001 no longer matches the applicability rule exactly; EC-002 lists it with the name for the operator; F-1 closed; counts updated (62 new tests). Tier placement unchanged (open question 3). `AAMAD_TARGET_RUNTIME=crewai` · no model call.
- 2026-11-21 · persona `qa-eng` · action `update` (follow-up to the H-068 check on SAD EC-002) · Lines in the follow-up list: "model judge" and "judge model" changed to "model grader" where they mean the future calibrated grader for EC-002, so this file uses the SAD's word. Left as written: the dated H-068 decision lines and handoff H-068 (records of what was decided then), and the applicability `judge` agent (DL-40). No threshold, criterion or code changed. No model call. `AAMAD_TARGET_RUNTIME=crewai`.
- 2026-11-21 · persona `qa-eng` · action `qa` (B8 Stage B grader slice, operator decision; `test-unit`, `test-integration`) · EC-004, EC-010 and EC-012 graded from a finished run read from the database; 45 new tests; 382 passed, 0 failed; no model call, no real key, no paid call. `*verify-change` and the `@security.eng` recommendation are still **not** made: B8 is not finished. `AAMAD_TARGET_RUNTIME=crewai`.
- 2026-11-21 · persona `qa-eng` · action `update` (operator answers to open questions 4 and 5, closed) · EC-004: the key's uncited facts on OBL-01, 02, 03 and 06 are a non-failing note (`Criterion.notes`, shown in the report); EC-010 and EC-012: the late share of the time and cost is labelled. 4 new tests in `test_evaluation_stage_b.py` and 1 in `test_evaluation_stage_b_run.py`; 5 deliberate breaks, all caught. No threshold changed. No model call, no real key, no paid call. `AAMAD_TARGET_RUNTIME=crewai`.
- 2026-11-23 · persona `qa-eng` · action `qa` + `log-defects` (H-077, the spike report) · wrote `2.build/spike-report.md`, an interim report on the 6 real trace lines made so far (extractor 2, verifier 2, judge 1, plus the pre-flight line; US$0.0164), read-only from `data/spike.db` and `data/app.db` and from `--tally`. No test, grader, threshold or code changed here; no model call, no real key, no paid call. Raised H-085 (`@system.arch`: name the report in the SAD Audit) and H-086 (`@backend.eng`: `--tally` adds the pre-flight line to the extractor's time and cost). The real clean run is not made, so the report waits for it. `*verify-change` and the `@security.eng` recommendation are still **not** made: B8 is not finished. `AAMAD_TARGET_RUNTIME=crewai`.
- 2026-11-24 · persona `qa-eng` · action `log-defects` + `update` (H-091, the note to `@qa.eng`) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read-only: file hashes of `data/app.db` (SHA-1 `29068e849cc62e921688a30ea31283bcc56ad81e`, equal to `data/app.db.bak-20261124`), `data/spike.db` (`32376900d98eae2eaaaa5ed434610260fa820f0a`); the table digest was read from the backup copy with `mode=ro&immutable=1`, not from the real file. New: the section "Database hash baseline (H-091)". Changed in `spike-report.md`: an Update line after each of the two "does not stop at 70" sentences (12.6 and 12.7). Same Update line added in `evals.md` line 186 (the "Real-run status of Case 1" row), at the operator's instruction. The after-start hash and digests are left open for the operator's first start. No model call, no real key, no paid call, no code changed, no snapshot changed. `*verify-change` and the `@security.eng` recommendation are still not made.
- 2026-11-24 · persona `qa-eng` · action `verify-change` (the increment H-091 to H-094, `main` at `f31848f`) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · ran Tier 1 (660 passed, 0 failed) and `ruff check backend tests` (clean); read the `backend/` diff from H-091's first commit. New: the section "Verification checklist". Result: pass for that increment, with three items left open (first start on the real `data/app.db`; the `call limit` retry test with B13b; the new sentences not viewed on a page). No AC-* exists for the two new reasons, so none was invented. No `*test-visual` run, no `*run-evals`. No model call, no real key, no paid call, no code changed, no snapshot changed; `data/app.db` and `data/spike.db` not opened. The `@security.eng` recommendation is **not** made: B8 is not finished.
- 2026-11-24 · persona `qa-eng` · action `qa` + `log-defects` (H-091, the four after-start checks) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read-only: file hashes, then `mode=ro&immutable=1` for digests and the stored `units` text; server not running. `data/app.db` SHA-1 `cfcd909e8875fab8f054b31ad6ad8e15d622ba76` (was `29068e84…`; changed as expected); table digests unchanged (names `307b68b55d321f89`, all `e5624554c3c393d3`); `data/spike.db` `32376900d98eae2eaaaa5ed434610260fa820f0a` unchanged. Noted a git-ignored symlink `data/data` (not removed). No model call, no real key, no paid call, no code changed, no snapshot changed. The `@security.eng` recommendation is still not made: B8 is not finished.
- 2026-11-24 · persona `backend-eng` · action `document-backend` (docs only; closes the `data/data` item from the H-091 after-start check) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read the code only (`backend/db/connection.py`, `scripts/`, the `backend.md` run-folder loop); the link was gone when the operator checked on 24 Nov; no database opened, no model call, no code changed.
- 2026-11-24 · persona `qa-eng` · action `test-unit` + `test-integration` (H-097 PR 2, the trace export, D4 and T-D4-1) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` in `.env` (not touched) · new `backend/evaluation/trace_export.py` (`export_trace`, `check_export`) and the command `python -m backend.evaluation export RUN-ID`; 16 new tests in `tests/tier2/test_trace_export.py` (Tier 2, as the SAD places T-D4-1), written first and seen to fail (import error), run in real mode against the fake OpenAI with the dummy key and temporary databases and a temporary export folder; full suite 858 passed, 4 skipped, 0 failed; `ruff check backend tests` clean; real-name scan empty; `aamad validate` OK. No real call; no database under `data/` opened (the worktree has no `data/` folder); no schema change, so the `data/app.db` hash baseline is unchanged; `.env` not changed. Not built here: the run starter that calls the export and reports a run failed (PR 4), the void rule (PR 5), the copy cases (PR 6).
- 2026-11-24 · persona `qa-eng` · action `test-unit` + `test-integration` (H-097 PR 4a, the evaluation run starter; operator go and decisions of 2026-11-24) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` in `.env` (not touched) · new `backend/evaluation/run_starter.py` and the command `python -m backend.evaluation run` (plan without `--go`; with `--go`, a typed confirmation `evaluate <commit> 19`, then Stage A as `specialist-eval`, then it stops at G1 with no gate decision). Refuses stand-in mode, an activity other than `evaluation`, no key or model, the planted row, an unreadable call count, less than 19 calls of room under the 63 cap, and a review already in progress. Stops the run on a 400 (also one CrewAI's repeat got past), a length stop or an invalid answer. 32 new tests in `tests/tier2/test_evaluation_run_starter.py` against the fake OpenAI (dummy key, temporary databases, a spike database that does not exist, a temporary report folder); breaking `stop_reasons` on purpose made 4 of them fail; full suite 917 passed, 4 skipped, 0 failed; `ruff check backend tests` clean; real-name scan empty. No real call; no database under `data/` opened; no schema change. **Finding for PR 4b (not fixed here):** the GP calendar page labels only a stand-in run (`agents_mode`), so a published evaluation run looks the same as a real one, and the newest publication is the live calendar. Reported to the operator before 4b.
- 2026-11-24 · persona `qa-eng` · action `test-unit` + `test-integration` (H-097 PR 4b, the scripted G1, G2 and G3 and the stop rules; the operator's go after H-099 and H-100 were merged) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` in `.env` (not touched) · built on the PR 4a branch (PR 4a, #233, was still open when this was written, so this PR is based on it). New `backend/evaluation/scripted_gates.py` (G1, G2, G3 through the services the pages use, as `specialist-eval`; the demo decisions of the stories index and KEY §5, found by the answer key's row code and never by row number) and `backend/evaluation/stop_rules.py` (the 4a stop checks moved here, plus a check that the run is still active and at the expected gate). `python -m backend.evaluation run --go` now goes on after Stage A, then grades Stage B and exports the whole trace, on a clean run and on a stopped one. **Stops:** a 400, a length stop, an invalid answer, a failed unit, a run not where expected, no row approved at G1, a gate step the service refused, an error nobody listed; each ends the run (abandoned, with the reason in the audit log) and the command exits 1. A row the key does not expect, or whose quote check did not pass, is rejected with a written reason (it cannot be approved, and G1 cannot finish while a row is undecided); an unsure verdict is resolved as applies (P-1), every other verdict is confirmed. The publish is real and DL-60 keeps it off the live calendar: a test asserts the General Partner's view stays "being prepared". 19 new Tier 2 tests in `tests/tier2/test_evaluation_scripted_gates.py` against the fake OpenAI (dummy key, temporary databases, a spike database that does not exist, a temporary report folder); two 4a tests that assumed "stops at G1" were rewritten. I broke the code three ways on purpose (stop check off, wrong G2 value, empty rejected list at G3) and 3, 2 and 1 tests failed. Full suite 941 passed, 4 skipped, 0 failed; `ruff check backend tests` clean; real-name scan empty; `aamad validate` OK. No real call; no database under `data/` opened; no schema change; no template or page changed, so no visual check. **Not in this PR:** the void rule (PR 5) and the `I-1` and injection copy cases (PR 6). **Open:** the written decisions for 4b were not found in the repository; the choices above come from the stories index (demo decisions), EC-R2, KEY §5 and the 4a finding, and are listed in the PR description for the operator to confirm.
