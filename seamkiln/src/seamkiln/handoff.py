"""Handing a finished garment to the next application.

"Export it as OBJ" is not a pipeline. Every application disagrees about which
way is up and how big a metre is, and a garment that arrives 100x too small
and lying on its face has not been integrated with anything. So a handoff
here is three things and not one:

  1. the mesh, with UVs that came from the flat pattern - exact, not unwrapped
  2. the CONVERSION that target needs, applied to the file, not left as advice
  3. for the applications TEE actually drives, the ops that load it

The conventions, and which are enforced by a format rather than by us:

  glTF (.glb) DEFINES its own: +Y up, right-handed, metres. Importers that
              honour the spec convert on the way in, so a GLB needs NO
              transform from us - and applying one would double-convert. This
              is the trap this module exists to avoid, and it was checked in a
              real Blender 5.2 rather than assumed. A zip-front jacket, handed
              off with NO transform:

                  tallest axis Z, 0.744 m tall, standing at z 0.830 .. 1.574,
                  1 unit = 1 m, UV layer present

              which is a 700 mm jacket body on a 1.79 m mannequin, upright and
              at the right height. The same mesh with our Z-up rotation baked
              in as well:

                  tallest axis Y, sunk to z -0.189 .. 0.175

              lying on its face through the floor. It would have looked like a
              bug in Blender's importer.
  OBJ         defines NOTHING. No units, no axis, no handedness. Every
              application guesses, which is why this is where the pain
              actually is, and why an OBJ handoff carries an explicit
              transform baked into the vertices.

seamkiln works in metres, +Y up, right-handed - trimesh's convention, and
glTF's.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True, slots=True)
class Target:
    """One downstream application and what it expects."""

    name: str
    up: str  # "Y" or "Z"
    handed: str  # "right" or "left"
    unit_m: float  # how many metres ONE of its units is
    prefers: str  # the format to hand it
    driven_by_tee: bool  # is there an adapter that can load it for us?
    note: str = ""


TARGETS: dict[str, Target] = {
    "blender": Target("blender", "Z", "right", 1.0, "glb", True, "TEE adapter: import_file op"),
    "unreal": Target(
        "unreal",
        "Z",
        "left",
        0.01,
        "glb",
        True,
        "TEE adapter: import_asset_file; needs TEE's content plugin in the project",
    ),
    "godot": Target(
        "godot",
        "Y",
        "right",
        1.0,
        "glb",
        False,
        "the bridge's add_node can only instantiate an allowed CLASS - it has no "
        "file-import op. Drop the .glb in the project's res:// tree, let Godot's "
        "own importer take it, then load_scene.",
    ),
    "maya": Target("maya", "Y", "right", 0.01, "obj", False, "default working units are cm"),
    "zbrush": Target(
        "zbrush", "Y", "right", 1.0, "obj", False, "unitless; GoZ rescales to fit the canvas"
    ),
    "houdini": Target("houdini", "Y", "right", 1.0, "obj", False, ""),
    "marvelous": Target(
        "marvelous", "Y", "right", 0.001, "obj", False, "Marvelous Designer works in mm"
    ),
}

# What seamkiln itself is. Everything below is a conversion FROM this.
SOURCE = Target("seamkiln", "Y", "right", 1.0, "glb", False, "")


def transform_for(target: Target, fmt: str) -> np.ndarray:
    """The 4x4 a target needs - or identity, when the format already says.

    A self-describing format is the whole point of a self-describing format.
    glTF states +Y up in metres and conforming importers convert; baking our
    own rotation in on top is the double-convert this module is named after.
    """
    matrix = np.eye(4)
    if fmt in ("glb", "gltf", "usd", "usda", "usdc", "usdz"):
        return matrix
    if target.up == "Z":
        # +Y up -> +Z up: rotate +90 deg about X
        matrix[:3, :3] = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])
    if target.handed == "left":
        matrix[:3, :3] = np.diag([1.0, -1.0, 1.0]) @ matrix[:3, :3]
    matrix[:3, :3] *= SOURCE.unit_m / target.unit_m
    return matrix


@dataclass(slots=True)
class Bundle:
    """What was written, where, and in whose coordinates."""

    target: Target
    directory: Path
    files: dict[str, str] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "target": self.target.name,
            "directory": str(self.directory),
            "files": dict(self.files),
            "up": self.target.up,
            "units": f"1 unit = {self.target.unit_m} m",
            "transform": self.manifest.get("transform"),
            "driven_by_tee": self.target.driven_by_tee,
            "note": self.target.note,
            **{
                k: self.manifest[k] for k in ("vertices", "faces", "hardware") if k in self.manifest
            },
        }


def bundle(
    session: Any,
    out_dir: str | Path,
    *,
    target: str = "blender",
    fmt: str | None = None,
    hardware: bool = True,
) -> Bundle:
    """Write a garment, its UVs and its hardware for one target application."""
    import trimesh

    from seamkiln.drape.preview import garment_mesh, pattern_uv

    if target not in TARGETS:
        raise ValueError(f"unknown target {target!r}. Known: {', '.join(sorted(TARGETS))}")
    if session.garment is None:
        raise ValueError("there is no garment to hand off. Run 'arrange' and 'drape' first.")
    spec = TARGETS[target]
    chosen = (fmt or spec.prefers).lower()
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)

    points = session.drape.points if session.drape else session.garment.points
    # The flat pattern IS the UV map. Every other 3D pipeline pays an unwrap
    # step and guesses where the seams go; here the seams are where the
    # pattern-maker put them, because that is what a pattern is.
    uv = pattern_uv(session.garment.rest_points_mm)
    mesh = garment_mesh(points, session.garment.triangles, uv=uv)
    matrix = transform_for(spec, chosen)
    if not np.allclose(matrix, np.eye(4)):
        mesh.apply_transform(matrix)

    files: dict[str, str] = {}
    garment_file = directory / f"{session.name}-garment.{chosen}"
    mesh.export(garment_file)
    files["garment"] = str(garment_file)

    parts: dict[str, Any] = {}
    if hardware:
        parts = _hardware_parts(session, points)
        if parts["instances"]:
            scene = trimesh.Scene()
            for name, item in parts["meshes"].items():
                scene.add_geometry(item, node_name=name)
            if not np.allclose(matrix, np.eye(4)):
                scene.apply_transform(matrix)
            hardware_file = directory / f"{session.name}-hardware.{chosen}"
            scene.export(hardware_file)
            files["hardware"] = str(hardware_file)

    manifest = {
        "seamkiln_handoff": 1,
        "name": session.name,
        "target": spec.name,
        "format": chosen,
        "up": spec.up,
        "handed": spec.handed,
        "unit_m": spec.unit_m,
        "transform": [[round(v, 6) for v in row] for row in matrix.tolist()],
        "transform_applied": not np.allclose(matrix, np.eye(4)),
        "why_no_transform": (
            "glTF states +Y up in metres and conforming importers convert; a second "
            "rotation here would double-convert"
            if np.allclose(matrix, np.eye(4)) and chosen in ("glb", "gltf")
            else None
        ),
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "uv": "from the flat pattern - exact, not unwrapped",
        "panels": {k: list(v) for k, v in session.garment.panel_slices.items()},
        "fabric": session.fabric,
        "fabric_render": _fabric_render(session.fabric),
        "hardware": parts.get("instances", []),
        "note": spec.note,
    }
    manifest_file = directory / f"{session.name}-handoff.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    files["manifest"] = str(manifest_file)
    return Bundle(target=spec, directory=directory, files=files, manifest=manifest)


def _fabric_render(name: str) -> dict[str, Any]:
    """The card's render properties, for the artist on the other side - and
    the label that says they are a starting point, not a measurement."""
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    try:
        return fabric_by_name(name).render()
    except KeyError:
        return {
            "roughness": None,
            "texture": None,
            "physical": False,
            "note": f"no material card {name!r}",
        }


def _hardware_parts(session: Any, points: np.ndarray) -> dict[str, Any]:
    """Zippers and buttons as geometry, plus what each instance IS.

    The instance list matters more than the meshes: a downstream artist wants
    to swap in their own slider model, and can only do that if TEE said where
    the sliders are and what size they should be.
    """
    import trimesh

    from seamkiln.hardware import zipper as Z

    meshes: dict[str, Any] = {}
    instances: list[dict[str, Any]] = []
    for name, fitted in getattr(session, "zippers", {}).items():
        parts = Z.geometry(fitted, points)
        radius = max(fitted.spec.size / 2000.0, 1e-4)
        for tooth_i, centre in enumerate(parts["teeth"]):
            box = trimesh.creation.box(extents=[radius * 2, radius, radius * 2])
            box.apply_translation(centre)
            meshes[f"zip.{name}.tooth.{tooth_i:04d}"] = box
        length, width = (v / 1000.0 for v in fitted.spec.slider_mm())
        for slider_i, centre in enumerate(parts["sliders"]):
            body = trimesh.creation.box(extents=[width, length, width * 0.6])
            body.apply_translation(centre)
            meshes[f"zip.{name}.slider.{slider_i}"] = body
        instances.append(
            {
                "kind": "zipper",
                **fitted.summary(),
                "slider_mm": [round(v, 2) for v in fitted.spec.slider_mm()],
                "tape_mm": fitted.spec.tape_mm,
            }
        )
    for fastening in getattr(session, "buttons", []):
        spec = fastening.button
        disc = trimesh.creation.cylinder(
            radius=spec.diameter_mm / 2000.0, height=spec.thickness_mm / 1000.0, sections=24
        )
        disc.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        disc.apply_translation(points[fastening.button_at])
        meshes[f"button.{fastening.id}"] = disc
        instances.append({"kind": "button", **fastening.summary()})
    return {"meshes": meshes, "instances": instances}


def ops_for(bundle: Bundle, *, name: str | None = None) -> list[dict[str, Any]]:
    """The batch that loads this bundle - for targets TEE can actually drive.

    Refuses rather than guesses. Godot's bridge has no file-import op, and
    emitting one that does not exist would fail inside the DCC instead of
    here, which is the expensive place to find out.
    """
    spec = bundle.target
    if not spec.driven_by_tee:
        raise ValueError(
            f"TEE cannot load a mesh into {spec.name} for you: {spec.note} "
            f"The files are written and the manifest says how they are oriented."
        )
    label = name or Path(bundle.files["garment"]).stem
    ops = [
        {
            "op": "create",
            "kind": "import_file",
            "name": label,
            "props": {"path": bundle.files["garment"]},
        }
    ]
    if "hardware" in bundle.files:
        ops.append(
            {
                "op": "create",
                "kind": "import_file",
                "name": f"{label}-hardware",
                "props": {"path": bundle.files["hardware"]},
            }
        )
    return ops
