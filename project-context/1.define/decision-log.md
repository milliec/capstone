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

---

## Audit

- 2026-11-09 · persona `product-mgr` · action `update` · log created; DL-01 to DL-12 from the UX and
  business reviews of the PRD
- 2026-11-09 · persona `product-mgr` · action `update` · DL-08 revised: six-week timebox replaces the
  40–50 hour budget; operator decision
- 2026-11-09 · persona `product-mgr` · action `approve-handover` · DL-13 added: handover to
  `@system.arch` approved; operator decision
