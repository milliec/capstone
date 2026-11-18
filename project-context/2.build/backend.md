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
| Stored data | `rows`, `paragraphs`, `quote_checks`, `verdicts`, `calendar_versions`, `calendar_entries` | Stage A and B outputs are the stand-in answers (B3 step 5); stage C's dates are placeholders until B4; stage B has one verdict per **approved** rule, stage C one entry per rule whose final answer is "applies" |
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
alone. Steps 1 to 6 are done; step 7 (CrewAI wiring behind the same functions, switched off, and
the role harness) is next. No model is called anywhere.

| Step | PR | What | Where |
|---|---|---|---|
| 1 Loader (W-02) | #92 | The 6 mock documents → 13 paragraphs, paragraph text only (no test notes, planted-conflict notes, header warning or amendments; CR-016). Refuses if the file and the config disagree | `backend/domain/sources.py`, `config/regulation/lu-part2.yaml` |
| 2 Quote check (QN-1, W-04) | #93 | Trim, collapse ordinary spaces, tabs and line breaks, then the quote must be one unbroken piece of the **cited** paragraph. Case, punctuation and Unicode forms count | `backend/domain/quote_check.py` |
| 3 Schemas and guardrails (CR-003) | #94 | The three step outputs as Pydantic models (unknown fields refused) and one guardrail per agent card | `backend/domain/schemas.py`, `guardrails.py` |
| 4 Stand-in answers and agent functions (CR-030) | #95 | Recipient codes; the fund facts loader (ID, fact, value; event ID and description); hand-written answers (6 rows, 1 flag, 1 "unsure"); `extract_rows`, `check_conflicts`, `judge_applicability`, which put each answer through the real guardrail | `backend/domain/fund_facts.py`, `backend/stand_in/*.yaml`, `backend/runtime/agents.py` |
| 5 Stages A and B wired | #96 | Stage A: loader → extract per primary document → demo rule if on → quote check per row → verifier per row; units: 5 documents then one check per rule. Stage B: fund facts → judge per approved rule. The store keeps the applicability rule, the quote check's reason and the flags; `offset` is stored as JSON. Pages get words for codes, recipient and document names from the config, and real fact values and counts | `backend/runtime/stages.py`, `services/stage_store.py`, `decisions.py`, `calendar.py`, `runs.py`, `backend/domain/wording.py` |
| 6 Trace, cost count, cost cap, stage timer | this PR | **Trace** (CR-018): table with the §4 columns, append-only triggers; every agent call, stand-in included, writes one line, adds its cost to `runs.cost_so_far` and writes an `agent_output` audit entry whose `trace_ref` is the record key, in one transaction. **Cost cap** (CR-017): before each call, at `RUN_COST_CAP_USD` or above the unit fails with "cost cap" and no call starts. **Stage timer** (rule 6, DL-43): a timer on its own thread around each stage fails the running unit with "stage time limit"; a call still running finishes, its output is marked `late`, kept in the trace only, its cost counts, nothing is stored (T-RUN-6, T-RUN-8). `fail_stage` now checks and changes the run under one write lock, so the timer can never fail a stage that has just finished. Settings use the SAD names `STAGE_TIME_LIMIT_A`, `_B`, `_C`. `run_unit` deleted (H-052) | `backend/services/trace.py`, `backend/db/schema.sql`, `backend/runtime/stages.py`, `agents.py`, `services/stage_store.py`, `backend/settings.py`, `.env.example` |

**Operator decisions in B3 (2026-11-18):** an empty quote fails; only ordinary whitespace is
collapsed; a date-shaped value is refused unless it is copied word for word from the agent's input
(H-052); the judge's facts come from the mock profile through a loader; recipient code `LBR`;
"who files" as the source writes it; a row the verifier has no answer for gets no flags; a
**temporary demo rule** (`backend/stand_in/demo_row_temporary.yaml`, rule 7, cites `SRC-UCILAW-P1`)
until B7 replaces it; the visual script's driving steps updated, snapshots not (H-053).

**Placeholder dates until B4 (operator, 2026-11-18).** Stage C is still the shell stub: the three
placeholder dates in `backend/stand_in/shell_data.py` attach to rules **1, 2 and 4**, whatever those
rules are, if their final answer is "applies". So the calendar shows real rule names with dates
that do not follow from the rules (for example the monthly report on 30 April). Rules 2 and 4 were
chosen so the calendar keeps one "moved off a weekend" entry and one "May not be required" entry
(rule 4 is the "AI can't tell" rule) until B4 works the dates out.

## Pattern Decision compliance

No agent loop, no retrieval over live state, no side-effecting tool, no model client anywhere.
`AGENTS_MODE=real` refuses at each agent function. The stand-in answers (`backend/stand_in/`) are
hand-written from the mock paragraphs, carry no answer-key IDs (`OBL-`, `C-1`, `I-1`, `AMD-`) or
notes, are never placed in a prompt, and pass the same guardrails as a model's output. The loaders
never read the "Decides" column, test notes or amendments (T-LEAK-1, loader half).

## Known gaps

- `DEMO_ROW_NOT_APPROVABLE` and "Approval blocked" are **B7**; the demo rule (temporary, rule 7)
  can be approved until then.
- `retry_run` is a stub (**B13b**). CrewAI wiring and the role harness are **B3 step 7**. The
  per-call timeout and its one automatic retry (D1, DL-43, T-RUN-2) come with the real calls (B3
  spike): a stand-in call cannot time out. The run status page shows the cost but not yet the
  "over US$2" warning (CR-017); the warning's wording and place are `@ux.designer`'s.
- Stand-in trace lines use `prompt_version` = `stand-in:` + a hash of the stand-in answer file
  (there is no prompt yet); B3 step 7 switches it to a hash of `agents.yaml` and `tasks.yaml`.
- Calendar dates are placeholders (**B4**), see above.
- T-W04-6 (the verifier claims "quote ok" for a row code failed) has no test: the verifier's schema
  has no such field, so the claim cannot reach the store, and the quote-check result is code's
  alone. Revisit with the real verifier (B3 spike).
- No Pydantic form models refusing unknown fields, no ruff/CI (`.github/workflows/ci.yml` is still
  to do in B1's follow-up).
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
