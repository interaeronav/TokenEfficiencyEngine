"""Plan linework: close the corners, and fill what the view cuts through.

Two things separate a drawing from a plot of fitted lines, and both are what
your eye is actually reading when a Revit plan looks crisp:

* **Corners close.** Surfaces fitted independently stop where their points
  stopped, so a room reads as four lines that nearly meet. Real drafting
  extends each to its neighbour's intersection.
* **The cut is filled.** A wall sliced by the view plane is drawn as a filled
  body between its two faces - poché - not as two thin parallel lines. This is
  the single biggest legibility gain available on a plan.

Pairing two faces into one wall is an INFERENCE, and A67's non-goal 1 forbids
guessing which points are the wall. So the pairing here is not a guess: two
faces are only paired when the band between them is EMPTY of returns, which is
what a solid wall looks like to a scanner that cannot see inside it. The test
is measured against the cloud, and `poche_bodies` reports the evidence for
every body it proposes so the drawing can say so.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIN_WALL_MM = 60.0
MAX_WALL_MM = 500.0
MIN_OVERLAP_FRACTION = 0.35
# A body shorter than this is 6 mm on paper at 1:50 and communicates nothing;
# it is also where a short stub against a long wall gets mistaken for a pier.
MIN_BODY_LEN_M = 0.30
EMPTY_BAND_TOLERANCE = 0.06  # fraction of the face's own point density
CORNER_REACH_M = 0.45  # how far a face may be extended to meet another


@dataclass
class Body:
    """A cut solid inferred from two faces with nothing measured between them."""

    a: tuple[float, float]
    b: tuple[float, float]
    c: tuple[float, float]
    d: tuple[float, float]
    thickness_mm: float
    interior_returns: int
    face_returns: int

    @property
    def polygon(self) -> list[tuple[float, float]]:
        return [self.a, self.b, self.c, self.d]


def _axis_of(seg) -> int | None:
    """0 if the segment runs along Y (constant X), 1 if along X. None if skew."""
    dx = abs(seg["a"][0] - seg["b"][0])
    dy = abs(seg["a"][1] - seg["b"][1])
    if dx < 0.05 * max(dy, 1e-9):
        return 0
    if dy < 0.05 * max(dx, 1e-9):
        return 1
    return None


def close_corners(segments: list[dict], reach: float = CORNER_REACH_M) -> list[dict]:
    """Extend each axis-parallel face to meet a perpendicular neighbour.

    Only extension, never truncation, and never further than `reach`: a face
    is evidence that a surface exists along its length, and stretching one
    across a room to meet something far away would be drawing a wall nobody
    measured.
    """
    out = [dict(s) for s in segments]
    for seg in out:
        axis = _axis_of(seg)
        if axis is None:
            continue
        other = 1 - axis
        fixed = (seg["a"][axis] + seg["b"][axis]) / 2.0
        lo, hi = sorted((seg["a"][other], seg["b"][other]))
        for mate in out:
            if mate is seg or _axis_of(mate) != other:
                continue
            mate_fixed = (mate["a"][other] + mate["b"][other]) / 2.0
            m_lo, m_hi = sorted((mate["a"][axis], mate["b"][axis]))
            if not (m_lo - reach <= fixed <= m_hi + reach):
                continue
            if 0 < lo - mate_fixed <= reach:
                lo = mate_fixed
            elif 0 < mate_fixed - hi <= reach:
                hi = mate_fixed
        seg["a"] = [fixed, lo] if axis == 0 else [lo, fixed]
        seg["b"] = [fixed, hi] if axis == 0 else [hi, fixed]
        seg["length_m"] = round(hi - lo, 4)
        seg["corner_closed"] = True
    return out


def poche_bodies(segments: list[dict], points_2d: np.ndarray) -> list[Body]:
    """Pair opposite faces into filled cut bodies, on measured evidence.

    A pair qualifies only when the band between the two faces holds almost no
    returns. A scanner sees both sides of a wall and nothing inside it, so an
    empty band is the signature of a solid; a band full of points is two
    surfaces with a gap between them, which is not a wall.
    """
    bodies: list[Body] = []
    used: set[int] = set()
    order = sorted(range(len(segments)), key=lambda i: -segments[i]["length_m"])
    for i in order:
        if i in used:
            continue
        first = segments[i]
        axis = _axis_of(first)
        if axis is None:
            continue
        other = 1 - axis
        f_pos = (first["a"][axis] + first["b"][axis]) / 2.0
        f_lo, f_hi = sorted((first["a"][other], first["b"][other]))

        best = None
        for j in order:
            if j == i or j in used or _axis_of(segments[j]) != axis:
                continue
            second = segments[j]
            s_pos = (second["a"][axis] + second["b"][axis]) / 2.0
            gap_mm = abs(s_pos - f_pos) * 1000.0
            if not (MIN_WALL_MM <= gap_mm <= MAX_WALL_MM):
                continue
            s_lo, s_hi = sorted((second["a"][other], second["b"][other]))
            overlap = min(f_hi, s_hi) - max(f_lo, s_lo)
            shorter = min(f_hi - f_lo, s_hi - s_lo)
            if shorter <= 0 or overlap < MIN_OVERLAP_FRACTION * shorter:
                continue
            if overlap < MIN_BODY_LEN_M:
                continue
            if best is None or gap_mm < best[1]:
                best = (j, gap_mm, s_pos, max(f_lo, s_lo), min(f_hi, s_hi))
        if best is None:
            continue
        j, gap_mm, s_pos, lo, hi = best

        # the measured test: is the band between the two faces empty?
        inner_lo, inner_hi = sorted((f_pos, s_pos))
        margin = 0.25 * (inner_hi - inner_lo)
        inside = points_2d[
            (points_2d[:, axis] > inner_lo + margin)
            & (points_2d[:, axis] < inner_hi - margin)
            & (points_2d[:, other] > lo)
            & (points_2d[:, other] < hi)
        ]
        on_faces = points_2d[
            (np.abs(points_2d[:, axis] - f_pos) < 0.05)
            & (points_2d[:, other] > lo)
            & (points_2d[:, other] < hi)
        ]
        if len(on_faces) < 20:
            continue
        if len(inside) > EMPTY_BAND_TOLERANCE * len(on_faces):
            continue  # points inside it: two surfaces, not one wall

        def corner(pos, along, _axis=axis):
            return (pos, along) if _axis == 0 else (along, pos)

        bodies.append(
            Body(
                a=corner(f_pos, lo),
                b=corner(f_pos, hi),
                c=corner(s_pos, hi),
                d=corner(s_pos, lo),
                thickness_mm=round(gap_mm, 1),
                interior_returns=len(inside),
                face_returns=len(on_faces),
            )
        )
        used.update({i, j})
    return bodies
