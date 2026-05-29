"""Anthropic-backed recipe parser (spec §3.2).

Sends raw recipe text (pasted, or extracted page text for the URL fallback) to
Claude and gets back strict JSON. Output is treated as untrusted and validated
by the caller against the Pydantic models before use.
"""

import json
import re

from app.config import get_settings
from app.errors import AppError

settings = get_settings()

_SYSTEM_PROMPT = """You convert a raw recipe into strict JSON. Output ONLY a JSON object, no prose, no markdown.

Schema:
{
  "title": string | null,
  "description": string | null,
  "ingredients": [ { "name": string, "quantity": number | null, "unit": string, "raw": string } ],
  "instructions": [ { "stepNumber": integer, "text": string } ],
  "servings": integer | null,
  "prepTime": integer | null,
  "cookTime": integer | null
}

Rules:
- "unit" MUST be exactly one of: "cups","tbsp","tsp","g","oz","ml","L","kg","whole","pinch","lb","fl_oz".
  If the source unit does not map cleanly, use "whole" and keep the original wording in "raw".
- Convert fractions and unicode fractions (1/2, 3/4) to decimals (0.5, 0.75).
- Convert ranges ("2-3 cloves") to the lower bound and note the range in "raw".
- "raw" is the original ingredient line, unmodified.
- stepNumber starts at 1 and increments by 1.
- prepTime/cookTime are integers in minutes; null if not stated.
- Do not invent ingredients or steps that are not present.
- If you cannot find a recipe at all, return all fields null/empty arrays."""

_MAX_TOKENS = 2000
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _invoke_model(text: str) -> str:
    """Single Anthropic API call. Returns the raw text content. Monkeypatched in tests."""
    try:
        import anthropic  # type: ignore
    except Exception as exc:  # pragma: no cover - import guard
        raise AppError("PARSER_UNAVAILABLE", "Parser is not configured.", status_code=502) from exc

    if not settings.anthropic_api_key:
        raise AppError("PARSER_UNAVAILABLE", "Parser is not configured.", status_code=502)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=_MAX_TOKENS,
        temperature=0,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                # Static instruction block — cache it to cut cost/latency.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": text}],
    )
    parts = [block.text for block in message.content if getattr(block, "type", None) == "text"]
    return "".join(parts).strip()


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        # Drop leading/trailing code fences defensively.
        raw = _FENCE_RE.sub("", raw)
        # Re-run for a trailing fence not caught by the anchored pattern.
        raw = re.sub(r"\s*```$", "", raw).strip()
    return raw


def parse_with_llm(text: str) -> dict:
    """Call the model (with one retry) and return parsed JSON as a dict.

    Raises AppError(PARSER_UNAVAILABLE) on persistent failure.
    """
    last_exc: Exception | None = None
    for attempt in range(2):  # one initial try + one retry
        try:
            raw = _invoke_model(text)
            cleaned = _strip_fences(raw)
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                raise ValueError("model did not return a JSON object")
            return data
        except AppError:
            raise
        except Exception as exc:  # transient API / JSON errors -> retry once
            last_exc = exc
            continue
    raise AppError(
        "PARSER_UNAVAILABLE",
        "Import is temporarily unavailable, please try again.",
        status_code=502,
    ) from last_exc
