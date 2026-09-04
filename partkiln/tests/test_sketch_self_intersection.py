"""A loop that crosses ITSELF is closed, so nothing upstream refuses it.

Found by the A66 verify pass, adversarially, and present on HEAD as well as on
defect B's fix - defect B was about a *pair* of loops overlapping, and a
bowtie is one loop. `sketch.closed()` passes; `BRepBuilderAPI_MakeFace`
succeeds; and the face OCCT hands back has the SIGNED sum of the lobes for its
area, so the numbers below were what the kernel answered, in silence:

    symmetric bowtie   drawn 200 mm2   answered 0 mm2, `create extrude` -> status ok, volume 0.0
    asymmetric bowtie  drawn 166.667   answered 100.0

The area arithmetic here is derived from the polygons, not read back from the
kernel. `ShapeAnalysis_Wire.CheckSelfIntersection` is the detector: measured
False on rect, circle, hexagon, L-poly, the dumbbell and a tangent-arc slot,
whose two arcs meet their lines tangentially and are the obvious false
positive.
"""

from __future__ import annotations

from typing import Any

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.sketch.profile import NAMED_FRAMES, build_profile

pytestmark = pytest.mark.brep

# (0,0) -> (20,20) -> (20,0) -> (0,20): the diagonals cross at (10, 10).
# Lobes 100 + 100 = 200 mm2 drawn; shoelace signed area 0.
BOWTIE = [{"poly": [[0, 0], [20, 20], [20, 0], [0, 20]], "tag": "bt"}]
# (0,0) -> (20,20) -> (20,0) -> (0,10): y=x meets y=10-x/2 at (20/3, 20/3).
# Lobes 100/3 + 400/3 = 500/3 = 166.667 mm2 drawn; shoelace signed area -100.
ASYMMETRIC = [{"poly": [[0, 0], [20, 20], [20, 0], [0, 10]], "tag": "bt"}]


def _profile(profile: list[dict[str, Any]]) -> Any:
    doc = Document()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": profile},
        }
    )
    return build_profile(doc.sketches["s"], NAMED_FRAMES["XY"])


@pytest.mark.parametrize("profile", [BOWTIE, ASYMMETRIC], ids=["symmetric", "asymmetric"])
def test_a_loop_that_crosses_itself_refuses_instead_of_answering_a_signed_area(
    profile: list[dict[str, Any]],
) -> None:
    with pytest.raises(CommandError) as excinfo:
        _profile(profile)
    assert excinfo.value.code == "pk_sketch_open"
    assert "crosses itself" in str(excinfo.value)


def test_the_refusal_names_the_two_curves_and_where_they_cross() -> None:
    """Law 6: the fix is a place, not 'the sketch is invalid'."""
    with pytest.raises(CommandError) as excinfo:
        _profile(BOWTIE)
    message = str(excinfo.value)
    assert "bt.0 crosses bt.2" in message
    assert "(10, 10) mm" in message
    assert "Split it into separate closed loops" in message


def test_extruding_a_self_crossing_loop_refuses_rather_than_making_a_zero_volume_body() -> None:
    """It used to answer `status: ok` with `volume_mm3: 0.0` and one solid."""
    doc = Document()
    doc.apply({"op": "create", "kind": "part", "name": "p"})
    doc.apply(
        {"op": "create", "kind": "sketch", "name": "s", "props": {"plane": "XY", "profile": BOWTIE}}
    )
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "extrude",
                "name": "e",
                "props": {"sketch": "s", "distance": 10},
            }
        )
    assert excinfo.value.code == "pk_sketch_open"


@pytest.mark.parametrize(
    ("name", "profile", "area_mm2"),
    [
        ("rect", [{"rect": [40, 20], "tag": "r"}], 800.0),
        ("circle", [{"circle": 20, "tag": "c"}], 314.159265),
        ("hexagon", [{"polygon": 6, "d": 40, "tag": "h"}], 1039.230485),
        (
            "L outline",
            [{"poly": [[0, 0], [40, 0], [40, 10], [10, 10], [10, 30], [0, 30]], "tag": "L"}],
            600.0,
        ),
        # the obvious false positive: the slot's two arcs meet its two lines tangentially.
        ("tangent-arc slot", [{"slot": [40, 10], "tag": "s"}], 378.539816),
        (
            "rect with a hole",
            [{"rect": [40, 20], "tag": "r"}, {"circle": 8, "at": [20, 10], "tag": "h"}],
            800.0 - 50.265482,
        ),
    ],
)
def test_the_guard_lets_every_ordinary_profile_through(
    name: str, profile: list[dict[str, Any]], area_mm2: float
) -> None:
    from partkiln.brep import shapes

    built = _profile(profile)
    assert sum(shapes.area(f) for f in built.faces) == pytest.approx(area_mm2, abs=1e-4)
