"""Learned parts of matching: ranker weights from accept/reject, and category suggestion.

Ranker: logistic regression on the stored sub-scores of decided matches. Its positive
coefficients, normalised to sum to 1, become the scoring weights, blended with the WEIGHT_*
prior in proportion to how much data exists (n / (n + RANKER_PRIOR_STRENGTH)). With no
labels the weights are exactly the prior; the score scale (0-100) never changes, so the
60/70 thresholds keep their meaning.
"""

import logging

import numpy as np
from sqlalchemy import func, select, union_all
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Match, ModelState, Offering, Requirement
from app.services.embedding import embed

log = logging.getLogger(__name__)
FEATURES = ["semantic", "price", "quantity", "delivery", "location"]
_KEY = "ranker_weights"


def fit_weights(X: np.ndarray, y: np.ndarray, prior: dict, prior_strength: int) -> dict:
    """Logistic regression (gradient descent, L2) -> non-negative weights summing to 1."""
    # ponytail: linear model on 5 features; switch to LightGBM LambdaMART once there are
    # thousands of decisions and interactions between features start to matter.
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(2000):
        p = 1 / (1 + np.exp(-(X @ w + b)))
        w -= 0.5 * (X.T @ (p - y) / len(y) + 0.01 * w)
        b -= 0.5 * float(np.mean(p - y))
    learned = np.clip(w, 0, None)
    prior_w = np.array([prior[f] for f in FEATURES])
    if learned.sum() == 0:
        return prior
    share = len(y) / (len(y) + prior_strength)
    blended = share * learned / learned.sum() + (1 - share) * prior_w
    return dict(zip(FEATURES, (blended / blended.sum()).round(4).tolist(), strict=True))


def retrain() -> dict:
    """Refit from every accepted/rejected match and store the weights (runs after decisions)."""
    settings = get_settings()
    with SessionLocal() as db:
        rows = db.execute(
            select(Match.score_breakdown, Match.status).where(
                Match.status.in_(("accepted", "rejected"))
            )
        ).all()
        weights = settings.weights
        if len({status for _, status in rows}) == 2:  # need both outcomes to learn anything
            X = np.array([[b[f] for f in FEATURES] for b, _ in rows])
            y = np.array([status == "accepted" for _, status in rows], dtype=float)
            weights = fit_weights(X, y, settings.weights, settings.RANKER_PRIOR_STRENGTH)
        value = {"weights": weights, "labels": len(rows)}
        db.execute(
            insert(ModelState)
            .values(key=_KEY, value=value)
            .on_conflict_do_update(
                index_elements=[ModelState.key], set_={"value": value, "updated_at": func.now()}
            )
        )
        db.commit()
    log.info("Ranker retrained on %d decisions: %s", len(rows), weights)
    return value


def current_weights(db: Session) -> dict:
    state = db.get(ModelState, _KEY)
    return state.value["weights"] if state else get_settings().weights


def suggest_category(db: Session, text: str) -> str | None:
    """Category of the most similar existing listing (1-NN over both tables)."""
    vector = embed(text)
    both = union_all(
        *(
            select(m.category, m.embedding.cosine_distance(vector).label("d")).where(
                m.embedding.is_not(None)
            )
            for m in (Requirement, Offering)
        )
    ).subquery()
    row = db.execute(select(both.c.category).order_by(both.c.d).limit(1)).first()
    return row[0] if row else None
