"""The three agent functions (extractor, verifier, judge).

B3 step 4: extract_rows, check_conflicts and judge_applicability return the fixed stand-in answers
from backend/stand_in/, checked by the real guardrails. Since B3 step 5 the stage functions call
them (backend/runtime/stages.py). The CrewAI wiring is B3 step 7. Real mode is refused: no model
call before the first green path.

The stand-in pause (DL-54, B13a): each stand-in unit waits STAND_IN_UNIT_PAUSE_S seconds before
returning, so the units table fills in one row at a time. Real mode NEVER pauses (T-PAUSE-1).
"""

import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Callable

import yaml

from backend.domain import guardrails
from backend.domain.quote_check import QuoteCheck
from backend.domain.schemas import Flag, Row, Verdict
from backend.services.audit import now_utc
from backend.services.trace import CallRecord
from backend.settings import Settings

STAND_IN_DIR = Path(__file__).resolve().parent.parent / "stand_in"

# A stand-in call costs nothing (CR-030). Tests set this above 0 to try the cost cap (CR-017).
STAND_IN_COST_USD = 0.0

# `record` is how an agent function reports each call for the trace (B3 step 6). The stage passes
# one in; it writes the trace line, adds the cost and says whether the output came too late.
Recorder = Callable[[CallRecord], None]


class RealAgentsNotBuilt(Exception):
    """Real agents arrive with the B3 spike, after the first green path. Not in the shell."""


class InvalidOutput(Exception):
    """An agent's output failed its schema or guardrail. The unit fails with "invalid output"
    and the model is never asked again (D5). `error` is the guardrail's reason, for the trace."""

    def __init__(self, error: str):
        super().__init__(error)
        self.error = error


class MissingStandInOutput(Exception):
    """The stand-in files have no answer for this unit: a gap in backend/stand_in/, not a model
    failure. Raised loudly so a gap is fixed instead of hidden."""


def unit_pause(settings: Settings, sleep=None) -> None:
    """Wait the stand-in pause for one unit. Does nothing in real mode.

    `sleep` can be swapped in tests, so a test can see whether a pause happened without waiting.
    It defaults to None (not time.sleep) on purpose: a default is fixed when the file loads, so
    `sleep=time.sleep` would ignore a test that swaps time.sleep later.
    """
    if settings.agents_mode != "stand_in":
        return  # Real mode: never pause (and settings never read the variable).
    if settings.stand_in_unit_pause_s > 0:
        (sleep or time.sleep)(settings.stand_in_unit_pause_s)


# --- The three agent functions (sad.md §2: "a plain function with a typed input and output") ----
#
# Stand-in mode (CR-030): pause, read the fixed answer from backend/stand_in/, then put it through
# the SAME guardrail a real model's output will face, so a stand-in answer can never be something
# a real one could not be. Real mode: refused until the B3 spike (after the first green path);
# the CrewAI agents are wired behind these same functions in B3 step 7.


@lru_cache
def _stand_in(name: str) -> dict:
    """backend/stand_in/<name>.yaml, read once."""
    return yaml.safe_load((STAND_IN_DIR / f"{name}.yaml").read_text(encoding="utf-8"))


def _refuse_real_mode(settings: Settings) -> None:
    if settings.agents_mode != "stand_in":
        raise RealAgentsNotBuilt("AGENTS_MODE=real is not built yet (B3 spike, after green path)")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache
def _stand_in_version(name: str) -> str:
    """The trace's prompt_version for a stand-in call: a hash of the stand-in answer file, so a
    change to the fixed answers shows in the trace. B3 step 7 hashes agents.yaml and tasks.yaml."""
    return "stand-in:" + _sha256((STAND_IN_DIR / f"{name}.yaml").read_text(encoding="utf-8"))[:16]


def _stand_in_call(settings: Settings, *, step: str, name: str, inputs: dict, answer,
                   check: Callable[[object], guardrails.GuardrailResult],
                   record: Recorder | None):
    """One stand-in call: pause, check the fixed answer with the real guardrail, report the call
    for the trace (pass or fail), then return the parsed output or raise InvalidOutput."""
    at, started = now_utc(), time.monotonic()
    unit_pause(settings)
    result = check(answer)
    if record is not None:
        record(CallRecord(
            step=step, at=at, prompt_version=_stand_in_version(name),
            input_hash=_sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False, default=str)),
            raw_output=json.dumps(answer, ensure_ascii=False),
            parsed_output=guardrails.to_json(result), validation_error=result.error,
            duration_ms=int((time.monotonic() - started) * 1000), cost_usd=STAND_IN_COST_USD))
    if not result.ok:
        raise InvalidOutput(result.error)
    return result.parsed


def extract_rows(settings: Settings, *, document_id: str, paragraphs: dict[str, str],
                 recipient_codes: list[str], record: Recorder | None = None) -> list[Row]:
    """W-03: one primary document → its obligation rows. `paragraphs` is THIS document's only."""
    _refuse_real_mode(settings)
    answers = _stand_in("extractor")
    if document_id not in answers:
        raise MissingStandInOutput(f"No stand-in rows for {document_id}")
    return _stand_in_call(
        settings, step="extract_rows", name="extractor", record=record,
        inputs={"document_id": document_id, "paragraphs": paragraphs,
                "recipient_codes": recipient_codes},
        answer={"rows": answers[document_id]},
        check=lambda raw: guardrails.check_extraction(
            raw, document_id=document_id, paragraphs=paragraphs,
            recipient_codes=recipient_codes)).rows


def check_conflicts(settings: Settings, *, row: dict, quote_check: QuoteCheck,
                    sources: dict[str, str], record: Recorder | None = None) -> list[Flag]:
    """W-05, W-06: one row → its flags. `sources` is every loaded paragraph.

    `quote_check` is given for information only, as the card says: code decided it and nothing
    the verifier returns can change it (T-W04-6). A row the stand-in file does not list gets no
    flags, like a verifier that found nothing (the planted demo row, for example: SOQ-22).
    """
    _refuse_real_mode(settings)
    return _stand_in_call(
        settings, step="check_conflicts", name="verifier", record=record,
        inputs={"row": row, "quote_check": getattr(quote_check, "result", None),
                "sources": sources},
        answer={"flags": _stand_in("verifier").get(row["source_paragraph_id"], [])},
        check=lambda raw: guardrails.check_verification(
            raw, row_quote=row["quote"], paragraphs=sources)).flags


def judge_applicability(settings: Settings, *, row: dict, fund_facts: dict,
                        record: Recorder | None = None) -> Verdict:
    """W-11: one approved row + the fund's facts and events → one verdict."""
    _refuse_real_mode(settings)
    answers = _stand_in("judge")
    if row["source_paragraph_id"] not in answers:
        raise MissingStandInOutput(f"No stand-in verdict for {row['source_paragraph_id']}")
    input_ids = ({f["fact_id"] for f in fund_facts["facts"]}
                 | {e["event_id"] for e in fund_facts["events"]})
    # Everything the judge was given, so a date copied from its input is not refused (H-052).
    given_text = json.dumps({"row": row, **fund_facts}, ensure_ascii=False)
    return _stand_in_call(
        settings, step="judge_applicability", name="judge", record=record,
        inputs={"row": row, **fund_facts},
        answer=answers[row["source_paragraph_id"]],
        check=lambda raw: guardrails.check_verdict(
            raw, input_ids=input_ids, given_text=given_text))
