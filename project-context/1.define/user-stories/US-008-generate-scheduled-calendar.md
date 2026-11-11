# US-008 — Generate calendar dates for scheduled obligations

## 1. Story Identity

- **ID**: US-008
- **Title**: Generate calendar dates for scheduled obligations
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want due dates calculated by code from the approved rules, so that every
date is correct and comes out the same each time.

## 3. Acceptance Criteria

1. **Given** G2 is complete with the demo decisions, **when** the calendar is generated, **then** it has
   21 scheduled entries: 12 for `OBL-01`, 4 for `OBL-02`, 1 for `OBL-03` and 4 for `OBL-04`, with the
   dates in answer key §4.
2. **Given** `OBL-01` due Sunday 2027-01-10 with rule "roll forward", **then** its calendar date is
   Monday 2027-01-11, with the note "moved from Sun 10 Jan". The same applies to 2027-04-10, 2027-07-10
   and 2027-10-10.
3. **Given** `OBL-02` with rule "no roll", **then** its dates are not adjusted.
4. **Given** `OBL-03` (31 Dec 2026 + 6 months), **then** its date is 2027-06-30.
5. **Then** only due dates from 2027-01-01 to 2027-12-31 are included.
6. **Then** rows that are rejected, or whose verdict is not "applies", produce no entries.
7. **Then** every entry has a stable ID. Generating twice from the same inputs gives the same IDs and the
   same dates.
8. **Then** no language model is used. These tests run without one.
9. **Given** `OBL-04` (applies, precautionary), **then** its 4 entries are 2027-02-28 (a Sunday;
   the CNMV roll rule is not confirmed, so it is **not** rolled and is marked "roll rule unconfirmed"),
   2027-05-31, 2027-08-31 (end-of-month convention) and 2027-11-30.

## 4. Scope Notes

- **In Scope for MVP**: month-end, quarter-end and year-end anchors; conventions `D-1` to `D-7`; the mock
  2027 Luxembourg holiday list.
- **Deferred**: business-day offsets (e.g. "40 business days"), official holiday sources, other
  jurisdictions' holidays.

## 5. Traceability

- **PRD Anchors**: F6 · §2 step 7 · UN-S6 · AB-5
- **System description**: FR-011, FR-012, FR-016 · MD-006, MD-010 · MN-005 · NFR-001, NFR-011 · AC-009,
  AC-010, AC-015
- **Answer key**: §4, §5
- **Related SFS**: none yet

## Sources

- `prd.md` F6 · `system-description.md` MD-006, AC-009, AC-010, AC-015 ·
  `mock-data/expected-obligation-library.md` §4–§5

## Assumptions

- The same occurrence of an obligation must always get the same ID. The SAD sets the stable entry-ID
  scheme (§4): the ID is built from the fund, the source paragraph, the recipient authority, the
  position of the quote in the paragraph and the period, and is independent of the due date, so an
  edited offset moves the date but not the ID. Test T-ID-2 covers distinct IDs, the same IDs on
  regeneration, and a refused generation when two approved rows would give the same ID.

## Open Questions

- **OQ-US008-1**: *Part resolved.* CNMV (`OBL-04`): *resolved* (decision log DL-19). The rule stays
  "not confirmed" until the specialist sets one at G1, so weekend dates keep the earlier day and are
  marked (`D-6`). **Still open:** the business-day rule for the AED subscription tax (`OBL-02`). (PRD
  OQ-7, SD OQ-4; DL-20)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 17 → 21 scheduled entries (`OBL-04` included)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · removed the ID-building method (left to
  the SAD); Spain note renamed
- 2026-11-11 · persona `product-mgr` · action `update` (DL-19) · OQ-US008-1 part resolved (CNMV `OBL-04`); AED subscription-tax part stays open (DL-20); no criterion changed
- 2026-11-11 · persona `product-mgr` · action `update` (SAD §4) · assumption points to the SAD's stable entry-ID scheme and test T-ID-2; no criterion changed
