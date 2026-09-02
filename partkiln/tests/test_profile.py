"""P2c acceptance for sketch/profile.py: frames, faces from loops (holes, rings,
arcs), the open-profile refusal naming the gap, and the sweep path."""

from __future__ import annotations

import math

import pytest

from partkiln.document import CommandError, Document
from partkiln.sketch.profile import NAMED_FRAMES, Frame, face_frame, make_frame, split_plane_ref

# -- pure Python: frames -----------------------------------------------------------------------


def test_named_frames_follow_the_right_hand_rule() -> None:
    xy, xz, yz = NAMED_FRAMES["XY"], NAMED_FRAMES["XZ"], NAMED_FRAMES["YZ"]
    assert xy.to_world(1, 2) == (1.0, 2.0, 0.0)
    assert xz.to_world(1, 2) == (1.0, 0.0, 2.0) and xz.normal == (0.0, -1.0, 0.0)
    assert yz.to_world(1, 2) == (0.0, 1.0, 2.0) and yz.normal == (1.0, 0.0, 0.0)
    for f in (xy, xz, yz):
        assert f.ydir == pytest.approx(_cross(f.normal, f.xdir))
        assert f.to_local(f.to_world(3, 4, 5)) == pytest.approx((3, 4, 5))
    assert xy.shifted(-5).origin == (0.0, 0.0, -5.0)
    assert xz.as_dict() == {
        "origin": [0.0, 0.0, 0.0],
        "normal": [0.0, -1.0, 0.0],
        "x": [1.0, 0.0, 0.0],
    }


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def test_face_frames_origin_rules_and_split() -> None:
    assert split_plane_ref("XY") == ("named", "XY", None)
    assert split_plane_ref("plane:top") == ("datum", "top", None)
    assert split_plane_ref("on:plate.end@centroid") == ("on", "plate.end", "centroid")
    assert split_plane_ref("on:plate.end@1,2,3") == ("on", "plate.end", "1,2,3")
    with pytest.raises(CommandError) as excinfo:
        split_plane_ref("top")
    assert excinfo.value.code == "pk_plane_missing"
    top = face_frame((50, 30, 10), (0, 0, 1), (50, 30, 10), None)
    assert top.origin == (0.0, 0.0, 10.0) and top.to_world(50, 30) == (50.0, 30.0, 10.0)
    assert face_frame((50, 30, 10), (0, 0, 1), (50, 30, 10), "centroid").origin == (
        50.0,
        30.0,
        10.0,
    )
    assert face_frame((50, 30, 10), (0, 0, 1), (50, 30, 10), "1,2,99").origin == (1.0, 2.0, 10.0)
    with pytest.raises(CommandError, match="@centroid or @x,y,z"):
        face_frame((0, 0, 0), (0, 0, 1), (0, 0, 0), "1,2")
    side = make_frame((100, 30, 5), (1, 0, 0))  # a +X face: x runs along world Y, y up
    assert side.xdir == (0.0, 1.0, 0.0) and side.ydir == pytest.approx((0.0, 0.0, 1.0))
    front = make_frame((50, 0, 5), (0, -1, 0))
    assert front.xdir == (1.0, 0.0, 0.0) and front.ydir == pytest.approx((0.0, 0.0, 1.0))
    with pytest.raises(CommandError, match="zero vector"):
        make_frame((0, 0, 0), (0, 0, 0))


# -- OCCT ---------------------------------------------------------------------------------------

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.sketch.profile import build_path, build_profile  # noqa: E402

pytestmark = pytest.mark.brep


def _sketch(props: dict) -> Document:
    doc = Document()
    doc.apply({"op": "create", "kind": "sketch", "name": "s", "props": {"plane": "XY", **props}})
    return doc


def _area(face) -> float:
    from partkiln.brep import shapes

    return shapes.area(face)


def test_rect_and_rect_with_a_hole() -> None:
    doc = _sketch({"profile": [{"rect": [100, 60], "tag": "r"}]})
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert len(p.faces) == 1 and p.loops == 1 and p.area_mm2 == 6000.0
    assert _area(p.faces[0]) == pytest.approx(6000.0)
    assert [t for t, _ in p.edges] == ["r.0", "r.1", "r.2", "r.3"]
    doc = _sketch(
        {"profile": [{"rect": [100, 60], "tag": "r"}, {"circle": 10, "at": [50, 30], "tag": "c"}]}
    )
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert len(p.faces) == 1 and p.loops == 2
    assert _area(p.faces[0]) == pytest.approx(6000 - math.pi * 25, abs=1e-6)
    assert p.edge_tag(p.edges[-1][1]) == "c"


def test_ring_and_two_disjoint_faces_and_arcs() -> None:
    doc = _sketch({"profile": [{"circle": 80, "tag": "o"}, {"circle": 20, "tag": "i"}]})
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert len(p.faces) == 1 and _area(p.faces[0]) == pytest.approx(
        math.pi * (1600 - 100), abs=1e-6
    )
    doc = _sketch(
        {"profile": [{"rect": [10, 10], "tag": "a"}, {"rect": [10, 10], "at": [30, 0], "tag": "b"}]}
    )
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert len(p.faces) == 2 and p.area_mm2 == 200.0
    doc = _sketch({"profile": [{"slot": [40, 10], "tag": "s"}]})
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert _area(p.faces[0]) == pytest.approx(30 * 10 + math.pi * 25, abs=1e-6)
    assert sorted(t for t, _ in p.edges) == ["s.0", "s.1", "s.a0", "s.a1"]


def test_placement_on_xz_and_a_shifted_frame() -> None:
    doc = _sketch({"profile": [{"rect": [100, 60], "tag": "r"}]})
    from partkiln.brep import shapes

    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XZ"])
    assert shapes.bbox(p.faces[0]) == pytest.approx((0, 0, 0, 100, 0, 60), abs=1e-9)
    p = build_profile(doc.sketches["s"], Frame((0.0, 0.0, 7.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)))
    assert shapes.bbox(p.faces[0])[2] == pytest.approx(7.0)


def test_open_profile_refuses_naming_the_gap() -> None:
    doc = Document()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {
                "plane": "XY",
                "entities": [
                    {"point": "a", "at": [0, 0], "fixed": True},
                    {"point": "b", "at": [30, 0], "fixed": True},
                    {"point": "c", "at": [30, 20], "fixed": True},
                    {"point": "d", "at": [0, 0.5], "fixed": True},
                    {"line": "ab", "a": "a", "b": "b"},
                    {"line": "bc", "a": "b", "b": "c"},
                    {"line": "cd", "a": "c", "b": "d"},
                ],
            },
        }
    )
    with pytest.raises(CommandError) as excinfo:
        build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert excinfo.value.code == "pk_sketch_open"
    assert "0.500 mm gap between a and d" in str(excinfo.value)
    assert "coincident" in str(excinfo.value)
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    with pytest.raises(CommandError, match=r"0\.500 mm gap") as excinfo:
        doc.apply({"op": "create", "kind": "extrude", "props": {"sketch": "s", "distance": 5}})
    assert excinfo.value.code == "pk_sketch_open"


def test_coincident_corners_close_a_wire_and_build_path() -> None:
    doc = Document()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {
                "plane": "XY",
                "entities": [
                    {"point": "a", "at": [0, 0], "fixed": True},
                    {"point": "b", "at": [30, 0], "fixed": True},
                    {"point": "c", "at": [30, 20], "fixed": True},
                    {"point": "d", "at": [0, 0], "fixed": True},
                    {"line": "ab", "a": "a", "b": "b"},
                    {"line": "bc", "a": "b", "b": "c"},
                    {"line": "cd", "a": "c", "b": "d"},
                ],
                "constraints": [{"c": "coincident", "a": "d", "b": "a"}],
            },
        }
    )
    p = build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])
    assert _area(p.faces[0]) == pytest.approx(300.0)
    from partkiln.brep import shapes

    assert shapes.counts(p.faces[0])["vertices"] == 3  # shared vertices, not four
    path_doc = Document()
    path_doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "p",
            "props": {
                "plane": "XZ",
                "entities": [
                    {"point": "a", "at": [0, 0], "fixed": True},
                    {"point": "b", "at": [0, 50], "fixed": True},
                    {"point": "c", "at": [20, 50], "fixed": True},
                    {"line": "l1", "a": "a", "b": "b"},
                    {"line": "l2", "a": "b", "b": "c"},
                ],
            },
        }
    )
    wire = build_path(path_doc.sketches["p"], NAMED_FRAMES["XZ"])
    assert shapes.counts(wire)["edges"] == 2 and shapes.bbox(wire)[5] == pytest.approx(50.0)
    with pytest.raises(CommandError, match="open chain"):
        build_path(doc.sketches["s"], NAMED_FRAMES["XY"]) if False else build_path(
            _sketch({"profile": {"circle": 5}}).sketches["s"], NAMED_FRAMES["XY"]
        )
