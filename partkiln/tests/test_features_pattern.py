"""P2c acceptance for pattern and mirror through the verbs: F5 (one n-ary cut),
suppression, the circular disc, sketch-driven copies, mirror of a body and of a
feature, and the refusals."""

from __future__ import annotations

import math
import time

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from test_document_parts import F1, F2, F5, build

pytestmark = pytest.mark.brep


def test_f5_rect_pattern_is_one_nary_cut_with_the_measured_topology() -> None:
    build(F5())
    doc = build(F5()[:4])
    t = time.perf_counter()
    r = doc.apply(
        {
            "op": "create",
            "kind": "pattern",
            "name": "p",
            "props": {"of": "h", "dx": 20, "nx": 10, "dy": 20, "ny": 10},
        }
    )
    dt = time.perf_counter() - t
    assert r["volume_mm3"] == pytest.approx(520481.421, abs=5e-4)
    assert r["faces"] == 106 and r["edges"] == 312
    assert r["instances"] == 100 and r["suppressed"] == [] and r["assumed"]["layout"] == "rect"
    assert r["names"] == {"count": 99, "first": [f"p.{i}.1.wall" for i in range(1, 9)]}
    assert dt < 0.6, f"pattern took {dt:.3f} s (cut alone measured 0.09-0.12 s)"
    inv = doc.parts["plate"].inventory()
    assert inv.face_index("p.57.1.wall") is not None
    assert sum(1 for n in inv.edge_names if n.endswith("~seam")) == 100


def test_suppress_three_instances_leaves_97_holes() -> None:
    doc = build(F5())
    r = doc.apply({"op": "set", "id": "feat:p", "props": {"suppress": [3, 7, 50]}})
    assert r["failed"] == []
    s = doc.parts["plate"].summary()
    assert s["faces"] - 6 == 97
    assert s["volume_mm3"] == pytest.approx(520481.421 + 3 * math.pi * 16 * 12, abs=5e-3)
    with pytest.raises(CommandError, match="0 is the source") as excinfo:
        doc.apply({"op": "set", "id": "feat:p", "props": {"suppress": [0]}})
    assert excinfo.value.code == "pk_needs"


def test_circular_pattern_on_a_disc() -> None:
    doc = Document(name="disc")
    for c in [
        {"op": "create", "kind": "part", "name": "disc"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "sk",
            "props": {"plane": "XY", "profile": [{"circle": 80, "tag": "c"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "disc",
            "props": {"sketch": "sk", "distance": 5},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "disc.end", "at": [[30, 0]], "dia": 5},
        },
    ]:
        doc.apply(c)
    r = doc.apply(
        {
            "op": "create",
            "kind": "pattern",
            "name": "p",
            "props": {"of": "h", "layout": "circ", "axis": "Z", "n": 6},
        }
    )
    assert r["volume_mm3"] == pytest.approx(24543.693, abs=5e-4) and r["faces"] == 9
    assert r["assumed"]["angle"] == 360 and r["instances"] == 6
    assert r["names"] == [f"p.{i}.1.wall" for i in range(1, 6)]
    twin = Document.replay(doc.script())
    assert twin.fingerprint() == doc.fingerprint()


def test_sketch_driven_pattern_of_a_join_extrude() -> None:
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "boss_sk",
            "props": {
                "plane": "on:plate.end",
                "profile": [{"circle": 6, "at": [10, 10], "tag": "b"}],
            },
        }
    )
    boss = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "boss",
            "props": {"sketch": "boss_sk", "distance": 4},
        }
    )
    assert boss["mode"] == "join" and boss["delta_mm3"] == pytest.approx(math.pi * 9 * 4, abs=5e-4)
    r = doc.apply(
        {
            "op": "create",
            "kind": "pattern",
            "name": "bp",
            "props": {"of": "boss", "points": [[20, 0], [0, 20]]},
        }
    )
    assert r["assumed"]["layout"] == "sketch" and r["instances"] == 3
    assert r["delta_mm3"] == pytest.approx(2 * math.pi * 9 * 4, abs=5e-4)
    assert {"bp.1.end", "bp.2.end", "bp.1.side.b", "bp.2.side.b"} <= set(r["names"])
    assert doc.parts["plate"].inventory().face_index("bp.1.end") is not None


def test_mirror_f2_about_x80_and_mirror_of_a_feature() -> None:
    doc = build(F2())
    r = doc.apply(
        {"op": "create", "kind": "mirror", "name": "m", "props": {"of": "bracket", "plane": "x=80"}}
    )
    assert r["volume_mm3"] == pytest.approx(89833.933, abs=5e-4) and r["faces"] == 17
    assert r["names"]["count"] == 12 and "m.h.1.wall" in r["names"]["first"]
    doc = build(F1())
    with pytest.raises(
        CommandError, match="changed nothing"
    ) as excinfo:  # x=50 mirrored about x=0 misses
        doc.apply(
            {
                "op": "create",
                "kind": "mirror",
                "name": "mh",
                "props": {"of": "hole1", "plane": "YZ"},
            }
        )
    assert excinfo.value.code == "pk_no_effect"
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "plane",
            "name": "mid",
            "props": {"offset": {"from": "YZ", "distance": 30}},
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "mirror",
            "name": "mh",
            "props": {"of": "hole1", "plane": "plane:mid"},
        }
    )
    assert r["delta_mm3"] == pytest.approx(-785.398, abs=5e-4) and r["names"] == ["mh.1.1.wall"]


def test_pattern_refusals_name_the_fix() -> None:
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "f",
            "props": {"edges": "plate:edges(dir=Z)", "r": 2},
        }
    )
    with pytest.raises(CommandError, match="no tool body") as excinfo:
        doc.apply({"op": "create", "kind": "pattern", "props": {"of": "f", "dx": 5, "nx": 2}})
    assert excinfo.value.code == "pk_needs"
    with pytest.raises(CommandError, match="layout") as excinfo:
        doc.apply({"op": "create", "kind": "pattern", "props": {"of": "hole1"}})
    assert excinfo.value.code == "pk_needs"
    with pytest.raises(CommandError, match="changed nothing") as excinfo:
        doc.apply({"op": "create", "kind": "pattern", "props": {"of": "hole1", "dx": 500, "nx": 2}})
    assert excinfo.value.code == "pk_no_effect"
    with pytest.raises(CommandError, match="every instance") as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "pattern",
                "props": {"of": "hole1", "dx": 20, "nx": 2, "suppress": [1]},
            }
        )
    assert excinfo.value.code == "pk_no_effect"
