"""web_search backend contracts (owner-directed A34 follow-on) - written
before the implementation. Three backends, one shape:

  searxng   - operator-run instance ([web] searxng_url; may be private -
              operator config is a trusted destination, unlike model input)
  brave     - keyed API (TEE_BRAVE_KEY env), fixed public host
  wikipedia - keyless, encyclopedic-only, the honest zero-config default

Selection: [web] search wins; else searxng when configured, else brave
when keyed, else wikipedia. Every response labels its backend; snippets
are untrusted web content (sanitized like extracts); result URLs face
the full SSRF guard only later, at tee_web_lookup time.
"""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest

from tee.kernel.errors import TeeError
from tee.web import search as web_search


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _urlopen_for(payloads: dict[str, Any], seen: list[str]):
    def fake_urlopen(request, timeout=0):
        url = request.full_url if hasattr(request, "full_url") else request
        seen.append(url)
        for marker, payload in payloads.items():
            if marker in url:
                return _Resp(json.dumps(payload).encode())
        raise urllib.error.URLError(f"no fixture for {url}")

    return fake_urlopen


SEARX_PAYLOAD = {
    "results": [
        {"title": "Block paving guide", "url": "https://ex.com/paving", "content": "Bedding sand 25-40 mm."},
        {"title": "Edge restraints", "url": "https://ex.com/edges", "content": "Install first."},
    ]
}  # fmt: skip

BRAVE_PAYLOAD = {
    "web": {
        "results": [
            {"title": "Paving spec", "url": "https://spec.example/p", "description": "Sand depth spec."},
        ]
    }
}  # fmt: skip

WIKI_PAYLOAD = [
    "block paving",
    ["Block paving", "Pavement (architecture)"],
    ["", ""],
    ["https://en.wikipedia.org/wiki/Block_paving", "https://en.wikipedia.org/wiki/Pavement_(architecture)"],
]  # fmt: skip


def test_searxng_backend_parses_and_labels(monkeypatch) -> None:
    seen: list[str] = []
    monkeypatch.setattr(
        web_search.urllib.request, "urlopen", _urlopen_for({"9888/search": SEARX_PAYLOAD}, seen)
    )
    out = web_search.run_search(
        "block paving sand", limit=5, config={"searxng_url": "http://127.0.0.1:9888"}
    )
    assert out["backend"] == "searxng"
    assert out["items"][0] == {
        "title": "Block paving guide",
        "url": "https://ex.com/paving",
        "snippet": "Bedding sand 25-40 mm.",
    }
    assert "format=json" in seen[0] and "q=block+paving+sand" in seen[0]


def test_brave_backend_sends_key_and_parses(monkeypatch) -> None:
    seen_headers: dict[str, str] = {}

    def fake_urlopen(request, timeout=0):
        seen_headers.update(request.headers)
        return _Resp(json.dumps(BRAVE_PAYLOAD).encode())

    monkeypatch.setattr(web_search.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("TEE_BRAVE_KEY", "k-123")
    out = web_search.run_search("paving spec", limit=3, config={"search": "brave"})
    assert out["backend"] == "brave"
    assert out["items"][0]["url"] == "https://spec.example/p"
    assert seen_headers.get("X-subscription-token") == "k-123"


def test_wikipedia_backend_is_the_zero_config_default(monkeypatch) -> None:
    seen: list[str] = []
    monkeypatch.delenv("TEE_BRAVE_KEY", raising=False)
    monkeypatch.setattr(
        web_search.urllib.request, "urlopen", _urlopen_for({"opensearch": WIKI_PAYLOAD}, seen)
    )
    out = web_search.run_search("block paving", limit=2, config={})
    assert out["backend"] == "wikipedia"
    assert out["items"][0]["url"].endswith("/Block_paving")
    assert "encyclopedic" in out["note"]


def test_selection_ladder_prefers_searxng_then_brave(monkeypatch) -> None:
    monkeypatch.setenv("TEE_BRAVE_KEY", "k")
    assert web_search.pick_backend({"searxng_url": "http://127.0.0.1:9888"}) == "searxng"
    assert web_search.pick_backend({}) == "brave"
    monkeypatch.delenv("TEE_BRAVE_KEY")
    assert web_search.pick_backend({}) == "wikipedia"
    assert web_search.pick_backend({"search": "wikipedia"}) == "wikipedia"


def test_explicit_backend_without_its_config_refuses_with_fix(monkeypatch) -> None:
    monkeypatch.delenv("TEE_BRAVE_KEY", raising=False)
    with pytest.raises(TeeError) as excinfo:
        web_search.run_search("q", limit=3, config={"search": "brave"})
    assert excinfo.value.code == "web_search_unconfigured"
    assert "TEE_BRAVE_KEY" in (excinfo.value.fix or "")
    with pytest.raises(TeeError) as excinfo:
        web_search.run_search("q", limit=3, config={"search": "searxng"})
    assert "searxng_url" in (excinfo.value.fix or "")


def test_snippets_are_sanitized_and_capped(monkeypatch) -> None:
    dirty = {
        "results": [{"title": "T​itle", "url": "https://ex.com/a", "content": "x" * 900 + "‮evil"}]
    }
    monkeypatch.setattr(web_search.urllib.request, "urlopen", _urlopen_for({"/search": dirty}, []))
    out = web_search.run_search("q", limit=1, config={"searxng_url": "http://127.0.0.1:9888"})
    row = out["items"][0]
    assert row["title"] == "Title"
    assert "‮" not in row["snippet"]
    assert len(row["snippet"]) <= 220


def test_empty_query_and_limit_clamp(monkeypatch) -> None:
    with pytest.raises(TeeError) as excinfo:
        web_search.run_search("  ", limit=5, config={})
    assert excinfo.value.code == "web_bad_arg"
    monkeypatch.setattr(
        web_search.urllib.request,
        "urlopen",
        _urlopen_for({"opensearch": WIKI_PAYLOAD}, []),
    )
    monkeypatch.delenv("TEE_BRAVE_KEY", raising=False)
    out = web_search.run_search("q", limit=99, config={})
    assert len(out["items"]) <= web_search.LIMIT_CAP


def test_unreachable_backend_is_one_cheap_error(monkeypatch) -> None:
    def fake_urlopen(request, timeout=0):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(web_search.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(TeeError) as excinfo:
        web_search.run_search("q", limit=3, config={"searxng_url": "http://127.0.0.1:9888"})
    assert excinfo.value.code == "web_search_failed"
    assert excinfo.value.fix


# --- the virtual tool -------------------------------------------------------


def test_web_search_virtual_tool_registered_and_untrusted_labeled(tmp_path, monkeypatch) -> None:
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.web.tools import register_web_tools

    monkeypatch.delenv("TEE_BRAVE_KEY", raising=False)
    monkeypatch.setattr(
        web_search.urllib.request, "urlopen", _urlopen_for({"opensearch": WIKI_PAYLOAD}, [])
    )
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        register_web_tools(app, tmp_path)
        described = app.registry.describe("web_search")
        assert "untrusted" in described["description"].lower()
        out = app.registry.call("web_search", {"query": "block paving", "limit": 2})
        assert out["backend"] == "wikipedia"
        assert out["items"]
    finally:
        app.shutdown()


@pytest.mark.network
@pytest.mark.timeout(120)
def test_live_wikipedia_search_feeds_lookup(tmp_path, network, monkeypatch) -> None:
    """The whole intended flow, live: find a URL, then read it guarded."""
    from tee.web.tools import WebLookupService

    monkeypatch.delenv("TEE_BRAVE_KEY", raising=False)
    found = web_search.run_search("block paving", limit=2, config={})
    assert found["backend"] == "wikipedia" and found["items"]
    answer = WebLookupService(tmp_path).lookup(
        found["items"][0]["url"], "how thick should the bedding sand be?"
    )
    assert answer["ok"] is True
    assert answer["source"]["url"].startswith("https://en.wikipedia.org/")
