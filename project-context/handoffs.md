# Handoffs between personas

A message board for change requests that cross persona boundaries, so nobody pastes text between chats.
Decisions live in the owner's file. This file only carries the request.

## Who owns what

| File | Owner |
|---|---|
| `1.define/prd.md`, `mrd.md`, `system-description.md`, `user-stories/`, `context-summary.md` | `@product-mgr` |
| `1.define/sad.md`, `sfs/` | `@system.arch` |
| `2.build/ux.md`, `1.define/prototypes/`, `2.build/ux-review.md` | `@ux.designer` |
| `2.build/setup.md` | `@project.mgr` |

Add a row when a new persona starts producing a file. Never edit a file you don't own: raise a handoff.

## How it works

1. Add an entry at the **top** of "Open". Address it **To** the file's owner, or **To: operator** for a
   decision only the operator can make.
2. The owner makes the change in their own file, then moves the entry to "Done" and fills in "Outcome".
3. Refer to IDs (F-xx, DL-xx, SOQ-xx, EC-xx). Never copy the text of a decision.

## Entry template

```
### H-NNN: short title
- From: @persona   To: @persona or operator   Date: YYYY-MM-DD
- Touches: file and IDs (for example, sad.md DL-40)
- Ask: one or two sentences. What should change?
- Why: one sentence.
- Outcome: (the owner fills this in: what changed, or why not)
```

## Open

### H-052: "No date-shaped value": the guardrails allow a date copied word for word from the agent's input
- From: @backend.eng (B3 step 3, operator decision 2026-11-18)   To: @system.arch   Date: 2026-11-18
- Touches: sad.md §2 agent cards ("Rules for all three cards": "The guardrail refuses any date-shaped value"; card 1 and card 3 guardrails "no date-shaped value"); Build card Never row; CR-003
- Ask: Reword the rule so it matches what B3 built and the operator approved: a guardrail refuses a date-shaped value **the agent wrote itself**, and allows one that is **copied word for word from the text the agent was given** (QN-1 steps 1 and 2 applied to both). Month names count only when capitalised ("rule 3 may apply" is not "3 May"). Code: `backend/domain/guardrails.py`, `find_date_shaped`; tests `tests/tier1/test_guardrails.py`.
- Why: Read literally, the rule fails correct output: the `SRC-VATLAW-P1` quote must contain "31 October", and an applicability rule may name the "Law of 17 December 2010" (the answer key's own `OBL-01` rule does). The intent, "a model never computes a date" (Never row), is kept.
- Outcome: (the owner fills this in)

### H-048: FYI and one fix: refusals are live; the abandon box reads `typed` the wrong way; the visual script changed
- From: @backend.eng (B2)   To: @frontend.eng   Date: 2026-11-17
- Touches: `backend/web/templates/pages/review_status.html` (the abandon textarea); `tests/visual/visual.spec.js`; 2.build/frontend.md §10.1 V-12
- Ask: (1) **Fix for you:** the abandon textarea prints `refusal.typed` as a whole, but the V-12 contract (and every other form) uses a dict, `{field name: text typed}`. B2 sends `typed = {"reason": "..."}` for abandon, so the box would show the dict. Please read `refusal.typed.reason`. (2) For information: the services now refuse for real (all 17 codes, `backend/services/refusals.py`). The page is shown again with the refusal and the refusal's HTTP status (409 or 422); anchors are `row-N`, `verdict-N`, `start`, `ack`, `decline-reason`, `decision`, `abandon`, or none; `RUN_ACTIVE` carries `short` and `link_text`. Please look at each page with each refusal once; the new Tier 1 tests only check the data, not how it looks. (3) I changed the **driving steps** (not any snapshot) in `tests/visual/visual.spec.js`: the server now refuses to finish G1 or G2 with an item undecided, and checks the publish lists, so the script decides rules 2 and 3 and answers 1 and 3 after the pictures that need them undecided, and posts the lists the page shows. The same 18 snapshots still differ; none were re-recorded.
- Why: B2 turns the stub forms into real checks; the page tests (`tests/tier2/test_pages.py`) also needed every item decided before finishing, via `tests/flow.py`.
- Outcome (`@frontend.eng`, 2026-11-18): **(1) Done.** The abandon textarea reads `refusal.typed.reason`, and only when the refusal's anchor is `abandon` (the same guard as the other forms, so another form's text can't land in it). Checked by rendering: a blank reason is refused (422) and comes back as typed; a stale page is a whole-page refusal and leaves the box empty. frontend.md S-29. **(2) and (3)** noted; the once-per-refusal look at each page is still to do.

### H-040: Build order: B12 (calendar views) pulled forward, before B10
- From: @frontend.eng (operator decision, 2026-11-17)   To: @system.arch   Date: 2026-11-17
- Touches: sad.md Build card "Order" row, "Order of work" row 12, Estimate (B12 row, "Build order" paragraph, drop order), §3 page 7; DL-49 (decision-log.md)
- Ask: Record that the operator moved B12 forward: it is built now, before B6 and B10, in its one-day box, because the frontend is waiting on the backend (H-036, B2) and the operator wants the views in the Friday demo. Scope unchanged from DL-49: Month and Year views and the dot chart (the only chart the calendar mock-ups use), chosen by a link, no script, front end only, the List view the default. One deviation to confirm or reject: the layout is arranged by a small display-only helper in the web layer (`backend/web/calendar_view.py`, frontend.md W-5), not by templates and the stylesheet alone. It reads only the entries the List view already gets and adds no field. **Second deviation (operator, 2026-11-17: "behave like the mock-up"):** the views are switched by a tab-styled radio group with CSS (`:has()`), in place and with no script, as in `docs/prototype/gp-calendar.html`, not "chosen by a link" (SAD §3 page 7). **Third (operator, 2026-11-17, later):** the **Month view is the default**, as in the mock-up, not the List view ("the view the tests and the demo use"); tests and the demo now open on Month, and the List view is one click away. Drop order (operator): dropped after B6 and Tier 2, before B13b.
- Why: The Build card "Order" row is authoritative (H-001); the order changed by operator decision, so the SAD should say so.
- Outcome (`@system.arch`, 2026-11-17): **Done.** Checked against the code first (`calendar.html`, `site.css`, `routes/calendar.py`; commits `f311130`, `a3e71dc`, `3c47ad3`): the radio group with Month as the default is what is built. The first B12 commit (`f311130`, links, List default) was replaced the same afternoon. Recorded: the Build card "Order" row and Order of work (new row 5a: B12 after B5, before B7, B6 and B10); the Estimate (B12 row, "Build order", drop order); §3 page 7 (Month default, radio group, below 960 px only the List view shows); a DL-49 update in `decision-log.md`; Audit entries in both. **Drop order as in H-040:** B12 as a whole after B6 and Tier 2, before B13b; the calendar then shows the List view alone. **Departure 4 (the helper) confirmed, on one condition written into DL-49:** `backend/web/calendar_view.py` stays display-only (it may group, order and count the entries it is given and pick "due next" by comparing with today; it may not add a field, drop or mark an entry, calculate a date, call a service or model, or read what the viewer may not see). Totals unchanged (≈ 7.75). Not edited, for their owners: `ux.md` (H-042), `scaffold-plan.md` (H-041), `frontend.md`. **One stale comment for `@frontend.eng`:** `backend/web/routes/calendar.py` line 75 still says the views are "chosen by a link"; the code below it is correct (default Month, line 79).

### H-036: View fields the B5 templates need from the services
- From: @frontend.eng (operator approval, 2026-11-17)   To: @backend.eng   Date: 2026-11-17
- Touches: 2.build/frontend.md §10.1 (V-1 to V-12) and §2; backend/services/runs.py, decisions.py, calendar.py (view functions only); 2.build/backend.md "Known gaps" (templates choosing from the phase); ux.md §1.2, §5, §10
- Ask: Add the view fields in the contract table of `frontend.md` §10.1 to the stub view functions, keeping the H-035 names and signatures. **The table gives the exact names and shapes the templates read** (rewritten 2026-11-17): review number, status tone, step states (`steps`), the status-sentence counts, end and failure details (`ended`, `failure`, `published_at`, `ended_because`), the starter's label, G1 / G2 / G3 card evidence and decided lines, the calendar summary, and the shared refusal object with the typed text to show again (V-12, with B2). Placeholder values are fine in stand-in mode; the names are what matter.
- Update (operator, 2026-11-17, frontend.md Open Question 10): **added** `steps` (V-3) and `failure` (V-6); the templates already read them when sent. **Dropped, do not build:** `index`, `total`, `next_undecided`, `show_forms`, `progress`, `index_order`, `weeks`, `months`, and (2026-11-17, later) the calendar `summary` (V-11; the page counts it from the entries) (the page counts and orders the lists you send; the calendar week grid and month grouping are not built). **Unit groups (operator, 2026-11-17): build it**, as a `group` field on each unit, not a separate list: one of `drafting`, `checking_drafts`, `applies`, `dates`, assigned by the backend (step 1 splits into the source-document units and the rule-checking units). Shape in `frontend.md` §10.1, V-4. The page already reads it. Sending it changes the step 1 review status snapshots: report them as with the others.
- Why: The page never decides (ux.md §1.2). Until these fields exist, the templates show only what the stubs send, plus interim lookups of ux.md's fixed tables in one file (`parts/lookups.html`), which go as each field lands.
- Note (2026-11-17, B12 in the Friday demo, H-040): the calendar's Month and Year views and dot chart are being built now. They look sparse with the shell's two placeholder entries; the stand-in fixtures (B3/B4: the full set of rules and dates) make them worth showing. If B3/B4 can land before Friday, the demo benefits.
- Note (2026-11-17, visual check): these fields will change what the pages show, so `cd tests/visual && npm run test:visual` (CLAUDE.md check 3) **will fail**, at least on the step 4 and calendar snapshots. That is expected (the operator accepted it for baseline v1; `ux-review.md` H-006). Do not re-record the snapshots: report which ones failed in the Outcome, and `@frontend.eng` proposes the refresh for the operator to approve.
- Outcome (`@backend.eng`, 2026-11-17): **Done except V-12.** V-1 to V-11 are in the stub view functions with the H-035 names and signatures (PRs #68 to #73; `backend.md` "View fields for the pages"). `steps`, `failure`, and the unit `group` are included; the dropped fields were not built. **V-12 (the refusal object) waits for B2/B7.** Two choices to confirm: the review number is the run's place among the fund's runs, oldest = 1 (the SAD does not define it); and stand-in calendar entry 2 now moves from Sun 18 to Mon 19 Apr 2027 so its "moved" mark is consistent. **Visual check (`npm run test:visual`) now fails on 18 snapshots, not re-recorded:** `02-filing-rules-populated` (1024, 1280); `03-review-status-your-turn` (1024, 1280), `-failed` (1280), `-published` (1280); `04-check-rules-at-step` (1024, 1280), `-two-decided` (1280); `05-confirm-applies-at-step` (1024, 1280); `06-publish-at-step` (1024, 1280); `07-calendar-gp-list-view` (1280), `-gp-published` (1280, 360), `-gp-year-view` (1280), `-specialist-published` (1280). `@frontend.eng` proposes the refresh for the operator to approve.

### H-027: The weekend-option refusal is not shown in the mock-up; build it from ux.md
- From: operator   To: @frontend.eng   Date: 2026-11-14
- Touches: 2.build/ux.md page 4 item 8 and §5 `BUSINESS_DAY_RULE_REQUIRED`; docs/prototype/review-rules.html (rule 3, design note)
- Ask: When the specialist submits "Approve rule" with no weekend-or-holiday option chosen, the server refuses with `BUSINESS_DAY_RULE_REQUIRED` and the page shows the refusal (top line and beside the field), as ux.md specifies. The static mock-up can't act this out, so it carries a design note under rule 3's options instead. Don't treat the missing refusal in the mock-up as the intended behaviour, and don't add a browser `required` check (ux.md §1, "No HTML `required` … on decision forms").
- Why: A static page can't check a form, and the operator chose a design note over faking the refusal on every click.
- Outcome: (the owner fills this in)

<!-- H-004 to H-026 come from the design exploration in docs/prototype/ (see docs/prototype/HANDOVER.md).
     One entry per difference row. Nothing in docs/prototype overrides sad.md until the owner decides. -->

### H-026: Decide the "Not designed" gaps and the scope split for the new mock-ups
- From: operator (design exploration)   To: operator   Date: 2026-11-14
- Touches: docs/prototype/HANDOVER.md "Not designed" and "Suggested scope"; sad.md Build card and estimate blocks B5, B6; SD §9; W-19a, W-03b
- Ask: (1) Decide how each gap gets designed or scoped out before the pages are built: abandoning a review at a step (W-19a, no control in the mock-ups); the failed, abandoned and declined states of a review; overruling an ordinary verdict at step 3 (only the "AI can't tell" case is designed); rules 4, 5 and 6 at the rule check and rule 5 at step 3 (collapsed placeholders); the 403, 404 and server-error pages. (2) Accept or change the suggested scope split: **in the build** are sign-in, Filing rules, the four review steps, the calendar List view, and the `app.css` tokens and shell; **after the stand-in green path passes** are the Month and Year views, dot chart, bars and ring; **future scope (SD §9)** is the Funds list and adding a second fund. (3) Say whether the missing rows A6 and A11 exist: the handover note lists A1 to A5 and A7 to A10 only.
- Why: The plan allows about one day for pages (B5) and a quarter-day for styling (B6), and this design is larger than that, so only the operator can trade scope against the five days.
- Decision (operator, 2026-11-14): **Partly decided.** Scope: A10 is in the MVP, built last with a one-day timebox (H-012); U7 and U8 get half a day in total (H-019, H-020); A5 is post-MVP (H-008). **Still open:** the five "Not designed" gaps, whether Funds and adding a second fund stay future scope, and whether rows A6 and A11 exist.
- Outcome: (the owner fills this in)

### H-020: New visual style: Lexend, Inter, rounded corners, Iconoir (U8)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/style-note.md; docs/prototype/app.css tokens
- Ask: Decide whether to update the style note to Lexend headings, Inter body, 6px corners on cards and buttons, pill chips and Iconoir icons (MIT licence, inline SVG).
- Why: The style note specifies Inter Tight, a top-left-only card radius and sharp buttons.
- Decision (operator, 2026-11-14): **In MVP, with limits.** U7 and U8 together get half a day of styling in total; drop anything that doesn't fit.
- Outcome: **Done.** 2026-11-15, `@ux.designer`: `2.build/style-note.md` now describes `docs/prototype/app.css` as the source of truth (Lexend / Inter / DM Mono, 6px radii, the orange, brass, slate and bordeaux status families, motion and reduced-motion rules) and has an Icons section for Iconoir. `2.build/ux.md` §6 now says "Done" and points to it.

### H-003: Add `aamad validate` to CI, and make `--no-verify` a stop-and-report
- From: @system.arch (operator request)   To: @project.mgr   Date: 2026-11-13
- Touches: setup.md (Git hooks section, and the "no CI code" line in the B1 scope), `.github/workflows/` (new), `requirements-dev.txt` (new, already created by @system.arch at the operator's request), `scripts/git-hooks/run-checks.sh`
- Ask: (1) Add a CI job that runs `aamad validate` only, as a backup for commits made with `--no-verify`. CI installs the validator with `pip install -r requirements-dev.txt`, which pins `aamad==1.0.1` (the version in the operator's local `.venv`); keep that pin in step with the local one and mention the file in setup.md. It must carry the same temporary qa.md exception as the hook until H-002 removes both together. (2) Keep the real-name scan local only: CI must not run it, and `reference/real-identifiers.txt` must never be uploaded, copied into a CI secret, or committed. (3) Record in setup.md the same rule that is now in the root `CLAUDE.md` (added by @system.arch with the operator's approval): any `--no-verify` commit by an agent is a stop-and-report to the operator, not something to fix quietly. Do not edit `CLAUDE.md` again for this.
- Why: Hooks are per clone and can be skipped; CI is the shared backstop, but the identifier list is itself sensitive, so that one check stays on the operator's machine.
- Outcome: (the owner fills this in)

### H-002: Remove the qa.md exception from run-checks.sh when qa.md is written
- From: @system.arch (operator request)   To: @project.mgr   Date: 2026-11-13
- Touches: `scripts/git-hooks/run-checks.sh` (the TEMPORARY qa.md exception in check 3), setup.md open question on qa.md
- Ask: Remove the qa.md exception from run-checks.sh when `@qa.eng` writes `2.build/qa.md`. If H-003's CI job is in place by then, remove the same exception there in the same change.
- Why: The exception was only meant to last until `qa.md` exists; left in place it would hide a real "qa.md missing" error.
- Outcome: (the owner fills this in)

## Done

### H-047: Record what B2 built: Rule 9 in B2, the order checks run in, and the start-up rule
- From: @backend.eng (B2, operator instruction)   To: @system.arch   Date: 2026-11-17
- Touches: sad.md Order of work row 3 and Build card (the stage-end store, rule 9, is listed under B3); §4 "Transitions and guards" and "Refusals"; run-state rules 7 and 9; 2.build/backend.md "B2"
- Ask: Record three things the build settled. (1) **Rule 9 is built in B2**, at the operator's request, because decisions cannot be stored (decide-once) before rows are: the store with the stage-attempt check, the discard of late output, and stage outputs written all or nothing. B3 now only replaces the stand-in data. (2) **The order checks run in** where the table lists several codes: the review has ended (`RUN_NOT_ACTIVE`), then wrong phase (`RUN_STAGE_RUNNING`), then a stale page (`VERSION_MISMATCH`), then the action's own checks; for a row or answer, already decided comes before no answer or a bad answer. Also: a row's or verdict's posted `version` is stored but **not compared** (the table lists `VERSION_MISMATCH` for the run only). (3) **The start-up rule (rule 7) is built now**, not later, because without it a restart mid-stage leaves a review `ACTIVE` in a `*_RUNNING` phase, which B2's `RUN_ACTIVE` and abandon checks would never let go of.
- Why: The SAD should match the build so the next persona does not repeat or undo it.
- Outcome (`@system.arch`, 2026-11-18): **Done**, checked against the code first. (1) Rule 9 in B2: rule 9 text, Service functions row, Estimate B2 and B13b rows, Order of work rows 2 and 3, SOQ-35; B3 keeps the `late` trace line and the cost count for discarded output; not re-estimated. **Also recorded:** B2 renamed `stage_store.finish_stage` to `store_stage_outputs`, a name H-035 had fixed; the new name stands. (2) New "Order of checks" paragraph after the Transitions table, as built. **One correction:** the posted row or verdict `version` is not compared **and not stored**; the decision stores the row's or verdict's own version (always 1). (3) Start-up rule: rule 7 text and a new Service functions row `runs.fail_interrupted_runs`; it was already a B2 item in the Estimate. Audit entry in `sad.md`.


### H-046: Write two backend rules into the SAD: the review number, and where "ended at" comes from
- From: @backend.eng (operator approval, 2026-11-17)   To: @system.arch   Date: 2026-11-17
- Touches: sad.md §4 ("Identifiers and versions" for the number; the "Service functions (H-035)" table or the `runs` / audit text for the time); 2.build/backend.md "View fields for the pages"; ux.md "Review {n}" wording (read-only here)
- Ask: Record two rules the build had to choose because the SAD is silent. (1) **Review number:** a review's number is its place among the fund's runs, oldest = 1 ("place among the fund's runs, oldest = 1"); runs are never deleted, so a number never changes. ux.md and the pages say "Review 4" but nothing defines it. (2) **"Ended at" comes from the audit log:** the time and reason shown for an abandoned or declined review are read from the review's last `gate_event` audit entry, because `runs` has no "ended at" column. Confirm both, or say what to change (for example, a real `ended_at` column).
- Why: H-036 V-1 and V-6 needed a rule; the code uses these, and the SAD should own them (`backend.md` Assumptions point here).
- Outcome (`@system.arch`, 2026-11-18): **Both confirmed, no `ended_at` column.** Review number: new row in "Identifiers and versions" (counted when shown, not stored; no service deletes a run). "Ended at": new paragraph after the §4 Data table. The last-`gate_event` rule is safe because every request on an ended run is refused and logged as `refusal`, never `gate_event`. `backend.md` Assumptions can point at those two places.


### H-051: Stand-in rules 2 and 3 say "central administration"; "Who files" should show one of the six options
- From: @ux.designer (operator decision, 2026-11-17)   To: @backend.eng   Date: 2026-11-17
- Touches: `backend/stand_in/shell_data.py` (`ROWS`, rules 2 and 3, `responsible_role`); ux.md UX-016 and page 7 (Who files); `backend/services/calendar.py` line 39 (reads the value, no change asked)
- Ask: Change `responsible_role` from `"central administration"` to `"fund administrator"` on rules 2 and 3. The calendar capitalizes it, so it then reads "Fund administrator", one of the six "who files" options (UX-016). Expect the calendar (page 7) and publish (step 4) snapshots to change, and probably the check-rules (step 2) ones, which print the value as the source says it. Run `cd tests/visual && npm run test:visual` and report which failed in the Outcome. Do not re-record: `@frontend.eng` proposes the refresh for the operator to approve (`CLAUDE.md` check 3).
- Why: "Central administration" is not a filing party in the mock profile or in ux.md, so the stand-in calendar showed a "Who files" value the product never offers.
- Outcome: Done by @backend.eng on branch `backend/h051-fund-administrator`. `responsible_role` is now `"fund administrator"` on rules 2 and 3 in `backend/stand_in/shell_data.py` (two lines; `calendar.py` unchanged), so "Who files" reads "Fund administrator". Tier 1 and Tier 2 (`pytest tests`): 138 passed. Real-name scan prints nothing. `aamad validate`: only the known missing-artifact findings (`qa.md` H-002, `integration.md`, `evals.md`). **Visual check: 10 snapshots differ, nothing re-recorded.** Plain `main` passes the visual check, so all 10 come from this change. Step 2 (check rules): `04-check-rules-at-step-1280`, `04-check-rules-at-step-1024`, `04-check-rules-two-decided-1280`. Step 4 (publish): `06-publish-at-step-1280`, `06-publish-at-step-1024`. Page 7 (calendar): `07-calendar-gp-published-1280`, `07-calendar-gp-published-360`, `07-calendar-gp-list-view-1280`, `07-calendar-gp-year-view-1280`, `07-calendar-specialist-published-1280`. Next: @frontend.eng proposes the new snapshots for the operator to approve (`CLAUDE.md` check 3).

### H-041: FYI: B12 built now; drop order and plan
- From: @frontend.eng (operator decision, 2026-11-17)   To: @project.mgr   Date: 2026-11-17
- Touches: 2.build/scaffold-plan.md §2 (block order) and §6 (drop order, "Hold B12 until B10 is green"); 2.build/frontend.md §11
- Ask: For information. B12 (calendar Month and Year views and the dot chart) is being built now, in its one-day box, while the frontend waits on H-036 and B2 (H-040). The List view stays the default and does not depend on it. Please update the plan's order and drop order when H-040 lands; the operator's drop order for the week grid (after B6 and Tier 2, before B13b) now covers B12 as a whole.
- Why: the build is on `frontend-spec` and the plan still says B12 is held until B10 is green.
- Outcome (`@project.mgr`, 2026-11-17): **Done** in `2.build/scaffold-plan.md`, after checking `sad.md` on `main` (PR #82). §2: B12 is row 5a, after B5 and before B7, B6 and B10, with the display-only helper condition from DL-49; B13b's row now reads "dropped after B6, Tier 2 and B12". §6: drop order is **B6 and Tier 2, then B12 as a whole, then B13b; T-MAP-1 never**; the "Hold B12 until B10 is green" risk is replaced; **H-050's forecast** (B2 about 0.8 to 1.0 day, B3 should shrink, B7 and B13b about 0.25 day each, stage time limit and Pydantic unknown-field refusal not estimated, B1 + B2 did not pass 1.3 days by the operator's clock, re-check after B7) is added. Totals unchanged (≈ 6.75, ≈ 7.75 with B12). `frontend.md` §11 is `@frontend.eng`'s to update. **Left as is, for the operator:** `setup.md` "Order" under Timing guardrails still lists no B12 (and no B13a); say if you want it brought in step.

### H-050: B1 + B2 checkpoint: please re-check the drop order against the operator's clock
- From: @backend.eng (B2, operator instruction)   To: @project.mgr   Date: 2026-11-17
- Touches: 2.build/setup.md (the "Checkpoint: if B1 and B2 together pass 1.3 days" line and the order of work); sad.md Build card "Checkpoint" and the drop order (read only: B6 and Tier 2 are dropped if B1 + B2 pass 1.3 days)
- Ask: Re-check the drop order. **I cannot measure calendar days, so I cannot say whether B1 + B2 passed 1.3 days; the operator's own clock decides.** What I can give is effort. (1) B2 as the operator scoped it (the real checks, V-12, Rule 9 and real stored data, plus the start-up rule) is larger than the SAD's 0.5 day: I would put it at roughly 0.8 to 1.0 days of focused work alone, so with B1 it is likely at or over 1.3. Most of the growth is Rule 9 and stored data, which the SAD put in B3 (H-047), so B3's own 1.0 day should shrink by a similar amount; I have not re-estimated it. (2) Left in my lane, from the SAD: B7 about 0.25 day (likely less, the refusal object and its slot exist), B13b about 0.25 day. The operator asked me **not to start** the stage time limit or the Pydantic unknown-field refusal yet; neither is estimated, and both are still B2 items in the SAD's block list, so please count them. (3) Evidence: PR #75 (3 commits, 138 tests).
- Why: The SAD says B6 and Tier 2 are dropped at this checkpoint if B1 + B2 pass 1.3 days; a forecast that ignores the pulled-forward Rule 9 work, or the two deferred B2 items, would misjudge it either way.
- Outcome: Closed 2026-11-17 by `@project.mgr`. The operator's clock says B1 + B2 did **not** pass 1.3 days, so the drop order is unchanged and nothing goes to `@system.arch`. The effort forecast (B2 about 0.8 to 1.0 day, B3 should shrink, B7 and B13b about 0.25 day each, the stage time limit and the Pydantic unknown-field refusal not estimated) is recorded in `setup.md` "Timing guardrails". **Re-check the checkpoint after B7** (operator instruction).

### H-044: FYI: the real-name scan now skips binary files
- From: @frontend.eng (operator approval, 2026-11-17)   To: @project.mgr   Date: 2026-11-17
- Touches: `scripts/git-hooks/run-checks.sh` (check 2), root `CLAUDE.md` ("Checks to run after changing committed files", item 1); commit `1676c8e`
- Ask: For information; no action needed. The scan gained `-I` (skip binary files) in the hook and in CLAUDE.md. Keep both in step if you change either, and use the same flags in CI if H-003 ever brings the scan there.
- Why: Compressed image bytes sometimes spell a listed word by chance: a visual-snapshot refresh was blocked on two PNGs whose only change was a 1-pixel underline. A text search cannot see a name drawn as pixels. Trade-off: a binary file with readable text (PDF, Word) is no longer scanned; such files are not committed here.
- Outcome: Done 2026-11-17 by `@project.mgr`. Information only. `setup.md` "Git hooks" check 2 names the `-I` flag and says to keep the hook and `CLAUDE.md` in step; CI does not run the scan (H-003).

### H-045: FYI: H-036 landed; frontend.md status marks updated; the interim lookups are yours to delete
- From: @backend.eng (operator approval, 2026-11-17)   To: @frontend.eng   Date: 2026-11-17
- Touches: 2.build/frontend.md §2 (intro, "Reads" lines for pages 2 to 7), §10, §11, S-06; `backend/web/templates/parts/lookups.html`, `parts/macros.html`; 2.build/backend.md "View fields for the pages"
- Ask: For information, plus one action that is yours. (1) The services now send H-036 V-1 to V-11 (PRs #68 to #73), so `frontend.md` was updated with the operator's approval (sync-docs D1 to D5): sent fields marked ✅, §10 and §11 say "done except V-12", and the S-06 note was removed. Still ⏳: the refusal object (V-12, with B2), "Approval blocked" (B7), and `rendered_at` / `refresh_on` (web layer, yours). Dropped fields are marked "not built". (2) The interim lookups in `parts/lookups.html`, and the fallbacks that use them in `macros.html` and the page templates, are now only a fallback. **Deleting them is yours**, as the file says; please check each page still renders when you do.
- Why: The lookups were marked "interim: replaced by H-036 V-n" so they would go when the fields landed. Two stand-in details to know: the stand-in makes no "Checking the drafts" units until B3, and calendar entry 2 now moves from Sun 18 to Mon 19 Apr 2027. The visual check now fails on 18 snapshots (listed in H-036's Outcome); none were re-recorded, and you propose the refresh for operator approval.
- Outcome (`@frontend.eng`, 2026-11-17): **Done.** The interim tables are deleted from `parts/lookups.html` (it keeps only ux.md's fixed wording) and the fallbacks are gone from `macros.html` and the pages (`001d348`, merged in #78; finished in `e44f4c7`, which also fixed the stepper test that #78 left failing on main). Every page renders in every review state; 138 tests pass. The visual candidates differ on exactly the 18 snapshots in H-036's Outcome, each traced to a server field; the refresh is proposed to the operator (`ux-review.md` §3b). H-005 and H-006 closed; two low wrapping findings (H-014, H-015) raised.

### H-049: Refusal wording and placement: three sentences ux.md lacks, and which refusals are "page-level"
- From: @backend.eng (B2)   To: @ux.designer   Date: 2026-11-17
- Touches: 2.build/ux.md §5 (refusal sentences, "Where"); `backend/services/refusals.py` (sentences marked PROPOSED); 2.build/frontend.md §10.1 V-12 (anchors)
- Ask: (1) Give the wording for three cases ux.md §5 does not cover; B2 uses these plain sentences until you answer. `GATE_INCOMPLETE` with exactly one item left: "1 rule is still undecided. Decide every rule before you finish checking." (and, at G2, "1 answer is still undecided, {u} of them where AI can't tell. Decide every answer before you finish."). `RUN_STAGE_RUNNING` when the review is at a **different gate** (not working): "This step is not open for decisions right now. The review status page shows where the review is." (2) Settle **placement** for four refusals: ux.md §5 calls `ACK_REQUIRED` page-level (full sentence in a box at the top and again by the control), but frontend.md V-12 lists the anchors `ack`, `decline-reason`, `decision` and `abandon`, and the page then shows only the short line "Not done. The reason is shown beside {target_label}." at the top. B2 sends the anchors, with `target_label` "the box", "the reason", "the question" and "abandon". Say whether those four should have an anchor (short top line) or none (full box at the top).
- Why: The services must send one or the other, and the two documents disagree.
- Outcome: Done 2026-11-17 by `@ux.designer` in `2.build/ux.md` §5. (1) Two sentences added to the table, as B2 wrote them: `GATE_INCOMPLETE` with one rule left (G1) or one answer left (G2), and `RUN_STAGE_RUNNING` when the review is at a different gate. (2) Placement: the four refusals **do get an anchor**. `ACK_REQUIRED` (`#ack`, "the box"), `REASON_REQUIRED` on abandon (`#abandon`, "abandon") and on "Close without publishing" (`#decline-reason`, "the reason"), and `VALIDATION` with no answer chosen (`#decision`, "the question") show the short top line with a "Go to {target}" link, and the full sentence beside the control, like a rule card. Refusals about the whole review (`GATE_INCOMPLETE`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE`, `RUN_STAGE_RUNNING`, `FORBIDDEN`) have no anchor and show the full box at the top only; the old "and again by the control" is dropped for them. `@frontend.eng`: V-12 already matches, and "Go to abandon" is the one link that reads oddly (operator may prefer a different `target_label`). §5 changes where `ACK_REQUIRED` is shown; ux.md approval is unchanged but the operator should read it.

### H-043: After a decision, land on the next card to decide
- From: @frontend.eng (operator decision, 2026-11-17)   To: @ux.designer   Date: 2026-11-17
- Touches: 2.build/ux.md page 4 "After each action" (Approve rule / Reject rule) and page 5 "After each action" (Confirm / Overrule / Decide); 2.build/frontend.md W-7
- Ask: Record the operator's decision: after a successful decision on step 2 or 3, the page lands on the **next card still to decide** (wrapping round to the first undecided one; the finish section when all are decided), not on the card just decided. The decided card still shows its decision and the "Next rule to decide" link. Refusals are unchanged: they still land on the card they are about (§5).
- Why: The operator found landing at the top, or on the card just decided, jarring during the click-through; the 30-minute review target (§7) favours moving straight on.
- Outcome: Done 2026-11-17 by `@ux.designer` in `2.build/ux.md`: page 4 and page 5 "After each action" (and the page 4 review-time bullet) now say a successful decision lands on the next card still to decide, wrapping round to the first undecided one, and on the finish section when all are decided; the decided card still shows its decision and the "Next rule to decide" link; refusals still land on the card they are about. `frontend.md` W-7 is `@frontend.eng`'s to mark as no longer a departure.

### H-042: Page 7 now follows the gp-calendar mock-up
- From: @frontend.eng (operator decision, 2026-11-17)   To: @ux.designer   Date: 2026-11-17
- Touches: 2.build/ux.md page 7 (items 5 to 8, phone width), "Mock-up differences this revision does not apply" (the Month and Year views); `docs/prototype/gp-calendar.html`; 2.build/frontend.md §2 page 7
- Ask: Record the operator's decisions in ux.md page 7. (1) The page follows `gp-calendar.html`: the three summary cards (Due next on the dark card, Entries in {year} with the dot chart, May not be required), then one calendar, "All entries for {year}", with a Month / Year / List switch that shows only the chosen view (**Month by default**, operator 2026-11-17). (2) The Month view replaces item 6's two-month week grid; the list (item 7) is one of the views, not always shown. (3) The summary cards are counted on the page from the entries the viewer sees. (4) Below 960 px only the List view shows. (5) New wording for the copy review: "No filings this month.", "Entries in {year}: {n}", "None" when nothing is due next, and the Year view legend ("May not be required (dashed)", "Due next (underlined)"). The Month and Year views leave "Mock-up differences".
- Why: The build follows the operator's decision; ux.md still describes the earlier page 7.
- Outcome: Done 2026-11-17 by `@ux.designer` in `2.build/ux.md` page 7: items 5 to 8 rewritten (three summary cards in the mock-up's order, one calendar "All entries for {year}" with a Month / Year / List switch, **Month by default**, only the chosen view shows, counted on the page); the two-month week grid is gone; the List table is one of the views; below 960 px only the List view shows. New wording recorded: "No filings this month.", "Entries in {year}: {n}", "None", and the Year legend "May not be required (dashed)" / "Due next (underlined)". The Month and Year views are removed from "Mock-up differences". Not touched: `sad.md` §3 page 7 still says the views are chosen by a link and List is the default; that is `@system.arch`'s (H-040).
- Second pass (`@ux.designer`, 2026-11-17, after PR #82): `sad.md` §3 page 7 and the DL-49 update now say what ux.md says (radio group styled as tabs, Month the default, only the List view below 960 px, dot chart, helper display-only), so the point above is closed. Checked ux.md page 7 against the SAD and the built page (`calendar.html`, `calendar_view.py`, `routes/calendar.py`, `site.css`); no wording or layout changed. Added what the SAD and the code say and ux.md did not: only the links between months reload the page; the month the Month view opens on; the Year view and the dot chart show one year; the H2 reads "All entries" when the entries span more than one year; the focus ring on the tabs. New check UX-023 (§8). Not touched: `frontend.md` (`@frontend.eng`).

### H-037: Sign-in adopts the mock-up's left-hand panel, in portfolio voice
- From: @frontend.eng (operator decision, 2026-11-17)   To: @ux.designer   Date: 2026-11-17
- Touches: 2.build/ux.md page 1 (Sign-in), §1.6 (Voice), "Mock-up differences this revision does not apply"; docs/prototype/sign-in.html; built in backend/web/templates/pages/sign_in.html (2.build/frontend.md §11)
- Ask: Record the operator's decision (option C): page 1 gets the mock-up's ivory left-hand panel with the wordmark, three decorative cards (dot calendar, bars, ring; hidden from screen readers and below 1100 px), the tagline "AI drafts. People approve." and the two first-person paragraphs, word for word. **Portfolio voice is allowed on the sign-in page only; every other page keeps the product voice of §1.6.** The right-hand sign-in box keeps ux.md page 1's wording. Remove "the left-hand panel on sign-in" from "Mock-up differences this revision does not apply", and tell the copy review (CR-019) that these lines are exempt from §1.6.
- Why: The operator wants the demo's first screen to carry the portfolio story; ux.md currently rules the panel out, and only its owner edits it.
- Outcome: Done 2026-11-17 by `@ux.designer` in `2.build/ux.md`: page 1 now describes the left-hand panel word for word (wordmark, three decorative cards hidden from screen readers and below 1100 px with no per-date labels, the tagline, the two first-person paragraphs); §1.6 allows portfolio voice on page 1's panel only and says the copy review (CR-019) treats those three lines as exempt; "the left-hand panel on sign-in" is removed from "Mock-up differences". The right-hand box keeps its wording.

### H-038: FYI: the real-name scan now skips node_modules
- From: @frontend.eng (operator approval, 2026-11-17)   To: @project.mgr   Date: 2026-11-17
- Touches: `scripts/git-hooks/run-checks.sh` (check 2, the real-name scan), root `CLAUDE.md` ("Checks to run after changing committed files", item 1); commit `91b9d4e`
- Ask: For information; no action needed. The scan gained `--exclude-dir=node_modules`, the same treatment as `.venv`, in the hook and in CLAUDE.md. Please keep it in step if you change either, and add the same line to the CI job if H-003 brings the scan there (H-003 keeps the scan local only, so today there is nothing to change).
- Why: The visual tests install Playwright into git-ignored `tests/visual/node_modules/`; the hook scanned that third-party code and blocked a commit on two lines of Playwright's bundle. Also learned: in some agent shells `grep` is replaced by a look-alike that misses matches the system `grep` finds; hand-run scans should call `/usr/bin/grep` (`docs/learning-notes.md`, §4).
- Outcome: Done 2026-11-17 by `@project.mgr`. Information only. `setup.md` "Git hooks" check 2 now lists what the scan skips (`node_modules` as well as `reference/`, `.venv`, `.git`) and says to keep the hook and `CLAUDE.md` in step. CI does not run the scan (H-003), so no CI change.

### H-039: Record the visual check in setup.md
- From: @frontend.eng (operator approval, 2026-11-17)   To: @project.mgr   Date: 2026-11-17
- Touches: 2.build/setup.md (tooling and test commands); `tests/visual/` (Playwright Test 1.64.1, pinned); root `CLAUDE.md` check 3; 2.build/frontend.md §11.1
- Ask: Add the visual check to setup.md next to the other test commands, as the visual-regression skill asks: install once with `cd tests/visual && npm install --ignore-scripts && npx playwright install chromium` (Node; the app itself stays Python); run with `cd tests/visual && npm run test:visual` (Playwright starts the app on port 8777 with a fresh database, stand-in agents, no pause). Note that it is not part of `make test`, the commit hook or CI, and that snapshots are re-recorded only after operator approval (CLAUDE.md check 3).
- Why: setup.md is where every persona looks for how to run things; today the commands are only in `frontend.md`, which other personas do not read.
- Outcome: Done 2026-11-17 by `@project.mgr` in `2.build/setup.md`. New "Tests and checks" section after "Git hooks": the install-once command, the run command, port 8777 with a fresh database, stand-in agents and no pause; says it is not part of `make test`, the commit hook or CI; says snapshots are re-recorded only after operator approval (`CLAUDE.md` check 3). Commands checked against `tests/visual/package.json` and `playwright.config.js`.

### H-035: Record the B2 service names, the stub rule, two ID schemes and the `trace` columns
- From: @backend.eng (operator decisions, 2026-11-16)   To: @system.arch   Date: 2026-11-16
- Touches: sad.md Build card ("Build approach" row), §4 Backend (services, "Identifiers and versions", table list `trace`), Order of work B2; 2.build/backend.md "Stub function list" and Open Questions 1 to 4
- Ask: (1) Write the service function names and signatures into the SAD's B2 section, taken from the "Stub function list" in `2.build/backend.md` (named after the §4 routes), so B2 fills them in without renaming. (2) Update the Build card "Build approach" row to say: Sprint 3 stubs move states but run no checks; B2 adds the checks. (3) Add the ID schemes `VER-<run>-<n>` (verdict) and `CAL-<run>` (calendar) to "Identifiers and versions". (4) List the `trace` table's columns before B3 starts.
- Why: the app shell had to choose names, a stub rule and two ID schemes the SAD does not give; the operator accepted them and wants the SAD to own them.
- Outcome: Done 2026-11-16 by `@system.arch` in `1.define/sad.md`. (1) New §4 "Service functions" table (names and signatures from `2.build/backend.md`, unchanged) and a note that a stage function gets the run ID and the stage name; "How the layers connect" says the same. (2) Build card "Build approach": stand-in shell stubs move status and phase and write units, audit, calendar and publication records but run no check; allowed only in stand-in mode; the first green path cannot pass before B2's checks. "Sprint 3" was not used. (3) "Identifiers and versions": `VER-<run>-<n>` and `CAL-<run>`. (4) New `trace` column list in §4, before B3. One note: the "form `decision` matches the route" check for decline stays in the page handler's form validation, because `decline_calendar` has no `decision` argument. `backend.md` not edited.


### H-032: SAD changes for the stubbed UI: demo-rule refusal wording, Retry, empty calendar, failure demo
- From: @ux.designer (operator decisions, 2026-11-16)   To: @system.arch   Date: 2026-11-16
- Touches: sad.md CR-029, DL-44 (decision-log.md), DL-27, EC-014, run-state model (rule 2, the `FAILED` row, "Transitions and guards"), §3 page 3 "No re-run action", §4 routes, refusal codes and failure reasons, `runs` table, data model (DL-50); 2.build/ux.md "Where ux.md and sad.md now disagree" D9 to D12 and §10.3 data gaps G-1 to G-10
- Ask: One batch, as the operator asked. (1) **D9:** update the `DEMO_ROW_NOT_APPROVABLE` sentence in CR-029 and DL-44 to the wording in ux.md §5. (2) **D11:** update DL-27 and EC-014 to the empty-calendar message in ux.md page 7 item 3 (Open Question 12). (3) **D10, G-3:** allow Retry of the failed stage only, keeping earlier decisions and auditing it (ux.md page 3 "Failed review"): a transition out of `FAILED`, its route, guard, refusal codes and audit event, which failure reasons allow it, how it counts towards the cost cap, and what happens to outputs the failed stage already stored. (4) **D12, G-10:** add the failure demo (ux.md page 2 and page 3 "Failure demo"): a start-time switch on the run like `demo_planted_row`, stand-in agents only, refused with the real model and on evaluation runs, audited, with its own failure reason; it fails step 1 once (Open Question 21). Also please answer the data gaps G-1, G-2 and G-4 to G-9 in ux.md §10.3; they need no new behaviour, only a decision on where the data comes from.
- Why: The operator approved these for the stubbed UI ("error and retry" is on the minimal UI bar), and Retry and the failure demo are new behaviour, which the project rules say is a SAD edit first. Until (3) lands, the build uses the fallback in ux.md (no Retry form; UX-022).
- Outcome: Checked 2026-11-16 by `@system.arch`; no SAD edit needed, because the batch had already landed in `sad.md` as DL-51 to DL-54. (1) D9: CR-029 and DL-44 carry the ux.md §5 sentence. (2) D11: DL-27 and EC-014 carry the new empty-calendar message. (3) D10, G-3: run-state rule 10, `POST …/retry`, `RUN_NOT_FAILED`, `RETRY_LIMIT_REACHED`, `RETRY_NOT_ALLOWED`, CR-032, DL-51. (4) D12, G-10: `demo_fail_step1`, failure reason 8 `demo failure`, CR-033, DL-52. G-1, G-2, G-4 to G-9 are answered in ux.md §10.3 (DL-53, SOQ-33). `ux.md` D9 to D12 are marked resolved. This entry was only waiting to be closed.


### H-034: Bring ux.md up to DL-51 to DL-54, and decide on stashed ux.md edits
- From: @project.mgr   To: @ux.designer   Date: 2026-11-16
- Touches: 2.build/ux.md lines about Retry and the failure demo being blocked (intro "Approval status" note, page 3 purpose and "Failed review", page 3 actions table, Audit); sad.md DL-51 to DL-54
- Ask: (1) ux.md on `main` still says Retry and the failure demo are blocked until H-032 lands; DL-51 to DL-53 allow them, and DL-54 (PR #58) splits B13 into B13a (failure demo and per-unit stand-in pause, after B3, kept) and B13b (Retry, after B9, dropped next after B6). Please update the wording. (2) Uncommitted ux.md edits doing part of (1) were found in the `scaffold-plan` working tree, written before the split, with no commit or branch. They are saved as the stash named "ux.md follow-ups to DL-51..53 from another session". Restore with `git stash apply` and that stash's number if you want them; note they also set approval back to `pending` and say "B13" where DL-54 now has B13a and B13b.
- Why: The build follows ux.md for wording, and the stash would be lost silently if nobody owns it.
- Outcome: Done 2026-11-16, branch `ux-sync-dl51-54`. (1) `ux.md` no longer says Retry or the failure demo are blocked; it follows DL-54 (failure demo = B13a, kept, does not need Retry; Retry = B13b, after B9, dropped next after B6; "Without Retry" is the page B5 builds). Also synced the stale lines outside the four places listed here (tests, data map and gaps G-1 to G-10, D9 to D12, Open Questions 18 and 21, Audit). Approval left `approved` (operator choice). New Open Question 24: three Retry refusal sentences in section 5 are drafts, not in the SAD. (2) The stash was read, not applied (it said "B13" and reset approval to `pending`). It can be dropped once this branch is merged; not dropped yet.

### H-033: Split B13 (failure demo early, Retry late) and add a stand-in per-unit pause
- From: @project.mgr (operator decisions, 2026-11-16)   To: @system.arch   Date: 2026-11-16
- Touches: sad.md Build card ("Time", "Order", "Tier 1" rows), "Order of work", Estimate (B13 row, totals, "Checkpoint" drop-order paragraph), SOQ-35, §2 / Production Shape (stage timer, DL-43), §4 "Sign-in and secrets", §9 EC-R4 Tier 1 list, CR-030, CR-033, DL-52 (decision-log.md); root `CLAUDE.md` (Tier 1 line naming T-DEMOFAIL-1); detail in 2.build/scaffold-plan.md §2 (block table) and §6 (estimate, drop order, the numbered list of edits)
- Base: edit `sad.md` as on `main` at `7048b38` (DL-51 to DL-53). Older branches carry a stale copy.
- Ask: Seven `sad.md` edits plus one `CLAUDE.md` line, in one batch.
  1. **Order** (Build card "Order" row and "Order of work"): split B13 into **B13a Failure demo and stand-in pause**, built straight after B3's stand-in part (B3 → B13a → B4 → B5 → B7 → first green path), and **B13b Retry**, after B9 and before B6, where B13 is now. B13a's page parts (start-form checkbox, "Failure demo on" label, the "Without Retry" failed page) are written in B5.
  2. **Estimate**: replace B13 (0.5) with B13a (0.25) and B13b (0.25). Totals unchanged (≈ 6.75; ≈ 7.75 with B12); note that work before the first green path grows from about 3.5 to about 3.75 days. Please confirm or correct the quarter-day split.
  3. **Drop order** ("Checkpoint" paragraph, SOQ-35): B6 and Tier 2 first; **B13b next**; **B13a kept** with B7 (it shows the failed and running states in Sprint 3 and is built before the tripwire). T-MAP-1 never dropped.
  4. **§4 "Sign-in and secrets"**: new variable `STAND_IN_UNIT_PAUSE_S`, read only when `AGENTS_MODE=stand_in`, default 1 (seconds per unit), 0 in tests.
  5. **§2 / Production Shape and CR-030**: each stand-in agent function waits `STAND_IN_UNIT_PAUSE_S` per unit before returning its fixed output, so units finish one by one (ux.md page 3). It runs inside the backend stage timer and never in real mode; stage limits unchanged (about 12 s for stage A, 6 s for B, 1 s for C at the default).
  6. **§9 EC-R4 Tier 1 list, Build card "Tier 1" row**: T-DEMOFAIL-1 is Tier 1 from B13a, no longer tied to Retry or dropped with it; add **T-PAUSE-1** (Tier 1): real mode never pauses; stand-in mode pauses the set amount per unit. T-RETRY-1 to T-RETRY-3 stay Tier 2 with B13b.
  7. **CR-033 and DL-52**: the failure demo no longer depends on Retry. Until B13b is built (or if it is dropped), a failure-demo run ends `FAILED` and the page offers only "Start a new review from Filing rules".
  8. **Root `CLAUDE.md`**: the Tier 1 line says T-DEMOFAIL-1 counts "once block B13, Retry and the failure demo, is built; if B13 is dropped, the test goes with it". Change it to B13a, add T-PAUSE-1, and drop the "goes with it" clause, since B13a is kept.
- Why: The operator wants the failed and running states visible in the Sprint 3 stubbed UI. The Build card is authoritative (H-001), and a new setting and test tier are SAD edits first, so nothing is built until this lands.
- Note: H-032 below looks done by `7048b38` (DL-51 to DL-53) but is still under "Open"; please move it to "Done" if so.
- Outcome: **Done.** 2026-11-16, `@system.arch`: all eight items made in commit `1d7ce2e` (DL-54 in `decision-log.md`; Build card, Order of work, Estimate, drop order, §2 and §4 stand-in pause, CR-030, CR-033, DL-52, rule 11, EC-R4 and the root `CLAUDE.md` Tier 1 line), merged to `main` as PR #58 (`986ccad`). Checked item by item by `@project.mgr` before the merge. Outcome recorded by `@project.mgr`, because this entry was only in an uncommitted copy the owner could not see. H-032 is left for its owner to close.

### H-030: ux.md follow-ups from the SAD update (DL-48, DL-19, DL-44)
- From: @system.arch   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §5 (new `VALIDATION` sentence), page 4 items 3 and 8, page 6 item 6, page 7, UX-003, Open Questions 5, 6, 8 and 15, "Where ux.md and sad.md now disagree" D1 to D5
- Ask: (1) Add a plain sentence for a decision submitted with no answer chosen (`VALIDATION`, DL-48), shown beside the form and in the top line. (2) With H-028, note the built field names (`decision`; `approve_reason` and `reject_reason`; one reason field per answer at G2; `decline_reason`) and that G3's two buttons post to their own routes with `formaction`. (3) Close Open Question 5 (DL-47 updated), Open Question 6 (DL-48: the server ignores the other answer's fields) and mark D1 to D5 as resolved in sad.md. (4) **D5, decided by the operator 2026-11-14:** show the quote-check result on **every** G1 rule, the demo rule included (SAD §3 page 4); change page 4 and UX-003, which say the demo rule shows no quote-check line. (5) **Open Question 15, decided by the operator 2026-11-14:** moved marks stay specialist-only; the General Partner's calendar has no "Moved off a weekend" card, chip, chart colour or legend entry, and the B12 charts follow the same rule (SAD §3 page 7, DL-49 update). The mock-up is already changed (`build.py`, `gp-calendar.html`); close the question.
- Why: sad.md now matches the accepted decisions, so ux.md's disagreement list and open questions are out of date.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (branch `ux-answer-first-form`): (1) §5 has a `VALIDATION` row for a decision with no answer chosen ("Choose an answer first, then use its button. Nothing was saved."), shown beside the form and in the top line; new check UX-020. (2) The built field names are in §4 "Decision form" and pages 4 to 6, and page 6 says G3's buttons post to their own routes with `formaction`. (3) Open Questions 5, 6 and 8 closed (and 2: the file stays in `2.build/`, operator); D1 to D5 marked resolved. (4) D5: page 4 item 3 and UX-003 now show the quote-check line on every rule, the demo rule included. (5) Open Question 15 closed; page 7 item 8 says moved marks are specialist-only, B12 included. Approval status left `pending`.

### H-028: Update ux.md to the answer-first decision form (A9 reversed)
- From: operator   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md page 4 item 8 ("two separate forms side by side … no 'choose an answer first' control, no CSS `:has()` reveal"), page 5 item 7, page 6 item 6, and the component table row "Decision form"; H-011
- Ask: Replace the two-forms-side-by-side wording with the answer-first pattern now in `docs/prototype` (`review-rules.html`, `applicability.html`, `publish.html`): one form, a radio question with nothing chosen ("What's your decision on this rule?" Approve / Reject; "Should this rule go on the calendar?"; "Is this calendar ready …?"), and only the chosen answer's fields and button appear. Record the fallback (both answers' fields visible where `:has()` is unsupported). Keep the ux.md §1 rules as they are: nothing preselected, no HTML `required`, `disabled` or `pattern`.
- Why: The operator reversed A9 after reviewing the side-by-side layout (H-011), so ux.md and the mock-ups disagree again.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (branch `ux-answer-first-form`): page 4 item 8, page 5 item 7, page 6 item 6 and the §4 "Decision form" row now describe one answer-first form with the mock-up questions, nothing chosen, and the all-fields fallback where `:has()` is unsupported. §1 rules kept (nothing preselected; no `required`, `disabled` or `pattern`), with one sentence in §1.2 saying the form is not a hidden-button exception. The G2 question for an ordinary answer ("What's your answer on this rule?") is new wording, since the mock-ups design only the "can't tell" case (H-026).

### H-031: The G3 publish mock-up does not show the OQ-7 mark
- From: @qa.eng   To: operator   Date: 2026-11-14
- Touches: docs/prototype/publish.html (and `build.py`); SAD CR-027, §3 page 6; T-W13-1; answer key §4
- Ask: Decide whether `publish.html` should show "Depends on open question OQ-7" on the `OBL-02` entries, as SAD CR-027 and §3 page 6 require at G3. Today the mark appears on the G1 page (`review-rules.html`) and the specialist calendar (`calendar.html`), but not on the G3 page. The built app follows sad.md either way.
- Why: The mock-ups are the layout reference, so a builder copying `publish.html` could leave the mark off G3, and T-W13-1 would then fail.
- Decision (operator, 2026-11-15): **Accepted.** Show the mark on the 4 `OBL-02` entries at G3, styled as on G1 and the specialist calendar; it must not block publishing.
- Outcome: Done 2026-11-15 by `@qa.eng` (uncommitted). `build.py` `yeargrid()`: in specialist mode only, the `OBL-02` row label carries the same `chip plain` "Depends on open question OQ-7" as G1 and the specialist calendar (a year-grid tile is too small for a chip), and each of the 4 `OBL-02` tiles carries the mark as screen-reader text and in its hover title. `app.css`: one rule so that chip keeps its normal text colour inside the row label. Pages rebuilt with the build date pinned to 14 Nov, so the only real page changes are `publish.html` and the specialist `calendar.html` Year view (the same grid); the other 12 pages change only the stylesheet version number. The GP grid is unchanged, and the Publish button and form are untouched. New mock-up tests in `tests/test_answer_key.py`: the 4 `OBL-02` tiles (and no other) carry the mark, the chip appears once, and the Publish button is present, not disabled, with no OQ-7 condition in the form. 25 tests pass; each new test was shown failing on the old page and on a disabled button.

### H-029: Answer key: business-day conventions and G1 settings after the DL-19 update
- From: @system.arch   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §4, §5, conventions `D-4` and `D-6`; SAD EC-007; linked to H-024
- Ask: Alongside H-024: (1) `D-4` lists three rules: roll forward, **roll backward** (to the preceding Luxembourg business day, skipping mock holidays) and no roll; "not confirmed" is only what the extractor reports for a silent source. (2) `D-6` is no longer reached by an approved row; mark it retired, or say so. (3) §5's expected G1 setting for `OBL-04` and `OBL-05` is "move to the preceding working day". (4) Counts: 22 entries, 6 moved off a weekend, 0 marked "roll rule unconfirmed" (SAD EC-007). **Must be done before the first evaluation run**, and before the B4 date test is written.
- Why: SAD DL-19 (updated 2026-11-14) adds `roll_backward` and removes "not confirmed" as a G1 choice; the answer key is the evaluation's ground truth.
- Outcome: Done 2026-11-14 by `@qa.eng` (uncommitted): (1) `D-4` lists roll forward, roll backward and no roll, both rolls skipping weekends and mock holidays; "not confirmed" is only the extractor's report for a silent source. (2) `D-6` is marked **Retired**. (3) §5 sets `OBL-04` and `OBL-05` to "Roll backward (preceding working day)". (4) §4 reads 22 entries, none on a weekend, 6 moved off a weekend (4 forward, 2 back), 0 "roll rule unconfirmed"; dates recomputed by script. New no-model test `tests/test_answer_key.py` (17 checks, standard library only) recomputes every date and fails on any weekend entry; it passes. Still open, outside this handoff: ux.md Open Question 10 (`EVT-01` awareness date 31 Jan 2027 is after the 13 Nov 2026 demo date); left unchanged because moving it breaks the 22-entry total. **Added 2026-11-14 (operator request, SAD EC-007, CR-027):** §4 has a new column "Open-question mark (specialist only)" with `OQ-7` on the 4 `OBL-02` entries and no other entry, and a note that the mark is never on the General Partner view (CR-027: "not shown to GPs"; SAD §3 page 7: "no open-question mark"). `tests/test_answer_key.py` now has 23 checks, including the mark on the specialist calendar mock-up's `OBL-02` rows only and never on `gp-calendar.html`; all pass. The G3 mock-up gap is raised as H-031.

### H-025: Answer key: state that 7 rows are drafted, including the planted row (Q2)
- From: operator (design exploration)   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §1; CR-029; T-DEMO-1
- Ask: Add one line to the answer key saying that 7 rows are drafted at rule approval (6 genuine rows plus the planted row) and that the planted row must be rejected, so the counts read 7 drafted → 6 approved → 6 checked for applicability → 5 apply → 22 dates. **Must be done before the first evaluation run.**
- Why: The key says 6 rows today and doesn't mention the planted row, so someone could later "correct" a count that is right by design. The operator confirmed this on 2026-11-14.
- Decision (operator, 2026-11-14): **Accepted.** Add the line "7 drafted, 6 genuine; the planted row must be rejected" to the answer key. **Must be done before the first evaluation run.**
- Outcome: **Q2 done** 2026-11-14 by `@qa.eng` (uncommitted): §1 opens with "7 drafted, 6 genuine; the planted row must be rejected." and the counts 7 drafted → 6 approved → 6 checked for applicability → 5 apply → 22 dates, with a note that the planted row is added by code (CR-029), not extracted, so EC-001's "0 extra rows" stands. Checked by `tests/test_answer_key.py`.

### H-024: Answer key: the two Sun 28 Feb 2027 filings move to Fri 26 Feb (Q1)
- From: operator (design exploration)   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §4, §5 (D-6); SD AC-011; CR-027; depends on H-021 (U9)
- Ask: With no "not confirmed" business-day option, show the Spain report A01 and the beneficial-owner update as moved to the preceding working day (Fri 26 Feb 2027). The total stays at 22 dates, 6 are now moved off a weekend (was 4), and no entry carries a "rule unconfirmed" mark. **Must be done before the first evaluation run.**
- Why: The answer key is the evaluation's ground truth and has to match the screens. The operator confirmed this on 2026-11-14.
- Decision (operator, 2026-11-14): **Accepted.** Both 28 Feb filings move to the preceding working day, Fri 26 Feb (DL-19 change, see H-021). "Moved off a weekend" becomes 6. **Must be done before the first evaluation run.**
- Outcome: **Q1 done** 2026-11-14 by `@qa.eng` (uncommitted): §4 shows `OBL-04` (anchor 2026-12-31) and `OBL-05` (`EVT-01`) moved from Sun 28 Feb to Fri 26 Feb 2027 under "roll backward"; the other three `OBL-04` dates fall on weekdays and are unchanged. Totals: 22 entries, 6 moved, 0 unconfirmed. "Roll rule unconfirmed" removed; moved marks noted as specialist-only (none expected on the General Partner view). The wrong event-date answer is now 2027-02-19 (Sat 20 Feb moved back).

### H-012: Calendar has Month, Year and List views plus charts (A10)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: sad.md §3 page 7; estimate blocks B5, B6; see H-026 for scope
- Ask: Decide whether the calendar page gains Month, Year and List views plus small charts (dot chart, bars, ring), or stays one read-only page for this build, with the extra views deferred.
- Why: The SAD has one read-only calendar page, and the extra views don't fit the B5/B6 estimate.
- Decision (operator, 2026-11-14): **In MVP, with limits.** Month and Year views and the charts are built last (after the first green path and B10), with a one-day timebox. Anything not done in that day is parked.
- Outcome: Done 2026-11-14 by `@system.arch`: DL-49; SAD §3 page 7 (List view default; Month and Year views and charts front end only), new block B12 after B10 with a one-day timebox, Build card "Time" and "Order" rows, "Order of work", build and drop order, F-19 for anything left over.

### H-011: Decision form: one form with two answers, revealed by CSS `:has()` (A9)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: 2.build/ux.md §4 "Decision form"; sad.md §3
- Ask: Decide whether a decision may be one form with two answers whose fields appear after an answer is chosen (CSS `:has()`, no script), and what the fallback is where `:has()` is unsupported (HANDOVER suggests showing both answers' fields open).
- Why: ux.md specifies a separate explicit form per action, and the server must still check that each submission carries only the chosen answer's fields.
- Decision (operator, 2026-11-14): **Rejected, then reversed the same day.** First decision: keep one separate form per action; the mock-ups were changed to two forms side by side. After reviewing that layout, the operator **reversed it and adopted the answer-first pattern**: one form, the specialist picks the answer (Approve or Reject, Yes or No), and only that answer's fields appear (CSS `:has()`). Fallback: where `:has()` is unsupported, both answers' fields stay visible (`@supports` in `app.css`). Still no browser `required`: a missing field is refused by the server on the page (`BUSINESS_DAY_RULE_REQUIRED`, `REASON_REQUIRED`). Mock-ups updated (`build.py`, `app.css`): `review-rules.html`, `applicability.html`, `publish.html`; `add-fund.html` already used it. **For @system.arch:** a CSS-hidden field is still submitted, so the server must act on the chosen answer only and ignore the other answer's fields. In the mock-up both reason boxes are named `reason`, so the built forms need distinct field names. ux.md now disagrees again; see H-028.
- Outcome: Done 2026-11-14 by `@system.arch`: DL-48; SAD §3 shared decision form (answer-first, `:has()` with all-fields fallback, nothing preselected, no browser `required`, no pop-ups) and §4 (the server acts only on the chosen `decision` and ignores the other answer's fields; reason fields `approve_reason`, `reject_reason`, `<answer>_reason`, `decline_reason`; G3 buttons use `formaction` and must match `decision`; no answer → `VALIDATION`). ux.md follow-up in H-028 and H-030.

### H-010: Calendar entries show the period they cover (A8)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: sad.md calendar entry data; 2.build/ux.md Open Question 8
- Ask: Decide whether a calendar entry carries the period it covers (for example "For December 2026") as a new field, and where it comes from.
- Why: It isn't a field on a calendar entry today, so showing it needs a data change, not just a template change.
- Decision (operator, 2026-11-14): **Post-MVP stretch, after A10** (H-012). No sad.md change now.
- Outcome: Done 2026-11-14 by `@system.arch`: no field added. Recorded as a post-MVP stretch after A10 in DL-49 and new Future Work F-19; this closes the period-field question (ux.md Open Question 8).

### H-009: "Start a new review" is hidden while a review is open (A7)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: 2.build/ux.md §1.2; CR-004; `RUN_ACTIVE`
- Ask: Decide whether the start control may be hidden (with an explanation) while a review is open, or must stay visible with the server refusing it (`RUN_ACTIVE`).
- Why: ux.md §1.2 says controls are never hidden, and the server-side refusal must stay either way.
- Decision (operator, 2026-11-14): **Fix in the mock-up (done for rule 7).** Nothing is pre-selected on any row, including the demo row. Approve is always visible and enabled. Clicking Approve on the demo row is refused by the server, which shows the message beside the row plus a top line with "Go to rule 7" and records the attempt in the audit trail, on the page and never as a browser pop-up. **"Start a new review" (decided 2026-11-14, same rule):** it stays visible. While a review is in progress the server refuses it (`RUN_ACTIVE`), shows the reason beside the button and records the attempt in the audit trail. This keeps ux.md §1.2 and CR-004 as they are, so no sad.md change. Mock-up updated (`build.py`, `frameworks.html`), with the refusal wording from ux.md §5 `RUN_ACTIVE` adjusted for U2 and U4.
- Outcome: Done 2026-11-14 by `@system.arch`: confirmed, no rule change. The demo-row rule is now written out in CR-029 and DL-44's update (nothing preselected, Approve visible and enabled, `DEMO_ROW_NOT_APPROVABLE`, message beside the row plus a top line, audited, no browser pop-up). "Start a new review": CR-004, CR-023, `RUN_ACTIVE` and the §3 refusal rule already covered it; §3 page 2 now says it in one sentence.

### H-008: Two sources disagree: the specialist picks which one the rule follows (A5)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: SD AC-006; CR-007; `REASON_REQUIRED`; DL-22 (F-01)
- Ask: Decide whether, when two sources disagree, the specialist may pick which source the rule follows (with a written reason) and then approve.
- Why: Today, approving over a flag only needs a reason, and changing a rule's deadline counts as an edit, which DL-22 defers (F-01). Picking a source may be that deferred edit.
- Decision (operator, 2026-11-14): **Post-MVP.** Choosing a source stays out (DL-22). When sources disagree, the specialist approves with a written reason despite the flag (the current rule) or rejects with a reason. Mock-up updated: rule 3's source picker is removed from `review-rules.html`, and the two quotes are shown read-only.
- Outcome: Done 2026-11-14 by `@system.arch`: DL-22 update (no choosing a source; approve over the flag with a reason, or reject and start a new review); SAD "Decisions in force", §3 page 4 (both quotes read-only), Future Work F-01.

### H-007: Planted row shows "Quote found in the source" (A4)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: CR-029; linked to H-006 (A3)
- Ask: Resolve the contradiction on rule 7: the mock-up shows a "Quote found in the source" chip and also says the rule "doesn't appear in the regulation text". Choose either the chip or the wording.
- Why: The planted row passes the quote check by design (CR-029), so A3's wording may be what has to change.
- Decision (operator, 2026-11-14): **Accepted.** The chip on the demo row says "Approval blocked", matching the refusal message. Already done in the mock-up (`build.py`, `review-rules.html`); record it with the DL-44 update in H-006.
- Outcome: Done 2026-11-14 by `@system.arch`: recorded with the DL-44 update; CR-029 and §3 page 4 say the chip reads "Approval blocked" after a refused approval. The "demo" label stays (CR-029).

### H-006: New wording for the planted row's refusal (A3)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: CR-029; DL-44; 2.build/ux.md §5 `DEMO_ROW_NOT_APPROVABLE`; linked to H-007 (A4)
- Ask: Decide whether the refusal on rule 7 reads "Approval blocked: no legal basis. This rule doesn't appear in the regulation text. Reject it with a reason. Recorded in the audit trail." in place of the fixed sentence in DL-44.
- Why: The sentence is fixed by DL-44 (an operator decision) and is probably checked by a test, and the new wording no longer says the row is a planted demo.
- Decision (operator, 2026-11-14): **Accepted.** Use the plain refusal copy from the mock-ups. Log it as a DL-44 update (through the operator).
- Outcome: Done 2026-11-14 by `@system.arch`: DL-44 update; CR-029 now carries the plain copy plus the line "Recorded in the audit trail." The old sentence is gone from sad.md.

### H-005: No demo-row switch on the start form and no "Demo row on" tag (A2)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: CR-029; sad.md §3 page 2; `POST /specialist/runs`; T-DEMO-1
- Ask: Decide whether the start form drops the demo-row switch (off by default) and run pages drop the "Demo row on" tag. If so, say how the planted row is switched on instead, since the counts in H-025 assume it is present.
- Why: The switch and tag are part of the run-start contract and the demo path.
- Decision (operator, 2026-11-14): **Prototype only, no rule change.** The prototype has the demo row on by default with no switch shown. The built app keeps the demo-row switch on the run-start form. No sad.md change; close with Outcome "no change".
- Outcome: No change (as decided). SAD §3 now has one line confirming the built app keeps the demo-row switch on the run-start form.

### H-004: No "Stand-in agents" label (A1)
- From: operator (design exploration)   To: @system.arch   Date: 2026-11-14
- Touches: CR-030; 2.build/ux.md §1.3 item 4; UX-002
- Ask: Decide whether the "Stand-in agents" label can be dropped from run pages and the GP calendar, or must stay while `AGENTS_MODE=stand_in`.
- Why: CR-030 requires the label on every page showing a stand-in run, so the demo doesn't present stand-in output as real AI output.
- Decision (operator, 2026-11-14): **Prototype only, no rule change.** The prototype omits the label. The built app must show it whenever `AGENTS_MODE=stand_in`, as sad.md says today. No sad.md change; close with Outcome "no change".
- Outcome: No change (as decided). SAD §3 now has one line confirming the built app shows "Stand-in agents" whenever `AGENTS_MODE=stand_in`.

### H-013: Product name "Compliance calendar" under an "acme" wordmark (U1)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §1.3
- Ask: Decide whether the product name is "Compliance calendar", shown under a placeholder "acme" wordmark.
- Why: ux.md names it "Obligations calendar".
- Decision (operator, 2026-11-14): **Accepted** as shown in the mock-ups.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): §1.3 sidebar shows the "acme" wordmark and "Compliance calendar"; page titles use "ACME Compliance calendar (demo)"; §1.8 mapping.

### H-014: "Run" becomes "Review" (U2)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md throughout
- Ask: Decide whether the user-facing word is "Review" ("Review 4") in place of "Run" ("Run 4").
- Why: ux.md uses "Run" throughout. Code, routes and IDs can keep "run".
- Decision (operator, 2026-11-14): **Accepted** as shown in the mock-ups.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): on-screen "Run" is "Review" throughout (pages 2, 3, §5); routes and codes keep "run"; §1.8 mapping.

### H-015: "AI" as the actor in place of "Agents" and "Stage A / B / C" (U3)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §1.4, §1.5
- Ask: Decide whether screens say "AI" as the actor ("AI drafts the rules"), with the two roles named only on the step 1 page as "the first AI" and "a second, separate AI".
- Why: ux.md uses "Agents" and "Stage A / B / C". This interacts with the stand-in label in H-004 (A1).
- Decision (operator, 2026-11-14): **Accepted** as shown in the mock-ups.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): "AI" is the actor in all screen text; "the first AI" and "a second, separate AI" appear only on the step 1 review-status page (page 3); "Stand-in agents" label kept as CR-030 text.

### H-016: Step names drop "Stage", "G1/G2/G3" and "gate" (U4)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §1.4
- Ask: Decide whether the user-facing steps are named "AI drafts the rules", "You check the rules", "You confirm what applies" and "You publish the calendar", with no "G1/G2/G3" or "gate" shown.
- Why: ux.md shows "Stage A → 1. Rule review (G1) → …". The internal IDs can stay in the documents and tests.
- Decision (operator, 2026-11-14): **Accepted** as shown in the mock-ups.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): §1.4 is a four-step stepper (AI drafts the rules / You check the rules / You confirm what applies / You publish the calendar) with a phase-to-step table; no G1/G2/G3, "Stage" or "gate" on screen; UX-019 added.

### H-017: "Precautionary" becomes "May not be required" (U5)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md; SD P-1; PRD F5, F8; CR-019; DL-01
- Ask: Decide whether entries the specialist added without confirmation are labelled "May not be required" in place of "Precautionary" with its reason, and whether the reason is still shown.
- Why: The term comes from SD, PRD and DL-01, so the label may need `@product-mgr` and the operator as well.
- Decision (operator, 2026-11-14): **Accepted.** Raise a short DL-01 amendment (through the operator), not just a ux.md edit.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): "May not be required" replaces "Precautionary" on pages 5 to 7, §4, §8; the reason is still shown as the "Why". **Still open:** the DL-01 amendment (operator) and the SAD wording (CR-019, W-12), listed as D4 in ux.md.

### H-018: "GP" becomes "General Partner / Fund Manager" (U6)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §1.1, §1.3
- Ask: Decide whether the role name is "General Partner / Fund Manager" (used on sign-in and in that role's sidebar), and whether to replace the roughly 14 other uses of "GP" in the mock-ups. The operator hasn't decided the second part yet.
- Why: ux.md uses "GP" throughout.
- Decision (operator, 2026-11-14): **Accepted in part.** "General Partner" in the UI; "GP" stays in the documents.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): role name "General Partner / Fund Manager" on sign-in and in the sidebar; "the General Partner" in other screen text; "GP" kept in the documents. ux.md Open Question 13 asks the operator to confirm the long vs short form.

### H-019: App shell becomes a white sidebar with Calendar, Funds, Filing rules (U7)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §1.3
- Ask: Decide whether to replace the header-plus-two-links shell (Runs, GP calendar) with a white sidebar on a grey page whose nav items are Calendar, Funds and Filing rules, with the review list on "Filing rules".
- Why: The shell sets every page's layout, and "Funds" points to future scope (see H-026).
- Decision (operator, 2026-11-14): **In MVP, with limits.** U7 and U8 together get half a day of styling in total; drop anything that doesn't fit.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): §1.3 rewritten as the white sidebar (wordmark, product, fund, nav, identity with the demo label, sign out) plus breadcrumb; review list is "Filing rules". "Funds" left out of the nav until H-026 decides (ux.md Open Question 11). Half-day limit noted.

### H-021: Business-day options drop "not confirmed" (U9)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §5 `BUSINESS_DAY_RULE_REQUIRED`; DL-19; linked to H-024 (Q1)
- Ask: Decide whether to use the three options "Move to the following working day / Move to the preceding working day / Keep the date", with no "not confirmed" option, and Approve needing one of them chosen.
- Why: ux.md and DL-19 allow "not confirmed" as a choice; removing it changes DL-19 (an operator decision) and the answer key (H-024).
- Decision (operator, 2026-11-14): **Accepted.** Remove "not confirmed". This is a DL-19 change (through the operator). See H-024 for the answer key.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): page 4 offers "Move to the following working day / Move to the preceding working day / Keep the date", no "not confirmed"; `BUSINESS_DAY_RULE_REQUIRED` sentence, marks and UX-015 updated; Open Question 9 closed. **Still open:** the DL-19 change (operator) and the SAD enum and §4 row (D2, D3 in ux.md).

### H-022: G3 decline becomes "Close without publishing" (U10)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md page 6; SD FR-022
- Ask: Decide whether to rename the G3 decline to "No, don't publish" → "Close without publishing", with the reason prompt "What needs to change before it can be published?"
- Why: ux.md says "Decline" with a reason; the mock-ups keep the reason but change the words.
- Decision (operator, 2026-11-14): **Accepted** as shown in the mock-ups.
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): page 6 "No, don't publish" with "What needs to change before it can be published?" and button "Close without publishing"; status word, page 3 state and `REASON_REQUIRED` sentence updated.

### H-023: Not-legal-advice wording differs by role (U11)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md page 7; SD FR-020
- Ask: Decide whether to split the calendar-level notice by role, as in the mock-ups: the specialist sees "not legal advice" plus the warning that the way deadlines are counted hasn't yet been checked against the legal texts, and the GP sees only "This calendar is not legal advice."
- Why: ux.md has one fixed sentence on the GP view carrying both points, and SD FR-020 may need the GP to see both.
- Decision (operator, 2026-11-14): **Accepted with new wording. No FR-020 change.** The GP line keeps the short grey style but must cover all three FR-020 points: "These dates are the specialist's approved reading of the rules. Not legal advice. Date counting hasn't yet been checked against the legal texts." The specialist keeps the longer note. Mock-up updated (`build.py`, `gp-calendar.html`).
- Outcome: Done 2026-11-14 by `@ux.designer` in `2.build/ux.md` (uncommitted, branch `ux-mockups-exploration-handover`): page 7 calendar note split by role: the General Partner sees the exact accepted sentence in the short grey style; the specialist keeps the longer note; UX-018 added. No FR-020 change.

### H-001: Confirm which copy of the build order is authoritative
- From: @project.mgr   To: @system.arch   Date: 2026-11-13
- Touches: sad.md, Build card "Order" row and the "Order of work" table
- Ask: Say which of the two is authoritative, and add a one-line note under the other that points to it. Do not change the order itself.
- Why: Both list the build sequence, so they can drift apart, and Build personas work from the Build card.
- Outcome: The Build card "Order" row is authoritative. Added an "Authority (H-001)" note under the "Order of work" table pointing to it. Also added a pointer under the "Build order" paragraph in the Estimate section (a third copy of the sequence, in prose), which the handoff did not ask for; the operator approved it. The order itself is unchanged.
