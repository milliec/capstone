# User Stories — Index

MVP stories derived from `prd.md` (features F1–F9) and `system-description.md`. One story per file.
All stories are **Must** priority. P1 features from the PRD are listed at the end but **not written**
(MVP only).

## Story map (follows the happy path in PRD §2)

| Step | Story | Title | Persona | PRD feature | SD requirements |
|---|---|---|---|---|---|
| 1–2 | [US-001](US-001-extract-obligation-rows.md) | Extract source-linked obligation rows | Specialist | F1 | FR-001, FR-002 |
| 3 | [US-002](US-002-verify-quotes.md) | Verify quotes | Specialist | F2 | FR-003 |
| 3 | [US-003](US-003-check-source-conflicts.md) | Check conflicts (internal and between sources) | Specialist | F2 | FR-004 |
| 4 | [US-004](US-004-approve-rules-g1.md) | Approve or reject rules (G1) | Specialist | F3 | FR-005 |
| 4 | [US-005](US-005-edit-rule-and-reverify.md) | Edit a rule and re-verify it | Specialist | F3 | FR-006, FR-007 |
| 5 | [US-006](US-006-judge-applicability.md) | Judge applicability for the fund | Specialist | F4 | FR-008, FR-009 |
| 6 | [US-007](US-007-approve-verdicts-g2.md) | Confirm or override verdicts (G2) | Specialist | F5 | FR-010 |
| 7 | [US-008](US-008-generate-scheduled-calendar.md) | Generate calendar dates for scheduled obligations | Specialist | F6 | FR-011, FR-012, FR-016 |
| 7 | [US-009](US-009-event-triggered-entry.md) | Generate a calendar entry from a logged event | Specialist | F6 | FR-013 |
| 8 | [US-010](US-010-publish-calendar-g3.md) | Publish the calendar (G3) | Specialist | F7 | FR-014 |
| 9 | [US-011](US-011-gp-read-only-calendar.md) | View the published calendar as a GP | GP | F8 | FR-015 |
| all | [US-012](US-012-audit-log.md) | Record every output and decision | Specialist | F9 | FR-017 |
| all | [US-013](US-013-evaluation-report.md) | Compare a run with the answer key | Specialist | F9 | FR-018 |

## Coverage check

Every Must requirement in `system-description.md` §4 is covered by at least one story:

| SD FR | Story | SD FR | Story |
|---|---|---|---|
| FR-001 | US-001 | FR-010 | US-007 |
| FR-002 | US-001 | FR-011 | US-008 |
| FR-003 | US-002 | FR-012 | US-008 |
| FR-004 | US-003 | FR-013 | US-009 |
| FR-005 | US-004 | FR-014 | US-010 |
| FR-006 | US-005 | FR-015 | US-011 |
| FR-007 | US-005 | FR-016 | US-008 |
| FR-008 | US-006 | FR-017 | US-012 |
| FR-009 | US-006 | FR-018 | US-013 |

**Not written (P1, after MVP):** FR-019 full trail view, FR-020 "not legal advice" note.

### Acceptance criteria coverage

Every acceptance criterion in `system-description.md` §8 is tested by at least one story:

| SD AC | Story | SD AC | Story |
|---|---|---|---|
| AC-001, AC-002 | US-001 | AC-010 | US-008 |
| AC-003 | US-003 | AC-011 | US-009, US-008 |
| AC-004 | US-002 | AC-012 | US-009 |
| AC-005 | US-005 | AC-013 | US-010, US-011 |
| AC-006 | US-004, US-005 | AC-014 | US-011 |
| AC-007 | US-006 | AC-015 | US-008 |
| AC-008 | US-007 | AC-016 | US-012 |
| AC-009 | US-008 | AC-017 | US-003, US-005 |

### Constraints covered outside the stories

These rules apply to the whole system, not to one user action, so no story owns them. QA and security
must still check them.

| Rule | What to check | Likely owner |
|---|---|---|
| SD MN-001 | No real names in committed files (scan against the private list in `reference/`) | `@security.eng` |
| SD MN-002 | No live calls to email, regulator portals or task tools | `@security.eng`, `@qa.eng` |
| SD MN-008 | No task tool used as the system of record | `@system.arch` |
| SD NFR-009 | No secrets in the repository | `@security.eng` |
| SD NFR-011 | Gate, date and audit tests run without a language model | `@qa.eng` |
| PRD §5 | Run time under 5 minutes, cost under US$2 (measured in US-013) | `@qa.eng` |

## Demo decisions the stories assume

The answer key expects a calendar of **22 entries**. That number depends on how the specialist decides
at each gate. The stories assume these demo decisions:

| Gate | Row | Specialist decision | Why |
|---|---|---|---|
| G1 | `OBL-03` | Approve with reason, keeping "6 months" | Primary source (`SRC-UCILAW-P3`) wins over the secondary summary (conflict `C-1`). |
| G1 | `OBL-05` | Approve with reason, keeping "becoming aware" | Primary source (`SRC-RBELAW-P1`) wins (conflict `C-2`). |
| G1 | All six rows | Business-day rules as in answer key §5 | Operator guidance (`D-5`). |
| G2 | `OBL-04` (unsure) | Resolve as **applies (precautionary: registration unconfirmed)**, reason: "Treated as applicable until CNMV registration is confirmed" | Design principle **P-1** (`system-description.md` §2): an extra entry is harmless, a missed filing is not. Adds 4 entries. |
| G2 | Other five | Confirm the agent's verdict | Matches answer key §2. |

## Sources

- `project-context/1.define/prd.md` (F1–F9, §2 happy path)
- `project-context/1.define/system-description.md` (FR, AC, MN, NFR)
- `project-context/1.define/mock-data/expected-obligation-library.md` (expected values)

## Assumptions

- The demo decisions above stand in for a real specialist's judgement. They are chosen so the expected
  results are fixed and testable.

## Open Questions

- See each story. Shared ones: four-eyes timing (PRD OQ-1), GP "under review" note (PRD OQ-6).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories` · 13 Must stories, index and coverage check
- 2026-11-06 · persona `product-mgr` · action `update` · `OBL-04` demo decision changed to "applies,
  pending confirmation" (P-1); calendar 18 → 22 entries across stories
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · AC coverage table; constraints covered
  outside stories; Spain note renamed "precautionary"; US-003 retitled
