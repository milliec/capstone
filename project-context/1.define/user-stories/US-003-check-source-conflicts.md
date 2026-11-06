# US-003 — Check conflicts (internal and between sources)

## 1. Story Identity

- **ID**: US-003
- **Title**: Check conflicts between sources
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want each rule checked against its own quote and against every other
source, so that disagreements are found by a check and not by chance.

## 3. Acceptance Criteria

1. **Given** the 6 rows and all mock sources, primary and secondary, **when** verification runs,
   **then** conflict `C-1` is flagged on `OBL-03`, citing `SRC-UCILAW-P3` (six months) and
   `SRC-PRACT-P1` (four months), with both quotes.
2. **Then** conflict `C-2` is flagged on `OBL-05`, citing `SRC-RBELAW-P1` (becoming aware) and
   `SRC-PRACT-P2` (date of the change), with both quotes.
3. **Then** no conflict is flagged on `OBL-01`, where `SRC-PRACT-P3` agrees with `SRC-CSSF15627-P2`.
4. **Given** the 6 correct rows, **then** exactly 2 cross-source flags and 0 internal flags are raised.
5. **Internal check:** **given** `OBL-02` with its offset changed to "+30 calendar days" and its quote
   left as "within 20 calendar days following the end of each calendar quarter", **when** verification
   runs, **then** an internal conflict is flagged (test `I-1`), even though the quote check passes.
6. **Then** each internal flag names the field that disagrees, its value, and what the quote says.
7. **Then** the check does not change any row and does not choose which source is right.
8. **Then** every flag is recorded in the audit log.

## 4. Scope Notes

- **In Scope for MVP**: disagreements in deadline, anchor and offset, both between a row and its own
  quote (internal) and between mock sources (cross-source).
- **Deferred**: ranking sources automatically, or detecting conflicts across frameworks.

## 5. Traceability

- **PRD Anchors**: F2 · §2 step 3 · UN-S3 · AB-3
- **System description**: FR-004 · MD-003 · MN-004 · AC-003, AC-017 · MP-003
- **Answer key**: §3
- **Related SFS**: none yet

## Sources

- `prd.md` F2 · `system-description.md` AC-003 · `mock-data/expected-obligation-library.md` §3

## Assumptions

- A flag must show both sides: each paragraph ID and its quote, so the specialist can decide without
  opening the source files.

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added the internal check (fields vs own
  quote) and test `I-1`
