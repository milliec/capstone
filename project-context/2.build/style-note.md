# Visual style note — Regulatory Intelligence

**How to use (@frontend.eng):** Layout from the operator's wireframes. Behaviour and wording from `project-context/2.build/ux.md`. Look from this note, which extends `editorial.css` — load that stylesheet first, then the app sheet whose `:root` is below. Buttons are never hidden or disabled to enforce a rule: a row that cannot be approved keeps its Approve button; the server refuses the click and the page shows the refusal message. Plain HTML, no JavaScript framework. No brand names or third-party wordmarks.

## Look

The same editorial system as the docs pages: near-monochrome, white page, no shadows, headings at weight 400, cards rounded at the top-left corner only. Colour is rationed. Orange marks the human gates and things that need attention; nothing else is coloured. Every page shows a "Demo with mock data" label. Status is always a word as well as a colour.

## Colour

Reuse the editorial token names and values. Two contrast fixes are applied as token changes (also listed under "Edits to editorial.css"). Status chips are the only app-only colours.

| Token | Hex | Use |
|-------|-----|-----|
| `--ink` | `#202020` | Text, headings, nav, icon strokes, primary button fill |
| `--ink-2` | `#4d4d4d` | Body copy |
| `--muted` | `#5c5c5c` | Helper, meta, captions, waiting-chip text. **Changed** from `#828282` (fails AA) |
| `--paper` | `#ffffff` | Page background, cards, primary-button text |
| `--band` | `#efefef` | Sidebar, section bands, pill containers |
| `--nest` | `#f5f5f5` | Nested surfaces, table headers, waiting-chip wash |
| `--warm` | `#ebe6dd` | Featured wash only — not the page background |
| `--rule` | `#e8e8e8` | Hairline borders and row dividers |
| `--accent` | `#ff682c` | Decoration only: gate marks, 3px left bars, underlines, focus outline. **Not text, not a fill** (2.89:1 on `--paper`; white-on-accent also fails) |
| `--accent-2` | `#816729` | Secondary accent and demo-label text, on `--paper` / `--band` / `--nest` only. **Not on `--warm`** (4.33:1, fails AA) |
| `--accent-text` | `#b33d12` | **New.** The only orange allowed for letters (5.84:1 on `--paper`, 4.70:1 on `--warm`) |

Links stay `--ink` text with an `--accent` underline, as in editorial.css. Do not colour anything else.

## Type

`--font-head`: Inter Tight (or Space Grotesk), weight **400 only**, tracking `-0.02em`. Do not bold headings. `--font-body`: Inter, 400 for paragraphs, 500 for UI labels, 600 only for small chip text if needed. Load both from a public source (for example Google Fonts). Do not commit a proprietary font file.

App scale (skip the docs hero size):

| Role | Size / leading / tracking |
|------|---------------------------|
| Page title | 32px / 1.19 / -0.02em, `--font-head` 400 |
| Section title | 18px / 1.25, `--font-head` 400 or Inter 500 |
| Body / controls | 16px / 1.5, Inter 400 or 500 |
| Caption, meta, chips, table helper | 14px / 1.43, Inter 400 or 500 |
| Small chip / stepper index | 12px / 1.2, Inter 500 or 600 |

## Spacing, radius, borders

Base unit 4px. Comfortable density: 8 / 12 / 16 / 20px inside components; 36–40px around page titles; `--gap` (20px) between cards. Sidebar about 240px. Content max-width 1200px. Borders: 1px `--rule`, or 1px `--ink` on ghost buttons. No box-shadows.

Reuse editorial radii. Do not use an 8px all-round card radius.

| Token | Value | Use |
|-------|-------|-----|
| `--r-card` | `6px 0 0` | Working cards, tables, alerts — soft top-left corner only |
| `--r-figure` | `20px` | KPI / summary cards, week-grid calendar, data figures |
| `--r-tag` | `20px` | Demo label, status chips |
| `--r-pill` | `200px` | Nav pills |
| Buttons | `0` | Same as `.ghost` — sharp corners on every button |
| Form controls, filters | `3px` | `--r-input` (app-only; matches editorial `code`) |

## Components

- **Shell.** `--paper` page; left sidebar in `--band` with `--ink` nav in `--font-head` at 16px/400. The current item uses an `--accent` underline, not a heavy fill. Header holds the product name in `--ink`, the fund name, the role (specialist or GP), and the demo label.
- **Demo label.** `--r-tag`, `--band` background, `--accent-2` text, Inter 12–14px 500, wording exactly "Demo with mock data". On every page. Keep it on `--band` or `--paper`, never on `--warm`.
- **Stepper** ("Step 1 of 3" and so on). Quiet typographic steps in `--font-head`, 14–16px. The current gate is `--ink` with an `--accent` underline; later steps use `--muted`. G1 / G2 / G3 section headers may use the same underline or a 3px `--accent` bar. No chunky wizard bar.
- **KPI / summary cards.** `--paper`, `--r-figure`, 20–40px padding, no shadow. Title in `--muted` 14px; figure in `--font-head` 32px/400, `--ink`. A row of three or four above a queue or calendar.
- **Tables (G1 / G2 queues).** `--paper` card, `--r-card`. Light `--rule` row dividers only. Header in Inter 14px 500, `--muted` or `--ink-2`. Status and quote-check always include a word, not colour alone.
- **Week-grid calendar (GP view, and the G3 review).** Seven columns, `--rule` hairlines, `--paper` cells, card `--r-figure`. Entries are chips plus the duty and who files, in words. "Due next" may use a `--warm` cell wash or an `--accent` underline on the date, never an `--accent` fill. The GP view has no action buttons.
- **Filter dropdowns.** `--paper` or `--nest`, 1px `--rule` border, `--r-input`, Inter 14px, `--ink` value, `--muted` placeholder.
- **Buttons.** Primary (Approve, Publish, Finish review, Start run): `--ink` fill, `--paper` text, 0 radius, 10px 20px padding, `--font-head` 16px/1, tracking `-0.02em`. Secondary (Reject, Decline, Abandon): same as `.ghost` — transparent, 1px `--ink` border, `--ink` text, same padding and radius. Links such as "Refresh now" and "Stop automatic refresh" are `--ink` text with an `--accent` underline. Never use `--accent` as a button fill.
- **Form controls.** 1px `--rule` border, `--r-input`, Inter 16px, `--ink` text, 8–12px padding. Nothing preselected that implies a decision.
- **Refusal / error alerts.** Sit beside the row or action, not in a modal. `--nest` or `--warm` wash, `--r-card`, a 3px `--accent` left bar (decoration only), `--ink` body text. The demo-row message uses the wording in `ux.md`. The Approve button stays visible and enabled. Focus uses editorial's `:focus-visible` outline (`2px solid var(--accent)`).

## Status chips

Always a short word (or the exact `ux.md` phrase) on a pale wash, dark AA-safe text, optional 1px same-hue border, `--r-tag`, Inter 12–14px 500. Do not use light text on a saturated fill. Rejected and declined share a family and are distinguished by words; so do refused/blocked and quote-check failed.

| Status | Text token / hex | Wash token / hex | Contrast |
|--------|------------------|------------------|----------|
| Approved | `--status-approved-text` `#1f5a32` | `--status-approved-bg` `#e6efe8` | 6.96:1 |
| Published | `--status-published-text` `#1b4d30` | `--status-published-bg` `#e7f0ea` | 8.39:1 |
| Rejected / declined | `--status-rejected-text` `#8a2c18` | `--status-rejected-bg` `#f8e6e0` | 7.08:1 |
| Waiting | `--status-waiting-text` `#5c5c5c` | `--status-waiting-bg` `#f5f5f5` | 6.13:1 |
| Verifier flag | `--status-flag-text` `#6b5420` | `--status-flag-bg` `#f3ead4` | 6.02:1 |
| Refused / blocked, quote-check failed | `--status-refused-text` `#8b1e12` | `--status-refused-bg` `#f3d8d1` | 6.79:1 |

## CSS custom properties

The app loads `editorial.css` first, then this `:root`, which extends it. Do not redeclare the shared tokens except the two contrast fixes, so the sheets stay one system. Until those fixes are patched into `editorial.css`, the overrides below keep the app correct.

```css
/* Load Inter (400, 500, 600) and Inter Tight (400) from a public source,
   then editorial.css, then this sheet. Do not commit a proprietary font file. */
:root {
  /* Contrast fixes — also apply these in editorial.css (see below). */
  --muted: #5c5c5c;
  --accent-text: #b33d12;

  --status-approved-text: #1f5a32;
  --status-approved-bg: #e6efe8;
  --status-published-text: #1b4d30;
  --status-published-bg: #e7f0ea;
  --status-rejected-text: #8a2c18;
  --status-rejected-bg: #f8e6e0;
  --status-waiting-text: #5c5c5c;
  --status-waiting-bg: #f5f5f5;
  --status-flag-text: #6b5420;
  --status-flag-bg: #f3ead4;
  --status-refused-text: #8b1e12;
  --status-refused-bg: #f3d8d1;

  --r-input: 3px;
  --sidebar-width: 240px;
  --page-max-width: 1200px;
  --button-padding: 10px 20px;
}
```

## Edits to editorial.css

Do not edit the attached copy. Apply these minimal changes in the project's `editorial.css` so docs and app share one token set:

1. In `:root`, change `--muted: #828282` to `--muted: #5c5c5c`.
2. In `:root`, add `--accent-text: #b33d12;`.
3. `.tag.hold { color: var(--accent-text); }` — the inset border can stay `--accent`.
4. `.hold-note b { color: var(--accent-text); font-weight: 600; }`.
5. `.tag.ok` currently sets `color: var(--accent-2)` on `background: var(--warm)`, which fails AA (4.33:1). Change the background to `var(--band)` (4.68:1) or `var(--paper)` (5.38:1).
6. `.d-acc-t` fills with `--accent`, which fails as text (2.89:1 on `--paper`). Change to `fill: var(--accent-text)`.

## Contrast recap

All pairs specified above meet WCAG AA (4.5:1) for normal text, including `--muted` and `--accent-text` on `--paper`, `--band`, `--nest` and `--warm`, and `--accent-2` on `--paper`, `--band` and `--nest`. `--ink` / `--ink-2` on those surfaces, and `--paper` on `--ink` (primary buttons), also pass.

Still fail, by design or until the docs edits land:

- `--accent` (`#ff682c`) as text, or as a fill under white text, on every light surface (2.89:1 on `--paper`). Keep it decorative only.
- `--accent-2` on `--warm` (4.33:1). Do not use this pair. `.tag.ok` in the unpatched docs file still uses it.
- `.d-acc-t` in the unpatched docs file still paints diagram labels with `--accent`.
