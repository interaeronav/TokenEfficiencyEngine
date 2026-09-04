"""Handing a finished part to the next application.

seamkiln's Target table, adapted to a CAD kernel (A66 D1). "Export it as STL"
is not a pipeline: every application disagrees about which way is up and how
big a millimetre is, and a bracket that arrives 1 000x too big lying on its
face has not been integrated with anything. So a handoff is three things:

  1. the file, written by `partkiln.exchange` in the unit that format can
     actually carry
  2. the CONVERSION the target needs - applied to the file where it is needed,
     and NOT applied where the format already states it
  3. for the applications TEE actually drives, the ops that load it; for the
     ones it does not, a refusal that says what to do by hand

What each format states, measured on this build (A66 P0a/P2b):

  glTF (.glb)  DEFINES its own: +Y up, right-handed, metres. partkiln's own
               writer already rotates and scales - `SetLengthUnit_s(doc,
               0.001)` plus `SetInputCoordinateSystem(RWMesh_Zup)` - so F1
               reads back extents [0.1, 0.01, 0.06] m and `dims_zup_m`
               [0.1, 0.06, 0.01]. A GLB therefore needs the IDENTITY
               transform from here, and applying one anyway would
               double-convert. This is the trap the module exists to avoid
               and the manifest says so in `why_no_transform`.
  STEP / IGES  carry a unit in the file (`write.step.unit = MM`), and CAD on
               the far side honours it. No transform; `declares_units` true.
  3MF          states `unit="millimeter"`. No transform.
  STL / OBJ /  declare NOTHING - no unit, no axis, no handedness. Every
  BREP         application guesses. That is where the pain actually is, and
               why a mesh handoff to a Y-up or centimetre target carries an
               explicit transform, baked into the vertices, with the matrix
               printed in the manifest.

partkiln works in millimetres, +Z up, right-handed (D4: mm on the wire, the
fabrication-lane convention). Everything below is a conversion FROM that.

`numpy` is the only import here and it costs nothing; OCP is reached lazily
through `partkiln.exchange`, so `import partkiln.handoff` loads no kernel.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from partkiln.document import CommandError

# Formats that state their own unit and axes; a transform on top of one of
# these is the double-convert bug, not a fix.
SELF_DESCRIBING = ("glb", "gltf")
DECLARES_UNITS = ("glb", "gltf", "step", "stp", "iges", "igs", "3mf")


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
}

# What partkiln itself is. Everything above is a conversion FROM this.
SOURCE = Target("partkiln", "Z", "right", 0.001, "step", False, "mm on the wire (D4)")


def _resolve(name: str) -> Target:
    """A target by name; refuses naming every target rather than guessing."""
    key = str(name).strip().lower()
    spec = TARGETS.get(key)
    if spec is None:
        raise CommandError(
            f"unknown handoff target {name!r}. Targets: {', '.join(sorted(TARGETS))}.",
            code="pk_ref_unknown",
        )
    return spec


target = _resolve


def transform_for(target: Target, fmt: str) -> np.ndarray:
    """The 4x4 a target needs - or identity, when the file already says.

    Identity for glTF BECAUSE partkiln's own writer rotates and scales: it
    sets the XCAF LengthUnit to 0.001 m and declares the input coordinate
    system Z-up, so the .glb on disk is already +Y up in metres, which is
    what the format normatively means. A rotation here would apply the same
    conversion twice. Identity for STEP/IGES/3MF for the same reason in a
    different currency: those files carry "MM" and CAD honours it.

    Everything else (STL, OBJ, BREP) declares nothing, so the conversion has
    to be in the vertices: mm -> the target's unit, +Z up -> its up axis,
    right-handed -> its handedness.
    """
    matrix = np.eye(4)
    kind = str(fmt).strip().lower().lstrip(".")
    if kind in DECLARES_UNITS:
        return matrix
    if target.up == "Y":
        # +Z up -> +Y up: rotate -90 deg about X.
        matrix[:3, :3] = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]])
    if target.handed == "left":
        matrix[:3, :3] = np.diag([1.0, -1.0, 1.0]) @ matrix[:3, :3]
    matrix[:3, :3] *= SOURCE.unit_m / target.unit_m
    return matrix


@dataclass(slots=True)
class Bundle:
    """What was written, where, and in whose coordinates."""

    target: Target
    directory: Path
    fmt: str
    files: dict[str, str] = field(default_factory=dict)
    manifest: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        """Scalars only (hard rule 1): the manifest itself is on disk."""
        return {
            "target": self.target.name,
            "format": self.fmt,
            "directory": str(self.directory),
            "files": dict(self.files),
            "up": self.manifest.get("up", self.target.up),
            "handed": self.manifest.get("handed", self.target.handed),
            "units": self.manifest.get("units", "mm"),
            "target_units": f"1 unit = {self.target.unit_m} m",
            "declares_units": bool(self.manifest.get("declares_units")),
            "transform_applied": bool(self.manifest.get("transform_applied")),
            "driven_by_tee": self.target.driven_by_tee,
            "note": self.target.note,
        }


WRITERS = ("glb", "gltf", "step", "stp", "iges", "igs", "3mf", "stl", "obj", "brep")

DEFAULT_TOL_MM = 0.05
"""Mesh deflection, in MILLIMETRES of the part - D5's export default."""


def _write(name: str, shape: Any, out: Path, fmt: str, deflection: float) -> dict[str, Any]:
    """One shape through `partkiln.exchange`, in whichever writer the format has.

    `deflection` is already in the units of the shape it is handed (see
    `scale_of`): `tessellate` takes an ABSOLUTE deflection, so a shape scaled
    to metres must be meshed at a scaled deflection or the mesh collapses.
    """
    if fmt in ("glb", "gltf"):
        from partkiln.exchange.gltf import write_glb

        return write_glb([(name, shape)], out, deflection_mm=deflection)
    if fmt in ("step", "stp"):
        from partkiln.exchange.step import write_step

        return write_step([(name, shape)], out)
    if fmt in ("iges", "igs"):
        from partkiln.exchange.iges import write_iges

        return write_iges([(name, shape)], out)
    if fmt == "3mf":
        from partkiln.exchange.threemf import write_3mf

        return write_3mf([(name, shape)], out, deflection_mm=deflection)
    if fmt == "stl":
        from partkiln.exchange.stl import write_stl

        return write_stl(shape, out, deflection_mm=deflection)
    if fmt == "obj":
        from partkiln.exchange.obj import write_obj

        return write_obj(shape, out, deflection_mm=deflection)
    from partkiln.exchange.brep_io import write_brep

    return write_brep(shape, out)


def scale_of(matrix: np.ndarray) -> float:
    """The uniform scale a handoff matrix carries (1.0 when it carries none).

    Every matrix here is one uniform scale times a rotation or a reflection,
    so the length of any column is the factor.
    """
    return float(np.linalg.norm(matrix[:3, 0]))


def _transformed(shape: Any, matrix: np.ndarray) -> Any:
    """Bake a 4x4 into a COPY of the shape. Only reached for the formats that
    declare nothing - the self-describing ones never get here."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_GTransform
    from OCP.gp import gp_GTrsf, gp_Mat, gp_XYZ

    rows = matrix[:3, :3]
    gtrsf = gp_GTrsf(
        gp_Mat(*[float(v) for v in rows.reshape(9)]),
        gp_XYZ(*[float(v) for v in matrix[:3, 3]]),
    )
    return BRepBuilderAPI_GTransform(shape, gtrsf, True).Shape()


def _file_frame(target: Target, fmt: str, applied: bool) -> tuple[str, str, str]:
    """What the FILE is in, once the transform (if any) is baked in.

    Three cases, and the third is the one that bites: a self-describing file
    is in its own normative frame (glTF: +Y up, metres); a file written with
    no transform is in partkiln's own (+Z up, mm) and either says so or does
    not; and a file written WITH one is in the target's frame - metres or
    centimetres, its up axis, its handedness - while STL and OBJ still
    declare none of it. `declares_units` is the separate half of the answer.
    """
    if fmt in SELF_DESCRIBING:
        return ("Y", "right", "m")
    if applied:
        return (target.up, target.handed, _unit_name(target.unit_m))
    return (SOURCE.up, SOURCE.handed, "mm")


def _unit_name(unit_m: float) -> str:
    return {1.0: "m", 0.01: "cm", 0.001: "mm"}.get(unit_m, f"{unit_m} m")


def _why(fmt: str, target: Target | None, applied: bool) -> tuple[str | None, str | None]:
    """The two halves of the answer a receiver actually needs: why there is a
    transform, or why there is deliberately none."""
    if applied and target is not None:
        return (
            None,
            f"{fmt.upper()} declares nothing - no unit, no up axis, no handedness - so the "
            f"conversion to {target.name} ({target.up}-up, {target.handed}-handed, 1 unit = "
            f"{target.unit_m} m) is baked into the vertices",
        )
    if fmt in SELF_DESCRIBING:
        return (
            "partkiln's glTF writer already rotates and scales (XCAF LengthUnit 0.001 m + "
            "input coordinate system Z-up), so the .glb on disk is +Y up in metres, which is "
            "what glTF normatively means; a second conversion here would double-convert",
            None,
        )
    if fmt in DECLARES_UNITS:
        return (f"{fmt.upper()} carries its own unit (mm) and the reader honours it", None)
    return (
        f"{fmt.upper()} declares nothing, and nothing has to change: the file is partkiln's "
        f"own mm, +Z up, right-handed - tell the receiver so",
        None,
    )


def manifest(fmt: str, target: str | None = None) -> dict[str, Any]:
    """The handoff facts for one format (and optionally one target), no files.

    `partkiln.methods._manifest` reaches for this by name so an `export`
    decorates itself from the one table rather than a second copy of it -
    and so the glTF answer is right there too: an importer that honours the
    spec converts, so `transform_needed` is FALSE for a .glb even though the
    target is Z-up and the file is Y-up. Guessing that one wrong is how a
    part arrives lying on its face.

    Returns `{}` for a format this module does not write (the drawing
    formats), so the caller's own row stands.
    """
    kind = str(fmt).strip().lower().lstrip(".")
    if kind not in WRITERS:
        return {}
    spec = TARGETS.get(str(target).strip().lower()) if target else None
    matrix = transform_for(spec, kind) if spec is not None else np.eye(4)
    applied = not np.allclose(matrix, np.eye(4))
    file_up, file_handed, file_units = _file_frame(spec or SOURCE, kind, applied)
    why_none, why = _why(kind, spec, applied)
    out: dict[str, Any] = {
        "format": kind,
        "source_units": "mm",
        "source_up": SOURCE.up,
        "source_handed": SOURCE.handed,
        "units": file_units,
        "up": file_up,
        "handed": file_handed,
        "declares_units": kind in DECLARES_UNITS,
        "transform_needed": applied,
        "transform": [[round(v, 9) + 0.0 for v in row] for row in matrix.tolist()],
        "why_no_transform": why_none,
        "why_transform": why,
    }
    if spec is not None:
        out.update(
            {
                "target": spec.name,
                "target_units": _unit_name(spec.unit_m),
                "target_up": spec.up,
                "target_handed": spec.handed,
                "scale_from_mm": SOURCE.unit_m / spec.unit_m,
                "driven_by_tee": spec.driven_by_tee,
                "note": spec.note,
            }
        )
    return out


def bundle(
    shapes_by_name: dict[str, Any],
    out_dir: str | Path,
    *,
    target: str = "blender",
    fmt: str | None = None,
    name: str = "part",
    tol_mm: float = DEFAULT_TOL_MM,
) -> Bundle:
    """Write named shapes plus a manifest for one target application.

    The manifest is the point: units per file, up axis, handedness, the exact
    4x4 (identity or not) and WHY it is what it is, whether TEE can drive the
    load, and the note for a target it cannot.

    `tol_mm` is the mesh deflection in millimetres OF THE PART, and it is
    scaled with the transform before it reaches the tessellator. That is not
    a nicety: measured here, an F1 plate scaled to metres and then meshed at
    the unscaled 0.1 came back as 18 triangles, not watertight, with the
    hole gone - the deflection was the size of the part.
    """
    if not shapes_by_name:
        raise CommandError(
            "handoff needs at least one {name: shape}; build the part first.", code="pk_needs"
        )
    spec = _resolve(target)
    chosen = str(fmt or spec.prefers).strip().lower().lstrip(".")
    if chosen not in WRITERS:
        raise CommandError(
            f"partkiln hands off {', '.join(WRITERS)}, not {chosen!r}. "
            f"{spec.name} prefers {spec.prefers}.",
            code="pk_bad_op",
        )
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    matrix = transform_for(spec, chosen)
    applied = not np.allclose(matrix, np.eye(4))
    deflection = float(tol_mm) * scale_of(matrix)

    file_up, file_handed, file_units = _file_frame(spec, chosen, applied)
    files: dict[str, str] = {}
    written: dict[str, Any] = {}
    for part_name, shape in shapes_by_name.items():
        body = _transformed(shape, matrix) if applied else shape
        result = _write(part_name, body, directory / f"{part_name}.{chosen}", chosen, deflection)
        files[part_name] = result["path"]
        written[part_name] = {
            "units": file_units,
            **{
                key: result[key]
                for key in ("bytes", "triangles", "products", "schema", "extents")
                if key in result
            },
        }

    declares = chosen in DECLARES_UNITS
    manifest: dict[str, Any] = {
        "partkiln_handoff": 1,
        "name": name,
        "format": chosen,
        # up / handed / units describe THE FILE - the thing this manifest is
        # about. What the application expects is under `target`, and the
        # transform above is what bridges the two (identity when the format
        # already does).
        "up": file_up,
        "handed": file_handed,
        "units": file_units,
        "declares_units": declares,
        "source": {"kernel": SOURCE.name, "up": SOURCE.up, "handed": SOURCE.handed, "units": "mm"},
        "target": {
            "name": spec.name,
            "up": spec.up,
            "handed": spec.handed,
            "unit_m": spec.unit_m,
            "prefers": spec.prefers,
        },
        "transform": [[round(v, 9) + 0.0 for v in row] for row in matrix.tolist()],
        "transform_applied": applied,
        "scale": round(scale_of(matrix), 9) + 0.0,
        "tol_mm": float(tol_mm),
        "why_no_transform": _why(chosen, spec, applied)[0],
        "why_transform": _why(chosen, spec, applied)[1],
        "files": written,
        "driven_by_tee": spec.driven_by_tee,
        "note": spec.note,
    }
    manifest["target_name"] = spec.name
    manifest_path = directory / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    files["manifest"] = str(manifest_path)
    return Bundle(target=spec, directory=directory, fmt=chosen, files=files, manifest=manifest)


def ops_for(bundle: Bundle, *, name: str | None = None) -> list[dict[str, Any]]:
    """The batch that loads this bundle - for targets TEE can actually drive.

    Refuses rather than guesses (seamkiln's rule): Godot's bridge has no
    file-import op at all, and emitting one that does not exist would fail
    inside the DCC instead of here, which is the expensive place to find out.

    The two shapes are not the same, because the two lanes in TEE are not:
    Blender takes a batch op whose verb IS `import_file` (the codegen
    dispatches on `op`, not on `kind`, and reads `path` off the op), while
    Unreal cannot import through the typed batch at all - Epic's AssetTools
    has no importer - so TEE's own asset lane calls the adapter method
    `import_asset_file(path, destination, label, location, scale)` directly,
    with metres converted to centimetres on the way. This returns that call's
    shape for Unreal so a caller cannot mistake it for a batch op.
    """
    spec = bundle.target
    if not spec.driven_by_tee:
        raise CommandError(
            f"TEE cannot load a part into {spec.name} for you: {spec.note} The files are "
            f"written in {bundle.directory} and manifest.json says how they are oriented.",
            code="pk_not_served",
        )
    bodies = [(key, path) for key, path in bundle.files.items() if key != "manifest"]
    if spec.name == "unreal":
        return [
            {
                "adapter": "unreal",
                "method": "import_asset_file",
                "params": {
                    "path": path,
                    "destination": "/Game/TeeAssets",
                    "label": name or key,
                    "location": [0.0, 0.0, 0.0],
                    "scale": 1.0,
                },
                "note": "not a batch op: TEE's asset lane calls the adapter method directly "
                "(Epic's AssetTools cannot import), and it needs TEE's content plugin",
            }
            for key, path in bodies
        ]
    return [
        {"op": "import_file", "path": path, "name": name or key, "props": {}}
        for key, path in bodies
    ]


__all__ = [
    "DECLARES_UNITS",
    "DEFAULT_TOL_MM",
    "SELF_DESCRIBING",
    "SOURCE",
    "TARGETS",
    "WRITERS",
    "Bundle",
    "Target",
    "bundle",
    "manifest",
    "ops_for",
    "scale_of",
    "target",
    "transform_for",
]
