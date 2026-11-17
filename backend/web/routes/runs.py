"""Page 2 · Filing rules (the review list) and page 3 · Review status (SAD §4 routes)."""

import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from backend.services import FUND_ID
from backend.services import runs as runs_service
from backend.services.audit import now_utc
from backend.services.auth import Identity
from backend.web.deps import get_conn, render, specialist

router = APIRouter(prefix="/specialist")


def load_run(conn: sqlite3.Connection, run_id: str) -> dict:
    """The run, or the 404 page if there is none (after the role check has passed)."""
    run = runs_service.get_run(conn, run_id)
    if run is None:
        raise HTTPException(status_code=404)
    return run


def page_filing_rules(request: Request, conn, identity: Identity, **extra):
    """Page 2. Also used to show the page again after a refusal (`extra` has the refusal)."""
    return render(request, conn, "pages/filing_rules.html", identity,
                  runs=runs_service.list_runs(conn, FUND_ID),
                  active_run=runs_service.get_active_run(conn, FUND_ID), **extra)


def page_review_status(request: Request, conn, identity: Identity, run: dict, **extra):
    """Page 3. Also used to show the page again after a refusal."""
    # Display only (frontend.md W-1). `refresh_on`: the specialist's "Stop automatic refresh"
    # choice, carried in the address as ?refresh=off and stored nowhere (ux.md page 3).
    # `rendered_at`: the time shown in "Last updated at …". Whether the page refreshes at all
    # still depends on the server's run state (run.is_working), not on this flag alone.
    return render(request, conn, "pages/review_status.html", identity, run=run,
                  units=runs_service.list_units(conn, run["run_id"]),
                  refresh_on=request.query_params.get("refresh") != "off",
                  rendered_at=now_utc(), **extra)


@router.get("/runs")
def filing_rules(request: Request, conn=Depends(get_conn),
                 identity: Identity = Depends(specialist)):
    return page_filing_rules(request, conn, identity)


@router.post("/runs")
def start_review(request: Request, background: BackgroundTasks, conn=Depends(get_conn),
                 identity: Identity = Depends(specialist),
                 demo_planted_row: bool = Form(False), demo_fail_step1: bool = Form(False)):
    run_id = runs_service.start_run(
        conn, request.app.state.settings, background.add_task, fund_id=FUND_ID,
        started_by=identity.identity_id, demo_planted_row=demo_planted_row,
        demo_fail_step1=demo_fail_step1)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.get("/runs/{run_id}")
def review_status(request: Request, run_id: str, conn=Depends(get_conn),
                  identity: Identity = Depends(specialist)):
    return page_review_status(request, conn, identity, load_run(conn, run_id))


@router.post("/runs/{run_id}/abandon")
def abandon(run_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
            run_version: int = Form(...), reason: str = Form("")):
    load_run(conn, run_id)
    runs_service.abandon_run(conn, run_id=run_id, run_version=run_version, reason=reason,
                             actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.post("/runs/{run_id}/retry")
def retry(request: Request, run_id: str, background: BackgroundTasks, conn=Depends(get_conn),
          identity: Identity = Depends(specialist), run_version: int = Form(...)):
    run = load_run(conn, run_id)
    notice = runs_service.retry_run(conn, request.app.state.settings, background.add_task,
                                    run_id=run_id, run_version=run_version,
                                    actor=identity.identity_id)
    return page_review_status(request, conn, identity, run, notice=notice)
