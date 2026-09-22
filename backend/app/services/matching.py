"""Matching: hard filters (SQL) -> semantic retrieval (pgvector) -> score -> store -> notify.

Plain functions that open their own session, so they can run from FastAPI BackgroundTasks
today and from a worker queue (Celery/RQ) later without changes.
"""

import logging

import httpx
import numpy as np
from sqlalchemy import case, func, literal, or_, select, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, undefer

from app.config import get_settings
from app.constants import DELIVERY_SCOPES, UNIT_FAMILIES
from app.db import SessionLocal
from app.models import Match, Offering, Requirement
from app.services import scoring, units
from app.services.embedding import clip_image, clip_text, embed, record_text
from app.services.geo import geocode, haversine_sql
from app.services.ml import current_weights
from app.services.notifications import notify

log = logging.getLogger(__name__)

# international = unlimited; half the Earth's circumference exceeds any real distance.
_RADIUS_KM = {scope: km or 20_040 for scope, km in DELIVERY_SCOPES.items()}
_UNIT_FACTOR = {unit: float(f) for unit, (_, f) in UNIT_FAMILIES.items()}
_ACTIVE_STATUS = {Requirement: "open", Offering: "active"}


def match_requirement(requirement_id: str) -> None:
    _run(Requirement, requirement_id)


def match_offering(offering_id: str) -> None:
    _run(Offering, offering_id)


def rematch_all() -> None:
    with SessionLocal() as db:
        requirement_ids = db.scalars(select(Requirement.id)).all()
        offering_ids = db.scalars(select(Offering.id)).all()
    for rid in requirement_ids:
        match_requirement(rid)
    for oid in offering_ids:
        match_offering(oid)


def _run(model: type[Requirement] | type[Offering], item_id: str) -> None:
    settings = get_settings()
    with SessionLocal() as db:
        item = db.get(model, item_id)
        if item is None or item.status != _ACTIVE_STATUS[model]:
            return
        prepare(db, item)
        db.commit()  # keep the embedding/coordinates even if matching fails below

        weights = current_weights(db)  # learned from accept/reject; the WEIGHT_* prior at first
        scored = []
        for other, cos, distance_km in _candidates(db, item):
            r, o = (item, other) if model is Requirement else (other, item)
            score, parts = score_pair(r, o, cos, distance_km, weights)
            if score >= settings.MATCH_MIN_SCORE and parts["semantic"] >= settings.MIN_SEMANTIC:
                scored.append((score, parts, r, o))
        scored.sort(key=lambda row: row[0], reverse=True)

        for score, parts, r, o in scored[: settings.MAX_MATCHES_PER_ITEM]:
            match_id = _upsert(db, r, o, score, parts)
            if score >= settings.NOTIFY_MIN_SCORE:
                notify(db, match_id, r, o, score)
        db.commit()
        log.info(
            "Matched %s %s: %d candidates above threshold",
            model.__tablename__,
            item_id,
            len(scored),
        )


def prepare(db: Session, item: Requirement | Offering) -> None:
    """Embed once and geocode once (each step is skipped if already done)."""
    text = record_text(item.product, item.notes)
    if item.embedding is None:
        item.embedding = embed(text)
    if item.clip_text_embedding is None:
        item.clip_text_embedding = clip_text(text)
    if item.image_url and item.image_embedding is None:
        try:
            item.image_embedding = clip_image(item.image_url)
        except (httpx.HTTPError, OSError, ValueError):  # bad download or not an image
            log.warning("Could not embed %s; matching on text only", item.image_url, exc_info=True)
    if item.latitude is None and (point := geocode(db, item.location)):
        item.latitude, item.longitude = point


def score_pair(
    r: Requirement, o: Offering, cos: float, distance_km: float | None, weights: dict
) -> tuple[float, dict]:
    s = get_settings()
    required_in_offer_units = units.convert(r.quantity, r.unit, o.unit)
    text_semantic = scoring.semantic(cos, s.SEMANTIC_FLOOR, s.SEMANTIC_RANGE)
    visual = visual_similarity(r, o)
    parts = {
        # Unsure text: photos decide. Confident text: a photo can only strengthen it.
        "semantic": visual
        if visual is not None and text_semantic < s.TEXT_CONFIDENT
        else max(text_semantic, visual or 0.0),
        "price": scoring.price(o.unit_price * required_in_offer_units, r.budget),
        "quantity": scoring.quantity(
            units.convert(o.available_quantity, o.unit, r.unit), r.quantity
        ),
        "delivery": scoring.delivery(o.lead_time_days, r.needed_within_days),
        "location": scoring.location(distance_km, r.location, o.location),
    }
    score = scoring.final(parts, weights)
    # Raw inputs are kept too: they are the ranker's training features.
    breakdown = {**{k: round(v, 4) for k, v in parts.items()}, "cosine": round(cos, 4)}
    breakdown["text_semantic"] = round(text_semantic, 4)
    breakdown["visual"] = None if visual is None else round(visual, 4)
    breakdown["distance_km"] = None if distance_km is None else round(distance_km, 1)
    return score, breakdown


def visual_similarity(r, o) -> float | None:
    """CLIP evidence in 0..1 when at least one side has a photo: photo vs photo if both do,
    otherwise the photo against the other side's description. None without photos."""
    s = get_settings()
    if r.image_embedding is not None and o.image_embedding is not None:
        cos = float(np.dot(r.image_embedding, o.image_embedding))
        return scoring.semantic(cos, s.VISUAL_IMAGE_FLOOR, s.VISUAL_IMAGE_RANGE)
    photo, text = (
        (r.image_embedding, o.clip_text_embedding)
        if r.image_embedding is not None
        else (o.image_embedding, r.clip_text_embedding)
    )
    if photo is None or text is None:
        return None
    return scoring.semantic(float(np.dot(photo, text)), s.VISUAL_TEXT_FLOOR, s.VISUAL_TEXT_RANGE)


def _candidates(db: Session, item: Requirement | Offering):
    """Rows of (other_item, cosine_similarity, distance_km) that pass every hard filter,
    nearest first, at most RETRIEVE_K."""
    s = get_settings()
    known = item
    other = Offering if isinstance(item, Requirement) else Requirement
    r, o = (known, other) if other is Offering else (other, known)

    if known.latitude is None or known.longitude is None:
        distance, distance_ok = literal(None), true()  # cannot filter by distance
    else:
        distance = haversine_sql(r.latitude, r.longitude, o.latitude, o.longitude)
        distance_ok = or_(
            other.latitude.is_(None),
            other.longitude.is_(None),
            distance <= _lookup(o.delivery_scope, _RADIUS_KM),
        )

    rf, of = _lookup(r.unit, _UNIT_FACTOR), _lookup(o.unit, _UNIT_FACTOR)
    filters = [
        other.status == _ACTIVE_STATUS[other],
        other.embedding.is_not(None),
        other.unit.in_(units.comparable_units(known.unit)),
        # quantities and prices compared in the same unit
        o.available_quantity * of / rf >= s.MIN_QTY_FRACTION * r.quantity,
        o.lead_time_days <= s.MAX_LEAD_FACTOR * r.needed_within_days,
        o.unit_price * r.quantity * rf / of <= s.MAX_BUDGET_FACTOR * r.budget,
        distance_ok,
    ]
    if s.STRICT_CATEGORY:
        filters.append(other.category == known.category)

    vector_distance = other.embedding.cosine_distance(known.embedding)
    stmt = (
        select(other, 1 - vector_distance, distance)
        .options(undefer(other.image_embedding), undefer(other.clip_text_embedding))
        .where(*filters)
        .order_by(vector_distance)
        .limit(s.RETRIEVE_K)
    )
    return db.execute(stmt).all()


def _lookup(key, mapping: dict):
    """mapping[key] for a Python value, or the equivalent SQL CASE for a column."""
    return mapping[key] if isinstance(key, str) else case(mapping, value=key)


def _upsert(db: Session, r: Requirement, o: Offering, score: float, breakdown: dict) -> str:
    """Insert or refresh the score. Never touches status, so re-running is idempotent."""
    stmt = insert(Match).values(
        requirement_id=r.id, offering_id=o.id, score=score, score_breakdown=breakdown
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[Match.requirement_id, Match.offering_id],
        set_={
            "score": stmt.excluded.score,
            "score_breakdown": stmt.excluded.score_breakdown,
            "updated_at": func.now(),
        },
    ).returning(Match.id)
    return db.execute(stmt).scalar_one()
