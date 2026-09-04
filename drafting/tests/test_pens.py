"""The Revit-inspired pen model: a weight is a category, not a millimetre."""

from __future__ import annotations

import numpy as np
import pytest

from drafting import standards as S
from drafting.linework import close_corners, poche_bodies


def seg(a, b, length=None):
    return {
        "a": list(a),
        "b": list(b),
        "length_m": length if length is not None else float(np.hypot(b[0] - a[0], b[1] - a[1])),
    }


# -- pens ------------------------------------------------------------------


def test_every_resolved_pen_lands_on_the_standard_set():
    """The indirection must not smuggle in a width nobody can plot."""
    for category in S.CATEGORY_PENS:
        for scale in S.PREFERRED_SCALES:
            for cut in (True, False):
                width = S.resolve_pen(category, scale, cut=cut)
                assert any(abs(width - w) < 1e-9 for w in S.LINE_WEIGHTS_MM), (category, scale)


def test_the_same_category_is_heavier_at_a_larger_scale():
    """The whole point of a weight index: re-scale the view, not the objects."""
    assert S.resolve_pen("wall", 20, cut=True) > S.resolve_pen("wall", 100, cut=True)
    assert S.resolve_pen("wall", 50, cut=True) >= S.resolve_pen("wall", 100, cut=True)


def test_the_cut_is_always_heavier_than_the_projection():
    """'The cut is black, the beyond is grey.'"""
    for category in S.CATEGORY_PENS:
        for scale in (20, 50, 100):
            assert S.resolve_pen(category, scale, cut=True) >= S.resolve_pen(category, scale)


def test_a_wall_cut_outweighs_a_grid_line_at_every_scale():
    for scale in (20, 50, 100, 200):
        assert S.resolve_pen("wall", scale, cut=True) > S.resolve_pen("grid", scale)


def test_dash_patterns_are_defined_on_the_paper_not_in_the_model():
    """A dash must read the same length whatever the view is scaled to."""
    assert S.dash_pattern("solid") is None
    a = S.dash_pattern("centre")
    b = S.dash_pattern("centre")
    assert a == b, "the pattern must not depend on view scale"
    assert a[1][0] == pytest.approx(9.0 * S.POINTS_PER_MM)


def test_halftone_moves_a_colour_toward_white_without_reaching_it():
    faded = S.halftone("#000000")
    assert all(0.0 < c < 1.0 for c in faded)
    assert S.halftone("#000000", 0.9)[0] > S.halftone("#000000", 0.1)[0]


# -- corner closure --------------------------------------------------------


def test_corners_close_to_their_neighbour():
    """Independently fitted faces stop where their points stopped."""
    segs = [seg((0.0, 0.05), (0.0, 3.0)), seg((0.05, 0.0), (4.0, 0.0))]
    closed = close_corners(segs)
    assert min(closed[0]["a"][1], closed[0]["b"][1]) == pytest.approx(0.0, abs=1e-6)


def test_closure_never_shortens_a_face():
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((0.0, 0.0), (4.0, 0.0))]
    closed = close_corners(segs)
    for before, after in zip(segs, closed, strict=True):
        assert after["length_m"] >= before["length_m"] - 1e-6


def test_a_face_is_never_stretched_across_the_room_to_find_a_mate():
    """Extension is bounded: a face is evidence over its own length only."""
    segs = [seg((0.0, 2.0), (0.0, 3.0)), seg((0.0, -5.0), (4.0, -5.0))]
    closed = close_corners(segs)
    assert min(closed[0]["a"][1], closed[0]["b"][1]) > -1.0


# -- poche -----------------------------------------------------------------


def _wall_cloud(x0, x1, y0=0.0, y1=3.0, n=600, seed=0):
    """Two faces with NOTHING between them: what a solid looks like to a scanner."""
    rng = np.random.default_rng(seed)
    ys = rng.uniform(y0, y1, n)
    return np.c_[np.r_[np.full(n, x0), np.full(n, x1)], np.r_[ys, ys]]


def test_two_faces_with_an_empty_band_become_a_filled_body():
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((0.15, 0.0), (0.15, 3.0))]
    bodies = poche_bodies(segs, _wall_cloud(0.0, 0.15))
    assert len(bodies) == 1
    assert bodies[0].thickness_mm == pytest.approx(150.0, abs=1.0)
    assert bodies[0].interior_returns == 0


def test_two_faces_with_returns_between_them_are_NOT_a_wall():
    """The evidence test. A band full of points is two surfaces with a gap."""
    cloud = _wall_cloud(0.0, 0.30)
    rng = np.random.default_rng(1)
    middle = np.c_[rng.uniform(0.10, 0.20, 400), rng.uniform(0.0, 3.0, 400)]
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((0.30, 0.0), (0.30, 3.0))]
    assert poche_bodies(segs, np.vstack([cloud, middle])) == []


def test_faces_too_far_apart_are_not_paired():
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((2.0, 0.0), (2.0, 3.0))]
    assert poche_bodies(segs, _wall_cloud(0.0, 2.0)) == []


def test_faces_that_barely_overlap_are_not_paired():
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((0.15, 2.9), (0.15, 3.0))]
    assert poche_bodies(segs, _wall_cloud(0.0, 0.15)) == []


def test_a_body_reports_the_evidence_it_was_inferred_from():
    """Pairing faces is an inference; the drawing has to be able to say so."""
    segs = [seg((0.0, 0.0), (0.0, 3.0)), seg((0.15, 0.0), (0.15, 3.0))]
    body = poche_bodies(segs, _wall_cloud(0.0, 0.15))[0]
    assert body.face_returns > 0
    assert len(body.polygon) == 4
