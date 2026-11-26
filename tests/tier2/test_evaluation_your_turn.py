"""H-104 (ux.md Open Question 26 a, option A2): no "Your turn" for an evaluation review. Tier 2.

The script's turn is the only one that counts, so a person is never told it is theirs. For an evaluation
review waiting at a step:
  (1) the sidebar and phone-bar tags do not show (`your_turn` is not set);
  (2) page 2's notice reads "Evaluation review {n}: ..." with the one link "Open review {n}", and never
      "Waiting for you", "AI is working" or "Continue checking";
  (3) page 3's pill says "In progress" in the quiet tone, and the stepper says "In progress" on that step
      and the step is not a link (only "Done" steps link);
  (4) the stepper on pages 4 to 6 says the same.
An ordinary review is unchanged (control tests). Same set-up as test_evaluation_pages.py: real-mode
evaluation runs answered by the fake OpenAI, temporary database, no real call.

NOT checked here: the words after the colon in page 2's notice, page 3's box heading and every page's
<title>. All three print the server's `status_words` ("Your turn: check the rules"). That is held until
`@ux.designer` answers (handoffs.md, H-108).
"""

import re

import pytest

from backend.services import runs
from tests import flow
from tests.conftest import _signed_in
from tests.tier1.test_evaluation_publish import World, the_answer_key
from tests.tier2.test_evaluation_pages import _eval_run_at, _words

STEP_OF = {"g1": 2, "g2": 3, "g3": 4}          # the stepper step a review at that gate is on
PAGE_OF = {"g1": "/g1", "g2": "/g2", "g3": "/g3"}

# Why one test per step, not one test per check: every real-mode evaluation review starts CrewAI timer
# threads that the library never stops, and the whole suite sits close to the process's thread limit
# ("can't start new thread" made test_trace_export fail when this file built ~13 of them). Three
# reviews, one per step, with every check run on each; the controls use ordinary stand-in reviews.


@pytest.fixture
def world(tmp_path, as_openai):
    as_openai.answer_with(the_answer_key)
    return World(tmp_path)


def _get(world, path):
    page = _signed_in(world.stand_in, "specialist-1").get(path)
    assert page.status_code == 200, path
    return page.text


def _stepper(html):
    """The four stepper items as [(state word, is_link)], in order."""
    block = html.split('class="steps"', 1)[1].split("</ol>", 1)[0]
    items = re.findall(r'<li[^>]*>(.*?)</li>', block, flags=re.DOTALL)
    return [(re.search(r'<span class="s">(.*?)</span>', i).group(1), "<a " in i) for i in items]


# --- the evaluation review at a step: every check, on one review per step -----------------------------

def _check_frame(world, run_id):
    """(1) The sidebar and phone bar: after <body>, before <main>. (The <title> is not the frame: it
    prints the server's `status_words`, held with the heading, H-108.)"""
    for path in ("/specialist/runs", f"/specialist/runs/{run_id}"):
        frame = _get(world, path).split("<main", 1)[0].split("<body", 1)[1]
        assert "Your turn" not in frame, path
        assert 'class="turn"' not in frame, path


def _check_notice(world, run_id):
    """(2) Page 2's notice: named, one link, none of the old words."""
    notice = _get(world, "/specialist/runs").split('class="notice', 1)[1].split("</section>", 1)[0]
    text = _words(notice)
    assert "Evaluation review 1:" in text
    assert "Open review 1" in text and f'href="/specialist/runs/{run_id}"' in notice
    for old in ("Waiting for you", "AI is working", "Continue checking"):
        assert old not in text, old
    assert notice.count("<a ") == 1


def _check_page_3(world, run_id, step):
    """(3) Page 3: the quiet pill and the stepper."""
    body = _get(world, f"/specialist/runs/{run_id}").split("<main", 1)[1]
    cta = body.split('class="cta', 1)[1].split("</div>", 1)[0]
    assert 'class="cta wait' in body                         # the quiet tone of "AI is working"
    assert ">In progress<" in cta and "Your turn" not in cta.split("<h2")[0]   # (the heading is held)
    n = STEP_OF[step]
    steps = _stepper(body)
    assert steps[n - 1] == ("In progress", False)            # not a link
    assert all(word != "Your turn" for word, _ in steps)
    assert [link for word, link in steps if word == "Done"] == [True] * (n - 1)
    assert body.count('aria-current="step"') == 1


def _check_pages_4_to_6(world, run_id, step):
    """(4) The same stepper on pages 4 to 6."""
    for page in ("g1", "g2", "g3"):
        body = _get(world, f"/specialist/runs/{run_id}{PAGE_OF[page]}").split("<main", 1)[1]
        steps = _stepper(body)
        assert steps[STEP_OF[step] - 1] == ("In progress", False), page
        assert all(word != "Your turn" for word, _ in steps), page


@pytest.mark.parametrize("step", ["g1", "g2", "g3"])
def test_an_evaluation_review_at_a_step_is_never_the_persons_turn(world, step):
    run_id = _eval_run_at(world, step)
    _check_frame(world, run_id)
    _check_notice(world, run_id)
    _check_page_3(world, run_id, step)
    _check_pages_4_to_6(world, run_id, step)
    run = runs.get_run(world.conn, run_id)                   # what the server sends
    n = STEP_OF[step]
    assert [s["state"] for s in run["steps"]][n - 1] == "In progress"
    assert [s["href"] is not None for s in run["steps"]] == [i < n - 1 for i in range(4)]
    assert run["status_tone"] == "info"


# --- ordinary reviews: the old words and tone (stand-in, no CrewAI) --------------------------------------

def test_an_ordinary_review_at_a_step_keeps_the_tag(world):
    flow.start_to_g1(world.conn, world.stand_in)
    frame = _get(world, "/specialist/runs").split("<main", 1)[0]
    assert frame.count(">Your turn<") == 3                   # the sidebar, the phone bar and the phone menu


def test_an_ordinary_notice_is_unchanged(world):
    flow.start_to_g1(world.conn, world.stand_in)
    notice = _words(_get(world, "/specialist/runs").split('class="notice', 1)[1].split("</section>", 1)[0])
    assert "Waiting for you" in notice and "Continue checking" in notice and "Review 1:" in notice
    assert "Evaluation review" not in notice


def test_an_ordinary_review_at_a_step_still_says_your_turn_on_page_3(world):
    run_id = flow.start_to_g1(world.conn, world.stand_in)
    body = _get(world, f"/specialist/runs/{run_id}").split("<main", 1)[1]
    assert _stepper(body)[1] == ("Your turn", True)
    assert "Your turn" in body.split('class="cta', 1)[1].split("</div>", 1)[0]
    assert runs.get_run(world.conn, run_id)["status_tone"] == "action"
