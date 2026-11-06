# US-013 — Compare a run with the answer key

## 1. Story Identity

- **ID**: US-013
- **Title**: Compare a run with the answer key
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want each run compared automatically with the expected results, so that I
can prove the system works and see exactly where it doesn't.

## 3. Acceptance Criteria

1. **Given** a completed run, **when** the evaluation runs, **then** it reports:
   - extraction: rows found out of 6, extra rows, quotes that are not word for word;
   - applicability: verdicts correct out of 6;
   - verification: `C-1` and `C-2` caught, no false flag on `OBL-01`, altered quote caught, wrong
     field with a correct quote caught (`I-1`);
   - calendar: entries correct out of 22, exact dates.
2. **Then** every mismatch is listed with the expected value and the actual value.
3. **Then** the report records run time and model cost against the targets: under 5 minutes and under
   US$2. It also records specialist review time, taken from audit-log timestamps (Gate 1 opened →
   Gate 3 published), against the target of under 30 minutes.
4. **Then** the altered-quote case and the `I-1` case are tested by changing **a copy** of the row
   (one word of `OBL-01`'s quote; `OBL-02`'s offset), never by editing the mock sources.
5. **Then** each report is saved with its run ID and is not overwritten by later runs.

## 4. Scope Notes

- **In Scope for MVP**: evaluation against the answer key for the mock data set.
- **Deferred**: evaluations on new data sets; trend tracking across runs.

## 5. Traceability

- **PRD Anchors**: F9 · §7 technical metrics
- **System description**: FR-018 · MP-001 to MP-004 · MC-001, MC-002, MC-003
- **Answer key**: §1 to §4
- **Related SFS**: none yet

## Sources

- `prd.md` F9, §7 · `system-description.md` MP-001 to MP-004, MC-001, MC-002 ·
  `mock-data/expected-obligation-library.md`

## Assumptions

- Review time is measured from the audit log, so a stranger can score it from the report without
  watching the demo (operator decision).

## Open Questions

- **OQ-US013-1**: How close must an extracted obligation name be to pass? (Shared with OQ-US001-1.)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · calendar out of 22
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added internal-conflict test `I-1`
- 2026-11-06 · persona `product-mgr` · action `update` · review time reported from audit-log timestamps
