# Regulatory Intelligence for Fund Compliance Calendars

AI agents read regulatory text and draft source-linked filing rules. A compliance specialist checks and
approves them, and ordinary code turns them into a fund's compliance calendar.

> **Status: Build phase.** Define is done (requirements, user stories, mock data, architecture and
> interaction design). **A clickable stand-in app runs locally**: the seven pages, the gates, the
> date code and the planted demo row work end to end on stand-in agents (fixed test outputs), and
> the first end-to-end green path passes in the automated tests. **No AI model has been called yet**:
> that waits for the operator to choose the models. See [Getting started](#getting-started).
>
> This is a six-week capstone project. All data is mock and the fund is fictional. Nothing here is
> legal advice.

---

## Contents

- [Overview](#overview)
- [The problem](#the-problem)
- [Value proposition](#value-proposition)
- [Key features](#key-features)
- [How it works: agents and their roles](#how-it-works-agents-and-their-roles)
- [How it is being built: the AAMAD crew](#how-it-is-being-built-the-aamad-crew)
- [Getting started](#getting-started)
- [Project structure](#project-structure)
- [Next steps for contributors](#next-steps-for-contributors)
- [Licence and notices](#licence-and-notices)

---

## Overview

Regulated investment funds get their filing obligations as legal text. Compliance teams read that
text and turn it into deadlines by hand, again for every new framework.

This project tests whether AI agents can do the first reading safely. For one fictional Luxembourg
UCI Part II fund (`FND-DEMO-01`), the system:

1. **extracts** each obligation from mock regulatory text, quoting its exact source paragraph,
2. **verifies** every quote and flags where sources disagree, using a separate checker,
3. **judges** which obligations apply to the fund, with reasons,
4. **calculates** due dates with deterministic code, not a language model,
5. **publishes** a read-only calendar for the fund manager (GP), but only after a specialist has
   approved the work at **three gates**.

The MVP is built as the **first configuration of a shared product**, so that other fund types,
jurisdictions and clients can be added later through configuration rather than copies. Only the Part II
configuration is built.

| | |
|---|---|
| **Primary user** | Compliance specialist: reviews agent output and approves at gates G1–G3 |
| **Secondary user** | GP / fund manager: reads the published calendar, changes nothing |
| **Platform** | Web (two surfaces: specialist review, GP calendar) |
| **Accessibility** | WCAG 2.2 AA |
| **Runtime (recorded)** | CrewAI. The agent design itself is decided in the SAD. |

## The problem

- **Manual interpretation.** Specialists turn static legal text into deadline rules by hand. Each new
  framework repeats the work.
- **Inconsistent rules.** In the illustrative scenario for a fictional firm, documents describing the
  same obligation disagreed (for example, on an annual-report deadline). No check caught the mismatch.
- **Overlapping sources.** A Part II fund's obligations come from several layers of rules: Luxembourg
  product law, the AIFM Law, EU rules such as PRIIPs and SFDR, and tax, registry and cross-border
  rules. Each has its own authority, deadlines and wording.
- **GPs can't read it.** Fund managers are accountable for filings but file few of them, and may be
  less familiar with Luxembourg rules. They need to know what is due, when, who files and why, without
  reading legal text.

No time or cost saving has been measured. The user needs are inferred from the project brief and an
illustrative scenario, not from interviews. The demo is their first test.

## Value proposition

**The specialist moves from *writing* rules to *checking* them.**

What makes the output trustworthy, compared with today's manual process:

| Principle | What it means |
|---|---|
| **Every rule shows its source** | Each row carries a paragraph ID and a word-for-word quote. |
| **A separate verifier** | A second check, independent of the extractor, tests every quote and looks for conflicts. It flags problems and never fixes them itself. |
| **People approve, at three gates** | Nothing reaches the GP until a specialist approves the rules (G1), the applicability verdicts (G2) and the calendar (G3). |
| **Dates come from code** | Due dates are calculated by deterministic code, so the same inputs always give the same calendar. |
| **Everything is logged** | Every agent output and human decision goes into an add-only audit log. |
| **Results are measured** | Each run is compared with a written answer key. A missed target is reported, not hidden. |

## Key features

MVP features (P0) from the [PRD](project-context/1.define/prd.md):

| ID | Feature | What it does |
|---|---|---|
| F1 | Source-linked extraction | Turns mock regulatory text into fixed obligation rows, each quoting its source paragraph. |
| F2 | Independent verification | Checks every quote, and flags internal and cross-source conflicts with evidence. |
| F3 | Gate G1: rule approval | Specialist approves, edits or rejects each row. Any edit re-runs the verifier. |
| F4 | Applicability verdicts | Judges each approved rule as *applies*, *does not apply* or *unsure*, citing fund facts. |
| F5 | Gate G2: applicability approval | Specialist confirms or overrides each verdict and decides every "unsure". |
| F6 | Deterministic calendar | Code calculates due dates, including weekend rolls and event-triggered deadlines. |
| F7 | Gate G3: publish | Specialist publishes the whole calendar at once, or declines with a reason. |
| F8 | GP read-only calendar | Shows what is due, when, who files and why, with the source quote. |
| F9 | Audit log and evaluation | Records every output and decision, and scores the run against the answer key. |
| F10 | *Stretch:* change monitoring | Works out which obligations a rule amendment affects. Built only if the core is finished. |

**Out of scope for the MVP:** filing status and confirmations, notifying filing parties, multiple funds
or frameworks, real authentication, and live connections to regulators or email. Stable calendar-entry
IDs keep the door open for filing status later.

### Success targets

| Measure | Target |
|---|---|
| Extraction | 6 of 6 rows, no extras |
| Applicability | 6 of 6 verdicts |
| Verifier | Both planted conflicts caught, no false alarms |
| Calendar | 22 of 22 entries, exact dates |
| Gate enforcement | 100% of bypass attempts refused |
| Run time / cost | Under 5 minutes, under US$2 per run |
| Specialist review time | Under 30 minutes for G1–G3 |

## How it works: agents and their roles

> ⚠️ **Planned, not final.** The brief names three AI responsibilities. How they map to actual CrewAI
> agents, and whether more agents are needed, is decided in the SAD by `@system.arch`. The table below
> shows the *responsibilities* and the rules they must follow, not a final agent roster.

```
 Mock regulatory text ──► [1] Extraction (AI) ──► [2] Verification (AI, separate)
                                                              │
                                                    ◆ G1  Specialist approves rules
                                                              │
 Mock fund profile ─────► [3] Applicability (AI) ◄────────────┘
                                   │
                         ◆ G2  Specialist confirms verdicts
                                   │
                          [4] Calendar dates (deterministic code, no AI)
                                   │
                         ◆ G3  Specialist publishes
                                   │
                          GP read-only calendar

 Every step and decision ──► add-only audit log
```

| Step | Responsibility | Done by | Rules it must follow |
|---|---|---|---|
| 1 | **Extraction** | AI agent | One paragraph ID and a verbatim quote per row. Marks the business-day rule "not confirmed" when the source is silent. |
| 2 | **Verification** | AI agent, separate from extraction | Quote check, internal-conflict check, cross-source check. Flags with evidence. Never changes a row. |
| G1 | Rule approval | Compliance specialist | Each row decided one by one. Overriding a flag needs a written reason. |
| 3 | **Applicability** | AI agent | Verdict of applies / does not apply / unsure, with reasoning and at least one fund-fact ID. |
| G2 | Verdict approval | Compliance specialist | Cannot finish while any verdict is "unsure". Overrides need a reason. |
| 4 | **Calendar generation** | Deterministic code | Not an AI task. Same inputs, same dates. Testable without a language model. |
| G3 | Publish | Compliance specialist | Whole calendar at once. Refused unless G1 and G2 are complete. |
| — | *Stretch:* impact assessment | To be decided in the SAD | May flag affected items for re-review. Never changes a rule, verdict or date itself. |

**Hard limits on every agent:** agents read only the mock sources and the mock fund profile. They have
no tools to approve, publish or write to the calendar. The language-model provider is the only live
service. Invalid agent output stops the run, and nothing partial is ever published.

## How it is being built: the AAMAD crew

This repo uses [AAMAD](docs/aamad-framework.md), a framework where AI "personas" each own one part of
the work and hand over through written documents in `project-context/`. Persona definitions are in
[`.cursor/agents/`](.cursor/agents/).

| Phase | Persona | Owns | Status |
|---|---|---|---|
| 1. Define | `@product-mgr` | Requirements, PRD, user stories | ✅ Done (handover approved 2026-11-09) |
| 1. Define | `@system.arch` | Architecture (SAD): pattern, agent roster, estimate | ✅ Done (SAD complete for the MVP; Build-week records only) |
| 1. Define | `@ux.designer` | Interaction design and visual direction (`ux.md`) | ✅ Done (`ux.md` and the style note; edits on request) |
| 2. Build | `@project.mgr` | Project scaffold and environment | ✅ Done (setup, git hooks, CI recorded in `setup.md`); keeps the plan and README current |
| 2. Build | `@frontend.eng` | Specialist and GP web surfaces | 🟡 Pages and calendar views built; closing checks and the visual snapshot refresh wait for the operator |
| 2. Build | `@backend.eng` | Agents, gates, date code, storage | 🟡 Stand-in path built and the first green path passes; real agents (CrewAI, one retry, a trace line per request) are built and tested against a fake model service only; the runner for the spike's first real call is built and the operator makes that call (steps in [`setup.md`](project-context/2.build/setup.md), "Run the spike's first real call") |
| 2. Build | `@integration.eng` | Connecting frontend and backend | Not started (no separate step so far: the pages call the services directly) |
| 2. Build | `@qa.eng` | Tests and evaluation against the answer key | 🟡 Answer-key tests and the green path co-owned; `qa.md` written; B8 Stage A and Stage B graders built (read a finished run, no model call); run starter, trace export, void rule and the model-calling cases come after the spike |
| 2. Build | `@security.eng` | Security review before delivery | Not started (the final acceptance block, B10) |
| 3. Deliver | `@devops.eng` | Run instructions and user guide | 🟡 Run instructions are in [Getting started](#getting-started); the rest is not started |

## Getting started

The app runs on your own machine as one process: a FastAPI server that shows the seven pages and
runs the review. **It uses stand-in agents: fixed test answers, no AI model is called and nothing
costs money.** Every page says so. Real model calls come later, only for measured runs (see the
SAD's Build card).

### Prerequisites

- **Git**
- **[uv](https://docs.astral.sh/uv/)**, which `make install` uses to create the Python 3.12
  environment (the app needs Python `>=3.12,<3.14`)
- **make** (preinstalled on macOS and Linux)
- **Node.js**, only if you want to run the visual check (see "Checks")

### 1. Install

```bash
git clone <this-repo-url>
cd capstone
make install              # creates .venv (Python 3.12), installs the app, test and dev tools, git hooks
cp .env.example .env      # your local settings; .env is git-ignored and never committed
```

Then open `.env` and set `SESSION_SECRET` to any long random value, for example the output of:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Leave `AGENTS_MODE=stand_in`. No API key is needed.

### 2. Run the app

```bash
make run                  # open http://localhost:8000 ; stop it with Ctrl+C
```

`http://localhost:8000/health` answers `{"status": "ok"}` once the app is up. The database is a single SQLite
file, `data/app.db`, created on first start.

**Sign in** with one of the two mock identities (no password; sign-in is a demo, not access
control):

- **Compliance specialist**: Filing rules, start a review, check and decide at each step, publish.
- **General Partner / Fund Manager**: the published calendar only, view only.

### 3. Walk through a review (the demo path)

This is the path the automated green-path test follows (`tests/tier1/test_green_path.py`).

1. Sign in as the **General Partner**: the calendar says it is being prepared. **Sign out.**
2. Sign in as the **Compliance specialist**. On **Filing rules**, tick **"Add the demo rule
   (rule 7)"** and press **Start a new review**. The review page fills in item by item (each
   stand-in step waits about a second, so you can watch it work).
3. **Step 2, check the rules** (7 rules). For each rule, choose **Approve** or **Reject**:
   - On **rule 7 (the demo rule)**, try **Approve**: the server refuses it, because its quote is
     genuine but does not support the rule. Choose **Reject** and give a reason, for example
     "Quote doesn't support the rule".
   - To approve, choose what happens **if the deadline falls on a weekend or holiday**. The demo
     uses: rule 1 *following working day*, rule 2 *keep the date*, rule 3 *following working day*,
     rules 4 and 5 *preceding working day*, rule 6 *keep the date*.
   - Where the source doesn't say **who files**, pick one: rules 2 and 3 *Fund administrator*,
     rule 5 *AIFM*, rule 6 *Tax advisor*.
   - **Rule 3** carries a checker flag (two sources disagree), so approving it needs a short
     reason.
   - Press **Finish checking**.
4. **Step 3, confirm what applies** (6 answers). Confirm each answer the AI gave. On **rule 4**
   the AI can't tell (registration not confirmed): choose **Yes, add it until someone confirms**
   and give a reason. Press **Finish and calculate dates**.
5. **Step 4, publish.** Check the 22 dates, read the rejected rule and the unused paragraphs, tick
   the box that says you've read them, and press **Publish calendar**.
6. Sign out and sign in as the **General Partner**: the published calendar shows 22 dates, 4 of
   them marked "May not be required".

**See a failed review:** tick **"Make step 1 fail (demo)"** on the start form. Step 1 stops at its
first unit, the review ends as failed, and the page offers a new review.

**Start again from nothing:** stop the app and delete `data/app.db`.

### Settings (`.env`)

| Setting | What it does |
|---|---|
| `AGENTS_MODE` | `stand_in` (the default): fixed answers, no model. `real` is for the spike command only and is given on the command line, not in `.env` (see [`setup.md`](project-context/2.build/setup.md), "Run the spike's first real call"); keep `stand_in` here |
| `STAND_IN_UNIT_PAUSE_S` | Seconds each stand-in step waits, so you can watch the units fill in. Default 1 |
| `RUN_COST_CAP_USD` | The hard stop on one review's model cost. Default 2.50 (always 0 with stand-in agents) |
| `STAGE_TIME_LIMIT_A`, `_B`, `_C` | Seconds before a step is stopped as too slow. Defaults 375, 150, 30 |
| `SESSION_SECRET` | Signs the sign-in cookie. Any long random value |
| `DATABASE_PATH` | Where the SQLite file is. Default `data/app.db` |

`OPENAI_API_KEY` and `SPEND_ACTIVITY` are only for real model calls; leave them as they are.

### Checks

| Command | What it checks | Where it also runs |
|---|---|---|
| `make test` | Every test, stand-in agents, no model call | CI (Tier 1 blocks a merge; Tier 2 reports) |
| `make lint` | Python lint with `ruff` | CI (blocks a merge) |
| `.venv/bin/aamad validate` | The planning documents pass the framework's quality gates | Git hooks and CI |
| `cd tests/visual && npm run test:visual` | Screenshots of every page against the approved ones | Nowhere else; run by hand after a page change |
| The real-name scan in [`CLAUDE.md`](CLAUDE.md) | No real names in committed files | Git hooks only (maintainers; it needs the private list in `reference/`) |

CI is GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)), on every pull
request. The visual check needs a one-off install: `cd tests/visual && npm install
--ignore-scripts && npx playwright install chromium`.

### Grade a finished review (evaluation)

The graders in `backend/evaluation/` score a **finished** review against the answer key. They only
read the database: they start nothing, call no model, need no key and cost nothing.

```bash
.venv/bin/python -m backend.evaluation RUN-20261121-1            # Stage A, and Stage B if the review finished it
.venv/bin/python -m backend.evaluation RUN-20261121-1 --stage b  # Stage B only
.venv/bin/python -m backend.evaluation RUN-20261121-1 --no-save  # print the report, save nothing
```

Use your own review ID (it is in the review page's address). Stage B can be graded once the review
has reached its second approval step (G2). A review that stopped earlier, or an unknown ID, prints
"Nothing to grade" and exits with 2. Any report, even one full of misses, exits with 0.

| Criterion | What it reports | Passes when |
|---|---|---|
| EC-004 | The six applicability verdicts against the answer key | All six match, every verdict cites an existing fact, and the two named rows cite the named facts |
| EC-010 | Agent time over every model step | Strictly under 5 minutes |
| EC-012 | Model cost over every model step | Strictly under US$2, and the trace adds up to the review's own cost count |

- **Stand-in reviews** are stamped "does not count towards the cycle". EC-010 and EC-012 show the
  measured numbers but are marked "not tested", because a stand-in step takes milliseconds and costs
  nothing, so a pass would say nothing.
- **Information-only notes (EC-004):** if a verdict leaves out facts that the key lists for it, the
  report adds a note. A note never changes the result.
- **Late calls (EC-010, EC-012):** a call that finished after the step had already been stopped is
  still counted, and the report says how many seconds and dollars were late.
- **Saved reports** go to `project-context/2.build/logs/<review ID>/`, one new numbered file each
  time. That folder is not git-ignored, so check `git status` before you commit.

More detail: [`setup.md`](project-context/2.build/setup.md#grade-a-finished-run-b8-slices-1-and-2-h-070)
and [`qa.md`](project-context/2.build/qa.md).

### Troubleshooting

- **"Address already in use"**: another app holds port 8000. Stop it, or start this one on another
  port: `.venv/bin/python -m uvicorn backend.main:create_app --factory --port 8001`.
- **"Review N is still in progress, so a new review can't start"**: only one review runs at a
  time. Open it from Filing rules and
  finish it, or abandon it while it waits at a step.
- **A review stuck on "working" after a restart**: on start-up the app marks any review that was
  interrupted mid-step as failed ("service restarted"); start a new one.

### Work on the planning documents

#### Read in this order

1. [`capstone-brief.md`](project-context/1.define/capstone-brief.md): one-page summary
2. [`prd.md`](project-context/1.define/prd.md): happy path, features, constraints
3. [`system-description.md`](project-context/1.define/system-description.md): every requirement and
   acceptance criterion
4. [`user-stories/README.md`](project-context/1.define/user-stories/README.md): 15 stories and the
   demo decisions at each gate
5. [`mock-data/`](project-context/1.define/mock-data/): the inputs and the answer key
6. [`decision-log.md`](project-context/1.define/decision-log.md): what changed and why

#### Work with a persona

You also need an AI coding tool that can load persona files, such as Claude Code or Cursor. Open
the repo in it, load a persona file and give it a command. For example, in Claude Code:

```
@.cursor/agents/system-arch.md *create-sad
```

Each persona's file lists its commands, the files it reads and the files it may write.

## Project structure

```
capstone/
├── README.md                 # This file
├── AGENTS.md                 # AAMAD personas and workflow
├── CLAUDE.md                 # Project rules for Claude Code (public-repo rules, checks)
├── CHECKLIST.md              # AAMAD phase checklist
├── aamad.config.yml          # Project mode (greenfield) and runtime (crewai)
├── NOTICES                   # Third-party notices
│
├── .cursor/
│   ├── agents/               # Persona definitions (product-mgr, system-arch, ...)
│   ├── rules/                # Framework rules, incl. approval design and runtime adapters
│   ├── skills/               # Reusable skills (approval design, diagram drawing)
│   ├── prompts/              # Phase prompts
│   └── templates/            # Templates for PRD, SAD, stories, ...
│
├── project-context/
│   ├── 1.define/             # ✅ Define phase documents
│   │   ├── capstone-brief.md
│   │   ├── mrd.md            # Evidence note (internal tool, no market claims)
│   │   ├── system-description.md
│   │   ├── prd.md
│   │   ├── context-summary.md   # Handover to the architect
│   │   ├── approval-map.md      # Where humans approve, and what they see
│   │   ├── decision-log.md
│   │   ├── user-stories/     # US-001 to US-015
│   │   ├── mock-data/        # Mock sources, fund profile, answer key
│   │   └── prototypes/
│   ├── 2.build/              # Build artifacts: setup, scaffold plan, UX note, backend notes
│   └── 3.deliver/            # Empty until Deliver
│
├── backend/                  # The one FastAPI app: services, runtime, pages, stand-in agents, evaluation graders
├── config/                   # The fund profile, the regulation (sources, holidays), the demo row
├── tests/                    # tier1/ blocks merges; tier2/ if time allows
├── pyproject.toml            # App dependencies (pinned)
├── Makefile                  # make install, make run, make test, make lint
├── .github/workflows/ci.yml  # CI: lint, tests, framework validator (no model, no name scan)
│
└── docs/
    ├── aamad-framework.md    # The AAMAD framework's own README
    ├── learning-notes.md     # Lessons learned while building
    └── ai-direction-log.md   # How the AI tools were directed
```

Two paths are **git-ignored** and never committed: `reference/` (private source material) and `.env`
(secrets).

## Next steps for contributors

### What happens next

1. ✅ **Define is done.** The operator approved the handover on 2026-11-09, and the SAD, the
   interaction design (`ux.md`) and the style note followed.
2. ✅ **The stand-in app is built.** Project setup and CI, the service layer and gates, the stand-in
   agents and the two stages they feed, the date code, the planted demo row, the failure demo, the
   seven pages and the calendar views. **The first end-to-end green path passes** (start, three
   steps, publish, the General Partner's view, the audit log), with no model call.
3. ✅ **The AI models are picked and the real agents are built.** CrewAI is installed and the three
   agents sit behind the same functions, with one retry after a timeout or a server error and a
   trace line for every request. They are tested against a fake model service only: no real key, no
   paid call, and `AGENTS_MODE` stays `stand_in` in `.env`.
4. **Next: the spike.** The runner for the first real call is built; the operator makes that one call from their own terminal, then the rest of the spike's calls with timings follow,
   then the rest of the evaluation runner (the graders for the first two stages are done and read a
   finished run; the run starter and the reports on cost are not), tuning the prompts and one
   evaluation cycle. After the spike the operator decides whether a call that drifts from the pinned
   reasoning setting counts as a failure.
5. **Alongside:** refresh the visual snapshots (the operator approves them), then retry, the light
   visual pass if time allows, and the final acceptance, security and run-instruction pass.
6. **Settle the open operator questions:** four-eyes review timing, programme submission
   requirements, the origin of the reused prototype front end, and a manual-effort estimate for the
   demo obligations. See *Open Questions* in the [PRD](project-context/1.define/prd.md#open-questions).
7. **Deliver**, following [`AGENTS.md`](AGENTS.md) and [`CHECKLIST.md`](CHECKLIST.md).

### How to contribute

- **Review the Define documents.** Raise an issue that cites the requirement ID (for example
  `SD AC-010` or `PRD F6`), so every comment traces to a requirement.
- **Use the persona that owns the file.** Each persona may only write its own documents. For example,
  the PRD belongs to `@product-mgr` and the SAD to `@system.arch`.
- **Work on a branch.** Never commit to `main`. Changes reach `main` only through a reviewed pull
  request.
- **Run the checks** before opening a pull request (see [Checks](#checks)): `make test`,
  `make lint`, `.venv/bin/aamad validate`, and the real-name scan in [`CLAUDE.md`](CLAUDE.md)
  (maintainers only; it needs the private list in `reference/`). CI runs all but the scan.

### Rules for this public repository

- **Mock data only.** No real company, fund, platform, service-provider or people names, and no
  internal dates or document details.
- **No employer material.** Evidence, examples and personas use only the fictional firm and public
  regulation.
- **No secrets.** API keys stay in `.env`, which git ignores.
- **Not legal advice.** Outputs are specialist-approved interpretations of mock text.

## Licence and notices

This project is built on the AAMAD framework, which is licensed under Apache 2.0. Third-party material
bundled with the framework is listed in [`NOTICES`](NOTICES). A licence for this project's own content
has not been chosen yet.
