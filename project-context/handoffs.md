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

(none yet)

## Done

(none yet)
