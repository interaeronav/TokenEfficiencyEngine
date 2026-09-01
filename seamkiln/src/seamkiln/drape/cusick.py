"""The Cusick drape test, simulated - a ruler for "does the cloth behave".

BS 5058 / ISO 9073-9 is the textile industry's drape measurement: a circular
specimen 300 mm across is laid over a 180 mm disc, the unsupported ring falls
into folds, and a parallel light casts its shadow onto paper. The **drape
coefficient** is

    DC = (shadow area - disc area) / (specimen area - disc area)

A perfectly stiff cloth does not fall at all and its shadow is the whole
specimen: DC = 1. A perfectly limp one collapses to the disc: DC = 0. Real
fabrics land in between, and the ordering - denim stiff, chiffon limp - is
the thing a cloth simulator has to get right before any of its other claims
mean anything.

Running it here is what makes "true-to-life physics" a measurement rather
than an adjective. The specimen is a real panel, the disc is a real solid,
the shadow is computed the way the instrument computes it - by projection -
and the number that comes out is comparable with a laboratory's.

The comparison has an honest limit, stated once: seamkiln's bundled fabric
cards are tier `plausible`, so a DC computed from them tests the SOLVER's
ordering and range, not the cloth. Feed it a measured card and the number
becomes a claim about the fabric too.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from seamkiln.pattern.geometry import Vertex, VertexKind
from seamkiln.pattern.model import Panel, Pattern

SPECIMEN_DIAMETER_MM = 300.0
DISC_DIAMETER_MM = 180.0


def specimen(diameter_mm: float = SPECIMEN_DIAMETER_MM, *, segments: int = 180) -> Pattern:
    """The circular test specimen, as a one-panel pattern."""
    radius = diameter_mm / 2.0
    ring = [
        Vertex(
            radius * math.cos(2 * math.pi * k / segments),
            radius * math.sin(2 * math.pi * k / segments),
            VertexKind.CURVE,
        )
        for k in range(segments)
    ]
    return Pattern(name=f"cusick-{diameter_mm:.0f}mm", panels=[Panel(id="SPECIMEN", outline=ring)])


@dataclass(slots=True)
class DrapeCoefficient:
    value: float
    shadow_mm2: float
    specimen_mm2: float
    disc_mm2: float
    node_count: int
    fold_depth_mm: float

    def verdict(self) -> str:
        """The scale a drape lab reads it on."""
        if self.value >= 0.80:
            return "very stiff"
        if self.value >= 0.65:
            return "stiff"
        if self.value >= 0.45:
            return "medium"
        if self.value >= 0.30:
            return "limp"
        return "very limp"

    def as_dict(self) -> dict[str, Any]:
        return {
            "drape_coefficient": round(self.value, 4),
            "verdict": self.verdict(),
            "shadow_mm2": round(self.shadow_mm2, 1),
            "specimen_mm2": round(self.specimen_mm2, 1),
            "disc_mm2": round(self.disc_mm2, 1),
            "nodes": self.node_count,
            "fold_depth_mm": round(self.fold_depth_mm, 2),
            "standard": "BS 5058 / ISO 9073-9",
        }


def shadow_area_mm2(points: np.ndarray, triangles: np.ndarray, *, resolution: int = 900) -> float:
    """The projected area, computed the way the instrument computes it.

    Rasterised rather than unioned: the drapemeter casts a parallel light and
    traces the outline on paper, so coverage on a fine grid is a closer model
    of the instrument than a polygon union - and it cannot trip over the
    self-intersections a folded specimen's projection is full of.
    """
    flat = np.asarray(points, dtype=np.float64)[:, [0, 2]] * 1000.0  # metres -> mm
    low = flat.min(axis=0)
    high = flat.max(axis=0)
    span = np.maximum(high - low, 1e-9)
    cell = float(span.max()) / resolution
    width = int(np.ceil(span[0] / cell)) + 1
    height = int(np.ceil(span[1] / cell)) + 1
    covered = np.zeros((width, height), dtype=bool)

    grid = (flat - low) / cell
    for tri in triangles:
        a, b, c = grid[tri[0]], grid[tri[1]], grid[tri[2]]
        x0 = max(int(np.floor(min(a[0], b[0], c[0]))), 0)
        x1 = min(int(np.ceil(max(a[0], b[0], c[0]))) + 1, width)
        y0 = max(int(np.floor(min(a[1], b[1], c[1]))), 0)
        y1 = min(int(np.ceil(max(a[1], b[1], c[1]))) + 1, height)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = np.arange(x0, x1) + 0.5
        ys = np.arange(y0, y1) + 0.5
        px, py = np.meshgrid(xs, ys, indexing="ij")
        # barycentric sign test, vectorised over the triangle's own bbox
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        u = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / d
        w = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / d
        inside = (u >= 0) & (w >= 0) & (u + w <= 1)
        covered[x0:x1, y0:y1] |= inside
    return float(covered.sum()) * cell * cell


def count_nodes(points: np.ndarray, *, disc_radius_mm: float = DISC_DIAMETER_MM / 2) -> int:
    """How many folds the specimen fell into.

    A drape lab counts nodes by eye off the traced outline. Here: walk the
    outer boundary by angle, take the radius, and count the local maxima -
    the same thing, done arithmetically.
    """
    coords = np.asarray(points, dtype=np.float64) * 1000.0
    # A node is a FOLD, and a fold has depth. A specimen that has not fallen
    # has none, however much its polygonal outline wobbles - and a peak finder
    # run over an almost-constant radius profile happily reports twenty.
    if float(coords[:, 1].max() - coords[:, 1].min()) < 2.0:
        return 0
    flat = coords[:, [0, 2]]
    radius = np.linalg.norm(flat, axis=1)
    outer = radius > disc_radius_mm * 1.02
    if outer.sum() < 24:
        return 0
    angle = np.arctan2(flat[outer, 1], flat[outer, 0])
    order = np.argsort(angle)
    profile = radius[outer][order]
    bins = 180
    binned = np.array(
        [
            profile[int(k * len(profile) / bins) : max(int((k + 1) * len(profile) / bins), 1)].max()
            if int((k + 1) * len(profile) / bins) > int(k * len(profile) / bins)
            else 0.0
            for k in range(bins)
        ]
    )
    smooth = np.convolve(np.r_[binned[-4:], binned, binned[:4]], np.ones(5) / 5, "same")[4:-4]
    # A flat specimen has a CONSTANT radius profile, and a peak finder run
    # over a constant signal happily reports thirty-four folds of
    # rasterisation noise. A fold is a real excursion or it is not a fold:
    # require the profile to vary by more than 3% of its own mean before any
    # peak counts, and then only count peaks that clear a quarter of the way
    # to the maximum.
    mean = float(smooth.mean())
    if mean <= 0.0:
        return 0
    swing = float(smooth.max() - smooth.min())
    if swing < 0.05 * mean:
        return 0
    threshold = mean + 0.25 * (float(smooth.max()) - mean)
    rolled_prev = np.roll(smooth, 1)
    rolled_next = np.roll(smooth, -1)
    peaks = (smooth > rolled_prev) & (smooth >= rolled_next) & (smooth >= threshold)
    return int(peaks.sum())


def drape_coefficient(
    points: np.ndarray,
    triangles: np.ndarray,
    *,
    specimen_diameter_mm: float = SPECIMEN_DIAMETER_MM,
    disc_diameter_mm: float = DISC_DIAMETER_MM,
) -> DrapeCoefficient:
    specimen_area = math.pi * (specimen_diameter_mm / 2.0) ** 2
    disc_area = math.pi * (disc_diameter_mm / 2.0) ** 2
    shadow = shadow_area_mm2(points, triangles)
    value = (shadow - disc_area) / max(specimen_area - disc_area, 1e-9)
    heights = np.asarray(points, dtype=np.float64)[:, 1] * 1000.0
    return DrapeCoefficient(
        value=float(np.clip(value, 0.0, 1.5)),
        shadow_mm2=shadow,
        specimen_mm2=specimen_area,
        disc_mm2=disc_area,
        node_count=count_nodes(points, disc_radius_mm=disc_diameter_mm / 2),
        fold_depth_mm=float(heights.max() - heights.min()),
    )
