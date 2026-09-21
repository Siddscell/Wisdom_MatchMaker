import uuid

import pytest
from factories import add_offering, add_requirement

from app.services.matching import match_requirement

REQUIREMENT = {
    "client_name": "  Acme Ltd ",
    "contact_email": "Buyer@Acme.example.com",
    "product_requirement": "Steel pipe",
    "category": "Raw Materials & Metals",
    "quantity": 100,
    "unit": "kg",
    "budget": 1000,
    "location": "Manchester",
    "needed_within_days": 10,
}


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)
    return body["error"]["fields"]


def test_meta(client):
    meta = client.get("/api/meta").json()
    assert "Packaging" in meta["categories"]
    assert meta["units"][:2] == ["kg", "tonne"]
    assert meta["delivery_scopes"]["international"] is None
    assert meta["score_thresholds"] == {"match_min": 60, "notify_min": 70}


def test_validation_error_shape(client):
    bad = {**REQUIREMENT, "contact_email": "nope", "quantity": 0, "unit": "bushel", "extra": 1}
    fields = assert_error(client.post("/api/requirements", json=bad), 422, "validation_error")
    assert set(fields) == {"contact_email", "quantity", "unit", "extra"}
    assert fields["unit"].startswith("must be one of")


def test_offering_scope_is_validated(client):
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


@pytest.mark.db
def test_health(client, db):
    assert client.get("/health").json()["db"] == "ok"


@pytest.mark.db
def test_create_trims_normalises_and_returns_201(client, db):
    response = client.post("/api/requirements", json=REQUIREMENT)
    assert response.status_code == 201
    body = response.json()
    assert body["client_name"] == "Acme Ltd"
    assert body["contact_email"] == "buyer@acme.example.com"
    listed = client.get("/api/requirements", params={"email": "BUYER@acme.example.com"}).json()
    assert [r["id"] for r in listed] == [body["id"]]


@pytest.mark.db
def test_unknown_ids_are_404(client, db):
    missing = uuid.uuid4()
    assert_error(client.get(f"/api/requirements/{missing}"), 404, "not_found")
    assert_error(client.post(f"/api/notifications/{missing}/read"), 404, "not_found")
    response = client.patch(f"/api/matches/{missing}/status", json={"status": "accepted"})
    assert_error(response, 404, "not_found")


@pytest.mark.db
def test_status_flow_and_email_privacy(client, db):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)
    match = client.get(f"/api/requirements/{r.id}").json()["matches"][0]
    assert match["client_email"] is None and match["supplier_email"] is None

    url = f"/api/matches/{match['id']}/status"
    assert_error(client.patch(url, json={"status": "new"}), 422, "validation_error")
    accepted = client.patch(url, json={"status": "accepted"}).json()
    assert accepted["status"] == "accepted"
    assert accepted["supplier_email"] == "good@supplier.test"
    assert_error(client.patch(url, json={"status": "rejected"}), 409, "conflict")


@pytest.mark.db
def test_notifications_filter_and_mark_read(client, db):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)

    mine = client.get("/api/notifications", params={"email": "buyer@acme.test"}).json()
    assert len(mine) == 1 and mine[0]["recipient_role"] == "client"
    assert "Good" in mine[0]["message"]
    client.post(f"/api/notifications/{mine[0]['id']}/read")
    unread = client.get("/api/notifications", params={"email": "buyer@acme.test", "unread": True})
    assert unread.json() == []


@pytest.mark.db
def test_dashboard_summary(client, db):
    r = add_requirement(db)
    add_offering(db, "Good")
    match_requirement(r.id)
    summary = client.get("/api/dashboard/summary").json()
    assert summary["total_requirements"] == 1
    assert summary["total_matches"] == 1
    assert summary["matches_by_status"]["notified"] == 1


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
