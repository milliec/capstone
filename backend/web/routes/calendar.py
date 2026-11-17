"""Page 6 · Check the calendar and publish (G3), and page 7 · Calendar (General Partner)."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from backend.services import FUND_ID, publishing
from backend.services import calendar as calendar_service
from backend.services.auth import Identity
from backend.web.deps import get_conn, render, signed_in, specialist
from backend.web.routes.runs import load_run

router = APIRouter()


@router.get("/specialist/runs/{run_id}/g3")
def publish_page(request: Request, run_id: str, conn=Depends(get_conn),
                 identity: Identity = Depends(specialist)):
    run = load_run(conn, run_id)
    return render(request, conn, "pages/publish.html", identity, run=run,
                  view=calendar_service.get_g3_view(conn, run))


@router.post("/specialist/calendars/{calendar_id}/publish")
def publish(calendar_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
            run_version: int = Form(...), acknowledged: bool = Form(False),
            rejected_row_ids: list[str] = Form([]),
            uncited_paragraph_ids: list[str] = Form([])):
    run_id = publishing.publish_calendar(
        conn, calendar_id=calendar_id, run_version=run_version, acknowledged=acknowledged,
        rejected_row_ids=rejected_row_ids, uncited_paragraph_ids=uncited_paragraph_ids,
        actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.post("/specialist/calendars/{calendar_id}/decline")
def decline(calendar_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
            run_version: int = Form(...), decline_reason: str = Form("")):
    run_id = publishing.decline_calendar(
        conn, calendar_id=calendar_id, run_version=run_version, decline_reason=decline_reason,
        actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.get("/calendar")
def calendar_page(request: Request, conn=Depends(get_conn),
                  identity: Identity = Depends(signed_in)):
    """Both roles may view the calendar (SAD §4)."""
    # Display only (B12, DL-49: views "chosen by a link, no script"; frontend.md W-6): which view
    # to show, ?view=list|month|year (anything else is the List view, the default), and for the
    # Month view which month, ?month=YYYY-MM. Stored nowhere; decides nothing about the entries.
    view = request.query_params.get("view", "list")
    return render(request, conn, "pages/calendar.html", identity,
                  published=calendar_service.get_published_calendar(conn, FUND_ID),
                  cal_view=view if view in ("list", "month", "year") else "list",
                  cal_month=request.query_params.get("month"))
