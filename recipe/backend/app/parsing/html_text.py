"""Lightweight HTML -> main text extraction for the LLM fallback path.

Strips script/style/nav/header/footer and tags, collapses whitespace. Dependency
-light on purpose; the structured-data path handles the high-quality extraction.
"""

import re

_DROP_BLOCKS = re.compile(
    r"<(script|style|noscript|nav|header|footer|svg|form|aside)\b[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\f\v]+")
_BLANK_LINES = re.compile(r"\n\s*\n+")


def html_to_text(html: str) -> str:
    text = _DROP_BLOCKS.sub(" ", html)
    # Turn block-level boundaries into newlines so steps stay separated.
    text = re.sub(r"</(p|div|li|h[1-6]|tr|br)\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = _TAG.sub("", text)
    text = _unescape(text)
    text = _WS.sub(" ", text)
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def _unescape(text: str) -> str:
    import html as _html

    return _html.unescape(text)
