"""The F1 sweep cannot mistake samples or vertex distances for a proof."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
from f1_geometry import polygon_gap, rotate, sweep_clearance


def box(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def test_crossing_edges_collide_even_when_all_vertices_are_far_apart() -> None:
    horizontal, vertical = box(-10, -0.1, 10, 0.1), box(-0.1, -10, 0.1, 10)
    assert min(math.dist(a, b) for a in horizontal for b in vertical) > 13
    assert polygon_gap(horizontal, vertical) == 0


@pytest.mark.parametrize("reverse", [False, True])
def test_containment_is_zero_despite_no_boundary_crossing(reverse: bool) -> None:
    inner, outer = box(1, 1, 2, 2), box(-3, -4, 8, 9)
    if reverse:
        outer.reverse()
    assert polygon_gap(inner, outer) == 0
    assert polygon_gap(outer, inner) == 0


@pytest.mark.parametrize("other", [box(1, 0, 2, 1), box(1, 1, 2, 2)])
def test_collinear_edge_and_single_corner_touch_both_collide(other: list[list[float]]) -> None:
    assert polygon_gap(box(0, 0, 1, 1), other) == 0


def test_near_parallel_edges_use_projected_distance_not_nearest_vertices() -> None:
    a = box(0, 0, 100, 1)
    b = [[20, 1.000001], [80, 1.000002], [80, 2], [20, 2]]
    assert min(math.dist(ap, bp) for ap in a for bp in b) >= 20
    assert polygon_gap(a, b) == pytest.approx(0.000001, abs=1e-12)
    assert polygon_gap(b, a) == pytest.approx(0.000001, abs=1e-12)


def test_collinear_but_separated_segments_do_not_collide() -> None:
    assert polygon_gap(box(0, 0, 1, 1), box(3, 0, 4, 1)) == pytest.approx(2)


def test_concave_empty_notch_is_not_mistaken_for_containment() -> None:
    u = [[0, 0], [4, 0], [4, 4], [3, 4], [3, 1], [1, 1], [1, 4], [0, 4]]
    assert polygon_gap(u, box(1.5, 2, 2.5, 3)) == pytest.approx(0.5)


def test_closed_ring_and_rotation_preserve_distance() -> None:
    a, b = box(1, 0, 2, 1), box(4, 0, 5, 1)
    assert polygon_gap([*a, a[0]], b) == 2
    assert rotate(a, 90)[0] == pytest.approx([0, 1])
    assert polygon_gap(rotate(a, 37), rotate(b, 37)) == pytest.approx(2)


def test_positive_sweep_bound_certifies_between_samples() -> None:
    moving, fixed = box(1, -0.5, 2, 0.5), box(-1, 7, 1, 9)
    result = sweep_clearance(fixed, moving, list(range(0, 26, 5)))
    assert result["interval_deg"] == [0, 25]
    assert result["sample_count"] == 6
    assert result["radius"] == pytest.approx(math.hypot(2, 0.5))
    penalty = 2 * result["radius"] * math.sin(math.radians(5) / 4)
    assert result["sampling_penalty"] == pytest.approx(penalty)
    assert result["lower_bound"] < result["min_sample_gap"] - penalty
    assert result["certified_clearance"] is True
    # Independent denser points check the bound's practical direction.
    for half_degree in range(51):
        assert polygon_gap(fixed, rotate(moving, half_degree / 2)) >= result["lower_bound"]


def test_separated_samples_cannot_certify_a_collision_between_them() -> None:
    moving = box(9.9, -0.1, 10.1, 0.1)
    fixed = rotate(moving, 45)
    result = sweep_clearance(fixed, moving, [0, 90])
    assert all(row["gap"] > 7 for row in result["samples"])
    assert polygon_gap(fixed, rotate(moving, 45)) == 0
    assert result["lower_bound"] < 0
    assert result["certified_clearance"] is False


@pytest.mark.parametrize(
    "angles",
    [[], [0], [0, 0], [25, 20, 15], [0, 5, 11], [0, float("nan")], [0, 361]],
)
def test_bad_sample_coverage_is_rejected(angles: list[float]) -> None:
    with pytest.raises(ValueError):
        sweep_clearance(box(0, 0, 1, 1), box(5, 0, 6, 1), angles)


@pytest.mark.parametrize(
    "polygon",
    [
        [[0, 0], [1, 0]],
        [[0, 0], [1, 0], [2, 0]],
        [[0, 0], [1, 0], [1, 0], [0, 1]],
        [[0, 0], [2, 2], [0, 2], [2, 0]],
        [[0, 0], [1, 0], [0, float("inf")]],
    ],
)
def test_invalid_polygon_cannot_receive_clearance(polygon: list[list[float]]) -> None:
    with pytest.raises(ValueError):
        polygon_gap(polygon, box(4, 4, 5, 5))
