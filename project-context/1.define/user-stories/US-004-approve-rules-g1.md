# US-004 — Approve or reject rules (Gate G1)

## 1. Story Identity

- **ID**: US-004
- **Title**: Approve or reject rules (G1)
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to approve or reject each verified rule and set its business-day
rule, so that only rules I trust enter the obligation library.

## 3. Acceptance Criteria

1. **Given** verified rows, **when** the specialist opens G1, **then** each row shows its fields,
   paragraph ID, quote, quote-check result and any conflict flags.
2. **When** the specialist approves a row, **then** they set its business-day rule (roll forward / no
   roll / not confirmed) and the row becomes **approved**.
3. **When** the specialist rejects a row, **then** a written reason is required, and the row is marked
   **rejected** and is never sent to applicability.
4. **Given** a row that failed the quote check, **then** it cannot be approved.
5. **Given** `OBL-03` with conflict `C-1`, **when** the specialist approves it without a reason, **then**
   approval is refused. **With** a reason, it is approved and the reason is recorded.
6. **Given** any row still undecided, **then** G1 is not complete and applicability (US-006) does not
   start.
7. **Then** every approval, rejection, reason and business-day rule is recorded in the audit log with
   who and when.
8. **Given** the demo decisions in the story index, **then** all 6 rows end G1 approved, with business-day
   rules as in answer key §5.

## 4. Scope Notes

- **In Scope for MVP**: one specialist; one decision per row.
- **Deferred**: four-eyes review (a second specialist confirms), pending decision on timing.

## 5. Traceability

- **PRD Anchors**: F3 · §2 step 4 · UN-S4, UN-S7 · AB-1, AB-4
- **System description**: FR-005 · MD-004 · MN-003, MN-006 · AC-006 · NFR-010
- **Answer key**: §5 (business-day rules)
- **Related SFS**: none yet

## Sources

- `prd.md` F3 · `system-description.md` MD-004, AC-006 · `user-stories/README.md` (demo decisions)

## Assumptions

- G1 is complete only when **every** row is approved or rejected. Applicability then runs on all
  approved rows together. Operator-confirmed.

## Open Questions

- **OQ-US004-1**: Four-eyes review: in the MVP or later? (PRD OQ-1)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
