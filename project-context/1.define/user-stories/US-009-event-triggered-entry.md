# US-009 — Generate a calendar entry from a logged event

## 1. Story Identity

- **ID**: US-009
- **Title**: Generate a calendar entry from a logged event
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want event-triggered obligations dated from the day the fund became aware
of the event, so that the deadline follows what the law actually says.

## 3. Acceptance Criteria

1. **Given** `OBL-05` is approved and applies, and `EVT-01` is in the mock event log (changed 2027-01-20,
   aware 2027-01-31), **when** the calendar is generated, **then** one `OBL-05` entry is produced, due
   2027-02-28.
2. **Then** the date is **not** 2027-02-20, which is what using the event date would give.
3. **Given** `OBL-05`'s business-day rule is "not confirmed", **then** the date stays Sunday 2027-02-28
   and is marked "roll rule unconfirmed" for the specialist.
4. **Then** the entry references `EVT-01`.
5. **Given** no event is logged for `OBL-05`, **then** no `OBL-05` entry is produced.
6. **Then** no language model is used. These tests run without one.

## 4. Scope Notes

- **In Scope for MVP**: events read from the mock fund profile's event log.
- **Deferred**: logging new events in the interface.

## 5. Traceability

- **PRD Anchors**: F6 · §2 step 7 · UN-S6
- **System description**: FR-013 · MD-007 · MN-005 · NFR-011 · AC-011, AC-012
- **Answer key**: §4, `D-3`, `D-6`
- **Related SFS**: none yet

## Sources

- `prd.md` F6 · `system-description.md` MD-007, AC-011, AC-012 · `mock-data/mock-fund-profile.md`
  (event log)

## Assumptions

- The MVP reads events only from the mock event log. No story covers adding events through the
  interface.

## Open Questions

- **OQ-US009-1**: Business-day rule for Luxembourg Business Registers filings. (PRD OQ-7)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
