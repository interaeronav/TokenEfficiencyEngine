"""Pinching: grab the cloth and hold it, on both sides at once.

A pinch is a pin with somewhere to go. `pins` says which particles are held;
`pin_target` says where. Held where they are, they anchor; moved, they pull.

**Symmetric** is the interesting half and the reason this is a module rather
than three lines at a call site. Pinching a garment on one side and then the
other gives a different result from pinching both at once - the first pinch
has already dragged the cloth by the time the second lands - so a symmetric
pinch has to be built as one set and applied in one solve.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.garment import GarmentMesh


@dataclass(slots=True)
class Pinch:
    """One grab: where, how wide, and where it is pulled to."""

    at: tuple[float, float, float]
    radius_mm: float = 25.0
    to: tuple[float, float, float] | None = None  # None = hold in place
    falloff: bool = True  # feather the grip, like fingers rather than a clamp

    def offset(self) -> np.ndarray:
        if self.to is None:
            return np.zeros(3)
        return np.asarray(self.to, dtype=np.float64) - np.asarray(self.at, dtype=np.float64)


@dataclass(slots=True)
class PinchSet:
    mask: np.ndarray
    target: np.ndarray
    grabbed: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {"pinched_particles": int((self.mask > 0).sum()), "grabs": self.grabbed}


def pinch(
    garment: GarmentMesh,
    points: np.ndarray,
    grabs: list[Pinch],
    *,
    mirror: bool = True,
    mirror_axis: int = 0,
) -> PinchSet:
    """Build the pin mask and targets for a set of grabs.

    `mirror=True` adds the reflected twin of every grab across the body's
    centre line and applies both in the SAME solve - which is what "pinch both
    sides at the same time" means, and is not the same as pinching one side
    and then the other.
    """
    positions = np.asarray(points, dtype=np.float64)
    mask = np.zeros(len(positions), dtype=np.float64)
    target = positions.copy()
    counted: dict[str, int] = {}

    full: list[tuple[str, Pinch]] = []
    for index, grab in enumerate(grabs):
        full.append((f"grab{index}", grab))
        if mirror:
            flipped_at = list(grab.at)
            flipped_at[mirror_axis] = -flipped_at[mirror_axis]
            flipped_to = None
            if grab.to is not None:
                flipped_to = list(grab.to)
                flipped_to[mirror_axis] = -flipped_to[mirror_axis]
                flipped_to = tuple(flipped_to)
            full.append(
                (
                    f"grab{index}:mirror",
                    Pinch(tuple(flipped_at), grab.radius_mm, flipped_to, grab.falloff),
                )
            )

    for label, grab in full:
        centre = np.asarray(grab.at, dtype=np.float64)
        radius = grab.radius_mm / 1000.0
        distance = np.linalg.norm(positions - centre, axis=1)
        inside = distance <= radius
        if not inside.any():
            counted[label] = 0
            continue
        # a feathered grip: full hold at the centre, easing to nothing at the
        # rim, because fingers are not clamps and a hard edge shows as a crease
        weight = np.where(
            inside,
            1.0 - (distance / max(radius, 1e-9)) ** 2 if grab.falloff else 1.0,
            0.0,
        )
        mask = np.maximum(mask, weight * inside)
        target[inside] += grab.offset() * weight[inside, None]
        counted[label] = int(inside.sum())

    return PinchSet(mask=(mask > 1e-6).astype(np.float64), target=target, grabbed=counted)


def pinch_report(before: np.ndarray, after: np.ndarray, pinches: PinchSet) -> dict[str, Any]:
    """What the pinch did, in millimetres."""
    held = pinches.mask > 0
    moved = np.linalg.norm(after - before, axis=1) * 1000.0
    return {
        "pinched_particles": int(held.sum()),
        "grabs": pinches.grabbed,
        "held_moved_mm": round(float(moved[held].max()), 2) if held.any() else 0.0,
        "cloth_moved_mm": round(float(moved[~held].max()), 2) if (~held).any() else 0.0,
        "symmetric": all(
            not label.endswith(":mirror") or count > 0 for label, count in pinches.grabbed.items()
        ),
    }
