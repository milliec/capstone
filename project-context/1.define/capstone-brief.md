# Capstone Brief: Regulatory Intelligence for Fund Compliance Calendars

> A one-page summary for readers who have not seen the Define documents. Detail lives in `prd.md`,
> `system-description.md` and `user-stories/`. All data is mock; the fund is fictional.

## Vision

Regulated funds receive their filing obligations as static legal text, and compliance teams turn that
text into deadlines by hand, again for every new framework. We want a system where AI agents do the
first reading: every rule is extracted with a link to its exact source paragraph, checked by a separate
verifier, and approved by a specialist before anyone relies on it. Deadlines are then calculated by
plain code, so they are the same every time. The specialist moves from *writing* rules to *checking*
them, and fund managers get a calendar they can trust and understand.

## Users and the primary use case

| User | Role in the system |
|---|---|
| **Compliance specialist** (primary) | Owns the obligation calendar. Reviews agent output and approves at three gates. |
| **GP / fund manager** | Accountable for filings but files few of them. Reads the published calendar only. |
| **Filing parties** (AIFM, administrator, auditor, tax advisor, local agent) | Do most of the actual filings. Named on every obligation as "who files". **Not users in the MVP:** no notifications or confirmations. |

**Primary use case:** a specialist turns a set of regulatory sources into an approved compliance
calendar for one Luxembourg UCI Part II fund.

1. Agents extract obligation rows from the source text, each with a paragraph ID and verbatim quote.
2. A separate verifier checks the quotes and flags conflicts.
3. **Gate 1:** the specialist approves, edits or rejects each rule.
4. Agents judge whether each rule applies to the fund: applies, does not apply, or unsure.
5. **Gate 2:** the specialist confirms or overrides each verdict and decides every "unsure".
6. Code calculates the due dates.
7. **Gate 3:** the specialist publishes the calendar.
8. The GP sees what is due, when, who files it and why.

**When something needs correcting.** Every gate decision is made one item at a time. There is no
"approve all", nothing is preselected, and walking away approves nothing.

- **Decline at Gate 3.** The specialist gives a reason and sends the work back to Gate 1 or 2, or keeps
  it for later. Nothing new is published, and the draft and its history are kept.
- **Reopen a rejected rule, or a confirmed verdict.** A reason is required. The item goes back through
  its gate, and the earlier decision stays in the audit log.
- **After publishing.** GPs keep seeing the last published calendar. If a correction calls it into
  question, they see a neutral "under review" notice, which stays until a corrected calendar is
  published. The notice warns; it doesn't stop anyone relying on a wrong date.

There is no way to withdraw a published calendar in the MVP. That is deliberately deferred for this
demonstration and must be revisited before real-world use.

## In and out of the MVP

| In | Out |
|---|---|
| One fictional fund, one framework (Luxembourg UCI Part II) | Real client data, names or branding |
| Five obligations covering monthly, quarterly, year-end, conditional and event-triggered patterns, plus one decoy | Other funds, frameworks or jurisdictions |
| Mock regulatory text (our wording, citing real public laws) | Reading real legal documents (e.g. PDFs) |
| Extraction, separate verification, applicability judgement | Filing status, evidence of filing, reminders |
| Three human approval gates, with edit and re-verify | Live email or contact with any external party, including notifying filing parties |
| Deterministic due dates, with per-authority weekend rolls | Task tools as the system of record |
| Read-only GP calendar | Real login (roles are mocked) |
| Add-only audit log and an automatic evaluation against an answer key | Architecture choices (decided later, in the SAD) |

The AI model provider is the only live service. Everything else is mocked.

**Stretch goal (after the core works): change monitoring.** When a rule amendment arrives, the system
works out which obligations it affects (one, several or none), flags only those, and sends them back
through the gates. The specialist must review every impact report, including "no impact" ones: accept it, or send it for
manual review. This is
the part where the system decides its own path. Extraction, verification and
applicability follow a fixed order. It is tested with three mock amendments and is **not** part of the
Week 6 definition of done.

## Behaviour you could demo

| # | Story | Acceptance criteria you can see in a demo |
|---|---|---|
| 1 | **Source-linked extraction** | 6 rows appear from 6 source documents. Each shows a paragraph ID and a quote found word for word in that paragraph. A definition paragraph produces no row. |
| 2 | **The verifier catches problems** | The annual report row is flagged: one source says six months, another says four. A row with a wrong offset but a correct quote is also flagged. A row whose sources agree is **not** flagged. |
| 3 | **Approval needs a reason** | Approving a flagged row without a reason is refused. With a reason, it is approved, and the reason appears in the audit log. |
| 4 | **"Unsure" is decided by a person** | The Spanish filing comes back "unsure" (marketed in Spain, registration unconfirmed). Gate 2 cannot finish until the specialist decides. They mark it "applies, precautionary". |
| 5 | **Dates are calculated, not guessed** | A deadline falling on Sunday 10 Jan 2027 shows as Monday 11 Jan, with a note that it moved. 31 Dec 2026 + 6 months shows as 30 Jun 2027. Regenerating gives identical dates. |
| 6 | **The GP sees only approved work** | Before publishing, the GP view is empty. After publishing, it shows 22 entries, each with what, when, who and why, including the source quote. The decoy obligation does not appear. |

## Week 6 definition of done

A stranger can score each line **pass / fail** from the demo, the evaluation report and the repository.
**Done = every line passes.**

| # | Check | How to verify |
|---|---|---|
| 1 | The full flow runs from mock sources to the GP calendar without hand-editing data files | Watch the demo |
| 2 | Extraction: 6 of 6 expected rows, 0 extra rows, every quote word for word | Evaluation report |
| 3 | Applicability: 6 of 6 verdicts match the answer key | Evaluation report |
| 4 | Verifier: both planted conflicts flagged, no flag on agreeing sources, altered quote caught, wrong-field row caught | Evaluation report |
| 5 | Calendar: 22 of 22 entries with exact dates | Evaluation report |
| 6 | Attempts to skip any of the three gates are refused | Test log |
| 7 | Generating the calendar twice gives identical results | Test log |
| 8 | Every agent output and human decision in the demo run is in the audit log, with who and when | Audit log |
| 9 | Gate, date and audit-log tests pass without calling an AI model | Test log |
| 10 | A full run takes under 5 minutes and costs under US$2 in model usage | Evaluation report |
| 11 | A specialist completes all three gates in under 30 minutes, measured from audit-log timestamps | Evaluation report |
| 12 | The GP view shows what, when, who and why for every entry, and cannot be edited | Watch the demo |
| 13 | The repository contains no real names and no secrets | Run the scan command in `CLAUDE.md` |

## Open questions

These are still undecided. Everything else has been decided and recorded.

| Question | Options | Needed by |
|---|---|---|
| Does the full scope fit six weeks, and is there room for the stretch goal? | Keep everything / cut the hardening work / drop the stretch | Architect's estimate |
| Four-eyes review (a second specialist confirms before publish)? | In the MVP / after the MVP | Build planning |
| Before a calendar is first published, should GPs see a neutral "under review" note? (After publishing, a notice is already decided.) | Show / hide (default: hide) | UX design |
| Do Spanish (CNMV) and business-register deadlines roll past weekends? Does the Luxembourg subscription tax? | Roll / no roll (default: keep the earlier date) | Final demo data |
| How close must an extracted obligation name be to the expected one to pass? | Exact / close match | Evaluation design |

*Deferred to after the MVP:* a target for the share of rows approved without edits. Demo decisions are
scripted, so in Week 6 that rate would measure the script, not the agents.

---

## Sources

- `prd.md`, `system-description.md`, `user-stories/`, `mrd.md`, `mock-data/expected-obligation-library.md`

## Assumptions

- The definition of done restates PRD §7 and the acceptance criteria in plain words. It adds no new
  requirements.

## Open Questions

- See the table above.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-brief` (cohort summary of the Define documents)
- 2026-11-06 · persona `product-mgr` · action `update` · DoD #11 scored from the evaluation report;
  no-edit target deferred to after the MVP
- 2026-11-06 · persona `product-mgr` · action `update` · added the change-monitoring stretch goal
- 2026-11-06 · persona `product-mgr` · action `update` · filing parties named as out-of-scope stakeholders
- 2026-11-07 · persona `product-mgr` · action `update` · "When something needs correcting" (SD FR-022 to
  FR-025, PRD §6); stretch report acceptance (FR-026); withdraw deferred; GP note question narrowed to
  before first publication. Definition of done unchanged.
