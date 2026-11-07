# US-012 — Record every output and decision

## 1. Story Identity

- **ID**: US-012
- **Title**: Record every output and decision
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want every agent output and every human decision recorded permanently, so
that I can show afterwards who decided what, when and why.

## 3. Acceptance Criteria

1. **Given** a run, **then** every agent output (extracted rows, check results, verdicts) is recorded
   with the time, the step that produced it and the run ID.
2. **Then** every human decision (approve, reject, edit, override, reopen, publish, decline) is recorded
   with who, when and what. Rejections, overrides, approvals over a flag, reopenings (SD FR-023,
   FR-024) and G3 declines (with the chosen next step, SD FR-022) include the written reason. Each
   approval decision (approve, reject, override, reopen, publish, decline) also records the version of
   the row, verdict or calendar it was made on (SD MD-009).
3. **Then** edits record the value before and after. Opening each gate is also recorded with who and
   when, so review time can be measured (US-013).
4. **When** anyone tries to change or delete a log entry, **then** it is refused.
5. **Given** a full demo run, **then** every decision made in that run appears in the log.
6. **Then** these tests run without a language model.

## 4. Scope Notes

- **In Scope for MVP**: one log for the demo run; mocked user identities.
- **Deferred**: tamper-evident storage, exporting the log, retention rules.

## 5. Traceability

- **PRD Anchors**: F9 · UN-S7 · §3 runtime constraints (Identity, Logging)
- **System description**: FR-017 · MD-009 · NFR-003, NFR-011 · AC-016 · MP-008 · FR-022 to FR-024
  (reasons)
- **Related SFS**: none yet

## Sources

- `prd.md` F9, §3 · `system-description.md` MD-009, NFR-003, AC-016

## Assumptions

- Mocked identities (e.g. "specialist-1") are enough to show who acted in the MVP.

## Open Questions

- None.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-stories`
- 2026-11-06 · persona `product-mgr` · action `update` · gate-opening events recorded (for review time)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` ·
  criterion 2 adds reopen and decline, with their required reasons (SD MD-009, FR-022 to FR-024); no
  new decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · criterion 2: each
  override records the rule or verdict version (SD MD-009), operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · criterion 2: the
  version requirement extended from overrides to every approval decision (SD MD-009); supersedes the
  override-only wording above; operator decision
