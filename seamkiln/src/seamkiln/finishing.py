"""Finishing: denim wet washes and fur, both driven by the drape itself.

The reason these two live together is that neither is a texture painted on
afterwards. Both read the garment's own geometry.

**Denim washes are abrasion, and abrasion follows the creases.** Whiskers at
the hip, honeycombs behind the knee, stacking at the hem - a laundry does not
paint those on, it abrades cloth that is already folded there, which is why
they land differently on every fit and every body. seamkiln has the draped
geometry, so it can find the creases the same way the laundry does: high
mean curvature on an outward-facing surface is where the cloth rubs. The wash
is then a colour ramp over that wear field, per wash level.

**Fur grows along the surface normal and falls with gravity.** Strands are
generated from the mesh, not scattered in space, so fur on a sleeve follows
the sleeve. Generation is measured, because "real-time" is a claim with a
number behind it.

Neither pretends to be a render: both produce geometry and per-vertex colour
that survive a glTF export, because a finish that only exists in one viewer
is a screenshot.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Indigo denim, undyed cotton, and the levels a laundry actually quotes.
# Colours are sRGB 0-1. A wash level is a pair: how far the ground is lifted
# toward the undyed cotton, and how hard the creases are hit.
INDIGO = np.array([0.114, 0.180, 0.322])
UNDYED = np.array([0.859, 0.827, 0.741])

WASH_LEVELS: dict[str, tuple[float, float]] = {
    "raw": (0.00, 0.00),
    "rinse": (0.06, 0.15),
    "light": (0.18, 0.45),
    "medium": (0.34, 0.70),
    "dark_used": (0.16, 0.85),
    "stone": (0.46, 0.60),
    "bleached": (0.72, 0.40),
}


@dataclass(slots=True)
class WearField:
    """Where the garment is being abraded, per vertex, 0..1."""

    wear: np.ndarray
    curvature: np.ndarray
    seconds: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "vertices": int(self.wear.shape[0]),
            "mean_wear": round(float(self.wear.mean()), 4),
            "p95_wear": round(float(np.percentile(self.wear, 95)), 4),
            "seconds": round(self.seconds, 3),
            **self.meta,
        }


def mean_curvature(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Discrete mean curvature per vertex, signed: positive where the surface
    bulges outward. A crease that folds OUT is what rubs on a machine drum;
    one that folds in is protected, which is why the two look different on a
    real pair of jeans."""
    points = np.asarray(points, dtype=np.float64)
    a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
    face_normal = np.cross(b - a, c - a)
    face_area = np.linalg.norm(face_normal, axis=1) * 0.5
    face_normal /= np.maximum(np.linalg.norm(face_normal, axis=1, keepdims=True), 1e-12)

    normals = np.zeros_like(points)
    area = np.zeros(len(points))
    centroid = np.zeros_like(points)
    weight = np.zeros(len(points))
    face_centre = (a + b + c) / 3.0
    for column in range(3):
        np.add.at(normals, triangles[:, column], face_normal * face_area[:, None])
        np.add.at(area, triangles[:, column], face_area / 3.0)
        np.add.at(centroid, triangles[:, column], face_centre * face_area[:, None])
        np.add.at(weight, triangles[:, column], face_area)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    centroid /= np.maximum(weight[:, None], 1e-12)
    # how far the one-ring centroid sits along the normal: the discrete
    # Laplacian, which is mean curvature up to a scale
    offset = np.einsum("ij,ij->i", centroid - points, normals)
    scale = np.sqrt(np.maximum(area, 1e-12))
    return -offset / np.maximum(scale, 1e-9)


def wear_field(
    points: np.ndarray,
    triangles: np.ndarray,
    *,
    strain: np.ndarray | None = None,
    hem_bias: float = 0.35,
) -> WearField:
    """Where this garment, as draped, would abrade."""
    started = time.perf_counter()
    curvature = mean_curvature(points, triangles)
    # only OUTWARD folds rub; inward ones are shielded
    ridges = np.clip(curvature, 0.0, None)
    if ridges.max() > 0:
        ridges = ridges / ridges.max()
    wear = ridges**0.7

    if strain is not None and len(strain) == len(wear):
        stretched = np.clip(np.asarray(strain, dtype=np.float64), 0.0, None)
        if stretched.max() > 0:
            wear = 0.75 * wear + 0.25 * (stretched / stretched.max())

    # the hem stacks and drags on the ground, so it wears whatever it folds
    heights = np.asarray(points)[:, 1]
    span = float(heights.max() - heights.min())
    if span > 1e-6 and hem_bias > 0.0:
        low = np.clip(1.0 - (heights - heights.min()) / span, 0.0, 1.0) ** 3
        wear = np.clip(wear + hem_bias * low * wear.mean() * 3.0, 0.0, 1.0)

    wear = np.clip(wear / max(float(np.percentile(wear, 99)), 1e-9), 0.0, 1.0)
    return WearField(
        wear=wear,
        curvature=curvature,
        seconds=time.perf_counter() - started,
        meta={"method": "outward mean curvature + hem bias", "used_strain": strain is not None},
    )


def denim_wash(
    points: np.ndarray,
    triangles: np.ndarray,
    *,
    level: str = "medium",
    strain: np.ndarray | None = None,
    base: np.ndarray | None = None,
) -> dict[str, Any]:
    """A wet-wash finish as per-vertex colour, from the garment's own creases.

    Returns colours ready to attach to a mesh (and therefore to survive a
    glTF export), plus the wear field they came from - because the field is
    the interesting output: it says WHERE this fit abrades, which is a fitting
    note, not just a look.
    """
    if level not in WASH_LEVELS:
        raise ValueError(f"no wash level {level!r}; levels: {', '.join(WASH_LEVELS)}.")
    lift, contrast = WASH_LEVELS[level]
    field_ = wear_field(points, triangles, strain=strain)
    ground = (base if base is not None else INDIGO) * (1.0 - lift) + UNDYED * lift
    highlight = field_.wear[:, None] * contrast
    colours = np.clip(ground[None, :] * (1.0 - highlight) + UNDYED[None, :] * highlight, 0, 1)
    return {
        "level": level,
        "colours": colours,
        "wear": field_,
        "summary": {
            "level": level,
            "ground_lift": lift,
            "crease_contrast": contrast,
            **field_.summary(),
        },
    }


def apply_colours(mesh, colours: np.ndarray):
    """Attach per-vertex colour so it survives an export."""
    import trimesh

    rgba = np.concatenate([np.clip(colours, 0, 1), np.ones((len(colours), 1))], axis=1)
    mesh.visual = trimesh.visual.ColorVisuals(
        mesh=mesh, vertex_colors=(rgba * 255).astype(np.uint8)
    )
    return mesh


# -- fur ---------------------------------------------------------------------


@dataclass(slots=True)
class Fur:
    starts: np.ndarray
    ends: np.ndarray
    mids: np.ndarray
    seconds: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "strands": int(self.starts.shape[0]),
            "seconds": round(self.seconds, 3),
            "strands_per_second": int(self.starts.shape[0] / max(self.seconds, 1e-6)),
            "mean_length_mm": round(
                float(np.linalg.norm(self.ends - self.starts, axis=1).mean()) * 1000.0, 2
            )
            if self.starts.size
            else 0.0,
            **self.meta,
        }

    def as_mesh(self, thickness_mm: float = 0.35):
        """Strands as thin two-segment tubes - enough to catch light and bend."""
        import trimesh

        if self.starts.shape[0] == 0:
            return None
        vertices, faces = [], []
        half = thickness_mm / 2000.0
        for index in range(self.starts.shape[0]):
            a, m, b = self.starts[index], self.mids[index], self.ends[index]
            side = np.cross(b - a, [0.0, 0.0, 1.0])
            norm = float(np.linalg.norm(side))
            side = np.array([half, 0.0, 0.0]) if norm < 1e-9 else side / norm * half
            base = len(vertices)
            vertices.extend([a - side, a + side, m - side, m + side, b])
            faces.extend(
                [
                    [base, base + 1, base + 3],
                    [base, base + 3, base + 2],
                    [base + 2, base + 3, base + 4],
                ]
            )
        return trimesh.Trimesh(
            vertices=np.asarray(vertices), faces=np.asarray(faces), process=False
        )


def fur(
    points: np.ndarray,
    triangles: np.ndarray,
    *,
    density_per_cm2: float = 4.0,
    length_mm: float = 18.0,
    curl: float = 0.45,
    droop: float = 0.55,
    clump: float = 0.3,
    seed: int = 20260901,
) -> Fur:
    """Grow fur on a garment surface.

    Strands are scattered by TRIANGLE AREA, so density is uniform per square
    centimetre of cloth rather than per triangle - otherwise a fine region
    grows a pelt and a coarse one goes bald, which is the classic giveaway.
    Each strand leaves along the surface normal, curls, and falls under
    gravity; `clump` pulls neighbours toward a shared direction, which is what
    makes fur read as fur rather than as a lawn.
    """
    started = time.perf_counter()
    points = np.asarray(points, dtype=np.float64)
    a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
    cross = np.cross(b - a, c - a)
    areas = np.linalg.norm(cross, axis=1) * 0.5
    normals = cross / np.maximum(np.linalg.norm(cross, axis=1, keepdims=True), 1e-12)

    total_cm2 = float(areas.sum()) * 1e4
    count = int(total_cm2 * density_per_cm2)
    if count <= 0:
        return Fur(np.zeros((0, 3)), np.zeros((0, 3)), np.zeros((0, 3)), 0.0, {"note": "no area"})

    rng = np.random.default_rng(seed)
    face = rng.choice(len(areas), size=count, p=areas / areas.sum())
    u = rng.random(count)
    v = rng.random(count)
    over = u + v > 1.0
    u[over], v[over] = 1.0 - u[over], 1.0 - v[over]
    root = a[face] + (b[face] - a[face]) * u[:, None] + (c[face] - a[face]) * v[:, None]

    direction = normals[face].copy()
    if clump > 0.0:
        # neighbours on the same face share a lean - the cheapest clumping
        # that still reads, and deterministic because the seed drives it
        lean = rng.normal(0.0, 1.0, (len(areas), 3))
        lean /= np.maximum(np.linalg.norm(lean, axis=1, keepdims=True), 1e-12)
        direction = direction * (1.0 - clump) + lean[face] * clump

    jitter = rng.normal(0.0, 0.25, (count, 3))
    direction = direction + jitter
    direction /= np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)

    length = (length_mm / 1000.0) * rng.uniform(0.7, 1.3, count)[:, None]
    gravity = np.array([0.0, -1.0, 0.0])
    mid = root + direction * length * 0.55
    mid[:, 1] -= float(droop) * length[:, 0] * 0.25
    tip_dir = direction * (1.0 - curl) + gravity * curl
    tip_dir /= np.maximum(np.linalg.norm(tip_dir, axis=1, keepdims=True), 1e-12)
    tip = mid + tip_dir * length * 0.45
    tip[:, 1] -= float(droop) * length[:, 0] * 0.35

    return Fur(
        starts=root,
        mids=mid,
        ends=tip,
        seconds=time.perf_counter() - started,
        meta={
            "density_per_cm2": density_per_cm2,
            "surface_cm2": round(total_cm2, 1),
            "length_mm": length_mm,
            "curl": curl,
            "clump": clump,
        },
    )
