# Integration build spec: one vertical path (button → API → crews → result or clear error)

Owner: `@integration.eng`. Written 2026-11-24 on branch `integration-eng/build-spec`.
`AAMAD_TARGET_RUNTIME=crewai`, `AGENTS_MODE=stand_in` while writing. **I wrote no code, made no model call,
used no key, and did not open `data/spike.db` or `data/app.db`.** Every fact below was read from the code or
from `sad.md`, `backend.md`, `setup.md`, `scaffold-plan.md` and `spike-report.md`.

**Status: DECIDED by the operator on 2026-11-24 (section 8). Documentation only: nothing is built yet.**
Two fixes are approved: **P-3** (a stuck review on an uncaught error, E-11) and **P-5** (the 70-call cap in the web
path). Everything else is **parked as future work** with an ID (`IFW-1` to `IFW-6`, section 7). Both fixes need
two **new failure reasons** first, so they wait for `@system.arch` (handoff H-092) before `@backend.eng` builds
(handoff H-091). Tested with the fake OpenAI only: **no real call.**

## 0. What I found first (read this before the rest)

Four things in the request do not match the repository. The spec below follows what the repository does.

1. **There is no `startRun` function and no JSON API.** The app is server-rendered: the button is a form post.
   What the request calls *startRun* is `runs.start_run(...)` behind **`POST /specialist/runs`**, which answers
   with a redirect to **`GET /specialist/runs/{run_id}`**, a page that reloads itself every 3 seconds while a
   stage runs. I read "the Week 3 contract" as the **Sprint 3 stand-in slice** (setup.md: "Sprint 3 is treated
   as done at the stand-in bar") and reuse that. **I add no second shape and no new endpoint** (section 3).
2. **Most of this path already exists and has run for real.** The three real runs in `spike-report.md` §12
   (`RUN-20261123-1`, `-20261124-1`, `-20261124-2`) went through this same button, API and crews. So this
   sprint **proves and hardens the path; it does not build a new one.** The work left is two fixes (item 4).
3. **The real-call budget is nearly spent.** `spike` has a cap of 70 real calls and **58 are used** (spike-report
   §12.7). A whole run needs about 17. **Decided (D-1): no new real run. `RUN-20261124-2` is the proof** that the
   real crews work through this path: it completed and published a 22-entry calendar. It is **one run, not graded,
   with four cautions** (spike-report §12.7). I have not re-read its log; the logging pass test in section 6 has
   not been applied to it.
4. **Two gaps, found by reading the code, not yet reproduced:**
   (a) if a real-mode stage meets a problem our code does not catch, the review can be left on "AI is drafting
   the rules" for good (section 4, row E-11);
   (b) **the web app never calls the real-call cap check** (`harness.check_call_allowed` has no caller outside
   its own file; I searched `backend/`). The 70-call (`spike`) and 60-call (`tuning`) caps are enforced by the
   spike command only. A real review started from the web page under those activities is stopped by the
   US$2.50 per-review cap, **not by the call cap**. Today the 58 of 70 is kept by discipline, not by the app
   (section 3.4, P-5).

## 1. Scenario

**One workflow: one review of the demo fund `FND-DEMO-01`, from "Start a new review" to the calendar the GP sees**,
on the same Sprint 3 slice, with the demo rule off and the failure demo off.

| Step | Who | What happens | Crew or code | Result the screen shows |
|---|---|---|---|---|
| Start | Specialist | Clicks **Start a new review** on Filing rules | none | Review page, "AI is drafting the rules" |
| Stage A | System | One extractor per primary document (5), then one verifier per drafted rule (6, or 7 with the demo rule) and the quote check | **Extractor crew, verifier crew** (CrewAI, one agent each); quote check is code | Units fill in one by one; then "Your turn: check the rules" |
| **G1** | Specialist | Approves or rejects each rule | none (human) | Rules page |
| Stage B | System | One judge per approved rule | **Judge crew** | "Your turn: confirm what applies" |
| **G2** | Specialist | Confirms, overrides, or decides each "unsure" | none (human) | Confirm page |
| Stage C | System | Dates worked out | **Code only** (no model may compute a date) | "Your turn: publish the calendar" |
| **G3** | Specialist | Publishes (or declines) | none (human) | Published; the GP sees the calendar |

**The vertical path under test** is *Start → Stage A → G1* (the first crew result reaching a person). Stages B
and C use the same mechanism, so they are checked the same way, not designed again. **Real crews are used on
every model step.** The only stand-in allowed is the whole-review stand-in mode, which is chosen when the review
starts, is fixed for that review, and is labelled "Stand-in agents" on every page about it (CR-030). **There is
no automatic fallback from real to stand-in when a call fails** (SAD: fail closed). A review that cannot reach
the model **ends as Failed with a reason** (section 4). I recommend keeping it that way: a silent fallback would
show fixed test answers as if the model had worked.

## 2. Pattern: which way the screen learns that the result is ready

### 2.1 How to time one stand-in run (PARKED as `IFW-4`: decided not to run it, D-4)

*Kept for later; nobody needs to run it now. It costs nothing and calls no model.*

**What this measures, honestly:** a stand-in step waits `STAND_IN_UNIT_PAUSE_S` (default 1 s) per unit, so its
times are the **plumbing** (the page reloads, the database, the hand-over between stages), **not model speed.**
Model speed comes from the real runs already in `spike-report.md` §12 and from the next real run. Both are used
in 2.2.

1. In a terminal, from the project folder, start a **separate** app on port 8001 with its own scratch database
   (so `data/app.db` and `data/spike.db` stay untouched; `data/` is git-ignored):
   ```bash
   DATABASE_PATH=data/timing-run.db AGENTS_MODE=stand_in STAND_IN_UNIT_PAUSE_S=1 \
     .venv/bin/python -m uvicorn backend.main:create_app --factory --port 8001
   ```
2. Open `http://localhost:8001`, sign in as the specialist, and leave both switches **unticked**.
3. Start a stopwatch the moment you click **Start a new review**. Stop it when the page first reads
   "Your turn: check the rules". Write the number down: **felt wait, stage A.**
4. Do the gates as the README's demo path does (approve every rule, confirm every verdict, publish). Do the same
   for stage B (stopwatch from completing G1 to "Your turn: confirm what applies") and stage C. Write each down.
5. Stop the app (Ctrl+C). Print the **machine's own clock**, read-only:
   ```bash
   sqlite3 -readonly data/timing-run.db "
   SELECT at, actor, event_type, reason FROM audit_log
   WHERE run_id = (SELECT run_id FROM runs ORDER BY rowid DESC LIMIT 1)
     AND (event_type = 'gate_event' OR reason LIKE 'Stage % finished%')
   ORDER BY audit_id;
   SELECT step, COUNT(*) AS calls, ROUND(SUM(duration_ms)/1000.0, 1) AS seconds
   FROM trace WHERE run_id = (SELECT run_id FROM runs ORDER BY rowid DESC LIMIT 1) GROUP BY step;"
   ```
   **Server time per stage** = the "Stage X finished (stand-in)" line minus the line just before it ("Review
   started", then each gate completion). **Reload lag** = your felt wait minus the server time (it is between 0
   and 3 s, because the page reloads every 3 s).
6. Optional second run with `STAND_IN_UNIT_PAUSE_S=0` to see the plumbing alone.
7. Send me the three felt waits, the printout, and the number from the second query.
   (I checked that both queries run against the schema; I did not run them on any data.)

### 2.2 Choosing the pattern

| Pattern | What it is here | Fits when | Cost |
|---|---|---|---|
| **REST wait** | The Start click does not return until the stage is done | A stage takes under ~10 s | Browser and form hold open; no progress; a 375 s stage limit makes no sense with it. **Rejected:** even a stand-in stage A takes 11 to 12 s |
| **Polling** (what exists) | Page reloads every 3 s while `is_working`; "Refresh now" and "Stop automatic refresh" links | A stage takes seconds to a few minutes | None new. No script, no open connection. Reload flicker; up to 3 s of lag |
| **SSE** | Server pushes unit updates over one open connection | Stages over ~1 to 2 min, or reload flicker is a real problem | A script, an open connection, a SAD edit (SAD §4 chose "no script") |
| **WebSocket** | Two-way open connection | A reviewer must send messages mid-stage | Never needed: the reviewer cannot act while a stage runs (`RUN_STAGE_RUNNING`) |

**Decided (D-4): polling stays.** It is chosen on timings already on file (real runs, `spike-report.md` §12):
stage A 25 to 30 s, stage B about 24 s, stage C under 1 s, all model calls together 47 to 53 s, against limits of
375, 150 and 30 s. **No code changes.** The rule for revisiting it: move to SSE only if a stage goes over about
2 minutes **or** a person who watches a run says the reloads are a problem, and then only after a SAD edit.

**Known limit KL-1 (recorded, not fixed).** The choice rests on **real-run times only**. I did **not** time a
stand-in run, so the page-reload plumbing and the **reload lag (0 to 3 s, because the page reloads every 3 s)**
are stated, not measured. Three runs gave only two or three values per stage, so the times are a guide, not a
distribution.

## 3. Contract (reused exactly; nothing renamed)

### 3.1 Endpoints used on this path

| Call | Who | Sends | Answers |
|---|---|---|---|
| `POST /specialist/runs` | specialist | Form: `demo_planted_row` (off), `demo_fail_step1` (only in stand-in mode; off) | **303 → `/specialist/runs/{run_id}`**. A refusal shows the page again with the message (`RUN_ACTIVE`; `VALIDATION`) |
| `GET /specialist/runs/{run_id}` | specialist | none | The review status page (the "result" below). Reloads every 3 s only while `is_working` |
| `GET /specialist/runs/{run_id}/g1` · `/g2` · `/g3` | specialist | none | The gate pages |
| `POST /specialist/rows/{row_id}/decision` · `.../verdicts/{verdict_id}/decision` | specialist | Decision fields (SAD §4) | Redirect; or a refusal message |
| `POST /specialist/runs/{run_id}/g1/complete` · `/g2/complete` | specialist | `run_version` | Starts stage B or C |
| `POST /specialist/calendars/{calendar_id}/publish` | specialist | `run_version` and the two lists | The calendar is published |
| `GET /calendar` | GP, specialist | none | The published calendar |
| `GET /health` | none | none | Start-up check |

`POST /specialist/runs/{run_id}/abandon` exists and is **not** part of this path. `retry` is a stub (B13b) and is
out of scope (section 7).

### 3.2 Status values (as built, unchanged)

| Field | Values |
|---|---|
| `status` | `ACTIVE`, `FAILED`, `ABANDONED`, `DECLINED`, `COMPLETED` |
| `phase` | `A_RUNNING`, `AT_G1`, `B_RUNNING`, `AT_G2`, `C_RUNNING`, `AT_G3` (keeps its last value after the run ends) |
| unit `status` | `waiting`, `running`, `done`, `failed` |
| unit `failure_reason` | `model service`, `stage time limit`, `invalid output`, `cost cap`, `service restarted`, `calendar generation`, `demo failure` |
| `agents_mode` | `stand_in`, `real` (fixed when the run starts) |

### 3.3 Result shape (the review status view fields, H-036 V-1 to V-10, unchanged)

`run_id`, `review_number`, `status`, `phase`, `status_words`, `status_tone`, `workflow_state`, `is_working`,
`is_at_gate`, `run_version`, `agents_mode`, `cost_so_far`, `started_by_label`, `started_at`, `steps[4]`
(`state`, `href`, `current`), `counts` (`rules`, `unsure`, `dates`), `ended`, `published_at`,
`failure` (`step`, `step_name`, `unit_label`, `reason_sentence`), `ended_because`; plus the unit list
(`unit_id`, `label`, `status`, `group`, `failure_reason`). The page shows these values as sent and never works
anything out itself.

### 3.4 Changes to the contract: decided 2026-11-24 (D-2)

**Approved (two):**

| # | Change | Why | Touches |
|---|---|---|---|
| P-3 | **Catch any unexpected error in a running stage and end the review as Failed** with a new reason `unexpected error` (E-11) | So no stage can hang on "AI is drafting the rules" | `runs.failure_reason` and the `units.failure_reason` `CHECK` get a new value; `FAILURE_SENTENCES` gets its sentence. **SAD edit first** (H-092), then `@backend.eng` (H-091) |
| P-5 | **Check the real-call cap before each real call from the web app** (`harness.count_real_calls`, counted across `data/spike.db` **and** the app's database, as the spike command does), and end the review as Failed with a new reason `call limit` | Today only the spike command stops at the cap | Same two places as P-3; one check in `stages._run_unit`, real mode only. The pinned US$2.50 cap does not change |

**New failure reasons (D-3: new wording, not a reuse).** The sentences follow the built style (no final full stop).
They are **proposed text**: `@system.arch` records them and `@ux.designer` owns the sentence table (ux.md page 3).

| Reason (stored) | Sentence on the review page |
|---|---|
| `unexpected error` | Something went wrong that the app did not expect, so this step was stopped and nothing from it was saved |
| `call limit` | The limit on real model calls for this kind of review was reached, so no further call was made |

For `unexpected error`, the audit entry records **the error's class name only**, never its message: a provider or
prompt error can carry text that must not be stored or shown. The review page says nothing about the cause beyond
the sentence above.

**Parked as future work (not built, IDs in section 7):**

| Was | ID | Change |
|---|---|---|
| P-1 | `IFW-1` | A visible **"Real agents"** tag beside "Stand-in agents" |
| P-2 | `IFW-2` | **Refuse to start** a real-mode review when a model ID or the key is missing. **Why parking it is safe:** with P-3 a missing setting now ends the review as **Failed with a sentence**, not a hang |
| P-4 | `IFW-3` | A written "accepted / rejected" helper for the trace. The derived word and the query stay in section 6 as documentation only |

**No new endpoint, no new status value and no new result field.** A failed review still shows the same fields; only
`failure.reason_sentence` can now read one of two new sentences.

## 4. Errors and timeouts: what the screen shows

Every row below is a state the review page already knows how to show, except E-10, E-11 and E-12. **A failed
review always shows the step, the unit and a sentence, and the way forward is "Start a new review from Filing
rules"** (Retry is B13b). No gate opens after a failure. Sentences are the built ones (`FAILURE_SENTENCES`).

| # | What goes wrong | Where it is caught | The screen shows | Built? |
|---|---|---|---|---|
| E-1 | Start while a review is active | `start_run` (`RUN_ACTIVE`) | The page again, a message naming the active review and a link to it | Yes |
| E-2 | Failure demo asked for in real mode | `start_run` (`VALIDATION`) | The page again with a plain message. The checkbox is not shown in real mode, so a person cannot reach it | Yes |
| E-3 | A model call times out, is rate-limited (429) or the provider errors (5xx) | `crews.run_step`: **one** retry (DL-43), then final | **Failed:** "The model service did not answer in time, or returned an error, twice", with step 1, 2 or 3 and the unit's name | Yes |
| E-4 | The model answers in the wrong shape, or fails a guardrail | `agents._real_call` → "invalid output". **Never asked again** (D5) | **Failed:** "The AI returned output in the wrong format, so it was not used" | Yes |
| E-5 | A stage runs past its limit (A 375 s, B 150 s, C 30 s) | The backend's own timer | **Failed:** "This step took longer than its time limit". A late answer goes to the trace only; its cost counts | Yes |
| E-6 | The review reaches US$2.50 | Checked before every call | **Failed:** "The review reached its cost limit of US$2.50". **Cannot be retried** (DL-51). A warning shows from US$2 | Yes |
| E-7 | The app restarts while a stage runs | Start-up check | **Failed:** "The application restarted while AI was working" | Yes |
| E-8 | The dates cannot be made into one calendar | Stage C | **Failed:** "The dates could not be worked out into one complete calendar" | Yes |
| E-9 | The failure demo (stand-in only) | Stage A, first unit | **Failed:** the demo sentence, which says nothing else went wrong | Yes |
| E-10 | The server is not running while the page reloads | The browser | **The browser's own "can't connect" page. The app cannot show anything here.** Accepted for the MVP (one local user, one run). Stated, not fixed | Limit, stated |
| E-11 | **Something unexpected inside a running stage**, such as a missing model ID or key in real mode (`ModelNotSet`, `KeyNotSet`) | **Not caught.** `stages._run_unit` handles only the listed failures, and `run_stage` cancels its timer in `finally`, so the stage ends with the review still `A_RUNNING` | **The review sits on "AI is drafting the rules" and keeps reloading until the app restarts** (then E-7). This is the nearest thing to a "blank screen" on the path | **Gap. Fixed by P-3 (approved)** |
| E-12 | An unexpected error while a page is built | `main.py` handler | The plain error page with the sentence for the signed-in role, never the error's details | Yes |

**Reproducing E-11 without any paid call:** with real mode set and the model ID left empty, start a review
against the **fake OpenAI** already used by the tests (`tests/fake_openai.py`). If the review stays on A_RUNNING,
the gap is real. That is the first test in handoff H-091, written to fail before the fix.

**E-3 to E-9 are not re-tested here.** Existing tests already drive the real CrewAI crews against the fake OpenAI
(`tests/fake_openai.py`); I have not re-checked their coverage against this table (`IFW-6`). **No real call is
made for any of this work.**

## 5. Where the human gates sit on this path

The model never decides. **G1 is the first gate on this path.** G2 and G3 behave the same way on their own pages.

**G1 (after stage A), `/specialist/runs/{run_id}/g1`.** The reviewer sees, for **every** rule, in this order:
the **quote** → the **quote check** (passed, or failed with why; shown on every row, the demo row included) → the
**paragraph** it cites → the **checker flags** → the fields they must set → the decision. Above the rules: the
summary counts (rules, flags) and the **coverage view** (loaded paragraphs no rule cites).

| The reviewer sees | Why it is shown |
|---|---|
| Inputs: the quote and its paragraph (from the five primary documents) | So they can judge the rule against its source, not against the model's word |
| Output: each drafted rule's fields | The thing being approved |
| **Why flagged:** "Flagged by the AI checker: two sources disagree" or "inside the same document", with **both texts** | The checker points out disagreements but never settles them; the specialist does |
| A failed quote check | Approval is **refused** for that rule |

Rules the server enforces here (not the page): a failed quote check → approval refused; a remaining flag →
a written reason is required to approve; a business-day rule must be chosen; "who files" must be chosen when the
source is silent; nothing is preselected; a rule is decided once; the demo rule can only be rejected. **If stage
A failed (section 4), G1 never opens**, so no half-checked rule can be approved.

## 6. Logging: what is recorded for every step

**The trace already has most of it, one line per HTTP request, append-only** (`trace` table, CR-018). It is
written for stand-in and real runs; a stand-in line has an empty model and zero tokens.

| What you asked for | Where it is today | Gap |
|---|---|---|
| **Run id on every step** | `trace.run_id`, `audit_log.run_id`, `units.run_id` on every row | None for the database. **To check (do not assume):** whether the app's own process log (`data/`, SAD §5) carries the run id on each stage event. If not, the audit log and trace are the record and no new log is added |
| **Model** | `trace.model` (asked) and `trace.model_returned` (what the API said) | None |
| **Tokens in / out** | `trace.tokens_in`, `trace.tokens_out` (cost: `cost_usd`; `cost_estimated` = 1 when no usage came back) | None |
| **Latency** | `trace.duration_ms` per request; `trace.at` = start | None. The stage's own time is the audit lines "Review started" and "Stage X finished" |
| **Stop reason** | `trace.stop_reason` (`stop`, `length`, empty when no answer); `provider_error` says why a request got none | None |
| **Accepted / rejected** | Two meanings, both kept apart. **(a) Our checks:** `parsed_output` set = accepted; `validation_error` set = rejected; `late` = 1 = arrived too late and not stored. **(b) The person:** `row_decisions` and `verdict_decisions` (approve, reject, confirm, override) and the `audit_log` | **(a) is derived, not a column** (P-4). I propose no schema change. **(b)** is complete |

**Run-by-run check query (read-only), so a person can read one run's log without a developer:**
```bash
sqlite3 -readonly data/app.db "
SELECT run_id, step, unit_id, attempt_n, model_returned, tokens_in, tokens_out, duration_ms, stop_reason,
  CASE WHEN late = 1 THEN 'late' WHEN validation_error IS NOT NULL THEN 'rejected'
       WHEN parsed_output IS NOT NULL THEN 'accepted' ELSE 'no answer' END AS output_check
FROM trace WHERE run_id = 'RUN-…' ORDER BY trace_id;"
```
(I checked it parses against the schema. I did not run it on `app.db`.) The planned trace export (D4, `@qa.eng`)
would replace this query; I do not build it.

**Pass test for logging on this path:** after one run, every line of the query above has a run id and a step;
every real line has `model_returned`, both token counts, a latency and a stop reason; every line with no answer
has a `provider_error`; and the audit log has one entry per start, per stage end, per gate event and per refusal.

## 7. Out of scope for this sprint

- **Retry** (B13b). A failed review is followed by a new review.
- **SSE and WebSockets** (section 2.2, KL-1).
- **Any JSON API, new endpoint, new status value or new result field.**
- **An automatic fallback from real to stand-in.**
- **A second provider, a bake-off or any model other than the three pinned** (DL-55).
- **The evaluation run and its report** (B8, B9), the trace export (D4), the three-run comparison.
- **Hosted deploy** and anything in Appendix A or the parked F-IDs (CLAUDE.md).
- **Changing `docs/architecture-decisions-summary.html`** (frozen).
- **Changing the pinned model settings, prompts, call timeouts or the US$2.50 cap.**
- **Any real model call by this work.** No new real run (D-1); tests use the fake OpenAI only.

**Parked as future work (D-2, D-4), none of it built:**

| ID | What | Source |
|---|---|---|
| `IFW-1` | "Real agents" tag beside "Stand-in agents" (`@frontend.eng`; snapshots would change, so you approve them) | was P-1 |
| `IFW-2` | Refuse to start a real-mode review when a model ID or the key is missing (existing `VALIDATION` refusal) | was P-2 |
| `IFW-3` | A written accepted / rejected helper for the trace (documentation only; the query is in section 6) | was P-4 |
| `IFW-4` | The timed stand-in run in 2.1, to measure the page-reload plumbing and lag (KL-1) | D-4 |
| `IFW-5` | Check whether the app's own process log carries the run id on each stage event (section 6) | Open question 2 |
| `IFW-6` | Check that the existing tests cover E-3 to E-9 with the real crews against the fake OpenAI | section 4 |

## 8. Decisions (operator, 2026-11-24) and what happens next

| # | Decision | Recorded as |
|---|---|---|
| D-1 | **No new real run.** `RUN-20261124-2` is the proof | Section 0, item 3. Not recorded in `decision-log.md` here: that file is `@system.arch`'s |
| D-2 | **Approve only the fixes for E-11 and the 70-call cap in the web path** (P-3, P-5). Park the rest with IDs | Section 3.4 and the table in section 7 (`IFW-1` to `IFW-3`) |
| D-3 | **New wording** for the two new failure reasons | Section 3.4: `unexpected error`, `call limit` |
| D-4 | **Skip the timed run; polling stays**, on existing timings, recorded as a known limit | Section 2.2 (KL-1) and `IFW-4` |

**What happens next, in order (each its own pull request; nothing here is merged by `@integration.eng`):**
1. **H-092** to `@system.arch`: record the two new failure reasons in `sad.md` (the run-state failure rows, the
   reason list and the `units.failure_reason` values), and say so to `@ux.designer` for the sentence table.
   **`@backend.eng` does not start before this is done** (CLAUDE.md: a SAD edit comes first).
2. **H-091** to `@backend.eng`: the two fixes, with their tests, **against the fake OpenAI only.**
3. `*sync-docs` after the code change, with the operator's approval before it writes.

## 9. Proposal: how an existing database gets the two new failure reasons (for H-091, step 3)

**Status: PROPOSED, tested on a copy. Nothing in `backend/` is changed and neither real database was opened for
writing.** It waits for H-092 (the reasons are recorded in the SAD first) and for the operator's approval.

### 9.1 The problem

`units.failure_reason` carries a `CHECK` that lists the seven reasons. `CREATE TABLE IF NOT EXISTS` leaves an
existing table alone, so a database made before the change would **refuse** `unexpected error` and `call limit`
with an integrity error, exactly when a review is already failing. SQLite cannot alter a `CHECK` with `ALTER
TABLE`. The code already has one precedent for an old database (`TRACE_ADDED_COLUMNS` in
`backend/db/connection.py`), but it only **adds columns**; it cannot change a `CHECK`.

### 9.2 What I tested, and on what

Both on **copies** of a read-only backup of the real app database (made with `sqlite3 -readonly ... ".backup"`),
in the scratchpad, outside the repository. **Before and after, `data/app.db` and `data/spike.db` had the same
SHA-1** (`29068e84…` and `32376900…`, the values `@qa.eng` records). The copy holds 9 reviews, 93 units, 52 trace
lines and 153 audit entries. For each way I compared the row count and a content digest of every table, the
triggers, `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, whether the new values are accepted and a wrong one
still refused, and what a second run does.

| | **A. Rewrite the stored table text** (SQLite's documented way to *loosen* a `CHECK`) | **B. Rebuild the table** (new table, copy, drop, rename) |
|---|---|---|
| Result on the copy | **Passed.** Every table's content, the 93 unit rows **with their row numbers**, and the 4 triggers unchanged. Integrity `ok`, 0 foreign-key problems. Both new reasons accepted; `banana` refused. Second run: "nothing to do" | **Passed**, same checks |
| Touches the data rows? | **No.** Only the table's definition changes | **Yes**, every `units` row is copied. Pages and stages read units `ORDER BY rowid`, so a copy that renumbers rows could reorder them (it did not here, because the numbers had no gaps) |
| Stored table text afterwards | **Identical to a database made fresh from the updated `schema.sql`** (checked with a diff) | Differs in one cosmetic way: `CREATE TABLE "units"` (quoted name) instead of `CREATE TABLE units` |
| Needs | `PRAGMA writable_schema`, which a **defensive** SQLite build **refuses** ("table sqlite_master may not be modified"; I tested this, it fails cleanly and nothing changes) | Nothing special; works in defensive builds |
| Risk | Low for data, but it is the "dangerous-looking" pragma. Guarded by an exact-text check (below) | Larger blast radius: a bug here loses or reorders rows |

### 9.3 Recommendation

**Use A, with B as the fallback only when the build refuses A.** A leaves every row alone, so the evidence in the
real runs cannot be disturbed, and it makes an old database look exactly like a new one.

1. **A new function `upgrade_failure_reasons(conn)`** in `backend/db/connection.py`, **called from
   `create_app` in `backend/main.py` only, not from `init_db`.** Reason: `init_db` is also called by the spike
   runner on `data/spike.db` (`spike.py` line 176), so putting it there would **change `spike.db` the next time the
   spike runs**. The spike never writes the new reasons, so `spike.db` keeps the old list on purpose and is never
   migrated.
2. **Guards, in this order:** if the stored `units` text already contains `'call limit'`, do nothing. If it does
   **not** contain `'demo failure')` exactly once, **stop and refuse to start** with a plain message (the table is
   not what was expected; nothing is changed). Otherwise run A inside one `BEGIN IMMEDIATE` transaction, raising
   `schema_version` by one, using `sqlite_master` (works on every SQLite; `sqlite_schema` needs 3.33 or later).
3. **If A is refused** (a defensive build), run B in one transaction with `PRAGMA foreign_keys = OFF`, copying
   `ORDER BY rowid`, then `PRAGMA foreign_key_check` must be empty before `COMMIT`, and `foreign_keys` goes back on.
4. **`schema.sql` gets the same two values** on the same line, so a new database and a migrated one match.
5. **It runs at start-up, before any request**, so nothing else holds the database. It is idempotent, so
   `make run --reload` can repeat it.

### 9.4 What the operator does and what changes

- **One visible change:** the first start of the app on the new code changes `data/app.db`'s **file hash** (the
  schema, not the data). `@qa.eng` watches that hash, so the handoff tells them the new baseline **and that the
  row contents are unchanged** (compare table digests, as above).
- **Before that first start, take a backup, read-only, by choice:** `sqlite3 -readonly data/app.db ".backup
  'data/app-before-reasons.db'"` (`data/` is git-ignored). I propose it as a step for you, **not** as something the
  app does by itself.
- **Fallback if you would rather not migrate the real evidence at all:** start a fresh database
  (`DATABASE_PATH=data/app-2.db`) and keep `data/app.db` read-only for `@qa.eng`. Cost: the new database's
  Filing rules list starts empty.

### 9.5 Tests for the migration (Tier 1, temporary files only, added to H-091)

Build an old-style database (seven reasons) in a temporary file, then: (a) the upgrade adds both reasons, a wrong
one is still refused, and every table's rows and the unit row numbers are unchanged; (b) a second run changes
nothing; (c) the stored text equals a database made from the new `schema.sql`; (d) a table that is **not** what was
expected is refused and left as it was; (e) with SQLite's defensive setting on, B is used and passes (a) to (c);
(f) **`init_db` on a spike-style database does not change `units`** (so `spike.db` stays as it is). The existing
`test_attempt_trace.py` trace-column test is the pattern to follow.

## Sources

`sad.md` (§4 routes, run states, failure reasons, CR-017, CR-023, CR-030), `setup.md`, `scaffold-plan.md`,
`spike-report.md` §12, `backend.md`; code read for facts: `backend/web/routes/runs.py`,
`backend/services/runs.py`, `backend/runtime/stages.py`, `crews.py`, `agents.py`, `model_settings.py`,
`harness.py`, `backend/db/schema.sql`, `backend/main.py`, the review status and G1 templates,
`tests/fake_openai.py`.

## Assumptions

- "The Week 3 contract" means the Sprint 3 stand-in slice, and "`startRun`" means `runs.start_run` behind
  `POST /specialist/runs`. **If you meant something else, tell me before anything is built** (section 0).
- "Real crews" means the CrewAI crews. **No new real run** (D-1): the proof is `RUN-20261124-2`; error paths and
  the two fixes use the same crews against the fake OpenAI.
- "Accepted / rejected" in the log means both: our checks on the model's output, and the person's decision at a gate.
- "Same sprint 3 slice" means the demo fund, the demo documents, the demo rule off and the failure demo off.

## Open Questions

1. **How does an existing `data/app.db` get the two new reasons?** Proposed and tested on a copy: section 9.
   **The operator still has to approve it,** and decide whether the real `data/app.db` is migrated (section 9.4) or
   kept as it is with a fresh database started beside it. Neither real database has been touched.
2. Is E-11 reproduced? I read it in the code; the first test in H-091 settles it.
3. `IFW-5` (process log) and `IFW-6` (test coverage) are open and parked.

## Audit

- 2026-11-24 · persona `integration-eng` · action `log-integration` · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · created this file: the build spec for one
  vertical path. **Documentation only; no code, no model call, no key, `data/spike.db` and `data/app.db` not opened.**
  Read: `backend/web/routes/runs.py`, `backend/services/runs.py`, `backend/runtime/stages.py`, `crews.py`,
  `agents.py`, `model_settings.py`, `harness.py`, `backend/db/schema.sql`, `backend/main.py`, the review status
  and G1 templates, `sad.md`, `setup.md`, `scaffold-plan.md`, `spike-report.md`. Queries in sections 2.1 and 6 were
  checked for syntax against an empty in-memory copy of the schema only.
- 2026-11-24 · persona `integration-eng` · action `log-integration` · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · recorded the operator's decisions D-1 to D-4: no new real run (`RUN-20261124-2` is the proof); P-3 and P-5 approved; P-1, P-2, P-4 parked as `IFW-1` to `IFW-3`; new failure-reason wording proposed; polling stays with known limit KL-1; the timed run parked as `IFW-4`. Raised H-091 (`@backend.eng`) and H-092 (`@system.arch`). **Documentation only; no code, no model call, no key; `data/spike.db` and `data/app.db` not opened.**
- 2026-11-24 · persona `integration-eng` · action `log-integration` · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · added section 9, the proposal for how an existing database gets the two new failure reasons, **tested on copies only** (a read-only `.backup` of `data/app.db`, in the scratchpad, outside the repository). `data/app.db` (`29068e84…`) and `data/spike.db` (`32376900…`) had the same SHA-1 before and after, and were opened read-only. **Documentation only; no change in `backend/`, no model call, no key.**
