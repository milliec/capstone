"""What one model call is sent with, per role, and what it can cost at most (B3 step 7b, PR 2).

Plain code: no CrewAI, no network, no model call. It answers three questions the crews (PR 4) and
the trace (PR 5) will ask:

  1. Which settings does this role's call use? (`role_settings`)  The model ID comes from .env and
     is never written in a committed file (DL-40). The sampling settings are DL-40's, written here
     because they are decisions, not secrets.
  2. What does a call cost, from the token counts the provider returns? (`call_cost_usd`)
  3. Can a whole run stay under the cost cap whatever the model answers? (`worst_case_run_cost_usd`)
     Every call has its own `max_completion_tokens`, so one call has a ceiling (CR-017); a test
     adds up the ceilings for a generous run and fails if they could pass the US$2.50 hard stop.

Prices are the operator's DL-40 prices (2026-11-19), US dollars per 1 million tokens, kept per
ROLE (not per model ID, so no ID is committed). The provider's price list is the source of truth:
re-check these before the spike.
"""

import json
from dataclasses import dataclass

from backend.settings import ROLES, Settings

# The role each agent function (step) uses.
STEP_ROLE = {"extract_rows": "extract", "check_conflicts": "verify", "judge_applicability": "judge"}

# DL-40, per role. `None` means the setting is not sent at all (a reasoning model may refuse it).
#  - extractor: reasoning_effort none, temperature 0
#  - verifier: reasoning_effort low. DL-40 names no temperature for it, so none is sent. (An
#    assumption: say if the verifier should also run at temperature 0.)
#  - judge: reasoning_effort medium, no temperature
REASONING_EFFORT = {"extract": "none", "verify": "low", "judge": "medium"}
TEMPERATURE = {"extract": 0.0, "verify": None, "judge": None}

# US$ per 1 million tokens, (input, output). DL-40 prices as given by the operator, 2026-11-19.
PRICE_PER_MILLION_USD = {"extract": (0.10, 0.50), "verify": (2.00, 12.00), "judge": (1.00, 5.00)}

# Sad.md DL-43: "the HTTP client timeout is set a few seconds below" the call's own timeout, so the
# client gives up first and the failure is ours to record. The same 5 seconds .env.example used.
HTTP_TIMEOUT_MARGIN_S = 5.0


class ModelNotSet(Exception):
    """A real call was about to be made for a role whose model ID is not set in .env."""


@dataclass(frozen=True)
class RoleSettings:
    role: str
    model: str
    reasoning_effort: str
    temperature: float | None
    max_completion_tokens: int
    call_timeout_s: float
    http_timeout_s: float

    def sent_to_provider(self) -> dict:
        """The sampling settings that go in the request. A `None` is left out, not sent as null."""
        sent = {"reasoning_effort": self.reasoning_effort,
                "max_completion_tokens": self.max_completion_tokens}
        if self.temperature is not None:
            sent["temperature"] = self.temperature
        return sent

    def logged(self) -> str:
        """The text for the trace's `settings_json` column (CR-018): what was sent, as JSON."""
        return json.dumps(self.sent_to_provider(), sort_keys=True)


def role_settings(settings: Settings, role: str) -> RoleSettings:
    """The call settings for one role. Refuses a role without a model ID: with no ID, no call."""
    if role not in ROLES:
        raise ValueError(f"Unknown role {role!r}; the roles are {ROLES}")
    model = settings.llm_models[role]
    if not model:
        raise ModelNotSet(f"LLM_MODEL_{role.upper()} is not set in .env, so no {role} call can "
                          "be made (DL-40).")
    timeout = settings.call_timeouts[role]
    return RoleSettings(
        role=role, model=model, reasoning_effort=REASONING_EFFORT[role],
        temperature=TEMPERATURE[role], max_completion_tokens=settings.max_completion_tokens[role],
        call_timeout_s=timeout, http_timeout_s=max(timeout - HTTP_TIMEOUT_MARGIN_S, 1.0))


def call_cost_usd(role: str, tokens_in: int, tokens_out: int) -> float:
    """What a call cost, from the provider's token counts and the role's prices."""
    price_in, price_out = PRICE_PER_MILLION_USD[role]
    return (tokens_in * price_in + tokens_out * price_out) / 1_000_000


def worst_case_call_cost_usd(settings: Settings, role: str, input_tokens: int) -> float:
    """The most one call can cost: its whole input, and an answer that fills its output limit."""
    return call_cost_usd(role, input_tokens, settings.max_completion_tokens[role])


def worst_case_run_cost_usd(settings: Settings, *, input_tokens: dict[str, int],
                            calls: dict[str, int]) -> float:
    """The most a run can cost: for each role, `calls[role]` calls at the worst-case price for
    `input_tokens[role]`. Count the retry yourself (DL-43 allows one: pass twice the calls)."""
    return sum(calls[role] * worst_case_call_cost_usd(settings, role, input_tokens[role])
               for role in ROLES)
