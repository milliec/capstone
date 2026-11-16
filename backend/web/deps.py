"""Shared pieces every route uses: the database connection, who is signed in, and rendering.

FastAPI "dependencies" are functions a route asks for in its parameters, e.g.
`identity = Depends(specialist)`. FastAPI runs them before the route, in order, so the role is
checked BEFORE the route looks up the review (ux.md §1.7: a General Partner gets 403 on a
specialist address whether or not that review exists).
"""

import sqlite3
from pathlib import Path

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from backend.db.connection import connect
from backend.services import FUND_ID
from backend.services.auth import Identity, identity_from_session, require_role
from backend.services.fund import load_fund
from backend.services.runs import get_active_run

templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))


class NotSignedIn(Exception):
    """No valid session: the web layer redirects to /sign-in (ux.md §1.7)."""


def get_conn(request: Request):
    """One database connection per request, closed when the response is done."""
    conn = connect(request.app.state.settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def signed_in(request: Request) -> Identity:
    """Anyone signed in (specialist or General Partner)."""
    identity = identity_from_session(request.session)
    if identity is None:
        raise NotSignedIn()
    return identity


def specialist(request: Request, conn: sqlite3.Connection = Depends(get_conn),
               identity: Identity = Depends(signed_in)) -> Identity:
    """Specialist only. The check itself lives in the service (auth.require_role)."""
    require_role(conn, identity, "specialist", request.url.path)
    return identity


def render(request: Request, conn: sqlite3.Connection | None, template: str,
           identity: Identity | None, status_code: int = 200, **context):
    """Render a page with the shared-frame data (ux.md §1.3) added to `context`."""
    your_turn = False
    if conn is not None and identity is not None and identity.role == "specialist":
        active = get_active_run(conn, FUND_ID)
        your_turn = bool(active and active["is_at_gate"])
    frame = {
        "identity": identity,
        "fund": load_fund(FUND_ID),
        "agents_mode": request.app.state.settings.agents_mode,
        "your_turn": your_turn,
        "current_path": request.url.path,
    }
    return templates.TemplateResponse(request, template, {**frame, **context},
                                      status_code=status_code)
