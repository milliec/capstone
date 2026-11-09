# Regulatory Intelligence for Fund Compliance Calendars

AI agents read regulatory text and draft source-linked filing rules. A compliance specialist checks and
approves them, and ordinary code turns them into a fund's compliance calendar.

> **Status: Define phase.** Requirements, user stories and mock data are written. The architecture
> (SAD) is next. **There is no application code yet.**
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
| 1. Define | `@product-mgr` | Requirements, PRD, user stories | ✅ Done (handover not yet approved) |
| 1. Define | `@system.arch` | Architecture (SAD): pattern, agent roster, estimate | ⏳ Next |
| 1. Define | `@ux.designer` | Interaction design and visual direction (`ux.md`) | ⏳ After the SAD |
| 2. Build | `@project.mgr` | Project scaffold and environment | Not started |
| 2. Build | `@frontend.eng` | Specialist and GP web surfaces | Not started |
| 2. Build | `@backend.eng` | Agents, gates, date code, storage | Not started |
| 2. Build | `@integration.eng` | Connecting frontend and backend | Not started |
| 2. Build | `@qa.eng` | Tests and evaluation against the answer key | Not started |
| 2. Build | `@security.eng` | Security review before delivery | Not started |
| 3. Deliver | `@devops.eng` | Run instructions and user guide | Not started |

## Getting started

There is no app to run yet. These steps get you set up to read and work on the planning documents.

### Prerequisites

- Git
- Python 3.9 or later
- An AI coding tool that can load persona files, such as Claude Code or Cursor

### 1. Clone and set up

```bash
git clone <this-repo-url>
cd capstone

# Create an isolated Python environment and install the AAMAD command-line tool
python3 -m venv .venv
.venv/bin/pip install aamad
```

### 2. Check the documents pass the framework's quality gates

```bash
.venv/bin/aamad validate
```

### 3. Read in this order

1. [`capstone-brief.md`](project-context/1.define/capstone-brief.md): one-page summary
2. [`prd.md`](project-context/1.define/prd.md): happy path, features, constraints
3. [`system-description.md`](project-context/1.define/system-description.md): every requirement and
   acceptance criterion
4. [`user-stories/README.md`](project-context/1.define/user-stories/README.md): 15 stories and the
   demo decisions at each gate
5. [`mock-data/`](project-context/1.define/mock-data/): the inputs and the answer key
6. [`decision-log.md`](project-context/1.define/decision-log.md): what changed and why

### 4. Work with a persona

Open the repo in your AI tool, load a persona file and give it a command. For example, in Claude Code:

```
@.cursor/agents/system-arch.md *create-sad
```

Each persona's file lists its commands, the files it reads and the files it may write.

### Later: running the app

Once Build starts, the language-model API key will go in a local `.env` file. `.env` is git-ignored and
must never be committed. Setup and run instructions will be added by `@devops.eng` in the Deliver phase.

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
│   ├── 2.build/              # Empty until Build
│   └── 3.deliver/            # Empty until Deliver
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

1. **Approve the Define handover.** The operator signs off
   [`context-summary.md`](project-context/1.define/context-summary.md).
2. **Write the SAD** (`@system.arch`). It must:
   - choose the application pattern and the CrewAI agent roster,
   - estimate whether the work fits the **six-week** timebox, and agree a cut line between the core
     demo path and hardening,
   - estimate the stretch goal (F10) separately,
   - confirm or replace the intended frontend framework (Next.js),
   - walk through the two extensibility scenarios (a fictional RAIF, and possible marketing in
     Singapore) on paper,
   - list the code folders, so the approval-design rule can cover them.
3. **Design the interaction** (`@ux.designer` → `ux.md`).
4. **Settle the open operator questions:** four-eyes review timing, programme submission requirements,
   the origin of the reused prototype front end, and a manual-effort estimate for the demo obligations.
   See *Open Questions* in the [PRD](project-context/1.define/prd.md#open-questions).
5. **Build**, then **Deliver**, following [`AGENTS.md`](AGENTS.md) and [`CHECKLIST.md`](CHECKLIST.md).

### How to contribute

- **Review the Define documents.** Raise an issue that cites the requirement ID (for example
  `SD AC-010` or `PRD F6`), so every comment traces to a requirement.
- **Use the persona that owns the file.** Each persona may only write its own documents. For example,
  the PRD belongs to `@product-mgr` and the SAD to `@system.arch`.
- **Work on a branch.** Never commit to `main`. Changes reach `main` only through a reviewed pull
  request.
- **Run the checks** before opening a pull request:
  - `.venv/bin/aamad validate`
  - the real-name scan in [`CLAUDE.md`](CLAUDE.md) (maintainers only; it needs the private list in
    `reference/`)

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
