"""Build an independent authored OCCT brake reference, never repair Fusion CAD.

Run with the partkiln sidecar's Python. OCP is imported only during a build;
module import and --help work with the standard library alone. The recipe's
revised analytic oracle supplies all dimensions and acceptance values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any


def build(recipe: Path, out: Path) -> dict[str, Any]:
    """Reconstruct the authored dimensions, export, and independently read back."""
    import OCP
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.BRepCheck import BRepCheck_Analyzer
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
    from OCP.GProp import GProp_GProps
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Reader, STEPControl_Writer
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS

    recipe = recipe.resolve()
    out = out.resolve()
    card = json.loads(recipe.read_text())
    wanted = card["revision"]["expected"]
    rims = wanted["rim_cylinders"]
    outer = float(next(r["radius_mm"] for r in rims if not r["inner"]))
    inner = float(next(r["radius_mm"] for r in rims if r["inner"]))
    bottom, top = float(wanted["min_mm"][2]), float(wanted["max_mm"][2])
    thickness = top - bottom
    volume_tolerance = float(wanted.get("volume_tolerance_mm3", 0.1))
    if not 0 < volume_tolerance <= 0.1:
        raise ValueError("Reference volume tolerance must stay positive and at most 0.1 mm3.")
    if not 0 < inner < outer or thickness <= 0:
        raise ValueError("The annulus needs positive ordered radii and thickness.")
    rows = wanted["rows"]
    if any(row["count"] != len(row["angles_deg"]) for row in rows):
        raise ValueError("Each row's angle list must contain exactly its stated channel count.")
    expected_count = sum(row["count"] for row in rows)
    if expected_count != wanted["inner_void_cylinder_count"]:
        raise ValueError("The total channel count must agree with the row counts.")
    # New directory only: no partial evidence or successful export is overwritten.
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    step = out / "reference.step"
    evidence_path = out / "evidence.json"

    def explore(shape: Any, kind: Any) -> list[Any]:
        items = []
        explorer = TopExp_Explorer(shape, kind)
        while explorer.More():
            items.append(explorer.Current())
            explorer.Next()
        return items

    def xyz(point: Any) -> list[float]:
        return [point.X(), point.Y(), point.Z()]

    def cylinder(
        radius: float,
        height: float,
        centre: tuple[float, float, float],
        direction: tuple[float, float, float],
    ) -> Any:
        axis = gp_Ax2(gp_Pnt(*centre), gp_Dir(*direction))
        return BRepPrimAPI_MakeCylinder(axis, radius, height).Shape()

    def cut(stock: Any, tool: Any) -> Any:
        operation = BRepAlgoAPI_Cut(stock, tool)
        if not operation.IsDone():
            raise RuntimeError("OCCT reference boolean cut failed.")
        return operation.Shape()

    def channel_key(radius: float, z: float, angle: float) -> tuple[float, float, float]:
        return round(radius, 6), round(z, 6), round(angle % 180, 6) % 180

    expected_channels = Counter(
        channel_key(row["radius_mm"], row["centre_height_mm"], angle)
        for row in rows
        for angle in row["angles_deg"]
    )
    channel_radii = {float(row["radius_mm"]) for row in rows}

    def measure(shape: Any) -> dict[str, Any]:
        props = GProp_GProps()
        error = BRepGProp.VolumeProperties_s(shape, props, Eps=1e-10)
        faces = [TopoDS.Face_s(face) for face in explore(shape, TopAbs_FACE)]
        face_edges = [explore(face, TopAbs_EDGE) for face in faces]
        surfaces = [BRepAdaptor_Surface(face, True) for face in faces]
        rim_faces = {}
        records = []
        channels = []
        actual_channels: Counter[tuple[float, float, float]] = Counter()
        for index, (face, surface) in enumerate(zip(faces, surfaces, strict=True)):
            row: dict[str, Any] = {"index": index, "type": str(surface.GetType())}
            if surface.GetType() == GeomAbs_Cylinder:
                cyl = surface.Cylinder()
                radius = cyl.Radius()
                origin, direction = xyz(cyl.Axis().Location()), xyz(cyl.Axis().Direction())
                row.update(
                    radius_mm=radius,
                    axis_origin_mm=origin,
                    axis_direction=direction,
                    inner=face.Orientation() == TopAbs_REVERSED,
                )
                if abs(abs(direction[2]) - 1) < 1e-8:
                    for rim in (inner, outer):
                        if abs(radius - rim) < 1e-7:
                            rim_faces[index] = rim
                elif (
                    abs(direction[2]) < 1e-8
                    and row["inner"]
                    and any(abs(radius - expected) < 1e-7 for expected in channel_radii)
                ):
                    channels.append(row)
                    angle = math.degrees(math.atan2(direction[1], direction[0]))
                    actual_channels[channel_key(radius, origin[2], angle)] += 1
                    row["axis_offset_mm"] = abs(origin[0] * direction[1] - origin[1] * direction[0])
            records.append(row)
        # Topological adjacency: every channel wall must share at least one
        # exact edge with each annular rim. No finite sampling passes this gate.
        for channel in channels:
            adjacent = {
                rim
                for index, rim in rim_faces.items()
                if any(
                    edge.IsSame(rim_edge)
                    for edge in face_edges[channel["index"]]
                    for rim_edge in face_edges[index]
                )
            }
            channel["adjacent_rim_radii_mm"] = sorted(adjacent)
        centre = xyz(props.CentreOfMass())
        volume_delta = props.Mass() - wanted["volume_mm3"]
        centre_delta = [
            actual - expected
            for actual, expected in zip(centre, wanted["centre_of_mass_mm"], strict=True)
        ]
        checks = {
            "valid_solid": BRepCheck_Analyzer(shape).IsValid(),
            "one_solid": len(explore(shape, TopAbs_SOLID)) == 1,
            "channel_count": len(channels) == expected_count,
            "channel_radii_heights_and_axes": actual_channels == expected_channels,
            "radial_axis_origins": all(channel["axis_offset_mm"] < 1e-7 for channel in channels),
            "both_rims_adjacent_to_every_channel": all(
                channel["adjacent_rim_radii_mm"] == [inner, outer] for channel in channels
            ),
            "two_rim_cylinders": len(rim_faces) == 2,
            "all_faces_accounted_for": (
                len(faces) == expected_count + 4
                and sum(surface.GetType() == GeomAbs_Plane for surface in surfaces) == 2
            ),
            "volume": abs(volume_delta) <= volume_tolerance,
            "centre_of_mass": max(map(abs, centre_delta)) <= 1e-4,
        }
        return {
            "volume_mm3": props.Mass(),
            "volume_delta_mm3": volume_delta,
            "centre_of_mass_mm": centre,
            "centre_of_mass_delta_mm": centre_delta,
            "adaptive_error_estimate": error,
            "checks": checks,
            "readback_matches_oracle": all(checks.values()),
            "channel_count": len(channels),
            "face_type_counts": dict(Counter(row["type"] for row in records)),
            "faces": records,
        }

    shape = cut(
        cylinder(outer, thickness, (0, 0, bottom), (0, 0, 1)),
        cylinder(inner, thickness, (0, 0, bottom), (0, 0, 1)),
    )
    for row in rows:
        for theta in row["angles_deg"]:
            angle = math.radians(theta)
            shape = cut(
                shape,
                cylinder(
                    row["radius_mm"],
                    outer + row["radius_mm"] + 1,
                    (0, 0, row["centre_height_mm"]),
                    (math.cos(angle), math.sin(angle), 0),
                ),
            )
    native = measure(shape)
    writer = STEPControl_Writer()
    if writer.Transfer(shape, STEPControl_AsIs) != IFSelect_RetDone:
        raise RuntimeError("OCCT reference STEP transfer failed.")
    if writer.Write(str(step)) != IFSelect_RetDone:
        raise RuntimeError("OCCT reference STEP write failed.")
    reader = STEPControl_Reader()
    if reader.ReadFile(str(step)) != IFSelect_RetDone:
        raise RuntimeError("OCCT reference STEP readback failed.")
    reader.TransferRoots()
    readback = measure(reader.OneShape())
    evidence = {
        "provenance": "independent_authored_OCCT_reference",
        "not_a_repaired_fusion_export": True,
        "recipe": str(recipe),
        "recipe_sha256": hashlib.sha256(recipe.read_bytes()).hexdigest(),
        "ocp_version": OCP.__version__,
        "expected": wanted,
        "acceptance": {
            "volume_tolerance_mm3": volume_tolerance,
            "centre_of_mass_tolerance_mm": 1e-4,
            "mouth_check": "shared topological edges with both exact annular rim faces",
        },
        "native": native,
        "step_readback": readback,
        "step": str(step),
        "step_sha256": hashlib.sha256(step.read_bytes()).hexdigest(),
        "elapsed_s": time.monotonic() - start,
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", required=True, type=Path)
    parser.add_argument(
        "--out", required=True, type=Path, help="New output directory; never replaced"
    )
    args = parser.parse_args()
    evidence = build(args.recipe, args.out)
    passed = all(
        evidence[phase]["readback_matches_oracle"] for phase in ("native", "step_readback")
    )
    print(
        json.dumps(
            {
                "step": evidence["step"],
                "reference_matches_oracle": passed,
                "volume_delta_mm3": evidence["step_readback"]["volume_delta_mm3"],
                "checks": evidence["step_readback"]["checks"],
            }
        )
    )
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
