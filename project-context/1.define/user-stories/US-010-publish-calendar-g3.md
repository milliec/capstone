# US-010 — Publish the calendar (Gate G3)

## 1. Story Identity

- **ID**: US-010
- **Title**: Publish the calendar (G3)
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to review the whole calendar and publish it only when I am satisfied,
so that GPs never see unfinished work.

## 3. Acceptance Criteria

1. **Given** a generated calendar, **when** the specialist opens G3, **then** they see all 22 entries,
   with roll notes, the "roll rule unconfirmed" mark on the 2027-02-28 entries for `OBL-04` and `OBL-05`,
   and the "precautionary: registration unconfirmed" note on `OBL-04`.
2. **Given** G1 or G2 is not complete, **when** the specialist tries to publish, **then** publishing is
   refused.
3. **Given** any entry is marked out of date (see US-005), **then** publishing is refused.
4. **Given** entries marked "roll rule unconfirmed" or "precautionary", **then** they do **not** block
   publishing. They are safe defaults (design principle P-1).
5. **When** the specialist publishes, **then** the whole fund calendar is published at once.
6. **Given** the calendar has not been published, **then** the GP view shows no entries for the fund,
   only the read-only message in US-011 criterion 7.
7. **Then** every publish, and every refused attempt, is recorded in the audit log with who and when.
8. **Given** a generated calendar, **when** the specialist declines at G3 without a reason, **then** the
   decline is refused. **With** a reason, it is accepted and the run ends as **declined** (final).
   Correcting the calendar means starting a new run (US-015 criterion 16). The next-step choices, going
   back to G1 or G2, and the reopen they need are future scope (DL-22).
9. **When** the specialist declines, **then** no new version is published. The draft and its review
   history stay available to the specialist only, any previously published version stays visible to
   GPs together with any review notice (deferred, US-011 criterion 10), and no earlier G1 or G2 approval is cancelled. The decline and the reason
   are recorded in the audit log with who and when.
10. **Then** publishing happens only through an explicit publish action. It is never preselected, and
    is never triggered by a timeout or by closing the screen. If the specialist leaves without
    publishing, the calendar stays unpublished.
11. **When** the specialist opens G3, **then** they see a note that the date conventions have not yet
    been checked against the legal texts (SD A-7). The note does not block publishing.
12. **Given** the open question on the AED subscription tax (PRD OQ-7, SD OQ-4), **when** the specialist
    opens G3, **then** each of the four `OBL-02` entries carries a mark saying its rule depends on that
    open question, shown next to the "roll rule unconfirmed" and "precautionary" marks. No other entry
    carries it. **Then** the mark does **not** block publishing (like criterion 4), and the GP view
    shows no such mark (US-011 assumptions). The four dates (20 January, 20 April, 20 July and
    20 October 2027) are the same whether the rule is "no roll" or "roll forward", so the 22 entries
    and their dates do not change. (Decision log DL-20, SAD CR-027, test T-W13-1, SD AC-032.)
13. **Given** the calendar has changed since the specialist's screen loaded (for example it was
    regenerated, or an entry was marked out of date), **when** they submit a publish or decline made on
    the old version, **then** it is refused and not recorded, and a plain message says the calendar
    changed and shows its current version. **Given** the same publish is submitted twice (for example a
    double click), **then** one version is published and the second request is refused with the same
    message. The message follows the voice rule in PRD §6. (SAD CR-009.)
14. **When** the specialist opens G3, **then** they see every row rejected at G1, with the reason given
    at rejection (a demo row keeps its "demo" label), and every source paragraph that no non-rejected
    row cites, with its text. **When** they publish, **then** they give one explicit acknowledgement
    that they have seen both lists, as part of the publish decision; it is never preselected.
    Publishing without it is refused, and so is publishing with an acknowledgement for lists that have
    changed since the page loaded (for example a row rejected meanwhile); a plain message shows the
    current lists. The audit log records the acknowledgement with who, when, and the rows (with their
    versions) and paragraphs it covered. A decline needs no acknowledgement. In the demo run the
    rejected list is the demo row and the uncited list is 7 paragraphs, including the 3 `SRC-PRACT`
    summaries, so the acknowledgement appears on every publish. (SD FR-030, AC-037; decision log DL-30;
    SAD CR-028, test T-G3ACK-1.)

## 4. Scope Notes

- **In Scope for MVP**: one specialist publishes one fund's calendar.
- **Open-question mark**: nothing in the MVP clears the criterion 12 mark. It goes only when the answer
  to the open question is recorded as a regulation change, outside this story. Wording and layout are
  for `@ux.designer`.
- **Deferred**: four-eyes review, scheduled publishing, publishing single entries, withdrawing or
  unpublishing a calendar (deliberately deferred for the demonstration; revisit before real-world use,
  SD §9).

## 5. Traceability

- **PRD Anchors**: F7 · §2 step 8 · UN-S4, UN-G4 · AB-5
- **System description**: FR-014, FR-022, FR-030 · MD-004 · MN-003, MN-007 · AC-013, AC-032, AC-037 · MP-006 · A-6
- **Decision log**: DL-20 (criterion 12) · DL-30 (criterion 14)
- **SAD controls**: CR-009 (criterion 13) · CR-028 (criterion 14)
- **Related SFS**: none yet

## Sources

- `prd.md` F7 · `system-description.md` MD-004, AC-013, A-6

## Assumptions

- Once a calendar is published, GPs keep seeing that version until the specialist publishes again.
  Operator-confirmed. When a change questions that version, GPs also see a neutral review notice (SD
  FR-025, US-011 criteria 9 and 10).

## Open Questions

- **OQ-US010-1**: *Resolved* (operator decision, 2026-11-12, DL-37). Four-eyes review is future scope; one specialist decides at G3. (PRD OQ-1)
- **OQ-US010-2**: *Resolved.* After a post-publish edit, GPs keep seeing the last published version
  until the specialist publishes again (operator-confirmed).
- **OQ-US010-3**: *Resolved* (operator decision, 2026-11-07). See criteria 8 and 9. (SD OQ-6)
- **OQ-US010-4**: *Resolved* (operator decision, 2026-11-07). The last published version plus a neutral
  review notice; OQ-US010-2 stands. (SD OQ-7, FR-025; US-011 criteria 9 and 10)
- **OQ-US010-5**: *Resolved: not in the MVP* (operator decision, 2026-11-07). Recovery is review notice
  → correct → republish. Revisit before real-world use. (SD OQ-8, §9)

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · 18 → 22 entries
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added criterion 4 (safe-default marks do
  not block publishing); Spain note renamed
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-US010-3 to -5 (approval
  map OD-1, OD-4, OD-5); no criterion changed
- 2026-11-07 · persona `product-mgr` · action `update` · added criteria 8 and 9 (G3 decline, FR-022);
  OQ-US010-3 resolved, operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 8 note now points to SD FR-024
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 9 links the review notice; OQ-US010-4
  resolved (SD FR-025), operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · withdraw/unpublish added to Deferred;
  OQ-US010-5 resolved (not in the MVP), operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · criterion 10 (publish only by explicit action;
  PRD §6), operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` ·
  Assumptions cross-reference the review notice (SD FR-025); no new decision
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · criterion 11: G3 note that
  date conventions are unverified (SD A-7, PRD F7); operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · criterion 12 and a scope note: `OBL-02`
  entries carry a mark that their rule depends on the open AED tax question (PRD OQ-7); it does not
  block publishing and is specialist-only; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (SAD CR-009) · criterion 13: a publish or decline
  made on an out-of-date calendar screen, or a publish submitted twice, is refused with a plain message
  showing the current version
- 2026-11-12 · persona `product-mgr` · action `update` (DL-27) · criterion 6 points to the GP message in US-011 criterion 7; no behaviour changed
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · criteria 8–9: a decline needs a reason, is audited and ends the run as declined; no next-step choice (back to G1 or G2 is future scope); correcting means a new run; operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-30) · new criterion 14: G3 lists rejected rows and uncited paragraphs; publishing needs one explicit acknowledgement, refused without it or for changed lists; not needed to decline; traceability updated; operator decision
