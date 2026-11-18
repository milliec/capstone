"""The source loader (W-02): the mock regulatory sources → paragraphs with stable IDs.

Plain code, no model (sad.md §4: the domain code has no model client).

Why this needs care (CR-016, DL-39, T-LEAK-1): the mock sources file carries the ANSWERS next to the
text: "Test note" blockquotes, "Planted conflict" notes, a header warning and a list of amendments.
Anything the loader returns can end up in a prompt, so it keeps ONLY:
  - the paragraph ID (a line like **SRC-UCILAW-P2**), and
  - the plain text lines straight under it, up to the next blank line.
Every blockquote line (starting with ">"), every heading and every table is dropped, and reading
stops at the "Amendments" heading (the amendments are a stretch goal, never part of a run).

The list of documents (ID, title, primary or secondary) comes from config/regulation/lu-part2.yaml,
not from the mock file, so a paragraph whose document is not listed there is never loaded.
"""

import re
from functools import lru_cache

import yaml

from backend.settings import ROOT

REGULATION_CONFIG = ROOT / "config" / "regulation" / "lu-part2.yaml"

# A paragraph ID line in the mock file: **SRC-UCILAW-P2** and nothing else on the line.
_PARAGRAPH_ID_LINE = re.compile(r"^\*\*(SRC-[A-Z0-9]+-P\d+)\*\*$")

# Reading stops at this heading: everything below it is the stretch goal's amendments.
_STOP_HEADING = "## Amendments"


class SourceFileError(Exception):
    """The mock sources file does not match the config (a missing or unexpected paragraph)."""


@lru_cache
def load_regulation_config() -> dict:
    """Read config/regulation/lu-part2.yaml once (a run reads its configuration when it starts)."""
    return yaml.safe_load(REGULATION_CONFIG.read_text(encoding="utf-8"))


def list_documents() -> list[dict]:
    """The source documents in run order: [{id, title, type}], type is 'primary' or 'secondary'."""
    return [dict(d) for d in load_regulation_config()["documents"]]


def list_recipients() -> dict[str, str]:
    """The allowed recipient codes and their display names: {code: name} (DL-53)."""
    return {r["code"]: r["name"] for r in load_regulation_config()["recipients"]}


def _document_id(paragraph_id: str) -> str:
    """SRC-UCILAW-P2 → SRC-UCILAW."""
    return paragraph_id.rsplit("-P", 1)[0]


def parse_paragraphs(markdown: str) -> list[dict]:
    """Pull the paragraphs out of the mock sources file's text.

    Returns [{paragraph_id, document_id, text}] in file order. `text` keeps the file's own line
    breaks; the quote check (QN-1) is what collapses whitespace, so nothing is lost here.
    """
    paragraphs = []
    current_id = None  # the paragraph we are collecting lines for, or None
    lines: list[str] = []

    def finish():
        if current_id is not None and lines:
            paragraphs.append({"paragraph_id": current_id,
                               "document_id": _document_id(current_id),
                               "text": "\n".join(lines)})

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith(_STOP_HEADING):
            break  # amendments: never loaded
        match = _PARAGRAPH_ID_LINE.match(line.strip())
        if match:
            finish()
            current_id, lines = match.group(1), []
            continue
        if current_id is None:
            continue  # header warning, tables, headings before the first paragraph
        if not line.strip():
            if lines:  # a blank line ends the paragraph's text
                finish()
                current_id, lines = None, []
            continue
        if line.lstrip().startswith((">", "#", "|", "---")):
            # A note, heading, table or rule: never paragraph text. It also ends the paragraph,
            # so text after a note can never be glued onto the paragraph above it.
            finish()
            current_id, lines = None, []
            continue
        lines.append(line.strip())
    finish()
    return paragraphs


def load_paragraphs() -> list[dict]:
    """The paragraphs of every configured document, in config order then file order.

    Refuses (SourceFileError) if a configured document has no paragraph, or if the file holds a
    paragraph whose document is not configured, so a mistake in either file is caught at once
    instead of silently giving the agents less, or more, than intended.
    """
    config = load_regulation_config()
    markdown = (ROOT / config["sources_file"]).read_text(encoding="utf-8")
    parsed = parse_paragraphs(markdown)

    order = [d["id"] for d in config["documents"]]
    unexpected = sorted({p["document_id"] for p in parsed} - set(order))
    if unexpected:
        raise SourceFileError(f"Paragraphs for documents not in the config: {unexpected}")
    missing = [doc for doc in order if not any(p["document_id"] == doc for p in parsed)]
    if missing:
        raise SourceFileError(f"Configured documents with no paragraph: {missing}")

    return sorted(parsed, key=lambda p: order.index(p["document_id"]))  # stable: keeps P1, P2, …
