"""Pure scoring functions (no I/O). Every sub-score is in 0..1."""


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def semantic(cos: float, floor: float, span: float) -> float:
    return clamp((cos - floor) / span)


def price(total: float, budget: float) -> float:
    ratio = total / budget
    if ratio <= 1:
        return 0.85 + 0.15 * (1 - ratio)
    return max(0.0, 1 - (ratio - 1) / 0.5)


def quantity(available: float, required: float) -> float:
    return min(1.0, available / required)


def delivery(lead: float, needed: float) -> float:
    if lead <= needed:
        return 0.8 + 0.2 * (1 - lead / needed)
    return max(0.0, 1 - (lead - needed) / needed)


def location(distance_km: float | None, place_a: str, place_b: str) -> float:
    """1 within 50 km, linear to 0 at 2000 km; without coordinates compare the place strings."""
    if distance_km is None:
        return 1.0 if place_a.strip().lower() == place_b.strip().lower() else 0.5
    return clamp(1 - (distance_km - 50) / (2000 - 50))


def final(parts: dict[str, float], weights: dict[str, float]) -> float:
    return round(100 * sum(weights[k] * parts[k] for k in weights), 2)
