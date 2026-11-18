"""T-LEAK-1, prompt half (CR-016, Tier 1): every task prompt, rendered from the REAL mock files, is
free of the answers. Plus the part of T-MODE-1 about the role harness: at its cap, the next real
call is refused (CR-030, EC-R10). No model, no CrewAI.

T-LEAK-1 fails if a prompt contains (a) "Test note", "Planted conflict" or "correct verdict",
(b) the "Decides" heading or any value from that column, (c) the text of any blockquote in the
mock files, or (d) any answer-key ID (OBL-, C-1, C-2, I-1, AMD-). Phrases are matched as written.
"""

import re

import pytest

from backend.db.connection import connect, init_db
from backend.domain import sources
from backend.domain.fund_facts import load_fund_facts
from backend.domain.quote_check import check_quote
from backend.runtime import agents, harness, prompts
from backend.settings import ROOT
from tests import flow

MOCK = ROOT / "project-context/1.define/mock-data"


def _rendered_prompts(settings):
    """Every prompt a stand-in review would send: 5 extractions, 6 checks, 6 judgements."""
    paragraphs = {p["paragraph_id"]: p["text"] for p in sources.load_paragraphs()}
    documents = sources.list_documents()
    types = {d["id"]: d["type"] for d in documents}
    codes = list(sources.list_recipients())
    facts = load_fund_facts()
    rendered, rows = [], []
    for d in documents:
        if d["type"] != "primary":
            continue
        own = {pid: t for pid, t in paragraphs.items() if pid.startswith(d["id"] + "-P")}
        rendered.append(("extract_rows", d["id"], prompts.render("extract_rows", prompts.extractor_inputs(
            document_id=d["id"], document_title=d["title"], paragraphs=own, recipient_codes=codes))))
        rows += [r.model_dump() for r in agents.extract_rows(
            settings, document_id=d["id"], paragraphs=own, recipient_codes=codes)]
    for row in rows:
        passed = check_quote(row["quote"], row["source_paragraph_id"], paragraphs).passed
        rendered.append(("check_conflicts", row["source_paragraph_id"], prompts.render(
            "check_conflicts", prompts.verifier_inputs(row=row, quote_check_passed=passed,
                                                       sources=paragraphs, document_types=types))))
        rendered.append(("judge_applicability", row["source_paragraph_id"], prompts.render(
            "judge_applicability", prompts.judge_inputs(row=row, fund_facts=facts))))
    return rendered


def _text(prompt: dict) -> str:
    return "\n".join(prompt.values())


def _decides_values():
    """Every cell of the fund profile's "Decides" column, as written."""
    text = (MOCK / "mock-fund-profile.md").read_text(encoding="utf-8")
    table = text.split("## Applicability facts", 1)[1].split("\n## ", 1)[0]
    rows = [line.strip().strip("|").split("|") for line in table.splitlines() if line.startswith("|")]
    return [cells[3].strip() for cells in rows[2:]]


def _blockquotes():
    quoted = []
    for name in ("mock-regulatory-sources.md", "mock-fund-profile.md"):
        for line in (MOCK / name).read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith(">"):
                q = " ".join(re.sub(r"[>*_`]", "", line).split())
                if len(q) > 15:
                    quoted.append(q)
    return quoted


def test_there_are_17_prompts_one_per_call(settings):
    assert [step for step, _, _ in _rendered_prompts(settings)].count("extract_rows") == 5
    assert len(_rendered_prompts(settings)) == 5 + 6 + 6


def test_leak_1_no_prompt_carries_the_answers(settings):
    decides, quoted = _decides_values(), _blockquotes()
    assert decides and quoted   # the test reads real content, so it cannot pass by reading nothing
    for step, unit, prompt in _rendered_prompts(settings):
        text = _text(prompt)
        flat = " ".join(text.split())
        where = f"{step} {unit}"
        for phrase in ("Test note", "Planted conflict", "correct verdict", "Decides",
                       "expected-obligation-library"):
            assert phrase not in text, (where, phrase)                       # (a), (b) heading
        for value in decides:
            # As written, as a whole phrase: "RBE" must not trip on the document ID "SRC-RBELAW".
            assert not re.search(rf"(?<![A-Za-z0-9]){re.escape(value)}(?![A-Za-z0-9])", text), \
                (where, value)                                               # (b) values
        for q in quoted:
            assert q not in flat, (where, q)                                 # (c)
        for key_id in ("OBL-", "AMD-", "C-1", "C-2", "I-1"):
            assert key_id not in text, (where, key_id)                       # (d)


def test_the_extractor_sees_only_its_own_document(settings):
    for step, unit, prompt in _rendered_prompts(settings):
        if step != "extract_rows":
            continue
        others = {d["id"] for d in sources.list_documents()} - {unit}
        # The invented one-shot example (SRC-SAMPLE) is meant to be there; no OTHER mock document is.
        found = set(re.findall(r"SRC-[A-Z0-9]+(?=-P\d)", prompt["description"])) - {"SRC-SAMPLE"}
        assert found == {unit} and not (found & others), unit


def test_the_judge_sees_facts_as_id_fact_and_value_only(settings):
    judge = next(p for s, _, p in _rendered_prompts(settings) if s == "judge_applicability")
    assert "FACT-04 Registered with the CNMV for marketing in Spain: " in judge["description"]
    assert "EVT-01 A new investor's holding crossed" in judge["description"]
    assert "2027-01-31" not in judge["description"]   # event dates are for the date engine only


# --- The role harness (T-MODE-1 "the harness at its cap → the next call is refused") ---------

@pytest.mark.parametrize("activity,cap", [("spike", 70), ("tuning", 60)])
def test_the_harness_refuses_the_call_after_the_cap(settings, activity, cap):
    init_db(settings.database_path)
    conn = connect(settings.database_path)
    run_id = flow.start_to_g1(conn, settings)
    insert = ("INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
              "prompt_version, input_hash, spend_activity) "
              "VALUES (?, 'FND-DEMO-01', 'extract_rows', 1, ?, 1, 'now', 'v', 'h', ?)")
    for n in range(cap - 1):
        conn.execute(insert, (run_id, f"U{n}", activity))
    conn.commit()
    harness.check_call_allowed(conn, activity)                 # call number `cap` is allowed
    conn.execute(insert, (run_id, "LAST", activity))
    conn.commit()
    with pytest.raises(harness.CallCapReached):
        harness.check_call_allowed(conn, activity)             # call number `cap` + 1 is not
    harness.check_call_allowed(conn, "evaluation")             # no call cap (one cycle instead)
