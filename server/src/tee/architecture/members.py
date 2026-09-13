"""Explicit profiled construction members in a declared local frame.

A role classifies geometry; it does not infer capacity, joints, a manufactured
section, waterproofing or connected MEP performance. All lengths are millimetres.
"""

from __future__ import annotations

import math

from .model import ArchitectureError, _point, _polygon, positive

# IFC4 classes/enumerators are checked by the installed EXPRESS/schema validator.
IFC_ROLES = {
    "beam": ("IfcBeam", "BEAM"),
    "column": ("IfcColumn", "COLUMN"),
    "brace": ("IfcMember", "BRACE"),
    "frame": ("IfcMember", "MEMBER"),
    "wall_infill": ("IfcWall", "ELEMENTEDWALL"),
    "glazing": ("IfcPlate", "CURTAIN_PANEL"),
    "covering": ("IfcCovering", "USERDEFINED"),
    "pipe": ("IfcPipeSegment", "RIGIDSEGMENT"),
    "duct": ("IfcDuctSegment", "RIGIDSEGMENT"),
}


def frame(entity: dict) -> tuple[list[float], list[float], list[float]]:
    axis, reference = entity["axis"], entity["x_direction"]
    _point(axis, "member.axis", 3)
    _point(reference, "member.x_direction", 3)
    na, nx = math.sqrt(sum(v * v for v in axis)), math.sqrt(sum(v * v for v in reference))
    if min(na, nx) <= 1e-9:
        raise ArchitectureError("ak_member_frame", "Member axis and x_direction must be nonzero.")
    z, x = [v / na for v in axis], [v / nx for v in reference]
    if abs(sum(a * b for a, b in zip(z, x, strict=True))) > 1e-8:
        raise ArchitectureError(
            "ak_member_frame", "Member axis and x_direction must be perpendicular."
        )
    y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]]
    return x, y, z


def profile_shape(entity: dict):
    from shapely.geometry import Polygon

    return Polygon(entity["profile"], entity.get("holes", []))


def validate_member(entity: dict) -> None:
    role = entity["role"]
    if not isinstance(role, str) or role not in IFC_ROLES:
        raise ArchitectureError(
            "ak_member_role", "Member role must be " + ", ".join(IFC_ROLES) + "."
        )
    _point(entity["origin"], "member.origin above storey", 3)
    positive(entity["length"], "member.length")
    frame(entity)
    _polygon(entity["profile"], "member.profile")
    holes = entity.get("holes", [])
    if not isinstance(holes, list) or len(holes) > 32:
        raise ArchitectureError("ak_member_profile", "Member profile supports at most 32 holes.")
    for ring in holes:
        _polygon(ring, "member.hole")
    shape = profile_shape(entity)
    if not shape.is_valid or shape.area <= 1e-6:
        raise ArchitectureError(
            "ak_member_profile",
            "Member holes must lie inside the profile without touching or overlapping.",
        )
    # GEOS permits point-touching interior rings; extrusion would not be manifold.
    from shapely.geometry import Polygon

    outer = Polygon(entity["profile"])
    previous = []
    for ring in holes:
        hole = Polygon(ring)
        if outer.boundary.distance(hole) <= 1e-6 or any(hole.distance(p) <= 1e-6 for p in previous):
            raise ArchitectureError(
                "ak_member_profile", "Member hole boundaries must be strictly separated."
            )
        previous.append(hole)


def member_mesh(entity: dict, entities: dict) -> dict:
    from .penetrations import profile_mesh

    mesh = profile_mesh(entity["profile"], entity.get("holes", []), 0, entity["length"])
    x, y, z = frame(entity)
    origin = list(entity["origin"])
    origin[2] += entities[entity["storey"]]["elevation"]
    mesh["vertices"] = [
        [origin[i] + x[i] * u + y[i] * v + z[i] * w for i in range(3)]
        for u, v, w in mesh["vertices"]
    ]
    return mesh


def member_quantities(entity: dict) -> dict:
    area = profile_shape(entity).area
    return {
        "role": entity["role"],
        "net_profile_area_mm2": area,
        "length_mm": entity["length"],
        "volume_m3": area * entity["length"] / 1e9,
        "hole_count": len(entity.get("holes", [])),
        "quantity_basis": "authored constant-section extrusion; no joint deductions",
        "engineering_verification": "not_established",
    }
