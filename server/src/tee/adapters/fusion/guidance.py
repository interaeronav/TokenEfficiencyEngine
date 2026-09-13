"""Small, executable operating cards for Fusion's typed lane (A78)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

UNITS = {"length": "mm", "angle": "deg", "volume": "mm3", "internal": "cm; TEE converts"}
TOPICS = {
    "sketch_extrude": "Plate, batch aliases and dimensions.",
    "hole_fillet": "Through hole, edge fillet and face selectors.",
    "parameters": "Bind a dimension and revise its driver.",
    "export": "STEP/F3D units and readback.",
    "cadagent": "Shell and rectangular/circular feature patterns.",
    "cadagent_architecture": "Headless BIM, roof/stair and cabinet workflows through ak_guide.",
    "cadagent_enclosure": "Constrained enclosure, vents and revision.",
    "cadagent_flange": "Revolved hub, bolt circle and driven bores.",
    "cadagent_joint": "Components and measured revolute motion.",
    "cadagent_f1_wing": "F1 Active Aero: sections, hinge and clearance sweep.",
    "cadagent_f1_brake": "F1 brake: staggered radial cooling passages.",
    "cadagent_f1_wishbone": "F1 wishbone: aperture, bosses and stepped bores.",
}
_RECIPE_TOPICS = {
    "cadagent_enclosure",
    "cadagent_flange",
    "cadagent_joint",
    "cadagent_f1_wing",
    "cadagent_f1_brake",
    "cadagent_f1_wishbone",
}
PLATE = [
    {
        "op": "create",
        "kind": "sketch",
        "name": "Plate profile",
        "as": "profile",
        "props": {"plane": "XY", "rects": [[0, 0, 120, 80]]},
    },
    {
        "op": "create",
        "kind": "extrude",
        "name": "Plate",
        "as": "plate",
        "props": {"sketch": "@profile", "distance": 10, "operation": "new_body"},
    },
]
_CARDS = {
    "cadagent": {
        "source": "CADAgent MIT, research 80; no CADAgent backend or add-in required.",
        "ops": [
            {
                "op": "create",
                "kind": "sketch",
                "as": "profile",
                "props": {"rects": [[0, 0, 60, 40]]},
            },
            {
                "op": "create",
                "kind": "extrude",
                "as": "box",
                "props": {"sketch": "@profile", "distance": 20},
            },
            {
                "op": "create",
                "kind": "shell",
                "name": "Open box",
                "props": {"body": "@box", "remove_faces": ["+z"], "inside": 2},
            },
        ],
        "properties": (
            "shell: body, remove_faces directional labels (default [] closed), inside/outside "
            "thickness mm >=0 with at least one >0, tangent bool, shell_type sharp|rounded. "
            "rectangular_pattern: features [feature-id/@seed.feature], axis x|y|z, count "
            "2..1000 INCLUDING seed, spacing signed mm; optional axis2/count2/spacing2 "
            "together, total <=1000. circular_pattern: features, axis x|y|z through the "
            "component origin, count, angle degrees (0,360], default 360. Root-component "
            "native targets only. Pattern @alias and @alias.feature both name its feature."
        ),
        "pattern_examples": [
            {
                "op": "create",
                "kind": "rectangular_pattern",
                "props": {
                    "features": ["@seed.feature"],
                    "axis": "x",
                    "count": 3,
                    "spacing": 15,
                },
            },
            {
                "op": "create",
                "kind": "circular_pattern",
                "props": {
                    "features": ["@seed.feature"],
                    "axis": "z",
                    "count": 4,
                    "angle": 360,
                },
            },
        ],
        "check": (
            "Shell example: fu_measure on the created body must read bbox [60,40,20] mm "
            "and volume 11712 mm3. Pattern examples require an earlier seed feature in "
            "the same batch. Verify actual bodies/hole centres and volume; a requested "
            "count alone is not evidence. Do not pattern the box example along 15 mm: "
            "that spacing overlaps its 60 mm width."
        ),
    },
    "sketch_extrude": {
        "ops": PLATE,
        "properties": (
            "sketch: plane XY|XZ|YZ; rects [[x1,y1,x2,y2]], circles "
            "[[cx,cy,r]], lines [[x1,y1,x2,y2]], points [[x,y]]. extrude: "
            "sketch id/@alias, distance mm, operation "
            "new_body|join|cut|intersect|new_component, profile 'all' or index."
        ),
        "check": (
            "From the batch diff choose a created id whose details.kind is "
            "body, then fu_measure(of=<that id>): bbox_mm=[120,80,10], "
            "volume_mm3=96000. Whole-design measurements include pre-existing "
            "bodies."
        ),
    },
    "hole_fillet": {
        "ops": [
            *PLATE,
            {
                "op": "create",
                "kind": "hole",
                "name": "Bore",
                "props": {
                    "body": "@plate",
                    "face": "+z",
                    "at": [60, 40],
                    "diameter": 8,
                    "through": True,
                },
            },
            {
                "op": "create",
                "kind": "fillet",
                "name": "Edge radius",
                "props": {"body": "@plate", "radius": 1, "edges": {"face": "+z"}},
            },
        ],
        "properties": (
            "hole: body, face +x|-x|+y|-y|+z|-z, at [u,v] or [x,y,z], diameter,"
            " through:true OR depth. fillet: body, radius, edges:'all' or "
            "{face:direction}."
        ),
        "check": (
            "fu_measure on the returned new body checks bbox [120,80,10], "
            "positive volume below 96000 mm3; inspect bore/fillet geometry. "
            "Preflight cannot prove a requested fillet fits the actual solid."
        ),
    },
    "parameters": {
        "ops": [
            {
                "op": "create",
                "kind": "param",
                "name": "A78_width",
                "props": {"value": "120 mm", "units": "mm"},
            },
            {
                "op": "create",
                "kind": "param",
                "name": "A78_thickness",
                "props": {"value": "10 mm", "units": "mm"},
            },
            {
                "op": "create",
                "kind": "sketch",
                "name": "Driven rectangle",
                "as": "profile",
                "props": {
                    "rects": [[0, 0, 120, 80]],
                    "dims": [
                        {
                            "type": "distance",
                            "of": ["r0.bl", "r0.br"],
                            "orientation": "horizontal",
                            "expression": "A78_width",
                        }
                    ],
                },
            },
            {
                "op": "create",
                "kind": "extrude",
                "as": "plate",
                "props": {"sketch": "@profile", "distance": 10},
            },
            {"op": "set", "id": "@plate.feature", "props": {"expression": "A78_thickness"}},
            {"op": "param_set", "name": "A78_width", "expression": "140 mm"},
        ],
        "check": (
            "Use a unique parameter name; fu_params must show A78_width=140 mm."
            " fu_measure on the new body must give bbox [140,80,10], volume "
            "112000 mm3. A78_thickness drives the extrusion via set on "
            "'@plate.feature'; a reference parameter alone does not drive "
            "geometry."
        ),
    },
    "export": {
        "call": {
            "name": "fu_export",
            "args": {"format": "step", "out": "/absolute/output/part.step"},
        },
        "properties": (
            "step|f3d|iges|sat accept component id or whole design (omit of); "
            "obj|stl|3mf may take body. OBJ is cm; STL uses the design length "
            "unit; trust the export units field. format='usd' writes .usdz."
        ),
        "check": (
            "Verify returned bytes/path/units, then re-import in an isolated "
            "document or measure the STEP with a CAD lane and compare bodies, "
            "dimensions and volume. fu_drawing routes through partkiln; Fusion "
            "API cannot create drawing documents."
        ),
    },
}


def guide(topic: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"lane": "fusion", "units": dict(UNITS)}
    if topic is None:
        return {
            **out,
            "topics": dict(TOPICS),
            "limits": (
                "Works in the open design. No typed loft, freeform surfacing or"
                " mesh import; an export is not a manufacturing/compliance "
                "approval."
            ),
        }
    if topic == "cadagent_architecture":
        from tee.architecture.guidance import guide as architecture_guide

        return {**architecture_guide(), "topic": topic, "next": {"name": "ak_guide", "args": {}}}
    if topic in _RECIPE_TOPICS:
        # Long examples cost nothing in the default response. No live connection,
        # training run or model call is implied by returning authored guidance.
        card = json.loads((Path(__file__).parent / "recipes" / f"{topic}.json").read_text())
    elif topic in _CARDS:
        card = deepcopy(_CARDS[topic])
    else:
        raise TeeError(
            "guide_topic",
            f"Fusion has no guide topic {topic!r}.",
            fix=f"Choose: {', '.join(TOPICS)}.",
        )
    return {
        **out,
        "topic": topic,
        "references": (
            "Create with as:'profile', refer to '@profile' later in this batch "
            "only. Extrude/revolve/fillet/hole/chamfer/shell aliases bind their "
            "single body; '@plate.feature' is the feature. Never guess sk1/b1 "
            "or substitute an object name for an id. Pattern aliases bind the feature."
        ),
        **card,
    }
