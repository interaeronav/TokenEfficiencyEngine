"""Levelling and orientation - the measured algorithm from doc 69 4.

Two findings are load-bearing here and both were measured, not reasoned:

* Floor and ceiling are EQUALLY dominant in a box room, so "most inliers"
  is a coin flip. The tie-break is the lowest median z among the planes
  that clear the inlier threshold.
* Normals must be estimated in 3D. In the XY projection, 12 mm of noise on
  a 15 mm sample grid is isotropic - a 2D estimator kept 6 neighbourhoods
  out of 40,000 and returned 26 degrees of error. In 3D at k>=80 the same
  data gives 0.004 degrees.
"""

from __future__ import annotations

import numpy as np

from tee.kernel.errors import TeeError

HORIZONTAL_DOT = 0.95  # |n_z| above this is "near-horizontal"
PLANE_TOL_M = 0.03
RANSAC_ITERS = 400
# A floor spans its room. This is what separates it from a table top, and it
# is scale-free where an inlier-count threshold is not.
MIN_FOOTPRINT_FRACTION = 0.25
# A seed neighbourhood must be flat, or it is a corner and its normal is a lie.
# Measured on the synthetic fixture: a genuinely flat patch scores 0.28-0.38
# (12 mm of noise across a ~70 mm neighbourhood), a corner scores far higher.
PATCH_FLATNESS = 0.50
NORMAL_K = 160  # doc 69 4.2: k=160 -> 0.004 deg, k=20 -> 0.073 deg
WALL_BAND_M = (0.4, 2.3)
VERTICAL_DOT = 0.25  # |n_z| below this is "near-vertical"
PLANARITY = 0.5


def fit_plane(points: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Least-squares plane through points. Returns (normal, centroid, rms_m)."""
    centroid = points.mean(axis=0)
    _, _, vt = np.linalg.svd(points - centroid, full_matrices=False)
    normal = vt[-1]
    if normal[2] < 0:
        normal = -normal
    rms = float(np.sqrt((((points - centroid) @ normal) ** 2).mean()))
    return normal, centroid, rms


def dominant_floor(
    points: np.ndarray, *, floor_hint_z: float | None = None, seed: int = 0
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    """RANSAC the floor plane. Returns (normal, centroid, rms_m, inlier_mask).

    Prefers the LOWEST qualifying horizontal plane, not the most populous -
    a ceiling has just as many points as the floor it mirrors.
    """
    rng = np.random.default_rng(seed)
    if floor_hint_z is not None:
        near = np.abs(points[:, 2] - float(floor_hint_z)) < 0.25
        if near.sum() >= 100:
            normal, centroid, _ = fit_plane(points[near])
            mask = np.abs((points - centroid) @ normal) < PLANE_TOL_M
            normal, centroid, rms = fit_plane(points[mask])
            return normal, centroid, rms, mask

    floor_min = max(100, len(points) // 200)
    # Hypothesise planes from LOCAL PATCHES, not from three random points.
    # Three uniform samples must all land on the same surface to describe it,
    # and on a real capture that is a lottery: the floor is 8.5% of the mesh
    # of the Okongo second scan, so P(all three) is about 0.06% per iteration
    # and 400 iterations found the CEILING instead - which has more area
    # because the floor is under the furniture. One seed point plus its own
    # neighbourhood is a real surface hypothesis every time.
    from scipy.spatial import cKDTree

    sample_n = min(len(points), 120_000)
    sample_idx = rng.choice(len(points), sample_n, replace=False)
    sample = points[sample_idx]
    tree = cKDTree(sample)
    k = min(48, len(sample) - 1)
    seeds = rng.choice(len(sample), min(RANSAC_ITERS, len(sample)), replace=False)
    _, neighbourhoods = tree.query(sample[seeds], k=k, workers=-1)

    candidates: dict[int, tuple[int, float, np.ndarray]] = {}
    for row in neighbourhoods:
        patch = sample[row]
        centroid = patch.mean(axis=0)
        _, sv, vt = np.linalg.svd(patch - centroid, full_matrices=False)
        # The patch must actually BE flat. A neighbourhood that straddles a
        # corner mixes floor and wall and yields a normal belonging to
        # neither, which is how a diagonal slab through a tilted room came to
        # be preferred over the floor.
        if sv[1] <= 1e-9 or sv[2] / sv[1] > PATCH_FLATNESS:
            continue
        normal = vt[-1]
        if abs(normal[2]) < HORIZONTAL_DOT:
            continue
        if normal[2] < 0:
            normal = -normal
        mask = np.abs((points - centroid) @ normal) < PLANE_TOL_M
        hits = int(mask.sum())
        if hits < floor_min:
            continue
        height = float(np.median(points[mask][:, 2]))
        bucket = round(height / (2 * PLANE_TOL_M))
        prior = candidates.get(bucket)
        if prior is None or hits > prior[0]:
            candidates[bucket] = (hits, height, mask)
    if not candidates:
        raise TeeError(
            "pc_no_floor_plane",
            "No dominant near-horizontal plane found - the cloud may be on its side.",
            fix="Pass up_axis to pc_open, or floor_hint_z to pc_level.",
        )
    # The floor is the lowest plane that is genuinely a FLOOR, and what makes
    # it one is FOOTPRINT, not popularity. Filtering candidates by "at least
    # half the inliers of the biggest plane" fails exactly where it matters:
    # a floor under furniture is scanned far less than the open ceiling above
    # it, so the real floor gets discarded as noise and the room is levelled
    # upside down. Spanning the room is the test; a tabletop cannot pass it.
    span = points[:, :2].max(axis=0) - points[:, :2].min(axis=0)
    footprint = float(span[0] * span[1]) or 1.0
    real = []
    for hits, height, mask in candidates.values():
        inliers = points[mask][:, :2]
        extent = inliers.max(axis=0) - inliers.min(axis=0)
        if float(extent[0] * extent[1]) >= MIN_FOOTPRINT_FRACTION * footprint:
            real.append((hits, height, mask))
    if not real:  # nothing spans the room: fall back to the most populous
        real = [max(candidates.values(), key=lambda c: c[0])]
    mask = min(real, key=lambda c: c[1])[2]
    normal, centroid, rms = fit_plane(points[mask])
    mask = np.abs((points - centroid) @ normal) < PLANE_TOL_M
    normal, centroid, rms = fit_plane(points[mask])
    return normal, centroid, rms, mask


def rotation_to_z(normal: np.ndarray) -> np.ndarray:
    """Rodrigues rotation taking `normal` onto +Z."""
    target = np.array([0.0, 0.0, 1.0])
    v = np.cross(normal, target)
    s = float(np.linalg.norm(v))
    c = float(normal @ target)
    if s < 1e-12:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    k = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + k + k @ k * ((1 - c) / s**2)


def wall_azimuth(points: np.ndarray, *, k: int = NORMAL_K, seed: int = 0) -> float | None:
    """Dominant wall azimuth in degrees, mod 90, from 3D normals.

    Estimated over the FULL-HEIGHT wall band - never a thin slice, which
    measured 1.289 deg of error against a 0.5 deg gate (doc 69 4.2).
    """
    from scipy.spatial import cKDTree

    band = points[(points[:, 2] > WALL_BAND_M[0]) & (points[:, 2] < WALL_BAND_M[1])]
    if len(band) < k * 4:
        band = points
    if len(band) < max(64, k):
        return None
    rng = np.random.default_rng(seed)
    if len(band) > 30_000:
        band = band[rng.choice(len(band), 30_000, replace=False)]
    kk = min(k, len(band) - 1)
    _, idx = cKDTree(band).query(band, k=kk, workers=-1)
    nb = band[idx]
    nb = nb - nb.mean(axis=1, keepdims=True)
    cov = np.einsum("nij,nik->njk", nb, nb) / kk
    evals, evecs = np.linalg.eigh(cov)
    normals = evecs[:, :, 0]
    planarity = (evals[:, 1] - evals[:, 0]) / np.maximum(evals[:, 2], 1e-12)
    keep = (np.abs(normals[:, 2]) < VERTICAL_DOT) & (planarity > PLANARITY)
    if keep.sum() < 32:
        return None
    ang = np.degrees(np.arctan2(normals[keep][:, 1], normals[keep][:, 0])) % 90.0
    # circular mean on the mod-90 wrap: multiply the angle by 4 to reach 360
    theta = np.deg2rad(ang * 4.0)
    mean = np.degrees(np.arctan2(np.sin(theta).mean(), np.cos(theta).mean())) / 4.0
    return float(mean % 90.0)


def level(
    points: np.ndarray, *, floor_hint_z: float | None = None, align_walls: bool = True
) -> dict:
    """Level the cloud and square it to the dominant wall.

    Returns the 4x4 transform plus the numbers that say whether to trust it.
    """
    normal, _centroid, rms, mask = dominant_floor(points, floor_hint_z=floor_hint_z)
    r1 = rotation_to_z(normal)
    levelled = points @ r1.T
    floor_z = float(np.median((points[mask] @ r1.T)[:, 2]))
    levelled[:, 2] -= floor_z

    azimuth = wall_azimuth(levelled) if align_walls else None
    rot = r1
    if azimuth is not None:
        rad = np.deg2rad(-azimuth)
        rz = np.array([[np.cos(rad), -np.sin(rad), 0], [np.sin(rad), np.cos(rad), 0], [0, 0, 1]])
        levelled = levelled @ rz.T
        rot = rz @ r1

    matrix = np.eye(4)
    matrix[:3, :3] = rot
    matrix[:3, 3] = [0.0, 0.0, -floor_z]
    residual = float(np.degrees(np.arccos(np.clip(float((rot @ normal) @ [0, 0, 1]), -1, 1))))
    return {
        "points": levelled,
        "matrix": [round(float(v), 8) for v in matrix.flatten()],
        "residual_tilt_deg": round(residual, 4),
        "floor_rms_mm": round(rms * 1000, 2),
        "floor_points": int(mask.sum()),
        "wall_azimuth_deg": None if azimuth is None else round(azimuth, 3),
    }
