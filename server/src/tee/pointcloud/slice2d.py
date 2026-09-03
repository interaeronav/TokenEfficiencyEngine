"""Sections and the tracing templates they become (doc 69 4.3).

A horizontal band through a levelled cloud is a floor plan waiting to be
traced. The fit turns a fuzzy 50 mm band of points into line segments a human
can draw over, and reports honestly how well those lines describe the points
they came from.

Residual is reported as MEDIAN first. The max over several thousand points
sits at ~4.7 sigma of the noise floor - arithmetically right, and read as a
failure by everyone who sees it (doc 69 4.3).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tee.kernel.errors import TeeError

MAX_SEGMENTS = 64  # the response cap is the design (acceptance A8)
LINE_TOL_M = 0.06
MIN_SEGMENT_POINTS = 40
MIN_SEGMENT_LEN_M = 0.25


def band(points: np.ndarray, z_m: float, thickness_m: float = 0.05) -> np.ndarray:
    """The 2D XY footprint of one horizontal slice."""
    half = float(thickness_m) / 2.0
    keep = np.abs(points[:, 2] - float(z_m)) <= half
    if keep.sum() < MIN_SEGMENT_POINTS:
        raise TeeError(
            "pc_empty_slice",
            f"Only {int(keep.sum())} points within {thickness_m * 1000:.0f} mm of z = {z_m:.3f} m.",
            fix="Check the level first (pc_level), or move z / widen thickness_m.",
        )
    return points[keep][:, :2]


def section_band(
    points: np.ndarray, p1_xy: list[float], p2_xy: list[float], thickness_m: float = 0.05
) -> np.ndarray:
    """A VERTICAL section along an arbitrary line: returns (along, z) pairs."""
    a = np.asarray(p1_xy, dtype=float)
    b = np.asarray(p2_xy, dtype=float)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 1e-6:
        raise TeeError(
            "pc_bad_section_line",
            "p1_xy and p2_xy are the same point.",
            fix="Give the section line two distinct XY endpoints.",
        )
    axis = axis / length
    normal = np.array([-axis[1], axis[0]])
    rel = points[:, :2] - a
    keep = np.abs(rel @ normal) <= float(thickness_m) / 2.0
    if keep.sum() < MIN_SEGMENT_POINTS:
        raise TeeError(
            "pc_empty_slice",
            f"Only {int(keep.sum())} points within {thickness_m * 1000:.0f} mm of the "
            "section line.",
            fix="Move the line onto the structure, or widen thickness_m.",
        )
    return np.c_[rel[keep] @ axis, points[keep][:, 2]]


def fit_lines(
    pts2d: np.ndarray, ortho_snap_deg: float = 3.0, max_segments: int = MAX_SEGMENTS
) -> tuple[list[dict], int]:
    """Greedy RANSAC line extraction. Returns (segments, points_ignored)."""
    remaining = pts2d.copy()
    segments: list[dict] = []
    rng = np.random.default_rng(0)

    while len(remaining) >= MIN_SEGMENT_POINTS and len(segments) < max_segments:
        best: tuple[int, np.ndarray, np.ndarray] | None = None
        for _ in range(200):
            i, j = rng.choice(len(remaining), 2, replace=False)
            a, b = remaining[i], remaining[j]
            direction = b - a
            norm = float(np.linalg.norm(direction))
            if norm < MIN_SEGMENT_LEN_M:
                continue
            direction = direction / norm
            normal = np.array([-direction[1], direction[0]])
            inliers = np.abs((remaining - a) @ normal) < LINE_TOL_M
            hits = int(inliers.sum())
            if best is None or hits > best[0]:
                best = (hits, inliers, direction)
        if best is None or best[0] < MIN_SEGMENT_POINTS:
            break

        _, inliers, direction = best
        member = remaining[inliers]
        # Re-select and refit, twice, with a shrinking tolerance. The RANSAC
        # seed is two noisy points, so its line sits up to a noise-sigma off
        # the true surface and its inlier set is correspondingly lop-sided;
        # fitting once inherits that bias. Measured: one pass left the room
        # 3.2 mm narrow against a +-2 mm gate, two passes 0.3 mm.
        centroid = member.mean(axis=0)
        for tol in (LINE_TOL_M, LINE_TOL_M * 0.6):
            _, _, vt = np.linalg.svd(member - centroid, full_matrices=False)
            direction = vt[0]
            normal = np.array([-direction[1], direction[0]])
            reselected = np.abs((remaining - centroid) @ normal) < tol
            if int(reselected.sum()) < MIN_SEGMENT_POINTS:
                break
            inliers = reselected
            member = remaining[inliers]
            centroid = member.mean(axis=0)
        _, _, vt = np.linalg.svd(member - centroid, full_matrices=False)
        direction = vt[0]
        angle = np.degrees(np.arctan2(direction[1], direction[0]))
        snapped_to = round(angle / 90.0) * 90.0
        if abs(angle - snapped_to) <= float(ortho_snap_deg):
            rad = np.deg2rad(snapped_to)
            direction = np.array([np.cos(rad), np.sin(rad)])
        normal = np.array([-direction[1], direction[0]])
        offsets = (member - centroid) @ normal
        centroid = centroid + normal * float(offsets.mean())
        along = (member - centroid) @ direction
        start = centroid + direction * float(along.min())
        end = centroid + direction * float(along.max())
        length = float(np.linalg.norm(end - start))
        residual = np.abs((member - centroid) @ normal) * 1000.0

        if length >= MIN_SEGMENT_LEN_M:
            segments.append(
                {
                    "a": [round(float(start[0]), 4), round(float(start[1]), 4)],
                    "b": [round(float(end[0]), 4), round(float(end[1]), 4)],
                    "length_m": round(length, 4),
                    "points": len(member),
                    "residual_median_mm": round(float(np.median(residual)), 1),
                    "residual_rms_mm": round(float(np.sqrt((residual**2).mean())), 1),
                    "residual_max_mm": round(float(residual.max()), 1),
                    "ortho_snapped": bool(abs(angle - snapped_to) <= float(ortho_snap_deg)),
                }
            )
        remaining = remaining[~inliers]
    return segments, len(remaining)


# -- writers ---------------------------------------------------------------


def write_dxf(segments: list[dict], out: Path, *, layer: str = "PC_TRACE") -> Path:
    """True-scale DXF in METRES. $INSUNITS = 6, verified (doc 69 3.3)."""
    import ezdxf

    doc = ezdxf.new("R2010", setup=False)
    doc.units = ezdxf.units.M  # -> $INSUNITS = 6
    doc.layers.add(layer)
    msp = doc.modelspace()
    for seg in segments:
        msp.add_lwpolyline([tuple(seg["a"]), tuple(seg["b"])], dxfattribs={"layer": layer})
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return out


def write_svg(segments: list[dict], out: Path, *, scale: str = "1:50") -> Path:
    """SVG at a declared paper scale, with a 1 m reference square and a bar.

    A template whose scale a reader cannot verify on the page is not a
    template, so both references are burned in.
    """
    try:
        denom = float(str(scale).split(":")[1])
    except (IndexError, ValueError) as exc:
        raise TeeError(
            "pc_bad_scale", f"'{scale}' is not a drawing scale.", fix="Use e.g. '1:50'."
        ) from exc

    pts = np.array([s["a"] for s in segments] + [s["b"] for s in segments], dtype=float)
    lo = pts.min(axis=0) - 0.5 if len(pts) else np.zeros(2)
    hi = pts.max(axis=0) + 0.5 if len(pts) else np.ones(2)
    mm_per_m = 1000.0 / denom
    width_mm = float(hi[0] - lo[0]) * mm_per_m
    height_mm = (float(hi[1] - lo[1]) + 1.2) * mm_per_m  # room for the legend

    def x(v: float) -> float:
        return (v - lo[0]) * mm_per_m

    def y(v: float) -> float:
        return height_mm - (v - lo[1]) * mm_per_m - 1.2 * mm_per_m

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm:.3f}mm" '
        f'height="{height_mm:.3f}mm" viewBox="0 0 {width_mm:.3f} {height_mm:.3f}">',
        f"<title>pc_slice trace template at {scale}</title>",
        '<g fill="none" stroke="#000" stroke-width="0.35">',
    ]
    for seg in segments:
        body.append(
            f'<line x1="{x(seg["a"][0]):.3f}" y1="{y(seg["a"][1]):.3f}" '
            f'x2="{x(seg["b"][0]):.3f}" y2="{y(seg["b"][1]):.3f}"/>'
        )
    body.append("</g>")
    base_y = height_mm - 0.35 * mm_per_m
    body.append(
        f'<rect x="{0.2 * mm_per_m:.3f}" y="{base_y - mm_per_m:.3f}" '
        f'width="{mm_per_m:.3f}" height="{mm_per_m:.3f}" fill="none" stroke="#c00" '
        'stroke-width="0.25"/>'
    )
    body.append(
        f'<text x="{0.2 * mm_per_m:.3f}" y="{base_y + 3:.3f}" font-size="3" '
        f'font-family="sans-serif">1 m reference square - scale {scale} - '
        "verify before tracing</text>"
    )
    body.append("</svg>")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(body))
    return out
