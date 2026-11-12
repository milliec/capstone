# US-004 — Approve or reject rules (Gate G1)

## 1. Story Identity

- **ID**: US-004
- **Title**: Approve or reject rules (G1)
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to approve or reject each verified rule and set its business-day
rule, so that only rules I trust enter the obligation library.

## 3. Acceptance Criteria

1. **Given** verified rows, **when** the specialist opens G1, **then** each row shows its fields,
   paragraph ID, quote, quote-check result and any conflict flags.
2. **When** the specialist approves a row, **then** they set its business-day rule (roll forward / no
   roll / not confirmed) and the row becomes **approved**.
3. **When** the specialist rejects a row, **then** a written reason is required, and the row is marked
   **rejected** and is not sent to applicability unless it is reopened (criterion 9).
4. **Given** a row that failed the quote check, **then** it cannot be approved.
5. **Given** `OBL-03` with conflict `C-1`, **when** the specialist approves it without a reason, **then**
   approval is refused. **With** a reason, it is approved and the reason is recorded.
6. **Given** any row still undecided, **then** G1 is not complete and applicability (US-006) does not
   start.
7. **Then** every approval, rejection, reason and business-day rule is recorded in the audit log with
   who and when.
8. **Given** the demo decisions in the story index, **then** all 6 rows end G1 approved, with business-day
   rules as in answer key §5.
9. *Deferred (DL-22).* **Given** a rejected row, before or after publication, **when** the specialist reopens it without a
   reason, **then** reopening is refused. **With** a reason, the row returns to **pending** and is
   re-verified. The original rejection stays in the audit log.
10. *Deferred (DL-22).* **Given** a reopened row, **then** G1 is not complete until the row is approved or rejected again,
    and its verdict then needs G2. Until both are done, publishing a new calendar version is refused
    (US-010 criterion 2). If a calendar is already published, GPs keep seeing it until the specialist
    republishes, with a neutral review notice (US-011 criterion 9).
11. *Deferred (DL-22).* **Given** a rejected row, **when** the specialist tries to edit it directly, **then** the edit is
    refused. A rejected row is read-only until it is reopened (criterion 9); after reopening, normal
    pending-row editing applies (US-005).
12. **Given** the G1 review screen, **then** there is no "approve all" or other bulk decision, and no
    row has a preselected approve or reject decision. Each decision is a separate, explicit action,
    recorded on its own in the audit log with its own timestamp. Safe default values, such as the
    business-day rule "not confirmed", may be shown as proposed values.
13. **Given** undecided rows, **when** the specialist closes the screen, the session times out, or
    nothing is done, **then** those rows stay **pending** and G1 is not complete. Rows already decided
    keep their recorded decisions.
14. *Deferred (DL-22).* **Given** rows that may describe one obligation, **when** G1 opens, **then** code groups them and
    shows each group as "possible duplicates" with a plain warning, every row's quote and source
    visible. A group forms when rows (a) cite the same paragraph ID, (b) match exactly on recipient,
    anchor and offset, or (c) match on recipient and frequency where one cites a primary source and the
    other a secondary summary (`SRC-PRACT-*`). No model merges rows, and a group does not block any
    single row: each row still needs its own decision (criterion 12). Groups are logged when computed.
    If the groups cannot be computed, G1 does not open and the failure is shown (US-015).
15. *Deferred (DL-22).* **Given** a group with two or more **approved** rows, **when** the specialist completes G1, **then**
    completion is refused until they give one confirmation with a written reason, naming the rows. With
    the reason, G1 completes, and the audit log records the confirmation with the reason and the rows'
    IDs and versions. A group with one or no approved rows needs no confirmation. (Decision log DL-16.)
16. *Deferred (DL-22).* **Example:** a copy of `OBL-02` is added so two rows cite `SRC-UCILAW-P2`: one group is shown with
    a warning. The specialist approves both and tries to complete G1 without a reason: refused. With a
    reason: G1 completes and the audit entry shows the reason and both rows. (Tested with a copy of a
    row, as in US-013 criterion 4.)
17. **Given** the open question on the AED subscription tax (PRD OQ-7, SD OQ-4), **when** the
    specialist sets the business-day rule for `OBL-02`, **then** the form shows that the rule depends on
    that open question. The row has no preselected rule beyond the proposed safe value "not confirmed"
    (criterion 12), and the code has no built-in default for it. The note does not block approval. In
    the demo the specialist sets "no roll" (answer key §5). The matching mark at G3 is US-010
    criterion 12. (Decision log DL-20, SAD CR-027, SD AC-032.)
18. **Given** a row has changed since the specialist's screen loaded (for example it was edited or
    re-verified), **when** they submit an approve, reject or reopen decision made on the old version,
    **then** the decision is refused and not recorded, and a plain message says the item changed and
    shows its current version. **Given** the same decision is submitted twice (for example a double
    click), **then** one decision is recorded and the second request is refused with the same message.
    The message follows the voice rule in PRD §6: facts, without reassurance or alarm. (SAD CR-009.)
19. **Given** a run started with the demo switch on, **when** G1 opens, **then** a seventh row marked
    "demo" is shown, and its only decision is reject with a written reason. Approving it is refused
    with a plain message and the refusal is logged; G1 is not complete until it is rejected. The 6
    extracted rows are decided as in criterion 8. With the switch off (the default), no demo row
    appears. (SD FR-031, AC-038; decision log DL-31; SAD CR-029.)

## 4. Scope Notes

- **In Scope for MVP**: one specialist; one decision per row.
- **Demo set**: the six answer-key rows form no group (different paragraphs, recipients and offsets;
  none cites `SRC-PRACT`), so criterion 15 does not apply to the demo path in criterion 8.
- **Open-question note (G1)**: now criterion 17; the mark at G3 is US-010 criterion 12.
- **Deferred**: four-eyes review (a second specialist confirms), pending decision on timing.

## 5. Traceability

- **PRD Anchors**: F3 · §2 step 4 · UN-S4, UN-S7 · AB-1, AB-4
- **System description**: FR-005, FR-023, FR-029, FR-031 · MD-004 · MN-003, MN-004, MN-006 · AC-006, AC-028, AC-032, AC-038 · NFR-010
- **Decision log**: DL-16 (criteria 14–16), DL-20 (criterion 17), DL-31 (criterion 19)
- **SAD controls**: CR-009 (criterion 18), CR-029 (criterion 19)
- **Answer key**: §5 (business-day rules)
- **Related SFS**: none yet

## Sources

- `prd.md` F3 · `system-description.md` MD-004, AC-006 · `user-stories/README.md` (demo decisions)

## Assumptions

- G1 is complete only when **every** row is approved or rejected. Applicability then runs on all
  approved rows together. Operator-confirmed.

## Open Questions

- **OQ-US004-1**: Four-eyes review: in the MVP or later? (PRD OQ-1)
- **OQ-US004-2**: *Resolved* (operator decision, 2026-11-07). Yes, with a reason, before or after
  publication. See criteria 9 and 10, SD FR-023. *(Approval map OD-2.)*

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-US004-2 (approval map
  OD-2); no criterion changed
- 2026-11-07 · persona `product-mgr` · action `update` · reopen a rejected row (new scope decision, SD
  FR-023): criterion 3 reworded ("never" → "unless reopened"), criteria 9 and 10 added; OQ-US004-2
  resolved
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 11 (rejected rows read-only until
  reopened); criterion 10 links the GP review notice; operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · criteria 12 and 13 (no bulk or preselected
  decisions; silence leaves rows pending; PRD §6), operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criteria 14–16: possible-duplicate
  groups at G1 and one confirmation with a reason at G1 completion (FR-029, DL-16); operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · scope note: the G1 form shows that
  `OBL-02`'s rule depends on the open AED tax question (PRD OQ-7); no criterion changed
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · the G1 note is now criterion 17 and is
  traced to SD AC-032; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (SAD CR-009) · criterion 18: a decision made on an
  out-of-date screen, or submitted twice, is refused with a plain message showing the current version
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · criteria 9–11 (reopen a rejected row; rejected rows read-only) and 14–16 (possible duplicates and the completion confirmation) marked deferred; nothing deleted
- 2026-11-12 · persona `product-mgr` · action `update` (DL-31) · new criterion 19: a demo row (switch on) can only be rejected with a reason; approval refused and logged; no demo row with the switch off; traceability updated; operator decision
