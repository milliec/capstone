"""The CrewAI crews behind the three agent functions (B3 step 7b, PR 4).

One crew per unit, one agent, one task, one `kickoff`, built from the step's rendered prompt
(backend/runtime/prompts.py) and the role's settings (backend/runtime/model_settings.py). Every
setting below is one the SAD fixes (sad.md §2 "CrewAI settings", D1 to D6, H-065):

  agent  : no delegation, no memory, no tools, `max_iter` 1, `max_retry_limit` 0. CrewAI's own
           default retry limit is 2: left alone, ONE failing call becomes THREE requests (checked
           against the fake OpenAI, tests/tier1/test_crews.py).
  task   : no `output_pydantic` (when the answer does not parse, CrewAI would call the model
           again to repair it) and no `Task.guardrail` (our guardrails run in our code after the
           call). `guardrail_max_retries` 0, set explicitly so the library's default of 3 can
           never apply.
  crew   : sequential, `max_rpm` 30, no memory.
  client : the OpenAI client's own retries off (`max_retries` 0), its timeout a few seconds below
           the call's (DL-43), `max_completion_tokens` and the sampling settings from DL-40.
           The answer's shape goes as a strict `response_format` (backend/runtime/wire_schema.py).

What is NOT here, and arrives in PR 5: the one DL-43 retry around a call, and one trace line per
HTTP attempt through CrewAI's `interceptor` (including CrewAI's silent repeat without
`reasoning_effort`). Until then a call that fails is ONE attempt, and the numbers on a trace line
come from CrewAI's own usage count, not from each request.

CrewAI is loaded only here, only when a real call is made, and only through `load_crewai()` (which
switches its telemetry, tracing and version check off first). A stand-in run never gets here
(T-MODE-1).
"""

from dataclasses import dataclass

from backend.domain.schemas import ExtractionResult, Verdict, VerificationResult
from backend.runtime import model_settings, prompts
from backend.runtime.crewai_setup import load_crewai
from backend.runtime.wire_schema import wire_schema
from backend.settings import Settings

# The class that checks each step's answer, and whose schema is sent to the provider.
STEP_RESULT = {"extract_rows": ExtractionResult, "check_conflicts": VerificationResult,
               "judge_applicability": Verdict}

MAX_RPM = 30           # sad.md §2: limits bursts from the parallel units


class ModelServiceError(Exception):
    """The provider did not give an answer: it timed out, was rate-limited, returned an error, or
    could not be reached. The unit fails with the reason "model service" (DL-43)."""


@dataclass
class StepResult:
    """What one real call gave back: the model's text and the token counts CrewAI reports."""
    text: str
    tokens_in: int
    tokens_out: int


def build_crew(settings: Settings, step: str, inputs: dict[str, str]):
    """The one-agent, one-task crew for one unit. Builds only; sends nothing."""
    load_crewai()                                                    # switches first, then imports
    from crewai import LLM, Agent, Crew, Process, Task

    role = model_settings.STEP_ROLE[step]
    call = model_settings.role_settings(settings, role)              # refuses a role with no model ID
    model_settings.require_api_key(settings)
    card = prompts.load_agents()[prompts.load_tasks()[step]["agent"]]
    text = prompts.render(step, inputs)

    llm_args = {"model": f"openai/{call.model}", "api_key": settings.openai_api_key,
                "max_retries": 0, "timeout": call.http_timeout_s,
                "max_completion_tokens": call.max_completion_tokens,
                "reasoning_effort": call.reasoning_effort,
                # Sent through `additional_params`, not `response_format=`: see wire_schema.py.
                "additional_params": {"response_format": wire_schema(STEP_RESULT[step])}}
    if call.temperature is not None:
        llm_args["temperature"] = call.temperature

    agent = Agent(role=text["role"], goal=text["goal"], backstory=text["backstory"],
                  llm=LLM(**llm_args), tools=[], allow_delegation=card["allow_delegation"],
                  memory=card["memory"], max_iter=card["max_iter"], max_retry_limit=0,
                  verbose=False)
    task = Task(description=text["description"], expected_output=text["expected_output"],
                agent=agent, guardrail_max_retries=0)
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, max_rpm=MAX_RPM,
                memory=False, verbose=False)


def run_step(settings: Settings, step: str, inputs: dict[str, str]) -> StepResult:
    """Send one unit's prompt to the model once and return its text. Provider failures (a timeout,
    a rate limit, a server or client error, no connection) become `ModelServiceError`."""
    crew = build_crew(settings, step, inputs)
    try:
        output = crew.kickoff()
    except Exception as error:                  # CrewAI wraps some provider errors; all are one thing
        raise ModelServiceError(f"{type(error).__name__}: {error}") from error
    usage = output.token_usage
    return StepResult(text=output.raw or "", tokens_in=usage.prompt_tokens,
                      tokens_out=usage.completion_tokens)
