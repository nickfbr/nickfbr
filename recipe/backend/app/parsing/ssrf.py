"""SSRF protection for server-side URL fetching (spec §5).

The parse endpoint fetches user-supplied URLs, so every URL — and every redirect
hop — must be validated against an allowlisted scheme and have its resolved IPs
checked against private/internal ranges before we connect.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from app.errors import AppError

_ALLOWED_SCHEMES = {"http", "https"}


def _block(message: str, url: str | None = None) -> AppError:
    fields = {"url": url} if url else None
    return AppError("URL_NOT_ALLOWED", message, status_code=400, fields=fields)


def _ip_is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Covers loopback (127/8, ::1), private (10/8, 172.16/12, 192.168/16,
    # fc00::/7), link-local (169.254/16 incl. 169.254.169.254 metadata), and
    # unspecified (0.0.0.0). Reserved/multicast blocked for good measure.
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def assert_safe_url(url: str) -> str:
    """Validate scheme + resolved host. Raises AppError(URL_NOT_ALLOWED) if unsafe.

    Returns the validated host (useful for the caller).
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise _block("Only http and https URLs can be imported.", url)
    host = parsed.hostname
    if not host:
        raise _block("URL has no host.", url)

    # A literal IP in the URL must itself be public.
    try:
        literal = ipaddress.ip_address(host)
        if _ip_is_blocked(literal):
            raise _block("That address range cannot be imported.", url)
        return host
    except ValueError:
        pass  # not a literal IP; resolve by name below

    # Resolve the hostname and reject if ANY resolved address is internal.
    try:
        infos = socket.getaddrinfo(host, parsed.port or None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise _block("Could not resolve that host.", url)

    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _ip_is_blocked(ip):
            raise _block("That URL resolves to a private address.", url)

    return host
