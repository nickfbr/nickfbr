"""Shared ingredient-line parser.

Normalizes a single free-text ingredient line into (name, quantity, unit, raw),
flagging any measure word it could not map to the canonical unit enum. Used for
lines coming from recipe-scrapers (the LLM does its own parsing).

Order of operations (per spec §3.3):
1. Normalize unicode fractions (½ -> 0.5) and mixed numbers ("1 1/2" -> 1.5).
2. Extract the leading quantity (number or range; ranges -> lower bound).
3. Map the next token against the unit synonym map -> canonical enum.
4. The remainder is the name. The full original line is kept as `raw`.
"""

import re
from dataclasses import dataclass
from fractions import Fraction

from app.units import DEFAULT_UNIT, normalize_unit

# Unicode fraction characters -> ascii fraction string.
_UNICODE_FRACTIONS = {
    "½": "1/2",
    "⅓": "1/3",
    "⅔": "2/3",
    "¼": "1/4",
    "¾": "3/4",
    "⅕": "1/5",
    "⅖": "2/5",
    "⅗": "3/5",
    "⅘": "4/5",
    "⅙": "1/6",
    "⅚": "5/6",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
    "⅐": "1/7",
    "⅑": "1/9",
    "⅒": "1/10",
}

# Measure words that are NOT in the canonical enum. When one of these leads the
# line we still strip it (it is clearly a unit, not part of the name) but flag it
# in unmappedUnits so the user can fix it. Plain count nouns ("eggs") are NOT
# here, so "2 eggs" parses as quantity=2, unit=whole, name="eggs".
_EXTRA_UNIT_WORDS = frozenset(
    {
        "clove", "cloves", "can", "cans", "stick", "sticks", "slice", "slices",
        "sprig", "sprigs", "bunch", "bunches", "package", "packages", "pkg",
        "dash", "dashes", "handful", "handfuls", "drop", "drops", "sheet",
        "sheets", "head", "heads", "stalk", "stalks", "ear", "ears", "fillet",
        "fillets", "piece", "pieces", "jar", "jars", "bottle", "bottles",
        "packet", "packets", "scoop", "scoops", "knob", "knobs",
        "quart", "quarts", "qt", "pint", "pints", "pt", "gallon", "gallons",
        "gal", "stalks", "sachet", "sachets", "tin", "tins",
    }
)

# A single quantity token: mixed number, fraction, or decimal/integer.
_NUM = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"
_RANGE_RE = re.compile(rf"^\s*(?P<lo>{_NUM})\s*(?:-|–|—|to)\s*(?P<hi>{_NUM})", re.IGNORECASE)
_SINGLE_RE = re.compile(rf"^\s*(?P<n>{_NUM})")
_WORD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z_\.]*)")

# Multi-word units collapsed to a single canonical token before word matching.
_MULTIWORD_RE = [
    (re.compile(r"\bfl\.?\s*oz\.?", re.IGNORECASE), "fl_oz"),
    (re.compile(r"\bfluid\s+ounces?\b", re.IGNORECASE), "fl_oz"),
]


@dataclass
class ParsedLine:
    name: str
    quantity: float | None
    unit: str
    raw: str
    unmapped_unit: str | None = None


def _normalize_unicode_fractions(text: str) -> str:
    out: list[str] = []
    for ch in text:
        if ch in _UNICODE_FRACTIONS:
            frac = _UNICODE_FRACTIONS[ch]
            # "1½" -> "1 1/2"; "½" -> "1/2".
            if out and out[-1].isdigit():
                out.append(" ")
            out.append(frac)
        else:
            out.append(ch)
    return "".join(out)


def _to_float(token: str) -> float:
    token = token.strip()
    if " " in token:  # mixed number "1 1/2"
        whole, frac = token.split(None, 1)
        return float(int(whole) + Fraction(frac))
    if "/" in token:
        return float(Fraction(token))
    return float(token)


def parse_ingredient_line(raw: str) -> ParsedLine:
    raw = (raw or "").strip()
    if not raw:
        return ParsedLine(name="", quantity=None, unit=DEFAULT_UNIT, raw=raw)

    work = _normalize_unicode_fractions(raw)
    for pattern, replacement in _MULTIWORD_RE:
        work = pattern.sub(replacement, work)

    quantity: float | None = None
    # 1. Quantity (range -> lower bound).
    m = _RANGE_RE.match(work)
    if m:
        quantity = _to_float(m.group("lo"))
        work = work[m.end():]
    else:
        m = _SINGLE_RE.match(work)
        if m:
            quantity = _to_float(m.group("n"))
            work = work[m.end():]

    # 2. Unit token (only consumed if it is a recognized measure word).
    unit = DEFAULT_UNIT
    unmapped: str | None = None
    wm = _WORD_RE.match(work)
    if wm:
        token = wm.group(1)
        canonical = normalize_unit(token)
        token_key = token.lower().rstrip(".")
        if canonical is not None:
            unit = canonical
            work = work[wm.end():]
        elif token_key in _EXTRA_UNIT_WORDS:
            unmapped = token
            work = work[wm.end():]
            # unit stays DEFAULT_UNIT ("whole")

    # 3. Remainder is the name.
    name = work.strip().strip(",").strip()
    if not name:
        # Whole line was quantity/unit with no name; fall back to original.
        name = raw

    return ParsedLine(
        name=name, quantity=quantity, unit=unit, raw=raw, unmapped_unit=unmapped
    )
