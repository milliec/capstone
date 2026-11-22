"""The one door to CrewAI (B3 step 7b, PR 1).

Real mode loads CrewAI only through `load_crewai()`. Stand-in mode never calls it, so a stand-in
run never loads CrewAI at all (T-MODE-1; tests/tier1/test_crewai_setup.py checks both).

Before the first import, `load_crewai()` switches off every way CrewAI 1.15.35 reaches the
outside on its own (checked in its source, 2026-11-19):

- CREWAI_DISABLE_TELEMETRY / OTEL_SDK_DISABLED: its anonymous usage data (OpenTelemetry). Either
  one is enough; both are set, as the operator asked.
- CREWAI_TRACING_ENABLED=false: its own "tracing", which can send a first run's traces to the
  CrewAI platform. Separate from telemetry. Our trace (CR-018) is the only trace.
- CREWAI_DISABLE_VERSION_CHECK=true: a check that asks the package index for a newer version.

Second job (PR 4): CrewAI wraps every model call in its OWN retry for rate limits (HTTP 429): three
attempts with a wait between them, and no setting for it (`crewai/llms/retry.py`). That would make
a rate-limited call three requests inside CrewAI, and six once our own DL-43 retry is added around
it. The SAD allows ONE retry, ours, with one trace line per attempt (H-065). So `load_crewai()`
sets that module's attempt count to 1. It is a library internal, so it is pinned with the version
and tests/tier1/test_crews.py fails if a CrewAI upgrade moves or renames it.

The values are FORCED, not defaults: a line in .env or the shell saying otherwise cannot turn
them back on. The only outside call the application makes is the model call itself (SD MN-002).
"""

import os
from types import ModuleType

# Name -> forced value. Read by tests; change only together with the test that checks them.
CREWAI_ENV: dict[str, str] = {
    "CREWAI_DISABLE_TELEMETRY": "true",
    "OTEL_SDK_DISABLED": "true",
    "CREWAI_TRACING_ENABLED": "false",
    "CREWAI_DISABLE_VERSION_CHECK": "true",
}


def load_crewai() -> ModuleType:
    """Switch CrewAI's outside connections off, then import it and return the module.

    Call this instead of `import crewai`. Setting the variables again on every call is harmless
    and keeps them forced even if something changed them after the first import.
    """
    os.environ.update(CREWAI_ENV)
    import crewai  # imported here on purpose: only real mode may load it
    from crewai.llms import retry

    # CrewAI's own 3-attempt rate-limit retry off: one attempt, then the error comes back to us.
    # `assert` is not used: a renamed constant must stop the real call, not be skipped.
    if not hasattr(retry, "_LLM_RATE_LIMIT_MAX_ATTEMPTS"):
        raise RuntimeError("CrewAI changed its rate-limit retry; check it before any real call")
    retry._LLM_RATE_LIMIT_MAX_ATTEMPTS = 1

    return crewai
