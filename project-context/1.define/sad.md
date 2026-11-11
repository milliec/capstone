# System Architecture Document (SAD)

**Product**: Regulatory Intelligence for fund compliance calendars
**Scope**: MVP only (six-week capstone). One fictional Luxembourg UCI Part II fund (`FND-DEMO-01`),
mock data, mocked roles.
**Status**: **In progress.** The five decision headings are filled: Work Ownership, Pattern Decision,
Reference Architecture, Model and Context Strategy, Control Register (plus Production Shape). The
numbered sections 1–10, the extensibility walkthroughs and the six-week estimate are filled by
`*create-sad`. A heading marked *pending* has not been decided and must not be read as a decision.

> **How to read the Trace column.** `SD` = `system-description.md` · `PRD` = `prd.md` · `US` =
> `user-stories/` · `AM` = `approval-map.md` · `DL` = `decision-log.md` · `KEY` =
> `mock-data/expected-obligation-library.md`.

## Input Requirements

**PRD Document**: `project-context/1.define/prd.md`
**MRD**: `project-context/1.define/mrd.md` (evidence note; internal tool, no external market)
**System Description**: `project-context/1.define/system-description.md`
**User Stories**: `project-context/1.define/user-stories/` (US-001 to US-015)
**Approval map and decision log**: `approval-map.md` (draft, proposals only), `decision-log.md`
**MVP Scope**: the one happy path in PRD §2, plus the Must recovery paths (SD FR-022 to FR-025) and
run recovery (US-015). Stretch F10 (US-014) is estimated separately and is not in the definition of done.
**Selected Runtime**: `crewai` (resolved from `AAMAD_TARGET_RUNTIME`; `aamad.config.yml` leaves
`runtime.target` unset)

## System Architecture Specification

### Work Ownership

Each user-visible step is assigned one owner. **Model** means a language-model call. **Existing
system** means deterministic application code (there is no legacy system; the "existing system" here
is the code this project writes, which owns rules and records). **Human** means the compliance
specialist, acting through the review surface. **Collaborative** means draft-and-decide: a model or
code drafts, a human decides, and the decision is the record.

**The lens.** The four behaviour properties of a language model decide what it may own:

- *Probabilistic output* → a model may draft, never decide or record. Every model output is a proposal
  that a human or code checks. Exact-match targets (SD MP-001 to MP-004) are measured, not guaranteed.
- *Knowledge cutoff* → the model is never asked what the law says from memory. It reads the mock source
  paragraphs and fund facts it is given, and every claim must cite one (SD MN-006, MD-002).
- *Limited working memory* → each model step receives only the documents it needs for that step
  (one row and its sources; one row and the fund profile). Nothing is asked to hold the whole library.
- *Steerability* → a model can be talked into a wrong answer by its inputs, so no model output changes
  state. Gates, dates, status and the audit log are code paths with no model in them (SD MN-003,
  MN-005, NFR-003).

Deterministic rules and live records stay with the code that owns them: due dates, business-day rolls,
holiday lists, stable IDs, gate state, approval versions and the audit log.

| # | Step (PRD §2 unless noted) | Owner | Reversibility | Stakes | Accountable party | Rationale and trace |
|---|---|---|---|---|---|---|
| W-01 | Start a run on the mock sources for `FND-DEMO-01` (step 1) | Human (trigger) · existing system (execution) | High: a run creates drafts only | Low | Specialist | One run at a time (PRD A-6). Starting a run changes nothing a GP can see. `SD FR-001`, `US-015` |
| W-02 | Load the 6 mock source documents and split them into paragraphs with stable IDs (step 2, first half) | Existing system | High | Low | Build crew | Pure parsing of known mock text. No interpretation. A model here would add nondeterminism to the IDs every later step cites. `SD FR-001`, `AM A1` |
| W-03 | **Extract** obligation rows (fixed schema, one paragraph ID, verbatim quote, no dates) (step 2) | **Model** | High before G1: drafts can be edited, rejected or discarded | Medium. Wrong row → caught at G1 or by the quote/conflict checks. **Missed row → silent until the evaluation report**, the costlier error under P-1 | Specialist (at G1) · Build crew for the schema check | This is the interpretation work the capstone tests (PRD §1). Output is validated against the row schema in code before anyone sees it; invalid output stops the run (SD NFR-004, US-001 c7). A row's business-day rule defaults to "not confirmed" in code when the model gives none. The extractor's output is the row; any rationale it emits is logged but is not passed to later steps (see W-05). `SD MD-001, FR-002, MN-005` · `US-001` |
| W-03a | **Group possible duplicate or overlapping rows** across documents and show the groups at G1 (step 2, after extraction; *review finding 1*) | **Existing system** (deterministic grouping) | High: a grouping is a display, not a change | Medium: two rows for one obligation would produce double calendar entries if both were approved | Specialist (resolves at G1) · Build crew (grouping rule) | **No model merges rows.** Code groups rows that (a) cite the same paragraph ID, or (b) match exactly on recipient, anchor and offset, or (c) match on recipient and frequency where one cites a primary source and the other a secondary summary (`SRC-PRACT-*`). The group is shown at G1 as "possible duplicates" with a plain warning and every row in it. Resolution is the specialist's ordinary per-row decision: approve one, reject the others with a reason, or edit. The grouping does not block any single row; if a group still has two or more approved rows when G1 is completed, one confirmation with a reason is required and logged (SA-9, CR-022; operator decision 2026-11-11). Groups are logged. `SD MD-004, MN-004` · `US-001 c4`, `US-004 c12` · `AM §6 recovery` |
| W-03b | **Coverage view at G1**: list every loaded source paragraph that no row cites (step 2, after extraction; *review finding 2*) | **Existing system** | High: a view only | High: a **missed row is the costlier error under P-1** and is otherwise invisible until the evaluation report (W-20) | Specialist (scans the list at G1) · Build crew | Pure set difference: loaded paragraph IDs minus cited paragraph IDs, shown with each paragraph's text. The answer key is **not** used at run time; the view makes no claim about which uncited paragraphs contain obligations, it only makes the gap visible. In the demo set, five uncited paragraphs are expected and correct (`US-001 c4`). A real miss is fixed by the specialist adding the row by hand (**W-07a**, DL-15, CR-020). `SD P-1, MP-001` · `US-001 c4` · `DL-10, DL-15` |
| W-04 | **Quote check**: does the quote appear word for word in the cited paragraph? (step 3) | **Existing system** (deterministic match under rule QN-1 below) | High | High: a failed check blocks approval with no override (SD MN-006). The check must be trustworthy | Build crew | **Decides AM OD-8 (operator-confirmed 2026-11-11).** Verbatim matching is a string comparison, not a judgement. A model saying "pass" would be a probabilistic opinion about a deterministic fact, and MN-006 enforcement must not depend on it. The code result is authoritative: it is the thing that blocks G1. The verifier agent (W-05, W-06) receives it as input and cannot overrule it. The verifier is still one separate responsibility (SD MD-003): a code quote check plus a model doing the conflict checks. `SD FR-003, MN-006, AC-004` · `US-002` · `AM §7 Enforcement, OD-8` |
| W-05 | **Internal conflict check**: do the row's fields (anchor, offset, frequency) match what its own quote says? (step 3) | **Model**, flag-only | High: adds a flag, changes no field | Medium: a miss means a wrong field reaches G1 unflagged; the specialist still sees the quote next to the field | Specialist (at G1) | Comparing "+6 months" with "within six months following the end of the financial year" is reading, not string matching: units, wording and anchors vary. A model reads it; code records the flag. The verifier never edits a row (SD MN-004): the capability to write row fields is not given to this step. **Inputs (review finding 6):** the row's fields, its quote, the code quote-check result (W-04) and the cited paragraph. **Not** the extractor's reasoning or prompt: a checker that reads the maker's justification is anchored by it, which defeats the separation MD-003 asks for. `SD FR-004, MD-003, AC-017` · `US-003 c5–c6` · `AM A5, A6` |
| W-06 | **Cross-source conflict check**: does any other source (primary or secondary) disagree with the row? (step 3) | **Model**, flag-only | High | Medium: false alarms cost trust (PRD AB-3); a miss leaves a disagreement to be found by chance (MRD §2) | Specialist (at G1) | Same reasoning as W-05. The model receives the row plus the full mock source set (small: 6 documents) and reports flags with both paragraph IDs and both quotes. As in W-05, it receives nothing from the extractor except the row itself. It must not choose which source is right (SD MN-004). `SD FR-004, AC-003` · `US-003` · `KEY §3` |
| W-07 | Show each verified row with its quote, check result and flags; **record the specialist's G1 decision** (approve + business-day rule, approve over a flag with a reason, edit, reject with a reason) (step 4) | **Human** decides · existing system records | Medium: approvals can be undone by edit (→ pending) and rejections by reopen (FR-023); nothing reaches a GP before G3 | High: this is where a wrong rule enters the library | Specialist | A fixed project gate, not a trust setting (AM §6). Blocks are enforced in code: failed quote check → approval unavailable; remaining flag → reason required; any undecided row → G1 incomplete. No bulk or preselected decisions (PRD §6, SD AC-026). `SD MD-004, FR-005, AC-006` · `US-004` |
| W-07a | **Create a missed row by hand** at G1: open the edit form on an empty row, enter the paragraph ID and fields (*operator decision DL-15, resolves SOQ-7*) | **Human** creates · existing system marks it `origin: human` and routes it through W-04 → W-05/W-06 → W-07 | High before G3: it is a pending row like any other and can be rejected | Medium-high: this is a second write path into the library, and the only one that starts from a person rather than a model; it exists because a missed row is the costliest error (P-1) | Specialist (content and G1 decision) · Build crew (flag and routing) · `@qa.eng` (separate count) | Smallest form: the existing edit form (W-08) on an empty row. **No model is involved in creating it, and no "re-extract" action exists.** The quote check is not skippable: a human-created row with no paragraph ID or a quote not found under QN-1 cannot be saved as approvable (CR-020). It gets its own G1 decision like every row (AC-026). The evaluation report counts human-created rows separately, so they can neither inflate nor hide the extractor's 6-of-6 result (W-20). Logged as a human action with before/after values. `DL-15` · `SD MN-006, MD-005, MD-009, P-1` · `US-005` (edit form) · *SD requirement and story to be added by `@product-mgr`* |
| W-08 | **Edit a row** and re-verify it (step 4; FR-006, FR-007) | **Collaborative**: human edits · code re-runs W-04 and triggers W-05/W-06 on that row only · code invalidates downstream state | Medium: an edit is itself reversible by another edit, but it invalidates the row's G1 and G2 approvals and marks its entries out of date | Medium: a human edit is "the one change nobody checked" unless re-verified (US-005 narrative) | Specialist (content) · Build crew (invalidation logic) | Invalidation is mechanical and must not depend on the specialist remembering: approved row → pending; its verdict → back through G2 after re-approval; its entries → out of date; GP review notice if the published calendar used the row. Before/after values logged. `SD MD-005, FR-007, AC-005` · `US-005` · `AM H5, A12` |
| W-09 | **Gate state and transitions** (G1 complete → applicability may run; G2 complete → calendar may generate; G3 → publish) | **Existing system** (the backend) | n/a (state machine) | Highest: a bypass is the failure the whole design exists to prevent | Build crew · verified by `@security.eng` | Enforced in backend code, never in the UI and never in a prompt. **The backend is the single owner of gate state; the per-stage CrewAI Flows (§2) never decide or remember gate status.** A Flow starts only when the backend triggers it and ends at its gate by returning outputs; the backend decides what the gate state is. Agents receive no tool that can approve, publish or advance work (PRD §3 runtime constraints). Tested without a model (SD NFR-011). `SD MN-003, MP-006` · `AM A13, A14, §7 Enforcement` · `CR-001` |
| W-10 | Load the mock fund profile (fact IDs) and event log (step 5, input) | Existing system | High | Low | Build crew | Static mock data. Read-only in the MVP (SD §9, fund-fact editing out of scope). `SD FR-008` |
| W-11 | **Applicability verdict** per approved row: applies / does not apply / unsure, with reasoning citing fact IDs (step 5) | **Model** | High before G2: every verdict is confirmed, overridden or decided by the specialist | High for a wrong "does not apply" (a deadline disappears, the most harmful error, SD P-1); medium otherwise | Specialist (at G2) | This is the second interpretation task the capstone tests. The model is the only source of "unsure" (US-007 assumption); it is told to prefer "unsure" over a confident guess when facts are missing (P-1). Output is validated in code: one verdict from the allowed set and at least one fact ID that exists in the profile, or the run stops (US-006 c7). Verdicts contain no dates (SD MN-005). `SD MD-002, FR-009, AC-007` · `US-006` · `KEY §2` |
| W-12 | **Record the specialist's G2 decision** (confirm, override with reason, decide "unsure", reopen with reason) and show cited fund facts read-only (step 6) | **Human** decides · existing system records | Medium: a confirmed verdict can be reopened with a reason (FR-024) | High: this decides what is on the calendar | Specialist | G2 cannot complete with any "unsure" (SD AC-008). The **precautionary** label is applied by code from the specialist's decision, never by the model (DL-01): the model's verdict stays "unsure" in the log; the specialist's "applies (precautionary: registration unconfirmed)" is the record. `SD MD-004, FR-010, FR-024, P-1` · `US-007` · `DL-01, DL-04` |
| W-13 | **Generate the calendar**: anchors, offsets, conventions `D-1` to `D-7`, business-day rolls against the mock holiday list, event-triggered entries from the awareness date, stable entry IDs (step 7) | **Existing system** | High: a draft calendar, regenerated at will, invisible before G3 | High for correctness (one wrong date breaks trust, PRD AB-5), but the owner choice removes the probabilistic risk | Build crew · `@qa.eng` (22-entry exact-match test) | A hard requirement, not a choice: no model may compute a date (SD MN-005), and two runs must be identical (SD NFR-001). Runs only after G2 is complete, on approved inputs only (AM A11). All-or-nothing: a partial calendar never exists as a publishable object (SD NFR-004). `SD MD-006, MD-007, FR-011 to FR-013, FR-016` · `US-008, US-009` · `KEY §4–§5` |
| W-14 | Mark dependent verdicts and calendar entries **out of date** after an edit, reopen or (stretch) impact flag | Existing system | n/a (status only; cleared by regeneration) | Medium: status blocks publishing; it adds no content | Build crew | Mechanical consequence of W-08, W-12 and W-15. Must never depend on a human or model remembering to do it. `SD FR-007, FR-024` · `AM A12, S2` |
| W-15 | **Publish or decline** the whole fund calendar (G3) (step 8) | **Human** decides · existing system executes atomically | **Low**: no unpublish or withdraw exists (SD §9, deliberately deferred). Recovery is review notice → correct → republish | **Highest**: this is the only step that reaches GPs | Specialist | One explicit decision for the whole calendar version, never preselected or triggered by timeout (US-010 c10). Code refuses publishing while G1 or G2 is incomplete or any entry is out of date; safe-default marks do not block (P-1). Decline requires a reason and a chosen next step, cancels no earlier approval. The specialist sees the "date conventions unverified" note at G3 (DL-12). `SD MD-004, FR-014, FR-022, MP-006, A-6` · `US-010` |
| W-16 | **GP read-only calendar**: what, when, who, why per entry; one calendar-level "not legal advice / conventions unverified" note; neutral review notice when a change questions the published version (step 9) | **Existing system** (rendering published data only) | n/a (read-only) | High: GPs rely on it; must show only published content | Build crew · `@ux.designer` (wording) | Read-only is enforced on the server, not by hiding buttons (AM G2r). The view reads only the published version; draft, flag and reasoning data are not sent to it (SD MN-007, FR-025). `SD FR-015, FR-020, FR-025, NFR-010` · `US-011` |
| W-17 | **GP-facing "why" text** for each entry (plain-English reason + citation + quote) (step 9) | **Collaborative**: model drafts the reasoning at W-11 · specialist confirms, overrides or decides at G2 · code renders the result with the citation and quote | Medium: reopening the verdict (FR-024) replaces it | High: a GP reads it as the explanation; it must not imply permission (DL-01) | Specialist (content, via G2) · `@ux.designer` (voice check and field design, DL-05) | **Rule (review finding 5): the GP sees the reasoning of whoever made the final decision.** (a) *Confirm* → the model's reasoning, exactly as confirmed. (b) *Override* → the specialist's written reason replaces the model's reasoning; the model's text stays in the audit log only. (c) *Decide "unsure"* → the specialist's written reason, plus the code-generated "precautionary" label and its note when the decision is "applies (precautionary)". For a "does not apply" decision there is no entry and so no GP text. **Therefore a G2 override or "unsure" reason must be GP-readable**: plain British English for a non-lawyer, no implied permission (SD NFR-005, DL-01, DL-05). The G2 form says so next to the field (SA-8; wording by `@ux.designer`). G1 reasons are specialist-only and are not shown to GPs. No model runs on the GP path. `SD MD-008, NFR-005, P-1` · `US-007 c3, c5–c6`, `US-011 c2–c5` · `DL-01, DL-05` |
| W-18 | **Audit log**: append every agent output, every human decision (with who, when, what, reason, version decided on) and every gate opening; refuse update and delete | Existing system | n/a (add-only by design) | High: this is the evidence for MP-008 and the review-time measurement (MC-003) | Build crew · `@security.eng` (verifies add-only) | Mandatory bookkeeping with no decision in it (AM A16). Versioning scheme (AM OD-11): **CR-009**; the audit log is append-only and distinct from the replaceable current-output store: **CR-013**. `SD MD-009, FR-017, NFR-003, AC-016` · `US-012` |
| W-19 | **Run status** and **re-run of a failed unit** from the last safe state (US-015) | **Human** triggers the re-run · existing system owns state, replaces the failed unit's own output, repeats nothing finished | High | Medium: a bad re-run could duplicate drafts (AM §7) or lose decisions; both are code responsibilities | Build crew | New scope (DL-02), in the estimate (PRD OQ-5). **"Last safe state" is per unit (review finding 3):** the set of units (documents for W-03, rows for W-05/W-06/W-11) that have a valid output for the current input version, plus every recorded gate decision. A failed unit is marked re-runnable; the specialist re-runs only that unit; the gate stays closed until every unit of the stage is valid. See "Partial failure per unit" below. Retry limit (AM OD-7) and the idempotency key for step outputs (AM OD-11): **CR-010**. `SD NFR-004` · `US-015` · `DL-02` |
| W-20 | **Evaluation report** against the answer key: extraction, verifier flags, verdicts, calendar; run time, model cost, review time from audit timestamps; misses reported, never hidden | Existing system (comparison and report) · reads model outputs as data | High | Medium: the report is the proof (PRD §7); a hidden miss would be the harm | `@qa.eng` | Scoring is deterministic comparison with KEY §1–§4; the altered-quote and `I-1` cases run on copies of rows, not on the mock sources. The fuzzy case (obligation-name closeness, US-001 OQ) is settled in the evaluation design, not here. `SD FR-018, MP-001 to MP-004` · `US-013` · `DL-10, DL-11` |
| W-21 | **Mocked identity** (specialist / GP) attached to every decision and checked on every write | Existing system | n/a | Medium for the demo; **not an access-control claim** (AM §3) | Build crew | Enforced server-side (template rule: identity in code, not in the prompt). Real authentication is out of scope (SD A-5). `SD NFR-010, A-5` · `PRD §3 Identity` |
| W-22 | *(Stretch, F10)* **Impact assessment** of a rule amendment: which rows, verdicts and entries are affected, and why (US-014) | **Collaborative, provisional**: existing system finds the mechanical dependencies (which rows cite the amended paragraphs; which verdicts and entries depend on those rows) · **model** judges whether the change is substantive and how far it reaches (wording-only vs offset change vs new scope paragraph) · code sets flags and status only | High: flags and status only; nothing substantive changes (SD MD-011) | Medium-high: a missed impact is silent (AM S3); over-flagging also counts as failure (US-014 assumption). Every report, including "no impact", needs specialist acceptance or manual review (FR-026) | Specialist (acceptance) · Build crew (dependency logic) | Provisional because the stretch is built only after US-001 to US-013 and US-015 pass, and is estimated separately. `AMD-01` and `AMD-02` need semantic judgement (is "five months" substantive? does a new scope paragraph change applicability?); `AMD-03` needs the model to say "same meaning". Code alone cannot do that; a model alone cannot be trusted to find every dependent entry. The split keeps the enumeration deterministic and the judgement reviewable. `SD MD-011, FR-021, FR-026, AC-018 to AC-020` · `US-014` · `KEY §6` |

**Quote-check normalisation rule (QN-1), for W-04.** Operator-confirmed 2026-11-11. Both the row's
quote and the cited paragraph are normalised the same way, then the quote must occur as a contiguous
substring of the paragraph.

1. Trim whitespace at the start and end.
2. Replace every run of whitespace (spaces, tabs, line breaks) with one space. *Reason:* the mock
   source paragraphs wrap mid-sentence at the end of a line, while a quote is written on one line.
3. Nothing else. Comparison is case-sensitive. Punctuation, typographic quotes and apostrophes, dashes
   and Unicode forms are **not** normalised. A difference in any of them fails the check. Tolerant
   matching for real documents stays deferred (US-002 scope note).
4. A row with no paragraph ID, or an ID that matches no loaded paragraph, fails.

A failed check blocks approval of that row until the row is edited and re-checked (SD MN-006). No
reason unlocks it (AM H3).

**Deterministic tests for W-04** (run without a model, SD NFR-011; `@qa.eng` implements):

| ID | Setup | Expected | Trace |
|---|---|---|---|
| T-W04-1 | The 6 answer-key quotes against their paragraphs | All pass | `US-002 c1`, `KEY §1` |
| T-W04-2 | `OBL-01` quote with "calendar" changed to "business" | Fails; row blocked from approval; G1 cannot approve it even with a reason | `SD AC-004`, `US-002 c2`, `AM T-04` |
| T-W04-3 | A correct quote with its line break replaced by two spaces and a trailing space added | Passes (rule steps 1–2) | `US-002 c8` |
| T-W04-4 | A correct quote with one straight quote mark changed to a typographic one, or one letter's case changed | Fails (rule step 3) | `US-002 c8` |
| T-W04-5 | Row with no paragraph ID; row citing an unknown ID | Both fail | `US-002 c3` |
| T-W04-6 | Verifier agent output claims "quote ok" for a row the code failed | Code result stands; row stays blocked; the disagreement is logged | `SD MN-006`, `AM §7 Enforcement` |

**Partial failure per unit (review finding 3).** Stages A and B are made of per-unit model calls:
one per source document for extraction, one per row for the verifier and for applicability. When a
unit's output fails schema validation or the call fails:

1. Valid outputs from the other units are **kept** and stored against the current input version.
2. The failed unit is marked **re-runnable**; the run status (US-015 c1) shows which units are
   valid, which failed and why, in plain words.
3. **The gate stays closed** until every unit of the stage has a valid output. "Nothing is passed to
   review" (US-001 c7, US-006 c7) means exactly this: G1 or G2 does not open on a partial stage.
4. A re-run replaces only that unit's output (US-015 c6). Finished units and recorded gate decisions
   are untouched.
5. Re-verification after an edit (W-08) is the same mechanism applied to one row: that row's verifier
   output is invalidated and re-run; all other rows keep theirs.

Every re-run, and every re-verification, is a model call and **counts against MC-001 and MC-002**
for that run (review finding 4): cost is the sum of all calls attributable to the run; time is the
wall-clock of agent steps, excluding time waiting for the specialist. The evaluation report (W-20)
reports both.

**Steps with no model, by requirement, not by choice:** W-02, W-03a, W-03b, W-04, W-09, W-13, W-14,
W-16, W-18, W-21. Tests for W-09, W-13 and W-18 run without a model (SD NFR-011).

**Model steps:** W-03 (extraction), W-05 and W-06 (verification judgement), W-11 (applicability) and,
in the stretch, part of W-22. Every one of them produces a draft that code validates against a schema
and a human decides on at a gate. None has a write path to the library, the calendar, the gate state
or the audit log beyond appending its own output as a logged proposal.

**Feasibility verdict**: `feasible with constraints`

**Load-bearing constraint**: **the six-week timebox against the full Must scope** (PRD OQ-5, DL-08).
The Must scope is 14 stories including three recovery paths (SD FR-022 to FR-025), the failed-step
re-run (US-015) and the full gate logic with versioned approvals. The work-ownership split above is
feasible as designed: the model steps are small, bounded and reviewable, and everything consequential
is code. What is not yet shown is that all of it fits six weeks for one operator. `*create-sad` carries
the estimate and proposes the cut line between the core demo path (steps 1–9) and hardening, to be
agreed with the operator before Build.

Two further constraints, named so they are not mistaken for guarantees:

- **Exact-match model targets are measured, not guaranteed.** MP-001 to MP-003 require 6 of 6 rows,
  6 of 6 verdicts and exactly the planted flags from probabilistic steps. The design makes a miss
  visible (W-20, DL-10) and harmless to GPs (W-09, W-15); it cannot make it impossible. The pass/fail
  thresholds are set under `*define-eval-criteria`.
- **Cost and time budgets bound the pattern.** Under US$2 and under 5 minutes per run (SD MC-001,
  MC-002) on 6 documents and 6 rows is comfortable for a fixed sequence of small calls, and would not be
  for an open-ended agent loop. This feeds `*select-pattern`.

### Pattern Decision

- **Primary shape**: `workflow`
- **Workflow sub-shape**: combination: **chaining** between stages, with **parallelization** of the
  per-row model calls inside a stage. The chain is broken by human gates, so the product is three
  short workflows run one after another, not one long-running process:

  | Stage | Steps (Work Ownership IDs) | Model calls | Ends at |
  |---|---|---|---|
  | A. Extract and verify | W-02 → W-03 → W-03a + W-03b (code) → W-04 → W-05 + W-06 (per row, in parallel) | 1 extraction call per source document (6), then 1 verifier call per row (6) | **G1** (W-07), human |
  | B. Judge applicability | W-10 → W-11 (per approved row, in parallel) | 1 call per approved row (up to 6) | **G2** (W-12), human |
  | C. Generate and publish | W-13 → W-14 → G3 | **None** | **G3** (W-15), human; then W-16 |

  Re-verification after an edit (W-08) runs stage A's verifier step on one row. Re-running a failed
  unit (W-19) re-runs only that unit; a stage is complete when every unit has a valid output, and
  only then does its gate open. Each unit's output replaces its own earlier output for the same input
  version, so a re-run adds no duplicates (US-015 c6). The key that makes this true (run ID + step +
  unit ID + input version, AM OD-11) is **CR-010**.

- **Deciding factor**: **predictability.** The path is written in full by the requirements: extract →
  verify → G1 → judge → G2 → dates → G3 (SD FR-001 to FR-014, PRD §2). No step needs a model to decide
  what happens next, and the three hard gates must happen at fixed points (SD MN-003). The template
  says an agent is legal only when the path cannot be enumerated; here it can, so the agent shape is
  ruled out by the first factor and the other four are not needed to decide. They confirm it:

  | Factor | Workflow | Why it also rules out the alternatives |
  |---|---|---|
  | Predictability | Fixed order, fixed gates, fixed outputs per step | Agent: a model choosing the next step could reorder, repeat or skip work around a gate. |
  | Error cost | Each model output is a schema-checked draft that stops at a gate; a wrong draft costs review time, never a wrong calendar | Augmented call: one call that extracts and checks itself has no separate verifier (SD MD-003) and no G1 stop between extraction and judgement. |
  | Observability | Every step's output is a logged artifact with a step name and run ID (US-012 c1); run status is per step (US-015 c1) | Agent: reasoning about "what to do next" is harder to show to a specialist than "step 3 of 4 finished". |
  | Latency | Roughly 18 small calls per run before any re-run, per-row calls in parallel; comfortably under 5 minutes (SD MC-001). Re-runs and re-verifications add to the same budget. *Estimate, measured by US-013* | Agent: open-ended loops have no fixed upper bound. |
  | Cost | Inputs are six short documents and one fund profile; a few thousand tokens per call; comfortably under US$2 (SD MC-002) including the re-runs and re-verifications of a demo run. *Estimate, measured by US-013* | Agent: turn count, not input size, drives cost. |

- **Rejected alternatives and reversal cost**:

  | Alternative | Why rejected | Cost to reverse later |
  |---|---|---|
  | **Agent** (a model orchestrates extraction, verification and judgement as tools) | Path is enumerable; gates are fixed; no requirement needs run-time planning in the MVP. Only the stretch (W-22) has a reach to work out, and it is handled as routing (below), measured first. | **Low to medium.** Each model step is a bounded, schema-validated function with no tools, so an orchestrator could call them unchanged. What would have to be added: a tool allowlist, a turn budget, stop conditions and a human gate before any irreversible call. The gate and date code would not change. |
  | **Augmented call** (one model call with the sources in context, producing rows, flags and verdicts together) | Breaks SD MD-003 (verifier separate from extractor) and puts G1 inside a single call. Also couples extraction errors to applicability errors. | **High.** The gates and the separate verifier would have to be re-inserted; the row schema and audit granularity would change. |
  | **Evaluator-optimizer** (verifier feeds its flags back to the extractor, which revises until the verifier passes) | The loop would let a model change a row in response to a flag. SD MN-004 says the verifier never changes a row, and SD MD-004 says a flag is resolved by the specialist with a reason. **The human closes this loop, by design.** Automating it would remove the one check the capstone exists to keep. | Not applicable: this is a requirement, not a reversible design choice. |
  | **Routing** as the primary shape | Core inputs do not vary in kind: every run processes the same six documents through the same steps. | n/a |

- **Progression used**: prompt → **structured output** (every model step returns a fixed schema that
  code validates; invalid output stops the run, SD NFR-004) → **inputs injected, not retrieved** (the
  whole mock corpus is small, so each call receives the documents it needs in context; no vector
  retrieval, no tools) → evaluator-optimizer **not used** (see above) → fine-tuning **not used** (not
  needed for six documents; not confirmed available; and every swap is a release with an eval gate).

**Agent-only fields** (recorded for completeness; the shape is a workflow, so none applies as an
agent control):

- **Tool allowlist**: **empty.** No model step has a tool. Code reads the mock sources and the fund
  profile and places them in the prompt. This is stronger than an allowlist and satisfies PRD §3
  "agents read only the mock source documents and the mock fund profile" by construction. Code, not
  the model, reads live state (gate status, versions, approvals), which the template forbids a model
  from obtaining through retrieval.
- **Turn budget**: one call per step per unit (document or row), one automatic transport retry,
  and up to 3 manual re-runs per unit per input version; the re-run limit and the idempotency key
  are defined together in **CR-010**, because one is meaningless without the other.
- **Stop conditions**: a stage stops at its gate; a unit stops on schema-invalid output (that unit
  is marked re-runnable, the failure is logged, the gate stays closed, nothing advances).

**Model roles and who owns the sequence.** There are three named model roles: **extractor** (W-03),
**verifier** (W-05, W-06; its quote check W-04 is code), and **applicability judge** (W-11). The
sequence is written in code and each role is a bounded step with a fixed input and output schema, so
by the template's classification this is a workflow, not an agent, however the roles are labelled in
the runtime. No role chooses which role runs next. No orchestrator or subagents are needed: one model
context holds one row plus the six short mock documents with room to spare. **Roles do not share
context**: each call is built by code from stored data (the row, the sources, the fund profile, the
code quote-check result). The verifier never sees the extractor's reasoning (W-05); the judge never
sees the verifier's reasoning, only the row as approved at G1. The AAMAD development
crew is outside this decision (`crew.autonomy` governs the personas, not the product).

**Stretch (W-22), if built.** Impact assessment is the one place the system must work out reach. It
is designed as a **routed workflow**, not an agent: code enumerates which rows cite the amended
paragraphs and which verdicts and entries depend on them (deterministic, complete by construction);
one model call classifies the amendment as *wording only*, *value change* or *scope change* with a
reason; code routes flagged items to G1 (value change) or G2 (scope change) and marks entries out of
date; every report, including "no impact", goes to the specialist (SD FR-026). Promotion to an agent
would need the routed version measured first against `AMD-01` to `AMD-03` (KEY §6) and an operator
decision.

### Reference Architecture

| Shape | Use when | Known failure to prevent |
|-------|----------|--------------------------|
| Agent | Path cannot be written in advance | Unbounded tools |
| Retrieval | Stable documents, not live state | Retrieval used as a substitute for live state |
| **Document pipeline** | Structured extraction with an exception path | No exception path |
| **Routing** | Inputs vary in kind | No human escalation, or an agent shipped before the routed workflow was measured |
| Coding agent | Agentic exploration, then deterministic edit/test/review | Edits without review or an eval |

- **Selected reference architecture**: **Document pipeline.** Fixed-schema extraction from known
  documents, checked, then judged, with a human at each hand-off. Stages A and B are the pipeline;
  stage C is ordinary application code downstream of it.
- **Known failure this design prevents**: **no exception path.** Every way a model step can be wrong
  has a named route that does not advance work:

  | Exception | Route | Trace |
  |---|---|---|
  | Output does not match the schema (missing field, verdict outside the allowed set, unknown fact ID) | That unit is marked re-runnable; valid units are kept; failure logged; gate stays closed until every unit is valid; specialist re-runs the unit | SD NFR-004 · US-001 c7, US-006 c7, US-015 · W-19 |
  | Two rows for one obligation (across documents, or primary vs summary source) | Grouped as "possible duplicates" at G1 by code; specialist rejects or edits with a reason; no model merges | W-03a |
  | A paragraph with an obligation has no row | Visible in the G1 coverage view; the specialist adds the row by hand (W-07a, CR-020) and it takes the normal path; always reported by the evaluation, with human-created rows counted separately | W-03b · W-07a · CR-020 · W-20 · DL-10, DL-15 |
  | Quote not found in the cited paragraph | Row blocked from approval; fix is an edit and re-check; no override | SD MN-006 · W-04, QN-1 |
  | Flag (internal or cross-source) | Approval requires a written reason, logged | SD AC-006 · W-07 |
  | Verdict "unsure" | G2 cannot complete until the specialist decides it; the safe default is "applies (precautionary)" (P-1) | SD AC-008 · W-12 |
  | Extraction misses a row | Not visible at run time; caught by the evaluation report and reported, never hidden | SD MP-001 · W-20 · DL-10 |
  | Verifier false alarm | Approve with a reason; counted by the evaluation report | SD MP-003 · AM §6 |

- **Second pattern**: **Routing**, for the stretch only (W-22). The core pipeline and the stretch fail
  differently: the pipeline fails by producing a wrong structured draft, which a gate catches; impact
  assessment fails by misjudging *reach* (over- or under-flagging), which no gate on the flagged item
  can catch because the miss is a missing flag. The routing failure to prevent is therefore built in
  twice: a human escalation on every report (SD FR-026, including "no impact"), and the rule that the
  routed workflow is measured against `AMD-01` to `AMD-03` before any agent is considered.
- **Retrieval**: not used, and never for live state. Documents are injected whole by code. Gate
  status, approval versions and published state are read only by code.

### Model and Context Strategy

- **Default model tier**: **balanced default**, one model for all three roles (extractor, verifier,
  judge). No measured need for a stronger tier exists; six short documents and six rows are a small
  task. The model name is configuration (`LLM_MODEL`), never hard-coded, so a tier change is a
  release under the swap rule below. Sampling is set for reproducibility (temperature 0 or the
  provider's deterministic setting, fixed `max_tokens` per step); model, temperature, `max_tokens` and
  prompt version are logged per call (aamad-core tooling rule).
- **Context strategy**: **progressive, built by code per call.** Each call receives only the stored
  data its step needs; nothing is carried over from a previous call.

  | Step | In the context window (minimum) | Deliberately **not** in it |
  |---|---|---|
  | W-03 extractor | One source document's paragraphs with their IDs; the row schema; the instruction to quote verbatim, cite one ID, give no dates, and leave the business-day rule unset when the source is silent | The other documents (SA-7); the answer key; any previous run's rows |
  | W-05/W-06 verifier | The row's fields and quote; the code quote-check result (W-04); the cited paragraph; all source paragraphs with IDs (6 documents); the flag schema | The extractor's reasoning or prompt (W-05); other rows' flags; gate state |
  | W-11 judge | The row as approved at G1 (fields, quote, business-day rule); the fund profile facts with IDs and the event log; the verdict schema; the P-1 instruction to answer "unsure" rather than guess when a fact is missing | Verifier reasoning and flags; G1 reasons; the specialist's identity; the answer key; other rows' verdicts |
  | W-22 *(stretch)* classifier | The old and new paragraph text; the rows that cite it (from code); the class schema | The calendar; the GP view; any approval record |

  The **answer key is never in any prompt or test fixture used at run time**; it is read only by the
  evaluation runner (W-20). Few-shot examples, if used, are written fresh and are not drawn from the
  answer key (fairness/leakage control CR-016).
- **Swap-as-release rule**: every change to a model, a prompt, a schema or a sampling setting is a
  **release**. Before it is adopted: the evaluation report (US-013) on the demo set must still match
  the answer key exactly on MP-001 to MP-004 and stay within MC-001 and MC-002. **Rollback
  criterion, written before the swap**: any regression on those exact-match checks, or a budget
  breach, reverts to the previous prompt/model version. Prompt versions are content-hashed and
  recorded in every trace record (CR-018), so the version behind any row or verdict can always be
  named.
- **Entry point**: **direct API.** The model provider is called from inside the three step functions,
  which run inside the per-stage Flows that the backend triggers (§2). There is no hosted chat, no
  agent SDK session, no MCP or tool server. CrewAI (`AAMAD_TARGET_RUNTIME`) is the library that runs
  the stage and makes that call; it is not a separate route and not the entry point itself.
- **Entry-point tradeoff named at decision time**: direct API gives the application full ownership of
  every call: the exact prompt, the parameters, the cost, the trace, and the schema check on the way
  back. In exchange the application must build what a hosted route would provide: retries, cost
  counting, prompt versioning and tracing (Production Shape and CR-017/CR-018). For a system whose
  whole claim is auditability, that is the right side of the trade.
- **Entry-point responsibility map**: one route only. The evaluation runner (W-20) calls the same
  step functions as the application, so evaluation measures the production path, not a copy of it.
- **Minimum data in the context window**: as the table above. No identities, no audit-log content,
  no gate state, no approval reasons, no other rows' outputs, no real data (there is none).
- **Identity**: enforced in server-side code. The mocked identity (specialist / GP) comes from the
  session, is checked on every write endpoint (CR-004) and is written to the audit log by the server.
  The model never receives it and could not act on it if it did (no tools).

### Control Register

What training already reduces (fluent text, following a schema most of the time, refusing obvious
harm) is not relied on for anything consequential. Everything below is enforced by the application.
Three control points: **input** (what goes into a model call), **output** (what comes back before it
is stored or shown), **tool-call** (any action with a side effect; here, every state change, since
models have no tools). Side effects fail closed. Review routing follows confidence, reversibility and
error cost, not volume, and the reviewer always receives the inputs and the reason for the flag.

| ID | Risk category | Control | Control point | Failure direction | Owner | Evidence artifact | Review routing |
|---|---|---|---|---|---|---|---|
| CR-001 | Gate bypass (SD MN-003, MP-006) | State transitions (G1 complete → stage B may run; G2 complete → stage C; G3 → publish) are a backend state machine. The transition function refuses any advance without the matching recorded decisions, regardless of caller. The UI cannot advance state; it only submits decisions. **The backend is the single owner of gate state; Flows never decide or remember gate status.** A stage Flow (§2) is started only by the backend, carries no gate state of its own, and cannot start the next stage; it ends by returning outputs that the backend stores and validates. | tool-call | fail closed: on any doubt or error, no transition | Build crew · verified by `@security.eng` | Gate tests T-02, T-03 (AM §7); audit entries for refused attempts; a test that invoking a stage Flow directly (not via the backend) cannot change any gate state | Refused attempts are logged and shown to the specialist as a plain message; none is silent |
| CR-002 | Agent side effects (PRD §3, AM A13, A14) | **No model step has a tool.** Inputs are injected by code; outputs are returned values that code validates and stores as proposals. There is no code path from a model output to approve, publish, write a date or advance state. | tool-call | fail closed by construction (the capability does not exist) | Build crew | Test T-07 (inspect each step: no tool, no write access); §2 interfaces | n/a |
| CR-003 | Invalid or malformed model output (SD NFR-004) | Every model output is parsed against its schema before storage: row fields present and typed; exactly one paragraph ID that exists; no date fields; verdict in {applies, does not apply, unsure}; every cited fact ID exists in the profile; flag type in the allowed set. Invalid → that unit marked re-runnable, stored nowhere except the trace, gate closed. | output | fail closed | Build crew | Test T-11; schema files; trace records of rejected outputs | Specialist sees the failed unit and the reason in run status (US-015), re-runs it |
| CR-004 | Unauthorised actor (SD NFR-010) | Every write endpoint checks the mocked role server-side: approve, edit, reject, reopen, override, decide, publish, decline, create row (W-07a) and, in the stretch, accept/refer/complete require `specialist`. GP endpoints are read-only and return published data only. Hiding a button is not a control. | tool-call | fail closed | Build crew · `@security.eng` | Test T-06; endpoint list with role requirement | Refusals logged |
| CR-005 | Unsourced row (SD MN-006) | Quote check W-04 under QN-1 in code. A row with no paragraph ID, an unknown ID or a quote not found cannot be approved; no reason unlocks it; a verifier "pass" cannot override a code "fail" (T-W04-6). Applies equally to model-extracted, edited and human-created rows. | output (on model rows) · tool-call (on save of edits and human rows) | fail closed | Build crew | Tests T-W04-1 to T-W04-6, T-04 | Blocked row shown at G1 with the mismatched text (US-002 c7); fix is edit and re-check |
| CR-006 | Verifier changes a row (SD MN-004) | The verifier interface returns flags only; it has no write access to row fields. Code compares the row before and after verification in tests. | output | fail closed (any field difference fails the test and the build) | Build crew | Test T-08 | n/a |
| CR-007 | Approval over an unresolved flag or an undecided item (SD AC-006, AC-008) | Remaining flag → approval requires a non-empty written reason, stored with the row version. Any "unsure" verdict → G2 cannot complete. Any undecided row or verdict → gate incomplete. No bulk action, no preselected decision, no decision on timeout or close (AC-026). | tool-call | fail closed | Build crew | Tests T-05, T-03, T-23 | Flagged rows and unsure verdicts are visibly distinct; routed to the specialist with both texts (flags) or the cited facts (verdicts) |
| CR-008 | Model-computed date (SD MN-005) | The date module has no model client dependency; the row and verdict schemas have no date fields (CR-003 rejects any). Calendar generation runs only after G2 is complete and only on approved, applicable rows. | tool-call | fail closed | Build crew · `@qa.eng` | Tests US-008 c8, US-009 c6 run with no model; T-12 (no partial calendar) | n/a |
| CR-009 | Stale approval and stale screen (SD MD-009, AM §7 freshness) | Every row, verdict and calendar carries an integer **version** that increments on every change (edit, reopen, regeneration, new agent output). Every decision stores the entity ID and version it was made on. An approval is valid only while the entity's current version equals the approved version; otherwise the item is pending and dependent entries are out of date (W-14). Publishing is refused while any entry is out of date. **Every decision request carries the entity version the specialist saw on screen; the server refuses the request if the entity's current version no longer matches.** This covers a decision made on a stale screen and a double submit (the second request carries a version that the first already advanced). | tool-call | fail closed | Build crew | Tests T-09, T-10, T-15; a test that submits a decision with an old version → refused, and the same decision twice → one recorded | The invalidation is shown on the review surface with what changed (AM H5); a refused request tells the specialist the item changed and shows the current version |
| CR-010 | Duplicate or orphaned step output on re-run (AM OD-7, OD-11; US-015 c6) | **Two stores, one key.** The **idempotency key** for a step output is `run_id · step · unit_id · input_version`, where `input_version` is the version (CR-009) of the exact inputs the step received (document version; row version plus sources version; row version plus fund-profile version). (1) The **current-output store** holds at most one output per key: a re-run **replaces** it, so the pipeline never sees two outputs for one unit. (2) The **trace store** (CR-018) is append-only and is keyed by the same key **plus an attempt number** (`· attempt_n`), so every attempt, including the ones that were replaced, is kept. A unit may be **re-run by the specialist up to 3 times per input version** (`UNIT_RERUN_LIMIT`); after that it is marked "needs attention" and the options are a new run or, for extraction, W-07a. No automatic re-run at step level (US-015 deferred); one automatic transport retry per call (Production Shape), which also increments the attempt number. | tool-call | fail closed (a replace outside a re-run, or a trace write that fails, is an error) | Build crew | Tests T-13 (publish twice → one version); re-run tests from US-015 (one current output, *n* trace records); key on every trace record | After the third failed re-run the specialist is told the unit is likely a systematic failure, not a transient one |
| CR-011 | Partial calendar reaches G3 or GPs (SD NFR-004) | Calendar generation is all-or-nothing within one transaction: either every entry for the version is written or none is. G3 offers only a complete version. Publish is one atomic switch of "published version" for the fund. | tool-call | fail closed | Build crew | Test T-12, T-13 | n/a |
| CR-012 | Working content shown to GPs (SD MN-007, FR-025) | The GP read model is built only from the published version; draft, flag, reasoning and audit tables are not joined into it. The review notice is computed from FR-025 triggers against the published version's row and verdict versions (CR-009). | output (what leaves the server to a GP) | **fail safe towards the notice**: if the trigger check cannot be evaluated, the notice is shown; the published entries are never hidden by an error | Build crew | Tests T-21, T-22, US-011 c4, c9, c10 | n/a |
| CR-013 | Audit tampering (SD NFR-003) | The **audit log** and the **trace store** accept inserts only; update and delete are not exposed by the data layer and are refused at the storage boundary. Superseding events (stretch) are new system-actor entries, never edits. The **current-output store** (CR-010) is a working table, not a record: it may be replaced per idempotency key, and every replaced value survives in the trace store with its attempt number. The audit entry for a decision points at the trace record it was made on. | tool-call | fail closed | Build crew · `@security.eng` | Test T-14 (audit and trace); a test that a re-run leaves one current output and two trace records; store configuration showing no update path on audit and trace | n/a |
| CR-014 | Direct prompt injection (operator-supplied text) | The only human-written text that reaches a prompt is a row edited at G1 that is then re-verified (W-08) or created by hand (W-07a). It is placed as **data** in a delimited field with the schema instruction outside it, never concatenated into the instruction. Output still passes CR-003 and CR-005. | input | fail closed (schema failure on the way back) | Build crew | Prompt templates with data/instruction separation; a test that injects instruction-like text into a row field and checks the verifier still returns only flags | Any odd verifier output is just a flag the specialist sees with both texts |
| CR-015 | Indirect injection via sources (mock documents) | Sources are version-controlled mock files loaded by code, not fetched. They are placed in prompts as data with paragraph IDs. Model outputs are stored and rendered as **text**, never executed, never rendered as HTML or markdown with active content. A quote is validated against the source by code (CR-005), so a model cannot "cite" text that is not there. | input · output | fail closed | Build crew · `@security.eng` | Rendering tests (output escaped); source files under version control with no network path | n/a |
| CR-016 | Fairness and leakage injection points | **Corpus**: fixed mock sources, no selection step. **Prompt framing**: the P-1 instruction to prefer "unsure" is a deliberate bias towards over-inclusion, disclosed here, and is why "unsure" routes to a human (CR-007). **Examples**: none drawn from the answer key; the key is never in a run-time prompt or fixture. **Routing**: none in the core; in the stretch, the class decides only which gate reviews the item, never whether a human reviews it (FR-026). | input | fail closed (a prompt that references the answer key fails a repository check) | `@system.arch` (design) · `@qa.eng` (check) | Grep-style test that no prompt template or run-time fixture references `expected-obligation-library` | n/a |
| CR-017 | Token and cost exhaustion (SD MC-001, MC-002) | Per call: fixed `max_tokens` per step and a bounded input (one document, or one row plus six short documents). Per run: a hard cost cap (`RUN_COST_CAP_USD`, **default 4, twice the MC-002 target**) counted from provider usage data across all calls including retries, re-runs and re-verifications; reaching it stops further model calls in the run and records why. **Why the cap is above the target:** the cap is a runaway guard against a broken loop or a re-run storm; stopping at exactly US$2 would turn a small overrun into a failed run with lost work. The target itself is enforced by measurement: **the evaluation report fails any run whose model cost is over US$2** (US-013 c3, c6; DL-10), and a soft warning is shown in run status when a run passes US$2. | input (size) · tool-call (issuing a call) | fail closed (no further calls; valid units kept) | Build crew · `@qa.eng` (report) | Evaluation report fields for cost and time, with pass/fail against US$2 and 5 minutes (US-013 c3, c6); trace records with token counts | Specialist sees the warning and, at the cap, the stop reason, and decides whether to start a new run |
| CR-018 | Reconstructing why an output was produced | Every model call, including each retry and re-run, appends a **trace record** keyed by CR-010's idempotency key **plus the attempt number**, sharing the run ID: prompt version (content hash), model, temperature, `max_tokens`, input hash, raw output, parsed output or validation error, token counts, cost, duration, attempt number, and whether this attempt became the current output. The audit entry for an agent output links to its trace record. Together with the audit log (decisions, versions, reasons) any row, verdict or entry can be explained end to end, including attempts that were replaced (SD MP-005). | output | fail closed (a call whose trace cannot be written is treated as failed) | Build crew | Trace store (append-only, CR-013); trail view (FR-019, P1) or a query that reconstructs one entry | n/a |
| CR-019 | GP text implies permission or gives advice (SD MN-009, DL-01, DL-05) | Code generates the "precautionary" label and note from the specialist's decision (W-12); the model never writes it. The G2 override/"unsure" reason field is labelled GP-visible (W-17, SA-8). The calendar-level "not legal advice / conventions unverified" note is a fixed string on the GP view, not per entry. Voice is checked in a copy review before the demo. | output (human control) | n/a (review) | `@ux.designer` · specialist | Copy review record; US-011 c5, c11 | Human review before the demo |
| CR-020 | Human-created row (DL-15, W-07a) | A row created by hand is stored with `origin: human` and the creator's identity; the flag is immutable and appears in the audit entry and the trace. It cannot bypass CR-005 (quote check not skippable) or CR-006/W-05/W-06 (verifier runs on it). It needs its own G1 decision (CR-007). The evaluation report counts human-created rows in a separate line, excluded from the extractor's row count. | tool-call | fail closed (cannot be saved as approvable without a paragraph ID and a passing quote check) | Build crew · `@qa.eng` | Test: create a row by hand with a bad quote → blocked; with a good quote → flags, G1 decision, audit entry with `origin: human`; evaluation report shows it separately | Shown at G1 like any row, labelled "added by specialist" |
| CR-021 | Secrets and real data (SD NFR-009, MN-001) | Provider key from `LLM_API_KEY` in the git-ignored `.env`; `.env.example` lists names only. Real-name scan runs before every commit. No real data exists in the system to leak. | input | fail closed (missing key → no calls; scan hit → no commit) | Operator · `@security.eng` | Scan output; `.env.example` | n/a |
| CR-022 | Duplicate rows approved (W-03a; *operator decision 2026-11-11*) | Deterministic grouping shown at G1 as "possible duplicates", with a **plain warning on each group**. Non-blocking per row (SA-9): each row keeps its own explicit decision. **At G1 completion, if any group has two or more approved rows, the server requires one confirmation with a written reason before G1 completes**, logged in the audit trail with the group's row IDs and versions. Groups are logged when computed. | output (display) · tool-call (G1 completion) | fail closed: if grouping cannot be computed, G1 does not open; G1 completion with an unconfirmed multi-approved group is refused | Build crew | Test T-W03a-1: two rows citing one paragraph → one group with a warning, shown and logged. **Test T-W03a-2**: approve both rows in a group, complete G1 without a reason → refused; with a reason → G1 completes and the audit log has the confirmation with reason, row IDs and versions. | Specialist sees the group with every row's quote and source; at completion, a single confirmation card naming the rows |
| CR-023 | Concurrent runs (PRD A-6) | The server refuses to start a run for a fund while one is active (any stage not ended at its gate, or a gate not yet completed). One run at a time is a code rule, not a convention; it also keeps versions (CR-009) and idempotency keys (CR-010) unambiguous. | tool-call | fail closed | Build crew | Test: start a run, start another → refused with the active run's ID | Specialist is shown the active run |

**Stretch controls (only if F10 is built):** CR-024 impact report requires acceptance or manual review
for every report, including "no impact" (SD FR-026, fail closed: unreviewed amendments stay in the
queue); CR-025 the classifier (W-22) may set status and flags only, never a field value (as CR-006);
CR-026 report and amendment versions on every decision (as CR-009). Recorded here so the estimate can
include them; detailed when the stretch is scheduled.

### Production Shape

- **Expected volume**: one run at a time (PRD A-6); during the capstone, a few runs per week plus
  re-verifications during review; for the demo, one full run plus the evaluation run. At roughly 18
  calls per clean run, each with a few thousand input tokens, the whole programme's model usage is
  small and MC-002 is a per-run ceiling, not a scaling concern. Latency per stage is bounded by the
  slowest per-unit call, since units run in parallel; stage C has no model and is sub-second. These
  are estimates (SA-6), measured by US-013.
- **Retries with backoff**: one automatic retry per call on transport or provider errors (timeout,
  rate limit, 5xx) with exponential backoff; **none** on a schema-invalid response, because a second
  identical prompt is not a fix and the specialist should see the failure. Beyond that, re-runs are
  manual and capped at 3 per unit per input version (CR-010).
- **Fallback chain**: **none in the MVP, by rule.** Falling back to a different model mid-run would
  be a model swap without its eval gate (Model and Context Strategy). A provider outage stops the
  run at the last safe state; valid units are kept.
- **Circuit breaker**: unit calls within a stage run in parallel, so "consecutive" has no meaning.
  The breaker counts **failed calls within a stage**: once 3 calls in the same stage have failed on
  transport or provider errors (after their automatic retry), the stage stops issuing new calls,
  in-flight calls are allowed to finish and their valid outputs are kept, and run status shows one
  message ("the model service is not responding; nothing moved forward") instead of one per unit.
  The run-level cost cap (CR-017) is the second breaker.
- **Week-1 measurement spike** (Build, before the estimate is final): run each role's call (extractor
  on one document, verifier on one row, judge on one row) on the demo inputs at least 5 times each and
  record tokens in and out, cost and latency per role, plus one full clean run end to end. The
  measured figures replace the estimates in SA-6, feed the six-week estimate and cut line (SOQ-1), and
  give `*define-eval-criteria` real numbers for the cost and latency thresholds. Output: a short
  table in `project-context/2.build/` (file named by `@project.mgr`), referenced from this SAD's
  Audit when it exists.
- **Failure mode specific to a document pipeline, and its mitigation**: **schema-valid but wrong, and
  silent omission.** A pipeline's outputs look right because they are well-formed; the dangerous
  cases are a plausible wrong field and a row that is simply absent. Mitigations: the verifier's
  internal check for plausible-but-wrong fields (W-05), the duplicate grouping (W-03a), the coverage
  view for absences (W-03b), the evaluation report that reports every miss (W-20, DL-10), and the
  gates that keep all of it away from GPs.
- **Per-request traces vs aggregate dashboards**: designed separately. **Per request**: the trace
  record per model call (CR-018) sharing the run ID, plus the audit log; together they reconstruct any
  single row, verdict or entry. **Aggregate**: the evaluation report per run (US-013) is the MVP's
  only aggregate view: accuracy against the key, cost, time, review time, human-created row count. No
  live dashboard is built; one would be Future Work.
- **Configuration names** (values never committed; `.env.example` is created in Build setup):
  `LLM_MODEL`, `LLM_API_KEY`, `RUN_COST_CAP_USD` (default 4), `UNIT_RERUN_LIMIT` (default 3),
  `LLM_MAX_TOKENS_EXTRACT`, `LLM_MAX_TOKENS_VERIFY`, `LLM_MAX_TOKENS_JUDGE`.

### 1. MVP Architecture Philosophy & Principles

*Pending: filled by `*create-sad`.*

### 2. Application Runtime Specification

*Mostly pending: filled by `*create-sad`.* One decision is recorded now because the Pattern Decision
depends on it (review finding 7):

**Runtime shape (operator decision, 2026-11-11).** The backend is the single owner of gate state. A
**short CrewAI Flow runs each stage** (A, B, C): it starts only when the backend triggers it, runs
that stage's steps in order (with the per-unit model calls in parallel), and **ends at its gate** by
returning its outputs to the backend. **Flows never decide or remember gate status.** The backend
validates and stores the outputs (CR-003, CR-010), records the gate as open, and waits for the
specialist. The next stage's Flow is started by the backend only after the backend's own state
machine says the gate is complete (W-09, CR-001). Stage C's Flow contains no model call; it exists
so the three stages have one shape and one place to add tracing.

Inside each Flow, every model step sits behind a **runtime-neutral function interface** with a typed
input and a typed output schema:

| Step | Interface (shape, not final names) | Runtime inside |
|---|---|---|
| W-03 | `extract_rows(document) -> list[Row]` | CrewAI agent + task, or a direct model call; the choice is invisible outside the function |
| W-05 + W-06 | `check_conflicts(row, quote_check_result, sources) -> list[Flag]` | same |
| W-11 | `judge_applicability(row, fund_profile) -> Verdict` | same |
| W-22 *(stretch)* | `classify_amendment(amendment, affected_rows) -> AmendmentClass` | same |

*Why a Flow per stage, and why the backend still owns the gates.* A Flow is a good fit for "run these
steps in this order, some in parallel, and hand back the results": it gives the stage one shape, one
trace, and the runtime's own orchestration conventions. It is a poor fit for a human gate, because a
gate is persisted state that must survive a restart and be refused on bypass (CR-001), and a Flow
that also held gate state would be a second state machine that has to agree with the first about
where the run is. So the split is: **Flows own the sequence within a stage; the backend owns
everything between stages.** A Flow has no way to start the next Flow; only the backend can. Each
Flow's state is the run ID and the stage's inputs, nothing more. *Why a neutral interface for the
model steps.* `AAMAD_TARGET_RUNTIME=crewai` constrains Build conventions only (PRD header); the
swap-as-release rule (Model and Context Strategy) is cheap to honour when a model change is confined
to the inside of one function, and SD NFR-011 is met because gate, date and audit tests call the
backend with the Flows stubbed out: no CrewAI object and no model are needed to run them. CrewAI's
agent, task and YAML conventions apply **inside** the Flows and are specified when this section is
completed.

### 3. Frontend Architecture Specification

*Pending: filled by `*create-sad`.* Framework choice answers PRD OQ-8 (Next.js is operator intent, not
a requirement).

### 4. Backend Architecture Specification

*Pending: filled by `*create-sad`.* Includes the version scheme for approval records (AM OD-11) and the
stable entry-ID scheme (US-008 assumption).

### 5. DevOps & Deployment Architecture

*Pending: filled by `*create-sad`.* Local demo; no hosting target (PRD §3 Infrastructure).

### 6. Data Flow & Integration Architecture

*Pending: filled by `*create-sad`.*

### 7. Performance & Scalability Specifications

*Pending: filled by `*create-sad`.*

### 8. Security & Compliance Architecture

*Pending: filled by `*create-sad`.* Names the future client-isolation boundary (SD §10.5, OQ-13)
without validating it.

### 9. Testing & Quality Assurance Specifications

*Pending: filled by `*create-sad`; Evaluation Criteria table by `*define-eval-criteria`.*

### 10. MVP Launch & Feedback Strategy

*Pending: filled by `*create-sad`.*

### Extensibility walkthroughs (SD §10.4)

*Pending: filled by `*create-sad`.* S-1 (fictional Luxembourg RAIF) and S-2 (`FND-DEMO-01`
considering Singapore marketing), separately, architecture-only, no coverage promise.

## Implementation Guidance for AI Development Agents

*Pending: filled by `*create-sad`.*

## Architecture Validation Checklist

- [ ] PRD requirements mapped to architectural components (`*create-sad`)
- [x] Work Ownership complete, with feasibility verdict and load-bearing constraint
- [x] Pattern Decision and Reference Architecture complete
- [x] Model and Context Strategy, Control Register and Production Shape complete
- [x] Runtime roles exist only when the Pattern Decision requires them (three bounded model steps,
      one per role; no default crew; §2 runtime shape recorded)
- [ ] Frontend and backend contracts agree on schemas / streaming (`*create-sad` §3–§4)
- [x] Secrets via env vars only (CR-021; names in Production Shape; `.env.example` in Build setup)
- [ ] MVP vs Future Work boundaries explicit (`*create-sad` §1; the stretch and deferred items are
      already marked throughout)
- [x] Resolved `AAMAD_TARGET_RUNTIME` recorded in Audit

## Sources

- `project-context/1.define/prd.md`: §2 happy path (the step list), §3 feasibility notes and runtime
  constraints, §4 F1–F10, §6 human–system interaction, §7 metrics, OQ-5, OQ-8.
- `project-context/1.define/system-description.md`: §2 P-1, §3 MD/MN/MC/MP buckets, §4 FR-001 to
  FR-026, §5 NFR-001 to NFR-012, §8 AC-001 to AC-026, §9, §10.
- `project-context/1.define/user-stories/README.md` and US-001 to US-015: acceptance criteria and
  demo decisions.
- `project-context/1.define/approval-map.md`: §3 actors and capabilities, §4 approval map, §7
  engineering review (proposals), §8 open decisions OD-7, OD-8, OD-11.
- `project-context/1.define/decision-log.md`: DL-01, DL-02, DL-04, DL-05, DL-08, DL-10 to DL-13.
- `project-context/1.define/mock-data/expected-obligation-library.md`: §1–§6 expected values (cited
  via the stories; not re-read for this step).
- `.cursor/templates/sad-template.md`: headings and the Work Ownership rules.
- `aamad.config.yml` (`project.mode: greenfield`) and `AAMAD_TARGET_RUNTIME=crewai` from the local
  `.env`.

## Assumptions

- **SA-1**: "Existing system" in the template means the deterministic code this project writes. There
  is no legacy application; the project is greenfield.
- **SA-2**: *Resolved 2026-11-11 (operator decision).* The verifier is one separate responsibility
  made of a deterministic quote check in code (W-04, rule QN-1) and a verifier agent doing the conflict
  checks (W-05, W-06). The SD wording was updated to "verifier step" for the quote check (MD-003,
  FR-003, vocabulary) and keeps "verifier agent" for the conflict checks (FR-004).
- **SA-3**: The GP-facing "why" text is the reasoning confirmed at G2, rendered by code. No requirement
  asks for a separate GP-facing rewrite, and adding a model call on the GP path would add an unreviewed
  output. If the UX step finds the G2 reasoning unsuitable for GPs, that is a change to W-17.
- **SA-4**: The stretch split in W-22 is provisional. It is recorded so the estimate under `*create-sad`
  has something to estimate; it is not a commitment to build F10.
- **SA-5**: Mocked identity (SD A-5) is enough for every "who" in the audit log. Roles are checked
  server-side against the mocked identity; no claim is made about real access control.
- **SA-6**: The call counts, latency and cost in the Pattern Decision are estimates from the size of
  the mock data set (six documents, six rows). They are confirmed or corrected by the evaluation
  report (US-013), not assumed.
- **SA-7**: Extraction is one call per source document rather than one call for all six. This keeps
  each call small and lets a failure be re-run per document. If the evaluation shows cross-document
  context is needed to get 6 of 6 rows, this becomes one call with all six documents; the pattern
  does not change. Per-document extraction is also why W-03a exists: two documents can describe one
  obligation, and no single call sees both.
- **SA-8**: At G2, the specialist's override or "unsure" reason is the GP-facing "why" for that entry
  (W-17). One field, labelled as GP-visible, rather than a separate GP text, so there is one piece of
  reasoning to keep consistent. `@ux.designer` designs the field and its prompt; if the UX step finds
  one field is not workable, a second GP-facing field is added and W-17 updated.
- **SA-9**: *Confirmed by operator decision, 2026-11-11.* A "possible duplicates" group (W-03a)
  stays non-blocking per row: each row in the group needs its own explicit decision (SD AC-026) and a
  plain warning is shown on the group. The one hard rule is at G1 completion: a group with two or more
  approved rows needs one confirmation with a written reason, logged (CR-022, test T-W03a-2). This
  keeps a deliberate "two rows for one obligation" possible (for example two authorities) while
  making an accidental one impossible to miss.

## Open Questions

- **SOQ-1** (from PRD OQ-5, DL-08): Does the Must scope fit six weeks? **Not yet shown.** Estimated
  under `*create-sad`, with a proposed cut line for the operator to agree before Build. The week-1
  measurement spike (Production Shape) replaces the cost and latency estimates in that estimate with
  measured figures.
- **SOQ-2**: *Resolved (`*define-controls`, CR-010, Production Shape).* One automatic transport
  retry per call; manual re-run up to 3 times per unit per input version; then "needs attention".
  Closes AM OD-7 and US-015 OQ-US015-1.
- **SOQ-3**: *Resolved (`*define-controls`, CR-009, CR-010).* Integer version per row, verdict and
  calendar; every decision stores entity ID + version; idempotency key `run_id · step · unit_id ·
  input_version`. Closes AM OD-11. The stable calendar entry-ID scheme stays with `*create-sad` §4.
- **SOQ-7**: *Resolved 2026-11-11 (operator decision, DL-15).* Manual row creation is in MVP scope
  in its smallest form: W-07a, CR-020. Still to do by `@product-mgr`: SD requirement (proposed
  FR-027), story (proposed US-016), US-013 criterion for the separate count.
- **SOQ-8** (for `@product-mgr`, not blocking): the Define documents do not yet contain DL-15's
  requirement, the duplicate grouping (W-03a), the coverage view (W-03b) or the per-unit partial
  failure rule. These are architecture-level additions that stay within existing requirements (P-1,
  NFR-004, MD-005), but the stories should reflect them before Build so QA tests them.
- **SOQ-4** (PRD OQ-8, AM OD-12): Frontend framework. Next.js is operator intent; confirmed or
  replaced under `*create-sad` §3.
- **SOQ-5**: *Resolved 2026-11-11 (operator decision).* The quote check is deterministic code and
  the authority that blocks G1; the verifier agent keeps the model-based conflict checks. AM OD-8
  closed with a reference to W-04 and QN-1.
- **SOQ-6** (carried from Define, for the operator): PRD OQ-1 four-eyes timing, OQ-6 pre-publication
  GP note (before the UX step), OQ-7 business-day rules for `OBL-04` and `OBL-05`, OQ-10 programme
  submission requirements, OQ-11 reused prototype front end, OQ-12 manual-effort estimate. None blocks
  the next SAD steps; OQ-10 and OQ-11 affect the estimate in SOQ-1.

## Audit

- 2026-11-11 · persona `system-arch` · action `decompose-work` · `AAMAD_TARGET_RUNTIME=crewai`
  (resolved from `.env`; config `runtime.target` unset) · created `sad.md` with the template headings;
  filled Work Ownership (W-01 to W-22), feasibility verdict `feasible with constraints`, load-bearing
  constraint (six-week timebox vs Must scope); decided AM OD-8 as code (quote check), subject to SOQ-5;
  all other decision headings left pending. Prompt Trace not captured: no model call was made by the
  application; this artifact is authored by the persona from Define inputs only.
- 2026-11-11 · persona `system-arch` · action `decompose-work` (update) · `AAMAD_TARGET_RUNTIME=crewai`
  · operator confirmed SOQ-5: quote check is code and blocks G1; verifier agent keeps conflict checks.
  Added normalisation rule QN-1 and tests T-W04-1 to T-W04-6; SA-2 and SOQ-5 resolved. The operator
  closed AM OD-8 and updated SD wording (MD-003, FR-003) directly; at the operator's instruction this
  persona added the SD vocabulary reference to QN-1, US-002 criterion 8 and the audit lines in those
  files.
- 2026-11-11 · persona `system-arch` · action `select-pattern` · `AAMAD_TARGET_RUNTIME=crewai` ·
  primary shape `workflow` (chaining between three gated stages, parallel per-row calls within a
  stage); deciding factor predictability; agent, augmented call and evaluator-optimizer rejected with
  reversal costs; reference architecture Document pipeline with Routing as the second pattern for the
  stretch only; empty tool allowlist; added SA-6, SA-7. Prompt Trace not captured: no model call made.
- 2026-11-11 · persona `system-arch` · action `select-pattern` (update, operator review findings 1–7)
  · `AAMAD_TARGET_RUNTIME=crewai` · added W-03a (deterministic duplicate grouping) and W-03b (G1
  coverage view); partial failure per unit, W-19 last safe state per unit; re-runs and
  re-verifications count against MC-001/MC-002; AM OD-11 moved to `*define-controls` with the
  idempotency key (SOQ-3); W-17 GP-text rule by decision type (SA-8); verifier inputs exclude the
  extractor's reasoning (W-05, W-06); §2 provisional: plain function calls, runtime-neutral step
  interfaces, no CrewAI Flow; new SOQ-7 (manual row creation, operator decision); SA-9.
- 2026-11-11 · persona `system-arch` · action `define-controls` · `AAMAD_TARGET_RUNTIME=crewai` ·
  SOQ-7 resolved by operator (DL-15): added W-07a and CR-020. Filled Model and Context Strategy
  (balanced tier, progressive context table, swap-as-release with rollback criterion, direct API entry
  point and its tradeoff, server-side identity), Control Register CR-001 to CR-022 plus stretch
  CR-023 to CR-025, Production Shape (retry, no fallback by rule, circuit breaker, pipeline failure
  mode, traces vs aggregate, config names). Resolved SOQ-2 (AM OD-7: 3 manual re-runs per unit) and
  SOQ-3 (AM OD-11: integer versions, idempotency key). New SOQ-8 for `@product-mgr`. Prompt Trace not
  captured: no model call made.
- 2026-11-11 · persona `system-arch` · action `define-controls` (update, operator review fixes 1–7 and
  two operator decisions) · `AAMAD_TARGET_RUNTIME=crewai` · CR-010/CR-013/CR-018: current-output
  store (replaced per key) separated from the append-only trace store (key + attempt number);
  CR-017: cap default 4 with reason, evaluation report fails runs over US$2; stale references to
  SOQ-7 and `*define-controls` repointed to W-03b, W-07a, CR-009, CR-010, CR-020; CR-009: decision
  requests carry the seen version, mismatch refused (covers double submits); new CR-023 single active
  run (PRD A-6), stretch controls renumbered CR-024 to CR-026; circuit breaker redefined as 3 failed
  calls within a stage; week-1 measurement spike added (feeds SOQ-1); checklist updated. Operator
  decisions: §2 runtime shape (a CrewAI Flow per stage, backend single owner of gate state; W-09 and
  CR-001 aligned); duplicates stay non-blocking with a warning per group and one confirmation with
  reason at G1 completion for multi-approved groups (SA-9, CR-022, tests T-W03a-1/2).
