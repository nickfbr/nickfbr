"""Canonical unit enum and synonym mapping.

Per the §6 product decision, the enum is extended with `lb` and `fl_oz` because
US recipes lean on them heavily. This is the single source of truth for units;
the DB column, API schemas, parser, and frontend dropdown all key off this list.
"""

# Canonical units. Order is meaningful for the frontend dropdown.
UNITS: tuple[str, ...] = (
    "cups",
    "tbsp",
    "tsp",
    "g",
    "oz",
    "ml",
    "L",
    "kg",
    "whole",
    "pinch",
    "lb",
    "fl_oz",
)

UNIT_SET = frozenset(UNITS)

# Fallback unit used when a source token cannot be mapped.
DEFAULT_UNIT = "whole"

# Synonym map: lowercase source token -> canonical unit.
# Keep keys lowercase; the parser lowercases tokens before lookup.
_SYNONYMS: dict[str, str] = {
    # volume
    "cup": "cups",
    "cups": "cups",
    "c": "cups",
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",
    "tbs": "tbsp",
    "tbsps": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "tsps": "tsp",
    "milliliter": "ml",
    "milliliters": "ml",
    "millilitre": "ml",
    "millilitres": "ml",
    "ml": "ml",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
    "l": "L",
    "fluidounce": "fl_oz",
    "fluidounces": "fl_oz",
    "floz": "fl_oz",
    "fl_oz": "fl_oz",
    # mass / weight
    "gram": "g",
    "grams": "g",
    "g": "g",
    "kilogram": "kg",
    "kilograms": "kg",
    "kg": "kg",
    "ounce": "oz",
    "ounces": "oz",
    "oz": "oz",
    "pound": "lb",
    "pounds": "lb",
    "lb": "lb",
    "lbs": "lb",
    # count / misc
    "pinch": "pinch",
    "pinches": "pinch",
    "whole": "whole",
}

# Case-sensitive single-letter tokens that collide when lowercased.
# "T" => tablespoon, "t" => teaspoon (classic recipe shorthand).
_CASE_SENSITIVE: dict[str, str] = {
    "T": "tbsp",
    "t": "tsp",
}


def normalize_unit(token: str | None) -> str | None:
    """Map a raw unit token to a canonical unit.

    Returns the canonical unit string, or None if the token does not correspond
    to any known unit (caller decides whether to treat that as `whole`).
    """
    if not token:
        return None
    stripped = token.strip()
    if not stripped:
        return None
    # Case-sensitive shorthand first (T vs t).
    if stripped in _CASE_SENSITIVE:
        return _CASE_SENSITIVE[stripped]
    key = stripped.lower().rstrip(".")
    return _SYNONYMS.get(key)
