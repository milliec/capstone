# US-011 — View the published calendar as a GP

## 1. Story Identity

- **ID**: US-011
- **Title**: View the published calendar as a GP
- **Priority**: Must
- **Persona**: GP / fund manager

## 2. Narrative

As a GP, I want to see what is due, when, who files it and why it applies to my fund, so that I don't
miss a filing and don't have to read legal text.

## 3. Acceptance Criteria

1. **Given** the calendar is published, **when** the GP opens the view, **then** they see 22 entries.
2. **Then** each entry shows:
   - **What**: obligation name and authority;
   - **When**: the due date, plus a note if it was moved;
   - **Who**: the role that files it;
   - **Why**: a plain-English reason it applies, with the source citation and quote.
3. **Example:** the first `OBL-01` entry shows "Monthly financial report U1.1 · CSSF", "11 Jan 2027
   (moved from Sun 10 Jan)", "Filed by: fund administrator", "Applies because the fund is subject to
   Part II", and "Source: CSSF Circular 15/627, `SRC-CSSF15627-P2`" with its quote.
4. **Then** no entry appears for `OBL-06`, and no pending, rejected, unsure or conflicted working content
   is shown. A neutral calendar-level review notice (criterion 9) is permitted.
5. **Then** each `OBL-04` entry's "why" says plainly that it is included **as a precaution** while the
   fund's CNMV registration is confirmed. The entry shows "precautionary" and its reason. No GP text
   states or implies that a registration or marketing is permitted. (PRD F8, SD P-1, OQ-11)
6. **Then** the GP has no way to change anything. Any attempt to change data as a GP is refused.
7. **Given** the calendar is not published, **then** the view shows an empty state with no entries.
8. **Then** the view meets WCAG 2.2 AA.
9. **Given** a published calendar, **when** a change calls its accuracy or completeness into question
   (SD FR-025 triggers, including reopening a "does not apply" verdict or a rejected rule), **then** the
   GP view shows a neutral calendar-level review notice. The last published entries stay visible with
   their publication date. No draft content, flag detail or specialist reasoning is shown. Draft work
   that doesn't affect the published calendar does not trigger it.
10. **Given** the notice is shown, **then** it clears only when a replacement calendar is successfully
    published. A declined or failed publication does not clear it.
11. **Given** the published calendar, **then** the view shows one calendar-level note: entries are
    specialist-approved interpretations, not legal advice, and the date conventions behind them have
    not yet been checked against the legal texts. The note is not repeated on each entry. (SD FR-020,
    Must)

## 4. Scope Notes

- **In Scope for MVP**: one fund; read-only; mocked GP role.
- **Deferred**: filing status, reminders and notifications, export.

## 5. Traceability

- **PRD Anchors**: F8 · §2 step 9 · §6 · UN-G1 to UN-G6 · AB-5, AB-6, AB-7
- **System description**: FR-015, FR-020, FR-025 · A-7 · MD-008 · MN-007 · NFR-005, NFR-010 · AC-013, AC-014
- **Related SFS**: none yet

## Sources

- `prd.md` F8, §6 · `system-description.md` MD-008, AC-014

## Assumptions

- The "roll rule unconfirmed" mark is for the specialist only. The GP sees the date without it.
  Operator-confirmed.
- Display wording above is an example. Exact wording and layout are for `@ux.designer`.

## Open Questions

- **OQ-US011-1**: Should the GP see a neutral "under review" note for items still with compliance?
  Decide before the UX step. (PRD OQ-6) *Before first publication only. After publication, see
  criteria 9 and 10.*

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 18 → 22 entries; `OBL-04` shown as a
  precaution (P-1)
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 4 clarified (working content);
  criteria 9 and 10 added (review notice, SD FR-025); OQ-US011-1 limited to before first publication;
  operator decision
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · criterion 11: one
  calendar-level "not legal advice" and unverified date-conventions note (SD FR-020 now Must, A-7);
  operator decision
- 2026-11-09 · persona `product-mgr` · action `update` (UX review) · criterion 5: shows "precautionary" and its reason; no implied registration or marketing permission (PRD F8); decision log DL-01
