# Project rules for Claude Code

Framework instructions (AAMAD personas and workflow) are in `AGENTS.md`. This file adds rules specific
to this project.

## Scope & Guard Rules (Build Week)

Full version: `project-context/2.build/setup.md`. Source: the Build card in `sad.md`.

- Build only from the Build card and Never row in `sad.md`. If something is missing, **stop and ask**.
  Never use the `sad-full-design` tag, Appendix A (F-18, S1 to S4, `DEPLOY_MODE`, CSRF) or parked F-IDs.
- Keep `AGENTS_MODE=stand_in`. No DL-40 / SOQ-25 pin and no real model call (including the B3 spike)
  until the full stand-in happy path passes end to end (start, Stage A, G1 with the demo row refused
  then rejected, Stage B, G2, Stage C, G3 ack, GP view and audit log).
- Tier 1 tests block merges (including EC-015, EC-019, T-MODE-1). If Tier 2 is dropped, T-MAP-1 must
  still pass before the first evaluation run.
- A new tool, memory, retry or re-ask is a SAD edit first.
- Netlify hosts `docs/architecture-decisions-summary.html` (public context page). It is **frozen**
  with the banner "Snapshot as of 12 Nov — see sad.md for Build-week deltas" until after the demo.
  Edit it only for a huge DL change.

## Public repository: binding rules

This repository is **public**. Anything committed should be treated as published forever.

- Never commit real company, fund, platform, service-provider or people names, internal document dates,
  version numbers, or other internal details.
- Real source material lives only in `reference/`, which git ignores. Never copy from it into committed
  files. Create anonymised mock data instead (see `project-context/1.define/mock-data/`).
- The repo is a git repository with a GitHub remote (`origin`). Before every commit and push, confirm
  `reference/` and `.env` do not appear in `git status`, and run the real-name scan below.
- Start new work on a branch, never on `main`. Changes reach `main` only through a reviewed pull
  request. If edits were started on `main` by mistake, move them with `git switch -c <branch>` before
  committing.

## Checks to run after changing committed files

1. **Real-name scan** (must print nothing):

   ```bash
   grep -rniwF --exclude-dir=reference --exclude-dir=.venv --exclude-dir=.git \
     -f <(grep -vE '^(#|$)' reference/real-identifiers.txt) .
   ```

2. **Framework validator**: `.venv/bin/aamad validate`

## Working with the operator

- Personal learning-mode preferences live in the operator's global `~/.claude/CLAUDE.md`.
- When a session produces a learning note (a lesson worth keeping), add it to `docs/learning-notes.md`
  under the right theme, as well as saying it in chat.
