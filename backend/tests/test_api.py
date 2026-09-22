import uuid

import pytest
from factories import add_offering, add_requirement

from app.services.matching import match_requirement

REQUIREMENT = {
    "client_name": "  Acme Ltd ",
    "product_requirement": "Steel pipe",
    "category": "Raw Materials & Metals",
    "quantity": 100,
    "unit": "kg",
    "budget": 1000,
    "location": "Mumbai",
    "needed_within_days": 10,
}
BUYER = "buyer@acme.test"  # factories' default requirement owner


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    return body["error"]["fields"]


def test_meta(client):
    meta = client.get("/api/meta").json()
    assert "Packaging" in meta["categories"]
    assert meta["units"][:3] == ["kg", "quintal", "tonne"]
    assert meta["delivery_scopes"]["international"] is None
    assert meta["score_thresholds"] == {"match_min": 60, "notify_min": 70}


def test_writes_need_login(client):
    assert_error(client.post("/api/requirements", json=REQUIREMENT), 401, "unauthorized")
    assert_error(client.get("/api/requirements/mine"), 401, "unauthorized")
    assert_error(client.get("/api/notifications"), 401, "unauthorized")


def test_validation_error_shape(client, login):
    login(BUYER)
    bad = {**REQUIREMENT, "quantity": 0, "unit": "bushel", "contact_email": "x@y.com"}
    fields = assert_error(client.post("/api/requirements", json=bad), 422, "validation_error")
    assert set(fields) == {"quantity", "unit", "contact_email"}  # email comes from the account
    assert fields["unit"].startswith("must be one of")


def test_role_must_match_listing_type(client, login):
    login("sales@steel.test", role="supplier")
    assert_error(client.post("/api/requirements", json=REQUIREMENT), 403, "forbidden")


def test_offering_scope_is_validated(client, login):
    login("sales@steel.test", role="supplier")
    body = {"supplier_name": "S", "delivery_scope": "galactic"}
    fields = assert_error(client.post("/api/offerings", json=body), 422, "validation_error")
    assert "delivery_scope" in fields
    assert "supplier_name" in fields  # shorter than 2 characters


def test_malformed_id_is_422(client):
    assert_error(client.get("/api/offerings/not-a-uuid"), 422, "validation_error")


def test_dev_routes_hidden_in_production(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setattr(get_settings(), "ENV", "production")
    assert_error(client.post("/api/dev/seed"), 404, "not_found")


def test_unexpected_error_keeps_shape_and_cors_headers(client):
    from app.db import get_db
    from app.main import app

    def broken_db():
        raise RuntimeError("boom")
        yield  # pragma: no cover

    app.dependency_overrides[get_db] = broken_db
    try:
        response = client.get("/api/dashboard/summary", headers={"Origin": "http://localhost:5173"})
    finally:
        app.dependency_overrides.clear()
    assert_error(response, 500, "internal_error")
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.db
def test_health(client, db):
    assert client.get("/health").json()["db"] == "ok"


@pytest.mark.db
def test_create_uses_account_email_and_public_view_hides_private_fields(client, db, login):
    login(BUYER)
    response = client.post("/api/requirements", json=REQUIREMENT)
    assert response.status_code == 201
    body = response.json()
    assert (body["client_name"], body["contact_email"], body["budget"]) == ("Acme Ltd", BUYER, 1000)
    assert [r["id"] for r in client.get("/api/requirements/mine").json()] == [body["id"]]

    login(None)
    public = client.get("/api/requirements").json()[0]
    assert "contact_email" not in public and "budget" not in public
    offer = add_offering(db, "Good")
    public_offer = client.get(f"/api/offerings/{offer.id}").json()
    assert "unit_price" not in public_offer and "contact_email" not in public_offer


@pytest.mark.db
def test_only_owner_edits_and_edits_rematch(client, db, login):
    r = add_requirement(db)
    add_offering(db, "Good")
    edited = {**REQUIREMENT, "product_requirement": "Mild steel pipe"}

    login("someone@else.test")
    assert_error(client.put(f"/api/requirements/{r.id}", json=edited), 403, "forbidden")

    login(BUYER)
    assert client.put(f"/api/requirements/{r.id}", json=edited).status_code == 200
    # the background re-match ran (TestClient runs background tasks) and re-embedded
    matches = client.get(f"/api/matches?requirement_id={r.id}").json()
    assert [m["supplier_name"] for m in matches] == ["Good"]


@pytest.mark.db
def test_close_and_reopen(client, db, login):
    r = add_requirement(db)
    login(BUYER)
    url = f"/api/requirements/{r.id}/status"
    assert_error(client.patch(url, json={"status": "inactive"}), 422, "validation_error")
    assert client.patch(url, json={"status": "closed"}).json()["status"] == "closed"
    add_offering(db, "Late")
    match_requirement(r.id)  # closed: no matching
    assert client.get("/api/matches").json() == []
    client.patch(url, json={"status": "open"})  # reopening re-matches
    assert len(client.get("/api/matches").json()) == 1


@pytest.mark.db
def test_unknown_ids_are_404(client, db, login):
    login(BUYER)
    missing = uuid.uuid4()
    assert_error(client.get(f"/api/requirements/{missing}"), 404, "not_found")
    assert_error(client.post(f"/api/notifications/{missing}/read"), 404, "not_found")
    response = client.patch(f"/api/matches/{missing}/status", json={"status": "accepted"})
    assert_error(response, 404, "not_found")


@pytest.mark.db
def test_status_flow_and_email_privacy(client, db, login):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)
    match = client.get(f"/api/requirements/{r.id}").json()["matches"][0]
    url = f"/api/matches/{match['id']}/status"

    login("stranger@else.test")
    assert_error(client.patch(url, json={"status": "accepted"}), 403, "forbidden")

    login(BUYER)
    assert_error(client.patch(url, json={"status": "new"}), 422, "validation_error")
    accepted = client.patch(url, json={"status": "accepted"}).json()
    assert accepted["status"] == "accepted"
    assert accepted["supplier_email"] == "good@supplier.test"  # visible to the parties...
    assert_error(client.patch(url, json={"status": "rejected"}), 409, "conflict")

    login(None)  # ...never to the public
    public = client.get("/api/matches").json()[0]
    assert public["supplier_email"] is None and public["client_email"] is None


@pytest.mark.db
def test_notifications_are_private_and_mark_read(client, db, login):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)

    login("good@supplier.test", role="supplier")
    theirs = client.get("/api/notifications").json()
    assert len(theirs) == 1 and theirs[0]["recipient_role"] == "supplier"

    login(BUYER)
    mine = client.get("/api/notifications").json()
    assert len(mine) == 1 and "Good" in mine[0]["message"]
    assert_error(client.post(f"/api/notifications/{theirs[0]['id']}/read"), 404, "not_found")
    client.post(f"/api/notifications/{mine[0]['id']}/read")
    assert client.get("/api/notifications", params={"unread": True}).json() == []


@pytest.mark.db
def test_dashboard_summary(client, db):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)
    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_requirements"] == 1
    assert summary["total_matches"] == 1
    assert summary["matches_by_status"]["notified"] == 1


@pytest.mark.db
def test_category_suggestion_uses_nearest_listing(client, db):
    none_yet = client.get("/api/categories/suggest", params={"text": "tubes"}).json()
    assert none_yet == {"category": None}
    add_offering(db, "Box", category="Packaging")
    suggestion = client.get("/api/categories/suggest", params={"text": "cartons"}).json()
    assert suggestion == {"category": "Packaging"}
