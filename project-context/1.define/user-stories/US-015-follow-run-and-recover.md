# US-015 — Follow a run and recover from a failed step

## 1. Story Identity

- **ID**: US-015
- **Title**: Follow a run and recover from a failed step
- **Priority**: Must
- **Persona**: Compliance specialist

## 2. Narrative

As a compliance specialist, I want to see how far a run has got and, if a step fails, what failed and
what I can do next, so that I don't wait without knowing what's happening and don't lose decisions I
have already made.

## 3. Acceptance Criteria

1. **Given** a run has started, **when** the specialist opens it, **then** they see which steps have
   finished and which step is running (extraction, verification, applicability, calendar generation).
2. **Given** a step fails or returns invalid output (as in US-001 criterion 7 and US-006 criterion 7),
   **then** a plain message names the step and confirms that nothing moved forward.
3. **Then** the run stops at the last safe state, and every gate decision already recorded is kept.
4. **When** the specialist re-runs the failed step, **then** it runs again from the last safe state.
   Finished steps are not repeated, and earlier gate decisions are not asked for again.
5. **Example:** applicability fails after G1 is complete. The specialist re-runs applicability. The six
   G1 decisions stay as they were, and extraction and verification do not run again.
6. **Then** a re-run step replaces its own failed output. It does not add duplicate rows or verdicts.
7. **Then** every failure and every re-run is recorded in the audit log with who, when and which step.
8. **Then** the messages follow the voice rule in PRD §6: they state facts without reassurance or alarm.

## 4. Scope Notes

- **In Scope for MVP**: one run at a time; re-running only the step that failed.
- **Deferred**: automatic retries; resuming a run after the application restarts, unless the SAD shows
  it comes free with the chosen storage.

## 5. Traceability

- **PRD Anchors**: §6 (run status, failures, voice) · OQ-5
- **System description**: NFR-004 · MC-001 · MD-009
- **Related SFS**: none yet

## Sources

- `prd.md` §6, OQ-5 · `system-description.md` NFR-004
- `approval-map.md` §7 "Failure and retries" (proposed: last safe state is the last completed gate; a
  retried step replaces its own failed draft)

## Assumptions

- "Last safe state" means the last completed step or gate. The SAD confirms how it is stored.
- No SD functional requirement covers run status or re-running. This story traces to the PRD §6
  operator decision (decision log DL-02).

## Open Questions

- **OQ-US015-1**: How many times can a step be re-run before the specialist must start a new run?
  (Approval map OD-7, retry limits.) For the SAD.

## Audit

- 2026-11-09 · persona `product-mgr` · action `create-stories` · new story for PRD §6 run status and
  failure recovery (UX review, operator decision); re-running is new scope, estimated under OQ-5;
  decision log DL-02
