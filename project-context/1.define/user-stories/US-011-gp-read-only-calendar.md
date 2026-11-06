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
4. **Then** no entry appears for `OBL-06`, and nothing pending, rejected, unsure or conflicted is shown.
5. **Then** each `OBL-04` entry's "why" says plainly that it is included **as a precaution** while the
   fund's CNMV registration is confirmed.
6. **Then** the GP has no way to change anything. Any attempt to change data as a GP is refused.
7. **Given** the calendar is not published, **then** the view shows an empty state with no entries.
8. **Then** the view meets WCAG 2.2 AA.

## 4. Scope Notes

- **In Scope for MVP**: one fund; read-only; mocked GP role.
- **Deferred**: filing status, reminders and notifications, export.

## 5. Traceability

- **PRD Anchors**: F8 · §2 step 9 · §6 · UN-G1 to UN-G6 · AB-5, AB-6, AB-7
- **System description**: FR-015 · MD-008 · MN-007 · NFR-005, NFR-010 · AC-013, AC-014
- **Related SFS**: none yet

## Sources

- `prd.md` F8, §6 · `system-description.md` MD-008, AC-014

## Assumptions

- The "roll rule unconfirmed" mark is for the specialist only. The GP sees the date without it.
  Operator-confirmed.
- Display wording above is an example. Exact wording and layout are for `@ux.designer`.

## Open Questions

- **OQ-US011-1**: Should the GP see a neutral "under review" note for items still with compliance?
  Decide before the UX step. (PRD OQ-6)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 18 → 22 entries; `OBL-04` shown as a
  precaution (P-1)
