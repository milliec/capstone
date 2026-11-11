# US-002 — Verify quotes

## 1. Story Identity

- **ID**: US-002
- **Title**: Verify quotes
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want every extracted rule's quote checked word for word against its
source paragraph by a separate check, so that I never approve a rule based on a quote that isn't really
in the law.

## 3. Acceptance Criteria

1. **Given** the 6 rows from US-001 with correct quotes, **when** verification runs, **then** all 6 pass
   the quote check.
2. **Given** `OBL-01` with its quote changed by one word ("10 **business** days" instead of "10
   **calendar** days"), **when** verification runs, **then** the quote check fails and the row is
   marked as blocked from approval.
3. **Given** a row with no paragraph ID, **when** verification runs, **then** the quote check fails.
4. **Then** the verification never changes any field of any row.
5. **Then** each verification result records which check produced it, and that it is **not** the
   extraction step that produced the row.
6. **Then** every result is recorded in the audit log.
7. **Given** a failed quote check, **then** the flag states its type ("quote check") and shows the
   text that does not match, next to the source paragraph it was checked against. (PRD F2)
8. **Normalisation boundary (SAD QN-1).** **Given** a correct quote whose line break is replaced by
   two spaces and which has a trailing space, **when** verification runs, **then** it passes. **Given**
   the same quote with one letter's case changed, or one straight quote mark changed to a typographic
   one, **then** it fails and the row is blocked from approval. The check is code and runs without a
   language model.

## 4. Scope Notes

- **In Scope for MVP**: exact, word-for-word matching on mock text, in deterministic code, with
  whitespace runs (including line breaks) treated as one space (SAD QN-1).
- **Deferred**: tolerant matching beyond whitespace (e.g. typographic quotes, case, Unicode forms) if
  real documents are added later.

## 5. Traceability

- **PRD Anchors**: F2 · §2 step 3 · UN-S2 · AB-1
- **System description**: FR-003 · MD-003 · MN-004, MN-006 · AC-004
- **Related SFS**: none yet

## Sources

- `prd.md` F2 · `system-description.md` MD-003, AC-004

## Assumptions

- "Word for word" means an exact, case-sensitive text match after trimming and collapsing whitespace
  (SAD rule QN-1). Nothing else is normalised.

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-09 · persona `product-mgr` · action `update` (UX review) · criterion 7: quote-check flag states its type and shows the mismatched text (PRD F2); decision log DL-03
- 2026-11-11 · operator session (`@system.arch`, at the operator's instruction) · action `update` · criterion 8 (normalisation boundary), scope note and assumption aligned with SAD QN-1; quote check is deterministic code (approval map OD-8 resolved); operator decision
