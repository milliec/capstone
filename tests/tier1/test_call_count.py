"""T-CAP-1 (Tier 1): the 70-call cap counts a real call WHICHEVER database it landed in.
No real key, no real model, no paid call. The tests only read and write throwaway database files.

The problem this closes (operator, 2026-11-23). The spike runner writes its trace to `data/spike.db`; the
web app writes its own to `data/app.db`. The cap (EC-R10, 70 real calls for the spike) used to be counted
inside ONE file, and only the spike runner ever checked it. A real review run through the web app, even
labelled `SPEND_ACTIVITY=spike`, was invisible to the cap and to the tally. Now one function
(`harness.count_real_calls`) sums the real-call lines across both files, and the spike runner's cap check
and `--tally` use it, with a per-database breakdown.

Not in this change, on purpose: the web app did not STOP at 70. That needed a new failure reason, which is a
SAD change. It was built afterwards (H-091, DL-58, 2026-11-24): see test_call_cap_web.py. A clean run is about
18 calls.
"""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from backend.db.connection import connect
from backend.runtime import harness, spike, spike_tally
from backend.settings import ROOT, load_settings
from tests.fake_openai import TEST_API_KEY

RUN_ENV = {"AGENTS_MODE": "real", "SPEND_ACTIVITY": "spike", "OPENAI_API_KEY": TEST_API_KEY,
           "LLM_MODEL_EXTRACT": "gpt-6-test-e"}


def settings_for(app_db: Path):
    return load_settings({**RUN_ENV, "DATABASE_PATH": str(app_db)})


def make_db(path: Path, **lines):
    """A database with `n` trace lines per activity (`none` = a stand-in line, which has no activity)."""
    run_id = spike.open_spike_run(settings_for(path), path)
    conn = connect(path)
    for activity, n in lines.items():
        for k in range(n):
            conn.execute(
                "INSERT INTO trace (run_id, fund_id, step, stage_attempt, unit_id, attempt_n, at, "
                "prompt_version, input_hash, spend_activity, cost_usd) "
                "VALUES (?, 'FND-DEMO-01', 'extract_rows', 1, ?, 1, 'now', 'v', 'h', ?, 0.001)",
                (run_id, f"{activity}-{k}", None if activity == "none" else activity))
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def dbs(tmp_path):
    """The two files, in the folder layout of the real thing (data/spike.db and data/app.db)."""
    data = tmp_path / "data"
    data.mkdir()
    return data / "spike.db", data / "app.db"


# --- The count --------------------------------------------------------------------------------

def test_a_call_counts_whichever_database_it_landed_in(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=6)
    make_db(app_db, spike=18)
    count = harness.count_real_calls("spike", [spike_db, app_db])
    assert count.total == 24
    assert [(d.label, d.lines) for d in count.databases] == [("data/spike.db", 6), ("data/app.db", 18)]
    assert count.breakdown() == "data/spike.db 6, data/app.db 18"
    assert count.cost_usd == pytest.approx(24 * 0.001)
    assert count.breakdown_with_cost() == "data/spike.db 6 (US$0.0060), data/app.db 18 (US$0.0180)"


def test_only_the_named_activity_counts(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=2, tuning=60, rehearsal=5, none=9)          # none = stand-in lines
    make_db(app_db, spike=3, demo=4, none=20)
    assert harness.count_real_calls("spike", [spike_db, app_db]).total == 5
    assert harness.count_real_calls("tuning", [spike_db, app_db]).total == 60
    assert harness.count_real_calls("evaluation", [spike_db, app_db]).total == 0


def test_the_same_file_reached_two_ways_is_counted_once(dbs):
    spike_db, _ = dbs
    make_db(spike_db, spike=7)
    roundabout = spike_db.parent / ".." / spike_db.parent.name / spike_db.name       # the same file, spelled differently
    count = harness.count_real_calls("spike", [spike_db, spike_db, roundabout])
    assert count.total == 7 and len(count.databases) == 1


def test_a_missing_database_counts_zero_and_is_never_created(tmp_path):
    ghost = tmp_path / "nowhere" / "app.db"
    count = harness.count_real_calls("spike", [ghost])
    assert count.total == 0 and count.databases[0].exists is False
    assert count.breakdown() == "nowhere/app.db 0 (no file yet)"
    assert not ghost.exists() and not ghost.parent.exists()


def test_a_database_with_no_trace_table_has_made_no_calls(tmp_path):
    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()                                        # a valid, empty database
    assert harness.count_real_calls("spike", [empty]).total == 0


def test_a_file_that_cannot_be_read_stops_the_count_instead_of_saying_zero(tmp_path):
    """Fail closed: a count that quietly said 0 would let the cap be passed."""
    broken = tmp_path / "broken.db"
    broken.write_bytes(b"this is not a database at all" * 20)
    with pytest.raises(sqlite3.DatabaseError):
        harness.count_real_calls("spike", [broken])


def test_counting_changes_nothing_and_every_connection_is_read_only(dbs, monkeypatch):
    spike_db, app_db = dbs
    make_db(spike_db, spike=3)
    make_db(app_db, spike=4)
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in dbs]
    opened = []
    real_connect = sqlite3.connect

    def spy(*args, **kwargs):
        opened.append((args, kwargs))
        return real_connect(*args, **kwargs)
    monkeypatch.setattr(harness.sqlite3, "connect", spy)
    harness.count_real_calls("spike", [spike_db, app_db])
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in dbs] == before
    assert len(opened) == 2
    for (uri,), kwargs in opened:
        assert uri.startswith("file:") and uri.endswith("?mode=ro") and kwargs.get("uri") is True


# --- Which files the spike counts --------------------------------------------------------------

def test_the_spike_counts_its_own_database_and_the_web_apps(tmp_path):
    spike_db = tmp_path / "data" / "spike.db"
    app_relative = load_settings({**RUN_ENV, "DATABASE_PATH": "data/app.db"})
    assert spike.counted_databases(app_relative, spike_db) == [spike_db, ROOT / "data" / "app.db"]
    absolute = settings_for(tmp_path / "elsewhere" / "app.db")
    assert spike.counted_databases(absolute, spike_db) == [spike_db, tmp_path / "elsewhere" / "app.db"]


def test_no_test_can_reach_the_real_database_by_default():
    """The conftest isolation: settings built with no DATABASE_PATH must not point at data/app.db."""
    default = Path(load_settings({}).database_path)
    assert default.name == "app.db" and ROOT / "data" not in default.parents and default != ROOT / "data" / "app.db"


# --- The spike runner's cap and the dry-run printout -------------------------------------------

def test_the_cap_is_reached_by_the_sum_of_both_databases(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=60)
    make_db(app_db, spike=10)                                               # the web app's calls
    with pytest.raises(harness.CallCapReached) as caught:
        spike.plan_first_call(settings_for(app_db), spike_db=spike_db)
    message = str(caught.value)
    assert "70 of 70" in message and "EC-R10" in message
    assert "Counted in data/spike.db 60, data/app.db 10" in message


def test_one_short_of_the_cap_still_plans_and_the_plan_says_where_the_calls_are(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=60)
    make_db(app_db, spike=9)
    plan = spike.plan_first_call(settings_for(app_db), spike_db=spike_db)
    assert plan.calls_used == 69 and plan.call_cap == 70
    assert plan.calls_breakdown == "data/spike.db 60, data/app.db 9"
    text = spike.format_plan(plan)
    assert "Spike calls    : 69 of 70 used (EC-R10)" in text
    assert "Counted in     : data/spike.db 60, data/app.db 9" in text


@pytest.mark.parametrize("planner", ["verify", "judge"])
def test_every_kind_of_call_uses_the_same_count(dbs, planner):
    spike_db, app_db = dbs
    make_db(spike_db, spike=1)
    make_db(app_db, spike=69)                                               # the web app alone almost fills it
    env = {**RUN_ENV, "DATABASE_PATH": str(app_db), "LLM_MODEL_VERIFY": "gpt-6-test-v",
           "LLM_MODEL_JUDGE": "gpt-6-test-j"}
    printed = []
    code = spike.main(["--step", planner], env=env, spike_db=spike_db, out=printed.append)
    assert code == 2 and "70 of 70" in "\n".join(printed) and "Counted in" in "\n".join(printed)


def test_a_real_call_is_refused_before_it_is_sent_when_the_web_app_used_the_rest(dbs, fake_openai, monkeypatch):
    spike_db, app_db = dbs
    make_db(app_db, spike=70)                                               # the whole cap, all in app.db
    monkeypatch.setenv("OPENAI_BASE_URL", fake_openai.base_url)
    env = {**RUN_ENV, "DATABASE_PATH": str(app_db)}
    printed, asked = [], []
    code = spike.main(["--go"], env=env, spike_db=spike_db, out=printed.append,
                      read_line=lambda prompt: asked.append(prompt) or "SRC-UCILAW")
    assert code == 2 and "REFUSED" in "\n".join(printed) and "70 of 70" in "\n".join(printed)
    assert asked == [] and fake_openai.requests == [] and not spike_db.exists()    # not even asked, nothing created


def test_when_both_settings_name_the_same_file_it_is_counted_once(dbs):
    spike_db, _ = dbs
    make_db(spike_db, spike=5)
    plan = spike.plan_first_call(settings_for(spike_db), spike_db=spike_db)       # DATABASE_PATH = the spike's file
    assert plan.calls_used == 5 and plan.calls_breakdown == "data/spike.db 5"


# --- The tally ----------------------------------------------------------------------------------

def test_the_tally_counts_both_files_and_says_where_each_call_is(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=6)
    make_db(app_db, spike=18)
    printed = []
    code = spike.main(["--tally"], env={**RUN_ENV, "DATABASE_PATH": str(app_db)}, spike_db=spike_db,
                      out=printed.append)
    text = "\n".join(printed)
    assert code == 0
    assert "Slots used     : 24 of 70 (46 left)" in text
    assert "Counted in     : data/spike.db 6 (US$0.0060), data/app.db 18 (US$0.0180)" in text


def test_the_tally_reads_the_database_a_web_app_run_wrote(dbs):
    spike_db, app_db = dbs
    make_db(app_db, spike=18)                                               # no spike database at all yet
    tally = spike_tally.collect(spike_db, other_databases=[app_db])
    assert tally.exists is False and tally.slots_used == 18
    text = spike_tally.format_tally(tally)
    assert "there is no spike database yet" in text
    assert "Real calls elsewhere: 18 of 70 (data/spike.db 0 (US$0.0000) (no file yet), data/app.db 18" in text
    assert not spike_db.exists()


def test_the_tally_alone_still_works_with_one_database(dbs):
    spike_db, _ = dbs
    make_db(spike_db, spike=3)
    tally = spike_tally.collect(spike_db)                                    # as before: no other databases
    assert tally.slots_used == 3 and tally.count.breakdown() == "data/spike.db 3"


def test_the_run_cost_line_covers_both_files_and_the_per_file_line_says_it_is_one_file(dbs):
    # 6 lines in the spike file and 18 in the web app's, US$0.001 each: the old line showed 0.0060 only.
    spike_db, app_db = dbs
    make_db(spike_db, spike=6)
    make_db(app_db, spike=18)
    printed = []
    spike.main(["--tally"], env={**RUN_ENV, "DATABASE_PATH": str(app_db)}, spike_db=spike_db,
               out=printed.append)
    text = "\n".join(printed)
    assert "Run cost       : US$0.0240 recorded, every database counted above" in text
    assert "This file only : US$0.0060 recorded;" in text
    assert "(the tables below read this file only)" in text


def test_the_run_cost_total_equals_the_sum_of_the_per_database_costs(dbs):
    spike_db, app_db = dbs
    make_db(spike_db, spike=2)
    make_db(app_db, spike=5, demo=9)                                        # a demo line is not a spike call
    tally = spike_tally.collect(spike_db, other_databases=[app_db])
    assert tally.count.cost_usd == pytest.approx(sum(d.cost_usd for d in tally.count.databases))
    assert tally.count.cost_usd == pytest.approx(0.007)
    assert "Run cost       : US$0.0070 recorded" in spike_tally.format_tally(tally)

