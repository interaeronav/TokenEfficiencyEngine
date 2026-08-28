"""tee_web_lookup service + surface wiring (A34 W3).

The tool joins the always-loaded surface; a hostile page flows through the
whole service as inert quoted data and no server state changes - the
integration half of the W0 contract.
"""

from __future__ import annotations

from typing import Any

import pytest
from fixtures_web import HOSTILE_BODY, INJECTION

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.web.fetch import WebFetcher
from tee.web.tools import WEB_LOOKUP_DESCRIPTION, WebLookupService

URL = "http://site.example/paving"


def service(tmp_path, *, registry=None, routes: dict[str, Any] | None = None) -> WebLookupService:
    all_routes = {
        "http://site.example/robots.txt": (404, {}, b""),
        URL: (200, {}, HOSTILE_BODY.encode()),
    }
    all_routes.update(routes or {})

    def transport(target, headers, timeout):
        return all_routes[target.url]

    fetcher = WebFetcher(
        tmp_path,
        transport=transport,
        resolve=lambda host, port: ["93.184.216.34"],
        min_interval_s=0.0,
        sleep=lambda s: None,
    )
    return WebLookupService(tmp_path, fetcher=fetcher, registry=registry)


def test_lookup_answers_with_schema_and_cache_note(tmp_path) -> None:
    svc = service(tmp_path)
    first = svc.lookup(URL, "how thick is bedding sand?")
    assert first["ok"] is True
    assert "25 to 40 mm" in first["quote"]
    assert first["source"] == {"url": URL, "title": "Paving guide"}
    assert "cache" not in first  # a miss is the norm, not news
    second = svc.lookup(URL, "how thick is bedding sand?")
    assert second["cache"] == "fresh"


def test_hostile_page_is_inert_and_state_untouched(tmp_path) -> None:
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        state_before = (
            app.checkpoints.list(),
            app.caches["fake"].stamp(),
            app.memory.preamble(),
        )
        svc = service(tmp_path, registry=app.registry)
        answer = svc.lookup(URL, "how thick is bedding sand?")
        # the visible injection text arrives as quoted data...
        assert INJECTION in answer["quote"]
        # ...and nothing on the server moved because of it
        assert (
            app.checkpoints.list(),
            app.caches["fake"].stamp(),
            app.memory.preamble(),
        ) == state_before
    finally:
        app.shutdown()


def test_kb_hint_appears_when_kb_matches(tmp_path) -> None:
    class FakeRegistry:
        def call(self, name: str, args: dict) -> dict:
            assert name == "kb_search"
            return {"items": [{"id": "05-block-paving", "title": "Block paving"}]}

    answer = service(tmp_path, registry=FakeRegistry()).lookup(URL, "bedding sand?")
    assert "kb_read '05-block-paving'" in answer["kb_hint"]


def test_no_kb_no_hint(tmp_path) -> None:
    answer = service(tmp_path).lookup(URL, "bedding sand?")
    assert "kb_hint" not in answer


# -- the SI-B10 relevance floor (A37 P0-F) ----------------------------------
# kb_search always crowns SOME file; the hint must honor the search's own
# match-strength note. The three questions below are the recorded 2026-08-28
# misfires (research 54): each got a correct extract plus an off-topic hint.

MISFIRES = [
    ("how do I merge selected vertices by distance in edit mode", "industry.case_studies"),
    ("what is XPlaneConnect and what can it do", "industry.sa_contractors"),
    ("what does the Ames Stereo Pipeline produce", "gxgd.game_disciplines"),
]


WEAK_NOTE = "weak match - only 'system' hits a title/id/tag"


class NotedRegistry:
    """Echoes kb_search responses the real corpus produced for the misfires."""

    def __init__(self, top_id: str, note: str | None):
        self.top_id, self.note = top_id, note

    def call(self, name: str, args: dict) -> dict:
        assert name == "kb_search"
        out: dict[str, Any] = {"items": [{"id": self.top_id, "title": self.top_id}]}
        if self.note:
            out["note"] = self.note
        return out


def test_kb_hint_suppressed_on_recorded_misfires(tmp_path) -> None:
    from tee.kb.search import NOTE_NO_STRONG

    for question, wrong_top in MISFIRES:
        registry = NotedRegistry(wrong_top, NOTE_NO_STRONG)
        answer = service(tmp_path, registry=registry).lookup(URL, question)
        assert "kb_hint" not in answer, question


def test_kb_hint_borderline_vetoed_by_rerank(tmp_path, monkeypatch) -> None:
    from tee.llm import chores

    seen: dict[str, Any] = {}

    def fake_rerank(query, candidates, **kwargs):
        seen["ids"] = [c["id"] for c in candidates]
        return {"order": ["none-of-these", "joinery.cabinetmaking"], "model": "m14"}

    monkeypatch.setattr(chores, "rerank", fake_rerank)
    registry = NotedRegistry("joinery.cabinetmaking", WEAK_NOTE)
    answer = service(tmp_path, registry=registry).lookup(URL, "32 mm system hole spacing")
    assert "kb_hint" not in answer
    assert seen["ids"] == ["joinery.cabinetmaking", "none-of-these"]


def test_kb_hint_borderline_kept_without_endpoint(tmp_path, monkeypatch) -> None:
    from tee.llm import chores

    monkeypatch.setattr(chores, "rerank", lambda *a, **k: None)  # absent endpoint
    registry = NotedRegistry("joinery.cabinetmaking", WEAK_NOTE)
    answer = service(tmp_path, registry=registry).lookup(URL, "32 mm system hole spacing")
    assert "kb_read 'joinery.cabinetmaking'" in answer["kb_hint"]
    assert "kb-rerank" not in answer["kb_hint"]  # floor only: no model label


def test_kb_hint_borderline_kept_by_rerank_is_labelled(tmp_path, monkeypatch) -> None:
    from tee.llm import chores

    monkeypatch.setattr(
        chores,
        "rerank",
        lambda *a, **k: {"order": ["joinery.cabinetmaking", "none-of-these"], "model": "m14"},
    )
    registry = NotedRegistry("joinery.cabinetmaking", WEAK_NOTE)
    answer = service(tmp_path, registry=registry).lookup(URL, "32 mm system hole spacing")
    assert "kb_read 'joinery.cabinetmaking'" in answer["kb_hint"]
    assert "[kb-rerank: m14]" in answer["kb_hint"]


def test_bad_media_and_empty_question_refused(tmp_path) -> None:
    svc = service(tmp_path)
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(URL, "q", media="pixels")
    assert excinfo.value.code == "web_bad_arg"
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(URL, "   ")
    assert excinfo.value.code == "web_bad_arg"


def test_max_tokens_clamped(tmp_path) -> None:
    svc = service(tmp_path)
    assert svc.lookup(URL, "bedding sand", max_tokens=999_999)["ok"] is True
    assert svc.lookup(URL, "bedding sand", max_tokens=1)["ok"] is True


def test_tool_joins_the_surface(tmp_path) -> None:
    import anyio
    from mcp.client import Client

    from tee.server import build_server

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        server = build_server(app)

        async def fetch():
            async with Client(server) as client:
                return (await client.list_tools()).tools

        tools = {t.name: t for t in anyio.run(fetch)}
        assert "tee_web_lookup" in tools
        assert tools["tee_web_lookup"].description == WEB_LOOKUP_DESCRIPTION
        props = tools["tee_web_lookup"].input_schema["properties"]
        assert set(props) == {"url", "question", "max_tokens", "media"}
    finally:
        app.shutdown()
