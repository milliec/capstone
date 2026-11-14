# Handover: design exploration → capstone build

**For:** the capstone build session and its personas (`@ux.designer`, `@system.arch`, `@qa.eng`, `@frontend.eng`, `@project.mgr`).
**From:** a design exploration done outside the capstone repo on 2026-11-14.
**Status:** the operator is happy with this direction and wants the build to follow it. The capstone documents have not been updated yet. Where this folder and the documents disagree, the documents must change first; nothing here overrides `sad.md` by itself.

## What is in this folder

| File | What it is |
|---|---|
| `index.html` | Links to every screen. Start here. |
| `sign-in.html` | Role chooser |
| `frameworks.html` | "Filing rules": the list of reviews (the SAD's run list) and the sources |
| `run-status.html`, `run-status-done.html` | Step 1 while AI is working, and after it finishes |
| `review-rules.html` | Step 2, rule approval (G1), including the blocked approval on rule 7 |
| `applicability.html` | Step 3, applicability (G2) |
| `publish.html` | Step 4, publish or close without publishing (G3) |
| `calendar.html`, `gp-calendar.html`, `gp-calendar-empty.html` | The published calendar for each role, and the empty state |
| `funds.html`, `add-fund.html`, `fund-applies.html` | A second fund reusing an approved framework. **Future scope, not for this build.** |
| `app.css` | The one stylesheet. Tokens are at the top. |
| `build.py` | Generates every page. Run `python3 build.py`. Edit text here, not in the `.html` files. |
| `icons/` | Iconoir SVG files (MIT licence), placed inline by `build.py` |

The pages are static. They have no JavaScript and no logic: buttons only link to the next screen, counts do not change, filters do not filter, and only January is built in the month view. Dates that mean "today" are filled in when `build.py` runs.

All data is fictional (funds "Bramblegate Credit Opportunities SICAV" and "Hollowmere Infrastructure Fund SICAV"). "Hollowmere" was invented during this exploration and has **not** been checked against `reference/real-identifiers.txt`. Run the real-name scan before committing.

## Differences the documents must settle before code is written

Each row is a place where the mock-ups depart from the current documents. The owner decides, then updates their document.

### For `@system.arch` (`sad.md`, and `decision-log.md` through the operator)

| # | Mock-ups | Documents today | Where |
|---|---|---|---|
| A1 | No "Stand-in agents" label anywhere | Label required on every page that shows a stand-in run, and on the GP calendar | CR-030; ux.md §1.3 item 4; UX-002 |
| A2 | No demo-rule switch on the start form, and no "Demo row on" tag | Switch on the run-start form, off by default; tag on run pages | CR-029; SAD §3 page 2; `POST /specialist/runs` |
| A3 | Rule 7's refusal reads "Approval blocked: no legal basis. This rule doesn't appear in the regulation text. Reject it with a reason. Recorded in the audit trail." | A fixed sentence: "This is a planted demo row. It cannot be approved. Reject it with a reason." | CR-029; DL-44; ux.md §5 `DEMO_ROW_NOT_APPROVABLE` |
| A4 | Rule 7 still shows a "Quote found in the source" chip, which contradicts A3's "doesn't appear in the regulation text" | The planted row passes the quote check by design | CR-029 |
| A5 | When two sources disagree, the specialist **picks which source the rule follows** and writes a reason, then approves. | Approving over a flag needs a written reason. Changing a rule's deadline is an edit, which is deferred. | SD AC-006; CR-007; `REASON_REQUIRED`; DL-22 (F-01) |
| A7 | "Start a new review" is not offered while a review is open; the page explains why instead | Controls are never hidden; the server refuses and the page shows the refusal (`RUN_ACTIVE`) | ux.md §1.2; CR-004 |
| A8 | Calendar entries show the period they cover ("For December 2026") | Not a field on a calendar entry | ux.md Open Question 8 |
| A9 | Decisions use one form with two answers; the fields for an answer appear after it is chosen (CSS `:has()`, no script) | Separate explicit forms per action | ux.md §4 "Decision form" |
| A10 | The calendar has Month, Year and List views plus small charts | One read-only calendar page | SAD §3 page 7; estimate block B5/B6 |


### For `@qa.eng` (`mock-data/expected-obligation-library.md`, the answer key)

**Both must be done before the first evaluation run.** The answer key is the test's ground truth, so it has to match the screens. Both were confirmed by the operator on 2026-11-14.

| # | Mock-ups | Documents today | Where |
|---|---|---|---|
| Q1 | **Answer-key change.** With no "not confirmed" option, the two filings that fell on Sun 28 Feb 2027 (Spain report A01 and the beneficial-owner update) are shown as moved to the preceding working day, Fri 26 Feb. Still 22 dates; 6 are now moved off a weekend (was 4), and no entry carries a "rule unconfirmed" mark. | Both stay on Sun 28 Feb, marked "roll rule unconfirmed" | KEY §4, §5 (`D-6`); SD AC-011; CR-027 |
| Q2 | **Add one clear line to the answer key:** "7 rows are drafted at rule approval: 6 genuine rows plus the planted row. The planted row must be rejected." The counts then run 7 drafted → 6 approved → 6 checked for applicability → 5 apply → 22 dates. This is the design, not a mismatch, and the line is there so nobody "corrects" it later. | The key says 6 rows and does not mention the planted row beside them | KEY §1; CR-029; T-DEMO-1 |

### For `@ux.designer` (`ux.md`, `style-note.md`)

| # | Mock-ups | Documents today | Where |
|---|---|---|---|
| U1 | Product name "Compliance calendar", under an "acme" wordmark | "Obligations calendar" | ux.md §1.3 |
| U2 | "Review 4" | "Run 4" | ux.md throughout |
| U3 | "AI" as the actor ("AI drafts the rules"); the two roles appear only on the step 1 page as "the first AI" and "a second, separate AI" | "Agents", "Stage A / B / C" | ux.md §1.4, §1.5 |
| U4 | Steps named "AI drafts the rules", "You check the rules", "You confirm what applies", "You publish the calendar". No "G1/G2/G3" or "gate". | "Stage A → 1. Rule review (G1) → …" | ux.md §1.4 |
| U5 | "May not be required" on entries the specialist added without confirmation | "Precautionary" with its reason | SD P-1; PRD F5, F8; CR-019; DL-01 |
| U6 | "General Partner / Fund Manager" on sign-in and in that role's sidebar. "GP" still appears about 14 times elsewhere and the operator has not yet said whether to replace it. | "GP" | ux.md §1.1, §1.3 |
| U7 | White sidebar on a grey page; nav items Calendar, Funds, Filing rules; the review list lives on "Filing rules" | Header plus two nav links (Runs, GP calendar) | ux.md §1.3 |
| U8 | Lexend headings, Inter body, 6px corners on cards and buttons, pill chips, Iconoir icons | The style note (Inter Tight, top-left-only card radius, sharp buttons) | style-note.md |
| U9 | Business-day options are "Move to the following working day / Move to the preceding working day / Keep the date". There is no "not confirmed" option, and Approve needs one chosen. | "Roll forward / No roll / Not confirmed"; "not confirmed" counts as a choice | ux.md §5 `BUSINESS_DAY_RULE_REQUIRED`; DL-19 |
| U10 | G3 decline is "No, don't publish" → "Close without publishing", asking "What needs to change before it can be published?" | "Decline" with a reason | SD FR-022; ux.md page 6 |
| U11 | The specialist sees "This calendar is not legal advice. Before anyone relies on these dates: the way deadlines are counted … has not yet been checked against the legal texts." The GP sees only "This calendar is not legal advice." | One fixed calendar-level sentence on the GP view carrying both points | SD FR-020; ux.md page 7 |

## Counts across the screens

7 rules drafted at step 2 (the answer key's 6 plus the planted row) → 6 approved → 6 checked at step 3 → 5 apply → 22 dates.

## Kept as the documents require

- Every row and verdict gets its own explicit decision. There is no bulk action.
- "Who files" is chosen at approval when the source is silent, from the five filing parties or "Not known" (DL-39).
- A business-day rule is chosen at approval; nothing is preselected anywhere, including after a refusal.
- The quote and its source paragraph are shown with every rule.
- The checking AI never changes a rule and never picks a source (it flags; a person decides).
- Publishing needs one acknowledgement of the rejected rule and the uncited paragraphs (CR-028).
- The uncited-paragraph list appears on the rule check and on publish (W-03b).
- The run-status page updates by itself and offers a link to stop (WCAG 2.2.1).
- No page needs JavaScript.
- The GP sees no specialist-only marks and has a fixed empty state before the first publication.

## Not designed (gaps the build still needs)

- Abandoning a review at a step (W-19a). No control exists in the mock-ups.
- The failed, abandoned and declined states of a review.
- Overruling an ordinary verdict at step 3. Only the "AI can't tell" case is designed.
- Rules 4, 5 and 6 on the rule check, and rule 5 at step 3, are collapsed placeholders.
- The 403, 404 and server-error pages.

## Suggested scope against the five-day plan

The plan allows about one day for pages (B5) and a quarter-day for styling (B6). This design is larger than that.

| When | What |
|---|---|
| In the build | Sign-in, Filing rules, the four review steps, the calendar's List view, `app.css` tokens and shell |
| After the stand-in green path passes | Month and Year views, dot chart, bars and ring |
| Future scope (SD §9) | Funds list and adding a second fund |

## Technical notes for `@frontend.eng`

- The one-question decisions, the view switch and the quote highlight use the CSS `:has()` selector. It works in current Chrome, Safari, Firefox and Edge.
- With `:has()` unsupported, the decision fields stay hidden. If that matters, render both answers' fields open as the fallback.
- Fonts load from Google Fonts. Icons are inline SVG, so they need no network.
- The mock-ups are a reference for templates, not code to copy as-is: `build.py` is a throwaway generator, and its markup has no server logic.
