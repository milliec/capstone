# UX review: the stubbed UI (B5 pages, light visual pass)

Rendered review of the seven pages, 403 and 404 against the approved contract. Method:
`.cursor/skills/product-design/SKILL.md` (Review mode). An agent's own reading is not the
acceptance decision; the operator's Human judgment pass is (§4).

## Input Requirements

**UX specification**: `project-context/2.build/ux.md` (approved 2026-11-16; the operator keeps it
in `2.build/`, ux.md Open Question 2).
**PRD / stories**: `project-context/1.define/prd.md` (through `ux.md` and `sad.md`; nothing taken
beyond them).
**frontend.md**: `project-context/2.build/frontend.md` (approved 2026-11-17).
**Renderer**: the real app (`uvicorn`, stand-in agents, `STAND_IN_UNIT_PAUSE_S=1`, temporary
database) driven over HTTP; pages saved as the server rendered them and screenshotted with headless
Chrome 157. The 360 px view is a 360 px `<iframe>`, because desktop Chrome will not open a window
that narrow.
**Viewports inspected**: 1280 px and 1024 px (specialist pages), 360 px (General Partner calendar).
**Compared with**: the mock-ups in `docs/prototype/` side by side at 1280 px (`run-status`,
`review-rules`, `frameworks`), added after the operator found H-008. The first pass compared the
pages with ux.md's wording only.

## 1. Scope

- **Exercised, rendered:** sign-in; Filing rules (empty, active, populated); review status
  (running with units filling in, refresh off, your turn, published, failed); Check the rules
  (at G1, after two decisions, unstyled); Confirm what applies (at G2); Check the calendar and
  publish (at G3); calendar (General Partner empty, General Partner published, specialist); 403.
- **Exercised through the test client only (HTML, not screenshotted):** every step page before,
  at and after its step; abandoned review; G1 "ended before this step"; 404; server error page
  (template only). 12 page tests in `tests/tier2/test_pages.py`.
- **Not tested:** any refusal on the page other than `FORBIDDEN` (the stub services refuse
  nothing until B2, H-036 V-12); keyboard pass by hand; screen reader; automated accessibility
  scan; visual regression; Firefox and Safari; the `:has()` fallback in a browser without
  `:has()` (checked only as markup).
- **Evidence:** `project-context/2.build/evidence/` (13 screenshots, listed in its README). The
  first-pass images named below were in the session scratchpad and are replaced by that set:
  `01-sign-in-1280`, `04b-running-still-1280`, `07-review-status-your-turn-1280`,
  `08-check-rules-1280`, `08u-unstyled-1280`, `10-confirm-applies-1280`, `11-publish-1024`,
  `13-gp-calendar-360`, `frame360-600` (the real 360 px view), `16-review-status-failed-1280`,
  `17-filing-rules-populated-1024`/`-1280`, `grey-1280` (greyscale).

## 2. Functional gate

| ID | Route | State | Viewport | Result | Evidence | Notes |
|----|-------|-------|----------|--------|----------|-------|
| F-001 | `/sign-in` → `/specialist/runs` | sign in as specialist | 1280 | passed | `01-sign-in` | Two equal buttons, nothing preselected |
| F-002 | `POST /specialist/runs` → status | start with the demo rule | 1280 | passed | `04b-running-still` | Lands on step 1 "In progress", brass pill "AI is drafting the rules", "Last updated at 08:14:51." |
| F-003 | `/specialist/runs/{id}` | running, units one by one | 1280 | passed | `04b-running-still` | Two Done, one Running, two Waiting with the 1 s pause; refresh links shown |
| F-004 | `/specialist/runs/{id}?refresh=off` | refresh off | — | passed | page test `test_refresh_only_while_working` | No reload; "Automatic refresh is off." |
| F-005 | status → `/g1` | your turn | 1280 | passed | `07-…`, `08-check-rules` | One primary link "Check the rules"; sidebar "Your turn" |
| F-006 | `/g1` | answer-first form | 1280 | passed | `08-check-rules` | Only the question shows until an answer is chosen (`:has()` in Chrome) |
| F-007 | `/g1` → `/g2` → `/g3` → publish | happy path | 1280, 1024 | passed | `10-…`, `11-publish-1024` | Each "Finish" lands on review status, then the next step |
| F-008 | `/calendar` (General Partner) | nothing published | — | passed | page test `test_empty_calendar_shows_only_the_message` | The fixed message only |
| F-009 | `/calendar` (General Partner) | published | 360 | passed | `frame360-600` | Rows stack with labels; no sideways scroll; no moved or OQ-7 mark |
| F-010 | `/specialist/runs` as General Partner | 403 | — | passed | `15-403` (HTML), Tier 1 tests | "No access" title, "Go to the calendar" |
| F-011 | start with "Make step 1 fail (demo)" | failed | 1280 | passed | `16-review-status-failed` | Without-Retry page; step 1 "Failed"; only "Start a new review from Filing rules" |
| F-012 | `POST …/abandon` | abandoned | — | passed | smoke run (HTML) | "Abandoned at step 2 (You check the rules)." Reason and time wait for H-036 V-6 |
| F-013 | demo rule "Approve rule" | refused on the page | — | **not tested** | — | Needs B2 + B7 (`DEMO_ROW_NOT_APPROVABLE`); the stub records the approval |
| F-014 | any other refusal (`RUN_ACTIVE`, `REASON_REQUIRED`, …) | refused | — | **not tested** | — | Needs B2; templates have the slots (H-036 V-12) |

## 3. Mechanical gate

| ID | Check | Tool | Result | Evidence | Notes |
|----|-------|------|--------|----------|-------|
| M-001 | Keyboard, primary task | real key events (DevTools protocol, headless Chrome 157) | passed, with findings K-1 and K-2 | focus-order log (session scratchpad) | Sign in → start with the demo rule → approve rule 1 (weekend option, who files) → reject the demo rule with a typed reason → finish → "can't tell" with a reason → finish → publish with the box ticked: all with Tab, Shift+Tab, arrows, Space, Enter and typing. Repeated in the operator's own Chrome (Claude in Chrome, 17 Nov 2026): sign-in, skip link, start with the demo rule, "Stop automatic refresh" as the first Tab stop, approve rule 1, switch rule 2 to Reject with the right arrow, typed reason, "Reject rule": all passed, focus ring visible throughout |
| M-002 | Visible focus | real key events + screenshots | passed | `01-skip-link-focused`, `05-answer-chosen` (scratchpad) | Every Tab stop on 9 pages matched `:focus-visible` with the 2px orange outline, was visible and on screen; the skip link appears on the first Tab and leads into the main content |
| M-003 | Contrast spot check | — | **not tested** | — | Only style-note token pairs are used (measured in `style-note.md`); no tool run on the pages |
| M-004 | Target size | screenshots | passed (visual) | `08-check-rules`, `10-…` | Answer options and buttons 40 px tall; checkboxes 18 px inside a full-width label |
| M-005 | Automated a11y scan | — | **not tested** | — | No scanner installed |
| M-006 | Visual regression | Playwright Test 1.64.1, Chromium | passed | `tests/visual/visual.spec.js`, `tests/visual/visual.spec.js-snapshots/` | Baseline v1 committed 17 Nov 2026 (24 snapshots), after the operator accepted H-006 for it. Stable on a second run; a deliberate 2px change fails it |
| M-007 | Status not by colour alone | greyscale screenshot | passed | `grey-1280` | Every pill and step state reads as a word |
| M-008 | Works unstyled | stylesheet removed | passed after fix | `08u-unstyled-1280` | Reading order intact; see H-003 |
| M-009 | Nothing preselected; no `required`/`disabled`/`pattern` | page tests | passed | `test_nothing_is_preselected_on_any_page`, `test_no_browser_checks_on_forms` | UX-004, UX-011, ux.md §1.2 |
| M-010 | No internal words on screen | page test | passed | `test_no_internal_words_on_screen` | UX-019 |
| M-011 | No horizontal scroll at 360 px | screenshot | passed | `frame360-600` | UX-012 |

### 3b. Visual regression

- **Command:** `cd tests/visual && npm run test:visual` (Playwright starts the app on port 8777, fresh
  database, stand-in agents, pause 0).
- **Browser and widths:** Playwright Chromium (headless shell 156), light scheme, `en-GB`; specialist
  pages 1280 and 1024 px, sign-in and the General Partner's calendar 1280 and 360 px.
- **Snapshots:** `tests/visual/visual.spec.js-snapshots/` (24, named page-state-width; the file name
  carries the platform, `-darwin`). Dynamic text (run IDs, today's date, times) is replaced with fixed
  placeholders before each picture; animations disabled; `maxDiffPixels` 150, `threshold` 0.2.
- **Check of the check:** a second run matched all 24; making every H1 2 px larger failed with
  12,343 pixels different; the stylesheet was restored from the commit.
- **Baseline status:** **v1 committed**, 17 Nov 2026. The operator accepted the open high-severity
  H-006 for this baseline (see H-006). When H-036 and B2 fill the empty columns and lists, the
  step 4 and calendar snapshots change: propose that refresh with `*update-visual-baselines` and
  wait for approval.
- **Last baseline Audit:** v1 · 2026-11-17 · `@frontend.eng` · operator accepted H-006 for it.
- **Calendar baseline v2** · 2026-11-17 · `@frontend.eng` · operator approved all 4 refreshes:
  `07-calendar-gp-published-1280`, `07-calendar-specialist-published-1280`,
  `07-calendar-gp-published-360` (week grid and month grouping) and `07-calendar-gp-empty-360`
  (v1 had captured the sidebar empty-gap bug at phone width; fixed in `58760c1`). The other 20
  snapshots stay v1. The H-006 refresh of the step 4 and calendar snapshots is still to come.
- **Review status (published) v2** · 2026-11-17 · `@frontend.eng` · operator approved
  `03-review-status-published-1280`: the unit cards in one row with their tops aligned (`93745d3`).
  An earlier refresh of the same snapshot was rejected (cards still not aligned; frontend.md Open
  Question 11).

## 4. Human judgment gate

Found and fixed by `@frontend.eng` during this review. **The operator's own pass is still owed**:
this table is the agent's reading, not the acceptance decision.

| ID | Finding | Route | State | Viewport | User impact | Severity | Resolution | Evidence |
|----|---------|-------|-------|----------|-------------|----------|------------|----------|
| H-001 | Units table heading ran into its intro line ("Drafting the rulesThe first AI…") | review status | any | 1280 | Reads as one garbled line | medium | fixed (`2a46163`) | `07-…` before, `04b-…` after |
| H-002 | Row headers kept a divider on the last row; looked heavier than cells | all tables | — | 1280 | Visual noise | low | fixed (`2a46163`) | `08-…` before, `04b-…` after |
| H-003 | Unstyled, the two nav icons filled the page as black shapes | every page | unstyled | 1280 | Sidebar unusable if B6 is dropped | **high** | fixed (`2a46163`): size and outline on the SVG itself | `08u-unstyled-1280` |
| H-004 | Mark pills stretched across the Marks column | `/g3` | at G3 | 1024 | Labels read as bars | low | fixed (`2a46163`) | `11-publish-1024` |
| H-005 | "Review RUN-20261117-1" instead of "Review 4" | pages 2 to 6 | any | — | Machine ID on screen | medium | open, waits for H-036 V-1 | all |
| H-006 | Empty "Who files", "Sent to", "Why" columns; empty "what's not in this calendar" lists even after a rejection | `/g3`, `/calendar` | at G3, published | 1024, 360 | The specialist cannot check what the General Partner will read | **high for the demo** | **accepted for baseline v1, 17 Nov 2026: empty columns and lists wait for H-036 and B2; step 4 and calendar snapshots need one approved refresh then** (operator) | `11-publish-1024`, `frame360-600` |
| H-007 | At 1024 px the sidebar stacks above the content (the mock-up breakpoint is 1100 px) | all | — | 1024 | Longer scroll; nothing breaks | low | fixed (`40be357`): breakpoint 960 px (operator, 2026-11-17) | `11-publish-1024` |
| H-008 | **Found by the operator.** Component sizes did not match the mock-ups: stepper boxes in place of the thin line, a 19 px status sentence in place of the 26 px panel heading, 13 px unit-group captions in place of 22 px headings, no avatar, one-column cards | review status, step pages | all | 1280, 1024 | The pages looked unlike the approved design | medium | fixed (`40be357`) with the mock-ups' own component styles (`.steps`, `.cta`, `.evidence`, `.avatar`) | `mock-run-status` beside `04b-running-still` |
| K-1 | **Keyboard.** While AI works the page reloads every 3 s and focus returns to the top; "Stop automatic refresh" is the 8th Tab stop, so it must be reached within 3 s | review status | AI working | 1280 | The control that makes the refresh acceptable (WCAG 2.2.1) is hard to reach by keyboard | **high** | fixed: "Stop automatic refresh" is the first Tab stop while refreshing; confirmed with real key presses and a page test | focus-order log |
| K-2 | **Screen reader (inferred, not tested with one).** Every decision group has the same legend, "What's your decision on this rule?", so moving between forms does not say which rule | `/g1`, `/g2` | at the step | — | Context lost when jumping between forms | medium | fixed: the rule's name is in each legend for screen readers only (page test); still to be heard with a real screen reader | page source |
| H-009 | **Week grid added (display-only).** Rendered at 1280 px (two months, "Due next" underlined, entries as chips) and 360 px (grid hidden, list grouped by month). Found and fixed while rendering: at phone width a short page stretched the stacked sidebar (empty gap); the month header row sat inset when the table stacked. **Baseline v1 had captured the sidebar empty-gap bug** (`07-calendar-gp-empty-360`); it is fixed now and the calendar baseline is v2 | `/calendar` | published | 1280, 360 | Layout gaps on phones | low | fixed (`58760c1`) | session screenshots |
| H-010 | **Found by the operator.** Unit cards on review status did not line up at the top: the stacked-card margin pushed every card after the first down, and at 1280 px the third card wrapped onto a second row | review status | any with several unit groups | 1280 | Cards look misplaced | low | fixed (`5a1ad3e`, `93745d3`): no margin inside the grid; always one row, stacked below 760 px | `03-review-status-published-1280` v2 |

## 5. Findings

1. **H-006 (open, high for the demo).** The G3 and calendar pages cannot show "Who files", "Sent
   to", "Why" or the rejected and unused lists until H-036 and B2 land. The demo script (§7 of
   `frontend.md`) works step by step, but step 11 shows empty lists and step 12 shows no "Why".
2. **H-005 (open, medium).** Review numbers show as run IDs until H-036 V-1.
3. **F-013, F-014 (not tested).** No refusal can be shown on the page yet; the slots exist and
   are covered by markup only.
4. **M-001, M-002 (not tested).** A keyboard pass by hand is still needed before acceptance.

## 6. Remaining limitations

- Open: H-005, H-006 (above). All wait on `@backend.eng` (H-036, B2) or an operator call.
- Not tested: keyboard, focus, contrast tool, automated scan, visual regression, other
  browsers, refusals, the `:has()` fallback in a real browser without `:has()`.
- Screenshots are taken from saved pages with the stylesheet beside them, so fonts load from the
  public font service; the pages render the same in the running app.

## Sources

- `project-context/2.build/ux.md`, `frontend.md`, `style-note.md`; `docs/prototype/` mock-ups.
- `tests/tier2/test_pages.py`; Tier 1 tests in `tests/tier1/`.
- Screenshots in `project-context/2.build/evidence/` (see its README).

## Assumptions

- The 1100 px stacking breakpoint from `app.css` is kept (H-007), so 1024 px shows the sidebar
  stacked rather than side by side.
- Fonts from the public font service are available during the demo.

## Open Questions

1. Closed 2026-11-17: evidence committed to `project-context/2.build/evidence/` (operator, option b).
2. Closed 2026-11-17: H-007, breakpoint lowered to 960 px.

## Audit

- 2026-11-17 · persona `frontend-eng` · action `review-ui` · renderer: the running app (stand-in,
  pause 1 s) and headless Chrome 157 · viewports 1280, 1024, 360 · `project.mode` greenfield ·
  four findings fixed in `2a46163`; three open. Keyboard, focus, scan and visual regression
  recorded as not tested. No model call.
- 2026-11-17 · persona `frontend-eng` · action `review-ui` (second pass) · the operator found
  H-008; compared the pages with the mock-ups side by side and fixed it with their component
  styles; H-007 fixed (breakpoint 960 px). Open: H-005, H-006. Keyboard pass still owed (the
  operator and `@frontend.eng` together).
- 2026-11-17 · persona `frontend-eng` · evidence: 13 screenshots committed to
  `project-context/2.build/evidence/` with a README, after a real-name scan of the folder.
- 2026-11-17 · persona `frontend-eng` · keyboard pass with real key events (headless Chrome over
  the DevTools protocol, the real app with the 1 s pause): primary task completed by keyboard;
  focus visible everywhere; findings K-1 (high) and K-2 (medium) proposed to the operator.
- 2026-11-17 · persona `frontend-eng` · K-1 and K-2 fixed (operator approval); keyboard pass
  re-run with real key presses: first Tab on the refreshing page is "Stop automatic refresh".
- 2026-11-17 · persona `frontend-eng` · keyboard pass repeated in the operator's Chrome through
  Claude in Chrome (41-frame recording kept, not exported). Passed. One tool quirk, not an app
  fault: the browser tool's arrow key is named "Right", not "ArrowRight".
- 2026-11-17 · persona `frontend-eng` · visual regression scaffolded (Playwright Test 1.64.1 in
  `tests/visual/`); 24 snapshots generated and stable; first baseline waiting for the operator to
  accept H-006.
- 2026-11-17 · persona `frontend-eng` · first visual baseline (v1, 24 snapshots) committed after the
  operator accepted H-006 for it; scanned with `/usr/bin/grep` first.
- 2026-11-17 · persona `frontend-eng` · week grid and month grouping rendered and checked at 1280 and
  360 px; keyboard pass with real key presses: the calendar has the same 5 Tab stops as before.
- 2026-11-17 · persona `frontend-eng` · calendar baseline v2: the 4 approved snapshots copied from the
  run's candidates (no other file changed); suite passes.
- 2026-11-17 · persona `frontend-eng` · H-010 fixed; `03-review-status-published-1280` refreshed (v2)
  after operator approval; the other 23 snapshots unchanged; suite passes.
