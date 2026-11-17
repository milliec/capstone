"""Per-state page tests (SAD Tier 2; frontend.md §8 D-4). They check the rendered HTML against
the ux.md acceptance checks that a page alone can show. Stand-in mode, pause 0, no model.

A "state" is set up by clicking through with the test client, as a person would. The running
state cannot be reached that way (the test client finishes background work at once), so one test
sets the run's phase directly in the test database.
"""

import re

import pytest

PAGES = ["", "/g1", "/g2", "/g3"]
FORBIDDEN_WORDS = [
    r"\b[Rr]uns?\b",            # "Review" on screen, never "run" (the RUN- ID is not a word)
    r"\bStage [ABC]\b",
    r"\bG[123]\b",
    r"\b[Gg]ates?\b",
    r"[Pp]recautionary",
]


def _start(client, **switches):
    """Start a review and return its run ID (the redirect lands on its status page)."""
    response = client.post("/specialist/runs", data={k: "true" for k, v in switches.items() if v})
    return re.search(r"/specialist/runs/(RUN-[\d-]+)", str(response.url)).group(1)


def _visible_text(html):
    """The words a person reads: no tags, no attribute values, no <title> or <head>."""
    body = html.split("<body", 1)[1]
    body = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", body)
    return re.sub(r"<[^>]+>", " ", body)


def _all_pages(client, run_id):
    return {path: client.get(f"/specialist/runs/{run_id}{path}").text for path in PAGES}


@pytest.fixture
def at_g1(specialist_client):
    return _start(specialist_client, demo_planted_row=True)


def test_nothing_is_preselected_on_any_page(specialist_client, gp_client, at_g1):
    """UX-004, UX-011: no radio or checkbox is checked on load, on any page."""
    pages = _all_pages(specialist_client, at_g1)
    pages["filing rules"] = specialist_client.get("/specialist/runs").text
    pages["calendar"] = gp_client.get("/calendar").text
    for name, html in pages.items():
        assert not re.search(r"<input[^>]*\bchecked\b", html), name


def test_no_browser_checks_on_forms(specialist_client, at_g1):
    """ux.md §1.2: no required, disabled or pattern; the server refuses on the page instead."""
    for path, html in _all_pages(specialist_client, at_g1).items():
        for attribute in ("required", "disabled", "pattern="):
            assert not re.search(rf"<(input|textarea|select|button)[^>]*\b{attribute}", html), (path, attribute)


def test_g1_form_is_answer_first_with_separate_reason_names(specialist_client, at_g1):
    """UX-020, DL-48: the question first, then each answer's fields; distinct reason names."""
    html = specialist_client.get(f"/specialist/runs/{at_g1}/g1").text
    form = html.split('class="decision"', 1)[1].split("</form>", 1)[0]
    assert form.index('name="decision"') < form.index('name="business_day_rule"')
    assert 'name="reject_reason"' in form
    assert 'data-answer="approve"' in form and 'data-answer="reject"' in form
    for option in ("Move to the following working day", "Move to the preceding working day", "Keep the date"):
        assert option in form  # UX-015: exactly these three, no "not confirmed"
    assert "not confirmed" not in form.lower()


def test_demo_rule_keeps_its_approve_button(specialist_client, at_g1):
    """UX-003, H-009: the demo rule gets the same form; Approve is never hidden or disabled."""
    html = specialist_client.get(f"/specialist/runs/{at_g1}/g1").text
    cards = [c.split("</article>", 1)[0] for c in html.split("<article")[1:]]
    demo_cards = [c for c in cards if '<span class="chip ">Demo</span>' in c]
    assert len(demo_cards) == 1
    assert "Approve rule" in demo_cards[0] and 'value="approve"' in demo_cards[0]


def test_who_files_options_read_exactly(specialist_client, at_g1):
    """UX-016: the six "who files" options, in order, for a rule whose source is silent."""
    html = _visible_text(specialist_client.get(f"/specialist/runs/{at_g1}/g1").text)
    expected = ["AIFM", "Fund administrator", "Auditor", "Local reporting agent (Spain)", "Tax advisor", "Not known"]
    positions = [html.index(label) for label in expected]
    assert positions == sorted(positions)


def test_no_internal_words_on_screen(specialist_client, gp_client, at_g1):
    """UX-019: no "run", "Stage A/B/C", "G1/G2/G3", "gate" or "precautionary" in visible text."""
    pages = _all_pages(specialist_client, at_g1)
    pages["filing rules"] = specialist_client.get("/specialist/runs").text
    pages["calendar"] = gp_client.get("/calendar").text
    for name, html in pages.items():
        text = _visible_text(html)
        for pattern in FORBIDDEN_WORDS:
            assert not re.search(pattern, text), (name, pattern, re.search(pattern, text))


def test_status_is_a_word_in_every_pill(specialist_client, at_g1):
    """UX-007: every coloured pill carries its word."""
    for path, html in _all_pages(specialist_client, at_g1).items():
        for words in re.findall(r'<span class="chip[^"]*">([^<]*)</span>', html):
            assert words.strip(), path


def test_failed_review_has_no_retry(specialist_client):
    """UX-022: the Without-Retry page has no Retry form, button or text, and links to a new review."""
    run_id = _start(specialist_client, demo_fail_step1=True)
    html = specialist_client.get(f"/specialist/runs/{run_id}").text
    assert "This review failed" in html
    assert "/retry" not in html and "Retry" not in _visible_text(html)
    assert "Start a new review from Filing rules" in html


def test_refresh_only_while_working(specialist_client, db, at_g1):
    """UX-006: the page reloads itself only while AI or code works, and the stop link works."""
    status_page = f"/specialist/runs/{at_g1}"
    assert 'http-equiv="refresh"' not in specialist_client.get(status_page).text  # at a step

    db.execute("UPDATE runs SET phase = 'A_RUNNING' WHERE run_id = ?", (at_g1,))
    db.commit()
    working = specialist_client.get(status_page).text
    assert 'http-equiv="refresh"' in working
    assert "Stop automatic refresh" in working and "Last updated at" in working
    stopped = specialist_client.get(status_page + "?refresh=off").text
    assert 'http-equiv="refresh"' not in stopped
    assert "Automatic refresh is off." in stopped


def test_stop_refresh_is_the_first_tab_stop_while_refreshing(specialist_client, db, at_g1):
    """K-1 (ux-review): each reload sends focus to the top, so the stop link must come first."""
    status_page = f"/specialist/runs/{at_g1}"
    db.execute("UPDATE runs SET phase = 'A_RUNNING' WHERE run_id = ?", (at_g1,))
    db.commit()
    first_link = re.search(r"<body[^>]*>\s*<a [^>]*>([^<]+)</a>", specialist_client.get(status_page).text)
    assert first_link.group(1) == "Stop automatic refresh"
    stopped = specialist_client.get(status_page + "?refresh=off").text
    assert re.search(r"<body[^>]*>\s*<a [^>]*>([^<]+)</a>", stopped).group(1) == "Skip to the main content"


def test_each_decision_question_names_its_rule_for_screen_readers(specialist_client, at_g1):
    """K-2 (ux-review): the legend carries the rule's name, hidden visually, on every card."""
    html = specialist_client.get(f"/specialist/runs/{at_g1}/g1").text
    legends = re.findall(r"<legend>What's your decision on this rule\?<span class=\"sr\"> ([^<]+)</span>", html)
    assert legends and all(name.startswith("Rule ") for name in legends)
    assert len(set(legends)) == len(legends)  # each one different


def test_empty_calendar_shows_only_the_message(gp_client):
    """UX-008, D11: before the first publication, the fixed message and nothing else."""
    html = gp_client.get("/calendar").text
    assert ("Your compliance calendar is being prepared and checked by a specialist. Nothing has "
            "been published yet. The deadlines will appear here once it is published.") in html
    assert "<table" not in html


def test_general_partner_note_reads_exactly(specialist_client, gp_client, at_g1):
    """UX-018: the General Partner's short note; and no moved or open-question mark (UX-009)."""
    run_id = at_g1
    specialist_client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    specialist_client.post(f"/specialist/runs/{run_id}/g2/complete", data={"run_version": 2})
    specialist_client.post(f"/specialist/calendars/CAL-{run_id}/publish",
                           data={"run_version": 3, "decision": "publish", "acknowledged": "true"})
    html = gp_client.get("/calendar").text
    assert ("These dates are the specialist's approved reading of the rules. Not legal advice. "
            "Date counting hasn't yet been checked against the legal texts.") in html
    text = _visible_text(html)
    assert "Moved off a weekend" not in text and "OQ-7" not in text


def test_every_page_links_the_stylesheet_and_a_skip_link(specialist_client, at_g1):
    for path, html in _all_pages(specialist_client, at_g1).items():
        assert '<link rel="stylesheet" href="/static/site.css">' in html, path
        assert 'href="#main"' in html and 'id="main"' in html, path


# --- H-036 V-3 and V-6 (operator, 2026-11-17): the templates use the server's values when sent ---
# The stub services do not send `steps` or `failure` yet, so these render the templates directly
# with server-style values, and check they win over the fixed ux.md tables (the fallback).

FUND = {"fund_id": "FND-DEMO-01", "name": "Fictional fund", "regime": "Regime", "year_end": "31 Dec"}


def _render(template, **context):
    from backend.web.deps import templates
    return templates.env.get_template(template).render(**context)


def test_stepper_uses_the_servers_steps_when_sent():
    from backend.web.deps import templates
    macros = templates.env.get_template("parts/macros.html").make_module({"fund": FUND})
    run = {"run_id": "RUN-X", "status": "ACTIVE", "phase": "A_RUNNING", "steps": [
        {"state": "Done", "href": "/step-1", "current": False},
        {"state": "Your turn", "href": "/step-2", "current": True},
        {"state": "Not started", "href": None, "current": False},
        {"state": "Not started", "href": None, "current": False}]}
    html = str(macros.stepper(run))
    assert 'href="/step-2"' in html and ">Your turn<" in html
    assert "In progress" not in html  # what the fallback would say for A_RUNNING
    assert html.count('aria-current="step"') == 1
    without = str(macros.stepper({k: v for k, v in run.items() if k != "steps"}))
    assert "In progress" in without  # no server steps: the fixed table


def test_failed_sentence_uses_the_servers_failure_when_sent():
    run = {"run_id": "RUN-X", "status": "FAILED", "phase": "B_RUNNING", "status_words": "Failed",
           "is_working": False, "is_at_gate": False, "agents_mode": "stand_in",
           "demo_planted_row": 0, "demo_fail_step1": 0, "cost_so_far": 0, "run_version": 3,
           "started_at": "2026-11-17T09:00:00+00:00", "fund_id": "FND-DEMO-01",
           "failure": {"step": 3, "step_name": "You confirm what applies",
                       "unit_label": "Server unit label", "reason_sentence": "Server reason sentence"}}
    html = _render("pages/review_status.html", run=run, units=[], fund=FUND, identity=None,
                   agents_mode="stand_in", your_turn=False, current_path="/", refresh_on=True,
                   rendered_at="2026-11-17T09:00:00+00:00")
    assert ("This review failed at step 3 (You confirm what applies), at unit Server unit label. "
            "Server reason sentence. Nothing moved forward.") in " ".join(html.split())


# --- Page 7 week grid and month grouping (operator, 2026-11-17: display-only) ---

def _publish(client, run_id):
    client.post(f"/specialist/runs/{run_id}/g1/complete", data={"run_version": 1})
    client.post(f"/specialist/runs/{run_id}/g2/complete", data={"run_version": 2})
    client.post(f"/specialist/calendars/CAL-{run_id}/publish",
                data={"run_version": 3, "decision": "publish", "acknowledged": "true"})


def test_week_grid_is_a_visual_view_with_no_tab_stops(specialist_client, gp_client, at_g1):
    """The list is the accessible view; the List view's grid repeats it visually, hidden from screen
    readers, with no Tab stops. The view switch above it is ordinary links (B12)."""
    _publish(specialist_client, at_g1)
    html = gp_client.get("/calendar").text
    views = html.split('<section class="section views"', 1)[1].split("</section>", 1)[0]
    assert '<h2 id="views-h">The next two months</h2>' in views
    grid = views.split('<div class="grid-view" aria-hidden="true">', 1)[1]
    assert "Due next" in grid
    assert not re.search(r"<(a|button|input|select|textarea)\b|tabindex", grid)  # nothing to Tab to
    assert "Moved off a weekend" not in grid and "OQ-7" not in grid  # CR-012, UX-009
    assert html.index('<section class="section views"') < html.index('id="entries-h"')


def test_list_is_grouped_by_month_with_row_group_headers(specialist_client, gp_client, at_g1):
    _publish(specialist_client, at_g1)
    html = gp_client.get("/calendar").text
    list_part = html.split('id="entries-h"', 1)[1]
    assert re.search(r'<th colspan="4" scope="rowgroup">April 2027</th>', list_part)
    assert "All entries for 2027" in html


# --- H-036 V-4 (operator, 2026-11-17): units shown under the server's `group` ---

def _status_page(units):
    run = {"run_id": "RUN-X", "status": "ACTIVE", "phase": "AT_G1", "status_words": "Your turn: check the rules",
           "is_working": False, "is_at_gate": True, "agents_mode": "stand_in", "demo_planted_row": 0,
           "demo_fail_step1": 0, "cost_so_far": 0, "run_version": 1,
           "started_at": "2026-11-17T09:00:00+00:00", "fund_id": "FND-DEMO-01"}
    return " ".join(_render("pages/review_status.html", run=run, units=units, fund=FUND, identity=None,
                            agents_mode="stand_in", your_turn=False, current_path="/", refresh_on=True,
                            rendered_at="2026-11-17T09:00:00+00:00").split())


def _unit(label, stage, **extra):
    return {"label": label, "stage": stage, "status": "done", "stage_attempt": 1, **extra}


def test_units_follow_the_servers_group_in_ux_order():
    html = _status_page([
        _unit("Rule check one", "A", group="checking_drafts"),   # sent first, shown second
        _unit("Source doc one", "A", group="drafting"),
        _unit("Odd unit", "A", group="something_new"),
    ])
    headings = re.findall(r'<h3 class="sq[^"]*" id="units-([a-z_]+)">([^<]+)</h3>', html)
    assert headings == [("drafting", "Drafting the rules"), ("checking_drafts", "Checking the drafts"),
                        ("other", "Other units")]
    assert html.index("Source doc one") < html.index("Rule check one") < html.index("Odd unit")


def test_units_without_group_fall_back_to_todays_view():
    html = _status_page([_unit("Source doc one", "A"), _unit("Source doc two", "A")])
    headings = re.findall(r'id="units-([a-z_]+)">([^<]+)</h3>', html)
    assert headings == [("drafting", "Drafting the rules")]  # no "Checking the drafts" yet


# --- B12 (operator, 2026-11-17; DL-49, H-040): views chosen by a link, dot chart ---

def test_view_switch_marks_the_current_view_and_defaults_to_list(specialist_client, gp_client, at_g1):
    _publish(specialist_client, at_g1)
    for query, current in [("", "List"), ("?view=month", "Month"), ("?view=year", "Year"), ("?view=nonsense", "List")]:
        html = gp_client.get("/calendar" + query).text
        nav = html.split('<nav class="tabs" aria-label="Show the calendar as">', 1)[1].split("</nav>", 1)[0]
        assert re.findall(r'aria-current="page">([A-Za-z]+)<', nav) == [current], query


def test_month_view_is_a_table_with_weekday_headers_and_paging(specialist_client, gp_client, at_g1):
    _publish(specialist_client, at_g1)
    html = gp_client.get("/calendar?view=month").text
    table = html.split('<table class="month-table"', 1)[1].split("</table>", 1)[0]
    assert re.findall(r'<th scope="col">([A-Za-z]+)</th>', table) == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert "Due next" in table and "May not be required" in table
    assert 'href="/calendar?view=month&amp;month=2027-05"' in html  # the next-month link
    assert "No filings this month." in gp_client.get("/calendar?view=month&month=2027-05").text


def test_year_view_is_a_table_with_row_and_column_headers(specialist_client, gp_client, at_g1):
    _publish(specialist_client, at_g1)
    html = gp_client.get("/calendar?view=year").text
    table = html.split('<table class="year-table">', 1)[1].split("</table>", 1)[0]
    assert '<caption class="sr">Filings in 2027, by month</caption>' in table
    assert len(re.findall(r'<th scope="col"', table)) == 13 and re.search(r'<th scope="row">', table)
    assert "(may not be required)" in table  # the dashed tile also says it in words


def test_no_view_shows_moved_or_open_question_marks(specialist_client, gp_client, at_g1):
    """CR-012, DL-49: the views and the chart count only what the General Partner may see."""
    _publish(specialist_client, at_g1)
    for query in ["", "?view=month", "?view=year"]:
        text = _visible_text(gp_client.get("/calendar" + query).text)
        assert "Moved off a weekend" not in text and "OQ-7" not in text, query


def test_dot_chart_writes_its_counts_as_text(specialist_client, gp_client, at_g1):
    _publish(specialist_client, at_g1)
    html = gp_client.get("/calendar").text
    assert '<h2 class="k" id="dots-h">Entries in 2027: 2</h2>' in html
    assert "May not be required: 1" in html
    assert re.search(r'<svg class="dots"[^>]*aria-hidden="true"', html)
