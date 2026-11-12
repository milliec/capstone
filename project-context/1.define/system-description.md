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
  | **GP / fund manager** | Accountable for the fund's filings, but files few of them. Often less familiar with Luxembourg rules *(unvalidated, A-10)*. | **Read only.** Sees what is due, when, who files it, and why. |
  | **Filing parties** (AIFM, administrator, auditor, tax advisor, local reporting agent) | Do most of the actual filings for the fund *(unvalidated, A-10)*. | **Nothing in the MVP.** Stakeholders, not users. Named on every obligation as "who files". |

- **Success definition (MVP)**: On the mock data set, the system produces the results in
  `mock-data/expected-obligation-library.md`. Every calendar entry traces back to a source paragraph and
  a specialist approval. Nothing reaches the GP view without passing all three approval gates.

## 2. Domain Context

### Vocabulary

| Term | Meaning |
|---|---|
| **Source paragraph** | One numbered paragraph of regulatory text, with a stable ID (e.g. `SRC-UCILAW-P3`). |
| **Obligation row** | One obligation in a fixed schema: what, recipient, who files, frequency, anchor, offset, applicability rule, business-day rule, source paragraph ID, verbatim quote. |
| **Human-created row** | An obligation row the specialist adds by hand at G1 because extraction missed it (FR-027). It is marked as human-created for good, and takes the same checks and its own G1 decision as any row. |
| **Obligation library** | All approved obligation rows for one regulatory framework. |
| **Applicability verdict** | For one fund and one row: **applies**, **does not apply** or **unsure**, with reasoning that cites fund facts. |
| **Anchor** | The reference date a deadline is calculated from: month-end, quarter-end, financial year-end, a fixed date, or an event's awareness date. |
| **Offset** | The time added to the anchor, e.g. "+10 calendar days" or "+6 months". |
| **Business-day rule** | Per obligation: **roll forward** to the next Luxembourg business day, **no roll**, or **not confirmed**. |
| **Calendar entry** | One dated occurrence of an applicable, approved obligation for the fund. It has a stable ID. |
| **Quote check** | The verifier step confirms, in deterministic code, that a row's quote appears word for word in its cited paragraph (normalisation rule: SAD QN-1). |
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
| MD-003 | Verify rows with a **separate** verifier agent | requirement | The verifier is not the agent that extracted the row. The verifier step runs a code-based quote check and a conflict check (internal and cross-source) on every row and reports flags. |
| MD-004 | Require specialist approval at three gates | requirement | **G1** rule approval (per row, after verification) · **G2** applicability approval (per verdict; "unsure" cannot pass without a human decision) · **G3** calendar publish (per fund). G1 and G2 offer approve / edit / reject for each item. G3 offers publish or decline (FR-022). |
| MD-005 | Re-verify after any edit | requirement | Editing a row re-runs the verifier on that row. A remaining flag can only be overridden with a written reason. Editing an approved row returns it to pending, sends its verdict back through G2 once it is re-approved, and marks dependent calendar entries out of date. |
| MD-006 | Calculate due dates with deterministic code | requirement | Dates come from approved rows only, using anchor + offset and conventions `D-1` to `D-7`. Each row's own business-day rule is applied. An unconfirmed rule keeps the earlier, unrolled date and marks it. |
| MD-007 | Handle event-triggered obligations | requirement | A logged event with an awareness date produces a calendar entry anchored on the **awareness** date. |
| MD-008 | Give GPs a read-only view of what is due and why | requirement | Each entry shows **what** (obligation + authority), **when** (date, plus a roll note if moved), **who** files, and **why** (plain-English reason + source citation and quote). |
| MD-009 | Keep an audit log | requirement | Every agent output and every human decision is recorded with who, when, what and (for overrides, rejections, reopenings (FR-023, FR-024), G3 declines and, in the stretch, sending an amendment for manual review (FR-026)) why. Every approval decision also records the version of the item it was made on: the row version for G1 approvals and rejections (including approvals over a flag) and for reopening a rejected row; the verdict version for G2 confirmations, overrides and decisions on "unsure", and for reopening a verdict; and the calendar version for G3 publishes and declines. In the stretch, impact-report decisions record the report and amendment versions instead (FR-026), and marking a manual review superseded is recorded as a **system event**, with the system as actor (not a human decision), the time, the triggering revision, the affected review and the old and new version references. How versions are identified and stored is for the SAD (approval map OD-11). Opening each gate is also recorded, so review time can be measured (MC-003). |
| MD-010 | Prepare for filing status later | requirement | Every calendar entry has a stable ID that a future filing record could reference. |
| MD-011 | **Stretch:** assess the impact of a rule amendment | requirement | Given an amendment to a source, the system identifies which rows, verdicts and calendar entries are affected (one, several or none), flags only those, and explains why. The change-monitoring system may update review status and flags (including marking entries out of date), but never changes the substance of a rule, applicability decision or deadline itself. Affected items go back through G1 or G2. Every impact report needs specialist acceptance or a documented manual review (FR-026). |

### Must not do

| ID | Item | Kind | Testable constraint |
|----|------|------|---------------------|
| MN-001 | Use real client data or branding | requirement | A scan of the repository for a private list of real identifiers returns no matches. The list lives in the git-ignored `reference/` folder and is never committed. |
| MN-002 | Contact external parties or live systems | requirement | No live email, regulator portal or task-tool calls. All externals are mocked. |
| MN-003 | Let agents move work past a gate | requirement | No row, verdict or calendar can reach the next step, or the GP view, without the matching gate approval. |
| MN-004 | Let the verifier resolve conflicts on its own | requirement | Conflicts are flagged for the specialist. The verifier never changes a row. |
| MN-005 | Let a language model calculate dates | requirement | Every due date is produced by deterministic code. Agent output contains no computed dates. |
| MN-006 | Accept a row without a source | requirement | A row with a missing paragraph ID or a failed quote check cannot be approved. |
| MN-007 | Show unfinished work to GPs | requirement | The GP view shows no pending, unsure, rejected or conflicted working content (see OQ-1). A neutral calendar-level review notice is permitted (FR-025). |
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
| FR-003 | The verifier step runs a code-based quote check on every row. | Must | MD-003, MN-006 |
| FR-004 | Verifier agent runs a conflict check on each row: internal (fields vs its own quote) and cross-source (against all other sources, primary and secondary). | Must | MD-003, MN-004 |
| FR-005 | G1: the specialist approves, edits or rejects each verified row and sets its business-day rule. *Edit deferred (DL-22): the MVP's G1 has approve and reject only.* | Must | MD-004 |
| FR-006 | Editing a row re-runs the verifier on that row. An override of a remaining flag requires a written reason. *Edit part deferred (DL-22); the part about overriding a remaining flag with a written reason stays in the MVP.* | Must | MD-005 |
| FR-007 | Editing an approved row returns it to pending, sends its verdict back through G2 once it is re-approved, and marks dependent calendar entries out of date. | Deferred (DL-22) | MD-005 |
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
| FR-020 | GP view shows one plain calendar-level note: entries are specialist-approved interpretations, not legal advice, and the date conventions have not yet been checked against the legal texts (A-7). *Raised from Should to Must, operator decision 2026-11-09; MN-009 already required the note.* | Must | MN-009, A-7 |
| FR-021 | **Stretch:** given an amendment, produce an impact report listing affected rows, verdicts and calendar entries with reasons, and send them back through G1 or G2. Unaffected items are left alone. | Could | MD-011, MN-003 |
| FR-022 | G3 decline: declining G3 requires a reason, publishes no new version and retains the draft and review history (including its evidence), visible to the specialist only. Any previously published version remains visible to GPs. In the MVP a decline ends the run as declined (terminal), and correcting the calendar means a new run. *The next-step choices, a rule needs correcting (go to G1) and a verdict needs review (return to G2 by reopening the verdict under FR-024), are deferred (DL-22).* Declining cancels no earlier G1 or G2 approval. | Must | MD-004, MD-009 |
| FR-023 | Reopen a rejected row: the specialist can reopen a rejected row, before or after publication. A reason is required, and the original rejection stays in the audit log. The row returns to pending, is re-verified, and needs fresh G1 approval and then a G2 verdict. Until those are complete, publishing a new calendar version is refused. GPs keep seeing the last published version until the specialist republishes. A rejected row is read-only: direct editing is refused until it is reopened, and after reopening normal pending-row editing applies (MD-005). *New scope decision (operator, 2026-11-07), supporting P-1; not implied by earlier requirements. Scope is limited to this recovery path; it is not a general undo system.* | Deferred (DL-22) | MD-004, MD-005, MD-009, P-1 |
| FR-024 | Reopen a confirmed verdict: the specialist can reopen a confirmed or overridden G2 verdict, before or after publication, to correct a judgement while the rule and the relevant fund facts are unchanged. A reason is required. The original decision and the agent's reasoning stay in the audit log. The rule keeps its G1 approval, and the applicability agent is not re-run. The verdict returns to pending G2, its calendar entries are marked out of date, and publishing a new version is refused until G2 is complete and the dates are regenerated. GPs keep seeing the last published version. The specialist must finish with "applies" or "does not apply", and an override still needs a reason. If the rule has changed, the edit path applies instead (MD-005). Fund facts are static in the MVP, so reassessment after a fact change is not defined (OQ-9). *New scope decision (operator, 2026-11-07).* | Deferred (DL-22) | MD-004, MD-009, FR-022, P-1 |
| FR-025 | Published-calendar review notice: when a change calls the currently published calendar's accuracy or completeness into question, the GP view shows a neutral, calendar-level review notice. Triggers: an edit to an approved row the published version used (MD-005); reopening a verdict the published version used, including a "does not apply" decision that excluded an obligation (FR-024); reopening a rejected row for the published calendar's fund and regulatory scope (FR-023); and, only if the stretch is built, an impact flag on a published item (MD-011). Unrelated draft work does not trigger it. The last published entries stay visible with their publication date. No draft content, flag detail or specialist reasoning is shown. The notice clears only when a replacement calendar is successfully published; a declined (FR-022) or failed publication does not clear it. Exact wording is set at the UX step. *Limit: the notice warns of uncertainty; it does not by itself prevent reliance on an incorrect date.* *New scope decision (operator, 2026-11-07).* | Deferred (DL-22) | MN-007, FR-015, P-1 |
| FR-026 | **Stretch:** impact-report acceptance. Whenever change monitoring is built, every impact report needs specialist acceptance or a documented manual review, including reports with flags and "no impact" reports. This is a separate review step, not a replacement for G1 to G3. Acceptance confirms the assessment only. It does not approve or apply any regulatory change, clear flags, restore invalidated approvals or clear the GP review notice, and flagged items still need their own G1 or G2 review. Instead of accepting, the specialist can send the amendment for manual review with a logged reason. It stays open until the specialist explicitly completes it with a completion note that records the conclusion and references any resulting corrections, or explains why none were needed. Corrections use existing paths (MD-005, FR-023, FR-024). Neither sending for nor completing a manual review clears flags, restores approvals or bypasses G1 to G3, and sending for manual review does not resolve the amendment. The specialist sees a visible queue of amendments not yet accepted or completed. Acceptance, sending for manual review and completing a manual review each record the actor, the time, the exact report version and the exact source amendment version decided on, plus the required reason (sending) or completion note (completing); identifier design is for the SAD (approval map OD-11). A decision covers only the report and amendment versions it names: if either is revised, the earlier decision does not carry over, the amendment returns to unreviewed and needs a fresh acceptance or manual review, and the earlier decision stays in the audit log. If either is revised while a manual review is still open, that review is marked superseded and keeps its notes and version references; the amendment stays unresolved in the specialist's queue, linked to the new report and amendment versions; the specialist can consult the earlier notes, but must make an explicit completion decision for the current versions, and completion against a superseded version is refused. Once an amendment has been referred for manual review, accepting a revised report does not close it: the new report is evidence for the review, and the amendment closes only when the specialist completes the manual review with a completion note against the current versions. Superseding a review does not clear impact flags or the GP review notice, restore approvals or bypass G1 to G3. The GP review notice stays tied to concrete impact flags (FR-025). *Limit: an unaccepted amendment may contain an undiscovered impact, so the absence of a notice does not mean the calendar has been checked against it. Human sign-off reduces the risk of a silent miss; it does not guarantee completeness.* *Operator decision, 2026-11-07.* | Could | MD-011, FR-025, P-1 |
| FR-027 | Create a missed row by hand: at G1 the specialist can open the edit form on an empty row and enter a paragraph ID, a quote and the other fields. No model is involved and there is no "re-extract" action. The row is stored as human-created, with the creator's identity; the marking cannot be changed. The quote check cannot be skipped: a row with no paragraph ID, or a quote not found word for word in the cited paragraph, cannot be approved (MN-006). The conflict checks run on it (FR-004) and it needs its own G1 decision (FR-005, AC-026). The evaluation report counts human-created rows on a separate line, so they neither inflate nor hide the extractor's result (FR-018). *New scope decision (operator, DL-15, 2026-11-11).* | Deferred (DL-22) | MD-005, MD-009, MN-006, P-1 |
| FR-028 | Coverage view at G1: G1 lists every loaded source paragraph that no non-rejected row cites, each with its text. It is a set difference between the loaded paragraph IDs and the IDs that non-rejected rows cite (human-created rows count, FR-027; a paragraph whose only row was rejected is listed again, so the specialist sees it, and it leaves the list if the row is reopened under FR-023). It does not use the answer key at run time and makes no claim about which uncited paragraphs contain an obligation; it only makes a possible gap visible, because a missed row is the costliest error (P-1). It does not block G1. A real gap is fixed by creating a row (FR-027, deferred: in the MVP a missed row means a new run, DL-22). *Raised with the SAD (W-03b); operator context DL-15, 2026-11-11.* | Must | MD-001, MD-004, P-1 |
| FR-029 | Possible-duplicate groups at G1: code (never a model) groups rows that may describe one obligation, across documents or between a primary source and a secondary summary, and G1 shows each group with a plain warning and every row's quote and source. Grouping does not block any single row; each row keeps its own explicit decision (AC-026). If a group still has two or more approved rows when the specialist completes G1, completion needs one confirmation with a written reason, logged with the rows' IDs and versions. If groups cannot be computed, G1 does not open. Grouping rules: SAD W-03a. *Operator decision (DL-16, 2026-11-11).* | Deferred (DL-22) | MD-004, MN-004, P-1 |
| FR-030 | G3 acknowledgement of what was left out: before publishing, G3 shows every row rejected at G1 (with the reason given at rejection) and every loaded source paragraph that no non-rejected row cites (with its text, as in FR-028). Publishing requires **one explicit acknowledgement** of both lists, given as part of the publish decision. It is never preselected and never given by a timeout or by closing the screen. Publishing is refused without it, or if either list has changed since it was shown. The acknowledgement is recorded in the audit log with who, when, and the rows (with their versions) and paragraphs it covered. It applies to publishing only, not to a decline (FR-022). In the demo the 3 `SRC-PRACT` summaries are always uncited, so the acknowledgement appears on every publish. *Operator decision (DL-30, 2026-11-12).* | Must | MD-004, MD-009, MN-003, P-1 |
| FR-031 | Labelled demo switch: when starting a run, the specialist can turn on a run-level demo switch. It is **off by default**, and turning it on is recorded in the audit log. When on, code (never the extractor) adds **one** planted row from a fixed demo fixture: a real quote, verbatim in its paragraph, that does not support the row's rule, so the quote check passes and the specialist is expected to reject it at G1. The row is marked "demo" wherever it appears (G1, the G3 rejected list, run status, audit log). The switch adds a row and never approves anything: approving a demo row is refused, the refusal is recorded in the audit log, and a plain message explains it; the only decision on a demo row is reject with a written reason. An evaluation run refuses to start with the switch on. The switch is not a role switcher: roles stay on the mock sign-in. *Operator decisions (DL-31, SAD SOQ-18, 2026-11-12).* | Must | MD-004, MD-009, MN-003, MP-001 |

## 5. Non-Functional Requirements

| ID | Category | Requirement | Traces to |
|----|----------|-------------|-----------|
| NFR-001 | Determinism | Due-date code gives identical output for identical approved inputs. No model calls in date calculation. | MP-007, MN-005 |
| NFR-002 | Traceability | Every row, verdict and calendar entry links to its source paragraph and the approvals behind it. | MP-005 |
| NFR-003 | Auditability | The audit log can be added to but not edited or deleted. | MP-008 |
| NFR-004 | Safety on failure | If an agent fails or returns invalid output, nothing moves forward and the failure is logged. A partial calendar is never published. Work is done per unit (a source document at extraction, a row at verification and applicability). A failed unit does not discard the valid output of other units; it is marked re-runnable, and the gate after its step stays closed until every unit has valid output. A re-run replaces only that unit's output and leaves finished units and recorded gate decisions untouched. The specialist can re-run a unit up to 3 times for the same input, then it is marked "needs attention". A source document in that state can be released to manual entry by the specialist, with a written reason, one document at a time: it then no longer holds G1 closed, every other unit must still be valid, the release is audited, and the evaluation report counts it as an extraction failure. A row unit (verification, applicability) has no release. *Operator decision (DL-18, 2026-11-11).* *DL-22: the re-run, "needs attention" and release sentences above are deferred. In the MVP a failed step ends the run as failed and the specialist starts a new run, or abandons an active run with a written reason (SAD run state model; US-015 criteria 19–21).* | MN-003 |
| NFR-005 | Explainability | Verdict reasoning and GP "why" text are readable by a non-lawyer. | MD-008 |
| NFR-006 | Performance | See MC-001. | MC-001 |
| NFR-007 | Cost | See MC-002. | MC-002 |
| NFR-008 | Usability | See MC-003. | MC-003 |
| NFR-009 | Security and privacy | No secrets or real data in the repository. API keys come from local environment settings that git ignores. | MN-001 |
| NFR-010 | Access | GP access is read-only. Only the specialist role can approve, edit, create a row by hand (FR-027), reject, override, reopen (FR-023, FR-024), publish (with the G3 acknowledgement, FR-030) or decline (FR-022), abandon a run waiting at a gate (AC-035), turn on the demo switch when starting a run (FR-031), and, in the stretch, accept impact reports or send them for manual review (FR-026). Naming "override" adds no permission: it covers only the existing approval over a remaining conflict flag (AC-006) and the G2 verdict override (FR-010), both with a reason. Checks that cannot be overridden stay so: a failed quote check or missing paragraph ID (MN-006), "unsure" at G2 close (AC-008), and publishing with gates incomplete or entries out of date (MP-006). Roles may be mocked for the MVP. | MN-003 |
| NFR-011 | Testability | Tests for gates, due-date calculation and the audit log run without calling a language model. Only agent evaluations need the live model. | MP-006, MP-007, MP-008 |
| NFR-012 | Extensibility (architecture quality goal) | The MVP is built as the **first validated configuration of a shared product**, not a bespoke implementation (§10). The SAD (a) names the shared capabilities, the configuration and the defined extension points; (b) walks through scenarios S-1 and S-2 (§10.4) separately and shows, for each, what would be configuration, what would need an extension point and what would stay unchanged, with no client-specific copy of a shared capability; and (c) shows how the extension rules EX-1 to EX-6 (§10.3) would be checked. The MVP builds only the Luxembourg UCI Part II configuration. No extension, extra configuration or configuration screen is in the MVP. *Operator decision, 2026-11-08.* | §10, MP-001 to MP-008 |

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
- **A-10**: The user descriptions in §1 are **unvalidated**. That GPs are often less familiar with
  Luxembourg rules, and that filing parties do most of the filings, come from the brief and the
  illustrative scenario (MRD SRC-ILLUS). No users were interviewed. The same applies to GPs as the expected future buyer
  (§10.1): it is the operator's expectation, not a finding.

## 8. Acceptance Criteria

- **AC-001** (MD-001): Given the 6 mock source documents, when extraction runs, then exactly the 6 rows
  in the answer key are produced, each with a paragraph ID and a quote that appears word for word in
  that paragraph.
- **AC-002** (MD-001): Given `SRC-UCILAW-P1` (a definition), when extraction runs, then no row cites it.
- **AC-003** (MD-003): Given the rows and `SRC-PRACT`, when the verifier runs, then conflicts `C-1`
  (`OBL-03`) and `C-2` (`OBL-05`) are flagged and `OBL-01` has no conflict flag.
- **AC-004** (MD-003): Given a row whose quote has been altered by one word, when the verifier runs,
  then the quote check fails and the row cannot be approved.
- **AC-005** (MD-005): *Deferred (DL-22).* Given an approved row, when the specialist edits its offset, then the verifier
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
- **AC-013** (MN-003, MN-007): Given a calendar that has not passed G3, when the GP view is opened,
  then it shows no entries for the fund and a read-only empty state with the message "Your obligations calendar is being prepared and checked by a specialist. Nothing has been published yet." It shows
  no count, status or draft content, and no notification is sent. *Detail: US-011 criterion 7; decision
  log DL-27.*
- **AC-014** (MD-008): Given a published entry, when a GP views it, then it shows what, when, who and
  why, including the source citation and quote.
- **AC-015** (MP-007): Given the same approved inputs, when the calendar is generated twice, then both
  outputs are identical.
- **AC-016** (MD-009): Given a full demo run, then every agent output and human decision appears in the
  audit log with who, when and what, and every approval decision names the row, verdict or calendar
  version it was made on.
- **AC-017** (MD-003): Given `OBL-02` with its offset changed to "+30 calendar days" but its quote
  unchanged ("within 20 calendar days…"), when the verifier runs, then an **internal** conflict is
  flagged, even though the quote check passes.

*Recovery paths and explicit decisions (added 2026-11-07). Each criterion states the observable
outcome; the linked story criteria hold the detail.*

- **AC-021** (FR-022): Given a generated calendar, when the specialist declines G3 without a reason,
  then the decline is refused. With a reason, no new version is published, the draft and its review
  history stay available to the specialist, any previously published version stays visible to GPs, no
  G1 or G2 approval changes, and the run ends as declined (terminal). *Detail: US-010 criteria 8–9.*
- **AC-022** (FR-023): *Deferred (DL-22).* Given a rejected row, when the specialist edits it directly or reopens it without
  a reason, then both are refused. When it is reopened with a reason, the row returns to pending and is
  re-verified, G1 is incomplete until the row is decided again, its verdict then needs G2, and
  publishing a new version is refused until both are done. The original rejection stays in the audit
  log. *Detail: US-004 criteria 9–11.*
- **AC-023** (FR-024): *Deferred (DL-22).* Given a confirmed verdict, when the specialist reopens it without a reason, then
  reopening is refused. With a reason, the verdict returns to pending G2 while its rule keeps its G1
  approval, the applicability agent does not re-run, the verdict's calendar entries are marked out of
  date, and publishing is refused until G2 is complete and the dates are regenerated. The original
  decision stays in the audit log. *Detail: US-007 criteria 8–9.*
- **AC-024** (FR-025): *Deferred (DL-22).* Given a published calendar, when an approved row it used is edited, a verdict it
  used is reopened (including `OBL-06`'s "does not apply"), or a rejected row in its scope is reopened,
  then the GP view shows a neutral calendar-level review notice with the last published entries and
  their publication date, and no draft content, flag detail or reasoning. Draft work that does not
  affect the published calendar shows no notice. The notice clears only when a replacement calendar is
  successfully published; a declined or failed publication leaves it in place. *Detail: US-011
  criteria 9–10; stretch trigger in US-014 criterion 10.*
- **AC-026** (MD-004, PRD §6): Given the G1 and G2 review screens, then there is no bulk approve or
  confirm action and no row or verdict has a preselected decision; each decision is a separate,
  explicit action logged on its own. When the specialist closes the screen, the session times out or
  nothing is done, undecided items stay pending, the gate stays incomplete, and decisions already
  recorded stay intact. Safe default values (such as the business-day rule "not confirmed") may still
  be shown as proposed values. G3 remains one explicit decision for the whole calendar, never
  preselected and never triggered by a timeout or by closing the screen. *Detail: US-004 criteria
  12–13, US-007 criteria 10–11, US-010 criterion 10; stretch: US-014 criterion 15.*
- **AC-027** (FR-027, MN-006): *Deferred (DL-22).* Given the G1 screen and an empty row, when the specialist enters a quote
  that does not appear word for word in the cited paragraph, or no paragraph ID, then the row cannot be
  approved. With a valid paragraph ID and a passing quote, the row is saved as human-created, the
  conflict checks run, it needs its own G1 decision, and its audit entry shows the origin "human". No
  model is called to create it. The evaluation report lists human-created rows on a separate line.
  *Detail: US-016, US-013 criterion 8.*
- **AC-028** (FR-029, MD-004): *Deferred (DL-22).* Given two rows that cite the same source paragraph, when G1 opens, then
  they are shown as one "possible duplicates" group with a warning, and each still needs its own
  decision. When both are approved and the specialist completes G1 without a reason, completion is
  refused; with a reason, G1 completes and the audit log records the reason and both rows' IDs and
  versions. A group with one or no approved rows needs no confirmation. *Detail: US-004 criteria
  14–16.*
- **AC-029** (FR-028, MD-001): Given the 13 mock source paragraphs and the 6 extracted rows, when G1
  opens, then the coverage view lists the 7 paragraphs that no non-rejected row cites, with their text,
  and none of the 6 that rows cite. When the specialist creates a row citing one of the 7, it leaves the list. If
  the only row citing a paragraph is rejected, the paragraph appears in the list again. The
  view does not use the answer key, says nothing about which paragraphs hold obligations, and does not
  block G1. *Detail: US-001 criteria 8–10.*
- **AC-030** (NFR-004, MN-003): *Re-run part deferred (DL-22): in the MVP a failed unit ends the run as failed; the parts about naming the failed unit and keeping the gate closed stay.* Given applicability output that is invalid for `OBL-04` only, when the
  step finishes, then the other five verdicts are kept, G2 does not open, and run status names
  `OBL-04` as failed. When only `OBL-04` is re-run and succeeds, G2 opens with six verdicts and no
  duplicates, and earlier gate decisions are unchanged. A unit that fails 3 re-runs for the same input
  is marked "needs attention". *Detail: US-015 criteria 9–13, US-001 criterion 7, US-006 criterion 7.*
- **AC-031** (NFR-004, DL-18): *Deferred (DL-22).* Given one source document whose extraction has failed 3 re-runs, when
  the specialist tries to release it without a reason, or before the limit, then the release is
  refused. With a reason, while another unit is still invalid, G1 stays closed. Once every other unit
  is valid, G1 opens; the released document's paragraphs appear in the coverage view; the audit log
  records the release; and the evaluation report counts one extraction failure. A verification or
  applicability unit at the limit offers no release. *Detail: US-015 criteria 14–15, US-016
  criterion 11, US-013 criterion 9.*
- **AC-032** (PRD OQ-7, DL-20): Given the AED subscription-tax question is open (SD OQ-4), when the
  demo calendar is generated, then at G1 the form for `OBL-02`'s business-day rule shows that the rule
  depends on that question, and at G3 all four `OBL-02` entries carry a mark saying so, shown with the
  other safe-default marks. No other entry carries it. The mark does not block publishing, the GP view
  shows no such mark, and the four dates (20 January, 20 April, 20 July, 20 October 2027) are the same
  under "no roll" and "roll forward". The date code has no built-in rule for `OBL-02`: a row whose
  rule is unset stays "not confirmed". *Traces to SAD CR-027, tests T-W13-1 and T-W13-2. Detail:
  US-004 criterion 17, US-010 criterion 12, US-011 assumptions.*
- **AC-033** (NFR-004, MN-003): Given a model step returns output that fails its schema, or a call fails
  after its one automatic retry, when the stage ends, then the run moves to **failed** (terminal). Run
  status names the step, the unit and the reason, no gate opens for the failed stage, and decisions
  already recorded stay as they were. *Detail: US-015 criterion 19; SAD test T-RUN-1.*
- **AC-034** (NFR-004, MN-003): Given a step that never returns, when its time limit passes, then the
  unit fails and the run moves to **failed** as in AC-033, so a hang cannot keep a run active.
  Given a stage that passes its stage time limit, then the stage ends and the run moves to **failed**
  in the same way. Given the backend restarts while a stage is running, then on start-up that run
  moves to **failed** with the reason "service restarted", recorded as a system event; a run waiting
  at a gate is unaffected. *(DL-29, superseding DL-28.)* *Detail: US-015 criterion 19 and the restart
  note; SAD test T-RUN-2 and run state model rules 6–7.*
- **AC-035** (NFR-004, MD-009, MN-003, NFR-010): Given an active run **waiting at G1, G2 or G3**,
  when the specialist abandons it without a written reason, then it is refused. Given a run whose
  stage is still running, then abandoning it is refused with a plain message, and the stage ends by
  itself (AC-034) *(DL-29)*. With a reason, a run waiting at a gate closes as **abandoned**, one audit
  entry records who, when, the reason and the stage, and nothing is undone: decisions, rows, verdicts,
  drafts, the audit log and any published calendar stay as they were, and GPs keep seeing the last
  published version. Abandoning a run that is not active, on an out-of-date screen, or twice is refused.
  This is not a general cancel. *Detail: US-015 criteria 20–21; SAD tests T-RUN-3 and T-RUN-4.*
- **AC-036** (PRD A-6, NFR-004): Given a run that is failed, declined or abandoned (or completed), when
  the specialist starts a new run, then it is allowed. Given a run that is still active, it is refused
  with a message that names the active run. *Detail: US-015 criterion 16; US-010 criterion 8; SAD tests
  T-RUN-0, T-RUN-1, T-RUN-3 and T-RUN-5.*
- **AC-037** (FR-030, MD-009, P-1): Given a generated calendar for a run in which one row was rejected
  at G1, when the specialist opens G3, then it lists that row with its rejection reason and every
  paragraph no non-rejected row cites, with its text. (In the demo run, the rejected list is the demo
  row, FR-031, and the uncited list is the 7 paragraphs of AC-029: a rejected row cites nothing.)
  Publishing without the acknowledgement is refused. Publishing with an acknowledgement made
  for lists that have since changed (for example a row rejected after the page loaded) is refused.
  With the acknowledgement of the current lists, the calendar is published and the audit log records
  the rows (with versions) and paragraphs acknowledged. The acknowledgement is never preselected. A
  decline needs no acknowledgement. *Detail: US-010 criterion 14; SAD CR-028, test T-G3ACK-1.*
- **AC-038** (FR-031, MD-009, MN-003, MP-001): Given a run started with the demo switch off (the
  default), then G1 shows the 6 extracted rows and no demo row, and the audit log has no switch entry.
  Given a run started with it on, then G1 shows 7 rows; the 7th is marked "demo" and passes the quote
  check, and the audit log records that the switch was turned on. Approving the demo row, with or
  without a reason, is refused with a plain message and the refusal is logged; the row stays pending
  and G1 cannot complete until it is rejected. Rejecting it with a reason is accepted and logged, and it
  then appears in the G3 rejected list (AC-037). After that rejection, the calendar is the same 22
  entries as with the switch off. Starting an evaluation run with the switch on is refused. *Detail:
  `user-stories/README.md`, "Demo decisions"; SAD CR-029, tests T-DEMO-1 and T-DEMO-2.*

*Stretch goal (FR-021, FR-026). Not part of the Week 6 definition of done.*

- **AC-018** (MD-011): Given the published calendar and amendment `AMD-01`, when impact is assessed,
  then only `OBL-03` is flagged and its calendar entry is marked out of date. `OBL-02` is not flagged.
- **AC-019** (MD-011): Given `AMD-02`, then `OBL-01` and `OBL-03` are flagged for applicability re-check
  at G2, and their 13 calendar entries are marked out of date. No other row is flagged.
- **AC-020** (MD-011): Given `AMD-03`, then nothing is flagged and the report states that the change is
  wording only.
- **AC-025** (FR-026; applies only if the stretch is built): Given any impact report, including
  `AMD-03`'s "no impact", then the amendment stays unreviewed in the specialist's queue until the report
  is accepted or a manual review is completed. Accepting changes the review status only: flags stay,
  invalidated approvals are not restored, flagged items still need G1 or G2, and any GP review notice
  stays. Sending for manual review requires a reason, and the amendment stays open until it is
  completed with a completion note. Each of these decisions names the report and amendment versions it
  was made on; when either is revised, the amendment returns to unreviewed and the earlier decision
  stays in the log. If the revision happens during an open manual review, that review is marked
  superseded with its notes kept, the amendment stays in the queue, accepting the revised report does
  not close it, and completion is accepted only for the current versions. The superseding appears in
  the audit log as a system event with the triggering revision and the old and new version references.
  *Detail: US-014 criteria 11–17.*

## 9. Out of Scope / Future Work

**Deferred by decision DL-22 (written down and designed in the SAD, not built in the MVP).** The MVP is
the thin slice: one complete happy path. Deferred: edit and re-verify (FR-006 edit part, FR-007, AC-005);
reopen a rejected row (FR-023, AC-022); reopen a verdict (FR-024, AC-023); the GP review notice
(FR-025, AC-024); re-running a failed step, "needs attention" and releasing a failed document
(NFR-004 sentences, AC-030 re-run part, AC-031); manual row creation (FR-027, AC-027); duplicate groups
and the completion confirmation (FR-029, AC-028); the verifier and judge dead-end handling (SAD
SOQ-10); the impact report (FR-021, FR-026, stretch, unchanged); the extra CI checks, the circuit
breaker and the restart sweep that marks units re-runnable. The list by story is in
`user-stories/README.md`, "Scope status (DL-22)". *Not deferred (DL-29, superseding DL-28):* the
start-up rule that fails a run interrupted mid-stage ("service restarted", AC-034) is in the MVP, so
the earlier known limitation (abandon an interrupted run by hand) no longer applies.

**Known MVP limitation (OQ-US001-2, accepted by the operator, 2026-11-12).** There is no way to mark a
source paragraph as read and holding no obligation. The coverage view (FR-028) shows such a paragraph as
uncovered, as a warning, on every run. A "reviewed, no obligation" mark is future scope.

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
- **Additional clients, other regimes (for example a RAIF) and other marketing jurisdictions (for
  example Singapore).** These are explored only as architecture walkthroughs (§10.4). They are not
  built, and they are not a promise of regulatory coverage. *(Operator decision, 2026-11-08.)*
- **Fund-fact editing.** Fund facts are static mock data in the MVP. *(Operator decision,
  2026-11-08; see also Future work, fund-fact changes.)*
- **Configuration screens**, and any feature for editing client policy. *(Operator decision,
  2026-11-08.)*
- **Separating one client's data from another's.** Deferred. The SAD names the future boundary only
  (§10.5).
- Obligations driven by an external published calendar, continuously monitored obligations and
  per-transaction reporting.
- Reading real regulatory documents (e.g. PDF parsing). The MVP reads mock text.
- Real authentication.
- Application pattern, full runtime roster and system architecture (SAD). Later sprints.
- **Withdrawing or unpublishing** a published calendar or entry. Operator decision: deliberately
  deferred for this bounded demonstration. It is not judged unnecessary or inherently less safe.
  Recovery in the MVP is: review notice (FR-025) → correct (FR-022 to FR-024, MD-005) → republish. One
  fictional fund removes the cross-fund publication case, but a calendar can still be wrong throughout.
  **Revisit before real-world use**, where leaving seriously misleading information visible could itself
  cause harm.

**Future work**
- Filing status and evidence, linked to calendar entries by stable ID.
- Notifying filing parties and collecting their confirmations, routed by each obligation's "who files"
  role.
- Multiple funds and frameworks, reusing approved libraries.
- An official holiday calendar source in place of the mock list.
- **Fund-fact changes** (operator decision; direction only, not designed). When a fund fact changes,
  identify affected applicability decisions, invalidate their approvals and derived calendar entries,
  reassess applicability using the updated facts, and require fresh G2 confirmation before
  republishing. Where the published calendar is affected, show the review notice (FR-025). Dependency
  detection must account for newly applicable obligations, not only existing fact citations. FR-024's
  judgement-only reopening is not the path for this, because its inputs must stay unchanged.
- *(Moved to a stretch goal: impact of rule amendments, MD-011 / FR-021. Built only after the core,
  and it depends on the edit-and-re-verify chain in MD-005.)*
- **Client-policy changes** (future requirement; §10.2).

## 10. Extensibility (architecture quality goal)

*Added 2026-11-08 by operator decision. This section sets a quality goal for the architecture. It adds
no MVP feature and changes no MVP requirement. The mechanisms are for the SAD (`@system.arch`).*

### 10.1 Product framing

- **The capstone stays an internal specialist tool, designed for future reuse.** The MVP is the
  **first validated configuration** of a shared product, not a bespoke build for one client. Later
  clients, regimes and jurisdictions should reuse the same capabilities through configuration and
  defined extension points, not through client-specific copies.
- **The future buyer is expected to be the GP** (general partner / fund manager), who uses the GP view
  of the compliance calendar. This names the buyer only. It adds no GP feature to the MVP or to agreed
  future scope. It is the operator's expectation and has not been validated (A-10).
- **Market research is revisited before commercialising, not to complete this MVP.** The MRD's
  internal-tool framing (`mrd.md`, A-4) and the PRD's "not sold" assumption (PRD A-1) still describe
  the capstone. They were not written for a commercial product.
- **The MVP is unchanged:** one fictional Luxembourg UCI Part II fund (`FND-DEMO-01`) with static fund
  facts.

### 10.2 Kinds of expected variation

Future configurations are expected to differ in three ways. They are kept apart because each has a
different owner and a different way of changing.

| Kind | Driven by | Examples | In the MVP |
|---|---|---|---|
| **Regulation** | Law and regulator guidance, interpreted by a specialist | Legal regime, marketing jurisdiction, authorities, source documents, obligations, anchors and offsets, business-day rules, holiday calendars | Mock sources, answer key, conventions `D-1` to `D-7` (fixed) |
| **Fund terms** | The fund's documents and records | Legal form, domicile, financial year-end, dealing frequency, investor types, marketing countries and marketing status, registrations, appointed filing parties ("who files") | Mock fund profile `FACT-01` to `FACT-07` (static) |
| **Client policy** | Choices a client makes within what regulation allows | Default for unconfirmed roll rules (A-3, `D-6`), precautionary treatment (P-1), internal lead times ahead of legal deadlines, four-eyes review (OQ-5), notice wording | Fixed values in the Define documents |

**Client policy cannot override mandatory controls.** It may add controls or set stricter values. It
may never remove, bypass or weaken the controls in EX-3 or any mandatory regulatory requirement.

**Future requirement for client-policy changes** (not in the MVP; no policy-editing feature is built).
A change to client policy needs an authorised decision, a reason, version history, and an assessment of
the work it affects (rows, verdicts and calendar entries). The SAD proposes the mechanism.

### 10.3 Extension rules

Every future extension (a new regime, jurisdiction, client, obligation set or convention) must meet
these rules.

| ID | Rule |
|---|---|
| EX-1 | **Shared first.** An extension uses shared capabilities with configuration or a defined extension point. A client-specific copy of a shared capability is not the default; any exception is recorded with its reason in the SAD. |
| EX-2 | **Validated behaviour is preserved.** After any extension, the evaluation of the Part II demo set (FR-018) still matches the answer key exactly: 6 rows, 6 verdicts, the expected verifier flags and 22 calendar entries (MP-001 to MP-004). |
| EX-3 | **Controls are preserved.** No extension or configuration removes, bypasses or weakens the separate verifier (MD-003, MN-004), the three gates (MD-004, MN-003), deterministic dates (MN-005, NFR-001), source links (MN-006), the add-only audit log with versioned decisions (MD-009, NFR-003), role limits (NFR-010) or the rule that GPs see only published content (MN-007). |
| EX-4 | **Specialist validation.** Before use, each extension is validated by a compliance specialist qualified for that regime or jurisdiction. The validation is recorded. |
| EX-5 | **Its own tests.** Each implemented extension addresses the relevant kinds of check in MP-001 to MP-008 with its own evidence (for example its own mock sources, fund facts and expected results), plus the EX-2 regression. A kind of check may be marked "not applicable" with a recorded justification. The extension's fixtures and counts need not match the Part II demo set. For the paper walkthroughs (§10.4), the tests are identified only, not built or run. |
| EX-6 | **No coverage promise.** An extension point or walkthrough is not a claim of regulatory coverage (`mrd.md` §5). |

### 10.4 Architecture walkthroughs

Two walkthroughs test extensibility **on paper**. **They do not promise regulatory coverage.** Each
starts from the MVP baseline on its own; they are not combined. Nothing in them is built, and no mock
data is added for them. Any regulatory difference named below is a question for a specialist, not a
finding.

**For each walkthrough, the SAD should show:**

- what is shared and unchanged;
- what is configuration, and which kind it is (regulation, fund terms or client policy);
- what needs a defined extension point;
- how EX-1 to EX-6 would be met;
- which tests EX-5 would need, for each kind of check in MP-001 to MP-008 (or why it is not
  applicable). The tests are identified, not built or run;
- what a specialist must validate.

#### S-1: a fictional Luxembourg RAIF

A second, fictional fund set up as a Luxembourg reserved alternative investment fund (RAIF).

- **Regulation (may differ, to be validated):** the governing law, how the fund is supervised (for
  example through its authorised AIFM rather than direct product authorisation), which authorities
  receive filings, which obligations exist, and their deadlines and tax treatment. Some Part II rows may
  not apply; others may be new.
- **Fund terms:** a new fund profile with its own fact IDs.
- **Client policy:** may be the same as for the Part II fund, or different.
- **Tests the architecture on:** adding a regime and a second fund without copying the extraction,
  verification, applicability, gate, date or audit capabilities.

#### S-2: the Part II fund considering marketing in Singapore

The existing fictional Part II fund (`FND-DEMO-01`) is **considering** marketing to institutional
investors in Singapore.

- **Marketing is not assumed to be permitted.** Whether the fund may be offered in Singapore, and on
  what basis, is a specialist's question. The system does not decide it.
- **Considered is not active.** A jurisdiction being considered is a different fund-term state from an
  approved or active marketing arrangement, just as "marketed" and "registered" are different states
  for Spain (`FACT-03`, `FACT-04`).
- **Conditional assessment.** Obligations are assessed against the stated hypothetical ("if the fund
  were marketed to institutional investors in Singapore on a given basis"). Conclusions are labelled
  **conditional**, and marketing permission is kept separate from obligation applicability.
- **P-1 in this case.** Uncertainty prompts specialist review. It must not silently become "applies",
  and nothing may imply that marketing is authorised. *(Operator decision, 2026-11-08; see OQ-11.)*
- **Regulation (may differ, to be validated):** Singapore sources and authority, the obligations tied
  to any marketing basis, a Singapore business-day calendar.
- **Fund terms:** marketing status and investor type for Singapore.
- **Client policy:** for example, whether to prepare a conditional calendar before a marketing decision.
- **Tests the architecture on:** adding a jurisdiction to an existing fund without changing its
  validated Part II results (EX-2), and handling conditional results.

### 10.5 Limits of these walkthroughs

- **Multi-client security is not validated.** Separating one client's data from another's is deferred.
  The SAD identifies the future isolation boundary and its access-control assumptions only.
- The walkthroughs check structure, not legal content. Neither adds an obligation, verdict or date to
  the answer key.

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
- User needs behind this document are inferred from the brief and an illustrative scenario for a
  fictional firm (MRD SRC-ILLUS). No user
  interviews were conducted (PRD A-7).

## Open Questions

- **OQ-1**: *Resolved* (operator decision, 2026-11-12, decision log DL-27). Yes, in a limited form: not
  a count such as "1 possible obligation is under review", but, before the first publication only,
  a read-only empty state with one fixed message: "Your obligations calendar is being prepared and checked by a specialist. Nothing has been published yet." It shows no entry, count, status or
  draft content, and sends no notification (MN-007). *After publication, see FR-025 (future scope,
  DL-22).*
- **OQ-2**: *Resolved* (operator decision, 2026-11-11, decision log DL-19). Business-day rules for
  Luxembourg Business Registers (`OBL-05`) and CNMV (`OBL-04`) filings: a rule the sources do not state
  stays "not confirmed" until the specialist sets one at G1. Code never infers or defaults one, so both
  rows stay "not confirmed" in the demo and their weekend dates keep the earlier day and are marked
  (`D-6`). See answer key `OQ-D1`. *The AED subscription-tax question is separate and stays open (OQ-4).*
- **OQ-3**: *Resolved.* MC-001 to MC-003 confirmed by the operator.
- **OQ-4**: **Open** (kept open by the operator, decision log DL-20). Does the AED subscription tax
  follow the "tax deadlines do not roll" rule? See answer key `OQ-D3`. The code assumes no answer: every
  `OBL-02` entry is marked as depending on this question at G1 and G3 (US-004 note, US-010 criterion 12),
  and the dates are the same either way.
- **OQ-5**: The operator wants **four-eyes review** (a second, different specialist confirms before
  publish). **Timing is undecided:** MVP or a later version. Until decided, the MVP happy path has one
  specialist, and every approval records who made it (MD-009) so a second approver can be added.
- **OQ-6**: *Resolved* (operator decision, 2026-11-07). Declining G3 requires a reason, publishes no new
  version and retains the draft and review history. Any previously published version remains visible
  to GPs. See MD-004, FR-022. *(Approval map OD-1, conflict K-1.)*
- **OQ-7**: *Resolved* (operator decision, 2026-11-07). GPs keep seeing the last published entries
  with their publication date, plus a neutral calendar-level review notice when a change questions the
  published calendar's accuracy or completeness, including an obligation possibly missing after a
  rejected row is reopened. MN-007 clarified to cover working content. See FR-025. *(Approval map OD-4,
  conflicts K-2 and K-3.)*
- **OQ-8**: *Resolved: not in the MVP* (operator decision, 2026-11-07). Deliberately deferred; revisit
  before real-world use. See §9. *Original question:* Is a way to withdraw a published calendar or
  entry needed? None exists in the requirements, and none is assumed. *(Approval map OD-5.)*
- **OQ-9**: *Deferred beyond MVP; direction recorded* (operator decision, 2026-11-07). See §9 Future
  work. The detailed design is not resolved. *Original question:* Should a change to fund facts
  invalidate approved G2 verdicts? The fund profile is static mock data in the MVP, so this does not
  arise yet. *(Approval map OD-6.)*
- **OQ-10**: *Resolved* (operator decision, 2026-11-08). **Product direction.** The capstone stays an
  internal specialist tool designed for future reuse. GPs are the expected future buyers (unvalidated,
  A-10). No new GP
  feature is added to agreed future scope. Market research is revisited before commercialising,
  not to complete this MVP. See §10.1.
- **OQ-11**: *Resolved* (operator decision, 2026-11-08). **P-1 before marketing.** A jurisdiction being
  considered is not an approved or active marketing arrangement. Obligations are assessed against the
  stated hypothetical and labelled conditional; marketing permission stays separate. Uncertainty
  prompts specialist review and never silently becomes "applies" or implies authorisation. See §10.4,
  S-2. *Original question:* how does P-1 apply to a jurisdiction that is only under consideration?
- **OQ-12**: *Resolved: future requirement, no MVP feature* (operator decision, 2026-11-08).
  **Client-policy changes** need an authorised decision, a reason, version history and an assessment
  of affected work. Policy must not override mandatory regulatory controls. The SAD proposes the
  mechanism. See §10.2.
- **OQ-13**: *Deferred* (operator decision, 2026-11-08). **Client-data separation.** Not built. The
  SAD identifies the future isolation boundary and access-control assumptions. The walkthroughs do not
  validate multi-client security. See §10.5.

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
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-6 to OQ-9 from the
  draft approval map (OD-1, OD-4, OD-5, OD-6); no requirement changed
- 2026-11-07 · persona `product-mgr` · action `update` · G3 decline defined (MD-004 wording, MD-009,
  new FR-022); OQ-6 resolved, operator decision (approval map PR-1)
- 2026-11-07 · persona `product-mgr` · action `update` · new FR-023 (reopen a rejected row, Must), a new
  scope decision by the operator (approval map PR-2); OQ-7 extended to cover omissions from reopened rows
- 2026-11-07 · persona `product-mgr` · action `update` · new FR-024 (reopen a confirmed verdict, Must),
  a new scope decision by the operator (approval map OD-3); FR-022 G2 route now points to FR-024
- 2026-11-07 · persona `product-mgr` · action `update` · MN-007 clarified (working content); new FR-025
  (published-calendar review notice, Must); FR-023: rejected rows read-only until reopened; OQ-7
  resolved; OQ-1 limited to before first publication; operator decisions (approval map OD-4)
- 2026-11-07 · persona `product-mgr` · action `update` · withdraw/unpublish deliberately deferred for
  the demonstration (§9), revisit before real-world use; OQ-8 resolved, operator decision (approval map
  OD-5)
- 2026-11-07 · persona `product-mgr` · action `update` · §9 Future work: fund-fact changes (direction
  only); OQ-9 deferred beyond MVP, direction recorded, operator decision (approval map OD-6)
- 2026-11-07 · persona `product-mgr` · action `update` · stretch: MD-011 wording scoped to the
  change-monitoring system (status and flags only); new FR-026 (impact-report acceptance, Could;
  mandatory whenever the stretch is built), operator decision (approval map OD-9, PR-5)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` · aligned
  MD-009 (reasons for reopenings and manual-review sends), MD-011 (acceptance *or* manual review) and
  NFR-010 (reopen, decline, report acceptance are specialist-only) with FR-022 to FR-026; no new decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · new AC-021 to AC-024
  (FR-022 to FR-025) and AC-025 (FR-026, stretch only), linking to story criteria; NFR-010 states that
  naming "override" adds no permission and lists the non-overridable checks; MD-009: each override
  records the rule or verdict version (scheme left to the SAD, OD-11); operator decisions
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · MD-009 and AC-016:
  every approval decision (G1, G2, reopenings, G3 publish and decline) records the version of the row,
  verdict or calendar it was made on, superseding the override-only wording above; version scheme
  still for the SAD (OD-11); new AC-026 (explicit decisions, PRD §6); operator decisions
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: FR-026 impact-report decisions record actor, time, report and amendment versions, and the
  reason or completion note; a revised report or amendment does not inherit an earlier decision;
  MD-009 and AC-025 updated to match; operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: FR-026 and AC-025 cover a revision during an open manual review (old review superseded with
  notes kept; amendment stays queued; completion only for current versions; nothing cleared, restored
  or bypassed); operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: FR-026, a referred amendment cannot be closed by accepting a revised report; MD-009,
  superseding a manual review is a system event (system actor, time, triggering revision, affected
  review, old and new versions); AC-025 updated; operator decisions
- 2026-11-08 · persona `product-mgr` · action `update` · new NFR-012 (extensibility, architecture
  quality goal) and §10 (product framing, kinds of variation, extension rules EX-1 to EX-6,
  walkthroughs S-1 RAIF and S-2 Singapore, limits); §9 out of scope adds additional clients, regimes,
  jurisdictions, fund-fact editing, configuration screens and client-data separation; §9 future work
  adds client-policy changes; OQ-10 to OQ-13; MVP scope unchanged; operator decisions. Same day,
  before commit: GP notifications removed (not agreed future scope); EX-5 allows a justified "not
  applicable", does not require identical fixtures or counts, and walkthroughs identify tests only
- 2026-11-09 · persona `product-mgr` · action `update` (UX review) · new A-10: user descriptions in §1
  and GPs as expected buyer (§10.1, OQ-10) labelled unvalidated; no requirement changed
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · A-10 and Assumptions note
  cite the illustrative scenario (MRD SRC-ILLUS) instead of internal documents; no requirement changed
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · FR-020 raised from Should to
  Must (now consistent with MN-009) and extended with the unverified date-conventions note (A-7);
  operator decision
- 2026-11-11 · operator (direct edit) · action `update` · wording only: the quote check is
  deterministic code within a separate verifier step (MD-003, FR-003); the verifier agent keeps the
  conflict checks (FR-004 unchanged). Decides approval map OD-8; see SAD W-04 and QN-1. No requirement
  added or removed. Same day, `@system.arch` added the QN-1 reference to the vocabulary entry and this
  audit line, at the operator's instruction
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · new FR-027 (create a missed row by
  hand; DL-15) with AC-027 and a vocabulary entry; NFR-010 lists row creation as a specialist-only
  action; story US-016. Operator decision; no other requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · new FR-029 and AC-028 (possible
  duplicate groups; one confirmation with a reason at G1 completion; DL-16); US-004 criteria 14–16.
  Operator decision; no other requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · new FR-028 and AC-029 (G1 coverage
  view of uncited paragraphs; SAD W-03b); US-001 criteria 8–9. Demo set: 7 uncited paragraphs (the SAD
  says 5; raised for `@system.arch`). No other requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` · FR-028 and AC-029: only non-rejected rows count
  as citing a paragraph, so a paragraph whose only row was rejected reappears in the coverage view;
  operator decision. AC-001 and AC-002 checked and unaffected (they test extraction output)
- 2026-11-11 · persona `product-mgr` · action `update` (SAD SOQ-8) · NFR-004 amended with the per-unit failure rule (valid units kept, failed unit re-runnable, gate closed until all valid, 3 manual re-runs); new AC-030; US-015 criteria 9–13. Operator-approved SAD decisions (SOQ-2, CR-010); no other requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` · wording only: FR-028 and AC-029 now say "no non-rejected row cites" from their first line, matching SAD W-03b; no requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18, DL-19) · NFR-004 extended with the release of a failed source document to manual entry; new AC-031; OQ-2 resolved (business-day rules never guessed). OQ-4 (AED subscription tax) stays open. Operator decisions; no other requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · OQ-4 kept open and pointed at the G1 note and G3 mark (US-004, US-010 criterion 12); no requirement changed
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · new AC-032 (OBL-02 open-question mark at G1 and G3; SAD CR-027, T-W13-1, T-W13-2); AC-031 detail points to US-013 criterion 9. Operator decision; no requirement changed
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · future-scope items marked deferred: FR-007, FR-023, FR-024, FR-025, FR-027 and FR-029 (priority), FR-005 and FR-006 edit parts and NFR-004 re-run sentences (notes), AC-005, AC-022 to AC-024, AC-027, AC-028 and AC-031 (prefix), AC-030 (re-run part); §9 lists them. Nothing deleted; operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-27) · OQ-1 resolved (the "being prepared" message before the first publication); AC-013 names the message; no requirement changed; operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · new AC-033 to AC-036 (failed step and timeout end the run as failed; abandon with a reason; a new run is allowed after a closed run); FR-022 and AC-021 drop the next-step choices (a decline ends the run as declined); NFR-010 lists abandon as specialist-only; §9 records the OQ-US001-2 limitation; operator decisions
- 2026-11-12 · persona `product-mgr` · action `update` (DL-29 to DL-31) · AC-034 adds the stage time limit and the start-up rule ("service restarted"); AC-035 abandon only while a run waits at a gate (refused while a stage runs); new FR-030 and AC-037 (G3 acknowledgement of rejected rows and uncited paragraphs); new FR-031 and AC-038 (labelled demo switch, off by default; one planted row that can only be rejected); NFR-010 lists both; §9 notes the start-up rule is in the MVP (DL-28 limitation superseded); operator decisions
