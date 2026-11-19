"""CrewAI is installed, but stays switched off from the outside world (B3 step 7b, PR 1; Tier 1).

1. Telemetry off: loading CrewAI through `load_crewai()` and building a crew opens no network
   connection, and CrewAI's own telemetry, tracing and version check all report "off", even when
   the environment tries to turn them back on.
2. T-MODE-1 (stand-in part): a whole stand-in review (the green path) never loads CrewAI.

Both run in a fresh Python process, because once any test in this process has loaded CrewAI it
stays loaded, and the answer would depend on the order the tests run in. No model, no key, no
paid call: the "key" below is a placeholder and every network connection is blocked.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from backend.runtime.crewai_setup import CREWAI_ENV

ROOT = Path(__file__).resolve().parents[2]


def _run(script: str, env_extra: dict[str, str], tmp_path: Path) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in CREWAI_ENV}
    env.update(env_extra)
    env["HOME"] = str(tmp_path)          # anything CrewAI writes for "its user" lands here
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180,
    )


# The network block: every way Python opens a connection or looks up a name is replaced by a
# function that writes down what was tried and then refuses.
BLOCK_NETWORK = """
    import socket
    tried = []
    def _refuse(*args, **kwargs):
        tried.append(repr(args[:2]))
        raise OSError("network blocked by the test")
    socket.socket.connect = _refuse
    socket.socket.connect_ex = _refuse
    socket.create_connection = _refuse
    socket.getaddrinfo = _refuse
"""


def test_loading_crewai_and_building_a_crew_opens_no_connection(tmp_path):
    script = BLOCK_NETWORK + """
    import os
    from backend.runtime.crewai_setup import CREWAI_ENV, load_crewai

    crewai = load_crewai()
    assert crewai.__version__ == "1.15.35", crewai.__version__

    # The switches are forced, even though the environment asked for the opposite.
    for name, value in CREWAI_ENV.items():
        assert os.environ[name] == value, (name, os.environ[name])

    # CrewAI's own answers: telemetry off, tracing off.
    from crewai.telemetry.telemetry import Telemetry
    from crewai.events.listeners.tracing.utils import should_enable_tracing
    assert Telemetry._is_telemetry_disabled() is True
    assert should_enable_tracing() is False

    # Build (do not run) a one-agent crew, as real mode will. No model call is made.
    llm = crewai.LLM(model="gpt-test-not-real", api_key="sk-test-placeholder-not-a-key")
    agent = crewai.Agent(role="r", goal="g", backstory="b", llm=llm,
                         allow_delegation=False, tools=[])
    task = crewai.Task(description="d", expected_output="e", agent=agent)
    crewai.Crew(agents=[agent], tasks=[task], memory=False)

    assert tried == [], tried
    print("OK")
    """
    # The environment tries to switch everything back on; load_crewai() must win.
    on_again = {
        "CREWAI_DISABLE_TELEMETRY": "false",
        "OTEL_SDK_DISABLED": "false",
        "CREWAI_TRACING_ENABLED": "true",
        "CREWAI_DISABLE_VERSION_CHECK": "false",
    }
    result = _run(script, on_again, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().endswith("OK")


def test_a_whole_stand_in_review_never_loads_crewai(tmp_path):
    """T-MODE-1: run the green path (a full stand-in review, start to published calendar), then
    check that CrewAI was never loaded. Every backend module is imported first too, so a
    top-level `import crewai` anywhere outside crewai_setup.py would also be caught."""
    script = """
    import importlib, pkgutil, sys
    import backend, pytest

    for m in pkgutil.walk_packages(backend.__path__, "backend."):
        if m.name != "backend.runtime.crewai_setup":
            importlib.import_module(m.name)
    assert "crewai" not in sys.modules, "a backend module imports crewai at load time"

    code = pytest.main(["-q", "-p", "no:cacheprovider", "tests/tier1/test_green_path.py"])
    assert code == 0, f"green path failed: {code}"
    assert "crewai" not in sys.modules, "the stand-in review loaded crewai"
    print("OK")
    """
    result = _run(script, {"AGENTS_MODE": "stand_in"}, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip().endswith("OK")
