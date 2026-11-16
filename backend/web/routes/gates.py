"""Page 4 · Check the rules (G1), page 5 · Confirm what applies (G2), and their POST forms."""

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import RedirectResponse

from backend.services import decisions, gates
from backend.services.auth import Identity
from backend.web.deps import get_conn, render, specialist
from backend.web.routes.runs import load_run

router = APIRouter(prefix="/specialist")


@router.get("/runs/{run_id}/g1")
def check_rules(request: Request, run_id: str, conn=Depends(get_conn),
                identity: Identity = Depends(specialist)):
    run = load_run(conn, run_id)
    return render(request, conn, "pages/check_rules.html", identity, run=run,
                  view=decisions.get_g1_view(conn, run))


@router.post("/rows/{row_id}/decision")
def decide_row(row_id: str, conn=Depends(get_conn), identity: Identity = Depends(specialist),
               version: int = Form(...), decision: str = Form(""),
               business_day_rule: str | None = Form(None), who_files: str | None = Form(None),
               approve_reason: str | None = Form(None), reject_reason: str | None = Form(None)):
    run_id = decisions.decide_row(
        conn, row_id=row_id, version=version, decision=decision,
        business_day_rule=business_day_rule, who_files=who_files,
        approve_reason=approve_reason, reject_reason=reject_reason, actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}/g1", status_code=303)


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
    run = load_run(conn, run_id)
    return render(request, conn, "pages/confirm_applies.html", identity, run=run,
                  view=decisions.get_g2_view(conn, run))


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
    return RedirectResponse(f"/specialist/runs/{run_id}/g2", status_code=303)


@router.post("/runs/{run_id}/g2/complete")
def complete_g2(request: Request, run_id: str, background: BackgroundTasks,
                conn=Depends(get_conn), identity: Identity = Depends(specialist),
                run_version: int = Form(...)):
    load_run(conn, run_id)
    gates.complete_g2(conn, request.app.state.settings, background.add_task, run_id=run_id,
                      run_version=run_version, actor=identity.identity_id)
    return RedirectResponse(f"/specialist/runs/{run_id}", status_code=303)
