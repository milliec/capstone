# Evidence Note (MRD — internal tool variant)

**Project**: Regulatory Intelligence for fund compliance calendars
**Document type**: Short evidence note in place of a full Market Research Document
**Selected Runtime**: crewai (from `aamad.config.yml`; recorded only, not evaluated here)

> **No external market.** This is an internal tool for one operator's compliance team and the GPs it
> serves. It will not be sold. This note therefore does not size a market, analyse competitors or
> propose pricing. Its job is narrower: show that the problem is real, that it is worth six weeks,
> and what we will and will not claim.

> **Anonymisation.** The source material contains real fund, company and personal names. All of these
> are replaced here with roles ("the operator", "the compliance team", "a GP"). Source documents are
> kept outside the repository.

---

## 1. Who hurts

| Who | The pain | Evidence |
|---|---|---|
| **Compliance specialists** (own the obligation calendar) | Every new regulatory framework means reading legal text again, interpreting each obligation and setting deadlines by hand. They also chase third parties who file for the fund. | Operator's internal working documents (SRC-INT). |
| **GPs / fund managers** (accountable for filings, but do not file most of them) | They receive a static legal document listing requirements but have no live view of what is due or why. GPs based outside Luxembourg are the least familiar with local obligations. | GP feedback reported in the operator's internal working documents (SRC-INT). |

## 2. What they do today

1. Obligations arrive as **static documents** that are not connected to any live system.
2. Deadlines and tasks are tracked **by hand** in spreadsheets and general task tools.
3. Each obligation is **interpreted manually** into deadline rules, and amended manually when someone spots a problem.

**What this produces: inconsistent interpretations.** Internal documents that describe the same obligations disagree with each other (SRC-INT). Illustrative examples of the kind of mismatch found:

| Obligation | One document says | Another says |
|---|---|---|
| Monthly Reporting U1.1, lead time | 3 days | 10 days |
| Annual Report, lead time | 30 days | 120 days |
| VAT, scheduling pattern | "Fixed date" | A relative rule: "31 October after year end" |
| Singapore declaration, due date | A fixed calendar date | Anniversary of fund registration |

None of these mismatches was caught by a check. A person had to notice it. This is the core problem the capstone targets.

**Why interpretation drifts: obligations come from overlapping layers** (SRC-CONTEXT). A Part II fund sits under several sets of rules at once:

- **Luxembourg product law:** the Law of 17 December 2010 (Part II), which governs the fund itself and its authorisation by the CSSF.
- **Fund-manager law:** the Law of 12 July 2013 on AIFMs, which applies because Part II funds qualify as alternative investment funds, and the EU AIFM Directive behind it.
- **Other EU rules:** for example PRIIPs (the KID, for funds open to retail investors) and SFDR (sustainability disclosures).
- **Tax, registry and cross-border rules:** for example the subscription tax, the beneficial-owner register, and reporting in each country where the fund is marketed.

Each layer brings its own authorities, deadlines and wording. The same filing can be described differently in different places, and a change in one layer can affect obligations in another. A specialist therefore interprets across several sources at once, and that is where the inconsistencies above come from. The capstone's five obligations deliberately span several of these layers.

## 3. Why this is worth six weeks

- **The risky part is interpretation, not the calendar.** Calendars, statuses and reminders are well-understood problems. The open question is whether legal text can be turned into structured, **source-linked** rows that a specialist trusts. The table above shows this is where errors enter today.
- **It repeats with every new framework.** The operator's goal is that onboarding a framework should be configuration, not a new software project (SRC-INT). Today that configuration is still manual reading. The capstone tests whether agents can do the first pass.
- **It can be tested in six weeks.** Five obligations, one fictional fund and mocked external systems give a contained test. If it fails, we learn that cheaply. If it works, the approach extends row by row.
- **Human approval stays in place.** A specialist approves, edits or rejects every extracted rule and every applicability decision. The time saved comes from *checking* rather than *authoring*, not from removing the human.

### Why a thin slice is enough

The capstone answers one question: **can agents turn legal text into deadline rules that a specialist trusts enough to approve?** A thin slice answers it because:

- **It covers every pattern, not every rule.** Five obligations span monthly, quarterly, year-end, conditional and event-triggered deadlines, plus one decoy that should be rejected. More obligations add rows, not new mechanics.
- **It includes the hard cases on purpose:** an ambiguous "unsure" case, two planted source conflicts, a wrong field behind a correct quote, and weekend and month-end date edge cases.
- **It runs end to end:** source text → extraction → verification → applicability → three human gates → calendar → GP view. Nothing is stubbed in the middle.
- **It is provable.** A fixed answer key (6 rows, 6 verdicts, 2 conflicts, 22 calendar entries) means success is measured, not judged by eye.
- **It is watchable.** The whole flow fits in one demo, with specialist review targeted at under 30 minutes.

## 4. What already exists

- **Earlier internal work** (SRC-INT): the operator has explored tracking obligations once rules exist. The capstone does not rebuild or depend on it. It covers the step *before*: producing the rules.
- **The "anchor + offset" deadline idea** (for example "year-end + 6 months") is a common way to express filing deadlines. The capstone uses it as its rule format.
- **Advice from legal counsel** (A-5): expert and authoritative, but delivered as documents. It still has to be turned into deadlines by hand, framework by framework.
- **General AI chat tools** asked to read the law (A-5): a fast first reading, but with no fixed structure, no verbatim source link, no independent check, no approval step, and dates computed by the model.
- **Commercial regulatory-compliance software: not researched.** No comparison is made or claimed.

## 5. What we will not claim

- **No market size, pricing or willingness to pay.** There is no external market.
- **No measured time savings.** No baseline has been measured. Any effort comparison in the capstone will be labelled as an estimate.
- **No legal advice and no guarantee of legal correctness.** Output is a draft that a specialist must approve.
- **No claim that the agents replace the compliance specialist.**
- **No accuracy claim beyond the five demo obligations, one decoy obligation and one fictional fund.** In particular, no claim for other frameworks, fund types or jurisdictions.
- **No claim to process real regulatory text verbatim.** The capstone uses mock source passages that cite real public laws. The wording is our own and labelled as mock.
- **No use of real client data or branding.**
- **No validated user research.** User needs are inferred from the brief and internal documents. No interviews were conducted (PRD A-7).
- **No verified legal date conventions.** Weekend-roll and end-of-month rules come from operator guidance and have not been checked against the legal texts (system description A-7).

---

## Sources

- **SRC-INT**: The operator's internal working documents. Private and confidential; not in the repository and not described further.
- **SRC-BRIEF**: Operator brief for this capstone (problem, users, MVP scope, in/out of scope).
- **SRC-CONTEXT**: Operator-provided regulatory background drawn from public sources (Luxembourg industry and law-firm summaries). Summarised in our own words. **Not independently verified.**

## Assumptions

- **A-1**: The pain described in SRC-INT (GP feedback, manual chasing) is representative of other regulated funds the operator serves. Not independently verified.
- **A-2**: The four document conflicts in §2 come from manual interpretation, not from deliberate per-fund differences. To be confirmed with the compliance team.
- **A-3**: Six weeks is the capstone timebox given in the brief. This note does not estimate effort.
- **A-4**: A full MRD is skipped because the tool is internal with no external market. This evidence note replaces it, by operator decision.
- **A-5**: The alternatives "advice from legal counsel" and "general AI chat tools" in §4 are described from general knowledge of how such work is done. They were not researched.
- **A-6**: The description of overlapping regulatory layers in §2 is background for the problem only. No requirement depends on it, and it is not used as a legal reference.

## Open Questions

- **OQ-1**: Which value is correct in each §2 conflict? The capstone does not need the answer, only to *detect* the conflict. Production would.
- **OQ-2**: What is a credible success signal for "worth it" that does not need a measured baseline? For example: the share of extracted rows a specialist approves without edits. *Deferred to after the MVP:* in the scripted demo this rate would measure the script, not the agents.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-mrd` (internal-tool evidence-note variant, operator-requested) · runtime `crewai`
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · reduced detail on internal sources for the public repo; added the decoy obligation to §5
- 2026-11-06 · persona `product-mgr` · action `update` · added "Why a thin slice is enough" (§3), two alternatives (§4, A-5) and two claims not made (§5), to match the cohort material
- 2026-11-06 · persona `product-mgr` · action `update` · enriched §2 with why interpretation drifts (overlapping regulatory layers); SRC-CONTEXT, A-6
