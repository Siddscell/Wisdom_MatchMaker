from app.constants import UNIT_FAMILIES


def comparable(a: str, b: str) -> bool:
    """Same family; count units (box/piece/unit) only when the unit strings are equal."""
    fa, fb = UNIT_FAMILIES.get(a), UNIT_FAMILIES.get(b)
    if fa is None or fb is None or fa[0] != fb[0]:
        return False
    return fa[0] != "count" or a == b


def comparable_units(unit: str) -> list[str]:
    return [u for u in UNIT_FAMILIES if comparable(unit, u)]


def factor(unit: str) -> float:
    return float(UNIT_FAMILIES[unit][1])


def convert(value: float, from_unit: str, to_unit: str) -> float:
    if not comparable(from_unit, to_unit):
        raise ValueError(f"{from_unit} and {to_unit} are not comparable")
    return value * factor(from_unit) / factor(to_unit)
