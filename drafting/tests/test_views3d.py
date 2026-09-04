"""Elevations and the drawn axonometric: never invent a height."""

from __future__ import annotations

import numpy as np
import pytest

from drafting import views3d as V


def seg(a, b):
    return {"a": list(a), "b": list(b), "length_m": float(np.hypot(b[0] - a[0], b[1] - a[1]))}


def wall_points(x, y0, y1, z0, z1, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    return np.c_[
        np.full(n, x) + rng.normal(0, 0.005, n), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)
    ]


def test_a_face_is_extruded_over_the_height_its_own_returns_cover():
    face = seg((0.0, 0.0), (0.0, 3.0))
    extent = V.face_extent(face, wall_points(0.0, 0.0, 3.0, 0.0, 2.6))
    assert extent[0] == pytest.approx(0.0, abs=0.05)
    assert extent[1] == pytest.approx(2.6, abs=0.05)


def test_a_partial_height_element_is_not_stretched_to_the_ceiling():
    """A sill at +0.69 must draw as a sill. This is the whole discipline."""
    face = seg((0.0, 0.0), (0.0, 1.2))
    base, _top = V.face_extent(face, wall_points(0.0, 0.0, 1.2, 0.69, 2.6))
    assert base == pytest.approx(0.69, abs=0.05)
    quads = V.wall_quads([face], wall_points(0.0, 0.0, 1.2, 0.69, 2.6))
    assert quads[0]["base"] == pytest.approx(0.69, abs=0.05)


def test_a_face_with_too_few_returns_is_not_drawn():
    face = seg((0.0, 0.0), (0.0, 3.0))
    assert V.face_extent(face, wall_points(0.0, 0.0, 3.0, 0.0, 2.6, n=20)) is None
    assert V.wall_quads([face], wall_points(0.0, 0.0, 3.0, 0.0, 2.6, n=20)) == []


def test_a_stray_return_does_not_decide_the_wall_height():
    """Percentiles, not min/max."""
    cloud = np.vstack([wall_points(0.0, 0.0, 3.0, 0.0, 2.6), [[0.0, 1.5, 9.0]]])
    _, top = V.face_extent(seg((0.0, 0.0), (0.0, 3.0)), cloud)
    assert top < 3.0


def test_a_flat_smear_is_not_a_solid():
    face = seg((0.0, 0.0), (0.0, 3.0))
    assert V.wall_quads([face], wall_points(0.0, 0.0, 3.0, 1.0, 1.05)) == []


def test_an_elevation_is_not_mirrored():
    """Looking at the two opposite walls of a room must not flip the content."""
    rng = np.random.default_rng(3)
    marker = np.c_[
        rng.uniform(-0.02, 0.02, 400) + 1.0, rng.uniform(0.1, 0.4, 400), rng.uniform(1.0, 1.4, 400)
    ]
    seen = V.elevation(np.vstack([marker]), 1, 0.0, -1.0, 3.0, look=+1.0)
    assert len(seen), "the marker should be visible from this side"
    assert seen[:, 0].min() == pytest.approx(0.0, abs=1e-9)


def test_an_elevation_only_takes_what_is_in_front_of_the_wall():
    rng = np.random.default_rng(4)
    front = np.c_[rng.uniform(0.1, 0.5, 300), rng.uniform(0, 2, 300), rng.uniform(0, 2, 300)]
    behind = np.c_[rng.uniform(-2.0, -1.0, 300), rng.uniform(0, 2, 300), rng.uniform(0, 2, 300)]
    seen = V.elevation(np.vstack([front, behind]), 0, 0.0, -1.0, 3.0, look=+1.0)
    assert len(seen) == 300


def test_painter_order_puts_the_far_solid_first():
    matrix = V.iso_matrix()
    near = {
        "corners": np.array([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]], float),
        "length_m": 1.0,
    }
    far = {
        "corners": np.array([[0, 8, 0], [1, 8, 0], [1, 8, 1], [0, 8, 1]], float),
        "length_m": 1.0,
    }
    ordered = V.painter_order([near, far], matrix)
    first_depth = (ordered[0]["corners"] @ matrix.T)[:, 1].mean()
    last_depth = (ordered[-1]["corners"] @ matrix.T)[:, 1].mean()
    assert first_depth > last_depth, "far solids must be painted first"


def test_the_projection_is_two_dimensional_and_preserves_the_corner_count():
    quad = np.array([[0, 0, 0], [1, 0, 0], [1, 0, 2], [0, 0, 2]], float)
    xy = V.project(quad, V.iso_matrix())
    assert xy.shape == (4, 2)


def test_a_taller_wall_projects_taller():
    matrix = V.iso_matrix()
    short = V.project(np.array([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]], float), matrix)
    tall = V.project(np.array([[0, 0, 0], [1, 0, 0], [1, 0, 3], [0, 0, 3]], float), matrix)
    assert np.ptp(tall[:, 1]) > np.ptp(short[:, 1])
