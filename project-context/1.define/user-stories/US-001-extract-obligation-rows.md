# US-001 — Extract source-linked obligation rows

## 1. Story Identity

- **ID**: US-001
- **Title**: Extract source-linked obligation rows
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want obligations extracted from regulatory text into fixed rows that each
quote their source paragraph, so that I check rules instead of writing them by hand.

## 3. Acceptance Criteria

1. **Given** the 6 mock source documents, **when** a run starts, **then** every paragraph is loaded with
   its paragraph ID (e.g. `SRC-UCILAW-P3`).
2. **Given** the loaded paragraphs, **when** extraction runs, **then** exactly 6 rows are produced,
   `OBL-01` to `OBL-06`, matching answer key §1 for obligation, pattern, frequency, anchor, offset,
   recipient, responsible role and applicability rule.
3. **Then** every row has exactly one paragraph ID and a quote that appears word for word in that
   paragraph (answer key §1 quotes).
4. **Then** no row cites `SRC-UCILAW-P1`, `SRC-CSSF15627-P1`, `SRC-CSSF15627-P3`, `SRC-CNMV-P2` or any
   `SRC-PRACT` paragraph.
5. **Then** every row's business-day rule is "not confirmed", because no source states one.
6. **Then** no row contains a calculated due date.
7. **Given** extraction output that is missing a required field, **when** the run checks it, **then**
   the run stops, nothing is passed to review, and the failure is recorded in the audit log.

## 4. Scope Notes

- **In Scope for MVP**: mock text sources only; one framework (Luxembourg UCI Part II).
- **Deferred**: reading real documents (e.g. PDF), other frameworks, re-extraction when a law changes.

## 5. Traceability

- **PRD Anchors**: F1 · §2 steps 1–2 · UN-S1, UN-S2 · AB-1
- **System description**: FR-001, FR-002 · MD-001 · MN-005, MN-006 · NFR-004 · AC-001, AC-002
- **Answer key**: §1
- **Related SFS**: none yet

## Sources

- `prd.md` F1 · `system-description.md` §3–§4, §8 · `mock-data/mock-regulatory-sources.md` ·
  `mock-data/expected-obligation-library.md` §1

## Assumptions

- "Matching the answer key" allows small wording differences in the obligation name. Field values such
  as anchor, offset and paragraph ID must match exactly.

## Open Questions

- **OQ-US001-1**: How close must the obligation name be to the answer key to pass? To be settled in the
  evaluation design (`@qa.eng`).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
