"""Collision: detection, material response, and which way "out" points.

Three things have to agree, and the third is the one that quietly does not.

  DETECTION   is the signed distance field: negative inside the subject,
              positive outside, sampled trilinearly. `body.py` bakes it.
  MATERIAL    is restitution and friction, read off the fabric and the
              subject - how bouncy the contact is and how sticky.
  RESOLUTION  pushes the particle back out along the surface normal and
              damps its tangential motion, so cloth rests instead of
              passing through.

**And the direction has to match the render.** The collision normal comes
from the field's gradient; the render normal comes from the triangle winding.
Nothing forces them to agree, and when they disagree a panel is lit from
inside: it renders dark, its wash lands on the wrong face, its fur grows
INTO the body, and the drape is unaffected - so the numbers all look fine.
`alignment` measures the disagreement and `align_to_field` fixes it by
flipping the winding of the panels that face the wrong way.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from seamkiln.drape.body import BodySDF
from seamkiln.drape.garment import GarmentMesh

# How bouncy a contact is. Cloth on a body is not a bouncing ball - real
# fabric dissipates almost everything - so the default is near zero and the
# range is there for the cases that are not cloth-on-skin.
DEFAULT_RESTITUTION = 0.02


@dataclass(slots=True)
class ContactMaterial:
    """What happens where the cloth meets the subject."""

    friction: float = 0.35
    restitution: float = DEFAULT_RESTITUTION
    thickness_mm: float = 1.0

    @classmethod
    def between(cls, fabric: Any, subject_friction: float = 0.5) -> ContactMaterial:
        """Combine the two surfaces' properties.

        Friction combines as the GEOMETRIC mean, which is the usual convention
        and matters: Bullet multiplies them, which makes two 0.5 surfaces read
        as 0.25 and surprises everyone once (research doc 34 records TEE
        hitting exactly that). Restitution takes the maximum, because the
        bouncier surface governs the bounce.
        """
        return cls(
            friction=float(np.sqrt(max(fabric.friction, 1e-6) * max(subject_friction, 1e-6))),
            restitution=max(getattr(fabric, "restitution", DEFAULT_RESTITUTION), 0.0),
            thickness_mm=max(fabric.thickness_mm, 0.2),
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "friction": round(self.friction, 4),
            "restitution": round(self.restitution, 4),
            "thickness_mm": round(self.thickness_mm, 3),
        }


def vertex_normals(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Render normals, from the triangle winding - what a shader will use."""
    points = np.asarray(points, dtype=np.float64)
    a, b, c = points[triangles[:, 0]], points[triangles[:, 1]], points[triangles[:, 2]]
    face = np.cross(b - a, c - a)
    out = np.zeros_like(points)
    for column in range(3):
        np.add.at(out, triangles[:, column], face)
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-12)


def alignment(
    garment: GarmentMesh, points: np.ndarray, sdf: BodySDF, *, near_mm: float = 25.0
) -> dict[str, Any]:
    """Do the render normals agree with the direction the collision pushes?

    Measured only NEAR the subject, because far from it the field's gradient
    is not a meaningful "out" and a hem hanging in free air would drag the
    number around for no reason.
    """
    render = vertex_normals(points, garment.triangles)
    outward = sdf.gradient(points)
    distance = sdf.sample(points)
    near = np.abs(distance) < near_mm / 1000.0
    agree = np.einsum("ij,ij->i", render, outward)

    per_panel: dict[str, dict[str, float]] = {}
    for panel_id, (low, high) in garment.panel_slices.items():
        mask = np.zeros(len(points), dtype=bool)
        mask[low:high] = True
        mask &= near
        if not mask.any():
            continue
        per_panel[panel_id] = {
            "mean_agreement": round(float(agree[mask].mean()), 4),
            "facing_inward_pct": round(float((agree[mask] < 0).mean()) * 100.0, 1),
            "sampled": int(mask.sum()),
        }
    overall = float(agree[near].mean()) if near.any() else 0.0
    inverted = [p for p, row in per_panel.items() if row["mean_agreement"] < 0.0]
    return {
        "mean_agreement": round(overall, 4),
        "inside_out_panels": inverted,
        "aligned": not inverted,
        "panels": per_panel,
        "note": "render normal vs the field's outward gradient, sampled near the "
        "subject. A panel below zero is lit from inside - the drape is unaffected, "
        "which is why nothing else reports it.",
    }


def align_to_field(
    garment: GarmentMesh, points: np.ndarray, sdf: BodySDF
) -> tuple[GarmentMesh, dict[str, Any]]:
    """Flip the winding of any panel whose render normals face the body.

    Per PANEL, not per triangle: a panel is one piece of cloth cut one way
    round, so its winding is right or wrong as a whole. Flipping triangles
    individually would produce a mesh that is locally consistent and globally
    nonsense, which is worse than the problem.
    """
    before = alignment(garment, points, sdf)
    if before["aligned"]:
        return garment, {**before, "flipped": []}

    triangles = garment.triangles.copy()
    flipped: list[str] = []
    for panel_id in before["inside_out_panels"]:
        low, high = garment.panel_slices[panel_id]
        rows = np.all((triangles >= low) & (triangles < high), axis=1)
        triangles[rows] = triangles[rows][:, [0, 2, 1]]
        flipped.append(panel_id)

    garment.triangles = triangles
    after = alignment(garment, points, sdf)
    return garment, {
        "flipped": flipped,
        "before": before["mean_agreement"],
        "after": after["mean_agreement"],
        "aligned": after["aligned"],
    }


def contacts(
    garment: GarmentMesh, points: np.ndarray, sdf: BodySDF, *, thickness_mm: float = 1.0
) -> dict[str, Any]:
    """Detection, reported: what is touching, what is inside, what is clear."""
    distance = sdf.sample(points) * 1000.0
    offset = thickness_mm
    touching = np.abs(distance - offset) < max(offset, 0.5)
    inside = distance < 0.0
    return {
        "particles": len(points),
        "touching": int(touching.sum()),
        "inside": int(inside.sum()),
        "deepest_mm": round(float(-distance.min()), 3) if inside.any() else 0.0,
        "clear_mm": round(float(distance.max()), 1),
        "voxel_mm": round(sdf.spacing * 1000.0, 2),
    }
