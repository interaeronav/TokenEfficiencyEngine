"""Real parametric bodies, via Anny (Apache-2.0).

Anny is the answer to a licensing problem, not just a modelling one. SMPL and
SMPL-X - the models every paper in this field uses - are licensed for
**non-commercial research only**; commercial use is sold separately. Anny is
Apache-2.0 over CC0 MakeHuman assets, is differentiable PyTorch, and spans
infants to elders in one shape space.

**One trap, and it is inside Anny itself.** Anny declares `smplx` under an
optional `[smpl]` extra, for interoperability with SMPL-X topology. Installing
`anny[smpl]` pulls a non-commercial dependency into the tree. seamkiln
declares plain `anny`, `load_topology` refuses the smplx one by name, and
tests/test_licences.py fails the build if `smplx` ever appears in the closure.

Measured on this machine, 2026-09-01: first instantiation **13.7 s** (it parses
MakeHuman assets and caches to ~/.cache/anny), **0.2 s** warm. 13,718
vertices, 27,420 faces, watertight. Anny's world is Z-up; seamkiln's is Y-up,
and that conversion happens here so nothing downstream has to know.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import trimesh

BANNED_TOPOLOGY = {
    "smplx": (
        "Anny's smplx topology is downloadable for NON-COMMERCIAL use only, "
        "even though Anny itself is Apache-2.0. Use the default 'anny' "
        "topology, or 'soma' (Apache-2.0)."
    )
}

# Anny's phenotype space, all in [0, 1]. Named here so a caller sees the knobs
# without instantiating a model that takes 13 seconds the first time.
PHENOTYPES = ("gender", "age", "muscle", "weight", "height", "proportions")


def available() -> tuple[bool, str]:
    try:
        import anny
    except ImportError:
        return False, "anny is not installed (uv pip install 'seamkiln[body]')"
    return True, f"anny {getattr(anny, '__version__', 'unknown')}"


def load_topology(name: str = "anny") -> str:
    """Guard the one non-commercial door Anny leaves open."""
    key = str(name).strip().lower()
    if key in BANNED_TOPOLOGY:
        raise ValueError(BANNED_TOPOLOGY[key])
    if key not in ("anny", "soma"):
        raise ValueError(f"unknown Anny topology {name!r}; use 'anny' or 'soma'")
    return key


def anny_body(
    *,
    gender: float = 0.5,
    age: float = 0.5,
    muscle: float = 0.5,
    weight: float = 0.5,
    height: float = 0.5,
    proportions: float = 0.5,
    topology: str = "anny",
    dtype: str = "float32",
    stature_m: float | None = None,
) -> trimesh.Trimesh:
    """A parametric body in seamkiln's world: metres, Y up, feet at y = 0.

    All six phenotype parameters run 0..1. `stature_m` rescales the finished
    body to an exact height, because a pattern maker works from a measured
    stature and "0.5 on the height axis" is not one.
    """
    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    load_topology(topology)

    import anny as anny_module
    import torch

    torch_dtype = getattr(torch, dtype)
    model = anny_module.Anny(topology=topology).to(dtype=torch_dtype)
    # identity per bone = the model's rest pose, which is already an A-pose
    pose = torch.eye(4, dtype=torch_dtype)[None, None].repeat(1, model.bone_count, 1, 1)
    phenotypes = {
        "gender": gender,
        "age": age,
        "muscle": muscle,
        "weight": weight,
        "height": height,
        "proportions": proportions,
    }
    unknown = set(phenotypes) - set(model.phenotype_labels)
    if unknown:
        raise ValueError(
            f"this Anny build does not have phenotype(s) {sorted(unknown)}; "
            f"it has {list(model.phenotype_labels)}"
        )
    output = model(pose_parameters=pose, phenotype_kwargs=phenotypes)
    vertices = output["vertices"].squeeze(0).detach().cpu().numpy().astype(np.float64)

    mesh = trimesh.Trimesh(vertices=vertices, faces=np.asarray(model.faces), process=False)
    # Anny is Z-up; seamkiln is Y-up. Measured, not assumed: the raw extent is
    # [1.043, 0.425, 1.625] and the tallest axis is Z.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1.0, 0.0, 0.0]))
    mesh.apply_translation([0.0, -float(mesh.bounds[0][1]), 0.0])  # feet on the floor

    if stature_m is not None:
        current = float(mesh.bounds[1][1] - mesh.bounds[0][1])
        mesh.apply_scale(stature_m / max(current, 1e-6))
        mesh.apply_translation([0.0, -float(mesh.bounds[0][1]), 0.0])
    return mesh


def describe(mesh: trimesh.Trimesh) -> dict[str, Any]:
    """A compact body summary - never the 13,718 vertices."""
    low, high = mesh.bounds
    return {
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
        "watertight": bool(mesh.is_watertight),
        "stature_mm": round(float(high[1] - low[1]) * 1000.0, 1),
        "span_mm": round(float(high[0] - low[0]) * 1000.0, 1),
        "depth_mm": round(float(high[2] - low[2]) * 1000.0, 1),
    }
