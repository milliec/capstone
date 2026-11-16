"""Loads the fund profile config for pages and stages (DL-53)."""

from functools import lru_cache

import yaml

from backend.services import FUND_ID
from backend.settings import ROOT


@lru_cache
def load_fund(fund_id: str = FUND_ID) -> dict:
    """Read config/fund/<fund_id>.yaml. App shell: display fields only (name, regime, year end)."""
    path = ROOT / "config" / "fund" / f"{fund_id}.yaml"
    return yaml.safe_load(path.read_text())
