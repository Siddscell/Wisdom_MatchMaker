from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError

from app.schemas import RequirementIn
from app.services.matching import score_pair, visual_similarity

WEIGHTS = {"semantic": 0.4, "price": 0.2, "quantity": 0.15, "delivery": 0.15, "location": 0.1}


def unit(*values):
    v = np.zeros(512)
    v[: len(values)] = values
    return v / np.linalg.norm(v)


def listing(image=None, text=None, **fields):
    base = dict(quantity=100, unit="kg", budget=1000, needed_within_days=10, location="Pune")
    offer = dict(available_quantity=100, unit_price=5, lead_time_days=5)
    return SimpleNamespace(
        image_embedding=image, clip_text_embedding=text, **base, **offer, **fields
    )


def test_no_photos_means_no_visual_evidence():
    assert visual_similarity(listing(text=unit(1)), listing(text=unit(1))) is None


def test_photo_vs_photo_and_photo_vs_text_use_their_own_scales():
    same_photo = visual_similarity(listing(image=unit(1)), listing(image=unit(1)))
    assert same_photo == 1.0
    # cos 0.30 is strong photo<->text (floor 0.23, range 0.09); photo<->photo it would be nothing
    photo_vs_text = visual_similarity(listing(image=unit(0.30, 0.954)), listing(text=unit(1)))
    assert photo_vs_text == pytest.approx((0.30 - 0.23) / 0.09, abs=0.01)


def test_photo_strengthens_confident_text_and_decides_unsure_text():
    weak_text_cos = 0.60  # below SEMANTIC_FLOOR: text alone says "not similar"
    no_photo, _ = score_pair(listing(), listing(), weak_text_cos, 0, WEIGHTS)
    matching_photos, parts = score_pair(
        listing(image=unit(1)), listing(image=unit(1)), weak_text_cos, 0, WEIGHTS
    )
    assert matching_photos > no_photo and parts["visual"] == 1.0
    strong_text_cos = 0.93
    unrelated_photos, parts = score_pair(
        listing(image=unit(1)), listing(image=unit(0, 1)), strong_text_cos, 0, WEIGHTS
    )
    assert parts["semantic"] == 1.0 and parts["visual"] == 0.0
    unsure_text_cos = 0.72  # text semantic ~0.25: short names like "Mirrors" vs "glass robot"
    _, parts = score_pair(
        listing(image=unit(1)), listing(image=unit(0, 1)), unsure_text_cos, 0, WEIGHTS
    )
    assert parts["semantic"] == 0.0  # photos disagree, so the pair is dropped


def test_only_images_from_our_bucket_are_accepted():
    base = dict(
        client_name="Acme",
        product_requirement="Pipes",
        category="Packaging",
        quantity=1,
        unit="kg",
        budget=1,
        location="Pune",
        needed_within_days=1,
    )
    ok = "https://unused.supabase.co/storage/v1/object/public/listing-images/u1/a.jpg"
    assert RequirementIn(**base, image_url=ok).image_url == ok
    with pytest.raises(ValidationError, match="uploaded to this site"):
        RequirementIn(**base, image_url="http://169.254.169.254/latest/meta-data")
