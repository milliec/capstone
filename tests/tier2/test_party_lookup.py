"""T-MAP-1 (EC-R11, DL-41): the responsible-role lookup. No model.

Tier 2 by the SAD, but it must pass before the first evaluation run (EC-R4, Build card).
(a) the five mappings, (b) text that does not map, (c) every target is a filing party,
(d) nothing in the app reads the lookup. The report half of (b) is in test_evaluation_stage_a.py.
"""

import re

import pytest

from backend.domain.schemas import NOT_STATED
from backend.evaluation import lookup
from backend.settings import ROOT

PROFILE = ROOT / "project-context/1.define/mock-data/mock-fund-profile.md"
BACKEND = ROOT / "backend"


@pytest.mark.parametrize("text,expected", [
    ("a local reporting agent", "Local reporting agent (Spain)"),
    ("Local reporting agent appointed by the undertaking", "Local reporting agent (Spain)"),
    ("The fund administrator", "Fund administrator"),
    ("  Fund   Administrator. ", "Fund administrator"),
    ("not stated in source", "not stated in source"),
])
def test_t_map_1_a_these_map_to_the_expected_names(text, expected):
    assert lookup.map_party(text) == expected


@pytest.mark.parametrize("text", [
    "the depositary", "administrator", "fund administrator (may transmit the report)",
    "Fund administrator or AIFM", "",
])
def test_t_map_1_b_these_give_no_match(text):
    assert lookup.map_party(text) is None


def test_the_normal_form_does_only_what_ec_r11_says():
    n = lookup.normalise_party
    assert n("  The   Auditor. ") == "auditor"
    assert n("An AIFM") == "aifm"
    assert n("the the auditor") == "the auditor"     # one leading article only
    assert n("auditor..") == "auditor."              # one full stop only
    assert n("theauditor") == "theauditor"           # no partial or fuzzy matching
    assert n("a") == "a"                             # an article needs a word after it


def _filing_parties() -> set[str]:
    parties = set()
    for line in PROFILE.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[1] == "Yes" and line.startswith("| ") and "Role" not in cells[0]:
            parties.add(cells[0])
    return parties


def test_t_map_1_c_every_target_is_a_filing_party_or_not_stated():
    filing = _filing_parties()
    assert filing, "the test must read real parties"
    assert {"AIFM", "Fund administrator", "Auditor", "Local reporting agent (Spain)",
            "Tax advisor"} <= filing
    for text, target in lookup.lookup_table().items():
        assert target in filing or target == NOT_STATED, (text, target)


def test_t_map_1_d_nothing_in_the_app_reads_or_imports_the_evaluation_package():
    """No module, template or config under backend/ outside backend/evaluation/ may name the
    lookup file or import the package. (The evaluation package may read the app: one way only.)"""
    pattern = re.compile(r"party_lookup|backend\.evaluation|from backend import evaluation")
    offenders = []
    for path in BACKEND.rglob("*"):
        if (not path.is_file() or "evaluation" in path.relative_to(BACKEND).parts
                or path.suffix not in {".py", ".html", ".yaml", ".yml", ".sql", ".css", ".js"}):
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
