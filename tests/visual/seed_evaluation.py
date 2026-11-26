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
from contextlib import contextmanager
from pathlib import Path

import pytest

import backend.settings
from backend.runtime import crews, spike, stages
from backend.services import runs
from tests import flow
from tests.fake_openai import TEST_API_KEY, FakeOpenAI
from tests.tier1.test_evaluation_publish import World
from tests.tier1.test_real_mode_green_path import the_answer_key


@contextmanager
def _fake_world(folder: Path):
    """The shared set-up: the real databases out of reach, CrewAI talking to a fake server on this
    machine with a placeholder key. Yields (world, fake); undoes everything afterwards."""
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
        yield World(folder), fake
        # Proof that nothing went out: every request reached the fake, and carried the placeholder key.
        assert fake.requests, "the evaluation review should have asked the fake"
        assert {seen.api_key for seen in fake.requests} == {TEST_API_KEY}
        assert not fake.unscripted, "a request nobody scripted reached the fake"
    finally:
        fake.stop()
        patches.undo()


def seed(folder: Path) -> None:
    with _fake_world(folder) as (world, fake):
        ordinary = flow.to_g3(world.conn, world.stand_in)        # Review 1
        flow.publish(world.conn, ordinary)
        evaluation = world.publish_evaluation_run()              # Review 2
        assert runs.get_run(world.conn, evaluation)["is_evaluation"] is True
        assert runs.get_run(world.conn, ordinary)["is_evaluation"] is False
        world.conn.close()
        print(f"Seeded {folder / 'app.db'}: 2 reviews published; {len(fake.requests)} requests, "
              "all to the fake server on this machine.")


def seed_at_step(folder: Path, step: str) -> None:
    """One evaluation review waiting at `step` ("g1", "g2" or "g3") and nothing else, for the "at a
    step" snapshots (H-106). Only one review can be active, so each step has its own database."""
    from tests.tier2.test_evaluation_pages import _eval_run_at       # the script takes it to the step
    with _fake_world(folder) as (world, fake):
        run_id = _eval_run_at(world, step)
        run = runs.get_run(world.conn, run_id)
        assert run["is_evaluation"] is True and run["status"] == "ACTIVE" and run["is_at_gate"]
        world.conn.close()
        print(f"Seeded {folder / 'app.db'}: one evaluation review at {step}; {len(fake.requests)} requests, "
              "all to the fake server on this machine.")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        seed_at_step(Path(sys.argv[1]), sys.argv[2])       # <folder> g1|g2|g3
    else:
        seed(Path(sys.argv[1]))
