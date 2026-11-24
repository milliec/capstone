# Integration build spec: one vertical path (button → API → crews → result or clear error)

Owner: `@integration.eng`. Written 2026-11-24 on branch `integration-eng/build-spec`.
`AAMAD_TARGET_RUNTIME=crewai`, `AGENTS_MODE=stand_in` while writing. **I wrote no code, made no model call,
used no key, and did not open `data/spike.db` or `data/app.db`.** Every fact below was read from the code or
from `sad.md`, `backend.md`, `setup.md`, `scaffold-plan.md` and `spike-report.md`.

**Status: PROPOSED. Nothing is built from this until the operator approves it.** Sections 3 and 4 list the
changes I propose; each one that touches the contract or the SAD is marked and waits for `@system.arch`.

## 0. What I found first (read this before the rest)

Four things in the request do not match the repository. The spec below follows what the repository does.

1. **There is no `startRun` function and no JSON API.** The app is server-rendered: the button is a form post.
   What the request calls *startRun* is `runs.start_run(...)` behind **`POST /specialist/runs`**, which answers
   with a redirect to **`GET /specialist/runs/{run_id}`**, a page that reloads itself every 3 seconds while a
   stage runs. I read "the Week 3 contract" as the **Sprint 3 stand-in slice** (setup.md: "Sprint 3 is treated
   as done at the stand-in bar") and reuse that. **I add no second shape and no new endpoint** (section 3).
2. **Most of this path already exists and has run for real.** The three real runs in `spike-report.md` §12
   (`RUN-20261123-1`, `-20261124-1`, `-20261124-2`) went through this same button, API and crews. So this
   sprint **proves and hardens the path; it does not build a new one.** The work is: timing, the error paths,
   one screen label, one gap in how a crash shows, and the log check.
3. **The real-call budget is nearly spent.** `spike` has a cap of 70 real calls and **58 are used** (spike-report
   §12.7). A whole run needs about 17. So **a real-provider proof run cannot be paid from `spike`.** Decision
   D-1 in section 8.
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

### 2.1 How to time one stand-in run (you run this; it costs nothing and calls no model)

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

### 2.2 Choosing the pattern (rule decided now, number decided by your timing)

| Pattern | What it is here | Fits when | Cost |
|---|---|---|---|
| **REST wait** | The Start click does not return until the stage is done | A stage takes under ~10 s | Browser and form hold open; no progress; a 375 s stage limit makes no sense with it. **Rejected:** even a stand-in stage A takes 11 to 12 s |
| **Polling** (what exists) | Page reloads every 3 s while `is_working`; "Refresh now" and "Stop automatic refresh" links | A stage takes seconds to a few minutes | None new. No script, no open connection. Reload flicker; up to 3 s of lag |
| **SSE** | Server pushes unit updates over one open connection | Stages over ~1 to 2 min, or reload flicker is a real problem | A script, an open connection, a SAD edit (SAD §4 chose "no script") |
| **WebSocket** | Two-way open connection | A reviewer must send messages mid-stage | Never needed: the reviewer cannot act while a stage runs (`RUN_STAGE_RUNNING`) |

**Decision rule:** keep polling if your timed stage A, B and C are each **under 60 s of server time** and the reload
lag stays **3 s or less**. Move to SSE only if a stage goes over about 2 minutes **or** a person who watches the
run says the reloads are a problem, and then only after a SAD edit.

**Provisional choice: keep polling.** Evidence already on file (real runs, `spike-report.md` §12): stage A 25 to
30 s, stage B about 24 s, stage C under 1 s, all model calls together 47 to 53 s, against limits of 375, 150 and
30 s. **This choice is provisional until your timed stand-in run confirms the plumbing and the next real run
confirms the model times.** No code changes if it holds.

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

### 3.4 Proposed changes to the contract (none is built; each waits for approval)

| # | Change | Why | Touches |
|---|---|---|---|
| P-1 | Add a visible **"Real agents"** tag beside "Stand-in agents" (`run_labels` shows only the stand-in tag today) | The reviewer should see which kind of run they are looking at without inferring it from the absence of a tag | Template part only. `@frontend.eng`; visual snapshots change, so `@frontend.eng` proposes them and you approve |
| P-2 | **Refuse to start a real-mode review** when a model ID or the key is missing (`ModelNotSet`, `KeyNotSet`), using the existing `VALIDATION` refusal | Today a missing setting is found **after** the review has started (E-11) | `runs.start_run` and a test. No new status, no schema change |
| P-3 | **Catch any unexpected error in a running stage and end the review as Failed** (E-11) | So no stage can hang on "AI is drafting the rules" | Needs a failure reason to name it. **A new reason is a SAD edit and a schema `CHECK` change**: `@system.arch` first. Option: reuse `invalid output` (cheap, misleading) |
| P-4 | Write the **accepted / rejected** word and the run's felt-wait helper query into `integration.md` (no new column) | Section 6 | Documentation only |
| P-5 | **Call the existing cap check before each real call from the web app**, so the `spike` and `tuning` caps hold there too (0 (a)) | Today only the spike command stops at the cap | `agents` or `stages` (one call to `check_call_allowed`). On the cap, the stage must end as Failed with a reason, so it **shares P-3's reason decision (D-3)**. It does not touch the pinned US$2.50 cap |

**No new endpoint, no new status value and no new result field is proposed.**

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
| E-11 | **Something unexpected inside a running stage**, such as a missing model ID or key in real mode (`ModelNotSet`, `KeyNotSet`) | **Not caught.** `stages._run_unit` handles only the listed failures, and `run_stage` cancels its timer in `finally`, so the stage ends with the review still `A_RUNNING` | **The review sits on "AI is drafting the rules" and keeps reloading until the app restarts** (then E-7). This is the nearest thing to a "blank screen" on the path | **Gap. P-2 and P-3** |
| E-12 | An unexpected error while a page is built | `main.py` handler | The plain error page with the sentence for the signed-in role, never the error's details | Yes |

**Reproducing E-11 without any paid call:** with real mode set and the model ID left empty, start a review
against the **fake OpenAI** already used by the tests (`tests/fake_openai.py`). If the review stays on A_RUNNING,
the gap is real. I will write that as a failing test **only after you approve** this spec.

**How error paths are tested without paying:** E-3 to E-9 run the **real CrewAI crews against the fake OpenAI**
(`tests/fake_openai.py` can answer, fail with a status such as 429 or 500, be slow, or give a scripted answer, so
a wrong-shape answer is one more script). Only the proof run in section 8 (D-1) uses the real provider, and only
the operator starts it.

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
- **SSE and WebSockets**, unless the timed run overturns section 2.2 and `@system.arch` edits the SAD.
- **Any JSON API, new endpoint, new status value or new result field.**
- **An automatic fallback from real to stand-in.**
- **A second provider, a bake-off or any model other than the three pinned** (DL-55).
- **The evaluation run and its report** (B8, B9), the trace export (D4), the three-run comparison.
- **Hosted deploy** and anything in Appendix A or the parked F-IDs (CLAUDE.md).
- **Changing `docs/architecture-decisions-summary.html`** (frozen).
- **Changing the pinned model settings, prompts, call timeouts or the US$2.50 cap.**
- **Any paid call started by an agent.** Only the operator starts a real run.

## 8. Decisions I need from you, then what happens next

| # | Decision | My recommendation |
|---|---|---|
| D-1 | **Which spend activity pays for the real proof run?** `spike` has 12 of 70 slots left and a run needs about 17. `tuning` (cap 60) and `rehearsal`, `demo` (no cap) are the others | `rehearsal`, one run, about US$0.05 on the figures so far, which needs no new cap. Your call, and it goes in `decision-log.md` |
| D-2 | **Approve P-1 to P-5** (section 3.4), or strike any | Approve all five. P-3 and P-5 need their failure reason from `@system.arch` first. P-5 matters most if D-1 is `spike` or `tuning` |
| D-3 | **The wording for P-3 and P-5:** a new failure reason ("something went wrong that the app did not expect"; and for P-5, "the real-call limit was reached"), or reuse an existing one | New reasons. Reusing "invalid output" or "cost cap" would tell the reviewer something false |
| D-4 | **Run the timing in 2.1 and send me the numbers**, so section 2.2 stops being provisional | Yes, before any build |

**After you approve, in this order (small steps, each one its own pull request):**
1. You time the stand-in run; I fix section 2.2 with your numbers.
2. `@system.arch` records the reasons for P-3 and P-5 (if D-3 says new). I change no code before that.
3. A failing test for E-11 and one for the call cap, against the fake OpenAI; then P-2, P-3 and P-5 to make them
   pass (`@backend.eng`).
4. P-1, the label (`@frontend.eng`; snapshots go to you for approval).
5. Error-path tests E-3 to E-9 with the real crews against the fake OpenAI.
6. One real proof run, started by you under D-1's activity, and its log checked with section 6.
7. `*sync-docs` after any code change, with your approval before it writes.

## Sources

`sad.md` (§4 routes, run states, failure reasons, CR-017, CR-023, CR-030), `setup.md`, `scaffold-plan.md`,
`spike-report.md` §12, `backend.md`; code read for facts: `backend/web/routes/runs.py`,
`backend/services/runs.py`, `backend/runtime/stages.py`, `crews.py`, `agents.py`, `model_settings.py`,
`harness.py`, `backend/db/schema.sql`, `backend/main.py`, the review status and G1 templates,
`tests/fake_openai.py`.

## Assumptions

- "The Week 3 contract" means the Sprint 3 stand-in slice, and "`startRun`" means `runs.start_run` behind
  `POST /specialist/runs`. **If you meant something else, tell me before anything is built** (section 0).
- "Real crews" means the CrewAI crews with the real provider only for the operator's proof run, and the same crews
  against the fake OpenAI for every error path.
- "Accepted / rejected" in the log means both: our checks on the model's output, and the person's decision at a gate.
- "Same sprint 3 slice" means the demo fund, the demo documents, the demo rule off and the failure demo off.

## Open Questions

1. D-1 to D-4 in section 8 (the spend activity, the five proposed changes, the failure-reason wording, your timing).
2. Does the app's own process log carry the run id on each stage event? (Section 6; I did not look at the log
   because that needs a running app.)
3. Is E-11 reproduced? I read it in the code; a free test against the fake OpenAI will settle it, after approval.

## Audit

- 2026-11-24 · persona `integration-eng` · action `log-integration` · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · created this file: the build spec for one
  vertical path. **Documentation only; no code, no model call, no key, `data/spike.db` and `data/app.db` not opened.**
  Read: `backend/web/routes/runs.py`, `backend/services/runs.py`, `backend/runtime/stages.py`, `crews.py`,
  `agents.py`, `model_settings.py`, `harness.py`, `backend/db/schema.sql`, `backend/main.py`, the review status
  and G1 templates, `sad.md`, `setup.md`, `scaffold-plan.md`, `spike-report.md`. Queries in sections 2.1 and 6 were
  checked for syntax against an empty in-memory copy of the schema only.
