"""Page 6 · Check the calendar and publish (G3), and page 7 · Calendar (General Partner)."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from backend.services import FUND_ID, publishing
from backend.services import calendar as calendar_service
from backend.services.auth import Identity
from backend.services.refusals import NotFound, refuse
from backend.web.deps import get_conn, render, signed_in, specialist
from backend.web.routes.runs import load_run

router = APIRouter()


def page_g3(request: Request, conn, identity: Identity, run: dict, **extra):
    """Page 6. Also used to show the page again after a refusal."""
    return render(request, conn, "pages/publish.html", identity, run=run,
                  view=calendar_service.get_g3_view(conn, run), **extra)


@router.get("/specialist/runs/{run_id}/g3")
def publish_page(request: Request, run_id: str, conn=Depends(get_conn),
                 identity: Identity = Depends(specialist)):
    return page_g3(request, conn, identity, load_run(conn, run_id))


def _check_decision_matches_route(conn, identity: Identity, calendar_id: str, decision: str,
                                  expected: str) -> None:
    """VALIDATION (DL-48): the G3 form must say which answer it is, and the button must match it.

    This stays here, not in the service, because the service functions have no `decision`
    (SAD §4 "Service functions"). It reads the form only; it decides nothing about the review.
    """
    cal = conn.execute("SELECT run_id, fund_id FROM calendar_versions WHERE calendar_id = ?",
                       (calendar_id,)).fetchone()
    if cal is None:
        raise NotFound(calendar_id)
    where = {"actor": identity.identity_id, "fund_id": cal["fund_id"], "run_id": cal["run_id"],
             "subject_id": calendar_id, "anchor": "decision", "target_label": "the question"}
    if decision not in ("publish", "decline"):
        refuse(conn, "VALIDATION", "no_answer", **where)
    if decision != expected:
        refuse(conn, "VALIDATION", "field", field="the answer", **where)


@router.post("/specialist/calendars/{calendar_id}/publish")
def publish(calendar_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
            run_version: int = Form(...), decision: str = Form(""), acknowledged: bool = Form(False),
            rejected_row_ids: list[str] = Form([]),
            uncited_paragraph_ids: list[str] = Form([])):
    _check_decision_matches_route(conn, identity, calendar_id, decision, "publish")
    run_id = publishing.publish_calendar(
        conn, calendar_id=calendar_id, run_version=run_version, acknowledged=acknowledged,
        rejected_row_ids=rejected_row_ids, uncited_paragraph_ids=uncited_paragraph_ids,
        actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.post("/specialist/calendars/{calendar_id}/decline")
def decline(calendar_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
            run_version: int = Form(...), decision: str = Form(""),
            decline_reason: str = Form("")):
    _check_decision_matches_route(conn, identity, calendar_id, decision, "decline")
    run_id = publishing.decline_calendar(
        conn, calendar_id=calendar_id, run_version=run_version, decline_reason=decline_reason,
        actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.get("/calendar")
def calendar_page(request: Request, conn=Depends(get_conn),
                  identity: Identity = Depends(signed_in)):
    """Both roles may view the calendar (SAD §4)."""
    # Display only (B12, DL-49; frontend.md W-6). The views are a radio group that CSS (:has())
    # switches in place, no script, so this only decides which radio starts ticked: ?view=list|
    # month|year (anything else is the Month view, the default: operator, 2026-11-17, as in the
    # mock-up). For the Month view's month links it also reads ?month=YYYY-MM. Stored nowhere;
    # decides nothing about the entries.
    view = request.query_params.get("view", "month")
    return render(request, conn, "pages/calendar.html", identity,
                  published=calendar_service.get_published_calendar(conn, FUND_ID),
                  cal_view=view if view in ("list", "month", "year") else "month",
                  cal_month=request.query_params.get("month"))
