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
8. **Then** the change-monitoring system may update review status and flags (including marking entries
   out of date), but never changes the substance of a rule, applicability decision or deadline itself.
   Every substantive change goes through G1 or G2.
9. **Then** every impact report and every resulting decision is recorded in the audit log.
10. **Given** an impact flag on an item in the published calendar, **then** the GP review notice is
    shown (SD FR-025, US-011 criteria 9 and 10).
11. **Given** any impact report, including `AMD-03`'s "no impact", **then** the amendment stays
    **unreviewed** and appears in the specialist's queue until the specialist accepts the report or
    completes manual review.
12. **When** the specialist accepts a report, **then** only its review status changes. Flags stay,
    invalidated approvals are not restored, flagged items still need G1 or G2, and any GP review notice
    stays until a successful republish.
13. **When** the specialist sends an amendment for manual review, **then** a reason is required and
    logged, and the amendment stays open. It leaves the queue only when the specialist marks the manual
    review complete with a **completion note** that records the conclusion and references any resulting
    corrections, or explains why none were needed. Completing it does not clear flags, restore
    approvals or bypass G1 to G3.
14. **Given** `AMD-03` has not yet been accepted, **then** no GP review notice is shown, because there
    are no flags. This is a known limit (see Assumptions).
15. **Then** no report has a preselected "accept" decision, and each report is accepted or sent for
    manual review as a separate, explicit action. Silence, a timeout or closing the screen leaves the
    amendment **unreviewed**.
16. **Then** every acceptance, referral to manual review and manual-review completion is recorded with
    who, when, the exact report version and source amendment version it was made on, and the required
    reason (referral) or completion note (completion). **Given** an accepted report, **when** the report
    is re-run or the amendment is revised, **then** the new version is **unreviewed** and back in the
    queue; the earlier acceptance stays in the audit log but does not apply to the new version.
17. **Given** an amendment in manual review, **when** its report is re-run or the amendment is revised,
    **then** the open review is marked **superseded** and keeps its notes and version references, and
    the amendment stays **unresolved** in the queue, linked to the new versions. The specialist can
    read the earlier notes. **When** the specialist tries to complete the review against a superseded
    version, **then** completion is refused; completion is accepted only as an explicit decision for
    the current versions. **When** the specialist accepts the revised report instead, **then** the
    amendment stays unresolved until the manual review is completed with a note. The audit log shows
    the superseding as a **system** event (not a specialist decision) with its time, the triggering
    revision, the affected review and the old and new version references. Flags, the GP review notice
    and invalidated approvals are unchanged, and G1–G3 still apply.

## 4. Scope Notes

- **In Scope (stretch)**: the three mock amendments; one fund; impact on rows, verdicts and calendar
  entries.
- **Deferred**: watching live sources for changes, amendments that add brand-new obligations, several
  amendments at once, and notifying GPs of changes. (The neutral review notice in criterion 10 is not a
  change notification: it shows no detail of the amendment, SD FR-025.)

## 5. Traceability

- **PRD Anchors**: F10 · UN-S1, UN-S3 · A-8
- **System description**: MD-011 · FR-021, FR-026 · MD-005 (the edit-and-re-verify chain this depends on) ·
  MN-003 · AC-018, AC-019, AC-020
- **Answer key**: §6
- **Related SFS**: none yet

## Sources

- `prd.md` F10 · `system-description.md` MD-011, FR-021, FR-025, FR-026 · `mock-data/mock-regulatory-sources.md`
  (Amendments) · `mock-data/expected-obligation-library.md` §6 · `mock-data/mock-fund-profile.md`
  (`FACT-07`)

## Assumptions

- This story depends on US-005 (edit and re-verify, out-of-date marking). If US-005 is cut, this story
  cannot be built.
- Over-flagging counts as a failure, just like missing an affected item.
- An unaccepted amendment may contain an undiscovered impact. The absence of a GP notice does not mean
  the calendar has been checked against it. Sign-off reduces the risk of a silent miss; it does not
  guarantee completeness.
- If this stretch is built, report acceptance or a documented manual review is mandatory for every
  report (SD FR-026).

## Open Questions

- **OQ-US014-1**: Does the stretch fit the six weeks? To be estimated separately in the SAD (PRD OQ-5).
- **OQ-US014-2**: *Resolved* (operator decision, 2026-11-07). Every report needs acceptance or a
  documented manual review, including "no impact". See criteria 11 to 14, SD FR-026. *(Approval map
  OD-9.)*

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories` · stretch goal, operator decision
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-US014-2 (approval map
  OD-9); no criterion changed
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 10 (impact flag on a published item
  triggers the GP review notice, SD FR-025), operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 8 scoped to the change-monitoring
  system; criteria 11 to 14 (report acceptance, manual review with completion note, SD FR-026);
  limitation added to Assumptions; OQ-US014-2 resolved, operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 15 (no preselected acceptance; PRD
  §6), operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` · Deferred
  note distinguishes the review notice from GP change notifications; Sources list FR-025, FR-026; no
  new decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · criterion 16
  (report-review decisions record report and amendment versions; a revised report or amendment does
  not inherit acceptance; SD FR-026), operator decision; applies only if the stretch is built
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · criterion 17
  (revision during an open manual review: superseded review kept, completion only for current
  versions; SD FR-026), operator decision; applies only if the stretch is built
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · criterion 17:
  accepting a revised report does not close a referred amendment; superseding logged as a system event
  (SD FR-026, MD-009), operator decisions; applies only if the stretch is built
