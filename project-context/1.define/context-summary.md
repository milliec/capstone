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
| 2 | `system-description.md` | Must do / must not / must cost / must prove, FR and NFR lists, 26 acceptance criteria (AC-018 to AC-020 and AC-025 are stretch; AC-021 to AC-024 cover the recovery paths; AC-026 covers explicit decisions), design principle **P-1**, and **§10 extensibility** (quality goal, kinds of variation, extension rules, two walkthroughs) |
| 3 | `user-stories/README.md` | 15 stories (14 Must, 1 stretch), coverage map, demo decisions at each gate |
| 4 | `mock-data/expected-obligation-library.md` | Expected results: 6 rows, verdicts, 2 conflicts, **22 calendar entries**, date conventions D-1 to D-7 |
| 5 | `mock-data/mock-regulatory-sources.md`, `mock-fund-profile.md` | The inputs |
| 6 | `mrd.md` | Why this is worth six weeks, and what is **not** claimed. Its evidence is an illustrative scenario for a fictional firm |
| 7 | `decision-log.md` | What was decided on 2026-11-09 (UX and business reviews), why, and where each document changed |

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
- **Public repo**: mock data only; real material stays in the git-ignored `reference/`. No employer
  documents are cited or summarised. *(SD MN-001, PRD §5, decision log DL-07)*
- **Timebox**: the MVP must fit the **six-week** capstone. A cut line between the core demo path and
  hardening is agreed before Build. *(PRD §8, OQ-5, decision log DL-08)*
- **Extensibility (quality goal)**: the MVP is the first validated configuration of a shared product.
  Prefer shared capabilities with configuration and defined extension points over client-specific
  copies. Future extensions keep the Part II results and every verification, approval and audit
  control. Only the Part II configuration is built. *(SD NFR-012, §10, EX-1 to EX-6)*

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
(stretch) report acceptance; silence leaves items pending (PRD §6) · extensibility is an architecture
quality goal; the capstone stays an internal specialist tool designed for reuse, with GPs as the
expected future buyers (unvalidated, SD A-10); market research waits until commercialising (SD §10.1, OQ-10) · additional
clients, regimes, marketing jurisdictions, fund-fact editing and configuration screens are out of MVP
scope (SD §9) · a jurisdiction under consideration is not active marketing: results are conditional,
and uncertainty prompts specialist review (SD §10.4, OQ-11) · client policy cannot override mandatory
controls; its future changes need an authorised decision, reason, version history and impact
assessment (SD §10.2, OQ-12).

**Decided 2026-11-09** (details and reasons in `decision-log.md`): precautionary verdicts labelled at G2
and in the GP view, with no implied registration or marketing permission (DL-01) · run status shown,
and a failed step can be re-run from the last safe state without losing gate decisions; new scope
(DL-02, US-015) · each verifier flag states its type and evidence (DL-03) · cited fund facts viewable
read-only at G2 (DL-04) · voice for agent and system text (DL-05) · persona claims and the expected buyer
labelled unvalidated (DL-06) · evidence uses only the fictional firm and public regulation (DL-07) ·
six-week timebox and a cut line before Build (DL-08) · a missed target is reported, not hidden (DL-10) ·
no ROI claim; labelled effort estimate for comparison (DL-11) · "not legal advice" is a Must, shown with
the unverified date-conventions note as one GP calendar-level note (SD FR-020, DL-12).

## Still open (none blocks the architecture)

| Question | Needed before |
|---|---|
| Four-eyes review: MVP or later? (PRD OQ-1) | Build planning |
| GP "under review" note **before first publication**? (PRD OQ-6; after publication it is decided, SD FR-025) | UX step |
| Roll rules for CNMV and business-register filings; AED subscription tax (PRD OQ-7) | Final demo data |
| How close must an extracted name be to pass? (OQ-US001-1) | QA evaluation design |
| **Does the scope fit six weeks?** Not yet shown. Full scope kept until the architect estimates; a cut line between the core demo path and hardening is then agreed (PRD OQ-5, §8, DL-08) | **SAD**: please include an estimate, including the failed-step re-run (US-015, new scope) |
| Retry limit for re-running a failed step (approval map OD-7, OQ-US015-1) | **SAD** |
| Capstone programme submission requirements (PRD OQ-10) | Operator, before the SAD estimate |
| Reused prototype front end: origin and clean-up (PRD OQ-11) | Operator, before Build |
| Manual-effort estimate for the five demo obligations (PRD OQ-12) | Operator, before the demo |
| **Stretch goal F10 (change monitoring, US-014, now including report acceptance FR-026):** fits after the core? Depends on the MD-005 chain | **SAD**: please estimate it separately |
| Gate recovery paths: none open. *Stretch: every impact report needs acceptance or a documented manual review (SD FR-026, Could; mandatory whenever F10 is built).* *Fund-fact changes: deferred beyond MVP, direction recorded (SD OQ-9, §9). Verdicts already cite fact IDs; the SAD may use these references, but no fact editing or reassessment is in scope.* *Decided: G3 decline (SD FR-022), reopening a rejected row (FR-023), reopening a confirmed verdict (FR-024), GP review notice (FR-025); withdraw/unpublish deliberately deferred, revisit before real-world use (SD §9).* | Operator decision, before build planning |
| Effort for FR-022 to FR-025, added after the estimate request. Reopening is meant to reuse the edit path (MD-005); the effort is not yet checked | **SAD**: include in the core estimate |
| Frontend framework: operator intends Next.js; not a requirement (PRD OQ-8) | **SAD**: confirm or propose otherwise |
| **Extensibility walkthroughs** S-1 (fictional Luxembourg RAIF) and S-2 (`FND-DEMO-01` considering Singapore institutional marketing; marketing not assumed permitted). Each is done separately and is architecture-only. For each, show what is shared, what is configuration (and of which kind), what needs an extension point, how EX-1 to EX-6 would be met, and which tests each would need (identified, not built or run) (SD NFR-012, §10.4, EX-5) | **SAD**: include both, and include any extensibility effort in the estimate |
| Client-data separation is deferred. The walkthroughs do not validate multi-client security (SD §10.5, OQ-13) | **SAD**: name the future isolation boundary and access-control assumptions |
| Client-policy changes: future requirement, no MVP feature (SD §10.2, OQ-12) | **SAD**: propose the mechanism |
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
- 2026-11-08 · persona `product-mgr` · action `update` · extensibility quality goal added to
  constraints and "Decided" (SD NFR-012, §10, OQ-10 to OQ-12); walkthroughs, isolation boundary and
  client-policy mechanism requested from the SAD; MVP scope unchanged
- 2026-11-09 · persona `product-mgr` · action `update` · UX and business reviews: decision log added to
  the reading order; story count 13 → 15; time-budget and no-employer-documents constraints; "Decided
  2026-11-09" paragraph; estimate request now in hours against 40–50; new open rows (retry limit, OQ-10
  to OQ-12); handover still pending operator approval
- 2026-11-09 · persona `product-mgr` · action `update` · time budget restated as the six-week timebox
  instead of 40–50 operator hours (decision log DL-08, revised); operator decision
