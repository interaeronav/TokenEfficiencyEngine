"""Destination validator for the web lane (research 49, mitigation 2).

Resolve first, then pin: every address a hostname resolves to is checked
against loopback / private / link-local / ULA / multicast / reserved
ranges, and the fetcher connects to the exact validated IP - never
re-resolving - which closes the DNS-rebinding race. Refusals are rule-6
shaped: one line, the exact fix.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

from tee.kernel.errors import TeeError

DEFAULT_PORTS = (80, 443)

_ALLOW_LOCAL_FIX = (
    "This address is private/internal. If you genuinely run a local service "
    "to read, set [web] allow_local = true in .tee/config.toml."
)


@dataclass(frozen=True)
class Target:
    """A validated destination: the URL plus the pinned IP to connect to."""

    url: str
    scheme: str
    host: str
    port: int
    ip: str


def _default_resolve(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips: list[str] = []
    for _family, _type, _proto, _canon, sockaddr in infos:
        ip = str(sockaddr[0]).split("%")[0]  # strip IPv6 zone id
        if ip not in ips:
            ips.append(ip)
    return ips


def _address_category(ip: str) -> str | None:
    """The blocked-range category for an IP, or None when it is public."""
    parsed: ipaddress.IPv4Address | ipaddress.IPv6Address = ipaddress.ip_address(ip)
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        parsed = parsed.ipv4_mapped  # ::ffff:127.0.0.1 is loopback, not "IPv6 global"
    if parsed.is_loopback:
        return "loopback"
    if parsed.is_link_local:
        return "link-local (cloud metadata lives here)"
    if parsed.is_multicast:
        return "multicast"
    if parsed.is_unspecified:
        return "unspecified (0.0.0.0/::)"
    if parsed.is_private:
        return "private"
    if parsed.is_reserved or not parsed.is_global:
        return "reserved/non-global"
    return None


def validate_url(
    url: str,
    *,
    allow_local: bool = False,
    ports: tuple[int, ...] = DEFAULT_PORTS,
    resolve=None,
) -> Target:
    """Validate one URL for fetching; return the Target with its pinned IP."""
    split = urlsplit(url)
    scheme = (split.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise TeeError(
            "web_scheme_blocked",
            f"Scheme '{scheme or '(none)'}' is not fetchable.",
            fix="Only http:// and https:// URLs are.",
        )
    if "@" in split.netloc:
        raise TeeError(
            "web_userinfo_blocked",
            "URLs with embedded credentials (user@host) are refused.",
            fix="Drop the userinfo part; web_lookup never authenticates.",
        )
    host = split.hostname
    if not host:
        raise TeeError(
            "web_url_invalid", f"No host in '{url}'.", fix="Give a full http(s)://host/path URL."
        )
    try:
        port = split.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise TeeError(
            "web_url_invalid", f"Bad port in '{url}'.", fix="Use a numeric port or none."
        ) from exc
    if port not in ports:
        raise TeeError(
            "web_port_blocked",
            f"Port {port} is not allowed (default: 80/443).",
            fix=f"Add it via [web] ports = [80, 443, {port}] in .tee/config.toml if intended.",
        )

    try:  # an IP literal IS the address - no resolver, injected or real
        ips: list[str] = [str(ipaddress.ip_address(host))]
    except ValueError:
        ips = []
    resolver = resolve or _default_resolve
    try:
        if not ips:
            ips = resolver(host, port)
    except (socket.gaierror, OSError) as exc:
        raise TeeError(
            "web_dns_failed",
            f"'{host}' did not resolve ({exc.__class__.__name__}).",
            fix="Check the hostname; offline lookups only work for cached URLs.",
        ) from exc
    if not ips:
        raise TeeError(
            "web_dns_failed", f"'{host}' resolved to nothing.", fix="Check the hostname."
        )

    pinned: str | None = None
    for ip in ips:
        category = _address_category(ip)
        if category and not allow_local:
            raise TeeError(
                "web_private_blocked",
                f"'{host}' resolves to a {category} address ({ip}) - blocked.",
                fix=_ALLOW_LOCAL_FIX,
            )
        # Prefer an IPv4 pin when one exists (simplest connect path);
        # otherwise the first address wins.
        if pinned is None or ("." in ip and "." not in pinned):
            pinned = ip
    assert pinned is not None
    return Target(url=url, scheme=scheme, host=host, port=port, ip=pinned)
