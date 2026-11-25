"""Seed a throwaway database for the evaluation-review snapshots (tests/visual/evaluation.spec.js).

An evaluation review only exists in REAL mode (T-MODE-1), which normally means calling a model. This
script never does. It copies the Tier 1 set-up (tests/tier1/test_evaluation_publish.py): a fake OpenAI
server on this machine (127.0.0.1), a placeholder key, and a temporary database. Then it publishes
two reviews into that database:

  Review 1: an ordinary (stand-in) review, published.
  Review 2: an evaluation review, started by the script identity in real mode, published.

so page 2 can show the "Evaluation review" tag on one row and not the other, and pages 3 and 6 can show
a published evaluation review. Playwright then serves the database with the app in STAND-IN mode
(AGENTS_MODE stays stand_in, CLAUDE.md), which only reads it.

Run from the project folder:   .venv/bin/python -m tests.visual.seed_evaluation <folder>
The database is <folder>/app.db. Nothing here reads or writes data/app.db or data/spike.db.
"""

import sys
from pathlib import Path

import pytest

import backend.settings
from backend.runtime import crews, spike, stages
from backend.services import runs
from tests import flow
from tests.fake_openai import TEST_API_KEY, FakeOpenAI
from tests.tier1.test_evaluation_publish import World
from tests.tier1.test_real_mode_green_path import the_answer_key


def seed(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    patches = pytest.MonkeyPatch()

    # The same two guards tests/conftest.py gives every test: the real databases are out of reach.
    patches.setattr(backend.settings, "DEFAULT_DATABASE_PATH", str(folder / "never-used.db"))
    patches.setattr(stages, "_counting_databases",
                    lambda settings: spike.counted_databases(settings, folder / "no-spike.db"))

    # The same set-up as the `as_openai` fixture: CrewAI talks to the fake, not to api.openai.com.
    crews.load_crewai()
    from crewai.llms.providers.openai.completion import OpenAICompletion
    patches.setattr(OpenAICompletion, "_on_compatible_server", lambda self: False)

    fake = FakeOpenAI().start()
    patches.setenv("OPENAI_BASE_URL", fake.base_url)
    patches.setenv("OPENAI_API_KEY", TEST_API_KEY)
    fake.answer_with(the_answer_key)
    try:
        world = World(folder)
        ordinary = flow.to_g3(world.conn, world.stand_in)        # Review 1
        flow.publish(world.conn, ordinary)
        evaluation = world.publish_evaluation_run()              # Review 2
        assert runs.get_run(world.conn, evaluation)["is_evaluation"] is True
        assert runs.get_run(world.conn, ordinary)["is_evaluation"] is False
        world.conn.close()

        # Proof that nothing went out: every request reached the fake, and carried the placeholder key.
        assert fake.requests, "the evaluation review should have asked the fake"
        assert {seen.api_key for seen in fake.requests} == {TEST_API_KEY}
        assert not fake.unscripted, "a request nobody scripted reached the fake"
        print(f"Seeded {folder / 'app.db'}: 2 reviews published; {len(fake.requests)} requests, "
              "all to the fake server on this machine.")
    finally:
        fake.stop()
        patches.undo()


if __name__ == "__main__":
    seed(Path(sys.argv[1]))
