# Mock Regulatory Sources

> ⚠️ **MOCK DATA — NOT LEGAL TEXT.** The instrument names for `SRC-CSSF15627`, `SRC-UCILAW`,
> `SRC-RBELAW` and `SRC-VATLAW` are real, public Luxembourg laws and circulars, used so the demo reads
> realistically. `SRC-CNMV` names a real regulator but *describes* its requirement instead of citing a
> specific instrument. `SRC-PRACT` is entirely fictional. **All paragraph wording and numbering is
> invented for this capstone.** It is a simplified paraphrase written to test the agents.
> Do not quote it as law, and do not use it for real compliance decisions.

## How to read this file

- Each **source document** has an ID (e.g. `SRC-UCILAW`).
- Each **paragraph** has a stable ID (e.g. `SRC-UCILAW-P3`). Every extracted rule must cite exactly one
  paragraph ID plus a verbatim quote from that paragraph.
- **Primary** sources are mock excerpts of the law itself. **Secondary** sources are mock summaries
  written by third parties. If a secondary source contradicts a primary one, that is a conflict for the
  verifier to flag. It must not be silently resolved.

| Source ID | Mock excerpt of | Type | Demo purpose |
|---|---|---|---|
| `SRC-CSSF15627` | CSSF Circular 15/627 | Primary | Monthly pattern |
| `SRC-UCILAW` | Law of 17 December 2010 on undertakings for collective investment | Primary | Quarterly + year-end patterns, plus a paragraph with no obligation |
| `SRC-CNMV` | CNMV statistical reporting requirements for foreign UCIs marketed in Spain | Primary | Conditional pattern ("unsure" case) |
| `SRC-RBELAW` | Law of 13 January 2019 establishing a Register of Beneficial Owners | Primary | Event-triggered pattern |
| `SRC-VATLAW` | Luxembourg law of 12 February 1979 on value added tax | Primary | Decoy ("does not apply" case) |
| `SRC-PRACT` | *Fictional* practitioner guide to Luxembourg fund filings | Secondary | Planted conflicts for the verifier |

---

## SRC-CSSF15627 — CSSF Circular 15/627 (mock excerpt)

**SRC-CSSF15627-P1**
This circular applies to all undertakings for collective investment subject to Part II of the Law of
17 December 2010, including those structured as investment companies with variable capital.

**SRC-CSSF15627-P2**
Each undertaking for collective investment within the scope of this circular shall transmit the monthly
financial information report U1.1 to the CSSF no later than 10 calendar days after the end of each month.

**SRC-CSSF15627-P3**
The report shall be transmitted through the CSSF's secure electronic reporting channel. The fund
administrator may transmit the report on behalf of the undertaking.

---

## SRC-UCILAW — Law of 17 December 2010 (mock excerpt)

**SRC-UCILAW-P1**
For the purposes of this excerpt, "financial year-end" means the last day of the financial year stated
in the constitutive documents of the undertaking for collective investment.

> *Test note: P1 is a definition. It creates no obligation, and no row should be extracted from it.*

**SRC-UCILAW-P2**
Undertakings for collective investment established in Luxembourg are subject to an annual subscription
tax calculated on their net assets. The subscription tax return and payment shall be made to the
Administration de l'enregistrement, des domaines et de la TVA within 20 calendar days following the end
of each calendar quarter.

**SRC-UCILAW-P3**
An undertaking for collective investment subject to Part II of this law shall publish an audited annual
report and file it with the CSSF within six months of the end of the period to which it relates.

---

## SRC-CNMV — CNMV statistical reporting for foreign UCIs (mock excerpt)

**SRC-CNMV-P1**
Foreign undertakings for collective investment registered with the CNMV for marketing in Spain shall
submit statistical report A01 to the CNMV each quarter, within two months after the last calendar day of
the quarter.

**SRC-CNMV-P2**
The report may be submitted by a local reporting agent appointed by the undertaking.

> *Test note: P1 applies only to funds **registered with the CNMV**. The fictional fund is marketed to
> Spanish investors but its CNMV registration status is unconfirmed. The correct applicability verdict
> is therefore **unsure**, not "applies".*

---

## SRC-RBELAW — Law of 13 January 2019 on the Register of Beneficial Owners (mock excerpt)

**SRC-RBELAW-P1**
Registered entities shall file with the Luxembourg Business Registers any change to the information on
their beneficial owners within one month of becoming aware of the event that made the change necessary.

> *Test note: the anchor is the date the entity **became aware**, not the date the change happened.*

---

## SRC-VATLAW — Luxembourg VAT law (mock excerpt)

**SRC-VATLAW-P1**
Every taxable person registered for value added tax in Luxembourg shall file an annual VAT return with
the Administration de l'enregistrement, des domaines et de la TVA by 31 October of the year following the
financial year concerned.

> *Test note: the fictional fund is **not VAT-registered**. Extract the row, but the applicability
> verdict must be **does not apply**.*

---

## SRC-PRACT — Practitioner guide to Luxembourg fund filings (fictional secondary source)

> Fictional third-party summary. It is deliberately inaccurate in two places so the verifier has real
> conflicts to catch.

**SRC-PRACT-P1**
Funds must publish their audited annual report within four months of financial year-end.

> *Planted conflict C-1: contradicts `SRC-UCILAW-P3` (six months). Four months is the UCITS rule, a
> realistic mix-up for Part II funds.*

**SRC-PRACT-P2**
Changes to beneficial ownership must be filed with the register within one month of the change.

> *Planted conflict C-2: contradicts `SRC-RBELAW-P1`, which anchors on **becoming aware** of the event,
> not on the date of the change.*

**SRC-PRACT-P3**
The monthly U1.1 report is due 10 calendar days after month-end.

> *Agrees with `SRC-CSSF15627-P2`. Confirms the verifier does not flag agreeing sources.*

---

## Amendments (stretch goal: change monitoring)

> These arrive **after** the library has been approved. They are used only by the stretch goal
> (US-014). Each tests a different path: one duty affected, several affected, or none.

**AMD-01: replaces `SRC-UCILAW-P3`**
An undertaking for collective investment subject to Part II of this law shall publish an audited annual
report and file it with the CSSF within five months of the end of the period to which it relates.

> *Test note: one duty affected (`OBL-03`). The offset changes from six to five months.*

**AMD-02: adds a new paragraph `SRC-UCILAW-P4`**
For the purposes of this law and of any circular referring to it, an undertaking subject to Part II
includes only undertakings whose constitutive documents provide for the redemption of units at least
once a year.

> *Test note: several duties affected. Every rule whose applicability depends on "subject to Part II"
> must be re-checked: `OBL-01` and `OBL-03`. Their dates do not change. The fund redeems monthly
> (`FACT-07`), so both should still apply after re-checking.*

**AMD-03: replaces `SRC-RBELAW-P1`**
Registered entities shall, within one month of becoming aware of the event that made the change
necessary, file with the Luxembourg Business Registers any change to the information on their beneficial
owners.

> *Test note: no duty affected. Same meaning, words reordered. `OBL-05`'s quote still appears word for
> word. Nothing should be flagged.*

---

## Sources

- Instrument names: public Luxembourg legislation and CSSF circulars, cited by title only.
- Paragraph wording: written for this capstone. Simplified paraphrases, not copied from the laws.
- Obligation choice and test cases: operator decisions during Define (five obligations, one decoy,
  planted conflicts).

## Assumptions

- The simplified wording is close enough to the real rules for a realistic demo. It is **not** checked
  against the official texts and must not be used as a legal reference.
- Business-day rules are deliberately left out of every paragraph, so the specialist must set them at
  approval.

## Open Questions

- None for this file. Date-convention questions are in `expected-obligation-library.md`.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-mock-data` · mock sources for the demo
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · clarified which instrument names are
  real; added required sections
- 2026-11-06 · persona `product-mgr` · action `update` · added amendments AMD-01 to AMD-03 for the
  change-monitoring stretch goal
