# Spike report: the first real model calls (B3 spike, reported under B8)

Owner: `@qa.eng`. Handoffs H-077 (sections 1 to 11) and H-088 (section 12). Written 2026-11-23 on branch
`qa-eng/h077-spike-report`; section 12 added 2026-11-24 on branch `qa-eng/h088-first-real-run`.
`AAMAD_TARGET_RUNTIME=crewai`, `AGENTS_MODE=stand_in` while writing: **I made no model call, used no key and
sent nothing.** Every number below was read from `data/spike.db` and `data/app.db` (opened read-only; their
hashes were the same before and after for sections 1 to 11; for section 12 see its first paragraph, because `app.db`
grew while I worked) and from the read-only `--tally`.

**Status: interim.** The spike is not finished. Sections 1 to 11 cover the **6 trace lines in `spike.db`**
(one command per call, made before the web app was run for real). **Section 12 covers the operator's first
real run through the web app (review A, `RUN-20261123-1`): 19 more requests in `app.db`. That run did not
finish: it failed at Stage C** (section 12.4). **Review B (`RUN-20261124-1`, section 12.6) completed and
published a calendar, but with 18 entries, not the key's 22, so it is not a clean Case 1 result either.**
**Where sections 1 to 11 say "the clean run is not made", read section 12:** two runs were made; neither is the
clean run the plan hopes for, and a key-matching calendar is still owed.

## 1. What was run, and what was not

**Run (as made, not as planned):** extractor 2 calls, verifier 2 calls, judge 1 call, plus one pre-flight
line. **6 of 70 call slots used. Run cost US$0.0164** (the US$2.50 per-run cap and the US$15 target in DL-36
are far away).

**Not run (DL-55, operator, 2026-11-23).** The SAD planned each role's call on the demo inputs five times
and a verifier bake-off between two models (DL-26). The operator skipped "five runs each" for the extractor
and the judge and dropped the bake-off. So **the verifier was not compared with another model**, and **C-2
and I-1 were never sent to it**. **The figures below are not a five-run share.** In particular, "4 of 5"
first-attempt schema-pass means 4 of the **5 real model calls made**, nothing more.

## 2. Result in one table

| Role | Model | Pinned setting accepted? | Real calls | Passed its schema on the first try | Cost per call | Time per call |
|---|---|---|---|---|---|---|
| Extractor | `gpt-6-luna` | `none`, temperature 0: yes | 2 | 2 of 2 | US$0.00033 and US$0.00034 | 4.4 s and 3.7 s |
| Verifier | `gpt-5.6-terra` | `low`, no temperature: yes | 2 | **1 of 2** (call 1 failed our check; section 4) | US$0.0077 and US$0.0057 | 5.1 s and 3.9 s |
| Judge | `gpt-6.1-terra` | `medium`, no temperature: yes | 1 | 1 of 1 | US$0.0013 | 3.9 s |
| **All** | | **yes, on every real call** | **5** | **4 of 5** | | |

Pass means "valid against the schema and our checks", not "right". Rightness is a separate column in the
next table, and only where an answer key exists.

## 3. Every trace line

| # | Unit | What it was | Model returned | In / out tokens | Cost | Time | Stop | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | `SRC-UCILAW#1` | **Not a model call:** CrewAI's own pre-flight token count | none | 0 / 0 | US$0.0011 (**estimated**) | 1.5 s | none | Flagged `off_pinned_setting` by mistake. Both the cost and the flag are false alarms (finding 1) |
| 2 | `SRC-UCILAW#1` | Extractor call | `gpt-6-luna` | 1500 / 360 | US$0.00033 | 4.4 s | `stop` | Valid; 3 rows (the key has 2 for this document) |
| 3 | `SRC-UCILAW#2` | Extractor call | `gpt-6-luna` | 1500 / 373 | US$0.00034 | 3.7 s | `stop` | Valid; 3 rows. First line to carry `request_path` |
| 4 | `SRC-UCILAW-P3#1` | Verifier, planted conflict C-1 | `gpt-5.6-terra` | 1723 / 351 | US$0.0077 | 5.1 s | `stop` | **Invalid** (our check refused it), but it **cited the right paragraph with a verbatim quote** (finding 2) |
| 5 | `SRC-UCILAW-P3#2` | Verifier, C-1, after the fix | `gpt-5.6-terra` | 1721 / 185 | US$0.0057 | 3.9 s | `stop` | **Valid, C-1 caught, no false alarm** |
| 6 | `SRC-UCILAW-P3#1` | Judge, row 1 | `gpt-6.1-terra` | 988 / 62 | US$0.0013 | 3.9 s | `stop` | **Valid and CORRECT** against the key (`applies`, citing `FACT-01`) |

The line costs add up to US$0.0164, the same as the run's cost count. Lines 2 to 6 were priced from the
usage the model returned (not estimated). Lines 4 and 6 share the unit name `SRC-UCILAW-P3#1` because
a unit name is counted per step: line 4 is the verifier's first attempt on that row and line 6 is the judge's.

## 4. Findings

**Finding 1: the first real call sent two requests (H-076).** The fake server could not have shown this.
CrewAI sent a pre-flight token count (`POST /v1/responses/input_tokens`) before the real call, so "one unit
sends one request" was broken. The answer itself was valid. **Report it as: one model call plus one pre-flight
request, 2 of the 70 slots used.** Take the model call's figures from line 2, not line 1. The pre-flight
switch is off since step A; a test (T-REQ-1) keeps it off; and since step D any request that is not a chat
completion is refused before it is sent and traced at cost 0 (T-REQ-2). The two lines stay as they are: the
trace is append-only (operator, 2026-11-22). **A request that is not a chat completion is itself a spike
finding**, and the fake server cannot show behaviour that only happens on the real service.

**Finding 2: the verifier caught C-1 but failed our schema check on its first try (H-078).** It wrote the
fields `field` and `row_value` on a cross-source flag, which only an internal flag may carry. **This is a
schema failure, not a miss**, and it counts in the first-attempt share. Three things together caused it
(strict mode requires every key; one flag shape with five optional keys; the card's example did not match the
strict format). **The fix is the schema, not the prompt or the check:** the flag is now sent as two shapes. So
**calls 4 and 5 were sent different `response_format`s; the prompt version did not change.** After the fix,
the answer was valid, caught C-1 and raised no false alarm, and OpenAI **accepted the nested `anyOf`**. That
is one valid answer, which is a data point and not a trend.

**Finding 3: the judge's first call passed (H-079).** One easy row, one request, 62 output tokens, the
verdict the key expects. It cost US$0.0013 against a planned US$0.004 to 0.016; the printed worst case
(US$0.0210) is a ceiling, not a forecast. Hidden reasoning tokens are inside the 62 and the trace cannot
separate them, so the fair reading is that it reasoned very little on an easy row.

**Untested precaution:** `minItems` and `maxItems` were dropped from the judge's wire schema (#172) because
OpenAI's guide lists them as both supported and not yet supported. We never sent them, so we do not know
whether they would have been refused. Our own check still enforces the rule.

## 5. The pinned reasoning setting (SAD "Decisions to take once the spike has shown the result", decision 2)

All three models accepted their pinned settings on every real call: no 400 on `reasoning_effort`, no silent
repeat by CrewAI. **Calls that ran off the pinned setting: 0 of 5 real calls.** Line 1 carries the flag but
is not a model call, so it is not counted (judge a line by its request, not only by its flag). Each spike
command is a new process and CrewAI remembers a refusal only inside a process, so a refusal would have been
seen and flagged again on every command. The honest wording is **"so far"**, on 5 calls. It is not "proved".

## 6. Against the targets, and what the numbers do not show

- **Per-call time and cost are far inside the limits:** 3.7 to 5.1 s against call timeouts of 60 to 90 s;
  at most US$0.0077 per call against the US$2.50 per-run hard stop.
- **Stage time limits (375 s, 150 s, 30 s) were not measured by the six `spike.db` lines.** They stay at the
  SAD's starting values as the operator's decision (DL-55). My reading from the per-call figures was that
  Stage A is about 5 extractions and 7 verifications (roughly a minute) and Stage B about 6 judge calls
  (roughly 25 s). **Those were estimates from per-call figures, not measured stage times**, and the units run
  one after another (DL-56). **Section 12.2 now gives one measured run** (Stage A 25 s, Stage B 30 s); the
  estimate for Stage A was high and for Stage B about right. One run is one value, not a distribution.
- **EC-010 (under 5 minutes) and EC-012 (under US$2) are not graded by this spike.** They are whole-run
  figures; the graders for them exist (`qa.md`), but no real run has been graded: the one real run in
  `app.db` is labelled `spike` (it does not count towards the cycle, EC-R6) and ended `FAILED`. Its figures are
  in section 12.2 as observations only.

## 7. Known limits (stated, not hidden)

1. **The verifier is measured on C-1 (sections 2 to 4) and, once, on C-2 (section 12.3).** I-1 was never sent
   to it. Each is one catch in one run, not a recall figure. The first proper test of them is the evaluation
   cycle, where a miss is reported as it stands; changing the model afterwards needs a recorded operator
   decision (DL-55).
2. **The verifier's false-alarm rate is unmeasured.** No separate OK-1 run exists. In the one web-app run it
   raised no flag on the 5 rows that should have none (section 12.3): one run, not a rate.
3. **In sections 1 to 11 the extractor was tried on one document of five** (the same one twice), and **the
   judge on one row of the six that reach it**, with only the `applies` verdict seen. The real extractor
   **split one rule in two** (3 rows against the key's 2 on `SRC-UCILAW`). That is a finding for EC-001 and
   EC-002, not a defect in the build. **Section 12 widens this, once:** all five documents were extracted and
   all seven rows were judged, in one run, and the judge gave `unsure` five times and `does_not_apply` once
   (so "no real model has produced `unsure` or `does_not_apply`" is no longer true). It is still one run.
4. **No per-role figures from five runs exist**, so none of the stage limits is "set from measurement".
5. **The verifier was not compared with another model**, and the bake-off tooling (`--case`, `--tally`) was
   built but not run. It is optional future work and needs a new operator decision.
6. **Two calls to one role are not a distribution.** Every "mean" in this report is a mean of 1 or 2 values.

## 8. Not tested (kept apart from passed)

- The bake-off (DL-26; dropped, DL-55) and the five runs each for the extractor and the judge (skipped).
- I-1 and the altered quote on the verifier (C-2 and the false-alarm check were seen once, in section 12;
  neither is a rate). The injection case on the extractor. Nothing here has had three runs of one commit.
- A **real run through the web app that completes**, start to finish. One was made (section 12); it ended
  `FAILED` at Stage C, so **Stage C, the GP's calendar and G3 have never run on real agents.**
- A **real provider failure** (a 5xx, a timeout, an invalid answer on the wire): none has happened.
- Stage times, whole-run cost and EC-010 and EC-012 as **graded** figures (section 12.2 has observations only).
- Quality of any real answer beyond the checks above (C-1 and C-2 caught once each; five judge verdicts
  compared with the key in section 12.3, not graded).
- No page or style changed, so accessibility, responsive behaviour and visual regression are out of scope.
  Performance and load testing are not scoped.

## 9. Reading the data (cautions for whoever uses these tables)

- **`--tally` counts the pre-flight line inside the extractor's first unit.** Its extractor "time (mean)
  4.9 s" and "cost US$0.0018" include line 1's 1.5 s and US$0.0011. The per-call figures in sections 2 and 3
  come from the trace lines, not from that mean. (Defect D-1, below.)
- `--tally` prints "valid 1/5" and "valid runs still needed for 5 of each case". The "5" is display only
  (`RUNS_PER_CASE = 5`); nothing in the runner stops on it (`backend.md`).
- `--exclude 'SRC-UCILAW-P3#1'` leaves out the verifier call sent before the two-shape fix. Both views give
  the same 6 slots and US$0.0164.
- Lines written before step D have an empty `request_path`.

## 10. Defects and findings

| ID | What | Severity | Owner |
|---|---|---|---|
| D-1 | `--tally` adds the pre-flight line's time and cost to the extractor's first unit, so its mean time and cost for the extractor read high (4.9 s against 4.1 s for the two model calls). It only changes a printed summary, not the trace or the cap | Low | `@backend.eng` (not changed here; I do not edit code under `backend/`) |
| F-1 to F-3 | The first-call pre-flight, the verifier's flag shape and the judge's schema precaution: found by the spike, fixed or recorded before this report | See section 4 | Closed (H-076, H-078, H-079) |
| F-4 | **One sentence became two rules, and Stage C refused the duplicate calendar entry.** The real extractor split `SRC-UCILAW-P2` the same way in 3 of 3 real calls; the run ended `FAILED` at Stage C on the DL-35 collision (section 12.4). The refusal worked as the SAD says; the open question is what the SAD should say a specialist does about it | Medium for the demo path (a real run cannot finish unless the specialist rejects one row at G1); not a defect in the refusal | `@system.arch` (H-087); evidence in section 12 |
| F-5 | **The judge said `unsure` on 4 rows where the key says `applies`** (OBL-01, OBL-02 ×2 rows, OBL-05), and asked for facts the fund profile does not hold (section 12.3). Safe direction (a human decides at G2). Repeated on OBL-01 and OBL-05 in review B (12.6): 2 runs | Low to Medium for EC-004 (3 of 3 runs, 6 of 6 needed); a key-or-judge question, not a build defect | Operator, in the evaluation cycle; recorded here, not decided |
| F-6 | **A false "duplicate" rejection at G1 removed a real obligation, and the calendar was published 4 entries short.** In review B the extractor did **not** split `SRC-UCILAW-P2`; the operator, expecting a split, rejected the one OBL-02 row as a duplicate, with a reason that is untrue for that run. The G3 audit entry records an acknowledgement of "1 rejected rules". The published calendar has 18 entries, not 22 (the 4 quarterly AED subscription-tax entries are missing). The system did what the human decided; the audit log keeps the untrue reason (append-only) | Medium for the demo path: a published calendar can silently miss a deadline, which is the wrong-output risk the gates exist for | Operator; for `@system.arch` with H-087 (the case for a G1 warning that tells one rule from two). I recommend nothing |
| D-2 | **The H-088 handoff's judge count (and `backend.md`'s) reads "one applies, two unsure, one does_not_apply".** The stored verdicts are 1 applies, **5 unsure**, 1 does_not_apply (7 rows). This report uses the stored figures | Low (a wording error in a hand-off; no data is wrong) | `@backend.eng` (H-089); not changed here, because `backend.md` is not mine |

## 11. Future work (deferred tests, in order)

1. ~~The operator's one real clean run, then a section 12 here~~ **Done once (section 12); the run failed at
   Stage C; review B (section 12.6) completed and published, with 18 entries instead of 22.** Still to do: one
   more real run whose calendar matches the key. The operator's plan: **it waits for `@system.arch`'s change for
   H-087, then tests that change and Case 1 together; about 16 slots, 41 of 70 used, so about 13 would remain.
   That is the last run the cap allows without a new operator decision; do not plan on a retry.**
2. The evaluation cycle (B8, B9): I-1 and the altered quote, and C-2 and OK-1 as proper cases, on the
   verifier; the judge's `unsure` on OBL-04 **and the four rows it said `unsure` on that the key says apply**
   (section 12.3); EC-010 and EC-012 on a graded real run; the stage times measured again, with the limits
   then reviewed.
3. Optional, new decision needed: the bake-off tooling that already exists.

## 12. The first two real runs through the web app (review A, `RUN-20261123-1`, 2026-11-23; review B, `RUN-20261124-1`, 2026-11-24)

**Added for H-088.** The operator ran the web app in real mode (`SPEND_ACTIVITY=spike`, demo rule off,
`FND-DEMO-01`). I read `data/app.db` read-only (SHA-1 `7d77ea92…` for every read of review A; `spike.db` `32376900…`
unchanged throughout) and checked every figure in the handoff against the `trace`, `rows`, `flags`, `verdicts`,
`audit_log` and `runs` tables. **I made no call.** The run is **`FAILED` at Stage C**, labelled `spike`, so it
**does not count towards the evaluation cycle** (EC-R6) and **cannot pass or fail a criterion** (3 of 3 runs,
EC-R1). Everything below is an observation about one run. **`app.db` changed during my work, and not because of me:** at 11:08 on 2026-11-24 its hash was `f9c8c90a…`,
because the operator had started review B (`RUN-20261124-1`, `ACTIVE` at G1, 11 trace lines at that moment). **Review B
is in section 12.6, not in 12.1 to 12.5, which are review A only.** The trace and the audit log are append-only, and I re-read review A's
totals after the change (19 trace lines, US$0.0427, 42 audit events, 7 rows, `FAILED` at `C_RUNNING`): they are the
same. **Any slot count in 12.1 to 12.5 is the count at the end of review A; section 12.6 has the count after review B.**

### 12.1 Calls

| Role | Model returned | Requests | Valid on the first try | Mean time | Cost | Tokens in / out |
|---|---|---|---|---|---|---|
| Extractor | `gpt-6-luna` | 5 (one per document) | **5 of 5** | 2.4 s | US$0.0012 | 7167 / 903 |
| Verifier | `gpt-5.6-terra` | 7 (one per row) | **7 of 7** | 1.5 s | US$0.0272 | 12163 / 240 |
| Judge | `gpt-6.1-terra` | 7 (one per approved row) | **7 of 7** | 4.3 s | US$0.0143 | 6852 / 1490 |
| **All** | | **19** | **19 of 19** | | **US$0.0427** | 26182 / 2633 |

- All 19 requests went to `/v1/chat/completions`; stop reason `stop` on every one; **0 off the pinned setting,
  0 estimated cost, 0 late, 0 invalid, 0 failed, 0 retried.** The settings sent were the pinned ones
  (extractor `none` and temperature 0; verifier `low`; judge `medium`). **This adds 19 first-attempt valid
  answers. It does not turn the first call's "4 of 5" into a five-run share** (section 1, H-077): the two
  figures cover different calls and neither is a rate.
- **Call slots: 25 of 70 at the end of review A** (6 in `spike.db`, 19 in `app.db`), **US$0.0591 over both** (US$0.0164 + US$0.0427).
  The `--tally` role tables read `spike.db` only, so the figures above come from `app.db` directly. The tally's
  "Run cost" line is being fixed in its own PR (merged as #195).
- The pinned-setting finding of section 5 now stands on **24 real calls** (5 + 19; 40 with review B, section 12.6) instead of 5: no 400 on
  `reasoning_effort`, nothing off the pinned setting. "So far" is still the honest wording.

### 12.2 Time and cost (observed, not graded)

| What | Observed | Where it comes from | Against |
|---|---|---|---|
| Stage A (start to "Stage A finished") | **25 s** | audit log, 23:04:16 to 23:04:41 | limit 375 s (DL-43); my earlier estimate "roughly a minute" was high |
| Stage B (G1 completed to "Stage B finished") | **30 s** | audit log, 23:07:18 to 23:07:48 | limit 150 s; my earlier estimate "roughly 25 s" was close |
| Stage C | 0 s of agent time | no model call; the stage failed on a rule in our code | limit 30 s |
| Sum of every model call (what EC-010 counts) | **52.7 s** | trace | EC-010 would be under 5 minutes |
| Run cost | **US$0.0427**, and the trace adds up to the run's own `cost_so_far` | trace and `runs` | EC-012 would be under US$2.00 |

- **Not graded.** EC-010 and EC-012 need 3 of 3 runs of one commit under `evaluation` (EC-R1, EC-R6); this is one
  `spike` run that ended `FAILED`. I give the figures so the next reader has a real number, not so they pass.
- The verifier's 1.5 s mean (against 3.9 s and 5.1 s in section 3) tracks how much it wrote: 240 output tokens
  over 7 calls here, against 185 and 351 for one call each earlier. **That is a reading from two kinds of
  call, not a measured cause.**
- Stage limits were **not tested**: nothing came near them, so this run says nothing about what happens at one.

### 12.3 What the three roles did

**Extractor: 7 rows against the key's 6.** Five documents, five valid answers. Every row sits on a paragraph the
key names, the decoy OBL-06 was extracted (as it must be), no row came from a paragraph that must not be
extracted, and the business-day rule is `not_confirmed` on all 7 rows (EC-003's wording). **The one extra row
is the OBL-02 split:** `SRC-UCILAW-P2` ("within 20 calendar days following the end of each calendar
quarter") came back as two rules, "subscription tax return" and "payment of subscription tax", with the
same recipient (AED), frequency, anchor and offset. **The real extractor made this split in all 3 of its 3 real
calls on this document** (the two spike calls, trace lines 2 and 3, and this run), with the same two names each
time. Three calls are three samples, not a rate, but they point to a stable reading of the sentence more than to
noise (my reading; the model could still differ on another day). Read against EC-001 ("6 of 6 rows; 0 extra")
it would be one extra row, and against EC-002 it is a name question for the operator. **It is a finding, not a
pass and not a defect in the build.**

**Verifier: C-1 and C-2 flagged, nothing else.**

| Row | Key obligation | Flag | Reading |
|---|---|---|---|
| 4 (`SRC-UCILAW-P3`) | OBL-03 | cross-source, against `SRC-PRACT-P1` (four months, not six) | **C-1 caught again** (first valid catch: section 4, call 5) |
| 6 (`SRC-RBELAW-P1`) | OBL-05 | cross-source, against `SRC-PRACT-P2` (the date of the change, not awareness) | **C-2 caught, first time ever sent to the verifier** |
| 1, 2, 3, 5, 7 | OBL-01, OBL-02 (×2), OBL-04, OBL-06 | none | **No false alarm**, including on OBL-01 (the key's "no conflict raised" row) |

2 cross-source flags, 0 internal. Read against EC-005 and EC-006 it would be what the key asks for on this
run, except that I-1 and the altered quote were not in it (EC-005 is 4 of 4 and only 2 were tested), and the
run had 7 rows, not the key's 6. **One run is not a recall or a false-alarm rate.**

**Judge: the first real `unsure` and `does_not_apply` verdicts, and a gap against the key.** The stored
verdicts are **1 `applies`, 5 `unsure`, 1 `does_not_apply`** (7 rows; the handoff's "one applies, two unsure,
one does_not_apply" counts 4, see D-2).

| Row | Key says | Judge said (facts it cited) | Same as the key? |
|---|---|---|---|
| 1 (OBL-01) | applies (FACT-01) | **unsure** (FACT-01, FACT-02) | **No** |
| 2 and 3 (OBL-02, split) | applies (FACT-02) | **unsure**, both (FACT-01, FACT-02) | **No**, both |
| 4 (OBL-03) | applies (FACT-01) | applies (FACT-01) | Yes |
| 5 (OBL-04) | **unsure** (FACT-03, FACT-04) | **unsure** (FACT-02, FACT-03, FACT-04) | **Yes**, and it cites both named facts |
| 6 (OBL-05) | applies (FACT-06, EVT-01) | **unsure** (FACT-06, EVT-01) | **No** |
| 7 (OBL-06) | does not apply (FACT-05) | does_not_apply (FACT-05) | Yes |

- **The named confident error did not happen:** the judge did not say "applies" on OBL-04 (EC-004's one named
  failure). It said `unsure` on OBL-04 for the key's reason (CNMV registration unconfirmed).
- **On the key's 6 obligations the judge matched on 3 (OBL-03, 04, 06) and was more cautious than the key on 3
  (OBL-01, 02, 05).** Every difference is `unsure` where the key says `applies`, so each one goes to a human
  at G2, the safe direction. Read against EC-004 (6 of 6 needed) it would be 3 of 6 on this run. **Not graded,
  and it is one run.**
- **Why, as the judge wrote it (I read the stored reasoning for all five):** it said the facts do not state
  something the rule needs: whether the fund is "within the scope of the circular" (OBL-01), whether it is "an
  undertaking for collective investment" (OBL-02 and the same wording on OBL-04), and whether the fund's
  beneficial-owner information actually changed after an investor crossed the threshold (OBL-05). The fund
  profile (FACT-01 to FACT-06) does not state those things. **I do not decide whether the key is too generous
  or the judge too strict; that is the operator's call**, and the evaluation cycle will show whether it repeats.
  What the run does show is that the judge reads the rule closely and asks for facts the profile lacks.
- At G2 the operator resolved the five `unsure` rows to `applies` (reason "test" on all five) and confirmed
  rows 4 and 7. That is the design (a human decides), and a "test" reason is not a real compliance decision.

### 12.4 The failure at Stage C (for evals Case 3)

After G2, Stage C found two approved rules with the same calendar entry ID
(`ENT-FND-DEMO-01-SRC-UCILAW-P2-AED-2026-12`, from rows 2 and 3) and **refused to build the calendar**, as DL-35
says it should. The run is `FAILED`, phase `C_RUNNING`.

| Check that it **failed clearly** | Result | How I checked it |
|---|---|---|
| The page said so in plain words | **Yes** | the wording "The dates could not be worked out into one complete calendar" is in `backend/services/runs.py:112`, and `backend.md` quotes the page; **I did not view the page** |
| The audit log names the reason and both rows | **Yes** | audit row 82: "Two approved rules give the same calendar entry ENT-FND-DEMO-01-SRC-UCILAW-P2-AED-2026-12: ROW-RUN-20261123-1-2 and ROW-RUN-20261123-1-3 (DL-35)" |
| No calendar was stored | **Yes** | 0 rows in `calendar_versions` for the run |
| Nothing moved forward | **Yes** | `FAILED`, phase `C_RUNNING`; no G3 |
| The cost was kept | **Yes** | `cost_so_far` US$0.0427 equals the trace total |
| No later request was sent | **Yes** | the last trace line is 23:07:46 (Stage B); Stage C ran at 23:09:42; no line after |
| The audit trail of earlier decisions survived | **Yes** | all 42 audit events for the run (rows 41 to 82: the review start, every agent output, every decision and refusal, G1, G2) are there, and the audit log is append-only |

**Keep these two apart, as the handoff asks.**
1. **What this shows:** the system **fails clearly** on a refusal in our own code, on a real run, and keeps the
   audit trail. That is real-run evidence that a failure is reported plainly.
2. **What it is not:** it is **not** one of the four reasons evals.md Case 3 lists (model service, invalid output,
   cost cap, stage time limit), and **not a provider failure**. It is a **fifth reason against that list, in
   our own code**: a stage declining to publish an inconsistent result. **The SAD already names it** (§4 failure
   reasons, number 7, `calendar generation`, "including an entry ID collision"): it is **not** a model-service
   failure for the void rule (EC-R8) and **cannot be retried** (`RETRY_NOT_ALLOWED`, DL-51). So Case 3's list of
   four was incomplete; the build did what the SAD says. **"What a real provider failure looks like on the wire" is
   still open and untested**; nothing here changes that, and I still do not recommend paying to provoke one.

It also shows that **a clean run will not always finish**: Case 3 said a clean run "will not show this case"; this
one did, by accident, and it ended before the GP's calendar and G3. **So Stage C, the calendar, G3 and the GP's
view have not run on real agents.** The specialist could have avoided the failure by rejecting one of the two
rows at G1 (the refusal is the safeguard; the operator tried that in review B, where it went wrong: see 12.6). Whether the SAD should merge
the two rules, split the entry ID, or leave the refusal as the answer is H-087, for `@system.arch`. **I make no
recommendation on that; it is a design decision.** **One consequence for the cycle** (evals.md Open Questions 6):
the split has now happened in 3 of 3 real calls on this document, and reason 7 is neither voidable nor retryable,
so a cycle run that repeats it ends `FAILED` unless a duplicate row is rejected at G1.

### 12.5 How to read sections 12.1 to 12.4 (review A)

- **One run, one commit, `spike`, `FAILED`.** None of it counts towards the cycle. Every "would be" above is a
  reading of one run against a criterion, never a result.
- **Neither the split nor the judge's caution is a defect in the build.** Both are what the real model did on a
  real document; the build handled them as designed (the refusal at Stage C; the human gate at G2).
- **Not tested here** (also added to section 8): I-1, the altered quote, the injection case, a provider failure,
  Stage C past the refusal and G3 (review B reached them: 12.6), the GP's view, three runs, and the page itself (I read the text in code and the
  database, not the screen).

### 12.6 Review B (`RUN-20261124-1`, 2026-11-24): the path completed, the calendar is 18 entries, not 22

**Added for H-088 (the operator's follow-up).** Read from `data/app.db` read-only (SHA-1 `eef1bba4…` at the time;
`spike.db` unchanged). I made no call and did not view any page. The run is `COMPLETED` at G3 with a published
calendar, labelled `spike`, so it **does not count towards the cycle** (EC-R6) and **cannot pass or fail a criterion**.
**Label it honestly: it shows the full real path works, but it is not a clean Case 1 result,** because the operator
wrongly rejected one row at G1 (below) and the calendar is 4 entries short.

| Role | Model returned | Requests | Valid on the first try | Mean time | Cost | Tokens in / out |
|---|---|---|---|---|---|---|
| Extractor | `gpt-6-luna` | 5 | **5 of 5** | 2.5 s | US$0.0011 | 7167 / 777 |
| Verifier | `gpt-5.6-terra` | 6 (one per row) | **6 of 6** | 1.8 s | US$0.0248 | 10412 / 333 |
| Judge | `gpt-6.1-terra` | 5 (the 5 approved rows) | **5 of 5** | 4.8 s | US$0.0096 | 4900 / 932 |
| **All** | | **16** | **16 of 16** | | **US$0.0355** | 22479 / 2042 |

- All 16 on `/v1/chat/completions`, stop reason `stop`, **0 off the pinned setting, 0 estimated, 0 late, 0 retried,
  0 invalid**. No request was sent after Stage B (the last trace line is 11:10:21).
- **Call slots: 41 of 70** (6 in `spike.db`, 35 in `app.db`); **US$0.0946 over both**. Real calls so far: 40 (5 + 19 + 16),
  none failed. The web app itself does not stop at 70 (`backend.md`, 2026-11-23), so the cap is kept by discipline.
- **Observed, not graded:** Stage A 25 s (11:07:40 to 11:08:05), Stage B 24 s (G1 completed 11:10:00 to 11:10:24),
  Stage C under a second (no model call), 47.2 s of model calls in all. Review A: 25 s and 30 s. Two runs, two values.

**Extractor: 6 rows, one per key row, no split.** `SRC-UCILAW-P2` came back as **one** rule, "subscription tax
return and payment", which is the key's OBL-02. **So the split is not predictable:** across the real extractions of
this document it split in 3 of 4 (the two spike calls and review A) and not in review B. Four samples, not a rate.
(I compared the row count and sources, not every field; the grader was not run.)

**Verifier: C-1 and C-2 flagged, nothing else.** Cross-source flags on row 3 (OBL-03, against `SRC-PRACT-P1`) and row 5
(OBL-05, against `SRC-PRACT-P2`); no flag on rows 1, 2, 4 and 6, OBL-01 included. That is **2 of 2 web-app runs** with
both caught and no false alarm. I-1 and the altered quote were not in the run (demo rule off). Still not a rate.

**Judge (5 approved rows; row 2, OBL-02, was rejected so it was not judged):**

| Key obligation | Key says | Judge said | Same? | Review A said |
|---|---|---|---|---|
| OBL-01 | applies | **unsure** | **No** | unsure |
| OBL-03 | applies | applies | Yes | applies |
| OBL-04 | **unsure** | unsure | Yes | unsure |
| OBL-05 | applies | **unsure** | **No** | unsure |
| OBL-06 | does not apply | does_not_apply | Yes | does_not_apply |

**The same verdicts in both runs on every obligation judged in both:** OBL-01 and OBL-05 `unsure` where the key says
`applies` (F-5), OBL-03, 04 and 06 as the key says. The named confident error ("applies" on OBL-04) did not happen in
either run. **Two runs now point the same way, which makes "the judge is stricter than the key on OBL-01 and
OBL-05" harder to call noise; it is still two runs, and whether the key or the judge is wrong is the operator's call**
(evals.md Open Questions 7). I did not re-read review B's stored reasoning.

**What went wrong, and whose it was.** At G1 the operator rejected `ROW-RUN-20261124-1-2` with the reason "Duplicate of
the subscription tax return rule: same source paragraph (SRC-UCILAW-P2), same deadline sentence. The extractor split one
rule in two; the calendar needs one. See H-087." **That reason is untrue for this run:** there was one row for that
paragraph, no duplicate. The operator expected a split because review A had one. So OBL-02 left the calendar, and the
published calendar holds **18 entries (OBL-01 12, OBL-03 1, OBL-04 4, OBL-05 1), not the key's 22**: the 4 quarterly AED
subscription-tax entries are missing. The audit log (append-only) keeps the untrue reason. G3 recorded "Calendar
published (acknowledged 1 rejected rules and 8 unused paragraphs)", so the acknowledgement named the rejection (I did
not view the screen). **The system did what the human decided.** This is finding F-6.

**What review B proves, and what it does not.**

| | |
|---|---|
| **Proves (real service, one run)** | The whole path ran on real agents: start, Stage A, G1 (with a rejection), Stage B, G2, Stage C, G3, publish. 16 of 16 first-try valid answers. The audit log has **0** events with stand-in wording. Stage C, which failed in review A, finished here **because no duplicate existed** (H-087 is still open, so the refusal itself is unchanged) |
| **Does not prove** | A calendar that matches the key (22 entries): **still owed**. Any EC criterion (spike run, one run). That the GP's page shows the calendar correctly (I did not view it; the database holds the 18 entries). A real provider failure. I-1, the altered quote, injection. The collision refusal and review B together show it **never fires when the extractor does not split**, and that a specialist at G1 must tell "two rules" from "one rule" by reading the rows (for H-087) |

**What comes next (the operator's plan, 2026-11-24).** Review C is **skipped for now.** There will be **one more real run,
after `@system.arch`'s change for H-087 lands**, testing that change and Case 1 together. It needs about 16 slots; 41 of 70
are used, so about 13 would remain, **not enough for a second full review. That run is the last one the cap allows without
a new operator decision; do not plan on a retry.**

## Sources

`handoffs.md` H-077, H-076, H-078, H-079, H-083, H-087, H-088; `sad.md` Measurement spike, DL-26, DL-35, DL-36,
DL-40, DL-43, DL-55, DL-56, EC-R1, EC-R6, EC-R10; `backend.md` "B3 spike finding", "finding 2", "finding 3",
"what is waived" and "The first real run through the web app"; `data/spike.db` (6 trace lines) and
`data/app.db` (19 real trace lines, run `RUN-20261123-1`, plus its rows, flags, verdicts and audit log),
read-only; `mock-data/expected-obligation-library.md` (the key) and `mock-fund-profile.md` (the facts);
`backend/services/runs.py` (the Stage C wording); `--tally` and `--tally --exclude 'SRC-UCILAW-P3#1'`;
`backend/runtime/spike_tally.py` (to find D-1).

## Assumptions

- The operator's decisions of 2026-11-23 stand (DL-55): no bake-off, no five-run figures, limits kept.
- "Valid" means the answer passed the schema and our checks (CR-003, D5); "CAUGHT" and "CORRECT" are
  judged against the answer key, as the tally does.
- Per-call figures are read from trace lines 2 to 6; line 1 is excluded from any model-call figure.

## Open Questions

1. ~~When the operator makes the clean run, where is it reported?~~ **Closed 2026-11-24.** Here, as section 12,
   because it counts toward the 70 and is labelled `spike`. Review B is section 12.6.
2. Should D-1 be fixed in `spike_tally.py`, or left as a documented reading caution? `@backend.eng` owns it.
3. `sad.md` says the spike's output is "named in this document's Audit when it exists". That is
   `@system.arch`'s file, so I raised a handoff rather than edit it.

## Audit

- 2026-11-23 · persona `qa-eng` · action `qa` + `log-defects` + `future-work` (H-077, the spike report) ·
  `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read-only: `data/spike.db` and `data/app.db` hashes
  unchanged, `--tally` only. No model call, no real key, no paid call, no code changed, no snapshot changed.
  Interim report on 6 trace lines; the real clean run is not made. `*verify-change` and the
  `@security.eng` recommendation are **not** made: B8 is not finished.
- 2026-11-24 · persona `qa-eng` · action `qa` + `log-defects` + `future-work` (H-088, section 12: the first real
  run through the web app, review A) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read-only:
  `data/app.db` and `data/spike.db` opened with `mode=ro`; `spike.db` unchanged; `app.db` unchanged for every read of review A, then it grew when the operator started review B (`RUN-20261124-1`, not mine, not in this report; review A's totals re-read and the same). Every figure in
  the handoff was re-read from the database; **one did not match** (the judge's verdict count: the stored
  figure is 5 `unsure`, not 2; D-2, H-089). New: section 12, findings F-4 and F-5, defect D-2; sections 6, 7, 8,
  11 and the header brought in line (the "clean run is not made" statements). No model call, no real key, no
  paid call, no code changed, no snapshot changed. I did not view the failure page (I read its wording in
  `backend/services/runs.py` and the audit log). `*verify-change` and the `@security.eng` recommendation are
  **still not made**: B8 is not finished and review B is to come.
- 2026-11-24 · persona `qa-eng` · action `qa` + `log-defects` (H-088 follow-up: section 12.6, review B, and F-6) · read-only: `data/app.db` (SHA-1 `eef1bba4…`) and `data/spike.db` opened with `mode=ro`. Every figure in `@backend.eng`'s two H-088 updates re-read from the database and **all matched** (16 requests, 5 / 6 / 5 by role, US$0.0355, 41 of 70, 18 entries, the flags, the judge verdicts); added: stage times (25 s and 24 s), the real-call count (40), the entry count per obligation, and the point that review B's judge verdicts repeat review A's. No model call, no real key, no paid call, no code changed. I did not view any page. `*verify-change` and the `@security.eng` recommendation are still not made.
