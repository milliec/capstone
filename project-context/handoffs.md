# Handoffs between personas

A message board for change requests that cross persona boundaries, so nobody pastes text between chats.
Decisions live in the owner's file. This file only carries the request.

## Who owns what

| File | Owner |
|---|---|
| `1.define/prd.md`, `mrd.md`, `system-description.md`, `user-stories/`, `context-summary.md` | `@product-mgr` |
| `1.define/sad.md`, `sfs/` | `@system.arch` |
| `1.define/ux.md`, `1.define/prototypes/`, `2.build/ux-review.md` | `@ux.designer` |
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

### H-030: ux.md follow-ups from the SAD update (DL-48, DL-19, DL-44)
- From: @system.arch   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md §5 (new `VALIDATION` sentence), page 4 items 3 and 8, page 6 item 6, page 7, UX-003, Open Questions 5, 6, 8 and 15, "Where ux.md and sad.md now disagree" D1 to D5
- Ask: (1) Add a plain sentence for a decision submitted with no answer chosen (`VALIDATION`, DL-48), shown beside the form and in the top line. (2) With H-028, note the built field names (`decision`; `approve_reason` and `reject_reason`; one reason field per answer at G2; `decline_reason`) and that G3's two buttons post to their own routes with `formaction`. (3) Close Open Question 5 (DL-47 updated), Open Question 6 (DL-48: the server ignores the other answer's fields) and mark D1 to D5 as resolved in sad.md. (4) **D5, decided by the operator 2026-11-14:** show the quote-check result on **every** G1 rule, the demo rule included (SAD §3 page 4); change page 4 and UX-003, which say the demo rule shows no quote-check line. (5) **Open Question 15, decided by the operator 2026-11-14:** moved marks stay specialist-only; the General Partner's calendar has no "Moved off a weekend" card, chip, chart colour or legend entry, and the B12 charts follow the same rule (SAD §3 page 7, DL-49 update). The mock-up is already changed (`build.py`, `gp-calendar.html`); close the question.
- Why: sad.md now matches the accepted decisions, so ux.md's disagreement list and open questions are out of date.
- Outcome: (the owner fills this in)

### H-029: Answer key: business-day conventions and G1 settings after the DL-19 update
- From: @system.arch   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §4, §5, conventions `D-4` and `D-6`; SAD EC-007; linked to H-024
- Ask: Alongside H-024: (1) `D-4` lists three rules: roll forward, **roll backward** (to the preceding Luxembourg business day, skipping mock holidays) and no roll; "not confirmed" is only what the extractor reports for a silent source. (2) `D-6` is no longer reached by an approved row; mark it retired, or say so. (3) §5's expected G1 setting for `OBL-04` and `OBL-05` is "move to the preceding working day". (4) Counts: 22 entries, 6 moved off a weekend, 0 marked "roll rule unconfirmed" (SAD EC-007). **Must be done before the first evaluation run**, and before the B4 date test is written.
- Why: SAD DL-19 (updated 2026-11-14) adds `roll_backward` and removes "not confirmed" as a G1 choice; the answer key is the evaluation's ground truth.
- Outcome: (the owner fills this in)

### H-028: Update ux.md to the answer-first decision form (A9 reversed)
- From: operator   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/ux.md page 4 item 8 ("two separate forms side by side … no 'choose an answer first' control, no CSS `:has()` reveal"), page 5 item 7, page 6 item 6, and the component table row "Decision form"; H-011
- Ask: Replace the two-forms-side-by-side wording with the answer-first pattern now in `docs/prototype` (`review-rules.html`, `applicability.html`, `publish.html`): one form, a radio question with nothing chosen ("What's your decision on this rule?" Approve / Reject; "Should this rule go on the calendar?"; "Is this calendar ready …?"), and only the chosen answer's fields and button appear. Record the fallback (both answers' fields visible where `:has()` is unsupported). Keep the ux.md §1 rules as they are: nothing preselected, no HTML `required`, `disabled` or `pattern`.
- Why: The operator reversed A9 after reviewing the side-by-side layout (H-011), so ux.md and the mock-ups disagree again.
- Outcome: (the owner fills this in)

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

### H-025: Answer key: state that 7 rows are drafted, including the planted row (Q2)
- From: operator (design exploration)   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §1; CR-029; T-DEMO-1
- Ask: Add one line to the answer key saying that 7 rows are drafted at rule approval (6 genuine rows plus the planted row) and that the planted row must be rejected, so the counts read 7 drafted → 6 approved → 6 checked for applicability → 5 apply → 22 dates. **Must be done before the first evaluation run.**
- Why: The key says 6 rows today and doesn't mention the planted row, so someone could later "correct" a count that is right by design. The operator confirmed this on 2026-11-14.
- Decision (operator, 2026-11-14): **Accepted.** Add the line "7 drafted, 6 genuine; the planted row must be rejected" to the answer key. **Must be done before the first evaluation run.**
- Outcome: (the owner fills this in)

### H-024: Answer key: the two Sun 28 Feb 2027 filings move to Fri 26 Feb (Q1)
- From: operator (design exploration)   To: @qa.eng   Date: 2026-11-14
- Touches: 1.define/mock-data/expected-obligation-library.md §4, §5 (D-6); SD AC-011; CR-027; depends on H-021 (U9)
- Ask: With no "not confirmed" business-day option, show the Spain report A01 and the beneficial-owner update as moved to the preceding working day (Fri 26 Feb 2027). The total stays at 22 dates, 6 are now moved off a weekend (was 4), and no entry carries a "rule unconfirmed" mark. **Must be done before the first evaluation run.**
- Why: The answer key is the evaluation's ground truth and has to match the screens. The operator confirmed this on 2026-11-14.
- Decision (operator, 2026-11-14): **Accepted.** Both 28 Feb filings move to the preceding working day, Fri 26 Feb (DL-19 change, see H-021). "Moved off a weekend" becomes 6. **Must be done before the first evaluation run.**
- Outcome: (the owner fills this in)

### H-020: New visual style: Lexend, Inter, rounded corners, Iconoir (U8)
- From: operator (design exploration)   To: @ux.designer   Date: 2026-11-14
- Touches: 2.build/style-note.md; docs/prototype/app.css tokens
- Ask: Decide whether to update the style note to Lexend headings, Inter body, 6px corners on cards and buttons, pill chips and Iconoir icons (MIT licence, inline SVG).
- Why: The style note specifies Inter Tight, a top-left-only card radius and sharp buttons.
- Decision (operator, 2026-11-14): **In MVP, with limits.** U7 and U8 together get half a day of styling in total; drop anything that doesn't fit.
- Outcome: **Partly done, stays open.** 2026-11-14, `@ux.designer`: `2.build/ux.md` §6 records the accepted look and points to `docs/prototype/app.css` as the look reference until the style note is updated. `style-note.md` itself is not updated yet (the operator asked for it to be left alone in this pass). Close this when it is.

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
