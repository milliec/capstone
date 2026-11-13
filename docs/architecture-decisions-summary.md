# Architecture decisions at a glance

> **Snapshot as of 12 Nov — see [sad.md](../project-context/1.define/sad.md) for Build-week deltas**

A plain-language summary of the System Architecture Document (`project-context/1.define/sad.md`)
and the decision log, as of 2026-11-12. The SAD is the source of truth; this page only summarises it.

| Question | Short answer | Status |
|---|---|---|
| Pattern | A **workflow**: three fixed stages with a human gate after each | Decided |
| Crews, Flows or hybrid | **Neither**: three single-agent CrewAI crews, called by plain Python functions | Decided |
| Agent design | Written as **agent cards** in SAD §2: role, goal, backstory, task, output, one example | Decided |
| Roster, tasks, handoffs | **3 agents**, about 17 calls a run, handing over only through stored data and people | Decided |
| LLM by role | Cheap / mid-tier / reasoning model per role; **exact model IDs on hold** | Pending (DL-40) |
| Deployment | **Local, one process**; a public hosted demo is an optional stretch goal | Decided |

---

## 1. Pattern, and why

**A workflow.** The order of work is written in code and never changes:

| Stage | What happens | Then |
|---|---|---|
| A | Extract rows, check quotes, flag conflicts | **G1**: specialist approves or rejects each row |
| B | Judge whether each approved row applies to the fund | **G2**: specialist confirms each verdict |
| C | Code works out every due date (no model) | **G3**: specialist publishes the calendar |

- **Why**: the path is known in advance and the three gates must sit at fixed points. A model
  never needs to decide what happens next. It is also easy to observe ("step 3 of 4 finished")
  and its cost and time are bounded.
- **Rejected**: a planning agent (it could skip or reorder work around a gate); one big model
  call (no separate checker, no gate between extraction and judgement); a self-correcting loop
  (the specialist, not a model, settles each flag); routing (every run takes the same path).
- **Reference shape**: a document pipeline, with a named route for every way a model can be
  wrong. No agent has a tool.

Sources: SAD Pattern Decision, Reference Architecture.

## 2. Crews, Flows or hybrid

**Neither a Flow nor a multi-agent crew.** Three separate CrewAI agents, each run on its own as a
one-agent, one-task crew, are called by plain Python "stage functions". The backend alone owns the
gates.

- **Where it started**: a hybrid, with a CrewAI Flow wrapping each stage (DL-17).
- **Why it changed**: with five focused days, the Flow added framework to learn and debug without
  changing who owns the gates (DL-35). The Flow is parked as future work (F-11).
- **"Multi-agent" here means** three agents with separate roles, models and prompts. They never
  talk to each other, and none plans its own steps.
- **CrewAI is still used** for the agents, their tasks, structured outputs, guardrails and limits.
  The library is free and open source; the cost is the model calls.

Sources: SAD §2, DL-17, DL-35.

## 3. Agent design

Each agent has a written **card** in SAD §2 ("Agent cards", DL-39). `agents.yaml` and
`tasks.yaml` are written from the cards.

| Agent | Role | Goal, in one line | Returns |
|---|---|---|---|
| Extractor | Regulatory text extractor | Turn one source document into fixed-schema rows, quoting the deadline word for word | Rows |
| Verifier | Independent checker | Report where a row disagrees with its own quote or with another source, with evidence | Flags |
| Judge | Applicability reviewer | Decide applies / does not apply / unsure, citing fund facts, in plain English | One verdict |

Each card also has a **backstory** (why accuracy matters and what to avoid), **numbered task
instructions**, the **inputs** (and what is deliberately left out), the **output schema**, a
**guardrail** (code that checks the output) and **one worked example**.

Rules that apply to all three:

- **No tools, no memory, no delegation**, at most 2 iterations.
- **No dates** in any output. Dates are always worked out by code.
- **Data sits inside tags**, instructions outside, so text in a source cannot act as an instruction.
- **The answers never reach a prompt.** The mock files contain test notes and a "Decides" column;
  the loader strips them, and a test (T-LEAK-1) fails if any gets through.
- **Each worked example is also a one-shot example in the prompt.** It uses invented text that is
  in no demo row and mirrors no demo trap (test T-EXAMPLE-1, plus a review table).
- **A failed check ends the run.** The model is never asked to try again.
- **The judge's key rule**: a fact counts only when what it asserts meets the condition as the
  rule words it; otherwise "unsure".

Sources: SAD §2 "Agent cards", DL-39, DL-41.

## 4. Roster, tasks and handoffs

| Agent | Calls per run | Sees | Never sees |
|---|---|---|---|
| Extractor | 5 (one per primary document) | One document's paragraphs | The secondary guide, the fund, the answer key |
| Verifier | 6 (7 with the planted demo row) | One row, its quote, all sources | The extractor's reasoning |
| Judge | Up to 6 (one per approved row) | The row as approved at G1, the fund facts | The verifier's flags, the "Decides" column |

About **17 model calls a run**. Everything else is code: loading, the quote check, the coverage
view, dates, gates and the audit log.

**Handoffs**

- Agents hand nothing to each other. Code builds each agent's input from stored data.
- People sit between the stages: **G1** (approve rows, set the business-day rule, and set "who
  files" when the source is silent), **G2** (confirm verdicts, decide every "unsure"), **G3**
  (publish, after acknowledging rejected rows and uncited paragraphs).
- "Who files" is never guessed. At G1 it is chosen from the **filing parties only** (AIFM, Fund
  administrator, Auditor, Local reporting agent (Spain), Tax advisor) or "not known".
- For grading, code maps the extractor's wording to a party name with a fixed lookup, frozen before
  the first evaluation run (EC-R11, DL-41).

Sources: SAD Work Ownership, Delegation Map, Pattern Decision, DL-39, DL-41.

## 5. LLM by role

| Role | Tier (decided) | Proposed model | Reasoning effort |
|---|---|---|---|
| Extractor | Cheapest | `gpt-6-luna` | none |
| Verifier | Mid-tier, a different model from the others | `gpt-6.1-terra`, or `gpt-5.6-terra` if your account has it | low |
| Judge | Reasoning | `gpt-6.1-sol` | medium |

- **Status: the exact IDs are on hold (DL-40)** until you check them against your OpenAI account's
  model list and pricing.
- **Why these tiers**: extraction is copying into a schema; the verifier must be independent of
  the extractor; the judge makes the judgement where a wrong "does not apply" costs most.
- **Family note**: the decisions require a *different model*, which the proposal meets.
  `gpt-5.6-terra` is a clearly different generation, if you want family-level independence.
- **Avoided**: `gpt-5-mini`, `gpt-5-nano`, `gpt-5` and `o3` shut down on 11 December 2026.
- **No temperature setting**: all current models are reasoning models, so each role gets a fixed
  reasoning effort instead.
- **Cost**: about US$0.30 to US$0.40 a run (estimate). Budget about US$15 in total, with a hard
  stop of US$2.50 per run. Building uses stand-in agents that call no model.

Sources: SAD Model and Context Strategy, SOQ-25, DL-25, DL-26, DL-36.

## 6. Deployment shape

**Core plan: local only.**

- One FastAPI process on your machine serves the pages and runs the stages, started with one
  command. Data is one SQLite file.
- Plain server-rendered pages with one stylesheet; no JavaScript framework (Next.js is post-course).
- CI on GitHub runs the checks that need no model, with the agents stubbed and no model key.
- Evaluation runs happen locally.

**Stretch goal: a hosted portfolio demo on Railway** (DL-38)

- Starts **only after the local demo works end to end**; it is the **first thing dropped**.
- **Public by design**, because there is nothing to reach: stand-in agents only, mock data, and no
  model key on the host (the app refuses to start with one).
- Safeguards: a "demo, mock data" banner on every page, a **Reset demo** button plus a nightly
  reset, mock sign-in to choose specialist or GP, and CSRF protection on every form.
- You confirm Railway's pricing and set a spend limit before deploying. If the visual pass is
  dropped, the link is not shared publicly until it is done.

Sources: SAD §5, §8, "Stretch goal: hosted portfolio demo", DL-33, DL-38.

---

**Still open**: the model IDs (DL-40, SOQ-25); Railway pricing and spend limit (SOQ-23 a);
the manual-effort figure (PRD A-9); story wording for `@product-mgr` (SOQ-27).
