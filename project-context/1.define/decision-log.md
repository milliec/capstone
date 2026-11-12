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

- **Decision**: accepted as a **known MVP limitation**. If the backend restarts while a stage is
  running, no step timer fires and the run stays `ACTIVE`; the specialist ends it with **abandon and a
  written reason** (SAD DM-18, W-19a, SD AC-035), and then starts a new run. The start-up rule that
  would mark such a run `FAILED` automatically ("service restarted") moves to **future scope**.
- **Why**: abandon already exists in the slice and undoes nothing; a restart is rare in a local demo;
  the start-up rule is extra Build work (about 0.25 day) for a case abandon already covers.
- **Changed**: SAD SOQ-17 resolved, future-scope table (robustness row), Delegation Map future-scope
  list · **for `@product-mgr`**: if the known-limitations list in US-015 or the PRD should name it.

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
