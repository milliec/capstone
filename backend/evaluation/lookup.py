"""The responsible-role lookup (EC-R11, DL-41): the extractor's free text → a party name.

Normalise, look up in the fixed table (party_lookup.yaml), and that is all. No spelling correction,
no partial or fuzzy match, no model. Text that does not map gives None: a miss on EC-001 for that
row, and the report shows the text.
"""

import re
from functools import lru_cache
from pathlib import Path

import yaml

LOOKUP_FILE = Path(__file__).resolve().parent / "party_lookup.yaml"

_SPACES = re.compile(r" +")
_LEADING_ARTICLE = re.compile(r"^(?:a|an|the) ")


def normalise_party(text: str) -> str:
    """EC-R11 point 1, in the SAD's order: lower case; trim; collapse runs of spaces; remove one
    leading "a", "an" or "the"; remove one trailing full stop. Nothing else."""
    text = _SPACES.sub(" ", text.lower().strip())
    text = _LEADING_ARTICLE.sub("", text, count=1)
    return text.removesuffix(".")


@lru_cache
def lookup_table() -> dict[str, str]:
    """{normalised text: party name}, read once."""
    return yaml.safe_load(LOOKUP_FILE.read_text(encoding="utf-8"))


def map_party(text: str) -> str | None:
    """The party name for the extractor's text, or None ("no match") when the table has no entry."""
    return lookup_table().get(normalise_party(text))
