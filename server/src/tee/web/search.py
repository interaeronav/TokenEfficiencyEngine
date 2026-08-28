"""Finding URLs - the research-49 named gap, built on owner direction.

Three backends behind one row shape ({title, url, snippet}); the
response always names its backend. Backend base URLs are OPERATOR
configuration (a trusted destination - a local SearXNG is the point),
unlike model-supplied URLs; every result URL faces the full SSRF guard
later, when tee_web_lookup fetches it. Titles and snippets are
untrusted web content: sanitized (zero-width/bidi stripped), capped,
data - never instructions.

Backends, evaluated 2026-08-28:
- searxng: self-hosted metasearch, no key, broadest results. Needs a
  running instance ([web] searxng_url).
- brave: keyed API (TEE_BRAVE_KEY), fixed public host, metered
  free tier - the keyed-backend slot (the Tripo/Meshy env pattern).
- wikipedia: keyless opensearch, encyclopedic only - the honest
  zero-config default, labeled as such in every response.
- Rejected: engine-page scraping (DuckDuckGo/Google HTML) - ToS-hostile
  and selector-fragile, the exact anti-goal class the web lane refuses.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from tee.kernel.errors import TeeError
from tee.web.extract import _DROP_CHARS
from tee.web.fetch import USER_AGENT

DEFAULT_LIMIT = 5
LIMIT_CAP = 10
_TITLE_CHARS = 80
_SNIPPET_CHARS = 220


def _clean(text: object, cap: int) -> str:
    return " ".join(str(text or "").translate(_DROP_CHARS).split())[:cap]


def pick_backend(config: dict) -> str:
    """Explicit [web] search wins; else the ladder: a configured SearXNG,
    then a keyed Brave, then keyless Wikipedia."""
    explicit = str(config.get("search") or "").strip().lower()
    if explicit:
        return explicit
    if config.get("searxng_url"):
        return "searxng"
    if os.environ.get("TEE_BRAVE_KEY"):
        return "brave"
    return "wikipedia"


def _get_json(url: str, *, headers: dict | None = None, timeout: float = 15.0):
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise TeeError(
            "web_search_failed",
            f"The search backend did not answer ({exc.__class__.__name__}).",
            fix="Check the backend (instance up? key valid? network?); "
            "tee_web_lookup of a known URL works without any search backend.",
        ) from exc


def _rows(entries, title_key: str, snippet_key: str, limit: int) -> list[dict]:
    rows = []
    for entry in entries[:limit]:
        url = str(entry.get("url") or "")
        if not url.startswith(("http://", "https://")):
            continue
        rows.append(
            {
                "title": _clean(entry.get(title_key), _TITLE_CHARS),
                "url": url,
                "snippet": _clean(entry.get(snippet_key), _SNIPPET_CHARS),
            }
        )
    return rows


def run_search(query: str, *, limit: int = DEFAULT_LIMIT, config: dict | None = None) -> dict:
    config = dict(config or {})
    query = " ".join(str(query or "").split())
    if not query:
        raise TeeError("web_bad_arg", "query is required.", fix="Give a few search words.")
    limit = max(1, min(int(limit or DEFAULT_LIMIT), LIMIT_CAP))
    backend = pick_backend(config)

    if backend == "searxng":
        base = str(config.get("searxng_url") or "").rstrip("/")
        if not base:
            raise TeeError(
                "web_search_unconfigured",
                "searxng selected but no instance configured.",
                fix='Set [web] searxng_url = "http://127.0.0.1:8888" (your instance).',
            )
        data = _get_json(f"{base}/search?" + urllib.parse.urlencode({"q": query, "format": "json"}))
        return {
            "ok": True,
            "backend": "searxng",
            "items": _rows(data.get("results") or [], "title", "content", limit),
        }

    if backend == "brave":
        key = os.environ.get("TEE_BRAVE_KEY", "")
        if not key:
            raise TeeError(
                "web_search_unconfigured",
                "brave selected but no key present.",
                fix="Set TEE_BRAVE_KEY (an api.search.brave.com subscription token).",
            )
        data = _get_json(
            "https://api.search.brave.com/res/v1/web/search?"
            + urllib.parse.urlencode({"q": query, "count": limit}),
            headers={"X-Subscription-Token": key},
        )
        entries = (data.get("web") or {}).get("results") or []
        return {
            "ok": True,
            "backend": "brave",
            "items": _rows(entries, "title", "description", limit),
        }

    if backend == "wikipedia":
        data = _get_json(
            "https://en.wikipedia.org/w/api.php?"
            + urllib.parse.urlencode(
                {"action": "opensearch", "search": query, "limit": limit, "format": "json"}
            )
        )
        titles = data[1] if isinstance(data, list) and len(data) > 3 else []
        urls = data[3] if isinstance(data, list) and len(data) > 3 else []
        items = [
            {"title": _clean(t, _TITLE_CHARS), "url": str(u), "snippet": ""}
            for t, u in zip(titles, urls, strict=False)
            if str(u).startswith("http")
        ]
        return {
            "ok": True,
            "backend": "wikipedia",
            "items": items[:limit],
            "note": "encyclopedic only (keyless default) - set [web] searxng_url "
            "or TEE_BRAVE_KEY for full-web search",
        }

    raise TeeError(
        "web_bad_arg",
        f"search backend '{backend}' is unknown.",
        fix="Use searxng, brave, or wikipedia in [web] search.",
    )
