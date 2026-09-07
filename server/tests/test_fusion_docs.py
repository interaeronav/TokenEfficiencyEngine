"""A71: the three tools ported from the A68 Fusion lane the owner's machine
carried - a design-wide health read and a live, version-matched API index.

The owner chose PR #1's richer lane and asked for these three to come across
rather than be lost with the branch that held them. They rest on doc 71's
existing rows (4, 14-16, 21, 53) plus Python's own `inspect`, which the API
table does not govern; the live half is `tests/test_fusion_live.py`.
"""

from __future__ import annotations

import json

import pytest
from fixtures_fusion import FakeFusionWire

from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.docs import FusionDocs
from tee.adapters.fusion.tools import register_fusion_tools
from tee.app import TeeApp
from tee.kernel import lanes, trust
from tee.kernel.errors import TeeError

PLATE = [
    {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 120, 80]]}},
    {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 10}},
]
OVERLAPPING = [
    {"op": "create", "kind": "sketch", "props": {"rects": [[10, 10, 60, 50]]}},
    {
        "op": "create",
        "kind": "extrude",
        "props": {"sketch": "sk2", "distance": 20, "operation": "new_body"},
    },
]


@pytest.fixture()
def served(tmp_path):
    adapter = FusionAdapter(FakeFusionWire(), workdir=str(tmp_path / "work"))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    register_fusion_tools(app, adapter, docs_cache_dir=tmp_path / "cache")
    try:
        yield app, adapter
    finally:
        app.shutdown()


# -- the surface ----------------------------------------------------------------------


def test_the_three_are_tabled_individually_and_add_no_always_loaded_tool(served):
    app, _ = served
    for name in ("fu_design_stats", "fu_search_docs", "fu_api_detail"):
        assert name in app.registry.names()
        assert lanes.lane_for(name) == "fusion"
        assert app.registry.describe(name)["lane"] == "fusion"
    # a design read is read-scene; an introspection of the API is not the design
    assert trust.capability_for("fu_design_stats") == "read-scene"
    assert trust.capability_for("fu_search_docs") == "read-compute"
    assert trust.capability_for("fu_api_detail") == "read-compute"


# -- fu_design_stats ------------------------------------------------------------------


def test_stats_reads_the_whole_design_in_one_call(served):
    app, _ = served
    app.run_batch("fusion", PLATE)
    out = app.registry.call("fu_design_stats", {})
    assert out["design"] == "parametric" and out["units"] == "mm"
    assert out["bodies"] == 1
    assert out["total_volume_mm3"] == pytest.approx(96_000.0)
    assert out["bbox_mm"] == pytest.approx([0.0, 0.0, 0.0, 120.0, 80.0, 10.0])
    assert out["overlapping_pairs"] == [] and out["problems"] == []
    assert out["features"] == 2 and out["suppressed"] == 0


def test_stats_names_an_overlapping_pair_in_text_before_any_pixel(served):
    """The point of the tool: two bodies sharing space is a fact a model can
    read for a few dozen tokens, where seeing it would cost a render."""
    app, _ = served
    app.run_batch("fusion", PLATE)
    app.run_batch("fusion", OVERLAPPING)
    out = app.registry.call("fu_design_stats", {})
    assert out["bodies"] == 2
    assert out["overlapping_pairs"] == [["Body1", "Body2"]]
    assert out["default_named"] == ["Body1", "Body2"], "bodies nobody has named yet"
    assert len(json.dumps(out)) < 900, "one compact read, never a dump"


def test_stats_on_a_direct_design_reports_no_timeline_rather_than_raising(tmp_path):
    """A direct design has no timeline and no userParameters - reading either
    raises inside Fusion (doc 71 rows 5, 21), so the program never does."""
    adapter = FusionAdapter(FakeFusionWire(parametric=False), workdir=str(tmp_path))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    register_fusion_tools(app, adapter, docs_cache_dir=tmp_path / "cache")
    try:
        out = app.registry.call("fu_design_stats", {})
        assert out["design"] == "direct"
        assert out["features"] == 0 and out["user_parameters"] == 0
    finally:
        app.shutdown()


# -- fu_search_docs / fu_api_detail -----------------------------------------------------


def test_the_index_is_built_from_the_live_fusion_and_cached_per_version(served, tmp_path):
    app, adapter = served
    first = app.registry.call("fu_search_docs", {"query": "extrude"})
    assert first["indexed_symbols"] > 0
    assert any("Extrude" in r["path"] for r in first["results"])
    cache = list((tmp_path / "cache").glob("fusion-api-*.json"))
    assert len(cache) == 1, f"one cache file per Fusion version, got {cache}"
    # a second search neither rebuilds nor re-reads: the index is in memory
    before = len(adapter.wire.executed)
    app.registry.call("fu_search_docs", {"query": "sketch"})
    assert len(adapter.wire.executed) == before, "the index is not rebuilt per query"
    # a fresh server reads the cache instead of the bridge
    other = FusionAdapter(FakeFusionWire(), workdir=str(tmp_path / "w2"))
    docs = FusionDocs(other, cache_dir=tmp_path / "cache")
    assert docs.ensure_index() == first["indexed_symbols"]
    # one call only, and it is the version ping - you cannot pick a
    # version-matched cache file without first asking which version this is.
    # The expensive part, the index build, never runs again.
    assert len(other.wire.executed) == 1
    assert "_entries" not in other.wire.executed[0], "the index was not rebuilt"


def test_a_search_result_is_compact_and_ranked_by_the_path_not_the_prose(served):
    app, _ = served
    out = app.registry.call("fu_search_docs", {"query": "extrude", "limit": 3})
    assert len(out["results"]) <= 3
    assert out["results"][0]["path"].startswith("adsk."), "a path, never a blob"
    for row in out["results"]:
        assert set(row) <= {"path", "kind", "doc", "sig", "value"}
        assert len(row.get("doc", "")) <= 140


def test_an_empty_query_and_a_miss_both_answer_in_one_line(served):
    app, _ = served
    with pytest.raises(TeeError) as err:
        app.registry.call("fu_search_docs", {"query": "   "})
    assert err.value.code == "bad_op"
    miss = app.registry.call("fu_search_docs", {"query": "zzzznotathing"})
    assert miss["results"] == [] and "no matches" in miss["hint"]


def test_detail_answers_one_symbol_and_refuses_the_two_wrong_shapes(served):
    app, _ = served
    out = app.registry.call("fu_api_detail", {"path": "adsk.fusion.ExtrudeFeature"})
    assert out["found"] is True and out["path"] == "adsk.fusion.ExtrudeFeature"
    assert "members" in out
    with pytest.raises(TeeError) as err:
        app.registry.call("fu_api_detail", {"path": "os.system"})
    assert err.value.code == "bad_path", "only the adsk namespace is readable"
    with pytest.raises(TeeError) as err:
        app.registry.call("fu_api_detail", {"path": "adsk.fusion.NoSuchThing"})
    assert err.value.code == "unknown_api_symbol"
    assert "fu_search_docs" in err.value.fix or "adsk." in err.value.fix


def test_the_index_refuses_honestly_when_no_fusion_answers(tmp_path):
    class _Down(FakeFusionWire):
        def probe(self):
            return False

        def ping(self):
            raise TeeError("fusion_unreachable", "down", fix="start Fusion")

    adapter = FusionAdapter(_Down(), workdir=str(tmp_path))
    docs = FusionDocs(adapter, cache_dir=tmp_path / "cache")
    with pytest.raises(TeeError) as err:
        docs.ensure_index()
    assert err.value.code == "fusion_unreachable" and "Fusion" in err.value.fix
