"""Parse orchestration (spec §3).

Selects the parse path (structured data -> LLM fallback for URLs, LLM for text),
builds a validated ParsedRecipeDraft, computes confidence/warnings/unmappedUnits,
re-sequences steps, and clamps numeric ranges. Never persists anything.
"""

from app.config import get_settings
from app.errors import AppError
from app.parsing.fetcher import fetch_html
from app.parsing.html_text import html_to_text
from app.parsing.ingredient_parser import parse_ingredient_line
from app.parsing.llm_parser import parse_with_llm
from app.parsing.scraper_adapter import scrape
from app.schemas import (
    ParsedIngredient,
    ParsedInstruction,
    ParsedRecipeDraft,
    ParseMeta,
    ParseRequest,
    ParseResponse,
)
from app.units import UNIT_SET

settings = get_settings()

_SERVINGS_RANGE = (1, 100)
_TIME_RANGE = (0, 6000)


def parse(req: ParseRequest) -> ParseResponse:
    if req.url:
        return _parse_url(req.url.strip())
    assert req.text is not None  # guaranteed by ParseRequest validation
    return _parse_text(req.text)


# --------------------------------------------------------------------------- #
# Path: text -> LLM
# --------------------------------------------------------------------------- #
def _parse_text(text: str) -> ParseResponse:
    data = parse_with_llm(text)
    draft, unmapped = _draft_from_llm(data, source_url=None)
    return _finalize(draft, "llm", unmapped, warnings=[])


# --------------------------------------------------------------------------- #
# Path: URL -> structured data, else LLM fallback
# --------------------------------------------------------------------------- #
def _parse_url(url: str) -> ParseResponse:
    final_url, html = fetch_html(url)  # raises URL_NOT_ALLOWED / FETCH_FAILED

    scraped = scrape(html, final_url)
    if scraped is not None:
        draft, unmapped = _draft_from_scraper(scraped, source_url=final_url)
        return _finalize(draft, "structured_data", unmapped, warnings=[])

    # Fall back to the LLM on extracted page text.
    page_text = html_to_text(html)[: settings.max_text_length]
    data = parse_with_llm(page_text)
    draft, unmapped = _draft_from_llm(data, source_url=final_url)
    return _finalize(
        draft,
        "llm_fallback",
        unmapped,
        warnings=["No structured recipe data was found; parsed the page text with AI."],
    )


# --------------------------------------------------------------------------- #
# Draft builders
# --------------------------------------------------------------------------- #
def _draft_from_scraper(scraped: dict, source_url: str | None) -> tuple[ParsedRecipeDraft, list[str]]:
    unmapped: list[str] = []
    ingredients: list[ParsedIngredient] = []
    for line in scraped.get("ingredients", []):
        parsed = parse_ingredient_line(line)
        if parsed.unmapped_unit:
            unmapped.append(parsed.unmapped_unit)
        ingredients.append(
            ParsedIngredient(
                name=parsed.name, quantity=parsed.quantity, unit=parsed.unit, raw=parsed.raw
            )
        )

    instructions = [
        ParsedInstruction(step_number=i + 1, text=str(t))
        for i, t in enumerate(scraped.get("instructions", []))
        if str(t).strip()
    ]

    prep = scraped.get("prep_time")
    cook = scraped.get("cook_time")
    if prep is None and cook is None and scraped.get("total_time") is not None:
        cook = scraped.get("total_time")

    draft = ParsedRecipeDraft(
        title=scraped.get("title"),
        description=None,
        ingredients=ingredients,
        instructions=instructions,
        servings=scraped.get("servings"),
        prep_time=prep,
        cook_time=cook,
        source_url=source_url,
    )
    return draft, unmapped


def _draft_from_llm(data: dict, source_url: str | None) -> tuple[ParsedRecipeDraft, list[str]]:
    unmapped: list[str] = []
    ingredients: list[ParsedIngredient] = []
    for item in data.get("ingredients", []) or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        raw = str(item.get("raw") or name).strip()
        if not name and not raw:
            continue
        unit_value = item.get("unit")
        if unit_value and unit_value not in UNIT_SET:
            unmapped.append(str(unit_value))
        ingredients.append(
            ParsedIngredient(
                name=name or raw,
                quantity=_as_float(item.get("quantity")),
                unit=str(unit_value) if unit_value else "whole",  # coerced by validator
                raw=raw or name,
            )
        )

    instructions: list[ParsedInstruction] = []
    for i, step in enumerate(data.get("instructions", []) or []):
        if isinstance(step, dict):
            text = str(step.get("text") or "").strip()
        else:
            text = str(step).strip()
        if text:
            instructions.append(ParsedInstruction(step_number=i + 1, text=text))

    draft = ParsedRecipeDraft(
        title=_as_str(data.get("title")),
        description=_as_str(data.get("description")),
        ingredients=ingredients,
        instructions=instructions,
        servings=_as_int(data.get("servings")),
        prep_time=_as_int(data.get("prepTime", data.get("prep_time"))),
        cook_time=_as_int(data.get("cookTime", data.get("cook_time"))),
        source_url=source_url,
    )
    return draft, unmapped


# --------------------------------------------------------------------------- #
# Finalization: re-sequence, clamp, confidence, UNPARSEABLE
# --------------------------------------------------------------------------- #
def _finalize(
    draft: ParsedRecipeDraft,
    method: str,
    unmapped_units: list[str],
    warnings: list[str],
) -> ParseResponse:
    warnings = list(warnings)

    # UNPARSEABLE: nothing usable extracted.
    if not draft.ingredients and not draft.instructions:
        raise AppError(
            "UNPARSEABLE",
            "We couldn't find a usable recipe in that input.",
            status_code=422,
        )

    # Re-sequence steps 1..N regardless of source numbering.
    for i, instruction in enumerate(draft.instructions, start=1):
        instruction.step_number = i

    # Clamp numeric ranges; out-of-range -> None + warning.
    draft.servings, w = _clamp(draft.servings, *_SERVINGS_RANGE, "servings")
    warnings += w
    draft.prep_time, w = _clamp(draft.prep_time, *_TIME_RANGE, "prep time")
    warnings += w
    draft.cook_time, w = _clamp(draft.cook_time, *_TIME_RANGE, "cook time")
    warnings += w

    # Dedupe unmapped units, preserving order.
    seen: set[str] = set()
    unmapped_units = [u for u in unmapped_units if not (u in seen or seen.add(u))]
    if unmapped_units:
        warnings.append(
            "Some units could not be recognized and were set to 'whole': "
            + ", ".join(unmapped_units)
        )

    confidence = _confidence(draft, method, unmapped_units)

    meta = ParseMeta(
        parse_method=method,  # type: ignore[arg-type]
        confidence=confidence,  # type: ignore[arg-type]
        warnings=warnings,
        unmapped_units=unmapped_units,
    )
    return ParseResponse(draft=draft, meta=meta)


def _confidence(draft: ParsedRecipeDraft, method: str, unmapped: list[str]) -> str:
    has_ing = len(draft.ingredients) > 0
    has_instr = len(draft.instructions) > 0

    # low: only one of ingredients/instructions, or many unmapped units.
    if not (has_ing and has_instr) or len(unmapped) >= 3:
        return "low"
    # high: structured data, or a complete LLM result with clean units.
    if method == "structured_data":
        return "high"
    if draft.title and has_ing and has_instr and not unmapped:
        if draft.prep_time is not None or draft.cook_time is not None:
            return "high"
    # otherwise: usable but missing title/times or thin on steps.
    return "medium"


# --------------------------------------------------------------------------- #
# Coercion helpers
# --------------------------------------------------------------------------- #
def _clamp(value: int | None, lo: int, hi: int, label: str) -> tuple[int | None, list[str]]:
    if value is None:
        return None, []
    if value < lo or value > hi:
        return None, [f"Ignored out-of-range {label} value ({value})."]
    return value, []


def _as_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _as_str(value) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None
