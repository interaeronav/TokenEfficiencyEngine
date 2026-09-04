"""Elevations and a drawn axonometric, built from fitted plan geometry.

The discipline is the same one that governs poche: nothing here invents a
height. Each face is extruded over the vertical extent that ITS OWN returns
cover, so a sill at +0.69 draws as a sill instead of being stretched to the
ceiling, and a face with too few returns is not drawn at all.

An axonometric assembled this way is a DRAWING, not a render. Solids are
painted back to front, so what is nearer hides what is behind it, and the
result reads with line weights rather than with pixels.
"""

from __future__ import annotations

import numpy as np

MIN_FACE_RETURNS = 200
MIN_SOLID_HEIGHT_M = 0.30
MIN_SOLID_LENGTH_M = 0.35
FACE_TOL_M = 0.08
ELEVATION_DEPTH_M = 0.75


def face_axis(segment: dict) -> int | None:
    """0 if the face runs along Y (constant X), 1 if along X, None if skew."""
    dx = abs(segment["a"][0] - segment["b"][0])
    dy = abs(segment["a"][1] - segment["b"][1])
    if dx < 0.05 * max(dy, 1e-9):
        return 0
    if dy < 0.05 * max(dx, 1e-9):
        return 1
    return None


def face_extent(segment: dict, points: np.ndarray) -> tuple[float, float] | None:
    """(base, top) measured from this face's own returns, or None if too few.

    Percentiles rather than min/max: a single stray return should not decide
    how tall a wall is drawn.
    """
    axis = face_axis(segment)
    if axis is None:
        return None
    other = 1 - axis
    position = (segment["a"][axis] + segment["b"][axis]) / 2.0
    lo, hi = sorted((segment["a"][other], segment["b"][other]))
    near = points[
        (np.abs(points[:, axis] - position) < FACE_TOL_M)
        & (points[:, other] > lo)
        & (points[:, other] < hi)
    ]
    if len(near) < MIN_FACE_RETURNS:
        return None
    return float(np.percentile(near[:, 2], 0.7)), float(np.percentile(near[:, 2], 99.3))


def elevation(
    points: np.ndarray,
    axis: int,
    position: float,
    along_lo: float,
    along_hi: float,
    look: float,
    depth: float = ELEVATION_DEPTH_M,
) -> np.ndarray:
    """A wall seen square-on: (along, z, depth) for everything in front of it.

    DEPTH IS RETURNED, not discarded. Flattening it was what made the first
    elevations unreadable: the wall, a wardrobe 400 mm proud of it, and the
    strip of floor within reach all landed in one grey mass with nothing to
    separate them. Depth is what tells an opening from a surface and a cabinet
    from the wall behind it.

    `look` is +1 or -1, the direction the viewer faces along `axis`. Returns
    `along` left-to-right as the viewer sees it, which is what stops an
    elevation coming out mirrored.
    """
    other = 1 - axis
    toward = (points[:, axis] - position) * look
    keep = (
        (toward > -0.06)
        & (toward < depth)
        & (points[:, other] > along_lo)
        & (points[:, other] < along_hi)
    )
    sub = points[keep]
    if not len(sub):
        return np.empty((0, 3))
    along = sub[:, other]
    if (axis == 0 and look > 0) or (axis == 1 and look < 0):
        along = -along
    return np.c_[along - along.min(), sub[:, 2], toward[keep]]


def depth_raster(
    elev: np.ndarray, cell: float = 0.02, z_lo: float = 0.0, z_hi: float = 2.70
) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Nearest-surface depth per cell, as an image with its extent.

    Nearest rather than mean: a cabinet front and the wall behind it fall in
    the same cell, and the front is what you see. Empty cells come back as NaN
    so an opening reads as a hole rather than as depth zero.
    """
    if not len(elev):
        return np.zeros((1, 1)), (0.0, 1.0, z_lo, z_hi)
    w = float(elev[:, 0].max())
    nx = max(2, int(w / cell))
    nz = max(2, int((z_hi - z_lo) / cell))
    ix = np.clip((elev[:, 0] / max(w, 1e-9) * (nx - 1)).astype(int), 0, nx - 1)
    iz = np.clip(((elev[:, 1] - z_lo) / max(z_hi - z_lo, 1e-9) * (nz - 1)).astype(int), 0, nz - 1)
    # Accumulate in -inf, NOT NaN. np.maximum propagates NaN, so a NaN-filled
    # image stays NaN at every cell it touches and the elevation renders blank.
    # Empty cells become NaN only afterwards, so an opening still reads as a
    # hole rather than as zero depth.
    img = np.full((nz, nx), -np.inf)
    np.maximum.at(img, (iz, ix), elev[:, 2])
    img[np.isinf(img)] = np.nan
    return img, (0.0, w, z_lo, z_hi)


def iso_matrix(azimuth_deg: float = 45.0, elevation_deg: float = 28.0) -> np.ndarray:
    a, e = np.deg2rad(azimuth_deg), np.deg2rad(elevation_deg)
    rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(e), -np.sin(e)], [0, np.sin(e), np.cos(e)]])
    return rx @ rz


def wall_quads(segments: list[dict], points: np.ndarray) -> list[dict]:
    """One solid per fitted face, over the height its own returns cover."""
    quads = []
    for segment in segments:
        if segment["length_m"] < MIN_SOLID_LENGTH_M:
            continue
        extent = face_extent(segment, points)
        if extent is None:
            continue
        base, top = extent
        if top - base < MIN_SOLID_HEIGHT_M:
            continue
        a, b = np.array(segment["a"], float), np.array(segment["b"], float)
        quads.append(
            {
                "corners": np.array(
                    [
                        [a[0], a[1], base],
                        [b[0], b[1], base],
                        [b[0], b[1], top],
                        [a[0], a[1], top],
                    ]
                ),
                "length_m": segment["length_m"],
                "base": round(base, 3),
                "top": round(top, 3),
            }
        )
    return quads


def project(corners: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    rotated = corners @ matrix.T
    return np.c_[rotated[:, 0], rotated[:, 2]]


def painter_order(quads: list[dict], matrix: np.ndarray) -> list[dict]:
    """Back to front. This IS the hidden-surface removal - opaque solids drawn
    in depth order occlude correctly without any visibility computation."""
    depths = [float((q["corners"] @ matrix.T)[:, 1].mean()) for q in quads]
    return [q for _, q in sorted(zip(depths, quads, strict=True), key=lambda pair: -pair[0])]
