# Backend: the app shell (page-first thin slice)

Owner: `@backend.eng`. Branch `b1-app-shell`. Inputs read: `sad.md` (Build card incl. "Build
approach", Order of work, §4 Backend incl. routes, refusal codes, failure reasons, table list,
"Data model: the happy path", "Sign-in and secrets"), `scaffold-plan.md` (§1 tree, §3, §5),
`ux.md` (workflow, §1.3, §1.5, §1.7, §10), `setup.md`, `.cursor/rules/adapter-crewai.mdc`.
Not read or used: Future Work, Appendix A, tag `sad-full-design`.

**Scope of this change set.** The thin app shell that the Build card's "Build approach" row allows
(operator, 2026-11-16, answering scaffold-plan Open Question 1): B1's follow-up, the FastAPI
skeleton, the full schema, mock sign-in, stub services with their B2 places, the seven pages as
placeholders, and Tier 1 tests for what the shell supports. **Not** the real step logic: no
checks beyond the role check, no stored rows, verdicts or entries, no CrewAI, no model call.

## How this maps to CrewAI terms

A reading aid only. Nothing here is a new decision; each line points to where it is recorded.

- **Scenario:** the one review flow: Extractor → quote check → Verifier → G1 → Judge → G2 → date
  engine → G3 → publish. Recorded in `sad.md` §2 "Runtime shape"; built in "B3 (stand-in part)" below.
- **Tasks and agents:** three single-agent crews, defined in `backend/config/agents.yaml` and
  `tasks.yaml`, behind `extract_rows`, `check_conflicts` and `judge_applicability`
  (`backend/runtime/agents.py`). Recorded in "B3 (stand-in part)", step 7a.
- **Tools:** none, by design. Recorded in `sad.md` "Pattern Decision" and "Pattern Decision
  compliance" below.
- **Process:** not CrewAI's `Process`. The backend runs stages A, B and C in plain Python ("the
  backend owns the steps"; `backend/runtime/stages.py`). Recorded in `sad.md` §2 "Runtime shape".
- **Kickoff:** one kickoff per unit, inside each agent function, in real mode only (step 7b PR 4;
  with DL-43's one retry since PR 5). In stand-in mode, the default, `start_run` runs with the
  stand-in answers and CrewAI is never loaded. See "B3 step 7b, PR 4" and "PR 5" below.

## How to run

```bash
make install            # .venv (Python 3.12), app + test deps, git hooks
cp .env.example .env    # set SESSION_SECRET to any local random value
make run                # http://localhost:8000, Ctrl+C to stop
make test               # all tests, stand-in agents, no model
```

Sign in as **Compliance specialist** (`specialist-1`) or **General Partner / Fund Manager**
(`gp-1`). Delete `data/app.db` to start from nothing.

The spike's real call is a separate command with its own database (`data/spike.db`): see "B3 spike
runner" below. `make run` and `make test` never make a real call.

## What was built

| Area | Files | Real or stub |
|---|---|---|
| B1 follow-up | `pyproject.toml` (pinned), `Makefile` (install, run, test), `.gitignore` (`data/`), `.env.example` (`STAND_IN_UNIT_PAUSE_S`, `SESSION_SECRET`, `DATABASE_PATH`), `tests/tier1/`, `tests/tier2/` | Real |
| Settings | `backend/settings.py`: `AGENTS_MODE` defaults to `stand_in`; real mode needs `SPEND_ACTIVITY`; `STAND_IN_UNIT_PAUSE_S` read only in stand-in mode | Real |
| Database | `backend/db/schema.sql`, `connection.py`: the 13 ERD tables, `fund_id` everywhere, CHECKs for enums, UNIQUE one-decision keys, append-only `audit_log` triggers. Full `runs` incl. `started_at`, `started_by`, `demo_planted_row`, `demo_fail_step1`, `stage_attempt`, `spend_activity` | Real (B2 may refine) |
| Config | `config/fund/FND-DEMO-01.yaml`: `fund_id`, `name`, `regime`, `year_end` only | Real |
| Sign-in | `services/auth.py`: two fixed identities, role from a signed session cookie, `require_role` writes a `FORBIDDEN` audit entry and raises 403 | Real |
| Services | `services/runs.py`, `gates.py`, `decisions.py`, `calendar.py`, `publishing.py`, `stage_store.py` | **Stubs** (list below) |
| Runtime | `runtime/stages.py` (units one by one; failure demo), `runtime/agents.py` (stand-in pause; real mode refused) | **Stubs** except `unit_pause` |
| Pages | `web/routes/` (sign_in, runs, gates, calendar), `web/templates/` (base, parts, 7 pages, 403, 404) | Thin handlers; **placeholder** templates |
| Tests | `tests/conftest.py`, `tests/tier1/test_sign_in.py`, `test_roles.py`, `test_pause_and_mode.py` | Real |

## Stub function list (to be filled in, not renamed)

The SAD names routes and what lives in the service layer, but **no function names or
signatures**. Only `list_runs(fund_id)` and `start_run` are named (scaffold-plan §3, §5). The other
names below are derived from the SAD §4 routes (Open Question 1). Every stub says
`STUB — replace in B…` in its docstring.

| Function | Route | Stub does | The real version adds (block) |
|---|---|---|---|
| `runs.list_runs(conn, fund_id)` | `GET /specialist/runs` | Real read, newest first, with status words | — |
| `runs.get_run`, `get_active_run`, `list_units` | pages 2, 3 | Real reads | — |
| `runs.start_run(conn, settings, schedule, *, fund_id, started_by, demo_planted_row, demo_fail_step1)` | `POST /specialist/runs` | New run `ACTIVE · A_RUNNING`, audits start and switches, starts stage A in background | `RUN_ACTIVE`; `VALIDATION` for the failure demo in real mode (B2, B13a) |
| `runs.abandon_run(conn, *, run_id, run_version, reason, actor)` | `POST …/abandon` | `ABANDONED`, phase kept, audited | Only at `AT_G*`, `VERSION_MISMATCH`, `REASON_REQUIRED` (B2) |
| `runs.retry_run(conn, settings, schedule, *, run_id, run_version, actor)` | `POST …/retry` | Changes nothing; returns "not built yet" | Rule 10, three retry codes (B13b) |
| `gates.start_stage(settings, schedule, run_id, stage)` | — | Schedules `run_stage` with the run ID only | — (shape as SAD §4) |
| `gates.complete_g1(conn, settings, schedule, *, run_id, run_version, actor)` | `POST …/g1/complete` | `AT_G1 → B_RUNNING`, version +1, stage B | Phase guard, version, `GATE_INCOMPLETE` (B2) |
| `gates.complete_g2(…same…)` | `POST …/g2/complete` | `AT_G2 → C_RUNNING`, version +1, stage C | As G1 (B2) |
| `decisions.get_g1_view(conn, run)` | `GET …/g1` | Placeholder rows (+ demo row if switched on) with the V-8 view fields (H-036) | Stored rows, quote checks, flags (B2, B3) |
| `decisions.decide_row(conn, *, row_id, version, decision, business_day_rule, who_files, approve_reason, reject_reason, actor)` | `POST /specialist/rows/{row_id}/decision` | Audit entry only, not stored | `row_decisions`, every G1 code incl. `DEMO_ROW_NOT_APPROVABLE` (B2, B7) |
| `decisions.get_g2_view(conn, run)` | `GET …/g2` | Placeholder verdicts with the V-9 view fields (H-036) | Stored verdicts (B3) |
| `decisions.decide_verdict(conn, *, verdict_id, version, decision, value, confirm_reason, override_reason, decide_reason, actor)` | `POST /specialist/verdicts/{verdict_id}/decision` | Audit entry only; reads only the chosen answer's reason (DL-48) | `verdict_decisions`, checks (B2) |
| `calendar.get_g3_view(conn, run)` | `GET …/g3` | Calendar ID + placeholder entries with the V-10 view fields (H-036); rejected rows are real | Real entries, uncited list (B2, B3, B4) |
| `calendar.get_published_calendar(conn, fund_id)` | `GET /calendar` | Newest publication is live (real); placeholder entries | Real entries (B4) |
| `publishing.publish_calendar(conn, *, calendar_id, run_version, acknowledged, rejected_row_ids, uncited_paragraph_ids, actor)` | `POST …/publish` | Insert publication, `COMPLETED`, audited | `ACK_REQUIRED`, version, phase (B2) |
| `publishing.decline_calendar(conn, *, calendar_id, run_version, decline_reason, actor)` | `POST …/decline` | `DECLINED`, audited | `REASON_REQUIRED`, decision/route match (B2) |
| `stage_store.add_units`, `mark_unit`, `finish_stage`, `fail_stage` | — | Unit lines and phase moves; stage C creates the calendar version | Rule 9 store, stage-attempt check (B3) |
| `runtime.stages.run_stage(settings, run_id, stage)` | — | Units one by one; failure demo on stage A unit 1, attempt 1, stand-in only | Stage timer, trace, cost cap (B3) |
| `runtime.agents.run_unit(settings, stage, unit_id)` | — | Deleted in B3 step 6 (H-052); replaced by the three agent functions | — |

## View fields for the pages (H-036, 2026-11-17)

The services now send the fields in `frontend.md` §10.1, so the templates stop choosing from the
phase. Names and signatures are unchanged (H-035). Values are stand-in placeholders; the names are
what matter. Built in six small steps on separate branches (PRs #68 to #73), with Tier 1 tests in
`tests/tier1/test_run_view_fields.py`.

| Field | Where | Notes |
|---|---|---|
| V-1 `review_number` | every run (`runs._describe`) | **Not defined in the SAD.** Rule used: the run's place among the fund's runs, oldest = 1. Runs are never deleted, so a number never changes |
| V-2 `status_tone` | every run | ux.md §1.5 table, now in `runs.TONE_ACTIVE` / `TONE_ENDED` |
| V-3 `steps` | every run | ux.md §1.4 table; links only on "Done" and "Your turn" |
| V-4 `group` | each unit (`runs.list_units`) | stage A: `DOC-` is `drafting`, `ROW-` is `checking_drafts`; B `applies`; C `dates`. The stand-in makes no `checking_drafts` units (B3) |
| V-5 `counts` | every run | Counted from the stored rows, verdicts and entries (B3 step 5) |
| V-6 `ended`, `failure`, `published_at`, `ended_because` | every run | `ended` (time and reason) is read from the run's last `gate_event` audit entry, because there is no "ended at" column |
| V-7 `started_by_label` | every run | `runs.actor_label`: sign-in label plus " (mock)" |
| V-8 G1 | `decisions.get_g1_view` | Row status, quote check, paragraph, flags, who-files choice, `decided` line; view `stage`, `summary`, `unused_paragraphs` |
| V-9 G2 | `decisions.get_g2_view` | Cited facts, approved rule, `missing_fact`, `overrule_value`, `decided.outcome` |
| V-10 G3 | `calendar.get_g3_view` | `stage`, `rejected_rows` (real), unused paragraphs, `previous_publication_at`, `outcome`; entry words and `marks.moved` |
| V-11 | `calendar.get_published_calendar` | Same entry builder, so published entries also carry `source_document` and `quote` |
| V-12 refusal object | `services/refusals.py` | **Built in B2** (`code`, `sentence`, `anchor`, `target_label`, `short`, `link_text`, `typed`); see "B2" below |

`runs.page_stage(run, "g1"|"g2"|"g3")` gives `before`, `at`, `after` or `ended_before` for all three
step pages. Stand-in data changed once: calendar entry 2 now moves from Sun 18 Apr to Mon 19 Apr
2027, so its "moved off a weekend" mark is consistent.

## B2: gates, run states and the refusal object (branch `b2-gates-and-checks`, 2026-11-17)

**What it does.** The stub services now hold the SAD's checks (§4 "Transitions and guards"), store
stage outputs through the Rule 9 function, and refuse through one shared object. A refusal does
three things in this order: writes one `refusal` audit entry, builds the V-12 object, and raises
`Refused` **before** the service has written anything else. So a refusal changes nothing except its
own audit entry (each Tier 1 test checks that).

| Part | Where | Notes |
|---|---|---|
| Refusal object (V-12) | `services/refusals.py` | All 17 SAD codes with their HTTP status; every ux.md §5 sentence word for word; `refuse()` audits and raises |
| Same page again | `web/refusal_pages.py`, `main.py` | The form's address says which page to show again; it gets `refusal` and the refusal's status (409 or 422); the pages already read it. Unknown rule, answer, calendar → 404 (`NotFound`) |
| Shared guards | `services/guards.py` | `RUN_NOT_ACTIVE` → `RUN_STAGE_RUNNING` → `VERSION_MISMATCH`, in that order |
| Start, abandon | `runs.py` | `RUN_ACTIVE` (the check and the insert run under `BEGIN IMMEDIATE`, so a double click cannot start two reviews), `VALIDATION` for the failure demo outside stand-in mode; abandon only at a gate |
| Rule 9 | `services/stage_store.py` | `store_stage_outputs`: one transaction; refuses unless the run is `ACTIVE`, in `<stage>_RUNNING`, on the same `stage_attempt`, and every unit is done; otherwise the output is **discarded** and one audit entry says so. `fail_stage` makes the same check. A failed stage stores nothing. Rollback on any error: no half a stage |
| Stored data | `rows`, `paragraphs`, `quote_checks`, `verdicts`, `calendar_versions`, `calendar_entries` | Stage A and B outputs are the stand-in answers (B3 step 5); stage C's dates are the date engine's (B4); stage B has one verdict per **approved** rule, stage C one entry per rule whose final answer is "applies" |
| G1 decisions | `decisions.decide_row` | Stored in `row_decisions` (decide-once: checked, and the UNIQUE key as a backstop). Order: already decided → no answer → reject reason, or approve: quote check → weekend rule → filing party (offered values only) → reason over a flag. The other answer's fields are ignored (DL-48) |
| G2 decisions | `decisions.decide_verdict` | Stored in `verdict_decisions`. The answer must fit AI's verdict (confirm repeats it, overrule gives the opposite, decide only for "can't tell"), else `VALIDATION`; overrule and decide need a reason |
| Finish G1 / G2 | `gates.py` | Ended → wrong phase → stale page → `GATE_INCOMPLETE` (counts the undecided, and the "can't tell" ones at G2). `stage_attempt` goes back to 1 for the next stage |
| Publish, decline | `publishing.py`, `web/routes/calendar.py` | Publish compares the posted lists with the server's own (`ACK_REQUIRED`); decline needs a reason; the form's `decision` must match the route (`VALIDATION`, in the route) |
| Start-up rule | `runs.fail_interrupted_runs`, called in `create_app` | A review caught mid-stage becomes `FAILED`, "service restarted"; reviews at a gate are unaffected. Without it, B2's own checks would leave a restarted review stuck and block every new one |

**Not in B2 (left, with owners):** `DEMO_ROW_NOT_APPROVABLE` and the "Approval blocked" chip (**B7**,
which uses `refuse()`; until then the demo rule can be approved like any other); Retry and its
three codes (**B13b**, `retry_run` is still a stub, the sentences exist); the stage time limit
and timer (rule 6; needs the real stage runner, **B3**); Pydantic form models that refuse unknown
fields; the `trace` table, cost count and cost cap (**B3**).

**Rule 9 is built here, not in B3.** The SAD's build order puts "the stage-end store with the stage
attempt (rule 9)" in B3 (Order of work row 3). The operator asked for it in B2 because decisions
cannot be stored (decide-once) until rows are. B3 therefore only has to replace the stand-in data.

**Checks I chose where the SAD is silent** (listed as Open Questions 5 to 8): the order the checks
run in; that a row's posted `version` is not compared (the SAD lists `VERSION_MISMATCH` for the
run, not for a row); `typed` as `{field: text}`; three sentences ux.md does not give.

## B3 (stand-in part): steps 1 to 5 (2026-11-18)

B3's stand-in part is built in seven small steps, one pull request each, so each can be reviewed
alone. Steps 1 to 6 and 7a are done. Step 7b (install CrewAI and build the crews behind the
same functions, switched off) has an approved plan (2026-11-19): PR 1 is done, and PRs 2 to 6 are
next week. See "Step 7b: dry-run findings" below. DL-40 is pinned (PR #121). No model is called
anywhere: `AGENTS_MODE` stays `stand_in`.

**Step 7b: dry-run findings, for reuse before the spike (2026-11-18).** `uv pip install
--dry-run "crewai==1.15.35"` against this `.venv`, nothing installed:

- **Version:** `crewai==1.15.35` (released 2026-11-03), the newest stable release at least two
  weeks old on that day; 1.15.42 was released the same day. Re-check before installing.
- **Size:** 117 new packages (137 resolved), including `chromadb`, `lancedb`, `onnxruntime` and
  `openai`.
- **Downgrade:** CrewAI needs `pydantic<2.13`, so `pydantic` goes from 2.14.3 to 2.12.5 (and
  `pydantic-core` 2.50.4 to 2.41.5). FastAPI 0.163.1 accepts it (`pydantic>=2.9.0`). Run every test
  and the visual check after the install.
- **Telemetry:** CrewAI ships OpenTelemetry and sends anonymous usage data by default. Switch it
  off (`CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`) and add a test that it stays off.
- **Plan then:** create the crews only in real mode, so tests and stand-in runs never import
  CrewAI (T-MODE-1); real mode still refuses to call while `LLM_MODEL_*` is empty (DL-40).

| Step | PR | What | Where |
|---|---|---|---|
| 1 Loader (W-02) | #92 | The 6 mock documents → 13 paragraphs, paragraph text only (no test notes, planted-conflict notes, header warning or amendments; CR-016). Refuses if the file and the config disagree | `backend/domain/sources.py`, `config/regulation/lu-part2.yaml` |
| 2 Quote check (QN-1, W-04) | #93 | Trim, collapse ordinary spaces, tabs and line breaks, then the quote must be one unbroken piece of the **cited** paragraph. Case, punctuation and Unicode forms count | `backend/domain/quote_check.py` |
| 3 Schemas and guardrails (CR-003) | #94 | The three step outputs as Pydantic models (unknown fields refused) and one guardrail per agent card | `backend/domain/schemas.py`, `guardrails.py` |
| 4 Stand-in answers and agent functions (CR-030) | #95 | Recipient codes; the fund facts loader (ID, fact, value; event ID and description); hand-written answers (6 rows, 1 flag, 1 "unsure"); `extract_rows`, `check_conflicts`, `judge_applicability`, which put each answer through the real guardrail | `backend/domain/fund_facts.py`, `backend/stand_in/*.yaml`, `backend/runtime/agents.py` |
| 5 Stages A and B wired | #96 | Stage A: loader → extract per primary document → demo rule if on → quote check per row → verifier per row; units: 5 documents then one check per rule. Stage B: fund facts → judge per approved rule. The store keeps the applicability rule, the quote check's reason and the flags; `offset` is stored as JSON. Pages get words for codes, recipient and document names from the config, and real fact values and counts | `backend/runtime/stages.py`, `services/stage_store.py`, `decisions.py`, `calendar.py`, `runs.py`, `backend/domain/wording.py` |
| 6 Trace, cost count, cost cap, stage timer | this PR | **Trace** (CR-018): table with the §4 columns, append-only triggers; every agent call, stand-in included, writes one line, adds its cost to `runs.cost_so_far` and writes an `agent_output` audit entry whose `trace_ref` is the record key, in one transaction. **Cost cap** (CR-017): before each call, at `RUN_COST_CAP_USD` or above the unit fails with "cost cap" and no call starts. **Stage timer** (rule 6, DL-43): a timer on its own thread around each stage fails the running unit with "stage time limit"; a call still running finishes, its output is marked `late`, kept in the trace only, its cost counts, nothing is stored (T-RUN-6, T-RUN-8). `fail_stage` now checks and changes the run under one write lock, so the timer can never fail a stage that has just finished. Settings use the SAD names `STAGE_TIME_LIMIT_A`, `_B`, `_C`. `run_unit` deleted (H-052) | `backend/services/trace.py`, `backend/db/schema.sql`, `backend/runtime/stages.py`, `agents.py`, `services/stage_store.py`, `backend/settings.py`, `.env.example` |
| 7a Prompts and role harness (no CrewAI yet) | this PR | `agents.yaml` and `tasks.yaml` written from the §2 agent cards (role, goal, backstory; instructions and expected output; braces only for inputs; no example of a demo trap); the cards' worked examples in `backend/config/examples/`, passed in as `{example}`. `prompts.py` builds each task's inputs from stored data only (Context strategy), fills them as CrewAI would and refuses a missing, unused or stray input, and gives each step's prompt version (hash of agent, task and example). Stand-in trace lines now record `<prompt version>+stand-in:<answer-file hash>`. Role harness call caps: spike 70, tuning 60, counted from the trace (EC-R10). Tests: T-LEAK-1 prompt half and the harness cap (Tier 1), T-PROMPT-1 and T-EXAMPLE-1 (Tier 2) | `backend/config/`, `backend/runtime/prompts.py`, `harness.py`, `agents.py` |

**Operator decisions in B3 (2026-11-18):** an empty quote fails; only ordinary whitespace is
collapsed; a date-shaped value is refused unless it is copied word for word from the agent's input
(H-052); the judge's facts come from the mock profile through a loader; recipient code `LBR`;
"who files" as the source writes it; a row the verifier has no answer for gets no flags; a
**temporary demo rule** (rule 7, cited `SRC-UCILAW-P1`) until B7 replaced it with
`config/demo/planted-row.yaml`; the visual script's driving steps updated, snapshots not (H-053).

**Placeholder dates, B3 step 5 to B4 (operator, 2026-11-18).** Until B4, stage C attached three
placeholder dates to rules 1, 2 and 4. B4 replaced them with the date engine and deleted
`backend/stand_in/shell_data.py` (see "B4" below).

## B13a: failure demo and stand-in pause (2026-11-19)

Most of B13a was already in place from the app shell and B2: the `demo_fail_step1` switch on the
run and its audit entry, the start-form checkbox shown only with stand-in agents, `VALIDATION` for
the field in real mode, the `demo failure` reason and its sentence, the "Failure demo on" label in
the specialist page header, `STAND_IN_UNIT_PAUSE_S` with the per-unit wait, and T-PAUSE-1. B13a adds:

| What | Where |
|---|---|
| **The stand-in extractor hook** (CR-033: "the stand-in extractor fails stage A's first unit"). The stage no longer fakes the failure itself: it calls `extract_rows(..., demo_fail=True)` for stage A's first unit on the first stage attempt, in stand-in mode, and the extractor pauses and raises `DemoFailure`. The unit goes through the normal unit path (cost cap check, "running", failure recorded) and fails with `demo failure`. No output, so no trace line | `backend/runtime/agents.py`, `stages.py` |
| **T-DEMOFAIL-1** in one Tier 1 file: switch off runs normally; switch on fails unit 1 with the other four `waiting` (and unit 1 runs alone first, rule 11), one audit entry, nothing stored; real mode refuses the field (`VALIDATION`, no run); the extractor hook refuses real mode; the specialist page shows the label and "Without Retry", and no GP calendar view contains "Failure demo" | `tests/tier1/test_demo_failure.py` |

Retry of the failed stage (rule 10, T-RETRY-1) is **B13b**. Until then a failure-demo run stays
`FAILED` and the page offers only a new review (`ux.md` page 3, "Without Retry").

## B4: stage C, the date engine (2026-11-19)

**What it does.** `backend/domain/dates.py` turns every approved rule whose final G2 answer is
"applies" into calendar entries, in plain code (no model computes a date, SD MN-005): anchors
(month end, quarter end, the fund's financial year end, or each logged event's awareness or
occurrence date) → offset (`D-1` calendar days; `D-2` months from a period end land on the month's
last day; `D-3` months from an event keep the day or the month's end; a fixed day and month, in the
anchor's year or the next) → the business-day rule chosen at G1 (`D-4`, `D-7`: roll forward, roll
backward or no roll, skipping weekends and the config's holidays) → kept if the calendar due date is
inside the fund's horizon. Marks: moved, precautionary (added at G2), and the open question
(CR-027). Entry ID `ENT-<fund>-<paragraph>-<recipient>-<period>`, independent of the due date.

**Fail closed.** A rule with no business-day rule (T-W13-2; there is no default, `D-6` is retired)
or two rules giving one entry ID (DL-35, both named) stop generation: stage C's unit fails with
`calendar generation`, nothing is stored (CR-011), and the audit log keeps the exact reason.

| Part | Where |
|---|---|
| Conventions in words, the 2027 mock holidays, open convention `OQ-7` → `SRC-UCILAW-P2` + `AED` | `config/regulation/lu-part2.yaml` |
| Financial year end and calendar horizon (2027) | `config/fund/FND-DEMO-01.yaml` |
| Event dates for the engine only (the judge still gets ID and description) | `backend/domain/fund_facts.py` `load_event_dates` |
| The engine and its config loader | `backend/domain/dates.py` |
| Stage C on the engine; `shell_data.py` deleted | `backend/runtime/stages.py` |
| G1 `open_question` set from the config (was always `False`); the "why" line says Monthly, Quarterly, Annual, Event-triggered | `services/decisions.py`, `calendar.py` |
| Tests: **EC-007** (a demo review gives the answer key's 22 entries exactly: calculated and calendar dates, 6 moved, 4 OQ-7, 4 precautionary), **EC-008** / **T-ID-2**, **T-W13-1**, **T-W13-2**, the collision, the failure path, `D-2`, `D-3`, events, holidays, the fixed day, the horizon, the why words | `tests/tier1/test_date_engine.py` |

**Choices where the SAD is silent (for review):**
1. **The horizon applies to the calendar due date** (after the roll), not the calculated date.
   No demo date crosses a year end, so the 22 entries are the same either way.
2. **Every logged event applies to every event-anchored rule.** The event log's "Obligation" column
   is not read (it names the answer). The MVP has one event and one such rule. Accepted by the operator
   and recorded under Known gaps as an MVP limitation.
3. **The period is taken from the anchor:** `YYYY-MM` for a month or quarter end, `FY<year>` for a
   financial year end, the event ID for an event (the SAD's examples).
4. **Test helpers and the visual script decide a whole review with the demo's G1 choices** (answer
   key §5: rule and "who files" per rule), so a full test review gives exactly the demo calendar.
   Single-decision helpers keep "roll forward" and "AIFM".

`@qa.eng` shares B4 (Order of work): EC-007 and the answer-key date checks
(`tests/test_answer_key.py`) both pass.

## B7: the planted demo row (2026-11-19)

Built straight after B4 at the operator's request (2026-11-19). The Build card puts B5 and B12
before B7: B12 is built, and so is B5 (templates and CSS, `@frontend.eng`; `frontend.md` §9, S-01
to S-34 all ✅). B7 needed nothing from either (the G1 page already had the refusal's place).
*(Corrected 2026-11-19, H-059: this note first said B5 was "still in progress"; `frontend.md` showed
it done.)*

| What | Where |
|---|---|
| **The fixture** (CR-029, DL-31): a real quote, word for word in `SRC-CSSF15627-P3`, that does not support the rule. The paragraph says how the monthly report is sent (a secure electronic channel); the row claims a monthly "Secure channel transmission confirmation" due 5 calendar days after month end. The quote check passes; nothing in the quote sets a deadline. No answer-key ID. Replaces the temporary demo rule | `config/demo/planted-row.yaml` (the temporary file is deleted) |
| **The refusal** (DL-44): an approve on a row with origin `demo` is refused with `DEMO_ROW_NOT_APPROVABLE` first among the approve checks, whatever reason or business-day rule was sent, and audited. The Approve button stays visible; reject with a reason is the only decision it can get | `backend/services/decisions.py` `decide_row` |
| **"Approval blocked"** (ux.md page 4): once an approval has been refused, the server sends that status (tone `problem`) for the demo rule until it is rejected, read from the refusal's audit entry, so it survives a reload | `decisions.get_g1_view` (H-036 V-8 `status`) |
| **Tests**: T-DEMO-1 (off: 6 rows, no switch entry; on: 7 rows, the 7th `demo`, quote check pass, verifier ran, switch entry; reject logged and in the G3 rejected list, never on a calendar) and T-DEMO-2 (every approve refused and logged, with and without a reason, with each rule; stays pending; "Approval blocked"; G1 waits for the reject; the page shows the sentence) | `tests/tier1/test_demo_row.py` |

Not built: "an evaluation run with the switch on is refused" (T-DEMO-1, EC-R7) needs the evaluation
runner (**B8**).

## The first green path (2026-11-19): passes

`tests/tier1/test_green_path.py` (Tier 1) drives one review through the pages, as the specialist
and the General Partner would, with `AGENTS_MODE=stand_in` and no model: the GP sees "being
prepared" → start with the demo rule → stand-in stage A (7 rules) → G1: Approve on the planted row
refused (409, the DL-44 sentence, "Approval blocked"), rules 1 to 6 approved with the demo's
choices, the planted row rejected → stand-in stage B → G2 (the "can't tell" rule added) → stage C
(22 dates) → G3 page; the GP still sees "being prepared" → publish with the acknowledgement → the GP
sees the published calendar (22 entries, 4 "May not be required", due next Mon 11 Jan 2027, no
OQ-7, moved or demo marks, labelled stand-in) → the audit log shows every step in order (start,
switch, stage A, G1, stage B, G2, stage C, publish), 18 agent outputs each pointing at its trace
line, the one refusal, 13 decisions; cost 0 and no model in the trace.

Checked that the test can fail: with the demo-row refusal switched off, it fails at the planted
row's Approve (303 instead of 409); with the code restored, it passes.

**What this unlocks (Build card):** the operator may now pin DL-40 (the model IDs, SOQ-25). Only then
the B3 spike, with step 7b (install CrewAI) just before it. No model ID is chosen and no paid call is
made by `@backend.eng`.

## B1 follow-up: CI (2026-11-19)

`.github/workflows/ci.yml` (sad.md §5 "CI", handoff H-003) runs on every pull request and every
push to `main`, with stand-in agents, no model key and read-only permissions:

| Step | Blocks a merge? |
|---|---|
| `ruff check backend tests` (ruff 0.17.3, pinned in `requirements-dev.txt`; settings in `pyproject.toml`: line length 100, Python 3.12, ruff's default rules minus `B008`, FastAPI's `Depends()`/`Form()` defaults) | Yes |
| Tier 1 tests: `pytest tests/tier1 tests/test_answer_key.py` | Yes |
| Tier 2 tests: `pytest tests/tier2` | No (`continue-on-error`, until promoted, §9) |
| `aamad validate` (1.0.1), with the same temporary `qa.md` exception as `scripts/git-hooks/run-checks.sh` (H-002: remove both together) | Yes |

**Never in CI:** the real-name scan (its list is in the git-ignored `reference/`, H-003) and any
model key. **Formatting is not checked yet** (operator, 2026-11-19): the one-time `ruff format`
(55 of 70 files) waits for a quiet moment, announced by handoff.

To get there: `ruff check --fix` (safe fixes only: imports, newer spellings) and 13 by hand. The
stage functions now pass each unit's inputs with `functools.partial` instead of a lambda over loop
variables (B023); a rule-9 test expects `sqlite3.IntegrityError` instead of any `Exception`
(B017); `tests/test_answer_key.py`'s mock-up checks are **skipped when `docs/prototype` is absent**
(private, so absent in CI; the real pages are checked by T-W13-1). Checked by running the blocking
tests in a copy with only the committed files: 221 passed, 4 skipped. `make lint` runs the same lint
locally.

## B3 step 7b, PR 1: CrewAI installed, its outside connections off (2026-11-19)

The step 7b plan (operator, 2026-11-19; SAD changes in H-065) is six small PRs: 1 install and
telemetry off, 2 model settings and per-call token limits, 3 a fake OpenAI for tests, 4 the crews
behind the three agent functions, 5 our single DL-43 retry and one trace line per attempt, 6 docs.
No real key and no paid call in any of them; the spike waits for the operator.

| What | Where |
|---|---|
| `crewai==1.15.35` pinned in the app's dependencies (CI installs it too) | `pyproject.toml` |
| **The one door to CrewAI**: `load_crewai()` forces four switches, then imports it. Telemetry (`CREWAI_DISABLE_TELEMETRY`, `OTEL_SDK_DISABLED`), CrewAI's own **tracing** (`CREWAI_TRACING_ENABLED=false`; it can send a first run's traces to the CrewAI platform, separate from telemetry) and its **version check** (`CREWAI_DISABLE_VERSION_CHECK=true`; it asks the package index). Forced, so `.env` cannot turn them back on | `backend/runtime/crewai_setup.py` |
| The same four switches in CI and, as information, in `.env.example` | `.github/workflows/ci.yml`, `.env.example` |
| **Tests (Tier 1):** in a fresh process with every network connection blocked and the environment asking for the opposite, loading CrewAI and building a one-agent crew opens no connection, and CrewAI itself reports telemetry and tracing off. **T-MODE-1:** every backend module is imported and a whole stand-in review (the green path) runs, and CrewAI is never loaded. Both tests were seen to fail with the switch broken and with a stray `import crewai` | `tests/tier1/test_crewai_setup.py` |

**What the install changed** (checked against `main` before the install):

- **Packages:** 115 new. Of the packages already installed, only two changed: `pydantic` 2.14.3 →
  2.12.5 and `pydantic-core` 2.50.4 → 2.41.5 (CrewAI needs `pydantic<2.13`; FastAPI 0.163.1
  accepts it).
- **Tests:** 273 before, 275 after (the 2 new ones); none changed result.
- **Test warnings:** 2 → 1. Gone: Starlette's "use `httpx2` instead of `httpx`" warning. CrewAI
  brings in `httpx2` 2.16.2, and Starlette's test client uses it when it is there. The page tests
  pass unchanged. Still there: pytest's warning about a `product(...)` in `test_demo_row.py`
  (unrelated).
- **Lint:** clean. **Visual check:** passes, no snapshot changed.

## B3 step 7b, PR 2: model settings and per-call token limits (2026-11-21)

Plain code and tests; no CrewAI call, no network, no model call, no model ID in any committed file.

| What | Where |
|---|---|
| Per-role settings read from the environment: the model ID (`LLM_MODEL_*`, empty until the operator sets it in their own `.env`), the output limit of one call (`LLM_MAX_TOKENS_*`, defaults 2000 / 2000 / 4000) and each call's own timeout (`CALL_TIMEOUT_*`, 90 / 60 / 60). Names are the SAD §4 names. A bad number refuses to start; a missing model ID does **not** (it is checked where a call is made) | `backend/settings.py` |
| `role_settings()`: one role's call settings (DL-40's reasoning effort and temperature, the limit, the call timeout, the HTTP timeout = call timeout minus 5 s), `sent_to_provider()` (what goes in the request; a temperature of `None` is left out) and `logged()` (the trace's `settings_json`). **No model ID means no call**: `ModelNotSet` | `backend/runtime/model_settings.py` |
| `call_cost_usd()` from provider token counts at the operator's DL-40 prices, kept **per role** (not per model ID, so no ID is committed), and `worst_case_run_cost_usd()` | `backend/runtime/model_settings.py` |
| **Tests (Tier 1):** the settings and their refusals; the sampling settings per role; the HTTP timeout below the call timeout; no ID, no call; **one call can never pass a tenth of the cap, and a generous run (12 rows, every call at its output limit, every call retried once) stays under US$2.50**. Another test shows that check fails when a limit is raised too far. Six deliberate breaks were all caught | `tests/tier1/test_model_settings.py` |
| `.env.example`: the new names, and the old `CALL_TIMEOUT_*_S` / `HTTP_TIMEOUT_*_S` variables removed (they were not read by anything; the SAD names differ). Handoff H-071 tells `@project.mgr` | `.env.example` |

**The worst case, so the limits are not a guess:** with the demo's largest real prompt of each role
(at most 7,000 characters, which is a ceiling on tokens), the most one call can cost is about
US$0.0015 (extractor), US$0.038 (verifier) and US$0.024 (judge). A whole run at the limits with
every call retried once comes to about **US$1.49**, against the US$2.50 hard stop.

**Choices where the SAD is silent (say if any should change):**

- **The limits (2000 / 2000 / 4000) are starting values**, not measurements. The judge and the verifier
  are reasoning models, whose hidden thinking counts inside `max_completion_tokens`, so a limit that
  is too low would cut an answer off and fail the unit as invalid output. The spike shows the real
  sizes. The provider's stop reason (a cut-off answer) is not a trace column yet; PR 5 should record it, or the spike will not show a limit that was too low.
- **The verifier sends no temperature.** DL-40 gives one for the extractor (0) and says "no
  temperature" for the judge, but names none for the verifier. A reasoning model may refuse one, so
  none is sent.
- **The prices are the operator's DL-40 prices from 2026-11-19**, written per role. Re-check them
  against the provider's list before the spike.
- **The agent file still says `max_iter: 2`**; H-065 says 1. Changing it changes every prompt
  version, so it moves in PR 4, with the crews that read it.

## B3 step 7b, PR 3: a fake OpenAI for tests (2026-11-21)

Test code only: nothing in `backend/` changed. No model, no real key, no outside connection.

| What | Where |
|---|---|
| **The fake**: a small server on `127.0.0.1` (this machine only), in a background thread of the test, that speaks the part of OpenAI's chat completions API the `openai` client (the one CrewAI uses) needs. A test **scripts** what the "model" does, in order: `Reply` (text or JSON, token counts, the model string returned, a stop reason, an optional delay) or `Failure` (429, 5xx, 401 and so on). It can also **refuse a setting** (`reject_params`, as OpenAI does for a model that does not accept it) | `tests/fake_openai.py` |
| **It counts every request that reaches it**, including ones that fail, time out or are refused, and keeps each request's whole body (so a test can check `max_completion_tokens`, `response_format`, `reasoning_effort`). A request nobody scripted gets a 500 and is written down in `unscripted`; `unused()` says how many scripted answers were never asked for. This is the test rule of H-065: **one unit sends exactly one request**, except our one DL-43 retry and CrewAI's silent repeat | `tests/fake_openai.py` |
| The `fake_openai` fixture | `tests/conftest.py` |
| **Tests (Tier 1), using the real `openai` client:** answers and token counts parse; the returned model string can differ; a cut-off answer; the body is kept; 429, 5xx and 401 raise the matching errors; a slow answer times out in the client and is still counted; a refused setting is refused, counted and leaves the scripted answer unused; the count is exact; an unscripted request is written down; a client that retries on its own shows two requests (why H-065 turns that off) and with its retries off exactly one; only the placeholder key is ever seen. Five deliberate breaks of the fake were all caught | `tests/tier1/test_fake_openai.py` |

**What it does not know:** CrewAI's own silent repeat without `reasoning_effort` (H-064 condition c). The
fake can refuse the setting (`reject_params`); whether CrewAI then repeats the call, and how our
interceptor sees it, is what PR 5 shows against this fake. If CrewAI behaves differently from what
the H-064 check found, PR 5 says so.

## B3 step 7b, PR 4: the crews behind the three agent functions (2026-11-21)

Real mode (`AGENTS_MODE=real`) now sends a unit to a CrewAI crew and puts the answer through the
same guardrail as a stand-in answer. **Tested only against the fake OpenAI (PR 3): no real key, no
real model, no paid call.** Stand-in mode is unchanged and never loads CrewAI (T-MODE-1).

| What | Where |
|---|---|
| **One crew per unit**: one agent, one task, one `kickoff`, built from the step's rendered prompt and the role's settings. Agent: no delegation, no memory, no tools, `max_iter` 1, `max_retry_limit` 0. Task: no `output_pydantic`, no `Task.guardrail`, `guardrail_max_retries` 0. Crew: sequential, `max_rpm` 30, no memory. OpenAI client: its own retries off, timeout = the call's minus 5 s, `max_completion_tokens`, `reasoning_effort`, temperature only where DL-40 sets one. `ModelServiceError` for any provider failure | `backend/runtime/crews.py` |
| **The strict `response_format`**: our own JSON schema, built from the existing Pydantic result classes, sent through the LLM's `additional_params` (CrewAI's own route strips `null`, so an optional field could never be null). Keywords strict mode does not accept are dropped; our Pydantic check still enforces them | `backend/runtime/wire_schema.py` |
| **Real-mode path in the three agent functions**: refuse with no model ID or no key *before* any input is built; render the prompt; call the crew once; parse the text as JSON; the same guardrail; one trace record with the model, the settings sent, `max_tokens`, token counts and cost, and the real prompt version. Not valid JSON, a broken schema and a broken guardrail all fail the unit as `invalid output` after ONE request: the model is never asked again (D5). `DemoFailureRefused`: the failure demo is stand-in only (DL-52, CR-033), also now refused with a clear error in real mode | `backend/runtime/agents.py` |
| **The stage**: a provider failure fails the unit with the run's reason `model service` (one attempt for now) | `backend/runtime/stages.py` |
| **The key** is read from `.env` into the settings and never shows when they are printed (CR-021) | `backend/settings.py`, `backend/runtime/model_settings.py` |
| **`max_iter` 1** on all three agent cards (H-065). This changes every prompt version in the trace, as `agents.yaml` is hashed | `backend/config/agents.yaml` |
| **Tests (Tier 1, against the fake):** each role sends ONE request with its model, limit, reasoning effort and (extractor only) temperature, and the strict schema; the prompt is the rendered one with no answer-key text; the trace line; bad JSON, a broken schema and a broken guardrail are each one request, no re-ask; **500, 503, 429 and 400 are each one request, and a timeout is one request**; no ID, the placeholder key or no key sends nothing; the crew has exactly the SAD's settings; the stage's `model service`; wire-schema rules on all three result classes. Nine deliberate breaks of the crew code were caught (one more was equivalent: sending `temperature=None` changes nothing) | `tests/tier1/test_crews.py`, `tests/tier1/test_wire_schema.py` |
| The old "real mode is refused" tests now check what is true: no model ID is refused first (`ModelNotSet`), and the failure demo is refused in real mode even with an ID and a key | `tests/tier1/test_stand_in_agents.py`, `test_demo_failure.py` |

**What the fake showed (these are findings; H-072 asks `@system.arch` to record them):**

- **CrewAI's default agent retry limit is 2**: left alone, ONE failing call is THREE requests. Set to 0.
- **CrewAI has a third retry layer nobody listed**: every model call is wrapped in a rate-limit retry
  (HTTP 429, three attempts, waits of 1 and 2 s, no setting). With the HTTP client's and the agent's
  retries off, a 429 was still three requests. `load_crewai()` now sets that attempt count to 1; it is
  a library internal, so it is pinned with CrewAI 1.15.35, `load_crewai()` stops the call if the name
  disappears, and a test fails on a 429 that is not exactly one request.
- **A timeout comes back from CrewAI as a plain `ConnectionError`** ("Failed to connect to OpenAI API:
  Request timed out"), not as the OpenAI client's timeout error. PR 4 treats every provider failure the
  same (`ModelServiceError`); PR 5 needs to tell a retriable failure (timeout, 429, 5xx, no
  connection) from one that is not (a 400, a 401).
- CrewAI warns that it assumes an 8,192-token context window for a model ID it does not know. The three
  DL-40 IDs are in its catalogue (H-064), so this shows only with the fake's made-up IDs.

**Not done here, on purpose (PR 5):** the one DL-43 retry around the call, one trace line per HTTP
attempt through CrewAI's `interceptor`, the model string the API returns (`model_returned`), the
provider's stop reason, and CrewAI's silent repeat without `reasoning_effort`. Until then a failed
call is one attempt, a failed call writes no trace line, and the token counts come from CrewAI's
own usage count. **Do not run real mode before PR 5 and the operator's spike.**

**Choices where the SAD is silent (say if any should change):**

- Any exception from `kickoff` is a `ModelServiceError`, including one that is really a CrewAI bug. PR 5
  narrows it when the retry needs to tell them apart.
- The strict schema is only known to follow OpenAI's documented rules. A 400 "invalid schema" on the
  first real call means one more keyword has to be dropped (`wire_schema.py` says so).
- `openai.lib._pydantic.to_strict_json_schema` is a private path of the `openai` library. A test fails if
  a CrewAI upgrade (which pins `openai`) moves it.

## B3 step 7b, PR 5: the one retry, one trace line per HTTP request, the silent-repeat flag (2026-11-22)

Real mode (`AGENTS_MODE=real`) now has DL-43's one retry and writes one trace line for every HTTP
request. **Tested only against the fake OpenAI (PR 3): no real key, no real model, no paid call.**
Stand-in mode is unchanged and never builds an attempt log. The SAD side is recorded: H-073 (§4 "The
`trace` columns", "What a line costs", "How many requests one unit can send"), merged in #159.

| What | Where |
|---|---|
| **Which failures get the one retry**: the call's own timeout, no connection, a rate limit (429) and a server error (5xx). **Not retried**: a 400, 401 or 404 (the same request cannot succeed and each try costs money), 408 and 409, a bad *answer* (D5: the model is never asked again about a bad answer), and anything that is not a provider failure. CrewAI wraps what the `openai` client raised, so the check walks the chain of causes and lets the first `openai` error decide | `backend/runtime/crews.py` (`is_retriable`) |
| **The retry itself**: `MAX_ATTEMPTS` 2 (the call, and one more), `RETRY_WAIT_S` 1.0 s between them (tests set it to 0). A second failure is final: `model service` (T-RUN-2) | `backend/runtime/crews.py` (`run_step`) |
| **One trace line per HTTP request**, through CrewAI's `interceptor`: the model string the API returned, the stop reason, that request's own token counts, and for a request with no answer, why. Failed requests are traced *before* the error is raised, so their cost counts. Only the request that answered carries the output and the guardrail's verdict | `backend/runtime/attempts.py`, `agents.py`, `services/trace.py` |
| **Four new `trace` columns**, added at the end with defaults (`stop_reason`, `provider_error`, `cost_estimated`, `off_pinned_setting`). `init_db` adds them to an older database, so no file has to be deleted. Nothing renamed or dropped | `backend/db/schema.sql`, `db/connection.py` |
| **`attempt_n` counts HTTP requests** of a unit (1, 2, ...), not only our attempts | `backend/services/trace.py` |
| **What a request costs towards the US$2.50 cap**: usage data when the provider sent it; **0 for a 4xx**; for a 5xx, a timeout, no connection or an answer with no usage data, the **worst case** (input estimated from the request's size, plus an answer that fills the output limit), marked `cost_estimated` = 1 | `backend/runtime/model_settings.py` (`attempt_cost_usd`) |
| **Lateness is judged by the unit's last trace line** (it was the first). With one line per request, the first can be a failed attempt that was not late while the answering retry was | `backend/runtime/stages.py` |
| **The silent repeat is flagged**: a request whose settings differ from the pinned ones gets `off_pinned_setting` = 1. It does not fail the call or stop the run | `backend/runtime/agents.py` |
| **Audit**: every trace line still gets its `agent_output` entry, one to one. A request with no answer reads "no answer (provider error)" | `backend/services/trace.py` |
| **Tests**: `tests/tier1/test_attempt_trace.py` (the attempt log; each cost case; one line per request; retry and timeout lines; the verdict only on the last line; the silent repeat and its flag; at most four requests and two billed; the cost count; lateness by the last line; the table keeps its columns, an older database migrates, the trace stays append-only, a stand-in trace looks as before) and updates to `test_crews.py` and `test_model_settings.py`. At the end of PR 5 (#158's final CI): Tier 1 344 passed, 4 skipped; Tier 2 161 passed | `tests/tier1/` |

**How many requests one unit can send.** Our bound is two attempts, but CrewAI can add one repeat inside
each, so **up to four requests** and four trace lines for one unit. **At most two can be billed**, because
CrewAI repeats only after a 4xx and a 4xx costs 0. The worst-case run (12 rows, 5 extractions, every call
at its output limit) is US$1.49 with two billed requests per unit; with four billed it would be US$2.98,
above the cap. **The cap's safety rests on "a 4xx costs 0", not on the request count** (SAD §4).

**What the fake showed (findings):**

- **CrewAI's silent repeat is sticky.** When a 400 says the model refuses `reasoning_effort`, CrewAI sends
  the call again without it, reports success, and then leaves it out of **every later call in the same
  process**, with no setting to turn that off (`completion.py`, crewai 1.15.35). After the first one there
  is no rejection to see, so each later request is flagged instead. The SAD now lists "treat a call off
  the pinned reasoning setting as a failure?" among the decisions to take after the spike.
- A 429 is retried by us (once) and costs 0 both times, so a rate-limited unit adds no spend.

**Not done here, on purpose:**

- Showing `off_pinned_setting` and estimated cost in the spike and evaluation reports (`@qa.eng`, with B8).
- Stopping a retry when the cap is reached in the middle of a unit. Calls in flight finish (CR-017).
- Any real call. **Do not run real mode before the operator's spike.**

## B3 spike runner: the dry-run (PR 1) and the first real call (PR 2a to 2c) (2026-11-22)

The spike runner is one command, `python -m backend.runtime.spike`. It makes **one** real Stage A
extractor call (document `SRC-UCILAW`, the largest primary document) and records it. **Built and tested
against the fake OpenAI only (T-SPIKE-1 to 4): no real key was used and no real call has been made.** The
operator runs the first real call from their own terminal. Per CLAUDE.md, no real model call before the
stand-in happy path passed: it passed (#105).

| What | Where |
|---|---|
| **Dry-run (PR 1, #164).** The command without `--go`. Checks, in order: `AGENTS_MODE=real`, `SPEND_ACTIVITY=spike`, an extractor model ID, a usable key, a *primary* document, and fewer than 70 spike calls (EC-R10, counted from the trace). Then prints the model, the settings it would send, the input size, and the worst-case cost of one request and of one request plus its retry. Sends nothing, creates nothing, never prints the key. T-SPIKE-1 | `backend/runtime/spike.py` (`plan_first_call`) |
| **The spike's own run (2a).** A trace line must belong to a run, so the spike has its own git-ignored database, `data/spike.db`, and **one** run row (ACTIVE, `A_RUNNING`, real, `spike`). Asking again returns the same run, so `cost_so_far` adds up the whole spike. It never touches the app's database. T-SPIKE-2 | `spike.py` (`open_spike_run`) |
| **The call (2b).** `run_first_call` re-runs every dry-run check, then refuses if the money spent plus this call's worst case with its retry would pass the US$2.50 cap (CR-017), then calls the **same real-mode path the app uses** (`agents.extract_rows`: DL-43's one retry, one trace line per HTTP request, the guardrail). A bad answer is reported and not asked for again (D5). Each call is its own trace unit (`SRC-UCILAW#1`, `#2`, ...) because the trace refuses two lines with the same key. Importing `spike.py` loads no CrewAI; the real-mode code is imported inside the function. T-SPIKE-2 and 3 | `spike.py` (`run_first_call`) |
| **`--go` (2c).** Prints the plan and an **Endpoint** line, then asks the operator to **type the document ID**. Only an exact match sends. A wrong word, an empty line, closed or piped input all mean "not confirmed". Every refusal comes *before* the prompt. Then it prints, for each HTTP request: answered or not, tokens, cost (marked when estimated), stop reason, model asked and answered, `off_pinned_setting`, the provider error or guardrail text; then the run cost so far. The answer itself stays in the trace. T-SPIKE-4 | `spike.py` (`main`, `_go`, `format_result`) |

### How to run the first real call (operator, from your own terminal)

1. **`.env`** holds the real `OPENAI_API_KEY` and `LLM_MODEL_EXTRACT` (the DL-40 extractor ID; it lives
   only there, never in a committed file). **Leave `AGENTS_MODE=stand_in` in `.env`** and give real mode on
   the command line, as below, so that `make run` can never go real by accident.
2. **Dry-run first** (sends nothing):

   ```bash
   AGENTS_MODE=real SPEND_ACTIVITY=spike .venv/bin/python -m backend.runtime.spike
   ```

   Read `Model`, `Settings sent` (extractor: `reasoning_effort` none, `temperature` 0.0,
   `max_completion_tokens` 2000), `Worst case` and `Spike calls` (0 of 70). On 2026-11-22 the
   worst case was about **US$0.0012** for one request and **US$0.0024** with the retry (a quarter of a
   cent; about 1,750 input tokens); a Tier 1 test fails if it ever passes US$0.01. Accept the number your
   run prints before going on.
3. **Go**: the same command with `--go` at the end.
4. **Check the Endpoint line.** It must say **`OpenAI's default (api.openai.com)`**. If it shows anything
   else (a proxy, or `127.0.0.1`), **do not type the ID**: press Enter to cancel, and find the cause with
   `env | grep OPENAI`. The Endpoint line shows only the *shell's* `OPENAI_BASE_URL`; a value in `.env` is
   not read by the OpenAI client, so it neither changes the endpoint nor shows here.
5. **Type `SRC-UCILAW` and press Enter.** That is the one thing that sends a request.
6. **Read the result.** Exit code 0: a usable answer. 1: the call was made but the answer was not usable.
   2: nothing was sent. Copy the printout back to `@backend.eng` (it never contains the key). The trace line,
   with the full answer, is in `data/spike.db`.

**What you may see instead of a result**

| You see | It means | What to do |
|---|---|---|
| `REFUSED: ...` | A condition failed (mode, spend label, key, model ID, document, 70-call cap, cost cap). **Nothing was sent.** The text says which | Fix that one thing |
| `NOT CONFIRMED: nothing was sent.` | What you typed was not exactly the document ID | Run it again if you meant to go |
| **`ImportError: Unable to initialize LLM with model 'openai/...'`**, "did not match any supported native provider", "the LiteLLM fallback package is not installed" | **CrewAI does not recognise the model ID in `LLM_MODEL_EXTRACT` as an OpenAI model**, and its fallback (LiteLLM) is not installed on purpose. It is raised while the model client is *built*, before any request exists, so **nothing was sent and nothing was billed**. The dry-run cannot see it (it never builds the client). It shows as a Python traceback, not as `REFUSED:`, because it is not one of the expected refusals | Check the ID in `.env` for a typo, a space or a wrong name against DL-40. If it is exactly right, **stop and tell `@backend.eng`**. Do **not** `pip install litellm`: a new dependency is a SAD edit first (CLAUDE.md) |
| `Answer : NOT USABLE - invalid output` | The request was made and **billed**; the answer failed the guardrail. It is not asked for again (D5) | Send the printout; the raw answer is in the trace |
| `Answer : NOT USABLE - model service` | Both requests (the call and DL-43's one retry) got no answer. Each is traced and counted, with the worst case when no usage data came back (`ESTIMATED`) | Send the printout |
| `NOT USABLE - model service: ... HTTP 400 ... invalid_request_error` (about the schema) | OpenAI refused the `response_format` we sent (for the verifier, the two flag shapes). **A refused request costs nothing**, and nothing is repeated. **This is the stop rule: do not run it again** | Send the printout; the schema needs a change, not a retry |
| `NOT USABLE - model service: refused before sending: ...` | Our own guard stopped a request that was not a chat completion **before it was sent**. Nothing reached OpenAI and nothing was charged. It is a spike finding in its own right | Send the printout: the `Path` line says which request it was |
| `Off pinned setting : YES` | CrewAI repeated the call without `reasoning_effort` after a 400 (H-064 c). The call is *not* a clean run of the pinned settings. **Check the request first:** a YES on a request with 0 tokens, no model and no stop reason is not a model call (on the first real call it was CrewAI's pre-flight; see "B3 spike finding"). That cannot happen after step A of the fix | Report it; this is what the spike is meant to find out |

**Do not delete `data/spike.db` to "start over".** It also resets the count of 70 calls, and EC-R10 says a
further call needs a recorded operator decision.

**Not done here, on purpose:**

- Only the **first extractor call** is in the runner. The verifier and judge calls, the call plan up to 70,
  and the spike report (`@qa.eng`, with B8) come later and are not built.
- The dry-run cannot tell an unrecognised model ID from a good one (see the `ImportError` row).
- If the database cannot be written *after* a request was sent, the command stops with that error: the
  request may have been billed without a trace line. The 70-call and cost caps would then undercount.
- Handoff H-075 asks `@project.mgr` to put these steps in `setup.md` (not mine to edit).

### How to run the verifier and judge calls (operator, from your own terminal)

The same command, with `--step verify` or `--step judge`. Both are measured on a **fixed input**: the
answer-key row of `SRC-UCILAW-P3` (where the planted conflict C-1 sits), so every run sees the same row.

| | Verifier | Judge |
|---|---|---|
| `.env` needs | `LLM_MODEL_VERIFY` (DL-40: `gpt-5.6-terra`) | `LLM_MODEL_JUDGE` (DL-40: `gpt-6.1-terra`) |
| Settings sent | `reasoning_effort` low, 2000 tokens, **no temperature** | `reasoning_effort` medium, 4000 tokens, **no temperature** |
| What it carries | the row and its quote, the code's quote check, and all 13 paragraphs (primary and secondary) | the approved row, 7 fund facts (ID, fact, value) and 1 event. Never the "Decides" column, flags or other verdicts |
| You type exactly | `verify SRC-UCILAW-P3` | `judge SRC-UCILAW-P3` |
| The result says | **CAUGHT** or **MISSED** for C-1 (a miss points at DL-26); any internal flag is a **false alarm** | **CORRECT** or **WRONG** against the answer key (`applies`, citing `FACT-01`); a wrong verdict is a finding, not a failure |

1. Dry-run first: `AGENTS_MODE=real SPEND_ACTIVITY=spike .venv/bin/python -m backend.runtime.spike --step verify`
   (or `--step judge`). Read the model, the settings, the worst case and `Spike calls`.
2. Then the same command with `--go`. Check that the Endpoint line says `OpenAI's default (api.openai.com)`,
   and type the exact words from the table. The other step's words do not confirm; neither does the bare row ID.
3. **Stop rule (operator, 2026-11-22):** after **any 400**, **`Off pinned setting : YES`**, **`Stop reason : length`**
   or an **invalid answer**, stop and send the printout. No further call until you decide. A 400 costs US$0.
   `Stop reason : length` is the reasoning models' own risk: reasoning tokens count against the token limit.
4. Each request is one trace line and takes one of the 70 slots. Each call is its own unit
   (`SRC-UCILAW-P3#1`, `#2`, numbered per step); all steps share the one spike run.

## B3 spike finding: the first real call sent two requests (RUN-20261122-1, 2026-11-22)

**Summary.** The operator's first real call (`SRC-UCILAW#1`, `gpt-6-luna`) gave a valid answer (3 rows)
for US$0.0003, but the trace holds **two** lines. Line 1 was **not a model call**. It was CrewAI's own
pre-flight request, `POST /v1/responses/input_tokens`, which asks OpenAI to count the prompt's tokens. Our
attempt log recorded it as if it were an answer. Fixed on branch `backend-eng/spike-preflight-fix`.

**What `data/spike.db` holds** (the trace is append-only, so these lines stay as they are):

| | Line 1 (`attempt_n` 1) | Line 2 (`attempt_n` 2) |
|---|---|---|
| What it really was | CrewAI's pre-flight token count | the model call |
| Tokens in / out | 0 / 0 (a count request has no usage data) | 1500 / 360 |
| Model returned, stop reason | none, none | `gpt-6-luna`, `stop` |
| Settings recorded | `{}` (the body carried none) | `reasoning_effort` none, `temperature` 0.0, `max_completion_tokens` 2000 |
| Duration | 1543 ms | 4437 ms |
| `cost_usd` | **0.0011342, estimated** (a false alarm, see below) | 0.00033 (from usage data) |
| `off_pinned_setting` | **1** (a false alarm, see below) | 0 |

The run's `cost_so_far` is US$0.0014642. The model call alone cost US$0.00033.

**How it was identified, and how sure we are.** Read-only, with no second real call. (1) The stored line
has exactly the shape of a non-model request that got a 200: no settings, no model, no stop reason, no
usage. (2) CrewAI 1.15.35 sends that request: `Agent.respect_context_window` is true by default, and
before each call it counts the prompt's tokens (`completion.py`, `get_input_tokens_count`). It skips the
request when the server is not `api.openai.com` (`_on_compatible_server`), which is why no test saw it.
(3) A local reproduction against the fake, with CrewAI made to believe it was on OpenAI, produced the same
line: cost 0.0011343 against 0.0011342, `estimated`, `off_pinned_setting` 1, no model, no stop reason. **The
real request's body is not stored**, so this is inference plus reproduction, not a recording. The
confirmation call after the fix should show one line.

**What did not go wrong.**

- **The pinned settings were accepted.** Line 2 carried `reasoning_effort` none, `temperature` 0.0 and
  `max_completion_tokens` 2000 and got a 200. No 400, so **no silent repeat**, and nothing was dropped for
  later calls. This is the first real evidence that `gpt-6-luna` accepts them.
- The answer was valid, and the model string returned was `gpt-6-luna` (the alias; no dated snapshot).

**What went wrong, and what it means.**

- **A false cost.** A 200 with no usage data is treated as "unknown", so the worst case of a model call was
  charged for a request that is not one. Too high, never too low, so the cap was never at risk.
- **A false flag.** `off_pinned_setting` is "the request did not carry the pinned settings". A count
  request never does, so it was marked YES. It is **not** a silent repeat.
- **Two of the 70 call slots used for one model call.** The cap counts trace lines (`real_calls_made`).
- **A broken rule.** SAD §2 "Counting every request" says one unit sends exactly one request, except our one
  retry and CrewAI's silent repeat. The interceptor saw the extra request, as designed, but nothing stopped
  it. H-076 tells `@system.arch`.
- **Billing of the count request is not verified.** The operator should look at the OpenAI usage page: one
  chat request of 1500 in and 360 out is what the trace says.

**Why no test saw it.** Every test talked to a fake on `127.0.0.1`. CrewAI does some things only when it
believes the server is OpenAI itself, and a fake on another host cannot show them. The first real call was
the first run on `api.openai.com`. There may be other behaviour like this; step D (below) refuses any
request that is not a chat completion, so the next one is stopped instead of discovered.

**The fix, in steps (branch `backend-eng/spike-preflight-fix`).**

| Step | What | Where |
|---|---|---|
| A (`bc0b320`) | `respect_context_window=False` on the agent: no pre-flight request, and no chance that CrewAI summarises our prompt on its own | `backend/runtime/crews.py` (`build_crew`) |
| B (`fcd2a69`) | **T-REQ-1**: the `as_openai` fixture makes CrewAI behave as if the fake were `api.openai.com`; the fake answers the count endpoint; four tests (one unit is one request; the fixture is not an empty shell; the spike call is one trace line and one slot; a retry adds a chat request and no count request). With A reverted, 3 of the 4 fail | `tests/conftest.py`, `tests/fake_openai.py`, `tests/tier1/test_one_request.py` |
| C | This section, H-076, and the note below | `backend.md`, `handoffs.md` |
| D (`9479f23`) | **T-REQ-2.** The interceptor refuses any request that is not `POST .../chat/completions` **before it is sent**, and writes it to the attempt log first, so the trace shows what was stopped. A refused request costs 0, is not an estimate, is not flagged `off_pinned_setting`, and is never retried. New `trace` column **`request_path`** (the URL path; additive, default empty). 17 tests; with the guard switched off 4 fail | `attempts.py`, `crews.py`, `model_settings.py`, `agents.py`, `trace.py`, `schema.sql`, `connection.py`, `spike.py`, `tests/tier1/test_request_guard.py` |

**What D does, and one thing it taught us.**

- **CrewAI swallows a failed pre-flight.** It wraps its token count in its own `try/except` and falls back to
  a local estimate. So if the guard ever stops that request, CrewAI shrugs it off and **still makes the real
  call**: the unit succeeds, the stopped request never leaves the machine, and the trace has a line for it
  (cost 0, `provider_error` "refused before sending: POST /v1/responses/input_tokens is not a chat completion",
  `request_path` `/v1/responses/input_tokens`). If instead the *chat request itself* were stopped, the unit
  fails once with that reason ("model service") and is **not** retried: DL-43's retry is for provider
  failures, and a refusal would only be refused again.
- **A stopped request still takes a trace line, so it still takes one of the 70 call slots**, at no cost.
  The alternative (not counting it) would need a special case in the cap's count; the conservative choice was kept.
- **The new column was rehearsed on a copy of the real `data/spike.db`.** `init_db` adds `request_path` the next
  time the spike opens the file. Every existing value, line 1 included, is unchanged; both old lines get an
  empty path ("not recorded"), the trace is still append-only, and the original file was not touched by the test.
- The bound in "How many requests one unit can send" is unchanged: a stopped request is never sent, so it
  is not one of the requests that can be billed.

**For the spike report (note for whoever writes it; `@qa.eng`, with B8).**

- **`SRC-UCILAW#1` stays as it is, as the honest record.** Do not edit or delete the two lines (the trace
  is append-only, and the operator decided on 2026-11-22 to leave them). Explain it in one sentence:
  **"One model call plus one pre-flight token-count request sent by CrewAI; 2 of the 70 call slots were used."**
  The 70-call count shows 2 of 70 used and stays that way. Calls made after the fix use one slot each.
- **Its cost and its `off_pinned_setting` flag on line 1 are false alarms.** Report the model call's
  figures from line 2: US$0.00033, 1500 in, 360 out, stop reason `stop`, not off the pinned setting. The
  run's US$0.0015 overstates the model call's cost by about US$0.0011.
- **Do not count line 1 as an off-pinned call** when counting how often CrewAI repeated a call without
  `reasoning_effort` (SAD, "Decisions to take once the spike has shown the result"). On this run it
  happened zero times. Judge a line by its request, not only by its flag: no model returned, no tokens and
  no stop reason means it was not a model call.
- Report that the first real call found a request the fake could not show, and what stops it now (steps A,
  B and D). That is a spike result in its own right.

## B3 spike finding 2: the first real verifier call caught the conflict but failed the schema (2026-11-22)

**Summary.** The operator's first real verifier call (`gpt-5.6-terra`, row `SRC-UCILAW-P3`, unit
`SRC-UCILAW-P3#1`, trace line 4) **accepted the pinned settings and caught the planted conflict C-1 in
substance**, but our validator refused the answer: **schema-pass on the first attempt: 0 of 1.** The
spike's stop rule fired (an invalid answer); no further call was made. Fixed by sending the verifier's
flag as two shapes (branch `backend-eng/spike-flag-shapes`, #170, T-WIRE-1).

**Update, 2026-11-23: the re-run after the fix passed.** The operator's second verifier call
(`SRC-UCILAW-P3#2`, trace line 5) **returned a valid answer and caught C-1**, and **OpenAI accepted the
nested `anyOf`**. See "The re-run" below. First-attempt schema-pass for the verifier is now **1 of 2**.

**What the trace holds** (append-only, so it stays as it is):

| | |
|---|---|
| Request | one, `POST /v1/chat/completions`; no 400, no retry; `off_pinned_setting` 0 |
| Settings | `reasoning_effort` low accepted; no temperature sent; `max_completion_tokens` 2000 |
| Size, cost, time | 1723 in, 351 out (hidden reasoning is inside the 351); **US$0.0077**; 5.1 s; stop reason `stop` |
| Model returned | `gpt-5.6-terra` |
| Count | **4 of 70** call slots used; run cost US$0.0095 |

**What the model sent.** One cross-source flag: it cited `SRC-PRACT-P1` with a quote copied word for word
("within four months of financial year-end") and explained the four-versus-six-month difference. It also
wrote `field` = `offset` and `row_value` = `6 months`, which belong to an **internal** flag only. Our `Flag`
check says a cross-source flag has `other_paragraph_id` and `other_quote` and **no** `field`, `row_value`
or `quote_says`, so the answer was refused as invalid output.

**Why it happened (three things together, none visible against the fake).**

1. **Strict mode requires every key on every object.** The schema we sent listed all seven flag keys as
   required, with `null` allowed on the five optional ones. A JSON schema cannot say "an internal flag has
   no `other_quote`", so the model had to choose a value for keys that did not apply.
2. **The prompt never says "leave the others null".** The card's expected output says a cross-source flag
   "also has" its two keys; its worked example shows a flag with only its own keys, which is not what the
   strict format asks for.
3. **The validator is right to refuse it.** The fake answered with our own stand-in flags, which carry
   only their own keys, so no test could have shown this.

**The fix (operator's choice: option 1 of 3, 2026-11-22).** `backend/runtime/wire_schema.py` sends the flag
as `anyOf` two shapes, built from `Flag` itself so the value sets cannot drift:

- **InternalFlag**: `flag_type` (`internal`), `explanation`, `field` (`frequency`, `anchor` or `offset`),
  `row_value`, `quote_says`;
- **CrossSourceFlag**: `flag_type` (`cross_source`), `explanation`, `other_paragraph_id`, `other_quote`.

Each shape lists exactly its own keys, all required, none nullable, so the model cannot mix them. **Not
changed:** the validator, the card text and worked example, the stored flags, and the extractor's and the
judge's schemas (checked byte for byte against their schemas from before the change). The two options not
taken: wording the prompt "set the others to null" (relies on the model obeying, and the card is
`@system.arch`'s), and a validator that strips the extra keys (loosens CR-003 and D5, and would hide the
very thing the spike measures).

**Tests (T-WIRE-1, fake only).** The shapes; the schema and the validator agree, checked with a real
JSON-Schema checker (what the schema allows the validator accepts; the first call's mixed flag is refused
by both); the validator still refuses and records a mixed flag that gets through anyway; our own stand-in
answers pass the schema; a verifier request carries the two shapes. With the fix switched off 9 tests
fail; with one shape damaged 4 fail.

**The re-run (2026-11-23, `SRC-UCILAW-P3#2`, trace line 5): passed.** Run by the operator after #170 merged.
Read from `data/spike.db`, opened read-only; the printout and the database agree.

| | Call #1 (before the fix) | Call #2 (after the fix) |
|---|---|---|
| Answer | **invalid**: a cross-source flag carried `field` and `row_value` | **valid**: exactly the cross-source keys (`flag_type`, `explanation`, `other_paragraph_id`, `other_quote`) |
| Planted conflict C-1 | cited `SRC-PRACT-P1` (but refused for its shape) | **CAUGHT**: cites `SRC-PRACT-P1`, quote word for word |
| False alarms | n/a | none |
| Request | one, `/v1/chat/completions` | one, `/v1/chat/completions` |
| Tokens in / out | 1723 / 351 | 1721 / 185 |
| Cost | US$0.0077 | **US$0.0057** |
| Duration | 5.1 s | 3.9 s |
| Settings | `reasoning_effort` low, no temperature, 2000 tokens; `off_pinned_setting` 0; stop reason `stop` | the same |

- **OpenAI accepted the nested `anyOf` in strict mode.** This was the one thing the tests could not prove.
  There was no 400 and no `provider_error`.
- The two calls' totals: **5 of 70** call slots used; the line costs add up to the run's `cost_so_far`
  (US$0.0151); nothing was estimated.
- One answer is one data point. The second answer was shorter (185 output tokens against 351), and that
  is not yet a trend. The output tokens include the model's hidden reasoning, which the trace cannot
  separate.
- **What this does not decide:** the DL-26 bake-off. It needs the runs on all three planted conflicts
  (C-1, C-2, I-1) for both candidate models, five times each. This is one valid answer on C-1.

**For the spike report (note for whoever writes it; `@qa.eng`, with B8).**

- **Record the verifier's two calls honestly.** Call #1: accepted `reasoning_effort` low; **caught C-1 in
  substance but failed the schema check**; US$0.0077. Call #2, after the fix: **valid, C-1 caught, no
  false alarm**; US$0.0057. **First-attempt schema-pass: 1 of 2**, and say why call #1 failed. Do not
  describe call #1 as a miss: the answer cited the right paragraph with a verbatim quote. **5 of 70** slots.
- **The DL-26 bake-off is not decided by these calls.** It needs the planted conflicts C-2 and I-1 and
  the other candidate model, five runs each. Count call #1 in "share of calls whose output passes its
  schema on the first attempt".
- Say what changed afterwards (two flag shapes) and that later verifier lines were sent a different
  `response_format` from this one. The prompt version did not change; the schema did.
- **The current numbers** (slots, cost, schema-pass for all three roles) are in "B3 spike finding 3"; use
  those, not the ones above.

## B3 spike finding 3: the first real judge call, and where the three roles stand (2026-11-23)

**Summary.** The operator's first real judge call (`gpt-6.1-terra`, row `SRC-UCILAW-P3`, unit
`SRC-UCILAW-P3#1`, trace line 6, run 2026-11-23 13:48 UTC) **passed**: a valid answer, the verdict the
answer key expects (**`applies`, citing `FACT-01`**), `reasoning_effort` medium accepted, one request, no
400. Read from `data/spike.db`, opened read-only; the printout and the database agree.

| | |
|---|---|
| Answer | exactly the four verdict keys; `missing_information` is `""`, as the worked example shows |
| Verdict | `applies`, citing `FACT-01`: **CORRECT** against the answer key |
| Request | one, `POST /v1/chat/completions`; `provider_error` empty; stop reason `stop`; 3.9 s |
| Settings | `reasoning_effort` medium accepted; no temperature sent; `max_completion_tokens` 4000; `off_pinned_setting` 0 |
| Size and cost | 988 in, **62 out**, **US$0.0013**; not estimated |
| Model returned | `gpt-6.1-terra` |

- **The cost estimate was too high.** The plan said US$0.004 to 0.016; the call cost US$0.0013. The printed
  worst case (US$0.0210) is a ceiling, not a forecast.
- **62 output tokens in total.** Hidden reasoning tokens are inside that number and the trace cannot
  separate them, so the only fair reading is that this call reasoned very little on an easy row. One
  data point; a harder row may differ.

**A precaution, untested: `minItems` was dropped from the judge's schema** (#172, `d12d2f3`). The judge's
`cited_fact_ids` carried `minItems: 1`. OpenAI's own Structured Outputs guide lists `minItems` both as
supported and as not yet supported, and developer-forum reports show real rejections, so it was removed
before the first real judge call, as `minLength` and `maxLength` already are. **We never sent it, so we do
not know whether OpenAI would have refused it.** Our Pydantic check still refuses an empty list of cited
IDs, so nothing was lost. Only the judge's schema changed, and by that one keyword.

**Where the three roles stand** (every real call so far, from `data/spike.db`):

| Role | Model | Pinned setting accepted? | Calls | Schema pass on the first try | Real cost per call |
|---|---|---|---|---|---|
| Extractor | `gpt-6-luna` | `none`, temperature 0: **yes** | 2 | **2 of 2** | about US$0.0003 |
| Verifier | `gpt-5.6-terra` | `low`, no temperature: **yes** | 2 | **1 of 2** (call #1: mixed flag, fixed by two shapes) | US$0.0057 to 0.0077 |
| Judge | `gpt-6.1-terra` | `medium`, no temperature: **yes** | 1 | **1 of 1** | US$0.0013 |

**All three models have accepted their pinned settings, so far.** There was no 400 on `reasoning_effort` and
no silent repeat by CrewAI on any real call. The one `off_pinned_setting` line in the database is the
first call's pre-flight request, a false alarm (finding 1). **Caveat: this is one or two calls per role**, so
the honest wording is "so far", not "proved". It bears on SAD "Decisions to take once the spike has shown the
result", decision 2 (H-079). One more point in its favour: every spike command is a new process, and
CrewAI's memory of a refused setting lives only inside a process, so a model that refused
`reasoning_effort` would be refused again, and flagged, on each command.

**Numbers for the spike report (supersede the numbers in "B3 spike finding" and "B3 spike finding 2").**

- **Slots: 6 of 70** used (one is the first call's pre-flight line). **Run cost: US$0.0164** of the US$2.50 cap.
  The line costs add up to the run's `cost_so_far`.
- The SAD asks for each role's call on the demo inputs **5 times**; so far: extractor 2, verifier 2, judge 1.
  The verifier bake-off (DL-26: both candidate models on C-1, C-2 and I-1, five runs each) has not started.
- **First-attempt schema-pass:** extractor 2 of 2, verifier 1 of 2, judge 1 of 1; **4 of 5** in all. Say why
  verifier call #1 failed (finding 2).
- **Cost and time per call, so far:** extractor about US$0.0003 and 3.7 to 4.4 s; verifier US$0.0057 to 0.0077 and
  3.9 to 5.1 s; judge US$0.0013 and 3.9 s. All well under the cost cap and the call timeouts (60 to 90 s).
- **Not decided yet:** the verifier model (DL-26, needs the bake-off); the stage time limits (they need the
  five-run figures).

## Pattern Decision compliance

No agent loop, no retrieval over live state, no side-effecting tool. **Stand-in mode (the default)
builds no model client and never loads CrewAI** (T-MODE-1). **Real mode builds one one-agent crew
per unit** behind the same three functions: no tools, no delegation, no memory, `max_iter` 1, one
task, and a model is never asked again about a bad answer (D5). Real mode refuses to start with no
model ID or no key, and has not been run: it is tested against the fake OpenAI only. The stand-in answers (`backend/stand_in/`) are
hand-written from the mock paragraphs, carry no answer-key IDs (`OBL-`, `C-1`, `I-1`, `AMD-`) or
notes, are never placed in a prompt, and pass the same guardrails as a model's output. The loaders
never read the "Decides" column, test notes or amendments (T-LEAK-1, loader half).

## Known gaps

- An evaluation run with the demo-row switch on is not refused yet: there is no evaluation run
  before the evaluation runner (**B8**, EC-R7).
- `retry_run` is a stub (**B13b**). The per-call timeout and its one automatic retry (D1, DL-43,
  T-RUN-2) are built (step 7b PR 5) and tested against the fake OpenAI; a stand-in call cannot
  time out. The run status page shows the cost but not yet the "over US$2" warning (CR-017); the
  warning's wording and place are `@ux.designer`'s.
- **Step 7b is built; no real call has been made** (plan approved 2026-11-19; PRs 1 to 5 merged,
  this documentation is PR 6): CrewAI is installed with its outside connections off (PR 1), per-role
  model settings and token limits (PR 2), a fake OpenAI for tests (PR 3), the crews behind the three
  agent functions (PR 4), and DL-43's one retry with one trace line per HTTP request (PR 5). **Real
  mode must not be run before the operator's spike.** The spike runner for the **first extractor
  call** is built (PR 1 and 2a to 2c, see "B3 spike runner") and tested against the fake only; the
  operator makes the first real call. Still to build: the runner's verifier and judge calls and the
  call plan up to 70 (DL-40 is pinned and the role harness has its call caps), and the reports that
  show `off_pinned_setting` and estimated cost (`@qa.eng`, B8).
  Open for after the spike: "treat a call off the pinned reasoning setting as a failure?" (SAD
  Production Shape, "Decisions to take once the spike has shown the result").
- **MVP limitation (B4, operator 2026-11-19): every logged event applies to every event-based
  rule.** The date engine anchors each `event_awareness` / `event_occurrence` rule on every event in
  the fund's event log; it does not read the log's "Obligation" column (that column names the
  answer, CR-016). The MVP has one event and one such rule, so the result is right. A real system
  would link each event to its obligation explicitly.
- T-W04-6 (the verifier claims "quote ok" for a row code failed) has no test: the verifier's schema
  has no such field, so the claim cannot reach the store, and the quote-check result is code's
  alone. Revisit with the real verifier (B3 spike).
- No Pydantic form models refusing unknown fields. CI checks lint but not formatting yet (see "B1
  follow-up: CI").
- The pages read the H-036 view fields (V-1 to V-12). The interim lookups in
  `parts/lookups.html` are `@frontend.eng`'s to delete.
- A row's posted `version` is stored, not compared (the SAD names `VERSION_MISMATCH` for the run only).
- Starlette 1.x prints a deprecation warning for `httpx` in the test client; harmless.

## Sources

- `project-context/1.define/sad.md`: Build card (incl. "Build approach", Never row), Order of work,
  §4 Backend (routes, refusal codes, failure reasons, table list, "Data model: the happy path",
  "Sign-in and secrets").
- `project-context/1.define/prd.md` (loaded per persona instructions; nothing taken beyond the SAD).
- `project-context/2.build/scaffold-plan.md` §1, §3, §5; `ux.md` workflow, §1.3, §1.5, §1.7, §10;
  `setup.md`.
- `.cursor/rules/adapter-crewai.mdc` (its CrewAI items apply from B3).

## Assumptions

- The stub function names follow the SAD §4 routes (Open Question 1).
- The operator's request for stubs that move run states overrides the Build card's "no state
  logic" wording for the shell only (Open Question 2).
- `trace` was built in B3 step 6 with the §4 columns (H-035).
- The templates and CSS are `@frontend.eng`'s (B5, done: `frontend.md` §9). The backend sends the
  view fields (H-036) and the refusal object; the pages decide nothing.

## Open Questions

1. **Function names.** *Answered 2026-11-16: accepted; SAD to own them (H-035).* The SAD has no B2 function names or signatures. The names above are
   derived from the §4 routes. Confirm them, or have `@system.arch` record them in the SAD.
2. **Spec drift: stubs with state moves.** *Answered: accepted for the stubbed UI; Build card update in H-035.* The Build card says "a stub holds no check and no state
   logic" (read-only stubs). This shell's stubs move status and phase (operator request,
   2026-11-16). Accept, or hand to `@system.arch` to update the Build card row.
3. **Verdict and calendar IDs.** *Answered: accepted; SAD to record them (H-035).* The SAD gives no scheme for verdict or calendar IDs; the shell uses
   `VER-<run>-<n>` and `CAL-<run>`.
4. **Env names.** Only the §4 names the shell needs were added. *Partly answered in B3 step 6:*
   the stage limits now use the SAD's `STAGE_TIME_LIMIT_A`, `_B`, `_C` (`.env.example` renamed
   from `STAGE_LIMIT_*_S`). The `CALL_TIMEOUT_*_S` rename waits for the real calls (B3 spike).

5. **Order of checks.** Where the SAD lists several codes for one action, the first that applies
   wins: ended → wrong phase → stale page → the action's own checks; for a decision, already
   decided comes before no answer / a bad answer. Confirm or change.
6. **Three sentences ux.md does not give** (marked PROPOSED in `refusals.py`): `GATE_INCOMPLETE`
   for exactly one item ("1 rule is still undecided…"), and `RUN_STAGE_RUNNING` when the review is
   at a *different* gate rather than working ("This step is not open for decisions right now…").
   Handed to `@ux.designer` (H-049).
7. **`typed` for the abandon box.** The V-12 contract says `typed` is `{field: text}`; the abandon
   textarea in `review_status.html` prints `refusal.typed` whole. Handed to `@frontend.eng` (H-048).
8. **Rule 9 in B2.** Built here at the operator's request; the SAD's order puts it in B3. Handed to
   `@system.arch` (H-047) so the SAD says so.

## Audit

- 2026-11-16 · persona `backend-eng` · actions `develop-be`, `implement-endpoint`, `stub-nonmvp`,
  `document-backend` · `AAMAD_TARGET_RUNTIME=crewai` (CrewAI not installed or imported yet) ·
  `AGENTS_MODE=stand_in` · built the app shell above in six commits on `b1-app-shell`; 42 tests
  pass (18 new Tier 1 tests plus the existing answer-key checks). No diagram needed. `sad.md`,
  `ux.md` and the frozen Netlify page not edited. No model call. LLM, temperature and max-token
  controls: none resolved (no model in the shell).
- 2026-11-16 · persona `backend-eng` · `sync-docs` · proposal made to the operator for `setup.md`
  and `README.md` (Project structure, Prerequisites); not written, waiting for approval.
- 2026-11-16 · persona `backend-eng` · `sync-docs` · operator approved all three items; applied to
  `setup.md` (dependency pins, pause-variable sentence) and `README.md` (Prerequisites, Project
  structure). Operator answered Open Questions 1 to 4: names, stub rule, ID schemes accepted;
  handoff H-035 asks `@system.arch` to record them in the SAD and to list the `trace` columns
  before B3.
- 2026-11-17 · persona `backend-eng` · actions `develop-be`, `implement-endpoint`, `document-backend`
  · `AAMAD_TARGET_RUNTIME=crewai` (CrewAI still not installed or imported) · `AGENTS_MODE=stand_in`
  · H-036: view fields V-1 to V-11 added to the stub view functions in six steps (PRs #68 to #73);
  86 tests pass. V-12 left for B2/B7. Review-number rule and ended-time source are the persona's
  choices (above). No model call. LLM, temperature and max-token controls: none resolved (no model
  in the shell). No diagram needed. `sad.md`, `ux.md`, `frontend.md` and the frozen Netlify page
  not edited.
- 2026-11-17 · persona `backend-eng` · `sync-docs` · proposal D1 to D5 for `frontend.md`
  (`setup.md` and `README.md` had nothing stale); operator approved all five and they were applied
  to `frontend.md`. Handoffs raised: H-045 (FYI to `@frontend.eng`), H-046 (`@system.arch`: write
  the review-number rule and the audit-log "ended at" source into the SAD). H-036 Outcome filled in.
  Snapshots not re-recorded.
- 2026-11-17 · persona `backend-eng` · actions `develop-be`, `implement-endpoint`, `document-backend`
  · `AAMAD_TARGET_RUNTIME=crewai` (CrewAI still not installed or imported) · `AGENTS_MODE=stand_in`
  · **B2** on `b2-gates-and-checks` in two commits: V-12 refusal object and the same-page handling,
  the run, decision, gate, publish and decline checks, Rule 9, the start-up rule. 138 Tier 1 and
  Tier 2 tests pass (up from 90). No model call. LLM, temperature and max-token controls: none
  resolved (no model in the shell). No diagram needed. `sad.md`, `ux.md`, `style-note.md` and the
  frozen Netlify page not edited. Snapshots not re-recorded: the visual check still fails on the same
  18 as H-036; `tests/visual/visual.spec.js` was changed (driving steps only) so a review can get
  through the new checks.
- 2026-11-17 · persona `backend-eng` · `sync-docs` · after B2: operator approved 4 items for
  `frontend.md`; applied on the B2 branch (PR #75). One more stale mark proposed (page 2 `refusal`).
  Handoff H-050 gives `@project.mgr` the checkpoint estimate. Stage time limit and Pydantic
  unknown-field refusal deliberately not started (operator).
- 2026-11-18 · persona `backend-eng` · actions `develop-be`, `define-runtime` (stand-in only),
  `document-backend` · `AAMAD_TARGET_RUNTIME=crewai` (CrewAI still not installed or imported) ·
  `AGENTS_MODE=stand_in` · **B3 steps 1 to 5** in five PRs (#92 to #95, and step 5's): loader, quote
  check, schemas and guardrails, stand-in answers and agent functions, stages A and B wired. 206
  tests pass. Operator decisions above; handoffs H-052 (`@system.arch`) and H-053
  (`@frontend.eng`). Visual check: **16 snapshots differ** (the 10 from H-051 and 6 new, listed in
  H-053), none re-recorded; the other 12 match. No model call. LLM, temperature and max-token
  controls: none resolved (no model yet). No diagram needed. `sad.md`, `ux.md` and the frozen
  Netlify page not edited.
- 2026-11-18 · persona `backend-eng` · `sync-docs` · after B3 step 5: operator approved all 3 items
  and they were applied on the PR #96 branch: `frontend.md` (agent functions replace `run_unit`),
  `backend.md` V-5 (counts from stored data) and the B2 "Stored data" row (stand-in answers;
  placeholder dates until B4). Spec drift (SAD §4 `run_unit` row) is already in H-052.
- 2026-11-18 · persona `backend-eng` · actions `develop-be`, `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI still not installed or imported) · `AGENTS_MODE=stand_in` ·
  **B3 step 6**: `trace` table and service, cost count, cost cap, stage timer, `fail_stage` under
  one write lock, `STAGE_TIME_LIMIT_*` settings, `run_unit` deleted (H-052 outcome). 218 tests pass
  (12 new, incl. T-RUN-6 and T-RUN-8; the timer tests passed 15 runs in a row). Visual check: the
  same 16 snapshots differ as after step 5 (H-053), none re-recorded. No model call. LLM,
  temperature and max-token controls: none resolved (no model yet). No diagram needed. `sad.md`,
  `ux.md` and the frozen Netlify page not edited.
- 2026-11-18 · persona `backend-eng` · `sync-docs` · after B3 step 6: operator approved all 4 items:
  `setup.md` env table and Open Point (stage limit names; operator kept the rename), `backend.md`
  stub table (`run_unit` deleted) and Assumptions (`trace` built). Operator also accepted: a trace
  line that cannot be written fails the unit as "invalid output"; stand-in `prompt_version` is a
  hash of the answer file until B3 step 7.
- 2026-11-18 · persona `backend-eng` · actions `develop-be`, `define-runtime` (YAML only),
  `document-backend` · `AAMAD_TARGET_RUNTIME=crewai` (CrewAI still NOT installed: step 7b waits
  for the operator) · `AGENTS_MODE=stand_in` · **B3 step 7a**: `backend/config/agents.yaml`,
  `tasks.yaml`, `examples/`; `backend/runtime/prompts.py`, `harness.py`. 233 tests pass (15 new:
  T-LEAK-1 prompt half and the harness cap in Tier 1; T-PROMPT-1 and T-EXAMPLE-1 in Tier 2). No
  model call; no model ID chosen. LLM, temperature and max-token controls: none resolved (DL-40
  pending). No diagram needed. `sad.md`, `ux.md` and the frozen Netlify page not edited.
- 2026-11-18 · persona `backend-eng` · `sync-docs` · after B3 step 7a: Doc sync: no updates.
- 2026-11-18 · persona `backend-eng` · operator decision: step 7b postponed until just before the spike; dry-run findings recorded above (crewai==1.15.35, 117 packages, pydantic 2.14.3 to 2.12.5, telemetry off with a test).
- 2026-11-19 · persona `backend-eng` · actions `develop-be`, `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI not installed; step 7b postponed) · `AGENTS_MODE=stand_in` ·
  **B13a**: the failure demo now runs through the stand-in extractor hook (CR-033); T-DEMOFAIL-1 in
  one Tier 1 file. 239 tests pass (6 new). Visual check: the same 16 snapshots differ as after B3
  step 5 (H-053), none new, none re-recorded. No model call. No diagram needed. `sad.md`, `ux.md`
  and the frozen Netlify page not edited.
- 2026-11-19 · persona `backend-eng` · `sync-docs` · after B13a: Doc sync: no updates.
- 2026-11-19 · persona `backend-eng` · actions `develop-be`, `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI not installed; step 7b postponed) · `AGENTS_MODE=stand_in` ·
  **B4**: the date engine (`backend/domain/dates.py`), its config (holidays, open convention OQ-7,
  horizon, year end), event dates for the engine, stage C on the engine (`shell_data.py` deleted),
  the G1 OQ-7 note, the why words. 255 tests pass (16 new; EC-007 gives the answer key's 22 entries
  exactly); `tests/test_answer_key.py` passes. Visual check: the same 16 snapshots differ (H-053,
  H-054), none new, none re-recorded; the visual script's G1 choices follow answer key §5 (H-054).
  No model call. No diagram needed. `sad.md`, `ux.md` and the frozen Netlify page not edited.
- 2026-11-19 · persona `backend-eng` · operator decisions on B4: choices 1 to 4 accepted; choice 2
  recorded under Known gaps as an MVP limitation. `sync-docs`: item 1 approved and applied (B2 table
  "Stored data": stage C's dates are the date engine's).
- 2026-11-19 · persona `backend-eng` · actions `develop-be`, `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI not installed; step 7b postponed) · `AGENTS_MODE=stand_in` ·
  **B7** (operator asked for it straight after B4; B5 is still in progress with `@frontend.eng`):
  `config/demo/planted-row.yaml` replaces the temporary demo rule; `DEMO_ROW_NOT_APPROVABLE` first
  among the approve checks; "Approval blocked" from the audit log. 269 tests pass (14 new: T-DEMO-1,
  T-DEMO-2). Visual check: the same 16 snapshots differ (H-053, H-054, H-055), none new, none
  re-recorded. Handoff H-055 to `@frontend.eng`. No model call. No diagram needed. `sad.md`,
  `ux.md` and the frozen Netlify page not edited.
- 2026-11-19 · persona `backend-eng` · `sync-docs` · after B7: Doc sync: no updates.
- 2026-11-19 · persona `backend-eng` · operator approved the planted row's content as proposed (B7).
- 2026-11-19 · persona `backend-eng` · actions `develop-be` (tests), `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI not installed) · `AGENTS_MODE=stand_in` · **The first green
  path**: `tests/tier1/test_green_path.py`, passes (checked to fail with the demo refusal off). 270
  tests pass. Handoff H-056 to `@project.mgr`. No page or template change, so no visual change. No
  model call; no model ID chosen. `sad.md`, `ux.md` and the frozen Netlify page not edited.
- 2026-11-19 · persona `backend-eng` · `sync-docs` · after the green path test: Doc sync: no updates
  (setup.md's tripwire is `@project.mgr`'s to record, H-056).
- 2026-11-19 · persona `backend-eng` · actions `develop-be` (CI), `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · **B1 follow-up: CI**:
  `.github/workflows/ci.yml` (ruff, Tier 1 blocking, Tier 2 not blocking, aamad validate with the
  qa.md exception; no name scan, no model key); ruff 0.17.3 pinned and configured (defaults minus
  B008, operator); 37 lint findings fixed (24 by ruff's safe fixes, 13 by hand); mock-up checks
  skip without `docs/prototype`; `make lint`. 270 tests pass locally; 221 passed and 4 skipped in a
  committed-files-only copy. Handoff H-057 to `@project.mgr`. No model call.
- 2026-11-19 · persona `backend-eng` · B10 run instructions (operator request): README "Getting
  started" rewritten: prerequisites (Git, uv, make, Node for the visual check), install, run
  (`/health`), the demo walkthrough (the green path, with the answer key §5 G1 choices), the failure
  demo, reset, settings, checks (incl. CI), troubleshooting; planning-docs part kept; "Project
  structure" and "How to contribute" lines on running updated. Every command and page label checked
  against the app (started on a spare port; `/health` 200). Other stale README parts (the status
  note, "What happens next", the persona status table) left for the operator. No code change.
- 2026-11-19 · persona `backend-eng` · `document-backend` · H-059: B5's status corrected to done, to
  match `frontend.md` §9 (S-01 to S-34 ✅): the B7 section notes the correction, and Assumptions no
  longer calls the templates placeholders. The B7 audit line above ("B5 is still in progress") is
  history and stays; this line corrects it. H-061: H-036 closed (V-12 landed with B2, PR #75). Docs
  only. No model call.
- 2026-11-19 · persona `backend-eng` · actions `develop-be`, `document-backend` ·
  `AAMAD_TARGET_RUNTIME=crewai` (CrewAI 1.15.35 installed; loaded only by `load_crewai()`, real
  mode only) · `AGENTS_MODE=stand_in` · **B3 step 7b, PR 1**: crewai pinned; telemetry, CrewAI
  tracing and the version check forced off; 2 Tier 1 tests (no connection; T-MODE-1 with the green
  path). pydantic 2.14.3 → 2.12.5; 275 tests pass; one test warning gone (httpx2); lint clean;
  visual check unchanged. No model call, no key.
- 2026-11-19 · persona `backend-eng` · `document-backend` · `AAMAD_TARGET_RUNTIME=crewai` ·
  `AGENTS_MODE=stand_in` · operator request: added "How this maps to CrewAI terms" near the top
  (scenario, tasks and agents, tools, process, kickoff), pointers only, no new decisions. The B3
  intro was already corrected on `main` (DL-40 pinned, step 7b plan approved); the one stale
  "(after DL-40)" in Known gaps now says DL-40 is pinned. Docs only. No model call.
- 2026-11-21 · persona `backend-eng` · `develop-be` (B3 step 7b, PR 2: per-role model settings and per-call token limits) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "move on to 7b PRs 2 to 4". New `backend/runtime/model_settings.py`; settings read `LLM_MODEL_*`, `LLM_MAX_TOKENS_*`, `CALL_TIMEOUT_*` (SAD §4 names; `.env.example` changed, H-071 to `@project.mgr`). LLM, temperature and max-token controls: **resolved in code** (DL-40 sampling; limits 2000 / 2000 / 4000 as starting values; verifier sends no temperature, an assumption); worst case for a whole run US$1.49 against the US$2.50 cap, checked by a Tier 1 test. No model ID chosen or committed, no CrewAI call, no real key, no paid call.
- 2026-11-21 · persona `backend-eng` · `develop-be` (B3 step 7b, PR 3: a fake OpenAI for tests) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "move on to 7b PRs 2 to 4". Test code only (`tests/fake_openai.py`, the `fake_openai` fixture, `tests/tier1/test_fake_openai.py`, 15 tests); nothing in `backend/` changed. LLM, temperature and max-token controls: none resolved here (PR 2). No model call, no real key, no paid call, no outside connection (127.0.0.1 only).
- 2026-11-21 · persona `backend-eng` · `develop-be` (B3 step 7b, PR 4: the crews behind the three agent functions) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` (tests use real mode against the fake OpenAI only) · operator instruction "move on to 7b PRs 2 to 4". New `crews.py`, `wire_schema.py`; real-mode path in `agents.py`; `ModelServiceError` to the stage; `max_iter` 1; key in settings; `load_crewai()` also sets CrewAI's own 429 retry to one attempt. LLM, temperature and max-token controls: **built and tested against the fake** (DL-40 sampling per role, limits from PR 2); never sent to a real provider. H-072 to `@system.arch` (the hidden retry; the schema route). Real mode is not to be run before PR 5 and the spike. No real key, no paid call, no model ID committed.
- 2026-11-22 · persona `backend-eng` · `sync-docs` (B3 step 7b, PR 6: documentation) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "move on to PR 6 (docs)". Docs only: new section "B3 step 7b, PR 5" (which failures are retried, one trace line per HTTP request, the four new columns, the cost rule, the four-request and two-billed bound, the sticky silent repeat); "Kickoff", "Pattern Decision compliance" and "Known gaps" brought in line with real mode and PR 5. Raised H-074 to `@project.mgr` for `setup.md` and the README (not mine to edit). Read against the merged code (`crews.py`, `attempts.py`, `model_settings.py`, `agents.py`, `schema.sql`) and the PR 5 description; no code changed. No model call.
- 2026-11-22 · persona `backend-eng` · `develop-be` (B3 spike runner, PR 1 and PR 2a to 2d) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` (tests use real mode against the fake OpenAI only) · operator instructions "continue with B3 spike", "Start 2a", "Go 2b", "Go 2c", "Go 2d". New `backend/runtime/spike.py` (dry-run `plan_first_call`; `open_spike_run`; `run_first_call`; `--go` with a typed document-ID confirmation and a printed result) and Tier 1 T-SPIKE-1 to 4. The pull request that carries 2a to 2d is from branch `backend-eng/spike-runner-2`; PR 1 is #164 (merged). 2d is docs only: new section "B3 spike runner" with how to run the first real call and what each outcome means, "How to run" and "Known gaps" brought in line. The worst-case figure in the run steps was computed on 2026-11-22 with the dry-run planner and made-up settings (no network). Raised H-075 to `@project.mgr` for `setup.md` and the README (not mine to edit). LLM, temperature and max-token controls: unchanged (DL-40 per role, limits from PR 2); the first call sends the extractor's pinned settings. **No real key was used, no model call was made, no paid call, no model ID committed, no snapshot changed.** The operator makes the first real call.
- 2026-11-22 · persona `backend-eng` · `document-backend` (B3 spike fix, step C: documentation) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "Go C" after the first real spike call (RUN-20261122-1, run by the operator). Docs only: new section "B3 spike finding" (what the two trace lines were, how it was identified and how sure we are, what did and did not go wrong, why no test saw it, the fix in steps A to D, and a note for the spike report: `SRC-UCILAW#1` stays as the honest record, 1 model call plus 1 pre-flight request, 2 of 70 slots used, its cost and `off_pinned_setting` are false alarms); one pointer added to the run instructions' "Off pinned setting" row. Read from `data/spike.db` opened read-only, and from the installed CrewAI 1.15.35; reproduced locally against the fake OpenAI with CrewAI made to believe it was on OpenAI (127.0.0.1 only). Raised H-076 to `@system.arch` (sad.md is not mine to edit). Steps A (`bc0b320`) and B (`fcd2a69`) are code; D is not built yet. LLM, temperature and max-token controls: unchanged. **No real key was used by me, no model call, no paid call, no snapshot changed.** The operator will make one confirmation call after the fix merges.
- 2026-11-22 · persona `backend-eng` · `develop-be` + `document-backend` (B3 spike fix, step D: the request guard) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` (tests use real mode against the fake OpenAI only, with CrewAI made to behave as if on OpenAI) · operator instruction "Go D". Code in `9479f23`: the interceptor refuses any request that is not `POST .../chat/completions` before it is sent; new `trace` column `request_path` (additive, default empty); a refused request costs 0 and is never retried; the spike prints each request's path; T-REQ-2 (17 tests) and two older tests updated. Rehearsed the column migration on a copy of the real `data/spike.db` (all values unchanged, still append-only; the original file untouched). The docs of step D are in this entry's commit: "B3 spike finding" (row D, "What D does"), one row added to the run instructions, H-076 updated (D's commit and the new column for sad.md §4), and H-077 to `@qa.eng` (a pointer to the spike report note). LLM, temperature and max-token controls: unchanged. **No real key was used by me, no model call, no paid call, no snapshot changed.** The operator will make one confirmation call after this merges.
- 2026-11-22 · persona `backend-eng` · `develop-be` + `document-backend` (B3 spike fix: the verifier's flag as two shapes) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` (tests use real mode against the fake OpenAI only) · operator instruction after the first real verifier call (run by the operator): "Option 1, two flag shapes, as its own PR with tests against the fake". Code in `666b27c`: `backend/runtime/wire_schema.py` sends the verifier's flag as `anyOf` two shapes built from `Flag`; T-WIRE-1 (20 new tests); one older test changed (it pinned the old nullable keys). The extractor's and judge's schemas checked byte for byte against their schemas from before the change. Read `data/spike.db` opened read-only; nothing in it was changed. This entry's docs: new section "B3 spike finding 2" (what the trace holds, the cause, the fix, what is not proved, a note for the spike report), one row added to the run instructions (a 400 on the schema), and H-078 to `@system.arch` (sad.md is not mine to edit). LLM, temperature and max-token controls: unchanged (verifier: reasoning effort low, no temperature, 2000 tokens). **No real key was used by me, no model call, no paid call, no snapshot changed.** The operator re-runs the verifier call after the fix merges.
- 2026-11-23 · persona `backend-eng` · `document-backend` (B3 spike: the verifier re-run) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "docs-only PR recording verifier call #2". Docs only: "B3 spike finding 2" now records the operator's second real verifier call (`SRC-UCILAW-P3#2`, run 2026-11-23, trace line 5): valid, C-1 caught, no false alarm, US$0.0057, 1721 in and 185 out; **OpenAI accepted the nested `anyOf` in strict mode**; the "not proved" paragraph became the result, with a side-by-side table of the two calls and the numbers in the spike-report note (schema-pass 1 of 2; 5 of 70). Read from `data/spike.db` opened read-only; nothing in it was changed. H-078 (to `@system.arch`) updated with the result. LLM, temperature and max-token controls: unchanged. **No real key was used by me, no model call, no paid call, no code changed, no snapshot changed.**
- 2026-11-23 · persona `backend-eng` · `document-backend` (B3 spike: step 3, the judge result and the run instructions) · `AAMAD_TARGET_RUNTIME=crewai` · `AGENTS_MODE=stand_in` · operator instruction "Step 3 docs PR". Docs only: new section "B3 spike finding 3" (the operator's first real judge call, `SRC-UCILAW-P3#1`, run 2026-11-23: valid, CORRECT, `reasoning_effort` medium accepted, US$0.0013, 988 in and 62 out; a table of where the three roles stand; **all three models accepted their pinned settings so far, with the caveat of one or two calls per role**; the `minItems` drop recorded as an untested precaution; the numbers for the spike report: 6 of 70, US$0.0164, first-attempt schema-pass 4 of 5); new subsection "How to run the verifier and judge calls" in the runner section; a pointer from the older spike-report notes. Raised H-079 to `@system.arch` (decision 2; sad.md is not mine to edit). Read from `data/spike.db` opened read-only; nothing in it was changed. `setup.md` and the README (`@project.mgr`'s) do not yet carry the verifier and judge run steps: not raised here. LLM, temperature and max-token controls: unchanged. **No real key was used by me, no model call, no paid call, no code changed, no snapshot changed.**
