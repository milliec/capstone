# Spike report: the first real model calls (B3 spike, reported under B8)

Owner: `@qa.eng`. Handoff H-077. Written 2026-11-23 on branch `qa-eng/h077-spike-report`.
`AAMAD_TARGET_RUNTIME=crewai`, `AGENTS_MODE=stand_in` while writing: **I made no model call, used no key and
sent nothing.** Every number below was read from `data/spike.db` and `data/app.db` (opened read-only; their
hashes were the same before and after) and from the read-only `--tally`.

**Status: interim.** The spike is not finished. The operator's one real clean run through the web app
(DL-55 keeps it in the plan) **has not been made**: `data/app.db` holds 0 real calls. This report covers the
6 trace lines made so far. When the clean run is made, it needs its own section here (see Open Questions).

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
- **Stage time limits (375 s, 150 s, 30 s) were not measured.** They stay at the SAD's starting values as the
  operator's decision (DL-55). My reading from the per-call figures is that Stage A is about 5 extractions
  and 7 verifications (roughly a minute) and Stage B about 6 judge calls (roughly 25 s). **These are
  estimates from per-call figures, not measured stage times**, and the units run one after another (DL-56).
- **EC-010 (under 5 minutes) and EC-012 (under US$2) are not measured by this spike.** They are
  whole-run figures; the graders for them exist (`qa.md`) but no real run has been graded yet.

## 7. Known limits (stated, not hidden)

1. **The verifier is measured on one planted conflict, C-1, in one valid run.** C-2 and I-1 were never sent to
   it. The first test of them on the verifier is the evaluation cycle, where a miss is reported as it
   stands; changing the model afterwards needs a recorded operator decision (DL-55).
2. **The verifier's false-alarm rate is unmeasured.** No OK-1 run exists.
3. **The extractor was tried on one document of five** (the same one twice), and **the judge on one row of
   the six that reach it**, with only the `applies` verdict seen. **No real model has produced an
   `unsure` or `does_not_apply` verdict.** The real extractor **split one rule in two** (3 rows against the
   key's 2 on `SRC-UCILAW`). That is a finding for EC-001 and EC-002, not a defect in the build.
4. **No per-role figures from five runs exist**, so none of the stage limits is "set from measurement".
5. **The verifier was not compared with another model**, and the bake-off tooling (`--case`, `--tally`) was
   built but not run. It is optional future work and needs a new operator decision.
6. **Two calls to one role are not a distribution.** Every "mean" in this report is a mean of 1 or 2 values.

## 8. Not tested (kept apart from passed)

- The bake-off (DL-26; dropped, DL-55) and the five runs each for the extractor and the judge (skipped).
- C-2, I-1 and OK-1 on the verifier; the extractor on four of the five documents; the judge on five of six rows.
- A **real clean run through the web app**, start to finish (not made yet).
- Stage times, whole-run cost and EC-010 and EC-012 on a real run.
- Quality of any real answer beyond the three checks above (C-1 caught; judge verdict correct).
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

## 11. Future work (deferred tests, in order)

1. The operator's one real clean run through the web app, then a section 12 here with its calls, times and cost.
2. The evaluation cycle (B8, B9): C-2, I-1, OK-1 on the verifier; `unsure` and `does_not_apply` on the
   judge; EC-010 and EC-012 on a real run; the stage times measured, with the limits then reviewed.
3. Optional, new decision needed: the bake-off tooling that already exists.

## Sources

`handoffs.md` H-077, H-076, H-078, H-079, H-083; `sad.md` Measurement spike, DL-26, DL-36, DL-40, DL-43,
DL-55, DL-56, EC-R10; `backend.md` "B3 spike finding", "finding 2", "finding 3" and "what is waived";
`data/spike.db` (6 trace lines) and `data/app.db` (0 real calls), read-only; `--tally` and
`--tally --exclude 'SRC-UCILAW-P3#1'`; `backend/runtime/spike_tally.py` (to find D-1).

## Assumptions

- The operator's decisions of 2026-11-23 stand (DL-55): no bake-off, no five-run figures, limits kept.
- "Valid" means the answer passed the schema and our checks (CR-003, D5); "CAUGHT" and "CORRECT" are
  judged against the answer key, as the tally does.
- Per-call figures are read from trace lines 2 to 6; line 1 is excluded from any model-call figure.

## Open Questions

1. When the operator makes the clean run, should its lines be reported here or in the evaluation report? I
   assume here, as section 12, because it still counts toward the 70 and is labelled `spike`.
2. Should D-1 be fixed in `spike_tally.py`, or left as a documented reading caution? `@backend.eng` owns it.
3. `sad.md` says the spike's output is "named in this document's Audit when it exists". That is
   `@system.arch`'s file, so I raised a handoff rather than edit it.

## Audit

- 2026-11-23 · persona `qa-eng` · action `qa` + `log-defects` + `future-work` (H-077, the spike report) ·
  `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · read-only: `data/spike.db` and `data/app.db` hashes
  unchanged, `--tally` only. No model call, no real key, no paid call, no code changed, no snapshot changed.
  Interim report on 6 trace lines; the real clean run is not made. `*verify-change` and the
  `@security.eng` recommendation are **not** made: B8 is not finished.
