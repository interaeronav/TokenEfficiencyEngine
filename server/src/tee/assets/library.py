"""Publish TEE's asset store as a Blender asset library (research 20/21).

Blender 5.2 ships `blender --command asset_listing generate <repo>`, which
indexes a folder of .blend files into the JSON a *remote* asset library
serves. That gives TEE a queryable library index for free - but only if the
assets exist as marked assets inside .blend files, and TEE's store holds
glTF/GLB plus texture sets.

So publishing is two steps: author one .blend per cached model with the
object `asset_mark()`ed and its provenance written into the asset metadata
(licence and attribution travel WITH the asset, which is the whole point of
the licence gate), then run Blender's own indexer over the folder.

Authoring runs in a throwaway headless Blender rather than through the
connected adapter: building a library is not an edit to the user's open
scene, and it must not disturb it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

AUTHOR_PROGRAM = r"""
import bpy, json, sys

payload = json.loads(sys.argv[-1])
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

path = payload["source"]
if path.lower().endswith((".glb", ".gltf")):
    bpy.ops.import_scene.gltf(filepath=path)
else:
    bpy.ops.wm.obj_import(filepath=path)

meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if not meshes:
    print("TEE_NO_MESH", flush=True)
    raise SystemExit(3)

# One asset per file: join to a single object so the library entry is the
# thing the user actually drags in, not a loose hierarchy.
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = payload["name"]

obj.asset_mark()
data = obj.asset_data
data.description = payload.get("description") or payload["name"]
if payload.get("author"):
    data.author = payload["author"]
if payload.get("license"):
    data.license = payload["license"]
for tag in payload.get("tags") or []:
    data.tags.new(tag)
obj.asset_generate_preview()

bpy.ops.wm.save_as_mainfile(filepath=payload["blend"], compress=True)
print("TEE_AUTHORED", payload["blend"], flush=True)
"""


def publish_library(
    store: Any,
    out_dir: Path | str,
    *,
    blender: str,
    limit: int | None = None,
    library_name: str | None = None,
) -> dict[str, Any]:
    """Author one .blend per cached model, then build the library index."""
    import tempfile

    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    # The authoring script must NOT live in the library folder - the indexer
    # walks it, and a stray .py is pollution in something the user may serve.
    scratch = Path(tempfile.mkdtemp(prefix="tee-library-"))
    program = scratch / "author.py"
    program.write_text(AUTHOR_PROGRAM)

    index = store.index()
    models = [e for e in index.values() if e.get("class") != "material" and e.get("primary")]
    if limit:
        models = models[:limit]
    if not models:
        raise TeeError(
            "no_assets_cached",
            "The asset store holds no cached models to publish.",
            fix="Cache assets first with as_import, or ingest a folder with as_ingest.",
        )

    authored: list[str] = []
    failed: list[dict[str, str]] = []
    for entry in models:
        source = (
            entry.get("path")
            if entry.get("source") == "local"
            else str(store.asset_dir(entry["hash"]) / entry["primary"])
        )
        if not Path(source).exists():
            failed.append({"asset": entry.get("id", "?"), "why": "cached file is gone"})
            continue
        name = entry.get("name") or entry.get("id", "asset")
        blend = out / f"{_slug(name)}.blend"
        payload = {
            "source": source,
            "blend": str(blend),
            "name": name,
            "description": entry.get("description") or entry.get("class") or "",
            "author": entry.get("author") or entry.get("attribution") or "",
            "license": entry.get("license") or "",
            "tags": [t for t in (entry.get("tags") or []) if isinstance(t, str)][:8],
        }
        result = subprocess.run(
            [
                blender,
                "--background",
                "--factory-startup",
                "--python",
                str(program),
                "--",
                json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if "TEE_AUTHORED" in result.stdout:
            authored.append(blend.name)
        else:
            failed.append(
                {"asset": entry.get("id", "?"), "why": _last_error(result.stdout, result.stderr)}
            )

    listing = subprocess.run(
        [blender, "--command", "asset_listing", "generate", str(out)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    # Blender writes a placeholder identity ("Your Asset Library" / "Your
    # Name"); a published library should say what it is.
    meta_path = out / "_asset-library-meta.json"
    indexed = 0
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            meta["name"] = library_name or "TEE asset library"
            meta_path.write_text(json.dumps(meta, indent=2))
        except (OSError, ValueError):
            pass
    index_path = out / "_v1" / "asset-index.json"
    if index_path.exists():
        try:
            indexed = int(json.loads(index_path.read_text()).get("asset_count", 0))
        except (OSError, ValueError):
            indexed = 0

    report: dict[str, Any] = {
        "library": str(out),
        "authored": len(authored),
        "indexed": indexed,
        "note": "add this folder as an asset library in Blender "
        "(Preferences > File Paths > Asset Libraries), or serve it as a "
        "remote library",
    }
    if failed:
        report["failed"] = failed[:5]
    if not index_path.exists():
        report["index_error"] = _last_error(listing.stdout, listing.stderr)
    shutil.rmtree(scratch, ignore_errors=True)
    return report


def _slug(name: str) -> str:
    keep = [c if c.isalnum() or c in "-_" else "_" for c in name]
    return "".join(keep)[:60] or "asset"


def _last_error(stdout: str, stderr: str) -> str:
    for stream in (stderr, stdout):
        lines = [line for line in (stream or "").splitlines() if line.strip()]
        if lines:
            return lines[-1][:200]
    return "no output"
