# Approval Map

**Product**: Regulatory Intelligence for fund compliance calendars
**Status**: **Matches the SAD as of 2026-11-12 (SAD SOQ-16; decisions DL-22, DL-27, DL-29 to DL-31).
Not a requirement in itself.** Requirements live in `system-description.md`, `prd.md` and the user
stories; rows marked "Proposed" remain proposals. This map does not itself change `prd.md`,
`system-description.md` or the user stories. On 2026-11-07 the operator decided most of its open
items through `@product-mgr`, and the earlier sections below have been updated to match. PR-1, PR-2,
PR-3, PR-5 and PR-6 (§9) are now applied in the Define documents. PR-4 is applied as a requirement for
every G1–G3 decision; the version scheme is left for the SAD (OD-11). See §8,
"Resolved in Define".

**Thin slice (2026-11-12, DL-22, SAD SOQ-16).** The MVP is the thin slice. Edit, reopen, manual
row creation, duplicate groups, re-running a step, the release of a failed document and the GP review
notice are **future scope**: they stay in this map, marked, and are not built. In the MVP a failed step
ends the run as `FAILED`, a G3 decline ends it as `DECLINED`, and correcting anything means a new run
(or abandoning a run that waits at a gate). The map also has rows for starting, abandoning and
restarting a run, the coverage view, and the GP "being prepared" message.

**DL-29 to DL-31 (2026-11-12).** Abandon works only while a run waits at G1, G2 or G3; a stage that
passes its time limit, or is interrupted by a backend restart, ends the run `FAILED` automatically
(A15, A25, H13, H13a). Publishing needs one explicit acknowledgement of the rejected rows and the
uncited paragraphs (H10, H11a, Card G3). A labelled demo switch, off by default, adds one planted row
for the demo run; it adds a row and never approves anything (H0b, A26, H3a).
**Method**: `.cursor/skills/agentic-approval-design/SKILL.md` (see that file for provenance)
**Selected Runtime**: `crewai` (recorded from `aamad.config.yml`; no runtime design is made here)

> **How to read the labels.**
> - **Existing**: stated in an agreed Define document. The trace gives the ID.
> - **Proposed**: an interpretation or control suggested by this map. Not agreed, not built.
> - **Open**: a choice nobody has made yet. Listed in §8.
> - **Future scope (DL-22)**: agreed in the Define documents and designed in the SAD, but not built in
>   the MVP. The item stays in the map so it is not lost.
>
> Trace prefixes: `SD` = `system-description.md`, `PRD` = `prd.md`, `US` = `user-stories/`,
> `KEY` = `mock-data/expected-obligation-library.md`.
>
> **Nothing in this map is implemented or tested.** There is no application code yet. Every
> "enforced by" note says where enforcement *must* live, not where it does.

---

## 1. Scope and sources

### What this map covers

Who may decide and act at each step of the happy path (PRD §2), when the compliance specialist must
approve, and what they need to see. It covers the MVP (F1–F9) and, separately marked, the stretch goal
F10 (change monitoring). It does not choose a pattern, runtime design or agent roster. Those belong to
the SAD.

### Sources and precedence

| Rank | Source | Role here |
|---|---|---|
| 1 | Operator decisions recorded in the Define documents (marked "operator-confirmed" or "operator decision") | Highest. Never overridden by this map. |
| 2 | `system-description.md` (MD, MN, FR, NFR, AC, A, OQ) | Agreed requirements. |
| 3 | `prd.md` (F, UN, AB, runtime constraints, A, OQ) | Agreed requirements; refers to SD. |
| 4 | `user-stories/US-001` to `US-016` | Agreed acceptance tests and operator-confirmed assumptions. |
| 5 | `mock-data/expected-obligation-library.md` | Expected values for tests. |
| 6 | `capstone-brief.md`, `context-summary.md`, `mrd.md` | Summaries and evidence. Used for context only. |
| 7 | This map | Proposals only. |

The Define → Architecture handover was **approved** on 2026-11-09 (`context-summary.md`, decision log
DL-13), and the SAD now exists (`sad.md`). Its Delegation Map (DM-01 to DM-18) reads each step against
this map. If a Define document or the SAD changes, the change is recorded in `decision-log.md`, and
this map must be re-checked.

### Fixed boundaries this map preserves

| Boundary | Status | Trace |
|---|---|---|
| G1: specialist approves each verified rule | Existing | SD MD-004, FR-005, US-004 |
| G2: specialist confirms every verdict and decides every "unsure" | Existing | SD MD-004, FR-010, AC-008, US-007 |
| Dates are calculated by ordinary code, after G2, from approved inputs only | Existing | SD MD-006, MN-005, FR-011, NFR-001 |
| G3: specialist publishes the whole fund calendar at once | Existing | SD FR-014, A-6, US-010 |
| The verifier can block approval but never changes a row | Existing | SD MN-004, MN-006, AC-004, AC-006 |
| Agents cannot approve, publish or write to the calendar | Existing | PRD §3 runtime constraints, SD MN-003 |
| Editing re-verifies, returns the row to pending, sends its verdict back to G2, marks entries out of date | Existing · *future scope (DL-22)* | SD MD-005, FR-006, FR-007, AC-005, US-005 |
| GP access is read-only | Existing | SD NFR-010, US-011 AC6 |
| Change monitoring is a stretch goal. It flags impacts and never applies changes. | Existing | SD MD-011, FR-021, US-014 AC8 |
| One specialist. Four-eyes review is **not** assumed. | Existing (timing open) | SD OQ-5, PRD OQ-1 |
| G3 offers publish or decline. A decline needs a reason, publishes nothing new and keeps the draft and its history. | Existing | SD MD-004, FR-022, AC-021, US-010 AC8–AC9 |
| A rejected row can be reopened with a reason; it is read-only until then. A confirmed verdict can be reopened with a reason for judgement-only corrections. | Existing · *future scope (DL-22)* | SD FR-023, FR-024, AC-022, AC-023, US-004 AC9–AC11, US-007 AC8–AC9 |
| After publication, GPs keep the last published version plus a neutral calendar-level review notice when a change questions it | Existing · *the notice is future scope (DL-22)* | SD MN-007, FR-025, AC-024, US-011 AC9–AC10 |
| A run ends only by G3 being decided, by failing (including a stage time limit or a backend restart mid-stage), or by the specialist abandoning it while it waits at a gate | Existing | SD AC-033 to AC-035, US-015 AC19–AC20, DL-29 |
| Publishing needs one explicit acknowledgement of the rejected rows and uncited paragraphs | Existing | SD FR-030, AC-037, US-010 AC14, DL-30 |
| The demo switch adds one labelled row and never approves anything | Existing | SD FR-031, AC-038, DL-31 |
| No bulk or preselected approval decisions; silence leaves items pending | Existing | PRD §6, SD AC-026, US-004 AC12–AC13, US-007 AC10–AC11, US-010 AC10 |
| No unpublish or withdraw feature exists. It is deliberately deferred for the demonstration and must be revisited before real-world use. | Existing (deferred) | SD §9, OQ-8 |

**Not in the Define documents:** a Next.js frontend. PRD A-4 says only "web", with the framework left
to the SAD. Next.js is recorded as operator intent for the SAD, not an agreed requirement (PRD OQ-8).

---

## 2. Handover

**System**: the regulatory-intelligence pipeline for fund `FND-DEMO-01`. It has three agent
responsibilities (extraction, verification, applicability; SD MD-001 to MD-003), deterministic code
(dates, gates, audit log) and, as a stretch, impact assessment (SD MD-011). How these map to runtime
agents is for the SAD.

| Dimension | Handover | Status · trace |
|---|---|---|
| **Goal** | A specialist-approved, source-linked obligation library; approved applicability verdicts for the fictional fund; and a deterministic calendar the specialist has published to a read-only GP view. On the mock data, results match the answer key. | Existing · SD §1, MP-001 to MP-004 |
| **Priority** | When outcomes compete: (1) no gate is bypassed and nothing unapproved reaches a GP; (2) under uncertainty, choose the cheaper mistake: an extra entry or an earlier date beats a missed filing; (3) stop at the last safe state rather than continue on invalid output; (4) then speed and cost targets. | (1) Existing SD MN-003, MN-007 · (2) Existing SD P-1 · (3) Existing SD NFR-004 · (4) the ordering against MC-001/MC-002 is **Proposed** |
| **Limits** | Mock data only. No live externals except the model provider. No task tool as the record. No model-computed dates. No unsourced rows. The verifier never changes rows. Agents never approve, publish or write the calendar. Not legal advice. | Existing · SD MN-001 to MN-009, PRD A-3 |
| **Check-in** | To the compliance specialist, on the specialist review surface: at G1 once every row is verified; at G2 once every approved row has a verdict; at G3 once the calendar is generated; immediately, as a plain message, when an agent fails or returns invalid output; after any edit (re-verification result). Stretch: when an impact report is ready. | Existing · PRD §2, §6, SD NFR-004, MD-005 · stretch: every impact report goes to the specialist for acceptance or manual review if the feature is built (SD FR-026) |

The goal does not grant any permission not listed below. Missing permission stays missing.

---

## 3. Actors and capabilities

The approval map in §4 depends on this table. Being able to **run** code that applies a
human-approved decision does not let any actor **make** that decision.

| Actor | Kind | Reads | Produces | Must never | Status · trace |
|---|---|---|---|---|---|
| Extraction | Model responsibility | Mock source paragraphs | Draft obligation rows (proposals) | Approve, write the library, compute dates | Existing · SD MD-001, FR-002, PRD §3 |
| Verifier | Model responsibility, separate from extraction | Draft rows, all mock sources | Quote-check result, conflict flags (internal and cross-source) | Edit, resolve or approve a row | Existing · SD MD-003, MN-004, FR-003, FR-004 |
| Applicability | Model responsibility | G1-approved rows, mock fund profile | Draft verdicts with reasoning citing fact IDs; the only source of "unsure" | Confirm its own verdict, decide "unsure" | Existing · SD MD-002, FR-009, US-007 assumption |
| Due-date code | Deterministic code | G2-approved rows and verdicts, mock holidays, mock event log | Draft calendar entries with stable IDs | Run before G2 is complete, call a model | Existing · SD MD-006, MN-005, FR-011 to FR-013, FR-016 |
| Gate and state code | Deterministic code | Approvals, flags, statuses | State changes only on a recorded specialist decision | Advance work without the matching approval | Existing · SD MN-003, MP-006 |
| Audit log | Deterministic code | Every agent output and human decision | Add-only entries | Edit or delete an entry | Existing · SD MD-009, NFR-003 |
| Impact assessment *(stretch)* | Model or code; SAD decides | An amendment, the library, verdicts, calendar | Impact report, flags and review status | Change the substance of a rule, verdict or deadline | Existing · SD MD-011, US-014 AC8 |
| Compliance specialist | Human, mocked role | Everything | Start a run (with or without the demo switch); abandon a run waiting at a gate; approve, reject, override, publish (with the G3 acknowledgement), decline (edit and reopen are future scope, DL-22); *(stretch)* accept impact reports or send them for manual review | Approve a row with a failed quote check; finish G2 with "unsure"; publish with gates incomplete or entries out of date | Existing · SD NFR-010, MN-006, AC-008, US-010 |
| GP / fund manager | Human, mocked role | Published calendar only | Nothing | Change anything | Existing · SD NFR-010, US-011 AC6 |
| Filing parties | Stakeholders, not users | Nothing | Nothing | (no access in the MVP) | Existing · SD A-9 |

Roles are mocked (SD A-5). "Only the specialist can approve" is therefore checked against a mocked
identity. That is enough for the demo. It is not an access-control claim.

---

## 4. Approval map

**Risk questions:** Hard to undo? · Changes their things? · Reaches others? · Would surprise them?
"Their things" means the specialist's library, verdicts and calendar, and what the GP relies on.

### 4a. Agent and code actions

| # | Action | Hard to undo? | Changes their things? | Reaches others? | Would surprise them? | Rule | Why / evidence status |
|---|---|---|---|---|---|---|---|
| A1 | **Load** mock source documents and split them into paragraph IDs (code) | No | No | No | No | **Alone** | Existing · SD FR-001 |
| A2 | **Read** mock sources and the mock fund profile (agents) | No | No | No | No | **Alone** | Existing · PRD §3 tool boundaries |
| A3 | **Draft** obligation rows with paragraph ID and verbatim quote; business-day rule "not confirmed" unless stated | No (draft) | No (draft state only) | No | No | **Alone** | Existing · SD FR-002. Output must pass schema validation first (SD NFR-004). |
| A4 | **Check** each row's quote word for word against its paragraph | No | No | No | No | **Alone** | Existing · SD FR-003. Model or code: closed, it is code (OD-8, SAD W-04). |
| A5 | **Flag** internal and cross-source conflicts on each row | No | No (adds flags, changes no field) | No | No | **Alone** | Existing · SD FR-004, AC-003, AC-017 |
| A6 | **Change** or resolve a row (verifier) | — | Yes | — | Yes | **Never** | Existing · SD MN-004. The capability must not exist, not just be hidden. |
| A7 | **Re-run** the verifier on an edited row only | No | No | No | No (specified) | **Alone** | *Future scope (DL-22).* Existing · SD MD-005, US-005 AC1 |
| A8 | **Draft** an applicability verdict (applies / does not apply / unsure) citing fact IDs | No (draft) | No (draft) | No | No | **Alone** | Existing · SD FR-009, MD-002 |
| A9 | **Re-run** applicability for a row re-approved at G1 after an edit | No | No (new draft verdict) | No | No (specified) | **Alone** | *Future scope (DL-22).* Existing · US-005 AC5 |
| A10 | **Calculate** a due date with a language model | — | Yes | Yes (via GP view) | Yes | **Never** | Existing · SD MN-005, NFR-001 |
| A11 | **Generate** draft calendar entries with code, only after G2 is complete | No (draft, repeatable) | Yes (draft calendar) | No (not visible before G3) | No | **Alone** | Existing · SD FR-011 to FR-013, AC-015. Runs on approved inputs only. Exception to "marked risk → Ask": the result is a draft, and G3 is the Ask. |
| A12 | **Mark** dependent verdicts and entries out of date after a row edit | No | Yes (status only, toward safety) | No | No (specified) | **Alone** | *Future scope (DL-22).* Existing · SD FR-007, AC-005. Exception to "marked risk → Ask": the status change only blocks work, it adds no content. |
| A13 | **Advance** work to the next step without the matching gate approval (any actor) | Yes | Yes | Yes | Yes | **Never** | Existing · SD MN-003, MP-006 |
| A14 | **Approve, reject, override, reopen, publish or decline**, or *(stretch)* accept an impact report (any agent) | Yes | Yes | Yes | Yes | **Never** | Existing · PRD §3 runtime constraints. Agents have no such tool. |
| A15 | **End** the run as `FAILED` (terminal) and log the failure on agent error, invalid output, a step timeout or the stage time limit | No | No | No | No | **Alone** | Existing · SD NFR-004, AC-033, AC-034, DL-29. A hang becomes a failed unit at the step's time limit, and the backend also ends any stage that passes its stage time limit, so every running stage ends on its own and no run stays active by mistake; a new run follows. |
| A16 | **Append** an audit entry for every agent output and human decision | No (by design) | No | No | No | **Alone** | Existing · SD MD-009. Mandatory bookkeeping; adding a gate here would add nothing. |
| A17 | **Edit or delete** an audit entry (any actor) | Yes | Yes | — | Yes | **Never** | Existing · SD NFR-003, US-012 AC4 |
| A18 | **Contact** external parties or live systems (email, regulator portals, task tools, filing parties) | Yes | — | Yes | Yes | **Never** | Existing · SD MN-002, A-9, §9 |
| A19 | **Store** obligations, verdicts or approvals in a task tool | Uncertain | Yes | Uncertain | Yes | **Never** | Existing · SD MN-008 |
| A20 | **Process** real client data or names | Yes | — | Yes (public repo) | Yes | **Never** | Existing · SD MN-001 |
| A21 | **Show** pending, unsure, rejected or conflicted items to a GP | Yes (reliance) | No | Yes | Yes | **Never** | Existing · SD MN-007, US-011 AC4. Covers working content; after publication a neutral calendar-level review notice is permitted (FR-025, resolving K-3; future scope, DL-22). The read-only "being prepared" message before the first publication (G3r) is not working content (DL-27). |
| A22 | **Publish** a partial calendar | Yes | Yes | Yes | Yes | **Never** | Existing · SD NFR-004 |
| A23 | **Show**, at G1, every loaded source paragraph that no non-rejected row cites (coverage view) | No | No | No | No | **Alone** | Existing · SD FR-028, AC-029, US-001 AC8, AC10. A view only: it makes no claim about which paragraphs hold an obligation, does not block G1, and lists a paragraph again if its only row is rejected. A missed row is the costliest error (P-1). |
| A24 | **Start** a run for the fund while another run is active (any actor) | No | No | No | No (specified) | **Never** | Existing · SD AC-036, US-015 AC16 (SAD CR-023). Refused with a message that names the active run. |
| A25 | **Fail** a run automatically at start-up: when the backend starts, an `ACTIVE` run whose stage was running becomes `FAILED` with the reason "service restarted" (code) | No (nothing is undone; a new run follows) | No (status only, toward safety) | No (GPs keep the last published version) | No (specified) | **Alone** | Existing · SD AC-034, US-015 AC19 and restart note, DL-29 (supersedes DL-28; SAD run state model rule 7). Logged as a system event, not a human decision. A run waiting at a gate is unaffected. Same exception as A12: the change only stops work, it adds no content. |
| A26 | **Add** one planted demo row from a fixed fixture, only when the specialist started the run with the demo switch on (code, never the extractor) | No (the specialist rejects it at G1) | Yes (one extra pending row, labelled "demo" everywhere) | No (it can never be approved, so it never reaches a calendar) | No (the specialist chose the switch; the label says what it is) | **Alone** | Existing · SD FR-031, AC-038, DL-31 (SAD CR-029). Adds a row and never approves anything; approving it is H3a (**Never**). |

### 4b. Specialist decisions

These are human actions. "Ask" means the system must stop and wait for the authorised specialist.
The system may never complete them for the specialist.

| # | Action | Hard to undo? | Changes their things? | Reaches others? | Would surprise them? | Rule | Why / evidence status |
|---|---|---|---|---|---|---|---|
| H0 | **Start** a run for the fund (extraction begins) | No (a run can be abandoned, H13; nothing is published by a run) | Yes (new draft rows; model cost, capped) | No | No | **Ask** (the specialist starts it; the system never starts a run) | Existing · US-015 AC16, SD AC-036. Refused while another run is active (A24). The demo switch is off unless the specialist turns it on (H0b). |
| H0b | **Start** a run with the labelled **demo switch** on | No (the planted row is rejected at G1; the run can be abandoned at a gate) | Yes (one extra row marked "demo", A26) | No | No (off by default; labelled) | **Ask** (only the specialist turns it on, only when starting a run) | Existing · SD FR-031, AC-038, DL-31 (SAD CR-029). Turning it on is an audit entry. It adds a row but never approves anything. An evaluation run refuses to start with it on. The mock sign-in stays as it is for roles: the switch is not a role switcher. |
| H0a | **Start a new run** after a closed one (`FAILED`, `DECLINED`, `ABANDONED` or `COMPLETED`) | No | Yes (a fresh run; the closed run and its audit trail stay) | No | No | **Ask** | Existing · SD AC-036, US-015 AC16, US-010 AC8. In the MVP a new run is how a failed quote check, a missed row, a stubborn document or a decline is corrected. |
| H1 | **Approve** a verified row and set its business-day rule (G1) | No before G3 (in the MVP: reject the row, or abandon the run and start a new one; edit is future scope, DL-22) | Yes (enters library) | Not until G3 | No | **Ask** | Existing · SD FR-005, US-004 AC2 |
| H2 | **Approve** a row over a remaining conflict flag, with a written reason (G1) | As H1 | Yes | Not until G3 | Uncertain (a known disagreement is accepted) | **Ask**, reason required | Existing · SD AC-006, US-004 AC5 |
| H3 | **Approve** a row with a failed quote check or no paragraph ID | — | Yes | Eventually | Yes | **Never** | Existing · SD MN-006, AC-004. No reason unlocks this; in the MVP the fix is to reject the row (or abandon the run) and start a new run; edit and re-check is future scope (DL-22). |
| H3a | **Approve** a row marked **demo** (the planted row added by the demo switch) | — | Yes (a fake obligation would enter the library) | Eventually (a fake entry on the GP calendar) | Yes | **Never** | Existing · operator decisions DL-31, SAD SOQ-18 (CR-029), SD FR-031, AC-038. The backend refuses it (`DEMO_ROW_NOT_APPROVABLE`), audits the refusal and shows a plain message. The only decision on a demo row is reject with a reason (H4). |
| H4 | **Reject** a row, with a written reason (G1) | No (reopening is future scope, DL-22; in the MVP a new run) | Yes (removes from library) | Not until G3 (fewer entries) | No | **Ask**, reason required | Existing · US-004 AC3 |
| H4a | **Reopen** a rejected row, with a written reason, before or after publication | No (it can be rejected again) | Yes (row returns to pending; re-verified; G1 then G2 again) | Not until republish; GPs see the review notice if a calendar is published | No | **Ask**, reason required | *Future scope (DL-22).* Existing · SD FR-023, US-004 AC9–AC10 |
| H4b | **Edit** a rejected row directly | — | — | — | — | **Never** | *Future scope (DL-22).* Existing · SD FR-023, US-004 AC11. Rejected rows are read-only until reopened. |
| H5 | **Edit** a row (pending or approved) | No (can edit again) | Yes; invalidates its G1 and G2 approval and its entries | Not until republish; GPs see the review notice if the published calendar used the row (FR-025) | Yes, if invalidation is not shown | **Ask**, with impact shown | *Future scope (DL-22).* Existing · SD MD-005, FR-007, US-005 · showing the impact before saving is Proposed |
| H6 | **Confirm** a verdict (G2) | No (reopening is future scope, DL-22; in the MVP a new run) | Yes | Not until G3 | No | **Ask** | Existing · SD FR-010, US-007 AC2 |
| H6a | **Reopen** a confirmed or overridden verdict, with a written reason, before or after publication | No | Yes (verdict returns to pending G2; its entries go out of date; the rule keeps G1 approval) | Not until republish; GPs see the review notice if a calendar is published | No | **Ask**, reason required | *Future scope (DL-22).* Existing · SD FR-024, US-007 AC8–AC9. For judgement-only corrections; a changed rule uses the edit path. |
| H7 | **Override** a verdict, with a written reason (G2) | As H6 | Yes | Not until G3 | Uncertain | **Ask**, reason required | Existing · US-007 AC3. The specialist cannot set "unsure" (US-007 assumption). |
| H8 | **Decide** an "unsure" verdict (G2) | As H6 | Yes | Not until G3 | No | **Ask**, blocking | Existing · SD AC-008, US-007 AC4–AC6, P-1 |
| H9 | **Complete** G2 while any verdict is "unsure" | — | Yes | Yes | Yes | **Never** | Existing · SD AC-008 |
| H10 | **Publish** the whole fund calendar (G3), with **one explicit acknowledgement** of the rows rejected at G1 and the paragraphs no non-rejected row cites | **Yes** (GP reliance; unpublish deliberately deferred) | Yes | **Yes** (GPs) | No | **Ask**, acknowledgement required | Existing · SD FR-014, FR-030, AC-037, A-6, US-010 AC14, DL-30 (SAD CR-028). The acknowledgement is part of the publish request, never preselected, and logged with the lists and versions acknowledged. It applies to publish only, not to a decline. In the demo the 3 `SRC-PRACT` summaries are always uncited, so it appears on every publish. |
| H10a | **Decline** to publish (G3), with a written reason *(the chosen next step is deferred, DL-22: in the MVP a decline ends the run as declined)* | No (draft and history kept) | No (nothing published; no approval cancelled) | No (any previous published version stays visible) | No | **Ask**, reason required | Existing · SD FR-022, US-010 AC8–AC9 |
| H11 | **Publish** while G1 or G2 is incomplete or any entry is out of date | Yes | Yes | Yes | Yes | **Never** | Existing · SD MP-006, US-010 AC2–AC3 |
| H11a | **Publish** without the G3 acknowledgement, or with one made for lists that have changed since they were shown | Yes | Yes | Yes | Yes | **Never** | Existing · SD FR-030, AC-037, US-010 AC14, DL-30. Refused (`ACK_REQUIRED`) and logged; a row rejected after the page loaded makes the old acknowledgement stale. |
| H12 | **Approve** as a second specialist (four-eyes) | — | — | — | — | **Not in this map** | Existing: timing undecided · SD OQ-5, PRD OQ-1 |
| H13 | **Abandon** an active run **while it waits at G1, G2 or G3**, with a written reason | Yes (the run is final) but it loses nothing: no decision, row, verdict, draft, audit entry or published calendar is undone | No (closes the run only) | No (GPs keep the last published version) | No | **Ask**, reason required | Existing · SD AC-035, US-015 AC20–AC21, DL-29 (SAD W-19a). Not a general cancel: no call cancel, undo, rollback or deleted draft. Only a run waiting at a gate; a stale screen or a double submit is refused. |
| H13a | **Abandon** a run while a stage is running | — | — | — | — | **Never** | Existing · SD AC-035, US-015 AC20, DL-29 (SAD run state model rule 8, `RUN_STAGE_RUNNING`). The stage ends by itself (A15, A25), so abandon never leaves model calls running for output nobody will use. |

### 4c. GP actions

| # | Action | Hard to undo? | Changes their things? | Reaches others? | Would surprise them? | Rule | Why / evidence status |
|---|---|---|---|---|---|---|---|
| G1r | **View** the published calendar | No | No | No | No | **Alone** | Existing · SD FR-015, US-011 |
| G2r | **Change** any data as a GP | Yes | Yes | Yes | Yes | **Never** | Existing · SD NFR-010, US-011 AC6. Refused on the server, not only hidden. |
| G3r | **View** the read-only "being prepared" message before the first publication | No | No | No | No | **Alone** | Existing · SD AC-013, US-011 AC7, DL-27. States only that work is in progress: no entry, count, status or draft content, and no notification. Separate from the review notice (future scope). |

### 4d. Stretch: change monitoring (F10, Could)

Built only after F1–F9 pass. Not part of the Week 6 definition of done (PRD F10).

| # | Action | Hard to undo? | Changes their things? | Reaches others? | Would surprise them? | Rule | Why / evidence status |
|---|---|---|---|---|---|---|---|
| S1 | **Assess** which rows, verdicts and entries an amendment affects, with reasons | No (report) | No | No | No | **Alone** | Existing · SD MD-011, FR-021, US-014 AC7 |
| S2 | **Flag** affected items and mark their entries out of date | No | Yes (status only, toward safety) | Notice only: GPs keep the last published version and see the review notice if a published item is flagged (FR-025, US-014 AC10) | No (specified) | **Alone** | Existing · SD AC-018, AC-019. Same exception as A12. |
| S3 | **Accept** an impact report, including a "no impact" conclusion, or send the amendment for manual review | Uncertain (a miss is silent) | No (review status only) | Possibly (a stale GP entry stays; no notice without flags) | Uncertain | **Ask**, required for every report if the stretch is built | Existing · SD FR-026 (Could), AC-025, US-014 AC11–AC17. Under P-1, "no impact" is the expensive mistake. Sign-off reduces the risk of a silent miss; it does not guarantee completeness. |
| S4 | **Apply** an amendment to a row, verdict or entry | Yes | Yes | Yes | Yes | **Never** | Existing · SD MD-011, US-014 AC8 |
| S5 | **Watch** live sources or notify GPs of changes | — | — | Yes | Yes | **Never** in the MVP | Existing: deferred · US-014 scope notes, SD MN-002. The neutral review notice (FR-025) is not a change notification: it shows no amendment detail. |

---

## 5. Ask moments (approval cards)

Each card answers the five card questions. Summaries stay short. Evidence stays one click away. No card
has a time limit: consequential expert review takes as long as it takes (the 30-minute target in SD
MC-003 is a measurement, not a cut-off).

**For every card:** no preselected choice, no bulk "approve all", and silence, a timeout or closing the
screen is not consent: undecided items stay pending (Existing: PRD §6, US-004 AC12–AC13, US-007
AC10–AC11, US-010 AC10, US-014 AC15). Safe default *values* are still allowed. The decision is recorded
with who, when, the version decided on, and any reason (Existing: SD MD-009, AC-016, US-012 AC2. The
version is the row's at G1, the verdict's at G2 and the calendar's at G3; the version scheme is for the
SAD, OD-11).

### Card G1: approve, edit, reject or reopen one rule (H1, H2, H4, H4a, H5) *(edit and reopen: future scope, DL-22)*

| | |
|---|---|
| **Authorised role** | Compliance specialist (mocked) · SD NFR-010 |
| **Unit of approval** | One row, including its business-day rule · SD MD-004 |
| **Evidence shown** | Fields, paragraph ID, verbatim quote, quote-check result, conflict flags with the other source's text · US-004 AC1, PRD §6. The coverage view lists every paragraph no non-rejected row cites · SD FR-028 (A23) |
| **Blocks** | Failed quote check or missing paragraph ID: approval unavailable (H3). A row marked "demo": approval unavailable, reject only (H3a). Remaining flag: approval needs a reason. G1 completes only when every row is approved or rejected · SD MN-006, AC-006, US-004 AC6, FR-031 |
| **1. What is proposed?** | "Add this rule to the library: *what, who files, anchor + offset*, from paragraph *ID*." |
| **2. Why now?** | Every row has been verified. Applicability cannot start until all rows are decided. |
| **3. What changes if approved?** | The row enters the library with the chosen business-day rule. It goes to applicability. Nothing reaches a GP until G3. |
| **4. How is it undone?** | In the MVP: reject the row with a written reason, or abandon the run (H13) and start a new one. *Future scope (DL-22).* Edit an approved row; it returns to pending and is re-verified (FR-007). Reopen a **rejected** row with a reason, before or after publication (FR-023). After G3, GPs see the review notice until republish (FR-025); see Card G3. |
| **5. Edit or decline?** | Approve, or reject with a written reason · US-004 AC3. *Future scope (DL-22).* Edit any field of a pending or approved row (re-verifies that row only); a rejected row can't be edited until it is reopened · US-004 AC11, US-005 AC1 |

### Card G2: confirm, override, decide or reopen one verdict (H6–H8, H6a) *(reopen: future scope, DL-22)*

| | |
|---|---|
| **Authorised role** | Compliance specialist (mocked) |
| **Unit of approval** | One verdict for one approved row and fund `FND-DEMO-01` · SD MD-004 |
| **Evidence shown** | Verdict, reasoning, cited fact IDs **with their values** · US-007 AC1 |
| **Blocks** | G2 cannot complete while any verdict is "unsure" · SD AC-008 |
| **1. What is proposed?** | "This rule *applies / does not apply / is unsure* for the fund, because *facts*." |
| **2. Why now?** | All approved rows have a verdict. Dates cannot be calculated until every verdict is decided. |
| **3. What changes if approved?** | "Applies" verdicts feed the calendar; "does not apply" removes the rule from it. Precautionary resolutions are stored as **applies** with the note "precautionary: registration unconfirmed" · US-007 AC6 |
| **4. How is it undone?** | In the MVP: abandon the run (H13) and start a new one. *Future scope (DL-22).* Reopen the verdict with a reason, before or after publication, without editing the row; it returns to pending G2 and its entries go out of date (FR-024). If the rule itself has changed, edit the row instead; the verdict then goes back through G2 (FR-007). |
| **5. Edit or decline?** | Override with a written reason, to any verdict except "unsure" · US-007 AC3, assumption |

### Card G3: publish (with the acknowledgement) or decline the whole fund calendar (H10, H10a, H11a)

| | |
|---|---|
| **Authorised role** | Compliance specialist (mocked) |
| **Unit of approval** | The whole fund calendar version, published at once. Deliberately atomic; not split into per-entry cards · SD A-6, US-010 AC5 |
| **Evidence shown** | All entries with roll notes, "roll rule unconfirmed" marks and precautionary notes · US-010 AC1. Each entry's trail (source, quote, verdict, approvals) is reachable · SD MP-005. **What was left out:** every row rejected at G1, with the reason given at rejection (a demo row keeps its "demo" label), and every source paragraph no non-rejected row cites, with its text · SD FR-030, US-010 AC14, DL-30 |
| **Blocks** | G1 or G2 incomplete; any entry out of date · US-010 AC2–AC3. No acknowledgement of the rejected rows and uncited paragraphs, or one made for lists that have since changed (H11a) · SD AC-037. Safe-default marks do **not** block · US-010 AC4 |
| **1. What is proposed?** | "Publish *N* entries for the fund to the GP view. These rows were rejected and these paragraphs are cited by no row: I have seen them." One explicit acknowledgement, never preselected, given as part of the publish decision. |
| **2. Why now?** | The calendar was generated from current G1 and G2 approvals, and no entry is out of date. G3 is the last point to catch a missed or wrongly rejected row before GPs rely on the calendar (P-1). |
| **3. What changes if approved?** | Every GP sees this calendar. The acknowledgement is logged with the rejected rows (and their versions) and the uncited paragraphs it covered. Before the first G3 they see the read-only "being prepared" message (G3r), or the previous published version. · SD AC-013, US-010 assumption, DL-27 |
| **4. How is it undone?** | **No unpublish or withdraw exists.** It is deliberately deferred for the demonstration and must be revisited before real-world use (SD §9). Recovery in the MVP: start a new run and publish again; GPs keep the old version until then · US-010 assumption. *Future scope (DL-22).* The neutral review notice while a correction questions the published calendar (FR-025), and correcting through G1/G2 (FR-023, FR-024, MD-005). The notice warns but does not undo GP reliance on the old version. |
| **5. Edit or decline?** | Decline with a **required** reason. *Deferred (DL-22): the chosen next step, a rule needs correcting (G1) or a verdict needs review (G2, by reopening it). In the MVP a decline ends the run as declined, and correcting means a new run.* Nothing new is published, the draft and history are kept, and no earlier approval is cancelled. A decline needs no acknowledgement · SD FR-022, FR-030, US-010 AC8–AC9 |

### Card S3 *(stretch; required for every report if built)*: accept an impact report

| | |
|---|---|
| **Authorised role** | Compliance specialist |
| **Unit of approval** | One version of one impact report, for one version of its source amendment · SD FR-026, US-014 AC16 |
| **Evidence shown** | Affected items with reasons, and items checked and found unaffected · US-014 AC7 |
| **1. What is proposed?** | "Amendment *X* affects *these* items / *no* items." |
| **2. Why now?** | An amendment has arrived; until checked, the library may be out of date. |
| **3. What changes if approved?** | Only the review status. Flags stay, invalidated approvals are not restored, flagged items still need G1 or G2, and any GP notice stays until republish. Accepting "no impact" closes the check · SD FR-026, US-014 AC12 |
| **4. How is it undone?** | Re-run the assessment, or correct items through the existing paths: edit (MD-005), reopen (FR-023, FR-024). A re-run report or revised amendment is unreviewed again; the earlier acceptance stays in the log and does not carry over · SD FR-026, US-014 AC16 |
| **5. Edit or decline?** | Send the amendment for manual review with a logged reason. It stays open until completed with a note that records the conclusion and any resulting corrections. If the report or amendment is revised meanwhile, the review is marked superseded (notes kept), the amendment stays queued against the new versions, and completion is refused for superseded versions. Accepting the revised report is no shortcut: a referred amendment closes only by completing the manual review with a note · SD FR-026, US-014 AC13, AC17 |

---

## 6. Trust and recovery

### Promotion policy

**No Ask → Alone promotion for G1, G2 or G3.** They are fixed project gates (SD MD-004, MN-003), not
trust settings. A run of approvals without edits is not evidence of safety; the no-edit rate is
deliberately deferred and is not a promotion signal (PRD OQ-2). Demo decisions are scripted (story
index), so any streak would measure the script.

If a promotion is ever proposed (for example, letting S3 "no impact" reports skip the sign-off that FR-026 now requires), it
would need, at minimum: an agreed evidence threshold from the evaluation report (US-013), a visible
notice to the specialist, and a way to revoke it. **None is proposed for the MVP.**

### Recovery (Show it · Fix it · Learn from it)

| Wrong turn | Show it | Fix it | Learn from it | Status |
|---|---|---|---|---|
| Agent fails or returns invalid output, a step or stage times out, or the backend restarts mid-stage | Plain message names the step, the unit and the reason ("service restarted" after a restart); the run ends `FAILED` and nothing moved forward | Start a new run. No run is left active by a crash: the start-up rule fails it (A25) | Failure logged (a restart as a system event) | Existing · SD NFR-004, AC-033 to AC-036, DL-29. *Future scope (DL-22).* Re-running the failed step from the last safe state, and the re-run limit (OD-7, 3 per unit in the SAD) |
| Wrong rule approved, found before G3 | Row status and flags on the review surface | In the MVP: abandon the run and start a new one. *Future scope (DL-22).* Edit → re-verify → re-approve → G2 → regenerate | Before/after values in the audit log | Existing · SD FR-007, US-005 AC6 (edit: future scope) |
| Wrong rule rejected | Row status on the review surface; its paragraph is listed again in the coverage view (A23) | In the MVP: start a new run. *Future scope (DL-22).* Reopen with a reason → re-verify → G1 → G2 → regenerate | Rejection (and reopening) in the audit log | Existing · SD FR-023 (reopen: future scope) |
| Wrong verdict confirmed | Verdict and cited facts | In the MVP: abandon the run and start a new one. *Future scope (DL-22).* Reopen the verdict with a reason (judgement-only), or edit the row if the rule changed | Audit log | Existing · SD FR-024, FR-007 (future scope) |
| Wrong entry published | *Future scope (DL-22).* Neutral calendar-level review notice for GPs, with the publication date of the version shown | In the MVP: start a new run and publish the whole calendar again; GPs keep the old version until then. *Future scope (DL-22).* Correct, regenerate, republish; the notice clears only then | Audit log | Existing · SD FR-025 (future scope). Withdrawal deliberately deferred (SD §9). |
| A row was missed | The coverage view lists the uncited paragraph (A23) | In the MVP: start a new run. *Future scope (DL-22).* Create the row by hand (FR-027) | Evaluation counts the miss (SD MP-001) | Existing · SD FR-028; manual row creation is future scope (DL-15, DL-22) |
| A run waiting at a gate is not wanted (for example after a wrong rejection) | Run status shows its state | Abandon it with a written reason (H13), then start a new run; nothing is undone. A running stage cannot be abandoned (H13a); it ends by itself | Abandon recorded with who, when, reason and stage | Existing · SD AC-035, AC-036, DL-29 |
| Planted demo row at G1 *(demo run only)* | Labelled "demo"; approve is unavailable | Reject it with a written reason; it then appears in the G3 rejected list | Rejection in the audit log | Existing · SD FR-031, AC-038, DL-31 |
| Calendar declined at G3 | The run ends `DECLINED`; the draft and review history stay with the specialist | Start a new run | Decline and reason in the audit log | Existing · SD FR-022, AC-021, US-010 AC8–AC9 |
| Verifier false alarm | Flag shown with both texts | Approve with a reason | Eval report counts false alarms (SD MP-003) | Existing |
| Verifier miss | Not visible at the time | Reject the row, or caught by evaluation. *Future scope (DL-22).* Specialist edit | Proposed: add the case to the answer key by an explicit operator decision | Proposed |
| Impact assessment misses an item *(stretch)* | Not visible; no GP notice without a flag | Specialist must accept every report, or send it for manual review | Same as above | Existing · SD FR-026. Reduces the risk of a silent miss; does not guarantee completeness. |

Learning never widens permissions, rewrites requirements or trains on data. No feedback store or
adaptation mechanism is specified; any such mechanism would be a new proposal.

---

## 7. Engineering review additions (Proposed, not framework or requirements)

These are controls the SAD and Build should decide. None exists yet.

### Enforcement

Prompts, this map and the skill are guidance only. Enforcement must live in code:

| Control | Where it must be enforced | Trace |
|---|---|---|
| Agents get read-only tools limited to mock sources and the fund profile | Agent tool lists in the runtime (CrewAI per config) | PRD §3 tool boundaries |
| Gate transitions refuse to advance without the matching approval | Backend state machine, not the UI | SD MN-003, MP-006 |
| Approve, reject, override, reopen, publish, decline (and, in the stretch, report acceptance) accept only the specialist role | Backend endpoints; hiding UI buttons is not enforcement | SD NFR-010 |
| GP endpoints are read-only and return published entries only, or the "being prepared" message before the first publication (*Future scope (DL-22).* plus the neutral review notice when one is active) | Backend | SD MN-007, NFR-010, AC-013, DL-27 (FR-025) |
| Agent output is schema-validated before a gate sees it | Backend, between agent and storage | SD NFR-004 |
| Failed quote check blocks approval regardless of model output | Deterministic verbatim match in code (OD-8 closed, SAD W-04) | SD MN-006 |
| Dates have no model call path | Due-date module; tested without a model | SD MN-005, NFR-011 |
| One run is active at a time; starting a second is refused and names the active run | Backend run-state code, not the UI | SD AC-036, US-015 AC16 (SAD CR-023) |
| A step failure, step timeout or stage time limit ends the run `FAILED`; at start-up, a run whose stage was running becomes `FAILED` ("service restarted"); abandon needs a reason, only the specialist, only a run waiting at a gate, and undoes nothing | Backend run-state code, the start-up routine and the abandon endpoint | SD AC-033 to AC-035, NFR-010, DL-29 (SAD run state model rules 6–8) |
| Publish carries the G3 acknowledgement of the current rejected rows and uncited paragraphs | Backend publish endpoint (`ACK_REQUIRED`); an unticked box in the UI is not the control | SD FR-030, AC-037, DL-30 (SAD CR-028) |
| The demo switch is off by default and audited when on; a `demo` row can only be rejected; an evaluation run refuses to start with the switch on | Backend: run start, row decision endpoint (`DEMO_ROW_NOT_APPROVABLE`) and evaluation runner | SD FR-031, AC-038, DL-31 (SAD CR-029) |
| A decision made on an out-of-date screen, or submitted twice, is refused | Backend, on the version carried by every decision | SAD CR-009, US-004 AC18, US-007 AC12, US-010 AC13 |
| Audit log rejects update and delete | Storage layer | SD NFR-003 |

### Approval freshness

| Approval | Covers (the recorded version, SD MD-009; ID scheme OD-11) | Invalidated by | Then | Status |
|---|---|---|---|---|
| Any decision (G1, G2, G3) | The version of the row, verdict or calendar on the specialist's screen | A change since the screen loaded, or a second submit | The decision is refused with a plain message showing the current version; one decision is recorded | Existing · SAD CR-009, US-004 AC18, US-007 AC12, US-010 AC13 |
| G1 (row) | Field values, business-day rule, flags and reason at approval time | Any edit to that row | Row → pending; re-verify; its verdict re-runs and needs G2 again; its entries → out of date | *Future scope (DL-22).* Existing · FR-007, US-005 AC4–AC5 |
| G2 (verdict) | Verdict, reasoning and cited facts for one row version | Re-approval of the row after edit | Re-run applicability; G2 again before entries regenerate | *Future scope (DL-22).* Existing · US-005 AC5 |
| G2 (verdict) | As above | Reopening the verdict with a reason | Verdict → pending G2; its entries → out of date; the rule keeps G1 approval | *Future scope (DL-22).* Existing · FR-024 |
| G2 (verdict) | As above | A change to fund facts | Deferred beyond the MVP (static mock profile). Direction recorded: reassess with the new facts, then fresh G2 | Deferred · SD OQ-9, §9 |
| G3 (calendar) | One calendar version | Any later out-of-date entry or regeneration | New G3 required; GPs keep the last published version, with the review notice if a change questions it | Existing · US-010 AC3, assumption. *Future scope (DL-22).* The review notice (FR-025). In the MVP a changed calendar means a new run and a new G3. |
| *(stretch)* any | As above | Impact flag | Back to G1 or G2 per KEY §6 | Existing · SD MD-011 |
| *(stretch)* report acceptance or manual-review completion | One report version for one amendment version | A re-run report or revised amendment | Amendment → unreviewed; fresh acceptance or manual review needed; earlier decision kept in the log. An open manual review is marked superseded (notes and version references kept), and completion is accepted only for the current versions | Existing (only if built) · SD FR-026, AC-025, US-014 AC16–AC17 |

Prior decisions stay in the audit log. Consent never carries over to changed content.

### Corrections

In the MVP, correcting anything means a new run, after abandoning the current run if it waits at a gate (H13). Reject a row
with a reason, or decline at G3; then start a new run (H0a). The items below are **future scope (DL-22)**:
they are agreed and designed, and not built.

- **Draft edit** (pending row): re-verify that row only. Existing, US-005 AC1. *Future scope.*
- **Approved-state correction**: edit → pending → re-approval chain. Existing, FR-007. *Future scope.*
- **Rejected-row recovery**: reopen with a reason (rejected rows are read-only until then). Existing,
  FR-023. *Future scope.*
- **Judgement-only verdict correction**: reopen the verdict with a reason. Existing, FR-024. *Future scope.*
- **Published replacement**: republish the whole calendar; GPs see the review notice meanwhile.
  Existing, FR-025 (the notice is *future scope*; in the MVP a new run and a new publish). **Withdrawal:
  none exists**, deliberately deferred (SD §9). Hiding an entry would not undo a GP's reliance on it.

### Failure and retries

Fail closed at every gate (SD NFR-004). In the MVP a failed step (invalid output, a failed call after
its one automatic retry, a step timeout, the stage time limit, or the cost cap) ends the run as
`FAILED` (terminal): nothing moves forward, no gate opens for the failed stage, recorded decisions stay,
and a new run follows. When the backend starts, a run whose stage was running is failed with the reason
"service restarted" (A25). So every running stage ends on its own, and abandon is needed only for a run
waiting at a gate (H13). Nothing is undone. Calendar generation is all-or-nothing, so a partial draft
never reaches G3; publishing the same version twice creates no second version. Existing · SD NFR-004,
AC-033 to AC-036, DL-29; SAD run state model.

*Future scope (DL-22):* the last safe state as a place to resume from, re-running a failed step or unit
so that it replaces its own failed draft, the re-run limit (OD-7; 3 per unit in the SAD), "needs
attention", and the release of a failed document to manual entry.

### Audit

Record actor, time, action, version, decision and reason (Existing: SD MD-009, AC-016, US-012). Every
approval decision records the version of the row, verdict or calendar it was made on; in the stretch,
report acceptance, referral and manual-review completion record the report and amendment versions
(FR-026), and superseding a manual review is logged as a **system event** (system actor; time,
triggering revision, affected review, old and new versions), kept distinct from human decisions (SD
MD-009). The version scheme is for the SAD (OD-11).
Reasons are required for rejections, overrides, reopenings (FR-023, FR-024; future scope, DL-22), G3 declines (FR-022), abandoning a run (AC-035) (a demo row is rejected with
a reason like any other row, FR-031) and, in the stretch, sending an amendment for manual review
(FR-026). A publish also records the acknowledged lists and row versions (FR-030); turning the demo
switch on is recorded (FR-031), and so is a restart failure, as a system event (A25). Distinguish an **override** (approval
over a conflict flag, with reason; allowed) from an **unresolved failure** (failed quote check, "unsure" at G2 close, out-of-date entries at G3; never overridable).
Tamper-evident storage is deferred (US-012); no storage guarantee is claimed.

### Proposed test matrix

Deterministic tests run without a model (SD NFR-011). Model-quality checks belong to the evaluation
report (US-013). A passing test is bounded evidence, not a safety claim.

| ID | Setup | Action | Observable result | Kind | Trace |
|---|---|---|---|---|---|
| T-01 | All gates completed with current approvals | Publish | 22 entries visible to GP | Deterministic | Existing · SD AC-009, AC-013 |
| T-02 | G1 incomplete | Call the publish endpoint directly | Refused and logged | Deterministic | Existing · SD MP-006, US-010 AC7 |
| T-03 | G2 has an "unsure" verdict | Call the G2-complete endpoint directly | Refused | Deterministic | Existing · SD AC-008 |
| T-04 | Row with failed quote check | Approve with a reason via API | Refused | Deterministic | Existing · SD AC-004, MN-006 |
| T-05 | Row with conflict flag | Approve without, then with, a reason | Refused, then approved with reason logged | Deterministic | Existing · SD AC-006 |
| T-06 | GP role | Call any write endpoint | Refused | Deterministic | Existing · US-011 AC6 |
| T-07 | Agent tool configuration | Inspect each agent's tools | No write, approve or publish tool | Deterministic | Proposed · PRD §3 |
| T-08 | Verifier on any row | Inspect row before and after | Row fields unchanged | Deterministic | Existing · SD MN-004 |
| T-09 | `OBL-02` approved at G1 and G2, published | Edit its offset | Row pending; verdict needs G2; 4 entries out of date; publish refused; GP still sees last published version, with the review notice | Deterministic | *Future scope (DL-22).* Existing · US-005 AC4–AC5, US-010 AC3, US-011 AC9 |
| T-10 | Approval recorded on version *n* | Edit to *n+1*, then try to reuse the old approval | Refused; old decision kept in log, naming version *n* | Deterministic | *Future scope (DL-22).* Existing · SD MD-009, AC-016, FR-007 · version scheme for the SAD (OD-11). The stale-screen check that stays in the MVP is T-31. |
| T-11 | Agent returns invalid output | Run | Run stops, failure logged, no state advances | Deterministic (stubbed agent) | Existing · SD NFR-004 |
| T-12 | Calendar generation fails midway | Open G3 | No partial calendar offered | Deterministic | Proposed · SD NFR-004 |
| T-13 | Same version | Publish twice | One published version | Deterministic | Proposed |
| T-14 | Any log entry | Update or delete | Refused | Deterministic | Existing · US-012 AC4 |
| T-15 | Full demo run | Read the log | Every decision with who, when, what, reason where required, and the version each approval decision was made on | Deterministic | Existing · SD AC-016, US-012 AC2 |
| T-16 | Mock data | Run extraction, verifier, applicability | Matches answer key | Model evaluation | Existing · SD MP-001 to MP-003 |
| T-17 *(stretch)* | `AMD-01`/`02`/`03` | Assess impact | Flags match KEY §6; nothing changed by the system | Model evaluation + deterministic check | Existing · SD AC-018 to AC-020 |
| T-18 | Generated calendar | Decline without, then with, a reason *(next step deferred, DL-22)* | As US-010 AC8–AC9 | Deterministic | Existing · SD AC-021 |
| T-19 | Rejected row, before and after publication | Edit it directly; reopen without, then with, a reason; try to publish | As US-004 AC9–AC11 | Deterministic | *Future scope (DL-22).* Existing · SD AC-022 |
| T-20 | Confirmed verdict, before and after publication | Reopen without, then with, a reason; try to publish | As US-007 AC8–AC9 | Deterministic | *Future scope (DL-22).* Existing · SD AC-023 |
| T-21 | Published calendar | Fire each FR-025 trigger in turn; separately, do draft work that does not affect it | As US-011 AC9 (stretch trigger: US-014 AC10) | Deterministic | *Future scope (DL-22).* Existing · SD AC-024 |
| T-22 | Review notice active | Decline; fail a publication; then publish successfully | As US-011 AC10 | Deterministic | *Future scope (DL-22).* Existing · SD AC-024 |
| T-23 | G1, G2 and G3 screens | Look for bulk or preselected decisions; close the screen or time out with items undecided | As US-004 AC12–AC13, US-007 AC10–AC11, US-010 AC10 (stretch: US-014 AC15) | Deterministic | Existing · SD AC-026 |
| T-24 *(stretch, only if built)* | Impact reports for `AMD-01` to `AMD-03` | Accept `AMD-03`'s "no impact" report; refer another for manual review, then complete it with a note; after each step, check flags, approvals and gate state; re-run one accepted report; re-run a report while its manual review is open, accept the revised report, then try to complete against the old version, then the new one; read the log | As US-014 AC11–AC14 and AC16–AC17: acceptance and completion never clear flags, restore approvals or bypass G1–G3; each decision names the report and amendment versions; the re-run report is unreviewed; the open review is superseded with notes kept; accepting the revised report leaves the amendment unresolved; completion against the old version is refused and against the new one accepted; the log shows the superseding as a system event with triggering revision and old and new versions | Deterministic | Existing · SD AC-025 (FR-026, Could) |
| T-25 | A run started with the demo switch on, so G1 shows a row marked demo | Approve the demo row through the API, with and without a reason; then reject it with a reason | Every approval refused with a plain message and logged; the row stays pending and G1 cannot complete; the rejection is accepted and logged | Deterministic | Existing · operator decisions DL-31, SAD SOQ-18, SD AC-038 · SAD CR-029, T-DEMO-2 |
| T-26 | A run is active | Start another run | Refused with a message that names the active run; the active run is unchanged | Deterministic | Existing · SD AC-036, US-015 AC16 (SAD T-RUN-0) |
| T-27 | A model step returns invalid output | Let the stage end; then start a new run | The run is `FAILED` (terminal) with the step, unit and reason named; no gate opens; recorded decisions are kept; the new run is allowed | Deterministic (stubbed agent) | Existing · SD AC-033, AC-036, US-015 AC19 (SAD T-RUN-1) |
| T-28 | A stubbed step never returns | Wait past its time limit | The unit fails and the run is `FAILED` | Deterministic (stubbed agent) | Existing · SD AC-034, US-015 AC19 (SAD T-RUN-2) |
| T-29 | An active run waiting at a gate, with recorded decisions | Abandon without, then with, a reason; abandon again; abandon a `FAILED` run | Refused; then `ABANDONED`, one audit entry (who, when, reason, stage), nothing undone, GP view unchanged, a new run allowed; the repeats are refused | Deterministic | Existing · SD AC-035, US-015 AC20–AC21 (SAD T-RUN-3, T-RUN-4) |
| T-30 | The six demo rows at G1 | Open the coverage view; reject a row | Lists the 7 uncited paragraphs; a paragraph whose only row is rejected is listed again | Deterministic | Existing · SD AC-029, US-001 AC8, AC10 |
| T-31 | No calendar has been published | Open the GP view | The read-only "being prepared" message; no entries, count or status; no notification | Deterministic | Existing · SD AC-013, US-011 AC7, DL-27 |
| T-32 | A decision screen goes stale (the row, verdict or calendar changes) | Submit the old decision; submit a decision twice | Refused with a plain message showing the current version; one decision recorded | Deterministic | Existing · SAD CR-009, US-004 AC18, US-007 AC12, US-010 AC13 |
| T-33 | A generated calendar | Decline with a reason; then start a new run | The run is `DECLINED`; audit entry; draft kept; GP view unchanged; a new run is allowed | Deterministic | Existing · SD AC-021, AC-036, US-010 AC8 (SAD T-RUN-5) |
| T-34 | A stage is running | Abandon the run, with a reason | Refused (`RUN_STAGE_RUNNING`) with a plain message; the run and the stage are unchanged; nothing is recorded as abandoned | Deterministic (stubbed agent) | Existing · SD AC-035, US-015 AC20, DL-29 (SAD run state model rule 8; no SAD test ID yet) |
| T-35 | A stubbed stage that passes its stage time limit; separately, a run with a stage running when the backend stops | Wait past the limit; restart the backend | Each run is `FAILED`, the second with the reason "service restarted" logged as a system event; recorded decisions kept; a run waiting at a gate is unaffected by the restart; a new run is allowed | Deterministic (stubbed agent) | Existing · SD AC-034, US-015 AC19, DL-29 (SAD run state model rules 6–7; no SAD test ID yet) |
| T-36 | A generated calendar, one row rejected at G1, uncited paragraphs | Publish without the acknowledgement; with one for an older list (a row rejected after the page loaded); with the current lists; decline without it | Refused, refused, then published with the acknowledged lists and versions in the audit log; the decline needs no acknowledgement | Deterministic | Existing · SD AC-037, US-010 AC14, DL-30 (SAD CR-028, T-G3ACK-1) |
| T-37 | Start a run with the switch off, then with it on; start an evaluation run with it on | Count rows; read the audit log | Off: 6 rows, no demo row, no switch entry. On: 7 rows, the 7th labelled "demo", passing the quote check, and an audit entry for the switch. Evaluation run refused | Deterministic | Existing · SD AC-038, DL-31 (SAD CR-029, T-DEMO-1) |

---

## 8. Open decisions

> **Original record.** The two tables below show the state when this map was first drafted
> (2026-11-07). They are kept unchanged for history. Most items have since been decided: see
> "Resolved in Define" below for the current outcome of each.

| ID | Decision | Why it matters | Who decides |
|---|---|---|---|
| OD-1 | G3 decline: is a reason recorded? Is there an explicit "reject" at G3? | SD MD-004 says each gate offers approve / edit / reject; US-010 defines only publish (K-1) | Operator (PM) |
| OD-2 | Can a rejected row be reopened, and how? | Rejection currently has no recovery path | Operator (PM) |
| OD-3 | Can a confirmed verdict be changed without editing its row? | Otherwise the only route back is a row edit | Operator (PM) |
| OD-4 | What does a GP see when a published entry is later marked out of date? | MN-007 vs US-010 assumption (K-3); related to PRD OQ-6 | Operator, before UX |
| OD-5 | Is a withdraw/unpublish capability needed? | None exists; do not assume one | Operator |
| OD-6 | Do fund-fact changes invalidate verdicts? | Fund profile is static in the MVP | Operator (future scope) |
| OD-7 | Retry policy for failed agent steps | Duplicate drafts, cost (SD MC-002) | SAD |
| OD-8 | Is the quote check deterministic code, a model, or both? | MN-006 enforcement should not rely on a model saying "pass" | SAD |
| OD-9 | *(stretch)* Does the specialist sign off impact reports, especially "no impact"? | A missed impact is silent | Operator (PM) |
| OD-10 | Four-eyes review: MVP or later? | Would add a second role to G1–G3 cards | Operator (PRD OQ-1, SD OQ-5) |
| OD-11 | Do approval records reference a version ID? | Needed to prove approvals are fresh | SAD |
| OD-12 | Is Next.js the frontend? | Not in the Define documents (PRD A-4 defers to SAD) | Operator / SAD |

### Conflicts found between sources

| ID | Conflict | Sources | Handling at drafting (superseded where resolved below) |
|---|---|---|---|
| K-1 | "Each gate offers approve / edit / reject" vs G3 offering publish only | SD MD-004 vs US-010 | Not resolved; OD-1 |
| K-2 | Change monitoring marks **published** entries out of date, but GPs keep seeing the last published version | US-014 AC2 vs US-010 assumption | Not resolved; OD-4 |
| K-3 | "GP view shows no … conflicted items" vs a published entry later known to be out of date staying visible | SD MN-007 vs US-010 assumption | Not resolved; OD-4 |
| K-4 | Next.js named by the operator but not in requirements | Operator instruction vs PRD A-4 | Treated as Open; OD-12 |

### Resolved in Define (2026-11-07)

`@product-mgr` recorded these as Open Questions and the operator decided them. The decisions now live
in the Define documents; the rows above are kept as the original record.

| Item | Outcome | Now recorded in |
|---|---|---|
| OD-1, K-1, PR-1 | G3 offers publish or decline; a decline needs a reason, publishes nothing new and keeps the draft and history | SD MD-004, MD-009, **FR-022** · US-010 criteria 8–9 |
| OD-2, PR-2 | A rejected row can be reopened with a reason, before or after publication; rejected rows are read-only until reopened | SD **FR-023** · US-004 criteria 3, 9–11 · US-005 scope note |
| OD-3 | A confirmed verdict can be reopened with a reason, for judgement-only corrections | SD **FR-024** · US-007 criteria 8–9 |
| OD-4, K-2, K-3, PR-3 | GPs keep the last published version plus a neutral calendar-level review notice; MN-007 clarified to cover working content | SD MN-007, **FR-025** · US-011 criteria 4, 9–10 |
| OD-5 | Withdraw/unpublish deliberately deferred for the demonstration; revisit before real-world use | SD §9, OQ-8 · US-010 scope notes |
| OD-6 | Fund-fact changes deferred beyond the MVP; direction recorded | SD §9 Future work, OQ-9 |
| OD-9, PR-5 *(stretch)* | Every impact report needs acceptance or a documented manual review, including "no impact" | SD MD-011, **FR-026** (Could) · US-014 criteria 8, 11–15 |
| PR-6 | No bulk or preselected approval decisions; silence leaves items pending | PRD §6 · US-004 (12–13), US-007 (10–11), US-010 (10), US-014 (15) |
| OD-10 | Not duplicated; still open | PRD OQ-1, SD OQ-5 |
| OD-12, K-4 | Recorded as operator intent for the SAD, not a requirement | PRD OQ-8 |
| OD-8 | **Closed.** The quote check is deterministic code, not a model. See SAD **W-04** (and assumption SA-2) | SAD W-04 · SD MN-006 |
| OD-7, OD-11, PR-4 | Left for `@system.arch`, except the PR-4/OD-11 requirement: every G1–G3 decision records the version it was made on (operator decision, later on 2026-11-07). The version scheme stays with the SAD | (SAD) · SD MD-009, AC-016 · US-012 AC2 |

---

## 9. Proposed requirement changes

Each needed operator approval and a `@product-mgr` update before it became a requirement. As of
2026-11-07, PR-1, PR-2, PR-3, PR-5 and PR-6 are **applied** (see §8, "Resolved in Define"). PR-4 is
**applied as a requirement** for every G1–G3 decision; its version scheme is left for the SAD (OD-11).

The Proposal column is the original wording and is kept for history; the Status column gives the
current state.

| ID | Proposal (as drafted) | Would change | Status |
|---|---|---|---|
| PR-1 | Define G3 decline (with optional reason logged), or amend MD-004 wording to match US-010 | SD MD-004, US-010 | **Applied, superseded wording**: the reason is *required*, not optional (SD FR-022) |
| PR-2 | Define a reopen path for rejected rows | US-004 | **Applied** (SD FR-023) |
| PR-3 | Decide post-publish behaviour for out-of-date entries | SD MN-007, US-010, US-011, US-014 | **Applied** (SD MN-007, FR-025) |
| PR-4 | Approval records reference the version they approve | SD MD-009, US-012 | **Applied (requirement)**: every G1–G3 decision records the row, verdict or calendar version it was made on (SD MD-009, AC-016, US-012 AC2, PRD F9). If the stretch is built, impact-report decisions record the report and amendment versions (SD FR-026, US-014 AC16). Still open: the version scheme (SAD, OD-11) |
| PR-5 | *(stretch)* Specialist acceptance of impact reports, including "no impact" | US-014 | **Applied** (SD FR-026, Could) |
| PR-6 | Approval surfaces offer no bulk approve and no preselected choice | PRD §6 | **Applied** (PRD §6) |

---

## Sources

- `project-context/1.define/system-description.md`, `prd.md`, `user-stories/` (US-001 to US-016,
  README), `mock-data/expected-obligation-library.md`
- `project-context/1.define/capstone-brief.md`, `context-summary.md`, `mrd.md` (context only)
- `.cursor/skills/agentic-approval-design/SKILL.md` (method)

## Assumptions

- The current Define set is the "Sprint 1" requirement set. The documents do not use the word "sprint".
- Specialist decisions are listed as Ask rows because the system must wait for them; they are not
  agent actions.

## Open Questions

- See §8 (OD-1 to OD-12) and conflicts K-1 to K-4. Most are resolved (§8, "Resolved in Define").
  Still open: OD-10 (four-eyes review, PRD OQ-1). Closed by the SAD: OD-8 (the quote check is code,
  W-04); OD-7 (one automatic transport retry per call, SAD SOQ-2; manual re-runs are future scope,
  DL-22, so in the MVP a failed step ends the run); OD-11 (integer versions per row, verdict and
  calendar, SAD SOQ-3, CR-009); OD-12 (Next.js, SAD §2).
- SAD SOQ-16 (this map vs the thin slice and the run states) is addressed by the 2026-11-12 update
  below. For `@system.arch`: the Delegation Map's "not in the approval map" notes (DM-01, DM-06,
  DM-14, DM-18) can now cite H0, A23, G3r and H13; SAD source line 25 still calls this map a draft;
  and the SAD has no test IDs yet for the stage time limit and the start-up rule (T-34, T-35 here).
## Audit

- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `create-approval-map` · draft
  from Define documents; no requirement changed; no SAD exists yet
- 2026-11-07 · persona `product-mgr` · action `update` · added "Resolved in Define" table mapping open
  decisions and proposals to the new Define IDs; no other part of the draft changed
- 2026-11-07 · persona `product-mgr` · action `update` · earlier sections aligned with the resolved
  decisions (status line, §1 boundaries, §2 check-in, §3 actors, §4b H4/H4a/H4b/H6/H6a/H10/H10a, §4d S3,
  §5 cards, §6 recovery, §7 freshness, corrections and audit, §9 status); no new decisions
- 2026-11-07 · (unlogged at the time; recorded here) · another session edited A21 (working content,
  FR-025), the G1/G2/G3 card titles (reopen, decline) and the §6 promotion example (FR-026). Actor not
  identified.
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` · aligned
  A14, H5, S2, S5, §3 specialist row, §7 enforcement rows and T-09 with FR-022 to FR-026 and NFR-010;
  §8 tables labelled as the original record; §9 Status column added (PR-1 marked superseded wording);
  traces to new SD AC-021 to AC-025; version reference now Existing for overrides only (operator
  decision, SD MD-009), PR-4 partly applied
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · version requirement
  extended to every G1–G3 decision (SD MD-009, AC-016), superseding the override-only entry above; PR-4
  now applied as a requirement (status line, §5, §7 freshness and audit, §8 resolved row, §9 intro and
  status, Open Questions); T-10 and T-15 updated; new T-18 to T-23 referencing story criteria; no-bulk
  boundary traces SD AC-026; operator decisions
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: report-review decisions record report and amendment versions, and a revised report does not
  inherit acceptance (S3 trace, Card S3, §7 freshness and audit, PR-4 status); new T-24 referencing SD
  AC-025 and US-014 AC11–AC14, AC16; the two stretch open questions resolved; operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: revision during an open manual review (Card S3 step 5, §7 freshness stretch row, T-24 extended;
  SD FR-026, US-014 AC17); operator decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · stretch only, if
  built: no shortcut past a referred review (Card S3 step 5); superseding logged as a system event (§7
  audit, SD MD-009); T-24 extended; operator decisions
- 2026-11-09 · persona `product-mgr` · action `update` · §1 handover status: approved (decision log
  DL-13); map content unchanged
- 2026-11-11 · operator (direct edit) · action `update` · OD-8 closed with a reference to SAD W-04
  (A4 row, §7 enforcement, §8 resolved table, Open Questions); operator decision. This audit line
  added by `@system.arch` at the operator's instruction
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22) · H10a, decision 5 and T-18: the next step after a G3 decline is deferred; a decline ends the run as declined; operator decision
- 2026-11-12 · persona `system-arch` (at the operator's instruction; this file is outside the architect's declared outputs) · action `update` · new H3a (approve a demo row: **Never**) and T-25, from operator decisions DL-31 and SAD SOQ-18; no other row changed. The wider approval-map gaps in SAD SOQ-16 remain with `@product-mgr`
- 2026-11-12 · persona `product-mgr` · action `update` (DL-22, SAD SOQ-16) · map brought in line with the thin slice (first drafted on branch `define-approval-map-thin-slice`, not merged; applied here): new rows A23, A24, H0, H0a, H13, G3r (coverage view, second run refused, start and restart a run, abandon, GP message); A15 and H3 reworded; A7, A9, A12, H4a, H4b, H5, H6a, cards G1 and G2, recovery and freshness tables, corrections and tests T-09, T-10, T-19 to T-22 marked future scope; failure and retries rewritten (a failed step ends the run FAILED); new freshness row, enforcement rows and tests T-26 to T-33 (numbered after `@system.arch`'s T-25); operator decision
- 2026-11-12 · persona `product-mgr` · action `update` (DL-29 to DL-31, SAD SOQ-16) · abandon only at a gate (H13, new H13a **Never**); stage time limit (A15) and automatic fail at start-up (new A25 **Alone**), superseding DL-28; G3 acknowledgement (H10 **Ask**, acknowledgement required; new H11a **Never**; Card G3 evidence, blocks, steps 1–3 and 5); labelled demo switch (new H0b **Ask**, A26 **Alone**; it adds a row and never approves; H3a and T-25 kept); boundary, recovery, enforcement and audit text; tests T-34 to T-37; OD-7, OD-11 and OD-12 marked closed by the SAD; status changed from DRAFT to "matches the SAD"; operator decisions
