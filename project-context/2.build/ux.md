# UX note: the seven pages (Block B5)

## The workflow (the one workflow the stubbed UI proves)

- **Who starts:** the compliance specialist.
- **What they give:** the fund `FND-DEMO-01`, then **"Start a new review"**.
- **What happens:** stand-in agents draft the rules; the specialist works through Step 2 (check the rules), Step 3 (confirm what applies) and Step 4 (publish). Step 1 is "AI drafts the rules" (§1.4).
- **How they know:** the review status shows idle, running, done or failed (§10.1).
- **What they get:** a published calendar the General Partner can read.

Owner: `@ux.designer` (`*design-ux`). For: `@frontend.eng` (templates in `backend/web/templates/`)
and `@backend.eng` (the refusal sentences in §5 are the text the service functions return).

Source of scope: `sad.md` → Build card, Never row, Order of work, and the sections it points to for
the pages (§3 "The seven pages", §4 routes and refusal codes, §7 review target, the run-state
"Transitions and guards" table, and the W- and CR- rows those name). Nothing here comes from
Future Work, Appendix A or the tag `sad-full-design`.

This note writes no HTML, template or code. It says what each page shows, in what order, in which
states, what each action does, and the exact words.

**Two references, two jobs** (operator decision, 2026-11-14). The mock-ups in `docs/prototype/` are
the reference for **layout and look**. This note is the reference for **behaviour, states, wording
and refusals**. Where they differ on behaviour or wording, this note wins. The mock-ups leave out
the "Stand-in agents" label and the demo-row switch (H-004, H-005): that is prototype-only, and the
built app keeps both (§1.3, page 2).

**Approval status**: `approved` (operator, 2026-11-16). `@frontend.eng` may build from this note.
The SAD now allows Retry and the failure demo (H-032 landed as DL-51 to DL-53; D10, D12). DL-54
splits their build: the **failure demo** is block **B13a** (built early, kept, does not need
Retry), and **Retry** is block **B13b** (built after B9, dropped next after B6). Until B13b is
built, or if it is dropped, the failed page uses the "Without Retry" version (page 3, UX-022).
Wording synced to DL-51 to DL-54 on 2026-11-16 (H-034). Approval unchanged: the sync records
decisions already made, with one exception, three draft Retry refusal sentences in §5 that only
matter if B13b is built (Open Question 24; see Audit).
Two failure-reason sentences were added on 2026-11-24 (`unexpected error`, `call limit`; H-093,
DL-58). Approval unchanged: it is wording for two reasons the SAD already records, plus one refusal
ending, confirmed by the operator (Open Question 25, closed).

---

## 1. Rules that hold on every page

### 1.1 Who uses what

| Role (mock identity) | Pages | Can change anything? |
|---|---|---|
| **Compliance specialist** | 1 to 7 | Yes: starts runs, decides rows and verdicts, publishes or declines, abandons |
| **GP** (Bramblegate Partners, fictional; on screen **"General Partner / Fund Manager"**, §1.8) | 1 and 7 only | No. Sees only the published calendar. Never sees a draft, failed, abandoned or declined run, a flag, a mark other than "May not be required", or any run status |

### 1.2 The page never decides

- Every status, count, flag, date, mark and decision on a page comes from the server.
  The templates only show it.
- **No button is hidden or disabled to enforce a rule.** If an action is not allowed, the server
  refuses it and the page shows why (§5), on the page and never as a browser pop-up. The refusal is
  recorded in the audit log (W-18). This is why the demo row and a row that failed the quote check
  both keep their Approve button, and why "Start a new review" stays visible while a review is in
  progress (H-009). The answer-first decision form (§4, DL-48) is not an exception: it shows each
  answer's button once that answer is chosen, every answer can always be chosen, and the server
  still decides whether the action is allowed.
- No HTML `required`, `disabled` or `pattern` attributes on decision forms. A missing reason is
  refused by the server with `REASON_REQUIRED`, not stopped in the browser.
- No placeholders: no "coming soon", no disabled future feature, no greyed-out control (§3,
  SD MN-007).
- No bulk action, no "approve all", nothing preselected (SD AC-026). Every radio group starts with
  nothing chosen and every checkbox starts unticked.

### 1.3 The shared frame (base template)

A white **sidebar** on the left of a grey page, and the page content in the main column (U7,
H-019; layout as in `docs/prototype/`). U7 and U8 together get half a day of styling; anything that
does not fit is dropped (H-019, H-020), and the page must still work as plain, ordered HTML (§6).

**Sidebar**, top to bottom, on every page except sign-in:

1. **Wordmark and product name**: the placeholder wordmark **"acme"**, then the product name
   **"Compliance calendar"** (U1, H-013).
2. **Fund**: label **"Fund"**, the fund name **"Bramblegate Credit Opportunities SICAV"**, and one
   small line **"Luxembourg UCI Part II · year end 31 Dec"**.
3. **Navigation** (a `<nav>` with `aria-current="page"` on the current item):
   - Specialist: **"Calendar"** · **"Filing rules"**. "Filing rules" is the review list (page 2)
     and carries a **"Your turn"** tag while a review waits for the specialist. The mock-ups also
     show **"Funds"**; it is not in this build (see Open Question 11).
   - GP: **"Calendar"** only; the calendar is their only page.
4. **Who is signed in** (at the foot): **"Compliance specialist"** with the line **"Demo with mock
   data"** under it, or **"General Partner / Fund Manager"** with the line **"Bramblegate Partners ·
   view only · demo with mock data"** (U6, H-018). Then a **"Sign out"** button (a form,
   `POST /sign-out`).

**The demo label** is the text **"Demo with mock data"** in the identity block (item 4), on every
page, as text (UX-001). It is static text only. It is *not* the F-18 hosted-demo banner: no Reset
button, no "someone may be mid-run" line.

**Main column**, top to bottom:

1. **Breadcrumb** (pages about one review, 3 to 6): **"Filing rules › Luxembourg UCI Part II ›
   Review {n}"**, the first item a link to page 2.
2. **H1** and a one-line lead (wording per page, §3).
3. **Run labels** (any page that shows a review): **"Stand-in agents"** when the review used them
   (CR-030), **"Demo rule on"** when the planted-row switch was on, and **"Failure demo on"** when
   the failure-demo switch was on (page 2, proposed). All as text tags next to the H1, never colour
   alone. The mock-ups leave them out; the built app keeps them (H-004, H-005).
4. **Refusal message** (only after a refused request, §5: the full sentence, or a short line with a
   "Go to rule {i}" link when the refusal is about one card).
5. The stepper (§1.4), on pages 3 to 6.
6. The page content.

Page `<title>` pattern: `<Page name> · ACME Compliance calendar (demo)`. After a refusal, prefix it
with `Not done: ` so a screen reader announces the refusal when the page loads. On the review
status page the title starts with the review and its status words instead:
`Review {n}: {status words} · ACME Compliance calendar (demo)`, for example `Review 4: AI is
drafting the rules`, so a screen-reader user can check progress from the tab while the page refreshes
(operator, 2026-11-17).

**Mobile shell (below 960 px)** (operator decision, 2026-11-19, H-062; on every page except sign-in).
Below 960 px, the same width at which the calendar's Month and Year views hide (page 7), the sidebar
is not shown. A slim top bar of about 56 px shows instead, so the page content starts straight
below it. From 960 px up nothing changes. The bar holds, left to right:

1. The **"acme"** wordmark, a link home. The product name "Compliance calendar" is not shown on
   the bar (it stays in the page `<title>`).
2. **"Your turn"** as a text tag, only when a review waits for the specialist (the same signal as
   the "Filing rules" tag in the sidebar). Words, never colour alone (§1.5). It is on the closed
   bar so it is not hidden inside the menu.
3. A **"Menu"** button with a three-line icon. The icon is decoration; the word "Menu" is the
   label. It is a native `<details>`/`<summary>`: the `<summary>` is the button, so keyboard
   (Enter, Space) and screen readers work with no script. The wordmark link and the tag sit
   **beside** the `<summary>`, not inside it, because a screen reader treats a `<summary>` as one
   button and would lose a link inside it.

**The panel** opens **over** the content (it does not push the page down) and holds what the
sidebar's items 2 to 4 hold, in the same order and words: the fund, the navigation (with the
"Your turn" tag on "Filing rules"), the person signed in with the demo label line, and "Sign out".
One source for both, so they never differ.

**Closing.** The menu closes when the person taps "Menu" again or follows a link (the next page
loads closed). **It does not close on a tap outside it or on Escape: no script in the MVP**
(operator decision, H-062). Escape-to-close is a possible polish-week item, listed in §9; it would
need a script exception.

### 1.4 The four-step stepper (one sitting, not three interruptions)

Every specialist page about one review (3 to 6) shows the same stepper under the H1 (U3, U4,
H-015, H-016). No "Stage", "G1/G2/G3" or "gate" is shown; those stay in the documents and tests.

> **Step 1 · AI drafts the rules** → **Step 2 · You check the rules** → **Step 3 · You confirm
> what applies** → **Step 4 · You publish the calendar**

| Server phase | Step 1 | Step 2 | Step 3 | Step 4 |
|---|---|---|---|---|
| `A_RUNNING` | In progress | Not started | Not started | Not started |
| `AT_G1` | Done | Your turn | Not started | Not started |
| `B_RUNNING` | Done | Done | In progress | Not started |
| `AT_G2` | Done | Done | Your turn | Not started |
| `C_RUNNING` | Done | Done | Done | In progress |
| `AT_G3` | Done | Done | Done | Your turn |
| `COMPLETED` | Done | Done | Done | Done |

On a review that ended without publishing, or failed:

- Steps before the one it stopped at: **"Done"**.
- The step it stopped at: **"Ended"** (`ABANDONED`, `DECLINED`) or **"Failed"** (`FAILED`).
- Later steps: **"Not started"**, with no link.

The step a review stopped at comes from `runs.phase`, which keeps its last value on an
ended review (DL-46): `A_RUNNING` → step 1, `AT_G1` → step 2, `B_RUNNING` or `AT_G2` → step 3,
`C_RUNNING` or `AT_G3` → step 4.

Stage B (AI checks what applies) is shown as the start of step 3, and Stage C (code works out the
dates) as the start of step 4, so the specialist sees four steps, not six (see Assumptions).

Each step carries a word, not just a colour: **"Done"**, **"In progress"**, **"Your turn"**,
**"Not started"**, **"Failed"** or **"Ended"**. Steps that are done or "Your turn" link to their page. It is an ordered list
(`<ol>`) with `aria-current="step"` on the current one.

How the flow feels like one sitting:

- Each step page ends with one primary button that finishes the step and lets AI or code start
  the next one.
- Finishing a step takes the specialist to the review status page, which refreshes itself while AI
  or code works and then shows one big link straight into the next step. No hunting, no extra
  clicks.
- Working out the dates (code only) is expected to take a few seconds, so step 3 → step 4 feels
  immediate.

### 1.5 Status words

A status is always a word first; colour only supports it.

| Server value | Words shown | Tone (colour role) |
|---|---|---|
| `ACTIVE` · `A_RUNNING` | **AI is drafting the rules** | info |
| `ACTIVE` · `AT_G1` | **Your turn: check the rules** | action |
| `ACTIVE` · `B_RUNNING` | **AI is checking what applies** | info |
| `ACTIVE` · `AT_G2` | **Your turn: confirm what applies** | action |
| `ACTIVE` · `C_RUNNING` | **Working out the dates** | info |
| `ACTIVE` · `AT_G3` | **Your turn: publish the calendar** | action |
| `FAILED` | **Failed** | problem |
| `ABANDONED` | **Abandoned** | neutral |
| `DECLINED` | **Closed without publishing** (U10, H-022) | neutral |
| `COMPLETED` | **Published** | success |

"Working out the dates" does not say "AI": the dates are computed by code, never by a model.

### 1.6 Voice (DL-05)

- Plain British English. Short sentences. State the fact and what happens next.
- No reassurance ("Don't worry"), no alarm ("Error!"), no advice, no "please". No exclamation marks.
- Cite the source (paragraph ID, fact ID) wherever text makes a claim.
- GP text is for a non-lawyer, stays neutral, and never implies that anything is permitted (DL-01).
- Buttons say what they do: verb + object ("Approve rule", "Publish calendar"), never "OK" or
  "Submit".
- Dates in full: "Mon 2 Feb 2027". Times: "14:02".

**One exception: the sign-in page's left-hand panel** (operator decision, 2026-11-17, option C,
H-037). Its tagline and two paragraphs are written in the first person, as the portfolio's author
speaking ("I designed this tool …"). That is allowed on page 1 only. Every other page, and the
right-hand sign-in box on page 1, keeps the product voice above. The copy review (CR-019) treats
those three lines as exempt from this section.

All wording in this note goes through the copy review before the demo (CR-019).

### 1.7 Signed out, wrong role, not found, server error

| Case | What happens | Words |
|---|---|---|
| Not signed in, any page | Redirect to `/sign-in` | — |
| No access (403): the General Partner opens a specialist page or sends a specialist form | 403 page in the shared frame | H1 **"You don't have access to this"**. Line: **"This page is for the compliance specialist. You are signed in as the General Partner, so you can view the published calendar only."** One link back (see below). Recorded in the audit log as a `FORBIDDEN` refusal |
| Not found (404): a review number or address that does not exist | 404 page in the shared frame | H1 **"We can't find that page"**. Line: **"The address may be wrong, or there is no review with this number."** One link back (see below). Not recorded in the audit log |
| Unexpected server error, specialist | Plain page | **"Something went wrong on the server. Nothing was changed by this request. Go back to Filing rules and try again."** |
| Unexpected server error, GP | Plain page, no working content (CR-012) | **"The calendar could not be shown just now. Try again in a few minutes."** |

**403 and 404 pages (H-026, gap d).** No new layout: the shared frame (§1.3), then the H1, one
line and one link, as a plain page. No status, no review content, no auto-refresh.

- **The link back** reads **"Go to Filing rules"** for the specialist. For the General Partner it
  reads **"Go to the calendar"**, because Filing rules would refuse them again (see Open Question
  17).
- **Role is checked before the address.** A General Partner who opens
  `/specialist/runs/{run_id}` always gets the 403 page, whether or not that review exists, so the
  page never tells them which reviews exist.
- `<title>`: `No access · ACME Compliance calendar (demo)` / `Page not found · ACME Compliance
  calendar (demo)`.

### 1.8 Words on screen and words in the documents

The documents, routes, codes and tests keep their internal names. Only what a user reads changes.

| In the documents and code | On screen | Decision |
|---|---|---|
| Run, "Run 4" | Review, "Review 4" | U2, H-014 |
| Agents; Stage A / B / C | "AI" as the actor ("AI drafts the rules"). On the step 1 page only: "the first AI" (extract) and "a second, separate AI" (verify) | U3, H-015 |
| Stage A, G1, Stage B + G2, Stage C + G3 | Step 1 · AI drafts the rules; Step 2 · You check the rules; Step 3 · You confirm what applies; Step 4 · You publish the calendar | U4, H-016 |
| Row (at G1 and in the G3 rejected list) | Rule ("Rule 3 of 7", "Approve rule", "Go to rule 7") | U4, H-009 |
| GP | "General Partner / Fund Manager" as the role name (sign-in, sidebar); "the General Partner" in other text | U6, H-018 |
| Precautionary | "May not be required" | U5, H-017 |
| Decline (G3) | "Close without publishing" | U10, H-022 |
| Roll forward / No roll / Not confirmed | Move to the following working day / Move to the preceding working day / Keep the date | U9, H-021 |
| Run list | Filing rules | U7, H-019 |
| Obligations calendar | Compliance calendar | U1, H-013 |

"Stand-in agents" stays as the label's exact text (CR-030), even though other text says "AI".

---

## 2. Flow

```text
Sign-in ─┬─ specialist ─> Filing rules ─(Start a new review)─> Review status [step 1: AI drafts, auto-refresh]
         │                                                    │
         │                                                    v
         │             Check the rules (G1) ─(Finish checking)─> Review status [step 3: AI checks what applies]
         │                                                                    │
         │                                                                    v
         │             Confirm what applies (G2) ─(Finish and calculate dates)─> Review status [step 4: dates]
         │                                                                    │
         │                                                                    v
         │             Publish (G3) ─(Publish calendar)─> Review status [Published] ─> Calendar
         │                          └(Close without publishing)─> Review status [Closed without publishing]
         │   (At any step that waits for you: Abandon on review status → Review status [Abandoned])
         │
         └─ GP ─────────> Calendar ("being prepared" message, or the published calendar)
```

After every form: on success, redirect to the page that shows the result; on refusal, the same
page again with the refusal message (§3, §4 of the SAD).

---

## 3. The seven pages

### Page 1 · Sign-in (`/sign-in`)

**Purpose.** Choose one of two mock identities. **Who:** anyone. `/` redirects here, or to the
role's first page when already signed in.

**On screen, in order**

1. No sidebar (no identity, no navigation). The page has two panels side by side: the ivory
   **left-hand panel** (see "Left-hand panel" below), then the sign-in box with everything in
   items 2 to 5. Items 2 to 5 sit in the right-hand box.
2. H1 **"Sign in to the demo"**
3. Line: **"Choose a role to explore the demo with mock data. You don't need a password."** This
   line carries the demo label on this page (UX-001), since there is no sidebar.
4. Two buttons, each its own form (`POST /sign-in`), equal weight, nothing preselected:
   - **"Sign in as the compliance specialist"**, with hint below: "Checks the rules AI drafts,
     then publishes the calendar."
   - **"Sign in as the General Partner / Fund Manager"** (U6, H-018), with hint below: "Sees the
     published calendar only. Cannot change anything."
5. Line: **"The fund and the firm are fictional."**

**Left-hand panel** (operator decision, 2026-11-17, option C, H-037; layout and look from
`docs/prototype/sign-in.html`). Portfolio voice is allowed here only (§1.6). In order:

- The **"acme"** wordmark.
- **Three decorative cards**, hidden from screen readers (`aria-hidden`) and **hidden below 1100 px**
  so the sign-in box comes first on small screens. They carry no information the page depends on:
  1. A dot calendar headed **"2027 filing calendar"**, with **"Fictional fund · 22 deadlines"**
     and the key **"Due date"** · **"May not be required"**. **No per-date labels**, so the
     evaluation answer key is not shipped in the app.
  2. A two-bar comparison: tag **"Sources disagree"**; **"The law"** 6 mo against **"A practitioner
     guide"** 4 mo.
  3. A ring: **"6 of 7"** **"rules approved by a person. One was rejected."**
- The tagline, **"AI drafts. People approve."** It is a paragraph, not a heading, so "Sign in to the
  demo" stays the page's one H1.
- Two first-person paragraphs, word for word: **"I designed this tool to read fund regulations and
  draft a compliance calendar: who must file what, and by when. A wrong date has real consequences,
  so I started from one question: where can I trust AI, and where can't I?"** and **"My approach is:
  decide what must never go wrong, make code and people responsible for that, and let AI speed up
  everything else. Then scope ruthlessly to what can actually ship."**

The panel has no links, buttons or form fields. The right-hand box keeps the words in items 2 to 5
exactly as written.

**Actions**

| Action | Then |
|---|---|
| Sign in as the compliance specialist | Redirect to `/specialist/runs` (Filing rules) |
| Sign in as the General Partner / Fund Manager | Redirect to `/calendar` |
| Sign out (any page) | Redirect to `/sign-in` |

**States.** Only the default state. A malformed request gets `VALIDATION` (§5).

---

### Page 2 · Filing rules: the review list (`/specialist/runs`)

**Purpose.** See every review and its state; start a new review. **Who:** specialist. The route
keeps its name; on screen this is **"Filing rules"** (U2, U7).

**On screen, in order**

1. Shared frame; "Filing rules" is the current navigation item.
2. Small label **"Regulatory framework"**, then H1 **"Luxembourg UCI Part II"**.
3. **Active-review notice** (only when a review is `ACTIVE`): label **"Waiting for you"** at a
   step, or **"AI is working"** while AI or code works; then "**Review {n}:** {status words}." and
   one primary link: **"Continue checking"** (at a step) or **"Open review {n}"** (while working).
4. **Reviews** (H2): a real table, newest first.

   | Column | Content |
   |---|---|
   | Review | "Review 4", links to review status |
   | Started | "Fri 13 Nov 2026, 14:00" |
   | Demo rule | "On" or "Off" |
   | Status | Status words (§1.5) |
   | Ended because | For `FAILED`, the reason in words (page 3); for `ABANDONED` and `DECLINED`, the first line of the written reason; otherwise empty |

5. **Start a new review** (under the table), one form (`POST /specialist/runs`):
   - Text: "Fund: **Bramblegate Credit Opportunities SICAV** (fictional, `FND-DEMO-01`)".
   - Text: "Agents: **stand-in agents** (fixed test outputs, no AI model is called)" or
     "Agents: **real model**", from the server setting (CR-030).
   - Checkbox, **unticked**: **"Add the demo rule (rule 7)"**. Hint: "Adds one rule that looks
     plausible but must not be approved. Use it only to show the review in a demo. The choice is
     recorded in the audit log." The built app keeps this switch; the mock-ups leave it out (H-005).
   - Checkbox, **unticked**, under the demo rule one (in sad.md: DL-52, DL-53; built in B13a, D12):
     **"Make step 1 fail (demo)"**. Hint: "Shows what a failed review looks like. Only with
     stand-in agents." Ticking it is recorded in the audit log, like the demo rule switch. What it
     does: see page 3, "Failure demo".
     - **Shown only when the server runs stand-in agents** (`AGENTS_MODE=stand_in`). With the real
       model the checkbox is not in the page at all. This is the one option on a form that depends
       on the server setting, like the "Agents:" line above it; it is not a hidden button (§1.2),
       because the option does not exist with the real model. The server still checks: a start
       with the box ticked under the real model, or on an evaluation run, is refused with
       `VALIDATION` (§5) and nothing starts.
     - The General Partner never sees this form or the label it leaves on a review.
   - Button: **"Start a new review"**.
   - The form and its button are **always shown**, even while a review is in progress (H-009).
     The server refuses a second review (`RUN_ACTIVE`, §5): the reason is shown beside the button,
     the top of the page shows the short line, and the attempt is recorded in the audit log.

**States**

| State | What shows |
|---|---|
| Empty (no reviews yet) | Table replaced by: **"No reviews yet. Start the first review below."** |
| Populated | Table as above |
| Review active | Active-review notice at the top |
| No review active (the last one was published, closed without publishing, abandoned or failed) | No active-review notice. "Start a new review" is accepted again: the server no longer refuses it with `RUN_ACTIVE` |
| Refused (`RUN_ACTIVE`) | Same page. Beside "Start a new review": the full `RUN_ACTIVE` sentence (§5). At the top: **"Not done. A new review can't start while review {n} is in progress."** and the link **"Go to 'Start a new review'"** |
| Refused (`VALIDATION`) | Same page, the full sentence at the top and next to "Start a new review" |

**Actions**

| Action | Then |
|---|---|
| Start a new review | Success: redirect to that review's status page (step 1, AI drafting). Refused: §5 |
| Open a review | Go to its review status page |

---

### Page 3 · Review status (`/specialist/runs/{run_id}`)

**Purpose.** The only place the specialist waits. Shows where the review is, each item the AI works on, the cost,
and what to do next. **Who:** specialist. **No re-run of a whole review.** The one exception is
**Retry** of the failed step (sad.md rule 10, DL-51; built in B13b, see "Failed review" below).

**On screen, in order**

1. Shared frame; breadcrumb ending **"Review {n}"**.
2. H1 for the state (see the states table), with the run labels (Stand-in agents, Demo rule on, Failure demo on).
3. Stepper (§1.4).
4. **Status line** (large text): the status words (§1.5) plus the sentence for the state below.
5. **Next step** (only at a step that waits for the specialist, or when ended): one primary link
   (see states).
6. **Refresh controls** (only while AI or code is working, see below).
7. **"What the AI is working on"**, as a real table per group: Item · Status (the column header is
   visually hidden). Status words: **"Waiting"**, **"Running"**, **"Done"**, **"Failed"**.
   "Unit" is the backend's word for one row (the `units` table, `STAND_IN_UNIT_PAUSE_S`). It is
   never shown to the specialist: operator decision 2026-11-20, because "unit" is engineering
   jargon (and means a fund unit in this domain). Each row is already named for what it is.
   - While step 1 runs, and in its record afterwards, two groups, each with its one-line
     intro. This is the **only** page that names the two AI roles (U3, H-015):
     - **"Drafting the rules"**: "The first AI reads each source and writes a rule, quoting the
       exact words it relied on." One item per source document, for example "CSSF Circular
       15/627".
     - **"Checking the drafts"**: "A second, separate AI compares every draft with all the sources
       and tells you where they disagree. It never changes a rule." One item per rule, for example
       "Audited annual report".
   - Step 3: **"Checking what applies"**, with the intro "One line per approved rule."
   - Step 4: **"Working out the dates"**, one item ("Code, no AI model").
   - Any group the server sends that is not one of these four: **"Other items"**.
   - Nothing has started yet: "Nothing has started yet."
8. **Cost so far**: "Model cost so far: **US$0.00**." For stand-in reviews add: "(stand-in agents
   make no model calls)". For real reviews add: "The review stops at US$2.50."
9. Review details: "Started Fri 13 Nov 2026, 14:00, by Compliance specialist (mock). Fund
   FND-DEMO-01."
10. **Abandon this review** (H2), only when the review waits for the specialist (see below).

**Automatic refresh (running only).** While the phase is `A_RUNNING`, `B_RUNNING` or `C_RUNNING`,
the page reloads itself every 3 seconds (§3 Freshness). Next to the status line:

- Beside the status words: **"Last updated at 14:02:09."**, the time the server drew the page,
  with seconds so each 3-second refresh is visible (operator, 2026-11-17).
- Text: **"This page refreshes every 3 seconds while AI is working."** (In step 4: "… while the
  dates are worked out.")
- Link: **"Refresh now"** (reloads the same page).
- Link: **"Stop automatic refresh"** (reloads the page with refresh off, for example
  `?refresh=off`; a display choice in the URL, not stored anywhere).

With refresh off: **"Automatic refresh is off."** Links: **"Refresh now"** · **"Turn automatic
refresh back on"**. "Refresh now" keeps refresh off.

**Stand-in agents finish one item at a time (DL-54).** With stand-in agents, each item takes about
one second (`STAND_IN_UNIT_PAUSE_S`), so the table fills in item by item across the 3-second
refreshes: "Waiting", then "Running", then "Done". At the default, step 1 takes about 12 seconds and step 3
about 6 (sad.md §4). The dates step is code with no agent, so it has no pause. Real agents have
no pause. This changes no wording and no
control on the page; it only means the "The items below finish one by one" sentence is true on screen.

At a step that waits for the specialist, or in an ended state, the page does not refresh and these
controls are not shown.

**States and their words**

| State | H1 | Status line sentence | Next step link |
|---|---|---|---|
| `A_RUNNING` | **"Nothing for you to do yet"** | "AI is drafting the rules and checking each one against the sources. You check the rules when it finishes. The items below finish one by one." | — |
| `AT_G1` | **"The rules are ready for you to check"** | "AI drafted **{n} rules** and checked each one against the sources. Nothing reaches the calendar until you approve it." | **"Check the rules"** → page 4 |
| `B_RUNNING` | **"Nothing for you to do yet"** | "You've finished checking the rules. AI is now checking whether each approved rule applies to the fund." | — |
| `AT_G2` | **"Ready for you to confirm what applies"** | "AI checked **{n} rules** against the fund's facts. **{u} of them** need your decision because AI can't tell." | **"Confirm what applies"** → page 5 |
| `C_RUNNING` | **"Nothing for you to do yet"** | "You've confirmed what applies. The dates are being worked out by code. This takes a few seconds." | — |
| `AT_G3` | **"The calendar is ready to check"** | "The calendar is ready: **{n} dates**." | **"Check the calendar and publish"** → page 6 |
| `COMPLETED` | **"Published"** | "Published on {date} at {time}. The General Partner now sees this calendar." | **"See the calendar as the General Partner sees it"** → `/calendar` |
| `DECLINED` | **"Closed without publishing"** | "Closed without publishing on {date} at {time}. Nothing was published. The General Partner still sees what they saw before." Then: "What needs to change: {reason}" | **"Go to Filing rules"** |
| `ABANDONED` | **"Abandoned"** | "Abandoned at step {k} ({step name}) on {date} at {time}. Nothing was published, and the decisions made so far stay in the audit log." Then: "Your reason: {reason}" | **"Go to Filing rules"** |
| `FAILED` | **"This review failed"** | Two versions, see "Failed review" below: without Retry (until B13b is built, or if it is dropped) and with Retry (B13b) | Without Retry: the link **"Start a new review from Filing rules"**. With Retry: the **"Retry step {k}"** form, then the link **"Or start a new review from Filing rules"** |

**Failure reason sentences** (one for each of the nine reasons in §4; number 2 is retired.
`demo failure` is DL-52; `unexpected error` and `call limit` are DL-58, H-092, H-093):

| Reason code | Sentence |
|---|---|
| `model service` | "The model service did not answer in time, or returned an error, twice" |
| `stage time limit` | "This step took longer than its time limit" |
| `invalid output` | "The AI returned output in the wrong format, so it was not used" |
| `cost cap` | "The review reached its cost limit of US$2.50" |
| `service restarted` | "The application restarted while AI was working" |
| `calendar generation` | "The dates could not be worked out into one complete calendar" |
| `demo failure` (reason 8, DL-52) | "This step failed on purpose, for the demo only, because "Make step 1 fail (demo)" was ticked when the review started. Nothing else went wrong" |
| `unexpected error` (reason 9, DL-58) | "Something went wrong that the app did not expect, so this step was stopped and nothing from it was saved" |
| `call limit` (reason 10, DL-58) | "The limit on real model calls for this kind of review was reached, so no further call was made" |

Like the others, these have no final full stop, because the status line adds one. **The page shows
the sentence only.** For `unexpected error` it never shows the error's own name or message (the
audit entry keeps the class name only, DL-58), so the page does not say what went wrong, only that
something did. Read in the status line, both sentences fit without change ("…while working on
{item}. Something went wrong that the app did not expect, so this step was stopped and nothing
from it was saved. Nothing moved forward…"). `call limit` can only appear with real agents; with
stand-in agents no real call is made.

**Abandon this review** (only in `AT_G1`, `AT_G2`, `AT_G3`). One form,
`POST /specialist/runs/{run_id}/abandon`, with the run version as a hidden field:

- Text: **"Abandoning ends this review. Nothing is published and nothing is undone: decisions made
  so far stay in the audit log. You can then start a new review. Use this, for example, after
  rejecting a rule by mistake."**
- Field: **"Reason for abandoning"** (multi-line). Hint: "Recorded in the audit log. Specialists
  only."
- Button: **"Abandon review"** (secondary style, not the primary colour).

While AI or code is working the form is not shown; instead: **"You can abandon this review once it
is waiting for you. While AI is working, it always finishes by itself."** If an old page sends the
form anyway, the server answers `RUN_STAGE_RUNNING` (§5).

**After abandoning** (H-026, gap b). The page reloads in the `ABANDONED` state (states table
above) and becomes a closed review (below). The abandon is recorded in the audit log with who,
when, the step it was at and the written reason (W-19a). On Filing rules the review shows
**"Abandoned"** with the first line of the reason under "Ended because", the active-review notice
goes, and **"Start a new review"** is accepted again. Abandon is offered only while the review
waits for the specialist at a step (SAD run-state rule 8); while AI or code works, the line above
explains why it is not offered.

#### Failed review (H-026, gap a)

**Reviewed and approved by the operator, 2026-11-16.** This approves the design of this section
only. Retry is now in the SAD (D10 resolved; rule 10, DL-51) and is built in B13b. The note's
overall approval status was set to `approved` later the same day.

**What the specialist sees** when a step fails, top to bottom, on this page:

1. H1 **"This review failed"**, with the status tag **"Failed"** (word, problem tone).
2. Stepper: earlier steps "Done", the failed step **"Failed"**, later steps "Not started" (§1.4).
3. Status line, in plain English. The reason sentence comes from the table above. The table
   marks that item **"Failed"**.
   - Without Retry: **"This review failed at step {k} ({step name}), while working on {item}. {reason
     sentence}. Nothing moved forward. Decisions you already made stay in the audit log."**
   - With Retry: **"This review failed at step {k} ({step name}), while working on {item}. {reason
     sentence}. Nothing moved forward, and the decisions you already made are kept."**
4. Automatic refresh stops (the review is no longer working).
5. What to do next: one of the two versions below, depending on whether Retry (B13b) is built.

**Without Retry.** This is the page B5 builds, and it stays the page if B13b is dropped (DL-54).
The failed page shows only the link **"Start a new review from Filing rules"** (primary link, to
page 2 at "Start a new review"). The Retry form is **left out of the page**: not hidden, not
disabled, not greyed out, and there is no "coming soon" (§1.2). A failure-demo review (B13a)
ends on this page until B13b is built, because the failure demo does not need Retry (DL-54).

**With Retry (B13b).** The page shows the Retry form (below) and, under it, the link **"Or start
a new review from Filing rules"**. Nothing else on the page changes. B13b adds the form to the
page B5 built; it does not rebuild the page.

> ✅ **Retry: kept by the operator (2026-11-16, Open Question 18) and now in the SAD.**
> `sad.md` run-state rule 10 and CR-032 (DL-51) define it: the route
> `POST /specialist/runs/{run_id}/retry`, the guard, the refusal codes, the audit entry and what
> happens to outputs the failed stage already stored. Those rules are in `sad.md`, not here.
> Build from `sad.md`. Retry is block **B13b**, built after B9 and dropped next after B6 (DL-54).
> If it is dropped, use "Without Retry" above and UX-022.

**Retry** (sad.md rule 10, DL-51). One form, under the status line, with the run version as a
hidden field. The route is `POST /specialist/runs/{run_id}/retry`.

- H2 **"Try this step again"**.
- Text: **"Retry runs step {k} again from its start. Your decisions on earlier steps are kept and
  are not asked again. The retry is recorded in the audit log."** For a failure at step 1:
  **"Retry runs step 1 again from its start. AI drafts every rule again."**
- Button: **"Retry step {k}"** (primary). Shown on every failed review, never hidden or disabled
  (§1.2); the server decides whether it is allowed.
- Under it, the link **"Or start a new review from Filing rules"**.

| What Retry does | Detail |
|---|---|
| Restarts | Only the stage that failed: AI drafting (step 1), AI checking what applies (start of step 3), or working out the dates (start of step 4) |
| Keeps | Every decision already recorded: the rule decisions from step 2 if the failure was at step 3 or 4, and the answers from step 3 if it was at step 4. They are not shown again as forms |
| Redoes | The failed stage's work, from its start |
| Then | Redirect to this page in the running state for that stage ("Nothing for you to do yet"), with automatic refresh on and the step "In progress" |
| Records | One audit entry: who, when, the step retried and the failure it follows. Every refusal is also recorded |
| Cost | Not reset. The retry's calls count towards the same US$2.50 limit (CR-017) |
| How often | Once per step. A step that fails again after its retry cannot be retried again; the specialist starts a new review. Each later step has its own single retry |
| Refused when | Another review is in progress (`RUN_ACTIVE`), the page is out of date (`VERSION_MISMATCH`), the review is not failed (`RUN_NOT_FAILED`), the step was already retried (`RETRY_LIMIT_REACHED`), or the review failed on the **cost limit**, on **working out the dates** (`calendar generation`) or on the **real model call limit** (`call limit`, DL-58), is an evaluation run, or a newer review has been started since (`RETRY_NOT_ALLOWED`; the sentence says which). Sentences: §5 (Open Question 24 proposed; Open Question 25 closed) |
| After `unexpected error` | Retry is allowed, once, like any reason not excluded above (DL-58). Nothing from the stopped step was saved, so it restarts from its start as the table says |

**What page 3 shows after `call limit`.** Nothing different from any other failed review: the
H1, the stepper, the status line with the sentence above, and (with Retry built) the "Retry step
{k}" button, shown and enabled as on every failed review (§1.2, the server decides). Clicking it is
refused with `RETRY_NOT_ALLOWED` and the sentence in §5, exactly as for the cost limit. There is no
extra page, banner or disabled button. One thing differs from the cost limit: the call limit
counts an activity's calls across both databases, not one review's, so **a new review would reach
the same limit**. The refusal sentence in §5 therefore does not send the specialist to Filing
rules for this reason (Open Question 25).

#### Failure demo (in sad.md: DL-52, CR-033; built in B13a, D12)

Stand-in agents never fail, so without this the failed review cannot be shown in a demo. **It does
not need Retry** (DL-54): it is built in B13a, straight after the stand-in agents, and is kept.

- **Start:** the specialist ticks **"Make step 1 fail (demo)"** on page 2 and starts the review.
  The audit log records the switch. The review shows the label **"Failure demo on"** next to the
  H1 on every page about it (§1.3).
- **What happens:** step 1 starts as usual. Its first item (the first source document) fails, on
  the first attempt only, with the reason `demo failure`; the items after it stay "Waiting" (the
  server starts item 1 alone first, so the others never start). The review ends as **Failed** at
  step 1. The switch exists only with stand-in agents: in real mode the checkbox is not on the
  form (§3 page 2).
- **What the specialist sees:** the normal "Failed review" screen above, nothing special, with
  the reason sentence: **"This step failed on purpose, for the demo only, because "Make step 1
  fail (demo)" was ticked when the review started. Nothing else went wrong."** On Filing rules the
  review shows **"Failed"**, and the same sentence under "Ended because".
- **Without Retry (B13a alone, or if B13b is dropped):** the specialist uses "Start a new review
  from Filing rules", leaves the box unticked, and the new review runs normally. The demo then
  shows the error but not the retry.
- **With Retry (B13b built):** the switch makes step 1 fail **once** (operator, 2026-11-16, Open
  Question 21). "Retry step 1" then runs step 1 normally, so one review shows both the error and
  the retry.
- **Never** with the real model, never on an evaluation run, never seen by the General Partner.
  It changes nothing on any published calendar.

#### Closed review: read-only (H-026, gap c)

A review is closed once it is **Published** (`COMPLETED`), **Closed without publishing**
(`DECLINED`) or **Abandoned** (`ABANDONED`). A failed review is also read-only, apart from Retry
(B13b).

- **Review status**: the state's H1 and sentence (states table above), the stepper (§1.4), the
  items and cost as a record, and one link (next-step column). No refresh controls, no abandon
  form.
- **The step pages** (4, 5 and 6): reached steps show their read-only record (each page's "After"
  state: every decision, no forms, no finish button). A step the review never reached shows one
  line, **"This review ended before this step."**, and the link **"Go to the review status
  page"**.
- **No form anywhere** on a closed review. A form sent from an old page is refused with
  `RUN_NOT_ACTIVE` (§5) and the refusal is recorded in the audit log.
- **The General Partner** sees none of it. Their calendar changes only when a review is published
  (page 7).

**Actions**

| Action | Then |
|---|---|
| Refresh now / Stop / Turn back on | Same page, refresh on or off |
| Next step link | The step page, or the calendar, or Filing rules |
| Abandon review | Success: same page, `ABANDONED` state. Refused: `REASON_REQUIRED`, `VERSION_MISMATCH`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE` |
| Retry step {k} (sad.md rule 10, DL-51; B13b, left out if B13b is dropped) | Success: same page, running state for that stage. Refused: `RUN_ACTIVE`, `VERSION_MISMATCH`, `RUN_NOT_FAILED`, `RETRY_LIMIT_REACHED`, `RETRY_NOT_ALLOWED` (see "Failed review" above) |

---

### Page 4 · Check the rules (G1) (`/specialist/runs/{run_id}/g1`)

**Purpose.** Decide each extracted row (on screen, a "rule") once: approve it (setting what
happens on a weekend or holiday, and who files when the source is silent) or reject it with a
reason. **Who:** specialist.

**Not on this page** (not in the Build card): editing a rule, adding a rule, reopening a decided
rule (DL-22), choosing which source a rule follows when two disagree (DL-22, H-008), bulk approve.
See §9.

**On screen, in order**

1. Shared frame; breadcrumb; H1 **"Check the rules"**; run labels; stepper (step 2 is "Your
   turn").
2. Lead: **"AI drafted {n} rules from the sources. Check each one against the words it came from,
   then approve or reject it. Nothing reaches the calendar until you approve it."** Then: **"Each
   decision is recorded with your name and the time, and cannot be changed in this review."**
3. **Summary cards** (a row of four, values from the server): **Rules** {n} · **Decided** {d} ·
   **To decide** {n−d} · **Checker flags** {f}. There is no separate progress sentence (operator
   decision, 2026-11-13).
4. **Rule index** (H2 **"Rules"**, a real table, one line per rule, each rule cell a jump link to
   its card). Columns: **Rule** ("Rule 3 · OBL-03") · **Obligation** ("Audited annual report") ·
   **Needs attention** · **Status** (**"To decide"**, **"Approved"**, **"Rejected"**, or
   **"Approval blocked"** on the demo rule after a refused approval, H-007).
   "Needs attention" shows, in words, **"Sources disagree"** or **"Checker flag"** (a flag),
   **"Quote check failed"**, **"Depends on open question OQ-7"** or **"Demo"**, and is empty
   otherwise. This gives the specialist the shape of the work in one glance.
5. **One card per rule** (shared "row card" part, §3 of the SAD), each with its own `id` anchor
   (`#row-{i}`), in this order:
   1. H2: "**Rule {i} of {n}**: {obligation summary}" plus tags: **"Demo"** (planted row),
      **"Sources disagree"** / **"Checker flag"**, **"Quote check failed"**, **"Depends on open
      question OQ-7"** as applicable, and the status tag (**"To decide"**, or **"Approval
      blocked"** on the demo rule after a refused approval).
   2. **Quote** (blockquote): the word-for-word quote. Caption: "Quote from paragraph {para_id}".
      On wide screens the card has two columns (the mock-up's evidence layout), each with a small
      heading: **"The source says"** over the quote and its check and paragraph, and **"The AI's
      reading"** over the rule fields (item 6). The reading order is unchanged: quote → check →
      paragraph → flags → fields. (Wording built from the mock-ups; confirmed 2026-11-17.)
   3. **Quote check**, one line, on **every** rule, the demo rule included (D5, operator decision
      2026-11-14; SAD §3 page 4; H-030):
      - pass: **"Quote check: passed. The quote appears word for word in paragraph {para_id}."**
      - fail: **"Quote check: failed. The quote does not appear word for word in paragraph
        {para_id}. This rule can only be rejected."**
      - **Demo rule** (CR-029, T-DEMO-1): its quote passes by design, so it shows the "passed"
        line like any other rule. There is still no "quote found" tag (A4, H-007). Before the click
        its status tag reads **"To decide"**; after a refused approval it reads **"Approval
        blocked"**, matching the refusal.
   4. **Cited paragraph** (full text, headed "Paragraph {para_id}, {source document}").
   5. **Flags** (shared "flag" part), one box per flag, each with both texts (DL-03):
      - Heading: **"Flagged by the AI checker: inside the same document"** (`internal`) or
        **"Flagged by the AI checker: two sources disagree"** (`cross_source`).
      - One line: **"The checker points out disagreements but never settles them. Approve it with
        a reason despite the flag, or reject it with a reason."**
      - "**The rule says:** {row text}"
      - "**The source says:** {source text}, paragraph {id}"
      - Both quotes are read-only. There is no control to choose which source the rule follows
        (H-008, post-MVP).
      - If no flag: **"No checker flags."** (so absence is stated, not implied)
   6. **Rule fields** (definition list): What must be done · Frequency · Due relative to · Offset ·
      Recipient · **Who files, as the source says** (a party, or "Not stated in source") ·
      **Weekend or holiday, as the source says** ("Following working day", "Preceding working
      day", "Keep the date" or "Not stated").
   7. **Open question mark** (only for rows the server marks, MVP: `OBL-02`): **"What happens on a
      weekend or holiday for this rule depends on open question OQ-7, which is not yet answered.
      Nothing is chosen for you. Whatever you choose, the dates will carry the OQ-7 mark when you
      publish."**
   8. **Decision** (only while the rule is undecided): one answer-first form (§4 "Decision form";
      A9 reversed, H-011, H-028), `POST /specialist/rows/{row_id}/decision` with the row version as
      a hidden field.

      - Radio question **"What's your decision on this rule?"** (named `decision`, nothing
        chosen): **"Approve"** · **"Reject"**. Only the chosen answer's fields and button show
        below it; where `:has()` is unsupported, both answers' fields show.

      **If "Approve" is chosen:**
      - Radio group (nothing chosen), legend **"If the deadline falls on a weekend or holiday
        (choose one to approve)"** (U9, H-021). The options, exactly and in this order:
        **"Move to the following working day"** · **"Move to the preceding working day"** ·
        **"Keep the date"**. There is no "not confirmed" option. If none is chosen, the server
        refuses with `BUSINESS_DAY_RULE_REQUIRED` (§5).
      - **"Who files this? The source doesn't say."** (radio group, nothing chosen), **only when
        the source says "Not stated in source"**. The options, exactly and in this order:
        **"AIFM"** · **"Fund administrator"** · **"Auditor"** · **"Local reporting agent
        (Spain)"** · **"Tax advisor"** · **"Not known"**. Hint: "Choose the party, or 'Not
        known'. The compliance specialist and the General Partner are not filing parties."
      - **"Why are you approving it although the checker flagged it?"** (multi-line), **only when
        the rule has a flag**, field name `approve_reason`. Hint: "Required because the checker
        raised a flag. Saved in the audit log with your name and the time. Specialists only."
      - Button: **"Approve rule"** (primary).

      **If "Reject" is chosen:**
      - **"Why are you rejecting it?"** (multi-line), field name `reject_reason`. Hint:
        "Required. If you reject it, no filing dates are created from this rule. Shown again when
        you publish and kept in the audit log. Specialists only."
      - Button: **"Reject rule"** (secondary).

      The server reads only the chosen answer's fields: on Reject it ignores any weekend-or-holiday
      or "who files" choice left over from Approve (SAD §4, DL-48). Submitting with no answer chosen
      is refused with `VALIDATION` (§5).

      The demo rule and a quote-check-failed rule show **exactly the same form**: both answers, and
      after choosing "Approve" its button is visible and active, with nothing preselected. The
      server refuses the approval (§5) on the page, never as a browser pop-up, and records the
      attempt in the audit log (H-009).
   9. **Decided** (replaces the form once decided):
      - "**Approved** by Compliance specialist (mock) at 14:02. Weekend or holiday: move to the
        following working day. Who files: Fund administrator." (+ "Reason: {reason}" if over a
        flag)
      - "**Rejected** by Compliance specialist (mock) at 14:05. Reason: {reason}"
      - Link: **"Next rule to decide"** (to the next undecided card), or **"All rules are
        decided. Finish checking"** (to the finish section).
6. **Check nothing was missed: paragraphs that no rule uses** (H2, the coverage view, W-03b):
   - Intro: **"These {k} paragraphs were loaded but no approved or undecided rule uses them. This
     list does not say whether they contain obligations. If one does, the review missed it: reject
     or finish as usual, then start a new review. You will see this list again when you
     publish."**
   - A real table: Paragraph ID · Source document · Text.
7. **Finish checking** (H2: **"{x} rules left to decide"**, or **"All rules decided"**), one form,
   `POST /specialist/runs/{run_id}/g1/complete`, with the run version:
   - Text: **"Decide every rule to move on. AI then works out which rules apply to the fund. You
     cannot change rule decisions after this."**
   - Button: **"Finish checking"** (primary). Always shown; the server refuses it while a rule is
     undecided (`GATE_INCOMPLETE`).
8. Link at the bottom: **"Abandon this review"** → review status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G1 (`A_RUNNING`) | Short page: **"AI is still drafting the rules. They will be here when it finishes."** Link: **"Watch progress on the review status page"** |
| At G1, rules to decide | Full page as above |
| At G1, all decided | Every card shows its decision; the summary cards show **To decide 0**; the finish section is the next thing to do |
| Refused, about one rule | Same page, landing on that rule's card: the full message sits inside the card, and the top shows the short line and **"Go to rule {i}"** (§5) |
| Refused, about the page (`GATE_INCOMPLETE`, `VERSION_MISMATCH`, …) | Same page; the full message at the top and next to the button it concerns |
| After G1 (`B_RUNNING` onward, or ended) | Read-only record: every card shows its decision, no forms, no finish button. Line under H1: **"You've finished checking the rules. This is the record of the decisions."** |

**After each action**

| Action | Then |
|---|---|
| Approve rule / Reject rule | Success: redirect to G1 at the **next rule still to decide** (`#row-{i}` of that rule), wrapping round to the first undecided rule if the one just decided was the last; when every rule is decided, to the "Finish checking" section. The rule just decided still shows its decision and the "Next rule to decide" link (operator decision, 2026-11-17, H-043). Refusals are different: they land on the rule they are about (§5) |
| Approve on the demo rule | Refused: same page, landing on the demo rule card (`#row-{i}`). The `DEMO_ROW_NOT_APPROVABLE` sentence sits in the card; its status tag changes to "Approval blocked"; the top shows the short line and "Go to rule {i}". The rule stays undecided, nothing is preselected, and the refusal is recorded in the audit log. The specialist then uses Reject |
| Finish checking | Success: redirect to review status (step 3, AI checking what applies, auto-refresh) |

**Review-time budget (§7, 30 minutes from G1 open to G3 published).** Target about 2 minutes per
row, so G1 takes about 15 minutes for 7 rows. Supporting decisions:

- Everything a decision needs is on one card, in reading order: quote → check → paragraph → flags →
  fields → decision. No clicking away.
- After a decision the page lands on the next rule still to decide, so the specialist moves
  straight on without scrolling (H-043). The rule just decided keeps its link to the next one.
- No confirmation dialogs; the decision forms are already explicit.

---

### Page 5 · Confirm what applies (G2) (`/specialist/runs/{run_id}/g2`)

**Purpose.** For each approved rule, confirm AI's answer, overrule it with a reason, or decide
where AI can't tell ("unsure"). Every "unsure" must be decided. **Who:** specialist. Three
decisions, as in the SAD (§3 page 5, W-12): **confirm**, **override with a reason**, **decide an
"unsure"**.

**On screen, in order**

1. Shared frame; breadcrumb; H1 **"Confirm what applies"**; run labels; stepper (step 3 is "Your
   turn").
2. Lead: **"AI checked the {n} rules you approved against the fund's facts. Confirm each answer or
   overrule it. Where AI can't tell, you decide."**
3. **Progress**: "**{d} of {n} answers decided.** {u} where AI can't tell still to decide."
4. **Rule index** (jump links): "OBL-04 · Statistical report A01 (Spain) · **AI can't tell, to
   decide**". "Can't tell" answers are listed first in the index, so the hardest decisions are
   visible early. Cards keep the rule order.
5. **One card per answer**:
   1. H2: "{obligation summary}" with row ID.
   2. **AI's answer** (big, in words): **"AI: applies"**, **"AI: doesn't apply"** or **"AI: can't
      tell"**. "Can't tell" has its own visual treatment and the words, not colour alone.
   3. **AI's reasoning** (2 to 3 sentences), captioned **"Why AI says this"** (for "can't tell":
      **"Why AI couldn't decide"**).
   4. **Missing information** (can't tell only): "**What is missing:** {text}".
   5. **Cited facts** (real table, read-only): Fact ID · Fact · Value. Example row: "FACT-04 ·
      Registered for marketing in the second country · Unknown, not confirmed in fund records".
   6. **The rule** (collapsed under a `<details>` element, "Show the approved rule and quote"): the
      rule, quote and paragraph ID as approved at G1.
   7. **Decision** (undecided only). One answer-first form (§4 "Decision form"; A9 reversed,
      H-011, H-028), `POST /specialist/verdicts/{verdict_id}/decision` with the verdict version.
      A radio question named `decision` comes first, with nothing chosen; only the chosen answer's
      text, field and button show (all of them where `:has()` is unsupported). Each answer's reason
      field has its own name (`<answer>_reason`, SAD §4), and only the chosen answer's field is
      read. No answer chosen → `VALIDATION`.

      When AI said **"applies"** or **"doesn't apply"** (the ordinary path; H-026, gap e). No new
      layout: the same card and answer-first form as the "can't tell" case in
      `applicability.html`, with these two answers in place of its two:
      - Question: **"What's your answer on this rule?"**
      - **"Confirm: applies"** (or **"Confirm: doesn't apply"**): text **"If you confirm, the
        General Partner will read AI's reasoning above as the explanation."** (for "doesn't
        apply": **"If you confirm, this obligation is left off the calendar."**). No reason field.
        Button: **"Confirm: applies"** or **"Confirm: doesn't apply"**.
      - **"Overrule: doesn't apply"** (or **"Overrule: applies"**, the opposite of AI's): field
        **"Reason for overruling"** with the hint for that outcome (below). Button: **"Overrule:
        doesn't apply"** / **"Overrule: applies"**.
      - Neither answer is preselected or styled as the default. The server acts only on the
        chosen answer and reads only that answer's reason field.
      - Confirm needs no reason. Overrule without a reason is refused with `REASON_REQUIRED`
        (§5), shown inside the card; the typed text is kept and the answer is shown unchosen
        again.
      - Every decision, and every refusal, is recorded in the audit log with who and when.

      When AI **can't tell** (U5, H-017; `applicability.html`): no Confirm.
      - Question: **"Nobody has confirmed {the missing fact}. Should this rule go on the
        calendar?"**
      - **"Yes, add it until someone confirms"**: text **"Choose this if you can't confirm it.
        The filings are added to the calendar, each marked 'May not be required'."**; field
        **"Why are you adding it?"** with the "creates an entry" hint; button **"Add to the
        calendar"**.
      - **"No, leave it off"**: text **"Choose this only if you know it doesn't apply. No filings
        are added for this rule."**; field **"How do you know it doesn't apply?"** with the
        audit-only hint; button **"Leave it off"**.
      - Neither is preselected or styled as the default.

      **Reason hints depend on whether the decision creates a calendar entry** (W-17, SA-8). Each
      hint sits next to its field:

      | Decision | Creates an entry? | Hint next to the reason field |
      |---|---|---|
      | Overrule to **applies** | Yes | **"The General Partner will read this reason as the explanation for the entry. Write it for a non-lawyer: state the condition and the fact. No advice."** |
      | Can't tell, decided as **add it** ("May not be required") | Yes | Same as above |
      | Overrule to **doesn't apply** | No | **"This obligation will not be on the calendar, so the General Partner will not see this reason. It is kept in the audit log for specialists."** |
      | Can't tell, decided as **leave it off** | No | Same as above |
   8. **Decided** (replaces the form), one line per outcome, then the **"Next answer to
      decide"** link:

      | Outcome | Line | On the calendar? |
      |---|---|---|
      | Confirm: applies | "**Confirmed: applies** by Compliance specialist (mock) at 14:21." | Yes; the General Partner reads AI's reasoning as the "Why" |
      | Confirm: doesn't apply | "**Confirmed: doesn't apply** by … at 14:21." | No |
      | Overrule: applies | "**Overruled: applies** by … at 14:21. Reason: {reason}" | Yes; the General Partner reads your reason as the "Why" |
      | Overrule: doesn't apply | "**Overruled: doesn't apply** by … at 14:21. Reason: {reason}" | No; the reason stays in the audit log |
      | Can't tell → add it | "**Added, marked 'May not be required'** by … at 14:21. Reason: {reason}" | Yes, marked "May not be required" |
      | Can't tell → leave it off | "**Left off** by … at 14:21. Reason: {reason}" | No |
6. **Finish** (H2: **"{x} answers left to confirm"**, or **"All answers decided"**), one form,
   `POST /specialist/runs/{run_id}/g2/complete`, run version:
   - Text: **"Once you've confirmed them all, the dates are calculated by code. No AI works out a
     date. This takes a few seconds. You cannot change these decisions after this."**
   - Button: **"Finish and calculate dates"** (primary). Always shown.
7. Link: **"Abandon this review"** → review status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G2 | **"AI has not finished checking what applies. The answers will be here when it does."** Link to review status |
| At G2 | Full page |
| All decided | Progress **"All {n} answers decided."** |
| Refused | Same page, as §5: about one answer, land on its card with the short top line and "Go to rule {i}"; about the page, the full message at the top |
| After G2 | Read-only record, no forms. **"You've confirmed what applies. This is the record of the decisions."** |

The mock-ups design only the "AI can't tell" case. The ordinary confirm and overrule (item 7)
reuse that layout; this note sets their behaviour and words (H-026, gap e).

**After each action**

| Action | Then |
|---|---|
| Confirm / Overrule / Decide | Success: redirect to G2 at the **next card still to decide** (`#verdict-{i}` of that card), wrapping round to the first undecided card; when every card is decided, to the "Finish and calculate dates" section (operator decision, 2026-11-17, H-043). The card just decided still shows its decision. Refused (lands on the card the refusal is about, §5): `REASON_REQUIRED`, `ALREADY_DECIDED`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE`, `VALIDATION` |
| Finish and calculate dates | Success: redirect to review status (step 4, dates being worked out; usually ready within one refresh). Refused: `GATE_INCOMPLETE`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |

**Budget:** about 1 minute per verdict, 6 minutes for G2.

---

### Page 6 · Check the calendar and publish (G3) (`/specialist/runs/{run_id}/g3`)

**Purpose.** See the whole calendar and what was left out, then publish it all at once or close
the review without publishing, with a reason. **Who:** specialist.

**On screen, in order**

1. Shared frame; breadcrumb; H1 **"Check the calendar and publish"**; run labels; stepper (step 4
   is "Your turn").
2. Lead: **"These {n} dates were calculated from the rules you approved. Check them, read what was
   left out, then publish for the General Partner. Some marks are shown only to you."**
3. **Date conventions note** (DL-12, specialist version, a boxed note): **"Before anyone relies on
   these dates: the way deadlines are counted (for example, the day 'six months after year end'
   falls on) has not yet been checked against the legal texts. This does not stop you publishing.
   The General Partner sees a short note saying the same."**
4. **Calendar** (H2), a real table sorted by due date:

   | Column | Content |
   |---|---|
   | Due date | "Mon 11 Jan 2027" |
   | What | Obligation summary |
   | Who files | Party, or **"Not confirmed"** for "not known" |
   | Sent to | Recipient name |
   | Marks | Mark labels, in words (below). Empty when none |
   | Why (the General Partner sees this) | The GP-facing reason, plus "Source: paragraph {id}" |

   **Mark labels** (shared "mark label" part):
   - **"Moved off a weekend"**: "Moved from Sun 10 Jan to Mon 11 Jan (following working day)."
     or "… (preceding working day)." Only you see this.
   - **"May not be required"** (U5, H-017): "Added because nobody has confirmed it applies. The
     General Partner sees this label."
   - **"Depends on open question OQ-7"**: "What happens on a weekend or holiday depends on an
     unanswered question. The date is the same whether or not it moves." Only you see this.
   There is no "Rule not confirmed" mark any more: every approved rule has one of the three
   weekend-or-holiday choices (U9, H-021; Q1, H-024). Only "May not be required" reaches the
   General Partner view.
5. **What's not in this calendar** (H2), intro **"Read both lists before you publish."**, then two
   real tables:
   - **Rules you rejected**: Rule · Your reason. The demo rule appears here tagged **"Demo"**. If
     none: **"No rules were rejected."**
   - **Paragraphs no rule uses**: Paragraph ID · Source · What it says. Line: **"No approved rule
     uses these paragraphs. The calendar has nothing from them."** If none: **"None."**
6. **Decision**: one answer-first form (§4 "Decision form"; A9 reversed, H-011, H-028;
   `publish.html`), with the run version and the two ID lists exactly as shown above as hidden
   fields. Radio question **"Is this calendar ready for the General Partner?"** (named `decision`,
   nothing chosen): **"Yes, publish it"** · **"No, don't publish"**. Only the chosen answer's text,
   fields and button show (all of them where `:has()` is unsupported). **Each button posts to its
   own route with `formaction`**; the form's `decision` must match that route, or the server
   refuses with `VALIDATION`, and each route ignores the other answer's fields (SAD §4, DL-48).

   **If "Yes, publish it" is chosen**, the button posts to
   `POST /specialist/calendars/{calendar_id}/publish`:
   - Text: **"The General Partner will see these {n} dates straight away, in place of anything
     they saw before. It cannot be withdrawn in this version. A later review can publish a new
     calendar."** (When a calendar is already published: "… in place of the calendar published on
     {date}.")
   - Checkbox, **unticked**: **"I've read the {r} rejected rules and the {k} unused paragraphs
     above. Nothing from them will be on the published calendar."**
   - Button: **"Publish calendar"** (primary).

   **If "No, don't publish" is chosen** (U10, H-022), the button posts to
   `POST /specialist/calendars/{calendar_id}/decline`:
   - Text: **"Nothing changes for the General Partner. They keep seeing what they see now, and
     this review closes. You can start a new review."**
   - Field: **"What needs to change before it can be published?"**, field name
     `decline_reason`. Hint: "Recorded in the audit
     log with your name and the time. Specialists only."
   - Button: **"Close without publishing"** (secondary).
7. Link: **"Abandon this review"** → review status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G3 (`C_RUNNING` or earlier) | **"The calendar is not ready yet."** Link: **"Watch progress on the review status page"** |
| At G3 | Full page |
| Refused | Same page, message at the top and next to the checkbox (`ACK_REQUIRED`) or the reason field (`REASON_REQUIRED`). The checkbox is shown **unticked** again |
| After G3 | Read-only calendar with **"Published on {date} at {time}."** or **"Closed without publishing on {date} at {time}. What needs to change: {reason}"**, no forms |

**After each action**

| Action | Then |
|---|---|
| Publish calendar | Success: redirect to review status, `COMPLETED`, with the link to the General Partner view. Refused: `ACK_REQUIRED`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |
| Close without publishing | Success: redirect to review status, `DECLINED` ("Closed without publishing"). Refused: `REASON_REQUIRED`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |

**Budget:** about 5 minutes to read and publish. Total G1 + G2 + G3 ≈ 26 minutes, under the
30-minute target.

---

### Page 7 · Calendar (`/calendar`)

**Purpose.** The published calendar, read-only. **Who:** GP; the specialist sees the same page,
read-only. **Must work at phone width.**

**On screen, in order (before the first publication)**

1. Shared frame.
2. H1 **"Compliance calendar"**
3. The fixed message, word for word, **and nothing else**: no count, no review, no status, no
   summary cards, no calendar:
   **"Your compliance calendar is being prepared and checked by a specialist. Nothing has been
   published yet. The deadlines will appear here once it is published."** (operator, 2026-11-16,
   Open Question 12). It replaces the DL-27 text; `@system.arch` updates DL-27 and EC-014 (D11).

**On screen, in order (published)**

1. Shared frame.
2. H1 **"Compliance calendar"** (operator decision, 2026-11-13; the fund name is in the sidebar).
3. Line: **"Published on {date}."** Plus **"Made with stand-in agents (fixed test outputs, no AI model)."** when the published review used them
   (CR-030). The mock-ups leave this line out; the built app keeps it (H-004).
4. **Calendar note** (DL-12, SD FR-020), different by role (U11, H-023):
   - **General Partner** (short line, small grey text): **"These dates are the specialist's
     approved reading of the rules. Not legal advice. Date counting hasn't yet been checked
     against the legal texts."**
   - **Specialist** (the longer boxed note): **"This calendar is not legal advice. Before anyone
     relies on these dates: the way deadlines are counted (for example, the day 'six months after
     year end' falls on) has not yet been checked against the legal texts."**
5. **Summary cards** (a row of three; operator decisions 2026-11-13 and 2026-11-17, H-042; layout
   from `docs/prototype/gp-calendar.html`), in this order:
   - **Due next** (the dark card): the next due date in full, then what is due and who files it.
     **"None"** when nothing is due next.
   - **"Entries in {year}: {n}"**, with a dot chart of the year (one dot per entry, a column per
     month, hollow for "May not be required"; key **"Due date"** · **"May not be required"**). The
     chart is decoration; its numbers are written as text in the card's heading.
   - **May not be required** {p}.

   The values are **counted on the page from the entries this viewer is shown**, so the cards can
   never count something the General Partner cannot also read in the calendar (DL-49, CR-012).
6. **One calendar** (H2 **"All entries for {year}"**; just **"All entries"** when the entries fall
   in more than one year) with a three-way switch labelled for screen readers **"Show the calendar
   as"**: **"Month"** · **"Year"** · **"List"**. The switch changes the view in place, with no page
   reload and no script, and **only the chosen view shows. Month is the default** (operator
   decision, 2026-11-17, H-042; SAD §3 page 7, DL-49 update). Where `:has()` is unsupported, all
   three views show one under another. The switch is a radio group styled as tabs (the chosen tab
   is filled; the tab with the keyboard focus has a visible ring); the server ticks the one the
   address asks for (`?view=`), so moving between months keeps the Month view. **Only the links
   between months reload the page**; switching between Month, Year and List does not.
   - **Month view:** one month as a real table, Monday to Sunday, with links to the months either
     side ("‹ {month}" and "{month} ›"). It opens on the month asked for, else the month of the
     next due date, else (when every date has passed) the month of the first entry. Each entry shows
     What, and Who files in words, and "May not be required" where it applies. The next due date
     carries the word **"Due next"**. A month with no entries shows **"No filings this month."**
   - **Year view:** a real table, one row per obligation ("What · who files") and a column per
     month; each date is a small weekday-and-day mark. Legend: **"May not be required (dashed)"** ·
     **"Due next (underlined)"**. The words are also in the table for screen readers, so colour or
     line style never carries the meaning alone. It shows **one year**: the next due date's, else
     the first entry's. The dot chart counts that same year ("Entries in {year}"); entries in
     another year show in the Month and List views only.
   - **List view:** the entries table in item 7.
7. **Entries (List view):** a real table sorted by due date, grouped by month, each month its own
   row group. Columns: **When** (due date) · **What** ·
   **Who files** ("Not confirmed" for "not known") · **Why** (the reason, then "Source: {document},
   paragraph {id}" and the quote in a smaller blockquote).
   Entries the specialist added without confirmation carry the label **"May not be required"**
   (word, not just colour; U5, H-017) and this code-generated note under the reason: **"May not be
   required: it is not yet confirmed that this applies to the fund. It is listed so that it is not
   missed. It does not mean that any registration or marketing is permitted."** The specialist's
   reason is still shown as the "Why".
8. Nothing else: no draft, flag, other mark, review status, or link to a failed, abandoned or
   closed review. The summary cards and all three views show published facts only.
   **Moved marks are specialist-only** (operator decision 2026-11-14, Open Question 15; SAD §3
   page 7, DL-49): this page has no "Moved off a weekend" card, count, chip, chart colour or legend
   entry, and no open-question mark, in any view.

**Narrow screens.** **Below 960 px the switch and the Month and Year views are hidden and only the
List view shows** (operator decision, 2026-11-17, H-042), because a seven-column month or a
twelve-column year does not fit. At phone width (≤ 480 px) the List table keeps its table markup
but each row stacks as a block: "When" first in bold, then What, Who files, Why, each with its
column name as a visible label. The summary cards stack. No horizontal page scroll.

**States**

| State | What shows |
|---|---|
| Nothing published yet | The fixed empty message only (item 3 above; D11) |
| Published | As above. A later review that is closed without publishing, failed or abandoned changes nothing here |
| Error | **"The calendar could not be shown just now. Try again in a few minutes."** (never working content, CR-012) |

**Actions.** None, apart from "Sign out". The specialist's navigation is still shown to the
specialist.

---

## 4. Shared parts (for the templates)

| Part | Used on | Contains |
|---|---|---|
| Base frame | All | Sidebar (wordmark, product name, fund, navigation, identity with the demo label, sign out), breadcrumb, run labels, refusal slot (§1.3) |
| Stepper | 3 to 6 | §1.4 |
| Status words | 2, 3 | §1.5 |
| Row card | 4 (and the rejected list on 6) | Quote, check result, paragraph, flags, fields, decision or decision forms |
| Flag | 4 | Type heading and both texts |
| Decision form | 4, 5, 6 | **Answer-first** (A9 reversed, H-011, H-028; SAD DL-48): one form per rule, answer or calendar. First a radio question named `decision`, nothing chosen; only the chosen answer's fields and button then show (CSS `:has()`, no script). **Fallback:** where `:has()` is unsupported, every answer's fields and buttons stay visible (`@supports` in `docs/prototype/app.css`). No browser `required`, `disabled` or `pattern`: a missing field is refused by the server on the page. Each answer's reason field has its own name (G1 `approve_reason`, `reject_reason`; G2 `<answer>_reason`; G3 `decline_reason`), and the server ignores the fields of the answer not chosen. No answer chosen → `VALIDATION` (§5). Reason fields carry their audience hint |
| Mark label | 6, 7 ("May not be required" only) | Word + one-line explanation |
| Refusal message | All forms | §5 |
| Refresh controls | 3 | §3 page 3 |

## 5. Refusal messages

**Where** (operator decision, 2026-11-13). The same page is shown again. The `<title>` starts with
"Not done: " in every case.

- **About one rule card** at G1 or G2 (for example `DEMO_ROW_NOT_APPROVABLE`,
  `QUOTE_CHECK_FAILED`, `REASON_REQUIRED` on a rule): the page lands on that card (the redirect
  carries its anchor, `#row-{i}` or `#verdict-{i}`). The full sentence sits **inside the card,
  beside the decision forms**, headed **"Not done"**. The top of the page, under the H1, shows
  only a short line: **"Not done. The reason is shown beside rule {i}."** with the link **"Go to
  rule {i}"** (H-009).
- **`RUN_ACTIVE`** (start a new review): the same pattern, about the button (H-009). The full
  sentence sits beside **"Start a new review"**; the top shows the short line and **"Go to 'Start
  a new review'"** (page 2).
- **About one control** (`ACK_REQUIRED`, `REASON_REQUIRED` on abandon or on "Close without
  publishing", and `VALIDATION` when no answer was chosen; **decided 2026-11-17, H-049**): the same
  pattern as a rule card. The page lands on the control (the redirect carries its anchor: `#ack`,
  `#abandon`, `#decline-reason`, `#decision`). The full sentence sits **beside that control**,
  headed **"Not done"**. The top of the page, under the H1, shows only the short line **"Not done.
  The reason is shown beside {target}."** with a link **"Go to {target}"**, where {target} is
  **"the box"** (`#ack`), **"the reason"** (`#decline-reason`), **"the question"** (`#decision`) or
  **"abandon"** (`#abandon`). This avoids showing a 30-word sentence twice on one page.
- **About the page or the review as a whole** (for example `GATE_INCOMPLETE`, `VERSION_MISMATCH`,
  `RUN_NOT_ACTIVE`, `RUN_STAGE_RUNNING`, `FORBIDDEN`): no anchor. The full sentence in a box at the
  top under the H1, headed **"Not done"**, and nowhere else.
- **Always:** on the page, never as a browser pop-up, and recorded in the audit log (W-18,
  H-009). Any text the specialist typed in a reason field is shown again so it is not lost; radio
  choices and the G3 checkbox are shown **empty** again (nothing preselected).

**What.** The backend returns the code and the sentence (§4 of the SAD); this table is the wording
for that sentence. `{…}` are values the server fills in.

| Code | Context | Sentence |
|---|---|---|
| `DEMO_ROW_NOT_APPROVABLE` | Approve on the demo rule (rule 7) | **"This rule can't be approved. The quote is genuine, but it doesn't say what this rule claims, so there's no legal basis for it. Reject it and add a short reason, for example "Quote doesn't support the rule". Your attempt has been recorded in the audit trail."** (operator, 2026-11-16, DL-44 wording; sad.md CR-029 still has the older sentence, see D9) |
| `QUOTE_CHECK_FAILED` | Approve on a rule that failed the check | **"This rule failed the quote check: its quote does not appear word for word in paragraph {para_id}. It cannot be approved. Reject it with a reason."** |
| `ALREADY_DECIDED` | Rule (G1) | **"This rule was already decided, so your decision was not recorded. The page now shows the decision that stands."** |
| `ALREADY_DECIDED` | Answer (G2) | **"This answer was already decided, so your decision was not recorded. The page now shows the decision that stands."** |
| `REASON_REQUIRED` | Reject a rule | **"Write a reason to reject this rule."** |
| `REASON_REQUIRED` | Approve over a flag | **"The AI checker flagged this rule. Write a reason to approve it despite the flag."** |
| `REASON_REQUIRED` | G2 overrule to applies, or "can't tell" decided as add it | **"Write a reason. The General Partner will read it as the explanation for this entry."** |
| `REASON_REQUIRED` | G2 overrule to doesn't apply, or "can't tell" decided as leave it off | **"Write a reason. It is kept in the audit log; the General Partner will not see it."** |
| `BUSINESS_DAY_RULE_REQUIRED` | Approve without a weekend-or-holiday choice | **"Choose what happens if the deadline falls on a weekend or holiday to approve this rule: move to the following working day, move to the preceding working day, or keep the date."** (U9, H-021) |
| `REASON_REQUIRED` | Abandon | **"Write a reason to abandon this review."** |
| `REASON_REQUIRED` | Close without publishing | **"Write what needs to change before this calendar can be published."** (U10, H-022) |
| `WHO_FILES_REQUIRED` | Approve, source silent | **"The source does not say who files this. Choose a filing party, or 'Not known', to approve the rule."** |
| `GATE_INCOMPLETE` | Finish G1 | **"{x} rules are still undecided. Decide every rule before you finish checking."** |
| `GATE_INCOMPLETE` | Finish G2 | **"{x} answers are still undecided, {u} of them where AI can't tell. Decide every answer before you finish."** |
| `GATE_INCOMPLETE` | Finish G1, exactly one rule left (H-049) | **"1 rule is still undecided. Decide every rule before you finish checking."** |
| `GATE_INCOMPLETE` | Finish G2, exactly one answer left (H-049) | **"1 answer is still undecided, {u} of them where AI can't tell. Decide every answer before you finish."** |
| `ACK_REQUIRED` | Publish, box not ticked | **"Tick the box to confirm you have read the rejected rules and the unused paragraphs. Then publish again."** |
| `ACK_REQUIRED` | Publish, lists changed | **"The lists of rejected rules or unused paragraphs are not the ones shown when you ticked the box. Read the lists above and tick the box again."** |
| `VERSION_MISMATCH` | Any review-level action | **"This review has moved on since the page was opened. The page now shows where it is. Check it, then try again if you still need to."** |
| `RUN_ACTIVE` | Start a new review | **"Review {n} is still in progress, so a new review can't start. Finish it, or abandon it at its step, first."** + link **"Open review {n}"**, then the line **"Recorded in the audit trail."** (H-009) |
| `RUN_NOT_ACTIVE` | Any decision on an ended review | **"This review has ended ({status words}), so it cannot take more decisions. Start a new review from Filing rules."** |
| `RUN_STAGE_RUNNING` | Abandon or decide while AI or code works | **"AI is still working on step {k}, so this cannot be done yet. It finishes by itself; follow it on the review status page."** (step 4: "The dates are still being worked out, …") |
| `RUN_STAGE_RUNNING` | A decision or finish sent while the review is at a **different gate**, with nothing working (H-049) | **"This step is not open for decisions right now. The review status page shows where the review is."** |
| `RUN_NOT_FAILED` | Retry on a review that has not failed (B13b; sentence **proposed**, Open Question 24) | **"This review has not failed, so there is nothing to retry. The page now shows where it is."** |
| `RETRY_LIMIT_REACHED` | Retry a step that was already retried (B13b; **proposed**, Open Question 24) | **"Step {k} has already been tried again once and failed again. Start a new review from Filing rules."** |
| `RETRY_NOT_ALLOWED` | Retry refused for one of five reasons (B13b; **proposed**, Open Question 24 proposed, Open Question 25 closed). The sentence names which one | **"This step can't be tried again, because {reason}. Start a new review from Filing rules."** where {reason} is one of: "the review reached its cost limit"; "the dates could not be worked out, and trying again would give the same result"; "this is an evaluation run"; "a newer review has been started". **For the fifth reason, the sentence is different:** **"This step can't be tried again, because the limit on real model calls was reached. A new review would reach the same limit. Ask the operator to review the limit."** (no "Start a new review" advice, which would not help; Open Question 25, closed) |
| `FORBIDDEN` | GP on a specialist action | **"This page is for the compliance specialist. You are signed in as the General Partner, so you can view the published calendar only."** |
| `VALIDATION` | Decision submitted with no answer chosen (G1, G2 or G3; DL-48, H-030). Shown beside the form (inside the card at G1 and G2, with the short top line; at G3 next to the question) and at the top | **"Choose an answer first, then use its button. Nothing was saved."** |
| `VALIDATION` | Malformed form, a "who files" value not offered, or a G3 answer that doesn't match the button used | **"Part of this form was not valid ({field}), so nothing was saved. Check the form and try again."** |

## 6. Visual style

The look (tokens, type, spacing, components, status chips, contrast) is in
**`project-context/2.build/style-note.md`** (operator decision, 2026-11-13). This note does not
repeat it.

**Done (U8, H-020).** The operator accepted a new look for the MVP: 6px corners on cards and
buttons, pill chips and Iconoir icons (MIT licence, inline SVG).

**Fonts** (as in `docs/prototype/app.css`; not Inter Tight):

| Use | Font | `app.css` token |
|---|---|---|
| Headings, wordmark, fund name | **Lexend** | `--font-head` |
| Body text, labels, buttons | **Inter** | `--font-body` |
| Data: IDs and codes (`OBL-03`, `SRC-X-P2`, `FND-DEMO-01`) | **DM Mono** | `--font-id` |

`style-note.md` now describes it, with `docs/prototype/app.css` as the source of truth. If the two
disagree, the stylesheet wins. U7 and U8 together get half a day; anything that does not fit is
dropped.

B6 is still the first block dropped if time runs out: every page must stay usable and accessible
unstyled.

## 7. Accessibility (WCAG 2.2 AA, PRD §6)

- Headings in order: one H1, H2 per section or card.
- Real tables with `<th scope>` for the run list, items the AI worked on, coverage, rejected rows, calendar.
- Every control has a `<label>`; radio groups in `<fieldset>` with a `<legend>`; hints linked with
  `aria-describedby`.
- Status in words as well as colour, everywhere (§1.5).
- Automatic refresh can be stopped (WCAG 2.2.1), only runs while a stage runs, and refusal pages
  never auto-refresh.
- A refusal changes the `<title>` and appears first in the content, so it is announced on load.
- Specialist pages: designed for desktop (1280 px), must not break at 1024 px. GP calendar: 360 px
  to desktop.
- Target size: buttons and radio labels at least 24 × 24 px (WCAG 2.5.8).

## 8. Acceptance checks (observable in the rendered pages)

| ID | Check | Trace |
|---|---|---|
| UX-001 | Every page shows the demo label as text ("Demo with mock data" in the sidebar; in the intro line on sign-in) | operator brief |
| UX-002 | Every specialist page showing a stand-in review shows "Stand-in agents"; so does the calendar when that review's calendar is published. Applies to the built app even though the mock-ups leave it out | CR-030, H-004 |
| UX-003 | The planted rule at G1 is tagged "Demo", shows the quote-check line ("passed") like every rule, and offers the same answer-first form; after choosing "Approve", its "Approve rule" button is visible and active with nothing preselected; clicking it lands on that rule, shows the `DEMO_ROW_NOT_APPROVABLE` sentence (§5) in the card, changes its status tag to "Approval blocked", shows the short top line with "Go to rule {i}", and records the attempt in the audit log; no browser pop-up; the rule stays undecided | DL-44, CR-029, H-006, H-007, H-009, D5 (H-030) |
| UX-004 | No radio, checkbox or select is preselected on any page, including after a refusal | SD AC-026 |
| UX-005 | No page has a bulk action, a disabled button or a "coming soon" | §3, AC-026 |
| UX-006 | Review status refreshes every 3 s only while AI or code works, and "Stop automatic refresh" stops it | §3 Freshness, WCAG 2.2.1 |
| UX-007 | Every status is readable with colour removed | §3 Accessibility |
| UX-008 | Before the first publication, `/calendar` shows only the empty message (page 7 item 3) | DL-27 (to be updated, D11), CR-012 |
| UX-009 | A GP never sees a flag, a "can't tell" answer, a mark other than "May not be required", or a review | CR-012 |
| UX-010 | G2 reason fields that create an entry say the General Partner will read the reason; "doesn't apply" and "leave it off" fields say it is for the audit log only | SA-8, W-17 |
| UX-015 | Approving a rule with no weekend-or-holiday choice shows the `BUSINESS_DAY_RULE_REQUIRED` sentence in that rule's card; the rule stays undecided. The options read exactly: Move to the following working day, Move to the preceding working day, Keep the date; there is no "not confirmed" | §5, H-021 |
| UX-017 | "Start a new review" is visible while a review is in progress; clicking it shows the `RUN_ACTIVE` sentence beside the button and the short top line, and records the attempt in the audit log | CR-004, H-009 |
| UX-018 | The General Partner's calendar note reads exactly the U11 sentence (page 7); the specialist sees the longer note | SD FR-020, H-023 |
| UX-019 | No user-facing text says "run", "Stage A/B/C", "G1/G2/G3", "gate" or "precautionary" (except the exact label "Stand-in agents") | §1.8 |
| UX-020 | Every decision form (G1, G2, G3) opens with its answer question and nothing chosen; choosing an answer shows only that answer's fields and button; with `:has()` unsupported, every answer's fields show; submitting with no answer shows the `VALIDATION` "Choose an answer first" sentence (§5) and saves nothing | DL-48, H-028, H-030 |
| UX-016 | The "who files" options read exactly: AIFM, Fund administrator, Auditor, Local reporting agent (Spain), Tax advisor, Not known | DL-39 |
| UX-011 | The G3 acknowledgement checkbox is unticked on every load | CR-028 |
| UX-012 | The GP calendar has no horizontal scroll at 360 px | §3 |
| UX-013 | Run status offers no re-run action (the one exception is Retry of a failed step, sad.md rule 10, built in B13b) | §3 page 3 |
| UX-014 | A stand-in happy path from G1 open to G3 published takes a first-time reader under 30 minutes (from audit timestamps) | §7, EC-011 |
| UX-021 | **With Retry** (B13b built; sad.md rule 10): a failed review shows the "Retry step {k}" button, visible and enabled, and the link "Or start a new review from Filing rules"; clicking Retry puts the review back to "In progress" at that step, keeps every earlier decision, and adds one audit entry | Page 3 "Failed review", D10, G-3 |
| UX-022 | **Without Retry** (the B5 page, and the page if B13b is dropped; a failure-demo review ends here until B13b is built): a failed review shows only the link "Start a new review from Filing rules"; the page source has no Retry form, button or text (not hidden, not disabled), and a new review can be started | Page 3 "Failed review", §1.2 |
| UX-023 | On a published calendar at 1024 px or wider, the Month tab is ticked on first load and only the Month view shows; choosing Year or List shows only that view without a page reload; with `?view=list` the List tab is ticked. Below 960 px only the List view shows and the switch is hidden. No view shows a moved mark, a flag or a review status | Page 7 items 6 to 8, H-042, SAD §3 page 7, DL-49 |
| UX-024 | Below 960 px a slim top bar replaces the sidebar: wordmark link, a "Your turn" text tag when it applies, and a "Menu" `<details>` button; its panel opens over the content and holds the fund, the nav links, the signed-in person and "Sign out"; it closes on tapping "Menu" again or following a link, and not on an outside tap or Escape. From 960 px up the sidebar shows and no bar | §1.3 (Mobile shell), H-062 |

## 9. Post-MVP ideas (not in the Build card; not designed)

- **Reopen a rejected row with a reason.** Out of the MVP: "There is no edit, no reopen and no
  re-run" (DL-22, W-07, §1 "One way out of a mistake"). The MVP's way out of a wrong rejection is
  **abandon the run and start a new one** (W-19a), and the abandon text on page 3 says so. Reopen
  would need a SAD change (new transition, new audit event).
- **Highlight the quote inside the cited paragraph.** Needs the backend to return where the quote
  matched; the templates must not work it out.
- **An audit-log page** for the specialist: the run's audit entries (who, when, what, reason,
  refusals) in one read-only table. Would be an eighth page, so a SAD change. In the MVP the demo
  uses what the SAD already provides (Open Question 3, closed).
- **Close the phone menu on Escape or an outside tap** (H-062). Out of the MVP: native `<details>` does
  neither and the project ships no script. A polish-week item; it would need a script exception.
- **"Approve and go to next row" in one click**, to save time at G1. Only if the 30-minute target
  is missed in the rehearsal.

## 10. Screen-to-data map (the workflow)

For each screen in the one workflow: what it shows and what the user changes, named as
`entity.field` from the sad.md ERD ("Data model: the happy path", DL-50). **This is not a
schema.** Where a screen needs something the ERD does not have, it is listed in §10.3. "Derived"
means the server counts or filters fields that exist; the page never works anything out (§1.2).
`units` is in the SAD table list but not drawn in the ERD, so it is marked "(table list)".

### 10.1 The four review states

The workflow's four states map to the server values like this. The screen still shows the status
words of §1.5.

| State | `runs.status` · `runs.phase` | What the specialist sees |
|---|---|---|
| **idle** | No `runs` row with `status = ACTIVE` for the fund (none yet, or the newest has ended) | Filing rules without the active-review notice; "Start a new review" is accepted |
| **running** | `ACTIVE` · `A_RUNNING`, `B_RUNNING` or `C_RUNNING` (AI or code working), or `ACTIVE` · `AT_G1`, `AT_G2` or `AT_G3` (waiting for the specialist) | "AI is working" or "Your turn" (§1.5); review status refreshes only while working |
| **done** | `COMPLETED` (the goal), or `DECLINED` or `ABANDONED` (ended without publishing) | "Published", "Closed without publishing" or "Abandoned"; a closed, read-only review (page 3) |
| **failed** | `FAILED` | "Failed", with step, item and reason (page 3, "Failed review") |

### 10.2 Screens

| Screen | State | Shows (`entity.field`) | User changes (`entity.field` written) |
|---|---|---|---|
| Sign-in (stub) | Any | Nothing from the ERD (two fixed mock identities) | Nothing in the ERD (session only) |
| Sidebar (every page) | Any | `fund_profile.fund_id`; fund name and line (G-8); role from the session; "Your turn" tag from `runs.status`, `runs.phase` | — |
| Filing rules | idle | Reviews table: `runs.run_id`, start time (G-1), `runs.demo_planted_row`, `runs.status` + `runs.phase` as words; "Ended because": `units.failure_reason` (table list) for `FAILED`, `audit_log.reason` for `ABANDONED` and `DECLINED`. Start form: `fund_profile.fund_id`; agents mode from the server setting, which also decides whether the "Make step 1 fail (demo)" checkbox is in the form | **Start a new review** → new `runs` row (`fund_id`, `demo_planted_row`, the failure-demo switch (G-10), `agents_mode`, `status = ACTIVE`, `phase = A_RUNNING`); `audit_log` entries for the start and, if ticked, each demo switch. A refused start → `audit_log` (`event_type = refusal`, `refusal_code = RUN_ACTIVE` or `VALIDATION`) |
| Filing rules | running | As idle, plus the active-review notice: `runs.run_id`, `runs.status`, `runs.phase` | Start is refused (as above) |
| Filing rules | done, failed | As idle; the ended review shows its status words and "Ended because" | Start is accepted |
| Review status | running (AI working) | `runs.phase`, `runs.status`, units and their status (`units`, table list; G-2), `runs.cost_so_far`, `runs.agents_mode`, `runs.demo_planted_row`, start details (G-1) | Nothing (refresh on/off is in the URL only) |
| Review status | running (your turn) | As above, plus the counts in the sentence (derived: `rows` for the run; `verdicts.verdict = unsure`; `calendar_entries` for the run's `calendar_versions`) | **Abandon** → `runs.status = ABANDONED` (checked against `runs.run_version`); `audit_log` (`actor`, `at`, `reason`, `subject_id = run_id`); `runs.phase` keeps the step |
| Review status | failed | `runs.status`, `runs.phase` (the step), the failed unit and `units.failure_reason` (table list; G-2), `runs.cost_so_far` | **Retry** (B13b): `POST /specialist/runs/{run_id}/retry`, sad.md rule 10 (G-3). Without Retry: nothing (the link goes to Filing rules) |
| Review status | failed (failure demo) | As failed, plus the "Failure demo on" label from `runs.demo_fail_step1`, and the reason `demo failure` in `units.failure_reason` (G-10, DL-52, DL-53) | As failed |
| Review status | done | `COMPLETED`: `publications.published_at`. `DECLINED` / `ABANDONED`: `audit_log.at`, `audit_log.reason`, `runs.phase` (the step) (G-4) | Nothing |
| Check the rules (step 2) | running (before `AT_G1`) | `runs.phase` only | Nothing |
| Check the rules (step 2) | running (`AT_G1`) | `rows.row_id`, `rows.obligation_name`, `rows.frequency`, `rows.anchor`, `rows.offset`, `rows.recipient_code` (G-7), `rows.responsible_role`, `rows.business_day_rule`, `rows.quote`, `rows.origin` ("Demo" tag); `quote_checks.result`; `paragraphs.paragraph_text`, `paragraphs.document_id` (via `rows.run_id` + `rows.source_paragraph_id`); `flags.flag_type`, `flags.explanation`, `flags.row_value`, `flags.quote_says`, `flags.other_paragraph_id`, `flags.other_quote`; decided rules from `row_decisions`; "Approval blocked" from `audit_log` (`refusal_code = DEMO_ROW_NOT_APPROVABLE`, `subject_id = row_id`) (G-9); OQ-7 mark (G-6); unused paragraphs (derived: `paragraphs` not cited by an approved or undecided row); summary counts (derived) | **Approve / Reject** → one `row_decisions` row (`decision`, `business_day_rule` on approve, `who_files` when the source is silent, `reason`, `row_version`, `decided_by`, `decided_at`) + `audit_log`. A refusal → `audit_log` only. **Finish checking** → `runs.phase = B_RUNNING`, `runs.run_version` up by one, `audit_log` |
| Check the rules (step 2) | done, failed (after `AT_G1`) | Read-only: the same fields and every `row_decisions` row | Nothing |
| Confirm what applies (step 3) | running (`AT_G2`) | `verdicts.verdict`, `verdicts.reasoning`, `verdicts.cited_fact_ids` → `fund_profile.facts`, `verdicts.missing_information` (can't tell only); the approved rule: `rows.*`, `row_decisions.*`; decided answers from `verdict_decisions`; progress (derived) | **Confirm / Overrule / Decide** → one `verdict_decisions` row (`decision` = `confirm`, `override` or `decide`; `final_value`; `reason`, empty on confirm; `verdict_version`; `decided_by`; `decided_at`) + `audit_log`. **Finish and calculate dates** → `runs.phase = C_RUNNING`, `runs.run_version` up by one, `audit_log` |
| Confirm what applies (step 3) | before, done, failed | Before: `runs.phase` only. After: read-only `verdicts` + `verdict_decisions` | Nothing |
| Check the calendar and publish (step 4) | running (`AT_G3`) | `calendar_entries.due_date`, `unadjusted_date`, `business_day_rule`, `moved`, `precautionary`, `open_question_id`; via `calendar_entries.row_id`: `rows.obligation_name`, `rows.recipient_code` (G-7), `row_decisions.who_files` or `rows.responsible_role`, `rows.source_paragraph_id`; "Why": `verdict_decisions.reason` when the specialist overruled or decided, else `verdicts.reasoning` (W-17); rejected rules: `row_decisions` with `decision = reject` (`reason`) and `rows.origin`; unused paragraphs (derived); earlier publication: newest `publications.published_at` | **Publish** → one `publications` row (`calendar_id`, `acknowledged_rejected_row_ids`, `acknowledged_uncited_paragraph_ids`, `published_by`, `published_at`), `runs.status = COMPLETED`, `audit_log`. **Close without publishing** → `runs.status = DECLINED`, `audit_log.reason` (G-4) |
| Check the calendar and publish (step 4) | done | Read-only: the same, plus `publications.published_at` or the close reason (`audit_log.reason`) | Nothing |
| Calendar (General Partner) | No publication yet | Nothing: no `publications` row for the fund → the empty message (page 7 item 3; D11) | Nothing |
| Calendar (General Partner) | Published | Newest `publications` row for the fund → its `calendar_versions` → `calendar_entries.due_date`, `calendar_entries.precautionary`; via `row_id`: `rows.obligation_name`, `rows.quote`, `rows.source_paragraph_id` → `paragraphs.document_id`, who files, "Why" (as step 4); `publications.published_at`; stand-in line from `runs.agents_mode` (via `calendar_versions.run_id`); summary cards (derived). Never `moved`, `open_question_id`, flags, verdicts or any `runs.status` | Nothing |
| Calendar (General Partner) | A later review running, failed or done without publishing | Unchanged: still the newest `publications` row | Nothing |
| 403 / 404 pages | Any | Nothing from the ERD | 403: `audit_log` (`refusal_code = FORBIDDEN`). 404: nothing |

### 10.3 Data gaps for `@system.arch`

Things a screen needs that the ERD does not have. This note proposes no columns; the architect
decides.

| # | Screen | What is needed | What the ERD has today |
|---|---|---|---|
| G-1 | Filing rules ("Started"), review status (details line) | When the review started and who started it | **Resolved 2026-11-16 (DL-53):** `runs` gains `started_at` and `started_by`; read them from `runs` |
| G-2 | Review status (units table, failed state), Filing rules ("Ended because") | Each unit's label (for example "CSSF Circular 15/627"), status and failure reason | **Resolved 2026-11-16 (DL-53):** `units` is now drawn, with a readable label and its stage attempt (a retry adds the second attempt's lines without overwriting the first). Source document titles come from the regulation config |
| G-3 | Review status, Retry | A transition out of `FAILED` back to the failed stage's `*_RUNNING` phase; its route, guard and refusal codes; an audit event for it; which failure reasons allow a retry (for example `cost cap`); how the retry counts towards the cost cap; and what happens to outputs the failed stage already stored (`verdicts.row_id` and `calendar_versions.run_id` are unique, so a stage cannot simply write again) | **Resolved 2026-11-16 (DL-51):** sad.md rule 10 and CR-032 define the transition, route, guard, refusal codes, audit entry, cost handling and stored outputs. Built in B13b (DL-54); if B13b is dropped, use "Without Retry" (page 3) |
| G-4 | Filing rules, review status, step 4 (read-only) | The abandon and close reasons and the time the review ended | **Resolved 2026-11-16 (DL-53):** no new field; read from tables already listed (`audit_log.reason`, `audit_log.at`) |
| G-5 | Review status (failed) | Which step the review failed at | `runs.phase` keeps its last value (DL-46). Enough; confirmed by DL-53 |
| G-6 | Check the rules (step 2) | The "Depends on open question OQ-7" mark on rule `OBL-02`, before any date exists | **Resolved 2026-11-16 (SOQ-33, CR-027):** no stored field. The mark is derived when the page is drawn, from the source paragraph `SRC-UCILAW-P2` and recipient `AED` named in the regulation config |
| G-7 | Step 4, calendar | The recipient's name ("CSSF") | **Resolved 2026-11-16 (DL-53):** each recipient code's name is in `config/regulation/lu-part2.yaml`, not in a table |
| G-8 | Sidebar | Fund name and the line "Luxembourg UCI Part II · year end 31 Dec" | **Resolved 2026-11-16 (DL-53):** the fund's name, regime line and year end are in `config/fund/FND-DEMO-01.yaml`, not in a table |
| G-9 | Check the rules (step 2) | "Approval blocked" tag on the demo rule after a refused approval | **Resolved 2026-11-16 (DL-53):** no new field; read from the `audit_log` refusal row |
| G-10 | Filing rules (start form), review status (label, failed state) | The failure demo: a switch on the review, set only at start, like `runs.demo_planted_row`; a failure reason for it (a seventh reason, beside the six in §4); which unit fails (proposed: the first unit of step 1); a refusal when the box is ticked with the real model or on an evaluation run; an audit entry when it is on; and, with Retry, how the review knows the first attempt has already failed (the operator decided it fails once, Open Question 21) | **Resolved 2026-11-16 (DL-52, DL-53):** `runs.demo_fail_step1`, reason 8 `demo failure`, CR-033 (refusal in real mode, audit entry). Built in B13a (DL-54), without Retry. The first-attempt-only rule uses `runs.stage_attempt` |

## 11. Out of scope for the stubbed UI

Not designed, not built, and not shown as a placeholder (§1.2):

- **Real sign-in.** Sign-in stays a stub: two mock identities, no password.
- **Live streaming from crews.** Review status refreshes every 3 seconds; no streaming.
- **Tool traces and cost panels.** Review status shows only the one "Model cost so far" line.
- **Multi-tenant.** One fund, `FND-DEMO-01`; no Funds page, no second fund.
- **Full design system and styling polish.** Within the half day for U7 and U8 (H-019, H-020);
  pages must work unstyled.
- **Real backend wiring.** Stand-in agents only (`AGENTS_MODE=stand_in`); no real model call.
- **Any second workflow.**
- **A5, the source picker** (choosing which source a rule follows; H-008, DL-22).
- **A8, the period field** ("For December 2026"; H-010, DL-49).

---

## Sources

- `project-context/2.build/setup.md` (Scope & Guard Rules).
- `project-context/1.define/sad.md`: "Implementation Guidance for AI Development Agents" (Build
  card, Never row, Order of work, Rules every Build persona follows), and the sections it points to:
  §3 Frontend (the seven pages, shared parts, refusals, stand-in label, waiting, accessibility, no
  placeholders), §4 routes, refusal codes and failure reasons, §7 review-time target, the run-state
  model and "Transitions and guards", and the rows W-03b, W-07, W-12, W-13, W-15 to W-17, W-19a,
  CR-009, CR-012, CR-019, CR-027 to CR-030, and "The planted demo row".
- `project-context/1.define/decision-log.md`: DL-01, DL-05, DL-12, DL-27 (cited by the pages).
- `project-context/1.define/mock-data/mock-fund-profile.md`: fictional fund name, filing parties.
- `project-context/1.define/mock-data/expected-obligation-library.md` and
  `mock-regulatory-sources.md`: rows, quotes, verdicts, flags and the 22 calendar dates used in the
  mock-ups.
- `project-context/2.build/style-note.md`: the visual style (§6).
- `project-context/handoffs.md`: the operator's decisions of 2026-11-14 on the design exploration
  (H-004 to H-026; this revision applies U1 to U11, A3, A4, A7, A9, H-009, H-023 and U9/Q1), and
  H-028 and H-030 (answer-first form; follow-ups from the SAD update).
- `project-context/1.define/sad.md` DL-47, DL-48, DL-49, §3 pages 4 and 7, §3 "Decision form",
  §4 routes and validation (read for H-030). Read again for the H-042 second pass: §3 page 7 and the
  DL-49 update of 2026-11-17 (`decision-log.md`), with `backend/web/templates/pages/calendar.html`,
  `backend/web/calendar_view.py` and `backend/web/routes/calendar.py` for what is built.
- `docs/prototype/HANDOVER.md` and `docs/prototype/build.py` (the mock-up wording and layout).
- `project-context/1.define/sad.md` "Data model: the happy path" (DL-50 ERD), the table list in
  §4 "Data", the run-state model, "Transitions and guards" and the failure reasons (read for §10
  and the H-026 gaps); `docs/prototype/app.css` font tokens (§6); `handoffs.md` H-026.
- `.cursor/templates/ux-template.md`, `.cursor/skills/product-design/SKILL.md`.
- The operator's B5 brief, and the operator's decisions on the mock-up review (2026-11-13).

Not read or used: Future Work, Appendix A, git tag `sad-full-design`, user-story files.

## Assumptions

- **File location.** The operator asked for `project-context/2.build/ux.md`. The framework's
  default is `project-context/1.define/ux.md`, and the validator only checks the approval status
  there, so it will not see this file's status. The operator confirmed `2.build/` (Open Question
  2, closed).
- **Mock-ups, not templates.** Static design mock-ups of every in-scope screen are in
  `docs/prototype/` (generated by `build.py`), with hard-coded fictional data. They are the layout
  and look reference for `@frontend.eng`, not code to copy: no logic, no JavaScript. The planted
  row's content in them is invented, because the backend fixture (SAD CR-029) does not exist yet.
  The Funds pages in the same folder are future scope and are not described here.
- **The demo label** is the static text "Demo with mock data" in the sidebar's identity block
  (and in the sign-in intro line). It is not the parked F-18 banner (no Reset, no extra
  behaviour).
- **Stepper mapping.** The mock-ups only show step 1 in progress and steps 2 to 4 waiting for the
  specialist. Showing Stage B as "In progress" on step 3 and Stage C on step 4 (§1.4) is this
  note's reading of U4.
- **Wording this note had to add.** The mock-ups do not show every state. Where a decision changed
  a word but no mock-up shows the screen, this note writes the new sentence in the same style:
  the H1s for `B_RUNNING` to `FAILED` on page 3, the failure and abandon sentences, and the §5
  refusals other than `DEMO_ROW_NOT_APPROVABLE` and `RUN_ACTIVE`. All of it goes through the copy
  review (CR-019).
- **Hidden-but-enforced vs shown-and-refused.** The Approve button is always shown (rule of the
  page). Two controls are shown only in the phase where they belong, following the SAD's wording:
  the abandon form (gates only) and the decision forms (undecided items only). The server still
  enforces both.
- **"Stop automatic refresh"** is a query parameter on the run status URL. It stores nothing.
- **G2 "can't tell"** ("unsure") can be decided as "Yes, add it until someone confirms" (the SAD's
  precautionary choice, labelled "May not be required") or "No, leave it off", both with a reason.
  The SAD names the precautionary choice; it does not say "does not apply" is ruled out.
- **Override** at G2 flips the verdict to its opposite; there is no third value.
- **"Moved off a weekend" mark** text assumes the server gives the original and the moved date,
  and which direction it moved.
- **Weekend-or-holiday choice at approve** offers three values: move to the following working day,
  move to the preceding working day, keep the date. "Not confirmed" is no longer offered (U9,
  H-021, a DL-19 change through the operator). A choice is always required (operator decision,
  2026-11-13); a missing one is refused with `BUSINESS_DAY_RULE_REQUIRED`.
- **Names checked against `mock-fund-profile.md`**: fund "Bramblegate Credit Opportunities SICAV",
  GP "Bramblegate Partners", fund ID `FND-DEMO-01`, all fictional. They match.
- **"Who files" labels** match the mock fund profile and the SAD (W-07, DL-39) exactly, including
  "Local reporting agent (Spain)" (operator decision, 2026-11-13).
- Time estimates (2 min per row, 1 min per verdict, 5 min at G3) are design targets, not
  measurements.

## Open Questions

1. **Closed 2026-11-13 (operator).** Reopen a rejected row stays out of the MVP (DL-22). It is
   listed under Post-MVP ideas.
2. **Closed 2026-11-14 (operator).** `ux.md` stays in `2.build/`. The validator does not track its
   approval status there, so the operator records approval in this file by hand.
3. **Closed 2026-11-13 (operator).** No new page. The demo shows the audit log through what the
   SAD already provides: the append-only `audit_log` table (CR-013), read with the query that
   rebuilds the history of one calendar entry (CR-018), and the trace export (D4, block B8), which
   writes the `trace` and `audit_log` records for a run to `project-context/2.build/logs/<run_id>/`
   (§6 of the SAD). An audit page is listed under Post-MVP ideas. Note for `@qa.eng` and
   `@backend.eng`: the SAD defines the export for evaluation runs; whether it is also run for the
   demo run is theirs to confirm.
4. **G2 "unsure" → "Does not apply".** Allowed? Assumed yes (see Assumptions).
5. **Closed 2026-11-14 (`@system.arch`, H-030).** `BUSINESS_DAY_RULE_REQUIRED` is in SAD §4
   (DL-47), and DL-47's update says "not confirmed" no longer counts as a choice.
6. **Closed 2026-11-14 (`@system.arch`, H-030).** On reject, the server reads only
   `reject_reason` and ignores any weekend-or-holiday or "who files" choice (SAD §4, DL-48).
7. **Closed 2026-11-13 (operator).** The page uses "Local reporting agent (Spain)", exactly as
   the mock fund profile and the SAD (DL-39) have it. No display label is needed.
8. **Closed 2026-11-14 (H-010, H-030; DL-49, F-19).** A period field for each calendar entry. On the GP calendar, twelve
   entries read "Monthly financial report U1.1 to the CSSF" and cannot be told apart. The mock-ups
   add a line such as "For December 2026" (the period the filing covers). The pages must not work
   this out themselves (§1.2), so the server would need to send it. Add a field to the calendar
   entry in the SAD, or drop the line? **Decided 2026-11-14 (operator, H-010):** post-MVP
   stretch, after the extra calendar views (H-012). No line in this build.
9. **Closed 2026-11-14 (operator, H-021 and H-024).** With no "not confirmed" option, the two
   filings that fell on Sun 28 Feb 2027 move to the preceding working day, Fri 26 Feb. No GP sees a
   Sunday deadline. `@qa.eng` updates the answer key (H-024).
10. **For `@qa.eng`: an event date after the publication date.** The demo calendar is published on
   Fri 13 Nov 2026, but the `OBL-05` entry rests on `EVT-01`, which the fund "became aware of" on
   31 Jan 2027 (`mock-fund-profile.md`). A published calendar cites an event that has not
   happened yet. Check whether the demo date or the event date should change.
11. **For the operator: the "Funds" item in the sidebar.** The mock-ups show "Calendar · Funds ·
   Filing rules". There is no Funds page in this build, and §1.2 allows no placeholder, so this
   note leaves "Funds" out until H-026 says whether Funds stays future scope.
12. **For the operator: the empty calendar's words.** The mock-up's empty state reads "No calendar
   has been published yet. You'll see deadlines here once compliance has signed them off." DL-27
   fixes the message word for word (EC-014 checks it), so this note keeps DL-27. Change DL-27, or
   update the mock-up?
   **Closed 2026-11-16 (operator): approved.** Page 7 now uses this copy for the General
   Partner's empty calendar. `@system.arch` updates DL-27 and EC-014 in the same batch as CR-029
   (D9, D11):
   > **"Your compliance calendar is being prepared and checked by a specialist. Nothing has been
   > published yet. The deadlines will appear here once it is published."**

   Why: it keeps DL-27's two sentences almost as they are, so EC-014 needs only a small update;
   it says "compliance calendar", the on-screen name (§1.8, U1), in place of "obligations
   calendar"; and it adds what happens next, as the voice rules ask (§1.6), without the mock-up's
   "signed them off", which reads like a legal sign-off. The mock-up `gp-calendar-empty.html`
   still shows its own words and needs changing to match.
13. **For the operator: "General Partner" or "General Partner / Fund Manager".** H-018 says
   "General Partner" in the UI. The mock-ups use "General Partner / Fund Manager" for the role name
   on sign-in and in the sidebar. This note uses the long form for the role name and "the General
   Partner" in running text. Confirm.
14. **For the operator: the "Demo" tag on the planted rule.** The mock-ups show no "Demo" tag on
   rule 7. CR-029 says the row is labelled "demo" wherever it appears, and no decision changed
   that, so this note keeps the tag (like A1 and A2, treated as prototype-only). Confirm.
15. **Closed 2026-11-14 (operator, H-030).** Moved marks stay specialist-only. The General
   Partner's calendar has no "Moved off a weekend" card, count, chip, chart colour or legend
   entry, and the B12 views and charts follow the same rule (SAD §3 page 7, DL-49 update; page 7
   item 8). The mock-up is already changed (`build.py`, `gp-calendar.html`).
16. **Closed 2026-11-16 (operator).** Step numbers follow the stepper on screen everywhere: the
   specialist's steps are Steps 2, 3 and 4 (check the rules, confirm what applies, publish); Step 1
   is "AI drafts the rules" (U4, H-016).
17. **Closed 2026-11-16 (operator).** The 403 page links the General Partner to **"Go to the
   calendar"** and the specialist to **"Go to Filing rules"** (§1.7).
18. **Closed 2026-11-16 (operator): keep Retry.** The minimal UI bar for the demo lists "error and
   retry". Keep it small: retry only the failed stage, keep earlier approvals, record it in the
   audit log (page 3, "Failed review"). The SAD change landed on 2026-11-16 (sad.md rule 10,
   DL-51; D10, §10.3 G-3). It is block B13b, built after B9 and dropped next after B6 (DL-54).
19. **Closed 2026-11-16 (operator).** Abandon is offered only while the review waits for the
   specialist at a step, never while AI or code is working, so no agent is cut off halfway (SAD
   run-state rule 8).
20. **Closed 2026-11-16 (operator).** The Filing rules column is now **"Demo rule"**, to match
   the refusal wording.
21. **Closed 2026-11-16 (operator).** The failure demo fails step 1 **once**. "Retry step 1" then
   succeeds, so one review shows both the error and the retry. In the SAD this is DL-52. The
   failure demo is built in B13a and works without Retry; the "then succeeds" half needs B13b
   (DL-54).
22. **Closed 2026-11-16 (operator).** No "Failure demo" column on Filing rules. The "Failed"
   status and the reason sentence under "Ended because" are enough, and the table stays simpler.
23. **Closed 2026-11-16 (operator).** The reason sentence is: "This step failed on purpose, for
   the demo only, because "Make step 1 fail (demo)" was ticked when the review started. Nothing
   else went wrong." One sentence, used everywhere (reason table, status line, "Ended because" on
   Filing rules), so `@system.arch` stores one version.
24. **Open (operator to confirm; only matters if B13b is built).** The three Retry refusal
   sentences in §5 (`RUN_NOT_FAILED`, `RETRY_LIMIT_REACHED`, `RETRY_NOT_ALLOWED`) are my drafts.
   The SAD defines the codes and says the `RETRY_NOT_ALLOWED` sentence "names which" reason, but
   gives no wording. Until confirmed, `@frontend.eng` may use the drafts.
25. **Closed 2026-11-24 (operator).** After `call limit` (DL-58, H-093) the `RETRY_NOT_ALLOWED`
   sentence does not end "Start a new review from Filing rules", because the call limit counts an
   activity's real calls across both databases (EC-R10), so a new review reaches the same limit. The
   sentence is: "This step can't be tried again, because the limit on real model calls was reached. A new review would reach the same limit. Ask the operator to review the limit." The other four reasons keep their ending.
   The ending is built where the refusal text is made (`backend/services/refusals.py` has one fixed
   ending today), so the change is H-094 to `@backend.eng`. The "Start a new review from Filing
   rules" link on the failed page stays: it is a link, not advice, and stand-in reviews still work.

## Mock-up differences this revision does not apply

These are in `docs/prototype/` but are not among the decisions applied here, so ux.md does not
follow them yet: the "For December 2026" period line (A8, H-010: post-MVP); the Funds pages (future
scope, H-026); the summary cards and Sources table on Filing rules; the fund facts strip on the
calendar; the "Why" expand link and the filters on the calendar list; and the left-hand panel on
sign-in. Items 11, 12, 14 and 15 above are also mock-up differences.

## Where ux.md and sad.md now disagree

`sad.md` was not edited by this persona (operator rule). **D1 to D5 are resolved:** `@system.arch`
updated sad.md on 2026-11-14 (H-030), so the "sad.md still says" column for those rows records the
old text. D6 to D8 stay as notes:

| # | ux.md now says | sad.md said | Where in sad.md | Decision |
|---|---|---|---|---|
| D1 | The demo-row refusal reads "Approval blocked: no legal basis. This rule doesn't appear in the regulation text. Reject it with a reason." | "This is a planted demo row. It cannot be approved. Reject it with a reason." | CR-029 (and DL-44 by reference); T-DEMO-2 may check the text | A3, H-006 (DL-44 update pending). **Resolved 2026-11-14:** sad.md updated (H-030) |
| D2 | Three weekend-or-holiday choices: following working day, preceding working day, keep the date. No "not confirmed" | `business_day_rule` is `roll_forward`, `no_roll`, `not_confirmed`; "'not confirmed' counts as a choice" | Data model enum; §4 `BUSINESS_DAY_RULE_REQUIRED` row; DL-19, DL-47. (The extractor may still output `not_confirmed` when the source is silent, EC-003; ux.md shows that as "Not stated", never as a choice) | U9, H-021 (DL-19 change pending). **Resolved 2026-11-14:** sad.md updated (H-030) |
| D3 | No "Rule not confirmed" mark; the marks are moved, may not be required, open question | Marks are "roll, rule unconfirmed, precautionary, open question" | §3 page 6 and "Shared template parts" (mark label) | U9 / Q1, H-021, H-024. **Resolved 2026-11-14:** sad.md updated (H-030) |
| D4 | "May not be required" in place of "Precautionary" | "precautionary" label, generated by code | CR-019, W-12, §3 page 6; also DL-01, PRD F5/F8, SD P-1 | U5, H-017 (DL-01 amendment pending). **Resolved 2026-11-14:** sad.md updated (H-030) |
| D5 | The quote-check line shows on every rule, the demo rule included; the demo rule's status tag reads "Approval blocked" after the refusal | The quote-check result "on **every** row, the demo row included" | §3 page 4 | A4, H-007. **Resolved 2026-11-14:** the operator chose sad.md's reading; ux.md page 4 item 3 and UX-003 changed to match (H-030) |
| D6 | Users read "review", "AI", four named steps, "General Partner", "Close without publishing" | "run", "Stage A/B/C", "G1/G2/G3", "GP", "decline" | Throughout (allowed: the documents keep the internal names, §1.8) | U2, U3, U4, U6, U10 |
| D7 | The General Partner's note: "These dates are the specialist's approved reading of the rules. Not legal advice. Date counting hasn't yet been checked against the legal texts." The specialist sees a longer note | One calendar-level "not legal advice / conventions not yet checked" note | W-16, DM-14 (wording only; H-023 says no FR-020 change) | U11, H-023 |
| D8 | The specialist's navigation is "Calendar · Filing rules" in a sidebar | Not specified beyond the seven pages | §3 (no conflict; noted for completeness) | U7, H-019 |
| D9 | The demo-rule refusal reads "This rule can't be approved. The quote is genuine, but it doesn't say what this rule claims, so there's no legal basis for it. Reject it and add a short reason, for example "Quote doesn't support the rule". Your attempt has been recorded in the audit trail." | "Approval blocked: no legal basis. This rule doesn't appear in the regulation text. Reject it with a reason." + "Recorded in the audit trail." | CR-029; DL-44 update of 2026-11-14 in `decision-log.md`; T-DEMO-2 may check the text | Operator, 2026-11-16. **Resolved 2026-11-16:** sad.md updated by `@system.arch` (CR-029, DL-44) |
| D10 | Retry on a failed step (proposed) | A failed run is never resumed or re-run; no re-run action | Run-state rules 2 and the `FAILED` row; §3 page 3 | Operator, 2026-11-16: keep Retry, small (failed stage only, earlier approvals kept, audited). **Resolved 2026-11-16:** sad.md rule 10, DL-51 (§10.3, G-3); built in B13b (DL-54) |
| D11 | The General Partner's empty calendar reads "Your compliance calendar is being prepared and checked by a specialist. Nothing has been published yet. The deadlines will appear here once it is published." | "Your obligations calendar is being prepared and checked by a specialist. Nothing has been published yet." | DL-27; EC-014 checks the text | Operator, 2026-11-16 (Open Question 12). **Resolved 2026-11-16:** sad.md updated by `@system.arch` (DL-27, EC-014) |
| D12 | A second demo switch, "Make step 1 fail (demo)", stand-in agents only, makes step 1 fail with its own reason sentence; the review shows "Failure demo on" | No such switch; six failure reasons (§4), none on purpose | §4 failure reasons; `runs` table; CR-029 (the demo rule switch it copies); CR-030 | Operator, 2026-11-16. **Resolved 2026-11-16:** sad.md DL-52, DL-53, CR-033 (§10.3, G-10); built in B13a, without Retry (DL-54) |

D6 and D8 need no SAD change. D1 to D5 were changed in sad.md by `@system.arch` (H-030). D7 is
wording only. D9, D10, D11 and D12 were resolved on 2026-11-16: `@system.arch` updated sad.md in
one batch (H-032; DL-44, DL-27, DL-51 to DL-53). No row in this table is open.

## Audit

- 2026-11-13 · persona `ux-designer` · action `design-ux` · `project.mode` greenfield ·
  `ui.design_system_mode` create (default; no `ui` block in `aamad.config.yml`) · created
  `project-context/2.build/ux.md` (page-by-page note for the seven pages of SAD §3) on branch
  `ux-b5-page-note`. No HTML, templates, code or prototype. No diagram file (a text flow in §2).
  No model call. Approval status left `pending`.
- 2026-11-13 · persona `ux-designer` · action `design-ux` (revision, operator review) · closed
  Open Questions 1 (reopen out, DL-22) and 3 (audit log via `audit_log` table, CR-018 query and
  trace export D4; audit page moved to Post-MVP); kept G2 override with a reason; added
  `BUSINESS_DAY_RULE_REQUIRED` (pending a SAD §4 row); G2 reason hints now depend on whether the
  decision creates an entry; named the six "who files" options; named `GATE_INCOMPLETE` on Finish
  applicability; removed echoes of the brief's reopen wording; checked names against
  `mock-fund-profile.md`. Approval status left `pending`.
- 2026-11-13 · persona `ux-designer` · action `design-ux` (revision) · "who files" label set to
  "Local reporting agent (Spain)" to match the profile and the SAD; closed Open Question 7. Open
  Question 5 stays open while `@system.arch` adds `BUSINESS_DAY_RULE_REQUIRED` to SAD §4.
  Approval status left `pending`.
- 2026-11-13 · persona `ux-designer` · action `design-ux` (prototype + revision, operator review of
  the mock-ups) · branch `ux-mockups-g1-gp` · static mock-ups of G1 review, the demo-row refusal
  and the GP calendar in `docs/prototype/`; `editorial.css` contrast fixes from `style-note.md`.
  Operator decisions applied: §6 replaced by a pointer to `style-note.md`; demo label is the pill
  "Demo with mock data" only; header carries the fund name; GP H1 is "Compliance calendar"; GP page
  may show summary cards and a week grid (published facts only); a refusal about one card lands on
  that card, with a short top line and "Go to row {i}" (extended to G2 verdict cards, as §5 covers
  both); G1 row index is a table with "Needs attention", and its progress sentence is replaced by
  summary cards; G1 row-index example corrected (OBL-03 is the audited annual report). Open
  Questions 8 (period field, `@system.arch`), 9 (Sunday due date) and 10 (event after publication,
  both `@qa.eng`) added. Approval status left `pending`.
- 2026-11-14 · persona `ux-designer` · action `design-ux` (revision, operator decisions on the
  design exploration in `handoffs.md`) · branch `ux-mockups-exploration-handover` · applied U1 to
  U11 (H-013 to H-023), A3 (H-006), A4 (H-007), A7 (H-009), A9 (H-011, rejected: separate forms
  kept) and U9/Q1 (H-021, H-024). The mock-ups are now the layout and look reference; this note
  stays the reference for behaviour, states, wording and refusals. Kept the "Stand-in agents"
  label and the demo-row switch (A1, A2: prototype-only, H-004, H-005). Added §1.8 (words on
  screen), UX-017 to UX-019, Open Questions 11 to 15, and the "Mock-up differences" and "Where
  ux.md and sad.md now disagree" sections. Closed Open Question 9; recorded the H-010 decision on
  Open Question 8; updated Open Question 5. Did not edit `sad.md` or `style-note.md`. No code. No
  model call. Approval status left `pending`.
- 2026-11-14 · persona `ux-designer` · action `design-ux` (revision, H-028 and H-030) · branch
  `ux-answer-first-form` · replaced the separate side-by-side decision forms with the answer-first
  form on pages 4, 5 and 6 and in §4 (A9 reversed, DL-48), with the `:has()` fallback and the built
  field names (`decision`, `approve_reason`, `reject_reason`, `<answer>_reason`, `decline_reason`;
  G3 `formaction`); added the G2 question for an ordinary answer as new wording (H-026 still open);
  added the `VALIDATION` "no answer chosen" sentence (§5) and UX-020; quote-check line now on every
  G1 rule, the demo rule included (D5), page 4 and UX-003; moved marks specialist-only on page 7,
  B12 included; closed Open Questions 2 (file stays in `2.build/`), 5, 6, 8 and 15; marked D1 to D5
  resolved. Did not edit `sad.md`, `style-note.md` or the mock-ups. No code. No model call.
  Approval status left `pending`.
- 2026-11-15 · persona `ux-designer` · action `design-ux` (follow-up, H-020) · branch
  `ux-style-note-followup` · §6 "Pending (U8, H-020)" changed to "Done": `style-note.md` was
  rewritten around `docs/prototype/app.css` (PR 52) and gained an Icons section for Iconoir. Closed
  H-020 in `handoffs.md`. No other section changed. Did not edit `sad.md` or the mock-ups. No code.
  No model call. Approval status left `pending`.
- 2026-11-16 · persona `ux-designer` · action `design-ux` (revision, stubbed UI) · branch
  `ux-sprint3-workflow` · added the five-line workflow at the top; filled the H-026 gaps:
  failed review with a proposed Retry (blocked until a SAD edit, D10), abandon follow-through,
  closed read-only reviews, 403 and 404 pages, the ordinary confirm and overrule at step 3; added
  "Ended" and "Failed" to the stepper; removed the "Agents" column on Filing rules; "Add the demo
  rule (rule 7)"; new demo-rule refusal wording (D9); §6 font table (Lexend, Inter, DM Mono); a
  proposal for Open Question 12; Open Questions 16 to 20; §10 screen-to-data map with data gaps
  G-1 to G-9; §11 out of scope for the stubbed UI. Edited only this file. No code. No model call.
  Approval status left `pending`.
- 2026-11-16 · persona `ux-designer` · action `design-ux` (revision, operator answers) · same
  branch · removed "Sprint 3" from the text; closed Open Questions 12 and 16 to 20 with the
  operator's decisions: page 7 empty message now the approved copy (D11, DL-27 and EC-014 to
  update with CR-029); step numbers follow the stepper; 403 link for the General Partner is "Go to
  the calendar"; Retry kept, small, still blocked until the SAD change (D10); abandon only at a
  step; Filing rules column renamed "Demo rule". Edited only this file. No code. No model call.
  Approval status left `pending`. Later the same day the operator reviewed and approved the
  "Failed review" section (page 3); recorded at its head. Run label renamed "Demo rule on" (§1.3
  and page 3), so the tag, the Filing rules column and the refusal use the same words.
- 2026-11-16 · persona `ux-designer` · action `design-ux` (revision, error and retry) · same
  branch · added the failure demo (proposed, D12, G-10): a "Make step 1 fail (demo)" checkbox on
  page 2, stand-in agents only, the "Failure demo on" label, its reason sentence and a page 3
  subsection; wrote the Retry fallback in "Failed review" (two versions of the status line and the
  next-step link; the Retry form left out of the page until the SAD change lands); added UX-021
  (with Retry) and UX-022 (without); updated §10.2; added Open Questions 21 to 23. Edited only this
  file. No code. No model call. Approval status left `pending`. Later the same day the operator
  closed Open Questions 21 (fail once) and 22 (no extra column); 23 stays open.
- 2026-11-16 · persona `ux-designer` · action `design-ux` (approval) · branch `ux-approve` · Open
  Question 23 closed earlier the same day (the operator's failure-demo reason sentence, used
  everywhere); handoff H-032 raised to `@system.arch` (PR 56). The operator approved this note:
  Approval status set to `approved`. Retry and the failure demo stay blocked until H-032 lands.
  No other change. No code. No model call.
- 2026-11-16 · persona `ux-designer` · action `design-ux` (revision, sync to DL-51 to DL-54, H-034)
  · branch `ux-sync-dl51-54` · removed "blocked until H-032 lands": Retry is in sad.md (rule 10,
  DL-51) and the failure demo too (DL-52, DL-53). Followed DL-54: the failure demo is B13a (kept,
  does not need Retry); Retry is B13b (after B9, dropped next after B6); "Without Retry" is now the
  page B5 builds, not a temporary fallback. Updated: top note, page 2 checkbox, page 3 (purpose,
  states table, reason table, stand-in pause note, "Failed review", "Failure demo", actions), §5
  (three Retry refusal sentences, **drafted by me, not in the SAD**, Open Question 24), UX-013,
  UX-021, UX-022, §10.2, §10.3 G-1 to G-10 (answers from DL-51 to DL-53 and SOQ-33), Open
  Questions 18 and 21, D9 to D12. Approval status left `approved` (operator choice, 2026-11-16):
  the sync adds no layout or behaviour beyond the SAD, except Open Question 24. The other
  session's stash (`stash@{0}`, "ux.md follow-ups to DL-51..53") was read, not applied: it said
  "B13" instead of B13a and B13b and set approval back to `pending`. Edited only this file. No
  code. No model call.
- 2026-11-17 · persona `ux-designer` · action `design-ux` (revision, H-037, H-042, H-043, H-049 and
  the wording `frontend.md` asked for) · branch `h045-lookups-cleanup` · page 1: left-hand panel and
  the portfolio-voice exception in §1.6 (H-037); page 7: summary cards, one calendar with Month /
  Year / List switch, Month default, List only below 960 px, new wording (H-042); pages 4 and 5:
  land on the next card to decide (H-043); §5: two new sentences and a placement rule, **the
  four control-level refusals get an anchor** (H-049, my decision, for the operator to confirm);
  page 4 column headings "The source says" / "The AI's reading", page 6 empty list "None.", page 3
  "Last updated at 14:02:09." and the review-status tab title. Did not edit `sad.md` (§3 page 7
  still says "chosen by a link", List default; H-040) or `frontend.md`. Approval status left
  `approved`: pages 1 and 7 and the §5 placement change layout after approval, so the operator
  should read them. No code. No model call.
- 2026-11-17 · persona `ux-designer` · action `design-ux` (revision, H-042 second pass, after PR #82) ·
  branch `ux/h042-page7-after-pr82` · checked page 7 against `sad.md` §3 page 7 and the DL-49 update
  (H-040, now landed) and against the built page (`calendar.html`, `calendar_view.py`,
  `routes/calendar.py`, `site.css`). The two now agree on: radio group styled as tabs, Month the
  default, only the List view below 960 px, the dot chart, no moved marks. Added to page 7 item 6
  what the SAD and the code say and ux.md did not: only the links between months reload the page;
  which month the Month view opens on; the Year view and the dot chart show one year; the H2 reads
  "All entries" when the entries span more than one year; the focus ring on the tabs. New check
  UX-023. Sources now list the SAD page 7 row and the DL-49 update. The "chosen by a link" note in
  the entry above is out of date: `sad.md` was corrected in PR #82. Approval status left `approved`:
  no layout or wording changed, only gaps filled. No code. No model call.
- 2026-11-19 · persona `ux-designer` · action `design-ux` (revision, H-062, operator decision) ·
  branch `ux-designer/h062-mobile-shell` · recorded the mobile shell built by `@frontend.eng`
  (checked against `parts/sidebar.html`, `parts/side_body.html` and `site.css`): new "Mobile shell
  (below 960 px)" in §1.3, new check UX-024, new §9 idea (Escape and outside-tap close). Operator
  decision: no outside-tap or Escape close in the MVP, so the no-script rule holds. Approval status
  left `approved`. No code. No model call.
- 2026-11-24 · persona `ux-designer` · action `design-ux` (revision, H-093; from `@system.arch`, DL-58) ·
  branch `ux-designer/h093-two-failure-sentences` · `AAMAD_TARGET_RUNTIME=crewai` ·
  `AGENTS_MODE=stand_in` · read `sad.md` §4 failure reasons 9 and 10 and DL-58, `integration.md`
  §3.4, and (read only) `backend/services/runs.py` and `refusals.py`. Page 3 "Failure reason
  sentences": lead-in now "one for each of the nine reasons" (was "the six reasons"), two rows added
  with `integration.md`'s proposed text unchanged (they read correctly in the status line), and a
  note that the page shows the sentence only, never the error's name or message. Retry table:
  `call limit` added to "Refused when"; new row for `unexpected error` (retry allowed once); new
  paragraph "What page 3 shows after `call limit`" (the normal failed page; the button is shown and
  refused, §1.2). §5 `RETRY_NOT_ALLOWED`: four reasons became five. **Found and recorded, not
  decided:** the call limit counts across both databases, so "Start a new review from Filing rules"
  would not help after it; drafted a different ending (Open Question 25). Left alone as history:
  G-10's "seventh reason" and D12's "six failure reasons". Approval status left `approved`: wording
  only. The backend already had both sentences word for word (`FAILURE_SENTENCES`), so the page and
  the code agree. No code. No model call.
- 2026-11-24 · persona `ux-designer` · action `design-ux` (revision, H-093 follow-up, operator decision) ·
  same branch · Open Question 25 **closed** by the operator, with one added sentence: the `call limit`
  refusal now ends "Ask the operator to review the limit." (§5 row and Open Question 25 updated).
  H-094 re-addressed to `@backend.eng`, no longer waiting. Approval status left `approved`. No code.
  No model call.
