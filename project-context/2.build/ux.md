# UX note: the seven pages (Block B5)

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

**Approval status**: `pending`

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
   (CR-030), and **"Demo row on"** when the planted-row switch was on. Both as text tags next to the
   H1, never colour alone. The mock-ups leave both out; the built app keeps them (H-004, H-005).
4. **Refusal message** (only after a refused request, §5: the full sentence, or a short line with a
   "Go to rule {i}" link when the refusal is about one card).
5. The stepper (§1.4), on pages 3 to 6.
6. The page content.

Page `<title>` pattern: `<Page name> · ACME Compliance calendar (demo)`. After a refusal, prefix it
with `Not done: ` so a screen reader announces the refusal when the page loads.

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

Stage B (AI checks what applies) is shown as the start of step 3, and Stage C (code works out the
dates) as the start of step 4, so the specialist sees four steps, not six (see Assumptions).

Each step carries a word, not just a colour: **"Done"**, **"In progress"**, **"Your turn"** or
**"Not started"**. Steps that are done or "Your turn" link to their page. It is an ordered list
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

All wording in this note goes through the copy review before the demo (CR-019).

### 1.7 Signed out, wrong role, not found, server error

| Case | What happens | Words |
|---|---|---|
| Not signed in, any page | Redirect to `/sign-in` | — |
| GP opens a specialist page | 403 page in the shared frame | **"This page is for the compliance specialist. You are signed in as the General Partner, so you can view the published calendar only."** Link: **"Go to the calendar"** |
| Run ID does not exist | 404 page | **"There is no review with this number."** Link: **"Go to Filing rules"** |
| Unexpected server error, specialist | Plain page | **"Something went wrong on the server. Nothing was changed by this request. Go back to Filing rules and try again."** |
| Unexpected server error, GP | Plain page, no working content (CR-012) | **"The calendar could not be shown just now. Try again in a few minutes."** |

The mock-ups do not design these pages (H-026, still open). The wording above stands until they do.

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

1. No sidebar (no identity, no navigation). The "acme" wordmark at the top.
2. H1 **"Sign in to the demo"**
3. Line: **"Choose a role to explore the demo with mock data. You don't need a password."** This
   line carries the demo label on this page (UX-001), since there is no sidebar.
4. Two buttons, each its own form (`POST /sign-in`), equal weight, nothing preselected:
   - **"Sign in as the compliance specialist"**, with hint below: "Checks the rules AI drafts,
     then publishes the calendar."
   - **"Sign in as the General Partner / Fund Manager"** (U6, H-018), with hint below: "Sees the
     published calendar only. Cannot change anything."
5. Line: **"The fund and the firm are fictional."**

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
   | Agents | "Stand-in agents" or "Real model" |
   | Demo row | "On" or "Off" |
   | Status | Status words (§1.5) |
   | Ended because | For `FAILED`, the reason in words (page 3); for `ABANDONED` and `DECLINED`, the first line of the written reason; otherwise empty |

5. **Start a new review** (under the table), one form (`POST /specialist/runs`):
   - Text: "Fund: **Bramblegate Credit Opportunities SICAV** (fictional, `FND-DEMO-01`)".
   - Text: "Agents: **stand-in agents** (fixed test outputs, no AI model is called)" or
     "Agents: **real model**", from the server setting (CR-030).
   - Checkbox, **unticked**: **"Add the planted demo row"**. Hint: "Adds one row that looks
     plausible but must not be approved. Use it only to show the review in a demo. The choice is
     recorded in the audit log." The built app keeps this switch; the mock-ups leave it out (H-005).
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
| Refused (`RUN_ACTIVE`) | Same page. Beside "Start a new review": the full `RUN_ACTIVE` sentence (§5). At the top: **"Not done. A new review can't start while review {n} is in progress."** and the link **"Go to 'Start a new review'"** |
| Refused (`VALIDATION`) | Same page, the full sentence at the top and next to "Start a new review" |

**Actions**

| Action | Then |
|---|---|
| Start a new review | Success: redirect to that review's status page (step 1, AI drafting). Refused: §5 |
| Open a review | Go to its review status page |

---

### Page 3 · Review status (`/specialist/runs/{run_id}`)

**Purpose.** The only place the specialist waits. Shows where the review is, each unit, the cost,
and what to do next. **Who:** specialist. **No re-run action, ever.**

**On screen, in order**

1. Shared frame; breadcrumb ending **"Review {n}"**.
2. H1 for the state (see the states table), with the run labels (Stand-in agents, Demo row on).
3. Stepper (§1.4).
4. **Status line** (large text): the status words (§1.5) plus the sentence for the state below.
5. **Next step** (only at a step that waits for the specialist, or when ended): one primary link
   (see states).
6. **Refresh controls** (only while AI or code is working, see below).
7. **Units**, as a real table per group: Unit · Status. Status words: **"Waiting"**,
   **"Running"**, **"Done"**, **"Failed"**.
   - While step 1 runs, and in its record afterwards, two groups, each with its one-line
     intro. This is the **only** page that names the two AI roles (U3, H-015):
     - **"Drafting the rules"**: "The first AI reads each source and writes a rule, quoting the
       exact words it relied on." One unit per source document, for example "CSSF Circular
       15/627".
     - **"Checking the drafts"**: "A second, separate AI compares every draft with all the sources
       and tells you where they disagree. It never changes a rule." One unit per rule, for example
       "Audited annual report".
   - Step 3: **"Checking what applies"**, one unit per approved rule.
   - Step 4: **"Working out the dates"**, one unit ("Code, no AI model").
8. **Cost so far**: "Model cost so far: **US$0.00**." For stand-in reviews add: "(stand-in agents
   make no model calls)". For real reviews add: "The review stops at US$2.50."
9. Review details: "Started Fri 13 Nov 2026, 14:00, by Compliance specialist (mock). Fund
   FND-DEMO-01."
10. **Abandon this review** (H2), only when the review waits for the specialist (see below).

**Automatic refresh (running only).** While the phase is `A_RUNNING`, `B_RUNNING` or `C_RUNNING`,
the page reloads itself every 3 seconds (§3 Freshness). Next to the status line:

- Text: **"This page refreshes every 3 seconds while AI is working."** (In step 4: "… while the
  dates are worked out.")
- Link: **"Refresh now"** (reloads the same page).
- Link: **"Stop automatic refresh"** (reloads the page with refresh off, for example
  `?refresh=off`; a display choice in the URL, not stored anywhere).

With refresh off: **"Automatic refresh is off."** Links: **"Refresh now"** · **"Turn automatic
refresh back on"**. "Refresh now" keeps refresh off.

At a step that waits for the specialist, or in an ended state, the page does not refresh and these
controls are not shown.

**States and their words**

| State | H1 | Status line sentence | Next step link |
|---|---|---|---|
| `A_RUNNING` | **"Nothing for you to do yet"** | "AI is drafting the rules and checking each one against the sources. You check the rules when it finishes. Units finish one by one below." | — |
| `AT_G1` | **"The rules are ready for you to check"** | "AI drafted **{n} rules** and checked each one against the sources. Nothing reaches the calendar until you approve it." | **"Check the rules"** → page 4 |
| `B_RUNNING` | **"Nothing for you to do yet"** | "You've finished checking the rules. AI is now checking whether each approved rule applies to the fund." | — |
| `AT_G2` | **"Ready for you to confirm what applies"** | "AI checked **{n} rules** against the fund's facts. **{u} of them** need your decision because AI can't tell." | **"Confirm what applies"** → page 5 |
| `C_RUNNING` | **"Nothing for you to do yet"** | "You've confirmed what applies. The dates are being worked out by code. This takes a few seconds." | — |
| `AT_G3` | **"The calendar is ready to check"** | "The calendar is ready: **{n} dates**." | **"Check the calendar and publish"** → page 6 |
| `COMPLETED` | **"Published"** | "Published on {date} at {time}. The General Partner now sees this calendar." | **"See the calendar as the General Partner sees it"** → `/calendar` |
| `DECLINED` | **"Closed without publishing"** | "Closed without publishing on {date} at {time}. Nothing was published. The General Partner still sees what they saw before." Then: "What needs to change: {reason}" | **"Go to Filing rules"** |
| `ABANDONED` | **"Abandoned"** | "Abandoned at step {k} ({step name}) on {date} at {time}. Nothing was published, and the decisions made so far stay in the audit log." Then: "Your reason: {reason}" | **"Go to Filing rules"** |
| `FAILED` | **"This review failed"** | "This review failed at step {k} ({step name}), at unit **{unit}**. {reason sentence}. Nothing moved forward. Start a new review from Filing rules." | **"Go to Filing rules"** |

**Failure reason sentences** (from the six reasons in §4):

| Reason code | Sentence |
|---|---|
| `model service` | "The model service did not answer in time, or returned an error, twice" |
| `stage time limit` | "This step took longer than its time limit" |
| `invalid output` | "The AI returned output in the wrong format, so it was not used" |
| `cost cap` | "The review reached its cost limit of US$2.50" |
| `service restarted` | "The application restarted while AI was working" |
| `calendar generation` | "The dates could not be worked out into one complete calendar" |

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

The mock-ups do not design the abandon control or the failed, abandoned and closed states
(H-026, still open). The behaviour and wording above stand until they do.

**Actions**

| Action | Then |
|---|---|
| Refresh now / Stop / Turn back on | Same page, refresh on or off |
| Next step link | The step page, or the calendar, or Filing rules |
| Abandon review | Success: same page, `ABANDONED` state. Refused: `REASON_REQUIRED`, `VERSION_MISMATCH`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE` |

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
| Approve rule / Reject rule | Success: redirect to G1 at that rule's anchor, now showing the decision and the "Next rule to decide" link |
| Approve on the demo rule | Refused: same page, landing on the demo rule card (`#row-{i}`). The `DEMO_ROW_NOT_APPROVABLE` sentence sits in the card; its status tag changes to "Approval blocked"; the top shows the short line and "Go to rule {i}". The rule stays undecided, nothing is preselected, and the refusal is recorded in the audit log. The specialist then uses Reject |
| Finish checking | Success: redirect to review status (step 3, AI checking what applies, auto-refresh) |

**Review-time budget (§7, 30 minutes from G1 open to G3 published).** Target about 2 minutes per
row, so G1 takes about 15 minutes for 7 rows. Supporting decisions:

- Everything a decision needs is on one card, in reading order: quote → check → paragraph → flags →
  fields → decision. No clicking away.
- The redirect returns to the same row with a link to the next one.
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

      When AI said **"applies"** or **"doesn't apply"** (not in the mock-ups, see H-026; the
      question is wording this note adds):
      - Question: **"What's your answer on this rule?"**
      - **"Confirm: applies"** (or **"Confirm: doesn't apply"**): text **"If you confirm, the
        General Partner will read AI's reasoning above as the explanation."** (for "doesn't
        apply": **"If you confirm, this obligation is left off the calendar."**). No reason field.
        Button: **"Confirm: applies"** or **"Confirm: doesn't apply"**.
      - **"Overrule: doesn't apply"** (or **"Overrule: applies"**, the opposite of AI's): field
        **"Reason for overruling"** with the hint for that outcome (below). Button: **"Overrule:
        doesn't apply"** / **"Overrule: applies"**.

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
   8. **Decided** (replaces the form): "**Confirmed: applies** by Compliance specialist (mock) at
      14:21." / "**Overruled: doesn't apply** … Reason: …" / "**Added, marked 'May not be
      required'** … Reason: …", then **"Next answer to decide"** link.
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

The mock-ups design only the "AI can't tell" case. Overruling an ordinary answer stays as written
above until H-026 decides it.

**After each action**

| Action | Then |
|---|---|
| Confirm / Overrule / Decide | Success: redirect to G2 at that card. Refused: `REASON_REQUIRED`, `ALREADY_DECIDED`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE`, `VALIDATION` |
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
     uses these paragraphs. The calendar has nothing from them."**
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
3. The fixed message (DL-27, word for word), **and nothing else**: no count, no review, no status,
   no summary cards, no week grid:
   **"Your obligations calendar is being prepared and checked by a specialist. Nothing has been
   published yet."** The mock-up's empty state uses other words; DL-27 wins (see Open Question 12).

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
5. **Summary cards** (a row of three; operator decision, 2026-11-13): **Entries in {year}** {n} ·
   **Due next** {date} · **May not be required** {p}. Every value is a fact of the published
   calendar, computed by the server.
6. **Week grid** (H2 **"The next two months"**): the two calendar months from the next due date,
   seven columns Mon to Sun. Each entry shows What and Who files in words, and "May not be
   required" where it applies. The next due date carries the word **"Due next"**. Published
   entries only: nothing the General Partner cannot also read in the table below.
7. **Entries** (H2 **"All entries for {year}"**): a real table sorted by due date, grouped by
   month. Columns: **When** (due date) · **What** ·
   **Who files** ("Not confirmed" for "not known") · **Why** (the reason, then "Source: {document},
   paragraph {id}" and the quote in a smaller blockquote).
   Entries the specialist added without confirmation carry the label **"May not be required"**
   (word, not just colour; U5, H-017) and this code-generated note under the reason: **"May not be
   required: it is not yet confirmed that this applies to the fund. It is listed so that it is not
   missed. It does not mean that any registration or marketing is permitted."** The specialist's
   reason is still shown as the "Why".
8. Nothing else: no draft, flag, other mark, review status, or link to a failed, abandoned or
   closed review. The summary cards and the week grid show published facts only.
   **Moved marks are specialist-only** (operator decision 2026-11-14, Open Question 15; SAD §3
   page 7, DL-49): this page has no "Moved off a weekend" card, count, chip, chart colour or legend
   entry, and no open-question mark. The Month and Year views and charts (block B12) follow the
   same rule.

**Phone width (≤ 480 px).** The table keeps its table markup but each row stacks as a block:
"When" first in bold, then What, Who files, Why, each with its column name as a visible label.
The week grid becomes a list of the days that have entries ("Mon 11 Jan"). No horizontal page
scroll.

**States**

| State | What shows |
|---|---|
| Nothing published yet | The fixed DL-27 message only |
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
- **About the page or the review** (for example `GATE_INCOMPLETE`, `VERSION_MISMATCH`,
  `ACK_REQUIRED`): the full sentence in a box at the top under the H1, headed **"Not done"**, and
  again next to the control it concerns.
- **Always:** on the page, never as a browser pop-up, and recorded in the audit log (W-18,
  H-009). Any text the specialist typed in a reason field is shown again so it is not lost; radio
  choices and the G3 checkbox are shown **empty** again (nothing preselected).

**What.** The backend returns the code and the sentence (§4 of the SAD); this table is the wording
for that sentence. `{…}` are values the server fills in.

| Code | Context | Sentence |
|---|---|---|
| `DEMO_ROW_NOT_APPROVABLE` | Approve on the planted row | **"Approval blocked: no legal basis. This rule doesn't appear in the regulation text. Reject it with a reason."** Then the line **"Recorded in the audit trail."** (A3, H-006; now the CR-029 sentence, DL-44 updated 2026-11-14) |
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
| `ACK_REQUIRED` | Publish, box not ticked | **"Tick the box to confirm you have read the rejected rules and the unused paragraphs. Then publish again."** |
| `ACK_REQUIRED` | Publish, lists changed | **"The lists of rejected rules or unused paragraphs are not the ones shown when you ticked the box. Read the lists above and tick the box again."** |
| `VERSION_MISMATCH` | Any review-level action | **"This review has moved on since the page was opened. The page now shows where it is. Check it, then try again if you still need to."** |
| `RUN_ACTIVE` | Start a new review | **"Review {n} is still in progress, so a new review can't start. Finish it, or abandon it at its step, first."** + link **"Open review {n}"**, then the line **"Recorded in the audit trail."** (H-009) |
| `RUN_NOT_ACTIVE` | Any decision on an ended review | **"This review has ended ({status words}), so it cannot take more decisions. Start a new review from Filing rules."** |
| `RUN_STAGE_RUNNING` | Abandon or decide while AI or code works | **"AI is still working on step {k}, so this cannot be done yet. It finishes by itself; follow it on the review status page."** (step 4: "The dates are still being worked out, …") |
| `FORBIDDEN` | GP on a specialist action | **"This page is for the compliance specialist. You are signed in as the General Partner, so you can view the published calendar only."** |
| `VALIDATION` | Decision submitted with no answer chosen (G1, G2 or G3; DL-48, H-030). Shown beside the form (inside the card at G1 and G2, with the short top line; at G3 next to the question) and at the top | **"Choose an answer first, then use its button. Nothing was saved."** |
| `VALIDATION` | Malformed form, a "who files" value not offered, or a G3 answer that doesn't match the button used | **"Part of this form was not valid ({field}), so nothing was saved. Check the form and try again."** |

## 6. Visual style

The look (tokens, type, spacing, components, status chips, contrast) is in
**`project-context/2.build/style-note.md`** (operator decision, 2026-11-13). This note does not
repeat it.

**Done (U8, H-020).** The operator accepted a new look for the MVP: Lexend headings, Inter body,
6px corners on cards and buttons, pill chips and Iconoir icons (MIT licence, inline SVG).
`style-note.md` now describes it, with `docs/prototype/app.css` as the source of truth. If the two
disagree, the stylesheet wins. U7 and U8 together get half a day; anything that does not fit is
dropped.

B6 is still the first block dropped if time runs out: every page must stay usable and accessible
unstyled.

## 7. Accessibility (WCAG 2.2 AA, PRD §6)

- Headings in order: one H1, H2 per section or card.
- Real tables with `<th scope>` for the run list, units, coverage, rejected rows, calendar.
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
| UX-008 | Before the first publication, `/calendar` shows only the DL-27 message | DL-27, CR-012 |
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
| UX-013 | Run status offers no re-run action | §3 page 3 |
| UX-014 | A stand-in happy path from G1 open to G3 published takes a first-time reader under 30 minutes (from audit timestamps) | §7, EC-011 |

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
- **"Approve and go to next row" in one click**, to save time at G1. Only if the 30-minute target
  is missed in the rehearsal.

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
  §4 routes and validation (read for H-030).
- `docs/prototype/HANDOVER.md` and `docs/prototype/build.py` (the mock-up wording and layout).
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

## Mock-up differences this revision does not apply

These are in `docs/prototype/` but are not among the decisions applied here, so ux.md does not
follow them yet: the calendar's Month and Year views and charts (A10, H-012: built last, one-day
timebox); the "For December 2026" period line (A8, H-010: post-MVP); the Funds pages (future
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

D6 and D8 need no SAD change. D1 to D5 were changed in sad.md by `@system.arch` (H-030). D7 is
wording only.

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
