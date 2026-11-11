# Product Requirements Document (PRD)

**Product**: Regulatory Intelligence for fund compliance calendars
**Scope**: **MVP only** (six-week capstone)
**Inputs**: `mrd.md` (evidence note, no external market) · `system-description.md` · `mock-data/`
**Selected Runtime**: `crewai`, recorded from `aamad.config.yml`. It constrains Build conventions only.
The **application pattern, runtime design and agent roster are decided in the SAD** (`@system.arch`),
not here.

> **How to read the Trace column.** `SD` = `system-description.md` (e.g. `SD FR-005`, `SD AC-010`).
> `MRD` = `mrd.md` (e.g. `MRD §2`). `KEY` = `mock-data/expected-obligation-library.md`. Every requirement
> in this PRD traces to at least one of these.

---

## 1. Executive Summary

### Problem Statement

- **Operator problem**: Fund compliance teams turn static legal text into deadlines by hand. Every new
  framework repeats the work, and manual interpretation produces inconsistent rules. *(MRD §1–§2)*
- **Impact**: In the illustrative scenario for the fictional operator, documents describing the same
  obligation disagree (for example, on the annual-report deadline and on what starts the clock for a
  beneficial-owner update). None of the mismatches was caught by a check. *(MRD §2, SRC-ILLUS)* No time
  or cost impact has been measured. *(MRD §5)*
- **Why it's hard**: a Part II fund's obligations come from overlapping layers of rules (Luxembourg
  product law, the AIFM Law, EU rules such as PRIIPs and SFDR, and tax, registry and cross-border
  rules). Each layer has its own authorities, deadlines and wording, so interpretation happens across
  several sources at once. *(MRD §2, background only)*
- **User population**: **N/A, internal tool.** One compliance team and the GPs it serves. No external
  market. *(MRD, top note)*

### Solution Overview

- **Approach**: An agentic system turns mock regulatory text into a **verified, source-linked
  obligation library**, judges which obligations apply to one fictional Luxembourg UCI Part II fund, and
  generates its **compliance calendar** with deterministic code. A compliance specialist approves at
  three gates before GPs see anything. *(SD §1, SD MD-001 to MD-008)*
- **Differentiator vs today's manual process**: every rule carries its **source paragraph and verbatim
  quote**. A **separate verifier** checks quotes and cross-source conflicts. Deadlines come from
  **code, not a language model**. *(SD MD-003, MN-005, MN-006)* No comparison with commercial products
  is claimed. *(MRD §4)*
- **Expected outcome**: the specialist moves from *authoring* rules to *checking* them. *(MRD §3)*

### Strategic Rationale

- **Why this response**: errors enter at interpretation, not in the calendar, so that is where the
  capstone tests agents. *(MRD §3)*
- **Value**: a contained test of whether framework onboarding can become configuration rather than
  manual reading. *(MRD §3)*
- **Market timing / positioning**: **N/A, internal tool.**
- **Product direction** *(operator decision, 2026-11-08)*: the MVP is the **first validated
  configuration of a shared product**, designed for future reuse, not a bespoke build. The operator
  expects the future buyer to be the GP (unvalidated, A-7). Market research is revisited before commercialising, not for this MVP. *(SD
  §10.1, NFR-012)*

## 2. Market Context & User Analysis

### Users

| Persona | Who they are | Needs | Can do in MVP | Trace |
|---|---|---|---|---|
| **Compliance specialist** | Owns the obligation calendar. Expert in the rules. | Rules they can trust and check quickly. Every rule traceable to its source. Conflicts surfaced, not hidden. | Run the pipeline, review, edit, reject, approve at G1–G3, publish. | SD §1, MRD §1 |
| **GP / fund manager** | Accountable for the fund's filings, files few of them. Often less familiar with Luxembourg rules *(unvalidated, A-7)*. | Know what is due, when, who files and why, without reading legal text. | **Read only.** View the published calendar. | SD §1, MRD §1 |
| **Filing parties** (AIFM, administrator, auditor, tax advisor, local reporting agent) | Do most of the actual filings *(unvalidated, A-7)*. Stakeholders, **not MVP users**. | Know what they must file and when (future). | **Nothing in the MVP.** Named on every obligation as "who files". No notifications, logins or confirmations. | SD §1, SD A-9, SRC-BRIEF |

Market segment size and geographic expansion: **N/A, internal tool.**

### The happy path (the one user-facing flow in the MVP)

| Step | Who | What happens | Gate | Trace |
|---|---|---|---|---|
| 1 | Specialist | Starts a run on the mock source documents for fund `FND-DEMO-01`. | — | SD FR-001 |
| 2 | System | Extracts obligation rows, each with a paragraph ID and verbatim quote. | — | SD FR-002 |
| 3 | System | Verifies each row: quote check and conflict check. | — | SD FR-003, FR-004 |
| 4 | Specialist | Reviews rows and flags. Resolves conflicts (with a reason if overriding), sets business-day rules, approves or rejects each row. Any edit re-verifies the row. | **G1** | SD FR-005, FR-006 |
| 5 | System | Judges applicability for each approved row: applies / does not apply / unsure, with reasoning, using the mock fund profile. | — | SD FR-008, FR-009 |
| 6 | Specialist | Confirms or overrides each verdict. Decides every "unsure". | **G2** | SD FR-010 |
| 7 | System | Generates the calendar with deterministic code. | — | SD FR-011 to FR-013 |
| 8 | Specialist | Reviews the calendar and publishes it. | **G3** | SD FR-014 |
| 9 | GP | Opens the read-only calendar and sees what, when, who and why for each entry. | — | SD FR-015 |

### User Needs Analysis

> **Evidence base.** These needs are **inferred** from the operator brief (SRC-BRIEF) and from the
> illustrative scenario for the fictional operator in `mrd.md` (SRC-ILLUS). **No user interviews were
> conducted** (Assumption A-7). Treat each need as a hypothesis the demo should test, not a validated
> finding.

#### Compliance specialist

| ID | Need | Happy-path step | Source |
|---|---|---|---|
| UN-S1 | Turn new regulatory text into deadline rules without re-reading and re-typing everything by hand. | 1–4 | MRD §1, §3 · SRC-BRIEF |
| UN-S2 | See exactly where each rule comes from, so it can be checked quickly against the source. | 4 | SRC-BRIEF ("every rule links to its source paragraph") |
| UN-S3 | Have disagreements between sources surfaced by a check, not found by chance. | 3–4 | MRD §2 |
| UN-S4 | Stay in control: nothing consequential happens without their approval. | 4, 6, 8 | SRC-BRIEF ("approves every consequential handoff") |
| UN-S5 | Decide unclear cases themselves, with the reasoning in front of them. | 6 | SRC-BRIEF ("applies / does not / unsure + reasoning") |
| UN-S6 | Trust that dates are calculated the same way every time. | 7 | SRC-BRIEF ("deterministic due-date code") |
| UN-S7 | Show afterwards who decided what, and why. | 4, 6, 8 | MRD §3 |

#### GP / fund manager

| ID | Need | Happy-path step | Source |
|---|---|---|---|
| UN-G1 | Know what is due and when, without reading legal text. | 9 | SRC-BRIEF ("what is due and why") · MRD §1 |
| UN-G2 | Understand why each obligation applies to their fund. | 9 | SRC-BRIEF ("what is due and why") |
| UN-G3 | Know who files each obligation, so they know whether they need to act. | 9 | MRD §1 (accountable for filings, but file few of them) |
| UN-G4 | Trust what they see: only information a specialist has approved. | 9 | SRC-BRIEF ("trustworthy read-only view") |
| UN-G5 | Not miss a filing deadline. | 9 | SRC-BRIEF ("so they don't miss the filing deadlines") |
| UN-G6 | Get help with Luxembourg-specific rules they are less familiar with. | 9 | MRD §1 |

#### Adoption barriers

| ID | Barrier | Who | How the MVP addresses it | Source |
|---|---|---|---|---|
| AB-1 | **Distrust of AI-written rules.** If output can't be verified quickly, the specialist redoes it by hand and the benefit disappears. | Specialist | Verbatim quote on every row, separate verifier, three gates. | MRD §3, §5 |
| AB-2 | **Checking takes as long as writing.** | Specialist | Flags point to what needs attention. Review time target of under 30 minutes is measured. | MRD §3 · SD MC-003 |
| AB-3 | **False alarms.** Too many flags and the specialist stops reading them. | Specialist | Tested: no flag where sources agree. | SD MP-003 |
| AB-4 | **Professional responsibility.** Specialists may be wary of relying on a tool for legal interpretation. | Specialist | Output is a draft. Every rule is approved by a person. Not legal advice. | MRD §5 · SD MN-009 |
| AB-5 | **One wrong date breaks trust** in the whole calendar. | GP | Deterministic dates, exact-match tests, roll notes, publish gate. | SD MD-006, MN-007 |
| AB-6 | **Legal language** the GP cannot interpret. | GP | Plain-English "why" for each entry. | SD NFR-005 |
| AB-7 | **Expecting filing status.** GPs may expect to see what has been filed. The MVP does not show it. | GP | Stated as out of scope. Stable entry IDs keep the path open. | SD §9, FR-016 |

### Competitive Landscape

**Not researched.** No comparison is made or claimed. *(MRD §4)*

## 3. Technical Requirements & Architecture

> This section states **constraints the architecture must satisfy**. It does not choose a pattern,
> runtime design or agent roster. Those are recorded in `sad.md` by `@system.arch`.

### Discovery constraints

The full must-do / must-not / must-cost / must-prove tables are in `system-description.md` §3. They are
summarised here and not repeated.

| Bucket | IDs | Key constraints |
|---|---|---|
| Must do | SD MD-001 to MD-010 | Source-linked extraction, applicability verdicts, separate verifier, three gates, re-verify on edit, deterministic dates, event handling, GP view, audit log, stable entry IDs |
| Must not | SD MN-001 to MN-009 | No real data, no live externals, no gate bypass, verifier never auto-resolves, no model-computed dates, no unsourced rows, no unfinished work shown to GPs, no task tool as record, not legal advice |
| Must cost | SD MC-001 to MC-003 | See §5 |
| Must prove | SD MP-001 to MP-008 | Exact match with the answer key, traceability, gate enforcement, determinism, complete audit log |

### Feasibility notes for the architect

These are inputs, not a pattern verdict.

- The brief names three **agent responsibilities**: extraction, applicability and verification. The
  verifier **must be separate** from the extractor (SD MD-003). How these map to runtime agents, and
  whether other agents are needed, is for the SAD.
- Date calculation is **not** an agent responsibility. It must be deterministic code (SD MN-005).
- The three gates are **hard stops**. The design must make it impossible for work to move on without
  the matching approval (SD MN-003, SD AC-013).
- Agent output must be **structured and validated** before a gate sees it. Invalid output stops the
  run (SD NFR-004).

### Architecture quality goal: extensibility

*Operator decision, 2026-11-08. Full text in SD §10 and NFR-012. Mechanisms are for the SAD.*

| Item | Requirement | Trace |
|---|---|---|
| Framing | Build the MVP as the first validated configuration of a shared product. Prefer shared capabilities with configuration and defined extension points over client-specific copies. | SD §10.1, NFR-012, EX-1 |
| Kinds of variation | Keep variation driven by **regulation**, **fund terms** and **client policy** apart. Client policy may tighten controls but never override mandatory ones. | SD §10.2 |
| Extension rules | Any future extension keeps the Part II answer-key results exactly, keeps the verification, approval and audit controls, is validated by a qualified specialist, and addresses the relevant kinds of check in SD MP-001 to MP-008 with its own evidence (a justified "not applicable" is allowed; fixtures and counts need not match the demo set). | SD EX-2 to EX-5 |
| Walkthroughs | The SAD walks through **S-1** (a fictional Luxembourg RAIF) and **S-2** (`FND-DEMO-01` considering marketing to institutional investors in Singapore, with marketing **not** assumed to be permitted) separately. They test extensibility only; they promise no regulatory coverage. Each identifies the tests it would need, without building or running them. | SD §10.4, EX-5, EX-6 |
| Limits | The walkthroughs do not validate multi-client security. The SAD names the future isolation boundary and access-control assumptions only. | SD §10.5, OQ-13 |
| MVP scope | **Unchanged.** One fictional Part II fund, static fund facts. Nothing in this block is built in the MVP. | SD §9 |

### Runtime constraints

| Constraint | Requirement | Trace |
|---|---|---|
| Tool boundaries | Agents read only the mock source documents and the mock fund profile. They have no tools that write to the calendar, approve, or publish. | SD MN-002, MN-003 |
| Network | No calls to email, regulator portals or task tools. The language-model provider is the only live service (see A-3). | SD MN-002 |
| Identity | Every approval, edit, override and rejection records who did it. Roles may be mocked. | SD MD-009, SD A-5 |
| Data minimisation | Only mock data is processed. No real client data enters prompts, logs or files. | SD MN-001 |
| Logging | Every agent output and human decision is written to an add-only audit log. | SD MD-009, NFR-003 |
| Testability | Tests for gates, due-date calculation and the audit log run **without** calling a language model. | SD NFR-011 |

### Integration Requirements

| Item | MVP | Trace |
|---|---|---|
| External APIs | Language-model provider only. Every business-side external system is mocked. | SD MN-002 |
| Mocked externals | Regulatory sources, fund records, holiday calendar, event log. All under `mock-data/`. | SD §2, KEY §5 |
| Storage | Must persist rows, verdicts, approvals, calendar entries and the audit log between sessions. The technology is decided in the SAD. | SD MD-009, MD-010 |
| Authentication | Mocked roles (specialist, GP). Real authentication is out of scope. | SD A-5, SD §9 |
| Secrets | Model API keys come from local environment settings that git ignores. Never committed. | SD NFR-009 |
| Performance | See §5. | SD MC-001 |

### Infrastructure Specifications

**Deferred to the SAD.** The MVP has no hosting, compute or network targets beyond §5. *(SD §6)*

## 4. Functional Requirements

### Core Features (P0, MVP)

Acceptance criteria are written as tests. "SD AC-xxx" refers to the full Given/When/Then in
`system-description.md` §8.

#### F1. Source-linked extraction
**Why:** UN-S1, UN-S2 · MRD §1 (manual re-reading per framework), MRD §3 (authoring → checking)
*As a compliance specialist, I want obligations extracted from regulatory text into fixed rows, each
quoting its source paragraph, so that I check rules instead of writing them.*

| Acceptance criterion | Trace |
|---|---|
| Exactly the 6 expected rows are produced from the 6 mock source documents. | SD AC-001, KEY §1 |
| No row cites a paragraph that contains no obligation (e.g. `SRC-UCILAW-P1`). | SD AC-002 |
| Every row has one paragraph ID and a quote found word for word in that paragraph. | SD AC-001, MN-006 |
| Business-day rule is output as "not confirmed" when the source does not state it. | SD FR-002, KEY §5 |

#### F2. Independent verification
**Why:** UN-S2, UN-S3 · MRD §2 (conflicting interpretations were never caught by a check)
*As a compliance specialist, I want a separate check of every row's quote and of conflicts with other
sources, so that I see problems before I approve.*

| Acceptance criterion | Trace |
|---|---|
| Conflicts `C-1` (`OBL-03`) and `C-2` (`OBL-05`) are flagged. | SD AC-003, KEY §3 |
| No conflict is flagged on `OBL-01`, where the sources agree. | SD AC-003 |
| A quote altered by one word fails the quote check, and the row cannot be approved. | SD AC-004 |
| A row whose fields don't match its own (correct) quote is flagged as an internal conflict. | SD AC-017 |
| The verifier never changes a row. | SD MN-004 |
| Each flag states its type and shows the evidence for it. **Quote check:** the text that does not match the source paragraph. **Internal:** the field that disagrees with the row's own quote. **Cross-source:** the conflicting paragraph ID and its quote. | SD MD-003, FR-003, FR-004 · Operator decision (UX review, 2026-11-09) |

#### F3. Gate G1: rule approval
**Why:** UN-S4, UN-S7 · MRD §3 (human approval stays in place), MRD §5 (not legal advice)
*As a compliance specialist, I want to approve, edit or reject each verified row, so that only rules I
trust enter the library.*

| Acceptance criterion | Trace |
|---|---|
| Each row can be approved, edited or rejected. The business-day rule is set at approval. | SD FR-005 |
| An edit re-runs the verifier on that row. | SD AC-005 |
| A row with a remaining flag cannot be approved without a written reason. With a reason, it is approved and the reason is logged. | SD AC-006 |
| Editing an approved row returns it to pending and marks its calendar entries out of date. | SD AC-005, FR-007 |
| A rejected row can be reopened with a reason, before or after publication. It returns to pending and goes through G1 and G2 again. | SD FR-023, AC-022 |
| At G1 the specialist can add a missed row by hand, using the edit form on an empty row. No model is involved. The row needs a source paragraph and a verbatim quote, passes the code quote check, is labelled as manual, gets its own G1 decision, and is audited. | SD FR-027, AC-027 |
| After a source document is released to manual entry (it failed its re-runs), the specialist adds that document's rows by hand in the same way: a source paragraph and verbatim quote, the code quote check, labelled as manual, audited. | SD FR-027, NFR-004, AC-031 |

#### F4. Applicability verdicts
**Why:** UN-S5 · MRD §1 (each framework means interpreting obligations again), MRD §3
*As a compliance specialist, I want the system to judge which approved rules apply to the fund, with
reasons, so that I confirm decisions instead of making each from scratch.*

| Acceptance criterion | Trace |
|---|---|
| Verdicts match the answer key: 4 applies, `OBL-04` unsure, `OBL-06` does not apply. | SD AC-007, KEY §2 |
| Every verdict cites at least one fund fact ID. | SD MD-002 |
| A verdict of "applies" for `OBL-04` counts as a failed test. | KEY §2 |

#### F5. Gate G2: applicability approval
**Why:** UN-S4, UN-S5 · MRD §3 (human approval stays in place)
*As a compliance specialist, I want to confirm or override each verdict, so that no obligation is
wrongly hidden or added.*

| Acceptance criterion | Trace |
|---|---|
| Each verdict can be confirmed or overridden. Overrides are logged with a reason. | SD FR-010, MD-009 |
| G2 cannot be completed while any verdict is "unsure". | SD AC-008 |
| When the specialist decides an "unsure" verdict as "applies" under P-1, it is labelled **precautionary** with its reason (for `OBL-04`: "precautionary: registration unconfirmed"). The label is visible at G2 and carried into the calendar. | SD P-1, OQ-11 · KEY §2 |
| At G2, each fund fact ID cited in a verdict can be opened to show what the fact says. Read-only. | SD MD-002, FR-008 · Operator decision (UX review, 2026-11-09) |
| A confirmed verdict can be reopened with a reason, before or after publication, without editing its rule. It returns to G2, and its entries are marked out of date until the dates are regenerated. | SD FR-024, AC-023 |

#### F6. Deterministic calendar
**Why:** UN-S6, UN-G5 · MRD §2 (deadlines set by hand, inconsistently), MRD §4 (anchor + offset)
*As a compliance specialist, I want due dates calculated by code from approved rules, so that dates are
correct and repeatable.*

| Acceptance criterion | Trace |
|---|---|
| The calendar contains exactly the 22 entries in the answer key, with the same dates. | SD AC-009, KEY §4 |
| A CSSF deadline on a weekend rolls to Monday with a note (2027-01-10 → 2027-01-11). | SD AC-010 |
| A deadline with an unconfirmed roll rule keeps the earlier date and is marked (2027-02-28). | SD AC-011 |
| An event-triggered deadline is calculated from the awareness date, not the event date. | SD AC-012 |
| Two runs from the same approved inputs give identical calendars. | SD AC-015 |
| Every calendar entry has a stable ID. | SD FR-016 |

#### F7. Gate G3: publish
**Why:** UN-S4, UN-G4 · MRD §1 (GPs need a view they can trust), MRD §3
*As a compliance specialist, I want to publish the fund's calendar only when I am satisfied, so that GPs
never see unfinished work.*

| Acceptance criterion | Trace |
|---|---|
| Before G3, the GP view shows no entries for the fund. | SD AC-013 |
| Publishing without G1 and G2 complete is refused. | SD MP-006 |
| G3 publishes the whole fund calendar at once. | SD A-6 |
| Declining G3 requires a reason, publishes no new version and keeps the draft and review history. Any previously published version stays visible to GPs. | SD FR-022, AC-021 |
| At G3, the specialist sees a note that the date conventions have not yet been checked against the legal texts. | SD A-7 · Operator decision (business review, 2026-11-09) |

#### F8. GP read-only calendar
**Why:** UN-G1 to UN-G6 · MRD §1 (static legal documents, no live view, unfamiliar local rules)
*As a GP, I want to see what is due, when, who files it and why it applies, so that I don't miss a
filing and don't have to read legal text.*

| Acceptance criterion | Trace |
|---|---|
| Each entry shows what (obligation + authority), when (date + roll note if moved), who files, and why (reason + source citation and quote). | SD AC-014 |
| No pending, unsure, rejected or conflicted working content is shown. | SD MN-007 |
| A precautionary entry shows "precautionary" and its reason. GP text must not state or imply that a registration or marketing is permitted. | SD P-1, OQ-11 |
| After publication, a change that questions the published calendar shows GPs a neutral review notice. The last published entries and their publication date stay visible. The notice clears only on a successful republish. | SD FR-025, AC-024 |
| The GP cannot change anything. | SD §1, NFR-010 |
| **Must.** The GP view carries one calendar-level note: entries are specialist-approved interpretations, not legal advice, and the date conventions behind them have not yet been checked against the legal texts. The note is not repeated on each entry. | SD FR-020, MN-009, A-7 · Operator decision (business review, 2026-11-09) |

#### F9. Audit log and evaluation
**Why:** UN-S7 · MRD §3 (auditable process), MRD §5 (no claims without evidence: the evaluation is the
evidence)
*As a compliance specialist, I want every agent output and decision recorded and the whole run checked
against the answer key, so that I can prove the system works.*

| Acceptance criterion | Trace |
|---|---|
| Every agent output and human decision appears in the log with who, when and what. Every approval decision names the row, verdict or calendar version it was made on. | SD AC-016, MD-009 |
| Log entries cannot be edited or deleted. | SD NFR-003 |
| An evaluation report compares extraction, verdicts, verifier flags and calendar with the answer key. | SD FR-018, MP-001 to MP-004 |

### Enhanced Features (P1, after MVP unless time allows)

| Feature | Trace |
|---|---|
| Full trail view per row: source, quote, flags, verdict, approvals in one place. | SD FR-019 (Should) |

The "not legal advice" note (SD FR-020) moved to F8 as a Must on 2026-11-09.

### Stretch Goal (P1, Could): built only after the core works

#### F10. Change monitoring
**Why:** UN-S1, UN-S3 · MRD §1, §3 (interpretation is repeated every time rules change) · Assumption A-8
*As a compliance specialist, I want the system to work out which obligations a rule amendment affects
and flag only those, so that I re-check what changed instead of re-reading everything.*

This is the part of the product where the system must **decide how far a change reaches**: one duty,
several, or none. Extraction, verification and applicability follow a fixed order. Impact assessment
does not. How it is built is for the SAD.

| Acceptance criterion | Trace |
|---|---|
| `AMD-01`: only `OBL-03` is flagged and its entry marked out of date. `OBL-02` is not flagged. | SD AC-018, KEY §6 |
| `AMD-02`: `OBL-01` and `OBL-03` are flagged for re-check at G2, and their 13 entries are marked out of date. | SD AC-019, KEY §6 |
| `AMD-03`: nothing is flagged, and the report says "wording change only". | SD AC-020, KEY §6 |
| The change-monitoring system may update review status and flags, but never changes the substance of a rule, applicability decision or deadline itself. Affected items go back through G1 or G2. | SD MD-011, MN-003 |
| Every impact report, including "no impact", needs specialist acceptance or a documented manual review. Acceptance changes review status only. | SD FR-026, AC-025 |
| Each acceptance, referral and manual-review completion records the report and amendment versions it was made on. A revised report or amendment needs a fresh review; it does not inherit acceptance. If the revision happens during manual review, the old review is kept as superseded (logged as a system event), accepting the revised report does not close the amendment, and completion is accepted only for the current versions. | SD FR-026, MD-009, AC-025 |

**Guardrails:** not part of the Week 6 definition of done. Depends on the edit-and-re-verify chain (F3,
SD MD-005), so it falls away if that chain is cut. The architect should estimate it separately
(OQ-5).

### Future Features (P2)

| Feature | Trace |
|---|---|
| Filing status, evidence and confirmations, linked by stable entry ID. | SD §9 |
| Notifying filing parties and collecting their confirmations, together with filing status. Routed by each obligation's "who files" role. | SD §9, SD A-9 |
| Multiple funds and frameworks, reusing approved libraries. | SD §9 |
| Official holiday calendar in place of the mock list. | SD §9 |
| Additional clients, other regimes (e.g. a RAIF) and other marketing jurisdictions (e.g. Singapore), as configurations of the shared product. Each needs specialist validation and its own tests. | SD §9, §10, EX-1 to EX-6 |
| Fund-fact editing and configuration screens. Client-policy changes need an authorised decision, reason, version history and impact assessment. | SD §9, §10.2 |
| Separation of one client's data from another's. | SD §10.5 |

Four-eyes review is **not** placed here yet. Its timing is undecided (OQ-1).

## 5. Non-Functional Requirements

### Performance

| Target | Value | Source |
|---|---|---|
| Full pipeline run on the demo set (agent output only) | Under 5 minutes | SD MC-001, operator-confirmed |
| Throughput / concurrency | One run at a time | Assumption A-6 |
| Availability | **N/A for the MVP** (local demo) | SD §6 |

### Security & Compliance

| Requirement | Trace |
|---|---|
| No real client data, names or branding in any committed file. Checked by scanning against a private, git-ignored list. | SD MN-001 |
| No secrets in the repository. | SD NFR-009 |
| Only the specialist role can approve, edit, reject, override, reopen, publish or decline (and, in the stretch, accept or send impact reports for manual review). GPs are read-only. | SD NFR-010 |
| Output is a specialist-approved interpretation, not legal advice. | SD MN-009 |
| Evidence, examples and personas use only the fictional firm and public regulation. No employer documents are cited or summarised in the repository or portfolio. | SD MN-001 · MRD SRC-ILLUS · Operator decision (business review, 2026-11-09) |

### Scalability & Reliability

| Requirement | Trace |
|---|---|
| **Scaling: deferred.** One fund, one framework in the MVP. | SD A-1, §9 |
| If an agent fails or returns invalid output, nothing moves forward and the failure is logged. | SD NFR-004 |
| A partial calendar is never published. | SD NFR-004 |
| **Extensibility: architecture quality goal.** Designed for reuse; only the Part II configuration is built. See §3. | SD NFR-012, §10 |

### Cost

| Target | Value | Source |
|---|---|---|
| Model usage per full demo run | Under US$2 | SD MC-002, operator-confirmed |

## 6. User Experience Design

> Interaction requirements only. Screens, layout and visual direction belong to `@ux.designer`
> (`ux.md`).

### Interface Requirements

| Requirement | Trace |
|---|---|
| Two surfaces: a **specialist review surface** (runs, gates G1–G3) and a **GP read-only calendar**. | SD §1, F3, F5, F7, F8 |
| The specialist sees, for each row, its source quote, verifier flags and status in one place. | SD MP-005 |
| Platform: web. | Assumption A-4 (operator-confirmed) |
| Accessibility standard: **WCAG 2.2 AA**. | Operator decision (Define) |

### Human–system interaction

| Requirement | Trace |
|---|---|
| Every agent claim is shown with its evidence: quote for rows, fact IDs for verdicts. | SD MD-001, MD-002 |
| Flags and "unsure" verdicts are visibly distinct and block their gate until resolved. | SD AC-006, AC-008 |
| Overrides ask for a written reason. | SD AC-006 |
| **Run status.** During a run, the specialist sees which steps have finished and which step is running. | SD MC-001 · Operator decision (UX review, 2026-11-09) |
| **Failures.** If a step fails, a plain message names the step and confirms nothing moved forward. The run stops at the last safe state, and gate decisions already recorded are kept. The specialist can re-run the failed step from that state, without repeating finished steps or earlier gate decisions. | SD NFR-004 · Operator decision (UX review, 2026-11-09) · OQ-5 |
| Rolled and unconfirmed dates are labelled in plain English. | SD AC-010, AC-011 |
| GP-facing "why" text is readable by a non-lawyer. | SD NFR-005 |
| **Voice.** Agent and system text uses plain British English. It states facts and uncertainty without reassurance or alarm, cites its source and gives no advice. GP-facing text is written for a non-lawyer and stays neutral. Checked in a copy review before the demo. Detailed voice guidance belongs to `@ux.designer`. | SD NFR-005, MN-009 · Operator decision (UX review, 2026-11-09) |
| **No bulk or preselected approval decisions (Must).** At G1 and G2, each row or verdict needs its own separate, explicit decision. No approval decision is preselected. Silence, a timeout or closing the screen leaves undecided items pending, and decisions already recorded stay intact. Safe default *values* (for example, the business-day rule "not confirmed") are still allowed. G3 stays one explicit decision to publish the whole calendar. If the stretch is built, the same rule applies to impact-report acceptance. *Separate clicks support deliberate review but don't prove it happened. The 30-minute review target (SD MC-003) must still be measured, not assumed.* | Operator decision (Define) · SD MD-004, MD-009, A-6, MC-003, AC-026 |

## 7. Success Metrics & KPIs

### Operational

| Metric | Target | Source |
|---|---|---|
| Specialist time to complete G1–G3 on the demo set, from audit-log timestamps | Under 30 minutes | SD MC-003, operator-confirmed |
| Manual-effort baseline | **No ROI or time saving is claimed.** A labelled estimate of manual effort for the five demo obligations is recorded for comparison with the review time. A measured baseline is needed before any value claim. | MRD §5 · OQ-12 · Operator decision (business review, 2026-11-09) |
| Share of extracted rows approved **without edits** | **After the MVP.** Not a Week 6 metric: demo decisions are scripted, so the rate would measure the script, not the agents. | OQ-2 (MRD OQ-2) |

### Technical

| Metric | Target | Source |
|---|---|---|
| Extraction accuracy | 6 of 6 rows, 0 extra rows | SD MP-001, KEY §1 |
| Applicability accuracy | 6 of 6 verdicts | SD MP-002, KEY §2 |
| Verifier recall and false alarms | Both planted conflicts caught. No flag on agreeing sources. Altered quote caught. Wrong field with a correct quote caught. | SD MP-003, KEY §3 |
| Calendar accuracy | 22 of 22 entries, exact dates | SD MP-004, KEY §4 |
| Determinism | Identical calendar on repeated runs | SD MP-007 |
| Gate enforcement | 100% of bypass attempts refused | SD MP-006 |
| Cost per run | Under US$2 | SD MC-002 |
| Run time | Under 5 minutes | SD MC-001 |

**If a target is missed.** The targets are exact on a small set, so a pass means the exact value above.
If a technical target is missed, the evaluation report states the result. Gates still prevent
unapproved output from reaching GPs. A miss is a finding, not hidden. *(SD FR-018, MRD §5 · Operator
decision, business review, 2026-11-09)*

### User Experience

| Metric | Target | Source |
|---|---|---|
| Happy path completed end to end by one specialist, then viewed by a GP | Yes / no in the demo | §2 happy path |
| Satisfaction measure | **None defined** | OQ-3 |

## 8. Implementation Strategy

### Development Phases

| Phase | Work | Owner |
|---|---|---|
| 1. Define | Evidence note ✅ · System description ✅ · PRD (this) · User stories · SAD (pattern, runtime design, agent roster) · UX | `@product-mgr`, `@system.arch`, `@ux.designer` |
| 2. Build | Setup → frontend / backend → integration → QA (evaluation against the answer key) → security review | `@project.mgr`, engineers, `@qa.eng`, `@security.eng` |
| 3. Deliver | Run instructions and user guide | `@devops.eng` |

Total timebox: six weeks. *(SRC-BRIEF)* How the weeks split across phases is **not set** (OQ-5).

### Resource Requirements

One operator, using the AAMAD personas. *(SRC-BRIEF)*

### Risk Mitigation

| Risk | Mitigation | Trace |
|---|---|---|
| Agents produce confident but wrong rows or verdicts. | Separate verifier, mandatory quotes, three gates, answer-key evaluation. | SD MD-003, MD-004, FR-018 |
| Real data leaks into the public repo. | Mock data only. Private identifier scan. `reference/` is git-ignored. | SD MN-001 |
| Date conventions are wrong. | Conventions written down, operator-confirmed where possible, open ones marked. Safe default for unknown roll rules. | KEY §5, SD A-3, A-7 |
| Scope grows into filing tracking. | Filing status explicitly out of scope, with a stable-ID hook for later. | SD §9, FR-016 |
| Three gates make the happy path too long for the demo. | Specialist time target of under 30 minutes is measured. | SD MC-003 |
| The stretch goal (F10) takes time from the core. | Built only after F1–F9 pass. Estimated separately. Not in the Week 6 definition of done. | SD MD-011, OQ-5 |
| Designing for extensibility over-builds the six-week MVP. | Only the Part II configuration is built. Extension points are added where the walkthroughs show a need, not speculatively. The architect includes this in the estimate. | SD NFR-012, §10, OQ-5 |
| The MVP does not fit the six-week timebox. | The MVP must fit the **six-week** capstone timebox. The SAD estimates the work against it, and a cut line between the core demo path and hardening is agreed before Build. | SRC-BRIEF · OQ-5 · Operator decision (business review, 2026-11-09) |
| Walkthroughs are read as regulatory coverage, or as saying Singapore marketing is permitted. | Each is labelled architecture-only. Regulatory differences are questions for a specialist. S-2 keeps marketing permission separate and labels results conditional. | SD §10.4, EX-6 |

## 9. Launch & Go-to-Market Strategy

**N/A, internal capstone tool.** See Assumption A-1.

---

## Quality Assurance Checklist

- [x] Requirements traceable to MRD, system description, or recorded Assumptions (Trace columns)
- [x] Technical specifications feasible with the selected runtime adapter (no runtime-specific design made; SAD to confirm)
- [x] Success metrics aligned with stated objectives (§7 maps to SD must-prove)
- [x] MVP vs Future Work boundaries explicit (§4 P0 / P1 / P2, SD §9)
- [x] Market sections marked N/A when MRD was intentionally skipped (§1, §2, §9)

## Sources

- `project-context/1.define/mrd.md`: evidence note (internal tool, no external market). Its evidence is
  an illustrative scenario for a fictional firm (SRC-ILLUS) plus public regulation.
- `project-context/1.define/system-description.md`: requirements, buckets, acceptance criteria.
- `project-context/1.define/mock-data/`: sources, fund profile, answer key (KEY).
- **SRC-BRIEF**: operator brief for this capstone.
- **Operator PRD instructions**: MVP only, one happy path, mock every external, testable acceptance
  criteria, trace every requirement, leave pattern/runtime/roster to the SAD, unsourced numbers to Open
  Questions.
- **Operator decisions** in Define: keep three gates, defer four-eyes timing, confirm MC-001 to MC-003,
  confirm SD A-5 and A-6, confirm PRD A-3 (with the testability condition) and A-4, WCAG 2.2 AA.
- **Operator decisions, 2026-11-08**: extensibility as an architecture quality goal; product
  direction; two architecture-only walkthroughs; P-1 before marketing; client-policy changes;
  client-data separation deferred (SD §10, OQ-10 to OQ-13).
- **Operator decisions, 2026-11-09** (UX and business reviews): recorded with reasons and the documents
  they changed in `project-context/1.define/decision-log.md` (DL-01 to DL-12).

## Assumptions

- **A-1**: Launch / go-to-market is N/A. The tool is internal and not sold. *(MRD)* *Note,
  2026-11-08: still true for the capstone. The longer-term direction is a shared product with GPs as
  the expected buyers (operator expectation, unvalidated; see A-7). Market research is revisited before commercialising (SD §10.1, OQ-9).*
- **A-2**: **Three approval gates, not one.** The operator's PRD instructions asked for one human
  approval gate. The operator then decided to keep three gates (G1, G2, G3), as agreed in the system
  description and required by the brief ("approves every consequential handoff"). This PRD follows that
  decision.
- **A-3**: "Mock every external system" covers business systems (regulators, email, fund records,
  holiday calendars, task tools). The **language-model provider** is a live dependency, because the
  agents cannot run without it. Operator-confirmed, with one condition: code that contains no AI
  (gates, dates, audit log) must be testable without the live model (SD NFR-011).
- **A-4**: The two surfaces are web-based. Operator-confirmed. The web framework is for the SAD.
- **A-5**: The happy path counts as one flow even though a GP views the result at the end. The GP only
  reads and has no decisions to make.
- **A-6**: The MVP handles one pipeline run at a time. This follows from one operator, one fund and one
  framework (SD A-1). It is not a measured limit.
- **A-7**: **Needs are inferred from the brief and an illustrative scenario (MRD SRC-ILLUS). No
  interviews were conducted.**
  The user needs in §2 are hypotheses. The demo is the first test of them. The same applies to the
  persona descriptions in §2 (for example, that GPs are often less familiar with Luxembourg rules and
  that filing parties do most of the filings) and to GPs as the expected future buyer (§1, A-1). These
  are the operator's expectations, not findings. *(SD A-10)*
- **A-8**: Rule amendments create the same manual re-reading burden as new frameworks. This is inferred
  from the brief and the MRD, not observed directly. It is the basis for the F10 stretch goal.

## Open Questions

- **OQ-1**: **Four-eyes review**: in the MVP or later? The operator wants it. Timing is undecided.
  (SD OQ-5)
- **OQ-2**: *Deferred to after the MVP* (operator decision). The share of rows approved without edits
  needs real specialists reviewing unscripted text. The Week 6 accuracy checks against the answer key
  cover agent correctness instead. (MRD OQ-2)
- **OQ-3**: Is any user-satisfaction measure needed for the capstone? None defined.
- **OQ-4**: *Resolved.* Accessibility standard is WCAG 2.2 AA (operator decision).
- **OQ-5**: Does the MVP scope fit six weeks, and how are the weeks split across Define, Build and
  Deliver? **Not yet shown.** Operator decision: keep the full scope until the architect estimates it
  after the SAD. A possible cut line (a core demo path vs hardening stories) was proposed in Define and
  **not** adopted. *2026-11-09: re-running a failed step (§6) is new scope and goes into the estimate.*
  *2026-11-09 (business review): the timebox is six weeks. `@system.arch` estimates the Must scope
  against it, including the recovery paths (SD FR-022 to FR-025) and the full gate
  logic, and a cut line is agreed with the operator before Build (§8 risks).*
- **OQ-6**: Should the GP view show a neutral "under review" note? Decide before the UX step. (SD OQ-1)
  *Before first publication only. After publication, see SD FR-025 (SD OQ-7 resolved).*
- **OQ-7**: *Part resolved.* Business-day rules for `OBL-04` and `OBL-05`: *resolved* (operator
  decision, 2026-11-11, decision log DL-19). A rule the sources do not state stays "not confirmed"
  until the specialist sets one at G1; code never infers one. Both rows stay "not confirmed" in the
  demo (SD OQ-2, KEY OQ-D1). **Still open:** whether the AED subscription tax follows the "tax does not
  roll" rule (SD OQ-4, KEY OQ-D3; DL-20).
- **OQ-8**: **Frontend framework, for the SAD.** The operator intends to use Next.js. This is a stated
  intent, **not a requirement**: A-4 still says only "web" and leaves the framework to the SAD.
  `@system.arch` to confirm or propose otherwise. *(Approval map OD-12, conflict K-4.)*
- **OQ-9**: *Resolved* (operator decision, 2026-11-08). The shared-product direction does not change the
  MVP or require market research to complete it. The capstone stays an internal specialist tool designed
  for reuse; GPs are the expected future buyers; market research is revisited before commercialising.
  P-1 before marketing, client-policy changes and client-data separation are recorded in SD OQ-11 to
  OQ-13. *(SD OQ-10, §10.)*
- **OQ-10**: **Programme submission requirements.** What the capstone programme requires for
  submission is not yet recorded. To be confirmed by the operator before the SAD estimate.
- **OQ-11**: **Reused prototype front end.** Its origin and the clean-up it needs are not yet
  recorded. To be confirmed before Build. If it was built for or at an employer, it is treated like
  employer documents (§5) and not reused.
- **OQ-12**: **Manual-effort estimate.** The operator provides a labelled estimate of how long the five
  demo obligations would take to interpret by hand, before the demo (§7). It is an estimate, not a
  measurement.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-prd` · runtime `crewai` (recorded from config; not
  a design decision)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · rewrote User Needs Analysis (needs per
  persona, adoption barriers, A-7), moved an unsourced number to A-6, recorded operator decisions on
  A-3, A-4 and accessibility, added FR-008 trace
- 2026-11-06 · persona `product-mgr` · action `update` · calendar target 18 → 22 entries (operator
  decision on `OBL-04`, SD principle P-1)
- 2026-11-06 · persona `product-mgr` · action `quality-pass` (stories) · added internal-conflict
  criterion to F2 and §7 (SD AC-017)
- 2026-11-06 · persona `product-mgr` · action `readiness-check` · added a "Why" trace (user need + MRD
  section) to F1–F9; OQ-5 records that the six-week fit awaits the architect's estimate
- 2026-11-06 · persona `product-mgr` · action `update` · review time measured from audit log; no-edit
  approval target deferred to after the MVP (OQ-2)
- 2026-11-06 · persona `product-mgr` · action `update` · added stretch goal F10 (change monitoring),
  moved out of P2; risk row; A-8
- 2026-11-06 · persona `product-mgr` · action `update` · "why it's hard" (overlapping layers, MRD §2);
  filing parties named as out-of-scope stakeholders (§2 users, P2 future), operator decision
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added OQ-8 (Next.js intent, for
  the SAD); OQ-6 cross-referenced to SD OQ-7; no requirement changed
- 2026-11-07 · persona `product-mgr` · action `update` · F7 criterion for G3 decline (SD FR-022),
  operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · F3 criterion for reopening a rejected row (SD
  FR-023), a new scope decision by the operator
- 2026-11-07 · persona `product-mgr` · action `update` · F5 criterion for reopening a confirmed verdict
  (SD FR-024), a new scope decision by the operator
- 2026-11-07 · persona `product-mgr` · action `update` · F8: "working content" wording (SD MN-007) and
  review-notice criterion (SD FR-025); OQ-6 limited to before first publication; operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · F10: guardrail scoped to the change-monitoring
  system; report-acceptance criterion (SD FR-026); operator decision
- 2026-11-07 · persona `product-mgr` · action `update` · §6: no bulk or preselected approval decisions
  (Must), operator decision (approval map PR-6)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` · §3
  access constraint lists reopen and decline (SD NFR-010, FR-022 to FR-026); no new decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · trace columns cite
  SD AC-021 to AC-026 next to their FR IDs (F3, F5, F7, F8, F10, §6); F9 audit row requires the version
  of every approval decision (SD MD-009, AC-016); operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · F10: report-review
  decisions record report and amendment versions; no silent inheritance by a revised report (SD
  FR-026); operator decision, stretch only
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · F10: revision
  during manual review (superseded review kept; completion only for current versions; SD FR-026);
  operator decision, stretch only
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · F10: no shortcut
  past a referred review; superseding logged as a system event (SD FR-026, MD-009); operator
  decisions, stretch only
- 2026-11-08 · persona `product-mgr` · action `update` · extensibility as an architecture quality goal
  (§3 block, §5 row, SD NFR-012, §10); product direction (§1, note on A-1); P2 future features; two
  risks; OQ-9 resolved; MVP scope unchanged; operator decisions. Same day, before commit: GP
  notifications row removed from P2 (not agreed future scope); extension-tests wording aligned with
  SD EX-5
- 2026-11-09 · persona `product-mgr` · action `update` (UX review) · F2 flag content per type; F5
  precautionary label (SD P-1) and read-only fund facts at G2; F8 precautionary label, no implied
  permission; §6 run status, failure handling with re-run of the failed step (new scope, OQ-5) and
  voice; persona claims and expected buyer labelled unvalidated (§1, §2, A-1, A-7, SD A-10); operator
  decisions
- 2026-11-09 · persona `product-mgr` · action `update` (business review) · evidence reworded to the
  fictional firm's illustrative scenario (§1 Impact, §2 evidence note, A-7, Sources; MRD SRC-ILLUS);
  §5 no employer documents; §7 missed-target handling; §8 hours-budget risk and OQ-5 (40–50 hours, cut
  line before Build); new OQ-10 (programme submission) and OQ-11 (prototype front end); operator
  decisions
- 2026-11-09 · persona `product-mgr` · action `update` (business review, second pass) · "not legal
  advice" note made Must and moved from P1 to F8 (SD FR-020), combined with the unverified
  date-conventions note (SD A-7) as one calendar-level GP note; G3 note for the specialist (F7); §7
  manual-effort baseline row and OQ-12; operator decisions
- 2026-11-09 · persona `product-mgr` · action `update` · §8 risk row and OQ-5: the 40–50 hour budget
  replaced by the six-week timebox (decision log DL-08, revised); operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-19) · OQ-7 part resolved: business-day rules for `OBL-04` and `OBL-05` are never guessed; the AED subscription-tax part stays open (DL-20); operator decision
- 2026-11-11 · persona `product-mgr` · action `update` (DL-18) · F3: one criterion for manual entry of rows after a source document is released (source quote, code quote check, labelled manual, audited); closes US-016 OQ-US016-2; operator decision
- 2026-11-11 · persona `product-mgr` · action `update` · F3 corrected: separate criteria for a missed row at G1 (FR-027, AC-027) and for a released document (FR-027, NFR-004, AC-031); replaces the earlier released-document-only line; operator decision
