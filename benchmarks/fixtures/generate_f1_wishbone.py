"""Write an original F1-inspired wishbone teaching card and analytic oracle.

No measured team dimensions, downloaded geometry, Fusion calls or third-party
CAD packages. The scalar oracle comes from triangle and cylinder arithmetic.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

RECIPE = Path(__file__).resolve().parents[2] / (
    "server/src/tee/adapters/fusion/recipes/cadagent_f1_wishbone.json"
)
CENTRES = [(30, -70), (30, 70), (250, 0)]


def create(kind: str, name: str, alias: str | None, **props: Any) -> dict[str, Any]:
    op = {"op": "create", "kind": kind, "name": name, "props": props}
    if alias:
        op["as"] = alias
    return op


def drive(alias: str, expression: str) -> dict[str, Any]:
    return {"op": "set", "id": f"@{alias}.feature", "props": {"expression": expression}}


def polygon(points: list[list[float]]) -> list[list[float]]:
    return [a + b for a, b in zip(points, points[1:] + points[:1], strict=True)]


def expected(plate: float, height: float, inboard: float, outboard: float) -> dict[str, Any]:
    # Boss footprints lie entirely inside the solid web, and do not overlap
    # the aperture or one another. The join contributes only above the plate.
    pad_area = math.pi * (2 * 16**2 + 14**2)
    holes = []
    removed = 0.0
    for index, (x, y) in enumerate(CENTRES):
        diameter = inboard if index < 2 else outboard
        cb_diameter, cb_depth = (20, 4) if index < 2 else (24, 6)
        volume = math.pi * (
            (diameter / 2) ** 2 * height + ((cb_diameter / 2) ** 2 - (diameter / 2) ** 2) * cb_depth
        )
        removed += volume
        holes.append(
            {
                "name": ("Aft inboard bearing", "Forward inboard bearing", "Upright bearing")[
                    index
                ],
                "axis": "z",
                "centre_xy_mm": [x, y],
                "diameter_mm": diameter,
                "counterbore_diameter_mm": cb_diameter,
                "counterbore_depth_mm": cb_depth,
                "counterbore_opening_face": "-z",
                "bore_z_interval_mm": [cb_depth, height],
                "counterbore_z_interval_mm": [0, cb_depth],
                "removed_volume_mm3": volume,
            }
        )
    volume = 22500 * plate + pad_area * (height - plate) - removed
    return {
        "bodies": 1,
        "components": 0,
        "features": 6,
        "bbox_mm": [300, 200, height],
        "min_mm": [0, -100, 0],
        "max_mm": [300, 100, height],
        "volume_mm3": volume,
        "volume_formula": (
            "22500*t + pi*(2*16^2+14^2)*(H-t) "
            "- 2*pi*((di/2)^2*H+(10^2-(di/2)^2)*4) "
            "- pi*((do/2)^2*H+(12^2-(do/2)^2)*6)"
        ),
        "formula_inputs_mm": {"t": plate, "H": height, "di": inboard, "do": outboard},
        "solids": [{"name": "CADAgent three-pickup wishbone", "volume_mm3": volume}],
        "web": {
            "outer_vertices_xy_mm": [[0, -100], [300, 0], [0, 100]],
            "aperture_vertices_xy_mm": [[60, -50], [210, 0], [60, 50]],
            "outer_area_mm2": 30000,
            "aperture_area_mm2": 7500,
            "remaining_area_mm2": 22500,
            "thickness_mm": plate,
            "aperture_through": True,
        },
        "bosses": [
            {
                "centre_xy_mm": [x, y],
                "diameter_mm": 32 if i < 2 else 28,
                "outer_cylinder_z_interval_mm": [plate, height],
            }
            for i, (x, y) in enumerate(CENTRES)
        ],
        "holes": holes,
        "inner_cylinders": 6,
        "outer_cylinders": 3,
        "parameter_values_mm": {
            "A79W_plate": plate,
            "A79W_boss_height": height,
            "A79W_inboard_bore": inboard,
            "A79W_outboard_bore": outboard,
        },
        "hardpoints": {
            "inboard_spacing_mm": 140,
            "outboard_reach_from_inboard_axis_mm": 220,
            "pickup_bore_axes": "Three parallel z axes, a planar CAD exercise.",
        },
    }


def recipe() -> dict[str, Any]:
    ops = [
        create("param", "A79W_plate", None, value="6 mm", units="mm"),
        create("param", "A79W_boss_height", None, value="20 mm", units="mm"),
        create("param", "A79W_inboard_bore", None, value="12 mm", units="mm"),
        create("param", "A79W_outboard_bore", None, value="16 mm", units="mm"),
        create(
            "sketch",
            "Wishbone outer web",
            "web",
            plane="XY",
            lines=polygon([[0, -100], [300, 0], [0, 100]]),
        ),
        create("extrude", "CADAgent three-pickup wishbone", "plate", sketch="@web", distance=6),
        drive("plate", "A79W_plate"),
        create(
            "sketch",
            "Triangular lightening aperture",
            "aperture",
            plane="XY",
            lines=polygon([[60, -50], [210, 0], [60, 50]]),
        ),
        create(
            "extrude",
            "Through web lightening cut",
            "lightening",
            sketch="@aperture",
            distance=6,
            operation="cut",
        ),
        drive("lightening", "A79W_plate"),
        create(
            "sketch",
            "Three bearing boss footprints",
            "boss_sections",
            plane="XY",
            circles=[[30, -70, 16], [30, 70, 16], [250, 0, 14]],
        ),
        create(
            "extrude",
            "Three integral bearing bosses",
            "bosses",
            sketch="@boss_sections",
            distance=20,
            operation="join",
            profile="all",
        ),
        drive("bosses", "A79W_boss_height"),
    ]
    for index, (x, y) in enumerate(CENTRES):
        name = ("Aft inboard bearing", "Forward inboard bearing", "Upright bearing")[index]
        alias = f"bearing_{index}"
        ops.append(
            create(
                "hole",
                name,
                alias,
                body="@plate",
                face="-z",
                at=[x, y],
                type="counterbore",
                diameter=12 if index < 2 else 16,
                cbore_diameter=20 if index < 2 else 24,
                cbore_depth=4 if index < 2 else 6,
                through=True,
            )
        )
        ops.append(drive(alias, "A79W_inboard_bore" if index < 2 else "A79W_outboard_bore"))
    ops += [
        {"op": "set", "id": f"@{alias}", "props": {"visible": False}}
        for alias in ("web", "aperture", "boss_sections")
    ]
    revised = expected(8, 24, 14, 18)
    initial = expected(6, 20, 12, 16)
    return {
        "topic": "cadagent_f1_wishbone",
        "title": "F1-inspired three-pickup wishbone with integral bearing bosses",
        "intent": (
            "Build a lightened triangulated suspension study, join three separated boss profiles "
            "into one existing solid, drill three stepped bearing seats from a common datum, "
            "then revise four dependent dimensions without leaving a membrane in the aperture."
        ),
        "context": (
            "Original educational geometry inspired by the three pickup points of a wishbone. "
            "The dimensions and planar parallel-axis bearing arrangement are chosen for this CAD "
            "exercise; they are not a team's design, a working suspension "
            "specification or an FEA result."
        ),
        "ops": ops,
        "expected": initial,
        "check": [
            (
                "Require one root-native solid and no feature warnings; three joined "
                "profiles must not produce three extra bodies."
            ),
            (
                "Read the actual web and aperture vertices and z extents, not only the "
                "body bounding box."
            ),
            (
                "Confirm the triangular aperture is open all the way through the 6 mm web "
                "and has area 7500 mm2."
            ),
            (
                "Check all three boss centres and outside radii, and distinguish their "
                "outward cylinders from the six inward bore/counterbore cylinders."
            ),
            (
                "Match cylindrical axes by projected XY position; an infinite cylinder's "
                "axis origin may slide along z."
            ),
            (
                "Measure each cylindrical face's z span: the two inboard counterbores "
                "open at z=0 and end at z=4; the outboard seat ends at z=6."
            ),
            (
                "Compare actual solid volume with the independent triangle-and-cylinder "
                "formula and independently read the STEP in OCP."
            ),
        ],
        "revision": {
            "ops": [
                {"op": "param_set", "name": name, "expression": value}
                for name, value in (
                    ("A79W_plate", "8 mm"),
                    ("A79W_boss_height", "24 mm"),
                    ("A79W_inboard_bore", "14 mm"),
                    ("A79W_outboard_bore", "18 mm"),
                )
            ],
            "expected": revised,
            "check": [
                (
                    "The creation batch's aliases have expired; change the four named user "
                    "parameters in a new batch."
                ),
                (
                    "The web extrusion AND aperture cut both depend on A79W_plate; after "
                    "revision the aperture remains through 8 mm of material."
                ),
                (
                    "Both inboard hole diameters must increase together to 14 mm; their 20 mm "
                    "counterbore diameter and 4 mm seat depth remain fixed."
                ),
                (
                    "The outboard bore grows to 18 mm, but its 24 mm counterbore diameter and "
                    "6 mm seat depth remain fixed."
                ),
                (
                    "The boss join is measured from the XY datum, so its 24 mm distance is "
                    "the total part height, not 24 mm above the revised web."
                ),
                (
                    "Require the revised per-solid volume and 300 by 200 by 24 mm bounding "
                    "box; a surviving body alone does not prove the dependency graph."
                ),
            ],
            "volume_change_mm3": revised["volume_mm3"] - initial["volume_mm3"],
        },
        "exports": [
            {"tool": "fu_export", "args": {"format": fmt, "out": f"cadagent_f1_wishbone.{fmt}"}}
            for fmt in ("step", "f3d")
        ],
        "teaching": [
            (
                "Separate sketches avoid selecting a profile by Fusion's unstable profile "
                "index: the web and aperture each have one closed region, while the boss "
                "sketch intentionally uses all three regions."
            ),
            (
                "The join intersects the existing web. Its volume contribution is boss "
                "footprint area times (boss height minus web thickness), not three "
                "complete cylinders."
            ),
            (
                "Choose the single shared underside (-z) as the drilling datum. The three "
                "separate boss tops are coplanar and a direction-only face selector "
                "cannot identify which top is intended."
            ),
            (
                "A bore and its counterbore are one feature, but this adapter's "
                "expression setter drives the through diameter only; seat diameters and "
                "depths remain explicit numeric values."
            ),
            (
                "Coordinate-defined polygon sketches are not claimed fully constrained. "
                "The four parameter dependencies drive depth and hole diameter; the "
                "pickup coordinates stay fixed."
            ),
            (
                "Suspension geometry concerns hardpoints and relationships. This planar "
                "exercise demonstrates the CAD dependency graph; it does not establish "
                "camber, anti-dive, compliance, strength or aero performance."
            ),
        ],
        "limits": [
            (
                "Original CAD practice piece; no dimensions were extracted from "
                "photographs or claimed as a real Formula One team's geometry."
            ),
            (
                "No FIA compliance, load capacity, bearing fit, material choice, "
                "machining suitability or vehicle safety is inferred."
            ),
            (
                "No curves, spherical bearings, composite laminates, lofted aero sections "
                "or vehicle kinematics are represented by this polygonal teaching model."
            ),
            (
                "All dimensions are millimetres. The shape stays root-native because the "
                "adapted CADAgent pattern/shell helpers do not accept occurrence proxies."
            ),
        ],
        "sources": [
            {
                "title": (
                    "Formula 1: What's the difference between pull-rod and push-rod suspension?"
                ),
                "url": "https://www.formula1.com/en/latest/article/explainer-whats-the-difference-between-pull-rod-and-push-rod-suspension.1I3wL4LEL0nQZbKZbx1Dhz",
                "accessed": "2026-09-10",
                "supports": (
                    "F1 uses upper and lower wishbones in independently sprung suspension; "
                    "the visible members also have an aerodynamic role. It supplies context, "
                    "not this exercise's dimensions."
                ),
            },
            {
                "title": "McLaren: Under the skin of the MCL39",
                "url": "https://www.mclaren.com/racing/heritage/under-the-skin-of-the-mcl39/",
                "accessed": "2026-09-10",
                "supports": (
                    "Changing suspension member placement changes anti-dive and driver "
                    "feedback, illustrating why a part model alone cannot establish "
                    "suspension performance."
                ),
            },
        ],
    }


def main() -> None:
    card = recipe()
    RECIPE.write_text(json.dumps(card, indent=2) + "\n")
    print(
        json.dumps(
            {
                "path": str(RECIPE),
                "ops": len(card["ops"]),
                "initial_volume_mm3": card["expected"]["volume_mm3"],
                "revised_volume_mm3": card["revision"]["expected"]["volume_mm3"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
