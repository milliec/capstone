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
deleted now that CrewAI is installed cleanly. `@backend.eng` installed CrewAI into this `.venv` in
B3 step 7b, PR 1 (2026-11-19), pinned as `crewai==1.15.35` (see "CrewAI settings" below).

## CrewAI settings (D1 to D6)

Recorded as given by the operator. The per-item D-numbers are not mapped here because the SAD uses
them for other things too (for example D4 for the trace export); confirm the mapping with the
architect before anyone cites a single D-number.

- Three crews, **one agent and one task each** (extractor, verifier, judge). No multi-agent crew, no
  Flow.
- Each task returns a typed result through a **strict `response_format`** (the step's JSON schema),
  checked by our own code against the Pydantic schemas; `output_pydantic` is not used (SAD §2,
  H-065).
- **No tools** on any agent.
- **No memory.**
- **No delegation** (`allow_delegation` off).
- **`guardrail_max_retries: 0`.** No re-ask of a bad answer. The only retry is DL-43's one: after a
  timeout, no connection, a 429 or a 5xx, our code tries once more (1 s later); a second failure
  becomes `model service`. A 400, 401 or 404 is never retried. Because CrewAI can repeat a call
  itself, one unit can send up to four HTTP requests (at most two billed), each with its own trace
  line (SAD §4, H-073).

The app shell (`@backend.eng`, 2026-11-16) installed the web stack, pinned in `pyproject.toml`:
fastapi 0.163.1, uvicorn 0.54.0, jinja2 3.1.6, python-multipart 0.0.34, itsdangerous 2.2.0,
pyyaml 6.0.3; for tests, pytest 9.2.0 and httpx 0.28.1. **CrewAI 1.15.35** was added in B3 step 7b,
PR 1 (2026-11-19). It needs `pydantic<2.13`, so pydantic is 2.12.5 (was 2.14.3). It is loaded only
in real mode, through `backend/runtime/crewai_setup.py`, which first forces four switches off:
`CREWAI_DISABLE_TELEMETRY=true`, `OTEL_SDK_DISABLED=true`, `CREWAI_TRACING_ENABLED=false` (CrewAI's
own tracing) and `CREWAI_DISABLE_VERSION_CHECK=true`. Stand-in mode never loads it (T-MODE-1). Steps 2 to 5 of 7b (2026-11-21 and 2026-11-22) added no package. PR 4 added one
pytest setting in `pyproject.toml` that hides CrewAI's own deprecation warnings. Real mode has run
against a fake OpenAI in the tests, never against the real one.

## Environment variables

`.env.example` is committed with placeholders only. Copy it to `.env` (git-ignored) to run locally.

| Variable | Default | Purpose |
|---|---|---|
| `AAMAD_TARGET_RUNTIME` | `crewai` | Framework runtime target |
| `AGENTS_MODE` | `stand_in` | `stand_in` = fixed outputs, no model call, no cost. **Keep `stand_in` in `.env`.** `real` is for the spike command only: give it on the command line, together with `SPEND_ACTIVITY=spike` (see "Run the spike's first real call" and "Run the verifier and judge calls"), so `make run` can never go real |
| `OPENAI_API_KEY` | placeholder | Only read when mode is not `stand_in`. Never commit a real key |
| `OPENAI_BASE_URL` | not set | **A shell variable, not a `.env` setting.** The OpenAI client reads it only from the shell, never from `.env`. If it is set it changes where a real call goes; the spike prints an `Endpoint` line so you can see it. Leave it unset |
| `RUN_COST_CAP_USD` | `2.50` | Hard stop per run |
| `SPEND_ACTIVITY` | empty | Which of the five paid activities (spike, tuning, evaluation, rehearsal, demo). The spike command needs `spike`; give it on the command line, not in `.env` |
| `CALL_TIMEOUT_EXTRACT` / `CALL_TIMEOUT_VERIFY` / `CALL_TIMEOUT_JUDGE` | 90 / 60 / 60 | Each call's own timeout, in seconds (SAD §4). The HTTP client timeout is **not a variable**: the code sets it to the call timeout minus 5 seconds (DL-43) |
| `LLM_MODEL_EXTRACT` / `LLM_MODEL_VERIFY` / `LLM_MODEL_JUDGE` | empty | The model ID for each role (DL-40). **Only in your own `.env`, never committed.** Empty in stand-in mode; a real call for a role with no ID is refused. **The spike's three steps each need their own ID:** `--step extract` reads `LLM_MODEL_EXTRACT`, `--step verify` reads `LLM_MODEL_VERIFY`, `--step judge` reads `LLM_MODEL_JUDGE` (see "Run the verifier and judge calls") |
| `LLM_MAX_TOKENS_EXTRACT` / `LLM_MAX_TOKENS_VERIFY` / `LLM_MAX_TOKENS_JUDGE` | 2000 / 2000 / 4000 | Output limit of one call, in tokens (a reasoning model's hidden thinking counts inside it). A test checks these keep a whole run under `RUN_COST_CAP_USD` |
| `STAGE_TIME_LIMIT_A` / `_B` / `_C` | 375 / 150 / 30 | Stage limits, on the backend's timer, not `max_execution_time` |
| `STAND_IN_UNIT_PAUSE_S` | `1` | Seconds each stand-in agent function waits per unit, so units finish one by one. Read **only** when `AGENTS_MODE=stand_in`; never in real mode; `0` in tests (sad.md §4, DL-54, T-PAUSE-1). Added to `.env.example` by `@backend.eng` in the app shell (2026-11-16), with the code that reads it |

**Open points to confirm against `sad.md` §4** (this block was told to read only the Implementation
Guidance section, so these were not checked):

- The exact variable name for `SPEND_ACTIVITY`. The name above is chosen here. (The timeout names now match SAD §4: H-071.)
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
| `aamad validate` (every error blocks, as in the hook) | Yes |

- **H-003 item 1 (validator in CI): built.** The one finding `project-context/2.build/qa.md: Build
  artifact missing` used to be ignored in `ci.yml` and in `run-checks.sh`. `@qa.eng` wrote `qa.md`, and
  both exceptions were removed in the B8 slice 1 pull request (#142, H-002, H-067).
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
| Framework validator | `.venv/bin/aamad validate` | The commit and push hooks, and **CI** (every validator error blocks) |
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

### Grade a finished run (B8 slices 1 and 2, H-070)

B8 has two slices so far, both merged: the **Stage A grader** (#142) and the **Stage B grader**
(#151). Both only **read a finished run from the database** (`DATABASE_PATH`, the app's own file).
They start nothing, call no model, need no key and spend nothing, so they work with
`AGENTS_MODE=stand_in`. The code is in `backend/evaluation/`; the design notes and the tests are in
`2.build/qa.md`.

```bash
.venv/bin/python -m backend.evaluation RUN-20261121-1            # Stage A, and Stage B if the run finished it
.venv/bin/python -m backend.evaluation RUN-20261121-1 --stage b  # Stage B only (also --stage a)
.venv/bin/python -m backend.evaluation RUN-20261121-1 --no-save  # print the report, save nothing
```

`RUN-20261121-1` is an example. The run ID is in the review page's address (`/specialist/runs/<run ID>`). `--out <folder>` changes
where reports are saved.

| What happens | Detail |
|---|---|
| Which stages | The default (`--stage all`) grades Stage A, then Stage B **if the run finished Stage B**. At G1 it prints "Stage B skipped" and still grades Stage A. With `--stage b` the same case stops with exit code 2 |
| Stage B is "finished" | When all its units are done, which the app only records when every unit is done (rule 9). A run that stopped earlier, or a run made before the app stored Stage A's output, has nothing to grade: the command says "Nothing to grade", exit code 2 |
| Exit code | **0 for any report, even with misses**: an evaluation reports, it never blocks (DL-34). 2 only when there is nothing to grade (no database, unknown run, not finished) |
| Saved files | `project-context/2.build/logs/<run ID>/stage-<a or b>-report-<n>.json` and `.md`. Grading the same run again writes report 2, never an edit of report 1. **This folder is not git-ignored**: check `git status` before you commit, and use `--no-save` when you only want to look |
| Does the run count? | A stand-in run is stamped "STAND-IN RUN: does not count towards the cycle": it checks the graders, it is not an evaluation of the agents. A real run counts only if it is labelled `evaluation` (`SPEND_ACTIVITY`) and the planted-row switch was off (EC-R6, EC-R7). The stamp only marks; it refuses nothing. The run starter that makes such runs is not built yet |

**What the Stage B report shows** (the Stage A criteria are in the Stage A report):

| ID | What it checks | Passes when | On a stand-in run |
|---|---|---|---|
| EC-004 | The six applicability verdicts against the answer key (KEY section 2) | 6 of 6: OBL-01, 02, 03 and 05 "applies", OBL-04 "unsure", OBL-06 "does not apply"; every verdict cites at least one existing fact ID; OBL-04 cites FACT-03 and FACT-04; OBL-05 cites FACT-06 and EVT-01 | Graded as normal. The stand-in's verdicts equal the key's, so it shows 6 of 6 |
| EC-010 | Agent time, from the trace: every model step, retries included, not the time waiting for the specialist | **Strictly under 5 minutes** (exactly 300 s is a miss) | `NOT TESTED`: a stand-in call takes milliseconds, so a pass would say nothing. The measured seconds are still printed |
| EC-012 | Model cost, from the trace (provider usage data, retries included) | **Strictly under US$2** (exactly US$2.00 is a miss), **and** the trace adds up to the run's own cost count | `INCOMPLETE`: the "trace adds up" check passes, the "under US$2" check is `NOT TESTED` because the cost is US$0. The measured cost is still printed |

Reading the results:

- **A verdict that is not graded.** A row the specialist did not approve at G1 is **not tested**
  (Stage B never judged it), which is not a miss. A key row that was never extracted is a miss. A
  missing verdict for an approved row is a miss. The reasoning text of a verdict is never graded.
- **A confident error is named.** If the key says "unsure" and the agent said "applies", the finding
  says so: that is the worst kind of EC-004 miss.
- **Information-only notes (EC-004).** On OBL-01, 02, 03 and 06 the SAD does not name the facts to
  cite, so the pass mark is only "at least one existing fact ID". If a verdict does not cite the
  facts the key lists for its row, the report adds a line under "Notes (information only, not a
  miss)", for example "OBL-02 …: the key's facts not cited: FACT-02". A note **never changes the
  result and never fails the run** (operator decision, 2026-11-21).
- **Late-call labels (EC-010 and EC-012).** A late call is one still running when the stage's time
  limit stopped the stage: its output is thrown away (rule 9), but it ran and was paid for and a
  user waited for it, so it **stays in** both the time and the cost. When there are any, the report adds a label to the result, in this form: "of this, LATE
  calls: N calls, X s, US$Y (counted: a user waits for them)". Calls on copy cases are also counted
  and named ("17 calls (1 late, 2 copy-case)").
- **One run is not a pass.** A criterion passes the cycle only on 3 of 3 consecutive runs of one
  commit (EC-R1). Every report says so.

**Still to do in B8, after the B3 spike:** the run starter (the evaluation-run type, scripted gates
and the EC-R7 refusal), the trace export (D4), the void rule (EC-R8), the `I-1` and injection cases
(they need the agents), grading a failed run, and the three-run comparison. Until a real model run
has been timed and priced, EC-010 and EC-012 are tested only on made-up traces, and EC-004 only on
the stand-in's verdicts.

### Run the spike's first real call (operator)

*Source: `2.build/backend.md`, section "B3 spike runner" (the exact steps and the table of outcomes
are there). Added for H-075.*

**Status (updated 2026-11-23, H-080).** The runner for the first extractor call is built and merged
(#164, #166) and was tested against the fake OpenAI first. **The operator has since made real calls**
(see "Run the verifier and judge calls" for the count). You run each real call from your own terminal and
send the printout back to `@backend.eng`. The extractor step sends one request for one document
(`SRC-UCILAW`). The worst case is about US$0.0012 for one request and US$0.0024 with the retry (a quarter
of a cent); the dry-run prints the number for your run.

**Before you start**

- `.env` holds the real `OPENAI_API_KEY` and `LLM_MODEL_EXTRACT` (the DL-40 extractor ID). Neither is ever
  committed.
- **Leave `AGENTS_MODE=stand_in` in `.env`.** The command below gives `real` on the command line, so
  `make run` can never go real by accident.

**Steps**

1. **Dry-run first.** It sends nothing:

   ```bash
   AGENTS_MODE=real SPEND_ACTIVITY=spike .venv/bin/python -m backend.runtime.spike
   ```

   Read the plan: the model, the settings it would send, the input size, the worst case and
   `Spike calls (0 of 70)`. Accept the cost before you go on.
2. **Go.** Run the same command with `--go` at the end.
3. **Check the `Endpoint` line.** It must say **`OpenAI's default (api.openai.com)`**. If it says
   anything else (a proxy, or `127.0.0.1`), **do not type the ID**: press Enter to cancel and look at
   `env | grep OPENAI`. The line reads only the shell's `OPENAI_BASE_URL`, not `.env`.
4. **Type `SRC-UCILAW` and press Enter.** That is the one thing that sends a request. Anything else
   (a wrong word, an empty line) means "not confirmed": nothing is sent.
5. **Read the result and send it back.** The printout never contains the key. The full answer stays in
   `data/spike.db`.

| Exit code | Meaning |
|---|---|
| 0 | The call was made and the answer was usable |
| 1 | The call was made (and billed) but the answer was not usable |
| 2 | Nothing was sent (a refusal, or not confirmed) |

**"Unable to initialize LLM" means CrewAI does not recognise the model ID in `LLM_MODEL_EXTRACT` as an
OpenAI model.** (Its fallback, LiteLLM, is deliberately not installed.) It appears as a Python traceback,
not as `REFUSED:`. It is raised while the model client is built, before any request exists, so **nothing
was sent and nothing was billed**, and the dry-run cannot see it. Check the ID in `.env` against DL-40
for a typo or a space. If it is exact, **stop and tell `@backend.eng`. Never run `pip install litellm`**: a
new dependency is a SAD edit first.

**Do not delete `data/spike.db` to start over.** It also resets the count of 70 spike calls, and EC-R10
says a further call needs a recorded operator decision.

**Not built yet:** the spike report (`@qa.eng`, B8). `backend.md` also lists what else you may see
instead of a result.

### Run the verifier and judge calls, the verifier bake-off, and the tally (operator)

*Source: `2.build/backend.md`, subsection "How to run the verifier and judge calls" and section "B3 spike:
the verifier bake-off (DL-26): how to run it, and the tally" (the exact words and tables are there).
Added for H-080.*

**Status (2026-11-23).** The spike runner now has **three steps**, each one real call per command, each
with a typed confirmation. All three are built and merged and were tested against the fake OpenAI first.
`--case` (the verifier bake-off's four cases) and `--tally` (a read-only summary) are merged too (#174,
#175); they are **built and ready, and not needed for the capstone**. **You have made real calls with all
three steps** (extractor 2, verifier 2, judge 1): **6 of 70 call slots used, US$0.0164**. **The verifier
bake-off (DL-26) is dropped (DL-55, operator, 2026-11-23): it was not run and is not owed.** The verifier
stays `gpt-5.6-terra`, and the "five runs each" for the extractor and the judge are skipped too. The
numbers are a snapshot: `--tally` prints the live ones.

| Step | Command ends with | You type exactly | `.env` needs |
|---|---|---|---|
| Extractor (the first call, above) | (nothing) | the document ID: `SRC-UCILAW` | `LLM_MODEL_EXTRACT` |
| Verifier | `--step verify` | `verify SRC-UCILAW-P3` | `LLM_MODEL_VERIFY` |
| Judge | `--step judge` | `judge SRC-UCILAW-P3` | `LLM_MODEL_JUDGE` |

The three model IDs are the DL-40 ones. They live only in your own `.env` and are never committed.
`AGENTS_MODE=real` goes on the command line, **not** in `.env`: keep `AGENTS_MODE=stand_in` there.

**How to run a step: the same way as the first call.**

1. **Dry-run first** (sends nothing). For the verifier, then the same with `--step judge` for the judge:

   ```bash
   AGENTS_MODE=real SPEND_ACTIVITY=spike .venv/bin/python -m backend.runtime.spike --step verify
   ```

   Read the model, the settings, the worst case and `Spike calls`.
2. **Go**: the same command with `--go` at the end.
3. **Check the `Endpoint` line.** It must say **`OpenAI's default (api.openai.com)`**. Anything else: do not
   type, press Enter to cancel.
4. **Type the exact words from the table.** The other step's words do not confirm a call, and neither does
   the bare row ID. Nothing is sent unless the words match exactly.
5. **Read the result and send the printout to `@backend.eng`.**

**What each step measures.** Both run on one fixed input, the answer-key row `SRC-UCILAW-P3` (where the
planted conflict C-1 sits), so every run sees the same row.

| | Verifier | Judge |
|---|---|---|
| Settings sent | `reasoning_effort` low, 2000 tokens, no temperature | `reasoning_effort` medium, 4000 tokens, no temperature |
| The result says | **CAUGHT** or **MISSED** for C-1; any other flag is a **false alarm** | **CORRECT** or **WRONG** against the answer key |

**A MISSED or WRONG verdict is a finding, not a failure.** A miss by the verifier points at DL-26; send it.

**Stop rule (operator, 2026-11-22).** After **any 400**, **`Off pinned setting : YES`**, **`Stop reason :
length`** or an **invalid answer**, **stop and send the printout**. Make no further call until you decide.
A 400 costs nothing. `Stop reason : length` is the reasoning models' own risk: their hidden thinking counts
against the token limit.

**Do not delete `data/spike.db`.** All steps share one spike run in it, each request is one trace line and
takes one of the 70 slots, and deleting it resets the count (EC-R10).

**The verifier bake-off (`--case`): built, ready, not needed for the capstone.** DL-26 asked whether the
mid-tier verifier model catches every planted conflict. **DL-55 (operator, 2026-11-23) dropped it: it is
not run and not owed, and DL-26 is closed.** The verifier stays `gpt-5.6-terra`. **Do not run the commands
below as a next step.** They stay documented in case a later operator decision brings the bake-off back
(that needs a new entry in the decision log). The first test of `C-2` and `I-1` on the verifier is the
evaluation cycle. The bake-off would run four cases, each on a fixed row: `C-1`, `C-2`, `I-1` (a copy of a
row with its offset changed, so the quote check alone would pass it) and `OK-1` (a correct row that should
get no flag).

```bash
AGENTS_MODE=real SPEND_ACTIVITY=spike .venv/bin/python -m backend.runtime.spike --step verify --case C-2 --go
```

- The typed words now name the case **and the model**, for example `verify C-2 gpt-5.6-terra`. The bare row
  ID, another case's words, or the wrong model all cancel.
- **Candidate 2** is the same command with `LLM_MODEL_VERIFY=gpt-6.1-terra` in front. If you forget it, the
  dry-run shows the model actually in use and the words you type will not match: nothing is sent.
- **If it were ever run** (it would need a new decision): candidate 1 first, then stop and review the
  tally, then candidate 2, about 41 of the 70 slots. `backend.md` has the slot arithmetic, the cost
  estimate and the pass and fail rules.
- **Paste one command at a time.** Each stops at a prompt and reads what you type.
- Five runs could say "no miss in five runs", never that a miss cannot happen. That is one of the known
  limits DL-55 states.

**The tally (read-only, no key needed).**

```bash
.venv/bin/python -m backend.runtime.spike --tally --exclude 'SRC-UCILAW-P3#1'
```

It reads `data/spike.db` and prints, per model and case: the calls, how many passed the schema check on
the first try, CAUGHT or MISSED, false alarms, tokens, time and cost, and how many more valid runs are
still needed. It sends nothing, needs no key and no real mode, opens the file read-only and never creates
it. `--exclude` leaves out the verifier call sent before the two-flag-shapes fix (`SRC-UCILAW-P3#1`).

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

*Refreshed 2026-11-19 (H-060, H-061, and again after H-059, H-062 to H-065); snapshot rows updated 2026-11-20 (H-055 closed, all 16 recorded); `@qa.eng` row updated 2026-11-21 (H-070); `@backend.eng` and Operator rows and the status note updated 2026-11-22 (H-074), and again 2026-11-22 (H-075: the spike runner is built); `@backend.eng` and Operator rows and the status note updated 2026-11-23 (H-080: the verifier and judge steps, `--case`, `--tally`). Merged on `main`: B1 with
CI, B2, B3 stand-in steps 1 to 6 and 7a, B13a, B4, B5, B7, B12, and **the first green path** (H-056).
**DL-40 is pinned** (H-064) and the four CrewAI settings changes are recorded in `sad.md` (H-065).
**Sprint 3 is treated as done at the stand-in bar** (operator, 2026-11-19).
**B3 step 7b is built: PRs 1 to 5 are merged** (#127, #153, #154, #155, #158; the SAD side of PR 5 is
H-073, #159) and PR 6, the documentation (#160), is merged too. Real mode builds one one-agent crew
per unit with DL-43's one retry, but it is **tested only against a fake OpenAI: no real key, no paid
call, and real mode must not be run before the operator's spike.** **The spike runner is built and merged for all three steps** (extractor #164, #166; verifier and judge; `--case` #174; `--tally` #175), tested against the fake OpenAI first. **The operator has made real calls with all three steps (6 of 70 slots, US$0.0164, as of 2026-11-23); the verifier bake-off (DL-26) is dropped by DL-55: not run and not owed.** Steps: "Run the spike's first real call" and "Run the verifier and judge calls". **The spike is under way; B8 and B9 follow** (week of 2026-11-23). Order from there, per the
Build card: the spike → B8 → B9 → B13b → B6 → B10. Drop order: B6 and Tier 2, then
B12, then B13b; never T-MAP-1. The live list of open requests is `project-context/handoffs.md`.*

| Agent | Next |
|---|---|
| Operator | **No bake-off to run: DL-55 (2026-11-23) dropped the verifier bake-off (DL-26), and the verifier stays `gpt-5.6-terra`.** `--case` and `--tally` stay built as optional future work; the steps are under "Run the verifier and judge calls, the verifier bake-off, and the tally" in "Tests and checks". Anything you run from there needs a typed confirmation: type the words with the model ID, and **stop and send the printout after any 400, `Off pinned setting : YES`, `Stop reason : length` or invalid answer.** `.env` must hold the real key and the three pinned model IDs (`LLM_MODEL_EXTRACT`, `_VERIFY`, `_JUDGE`; never committed), with `AGENTS_MODE=stand_in` left in place; do not delete `data/spike.db`. **After the spike, decide whether a call off the pinned reasoning setting counts as a failure** (SAD Production Shape, "Decisions to take once the spike has shown the result); so far all three models have accepted their pinned settings (H-079), so it may not arise. Snapshots: all 16 are approved and recorded and the visual check passes (H-055; four review-status baselines were refreshed on 2026-11-20 for the "unit" wording change, #140). Re-check the B1 + B2 timing now that B7 is done |
| `@backend.eng` | **B3 step 7b** is built, PRs 1 to 5 merged (#127, #153, #154, #155, #158) plus the PR 6 docs (#160): CrewAI 1.15.35 installed with its outside connections off; real mode sends one one-agent crew per unit, with DL-43's one retry (a timeout, no connection, a 429 or a 5xx; never a 400, 401 or 404; never a bad answer), **one trace line per HTTP request** (up to four per unit, at most two billed), four new `trace` columns, and a flag when CrewAI repeats a call without `reasoning_effort`. All tested against the fake OpenAI only: no real key, no paid call. **The spike runner is built for all three steps** (`python -m backend.runtime.spike`: extractor #164, #166; `--step verify`, `--step judge`; `--case` #174; read-only `--tally` #175; a dry-run and a `--go` with a typed confirmation, its own `data/spike.db`; tested against the fake OpenAI first). The operator has made real calls with all three (6 of 70 slots, US$0.0164, 2026-11-23). The verifier bake-off and the "five runs each" are dropped (DL-55); the stage limits stay at their starting values as the operator's decision. The next steps are not yet merged; a later handoff will carry them. Later: **B13b** Retry if time allows. H-059 and H-061 (H-036 part) are done |
| `@frontend.eng` | Nothing open on snapshots: the mobile fix (H-062) and the 360 px baselines are done. H-061: move your finished entries (H-048, H-027) to Done (H-054 is already there). Later: **B6** light visual pass (dropped first) |
| `@qa.eng` | **B8** has two slices built and merged, both reading a finished run from the database with no model call: the Stage A grader (#142) and the Stage B grader (#151: EC-004 applicability verdicts, EC-010 agent time and EC-012 cost, from the trace). How to run them and what they report: "Grade a finished run" under "Tests and checks"; the details are in `2.build/qa.md`. Still to do, after the spike: the run starter (evaluation-run type, scripted gates, EC-R7 refusal), the trace export (D4), the void rule (EC-R8), the `I-1` and injection cases, grading a failed run, and the three-run comparison, and the spike and evaluation reports that show `off_pinned_setting` and estimated cost (the `trace` columns exist since 7b PR 5; nothing reads them yet). `T-MAP-1` must pass before the first evaluation run. **B9** tuning and one evaluation cycle with the operator |
| `@ux.designer` | **H-063** (open): say whether specialist pages at 360 px are a requirement or a courtesy, and the sign-in order when narrow. Otherwise answers questions from `ux.md` and reviews the pages again after B6 |
| `@system.arch` | Nothing blocking: H-064 and H-065 are done. H-061 (H-040) still needs the entry moved to Done. Records Build-week decisions in `sad.md` and `decision-log.md` when a handoff asks. Checks the drop order if the clock forces a drop |
| `@project.mgr` | This table and the README stay current as blocks merge (the README status note was last aligned in H-067). The temporary `qa.md` exception is gone from `scripts/git-hooks/run-checks.sh` and `.github/workflows/ci.yml` (H-002, H-067); nothing left to remove |
| `@security.eng`, `@devops.eng`, `@integration.eng` | **B10** only (acceptance pass, security checklist, rehearsal, final run instructions). The README run instructions already exist (PR #107). Nothing before the evaluation cycle |

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
  *Update 2026-11-22 (H-071):* `CALL_TIMEOUT_EXTRACT`, `_VERIFY`, `_JUDGE`, `LLM_MODEL_*` and
  `LLM_MAX_TOKENS_*` are now in `.env.example` and in the table above, and the code reads them; the
  `HTTP_TIMEOUT_*` variables are gone (the HTTP timeout is set in code). `SESSION_SECRET` and
  `DATABASE_PATH` were not checked here.
- **Resolved (H-002).** Does the validator's hard requirement for `qa.md` once `2.build/` has
  content stay, or should the hook treat it differently? Decision: the hook ignores only the one
  finding `project-context/2.build/qa.md: Build artifact missing`. Every other validator error still
  blocks. The exception was temporary. `@qa.eng` wrote `project-context/2.build/qa.md`, and the
  exception was removed from `scripts/git-hooks/run-checks.sh` and `.github/workflows/ci.yml` in the
  B8 slice 1 pull request (#142). Every validator error now blocks.

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
- 2026-11-19 · persona `project-mgr` · action `document-setup` (operator request) ·
  `AAMAD_TARGET_RUNTIME=crewai` · "Hand-off" table refreshed: DL-40 pinned (H-064), H-065 done,
  H-059 done, snapshots 15 of 16 approved, H-063 open for `@ux.designer`; Sprint 3 treated as done at
  the stand-in bar and the rest of step 7b (after PR 1), the spike, B8 and B9 start next week. No code. No model call.
- 2026-11-19 · persona `backend-eng` · `sync-docs` (operator-approved) · `AAMAD_TARGET_RUNTIME=crewai`
  · B3 step 7b PR 1: CrewAI 1.15.35 recorded as installed (Virtualenv note and "CrewAI settings"),
  pydantic 2.12.5 and the four forced switches noted; `output_pydantic` replaced by the strict
  `response_format` (H-065). No code. No model call.
- 2026-11-20 · persona `project-mgr` · action `document-setup` (operator request) ·
  `AAMAD_TARGET_RUNTIME=crewai` · "Hand-off" table: snapshot rows brought in step with H-055 (all 16
  recorded, visual check passes, four more refreshed in #140); `@frontend.eng` row no longer waits on
  the 360 px baseline. Checked `main` and `handoffs.md` first: no open PRs, 7b PRs 2 to 6 not started.
  No code. No model call.
- 2026-11-21 · persona `project-mgr` · action `document-setup` (handoff H-067) ·
  `AAMAD_TARGET_RUNTIME=crewai` · the temporary `qa.md` validator exception is described as removed
  (CI row, H-003 note, "Tests and checks" row, Resolved H-002, `@qa.eng` and `@project.mgr` rows);
  `@qa.eng` row says B8 slice 1 is built (#142). README status row for `@qa.eng` aligned. Verified in
  `run-checks.sh` and `ci.yml` that the exception is gone. No code. No model call.
- 2026-11-21 · persona `project-mgr` · action `document-setup` (handoff H-070) ·
  `AAMAD_TARGET_RUNTIME=crewai` · new subsection "Grade a finished run" under "Tests and checks"
  (the command, its options, exit codes, where reports are saved, what EC-004, EC-010 and EC-012
  report, the information-only notes and the late-call labels); `@qa.eng` Hand-off row now names both
  B8 slices (#142, #151). Checked against `backend/evaluation/` and the rendered report; the
  command was run read-only against `data/app.db`: every run there answers "Nothing to grade" (Stage A
  has not stored its output), so the report text was checked on a throwaway test run instead. No code. No model call. No real key. No paid call.
- 2026-11-22 · persona `project-mgr` · action `document-setup` (handoff H-074) ·
  `AAMAD_TARGET_RUNTIME=crewai` · "Hand-off" status note and the Operator, `@backend.eng` and
  `@qa.eng` rows now say 7b PRs 1 to 6 are merged (#127, #153, #154, #155, #158, #160) and real mode
  is tested against the fake OpenAI only; new Operator item: after the spike, decide whether a call
  off the pinned reasoning setting is a failure. "CrewAI settings": the retry bullet now describes
  DL-43's one retry and the four-request bound; the install note says PRs 2 to 5 added no package.
  Checked against `backend.md` (PR 5 section and "Known gaps"), `handoffs.md` and `git log`
  (`pyproject.toml` history). README status row and "What happens next" aligned. No code. No model
  call. No real key. No paid call.
- 2026-11-22 · persona `project-mgr` · action `document-setup` (handoff H-071) ·
  `AAMAD_TARGET_RUNTIME=crewai` · environment-variable table: the three timeout rows renamed to the
  SAD §4 names, the `HTTP_TIMEOUT_*` row removed (set in code, DL-43), rows added for `LLM_MODEL_*`
  and `LLM_MAX_TOKENS_*`; "Open points" and the Open Question about variable names updated. Checked
  against `.env.example` (lines 31 to 46) and `handoffs.md`. No code. No model call. No real key. No paid call.
- 2026-11-22 · persona `project-mgr` · action `document-setup` (handoff H-075) ·
  `AAMAD_TARGET_RUNTIME=crewai` · new subsection "Run the spike's first real call" under "Tests and
  checks" (dry-run, `--go`, the Endpoint check, typing `SRC-UCILAW`, exit codes 0, 1 and 2, the "Unable to
  initialize LLM" case, do not delete `data/spike.db`); environment table: `AGENTS_MODE` and
  `SPEND_ACTIVITY` notes, new `OPENAI_BASE_URL` row (a shell variable); Hand-off status note, Operator
  and `@backend.eng` rows. Copied from `backend.md` "B3 spike runner" and checked against
  `backend/runtime/spike.py` (Endpoint wording, `--go`, exit codes, `data/spike.db`). The command was
  not run. No code. No model call. No real key. No paid call.
- 2026-11-23 · persona `project-mgr` · action `document-setup` (handoff H-080) ·
  `AAMAD_TARGET_RUNTIME=crewai` · new subsection "Run the verifier and judge calls, the verifier
  bake-off, and the tally" under "Tests and checks" (the three steps and their typed words, the dry-run
  then `--go`, the Endpoint check, `LLM_MODEL_VERIFY` and `LLM_MODEL_JUDGE` in `.env`, the stop rule,
  CAUGHT/MISSED and CORRECT/WRONG as findings, do not delete `data/spike.db`, `--case` with the model ID
  in the typed words and the staging, the read-only `--tally` with `--exclude`); the first-call
  subsection's status and its "Not built yet" paragraph brought to the present; environment table notes
  for `AGENTS_MODE` and `LLM_MODEL_*`; Hand-off status note, Operator and `@backend.eng` rows. Copied
  from `backend.md` and checked against `backend/runtime/spike.py` (`--step`, `--case`, `--tally`,
  `--exclude`, the typed words) and `python -m backend.runtime.spike --help`; `--tally` was run read-only
  (6 of 70 slots, US$0.0164, matching `backend.md`). No real call was made. No code. No model call. No
  real key. No paid call.
- 2026-11-23 · persona `project-mgr` · action `document-setup` (handoff H-082) ·
  `AAMAD_TARGET_RUNTIME=crewai` · wording only: the verifier bake-off (DL-26) is dropped by DL-55, not run
  and not owed, and "five runs each" are skipped; `--case` and `--tally` stay documented as built, ready,
  not needed. Changed the subsection's status line and the bake-off paragraph, the Hand-off status note, and
  the Operator and `@backend.eng` rows (the Operator row no longer says to run the bake-off). Does not say
  what comes next, as asked: the next steps are not yet merged. Source: `backend.md` and DL-55. No code. No
  model call. No real key. No paid call.
