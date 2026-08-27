"""Phase 8 (A12): tee_status recap - eviction-safe one-call resume - and
the caption-once media pass."""

from __future__ import annotations

import json
import time

import anyio
import pytest
from fixtures_extract import DJI_SRT, make_dxf, make_scene_frames, make_video
from mcp.client import Client
from mcp.types import TextContent

from tee.app import TeeApp
from tee.extract.tools import register_extract_tools
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.server import build_server


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    media = tmp_path_factory.mktemp("media")
    make_dxf(media / "plan.dxf")
    frames = make_scene_frames(tmp_path_factory.mktemp("frames"))
    make_video(media / "walkthrough.mp4", frames)
    (media / "flight.srt").write_text(DJI_SRT)

    project = tmp_path_factory.mktemp("project")
    application = TeeApp({"fake": FakeAdapter()}, project_root=project)
    application._store = register_extract_tools(application, project)[0]
    application.memory.remember("units", "meters")
    out = application.registry.call("ex_ingest", {"path": str(media)})
    deadline = time.time() + 300
    while time.time() < deadline:
        status = application.jobs.status(out["job"])
        if status["state"] in ("done", "error"):
            break
        time.sleep(0.2)
    assert status["state"] == "done", status
    application.run_batch(
        "fake",
        [{"op": "create", "kind": "cube", "name": f"W{i}"} for i in range(120)],
    )
    yield application
    application.shutdown()


# -- recap -------------------------------------------------------------------


def test_recap_is_compact_and_complete(app):
    recap = app.recap()
    assert recap["adapters"]["fake"]["entities"] == 120
    assert recap["adapters"]["fake"]["kinds"] == {"cube": 120}
    assert "revision" in recap["adapters"]["fake"]
    assert recap["checkpoints"]  # the batch auto-checkpoint shows up
    assert recap["memory"]["facts"]["units"] == "meters"
    assert recap["extract"]["sources"] == 3
    kinds = recap["extract"]["fact_kinds"]
    assert kinds.get("plan") == 1 and kinds.get("keyframe", 0) >= 1
    # the 8.3 budget: <= 500 estimated tokens on a full project
    assert estimate_tokens(recap) <= 500


def test_recap_over_mcp_surface(app):
    """A fresh client given ONLY tee_status(recap=true) can resume: it
    learns the scene stamp (for tee_diff), the store shape (for ex_facts),
    and memory - without re-listing the scene."""
    server = build_server(app)
    got = {}

    async def scenario():
        async with Client(server) as client:
            result = await client.call_tool("tee_status", {"recap": True})
            block = result.content[0]
            assert isinstance(block, TextContent)
            got.update(json.loads(block.text))

    anyio.run(scenario)
    recap = got["recap"]
    # the resume contract is the RESPONSE: the scene stamp arrives at top
    # level, and the recap block dedups against it instead of repeating it
    # (SI-1.2 - intra-response duplication was ~30% of the recap payload)
    stamp = got["adapters"]["fake"]["scene"]
    assert {"epoch", "revision"} <= set(stamp)
    assert recap["adapters"]["fake"] == {"kinds": {"cube": 120}}
    assert recap.get("checkpoints") != got.get("checkpoints")
    assert recap["extract"]["fact_kinds"]["plan"] == 1
    # plain status stays lean: no recap unless asked
    assert "recap" not in json.dumps(got["adapters"])


def test_status_without_recap_unchanged(app):
    assert "recap" not in app.status()


# -- caption-once ------------------------------------------------------------


def test_prepare_lists_uncaptioned_then_excludes_captioned(app):
    packet = app.registry.call("ex_prepare", {"source": "walkthrough.mp4"})
    assert packet["uncaptioned"], packet
    assert "caption" in packet["caption_guidance"]
    first = packet["uncaptioned"][0]
    assert any(first in p for p in packet["prepared_images"])

    stored = app.registry.call(
        "ex_store_facts",
        {
            "source": "walkthrough.mp4",
            "extractor": "vlm-video",
            "facts": [{"kind": "caption", "ref": first, "text": "empty hallway, grey walls"}],
            "merge": True,
        },
    )
    assert stored["stored"] == 1

    packet2 = app.registry.call("ex_prepare", {"source": "walkthrough.mp4"})
    assert first not in packet2.get("uncaptioned", [])
    assert not any(first in p for p in packet2.get("prepared_images", []))


def test_captions_are_searchable(app):
    hits = app.registry.call("ex_search", {"query": "grey hallway"})
    assert any(h["fact"].get("kind") == "caption" for h in hits["hits"])


def test_all_captioned_collapses_to_note(app):
    packet = app.registry.call("ex_prepare", {"source": "walkthrough.mp4"})
    for ref in packet.get("uncaptioned", []):
        app.registry.call(
            "ex_store_facts",
            {
                "source": "walkthrough.mp4",
                "extractor": "vlm-video",
                "facts": [{"kind": "caption", "ref": ref, "text": f"scene {ref}"}],
                "merge": True,
            },
        )
    final = app.registry.call("ex_prepare", {"source": "walkthrough.mp4"})
    assert "prepared_images" not in final
    assert "caption facts" in final["note"]
