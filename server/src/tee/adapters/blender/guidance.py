"""Small, executable operating cards for Blender's typed lane (A78)."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

UNITS = {"length": "m", "rotation_euler": "rad", "lens": "mm", "up": "+Z"}
TOPICS = {
    "create": "Primitives, units and returned IDs.",
    "material": "Principled assignment and appearance checks.",
    "camera": "Aim a camera; metres and lens mm.",
    "render": "Render, wait, inspect the image.",
    "cadagent_enclosure": "Driven housing and fifteen vents.",
    "cadagent_flange": "Flanged hub and linked bores.",
    "cadagent_joint": "Pivot, driven motion and clearance.",
    "cadagent_f1_wing": "Airfoil sections and articulated flap.",
    "cadagent_f1_brake": "Sixty radial cooling passages.",
    "cadagent_f1_wishbone": "Web, bearing bosses and counterbores.",
    "house": "Modern house: rooms, openings and roof.",
    "cadagent_architecture": "Headless BIM, roof/stair and cabinet workflows through ak_guide.",
    "textures": "UVs, physical scale and portable shaders.",
    "fabric": "Woven relief, roughness and sheen on draped swatches.",
}
_LESSONS = {
    "cadagent_enclosure": (
        "enclosure",
        "Revise the envelope while retaining the cavity and vents.",
    ),
    "cadagent_flange": ("flange", "Drive central and mounting bores through shared parameters."),
    "cadagent_joint": ("joint", "Measure motion around a real pivot and preserve the gap."),
    "cadagent_f1_wing": ("f1_wing", "Revise both spans and verify the flap's relative geometry."),
    "cadagent_f1_brake": ("f1_brake", "Revise two radial passage rows and check actual openings."),
    "cadagent_f1_wishbone": ("f1_wishbone", "Keep the lightening cut through a revised web."),
    "house": ("house", "Drive a compact modern house with rooms, openings and a roof."),
    "textures": (
        "textures",
        "Build, revise and verify texture coordinates and shader dependencies.",
    ),
    "fabric": (
        "fabric",
        "Revise physical weave scale, roughness and sheen while preserving the drape.",
    ),
}
_STAGES = ("build", "revise", "inspect")


def _lesson(topic: str) -> dict[str, Any] | None:
    base, separator, stage = topic.partition(".")
    if base not in _LESSONS or stage not in ("", *_STAGES) or (separator and not stage):
        return None
    filename, purpose = _LESSONS[base]
    overview = {
        "title": TOPICS[base],
        "intent": purpose,
        "stages": {action: f"{base}.{action}" for action in _STAGES},
        "requires": (
            "Blender 5.2; discover bl_execute_python under the existing execution policy. "
            "Choose a dedicated lesson scene. Build refuses an existing lesson collection. "
            "Run build, inspect, revise, inspect; never infer success from an object count."
        ),
        "check": (
            "Stages return measured checks from evaluated geometry or shader dependencies. "
            "Save an editable .blend, reopen and inspect again; inspect actual renders too. "
            "Mesh exchange omits feature history; a material name does not prove appearance."
        ),
        "limits": (
            "Original authored teaching study, not model training or a certified design. "
            "Meshes approximate curved CAD surfaces. Typed batch preflight does not check "
            "these Python stages; bl_execute_python applies its version guard and checkpoint."
        ),
    }
    if not stage:
        return overview
    # Fixed whitelist: no user-controlled path and no Blender imports on the server.
    source = (Path(__file__).with_name("recipes") / f"{filename}.py").read_text()
    code = (
        "import bpy\n"
        "if bpy.app.version < (5, 2, 0):\n"
        "    raise RuntimeError('These lessons require Blender 5.2 or newer.')\n"
        + source
        + f"\nresult = {stage}()\n"
    )
    return {
        "title": TOPICS[base],
        "stage": stage,
        "source_sha256": sha256(source.encode()).hexdigest(),
        "call": {"name": "bl_execute_python", "args": {"code": code, "timeout": 120}},
        "next": overview["stages"],
        "check": overview["check"],
    }


_CARDS = {
    "create": {
        "properties": {
            "all": (
                "name, location[3], rotation_euler[3], scale[3], dimensions[3],"
                " parent, hide_render, hide_viewport"
            ),
            "cube": "size",
            "cylinder": "radius, depth, segments",
            "cone": "radius, radius_top, depth, segments",
            "sphere": "uv_sphere: radius, segments; ico_sphere: radius, subdivisions",
        },
        "ops": [
            {
                "op": "create",
                "kind": "cube",
                "name": "Housing",
                "props": {"dimensions": [0.12, 0.08, 0.02], "location": [0, 0, 0.01]},
            }
        ],
        "check": (
            "Use the returned created[0] in "
            "tee_entity_detail(adapter='blender'); dimensions must be "
            "[0.12,0.08,0.02] m. IDs are returned, never guessed."
        ),
    },
    "material": {
        "ops": [
            {
                "op": "assign_material",
                "id": "b42",
                "props": {
                    "material": "Graphite",
                    "base_color": [0.03, 0.04, 0.05],
                    "metallic": 0.7,
                    "roughness": 0.25,
                },
            }
        ],
        "requires": (
            "Replace b42 with an actual target mesh id from a scene query or "
            "prior batch diff. The script below obtains a new mesh id "
            "automatically."
        ),
        "script": (
            'r=batch([{"op":"create","kind":"cube","name":"Panel","props":{"dim'
            'ensions":[0.12,0.08,0.02]}}],adapter="blender")\nb=r["created"][0]\n'
            'call("bl_assign_material",{"entity_id":b,"material":"Graphite","ba'
            'se_color":[0.03,0.04,0.05],"metallic":0.7,"roughness":0.25})\n'
            'result=detail(b,adapter="blender")'
        ),
        "check": (
            "The returned entity must name Graphite in materials. A "
            "material-name match checks assignment, not appearance; inspect one"
            " rendered view for visual quality."
        ),
        "properties": (
            "base_color RGB/RGBA 0..1; metallic/roughness 0..1; emission_color "
            "RGB/RGBA; emission_strength >=0. Geometry and material are "
            "separate typed ops."
        ),
    },
    "camera": {
        "properties": (
            "camera: lens >0 mm, target world [x,y,z] m, active boolean. All "
            "objects: location m, rotation_euler rad. target and rotation_euler"
            " are alternatives. light: light_type POINT|SUN|SPOT|AREA, energy "
            ">=0, color RGB."
        ),
        "ops": [
            {
                "op": "create",
                "kind": "camera",
                "name": "Product camera",
                "props": {
                    "location": [0.5, -0.6, 0.35],
                    "target": [0, 0, 0.04],
                    "lens": 70,
                    "active": True,
                },
            },
            {
                "op": "create",
                "kind": "light",
                "name": "Key",
                "props": {"light_type": "AREA", "location": [0, -1, 2], "energy": 500},
            },
        ],
        "check": (
            "tee_entity_detail on the returned camera id reads lens_mm, active "
            "and rotation_euler. Verify lens_mm=70 and active=true; a render "
            "checks framing. target is a one-time aim, not a tracking "
            "constraint."
        ),
    },
    "render": {
        "call": {
            "name": "bl_render",
            "args": {
                "width": 1600,
                "height": 1000,
                "samples": 64,
                "path": "/absolute/output/product.jpg",
            },
        },
        "requires": (
            "Create an active camera (camera topic), geometry, materials and "
            "lighting first; use an absolute output path whose parent exists. "
            "bl_render returns job, not the completed file."
        ),
        "check": (
            "tee_job(job_id=<returned job>) until state=done. Read the returned"
            " file path and inspect a view; job completion alone does not grade"
            " appearance. Multi-angle views: set the camera location+target, "
            "render, wait, repeat."
        ),
    },
}


def guide(topic: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"lane": "blender", "units": dict(UNITS)}
    if topic is None:
        return {
            **out,
            "topics": dict(TOPICS),
            "limits": (
                "Lessons disclose build/revise/inspect stages on request. "
                "Python stages use the existing execution policy; syntax is not quality."
            ),
        }
    if topic == "cadagent_architecture":
        from tee.architecture.guidance import guide as architecture_guide

        return {**architecture_guide(), "topic": topic, "next": {"name": "ak_guide", "args": {}}}
    lesson = _lesson(topic)
    if lesson is not None:
        return {**out, "topic": topic, **lesson}
    if topic not in _CARDS:
        raise TeeError(
            "guide_topic",
            f"Blender has no guide topic {topic!r}.",
            fix=f"Choose: {', '.join(TOPICS)}.",
        )
    return {**out, "topic": topic, **deepcopy(_CARDS[topic])}
