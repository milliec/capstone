"""Shared test fixtures. Every test gets its own fresh database; no model is ever called.

A "fixture" is something pytest builds and hands to a test that names it as a parameter.
"""

import pytest
from fastapi.testclient import TestClient

from backend.db.connection import connect
from backend.main import create_app
from backend.settings import load_settings
from tests.fake_openai import FakeOpenAI


@pytest.fixture
def settings(tmp_path):
    """Stand-in mode, pause 0 (tests stay fast), a temporary database file."""
    return load_settings({
        "AGENTS_MODE": "stand_in",
        "STAND_IN_UNIT_PAUSE_S": "0",
        "SESSION_SECRET": "test-only",
        "DATABASE_PATH": str(tmp_path / "test.db"),
    })


@pytest.fixture
def client(settings):
    """A browser-like client that is not signed in."""
    return TestClient(create_app(settings))


def _signed_in(settings, identity_id):
    c = TestClient(create_app(settings))
    c.post("/sign-in", data={"identity_id": identity_id})
    return c


@pytest.fixture
def specialist_client(settings):
    return _signed_in(settings, "specialist-1")


@pytest.fixture
def gp_client(settings):
    return _signed_in(settings, "gp-1")


@pytest.fixture
def db(settings):
    """A connection to the test database, for checking what was stored."""
    conn = connect(settings.database_path)
    yield conn
    conn.close()


@pytest.fixture
def fake_openai():
    """A fake OpenAI server on this machine only (tests/fake_openai.py). No real model, no real
    key. It is stopped when the test ends."""
    fake = FakeOpenAI().start()
    yield fake
    fake.stop()


@pytest.fixture
def as_openai(fake_openai, monkeypatch):
    """Make CrewAI behave as if it were talking to api.openai.com, while every request still goes
    to the fake on this machine.

    Why: CrewAI does extra things only when it believes the server is OpenAI itself, for example a
    pre-flight request that counts the prompt's tokens (`POST /v1/responses/input_tokens`). Against
    any other host it skips them, so a plain fake never shows them, and the first real spike call
    sent a request no test had ever seen (RUN-20261122-1). With this fixture the fake answers that
    endpoint like OpenAI does, and the request shows in `fake_openai.requests`.

    It patches CrewAI's own test for "is this a compatible server?". If a CrewAI upgrade renames it,
    this fails loudly (monkeypatch refuses a name that does not exist) instead of testing nothing.
    """
    from backend.runtime import crews
    crews.load_crewai()                      # CrewAI is only imported through here (switches first)
    from crewai.llms.providers.openai.completion import OpenAICompletion
    monkeypatch.setattr(OpenAICompletion, "_on_compatible_server", lambda self: False)
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    return fake_openai
