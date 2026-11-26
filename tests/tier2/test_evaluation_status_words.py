"""H-109 (ux.md §1.5, answers H-108): the words the server sends for an evaluation review at a step. Tier 2.

For an evaluation review (`is_evaluation`) that is ACTIVE at AT_G1, AT_G2 or AT_G3, `status_words` is
  AT_G1  "The evaluation script is deciding on the rules"
  AT_G2  "The evaluation script is deciding what applies"
  AT_G3  "The evaluation script is deciding whether to publish"
and the tone stays "info" (A2). Every other state of an evaluation review, and every ordinary review,
keeps today's words and tone. The pages print the one string (page 2's notice and Status pill, page 3's
status box and <title>) and work nothing out (ux.md §1.2), so the server is the only place that changes.

Set-up: a stand-in review in a temporary database (conftest's guard keeps the real ones shut), then its
row is rewritten to the state under test. `status_words` depends only on the row's status, phase,
`spend_activity` and `started_by`, so no CrewAI run and no fake OpenAI is needed. No real call.
"""

import pytest

from backend.services import runs
from tests import flow

EVAL_WORDS = {
    "AT_G1": "The evaluation script is deciding on the rules",
    "AT_G2": "The evaluation script is deciding what applies",
    "AT_G3": "The evaluation script is deciding whether to publish",
}
ORDINARY_WORDS = {
    ("ACTIVE", "A_RUNNING"): ("AI is drafting the rules", "info"),
    ("ACTIVE", "AT_G1"): ("Your turn: check the rules", "action"),
    ("ACTIVE", "B_RUNNING"): ("AI is checking what applies", "info"),
    ("ACTIVE", "AT_G2"): ("Your turn: confirm what applies", "action"),
    ("ACTIVE", "C_RUNNING"): ("Working out the dates", "info"),
    ("ACTIVE", "AT_G3"): ("Your turn: publish the calendar", "action"),
    ("FAILED", "A_RUNNING"): ("Failed", "problem"),
    ("ABANDONED", "AT_G1"): ("Abandoned", "neutral"),
    ("DECLINED", "AT_G3"): ("Closed without publishing", "neutral"),
    ("COMPLETED", "AT_G3"): ("Published", "success"),
}
EVALUATION_ACTOR = "specialist-eval"


@pytest.fixture(autouse=True)
def _tables_exist(specialist_client):
    """Building the app creates the tables in the temporary database; the `db` fixture alone does not."""


def _review(db, settings, *, status="ACTIVE", phase="AT_G1", evaluation=False,
            spend_activity=None, started_by=None):
    """A stand-in review whose row is rewritten to the state under test. Returns the run as the server
    describes it (`runs.get_run`)."""
    run_id = flow.start_to_g1(db, settings)
    if evaluation:
        spend_activity, started_by = "evaluation", EVALUATION_ACTOR
    db.execute("UPDATE runs SET status = ?, phase = ?, spend_activity = COALESCE(?, spend_activity), "
               "started_by = COALESCE(?, started_by) WHERE run_id = ?",
               (status, phase, spend_activity, started_by, run_id))
    db.commit()
    return runs.get_run(db, run_id)


# --- the evaluation review at a step: the new words ----------------------------------------------------

@pytest.mark.parametrize("phase", ["AT_G1", "AT_G2", "AT_G3"])
def test_an_evaluation_review_at_a_step_gets_the_evaluation_words(db, settings, phase):
    run = _review(db, settings, phase=phase, evaluation=True)
    assert run["is_evaluation"] is True
    assert run["status_words"] == EVAL_WORDS[phase]
    assert run["status_tone"] == "info"                       # unchanged: the quiet tone (A2)


@pytest.mark.parametrize("phase", ["AT_G1", "AT_G2", "AT_G3"])
def test_the_evaluation_words_never_say_your_turn(db, settings, phase):
    run = _review(db, settings, phase=phase, evaluation=True)
    assert "your turn" not in run["status_words"].lower()
    assert not run["status_words"].startswith("In progress")  # the pill beside it already says that


# --- everything else keeps today's words ---------------------------------------------------------------

AT_A_STEP = [("ACTIVE", p) for p in ("AT_G1", "AT_G2", "AT_G3")]      # the three cases that change
OTHER_STATES = [s for s in ORDINARY_WORDS if s not in AT_A_STEP]


@pytest.mark.parametrize("state", OTHER_STATES, ids=lambda s: "-".join(s))
def test_an_evaluation_review_in_any_other_state_keeps_the_ordinary_words(db, settings, state):
    status, phase = state
    words, tone = ORDINARY_WORDS[state]
    run = _review(db, settings, status=status, phase=phase, evaluation=True)
    assert run["is_evaluation"] is True
    assert (run["status_words"], run["status_tone"]) == (words, tone)


@pytest.mark.parametrize("state", list(ORDINARY_WORDS), ids=lambda s: "-".join(s))
def test_an_ordinary_review_keeps_the_ordinary_words_in_every_state(db, settings, state):
    status, phase = state
    words, tone = ORDINARY_WORDS[state]
    run = _review(db, settings, status=status, phase=phase)
    assert run["is_evaluation"] is False
    assert (run["status_words"], run["status_tone"]) == (words, tone)


@pytest.mark.parametrize("spend_activity, started_by", [("evaluation", "specialist-1"),
                                                        (None, EVALUATION_ACTOR)])
def test_one_half_of_the_evaluation_test_is_not_enough(db, settings, spend_activity, started_by):
    """An evaluation run is DERIVED from both facts (DL-59): either alone is an ordinary review."""
    run = _review(db, settings, spend_activity=spend_activity, started_by=started_by)
    assert run["is_evaluation"] is False
    assert run["status_words"] == "Your turn: check the rules"
    assert run["status_tone"] == "action"


def test_the_table_for_ordinary_reviews_is_unchanged():
    """The module's own table still holds the three "Your turn" words (the new words live beside it)."""
    assert runs.STATUS_WORDS[("ACTIVE", "AT_G1")] == "Your turn: check the rules"
    assert runs.STATUS_WORDS[("ACTIVE", "AT_G2")] == "Your turn: confirm what applies"
    assert runs.STATUS_WORDS[("ACTIVE", "AT_G3")] == "Your turn: publish the calendar"


# --- the pages print the one string -------------------------------------------------------------------

def test_pages_2_and_3_print_the_evaluation_words(db, settings, specialist_client):
    run = _review(db, settings, phase="AT_G1", evaluation=True)
    words = EVAL_WORDS["AT_G1"]
    page_2 = specialist_client.get("/specialist/runs")
    page_3 = specialist_client.get(f"/specialist/runs/{run['run_id']}")
    assert page_2.status_code == page_3.status_code == 200
    notice = page_2.text.split('class="notice', 1)[1].split("</section>", 1)[0]
    assert words in notice                                    # page 2's notice
    title = page_3.text.split("<title>", 1)[1].split("</title>", 1)[0]
    assert words in title                                     # page 3's <title>
    assert f"<h2 id=\"status-h\">{words}</h2>" in page_3.text   # page 3's status box heading
    for html in (notice, title, page_3.text.split("<main", 1)[1]):
        assert "Your turn: check the rules" not in html


def test_page_3_of_an_ordinary_review_still_prints_your_turn(db, settings, specialist_client):
    run = _review(db, settings, phase="AT_G1")
    page_3 = specialist_client.get(f"/specialist/runs/{run['run_id']}").text
    assert "Your turn: check the rules" in page_3
    assert "The evaluation script is deciding" not in page_3
