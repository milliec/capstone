"""The three agent functions (extractor, verifier, judge).

App shell: only the stand-in path exists, and it returns nothing yet (B3 adds the fixed outputs
and the CrewAI wiring). Real mode is refused: no model call before the first green path.

The stand-in pause (DL-54, B13a): each stand-in unit waits STAND_IN_UNIT_PAUSE_S seconds before
returning, so the units table fills in one row at a time. Real mode NEVER pauses (T-PAUSE-1).
"""

import time

from backend.settings import Settings


class RealAgentsNotBuilt(Exception):
    """Real agents arrive with the B3 spike, after the first green path. Not in the shell."""


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


def run_unit(settings: Settings, stage: str, unit_id: str) -> None:
    """STUB — replace in B3. Run one unit of a stage with the configured agents.

    Stand-in: pause, then return (B3 returns the fixed output from backend/stand_in/).
    Real: refused in the shell.
    """
    if settings.agents_mode != "stand_in":
        raise RealAgentsNotBuilt("AGENTS_MODE=real is not built yet (B3 spike, after green path)")
    unit_pause(settings)
