"""Wrong role gets 403, audited as FORBIDDEN (CR-004; part of EC-019; ux.md §1.7)."""


def _forbidden_count(db):
    (n,) = db.execute(
        "SELECT COUNT(*) FROM audit_log WHERE event_type = 'refusal' AND refusal_code = 'FORBIDDEN'"
    ).fetchone()
    return n


def test_general_partner_gets_403_on_a_specialist_page(gp_client, db):
    response = gp_client.get("/specialist/runs")
    assert response.status_code == 403
    assert "You don't have access to this" in response.text
    assert "Go to the calendar" in response.text
    assert _forbidden_count(db) == 1


def test_general_partner_gets_403_on_a_specialist_form(gp_client, db):
    response = gp_client.post("/specialist/runs", data={})
    assert response.status_code == 403
    (runs,) = db.execute("SELECT COUNT(*) FROM runs").fetchone()
    assert runs == 0  # nothing was started
    assert _forbidden_count(db) == 1


def test_role_is_checked_before_the_address(gp_client):
    """A review that does not exist still gives 403, so the GP never learns which reviews exist."""
    assert gp_client.get("/specialist/runs/RUN-20000101-99").status_code == 403


def test_specialist_gets_404_for_an_unknown_review(specialist_client, db):
    response = specialist_client.get("/specialist/runs/RUN-20000101-99")
    assert response.status_code == 404
    assert "We can't find that page" in response.text
    assert _forbidden_count(db) == 0  # a 404 is not recorded in the audit log


def test_both_roles_can_view_the_calendar(specialist_client, gp_client):
    assert specialist_client.get("/calendar").status_code == 200
    assert gp_client.get("/calendar").status_code == 200
