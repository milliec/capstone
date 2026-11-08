# Context Summary — Define → Architecture

> **Handover status: NOT YET APPROVED.** The operator will approve the handover to `@system.arch`
> later. Until then, Define documents may still change.

**Product**: Regulatory Intelligence for fund compliance calendars · **Mode**: greenfield ·
**Runtime (config)**: `crewai`, recorded only. Pattern, runtime design and agent roster are for the SAD.

## In one paragraph

Compliance specialists turn static legal text into filing deadlines by hand, and manual interpretation
produces inconsistent rules. The MVP is an agentic system that extracts **source-linked** obligation
rows from mock regulatory text, checks them with a **separate verifier**, judges which apply to **one
fictional Luxembourg UCI Part II fund**, and generates its compliance calendar with **deterministic
code**. A compliance specialist approves at **three gates** before a GP sees anything. All externals
are mocked.

## Read in this order

| # | Document | What it gives the architect |
|---|---|---|
| 1 | `prd.md` | Happy path (§2), features F1–F9 with testable criteria (§4), constraints for the architecture (§3) |
| 2 | `system-description.md` | Must do / must not / must cost / must prove, FR and NFR lists, 26 acceptance criteria (AC-018 to AC-020 and AC-025 are stretch; AC-021 to AC-024 cover the recovery paths; AC-026 covers explicit decisions), design principle **P-1** |
| 3 | `user-stories/README.md` | 13 stories, coverage map, demo decisions at each gate |
| 4 | `mock-data/expected-obligation-library.md` | Expected results: 6 rows, verdicts, 2 conflicts, **22 calendar entries**, date conventions D-1 to D-7 |
| 5 | `mock-data/mock-regulatory-sources.md`, `mock-fund-profile.md` | The inputs |
| 6 | `mrd.md` | Why this is worth six weeks, and what is **not** claimed |

## Constraints the SAD must satisfy

- **Three hard gates** (G1 rules, G2 applicability, G3 publish). No bypass is possible. *(SD MD-004, MN-003)*
- **Verifier separate** from the extractor. It runs a quote check plus internal and cross-source
  conflict checks. It flags and never resolves. *(SD MD-003, FR-004, MN-004)*
- **No model-computed dates.** Date code is deterministic and testable without a model. *(SD MN-005, NFR-001, NFR-011)*
- **Every row is source-linked**: paragraph ID plus a verbatim quote. *(SD MD-001, MN-006)*
- **Add-only audit log**; every approval records who made it. *(SD MD-009, NFR-003)*
- **Stable calendar-entry IDs**, so filing status can be added later. *(SD MD-010)*
- **Safe on failure**: invalid agent output stops the run, and nothing partial is published. *(SD NFR-004)*
- **Targets**: run under 5 min, under US$2 per run, specialist review under 30 min. *(SD MC-001 to MC-003)*
- **Public repo**: mock data only; real material stays in the git-ignored `reference/`. *(SD MN-001)*

## Decided in Define

Three gates (not one) · filing status out of scope · web surfaces · WCAG 2.2 AA · mocked roles · whole
calendar published at once · end-of-month date convention · business-day rule per obligation · `OBL-04`
resolved at G2 as "applies (precautionary: registration unconfirmed)" (P-1) · business-day rolls in
scope · G1 completes only when every row is decided · overrides cannot set "unsure" · GPs keep the last
published calendar until republished · "roll rule unconfirmed" marks are specialist-only · filing
parties (AIFM, administrator, auditor, tax advisor, local agent) are named stakeholders but not MVP
users (SD A-9) · G3 decline needs a reason and keeps the draft (SD FR-022) · a rejected row can be
reopened with a reason, then goes through G1 and G2 again (SD FR-023, a new scope decision, not a general
undo) · a confirmed verdict can be reopened with a reason without editing its rule (SD FR-024, a new
scope decision) · rejected rows are read-only until reopened (FR-023) · after publication, a change that
questions the published calendar shows GPs a neutral review notice; it clears only on a successful
republish (SD FR-025, MN-007 clarified) · no bulk or preselected approval decisions at G1, G2, G3 or
(stretch) report acceptance; silence leaves items pending (PRD §6).

## Still open (none blocks the architecture)

| Question | Needed before |
|---|---|
| Four-eyes review: MVP or later? (PRD OQ-1) | Build planning |
| GP "under review" note **before first publication**? (PRD OQ-6; after publication it is decided, SD FR-025) | UX step |
| Roll rules for CNMV and business-register filings; AED subscription tax (PRD OQ-7) | Final demo data |
| How close must an extracted name be to pass? (OQ-US001-1) | QA evaluation design |
| **Does the scope fit six weeks?** Not yet shown. Full scope kept until the architect estimates (PRD OQ-5) | **SAD**: please include an estimate |
| **Stretch goal F10 (change monitoring, US-014, now including report acceptance FR-026):** fits after the core? Depends on the MD-005 chain | **SAD**: please estimate it separately |
| Gate recovery paths: none open. *Stretch: every impact report needs acceptance or a documented manual review (SD FR-026, Could; mandatory whenever F10 is built).* *Fund-fact changes: deferred beyond MVP, direction recorded (SD OQ-9, §9). Verdicts already cite fact IDs; the SAD may use these references, but no fact editing or reassessment is in scope.* *Decided: G3 decline (SD FR-022), reopening a rejected row (FR-023), reopening a confirmed verdict (FR-024), GP review notice (FR-025); withdraw/unpublish deliberately deferred, revisit before real-world use (SD §9).* | Operator decision, before build planning |
| Effort for FR-022 to FR-025, added after the estimate request. Reopening is meant to reuse the edit path (MD-005); the effort is not yet checked | **SAD**: include in the core estimate |
| Frontend framework: operator intends Next.js; not a requirement (PRD OQ-8) | **SAD**: confirm or propose otherwise |
| Code folders for the approval-design rule. `.cursor/rules/approval-design.mdc` attaches only to `project-context/**/*.md`, so build and QA personas working in application code won't see the approval-map pointer. List the folders that will hold application code, agent configuration and tests, so the operator can widen the rule's file pattern before build starts. The rule is guidance only; enforcement stays in code and tests (approval map §7). | **SAD**: list the folders |

## Sources

- All Define documents listed above.

## Assumptions

- The architect reads this summary together with the documents it points to, not instead of them.

## Open Questions

- See "Still open" above.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-context` (summary only; MRD and PRD already exist) ·
  runtime `crewai` · handover pending operator approval
- 2026-11-06 · persona `product-mgr` · action `update` · verifier checks and AC count updated; Spain note
  renamed
- 2026-11-06 · persona `product-mgr` · action `readiness-check` · five PM calls confirmed by the operator;
  six-week fit handed to the SAD as an estimate request
- 2026-11-06 · persona `product-mgr` · action `update` · stretch goal F10 (change monitoring) added;
  separate estimate requested
- 2026-11-07 · persona `product-mgr` · action `record-open-questions` · added open questions from the
  draft approval map to "Still open"; no constraint changed
- 2026-11-07 · persona `product-mgr` · action `update` · G3 decline decided (SD FR-022); removed from
  "Still open"
- 2026-11-07 · persona `product-mgr` · action `update` · reopening a rejected row decided (SD FR-023,
  new scope decision); added to "Decided"; effort for FR-022/FR-023 requested from the SAD
- 2026-11-07 · persona `product-mgr` · action `update` · reopening a confirmed verdict decided (SD
  FR-024, new scope decision); added to "Decided" and to the SAD effort row
- 2026-11-07 · persona `product-mgr` · action `update` · GP review notice decided (SD FR-025, MN-007
  clarified); rejected rows read-only until reopened; "Still open" and the SAD effort row updated
- 2026-11-07 · persona `product-mgr` · action `update` · withdraw/unpublish deliberately deferred (SD
  §9); removed from "Still open"
- 2026-11-07 · persona `product-mgr` · action `update` · fund-fact changes deferred beyond MVP,
  direction recorded (SD OQ-9, §9)
- 2026-11-07 · persona `product-mgr` · action `update` · impact-report acceptance decided (SD FR-026,
  stretch); added to the stretch estimate request
- 2026-11-07 · persona `product-mgr` · action `update` · no bulk or preselected approval decisions
  (PRD §6) added to "Decided"
- 2026-11-07 · persona `product-mgr` · action `update` · corrected acceptance-criteria count (17 → 20)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `consistency-sweep` · OQ-6 row
  narrowed to before first publication (SD FR-025); no new decision
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · acceptance-criteria
  count 20 → 25 (new SD AC-021 to AC-025)
- 2026-11-07 · operator session (Claude Code, no AAMAD persona) · action `update` · acceptance-criteria
  count 25 → 26 (new SD AC-026)
- 2026-11-08 · operator session (Claude Code, no AAMAD persona) · action `record-open-questions` · asked
  the SAD to list code folders so the approval-design rule's file pattern can be widened before build;
  no requirement changed
