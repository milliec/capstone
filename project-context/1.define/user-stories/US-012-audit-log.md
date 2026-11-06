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
2. **Then** every human decision (approve, reject, edit, override, publish) is recorded with who, when
   and what. Rejections, overrides and approvals over a flag include the written reason.
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
- **System description**: FR-017 · MD-009 · NFR-003, NFR-011 · AC-016 · MP-008
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
