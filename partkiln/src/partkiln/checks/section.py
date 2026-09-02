"""Planar section area: the shape's material on a cutting plane.

`BRepAlgoAPI_Common(solid, big planar face)` returns the part of the face
INSIDE the solid - the section - as one face per connected region; its
exact area is `BRepGProp.SurfaceProperties_s`. Measured (2026-09-02, this
Mac): F1 at x = 50 -> 500.000 mm2 in TWO faces (the plane passes through the
d10 hole's axis, so the 60x10 band loses a 10x10 strip and splits into two
25x10 rectangles), 1.5 ms; the F3-style stepped shaft (d20x50 + d30x30 +
d20x40 along z, 49 480.084 mm3, 7 faces) sectioned through its axis ->
2 700.000 mm2 in ONE face (1000 + 900 + 800). The plane face is sized to the
shape's bounding box (its diagonal, doubled) so it always covers the section
without depending on a magic constant.

A plane that misses the shape is refused (`pk_no_effect`, Law 11 read for a
measure: an empty section is an answer to a different question) with the
bbox in the message so the caller can move the plane.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from partkiln.document import CommandError


def _r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def section_area(
    shape: Any, plane_point: Sequence[float], plane_normal: Sequence[float]
) -> dict[str, Any]:
    """{area_mm2, loops, faces, plane: {point, normal}, per_face: [mm2]}.

    `loops` counts wires over the section faces (an outer boundary plus one
    per island hole), `faces` the connected regions.
    """
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
    from OCP.TopAbs import TopAbs_FACE, TopAbs_WIRE

    from partkiln.brep import shapes

    nx, ny, nz = (float(c) for c in plane_normal)
    if math.hypot(nx, ny, nz) < 1e-12:
        raise CommandError(
            "plane_normal is the zero vector. Fix: pass a direction such as [1, 0, 0].",
            code="pk_needs",
        )
    px, py, pz = (float(c) for c in plane_point)
    x0, y0, z0, x1, y1, z1 = shapes.bbox(shape)
    half = math.dist((x0, y0, z0), (x1, y1, z1)) + math.dist((px, py, pz), (x0, y0, z0))
    half = 2.0 * half + 1.0
    plane = gp_Pln(gp_Pnt(px, py, pz), gp_Dir(nx, ny, nz))
    cutter = BRepBuilderAPI_MakeFace(plane, -half, half, -half, half).Face()
    algo = BRepAlgoAPI_Common(shape, cutter)
    if not algo.IsDone():
        raise CommandError(
            f"section at {list(plane_point)} normal {list(plane_normal)} failed in the boolean. "
            "Fix: run validate() on the shape.",
            code="pk_op_failed",
        )
    result = algo.Shape()
    faces = shapes.unique_subshapes(result, TopAbs_FACE)
    if not faces:
        raise CommandError(
            f"the plane at {[_r3(px), _r3(py), _r3(pz)]} normal "
            f"{[_r3(nx), _r3(ny), _r3(nz)]} misses the shape (bbox "
            f"{[_r3(x0), _r3(y0), _r3(z0)]}..{[_r3(x1), _r3(y1), _r3(z1)]}). "
            "Fix: move the plane point inside the bbox.",
            code="pk_no_effect",
        )
    per_face = sorted(_r3(shapes.area(f)) for f in faces)
    return {
        "area_mm2": _r3(shapes.area(result)),
        "faces": len(faces),
        "loops": len(shapes.unique_subshapes(result, TopAbs_WIRE)),
        "per_face": per_face,
        "plane": {
            "point": [_r3(px), _r3(py), _r3(pz)],
            "normal": [_r3(nx), _r3(ny), _r3(nz)],
        },
    }


__all__ = ["section_area"]
