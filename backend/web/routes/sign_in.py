"""Page 1 · Sign-in, sign-out, the home redirect and /health (SAD §4 routes)."""

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from backend.services.auth import IDENTITIES, identity_from_session, sign_in
from backend.web.deps import render

router = APIRouter()


def _home_for(identity) -> str:
    return "/specialist/runs" if identity.role == "specialist" else "/calendar"


@router.get("/health")
def health():
    """Tells a start-up check that the application is running (SAD §5)."""
    return {"status": "ok"}


@router.get("/")
def home(request: Request):
    identity = identity_from_session(request.session)
    return RedirectResponse(_home_for(identity) if identity else "/sign-in", status_code=303)


@router.get("/sign-in")
def sign_in_page(request: Request):
    return render(request, None, "pages/sign_in.html", None,
                  identities=list(IDENTITIES.values()))


@router.post("/sign-in")
def sign_in_submit(request: Request, identity_id: str = Form(...)):
    identity = sign_in(identity_id)
    if identity is None:
        return render(request, None, "pages/sign_in.html", None, status_code=422,
                      identities=list(IDENTITIES.values()),
                      refusal="Choose one of the two demo identities.")
    request.session.clear()
    request.session["identity_id"] = identity.identity_id
    return RedirectResponse(_home_for(identity), status_code=303)


@router.post("/sign-out")
def sign_out(request: Request):
    request.session.clear()
    return RedirectResponse("/sign-in", status_code=303)
