"""The planted demo row (CR-029, DL-31, DL-44; block B7): T-DEMO-1 and T-DEMO-2 (Tier 1). No model.

T-DEMO-1: switch off → 6 rows, no demo row, no switch entry in the audit log; switch on → 7 rows,
the 7th marked origin "demo", with a quote-check pass and a verifier result, and the switch entry
exists; reject it → logged, and it appears in the G3 rejected list.
T-DEMO-2: approve the demo row, with and without a reason and with each business-day rule → every
request refused and logged; the row stays pending; G1 cannot complete until it is rejected.
(The "evaluation run with the switch on → refused" part needs the evaluation runner, B8.)
"""

import itertools

import pytest
import yaml

from backend.db.connection import connect, init_db
from backend.domain import sources
from backend.domain.quote_check import check_quote
from backend.services import calendar as calendar_service
from backend.services import decisions, runs, trace
from backend.services.refusals import Refused
from backend.settings import ROOT
from tests import flow

FIXTURE = ROOT / "config/demo/planted-row.yaml"


@pytest.fixture
def conn(settings):
    init_db(settings.database_path)
    return connect(settings.database_path)


def _rows(conn, run_id):
    return [dict(r) for r in conn.execute(
        """SELECT r.*, q.result AS quote_result FROM rows r JOIN quote_checks q
           ON q.row_id = r.row_id WHERE r.run_id = ? ORDER BY r.rowid""", (run_id,))]


def _switch_entries(conn, run_id):
    return conn.execute("SELECT COUNT(*) FROM audit_log WHERE run_id = ? AND reason LIKE ?",
                        (run_id, "%demo%switch%")).fetchone()[0]


# --- The fixture -----------------------------------------------------------------------------

def test_the_fixture_quote_is_real_but_does_not_state_the_rule():
    row = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    paragraphs = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    assert check_quote(row["quote"], row["source_paragraph_id"], paragraphs).passed   # genuine
    # ... but it states no deadline: no number of days, no "month", no "within" or "by".
    quote = row["quote"].lower()
    assert not any(w in quote for w in ("day", "month", "within", "no later", " by "))
    assert "OBL-" not in FIXTURE.read_text(encoding="utf-8")                          # CR-016


# --- T-DEMO-1 --------------------------------------------------------------------------------

def test_demo_1_switch_off_gives_six_rows_and_no_switch_entry(conn, settings):
    run_id = flow.start_to_g1(conn, settings, demo=False)
    rows = _rows(conn, run_id)
    assert len(rows) == 6 and {r["origin"] for r in rows} == {"model"}
    assert _switch_entries(conn, run_id) == 0


def test_demo_1_switch_on_adds_a_seventh_demo_row_checked_like_the_others(conn, settings):
    run_id = flow.start_to_g1(conn, settings, demo=True)
    rows = _rows(conn, run_id)
    assert len(rows) == 7
    demo = rows[6]
    assert (demo["origin"], demo["row_id"]) == ("demo", f"ROW-{run_id}-7")
    assert demo["quote_result"] == "pass"                                  # the quote is genuine
    verifier = [t for t in trace.list_trace(conn, run_id)
                if t["step"] == "check_conflicts" and t["unit_id"] == demo["row_id"]]
    assert len(verifier) == 1 and verifier[0]["parsed_output"]             # the verifier ran (SOQ-22)
    assert _switch_entries(conn, run_id) == 1
    view = decisions.get_g1_view(conn, runs.get_run(conn, run_id))["rows"][6]
    assert view["needs_attention"] == ["Demo"] and view["status"] == "To decide"


def test_demo_1_rejecting_it_is_logged_and_it_appears_in_the_g3_rejected_list(conn, settings):
    run_id = flow.to_g3(conn, settings, demo=True)
    demo_id = f"ROW-{run_id}-7"
    logged = conn.execute("SELECT reason FROM audit_log WHERE subject_id = ? AND "
                          "event_type = 'decision'", (demo_id,)).fetchone()
    assert logged["reason"].startswith("reject")
    g3 = calendar_service.get_g3_view(conn, runs.get_run(conn, run_id))
    assert [(r["row_id"], r["is_demo"]) for r in g3["rejected_rows"]] == [(demo_id, True)]
    assert all(e["row_id"] != demo_id for e in g3["entries"])            # never on a calendar


# --- T-DEMO-2 --------------------------------------------------------------------------------

@pytest.mark.parametrize("reason,rule", itertools.product(
    [None, "It looks right to me"], ["roll_forward", "roll_backward", "no_roll", None]))
def test_demo_2_every_approval_is_refused_and_logged(conn, settings, reason, rule):
    run_id = flow.start_to_g1(conn, settings, demo=True)
    before = conn.execute("SELECT COUNT(*) FROM audit_log WHERE refusal_code = ?",
                          ("DEMO_ROW_NOT_APPROVABLE",)).fetchone()[0]
    with pytest.raises(Refused) as caught:
        flow.approve_rule(conn, run_id, flow.DEMO_N, rule=rule, reason=reason)
    refusal = caught.value.refusal
    assert (refusal.code, refusal.anchor) == ("DEMO_ROW_NOT_APPROVABLE", "row-7")
    assert refusal.sentence.startswith("This rule can't be approved. The quote is genuine")
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE refusal_code = ?",
                        ("DEMO_ROW_NOT_APPROVABLE",)).fetchone()[0] == before + 1
    assert conn.execute("SELECT COUNT(*) FROM row_decisions").fetchone()[0] == 0   # still pending


def test_demo_2_after_a_refusal_it_reads_approval_blocked_and_g1_waits_for_the_reject(
        conn, settings):
    run_id = flow.start_to_g1(conn, settings, demo=True)
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n])
    with pytest.raises(Refused):
        flow.approve_rule(conn, run_id, flow.DEMO_N)
    view = decisions.get_g1_view(conn, runs.get_run(conn, run_id))["rows"][6]
    assert (view["status"], view["status_tone"], view["decision"]) == \
        ("Approval blocked", "problem", None)
    with pytest.raises(Refused) as caught:
        flow.finish_g1(conn, settings, run_id)                             # 1 rule still undecided
    assert caught.value.refusal.code == "GATE_INCOMPLETE"
    flow.reject_rule(conn, run_id, flow.DEMO_N, "Quote doesn't support the rule")
    assert decisions.get_g1_view(conn, runs.get_run(conn, run_id))["rows"][6]["status"] == "Rejected"
    flow.finish_g1(conn, settings, run_id)
    assert runs.get_run(conn, run_id)["phase"] == "AT_G2"


def test_demo_2_through_the_page_the_refusal_shows_beside_the_demo_rule(specialist_client, db):
    specialist_client.post("/specialist/runs", data={"demo_planted_row": "true"})
    run_id = runs.list_runs(db, flow.FUND_ID)[0]["run_id"]
    page = flow.approve_rule_http(specialist_client, run_id, flow.DEMO_N)
    assert page.status_code == 409
    assert "This rule can&#39;t be approved" in page.text or "This rule can't be approved" in page.text
    again = specialist_client.get(f"/specialist/runs/{run_id}/g1").text
    assert "Approval blocked" in again                                    # still there after reload
