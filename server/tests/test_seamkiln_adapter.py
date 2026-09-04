"""The seamkiln adapter (A53 P4): garments through the existing 17 tools.

The point of these tests is the surface promise. seamkiln adds a whole
product - patterns, sewing, bodies, drape, interchange - and the always-loaded
tool list does not move, because a garment is a scene and the Adapter protocol
already knows how to drive one.
"""

from __future__ import annotations

import pytest

from tee.adapters.seamkiln import SeamkilnAdapter
from tee.app import TeeApp
from tee.kernel.adapter import Adapter
from tee.kernel.errors import TeeError

seamkiln = pytest.importorskip("seamkiln", reason="seamkiln is an optional extra")

COARSE = 25.0


@pytest.fixture
def app(tmp_path):
    return TeeApp({"seamkiln": SeamkilnAdapter(tmp_path)}, project_root=tmp_path)


@pytest.fixture
def adapter(app):
    return app.adapters["seamkiln"]


def test_it_is_an_adapter(adapter) -> None:
    assert isinstance(adapter, Adapter)
    assert adapter.probe() is True
    assert adapter.info().id == "seamkiln"


def test_a_block_becomes_entities_with_stable_ids(adapter) -> None:
    diff = adapter.execute([{"op": "create", "kind": "block", "props": {"block": "tee"}}])
    assert len(diff.created) == 4
    assert "panel:FRONT" in diff.created

    ids = {e.id for e in adapter.list_entities()}
    assert {"panel:FRONT", "panel:BACK", "seam:side-right"} <= ids
    assert adapter.list_entities() == adapter.list_entities()  # stable across calls


def test_entities_carry_summaries_not_geometry(adapter) -> None:
    adapter.execute([{"op": "create", "kind": "block", "props": {"block": "tee"}}])
    front = next(e for e in adapter.list_entities() if e.id == "panel:FRONT")
    assert set(front.summary) >= {"area_mm2", "perimeter_mm", "edges", "bbox_mm"}
    assert "outline" not in front.summary and "points" not in front.summary
    assert len(repr(front.detailed())) < 400


def test_a_panel_can_be_built_from_points(adapter) -> None:
    diff = adapter.execute(
        [
            {
                "op": "create",
                "kind": "panel",
                "name": "SQ",
                "props": {"outline": [[0, 0], [100, 0], [100, 100], [0, 100]]},
            }
        ]
    )
    assert diff.created == ["panel:SQ"]
    assert diff.details["panel:SQ"]["area_mm2"] == pytest.approx(10_000.0)


def test_seam_allowance_does_not_invalidate_the_seams(adapter) -> None:
    """The bug this test exists for: replacing the outline with the mitred cut
    line re-tags corners by angle, so the tee front went from 8 edges to 6 and
    every seam naming edge 6 or 7 pointed past the end of the list."""
    adapter.execute([{"op": "create", "kind": "block", "props": {"block": "tee"}}])
    before = next(e for e in adapter.list_entities() if e.id == "panel:FRONT").summary["edges"]
    adapter.execute([{"op": "set", "id": "panel:FRONT", "props": {"seam_allowance_mm": 10.0}}])
    after = next(e for e in adapter.list_entities() if e.id == "panel:FRONT").summary["edges"]
    assert after == before

    diff = adapter.execute(
        [{"op": "arrange", "props": {"body": "mannequin", "particle_distance_mm": COARSE}}]
    )
    assert diff.details["garment"]["points"] > 0


def test_the_full_lane_is_one_batch(adapter, tmp_path) -> None:
    out = tmp_path / "pattern.dxf"
    diff = adapter.execute(
        [
            {"op": "create", "kind": "block", "props": {"block": "tee"}},
            {"op": "arrange", "props": {"body": "mannequin", "particle_distance_mm": COARSE}},
            {"op": "drape", "props": {"fabric": "cotton_poplin", "frames": 60}},
            {"op": "export", "props": {"format": "dxf", "out": str(out)}},
        ]
    )
    assert out.is_file() and out.stat().st_size > 1000
    report = diff.details["garment"]
    assert report["contact"]["worn"] is True
    assert report["seam_gaps"]["mean_gap_mm"] < 10.0


def test_drape_arranges_first_rather_than_refusing(adapter) -> None:
    """Session.drape arranges when nothing is arranged yet. A refusal that a
    caller can only answer by typing the obvious next step is friction, not
    safety - the refusals that matter are the ones naming something the
    caller actually got wrong."""
    adapter.execute([{"op": "create", "kind": "block", "props": {"block": "tee"}}])
    diff = adapter.execute([{"op": "drape", "props": {"frames": 4}}])
    assert "garment" in diff.details


def test_a_drape_that_fell_off_says_so_in_the_diff(adapter) -> None:
    """A silent failure would be a garment on the floor with healthy-looking
    seam numbers. The note is how the caller finds out without asking."""
    adapter.execute(
        [
            {"op": "create", "kind": "block", "props": {"block": "tee"}},
            {"op": "arrange", "props": {"body": "mannequin", "particle_distance_mm": COARSE}},
        ]
    )
    diff = adapter.execute([{"op": "drape", "props": {"frames": 4}}])
    worn = diff.details["garment"]["contact"]["worn"]
    assert worn or any("NOT being worn" in note for note in diff.notes)


def test_checkpoint_and_rollback_round_trip(adapter) -> None:
    adapter.execute([{"op": "create", "kind": "block", "props": {"block": "tee"}}])
    payload = adapter.snapshot("four-panels")
    adapter.execute([{"op": "delete", "id": "panel:SLEEVE_L"}])
    assert adapter.info().to_payload()["panels"] == 3

    adapter.restore(payload)
    assert adapter.info().to_payload()["panels"] == 4
    assert {e.id for e in adapter.list_entities() if e.kind == "panel"} == {
        "panel:FRONT",
        "panel:BACK",
        "panel:SLEEVE_L",
        "panel:SLEEVE_R",
    }


def test_every_refusal_names_the_fix(adapter, tmp_path) -> None:
    for batch, needle in (
        ([{"op": "knit"}], "seamkiln accepts"),
        # draping with nothing drafted says THAT, rather than complaining
        # about a missing arrange step the caller could not have taken
        ([{"op": "drape"}], "block"),
        ([{"op": "create", "kind": "block", "props": {"block": "corset"}}], "Built-in blocks"),
    ):
        with pytest.raises(TeeError) as excinfo:
            adapter.execute(batch)
        assert needle in excinfo.value.fix, f"{excinfo.value.fix!r} does not name the fix"
    with pytest.raises(TeeError, match="export needs"):
        adapter.execute(
            [
                {"op": "create", "kind": "block", "props": {"block": "tee"}},
                {"op": "export", "props": {"format": "dxf"}},
            ]
        )


def test_capture_refuses_rather_than_returning_an_empty_room(adapter) -> None:
    with pytest.raises(TeeError, match="nothing to render"):
        adapter.capture("front", 200_000)


def test_the_surface_does_not_move(app) -> None:
    """A53's whole architectural claim, as an assertion."""
    from tee.server import _DESC

    assert len(_DESC) == 17, "the always-loaded surface moved"
    assert not any(name.startswith("sk_") for name in _DESC)
    assert {"sk_blocks", "sk_fabrics", "sk_fit", "sk_plot", "sk_interchange", "sk_body"} <= set(
        app.registry.names()
    )


def test_garment_queries_find_the_tools(app) -> None:
    for query in ("sewing pattern", "drape a garment", "fit a shirt", "fabric properties"):
        names = [item["name"] for item in app.registry.search(query, limit=3)["items"]]
        assert any(n.startswith("sk_") for n in names), f"{query!r} found {names}"


def test_the_long_tail_answers_without_an_adapter_scene(app) -> None:
    fabrics = app.registry.call("sk_fabrics", {})
    assert fabrics["fabrics"] and all(row["tier"] == "plausible" for row in fabrics["fabrics"])
    dialects = app.registry.call("sk_interchange", {"action": "dialects"})["dialects"]
    assert dialects["astm"]["verified"] is True
    assert dialects["aama"]["verified"] is False
    with pytest.raises(TeeError) as excinfo:
        app.registry.call("sk_fit", {})
    assert "arrange" in excinfo.value.fix


def test_a_cad_export_reads_through_the_interchange_tool(app, tmp_path) -> None:
    """What CLO writes: an R12 file (no $INSUNITS), a heavy POLYLINE boundary
    in centimetres declared by the header's "UNITS: METRIC", the piece named
    by its "PIECE NAME:" text. The tool must hand back millimetres and say
    where the unit came from - the same file read as mm is doll-sized."""
    import ezdxf

    doc = ezdxf.new("R12")
    space = doc.modelspace()
    space.add_text("STYLE NAME: Camiseta", dxfattribs={"layer": "1", "insert": (0.0, 90.0)})
    space.add_text("UNITS: METRIC", dxfattribs={"layer": "1", "insert": (0.0, 80.0)})
    block = doc.blocks.new("Frente_M")
    block.add_polyline2d(
        [(0, 0), (45, 0), (45, 61), (0, 61)], close=True, dxfattribs={"layer": "1"}
    )
    for spot in ((0, 0), (45, 0), (45, 61), (0, 61)):
        block.add_point(spot, dxfattribs={"layer": "2"})
    block.add_polyline2d(
        [(0, 0), (45, 0), (45, 61), (0, 61)], close=True, dxfattribs={"layer": "84"}
    )
    block.add_text("PIECE NAME: Frente", dxfattribs={"layer": "1", "insert": (1.0, 1.0)})
    block.add_text("# 180", dxfattribs={"layer": "1", "insert": (1.0, 2.0)})
    space.add_blockref("Frente_M", (0.0, 0.0))
    path = tmp_path / "clo.dxf"
    doc.saveas(path)

    result = app.registry.call("sk_interchange", {"action": "read", "path": str(path)})
    assert result["pieces"] == 1 and result["style"] == "Camiseta"
    assert result["insunits"] == 0 and result["units_source"] == "header UNITS: METRIC"
    assert result["scale_mm_per_unit"] == 10.0
    assert result["validation_curves"] == 1 and result["notes"] == []
    assert result["names"] == {"Frente_M": "Frente"}
    assert result["summary"]["name"] == "Camiseta"
    (piece,) = result["summary"]["pieces"]
    assert (piece["id"], piece["edges"], piece["area_mm2"]) == ("Frente_M", 4, 274500.0)

    forced = app.registry.call(
        "sk_interchange", {"action": "read", "path": str(path), "units_mm": 1.0}
    )
    assert forced["units_source"] == "units_mm argument"
    assert forced["summary"]["pieces"][0]["area_mm2"] == 2745.0


def test_sk_tools_are_tabled_in_the_trust_kernel(app) -> None:
    """A tool the trust table does not know fails at STARTUP - so reaching
    this line at all is most of the assertion."""
    from tee.kernel import trust

    for name in ("sk_blocks", "sk_fabrics", "sk_fit"):
        assert trust.capability_for(name) == "read-scene"
    for name in ("sk_plot", "sk_interchange"):
        assert trust.capability_for(name) == "write-artifacts"


# ------------------------------------------------------------------- A65
# The A54-A64 capabilities existed and were invisible: a zipped, buttoned,
# locked garment on a walking figure listed the same entities as a bare tee,
# and "zipper", "button" and "walk cycle" returned an EMPTY tool search. P4's
# acceptance says the long tail lands top-3; these pin it for the follow-ups.


def test_hardware_locks_and_the_body_are_entities(adapter) -> None:
    adapter.execute(
        [
            {"op": "create", "kind": "block", "props": {"block": "jacket-zip"}},
            {"op": "arrange", "props": {"particle_distance_mm": COARSE}},
            {"op": "zip", "props": {"opening": "centre-front", "material": "nylon", "frames": 20}},
            {"op": "lock", "props": {"scope": "panel:BACK", "why": "approved"}},
        ]
    )
    by_kind = {}
    for entity in adapter.list_entities():
        by_kind.setdefault(entity.kind, []).append(entity)
    assert {"panel", "seam", "garment", "zipper", "locks", "body"} <= set(by_kind)
    zipper = by_kind["zipper"][0]
    assert zipper.id == "zip:centre-front" and zipper.summary["material"] == "nylon"
    assert by_kind["locks"][0].summary["locked"] == ["panel:BACK"]
    assert by_kind["body"][0].summary["kind"] == "mannequin"
    assert by_kind["body"][0].summary["arrangement"] == "cylinder"


def test_the_follow_up_capabilities_land_top_three_in_search(app) -> None:
    for query, want in (
        ("zipper on a jacket", "sk_hardware"),
        ("fasten a button", "sk_hardware"),
        ("walk cycle animation", "sk_avatar"),
        ("import a custom avatar", "sk_avatar"),
        ("pull the cloth interactively", "sk_touch"),
        ("hand off garment to blender", "sk_handoff"),
    ):
        names = [item["name"] for item in app.registry.search(query, limit=3)["items"]]
        assert want in names, f"{query!r} found {names}"


def test_the_new_long_tail_tools_answer_and_the_surface_still_does_not_move(app) -> None:
    from tee.server import _DESC

    assert len(_DESC) == 17
    hardware = app.registry.call("sk_hardware", {})
    assert set(hardware["zippers"]["materials"]) == {"nylon", "plastic", "metal"}
    assert "two-way-head-to-head" in hardware["zippers"]["layouts"]
    avatar = app.registry.call("sk_avatar", {})
    assert {"mannequin", "anny", "posed", "figure", "custom"} <= set(avatar["bodies"])
    assert avatar["gaits"]["walk"]["speed_ms"] == pytest.approx(1.35)
    touch = app.registry.call("sk_touch", {})
    assert {"pull", "fold", "ease"} <= set(touch["verbs"])
    handoff = app.registry.call("sk_handoff", {})
    assert handoff["targets"]["blender"]["driven_by_tee"] is True
    assert handoff["targets"]["godot"]["driven_by_tee"] is False
