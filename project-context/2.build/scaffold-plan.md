# Scaffold plan: repo structure for the stubbed UI

Owner: `@project.mgr`. **Plan only.** This file creates no folder, file, dependency or code. It
says what each Build persona will create, in which block, and in what order.

Sources: `project-context/1.define/sad.md` **as on `main` at commit `7048b38`** (DL-01 to DL-53:
Build card, Order of work, Estimate with blocks B1 to B13, run-state rules 9 to 11, §3 Frontend,
§4 Backend including "Data model: the happy path" (DL-50, `units` drawn by DL-53), §5 DevOps, §9
test tiers, CR-032, CR-033), `project-context/2.build/ux.md` (the workflow, §1.3 shared frame, the
seven pages, §10 screen-to-data map, §11 out of scope), `project-context/2.build/setup.md` (B1 as
done on 2026-11-13), root `CLAUDE.md` on `main` (T-DEMOFAIL-1). Not read or used: Future Work,
Appendix A, git tag `sad-full-design`.

**Branch note.** This branch (`scaffold-plan`) is now on `main` at `986ccad` (2026-11-16). The
B13 split is DL-54, merged as PR #58.

**Update 2026-11-17 (H-041).** `sad.md` now puts B12 after B5 (PR #82, H-040, DL-49 update) and
drops B12 as a whole after B6 and Tier 2, before B13b. §2 and §6 follow it, and §6 carries H-050's
forecast. The other sections are not changed.

Rules that hold for everything below: public repo; mock data and fictional names only
(`FND-DEMO-01`, Bramblegate, ACME); no secrets; `.env`, `data/` and `reference/` stay git-ignored;
never `--no-verify`. `sad.md` and `ux.md` are not changed by this plan; conflicts are listed under
Open Questions.

---

## 1. Folder tree

What already exists is marked **(exists)**. Everything else is planned. Folder names follow SAD §4
("Folder names show the shape; Build may adjust them"). One line per folder or key file.

```text
capstone/
├── backend/                        The one FastAPI application: pages, rules and stages in one process
│   ├── main.py                     Builds the app, mounts static files, runs the start-up rule, serves GET /health
│   ├── settings.py                 Reads env variables once; AGENTS_MODE defaults to stand_in when unset; STAND_IN_UNIT_PAUSE_S (B13a)
│   ├── db/                         SQLite setup: connection, schema, append-only triggers
│   │   ├── schema.sql              The 14 tables of SAD §4 "Data", every one with fund_id; CHECKs stand in for enums; runs and units with the DL-51 to DL-53 fields
│   │   └── connection.py           Opens the file at DATABASE_PATH, applies the schema on first start
│   ├── services/                   Every check and rule lives here (role, gate, decide-once, version, reason, ack)
│   │   ├── auth.py                 Mock identity from the signed session cookie; role check (CR-004)
│   │   ├── runs.py                 Start, list, abandon, run states and phases, one-active-run rule (CR-023); retry (B13b, rule 10)
│   │   ├── stage_store.py          Stores a stage's outputs in one transaction when it ends, checked against run, phase and stage attempt (rule 9)
│   │   ├── gates.py                G1/G2/G3 completion and the transitions; starts the next stage as a background task
│   │   ├── decisions.py            Row and verdict decisions, once each (CR-009)
│   │   ├── calendar.py             Calendar generation hand-off and the G3 view data
│   │   ├── publishing.py           Publish and decline, with the acknowledgement check (CR-028)
│   │   ├── audit.py                Writes audit_log entries (append-only)
│   │   ├── fund.py                 Loads the fund profile config for pages and stages
│   │   └── refusals.py             Refusal codes, HTTP statuses and the plain sentences from ux.md §5
│   ├── domain/                     Deterministic code with no model client
│   │   ├── quote_check.py          Word-for-word quote check (W-04, CR-005)
│   │   ├── date_engine.py          Due dates, rolls and marks against the 22-entry key (W-13)
│   │   ├── coverage.py             Paragraphs no non-rejected row cites (W-03b)
│   │   └── ids.py                  RUN-, ROW- and ENT- identifier schemes (§4 "Identifiers")
│   ├── runtime/                    Stage functions and the three agents; stores outputs only through services
│   │   ├── loader.py               Reads mock sources and fund facts, strips the answers (DL-39, T-LEAK-1)
│   │   ├── stages.py               Stage A, B and C functions; the backend stage timer (DL-43); the stand-in pause (B13a)
│   │   ├── agents.py               The three agent functions; returns stand-in outputs or calls a one-agent crew
│   │   ├── trace.py                One trace record per call attempt, cost count, cost cap (CR-017, CR-018)
│   │   └── schemas.py              Pydantic output models used as output_pydantic
│   ├── config/                     CrewAI configuration (versioned)
│   │   ├── agents.yaml             Extractor, verifier, judge: one model each, no tools, no memory
│   │   └── tasks.yaml              One task per agent, with its Task.id
│   ├── stand_in/                   Fixed outputs the three agent functions return when AGENTS_MODE=stand_in (CR-030)
│   │   ├── extractor.yaml          Stand-in rows (never placed in a prompt); B13a adds the failure-demo hook (DL-52)
│   │   ├── verifier.yaml           Stand-in flags
│   │   └── judge.yaml              Stand-in verdicts
│   ├── evaluation/                 Evaluation runner, report and trace export (B8). Name not fixed by the SAD
│   └── web/                        Thin page handlers, templates and the stylesheet (SAD §3, §4)
│       ├── routes/                 One module per area: sign_in, runs, g1, g2, g3, calendar, errors
│       ├── calendar_view.py            Display-only helper for the calendar Month and Year views (B12, DL-49 update; frontend.md W-5)
│       ├── templates/
│       │   ├── base.html           Shared frame: sidebar, breadcrumb, H1, run labels, refusal line (ux.md §1.3)
│       │   ├── parts/              Shared parts (ux.md §4): row card, flag, decision form, mark label, refusal, stepper, sidebar, run labels
│       │   └── pages/              The seven pages plus the 403 and 404 pages
│       │       ├── sign_in.html            Page 1 · Sign-in
│       │       ├── filing_rules.html       Page 2 · Filing rules (the review list)
│       │       ├── review_status.html      Page 3 · Review status (idle, running, done, failed)
│       │       ├── check_rules.html        Page 4 · Check the rules (G1)
│       │       ├── confirm_applies.html    Page 5 · Confirm what applies (G2)
│       │       ├── publish.html            Page 6 · Check the calendar and publish (G3)
│       │       ├── calendar.html           Page 7 · Calendar (General Partner, List view)
│       │       ├── no_access.html          403 page (ux.md §1.7)
│       │       └── not_found.html          404 page
│       └── static/
│           ├── site.css            The one shared stylesheet (B6); pages work without it
│           └── icons/              Iconoir SVGs copied in (B6, U8); no icon font, no script
├── config/                         Business configuration read once when a run starts
│   ├── fund/FND-DEMO-01.yaml       Fund profile: ID, display name, regime line, year end (DL-53), facts, filing parties (fictional)
│   ├── regulation/lu-part2.yaml    Conventions D-1 to D-7, mock holiday list, OQ-7 by paragraph and recipient code (CR-027),
│   │                               source files with their titles, recipient codes with display names (DL-53)
│   ├── policy/default.yaml         Client policy (P-1); holds no default roll rule (DL-19)
│   └── demo/planted-row.yaml       The planted demo row (CR-029); the evaluation runner never reads it
├── data/                           Git-ignored. The SQLite file and the local process log
├── tests/                          (exists, with test_answer_key.py) All run with stand-in agents, no model
│   ├── test_answer_key.py          (exists) No-model checks on the answer key
│   ├── conftest.py                 Fresh temporary database per test, signed-in clients for each role
│   ├── tier1/                      Blocks every merge (Build card list; T-DEMOFAIL-1 and T-PAUSE-1 join with B13a)
│   └── tier2/                      If time allows (T-RETRY-1 to 3 with B13b); T-MAP-1 lives here but must pass before the first eval run
├── scripts/
│   └── git-hooks/                  (exists) pre-commit and pre-push; real-name scan, .env/reference block, validator
├── .github/workflows/ci.yml        Lint with ruff, then the backend tests with stand-in agents; no model key
├── project-context/2.build/logs/   Trace and audit exports per evaluation run (B8); created by the runner
├── docs/                           (exists) Private and git-ignored, except learning-notes.md and ai-direction-log.md
├── pyproject.toml                  Application dependencies and ruff settings (B2 pins them)
├── Makefile                        make dev (start and wait for /health), make test, make install-hooks
├── .env.example                    (exists) Placeholders only
├── .gitignore                      (exists) Add data/ in B1's follow-up
└── README.md                       (exists) Rewritten with run instructions in B10 (outline in section 4)
```

Where the mock sources come from at run time: `config/regulation/lu-part2.yaml` lists the source
files, which stay in `project-context/1.define/mock-data/`. The loader reads them and strips the
answers (CR-016). Nothing is copied out of `mock-data/` into `backend/`.

---

## 2. Which block creates what, in build order

Order follows the Build card "Order" row, which is authoritative (H-001). B11 is time already
inside B3 and B5, not a block of files.

**B13 is split (operator decision, 2026-11-16, this plan).** The SAD has one B13 (Retry and the
failure demo, 0.5 day, after B9). The operator splits it so the failed state can be shown in
Sprint 3:

- **B13a Failure demo and stand-in pause**, 0.25 day, **straight after B3** (stand-in part).
- **B13b Retry**, 0.25 day, **after B9, before B6**, where B13 was.

⚠️ **This changes the SAD's Build card "Order" row, the Order of work table, the Estimate and the
drop order, and adds a setting.** The Build card is authoritative (H-001), so nobody builds from
this split until `@system.arch` makes the matching `sad.md` edit (listed at the end of section 6).

| # | Block | Persona | Creates or fills |
|---|---|---|---|
| 1 | **B1** Setup and data (done 2026-11-13, part) | `@project.mgr` | `setup.md`, `.env.example`, `scripts/git-hooks/`. **Still to do in B1's follow-up:** `data/` in `.gitignore`, `Makefile`, `.github/workflows/ci.yml`, the empty `tests/tier1/` and `tests/tier2/` |
| 2 | **B2** Gates and run states | `@backend.eng` | `pyproject.toml` (FastAPI, Jinja2, Uvicorn, Pydantic, PyYAML, CrewAI; pins recorded in `setup.md`), `backend/main.py`, `backend/settings.py`, `backend/db/` (the full schema, including the DL-51 to DL-53 fields on `runs` and `units`, so B13a and B13b need no schema change), `backend/services/` (except retry), `backend/domain/ids.py`, `config/fund/FND-DEMO-01.yaml`, Tier 1 tests EC-013 (service part), EC-016, EC-019, T-RUN-0, T-RUN-1, T-RUN-3, T-MODE-1. **Checkpoint:** B1 + B2 over 1.3 days → tell the operator |
| 3 | **B3** Stages A and B, **stand-in part only** | `@backend.eng` | `backend/runtime/` (loader, stages, agents, trace, schemas), `backend/services/stage_store.py` (**the stage-end store with the stage attempt, rule 9: built here whether or not B13b is built**), `backend/config/agents.yaml`, `tasks.yaml`, `backend/stand_in/`, `backend/domain/quote_check.py`, `coverage.py`, `config/regulation/lu-part2.yaml`. Tests T-W04-1 to T-W04-6, T-LEAK-1, EC-015 |
| 3a | **B13a** Failure demo and stand-in pause (stand-in, no model; **kept**, see drop order) | `@backend.eng` | **Failure demo** (DL-52, CR-033, rule 11): `runs.demo_fail_step1` accepted by `start_run` only when `AGENTS_MODE=stand_in` (else `VALIDATION`, audited); the start audit entry; the stand-in extractor hook that fails stage A's first unit on the first stage attempt with reason `demo failure`, starting unit 1 alone so the others stay "Waiting". **Stand-in pause**: `STAND_IN_UNIT_PAUSE_S` (default 1) in `settings.py` and `.env.example`; each stand-in agent function waits that long **per unit**, before returning its fixed output, so the units table fills in one row at a time (`ux.md` page 3, "Units finish one by one below"). **Only when `AGENTS_MODE=stand_in`**; in real mode it is never read. It runs inside the backend stage timer, well under every limit: stage A about 11 to 12 s (5 documents plus 6 or 7 rows) against 375 s, stage B about 5 to 6 s against 150 s, stage C about 1 s against 30 s. Tests: T-DEMOFAIL-1 (Tier 1), T-PAUSE-1 (new, Tier 1: real mode never pauses; stand-in pauses by the set amount per unit). Tests set the pause to 0 so the suite stays fast. **Page parts** (the checkbox on page 2, the "Failure demo on" label, the failed page in its "Without Retry" version) are written in B5 with the other templates |
| 4 | **B4** Stage C | `@backend.eng`, `@qa.eng` | `backend/domain/date_engine.py`, `config/policy/default.yaml`. Tests EC-007 (date test), EC-008, EC-014 (data part) |
| 5 | **B5** Gate actions and pages | `@frontend.eng`, `@backend.eng` | `backend/web/routes/`, `backend/web/templates/` (base, parts, all seven pages, 403, 404). Tests T-G3ACK-1, EC-013 (route part), EC-014 (page part) |
| 5a | **B12** Calendar Month and Year views and dot chart (one-day timebox; **pulled forward 2026-11-17, H-040**; dropped as a whole after B6 and Tier 2, before B13b) | `@frontend.eng`, `@ux.designer` | Templates under `pages/`, stylesheet rules, and one display-only helper, `backend/web/calendar_view.py` (DL-49 update: it may group, order and count the entries it is given and pick "due next" by comparing with today; it may not add a field, drop or mark an entry, calculate a date, call a service or model, or read what the viewer may not see). The Month view is the default; a radio group styled as tabs, CSS only, no script; below 960 px only the List view shows. Front end only, so it was built on the stub UI while the frontend waited on B2 (H-036) |
| 6 | **B7** Planted demo row | `@backend.eng` | `config/demo/planted-row.yaml`, the switch on the start form. Tests T-DEMO-1, T-DEMO-2 |
| — | **First green path** (a gate, not a block) | `@backend.eng`, `@qa.eng` | `tests/tier1/test_green_path.py`: start → Stage A → G1 with the demo row refused then rejected → Stage B → G2 → Stage C → G3 ack → GP view → audit log. Nothing that spends money starts before it passes |
| — | Pin DL-40 | operator | Model IDs in `.env` (not committed) and `decision-log.md` |
| 7 | **B3 spike** and verifier bake-off | `@backend.eng`, operator | No new folders. Timings replace the starting limits in `.env.example` |
| 8 | **B8** Evaluation runner | `@qa.eng` | `backend/evaluation/`, the responsible-role lookup for T-MAP-1, `project-context/2.build/logs/` |
| 9 | **B9** Tuning, then one evaluation cycle | `@qa.eng`, operator | Prompt edits in `backend/config/`; reports in `2.build/` |
| 9a | **B13b** Retry (stand-in, no model; **dropped after B6, Tier 2 and B12**) | `@backend.eng`, `@frontend.eng` | Retry in `services/runs.py` and `POST /specialist/runs/{run_id}/retry` with `RUN_NOT_FAILED`, `RETRY_LIMIT_REACHED`, `RETRY_NOT_ALLOWED`; the Retry form on page 3 above the existing link. Tests T-RETRY-1 to T-RETRY-3 (Tier 2). With it, the failure demo's "fails once" rule shows its purpose: "Retry step 1" then runs normally |
| 10 | **B6** Light visual pass (**dropped first**) | `@frontend.eng`, `@ux.designer` | `backend/web/static/site.css`, `static/icons/` |
| 11 | **B10** Acceptance and rehearsal | `@qa.eng`, `@security.eng`, `@devops.eng` | `README.md` run instructions (section 4), `2.build/qa.md`, the security checklist |

Tier 2 tests (T-EXAMPLE-1 overlap, T-PROMPT-1, T-D4-1, per-state page tests, T-RETRY-1 to
T-RETRY-3) go into `tests/tier2/` alongside the block they test, only if time allows.

**From B5 to B13b** the failed page uses the "Without Retry" version in `ux.md` page 3: only the
link "Start a new review from Filing rules". So in Sprint 3 the failure demo shows the failed
state, and the way forward is a new review. B13b adds the Retry form above the link.

---

## 3. What the stubbed UI needs to run with dummy data

| Need | How | Where | Source |
|---|---|---|---|
| **Stand-in agents by default** | `settings.py` treats a missing `AGENTS_MODE` as `stand_in`. Real mode also needs `SPEND_ACTIVITY`, else start-up refuses (T-MODE-1). Every page about a stand-in review shows the "Stand-in agents" label; the start form says "Agents: stand-in agents (fixed test outputs, no AI model is called)" | `backend/settings.py`, `parts/run_labels.html` | CR-030, ux.md page 2 |
| **Mock sign-in** | Two buttons, no password. `POST /sign-in` sets a signed session cookie with `specialist-1` or `gp-1` and the role. The backend reads the role from the cookie on every request. Needs `SESSION_SECRET` in `.env` (a local random value, never committed) | `services/auth.py`, `pages/sign_in.html` | SAD §4 "Sign-in and secrets", ux.md page 1 |
| **Seed data for `FND-DEMO-01`** | No database seed for the happy path: a run creates its own data. The "seed" is three sets of files: (1) the fund profile `config/fund/FND-DEMO-01.yaml` (fictional name, regime line, facts, filing parties); (2) the mock sources, loaded and split into 13 paragraphs when a run starts; (3) the stand-in outputs in `backend/stand_in/`, which give the rows, flags and verdicts that lead to the 22 calendar entries | `config/`, `backend/stand_in/` | SAD §4 "How the layers connect", MVP scope steps 1 to 3 |
| **Demo rule switch** (in the SAD) | Unticked checkbox "Add the demo rule (rule 7)" on the start form. When ticked, the run adds the planted row from `config/demo/planted-row.yaml`, labelled "Demo". Approve stays visible; the server refuses it (`DEMO_ROW_NOT_APPROVABLE`) and audits it | B7 | DL-31, DL-44, CR-029 |
| **Stand-in pause** (B13a) | `STAND_IN_UNIT_PAUSE_S`, default 1 second **per unit**, in stand-in mode only. Each unit in the units table moves from "Running" to "Done" one at a time, and step 1 runs for about 12 seconds, so the 3-second auto-refresh shows it filling in. Set it higher for a slower demo, or 0 in tests | `backend/settings.py`, `backend/runtime/agents.py` | Operator, 2026-11-16. Rename closed: the setting is built as `STAND_IN_UNIT_PAUSE_S` on `b1-app-shell` (`settings.py`, `.env.example`, `agents.unit_pause`, tests set it to 0); named in the SAD by DL-54 |
| **Failure demo switch** (B13a) | Unticked checkbox "Make step 1 fail (demo)", in the start form **only when `AGENTS_MODE=stand_in`**. Stored as `runs.demo_fail_step1`, audited. The stand-in extractor fails stage A's first unit on the first attempt only, with reason `demo failure`; the other units stay "Waiting". Sent in real mode → `VALIDATION`. Never on an evaluation run, never seen by the General Partner. With the pause, unit 1 shows "Running" for about 1 second, then the review shows "Failed" | B13a (page parts in B5) | DL-52, CR-033, run-state rule 11 |
| **Retry** (B13b) | "Retry step {k}" on every failed review; the server decides. Restarts only the failed stage, keeps every decision, `stage_attempt` goes to 2, one audit entry. Refused after a cost-cap or calendar-generation failure, a second retry, an evaluation run or when a newer run exists. Until B13b: the "Start a new review" fallback | B13b | DL-51, CR-032, run-state rule 10 |
| **Local database** | One SQLite file at `DATABASE_PATH` (default `data/app.db`), created on first start. Delete the file to start from nothing | `backend/db/` | SAD §5 |

---

## 4. README outline (for B10; the existing README is replaced then)

This persona does not write the README. `@devops.eng` or `@qa.eng` writes it in B10 ("run
instructions"). This outline is what it must cover for the Sprint 3 bar.

1. **What it does** (two sentences). "AI agents draft filing rules from mock regulatory text for one
   fictional fund, and a compliance specialist checks them in three steps. Code then works out the
   due dates and publishes a compliance calendar the General Partner can read."
2. **Status and honesty line.** Mock data only, fictional fund, stand-in agents by default, not
   legal advice.
3. **Install.** Python 3.12, `uv venv --python 3.12 .venv`, install dependencies, `cp .env.example
   .env`, set `SESSION_SECRET` to any local random value, `git config core.hooksPath
   scripts/git-hooks`.
4. **Run locally.** `make dev`, open `http://localhost:8000`. How to stop it.
5. **Sign in.** The two mock identities and what each can do: compliance specialist (all pages,
   makes every decision) and General Partner / Fund Manager (calendar only, view only). No password.
6. **Walk through the four states** (ux.md §10.1):
   - **Idle:** sign in as the specialist; Filing rules shows no active review.
   - **Running:** click "Start a new review" (optionally tick "Add the demo rule"). With stand-in
     agents each unit takes about 1 second (`STAND_IN_UNIT_PAUSE_S`), so the units table fills in
     one row at a time. Review status refreshes every 3 seconds while AI or code works, then says
     "Your turn". Raise the pause in `.env` for a slower walkthrough.
   - **Done:** finish steps 2 to 4 and publish; sign out and sign in as the General Partner to see
     the calendar. Also: "Closed without publishing" and "Abandoned".
   - **Failed:** tick "Make step 1 fail (demo)" (only shown with stand-in agents) and start. Step 1
     fails at its first unit with the "failed on purpose, for the demo only" sentence. The way
     forward is "Start a new review from Filing rules" (untick the box). **Once B13b is built**,
     add: click "Retry step 1" and step 1 runs normally, so one review shows the error and the
     retry. **If B13b is dropped**, the README keeps the failure demo and leaves Retry out.
7. **Reset.** Abandon the review at any step that waits for you (a reason is required), or finish
   it, then start a new review. To clear everything: stop the app and delete `data/app.db`.
8. **What is stubbed.** Stand-in agents with fixed outputs; mock sign-in; mock sources and a
   fictional fund; mock holiday list.
9. **Out of scope** (ux.md §11, SAD "Never in the MVP"). Real sign-in, streaming, tool traces and
   cost panels, more than one fund, a second workflow, the source picker, the period line, styling
   polish beyond the light pass, editing or reopening decisions, hosting.
10. **Tests.** `make test`; Tier 1 blocks merges; no model is called.
11. **Repository rules.** Public repo, no real names, the hooks, never `--no-verify`.

---

## 5. The smallest first commit: Filing rules with stand-in data

Goal: sign in as the specialist and see page 2 rendered by the real app from the real database and
config, with nothing more. It is a thin vertical slice of B2 and B5. **It needs the operator's OK
because the Build order puts B2's service layer before any page** (Open Question 1).

| File | Why it is needed | Kept small by |
|---|---|---|
| `pyproject.toml` | FastAPI, Uvicorn, Jinja2, python-multipart (forms), itsdangerous (signed cookie), PyYAML | No CrewAI yet |
| `Makefile` | `make dev` | `dev` target only |
| `.gitignore` | Add `data/` | One line |
| `.env.example` | Add `SESSION_SECRET` (placeholder) and `DATABASE_PATH` | Waits on the naming decision in `setup.md` Open Points |
| `backend/__init__.py`, `backend/main.py` | App, session middleware, `GET /health` | No start-up rule yet |
| `backend/settings.py` | `AGENTS_MODE` (default `stand_in`), `SESSION_SECRET`, `DATABASE_PATH` | Three settings |
| `backend/db/schema.sql`, `backend/db/connection.py` | `runs` (with every DL-51 to DL-53 field: `started_at`, `started_by`, `demo_fail_step1`, `stage_attempt`, `spend_activity`) and `audit_log` (append-only triggers) | Two tables only; the rest come with B2. Full `runs` columns now, so no later change |
| `backend/services/auth.py` | Role from the cookie; specialist check; refusal written to `audit_log` | `FORBIDDEN` only |
| `backend/services/fund.py` | Reads the fund name and line for the sidebar and start form | Reads three fields |
| `backend/services/runs.py` | `list_runs(fund_id)`, read-only | No start, no states logic |
| `config/fund/FND-DEMO-01.yaml` | `fund_id`, `name` ("Bramblegate Credit Opportunities SICAV"), `regime` ("Luxembourg UCI Part II"), `year_end` ("31 Dec"), as DL-53 names them | Display fields only; facts and filing parties come in B3 |
| `backend/web/routes/sign_in.py`, `runs.py` | `GET/POST /sign-in`, `POST /sign-out`, `GET /specialist/runs` | Thin handlers |
| `backend/web/templates/base.html`, `parts/sidebar.html` | Shared frame: wordmark "acme", fund block, nav, identity, sign out | No stepper |
| `backend/web/templates/pages/sign_in.html`, `filing_rules.html`, `no_access.html` | Pages 1 and 2, and the 403 for a General Partner | Unstyled HTML |
| `tests/tier1/test_filing_rules.py` | Specialist sees page 2; GP gets 403 and an audit entry (part of EC-019); default mode is stand-in (part of T-MODE-1) | Three tests |

**Not in it:** the stylesheet (B6), the start form's `POST` (B2), stages, stand-in outputs, any
other page.

**What "stand-in data" shows in this commit.** The fund block and the "Agents: stand-in agents"
line come from config and settings. The reviews table is empty ("No reviews yet."), because
reviews are only created by "Start a new review", which is B2. To show a populated table now,
the commit would need a dev-only seed script that writes sample runs straight into the database,
which the SAD does not describe (Open Question 2).

---

## 6. Risks to the day-8 hard stop, and what to drop first

**Drop order (SAD "Estimate", operator decision 2026-11-12, DL-42).** Nothing else is dropped
without a new operator decision.

**Estimate with the split.** The architect's figures are in quarter days; the split is this
plan's proposal and needs `@system.arch` to confirm it.

| Block | SAD now | Proposed | Note |
|---|---|---|---|
| B13 (one block, after B9) | 0.5 | — | Replaced by B13a and B13b |
| B13a Failure demo and stand-in pause (after B3) | — | 0.25 | Switch, extractor hook, reason, start-form check, a setting and a per-unit wait in the stand-in agent functions, two tests. The page parts ride in B5 |
| B13b Retry (after B9) | — | 0.25 | Route, guard, three refusal codes, form, T-RETRY-1 to 3. Rule 9's store is already in B3 |
| **MVP** | ≈ 6.75 (5.75–9.25) | **≈ 6.75 (5.75–9.25)** | Unchanged total. The pause is about an hour and fits inside B13a's quarter day |
| **MVP with B12** | ≈ 7.75 (6.75–10.25) | **≈ 7.75 (6.75–10.25)** | Unchanged |

**What does change is when the time is spent.** The work before the first green path grows from
about 3.5 days (B1 to B7) to about 3.75 days, so there is a quarter day less slack before the
day-4 tripwire.

**Drop order, with the split** (the SAD's order, adjusted; needs the same SAD edit):

1. **B6 light visual pass and Tier 2 tests** (including T-RETRY-1 to 3), at once if the tripwire
   fires (first stand-in green path not passed by the end of day 4). Pages stay unstyled but usable
   and accessible.
2. **B12 calendar Month and Year views and dot chart, as a whole** (operator, 2026-11-17, H-040;
   SAD "Estimate"). It is dropped after B6 and Tier 2 and before B13b. The calendar then shows the
   List view alone.
3. **B13b Retry**, after B12 (SOQ-35 placed B13 next after B6; B12 now sits between). The failed
   page keeps the "Without Retry" version. The stage-end store (rule 9) stays, because B3 builds it.
4. **Never T-MAP-1.** It must pass before the first evaluation run even if Tier 2 is dropped.
5. **Kept: B7 planted demo row** (it demonstrates the human checkpoint) and **B13a failure demo
   and pause** (they show the failed and running states in Sprint 3; built before the tripwire, so
   dropping them later would save nothing). T-DEMOFAIL-1 and T-PAUSE-1 stay Tier 1.

**B12 is built early, not last (2026-11-17).** It was planned after B10 and parked first. The
operator moved it to after B5 (before B7, B6 and B10) because it is front end only and the frontend
was waiting on B2. Its one-day timebox is unchanged: what is not done at the end of the day is
parked (F-19). B10's accessibility and copy checks now cover the new views.

**Forecast at the B1 + B2 checkpoint (H-050, `@backend.eng`, 2026-11-17; effort only, the
operator's clock decides).** B2 as scoped (the real checks, V-12, Rule 9 and real stored data, and
the start-up rule) is about 0.8 to 1.0 day against the SAD's 0.5, so with B1 it was likely at or
over 1.3 days. Rule 9 and stored data moved here from B3 (H-047), so B3's 1.0 day should shrink by a
similar amount (not re-estimated). Still to come: B7 about 0.25 day (likely less) and B13b about
0.25 day. The stage time limit and the Pydantic unknown-field refusal are B2 items in the SAD, not
started and not estimated; count them. **The operator's clock says B1 + B2 did not pass 1.3 days,
so nothing is dropped at this checkpoint** and the drop order above is unchanged. **Re-check after
B7** (operator instruction), with the time then known and the unestimated B2 items. The same note
is in `setup.md` "Timing guardrails".

| Risk | Effect on day 8 | Signal | Response |
|---|---|---|---|
| B1 + B2 run long (14 tables, guards, refusal envelope) | Pushes everything | Over 1.3 days | Tell the operator at once (Build card checkpoint) |
| Green path late | Spike, eval and demo squeezed | Not passed by end of day 4 | Tripwire: drop B6 and Tier 2 |
| Rule 9's stage-end store is skipped in B3 to save time | B13b then needs rework in the stages, and late outputs could be stored (T-RUN-8) | B3 review | Build it in B3 as the SAD says, whether or not B13b survives |
| B13a before the green path eats tripwire slack | A quarter day less before day 4 | B1 to B3 over about 2 days | Keep B13a to its quarter day; if B1 + B2 trip the 1.3-day checkpoint, tell the operator then, not at day 4 |
| The pause hides a real slowness bug, or leaks into real mode | Misleading timings; real runs slowed | T-PAUSE-1 | The pause is read only in stand-in mode, and T-PAUSE-1 (Tier 1) checks that real mode never pauses |
| Units must actually be stored and shown one by one | If the stage updates every unit line only at the end, the per-unit pause shows nothing new | First stand-in run | Rule 9 already updates each unit line as its output arrives; build it that way in B3 |
| B13b squeezed between B9 and B6 | Retry dropped late | B9 runs over | Drop B13b per the order above (after B6, Tier 2 and B12); the fallback page already exists from B5 |
| Page-first first commit (section 5) | Small rework if B2's service shape differs | Operator decision | Keep commit 1's services read-only and minimal |
| Stand-in fixtures look like the answer key | T-LEAK-1 / CR-016 failure, rework in B3 | Review of `backend/stand_in/` | Write fixtures without answer-key IDs (`OBL-`, `C-1`, `I-1`, `AMD-`) and not copied from the key file, as CR-027 now does for OQ-7 (Open Question 4) |
| Env variable names still provisional | Renames across settings and README | `setup.md` Open Points | Decide names before commit 1 |
| B12 built early takes the frontend's day while B2 and B3 are still open | B7 and the first green path start later; tripwire slack shrinks | B12 passes its one-day box | Park what is not done at the end of the day (F-19); the day-4 tripwire and the drop order above still apply. The old "hold B12 until B10 is green" rule is withdrawn (operator, H-040) |
| Python 3.12 / CrewAI install issues | B2 stalls | Install fails | Already pinned to 3.12.16 in `setup.md` |

**`sad.md` edits the split needs (for `@system.arch`; not made by this persona).** Until they
land, the Build card as on `main` stays the build instruction.

1. **Build card "Order" row** and **"Order of work"**: B3 (stand-in) → **B13a** → B4 → B5 → B7 →
   first green path → … → B9 → **B13b** → B6 → B10 → B12. *(Landed with DL-54. B12 has since moved
   to after B5: see §2 row 5a and H-040, H-041.)*
2. **Estimate table**: B13 replaced by B13a (0.25) and B13b (0.25); totals unchanged.
3. **Drop order** (Estimate "Checkpoint" paragraph and SOQ-35): B13b next after B6; B13a kept.
4. **§4 "Sign-in and secrets"**: new variable `STAND_IN_UNIT_PAUSE_S` (stand-in only, default 1
   second per unit, 0 in tests).
5. **§2 / Production Shape** (stage timer, DL-43) and **CR-030** (stand-in mode): the per-unit
   pause runs inside the stage timer and is never applied in real mode; it does not change the
   stage limits.
6. **§9 / EC-R4 Tier 1 list**: T-DEMOFAIL-1 is Tier 1 from B13a, no longer tied to Retry; new
   T-PAUSE-1. Root `CLAUDE.md` names T-DEMOFAIL-1 with "block B13, Retry and the failure demo", so
   its wording needs the same change.
7. **CR-033 / DL-52**: the failure demo no longer depends on Retry; until B13b, the failed page
   offers only "Start a new review".

`setup.md`'s environment table already lists `STAND_IN_UNIT_PAUSE_S` (done, 2026-11-16).

---

## Open Questions (for the operator)

**Answered by the SAD update (`7048b38`), closed here:**

- *There is no B13* → B13 is Retry and the failure demo (DL-51, DL-52), 0.5 day, after B9.
- *How to show the failed state* → the failure demo switch (DL-52) and Retry (DL-51), in B13.
- *"Recipients" config* → no separate file: recipient display names and document titles go in
  `config/regulation/lu-part2.yaml` (DL-53, answers G-7 and G-2).
- *Fund profile fields* → `name`, `regime`, `year_end` in `config/fund/FND-DEMO-01.yaml`
  (DL-53, answers G-8).

**Answered by the operator, 2026-11-16 (pause rename closed, built on `b1-app-shell`):**

- *Failed state before B13* → B13 split: the failure demo (B13a) is built right after B3; Retry
  (B13b) stays after B9.
- *Stand-in stage timing* → a configurable pause, stand-in mode only.
- *Send the split to `@system.arch`* → yes: handoff **H-033** in `project-context/handoffs.md`.
- *Pause per stage or per unit* → per unit, about 1 second, setting renamed
  `STAND_IN_UNIT_PAUSE_S`, 0 in tests.

**Still open:**

1. **Page-first first commit.** The Build order still says the service layer (B2) comes before any
   page. Section 5 shows Filing rules first, as a thin read-only slice. OK to deviate, or should
   commit 1 be B2's service layer with no page?
2. **Populated Filing rules in commit 1.** Accept the empty table until B2, or add a dev-only seed
   script (not in the SAD) that writes sample runs into the local database? (The SAD's only seed
   script is in parked Appendix A, so it cannot be borrowed.)
3. **Fund profile source.** Is `config/fund/FND-DEMO-01.yaml` hand-written from
   `mock-fund-profile.md` without the "Decides" column and test notes (CR-016)?
4. **Stand-in fixtures and CR-016.** CR-016 says no run-time fixture refers to the answer key, yet
   the stand-in outputs must produce the rows that lead to the 22 entries. Confirm with
   `@system.arch` that stand-in outputs are allowed if they carry no answer-key IDs and are not
   read from the key file (the same approach SOQ-33 took for OQ-7).
5. **Hook path drift.** SAD §5 still names `scripts/real-name-scan.sh` and `make install-hooks`;
   `setup.md` records `scripts/git-hooks/` and `git config core.hooksPath`. The plan follows
   `setup.md`. Should `make install-hooks` just run that `git config` line?
6. **"Hollowmere".** Listed as an allowed fictional name, but no project file uses it. Where should
   it appear, if anywhere?
7. **Env variable names.** `setup.md` Open Points still waits on renaming `CALL_TIMEOUT_*_S` and
   `STAGE_LIMIT_*_S` to the §4 names and adding `SESSION_SECRET`, `DATABASE_PATH`, `LLM_MODEL_*`
   and `LLM_MAX_TOKENS_*`. Commit 1 needs the first two.
8. **Uncommitted `ux.md` edits.** Moved to a named stash so this branch could move to `main`;
    nothing deleted. Handed to `@ux.designer` as H-034.

## Audit

- 2026-11-16 · persona `project-mgr` · action `setup-project` (plan only) · `AAMAD_TARGET_RUNTIME=crewai`
  · created this file on branch `scaffold-plan`. No folder, code, dependency or README created. No
  diagram needed. `sad.md` and `ux.md` not edited. No model call.
- 2026-11-16 · persona `project-mgr` · action `setup-project` (plan update) · re-read `sad.md` on
  `main` at `7048b38` (DL-51 to DL-53, B13, SOQ-32, SOQ-33, SOQ-35). Added B13 to the tree, order
  and drop order; the rule 9 stage-end store in B3; DL-53 config fields and `runs` columns;
  T-DEMOFAIL-1 and T-RETRY-1 to 3; the new estimate. Closed four open questions, added two. Still
  plan only; `sad.md` and `ux.md` not edited.
- 2026-11-16 · persona `project-mgr` · action `setup-project` (plan update, operator decision) ·
  split B13 into B13a (failure demo and stand-in pause, after B3) and B13b (Retry, after B9);
  added `STAND_IN_STAGE_PAUSE_S` (default 3, stand-in only) and T-PAUSE-1; updated the block
  table, estimate (totals unchanged), drop order and risks; listed the seven `sad.md` edits for
  `@system.arch`. Closed two open questions, added two. Still plan only; `sad.md` not edited.
- 2026-11-16 · persona `project-mgr` · action `setup-project` (plan update, operator decision) ·
  pause changed from once per stage to about 1 second per unit, setting renamed
  `STAND_IN_UNIT_PAUSE_S` (stand-in only, 0 in tests); wrote handoff H-033 to `@system.arch` with
  the seven `sad.md` edits and the root `CLAUDE.md` T-DEMOFAIL-1 wording. Closed two open
  questions. Still plan only; `sad.md` and `CLAUDE.md` not edited.
- 2026-11-16 · persona `project-mgr` · action `document-setup` (plan update, operator instruction) ·
  closed the pause rename: `STAND_IN_UNIT_PAUSE_S` (about 1 second per unit, stand-in only, 0 in
  tests) is built on `b1-app-shell` and in `.env.example`. Removed the "SAD edit pending" marker on
  that setting and the "setup.md gains it later" note (`setup.md` already lists it). The old name
  `STAND_IN_STAGE_PAUSE_S` stays only in the earlier audit entry, as history. No code, `sad.md` or
  `CLAUDE.md` edited.
- 2026-11-17 · persona `project-mgr` · action `setup-project` (plan update, handoff H-041) · checked
  `sad.md` on `main` after PR #82 first (Build card "Order" row, Order of work row 5a, Estimate drop
  order). §2: B12 moved to row 5a (after B5) with the display-only helper condition; B13b's row says
  "dropped after B6, Tier 2 and B12". §6: drop order is B6 and Tier 2, then B12, then B13b, T-MAP-1
  never; the "Hold B12 until B10 is green" risk is replaced; H-050's forecast added. No block, test
  or estimate figure changed (totals ≈ 6.75 and ≈ 7.75). `sad.md`, `ux.md`, `frontend.md` and
  `setup.md` not edited. No code. No model call.
