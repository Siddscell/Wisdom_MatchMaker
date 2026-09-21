import pytest
from factories import LONDON, add_offering, add_requirement
from sqlalchemy import func, select

from app.models import EmailOutbox, Match, Notification
from app.services.matching import match_offering, match_requirement

pytestmark = pytest.mark.db


def matched_suppliers(db, requirement_id):
    db.expire_all()
    rows = db.scalars(select(Match).where(Match.requirement_id == requirement_id))
    return {m.offering.supplier_name for m in rows}


def test_hard_filters_exclude_what_they_should(db):
    r = add_requirement(db)  # 100 kg, budget 1000, 10 days, Manchester
    add_offering(db, "Good")
    add_offering(db, "Tonnes", available_quantity=0.5, unit="tonne", unit_price=5000)
    add_offering(db, "FarButGlobal", delivery_scope="international", **LONDON)
    add_offering(db, "OtherCategory", category="Packaging")
    add_offering(db, "Litres", unit="litre")
    add_offering(db, "TooLittle", available_quantity=20)  # < 25% of 100
    add_offering(db, "TooSlow", lead_time_days=21)  # > 2 x 10 days
    add_offering(db, "TooPricey", unit_price=16)  # 1600 > 1.5 x 1000
    add_offering(db, "TooFar", **LONDON)  # local scope, ~260 km away
    add_offering(db, "Inactive", status="inactive")

    match_requirement(r.id)

    assert matched_suppliers(db, r.id) == {"Good", "Tonnes", "FarButGlobal"}


def test_box_and_piece_never_match(db):
    r = add_requirement(db, unit="piece")
    add_offering(db, "Boxes", unit="box")
    add_offering(db, "Pieces", unit="piece")
    match_requirement(r.id)
    assert matched_suppliers(db, r.id) == {"Pieces"}


def test_offering_side_mirrors_requirement_side(db):
    r = add_requirement(db)
    o = add_offering(db, "Late")
    match_offering(o.id)
    assert matched_suppliers(db, r.id) == {"Late"}


def test_results_sorted_and_capped(db, client):
    r = add_requirement(db)
    for i in range(12):  # cheaper -> higher price sub-score -> higher total
        add_offering(db, f"S{i}", unit_price=5 + i * 0.5)
    match_requirement(r.id)

    scores = [m["score"] for m in client.get(f"/api/matches?requirement_id={r.id}").json()]
    assert len(scores) == 10  # MAX_MATCHES_PER_ITEM
    assert scores == sorted(scores, reverse=True)


def test_rerun_is_idempotent_keeps_status_and_notifies_once(db, client):
    r = add_requirement(db)
    add_offering(db, "A")
    add_offering(db, "B", unit_price=6)

    match_requirement(r.id)
    first = client.get("/api/matches").json()
    assert {m["status"] for m in first} == {"notified"}
    decided = client.patch(f"/api/matches/{first[0]['id']}/status", json={"status": "rejected"})
    assert decided.status_code == 200

    match_requirement(r.id)
    for offering_id in {m["offering_id"] for m in first}:
        match_offering(offering_id)

    second = client.get("/api/matches").json()
    assert [m["id"] for m in second] == [m["id"] for m in first]
    assert second[0]["status"] == "rejected"
    assert db.scalar(select(func.count()).select_from(Notification)) == 4  # 2 matches x 2 sides
    assert db.scalar(select(func.count()).select_from(EmailOutbox)) == 4


def test_fair_match_is_stored_but_not_notified(db):
    # semantic 1 (40) + price ratio 1.4 (4) + quantity 0.3 (4.5) + lead = needed (12)
    # + no coordinates, different place (5) = 65.5: between MATCH_MIN 60 and NOTIFY_MIN 70
    r = add_requirement(db, latitude=None, longitude=None)
    add_offering(
        db,
        "Fair",
        available_quantity=30,
        unit_price=14,
        lead_time_days=10,
        location="Leeds",
        latitude=None,
        longitude=None,
    )
    match_requirement(r.id)
    db.expire_all()
    match = db.scalars(select(Match)).one()
    assert (match.score, match.status) == (65.5, "new")
    assert db.scalar(select(func.count()).select_from(Notification)) == 0
