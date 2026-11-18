"""T-PROMPT-1 and T-EXAMPLE-1 (DL-39, Tier 2). No model, no CrewAI.

T-PROMPT-1: every task renders with sample inputs, with no missing or left-over placeholder.
T-EXAMPLE-1: the one-shot examples are invented. No example quote (normalised as QN-1 steps 1-2,
compared without case) appears in the mock sources (amendments included), the planted-row
fixture, or the answer key (whose quotes the evaluation copy cases are made from); no example
paragraph shares six or more consecutive words with them; and no example uses a mock-data ID.
"""

import json
import re

import pytest

from backend.domain.quote_check import normalise
from backend.runtime import prompts
from backend.settings import ROOT

MOCK = ROOT / "project-context/1.define/mock-data"
# The planted-row fixture: the temporary demo rule until B7 writes config/demo/planted-row.yaml.
PLANTED = ROOT / "backend/stand_in/demo_row_temporary.yaml"

SAMPLE_INPUTS = {
    "extract_rows": {"document_id": "SRC-X", "document_title": "A title",
                     "paragraphs": "SRC-X-P1 Some text.", "recipient_codes": "AAA"},
    "check_conflicts": {"row_fields_and_quote": "row", "quote_check_result": "passed",
                        "cited_paragraph": "SRC-X-P1 Some text.",
                        "all_paragraphs_with_ids_and_document_type": "SRC-X-P1 (primary) Text."},
    "judge_applicability": {"approved_row": "row", "fund_facts": "FACT-X1 A fact: Yes",
                            "event_log": "none"},
}


# --- T-PROMPT-1 ----------------------------------------------------------------------------

@pytest.mark.parametrize("step", prompts.STEPS)
def test_prompt_1_every_task_renders_with_nothing_missing_or_left_over(step):
    rendered = prompts.render(step, SAMPLE_INPUTS[step])
    for name in ("description", "expected_output"):
        assert not prompts.placeholders(rendered[name]) - {"rows", "flags"}, (step, name)
    assert "<example>" in rendered["description"] and prompts.example(step) in rendered["description"]
    assert rendered["role"] and rendered["goal"] and rendered["backstory"]


def test_prompt_1_the_example_json_braces_are_never_read_as_placeholders():
    """The example is passed in as an input, so the braces of its JSON stay as they are."""
    rendered = prompts.render("extract_rows", SAMPLE_INPUTS["extract_rows"])
    assert '{"rows": [{' in rendered["description"]


def test_prompt_1_a_missing_unused_or_stray_input_is_refused():
    with pytest.raises(prompts.PromptError, match="missing"):
        prompts.render("extract_rows", {k: v for k, v in SAMPLE_INPUTS["extract_rows"].items()
                                        if k != "paragraphs"})
    with pytest.raises(prompts.PromptError, match="unused"):
        prompts.render("extract_rows", {**SAMPLE_INPUTS["extract_rows"], "answer_key": "x"})
    with pytest.raises(prompts.PromptError, match="brace"):
        prompts.fill("Text {name} and a stray } brace", {"name": "x"})


def test_each_step_has_its_own_prompt_version():
    versions = {prompts.prompt_version(step) for step in prompts.STEPS}
    assert len(versions) == 3 and all(re.fullmatch(r"[0-9a-f]{16}", v) for v in versions)


# --- T-EXAMPLE-1 ---------------------------------------------------------------------------

def _haystacks() -> list[str]:
    texts = [(MOCK / name).read_text(encoding="utf-8") for name in (
        "mock-regulatory-sources.md", "expected-obligation-library.md", "mock-fund-profile.md")]
    return texts + [PLANTED.read_text(encoding="utf-8")]


def _example_answer(step: str) -> dict:
    return json.loads(prompts.example(step).split("Answer:", 1)[1].split("\nWhy:", 1)[0])


def _example_quotes() -> list[str]:
    rows = _example_answer("extract_rows")["rows"]
    flags = _example_answer("check_conflicts")["flags"]
    return ([r["quote"] for r in rows]
            + [f[k] for f in flags for k in ("quote_says", "other_quote") if f.get(k)])


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _six_grams(text: str) -> set[tuple]:
    w = _words(text)
    return {tuple(w[i:i + 6]) for i in range(len(w) - 5)}


def _example_paragraphs() -> list[str]:
    """The example's own source text: the lines that start with an invented ID."""
    return [line for step in prompts.STEPS for line in prompts.example(step).splitlines()
            if re.match(r"(SRC-SAMPLE|SRC-ANNEX|FACT-S)\S*", line)]


def test_example_1_no_example_quote_appears_in_the_mock_data_or_the_answer_key():
    quotes = _example_quotes()
    assert len(quotes) == 2
    hay = [normalise(t).lower() for t in _haystacks()]
    for q in quotes:
        assert not any(normalise(q).lower() in h for h in hay), q


def test_example_1_no_example_paragraph_shares_six_words_in_a_row():
    paragraphs = _example_paragraphs()
    assert len(paragraphs) == 8       # extractor 2; verifier 3 (the sample again, 2 annex); judge 3
    hay = set().union(*(_six_grams(t) for t in _haystacks()))
    for paragraph in paragraphs:
        shared = _six_grams(paragraph) & hay
        assert not shared, (paragraph, sorted(shared)[:3])


def test_example_1_no_example_uses_a_mock_data_id():
    text = "\n".join(prompts.example(step) for step in prompts.STEPS)
    assert not re.search(r"SRC-(CSSF15627|UCILAW|CNMV|RBELAW|VATLAW|PRACT)|FACT-0\d|EVT-|OBL-",
                         text)
