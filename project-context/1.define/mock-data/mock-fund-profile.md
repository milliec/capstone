# Mock Fund Profile

> ⚠️ **FICTIONAL FUND.** The name, people, dates and facts below are invented for this capstone. Any
> resemblance to a real fund or firm is unintended. Service providers are described by **role only**.

## Identity

| Field | Value |
|---|---|
| Fund ID | `FND-DEMO-01` |
| Fund name | Bramblegate Credit Opportunities SICAV *(fictional)* |
| GP / fund manager | Bramblegate Partners *(fictional)* |
| Legal regime | Luxembourg UCI subject to Part II of the Law of 17 December 2010 |
| Legal form | Investment company with variable capital (SICAV) |
| Domicile | Luxembourg |
| Liquidity profile | Semi-liquid, open-ended (monthly dealing) |
| Financial year-end | 31 December |
| First financial year-end | 31 December 2026 |

## Applicability facts

These are the facts the applicability agent should use. Each one is tagged with the obligation it
decides.

| Fact ID | Fact | Value | Decides |
|---|---|---|---|
| `FACT-01` | Subject to Part II of the Law of 17 December 2010 | **Yes** | U1.1 monthly report, annual report |
| `FACT-02` | Established in Luxembourg | **Yes** | Subscription tax (taxe d'abonnement), RBE |
| `FACT-03` | Countries where marketed | Luxembourg, Germany, Spain | Spain A01 |
| `FACT-04` | Registered with the CNMV for marketing in Spain | **Unknown — not confirmed in fund records** | Spain A01 → **unsure** |
| `FACT-05` | Registered for VAT in Luxembourg | **No** | VAT annual return → **does not apply** |
| `FACT-06` | Registered entity with the Luxembourg Business Registers | **Yes** | RBE |
| `FACT-07` | Redemption frequency in constitutive documents | **Monthly** | Stretch only: re-check after amendment `AMD-02` |

## Parties (roles only)

| Role | Notes |
|---|---|
| Compliance specialist | Owns the obligation calendar. Approves, edits or rejects every agent output. |
| GP | Read-only view of the calendar. |
| AIFM | Files RBE updates. |
| Fund administrator | Files U1.1 and the subscription tax return. |
| Auditor | Audits the annual report. |
| Local reporting agent (Spain) | Would file A01 if it applies. |

## Event log (for event-triggered obligations)

| Event ID | Event | Date the change happened | Date the fund became aware | Obligation |
|---|---|---|---|---|
| `EVT-01` | A new investor's holding crossed the 25% beneficial-ownership threshold | 2027-01-20 | 2027-01-31 | RBE update |

> *Test note: the due date must be calculated from the **awareness** date (2027-01-31), not the event
> date (2027-01-20). See `SRC-RBELAW-P1`.*

## Demo calendar horizon

The demo calendar covers obligations whose **due date falls between 2027-01-01 and 2027-12-31**.

---

## Sources

- Fund facts: invented for this capstone. Chosen so that the six obligation rows produce all three
  verdicts: applies, does not apply and unsure (operator decision during Define).
- Fund name: chosen by the operator from a shortlist of invented names.

## Assumptions

- A single financial year-end (31 December) and one event are enough to test every anchor type in the
  demo.
- The fund's name is not used by a real fund or firm. **Not checked with a web search.**

## Open Questions

- None for this file.

## Audit

- 2026-11-06 · persona `product-mgr` · action `create-mock-data` · fictional fund profile
- 2026-11-06 · persona `product-mgr` · action `quality-pass` · renamed the fund to Bramblegate; added
  required sections
- 2026-11-06 · persona `product-mgr` · action `update` · added `FACT-07` (redemption frequency) for the
  change-monitoring stretch goal
