"""P2a acceptance for partkiln.brep.fingerprint: identical across processes."""

from __future__ import annotations

import subprocess
import sys

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from partkiln._errors import KernelError
from partkiln.brep import fingerprint, fixtures, query, shapes

pytestmark = pytest.mark.brep


def test_f5_fingerprint_identical_in_a_fresh_process() -> None:
    here = fingerprint.shape_fingerprint(fixtures.build_F5())
    code = (
        "from partkiln.brep import fingerprint, fixtures\n"
        "print(fingerprint.shape_fingerprint(fixtures.build_F5()))"
    )
    there = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert len(here) == 16 and here == there


def test_fingerprint_changes_with_geometry_not_with_rebuild() -> None:
    a, b = fixtures.build_F1(), fixtures.build_F1()
    assert fingerprint.shape_fingerprint(a) == fingerprint.shape_fingerprint(b)
    edited = shapes.cut(shapes.box(100, 60, 10), [shapes.cylinder(6, 12, (50, 30, -1))]).shape
    assert fingerprint.shape_fingerprint(edited) != fingerprint.shape_fingerprint(a)
    keys = fingerprint.face_keys(a)
    assert keys == sorted(keys) and len(keys) == 7
    assert keys[0][0] == "cylinder" and keys[0][1] == pytest.approx(314.159)


def test_subshape_fingerprint_is_the_rounded_tuple() -> None:
    f1 = fixtures.build_F1()
    faces = query.faces(f1)
    top = next(f for f in faces if f.normal and f.normal[2] > 0.99)
    assert fingerprint.subshape_fingerprint(top.shape) == (
        "plane",
        5921.46,
        (50.0, 30.0, 10.0),
        (0.0, 0.0, 1.0),
        None,
    )
    wall = next(f for f in faces if f.surface_type == "cylinder")
    kind, area, centroid, _normal, radius = fingerprint.subshape_fingerprint(wall.shape)
    assert (kind, area, centroid, radius) == ("cylinder", 314.159, (50.0, 30.0, 5.0), 5.0)
    edge = fixtures.edge_at(f1, (50.0, 0.0, 10.0))
    assert fingerprint.subshape_fingerprint(edge) == (
        "line",
        100.0,
        (50.0, 0.0, 10.0),
        (1.0, 0.0, 0.0),
        None,
    )
    circle = next(e for e in query.edges(f1) if e.curve_type == "circle" and e.midpoint[2] > 5)
    assert fingerprint.subshape_fingerprint(circle.shape) == (
        "circle",
        31.416,
        (45.0, 30.0, 10.0),
        None,
        5.0,
    )
    with pytest.raises(KernelError, match="only a face or an edge"):
        fingerprint.subshape_fingerprint(f1)


def test_subshape_fingerprint_survives_an_unrelated_edit() -> None:
    """The fallback D6 relies on: the same face after an edit elsewhere keeps its tuple."""
    before = fixtures.build_F1()
    after = shapes.cut(before, [shapes.cylinder(2, 12, (10, 10, -1))]).shape
    front = lambda s: next(f for f in query.faces(s) if f.normal and f.normal[1] < -0.99)  # noqa: E731
    assert fingerprint.subshape_fingerprint(
        front(before).shape
    ) == fingerprint.subshape_fingerprint(front(after).shape)
