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
| `runtime.agents.run_unit(settings, stage, unit_id)` | — | Stand-in pause, no output; real mode raises | Fixed outputs, CrewAI wiring (B3) |

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
| V-5 `counts` | every run | Counted from the stand-in data |
| V-6 `ended`, `failure`, `published_at`, `ended_because` | every run | `ended` (time and reason) is read from the run's last `gate_event` audit entry, because there is no "ended at" column |
| V-7 `started_by_label` | every run | `runs.actor_label`: sign-in label plus " (mock)" |
| V-8 G1 | `decisions.get_g1_view` | Row status, quote check, paragraph, flags, who-files choice, `decided` line; view `stage`, `summary`, `unused_paragraphs` |
| V-9 G2 | `decisions.get_g2_view` | Cited facts, approved rule, `missing_fact`, `overrule_value`, `decided.outcome` |
| V-10 G3 | `calendar.get_g3_view` | `stage`, `rejected_rows` (real), unused paragraphs, `previous_publication_at`, `outcome`; entry words and `marks.moved` |
| V-11 | `calendar.get_published_calendar` | Same entry builder, so published entries also carry `source_document` and `quote` |
| V-12 refusal object | — | **Not built.** Shared with B2/B7 (`code`, `sentence`, `anchor`, `target_label`, `typed`) |

`runs.page_stage(run, "g1"|"g2"|"g3")` gives `before`, `at`, `after` or `ended_before` for all three
step pages. Stand-in data changed once: calendar entry 2 now moves from Sun 18 Apr to Mon 19 Apr
2027, so its "moved off a weekend" mark is consistent.

## Pattern Decision compliance

No agent loop, no retrieval over live state, no side-effecting tool, no model client anywhere.
`AGENTS_MODE=real` refuses at the agent function. Stand-in placeholder data
(`backend/stand_in/shell_data.py`) is generic, carries no answer-key IDs (`OBL-`, `C-1`, `I-1`,
`AMD-`) and is not copied from `mock-data/`.

## Known gaps (by design in the shell)

- No refusal checks other than `FORBIDDEN`; double-clicking "Start" can create two active runs.
- Decisions are audit entries only; `rows`, `row_decisions`, `verdicts`, `verdict_decisions`,
  `calendar_entries` stay empty. `trace` table not created (columns not in the SAD).
- The pages now read the H-036 view fields (V-1 to V-11), so templates no longer choose from the
  phase; only V-12 (the refusal object) is missing and comes with B2/B7. The interim lookups in
  `parts/lookups.html` are `@frontend.eng`'s to delete.
- **Stub detail:** an approve's weekend rule and who-files choice are kept in the stub's audit text
  after `| stub details: `, so the "decided" line can show them. B2 stores them in `row_decisions`
  and removes the suffix.
- `Approval blocked` (the demo row's chip after a refused approval) is B7; nothing sends it yet.
- No start-up rule (`service restarted`), no stage timer, no Pydantic form models refusing
  unknown fields, no ruff/CI (`.github/workflows/ci.yml` is still to do in B1's follow-up).
- Starlette 1.x prints a deprecation warning for `httpx` in the test client; harmless.
- CrewAI adapter items (`backend/config/agents.yaml`, `tasks.yaml`, crew controls) are B3.

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
- `trace` waits for B3 because the SAD names its record key but not its columns.
- Templates are placeholders; their look is `@frontend.eng`'s work in B5.

## Open Questions

1. **Function names.** *Answered 2026-11-16: accepted; SAD to own them (H-035).* The SAD has no B2 function names or signatures. The names above are
   derived from the §4 routes. Confirm them, or have `@system.arch` record them in the SAD.
2. **Spec drift: stubs with state moves.** *Answered: accepted for the stubbed UI; Build card update in H-035.* The Build card says "a stub holds no check and no state
   logic" (read-only stubs). This shell's stubs move status and phase (operator request,
   2026-11-16). Accept, or hand to `@system.arch` to update the Build card row.
3. **Verdict and calendar IDs.** *Answered: accepted; SAD to record them (H-035).* The SAD gives no scheme for verdict or calendar IDs; the shell uses
   `VER-<run>-<n>` and `CAL-<run>`.
4. **Env names.** Only the §4 names the shell needs were added. The `CALL_TIMEOUT_*_S` /
   `STAGE_LIMIT_*_S` renames in `setup.md` Open Points are still waiting.

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
