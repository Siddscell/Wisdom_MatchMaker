from app.models import Offering, Requirement

MANCHESTER = {"location": "Manchester", "latitude": 53.4808, "longitude": -2.2426}
FAKE_VECTOR = [1.0] + [0.0] * 383  # identical vectors -> cosine 1 -> semantic sub-score 1

LONDON = {"location": "London", "latitude": 51.5074, "longitude": -0.1278}


def add_requirement(db, **overrides) -> Requirement:
    fields = dict(
        client_name="Acme Ltd",
        contact_email="buyer@acme.test",
        product_requirement="steel pipe",
        category="Raw Materials & Metals",
        quantity=100,
        unit="kg",
        budget=1000,
        needed_within_days=10,
        embedding=FAKE_VECTOR,
        **MANCHESTER,
    )
    item = Requirement(**{**fields, **overrides})
    db.add(item)
    db.commit()
    return item


def add_offering(db, supplier_name: str, **overrides) -> Offering:
    fields = dict(
        supplier_name=supplier_name,
        contact_email=f"{supplier_name.lower()}@supplier.test",
        product_offered="mild steel tube",
        category="Raw Materials & Metals",
        available_quantity=100,
        unit="kg",
        unit_price=5,
        lead_time_days=5,
        delivery_scope="local",
        embedding=FAKE_VECTOR,
        **MANCHESTER,
    )
    item = Offering(**{**fields, **overrides})
    db.add(item)
    db.commit()
    return item
