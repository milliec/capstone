# User Stories — Index

MVP stories derived from `prd.md` (features F1–F9) and `system-description.md`. One story per file.
US-001 to US-013, US-015 and US-016 are **Must** priority. **US-014 is a stretch goal (Could)**, built only after the Must
stories pass. It depends on US-005 and is not part of the Week 6 definition of done. P1 features from the PRD are listed at the end but **not written**
(MVP only).

## Story map (follows the happy path in PRD §2)

| Step | Story | Title | Persona | PRD feature | SD requirements |
|---|---|---|---|---|---|
| 1–2 | [US-001](US-001-extract-obligation-rows.md) | Extract source-linked obligation rows | Specialist | F1 | FR-001, FR-002, FR-028 |
| 3 | [US-002](US-002-verify-quotes.md) | Verify quotes | Specialist | F2 | FR-003 |
| 3 | [US-003](US-003-check-source-conflicts.md) | Check conflicts (internal and between sources) | Specialist | F2 | FR-004 |
| 4 | [US-004](US-004-approve-rules-g1.md) | Approve or reject rules (G1) | Specialist | F3 | FR-005, FR-023, FR-029 |
| 4 | [US-005](US-005-edit-rule-and-reverify.md) | Edit a rule and re-verify it *(deferred, DL-22)* | Specialist | F3 | FR-006, FR-007 |
| 4 | [US-016](US-016-create-missed-rule-by-hand.md) | Add a missed rule by hand *(deferred, DL-22)* | Specialist | F3 (new scope, DL-15) | FR-027 |
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
| FR-027 | US-016 (separate count: US-013) | FR-029 | US-004 |
| FR-028 | US-001 (fix: US-016) | | |

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
| AC-026 | US-004, US-007, US-010 (stretch: US-014) | AC-027 | US-016, US-013 |
| AC-028 | US-004 | AC-029 | US-001 |
| AC-030 | US-015 (also US-001 c7, US-006 c7) | AC-031 | US-015, US-016, US-013 |
| AC-032 | US-010, US-004 (assumptions: US-011) | AC-033 | US-015 |
| AC-034 | US-015 | AC-035 | US-015 |
| AC-036 | US-015, US-010 | AC-037 | US-010 |
| AC-038 | US-004 (criterion 19) | | |

Stretch: AC-018, AC-019, AC-020 and AC-025 are covered by US-014.

### Scope status (DL-22)

The MVP is the thin slice (decision log DL-22). The items below are written down and designed, not
built; they are marked *Deferred (DL-22)* where they appear. Nothing was deleted.

| Where | Deferred |
|---|---|
| Whole stories | US-005 (edit and re-verify), US-016 (add a missed rule by hand) |
| US-001 | criterion 9; the reopening clause of criterion 10 |
| US-004 | criteria 9–11 (reopen a rejected row), 14–16 (possible duplicates, completion confirmation) |
| US-007 | criteria 8–9 (reopen a verdict) |
| US-010 | the next-step choices after a G3 decline (back to G1 or G2); criteria 8–9 are reworded: a decline ends the run as declined |
| US-011 | criteria 9–10 (GP review notice) |
| US-013 | criteria 8–9 (human-created rows, release counted) |
| US-015 | criteria 4–6, 11–13, 14–15, 18; the restart note. Criteria 19–21 (failed run, abandon) stay |
| System description | FR-007, FR-023, FR-024, FR-025, FR-027, FR-029; AC-005, AC-022 to AC-024, AC-027, AC-028, AC-031; the edit parts of FR-005 and FR-006; the re-run sentences of NFR-004 and AC-030 |

Still in the MVP: the coverage view (FR-028), G1 reject and approve over a flag with a reason, G2
override and "unsure", G3 decline with a reason, the evaluation report, and the run states (US-015
criteria 16, 19–21).

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
| G1 | All six rows | Business-day rules and "who files" settings as in answer key §5 | Operator guidance (`D-5`); "who files" is set only where the source is silent (DL-39). |
| G1 | The planted row marked "demo" *(demo run only: the run is started with the demo switch on)* | Reject with reason: "Planted demo row: the quote does not support this rule" | The demo shows the specialist catching a row whose quote is verbatim but does not support its rule, which the code quote check cannot catch (SD FR-031, DL-31). Approve is refused for a demo row. The verifier runs on the planted row like on every other row, and the demo script does not depend on whether it raises a flag (SAD SOQ-22). The row then appears in the G3 rejected list (US-010 criterion 14). The calendar stays at 22 entries. Evaluation runs have the switch off. |
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

- See each story. Shared ones: four-eyes review (future scope, PRD OQ-1, DL-37), GP "under review" note before first
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
- 2026-11-11 · persona `product-mgr` · action `create-stories` (SAD SOQ-8) · new US-016 (add a missed rule
  by hand, DL-15) with FR-027 and AC-027 in the coverage tables; US-013 criterion 8
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · US-004 criteria 14–16 (possible
  duplicates, DL-16) with FR-029 and AC-028 in the coverage tables
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · US-001 criteria 8–10 (G1 coverage
  view) with FR-028 and AC-029 in the coverage tables
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · only non-rejected rows count in the coverage view (US-001 c8, c10; operator decision) and the per-unit failure rule: US-015 criteria 9–13, clarifications in US-001 c7 and US-006 c7, NFR-004 amended, AC-030
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18) · US-015 criteria 14–15 (release of a failed source document to manual entry), US-016 criterion 11; AC-031 added to the coverage table
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · US-010 criterion 12 (OBL-02 open-question mark at G3) and a US-004 G1 note; SD OQ-4 and KEY OQ-D3 kept open
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18, DL-20) · US-004 criterion 17, US-010 criterion 12, US-013 criterion 9, US-011 assumption; AC-031 and AC-032 in the coverage table; PRD F3 line for released documents
- 2026-11-11 · persona `product-mgr` · action `update` (SAD CR-009, CR-023, CR-017) · new criteria for out-of-date and double-submitted decisions (US-004 c18, US-007 c12, US-010 c13) and for the active-run rule, cost-cap stop and service-outage message (US-015 c16–18); OQ-US015-4 raised
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-4, SOQ-11, §2, §4) · PRD OQ-8 and OQ-US016-1 resolved; US-008 and US-015 notes point to the SAD's entry-ID scheme and restart behaviour
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · future-scope stories and criteria marked deferred; new "Scope status (DL-22)" table; nothing deleted
- 2026-11-12 · persona `product-mgr` · action `update` (DL-23) · US-013 criteria 10–11 (3 of 3 consecutive runs on one commit; names graded by the specialist); OQ-US001-1 and OQ-US013-1 resolved
- 2026-11-12 · persona `product-mgr` · action `update` (DL-27) · US-011 criterion 7 and SD AC-013 name the GP "being prepared" message; PRD OQ-6, SD OQ-1 and OQ-US011-1 resolved
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · AC-033 to AC-036 in the coverage table; US-010 criteria 8–9 reworded (a decline ends the run as declined); OQ-US001-2 accepted as a known limitation
- 2026-11-12 · persona `product-mgr` · action `update` (DL-30, DL-31) · demo decision added: reject the planted demo row at G1 with a reason (demo run only); AC-037 and AC-038 in the coverage table (AC-038 backed by US-004 criterion 19); operator decisions
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-20 e, f, h) · demo decision for the planted row: the verifier runs on it and the demo does not depend on its flag (SOQ-22)
- 2026-11-12 · persona `product-mgr` · action `update` (DL-39, SAD SOQ-24 d) · G1 demo-decision row: "who files" settings added beside the business-day rules
