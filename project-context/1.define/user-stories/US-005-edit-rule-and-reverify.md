# US-005 — Edit a rule and re-verify it

## 1. Story Identity

- **ID**: US-005
- **Title**: Edit a rule and re-verify it
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want my edits to a rule to be checked the same way the agent's output is,
so that a human edit is never the one change nobody checked.

## 3. Acceptance Criteria

1. **Given** a pending row, **when** the specialist edits any field, **then** the quote and conflict
   checks re-run on that row only, and no other row changes.
2. **Given** an edit to `OBL-03`'s offset from "+6 months" to "+4 months", **when** the checks re-run,
   **then** an **internal** conflict is flagged (its own quote says "within six months"), and approval
   needs a written reason. The cross-source flag against `SRC-PRACT-P1` clears, because the two now
   agree.
3. **Given** an edit that changes a quote so it no longer appears in the cited paragraph, **then** the
   quote check fails and the row cannot be approved.
4. **Given** `OBL-02` is approved and has 4 calendar entries, **when** the specialist edits its offset,
   **then** the row returns to **pending**, its 4 entries are marked **out of date**, and the other 18
   entries are unchanged.
5. **Given** `OBL-02` was approved at G1 and its verdict at G2, **when** the specialist edits the row and
   re-approves it at G1, **then** applicability re-runs for that row, and its verdict must be approved
   again at G2 before its calendar entries are regenerated.
6. **Then** every edit is recorded in the audit log with who, when, and the value before and after.

## 4. Scope Notes

- **In Scope for MVP**: edits during G1, and edits to already-approved rows.
- **Deferred**: bulk edits; edit history comparison views.

## 5. Traceability

- **PRD Anchors**: F3 · §2 step 4 · UN-S4, UN-S7
- **System description**: FR-006, FR-007 · MD-005 · AC-005, AC-006, AC-017
- **Related SFS**: none yet

## Sources

- `prd.md` F3 · `system-description.md` MD-005, AC-005, AC-006

## Assumptions

- Out-of-date entries cannot be published (see US-010).

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 14 → 18 unaffected entries (calendar now 22)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · criterion 2 uses the internal check;
  added criterion 5 (edited rows re-enter G2)
