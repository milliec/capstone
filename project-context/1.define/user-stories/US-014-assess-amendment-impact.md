# US-014 — Assess the impact of a rule amendment (stretch goal)

## 1. Story Identity

- **ID**: US-014
- **Title**: Assess the impact of a rule amendment
- **Priority**: Could (stretch goal, built only after the Must stories pass)
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want the system to work out which obligations a rule amendment affects and
flag only those, so that I re-check what changed instead of re-reading the whole library.

## 3. Acceptance Criteria

All criteria start from the published 22-entry demo calendar. Each amendment is tested on its own.

1. **Given** amendment `AMD-01` (annual report: six → five months), **when** impact is assessed,
   **then** only `OBL-03` is flagged, with the reason that its offset and quote no longer match the
   amended text.
2. **Then** the `OBL-03` calendar entry is marked out of date, and `OBL-02`, from the same source
   document, is **not** flagged.
3. **Given** the specialist re-approves `OBL-03` at G1 with "+5 months", **then** its new calendar date
   is 2027-05-31.
4. **Given** amendment `AMD-02` (a new Part II scope paragraph), **then** `OBL-01` and `OBL-03` are
   flagged for applicability re-check at G2, their 13 calendar entries are marked out of date, and no
   other row is flagged.
5. **Given** the specialist confirms both verdicts using `FACT-07` (monthly redemption), **then** both
   still apply and their dates are unchanged.
6. **Given** amendment `AMD-03` (RBE wording reordered, same meaning), **then** nothing is flagged and the
   report states "wording change only; no impact".
7. **Then** for every amendment, the report lists each affected item with a reason, and says which items
   were checked and found unaffected.
8. **Then** the system never changes a row, verdict or calendar entry itself. Every change goes through
   G1 or G2.
9. **Then** every impact report and every resulting decision is recorded in the audit log.

## 4. Scope Notes

- **In Scope (stretch)**: the three mock amendments; one fund; impact on rows, verdicts and calendar
  entries.
- **Deferred**: watching live sources for changes, amendments that add brand-new obligations, several
  amendments at once, and notifying GPs of changes.

## 5. Traceability

- **PRD Anchors**: F10 · UN-S1, UN-S3 · A-8
- **System description**: MD-011 · FR-021 · MD-005 (the edit-and-re-verify chain this depends on) ·
  MN-003 · AC-018, AC-019, AC-020
- **Answer key**: §6
- **Related SFS**: none yet

## Sources

- `prd.md` F10 · `system-description.md` MD-011, FR-021 · `mock-data/mock-regulatory-sources.md`
  (Amendments) · `mock-data/expected-obligation-library.md` §6 · `mock-data/mock-fund-profile.md`
  (`FACT-07`)

## Assumptions

- This story depends on US-005 (edit and re-verify, out-of-date marking). If US-005 is cut, this story
  cannot be built.
- Over-flagging counts as a failure, just like missing an affected item.

## Open Questions

- **OQ-US014-1**: Does the stretch fit the six weeks? To be estimated separately in the SAD (PRD OQ-5).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories` · stretch goal, operator decision
