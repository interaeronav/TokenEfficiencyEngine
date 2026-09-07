"""The handoff lands in-server (A68 P3): an exported file into a served lane.

`pk_export`, `sk_handoff` and `fc_export` write a file for another
application to load. Until A68 the route from that file to a scene was
four manual calls, one of them "in a TEE served on Blender" - false since
the multi-lane serve, and the reason partkiln's capture refusal could say
"nothing in this session can do it for you". `land()` is the one function
the three tools share when the caller says `into=`:

1. resolve the lane - a served lane's name, or `auto` for the one served
   lane whose vocabulary imports the file's suffix (`TeeApp.importer_lane`);
2. refuse when that lane cannot import the suffix, naming one that can, or
   the format to export instead (a STEP into Blender: export glb);
3. ask the trust kernel for `write-scene` - the calling tool is tabled
   `write-artifacts`, and a write-artifacts tool may not exercise write-scene
   silently, taint law included;
4. run the import as an ORDINARY checkpointed batch on that lane (Unreal's
   content plugin where the lane imports through `import_asset_file`), so the
   reply carries the checkpoint and the diff like any batch;
5. read the dimensions back and compare them with what the writer declared.

An export with no `into` never touches a scene. Scale is the trap both
handoff modules document: glTF states metres and +Y up and a conforming
importer converts, so a .glb lands at scale 1.0 whatever the source's
units; OBJ/FBX declare nothing, so the scale comes from the units the
writer declared, and a writer that declared none is refused rather than
guessed. A second conversion would double-convert.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# Formats that carry their own units and axis: no scale, ever.
SELF_DESCRIBING = frozenset({"glb", "gltf"})
# Metres per unit for the formats that declare nothing (a scene lane's unit is
# the metre: Blender's, and the glTF convention Unreal's importer converts).
UNIT_M: dict[str, float] = {
    "m": 1.0,
    "metre": 1.0,
    "metres": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "cm": 0.01,
    "mm": 0.001,
    "in": 0.0254,
    "inch": 0.0254,
    "inches": 0.0254,
}
# Read-back dimensions within this band of the writer's: the rotation-no-op
# lesson (an import that "worked" and landed a rotated, wrongly scaled asset).
VERIFY_TOLERANCE = 0.05
# Formats no scene lane imports as a mesh; the fix says what to export instead.
_MESH_ADVICE = frozenset({"step", "stp", "iges", "igs", "brep", "stl", "3mf", "dxf"})


def unit_m(units: str | float | None) -> float | None:
    """Metres per unit from what a writer declared: a name ("mm"), a number,
    or seamkiln's "1 unit = 0.01 m". None when it declared nothing usable."""
    if units is None:
        return None
    if isinstance(units, (int, float)):
        return float(units)
    key = str(units).strip().lower()
    if "=" in key:
        with contextlib.suppress(ValueError, IndexError):
            return float(key.split("=", 1)[1].split()[0])
        return None
    return UNIT_M.get(key)


def scale_for(suffix: str, units: str | float | None) -> float:
    """1.0 for a self-describing file; else metres per declared unit."""
    if suffix in SELF_DESCRIBING:
        return 1.0
    metres = unit_m(units)
    if metres is None:
        raise TeeError(
            "handoff_units_unknown",
            f"'.{suffix}' declares no units and the writer named none ({units!r}), so the "
            "scale cannot be set.",
            fix="Export glb (self-describing: metres, +Y up, the importer converts), or "
            "state the units the writer used: m, cm, mm, in.",
        )
    return metres


def max_deviation(got: list[float], expected: list[float]) -> float:
    worst = 0.0
    for g, e in zip(got, expected, strict=False):
        if e > 1e-6:
            worst = max(worst, abs(g - e) / e)
    return worst


def verify(
    batch: dict[str, Any], expected_dims_m: list[float] | None, *, name: str | None = None
) -> dict[str, Any] | None:
    """The read-back verdict: the landed entity's dimensions against the
    writer's, sorted so the axis order (Y-up file, Z-up scene) cannot fail
    it. None when nothing was declared or nothing reported dimensions."""
    if not expected_dims_m or not batch.get("details"):
        return None
    rows = list(batch["details"].values())
    named = [d for d in rows if name and isinstance(d, dict) and d.get("name") == name]
    for detail in [*named, *rows]:
        if not isinstance(detail, dict):
            continue
        got = detail.get("dimensions") or detail.get("dims_m")
        if not got:
            continue
        expected = sorted(float(v) for v in expected_dims_m)
        read = sorted(float(v) for v in got)
        deviation = max_deviation(read, expected)
        verdict: dict[str, Any] = {
            "expected_dims": [round(v, 4) for v in expected_dims_m],
            "read_back": [round(float(v), 4) for v in got],
            "ok": deviation <= VERIFY_TOLERANCE,
        }
        if not verdict["ok"]:
            verdict["note"] = (
                f"read-back deviates {deviation:.0%} from the writer's extents - "
                "check units/axis of the file"
            )
        return verdict
    return None


def declared_dims_m(path: Path, suffix: str) -> list[float] | None:
    """What the file itself declares, for a verdict when the writer's reply
    carried no extents: a glTF's world-space extents in metres."""
    if suffix not in SELF_DESCRIBING:
        return None
    try:
        from tee.assets import gltf

        probed = gltf.probe(path)
    except Exception:
        return None
    extents = probed.get("extents_m")
    return [float(v) for v in extents] if extents else None


def resolve_lane(app: Any, into: str | None, suffix: str) -> str:
    """`auto` (or nothing) is the one served lane that imports the suffix;
    a name is checked against the served lanes."""
    key = str(into or "").strip()
    if key.lower() in ("", "auto"):
        return app.importer_lane(suffix)
    if key not in app.adapters:
        app.adapter(key)  # raises unknown_adapter naming the served lanes
    return key


def _importers(app: Any, suffix: str) -> list[str]:
    return [name for name in app.adapters if suffix in app.vocab(name).imports]


def _unsupported_fix(app: Any, lane: str, suffix: str) -> str:
    takers = [name for name in _importers(app, suffix) if name != lane]
    if takers:
        return f"Pass into={takers[0]} (served lanes that import .{suffix}: {', '.join(takers)})."
    advice = (
        f"No served lane imports .{suffix}. Export glb instead - it carries its units and "
        "up axis - "
        if suffix in _MESH_ADVICE
        else f"No served lane imports .{suffix}; "
    )
    return (
        f"{advice}and land it in a lane that imports it (Blender takes glb/gltf/obj/fbx, "
        "Unreal glb/gltf/fbx/obj); tee_status lists the served lanes."
    )


def land(
    app: Any,
    *,
    files: dict[str, str],
    into: str | None,
    units: str | float | None = None,
    expected_dims_m: list[float] | None = None,
    caller: str = "handoff",
) -> dict[str, Any]:
    """Land written files in a served scene lane as one checkpointed batch.

    `files` maps the entity name each file lands as to its path (one format
    per call - a bundle's garment and hardware, or a single part). `units`
    is what the writer declared, used only for formats that declare nothing.
    `expected_dims_m` are the writer's extents in metres, for the verdict;
    when absent a glTF's own declared extents stand in. `caller` names the
    tool in the trust decision and the checkpoint label.
    """
    if not files:
        raise TeeError("handoff_nothing_to_land", "no file to land.", fix="Pass the export's path.")
    paths = {str(name): Path(str(path)) for name, path in files.items()}
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        raise TeeError(
            "handoff_file_missing",
            f"not written: {', '.join(missing)}.",
            fix="Export first; the path the export reply names is what lands.",
        )
    suffixes = sorted({p.suffix.lower().lstrip(".") for p in paths.values()})
    if len(suffixes) != 1:
        raise TeeError(
            "handoff_mixed_formats",
            f"one format per landing; got {', '.join(suffixes)}.",
            fix="Land each format with its own call.",
        )
    suffix = suffixes[0]
    lane = resolve_lane(app, into, suffix)
    dcc = app.adapters[lane]
    unreal_shaped = hasattr(dcc, "import_asset_file")
    if suffix not in app.vocab(lane).imports and not unreal_shaped:
        raise TeeError(
            "handoff_import_unsupported",
            f"lane '{lane}' does not import '.{suffix}' files.",
            fix=_unsupported_fix(app, lane, suffix),
        )
    # The calling tool is write-artifacts; landing its file in a scene is a
    # write-scene, and the kernel decides it as one (the taint law included)
    # rather than letting it ride on the export's row.
    app.registry.require("write-scene", name=f"{caller} into={lane}")
    scale = scale_for(suffix, units)
    primary = next(iter(paths))
    if unreal_shaped:
        batch = _through_content_plugin(app, lane, paths, scale, primary)
    else:
        props: dict[str, Any] = {} if scale == 1.0 else {"scale": [scale, scale, scale]}
        ops = [
            {"op": "import_file", "path": str(path), "name": name, "props": dict(props)}
            for name, path in paths.items()
        ]
        batch = app.run_batch(lane, ops, label=f"handoff:{primary}")
    out: dict[str, Any] = {"lane": lane, "scale": scale}
    for key in ("checkpoint", "created", "epoch", "revision"):
        if key in batch:
            out[key] = batch[key]
    if scale != 1.0:
        out["note"] = f"scaled from the writer's units ({units}); the lane's unit is the metre"
    verdict = verify(
        batch, expected_dims_m or declared_dims_m(paths[primary], suffix), name=primary
    )
    if verdict:
        out["verify"] = verdict
    return out


def _through_content_plugin(
    app: Any, lane: str, paths: dict[str, Path], scale: float, primary: str
) -> dict[str, Any]:
    """Unreal: Epic's AssetTools cannot import from the script lane, so the
    file goes through TEE's content plugin - checkpointed by hand to keep the
    rollback guarantee a batch gives (the as_import precedent)."""
    dcc = app.adapter(lane)
    checkpoint = app.checkpoints.create(
        dcc, f"handoff:{primary}", app.cache(lane).revision, lane=lane
    )
    created: list[str] = []
    details: dict[str, Any] = {}
    for name, path in paths.items():
        imported = dcc.import_asset_file(
            str(path), label=name, location=[0.0, 0.0, 0.0], scale=scale
        )
        entity_id = imported.get("entity_id")
        if entity_id:
            created.append(entity_id)
            details[entity_id] = {"name": name, "dims_m": imported.get("dims_m")}
    app.cache(lane).resync(dcc)
    return {
        "checkpoint": checkpoint.id,
        "created": created,
        "details": details,
        **app.cache(lane).stamp(),
    }
