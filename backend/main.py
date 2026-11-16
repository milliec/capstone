"""Builds the app: settings, database, session cookie, routes and the error pages.

Run it with `make run` (or: .venv/bin/python -m uvicorn backend.main:create_app --factory).
`--factory` tells uvicorn to call create_app() itself, so merely importing this file (as the tests
do) creates no app and no database file.
"""

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from backend.db.connection import init_db
from backend.services.auth import Forbidden, identity_from_session
from backend.settings import Settings, load_settings
from backend.web.deps import NotSignedIn, render
from backend.web.routes import calendar, gates, runs, sign_in


def create_app(settings: Settings | None = None) -> FastAPI:
    """Make one app. Tests pass their own settings (temporary database, pause 0)."""
    settings = settings or load_settings()
    init_db(settings.database_path)

    app = FastAPI(title="Compliance calendar (demo)", docs_url=None, redoc_url=None)
    app.state.settings = settings

    # The signed session cookie that holds the mock identity (SAD §4). Signed means the browser
    # cannot change it without the server noticing; it is not encrypted, and holds no secret.
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret,
                       session_cookie="session", same_site="lax", https_only=False)

    for module in (sign_in, runs, gates, calendar):
        app.include_router(module.router)

    @app.exception_handler(NotSignedIn)
    def not_signed_in(request: Request, exc: NotSignedIn):
        return RedirectResponse("/sign-in", status_code=303)

    @app.exception_handler(Forbidden)
    def forbidden(request: Request, exc: Forbidden):
        # The refusal was already written to the audit log by auth.require_role.
        return render(request, None, "pages/no_access.html", exc.identity, status_code=403,
                      refusal=exc.refusal)

    @app.exception_handler(StarletteHTTPException)
    def http_error(request: Request, exc: StarletteHTTPException):
        identity = identity_from_session(request.session)
        if exc.status_code == 404:
            if identity is None:
                return RedirectResponse("/sign-in", status_code=303)
            return render(request, None, "pages/not_found.html", identity, status_code=404)
        # Any other HTTP error (405, ...): a plain line, nothing changed.
        return render(request, None, "pages/not_found.html", identity,
                      status_code=exc.status_code)

    return app
