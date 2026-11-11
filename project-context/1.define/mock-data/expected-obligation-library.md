# Expected Obligation Library (Answer Key)

> ⚠️ **MOCK DATA.** This is the **expected output** for the demo, derived from
> `mock-regulatory-sources.md` and `mock-fund-profile.md`. It is used later to test whether the
> extraction, applicability and verifier agents and the due-date code behave correctly. It is not legal
> advice.

**Contents:** (1) expected extracted rows · (2) expected applicability verdicts · (3) expected verifier
flags · (4) expected 2027 calendar · (5) date conventions · open questions.

> **Schema status:** the columns below are a **Define-phase draft** of the fixed extraction schema. The
> PRD will confirm the final field list. The architecture decides how it is stored.

---

## 1. Expected extracted rows (extraction agent)

Six rows are expected: five calendar obligations plus one decoy. **No row** should come from
`SRC-UCILAW-P1` (a definition), `SRC-CSSF15627-P1`/`P3`, `SRC-CNMV-P2` (supporting detail) or any
`SRC-PRACT` paragraph (secondary sources are checked by the verifier, not extracted).

| Code | Obligation | Pattern | Frequency | Anchor | Offset | Recipient | Responsible role | Applicability rule | Source paragraph |
|---|---|---|---|---|---|---|---|---|---|
| `OBL-01` | Monthly financial report U1.1 | Monthly | Monthly | Month-end | +10 calendar days | CSSF | Fund administrator | Fund is subject to Part II of the Law of 17 December 2010 | `SRC-CSSF15627-P2` |
| `OBL-02` | Subscription tax return and payment (taxe d'abonnement) | Quarterly | Quarterly | Calendar quarter-end | +20 calendar days | AED | Fund administrator | Fund is established in Luxembourg | `SRC-UCILAW-P2` |
| `OBL-03` | Audited annual report | Year-end | Annually | Financial year-end | +6 months | CSSF | Fund administrator, with AIFM and auditor | Fund is subject to Part II of the Law of 17 December 2010 | `SRC-UCILAW-P3` |
| `OBL-04` | Statistical report A01 (Spain) | Conditional | Quarterly | Calendar quarter-end | +2 months | CNMV | Local reporting agent | Fund is registered with the CNMV for marketing in Spain | `SRC-CNMV-P1` |
| `OBL-05` | Beneficial-owner information update (RBE) | Event-triggered | On occurrence | Date the entity became aware of the event | +1 month | Luxembourg Business Registers | AIFM | Fund is a registered entity | `SRC-RBELAW-P1` |
| `OBL-06` | Annual VAT return *(decoy)* | Year-end (fixed date) | Annually | Financial year-end | 31 October of the following year | AED | Tax advisor | Fund is registered for VAT in Luxembourg | `SRC-VATLAW-P1` |

Each row also carries a **business-day rule**. The sources do not state one, so the extraction agent
should output "not confirmed" for every row. The specialist's expected settings are in section 5.

**Expected verbatim quotes** (the quote check passes only if each quote appears exactly in its paragraph):

| Code | Quote |
|---|---|
| `OBL-01` | "no later than 10 calendar days after the end of each month" |
| `OBL-02` | "within 20 calendar days following the end of each calendar quarter" |
| `OBL-03` | "within six months of the end of the period to which it relates" |
| `OBL-04` | "within two months after the last calendar day of the quarter" |
| `OBL-05` | "within one month of becoming aware of the event that made the change necessary" |
| `OBL-06` | "by 31 October of the year following the financial year concerned" |

## 2. Expected applicability verdicts (applicability agent) for `FND-DEMO-01`

| Code | Verdict | Reasoning the agent should give | Facts used |
|---|---|---|---|
| `OBL-01` | **Applies** | The fund is subject to Part II. | `FACT-01` |
| `OBL-02` | **Applies** | The fund is established in Luxembourg. | `FACT-02` |
| `OBL-03` | **Applies** | The fund is subject to Part II. | `FACT-01` |
| `OBL-04` | **Unsure** | The rule requires CNMV registration. The fund is *marketed* in Spain, but its CNMV registration is not confirmed. Marketing alone does not satisfy the rule. A specialist must confirm. | `FACT-03`, `FACT-04` |
| `OBL-05` | **Applies** | The fund is a registered entity. An occurrence is logged as `EVT-01`. | `FACT-06`, `EVT-01` |
| `OBL-06` | **Does not apply** | The fund is not registered for VAT. | `FACT-05` |

> A wrong answer worth testing: the agent says **applies** for `OBL-04` because the fund is marketed in
> Spain. That is a confident error and should fail the test.

## 3. Expected verifier flags (verifier agent)

| Flag | Type | Rows | What the verifier should report | Expected handling |
|---|---|---|---|---|
| `C-1` | Conflict | `OBL-03` | `SRC-PRACT-P1` says four months. `SRC-UCILAW-P3` says six months. | Flag for the specialist. Do not auto-resolve. |
| `C-2` | Conflict | `OBL-05` | `SRC-PRACT-P2` anchors on the date of the change. `SRC-RBELAW-P1` anchors on becoming aware. | Flag for the specialist. Do not auto-resolve. |
| — | No flag | `OBL-01` | `SRC-PRACT-P3` agrees with `SRC-CSSF15627-P2`. | No conflict raised (tests for false alarms). |
| `I-1` | Internal conflict (injected test) | `OBL-02` | With the offset changed to "+30 calendar days" and the quote left as "within 20 calendar days…", the fields no longer match the quote. | Flag and block approval of that row. The quote check alone would pass. |
| `Q-*` | Quote check | All rows | Any quote that does not appear verbatim in its cited paragraph. | Flag and block approval of that row. |

## 4. Expected 2027 calendar (deterministic due-date code)

Generated **only from specialist-approved rows with a verdict of "applies"**. Horizon: due dates from
2027-01-01 to 2027-12-31.

"Calculated due date" is anchor + offset. "Calendar due date" applies that obligation's business-day
rule (see section 5).

| Code | Anchor date | Calculated due date | Business-day rule | Calendar due date |
|---|---|---|---|---|
| `OBL-01` | 2026-12-31 | 2027-01-10 (Sun) | Roll forward | **2027-01-11** (Mon) |
| `OBL-01` | 2027-01-31 | 2027-02-10 | Roll forward | 2027-02-10 |
| `OBL-01` | 2027-02-28 | 2027-03-10 | Roll forward | 2027-03-10 |
| `OBL-01` | 2027-03-31 | 2027-04-10 (Sat) | Roll forward | **2027-04-12** (Mon) |
| `OBL-01` | 2027-04-30 | 2027-05-10 | Roll forward | 2027-05-10 |
| `OBL-01` | 2027-05-31 | 2027-06-10 | Roll forward | 2027-06-10 |
| `OBL-01` | 2027-06-30 | 2027-07-10 (Sat) | Roll forward | **2027-07-12** (Mon) |
| `OBL-01` | 2027-07-31 | 2027-08-10 | Roll forward | 2027-08-10 |
| `OBL-01` | 2027-08-31 | 2027-09-10 | Roll forward | 2027-09-10 |
| `OBL-01` | 2027-09-30 | 2027-10-10 (Sun) | Roll forward | **2027-10-11** (Mon) |
| `OBL-01` | 2027-10-31 | 2027-11-10 | Roll forward | 2027-11-10 |
| `OBL-01` | 2027-11-30 | 2027-12-10 | Roll forward | 2027-12-10 |
| `OBL-02` | 2026-12-31 | 2027-01-20 | No roll (tax) | 2027-01-20 |
| `OBL-02` | 2027-03-31 | 2027-04-20 | No roll (tax) | 2027-04-20 |
| `OBL-02` | 2027-06-30 | 2027-07-20 | No roll (tax) | 2027-07-20 |
| `OBL-02` | 2027-09-30 | 2027-10-20 | No roll (tax) | 2027-10-20 |
| `OBL-03` | 2026-12-31 | 2027-06-30 | Roll forward | 2027-06-30 |
| `OBL-05` | 2027-01-31 (awareness, `EVT-01`) | 2027-02-28 (Sun) | **Not confirmed** → no roll | **2027-02-28** (Sun), marked "roll rule unconfirmed" |
| `OBL-04` | 2026-12-31 | 2027-02-28 (Sun) | **Not confirmed** → no roll | **2027-02-28** (Sun), marked "roll rule unconfirmed" |
| `OBL-04` | 2027-03-31 | 2027-05-31 | Not confirmed | 2027-05-31 |
| `OBL-04` | 2027-06-30 | 2027-08-31 (end-of-month, `D-2`) | Not confirmed | 2027-08-31 |
| `OBL-04` | 2027-09-30 | 2027-11-30 | Not confirmed | 2027-11-30 |

**Total: 22 calendar entries. 4 are rolled. 2 are marked as unconfirmed.**

**Why `OBL-04` is on the calendar:** the agent's verdict is **unsure** (section 2). In the demo the
specialist resolves it at G2 as **applies (precautionary: registration unconfirmed)**, following
design principle **P-1** in `system-description.md` (under uncertainty, choose the cheaper mistake). An
extra entry is harmless. A missed filing is not.

**Not on the calendar:**
- `OBL-06` (does not apply): no dates.

**Date edge cases this set tests:**
- February month-end (2027-02-28, not a leap year) as an anchor for `OBL-01`.
- 31 December + 6 months lands on 30 June, a month with only 30 days (`OBL-03`).
- 31 January + 1 month lands on 28 February (`OBL-05`).
- Using the event date (2027-01-20) instead of the awareness date gives **2027-02-20**, which is wrong
  (`OBL-05`).
- 30 June + 2 months = 31 August, the end-of-month convention (`OBL-04`).
- A weekend due date rolls to Monday for a CSSF filing (`OBL-01`), but **not** when the rule is
  unconfirmed (`OBL-05`). The code must read the rule per obligation, not apply one global setting.

## 5. Date conventions assumed in this answer key

| ID | Convention | Why it matters |
|---|---|---|
| ID | Convention | Status |
|---|---|---|
| `D-1` | Day offsets are counted in **calendar days**. | Assumed |
| `D-2` | When the anchor is a **period end** (month, quarter or year end) and the offset is in **months**, the due date is the **last day of the target month** (end-of-month to end-of-month). 30 June + 2 months = 31 August. | **Confirmed** by operator |
| `D-3` | When the anchor is an **event date** and the offset is in months, keep the same day of the month, moved back to the month's last day if that day doesn't exist. 31 January + 1 month = 28 February. | Assumed |
| `D-4` | Each obligation carries its own **business-day rule**: *roll forward* (to the next Luxembourg business day), *no roll*, or *not confirmed*. There is no global default. | **Confirmed** by operator |
| `D-5` | CSSF (and BCL) regulatory reporting: **roll forward**. Tax deadlines: **no roll**. | **Confirmed** by operator |
| `D-6` | If the rule is **not confirmed**, the calendar keeps the **earlier, unrolled date** and marks it "roll rule unconfirmed" for the specialist. Filing early is safe. Filing late is not. An application of design principle P-1. | Assumed (safe default) |
| `D-7` | `D-2` is applied first, then the business-day rule. | **Confirmed** by operator |

**Business-day rule per obligation**

| Code | Recipient | Rule | Basis |
|---|---|---|---|
| `OBL-01` | CSSF | Roll forward | `D-5` |
| `OBL-02` | AED (tax) | No roll | `D-5` |
| `OBL-03` | CSSF | Roll forward | `D-5` |
| `OBL-04` | CNMV (Spain) | Not confirmed | Spanish practice not covered by `D-5` |
| `OBL-05` | Luxembourg Business Registers | Not confirmed | Not covered by `D-5` |
| `OBL-06` | AED (tax) | No roll | `D-5` |

> The mock sources do not state business-day rules. So the extraction agent should output
> **not confirmed**, and the specialist sets the rule when approving the row. The values above are the
> **specialist's expected settings** for the demo.

**Mock Luxembourg public holidays, 2027** (a stand-in for an official holiday calendar)

1 Jan (New Year) · 29 Mar (Easter Monday) · 1 May (Labour Day) · 6 May (Ascension Day) · 9 May (Europe
Day) · 17 May (Whit Monday) · 23 Jun (National Day) · 15 Aug (Assumption) · 1 Nov (All Saints) · 25 Dec
(Christmas) · 26 Dec (St Stephen's Day)

> *Note: in this demo every roll is caused by a weekend. None of the due dates falls on a public
> holiday.*

## 6. Stretch goal: expected impact of amendments (change monitoring)

Run **after** the 22-entry calendar has been published. Each amendment is run on its own against that
published state. The system proposes impact. The specialist decides at G1 and G2 as usual.

| Amendment | Expected impact | Rows to flag | Gate | Calendar effect | Must **not** flag |
|---|---|---|---|---|---|
| `AMD-01` (annual report: 6 → 5 months) | **One** duty | `OBL-03` (its quote and offset no longer match the new text) | G1 | The `OBL-03` entry is marked out of date. If the specialist approves "+5 months", the new date is **2027-05-31** (Monday, no roll). | `OBL-02` (same source document, different paragraph) |
| `AMD-02` (new Part II scope paragraph) | **Several** duties | `OBL-01`, `OBL-03` (applicability depends on "subject to Part II") | G2 | 13 entries marked out of date until verdicts are re-confirmed. After re-check (`FACT-07`: monthly redemption) both still **apply**, and the dates are unchanged. | `OBL-02`, `OBL-04`, `OBL-05`, `OBL-06` |
| `AMD-03` (RBE wording reordered) | **None** | none | — | None. The report says "wording change only; no impact". | `OBL-05` |

**What this tests:** that the system decides *how far* a change reaches. It must find several affected
duties where they exist (`AMD-02`), stop at one where only one is affected (`AMD-01`), and recognise when
nothing is affected (`AMD-03`). Over-flagging (for example flagging `OBL-02` for `AMD-01`) counts as a
failure.

## Sources

- Date conventions `D-2`, `D-4`, `D-5` and `D-7`: operator-provided domain guidance (Define phase). Not
  yet checked against the legal texts.

## Assumptions

- Conventions marked **Assumed** in section 5 (`D-1`, `D-3`, `D-6`) are PM proposals. They have not been
  confirmed by a compliance specialist.
- The mock holiday list matches the real 2027 Luxembourg public holidays as far as known. It is not
  taken from an official source.
- Expected values in this file assume the mock sources and fund profile are not changed. Any change to
  those files means this answer key must be recomputed.

## Open Questions

- **OQ-D2**: *Resolved.* "2 months after 30 June" is 31 August (operator-confirmed, now `D-2`).
- **OQ-D1**: *Resolved* (operator decision, 2026-11-11, decision log DL-19). The business-day rule for
  Luxembourg Business Registers filings (`OBL-05`) and CNMV filings (`OBL-04`) is never guessed: it
  stays "not confirmed" until the specialist sets one at G1, and `D-6` applies. The expected entries do
  not change.
- **OQ-D3**: Is the subscription tax return (`OBL-02`, AED) covered by the "tax deadlines do not roll"
  rule? The guidance named the ACD. The AED is a different authority. **Open** (kept open by the
  operator, decision log DL-20). The table above uses **no roll** (the safe choice) as the specialist's
  demo decision at G1, not as a built-in rule; the four `OBL-02` dates are the same under "roll forward".

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-mock-data` (answer key for demo evaluation) ·
  dates computed with a script, not by hand
- 2026-11-06 · persona `product-mgr` · action `update` · business-day rules and end-of-month convention
  applied from operator guidance; calendar recomputed by script
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · added Assumptions; marked OQ-D2 resolved;
  linked business-day rule from section 1 to section 5
- 2026-11-06 · persona `product-mgr` · action `update` · `OBL-04` added to the calendar (operator
  decision: applies, pending confirmation, per P-1); total 18 → 22 entries
- 2026-11-06 · persona `product-mgr` · action `quality-pass` (stories) · added internal-conflict test
  `I-1`; renamed the Spain note to "precautionary: registration unconfirmed"
- 2026-11-06 · persona `product-mgr` · action `update` · added section 6 (stretch: expected impact of
  amendments AMD-01 to AMD-03)
- 2026-11-11 · persona `product-mgr` · action `update` (DL-19) · OQ-D1 resolved: business-day rules for `OBL-04` and `OBL-05` are never guessed; expected results unchanged. OQ-D3 stays open (DL-20)
- 2026-11-11 · persona `product-mgr` · action `update` (DL-20) · OQ-D3 kept open; the no-roll table is the specialist's demo decision at G1, not a built-in rule; expected results unchanged
