"""Fingerprints: the cross-process identity of a shape and of a sub-shape.

Measured (A66 P0a): the sorted, ROUNDED per-face tuple (area, centroid)
hashed in two fresh processes gave the same 16 hex digits for F5 - so a
document's `fingerprint()` (D3) can be compared across a restore, and a
regen that changes nothing is provably a no-op. Rounding happens BEFORE
hashing (1e-3 mm on lengths and positions, 1e-6 mm3 on volume) because the
last bits of an exact `BRepGProp` integral are not reproducible across
thread schedules; nothing else about the shape (map order, tolerances,
triangulation) enters the hash.

`subshape_fingerprint` is naming.py's fallback when history cannot follow a
face or edge (D6): the same rounded tuple, equal for the "same" sub-shape
after an unrelated edit and different for anything that moved by more than
1e-3 mm.
"""

from __future__ import annotations

import hashlib

from partkiln.brep import require_ocp

require_ocp()

from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE  # noqa: E402
from OCP.TopoDS import TopoDS, TopoDS_Shape  # noqa: E402

from partkiln.brep import query  # noqa: E402
from partkiln.brep.shapes import volume  # noqa: E402

FaceKey = tuple[str, float, tuple[float, float, float]]
SubshapeKey = tuple[
    str,
    float,
    tuple[float, float, float],
    tuple[float, float, float] | None,
    float | None,
]


def _r3(v: tuple[float, ...] | None) -> tuple[float, float, float] | None:
    if v is None:
        return None
    return tuple(round(c, 3) + 0.0 for c in v)  # type: ignore[return-value]


def face_keys(shape: TopoDS_Shape) -> list[FaceKey]:
    """Sorted per-face (surface_type, round(area, 3), round(centroid, 3))."""
    keys: list[FaceKey] = [
        (f.surface_type, round(f.area, 3) + 0.0, _r3(f.centroid))  # type: ignore[arg-type]
        for f in query.faces(shape)
    ]
    keys.sort()
    return keys


def shape_fingerprint(shape: TopoDS_Shape) -> str:
    """16 hex sha256 digits over `face_keys` plus round(volume, 6)."""
    payload = repr((face_keys(shape), round(volume(shape), 6) + 0.0))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def subshape_fingerprint(subshape: TopoDS_Shape) -> SubshapeKey:
    """(type, area|length, centroid|midpoint, normal|direction, radius) at 1e-3.

    A face's normal is its outward normal at the parametric midpoint; an
    edge's direction is its canonical line direction (None for curves).
    """
    kind = subshape.ShapeType()
    if kind == TopAbs_FACE:
        info = query.faces(TopoDS.Face_s(subshape))[0]
        return (
            info.surface_type,
            round(info.area, 3) + 0.0,
            _r3(info.centroid),  # type: ignore[return-value]
            _r3(info.normal),
            None if info.radius is None else round(info.radius, 3) + 0.0,
        )
    if kind == TopAbs_EDGE:
        info = query.edges(TopoDS.Edge_s(subshape), face_infos=[])[0]
        return (
            info.curve_type,
            round(info.length, 3) + 0.0,
            _r3(info.midpoint),  # type: ignore[return-value]
            _r3(info.direction),
            None if info.radius is None else round(info.radius, 3) + 0.0,
        )
    from partkiln._errors import KernelError

    raise KernelError(
        f"only a face or an edge has a sub-shape fingerprint, got {kind.name}.",
        fix="fingerprint the whole shape with shape_fingerprint",
    )


__all__ = ["face_keys", "shape_fingerprint", "subshape_fingerprint"]
