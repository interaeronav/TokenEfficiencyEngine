"""Measurements, ease and fit maps - what makes this a fashion tool.

A cloth simulator answers "where did the fabric go". A garment tool has to
answer the questions a fitting answers: how big is this body, how big is the
garment on it, how much room is there at the bust, and where is the fabric
under strain. Those are all numbers, and they are reported as numbers -
colour is optional decoration on top (hard rule 4: text over pixels).

Girths are taken as cross-sections through the torso, the same arm-proof way
`body_landmarks` measures the chest, so a body measurement here means the
same thing a tape measure means.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import trimesh

from seamkiln.drape.garment import GarmentMesh, _torso_section, body_landmarks

# Fractions of stature at which a tape measure is placed. Fractions, not
# absolutes, so the same landmarks work on a child and on an adult - which is
# the point of using Anny, whose shape space spans infants to elders.
LANDMARKS: dict[str, float] = {
    "bust": 0.72,
    "underbust": 0.68,
    "waist": 0.62,
    "high_hip": 0.57,
    "hip": 0.52,
}


@dataclass(slots=True)
class Measurement:
    name: str
    y_m: float
    girth_mm: float

    def as_dict(self) -> dict[str, float]:
        return {"y_m": round(self.y_m, 4), "girth_mm": round(self.girth_mm, 1)}


def girth_at(mesh: trimesh.Trimesh, y: float) -> float | None:
    """Torso circumference at height y, in millimetres."""
    polygon = _torso_section(mesh, y)
    return None if polygon is None else float(polygon.length) * 1000.0


def body_measurements(mesh: trimesh.Trimesh) -> dict[str, Any]:
    """The tape-measure set, plus the landmarks the arrangement needs."""
    marks = body_landmarks(mesh)
    low = float(mesh.bounds[0][1])
    height = marks["height_m"]
    rows: dict[str, dict[str, float]] = {}
    for name, fraction in LANDMARKS.items():
        y = low + height * fraction
        girth = girth_at(mesh, y)
        if girth is not None:
            rows[name] = Measurement(name, y, girth).as_dict()
    return {
        "height_mm": round(height * 1000.0, 1),
        "chest_girth_mm": round(marks["chest_girth_m"] * 1000.0, 1),
        "shoulder_y_m": marks["shoulder_y_m"],
        "landmarks": rows,
    }


def torso_panels(garment: GarmentMesh, points: np.ndarray) -> list[str]:
    """Panels that wrap the body, as opposed to a limb.

    A torso panel straddles the body's centre line; a sleeve sits entirely on
    one side of it. Without this the "bust girth" of a draped tee is the hull
    across BOTH SLEEVES - it read 1,374 mm on an 890 mm body, and called a
    normal tee oversized by half a metre.
    """
    out: list[str] = []
    for panel_id, (low, high) in garment.panel_slices.items():
        xs = points[low:high, 0]
        if float(xs.min()) < 0.0 < float(xs.max()):
            out.append(panel_id)
    return out or list(garment.panel_slices)


def garment_measurements(
    garment: GarmentMesh,
    points: np.ndarray,
    body: trimesh.Trimesh,
    *,
    panels: list[str] | None = None,
) -> dict[str, Any]:
    """The same girths, taken through the DRAPED garment.

    A garment cross-section can be several loops (front and back apart at the
    hem, a sleeve passing through the plane), so this measures the convex
    hull of the slice: that is what a tape measure round the outside of a
    garment actually reports.
    """
    from shapely.geometry import MultiPoint

    floor = float(body.bounds[0][1])
    height = body_landmarks(body)["height_m"]
    chosen = set(panels if panels is not None else torso_panels(garment, points))
    keep = np.zeros(len(points), dtype=bool)
    for panel_id in chosen:
        # `first`/`last`, NOT `low`/`high`: naming these `low` clobbered the
        # body's floor height a few lines up, so every measurement plane ended
        # up at a POINT INDEX instead of a height - thousands of metres in the
        # air, intersecting nothing, and the fit report came back empty with
        # no error at all.
        first, last = garment.panel_slices[panel_id]
        keep[first:last] = True
    faces = garment.triangles[keep[garment.triangles].all(axis=1)]
    mesh = trimesh.Trimesh(vertices=points, faces=faces, process=False)
    rows: dict[str, dict[str, float]] = {"_panels": sorted(chosen)}
    for name, fraction in LANDMARKS.items():
        y = floor + height * fraction
        section = mesh.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
        if section is None or len(section.vertices) < 3:
            continue
        # The slice's own vertices, hulled in the horizontal plane. Going via
        # Path2D's polygon API was fragile - a garment slice is often several
        # open loops (front and back apart at the hem, a sleeve crossing the
        # plane) and the polygon accessors differ between trimesh versions.
        # The convex hull of the slice points is also what a tape measure
        # round the outside of a garment actually reports.
        flat = np.asarray(section.vertices)[:, [0, 2]]
        hull = MultiPoint([tuple(row) for row in flat]).convex_hull
        if hull.geom_type != "Polygon":
            continue
        rows[name] = {"y_m": round(y, 4), "girth_mm": round(float(hull.length) * 1000.0, 1)}
    return rows


def ease(garment_rows: dict[str, Any], body_rows: dict[str, Any]) -> dict[str, Any]:
    """Garment minus body at each landmark, in millimetres.

    Ease is the number a fitting argues about: negative is a garment that
    will not do up, 0-20 mm is close-fitting, 60-120 mm is a relaxed tee.
    Reported per landmark because a garment can be generous at the bust and
    tight at the hip, and a single number hides exactly that.
    """
    out: dict[str, Any] = {}
    body_landmarks_rows = body_rows.get("landmarks", body_rows)
    for name, garment_row in garment_rows.items():
        if name.startswith("_"):
            continue
        body_row = body_landmarks_rows.get(name)
        if body_row is None:
            continue
        delta = garment_row["girth_mm"] - body_row["girth_mm"]
        out[name] = {
            "body_mm": body_row["girth_mm"],
            "garment_mm": garment_row["girth_mm"],
            "ease_mm": round(delta, 1),
            "verdict": _ease_verdict(delta),
        }
    return out


def _ease_verdict(delta_mm: float) -> str:
    if delta_mm < 0:
        return "negative - will not close"
    if delta_mm < 20:
        return "skin-tight"
    if delta_mm < 60:
        return "close"
    if delta_mm < 140:
        return "relaxed"
    return "oversized"


def strain_map(garment: GarmentMesh, points: np.ndarray) -> dict[str, Any]:
    """Per-panel strain from rest length to draped length.

    Numbers first. A colour map is a rendering of this, not a replacement:
    "the right sleeve cap is at 12% mean strain" is actionable, a red patch
    is a conversation starter.
    """
    # Sliver edges - a fraction of the particle distance long - give absurd
    # relative strains: a 0.1 mm rest length stretched 3 mm is 3,000%, which
    # says nothing about the fabric and drowns out every real number. Edges
    # under a tenth of the particle distance are meshing artefacts and are
    # excluded, with the count reported so the exclusion is visible.
    floor = max(garment.particle_distance_mm, 1.0) * 1e-3 * 0.1
    usable = garment.structural_rest > floor
    pairs = garment.structural[usable]
    rest = garment.structural_rest[usable]
    excluded = int((~usable).sum())
    current = np.linalg.norm(points[pairs[:, 0]] - points[pairs[:, 1]], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        strain = np.where(rest > 1e-9, (current - rest) / np.maximum(rest, 1e-9), 0.0)

    panels: dict[str, dict[str, float]] = {}
    for panel_id, (low, high) in garment.panel_slices.items():
        inside = (
            (pairs[:, 0] >= low)
            & (pairs[:, 0] < high)
            & (pairs[:, 1] >= low)
            & (pairs[:, 1] < high)
        )
        values = strain[inside]
        if values.size == 0:
            continue
        panels[panel_id] = {
            "mean_pct": round(float(values.mean()) * 100.0, 2),
            "p95_pct": round(float(np.percentile(values, 95)) * 100.0, 2),
            "max_pct": round(float(values.max()) * 100.0, 2),
            "compressed_pct": round(float((values < -0.02).mean()) * 100.0, 1),
        }
    return {
        "overall_mean_pct": round(float(strain.mean()) * 100.0, 2),
        "overall_p99_pct": round(float(np.percentile(strain, 99)) * 100.0, 2),
        "overall_max_pct": round(float(strain.max()) * 100.0, 2),
        "sliver_edges_excluded": excluded,
        "panels": panels,
    }


def fit_report(garment: GarmentMesh, points: np.ndarray, body: trimesh.Trimesh) -> dict[str, Any]:
    """Everything a fitting would say, compactly. No vertices."""
    body_rows = body_measurements(body)
    garment_rows = garment_measurements(garment, points, body)
    return {
        "body": body_rows,
        "ease": ease(garment_rows, body_rows),
        "strain": strain_map(garment, points),
    }
