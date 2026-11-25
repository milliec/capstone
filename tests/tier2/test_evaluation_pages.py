"""H-106 (UX-026, DL-61): pages 3 to 6 of an evaluation review offer no way to decide. Tier 2.

A person cannot decide on an evaluation review (the server refuses it, T-EVALHAND-1), so the pages show
the record read-only and one line, and no control to try. Same set-up as UX-025's test: real-mode
evaluation runs answered by the fake OpenAI (dummy key, temporary database). No real call.

  (1) Pages 4, 5 and 6, at the step: the one line under the H1; no form, button, input or "Finish" /
      "Publish" / "Close" words in the page body (not hidden, not disabled: absent from the source).
  (2) Page 6 never says the General Partner "will see these dates", and drops the last two sentences
      of the date conventions note.
  (3) After the step (published): the same line, no form, the record still shown.
  (4) Page 3 at a step: "Nothing for you to do yet", the evaluation-script sentence, the "stopped"
      line, no next-step link, no refresh controls, "Abandon this review" still offered.
  (5) Ordinary reviews are unchanged: the same pages still offer their forms and old sentences.
"""

import re

import pytest

from backend.services import FUND_ID, runs
from backend.services.auth import EVALUATION_ACTOR
from tests import flow
from tests.conftest import _signed_in
from tests.tier1.test_evaluation_publish import World, the_answer_key

LINE = ("This is an evaluation review. The evaluation script makes its decisions, so there is "
        "nothing for you to decide here.")
H1_WAITING = "Nothing for you to do yet"
STOPPED = "If this stays the same, the script has probably stopped."
# Words that name a decision control. None may appear in the body of pages 4 to 6 (UX-026).
CONTROL_WORDS = ["Finish checking", "Finish and calculate dates", "Publish calendar",
                 "Close without publishing", "Next rule to decide", "Next answer to decide"]


@pytest.fixture
def world(tmp_path, as_openai):
    as_openai.answer_with(the_answer_key)
    return World(tmp_path)


def _eval_run_at(world, step):
    """A real-mode evaluation run, taken to `step` ("g1", "g2" or "g3") by the script identity."""
    script = {"actor": EVALUATION_ACTOR}
    conn, settings = world.conn, world.evaluation
    conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")   # test set-up
    conn.commit()
    run_id = runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID,
                            started_by=EVALUATION_ACTOR, demo_planted_row=False, demo_fail_step1=False)
    if step == "g1":
        return run_id
    for n in flow.RULES:
        flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n], **script)
    flow.finish_g1(conn, settings, run_id, **script)
    if step == "g2":
        return run_id
    for n in flow.APPLIES_NS:
        flow.answer(conn, run_id, n, "confirm", "applies", **script)
    flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "Not confirmed in fund records yet", **script)
    flow.answer(conn, run_id, flow.DOES_NOT_APPLY_N, "confirm", "does_not_apply", **script)
    flow.finish_g2(conn, settings, run_id, **script)
    return run_id


def _main(world, path):
    """The page body: what is inside <main>. The sidebar's "Sign out" form is not the page's."""
    page = _signed_in(world.stand_in, "specialist-1").get(path)
    assert page.status_code == 200, path
    return page.text.split("<main", 1)[1].split("</main>", 1)[0]


def _words(html):
    """What a person reads, whitespace collapsed (tags removed)."""
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


# --- (1) pages 4 to 6, at the step -----------------------------------------------------------------

@pytest.mark.parametrize("step, page", [("g1", "g1"), ("g2", "g2"), ("g3", "g3")])
def test_an_evaluation_step_page_shows_the_line_and_no_decision_control(world, step, page):
    run_id = _eval_run_at(world, step)
    body = _main(world, f"/specialist/runs/{run_id}/{page}")
    assert LINE in _words(body)
    assert body.count(LINE) == 1
    assert body.index(LINE) > body.index("<h1")
    assert body.index(LINE) < body.index('class="steps"')       # under the H1, above the stepper
    for tag in ("<form", "<button", "<input", "<textarea", "<select"):
        assert tag not in body, tag
    for words in CONTROL_WORDS:
        assert words not in body, words
    assert f'href="/specialist/runs/{run_id}#abandon"' in body       # "Abandon this review" stays
    assert "Abandon this review" in body


def test_the_usual_leads_are_replaced_not_kept(world):
    bodies = [_words(_main(world, f"/specialist/runs/{_eval_run_at(world, s)}/{p}"))
              for s, p in (("g1", "g1"), ("g2", "g2"), ("g3", "g3"))]
    assert "then approve or reject it" not in bodies[0]
    assert "recorded with your name" not in bodies[0]
    assert "Confirm each answer or overrule it" not in bodies[1]
    assert "then publish for the General Partner" not in bodies[2]


def test_an_undecided_rule_keeps_its_status_word_and_has_no_form(world):
    run_id = _eval_run_at(world, "g1")
    body = _main(world, f"/specialist/runs/{run_id}/g1")
    assert "To decide" in body                       # the status word stays
    assert 'class="rule-card open' not in body       # no "still needs a person" bar
    assert 'class="sq you"' not in body              # no orange "your turn" marker


# --- (2) page 6: nothing the General Partner "will see" ---------------------------------------------

def test_page_6_has_no_general_partner_promise(world):
    run_id = _eval_run_at(world, "g3")
    text = _words(_main(world, f"/specialist/runs/{run_id}/g3"))
    assert "will see these" not in text
    assert "The General Partner sees a short note" not in text
    assert "This does not stop you publishing" not in text
    # what stays: the first sentence of the note, the calendar and both lists
    assert "has not yet been checked against the legal texts" in text
    assert "What's not in this calendar" in text and "Calendar" in text


# --- (3) after the step ----------------------------------------------------------------------------

def test_after_the_step_the_line_stays_and_the_record_is_read_only(world):
    run_id = world.publish_evaluation_run()
    for page in ("g1", "g2", "g3"):
        body = _main(world, f"/specialist/runs/{run_id}/{page}")
        assert LINE in _words(body), page
        assert "<form" not in body and "<button" not in body, page
    assert "for the evaluation only. It was not shown to the General Partner." \
        in _words(_main(world, f"/specialist/runs/{run_id}/g3"))


# --- (4) page 3 at a step --------------------------------------------------------------------------

SENTENCES = {
    "g1": "The evaluation script now decides on each rule. Nothing here is for you to decide.",
    "g2": "The evaluation script now decides what applies. Nothing here is for you to decide.",
    "g3": "The evaluation script now decides whether to publish it. Nothing here is for you to decide.",
}


@pytest.mark.parametrize("step", ["g1", "g2", "g3"])
def test_page_3_at_a_step_has_nothing_for_the_person_to_do(world, step):
    run_id = _eval_run_at(world, step)
    body = _main(world, f"/specialist/runs/{run_id}")
    text = _words(body)
    assert f"<h1>{H1_WAITING}</h1>" in body
    assert SENTENCES[step] in text
    assert STOPPED in text and "Abandon this review" in text
    assert 'class="btn"' not in body                       # no next-step link ("Abandon" is a ghost button)
    assert "Refresh now" not in text and "refreshes every" not in text
    assert f'action="/specialist/runs/{run_id}/abandon"' in body      # the way out stays


# --- (5) ordinary reviews are unchanged ------------------------------------------------------------

def test_an_ordinary_review_keeps_its_forms_and_its_old_words(world):
    conn, settings = world.conn, world.stand_in
    run_id = flow.start_to_g1(conn, settings)
    g1 = _main(world, f"/specialist/runs/{run_id}/g1")
    assert LINE not in g1 and "Finish checking" in g1 and "<form" in g1
    status = _words(_main(world, f"/specialist/runs/{run_id}"))
    assert "The rules are ready for you to check" in status
    assert STOPPED not in status and "Check the rules" in status

    g3_id = flow.to_g3(conn, settings)
    g3 = _words(_main(world, f"/specialist/runs/{g3_id}/g3"))
    assert "will see these" in g3
    assert "then publish for the General Partner" in g3
    assert "This does not stop you publishing. The General Partner sees a short note saying the same." in g3
