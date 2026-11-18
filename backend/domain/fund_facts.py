"""The fund facts loader (W-10): the mock fund profile → the facts and events the judge reads.

Plain code, no model. Like the source loader, it must not let the answers through (CR-016,
DL-39, T-LEAK-1). The mock profile's facts table has a "Decides" column that says which rule each
fact settles, and what the right verdict is ("→ unsure", "→ does not apply"). The judge gets only:
  - each fact as {fact_id, fact, value}, and
  - each event as {event_id, event} (ID and description; the dates are for the date engine, B4).
Markdown bold (**Yes**) is removed from values. Blockquotes (test notes) are never read.
"""

from functools import lru_cache

from backend.services.fund import load_fund
from backend.settings import ROOT

_FACTS_HEADING = "## Applicability facts"
_EVENTS_HEADING = "## Event log"


def _table_rows(markdown: str, heading: str) -> list[list[str]]:
    """The body rows of the first table under `heading`, as lists of cell text.

    Stops at the next heading. Skips the header row and the |---| line. Blockquotes and text
    around the table are ignored.
    """
    lines = markdown.splitlines()
    # startswith: the event heading carries a note, "## Event log (for event-triggered …)".
    start = next(i for i, line in enumerate(lines) if line.startswith(heading))
    rows = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows[2:]  # drop the header row and the |---| separator


def _clean(cell: str) -> str:
    """`FACT-01` → FACT-01; **Yes** → Yes."""
    return cell.replace("`", "").replace("**", "").strip()


@lru_cache
def load_fund_facts(fund_id: str = "FND-DEMO-01") -> dict:
    """{"facts": [{fact_id, fact, value}], "events": [{event_id, event}]} for the judge."""
    markdown = (ROOT / load_fund(fund_id)["profile_file"]).read_text(encoding="utf-8")
    # Facts table columns: Fact ID | Fact | Value | Decides. Only the first three are read.
    facts = [{"fact_id": _clean(r[0]), "fact": _clean(r[1]), "value": _clean(r[2])}
             for r in _table_rows(markdown, _FACTS_HEADING)]
    # Event table columns: Event ID | Event | dates … | Obligation. Only the first two are read.
    events = [{"event_id": _clean(r[0]), "event": _clean(r[1])}
              for r in _table_rows(markdown, _EVENTS_HEADING)]
    return {"facts": facts, "events": events}
