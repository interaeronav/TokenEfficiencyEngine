"""Interference, contact and clearance between placed bodies.

Numbers, not pixels (D7 `details.asm`): every pair whose bounding boxes
overlap is intersected with `BRepAlgoAPI_Common` (through
`partkiln.brep.shapes.common`) and the common solid's exact volume and
centroid are the answer; a pair whose boxes are apart is never sent to the
boolean (the prefilter is what keeps a 20-component assembly under the
batch deadline - each Common on F6 costs ~1.3 ms, each box test nothing).

The fuzzy policy, measured on this Mac (OCP 7.9.3, 2026-09-02): a d10 pin
in a d10 hole - the exact fit - gives an EMPTY common (0 solids, volume 0)
with `SetFuzzyValue` left at 0, and stays empty when the pin's pose carries
1e-9 or 1e-7 mm of solver noise or a 1e-9 degree tilt. OCCT returns no
slivers here, so `FUZZY_MM` is 0 and `shapes.common` is used unchanged; the
tolerance that DOES matter is on the distance: the noisy exact fit measures
`BRepExtrema_DistShapeShape = 2.26e-9`, not 0, so `contact` is
`distance <= CONTACT_MM` (1e-6 mm), and that is the value the report
declares. An interference of exactly 0 with contact True is therefore the
fit's honest reading, never a rounding accident.

`BRepExtrema_DistShapeShape` is the one OCCT call `partkiln.brep` does not
wrap yet, so `_distance` imports it lazily HERE - flagged for the lift into
`brep/shapes.py` (P3c); `import partkiln.assembly` stays OCP-free.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from partkiln.assembly.model import Assembly, Pose
from partkiln.document import CommandError

Body = tuple[str, Any, Pose | None]

CONTACT_MM = 1e-6
FUZZY_MM = 0.0
# Clearance is reported for pairs whose boxes are at most this far apart;
# a body 500 mm away has a distance too, but nobody asked.
NEAR_MM = 10.0


def placed(shape: Any, pose: Pose | None) -> Any:
    """`shape` moved by `pose` (a copy; the identity pose returns the shape itself)."""
    if pose is None or pose.is_identity():
        return shape
    from partkiln.brep import shapes

    rot = None
    rv = pose.rotvec()
    angle = (rv[0] ** 2 + rv[1] ** 2 + rv[2] ** 2) ** 0.5
    if angle > 0:
        rot = ((0.0, 0.0, 0.0), rv, math.degrees(angle))
    return shapes.transform(shape, pose.translation, rot).shape


def bodies_of(asm: Assembly) -> list[tuple[str, Any]]:
    """(name, placed shape) for every non-virtual component, in assembly order."""
    return [(c.name, placed(c.shape, c.pose)) for c in asm.components.values() if not c.virtual]


def _boxes_overlap(a: Sequence[float], b: Sequence[float], pad: float = 0.0) -> bool:
    return all(a[i] - pad <= b[i + 3] and b[i] - pad <= a[i + 3] for i in range(3))


def _box_gap(a: Sequence[float], b: Sequence[float]) -> float:
    gap = 0.0
    for i in range(3):
        d = max(a[i] - b[i + 3], b[i] - a[i + 3], 0.0)
        gap += d * d
    return gap**0.5


def _distance(a: Any, b: Any) -> tuple[float, list[list[float]]]:
    """Minimum distance and one closest pair of points (rounded 3 dp)."""
    from partkiln.brep import require_ocp

    require_ocp()
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    algo = BRepExtrema_DistShapeShape(a, b)
    algo.Perform()
    if not algo.IsDone():
        raise CommandError(
            "distance computation failed (BRepExtrema_DistShapeShape not done); "
            "check both shapes are valid solids.",
            code="pk_op_failed",
        )
    d = float(algo.Value())
    points: list[list[float]] = []
    if algo.NbSolution() >= 1:
        p, q = algo.PointOnShape1(1), algo.PointOnShape2(1)
        points = [
            [round(p.X(), 3) + 0.0, round(p.Y(), 3) + 0.0, round(p.Z(), 3) + 0.0],
            [round(q.X(), 3) + 0.0, round(q.Y(), 3) + 0.0, round(q.Z(), 3) + 0.0],
        ]
    return d, points


def _place_all(
    bodies: Sequence[Body | tuple[str, Any]],
) -> list[tuple[str, Any, tuple[float, ...]]]:
    from partkiln.brep import shapes

    out = []
    seen: set[str] = set()
    for row in bodies:
        name, shape = row[0], row[1]
        pose = row[2] if len(row) > 2 else None  # type: ignore[misc]
        if name in seen:
            raise CommandError(f"body {name!r} is listed twice.", code="pk_ref_ambiguous")
        seen.add(name)
        s = placed(shape, pose)
        out.append((name, s, shapes.bbox(s)))
    return out


def interference(
    bodies: Sequence[Body | tuple[str, Any]], *, contact: bool = True
) -> list[dict[str, Any]]:
    """Every pair that shares volume, or (with `contact`) touches.

    Rows `{a, b, mm3, centroid, contact}` in input pair order: `mm3` is the
    exact common volume rounded to 3 dp with its centroid (3 dp), or 0.0
    with `centroid: None` for a pure contact. Pairs whose boxes do not
    overlap are skipped without a boolean.
    """
    from partkiln.brep import shapes

    items = _place_all(bodies)
    rows: list[dict[str, Any]] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            na, sa, ba = items[i]
            nb, sb, bb = items[j]
            if not _boxes_overlap(ba, bb, pad=CONTACT_MM):
                continue
            res = shapes.common(sa, sb)
            vol = 0.0 if res.empty else shapes.volume(res.shape)
            if vol > 1e-9:
                c = shapes.centre_of_mass(res.shape)
                rows.append(
                    {
                        "a": na,
                        "b": nb,
                        "mm3": round(vol, 3) + 0.0,
                        "centroid": [round(v, 3) + 0.0 for v in c],
                        "contact": False,
                    }
                )
            elif contact:
                d, _pts = _distance(sa, sb)
                if d <= CONTACT_MM:
                    rows.append({"a": na, "b": nb, "mm3": 0.0, "centroid": None, "contact": True})
    return rows


def clearance(
    a: Any, b: Any, a_pose: Pose | None = None, b_pose: Pose | None = None
) -> dict[str, Any]:
    """`{mm, points, contact}`: the minimum distance between two placed bodies
    (3 dp; d9.9 pin in a d10 hole -> 0.050) and one closest pair of points.
    Interfering bodies read 0.0 - ask `interference` how much."""
    d, points = _distance(placed(a, a_pose), placed(b, b_pose))
    return {"mm": round(d, 3) + 0.0, "points": points, "contact": d <= CONTACT_MM}


def report(bodies: Sequence[Body | tuple[str, Any]], *, near_mm: float = NEAR_MM) -> dict[str, Any]:
    """The `details.asm` triple (D7): `interference` rows, `contacts` pairs and
    `clearance_mm` per near pair ("a-b" -> mm) for the pairs that neither
    interfere nor touch and whose boxes are within `near_mm`."""
    rows = interference(bodies, contact=True)
    items = _place_all(bodies)
    touching = {(r["a"], r["b"]) for r in rows}
    clearances: dict[str, float] = {}
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            na, sa, ba = items[i]
            nb, sb, bb = items[j]
            if (na, nb) in touching or _box_gap(ba, bb) > near_mm:
                continue
            d, _pts = _distance(sa, sb)
            clearances[f"{na}-{nb}"] = round(d, 3) + 0.0
    return {
        "interference": [
            {k: v for k, v in r.items() if k != "contact"} for r in rows if not r["contact"]
        ],
        "contacts": [[r["a"], r["b"]] for r in rows if r["contact"]],
        "clearance_mm": clearances,
        "contact_tol_mm": CONTACT_MM,
        "fuzzy_mm": FUZZY_MM,
    }


__all__ = [
    "CONTACT_MM",
    "FUZZY_MM",
    "NEAR_MM",
    "Body",
    "bodies_of",
    "clearance",
    "interference",
    "placed",
    "report",
]
