"""P2a acceptance for partkiln.brep.query: the facts behind D6's selectors."""

from __future__ import annotations

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln.brep import fixtures, query, shapes

pytestmark = pytest.mark.brep


def test_f1_faces_types_normals_radius() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    assert [f.index for f in faces] == list(range(7))
    assert sorted(f.surface_type for f in faces) == ["cylinder"] + ["plane"] * 6
    cyl = next(f for f in faces if f.surface_type == "cylinder")
    assert cyl.radius == pytest.approx(5.0) and cyl.centroid == pytest.approx((50, 30, 5), abs=1e-9)
    top = next(f for f in faces if f.normal and f.normal[2] > 0.99)
    assert top.centroid == pytest.approx((50, 30, 10), abs=1e-9)
    assert top.area == pytest.approx(6000 - 25 * 3.141592653589793, abs=1e-6)
    normals = sorted(tuple(round(c) for c in f.normal) for f in faces if f.surface_type == "plane")
    assert normals == [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0), (1, 0, 0)]
    assert top.bbox == pytest.approx((0, 0, 10, 100, 60, 10), abs=1e-7)


def test_f1_edges_seam_direction_radius_convexity() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    edges = query.edges(f1, faces)
    assert len(edges) == 15 and [e.index for e in edges] == list(range(15))
    seams = [e for e in edges if e.is_seam]
    assert (
        len(seams) == 1 and seams[0].curve_type == "line" and seams[0].direction == (0.0, 0.0, 1.0)
    )
    assert seams[0].adjacent_face_indices == (
        faces.index(next(f for f in faces if f.surface_type == "cylinder")),
    )
    circles = [e for e in edges if e.curve_type == "circle"]
    assert len(circles) == 2 and all(e.radius == pytest.approx(5.0) for e in circles)
    assert all(e.convexity == "convex" for e in circles)  # a drilled rim is convex
    vertical = [e for e in edges if e.direction == (0.0, 0.0, 1.0) and not e.is_seam]
    assert len(vertical) == 4 and all(e.length == pytest.approx(10.0) for e in vertical)
    assert all(e.convexity == "convex" for e in edges if not e.is_seam)
    assert all(len(e.adjacent_face_indices) == 2 for e in edges if not e.is_seam)


def test_direction_sign_is_canonical() -> None:
    b = shapes.box(10, 20, 30)
    dirs = {e.direction for e in query.edges(b)}
    assert dirs == {(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)}


def test_concave_and_tangent_edges_on_the_l_bracket() -> None:
    fused, _ = shapes.unify(
        shapes.fuse([shapes.box(80, 60, 6), shapes.box(80, 6, 34, (0, 0, 6))]).shape
    )
    inner = next(e for e in query.edges(fused) if e.midpoint == pytest.approx((40, 6, 6), abs=1e-9))
    assert inner.convexity == "concave"
    assert sum(e.convexity == "concave" for e in query.edges(fused)) == 1
    filleted = shapes.fillet(fused, [inner.shape], 6.0).shape
    tangent = [e for e in query.edges(filleted) if e.convexity == "tangent"]
    assert len(tangent) == 2 and all(e.length == pytest.approx(80.0) for e in tangent)


def test_loops_outer_and_inner() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    edges = query.edges(f1, faces)
    top = next(f for f in faces if f.normal and f.normal[2] > 0.99)
    loops = query.loops(top.shape, edges)
    assert len(loops["outer"]) == 1 and len(loops["outer"][0]) == 4
    assert len(loops["inner"]) == 1 and len(loops["inner"][0]) == 1
    assert edges[loops["inner"][0][0]].curve_type == "circle"
    assert all(
        edges[i].curve_type == "line" and edges[i].length in (60.0, 100.0)
        for i in loops["outer"][0]
    )


def test_nearest_is_deterministic() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    assert query.nearest(faces, (50, 30, 9.9)).centroid == pytest.approx((50, 30, 10), abs=1e-9)
    edges = query.edges(f1, faces)
    hit = query.nearest(edges, (0, 0, 5))
    assert hit.midpoint == pytest.approx((0, 0, 5), abs=1e-9)
    assert query.nearest([], (0, 0, 0)) is None


def test_order_is_stable_across_processes() -> None:
    """Index i names the same face in a fresh interpreter (the geometric sort)."""
    import subprocess
    import sys

    code = (
        "from partkiln.brep import fixtures, query\n"
        "f = fixtures.build_F5()\n"
        "print([(x.surface_type, round(x.centroid[0], 3), round(x.centroid[1], 3)) "
        "for x in query.faces(f)][:12])\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    here = repr(
        [
            (x.surface_type, round(x.centroid[0], 3), round(x.centroid[1], 3))
            for x in query.faces(fixtures.build_F5())
        ][:12]
    )
    assert out == here
