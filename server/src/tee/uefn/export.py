"""export_for_uefn (12.4): the Blender->UEFN lane nobody has built.

Preflight is a PURE-PYTHON validator over the encoded Fortnite-Ready
budget tables - every violation carries the exact fix (dogma rule 6).
The Blender-side program autogenerates LOD1/LOD2 at -50% steps and
exports a correctly configured FBX; channel packing (Spec=R, Metal=G,
Rough=B) is server-side PIL. Procedural node graphs never transfer -
they must be baked first (validated here as a fact, executed on GPU
machines).
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError


@cache
def budgets() -> dict[str, Any]:
    text = resources.files("tee.uefn").joinpath("data/budgets.json").read_text()
    return json.loads(text)


def _size_class(dims_m: list[float] | None) -> str:
    if not dims_m:
        return "M"
    longest = max(dims_m)
    return "S" if longest < 1.0 else "M" if longest <= 4.0 else "L"


def _is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


def validate_export(asset: dict[str, Any]) -> dict[str, Any]:
    """Preflight one asset description:
    {name, complexity: simple|medium|complex, dims_m, lods: [{tris}],
     textures: [{name, px: [w, h]}], material_sections, collision_meshes:
     ["UCX_Name_00", …], applied_transforms: bool, procedural_materials:
     bool}
    Returns violations with exact fixes + the pass summary."""
    table = budgets()
    violations: list[dict[str, Any]] = []
    checked = 0
    name = asset.get("name", "asset")

    complexity = str(asset.get("complexity", "medium"))
    size = _size_class(asset.get("dims_m"))
    tri_cap = table["lod0_tris"].get(complexity, table["lod0_tris"]["medium"])[size]
    lods = asset.get("lods", [])

    checked += 1
    if not lods:
        violations.append(
            {
                "check": "lods",
                "fix": f"no LODs described - {table['lods']['required']} required "
                "(LOD0-2, -50% steps); export_for_uefn autogenerates LOD1/2",
            }
        )
    else:
        lod0 = int(lods[0].get("tris", 0))
        checked += 1
        if lod0 > tri_cap:
            violations.append(
                {
                    "check": "lod0_tris",
                    "measured": lod0,
                    "cap": tri_cap,
                    "fix": f"LOD0 {lod0:,} tris > the {complexity}/{size} cap "
                    f"{tri_cap:,} - decimate or reclassify complexity",
                }
            )
        checked += 1
        if len(lods) < table["lods"]["required"]:
            violations.append(
                {
                    "check": "lod_count",
                    "measured": len(lods),
                    "fix": f"{len(lods)} LOD(s) < required {table['lods']['required']} "
                    "- autogenerate LOD1/2 at -50% steps (export_for_uefn does this)",
                }
            )
        for i in range(1, len(lods)):
            checked += 1
            prev, cur = int(lods[i - 1].get("tris", 0)), int(lods[i].get("tris", 0))
            if prev and cur > prev * (table["lods"]["reduction_per_step"] + 0.15):
                violations.append(
                    {
                        "check": "lod_reduction",
                        "fix": f"LOD{i} ({cur:,} tris) reduces less than ~50% from "
                        f"LOD{i - 1} ({prev:,}) - decimate harder",
                    }
                )

    tex_table = table["textures"]
    for texture in asset.get("textures", []):
        w, h = (int(v) for v in texture.get("px", [0, 0]))
        tex_name = texture.get("name", "?")
        checked += 1
        if max(w, h) > tex_table["hard_max_px"]:
            violations.append(
                {
                    "check": "texture_max",
                    "texture": tex_name,
                    "fix": f"{tex_name} is {w}x{h} - hard max is "
                    f"{tex_table['hard_max_px']} px; resize",
                }
            )
        elif max(w, h) > tex_table["recommended_max_px"]:
            violations.append(
                {
                    "check": "texture_recommended",
                    "texture": tex_name,
                    "severity": "warning",
                    "fix": f"{tex_name} is {w}x{h} - above the recommended "
                    f"{tex_table['recommended_max_px']} px; consider resizing",
                }
            )
        checked += 1
        if not (_is_power_of_two(w) and _is_power_of_two(h)):
            violations.append(
                {
                    "check": "power_of_two",
                    "texture": tex_name,
                    "fix": f"{tex_name} is {w}x{h} - dimensions must be powers of "
                    "two (e.g. 1024, 2048)",
                }
            )

    checked += 1
    sections = int(asset.get("material_sections", 1))
    if sections > table["materials"]["sections_per_mesh_ideal"]:
        violations.append(
            {
                "check": "material_sections",
                "measured": sections,
                "severity": "warning",
                "fix": f"{sections} material sections - one per mesh is ideal "
                "(merge materials / atlas textures)",
            }
        )

    col = table["collision"]
    collision = asset.get("collision_meshes", [])
    checked += 1
    if len(collision) > col["max_meshes"]:
        violations.append(
            {
                "check": "collision_count",
                "fix": f"{len(collision)} collision meshes > max {col['max_meshes']}",
            }
        )
    for mesh_name in collision:
        checked += 1
        if not str(mesh_name).startswith(col["prefix"]):
            violations.append(
                {
                    "check": "collision_prefix",
                    "mesh": mesh_name,
                    "fix": f"'{mesh_name}' must start with '{col['prefix']}' "
                    "(case-sensitive) to import as collision",
                }
            )

    checked += 1
    if not asset.get("applied_transforms", True):
        violations.append(
            {
                "check": "transforms",
                "fix": "unapplied object transforms - apply rotation & scale "
                "before export (1 uu = 1 cm; the x100 unit boundary is the top "
                "import friction)",
            }
        )
    checked += 1
    if asset.get("procedural_materials"):
        violations.append(
            {
                "check": "procedural_materials",
                "fix": "Blender procedural node graphs never transfer - bake to "
                "textures first (as_photo_material / bake pipeline), then pack "
                "Spec=R/Metal=G/Rough=B",
            }
        )

    hard = [v for v in violations if v.get("severity") != "warning"]
    out: dict[str, Any] = {
        "asset": name,
        "size_class": size,
        "complexity": complexity,
        "checked": checked,
        "violations": violations,
        "export_ready": not hard,
    }
    if not violations:
        out["summary"] = f"{name}: export-ready ({checked} checks)"
    return out


def pack_channels(
    specular: Path | None,
    metallic: Path | None,
    roughness: Path | None,
    out_path: Path,
    *,
    size: int = 1024,
) -> dict[str, Any]:
    """Spec=R, Metal=G, Rough=B utility map (server-side PIL)."""
    try:
        from PIL import Image

        from tee.kernel.imaging import open_image
    except ImportError as exc:
        raise TeeError(
            "extract_extra_missing",
            "Channel packing needs Pillow (the [extract]/[assets] extra).",
            fix="uv sync --extra assets",
        ) from exc
    if not _is_power_of_two(size):
        raise TeeError("bad_size", f"{size} is not a power of two.")

    def load_channel(path: Path | None, default: int) -> Image.Image:
        if path is None:
            return Image.new("L", (size, size), default)
        with open_image(path) as img:
            return img.convert("L").resize((size, size))

    packed = Image.merge(
        "RGB",
        (
            load_channel(specular, 128),
            load_channel(metallic, 0),
            load_channel(roughness, 200),
        ),
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    packed.save(out_path, "PNG")
    return {
        "path": str(out_path),
        "px": [size, size],
        "channels": {"R": "specular", "G": "metallic", "B": "roughness"},
    }


def export_program(entity_ids: list[str], out_path: str, *, autogen_lods: bool = True) -> str:
    """Blender-side program: duplicate to LOD1/2 via decimate at -50%
    steps, name for FBX LOD import, export at cm scale with Face
    smoothing - the documented Fortnite-ready FBX configuration."""
    return f"""
import bpy, time
_t0 = time.time()

def _find(eid):
    want = int(str(eid)[1:])
    for o in bpy.data.objects:
        if o.session_uid == want:
            return o
    return None

_targets = []
for _eid in {json.dumps(entity_ids)}:
    _o = _find(_eid)
    if _o is None:
        raise ValueError("no entity %r for export" % _eid)
    _targets.append(_o)

_lod_objects = []
if {autogen_lods!r}:
    for _o in _targets:
        for _i, _ratio in ((1, 0.5), (2, 0.25)):
            _dup = _o.copy()
            _dup.data = _o.data.copy()
            _dup.name = "%s_LOD%d" % (_o.name, _i)
            bpy.context.scene.collection.objects.link(_dup)
            _mod = _dup.modifiers.new(name="tee_lod", type="DECIMATE")
            _mod.ratio = _ratio
            with bpy.context.temp_override(object=_dup, active_object=_dup,
                                           selected_objects=[_dup]):
                bpy.ops.object.modifier_apply(modifier=_mod.name)
            _lod_objects.append(_dup)

for _o in bpy.data.objects:
    _o.select_set(False)
for _o in _targets + _lod_objects:
    _o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath={out_path!r},
    use_selection=True,
    apply_unit_scale=True,
    global_scale=1.0,
    apply_scale_options="FBX_SCALE_ALL",
    mesh_smooth_type="FACE",
    use_mesh_modifiers=True,
    add_leaf_bones=False,
)
for _dup in _lod_objects:
    bpy.data.objects.remove(_dup, do_unlink=True)
result = {{
    "exported": {out_path!r},
    "objects": len(_targets),
    "lods_generated": len(_lod_objects),
    "wall_s": round(time.time() - _t0, 2),
}}
"""
