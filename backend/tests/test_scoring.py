import pytest

from app.services import scoring


@pytest.mark.parametrize(
    ("cos", "expected"),
    [(0.40, 0.0), (0.55, 0.0), (0.725, 0.5), (0.90, 1.0), (0.99, 1.0)],
)
def test_semantic(cos, expected):
    assert scoring.semantic(cos, floor=0.55, span=0.35) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("total", "budget", "expected"),
    [
        (0, 100, 1.0),
        (50, 100, 0.925),
        (100, 100, 0.85),  # ratio = 1 boundary
        (125, 100, 0.5),
        (150, 100, 0.0),
        (300, 100, 0.0),
    ],
)
def test_price(total, budget, expected):
    assert scoring.price(total, budget) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("available", "required", "expected"),
    [(25, 100, 0.25), (100, 100, 1.0), (500, 100, 1.0)],  # available = required boundary
)
def test_quantity(available, required, expected):
    assert scoring.quantity(available, required) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("lead", "needed", "expected"),
    [(0, 10, 1.0), (5, 10, 0.9), (10, 10, 0.8), (15, 10, 0.5), (20, 10, 0.0), (40, 10, 0.0)],
)
def test_delivery(lead, needed, expected):
    assert scoring.delivery(lead, needed) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("distance", "a", "b", "expected"),
    [
        (0, "x", "y", 1.0),
        (50, "x", "y", 1.0),
        (1025, "x", "y", 0.5),
        (2000, "x", "y", 0.0),
        (9000, "x", "y", 0.0),
        (None, "Pune ", "pune", 1.0),
        (None, "Pune", "Nashik", 0.5),
    ],
)
def test_location(distance, a, b, expected):
    assert scoring.location(distance, a, b) == pytest.approx(expected)


def test_final_is_weighted_and_rounded():
    weights = {"semantic": 0.4, "price": 0.2, "quantity": 0.15, "delivery": 0.15, "location": 0.1}
    parts = {"semantic": 0.5, "price": 0.85, "quantity": 1, "delivery": 0.8, "location": 0.5}
    assert scoring.final(parts, weights) == 69.0
    assert scoring.final(dict.fromkeys(weights, 1.0), weights) == 100.0
    assert scoring.final({k: 1 / 3 for k in weights}, weights) == 33.33


def test_weights_must_sum_to_one(monkeypatch):
    from pydantic import ValidationError

    from app.config import Settings

    monkeypatch.setenv("WEIGHT_PRICE", "0.5")
    with pytest.raises(ValidationError, match="must sum to 1.0"):
        Settings()
