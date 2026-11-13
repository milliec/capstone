# Handoffs between personas

A message board for change requests that cross persona boundaries, so nobody pastes text between chats.
Decisions live in the owner's file. This file only carries the request.

## Who owns what

| File | Owner |
|---|---|
| `1.define/prd.md`, `mrd.md`, `system-description.md`, `user-stories/`, `context-summary.md` | `@product-mgr` |
| `1.define/sad.md`, `sfs/` | `@system.arch` |
| `1.define/ux.md`, `1.define/prototypes/`, `2.build/ux-review.md` | `@ux.designer` |
| `2.build/setup.md` | `@project.mgr` |

Add a row when a new persona starts producing a file. Never edit a file you don't own: raise a handoff.

## How it works

1. Add an entry at the **top** of "Open". Address it **To** the file's owner, or **To: operator** for a
   decision only the operator can make.
2. The owner makes the change in their own file, then moves the entry to "Done" and fills in "Outcome".
3. Refer to IDs (F-xx, DL-xx, SOQ-xx, EC-xx). Never copy the text of a decision.

## Entry template

```
### H-NNN: short title
- From: @persona   To: @persona or operator   Date: YYYY-MM-DD
- Touches: file and IDs (for example, sad.md DL-40)
- Ask: one or two sentences. What should change?
- Why: one sentence.
- Outcome: (the owner fills this in: what changed, or why not)
```

## Open

### H-003: Add `aamad validate` to CI, and make `--no-verify` a stop-and-report
- From: @system.arch (operator request)   To: @project.mgr   Date: 2026-11-13
- Touches: setup.md (Git hooks section, and the "no CI code" line in the B1 scope), `.github/workflows/` (new), `requirements-dev.txt` (new, already created by @system.arch at the operator's request), `scripts/git-hooks/run-checks.sh`
- Ask: (1) Add a CI job that runs `aamad validate` only, as a backup for commits made with `--no-verify`. CI installs the validator with `pip install -r requirements-dev.txt`, which pins `aamad==1.0.1` (the version in the operator's local `.venv`); keep that pin in step with the local one and mention the file in setup.md. It must carry the same temporary qa.md exception as the hook until H-002 removes both together. (2) Keep the real-name scan local only: CI must not run it, and `reference/real-identifiers.txt` must never be uploaded, copied into a CI secret, or committed. (3) Record in setup.md the same rule that is now in the root `CLAUDE.md` (added by @system.arch with the operator's approval): any `--no-verify` commit by an agent is a stop-and-report to the operator, not something to fix quietly. Do not edit `CLAUDE.md` again for this.
- Why: Hooks are per clone and can be skipped; CI is the shared backstop, but the identifier list is itself sensitive, so that one check stays on the operator's machine.
- Outcome: (the owner fills this in)

### H-002: Remove the qa.md exception from run-checks.sh when qa.md is written
- From: @system.arch (operator request)   To: @project.mgr   Date: 2026-11-13
- Touches: `scripts/git-hooks/run-checks.sh` (the TEMPORARY qa.md exception in check 3), setup.md open question on qa.md
- Ask: Remove the qa.md exception from run-checks.sh when `@qa.eng` writes `2.build/qa.md`. If H-003's CI job is in place by then, remove the same exception there in the same change.
- Why: The exception was only meant to last until `qa.md` exists; left in place it would hide a real "qa.md missing" error.
- Outcome: (the owner fills this in)

## Done

### H-001: Confirm which copy of the build order is authoritative
- From: @project.mgr   To: @system.arch   Date: 2026-11-13
- Touches: sad.md, Build card "Order" row and the "Order of work" table
- Ask: Say which of the two is authoritative, and add a one-line note under the other that points to it. Do not change the order itself.
- Why: Both list the build sequence, so they can drift apart, and Build personas work from the Build card.
- Outcome: The Build card "Order" row is authoritative. Added an "Authority (H-001)" note under the "Order of work" table pointing to it. Also added a pointer under the "Build order" paragraph in the Estimate section (a third copy of the sequence, in prose), which the handoff did not ask for; the operator approved it. The order itself is unchanged.
