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
# A real room is not a clean rectangle. It has wall thickness, furniture,
# doorways and other rooms, and a RANSAC line scored purely on inlier count
# will happily run a 4 m diagonal through the clutter and call it a wall.
# Measured on the Okongo test scan (1.52 M points, two rooms): the unguarded
# fitter returned 35 segments totalling 133 m of wall inside a 5 x 5 m room.
# Two guards fix it, and both are architectural facts rather than tuning:
# a wall is CONTINUOUS along its length, and a surface found twice is one
# surface, not two.
GAP_M = 0.35  # a break longer than this ends the run (a doorway, or clutter)
OCCUPANCY_BIN_M = 0.10
MIN_OCCUPANCY = 0.65  # fraction of bins along the run that must hold points
DUPLICATE_OFFSET_M = 0.08  # nearer than this and it is the same surface refound


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


def fit_ortho(pts2d: np.ndarray, max_segments: int = MAX_SEGMENTS) -> tuple[list[dict], int]:
    """Fit AXIS-PARALLEL walls only, by peak-finding on each axis.

    An explicit declaration that the building is rectilinear, not an
    assumption: `pc_level` has already removed the wall azimuth, so in a
    rectilinear building every wall is parallel to X or Y and anything
    diagonal is furniture or a fitting artefact.

    Peak-finding beats RANSAC badly here. RANSAC scores a candidate on inlier
    count alone, so on the Okongo test scan it ran 4 m diagonals through a
    bed and a wardrobe and called them walls. A wall is instead a SPIKE in
    the histogram of perpendicular offsets - which is what a flat vertical
    surface actually is - and everything else never becomes a candidate.
    """
    segments: list[dict] = []
    used = np.zeros(len(pts2d), dtype=bool)
    for axis in (0, 1):
        other = 1 - axis
        coord = pts2d[:, axis]
        lo, hi = float(coord.min()), float(coord.max())
        bins = max(8, int((hi - lo) / 0.02))
        counts, edges = np.histogram(coord, bins=bins, range=(lo, hi))
        # A wall must stand well clear of the background clutter density.
        floor_level = max(MIN_SEGMENT_POINTS / 4.0, float(np.median(counts)) * 3.0)
        for i in range(1, len(counts) - 1):
            if counts[i] < floor_level:
                continue
            if counts[i] < counts[i - 1] or counts[i] < counts[i + 1]:
                continue  # keep local maxima only
            centre = float((edges[i] + edges[i + 1]) / 2)
            if any(
                abs(centre - s["_off"]) < DUPLICATE_OFFSET_M and s["_axis"] == axis
                for s in segments
            ):
                continue
            near = np.abs(coord - centre) < LINE_TOL_M
            if near.sum() < MIN_SEGMENT_POINTS:
                continue
            member = pts2d[near]
            centre = float(member[:, axis].mean())  # refit the surface position
            along = np.sort(member[:, other])
            residual = np.abs(member[:, axis] - centre) * 1000.0
            runs = np.split(np.arange(len(along)), np.nonzero(np.diff(along) > GAP_M)[0] + 1)
            for run in runs:
                if len(run) < MIN_SEGMENT_POINTS:
                    continue
                t0, t1 = float(along[run[0]]), float(along[run[-1]])
                run_length = t1 - t0
                if run_length < MIN_SEGMENT_LEN_M:
                    continue
                nbins = max(1, int(run_length / OCCUPANCY_BIN_M))
                slot = (along[run] - t0) / run_length * nbins * 0.999
                occupancy = len(np.unique(slot.astype(int))) / nbins
                if occupancy < MIN_OCCUPANCY:
                    continue
                a = [centre, t0] if axis == 0 else [t0, centre]
                b = [centre, t1] if axis == 0 else [t1, centre]
                segments.append(
                    {
                        "a": [round(v, 4) for v in a],
                        "b": [round(v, 4) for v in b],
                        "length_m": round(run_length, 4),
                        "points": len(run),
                        "residual_median_mm": round(float(np.median(residual)), 1),
                        "residual_rms_mm": round(float(np.sqrt((residual**2).mean())), 1),
                        "residual_max_mm": round(float(residual.max()), 1),
                        "occupancy": round(occupancy, 2),
                        "ortho_snapped": True,
                        "_off": centre,
                        "_axis": axis,
                    }
                )
            used |= near
    segments.sort(key=lambda s: -s["length_m"])
    for seg in segments:
        seg.pop("_off", None)
        seg.pop("_axis", None)
    return segments[:max_segments], int((~used).sum())


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
        residual = np.abs((member - centroid) @ normal) * 1000.0

        # Split the run wherever support breaks. A doorway genuinely ends one
        # length of wall and starts another; a diagonal through scattered
        # furniture is nothing but breaks.
        order = np.argsort(along)
        sorted_along = along[order]
        runs = np.split(
            np.arange(len(sorted_along)), np.nonzero(np.diff(sorted_along) > GAP_M)[0] + 1
        )
        for run in runs:
            if len(run) < MIN_SEGMENT_POINTS:
                continue
            t0, t1 = float(sorted_along[run[0]]), float(sorted_along[run[-1]])
            run_length = t1 - t0
            if run_length < MIN_SEGMENT_LEN_M:
                continue
            bins = max(1, int(run_length / OCCUPANCY_BIN_M))
            filled = len(
                np.unique(((sorted_along[run] - t0) / run_length * bins * 0.999).astype(int))
            )
            occupancy = filled / bins
            if occupancy < MIN_OCCUPANCY:
                continue
            run_residual = residual[order[run]]
            segments.append(
                {
                    "a": _round2(centroid + direction * t0),
                    "b": _round2(centroid + direction * t1),
                    "length_m": round(run_length, 4),
                    "points": len(run),
                    "residual_median_mm": round(float(np.median(run_residual)), 1),
                    "residual_rms_mm": round(float(np.sqrt((run_residual**2).mean())), 1),
                    "residual_max_mm": round(float(run_residual.max()), 1),
                    "occupancy": round(occupancy, 2),
                    "ortho_snapped": bool(abs(angle - snapped_to) <= float(ortho_snap_deg)),
                    "_dir": direction,
                    "_off": float(centroid @ normal),
                }
            )
        remaining = remaining[~inliers]

    segments = _drop_duplicate_surfaces(segments)
    segments.sort(key=lambda s: -s["length_m"])
    for seg in segments:
        seg.pop("_dir", None)
        seg.pop("_off", None)
    return segments[:max_segments], len(remaining)


def _round2(point: np.ndarray) -> list[float]:
    return [round(float(point[0]), 4), round(float(point[1]), 4)]


def _drop_duplicate_surfaces(segments: list[dict]) -> list[dict]:
    """One physical surface found twice is one surface.

    Wall THICKNESS is real and must survive - the two faces of a 260 mm
    partition are two genuine segments - so only near-coincident parallel
    runs are merged, and the better-supported one wins.
    """
    kept: list[dict] = []
    for seg in sorted(segments, key=lambda s: -s["points"]):
        direction = seg["_dir"]
        duplicate = False
        for other in kept:
            if abs(float(direction @ other["_dir"])) < 0.996:  # more than ~5 deg apart
                continue
            if abs(seg["_off"] - other["_off"]) > DUPLICATE_OFFSET_M:
                continue
            span = [np.array(seg["a"]) @ direction, np.array(seg["b"]) @ direction]
            other_span = [np.array(other["a"]) @ direction, np.array(other["b"]) @ direction]
            overlap = min(max(span), max(other_span)) - max(min(span), min(other_span))
            if overlap > 0.3 * min(seg["length_m"], other["length_m"]):
                duplicate = True
                break
        if not duplicate:
            kept.append(seg)
    return kept


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
