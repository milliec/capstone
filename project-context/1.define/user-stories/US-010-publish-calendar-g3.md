# US-010 — Publish the calendar (Gate G3)

## 1. Story Identity

- **ID**: US-010
- **Title**: Publish the calendar (G3)
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to review the whole calendar and publish it only when I am satisfied,
so that GPs never see unfinished work.

## 3. Acceptance Criteria

1. **Given** a generated calendar, **when** the specialist opens G3, **then** they see all 22 entries,
   with roll notes, the "roll rule unconfirmed" mark on the 2027-02-28 entries for `OBL-04` and `OBL-05`,
   and the "precautionary: registration unconfirmed" note on `OBL-04`.
2. **Given** G1 or G2 is not complete, **when** the specialist tries to publish, **then** publishing is
   refused.
3. **Given** any entry is marked out of date (see US-005), **then** publishing is refused.
4. **Given** entries marked "roll rule unconfirmed" or "precautionary", **then** they do **not** block
   publishing. They are safe defaults (design principle P-1).
5. **When** the specialist publishes, **then** the whole fund calendar is published at once.
6. **Given** the calendar has not been published, **then** the GP view shows no entries for the fund.
7. **Then** every publish, and every refused attempt, is recorded in the audit log with who and when.

## 4. Scope Notes

- **In Scope for MVP**: one specialist publishes one fund's calendar.
- **Deferred**: four-eyes review, scheduled publishing, publishing single entries.

## 5. Traceability

- **PRD Anchors**: F7 · §2 step 8 · UN-S4, UN-G4 · AB-5
- **System description**: FR-014 · MD-004 · MN-003, MN-007 · AC-013 · MP-006 · A-6
- **Related SFS**: none yet

## Sources

- `prd.md` F7 · `system-description.md` MD-004, AC-013, A-6

## Assumptions

- Once a calendar is published, GPs keep seeing that version until the specialist publishes again.
  Operator-confirmed.

## Open Questions

- **OQ-US010-1**: Four-eyes review: in the MVP or later? (PRD OQ-1)
- **OQ-US010-2**: *Resolved.* After a post-publish edit, GPs keep seeing the last published version
  until the specialist publishes again (operator-confirmed).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 18 → 22 entries
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added criterion 4 (safe-default marks do
  not block publishing); Spain note renamed
