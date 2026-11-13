# Project setup: Block B1 (Setup and data)

Owner: `@project.mgr`. Source: `project-context/1.define/sad.md`, "Implementation Guidance for AI
Development Agents" (Build card, Never row, Order of work, Rules every Build persona follows).
This file records setup only. It contains no application logic.

## Scope & Guard Rules (Build Week)

Every Build persona reads this first. A concise copy lives in the root `CLAUDE.md`.

- Build ONLY from `sad.md` → `### Build card (one page for the build personas)`.
- NEVER build items from `Future Work`, `Appendix A` (F-18 hosted demo / S1–S4 / `DEPLOY_MODE` / CSRF), or git tag `sad-full-design` (reference only). If something is missing, stop and ask.
- Default `AGENTS_MODE=stand_in`. Do NOT run `AGENTS_MODE=real` or the B3 spike until the full stand-in happy path is green (start → Stage A → G1 + demo-row refusal/reject → Stage B → G2 → Stage C → G3 ack → GP view + audit) AND `SOQ-25` / `DL-40` is pinned.
- Tier 1 tests block merges (include `EC-015`, `EC-019`, and `T-MODE-1`). If the day-3 tripwire drops Tier 2, `T-MAP-1` must still pass before the first eval run.
- Never put date math in a model, gate checks in templates/handlers, tools/memory on agents, or the answer key in prompts.
- New tools, memory, retries, or re-asks require a SAD change first, never a code workaround.
- Netlify summary rule: Netlify hosts the standalone page `docs/architecture-decisions-summary.html` as the public context page (the `.md` beside it is its source). **Decided: frozen.** The page carries the banner "Snapshot as of 12 Nov — see sad.md for Build-week deltas" and stays frozen until after the demo. Update it during Build week only if a DL change is huge. The page is public, so any edit follows the same no-real-names rule as the rest of the repo.

The Never row, verbatim in meaning: a model never computes a date, approves, publishes or holds a
tool; the answer key or the mock files' notes never reach a prompt; a check never lives in a page
handler; the planted row is never approved (its Approve button stays visible and the server refuses
it, DL-44).

### Timing guardrails from the Build card

- Plan 5 days, **8 days hard stop**. Tripwire: if the first stand-in green path has not passed by
  the end of day 4, drop B6 and Tier 2, never T-MAP-1.
- Checkpoint: if B1 and B2 together pass 1.3 days, tell the operator at once.
- Order: B1 → B2 → B3 (stand-in only) → B4 → B5 → B7 → **first green path** → pin DL-40 → B3 spike
  → B8 → B9 → B6 → B10.

## Runtime target

| Setting | Value | Where |
|---|---|---|
| `AAMAD_TARGET_RUNTIME` | `crewai` | `.env` (git-ignored, already set) and `.env.example` |
| `runtime.target` | `crewai` | `aamad.config.yml` (already set) |
| `project.mode` | `greenfield` | `aamad.config.yml` |

## CrewAI settings (D1 to D6)

Recorded as given by the operator. The per-item D-numbers are not mapped here because the SAD uses
them for other things too (for example D4 for the trace export); confirm the mapping with the
architect before anyone cites a single D-number.

- Three crews, **one agent and one task each** (extractor, verifier, judge). No multi-agent crew, no
  Flow.
- Each task returns a typed result through **`output_pydantic`**.
- **No tools** on any agent.
- **No memory.**
- **No delegation** (`allow_delegation` off).
- **`guardrail_max_retries: 0`.** No automatic retry or re-ask. The only retry is the one allowed
  per model call by the Timeouts row (a second timeout becomes `model service`).

Nothing in this block installs or imports CrewAI. Dependencies come in with the backend block (B2),
by `@backend.eng`, and are recorded here when they do.

## Environment variables

`.env.example` is committed with placeholders only. Copy it to `.env` (git-ignored) to run locally.

| Variable | Default | Purpose |
|---|---|---|
| `AAMAD_TARGET_RUNTIME` | `crewai` | Framework runtime target |
| `AGENTS_MODE` | `stand_in` | `stand_in` = fixed outputs, no model call, no cost |
| `OPENAI_API_KEY` | placeholder | Only read when mode is not `stand_in`. Never commit a real key |
| `RUN_COST_CAP_USD` | `2.50` | Hard stop per run |
| `SPEND_ACTIVITY` | empty | Which of the five paid activities (spike, tuning, evaluation, rehearsal, demo) |
| `CALL_TIMEOUT_EXTRACT_S` / `_VERIFY_S` / `_JUDGE_S` | 90 / 60 / 60 | Per-call timeouts (Build card) |
| `HTTP_TIMEOUT_EXTRACT_S` / `_VERIFY_S` / `_JUDGE_S` | 85 / 55 / 55 | HTTP client, a few seconds below the call timeout |
| `STAGE_LIMIT_A_S` / `_B_S` / `_C_S` | 375 / 150 / 30 | Stage limits, on the backend's timer, not `max_execution_time` |

**Open points to confirm against `sad.md` §4** (this block was told to read only the Implementation
Guidance section, so these were not checked):

- The exact variable names for the timeouts and `SPEND_ACTIVITY`. The names above are chosen here.
- The exact HTTP timeout values (the Build card says only "a few seconds lower").
- The accepted values of `SPEND_ACTIVITY`.

Spend rule from the Build card: real calls only for the spike, tuning (60 calls), one evaluation
cycle, the rehearsal and the demo. Keep US$5 in reserve for the rehearsal and the demo.

## Git hooks

Hooks live in the tracked folder `scripts/git-hooks/` so they are versioned and reviewable. Git is
pointed at it with a **local** setting, which each clone must run once:

```bash
git config core.hooksPath scripts/git-hooks
```

| Hook | Runs | Does |
|---|---|---|
| `pre-commit` | before every commit | `run-checks.sh` |
| `pre-push` | before every push | `run-checks.sh` |

`run-checks.sh` runs three checks and **fails closed** (if a check cannot run, the commit is
blocked):

1. Blocks if `reference/` or `.env` is staged.
2. Real-name scan against `reference/real-identifiers.txt` (the same command as `CLAUDE.md`). On a
   hit it prints file and line only, so the log never repeats a real name.
3. `.venv/bin/aamad validate`.

## What is not done in this block

- No backend, frontend, agent or CI code, and no dependency installs (B2 onward).
- No `README.md` created or changed.
- No diagram was needed.

## Hand-off: what is next for each downstream agent

| Agent | Next |
|---|---|
| `@backend.eng` | **B2**: service layer, run states and gate checks, before any page or agent. Installs dependencies (CrewAI and the web stack) and records them here. Checkpoint at 1.3 days for B1 + B2 |
| `@ux.designer` | `ux.md`, the page-by-page note for the seven pages, needed before B5 |
| `@frontend.eng` | B5 templates in `backend/web/`, after `ux.md` and B2 |
| `@qa.eng` | B4 date engine against the 22-entry answer key; Tier 1 tests; the first green path with `@backend.eng` |
| `@security.eng`, `@devops.eng` | B10 only. Nothing now |
| Operator | Pin DL-40 only after the first green path passes. Redeploy the Netlify page after this branch merges so the banner goes live |

## Sources

- `project-context/1.define/sad.md`, section "Implementation Guidance for AI Development Agents"
  only (Build card, Never row, Order of work, Rules every Build persona follows, Scope guardrails).
- `.cursor/agents/project-mgr.md` (persona and limits), `.cursor/rules/adapter-crewai.mdc`
  (checked: it does not number D1 to D6).
- `CLAUDE.md` (the two checks the hooks run), `aamad.config.yml`, the existing git-ignored `.env`.
- The CrewAI settings list was supplied by the operator in the B1 request.

Not read or used: Future Work, Appendix A, git tag `sad-full-design`.

## Assumptions

- Hook scripts in `scripts/git-hooks/` are setup tooling, not application code.
- The timeout variable names, HTTP timeout values and `SPEND_ACTIVITY` values are provisional (see
  "Open points" above).
- Hooks are enabled per clone with `git config core.hooksPath scripts/git-hooks`.

## Open Questions

- **Open.** Do the variable names in `.env.example` match `sad.md` §4? Checked 2026-11-13: not all
  of them do. `CALL_TIMEOUT_*_S` should be `CALL_TIMEOUT_EXTRACT`, `_VERIFY`, `_JUDGE`, and
  `STAGE_LIMIT_*_S` should be `STAGE_TIME_LIMIT_A`, `_B`, `_C`. §4 does not name the
  `HTTP_TIMEOUT_*` variables (it only says the HTTP timeout sits a few seconds below the call
  timeout). §4 also lists variables not yet in `.env.example`: `LLM_MODEL_*`, `LLM_MAX_TOKENS_*`,
  `SESSION_SECRET` and `DATABASE_PATH`. Waiting on the operator's decision before renaming.
- **Resolved (H-002).** Does the validator's hard requirement for `qa.md` once `2.build/` has
  content stay, or should the hook treat it differently? Decision: the hook ignores only the one
  finding `project-context/2.build/qa.md: Build artifact missing`. Every other validator error still
  blocks. The exception in `scripts/git-hooks/run-checks.sh` is temporary and is removed when
  `@qa.eng` writes `project-context/2.build/qa.md`.

## Audit

- 2026-11-13 · persona `project-mgr` · action `setup-project`, `configure-env`, `document-setup` ·
  `AAMAD_TARGET_RUNTIME=crewai` · created this file, `.env.example`, `scripts/git-hooks/`
  (pre-commit, pre-push, shared checks) and the Scope & Guard Rules block in `CLAUDE.md`. No
  application code and no dependency installs. No model call was made. The hooks were tested: the
  `.env`-staged block fires.
