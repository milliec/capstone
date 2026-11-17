"""Page 4 · Check the rules (G1), page 5 · Confirm what applies (G2), and their POST forms."""

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import RedirectResponse

from backend.services import decisions, gates
from backend.services.auth import Identity
from backend.web.deps import get_conn, render, specialist
from backend.web.routes.runs import load_run

router = APIRouter(prefix="/specialist")


def page_g1(request: Request, conn, identity: Identity, run: dict, **extra):
    """Page 4. Also used to show the page again after a refusal."""
    # Display only (frontend.md W-7): ?after=<row just decided> lets the page put its #next marker on
    # the next rule that still needs a decision (operator, 2026-11-17). Decides nothing.
    return render(request, conn, "pages/check_rules.html", identity, run=run,
                  view=decisions.get_g1_view(conn, run), after=request.query_params.get("after"),
                  **extra)


def page_g2(request: Request, conn, identity: Identity, run: dict, **extra):
    """Page 5. Also used to show the page again after a refusal."""
    return render(request, conn, "pages/confirm_applies.html", identity, run=run,
                  view=decisions.get_g2_view(conn, run), after=request.query_params.get("after"),
                  **extra)


@router.get("/runs/{run_id}/g1")
def check_rules(request: Request, run_id: str, conn=Depends(get_conn),
                identity: Identity = Depends(specialist)):
    return page_g1(request, conn, identity, load_run(conn, run_id))


@router.post("/rows/{row_id}/decision")
def decide_row(row_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
               version: int = Form(...), decision: str = Form(""),
               business_day_rule: str | None = Form(None), who_files: str | None = Form(None),
               approve_reason: str | None = Form(None), reject_reason: str | None = Form(None)):
    run_id = decisions.decide_row(
        conn, row_id=row_id, version=version, decision=decision,
        business_day_rule=business_day_rule, who_files=who_files,
        approve_reason=approve_reason, reject_reason=reject_reason, actor=identity.identity_id)
    # Land on the next rule that still needs a decision, not the top of the page (operator,
    # 2026-11-17; frontend.md W-7). The page places #next; the server's view decides nothing here.
    return RedirectResponse(f"/specialist/runs/{run_id}/g1?after={row_id}#next", status_code=303)


@router.post("/runs/{run_id}/g1/complete")
def complete_g1(request: Request, run_id: str, background: BackgroundTasks,
                conn=Depends(get_conn), identity: Identity = Depends(specialist),
                run_version: int = Form(...)):
    load_run(conn, run_id)
    gates.complete_g1(conn, request.app.state.settings, background.add_task, run_id=run_id,
                      run_version=run_version, actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)


@router.get("/runs/{run_id}/g2")
def confirm_applies(request: Request, run_id: str, conn=Depends(get_conn),
                    identity: Identity = Depends(specialist)):
    return page_g2(request, conn, identity, load_run(conn, run_id))


@router.post("/verdicts/{verdict_id}/decision")
def decide_verdict(verdict_id: str, conn=Depends(get_conn),
                   identity: Identity = Depends(specialist), version: int = Form(...),
                   decision: str = Form(""), value: str | None = Form(None),
                   confirm_reason: str | None = Form(None),
                   override_reason: str | None = Form(None),
                   decide_reason: str | None = Form(None)):
    run_id = decisions.decide_verdict(
        conn, verdict_id=verdict_id, version=version, decision=decision, value=value,
        confirm_reason=confirm_reason, override_reason=override_reason,
        decide_reason=decide_reason, actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}/g2?after={verdict_id}#next", status_code=303)


@router.post("/runs/{run_id}/g2/complete")
def complete_g2(request: Request, run_id: str, background: BackgroundTasks,
                conn=Depends(get_conn), identity: Identity = Depends(specialist),
                run_version: int = Form(...)):
    load_run(conn, run_id)
    gates.complete_g2(conn, request.app.state.settings, background.add_task, run_id=run_id,
                      run_version=run_version, actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)
