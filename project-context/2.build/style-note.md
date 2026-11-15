# Visual style note — Regulatory Intelligence

**Source of truth:** `docs/prototype/app.css`. Its section 1 (`:root` tokens) holds every colour, font, radius and easing value used here. This note describes that stylesheet and records the product rules around it. If the two disagree, the stylesheet wins: fix this note.

**How to use (@frontend.eng):** Layout from the operator's wireframes. Behaviour and wording from `project-context/2.build/ux.md`. Look from `app.css` and this note. The app loads one stylesheet; there is no separate base sheet. Buttons are never hidden or disabled to enforce a rule: a row that cannot be approved keeps its Approve button; the server refuses the click and the page shows the refusal message. Plain HTML, no JavaScript framework. No brand names or third-party wordmarks. Load the fonts from a public source (for example Google Fonts). Do not commit a proprietary font file.

## Look

A grey page with a white sidebar panel and white cards on it. No shadows. Headings at weight 400. Corners are soft and the same everywhere (6px on panels, cards and buttons). Colour is rationed: orange marks the human gates and things that need a person, brass marks work drafted by an agent, slate marks things that are settled, bordeaux marks refusals. Every page shows a "Demo with mock data" label. Status is always a word as well as a colour.

## Layout

- **Page.** `--page` (`#f5f5f5`) behind everything. Body text 15px / 1.5 in `--body`.
- **Shell.** A two-column grid: a 264px white sidebar and the main column, 8px apart, 16px of padding round the edge. The sidebar is a `--card` panel, sticky, full viewport height minus 32px. Below 1100px it stacks above the content and stops being sticky.
- **Main column.** Up to 1240px wide, 28px / 32px padding.
- **Sidebar contents (top to bottom).** Wordmark with a small orange square, product name, fund block (hairline above), nav, the "waiting" panel on `--ivory`, then the person and demo label pinned to the foot.
- **Nav.** Heading font 15px / 400, an 18px line icon in brass. The current page has a `--panel` row, weight 500, and an orange icon. Hover uses `--page`.
- **The stage.** `--ivory` is the "stage": things that need a person. It is a surface for notes, the waiting panel and sign-in, not a page background.

## Colour

All values come from `:root` in `app.css`. Contrast is measured against the four surfaces text can sit on.

| Token | Hex | Use | on `--card` | on `--page` | on `--panel` | on `--ivory` |
|-------|-----|-----|-------------|-------------|--------------|--------------|
| `--ink` | `#202020` | Headings, buttons, nav, links | 16.29 | 14.94 | 14.17 | 13.11 |
| `--body` | `#4d4d4d` | Paragraphs | 8.45 | 7.75 | 7.35 | 6.80 |
| `--muted` | `#636363` | Helper text, meta, captions | 6.01 | 5.51 | 5.22 | 4.83 |
| `--orange-text` | `#b33d12` | **The only orange allowed for letters** | 5.84 | 5.36 | 5.08 | 4.70 |
| `--brass` | `#816729` | Small labels, link underlines, ids | 5.38 | 4.93 | 4.68 | **4.33 fails** |
| `--bordeaux` | `#6b1e1c` | Refused, rejected, failed | 11.49 | 10.54 | 9.99 | 9.24 |
| `--slate` | `#1f3138` | Done, approved, published | 13.51 | 12.39 | 11.75 | 10.87 |
| `--orange` | `#ff682c` | **Decoration only:** gate squares, 3px left bars, underlines, focus outline | **2.89 fails** | **2.65 fails** | **2.51 fails** | **2.32 fails** |

Surfaces: `--page` `#f5f5f5` (page), `--panel` `#efefef` (quiet bands, the active nav row, tab trays), `--card` `#ffffff` (sidebar, cards, tables), `--ivory` `#ebe6dd` (the stage). Lines: `--rule` `#e4e4e4` for hairlines, `--line` (ink at 21%) for control borders.

Rules that follow from the table:

- **Never use `--orange` as text, or as a fill under text.** It is decoration. Use `--orange-text` for letters.
- **Never put `--brass` text on `--ivory`** (4.33:1, below AA). Use `--ink`, `--body` or `--orange-text` there.
- Links are `--ink` with a 1px brass underline, 3px below the text. On hover the text turns brass.
- Focus is a 2px orange outline, 2px offset, on every focusable element.
- Do not colour anything else. If a new meaning needs a colour, add it to this note first.

## Status families

Four tone families, each a text colour, a pale wash and a thin border of the same hue. Chips (`.chip`) are pill-shaped, Inter 12px / 500, with a short word or the exact `ux.md` phrase. Never light text on a saturated fill.

| Family | Class | Means | Text | Wash | Border | Contrast |
|--------|-------|-------|------|------|--------|----------|
| Orange | `.chip.you` | Needs a person | `--orange-text` `#b33d12` | `--orange-wash` `#fff0ea` | `--orange-line` `#ffc2a6` | 5.26 |
| Brass | `.chip.agent` | Drafted by an agent | `#6b5420` | `--brass-wash` `#f4f0e3` | `--brass-line` `#d3c7a3` | 6.32 |
| Slate | `.chip.done` | Done, approved, published | `--slate` `#1f3138` | `--slate-wash` `#e7eef0` | `--slate-line` `#b9cad0` | 11.50 |
| Bordeaux | `.chip.no` | Refused, rejected, failed | `--bordeaux` `#6b1e1c` | `--bordeaux-wash` `#f6e9e7` | `--bordeaux-line` `#dcb6b1` | 9.70 |
| Plain | `.chip` | Neutral, waiting | `--body` `#4d4d4d` | `#f7f7f7` | `--rule` | 7.89 |

Rejected and declined share the bordeaux family and are told apart by their words; so do refused/blocked and quote-check failed. The same four hues drive the small square before a section title (`.sq`: orange = needs you, brass = agent, ink = settled), the stepper, and the KPI icon tile.

## Type

Three fonts, all loaded from a public source.

| Font | Token | Used for |
|------|-------|----------|
| Lexend | `--font-head` | Headings, nav, buttons, tabs, figures. Weight **400 only**, tracking `-0.02em` (`-0.01em` for small sizes). Do not bold headings. |
| Inter | `--font-body` | Paragraphs (400), UI labels (500), chip text (500) |
| DM Mono | `--font-id` | Rule and record ids only, 12.5px, brass, no tracking |

| Role | Size / leading |
|------|----------------|
| Page title (`h1`) | 34px / 1.1 |
| Section title (`h2`) | 22px / 1.15 |
| Card title (`h3`) | 16px / 1.25 |
| Body | 15px / 1.5 |
| Buttons, nav | 15px / 1, Lexend |
| Small text, meta | 13px / 1.45 |
| Chips, small labels | 12px / 1 or 1.3, Inter 500 |

Numbers in tables and counts use tabular figures (`.num`).

## Icons

Iconoir line icons (MIT licence), placed inline as SVG so they need no network. The source files are in `docs/prototype/icons/` and `build.py` inlines them. They use `stroke="currentColor"`, no fill, stroke width 1.5. Colour comes from the surrounding rule in `app.css`: brass in the nav, orange for the current page, white on the KPI tile, slate in the trust line. An icon never carries meaning alone; a word sits beside it.

## Radius, borders, depth

| Token | Value | Use |
|-------|-------|-----|
| `--r-panel` | `6px` | Sidebar, KPI cards, cards, the stage, the right-hand rail |
| `--r-card` | `6px` | Alerts, notes, source panels, option boxes |
| `--r-btn` | `6px` | Buttons, tab tray |
| `--r-ctl` | `4px` | Inputs, selects, date tiles, tabs inside the tray, fact cards |
| `--r-pill` | `200px` | Chips, the demo label |

Borders are 1px `--rule`, or 1px `--ink` on ghost buttons. Notes and alerts that sit beside a row have a 3px left bar (square on the left edge, rounded on the right). **No drop shadows.** `box-shadow` is used only as a hard-edged line: inset underlines and left bars (orange or brass), a 1px inset outline, and one 1px ring on the stacked cards in the sign-in cluster. Never blur or spread a shadow to lift a card.

## Components

- **Buttons.** Primary (Approve, Publish, Finish review, Start run): `.btn`, `--ink` fill, near-white text, Lexend 15px, 40px tall, 20px side padding. Secondary (Reject, Decline, Abandon): `.ghost`, transparent with a 1px `--ink` border; on hover it fills with `--ink`. Small variant (`.sm`) is 32px tall. Never use orange as a button fill.
- **Demo label.** `.demo`, a pill in the brass family: brass text on `--brass-wash` with a `--brass-line` border, Inter 12px / 500. Wording exactly "Demo with mock data". On every page, in the sidebar foot.
- **Stepper and pillars.** Four steps with a 3px top rule. Done steps use a slate rule; the current step uses an orange rule and orange-text sub-label; a skipped step has a dashed rule and a struck-through title. Later steps are `--muted`.
- **KPI cards.** `.kpi`, white, `--r-panel`, 22px / 24px padding, no shadow. Title in `--muted`; figure in Lexend. A row of three or four above a queue or calendar.
- **Tables and queues.** White card, light `--rule` row dividers only. Status and quote-check always include a word, not colour alone.
- **Calendar (month, year and GP views).** `--rule` hairlines, white cells, date tiles at `--r-ctl`. Entries are chips plus the duty and who files, in words. The GP view has no action buttons.
- **Form controls.** `select`, text input and textarea: Inter 14px, white, 1px `--line` border, `--r-ctl`, 8px / 10px padding. Nothing preselected that implies a decision.
- **Refusal alerts.** `.refusal`: a `--bordeaux-wash` box with a 3px bordeaux left bar, `--ink` text. Sits beside the row or action, not in a modal. The Approve button stays visible and enabled. The refused row pulses once (orange outline, 1.4s).
- **Flags and callouts.** `.flag`, `.caught`, `.cta`, `.refline`: `--ivory` or white with a 3px **orange** left bar (decoration only). A waiting call to action swaps the bar to brass.
- **Trust line.** `.trust`: slate wash and border, slate text, for "this was checked" statements.

## Motion

One easing curve, `--ease: cubic-bezier(.645, .045, .355, 1)`, for everything that moves. Colour changes on hover use a plain 200ms linear fade.

| Where | What | Duration |
|-------|------|----------|
| Links, buttons, rows, chips on hover | Colour and background fade | 200ms linear |
| "More" links | Brass underline draws left to right | 400ms |
| Sign-in cards and calendar cards | `settle`: fade up 18px, staggered 120 / 320 / 520ms | 700ms |
| Caught-by-the-check note | `slidein`: fade in from 10px left | 500ms |
| Refused rule card | `pulse`: one orange outline ring | 1400ms, 300ms delay |
| Source highlight | `draw`: highlight grows across | 800ms |
| Ring, bars, dots | Arc draws, bars grow, dots scale in | 1100ms / 900ms / 420ms |

**Reduced motion.** `@media (prefers-reduced-motion: reduce)` switches off every animation and transition on every element (`animation: none`, `transition: none`, both `!important`). Anything that starts hidden and relies on an animation to appear must also be given its end state under that media query. The `.dot` marks do this (`opacity: 1; transform: none`). Check every new animated element with reduced motion on.

## Contrast recap

Every pair in the tables above meets WCAG AA (4.5:1) for normal text except the ones marked **fails**, which are banned by the rules under "Colour": `--orange` as text anywhere, and `--brass` text on `--ivory`. Primary-button text (`#f5f5f5` on `--ink`) is 14.94:1. Ratios were calculated from the hex values in `app.css`; recalculate them whenever a token changes.
