"""Settings, read from the environment (and the git-ignored .env file) once.

Variable names follow SAD §4 "Sign-in and secrets". Only the settings the app shell uses are read
here; the timeouts, stage limits and model settings come in with B3.

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
    )
