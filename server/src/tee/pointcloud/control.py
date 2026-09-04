"""Control baselines and scale - the accuracy spine (doc 69 1).

Phone LiDAR and video SfM drift. Dimensions must come from a tape; the cloud
supplies the shape between them. This is the input A42 T6 did not have: its
7-DOF ICP collapsed (scale -> 0, RMS 15 um) and the honest fallback was to
borrow scale from the design envelope, because the tape measurements the
field protocol collects had nowhere to go.

Baselines disagreeing by more than their tolerance are DRIFT, not scale. No
single factor fixes drift, and saying so is more useful than a number.
"""

from __future__ import annotations

import numpy as np

from tee.kernel.errors import TeeError

# The snap patch must be big enough to average the scanner's noise down.
# Measured on the 12 mm-noise fixture: a 0.15 m patch (~310 points) left the
# 4 m baseline 2.0 mm long = 503 ppm, failing the 500 ppm gate; 0.25 m
# (~860 points) lands at 0.3 mm = 78 ppm. The plane's standard error goes as
# sigma/sqrt(n), so this is a sample-size floor, not a taste knob.
SNAP_RADIUS_M = 0.30
SNAP_MIN_POINTS = 400
SNAP_MAX_RADIUS_M = 1.20
# Below this share of the neighbourhood on the snapped plane, the pick is in
# front of something and the reading is not to be trusted.
CLEAR_PICK = 0.60
# doc 18 Rec. 5, reused: a free-scale deviation past this is a units problem,
# not a calibration - reported as a conflict rather than silently applied.
UNITS_CONFLICT = 0.02


def snap_to_surface(
    points: np.ndarray, pick: np.ndarray, radius: float = SNAP_RADIUS_M
) -> tuple[np.ndarray, int, float]:
    """Move an approximate 3D pick onto the local dominant plane.

    The operator aims by eye at a wall in a viewer; this is what makes that
    good enough. Returns (snapped point, neighbours used).
    """
    from scipy.spatial import cKDTree

    tree = cKDTree(points)
    # Grow the patch until it holds enough points to average the noise down.
    # A sparse scan needs a wider ball than a dense one for the same accuracy.
    idx: list[int] = []
    while radius <= SNAP_MAX_RADIUS_M:
        idx = tree.query_ball_point(pick, radius)
        if len(idx) >= SNAP_MIN_POINTS:
            break
        radius *= 1.6
    if len(idx) < 3:
        idx = np.atleast_1d(tree.query(pick, k=min(64, len(points)))[1]).tolist()
    local = points[np.asarray(idx, dtype=int)]
    if len(local) < 3:
        return np.asarray(pick, dtype=float), len(local)
    # Re-select and refit, the same discipline the line fitter needs. A single
    # SVD over everything in the ball is biased by whatever else is within the
    # radius - a bedhead 200 mm off the wall drags the plane with it, and the
    # snap lands tens of millimetres inside the surface it was aiming at.
    centroid = local.mean(axis=0)
    normal = np.array([0.0, 0.0, 1.0])
    for tol in (radius * 0.5, 0.06, 0.03):
        _, _, vt = np.linalg.svd(local - centroid, full_matrices=False)
        normal = vt[-1]
        # The surface is the PEAK of the offset histogram, not the mean of it.
        # Averaging puts the plane somewhere between the wall and whatever
        # stands in front of it: measured on the Okongo scan, a least-squares
        # snap between two curtained walls read 3790 mm where the walls are
        # 3963 mm apart - a 173 mm error that made the tool useless exactly
        # where a control baseline matters most. A wall is the densest return
        # in its own neighbourhood; a curtain is not.
        offsets = (local - centroid) @ normal
        counts, edges = np.histogram(offsets, bins=max(12, int(radius / 0.01)))
        peak = float((edges[counts.argmax()] + edges[counts.argmax() + 1]) / 2)
        keep = np.abs(offsets - peak) < tol
        if int(keep.sum()) < max(SNAP_MIN_POINTS // 8, 20):
            centroid = centroid + normal * peak
            break
        local = local[keep]
        centroid = local.mean(axis=0)
    snapped = np.asarray(pick, dtype=float)
    on_plane = snapped - normal * float((snapped - centroid) @ normal)
    # How much of the neighbourhood actually sits on the surface we snapped to.
    # A pick in front of a curtain still returns a plane; without this number
    # nothing distinguishes it from a pick on bare wall, and the resulting
    # baseline is short by tens of millimetres with no sign that it is wrong.
    ball = points[np.linalg.norm(points - np.asarray(pick, float), axis=1) < radius]
    confidence = float((np.abs((ball - on_plane) @ normal) < 0.03).mean()) if len(ball) else 0.0
    return on_plane, len(local), confidence


def add_baseline(
    points: np.ndarray,
    name: str,
    p1: list[float],
    p2: list[float],
    true_mm: float,
    tol_mm: float = 5.0,
) -> dict:
    """Record one tape baseline, snapping both picks to their local surfaces."""
    if float(true_mm) <= 0:
        raise TeeError(
            "pc_bad_baseline",
            "true_mm must be the positive distance you measured.",
            fix="Pass the tape reading in millimetres.",
        )
    a, na, ca = snap_to_surface(points, np.asarray(p1, dtype=float))
    b, nb, cb = snap_to_surface(points, np.asarray(p2, dtype=float))
    measured_mm = float(np.linalg.norm(b - a) * 1000.0)
    if measured_mm < 1.0:
        raise TeeError(
            "pc_degenerate_baseline",
            f"'{name}' snapped to a {measured_mm:.2f} mm length - the two picks coincide.",
            fix="Pick two points on OPPOSITE surfaces, in cloud units (metres).",
        )
    out = {
        "name": str(name)[:64],
        "p1": [round(float(v), 4) for v in a],
        "p2": [round(float(v), 4) for v in b],
        "true_mm": round(float(true_mm), 2),
        "measured_mm": round(measured_mm, 2),
        "tol_mm": round(float(tol_mm), 2),
        "snapped_from": [round(float(v), 4) for v in p1] != [round(float(v), 4) for v in a],
        "neighbours": [int(na), int(nb)],
        "confidence": [round(ca, 2), round(cb, 2)],
    }
    if min(ca, cb) < CLEAR_PICK:
        out["warning"] = (
            f"only {min(ca, cb):.0%} of the neighbourhood at one end sits on the "
            "surface it snapped to - the pick is in front of clutter, and the "
            "baseline will read SHORT."
        )
        out["fix"] = "Move that pick to a clear length of bare wall and re-add."
    return out


def check(baselines: list[dict]) -> dict:
    """Compare every baseline against its tape reading; suggest one scale."""
    if not baselines:
        raise TeeError(
            "pc_no_baselines",
            "No control baselines recorded on this cloud.",
            fix="Add at least one with pc_control_add before checking scale.",
        )
    rows = []
    for base in baselines:
        measured = float(base["measured_mm"])
        true = float(base["true_mm"])
        delta = measured - true
        rows.append(
            {
                "name": base["name"],
                "measured_mm": round(measured, 2),
                "true_mm": round(true, 2),
                "delta_mm": round(delta, 2),
                "ppm": round(delta / true * 1e6, 1),
                "factor": true / measured,
            }
        )
    factors = np.array([r["factor"] for r in rows])
    # Least-squares over the ratios: one uniform factor, the honest kind.
    factor = float(np.exp(np.log(factors).mean()))
    residuals_ppm = [abs(f - factor) / factor * 1e6 for f in factors]
    worst = max(rows, key=lambda r: abs(r["delta_mm"]))

    out: dict = {
        "baselines": [{k: v for k, v in r.items() if k != "factor"} for r in rows[:24]],
        "suggested_scale": round(factor, 7),
        "scale_residual_ppm": round(max(residuals_ppm), 1),
        "worst_offender": worst["name"],
        "worst_delta_mm": worst["delta_mm"],
    }
    if len(rows) > 24:
        out["truncated"] = f"{len(rows) - 24} more baselines not listed"

    if abs(factor - 1.0) > UNITS_CONFLICT:
        out["units_conflict"] = (
            f"The fitted scale is {factor:.4f}, more than {UNITS_CONFLICT:.0%} from 1.0. "
            "That is a units problem, not a calibration one."
        )
        out["fix"] = "Re-open the cloud with an explicit units= (mm, cm, ft) rather than scaling."

    # Drift is the failure a single factor CANNOT fix. Say so.
    if len(rows) > 1:
        corrected = [abs(r["measured_mm"] * factor - r["true_mm"]) for r in rows]
        tols = [float(b["tol_mm"]) for b in baselines]
        offenders = [rows[i]["name"] for i, c in enumerate(corrected) if c > tols[i]]
        if offenders:
            out["drift"] = (
                f"{len(offenders)} baseline(s) stay outside tolerance after the best "
                f"single scale: {', '.join(offenders[:4])}. That is drift, not scale."
            )
            out["fix"] = (
                "No uniform factor fixes drift. Re-register from smaller scans, or crop to "
                "the region your baselines actually cover."
            )
    return out
