"""A66 defect B: closed profiles that OVERLAP in one sketch.

The defect: `nest_loops` knew only "disjoint" and "nested" and decided which
by sampling ONE point per loop into a chord polygon, so loops whose
boundaries cross were classified at random. A dumbbell - two circles joined
by a bar, drawn as three closed profiles - cut exactly ONE circle out of a
plate, with no refusal and no note, and left a solid whose interior far from
the cut classified OUT. These tests pin the correct volume (derived
analytically here, not copied from the kernel), the declaration that says
what was assumed, and the three neighbouring readings that must NOT change:
nested, disjoint, and merely touching.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from partkiln.document import Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.sketch.profile import NAMED_FRAMES, build_profile

pytestmark = pytest.mark.brep

# The dumbbell: circles d8 at (40, 40) and (80, 40), a 40 x 4 bar between the
# two centres. Each circle meets the bar in a lens = the part of a disc r4
# inside the strip |y| <= 2:  2 * integral(0..2) sqrt(16 - y^2) dy
#                           = 2 * (2 * sqrt(12) / 2 + 8 * asin(1/2)).
LENS = 2.0 * (math.sqrt(12.0) + 8.0 * math.asin(0.5))
DUMBBELL_MM2 = 2.0 * math.pi * 16.0 + 40.0 * 4.0 - 2.0 * LENS  # 229.9194 mm2
DUMBBELL = [
    {"circle": 8, "at": [40, 40], "tag": "c1"},
    {"circle": 8, "at": [80, 40], "tag": "c2"},
    {"rect": [40, 4], "at": [40, 38], "tag": "bar"},
]


def _profile(profile: list[dict[str, Any]], plane: str = "XY") -> Any:
    doc = Document()
    props = {"plane": plane, "profile": profile}
    doc.apply({"op": "create", "kind": "sketch", "name": "s", "props": props})
    return build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])


def _occt_area(profile: Any) -> float:
    from partkiln.brep import shapes

    return sum(shapes.area(f) for f in profile.faces)


def _plate_with(profile: list[dict[str, Any]]) -> tuple[Document, dict[str, Any]]:
    """A 120 x 80 x 10 plate, then `profile` cut through it from its top face."""
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "plate"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [120, 80], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": 10},
        },
        {
            "op": "create",
            "kind": "sketch",
            "name": "db",
            "props": {"plane": "on:plate.end", "profile": profile},
        },
    ):
        doc.apply(op)
    result = doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "cut1",
            "props": {"sketch": "db", "distance": "through", "mode": "cut"},
        }
    )
    return doc, result


# -- the defect --------------------------------------------------------------------------------


def test_a_dumbbell_cuts_its_whole_union_and_declares_it() -> None:
    doc, result = _plate_with(DUMBBELL)
    assert pytest.approx(229.91940, abs=1e-5) == DUMBBELL_MM2
    assert result["delta_mm3"] == pytest.approx(-DUMBBELL_MM2 * 10.0, abs=5e-4)
    # Law 19: the union is a default, so it is echoed once, naming the loops.
    note = result["assumed"]["overlap"]
    assert note == "3 overlapping loops (bar.0, c1, c2) unioned into 1 region"
    assert doc.parts["plate"].summary()["volume_mm3"] == pytest.approx(
        120 * 80 * 10 - DUMBBELL_MM2 * 10.0, abs=5e-4
    )


def test_the_cut_solid_is_valid_and_its_interior_classifies_inside() -> None:
    """BRepCheck_Analyzer alone missed the defect - it called the corrupt
    solid valid. The classifier is what caught it, so both are pinned."""
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.gp import gp_Pnt
    from OCP.TopAbs import TopAbs_State

    doc, _ = _plate_with(DUMBBELL)
    shape = doc.parts["plate"].shape
    assert BRepCheck_Analyzer(shape).IsValid()
    for point, state in (
        ((10.0, 10.0, 5.0), TopAbs_State.TopAbs_IN),  # deep in the plate, far from the cut
        ((110.0, 70.0, 5.0), TopAbs_State.TopAbs_IN),  # the far corner
        ((60.0, 40.0, 5.0), TopAbs_State.TopAbs_OUT),  # inside the bar of the dumbbell
        ((40.0, 40.0, 5.0), TopAbs_State.TopAbs_OUT),  # inside the left bulb
        ((80.0, 40.0, 5.0), TopAbs_State.TopAbs_OUT),  # inside the right bulb
    ):
        classifier = BRepClass3d_SolidClassifier(shape)
        classifier.Perform(gp_Pnt(*point), 1e-7)
        assert classifier.State() == state, point


def test_the_union_is_one_face_of_the_analytic_area() -> None:
    p = _profile(DUMBBELL)
    assert len(p.faces) == 1 and p.loops == 3
    assert p.area_mm2 == pytest.approx(DUMBBELL_MM2, abs=5e-4)
    assert _occt_area(p) == pytest.approx(DUMBBELL_MM2, abs=1e-6)
    # The bar's end walls are interior to the union and no longer exist, so
    # they name nothing; the sides that survived still carry their tags.
    assert sorted({t for t, _ in p.edges}) == ["bar.0", "bar.2", "c1", "c2"]


def test_a_crossing_region_still_takes_a_nested_loop_as_a_hole() -> None:
    hole = {"circle": 2, "at": [38, 40], "tag": "h"}  # inside the left bulb, clear of the bar
    p = _profile([*DUMBBELL, hole])
    assert len(p.faces) == 1 and p.loops == 4
    assert _occt_area(p) == pytest.approx(DUMBBELL_MM2 - math.pi, abs=1e-6)
    assert "h" in {t for t, _ in p.edges}
    assert p.assumed["overlap"].endswith("unioned into 1 region")


def test_two_separate_overlapping_pairs_become_two_regions() -> None:
    p = _profile(
        [
            {"rect": [20, 20], "at": [0, 0], "tag": "a"},
            {"rect": [20, 20], "at": [10, 10], "tag": "b"},
            {"rect": [20, 20], "at": [100, 0], "tag": "c"},
            {"rect": [20, 20], "at": [110, 10], "tag": "d"},
        ]
    )
    assert len(p.faces) == 2
    assert _occt_area(p) == pytest.approx(2 * (2 * 400 - 100), abs=1e-9)
    assert p.assumed["overlap"] == "4 overlapping loops (a.0, b.0, c.0, d.0) unioned into 2 regions"


def test_the_same_profile_drawn_twice_is_one_region() -> None:
    twice = [{"circle": 20, "at": [0, 0], "tag": "a"}, {"circle": 20, "at": [0, 0], "tag": "b"}]
    p = _profile(twice)
    assert len(p.faces) == 1
    assert _occt_area(p) == pytest.approx(math.pi * 100, abs=1e-9)
    assert p.assumed["overlap"] == "2 overlapping loops (a, b) unioned into 1 region"


def test_a_revolve_declares_the_union_too() -> None:
    doc = Document()
    for op in (
        {"op": "create", "kind": "part", "name": "p"},
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {
                "plane": "XZ",
                "profile": [
                    {"rect": [10, 10], "at": [20, 0], "tag": "a"},
                    {"rect": [10, 10], "at": [25, 5], "tag": "b"},
                ],
            },
        },
    ):
        doc.apply(op)
    result = doc.apply(
        {
            "op": "create",
            "kind": "revolve",
            "name": "r",
            "props": {"sketch": "s", "axis": "Z"},
        }
    )
    assert result["assumed"]["overlap"] == "2 overlapping loops (a.0, b.0) unioned into 1 region"


# -- the readings that must NOT change -----------------------------------------------------------


def test_a_nested_ring_is_unchanged() -> None:
    ring = [{"circle": 80, "at": [0, 0], "tag": "o"}, {"circle": 10, "at": [0, 0], "tag": "i"}]
    p = _profile(ring)
    assert len(p.faces) == 1 and p.loops == 2 and p.assumed == {}
    assert _occt_area(p) == pytest.approx(math.pi * (1600 - 25), abs=1e-6)


def test_two_disjoint_rectangles_are_still_two_faces() -> None:
    p = _profile([{"rect": [10, 10], "tag": "a"}, {"rect": [10, 10], "at": [30, 0], "tag": "b"}])
    assert len(p.faces) == 2 and p.area_mm2 == 200.0 and p.assumed == {}


@pytest.mark.parametrize(
    ("what", "profile", "area"),
    [
        (
            "rectangles touching at one corner",
            [{"rect": [10, 10], "tag": "a"}, {"rect": [10, 10], "at": [10, 10], "tag": "b"}],
            200.0,
        ),
        (
            "rectangles sharing a whole edge",
            [{"rect": [10, 10], "tag": "a"}, {"rect": [10, 10], "at": [10, 0], "tag": "b"}],
            200.0,
        ),
        (
            "circles tangent from outside",
            [{"circle": 20, "at": [0, 0], "tag": "a"}, {"circle": 20, "at": [20, 0], "tag": "b"}],
            2 * math.pi * 100,
        ),
    ],
)
def test_loops_that_only_touch_are_not_crossing(
    what: str, profile: list[dict[str, Any]], area: float
) -> None:
    """Their boundaries MEET, so the cheap "do they touch" test is not enough;
    the area they share is zero, which is what says they only touch."""
    p = _profile(profile)
    assert len(p.faces) == 2, what
    assert p.assumed == {}, what
    assert _occt_area(p) == pytest.approx(area, abs=1e-6), what


# -- nesting is measured now, not sampled --------------------------------------------------------


def test_a_hole_tangent_to_its_outer_wire_is_still_a_hole() -> None:
    """Measured on the old code: the inner circle's sampled point landed
    exactly ON the outer circle, `_inside` answered "outside" (it tests
    `< radius`), and the hole silently vanished into a second face."""
    ring = [{"circle": 80, "at": [0, 0], "tag": "o"}, {"circle": 20, "at": [30, 0], "tag": "i"}]
    p = _profile(ring)
    assert len(p.faces) == 1 and p.assumed == {}
    assert _occt_area(p) == pytest.approx(math.pi * (1600 - 100), abs=1e-6)


def test_a_hole_in_an_arc_bulge_is_a_hole_not_a_second_face() -> None:
    """A slot's chord polygon is the 30 x 10 rectangle between its tangent
    points; a circle in the rounded cap is outside THAT and inside the slot.
    The old point-in-chord-polygon test called it a separate face."""
    p = _profile(
        [{"slot": [40, 10], "at": [0, 0], "tag": "s"}, {"circle": 4, "at": [17, 0], "tag": "h"}]
    )
    assert len(p.faces) == 1 and p.assumed == {}
    assert _occt_area(p) == pytest.approx(30 * 10 + math.pi * 25 - math.pi * 4, abs=1e-6)


def test_an_arc_crosses_by_its_bulge_not_its_chord() -> None:
    """The same geometry moved out: the circle now straddles the cap's arc, so
    it CROSSES it - a crossing the chord polygon cannot see either."""
    p = _profile(
        [{"slot": [40, 10], "at": [0, 0], "tag": "s"}, {"circle": 4, "at": [20, 0], "tag": "c"}]
    )
    assert len(p.faces) == 1
    assert p.assumed["overlap"] == "2 overlapping loops (c, s.0) unioned into 1 region"
    assert _occt_area(p) > 30 * 10 + math.pi * 25
