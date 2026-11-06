# System Description

**Working title**: Regulatory Intelligence for fund compliance calendars
**Author / stakeholder**: Capstone operator (product owner)
**Selected Runtime**: `crewai`, as recorded in `aamad.config.yml`. This is a configuration value only.
The application pattern and the full runtime roster are **not** decided here. They belong to the
architecture step (`@system.arch`) in a later sprint.

> **Phase:** Define. This document says *what* the system must do and *how we will know it works*. It
> deliberately says nothing about architecture, components or screens.

> **Data:** All data is mock. See `project-context/1.define/mock-data/`. No real client data, fund
> names or branding appear anywhere in this project.

---

## 1. Intent and Problem

- **Problem statement**: Managers of regulated funds (for example Luxembourg UCI Part II funds) receive
  their filing obligations as static legal text and track them in spreadsheets. Every new regulatory
  framework means another manual round of reading, interpreting and setting deadlines. Manual
  interpretation produces inconsistent rules (evidence: `mrd.md` §2). The difficulty grows because a
  Part II fund's obligations come from overlapping layers (Luxembourg product law, the AIFM Law and EU
  rules, plus tax, registry and cross-border rules), each with its own authorities, deadlines and wording
  (`mrd.md` §2, background only).
- **Primary users / operators**:

  | User | Setting | Can do |
  |---|---|---|
  | **Compliance specialist** | Owns the obligation calendar. Works through agent output and decides. | Approve, edit or reject at every gate. Set business-day rules. Publish the calendar. |
  | **GP / fund manager** | Accountable for the fund's filings, but files few of them. Often less familiar with Luxembourg rules. | **Read only.** Sees what is due, when, who files it, and why. |
  | **Filing parties** (AIFM, administrator, auditor, tax advisor, local reporting agent) | Do most of the actual filings for the fund. | **Nothing in the MVP.** Stakeholders, not users. Named on every obligation as "who files". |

- **Success definition (MVP)**: On the mock data set, the system produces the results in
  `mock-data/expected-obligation-library.md`. Every calendar entry traces back to a source paragraph and
  a specialist approval. Nothing reaches the GP view without passing all three approval gates.

## 2. Domain Context

### Vocabulary

| Term | Meaning |
|---|---|
| **Source paragraph** | One numbered paragraph of regulatory text, with a stable ID (e.g. `SRC-UCILAW-P3`). |
| **Obligation row** | One obligation in a fixed schema: what, recipient, who files, frequency, anchor, offset, applicability rule, business-day rule, source paragraph ID, verbatim quote. |
| **Obligation library** | All approved obligation rows for one regulatory framework. |
| **Applicability verdict** | For one fund and one row: **applies**, **does not apply** or **unsure**, with reasoning that cites fund facts. |
| **Anchor** | The reference date a deadline is calculated from: month-end, quarter-end, financial year-end, a fixed date, or an event's awareness date. |
| **Offset** | The time added to the anchor, e.g. "+10 calendar days" or "+6 months". |
| **Business-day rule** | Per obligation: **roll forward** to the next Luxembourg business day, **no roll**, or **not confirmed**. |
| **Calendar entry** | One dated occurrence of an applicable, approved obligation for the fund. It has a stable ID. |
| **Quote check** | The verifier confirms that a row's quote appears word for word in its cited paragraph. |
| **Conflict check** | The verifier flags two kinds of disagreement. **Internal**: the row's fields (e.g. offset, anchor) do not match what its own quote says. **Cross-source**: the row disagrees with another source. |
| **Gate** | A point where a compliance specialist must approve before anything moves on (G1, G2, G3; see MD-004). |

### Design principles

**P-1: Under uncertainty, choose the cheaper mistake.** When the system or the specialist cannot be sure,
pick the option whose error is harmless. In compliance, an extra calendar entry or an early deadline
costs minutes to fix. A missed filing is a regulatory breach.

| Situation | Uncertain about | Safe default | Where applied |
|---|---|---|---|
| Applicability | Whether an obligation applies (e.g. CNMV registration unconfirmed) | Treat it as **applies (precautionary)**, with the note "precautionary: registration unconfirmed" | Demo decision at G2 for `OBL-04` |
| Business-day rule | Whether a weekend deadline rolls forward | **Keep the earlier date** and mark it | Answer key `D-6` |
| Gate approval | Whether a flagged rule is right | **Block** until a person decides, with a reason | MD-004, MD-005 |

*Why this is written down:* during Define, the demo decision for `OBL-04` was first set to "does not
apply". That would have made a deadline disappear because information was missing, the most harmful
error this system can make. Naming the principle stops the same choice being made again.

### Existing systems, data and workflows to respect

- The mock data set in `project-context/1.define/mock-data/`: sources, fund profile and answer key.
- The date conventions `D-1` to `D-7` defined in the answer key.
- No live systems are connected. Every external system is mocked.

### Regulatory and organisational constraints

- Output is a **draft for a specialist**, not legal advice.
- The repository is **public**. Nothing confidential may be committed.

## 3. Discovery Buckets

### Must do

| ID | Item | Kind | Testable constraint |
|----|------|------|---------------------|
| MD-001 | Extract obligations from source text into fixed-schema rows | requirement | Each row cites exactly one source paragraph ID and a verbatim quote from it. Paragraphs with no obligation produce no row. |
| MD-002 | Judge whether each approved row applies to the fund | requirement | Each verdict is one of applies / does not apply / unsure, with reasoning that cites at least one fund fact ID. |
| MD-003 | Verify rows with a **separate** verifier agent | requirement | The verifier is not the agent that extracted the row. It runs a quote check and a conflict check (internal and cross-source) on every row and reports flags. |
| MD-004 | Require specialist approval at three gates | requirement | **G1** rule approval (per row, after verification) · **G2** applicability approval (per verdict; "unsure" cannot pass without a human decision) · **G3** calendar publish (per fund). Each gate offers approve / edit / reject. |
| MD-005 | Re-verify after any edit | requirement | Editing a row re-runs the verifier on that row. A remaining flag can only be overridden with a written reason. Editing an approved row returns it to pending, sends its verdict back through G2 once it is re-approved, and marks dependent calendar entries out of date. |
| MD-006 | Calculate due dates with deterministic code | requirement | Dates come from approved rows only, using anchor + offset and conventions `D-1` to `D-7`. Each row's own business-day rule is applied. An unconfirmed rule keeps the earlier, unrolled date and marks it. |
| MD-007 | Handle event-triggered obligations | requirement | A logged event with an awareness date produces a calendar entry anchored on the **awareness** date. |
| MD-008 | Give GPs a read-only view of what is due and why | requirement | Each entry shows **what** (obligation + authority), **when** (date, plus a roll note if moved), **who** files, and **why** (plain-English reason + source citation and quote). |
| MD-009 | Keep an audit log | requirement | Every agent output and every human decision is recorded with who, when, what and (for overrides and rejections) why. Opening each gate is also recorded, so review time can be measured (MC-003). |
| MD-010 | Prepare for filing status later | requirement | Every calendar entry has a stable ID that a future filing record could reference. |
| MD-011 | **Stretch:** assess the impact of a rule amendment | requirement | Given an amendment to a source, the system identifies which rows, verdicts and calendar entries are affected (one, several or none), flags only those, and explains why. It never applies a change itself. Affected items go back through G1 or G2. |

### Must not do

| ID | Item | Kind | Testable constraint |
|----|------|------|---------------------|
| MN-001 | Use real client data or branding | requirement | A scan of the repository for a private list of real identifiers returns no matches. The list lives in the git-ignored `reference/` folder and is never committed. |
| MN-002 | Contact external parties or live systems | requirement | No live email, regulator portal or task-tool calls. All externals are mocked. |
| MN-003 | Let agents move work past a gate | requirement | No row, verdict or calendar can reach the next step, or the GP view, without the matching gate approval. |
| MN-004 | Let the verifier resolve conflicts on its own | requirement | Conflicts are flagged for the specialist. The verifier never changes a row. |
| MN-005 | Let a language model calculate dates | requirement | Every due date is produced by deterministic code. Agent output contains no computed dates. |
| MN-006 | Accept a row without a source | requirement | A row with a missing paragraph ID or a failed quote check cannot be approved. |
| MN-007 | Show unfinished work to GPs | requirement | The GP view shows no pending, unsure, rejected or conflicted items (see OQ-1). |
| MN-008 | Use a task tool as the system of record | requirement | Obligations, verdicts, approvals and calendar entries live in this system only. |
| MN-009 | Present output as legal advice | requirement | The GP view and exports carry a note that rules are specialist-approved interpretations, not legal advice. |

### Must cost

| ID | Item | Kind | Testable constraint |
|----|------|------|---------------------|
| MC-001 | Pipeline run time | requirement (operator-confirmed) | A full run on the demo set (6 source documents) produces all agent output in **under 5 minutes**, not counting specialist review time. |
| MC-002 | Model cost per run | requirement (operator-confirmed) | A full demo run costs **under US$2** in model usage. |
| MC-003 | Specialist review effort | requirement (operator-confirmed) | A specialist can work through all three gates for the demo set in **under 30 minutes**, measured from audit-log timestamps (Gate 1 opened → Gate 3 published), not by hand. |

> All three values were confirmed by the operator during Define.

### Must prove

| ID | Item | Kind | Evidence the system must produce |
|----|------|------|----------------------------------|
| MP-001 | Extraction is correct | requirement | Evaluation report: 6 of 6 expected rows, 0 rows from non-obligation paragraphs, all quotes verbatim. |
| MP-002 | Applicability is correct | requirement | Evaluation report: 6 of 6 verdicts match, including `OBL-04` = unsure and `OBL-06` = does not apply. |
| MP-003 | The verifier catches problems and avoids false alarms | requirement | Evaluation report: conflicts `C-1` and `C-2` flagged. No flag on `OBL-01`. A deliberately altered quote is caught. A deliberately wrong field with a correct quote is caught. |
| MP-004 | The calendar is correct | requirement | Generated calendar equals the 22 entries in the answer key, including the 4 rolled dates and 2 marked dates. |
| MP-005 | Every entry is traceable | requirement | For any GP calendar entry, the system shows its source paragraph, quote, verdict and approval records. |
| MP-006 | Gates cannot be bypassed | requirement | Test log: attempts to publish without G1, G2 or G3 approval are refused. |
| MP-007 | Dates are deterministic | requirement | Two runs from the same approved inputs produce identical calendars. |
| MP-008 | The audit log is complete | requirement | Every decision in a demo run appears in the log with who, when and what. |

## 4. Functional Requirements

| ID | Description | Priority | Source bucket ID |
|----|-------------|----------|------------------|
| FR-001 | Load mock source documents, split into identified paragraphs. | Must | MD-001 |
| FR-002 | Extraction agent produces fixed-schema rows, each with one paragraph ID and a verbatim quote. Business-day rule defaults to "not confirmed" unless the source states it. | Must | MD-001 |
| FR-003 | Verifier agent runs a quote check on every row. | Must | MD-003, MN-006 |
| FR-004 | Verifier agent runs a conflict check on each row: internal (fields vs its own quote) and cross-source (against all other sources, primary and secondary). | Must | MD-003, MN-004 |
| FR-005 | G1: the specialist approves, edits or rejects each verified row and sets its business-day rule. | Must | MD-004 |
| FR-006 | Editing a row re-runs the verifier on that row. An override of a remaining flag requires a written reason. | Must | MD-005 |
| FR-007 | Editing an approved row returns it to pending, sends its verdict back through G2 once it is re-approved, and marks dependent calendar entries out of date. | Must | MD-005 |
| FR-008 | Load the mock fund profile, with fact IDs and event log. | Must | MD-002, MD-007 |
| FR-009 | Applicability agent gives a verdict with reasoning citing fact IDs for each approved row. | Must | MD-002 |
| FR-010 | G2: the specialist confirms or overrides each verdict. "Unsure" must be resolved by a human. | Must | MD-004 |
| FR-011 | Due-date code generates calendar entries within the demo horizon from approved, applicable rows. | Must | MD-006, MN-005 |
| FR-012 | Due-date code applies each row's business-day rule and the mock Luxembourg holiday list. | Must | MD-006 |
| FR-013 | Event-triggered rows generate entries from logged events, anchored on the awareness date. | Must | MD-007 |
| FR-014 | G3: the specialist publishes the fund's calendar to the GP view. | Must | MD-004, MN-003 |
| FR-015 | GP read-only view shows what, when, who and why for each published entry. | Must | MD-008, MN-007 |
| FR-016 | Every calendar entry has a stable ID. | Must | MD-010 |
| FR-017 | Audit log records every agent output and human decision. | Must | MD-009 |
| FR-018 | An evaluation run compares agent and calendar output with the answer key and writes a report. | Must | MP-001 to MP-004 |
| FR-019 | The specialist can view a row's full trail: source, quote, verifier flags, verdict, approvals. | Should | MP-005 |
| FR-020 | GP view shows a plain "not legal advice" note. | Should | MN-009 |
| FR-021 | **Stretch:** given an amendment, produce an impact report listing affected rows, verdicts and calendar entries with reasons, and send them back through G1 or G2. Unaffected items are left alone. | Could | MD-011, MN-003 |

## 5. Non-Functional Requirements

| ID | Category | Requirement | Traces to |
|----|----------|-------------|-----------|
| NFR-001 | Determinism | Due-date code gives identical output for identical approved inputs. No model calls in date calculation. | MP-007, MN-005 |
| NFR-002 | Traceability | Every row, verdict and calendar entry links to its source paragraph and the approvals behind it. | MP-005 |
| NFR-003 | Auditability | The audit log can be added to but not edited or deleted. | MP-008 |
| NFR-004 | Safety on failure | If an agent fails or returns invalid output, nothing moves forward and the failure is logged. A partial calendar is never published. | MN-003 |
| NFR-005 | Explainability | Verdict reasoning and GP "why" text are readable by a non-lawyer. | MD-008 |
| NFR-006 | Performance | See MC-001. | MC-001 |
| NFR-007 | Cost | See MC-002. | MC-002 |
| NFR-008 | Usability | See MC-003. | MC-003 |
| NFR-009 | Security and privacy | No secrets or real data in the repository. API keys come from local environment settings that git ignores. | MN-001 |
| NFR-010 | Access | GP access is read-only. Only the specialist role can approve, edit, reject or publish. Roles may be mocked for the MVP. | MN-003 |
| NFR-011 | Testability | Tests for gates, due-date calculation and the audit log run without calling a language model. Only agent evaluations need the live model. | MP-006, MP-007, MP-008 |

## 6. Constraints

- **Technology**: the runtime value in `aamad.config.yml` is `crewai`. The application pattern is not
  chosen in Define.
- **Timeline**: a six-week capstone.
- **Integration**: no live integrations. Email, regulator portals, holiday calendars and task tools are
  mocked or excluded.
- **Repository**: public. Real source material stays in the git-ignored `reference/` folder.

## 7. Assumptions

- **A-1**: One fund, one framework (Luxembourg UCI Part II) and the 6 mock source documents are enough
  to show the approach.
- **A-2**: *Resolved.* The cost and time targets MC-001 to MC-003 were confirmed by the operator.
- **A-3**: Business-day roll rules not confirmed by the operator default to "no roll, marked" (`D-6`).
- **A-4**: The subscription tax (AED) does not roll, the safe reading of the operator's tax guidance
  (`OQ-D3`).
- **A-5**: Specialist and GP roles can be mocked for the MVP (no real login). Operator-confirmed.
- **A-6**: G3 publishes a whole fund calendar at once, not entry by entry. Operator-confirmed.
- **A-7**: The date conventions given by the operator are correct. They have not yet been checked
  against the legal texts.
- **A-8**: Business-day and public-holiday rolls are **in scope** for the MVP, although the original brief
  named only "anchor + offset". Operator-confirmed. Scope fit to six weeks awaits the architect's
  estimate (PRD OQ-5).
- **A-9**: Filing parties are out of scope as users (operator decision). Each obligation's "who files"
  role is enough to route notifications to them later, together with filing status.

## 8. Acceptance Criteria

- **AC-001** (MD-001): Given the 6 mock source documents, when extraction runs, then exactly the 6 rows
  in the answer key are produced, each with a paragraph ID and a quote that appears word for word in
  that paragraph.
- **AC-002** (MD-001): Given `SRC-UCILAW-P1` (a definition), when extraction runs, then no row cites it.
- **AC-003** (MD-003): Given the rows and `SRC-PRACT`, when the verifier runs, then conflicts `C-1`
  (`OBL-03`) and `C-2` (`OBL-05`) are flagged and `OBL-01` has no conflict flag.
- **AC-004** (MD-003): Given a row whose quote has been altered by one word, when the verifier runs,
  then the quote check fails and the row cannot be approved.
- **AC-005** (MD-005): Given an approved row, when the specialist edits its offset, then the verifier
  re-runs on that row, the row returns to pending, and its calendar entries are marked out of date.
- **AC-006** (MD-005): Given a row with a remaining conflict flag, when the specialist approves it
  without a reason, then approval is refused. With a reason, it is approved and the reason is logged.
- **AC-007** (MD-002): Given the approved rows and fund `FND-DEMO-01`, when applicability runs, then
  verdicts match the answer key: 4 applies, `OBL-04` unsure, `OBL-06` does not apply.
- **AC-008** (MD-004): Given `OBL-04` is unsure, when the specialist tries to finish G2 without deciding
  it, then G2 cannot be completed.
- **AC-009** (MD-006): Given the answer key's approved rows and verdicts, when the calendar is
  generated, then it contains exactly the 22 entries in the answer key, with the same dates.
- **AC-010** (MD-006): Given `OBL-01` due Sunday 2027-01-10 with rule "roll forward", then the calendar
  date is Monday 2027-01-11 with a note that it moved.
- **AC-011** (MD-006): Given `OBL-05` due Sunday 2027-02-28 with rule "not confirmed", then the calendar
  date stays 2027-02-28 and is marked "roll rule unconfirmed".
- **AC-012** (MD-007): Given `EVT-01` (changed 2027-01-20, aware 2027-01-31), then the `OBL-05` entry is
  calculated from 2027-01-31, not 2027-01-20.
- **AC-013** (MN-003): Given a calendar that has not passed G3, when the GP view is opened, then it
  shows no entries for the fund.
- **AC-014** (MD-008): Given a published entry, when a GP views it, then it shows what, when, who and
  why, including the source citation and quote.
- **AC-015** (MP-007): Given the same approved inputs, when the calendar is generated twice, then both
  outputs are identical.
- **AC-016** (MD-009): Given a full demo run, then every agent output and human decision appears in the
  audit log with who, when and what.
- **AC-017** (MD-003): Given `OBL-02` with its offset changed to "+30 calendar days" but its quote
  unchanged ("within 20 calendar days…"), when the verifier runs, then an **internal** conflict is
  flagged, even though the quote check passes.

*Stretch goal (FR-021). Not part of the Week 6 definition of done.*

- **AC-018** (MD-011): Given the published calendar and amendment `AMD-01`, when impact is assessed,
  then only `OBL-03` is flagged and its calendar entry is marked out of date. `OBL-02` is not flagged.
- **AC-019** (MD-011): Given `AMD-02`, then `OBL-01` and `OBL-03` are flagged for applicability re-check
  at G2, and their 13 calendar entries are marked out of date. No other row is flagged.
- **AC-020** (MD-011): Given `AMD-03`, then nothing is flagged and the report states that the change is
  wording only.

## 9. Out of Scope / Future Work

**Out of scope for the MVP**
- Real client data, fund names or branding.
- Live email or any contact with external parties.
- **Filing parties as users** (AIFM, administrator, auditor, tax advisor, local reporting agent): no
  notifications, logins or confirmations. They appear only as each obligation's "who files" role (A-9).
- Task tools as the system of record.
- **Filing status** (filed, filed late, overdue), evidence of filing, confirmations from filing parties
  and reminders. Operator decision: the capstone tests rule generation, not filing tracking. A design
  for this exists outside the capstone. FR-016 keeps the path open.
- More than one fund, or frameworks other than Luxembourg UCI Part II.
- Obligations driven by an external published calendar, continuously monitored obligations and
  per-transaction reporting.
- Reading real regulatory documents (e.g. PDF parsing). The MVP reads mock text.
- Real authentication.
- Application pattern, full runtime roster and system architecture (SAD). Later sprints.

**Future work**
- Filing status and evidence, linked to calendar entries by stable ID.
- Notifying filing parties and collecting their confirmations, routed by each obligation's "who files"
  role.
- Multiple funds and frameworks, reusing approved libraries.
- An official holiday calendar source in place of the mock list.
- *(Moved to a stretch goal: impact of rule amendments, MD-011 / FR-021. Built only after the core,
  and it depends on the edit-and-re-verify chain in MD-005.)*

---

## Sources

- **SRC-BRIEF**: Operator brief for this capstone (problem, users, MVP scope, in/out of scope).
- **Operator decisions** made during the Define phase: source-text approach, the five obligations and
  the decoy, fund profile, approval gates, re-verification on edit, the GP view's four questions,
  filing status out of scope, and date conventions.
- `project-context/1.define/mrd.md`: evidence note.
- `project-context/1.define/mock-data/`: sources, fund profile, answer key.

## Assumptions

- See §7. A-5 (mocked roles) and A-6 (whole-calendar publish) began as PM recommendations and were then
  confirmed by the operator.
- User needs behind this document are inferred from the brief and internal documents. No user
  interviews were conducted (PRD A-7).

## Open Questions

- **OQ-1**: Should the GP view show a neutral note such as "1 possible obligation is under review by
  compliance"? **Decide before the UX step (`@ux.designer`).** Until then, nothing under review is
  shown.
- **OQ-2**: Business-day rules for Luxembourg Business Registers (`OBL-05`) and CNMV (`OBL-04`) filings.
  See answer key `OQ-D1`.
- **OQ-3**: *Resolved.* MC-001 to MC-003 confirmed by the operator.
- **OQ-4**: Does the AED subscription tax follow the "tax deadlines do not roll" rule? See answer key
  `OQ-D3`.
- **OQ-5**: The operator wants **four-eyes review** (a second, different specialist confirms before
  publish). **Timing is undecided:** MVP or a later version. Until decided, the MVP happy path has one
  specialist, and every approval records who made it (MD-009) so a second approver can be added.

## Audit

- 2026-11-06 · persona `product-mgr` · action `elicit-requirements` (written from the operator brief and
  Define-phase decisions) · runtime `crewai` (recorded, not evaluated)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · confirmed MC-001 to MC-003, A-5, A-6;
  closed OQ-3; noted four-eyes timing in OQ-5; added NFR-011 (testability); noted the private
  identifier list location in MN-001
- 2026-11-06 · persona `product-mgr` · action `update` · added design principle P-1 (cheaper mistake
  under uncertainty); demo calendar changed from 18 to 22 entries (operator chose `OBL-04` = applies,
  pending confirmation)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` (stories) · conflict check split into
  internal and cross-source (MD-003, FR-004, MP-003, new AC-017); edited approved rows re-enter G2
  (MD-005, FR-007); Spain note renamed "precautionary: registration unconfirmed"
- 2026-11-06 · persona `product-mgr` · action `readiness-check` · added A-8 (business-day rolls in scope,
  operator-confirmed)
- 2026-11-06 · persona `product-mgr` · action `update` · MC-003 measured from audit-log timestamps;
  MD-009 records gate opening (operator decision)
- 2026-11-06 · persona `product-mgr` · action `update` · change monitoring moved from future work to a
  stretch goal (MD-011, FR-021 Could, AC-018 to AC-020), operator decision
- 2026-11-06 · persona `product-mgr` · action `update` · problem statement enriched (overlapping layers);
  filing parties named as out-of-scope stakeholders (§1, A-9, §9), operator decision
