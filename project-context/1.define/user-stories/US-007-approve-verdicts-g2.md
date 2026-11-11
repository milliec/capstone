# US-007 — Confirm or override verdicts (Gate G2)

## 1. Story Identity

- **ID**: US-007
- **Title**: Confirm or override verdicts (G2)
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to confirm or override each applicability verdict and decide every
unclear case myself, so that no obligation is wrongly hidden from, or added to, the fund's calendar.

## 3. Acceptance Criteria

1. **Given** verdicts from US-006, **when** the specialist opens G2, **then** each verdict shows its
   reasoning and the fund facts it cites. Each cited fact ID can be opened to show what the fact says.
   Facts are read-only at G2. (PRD F5)
2. **When** the specialist confirms a verdict, **then** it becomes **approved** as it is.
3. **When** the specialist overrides a verdict, **then** a written reason is required, and the new
   verdict and reason are recorded.
4. **Given** any verdict is still **unsure**, **then** G2 cannot be completed.
5. **Given** the demo decisions in the story index, **when** the specialist resolves `OBL-04` as
   **applies (precautionary)** with the reason "Treated as applicable until CNMV registration is
   confirmed" and confirms the other five, **then** G2 is complete.
6. **Given** a verdict resolved as precautionary, **then** it is recorded as **applies** with the note
   "precautionary: registration unconfirmed", so the calendar includes it and the note stays visible
   (design principle P-1). The word "pending" is not used, because "pending" means *not yet approved*.
7. **Then** every confirmation and override is recorded in the audit log with who and when.
8. **Given** a confirmed or overridden verdict, before or after publication, **when** the specialist
   reopens it without a reason, **then** reopening is refused. **With** a reason, the verdict returns to
   **pending** G2 and the rule stays G1-approved. The original decision and reasoning stay in the audit
   log, and the applicability agent does not run again.
9. **Given** a reopened verdict, **then** its calendar entries are marked out of date, and publishing a
   new version is refused until G2 is complete and the dates are regenerated. The specialist must
   finish with **applies** or **does not apply**, and an override still needs a reason. GPs keep seeing
   the last published version until the specialist republishes.
10. **Given** the G2 review screen, **then** there is no "confirm all" or other bulk decision, and no
    verdict has a preselected confirm or override decision. Each decision is a separate, explicit
    action, recorded on its own in the audit log with its own timestamp.
11. **Given** undecided verdicts, **when** the specialist closes the screen, the session times out, or
    nothing is done, **then** those verdicts stay **pending** and G2 is not complete. Verdicts already
    decided keep their recorded decisions.
12. **Given** a verdict has changed since the specialist's screen loaded (for example it was
    regenerated, or its row was edited and re-approved), **when** they submit a confirm, override or
    reopen decision made on the old version, **then** the decision is refused and not recorded, and a
    plain message says the item changed and shows its current version. **Given** the same decision is
    submitted twice (for example a double click), **then** one decision is recorded and the second
    request is refused with the same message. The message follows the voice rule in PRD §6.
    (SAD CR-009.)

## 4. Scope Notes

- **In Scope for MVP**: one specialist; one decision per verdict.
- **Deferred**: four-eyes review, pending decision on timing.

## 5. Traceability

- **PRD Anchors**: F5 · §2 step 6 · UN-S4, UN-S5, UN-S7 · AB-4
- **System description**: FR-010, FR-024 · MD-004 · MD-009 · AC-008
- **SAD controls**: CR-009 (criterion 12)
- **Related SFS**: none yet

## Sources

- `prd.md` F5 · `system-description.md` MD-004, AC-008 · `user-stories/README.md` (demo decisions)

## Assumptions

- An override can turn any verdict into any other verdict, except "unsure", which only the agent can
  give. Operator-confirmed.
- When resolving "unsure", the specialist follows design principle P-1 (`system-description.md` §2):
  choose the option whose mistake is cheaper.

## Open Questions

- **OQ-US007-1**: Four-eyes review: in the MVP or later? (PRD OQ-1)
- **OQ-US007-2**: *Resolved* (operator decision, 2026-11-07). Yes, with a reason, before or after
  publication. See criteria 8 and 9, SD FR-024. *(Approval map OD-3.)*

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · `OBL-04` demo decision changed to applies (P-1)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · note renamed to "precautionary:
  registration unconfirmed"
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-US007-2 (approval map
  OD-3); no criterion changed
- 2026-11-07 · persona `product-mgr` · action `update` · reopen a confirmed verdict (new scope decision,
  SD FR-024): criteria 8 and 9 added; OQ-US007-2 resolved
- 2026-11-07 · persona `product-mgr` · action `update` · criteria 10 and 11 (no bulk or preselected
  decisions; silence leaves verdicts pending; PRD §6), operator decision
- 2026-11-09 · persona `product-mgr` · action `update` (UX review) · criterion 1: cited fund facts can be opened, read-only (PRD F5); decision log DL-04
- 2026-11-11 · persona `product-mgr` · action `update` (SAD CR-009) · criterion 12: a decision made on an
  out-of-date screen, or submitted twice, is refused with a plain message showing the current version
