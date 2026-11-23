"""T-INT-1 (Tier 1): the first green path, driven in REAL mode against the fake OpenAI.
No real key, no real model, no paid call: every request goes to a server on this machine.

Why this test exists. The stand-in green path (test_green_path.py) proves the pages, the gates and the
date code work end to end. It cannot prove that the same journey works when the agents are real: the
real-mode code path (CrewAI crews, the schema sent to the provider, the trace line per request, the cost
count, the guard that sends only chat completions) is a different path through the same pages. The
SAD gives `@integration.eng` no separate epic: the pages and the backend are one process, so integration
IS the happy path passing end to end (SAD, "Order of work"). This is that test, with the model replaced by
a fake, so wiring bugs are found before any money is spent.

The three Sprint 4 cases, in this file:
  1. SHOULD SUCCEED   test_a_real_mode_review_passes_end_to_end_against_the_fake
  2. SHOULD REFUSE OR ASK A HUMAN   the same test: the planted rule's Approval is refused and it is
     rejected at G1 (code decides, CR-029); the judge's "unsure" is put to the human at G2
  3. SHOULD FAIL CLEARLY   test_a_provider_failure_fails_the_review_clearly

The fake answers by LOOKING at each request (`answer_with`): which model asked, and which document or
row its prompt names. It answers with the stand-in answer key, so the numbers must equal the stand-in
green path's: 5 documents, 7 rules drafted, 6 approved and checked, 5 apply, 22 dates.
"""

import copy
import re
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from backend.db.connection import connect
from backend.main import create_app
from backend.runtime import agents, crews, model_settings
from backend.services import FUND_ID, runs, trace
from backend.services.audit import list_audit
from backend.settings import load_settings
from tests import flow
from tests.fake_openai import TEST_API_KEY, Failure, Reply
from tests.tier1.test_one_request import CHAT

MODELS = {"extract": "gpt-6-test-e", "verify": "gpt-6-test-v", "judge": "gpt-6-test-j"}
ROLE_OF_MODEL = {model: role for role, model in MODELS.items()}
TOKENS = {"extract": (1500, 300), "verify": (1700, 100), "judge": (1000, 80)}      # what each fake reply reports
DEMO_REASON = "Quote doesn't support the rule"


def _text(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def _prompt(body: dict) -> str:
    return "\n".join(message["content"] for message in body["messages"])


def the_answer_key(body: dict):
    """The fake's switch: answer by the MODEL that asked, then by the document or row its prompt names.
    Pure and thread-safe (the fake calls it from its own threads)."""
    role, text = ROLE_OF_MODEL.get(body["model"]), _prompt(body)
    tokens_in, tokens_out = TOKENS.get(role, (0, 0))
    if role == "extract":                       # the extractor sees ONE document: its paragraphs name it
        document = re.search(r"(SRC-[A-Z0-9]+)-P\d", text).group(1)
        answer = {"rows": copy.deepcopy(agents._stand_in("extractor")[document])}
    elif role in ("verify", "judge"):           # both are given ONE row, which names its source paragraph
        paragraph = re.search(r'"source_paragraph_id": "([^"]+)"', text).group(1)
        if role == "verify":
            answer = {"flags": copy.deepcopy(agents._stand_in("verifier").get(paragraph, []))}
        else:
            answer = copy.deepcopy(agents._stand_in("judge")[paragraph])
    else:
        return None                             # a model nobody expected: no opinion, so it is "unscripted"
    return Reply(answer, tokens_in=tokens_in, tokens_out=tokens_out)


@pytest.fixture(autouse=True)
def no_retry_wait(monkeypatch):
    monkeypatch.setattr(crews, "RETRY_WAIT_S", 0)


@pytest.fixture
def real_settings(tmp_path, as_openai):
    """Real mode, pointed at the fake, with CrewAI believing the fake is OpenAI."""
    as_openai.answer_with(the_answer_key)
    return load_settings({
        "AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
        "LLM_MODEL_EXTRACT": MODELS["extract"], "LLM_MODEL_VERIFY": MODELS["verify"],
        "LLM_MODEL_JUDGE": MODELS["judge"], "SESSION_SECRET": "test-only",
        "DATABASE_PATH": str(tmp_path / "real.db")})


def signed_in(settings, identity_id):
    client = TestClient(create_app(settings))
    client.post("/sign-in", data={"identity_id": identity_id})
    return client


@pytest.fixture
def specialist(real_settings):
    return signed_in(real_settings, "specialist-1")


@pytest.fixture
def gp(real_settings):
    return signed_in(real_settings, "gp-1")


@pytest.fixture
def db(real_settings, specialist):                  # after the app, which makes the database
    conn = connect(real_settings.database_path)
    yield conn
    conn.close()


def asked(fake):
    """Which model asked how many times, and every path that was used."""
    return (Counter(ROLE_OF_MODEL[r.body["model"]] for r in fake.requests),
            {r.path for r in fake.requests})


# --- 1 and 2: SHOULD SUCCEED, and SHOULD REFUSE OR ASK A HUMAN ----------------------------------

def test_a_real_mode_review_passes_end_to_end_against_the_fake(
        real_settings, specialist, gp, db, as_openai):
    fake = as_openai
    assert real_settings.agents_mode == "real"

    # --- The start form says it is the real model, and hides the stand-in-only option ------------
    form = _text(specialist.get("/specialist/runs").text)
    assert "Agents: real model" in form and "Make step 1 fail" not in form
    assert "being prepared and checked" in gp.get("/calendar").text

    # --- Start with the demo rule; REAL stage A runs: 5 extractions, then 7 verifications -------
    started = specialist.post("/specialist/runs", data={"demo_planted_row": "true"}, follow_redirects=False)
    assert started.status_code == 303
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    run = runs.get_run(db, run_id)
    assert (run["status"], run["phase"], run["agents_mode"]) == ("ACTIVE", "AT_G1", "real")
    assert db.execute("SELECT spend_activity FROM runs WHERE run_id = ?", (run_id,)).fetchone()[0] == "spike"
    by_role, paths = asked(fake)
    assert by_role == {"extract": 5, "verify": 7} and paths == {CHAT}        # the planted row is verified too
    status_page = _text(specialist.get(f"/specialist/runs/{run_id}").text)
    assert "Stand-in agents" not in status_page and "Demo rule on" in status_page
    assert "The review stops at US$2.50" in status_page

    # --- G1: 7 rules; the planted row's approval is refused by CODE, then it is rejected --------
    assert "Rule 7 of 7" in _text(specialist.get(f"/specialist/runs/{run_id}/g1").text)
    refused = flow.approve_rule_http(specialist, run_id, flow.DEMO_N)
    assert refused.status_code == 409 and "This rule can" in refused.text
    assert "Approval blocked" in specialist.get(f"/specialist/runs/{run_id}/g1").text
    flow.decide_every_rule_http(specialist, run_id)                              # rules 1 to 6
    assert flow.reject_rule_http(specialist, run_id, flow.DEMO_N, DEMO_REASON).status_code == 303
    assert specialist.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1},
                           follow_redirects=False).status_code == 303

    # --- REAL stage B: one judge call per approved rule; G2 puts the "unsure" one to a human ----
    assert runs.get_run(db, run_id)["phase"] == "AT_G2"
    by_role, paths = asked(fake)
    assert by_role == {"extract": 5, "verify": 7, "judge": 6} and paths == {CHAT}
    assert "Statistical report A01" in _text(specialist.get(f"/specialist/runs/{run_id}/g2").text)
    flow.answer_every_verdict_http(specialist, run_id)
    assert specialist.post(f"/specialist/runs/{run_id}/g2/complete", data={"run_version": 2},
                           follow_redirects=False).status_code == 303

    # --- Stage C (code only: no request) and G3: the same counts as the stand-in path ----------
    run = runs.get_run(db, run_id)
    assert (run["phase"], run["counts"]) == ("AT_G3", {"rules": 7, "unsure": 1, "dates": 22})
    assert len(fake.requests) == 18                                              # stage C sent nothing
    assert "being prepared and checked" in gp.get("/calendar").text
    assert flow.publish_http(specialist, run_id).status_code == 303
    assert runs.get_run(db, run_id)["status"] == "COMPLETED"

    # --- The GP's published calendar: 22 dates, and NOT labelled as made with stand-in agents ---
    gp_page = gp.get("/calendar?view=list").text
    words = _text(gp_page)
    assert "Entries in 2027: 22" in words and "May not be required 4" in words
    assert "Made with stand-in agents" not in words and "Stand-in" not in gp_page
    assert "OQ-7" not in gp_page and "Demo" not in words

    # --- The audit log: every step in order, and none of it says "stand-in" (stages A, B and C) ---
    audit = list_audit(db, run_id)
    assert not [a["reason"] for a in audit if "stand-in" in (a["reason"] or "")]
    milestones = [a["reason"] for a in audit if a["event_type"] in ("gate_event", "system")]
    expected = ["Review started", "Demo rule switch on", "Stage A finished", "G1 completed",
                "Stage B finished", "G2 completed", "Stage C finished"]
    assert [m for m in milestones if m in expected] == expected
    assert milestones[-1].startswith("Calendar published (acknowledged 1 rejected rules")
    kinds = [a["event_type"] for a in audit]
    assert kinds.count("agent_output") == 5 + 7 + 6 and kinds.count("decision") == 7 + 6
    assert [a["refusal_code"] for a in audit if a["event_type"] == "refusal"] == ["DEMO_ROW_NOT_APPROVABLE"]

    # --- The trace and the cost: one line per request, real models, real money counted ----------
    lines = trace.list_trace(db, run_id)
    assert len(lines) == 18 == len(fake.requests)
    assert {line["model"] for line in lines} == set(MODELS.values())
    assert {line["spend_activity"] for line in lines} == {"spike"}
    assert {line["request_path"] for line in lines} == {CHAT}
    assert {(line["late"], line["cost_estimated"], line["off_pinned_setting"], line["attempt_n"],
             line["provider_error"]) for line in lines} == {(0, 0, 0, 1, None)}
    expected_cost = sum(model_settings.call_cost_usd(role, *TOKENS[role]) * n
                        for role, n in {"extract": 5, "verify": 7, "judge": 6}.items())
    assert expected_cost > 0
    assert runs.get_run(db, run_id)["cost_so_far"] == pytest.approx(expected_cost)
    refs = {a["trace_ref"] for a in audit if a["event_type"] == "agent_output"}
    assert refs == {trace.record_key(run_id, t["step"], t["stage_attempt"], t["unit_id"], t["attempt_n"]) for t in lines}
    # What the real verifier and judge were asked is what the answer key says: the planted row got no flag.
    assert fake.unscripted == []


def test_the_audit_does_not_claim_stand_in_agents_in_a_real_run(real_settings, specialist, db):
    """A real run's audit log must not say stand-in agents did the work.

    This test FOUND a bug: `store_stage_outputs` wrote "Stage A finished (stand-in)" for every run,
    whatever the mode, so the log people rely on said the opposite of the truth in a real run. It was
    pinned as an expected failure until the fix; the stand-in wording is kept for stand-in runs
    (test_green_path.py asserts it)."""
    specialist.post("/specialist/runs", data={}, follow_redirects=False)
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    said = [a["reason"] for a in list_audit(db, run_id) if "stand-in" in (a["reason"] or "")]
    assert said == [], f"a real run's audit log says stand-in: {said}"
    assert "Stage A finished" in [a["reason"] for a in list_audit(db, run_id)]


# --- 3: SHOULD FAIL CLEARLY ---------------------------------------------------------------------

def test_a_provider_failure_fails_the_review_clearly(real_settings, specialist, gp, db, as_openai):
    """The provider answers 503 for the third document, and for the retry too (DL-43: once more, then
    stop). The review must say so plainly, keep what it cost, store nothing half-done, and send
    nothing after the failure."""
    fake = as_openai

    def third_document_fails(body):
        if ROLE_OF_MODEL.get(body["model"]) == "extract" and "SRC-CNMV-P" in _prompt(body):
            return Failure(503, "Overloaded")
        return the_answer_key(body)
    fake.answer_with(third_document_fails)

    started = specialist.post("/specialist/runs", data={}, follow_redirects=False)
    assert started.status_code == 303
    run_id = runs.list_runs(db, FUND_ID)[0]["run_id"]
    run = runs.get_run(db, run_id)
    assert (run["status"], run["phase"]) == ("FAILED", "A_RUNNING")           # it keeps its phase (DL-46)

    # The page says what happened, in words, and does not pretend the review can go on.
    page = _text(specialist.get(f"/specialist/runs/{run_id}").text)
    assert "Failed" in page and "The model service did not answer in time, or returned an error, twice" in page
    assert "Stand-in" not in page

    # Nothing after the failure was sent; nothing half-done was stored.
    by_role, paths = asked(fake)
    assert by_role == {"extract": 2 + 2} and paths == {CHAT}                    # 2 documents answered, 1 asked twice
    assert db.execute("SELECT COUNT(*) FROM paragraphs WHERE run_id = ?", (run_id,)).fetchone()[0] == 0   # rule 9: nothing half-stored
    failed = db.execute("SELECT unit_id, failure_reason FROM units WHERE status = 'failed'").fetchall()
    assert [tuple(r) for r in failed] == [("SRC-CNMV", "model service")]

    # Both requests that got no answer are in the trace and their cost is counted (it may have been billed).
    failures = [t for t in trace.list_trace(db, run_id) if t["provider_error"]]
    assert [(t["unit_id"], t["attempt_n"]) for t in failures] == [("SRC-CNMV", 1), ("SRC-CNMV", 2)]
    assert all(t["cost_estimated"] == 1 and t["cost_usd"] > 0 for t in failures)
    assert runs.get_run(db, run_id)["cost_so_far"] >= sum(t["cost_usd"] for t in failures)
    assert "being prepared and checked" in gp.get("/calendar").text            # the GP never sees a half-made calendar

