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

## How to run

```bash
make install            # .venv (Python 3.12), app + test deps, git hooks
cp .env.example .env    # set SESSION_SECRET to any local random value
make run                # http://localhost:8000, Ctrl+C to stop
make test               # all tests, stand-in agents, no model
```

Sign in as **Compliance specialist** (`specialist-1`) or **General Partner / Fund Manager**
(`gp-1`). Delete `data/app.db` to start from nothing.

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
same functions, switched off) is **postponed until just before the spike** (operator,
2026-11-18); see "Step 7b: dry-run findings" below. No model is called anywhere, and no model ID
is chosen (DL-40 waits for the first green path).

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
before B7: B12 is built; B5 (templates and CSS, `@frontend.eng`) is still in progress, and B7 needed
nothing from it (the G1 page already had the refusal's place).

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

## Pattern Decision compliance

No agent loop, no retrieval over live state, no side-effecting tool, no model client anywhere.
`AGENTS_MODE=real` refuses at each agent function. The stand-in answers (`backend/stand_in/`) are
hand-written from the mock paragraphs, carry no answer-key IDs (`OBL-`, `C-1`, `I-1`, `AMD-`) or
notes, are never placed in a prompt, and pass the same guardrails as a model's output. The loaders
never read the "Decides" column, test notes or amendments (T-LEAK-1, loader half).

## Known gaps

- An evaluation run with the demo-row switch on is not refused yet: there is no evaluation run
  before the evaluation runner (**B8**, EC-R7).
- `retry_run` is a stub (**B13b**). CrewAI wiring and the role harness are **B3 step 7**. The
  per-call timeout and its one automatic retry (D1, DL-43, T-RUN-2) come with the real calls (B3
  spike): a stand-in call cannot time out. The run status page shows the cost but not yet the
  "over US$2" warning (CR-017); the warning's wording and place are `@ux.designer`'s.
- **Step 7b postponed until just before the spike** (operator, 2026-11-18): CrewAI is not
  installed; the crews, the per-call timeout and its one retry, and real mode stay refused. The role harness has its call
  caps; the runner that makes the spike's per-role calls comes with the spike (after DL-40).
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
- Templates are placeholders; their look is `@frontend.eng`'s work in B5.

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
