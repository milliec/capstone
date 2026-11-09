# User Stories — Index

MVP stories derived from `prd.md` (features F1–F9) and `system-description.md`. One story per file.
US-001 to US-013 and US-015 are **Must** priority. **US-014 is a stretch goal (Could)**, built only after the Must
stories pass. It depends on US-005 and is not part of the Week 6 definition of done. P1 features from the PRD are listed at the end but **not written**
(MVP only).

## Story map (follows the happy path in PRD §2)

| Step | Story | Title | Persona | PRD feature | SD requirements |
|---|---|---|---|---|---|
| 1–2 | [US-001](US-001-extract-obligation-rows.md) | Extract source-linked obligation rows | Specialist | F1 | FR-001, FR-002 |
| 3 | [US-002](US-002-verify-quotes.md) | Verify quotes | Specialist | F2 | FR-003 |
| 3 | [US-003](US-003-check-source-conflicts.md) | Check conflicts (internal and between sources) | Specialist | F2 | FR-004 |
| 4 | [US-004](US-004-approve-rules-g1.md) | Approve or reject rules (G1) | Specialist | F3 | FR-005, FR-023 |
| 4 | [US-005](US-005-edit-rule-and-reverify.md) | Edit a rule and re-verify it | Specialist | F3 | FR-006, FR-007 |
| 5 | [US-006](US-006-judge-applicability.md) | Judge applicability for the fund | Specialist | F4 | FR-008, FR-009 |
| 6 | [US-007](US-007-approve-verdicts-g2.md) | Confirm or override verdicts (G2) | Specialist | F5 | FR-010, FR-024 |
| 7 | [US-008](US-008-generate-scheduled-calendar.md) | Generate calendar dates for scheduled obligations | Specialist | F6 | FR-011, FR-012, FR-016 |
| 7 | [US-009](US-009-event-triggered-entry.md) | Generate a calendar entry from a logged event | Specialist | F6 | FR-013 |
| 8 | [US-010](US-010-publish-calendar-g3.md) | Publish the calendar (G3) | Specialist | F7 | FR-014, FR-022 |
| 9 | [US-011](US-011-gp-read-only-calendar.md) | View the published calendar as a GP | GP | F8 | FR-015, FR-025 |
| all | [US-012](US-012-audit-log.md) | Record every output and decision | Specialist | F9 | FR-017 |
| all | [US-013](US-013-evaluation-report.md) | Compare a run with the answer key | Specialist | F9 | FR-018 |
| 1–7 | [US-015](US-015-follow-run-and-recover.md) | Follow a run and recover from a failed step | Specialist | §6 | NFR-004 (no FR; PRD §6 decision) |
| after 9 | [US-014](US-014-assess-amendment-impact.md) | **Stretch (Could):** assess the impact of a rule amendment | Specialist | F10 | FR-021, FR-026 |

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
| FR-022 | US-010 | FR-024 | US-007 |
| FR-023 | US-004, US-005 | FR-025 | US-011 (also linked from US-004, US-010, US-014) |

**Not written (P1, after MVP):** FR-019 full trail view.

**FR-020** ("not legal advice" and unverified date-conventions note) became a Must on 2026-11-09 and is
covered by US-011 (criterion 11).

**Stretch (Could):** FR-021 and FR-026 are covered by US-014.

**Interaction rule (PRD §6, Must):** no bulk or preselected approval decisions. Tested in US-004
(criteria 12–13), US-007 (10–11), US-010 (10) and, for the stretch, US-014 (15).

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
| AC-021 | US-010 | AC-023 | US-007 |
| AC-022 | US-004, US-005 | AC-024 | US-011 |
| AC-026 | US-004, US-007, US-010 (stretch: US-014) | | |

Stretch: AC-018, AC-019, AC-020 and AC-025 are covered by US-014.

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
| PRD §5 | Evidence, examples and personas use only the fictional firm and public regulation; no employer documents cited or summarised | `@security.eng` |
| PRD §6 | Voice: plain British English, facts and uncertainty without reassurance or alarm, sources cited, no advice; checked in a copy review before the demo | `@ux.designer` |

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

- See each story. Shared ones: four-eyes timing (PRD OQ-1), GP "under review" note before first
  publication (PRD OQ-6).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories` · 13 Must stories, index and coverage check
- 2026-11-06 · persona `product-mgr` · action `update` · `OBL-04` demo decision changed to "applies,
  pending confirmation" (P-1); calendar 18 → 22 entries across stories
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · AC coverage table; constraints covered
  outside stories; Spain note renamed "precautionary"; US-003 retitled
- 2026-11-06 · persona `product-mgr` · action `create-stories` · added US-014 (stretch, Could)
- 2026-11-07 · persona `product-mgr` · action `update` · story map and coverage updated for FR-022 to
  FR-026 and the PRD §6 interaction rule (approval-map decisions)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · AC coverage table
  adds SD AC-021 to AC-024 and stretch AC-025
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · AC coverage table
  adds SD AC-026 (explicit decisions)
- 2026-11-09 · persona `product-mgr` · action `update` · stories brought up to date with the UX and
  business reviews of the PRD: new US-015 (run status and failed-step re-run, Must); criteria added to
  US-002, US-003, US-007, US-010, US-011, US-013; FR-020 now Must (US-011); two system-wide rules
  (no employer documents, voice). See `../decision-log.md` DL-01 to DL-12
