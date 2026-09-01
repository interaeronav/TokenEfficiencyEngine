"""Lacing: eyelets, a lace path, and a lace that actually pulls.

A lace is not decoration drawn over a garment - it is a load path. Tightening
one closes the opening it threads, and the cloth between the eyelets gathers
into the scallops anyone who has laced a boot would recognise. So a lace here
is BUILT as geometry (eyelets on the pattern, a path between them) and
SIMULATED as constraints (each threaded span pulls its two eyelets together
by however much the lace was tightened).

Three lace styles, because they pull differently and that is the point:
  criss-cross   the common one; each span crosses, so tightening also shears
  straight-bar  parallel rungs; pulls square, no shear
  spiral        one continuous helix; pulls unevenly, which is why it is
                usually a mistake on a boot and deliberate on a corset
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh

STYLES = ("criss-cross", "straight-bar", "spiral")


@dataclass(slots=True)
class Eyelets:
    """Where a lace passes through the cloth."""

    indices: np.ndarray  # int64 [n] - particle indices
    positions: np.ndarray  # float64 [n, 3]
    panel: str = ""
    side: str = ""

    def __len__(self) -> int:
        return int(self.indices.shape[0])


@dataclass(slots=True)
class Lace:
    """A threaded lace: its path, its constraints, and how tight it is."""

    spans: np.ndarray  # int32 [m, 2] - particle pairs the lace pulls together
    rest: np.ndarray  # float64 [m] - metres
    path: np.ndarray  # float64 [k, 3] - the polyline, for rendering
    style: str = "criss-cross"
    tension: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "style": self.style,
            "tension": round(self.tension, 3),
            "spans": int(self.spans.shape[0]),
            "path_points": int(self.path.shape[0]),
            "lace_length_mm": round(
                float(np.linalg.norm(np.diff(self.path, axis=0), axis=1).sum()) * 1000.0, 1
            )
            if self.path.shape[0] > 1
            else 0.0,
            **self.meta,
        }

    def as_tube(self, radius_mm: float = 1.6):
        """The lace as renderable geometry."""
        import trimesh

        if self.path.shape[0] < 2:
            return None
        parts = []
        for start, end in zip(self.path[:-1], self.path[1:], strict=False):
            direction = end - start
            length = float(np.linalg.norm(direction))
            if length < 1e-6:
                continue
            tube = trimesh.creation.cylinder(radius=radius_mm / 1000.0, height=length, sections=8)
            transform = np.eye(4)
            transform[:3, :3] = trimesh.geometry.align_vectors([0.0, 0.0, 1.0], direction / length)[
                :3, :3
            ]
            transform[:3, 3] = (start + end) / 2.0
            tube.apply_transform(transform)
            parts.append(tube)
        return trimesh.util.concatenate(parts) if parts else None


def eyelets_along(
    garment: GarmentMesh,
    points: np.ndarray,
    *,
    panel: str,
    axis: int = 0,
    side: str = "max",
    count: int = 7,
    inset_mm: float = 12.0,
    span: tuple[float, float] = (0.15, 0.85),
) -> Eyelets:
    """Evenly spaced eyelets down one side of a panel.

    Picked from the DRAPED positions rather than the flat pattern, because an
    eyelet has to be where the cloth actually is before a lace can thread it.
    """
    if panel not in garment.panel_slices:
        known = ", ".join(sorted(garment.panel_slices))
        raise KeyError(f"no panel {panel!r}; have: {known}.")
    low, high = garment.panel_slices[panel]
    local = points[low:high]
    order = np.argsort(local[:, 1])  # bottom to top
    heights = local[order, 1]
    lo_h = heights[int(len(heights) * span[0])]
    hi_h = heights[int(len(heights) * span[1]) - 1]

    chosen: list[int] = []
    inset = inset_mm / 1000.0
    for level in np.linspace(lo_h, hi_h, count):
        band = np.flatnonzero(np.abs(local[:, 1] - level) < max((hi_h - lo_h) / count, 1e-4))
        if band.size == 0:
            continue
        edge = (
            band[np.argmax(local[band, axis])]
            if side == "max"
            else band[np.argmin(local[band, axis])]
        )
        chosen.append(int(edge))
    indices = np.asarray(sorted(set(chosen)), dtype=np.int64)
    if indices.size < 2:
        raise ValueError(
            f"only {indices.size} eyelet(s) found on {panel}: the panel may be too "
            "coarse to place them. Use a finer particle distance."
        )
    positions = local[indices].copy()
    # sit the eyelet in from the raw edge, the way a real one is punched
    positions[:, axis] -= inset * (1.0 if side == "max" else -1.0)
    return Eyelets(indices=indices + low, positions=positions, panel=panel, side=side)


def thread(
    left: Eyelets,
    right: Eyelets,
    points: np.ndarray,
    *,
    style: str = "criss-cross",
    tension: float = 0.35,
) -> Lace:
    """Thread a lace between two rows of eyelets and tighten it.

    `tension` is how much shorter each threaded span is made than the gap it
    spans: 0 threads the lace without pulling, 0.35 draws the opening in by a
    third, 1.0 closes it. That is the only knob, and it is the one a person
    actually turns.
    """
    if style not in STYLES:
        raise ValueError(f"no lace style {style!r}; styles: {', '.join(STYLES)}.")
    if not 0.0 <= tension <= 1.0:
        raise ValueError(f"tension runs 0 (threaded, loose) to 1 (closed), got {tension}")
    count = min(len(left), len(right))
    if count < 2:
        raise ValueError("a lace needs at least two eyelets a side")

    pairs: list[tuple[int, int]] = []
    path: list[np.ndarray] = []
    left_at = points[left.indices[:count]]
    right_at = points[right.indices[:count]]

    if style == "straight-bar":
        for k in range(count):
            pairs.append((int(left.indices[k]), int(right.indices[k])))
            path.extend([left_at[k], right_at[k]])
    elif style == "spiral":
        for k in range(count):
            pairs.append((int(left.indices[k]), int(right.indices[(k + 1) % count])))
            path.extend([left_at[k], right_at[(k + 1) % count]])
    else:  # criss-cross
        for k in range(count - 1):
            pairs.append((int(left.indices[k]), int(right.indices[k + 1])))
            pairs.append((int(right.indices[k]), int(left.indices[k + 1])))
            path.extend([left_at[k], right_at[k + 1], right_at[k], left_at[k + 1]])

    spans = np.asarray(pairs, dtype=np.int32)
    gaps = np.linalg.norm(points[spans[:, 0]] - points[spans[:, 1]], axis=1)
    return Lace(
        spans=spans,
        rest=gaps * (1.0 - tension),
        path=np.asarray(path, dtype=np.float64),
        style=style,
        tension=tension,
        meta={
            "eyelets_per_side": count,
            "opening_mm": round(float(gaps.mean()) * 1000.0, 1),
            "drawn_to_mm": round(float((gaps * (1.0 - tension)).mean()) * 1000.0, 1),
        },
    )


def apply(garment: GarmentMesh, lace: Lace) -> GarmentMesh:
    """Add the lace's constraints to a garment, ready to solve."""
    extra = lace.spans if garment.extra is None else np.vstack([garment.extra, lace.spans])
    rest = (
        lace.rest if garment.extra_rest is None else np.concatenate([garment.extra_rest, lace.rest])
    )
    garment.extra = np.ascontiguousarray(extra, dtype=np.int32)
    garment.extra_rest = np.ascontiguousarray(rest, dtype=np.float64)
    return garment
