"""Generate an original, polygonal two-element Active Aero teaching fixture.

NASA TM 4741 p.3 supplies the symmetric four-digit thickness distribution.
The section coordinates and mechanism dimensions are authored, not team CAD.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


def section(chord: float, leading_x: float, offset_y: float, panels: int = 24) -> list:
    upper = []
    lower = []
    for i in range(panels + 1):
        u = (1 - math.cos(math.pi * i / panels)) / 2
        thickness = (
            5
            * 0.12
            * chord
            * (0.2969 * math.sqrt(u) - 0.1260 * u - 0.3516 * u**2 + 0.2843 * u**3 - 0.1015 * u**4)
        )
        upper.append([round(leading_x + chord * u, 5), round(offset_y + thickness, 5)])
        lower.append([round(leading_x + chord * u, 5), round(offset_y - thickness, 5)])
    return upper + lower[:0:-1]


def area(points: list) -> float:
    return (
        abs(
            sum(
                a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1], strict=True)
            )
        )
        / 2
    )


def bounds(points: list, span: float) -> dict:
    lo = [min(p[k] for p in points) for k in range(2)] + [0]
    hi = [max(p[k] for p in points) for k in range(2)] + [span]
    return {
        "min_mm": lo,
        "max_mm": hi,
        "bbox_mm": [high - low for high, low in zip(hi, lo, strict=True)],
    }


def rotate(points: list, degrees: float) -> list:
    a = math.radians(degrees)
    return [
        [math.cos(a) * x - math.sin(a) * y, math.sin(a) * x + math.cos(a) * y] for x, y in points
    ]


def build_recipe() -> dict:
    profiles = {
        "F1 fixed mainplane": section(360, -420, 15),
        "F1 active flap": section(160, -40, 0),
    }
    ops = [
        {
            "op": "create",
            "kind": "param",
            "name": "F1W_span",
            "props": {"value": "1000 mm", "units": "mm"},
        }
    ]
    for alias, (name, points) in zip(("main", "flap"), profiles.items(), strict=True):
        ops.extend(
            [
                {
                    "op": "create",
                    "kind": "sketch",
                    "name": name + " section",
                    "as": alias + "_section",
                    "props": {
                        "plane": "XY",
                        "lines": [
                            a + b for a, b in zip(points, points[1:] + points[:1], strict=True)
                        ],
                    },
                },
                {
                    "op": "create",
                    "kind": "extrude",
                    "name": name,
                    "as": alias,
                    "props": {
                        "sketch": "@" + alias + "_section",
                        "distance": 1000,
                        "operation": "new_component",
                    },
                },
                {"op": "set", "id": "@" + alias + ".feature", "props": {"expression": "F1W_span"}},
                {"op": "set", "id": "@" + alias + "_section", "props": {"visible": False}},
            ]
        )

    def expected(span: float, angle: float) -> dict:
        bodies = []
        for name, points in profiles.items():
            positioned = rotate(points, -angle) if name == "F1 active flap" else points
            bodies.append(
                {"name": name, "volume_mm3": area(points) * span, **bounds(positioned, span)}
            )
        return {
            "components": 2,
            "bodies": bodies,
            "root_bodies": 0,
            "joints": 1,
            "span_mm": span,
            "rotation_deg": angle,
            "total_volume_mm3": sum(b["volume_mm3"] for b in bodies),
            "minimum_clearance_mm": 10,
        }

    return {
        "topic": "cadagent_f1_wing",
        "title": "Formula One inspired Active Aero: two-element wing and articulated flap",
        "intent": "Build closed cosine-sampled airfoil sections, preserve finite trailing edges, "
        "bind both extrusion spans to one driver, assemble at the actual hinge origin, "
        "then verify a span change and a collision-free flap sweep.",
        "ops": ops,
        "bindings": {
            "main_component": {"kind": "component", "body_name": "F1 fixed mainplane"},
            "flap_component": {"kind": "component", "body_name": "F1 active flap"},
            "wing_joint": {"kind": "joint", "name": "F1 active flap hinge"},
        },
        "assembly": {
            "ops": [
                {
                    "op": "create",
                    "kind": "joint",
                    "name": "F1 active flap hinge",
                    "props": {
                        "one": {"component": "{{main_component}}"},
                        "two": {"component": "{{flap_component}}"},
                        "motion": "revolute",
                        "axis": "z",
                        "angle": 0,
                    },
                }
            ]
        },
        "expected": expected(1000, 0),
        "revision": {
            "ops": [
                {"op": "param_set", "name": "F1W_span", "expression": "1200 mm"},
                {"op": "set", "id": "{{wing_joint}}", "props": {"rotation": 25}},
            ],
            "expected": expected(1200, 25),
        },
        "motion_probe": {
            "angles_deg": [0, 5, 10, 15, 20, 25, 0, 25],
            "continuous_interval_deg": [0, 25],
            "sample_step_deg": 5,
        },
        "geometry": {
            "profiles_mm": profiles,
            "section_area_mm2": {name: area(points) for name, points in profiles.items()},
            "panels_per_surface": 24,
            "span_axis": "z",
            "chord_axis": "x",
            "height_axis": "y",
            "hinge_mm": [0, 0, 0],
            "flap_hinge_chord_fraction": 0.25,
            "relative_angle_sign": -1,
        },
        "check": "Preflight and run ops in a separate empty parametric design. Resolve component "
        "IDs by the named bodies' parent IDs after tee_scene_summary refresh=true. "
        "Bind assembly.ops before preflight/execution; resolve wing_joint from that diff. "
        "Never substitute a body ID for its component or carry @aliases across batches.",
        "revision_check": "Both spans must grow 1000 to 1200 mm with their extrusion expressions "
        "still F1W_span. Check each volume against polygon area times span. "
        "For every motion sample compare actual occurrence vertices in the "
        "mainplane frame to the rotated section, not just rotationValue. "
        "Require at least 10 mm physical clearance between elements and check "
        "the entire 0..25 degree interval with a conservative displacement bound.",
        "lessons": [
            "Four-digit symmetric thickness uses NASA TM 4741's -0.1015 trailing coefficient. "
            "The resulting trailing edge has finite thickness; "
            "the explicit last segment closes it.",
            "These are 49-edge polygonal section solids. Their exact area is computed from the "
            "rounded 0.00001 mm coordinates accepted by the typed lane. "
            "They are reference CAD, not smooth production aero.",
            "The mainplane sits upstream; the flap's quarter-chord hinge is at the origin. "
            "An origin joint cannot invent a different pivot location from the component origins.",
            "A single span parameter drives both components. Root-native shell/pattern operations "
            "are not used on these component bodies.",
            "With mainplane as joint side one and flap as side two, a positive joint rotation "
            "moves this flap clockwise in the mainplane XY frame. Use the measured -1 sign "
            "when comparing geometry; a reported rotation value alone does not fix handedness.",
            "A positive continuous clearance bound proves only this rigid geometric sweep. "
            "It does not establish downforce, drag, stiffness or compliant aero behavior.",
        ],
        "limits": [
            "Original dimensions and symmetric reference sections, "
            "not a team's wing or FIA-approved design.",
            "The 0 and 25 degree positions are teaching states, "
            "not prescribed Corner/Straight Mode angles.",
            "No endplates, actuator, control law, carbon layup, "
            "aeroelasticity or structural validation. "
            "Neither component is grounded; inspect relative motion in the mainplane's frame.",
        ],
        "sources": [
            {
                "title": "Formula 1: 2026 aerodynamics explained",
                "url": "https://www.formula1.com/en/latest/article/2026-regulations-explained-all-you-need-to-know-about-f1s-new-aerodynamics.7IAt0auc32UkCEFE5ypkTB.7IAt0auc32UkCEFE5ypkTB",
            },
            {
                "title": "NASA TM 4741, p.3: four-digit thickness distribution",
                "url": "https://ntrs.nasa.gov/api/citations/19970008124/downloads/19970008124.pdf",
            },
        ],
        "exports": [
            {
                "name": "fu_export",
                "args": {"format": fmt, "out": f"/absolute/output/cadagent_f1_wing.{fmt}"},
            }
            for fmt in ("step", "f3d")
        ],
    }


if __name__ == "__main__":
    target = (
        Path(__file__).resolve().parents[2]
        / "server/src/tee/adapters/fusion/recipes/cadagent_f1_wing.json"
    )
    target.write_text(json.dumps(build_recipe(), indent=2) + "\n")
