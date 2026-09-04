"""L1 acceptance: the coil (a true helical sweep) and the MODELLED thread.

Every number here is arithmetic, not a golden file. The coil is pinned
against the helix length `sqrt((pi*D)^2 + p^2) * turns` and the torus
approximation `A * L` (Pappus on the wire's own section); the modelled
thread against ISO 68-1's basic profile - minor `d1 = d - 1.0825 P` and the
volume of a core cylinder plus the swept thread material. The cosmetic
thread is pinned the other way round: Law 18 says it moves NOTHING, so the
part fingerprint must be bit-identical with and without it.
"""

from __future__ import annotations

import math
import time
from typing import Any

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from test_document_parts import build

pytestmark = pytest.mark.brep

# The acceptance spring: wire d2, mean coil d20, pitch 5, 6 turns, about Z.
WIRE_D, COIL_D, PITCH, TURNS = 2.0, 20.0, 5.0, 6.0
HELIX_MM = math.sqrt((math.pi * COIL_D) ** 2 + PITCH**2) * TURNS
TORUS_MM3 = math.pi * (WIRE_D / 2.0) ** 2 * HELIX_MM

# ISO 68-1 / ISO 261 for M6 x 1.
M6_P = 1.0
M6_MINOR = 6.0 - 1.25 * (math.sqrt(3.0) / 2.0) * M6_P  # 4.917 468 mm


def spring(section: str | None = None, **props: Any) -> list[dict[str, Any]]:
    return [
        {"op": "create", "kind": "part", "name": "spring"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "wire",
            "plane": "XZ",
            "profile": [{"circle": WIRE_D, "at": [COIL_D / 2.0, 0], "tag": "w"}],
        },
        {
            "op": "create",
            "kind": "coil",
            "name": "c",
            "profile": "wire",
            "axis": [[0, 0, 0], [0, 0, 1]],
            "pitch": PITCH,
            "turns": TURNS,
            **({"section": section} if section else {}),
            **props,
        },
    ]


def stud(length: float = 12.0) -> list[dict[str, Any]]:
    return [
        {"op": "create", "kind": "part", "name": "stud"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "plane": "XY",
            "profile": [{"circle": 6, "tag": "o"}],
        },
        {"op": "create", "kind": "extrude", "name": "shaft", "sketch": "s", "distance": length},
    ]


def details(doc: Document, fid: str) -> dict[str, Any]:
    part = doc.parts[next(iter(doc.parts))]
    return next(f.details() for f in part.features if f.id == fid)


# -- the coil ---------------------------------------------------------------------------------


def test_coil_spring_is_a_valid_solid_matching_the_torus_arithmetic() -> None:
    from partkiln.brep import shapes

    doc = build(spring())
    part = doc.parts["spring"]
    d = details(doc, "c")
    # The helix's own length against sqrt((pi*D)^2 + p^2) * turns. The 1e-3 mm
    # band is GCPnts_AbscissaPoint's integration (measured: 1.5e-5 mm), not
    # slack in the curve.
    assert d["helix_mm"] == pytest.approx(HELIX_MM, abs=1e-3)
    # Volume against the torus approximation A * L. Measured relative error
    # -4.0e-7, so 1e-5 relative is a real pin, not a rubber band.
    assert d["volume_mm3"] == pytest.approx(TORUS_MM3, rel=1e-5)
    assert d["solids"] == 1 and d["radius_mm"] == 10.0 and d["turns"] == 6.0
    assert d["height_mm"] == 30.0 and d["hand"] == "right"
    assert shapes.is_valid(part.shape)
    from OCP.BRepCheck import BRepCheck_Analyzer

    assert BRepCheck_Analyzer(part.shape).IsValid()
    assert set(part.inventory().face_names) >= {"c.side.w", "c.cap.a", "c.cap.b"}


def test_coil_section_axial_sweeps_pappus_on_the_horizontal_travel() -> None:
    """`section: axial` keeps the profile in the plane it was drawn in, so the
    volume is A * (pi*D) * turns - 0.3 % under the wire reading, and the diff
    says which rule it used every time (Law 19)."""
    doc = build(spring(section="axial"))
    d = details(doc, "c")
    assert d["volume_mm3"] == pytest.approx(
        math.pi * (WIRE_D / 2.0) ** 2 * math.pi * COIL_D * TURNS, rel=1e-5
    )
    assert d["section"] == "axial"
    assert d["volume_mm3"] < TORUS_MM3


def test_coil_defaults_are_declared_once() -> None:
    doc = build(spring())
    assumed = details(doc, "c")["assumed"]
    assert assumed["hand"] == "right" and assumed["taper"] == 0
    assert assumed["section"] == "normal"


def test_coil_height_is_turns_times_pitch() -> None:
    cmds = spring()
    cmds[-1].pop("turns")
    cmds[-1]["height"] = TURNS * PITCH
    d = details(build(cmds), "c")
    assert d["turns"] == pytest.approx(TURNS)
    assert d["volume_mm3"] == pytest.approx(TORUS_MM3, rel=1e-5)


def test_left_hand_coil_is_the_same_volume_and_a_different_shape() -> None:
    """A left-hand coil is the mirror image: same wire, same length, opposite
    winding. The B-rep fingerprint canNOT tell them apart - it is sorted face
    areas and centroids, and a helicoid's centroid sits on the axis - so the
    proof is the tessellation, which is what a mirror image really changes."""
    from partkiln.brep import mesh

    right = build(spring())
    left = build(spring(hand="left"))
    assert details(left, "c")["volume_mm3"] == pytest.approx(
        details(right, "c")["volume_mm3"], rel=1e-6
    )
    assert details(left, "c")["helix_mm"] == pytest.approx(details(right, "c")["helix_mm"])
    assert details(left, "c")["hand"] == "left"
    assert mesh.mesh_hash(left.parts["spring"].shape) != mesh.mesh_hash(right.parts["spring"].shape)


@pytest.mark.parametrize("taper", [3.0, -3.0])
def test_tapered_coil_opens_and_closes_the_radius(taper: float) -> None:
    d = details(build(spring(taper=taper)), "c")
    expected_end = 10.0 + TURNS * PITCH * math.tan(math.radians(taper))
    assert d["end_radius_mm"] == pytest.approx(expected_end, abs=1e-3)
    # A cone that OPENS climbs a longer helix than the cylinder; one that
    # closes climbs a shorter one. (The earlier guess that a taper always
    # lengthens the helix was wrong and is pinned here so it stays wrong.)
    assert (d["helix_mm"] > HELIX_MM) is (taper > 0)
    # Still A * L: the sweep is exact on a cone too.
    assert d["volume_mm3"] == pytest.approx(math.pi * (WIRE_D / 2.0) ** 2 * d["helix_mm"], rel=1e-4)


def test_coil_joins_a_body_and_reports_its_own_delta() -> None:
    cmds = spring()
    cmds[-1]["mode"] = "new"
    cmds += [
        {
            "op": "create",
            "kind": "sketch",
            "name": "pad",
            "plane": "XY",
            "profile": [{"rect": [30, 30]}],
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "base",
            "sketch": "pad",
            "distance": 2,
            "direction": "-",
            "mode": "join",
        },
    ]
    doc = build(cmds)
    assert doc.parts["spring"].summary()["solids"] == 1


# -- the coil's refusals ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edit", "code", "needle"),
    [
        ({"pitch": None}, "pk_needs", "pitch"),
        ({"pitch": 0}, "pk_needs", "must be > 0"),
        ({"turns": None}, "pk_needs", "turns"),
        ({"turns": -1}, "pk_needs", "must be > 0"),
        ({"hand": "widdershins"}, "pk_needs", "'right' or 'left'"),
        ({"section": "sideways"}, "pk_needs", "'normal'"),
        ({"taper": 85}, "pk_needs", "taper must be within"),
        ({"taper": -20}, "pk_spec_conflict", "closes the coil radius"),
        ({"height": 30.0}, "pk_spec_conflict", "turns OR height"),
    ],
)
def test_coil_refuses_bad_input_with_a_code_and_a_fix(
    edit: dict[str, Any], code: str, needle: str
) -> None:
    cmds = spring()
    for key, value in edit.items():
        if value is None:
            cmds[-1].pop(key, None)
        else:
            cmds[-1][key] = value
    with pytest.raises(CommandError) as exc:
        build(cmds)
    assert exc.value.code == code
    assert needle in str(exc.value)


def test_coil_refuses_a_profile_on_the_axis() -> None:
    cmds = spring()
    cmds[1]["profile"] = [{"circle": WIRE_D, "at": [0, 0], "tag": "w"}]
    with pytest.raises(CommandError) as exc:
        build(cmds)
    assert exc.value.code == "pk_spec_conflict"
    assert "sits ON the axis" in str(exc.value)


def test_coil_turns_is_unitless_and_never_read_as_millimetres() -> None:
    """`turns: '6mm'` is not a count; Law 12's bare-number rule must not leak."""
    cmds = spring()
    cmds[-1]["turns"] = "6mm"
    with pytest.raises(CommandError) as exc:
        build(cmds)
    assert exc.value.code == "pk_unit_kind"
    assert "turns is a count" in str(exc.value)


# -- the cosmetic thread (Law 18) -------------------------------------------------------------


def test_cosmetic_thread_is_the_default_and_moves_nothing() -> None:
    doc = build(stud())
    before = doc.fingerprint()
    volume = doc.parts["stud"].summary()["volume_mm3"]
    doc.apply({"op": "create", "kind": "thread", "name": "th", "on": "shaft.side.o", "spec": "M6"})
    d = details(doc, "th")
    assert d["modelled"] is False
    assert d["assumed"]["modelled"] is False
    assert d["delta_mm3"] == 0.0
    assert d["cosmetic"]["thread"] == "M6" and d["cosmetic"]["pitch_mm"] == 1.0
    assert d["iso_minor_dia_mm"] == pytest.approx(round(M6_MINOR, 3))
    assert doc.parts["stud"].summary()["volume_mm3"] == volume
    assert doc.fingerprint() == before  # bit-identical: Law 18
    assert any("cosmetic" in n for n in d["notes"])


def test_cosmetic_thread_costs_no_geometry_time() -> None:
    doc = build(stud())
    t = time.perf_counter()
    doc.apply({"op": "create", "kind": "thread", "name": "th", "on": "shaft.side.o", "spec": "M6"})
    assert time.perf_counter() - t < 0.25


# -- the modelled thread ----------------------------------------------------------------------


@pytest.fixture(scope="module")
def modelled_m6() -> Document:
    doc = build(stud())
    doc.apply(
        {
            "op": "create",
            "kind": "thread",
            "name": "tm",
            "on": "shaft.side.o",
            "spec": "M6",
            "modelled": True,
        }
    )
    return doc


def test_modelled_m6_is_a_valid_solid_smaller_than_the_plain_shaft(modelled_m6: Document) -> None:
    from OCP.BRepCheck import BRepCheck_Analyzer

    from partkiln.brep import shapes

    part = modelled_m6.parts["stud"]
    d = details(modelled_m6, "tm")
    plain = math.pi * 3.0**2 * 12.0
    assert d["modelled"] is True
    assert d["solids"] == 1
    assert shapes.is_valid(part.shape) and BRepCheck_Analyzer(part.shape).IsValid()
    assert d["volume_mm3"] < plain
    assert d["delta_mm3"] < 0
    # The arithmetic: a core cylinder at the minor plus the swept ISO 68-1
    # thread material (3P/4 wide at the minor, P/8 at the major), by Pappus on
    # the horizontal travel. Measured relative error +8.6e-5 (the partial
    # threads at the two ends), so the band is 1e-3 relative.
    r_minor, r_major = M6_MINOR / 2.0, 3.0
    a = (3 * M6_P / 4 + M6_P / 8) / 2 * (r_major - r_minor)
    r_bar = r_minor + (r_major - r_minor) * (3 * M6_P / 4 + 2 * (M6_P / 8)) / (
        3 * (3 * M6_P / 4 + M6_P / 8)
    )
    expected = math.pi * r_minor**2 * 12.0 + 2 * math.pi * r_bar * a * (12.0 / M6_P)
    assert d["volume_mm3"] == pytest.approx(expected, rel=1e-3)


def test_modelled_m6_measures_the_iso_minor_diameter(modelled_m6: Document) -> None:
    d = details(modelled_m6, "tm")
    assert d["measured_minor_dia_mm"] == pytest.approx(M6_MINOR, abs=1e-3)
    assert d["iso_minor_dia_mm"] == pytest.approx(round(M6_MINOR, 3))
    assert d["pitch_mm"] == 1.0 and d["turns"] == 12.0


def test_modelled_thread_names_its_root_crest_and_flanks(modelled_m6: Document) -> None:
    names = set(modelled_m6.parts["stud"].inventory().face_names)
    assert any(n.startswith("tm.root[") for n in names)
    assert any(n.startswith("tm.crest[") for n in names)
    assert any(n.startswith("tm.flank[") for n in names)


def test_modelled_thread_is_not_reported_as_cosmetic(modelled_m6: Document) -> None:
    """A thread that moved 63.8 mm3 must not sit in the field that means
    'annotation only' - `checks/spec.py` reads it to skip cosmetic threads."""
    assert "cosmetic" not in details(modelled_m6, "tm")


def test_modelled_thread_does_not_multiply_faces(modelled_m6: Document) -> None:
    """A helicoid is ONE face however many turns it makes: 12 turns of M6 add
    22 - 3 = 19 faces, not 12 x anything. The cost of a modelled thread is
    time, not topology, and this pins the claim."""
    assert details(modelled_m6, "tm")["faces"] < 40


def test_modelled_thread_changes_the_fingerprint() -> None:
    plain = build(stud())
    before = plain.fingerprint()
    plain.apply(
        {
            "op": "create",
            "kind": "thread",
            "name": "tm",
            "on": "shaft.side.o",
            "spec": "M6",
            "modelled": True,
        }
    )
    assert plain.fingerprint() != before


def test_modelled_left_hand_thread_matches_the_right_hand_volume() -> None:
    doc = build(stud())
    doc.apply(
        {
            "op": "create",
            "kind": "thread",
            "name": "tm",
            "on": "shaft.side.o",
            "spec": "M6",
            "modelled": True,
            "hand": "left",
        }
    )
    d = details(doc, "tm")
    assert d["hand"] == "left"
    assert d["measured_minor_dia_mm"] == pytest.approx(M6_MINOR, abs=1e-3)
    assert d["solids"] == 1


def test_modelled_internal_thread_bores_to_the_major_diameter() -> None:
    doc = build(
        [
            {"op": "create", "kind": "part", "name": "nut"},
            {
                "op": "create",
                "kind": "sketch",
                "name": "s",
                "plane": "XY",
                "profile": [{"circle": 14}],
            },
            {"op": "create", "kind": "extrude", "name": "blank", "sketch": "s", "distance": 8},
            {
                "op": "create",
                "kind": "hole",
                "name": "h",
                "on": "blank.end",
                "at": [[0, 0]],
                "std": "M6 tap",
            },
        ]
    )
    doc.apply(
        {
            "op": "create",
            "kind": "thread",
            "name": "tm",
            "on": "h.1.wall",
            "spec": "M6",
            "modelled": True,
        }
    )
    d = details(doc, "tm")
    assert d["internal"] is True and d["solids"] == 1
    assert d["measured_major_dia_mm"] == pytest.approx(6.0, abs=1e-3)
    # Tapping removes the crest material the tap drill left: a tapped hole
    # holds LESS metal than the drilled blank did.
    assert d["delta_mm3"] < 0


# -- the modelled thread's cost, declared -----------------------------------------------------


def test_modelled_thread_wall_time_is_measured_and_bounded() -> None:
    """Measured on this machine (M5 Max, OCP 7.9.3): M6x1 over 12 mm takes
    about 0.65-0.85 s against the 13-17 ms every other feature costs, and it
    scales at roughly 65 ms per turn. The bound is deliberately loose - the
    point is the ORDER of magnitude, which is why MAX_TURNS exists."""
    doc = build(stud())
    t = time.perf_counter()
    doc.apply(
        {
            "op": "create",
            "kind": "thread",
            "name": "tm",
            "on": "shaft.side.o",
            "spec": "M6",
            "modelled": True,
        }
    )
    assert time.perf_counter() - t < 8.0


def test_modelled_thread_refuses_more_turns_than_it_can_afford() -> None:
    from partkiln.features import thread as thread_mod

    doc = build(stud(length=300.0))
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "thread",
                "name": "tm",
                "on": "shaft.side.o",
                "spec": "M6",
                "modelled": True,
            }
        )
    assert exc.value.code == "pk_too_long"
    assert "job: true" in str(exc.value)
    assert f"{thread_mod.MAX_TURNS:g} turns" in str(exc.value)


# -- the thread's refusals --------------------------------------------------------------------


def test_thread_refuses_a_planar_face() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply({"op": "create", "kind": "thread", "name": "t", "on": "shaft.end", "spec": "M6"})
    assert exc.value.code == "pk_plane_mismatch"
    assert "cylindrical face" in str(exc.value)


def test_thread_refuses_a_spec_that_contradicts_the_shaft() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {"op": "create", "kind": "thread", "name": "t", "on": "shaft.side.o", "spec": "M20"}
        )
    assert exc.value.code == "pk_spec_conflict"
    assert "6.0 mm across" in str(exc.value)


def test_thread_refuses_a_length_longer_than_the_face() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "thread",
                "name": "t",
                "on": "shaft.side.o",
                "spec": "M6",
                "length": 40,
            }
        )
    assert exc.value.code == "pk_spec_conflict"
    assert "12.0 mm long" in str(exc.value)


def test_thread_refuses_without_a_spec() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply({"op": "create", "kind": "thread", "name": "t", "on": "shaft.side.o"})
    assert exc.value.code == "pk_needs" and "spec" in str(exc.value)


def test_thread_refuses_an_unknown_designation() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {"op": "create", "kind": "thread", "name": "t", "on": "shaft.side.o", "spec": "M6x9"}
        )
    # The refusal names the pitches ISO 261 actually tables for M6 (rule 6:
    # one short message with the exact fix), not just "no".
    assert "Tabled pitches" in str(exc.value) and "0.75" in str(exc.value)


def test_thread_refuses_a_bad_hand() -> None:
    doc = build(stud())
    with pytest.raises(CommandError) as exc:
        doc.apply(
            {
                "op": "create",
                "kind": "thread",
                "name": "t",
                "on": "shaft.side.o",
                "spec": "M6",
                "hand": "clockwise",
            }
        )
    assert exc.value.code == "pk_needs" and "'right' or 'left'" in str(exc.value)


# -- the vocabulary ---------------------------------------------------------------------------


def test_coil_and_thread_are_documented_verbs() -> None:
    from partkiln.client import LocalKernel

    out = LocalKernel().call("verbs", {})
    for kind, required in (("coil", "pitch"), ("thread", "spec")):
        assert out["kinds"][kind].get("documented") is not False
        assert required in out["kinds"][kind]["required"]
