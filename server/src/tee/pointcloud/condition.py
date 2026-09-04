"""Cropping and cleaning: get rid of what is not the building.

Both of these earn their place on the Okongo scan. `pc_slice` reported 3,843
points it could not fit to any wall, and the honest advice in that response is
"crop and re-run" - which was not possible until now. And the wall fits carry
outlier tails from a scanner that sees through doorways into the next room.

Every operation mints a new cloud and records what it dropped. Nothing is
removed in place, so a crop that took too much is one id away from being undone.
"""

from __future__ import annotations

import numpy as np

from tee.kernel.errors import TeeError

SOR_K = 16
SOR_STD = 2.0
MIN_KEEP = 100


def crop_box(points: np.ndarray, box: list[float]) -> np.ndarray:
    """Keep points inside an axis-aligned box [x0,y0,z0, x1,y1,z1]."""
    if len(box) != 6:
        raise TeeError(
            "pc_bad_box",
            f"A box needs six numbers, got {len(box)}.",
            fix="Pass [x0, y0, z0, x1, y1, z1] in metres.",
        )
    lo = np.minimum(box[:3], box[3:])
    hi = np.maximum(box[:3], box[3:])
    return np.all((points >= lo) & (points <= hi), axis=1)


def crop_z(points: np.ndarray, z_range: list[float]) -> np.ndarray:
    if len(z_range) != 2:
        raise TeeError(
            "pc_bad_z_range",
            f"A z range needs two numbers, got {len(z_range)}.",
            fix="Pass [z_min, z_max] in metres.",
        )
    lo, hi = sorted(z_range)
    return (points[:, 2] >= lo) & (points[:, 2] <= hi)


def crop_polygon(points: np.ndarray, polygon: list[list[float]]) -> np.ndarray:
    """Keep points whose XY falls inside a polygon, by ray casting.

    Written out rather than pulled from shapely: it is twenty lines, it runs on
    the whole cloud at once, and it saves the lane a dependency it would
    otherwise carry for this alone.
    """
    poly = np.asarray(polygon, dtype=float)
    if poly.ndim != 2 or poly.shape[1] != 2 or len(poly) < 3:
        raise TeeError(
            "pc_bad_polygon",
            "A polygon needs at least three [x, y] vertices.",
            fix="Pass [[x, y], [x, y], [x, y], ...] in metres.",
        )
    x, y = points[:, 0], points[:, 1]
    inside = np.zeros(len(points), dtype=bool)
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        straddles = (yi > y) != (yj > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            crossing = xi + (y - yi) * (xj - xi) / np.where(yj - yi == 0, np.nan, yj - yi)
        inside ^= straddles & (x < crossing)
        j = i
    return inside


def statistical_outliers(
    points: np.ndarray, k: int = SOR_K, std_mul: float = SOR_STD, seed: int = 0
) -> np.ndarray:
    """Mask of points to KEEP: those whose neighbourhood is not unusually sparse.

    The threshold comes from the cloud's own distribution, not from a fixed
    distance, so the same call works on a 15 mm room scan and a 100 mm site
    scan without being re-tuned.
    """
    from scipy.spatial import cKDTree

    if len(points) <= k:
        return np.ones(len(points), dtype=bool)
    tree = cKDTree(points)
    distances, _ = tree.query(points, k=min(k, len(points) - 1) + 1, workers=-1)
    mean_distance = distances[:, 1:].mean(axis=1)
    limit = float(mean_distance.mean() + std_mul * mean_distance.std())
    return mean_distance <= limit


def voxel_downsample(points: np.ndarray, voxel_m: float) -> np.ndarray:
    """Indices of one representative point per occupied voxel.

    The point NEAREST its voxel centroid, not the centroid itself: a returned
    point is a thing the scanner saw, and an averaged one is not. On a wall the
    difference is nothing; across an edge the average floats in mid-air.
    """
    if voxel_m <= 0:
        raise TeeError(
            "pc_bad_voxel", "voxel_m must be positive.", fix="Try 0.02 for a 20 mm grid."
        )
    keys = np.floor(points / voxel_m).astype(np.int64)
    _, inverse = np.unique(keys, axis=0, return_inverse=True)
    order = np.argsort(inverse, kind="stable")
    sorted_inverse = inverse[order]
    starts = np.flatnonzero(np.r_[True, sorted_inverse[1:] != sorted_inverse[:-1]])
    groups = np.split(order, starts[1:])
    keep = np.empty(len(groups), dtype=np.int64)
    for i, group in enumerate(groups):
        block = points[group]
        keep[i] = group[int(np.argmin(((block - block.mean(axis=0)) ** 2).sum(axis=1)))]
    return keep


def out_of_range(points: np.ndarray, axis: int, lo: float, hi: float) -> str | None:
    """Say so when a requested range reaches past the cloud, and by how much.

    Found by driving this on the real Okongo scan: a z_range of 0.05-2.35 m
    looked like "everything from just above the floor to just below the
    ceiling" and returned the top HALF of the room, because a PLY round trip
    origin-shifts and that cloud's floor sits at z = -1.36. The crop was
    correct and the request was not, and nothing in the answer said so. This
    is the line that does.
    """
    low, high = float(points[:, axis].min()), float(points[:, axis].max())
    name = "xyz"[axis]
    if lo <= low and hi >= high:
        return None
    span = f"({name} is {low:.3f}..{high:.3f})"
    if lo > high or hi < low:
        return f"{name} {lo:g}..{hi:g} does not meet this cloud at all {span}."
    if lo < low or hi > high:
        return f"{name} {lo:g}..{hi:g} reaches past this cloud {span}."
    return None


def guard_survivors(kept: int, name: str) -> None:
    if kept < MIN_KEEP:
        raise TeeError(
            "pc_crop_too_aggressive",
            f"{name} would leave {kept} points, which is not a cloud.",
            fix="Widen the region, or check the units - the cloud is in metres.",
        )
