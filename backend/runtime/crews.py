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

The one DL-43 retry is here (PR 5, step 2): a call that fails with a timeout, no connection, a
rate limit or a server error is sent ONCE more, after a short wait; any other failure, and any
failure of the second attempt, is final. A bad ANSWER is never retried (D5: that happens after
`run_step`, in agents.py, and sends nothing again).

Every HTTP request the crew makes goes through CrewAI's `interceptor` into an `AttemptLog`
(backend/runtime/attempts.py), so agents.py can write ONE TRACE LINE PER REQUEST (PR 5, step 3):
the model string the API returned, its stop reason, that request's own token counts, and for a
request with no answer, why. The lines also show CrewAI's own silent repeat: when a 400 says the
model refuses `reasoning_effort`, CrewAI sends the call again WITHOUT it and then leaves it out of
every later call of the process (H-064 condition c). Such a request is flagged `off_pinned_setting`
on its trace line (PR 5, step 4); it is not stopped, so a run that goes off the pinned setting can
be seen and judged afterwards. Our own bound is still two attempts, but each of them can carry
CrewAI's repeat, so up to FOUR requests are possible, every one with its own line.

CrewAI is loaded only here, only when a real call is made, and only through `load_crewai()` (which
switches its telemetry, tracing and version check off first). A stand-in run never gets here
(T-MODE-1).
"""

import time
from dataclasses import dataclass
from functools import lru_cache

from backend.domain.schemas import ExtractionResult, Verdict, VerificationResult
from backend.runtime import model_settings, prompts
from backend.runtime.attempts import AttemptLog, HttpAttempt
from backend.runtime.crewai_setup import load_crewai
from backend.runtime.wire_schema import wire_schema
from backend.settings import Settings

# The class that checks each step's answer, and whose schema is sent to the provider.
STEP_RESULT = {"extract_rows": ExtractionResult, "check_conflicts": VerificationResult,
               "judge_applicability": Verdict}

MAX_RPM = 30           # sad.md §2: limits bursts from the parallel units
MAX_ATTEMPTS = 2       # DL-43: the call, and ONE retry. Never more.
RETRY_WAIT_S = 1.0     # DL-43's "short wait" before the retry (tests set it to 0)

# How many requests one unit can send, and how many of those can be BILLED (H-073). Each of our
# attempts can carry CrewAI's own repeat without `reasoning_effort`, so up to four requests. But
# CrewAI repeats only after a 400, which costs nothing (attempts.py: "rejected"), so only the
# request that follows can be billed. The cost cap's safety rests on that, and tests pin it.
MAX_REQUESTS_PER_UNIT = 2 * MAX_ATTEMPTS
MAX_BILLED_REQUESTS_PER_UNIT = MAX_ATTEMPTS


class ModelServiceError(Exception):
    """The provider did not give an answer: it timed out, was rate-limited, returned an error, or
    could not be reached. The unit fails with the reason "model service" (DL-43).
    `attempts` is every HTTP request that was sent, so each can still get its trace line."""

    def __init__(self, message: str, attempts: list[HttpAttempt] | None = None):
        super().__init__(message)
        self.attempts = attempts or []


def is_retriable(error: BaseException) -> bool:
    """Is this provider failure one DL-43 allows ONE retry for? (PR 5, step 1; `run_step` uses it.)

    Yes: the call's own timeout, no connection, a rate limit (429), a server error (5xx).
    No: any other answer from the provider (400 bad request, 401 bad key, 404 no such model...:
    sending the same request again cannot fix it and every attempt costs money), and anything
    that is not a provider failure at all (an invalid answer, a bug of ours).

    CrewAI wraps what the `openai` client raised (a timeout becomes a plain `ConnectionError`, a
    404 a `ValueError`), and `run_step` wraps that again as `ModelServiceError`. So we walk the
    chain of causes and let the FIRST `openai` error decide. Only when there is none do we trust a
    plain `ConnectionError` or `TimeoutError`. The walk stops at an error it has already seen, so
    a chain that loops back on itself cannot hang a run.
    """
    import openai  # only a real call gets here; stand-in never does

    seen: set[int] = set()
    looks_like_connection = False
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, openai.APIStatusError):
            return current.status_code == 429 or current.status_code >= 500
        if isinstance(current, openai.APIConnectionError):      # includes the client's own timeout
            return True
        if isinstance(current, (ConnectionError, TimeoutError)):
            looks_like_connection = True
        current = current.__cause__ or current.__context__
    return looks_like_connection


@dataclass
class StepResult:
    """What one real call gave back: the model's text, the token counts CrewAI reports, and every
    HTTP request that was made (the last one is the answer; earlier ones failed and were retried)."""
    text: str
    tokens_in: int
    tokens_out: int
    attempts: list[HttpAttempt]


@lru_cache
def _interceptor_class():
    """The class CrewAI's `interceptor` hook wants, made on first use because it must subclass
    CrewAI's `BaseInterceptor` and CrewAI may only be imported through `load_crewai()`."""
    load_crewai()
    import httpx
    from crewai.llms.hooks.base import BaseInterceptor

    class AttemptRecorder(BaseInterceptor[httpx.Request, httpx.Response]):
        """Hands every HTTP request and response to an `AttemptLog`. It changes nothing: the request
        and the response go on exactly as they were. It never raises, so recording can never be
        the reason a call fails."""

        def __init__(self, log: AttemptLog):
            self.log = log

        def on_outbound(self, message: httpx.Request) -> httpx.Request:
            self.log.begin(message.read())
            return message

        def on_inbound(self, message: httpx.Response) -> httpx.Response:
            self.log.finish(message.status_code, message.read())     # read() keeps the body for the client
            return message

        async def aon_outbound(self, message: httpx.Request) -> httpx.Request:
            return self.on_outbound(message)

        async def aon_inbound(self, message: httpx.Response) -> httpx.Response:
            self.log.finish(message.status_code, await message.aread())
            return message

    return AttemptRecorder


def build_crew(settings: Settings, step: str, inputs: dict[str, str],
               attempt_log: AttemptLog | None = None):
    """The one-agent, one-task crew for one unit. Builds only; sends nothing. With an
    `attempt_log`, every HTTP request the crew makes is written into it (the interceptor)."""
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
    if attempt_log is not None:
        llm_args["interceptor"] = _interceptor_class()(attempt_log)

    agent = Agent(role=text["role"], goal=text["goal"], backstory=text["backstory"],
                  llm=LLM(**llm_args), tools=[], allow_delegation=card["allow_delegation"],
                  memory=card["memory"], max_iter=card["max_iter"], max_retry_limit=0,
                  verbose=False)
    task = Task(description=text["description"], expected_output=text["expected_output"],
                agent=agent, guardrail_max_retries=0)
    return Crew(agents=[agent], tasks=[task], process=Process.sequential, max_rpm=MAX_RPM,
                memory=False, verbose=False)


def run_step(settings: Settings, step: str, inputs: dict[str, str]) -> StepResult:
    """Send one unit's prompt to the model and return its text. A failure `is_retriable` allows is
    sent ONCE more after `RETRY_WAIT_S` (DL-43); every other failure, and any failure of the second
    attempt, becomes `ModelServiceError` (the reason "model service"). At most `MAX_ATTEMPTS`
    requests of ours, whatever happens. Every HTTP request actually sent is in `.attempts` of the
    result, or of the error, whether it got an answer or not."""
    log = AttemptLog()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        crew = build_crew(settings, step, inputs, log)    # a fresh crew each time; refusals come from here
        try:
            output = crew.kickoff()
            break
        except Exception as error:              # CrewAI wraps some provider errors; all are one thing
            log.fail(f"{type(error).__name__}: {error}")     # a request with no response at all
            if attempt < MAX_ATTEMPTS and is_retriable(error):
                time.sleep(RETRY_WAIT_S)
                continue
            raise ModelServiceError(
                f"{type(error).__name__}: {error} (attempt {attempt} of {MAX_ATTEMPTS})",
                log.attempts) from error
    usage = output.token_usage
    return StepResult(text=output.raw or "", tokens_in=usage.prompt_tokens,
                      tokens_out=usage.completion_tokens, attempts=log.attempts)
