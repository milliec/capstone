"""The three agent functions (extractor, verifier, judge).

B3 step 4: extract_rows, check_conflicts and judge_applicability return the fixed stand-in answers
from backend/stand_in/, checked by the real guardrails. Since B3 step 5 the stage functions call
them (backend/runtime/stages.py). Since B3 step 7b PR 4, real mode (AGENTS_MODE=real) sends the
unit to a CrewAI crew (backend/runtime/crews.py) and puts the model's answer through the SAME
guardrail. A real call needs a model ID and the key in .env: with either missing it is refused
before any request. Real mode is not meant to run until PR 5 (the one retry, one trace line per
attempt) and the operator's spike.

The stand-in pause (DL-54, B13a): each stand-in unit waits STAND_IN_UNIT_PAUSE_S seconds before
returning, so the units table fills in one row at a time. Real mode NEVER pauses (T-PAUSE-1).
"""

import hashlib
import json
import time
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import yaml

from backend.domain import guardrails
from backend.domain import sources as source_files
from backend.domain.quote_check import QuoteCheck
from backend.domain.schemas import Flag, Row, Verdict
from backend.runtime import crews, model_settings, prompts
from backend.services.audit import now_utc
from backend.services.trace import CallRecord
from backend.settings import Settings

STAND_IN_DIR = Path(__file__).resolve().parent.parent / "stand_in"

# A stand-in call costs nothing (CR-030). Tests set this above 0 to try the cost cap (CR-017).
STAND_IN_COST_USD = 0.0

# `record` is how an agent function reports each call for the trace (B3 step 6). The stage passes
# one in; it writes the trace line, adds the cost and says whether the output came too late.
Recorder = Callable[[CallRecord], None]


# A provider failure (no answer). Defined with the crews; named here because the stage catches the
# agent functions' failures as `agents.<Name>`.
ModelServiceError = crews.ModelServiceError


class InvalidOutput(Exception):
    """An agent's output failed its schema or guardrail. The unit fails with "invalid output"
    and the model is never asked again (D5). `error` is the guardrail's reason, for the trace."""

    def __init__(self, error: str):
        super().__init__(error)
        self.error = error


class MissingStandInOutput(Exception):
    """The stand-in files have no answer for this unit: a gap in backend/stand_in/, not a model
    failure. Raised loudly so a gap is fixed instead of hidden."""


class DemoFailure(Exception):
    """The failure demo (DL-52, CR-033, rule 11): the stand-in extractor fails on purpose. The unit
    fails with the reason "demo failure". It is never raised in real mode (asking for it there is refused: DemoFailureRefused)."""


class DemoFailureRefused(Exception):
    """The failure demo was asked for in real mode. It is stand-in only: never with real agents."""


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


def _ready(settings: Settings, step: str) -> None:
    """Refuse a real call with no model ID or no key, FIRST: before any input is built or sent."""
    model_settings.role_settings(settings, model_settings.STEP_ROLE[step])
    model_settings.require_api_key(settings)


def _real_call(settings: Settings, *, step: str, inputs: dict[str, str], hash_inputs: dict,
               check: Callable[[object], guardrails.GuardrailResult], record: Recorder | None):
    """One real call (AGENTS_MODE=real): send the unit to its crew once, put the answer through the
    SAME guardrail as a stand-in answer, report the call for the trace, then return the parsed
    output or raise InvalidOutput. A provider failure raises ModelServiceError (no trace line:
    PR 5 writes one per attempt). The model is never asked again (D5)."""
    role = model_settings.STEP_ROLE[step]
    call = model_settings.role_settings(settings, role)     # no model ID: refused, nothing sent
    at, started = now_utc(), time.monotonic()
    result = crews.run_step(settings, step, inputs)         # may raise ModelServiceError
    try:
        answer = json.loads(result.text)
        checked = check(answer)
    except json.JSONDecodeError as error:
        checked = guardrails.GuardrailResult(ok=False, error=f"The answer is not valid JSON: {error}")
    if record is not None:
        record(CallRecord(
            step=step, at=at, prompt_version=prompts.prompt_version(step),
            input_hash=_sha256(json.dumps(hash_inputs, sort_keys=True, ensure_ascii=False,
                                          default=str)),
            raw_output=result.text, parsed_output=guardrails.to_json(checked),
            validation_error=checked.error, duration_ms=int((time.monotonic() - started) * 1000),
            model=call.model, settings_json=call.logged(), max_tokens=call.max_completion_tokens,
            tokens_in=result.tokens_in, tokens_out=result.tokens_out,
            cost_usd=model_settings.call_cost_usd(role, result.tokens_in, result.tokens_out)))
    if not checked.ok:
        raise InvalidOutput(checked.error)
    return checked.parsed


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@lru_cache
def _stand_in_version(step: str, name: str) -> str:
    """The trace's prompt_version for a stand-in call (B3 step 7a): the prompt version a real
    call would use (a hash of the agent, task and example, backend/runtime/prompts.py), then
    "+stand-in:" and a hash of the answer file that stood in for the model. A change to either
    shows in the trace (CR-018)."""
    answers = _sha256((STAND_IN_DIR / f"{name}.yaml").read_text(encoding="utf-8"))[:8]
    return f"{prompts.prompt_version(step)}+stand-in:{answers}"


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
            step=step, at=at, prompt_version=_stand_in_version(step, name),
            input_hash=_sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False, default=str)),
            raw_output=json.dumps(answer, ensure_ascii=False),
            parsed_output=guardrails.to_json(result), validation_error=result.error,
            duration_ms=int((time.monotonic() - started) * 1000), cost_usd=STAND_IN_COST_USD))
    if not result.ok:
        raise InvalidOutput(result.error)
    return result.parsed


def extract_rows(settings: Settings, *, document_id: str, paragraphs: dict[str, str],
                 recipient_codes: list[str], record: Recorder | None = None,
                 demo_fail: bool = False) -> list[Row]:
    """W-03: one primary document → its obligation rows. `paragraphs` is THIS document's only.

    `demo_fail` is the stand-in extractor hook for the failure demo (B13a, CR-033): the stage
    sets it for stage A's first unit on the first stage attempt when the run's switch is on. The
    unit pauses like any stand-in unit (so it shows "running" for a moment), then fails. No output
    is produced, so no trace line is written. Real mode never gets here (refused first).
    """
    if demo_fail:
        if settings.agents_mode != "stand_in":
            raise DemoFailureRefused("The failure demo is stand-in only (DL-52, CR-033)")
        unit_pause(settings)
        raise DemoFailure(f"Failure demo: {document_id} fails on purpose")
    if settings.agents_mode == "real":
        _ready(settings, "extract_rows")
        title = next(d["title"] for d in source_files.list_documents() if d["id"] == document_id)
        return _real_call(
            settings, step="extract_rows", record=record,
            inputs=prompts.extractor_inputs(document_id=document_id, document_title=title,
                                            paragraphs=paragraphs, recipient_codes=recipient_codes),
            hash_inputs={"document_id": document_id, "paragraphs": paragraphs,
                         "recipient_codes": recipient_codes},
            check=lambda raw: guardrails.check_extraction(
                raw, document_id=document_id, paragraphs=paragraphs,
                recipient_codes=recipient_codes)).rows
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
    if settings.agents_mode == "real":
        _ready(settings, "check_conflicts")
        types = {d["id"]: d["type"] for d in source_files.list_documents()}
        return _real_call(
            settings, step="check_conflicts", record=record,
            inputs=prompts.verifier_inputs(row=row, quote_check_passed=bool(quote_check.passed),
                                           sources=sources, document_types=types),
            hash_inputs={"row": row, "quote_check": getattr(quote_check, "result", None),
                         "sources": sources},
            check=lambda raw: guardrails.check_verification(
                raw, row_quote=row["quote"], paragraphs=sources)).flags
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
    if settings.agents_mode == "real":
        _ready(settings, "judge_applicability")
        input_ids = ({f["fact_id"] for f in fund_facts["facts"]}
                     | {e["event_id"] for e in fund_facts["events"]})
        given_text = json.dumps({"row": row, **fund_facts}, ensure_ascii=False)
        return _real_call(
            settings, step="judge_applicability", record=record,
            inputs=prompts.judge_inputs(row=row, fund_facts=fund_facts),
            hash_inputs={"row": row, **fund_facts},
            check=lambda raw: guardrails.check_verdict(
                raw, input_ids=input_ids, given_text=given_text))
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
