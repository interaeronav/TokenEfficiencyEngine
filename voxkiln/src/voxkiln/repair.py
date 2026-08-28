"""Mesh repair (research 44/46): three escalating levels, MIT/BSD/Apache
deps only, every action recorded so the report can say exactly what was
touched.

- fast:     dedup / degenerate cull / small-component cull / winding fix /
            boundary-loop hole fill (the in-house replacement for
            crash-prone cumesh, upstream's 3e-2 perimeter default).
- manifold: fast + manifold3d validation/merge attempt (optional dep).
- rebuild:  voxelize + marching cubes (optional scikit-image) - the
            UV-destroying big hammer, only ever used pre-UV.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import numpy as np
import trimesh

LEVELS = ("fast", "manifold", "rebuild")

# Upstream fills only boundary loops whose perimeter is under 3% of the
# unit-normalized scene (o_voxel/postprocess.py:110); same default here,
# scaled by the mesh's own bbox diagonal.
DEFAULT_MAX_HOLE_PERIMETER = 3e-2
_COMPONENT_AREA_FRACTION = 1e-5


def _boundary_loops(mesh: trimesh.Trimesh) -> list[list[int]]:
    """Ordered vertex loops of boundary edges (edges on exactly one face)."""
    counts = Counter(map(tuple, mesh.edges_sorted))
    boundary = [e for e, n in counts.items() if n == 1]
    if not boundary:
        return []
    adjacency: dict[int, list[int]] = defaultdict(list)
    for a, b in boundary:
        adjacency[a].append(b)
        adjacency[b].append(a)
    unused = {tuple(sorted(e)) for e in boundary}
    loops = []
    while unused:
        start_edge = next(iter(unused))
        unused.discard(start_edge)
        loop = [start_edge[0], start_edge[1]]
        while True:
            cur = loop[-1]
            nxt = None
            for cand in adjacency[cur]:
                key = tuple(sorted((cur, cand)))
                if key in unused:
                    nxt = cand
                    unused.discard(key)
                    break
            if nxt is None:
                break
            if nxt == loop[0]:
                loops.append(loop)
                break
            loop.append(nxt)
        else:  # pragma: no cover
            continue
        if loop[-1] != loop[0] and loop not in loops:
            # open chain (non-manifold boundary weirdness): skip, unfillable
            continue
    return loops


def _directed_edges(mesh: trimesh.Trimesh) -> set[tuple[int, int]]:
    """Every directed edge a->b as traversed by its owning face. Built once
    per fill pass: rebuilding it per loop made repair quadratic in mesh size
    (hours on a raw decode mesh, whose hole fill is deferred to this stage)."""
    edges = mesh.faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    return set(map(tuple, edges.tolist()))


def _winding_for_fill(edge_dirs: set[tuple[int, int]], loop: list[int]) -> list[int]:
    """Orient the loop so fan triangles face outward: a boundary edge (a,b)
    appearing as a->b in its owning face must appear as b->a in the fill."""
    a, b = int(loop[0]), int(loop[1])
    if (a, b) in edge_dirs:
        return list(reversed(loop))
    return loop


def fill_boundary_loops(
    mesh: trimesh.Trimesh,
    max_hole_perimeter: float = DEFAULT_MAX_HOLE_PERIMETER,
) -> tuple[trimesh.Trimesh, int]:
    """Centroid-fan fill of small boundary loops. Returns (mesh, filled)."""
    loops = _boundary_loops(mesh)
    if not loops:
        return mesh, 0
    scale = float(np.linalg.norm(mesh.bounds[1] - mesh.bounds[0])) or 1.0
    edge_dirs = _directed_edges(mesh)
    vertices = mesh.vertices.copy()
    new_faces = []
    filled = 0
    for loop in loops:
        pts = mesh.vertices[loop]
        perimeter = float(np.linalg.norm(np.diff(np.vstack([pts, pts[:1]]), axis=0), axis=1).sum())
        if perimeter > max_hole_perimeter * scale:
            continue
        loop = _winding_for_fill(edge_dirs, loop)
        if len(loop) == 3:
            new_faces.append([loop[0], loop[1], loop[2]])
        else:
            centroid_idx = len(vertices)
            vertices = np.vstack([vertices, mesh.vertices[loop].mean(axis=0)])
            for i in range(len(loop)):
                new_faces.append([loop[i], loop[(i + 1) % len(loop)], centroid_idx])
        filled += 1
    if not filled:
        return mesh, 0
    faces = np.vstack([mesh.faces, np.array(new_faces)])
    out = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    return out, filled


def _cull_small_components(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, int]:
    """Drop components holding a negligible share of the surface area.

    Face-graph labels + one face mask (the cb7e377 mesh_stats idiom): the
    previous split()/concatenate built one Trimesh per component - ~30K of
    them on decode-class meshes, 303 s of a 327 s repair, almost all of it
    trimesh cache-hashing. Definition note (the SI-2 boundary-loop
    precedent): component area is now the sum of that component's OWN face
    areas on the actual mesh; split()'s reprocessed parts carried ~0.4%
    duplicated faces, so a handful of borderline-tiny components that the
    inflated measure kept now correctly fall under the negligible-share
    threshold. Vertex order also differs from the old concatenate path;
    downstream stages are order-agnostic."""
    if len(mesh.faces) == 0:
        return mesh, 0
    components = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces))
    )
    if len(components) <= 1:
        return mesh, 0
    face_areas = mesh.area_faces
    areas = np.array([face_areas[comp].sum() for comp in components])
    keep = areas > _COMPONENT_AREA_FRACTION * float(areas.sum())
    dropped = int(len(components) - keep.sum())
    if dropped == 0 or not keep.any():
        return mesh, 0
    mask = np.zeros(len(mesh.faces), dtype=bool)
    for component, keep_it in zip(components, keep, strict=True):
        if keep_it:
            mask[component] = True
    out = mesh.copy()
    out.update_faces(mask)
    out.remove_unreferenced_vertices()
    return out, dropped


def repair(
    mesh: trimesh.Trimesh,
    level: str = "fast",
    max_hole_perimeter: float = DEFAULT_MAX_HOLE_PERIMETER,
    rebuild_resolution: int = 256,
) -> tuple[trimesh.Trimesh, list[dict[str, Any]]]:
    """Repair a mesh; returns (repaired_mesh, action log).

    Each log entry: {"op": ..., "count"/"detail": ...} - only ops that
    actually changed something are recorded (diffs over snapshots).
    """
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
    log: list[dict[str, Any]] = []
    m = mesh.copy()

    # dedup + degenerate cull
    before_v = len(m.vertices)
    m.merge_vertices()
    if len(m.vertices) != before_v:
        log.append({"op": "merge_vertices", "removed": before_v - len(m.vertices)})
    ok = trimesh.triangles.nondegenerate(m.triangles, height=1e-8)
    if (~ok).sum():
        log.append({"op": "drop_degenerate_faces", "removed": int((~ok).sum())})
        m.update_faces(ok)
    before_f = len(m.faces)
    m.update_faces(m.unique_faces())
    if len(m.faces) != before_f:
        log.append({"op": "drop_duplicate_faces", "removed": before_f - len(m.faces)})
    m.remove_unreferenced_vertices()

    # small components
    m, dropped = _cull_small_components(m)
    if dropped:
        log.append({"op": "drop_small_components", "removed": dropped})

    # winding / normals
    flipped_before = m.is_winding_consistent
    trimesh.repair.fix_normals(m)
    if not flipped_before:
        log.append({"op": "fix_winding"})

    # boundary-loop hole fill
    m, filled = fill_boundary_loops(m, max_hole_perimeter=max_hole_perimeter)
    if filled:
        log.append({"op": "fill_holes", "loops_filled": filled})

    if level in ("manifold", "rebuild"):
        try:
            import manifold3d

            mm = manifold3d.Mesh(
                vert_properties=np.asarray(m.vertices, dtype=np.float32),
                tri_verts=np.asarray(m.faces, dtype=np.uint32),
            )
            man = manifold3d.Manifold(mm)
            status = man.status()
            log.append({"op": "manifold_check", "status": str(status).split(".")[-1]})
        except ImportError:
            log.append({"op": "manifold_check", "status": "skipped: manifold3d not installed"})
        except BaseException as exc:  # manifold3d raises plain exceptions on bad input
            log.append({"op": "manifold_check", "status": f"failed: {exc}"})

    if level == "rebuild":
        try:
            pitch = float((m.bounds[1] - m.bounds[0]).max()) / rebuild_resolution
            vox = m.voxelized(pitch).fill()
            rebuilt = vox.marching_cubes
            rebuilt.apply_translation(m.bounds[0] - rebuilt.bounds[0])
            log.append(
                {
                    "op": "voxel_rebuild",
                    "resolution": rebuild_resolution,
                    "note": "topology replaced; UVs destroyed (pre-UV only)",
                }
            )
            m = rebuilt
        except ImportError as exc:
            log.append(
                {"op": "voxel_rebuild", "status": f"unavailable: {exc}; install voxkiln[rebuild]"}
            )

    return m, log
