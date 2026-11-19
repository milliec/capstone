# Frontend: build spec for the stubbed UI (B5 pages, with the light visual pass)

Owner: `@frontend.eng`. Branch `frontend-spec` (made from `main` at `12c674b`, because work never
starts on `main`). **Stage 1 (this spec): approved by the operator on 2026-11-17**, with the answers
recorded under Open Questions. **Stage 2 (templates and CSS): in progress**; see the Spec Sync
checklist (§9).

For: the operator (approval), `@frontend.eng` (stage 2), `@backend.eng` (the view fields in §10,
proposed handoff H-036), `@qa.eng` (the checks in §6 and §7).

**Goal.** The seven pages, the 403 and 404 pages and the shared frame, rendered by the real app on
top of the stand-in shell (`backend.md`), so the operator can click through the Friday demo
script (§7) with stand-in data and no model call.

**Two references, two jobs** (ux.md, top). `ux.md` (approved 2026-11-16) is the reference for
behaviour, states, wording and refusals. The mock-ups in `docs/prototype/` and `app.css` are the
reference for layout and look. Where they differ on behaviour or wording, `ux.md` wins.

**The one rule that shapes every template** (ux.md §1.2, SAD §4 "Page handlers", Never row):
**the page never decides.** A template shows what the service view gives it and posts forms. It
holds the fixed `ux.md` wording, keyed by values the server sends. It does not compare counts,
work out a state, check a rule, or hide a button to enforce one. Where a template needs something
the stub services do not send yet, this spec lists it in §10 for `@backend.eng`; the template does
not work it out instead.

---

## 1. Templates: what each one is, and which route and stub it uses

All templates live in `backend/web/templates/`. Stage 2 replaces every placeholder there. The
routes and service functions already exist (`backend.md`, SAD §4 "Service functions", H-035);
none is renamed.

### 1.1 Pages

| Template | ux.md | Route(s) it serves | Handler (`backend/web/routes/`) | Service functions it shows or posts to |
|---|---|---|---|---|
| `pages/sign_in.html` | page 1 | `GET /sign-in`, `POST /sign-in` | `sign_in.sign_in_page`, `sign_in_submit` | `auth.IDENTITIES`, `auth.sign_in` |
| `pages/filing_rules.html` | page 2 | `GET /specialist/runs`; form → `POST /specialist/runs` | `runs.filing_rules`, `runs.start_review` | `runs.list_runs`, `runs.get_active_run`, `runs.start_run` |
| `pages/review_status.html` | page 3 | `GET /specialist/runs/{run_id}`; form → `POST …/abandon` | `runs.review_status`, `runs.abandon` | `runs.get_run`, `runs.list_units`, `runs.abandon_run` |
| `pages/check_rules.html` | page 4 | `GET /specialist/runs/{run_id}/g1`; forms → `POST /specialist/rows/{row_id}/decision`, `POST …/g1/complete` | `gates.check_rules`, `decide_row`, `complete_g1` | `decisions.get_g1_view`, `decisions.decide_row`, `gates.complete_g1` |
| `pages/confirm_applies.html` | page 5 | `GET …/g2`; forms → `POST /specialist/verdicts/{verdict_id}/decision`, `POST …/g2/complete` | `gates.confirm_applies`, `decide_verdict`, `complete_g2` | `decisions.get_g2_view`, `decisions.decide_verdict`, `gates.complete_g2` |
| `pages/publish.html` | page 6 | `GET …/g3`; one form, two buttons → `POST /specialist/calendars/{calendar_id}/publish` or `…/decline` | `calendar.publish_page`, `publish`, `decline` | `calendar.get_g3_view`, `publishing.publish_calendar`, `publishing.decline_calendar` |
| `pages/calendar.html` | page 7 | `GET /calendar` | `calendar.calendar_page` | `calendar.get_published_calendar` |
| `pages/no_access.html` | §1.7 (403) | any specialist route, as the General Partner | `main.forbidden` | `auth.require_role` (the `FORBIDDEN` refusal) |
| `pages/not_found.html` | §1.7 (404) | an address or review that does not exist | `main.http_error` | — |
| `pages/server_error.html` (**new**) | §1.7 (500) | — | needs a 500 handler in `main.py` (§10, item W-4) | — |

**Retry is left out.** The current placeholder has a "Retry step (stub, B13b)" form. B5 builds the
**"Without Retry"** failed page (ux.md page 3, UX-022): no Retry form, button or text in the page
source, not hidden and not disabled. The `POST …/retry` route stays in the backend for B13b; no
template posts to it until then.

### 1.2 Shared parts (as built)

Stage 2 built the small shared parts as **macros** in one file, `parts/macros.html` (a macro is a
reusable piece of page, like a component), and kept the three decision forms as their own files.
Sections used by one page only (status banner, refresh controls, units tables, rule and answer
cards) live in that page.

| File · macro | ux.md | Used on | Contents |
|---|---|---|---|
| `base.html` | §1.3 | every page | `<title>` (`<Page name> · ACME Compliance calendar (demo)`, prefixed `Not done: ` after a refusal, except on the 403 page, ux.md §1.7); fonts and `site.css`; skip link to `#main`; the sidebar when signed in, else one white panel |
| `parts/sidebar.html` | §1.3 | every page but sign-in | wordmark and product name; fund block; `<nav aria-label="Main">` with `aria-current="page"`; the "Your turn" pill on Filing rules; identity and its demo line; "Sign out" |
| `macros.html` · `tag`, `run_tag`, `run_tone` | §1.5 | everywhere | the status pill: word inside, tone → style-note family (§4.2) |
| `macros.html` · `review_no`, `review_name` | §1.8 | pages 2 to 6 | "Review {n}" (`review_number`, H-036 V-1) |
| `macros.html` · `breadcrumb`, `run_labels`, `stepper`, `review_head` | §1.3, §1.4 | pages 3 to 6 | the head of a review page in the §1.3 order: breadcrumb → H1 with run labels → lead → refusal → stepper |
| `macros.html` · `refusal_top`, `refusal_here` | §5 | all forms | the "Not done" box or the short line with "Go to …" at the top; the full sentence beside the control or inside the card the server names (`refusal.anchor`) |
| `macros.html` · `stage_of`, `not_reached` | pages 4 to 6, "Closed review" | pages 4 to 6 | where a step page stands (before / at / after / ended before) and the one-line "not ready" message |
| `macros.html` · `mark_label` | page 6 "Mark labels" | page 6 | "Moved off a weekend", "May not be required", "Depends on open question OQ-7", each with its line |
| `parts/lookups.html` | §1.4, §1.5, pages 3 to 5 | via the macros and pages | ux.md's fixed wording only (step names, weekend and holiday words, AI answer words, unit words). The interim lookups were deleted with H-045 (§2) |
| `parts/decision_rule.html` | page 4 item 5.8 | page 4 | G1 answer-first form (§3) |
| `parts/decision_answer.html` | page 5 item 5.7 | page 5 | G2 answer-first form (§3) |
| `parts/decision_publish.html` | page 6 item 6 | page 6 | G3 answer-first form (§3) |

`parts/review_nav.html` and `parts/run_labels.html` (placeholders) are deleted. The breadcrumb,
stepper and run-labels macros replace them.

---

## 2. Each page: states, data read, forms posted

"Reads" names the field the template needs. ✅ = the stub view sends it (H-036 landed 2026-11-17: V-1 to V-12, V-12 with B2). ⏳ = still
not sent: the web-layer items of §10.2. ("Approval blocked" is sent since B7, 2026-11-19, H-055.) The template never works a ⏳ field out by itself.

**Interim lookups: deleted (H-045, 17 Nov 2026).** Until H-036 landed, `parts/lookups.html` held
ux.md's fixed tables keyed by `run.status` and `run.phase` (status tone, stepper states, the step a
review stopped at, page stage, filing parties, decided words, failure sentences), each marked
"interim: replaced by H-036 V-n", and the page used them only when the server's field was missing.
The server now sends every one, so the tables and their fallbacks are gone: the pages show the
server's values (V-1 to V-11) with no fallback. `parts/lookups.html` keeps only ux.md's fixed
wording for values the server sends (step names, weekend and holiday words, AI answer words, unit
words). The "Continue checking" link on Filing rules and "Abandoned at step k" now read the step the
server marks "Your turn" or `current` in `steps`. Counts, dates, reasons and evidence were never
looked up.

### Page 1 · Sign-in

| | |
|---|---|
| **States** | default; refused (`VALIDATION`: an identity that does not exist) |
| **Reads** | `identities[]` (`identity_id`, `label`) ✅; `refusal` ✅ (a plain sentence on this page; every other page gets the shared refusal object, V-12) |
| **Shows** | no sidebar; "acme"; H1 "Sign in to the demo"; the intro line (carries the demo label, UX-001); two forms, equal weight, each with its hint; "The fund and the firm are fictional." |
| **Left panel** | **Operator decision 2026-11-17 (option C, H-037):** the mock-up's ivory panel: wordmark, three decorative cards (`aria-hidden`, hidden below 1100 px, no per-date labels so the answer key is not shipped), the tagline "AI drafts. People approve." and two first-person paragraphs. **Portfolio voice on this page only**; every other page keeps the product voice (ux.md §1.6). The tagline is a paragraph, so "Sign in to the demo" stays the one H1. At 1100 px and narrower the sign-in box comes first, with a small wordmark, and this panel follows below it without its own wordmark (S-33) |
| **Posts** | `POST /sign-in` with `identity_id` (hidden), one form per identity. Buttons: "Sign in as the compliance specialist", "Sign in as the General Partner / Fund Manager" |

### Page 2 · Filing rules

| State (ux.md §10.1) | What shows |
|---|---|
| idle, no reviews | "No reviews yet. Start the first review below." in place of the table |
| idle, reviews | the table, newest first; no active-review notice |
| running, AI working | notice: label "AI is working", "**Review {n}:** {status words}.", link "Open review {n}" |
| running, your turn | notice: label "Waiting for you", same line, link "Continue checking" |
| refused `RUN_ACTIVE` | short top line "Not done. A new review can't start while review {n} is in progress." + "Go to 'Start a new review'"; the full sentence beside the button |
| refused `VALIDATION` | the full sentence at the top and beside the button |

| | |
|---|---|
| **Reads** | `runs[]`: `run_id` ✅, `status_words` ✅, `status` ✅, `demo_planted_row` ✅, `started_at` ✅ (ISO, formatted by a filter, §10 W-2), `review_number` ✅, `status_tone` ✅, `ended_because` ✅; `active_run` ✅ with `is_working` / `is_at_gate` ✅; `agents_mode` ✅ (decides whether the failure-demo checkbox is in the form: an option that does not exist in real mode, ux.md page 2, not a hidden button); `fund.fund_id`, `fund.name` ✅; `refusal` ✅ (the shared refusal object, V-12) |
| **Table** | Review · Started · Demo rule ("On"/"Off") · Status (pill + words) · Ended because. `<th scope="col">` |
| **Posts** | `POST /specialist/runs`: checkbox `demo_planted_row` (unticked), checkbox `demo_fail_step1` (unticked, stand-in only), button "Start a new review". The form is **always shown** (H-009) |

The placeholder's "By" and "Failure demo" columns are removed (ux.md page 2 table; Open Question 22
of ux.md: no failure-demo column).

### Page 3 · Review status

| State | H1 | Status pill (words, tone) | Shows | Refresh |
|---|---|---|---|---|
| `A_RUNNING` | "Nothing for you to do yet" | "AI is drafting the rules", info | step 1 sentence; units in two groups, "Drafting the rules" and "Checking the drafts" | on |
| `AT_G1` | "The rules are ready for you to check" | "Your turn: check the rules", action | sentence with {n} rules; link "Check the rules"; abandon form | off |
| `B_RUNNING` | "Nothing for you to do yet" | "AI is checking what applies", info | units "Checking what applies" | on |
| `AT_G2` | "Ready for you to confirm what applies" | "Your turn: confirm what applies", action | sentence with {n} and {u}; link "Confirm what applies"; abandon form | off |
| `C_RUNNING` | "Nothing for you to do yet" | "Working out the dates", info | one unit, "Code, no AI model" | on ("… while the dates are worked out.") |
| `AT_G3` | "The calendar is ready to check" | "Your turn: publish the calendar", action | sentence with {n} dates; link "Check the calendar and publish"; abandon form | off |
| `COMPLETED` | "Published" | "Published", success | published sentence; link "See the calendar as the General Partner sees it" | off |
| `DECLINED` | "Closed without publishing" | "Closed without publishing", neutral | closed sentence + "What needs to change: {reason}"; link "Go to Filing rules" | off |
| `ABANDONED` | "Abandoned" | "Abandoned", neutral | abandoned sentence + "Your reason: {reason}"; link "Go to Filing rules" | off |
| `FAILED` | "This review failed" | "Failed", problem | the **Without Retry** sentence: "This review failed at step {k} ({step name}), at unit {unit}. {reason sentence}. Nothing moved forward. Decisions you already made stay in the audit log."; primary link "Start a new review from Filing rules" | off |

Below the banner on every state: the units table(s), "Model cost so far: **US$0.00**." with
"(stand-in agents make no model calls)" for stand-in reviews, and the details line "Started {date},
{time}, by Compliance specialist (mock). Fund FND-DEMO-01."

**Abandon** (`AT_G*` only, ux.md page 3 item 10; the SAD says the form shows only at a gate). H2
"Abandon this review" with `id="abandon"`; the explanatory text; a `<textarea>` labelled "Reason
for abandoning" with its hint; button "Abandon review" in the secondary style. While AI or code
works, in its place: "You can abandon this review once it is waiting for you. While AI is working,
it always finishes by itself." On a closed review: nothing.

| | |
|---|---|
| **Reads** | `run` ✅ (`status`, `phase`, `status_words`, `is_working`, `is_at_gate`, `agents_mode`, `demo_planted_row`, `demo_fail_step1`, `cost_so_far`, `run_version`, `started_at`); `units[]` ✅ (`stage`, `label`, `status`, `failure_reason`, `stage_attempt`); `review_number` ✅, `status_tone` ✅, `steps[]` ✅, `counts` ✅ ({n}, {u}), `failure` ✅ (step k, step name, unit label, reason sentence), `ended` ✅ (date, time, reason), `published_at` ✅, `started_by_label` ✅, and per unit `group` ✅ (the stub makes no "Checking the drafts" units until B3); ⏳ `rendered_at`, `refresh_on` (web layer, §10.2) |
| **Posts** | `POST /specialist/runs/{run_id}/abandon`: `run_version` (hidden), `reason` (the route's field name) |

### Page 4 · Check the rules (G1)

| State | What shows |
|---|---|
| not yet (`A_RUNNING`) | the `not_reached` macro: "AI is still drafting the rules. They will be here when it finishes." + "Watch progress on the review status page" |
| at G1, rules to decide | full page: lead, four summary cards, rule index table, one card per rule, unused paragraphs, finish section, "Abandon this review" link |
| at G1, all decided | every card shows its decision; "To decide 0"; finish section H2 "All rules decided" |
| refused, about one rule | lands on `#row-{i}`; full sentence inside the card under "Not done"; short top line "Not done. The reason is shown beside rule {i}." + "Go to rule {i}"; the demo rule's tag becomes "Approval blocked" |
| refused, about the page | full sentence in a box at the top and beside "Finish checking" |
| after G1, or ended | read-only record; line "You've finished checking the rules. This is the record of the decisions."; no forms. On a review that ended before G1: "This review ended before this step." |

| | |
|---|---|
| **Reads** | `view.rows[]` ✅ `row_id`, `version`, `obligation_name`, `frequency`, `anchor`, `offset`, `recipient_code`, `responsible_role`, `business_day_rule`, `source_paragraph_id`, `quote`, `origin`, `decision` (a text read back from the audit log); per row ✅: `quote_check`, `paragraph` (text and document title), `flags[]`, `has_flag`, `open_question`, `needs_who_files`, `needs_attention[]`, `tags[]`, `recipient_name`, `status` + `status_tone` (to decide / approved / rejected; ⏳ "approval blocked", B7), `decided` (who, when, choices, reason), `filing_parties[]` (value, label); not built (dropped from H-036; the page works it out from `refusal.anchor`): `refused`; page ✅: `summary.flags`, `unused_paragraphs[]`, `stage` (before / at / after); not built (dropped from H-036): `index`, `total`, `next_undecided`, `show_forms` |
| **Posts** | per rule: `POST /specialist/rows/{row_id}/decision` with `version` (hidden), `decision` (`approve` / `reject`), `business_day_rule` (`roll_forward` / `roll_backward` / `no_roll`), `who_files` (only when the source is silent), `approve_reason` (only when the rule has a flag), `reject_reason`. Page: `POST …/g1/complete` with `run_version`; button "Finish checking", always shown at G1 |

### Page 5 · Confirm what applies (G2)

| State | What shows |
|---|---|
| not yet | "AI has not finished checking what applies. The answers will be here when it does." + link to review status |
| at G2 | lead, progress line, index ("can't tell" first), one card per answer, finish section, abandon link |
| all decided | progress "All {n} answers decided." |
| refused | as page 4: about one answer, land on `#verdict-{i}`; about the page, the box at the top |
| after G2 | read-only record: "You've confirmed what applies. This is the record of the decisions." |

| | |
|---|---|
| **Reads** | `view.verdicts[]` ✅ `verdict_id`, `version`, `row_id`, `obligation_name`, `verdict` (`applies` / `does_not_apply` / `unsure`), `reasoning`, `cited_fact_ids` (one string), `missing_information`, `decision`; per card ✅: `cited_facts[]` (ID, fact, value), `approved_rule` (rule, quote, paragraph ID), `missing_fact` (the phrase in "Nobody has confirmed {the missing fact}."), `overrule_value`, `decided` (outcome, who, when, reason); not built (dropped from H-036; the page works it out from `refusal.anchor`): `refused`; page ✅: `stage`; not built (dropped from H-036): `index`, `progress`, `index_order`, `next_undecided`, `show_forms` |
| **Posts** | per card: `POST /specialist/verdicts/{verdict_id}/decision` with `version`, `decision` (`confirm` / `override` / `decide`), `value` (carried by the button pressed, §3.3), `override_reason`, `decide_reason`. Page: `POST …/g2/complete` with `run_version`; button "Finish and calculate dates" |

### Page 6 · Check the calendar and publish (G3)

| State | What shows |
|---|---|
| not yet (`C_RUNNING` or earlier) | "The calendar is not ready yet." + "Watch progress on the review status page" |
| at G3 | lead; the boxed date-conventions note; calendar table; "What's not in this calendar" with its two tables; the decision form; abandon link |
| refused | the sentence at the top and beside the checkbox (`ACK_REQUIRED`) or the reason field (`REASON_REQUIRED`); the checkbox **unticked** again |
| after G3 | read-only calendar with "Published on {date} at {time}." or "Closed without publishing on {date} at {time}. What needs to change: {reason}"; no forms |

| | |
|---|---|
| **Reads** | `view.calendar_id` ✅, `view.entries[]` ✅ (`due_date`, `obligation_name`, `moved`, `precautionary`, `open_question_id`), `view.rejected_row_ids` ✅ (empty in the stub), `view.uncited_paragraph_ids` ✅ (empty); per entry ✅: `who_files_label`, `recipient_name`, `why` (the reason the General Partner reads), `source_paragraph_id`, `marks.moved` (from and to dates, direction); ✅ `rejected_rows[]` (rule, reason, demo; the lists are real since the G1 rejects), `unused_paragraphs[]` (ID, source, text), `previous_publication_at`, `outcome` (published or closed: date, time, reason), `stage` |
| **Posts** | one form: `decision` (`publish` / `decline`, radio), `run_version`, `rejected_row_ids[]`, `uncited_paragraph_ids[]` (hidden, exactly the lists shown), `acknowledged` (checkbox, unticked), `decline_reason`. Button "Publish calendar" (`formaction=…/publish`), button "Close without publishing" (`formaction=…/decline`) |

### Page 7 · Calendar

| State | What shows |
|---|---|
| nothing published | H1 "Compliance calendar" and the fixed message only: "Your compliance calendar is being prepared and checked by a specialist. Nothing has been published yet. The deadlines will appear here once it is published." |
| published | "Published on {date}." (+ "Made with stand-in agents (fixed test outputs, no AI model)." when it applies); the role's calendar note; three summary cards (counted on the page, see below); one calendar "All entries for {year}" with a Month (default), Year and List switch (display-only, see below; the Month view replaced the two-month grid) |
| error | "The calendar could not be shown just now. Try again in a few minutes." (§10, W-4) |

| | |
|---|---|
| **Reads** | `published` ✅ (`None` = nothing published; `published_at`, `agents_mode`, `entries[]` with `due_date`, `obligation_name`, `precautionary`); `identity.role` ✅ (picks the General Partner or specialist note); per entry ✅ `who_files_label`, `why`, `source_document`, `source_paragraph_id`, `quote`; not built (dropped from H-036; arranged display-only in the web layer, W-5): `summary`, `weeks`, `months[]` |
| **Posts** | nothing (only "Sign out") |
| **Never shows** | a "Moved off a weekend" mark, an open-question mark, a flag, a "can't tell", a review status (CR-012, UX-009) |

Phone width (≤ 480 px): each table row stacks as a block with visible column labels; no horizontal
page scroll (UX-012).

**Page 7 as built (operator, 2026-11-17: "behave like `docs/prototype/gp-calendar.html`"; B12,
DL-49, H-040).** Top to bottom:

1. **Summary cards** (ux.md item 5), as in the mock-up: *Due next* (dark card: date and what), *Entries
   in {year}: {n}* with the dot chart (one dot per entry per month, hollow for "May not be
   required"; the drawing is decorative, the numbers are text), *May not be required* with its count.
   Counted **display-only** from the entries already sent, so they count only what this viewer may
   see (CR-012). V-11 `summary` is no longer needed from the server.
2. **One calendar**, "All entries for {year}", with a **Month · Year · List** switch: a radio group
   styled as tabs. CSS (`:has()`) shows **only the chosen view, in place, no reload, no script**;
   Tab reaches the switch, arrow keys change the view. The server ticks the radio for `?view=`
   (**Month by default**, operator 2026-11-17, as in the mock-up; the SAD said List), so the Month view's "‹ March 2027" / "May 2027 ›" links (which reload,
   to `#entries`) keep it. Without `:has()` every view shows, one under another.
   - **Month:** one month as a real table (weekday column headers), "Due next" and "May not be
     required" in words. It replaces the two-month week grid of ux.md item 6.
   - **Year:** a real table, one row per obligation, a column per month; "May not be required" is a
     dashed tile plus words; due next underlined plus words.
   - **List:** the entries grouped by month, with row-group headers (ux.md item 7).
3. **Below 960 px:** the switch and the Month and Year views hide; the List view shows.

No moved or open-question mark anywhere (CR-012). Arranged by `backend/web/calendar_view.py` (W-5);
the view choice is W-6. **Drop order:** after B6 and Tier 2, before B13b; without it, the List view
alone. **Departures from approved documents, recorded for their owners:** the switch is a radio group, not "chosen by a link", and Month, not List, is the default (SAD §3 page 7; H-040); the Month view replaces the two-month grid and
the list is one view, not always shown (ux.md page 7 items 6 and 7; H-042); the summary cards are
counted on the page (ux.md item 5, V-11; H-036, H-042). New wording for the copy review: "No filings
this month.", "Entries in {year}: {n}", "None" (no date due next), the legend lines.

### 403, 404, 500

Shared frame, H1, one line, one link, nothing else (ux.md §1.7). Already worded in the
placeholders; stage 2 moves them into the new frame. The existing Tier 1 tests check
"You don't have access to this", "Go to the calendar" and "We can't find that page" and must keep
passing.

---

## 3. Answer-first decision forms

One pattern on pages 4, 5 and 6 (ux.md §4 "Decision form", SAD §3, DL-48).

### 3.1 Markup

```html
<form class="decision" method="post" action="…">
  <input type="hidden" name="version" value="…">
  <fieldset>
    <legend>What's your decision on this rule?</legend>
    <label class="opt"><input type="radio" name="decision" value="approve" data-answer="approve"> Approve</label>
    <label class="opt"><input type="radio" name="decision" value="reject" data-answer="reject"> Reject</label>
  </fieldset>
  <div class="if" data-answer="approve"> … the Approve fields … <button class="btn">Approve rule</button></div>
  <div class="if" data-answer="reject">  … the Reject fields …  <button class="ghost">Reject rule</button></div>
</form>
```

- The radio question comes first, named `decision`, **nothing checked**.
- Each answer's fields and button sit in their own `.if` block, marked with `data-answer`.
- `data-answer` on the radio, not its `value`, drives the reveal. Two G2 answers send the same
  `value` (`decide`), so the value cannot tell them apart (§3.3).

### 3.2 Reveal with `:has()`, and the fallback

```css
.if { display: grid; }                       /* fallback: every answer's fields show */
@supports selector(:has(*)) {
  .decision .if { display: none; }
  .decision:has(input[name="decision"][data-answer="approve"]:checked) .if[data-answer="approve"],
  .decision:has(input[name="decision"][data-answer="reject"]:checked)  .if[data-answer="reject"],
  /* … one line per answer: confirm, overrule, add, leave, publish, decline … */
  { display: grid; }
}
```

- `[name="decision"]` matters: the weekend-or-holiday and "who files" radios inside the Approve
  block must not trigger a reveal.
- **Fallback:** a browser without `:has()` skips the `@supports` block, so every answer's fields
  and buttons show and every control can be reached. The server reads only the chosen answer's
  fields (DL-48), so the fallback is safe.
- **No script.** No `required`, `disabled` or `pattern` on any decision form (ux.md §1.2). A
  missing field is the server's refusal, shown on the page.
- **Nothing preselected**: no `checked` on any radio or checkbox in any template, ever, including
  after a refusal (UX-004, UX-011). Typed reason text **is** shown again after a refusal (⏳ the
  server must send it back, §10).
- Labels: every radio inside a `<label>`; every group in a `<fieldset>` with a `<legend>`; every
  hint linked with `aria-describedby`; targets at least 24 × 24 px (WCAG 2.5.8).

### 3.3 The three forms

**G1, Check the rules** (`parts/decision_rule.html`)

| Answer | Fields (name) | Button |
|---|---|---|
| Approve | radio group `business_day_rule`, legend "If the deadline falls on a weekend or holiday (choose one to approve)": "Move to the following working day" `roll_forward` · "Move to the preceding working day" `roll_backward` · "Keep the date" `no_roll`. **Only when the source is silent:** radio group `who_files`, legend "Who files this? The source doesn't say.", options from `filing_parties` (⏳), with the hint. **Only when the rule has a flag:** textarea **`approve_reason`**, "Why are you approving it although the checker flagged it?", with the hint | "Approve rule" (primary) |
| Reject | textarea **`reject_reason`**, "Why are you rejecting it?", with the hint | "Reject rule" (secondary) |

The approve and reject reason fields have **different names**, so a reason typed under one answer
is never read as the other's (DL-48). The demo rule and a quote-check-failed rule get **exactly
the same form**: the Approve button is visible and active once "Approve" is chosen (UX-003).

**G2, Confirm what applies** (`parts/decision_answer.html`)

| AI said | Question | Answer A | Answer B |
|---|---|---|---|
| applies / doesn't apply | "What's your answer on this rule?" | **Confirm: applies** (or doesn't apply): text only, no reason field. Radio `decision=confirm`, `data-answer="confirm"`. Button "Confirm: applies" with `name="value" value="{AI's value}"` | **Overrule: doesn't apply** (or applies): textarea **`override_reason`**, "Reason for overruling", hint by outcome (ux.md page 5 table). Radio `decision=override`, `data-answer="overrule"`. Button "Overrule: …" with `name="value" value="{overrule_value}"` (⏳) |
| can't tell | "Nobody has confirmed {missing fact}. Should this rule go on the calendar?" | **Yes, add it until someone confirms**: radio `decision=decide`, `data-answer="add"`; button "Add to the calendar" with `name="value" value="applies"` | **No, leave it off**: radio `decision=decide`, `data-answer="leave"`; button "Leave it off" with `name="value" value="does_not_apply"` |

The SAD fixes the G2 reason names as `confirm_reason`, `override_reason` and `decide_reason`
(H-035). Both "can't tell" answers are `decide`, so they share **one** field, `decide_reason`.
**Decided (operator, 2026-11-17, Open Question 7):** **one textarea** below the two answers, with
two `<label>`s and two hints ("Why are you adding it?" plus the "creates an entry" hint; "How do
you know it doesn't apply?" plus the audit-only hint). `:has()` shows the label and hint for the
chosen answer; the fallback shows both. `confirm_reason` is never rendered: ux.md says Confirm
needs no reason.

**G3, Publish** (`parts/decision_publish.html`)

| Answer | Fields | Button |
|---|---|---|
| Yes, publish it (`decision=publish`) | the "will see these {n} dates straight away" text (with the "in place of the calendar published on {date}" variant, ⏳); checkbox `acknowledged`, **unticked**, "I've read the {r} rejected rules and the {k} unused paragraphs above. Nothing from them will be on the published calendar." | "Publish calendar" (primary), `formaction="/specialist/calendars/{id}/publish"` |
| No, don't publish (`decision=decline`) | the "Nothing changes for the General Partner" text; textarea **`decline_reason`**, "What needs to change before it can be published?", with the hint | "Close without publishing" (secondary), `formaction="/specialist/calendars/{id}/decline"` |

The two ID lists go in as hidden fields, exactly as the page shows them; the server compares them
with its own (CR-028).

---

## 4. Making the review status obvious

What the operator asked for, mapped to `ux.md`. Items marked **new** were approved by the operator
on 2026-11-17 and are not in `ux.md` yet; the operator asks `@ux.designer` to add them (Open
Question 4).

### 4.1 The status banner (review status page)

One section of `pages/review_status.html`, the first thing under the stepper (ux.md page 3 item 4,
the "status line"). Top to bottom:

1. **The pill**: the status words of ux.md §1.5, in a pill with its tone (§4.2). For example
   **"AI is drafting the rules"**, **"Your turn: check the rules"**, **"Failed"**. Never "Crew:
   running", "Stage A" or "G1" (UX-019).
2. **The sentence** for the state (§2, page 3 table), in large text.
3. **"Last updated at 14:02:09."** (**new**, approved), only while auto-refresh runs, next to the
   pill. Seconds are shown so the specialist can see each 3-second refresh. The time is the
   server's render time (`rendered_at`, W-1).
4. **The refresh controls** (only while AI or code works): "This page refreshes every 3 seconds
   while AI is working." · "Refresh now" · "Stop automatic refresh". With refresh off: "Automatic
   refresh is off." · "Refresh now" · "Turn automatic refresh back on".

The banner is `role="status"` **only when it is not refreshing**. A live region that re-renders
every 3 seconds would make a screen reader read it again and again. While running, the `<title>`
carries the status words instead, so a screen-reader user can check it.

**Position. Decided (operator, 2026-11-17, Open Question 5):** ux.md's order: breadcrumb → H1
with labels → stepper → banner. The banner is the most visible block on the page.

### 4.2 Pills: word first, colour second

Every status is a pill **with its word inside**: `<span class="chip {tone}">{words}</span>`.
Colour never carries the meaning alone (UX-007). The tone comes from the server (`status_tone` ✅,
from ux.md §1.5); the template maps tone to a class.

**Decided (operator, 2026-11-17, Open Question 1):** the existing style-note families, no new
colour. "Always show the word with the colour."

| Meaning | ux.md tone | Class | Where |
|---|---|---|---|
| idle, waiting, not started, ended without publishing | neutral | grey: `.chip` (plain) | "Abandoned", "Closed without publishing", stepper "Not started", unit "Waiting" |
| running (AI or code working) | info | **brass**: `.chip.agent` | "AI is drafting the rules", "Working out the dates", stepper "In progress", unit "Running" |
| needs the specialist | action | **orange**: `.chip.you` | "Your turn: …", the sidebar "Your turn" tag |
| done | success | **slate**: `.chip.done` | "Published", stepper "Done", unit "Done", "Approved" |
| failed or refused | problem | **bordeaux**: `.chip.no` | "Failed", unit "Failed", "Rejected", "Approval blocked" |

All five meet AA contrast already (style-note "Status families").

### 4.3 Auto-refresh

- `<meta http-equiv="refresh" content="3">` in `<head>`, **only** while the phase is `A_RUNNING`,
  `B_RUNNING` or `C_RUNNING` **and** refresh is not switched off. No script.
- "Stop automatic refresh" is a link to the same page with `?refresh=off`; "Refresh now" keeps
  whatever the URL says. Nothing is stored (ux.md Assumptions). The handler must pass `refresh_on`
  (⏳ W-1).
- Never on a refusal page, a gate, an ended or a failed review (ux.md §7, UX-006).
- **Units fill in one by one**: the stub already runs units one at a time with
  `STAND_IN_UNIT_PAUSE_S` (1 s per unit), so each refresh shows more rows moving "Waiting" →
  "Running" → "Done". The template only shows the `units` rows; it adds no animation that pretends
  progress.

### 4.4 The same words everywhere

| Where | Words used |
|---|---|
| review status banner | §1.5 status words |
| Filing rules table, Status column | the same §1.5 words, the same pill |
| Filing rules active-review notice | "**Review {n}:** {§1.5 words}." |
| sidebar tag | "Your turn" (orange, the same pill) |
| stepper | "Done", "In progress", "Your turn", "Not started", "Failed", "Ended" |
| page `<title>` on review status | "Review {n}: {§1.5 words} · ACME Compliance calendar (demo)", for example "Review 4: AI is drafting the rules" (**new**, approved) |
| buttons and next-step links | ux.md verb + object ("Check the rules", "Confirm what applies", "Check the calendar and publish") |
| refusal sentences | ux.md §5, using the same §1.5 words in `RUN_NOT_ACTIVE` ("This review has ended ({status words}) …") |

The status words are already held once, in `runs.STATUS_WORDS` (server). Templates never retype
them.

---

## 5. CSS plan

| | |
|---|---|
| **File** | `backend/web/static/site.css`: the one stylesheet (SAD §3). Served at `/static/site.css` (⏳ W-3: a static mount in `main.py`) |
| **Source** | `docs/prototype/app.css`. Copy the tokens unchanged; take only the rules the seven pages use; no new colour, radius or font |
| **Fonts** | Lexend (`--font-head`: headings, wordmark, fund name), Inter (`--font-body`: body, labels, buttons), DM Mono (`--font-id`: IDs such as `FND-DEMO-01`). Loaded from Google Fonts with `display=swap`, as the mock-ups do. No font file committed (style-note) |
| **Icons** | Iconoir, inline SVG, for the two nav items only ("Calendar", "Filing rules"), copied from `docs/prototype/icons/`. Add the Iconoir MIT notice to `NOTICES`. Every icon sits next to a word and is `aria-hidden="true"` |
| **Time box** | **Half a day at most** (U7 and U8, H-019, H-020). Anything that does not fit is dropped and recorded in the Spec Sync checklist |
| **Unstyled test** | Every page must read and work in order with the stylesheet removed: real headings, lists, tables and forms, the main column in reading order, no meaning carried by CSS alone. Checked by loading each page with `site.css` blocked (§6) |
| **Third-party comments** | The new file carries no comment naming a third-party site or brand (operator, 2026-11-17, Open Question 9) |

**Matching the mock-ups (operator, 2026-11-17).** The first pass rebuilt components from
`app.css`'s generic rules and missed the mock-ups' own component styles, so sizes were off. The
second pass uses them: the stepper is `.steps` (thin top line, 15 px step names), the status line
is `.cta` (ivory panel, 3 px tone bar, 26 px heading, button on the right), unit groups are cards
with a 22 px `.sq` heading and 15 px rows, cards use `.evidence` (source and AI's reading side by
side above 1180 px) and the sidebar foot has the `.avatar`. One deliberate difference: the
mock-up draws the in-progress step in orange; here it is brass, matching the operator's status
families (orange is "Your turn" only). **Breakpoint:** the sidebar stays beside the content down to
960 px (was 1100 px in the mock-up, which was a guess); below that it becomes a slim top bar with a Menu button (S-32, H-062).

**Sections taken from `app.css`**

| `app.css` section | Take | Leave out |
|---|---|---|
| 1 Tokens | all | — |
| 2 Base | all | — |
| 3 Shell | shell, sidebar, brand, fund, nav, side-foot, who, demo, main | the "waiting" panel (not in ux.md §1.3) |
| 4 Page parts | crumb, head, tags, section, sec-h, sq, facts | — |
| 5 Components | buttons, chips, kpi, card, card-h, tables, refusal, pillars (as the stepper), units | — |
| 6 Calendar | the list table and the GP card styles only | month and year grids (B12) |
| 7 Review | rule card, quote, paragraph, flag | the two-column source/draft layout's "source picking" (A5, out of scope) |
| 8 Sign-in | the `.enter` panel, `.role` buttons and, since H-037, the ivory `.stage` with its tagline and text | the `.float` cards (an older version of the cluster) |
| 9 Second pass | `.decision`, `.opt`, `.if` and its `@supports` block, `.refusal` / `.refline`, `pulse` | `.design-note`, prototype-only classes |
| 10 Charts, 11 Source picker, 12 View switch, 13 Add fund | the sign-in cluster only (`.cluster`, `.dcard`, dots, bars, ring; H-037) | the calendar charts (B12), the source picker (A5), the view switch and the Funds pages (future scope) |
| Responsive and reduced motion | the 1100 px stacking, the phone-width table stacking, `prefers-reduced-motion` | — |

**Motion kept from the mock-ups** (all switched off under `prefers-reduced-motion`):

| Keep | Where | Why |
|---|---|---|
| 200 ms colour fade on hover | links, buttons, nav rows | already in `app.css`; signals "clickable" |
| `pulse`: one orange outline ring, 1.4 s, 300 ms delay | the refused rule or answer card, on landing | draws the eye to where the refusal is, once |
| `slidein`: fade in from 10 px, 500 ms | the in-card refusal box | the refusal appears beside the form without a jump |
| `.more` underline draw, 400 ms | the next-step links ("Check the rules ›") | a quiet "go here next" |

Also kept since H-037, on the sign-in cluster only: `settle`, `dotIn`, `arc`, `grow`, each once on
load. Left out: `draw` (source highlight, not built). **No new motion** for running states: no spinner, no pulsing dot. The units table filling in
is the progress signal, and it is real.

---

## 6. Accessibility checks (WCAG 2.2 AA, ux.md §7)

Run on every page in stage 2, recorded in `project-context/2.build/ux-review.md`.

| Check | How | ux.md |
|---|---|---|
| Keyboard only | Tab through every page: skip link first, then sidebar, then main; every link, radio, checkbox, textarea and button reachable and operable; focus always visible (2 px orange outline); no trap; the G1 "Go to rule {i}" link moves focus to the card | §7 |
| Semantic headings | one `<h1>` per page; `<h2>` per section and per card; no skipped level. Checked with the browser's accessibility tree | §7 |
| Landmarks | `<aside>` sidebar with `<nav aria-label="Main">`, one `<main id="main">`, breadcrumb in `<nav aria-label="Breadcrumb">` | §1.3 |
| Status not by colour alone | view each page in greyscale; every status still reads as a word | UX-007 |
| Forms | every control labelled; groups in `<fieldset>` + `<legend>`; hints on `aria-describedby`; no `required`, `disabled`, `pattern` | §7, §1.2 |
| Nothing preselected | no `checked` in any template, on first load and after a refusal | UX-004, UX-011 |
| Refusal announced | `<title>` starts "Not done: "; the refusal is the first thing in `<main>` after the H1 | §7, §5 |
| Timing adjustable | auto-refresh only while running; "Stop automatic refresh" works | UX-006, WCAG 2.2.1 |
| Target size | buttons, radios and their labels at least 24 × 24 px | WCAG 2.5.8 |
| Tables | real `<table>` with `<th scope>` for reviews, units, rule index, unused paragraphs, calendar, rejected rules | §7 |
| Widths | specialist pages at 1280 px and 1024 px; the calendar at 360 px, 480 px and desktop, with no horizontal page scroll | §7, UX-012 |
| Contrast | only the style-note pairs; never `--orange` as text; never brass on ivory | style-note |
| Reduced motion | every animation off with `prefers-reduced-motion: reduce` | style-note |
| Unstyled | each page with `site.css` blocked still reads in order and works | §6 |
| Words | no "run", "Stage A/B/C", "G1/G2/G3", "gate" or "precautionary" in user-facing text (except "Stand-in agents") | UX-019 |

Tools: the rendered pages in a browser (keyboard and greyscale by hand) and Playwright for
screenshots at the agreed widths (§8). An automated scan is a help, never the acceptance on its
own.

---

## 7. Demo script for Friday (20 Nov 2026)

Start: `make run`, then delete `data/app.db` for a clean start. Browser at
`http://localhost:8000`. About 10 minutes.

The **Depends on** column says what must be built for the step to show what `ux.md` describes.
"Stub" means it works on today's stand-in shell once stage 2 is done.

| # | Do | You should see | Depends on |
|---|---|---|---|
| 1 | Open the app | Sign-in: "Sign in to the demo", two equal buttons, "The fund and the firm are fictional." | Stub |
| 2 | "Sign in as the compliance specialist" | Filing rules: "No reviews yet. Start the first review below."; the start form says "stand-in agents"; both checkboxes unticked | Stub |
| 3 | Tick "Add the demo rule (rule 7)", then "Start a new review" | Review status, step 1 "In progress", pill "AI is drafting the rules", "Last updated at …", labels "Stand-in agents" and "Demo rule on" | Stub (`review_number`, `rendered_at`: H-036) |
| 4 | Wait about 12 seconds | The page refreshes every 3 s; units go "Waiting" → "Running" → "Done" one by one; then "The rules are ready for you to check", pill "Your turn: check the rules", sidebar "Your turn" | Stub (the "Checking the drafts" group: H-036) |
| 5 | "Check the rules" | Summary cards, rule index, one card per rule, every card with its quote-check line; the demo rule tagged "Demo" | Stub shows the rules; quote check, paragraph, flags and counts need B2/B3 (H-036) |
| 6 | On the demo rule: choose "Approve", pick a weekend option, "Approve rule" | **Refused on the page**: lands on the demo rule; "Not done" box with the `DEMO_ROW_NOT_APPROVABLE` sentence; tag "Approval blocked"; top line "Not done. The reason is shown beside rule {i}." + "Go to rule {i}"; nothing preselected | ✅ B2 and B7 are built (2026-11-19). The server refuses the approval and the page shows it (S-30, S-31). Keep this step in the demo. |
| 7 | Choose "Reject", type "Quote doesn't support the rule", "Reject rule" | "Rejected by Compliance specialist (mock) at 14:05. Reason: …"; "Next rule to decide" | Stub (the decided line's who and when: H-036) |
| 8 | Decide the other rules (one Approve over a flag, one Reject), "Finish checking" | Review status, step 3 "In progress", "AI is checking what applies", units fill in, then "Ready for you to confirm what applies" | Stub |
| 9 | "Confirm what applies": confirm one answer, overrule one with a reason, and for the "can't tell" one choose "Yes, add it until someone confirms" with a reason | Each card shows its decided line; progress counts down; "Finish and calculate dates" | Stub (cited facts, progress, decided lines: H-036) |
| 10 | "Finish and calculate dates" | "Working out the dates", then "The calendar is ready to check" within a refresh | Stub |
| 11 | "Check the calendar and publish": read the table and the two lists, choose "Yes, publish it", tick the box, "Publish calendar" | Review status "Published", pill "Published", link "See the calendar as the General Partner sees it" | Stub (placeholder entries; real dates are B4). ⚠️ Both "what's not in this calendar" lists stay empty until B2 stores decisions, so the box reads "0 rejected rules" (§11) |
| 12 | "Sign out", then "Sign in as the General Partner / Fund Manager" | Calendar with "Published on …", "Made with stand-in agents …", the short General Partner note, the entries; "May not be required" on the one entry it applies to; no moved mark, no review status | Stub (entries are placeholders; summary cards and week grid need H-036) |
| 13 | Open `/specialist/runs` by hand | 403: "You don't have access to this", "Go to the calendar" | Stub |
| 14 | Sign out, sign in as the specialist, tick "Make step 1 fail (demo)", "Start a new review" | Unit 1 "Running" for about a second, then "This review failed", pill "Failed", stepper step 1 "Failed", the demo-failure reason sentence, only the link "Start a new review from Filing rules" (no Retry) | Stub (`failure` sentence fields: H-036) |
| 15 | "Start a new review from Filing rules", leave both boxes unticked, start; wait for "Your turn"; open review status; type a reason under "Abandon this review"; "Abandon review" | "Abandoned", "Abandoned at step 2 (You check the rules) on … Your reason: …"; Filing rules shows "Abandoned" and the reason under "Ended because"; "Start a new review" works again | Stub (`ended` fields: H-036) |

Optional, if B2 is in: click "Start a new review" while a review is in progress to show the
`RUN_ACTIVE` refusal beside the button (UX-017).

---

## 8. Deliverables

| # | Deliverable | Where |
|---|---|---|
| D-1 | The templates in §1 (pages and parts), replacing every placeholder; `parts/review_nav.html` deleted | `backend/web/templates/` |
| D-2 | `site.css` and the two nav icons | `backend/web/static/` |
| D-3 | The Iconoir MIT notice | `NOTICES` |
| D-4 | Page tests (SAD Tier 2 "per-state page tests"): nothing preselected (UX-004), no forbidden words (UX-019), no Retry form on a failed review (UX-022), auto-refresh only while running (UX-006), the empty calendar message (UX-008), "Stop automatic refresh" first while refreshing (K-1), each decision question names its rule for screen readers (K-2). 18 page tests (incl. the week grid: no Tab stops, hidden from screen readers, no moved marks; month grouping) and 7 layout tests (`tests/tier2/test_calendar_layout.py`). The Tier 1 tests keep passing | `tests/tier2/test_pages.py` |
| D-5 | The rendered review: screenshots at 1280, 1024 and 360 px, keyboard and greyscale checks, findings and fixes | `project-context/2.build/ux-review.md` |
| D-6 | Visual regression: Playwright Test 1.64.1, 24 snapshots, baseline v1 committed 17 Nov 2026 after the operator accepted H-006 for it (§11.1) | `tests/visual/` |
| D-7 | README notes, proposed through `*sync-docs` and written only after approval (below) | `README.md` |
| D-8 | This file, kept current: the Spec Sync checklist after every commit | `project-context/2.build/frontend.md` |

**README notes (D-7), proposed content.** The scaffold plan gives the full README rewrite to B10
(`@devops.eng` or `@qa.eng`). This change set proposes two short sections only:

1. **Run it locally**: `make install`, `cp .env.example .env` (set `SESSION_SECRET`), `make run`,
   open `http://localhost:8000`, the two demo identities, delete `data/app.db` to start again.
   `STAND_IN_UNIT_PAUSE_S` sets how slowly the units fill in.
2. **Where the CrewAI crews connect next**: the pages never call an agent. They render what the
   service functions return. The crews connect in **B3** behind `backend/runtime/agents.py`
   (`extract_rows`, `check_conflicts`, `judge_applicability`), which today return the stand-in
   answers in `backend/stand_in/` with a pause; `backend/runtime/stages.py`
   runs the units and `backend/services/stage_store.py` stores them. Switching
   `AGENTS_MODE=stand_in` to `real` changes no template. Real calls wait for the first green path
   and DL-40 (Build card).

---

## 9. Spec Sync checklist

Updated after every commit. Status: ⬜ not started · 🟡 in progress · ✅ done · ⏸️ blocked ·
➖ dropped (with the reason).

| # | Item | Status | Note |
|---|---|---|---|
| S-01 | `frontend.md` (this spec) | ✅ | Approved 2026-11-17; §1.2 updated to the parts as built |
| S-21 | W-1 to W-4 (refresh flag and render time, date filters, static mount, 500 page) | ✅ | `80b9d7e`, `e7bf018`. Display only |
| S-14 | `static/site.css` + nav icons + `NOTICES` | ✅ | `e7bf018`. Icons inline in the sidebar; Iconoir and font notices added |
| S-02 | `base.html` + `parts/sidebar.html` + skip link | ✅ | `093c07b` |
| S-03 | `parts/macros.html` + `parts/lookups.html` | ✅ | `093c07b`. Interim lookups and their fallbacks deleted with H-045 (`001d348`, `e44f4c7`); `lookups.html` keeps only ux.md's fixed wording |
| S-04 | Breadcrumb, run labels, stepper | ✅ | Built as macros (§1.2), not separate files |
| S-05 | `pages/sign_in.html` | ✅ | `53f08d8`; two-panel layout with the portfolio panel added 2026-11-17 (H-037) |
| S-12 | `pages/no_access.html`, `not_found.html`, `server_error.html` | ✅ | `53f08d8`. 403 title without "Not done: " (ux.md §1.7) |
| S-06 | `pages/filing_rules.html` | ✅ | `4b75b7b` |
| S-07 | `pages/review_status.html` + banner + refresh + units | ✅ | `1ed4fbf`. Count, date and reason clauses filled by H-036 V-5, V-6 (seen in the 17 Nov candidates) |
| S-08 | `pages/check_rules.html` + G1 form | ✅ | `3b665d7`. Quote check, paragraph, flags and unused paragraphs filled by H-036 V-8 (seen in the 17 Nov candidates) |
| S-09 | `pages/confirm_applies.html` + G2 form | ✅ | `16acd65`. Shared `decide_reason` box |
| S-10 | `pages/publish.html` + G3 form | ✅ | `c78163e`. Who files, Sent to, Why, the moved dates and both "not in this calendar" lists filled by H-036 V-10 and B2 (seen in the 17 Nov candidates) |
| S-11 | `pages/calendar.html` | ✅ | `36f02cc`, `58760c1`. List grouped by month; week grid display-only (droppable after B6 and Tier 2, before B13b). Who files, Why, source and quote filled by H-036 V-11; summary cards counted from the entries (V-11 `summary` dropped) |
| S-13 | Placeholder parts deleted; no Retry form anywhere | ✅ | `36f02cc`; UX-022 is tested |
| S-15 | `tests/tier2/test_pages.py` | ✅ | `aa9202b`, `7ef8a0f`. The stepper test no longer checks the deleted fallback (`e44f4c7`); 138 in the suite pass (17 Nov 2026) |
| S-16 | `ux-review.md` (rendered review, three widths, keyboard, greyscale, unstyled) | ✅ | Written 2026-11-17. Four findings fixed; keyboard, focus, scan and visual regression recorded as not tested |
| S-17 | Visual baselines | ✅ | Baseline v1 (24 snapshots) committed 17 Nov 2026 after the operator accepted H-006 for it. H-036 refresh of the 18 changed snapshots approved by the operator (17 Nov 2026), after the H-014 and H-015 fix (`c84d181`); all 26 pass (ux-review.md §3b) |
| S-18 | README notes via `*sync-docs` | ✅ | Operator approved items 1 to 3 on 2026-11-17; written |
| S-23 | Match the mock-ups' component styles; breakpoint 960 px | ✅ | `40be357` |
| S-24 | Screenshots as evidence | ✅ | 13 images in `project-context/2.build/evidence/` with a README (operator, 2026-11-17). Local copies stay in the git-ignored `docs/screenshots/` |
| S-25 | Week grid and month grouping (display-only) | ✅ | Built and tested (`c263fca`, `58760c1`, `8207349`); keyboard pass: no new Tab stops. Calendar baseline v2 approved (4 snapshots) |
| S-26 | B12 and page 7 like the mock-up (pulled forward, H-040) | ✅ | Summary row, one calendar with a Month / Year / List switch in place, Month by default. Keyboard and click checked; calendar baseline v3 approved (26 snapshots) |
| S-27 | Click-through feedback: land on the next card after a decision (W-7); no jump when switching calendar views | ✅ | `0eed7b4`, `e827a3e`. Measured in a real browser: next card 24px from the top, first Tab inside it; tabs stay at 80px through every switch |
| S-19 | H-036 view fields from `@backend.eng` | ✅ | V-1 to V-11 landed in PRs #68 to #73, V-12 with B2 (#75) |
| S-28 | H-045: delete the interim lookups and their fallbacks | ✅ | `001d348` (fallbacks, merged in #78 before it was finished) and `e44f4c7` (the 14 interim tables, an unused import, the stepper test). Every page renders at AT_G1, AT_G2, AT_G3, published, abandoned, declined and failed, plus sign-in, 403 and 404; 138 tests pass |
| S-29 | H-048: abandon box shows the typed reason | ✅ | `review_status.html` reads `typed.reason` (V-12 dict), only when the refusal's anchor is `abandon`, like the other forms. Checked by rendering: a blank reason comes back as typed (422); a stale page leaves the box empty; a rule 2 refusal does not fill it |
| S-22 | H-027 (weekend-option refusal from ux.md, no `required`) | ✅ | Rendered 2026-11-19 with B2: approve with no weekend choice gives 422, the top line and the sentence in the card; no `required`. Typed text kept, answer shown unchosen (ux.md) |
| S-30 | H-048 part 2: look at each page with each refusal | ✅ | Rendered 22 cases in Chromium (page 3, 4, 5, 6, ended review). **One gap fixed:** `ALREADY_DECIDED` (G1, G2) left the card without its sentence (the card is decided, so no form); now shown in the decided block (2 Tier 2 tests). Not reachable from the UI, so not looked at: `QUOTE_CHECK_FAILED`, `RUN_STAGE_RUNNING`, `RUN_NOT_FAILED`, `RETRY_*` |
| S-31 | H-055 (1): print the server's status | ✅ | `check_rules.html` no longer checks for `DEMO_ROW_NOT_APPROVABLE`; it prints `status` and `status_tone`. Checked: "Approval blocked" shows after the refusal and after a reload |
| S-32 | H-062 (operator): phone menu below 960 px | ✅ | `parts/sidebar.html` + new `parts/side_body.html`, `site.css` (959 px block). Slim bar (56 px): wordmark, "Your turn" text tag, native `<details>` Menu that opens over the content. Checked in Chromium at 360, 768 and 1024 px: sidebar unchanged at 1024; keyboard Tab and Enter work; the GP calendar has no sideways scroll at 360. **Not caused by the menu:** a table on the specialist rule page is 528 px wide at 360 px (specialist pages are specified from 1024 px). Changes 2 pictures at 360 px: `07-calendar-gp-published` and `07-calendar-gp-empty`; neither re-recorded |
| S-33 | Sign-in page, stacked layout (1100 px and narrower), operator 2026-11-19 | ✅ | Built to ux.md page 1's own intent ("the sign-in box comes first on small screens"), which the build had missed: only the cards were hidden. Now `.enter` is ordered first with a small `acme` wordmark (`.brand-narrow`, decorative); the story panel follows with no second wordmark and a 28 px tagline. Checked at 360, 768, 1280 px: both buttons end at 470 px on a 740 px screen; 1280 px unchanged; Tab goes skip link, specialist, General Partner. Reading order: the story is still first in the HTML; the skip link goes to the sign-in box. Changes `01-sign-in-360`; not re-recorded |
| S-34 | Specialist pages at 360 px: no sideways scroll (operator 2026-11-19) | ✅ | Measured before: reviews list 545 px, rule check 528, confirm 366, publish 911 (page width 360). The 8 tables now use the existing `stack-sm` pattern (`data-label` on data cells; `site.css` ≤ 480 px block extended for row headers `th[scope=row]`, and empty cells hide their label). After: every specialist page is 360 px wide. All visual snapshots pass unchanged (no re-recording). The publish page is long at 360 px (22 entries, about 10,000 px); a shorter phone layout is not designed. ux.md only requires 360 px for the GP calendar (UX-012), so this is beyond spec. Tier 2 test added |
| S-20 | **Spec-to-code pass before merge** | ✅ | 17 Nov 2026: files, macros, form fields and answer markers, CSS classes and markers match. Fixed: §10.1 rewritten as the exact field contract; stale sentences (sign-in panel, charts, tests, visual baseline, calendar grid); two dead CSS rules removed. Open: Question 10 (fields no template reads; the week grid). Run again if anything changes before the merge |

---

## 10. What the templates need from the services (H-036: sent, V-1 to V-12)

These are the ⏳ fields of §2. The templates must not work them out (ux.md §1.2, backend.md "Known
gaps": "B5 moves any such choice into the service view"). Raised as handoff **H-036** to
`@backend.eng` on 2026-11-17. **Done 2026-11-17, V-12 with B2** (`backend.md` "View fields for the
pages" and "B2"); the interim lookups (§2) were deleted with H-045 (17 Nov 2026).

### 10.1 View fields (services, `@backend.eng`): the exact contract

**Exact names and shapes, as the templates read them today** (spec-to-code pass, 17 Nov 2026). The
templates print these as sent. Since H-045 (17 Nov 2026) the fields that choose a word, tone, step or
form (V-1, V-2, V-3, V-6 `failure`, V-8 to V-10 `stage`, `status`, `filing_parties`,
`needs_who_files`, `overrule_value`, `decided`) have no fallback. Optional evidence and clauses still
show less when a value is empty, never a made-up value (§11). Names are what matter; values may be
placeholders in stand-in mode.

| # | Where the template reads it | Field and shape | Page |
|---|---|---|---|
| V-1 | every run (`runs._describe`) | `review_number` (int) | all review pages, Filing rules |
| V-2 | every run; every G1 row | run `status_tone`; row `status_tone`: one of `info`, `action`, `problem`, `neutral`, `success` (ux.md §1.5) | pills |
| V-3 | every run (review pages) | `steps` = four items of `{state, href, current}`: `state` one of "Done", "In progress", "Your turn", "Not started", "Failed", "Ended"; `href` the step's page or none; `current` true on the step the review is at (operator, 17 Nov 2026) | stepper, pages 3 to 6 |
| V-4 | each unit (`runs.list_units`) | `group`: one of `drafting` (step 1, one per source document), `checking_drafts` (step 1, one per drafted rule), `applies` (step 3), `dates` (step 4). **The backend assigns it; the page never works it out.** The page maps each code to ux.md page 3's heading and intro, in that order; a unit with any other code shows under "Other units" (operator, 17 Nov 2026) | page 3 |
| V-5 | `run` (review status) | `counts.rules`, `counts.unsure`, `counts.dates` (ints) | page 3 sentences |
| V-6 | `run` | `ended.at` (ISO time), `ended.reason` (text, first line shown); `published_at` (ISO time); on Filing rules rows `ended_because` (text: the failure sentence or the first line of the reason) | pages 2, 3 |
| V-6 | `run` (failed review) | `failure` = `{step (int), step_name, unit_label, reason_sentence}`; the reason sentence is ux.md page 3's wording for the failure reason, without the final full stop (operator, 17 Nov 2026) | page 3 |
| V-7 | `run` | `started_by_label` ("Compliance specialist (mock)") | page 3 |
| V-8 | `view` (G1) | `stage` (`before`, `at`, `after`, `ended_before`); `summary.flags` (int); `unused_paragraphs[]` of `{paragraph_id, document, text}` | page 4 |
| V-8 | each `view.rows[]` | `status` (word: "To decide", "Approved", "Rejected", "Approval blocked") + `status_tone`; `quote_check.passed` (bool); `paragraph.document`, `paragraph.text`; `flags[]` of `{flag_type: internal or cross_source, row_value, quote_says, other_paragraph_id}` (an empty list prints "No checker flags."); `has_flag` (bool); `needs_who_files` (bool); `filing_parties[]` of `[value, label]` pairs, in the fund's order, "not known" last; `open_question` (bool); `needs_attention[]` (words for the index column); `tags[]` (extra card tags); `recipient_name`; `decided` = `{by_label, at, business_day_rule, who_files, reason}` | page 4 |
| V-9 | `view` (G2) | `stage` | page 5 |
| V-9 | each `view.verdicts[]` | `cited_facts[]` of `{fact_id, label, value}`; `approved_rule` = `{text, quote, paragraph_id}`; `missing_fact` (phrase that fits "Nobody has confirmed {…}."); `overrule_value` (`applies` or `does_not_apply`); `decided` = `{outcome (ux.md page 5 words), by_label, at, reason}` | page 5 |
| V-10 | `view` (G3) | `stage`; `rejected_rows[]` of `{label, reason, is_demo}`; `unused_paragraphs[]` of `{paragraph_id, document, text}`; `previous_publication_at`; `outcome` = `{at, reason}` | page 6 |
| V-10 | each `view.entries[]` | `who_files_label`; `recipient_name`; `why`; `source_paragraph_id`; `marks.moved` = `{from_date, to_date, direction}` (direction in words, for example "following working day") | page 6 |
| V-11 | each `published.entries[]` | `who_files_label`; `why`; `source_document`; `source_paragraph_id`; `quote` | page 7 |
| V-12 | `refusal` (any page) | `code`; `sentence`; `anchor` (`row-3`, `verdict-2`, `start`, `ack`, `decline-reason`, `decision`, `abandon`; none for a page-level refusal); `target_label` ("rule 3"); `short` and `link_text` (optional, for `RUN_ACTIVE`); `typed` = `{field name: text typed}` | all forms |

**Dropped from H-036** (operator, 17 Nov 2026, Open Question 10, option A). The page works these
out from the lists the server sends, or they are not built:

- `index`, `total`, `next_undecided` (V-8, V-9): rule numbers and "next rule to decide" come from the
  order of the lists; `show_forms`: `stage` already decides which forms show.
- `progress`, `index_order` (V-9): the step 3 counts and the "can't tell first" order are counted and
  sorted from `view.verdicts`.
- `weeks`, `months`, `summary` (V-11): not needed. The calendar's month grouping, views and summary
  cards are arranged **display-only** in the web layer from the entries already sent (operator,
  2026-11-17; §2 page 7, W-5).

**Decided 2026-11-17 (operator): unit groups.** V-4 is a `group` on each unit (contract table above),
not a separate `unit_groups` list. Until units carry it, page 3 shows today's view, grouped by stage
(`6a2fb2b`).

### 10.2 Web-layer items (`backend/web/`, `backend/main.py`)

These are display plumbing, not checks. `@frontend.eng` writes them, with no logic (operator,
2026-11-17, Open Question 2).

| # | Item | File |
|---|---|---|
| W-1 | Pass `refresh_on` (from `?refresh=off`) and `rendered_at` to the review status page | `backend/web/routes/runs.py` |
| W-2 | Jinja filters for dates and times in ux.md's format ("Fri 13 Nov 2026", "14:02") | `backend/web/deps.py` |
| W-3 | Mount `backend/web/static/` at `/static` | `backend/main.py` |
| W-4 | A 500 handler that renders `pages/server_error.html` with the role's sentence | `backend/main.py` |
| W-5 | Page 7's month grouping and two-month week grid, display-only: arranges the entries the server sends, adds and marks nothing (operator, 2026-11-17) | `backend/web/calendar_view.py`, filter `calendar_layout` in `backend/web/deps.py` |
| W-6 | Page 7's view choice, display only: `?view=list|month|year` (anything else is List) and `?month=YYYY-MM`, passed as `cal_view` and `cal_month` (B12, operator 2026-11-17) | `backend/web/routes/calendar.py` |
| W-7 | Where steps 2 and 3 land after a decision: the redirect adds `?after=<decided id>#next`; the page passes `after` on, and puts a zero-height `#next` marker at the top of the next card still to decide (wrapping round), or before Finish when all are decided (operator, 2026-11-17) | `backend/web/routes/gates.py`, `pages/check_rules.html`, `pages/confirm_applies.html` |

---

## 11. Stage 2 notes: what the pages show now that H-036 and B2 have landed

The templates read the H-036 field names, so each item below filled in by itself when the field
arrived. None of them shows a made-up value. Since H-036 landed (2026-11-17), the "Shows once"
column is what the services send for every row; the "Shows now"
column is kept as the record of the interim behaviour.

| Where | Shows now | Shows once | Why |
|---|---|---|---|
| Every review | "Review RUN-20261117-1" | "Review 4" | `review_number`, H-036 V-1 |
| Page 3, `AT_G1` sentence | "AI drafted the rules and checked each one against the sources. …" | "AI drafted **7 rules** and …" | counts, V-5 |
| Page 3, `AT_G2` sentence | "AI checked the approved rules against the fund's facts." | "AI checked **6 rules** … **1 of them** need your decision …" | counts, V-5 |
| Page 3, `AT_G3` sentence | "The calendar is ready." | "The calendar is ready: **22 dates**." | counts, V-5 |
| Page 3, published / closed / abandoned | the sentence without "on {date} at {time}" and without the reason | the full ux.md sentence | `published_at`, `ended`, V-6 |
| Page 3, units | step 1 shows "Drafting the rules" only | also "Checking the drafts" | `unit_groups`, V-4 |
| Page 2, "Ended because" | empty | the failure sentence or the first line of the reason | `ended_because`, V-6 |
| Page 4 | no quote-check line, paragraph, flags, OQ-7 mark, "Checker flags" card or unused-paragraphs list; decided line is "**Approved**." only | all of them, and "Approved by … at 14:02. …" | V-8 |
| Page 5 | cited facts as IDs only; no "Show the approved rule"; the can't-tell question without "Nobody has confirmed {fact}." | the facts table, the rule, the full question | V-9 |
| Page 6 | "Who files", "Sent to", "Why" empty; moved mark without its dates; **both "what's not in this calendar" lists empty**, even after a rejection | filled | V-10; the lists need B2 to store decisions |
| Page 7 | no summary cards, no two-month grid, heading "All entries" without the year; "Who files" and "Why" empty | **Built (B12, H-040, H-041):** summary cards with the dot chart, and one calendar with Month (default), Year and List views, all arranged on the page from the entries sent (display-only, W-5, W-6); "Who files" and "Why" filled (V-10). V-11 `summary`, `weeks` and `months[]` are not needed and not built | page 7 as built, above |
| Refusals | every ux.md §5 refusal on the page, with its 409 or 422 status | every ux.md §5 refusal on the page | V-12 and B2 |

**Later (not this sprint).** Collapsible nav below the breakpoint: done 2026-11-19 (S-32, H-062):
below 960 px the sidebar is a top bar with a native `<details>` Menu; keyboard checked. Still open:
closing the panel on an outside click or Escape (needs a script; asked in H-062).

**Wording to confirm with `@ux.designer`** (not in ux.md): the empty "Paragraphs no rule uses" list
on page 6 shows "None."; the fallback lines above that drop a count or date; the rule-card column
headings "The source says" and "The AI's reading" (taken from the mock-ups; ux.md names no headings
there); the "AI is working" / "Your turn" pill above the status heading (ux.md §10.1 words); the sign-in panel's portfolio-voice lines (H-037).

**For `@backend.eng` (add to H-036 V-12).** The refusal object the templates read: `code`,
`sentence`, `anchor` (`row-3`, `verdict-2`, `start`, `ack`, `decline-reason`, `decision`, `abandon`;
none for a page-level refusal), `target_label` ("rule 3"), optional `short` and `link_text` (for
`RUN_ACTIVE`: "Not done. A new review can't start while review {n} is in progress." and "Go to
'Start a new review'"), and `typed` (the reason text to show again, by field name). **G2 fallback:**
without `:has()`, both answers' buttons show, so a request can carry `decision=confirm` with the
overrule button's `value`. The service should refuse a `value` that does not match the answer
(`VALIDATION`), as the G3 route does for `decision`.

### 11.1 Visual regression (how to run)

- **Where:** `tests/visual/` (its own `package.json`; Node is used only here; the app stays Python).
- **Install once:** `cd tests/visual && npm install --ignore-scripts && npx playwright install chromium`
  (Playwright Test 1.64.1, pinned; Chromium goes to the user cache, not the repo).
- **Run:** `cd tests/visual && npm run test:visual`. Playwright starts the app itself on port 8777 with
  a fresh database, stand-in agents and no pause. Report: `npm run test:visual:report`.
- **What it checks:** 24 snapshots (sign-in, Filing rules, review status, the three step pages, the
  calendar, 403, 404) at ux.md's widths. Run IDs, today's date and clock times are replaced with
  fixed placeholders before each picture; animations are frozen. Threshold: `maxDiffPixels` 150.
- **Updating a baseline** follows the skill: propose, wait for the operator, then write.

## Sources

- `project-context/2.build/ux.md` (approved 2026-11-16): workflow, §1 to §11, Assumptions, Open
  Questions, "Mock-up differences".
- `docs/prototype/` (`app.css`, `HANDOVER.md`, `run-status.html` and the other mock-ups) for layout
  and look; `project-context/2.build/style-note.md` for tokens, status families, motion and
  contrast.
- `project-context/1.define/sad.md`: Build card (incl. "Build approach", Never row), Order of work,
  §3 Frontend (rendering, styling, scripts, freshness, the seven pages, shared parts, decision
  form, refusals), §4 routes, validation, refusal codes and "Service functions" (H-035).
- `project-context/2.build/backend.md`: stub function list, Known gaps.
- `project-context/2.build/scaffold-plan.md` §1 to §3 (folder tree, block order, stand-in setup).
- `project-context/2.build/setup.md`; `.cursor/agents/frontend-eng.md`;
  `.cursor/skills/product-design/SKILL.md`.
- The code on `main` at `12c674b`: `backend/web/` (routes, deps, placeholder templates),
  `backend/services/`, `backend/runtime/stages.py`, `backend/stand_in/shell_data.py`,
  `config/fund/FND-DEMO-01.yaml`, `tests/tier1/`.
- The operator's stage-1 brief (2026-11-16).

Not read or used: Future Work, Appendix A, tag `sad-full-design`, `reference/`.

## Assumptions

- **Styling now.** The operator's brief asks for the CSS in stage 2. In the SAD that is B6, the
  last block and the first dropped. This spec pulls a half-day pass forward at the operator's
  request; every page still works unstyled, so dropping it later costs nothing.
- **Wording lives in templates, state lives on the server.** A template may look up ux.md's fixed
  words by a value the server sends (a status, a tone, a step state). It may count a list the
  server sends (`|length`). It may not compare values, work out a state or decide which form to
  show; those come as view fields (§10).
- **The failure-demo checkbox** is in the form only when `agents_mode == "stand_in"`. ux.md page 2
  says this is the one option that depends on the server setting, not a hidden button.
- **Retry** is left out of every template (B13b; ux.md "Without Retry").
- **The stub's demo rule is rule 4**, not rule 7, because the shell has three placeholder rules.
  The checkbox still reads "Add the demo rule (rule 7)", as ux.md says; B3 and B7 bring the real
  six rules plus the demo rule.
- **Times** are shown in the server's local time.
- **Branch.** `frontend-spec`, made from `main`; stage 2 continues on it unless the operator says
  otherwise.

## Open Questions

All nine closed by the operator on 2026-11-17, when approving this spec.

1. **Closed: pill colours.** The brief asked for grey, blue, green and red; the approved palette has
   no blue or green. Decision: the existing families (grey idle, brass running, orange "Your turn",
   slate done, bordeaux failed), always with the word in the pill (§4.2).
2. **Closed: web-layer edits.** `@frontend.eng` makes W-1 to W-4, display only, no logic. Business
   logic stays with `@backend.eng` (§10.2).
3. **Closed: H-036.** Raised now, so the backend work runs alongside stage 2 (§10.1).
4. **Closed: new wording.** "Last updated at 14:02:09." and the tab title "Review 4: AI is drafting
   the rules" are approved. The operator asks `@ux.designer` to add both to `ux.md`.
5. **Closed: banner position.** ux.md's order: the status line under the H1 and the stepper.
6. **Closed: the demo-rule refusal on Friday.** Step 6 stays in the script, marked "needs B2 + B7".
   If they are not built by Friday, the step is skipped in the demo (§7).
7. **Closed: the "can't tell" reason field.** One textarea, `decide_reason`, with the label and hint
   changing per answer (§3.3).
8. **Closed: commits.** Stage 2 commits go on `frontend-spec`. No push, no merge.
9. **Closed: "ventriloc.ca".** Not in the repository; ignore it. No third-party comments in the new
   stylesheet.
10. **Closed 2026-11-17 (operator): split.** Option B for step states and failure details: added to
    H-036 (`steps`, `failure`, §10.1) and the templates read them when sent (`688a983`). Option A for
    counts, ordering on step 3, and the calendar week grid and month grouping: dropped from H-036; the
    grid stays not built. `unit_groups` (V-4) was decided separately the same day: a `group` per unit (§10.1).
11. **Rejected snapshot refresh, 2026-11-17.** `03-review-status-published-1280` after `5a1ad3e`
    (cards' top margin removed): rejected by the operator, "cards are still not top aligned". At
    1280 px the third card wrapped onto a second row. Decided: **always one row**: every unit card
    shares one row, tops aligned, stacked below 760 px. A new refresh is proposed for that layout.
- **Mobile calendar (360 px, operator 2026-11-19):** the General Partner's calendar at 360 px needs a layout fix (it is now one 9,276 px column of 22 entries). Not yet specified what is wrong; `@frontend.eng` to look with the operator. Until then `07-calendar-gp-published-360` keeps its old baseline and the visual check fails on that one picture.
- **Mobile calendar (360 px) — 2026-11-19, in progress:** built as H-062 (phone menu). Both 360 px calendar pictures (`07-calendar-gp-published-360`, `07-calendar-gp-empty-360`) now differ and wait for the operator's approval; the operator asked to propose the published one only, so the empty one needs a decision.

## Audit

- 2026-11-16 · persona `frontend-eng` · stage 1 of the operator's brief · `project.mode`
  greenfield · `ux.md` approval checked: `approved` (2026-11-16). Read the sources above. Wrote this
  file only, on branch `frontend-spec`. No template, stylesheet, test or backend file changed. No
  diagram needed (§1 and §2 tables carry the structure). No model call; `AGENTS_MODE=stand_in`
  untouched. `ux.md` and `sad.md` not edited. `*sync-docs` not run (no application source, runtime
  config or deploy change in this change set).
- 2026-11-17 · persona `frontend-eng` · stage 1 approved by the operator; Open Questions 1 to 9
  closed with the answers above. Added the interim lookups (§2) so the demo can be clicked through
  before H-036 lands. Raised H-036 to `@backend.eng` in `handoffs.md`; noted H-027 (owned by
  `@frontend.eng`) in the Spec Sync checklist. Stage 2 starts on `frontend-spec`.
- 2026-11-17 · persona `frontend-eng` · stage 2 · templates, `site.css`, web-layer display edits
  (W-1 to W-4) and Tier 2 page tests on `frontend-spec`; rendered review in `ux-review.md`. After
  the operator's review, matched the mock-ups' component styles and lowered the breakpoint to
  960 px (`40be357`). No model call; `AGENTS_MODE=stand_in` untouched; `ux.md` and `sad.md` not
  edited.
- 2026-11-17 · persona `frontend-eng` · `sync-docs` · operator approved items 1 to 3; applied to
  `README.md` ("Status" note and "Run the app shell": the pages are no longer placeholders; one
  paragraph on where the CrewAI crews connect, B3, `backend/runtime/agents.py`). `backend.md` still
  says "placeholder templates": left for `@backend.eng` (its owner). No spec drift found.
- 2026-11-17 · persona `frontend-eng` · sign-in: operator chose option C (the mock-up's left-hand
  panel, portfolio voice on this page only). Built from `docs/prototype/sign-in.html` after a
  real-name scan; per-date labels removed from the dot chart. Raised H-037 to `@ux.designer` so
  ux.md records it. Rendered at 1280 px and 800 px.
- 2026-11-17 · persona `frontend-eng` · spec-to-code pass (S-20): checked named files, macros, form
  field names, answer markers against the CSS reveal rules, CSS classes both ways, view fields both
  ways, and leftover markers. §10.1 now lists the exact names and shapes the templates read; fields
  no template reads moved to a pending list (Open Question 10). Removed the unused `.demo` and
  `.month-h` rules; unit tests (56) and the visual check (24) still pass.
- 2026-11-17 · persona `frontend-eng` · Open Question 10 closed (operator split): `steps` and
  `failure` added to the §10.1 contract and read by the templates when sent; counts, ordering and the
  week grid / month grouping dropped from H-036. Tests 58, visual 24 of 24.
- 2026-11-17 · persona `frontend-eng` · page 7 week grid and month grouping, display-only (operator):
  web-layer helper (W-5), template, styles, 7 layout tests and 2 page tests; rendered at 1280 and
  360 px; keyboard pass unchanged on the calendar (5 Tab stops). Marked droppable after B6 and
  Tier 2, before B13b. Snapshot refresh proposed, not written.
- 2026-11-17 · persona `frontend-eng` · unit groups (operator): `group` per unit added to the §10.1
  contract and to H-036; page 3 shows units under their group headings when sent, today's stage
  view until then (`6a2fb2b`). Tests 69; visual 24 of 24, so no snapshot refresh now; the step 1
  status snapshots will change when the backend sends `group` (with the H-006 refresh).
- 2026-11-17 · persona `frontend-eng` · B12 pulled forward (operator; H-040, H-041): dot chart and
  List / Month / Year views, display-only (W-5, W-6); 10 layout tests and 5 page tests (77 in all);
  keyboard pass with real key presses clean; snapshot refresh proposed, not written.
- 2026-11-17 · persona `frontend-eng` · page 7 rebuilt like `gp-calendar.html` (operator): summary
  cards with the dot chart, one calendar with a tab-styled radio switch (only the chosen view shows,
  no reload, no script); the two-month grid replaced by the Month view and removed from the helper.
  75 tests; switch checked with real key presses and a click. Departures recorded in H-036, H-040,
  H-042.
- 2026-11-17 · persona `frontend-eng` · operator's click-through feedback: after a decision, steps 2
  and 3 land on the next card to decide (W-7); switching calendar views no longer moves the page
  (section at least one screen tall on wide screens). 78 tests. Departure from ux.md page 4 "After
  each action" raised as H-043.
- 2026-11-17 · persona `frontend-eng` · calendar default view is Month (operator); recorded in H-040 and
  H-042. Visual-check flake fixed (M-012).
- 2026-11-17 · persona `backend-eng` · `sync-docs` · operator approved D1 to D5 after H-036 landed
  (V-1 to V-11, PRs #68 to #73): ✅/⏳ marks, the interim-lookups note, §10 and §11 headings and
  intros, S-06 and the `review_no` row updated. Only sentences the change made false; no spec edited.
  Handoff H-045 tells `@frontend.eng` the lookups are theirs to delete.
- 2026-11-17 · persona `backend-eng` · `sync-docs` · after B2 (PR #75): operator approved items 1 to 4
  (page 1 `refusal` wording, V-12 marked done in the intro and in §10 and §11, the §11 Refusals row,
  `refused` marked "not built"). Item 1 was worded "a plain sentence on this page" because sign-in
  still sends a plain sentence. Not touched: the other "⏳ `refusal`" marks (see the proposal).
- 2026-11-17 · persona `backend-eng` · `sync-docs` · operator asked for the page 2 "Reads" mark to
  be fixed: "⏳ `refusal`" is now "`refusal` ✅" (the shared refusal object, V-12).
- 2026-11-17 · persona `frontend-eng` · H-045 finished: the 14 interim tables deleted from
  `parts/lookups.html` (fixed ux.md wording kept), an unused import removed, the stepper test fixed
  (main had one failing test after #78). Every page rendered in every review state. Visual
  candidates: 18 changed, the 18 named in H-036's Outcome, each traced to a server field; refresh
  proposed, not written. §2, §4, §10, §10.1 and S-03, S-07, S-08, S-10, S-11, S-15, S-17, S-19,
  S-28 updated.
- 2026-11-17 · persona `frontend-eng` · H-014 and H-015 fixed in `site.css` (`c84d181`, operator
  option A) before the snapshot refresh; S-17 updated.
- 2026-11-17 · persona `frontend-eng` · H-036 snapshot refresh approved (18) and written; S-17 ✅;
  visual check passes on all 26.
- 2026-11-17 · persona `frontend-eng` · `frontend.md` brought in step with B12 (H-041, operator): §11
  Page 7 row now says the summary cards and the Month, Year and List views are built (display-only);
  §2 Page 7 "published" row no longer names the two-month week grid, which the Month view replaced.
  Docs only. No code. No snapshots touched.
- 2026-11-18 · persona `frontend-eng` · H-048 (1): the abandon textarea reads `typed.reason` and only
  for an `abandon` refusal, as the other forms do (S-29). Small change reusing an existing pattern:
  no UX session. Checked by rendering the refused page. No snapshot shows a refused abandon.
- 2026-11-18 · persona `backend-eng` · `sync-docs` (operator-approved) · "Where the CrewAI crews
  connect next": the three agent functions replace `run_unit` (B3 step 5, PR #96). One sentence only.
- 2026-11-19 · persona `frontend-eng` · `sync-docs` · §2 ("Approval blocked" is now sent) and §7 step 6 (B2 and B7 built) updated after the H-055, H-048 and H-027 change set; no rejected items.
- 2026-11-19 · persona `frontend-eng` · `update-visual-baselines` (operator approved 15 of 16) · 15 snapshots re-recorded; `07-calendar-gp-published-360` held back (mobile fix, see Open Questions).
- 2026-11-19 · persona `frontend-eng` · operator decision (phone menu below 960 px, H-062) · `sidebar.html`, `side_body.html`, `site.css`; no snapshot re-recorded.
- 2026-11-19 · persona `frontend-eng` · operator request (sign-in first on narrow screens, S-33) · `sign_in.html`, `site.css`; no snapshot re-recorded.
- 2026-11-19 · persona `frontend-eng` · `sync-docs` (operator-approved, 3 items) · sidebar breakpoint paragraph, "Later" note, sign-in left-panel row; no rejected items. Also: 3 baselines re-recorded with approval (`01-sign-in-360`, `07-calendar-gp-published-360`, `07-calendar-gp-empty-360`).
- 2026-11-19 · persona `frontend-eng` · operator request (specialist pages at 360 px, S-34) · `filing_rules.html`, `check_rules.html`, `confirm_applies.html`, `publish.html`, `site.css`; no snapshot touched.
- 2026-11-19 · persona `frontend-eng` · `sync-docs` · Doc sync: no updates (specialist 360 px tables, S-34).
- 2026-11-19 · persona `frontend-eng` · `document-frontend` (handoff H-063 to `@ux.designer`) · asks ux.md to record S-33 (sign-in first when narrow) and S-34 (specialist pages at 360 px; beyond UX-012). `handoffs.md` only; no code, no snapshot touched.
