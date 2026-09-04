"""Minimum wall thickness by casting rays INWARD from sampled surface points.

Method `ray` (an UPPER bound, never a proof) runs two passes over the same
loaded `IntCurvesFace_ShapeIntersector`, and reports the smaller:

1. **The UV grid.** Every unique face is sampled on an n x n grid in its own
   parameter space (`BRepTools.UVBounds_s` gives the TRIMMED bounds; the grid
   sits at the cell centres so no sample lands on an edge), each sample is
   classified in UV (`BRepClass_FaceClassifier`) so a point in a hole is
   dropped, the outward normal comes from `BRepLProp_SLProps` at that (u, v)
   with the face orientation applied, and a `gp_Lin` along the INWARD normal
   is handed to `PerformNearest(lin, eps, big)`. The nearest hit beyond `eps`
   is the wall under that point. A hit whose transition is `In` means the ray
   was travelling OUTSIDE the material (a degenerate sample) and is skipped.
2. **Face-pair extrema.** A grid of cell centres cannot see a wall that is
   thinnest along one generatrix or ON a face boundary, and the answer it
   gives is not even monotone in n: measured 2026-09-04, a 100x60x10 plate
   with one d10 bore at (94.4, 24) - true minimum 0.600 mm to the x=100 face
   - reads 1.922 (n=5), 1.216 (n=7), 0.645 (n=9), 0.768 (n=13), 0.608 (n=21),
   so raising n is NOT the fix. So for each non-adjacent face pair
   `BRepExtrema_DistShapeShape` gives the closest approach, each solution
   point is projected back to its own face with `GeomAPI_ProjectPointOnSurf`
   (`LowerDistanceParameters`; NOT `ParOnFaceS1/S2` - the governing solutions
   are `IsVertex`/`IsOnEdge`, where those accessors are unavailable) and the
   same inward ray is cast from there. That reads 0.600 on the bore and 0.200
   on a wedge whose heel is on both faces' boundary, where the grid reads
   1.922 and 0.680.

The pair pass is O(faces^2) and is gated three ways so it stays cheap: faces
that share an edge are skipped (their closest approach is 0 at that edge),
pairs are visited in ascending bounding-box gap - a LOWER bound on the wall
they could hold - and the loop stops as soon as that gap can no longer beat
the running minimum. Measured on F5 (a 220x220x12 plate with 100 holes, 106
faces): 5 353 candidate pairs, 0 examined, 0.107 s -> 0.112 s. F4's housing
and F1 examine 0 pairs likewise; the bore fixture examines 1.

Neither pass PROVES the minimum: the pair pass finds each pair's global
closest approach, not every local one, and the grid can miss a thin spot
between its samples. So the ray result says `estimate: True, proven: False`
with its sample density, and `check_spec` repeats that in `unproven` rather
than letting a "pass" claim more than was measured.

Method `mesh` (estimate): `trimesh.proximity.thickness` on the tessellation
(`brep.mesh.to_trimesh`), sampled at triangle centres. It is a different
answer, not a rougher one (the coarse-preview law): it reads the polygonal
skin, so a curved wall reports slightly thin. It needs `rtree` (trimesh
builds an R-tree over the triangles), which is the `[mesh]` extra and is
absent by default - a refusal with the install line, never a
`ModuleNotFoundError` three frames down inside trimesh. It was expected to
be the cheap path and is NOT on this machine: the F4 housing takes 0.35 s
through trimesh's pure-numpy ray engine against 4 ms for 250 exact rays - it
stays as the cross-check for an imported mesh that has no B-rep.
"""

from __future__ import annotations

import math
from typing import Any

from partkiln.document import CommandError

BIG = 1.0e6
EPS = 1.0e-4
METHODS = ("ray", "mesh")
# Above this many faces the pair pass is skipped outright: building the
# candidate list is itself O(faces^2) in Python (400 faces = 79 800 gaps,
# ~40 ms; 5 000 faces would be 12.5 M).
FACE_CAP = 400
# And within it, at most this many extrema solves - one costs ~1 ms, so a
# pathological shape cannot turn a measure into a minute.
PAIR_CAP = 1000
MESH_INSTALL_LINE = "uv pip install 'partkiln[mesh]'"


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
    """{min_mm, at, method, samples, hits, face, hit_face, pairs, proven}.

    `samples_per_face` is the grid side (5 -> 25 rays per face); `pairs` lists
    the thinnest span per (face, hit face) pair, thinnest first, at most 8.
    `min_mm` is an UPPER bound on the true wall (`proven` is False, see the
    module docstring), so a check that passes on it is "not disproven", not
    "proven safe". A shape with no solid refuses (`pk_needs`): a wall is a
    property of material, and an open shell has none.
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


class _Rays:
    """The loaded intersector and per-face surface machinery, shared by both
    passes: loading it costs more than a thousand rays (measured 2026-09-02,
    ~70 us per ray on an 11-face shell)."""

    def __init__(self, shape: Any, faces: list[Any]) -> None:
        from OCP.BRepAdaptor import BRepAdaptor_Surface
        from OCP.BRepLProp import BRepLProp_SLProps
        from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
        from OCP.TopAbs import TopAbs_REVERSED

        self.faces = faces
        self.intersector = IntCurvesFace_ShapeIntersector()
        self.intersector.Load(shape, 1e-6)
        self._props = [BRepLProp_SLProps(BRepAdaptor_Surface(f.shape), 1, 1e-9) for f in faces]
        self._sign = [-1.0 if f.shape.Orientation() == TopAbs_REVERSED else 1.0 for f in faces]
        # hash(TopoDS_Shape) is OCP's TShape+location hash: equal for IsSame
        # shapes, so this turns the O(faces) hit-face scan into a lookup.
        self._by_hash = {hash(f.shape): i for i, f in enumerate(faces)}
        self.samples = 0
        self.hits = 0

    def index_of(self, face: Any) -> int:
        i = self._by_hash.get(hash(face))
        if i is not None and self.faces[i].shape.IsSame(face):
            return i
        return next((k for k, f in enumerate(self.faces) if f.shape.IsSame(face)), -1)

    def cast(self, index: int, u: float, v: float) -> tuple[int, float, Any, int] | None:
        """(face index, wall mm, point, hit face index) for the inward ray at
        (u, v) on face `index`, or None where there is nothing to report."""
        from OCP.gp import gp_Dir, gp_Lin

        props = self._props[index]
        props.SetParameters(u, v)
        if not props.IsNormalDefined():
            return None
        self.samples += 1
        point = props.Value()
        normal = props.Normal()
        sign = self._sign[index]
        inward = gp_Dir(-sign * normal.X(), -sign * normal.Y(), -sign * normal.Z())
        self.intersector.PerformNearest(gp_Lin(point, inward), EPS, BIG)
        if not self.intersector.IsDone() or self.intersector.NbPnt() < 1:
            return None
        if self.intersector.Transition(1).name.endswith("_In"):
            return None
        self.hits += 1
        hit_index = self.index_of(self.intersector.Face(1))
        return index, self.intersector.WParameter(1), point, hit_index


class _Thinnest:
    """The running minimum and the per-face-pair table both passes fill."""

    def __init__(self, faces: list[Any]) -> None:
        self.faces = faces
        self.best: dict[str, Any] | None = None
        self.pairs: dict[tuple[int, int], dict[str, Any]] = {}

    def offer(self, hit: tuple[int, float, Any, int] | None) -> None:
        if hit is None:
            return
        index, w, point, hit_index = hit
        info = self.faces[index]
        row = {
            "mm": _r3(w),
            "at": [_r3(point.X()), _r3(point.Y()), _r3(point.Z())],
            "face": _face_label(info),
            "hit_face": _face_label(self.faces[hit_index]) if hit_index >= 0 else None,
        }
        key = (min(index, hit_index), max(index, hit_index))
        if key not in self.pairs or w < self.pairs[key]["mm"]:
            self.pairs[key] = row
        if self.best is None or w < self.best["mm"]:
            self.best = row


def _grid_pass(rays: _Rays, thinnest: _Thinnest, n: int) -> None:
    from OCP.BRepClass import BRepClass_FaceClassifier
    from OCP.BRepTools import BRepTools
    from OCP.gp import gp_Pnt2d
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON

    for i, info in enumerate(rays.faces):
        u0, u1, v0, v1 = BRepTools.UVBounds_s(info.shape)
        for a in range(n):
            u = u0 + (u1 - u0) * (a + 0.5) / n
            for b in range(n):
                v = v0 + (v1 - v0) * (b + 0.5) / n
                if BRepClass_FaceClassifier(info.shape, gp_Pnt2d(u, v), 1e-6).State() not in (
                    TopAbs_IN,
                    TopAbs_ON,
                ):
                    continue
                thinnest.offer(rays.cast(i, u, v))


def _bbox_gap(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Distance between two axis-aligned boxes (xmin ymin zmin xmax ymax zmax).

    A LOWER bound on the distance between the faces inside them, so a pair
    whose gap already exceeds the running minimum can never beat it - the
    prune that keeps F5's 5 353 pairs at 0 extrema solves.
    """
    total = 0.0
    for k in range(3):
        d = max(a[k] - b[k + 3], b[k] - a[k + 3], 0.0)
        total += d * d
    return math.sqrt(total)


def _adjacent_pairs(shape: Any, rays: _Rays) -> set[tuple[int, int]]:
    """Face index pairs that share an edge: their closest approach is 0 AT that
    edge, which is a meeting, not a wall."""
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape

    from partkiln.brep.shapes import as_list

    ancestors = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape, TopAbs_EDGE, TopAbs_FACE, ancestors)
    pairs: set[tuple[int, int]] = set()
    for k in range(1, ancestors.Extent() + 1):
        touching = sorted({rays.index_of(f) for f in as_list(ancestors.FindFromIndex(k))})
        for a in range(len(touching)):
            for b in range(a + 1, len(touching)):
                pairs.add((touching[a], touching[b]))
    return pairs


def _extrema_pass(shape: Any, rays: _Rays, thinnest: _Thinnest) -> tuple[int, bool]:
    """Cast a ray from the closest approach of every face pair that could still
    beat the running minimum. -> (pairs examined, capped)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.GeomAPI import GeomAPI_ProjectPointOnSurf

    faces = rays.faces
    if len(faces) > FACE_CAP:
        return 0, True
    adjacent = _adjacent_pairs(shape, rays)
    candidates = sorted(
        (_bbox_gap(faces[i].bbox, faces[j].bbox), i, j)
        for i in range(len(faces))
        for j in range(i + 1, len(faces))
        if (i, j) not in adjacent
    )
    surfaces: dict[int, Any] = {}
    examined = 0
    for gap, i, j in candidates:
        if thinnest.best is not None and gap >= thinnest.best["mm"] - EPS:
            return examined, False
        if examined >= PAIR_CAP:
            return examined, True
        examined += 1
        extrema = BRepExtrema_DistShapeShape(faces[i].shape, faces[j].shape)
        if not extrema.IsDone():
            continue
        for k in range(1, extrema.NbSolution() + 1):
            for point, index in ((extrema.PointOnShape1(k), i), (extrema.PointOnShape2(k), j)):
                if index not in surfaces:
                    surfaces[index] = BRep_Tool.Surface_s(faces[index].shape)
                projection = GeomAPI_ProjectPointOnSurf(point, surfaces[index])
                if projection.NbPoints() < 1:
                    continue
                u, v = projection.LowerDistanceParameters()
                thinnest.offer(rays.cast(index, u, v))
    return examined, False


def _min_wall_ray(shape: Any, n: int) -> dict[str, Any]:
    from partkiln.brep import query

    faces = query.faces(shape)
    rays = _Rays(shape, faces)
    thinnest = _Thinnest(faces)
    _grid_pass(rays, thinnest, n)
    examined, capped = _extrema_pass(shape, rays, thinnest)
    best = thinnest.best
    if best is None:
        raise CommandError(
            f"no inward ray hit anything ({rays.samples} samples on {len(faces)} faces). "
            "Fix: the solid may be degenerate; run validate() first.",
            code="pk_op_failed",
        )
    ordered = sorted(thinnest.pairs.values(), key=lambda r: (r["mm"], r["face"]["index"]))[:8]
    return {
        "min_mm": best["mm"],
        "at": best["at"],
        "face": best["face"],
        "hit_face": best["hit_face"],
        "method": "ray",
        # An upper bound, and it says so: neither pass proves minimality.
        "estimate": True,
        "proven": False,
        "samples_per_face": n,
        "samples": rays.samples,
        "hits": rays.hits,
        "faces": len(faces),
        "pairs_examined": examined,
        "pairs_capped": capped,
        "pairs": ordered,
    }


def _min_wall_mesh(shape: Any, deflection_mm: float) -> dict[str, Any]:
    import numpy as np
    import trimesh

    from partkiln.brep import mesh

    tm, report = mesh.to_trimesh(shape, deflection_mm)
    points = tm.triangles_center
    try:
        thickness = trimesh.proximity.thickness(
            tm, points, exterior=False, normals=tm.face_normals, method="ray"
        )
    except ImportError as exc:
        # trimesh indexes the triangles with rtree; it is an optional extra,
        # and a missing one is a refusal with the install line (D8), never a
        # ModuleNotFoundError raised three frames down inside trimesh.
        missing = getattr(exc, "name", None) or "rtree"
        raise CommandError(
            f"method='mesh' needs {missing}, which is not installed (trimesh.proximity "
            f"builds an R-tree index over the triangles). Fix: {MESH_INSTALL_LINE} - or use "
            "method='ray', which needs no extra and measures the B-rep itself.",
            code="pk_not_served",
        ) from exc
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
        "proven": False,
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
    """{ok, min_mm, limit_mm, at, proven, violations} - the `min_wall_mm` rule.

    The violation names got, limit and the point, and the fix is literal:
    "increase min wall to 2 mm at [x, y, z]". `ok` is "not disproven at this
    sample density", never a proof: `proven` is False and the caller is
    expected to say so (see `checks.spec`).
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
        "proven": result.get("proven", False),
        "samples_per_face": result.get("samples_per_face"),
        "pairs_examined": result.get("pairs_examined"),
        "violations": violations,
    }


__all__ = ["BIG", "EPS", "FACE_CAP", "METHODS", "PAIR_CAP", "check_wall", "min_wall"]
