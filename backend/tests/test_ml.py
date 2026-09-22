import numpy as np
import pytest
from factories import add_offering, add_requirement
from sqlalchemy import select, update

from app.models import Match
from app.services import ml
from app.services.matching import match_requirement

PRIOR = {"semantic": 0.4, "price": 0.2, "quantity": 0.15, "delivery": 0.15, "location": 0.1}


def synthetic(n, seed=0):
    """Decisions where only quantity decides acceptance."""
    rng = np.random.default_rng(seed)
    X = rng.uniform(0, 1, size=(n, 5))
    return X, (X[:, 2] > 0.5).astype(float)


def test_learns_what_drives_acceptance_and_trusts_data_gradually():
    few = ml.fit_weights(*synthetic(10), PRIOR, prior_strength=50)
    many = ml.fit_weights(*synthetic(2000), PRIOR, prior_strength=50)
    for weights in (few, many):
        assert sum(weights.values()) == pytest.approx(1, abs=1e-3)
        assert min(weights.values()) >= 0
    assert PRIOR["quantity"] < few["quantity"] < many["quantity"]
    assert many["quantity"] == max(many.values())


@pytest.mark.db
def test_retrain_needs_both_outcomes_then_changes_weights(db):
    r = add_requirement(db)
    for i in range(4):
        add_offering(db, f"S{i}", unit_price=5 + i)
    match_requirement(r.id)
    ids = db.scalars(select(Match.id)).all()

    db.execute(update(Match).values(status="accepted"))
    db.commit()
    assert ml.retrain()["weights"] == PRIOR  # one class only: nothing to learn yet

    db.execute(update(Match).where(Match.id.in_(ids[:2])).values(status="rejected"))
    db.commit()
    learned = ml.retrain()
    assert learned["labels"] == 4
    assert learned["weights"] != PRIOR
    assert ml.current_weights(db) == learned["weights"]
