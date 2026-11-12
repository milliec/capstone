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
4. *Deferred (DL-22).* **When** the specialist re-runs the failed step, **then** it runs again from the last safe state.
   Finished steps are not repeated, and earlier gate decisions are not asked for again.
5. *Deferred (DL-22).* **Example:** applicability fails after G1 is complete. The specialist re-runs applicability. The six
   G1 decisions stay as they were, and extraction and verification do not run again.
6. *Deferred (DL-22).* **Then** a re-run step replaces its own failed output. It does not add duplicate rows or verdicts.
7. **Then** every failure and every re-run is recorded in the audit log with who, when and which step.
8. **Then** the messages follow the voice rule in PRD §6: they state facts without reassurance or alarm.
9. **Given** a step made of one call per unit (extraction: one per source document; verification and
   applicability: one per row), **when** one unit fails or returns invalid output, **then** the valid
   output of every other unit is kept, the failed unit is marked **re-runnable**, and run status shows
   in plain words which units are valid and which failed, and why.
10. **Then** the gate after that step does not open until every unit has valid output. This is what
    "nothing is passed to review" means in US-001 criterion 7 and US-006 criterion 7. The one exception
    is a source document released to manual entry (criterion 14).
11. *Deferred (DL-22).* **When** the specialist re-runs a failed unit, **then** only that unit runs again. Its new output
    replaces its own earlier output for the same input, valid units and recorded gate decisions stay as
    they were, no duplicate rows or verdicts appear, and the audit log names the unit.
12. *Deferred (DL-22).* **Example:** applicability output for `OBL-04` is invalid. The other five verdicts are kept and G2
    does not open. The specialist re-runs `OBL-04` only, and G2 then opens with all six verdicts.
13. *Deferred (DL-22).* **Given** a unit that has been re-run 3 times for the same input without valid output, **then** it
    is marked **needs attention**, the specialist is told this is likely a systematic failure and not a
    one-off, and no further re-run is offered for that input. The specialist can start a new run. For a
    source document, criterion 14 also applies. (SAD CR-010; an input changes when a row or document
    changes.)
14. *Deferred (DL-22).* **Given** a source document whose extraction is **needs attention**, **when** the specialist
    releases it to manual entry with a written reason, **then** that one document stops holding G1
    closed. Release is refused without a reason, refused before the document has reached the re-run
    limit, and applies to one document at a time. Every other unit must still be valid before G1 opens.
    The release is recorded in the audit log with who, when, the document and the reason.
15. *Deferred (DL-22).* **Given** a released document, **when** G1 opens, **then** its paragraphs appear in the coverage view
    (US-001 criterion 8) because no row cites them, and the specialist adds any missing rows by hand
    (US-016). The evaluation report counts the release as one **extraction failure** (SD AC-031).
    A row unit (verification or applicability) that reaches "needs attention" has no release: a new run
    is the only way through (OQ-US015-3).
16. **Given** a run is active for the fund (a stage is running, or a gate is waiting for the
    specialist), **when** the specialist tries to start another run, **then** it is refused with a plain
    message that names the active run (its ID), and the active run is unchanged. A run that has failed,
    been abandoned or completed is not active (criteria 19 and 20). One run at a time is a rule the
    system enforces, not a convention. (SAD CR-023, PRD A-6, SAD run state model.)
17. **Given** a run's model cost passes US$2, **then** run status shows a warning. **Given** it reaches
    the run's cost cap (set by configuration, US$4 by default), **then** no further model calls are made
    in that run, the valid units are kept, and run status states in plain words that the cost cap was
    reached and nothing further moved forward. The cost counts every call, including retries, re-runs
    and re-verifications. The specialist decides whether to start a new run. (SAD CR-017, SD MC-002;
    the US$2 target itself is judged in US-013 criteria 3 and 6.)
18. *Deferred (DL-22).* **Given** 3 model calls in the same stage have failed on transport or provider errors (after their
    one automatic retry), **then** the stage issues no new calls, calls already in progress finish and
    their valid outputs are kept, and run status shows **one** message, such as "the model service is
    not responding; nothing moved forward", not one message per unit. The message follows the voice rule
    in criterion 8. (SAD Production Shape, circuit breaker; exact wording is for `@ux.designer`.)
19. **Given** a step fails, returns invalid output, or does not finish within its time limit, **then**
    the run moves to **failed**: a plain message names the step, the unit and the reason, and says that
    nothing moved forward. No gate opens for the failed stage, and every decision already recorded stays
    as it was. A failed run is final: it is not resumed or re-run. A step that never returns is treated
    the same way once its time limit passes, so a hang cannot keep a run active for good. Because a
    failed run is not active, the specialist can start a new run (criterion 16). (SAD run state model,
    tests T-RUN-1 and T-RUN-2; decision log DL-22.)
20. **Given** an active run, **when** the specialist abandons it **with a written reason**, **then** the
    run is closed as **abandoned** and the specialist can start a new run. Abandoning without a reason
    is refused. Nothing is undone or deleted: decisions already recorded, rows, verdicts, drafts, the
    audit log and any published calendar stay as they were, and GPs keep seeing the last published
    version. No new model call is started for the run. The audit log records who, when, the reason and
    the stage the run was in. (SAD W-19a, test T-RUN-3.)
21. **Given** a run that is failed, abandoned or completed, **when** the specialist tries to abandon it,
    or a decision is sent for it, **then** the request is refused with a plain message giving the run's
    state. **Given** an abandon request made on an out-of-date run screen, or submitted twice, **then** it
    is refused and only one abandon is recorded (the stale-screen rule, US-004 criterion 18). (SAD test
    T-RUN-4.)

## 4. Scope Notes

- **In Scope for MVP**: one run at a time; re-running only the unit that failed (a document or a row),
  by the specialist, up to 3 times per unit and input; releasing one failed source document to manual
  entry after that limit (decision log DL-18). *Deferred (DL-22): unit re-runs and the release. In the
  MVP a failed step ends the run as failed (criterion 19).*
- **Not included**: releasing a verification or applicability unit, releasing several documents at
  once, or releasing before the re-run limit. A release is never a shortcut.
- **Abandon is not a general cancel**: it closes a run and nothing else. There is no cancel of a model
  call or a step, no undo of a decision, no rollback of a stage and no deletion of a draft (decision
  log DL-22, SAD W-19a).
- **Deferred**: automatic re-runs of a failed step or unit; resuming a run after the application
  restarts. (The SAD allows one automatic retry of a single failed call; the specialist sees only the
  outcome.)
- **Restart (SAD §2)**: *Deferred (DL-22): the restart sweep.* A restart does not resume a run. On start-up, every unit that was still
  running is marked failed and re-runnable, so the recorded decisions and the last safe state survive.
  That is the "comes free" part; a full resume stays deferred.

## 5. Traceability

- **PRD Anchors**: §6 (run status, failures, voice) · OQ-5
- **System description**: NFR-004 · MC-001 · MD-009 · AC-030, AC-031
- **Decision log**: DL-18 (criteria 14–15)
- **SAD controls**: CR-023 (criterion 16) · CR-017 and MC-002 (criterion 17) · Production Shape circuit
  breaker (criterion 18) · run state model, W-19a and tests T-RUN-0 to T-RUN-4 (criteria 19–21)
- **Decision log**: DL-22 (run state and abandon)
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

- **OQ-US015-1**: *Resolved by the SAD (SOQ-2, CR-010).* 3 manual re-runs per unit per input; then
  "needs attention" (criterion 13). *(Approval map OD-7.)*
- **OQ-US015-2**: *Resolved* (operator decision, 2026-11-11, decision log DL-18, SAD SOQ-9). A source
  document that reaches "needs attention" can be released to manual entry with a written reason, one
  document at a time and only after the re-run limit. Then G1 opens and the specialist adds missing
  rows by hand (US-016). See criteria 14–15.
- **OQ-US015-3**: *Resolved for the MVP* (operator decision, 2026-11-12, decision log DL-22 and
  OQ-US015-4). A verification or applicability unit (a row) that fails makes the run **failed**, and a
  new run follows (criterion 19). Releasing such a unit stays future scope (SAD SOQ-10).
- **OQ-US015-4**: *Resolved* (operator decision, 2026-11-12, decision log DL-22, SAD run state model).
  A failed step moves the run to a terminal failed state, so it is no longer active and a new run is
  allowed (criterion 19). Every agent step has a time limit that turns a hang into a failure. A
  specialist action to **abandon** a run, with a written reason and an audit entry, closes an active run
  without undoing anything (criterion 20). This is not a general cancel feature. A run ends when G3 is
  decided, fails, or is abandoned; the architect confirms that a declined G3 also ends the run (SAD
  SA-17).

## Audit

- 2026-11-09 · persona `product-mgr` · action `create-stories` · new story for PRD §6 run status and
  failure recovery (UX review, operator decision); re-running is new scope, estimated under OQ-5;
  decision log DL-02
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · criteria 9–13 and scope notes: failure
  and re-run are per unit (SAD partial-failure rule, CR-003, CR-010); OQ-US015-1 resolved; new
  OQ-US015-2 (extraction dead end); NFR-004 amended, AC-030; operator-approved SAD decisions
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18, SAD SOQ-9) · OQ-US015-2 resolved:
  release of a failed source document to manual entry (criteria 14–15, criterion 10 exception, scope
  notes); new OQ-US015-3 for verifier and judge units (SAD SOQ-10); NFR-004 and AC-031 in the SD
- 2026-11-11 · persona `product-mgr` · action `update` (SAD CR-023, CR-017, Production Shape) · criteria 16–18: a second run is refused and names the active run; run status shows the US$2 warning and the cost-cap stop; one "model service not responding" message instead of one per unit; new OQ-US015-4 (how a stuck run ends, since a new run is refused while one is active)
- 2026-11-11 · persona `product-mgr` · action `update` (SAD §2) · scope note: a restart does not resume a run, but running units are marked failed and re-runnable so decisions survive; full resume stays deferred; no criterion changed
- 2026-11-12 · persona `product-mgr` · action `update` (OQ-US015-4, DL-22) · criterion 16 reworded to the
  run state model; criteria 19–21 (a failed step or timeout ends the run as failed; abandon with a
  reason, audited, nothing undone; refusals on a closed run); scope note that abandon is not a general
  cancel; OQ-US015-3 and OQ-US015-4 resolved; operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · criteria 4–6 (re-run from the last safe state), 11–13 (unit re-run, example, "needs attention"), 14–15 (release) and 18 (circuit breaker) marked deferred, with the restart note; criteria 1–3, 7–10, 16–17 and 19–21 stay; DL-02's re-run is superseded for the MVP
