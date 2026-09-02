"""Minimum wall thickness by casting rays INWARD from sampled surface points.

Method `ray` (exact): every unique face is sampled on an n x n grid in its
own parameter space (`BRepTools.UVBounds_s` gives the TRIMMED bounds; the
grid sits at the cell centres so no sample lands on an edge), each sample is
classified in UV (`BRepClass_FaceClassifier`) so a point in a hole is
dropped, the outward normal comes from `BRepLProp_SLProps` at that (u, v)
with the face orientation applied, and a `gp_Lin` along the INWARD normal is
handed to `IntCurvesFace_ShapeIntersector.PerformNearest(lin, eps, big)`.
The nearest hit beyond `eps` is the wall under that point. Measured
(2026-09-02, this Mac): one ray on an 11-face shell costs ~70 us; from the
outer skin of a 30x30x10 box shelled 1.2 mm the hits are w = 0 (the sample's
own face, why `eps` exists) and w = 1.2. A hit whose transition is `In`
means the ray was travelling OUTSIDE the material (a degenerate sample) and
is skipped rather than reported as a wall.

Method `mesh` (estimate): `trimesh.proximity.thickness` on the
tessellation (`brep.mesh.to_trimesh`), sampled at triangle centres. It is a
different answer, not a rougher one (the coarse-preview law): it reads the
polygonal skin, so a curved wall reports slightly thin. It is labelled
`estimate` in the result and never feeds a spec verdict. It was expected to
be the cheap path and is NOT on this machine: the F4 housing takes 0.35 s
through trimesh's pure-numpy ray engine against 4 ms for 250 exact rays -
it stays as the cross-check for an imported mesh that has no B-rep.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError

BIG = 1.0e6
EPS = 1.0e-4
METHODS = ("ray", "mesh")


def _r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def _face_label(info: Any) -> dict[str, Any]:
    return {"index": info.index, "type": info.surface_type}


def min_wall(
    shape: Any,
    samples_per_face: int = 5,
    method: str = "ray",
    deflection_mm: float = 0.1,
) -> dict[str, Any]:
    """{min_mm, at, method, samples, hits, face, hit_face, pairs}.

    `samples_per_face` is the grid side (5 -> 25 rays per face); `pairs` lists
    the thinnest span per (face, hit face) pair, thinnest first, at most 8.
    A shape with no solid refuses (`pk_needs`): a wall is a property of
    material, and an open shell has none.
    """
    if method not in METHODS:
        raise CommandError(
            f"unknown wall method {method!r}. Fix: use one of {', '.join(METHODS)}.",
            code="pk_bad_op",
        )
    if samples_per_face < 1:
        raise CommandError(
            f"samples_per_face must be >= 1, got {samples_per_face}. Fix: pass 3-9.",
            code="pk_needs",
        )
    from partkiln.brep import shapes

    if shapes.counts(shape)["solids"] < 1:
        raise CommandError(
            "min_wall needs a solid; this shape has no solid (an open shell has no wall). "
            "Fix: close the shell (validate() names the free edges) or measure the solid.",
            code="pk_needs",
        )
    if method == "mesh":
        return _min_wall_mesh(shape, deflection_mm)
    return _min_wall_ray(shape, samples_per_face)


def _min_wall_ray(shape: Any, n: int) -> dict[str, Any]:
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepClass import BRepClass_FaceClassifier
    from OCP.BRepLProp import BRepLProp_SLProps
    from OCP.BRepTools import BRepTools
    from OCP.gp import gp_Dir, gp_Lin, gp_Pnt2d
    from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON, TopAbs_REVERSED

    from partkiln.brep import query

    faces = query.faces(shape)
    intersector = IntCurvesFace_ShapeIntersector()
    intersector.Load(shape, 1e-6)
    best: dict[str, Any] | None = None
    pairs: dict[tuple[int, int], dict[str, Any]] = {}
    samples = hits = 0
    for info in faces:
        face = info.shape
        surf = BRepAdaptor_Surface(face)
        u0, u1, v0, v1 = BRepTools.UVBounds_s(face)
        props = BRepLProp_SLProps(surf, 1, 1e-9)
        sign = -1.0 if face.Orientation() == TopAbs_REVERSED else 1.0
        for i in range(n):
            u = u0 + (u1 - u0) * (i + 0.5) / n
            for j in range(n):
                v = v0 + (v1 - v0) * (j + 0.5) / n
                if BRepClass_FaceClassifier(face, gp_Pnt2d(u, v), 1e-6).State() not in (
                    TopAbs_IN,
                    TopAbs_ON,
                ):
                    continue
                props.SetParameters(u, v)
                if not props.IsNormalDefined():
                    continue
                samples += 1
                p = props.Value()
                nrm = props.Normal()
                inward = gp_Dir(-sign * nrm.X(), -sign * nrm.Y(), -sign * nrm.Z())
                intersector.PerformNearest(gp_Lin(p, inward), EPS, BIG)
                if not intersector.IsDone() or intersector.NbPnt() < 1:
                    continue
                if intersector.Transition(1).name.endswith("_In"):
                    continue
                w = intersector.WParameter(1)
                hits += 1
                hit_face = intersector.Face(1)
                hit_index = next((f.index for f in faces if f.shape.IsSame(hit_face)), -1)
                row = {
                    "mm": _r3(w),
                    "at": [_r3(p.X()), _r3(p.Y()), _r3(p.Z())],
                    "face": _face_label(info),
                    "hit_face": _face_label(faces[hit_index]) if hit_index >= 0 else None,
                }
                key = (min(info.index, hit_index), max(info.index, hit_index))
                if key not in pairs or w < pairs[key]["mm"]:
                    pairs[key] = row
                if best is None or w < best["mm"]:
                    best = row
    if best is None:
        raise CommandError(
            f"no inward ray hit anything ({samples} samples on {len(faces)} faces). "
            "Fix: the solid may be degenerate; run validate() first.",
            code="pk_op_failed",
        )
    ordered = sorted(pairs.values(), key=lambda r: (r["mm"], r["face"]["index"]))[:8]
    return {
        "min_mm": best["mm"],
        "at": best["at"],
        "face": best["face"],
        "hit_face": best["hit_face"],
        "method": "ray",
        "samples": samples,
        "hits": hits,
        "faces": len(faces),
        "pairs": ordered,
    }


def _min_wall_mesh(shape: Any, deflection_mm: float) -> dict[str, Any]:
    import numpy as np
    import trimesh

    from partkiln.brep import mesh

    tm, report = mesh.to_trimesh(shape, deflection_mm)
    points = tm.triangles_center
    thickness = trimesh.proximity.thickness(
        tm, points, exterior=False, normals=tm.face_normals, method="ray"
    )
    finite = np.isfinite(thickness)
    if not finite.any():
        raise CommandError(
            "the mesh thickness estimate found no wall. Fix: use method='ray' on the B-rep.",
            code="pk_op_failed",
        )
    k = int(np.argmin(np.where(finite, thickness, math.inf)))
    return {
        "min_mm": _r3(thickness[k]),
        "at": [_r3(c) for c in points[k]],
        "face": None,
        "hit_face": None,
        "method": "mesh",
        "estimate": True,
        "samples": len(points),
        "hits": int(finite.sum()),
        "faces": None,
        "pairs": [],
        "triangles": report["triangles"],
        "deflection_mm": deflection_mm,
    }


def check_wall(
    shape: Any, limit_mm: float, samples_per_face: int = 5, method: str = "ray"
) -> dict[str, Any]:
    """{ok, min_mm, limit_mm, at, violations} - the `min_wall_mm` spec rule.

    The violation names got, limit and the point, and the fix is literal:
    "increase min wall to 2 mm at [x, y, z]".
    """
    if limit_mm <= 0:
        raise CommandError(
            f"limit_mm must be > 0, got {limit_mm}. Fix: pass the wall limit in mm.",
            code="pk_needs",
        )
    result = min_wall(shape, samples_per_face=samples_per_face, method=method)
    got = result["min_mm"]
    limit = _r3(limit_mm)
    violations: list[dict[str, Any]] = []
    if got < limit - 5e-4:
        violations.append(
            {
                "rule": "min_wall_mm",
                "got": got,
                "limit": limit,
                "at": result["at"],
                "fix": f"increase min wall to {limit:g} mm at {result['at']} "
                f"(got {got:g} mm between face {result['face']['index']} "
                f"and face {result['hit_face']['index']})"
                if result.get("hit_face") and result.get("face")
                else f"increase min wall to {limit:g} mm at {result['at']} (got {got:g} mm)",
            }
        )
    return {
        "ok": not violations,
        "min_mm": got,
        "limit_mm": limit,
        "at": result["at"],
        "method": result["method"],
        "violations": violations,
    }


__all__ = ["BIG", "EPS", "METHODS", "check_wall", "min_wall"]
