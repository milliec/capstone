# UX note: the seven pages (Block B5)

Owner: `@ux.designer` (`*design-ux`). For: `@frontend.eng` (templates in `backend/web/templates/`)
and `@backend.eng` (the refusal sentences in §5 are the text the service functions return).

Source of scope: `sad.md` → Build card, Never row, Order of work, and the sections it points to for
the pages (§3 "The seven pages", §4 routes and refusal codes, §7 review target, the run-state
"Transitions and guards" table, and the W- and CR- rows those name). Nothing here comes from
Future Work, Appendix A or the tag `sad-full-design`.

This note writes no HTML, template or code. It says what each page shows, in what order, in which
states, what each action does, and the exact words.

**Approval status**: `pending`

---

## 1. Rules that hold on every page

### 1.1 Who uses what

| Role (mock identity) | Pages | Can change anything? |
|---|---|---|
| **Compliance specialist** | 1 to 7 | Yes: starts runs, decides rows and verdicts, publishes or declines, abandons |
| **GP** (Bramblegate Partners, fictional) | 1 and 7 only | No. Sees only the published calendar. Never sees a draft, failed, abandoned or declined run, a flag, a mark other than "precautionary", or any run status |

### 1.2 The page never decides

- Every status, count, flag, date, mark and decision on a page comes from the server.
  The templates only show it.
- **No button is hidden or disabled to enforce a rule.** If an action is not allowed, the server
  refuses it and the page shows why (§5). This is why the demo row and a row that failed the quote
  check both keep their Approve button.
- No HTML `required`, `disabled` or `pattern` attributes on decision forms. A missing reason is
  refused by the server with `REASON_REQUIRED`, not stopped in the browser.
- No placeholders: no "coming soon", no disabled future feature, no greyed-out control (§3,
  SD MN-007).
- No bulk action, no "approve all", nothing preselected (SD AC-026). Every radio group starts with
  nothing chosen and every checkbox starts unticked.

### 1.3 The shared frame (base template)

Top to bottom, on every page:

1. **Demo label** (plain text strip, always first): **"Demo with mock data. The fund, the people and
   the documents are fictional."**
   This is static text only. It is *not* the F-18 hosted-demo banner: no Reset button, no "someone
   may be mid-run" line.
2. **Header**: product name **"Obligations calendar"**, then on the right
   "Signed in as **Compliance specialist (mock)**" or "Signed in as **GP, Bramblegate Partners
   (mock)**", and a **"Sign out"** button (a form, `POST /sign-out`).
3. **Navigation** (specialist only): **"Runs"** · **"GP calendar (read-only)"**. The GP has no
   navigation; the calendar is their only page.
4. **Run labels** (any page that shows a run): **"Stand-in agents"** when the run used them
   (CR-030), and **"Demo row on"** when the planted-row switch was on. Both as text tags next to the
   run title, never colour alone.
5. **Refusal message** (only after a refused request, §5).
6. The page content.

Page `<title>` pattern: `<Page name> · Obligations calendar (demo)`. After a refusal, prefix it with
`Not done: ` so a screen reader announces the refusal when the page loads.

### 1.4 The three-step stepper (one sitting, not three interruptions)

Every specialist page about one run (3 to 6) shows the same stepper under the run title:

> **Stage A** → **1. Rule review (G1)** → **Stage B** → **2. Applicability (G2)** → **Stage C** →
> **3. Calendar (G3)**

Each step carries a word, not just a colour: **"done"**, **"now"**, **"running"** or **"to do"**.
Steps that are done or now link to their page. It is an ordered list (`<ol>`) with
`aria-current="step"` on the current one.

How the flow feels like one sitting:

- Each gate page ends with one primary button that finishes the step and starts the next stage.
- Finishing a gate takes the specialist to run status, which refreshes itself while the stage runs
  and then shows one big link straight into the next gate. No hunting, no extra clicks.
- Stage C (dates, code only) is expected to take a few seconds, so G2 → G3 feels immediate.

### 1.5 Status words

A status is always a word first; colour only supports it.

| Server value | Words shown | Tone (colour role) |
|---|---|---|
| `ACTIVE` · `A_RUNNING` | **Running: Stage A** (reading the sources and checking each row) | info |
| `ACTIVE` · `AT_G1` | **Waiting for you: rule review (G1)** | action |
| `ACTIVE` · `B_RUNNING` | **Running: Stage B** (checking whether each rule applies to the fund) | info |
| `ACTIVE` · `AT_G2` | **Waiting for you: applicability (G2)** | action |
| `ACTIVE` · `C_RUNNING` | **Running: Stage C** (working out the dates) | info |
| `ACTIVE` · `AT_G3` | **Waiting for you: calendar (G3)** | action |
| `FAILED` | **Failed** | problem |
| `ABANDONED` | **Abandoned** | neutral |
| `DECLINED` | **Declined at G3** | neutral |
| `COMPLETED` | **Published** | success |

### 1.6 Voice (DL-05)

- Plain British English. Short sentences. State the fact and what happens next.
- No reassurance ("Don't worry"), no alarm ("Error!"), no advice, no "please". No exclamation marks.
- Cite the source (paragraph ID, fact ID) wherever text makes a claim.
- GP text is for a non-lawyer, stays neutral, and never implies that anything is permitted (DL-01).
- Buttons say what they do: verb + object ("Approve row", "Publish calendar"), never "OK" or
  "Submit".
- Dates in full: "Mon 2 Feb 2027". Times: "14:02".

All wording in this note goes through the copy review before the demo (CR-019).

### 1.7 Signed out, wrong role, not found, server error

| Case | What happens | Words |
|---|---|---|
| Not signed in, any page | Redirect to `/sign-in` | — |
| GP opens a specialist page | 403 page in the shared frame | **"This page is for the compliance specialist. You are signed in as a GP, so you can view the published calendar only."** Link: **"Go to the calendar"** |
| Run ID does not exist | 404 page | **"There is no run with this number."** Link: **"Go to the run list"** |
| Unexpected server error, specialist | Plain page | **"Something went wrong on the server. Nothing was changed by this request. Go back to the run list and try again."** |
| Unexpected server error, GP | Plain page, no working content (CR-012) | **"The calendar could not be shown just now. Try again in a few minutes."** |

---

## 2. Flow

```text
Sign-in ─┬─ specialist ─> Run list ─(Start run)─> Run status [Stage A running, auto-refresh]
         │                                            │
         │                                            v
         │                         G1 rule review ─(Finish rule review)─> Run status [Stage B running]
         │                                                                    │
         │                                                                    v
         │                         G2 applicability ─(Finish applicability)─> Run status [Stage C running]
         │                                                                    │
         │                                                                    v
         │                         G3 calendar ─(Publish)─> Run status [Published] ─> GP calendar
         │                                    └(Decline)─> Run status [Declined]
         │   (At any gate: Abandon on run status → Run status [Abandoned])
         │
         └─ GP ─────────> GP calendar ("being prepared" message, or the published calendar)
```

After every form: on success, redirect to the page that shows the result; on refusal, the same
page again with the refusal message (§3, §4 of the SAD).

---

## 3. The seven pages

### Page 1 · Sign-in (`/sign-in`)

**Purpose.** Choose one of two mock identities. **Who:** anyone. `/` redirects here, or to the
role's first page when already signed in.

**On screen, in order**

1. Shared frame (demo label; no header identity, no navigation).
2. H1 **"Sign in to the demo"**
3. Line: **"There are no passwords. Choose who you want to be."**
4. Two buttons, each its own form (`POST /sign-in`), equal weight, nothing preselected:
   - **"Sign in as the compliance specialist"**, with hint below: "Runs the agents, reviews each
     step and publishes the calendar."
   - **"Sign in as a GP"**, with hint below: "Sees the published calendar only. Cannot change
     anything."

**Actions**

| Action | Then |
|---|---|
| Sign in as the compliance specialist | Redirect to `/specialist/runs` |
| Sign in as a GP | Redirect to `/calendar` |
| Sign out (any page) | Redirect to `/sign-in` |

**States.** Only the default state. A malformed request gets `VALIDATION` (§5).

---

### Page 2 · Run list (`/specialist/runs`)

**Purpose.** See every run and its state; start a new run. **Who:** specialist.

**On screen, in order**

1. Shared frame.
2. H1 **"Runs"**
3. **Active-run notice** (only when a run is `ACTIVE`): "**Run {n} is active.** {status words}."
   Link: **"Open run {n}"**.
4. **Start a new run** (H2), one form (`POST /specialist/runs`):
   - Text: "Fund: **Bramblegate Credit Opportunities SICAV** (fictional, `FND-DEMO-01`)".
   - Text: "Agents: **stand-in agents** (fixed test outputs, no AI model is called)" or
     "Agents: **real model**", from the server setting.
   - Checkbox, **unticked**: **"Add the planted demo row"**. Hint: "Adds one row that looks
     plausible but must not be approved. Use it only to show the review in a demo. The choice is
     recorded in the audit log."
   - Button: **"Start run"**.
   - The form is always shown, even while a run is active. The server refuses a second run (§5,
     `RUN_ACTIVE`).
5. **All runs** (H2): a real table, newest first.

   | Column | Content |
   |---|---|
   | Run | "Run 4", links to run status |
   | Started | "Fri 13 Nov 2026, 14:00" |
   | Agents | "Stand-in agents" or "Real model" |
   | Demo row | "On" or "Off" |
   | Status | Status words (§1.5) |
   | Ended because | For `FAILED`, the reason in words (page 3); for `ABANDONED` and `DECLINED`, the first line of the written reason; otherwise empty |

**States**

| State | What shows |
|---|---|
| Empty (no runs yet) | Table replaced by: **"No runs yet. Start the first run above."** |
| Populated | Table as above |
| Run active | Active-run notice at the top |
| Refused (`RUN_ACTIVE`, `VALIDATION`) | Same page, refusal at the top and next to "Start run" |

**Actions**

| Action | Then |
|---|---|
| Start run | Success: redirect to that run's status page (Stage A running). Refused: §5 |
| Open a run | Go to its run status page |

---

### Page 3 · Run status (`/specialist/runs/{run_id}`)

**Purpose.** The only place the specialist waits. Shows where the run is, each unit, the cost,
and what to do next. **Who:** specialist. **No re-run action, ever.**

**On screen, in order**

1. Shared frame.
2. H1 **"Run {n}"** with the run labels (Stand-in agents, Demo row on).
3. Stepper (§1.4).
4. **Status line** (large text): the status words (§1.5) plus the sentence for the state below.
5. **Next step** (only at a gate, or when ended): one primary link (see states).
6. **Refresh controls** (only while a stage is running, see below).
7. **Units** (H2) table: Unit · Stage · Status. Unit names, for example "Extract: source document
   SRC-A", "Verify: row OBL-03", "Judge: row OBL-04", "Work out dates". Status words: **"Waiting"**,
   **"Running"**, **"Done"**, **"Failed"**.
8. **Cost so far**: "Model cost so far: **US$0.00**." For stand-in runs add: "(stand-in agents
   make no model calls)". For real runs add: "The run stops at US$2.50."
9. Run details: "Started Fri 13 Nov 2026, 14:00, by Compliance specialist (mock). Fund
   FND-DEMO-01."
10. **Abandon this run** (H2), only when the run waits at a gate (see below).

**Automatic refresh (running only).** While the phase is `A_RUNNING`, `B_RUNNING` or `C_RUNNING`,
the page reloads itself every 3 seconds (§3 Freshness). Next to the status line:

- Text: **"This page refreshes every 3 seconds while the stage runs."**
- Link: **"Refresh now"** (reloads the same page).
- Link: **"Stop automatic refresh"** (reloads the page with refresh off, for example
  `?refresh=off`; a display choice in the URL, not stored anywhere).

With refresh off: **"Automatic refresh is off."** Links: **"Refresh now"** · **"Turn automatic
refresh back on"**. "Refresh now" keeps refresh off.

At a gate or in an ended state the page does not refresh and these controls are not shown.

**States and their words**

| State | Status line sentence | Next step link |
|---|---|---|
| `A_RUNNING` | "Stage A is running: the agents read the sources, quote each rule and check it. Units finish one by one below." | — |
| `AT_G1` | "Stage A is finished. **{n} rows** are waiting for your review." | **"Review the rows (step 1 of 3)"** → G1 |
| `B_RUNNING` | "Rule review is finished. Stage B is running: an agent checks whether each approved rule applies to the fund." | — |
| `AT_G2` | "Stage B is finished. **{n} verdicts** are waiting for your review, **{u} of them 'unsure'**." | **"Check applicability (step 2 of 3)"** → G2 |
| `C_RUNNING` | "Applicability is finished. Stage C is working out the dates. This takes a few seconds." | — |
| `AT_G3` | "The calendar is ready: **{n} entries**." | **"Review the calendar (step 3 of 3)"** → G3 |
| `COMPLETED` | "Published on {date} at {time}. GPs now see this calendar." | **"See the calendar as GPs see it"** → `/calendar` |
| `DECLINED` | "Declined at G3 on {date} at {time}. Nothing was published. GPs still see what they saw before." Then: "Your reason: {reason}" | **"Go to the run list"** |
| `ABANDONED` | "Abandoned at {gate} on {date} at {time}. Nothing was published, and the decisions made so far stay in the audit log." Then: "Your reason: {reason}" | **"Go to the run list"** |
| `FAILED` | "This run failed in **{stage}**, at unit **{unit}**. {reason sentence}. No gate opened and nothing moved forward. Start a new run from the run list." | **"Go to the run list"** |

**Failure reason sentences** (from the six reasons in §4):

| Reason code | Sentence |
|---|---|
| `model service` | "The model service did not answer in time, or returned an error, twice" |
| `stage time limit` | "The stage took longer than its time limit" |
| `invalid output` | "An agent returned output in the wrong format, so it was not used" |
| `cost cap` | "The run reached its cost limit of US$2.50" |
| `service restarted` | "The application restarted while the stage was running" |
| `calendar generation` | "The dates could not be worked out into one complete calendar" |

**Abandon this run** (only in `AT_G1`, `AT_G2`, `AT_G3`). One form,
`POST /specialist/runs/{run_id}/abandon`, with the run version as a hidden field:

- Text: **"Abandoning ends this run. Nothing is published and nothing is undone: decisions made so
  far stay in the audit log. You can then start a new run. Use this, for example, after rejecting a
  row by mistake."**
- Field: **"Reason for abandoning"** (multi-line). Hint: "Recorded in the audit log. Specialists
  only."
- Button: **"Abandon run"** (secondary style, not the primary colour).

While a stage is running the form is not shown; instead: **"You can abandon this run once it
reaches a gate. A running stage always ends by itself."** If an old page sends the form anyway,
the server answers `RUN_STAGE_RUNNING` (§5).

**Actions**

| Action | Then |
|---|---|
| Refresh now / Stop / Turn back on | Same page, refresh on or off |
| Next step link | The gate page, or the calendar, or the run list |
| Abandon run | Success: same page, `ABANDONED` state. Refused: `REASON_REQUIRED`, `VERSION_MISMATCH`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE` |

---

### Page 4 · G1 rule review (`/specialist/runs/{run_id}/g1`)

**Purpose.** Decide each extracted row once: approve it (setting its business-day rule, and who
files when the source is silent) or reject it with a reason. **Who:** specialist.

**Not on this page** (not in the Build card): editing a row, adding a row, reopening a decided
row (DL-22), bulk approve. See §9.

**On screen, in order**

1. Shared frame; H1 **"Step 1 of 3: Rule review (G1)"**; run labels; stepper.
2. Intro: **"Decide each row once. Approving lets the rule into this run's calendar. Rejecting
   keeps it out. Each decision is recorded with your name and the time, and cannot be changed in
   this run."**
3. **Progress**: "**{d} of {n} rows decided.** {n−d} to decide."
4. **Row index** (a short list of jump links, one per row): "Row 3 · OBL-03 · Monthly report ·
   **To decide**" / "… · **Approved**" / "… · **Rejected**". Rows with a flag, a failed quote
   check or the demo tag show it here too, in words. This gives the specialist the shape of the
   work in one glance.
5. **One card per row** (shared "row card" part, §3 of the SAD), each with its own `id` anchor, in
   this order:
   1. H2: "**Row {i} of {n}**: {obligation summary}" plus tags: **"Demo"** (planted row),
      **"Flag"**, **"Quote check failed"**, **"Depends on open question OQ-7"** as applicable.
   2. **Quote** (blockquote): the word-for-word quote. Caption: "Quote from paragraph {para_id}".
   3. **Quote check**, one line:
      - pass: **"Quote check: passed. The quote appears word for word in paragraph {para_id}."**
      - fail: **"Quote check: failed. The quote does not appear word for word in paragraph
        {para_id}. This row can only be rejected."**
   4. **Cited paragraph** (full text, headed "Paragraph {para_id}, {source document}").
   5. **Flags** (shared "flag" part), one box per flag, each with both texts (DL-03):
      - Heading: **"Verifier flag: inside the same document"** (`internal`) or **"Verifier flag:
        against another source"** (`cross_source`).
      - "**The row says:** {row text}"
      - "**The source says:** {source text}, paragraph {id}"
      - If no flag: **"No verifier flags."** (so absence is stated, not implied)
   6. **Row fields** (definition list): What must be done · Frequency · Due relative to · Offset ·
      Recipient · **Who files, as the source says** (a party, or "Not stated in source") ·
      **Business-day rule, as the source says** ("Roll forward", "No roll" or "Not stated").
   7. **Open question mark** (only for rows the server marks, MVP: `OBL-02`): **"The business-day
      rule for this row depends on open question OQ-7, which is not yet answered. No rule is
      chosen for you. Whatever you choose, the entries will carry the OQ-7 mark at G3."**
   8. **Decision** (only while the row is undecided): two separate forms side by side, both
      `POST /specialist/rows/{row_id}/decision` with the row version as a hidden field.

      **Approve** (fieldset legend **"Approve this row"**):
      - **"Business-day rule"** (radio group, nothing chosen):
        "Roll forward to the next business day" · "No roll: keep the date" ·
        "Not confirmed: keep the earlier date and mark it".
        If none is chosen, the server refuses with `BUSINESS_DAY_RULE_REQUIRED` (§5).
      - **"Who files"** (radio group, nothing chosen), **only when the source says "Not stated in
        source"**. The options, exactly and in this order: **"AIFM"** · **"Fund administrator"** ·
        **"Auditor"** · **"Local reporting agent (Spain)"** · **"Tax advisor"** · **"Not known"**.
        Hint: "The source does not say who files. Choose the party, or 'Not known'. The
        compliance specialist and the GP are not filing parties."
      - **"Reason for approving over the flag"** (multi-line), **only when the row has a flag**.
        Hint: "Required because the verifier raised a flag. Specialists only."
      - Button: **"Approve row"** (primary).

      **Reject** (fieldset legend **"Reject this row"**):
      - **"Reason for rejecting"** (multi-line). Hint: "Required. Shown again at G3 and kept in the
        audit log. Specialists only."
      - Button: **"Reject row"** (secondary).

      The demo row and a quote-check-failed row show **exactly the same two forms**, with the
      Approve button visible and active. The server refuses the approval (§5).
   9. **Decided** (replaces the forms once decided):
      - "**Approved** by Compliance specialist (mock) at 14:02. Business-day rule: Roll forward.
        Who files: Fund administrator." (+ "Reason: {reason}" if over a flag)
      - "**Rejected** by Compliance specialist (mock) at 14:05. Reason: {reason}"
      - Link: **"Next row to decide"** (to the next undecided card), or **"All rows are decided.
        Finish the rule review"** (to the finish section).
6. **Paragraphs no row cites** (H2, the coverage view, W-03b):
   - Intro: **"These {k} paragraphs were loaded but no approved or undecided row cites them. This
     list does not say whether they contain obligations. If one does, the run missed it: reject or
     finish as usual, then start a new run. You will see this list again at G3."**
   - A real table: Paragraph ID · Source document · Text.
7. **Finish the rule review** (H2), one form, `POST /specialist/runs/{run_id}/g1/complete`, with
   the run version:
   - Text: **"When every row is decided, Stage B checks whether each approved rule applies to the
     fund. You cannot change rule decisions after this."**
   - Button: **"Finish rule review and start Stage B"** (primary). Always shown; the server refuses
     it while a row is undecided (`GATE_INCOMPLETE`).
8. Link at the bottom: **"Abandon this run"** → run status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G1 (`A_RUNNING`) | Short page: **"Stage A is still running. The rows will be here when it finishes."** Link: **"Watch progress on the run status page"** |
| At G1, rows to decide | Full page as above |
| At G1, all decided | Every card shows its decision; progress says **"All {n} rows decided."**; the finish section is the next thing to do |
| Refused | Same page; message at the top **and** inside the row card it concerns (the page scrolls to it via the anchor) |
| After G1 (`B_RUNNING` onward, or ended) | Read-only record: every card shows its decision, no forms, no finish button. Line under H1: **"The rule review is finished. This is the record of the decisions."** |

**After each action**

| Action | Then |
|---|---|
| Approve row / Reject row | Success: redirect to G1 at that row's anchor, now showing the decision and the "Next row to decide" link |
| Approve on the demo row | Refused: same page, message `DEMO_ROW_NOT_APPROVABLE` at the top and in the demo row card, the row still undecided, the refusal logged. The specialist then uses Reject |
| Finish rule review | Success: redirect to run status (Stage B running, auto-refresh) |

**Review-time budget (§7, 30 minutes from G1 open to G3 published).** Target about 2 minutes per
row, so G1 takes about 15 minutes for 7 rows. Supporting decisions:

- Everything a decision needs is on one card, in reading order: quote → check → paragraph → flags →
  fields → decision. No clicking away.
- The redirect returns to the same row with a link to the next one.
- No confirmation dialogs; the decision forms are already explicit.

---

### Page 5 · G2 applicability (`/specialist/runs/{run_id}/g2`)

**Purpose.** For each approved row, confirm the agent's verdict, override it with a reason, or
decide an "unsure". Every "unsure" must be decided. **Who:** specialist. Three decisions, as in
the SAD (§3 page 5, W-12): **confirm**, **override with a reason**, **decide an "unsure"**.

**On screen, in order**

1. Shared frame; H1 **"Step 2 of 3: Applicability (G2)"**; run labels; stepper.
2. Intro: **"For each approved rule, an agent checked the fund's facts and gave a verdict. Decide
   each verdict once. Every 'unsure' needs your decision."**
3. **Progress**: "**{d} of {n} verdicts decided.** {u} 'unsure' still to decide."
4. **Verdict index** (jump links): "OBL-04 · Spain annual return · **Unsure, to decide**". "Unsure"
   verdicts are listed first in the index, so the hardest decisions are visible early. Cards keep
   the row order.
5. **One card per verdict**:
   1. H2: "{obligation summary}" with row ID.
   2. **Agent's verdict** (big, in words): **"Applies"**, **"Does not apply"** or **"Unsure: needs
      your decision"**. "Unsure" has its own visual treatment and the word, not colour alone.
   3. **Agent's reasoning** (2 to 3 sentences), captioned "Agent's reasoning".
   4. **Missing information** (unsure only): "**What is missing:** {text}".
   5. **Cited facts** (real table, read-only): Fact ID · Fact · Value. Example row: "FACT-04 ·
      Registered for marketing in the second country · Unknown, not confirmed in fund records".
   6. **The rule** (collapsed under a `<details>` element, "Show the approved rule and quote"): the
      rule, quote and paragraph ID as approved at G1.
   7. **Decision** (undecided only). Separate forms, each
      `POST /specialist/verdicts/{verdict_id}/decision` with the verdict version:

      When the agent said **"Applies"** or **"Does not apply"**:
      - **Confirm** form: text **"If you confirm, GPs will read the agent's reasoning above as the
        explanation."** (only shown when the verdict is "Applies"; for "Does not apply" the text is
        **"If you confirm, this obligation is left off the calendar."**). Button: **"Confirm:
        applies"** or **"Confirm: does not apply"**.
      - **Override** form (legend **"Override the verdict"**): text "Your verdict: **Does not
        apply**" (or **Applies**, the opposite of the agent's). Field **"Reason for overriding"**
        with the hint for that outcome (below). Button: **"Override: does not apply"** /
        **"Override: applies"**.

      When the agent said **"Unsure"**: no Confirm. Two forms:
      - **"Applies (precautionary)"**: field **"Reason"** with the GP hint; button **"Decide:
        applies (precautionary)"**. Extra line: "GPs will see this entry labelled
        'Precautionary'."
      - **"Does not apply"**: field **"Reason"** with the audit-only hint; button **"Decide: does
        not apply"**.
      - Neither is preselected or styled as the default.

      **Reason hints depend on whether the decision creates a calendar entry** (W-17, SA-8). Each
      hint sits next to its field:

      | Decision | Creates an entry? | Hint next to the reason field |
      |---|---|---|
      | Override to **applies** | Yes | **"GPs will read this reason as the explanation for the entry. Write it for a non-lawyer: state the condition and the fact. No advice."** |
      | Unsure decided as **applies (precautionary)** | Yes | Same as above |
      | Override to **does not apply** | No | **"This obligation will not be on the calendar, so GPs will not see this reason. It is kept in the audit log for specialists."** |
      | Unsure decided as **does not apply** | No | Same as above |
   8. **Decided** (replaces the forms): "**Confirmed: applies** by Compliance specialist (mock) at
      14:21." / "**Overridden: does not apply** … Reason: …" / "**Decided: applies (precautionary)**
      … Reason: …", then **"Next verdict to decide"** link.
6. **Finish applicability** (H2), one form, `POST /specialist/runs/{run_id}/g2/complete`, run
   version:
   - Text: **"When every verdict is decided, the dates are worked out by code (no AI model). This
     takes a few seconds. You cannot change these decisions after this."**
   - Button: **"Finish applicability and work out the dates"** (primary). Always shown.
7. Link: **"Abandon this run"** → run status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G2 | **"Stage B has not finished yet. The verdicts will be here when it does."** Link to run status |
| At G2 | Full page |
| All decided | Progress **"All {n} verdicts decided."** |
| Refused | Same page, message at the top and in the card |
| After G2 | Read-only record, no forms. **"Applicability is finished. This is the record of the decisions."** |

**After each action**

| Action | Then |
|---|---|
| Confirm / Override / Decide | Success: redirect to G2 at that card. Refused: `REASON_REQUIRED`, `ALREADY_DECIDED`, `RUN_STAGE_RUNNING`, `RUN_NOT_ACTIVE`, `VALIDATION` |
| Finish applicability | Success: redirect to run status (Stage C running; usually at G3 within one refresh). Refused: `GATE_INCOMPLETE`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |

**Budget:** about 1 minute per verdict, 6 minutes for G2.

---

### Page 6 · G3 calendar (`/specialist/runs/{run_id}/g3`)

**Purpose.** See the whole calendar and what was left out, then publish it all at once or decline
it with a reason. **Who:** specialist.

**On screen, in order**

1. Shared frame; H1 **"Step 3 of 3: Calendar (G3)"**; run labels; stepper.
2. Intro: **"This is the whole calendar as GPs would see it, plus marks only you can see. Publish
   it all at once, or decline it."**
3. **Date conventions note** (DL-12, specialist version, a boxed note): **"The date conventions
   used here have not yet been checked against the legal texts. This does not stop you
   publishing. GPs see a note saying the same."**
4. **Calendar** (H2), a real table sorted by due date:

   | Column | Content |
   |---|---|
   | Due date | "Mon 2 Feb 2027" |
   | What | Obligation summary |
   | Who files | Party, or **"Not confirmed"** for "not known" |
   | Recipient | Recipient name |
   | Marks | Mark labels, in words (below). Empty when none |
   | Why (GPs see this) | The GP-facing reason, plus "Source: paragraph {id}" |

   **Mark labels** (shared "mark label" part):
   - **"Rolled"**: "Moved from Sat 31 Jan to Mon 2 Feb (roll forward)."
   - **"Rule not confirmed"**: "Business-day rule not confirmed. The earlier date is kept."
   - **"Precautionary"**: "Decided as applies, to be safe. GPs see this label."
   - **"Open question OQ-7"**: "The business-day rule depends on an unanswered question. Same
     date with or without a roll."
   Only "Precautionary" reaches the GP view.
5. **Rows you rejected at G1** (H2): table Row · Summary · Your reason. The demo row appears here
   tagged **"Demo"**. If none: **"No rows were rejected."**
6. **Paragraphs no approved row cites** (H2): table Paragraph ID · Source · Text. Intro: **"No
   approved row cites these paragraphs. The calendar has nothing from them."**
7. **Publish** (H2), one form, `POST /specialist/calendars/{calendar_id}/publish`, with the run
   version and the two ID lists exactly as shown above as hidden fields:
   - Checkbox, **unticked**: **"I have read the {r} rejected rows and the {k} uncited paragraphs
     listed above. Nothing from them will be on the published calendar."**
   - Text: **"Publishing shows this calendar to GPs straight away and replaces anything they saw
     before. It cannot be withdrawn in this version. A later run can publish a new calendar."**
   - Button: **"Publish calendar to GPs"** (primary).
8. **Decline** (H2), one form, `POST /specialist/calendars/{calendar_id}/decline`, run version:
   - Text: **"Declining ends this run without publishing. GPs keep seeing what they see now. You
     can start a new run."**
   - Field: **"Reason for declining"**. Hint: "Recorded in the audit log. Specialists only."
   - Button: **"Decline calendar"** (secondary).
9. Link: **"Abandon this run"** → run status `#abandon`.

**States**

| State | What shows |
|---|---|
| Not yet at G3 (`C_RUNNING` or earlier) | **"The calendar is not ready yet."** Link: **"Watch progress on the run status page"** |
| At G3 | Full page |
| Refused | Same page, message at the top and next to the checkbox (`ACK_REQUIRED`) or the reason field (`REASON_REQUIRED`). The checkbox is shown **unticked** again |
| After G3 | Read-only calendar with **"Published on {date} at {time}."** or **"Declined on {date} at {time}. Reason: {reason}"**, no forms |

**After each action**

| Action | Then |
|---|---|
| Publish calendar to GPs | Success: redirect to run status, `COMPLETED`, with the link to the GP view. Refused: `ACK_REQUIRED`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |
| Decline calendar | Success: redirect to run status, `DECLINED`. Refused: `REASON_REQUIRED`, `VERSION_MISMATCH`, `RUN_NOT_ACTIVE` |

**Budget:** about 5 minutes to read and publish. Total G1 + G2 + G3 ≈ 26 minutes, under the
30-minute target.

---

### Page 7 · GP calendar (`/calendar`)

**Purpose.** The published calendar, read-only. **Who:** GP; the specialist sees the same page,
read-only. **Must work at phone width.**

**On screen, in order (before the first publication)**

1. Shared frame.
2. H1 **"Obligations calendar"**
3. The fixed message (DL-27, word for word), **and nothing else**: no count, no run, no status:
   **"Your obligations calendar is being prepared and checked by a specialist. Nothing has been
   published yet."**

**On screen, in order (published)**

1. Shared frame.
2. H1 **"Obligations calendar: Bramblegate Credit Opportunities SICAV"**
3. Line: **"Published on {date}."** Plus **"Made with stand-in agents (fixed test outputs, no AI
   model)."** when the published run used them (CR-030).
4. **Calendar note** (one fixed sentence, DL-12): **"This calendar is not legal advice, and its
   date conventions have not yet been checked against the legal texts."**
5. **Entries**: a real table sorted by due date. Columns: **When** (due date) · **What** ·
   **Who files** ("Not confirmed" for "not known") · **Why** (the reason, then "Source: {document},
   paragraph {id}" and the quote in a smaller blockquote).
   Precautionary entries carry the label **"Precautionary"** (word, not just colour) and this
   code-generated note under the reason: **"Precautionary: it is not yet confirmed that this
   applies to the fund. It is listed so that it is not missed. It does not mean that any
   registration or marketing is permitted."**
6. Nothing else: no draft, flag, other mark, run status, or link to a failed, abandoned or declined
   run.

**Phone width (≤ 480 px).** The table keeps its table markup but each row stacks as a block:
"When" first in bold, then What, Who files, Why, each with its column name as a visible label.
No horizontal page scroll.

**States**

| State | What shows |
|---|---|
| Nothing published yet | The fixed DL-27 message only |
| Published | As above. A later declined, failed or abandoned run changes nothing here |
| Error | **"The calendar could not be shown just now. Try again in a few minutes."** (never working content, CR-012) |

**Actions.** None, apart from "Sign out". The specialist's navigation is still shown to the
specialist.

---

## 4. Shared parts (for the templates)

| Part | Used on | Contains |
|---|---|---|
| Base frame | All | Demo label, header, navigation, run labels, refusal slot (§1.3) |
| Stepper | 3 to 6 | §1.4 |
| Status words | 2, 3 | §1.5 |
| Row card | 4 (and the rejected list on 6) | Quote, check result, paragraph, flags, fields, decision or decision forms |
| Flag | 4 | Type heading and both texts |
| Decision form | 4, 5 | Separate explicit forms, nothing preselected, reason fields with their audience hint |
| Mark label | 6, 7 (precautionary only) | Word + one-line explanation |
| Refusal message | All forms | §5 |
| Refresh controls | 3 | §3 page 3 |

## 5. Refusal messages

**Where.** The same page is shown again. The sentence appears (a) in a box at the top under the
H1, headed **"Not done"**, and (b) next to the control it concerns, inside the row or verdict card
when it is about one. The `<title>` starts with "Not done: ". Any text the specialist typed in a
reason field is shown again so it is not lost; radio choices and the G3 checkbox are shown
**empty** again (nothing preselected).

**What.** The backend returns the code and the sentence (§4 of the SAD); this table is the wording
for that sentence. `{…}` are values the server fills in.

| Code | Context | Sentence |
|---|---|---|
| `DEMO_ROW_NOT_APPROVABLE` | Approve on the planted row | **"This is a planted demo row. It cannot be approved. Reject it with a reason."** (word for word from CR-029) |
| `QUOTE_CHECK_FAILED` | Approve on a row that failed the check | **"This row failed the quote check: its quote does not appear word for word in paragraph {para_id}. It cannot be approved. Reject it with a reason."** |
| `ALREADY_DECIDED` | Row | **"This row was already decided, so your decision was not recorded. The page now shows the decision that stands."** |
| `ALREADY_DECIDED` | Verdict | **"This verdict was already decided, so your decision was not recorded. The page now shows the decision that stands."** |
| `REASON_REQUIRED` | Reject a row | **"Write a reason to reject this row."** |
| `REASON_REQUIRED` | Approve over a flag | **"This row has a verifier flag. Write a reason to approve it over the flag."** |
| `REASON_REQUIRED` | G2 override to applies, or "unsure" decided as precautionary | **"Write a reason. GPs will read it as the explanation for this entry."** |
| `REASON_REQUIRED` | G2 override to does not apply, or "unsure" decided as does not apply | **"Write a reason. It is kept in the audit log; GPs will not see it."** |
| `BUSINESS_DAY_RULE_REQUIRED` | Approve without a business-day rule | **"Choose a business-day rule to approve this row: roll forward, no roll, or not confirmed."** (new code, see Open Questions) |
| `REASON_REQUIRED` | Abandon | **"Write a reason to abandon this run."** |
| `REASON_REQUIRED` | Decline | **"Write a reason to decline this calendar."** |
| `WHO_FILES_REQUIRED` | Approve, source silent | **"The source does not say who files this. Choose a filing party, or 'Not known', to approve the row."** |
| `GATE_INCOMPLETE` | Finish G1 | **"{x} rows are still undecided. Decide every row before finishing the rule review."** |
| `GATE_INCOMPLETE` | Finish G2 | **"{x} verdicts are still undecided, {u} of them 'unsure'. Decide every verdict before finishing."** |
| `ACK_REQUIRED` | Publish, box not ticked | **"Tick the box to confirm you have read the rejected rows and the uncited paragraphs. Then publish again."** |
| `ACK_REQUIRED` | Publish, lists changed | **"The lists of rejected rows or uncited paragraphs are not the ones shown when you ticked the box. Read the lists below and tick the box again."** |
| `VERSION_MISMATCH` | Any run-level action | **"This run has moved on since the page was opened. The page now shows where it is. Check it, then try again if you still need to."** |
| `RUN_ACTIVE` | Start run | **"Run {n} is still active, so a new run cannot start. Finish it, or abandon it at its gate, first."** + link **"Open run {n}"** |
| `RUN_NOT_ACTIVE` | Any decision on an ended run | **"This run has ended ({status words}), so it cannot take more decisions. Start a new run from the run list."** |
| `RUN_STAGE_RUNNING` | Abandon or decide during a stage | **"{Stage} is still running, so this cannot be done yet. It ends by itself; follow it on the run status page."** |
| `FORBIDDEN` | GP on a specialist action | **"This page is for the compliance specialist. You are signed in as a GP, so you can view the published calendar only."** |
| `VALIDATION` | Malformed form, or a "who files" value not offered | **"Part of this form was not valid ({field}), so nothing was saved. Check the form and try again."** |

## 6. Light visual pass (B6 input, `create` mode)

No design-system source is configured (`aamad.config.yml` has no `ui` block), so this is `create`
at the smallest useful size. One stylesheet, `backend/web/static/site.css`, as CSS custom
properties. B6 is the first block dropped if time runs out; every page must stay usable and
accessible unstyled.

- **Type**: system font stack; body 16 px / 1.5; H1 28 px, H2 21 px; quotes in a serif or with a
  left rule so evidence reads differently from interface text.
- **Spacing**: 4 / 8 / 16 / 24 / 40 px. Cards 16 px padding, 24 px apart. Max content width 72rem
  for specialist pages (desktop), 40rem for the GP calendar.
- **Colour roles** (each with text at 4.5:1 contrast or better, and always paired with a word):
  `--text`, `--muted`, `--surface`, `--border`, `--focus` (a thick visible outline),
  `--info` (running), `--action` (waiting for you), `--success` (published, passed),
  `--problem` (failed, quote check failed, refusal box), `--caution` (flag, unsure, precautionary,
  open question), `--demo` (demo label and the "Demo" tag; distinct from `--problem`).
- **Buttons**: one primary style (the next step on each page), one secondary (reject, decline,
  abandon). No icon-only buttons.
- **Focus**: visible on every control; never removed.

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
| UX-001 | Every page shows the demo label as text | operator brief |
| UX-002 | Every specialist page showing a stand-in run shows "Stand-in agents"; so does the GP calendar when that run's calendar is published | CR-030 |
| UX-003 | The planted row at G1 is tagged "Demo" and its "Approve row" button is visible and active; clicking it shows the CR-029 sentence at the top and in the card; the row stays undecided | DL-44, CR-029 |
| UX-004 | No radio, checkbox or select is preselected on any page, including after a refusal | SD AC-026 |
| UX-005 | No page has a bulk action, a disabled button or a "coming soon" | §3, AC-026 |
| UX-006 | Run status refreshes every 3 s only while a stage runs, and "Stop automatic refresh" stops it | §3 Freshness, WCAG 2.2.1 |
| UX-007 | Every status is readable with colour removed | §3 Accessibility |
| UX-008 | Before the first publication, `/calendar` shows only the DL-27 message | DL-27, CR-012 |
| UX-009 | A GP never sees a flag, an unsure verdict, a mark other than "Precautionary", or a run | CR-012 |
| UX-010 | G2 reason fields that create an entry say GPs will read the reason; "does not apply" fields say it is for the audit log only | SA-8, W-17 |
| UX-015 | Approving a row with no business-day rule chosen shows the `BUSINESS_DAY_RULE_REQUIRED` sentence in that row's card; the row stays undecided | §5 |
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
- `.cursor/templates/ux-template.md`, `.cursor/skills/product-design/SKILL.md`.
- The operator's B5 brief (this session).

Not read or used: Future Work, Appendix A, git tag `sad-full-design`, user-story files.

## Assumptions

- **File location.** The operator asked for `project-context/2.build/ux.md`. The framework's
  default is `project-context/1.define/ux.md`, and the validator only checks the approval status
  there, so it will not see this file's status. See Open questions.
- **No prototype.** The persona normally prototypes the hardest screen; the brief said no HTML, so
  none was made. G1 would be the screen to prototype.
- **The demo label** is a static line of text in the base template, asked for in the brief. It is
  not the parked F-18 banner (no Reset, no extra behaviour).
- **Hidden-but-enforced vs shown-and-refused.** The Approve button is always shown (rule of the
  page). Two controls are shown only in the phase where they belong, following the SAD's wording:
  the abandon form (gates only) and the decision forms (undecided items only). The server still
  enforces both.
- **"Stop automatic refresh"** is a query parameter on the run status URL. It stores nothing.
- **G2 "unsure"** can be decided as "Applies (precautionary)" or "Does not apply", both with a
  reason. The SAD names the precautionary choice; it does not say "does not apply" is ruled out.
- **Override** at G2 flips the verdict to its opposite; there is no third value.
- **"Rolled" mark** text assumes the server gives the original and the rolled date.
- **Business-day rule at approve** offers all three values, including "Not confirmed", which the
  SAD names as a valid outcome (W-13, `D-6`). A choice is always required (operator decision,
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
2. **File location.** Keep `ux.md` in `2.build/`, or move it to `1.define/ux.md` so the validator
   tracks its approval?
3. **Closed 2026-11-13 (operator).** No new page. The demo shows the audit log through what the
   SAD already provides: the append-only `audit_log` table (CR-013), read with the query that
   rebuilds the history of one calendar entry (CR-018), and the trace export (D4, block B8), which
   writes the `trace` and `audit_log` records for a run to `project-context/2.build/logs/<run_id>/`
   (§6 of the SAD). An audit page is listed under Post-MVP ideas. Note for `@qa.eng` and
   `@backend.eng`: the SAD defines the export for evaluation runs; whether it is also run for the
   demo run is theirs to confirm.
4. **G2 "unsure" → "Does not apply".** Allowed? Assumed yes (see Assumptions).
5. **New refusal code `BUSINESS_DAY_RULE_REQUIRED`.** Added at the operator's request
   (2026-11-13). It is not in the SAD §4 refusal-code table yet. Proposed row: "A business-day
   rule was not chosen on approve · 422". `@system.arch` to add it to §4 so `@backend.eng` builds
   from the SAD.
6. **Reject a row with a business-day rule chosen.** Separate forms avoid this, but confirm the
   service ignores or refuses stray fields on reject.
7. **Closed 2026-11-13 (operator).** The page uses "Local reporting agent (Spain)", exactly as
   the mock fund profile and the SAD (DL-39) have it. No display label is needed.

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
