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
| 2 | `system-description.md` | Must do / must not / must cost / must prove, FR and NFR lists, 17 acceptance criteria, design principle **P-1** |
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
published calendar until republished · "roll rule unconfirmed" marks are specialist-only.

## Still open (none blocks the architecture)

| Question | Needed before |
|---|---|
| Four-eyes review: MVP or later? (PRD OQ-1) | Build planning |
| GP "under review" note? (PRD OQ-6) | UX step |
| Roll rules for CNMV and business-register filings; AED subscription tax (PRD OQ-7) | Final demo data |
| How close must an extracted name be to pass? (OQ-US001-1) | QA evaluation design |
| **Does the scope fit six weeks?** Not yet shown. Full scope kept until the architect estimates (PRD OQ-5) | **SAD**: please include an estimate |
| **Stretch goal F10 (change monitoring, US-014):** fits after the core? Depends on the MD-005 chain | **SAD**: please estimate it separately |

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
