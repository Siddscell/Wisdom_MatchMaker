import pytest

from app.services import units


def test_comparable():
    assert units.comparable("kg", "tonne")
    assert units.comparable("box", "box")
    assert not units.comparable("box", "piece")  # same family, never converted
    assert not units.comparable("kg", "litre")
    assert not units.comparable("kg", "furlong")


def test_convert():
    assert units.convert(2, "tonne", "kg") == 2000
    assert units.convert(500, "kg", "tonne") == 0.5
    assert units.convert(3, "quintal", "kg") == 300
    assert units.convert(7, "piece", "piece") == 7
    with pytest.raises(ValueError):
        units.convert(1, "box", "piece")


def test_comparable_units():
    assert set(units.comparable_units("kg")) == {"kg", "quintal", "tonne"}
    assert units.comparable_units("box") == ["box"]
