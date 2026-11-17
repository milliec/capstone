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
- **Evidence:** screenshots in the session scratchpad (not committed; see Open Questions):
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
| M-001 | Keyboard, primary task | manual | **not tested** | — | Markup is native links, radios, buttons, a skip link first; a hand pass with Tab is still owed (operator or `@qa.eng`) |
| M-002 | Visible focus | manual | **not tested** | — | `:focus-visible` 2 px orange outline is in `site.css`; not seen in a browser yet |
| M-003 | Contrast spot check | — | **not tested** | — | Only style-note token pairs are used (measured in `style-note.md`); no tool run on the pages |
| M-004 | Target size | screenshots | passed (visual) | `08-check-rules`, `10-…` | Answer options and buttons 40 px tall; checkboxes 18 px inside a full-width label |
| M-005 | Automated a11y scan | — | **not tested** | — | No scanner installed |
| M-006 | Visual regression | Playwright Test | **not tested** | — | See 3b |
| M-007 | Status not by colour alone | greyscale screenshot | passed | `grey-1280` | Every pill and step state reads as a word |
| M-008 | Works unstyled | stylesheet removed | passed after fix | `08u-unstyled-1280` | Reading order intact; see H-003 |
| M-009 | Nothing preselected; no `required`/`disabled`/`pattern` | page tests | passed | `test_nothing_is_preselected_on_any_page`, `test_no_browser_checks_on_forms` | UX-004, UX-011, ux.md §1.2 |
| M-010 | No internal words on screen | page test | passed | `test_no_internal_words_on_screen` | UX-019 |
| M-011 | No horizontal scroll at 360 px | screenshot | passed | `frame360-600` | UX-012 |

### 3b. Visual regression

**Not tested.** Playwright is not installed in `.venv`, and the skill says the first baseline is
taken only after the operator's Human judgment pass has no open high-severity finding. Next step:
the operator reviews §4; then `@frontend.eng` proposes adding Playwright to
`requirements-dev.txt` and scaffolds `tests/visual/` per `.cursor/skills/visual-regression/SKILL.md`.

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
| H-006 | Empty "Who files", "Sent to", "Why" columns; empty "what's not in this calendar" lists even after a rejection | `/g3`, `/calendar` | at G3, published | 1024, 360 | The specialist cannot check what the General Partner will read | **high for the demo** | open, waits for H-036 V-10, V-11 and B2 | `11-publish-1024`, `frame360-600` |
| H-007 | At 1024 px the sidebar stacks above the content (the mock-up breakpoint is 1100 px) | all | — | 1024 | Longer scroll; nothing breaks | low | accepted as in `app.css`; operator to confirm | `11-publish-1024` |

## 5. Findings

1. **H-006 (open, high for the demo).** The G3 and calendar pages cannot show "Who files", "Sent
   to", "Why" or the rejected and unused lists until H-036 and B2 land. The demo script (§7 of
   `frontend.md`) works step by step, but step 11 shows empty lists and step 12 shows no "Why".
2. **H-005 (open, medium).** Review numbers show as run IDs until H-036 V-1.
3. **F-013, F-014 (not tested).** No refusal can be shown on the page yet; the slots exist and
   are covered by markup only.
4. **M-001, M-002 (not tested).** A keyboard pass by hand is still needed before acceptance.

## 6. Remaining limitations

- Open: H-005, H-006, H-007 (above). All wait on `@backend.eng` (H-036, B2) or an operator call.
- Not tested: keyboard, focus, contrast tool, automated scan, visual regression, other
  browsers, refusals, the `:has()` fallback in a real browser without `:has()`.
- Screenshots are taken from saved pages with the stylesheet beside them, so fonts load from the
  public font service; the pages render the same in the running app.

## Sources

- `project-context/2.build/ux.md`, `frontend.md`, `style-note.md`; `docs/prototype/` mock-ups.
- `tests/tier2/test_pages.py`; Tier 1 tests in `tests/tier1/`.
- Screenshots listed in §1 (session scratchpad).

## Assumptions

- The 1100 px stacking breakpoint from `app.css` is kept (H-007), so 1024 px shows the sidebar
  stacked rather than side by side.
- Fonts from the public font service are available during the demo.

## Open Questions

1. **Evidence.** The screenshots are in the session scratchpad, which is temporary. Commit a small
   set (fictional data only) under `project-context/2.build/evidence/`, or keep the review
   without committed images?
2. **H-007.** Keep the 1100 px breakpoint, or lower it so 1024 px keeps the sidebar beside the
   content?

## Audit

- 2026-11-17 · persona `frontend-eng` · action `review-ui` · renderer: the running app (stand-in,
  pause 1 s) and headless Chrome 157 · viewports 1280, 1024, 360 · `project.mode` greenfield ·
  four findings fixed in `2a46163`; three open. Keyboard, focus, scan and visual regression
  recorded as not tested. No model call.
