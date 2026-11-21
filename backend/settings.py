"""Settings, read from the environment (and the git-ignored .env file) once.

Variable names follow SAD §4 "Sign-in and secrets". B3 step 6 adds the cost cap
(RUN_COST_CAP_USD) and the stage time limits (STAGE_TIME_LIMIT_A, _B, _C). B3 step 7b PR 2 adds
the per-role model settings: the model IDs (LLM_MODEL_*), each call's output limit
(LLM_MAX_TOKENS_*) and each call's own timeout (CALL_TIMEOUT_*). They are READ here and checked
where a call is made (backend/runtime/model_settings.py), so a missing model ID never stops the
app in stand-in mode.

Two rules this file enforces (Build card, CR-030, DL-54):
- AGENTS_MODE defaults to "stand_in" when it is not set (T-MODE-1).
- STAND_IN_UNIT_PAUSE_S is read ONLY in stand-in mode. In real mode it is never read, and the
  pause is always 0 (T-PAUSE-1).
"""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

AGENTS_MODES = ("stand_in", "real")
SPEND_ACTIVITIES = ("spike", "tuning", "evaluation", "rehearsal", "demo")

# The three model roles (sad.md §2 "Model and Context Strategy"): the extractor, the verifier and
# the applicability judge. The settings below are keyed by these names.
ROLES = ("extract", "verify", "judge")


class SettingsError(Exception):
    """A setting is missing or wrong, so the app refuses to start."""


def _load_dotenv(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines from .env. Tiny on purpose: no extra dependency for this.

    Lines starting with # and blank lines are skipped. Values are not unquoted.
    """
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()
    return values


@dataclass(frozen=True)
class Settings:
    agents_mode: str
    spend_activity: str
    stand_in_unit_pause_s: float
    session_secret: str
    database_path: Path
    run_cost_cap_usd: float = 2.50                     # CR-017, DL-36
    # Seconds per stage on the backend's own timer (rule 6, DL-43); replaced after the spike.
    stage_time_limits: dict = None                     # {"A": 375.0, "B": 150.0, "C": 30.0}
    # Per role (B3 step 7b PR 2). The model ID is "" until the operator sets it in .env (DL-40);
    # no ID is written in any committed file.
    llm_models: dict = None                            # {"extract": "", "verify": "", "judge": ""}
    max_completion_tokens: dict = None                 # the output limit of one call, per role
    call_timeouts: dict = None                         # seconds a call may take (D1, DL-43), per role


STAGE_TIME_LIMIT_DEFAULTS = {"A": 375.0, "B": 150.0, "C": 30.0}

# The output limit of one call. A reasoning model's hidden thinking counts inside it, so the two
# reasoning roles get more room. These are starting values: the spike shows the real sizes, and
# backend/runtime/model_settings.py checks that any values still keep a whole run under the cap.
MAX_COMPLETION_TOKENS_DEFAULTS = {"extract": 2000, "verify": 2000, "judge": 4000}

# Each call's own timeout in seconds (sad.md §2 stage table; DL-43).
CALL_TIMEOUT_DEFAULTS = {"extract": 90.0, "verify": 60.0, "judge": 60.0}


def _positive(env: dict, name: str, default: float) -> float:
    """A number setting that must be above 0; empty means the default."""
    raw = env.get(name, "").strip()
    try:
        value = float(raw) if raw else default
    except ValueError:
        raise SettingsError(f"{name} must be a number, not {raw!r}")
    if value <= 0:
        raise SettingsError(f"{name} must be above 0")
    return value


def _whole_number(env: dict, name: str, default: int) -> int:
    """A whole-number setting that must be above 0; empty means the default."""
    raw = env.get(name, "").strip()
    try:
        value = int(raw) if raw else default
    except ValueError:
        raise SettingsError(f"{name} must be a whole number, not {raw!r}")
    if value <= 0:
        raise SettingsError(f"{name} must be above 0")
    return value


def load_settings(env: dict[str, str] | None = None) -> Settings:
    """Build the settings.

    `env` lets tests pass their own values. When it is None, the real environment is used, with
    .env filling in anything the environment does not set.
    """
    if env is None:
        env = {**_load_dotenv(ROOT / ".env"), **os.environ}

    # An empty or missing AGENTS_MODE means stand-in (T-MODE-1).
    agents_mode = env.get("AGENTS_MODE", "").strip() or "stand_in"
    if agents_mode not in AGENTS_MODES:
        raise SettingsError(f"AGENTS_MODE must be one of {AGENTS_MODES}, not {agents_mode!r}")

    spend_activity = env.get("SPEND_ACTIVITY", "").strip()
    if agents_mode == "real" and spend_activity not in SPEND_ACTIVITIES:
        # Real mode is only for the five paid activities (CR-030). Refuse to start otherwise.
        raise SettingsError("AGENTS_MODE=real needs SPEND_ACTIVITY set to one of "
                            f"{SPEND_ACTIVITIES}")

    if agents_mode == "stand_in":
        # Default 1 second per unit (DL-54). Tests set it to 0.
        pause = float(env.get("STAND_IN_UNIT_PAUSE_S", "1") or "1")
        if pause < 0:
            raise SettingsError("STAND_IN_UNIT_PAUSE_S cannot be negative")
    else:
        pause = 0.0  # Real mode: the variable is deliberately never read.

    session_secret = env.get("SESSION_SECRET", "").strip()
    if not session_secret or session_secret.startswith("REPLACE-ME"):
        # A local-only fallback so `make run` works before .env is filled in. It is not a secret:
        # sign-in is a mock (SD A-5), not access control. Set SESSION_SECRET in .env anyway.
        session_secret = "local-dev-only-not-a-secret"

    database_path = Path(env.get("DATABASE_PATH", "").strip() or "data/app.db")
    if not database_path.is_absolute():
        database_path = ROOT / database_path

    return Settings(
        agents_mode=agents_mode,
        spend_activity=spend_activity,
        stand_in_unit_pause_s=pause,
        session_secret=session_secret,
        database_path=database_path,
        run_cost_cap_usd=_positive(env, "RUN_COST_CAP_USD", 2.50),
        stage_time_limits={stage: _positive(env, f"STAGE_TIME_LIMIT_{stage}", default)
                           for stage, default in STAGE_TIME_LIMIT_DEFAULTS.items()},
        llm_models={role: env.get(f"LLM_MODEL_{role.upper()}", "").strip() for role in ROLES},
        max_completion_tokens={role: _whole_number(env, f"LLM_MAX_TOKENS_{role.upper()}", default)
                               for role, default in MAX_COMPLETION_TOKENS_DEFAULTS.items()},
        call_timeouts={role: _positive(env, f"CALL_TIMEOUT_{role.upper()}", default)
                       for role, default in CALL_TIMEOUT_DEFAULTS.items()},
    )
