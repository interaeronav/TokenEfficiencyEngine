"""CoACD collision proxies, cached per asset hash (11.4 tier 1).

The settle test needs collision geometry, and a concave mesh under UE/
Blender's convex-hull default sails through itself. CoACD (MIT) decomposes
a concave mesh into a small set of convex hulls that together hug the
shape; those hulls are what the physics engine should simulate.

Decomposition is seconds-to-minutes, so results are cached under
`.tee/proxies/<sha16>/` keyed by the SOURCE FILE's content hash - the same
asset never decomposes twice, and a changed file never reuses a stale
proxy. The cache holds one GLB (all hulls as separate meshes) plus a meta
report; callers get the report either way with `cache_hit` set honestly.

Determinism: CoACD is seeded (default 0) - same file, same params, same
hulls on this build. The seed rides in the cache key so a param change
invalidates cleanly.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

PROXY_LICENSE = "MIT"  # CoACD itself
DEFAULT_THRESHOLD = 0.05
DEFAULT_MAX_HULLS = 32


def _require_deps():
    try:
        import coacd
        import trimesh
    except ImportError as exc:
        raise TeeError(
            "coacd_missing",
            "Collision proxies need coacd + trimesh.",
            fix="uv pip install coacd trimesh",
        ) from exc
    return coacd, trimesh


def cache_key(source: Path, threshold: float, max_hulls: int, seed: int) -> str:
    digest = hashlib.sha256()
    digest.update(source.read_bytes())
    digest.update(f"|{threshold}|{max_hulls}|{seed}|coacd".encode())
    return digest.hexdigest()[:16]


def coacd_proxy(
    source: Path | str,
    cache_root: Path | str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    max_hulls: int = DEFAULT_MAX_HULLS,
    seed: int = 0,
) -> dict[str, Any]:
    """Decompose `source` into convex hulls; return the cached report."""
    coacd, trimesh = _require_deps()
    src = Path(source).expanduser()
    if not src.is_file():
        raise TeeError(
            "no_such_file",
            f"Not a file: {src}",
            fix="Pass a mesh file (glb/gltf/obj/stl/ply).",
        )
    key = cache_key(src, threshold, max_hulls, seed)
    slot = Path(cache_root).expanduser() / key
    meta_path = slot / "proxy.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text())
        meta["cache_hit"] = True
        return meta

    mesh = trimesh.load(str(src), force="mesh")
    started = time.monotonic()
    parts = coacd.run_coacd(
        coacd.Mesh(mesh.vertices, mesh.faces),
        threshold=float(threshold),
        max_convex_hull=int(max_hulls) if max_hulls else -1,
        seed=int(seed),
    )
    scene = trimesh.Scene()
    hull_tris = 0
    for i, (verts, faces) in enumerate(parts):
        hull = trimesh.Trimesh(vertices=verts, faces=faces)
        hull_tris += len(hull.faces)
        scene.add_geometry(hull, node_name=f"hull_{i:03d}")
    slot.mkdir(parents=True, exist_ok=True)
    glb_path = slot / "proxy.glb"
    scene.export(str(glb_path))

    meta = {
        "source": str(src),
        "proxy": str(glb_path),
        "cache_key": key,
        "hulls": len(parts),
        "tris_in": len(mesh.faces),
        "tris_proxy": int(hull_tris),
        "threshold": float(threshold),
        "max_hulls": int(max_hulls),
        "seed": int(seed),
        "wall_s": round(time.monotonic() - started, 1),
        "license": PROXY_LICENSE,
        "cache_hit": False,
    }
    meta_path.write_text(json.dumps(meta, indent=1) + "\n")
    return meta
