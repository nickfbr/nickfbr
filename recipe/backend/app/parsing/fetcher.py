"""Safe server-side URL fetcher (spec §5).

Follows redirects manually so each hop is re-validated against SSRF rules, caps
the body size, enforces a short timeout, and only accepts HTML responses. No
auth or cookies are forwarded.
"""

import httpx

from app.config import get_settings
from app.errors import AppError
from app.parsing.ssrf import assert_safe_url

settings = get_settings()

_USER_AGENT = "RecipeBox-Importer/1.0 (+https://example.com/recipe-importer)"
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


def _fetch_failed(message: str) -> AppError:
    return AppError("FETCH_FAILED", message, status_code=502)


def fetch_html(url: str) -> tuple[str, str]:
    """Fetch an HTML page safely.

    Returns (final_url, html_text). Raises AppError(URL_NOT_ALLOWED) for SSRF
    violations or AppError(FETCH_FAILED) for network/timeout/non-HTML problems.
    """
    timeout = httpx.Timeout(settings.fetch_timeout_seconds)
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    current = url
    try:
        # No cookies, no auth, manual redirects so we can re-check each hop.
        with httpx.Client(
            timeout=timeout, follow_redirects=False, headers=headers
        ) as client:
            for _ in range(settings.max_redirects + 1):
                assert_safe_url(current)  # re-validate every hop
                resp = client.get(current)

                if resp.status_code in _REDIRECT_STATUSES:
                    location = resp.headers.get("location")
                    if not location:
                        raise _fetch_failed("Redirect without a location.")
                    current = str(httpx.URL(current).join(location))
                    continue

                if resp.status_code >= 400:
                    raise _fetch_failed(f"Upstream returned HTTP {resp.status_code}.")

                content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                if content_type and content_type not in ("text/html", "application/xhtml+xml"):
                    raise _fetch_failed("The URL did not return an HTML page.")

                body = _read_capped(resp)
                return current, body

            raise _fetch_failed("Too many redirects.")
    except httpx.TimeoutException:
        raise _fetch_failed("The request timed out.")
    except httpx.HTTPError:
        raise _fetch_failed("Could not fetch that URL.")


def _read_capped(resp: httpx.Response) -> str:
    cap = settings.max_fetch_bytes
    content = resp.content
    if len(content) > cap:
        content = content[:cap]
    encoding = resp.encoding or "utf-8"
    try:
        return content.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return content.decode("utf-8", errors="replace")
