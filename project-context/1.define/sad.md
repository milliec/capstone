# System Architecture Document (SAD)

**Product**: Regulatory Intelligence for fund compliance calendars
**Scope**: MVP only (six-week capstone). One fictional Luxembourg UCI Part II fund (`FND-DEMO-01`),
mock data, mocked roles.
**Status**: **In progress.** The five decision headings are filled: Work Ownership, Pattern Decision,
Reference Architecture, Model and Context Strategy, Control Register (plus Production Shape).
`*create-sad` pass (a) filled sections 1–4 and pass (b) sections 5–8, 10 and the extensibility
walkthroughs, and pass (c) section 9, the requirement map, the six-week estimate and the
implementation guidance. **Scope agreed (DL-22): the MVP is the thin slice.** Items marked *future
scope* in "Six-week estimate and agreed scope" are designed in this SAD but not built. Section 9's criteria table is
`*define-eval-criteria`. A heading marked *pending* has not been decided and must not be
read as a decision.

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
**Selected Runtime**: `crewai` (resolved from `AAMAD_TARGET_RUNTIME`; matches `runtime.target` in
`aamad.config.yml`, which was unset when this SAD was started and now reads `crewai`)

## System Architecture Specification

### Work Ownership

Each user-visible step is assigned one owner. **Model** means a language-model call. **Existing
system** means deterministic application code (there is no legacy system; the "existing system" here
is the code this project writes, which owns rules and records). **Human** means the compliance
specialist, acting through the review surface. **Collaborative** means draft-and-decide: a model or
code drafts, a human decides, and the decision is the record.

> **Thin-slice scope key (DL-22).** Rows W-03a, W-07a and W-08, the re-run part of W-19, and the
> stretch row W-22 are **future scope**: designed here, not built in the MVP. W-03b's fix for a
> real miss is a new run in the MVP. See "Six-week estimate and agreed scope".

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
| W-03b | **Coverage view at G1**: list every loaded source paragraph that no non-rejected row cites (step 2, after extraction; *review finding 2*) | **Existing system** | High: a view only | High: a **missed row is the costlier error under P-1** and is otherwise invisible until the evaluation report (W-20) | Specialist (scans the list at G1) · Build crew | Pure set difference: loaded paragraph IDs minus the IDs cited by **non-rejected** rows (pending or approved, human-created rows included), shown with each paragraph's text. A paragraph whose only row is rejected appears in the list again, and leaves it if that row is reopened (SD FR-023). The answer key is **not** used at run time; the view makes no claim about which uncited paragraphs contain obligations, it only makes the gap visible. In the demo set, **seven** uncited paragraphs are expected and correct: 13 loaded minus the 6 cited (`US-001 c4`, SD AC-029). Three of the seven are the `SRC-PRACT` secondary summaries, which the verifier compares against but which are never a row's source, so they will always be listed. A real miss is fixed by the specialist adding the row by hand (**W-07a**, DL-15, CR-020). `SD FR-028, AC-029, P-1, MP-001` · `US-001 c4, c8–c9` · `DL-10, DL-15` |
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
| W-13 | **Generate the calendar**: anchors, offsets, conventions `D-1` to `D-7`, business-day rolls against the mock holiday list, event-triggered entries from the awareness date, stable entry IDs (step 7) | **Existing system** | High: a draft calendar, regenerated at will, invisible before G3 | High for correctness (one wrong date breaks trust, PRD AB-5), but the owner choice removes the probabilistic risk | Build crew · `@qa.eng` (22-entry exact-match test) | A hard requirement, not a choice: no model may compute a date (SD MN-005), and two runs must be identical (SD NFR-001). **Business-day rules are never inferred by code (operator decision, PRD OQ-7, DL-19):** a row's rule is either stated in its source (extracted) or set by the specialist at G1; otherwise it stays "not confirmed" and `D-6` applies (keep the earlier date, mark it). The date code has no default, lookup or heuristic that turns "not confirmed" into a roll rule. For the demo this keeps `OBL-04` and `OBL-05` as "not confirmed", matching KEY §5. **A stated convention whose application is open is marked, never silently resolved (operator decision, DL-20):** the AED subscription tax (`OBL-02`) follows the stated "tax does not roll" convention (`D-5`) only if that convention covers it, which is open (PRD OQ-7, KEY OQ-D3). The code applies whatever rule the specialist set at G1 and has no built-in default for `OBL-02`; every entry whose rule depends on an open question carries a specialist-visible mark naming that question (CR-027). In 2027 none of `OBL-02`'s four dates falls on a non-business day, so either answer gives the same dates; the mark makes the dependency visible, it does not move a date. Runs only after G2 is complete, on approved inputs only (AM A11). All-or-nothing: a partial calendar never exists as a publishable object (SD NFR-004). `SD MD-006, MD-007, FR-011 to FR-013, FR-016` · `US-008, US-009` · `KEY §4–§5` |
| W-14 | Mark dependent verdicts and calendar entries **out of date** after an edit, reopen or (stretch) impact flag | Existing system | n/a (status only; cleared by regeneration) | Medium: status blocks publishing; it adds no content | Build crew | Mechanical consequence of W-08, W-12 and W-15. Must never depend on a human or model remembering to do it. `SD FR-007, FR-024` · `AM A12, S2` |
| W-15 | **Publish or decline** the whole fund calendar (G3) (step 8) | **Human** decides · existing system executes atomically | **Low**: no unpublish or withdraw exists (SD §9, deliberately deferred). Recovery is review notice → correct → republish | **Highest**: this is the only step that reaches GPs | Specialist | One explicit decision for the whole calendar version, never preselected or triggered by timeout (US-010 c10). Code refuses publishing while G1 or G2 is incomplete or any entry is out of date; safe-default marks do not block (P-1). Decline requires a reason and a chosen next step, cancels no earlier approval. The specialist sees the "date conventions unverified" note at G3 (DL-12). `SD MD-004, FR-014, FR-022, MP-006, A-6` · `US-010` |
| W-16 | **GP read-only calendar**: what, when, who, why per entry; one calendar-level "not legal advice / conventions unverified" note; **before the first G3 publication, a read-only empty state with a fixed message (DL-27, in the thin slice)**; neutral review notice when a change questions the published version (step 9; *future scope*, DL-22) | **Existing system** (rendering published data only) | n/a (read-only) | High: GPs rely on it; must show only published content | Build crew · `@ux.designer` (wording) | Read-only is enforced on the server, not by hiding buttons (AM G2r). The view reads only the published version; draft, flag and reasoning data are not sent to it (SD MN-007, FR-025). `SD FR-015, FR-020, FR-025, NFR-010` · `US-011` |
| W-17 | **GP-facing "why" text** for each entry (plain-English reason + citation + quote) (step 9) | **Collaborative**: model drafts the reasoning at W-11 · specialist confirms, overrides or decides at G2 · code renders the result with the citation and quote | Medium: reopening the verdict (FR-024) replaces it | High: a GP reads it as the explanation; it must not imply permission (DL-01) | Specialist (content, via G2) · `@ux.designer` (voice check and field design, DL-05) | **Rule (review finding 5): the GP sees the reasoning of whoever made the final decision.** (a) *Confirm* → the model's reasoning, exactly as confirmed. (b) *Override* → the specialist's written reason replaces the model's reasoning; the model's text stays in the audit log only. (c) *Decide "unsure"* → the specialist's written reason, plus the code-generated "precautionary" label and its note when the decision is "applies (precautionary)". For a "does not apply" decision there is no entry and so no GP text. **Therefore a G2 override or "unsure" reason must be GP-readable**: plain British English for a non-lawyer, no implied permission (SD NFR-005, DL-01, DL-05). The G2 form says so next to the field (SA-8; wording by `@ux.designer`). G1 reasons are specialist-only and are not shown to GPs. No model runs on the GP path. `SD MD-008, NFR-005, P-1` · `US-007 c3, c5–c6`, `US-011 c2–c5` · `DL-01, DL-05` |
| W-18 | **Audit log**: append every agent output, every human decision (with who, when, what, reason, version decided on) and every gate opening; refuse update and delete | Existing system | n/a (add-only by design) | High: this is the evidence for MP-008 and the review-time measurement (MC-003) | Build crew · `@security.eng` (verifies add-only) | Mandatory bookkeeping with no decision in it (AM A16). Versioning scheme (AM OD-11): **CR-009**; the audit log is append-only and distinct from the replaceable current-output store: **CR-013**. `SD MD-009, FR-017, NFR-003, AC-016` · `US-012` |
| W-19 | **Run status** and **re-run of a failed unit** from the last safe state (US-015) | **Human** triggers the re-run · existing system owns state, replaces the failed unit's own output, repeats nothing finished | High | Medium: a bad re-run could duplicate drafts (AM §7) or lose decisions; both are code responsibilities | Build crew | New scope (DL-02), in the estimate (PRD OQ-5). **"Last safe state" is per unit (review finding 3):** the set of units (documents for W-03, rows for W-05/W-06/W-11) that have a valid output for the current input version, plus every recorded gate decision. A failed unit is marked re-runnable; the specialist re-runs only that unit; the gate stays closed until every unit of the stage is valid. **One exception (SOQ-9, DL-18):** an extraction unit that has reached the re-run limit can be released to manual entry with a written reason; it then no longer holds G1 closed, but every other unit must still be valid. See "Partial failure per unit" below and CR-010. Retry limit (AM OD-7) and the idempotency key for step outputs (AM OD-11): **CR-010**. `SD NFR-004` · `US-015` · `DL-02` |
| W-19a | **Abandon a run**: the specialist closes an `ACTIVE` run with a written reason, without undoing anything (OQ-US015-4, DL-22) | **Human** decides · existing system closes the run, records it and refuses further decisions on it | High: nothing is undone or deleted, and a new run can start | Low to medium: abandoning the wrong run wastes review work in progress, but no published calendar, decision or audit entry changes | Build crew | **Not a general cancel feature:** it does not cancel a model call or a step, undo a decision, roll back a stage or delete a draft; it is the only way out of a run that is stuck or not wanted, because a failed step already ends the run as `FAILED`. A reason is required (`REASON_REQUIRED`); the request carries the run version (CR-009); only an `ACTIVE` run can be abandoned (`RUN_NOT_ACTIVE`). Audited with who, when, reason, the stage and the run version. `SD MN-003, NFR-004, MD-009` · `US-015` · `DL-22` |
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

**Run state model (OQ-US015-4, DL-22).** A run is in exactly one state. Only `ACTIVE` blocks a new run.

| State | Meaning | Ends when |
|---|---|---|
| `ACTIVE` | A stage is running, or a gate is waiting for the specialist | A stage fails (`FAILED`), the specialist abandons it (`ABANDONED`), or G3 is decided (`COMPLETED`) |
| `FAILED` (terminal) | A step failed: a unit returned invalid output, its call failed after the one automatic retry, a task exceeded `max_execution_time`, or the cost cap stopped the run (CR-017). The run status names the step, the unit and the reason | Never; a new run follows |
| `ABANDONED` (terminal) | The specialist closed an active run with a written reason (W-19a) | Never; a new run follows |
| `COMPLETED` (terminal) | G3 was decided (published, or declined with a reason) | Never; see SA-18 |

Rules: (1) A step fails when its stage ends with any failed unit, or a hang reaches
`max_execution_time`; in-flight calls finish and their valid outputs stay in the trace, and **no gate
opens on a failed stage** (the "gate stays closed" rule above). (2) A terminal run is never resumed
and never re-run; the MVP has no unit re-run (DL-22). (3) Entering `FAILED` or `ABANDONED` deletes and
undoes nothing: recorded decisions, row and verdict versions, drafts, the audit log, the traces and any
published calendar stay as they were, and GPs keep seeing the last published version. (4) A decision
request on a run that is not `ACTIVE` is refused (`RUN_NOT_ACTIVE`), and no new model call is started for it. (5) CR-023 reads the state:
`POST /runs` is refused only while a run is `ACTIVE`.

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
is code. What is not yet shown is that all of it fits six weeks for one operator. *Update
(`*create-sad` pass c):* the Must scope is estimated at about **52 focused days** (39–73), of which the
core demo path is about **46** (34–64). The verdict depends on the focused days remaining (SOQ-12); see
"Six-week estimate and proposed cut line". *Update (DL-22):* the operator agreed the **thin slice**, estimated at
about **42.5 focused days** (32–60); with the run state model and abandon action (OQ-US015-4, WP-12a) about **44.5
(33.5–63)**. The verdict stays `feasible with constraints`; the constraint is
now the slice against the operator's capacity, which the operator has committed without a number
(SOQ-12); the week-1 re-estimate checks it.

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

- **Provider and model per role** (operator decision, 2026-11-12, DL-25; resolves SOQ-14). One
  provider: the **OpenAI API**, on prepaid credits. A model is chosen **per role**, each from its own
  configuration value, never hard-coded:

  | Role | Model (family) | Variable | Why |
  |---|---|---|---|
  | Extractor (W-03) | A **cheaper default** model | `LLM_MODEL_EXTRACT` | Fixed-schema extraction from short mock paragraphs; the code quote check and the verifier catch its mistakes |
  | Verifier (W-05, W-06) | **Default: a cheaper mid-tier model, different from both the extractor's and the judge's** (DL-26). **Switch to the judge's reasoning model** only if the mid-tier model misses any planted conflict in the spike | `LLM_MODEL_VERIFY` | Strengthens the separate verifier (SD MD-003): two different models are less likely to share a blind spot. Same provider, so no second live service (SD MN-002, PRD A-3 unchanged) |
  | Applicability judge (W-11) | A **reasoning** model | `LLM_MODEL_JUDGE` | Applicability is the judgement-heavy step, and a wrong "does not apply" is the costliest error (P-1) |

  No other step uses a model: calendar generation is code (MN-005) and the GP text is the reasoning
  confirmed at G2 (W-17). **Exact model IDs are confirmed against the provider's current list before
  the week-1 spike**, recorded in the decision log, and from then on a change to any role's model is
  a release under the swap rule. **Claude Code is the build tool only**: it is not a runtime provider,
  no application call goes to it, and its usage is not part of the application's model spend.
  Sampling is set for reproducibility per role: temperature 0 where the model supports it, fixed
  `max_tokens` per step. **Reasoning models may not accept a temperature setting**; for the judge the
  spike records whether its verdicts are stable across runs, which EC-R1 (3 of 3) then tests. Model,
  sampling settings, `max_tokens` and prompt version are logged per call (aamad-core tooling rule).
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

> **Thin-slice scope key (DL-22).** CR-020 and CR-022, the re-run and release parts of CR-010, the
> review-notice part of CR-012, the circuit breaker (Production Shape) and the stretch controls
> CR-024 to CR-026 are **future scope**. All other controls apply to the MVP.

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
| CR-010 | Duplicate or orphaned step output on re-run (AM OD-7, OD-11; US-015 c6) | **Two stores, one key.** The **idempotency key** for a step output is `run_id · step · unit_id · input_version`, where `input_version` is the version (CR-009) of the exact inputs the step received (document version; row version plus sources version; row version plus fund-profile version). (1) The **current-output store** holds at most one output per key: a re-run **replaces** it, so the pipeline never sees two outputs for one unit. (2) The **trace store** (CR-018) is append-only and is keyed by the same key **plus an attempt number** (`· attempt_n`), so every attempt, including the ones that were replaced, is kept. A unit may be **re-run by the specialist up to 3 times per input version** (`UNIT_RERUN_LIMIT`); after that it is marked "needs attention". The options are a new run or, **for an extraction unit only, a release to manual entry (SOQ-9, DL-18)**: the specialist releases that one document with a written reason; the release is per document, never bulk, and never available for a unit that has not reached the limit. G1 opens only when every *other* unit is valid. The released document's paragraphs then appear in the coverage view (W-03b) and the specialist adds any rows by hand (W-07a, CR-020: labelled manual, source paragraph and quote required, code quote check and verifier conflict checks still run). The release is audited (actor, time, reason, document ID and version) and the evaluation report counts the document as an **extraction failure**. Verifier and judge units have no release (SOQ-10). No automatic re-run at step level (US-015 deferred); one automatic transport retry per call (Production Shape), which also increments the attempt number. | tool-call | fail closed (a replace outside a re-run, or a trace write that fails, is an error) | Build crew | Tests T-13 (publish twice → one version); re-run tests from US-015 (one current output, *n* trace records); key on every trace record. **T-REL-1**: one extraction unit fails 3 re-runs → release without a reason refused; release before the limit refused; release with a reason while another unit is still invalid → G1 stays closed; once all other units are valid → G1 opens, the released document's paragraphs are in the coverage view, the audit log has the release, and the evaluation report counts one extraction failure. **T-REL-2**: a verifier or judge unit at the limit offers no release | After the third failed re-run the specialist is told the unit is likely a systematic failure, not a transient one |
| CR-011 | Partial calendar reaches G3 or GPs (SD NFR-004) | Calendar generation is all-or-nothing within one transaction: either every entry for the version is written or none is. G3 offers only a complete version. Publish is one atomic switch of "published version" for the fund. | tool-call | fail closed | Build crew | Test T-12, T-13 | n/a |
| CR-012 | Working content shown to GPs (SD MN-007, FR-025) | The GP read model is built only from the published version; draft, flag, reasoning and audit tables are not joined into it. **Before the first publication, the GP read model returns a fixed empty state** (DL-27): a constant message defined in code, with no entry count, no run or gate status and no draft content, so it cannot leak working content and a blank screen is never read as "no obligations" (P-1). The review notice is computed from FR-025 triggers against the published version's row and verdict versions (CR-009). | output (what leaves the server to a GP) | **fail safe towards the notice**: if the trigger check cannot be evaluated, the notice is shown; the published entries are never hidden by an error | Build crew | Tests T-21, T-22, US-011 c4, c9, c10 | n/a |
| CR-013 | Audit tampering (SD NFR-003) | The **audit log** and the **trace store** accept inserts only; update and delete are not exposed by the data layer and are refused at the storage boundary. Superseding events (stretch) are new system-actor entries, never edits. The **current-output store** (CR-010) is a working table, not a record: it may be replaced per idempotency key, and every replaced value survives in the trace store with its attempt number. The audit entry for a decision points at the trace record it was made on. | tool-call | fail closed | Build crew · `@security.eng` | Test T-14 (audit and trace); a test that a re-run leaves one current output and two trace records; store configuration showing no update path on audit and trace | n/a |
| CR-014 | Direct prompt injection (operator-supplied text) | The only human-written text that reaches a prompt is a row edited at G1 that is then re-verified (W-08) or created by hand (W-07a). It is placed as **data** in a delimited field with the schema instruction outside it, never concatenated into the instruction. Output still passes CR-003 and CR-005. | input | fail closed (schema failure on the way back) | Build crew | Prompt templates with data/instruction separation; a test that injects instruction-like text into a row field and checks the verifier still returns only flags | Any odd verifier output is just a flag the specialist sees with both texts |
| CR-015 | Indirect injection via sources (mock documents) | Sources are version-controlled mock files loaded by code, not fetched. They are placed in prompts as data with paragraph IDs. Model outputs are stored and rendered as **text**, never executed, never rendered as HTML or markdown with active content. A quote is validated against the source by code (CR-005), so a model cannot "cite" text that is not there. | input · output | fail closed | Build crew · `@security.eng` | Rendering tests (output escaped); source files under version control with no network path | n/a |
| CR-016 | Fairness and leakage injection points | **Corpus**: fixed mock sources, no selection step. **Prompt framing**: the P-1 instruction to prefer "unsure" is a deliberate bias towards over-inclusion, disclosed here, and is why "unsure" routes to a human (CR-007). **Examples**: none drawn from the answer key; the key is never in a run-time prompt or fixture. **Routing**: none in the core; in the stretch, the class decides only which gate reviews the item, never whether a human reviews it (FR-026). | input | fail closed (a prompt that references the answer key fails a repository check) | `@system.arch` (design) · `@qa.eng` (check) | Grep-style test that no prompt template or run-time fixture references `expected-obligation-library` | n/a |
| CR-017 | Token and cost exhaustion (SD MC-001, MC-002) | Per call: fixed `max_tokens` per step and a bounded input (one document, or one row plus six short documents). **Cost rule: US$4 hard stop; any run over US$2 fails EC-012.** Per run, a hard stop (`RUN_COST_CAP_USD`, default 4) is counted from provider usage data across all calls in the run, including retries; reaching it stops further model calls and records why. **Why the cap is above the target:** the cap is a runaway guard against a broken loop or a re-run storm; stopping at exactly US$2 would turn a small overrun into a failed run with lost work. The US$2 target (MC-002) is enforced by measurement: a run whose model cost is over US$2 fails EC-012 in the evaluation report (US-013 c3, c6; DL-10). Run status shows a warning when a run passes US$2. | input (size) · tool-call (issuing a call) | fail closed (no further calls; valid units kept) | Build crew · `@qa.eng` (report) | Evaluation report fields for cost and time, with pass/fail against US$2 and 5 minutes (US-013 c3, c6); trace records with token counts | Specialist sees the warning and, at the cap, the stop reason, and decides whether to start a new run |
| CR-018 | Reconstructing why an output was produced | Every model call, including each retry and re-run, appends a **trace record** keyed by CR-010's idempotency key **plus the attempt number**, sharing the run ID: prompt version (content hash), model, temperature, `max_tokens`, input hash, raw output, parsed output or validation error, token counts, cost, duration, attempt number, and whether this attempt became the current output. The audit entry for an agent output links to its trace record. Together with the audit log (decisions, versions, reasons) any row, verdict or entry can be explained end to end, including attempts that were replaced (SD MP-005). | output | fail closed (a call whose trace cannot be written is treated as failed) | Build crew | Trace store (append-only, CR-013); trail view (FR-019, P1) or a query that reconstructs one entry | n/a |
| CR-019 | GP text implies permission or gives advice (SD MN-009, DL-01, DL-05) | Code generates the "precautionary" label and note from the specialist's decision (W-12); the model never writes it. The G2 override/"unsure" reason field is labelled GP-visible (W-17, SA-8). The calendar-level "not legal advice / conventions unverified" note is a fixed string on the GP view, not per entry. Voice is checked in a copy review before the demo. | output (human control) | n/a (review) | `@ux.designer` · specialist | Copy review record; US-011 c5, c11 | Human review before the demo |
| CR-020 | Human-created row (DL-15, W-07a) | A row created by hand is stored with `origin: human` and the creator's identity; the flag is immutable and appears in the audit entry and the trace. It cannot bypass CR-005 (quote check not skippable) or CR-006/W-05/W-06 (verifier runs on it). It needs its own G1 decision (CR-007). The evaluation report counts human-created rows in a separate line, excluded from the extractor's row count. | tool-call | fail closed (cannot be saved as approvable without a paragraph ID and a passing quote check) | Build crew · `@qa.eng` | Test: create a row by hand with a bad quote → blocked; with a good quote → flags, G1 decision, audit entry with `origin: human`; evaluation report shows it separately | Shown at G1 like any row, labelled "added by specialist" |
| CR-021 | Secrets and real data (SD NFR-009, MN-001) | Provider key from `OPENAI_API_KEY` in the git-ignored `.env`; `.env.example` lists names only. Real-name scan runs before every commit. No real data exists in the system to leak. | input | fail closed (missing key → no calls; scan hit → no commit) | Operator · `@security.eng` | Scan output; `.env.example` | n/a |
| CR-022 | Duplicate rows approved (W-03a; *operator decision 2026-11-11*) | Deterministic grouping shown at G1 as "possible duplicates", with a **plain warning on each group**. Non-blocking per row (SA-9): each row keeps its own explicit decision. **At G1 completion, if any group has two or more approved rows, the server requires one confirmation with a written reason before G1 completes**, logged in the audit trail with the group's row IDs and versions. Groups are logged when computed. | output (display) · tool-call (G1 completion) | fail closed: if grouping cannot be computed, G1 does not open; G1 completion with an unconfirmed multi-approved group is refused | Build crew | Test T-W03a-1: two rows citing one paragraph → one group with a warning, shown and logged. **Test T-W03a-2**: approve both rows in a group, complete G1 without a reason → refused; with a reason → G1 completes and the audit log has the confirmation with reason, row IDs and versions. | Specialist sees the group with every row's quote and source; at completion, a single confirmation card naming the rows |
| CR-023 | Concurrent runs (PRD A-6) | The server refuses to start a run for a fund while one is `ACTIVE` (a stage running, or a gate waiting for the specialist: see "Run state model" in Work Ownership). A run in `FAILED`, `ABANDONED` or `COMPLETED` is not active. One run at a time is a code rule, not a convention; it also keeps versions (CR-009) and idempotency keys (CR-010) unambiguous. **Ways out of an active run:** it ends by completing, by failing (a failed step or a timeout), or by the specialist abandoning it (W-19a; reason required, audited, nothing undone); there is no other cancel. | tool-call | fail closed | Build crew | **T-RUN-0**: start a run, start another → refused with the active run's ID. **T-RUN-1**: make a unit fail → the stage ends, the run is `FAILED`, no gate opens, `POST /runs` now succeeds. **T-RUN-2**: a step that never returns → after `max_execution_time` the unit fails and the run is `FAILED`. **T-RUN-3**: abandon without a reason → `REASON_REQUIRED`; with a reason → `ABANDONED`, one audit entry (who, when, reason, stage, run version), row, verdict, decision and publication records unchanged, GP view unchanged, `POST /runs` succeeds. **T-RUN-4**: abandon a `FAILED`, `ABANDONED` or `COMPLETED` run → `RUN_NOT_ACTIVE`; a decision on an abandoned run → `RUN_NOT_ACTIVE`; a stale run version or a double submit → `VERSION_MISMATCH`, one audit entry | Specialist is shown the active run, and on a terminal run the state and its reason |

| CR-027 | A date rule silently resolved while its convention is open (PRD OQ-7, KEY OQ-D3; DL-20) | The regulation configuration records, for each convention application still under an open question, the question ID and the obligations it affects (MVP: `OQ-7` / `OQ-D3` → `OBL-02`). (1) At G1, when the specialist sets that row's business-day rule, the form shows that the rule depends on the open question; the row has no preselected rule beyond the safe default value (SD AC-026). (2) The date code copies the dependency onto every entry generated from that row: "rule depends on open question OQ-7 (AED subscription tax)". (3) At G3 the mark is shown on those entries, next to the "roll rule unconfirmed" and "precautionary" marks. It does **not** block publishing (like the other safe-default marks, US-010 c4) and is specialist-only, not shown to GPs (as the "roll rule unconfirmed" mark, US-011 assumptions). The mark is removed only by recording the answer to the open question in the configuration, which is a regulation change reviewed like any other (SD §10.2). | output (what the specialist sees at G1 and G3) | fail safe towards the mark: if the dependency cannot be evaluated, the entry is marked | Build crew · `@ux.designer` (mark wording) | **T-W13-1**: generate the demo calendar → all four `OBL-02` entries carry the OQ-7 mark at G3 and have the same dates under "no roll" and "roll forward"; no other entry carries it; GP view shows no mark; publishing is not blocked. **T-W13-2**: the date module contains no default rule for `OBL-02` (a row with rule unset stays "not confirmed") | Specialist sees the mark at G1 and G3; resolving it is a specialist decision or a question to a tax specialist, outside the system |

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
  The run-level hard stop at US$4 (CR-017) is the second breaker; any run over US$2 fails EC-012.
- **Week-1 measurement spike** (Build, before the estimate is final): run each role's call (extractor
  on one document, verifier on one row, judge on one row) on the demo inputs at least 5 times each and
  record tokens in and out, cost and latency per role, and **first-pass success with no re-ask** per
  role (the share of calls whose output passes the guardrail on the first attempt, with
  `guardrail_max_retries: 0`; D5), plus one full clean run end to end. The
  measured figures replace the estimates in SA-6, feed the six-week estimate and cut line (SOQ-1), and
  give `*define-eval-criteria` real numbers for the cost and latency thresholds. **Verifier
  bake-off (DL-26):** both verifier candidates, the mid-tier default and the reasoning model, run on
  the planted conflicts (`C-1` on `OBL-03`, `C-2` on `OBL-05`, and `I-1` on a copy of `OBL-02`), at
  least 5 times each. **If the mid-tier model misses any planted conflict in any run, the verifier
  switches to the reasoning model**; otherwise the mid-tier model stays. The spike records, for each
  candidate, recall on the planted conflicts, false alarms on the correct rows (reported for the
  operator; not part of the switch rule), and **cost per full run** (verifier calls × 6 rows plus the
  other roles), so the cost of each option against MC-002 and the US$50 cap is known. The choice is
  recorded in the decision log before the first evaluation cycle. Output: a short
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
  `OPENAI_API_KEY`, `LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY`, `LLM_MODEL_JUDGE`, `RUN_COST_CAP_USD`
  (default 4: the hard stop; any run over US$2 fails
  EC-012), `UNIT_RERUN_LIMIT` (default 3; future scope with re-run),
  `LLM_MAX_TOKENS_EXTRACT`, `LLM_MAX_TOKENS_VERIFY`, `LLM_MAX_TOKENS_JUDGE`.

### 1. MVP Architecture Philosophy & Principles

**MVP design principles** (each traced to the decision it comes from):

| Principle | What it means here | Source |
|---|---|---|
| Specialist feedback first | The demo's question is whether a specialist can *check* rather than *author* rules in under 30 minutes. Every design choice that adds review friction is measured against that (MC-003). | PRD §1, §7 · SD MC-003 |
| Simplest orchestration that delivers the value | A gated workflow: three stages, a CrewAI Flow per stage, three bounded model steps with no tools. No agent, no orchestrator, no memory. | Pattern Decision · DL-17 |
| Code owns state, models draft | Gates, dates, versions, IDs and the audit log are deterministic code in the backend; every model output is a validated proposal. | Work Ownership · CR-001, CR-002 |
| Fail closed, stay visible | Anything with a side effect refuses on doubt; anything uncertain is shown, not resolved (flags, "unsure", coverage gaps, open conventions). | Control Register · P-1 |
| Observable by default | Every model call has an append-only trace record; every decision has an audit entry with the version it was made on; run status is per unit. | CR-013, CR-018 · US-015 |
| Testable without a model | Gate, date, audit and access tests run with the Flows stubbed. | SD NFR-011 |
| Build for reuse, build only Part II | Regulation, fund terms and client policy live in configuration files, not in code; only the Luxembourg Part II configuration exists. | SD NFR-012, §10 |

**Core vs Future**:

| In the MVP (Must) | Stretch (Could, after the Must stories pass) | Future work (not built) |
|---|---|---|
| F1–F9 happy path; recovery paths (FR-022 to FR-025); manual row creation and release (FR-027, DL-18); coverage view (FR-028); duplicate groups (FR-029); per-unit failure and re-run (US-015); evaluation report (US-013) | F10 change monitoring (US-014; FR-021, FR-026; W-22; CR-024 to CR-026) | Filing status; notifications to filing parties; multiple funds and frameworks; official holiday source; fund-fact editing; configuration screens; client-data separation; unpublish/withdraw; four-eyes review (timing open, PRD OQ-1); full trail view (FR-019, P1); live dashboards; real authentication |

**Explicit exclusions** (from SD §9, kept visible because each is a tempting addition): no live
externals except the model provider; no task tool as the record; no PDF parsing; no real data; no
GP-facing change notifications (the review notice is not one, FR-025).

**Technical architecture decisions**:

| Decision | Choice | Why | Trace |
|---|---|---|---|
| Frontend framework | **Next.js (App Router) with TypeScript** | Operator intent (PRD OQ-8) and a sound fit: two route-based surfaces, server rendering for the read-only GP view, typed contracts with the backend. Resolves SOQ-4. | PRD A-4, OQ-8 · AM OD-12 |
| Backend language and framework | **Python 3.12, FastAPI, Pydantic v2** | CrewAI is a Python library, so the Flows run in Python; keeping gates, dates and audit in the same process avoids a second service that must agree on state. FastAPI gives typed request/response schemas and an OpenAPI contract the frontend can generate its client from. Pydantic models are shared by the API and by the CrewAI tasks' structured outputs. | `AAMAD_TARGET_RUNTIME=crewai` · CR-001, CR-003 |
| Storage | **SQLite** (one file, local), via SQLAlchemy 2 | PRD §3 requires persistence between sessions; one run at a time (A-6) and a local demo need no server database. Append-only is enforced at the storage boundary with database triggers (CR-013). | PRD §3 Storage · SD MD-009, NFR-003 |
| UI approach | Two surfaces, both route-based: a **specialist review surface** (runs, G1, G2, G3) and a **GP read-only calendar**. Not a chat, not a dashboard. Layout, components and visual design belong to `ux.md`. | PRD §6 names exactly these two surfaces. | PRD §6 · SD §1 |
| Runtime communication | The backend runs each stage's Flow as a **background task**; the frontend reads progress by **polling** the run-status endpoint. | Runs last minutes, not seconds; one user, one run. Polling is enough to show which units are finished, running or failed (US-015 c1) and needs no connection management. | US-015 · PRD A-6 |
| Streaming | **None.** No model output is shown while it is being generated; every model output is shown only after schema validation (CR-003). | Showing partial model text before validation would display unvalidated content. | SD NFR-004 |

### 2. Application Runtime Specification

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
agent, task and YAML conventions apply **inside** the Flows, as below.

**Runtime roles** (the only three; no others are added):

| Role (CrewAI agent) | Goal | Tools | Memory | Used in |
|---|---|---|---|---|
| `extractor` | Turn one source document into fixed-schema obligation rows, each citing one paragraph ID with a verbatim quote, with no dates and no business-day rule unless the source states one | **None** | None | Stage A, W-03 |
| `verifier` | Report internal and cross-source conflicts for one row, with evidence; never change the row, never choose a source | **None** | None | Stage A, W-05/W-06; re-verification W-08 |
| `judge` | Give one applicability verdict for one approved row, citing fact IDs; answer "unsure" rather than guess when a fact is missing | **None** | None | Stage B, W-11 |

Each role is used as a **one-agent, one-task crew** inside a function that implements the
runtime-neutral interface above. `allow_delegation=false`, `memory=False`, `tools=[]`, no manager
agent, `process=sequential` (trivially, with one task).

**Task and turn orchestration**:

| Stage Flow | Steps in order | Parallel part | Output to the backend | Budget (estimates; replaced by the week-1 spike) |
|---|---|---|---|---|
| A | load paragraphs (code) → `extract_rows` per document → duplicate grouping W-03a and coverage W-03b (code) → quote check W-04 (code) → `check_conflicts` per row | extraction per document; verification per row | rows, flags, quote-check results, groups, coverage list, per-unit status | `max_execution_time` 90 s per extraction task, 60 s per verification task; stage ≤ 3 min |
| B | load fund profile (code) → `judge_applicability` per approved row | per row | verdicts, per-unit status | 60 s per task; stage ≤ 90 s |
| C | date generation W-13, out-of-date marks W-14 (code only) | none | one complete calendar version, or nothing (CR-011) | < 5 s |

- **Context passing** between steps is through stored data, never through task context or agent
  memory: each task's input is built by code from the stored row, sources and profile (Model and
  Context Strategy). `Task.context` chaining is therefore **not used**; the dependency order is the
  Flow's step order, which is deterministic (adapter deviation D2).
- **Parallel units** run with `kickoff_for_each` (or its async form). The **deterministic merge key
  is the idempotency key** `run_id · step · unit_id · input_version` (CR-010), which the adapter
  requires for batch kickoffs.
- **Expected outputs**: every task sets `output_pydantic` to the step's schema (Row list, Flag list,
  Verdict) and a `guardrail` that validates the schema rules in CR-003 (paragraph ID exists, no date
  fields, verdict in the allowed set, fact IDs exist). Every task has a `Task.id` equal to the step
  name.
- **Error handling**: a guardrail failure or a timeout marks that unit failed and re-runnable (W-19);
  it is never retried automatically (Production Shape; `guardrail_max_retries: 0`, D5). Transport errors get one automatic retry.
- **Cancellation and timeouts**: there is **no general cancel** in the MVP: no cancel of a model call
  or a step, no undo and no rollback. Every task has a `max_execution_time`; a task that exceeds it
  fails its unit, so a hang becomes a failed unit and then a `FAILED` run ("Run state model" in Work Ownership).
  The one human way to close a run is **abandon** (W-19a): a specialist action with a written reason
  that closes an active run without undoing anything. The restart sweep that marked running units
  failed on start-up is future scope (DL-22); until it is built, a run left active by a crash is
  closed by abandoning it.
- **Sampling**: per role: temperature 0 where the model supports it (the reasoning judge may not),
  per-step `max_tokens` from configuration; model from `LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY` or
  `LLM_MODEL_JUDGE` (Model and Context Strategy).

**Runtime-conditional configuration (crewai)**, per `.cursor/rules/adapter-crewai.mdc`:

| Adapter rule | Setting here | Note |
|---|---|---|
| Agents and tasks in YAML | `backend/config/agents.yaml`, `backend/config/tasks.yaml` (three agents, three tasks) | Prompts live in these files and are content-hashed for the trace (CR-018) |
| Entry point | `backend/runtime/flows.py` (three stage Flows) instead of `crew.py` | "or equivalent runtime entrypoint" |
| `allow_delegation=false` | Yes, all agents | |
| Sequential process | Yes | Hierarchical not used |
| `max_iter <= 12` | `max_iter: 2` | No tools, so one reasoning step plus a final answer |
| `max_execution_time` per epic | As in the table above | Tuned after the spike |
| `max_rpm` at crew level | 30 | Bounds bursts from parallel units |
| Tools: minimum set | Empty for every agent | CR-002 |
| `memory=False` | Yes | No `CREWAI_STORAGE_DIR` needed |
| `Task.guardrail` for high-risk outputs | Yes, on all three tasks | Retry setting: D5 |
| `max_retry_limit`, `Task.context`, `expected_output`, output path, human review gate | See D1–D4 and D6 below | |

**Adapter deviations and interpretation (D1–D6).** *Accepted by operator decision, 2026-11-11
(DL-21).* Source: `.cursor/rules/adapter-crewai.mdc`. Build follows these instead of the adapter text
they name.

*Summary:*

- **D1**: `max_retry_limit` is 1, not ≥ 2: one automatic retry, transport errors only.
- **D2**: `Task.context` chaining is not used: every input is built by code from stored data.
- **D3**: `expected_output` describes a typed schema, not headings and artifact paths.
- **D4**: no per-task output path: outputs go to the database; every evaluation run must export its trace.
- **D5**: `guardrail_max_retries` is 0: a failed check is shown to the specialist, never re-asked.
- **D6** (interpretation): the human review gate is G1–G3 in the backend, not `human_input=true`.

*Detail:*

| # | Adapter rule, verbatim (line) | Conflicts with | Setting and justification | Accepted risk and mitigation |
|---|---|---|---|---|
| D1 | "`max_retry_limit >= 2`." (34) | Production Shape (retries) · CR-010 · CR-017 | `max_retry_limit: 1`. A second automatic attempt hides a systematic failure from the specialist and spends budget unseen. | More manual re-runs after two transient errors in a row; costs review time (MC-003), not correctness. |
| D2 | "Use explicit task context chaining (`Task.context`) for deterministic dependency flow." (24) | Model and Context Strategy · W-05 · DL-17 | Not used. `Task.context` would pass the extractor's output and reasoning into the verifier's prompt, breaking W-05. Order stays deterministic: it is the Flow's step order; inputs come from stored data. | Low; developers used to CrewAI may expect it. §2 states where every input comes from. |
| D3 | "Define `expected_output` with required headings and target artifact paths." (25) | CR-003 · CR-010 | `expected_output` describes the step's typed schema; `output_pydantic` enforces it. The adapter rule is written for document-producing crews; these tasks return data. | Low; a reviewer comparing against the adapter text sees a mismatch, so it is recorded here. |
| D4 | "Require `Task.id` and explicit output path for traceability." (54) | CR-010 · CR-013 · CR-018 | `Task.id` kept (equal to the step name); **no output path**. Outputs are stored in the database under their idempotency key; a file would be a second store outside the replace and append-only rules. Traceability is the trace store plus a **required export**: every evaluation run writes its trace records and lifecycle events to `project-context/2.build/logs/<run_id>/`, secrets redacted (adapter line 48). **The export is part of the evaluation run's definition of done**: an evaluation run without its export is reported as failed. Test **T-D4-1**: run the evaluation with the export step disabled or its output deleted → the evaluation run is marked failed and says why; with the export present → it passes the check and the export contains one record per model call attempt (matching the trace store count). | Medium-low before the test; low with T-D4-1 in place. |
| D5 | *Library default, not an adapter rule:* CrewAI re-asks the model when a guardrail fails (`guardrail_max_retries`). The adapter rule followed is "Use `Task.guardrail` for high-risk outputs" (53). | Pattern Decision (evaluator-optimizer rejected) · Production Shape (no retry on schema-invalid) · CR-003 | `guardrail_max_retries: 0`. Re-asking the model with its own failure is the self-correcting loop the design rejects; the failed unit is marked re-runnable for the specialist. | First-pass success may be lower (small formatting slips are not fixed by a re-ask). **The week-1 spike records first-pass success with no re-ask, per role** (Production Shape). If it is too low, the fix is a better prompt or schema, released under the swap rule, never a re-ask. |
| D6 | "For high-risk outputs, require a human review gate (`human_input=true` or explicit review task)." (56) | DL-17 (backend owns gate state) | *Recorded interpretation, not a deviation.* G1, G2 and G3 in the backend are the explicit review; `human_input=true` would put gate state inside a Flow. | Low; if `@security.eng` reads the rule literally, this is re-raised as a deviation. |

### 3. Frontend Architecture Specification

**Technology stack**:

| Concern | Choice | Note |
|---|---|---|
| Framework | Next.js (App Router), TypeScript in strict mode | §1 |
| UI library and styling | **Proposed default:** Tailwind CSS with accessible headless primitives (for example Radix UI). **Not mandatory**; `ux.md` may replace it | The SAD does not fix a vendor UI library (template rule). The constraint is WCAG 2.2 AA (PRD §6) and the voice rule (DL-05) |
| Type safety at the boundary | **The FastAPI OpenAPI schema is the single contract.** TypeScript types, the API client and the frontend fixtures are all generated from it; none is written by hand | One source of truth for request and response shapes; a schema change regenerates all three, so they cannot drift (§4) |
| State management | Server data fetched per page; no global client store. Local form state only. The server is the source of truth for every status and version | The frontend never computes gate state, dates, flags or versions |
| Data freshness | Run status polled every 2 s while a stage is running; review pages re-fetch after each decision | §1 |

**Application structure** (route boundaries; screens and layout belong to `ux.md`):

| Route | Role | Purpose | Trace |
|---|---|---|---|
| `/` | any | Mock sign-in: choose specialist or GP (mocked identity) | SD A-5 |
| `/specialist/runs` | specialist | Start a run (refused while one is active, CR-023); list runs | US-015 |
| `/specialist/runs/[runId]` | specialist | Run status per stage and per unit, with the run state (`ACTIVE`, `FAILED`, `ABANDONED`, `COMPLETED`); abandon an active run (reason required); re-run a failed unit and release a failed extraction document (future scope) | US-015, DL-18, DL-22 |
| `/specialist/runs/[runId]/g1` | specialist | Rows with quote, quote-check result and flags; duplicate groups with warnings; coverage view; edit, approve, reject, reopen; add a row by hand; complete G1 (with group confirmation when required) | US-001 to US-005, US-016 · FR-027 to FR-029 |
| `/specialist/runs/[runId]/g2` | specialist | Verdicts with reasoning and openable fact values; confirm, override, decide "unsure", reopen; GP-visible reason field | US-007 · W-17 |
| `/specialist/runs/[runId]/g3` | specialist | Full calendar version with roll, unconfirmed, precautionary and OQ-7 marks; "conventions not yet checked" note; publish or decline | US-010 · CR-027 |
| `/calendar` | GP (and specialist, read-only) | Published calendar only; calendar-level note. **Before the first publication: a read-only empty state with the fixed message 'Your obligations calendar is being prepared and checked by a specialist. Nothing has been published yet.' (DL-27).** No entries, counts or draft content, and no notifications. Review notice when active (*future scope*, DL-22) | US-011 · DL-27 |

- **API client boundary**: all calls go through one generated client module. During the Frontend epic
  the client is backed by **fixtures generated from the OpenAPI schema** (examples on the Pydantic
  models, so each fixture is a valid response by construction; no backend wiring in the FE epic). The
  Integration epic swaps the fixtures for the live backend. A check in CI regenerates the types and
  fixtures from the current schema and fails if the committed copies differ.
- **Component architecture**: shared building blocks for the recurring evidence patterns: a row card
  (fields, quote, check result, flags), a flag (type plus evidence, DL-03), a decision control
  (separate explicit actions, nothing preselected, reason field when required, AC-026), a mark badge
  (roll, unconfirmed, precautionary, OQ-7). Exact components are `ux.md`'s.
- **Accessibility and responsiveness**: WCAG 2.2 AA on both surfaces (PRD §6). The specialist surface
  is designed for desktop review; the GP calendar must also work on a phone-width screen.

**Interface requirements**:

- **Primary interaction surface**: the specialist review pages above (PRD §6), not a chat.
- **Loading states**: per unit during a run (running, finished, failed with reason); per page while
  data loads.
- **Error states**: every refusal from the backend is shown as the plain message the backend returns,
  naming what was refused and why, in the voice of DL-05: gate incomplete, version changed since the
  page was loaded (CR-009), run already active (CR-023), re-run limit reached (CR-010), cost cap
  reached (CR-017), model service not responding (circuit breaker).
- **Placeholders for future work**: **none.** No disabled buttons or "coming soon" items for future
  features, on either surface. A placeholder can imply functionality the system does not have, which
  matters most on the GP view (MN-007, DL-01).

### 4. Backend Architecture Specification

**API architecture.** FastAPI, JSON over HTTP, all request and response bodies as Pydantic models
published in the OpenAPI schema. **That schema is the single contract** between frontend and backend
(§3): TypeScript types, the client and the fixtures are generated from it. Every write endpoint
checks the mocked role server-side (CR-004). **Every decision or state-changing request carries the
version the specialist saw**, and the server refuses it with `VERSION_MISMATCH` if that version is no
longer current (CR-009): the entity version for row, verdict and calendar decisions, and the **run
state version** (an integer on the run, +1 on every unit or gate change) for re-run, release and gate
completion. This also absorbs double submits.

**How the round-2 controls appear in this section** (cross-check):

| Control | Where in §4 |
|---|---|
| CR-010, CR-013: replaceable current outputs vs append-only records | `current_outputs` table (replaced per idempotency key) vs `trace`, `audit_log` and the `*_versions` tables (append-only, enforced by triggers) |
| CR-017: cost cap aligned to MC-002 | **Cost rule: US$4 hard stop; any run over US$2 fails EC-012.** `RUN_COST_CAP_USD` (default 4) stops model calls; `COST_CAP` refusal code |
| CR-023: one active run | `POST /runs` refuses with `RUN_ACTIVE` while a run is active |
| CR-009: version on every decision | Every decision and state-changing request below carries `version` or `run_version` |

| Endpoint (shape) | Role | Purpose | Controls |
|---|---|---|---|
| `POST /runs` | specialist | Start a run for `FND-DEMO-01`; backend triggers stage A | CR-023 |
| `GET /runs/{run_id}` | specialist | Run status: stages, units, failures, cost so far | US-015 |
| `POST /runs/{run_id}/units/{unit_id}/rerun` `{run_version}` | specialist | Re-run one failed unit | CR-009, CR-010 |
| `POST /runs/{run_id}/units/{unit_id}/release` `{run_version, reason}` | specialist | Release a failed extraction document to manual entry | CR-009, CR-010, DL-18 |
| `POST /runs/{run_id}/abandon` `{run_version, reason}` | specialist | Abandon an `ACTIVE` run with a written reason; nothing is undone | CR-009, CR-023, W-19a |
| `GET /runs/{run_id}/g1` | specialist | Rows, flags, quote checks, duplicate groups, coverage list | W-03a, W-03b |
| `POST /runs/{run_id}/rows` `{paragraph_id, quote, fields}` | specialist | Create a row by hand | CR-020 |
| `PATCH /rows/{row_id}` `{version, fields}` | specialist | Edit a pending or approved row; triggers re-verification | CR-005, CR-009, W-08 |
| `POST /rows/{row_id}/decision` `{version, decision, business_day_rule, reason?}` | specialist | Approve or reject one row | CR-005, CR-007, CR-009 |
| `POST /rows/{row_id}/reopen` `{version, reason}` | specialist | Reopen a rejected row | FR-023 |
| `POST /runs/{run_id}/g1/complete` `{run_version, group_confirmations?: [{group_id, row_versions: {row_id: version}, reason}]}` | specialist | Complete G1; backend triggers stage B. A group confirmation is refused if any confirmed row's version has changed | CR-001, CR-009, CR-022 |
| `GET /runs/{run_id}/g2` | specialist | Verdicts with reasoning and fact values | W-12 |
| `POST /verdicts/{verdict_id}/decision` `{version, decision, value?, reason?}` | specialist | Confirm, override or decide "unsure" | CR-007, CR-009 |
| `POST /verdicts/{verdict_id}/reopen` `{version, reason}` | specialist | Reopen a confirmed verdict | FR-024 |
| `POST /runs/{run_id}/g2/complete` `{run_version}` | specialist | Complete G2; backend triggers stage C | CR-001, CR-009 |
| `GET /runs/{run_id}/g3` | specialist | Calendar version with marks | CR-027 |
| `POST /calendars/{calendar_id}/publish` `{version}` | specialist | Publish the whole version | CR-001, CR-011 |
| `POST /calendars/{calendar_id}/decline` `{version, reason, next_step}` | specialist | Decline at G3 | FR-022 |
| `GET /calendar` | GP, specialist | Published version only, review notice, calendar-level note | CR-012 |
| `GET /health` | none | Liveness for local start-up checks | §5 |

- **Validation**: Pydantic on every request; unknown fields rejected.
- **Rate limiting**: none at the HTTP layer (one local user). Model-call limits are `max_rpm` and the
  cost cap (CR-017).
- **Error envelope** (every non-2xx response):
  `{"error": {"code": "VERSION_MISMATCH", "message": "<plain sentence for the specialist>", "details": {...}}}`.
  Codes: `FORBIDDEN` (403), `VALIDATION` (422), `VERSION_MISMATCH` (409), `GATE_INCOMPLETE` (409),
  `RUN_ACTIVE` (409), `RUN_NOT_ACTIVE` (409), `RERUN_LIMIT` (409), `QUOTE_CHECK_FAILED` (409), `REASON_REQUIRED` (422),
  `COST_CAP` (409), `MODEL_UNAVAILABLE` (503). Every refusal is also written to the audit log
  (CR-001).
- **Streaming or event envelope**: none (§1).

**Data architecture.** Persistence is required (PRD §3), so this section is not deferred. One SQLite
file; the main tables:

**Every business table carries `fund_id`**, even though the MVP has one fund (`FND-DEMO-01`): runs,
units, rows and row versions, flags and quote checks, duplicate groups and coverage, verdicts and
verdict versions, calendar versions and entries, publications, releases, and the audit log and
trace. Foreign keys include it, so a row cannot point at another fund's run and an entry cannot
belong to another fund's calendar. Adding a second fund (S-1) is then data and a fund selector, not
a schema migration. The `fund_id` is set by the backend from the run, never taken from a request
body on a decision endpoint.

| Table | Holds | Write rule |
|---|---|---|
| `runs`, `units` | Run (with `fund_id`) and per-unit status, attempt counts, release records | Updated by the backend |
| `paragraphs` | Loaded source paragraphs with IDs and a content hash | Loaded from mock files per run |
| `rows`, `row_versions` | Current row and every version of it (`fund_id`, fields, quote, origin, status) | `row_versions` append-only |
| `flags`, `quote_checks` | Verification results per row version | Append per row version |
| `duplicate_groups`, `coverage` | W-03a groups and W-03b list per run | Recomputed by code; computations logged |
| `verdicts`, `verdict_versions` | Current verdict and every version (`fund_id`, row ID and row version judged) | `verdict_versions` append-only |
| `calendar_versions`, `calendar_entries` | Each generated calendar version and its entries (`fund_id` on both) | Append-only per version (CR-011) |
| `publications` | The published calendar version per fund, and the review-notice state | One atomic pointer switch per publish |
| `current_outputs` | One model output per idempotency key | Replaced on re-run (CR-010) |
| `trace` | Every model call attempt | **Append-only** (CR-013, CR-018) |
| `audit_log` | Every human decision, agent output reference, gate event, refusal and system event | **Append-only** (CR-013) |

Append-only tables have database triggers that raise an error on `UPDATE` or `DELETE`, so the rule
holds even if application code tries (CR-013).

**Identifier and version schemes** (resolves the remainder of SOQ-3; answers OQ-US016-1):

| Identifier | Scheme | Why |
|---|---|---|
| Run | `RUN-<yyyymmdd>-<n>` | Readable in reports and logs |
| Row | `ROW-<run>-<n>`, where `<n>` is a **run-wide sequence assigned by the backend** when the row is stored (never by a model, never per paragraph). The same scheme for model-extracted and human-created rows; **origin is a separate field** (`model` / `human`) | Unique by construction: a human-created and an extracted row citing the same paragraph, or two rows extracted from one paragraph, get different `<n>`. The origin label is the rule (US-016); meaning is not encoded in the ID. The evaluation filters by origin to count human-created rows separately (US-013 c8). Test **T-ID-1**: extract two rows from one paragraph and create a third by hand citing it → three distinct row IDs; a unique constraint on `rows.id` refuses any duplicate insert |
| Versions | Integer per row, verdict and calendar, starting at 1, +1 on every change | CR-009 |
| Stable calendar entry ID | `ENT-<fund>-<paragraph_id>-<recipient>-q<quote_pos>-<period>`, where `<recipient>` is the authority code (for example `CSSF`, `AED`), `<quote_pos>` is the character position where the row's quote starts in its normalised paragraph (QN-1), and `<period>` is the anchor period (for example `2027-03` for a monthly or quarterly obligation, `FY2026` for an annual one) or the event ID for an event-triggered entry (`EVT-01`). Example: `ENT-FND-DEMO-01-SRC-CSSF15627-P2-CSSF-q0-2026-12` | Same occurrence, same ID, across regenerations and runs (US-008 c7, FR-016), and independent of the due date, so editing an offset moves the date without changing the ID a future filing record would reference. The recipient separates rows from one paragraph that go to different authorities (SA-9); the quote position separates two obligations in one paragraph to the **same** authority, because their quotes start at different places. The quote position is used rather than a sequence number because a sequence would shift when a row is added, rejected or reopened; the position changes only if the quote itself is edited, which is a new occurrence. If two approved rows would still produce the same entry ID (same paragraph, authority, quote and period: a true duplicate), generation fails closed and names both rows. Test **T-ID-2**: two approved rows citing one paragraph, same authority, different quotes → distinct entry IDs; regenerate → same IDs; edit one row's offset → its dates move, its IDs do not; two rows with the same quote → generation refused naming both |
| Idempotency key | `run_id · step · unit_id · input_version`; trace adds `· attempt_n` | CR-010 |

**Runtime integration layer.** The API layer calls services; services own gate transitions, versions
and audit writes. When a gate completes, the gate service records the transition and **then** starts
the next stage's Flow as a background task with only the run ID. The Flow calls back into service
functions to store each unit's output; it cannot call the gate service. Configuration for the
pattern is in versioned files: `backend/config/agents.yaml` and `tasks.yaml` (runtime),
`config/regulation/lu-part2.yaml` (conventions `D-1` to `D-7`, mock holiday list, open conventions
for CR-027, source file list), `config/fund/FND-DEMO-01.yaml` (fund profile), and
`config/policy/default.yaml` (client policy: unconfirmed-roll default, P-1 treatment). Each file's
content hash is part of the input version of the steps that read it, so a configuration change
invalidates outputs the same way an edit does (SD §10.2). Logging and trace hooks: CR-018 records per
call; the audit log per decision.

**Authentication and secrets** (names only; values never committed; `.env.example` created in
Build setup):

| Variable | Purpose |
|---|---|
| `AAMAD_TARGET_RUNTIME` | `crewai` (development crew setting, recorded in Audit) |
| `OPENAI_API_KEY` | OpenAI API key; the provider's standard name, which CrewAI reads directly (DL-25) |
| `LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY`, `LLM_MODEL_JUDGE` | Model per role (DL-25); exact IDs confirmed before the spike |
| `LLM_MAX_TOKENS_EXTRACT`, `LLM_MAX_TOKENS_VERIFY`, `LLM_MAX_TOKENS_JUDGE` | Per-step output limits |
| `RUN_COST_CAP_USD`, `UNIT_RERUN_LIMIT` | CR-017, CR-010 |
| `SESSION_SECRET` | Signs the mocked-identity session cookie |
| `DATABASE_PATH` | SQLite file location |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend → backend base URL |

Authentication is mocked (SD A-5): the sign-in page sets a signed session cookie holding a mocked
identity and role (`specialist-1` / `gp-1`); the backend reads the role from the cookie on every
request. This is a demo mechanism, not access control (AM §3).

### 5. DevOps & Deployment Architecture

**Hosting**: **local only** (PRD §3 Infrastructure, §5 Availability N/A). The demo runs on the
operator's machine: the FastAPI backend and the Next.js frontend as two local processes, started by
one documented command (for example `make dev`), with the SQLite file under a git-ignored `data/`
folder. No cloud target, no container registry, no domain. `GET /health` returns 200 once the
database is reachable and the configuration files have loaded; the start command waits on it.

**CI (minimal, on every pull request, GitHub Actions):**

| Step | What it checks | Never does |
|---|---|---|
| Lint and format | Python (ruff), TypeScript (eslint, prettier) | |
| Type check | Python (mypy or pyright, strict on `backend/`), TypeScript (`tsc --noEmit`, strict) | |
| Backend tests | Gate, date, audit, access, ID, version and control tests (CR-001 to CR-027 tests, T-W04-*, T-ID-*, T-REL-*, T-W13-*) with the Flows and model steps **stubbed** | Call a language model (SD NFR-011); CI holds no model API key |
| Contract drift | Regenerates OpenAPI, TypeScript types and fixtures; fails if committed copies differ (§3) | |
| Frontend build and tests | `next build`; component tests against the generated fixtures | |
| Prompt and fixture check | No prompt template or run-time fixture references the answer key (CR-016) | |

**Not in CI, and why:**

- **The real-name scan** cannot run in CI: its identifier list lives in the git-ignored
  `reference/` folder and must never reach GitHub. It runs locally instead, as below.
- **Evaluation runs** (US-013) need the live model and a key. They run locally, by the operator or
  `@qa.eng`, on demand and before the demo; each produces a saved report and the required trace
  export (D4, T-D4-1).

**Release rule for model-facing changes** (because evaluations are not in CI): a pull request that
changes any **prompt** (`agents.yaml`, `tasks.yaml`), the **model or sampling settings**
(`LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY`, `LLM_MODEL_JUDGE`, temperature, `max_tokens`), or any **step schema** (Row, Flag, Verdict, guardrails)
must link the saved reports of **three consecutive local evaluation runs** made **on that branch's
final commit** (EC-R1), and each must meet the swap-as-release criteria (Model and Context Strategy)
and the model-dependent criteria in §9 (EC-001 to EC-007, EC-010, EC-012, EC-021). No report, or a stale or failing one, means no merge. A CI step
helps enforce it: if the PR touches those files, the PR description must contain a report link, or
the check fails. The reviewer confirms the report's commit matches the PR head.

**Real-name scan as a local git hook** (project `CLAUDE.md`):

- A **pre-commit hook** runs the scan on the staged files, and a **pre-push hook** runs it on the
  whole tree. The hook script is committed (`scripts/real-name-scan.sh`, installed by
  `make install-hooks`); it contains no identifiers and reads them from
  `reference/real-identifiers.txt` at run time.
- **Fail closed**: a match blocks the commit or push. If the identifier file is missing (for
  example in a fresh clone without `reference/`), the hook **refuses** the commit or push instead of
  passing silently.
- **If it is bypassed** (`git commit --no-verify`, hooks not installed, or a commit made elsewhere):
  git cannot prevent this, so the rule is procedural. (1) The project rules still require the scan
  before every commit and push, and the pre-push hook is a second chance. (2) If a match is found
  in a commit that has **not** been pushed, the commit is rewritten locally before pushing. (3) If
  a match has **already been pushed**, the repository is public, so treat it as **exposed**: stop
  pushing, remove it in a new commit at once, and take the history question (rewrite history or
  make the repository private) to the operator, which is the same open decision as DL-07.
  `@security.eng` checks that the hooks are installed and that no bypass has left a match in
  history.

**IaC, multi-region, advanced monitoring**: Future Work (no hosting target exists).

**Observability** (two separate designs, as the template requires):

| Kind | Design | Where |
|---|---|---|
| Per request | One trace record per model-call attempt (CR-018) plus audit entries for every decision and refusal, all sharing the run ID; together they reconstruct any row, verdict or entry | `trace`, `audit_log` tables; exported per evaluation run to `project-context/2.build/logs/<run_id>/` |
| Aggregate | The evaluation report per run: accuracy against the answer key, cost, time, review time, human-created rows, extraction failures, first-pass success | Saved per run ID, never overwritten (US-013 c5) |
| Process logs | Structured backend logs (start-up, stage start/end, refusals) at INFO; no prompt text or secrets at INFO | Console and a git-ignored log file |

### 6. Data Flow & Integration Architecture

**Request and response path for the happy path** (each arrow is an HTTP call from the frontend or a
backend call; "→ Flow" means the backend starts a stage Flow as a background task):

| # | Actor action | Path | What is stored | What the specialist sees next |
|---|---|---|---|---|
| 1 | Start run | UI → `POST /runs` → gate service (CR-023) → **Flow A** | run, units (`pending`) | Run status, polled |
| 2 | (Flow A) | load paragraphs → `extract_rows` per document (model) → grouping, coverage, quote check (code) → `check_conflicts` per row (model) | `current_outputs`, `trace`, rows v1, flags, groups, coverage; units `valid` / `failed` | Units turning finished or failed; G1 opens when all units are valid or released |
| 3 | Review at G1 | UI → `GET g1`; decisions → `POST /rows/...` (with versions) | `row_versions`, `audit_log` | Row status, flags, groups, coverage |
| 4 | Complete G1 | UI → `POST g1/complete` → gate service → **Flow B** | gate event in `audit_log` | Run status for stage B |
| 5 | (Flow B) | `judge_applicability` per approved row (model) | `current_outputs`, `trace`, verdicts v1 | G2 opens when all units are valid |
| 6 | Review and complete G2 | UI → verdict decisions → `POST g2/complete` → gate service → **Flow C** | `verdict_versions`, `audit_log` | Stage C status |
| 7 | (Flow C) | date generation, out-of-date marks (code) | one `calendar_versions` row and its entries, or nothing | G3 |
| 8 | Publish at G3 | UI → `POST /calendars/{id}/publish` | `publications` pointer switch, `audit_log` | Confirmation |
| 9 | GP views | GP UI → `GET /calendar` | nothing | Published entries, calendar note, review notice if active |

Edits, reopenings and re-runs use the same path at a smaller scale: an edit re-runs the verifier on
one row (W-08) through the same `check_conflicts` function, outside a stage Flow, triggered by the
row service.

**External integrations in the MVP**: one only, the **language-model provider**, called from inside
the three step functions (Model and Context Strategy, entry point). Every business-side system is
replaced by a versioned file under `config/` or `mock-data/` (PRD §3 Integration Requirements).

**Error propagation and user-visible feedback**:

| Where it fails | What happens | What the specialist sees |
|---|---|---|
| A model call (transport) | One automatic retry (D1); then the unit is failed | The unit marked failed with "the model service did not respond"; re-run option |
| A model output (schema) | Guardrail fails, no re-ask (D5); unit failed | The unit marked failed with the validation message, in plain words |
| Several calls in a stage | Circuit breaker stops new calls (Production Shape) | One message: "the model service is not responding; nothing moved forward" |
| The cost cap | No further calls in the run (CR-017) | The stop reason and cost so far |
| A decision request | Refused with an error code (§4) and logged | The backend's plain message (§3 error states) |
| Calendar generation | All-or-nothing; nothing stored on failure (CR-011) | Stage C failed; G3 not offered |
| The backend process | Restart marks running units failed (§2); in the MVP the restart sweep is future scope (DL-22) | Units marked failed and re-runnable after restart (future scope); in the MVP a run left active by a crash is abandoned with a reason |
| A step fails or exceeds its time limit | The stage ends, the run moves to `FAILED`, no gate opens (Run state model) | The state `FAILED`, the step, the unit and the reason; a new run can be started |
| The specialist abandons a run | The run moves to `ABANDONED`; nothing is undone; audited (W-19a) | The state `ABANDONED` with the reason; a new run can be started |

### 7. Performance & Scalability Specifications

**Targets at expected volume** (one specialist, one fund, one run at a time, PRD A-6):

| Target | Value | Source | Measured by |
|---|---|---|---|
| Agent output for a full run | **Under 5 minutes**, including re-runs and re-verifications attributable to the run, excluding time waiting for the specialist | SD MC-001 | Evaluation report (US-013 c3) |
| Model cost per run | **Under US$2**, same scope. **Cost rule: US$4 hard stop; any run over US$2 fails EC-012.** (CR-017) | SD MC-002 | Evaluation report (EC-012) |
| Specialist review | **Under 30 minutes**, G1 opened → G3 published, from audit timestamps. **Depends on the G1 and G2 review design by `@ux.designer`**: the architecture fixes what must be shown and decided per item (explicit decisions, no bulk actions, AC-026), but how quickly a specialist can read a row's evidence and decide is a UX outcome. `ux.md` should treat this target as a design constraint | SD MC-003 | Evaluation report |
| Concurrency | One active run (CR-023); one specialist and any number of GP readers of a static published version | PRD A-6 | Test for CR-023 |
| Interactive response (design budget, not a requirement) | Page data and decision requests answer in under 1 second on the demo machine; stage C under 5 seconds | SA-14 | Observed in the demo rehearsal; not a pass/fail target |

**Evaluation cost (development budget, not MC-002).** MC-002 limits **one** run. Every evaluation
**cycle** is three runs (EC-R1), so a cycle costs **up to US$6** in model usage and about **15
minutes** of agent time, and any failure repeats all three (EC-R1a). Cycles happen at least for the
week-1 spike follow-up, every prompt, model or schema change (§5 release rule), each prompt-tuning
iteration in WP-19 (the widest-range package), and the demo. The number of cycles is not knowable in
advance; total evaluation spend is the sum recorded in the saved reports, and `@qa.eng` reports it
with each cycle.

**Development spend cap (operator decision, DL-24; resolves SOQ-13)**:

| Item | Rule |
|---|---|
| Hard cap | **US$50** of model usage for development (spike, prompt tuning, evaluation runs, any other Build calls) **until 13 December 2026** |
| How it is enforced in practice | **Prepaid OpenAI credits** (DL-25): **US$25 loaded to start**, which is the checkpoint, so usage stops when the balance runs out; topping up to the **US$50 ceiling** is a deliberate step taken only after the checkpoint review. A provider spending limit at US$50 is set as a second guard where the account offers one |
| Where it is enforced | **In the model provider's account** (a spending limit set by the operator), **not in the application**. It is an operator-owned control; nothing in the code claims to enforce it. The per-run hard stop (CR-017) is separate and still applies inside each run |
| Checkpoint | At **US$25 (50%)**: **stop** model calls and review usage **by activity** (spike, tuning, evaluation runs) before continuing. The provider account's usage figure is the authority for the total; the evaluation reports (EC-R6) give the breakdown by activity |
| Raising it | Only on purpose, by a recorded operator decision (for example, to match course credits if they cover more, so nothing is paid out of pocket) |
| Planning basis | About 15–20 evaluation runs (5–7 cycles) at under US$2 each, plus the spike and a day of tuning; estimates, replaced by the spike's measured figures |

A model swap for any role (for example a stronger model for the applicability judge) is a release
under the swap rule, with its own three-run evaluation; its cost shows at the checkpoint.

**Scaling path, deferred with reasons**: the MVP is one fund, one framework, local (SD A-1, §9). The
known steps if that changes, none built: SQLite → a server database (the data layer uses SQLAlchemy,
so the change is configuration plus migrations); background task → a job queue with one worker per
run; one active run → one active run *per fund*; per-client isolation (§8). The per-unit design (W-19)
already parallelises within a stage, which is the part that grows with document count.

**Token and cost controls at the runtime layer**: fixed `max_tokens` per step; bounded inputs (one
document, or one row plus the source set); `max_rpm: 30`; one transport retry, no re-ask (D1, D5);
three manual re-runs per unit (CR-010); the per-run cost cap (CR-017); cost per call in every trace
record (CR-018). The week-1 spike replaces the estimates (SA-6, SA-13).

### 8. Security & Compliance Architecture

**AuthN and AuthZ for the MVP**: authentication is **mocked** (SD A-5): a signed session cookie
holding a mocked identity and role (§4). Authorisation is real code: every write endpoint checks the
role server-side, GP endpoints are read-only and serve published data only (CR-004, CR-012). This is
enough to demonstrate the role rules; it is not an access-control claim (AM §3).

**Baselines**:

| Area | Baseline | Control |
|---|---|---|
| Input validation | Pydantic on every request, unknown fields rejected; versions required on decisions | §4, CR-009 |
| Model input | Human-written text placed as delimited data, never as instruction | CR-014 |
| Model output | Schema-validated before storage; rendered as escaped text, never as HTML or markdown with active content | CR-003, CR-015 |
| Secrets | Environment variables only; `.env` git-ignored; `.env.example` lists names | CR-021, §4 |
| Data at rest | Local SQLite file in a git-ignored folder. No encryption at rest: mock data only, no personal or client data (SD MN-001) | Future work if real data is ever used |
| Data in transit | Localhost only; no TLS in the local demo. The only external call, to the model provider, uses the provider's HTTPS endpoint | |
| Record integrity | Append-only audit and trace tables enforced by triggers (CR-013). Not tamper-evident (no hashing chain): deferred (US-012 scope) | CR-013 |
| Dependencies | Versions pinned in lock files; dependency audit in `@security.eng`'s assessment | |

**The Control Register is the application-layer safety design.** `@security.eng` verifies it against
the code before Deliver (`security.require_security_assessment`, aamad-core), including the D1–D6
adapter deviations and the D6 interpretation.

**Compliance**: the output is a specialist-approved interpretation, **not legal advice** (SD MN-009):
a fixed calendar-level note on the GP view (FR-020) and the conventions note at G3. No personal data is
processed. The repository is public, so no real identifiers are committed (MN-001). The real-name scan runs as local pre-commit and pre-push hooks that fail closed, with a defined response if they are bypassed (§5).

**Future client-isolation boundary** (SD §10.5, OQ-13; **named only, not built or validated**):

- **Boundary**: one **client** = one isolated data store (its own database, or its own schema in a
  shared server database) plus its own namespace of configuration (`config/fund/<client>/…`,
  `config/policy/<client>.yaml`). Regulation configuration is shared across clients (it is the
  regulation, not the client's), which is what EX-1 asks for.
- **Access-control assumptions this boundary relies on**: real authentication with per-user
  identity; every identity bound to exactly one client; the client is resolved server-side from the
  identity, never from a request parameter; the backend opens only that client's store for the
  request; the audit log and the trace are per client; the evaluation fixtures stay outside client
  stores.
- **Not claimed**: that the MVP's mocked roles, single SQLite file or single configuration namespace
  provide any of this. The walkthroughs do not validate multi-client security (SD §10.5).

### 9. Testing & Quality Assurance Specifications

**Test layers** (all except the last run in CI with the model stubbed, SD NFR-011):

| Layer | What it covers | Examples (test IDs in this SAD and AM §7) |
|---|---|---|
| Unit (backend) | Deterministic modules in isolation | Date engine: the 22 expected entries, rolls, unconfirmed marks, event awareness, OQ-7 mark (US-008, US-009, T-W13-1/2) · quote check under QN-1 (T-W04-1 to 6) · ID schemes (T-ID-1/2) · grouping and coverage (T-W03a-1, AC-029) |
| Control tests (integration, stubbed model) | Every Control Register entry through the API, with the database | CR-001 to CR-027 evidence tests · AM T-01 to T-23 · T-REL-1/2 · T-W03a-2 · version and double-submit refusals (CR-009) · one active run (CR-023) |
| Runtime checks | The CrewAI configuration behaves as recorded | No agent has a tool (T-07) · every task has `Task.id` and `output_pydantic` · a guardrail failure fails the unit with **no re-ask** (D5) · one transport retry only (D1) · one trace record per attempt (CR-018) · trace export present (T-D4-1) |
| Contract | Frontend and backend agree | OpenAPI regenerated; types and fixtures match (drift check, §3) · request validation rejects unknown fields |
| Frontend | Pages render every state from generated fixtures | Component tests per route; automated accessibility checks plus a manual WCAG 2.2 AA review of both surfaces (PRD §6) |
| Smoke / acceptance | The happy path end to end | In CI with stubbed model outputs equal to the answer key (deterministic); locally with the live model before the demo |
| Evaluation (local, live model) | Agent quality against the answer key | US-013 report; pass/fail per the criteria table below; required for every prompt, model or schema change (§5 release rule) |

**Verification before Deliver**: `@qa.eng` `*verify-change` on the final branch; the security
assessment by `@security.eng` is **required** (aamad-core 1.0 default; `aamad.config.yml` does not
switch it off), and verifies the Control Register, D1–D6 and the git hooks (§5).

**Evaluation Criteria** (`*define-eval-criteria`, 2026-11-11). The pass/fail contract only; golden
dataset, graders and runner are `@qa.eng`'s `*run-evals`. Thresholds come from PRD §7, SD MC-001 to
MC-003 and MP-001 to MP-008, the answer key (KEY), and two operator answers (EC-R1, EC-002). Scope is
the **thin slice** (DL-22); future-scope behaviour has no criterion here.

**Run rules**:

- **EC-R1 (operator decision, DL-23): 3 of 3.** The model-dependent criteria (EC-001 to EC-007,
  EC-010, EC-012, EC-021) must pass on **each of three consecutive evaluation runs on the same
  commit**. One failing run fails the release or the demo gate.
- **EC-R2: scripted gates.** An evaluation run drives G1, G2 and G3 through the API with the demo
  decisions in the story index (`user-stories/README.md`), as the mocked identity `specialist-eval`,
  which the audit log records. This is why review time is **not** measured on evaluation runs (EC-011).
- **EC-R3: exact or miss.** A criterion passes only at its stated value. A miss is reported with the
  expected and actual values, never hidden, and the gates still keep unapproved output from GPs
  (PRD §7, DL-10).
- **EC-R1a: no best-of.** If any criterion fails on **any** of the three runs, the cycle fails. The
  fix is made, and **all three** runs are repeated on the new commit. Passing runs from an earlier
  commit are not reused, and a cycle is never judged on its best runs. Every run's report is kept
  (US-013 c5), including failed ones.
- **EC-R5: name-match rule, written before the first evaluation run.** The operator writes the rule
  EC-002 is judged by and records it in `project-context/2.build/evals.md` (or the file `@qa.eng`
  names for it) **before the first evaluation run**; a rule changed after a run has been graded
  applies only to later cycles, and the change is logged. Starting draft for the operator to confirm
  or change: *a name matches if it identifies the same filing, report or payment, for the same
  recipient, as the KEY §1 name; wording, word order, abbreviations, articles and capitalisation may
  differ. It does not match if it names a different document, adds or drops a component (for
  example "return" where KEY §1 has "return and payment"), or names a different recipient.*
- **EC-R6: spend logged per evaluation run (DL-24).** Every evaluation run's saved report records:
  its model cost from provider usage data (as for EC-012); an **activity label** (`spike`, `tuning`,
  `release` or `demo`); and the **running total** of development spend recorded in reports since
  2026-11-12, against the US$50 cap and the US$25 checkpoint. When the running total reaches US$25,
  the report says so at the top, and model calls stop until the operator has reviewed usage by
  activity. Calls outside evaluation runs (for example the spike's single-role calls) are logged the
  same way by the spike script. The provider account remains the authority for the true total;
  the reports explain where it went.
- **EC-R4: where each runs.** Code-based criteria that need no model (EC-008, EC-009, EC-013, EC-015
  to EC-017, EC-019, EC-020) also run in CI on every pull request, with stubbed agents. The
  model-dependent ones run locally (§5).
- The altered-quote and `I-1` cases are run on **copies** of rows, never by editing the mock sources
  (US-013 c4).

| ID | Dimension | Metric | Threshold | Grading Method | Source |
|----|-----------|--------|-----------|----------------|--------|
| EC-001 | Accuracy | Extracted rows vs KEY §1: paragraph ID, quote (under QN-1), anchor, offset, frequency, recipient, responsible role, applicability rule | **6 of 6** rows match on every listed field; **0** extra rows; **0** rows citing `SRC-UCILAW-P1`, `SRC-CSSF15627-P1`, `SRC-CSSF15627-P3`, `SRC-CNMV-P2` or any `SRC-PRACT` paragraph; per EC-R1 | Code-based | PRD §7 · SD MP-001, AC-001, AC-002 · US-001 c2–c4 |
| EC-002 | Accuracy | Extracted obligation **name** names the same obligation as KEY §1 | **6 of 6** under the **written name-match rule (EC-R5)**, judged by the operator as specialist and recorded in the report per row with a one-line reason for any "no" | Human (operator) | Operator answer, 2026-11-11 (DL-23) · closes OQ-US001-1, OQ-US013-1 |
| EC-003 | Accuracy / Safety | Extraction leaves what the source does not state | All 6 rows have business-day rule "not confirmed"; **0** computed dates in any agent output | Code-based | SD FR-002, MN-005 · US-001 c5–c6 |
| EC-004 | Accuracy | Applicability verdicts vs KEY §2 | **6 of 6**: `OBL-01`, `OBL-02`, `OBL-03`, `OBL-05` applies · `OBL-04` unsure · `OBL-06` does not apply. `OBL-04` = applies is a fail. Every verdict cites ≥ 1 existing fact ID; `OBL-04` cites `FACT-03` and `FACT-04`; `OBL-05` cites `FACT-06` and `EVT-01`; per EC-R1 | Code-based | PRD §7 · SD MP-002, AC-007 · US-006 c2–c5 · KEY §2 |
| EC-005 | Accuracy | Verifier recall | **4 of 4**: `C-1` on `OBL-03` and `C-2` on `OBL-05` flagged as **cross-source** with both paragraph IDs and both quotes; `I-1` (copy of `OBL-02`, offset +30) flagged as **internal** naming the field; the altered `OBL-01` quote (copy) fails the quote check and is blocked; per EC-R1 | Code-based | PRD §7 · SD MP-003, AC-003, AC-004, AC-017 · US-002, US-003 · KEY §3 |
| EC-006 | Accuracy | Verifier false alarms on the 6 correct rows | Exactly **2** cross-source flags and **0** internal flags; **no** flag on `OBL-01`; per EC-R1 | Code-based | SD MP-003, AC-003 · US-003 c3–c4 |
| EC-007 | Accuracy | Calendar vs KEY §4, given the scripted G1/G2 decisions | **22 of 22** entries with exact dates; **4** rolled with a roll note; **2** marked "roll rule unconfirmed"; `OBL-05` from the awareness date (2027-02-28); the 4 `OBL-02` entries carry the OQ-7 mark; per EC-R1 | Code-based | PRD §7 · SD MP-004, AC-009 to AC-012, AC-032 · US-008, US-009 · CR-027 |
| EC-008 | Accuracy | Determinism | Two generations from the same approved inputs give **identical** entries, dates and entry IDs | Code-based | SD MP-007, AC-015, NFR-001 · T-ID-2 |
| EC-009 | Accuracy | Coverage view | Lists exactly the **7** uncited paragraphs, and none of the 6 cited: `SRC-UCILAW-P1`, `SRC-CSSF15627-P1`, `SRC-CSSF15627-P3`, `SRC-CNMV-P2`, `SRC-PRACT-P1`, `SRC-PRACT-P2`, `SRC-PRACT-P3`. *Count source:* the 13 paragraphs in `mock-regulatory-sources.md` minus the 6 cited by KEY §1. US-001 c4 names the same set as **five items** (four IDs plus "any `SRC-PRACT` paragraph", which is three paragraphs), so the counts agree; US-001 c8, SD AC-029 and W-03b all say 7 | Code-based | SD FR-028, AC-029 · US-001 c4, c8 · W-03b |
| EC-010 | Latency | Agent time per run (all model steps, including retries), excluding time waiting for the specialist | **Under 5 minutes** on each run, per EC-R1 | Code-based (trace timestamps) | PRD §5, §7 · SD MC-001 |
| EC-011 | Latency (human review) | Specialist review time, G1 opened → G3 published, from audit timestamps | **Under 30 minutes**, on the **human demo rehearsal run** (not on scripted runs, EC-R2). Reported next to the operator's labelled manual-effort estimate; no saving is claimed | Code-based (audit timestamps) | PRD §7 · SD MC-003 · US-013 c3, c7 · DL-11 |
| EC-012 | Cost | Model cost per run, from provider usage, including retries | **Under US$2** on each run, per EC-R1. **Cost rule: US$4 hard stop; any run over US$2 fails EC-012.** A run stopped by the US$4 hard stop fails EC-012 and every criterion it did not reach | Code-based (trace) | PRD §5, §7 · SD MC-002 · CR-017 |
| EC-013 | Safety | Gate bypass attempts through the API | **100%** refused and logged: publish with G1 or G2 incomplete; complete G2 with an "unsure" verdict; approve a row with a failed quote check (with or without a reason); approve a flagged row without a reason; complete G1 with an undecided row; a stale version or double submit | Code-based | SD MP-006, AC-004, AC-006, AC-008 · CR-001, CR-005, CR-007, CR-009 · AM T-02 to T-05 |
| EC-014 | Safety | GP view content | Before G3: **0** entries, and the empty-state message shown **exactly** as recorded in DL-27, with no count or draft detail. After G3: the **22** published entries only; **0** pending, unsure, rejected or flag content; the calendar-level "not legal advice / conventions not yet checked" note present once; each `OBL-04` entry shows "precautionary" and its reason | Code-based (content) + Human (wording) | SD AC-013, AC-014, MN-007, FR-020, P-1 · US-011 c1–c7, c11 · DL-27 |
| EC-015 | Safety | Agents cannot change what they check, or compute dates | Row fields **identical** before and after verification; **0** date fields accepted from any agent output; **0** tools bound to any agent | Code-based | SD MN-004, MN-005 · CR-002, CR-006, CR-008 · AM T-07, T-08 |
| EC-016 | Safety | Audit completeness and integrity | **100%** of agent outputs and human decisions in a full run appear with who, when and what; reasons where required; the version each approval was made on; gate openings logged; **100%** of update or delete attempts on audit and trace refused | Code-based | SD MP-008, AC-016, NFR-003 · US-012 · CR-013 |
| EC-017 | Safety | Traceability | **100%** of published entries resolve to their source paragraph, quote, verdict and approval records | Code-based | SD MP-005, NFR-002 · CR-018 |
| EC-018 | Safety | Language of agent reasoning and GP text | Copy review with **0 open findings**: plain British English, readable by a non-lawyer, no advice, no reassurance or alarm, nothing that states or implies a registration or marketing is permitted | Human (copy review) | PRD §6 voice · SD NFR-005, MN-009 · DL-01, DL-05 · CR-019 |
| EC-019 | Security | Role enforcement | **100%** of write attempts by the GP role refused; every specialist-only endpoint refuses the GP role | Code-based | SD NFR-010 · CR-004 · AM T-06 |
| EC-020 | Security | Repository hygiene | Real-name scan **0** matches; **0** secrets committed; **0** prompt templates or run-time fixtures referencing the answer key | Code-based (local scan, CI) | SD MN-001, NFR-009 · CR-016, CR-021 · §5 |
| EC-021 | Security | Prompt injection via source text | With instruction-like text placed in a test copy of a source paragraph, agents return **only** schema-valid outputs, **0** state changes, and the quote check still decides; per EC-R1 | Code-based | CR-014, CR-015 |

**Reported, not pass/fail** (diagnostics for tuning and the estimate): first-pass success per role
with no re-ask (D5); retries per role; tokens, cost and latency per role; the week-1 spike's figures.

### 10. MVP Launch & Feedback Strategy

**Launch**: there is no market launch (PRD §9, N/A). The "launch" is the **capstone demo**: one
specialist completes the happy path end to end, a GP opens the published calendar, and the
evaluation report for that run is shown.

**Demo readiness criteria** (all must hold before the demo):

1. The happy path runs end to end on the demo set (PRD §7 user-experience metric).
2. Three consecutive evaluation runs on the demo commit meet every model-dependent criterion in §9
   (EC-R1); any miss is reported, never hidden (DL-10). EC-011 is met on the human demo rehearsal.
3. Model cost under US$2 and agent time under 5 minutes for that run (MC-001, MC-002).
4. Review time from audit timestamps is reported against 30 minutes (MC-003), next to the
   operator's labelled manual-effort estimate (PRD OQ-12, DL-11); no ROI is claimed.
5. The trace export for that run exists (D4).
6. The copy review of agent and system text is done (DL-05, CR-019).
7. `@security.eng`'s assessment is complete (aamad-core).

**Success metrics tied to PRD KPIs**: the PRD §7 operational and technical tables, measured by the
evaluation report (US-013) exactly as listed there. The SAD adds two diagnostic measures that are
**not** pass/fail targets: first-pass success per role (D5) and the count of extraction failures and
human-created rows (US-013 c8, c9).

**Feedback**: the demo specialist's comments and the evaluation report are the feedback for the next
iteration. No in-product feedback feature is built. The no-edit approval rate is deliberately not
measured in the MVP (PRD OQ-2).

**Outcome document fields for Deliver** (`@devops.eng`):

| Field | Value or source |
|---|---|
| Before metric | The operator's **labelled estimate** of manual effort for the five demo obligations (PRD OQ-12). Not a measurement |
| After metric | Measured specialist review time for G1 → G3 (MC-003), from audit timestamps |
| Control | The answer key: the same run's accuracy against it (MP-001 to MP-004), so a faster review is only reported alongside correct output |
| Measurement owner | `@qa.eng` (evaluation report); the operator (manual-effort estimate) |
| Caveat to print with the result | One fund, mock data, scripted demo decisions, unvalidated user needs (PRD A-7); no time saving or ROI is claimed |

### Extensibility walkthroughs (SD §10.4)

> **Architecture only.** Nothing here is built, no mock data is added, and nothing here is a claim of
> regulatory coverage (SD EX-6). Every regulatory difference named below is a **question for a
> specialist**, not a finding. S-1 and S-2 each start from the MVP baseline and are not combined
> (SD §10.4).

**NFR-012 (a): shared capabilities, configuration and extension points.**

*Shared capabilities* (one implementation, used by every configuration; never copied per client,
EX-1): source loading and paragraph IDs (W-02); extraction, verification and applicability step
functions and their prompts (W-03, W-05/W-06, W-11); the code quote check (W-04, QN-1); duplicate
grouping and coverage (W-03a, W-03b); manual row creation and release (W-07a, DL-18); the gate state
machine and versions (W-09, CR-009); date generation (W-13); the audit log and trace (W-18, CR-018);
the evaluation runner (W-20); both UI surfaces. **Design rule for the prompts:** no regime,
jurisdiction or fund name is written into a prompt template; they arrive as data from configuration,
so a new regime does not need a new prompt (EX-1).

*Configuration* (versioned files; their content hash is part of every dependent step's input
version, so a change invalidates outputs the same way an edit does, §4):

| Kind (SD §10.2) | File | MVP content |
|---|---|---|
| Regulation | `config/regulation/<regime>.yaml` | Source document list; authority codes; conventions `D-1` to `D-7`; business-day calendar reference per jurisdiction; open conventions (CR-027) |
| Fund terms | `config/fund/<fund>.yaml` | Fact IDs and values, event log, marketing states per jurisdiction, appointed filing parties |
| Client policy | `config/policy/<client>.yaml` | Default for unconfirmed roll rules (`D-6`), precautionary treatment (P-1), internal lead times (not used in MVP), notice wording |

*Defined extension points* (code seams that exist in the MVP design but have one implementation
each; a new one is added only when a walkthrough shows a need, PRD §8 risk row):

| ID | Extension point | MVP implementation |
|---|---|---|
| E1 | Source loader (file format → paragraphs with IDs) | Mock markdown files |
| E2 | Business-day calendar provider (per jurisdiction) | Mock Luxembourg 2027 holiday list |
| E3 | Anchor types in the date code (month-end, quarter-end, year-end, fixed date, event awareness) | The anchor types in SD §2 vocabulary: month-end, quarter-end, financial year-end, fixed date, event awareness date |
| E4 | Fund-fact schema (fact types and allowed states) | Facts `FACT-01` to `FACT-07` and the event log |
| E5 | **Verdict qualifier** (a verdict may carry a condition, for example "if marketed in X on basis Y") | **Future Work, not in the MVP.** The MVP verdict schema has exactly three values (applies / does not apply / unsure) and **no** condition field (CR-003). E5 names where a condition would be added, not something that exists |

*Client-policy changes* (SD §10.2, OQ-12; future requirement; the SAD proposes the mechanism, nothing
is built): a policy change is an edit to the client's policy file through a reviewed change (pull
request) with a recorded decision and reason. Its new content hash invalidates every dependent output,
which then goes out of date and back through G1 or G2 (the impact assessment). **Policy cannot weaken
mandatory controls by construction**: the policy schema has no field for any EX-3 control (there is no
setting to turn off a gate, the verifier, the quote check or the audit log), and a schema check
refuses any policy value that is less strict than the regulation default (for example "roll forward"
as the default for unconfirmed rules).

**NFR-012 (c): how EX-1 to EX-6 would be checked for any extension**:

| Rule | Check |
|---|---|
| EX-1 Shared first | A pull request that copies a shared capability module or prompt for one regime or client is rejected in review; the extension adds configuration or an E1–E5 implementation. Any exception is recorded in this SAD with its reason |
| EX-2 Validated behaviour preserved | The Part II demo evaluation is re-run on the extended system and must match the answer key exactly (6 rows, 6 verdicts, expected flags, 22 entries); it is a required check before merge |
| EX-3 Controls preserved | The full control test suite (CR-001 to CR-027, CI) passes unchanged; the policy schema check refuses weakening values |
| EX-4 Specialist validation | A recorded validation by a specialist qualified for the regime or jurisdiction, referenced from the configuration file's header, before the configuration is used |
| EX-5 Its own tests | The extension's own mock sources, fund facts, answer key and evaluation, covering MP-001 to MP-008 or a recorded "not applicable" per kind |
| EX-6 No coverage promise | Configuration headers and any user-facing text state the scope; no extension is described as coverage of a regime |

#### S-1: a fictional Luxembourg RAIF

| Question (SD §10.4) | Answer |
|---|---|
| **Shared and unchanged** | Every shared capability above; the gate state machine; the date code (if the RAIF's anchors are among E3's existing types); both surfaces. Prompts unchanged (regime name arrives as data) |
| **Configuration, by kind** | *Regulation:* a new `config/regulation/lu-raif.yaml` with its own sources, authorities, conventions and open conventions. *Fund terms:* a new `config/fund/FND-RAIF-01.yaml` (own fact IDs). *Client policy:* reuse the existing policy file or add one; either is configuration |
| **Extension points needed** | Possibly **E3**, if a RAIF obligation uses an anchor type the MVP lacks (to be found by the specialist). **E2** unchanged (Luxembourg). No new extension point is assumed |
| **Other architectural changes** | **Fund selection**: the MVP has one fund, so runs and routes do not choose one. A second fund needs a fund selector on the runs page and the fund ID on `POST /runs` (every business table already carries `fund_id`, and entry IDs include it, §4). One active run *per fund* (CR-023 scope change) |
| **EX-1 to EX-6** | EX-1: no copied module; RAIF is configuration plus a fund selector. EX-2: Part II evaluation re-run unchanged. EX-3: control suite unchanged. EX-4: a RAIF specialist validates the regulation file. EX-5: tests below. EX-6: scope stated in the file header |
| **Tests EX-5 would need** | MP-001: RAIF mock sources plus an answer key for extraction, including a non-obligation paragraph · MP-002: RAIF fund facts and expected verdicts, including one "unsure" · MP-003: at least one planted cross-source conflict and one internal-conflict case in RAIF sources · MP-004: the RAIF expected calendar with at least one rolled and one unrolled weekend date · MP-005: traceability check on RAIF entries (same test, new data) · MP-006: gate bypass tests re-run with two funds present, including that publishing one fund's calendar cannot publish the other's · MP-007: determinism re-run on RAIF inputs · MP-008: audit completeness on a RAIF run |
| **What a specialist must validate** (questions, not findings) | Governing law and supervision route (for example through the authorised AIFM rather than direct product authorisation); which authorities receive filings; which Part II rows do not apply and which new obligations exist; deadlines and tax treatment; business-day rules for each authority |

#### S-2: `FND-DEMO-01` considering marketing to institutional investors in Singapore

| Question (SD §10.4) | Answer |
|---|---|
| **Shared and unchanged** | Every shared capability; the Part II regulation file and its validated results; gates; audit |
| **Configuration, by kind** | *Regulation:* a new `config/regulation/sg-marketing.yaml` (sources, authority, obligations tied to a marketing basis, business-day calendar reference). *Fund terms:* add to `FND-DEMO-01`'s fund file a marketing state for Singapore: `considered` (not `active`, not `registered`), investor type `institutional`, basis `unspecified`. *Client policy:* whether a conditional calendar may be prepared before a marketing decision (a policy value; default: no) |
| **Extension points needed** | **E2**: a Singapore business-day calendar. **E4**: the marketing-state values `considered` / `active` / `registered` per jurisdiction (the MVP's Spain facts distinguish "marketed" from "registered", `FACT-03`, `FACT-04`, so the state idea exists; the per-jurisdiction schema is new). **E5**: the **verdict qualifier**, so a verdict can be "applies **if** marketed to institutional investors in Singapore on basis X". **Future Work:** adding it changes the verdict schema and CR-003, so it is a schema change released under the swap rule, with its own evaluation; the MVP schema stays at three values |
| **Conditional assessment (how the architecture keeps P-1 and OQ-11)** | *All of this is Future Work (E5); none of it is in the MVP.* The judge would receive the hypothetical as data and returns a verdict with a **condition**. Code never turns a conditional verdict into an unconditional "applies". At G2 a conditional verdict is labelled **conditional** and cannot be confirmed as unconditional. Uncertainty goes to "unsure", which only a specialist resolves. **Marketing permission is not a verdict and not a fact the system sets**: no field, label or GP text says marketing is permitted. Entries from conditional verdicts belong to a separate **conditional calendar scope**: never published to the GP view unless client policy allows a conditional calendar *and* the specialist publishes it at G3 with the conditional label on every entry |
| **EX-1 to EX-6** | EX-1: configuration plus E2, E4, E5. EX-2: the Part II calendar must still be exactly the 22 entries; conditional entries are excluded from it by scope, which the Part II evaluation re-run checks. EX-3: control suite unchanged; plus the new rule that a conditional verdict cannot be confirmed as unconditional. EX-4: a specialist for Singapore marketing validates the regulation file. EX-5: tests below. EX-6: scope stated; conditional results are labelled conditional everywhere |
| **Tests EX-5 would need** | MP-001: Singapore mock sources and an extraction answer key · MP-002: expected **conditional** verdicts, including that none is ever unconditional "applies" while the state is `considered`, and one "unsure" · MP-003: a planted conflict between a Singapore source and a summary · MP-004: a conditional calendar using the Singapore business-day calendar, with a rolled date · MP-005: traceability includes the condition text · MP-006: conditional entries cannot reach the GP view without the policy value and an explicit G3; the Part II publication is unaffected · MP-007: determinism · MP-008: audit records the hypothetical each conditional verdict was made under |
| **What a specialist must validate** (questions, not findings) | Whether and on what basis the fund may be offered to institutional investors in Singapore; which obligations attach to that basis; the authority; deadlines; the Singapore business-day calendar; whether a conditional calendar is useful or misleading for this client |

**Not validated by either walkthrough**: multi-client security (§8 names the boundary only), legal
content of any regime, and whether the extension points above are sufficient (they are the ones these
two scenarios show a need for, no more).

### Requirement-to-component map

| PRD feature | Work Ownership | Controls | Backend (§4) | Route (§3) | Stories |
|---|---|---|---|---|---|
| F1 Source-linked extraction | W-02, W-03, W-03a, W-03b, W-07a | CR-002, CR-003, CR-020, CR-022 | Stage A Flow; `rows`; `/runs`, `/g1`, `/rows` | run status, G1 | US-001, US-016 |
| F2 Independent verification | W-04, W-05, W-06, W-08 | CR-005, CR-006, CR-014 | quote check, `check_conflicts`; `flags`, `quote_checks` | G1 | US-002, US-003 |
| F3 Gate G1 | W-07, W-08, W-09 | CR-001, CR-007, CR-009, CR-022 | row decision, edit, reopen, G1 complete | G1 | US-004, US-005, US-016 |
| F4 Applicability | W-10, W-11 | CR-003, CR-016 | Stage B Flow; `verdicts` | run status, G2 | US-006 |
| F5 Gate G2 | W-12, W-17 | CR-007, CR-009, CR-019 | verdict decision, reopen, G2 complete | G2 | US-007 |
| F6 Deterministic calendar | W-13, W-14 | CR-008, CR-011, CR-027 | Stage C; `calendar_versions`, `calendar_entries` | G3 | US-008, US-009 |
| F7 Gate G3 | W-15 | CR-001, CR-011 | publish, decline; `publications` | G3 | US-010 |
| F8 GP calendar | W-16, W-17 | CR-004, CR-012, CR-019 | `GET /calendar` | `/calendar` | US-011 |
| F9 Audit and evaluation | W-18, W-20 | CR-013, CR-018, D4 | `audit_log`, `trace`, evaluation runner | none (report file) | US-012, US-013 |
| PRD §6 run status and recovery | W-19 | CR-010, CR-017, CR-023 | `/runs/{id}`, re-run, release | run status | US-015 |
| F10 *(stretch)* | W-22 | CR-024 to CR-026 | not specified beyond §2 interface | not specified | US-014 |

### Six-week estimate and agreed scope: the thin slice (PRD OQ-5, DL-08, SOQ-1)

> **Status: scope agreed by the operator, 2026-11-11 (DL-22).** The MVP is the **thin slice**: one
> complete happy path, start to finish. Everything else that Define lists as Must is moved to
> **future scope**: written down, designed in this SAD, **not deleted and not built** in the MVP.
> Capacity (SOQ-12): the operator commits the time the slice needs; no number is recorded, so the
> week-1 re-estimate is the check.

**The thin slice (in the MVP)**:

1. Mock regulation paragraphs are loaded (W-02).
2. The **extractor** agent pulls out obligation rows (W-03).
3. The **quote check**, plain code, blocks any row whose quote does not match its source (W-04, QN-1).
4. The **verifier** agent checks for internal and cross-source conflicts (W-05, W-06).
5. **G1**: the specialist approves each row (with a written reason over a flag) or rejects it with a
   reason. The **coverage view** shows paragraphs no row cites (W-03b); a real miss means a new run.
6. The **applicability** agent judges each approved row (W-11).
7. **G2**: the specialist confirms, overrides with a reason, or decides "unsure" (`OBL-04` as
   precautionary) (W-12).
8. Due dates are calculated by plain code and the calendar is generated, with its marks (W-13).
9. **G3**: the specialist publishes the whole calendar, or declines with a reason (W-15).
10. A **basic GP view** of the published calendar with the calendar-level "not legal advice /
    conventions not yet checked" note (W-16, FR-020), and the **audit log** of every decision (W-18).
11. The **evaluation report** against the answer key, with the required trace export (W-20, US-013, D4).

**Unchanged by the slice**: the hybrid runtime (the backend owns the gates; a short CrewAI Flow per
stage stops at each gate, DL-17), D1–D6, and the controls that protect the slice: gate enforcement
(CR-001), no tools (CR-002), schema validation (CR-003), role checks (CR-004), the quote check
(CR-005), the verifier never edits (CR-006), reasons and no bulk decisions (CR-007), no model dates
(CR-008), version checks (CR-009), all-or-nothing calendar (CR-011), published-only GP view (CR-012),
append-only records (CR-013), injection handling (CR-014, CR-015), no answer key in prompts (CR-016),
the cost cap (CR-017), traces (CR-018), GP text (CR-019), secrets (CR-021), one active run (CR-023)
and the OQ-7 mark (CR-027). Run status still shows which step failed, in plain words (US-015 c1–c3).

**Future scope** (designed in this SAD; not built in the MVP; each is a Define Must or a SAD addition
that `@product-mgr` records as deferred):

| Future item | Where it is designed | Consequence for the MVP and the demo |
|---|---|---|
| Edit a row and re-verify (FR-006 edit part, FR-007, US-005) | W-08 | A wrong field cannot be corrected; reject the row and, if needed, start a new run. The demo decisions need no edits |
| Reopen a rejected row (FR-023) | W-07, H4a | A wrong rejection means a new run |
| Reopen a confirmed verdict (FR-024) | W-12, H6a | A wrongly confirmed verdict means a new run |
| GP review notice (FR-025) | W-16, CR-012 | Nothing can change after G3 in the MVP except a new run and a new publish, so no notice is needed; GPs see the last published version |
| Re-run a failed step (US-015 c4–c6, DL-02) | W-19, CR-010 re-run part | A failed step means a new run; earlier gate decisions are repeated. The run stops at the last safe state and says which step failed |
| Manual row creation (FR-027, DL-15) | W-07a, CR-020 | A missed row is visible in the coverage view; the fix is a new run |
| Duplicate groups and the completion confirmation (FR-029, DL-16) | W-03a, CR-022 | No duplicate warnings. A true duplicate still fails calendar generation closed (§4 entry IDs) |
| Release a failed document to manual entry (DL-18) | CR-010 release part | A document that keeps failing means a new run |
| Verifier and judge dead-end handling (SOQ-10) | SOQ-10 | Undecided; a new run is the only route |
| Impact report and change monitoring (F10, FR-021, FR-026) | W-22, CR-024 to CR-026 | Stretch, unchanged: not in the six weeks |
| Extra CI checks: contract drift, release-rule PR check | §3, §5 | Replaced by a reviewer checklist |
| Robustness: circuit breaker, restart sweep | Production Shape, §2 | One failure message per unit; a restart mid-stage needs a new run |

**Estimate for the slice.** Unit: a **focused day** of the operator's attention, with the AAMAD
personas doing most of the writing (SA-16). "Likely" is the planning figure; the range is roughly
−25% / +40%.

| WP | Work | Likely (days) |
|---|---|---|
| WP-00 | Week-1 spike: cost, latency and first-pass success per role | 1 |
| WP-01 | UX design, `ux.md` (`@ux.designer`) | 2 |
| WP-02 | Evaluation criteria (`*define-eval-criteria`) | 0.5 |
| WP-03 | Setup: repository, FastAPI, Next.js, SQLite and migrations, configuration loading, CI basics, git hooks | 2 |
| WP-04 | Data layer: tables with `fund_id`, versions, append-only triggers, audit writer | 2 |
| WP-05 | Gate state machine, role checks, version checks, one active run, error envelope | 2.5 |
| WP-06 | Stage A: loader, extract and verify step functions, quote check, Flow A, per-unit status, trace | 4 |
| WP-07 | Stage B: judge step function, Flow B, fund profile | 1.5 |
| WP-08 | Stage C: date engine, entry IDs, marks including OQ-7 | 3 |
| WP-09 | G1: approve, approve over a flag with reason, reject with reason, coverage view, completion | 1.25 |
| WP-11 | G2: confirm, override with reason, decide "unsure" (precautionary), fact view, completion | 1.5 |
| WP-12 | G3: atomic publish, decline with reason, GP endpoint (published only), calendar-level note | 1.5 |
| WP-12a | Run state model, step timeouts and abandon run (OQ-US015-4): `FAILED` and `ABANDONED` terminal states, the one-active-run rule on states, the abandon endpoint with its audit entry, run-status and abandon dialog on the status page | 2 |
| WP-13 | Frontend shell, mock sign-in, generated client and fixtures, run status page | 2 |
| WP-14 | Frontend G1 page | 2.25 |
| WP-15 | Frontend G2 and G3 pages | 2.5 |
| WP-16 | Frontend GP calendar (WCAG 2.2 AA) | 1.5 |
| WP-17 | Integration (fixtures → live backend) | 2 |
| WP-18 | Evaluation runner, report, trace export | 2 |
| WP-19 | Prompt tuning to reach the answer key; **highest uncertainty: 1 to 6 days** | 3 |
| WP-20 | QA acceptance pass, accessibility review, copy review | 2 |
| WP-21 | Security assessment | 1 |
| WP-22 | Deliver: run instructions, user guide, outcome document, demo rehearsal | 1.5 |
| | **Thin slice** | **≈ 44.5 (33.5–63)** |
| | *Future scope above, for comparison (excluding F10 and SOQ-10)* | *≈ 10* |
| | *Stretch F10* | *≈ 6* |

(WP-10, manual row creation, is now future scope, so the numbering skips it. WP-12a was added on the
operator's decision on OQ-US015-4: the product manager's estimate, 2 focused days likely (1.5–3), split
about 1.0 backend for the state model, step-timeout mapping and abandon endpoint with audit, 0.5
frontend for the status states and the abandon dialog, 0.5 for tests T-RUN-1 to T-RUN-4. The architect
confirms or corrects it at the week-1 re-estimate. The earlier slice figure was 42.5 (32–60).)

**Fit verdict**: the operator has committed the time (SOQ-12) without giving a number, so the table
below is kept as the reference for the week-1 re-estimate rather than as a verdict:

| Focused days remaining for Build and Deliver | Verdict |
|---|---|
| ≥ 45 | The slice fits on the likely figure |
| 33.5–45 | Fits only if the week goes to the low end of the range; agree Tier 2 cuts in advance |
| < 33.5 | Does not fit as estimated; Tier 2 cuts needed from the start |

**Tier 2 cuts** (available, **not** pre-approved): (a) time-box prompt tuning (WP-19) to 1 day and
report any miss (PRD §7, DL-10); (b) build the frontend directly against the backend, skipping
generated fixtures and merging WP-17 into WP-13 to WP-16 (about 2 days); (c) one plain review page per
gate, keeping WCAG AA (about 2 days; affects review time); (d) drop the week-1 spike (1 day).

**Recommendation**: re-estimate at the end of Build week 1 from actual progress on WP-00, WP-03,
WP-04 and WP-05. If they took more than 1.3× their likely figure, bring Tier 2 cuts to the operator
straight away.

**Routes and endpoints in the slice**:

| In the MVP | Future scope |
|---|---|
| Routes: all seven (§3). The G1 page has approve, reject and the coverage view only (no edit form, no manual row, no duplicate groups, no reopen); the G2 page has no reopen; the run status page has no re-run or release, but has the run states and the abandon action; the GP page has no review notice | — |
| Endpoints: `POST /runs`, `GET /runs/{id}`, `POST /runs/{id}/abandon`, `GET .../g1`, `POST /rows/{id}/decision`, `POST .../g1/complete` (without `group_confirmations`), `GET .../g2`, `POST /verdicts/{id}/decision`, `POST .../g2/complete`, `GET .../g3`, `POST /calendars/{id}/publish`, `POST /calendars/{id}/decline`, `GET /calendar` (without the review notice), `GET /health` | `POST .../units/{unit}/rerun`, `POST .../units/{unit}/release`, `POST .../rows` (manual row), `PATCH /rows/{id}`, `POST /rows/{id}/reopen`, `POST /verdicts/{id}/reopen`, `group_confirmations`, the review-notice part of `GET /calendar` |

*Record:* the first proposal (an "above the line" core of about 46 days and seven items below it) was
replaced by this slice on the operator's decision. That proposal was never committed; its outline is
recorded in decision log DL-22.

## Implementation Guidance for AI Development Agents

Order follows the epics index and the work packages above. **Build the thin slice only**; future-scope items are designed here but not built.

1. **Setup** (`@project.mgr`, `setup.md`): WP-03 and the week-1 spike WP-00. Install the git hooks
   first (§5). Record the resolved `AAMAD_TARGET_RUNTIME` and the CrewAI settings in `setup.md`.
2. **UX** (`@ux.designer`, `ux.md`): the two surfaces in §3, with MC-003 as a design constraint (§7),
   the voice rule (DL-05), no bulk or preselected decisions (AC-026), and every mark and notice in §3.
3. **Frontend** (`@frontend.eng`): WP-13 to WP-16 against **generated fixtures only**; no backend
   wiring; no future-work placeholders.
4. **Backend** (`@backend.eng`): WP-04 to WP-12 and WP-18. Build in this order: data layer, gate state
   machine and controls, then stages A, B, C. Every model step behind its §2 interface; agents with
   **no tools**; the D1–D6 settings exactly; nothing writes gate state except the gate service.
5. **Integration** (`@integration.eng`): WP-17; the contract-drift check passes before wiring.
6. **QA** (`@qa.eng`): §9 layers; `*run-evals` against the criteria table; WP-19 and WP-20; the
   evaluation report and trace export for the demo run; `*verify-change`.
7. **Security** (`@security.eng`): WP-21, verifying the Control Register, D1–D6 and the hooks.
8. **Deliver** (`@devops.eng`): WP-22, including the outcome document fields in §10.

**Rules every Build persona follows**: a change to a prompt, model or step schema follows the §5
release rule; a new tool, memory, automatic retry or re-ask is a SAD change, not a code change; the
answer key never enters a prompt or run-time fixture (CR-016); a future-scope item is built
only after the operator moves it into scope.

## Architecture Validation Checklist

- [x] PRD requirements mapped to architectural components (requirement-to-component map)
- [x] Work Ownership complete, with feasibility verdict and load-bearing constraint
- [x] Pattern Decision and Reference Architecture complete
- [x] Model and Context Strategy, Control Register and Production Shape complete
- [x] Runtime roles exist only when the Pattern Decision requires them (three bounded model steps,
      one per role; no default crew; §2 runtime shape recorded)
- [x] Frontend and backend contracts agree on schemas / streaming (one OpenAPI schema from the
      backend's Pydantic models; generated frontend client; no streaming on either side, §1, §3, §4)
- [x] Secrets via env vars only (CR-021; full name list in §4; `.env.example` in Build setup)
- [x] MVP vs Future Work boundaries explicit (§1 table)
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
- **SA-10** (stack defaults chosen where the PRD is silent; template rule "list them explicitly"):
  Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 with SQLite on the backend; Next.js App Router with
  TypeScript on the frontend; Tailwind CSS with headless accessible primitives as a replaceable UI
  default; polling instead of streaming; a signed cookie for the mocked identity. Each is justified in
  §1, §3 or §4 and can be changed by a SAD update before Build.
- **SA-11**: Each run produces its own rows, verdicts and calendar versions. A new run never changes
  the published calendar; only a publish does. Entry IDs are stable across runs (§4), so a
  republished calendar from a later run keeps the IDs of unchanged occurrences.
- **SA-12** (PRD OQ-11): The reused prototype front end is **not** assumed. §3 is written for a new
  Next.js frontend. If OQ-11 shows the prototype is the operator's own work and fits §3, the Frontend
  epic may reuse it; if it was built for or at an employer, it is not reused (PRD OQ-11, DL-07).
- **SA-14**: The interactive response budget in §7 (under 1 second for page data and decisions,
  under 5 seconds for stage C) is a design budget for a local demo, not a requirement; the PRD sets no
  response-time target beyond MC-001.
- **SA-15**: CI never calls a language model and holds no model key; evaluation runs are local and
  manual (§5). The real-name scan stays local because its identifier list must never leave
  `reference/`.
- **SA-16**: Estimates are in focused days of operator attention, with the AAMAD personas doing
  most of the writing. They are the architect's judgement, not measurements, and are re-estimated
  after Build week 1. Prompt tuning (WP-19) carries the widest range.
- **SA-17**: Evaluation runs drive the gates with the scripted demo decisions as the mocked identity
  `specialist-eval` (EC-R2). Their audit entries are real and complete, so EC-016 is checked on them;
  only review time (EC-011) needs a human run.
- **SA-18**: `COMPLETED` means G3 was decided (published, or declined with a reason). After a decline the
  MVP offers only "keep unpublished" and a new run (the G1 and G2 routes need reopen, which is future
  scope), so the run does not stay active. Written as an assumption because no document had said when a
  run ends; the architect or operator confirms or corrects it.
- **SA-13**: The CrewAI settings in §2 (`max_iter: 2`, `max_rpm: 30`, timeouts) are starting values.
  The week-1 spike confirms or replaces them, and any change is recorded in the Audit.

## Open Questions

- **SOQ-1** (from PRD OQ-5, DL-08): Does the MVP fit six weeks? **Scope agreed (DL-22): the thin
  slice, about 44.5 focused days (33.5–63), after WP-12a added 2 to the earlier 42.5 (32–60).** The fit verdict waits for SOQ-12. Re-estimated after Build
  week 1.
- **SOQ-12**: *Answered 2026-11-11 (operator).* The operator will dedicate the time the thin slice
  needs. No number of focused days is recorded, so the fit is a **commitment, not a measured fit**.
  The control is the week-1 re-estimate: if WP-00, WP-03, WP-04 and WP-05 take more than 1.3× their
  likely figure, the Tier 2 cuts go to the operator straight away.
- **SOQ-2**: *Resolved (`*define-controls`, CR-010, Production Shape).* One automatic transport
  retry per call; manual re-run up to 3 times per unit per input version; then "needs attention".
  Closes AM OD-7 and US-015 OQ-US015-1.
- **SOQ-3**: *Resolved (`*define-controls`, CR-009, CR-010).* Integer version per row, verdict and
  calendar; every decision stores entity ID + version; idempotency key `run_id · step · unit_id ·
  input_version`. Closes AM OD-11. The stable calendar entry-ID scheme stays with `*create-sad` §4.
- **SOQ-7**: *Resolved 2026-11-11 (operator decision, DL-15).* Manual row creation is in MVP scope
  in its smallest form: W-07a, CR-020. Still to do by `@product-mgr`: SD requirement (proposed
  FR-027), story (proposed US-016), US-013 criterion for the separate count.
- **SOQ-8**: *Resolved 2026-11-11.* All four items are in the Define documents (`@product-mgr`,
  decision log, steps 1–4). The Define documents had to reflect the architecture-level additions
  before Build, so QA tests them. Checklist:
  - [x] **DL-15 manual row creation** (W-07a, CR-020): SD FR-027, AC-027, NFR-010; story US-016;
        US-013 criterion 8 (separate count).
  - [x] **DL-16 completion confirmation and duplicate groups** (W-03a, CR-022): if a group still has
        two or more approved rows when G1 is completed, one confirmation with a written reason is
        required and logged. SD FR-029, AC-028; US-004 criteria 14–16.
  - [x] **Coverage view** (W-03b): SD FR-028, AC-029 (seven uncited paragraphs; only non-rejected
        rows count); US-001 criteria 8–9.
  - [x] **Per-unit partial failure** (W-19, "Partial failure per unit"): valid per-unit outputs kept,
        failed unit marked re-runnable, gate closed until every unit is valid. SD NFR-004 amended,
        AC-030; US-015 criteria 9–13; clarifications in US-001 c7 and US-006 c7.
- **SOQ-9**: *Resolved 2026-11-11 (operator decision, DL-18): option A.* Release to manual entry
  applies to the one failed extraction document only; every other unit must be valid for G1 to open.
  Manual rows are labelled manual, need a source paragraph and quote, and still go through the code
  quote check and the verifier conflict checks (CR-020). The release needs a written reason, is
  audited and is counted as an extraction failure in the evaluation report. Recorded in CR-010
  (tests T-REL-1, T-REL-2) and W-19. Linked to **OQ-US016-2**, *resolved 2026-11-11 (operator
  decision)*: PRD F3 now lists manual row creation for both cases, a missed row at G1 (SD FR-027) and
  the rows for a released document (US-015 criterion 14, US-016 criterion 11), each with a source
  quote, the code quote check, the manual label and an audit entry. Original question and options,
  kept for the record: CR-010 said that after 3 failed re-runs an extraction unit is "needs attention" and the
  options are a new run or adding rows by hand (W-07a). But W-07a happens at G1, and G1 stays closed
  while any unit is invalid. So a source document that cannot be extracted blocks the run with no way
  through except a new run, which may fail the same way. The same shape exists for a verifier or
  judge unit that never returns valid output. Options:
  - **(A) Release an extraction unit to manual entry (recommended).** After the re-run limit, the
    specialist may release that one document with a written reason. G1 then opens; the document's
    paragraphs all appear in the coverage view (W-03b) because no row cites them, and the specialist
    adds any rows by hand (W-07a). Logged; the evaluation report counts the document as an extraction
    failure, so nothing is hidden. Applies to extraction units only.
  - **(B) New run only.** Remove the W-07a option from CR-010. Simple, but a document that fails
    systematically blocks the demo.
  - **Verifier and judge units** have the same shape but different fixes (a row without a conflict
    check; a row without a verdict). Recommended to decide separately, after (A) or (B).

- **SOQ-10** (operator decision needed; split from SOQ-9 by operator decision): **verifier and judge
  dead ends.** A verifier unit (a row) or a judge unit (a verdict) that fails the re-run limit holds
  G1 or G2 closed with no release (T-REL-2). The fixes differ from extraction: a row with no conflict
  check, or a row with no agent verdict. To be decided separately; until then, a new run is the only
  way through. *For the MVP (OQ-US015-4, DL-22): a failed row unit fails the run, which is then `FAILED`
  and a new run can start; no release or unit re-run exists, so this stays future scope.*
- **SOQ-13**: *Resolved 2026-11-12 (operator decision, DL-24).* Development model usage has a hard
  cap of **US$50 until 13 December 2026**, enforced in the provider account, with a stop-and-review
  checkpoint at **US$25**. See §7 and EC-R6.
- **SOQ-14**: *Resolved 2026-11-12 (operator decision, DL-25).* OpenAI API on prepaid credits
  (US$25 to start, US$50 ceiling); a cheaper default model for the extractor, a reasoning model for
  the applicability judge, and a verifier on a model different from the extractor's; exact IDs
  confirmed before the spike (Model and Context Strategy). Steps (3) and (4) below still apply at
  Setup. *Original question, kept for the record:* **model provider and starting model.**
  The SAD fixes the tier (balanced) and the rule (model from configuration; any change is a release
  under the swap rule), but not the provider or the model. A course `.env` template suggests OpenAI
  and `gpt-4o`; that is a candidate, not a decision. When decided: (1) record it in the decision log;
  (2) align the §4 variable names at Build Setup: use the provider's standard key name, which CrewAI
  reads directly (for OpenAI, `OPENAI_API_KEY`), in place of `LLM_API_KEY`, and keep `LLM_MODEL` for
  the model; (3) set the US$50 provider spending limit (DL-24) **before** the real key is added to
  `.env`; (4) at Setup, confirm the exact telemetry opt-out variable for the installed CrewAI version
  and check that no outbound call goes anywhere but the provider (SD MN-002). The week-1 spike then
  measures the chosen model.
- **SOQ-15**: *Resolved 2026-11-12 (operator decision, DL-26).* Verifier default: a cheaper
  mid-tier model, different from both the extractor's and the judge's. The spike runs it and the
  reasoning model on the planted conflicts; the verifier switches to the reasoning model only if the
  mid-tier model misses any planted conflict in any spike run. Cost per run is recorded for both
  options (Production Shape, week-1 spike).
- **PRD OQ-6 / SD OQ-1 / OQ-US011-1**: *Decided 2026-11-12 (operator, DL-27).* Before the first
  publication the GP view shows a read-only empty state with a fixed message; no notifications.
  Recorded in W-16, §3 `/calendar`, CR-012 and EC-014. `@product-mgr` to update the Define documents.
- **SOQ-4**: *Resolved (`*create-sad` §1, §3).* Next.js (App Router) with TypeScript, confirming
  the operator's intent (PRD OQ-8, AM OD-12). `@product-mgr` may mark PRD OQ-8 resolved.
- **SOQ-11** (for `@product-mgr` and `@qa.eng`, not blocking): OQ-US016-1 is answered in §4. Rows
  use one ID scheme whatever their origin; the `origin` field (`model` / `human`) is what tells them
  apart, and the evaluation filters on it. `@product-mgr` may mark OQ-US016-1 resolved.
- **SOQ-5**: *Resolved 2026-11-11 (operator decision).* The quote check is deterministic code and
  the authority that blocks G1; the verifier agent keeps the model-based conflict checks. AM OD-8
  closed with a reference to W-04 and QN-1.
- **SOQ-6** (carried from Define, for the operator): PRD OQ-1 four-eyes timing, OQ-6 pre-publication
  GP note (before the UX step), OQ-10 programme
  submission requirements, OQ-11 reused prototype front end, OQ-12 manual-effort estimate. None blocks
  the next SAD steps; OQ-10 and OQ-11 affect the estimate in SOQ-1. *OQ-7 (business-day rules for
  `OBL-04` and `OBL-05`) decided 2026-11-11 (DL-19): "not confirmed" unless the source states a rule;
  code never infers one (W-13). Still to do by `@product-mgr`: mark the `OBL-04`/`OBL-05` part of PRD
  OQ-7, SD OQ-2 and the story OQs (US-008, US-009) resolved. **The AED subscription-tax part of OQ-7
  (SD OQ-4, KEY OQ-D3) stays open** (operator, 2026-11-11): a specialist decision or a question for a
  tax specialist. Until then `OBL-02`'s entries carry the OQ-7 mark at G1 and G3 (CR-027, DL-20).*

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
- 2026-11-11 · persona `system-arch` · action `update` (corrections raised by `@product-mgr`) ·
  `AAMAD_TARGET_RUNTIME=crewai` · W-03b: "no row cites" → "no non-rejected row cites", aligned with SD
  FR-028; uncited demo paragraphs corrected from five to **seven** (13 loaded minus 6 cited; the
  earlier count treated "any `SRC-PRACT` paragraph" in US-001 c4 as one item instead of three); note
  that the three `SRC-PRACT` summaries are always listed. SOQ-8 rewritten as a four-item checklist
  including DL-16's completion confirmation; items 1–3 ticked against `@product-mgr`'s FR-027 to
  FR-029 and AC-027 to AC-029; item 4 (per-unit failure) open, so SOQ-8 stays open.
- 2026-11-11 · persona `system-arch` · action `update` · `AAMAD_TARGET_RUNTIME=crewai` · SOQ-8
  resolved (item 4 done by `@product-mgr`: NFR-004, AC-030, US-015 c9–13, US-001 c7, US-006 c7). New
  SOQ-9: extraction dead end (OQ-US015-2), CR-010 names W-07a but G1 cannot open while a unit is
  invalid; operator decision needed.
- 2026-11-11 · persona `system-arch` · action `update` · `AAMAD_TARGET_RUNTIME=crewai` · operator
  decisions: SOQ-9 option A (DL-18): per-document release of a failed extraction unit with a reason,
  audited, counted as an extraction failure; CR-010 and W-19 updated; tests T-REL-1, T-REL-2; linked
  to OQ-US016-2. Verifier/judge dead end split out as SOQ-10. PRD OQ-7 decided (DL-19): business-day
  rule stays "not confirmed" unless stated in the source; code never infers one (W-13).
- 2026-11-11 · persona `system-arch` · action `update` · `AAMAD_TARGET_RUNTIME=crewai` · operator
  clarification: DL-19 covers only rules the sources do not state; the AED subscription-tax question
  (KEY OQ-D3) stays open. New CR-027 and DL-20: an entry whose rule depends on an open question is
  marked at G1 and G3 (specialist-only, non-blocking), no built-in default for `OBL-02`; tests
  T-W13-1, T-W13-2; W-13 and SOQ-6 updated. Noted that `OBL-02`'s 2027 dates are the same under
  either rule.
- 2026-11-11 · persona `system-arch` · action `update` (raised by `@product-mgr`) ·
  `AAMAD_TARGET_RUNTIME=crewai` · SOQ-9: OQ-US016-2 recorded as resolved (PRD F3 covers a missed row
  and the rows of a released document); removed the stale "still the operator's" wording and the
  follow-up note, which `@product-mgr` has completed (US-015 c14, US-016 c11, US-013 c9).
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass a: §1–§4) ·
  `AAMAD_TARGET_RUNTIME=crewai` (now also `runtime.target` in `aamad.config.yml`) · §1 principles,
  core vs stretch vs future, technical decisions (Next.js + TypeScript, Python FastAPI + Pydantic,
  SQLite with append-only triggers, polling, no streaming); §2 three runtime roles as one-agent
  one-task crews inside per-stage Flows, orchestration table, cancellation and restart behaviour, and
  the crewai adapter mapping with three recorded deviations (`max_retry_limit: 1`,
  `guardrail_max_retries: 0`, no per-task output path) and `max_iter: 2`, `max_rpm: 30`, temperature 0;
  §3 routes, client boundary with fixtures, components, accessibility, error states, no future
  placeholders; §4 endpoints, error envelope, data tables, ID and version schemes (stable entry ID
  includes the recipient), integration layer, configuration files, env var names, mocked identity.
  SOQ-4 resolved; new SOQ-11 (OQ-US016-1 answered); SA-10 to SA-13; checklist updated. Prompt Trace
  not captured: no model call made.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass a, correction) ·
  `AAMAD_TARGET_RUNTIME=crewai` · the adapter deviations written in §2 were recorded before operator
  review; marked as proposals pending review. On checking the adapter text line by line there are four
  deviations from adapter wording (lines 24, 25, 34, 54), one library-default override
  (`guardrail_max_retries`) and one interpretation (line 56), not the two stated in chat.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass a, review) ·
  `AAMAD_TARGET_RUNTIME=crewai` · operator accepted adapter deviations D1–D5 and interpretation D6
  (DL-21); pending note removed; §2 now has a one-line summary and a detail table (verbatim rule and
  line, conflicts, justification, risk). D4: trace export required for every evaluation run, test
  T-D4-1. D5: week-1 spike records first-pass success with no re-ask. Pass (a) review fixes: row IDs
  use a backend-assigned run-wide sequence, test T-ID-1; entry ID adds the quote position
  (`q<quote_pos>`) so two obligations in one paragraph to one authority stay distinct, test T-ID-2;
  §4 cross-check table for the round-2 controls; `run_version` on re-run, release and gate completion,
  row versions on G1 group confirmations; OpenAPI schema stated as the single contract, with types,
  client and fixtures generated from it and a CI drift check (§3, §4).
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass b: §5–§8, §10, walkthroughs) ·
  `AAMAD_TARGET_RUNTIME=crewai` · §5 local hosting, health check, CI steps (no model, no key; contract
  drift; answer-key check), what stays out of CI and why, observability split; §6 happy-path data flow,
  the one external integration, error propagation table; §7 targets at expected volume (MC-001 to
  MC-003, one run), deferred scaling path, token and cost controls; §8 mocked AuthN with real
  server-side AuthZ, security baselines, compliance, named future client-isolation boundary and its
  access-control assumptions (not validated); §10 demo readiness criteria, metrics, outcome document
  fields; walkthroughs: shared capabilities, configuration by kind, extension points E1–E5, proposed
  client-policy change mechanism (SD OQ-12), EX-1 to EX-6 checks, S-1 and S-2 with tests and
  specialist questions. SA-14, SA-15. Prompt Trace not captured: no model call made.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass b, review fixes 1–5) ·
  `AAMAD_TARGET_RUNTIME=crewai` · §5 release rule: prompt, model or schema changes need a linked local
  evaluation report on the PR's final commit, with a CI check for the link; §5/§8 real-name scan as
  committed pre-commit and pre-push hooks that fail closed (including a missing identifier file), and
  the response if bypassed (unpushed: rewrite; pushed: treat as exposed, history decision to the
  operator, DL-07); §4 every business table carries `fund_id` (corrects an S-1 claim that it already
  did); S-2 and E5: conditional verdicts marked Future Work, MVP verdict schema stays at three
  values (CR-003); §7 the 30-minute review target depends on the G1/G2 UX design.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass c) · `AAMAD_TARGET_RUNTIME=crewai` ·
  §9 test layers, runtime checks, verification and security assessment before Deliver (criteria
  table left for `*define-eval-criteria`); requirement-to-component map (F1–F10); six-week estimate
  in focused days (≈ 52 Must, ≈ 46 core) with a **proposed** cut line (WP-23 to WP-29 below), the
  consequences of each item below the line, a provisional fit verdict by remaining capacity, Tier 2
  cuts and a week-1 re-estimate trigger, routes and endpoints by line; implementation guidance by
  epic. SOQ-1 updated; new SOQ-12 (remaining capacity, operator); SA-16; checklist: requirement map
  ticked. Cut line not agreed: it is a scope decision for the operator, then `@product-mgr`.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass c, scope agreed) ·
  `AAMAD_TARGET_RUNTIME=crewai` · operator agreed the **thin slice** (DL-22) with four answers: keep
  the evaluation report; keep G1 reject, G2 override and G3 decline with reasons; keep the coverage
  view only; re-run of a failed step to future scope. Estimate section rewritten as "Six-week estimate
  and agreed scope" (≈ 42.5 focused days, 32–60; future scope ≈ 10; Tier 2 cuts available, not
  pre-approved; routes and endpoints by scope); thin-slice scope keys added to Work Ownership and the
  Control Register; feasibility note and SOQ-1 updated; implementation guidance builds the slice only.
  SOQ-12 (remaining capacity) still open. Note: the pass (c) edits were stashed automatically by
  GitHub Desktop during a branch switch and restored from `stash@{0}` before this change.
- 2026-11-11 · persona `system-arch` · action `create-sad` (pass c, SOQ-12) ·
  `AAMAD_TARGET_RUNTIME=crewai` · SOQ-12 answered: the operator commits the time the thin slice needs,
  without a number; recorded as a commitment, not a measured fit; the week-1 re-estimate (1.3×
  trigger) is the check. Feasibility note, scope status and fit table wording updated.
- 2026-11-11 · persona `system-arch` · action `define-eval-criteria` · `AAMAD_TARGET_RUNTIME=crewai` ·
  §9 Evaluation Criteria filled for the thin slice: run rules EC-R1 to EC-R4 and criteria EC-001 to
  EC-021 across accuracy, latency, safety, security and cost, each with metric, threshold, grading
  method and source; diagnostics listed separately. Two operator answers (DL-23): 3 of 3 evaluation
  runs on the same commit must pass; obligation names graded by the operator's judgement (closes
  OQ-US001-1, OQ-US013-1 for `@product-mgr`). Review time measured on the human demo rehearsal, not
  on scripted runs. §5 release rule and §10 demo criterion updated to three runs; SA-17. Golden
  dataset, graders and runner left to `@qa.eng` `*run-evals`.
- 2026-11-11 · persona `system-arch` · action `define-eval-criteria` (review fixes 1–5) ·
  `AAMAD_TARGET_RUNTIME=crewai` · one cost sentence ("US$4 hard stop; any run over US$2 fails EC-012")
  in CR-017, Production Shape, §4 cross-check, §7 and EC-012; EC-R5 written name-match rule recorded
  before the first evaluation run, with a starting draft for the operator; EC-009 lists the 7
  paragraphs and reconciles US-001 c4's five items; EC-R1a no best-of (any failing run → fix and
  re-run all three); §7 evaluation cost per cycle (up to US$6, about 15 minutes) and new SOQ-13
  (development spend limit, operator).
- 2026-11-12 · persona `system-arch` · action `define-eval-criteria` (SOQ-13) ·
  `AAMAD_TARGET_RUNTIME=crewai` · operator decision DL-24: development model usage capped at US$50
  until 13 December 2026, enforced in the provider account (operator-owned, not application code),
  checkpoint at US$25 with stop-and-review by activity; §7 development spend cap table; EC-R6 spend
  logged per evaluation run with activity label and running total; SOQ-13 resolved. A model swap for
  one role is noted as a release under the swap rule, not assumed.
- 2026-11-12 · persona `system-arch` · action `update` · `AAMAD_TARGET_RUNTIME=crewai` · new SOQ-14
  (model provider and starting model, before the week-1 spike), with the Setup steps it triggers:
  provider-standard key name, spending limit before the key, telemetry opt-out verified against the
  installed CrewAI version (SD MN-002).
- 2026-11-12 · operator session (Claude Code, no AAMAD persona; at the operator's instruction, edited by
  the product manager session because the operator asked for the SAD run state model to be updated) ·
  action `update` (OQ-US015-4, DL-22) · added the Run state model (`ACTIVE`, `FAILED`, `ABANDONED`,
  `COMPLETED`); a failed step or a timeout ends the run as `FAILED`; new W-19a abandon run (reason
  required, audited, nothing undone, not a general cancel); CR-023 reads the state, tests T-RUN-0 to
  T-RUN-4; endpoint `POST /runs/{id}/abandon` and error `RUN_NOT_ACTIVE`; new WP-12a (2 focused days,
  the product manager's estimate for the architect to confirm), slice 42.5 → 44.5 (32–60 → 33.5–63) and
  the fit table moved by 2; SA-18 (`COMPLETED` = G3 decided); SOQ-10 note. Flagged for `@system.arch`.
- 2026-11-12 · persona `system-arch` · action `update` (SOQ-14) · `AAMAD_TARGET_RUNTIME=crewai` ·
  operator decision DL-25: OpenAI API on prepaid credits (US$25 to start, US$50 ceiling); model per
  role (cheaper default for the extractor, reasoning model for the judge, verifier on a model
  different from the extractor's; exact IDs confirmed before the spike); Claude Code is the build
  tool only. Model and Context Strategy, §2 sampling, §4 and Production Shape variables
  (`OPENAI_API_KEY`, `LLM_MODEL_EXTRACT`, `LLM_MODEL_VERIFY`, `LLM_MODEL_JUDGE`), §7 enforcement via
  prepaid credits updated. "Generation" in the operator's wording recorded as the extractor only
  (no other model step exists). SOQ-14 resolved; new SOQ-15 (verifier model family).
- 2026-11-12 · persona `system-arch` · action `update` (SOQ-15) · `AAMAD_TARGET_RUNTIME=crewai` ·
  operator decision DL-26: verifier defaults to a cheaper mid-tier model different from both the
  extractor's and the judge's; the week-1 spike runs both candidates on `C-1`, `C-2` and `I-1` at
  least 5 times; switch to the reasoning model if the mid-tier misses any planted conflict in any run;
  recall, false alarms and cost per run recorded for each. Model table and spike bullet updated;
  SOQ-15 resolved.
- 2026-11-12 · persona `system-arch` · action `update` (PRD OQ-6) · `AAMAD_TARGET_RUNTIME=crewai` ·
  operator decision DL-27: before the first G3 publication the GP view shows a read-only empty state
  with a fixed message and no notifications; in the thin slice. Kept distinct from the
  post-publication review notice (FR-025), which stays future scope (DL-22). W-16, §3 `/calendar`,
  CR-012 (constant message, no counts or status) and EC-014 (exact message) updated.
