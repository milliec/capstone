# US-016 — Add a missed rule by hand

## 1. Story Identity

- **ID**: US-016
- **Title**: Add a missed rule by hand
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to add an obligation the extraction missed, so that a gap I can see
at G1 is fixed by me, in the same checked way as every other row, instead of by re-running extraction
and hoping.

## 3. Acceptance Criteria

1. **Given** the G1 review screen, **when** the specialist opens the edit form on an empty row,
   **then** they can enter a source paragraph ID, a quote and the other row fields. No model is called
   to create the row, and the screen offers no "re-extract" action.
2. **Given** a new row with no paragraph ID, or a paragraph ID that is not among the loaded
   paragraphs, **then** it cannot be saved as approvable.
3. **Given** a new row whose quote does not appear word for word in the cited paragraph, **then** the
   quote check fails and the row cannot be approved. The quote check cannot be skipped for a row made
   by hand (US-002).
4. **Given** a new row with a valid paragraph ID and a quote that passes the check, **when** the
   specialist saves it, **then** it is stored as **human-created** and shown at G1 labelled "added by
   specialist". The creator's identity is recorded. The label cannot be changed afterwards.
5. **Then** the conflict checks (internal and cross-source) run on the new row, as for any row
   (US-003, US-005 criterion 1). No other row changes.
6. **Then** the new row is **pending** and needs its own G1 decision (US-004). It has no preselected
   decision, and G1 is not complete until the specialist has approved or rejected it.
7. **Given** an approved human-created row, **then** it follows the normal path: applicability (US-006),
   G2 (US-007) and the calendar. Editing it later returns it to pending (US-005).
8. **Then** creating the row is recorded in the audit log with who, when, the origin "human" and the
   values entered.
9. **Then** the evaluation report counts human-created rows on their own line (US-013 criterion 8).
10. **Example:** the specialist creates a row with a quote that has one word changed: it cannot be
    approved. They correct the quote: the row is saved, flags are shown, it gets a G1 decision, and its
    audit entry shows the origin "human".
11. **Given** a source document the specialist has released to manual entry (US-015 criterion 14),
    **when** G1 opens, **then** its paragraphs appear in the coverage view and the specialist can create
    rows for them by hand with the same form. These rows are human-created like any other: source
    paragraph and quote required, the code quote check cannot be skipped, the conflict checks run, and
    each gets its own G1 decision (criteria 2–6). Nothing about them is trusted because the document was
    released.

## 4. Scope Notes

- **In Scope for MVP**: one row at a time, entered through the existing edit form (US-005). Only the
  specialist role can create a row (NFR-010).
- **Not included**: any model-assisted creation, a "re-extract this paragraph" action, and creating
  several rows at once. This is deliberate (decision log DL-15): the costliest error should not be
  fixed with a probabilistic step.
- The coverage view (FR-028) is how the specialist finds a paragraph that may have been missed. It
  makes the gap visible; it does not say which paragraphs hold an obligation.
- **Two ways in**: a row missed by extraction (criteria 1–10) and a row for a released document
  (criterion 11, decision log DL-18). Both use the same form and the same checks.

## 5. Traceability

- **PRD Anchors**: F3 (G1 review; both cases are listed, see OQ-US016-2) · §2 step 4 · UN-S4. New
  Must scope added by operator decision (DL-15).
- **System description**: FR-027 · MD-005, MD-009 · MN-006 · P-1 · AC-027 · NFR-010
- **Decision log**: DL-15, DL-18 (criterion 11)
- **Related SFS**: none yet

## Sources

- `decision-log.md` DL-15 · `sad.md` W-07a, CR-020 · `system-description.md` MN-006, MD-005

## Assumptions

- The system assigns the new row's ID. The ID format is for the architect and must not collide with
  the answer key's `OBL-01` to `OBL-06`.

## Open Questions

- **OQ-US016-1**: Which ID format do human-created rows get, and how does the evaluation tell them
  apart from extracted rows? (For `@system.arch` and `@qa.eng`; the origin label is the rule.)
- **OQ-US016-2**: *Resolved* (operator decision, 2026-11-11). PRD F3 mentions manual row creation for
  both cases: a missed row at G1 (SD FR-027, this story's criteria 1–10) and the rows for a released
  document (US-015 criterion 14, this story's criterion 11). In both, the row needs a source quote,
  passes the code quote check, is labelled as manual and is audited.

## Audit

- 2026-11-11 · persona `product-mgr` · action `create-stories` · new story for DL-15 (manual row
  creation), from SAD SOQ-8; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18, SAD SOQ-9) · criterion 11 and scope note: rows created by hand for a source document released to manual entry (US-015 criteria 14–15); OQ-US016-2 now covers the release too
- 2026-11-11 · persona `product-mgr` · action `update` · OQ-US016-2 resolved (operator decision): PRD F3 mentions manual row creation only for a released document; PRD anchor wording updated; no criterion changed
- 2026-11-11 · persona `product-mgr` · action `update` · OQ-US016-2 resolution corrected (operator confirmed the earlier wording only described the PRD): PRD F3 lists manual row creation for both a missed row at G1 and a released document; PRD anchor wording updated; no criterion changed, DL-15 and FR-027 unchanged
