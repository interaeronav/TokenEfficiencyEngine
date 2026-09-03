"""The line fitter against a room that behaves like a real one.

Everything here exists because the single-rectangle fixture passed while the
fitter was badly wrong on a real scan: on the Okongo capture it returned 35
segments totalling 133 m of wall inside a 5 x 5 m room, running 4 m diagonals
through a bed and finding the same partition six times.
"""

from __future__ import annotations

import numpy as np
import pytest
from fixtures_pointcloud import make_two_rooms

from tee.pointcloud import slice2d


@pytest.fixture(scope="module")
def plan():
    # The fixture is already level and axis-aligned, which is the state
    # fit_ortho documents as its precondition. Levelling it again would
    # re-rotate it by the azimuth it finds (mod 90), swapping the axes and
    # testing the fixture rather than the fitter - levelling has its own tests.
    points, truth = make_two_rooms()
    return slice2d.band(points, 1.20, 0.05), truth


def _offsets(segments, axis):
    """Positions of the surfaces running perpendicular to `axis`."""
    out = []
    for seg in segments:
        a, b = np.array(seg["a"]), np.array(seg["b"])
        if abs((b - a)[axis]) < 0.05 * max(abs((b - a)[1 - axis]), 1e-9):
            out.append(float((a[axis] + b[axis]) / 2))
    return sorted(out)


def test_ortho_fit_finds_every_wall_and_invents_none(plan):
    band, _truth = plan
    segments, _ = slice2d.fit_ortho(band)
    total = sum(s["length_m"] for s in segments)
    # 2 long walls + 2 end walls + 2 partition faces, each split by the door
    assert 8 <= len(segments) <= 16, [round(s["length_m"], 2) for s in segments]
    # the real perimeter is about 27 m; anything near 100 m is invention
    assert 18.0 < total < 40.0, total


def test_ortho_fit_recovers_the_wall_positions(plan):
    band, truth = plan
    segments, _ = slice2d.fit_ortho(band)
    found = _offsets(segments, 0)
    for expected in (
        truth["west"],
        truth["partition_west"],
        truth["partition_east"],
        truth["east"],
    ):
        assert any(abs(f - expected) < 0.05 for f in found), (expected, found)


def test_partition_thickness_survives_duplicate_suppression(plan):
    """Two faces 260 mm apart are two surfaces; the same face found twice is one."""
    band, truth = plan
    segments, _ = slice2d.fit_ortho(band)
    found = _offsets(segments, 0)
    west = [f for f in found if abs(f - truth["partition_west"]) < 0.06]
    east = [f for f in found if abs(f - truth["partition_east"]) < 0.06]
    assert west and east, found
    assert abs((east[0] - west[0]) - truth["partition_thickness"]) < 0.03


def test_the_doorway_splits_the_partition_rather_than_being_bridged(plan):
    band, truth = plan
    segments, _ = slice2d.fit_ortho(band)
    partition = [
        s
        for s in segments
        if abs(np.array(s["a"])[0] - truth["partition_west"]) < 0.06
        or abs(np.array(s["a"])[0] - truth["partition_east"]) < 0.06
    ]
    assert partition, segments
    # no single run may span the doorway - that would be a wall that is not there
    for seg in partition:
        lo, hi = sorted((seg["a"][1], seg["b"][1]))
        assert not (lo < truth["door_from"] - 0.1 and hi > truth["door_to"] + 0.1), seg


def test_every_ortho_segment_is_continuous_along_its_length(plan):
    band, _ = plan
    segments, _ = slice2d.fit_ortho(band)
    for seg in segments:
        assert seg["occupancy"] >= slice2d.MIN_OCCUPANCY, seg


def test_no_segment_bridges_a_gap_in_its_own_support():
    """The failure the gap guard exists for, in isolation.

    Two tight clusters 3 m apart are collinear enough for RANSAC to join them
    into one 3.7 m "wall" spanning empty air. They are two short surfaces, and
    the fitter must say so rather than inventing the span between them.
    """
    rng = np.random.default_rng(0)
    t = np.concatenate([rng.uniform(0.0, 0.3, 120), rng.uniform(3.4, 3.7, 120)])
    sparse = np.c_[t, t] + rng.normal(0, 0.008, (len(t), 2))
    segments, _ = slice2d.fit_lines(sparse)
    assert all(s["length_m"] < 1.0 for s in segments), segments
    assert all(s["occupancy"] >= slice2d.MIN_OCCUPANCY for s in segments), segments


def test_clutter_does_not_become_architecture(plan):
    """No fitted surface may sit in the middle of the room away from a wall."""
    band, truth = plan
    segments, _ = slice2d.fit_ortho(band)
    walls = (truth["west"], truth["partition_west"], truth["partition_east"], truth["east"])
    for seg in segments:
        a, b = np.array(seg["a"]), np.array(seg["b"])
        if abs((b - a)[0]) < 0.05 * abs((b - a)[1]):  # runs along Y, so it has an X position
            x = float((a[0] + b[0]) / 2)
            assert min(abs(x - w) for w in walls) < 0.10, f"invented a wall at x={x:.2f}"
