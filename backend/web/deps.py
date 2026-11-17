"""Shared pieces every route uses: the database connection, who is signed in, and rendering.

FastAPI "dependencies" are functions a route asks for in its parameters, e.g.
`identity = Depends(specialist)`. FastAPI runs them before the route, in order, so the role is
checked BEFORE the route looks up the review (ux.md §1.7: a General Partner gets 403 on a
specialist address whether or not that review exists).
"""

import sqlite3
from datetime import date, datetime
from pathlib import Path

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from backend.db.connection import connect
from backend.services import FUND_ID
from backend.services.auth import Identity, identity_from_session, require_role
from backend.services.fund import load_fund
from backend.services.runs import get_active_run

templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))


# --- Date and time formats for the pages (frontend.md §10.2, W-2) -----------------------------
# Display only: these turn a stored value into the words ux.md §1.6 asks for ("Mon 2 Feb 2027",
# "14:02"). They decide nothing. Stored times are UTC (audit.now_utc); the page shows them in the
# server's local time (frontend.md Assumptions). An empty value shows as an empty string.

def _to_local(value) -> datetime | None:
    """A stored ISO timestamp (or a datetime) as a local datetime, or None if empty."""
    if not value:
        return None
    moment = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return moment.astimezone()  # no argument = the server's local time zone


def format_date(value) -> str:
    """'2027-01-11' or a timestamp → 'Mon 11 Jan 2027'."""
    if not value:
        return ""
    if isinstance(value, date) and not isinstance(value, datetime):
        day = value
    elif isinstance(value, str) and len(value) == 10:  # a plain date such as a due date
        day = date.fromisoformat(value)
    else:
        day = _to_local(value).date()
    return f"{day:%a} {day.day} {day:%b %Y}"  # day.day avoids a leading zero ("2", not "02")


def format_time(value) -> str:
    """A timestamp → '14:02'."""
    moment = _to_local(value)
    return f"{moment:%H:%M}" if moment else ""


def format_time_seconds(value) -> str:
    """A timestamp → '14:02:09' (used by "Last updated at …", approved 2026-11-17)."""
    moment = _to_local(value)
    return f"{moment:%H:%M:%S}" if moment else ""


def format_datetime(value) -> str:
    """A timestamp → 'Fri 13 Nov 2026, 14:00' (Filing rules "Started", ux.md page 2)."""
    return f"{format_date(value)}, {format_time(value)}" if value else ""


templates.env.filters["date"] = format_date
templates.env.filters["time"] = format_time
templates.env.filters["time_seconds"] = format_time_seconds
templates.env.filters["datetime"] = format_datetime


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
