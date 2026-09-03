"""A67 acceptance A1-A4: level, yaw, slice fidelity, control and scale.

Every number asserted here was measured before the code was written and is
recorded in docs/research/69. A gate that drifts is a regression in the
algorithm, not a flaky test - the fixture is deterministic.
"""

from __future__ import annotations

import numpy as np
import pytest
from fixtures_pointcloud import make_room

from tee.kernel.errors import TeeError
from tee.pointcloud import control, slice2d
from tee.pointcloud import level as level_mod


@pytest.fixture(scope="module")
def room():
    return make_room()


@pytest.fixture(scope="module")
def levelled(room):
    points, truth = room
    return level_mod.level(points), truth


def _yaw_error(found: float, injected: float = 37.0) -> float:
    return min(abs(found - injected), abs(found - injected + 90), abs(found - injected - 90))


def _interior(segments):
    xs = sorted(
        np.mean([s["a"][0], s["b"][0]]) for s in segments if abs(s["a"][0] - s["b"][0]) < 0.05
    )
    ys = sorted(
        np.mean([s["a"][1], s["b"][1]]) for s in segments if abs(s["a"][1] - s["b"][1]) < 0.05
    )
    return xs[-1] - xs[0], ys[-1] - ys[0], xs, ys


def test_fixture_is_the_one_the_reference_numbers_came_from(room):
    points, truth = room
    assert len(points) == 279_352, "doc 69 4 quotes this exact count"
    assert truth["scaled_L"] == pytest.approx(4.0160, abs=1e-4)
    assert truth["correction"] == pytest.approx(0.99602, abs=1e-5)


# -- A1 --------------------------------------------------------------------


def test_a1_level_recovers_the_injected_tilt(levelled):
    out, _ = levelled
    assert out["residual_tilt_deg"] <= 0.05, out


def test_a1_floor_rms_lands_within_20_percent_of_the_injected_noise(levelled):
    out, truth = levelled
    injected_mm = truth["noise"] * 1000
    assert 0.8 * injected_mm <= out["floor_rms_mm"] <= 1.2 * injected_mm, out


def test_level_puts_the_room_above_its_floor_not_below_its_ceiling(levelled):
    """The regression this caught: floor and ceiling have the same point count,
    so 'most inliers' picked the ceiling and hung the room underneath it."""
    out, truth = levelled
    z = out["points"][:, 2]
    assert z.min() > -0.1, "floor should sit at z=0"
    assert z.max() == pytest.approx(truth["H"] * truth["scale"], abs=0.1)
    # The floor's own 12 mm noise straddles zero, so a bare sign count proves
    # nothing. What proves it: essentially nothing sits BELOW the floor's
    # noise band, and the room's mass is up in the middle of its height.
    assert (z < -0.05).sum() < len(z) * 0.01
    assert np.median(z) > truth["H"] * 0.25


def test_level_is_deterministic(room):
    points, _ = room
    assert level_mod.level(points)["matrix"] == level_mod.level(points)["matrix"]


def test_level_refuses_when_there_is_no_horizontal_plane():
    rng = np.random.default_rng(0)
    with pytest.raises(TeeError) as exc:
        level_mod.level(rng.uniform(0, 5, (5_000, 3)))
    assert exc.value.code == "pc_no_floor_plane"
    assert "floor_hint_z" in (exc.value.fix or "")


# -- A2 --------------------------------------------------------------------


def test_a2_wall_azimuth_is_within_half_a_degree(levelled):
    out, truth = levelled
    assert _yaw_error(out["wall_azimuth_deg"], truth["yaw"]) <= 0.5, out


def test_a2_the_3d_normal_estimator_beats_the_scripts_hoped_for_tenth_of_a_degree(levelled):
    out, _ = levelled
    assert _yaw_error(out["wall_azimuth_deg"]) <= 0.1


def test_yaw_from_a_thin_slice_would_fail_the_gate(levelled):
    """Why yaw is estimated on the full-height band and never on the section.

    Measured 1.289 deg from a 50 mm slice against a 0.5 deg gate - so this is
    pinned, to stop a future 'simplification' from sharing the two estimators.
    """
    out, _ = levelled
    points = out["points"]
    thin = points[np.abs(points[:, 2] - 1.2) < 0.025][:, :2]
    _, _, vt = np.linalg.svd(thin - thin.mean(axis=0), full_matrices=False)
    slice_yaw = np.degrees(np.arctan2(vt[0][1], vt[0][0])) % 90
    assert _yaw_error(slice_yaw) > 0.5, "if this ever passes, re-measure before simplifying"


# -- A3 --------------------------------------------------------------------


@pytest.fixture(scope="module")
def plan(levelled):
    out, truth = levelled
    segments, ignored = slice2d.fit_lines(slice2d.band(out["points"], 1.2, 0.05))
    return segments, ignored, truth


def test_a3_slice_finds_the_four_walls(plan):
    segments, _, _ = plan
    assert len(segments) == 4, [s["length_m"] for s in segments]


def test_a3_interior_dimensions_are_within_five_millimetres(plan):
    segments, _, truth = plan
    length, width, _, _ = _interior(segments)
    assert length == pytest.approx(truth["scaled_L"], abs=0.005)
    assert width == pytest.approx(truth["scaled_W"], abs=0.005)


def test_slice_residual_median_is_near_the_noise_floor(plan):
    segments, _, truth = plan
    for seg in segments:
        assert seg["residual_median_mm"] <= truth["noise"] * 1000
        assert seg["residual_median_mm"] < seg["residual_max_mm"], "max is the misleading one"


def test_slice_refuses_an_empty_band(levelled):
    out, _ = levelled
    with pytest.raises(TeeError) as exc:
        slice2d.band(out["points"], 40.0)
    assert exc.value.code == "pc_empty_slice"


# -- A4 --------------------------------------------------------------------


@pytest.fixture(scope="module")
def baseline(levelled, plan):
    out, truth = levelled
    segments, _, _ = plan
    _, _, xs, ys = _interior(segments)
    mid = (ys[0] + ys[-1]) / 2
    # picked sloppily on purpose: 30-50 mm off the wall, which the snap fixes
    return control.add_baseline(
        out["points"],
        "long wall",
        [xs[0] + 0.04, mid + 0.03, 1.2],
        [xs[-1] - 0.05, mid - 0.02, 1.2],
        4000.0,
    ), truth


def test_control_snaps_a_sloppy_pick_onto_the_surface(baseline):
    base, _ = baseline
    assert base["snapped_from"] is True
    assert base["measured_mm"] == pytest.approx(4016, abs=6)


def test_a4_suggested_scale_is_within_500_ppm(baseline):
    base, truth = baseline
    result = control.check([base])
    error_ppm = abs(result["suggested_scale"] - truth["correction"]) / truth["correction"] * 1e6
    assert error_ppm <= 500, result


def test_a4_applying_the_scale_lands_both_dimensions_within_two_millimetres(plan, baseline):
    segments, _, truth = plan
    base, _ = baseline
    factor = control.check([base])["suggested_scale"]
    length, width, _, _ = _interior(segments)
    assert length * factor == pytest.approx(truth["L"], abs=0.002)
    assert width * factor == pytest.approx(truth["W"], abs=0.002)


def test_control_names_drift_rather_than_inventing_a_factor():
    """Two baselines that cannot both be right must be called drift."""
    rows = [
        {"name": "north", "measured_mm": 4016.0, "true_mm": 4000.0, "tol_mm": 5.0},
        {"name": "south", "measured_mm": 3020.0, "true_mm": 3000.0, "tol_mm": 5.0},
    ]
    result = control.check(rows)
    assert "drift" in result
    assert "south" in result["drift"] or "north" in result["drift"]
    assert "smaller scans" in result["fix"]


def test_control_calls_a_units_error_a_units_error():
    rows = [{"name": "wall", "measured_mm": 4_000_000.0, "true_mm": 4000.0, "tol_mm": 5.0}]
    result = control.check(rows)
    assert "units_conflict" in result
    assert "units" in result["fix"]


def test_control_refuses_a_degenerate_baseline(levelled):
    out, _ = levelled
    with pytest.raises(TeeError) as exc:
        control.add_baseline(out["points"], "nothing", [1, 1, 1.2], [1, 1, 1.2], 4000.0)
    assert exc.value.code == "pc_degenerate_baseline"


def test_control_check_refuses_with_no_baselines():
    with pytest.raises(TeeError) as exc:
        control.check([])
    assert exc.value.code == "pc_no_baselines"
