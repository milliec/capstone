"""T-EVALPUB-1 (H-099, DL-60): an evaluation run publishes at G3 but is never the live calendar. Tier 1.

  (1) The live calendar skips evaluation runs. With an earlier real publication, publishing an
      evaluation run changes neither the General Partner's calendar nor the "previous publication"
      line at G3.
  (2) "Being prepared" stays true. If only evaluation runs have published, the General Partner still
      gets the fixed message (DL-27, EC-014): an evaluation publish is not a first publication.
  (3) An evaluation run still publishes (EC-R2): its own publication is still read for its own pages.
  (4) The run's page data says whether it is an evaluation run (`is_evaluation`), for the label (H-100).

The evaluation runs here are the real thing: started by `specialist-eval` with `SPEND_ACTIVITY=evaluation`
in REAL mode (an evaluation run refuses stand-in mode, T-MODE-1), answered by the fake OpenAI (dummy key,
temporary database, `as_openai`). No real call, no real key, no real database. The "real" publication the
General Partner sees is an ordinary stand-in review, as in the demo.
"""

import pytest

from backend.db.connection import connect, init_db
from backend.services import FUND_ID, calendar, runs
from backend.services.auth import EVALUATION_ACTOR
from backend.settings import load_settings
from tests import flow
from tests.conftest import _signed_in
from tests.fake_openai import TEST_API_KEY
from tests.tier1.test_real_mode_green_path import MODELS, the_answer_key


def _settings(tmp_path, *, mode, activity):
    env = {"AGENTS_MODE": mode, "SPEND_ACTIVITY": activity, "SESSION_SECRET": "test-only",
           "STAND_IN_UNIT_PAUSE_S": "0", "DATABASE_PATH": str(tmp_path / "app.db")}
    if mode == "real":
        env.update({"OPENAI_API_KEY": TEST_API_KEY, "LLM_MODEL_EXTRACT": MODELS["extract"],
                    "LLM_MODEL_VERIFY": MODELS["verify"], "LLM_MODEL_JUDGE": MODELS["judge"]})
    return load_settings(env)


class World:
    """One temporary database, two kinds of settings on it: stand-in (a real publication) and
    real-mode evaluation (an evaluation run)."""

    def __init__(self, tmp_path):
        self.stand_in = _settings(tmp_path, mode="stand_in", activity="")
        self.evaluation = _settings(tmp_path, mode="real", activity="evaluation")
        init_db(self.stand_in.database_path)
        self.conn = connect(self.stand_in.database_path)

    def publish_real_run(self) -> str:
        """An ordinary publish, back-dated to a distinct day. Timestamps are to the second, so without
        this a real and an evaluation publish made in one test would carry the same text and the test
        could not tell which one a reader returned."""
        run_id = flow.to_g3(self.conn, self.stand_in)
        flow.publish(self.conn, run_id)
        day = self.conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]    # 1, 2, ... per test
        self.conn.execute("UPDATE publications SET published_at = ? WHERE calendar_id = ?",
                          (f"2026-01-{day:02d}T09:00:00+00:00", f"CAL-{run_id}"))
        self.conn.commit()
        return run_id

    def evaluation_run_at_g3(self) -> str:
        """A real-mode evaluation run, started by the script identity, taken to G3 as the scripted gates
        will take it (the same decisions as `flow.to_g3`). It acts as the script: a person cannot decide on an
        evaluation run (DL-61, T-EVALHAND-1)."""
        script = {"actor": EVALUATION_ACTOR}
        conn, settings = self.conn, self.evaluation
        conn.execute("UPDATE runs SET status = 'ABANDONED' WHERE status = 'ACTIVE'")   # test set-up
        conn.commit()
        run_id = runs.start_run(conn, settings, flow.run_now, fund_id=FUND_ID,
                                started_by=EVALUATION_ACTOR, demo_planted_row=False,
                                demo_fail_step1=False)
        for n in flow.RULES:
            flow.approve_rule(conn, run_id, n, rule=flow.DEMO_RULES[n], who=flow.DEMO_WHO[n], **script)
        flow.finish_g1(conn, settings, run_id, **script)
        for n in flow.APPLIES_NS:
            flow.answer(conn, run_id, n, "confirm", "applies", **script)
        flow.answer(conn, run_id, flow.UNSURE_N, "decide", "applies", "Not confirmed in fund records yet", **script)
        flow.answer(conn, run_id, flow.DOES_NOT_APPLY_N, "confirm", "does_not_apply", **script)
        flow.finish_g2(conn, settings, run_id, **script)
        assert runs.is_evaluation_run(runs.get_run(conn, run_id))      # it really is one, not a shortcut
        return run_id

    def publish_evaluation_run(self) -> str:
        run_id = self.evaluation_run_at_g3()
        flow.publish(self.conn, run_id, actor=EVALUATION_ACTOR)
        return run_id


@pytest.fixture
def world(tmp_path, as_openai):
    as_openai.answer_with(the_answer_key)
    return World(tmp_path)


def test_an_evaluation_publish_leaves_the_live_calendar_and_previous_publication_alone(world):
    conn = world.conn
    real_id = world.publish_real_run()
    real_published_at = runs.get_run(conn, real_id)["published_at"]
    live_before = calendar.get_published_calendar(conn, FUND_ID)
    assert live_before["run_id"] == real_id

    eval_id = world.publish_evaluation_run()                 # the newest publication in the table
    assert conn.execute("SELECT run_id FROM calendar_versions c JOIN publications p "
                        "ON p.calendar_id = c.calendar_id ORDER BY p.publication_id DESC"
                        ).fetchone()["run_id"] == eval_id

    live_after = calendar.get_published_calendar(conn, FUND_ID)                  # (1) page 7
    assert live_after["run_id"] == real_id
    assert live_after["publication_id"] == live_before["publication_id"]
    assert live_after["published_at"] == real_published_at

    third_id = flow.to_g3(conn, world.stand_in)                                  # (1) the G3 line
    assert calendar.get_g3_view(conn, runs.get_run(conn, third_id))["previous_publication_at"] \
        == real_published_at


def test_an_evaluation_run_is_still_published_and_its_own_page_shows_it(world):
    conn = world.conn
    real_id = world.publish_real_run()
    eval_id = world.publish_evaluation_run()

    run = runs.get_run(conn, eval_id)                                            # (3) EC-R2
    assert run["status"] == "COMPLETED" and run["published_at"]
    view = calendar.get_g3_view(conn, run)
    assert view["outcome"]["at"] == run["published_at"]
    # Its "previous publication" is the real one, not itself and not another evaluation run.
    assert view["previous_publication_at"] == runs.get_run(conn, real_id)["published_at"]


def test_with_only_evaluation_publications_the_general_partner_still_sees_being_prepared(world):
    conn = world.conn
    world.publish_evaluation_run()
    world.publish_evaluation_run()

    assert calendar.get_published_calendar(conn, FUND_ID) is None                # (2)
    page = _signed_in(world.stand_in, "gp-1").get("/calendar")
    assert page.status_code == 200
    assert "Your compliance calendar is being prepared" in page.text
    assert "Published on" not in page.text

    third_id = flow.to_g3(conn, world.stand_in)   # and a later G3 shows no "previous publication"
    assert calendar.get_g3_view(conn, runs.get_run(conn, third_id))["previous_publication_at"] is None


def test_a_real_publish_after_an_evaluation_publish_is_the_live_calendar(world):
    """The rule skips evaluation runs; it must not freeze the calendar on an older publication."""
    world.publish_real_run()
    world.publish_evaluation_run()
    newest_real = world.publish_real_run()
    assert calendar.get_published_calendar(world.conn, FUND_ID)["run_id"] == newest_real


def test_the_run_page_data_says_whether_it_is_an_evaluation_run(world):
    conn = world.conn
    real_id = world.publish_real_run()
    eval_id = world.publish_evaluation_run()
    assert runs.get_run(conn, real_id)["is_evaluation"] is False                 # (4)
    assert runs.get_run(conn, eval_id)["is_evaluation"] is True
    assert {r["run_id"]: r["is_evaluation"] for r in runs.list_runs(conn, FUND_ID)} \
        == {real_id: False, eval_id: True}
