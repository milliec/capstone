# US-006 — Judge applicability for the fund

## 1. Story Identity

- **ID**: US-006
- **Title**: Judge applicability for the fund
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want the system to judge which approved rules apply to the fund and show
its reasoning, so that I confirm decisions instead of making each one from scratch.

## 3. Acceptance Criteria

1. **Given** G1 is complete and the mock fund profile for `FND-DEMO-01` is loaded, **when**
   applicability runs, **then** each approved row gets one verdict: applies, does not apply or unsure.
2. **Then** the verdicts match answer key §2: `OBL-01`, `OBL-02`, `OBL-03`, `OBL-05` **applies** ·
   `OBL-04` **unsure** · `OBL-06` **does not apply**.
3. **Then** every verdict cites at least one fund fact ID. `OBL-04` cites `FACT-03` and `FACT-04`.
   `OBL-05` cites `FACT-06` and `EVT-01`.
4. **Then** every verdict has reasoning in plain English, readable by a non-lawyer.
5. **Given** `OBL-04`, **if** the verdict is "applies", **then** the test fails (marketing in Spain is
   not CNMV registration).
6. **Given** a rejected row, **then** it gets no verdict.
7. **Given** applicability output with a missing verdict or fact ID, **then** the run stops, nothing
   goes to G2, and the failure is recorded. Verdicts for the other rows are kept, and only the failed
   row is re-run (US-015 criteria 9–12).

## 4. Scope Notes

- **In Scope for MVP**: one fund, facts from the mock profile only.
- **Deferred**: several funds; fetching facts from real fund records.

## 5. Traceability

- **PRD Anchors**: F4 · §2 step 5 · UN-S5 · AB-1
- **System description**: FR-008, FR-009 · MD-002 · NFR-004, NFR-005 · AC-007
- **Answer key**: §2
- **Related SFS**: none yet

## Sources

- `prd.md` F4 · `system-description.md` MD-002, AC-007 · `mock-data/mock-fund-profile.md` ·
  `mock-data/expected-obligation-library.md` §2

## Assumptions

- Exact reasoning wording is not tested. Only the verdict and the cited fact IDs are.

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criterion 7 clarified: a failed row
  keeps the other verdicts and is re-run alone (US-015, NFR-004); no behaviour removed
