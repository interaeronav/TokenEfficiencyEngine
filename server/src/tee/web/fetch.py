"""The polite guarded fetcher (research 49, mitigations 2 and 4).

Cache-first (URL-hash + ETag revalidation, TTL'd, private under
`.tee/web/`), robots.txt + Crawl-delay honored per host, per-host rate
limit, honest versioned UA, 429/503 backoff with Retry-After, size caps,
redirects never auto-followed - each hop re-validated through the guard
against its own freshly pinned IP, max 3. stdlib only.

Injectable seams (transport / resolve / clock / sleep) exist so every
behavior above is testable without a socket; the default transport
connects to the pinned IP with the Host header and SNI set to the
validated hostname, so the address that was checked is the address dialed.
"""

from __future__ import annotations

import http.client
import json
import socket
import ssl
import time
import urllib.robotparser
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

from tee.kernel.errors import TeeError
from tee.web.guard import DEFAULT_PORTS, Target, validate_url

try:  # single source for the UA version
    from importlib.metadata import version as _dist_version

    _VERSION = _dist_version("tee-engine")
except Exception:  # pragma: no cover - source checkouts without dist metadata
    _VERSION = "0.2"

USER_AGENT = f"TEE-web/{_VERSION} (+https://github.com/interaeronav/TokenEfficiencyEngine)"
UA_TOKEN = "TEE-web"
MAX_BYTES = 5_000_000
MAX_REDIRECTS = 3
_REDIRECTS = (301, 302, 303, 307, 308)
_RETRY_AFTER_CAP_S = 30.0

Transport = Callable[[Target, dict[str, str], float], tuple[int, dict[str, str], bytes]]


@dataclass
class FetchResult:
    url: str  # final URL after any redirects
    status: int
    headers: dict[str, str]
    body: bytes
    cache: str  # miss | fresh | revalidated | stale-offline
    retrieved_at: str  # ISO-8601 UTC


def _iso_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class WebFetcher:
    def __init__(
        self,
        project_root: Path | str,
        *,
        allow_local: bool = False,
        ports: tuple[int, ...] = DEFAULT_PORTS,
        min_interval_s: float = 2.0,
        ttl_s: float = 3600.0,
        max_bytes: int = MAX_BYTES,
        timeout_s: float = 20.0,
        transport: Transport | None = None,
        resolve=None,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cache_dir = Path(project_root) / ".tee" / "web" / "cache"
        self.allow_local = allow_local
        self.ports = tuple(ports)
        self.min_interval_s = min_interval_s
        self.ttl_s = ttl_s
        self.max_bytes = max_bytes
        self.timeout_s = timeout_s
        self._transport = transport or self._default_transport
        self._resolve = resolve
        self._clock = clock
        self._sleep = sleep
        self._robots: dict[str, tuple[urllib.robotparser.RobotFileParser | None, float]] = {}
        self._interval: dict[str, float] = {}  # per-host, crawl-delay aware
        self._last_request: dict[str, float] = {}

    # -- public ---------------------------------------------------------------

    def fetch(self, url: str, *, max_bytes: int | None = None) -> FetchResult:
        cap = max_bytes or self.max_bytes
        target = self._validate(url)
        cached = self._cache_load(url)
        if cached is not None and self._age(cached) < self.ttl_s:
            return self._from_cache(url, cached, "fresh")

        self._robots_check(target)
        headers = self._headers()
        if cached is not None and cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]

        try:
            status, resp_headers, body = self._request(target, headers, cap)
            hops = 0
            current = target
            while status in _REDIRECTS and resp_headers.get("Location"):
                hops += 1
                if hops > MAX_REDIRECTS:
                    raise TeeError(
                        "web_redirect_loop",
                        f"More than {MAX_REDIRECTS} redirects from {url}.",
                        fix="Fetch the final URL directly.",
                    )
                next_url = urljoin(current.url, resp_headers["Location"])
                current = self._validate(next_url)
                self._robots_check(current)
                status, resp_headers, body = self._request(current, self._headers(), cap)
        except TeeError:
            raise
        except (OSError, http.client.HTTPException) as exc:
            if cached is not None:
                return self._from_cache(url, cached, "stale-offline")
            raise TeeError(
                "web_fetch_failed",
                f"Could not fetch {url.split('?')[0]} ({exc.__class__.__name__}).",
                fix="Check the URL and connectivity; cached URLs keep answering offline.",
            ) from exc

        if status == 304 and cached is not None:
            cached["fetched_at"] = self._clock()
            self._cache_store_meta(url, cached)
            return self._from_cache(url, cached, "revalidated")
        if status >= 400:
            raise TeeError(
                "web_http_error",
                f"HTTP {status} from {current.url.split('?')[0]}.",
                fix="Check the URL; paywalled or private pages are not fetchable.",
            )
        self._check_size(len(body), cap, current.url)
        retrieved_at = _iso_now()
        self._cache_store(
            url,
            body,
            {
                "url": current.url,
                "etag": resp_headers.get("ETag"),
                "retrieved_at": retrieved_at,
                "fetched_at": self._clock(),
            },
        )
        return FetchResult(
            url=current.url,
            status=status,
            headers=resp_headers,
            body=body,
            cache="miss",
            retrieved_at=retrieved_at,
        )

    # -- validation / robots / throttle ---------------------------------------

    def _validate(self, url: str) -> Target:
        return validate_url(
            url, allow_local=self.allow_local, ports=self.ports, resolve=self._resolve
        )

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": USER_AGENT, "Accept": "text/html, text/*;q=0.8, */*;q=0.1"}

    def _host_key(self, target: Target) -> str:
        return f"{target.host}:{target.port}"

    def _robots_check(self, target: Target) -> None:
        path = urlsplit(target.url).path or "/"
        if path == "/robots.txt":
            return
        key = self._host_key(target)
        entry = self._robots.get(key)
        if entry is None or (self._clock() - entry[1]) >= self.ttl_s:
            parser = self._robots_fetch(target)
            self._robots[key] = (parser, self._clock())
            if parser is not None:
                delay = parser.crawl_delay(UA_TOKEN)
                if delay is not None:
                    self._interval[key] = max(self.min_interval_s, float(delay))
        parser = self._robots[key][0]
        if parser is not None and not parser.can_fetch(UA_TOKEN, target.url):
            raise TeeError(
                "web_robots_blocked",
                f"robots.txt of {target.host} disallows this path for crawlers.",
                fix="Read the page in a browser instead; TEE honors robots.txt.",
            )

    def _robots_fetch(self, target: Target) -> urllib.robotparser.RobotFileParser | None:
        default_port = 443 if target.scheme == "https" else 80
        netloc = target.host if target.port == default_port else f"{target.host}:{target.port}"
        robots_url = f"{target.scheme}://{netloc}/robots.txt"
        try:
            robots_target = self._validate(robots_url)
            status, _headers, body = self._request(robots_target, self._headers(), 512 * 1024)
        except (TeeError, OSError, http.client.HTTPException):
            return None  # unreachable robots -> no rules known; the page fetch decides
        if status >= 400:
            return None  # no robots.txt -> everything allowed (the standard reading)
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(body.decode("utf-8", errors="replace").splitlines())
        return parser

    def _throttle(self, target: Target) -> None:
        key = self._host_key(target)
        interval = self._interval.get(key, self.min_interval_s)
        last = self._last_request.get(key)
        if last is not None:
            wait = interval - (self._clock() - last)
            if wait > 0:
                self._sleep(wait)
        self._last_request[key] = self._clock()

    def _request(
        self, target: Target, headers: dict[str, str], cap: int
    ) -> tuple[int, dict[str, str], bytes]:
        """One throttled request with a single 429/503 Retry-After backoff."""
        for attempt in (1, 2):
            self._throttle(target)
            status, resp_headers, body = self._transport(target, headers, self.timeout_s)
            if status in (429, 503):
                if attempt == 2:
                    raise TeeError(
                        "web_rate_limited",
                        f"{target.host} keeps answering HTTP {status}.",
                        fix="The host is throttling us; retry later - cached URLs "
                        "keep answering meanwhile.",
                    )
                retry_after = min(
                    _RETRY_AFTER_CAP_S,
                    float(resp_headers.get("Retry-After") or self.min_interval_s or 1.0),
                )
                self._sleep(retry_after)
                continue
            length = resp_headers.get("Content-Length")
            if length and length.isdigit():
                self._check_size(int(length), cap, target.url)
            self._check_size(len(body), cap, target.url)
            return status, resp_headers, body
        raise AssertionError("unreachable")

    def _check_size(self, size: int, cap: int, url: str) -> None:
        if size > cap:
            raise TeeError(
                "web_too_large",
                f"{url.split('?')[0]} is {size} bytes (cap {cap}).",
                fix="Fetch a more specific page; media files go through the "
                "size-gated media lane, not the text path.",
            )

    # -- cache ----------------------------------------------------------------

    def _cache_paths(self, url: str) -> tuple[Path, Path]:
        digest = sha256(url.encode()).hexdigest()[:32]
        return self.cache_dir / f"{digest}.body", self.cache_dir / f"{digest}.meta.json"

    def _cache_load(self, url: str) -> dict[str, Any] | None:
        body_path, meta_path = self._cache_paths(url)
        if not (body_path.exists() and meta_path.exists()):
            return None
        try:
            meta = json.loads(meta_path.read_text())
            meta["_body"] = body_path.read_bytes()
        except (OSError, json.JSONDecodeError):
            return None
        return meta

    def _age(self, meta: dict[str, Any]) -> float:
        return self._clock() - float(meta.get("fetched_at", 0))

    def _from_cache(self, url: str, meta: dict[str, Any], kind: str) -> FetchResult:
        return FetchResult(
            url=str(meta.get("url", url)),
            status=200,
            headers={},
            body=meta["_body"],
            cache=kind,
            retrieved_at=str(meta.get("retrieved_at", "")),
        )

    def _cache_store(self, url: str, body: bytes, meta: dict[str, Any]) -> None:
        body_path, _ = self._cache_paths(url)
        body_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = body_path.with_suffix(".tmp")
        tmp.write_bytes(body)
        tmp.replace(body_path)
        self._cache_store_meta(url, meta)

    def _cache_store_meta(self, url: str, meta: dict[str, Any]) -> None:
        _, meta_path = self._cache_paths(url)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {k: v for k, v in meta.items() if not k.startswith("_")}
        tmp = meta_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload))
        tmp.replace(meta_path)

    # -- the real transport: connect to the PINNED ip -------------------------

    def _default_transport(
        self, target: Target, headers: dict[str, str], timeout: float
    ) -> tuple[int, dict[str, str], bytes]:
        split = urlsplit(target.url)
        path = split.path or "/"
        if split.query:
            path += f"?{split.query}"
        default_port = 443 if target.scheme == "https" else 80
        host_header = target.host if target.port == default_port else f"{target.host}:{target.port}"
        conn: http.client.HTTPConnection
        if target.scheme == "https":
            conn = _PinnedHTTPSConnection(
                target.ip, target.port, server_hostname=target.host, timeout=timeout
            )
        else:
            conn = http.client.HTTPConnection(target.ip, target.port, timeout=timeout)
        try:
            conn.putrequest("GET", path, skip_host=True, skip_accept_encoding=True)
            conn.putheader("Host", host_header)
            for name, value in headers.items():
                conn.putheader(name, value)
            conn.endheaders()
            response = conn.getresponse()
            body = response.read(self.max_bytes + 1)
            resp_headers = {k: v for k, v in response.getheaders()}
            return response.status, resp_headers, body
        finally:
            conn.close()


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """TLS to the pinned IP while SNI + certificate checks use the hostname."""

    def __init__(self, ip: str, port: int, *, server_hostname: str, timeout: float):
        context = ssl.create_default_context()
        super().__init__(ip, port, timeout=timeout, context=context)
        self._tee_context = context
        self._tee_server_hostname = server_hostname

    def connect(self) -> None:  # pragma: no cover - needs real TLS; network tests hit it
        sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock = self._tee_context.wrap_socket(sock, server_hostname=self._tee_server_hostname)
