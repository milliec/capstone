"""Mock sign-in works (SAD §4 "Sign-in and secrets", ux.md page 1 and §1.7)."""


def test_signed_out_visitor_is_sent_to_sign_in(client):
    response = client.get("/specialist/runs", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/sign-in"


def test_specialist_signs_in_and_sees_filing_rules(client):
    response = client.post("/sign-in", data={"identity_id": "specialist-1"})
    assert response.status_code == 200
    assert response.url.path == "/specialist/runs"
    assert "Compliance specialist" in response.text


def test_general_partner_signs_in_and_sees_the_calendar(client):
    response = client.post("/sign-in", data={"identity_id": "gp-1"})
    assert response.status_code == 200
    assert response.url.path == "/calendar"
    assert "General Partner / Fund Manager" in response.text


def test_unknown_identity_is_refused(client):
    response = client.post("/sign-in", data={"identity_id": "someone-else"})
    assert response.status_code == 422
    assert "session" not in client.cookies


def test_the_cookie_cannot_be_forged(client):
    """The session cookie is signed: a hand-made one is ignored, so the visitor is signed out."""
    client.cookies.set("session", "identity_id=specialist-1")
    response = client.get("/specialist/runs", follow_redirects=False)
    assert response.status_code == 303


def test_sign_out_ends_the_session(specialist_client):
    specialist_client.post("/sign-out")
    response = specialist_client.get("/specialist/runs", follow_redirects=False)
    assert response.status_code == 303


# --- H-096 PR 3 (b): `specialist-eval` is for the scripted evaluation gates, not a sign-in choice ---------

def test_the_sign_in_page_still_offers_exactly_two_identities(client):
    page = client.get("/sign-in").text
    assert page.count('name="identity_id"') == 2
    assert 'value="specialist-1"' in page and 'value="gp-1"' in page
    assert "specialist-eval" not in page and "Evaluation script" not in page


def test_specialist_eval_cannot_sign_in(client):
    response = client.post("/sign-in", data={"identity_id": "specialist-eval"})
    assert response.status_code == 422
    assert "session" not in client.cookies


def test_a_session_naming_specialist_eval_is_not_an_identity():
    from backend.services.auth import identity_from_session, sign_in
    assert sign_in("specialist-eval") is None
    assert identity_from_session({"identity_id": "specialist-eval"}) is None
