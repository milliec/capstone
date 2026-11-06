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

## 4. Scope Notes

- **In Scope for MVP**: exact, word-for-word matching on mock text.
- **Deferred**: tolerant matching (e.g. ignoring line breaks or typographic quotes) if real documents
  are added later.

## 5. Traceability

- **PRD Anchors**: F2 · §2 step 3 · UN-S2 · AB-1
- **System description**: FR-003 · MD-003 · MN-004, MN-006 · AC-004
- **Related SFS**: none yet

## Sources

- `prd.md` F2 · `system-description.md` MD-003, AC-004

## Assumptions

- "Word for word" means an exact text match after trimming spaces at the start and end.

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
