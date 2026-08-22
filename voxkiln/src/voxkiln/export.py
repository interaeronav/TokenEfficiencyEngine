"""Repair-before-bake GLB export (research 46) - the license-clean
replacement for upstream's `o_voxel.postprocess.to_glb` (nvdiffrast +
cumesh, NVIDIA non-commercial).

Keeps upstream's two structural ideas and fixes the two trellis-mac
defects:
1. repair FIRST, then freeze the full-res repaired surface as the
   projection reference for texels (trellis-mac discarded it - that, not
   decimation, was its fidelity loss);
2. staged simplify with re-cleaning between stages (decimation can open
   holes).

Because PBR data lives in the sparse voxel attribute volume until export,
hole-fill triangles get plausible textures for free - there is no
"repair after export" texture problem. Pure numpy/scipy/cv2 bake: slower
than a GPU rasterizer but runs identically on macOS/Linux/CUDA-less
machines. GPU acceleration is an optimization slot, not a dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import trimesh

DEFAULT_LAYOUT = {
    "base_color": slice(0, 3),
    "metallic": slice(3, 4),
    "roughness": slice(4, 5),
    "alpha": slice(5, 6),
}

_KEY_SPAN = 2**21


@dataclass
class VoxelAttrs:
    """Sparse voxel PBR attribute volume (the pipeline's native output)."""

    coords: np.ndarray  # [N, 3] int voxel coords
    attrs: np.ndarray  # [N, C] float in [0, 1]
    origin: np.ndarray  # [3] world position of voxel (0,0,0)
    voxel_size: float
    layout: dict[str, slice] = field(default_factory=lambda: dict(DEFAULT_LAYOUT))


def _pack3(c: np.ndarray) -> np.ndarray:
    c = c.astype(np.int64) + (_KEY_SPAN // 2)
    return (c[:, 0] * _KEY_SPAN + c[:, 1]) * _KEY_SPAN + c[:, 2]


def sparse_trilinear(voxel: VoxelAttrs, points: np.ndarray) -> np.ndarray:
    """Exact trilinear sampling of the sparse volume at world positions.
    Missing corner voxels get zero weight; weights renormalize over the
    corners present (matches the vendored torch fallback)."""
    grid = (points - voxel.origin[None, :]) / voxel.voxel_size - 0.5
    base = np.floor(grid).astype(np.int64)
    frac = grid - base

    keys = _pack3(voxel.coords)
    order = np.argsort(keys)
    sorted_keys = keys[order]
    n = len(sorted_keys)

    out = np.zeros((len(points), voxel.attrs.shape[1]), dtype=np.float64)
    wsum = np.zeros((len(points), 1), dtype=np.float64)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                corner = base + np.array([dz, dy, dx])
                w = (
                    (frac[:, 0] if dz else 1 - frac[:, 0])
                    * (frac[:, 1] if dy else 1 - frac[:, 1])
                    * (frac[:, 2] if dx else 1 - frac[:, 2])
                )[:, None]
                q = _pack3(corner)
                pos = np.searchsorted(sorted_keys, q).clip(max=max(n - 1, 0))
                found = (sorted_keys[pos] == q)[:, None]
                vals = voxel.attrs[order[pos]]
                out += np.where(found, vals * w, 0.0)
                wsum += np.where(found, w, 0.0)
    return out / np.clip(wsum, 1e-8, None)


def _staged_simplify(
    mesh: trimesh.Trimesh, target_faces: int
) -> tuple[trimesh.Trimesh, list[dict]]:
    """Upstream's simplify-clean-simplify (postprocess.py:136-149) on the
    CPU quadric decimator, re-repairing between stages."""
    from voxkiln.repair import repair

    log: list[dict] = []
    if len(mesh.faces) <= target_faces:
        return mesh, log
    import fast_simplification

    def simplify_to(m: trimesh.Trimesh, count: int) -> trimesh.Trimesh:
        v, f = fast_simplification.simplify(
            np.asarray(m.vertices, dtype=np.float32),
            np.asarray(m.faces, dtype=np.int64),
            target_count=int(count),
        )
        return trimesh.Trimesh(vertices=v, faces=f, process=False)

    if len(mesh.faces) > 3 * target_faces:
        mesh = simplify_to(mesh, 3 * target_faces)
        mesh, rlog = repair(mesh, level="fast")
        log.append({"op": "simplify_stage", "faces": len(mesh.faces), "repairs": rlog})
    mesh = simplify_to(mesh, target_faces)
    mesh, rlog = repair(mesh, level="fast")
    log.append({"op": "simplify_final", "faces": len(mesh.faces), "repairs": rlog})
    return mesh, log


def _unwrap(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, np.ndarray]:
    """xatlas UV unwrap; returns (rebuilt mesh, per-vertex uv)."""
    import xatlas

    vmapping, indices, uvs = xatlas.parametrize(
        np.asarray(mesh.vertices, dtype=np.float32),
        np.asarray(mesh.faces, dtype=np.uint32),
    )
    out = trimesh.Trimesh(
        vertices=mesh.vertices[vmapping], faces=indices.astype(np.int64), process=False
    )
    return out, uvs.astype(np.float64)


def _rasterize_uv(
    mesh: trimesh.Trimesh, uvs: np.ndarray, texture_size: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """CPU UV-space rasterizer. Returns (positions [T,3], texel_rc [T,2],
    covered mask [S,S]) where positions are 3D points on the mesh surface
    for every covered texel."""
    size = texture_size
    covered = np.zeros((size, size), dtype=bool)
    pos_img = np.zeros((size, size, 3), dtype=np.float64)
    uv_px = uvs * (size - 1)
    for face in mesh.faces:
        tri_uv = uv_px[face]  # [3, 2] in pixel space
        tri_v = mesh.vertices[face]  # [3, 3]
        lo = np.floor(tri_uv.min(axis=0)).astype(int).clip(0, size - 1)
        hi = np.ceil(tri_uv.max(axis=0)).astype(int).clip(0, size - 1)
        if (hi < lo).any():
            continue
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        pts = np.stack([gx.ravel(), gy.ravel()], axis=1).astype(np.float64)
        # barycentric coordinates in UV space
        v0 = tri_uv[1] - tri_uv[0]
        v1 = tri_uv[2] - tri_uv[0]
        v2 = pts - tri_uv[0]
        den = v0[0] * v1[1] - v1[0] * v0[1]
        if abs(den) < 1e-12:
            continue
        b1 = (v2[:, 0] * v1[1] - v1[0] * v2[:, 1]) / den
        b2 = (v0[0] * v2[:, 1] - v2[:, 0] * v0[1]) / den
        b0 = 1.0 - b1 - b2
        eps = -1e-6
        inside = (b0 >= eps) & (b1 >= eps) & (b2 >= eps)
        if not inside.any():
            continue
        p3d = (
            b0[inside, None] * tri_v[0] + b1[inside, None] * tri_v[1] + b2[inside, None] * tri_v[2]
        )
        xs = pts[inside, 0].astype(int)
        ys = pts[inside, 1].astype(int)
        # v axis flips: texture row 0 = v of 1
        rows = (size - 1) - ys
        pos_img[rows, xs] = p3d
        covered[rows, xs] = True
    rc = np.argwhere(covered)
    positions = pos_img[covered]
    return positions, rc, covered


def _project_to_reference(reference: trimesh.Trimesh, points: np.ndarray) -> np.ndarray:
    """Closest points on the frozen full-res repaired surface - upstream's
    cuBVH re-projection ('corrects geometric errors introduced by
    simplification'), done with trimesh's spatial index."""
    try:
        closest, _, _ = trimesh.proximity.closest_point(reference, points)
        return closest
    except BaseException:
        # last-resort: nearest reference vertex (still bounded error)
        from scipy.spatial import cKDTree

        tree = cKDTree(reference.vertices)
        _, idx = tree.query(points)
        return reference.vertices[idx]


def _inpaint_seams(image: np.ndarray, covered: np.ndarray) -> np.ndarray:
    """cv2 TELEA inpaint of uncovered texels near charts (upstream's
    'prevent black seams' step, postprocess.py:288-293)."""
    import cv2

    mask = (~covered).astype(np.uint8)
    dilated = cv2.dilate(covered.astype(np.uint8), np.ones((9, 9), np.uint8))
    ring = (mask & dilated).astype(np.uint8)
    if ring.sum() == 0:
        return image
    img8 = (image * 255).clip(0, 255).astype(np.uint8)
    out = cv2.inpaint(img8, ring, 3, cv2.INPAINT_TELEA)
    result = image.copy()
    sel = ring.astype(bool)
    result[sel] = out[sel] / 255.0
    return result


def export_glb(
    vertices: np.ndarray,
    faces: np.ndarray,
    voxel: VoxelAttrs,
    out_path: str,
    *,
    texture_size: int = 1024,
    target_faces: int = 500_000,
    repair_level: str = "fast",
    max_hole_perimeter: float = 3e-2,
) -> dict[str, Any]:
    """The full chain: repair -> freeze reference -> staged simplify ->
    UV unwrap -> bake -> seam inpaint -> GLB. Returns the export report."""
    from voxkiln.metrics import mesh_stats
    from voxkiln.repair import repair

    report: dict[str, Any] = {"repairs": [], "export": {}}

    mesh = trimesh.Trimesh(
        vertices=np.asarray(vertices, dtype=np.float64),
        faces=np.asarray(faces, dtype=np.int64),
        process=False,
    )
    report["stats_raw"] = mesh_stats(mesh)

    # 1. repair at full resolution
    mesh, rlog = repair(mesh, level=repair_level, max_hole_perimeter=max_hole_perimeter)
    report["repairs"].extend(rlog)

    # 2. freeze the full-res repaired surface (the projection reference)
    reference = mesh.copy()

    # 3. staged simplify + re-clean
    mesh, slog = _staged_simplify(mesh, target_faces)
    report["repairs"].extend(slog)

    # 4. UV unwrap
    mesh, uvs = _unwrap(mesh)

    # 5. bake: texel -> surface point -> reference projection -> volume sample
    grid_res = max(2, round(1.0 / voxel.voxel_size)) if voxel.voxel_size > 0 else 1024
    max_useful = 2 * grid_res
    clamped = min(texture_size, 2048)
    if clamped > max_useful:
        report["export"]["texture_size_clamped"] = {
            "requested": texture_size,
            "actual": max_useful,
            "reason": f"attr volume is {grid_res}^3 - larger textures add no detail",
        }
        clamped = max_useful
    positions, rc, covered = _rasterize_uv(mesh, uvs, clamped)
    if len(positions):
        projected = _project_to_reference(reference, positions)
        samples = sparse_trilinear(voxel, projected)
    else:
        samples = np.zeros((0, voxel.attrs.shape[1]))

    size = clamped
    channels = {
        name: np.zeros((size, size, sl.stop - sl.start)) for name, sl in voxel.layout.items()
    }
    for name, sl in voxel.layout.items():
        img = channels[name]
        img[rc[:, 0], rc[:, 1]] = samples[:, sl]

    base_color = _inpaint_seams(channels["base_color"], covered)
    metallic = channels.get("metallic", np.zeros((size, size, 1)))
    roughness = channels.get("roughness", np.ones((size, size, 1)))
    alpha = channels.get("alpha", np.ones((size, size, 1)))

    # 6. alphaMode from measured alpha (upstream hardcoded OPAQUE + uint8
    #    factor - the issue #91 defect); factor stays float, per spec.
    alpha_cov = alpha[covered] if covered.any() else np.ones((1, 1))
    translucent = alpha_cov.min() < 0.5 and alpha_cov.mean() < 0.999
    alpha_mode = "BLEND" if translucent else "OPAQUE"
    report["export"]["alpha_mode"] = alpha_mode

    from PIL import Image

    rgba = np.concatenate(
        [base_color, alpha if alpha_mode == "BLEND" else np.ones_like(alpha)], axis=2
    )
    base_img = Image.fromarray((rgba * 255).clip(0, 255).astype(np.uint8), mode="RGBA")
    # glTF metallicRoughness packing: G = roughness, B = metallic
    mr = np.zeros((size, size, 3))
    mr[..., 1] = roughness[..., 0]
    mr[..., 2] = metallic[..., 0]
    mr_img = Image.fromarray((mr * 255).clip(0, 255).astype(np.uint8), mode="RGB")

    material = trimesh.visual.material.PBRMaterial(
        baseColorTexture=base_img,
        baseColorFactor=[1.0, 1.0, 1.0, 1.0],
        metallicRoughnessTexture=mr_img,
        metallicFactor=1.0,
        roughnessFactor=1.0,
        alphaMode=alpha_mode,
    )
    mesh.visual = trimesh.visual.TextureVisuals(uv=uvs, material=material)
    mesh.export(out_path)

    # topology stats on a welded copy: xatlas splits vertices along UV
    # seams, which would misreport a closed surface as open
    welded = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False)
    welded.merge_vertices()
    stats = mesh_stats(welded)
    stats["tris"] = len(mesh.faces)
    stats["verts"] = len(mesh.vertices)
    report["stats"] = stats
    report["export"]["texture_size"] = size
    report["export"]["path"] = str(out_path)
    return report
