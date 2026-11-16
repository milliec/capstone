"""Shared test fixtures. Every test gets its own fresh database; no model is ever called.

A "fixture" is something pytest builds and hands to a test that names it as a parameter.
"""

import pytest
from fastapi.testclient import TestClient

from backend.db.connection import connect
from backend.main import create_app
from backend.settings import load_settings


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
