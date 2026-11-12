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
   the run stops, nothing is passed to review, and the failure is recorded in the audit log. Rows from
   the other documents are kept, and only the failed document is re-run (US-015 criteria 9–11).
8. **Given** the 13 loaded source paragraphs and the 6 extracted rows, **when** G1 opens, **then** the
   coverage view lists every paragraph that no non-rejected row cites, each with its text: here the 7
   paragraphs named in criterion 4 (4 listed by ID, plus the 3 `SRC-PRACT` paragraphs). It lists none
   of the 6 paragraphs the rows cite. It is computed from the loaded paragraph IDs and the rows' cited IDs only:
   the answer key is not used, and the view does not say which uncited paragraphs contain an
   obligation. It does not block G1.
9. *Deferred (DL-22).* **Given** the coverage view lists a paragraph, **when** the specialist creates a row that cites it
   (US-016), **then** the paragraph no longer appears in the view.
10. **Given** a paragraph whose only row is rejected at G1 (US-004), **then** the paragraph appears in
    the coverage view again. If the row is reopened (US-004 criterion 9), the paragraph leaves the view. *The reopening part is deferred (DL-22).*
    (Tested with a rejected copy of a row, not by changing the mock sources.)

## 4. Scope Notes

- **In Scope for MVP**: mock text sources only; one framework (Luxembourg UCI Part II).
- **Coverage view**: it makes a gap visible (a missed row is the costliest error, P-1); fixing a real
  gap is done with US-016. Only a row that is not rejected counts as citing a paragraph, so a rejected
  row never hides its paragraph (operator decision, 2026-11-11).
- **Not included**: any way to mark a paragraph as "reviewed, no obligation" (see OQ-US001-2).
- **Deferred**: reading real documents (e.g. PDF), other frameworks, re-extraction when a law changes.

## 5. Traceability

- **PRD Anchors**: F1 · §2 steps 1–2 · UN-S1, UN-S2 · AB-1
- **System description**: FR-001, FR-002, FR-028 · MD-001 · MN-005, MN-006 · NFR-004 · AC-001, AC-002, AC-029
- **Answer key**: §1
- **Related SFS**: none yet

## Sources

- `prd.md` F1 · `system-description.md` §3–§4, §8 · `mock-data/mock-regulatory-sources.md` ·
  `mock-data/expected-obligation-library.md` §1

## Assumptions

- "Matching the answer key" allows small wording differences in the obligation name. Field values such
  as anchor, offset and paragraph ID must match exactly. Whether a name is the "same obligation" is the
  specialist's call (DL-23, US-013 criterion 11).

## Open Questions

- **OQ-US001-1**: *Resolved* (operator decision, decision log DL-23, SAD EC-002). The obligation name is
  graded by the specialist's judgement, recorded per row in the evaluation report; the fields that
  drive dates and routing must match exactly (US-013 criterion 11).
- **OQ-US001-2**: *Resolved: accepted as a known MVP limitation* (operator decision, 2026-11-12).
  Nothing records that a paragraph was read and holds no obligation (for example `SRC-UCILAW-P1`, a
  definition), so the 7 demo paragraphs stay in the coverage view on every run, as uncovered, a
  warning. The specialist cannot clear them. A "reviewed, no obligation" mark is **future scope**; no
  feature is added now (SD §9).

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criteria 8–9 and a scope note: G1
  coverage view of uncited paragraphs (FR-028); 7 uncited paragraphs in the demo set; operator decision
  DL-15 context
- 2026-11-11 · persona `product-mgr` · action `update` · only non-rejected rows count as citing a
  paragraph (criteria 8 and 10, scope note); OQ-US001-2 (no way to mark a paragraph as having no
  obligation); operator decision. AC-001 and AC-002 unaffected
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criterion 7 clarified: valid rows from
  other documents are kept and only the failed document is re-run (US-015, NFR-004)
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · criterion 9 (a row created by hand removes the paragraph from the view) deferred; the reopening clause of criterion 10 deferred; the coverage view itself stays
- 2026-11-12 · persona `product-mgr` · action `update` (DL-23) · OQ-US001-1 resolved: the name is graded by the specialist, the date and routing fields by exact match; assumption points to US-013 criterion 11
- 2026-11-12 · persona `product-mgr` · action `update` · OQ-US001-2 resolved: accepted as a known MVP limitation, the mark is future scope; operator decision
