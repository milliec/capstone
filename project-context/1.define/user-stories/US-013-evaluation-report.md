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
6. **Then** a target counts as passed only at its exact value (for example 6 of 6 rows, 22 of 22
   entries). A missed target is reported as a result, with what was expected and what happened. The
   report never leaves a miss out. (PRD §7)
7. **Then** the report shows the operator's manual-effort estimate next to the measured review time,
   labelled as an **estimate**. It claims no time saving or ROI. (PRD §7, OQ-12)
8. *Deferred (DL-22).* **Given** the specialist created rows by hand at G1 (US-016), **then** the report counts them on
   their own line, separate from the extractor's result. They are left out of the "rows found out of 6"
   and "extra rows" figures, so they can neither inflate nor hide the extractor's result. With no
   human-created rows, the line shows 0. (SD FR-027, decision log DL-15)
9. *Deferred (DL-22).* **Given** a source document was released to manual entry after failing its re-runs (US-015
   criterion 14), **then** the report counts the release as one **extraction failure**, names the
   document, and does not count it as a pass. The rows the specialist then creates by hand for it are
   counted on the human-created line (criterion 8), not as extracted rows. With no release, the
   extraction-failure count shows 0. (SD AC-031, decision log DL-18, SAD test T-REL-1)
10. **Given** the evaluation criteria that depend on the live model (SAD §9: EC-001 to EC-007, EC-010,
    EC-012 and EC-021), **then** they count as passed only when they pass on **3 of 3 consecutive
    evaluation runs on the same commit**. This applies before a merge that changes a prompt, a model or
    a schema, and before the demo. One passing run is not enough, because the agents are probabilistic
    even at temperature 0. The report records which runs and which commit the three passes belong to.
    (Decision log DL-23, SAD EC-R1.)
11. **Given** an extracted obligation name, **then** it is graded by the specialist's judgement ("same
    obligation" or not) and the verdict is recorded per row in the report. The fields that drive dates
    and routing (paragraph ID, quote, frequency, anchor, offset, recipient, responsible role and
    applicability rule) are graded by exact match against the answer key. No model grades the name.
    (Decision log DL-23, SAD EC-002.)

## 4. Scope Notes

- **In Scope for MVP**: evaluation against the answer key for the mock data set.
- **Deferred**: evaluations on new data sets; trend tracking across runs.

## 5. Traceability

- **PRD Anchors**: F9 · §7 technical metrics
- **System description**: FR-018, FR-027 · MP-001 to MP-004 · MC-001, MC-002, MC-003 · AC-027, AC-031
- **Decision log**: DL-23 (criteria 10–11)
- **Answer key**: §1 to §4
- **Related SFS**: none yet

## Sources

- `prd.md` F9, §7 · `system-description.md` MP-001 to MP-004, MC-001, MC-002 ·
  `mock-data/expected-obligation-library.md`

## Assumptions

- Review time is measured from the audit log, so a stranger can score it from the report without
  watching the demo (operator decision).

## Open Questions

- **OQ-US013-1**: *Resolved* (operator decision, decision log DL-23, SAD EC-002). The name is graded by
  the specialist's judgement, recorded per row; the fields that drive dates and routing are graded by
  exact match (criterion 11). *(Shared with OQ-US001-1.)*

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · calendar out of 22
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added internal-conflict test `I-1`
- 2026-11-06 · persona `product-mgr` · action `update` · review time reported from audit-log timestamps
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · criterion 6 (exact-value pass, misses reported) and criterion 7 (labelled manual-effort estimate, no ROI claim) (PRD §7); decision log DL-10, DL-11
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criterion 8 (human-created rows counted
  on a separate line); decision log DL-15; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18) · criterion 9: a release to manual entry
  is counted as one extraction failure (SD AC-031); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · criteria 8–9 (human-created rows; release counted as an extraction failure) marked deferred; nothing deleted
- 2026-11-12 · persona `product-mgr` · action `update` (DL-23) · criterion 10 (model-dependent criteria must pass 3 of 3 consecutive runs on one commit) and criterion 11 (names graded by the specialist, date and routing fields by exact match); OQ-US013-1 resolved; operator decision. DL-23 and SAD EC-R1, EC-002 are on the architect's branch and not yet on main
