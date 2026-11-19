"""Shows the page again after a service refused a request (ux.md §5, H-036 V-12).

A service raises `Refused`; this module finds the page the form came from, builds it exactly as
its GET route does, and adds `refusal` (the shared object) with the refusal's HTTP status. Nothing
is decided here: the service already refused, audited the refusal and changed nothing.

A form posts to one address, so the address says which page to show again.
"""

import re

from fastapi import HTTPException, Request

from backend.db.connection import connect
from backend.domain.ids import run_id_from_child
from backend.services import runs as runs_service
from backend.services.auth import identity_from_session
from backend.services.refusals import Refusal
from backend.web.routes import calendar, gates, runs

# (address pattern, page). `child` is a row, verdict or calendar ID; the run is inside it.
_PAGES = [
    (re.compile(r"^/specialist/runs$"), "filing_rules"),
    (re.compile(r"^/specialist/runs/(?P<run_id>[^/]+)/(abandon|retry)$"), "review_status"),
    (re.compile(r"^/specialist/runs/(?P<run_id>[^/]+)/g1/complete$"), "g1"),
    (re.compile(r"^/specialist/runs/(?P<run_id>[^/]+)/g2/complete$"), "g2"),
    (re.compile(r"^/specialist/rows/(?P<child>[^/]+)/decision$"), "g1"),
    (re.compile(r"^/specialist/verdicts/(?P<child>[^/]+)/decision$"), "g2"),
    (re.compile(r"^/specialist/calendars/(?P<child>[^/]+)/(publish|decline)$"), "g3"),
]


def render_refused(request: Request, refusal: Refusal):
    """The page the form came from, with the refusal on it. 404 if the page cannot be found."""
    identity = identity_from_session(request.session)
    conn = connect(request.app.state.settings.database_path)
    try:
        for pattern, page in _PAGES:
            match = pattern.match(request.url.path)
            if not match:
                continue
            extra = {"refusal": refusal, "status_code": refusal.http_status}
            if page == "filing_rules":
                return runs.page_filing_rules(request, conn, identity, **extra)
            ids = match.groupdict()
            run_id = ids.get("run_id") or run_id_from_child(ids["child"])
            run = runs_service.get_run(conn, run_id)
            if run is None:
                raise HTTPException(status_code=404)
            builder = {"review_status": runs.page_review_status, "g1": gates.page_g1,
                       "g2": gates.page_g2, "g3": calendar.page_g3}[page]
            return builder(request, conn, identity, run, **extra)
        raise HTTPException(status_code=404)
    finally:
        conn.close()
