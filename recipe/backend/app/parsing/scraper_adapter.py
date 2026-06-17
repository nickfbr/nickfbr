"""Adapter around the `recipe-scrapers` library (spec §3.1).

Reads embedded schema.org Recipe JSON-LD / microdata for hundreds of sites.
Returns a normalized dict of raw fields, or None if no usable recipe was found.
Ingredient lines are still free text — the caller runs them through the shared
ingredient-line parser.
"""

from typing import Any, Optional


def _safe(fn) -> Any:
    try:
        return fn()
    except Exception:
        return None


def scrape(html: str, url: str) -> Optional[dict]:
    """Return {title, ingredients[str], instructions[str], servings, total_time,
    prep_time, cook_time} or None if the page has no usable recipe."""
    try:
        from recipe_scrapers import scrape_html  # type: ignore
    except Exception:
        return None

    scraper = None
    try:
        # Newer API. wild_mode lets it attempt schema.org on unknown domains.
        scraper = scrape_html(html=html, org_url=url, wild_mode=True)
    except TypeError:
        try:
            scraper = scrape_html(html, org_url=url)  # older positional signature
        except Exception:
            scraper = None
    except Exception:
        scraper = None

    if scraper is None:
        return None

    title = _safe(scraper.title)
    ingredients = _safe(scraper.ingredients) or []

    # A usable structured result needs at least a title and ingredients.
    if not title or not ingredients:
        return None

    instructions_text = _safe(scraper.instructions) or ""
    instructions = [s.strip() for s in str(instructions_text).split("\n") if s.strip()]
    if not instructions:
        instructions = _safe(scraper.instructions_list) or []

    return {
        "title": title,
        "ingredients": [str(i) for i in ingredients],
        "instructions": [str(i) for i in instructions],
        "servings": _parse_servings(_safe(scraper.yields)),
        "total_time": _coerce_int(_safe(scraper.total_time)),
        "prep_time": _coerce_int(_safe(getattr(scraper, "prep_time", lambda: None))),
        "cook_time": _coerce_int(_safe(getattr(scraper, "cook_time", lambda: None))),
    }


def _parse_servings(yields: Any) -> Optional[int]:
    if yields is None:
        return None
    import re

    m = re.search(r"\d+", str(yields))
    return int(m.group()) if m else None


def _coerce_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
