"""P2c acceptance for the part kernel through the document verbs: F1, F2, F3, sweep,
loft, shell, draft, taper, split, combine, datums, edits (Law 14), cosmetic threads
(Law 18), no-effect booleans (Law 11) and the deliberate failures (rule 6)."""

from __future__ import annotations

import math
import time
from typing import Any

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from test_document_parts import F1, F2, F3, build

pytestmark = pytest.mark.brep


def part_of(doc: Document) -> Any:
    return doc.parts[next(iter(doc.parts))]


# -- F1 ---------------------------------------------------------------------------------------


def test_f1_through_the_verbs_numbers_names_and_time() -> None:
    build(F1())  # warm
    t = time.perf_counter()
    doc = build(F1())
    dt = time.perf_counter() - t
    part = doc.parts["plate"]
    s = part.summary()
    assert s["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert s["faces"] == 7 and s["edges"] == 15 and s["solids"] == 1
    assert s["area_mm2"] == pytest.approx(15357.080, abs=5e-4)
    names = set(part.inventory().face_names)
    assert {
        "plate.start",
        "plate.end",
        "plate.side.r.0",
        "plate.side.r.1",
        "plate.side.r.2",
        "plate.side.r.3",
        "hole1.1.wall",
    } == names
    assert "hole1.1.wall|plate.end" in part.inventory().edge_names
    assert "hole1.1.wall~seam" in part.inventory().edge_names
    assert dt < 0.2, f"F1 through the verbs took {dt * 1000:.1f} ms (budget 30 ms warm + slack)"


def test_hole_std_m6_clearance_reads_iso_273_and_says_so() -> None:
    doc = build(F1()[:3])
    r = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "plate.end", "at": [[20, 30]], "std": "M6 clearance"},
        }
    )
    assert r["dia_mm"] == 6.6
    assert r["assumed"]["series"] == "normal"
    assert r["assumed"]["dia"].startswith("6.6mm from ISO 273")
    assert any("ISO 273" in n and "Apache" in n for n in r["notes"])
    assert r["delta_mm3"] == pytest.approx(-math.pi * 3.3**2 * 10, abs=5e-4)
    tap = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "tap",
            "props": {"on": "plate.end", "at": [[80, 30]], "std": "M6 tap", "depth": 6},
        }
    )
    assert tap["dia_mm"] == 5.0 and tap["cosmetic"] == {"thread": "M6x1"}
    assert tap["names"] == ["tap.1.wall", "tap.1.bottom"]
    assert tap["assumed"]["bottom"] == "flat"


def test_hole_seats_match_the_measured_arithmetic() -> None:
    doc = build(F1()[:3])
    cb = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "cb",
            "props": {
                "on": "plate.end",
                "at": [[50, 30]],
                "dia": 10,
                "seat": {"kind": "counterbore", "dia": 11, "depth": 6},
            },
        }
    )
    assert cb["delta_mm3"] == pytest.approx(-(785.398 + 98.96), abs=5e-3)
    assert set(cb["names"]) == {"cb.1.wall", "cb.1.seat", "cb.1.seat.wall"}
    doc = build(F1()[:3])
    cs = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "cs",
            "props": {
                "on": "plate.end",
                "at": [[50, 30]],
                "dia": 10,
                "seat": {"kind": "countersink", "dia": 12, "angle": 90},
            },
        }
    )
    assert cs["delta_mm3"] == pytest.approx(-(785.398 + 16.755), abs=5e-3)
    assert set(cs["names"]) == {"cs.1.wall", "cs.1.seat"}


def test_edit_hole_d10_to_d12_reports_the_blast_radius() -> None:
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "fillet1",
            "props": {"edges": "plate:edges(dir=Z)", "r": 2},
        }
    )
    r = doc.apply({"op": "set", "id": "feat:hole1", "props": {"dia": 12}})
    assert r["changed"] == [
        {"feature": "hole1", "delta_mm3": pytest.approx(-345.575, abs=5e-4), "faces": 7}
    ]
    assert r["unchanged"] == 1 and r["unchanged_features"] == ["fillet1"]
    assert r["failed"] == []
    assert r["volume_mm3"] == pytest.approx(58869.027 - 34.336, abs=2e-3)
    plain = build(F1())
    assert plain.apply({"op": "set", "id": "hole1", "props": {"dia": 12}})[
        "volume_mm3"
    ] == pytest.approx(58869.027, abs=5e-4)


def test_cosmetic_thread_leaves_the_fingerprint_bit_identical() -> None:
    doc = build(F1())
    before = doc.fingerprint()
    r = doc.apply({"op": "set", "id": "feat:hole1", "props": {"thread": "M12"}})
    assert r["changed"] == [] and r["unchanged"] == 1
    assert doc.fingerprint() == before
    assert doc.parts["plate"].feature("hole1").details()["cosmetic"] == {"thread": "M12"}
    shaft = build(F3()[:3])
    bare = build(F3()[:3])
    bare.parts["shaft"].feature("shaft").args.pop("thread")
    bare.parts["shaft"].regen(bare, 0)
    assert shaft.fingerprint() == bare.fingerprint()


def test_a_cut_that_removes_nothing_refuses_pk_no_effect() -> None:
    doc = build(F1())
    before = doc.fingerprint()
    with pytest.raises(CommandError, match="changed nothing") as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "extrude",
                "name": "miss",
                "props": {"sketch": "base", "distance": 5, "mode": "cut", "direction": "-"},
            }
        )
    assert excinfo.value.code == "pk_no_effect"
    assert "allow_no_effect" in str(excinfo.value)
    assert doc.fingerprint() == before
    r = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "miss",
            "props": {
                "sketch": "base",
                "distance": 5,
                "mode": "cut",
                "direction": "-",
                "allow_no_effect": True,
            },
        }
    )
    assert r["delta_mm3"] == 0.0 and "allow_no_effect" in r["notes"][0]


# -- F2 ---------------------------------------------------------------------------------------


def test_f2_through_the_verbs_and_the_thickness_edit() -> None:
    build(F2())
    t = time.perf_counter()
    doc = build(F2())
    dt = time.perf_counter() - t
    part = doc.parts["bracket"]
    s = part.summary()
    assert s["volume_mm3"] == pytest.approx(44916.967, abs=5e-4)
    assert s["faces"] == 13 and s["edges"] == 33
    assert s["mass_g"] == pytest.approx(44916.967 * 7850 * 1e-6, abs=1e-3)
    fillet = part.feature("fillet1").details()
    assert fillet["resolved"] == {"upright:edges(concave)": 1}
    assert fillet["selected"] == {"upright:edges(concave)": ["base.end|upright.end"]}
    hole = part.feature("h").details()
    assert hole["dia_mm"] == 6.6 and hole["names"] == [
        "h.1.wall",
        "h.2.wall",
        "h.3.wall",
        "h.4.wall",
    ]
    assert dt < 0.3, f"F2 took {dt * 1000:.0f} ms"
    r = doc.apply({"op": "param_set", "props": {"t": "8mm"}})
    regen = r["regen"]["part:bracket"]
    assert [c["feature"] for c in regen["changed"]] == ["base", "upright", "h"]
    assert regen["unchanged_features"] == ["fillet1"]
    assert regen["failed"] == []
    assert regen["volume_mm3"] == pytest.approx(58403.27, abs=5e-3)
    r = doc.apply({"op": "param_set", "props": {"t": "4mm"}})
    assert r["regen"]["part:bracket"]["volume_mm3"] == pytest.approx(30790.66, abs=5e-3)
    assert r["regen"]["part:bracket"]["unchanged_features"] == ["fillet1"]
    assert part.summary()["faces"] == 13


def test_sketch_dimension_edit_regenerates_the_part() -> None:
    doc = build(F1())
    r = doc.apply({"op": "set", "id": "sk:base", "props": {"r.w": 120}})
    regen = r["regen"]["part:plate"]
    assert [c["feature"] for c in regen["changed"]] == ["plate"]
    assert regen["unchanged_features"] == ["hole1"]
    assert regen["volume_mm3"] == pytest.approx(120 * 60 * 10 - 785.398, abs=5e-4)


def test_rename_resolves_downstream_references_by_fingerprint_and_says_so() -> None:
    doc = build(F1())
    r = doc.apply({"op": "set", "id": "feat:plate", "props": {"name": "base"}})
    assert r["props"] == [{"key": "name", "old": "plate", "new": "base"}]
    assert r["failed"] == [] and r["unchanged"] == 2
    hole = doc.parts["plate"].feature("hole1")
    assert hole.selected == {"plate.end": ["base.end"]}
    assert any("resolved by fingerprint to base.end" in n for n in hole.notes)
    assert "base.end" in doc.parts["plate"].inventory().face_names


def test_face_reorder_after_upstream_edit_never_silently_retargets() -> None:
    """The upright's height changes so every face moves; the fillet and the
    holes must land on the same named edge/face (history), not on whatever
    OCCT lists first now."""
    doc = build(F2())
    r = doc.apply({"op": "set", "id": "sk:up_sk", "props": {"u.h": 60}})
    regen = r["regen"]["part:bracket"]
    assert regen["failed"] == []
    part = doc.parts["bracket"]
    assert part.feature("fillet1").selected == {"upright:edges(concave)": ["base.end|upright.end"]}
    assert part.feature("h").selected == {"base.end": ["base.end"]}
    assert part.summary()["volume_mm3"] == pytest.approx(44916.967 + 80 * 6 * 20, abs=5e-3)


# -- F3 and the other kinds ------------------------------------------------------------------


def test_f3_revolve_names_every_step_and_the_keyway() -> None:
    doc = build(F3())
    part = doc.parts["shaft"]
    rev = part.feature("shaft").details()
    assert rev["volume_mm3"] == pytest.approx(49480.084, abs=5e-4) and rev["faces"] == 7
    assert set(rev["names"]) == {f"shaft.p.{k}" for k in range(7)}
    assert rev["cosmetic"] == {"thread": "M20x2.5"}
    key = part.feature("keyway").details()
    assert key["delta_mm3"] == pytest.approx(-611.9, abs=0.1)
    # the keyway spans the r15 step exactly (x 50..80), so its end walls merge
    # into the step annuli: floor + two long walls = 3 new faces
    assert part.summary()["faces"] == 7 + 3


def test_revolve_partial_has_caps_and_axis_forms() -> None:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [10, 20], "tag": "r"}]},
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "revolve",
            "name": "half",
            "props": {"sketch": "s", "axis": "Y", "angle": 180},
        }
    )
    assert r["volume_mm3"] == pytest.approx(math.pi * 100 * 10, abs=5e-4)
    assert {"half.cap.a", "half.cap.b"} <= set(r["names"])
    doc2 = Document()
    doc2.apply({"op": "create", "kind": "part", "name": "p"})
    doc2.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [10, 20], "tag": "r"}]},
        }
    )
    r2 = doc2.apply(
        {
            "op": "create",
            "kind": "revolve",
            "name": "full",
            "props": {"sketch": "s", "axis": [[0, 0, 0], [0, 1, 0]]},
        }
    )
    assert r2["volume_mm3"] == pytest.approx(math.pi * 100 * 20, abs=5e-4)
    assert r2["assumed"]["angle"] == 360


def test_sweep_and_loft() -> None:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "a"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "circ",
            "props": {"plane": "XY", "profile": [{"circle": 6, "tag": "c"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "path",
            "props": {
                "plane": "XZ",
                "entities": [
                    {"point": "a", "at": [0, 0], "fixed": True},
                    {"point": "b", "at": [0, 50], "fixed": True},
                    {"line": "l", "a": "a", "b": "b"},
                ],
            },
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "sweep",
            "name": "sw",
            "props": {"profile": "circ", "path": "path"},
        }
    )
    assert r["volume_mm3"] == pytest.approx(math.pi * 9 * 50, abs=5e-4)
    assert set(r["names"]) == {"sw.side.c", "sw.cap.a", "sw.cap.b"}
    assert r["assumed"]["frenet"] is False
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "a"})
    doc.apply(
        {
            "op": "create",
            "kind": "plane",
            "name": "top",
            "props": {"offset": {"from": "XY", "distance": 30}},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s0",
            "props": {"plane": "XY", "profile": [{"rect": [40, 40], "tag": "r"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s1",
            "props": {
                "plane": "plane:top",
                "profile": [{"rect": [20, 20], "at": [10, 10], "tag": "r"}],
            },
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "loft",
            "name": "lf",
            "props": {"sections": ["s0", "s1"], "ruled": True},
        }
    )
    assert r["volume_mm3"] == pytest.approx(28000.0, abs=1e-6) and r["faces"] == 6
    assert set(r["names"]) == {
        "lf.side.r.0",
        "lf.side.r.1",
        "lf.side.r.2",
        "lf.side.r.3",
        "lf.cap.a",
        "lf.cap.b",
    }
    assert doc.summary()["datums"] == [
        {
            "id": "plane:top",
            "kind": "datum",
            "type": "plane",
            "origin": [0.0, 0.0, 30.0],
            "normal": [0.0, 0.0, 1.0],
        }
    ]


def _box(w: float, h: float, d: float) -> Document:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "box"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s0",
            "props": {"plane": "XY", "profile": [{"rect": [w, h], "tag": "r"}]},
        }
    )
    doc.apply(
        {"op": "create", "kind": "extrude", "name": "b", "props": {"sketch": "s0", "distance": d}}
    )
    return doc


def test_f4_shell_and_draft() -> None:
    doc = _box(60, 40, 30)
    r = doc.apply(
        {"op": "create", "kind": "shell", "name": "sh", "props": {"faces": "b.end", "t": 2}}
    )
    assert r["volume_mm3"] == pytest.approx(15552.0, abs=1e-6) and r["faces"] == 11
    assert r["names"] == [f"sh.inner[{k}]" for k in range(5)]
    assert r["assumed"]["direction"] == "in"
    doc = _box(40, 40, 20)
    r = doc.apply(
        {
            "op": "create",
            "kind": "draft",
            "name": "d",
            "props": {
                "faces": "b:faces(not(normal=+Z), not(normal=-Z))",
                "angle": 3,
                "neutral": "b.start",
            },
        }
    )
    assert r["resolved"]["b:faces(not(normal=+Z), not(normal=-Z))"] == 4
    top = 40 + 2 * 20 * math.tan(math.radians(3))
    frustum = 20 / 3 * (1600 + top * top + math.sqrt(1600 * top * top))
    assert r["volume_mm3"] == pytest.approx(frustum, abs=5e-4)
    assert r["assumed"]["pull"] == "the neutral plane's normal"


def test_draft_on_a_sphere_refuses_naming_the_type() -> None:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "ball"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {
                "plane": "XY",
                "entities": [
                    {"point": "c", "at": [0, 0], "fixed": True},
                    {"point": "a", "at": [0, -10], "fixed": True},
                    {"point": "b", "at": [0, 10], "fixed": True},
                    {"arc": "arc", "center": "c", "start": "b", "end": "a", "ccw": False},
                    {"line": "l", "a": "a", "b": "b"},
                ],
            },
        }
    )
    r = doc.apply(
        {"op": "create", "kind": "revolve", "name": "ball", "props": {"sketch": "s", "axis": "Y"}}
    )
    assert r["volume_mm3"] == pytest.approx(4 / 3 * math.pi * 1000, abs=5e-4)
    with pytest.raises(CommandError, match="it is a sphere") as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "draft",
                "props": {"faces": "ball:faces(type=sphere)", "angle": 3, "neutral": "XY"},
            }
        )
    assert excinfo.value.code == "pk_plane_mismatch"


def test_taper_both_semantics_and_direction_both() -> None:
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "raw",
            "props": {"sketch": "s", "distance": 10, "taper": 3, "height": "along_wall"},
        }
    )
    assert r["volume_mm3"] == pytest.approx(59085.191, abs=5e-4) and r["faces"] == 6
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [100, 60], "tag": "r"}]},
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "v",
            "props": {"sketch": "s", "distance": 10, "taper": 3},
        }
    )
    assert r["volume_mm3"] == pytest.approx(59165.138, abs=5e-4) and r["bbox_max"][2] == 10.0
    assert r["assumed"]["height"].startswith("vertical")
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": [{"rect": [10, 10], "tag": "r"}]},
        }
    )
    r = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "sym",
            "props": {"sketch": "s", "distance": 10, "direction": "both"},
        }
    )
    assert r["bbox_min"][2] == -5.0 and r["bbox_max"][2] == 5.0
    assert r["bbox_mm"] == [10.0, 10.0, 10.0]


def test_split_combine_and_datums() -> None:
    doc = _box(40, 40, 20)
    r = doc.apply(
        {"op": "create", "kind": "split", "name": "sp", "props": {"plane": "x=25", "keep": "+"}}
    )
    assert (
        r["volume_mm3"] == pytest.approx(15 * 40 * 20, abs=1e-6)
        and r["solids"] == 1
        and r["pieces"] == 2
    )
    assert r["names"] == ["sp.cap[0]"]
    doc = _box(40, 40, 20)
    r = doc.apply({"op": "create", "kind": "split", "name": "sp", "props": {"plane": "x=25"}})
    assert r["solids"] == 2 and r["assumed"]["keep"] == "both"
    doc = Document()
    for c in [
        {"op": "create", "kind": "part", "name": "a"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "s0",
            "props": {"plane": "XY", "profile": [{"rect": [20, 20], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "b",
            "props": {"sketch": "s0", "distance": 20, "part": "a"},
        },
        {"op": "create", "kind": "part", "name": "c"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "s1",
            "props": {"plane": "XY", "profile": [{"rect": [20, 20], "at": [19, 0], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "b2",
            "props": {"sketch": "s1", "distance": 20, "part": "c"},
        },
    ]:
        doc.apply(c)
    r = doc.apply(
        {
            "op": "create",
            "kind": "combine",
            "name": "cb",
            "props": {"bodies": ["a", "c"], "mode": "intersect"},
        }
    )
    assert r["volume_mm3"] == pytest.approx(400.0, abs=5e-4)
    assert doc.parts["a"].summary()["com_mm"] == [19.5, 10.0, 10.0]
    assert doc.parts["c"].consumed_by == "a" and r["assumed"]["keep_tool"] is False
    assert doc.dependents_of("part:c") == ["feat:cb"]
    with pytest.raises(CommandError, match="consumed") as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "hole",
                "props": {"on": "b2.end", "at": [[25, 10]], "dia": 2, "part": "c"},
            }
        )
    assert excinfo.value.code == "pk_needs"
    # datums: an axis from a cylindrical face, a point on a face, a midplane
    f1 = build(F1())
    ax = f1.apply({"op": "create", "kind": "axis", "name": "bore", "props": {"of": "hole1.1.wall"}})
    assert ax["origin"][:2] == [50.0, 30.0] and [abs(c) for c in ax["direction"]] == [0.0, 0.0, 1.0]
    pt = f1.apply(
        {
            "op": "create",
            "kind": "point",
            "name": "corner",
            "props": {"on": "plate.end", "at": [10, 10]},
        }
    )
    assert pt["origin"] == [10.0, 10.0, 10.0]
    mid = f1.apply(
        {
            "op": "create",
            "kind": "plane",
            "name": "mid",
            "props": {"midplane": ["plate.start", "plate.end"]},
        }
    )
    assert mid["origin"] == [50.0, 30.0, 5.0]
    sk = f1.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "on_face",
            "props": {"plane": "on:plate.end", "origin": "centroid", "profile": [{"circle": 4}]},
        }
    )
    assert sk["frame"] == "on:plate.end@centroid"
    r = f1.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "boss",
            "props": {"sketch": "on_face", "distance": 5},
        }
    )
    assert r["frame"]["origin"] == [50.0, 30.0, 10.0]
    assert r["delta_mm3"] == pytest.approx(math.pi * 4 * 5, abs=5e-4)  # circle: 4 is the DIAMETER


# -- the deliberate failures: one CommandError each, naming the feature and the fix -------------


FAILURES: list[tuple[dict[str, Any], str, str]] = [
    (
        {"op": "create", "kind": "extrude", "name": "e", "props": {"sketch": "base"}},
        "pk_needs",
        "distance",
    ),
    (
        {
            "op": "create",
            "kind": "extrude",
            "name": "e",
            "props": {"sketch": "nope", "distance": 1},
        },
        "pk_ref_unknown",
        "sk:base",
    ),
    (
        {
            "op": "create",
            "kind": "extrude",
            "name": "e",
            "props": {"sketch": "base", "distance": "12 furlongs"},
        },
        "pk_unit_unknown",
        "Accepted length units",
    ),
    (
        {
            "op": "create",
            "kind": "extrude",
            "name": "e",
            "props": {"sketch": "base", "distance": 5, "mode": "new"},
        },
        "pk_needs",
        "already has a body",
    ),
    (
        {
            "op": "create",
            "kind": "extrude",
            "name": "e",
            "props": {"sketch": "base", "distance": "through"},
        },
        "pk_needs",
        "cut or intersect",
    ),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "h2",
            "props": {"on": "plate.nowhere", "at": [[1, 1]], "dia": 2},
        },
        "pk_ref_unknown",
        "Face names",
    ),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "h2",
            "props": {"on": "plate:faces(normal=+Z)", "at": [[1, 1]]},
        },
        "pk_needs",
        "dia",
    ),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "h2",
            "props": {"on": "plate.end", "at": [[1, 1]], "dia": 2, "std": "M6 tap"},
        },
        "pk_spec_conflict",
        "not both",
    ),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "h2",
            "props": {"on": "plate.end", "at": [[1, 1]], "std": "M6 welded"},
        },
        "pk_needs",
        "clearance",
    ),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "h2",
            "props": {"on": "plate:faces(type=plane)", "at": [[1, 1]], "dia": 2},
        },
        "pk_ref_ambiguous",
        "exactly one face",
    ),
    (
        {
            "op": "create",
            "kind": "fillet",
            "name": "f",
            "props": {"edges": "plate:edges(dir=Z, len>500)", "r": 1},
        },
        "pk_ref_empty",
        "none after len>500",
    ),
    (
        {"op": "create", "kind": "shell", "name": "s", "props": {"faces": "plate.end"}},
        "pk_needs",
        "t",
    ),
    (
        {"op": "create", "kind": "pattern", "name": "p", "props": {"of": "hole1", "nx": 3}},
        "pk_needs",
        "dx",
    ),
    (
        {
            "op": "create",
            "kind": "mirror",
            "name": "m",
            "props": {"of": "hole1", "plane": "plane:missing"},
        },
        "pk_ref_unknown",
        "Datums",
    ),
    (
        {"op": "create", "kind": "split", "name": "s", "props": {"plane": "x=500"}},
        "pk_no_effect",
        "does not cut",
    ),
    ({"op": "set", "id": "feat:ghost", "props": {"dia": 1}}, "pk_ref_unknown", "Settable ids"),
    ({"op": "create", "kind": "plane", "name": "p", "props": {}}, "pk_needs", "offset"),
    (
        {
            "op": "create",
            "kind": "hole",
            "name": "plate",
            "props": {"on": "plate.end", "at": [[1, 1]], "dia": 2},
        },
        "pk_ref_ambiguous",
        "already exists",
    ),
]


@pytest.mark.parametrize(
    "command,code,fix",
    FAILURES,
    ids=[f"{c['op']}-{c.get('kind', '')}-{code}" for c, code, _ in FAILURES],
)
def test_deliberate_failures_are_one_command_error_naming_feature_and_fix(
    command: dict[str, Any], code: str, fix: str
) -> None:
    doc = build(F1())
    before = doc.fingerprint()
    with pytest.raises(CommandError) as excinfo:
        doc.apply(command)
    assert excinfo.value.code == code, str(excinfo.value)
    message = str(excinfo.value)
    assert fix in message, message
    assert "Traceback" not in message and len(message) < 700
    assert doc.fingerprint() == before
    assert len(doc.history) == len(F1())


# -- the defects the A66 audit found ------------------------------------------------------------


def test_set_refuses_an_unknown_prop_and_names_the_real_one() -> None:
    """A typo'd prop used to be stored, regenerate nothing and report success.

    D8: a no-op that says it worked is the worst refusal of all. `diameter`
    is not a hole prop - `dia` is - so `set` refuses and names the settable
    props of that kind.
    """
    doc = build(F1())
    before = doc.fingerprint()
    with pytest.raises(CommandError) as excinfo:
        doc.apply({"op": "set", "id": "feat:hole1", "props": {"diameter": 12}})
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_bad_op"
    assert "diameter" in message and "dia" in message
    assert doc.fingerprint() == before
    assert "diameter" not in doc.parts["plate"].feature("hole1").args
    # a real prop still works, and so do the two meta props
    assert doc.apply({"op": "set", "id": "feat:hole1", "props": {"dia": 12}})["props"] == [
        {"key": "dia", "old": 10, "new": 12}
    ]
    assert doc.apply({"op": "set", "id": "feat:hole1", "props": {"suppressed": True}})["props"] == [
        {"key": "suppressed", "old": False, "new": True}
    ]
    # nothing is written when one prop of a batch is wrong
    with pytest.raises(CommandError):
        doc.apply({"op": "set", "id": "feat:hole1", "props": {"dia": 14, "diameter": 14}})
    assert doc.parts["plate"].feature("hole1").args["dia"] == 12


def test_hole_counts_the_holes_that_were_actually_cut() -> None:
    """`count` used to be `len(at)`: a tool that missed the body was silent.

    Law 11's sibling - a feature reports what it DID, not what it was asked
    for. One point on the face and one 500 mm off it makes exactly one hole.
    """
    doc = build(F1()[:3])
    r = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "plate.end", "at": [[50, 30], [500, 30]], "dia": 10},
        }
    )
    assert r["count"] == 1 and r["requested"] == 2 and r["missed"] == 1
    assert r["names"] == ["h.1.wall"]
    assert any("500" in n and "cut nothing" in n for n in r["notes"]), r["notes"]
    assert r["delta_mm3"] == pytest.approx(-math.pi * 25 * 10, abs=5e-4)


def test_a_hole_where_every_point_misses_refuses_rather_than_reporting_it_cut() -> None:
    doc = build(F1()[:3])
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "hole",
                "name": "h",
                "props": {"on": "plate.end", "at": [[500, 30], [600, 30]], "dia": 10},
            }
        )
    assert excinfo.value.code == "pk_no_effect"
    r = doc.apply(
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {
                "on": "plate.end",
                "at": [[500, 30], [600, 30]],
                "dia": 10,
                "allow_no_effect": True,
            },
        }
    )
    assert r["count"] == 0 and r["requested"] == 2 and r["missed"] == 2
    assert any("cut nothing" in n for n in r["notes"]), r["notes"]
