CATEGORIES = [
    "Raw Materials & Metals",
    "Electronics & Electrical",
    "Packaging",
    "Textiles & Apparel",
    "Food & Agriculture",
    "Construction Materials",
    "Chemicals",
    "Machinery & Equipment",
    "Office & Consumables",
    "Other",
]

# Max delivery radius in km, used when both sides have coordinates. None = unlimited.
DELIVERY_SCOPES = {
    "local": 100,
    "regional": 500,
    "national": 5000,
    "international": None,
}

# unit -> (family, factor to the family's base unit)
UNIT_FAMILIES = {
    "kg": ("mass", 1),
    "tonne": ("mass", 1000),
    "piece": ("count", 1),
    "box": ("count", 1),
    "unit": ("count", 1),
    "metre": ("length", 1),
    "litre": ("volume", 1),
}
