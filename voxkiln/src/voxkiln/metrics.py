"""Topology-aware mesh metrics (research 48 - every metric here was
verified live against seeded-defect fixtures before adoption).

The same code serves twice: the CI test battery asserts exact counts on
synthetic fixtures, and the product report embeds these numbers for the
calling agent. Self-intersection counting is deliberately absent - the
only verified tool is pymeshlab (GPL3), which stays in the dev-only eval
environment, never in the product.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import trimesh

# O-Voxel produces open surfaces ON PURPOSE (leaves, cloth, opacity).
# Watertightness is only a defect where "closed" was expected.
TOPOLOGY_EXPECTATIONS = ("closed", "open", "mixed")


def boundary_edge_count(mesh: trimesh.Trimesh) -> int:
    if len(mesh.faces) == 0:
        return 0
    groups = trimesh.grouping.group_rows(mesh.edges_sorted, require_count=1)
    return len(groups)


def boundary_loop_count(mesh: trimesh.Trimesh) -> int:
    """Boundary loops counted as connected components of the boundary-edge
    graph. Definition changed 2026-08-27 (SI-2): `outline()` built path
    traversals for every loop - 66 s vs 0.5 s on a 22k-component decode
    mesh - and split shared-vertex boundary webs into separate arcs (27,593
    vs 22,892 there). Rows recorded before that date used the old count."""
    if len(mesh.faces) == 0:
        return 0
    edges = mesh.edges_sorted
    groups = trimesh.grouping.group_rows(edges, require_count=1)
    if not len(groups):
        return 0
    boundary = edges[np.asarray(groups).reshape(-1)]
    return len(trimesh.graph.connected_components(boundary))


def nonmanifold_edge_count(mesh: trimesh.Trimesh) -> int:
    counts = Counter(map(tuple, mesh.edges_sorted))
    return sum(1 for n in counts.values() if n > 2)


def degenerate_face_count(mesh: trimesh.Trimesh, height: float = 1e-8) -> int:
    if len(mesh.faces) == 0:
        return 0
    ok = trimesh.triangles.nondegenerate(mesh.triangles, height=height)
    return int((~ok).sum())


def euler_numbers(mesh: trimesh.Trimesh) -> list[int]:
    """Per connected component, computed directly (V - E + F on each
    component's own faces) - trimesh's split() reprocesses geometry and
    can shift the value on open meshes."""
    if len(mesh.faces) == 0:
        return [0]
    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces))
    )
    out = []
    for comp in components:
        faces = mesh.faces[comp]
        v = len(np.unique(faces))
        edges = np.sort(faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2), axis=1)
        e = len(np.unique(edges, axis=0))
        out.append(int(v - e + len(faces)))
    return out


def uv_overlap_fraction(mesh: trimesh.Trimesh) -> float | None:
    """1 - union_area/total_area over UV triangles; None when no UVs."""
    uv = getattr(mesh.visual, "uv", None)
    if uv is None or len(uv) == 0:
        return None
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    tris = []
    total = 0.0
    for face in mesh.faces:
        pts = uv[face]
        poly = Polygon(pts)
        if poly.is_valid and poly.area > 0:
            tris.append(poly)
            total += poly.area
    if not tris or total <= 0:
        return None
    union = unary_union(tris).area
    return float(max(0.0, 1.0 - union / total))


def texel_density_cv(mesh: trimesh.Trimesh) -> float | None:
    """Coefficient of variation of per-face sqrt(uv_area / 3d_area)."""
    uv = getattr(mesh.visual, "uv", None)
    if uv is None or len(uv) == 0:
        return None
    areas3d = mesh.area_faces
    uv_tri = uv[mesh.faces]
    d1 = uv_tri[:, 1] - uv_tri[:, 0]
    d2 = uv_tri[:, 2] - uv_tri[:, 0]
    areas_uv = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0])
    valid = areas3d > 1e-12
    if valid.sum() == 0:
        return None
    density = np.sqrt(areas_uv[valid] / areas3d[valid])
    mean = density.mean()
    if mean <= 0:
        return None
    return float(density.std() / mean)


def silhouette_iou(
    mesh: trimesh.Trimesh,
    alpha_mask: np.ndarray,
    resolution: int = 64,
) -> float | None:
    """CPU orthographic raycast IoU vs the input alpha mask (front view,
    -Y looking direction). Returns None when the ray engine is missing."""
    try:
        bounds = mesh.bounds
        span = (bounds[1] - bounds[0]).max() * 1.05
        center = bounds.mean(axis=0)
        xs = np.linspace(center[0] - span / 2, center[0] + span / 2, resolution)
        zs = np.linspace(center[2] + span / 2, center[2] - span / 2, resolution)
        gx, gz = np.meshgrid(xs, zs)
        origins = np.stack(
            [
                gx.ravel(),
                np.full(gx.size, bounds[0][1] - span),
                gz.ravel(),
            ],
            axis=1,
        )
        directions = np.tile([0.0, 1.0, 0.0], (origins.shape[0], 1))
        hits = mesh.ray.intersects_any(origins, directions).reshape(resolution, resolution)
    except BaseException:
        return None
    from PIL import Image

    ref = (
        np.array(
            Image.fromarray((alpha_mask > 0).astype(np.uint8) * 255).resize(
                (resolution, resolution), Image.NEAREST
            )
        )
        > 0
    )
    inter = np.logical_and(hits, ref).sum()
    union = np.logical_or(hits, ref).sum()
    if union == 0:
        return None
    return float(inter / union)


def mesh_stats(
    mesh: trimesh.Trimesh,
    expected_topology: str | None = None,
) -> dict[str, Any]:
    """The compact stats block of the product report."""
    if expected_topology is not None and expected_topology not in TOPOLOGY_EXPECTATIONS:
        raise ValueError(f"expected_topology must be one of {TOPOLOGY_EXPECTATIONS}")
    # count components by face-adjacency labeling (same call euler_numbers
    # uses): split() builds a full Trimesh per component, which the profiler
    # measured at 189 s of the 276 s stats stage on a 22k-component decode
    # mesh - the count is the only thing this block needs
    if len(mesh.faces):
        components = len(
            trimesh.graph.connected_components(
                mesh.face_adjacency, nodes=np.arange(len(mesh.faces))
            )
        )
    else:
        components = 1
    bbox = (mesh.bounds[1] - mesh.bounds[0]) if len(mesh.vertices) else np.zeros(3)
    stats: dict[str, Any] = {
        "tris": len(mesh.faces),
        "verts": len(mesh.vertices),
        "watertight": bool(mesh.is_watertight),
        "boundary_edges": boundary_edge_count(mesh),
        "boundary_loops": boundary_loop_count(mesh),
        "nonmanifold_edges": nonmanifold_edge_count(mesh),
        "degenerate_faces": degenerate_face_count(mesh),
        "components": int(max(components, 1)),
        "euler_per_component": euler_numbers(mesh),
        "bbox": [round(float(x), 6) for x in bbox],
    }
    uv_overlap = uv_overlap_fraction(mesh)
    if uv_overlap is not None:
        stats["uv_overlap"] = round(uv_overlap, 4)
    density_cv = texel_density_cv(mesh)
    if density_cv is not None:
        stats["texel_density_cv"] = round(density_cv, 4)
    if expected_topology is not None:
        stats["expected_topology"] = expected_topology
        if expected_topology == "closed":
            stats["topology_ok"] = bool(mesh.is_watertight)
        elif expected_topology == "open":
            stats["topology_ok"] = True
        else:
            stats["topology_ok"] = True
    return stats
