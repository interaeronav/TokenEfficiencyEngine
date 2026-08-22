"""Synthetic seeded-defect fixtures (research 48).

Each builder returns a trimesh.Trimesh with KNOWN metric values, so tests
assert exact counts. They double as documentation of the defect taxonomy
the repair stage exists to fix.
"""

from __future__ import annotations

import numpy as np
import trimesh


def clean_sphere(subdivisions: int = 2) -> trimesh.Trimesh:
    """Watertight genus-0 icosphere: 0 boundary edges, euler 2."""
    return trimesh.creation.icosphere(subdivisions=subdivisions)


def holed_sphere(subdivisions: int = 2) -> trimesh.Trimesh:
    """Icosphere with one face removed: exactly 1 boundary loop of 3 edges."""
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    faces = mesh.faces[1:]
    return trimesh.Trimesh(vertices=mesh.vertices, faces=faces, process=False)


def nonmanifold_fin(subdivisions: int = 1) -> trimesh.Trimesh:
    """Icosphere plus one extra triangle sharing an existing edge:
    exactly 1 non-manifold edge (shared by 3 faces)."""
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    apex = mesh.vertices.mean(axis=0) + np.array([0.0, 0.0, 2.0])
    v = np.vstack([mesh.vertices, apex])
    edge = mesh.faces[0][:2]
    fin = np.array([[edge[0], edge[1], len(v) - 1]])
    return trimesh.Trimesh(vertices=v, faces=np.vstack([mesh.faces, fin]), process=False)


def degenerate_slivers() -> trimesh.Trimesh:
    """A quad plus 2 degenerate faces: one zero-area (duplicate vertex),
    one 1e-9-offset sliver."""
    v = np.array(
        [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [2, 0, 0],
            [2, 0, 1e-9],
        ],
        dtype=float,
    )
    f = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],  # valid quad
            [1, 1, 2],  # zero-area: duplicate vertex index
            [1, 4, 5],  # sliver: height ~1e-9
        ]
    )
    return trimesh.Trimesh(vertices=v, faces=f, process=False)


def interpenetrating_boxes() -> trimesh.Trimesh:
    """Two overlapping watertight boxes concatenated: is_watertight stays
    True while the surfaces self-intersect - the trap metric (research 48)."""
    a = trimesh.creation.box(extents=(1, 1, 1))
    b = trimesh.creation.box(extents=(1, 1, 1))
    b.apply_translation([0.5, 0.0, 0.0])
    return trimesh.util.concatenate([a, b])


def small_debris(subdivisions: int = 2) -> trimesh.Trimesh:
    """Icosphere plus a tiny far-away triangle: 2 components, one of
    negligible area - the small-component cull target."""
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    base = len(mesh.vertices)
    debris_v = np.array([[10, 10, 10], [10.001, 10, 10], [10, 10.001, 10]])
    v = np.vstack([mesh.vertices, debris_v])
    f = np.vstack([mesh.faces, [[base, base + 1, base + 2]]])
    return trimesh.Trimesh(vertices=v, faces=f, process=False)
