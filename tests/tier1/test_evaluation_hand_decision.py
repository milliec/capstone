"""T-EVALHAND-1 (H-105, DL-61): a person cannot decide on an evaluation review. Tier 1.

On an evaluation run (`spend_activity` `evaluation`, started by `specialist-eval`), six requests made by
anyone other than `specialist-eval` are refused with EVALUATION_NOT_DECIDABLE (409): the row decision,
G1 complete, the verdict decision, G2 complete, publish and decline.

  (1) Each of the six, made as the specialist, is refused with the new code, is audited once, and
      changes nothing (rows, verdicts, run phase and version, publications: every table but the audit).
  (2) The same six, made as `specialist-eval`, are NOT refused: the scripted gates call these same service
      functions and must pass. The guard keys on who acts, never on the route.
  (3) The check is straight after the role check, before every other check: a person gets the same
      refusal in the wrong phase, with a stale version, and on an ended review.
  (4) Not refused: abandon, and reading a page's data.
  (5) An ordinary run is unchanged: the specialist still decides on it.

The evaluation runs are real-mode runs answered by the fake OpenAI (an evaluation run refuses stand-in
mode, T-MODE-1): dummy key, temporary database, `as_openai`. No real call, no real key, no real database.
"""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, decisions, gates, publishing, runs
from backend.services.auth import EVALUATION_ACTOR
from backend.services.refusals import HTTP_STATUS, Refused, sentence
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key

PERSON = flow.SPECIALIST          # "specialist-1": a person signed in as the compliance specialist
CODE = "EVALUATION_NOT_DECIDABLE"
SENTENCE = ("This review is part of the evaluation. The evaluation script makes its decisions, so it "
            "can't be decided here. Nothing was saved.")


def _settings(tmp_path, *, mode="real", activity="evaluation"):
    env = {"AGENTS_MODE": mode, "SPEND_ACTIVITY": activity, "SESSION_SECRET": "test-only",
           "STAND_IN_UNIT_PAUSE_S": "0", "DATABASE_PATH": str(tmp_path / "app.db")}
    if mode == "real":
        env.update({"OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": MODELS["extract"],
                    "LLM_MODEL_VERIFY": MODELS["verify"], "LLM_MODEL_JUDGE": MODELS["judge"]})
    return load_settings(env)


@pytest.fixture
def fake(as_openai):
    as_openai.answer_with(the_answer_key)
    return as_openai


@pytest.fixture
def world(tmp_path, fake):
    settings = _settings(tmp_path)
    init_db(settings.database_path)
    return settings, connect(settings.database_path)


# --- Helpers: take an evaluation run to a gate, acting as `actor` -------------------------------------

def _start(conn, settings, *, started_by=EVALUATION_ACTOR):
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")   # test set-up
    conn.commit()
    return runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID, started_by=started_by,
                          demo_planted_row=False, demo_fail_step1=False)


def _decide_row(conn, run_id, n, actor, version=1):
    return decisions.decide_row(
        conn, row_id=f"ROW-{run_id}-{n}", version=version, decision="approve",
        business_day_rule=flow.DEMO_RULES[n], who_files=flow.DEMO_WHO[n],
        approve_reason=flow.FLAG_REASON if n == flow.FLAGGED_N else None, reject_reason=None, actor=actor)


def _decide_verdict(conn, run_id, n, actor):
    return decisions.decide_verdict(
        conn, verdict_id=f"VER-{run_id}-{n}", version=1, decision="confirm", value="applies",
        confirm_reason=None, override_reason=None, decide_reason=None, actor=actor)


def _complete_g1(conn, settings, run_id, actor):
    return gates.complete_g1(conn, settings, flow.run_now, run_id=run_id, actor=actor,
                             run_version=runs.get_run(conn, run_id)["run_version"])


def _complete_g2(conn, settings, run_id, actor):
    return gates.complete_g2(conn, settings, flow.run_now, run_id=run_id, actor=actor,
                             run_version=runs.get_run(conn, run_id)["run_version"])


def _publish(conn, run_id, actor):
    return flow.publish(conn, run_id, actor=actor)


def _decline(conn, run_id, actor):
    return publishing.decline_calendar(
        conn, calendar_id=f"CAL-{run_id}", actor=actor, decline_reason="Not ready",
        run_version=runs.get_run(conn, run_id)["run_version"])


def _evaluation_run_at(conn, settings, phase):
    """A real evaluation run taken to `phase` by the script identity (the gates are the script's)."""
    run_id = _start(conn, settings)
    if phase != "AT_G1":
        for n in flow.RULES:
            _decide_row(conn, run_id, n, EVALUATION_ACTOR)
        _complete_g1(conn, settings, run_id, EVALUATION_ACTOR)
    if phase == "AT_G3":
        for n in flow.APPLIES_NS:
            _decide_verdict(conn, run_id, n, EVALUATION_ACTOR)
        decisions.decide_verdict(
            conn, verdict_id=f"VER-{run_id}-{flow.UNSURE_N}", version=1, decision="decide", value="applies",
            confirm_reason=None, override_reason=None, decide_reason="Treated as applicable", actor=EVALUATION_ACTOR)
        decisions.decide_verdict(
            conn, verdict_id=f"VER-{run_id}-{flow.DOES_NOT_APPLY_N}", version=1, decision="confirm",
            value="does_not_apply", confirm_reason=None, override_reason=None, decide_reason=None,
            actor=EVALUATION_ACTOR)
        _complete_g2(conn, settings, run_id, EVALUATION_ACTOR)
    assert runs.is_evaluation_run(runs.get_run(conn, run_id))       # a real evaluation run, not a shortcut
    assert runs.get_run(conn, run_id)["phase"] == phase
    return run_id


def _everything_but_the_audit(conn):
    """Every row of every table except the audit log: a refusal may write its own audit entry, nothing else."""
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
        "AND name != 'audit_log' ORDER BY name")]
    return {t: [tuple(r) for r in conn.execute(f"SELECT * FROM {t} ORDER BY 1, 2")] for t in tables}


def _refusal_entries(conn):
    return [dict(r) for r in conn.execute(
        "SELECT actor, refusal_code, run_id FROM audit_log WHERE event_type = 'refusal'")]


# The six requests: (name, the phase the review is at, the call as `actor`).
SIX = [
    ("decide_row", "AT_G1", lambda c, s, r, a: _decide_row(c, r, 1, a)),
    ("complete_g1", "AT_G1", lambda c, s, r, a: _complete_g1(c, s, r, a)),
    ("decide_verdict", "AT_G2", lambda c, s, r, a: _decide_verdict(c, r, 1, a)),
    ("complete_g2", "AT_G2", lambda c, s, r, a: _complete_g2(c, s, r, a)),
    ("publish", "AT_G3", lambda c, s, r, a: _publish(c, r, a)),
    ("decline", "AT_G3", lambda c, s, r, a: _decline(c, r, a)),
]


# --- (1) a person is refused, audited, and nothing changes ---------------------------------------------

def test_the_code_is_409_and_has_its_one_sentence():
    assert HTTP_STATUS[CODE] == 409
    assert sentence(CODE) == SENTENCE


@pytest.mark.parametrize("name,phase,call", SIX, ids=[s[0] for s in SIX])
def test_a_person_is_refused_on_an_evaluation_run(world, name, phase, call):
    settings, conn = world
    run_id = _evaluation_run_at(conn, settings, phase)
    before, audits = _everything_but_the_audit(conn), _refusal_entries(conn)

    with pytest.raises(Refused) as caught:
        call(conn, settings, run_id, PERSON)

    refusal = caught.value.refusal
    assert (refusal.code, refusal.http_status, refusal.sentence) == (CODE, 409, SENTENCE)
    assert _refusal_entries(conn) == audits + [{"actor": PERSON, "refusal_code": CODE, "run_id": run_id}]
    assert _everything_but_the_audit(conn) == before            # rows, verdicts, run version, publications


# --- (2) the script is not refused ----------------------------------------------------------------------

def test_the_script_passes_all_five_gate_requests_and_the_decline(world):
    """Rows, G1, verdicts, G2 and publish as `specialist-eval` all go through: that is the whole of
    `_evaluation_run_at`, plus the publish. A second run takes the decline."""
    settings, conn = world
    run_id = _evaluation_run_at(conn, settings, "AT_G3")      # row decision, G1, verdicts, G2: no refusal
    _publish(conn, run_id, EVALUATION_ACTOR)
    assert runs.get_run(conn, run_id)["status"] == "COMPLETED"

    second = _evaluation_run_at(conn, settings, "AT_G3")
    _decline(conn, second, EVALUATION_ACTOR)
    assert runs.get_run(conn, second)["status"] == "DECLINED"
    assert not [e for e in _refusal_entries(conn) if e["refusal_code"] == CODE]


# --- (3) straight after the role check: the same refusal in every state ----------------------------------

def test_a_person_gets_the_same_refusal_in_the_wrong_phase_with_a_stale_version_and_on_an_ended_run(world):
    settings, conn = world
    run_id = _evaluation_run_at(conn, settings, "AT_G2")
    for call in (
            lambda: _decide_row(conn, run_id, 1, PERSON),                 # the wrong phase (G1 is over)
            lambda: gates.complete_g2(conn, settings, flow.run_now, run_id=run_id, run_version=99,
                                      actor=PERSON),                      # a stale page, and an unfinished gate
            lambda: _complete_g2(conn, settings, run_id, PERSON),         # an unfinished gate
            lambda: _complete_g1(conn, settings, run_id, PERSON)):        # the wrong gate
        with pytest.raises(Refused) as caught:
            call()
        assert caught.value.refusal.code == CODE
    # An ended review: anyone else would get RUN_NOT_ACTIVE.
    runs.abandon_run(conn, run_id=run_id, run_version=runs.get_run(conn, run_id)["run_version"],
                     reason="Closing it", actor=PERSON)
    with pytest.raises(Refused) as caught:
        _decide_verdict(conn, run_id, 1, PERSON)
    assert caught.value.refusal.code == CODE


# --- (4) abandon and reading are not refused ---------------------------------------------------------------

def test_a_person_can_abandon_an_evaluation_review_and_read_its_pages(world):
    settings, conn = world
    run_id = _evaluation_run_at(conn, settings, "AT_G1")
    assert decisions.get_g1_view(conn, runs.get_run(conn, run_id))        # reading is not guarded
    runs.abandon_run(conn, run_id=run_id, run_version=1, reason="The script left it stuck", actor=PERSON)
    assert runs.get_run(conn, run_id)["status"] == "ABANDONED"
    assert not [e for e in _refusal_entries(conn) if e["refusal_code"] == CODE]


# --- (5) an ordinary run is unchanged ----------------------------------------------------------------------

def test_an_ordinary_run_is_unchanged(tmp_path):
    settings = _settings(tmp_path, mode="stand_in", activity="")
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    assert not runs.is_evaluation_run(runs.get_run(conn, run_id))
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n])
    flow.finish_g1(conn, settings, run_id)
    assert runs.get_run(conn, run_id)["phase"] == "AT_G2"
    assert not _refusal_entries(conn)
