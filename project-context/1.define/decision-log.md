# Define Decision Log

**Product**: Regulatory Intelligence for fund compliance calendars
**Purpose**: one place to see what was decided in the Define phase, why, and which documents changed as
a result. Each document keeps its own Audit section; this log ties the changes together.

> **How to read an entry.** **Decision** is what was agreed. **Why** is the reason. **Considered** lists
> the alternatives weighed, when there were any. **Changed** lists every document and section
> updated. All decisions are the operator's, made with `@product-mgr`.
>
> Earlier Define decisions (2026-11-06 to 2026-11-08) are recorded in each document's Audit section,
> the approval map (§8, "Resolved in Define") and `context-summary.md`. This log starts with the
> 2026-11-09 reviews.

---

## 2026-11-09 · UX review of the PRD

The operator reviewed the PRD from a user-experience point of view.

### DL-01 · Precautionary verdicts are labelled everywhere they appear

- **Decision**: when the specialist decides an "unsure" verdict as "applies" under P-1, it carries the
  label "precautionary" and its reason, at G2 and in the GP view. GP text must not state or imply that a
  registration or marketing is permitted.
- **Why**: the system description already defined the label (SD P-1), but the PRD dropped it. A GP
  could read a plain "applies" for `OBL-04` as definite, or as permission to market in Spain.
- **Considered**: having the agent assign the label. Rejected: the agent's verdict is "unsure"; only the
  specialist turns it into "applies (precautionary)".
- **Changed**: PRD F5, F8 · US-011 criterion 5 (US-007 criteria 5 and 6 already covered G2).

### DL-02 · Run status, and re-running a failed step

- **Decision**: during a run, the specialist sees which steps are finished and which is running. If a
  step fails, the message names the step and confirms nothing moved forward; recorded gate decisions
  are kept; the specialist can re-run the failed step from the last safe state.
- **Why**: a run can take up to 5 minutes, and the PRD only said "plain messages… last safe state".
  Without a re-run, a failure after G1 would force a new run and repeat all G1 approvals, which works
  against the 30-minute review target (SD MC-003).
- **Considered**: (a) re-run only the failed step; (b) offer only "start a new run". Chose (a). (b)
  looked smaller but would throw away completed review work.
- **Note**: re-running is **new scope**. It goes into the architect's estimate (PRD OQ-5). Retry limits
  stay open (approval map OD-7, US-015 OQ-US015-1).
- **Changed**: PRD §6 (replaces the one-line failure requirement), OQ-5 · new US-015.
- **Superseded for the MVP (DL-22, 2026-11-12):** re-running a failed step is future scope. In the thin
  slice a failed step ends the run as failed and the specialist starts a new run, or abandons an active
  run with a written reason (US-015 criteria 19–21). The rest of this decision stands.

### DL-03 · Each verifier flag states its type and evidence

- **Decision**: a quote-check flag shows the text that does not match; an internal flag shows the field
  that disagrees with the row's own quote; a cross-source flag shows the conflicting paragraph ID and
  quote.
- **Why**: flag content affects trust and false alarms (PRD AB-3), and it shapes what the verifier must
  output.
- **Considered**: adding "the verifier did not change this row" to every flag. Rejected: SD MN-004
  already guarantees it, and repeating it on each flag adds noise.
- **Changed**: PRD F2 · US-002 criterion 7 · US-003 criterion 9.

### DL-04 · Fund facts can be viewed at G2, read-only

- **Decision**: at G2, each fund fact ID cited in a verdict can be opened to show what it says.
- **Why**: verdicts cite fact IDs, but the specialist could not check what a fact said before confirming.
- **Changed**: PRD F5 · US-007 criterion 1.

### DL-05 · Voice for agent and system text

- **Decision**: plain British English; facts and uncertainty stated without reassurance or alarm;
  sources cited; no advice. GP-facing text is written for a non-lawyer and stays neutral. Checked in a
  copy review before the demo; detailed guidance belongs to `@ux.designer`.
- **Why**: the firm is fictional, so the voice describes how text should read, not brand values.
- **Considered**: writing it as a testable acceptance criterion. Rejected: tone can't be tested
  automatically, so it is checked by review instead.
- **Changed**: PRD §6 · stories README (system-wide rules) · US-015 criterion 8.

### DL-06 · Persona claims and the expected buyer are labelled unvalidated

- **Decision**: "GPs are often less familiar with Luxembourg rules", "filing parties do most of the
  filings" and "GPs are the expected future buyer" are labelled as unvalidated expectations.
- **Why**: they read as fact, but no users were interviewed.
- **Changed**: PRD §1, §2 users, A-1, A-7 · SD §1 users, new A-10, §10.1, OQ-10.

## 2026-11-09 · Business review of the PRD

The operator reviewed the PRD from a business point of view.

### DL-07 · No employer material in the evidence

- **Decision**: the evidence is an illustrative scenario for a fictional fund-services firm (new source
  SRC-ILLUS) plus public regulation. The citations to the operator's internal working documents
  (SRC-INT) are removed.
- **Why**: the repository is public and part of a portfolio. Even with names removed, specific figures
  and document details from an employer are confidential and can identify the source. The real-name
  scan catches names, not details.
- **Considered**: keeping the original mismatch examples with names removed. Rejected for the reason
  above. Replaced with the two conflicts already planted in the mock data (`C-1`, `C-2`), so every
  example traces to the answer key.
- **Trade-off**: the MRD no longer claims the problem was observed. It is openly illustrative, which
  matches the existing statement that no user research was done.
- **Changed**: MRD header note, §1, §2 table, §3, §4 ("earlier internal work" removed), §5, Sources,
  A-1, A-2 · PRD §1 Impact, §2 evidence note, §5 Security (new row), A-7, Sources · SD A-10,
  Assumptions note · `docs/learning-notes.md` · stories README (system-wide rules).
- **Still open**: the earlier wording remains in the public git history. Whether to make the repository
  private or rewrite the history is a separate decision, not yet taken.

### DL-08 · The MVP must fit the six-week timebox

- **Decision**: the MVP must fit the six-week capstone timebox. The architect estimates the Must scope
  against it, and a cut line between the core demo path and hardening is agreed before Build.
- **Revised 2026-11-09**: first recorded as a budget of about 40–50 operator hours (an estimate from
  8–10 hours a week). The operator replaced it with the six-week timebox the same day, so the estimate
  is framed in weeks, as in the brief.
- **Why**: the Must list includes the recovery paths (SD FR-022 to FR-025), the full gate logic and now
  the failed-step re-run (DL-02). Six-week fit had not been shown, and the cut line proposed earlier was
  not adopted.
- **Note**: the two extensibility walkthroughs are paper exercises in the SAD, not Build work.
- **Changed**: PRD §8 risks (new row), OQ-5 · context summary · project README.

### DL-09 · Two unrecorded constraints become open questions

- **Decision**: the capstone programme's submission requirements and the reused prototype front end are
  recorded as open questions, without inventing detail.
- **Why**: neither was in any Define document. If the prototype was built for or at an employer, it is
  treated like employer documents (DL-07) and not reused.
- **Changed**: PRD OQ-10, OQ-11.

### DL-10 · A missed target is reported, not hidden

- **Decision**: a target passes only at its exact value. A miss is stated in the evaluation report;
  gates still keep unapproved output from GPs.
- **Why**: the targets (6 of 6 rows, 22 of 22 entries) are exact on a small set, so the plan for a miss
  needs to be stated in advance.
- **Changed**: PRD §7 · US-013 criterion 6.

### DL-11 · No ROI claim; a labelled effort estimate for comparison

- **Decision**: no ROI or time saving is claimed. The operator provides a labelled estimate of manual
  effort for the five demo obligations, shown next to the measured review time. A measured baseline is
  needed before any value claim.
- **Why**: without a baseline, the 30-minute review target has nothing to compare against.
- **Changed**: PRD §7 (new row), OQ-12 · US-013 criterion 7.

### DL-12 · "Not legal advice" becomes a Must, combined with the date-conventions note

- **Decision**: SD FR-020 rises from Should to Must. The GP view shows **one** calendar-level note: not
  legal advice, and the date conventions have not yet been checked against the legal texts (SD A-7).
  The specialist sees the date-conventions note at G3; it does not block publishing.
- **Why**: SD MN-009 already required the note, so leaving FR-020 as a Should was inconsistent.
- **Considered**: a label on every calendar entry. Rejected: it would make the GP distrust correct dates,
  and per-entry date marks are specialist-only (US-011 Assumptions, operator-confirmed).
- **Changed**: SD FR-020 · PRD F7, F8, P1 table (row removed) · US-010 criterion 11 · US-011 criterion
  11 · stories README.

## 2026-11-09 · Define handover

### DL-13 · Handover to the architect approved

- **Decision**: the operator approved `context-summary.md`. `@system.arch` may start the SAD.
- **Why**: both reviews (DL-01 to DL-12) are applied and merged, and none of the items under "Still
  open" in the context summary blocks the architecture.
- **Carried forward**: the open questions in the context summary (including OQ-10 to OQ-12 for the
  operator) and the separate decision on the public git history (DL-07). Any later change to a Define
  document is recorded in this log.
- **Changed**: `context-summary.md` status banner · `approval-map.md` §1 · project README status and
  next steps.

### Reviewed, no change needed

- **Buyer stated too firmly** (PRD A-1): already handled by DL-06.
- **Four-eyes review**: already recorded as PRD OQ-1; timing still undecided.

## 2026-11-11 · Architecture (SAD) decisions

Decisions taken by the operator while `@system.arch` filled the SAD decision headings. Each changes
or adds to a Define document, so it is logged here as DL-13 requires.

### DL-14 · The quote check is deterministic code; the verifier keeps the conflict checks

- **Decision**: the quote check (does the quote appear word for word in the cited paragraph?) is
  ordinary code and is the authority that blocks G1. The verifier agent does the internal and
  cross-source conflict checks, which need judgement. Normalisation rule QN-1: trim, collapse
  whitespace runs (including line breaks) to one space, compare case-sensitively, normalise nothing
  else.
- **Why**: a word-for-word match is a string comparison, not an opinion, and MN-006 ("a failed quote
  check cannot be approved") must not depend on a model saying "pass". Closes approval map OD-8.
- **Considered**: a model quote check with code as a backstop. Rejected: two answers to one factual
  question, and the model one adds nothing.
- **Changed**: SAD W-04, QN-1, tests T-W04-1 to T-W04-6 · SD vocabulary, MD-003, FR-003 (operator
  edit) · approval map A4, §7, §8, Open Questions (operator edit) · US-002 criterion 8, scope note,
  assumption.

### DL-15 · Manual row creation is in MVP scope, smallest form

- **Decision**: at G1 the specialist can add a missed row by opening the edit form on an empty row.
  The row is marked **human-created** and then takes the normal path: code quote check (QN-1),
  verifier conflict checks, and its own G1 decision. **No "re-extract" button.** In the evaluation
  report, human-created rows are counted separately from model-extracted rows.
- **Why**: the SAD adds a G1 coverage view (W-03b) that shows paragraphs no row cites, so a missed
  row, the costliest error under P-1, becomes visible at run time. Without a way to add a row, the
  only fix would be re-running extraction and hoping. The smallest form reuses the edit path (W-08)
  and adds no model path for the costliest error.
- **Considered**: (a) a model "re-extract this paragraph" action: rejected, it puts a probabilistic
  step on the path for the error that matters most; (b) out of scope for the MVP: rejected, the
  coverage view would then show a problem the specialist cannot fix.
- **Scope note**: new Must scope. Goes into the architect's estimate (PRD OQ-5, SAD SOQ-1).
- **Changed**: SAD W-07a (Work Ownership), SOQ-7 resolved, Control Register CR-020 · **still to do by
  `@product-mgr`**: a system-description requirement (proposed FR-027) and a story (proposed US-016);
  US-013 criterion for counting human-created rows separately. **Done 2026-11-11 by `@product-mgr`:**
  SD FR-027 and AC-027, NFR-010, story US-016, US-013 criterion 8, US-005 scope note.

### DL-16 · Possible duplicate rows: warn per group, confirm once at G1 completion

- **Decision**: duplicate groups (SAD W-03a) stay non-blocking per row. Each group shows a plain
  warning at G1. If a group still has two or more approved rows when the specialist completes G1,
  the server requires one confirmation with a written reason, logged in the audit trail.
- **Why**: two rows for one obligation can be legitimate (for example two authorities), so a hard
  block would be wrong; an accidental double approval would produce double calendar entries, so it
  must be impossible to miss. One confirmation at completion catches the accident without adding a
  decision per row.
- **Considered**: (a) hard block on any multi-approved group: rejected, too strict; (b) nothing beyond
  the per-row decisions: rejected, an accident would be silent until the calendar.
- **Changed**: SAD SA-9, CR-022, tests T-W03a-1 and T-W03a-2 · **still to do by `@product-mgr`**:
  US-004 criterion for the completion confirmation (with US-016 / FR-027 from DL-15). **Done
  2026-11-11 by `@product-mgr`:** SD FR-029 and AC-028, US-004 criteria 14–16.

### DL-17 · Runtime shape: a CrewAI Flow per stage, the backend owns the gates

- **Decision**: the backend is the single owner of gate state. A short CrewAI Flow runs each stage
  (A extract and verify, B judge, C generate), starts only when the backend triggers it, and ends at
  its gate. Flows never decide or remember gate status. Model steps keep a runtime-neutral function
  interface inside the Flows.
- **Why**: a Flow suits "run these steps in order and hand back results"; a human gate is persisted
  state that must survive restarts and refuse bypass, which belongs in one place. Keeping the
  interfaces neutral keeps model swaps and model-free tests cheap (SD NFR-011).
- **Considered**: plain function calls with no Flow (the SAD's earlier provisional choice). Replaced:
  the operator prefers the runtime's own orchestration within a stage, with the same gate ownership.
- **Changed**: SAD §2, W-09, CR-001, Model and Context Strategy (entry point). No Define document
  changes.
- **Wording change, 2026-11-12 (operator, with DL-35):** *Runtime shape: three CrewAI agents run by
  plain stage functions; the backend owns the gates.* The backend is still the single owner of gate
  state. Each stage (A extract and verify, B judge, C generate) is now run by a **plain backend
  function**, with **no CrewAI Flow wrapper**. The extractor, the verifier and the applicability
  judge **remain CrewAI agents**, each run as a one-agent, one-task crew behind its runtime-neutral
  function interface, so the system stays visibly multi-agent. A stage function starts only when
  the backend triggers it, ends at its gate, and never decides or remembers gate status. The Flow
  wrapper is future scope (SAD F-11). *Why:* with five focused days (DL-32), the wrapper adds
  framework surface to learn and debug without changing who owns the gates; this returns to the
  "plain function calls" option listed under Considered, while keeping the agents in CrewAI.

### DL-18 · A document that cannot be extracted can be released to manual entry

- **Decision**: when one extraction unit (a source document) has failed the re-run limit, the
  specialist may release that one document to manual entry with a written reason. Every other unit
  must still be valid before G1 opens. The specialist then adds any missing rows by hand: they are
  labelled manual, need a source paragraph and quote, and go through the code quote check and the
  verifier conflict checks like any row. The release is audited and counted as an **extraction
  failure** in the evaluation report.
- **Why**: without it, the SAD named manual row creation as the way out, but manual rows are added at
  G1, which a failed unit keeps closed. One document the model cannot extract would block the run for
  good (raised by `@product-mgr` as OQ-US015-2, SAD SOQ-9).
- **Considered**: (B) a new run as the only way out: rejected, a document that fails systematically
  would block the demo. Releasing several documents at once, or before the re-run limit: rejected,
  per document and only after the limit, so a release is never a shortcut.
- **Not decided here**: the same dead end for verifier and judge units (SAD SOQ-10), decided
  separately. Whether PRD F3 should mention manual row creation and this release (OQ-US016-2) is
  still open for the operator.
- **Changed**: SAD CR-010, W-19, SOQ-9, SOQ-10, tests T-REL-1 and T-REL-2 · **still to do by
  `@product-mgr`**: close OQ-US015-2; reflect the release in US-015 and US-016 (and in SD NFR-004 or
  FR-027 if a requirement line is needed). **Done 2026-11-11 by `@product-mgr`:** OQ-US015-2 closed;
  US-015 criteria 14–15 and scope notes; US-016 criterion 11; SD NFR-004 and AC-031. New OQ-US015-3
  records the verifier and judge dead end (SAD SOQ-10). The evaluation-report count of the release as
  an extraction failure is stated in AC-031 and US-015 criterion 15 and, since the follow-up below, as
  US-013 criterion 9. **OQ-US016-2 resolved (operator, 2026-11-11):** PRD F3 lists manual row
  creation for both a missed row at G1 (DL-15) and a released document (this entry).

### DL-19 · Business-day rules are never guessed

- **Decision**: if a source paragraph does not state a business-day rule, the row's rule stays
  "not confirmed" until the specialist sets one at G1. Code never infers or defaults one. This
  decides PRD OQ-7 for the demo: `OBL-04` (CNMV) and `OBL-05` (Luxembourg Business Registers) stay
  "not confirmed", so their weekend dates keep the earlier day and are marked (`D-6`).
- **Why**: this is how the extraction spec already treats a silent source (SD FR-002), and P-1:
  filing early is safe, filing late is not. A guessed rule would be an interpretation nobody approved.
- **Considered**: looking up a rule from the authority (for example "Luxembourg registers roll
  forward"): rejected, that is legal interpretation hidden in code.
- **Effect on expected results**: none. The answer key (KEY §5) already has both rows as "not
  confirmed", and the 22 expected entries do not change.
- **Changed**: SAD W-13, SOQ-6 · **still to do by `@product-mgr`**: mark PRD OQ-7, SD OQ-2, KEY
  OQ-D1 and the story questions (US-008 OQ-US008-1 for CNMV, US-009 OQ-US009-1) resolved. The AED
  subscription-tax part of PRD OQ-7 (SD OQ-4, KEY OQ-D3) is a separate question and is not decided
  here (confirmed by the operator; see DL-20). **Done 2026-11-11 by `@product-mgr`:** SD OQ-2 and
  KEY OQ-D1 resolved; US-009 OQ-US009-1 resolved. PRD OQ-7 and US-008 OQ-US008-1 are marked resolved
  for `OBL-04` and `OBL-05` only; their AED subscription-tax part stays open.

### DL-20 · An open convention is marked, never silently resolved

- **Decision**: the AED subscription-tax question (does the stated "tax deadlines do not roll"
  convention cover `OBL-02`? PRD OQ-7, SD OQ-4, KEY OQ-D3) **stays open**. It is for the specialist to
  decide, or to ask a tax specialist; the code must not assume an answer. Until it is decided, the
  date code applies whatever rule the specialist set at G1, has no built-in default for `OBL-02`, and
  marks every `OBL-02` entry as depending on OQ-7. The mark is shown at G1 (when setting the rule) and
  at G3 (before publishing).
- **Why**: DL-19 covers rules the sources do not state at all. This is different: the convention is
  stated, and the open point is whether it applies. Picking either behaviour in code would be an
  interpretation nobody approved; making the dependency visible keeps the decision with a person.
- **Effect on expected results**: none. In 2027 none of `OBL-02`'s four due dates (20 January, 20
  April, 20 July, 20 October) falls on a weekend or a mock holiday, so both answers give the same
  dates. The 22 expected entries do not change.
- **Considered**: setting `OBL-02` to "not confirmed" until decided: not chosen, it would change the
  answer key's business-day table and US-008 criterion 3 for no difference in dates. Showing the mark
  to GPs: not chosen, per-entry rule marks are specialist-only (US-011 assumptions); the calendar-level
  "conventions not yet checked" note (FR-020) already covers GPs.
- **Changed**: SAD W-13, CR-027, tests T-W13-1 and T-W13-2, SOQ-6 · **still to do by `@product-mgr`**:
  a G3 criterion in US-010 (the OQ-7 mark is shown on `OBL-02` entries and does not block publishing)
  and a G1 note in US-004; keep PRD OQ-7's tax part, SD OQ-4 and KEY OQ-D3 open. **Done 2026-11-11 by
  `@product-mgr`:** US-010 criterion 12, US-004 G1 scope note; PRD OQ-7 (tax part), SD OQ-4 and KEY OQ-D3
  kept open with a pointer to this entry. Later the same day: the G1 note became US-004 criterion 17, and AC-032 plus a US-011
  assumption cover the `OBL-02` mark.

### DL-21 · Five CrewAI adapter deviations and one interpretation are accepted

- **Decision**: the operator reviewed and accepted D1–D5 as justified deviations and D6 as a recorded
  interpretation of `.cursor/rules/adapter-crewai.mdc`: D1 `max_retry_limit: 1`; D2 no `Task.context`
  chaining; D3 `expected_output` as a typed schema; D4 no per-task output path; D5
  `guardrail_max_retries: 0` (a library default, not an adapter rule); D6 the backend gates count as
  the human review gate. Two conditions: **D4** makes the trace export a required step of every
  evaluation run, with test T-D4-1 failing a run whose export is missing; **D5** requires the week-1
  spike to record first-pass success per role with no re-ask.
- **Why**: each adapter rule, followed literally, would undo an earlier decision: automatic retries
  and guardrail re-asks rebuild the rejected self-correcting loop and hide failures (Pattern
  Decision, Production Shape); `Task.context` would show the verifier the extractor's output (W-05);
  output files would be a second store outside the idempotency and append-only rules (CR-010,
  CR-013).
- **Process note**: the deviations were first written into the SAD before review, then marked as
  pending and reviewed one by one, with the verbatim rule, its line, the conflicting decisions, the
  justification and the risk. Only then were they recorded.
- **Changed**: SAD §2 (adapter table, D1–D6 summary and detail), Production Shape (spike measures
  first-pass success), tests T-D4-1. No Define requirement changes.

### DL-22 · The MVP is the thin slice; the rest moves to future scope

- **Decision**: the MVP is **one complete happy path**: mock paragraphs in → extractor → code quote
  check → verifier → G1 (approve, approve over a flag with a reason, reject with a reason; coverage
  view) → applicability → G2 (confirm, override with a reason, decide "unsure" as precautionary) →
  code-generated calendar → G3 (publish, or decline with a reason) → a basic GP view with the
  calendar-level note → an audit log of every decision → the evaluation report against the answer
  key, with its trace export. The hybrid runtime is unchanged (DL-17).
- **Moved to future scope** (written down, designed in the SAD, not deleted, not built): edit and
  re-verify (FR-006 edit part, FR-007); reopen a rejected row (FR-023); reopen a verdict (FR-024); the
  GP review notice (FR-025); re-running a failed step (US-015 criteria 4–6, **superseding DL-02 for
  the MVP**); manual row creation (FR-027, DL-15); duplicate groups and the completion confirmation
  (FR-029, DL-16); releasing a failed document (DL-18); the verifier and judge dead-end handling (SAD
  SOQ-10); the impact report (F10, unchanged as stretch); the extra CI checks (contract drift,
  release-rule PR check); circuit breaker and restart sweep.
- **Why**: the six-week timebox (DL-08). The SAD estimated all Must scope at about 52 focused days and
  the slice at about 42.5 (32–60). The slice keeps every control that stops an unapproved or wrong
  output reaching a GP, and the evaluation that proves the output; what moves out is used only after a
  mistake or a fault.
- **Considered**: (a) the architect's first proposal: a core of about 46 days that also kept manual row
  creation, edit and re-verify, duplicate groups, and re-running a failed step, with seven recovery and
  hardening items below the line (never committed; this entry is its record). The operator chose the
  narrower slice. (b) Dropping the evaluation report: rejected, it is the proof the system works (SD
  §1, PRD §7). (c) Keeping re-run of a failed step: not chosen; a failed step means a new run.
- **Consequences for the demo**: no edits at G1 (the demo decisions need none); nothing changes after
  G3 except a new run and a new publish; a failed step, a stubborn document or a missed row means a
  new run.
- **Capacity** (SAD SOQ-12, answered the same day): the operator commits the time the slice needs,
  without a number. It is a commitment, not a measured fit; the re-estimate after Build week 1 is the
  check (Tier 2 cuts go to the operator if the first packages take more than 1.3× their estimate).
- **Update 2026-11-12 (operator, answering OQ-US015-4): a failed step ends the run, and a run can be
  abandoned.** The consequence above ("a failed step ... means a new run") needed a way for a new run to
  start, because CR-023 refuses one while a run is active. Decided: (1) a failed step moves the run to a
  terminal `FAILED` state, so it is no longer active; (2) every agent step has a time limit that turns a
  hang into a failed unit and so a `FAILED` run; (3) a specialist **abandon run** action, with a written
  reason and an audit entry, closes an active run without undoing anything. It is **not a general cancel
  feature**: no cancel of a call or step, no undo, no rollback, no deleted drafts. It also covers a run
  left active by a crash, because the restart sweep stays future scope. **Estimate:** one new package,
  WP-12a, **2 focused days likely (1.5–3)**, so the slice moves from about 42.5 (32–60) to about
  **44.5 (33.5–63)**, and the fit table moves by 2. That is the product manager's figure for the
  architect to confirm at the week-1 re-estimate. Recorded in the SAD (Run state model, W-19a, CR-023,
  tests T-RUN-0 to T-RUN-4, SA-18) and in US-015 criteria 19–21.
- **Update 2026-11-12 (operator, second answer set).** (1) A G3 decline needs a written reason, is audited,
  and ends the run as a terminal `DECLINED` state; correcting means a new run. The next-step choices after
  a decline (back to G1 or G2) and reopen stay future scope. (2) SA-18 is **confirmed** and reworded:
  a run is complete once G3 is decided; publishing gives `COMPLETED`, a decline gives `DECLINED`.
  (3) The WP-12a estimate is **confirmed** at 2 focused days (1.5–3). (4) OQ-US001-2 is accepted as a
  known MVP limitation: there is no "no obligation" mark, the coverage view shows the paragraph as
  uncovered (a warning), and the mark is future scope. SD AC-033 to AC-036 now cover the failed step, the
  timeout, abandon and a new run after a closed run; the PRD (F8) lists the pre-publication message.
- **Changed**: SAD "Six-week estimate and agreed scope", scope keys in Work Ownership and the Control
  Register, feasibility note, SOQ-1, implementation guidance · **still to do by `@product-mgr`**: mark
  the future-scope requirements, acceptance criteria and story criteria as deferred (starting list:
  FR-006 edit part, FR-007, FR-023 to FR-025, FR-027, FR-029, AC-005, AC-022 to AC-024, AC-027,
  AC-028, AC-031, US-005, US-016, US-015 criteria 4–6 and the release criteria, US-004 reopen and
  group-confirmation criteria, US-007 reopen criteria, US-011 review-notice criteria, US-013 criteria
  8–9); record PRD OQ-5 as decided (scope) with capacity still open; note that DL-02's re-run is
  superseded for the MVP. **Done 2026-11-12 by `@product-mgr`:** the future-scope items are marked
  *Deferred (DL-22)* in the SD (FR/AC/NFR-004, §9 list), the stories, the PRD (F3, F5, F8, §6, OQ-5 decided
  on scope) and the story README ("Scope status (DL-22)"); DL-02 carries a superseded note. Beyond the
  starting list, these were also marked: FR-005 and FR-006 edit parts, AC-030's re-run part, US-001
  criterion 9, and US-015 criteria 11–13 and 18 and the restart note. Kept in the MVP: US-015 criteria 9
  and 10 (a failed unit is named, the gate stays closed).

### DL-23 · Evaluation: three passing runs, and names graded by the specialist

- **Decision**: (1) the model-dependent evaluation criteria (SAD §9, EC-001 to EC-007, EC-010, EC-012,
  EC-021) must pass on **3 of 3 consecutive evaluation runs on the same commit** before a merge that
  changes a prompt, model or schema, and before the demo. (2) The extracted obligation **name** is
  graded by the operator's judgement as specialist ("same obligation" or not, recorded per row in the
  report); the fields that drive dates and routing are graded by exact match.
- **Why**: (1) the agents are probabilistic even at temperature 0, so one passing run can be luck;
  three runs cost under US$6 and about 15 minutes. (2) Name wording legitimately varies; a person
  reading six names is cheaper and more trustworthy than adding a model as grader.
- **Considered**: (1) one run (cheapest, but hides intermittent failure); five runs (stronger, five
  times the cost per release). (2) An LLM judge (automatic, but a probabilistic grader with its own
  cost and rubric); not grading the name at all.
- **Changed**: SAD §9 (EC-R1, EC-002), §5 release rule, §10 demo criterion 2 · **still to do by
  `@product-mgr`**: mark OQ-US001-1 and OQ-US013-1 resolved (EC-002); add to US-013 that a pass needs
  three consecutive runs on one commit, and that names are graded by the specialist. **Done 2026-11-12
  by `@product-mgr`** (branch `define-defer-future-scope`, not yet merged): OQ-US001-1 and OQ-US013-1
  resolved; US-013 criterion 10 (3 of 3 consecutive runs on one commit) and criterion 11 (names graded
  by the specialist, date and routing fields by exact match); US-001 assumption points to criterion 11.
- **Superseded in part, 2026-11-12, by DL-34:** part (1) is no longer a gate. The three runs are still
  made and a pass still means 3 of 3, but a miss is reported and does not block a merge or the demo.
  Part (2), names graded by the specialist, stands.

### DL-24 · Development model spend is capped at US$50 until 13 December 2026

- **Decision**: a hard cap of **US$50** on model usage for development (the week-1 spike, prompt
  tuning, evaluation runs and any other Build calls) until **13 December 2026**, enforced as a
  spending limit **in the model provider's account**. A soft checkpoint at **US$25 (50%)**: stop
  model calls and review usage by activity (spike, tuning, evaluation runs) before continuing. Spend
  is logged per evaluation run, with an activity label and a running total (SAD EC-R6).
- **Why**: the SAD separates the per-run limit (MC-002, US$2) from development spend, which had no
  limit (SOQ-13). Planning basis: about 15–20 evaluation runs at under US$2 each (about US$30–40),
  plus the spike and a day of tuning (about US$10); the mock inputs are small. The checkpoint shows
  early if a cost assumption is wrong.
- **Considered**: no cap, tracking only (the SAD's earlier default); setting the cap to the value of
  any course credits, so nothing is paid out of pocket: kept as the way to raise the cap, by a
  recorded decision, if the credits cover more.
- **Note**: the cap lives in the provider account, so it is an operator-owned control; the
  application does not enforce it, and the SAD does not claim it does. A different model for one role
  (for example the applicability judge) would be a release under the swap rule, with its own
  evaluation; it is not assumed.
- **Changed**: SAD §7 (development spend cap), §9 EC-R6, SOQ-13 resolved. No Define requirement
  changes.
- **Superseded 2026-11-12 by DL-36.** This entry is kept as the record of the earlier decision; it
  is not deleted. DL-36 carries forward the US$50 ceiling and the 13 December 2026 date, and
  replaces the US$25 checkpoint and the planning basis of 15 to 20 evaluation runs.

### DL-25 · OpenAI on prepaid credits, with a model chosen per role

- **Decision**: the application's model provider is the **OpenAI API**, paid with **prepaid
  credits**: **US$25 loaded to start**, **US$50 ceiling**. Models per role: a **cheaper default**
  model for the extractor; a **reasoning** model for the applicability judge; the verifier on a model
  **different from the extractor's** (family still to choose, SAD SOQ-15). The current model IDs are
  confirmed against the provider's list **before the week-1 spike** and recorded here. The spike
  records first-pass success, cost, time and run-to-run consistency per role, against the US$50 cap.
  **Claude Code is the build tool only**, not a runtime provider.
- **Why**: one provider keeps a single live external service (SD MN-002, PRD A-3 unchanged). A cheaper
  extractor is backed by the code quote check and the verifier. A different verifier model reduces
  shared blind spots between maker and checker (SD MD-003). The judge does the judgement-heavy step
  where a wrong "does not apply" is the costliest error (P-1). Prepaid credits make the US$25
  checkpoint (DL-24) a hard stop in practice: topping up to US$50 is a deliberate step after review.
- **Considered**: one balanced model for all roles (the SAD's earlier default); a second provider for
  the verifier (rejected for now: it would add a second live service and need PRD A-3 changed).
- **Note**: the operator's wording "extraction and generation" is recorded as the extractor only;
  no other step uses a model (calendar generation is code, MN-005; GP text is confirmed at G2, W-17).
  Reasoning models may not accept a temperature setting, so the judge's stability across runs is
  measured by the spike and tested by EC-R1.
- **Changed**: SAD Model and Context Strategy, §2 sampling, §4 and Production Shape variables
  (`OPENAI_API_KEY`, `LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY`, `LLM_MODEL_JUDGE`), §5 release rule,
  CR-021, §7 enforcement, SOQ-14 resolved, new SOQ-15. No Define requirement changes.
- **Changed 2026-11-12 by DL-36:** the first load of prepaid credits is **US$15**, not US$25. The
  provider, the per-role models and the US$50 ceiling stand.

### DL-26 · Verifier: a mid-tier model by default, with a measured switch rule

- **Decision**: the verifier defaults to a **cheaper mid-tier model, different from both the
  extractor's and the judge's**. In the week-1 spike, **both** candidates (the mid-tier model and the
  judge's reasoning model) run on the planted conflicts `C-1`, `C-2` and `I-1`, at least 5 times each.
  **If the mid-tier model misses any planted conflict in any run, the verifier switches to the
  reasoning model.** Cost per full run is recorded for both options.
- **Why**: the verifier runs once per row, so its model drives a large share of run cost; a mid-tier
  model is cheaper, and a third model keeps maker and checker independent. The switch rule is tied
  to the thing the verifier exists for (catching planted conflicts, SD MP-003), so cost is only saved
  where it does not cost recall.
- **Interpretation recorded**: "misses any planted conflict" is read as **any miss in any spike run**,
  matching the no-best-of rule (SAD EC-R1a). False alarms on correct rows are measured and reported,
  but are not part of the switch rule; if the mid-tier model catches every conflict but raises false
  alarms (EC-006), that is brought to the operator as a separate decision.
- **Changed**: SAD Model and Context Strategy (verifier row), Production Shape (week-1 spike),
  SOQ-15 resolved. The chosen verifier model and its ID are added to this entry after the spike.

### DL-27 · Before the first publication, GPs see a read-only "being prepared" message

- **Decision**: answers PRD OQ-6 (SD OQ-1, US-011 OQ-US011-1): **yes**. Before the first G3
  publication, the GP view shows a read-only empty state with this message:
  *"Your obligations calendar is being prepared and checked by a specialist. Nothing has been
  published yet."* No notifications are sent. It is in the thin slice.
- **Why**: a blank calendar could be read as "this fund has no obligations", which is the costliest
  misreading (P-1). The message states only that work is in progress; it shows no entry, count,
  status or draft content, so it stays within SD MN-007.
- **Not the review notice**: the post-publication review notice (SD FR-025, shown when a change
  questions a published calendar) stays **future scope** (DL-22). The two are separate: this one is
  shown only before anything has been published.
- **Wording**: the operator's text is the agreed message. It goes through the copy review (DL-05)
  like all GP text; any change to it is recorded here.
- **Changed**: SAD W-16, §3 `/calendar`, CR-012, EC-014 · **still to do by `@product-mgr`**: mark
  PRD OQ-6, SD OQ-1 and US-011 OQ-US011-1 resolved; update US-011 criterion 7 (the empty state shows
  this message, read-only, no notifications) and SD AC-013 if its wording needs it. **Done 2026-11-12
  by `@product-mgr`** (branch `define-gp-pre-publication-message`, not yet merged): PRD OQ-6, SD OQ-1 and
  OQ-US011-1 resolved; US-011 criterion 7 and SD AC-013 now name the message; US-010 criterion 6 points
  to it.


### DL-28 · After a backend restart, the specialist abandons the interrupted run

> **Superseded 2026-11-12 by DL-29** (operator decision): the start-up rule is now in the slice, and
> abandon works only while a run waits at a gate. Kept for the record.

- **Decision**: accepted as a **known MVP limitation**. If the backend restarts while a stage is
  running, no step timer fires and the run stays `ACTIVE`; the specialist ends it with **abandon and a
  written reason** (SAD DM-18, W-19a, SD AC-035), and then starts a new run. The start-up rule that
  would mark such a run `FAILED` automatically ("service restarted") moves to **future scope**.
- **Why**: abandon already exists in the slice and undoes nothing; a restart is rare in a local demo;
  the start-up rule is extra Build work (about 0.25 day) for a case abandon already covers.
- **Changed**: SAD SOQ-17 resolved, future-scope table (robustness row), Delegation Map future-scope
  list · **for `@product-mgr`**: if the known-limitations list in US-015 or the PRD should name it.


### DL-29 · Abandon only at a gate; a run interrupted mid-stage fails automatically

- **Decision** (supersedes DL-28): (1) the specialist can abandon an `ACTIVE` run, with a written
  reason, **only while it waits at G1, G2 or G3**; abandon is refused while a stage is running.
  (2) **Start-up rule:** when the backend starts, any `ACTIVE` run whose stage was running becomes
  `FAILED` with the reason "service restarted", logged as a system event; a new run can then start.
  (3) Architect's addition, needed so that (1) leaves no dead end: the backend enforces a **stage
  time limit**; a stage that exceeds it ends and the run becomes `FAILED`.
- **Why**: a running stage already ends by itself (step timeouts, now a stage limit), so abandoning
  mid-stage is never needed, and it would leave model calls running and spending for output nobody
  uses. The start-up rule closes the one case where a stage could otherwise stay "running" forever.
- **Considered**: keeping DL-28 (abandon any active run; abandon by hand after a restart): simpler,
  but it allows orphan model calls and depends on someone noticing an interrupted run.
- **Cost**: about 0.25 focused day (SAD WP-12b).
- **Changed**: SAD Run state model (rules 6 to 8), W-19a, DM-17, DM-18, abandon endpoint, error
  codes (`RUN_STAGE_RUNNING`), future-scope rows, SOQ-17 · **still to do by `@product-mgr`**: SD
  AC-035 (abandon only at a gate), the failed-run ACs for the stage limit and the start-up rule,
  US-015 criterion 20 and the known-limitations note from DL-28. **Done 2026-11-12 by
  `@product-mgr`** (branch `sad-dl29-31`): SD AC-034 and AC-035, NFR-010 and §9; US-015 criteria 19–20
  and the restart scope note; approval map A15, A25, H13, H13a.

### DL-30 · G3 requires an acknowledgement of rejected rows and uncited paragraphs

- **Decision**: before publishing, the specialist sees the rows rejected at G1 and the paragraphs no
  non-rejected row cites, and gives **one explicit acknowledgement** as part of the publish request.
  It is never preselected; publish is refused without it, or if either list changed after it was
  shown; it is logged with the lists acknowledged. It does not apply to a decline.
- **Why**: P-1. A missed or wrongly rejected row is the costliest error, and the last point to catch
  it before GPs rely on the calendar is G3.
- **Note**: in the demo the three `SRC-PRACT` summaries are always uncited, so the acknowledgement
  appears on every publish; that is intended.
- **Cost**: about 0.5 focused day (SAD WP-12c).
- **Changed**: SAD W-15, DM-12, §3 G3 route, §4 G3 and publish endpoints (`ACK_REQUIRED`), new
  CR-028, EC-013 · **still to do by `@product-mgr`**: a requirement and acceptance criterion for the
  acknowledgement, and a US-010 criterion; approval map H10 and Card G3 (as part of SOQ-16). **Done
  2026-11-12 by `@product-mgr`** (branch `sad-dl29-31`): SD FR-030 and AC-037; US-010 criterion 14;
  approval map H10, H11a and Card G3.

### DL-31 · A labelled demo switch adds one planted row for the demo run

*Partly superseded by DL-44 (2026-11-12): the demo row's Approve button stays visible and the server refuses it; it no longer "offers reject only".*

- **Decision**: a run-level setting, **off by default**, that adds a seventh row: a real quote,
  verbatim in its paragraph, that does not support its rule, so the code quote check passes and the
  specialist rejects it at G1. The extractor never produces it; code adds it from a fixed demo
  fixture. It is on for the demo run and off for evaluation runs. It adds a row but never approves
  anything; the row is marked "demo" wherever it appears; turning the switch on is recorded in the
  audit log. The mock sign-in page stays as it is for roles; no role switcher.
- **Design** (SAD CR-029): `demo_planted_row` on `POST /runs`; row `origin: demo`; evaluation runs
  refuse to start with the switch on and each report records the switch state (EC-R7).
- **Decided 2026-11-12 (operator, SAD SOQ-18):** the backend **refuses approval of any `demo` row**,
  records the refusal in the audit log and shows a plain message; the only decision that can be
  recorded on a demo row is reject. **Its Approve button stays visible and the server refuses the
  click (DL-44).** Test T-DEMO-2 (SAD CR-029); approval map H3a (**Never**) and T-25.
- **Cost**: about 0.5 focused day (SAD WP-12d).
- **Changed**: SAD `POST /runs`, row origin values, new CR-029, EC-R7, EC-013 · **still to do by
  `@product-mgr`**: a requirement and acceptance criterion for the switch and the demo row; the demo
  decisions in the stories index (reject the planted row at G1, with a reason). **Done 2026-11-12 by
  `@product-mgr`** (branch `sad-dl29-31`): SD FR-031 and AC-038; US-004 criterion 19; the demo decision in
  `user-stories/README.md`; approval map H0b and A26 (H3a and T-25 kept).
- **Decided 2026-11-12 (operator, SAD SOQ-22):** **the verifier runs on the planted row**, so it
  follows the same path as every other row and nothing is special-cased. The demo script does not
  depend on whether the verifier flags it: the specialist rejects it at G1 either way, and
  approving it is still refused. One extra verifier call on a demo run. **Still to do by
  `@product-mgr`**: say so in SD FR-031 and in the demo decisions in the stories index.

### DL-32 · Capacity is five focused days; anything beyond is buffer

- **Decision**: the operator plans Build and Deliver for **five focused days**. Anything beyond that
  is buffer, not scope. This resolves SAD SOQ-12 and the capacity part of PRD OQ-5.
- **Why**: a senior-architect review of the SAD found the thin slice estimated at about 44.5 focused
  days (45.75 after DL-29 to DL-31) against 5 to 8 days actually available. DL-22 recorded the
  capacity as a commitment "without a number", so the fit could not be checked.
- **Considered**: planning for 8 days, the upper end of what is available. Not chosen: with 5 as the
  plan, the buffer is real.
- **Consequence**: the SAD estimate is re-cut to about **5.5 focused days (4.5–8)**, which is half a
  day over. **Decided 2026-11-12 (operator, SAD SOQ-19):** the half day, a quarter each for the
  light visual pass and the planted demo row, comes from the buffer. If the first day's work
  overruns (SAD checkpoint: blocks B1 and B2 over 1.3 days), **the visual pass is dropped first and
  the planted demo row is kept**, because the row demonstrates the human checkpoint; the visual
  pass can then be done after the course for the operator's portfolio.
- **Fallback, decided 2026-11-12 (operator):** this applies only if the planted demo row is later
  cut as well. The specialist rejects `OBL-06` at G1 if, on the day, the specialist judges `OBL-06` unsound.
  `OBL-06` produces no calendar entries, so the demo calendar stays at 22. If `OBL-06` is sound on
  the day, the demo shows no rejection and relies on the decisions already in the script: the two
  approvals over a flag and the "unsure" decision.
- **Changed**: SAD "Estimate: five focused days", SOQ-1, SOQ-12 · **still to do by `@product-mgr`**:
  PRD OQ-5 (capacity and the new estimate).

### DL-33 · Plain server-rendered pages with a light visual pass; Next.js is post-course

- **Decision**: the MVP's two surfaces are **plain server-rendered HTML pages** served by the
  backend. A visual pass is in scope and kept light: one small shared stylesheet with clear type,
  spacing and status colours, and **no JavaScript framework**. The backend's page handlers stay thin,
  calling the same service functions a JSON API would call, so an API can be added later without
  rework. **Next.js is recorded as post-course future scope.**
- **Why**: a separate Next.js application with a generated client, fixtures and an integration step
  was about 10 of the 45.75 estimated days, the largest single block. Pages served by the backend
  remove that block. The visual pass stays so the demo is readable.
- **Considered**: keeping Next.js (does not fit five days); unstyled pages (not chosen: the operator
  put a light visual pass in scope).
- **Supersedes**: SAD SOQ-4 and the resolution of PRD OQ-8, for the MVP. PRD A-4 ("web") and the
  WCAG 2.2 AA standard are unchanged.
- **Cost**: about 1 focused day for the gate actions and pages (SAD B5) and 0.25 for the stylesheet
  (B6).
- **Changed**: SAD decisions in force, estimate, Future Work F-10 · **still to do**: `@product-mgr`,
  PRD OQ-8; `@system.arch`, SAD §1 and §3 in the rewrite, and diagram view 2 (containers), which
  names Next.js.

### DL-34 · Evaluations report; they do not block (replaces DL-23's gate)

- **Decision**: (1) Evaluations **report, they do not block**. Three runs on the same commit; a pass
  means 3 of 3; a miss is stated in the evaluation report and the demo goes ahead. (2) **Tuning is
  capped at half a day**, after which the result is reported as it stands. (3) A run that fails only
  because of a **model-service timeout or outage** is voided and re-run once, under a rule written
  down before the first run (SAD EC-R8). **The checks that use no model stay blocking:** gates
  cannot be bypassed, GPs see only published content, dates match the 22 expected entries, and the
  audit log is complete. DL-23's second part, names graded by the specialist, is unchanged.
- **Why**: the targets are exact matches from probabilistic models, and DL-23's "fix and repeat all
  three runs" loop had no upper bound (the SAD estimated tuning at 1 to 6 days) against a five-day
  plan. The PRD (§7) and DL-10 already say a missed target is a finding to report, not to hide.
- **Considered**: keeping the gate. Not chosen: tuning could use the whole buffer or delay the demo.
- **Trade-off accepted**: the demo may carry an honest reported miss (for example a conflict flagged
  on 2 of 3 runs) instead of a clean pass. The gates still stop anything unapproved reaching a GP.
- **Changed**: SAD §5 release rule; §9 run rules EC-R1, EC-R1a and EC-R4, new EC-R8 (void rule) and
  EC-R9 (tuning cap); estimate block B9; US-013 criteria 10 and 12 (done 2026-11-12 by `@product-mgr`) ·
  **still to do**: `@system.arch`, demo readiness in SAD §10 (pass 4 of the rewrite).

### DL-35 · The SAD is rewritten as an MVP version, with three simplifications

- **Decision**: `sad.md` becomes a lean MVP SAD (`*create-sad --mvp`). It describes only what the
  five-day build needs and lists everything else once, under "Future Work". The full design is kept
  unchanged at git tag `sad-full-design` (commit `9e7da27`). IDs that stay keep their numbers;
  retired IDs are listed and never reused.
- **Three simplifications that go with the five-day cut** (proposed by the architect; **accepted by
  the operator on 2026-11-12**, with a condition on the first): (a) each stage is run by a **plain
  function in the backend**, with no CrewAI Flow wrapper. *Operator's condition:* the extractor,
  verifier and applicability steps **remain CrewAI agents**, so the system stays visibly
  multi-agent, and the backend still alone owns the gates (see the wording change on DL-17). (b) **No
  invalidation machinery**: each row and verdict is decided once, so nothing goes out of date; the
  version each decision was made on is still recorded (SD MD-009) and stays at 1. (c) **Entry IDs
  drop the quote position**, which depended on where a model started its quote; if two approved rows
  would give the same ID, generation fails closed and names both.
- **Why**: build agents read the whole SAD, and "future scope" labels did not stop about 30 places
  from describing deferred features as built. Each fix so far had added text; the file grew from
  1,841 to 1,960 lines while being corrected.
- **Considered**: another sweep of the existing file (the same additive pattern); a separate
  `sad-mvp.md` (26 framework files read the SAD by the name `sad.md`); an archived copy in the
  repository (agents searching the repository would still read it).
- **Changed**: `sad.md`, in four passes on branch `sad-mvp-rewrite` · **still to do**: `@system.arch`,
  passes 2 to 4, diagram views 2 and 3, the approval-map re-check; `@product-mgr`, the list in SAD
  SOQ-20.

### DL-36 · Model spend: a target of about US$15, with real model calls only where they count

- **Decision** (operator, 2026-11-12; supersedes DL-24):
  1. **Per-run hard stop: US$2.50**, in place of US$4. The US$2 target per run (SD MC-002) and the
     warning at US$2 are unchanged.
  2. **Building and the automated tests use stand-in agents**, which return fixed outputs and call
     no model. Stand-in is the default mode; a stand-in run is labelled wherever it appears; an
     evaluation run refuses to start in stand-in mode.
  3. **Real model calls are allowed for five activities only**: the measurement spike and verifier
     bake-off (at most 70 calls), prompt tuning (at most 60 calls, as well as the half-day cap),
     **one** evaluation cycle of three runs, one rehearsal run, and the demo run.
  4. **One budget line: a target of about US$15 in total.** US$15 of prepaid credits is loaded, so
     the balance enforces the target. Going past it needs a recorded operator decision; the
     absolute ceiling stays US$50 until 13 December 2026.
- **Why**: the earlier plan assumed several real runs a day during the build and 15 to 20
  evaluation runs, with a worst case of US$12 a cycle. A clean run is about 18 small calls and is
  expected to cost well under US$1, so most of that spend bought nothing the stand-ins cannot give.
- **Trade-offs accepted**: a run that reaches US$2.50 is cut off, and every criterion it would
  have measured counts as a miss. Problems with the real model can surface late, which is why the
  spike stays as the first real calls. **There is one evaluation cycle: a miss is reported as it
  stands**, and fixing and re-measuring needs a decision to spend more. The stand-in mode, its
  label and the call counter add about an hour or two of build work.
- **Considered**: dropping the spike (not chosen: the time limits and the verifier's model, DL-26,
  would be unmeasured); no real rehearsal (not chosen: the demo would be the first real run with
  the planted row); keeping US$25 loaded (not chosen: the balance would not enforce the target).
- **Changed**: SAD CR-017, new CR-030, Production Shape, §3, §4, §5, §7, §9 (EC-R9, new EC-R10),
  the estimate note and Known limitations · **still to do by `@product-mgr`**: US-015 criterion
  17, change "US$4 by default" to the new per-run hard stop (SAD SOQ-20 i).

### DL-37 · Four operator questions carried from Define (SAD SOQ-6) answered

- **Decision** (operator, 2026-11-12):
  1. **PRD OQ-1, four-eyes review: future scope.** In the MVP a single specialist decides at each gate.
  2. **PRD OQ-10, programme submission requirements: not important; omitted.** Nothing is recorded
     against them.
  3. **PRD OQ-12, manual-effort estimate: recorded as an assumption (PRD A-9), not a measured figure**:
     about [X hours/days] per fund per year by hand today. **The figure is still a placeholder**; the
     operator gives it before the demo.
  4. **PRD OQ-7, AED subscription-tax part: stays marked as unconfirmed under CR-027** until it is
     checked against the public source. The demo shows the flag.
- **Why**: one specialist per gate keeps the MVP to the thin slice (DL-22, DL-32); the programme
  requirements do not change what is built; no ROI is claimed without a measured baseline (PRD §7);
  the tax rule is never guessed by code (DL-19, DL-20).
- **Changed**: PRD §4 future-scope note, A-9, OQ-1, OQ-7, OQ-10, OQ-11 (no longer arises, SAD SOQ-6),
  OQ-12; four-eyes wording in US-004, US-007, US-010, the stories index, `context-summary.md`,
  SD OQ-5 and `approval-map.md` (done) · **still to do by `@product-mgr`**: the OQ-12 figure.

### DL-38 · A hosted portfolio demo is a stretch goal, started only after the local demo works

- **Decision** (operator, 2026-11-12):
  1. **The core five-day plan does not change.** The demo is local (DL-32, PRD §3). Nothing in the
     core build depends on hosting.
  2. **A hosted "portfolio demo mode" is a stretch goal.** It starts only after the local demo works
     end to end: the acceptance pass and the rehearsal run (estimate block B10) are done on the local
     build and the checks that use no model pass. The reason for it: a hosted link during the course,
     so that if hosting goes wrong the operator can get help at office hours.
  3. **Host: Railway**, one service with one volume for the SQLite file. The operator confirms the
     current Railway pricing and sets a spend limit on the account **before deploying**. The SAD
     states no price.
  4. **The hosted demo is public by design.** It runs the stand-in agents only (fixed outputs), holds
     mock data only, and has **no model key set on Railway at all**, so a visitor cannot cause model
     spend and there is nothing secret to leak. Safeguards kept: a visible "demo, mock data" label on
     every page; an automatic reset of the demo data (nightly, and on a button); no model key; the
     mock sign-in page, where a visitor chooses specialist or GP; and CSRF protection on every form.
     **Added the same day:** a visible **Reset demo** button on every page, open to every visitor, as
     well as the nightly reset, so offensive text can be cleared at once (a named exception to the
     rule that a GP cannot write, limited to once a minute for the whole site); and a short banner
     saying someone may be mid-run and how to reset.
  5. **Drop order.** The hosted stretch is below everything in the core plan: it is dropped (not
     started) before the light visual pass (B6), and the visual pass is dropped before the planted
     demo row (B7), which is kept.
  6. **Sharing rule.** If the visual pass (B6) is dropped, the hosted link is not shared publicly
     until the visual pass is done (SAD SOQ-23c). It may still be used privately, for example at
     office hours. This is a rule about what the operator does, not a security control.
- **Why**: a link the operator can show, and debug with help, is worth about a day only if the core
  demo already works. Stand-in agents make a public site safe and free to run. A public site with
  mocked sign-in is not access control, so the safety rests on there being nothing of value to reach
  (SAD §8).
- **Considered**: AWS (more setup than one process and one file need; not chosen); a password on the
  whole site (rejected by the operator: the demo is meant to be open to visitors); real model calls
  on the hosted copy (rejected: it would need a key on the host and an open spend path).
- **Changed**: SAD (new "Stretch goal: hosted portfolio demo" section, decisions table, §5, §8,
  Control Register CR-031, estimate drop order, Implementation Guidance, SA-21, SOQ-23). No Define
  requirement changes; PRD §3 Infrastructure is raised for `@product-mgr` as SOQ-23 (b).

### DL-39 · Agent cards: what each agent sees, says and leaves to the specialist

- **Decision** (operator, 2026-11-12, on the architect's agent-card proposal):
  1. **The mock files' answers never reach a prompt.** The loader reads only the paragraph text of
     each source and only the ID, fact and value of each fund fact. It never reads the "Test note"
     or "Planted conflict" notes, the header warnings, the amendments, or the fund profile's
     "Decides" column. A test that uses no model (T-LEAK-1) fails if any of that content, or the
     phrases "Test note", "Planted conflict", "correct verdict" or the "Decides" column, appears
     in a rendered prompt.
  2. **"Who files" is never guessed.** The extractor reports the responsible party only when the
     source document states it, and otherwise "not stated in source". In that case the specialist
     sets "who files" at G1, from the fund's parties, like the business-day rule. US-001
     criterion 2 needs rewording by `@product-mgr` (SAD SOQ-24). **Narrowed the same day
     (operator):** the G1 list is **only the filing parties** (AIFM, Fund administrator, Auditor,
     Local reporting agent (Spain), Tax advisor) plus "not known". The compliance specialist and the GP are
     not filers and are never offered (SAD W-07, CR-007, SOQ-26).
  3. **Only primary documents go to the extractor**: five calls, not six. The secondary guide still
     goes to the verifier. "No row cites the guide" becomes true by construction.
  4. **No `pattern` field in the extractor's output.** Code derives the pattern for the evaluation
     report from the frequency and the anchor.
  5. **The judge's general rule is worded generally.** It says a fact counts only when what it
     asserts meets the condition as the rule words it. The wording was checked against the demo
     material so that it does not repeat the words of any demo trap (SAD, "Agent cards").
  6. **Each card's worked example is also its one-shot example in the prompt**, on one condition:
     the example is drawn from text in none of the six demo rows, the planted row or any evaluation
     case, and it does not mirror a demo trap. A test that uses no model (T-EXAMPLE-1) fails if an
     example's quote matches any mock source paragraph (and the planted-row fixture, the answer
     key's quotes and the evaluation cases); "does not mirror a demo trap" is recorded in a review
     table in the SAD. The first drafts of the examples were replaced because two mirrored demo
     traps in structure (a secondary source giving a different offset; a definition paragraph and a
     "may submit on its behalf" paragraph).
- **Why**: (1) a prompt that contains the answer makes the evaluation meaningless (CR-016). (2) The
  sources are silent on who files for four of the six demo rows, so an extractor that matched the
  answer key there would be guessing (the same principle as DL-19). (3) A rule code can enforce
  should not be left to a model. (4) `pattern` repeated other fields, and "conditional" was too vague
  to apply consistently. (5) The rule protects against the costliest error (P-1), but wording that
  echoed a demo case would teach to the test and flatter the evaluation.
  (6) A one-shot example helps the model get the format right, but an example that echoes a demo
  case teaches the answer to that case.
- **Considered**: giving the extractor the fund's parties table (rejected: it would judge facts about
  the fund, and its context would no longer be one document); removing the judge's rule entirely
  (rejected by the operator: the rule is sound, only its wording needed to be general).
- **Pending, not part of this decision**: the exact model IDs. **DL-40 is held** until the operator
  has checked them against the OpenAI account's model list and pricing (SAD SOQ-25, which also sets
  out whether the verifier is from a different family than the extractor).
- **Changed**: SAD (new "Agent cards" in §2; MVP scope steps 3 and 6; W-03, W-07, W-16; call counts;
  Model and Context Strategy; CR-007, CR-016; §3 G1 page; §4 route, refusal code and
  `row_decisions`; EC-001; SA-7; the estimate note for B5; SOQ-24, SOQ-25). For `@product-mgr`:
  US-001 criterion 2, the answer key's notes on responsible role and pattern, and the related G1
  story wording (SAD SOQ-24).

*DL-40 is reserved for the model IDs, held until the operator has checked them (SAD SOQ-25).*

### DL-41 · Responsible role is graded through a fixed lookup to the profile's party names

- **Decision** (operator, 2026-11-12, recorded **before the first evaluation run**):
  1. **The extractor is unchanged in substance.** It still reports who files as free text, as the
     document states it, or "not stated in source". **DL-39 stands: no parties list goes in the
     extractor's prompt.**
  2. **The evaluation maps the text in code.** Before the exact-match comparison with answer key §1
     (US-013 criterion 11, SAD EC-001), the evaluation runner normalises the extracted text and
     looks it up in a small, fixed table that gives a party name from the fund profile (for
     example "a local reporting agent" becomes "Local reporting agent (Spain)"), or "not stated in
     source". The table is in SAD EC-R11.
  3. **Text that does not map is a miss.** The report shows the extracted text, "no match" and the
     expected value. No model and no judgement is used to stretch a match.
  4. **A test that uses no model** (T-MAP-1) checks the lookup.
  5. **The table is fixed before the first evaluation run** from the profile's party names and the
     mock sources' own wording, **never from a model's output**, and is **not changed between the
     runs of a cycle**. A change needs a recorded operator decision and applies from the next
     cycle. *(Proposed by the architect for the same reason as the void rule, EC-R8; confirmed by
     the operator the same day.)*
  6. **The extractor's wording for who files** is "the party's name as the document writes it,
     with no explanation", or "not stated in source". It is still free text, and still no parties
     list is in its prompt. *(Proposed by the architect; confirmed by the operator.)*
  7. **One name for the Spanish agent everywhere: "Local reporting agent (Spain)"**, in the
     profile, the answer key, the G1 list, the stories and the SAD. The sources' own wording ("a
     local reporting agent appointed by the undertaking") stays as it is; the lookup maps it.
     *(Confirmed by the operator.)*
- **Why**: the sources name a party in their own words ("a local reporting agent appointed by the
  undertaking"), while the answer key uses the profile's name ("Local reporting agent (Spain)").
  An exact match on raw text would fail a correct row; giving the extractor the parties list
  would break DL-39. A fixed lookup keeps the comparison exact and repeatable, and fixing it
  before any run keeps it from being tuned to the results.
- **Considered**: grading responsible role by the specialist's judgement, as for the obligation
  name (option 2 in the discussion; not chosen); giving the extractor the parties list (rejected:
  DL-39).
- **Changed**: SAD EC-R11 (new), EC-001, the extractor card's wording for `responsible_role`,
  SOQ-27. For `@product-mgr`: US-013 criterion 11, and the matching wording in US-001 criterion 2
  and the answer key §1 column heading (SAD SOQ-27).


### DL-42 · Capacity: 5 days planned, 8 days hard stop; tests in two tiers; day-3 tripwire; hosted demo parked

- **Decision** (operator, 2026-11-12, final review of the MVP SAD; refines DL-32, parks DL-38):
  1. **Capacity is 5 focused days planned and 8 days as a hard stop.** Days 6 to 8 are buffer; what
     is not done on day 8 is not done.
  2. **The uncounted hours are added to the estimate** as block B11, about half a day: stand-in
     mode and the role harness (DL-36), the G1 "who files" choice and the loader tests T-LEAK-1,
     T-PROMPT-1 and T-EXAMPLE-1 (DL-39). The likely figure becomes about 6 days (5 to 8.5).
  3. **Tests in two tiers.** **Tier 1 blocks the build**: EC-013, EC-014, EC-007, EC-008, EC-016,
     T-W04, T-RUN-0, T-RUN-1, T-RUN-3, T-G3ACK-1, T-DEMO-1, T-DEMO-2, T-LEAK-1. **Tier 2 is done if
     time allows**: the six-word overlap part of T-EXAMPLE-1, T-PROMPT-1, T-D4-1, the per-state page
     tests, and T-MAP-1 until the evaluation cycle.
  4. **Day-3 tripwire.** If there are no real Stage A rows by the end of day 3, drop B6 (the visual
     pass) and Tier 2. *Replaced by item 9 on 2026-11-13.*
  5. **The hosted demo stretch goal (DL-38) is parked as Future Work** (SAD F-18).
  6. **Budget:** before the evaluation cycle, the operator confirms at least US$5 will be left for
     the rehearsal and the demo (SAD EC-R10 point 4).
  7. **Refined 2026-11-13 (operator, final pre-Build polish; SAD SOQ-29, partly):** EC-015, EC-019
     and T-MODE-1 join **Tier 1**. **T-MAP-1 is not dropped with Tier 2**: it must pass before the
     first evaluation run even if the day-3 tripwire drops Tier 2. This supersedes the Tier lists
     in item 3.
  8. **Refined 2026-11-13 (operator): first green path before any paid model call.** With
     `AGENTS_MODE=stand_in`, the full happy path must pass end to end (start run → stand-in Stage A
     → G1, including the planted row refused and rejected → stand-in Stage B → G2 → Stage C dates →
     G3 acknowledgement → GP "being prepared", then the published calendar → audit log) **before
     DL-40 is pinned and before the B3 measurement spike**. B3 is stand-in only until B5 and B7 are
     done; the spike moves after B7.
  9. **Tripwire moved 2026-11-13 (operator agreed the architect's recommendation; SAD SOQ-30,
     resolved):** item 4 assumed the spike runs early, and with item 8 it would fire on plan (B1 to
     B7 take about 3.5 days). The tripwire is now: **the first stand-in green path has not passed
     by the end of day 4 → drop B6 and Tier 2, never T-MAP-1.** The green path is the earliest
     reliable sign that the riskiest block works; it does not test real-model behaviour, which the
     spike and bake-off still do.
- **Why**: the estimate left about half a day "in the same margin" without counting it, and a
  five-day plan with no hard stop has no point at which scope is cut. Real extractor output by day 3
  is the earliest reliable sign that the riskiest block (B3) works.
- **Trade-off accepted**: Tier 2 tests and the visual pass may not exist at the demo. The tests
  that protect the gates, dates, audit log and prompts stay blocking.
- **Changed**: SAD "Decisions in force", feasibility constraint, Estimate (B11, capacity, tiers,
  tripwire, drop order), §5 CI, §9 EC-R4, EC-R10 point 4, EC-R11, F-18 and Appendix A, build card,
  SOQ-1, SOQ-23, new SOQ-29 (tests in neither tier, for the operator). **Items 7 to 9 (2026-11-13):**
  SAD build card, "Order of work", Estimate (B3 row, tiers, tripwire, build order), §6 spike, EC-R4,
  SOQ-25, SOQ-29, SOQ-30 (raised and resolved), "Implementation Guidance" scope guardrails, DL-31 line in "Decisions
  in force".

### DL-43 · One timeout rule everywhere

- **Decision** (operator, 2026-11-12):
  1. **Each model call has its own timeout**, with the HTTP client timeout set slightly below it.
  2. **A timed-out call is retried once.** Only a timeout after that retry is a final failure, and
     it is classed as a model-service reason (voidable in evaluations, SAD EC-R8).
  3. **Each stage limit is the sum of its calls with one retry each, plus about 25%**: Stage A ≈
     375 s (90 + 90 + 60 + 60 = 300, plus margin), Stage B ≈ 150 s (60 + 60 = 120, plus margin),
     Stage C 30 s (no model).
  4. **The backend stage timer is the real bound.** CrewAI `max_execution_time` does not cancel a
     call in flight.
  5. **Every store call checks the run state.** A late result after its stage has failed is
     discarded but counts towards cost.
  6. These are starting values, replaced by measured times after the spike.
- **Why**: the SAD described the time limits in three ways (task `max_execution_time`, a stage
  limit of 180 s smaller than its own calls with retries, and a separate "task time limit" failure
  reason), which contradicted each other and the retry rule.
- **Changed**: SAD Production Shape, run state rules 6 and 9, §2 stage table and settings, §4
  failure reasons (reason 2 retired) and settings, §6, EC-R8, T-RUN-2, new T-RUN-8.

### DL-44 · The planted demo row keeps its Approve button; the server refuses it

- **Decision** (operator, 2026-11-12; replaces the "offers reject only" part of DL-31 and SAD
  SOQ-18): on the planted demo row, **Approve stays visible**. On click, the server refuses with
  `DEMO_ROW_NOT_APPROVABLE`, writes the refusal to the audit log, and the page shows a plain
  message. The specialist then rejects the row with a reason.
- **Why**: the demo shows that the server, not a hidden button, refuses the approval, and every row
  keeps the same decision form (the SAD allows no disabled buttons).
- **Changed**: SAD planted-row note, §3 page 4, CR-029, demo script step 5, SOQ-18;
  `approval-map.md` Card G1 and §6 recovery row.

### DL-45 · Evaluation copy cases are separate harness calls

- **Decision** (operator, 2026-11-12): the altered-quote case, `I-1` and the EC-021 injection case
  are **separate harness calls** to the quote check, `check_conflicts` and `extract_rows`, outside
  the run's rows table, labelled in the trace and scored separately.
- **Why**: so EC-001's "0 extra rows" and EC-007's "22 entries" stay true on the run's own data.
- **Consequence**: two model calls per evaluation run, not three (the altered quote is a code check).
- **Changed**: SAD W-20, §7 budget table, §9 "Copy cases".

### DL-46 · Runs carry a phase alongside their status

- **Decision** (operator, 2026-11-12): `runs` gets **`phase`** ∈ {`A_RUNNING`, `AT_G1`,
  `B_RUNNING`, `AT_G2`, `C_RUNNING`, `AT_G3`}, alongside status `ACTIVE`, `FAILED`, `ABANDONED`,
  `DECLINED` or `COMPLETED`. Run-state rules and guards, including `RUN_STAGE_RUNNING` and
  abandon-at-a-gate-only, refer to the phase.
- **Why**: "a stage is running" and "waiting at a gate" were described in words, so each guard had
  to work out the phase again; one stored field makes every guard and the start-up rule a single
  check.
- **Changed**: SAD MVP scope step 13, run state model (phase table, rules 7 to 9, "Transitions and
  guards" with a legend), W-19a, §4 `runs` table, the abandon route and `RUN_STAGE_RUNNING`,
  T-RUN-7. **Still to do**: the run-state diagram, a type the diagram skill gives to `@backend.eng`
  (SAD SOQ-28).

### DL-47 · Approving a row with no business-day rule is refused

- **Decision** (operator, 2026-11-13; raised in `2.build/ux.md` Open Question 5): a G1 **Approve
  with no business-day rule chosen** is refused with the new code **`BUSINESS_DAY_RULE_REQUIRED`**
  (422). The refusal is written to the audit log, the page shows a plain message, and the row
  stays undecided. "Not confirmed" counts as a choice; an empty selection does not.
- **Why**: DL-19 says a rule is never guessed or defaulted by code. Without a refusal, a missing
  selection would either block silently or be filled in by default, which is a guess.
- **Changed**: SAD §4 refusal-code table; `approval-map.md` new row H2a (**Never**). The message
  wording stays in `2.build/ux.md`.

---

## Audit

- 2026-11-09 · persona `product-mgr` · action `update` · log created; DL-01 to DL-12 from the UX and
  business reviews of the PRD
- 2026-11-09 · persona `product-mgr` · action `update` · DL-08 revised: six-week timebox replaces the
  40–50 hour budget; operator decision
- 2026-11-09 · persona `product-mgr` · action `approve-handover` · DL-13 added: handover to
  `@system.arch` approved; operator decision
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-14 (quote
  check is code, OD-8) and DL-15 (manual row creation, SAD SOQ-7) added; operator decisions. SD and
  story updates for DL-15 are listed as still to do by `@product-mgr`
- 2026-11-11 · persona `system-arch` · action `update` · DL-16 (duplicate groups: warn, confirm once
  at G1 completion) and DL-17 (runtime shape: Flow per stage, backend owns gates) added; operator
  decisions from the Control Register review
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · DL-15 follow-up done: FR-027, AC-027, US-016, US-013 criterion 8 (step 1 of 4; DL-16, coverage view and per-unit failure rule still to do)
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · DL-16 follow-up done: FR-029, AC-028, US-004 criteria 14–16 (step 2 of 4; coverage view and per-unit failure rule still to do)
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · coverage view (SAD W-03b) added to Define: FR-028, AC-029, US-001 criteria 8–9 (step 3 of 4; per-unit failure rule still to do)
- 2026-11-11 · persona `product-mgr` · action `update` · coverage view: only non-rejected rows count as citing a paragraph (FR-028, AC-029, US-001 criteria 8 and 10); OQ-US001-2 added; operator decision. SAD W-03b wording ("no row cites") and its count of 5 uncited paragraphs (7 in the demo set) are for `@system.arch`
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · per-unit failure rule added to Define: NFR-004 amended, AC-030, US-015 criteria 9–13, clarifications in US-001 c7 and US-006 c7 (step 4 of 4). All four SOQ-8 items are now in the Define documents; raised for `@system.arch` and the operator: SAD W-03b wording and count, SOQ-8 text (add DL-16, mark resolved), extraction dead end (OQ-US015-2)
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-18 (release a failed extraction document to manual entry; SAD SOQ-9) and DL-19 (business-day rules never guessed; PRD OQ-7 for `OBL-04`, `OBL-05`) added; operator decisions. Follow-ups listed in each entry for `@product-mgr`
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-20 (AED subscription-tax question stays open; dependent entries marked at G1 and G3, no code default); DL-19 note that it excludes the tax question; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` · DL-18 follow-up done (OQ-US015-2 closed; US-015 criteria 14–15, US-016 criterion 11, SD NFR-004, AC-031; new OQ-US015-3) and DL-19 follow-up done (SD OQ-2, KEY OQ-D1, US-009 OQ-US009-1 resolved; PRD OQ-7 and OQ-US008-1 resolved for OBL-04 and OBL-05, AED tax part open). Still to do by `@product-mgr` from DL-20: a G3 criterion in US-010 and a G1 note in US-004
- 2026-11-11 · persona `product-mgr` · action `update` · DL-20 follow-up done: US-010 criterion 12 (mark shown at G3, does not block, specialist-only) and US-004 G1 scope note; PRD OQ-7 tax part, SD OQ-4 and KEY OQ-D3 kept open. No `@product-mgr` follow-ups from DL-15 to DL-20 remain except OQ-US016-2 (operator) and the optional US-013 criterion for counting a release (DL-18)
- 2026-11-11 · persona `product-mgr` · action `update` · US-004 criterion 17 (DL-20 G1), US-013 criterion 9 (release counts as an extraction failure, DL-18), AC-032 and US-011 assumption (DL-20); OQ-US016-2 resolved: PRD F3 line for released documents only. DL-15 to DL-20 follow-ups for `@product-mgr` are complete
- 2026-11-11 · persona `product-mgr` · action `update` · PRD F3 corrected to list manual row creation for both a missed row at G1 and a released document (operator confirmed the earlier wording only described the PRD); DL-15 unchanged; OQ-US016-2 closed on that basis
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-21 (CrewAI adapter deviations D1–D5 and interpretation D6 accepted, with conditions on D4 and D5); operator decision
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-22 (the MVP is the thin slice; recovery, reopen, release, dead-end handling, impact report and extra CI checks move to future scope); operator decision. Follow-ups listed for `@product-mgr`
- 2026-11-11 · persona `system-arch` (at the operator's instruction) · action `update` · DL-23 (evaluation: 3 of 3 runs on one commit; obligation names graded by the specialist); operator decisions
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-24 (development model spend capped at US$50 until 13 December 2026 in the provider account; US$25 checkpoint; spend logged per evaluation run); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` · DL-23 follow-up marked done: US-013 criteria 10–11, OQ-US001-1 and OQ-US013-1 resolved (on branch `define-defer-future-scope`, not yet merged)
- 2026-11-12 · persona `product-mgr` · action `update` · DL-22 updated with the operator's answer to OQ-US015-4: failed step → terminal FAILED run, step time limits, specialist abandon run with a reason (not a general cancel); estimate +2 days (slice ≈ 44.5, 33.5–63); SAD run state model, US-015 criteria 19–21
- 2026-11-12 · persona `product-mgr` · action `update` · DL-22 follow-up done: future-scope requirements, acceptance criteria, story criteria and PRD rows marked deferred (nothing deleted); PRD OQ-5 recorded as decided on scope, capacity open; DL-02 re-run superseded for the MVP
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-25 (OpenAI API on prepaid credits, US$25 to start and US$50 ceiling; model per role; IDs confirmed before the spike; Claude Code is the build tool only); operator decision
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-26 (verifier: mid-tier model by default, switch to the reasoning model if any planted conflict is missed in the spike; cost per run recorded for both); operator decision
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-27 (PRD OQ-6: before the first publication, a read-only empty state with a fixed message; no notifications); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` · DL-27 follow-up marked done: PRD OQ-6, SD OQ-1 and OQ-US011-1 resolved; US-011 criterion 7 and SD AC-013 name the message (on branch `define-gp-pre-publication-message`, not yet merged)
- 2026-11-12 · persona `product-mgr` · action `update` · DL-22 second update: G3 decline ends the run as DECLINED (terminal), SA-18 and the WP-12a estimate confirmed, OQ-US001-2 accepted as a known limitation; SD AC-033 to AC-036, US-010 criteria 8–9, PRD F8 line
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-28 (after a backend restart the specialist abandons the interrupted run; start-up auto-fail is future scope, a known limitation); operator decision
- 2026-11-12 · persona `system-arch` (at the operator's instruction, raised through `@product-mgr`) · action `update` · DL-29 (abandon only at a gate; start-up rule and stage time limit; supersedes DL-28), DL-30 (G3 acknowledgement), DL-31 (planted demo row switch); operator decisions
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-31: SOQ-18 decided (approval of a demo row refused, audited, plain message; reject only); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` · DL-29, DL-30 and DL-31 follow-ups marked done (SD FR-030, FR-031, AC-034, AC-035, AC-037, AC-038; US-010 criterion 14; US-015 criteria 19–20 and restart note; demo decision in the stories index); approval map brought in line with the SAD (SOQ-16) and no longer marked draft; on branch `sad-dl29-31`, not yet merged
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-32 (capacity: five focused days), DL-33 (plain server-rendered pages with a light visual pass; Next.js post-course), DL-34 (evaluations report and do not block; replaces DL-23's gate, with a superseded note on DL-23) and DL-35 (the SAD rewritten as an MVP version, full design at tag `sad-full-design`; three simplifications listed for the operator's review); operator decisions. Follow-ups for `@product-mgr` are in SAD SOQ-20
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · operator's review of SAD pass 1: DL-32 records the buffer decision and the drop order (visual pass first, planted demo row kept); DL-35's three simplifications accepted, with the condition that the three steps remain CrewAI agents; DL-17 carries the wording change (plain stage functions, no Flow wrapper, backend alone owns the gates)
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-32: fallback recorded for the case where the planted demo row is also cut (reject `OBL-06` at G1 only if genuinely weak, calendar stays at 22; otherwise no rejection); operator decision. Operator also confirmed the pattern stays "workflow", described as three CrewAI agents in a gated workflow (DL-17 as reworded); no text change
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-31: the verifier runs on the planted demo row and the demo script does not depend on its flag (SAD SOQ-22); DL-32: fallback wording changed to "if, on the day, the specialist judges `OBL-06` unsound"; tag `sad-full-design` pushed to the remote; operator decisions
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-36 (model spend: target about US$15; per-run hard stop US$2.50; stand-in agents for building; real calls only for the spike, capped tuning, one evaluation cycle, one rehearsal and the demo); DL-24 marked superseded by DL-36, kept and not deleted; DL-25 notes the US$15 first load; operator decision. Follow-up for `@product-mgr`: US-015 criterion 17
- 2026-11-12 · persona `product-mgr` · action `update` · US-015 criterion 17: per-run cost cap changed from US$4 to US$2.50 (hard stop, set in configuration) to match DL-36 and SAD CR-017; closes SAD SOQ-20 (i). The US$2 warning is unchanged
- 2026-11-12 · persona `product-mgr` · action `update` · DL-37 (SAD SOQ-6 answered: four-eyes is future scope; programme submission requirements omitted; manual-effort estimate recorded as an assumption with the figure still to come; AED part of OQ-7 stays unconfirmed and the demo shows the flag); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` · DL-37 follow-through (four-eyes wording in 3 stories, stories index, context-summary, system-description, approval-map); SAD SOQ-20 (a) and (b) done in the PRD. `capstone-brief.md` left unchanged as the original input
- 2026-11-12 · persona `product-mgr` · action `update` · DL-34 follow-through: US-013 criterion 10 reworded (a miss does not block) and new criterion 12 (void rule, tuning cap of half a focused day or 60 real calls, blocking non-model checks); closes SAD SOQ-20 (c) for US-013. The 60-call figure matches SAD EC-R9, EC-R10 and the budget table
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · SAD SOQ-20 (d) and (g): US-001 criterion 7, US-006 criterion 7 and US-015 criterion 9 no longer promise a re-run or a "re-runnable" unit; the failed unit is named and the run fails
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-20 e, f, h) · (e) PRD edit wording, (f) US-008 entry-ID assumption, (h) stories index and SD FR-031 planted-row wording
- 2026-11-12 · persona `product-mgr` · action `update` · SAD SOQ-20 (j) closed: approval-map row H8a added for a second decision on an already-decided row (CR-009, ALREADY_DECIDED); no map row for stand-in agents (CR-030); operator decisions. All of SOQ-20 (a) to (j) is now done
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-38 (a hosted portfolio demo on Railway as a stretch goal after the local demo works; stand-in agents only, no model key, public by design; first to be dropped, then the visual pass, with the planted row kept); operator decision. SAD, section "Stretch goal: hosted portfolio demo", CR-031, SOQ-23
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-23 b) · PRD §3 Infrastructure and §5 Availability now note the DL-38 hosted stretch; no requirement change
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-38 amended: Reset demo button on every page (open to every visitor), banner saying someone may be mid-run, and the sharing rule if the visual pass is dropped; SAD SOQ-23c decided
- 2026-11-12 · persona `product-mgr` · action `update` · wording cleanup after the SOQ-20 spot-check: PRD OQ-5 headline, US-015 Scope Notes and OQ-US015-1; no decision changed
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-39 (agent cards: the loader strips the mock files' answers, with test T-LEAK-1; "who files" set by the specialist at G1 when the source is silent; only primary documents to the extractor; no `pattern` field, derived by code; the judge's general rule worded generally and checked against the demo traps); operator decisions on the architect's proposal. Model IDs and one-shot examples still pending (SAD SOQ-25)
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-24 a to e) · US-001 c2, answer key §1 and §5, US-004 c8 and c20, US-011 c2 and c12, PRD F3, stories index; OQ-D4 (tax advisor missing from the mock profile) and OQ-D5 (more than one party for OBL-03) opened in the answer key; no date, verdict or flag changed
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-39 item 6 added: worked examples are used as one-shot examples, drawn from text in no demo row, planted row or evaluation case and mirroring no demo trap, checked by T-EXAMPLE-1 and a review table; DL-40 (model IDs) held until the operator checks the account's model list and pricing
- 2026-11-12 · persona `product-mgr` · action `update` (operator decisions on OQ-D4, OQ-D5; SAD SOQ-24) · fictional "Tax advisor" added to the mock profile's parties; `OBL-06` expected G1 value "Tax advisor"; `OBL-03` "Fund administrator" (G1 takes one party, the filer); answer key rechecked, no expected result changed; US-004 and US-011 examples aligned; system description FR-005 and approval-map H1 updated, both flagged for `@product-mgr` to confirm
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-39 item 2 narrowed: the G1 "who files" list is only the filing parties (AIFM, Fund administrator, Auditor, Local reporting agent, Tax advisor) plus "not known"; SAD W-07, CR-007 (T-WHO-2), SOQ-26 for `@product-mgr`
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-26 a to c; operator decision on naming) · G1 "who files" list is the filing parties only: US-004 criterion 20, answer key §5 note, profile "Filing party" column; "Local reporting agent (Spain)" is the one name in the stories, the key, the profile and the G1 list; PRD F3 aligned
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-41 (responsible role graded through a fixed lookup to the profile's party names before the exact match; unmapped text is a miss; test T-MAP-1; table fixed before the first evaluation run; DL-39 stands, no parties list in the extractor's prompt); recorded before any evaluation run exists. DL-40 stays reserved for the model IDs
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-41 confirmed by the operator: item 5 (lookup table fixed before the first evaluation run, never from model output, not changed mid-cycle), new item 6 (extractor wording: party name as written, no explanation, no parties list), new item 7 (one name, "Local reporting agent (Spain)"). DL-39 item 2's note now uses that name
- 2026-11-12 · persona `product-mgr` · action `update` (SAD SOQ-27, DL-41) · US-013 criterion 11, US-001 criterion 2 and the answer key's §1 heading and notes now agree: responsible role is mapped to the profile's party name by a fixed lookup, then matched exactly (SOQ-27 a to c)
- 2026-11-12 · persona `system-arch` (at the operator's instruction) · action `update` · DL-42 (capacity 5 days planned, 8 days hard stop; test tiers; day-3 tripwire [superseded 2026-11-13: the tripwire is now "the first stand-in green path has not passed by the end of day 4", SOQ-30; see the 2026-11-13 entry]; hosted demo parked; US$5 kept for rehearsal and demo), DL-43 (one timeout rule), DL-44 (demo row Approve stays visible and is refused by the server), DL-45 (evaluation copy cases as separate harness calls), DL-46 (run phase); operator decisions from the final SAD review. Follow-up for `@product-mgr`: PRD A-9 wording (SAD SOQ-6)
- 2026-11-13 · persona `system-arch` (at the operator's instruction, final pre-Build polish) · action `update` · DL-42 refined: items 7 (EC-015, EC-019 and T-MODE-1 to Tier 1; T-MAP-1 not dropped with Tier 2), 8 (first stand-in green path before DL-40 is pinned and before the B3 spike, which moves after B7) and 9 (tripwire moved from day 3 real Stage A rows to day 4 green path, SAD SOQ-30 resolved); DL-31 now states that the planted row's Approve button stays visible and the server refuses it (DL-44). No new DL number
- 2026-11-13 · persona `system-arch` (at the operator's instruction; ux.md Open Question 5) · action `update` · DL-47 (approving a row with no business-day rule is refused as `BUSINESS_DAY_RULE_REQUIRED`, audited, plain message); operator decision
