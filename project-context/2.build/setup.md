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
  **Forecast at 2026-11-17 (H-050, `@backend.eng`; effort only, the operator's clock decides):**
  B2 as scoped (real checks, V-12, Rule 9 and real stored data, start-up rule) is about 0.8 to
  1.0 day against the SAD's 0.5, so with B1 it is likely at or over 1.3. Rule 9 and stored data
  moved here from B3 (H-047), so B3's 1.0 day should shrink by a similar amount (not re-estimated).
  Still to come: B7 about 0.25 day, B13b about 0.25 day. The stage time limit and the Pydantic
  unknown-field refusal are B2 items in the SAD, not started and not estimated; count them.
  **Operator, 2026-11-17: B1 + B2 did not pass 1.3 days**, so nothing is dropped at this
  checkpoint. **Re-check after B7**, with the then-known time and the unestimated B2 items.
- Order (as in the `sad.md` Build card, after H-040 and DL-54): B1 → B2 → B3 (stand-in only) →
  B13a → B4 → B5 → **B12** → B7 → **first green path** → pin DL-40 → B3 spike → B8 → B9 → B13b →
  B6 → B10. **Drop order:** B6 and Tier 2, then B12 as a whole, then B13b; never T-MAP-1.
- **First green path passed on 2026-11-19 (H-056, `@backend.eng`).** `tests/tier1/test_green_path.py`
  (Tier 1; details in `backend.md` "The first green path", PR #105) drives start → step 1 → G1 with
  the demo row refused then rejected → step 2 → G2 → step 3 → G3 ack → GP view → audit log, with
  stand-in agents and no model. **The day-4 tripwire is cleared**: B6 and Tier 2 stay in the plan,
  and the "no paid call before the green path" rule is met on its first half. **Still closed:** the
  second half, the operator's pin of `SOQ-25` / `DL-40` (model IDs), which is the next item in the
  Order. `@qa.eng` co-owns the green path and may review the test. The B1 + B2 re-check "after B7"
  above is still the operator's call.

## Runtime target

| Setting | Value | Where |
|---|---|---|
| `AAMAD_TARGET_RUNTIME` | `crewai` | `.env` (git-ignored, already set) and `.env.example` |
| `runtime.target` | `crewai` | `aamad.config.yml` (already set) |
| `project.mode` | `greenfield` | `aamad.config.yml` |

## Python environment

| Setting | Value | Why |
|---|---|---|
| Python | 3.12.16 (installed with `uv python install 3.12`) | CrewAI 1.15.x requires Python >=3.10, <3.14 (PyPI metadata and docs.crewai.com install page, checked 13 Nov 2026). The operator's default Python 3.15.2 cannot install CrewAI. |
| Virtualenv | `.venv/` at the repo root (git-ignored), made with `uv venv --python 3.12 .venv` | The git hooks call `.venv/bin/aamad`, so the name must stay `.venv`. |
| Dev tooling | `uv pip install --python .venv -r requirements-dev.txt` (aamad 1.0.1) | Restores the framework validator used by the hooks. |

The previous Python 3.15 `.venv` was moved outside the repo as a backup on 13 Nov 2026 and can be
deleted once B2 installs CrewAI cleanly. `@backend.eng` installs CrewAI into this `.venv` in B2 and
pins the exact version here.

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

Nothing in this block installs or imports CrewAI. The app shell (`@backend.eng`, 2026-11-16) installed
the web stack, pinned in `pyproject.toml`: fastapi 0.163.1, uvicorn 0.54.0, jinja2 3.1.6,
python-multipart 0.0.34, itsdangerous 2.2.0, pyyaml 6.0.3; for tests, pytest 9.2.0 and httpx 0.28.1.
CrewAI still comes in with B3 (stand-in part) and is recorded here then.

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
| `STAGE_TIME_LIMIT_A` / `_B` / `_C` | 375 / 150 / 30 | Stage limits, on the backend's timer, not `max_execution_time` |
| `STAND_IN_UNIT_PAUSE_S` | `1` | Seconds each stand-in agent function waits per unit, so units finish one by one. Read **only** when `AGENTS_MODE=stand_in`; never in real mode; `0` in tests (sad.md §4, DL-54, T-PAUSE-1). Added to `.env.example` by `@backend.eng` in the app shell (2026-11-16), with the code that reads it |

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

1. Blocks if `reference/`, `.venv` or `.env` is staged, including a file or symlink named exactly
   `reference` or `.venv` (`.gitignore`'s `reference/` only matches real folders, so a symlink to
   one is not ignored; found 2026-11-16).
2. Real-name scan against `reference/real-identifiers.txt` (the same command as `CLAUDE.md`). On a
   hit it prints file and line only, so the log never repeats a real name. The scan skips
   `reference/`, `.venv`, `node_modules` and `.git` (H-038), and skips binary files with `-I`
   (H-044). If you change the command in the hook or in `CLAUDE.md`, change the other too. CI does
   not run the scan (H-003 keeps it local), so there is nothing to change there today.
3. `.venv/bin/aamad validate`.

**`--no-verify` is a stop-and-report, not a quiet fix (H-003 item 3; same rule as the root
`CLAUDE.md`).** Never commit or push with `--no-verify`. If a hook blocks, stop and tell the
operator. An agent that used `--no-verify` says so at once. CI (below) is the backstop for
`aamad validate` only; it cannot replace the name scan.

### CI (B1 follow-up, H-003 and H-057)

`.github/workflows/ci.yml` runs on every pull request and every push to `main`, with stand-in
agents (`AGENTS_MODE=stand_in`, pause 0), **no model key** and read-only permissions. It installs
`pip install -e ".[test]" -r requirements-dev.txt`. `requirements-dev.txt` pins `aamad==1.0.1` (keep
it in step with the local `.venv`) and `ruff==0.17.3`.

| Step | Blocks a merge? |
|---|---|
| `ruff check backend tests` (settings in `pyproject.toml`; formatting is not checked yet) | Yes |
| Tier 1 tests: `pytest tests/tier1 tests/test_answer_key.py` | Yes |
| Tier 2 tests: `pytest tests/tier2` | No (`continue-on-error` until promoted, `sad.md` §9) |
| `aamad validate`, with the same temporary `qa.md` exception as the hook | Yes |

- **H-003 item 1 (validator in CI): built.** The exception for the one finding `project-context/
  2.build/qa.md: Build artifact missing` is in `ci.yml` and in `run-checks.sh`. **H-002 removes both
  in the same change** when `@qa.eng` writes `qa.md`.
- **H-003 item 2 (no name scan in CI): built.** CI never runs the scan, and
  `reference/real-identifiers.txt` is never uploaded, copied into a secret or committed.
- **H-003 item 3:** recorded above.
- Details and the lint fixes that got CI green: `backend.md` "B1 follow-up: CI". `make lint` runs the
  same lint locally.

## Tests and checks

| Check | Command | Runs in the hook or CI? |
|---|---|---|
| All Python tests (stand-in agents, no model call) | `make test` | By hand; **CI runs them too** (Tier 1 blocks, Tier 2 does not) |
| Lint (ruff) | `make lint` | **CI** (blocks) |
| Framework validator | `.venv/bin/aamad validate` | The commit and push hooks, and **CI** (both with the temporary `qa.md` exception) |
| Real-name scan | the command in `CLAUDE.md` | The commit and push hooks only. **Never CI** (H-003) |
| Visual check (Playwright snapshots of the stubbed UI) | `cd tests/visual && npm run test:visual` | **No.** Not part of `make test`, the commit hook or CI |

**Visual check: install once** (needs Node; the app itself stays Python):

```bash
cd tests/visual && npm install --ignore-scripts && npx playwright install chromium
```

Playwright Test is pinned at 1.64.1 in `tests/visual/package.json`. To run it: `cd tests/visual && npm run test:visual`. Playwright starts the app itself on port 8777 with a fresh database, stand-in
agents and no pause (`STAND_IN_UNIT_PAUSE_S=0`), so no model is called and every run starts from
the same nothing.

**Snapshots are never re-recorded by the persona that changed the page.** A failed snapshot is
reported; `@frontend.eng` proposes the new snapshots and the operator approves them (`CLAUDE.md`,
check 3; `frontend.md` §11.1).

## Persona sessions: one worktree each

**Rule: two Claude Code sessions never share one working folder.** (On 2026-11-17 a `git stash` in
the shared folder briefly removed another session's uncommitted work, and a second session edited
`ux.md` in that window.) Each persona session works in its own git worktree, on its own new branch.
The main folder (`capstone/`) is the operator's: no persona session runs in it.

**Start a session**, from the main folder:

```bash
scripts/new-session.sh <persona> <new-branch>        # e.g. frontend.eng frontend/calendar-fix
cd ../capstone-worktrees/<persona> && make install    # once per worktree
```

The script creates `../capstone-worktrees/<persona>` (outside the repo, so the real-name scan never
reads a second copy) on a **new** branch cut from `main`. It refuses `main` as the branch and an
existing folder. Git itself refuses a branch that is already checked out in another worktree.
Then open the Claude Code session **in that folder**. One worktree per persona at a time; the
branch can carry more than one block.

**What the script links or copies** (these are git-ignored, so a new worktree would not have them):

| Item | How | Why |
|---|---|---|
| `reference/` | symlink to the main folder's | the commit hook needs `reference/real-identifiers.txt`. The symlink is hidden by the shared `.git/info/exclude` (`/reference`), because `.gitignore`'s `reference/` does not match a symlink |
| `.env` | **copy** | each session may set its own values; still git-ignored |
| private `docs/` entries (`prototype/`, `assets/`, …) | symlink, one per entry | the two public docs stay real, tracked files; the `docs/*` rule ignores the links |

**What each worktree has of its own, so install it there:**

- `.venv`: **never share one.** `make install` records the folder it ran in, so a shared `.venv`
  would run another worktree's code (checked: after `make install`, `backend` imports from the
  worktree itself).
- `data/app.db` (untracked, so each worktree has its own database).
- `tests/visual/node_modules`: `cd tests/visual && npm install --ignore-scripts && npx playwright install chromium`.

**Still shared, so do not overlap:**

- **Ports.** `make run` uses 8000 and the visual check uses 8777. Two sessions cannot run the same
  one at once. Start a second app with `--port <other>`; run the visual check one session at a time.
- The git history and config (hooks, `core.hooksPath`) are shared on purpose. Hooks run in every
  worktree.
- Never run `git stash` to compare things. Stash is shared across worktrees; make a worktree or a
  commit instead.

**Finish:** push the branch and open the pull request as usual, then from the main folder:
`git worktree remove ../capstone-worktrees/<persona>` (refuses if there are uncommitted changes,
which is the point) and `git branch -d <branch>` after the merge. `git worktree list` shows what
exists.

Note: Claude Code keys its project memory to the folder, so a session in a worktree starts with the
repo's `CLAUDE.md` but not your auto-memory for the main folder.

## What is not done in this block

- No backend, frontend, agent or CI code, and no dependency installs (B2 onward). *This describes
  B1 as first done on 2026-11-13. `@backend.eng` has since built B2 to B4, B7, B13a and the CI
  workflow (H-057); this section is not rewritten, and the sections above record the current state.*
- No `README.md` created or changed in B1. (Later: `@backend.eng` wrote the run instructions, PR
  #107, and `@project.mgr` brought the status parts up to date, H-058.)
- No diagram was needed.

## Hand-off: what is next for each downstream agent

*Refreshed 2026-11-19 (H-060). Merged on `main`: B1 with CI, B2, B3 stand-in steps 1 to 6 and 7a,
B13a, B4, B7, B12, and **the first green path** (H-056). B5's status is being aligned between
`backend.md` and `frontend.md` (H-059). Order from here, per the Build card: operator pins DL-40 →
B3 step 7b and the spike → B8 → B9 → B13b → B6 → B10. Drop order: B6 and Tier 2, then B12, then
B13b; never T-MAP-1. The live list of open requests is `project-context/handoffs.md`.*

| Agent | Next |
|---|---|
| Operator | **Pin DL-40 / SOQ-25** (model IDs in `.env`, never committed, and in `decision-log.md`). Nothing that costs money runs before it. Then say when B3 step 7b (installing CrewAI) and the spike start. Approve the 16 proposed visual snapshots (H-053, H-054, H-055). Re-check the B1 + B2 timing after B7 |
| `@backend.eng` | H-059 (B5 status in `backend.md`) and H-061 (close H-036). After the DL-40 pin: **B3 step 7b** (install CrewAI, build the crews behind the same agent functions), then the spike with timings (they replace the starting limits in `.env.example`). Later: **B13b** Retry if time allows |
| `@frontend.eng` | **Waiting for the operator:** the 16 proposed snapshots (H-055, H-053; candidates in `tests/visual/candidates/`, git-ignored). H-027 and H-048 are done. Later: **B6** light visual pass (dropped first). Moves its finished entries to Done (H-061) |
| `@qa.eng` | Review `tests/tier1/test_green_path.py` (co-owned, H-056). Then **B8** the evaluation runner, with `T-MAP-1` passing before the first evaluation run; **B9** tuning and one evaluation cycle with the operator. Writes `2.build/qa.md` in **B10**, which ends the temporary validator exception (H-002) |
| `@ux.designer` | Nothing blocking. Answers questions from `ux.md` and reviews the pages again after B6 |
| `@system.arch` | Nothing blocking. Records Build-week decisions in `sad.md` and `decision-log.md` when a handoff asks. Checks the drop order if the clock forces a drop |
| `@project.mgr` | This table and the README stay current as blocks merge. When `qa.md` exists, remove the temporary `qa.md` exception in `scripts/git-hooks/run-checks.sh` and `.github/workflows/ci.yml` together (H-002) |
| `@security.eng`, `@devops.eng`, `@integration.eng` | **B10** only (acceptance pass, security checklist, rehearsal, final run instructions). The README run instructions already exist (PR #107). Nothing before the green path and the evaluation cycle |

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
  *Update 2026-11-18:* the stage limits were renamed to `STAGE_TIME_LIMIT_A`, `_B`, `_C` in B3
  step 6 (operator kept the rename); the rest still waits.
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
- 2026-11-16 · persona `project-mgr` · action `setup-project` · `AAMAD_TARGET_RUNTIME=crewai` ·
  `run-checks.sh` check 1 now also blocks a staged `.venv`, and a file or symlink named exactly
  `reference` or `.venv`. Found when a worktree used symlinks to run the hooks; nothing was
  committed. Pattern tested against nine sample paths. Wrote `scaffold-plan.md` (plan only) and
  handoff H-033. After PR #58 (DL-54) merged: added `STAND_IN_UNIT_PAUSE_S` to the environment
  table.
- 2026-11-16 · persona `backend-eng` · `sync-docs` (operator-approved) · `AAMAD_TARGET_RUNTIME=crewai`
  · recorded the app shell's pinned dependencies under "CrewAI settings" and corrected where
  `STAND_IN_UNIT_PAUSE_S` was added to `.env.example`. Nothing else changed.
- 2026-11-17 · persona `project-mgr` · action `document-setup` (handoff H-041 follow-up, operator
  instruction) · "Timing guardrails" Order line brought in step with `sad.md`: B13a after B3, B12
  after B5, B13b after B9, plus the drop order. `AAMAD_TARGET_RUNTIME=crewai`. No code. No model call.
- 2026-11-18 · persona `backend-eng` · `sync-docs` (operator-approved) · after B3 step 6: the stage
  limit variables are `STAGE_TIME_LIMIT_A`, `_B`, `_C` (env table and the Open Point on names). The
  operator kept the rename. No other change.
- 2026-11-19 · persona `project-mgr` · action `document-setup` (handoffs H-056, H-057; H-003 closed) ·
  `AAMAD_TARGET_RUNTIME=crewai` · recorded the first green path pass and the cleared day-4 tripwire
  in "Timing guardrails"; added the CI subsection and the `--no-verify` rule under "Git hooks"; the
  "Tests and checks" table now says where each check runs; marked the B1 "not done" list as
  B1-as-first-done. No code. No model call.
- 2026-11-19 · persona `project-mgr` · `sync-docs` (handoff H-058, operator request) · `README.md`
  status note, persona status table and "What happens next" brought up to the Build state. No code.
  No model call.
- 2026-11-19 · persona `project-mgr` · action `document-setup` (handoff H-060) ·
  `AAMAD_TARGET_RUNTIME=crewai` · "Hand-off" table rewritten for the Build state after the first
  green path. The old Netlify-banner line was dropped: the banner's state was not checked. No code.
  No model call.
- 2026-11-19 · persona `project-mgr` · action `document-setup` (handoff H-061) · "Hand-off" table
  updated: `@frontend.eng` row now shows the snapshots waiting for the operator, with H-027 and
  H-048 done; `@backend.eng` row mentions H-061. No code. No model call.
