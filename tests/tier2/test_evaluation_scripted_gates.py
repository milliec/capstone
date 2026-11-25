"""The scripted G1, G2 and G3 and the stop rules, PR 4b (H-097, sad.md EC-R2, DL-60).

`python -m backend.evaluation run --go` now goes on after Stage A: it decides G1, G2 and G3 by script as
`specialist-eval`, through the same service functions the pages use, grades Stage B and exports the trace.
At every gate it first asks the stop rules (backend/evaluation/stop_rules.py), and on any stop it ends the
run and says why.

How these tests stay safe (H-097 checks), as in the 4a tests:
  * Real mode against the fake OpenAI on this machine, the dummy key, temporary databases, a spike
    database that does not exist and a temporary report/export folder. No real call; no file under
    `data/` is touched and none is opened.
"""

import copy

import pytest

from backend.evaluation import run_starter, scripted_gates, stop_rules
from backend.runtime import crews
from backend.services import FUND_ID, calendar, runs
from backend.services.auth import EVALUATION_ACTOR
from tests.fake_openai import Failure, Reply
from tests.tier1.test_real_mode_green_path import ROLE_OF_MODEL, the_answer_key
from tests.tier2.test_evaluation_run_starter import Console, app_db, make_env, start


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def spike_db(tmp_path, monkeypatch):
    nowhere = tmp_path / "spike" / "spike.db"          # does not exist: counts as 0, never created
    monkeypatch.setattr(run_starter, "SPIKE_DB", nowhere)
    return nowhere


@pytest.fixture
def fake(as_openai):
    as_openai.answer_with(the_answer_key)
    return as_openai


@pytest.fixture
def env(tmp_path):
    return make_env(tmp_path)


def go(env, spike_db, tmp_path, fake=None):
    """Run the command with --go and the right words. Returns (exit code, console, connection, run)."""
    console = Console()
    code = start(env, spike_db, tmp_path, console, "--go")
    conn = app_db(env)
    return code, console, conn, runs.list_runs(conn, FUND_ID)[0]


def decisions_by_code(conn, run_id):
    """{OBL code: row_decisions row}: each stored row is matched to its code by the paragraph it cites."""
    from backend.evaluation import golden
    key = golden.load_golden_set()
    found = {}
    for d in conn.execute("SELECT d.*, r.source_paragraph_id FROM row_decisions d "
                          "JOIN rows r ON r.row_id = d.row_id WHERE r.run_id = ?", (run_id,)):
        row = key.row_for_paragraph(d["source_paragraph_id"])
        if row:
            found.setdefault(row.code, d)
    return found


# --- A clean run goes through G1, G2 and G3 ---------------------------------------------------------

def test_a_clean_run_goes_through_g1_g2_and_g3_by_script(env, spike_db, tmp_path, fake):
    code, console, _, run = go(env, spike_db, tmp_path)
    assert code == 0, console.text
    assert (run["status"], run["phase"]) == ("COMPLETED", "AT_G3")
    assert run["counts"] == {"rules": 6, "unsure": 1, "dates": 22}        # the demo calendar (KEY §4)
    by_model = {}
    for request in fake.requests:
        by_model[ROLE_OF_MODEL[request.body["model"]]] = by_model.get(ROLE_OF_MODEL[request.body["model"]], 0) + 1
    # 5 + 6 + 6 for the run, plus the two copy calls made after G3: the injection (extract) and I-1 (verify)
    assert by_model == {"extract": 6, "verify": 7, "judge": 6} and len(fake.requests) == 19
    assert "G1 by script: 6 rules approved, 0 rejected" in console.text
    assert "G2 by script: 5 verdicts confirmed, 1 unsure resolved as applies" in console.text
    assert "G3 by script: published" in console.text and "Done:" in console.text


def test_every_decision_is_made_as_specialist_eval_and_the_audit_log_says_so(env, spike_db, tmp_path, fake):
    _, _, conn, run = go(env, spike_db, tmp_path)
    decided_by = {r[0] for r in conn.execute("SELECT decided_by FROM row_decisions")} | \
                 {r[0] for r in conn.execute("SELECT decided_by FROM verdict_decisions")}
    assert decided_by == {EVALUATION_ACTOR}
    actors = {r[0] for r in conn.execute(
        "SELECT DISTINCT actor FROM audit_log WHERE run_id = ? AND event_type IN ('decision', 'gate_event')",
        (run["run_id"],))}
    assert actors == {EVALUATION_ACTOR}                      # every gate step, and nobody else
    reasons = [r["reason"] for r in conn.execute(
        "SELECT reason FROM audit_log WHERE run_id = ? AND event_type = 'gate_event' ORDER BY audit_id",
        (run["run_id"],))]
    assert [r for r in reasons if r in ("G1 completed", "G2 completed")] == ["G1 completed", "G2 completed"]
    assert reasons[-1].startswith("Calendar published (acknowledged 0 rejected rules")
    assert conn.execute("SELECT published_by FROM publications").fetchone()[0] == EVALUATION_ACTOR


def test_the_decisions_are_the_demo_decisions_of_the_answer_key(env, spike_db, tmp_path, fake):
    _, _, conn, run = go(env, spike_db, tmp_path)
    got = decisions_by_code(conn, run["run_id"])
    assert set(got) == {f"OBL-0{n}" for n in range(1, 7)}
    assert {c: d["decision"] for c, d in got.items()} == {c: "approve" for c in got}
    assert {c: d["business_day_rule"] for c, d in got.items()} == scripted_gates.BUSINESS_DAY_RULE
    # KEY §5: "who files" is set only where the source is silent (OBL-02, 03, 05, 06)
    assert {c: d["who_files"] for c, d in got.items() if d["who_files"]} == scripted_gates.WHO_FILES
    assert set(scripted_gates.WHO_FILES) == {"OBL-02", "OBL-03", "OBL-05", "OBL-06"}
    assert got["OBL-03"]["reason"] == scripted_gates.APPROVE_REASON["OBL-03"]       # conflict C-1
    assert got["OBL-05"]["reason"] == scripted_gates.APPROVE_REASON["OBL-05"]       # conflict C-2
    verdicts = {r["row_id"]: r for r in conn.execute("SELECT * FROM verdict_decisions d JOIN verdicts v "
                                                    "ON v.verdict_id = d.verdict_id")}
    unsure = [v for v in verdicts.values() if v["verdict"] == "unsure"]
    assert len(unsure) == 1 and (unsure[0]["decision"], unsure[0]["final_value"]) == ("decide", "applies")
    assert unsure[0]["reason"] == "Treated as applicable until CNMV registration is confirmed"
    assert {v["decision"] for v in verdicts.values() if v["verdict"] != "unsure"} == {"confirm"}


def test_the_answer_key_table_agrees_with_the_stories_demo_choices():
    """flow.DEMO_RULES and DEMO_WHO are the stand-in green path's version of the same decisions."""
    from tests import flow
    assert [scripted_gates.BUSINESS_DAY_RULE[f"OBL-0{n}"] for n in flow.RULES] == \
        [flow.DEMO_RULES[n] for n in flow.RULES]
    assert {f"OBL-0{n}": who for n, who in flow.DEMO_WHO.items() if who} == scripted_gates.WHO_FILES


# --- The publish is real but never the live calendar (DL-60) ----------------------------------------

def test_the_scripted_publish_is_real_but_the_general_partner_still_sees_being_prepared(
        env, spike_db, tmp_path, fake):
    _, _, conn, _ = go(env, spike_db, tmp_path)
    assert conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 1       # a real insert (EC-R2)
    assert calendar.get_published_calendar(conn, FUND_ID) is None                      # DL-60, H-099


# --- What the script writes out ----------------------------------------------------------------------

def test_both_reports_and_a_matching_trace_export_are_saved_in_the_temporary_folder(
        env, spike_db, tmp_path, fake):
    from backend.evaluation import trace_export
    _, console, conn, run = go(env, spike_db, tmp_path)
    folder = tmp_path / "logs" / run["run_id"]
    assert (folder / "stage-a-report-1.json").exists() and (folder / "stage-b-report-1.json").exists()
    assert trace_export.check_export(conn, run["run_id"], tmp_path / "logs").ok
    assert len(list(conn.execute("SELECT 1 FROM trace WHERE run_id = ?", (run["run_id"],)))) == 19
    assert "Trace export: 19 records" in console.text


# --- Rows the key does not expect, and rows that cannot be approved --------------------------------

def test_an_extra_row_is_rejected_with_a_reason_and_listed_at_g3(env, spike_db, tmp_path, fake):
    done = []

    def one_extra_row(body):
        reply = the_answer_key(body)
        if ROLE_OF_MODEL.get(body["model"]) == "extract" and not done:
            done.append(1)
            rows = reply.content["rows"]
            rows.append(copy.deepcopy(rows[0]))        # a second row on the same paragraph: an extra
        return reply
    fake.answer_with(one_extra_row)
    code, console, conn, _ = go(env, spike_db, tmp_path)
    assert done and code == 0, console.text
    assert "G1 by script: 6 rules approved, 1 rejected" in console.text
    rejected = conn.execute("SELECT reason, decided_by FROM row_decisions WHERE decision = 'reject'").fetchall()
    assert [(r["reason"], r["decided_by"]) for r in rejected] == \
        [(scripted_gates.REJECT_EXTRA_REASON, EVALUATION_ACTOR)]
    last = conn.execute("SELECT reason FROM audit_log WHERE event_type = 'gate_event' ORDER BY audit_id DESC"
                        ).fetchone()[0]
    assert last.startswith("Calendar published (acknowledged 1 rejected rules")      # the page's own list


# --- The stop rules ------------------------------------------------------------------------------------

def audit_stop_reason(conn, run_id):
    row = conn.execute("SELECT actor, reason FROM audit_log WHERE run_id = ? AND event_type = 'gate_event' "
                       "ORDER BY audit_id DESC", (run_id,)).fetchone()
    return row["actor"], row["reason"]


def test_a_stage_b_failure_stops_before_g2_and_nothing_is_published(env, spike_db, tmp_path, fake):
    fake.answer_with(lambda body: Failure(status=400) if ROLE_OF_MODEL.get(body["model"]) == "judge"
                     else the_answer_key(body))
    code, console, conn, run = go(env, spike_db, tmp_path)
    assert code == 1 and "STOPPED" in console.text
    assert run["status"] in ("FAILED", "ABANDONED")
    assert conn.execute("SELECT COUNT(*) FROM verdict_decisions").fetchone()[0] == 0     # G2 never began
    assert conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0
    assert calendar.get_published_calendar(conn, FUND_ID) is None


def test_an_invalid_stage_b_answer_stops_the_run(env, spike_db, tmp_path, fake):
    fake.answer_with(lambda body: Reply("this is not the schema") if ROLE_OF_MODEL.get(body["model"]) == "judge"
                     else the_answer_key(body))
    code, console, conn, run = go(env, spike_db, tmp_path)
    assert code == 1 and run["status"] in ("FAILED", "ABANDONED")
    assert conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0
    assert "invalid" in console.text.lower()


def test_a_stopped_run_still_exports_its_whole_trace(env, spike_db, tmp_path, fake):
    from backend.evaluation import trace_export
    fake.answer_with(lambda body: Reply("this is not the schema") if ROLE_OF_MODEL.get(body["model"]) == "judge"
                     else the_answer_key(body))
    _, console, conn, run = go(env, spike_db, tmp_path)
    assert trace_export.check_export(conn, run["run_id"], tmp_path / "logs").ok
    assert "Trace export:" in console.text


def test_when_no_rule_can_be_approved_the_script_stops_at_g1_and_ends_the_run(env, spike_db, tmp_path, fake):
    def altered_quotes(body):
        reply = the_answer_key(body)
        if ROLE_OF_MODEL.get(body["model"]) == "extract":
            for row in reply.content["rows"]:
                row["quote"] = "A sentence the paragraph does not contain at all."
        return reply
    fake.answer_with(altered_quotes)
    code, console, conn, run = go(env, spike_db, tmp_path)
    assert code == 1 and "no rule was approved" in console.text and run["status"] == "ABANDONED" and run["phase"] == "AT_G1"
    assert not [r for r in fake.requests if ROLE_OF_MODEL[r.body["model"]] == "judge"]    # Stage B never ran
    actor, reason = audit_stop_reason(conn, run["run_id"])
    assert actor == EVALUATION_ACTOR and "no rule was approved" in reason


def test_a_step_the_service_refuses_stops_the_run_and_says_what_was_refused(
        env, spike_db, tmp_path, fake, monkeypatch):
    monkeypatch.setitem(scripted_gates.BUSINESS_DAY_RULE, "OBL-01", "not_confirmed")    # the service says no
    code, console, conn, run = go(env, spike_db, tmp_path)
    assert code == 1 and run["status"] == "ABANDONED" and run["phase"] == "AT_G1"
    assert "refused by the service" in console.text
    assert conn.execute("SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal' AND run_id = ?",
                        (run["run_id"],)).fetchone()[0] >= 1                              # the refusal is audited
    assert conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0


def test_an_error_nobody_listed_stops_the_run_at_the_gate_it_reached(
        env, spike_db, tmp_path, fake, monkeypatch):
    def broken(conn, run_id):
        raise RuntimeError("boom")
    monkeypatch.setattr(scripted_gates, "publish_g3", broken)
    code, console, conn, run = go(env, spike_db, tmp_path)
    assert code == 1 and run["status"] == "ABANDONED" and run["phase"] == "AT_G3"
    assert "unexpected error (RuntimeError): boom" in console.text
    assert conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0] == 0


def test_a_stopped_run_leaves_no_review_in_progress(env, spike_db, tmp_path, fake, monkeypatch):
    monkeypatch.setitem(scripted_gates.BUSINESS_DAY_RULE, "OBL-01", "not_confirmed")
    _, _, conn, _ = go(env, spike_db, tmp_path)
    assert runs.get_active_run(conn, FUND_ID) is None            # the next evaluation run can start


def test_the_script_never_sends_a_request_after_it_has_stopped(env, spike_db, tmp_path, fake, monkeypatch):
    monkeypatch.setitem(scripted_gates.BUSINESS_DAY_RULE, "OBL-01", "not_confirmed")
    go(env, spike_db, tmp_path)
    assert len(fake.requests) == 11                              # Stage A only: no judge call


# --- stop_rules.problems() on its own ----------------------------------------------------------------

@pytest.fixture
def at_g1(env, spike_db, tmp_path, fake, monkeypatch):
    monkeypatch.setitem(scripted_gates.BUSINESS_DAY_RULE, "OBL-01", "not_confirmed")  # stop right after Stage A
    _, _, conn, run = go(env, spike_db, tmp_path)
    conn.execute("UPDATE runs SET status = 'ACTIVE' WHERE run_id = ?", (run["run_id"],))
    conn.commit()
    return conn, run["run_id"]


def test_a_clean_run_at_the_expected_gate_has_no_problem(at_g1):
    conn, run_id = at_g1
    assert stop_rules.problems(conn, run_id, expect_phase="AT_G1") == []


def test_a_run_at_another_gate_than_expected_is_a_problem(at_g1):
    conn, run_id = at_g1
    [reason] = stop_rules.problems(conn, run_id, expect_phase="AT_G2")
    assert "AT_G1" in reason and "AT_G2" in reason


def test_a_run_that_is_not_active_is_a_problem(at_g1):
    conn, run_id = at_g1
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE run_id = ?", (run_id,))
    conn.commit()
    assert stop_rules.problems(conn, run_id, expect_phase="AT_G1") == ["the run is ABANDONED, not ACTIVE"]


def test_a_failed_unit_is_named_with_its_reason_not_just_as_a_failed_run(at_g1):
    conn, run_id = at_g1
    conn.execute("UPDATE units SET status = 'failed', failure_reason = 'model service' "
                 "WHERE rowid = (SELECT MIN(rowid) FROM units WHERE run_id = ?)", (run_id,))
    conn.commit()
    [reason] = stop_rules.problems(conn, run_id, expect_phase="AT_G1")
    assert reason.endswith("failed: model service")

