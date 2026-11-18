"""The three task prompts: their inputs, how they are filled in, and their version (B3 step 7a).

Plain code, no model and no CrewAI. It reads backend/config/agents.yaml, tasks.yaml and
examples/, and:
  - builds each task's inputs from stored data only (sad.md "Context strategy": the minimum a step
    needs; never the answer key, the mock files' notes or the "Decides" column, CR-016);
  - fills a task's {placeholders} the way CrewAI does, refusing a missing or unknown input, so a
    prompt can be rendered and checked in tests with no model (T-PROMPT-1, T-LEAK-1);
  - gives each step's prompt version: a hash of its agent, task and example text, recorded in the
    trace (CR-018). A change to any of them is a release (sad.md "Swap-as-release rule").
The CrewAI crews that send these prompts to a model come in B3 step 7b.
"""

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
EXAMPLES_DIR = CONFIG_DIR / "examples"

STEPS = ("extract_rows", "check_conflicts", "judge_applicability")

# A placeholder is {lower_case_name}. Nothing else in the task text may use braces.
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")

# The row fields the verifier and the judge see (sad.md "Context strategy").
_ROW_FIELDS = ("obligation_name", "frequency", "anchor", "offset", "recipient_code",
               "responsible_role", "applicability_rule", "business_day_rule",
               "source_paragraph_id", "quote")


class PromptError(Exception):
    """A task could not be filled in: an input is missing, unknown, or the text has a stray brace."""


@lru_cache
def load_agents() -> dict:
    return yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text(encoding="utf-8"))


@lru_cache
def load_tasks() -> dict:
    return yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text(encoding="utf-8"))


@lru_cache
def example(step: str) -> str:
    """The step's one-shot example, passed in as the {example} input (DL-39 item 6)."""
    return (EXAMPLES_DIR / f"{step}.txt").read_text(encoding="utf-8").strip()


def placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER.findall(text))


def fill(text: str, inputs: dict[str, str]) -> str:
    """Replace each {name} with its input, in one pass, as CrewAI's interpolation does.

    Refuses a placeholder with no input, an input the text does not use, and any brace left that
    is not a placeholder: each would mean a broken or changed prompt (T-PROMPT-1). One pass means
    braces INSIDE an input (the example's JSON) are never read as placeholders.
    """
    wanted = placeholders(text)
    missing, unused = wanted - set(inputs), set(inputs) - wanted
    if missing or unused:
        raise PromptError(f"missing inputs {sorted(missing)}, unused inputs {sorted(unused)}")
    if re.search(r"[{}]", _PLACEHOLDER.sub("", text)):
        raise PromptError("the task text has a brace that is not a placeholder")
    return _PLACEHOLDER.sub(lambda m: str(inputs[m.group(1)]), text)


def render(step: str, inputs: dict[str, str]) -> dict[str, str]:
    """The step's agent text and filled-in task: {role, goal, backstory, description,
    expected_output}. `inputs` excludes `example`, which is always added here."""
    task = load_tasks()[step]
    agent = load_agents()[task["agent"]]
    full = {**inputs, "example": example(step)}
    texts = {"description": task["description"], "expected_output": task["expected_output"]}
    unused = set(full) - set().union(*(placeholders(t) for t in texts.values()))
    if unused:
        raise PromptError(f"unused inputs {sorted(unused)}")
    # Each text gets the inputs it names; `fill` refuses any it names but was not given.
    filled = {name: fill(text, {k: full[k] for k in placeholders(text) if k in full})
              for name, text in texts.items()}
    return {"role": agent["role"].strip(), "goal": agent["goal"].strip(),
            "backstory": agent["backstory"].strip(), **filled}


def prompt_version(step: str) -> str:
    """Hash of the step's agent, task and example text: the trace's prompt_version (CR-018)."""
    task = load_tasks()[step]
    agent = load_agents()[task["agent"]]
    content = json.dumps({"agent": agent, "task": task, "example": example(step)},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# --- Inputs, built by code from stored data (sad.md "Context strategy") ----------------------

def _paragraph_lines(paragraphs: dict[str, str], types: dict[str, str] | None = None) -> str:
    """One paragraph per line, starting with its ID (and its document type for the verifier)."""
    lines = []
    for pid, text in paragraphs.items():
        kind = f" ({types[pid]})" if types else ""
        lines.append(f"{pid}{kind} " + " ".join(text.split()))
    return "\n".join(lines)


def extractor_inputs(*, document_id: str, document_title: str, paragraphs: dict[str, str],
                     recipient_codes: list[str]) -> dict[str, str]:
    """W-03: ONE primary document's paragraphs (this document's only) and the allowed codes."""
    return {"document_id": document_id, "document_title": document_title,
            "paragraphs": _paragraph_lines(paragraphs),
            "recipient_codes": ", ".join(recipient_codes)}


def _row_text(row: dict) -> str:
    return json.dumps({k: row[k] for k in _ROW_FIELDS if k in row}, ensure_ascii=False,
                      indent=1, default=str)


def verifier_inputs(*, row: dict, quote_check_passed: bool, sources: dict[str, str],
                    document_types: dict[str, str]) -> dict[str, str]:
    """W-05, W-06: the row and its quote, the code's quote-check result, the cited paragraph, and
    every loaded paragraph with its ID and document type. Never the extractor's reasoning, other
    rows' flags or gate state."""
    types = {pid: document_types[pid.rsplit("-P", 1)[0]] for pid in sources}
    cited = row["source_paragraph_id"]
    return {"row_fields_and_quote": _row_text(row),
            "quote_check_result": "passed" if quote_check_passed else "failed",
            "cited_paragraph": f"{cited} " + " ".join(sources.get(cited, "").split()),
            "all_paragraphs_with_ids_and_document_type": _paragraph_lines(sources, types)}


def judge_inputs(*, row: dict, fund_facts: dict) -> dict[str, str]:
    """W-11: the row as approved, the facts as ID, fact and value only, the events as ID and
    description. Never the "Decides" column, flags, G1 reasons or other verdicts."""
    facts = "\n".join(f"{f['fact_id']} {f['fact']}: {f['value']}" for f in fund_facts["facts"])
    events = "\n".join(f"{e['event_id']} {e['event']}" for e in fund_facts["events"]) or "none"
    return {"approved_row": _row_text(row), "fund_facts": facts, "event_log": events}
