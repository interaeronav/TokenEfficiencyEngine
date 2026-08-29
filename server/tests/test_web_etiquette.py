"""Fetcher etiquette + SSRF-in-motion spec for the web lane (A34 W0).

Research 49, mitigations 2 and 4: pinned connections, per-hop redirect
revalidation, robots.txt + Crawl-delay, per-host rate limiting, honest UA,
TTL'd ETag cache, size caps, 429 backoff. Everything here runs against an
injected transport/clock (no sockets) except the final class, which runs a
real http.server on loopback through the [web] allow_local opt-in - the
documented operator escape hatch, dogfooded.
"""

from __future__ import annotations

import http.server
import threading
from typing import Any

import pytest
from fixtures_web import TINY_PAGE, robots_txt

from tee.kernel.errors import TeeError
from tee.web.fetch import WebFetcher

# Real public addresses on purpose: documentation/TEST-NET ranges are
# correctly non-global to the guard, so they cannot play "public" here.
HOSTS = {"site.example": ["93.184.216.34"], "other.example": ["151.101.1.140"]}


def resolve(host: str, port: int) -> list[str]:
    if host in HOSTS:
        return HOSTS[host]
    raise OSError(f"unknown test host {host}")


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeTransport:
    """Routes url -> (status, headers, body) or a list of those (sequenced)."""

    def __init__(self, routes: dict[str, Any]):
        self.routes = dict(routes)
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def __call__(self, target: Any, headers: dict[str, str], timeout: float):
        self.calls.append((target.url, dict(headers), timeout))
        entry = self.routes[target.url]
        if isinstance(entry, list):
            response = entry.pop(0) if len(entry) > 1 else entry[0]
        else:
            response = entry
        if isinstance(response, Exception):
            raise response
        return response

    def urls(self) -> list[str]:
        return [url for url, _, _ in self.calls]


OK_ROBOTS = (200, {}, robots_txt().encode())
NO_ROBOTS = (404, {}, b"")
PAGE = (200, {"ETag": '"v1"'}, TINY_PAGE.encode())


def make_fetcher(tmp_path, routes, **kwargs):
    transport = FakeTransport(routes)
    clock = FakeClock()
    defaults = dict(
        transport=transport,
        resolve=resolve,
        clock=clock.clock,
        sleep=clock.sleep,
        min_interval_s=2.0,
        ttl_s=3600,
    )
    defaults.update(kwargs)
    return WebFetcher(tmp_path, **defaults), transport, clock


# --- basic fetch, UA, robots ------------------------------------------------


def test_fetch_serves_page_with_honest_ua(tmp_path) -> None:
    fetcher, transport, _ = make_fetcher(
        tmp_path,
        {"http://site.example/robots.txt": NO_ROBOTS, "http://site.example/page": PAGE},
    )
    result = fetcher.fetch("http://site.example/page")
    assert result.status == 200
    assert b"One short paragraph" in result.body
    assert result.cache == "miss"
    assert result.retrieved_at.endswith("Z")
    for _, headers, timeout in transport.calls:
        assert headers["User-Agent"].startswith("TEE-web/")
        assert "+http" in headers["User-Agent"]
        assert timeout > 0


def test_robots_disallow_refused_with_fix(tmp_path) -> None:
    fetcher, transport, _ = make_fetcher(
        tmp_path,
        {"http://site.example/robots.txt": OK_ROBOTS, "http://site.example/secret": PAGE},
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/secret")
    assert excinfo.value.code == "web_robots_blocked"
    assert "robots.txt" in excinfo.value.message + (excinfo.value.fix or "")
    assert transport.urls() == ["http://site.example/robots.txt"]


def test_robots_fetched_once_per_host(tmp_path) -> None:
    fetcher, transport, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/a": PAGE,
            "http://site.example/b": PAGE,
        },
    )
    fetcher.fetch("http://site.example/a")
    fetcher.fetch("http://site.example/b")
    assert transport.urls().count("http://site.example/robots.txt") == 1


def test_crawl_delay_honored(tmp_path) -> None:
    robots = (200, {}, robots_txt(crawl_delay=5).encode())
    fetcher, _, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": robots,
            "http://site.example/a": PAGE,
            "http://site.example/b": PAGE,
        },
    )
    fetcher.fetch("http://site.example/a")
    fetcher.fetch("http://site.example/b")
    assert sum(clock.sleeps) >= 5.0


# --- rate limit + backoff ---------------------------------------------------


def test_per_host_rate_limit_spaces_requests(tmp_path) -> None:
    fetcher, _, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/a": (200, {}, b"a"),
            "http://site.example/b": (200, {}, b"b"),
        },
    )
    fetcher.fetch("http://site.example/a")
    fetcher.fetch("http://site.example/b")
    assert sum(clock.sleeps) >= 2.0


def test_first_lookup_of_a_host_pays_no_interval_sleep(tmp_path) -> None:
    """robots.txt obeys the per-host interval but does not arm it: the first
    content fetch of a fresh host must not sleep (A35 P0 measured every
    first lookup paying ~min_interval_s between robots and the page)."""
    fetcher, _, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": OK_ROBOTS,
            "http://site.example/a": PAGE,
        },
    )
    fetcher.fetch("http://site.example/a")
    assert sum(clock.sleeps) == 0.0


def test_429_backoff_honors_retry_after_once(tmp_path) -> None:
    fetcher, _, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/busy": [(429, {"Retry-After": "3"}, b""), (200, {}, b"ok")],
        },
    )
    result = fetcher.fetch("http://site.example/busy")
    assert result.body == b"ok"
    assert any(s >= 3.0 for s in clock.sleeps)


def test_429_twice_gives_up_loud(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/busy": (429, {"Retry-After": "1"}, b""),
        },
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/busy")
    assert excinfo.value.code == "web_rate_limited"
    assert excinfo.value.fix


# --- redirects: every hop revalidated ---------------------------------------


def test_redirect_followed_with_revalidation(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://other.example/robots.txt": NO_ROBOTS,
            "http://site.example/moved": (301, {"Location": "http://other.example/new"}, b""),
            "http://other.example/new": PAGE,
        },
    )
    result = fetcher.fetch("http://site.example/moved")
    assert result.url == "http://other.example/new"
    assert result.status == 200


def test_relative_redirect_resolved(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/moved": (302, {"Location": "/new"}, b""),
            "http://site.example/new": PAGE,
        },
    )
    assert fetcher.fetch("http://site.example/moved").url == "http://site.example/new"


def test_redirect_to_loopback_refused(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/evil": (302, {"Location": "http://127.0.0.1/admin"}, b""),
        },
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/evil")
    assert excinfo.value.code == "web_private_blocked"


def test_redirect_to_bad_scheme_refused(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/evil": (302, {"Location": "ftp://site.example/f"}, b""),
        },
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/evil")
    assert excinfo.value.code == "web_scheme_blocked"


def test_redirect_chain_capped(tmp_path) -> None:
    routes = {"http://site.example/robots.txt": NO_ROBOTS}
    for i in range(5):
        routes[f"http://site.example/r{i}"] = (
            301,
            {"Location": f"http://site.example/r{i + 1}"},
            b"",
        )
    fetcher, _, _ = make_fetcher(tmp_path, routes)
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/r0")
    assert excinfo.value.code == "web_redirect_loop"


# --- size caps --------------------------------------------------------------


def test_content_length_over_cap_refused(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/big": (200, {"Content-Length": "99999999"}, b""),
        },
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/big")
    assert excinfo.value.code == "web_too_large"


def test_oversize_body_refused(tmp_path) -> None:
    fetcher, _, _ = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/big": (200, {}, b"x" * 2048),
        },
        max_bytes=1024,
    )
    with pytest.raises(TeeError) as excinfo:
        fetcher.fetch("http://site.example/big")
    assert excinfo.value.code == "web_too_large"


# --- cache: fresh, revalidated, stale-offline -------------------------------


def test_repeat_fetch_within_ttl_costs_no_request(tmp_path) -> None:
    fetcher, transport, _ = make_fetcher(
        tmp_path,
        {"http://site.example/robots.txt": NO_ROBOTS, "http://site.example/page": PAGE},
    )
    first = fetcher.fetch("http://site.example/page")
    calls = len(transport.calls)
    second = fetcher.fetch("http://site.example/page")
    assert len(transport.calls) == calls
    assert second.cache == "fresh"
    assert second.body == first.body
    assert second.retrieved_at == first.retrieved_at


def test_expired_cache_revalidates_with_etag(tmp_path) -> None:
    fetcher, transport, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/page": [PAGE, (304, {}, b"")],
        },
        ttl_s=100,
    )
    fetcher.fetch("http://site.example/page")
    clock.now += 200
    result = fetcher.fetch("http://site.example/page")
    assert result.cache == "revalidated"
    assert b"One short paragraph" in result.body
    conditional = [h for url, h, _ in transport.calls if url.endswith("/page")][-1]
    assert conditional.get("If-None-Match") == '"v1"'


def test_offline_with_cache_degrades_to_stale(tmp_path) -> None:
    fetcher, _, clock = make_fetcher(
        tmp_path,
        {
            "http://site.example/robots.txt": NO_ROBOTS,
            "http://site.example/page": [PAGE, OSError("network down")],
        },
        ttl_s=100,
    )
    fetcher.fetch("http://site.example/page")
    clock.now += 200
    result = fetcher.fetch("http://site.example/page")
    assert result.cache == "stale-offline"
    assert b"One short paragraph" in result.body


# --- the real thing on loopback (allow_local opt-in, no outbound) -----------


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body, status = b"", 200
        if self.path == "/robots.txt":
            body = robots_txt().encode()
        elif self.path == "/page.html":
            body = TINY_PAGE.encode()
        elif self.path == "/secret":
            body = b"nope"
        else:
            status = 404
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:  # quiet
        return


def test_live_loopback_fetch_through_allow_local(tmp_path) -> None:
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        fetcher = WebFetcher(tmp_path, allow_local=True, ports=(80, 443, port), min_interval_s=0.0)
        result = fetcher.fetch(f"http://127.0.0.1:{port}/page.html")
        assert result.status == 200
        assert b"One short paragraph" in result.body
        with pytest.raises(TeeError) as excinfo:
            fetcher.fetch(f"http://127.0.0.1:{port}/secret")
        assert excinfo.value.code == "web_robots_blocked"
        with pytest.raises(TeeError) as blocked:
            WebFetcher(tmp_path, ports=(80, 443, port)).fetch(f"http://127.0.0.1:{port}/page.html")
        assert blocked.value.code == "web_private_blocked"
    finally:
        server.shutdown()
        thread.join(timeout=5)


# --- cache sweep (A38 S3.2: the on-disk cache is bounded) --------------------


def _seed_cache_entry(tmp_path, name: str, *, age_s: float, size: int) -> None:
    import json as _json
    import time as _time

    cache = tmp_path / ".tee" / "web" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    (cache / f"{name}.body").write_bytes(b"x" * size)
    (cache / f"{name}.meta.json").write_text(
        _json.dumps({"url": f"https://example.com/{name}", "fetched_at": _time.time() - age_s})
    )


def test_sweep_evicts_by_age_and_keeps_fresh(tmp_path) -> None:
    _seed_cache_entry(tmp_path, "ancient", age_s=20 * 86400, size=10)
    _seed_cache_entry(tmp_path, "fresh", age_s=60, size=10)
    WebFetcher(tmp_path, transport=FakeTransport({}), resolve=resolve)
    cache = tmp_path / ".tee" / "web" / "cache"
    assert not (cache / "ancient.body").exists()
    assert not (cache / "ancient.meta.json").exists()
    assert (cache / "fresh.body").exists()


def test_sweep_evicts_oldest_first_down_to_the_size_cap(tmp_path) -> None:
    _seed_cache_entry(tmp_path, "older", age_s=3600, size=700_000)
    _seed_cache_entry(tmp_path, "newer", age_s=60, size=700_000)
    WebFetcher(tmp_path, transport=FakeTransport({}), resolve=resolve, cache_max_mb=1.0)
    cache = tmp_path / ".tee" / "web" / "cache"
    assert not (cache / "older.body").exists()
    assert (cache / "newer.body").exists()


def test_sweep_treats_corrupt_meta_as_oldest(tmp_path) -> None:
    cache = tmp_path / ".tee" / "web" / "cache"
    cache.mkdir(parents=True)
    (cache / "broken.meta.json").write_text("{not json")
    (cache / "broken.body").write_bytes(b"x")
    _seed_cache_entry(tmp_path, "fine", age_s=60, size=10)
    WebFetcher(tmp_path, transport=FakeTransport({}), resolve=resolve)
    assert not (cache / "broken.body").exists()
    assert (cache / "fine.body").exists()
