"""UX-025 (H-100, H-101, DL-60): the pages show the "Evaluation review" label and outcome sentence. Tier 1.

  (1) An evaluation review shows the text tag "Evaluation review" on pages 2 to 6, never "Stand-in agents".
  (2) Once published, pages 3 and 6 read exactly the evaluation sentence; page 3 links to Filing rules,
      not to /calendar.
  (3) An ordinary review shows none of this, and /calendar and the sign-in page never show it.

Same set-up as T-EVALPUB-1 (temporary database, fake OpenAI, no real call).
"""

import pytest

from tests.conftest import _signed_in
from tests.fake_openai import TEST_API_KEY  # noqa: F401  (keeps the fixture import path obvious)
from tests.tier1.test_evaluation_publish import World, the_answer_key

LABEL = "Evaluation review"
SENTENCE = "for the evaluation only. It was not shown to the General Partner."


@pytest.fixture
def world(tmp_path, as_openai):
    as_openai.answer_with(the_answer_key)
    return World(tmp_path)


def _get(world, path):
    page = _signed_in(world.stand_in, "specialist-1").get(path)
    assert page.status_code == 200, path
    return page.text


def test_an_evaluation_review_shows_the_label_on_pages_2_to_6(world):
    eval_id = world.publish_evaluation_run()
    for path in ("/specialist/runs", f"/specialist/runs/{eval_id}",
                 f"/specialist/runs/{eval_id}/g1", f"/specialist/runs/{eval_id}/g2",
                 f"/specialist/runs/{eval_id}/g3"):
        text = _get(world, path)
        assert LABEL in text, path
        assert "Stand-in agents" not in text, path


def test_a_published_evaluation_review_says_it_was_not_shown_to_the_gp(world):
    eval_id = world.publish_evaluation_run()
    status = _get(world, f"/specialist/runs/{eval_id}")
    after = _get(world, f"/specialist/runs/{eval_id}/g3")
    for text in (status, after):
        assert "Published on" in text and SENTENCE in text
        assert "The General Partner now sees this calendar" not in text
    assert 'href="/calendar"' not in status.split("<main", 1)[1]    # page 3 links to Filing rules instead
    assert "Go to Filing rules" in status


def test_an_ordinary_review_and_the_gp_pages_show_none_of_it(world):
    real_id = world.publish_real_run()
    for path in ("/specialist/runs", f"/specialist/runs/{real_id}", f"/specialist/runs/{real_id}/g3"):
        text = _get(world, path)
        assert LABEL not in text and SENTENCE not in text, path
    assert "The General Partner now sees this calendar" in _get(world, f"/specialist/runs/{real_id}")

    world.publish_evaluation_run()
    assert LABEL not in _signed_in(world.stand_in, "gp-1").get("/calendar").text
    assert LABEL not in _signed_in(world.stand_in, "gp-1").get("/sign-in").text
