"""XPBD on any torch device - the same kernel on MPS, CPU and CUDA.

One implementation, three backends, because the only thing that differs is
`torch.device`. On this Mac that matters: NVIDIA Warp's macOS wheels are
CPU-only (no Metal), so torch-MPS is the shortest path to the GPU that is
actually in the machine - and it is already installed as a TEE dependency.

Small-steps XPBD (Macklin 2019): many substeps, one constraint iteration
each, multipliers reset per substep. Correction is applied by direct
indexed assignment, which is exact and deterministic *because* the groups
are disjoint - no scatter-add, no atomics, no run-to-run reduction order.
"""

from __future__ import annotations

import numpy as np

from seamkiln.solver.problem import GRAVITY, ClothProblem


def available(device: str = "mps") -> tuple[bool, str]:
    try:
        import torch
    except ImportError:
        return False, "torch is not installed"
    if device == "mps":
        if not torch.backends.mps.is_available():
            return False, "torch.backends.mps.is_available() is False"
        return True, f"torch {torch.__version__} mps"
    if device == "cuda":
        if not torch.cuda.is_available():
            return False, "torch.cuda.is_available() is False"
        return True, f"torch {torch.__version__} cuda"
    return True, f"torch {torch.__version__} cpu"


def simulate(problem: ClothProblem, frames: int, *, device: str = "mps") -> np.ndarray:
    import torch

    ok, why = available(device)
    if not ok:
        raise RuntimeError(why)

    # MPS has no float64. Precision is per-backend and reported, never hidden.
    dtype = torch.float32 if device == "mps" else torch.float64
    dev = torch.device(device)

    x = torch.tensor(problem.positions, dtype=dtype, device=dev)
    v = torch.zeros_like(x)
    w = torch.tensor(problem.inv_mass, dtype=dtype, device=dev)
    gravity = torch.tensor(GRAVITY, dtype=dtype, device=dev)
    centre = torch.tensor(problem.sphere_center, dtype=dtype, device=dev)
    radius = float(problem.sphere_radius)

    groups = [
        (
            torch.tensor(g.i, dtype=torch.long, device=dev),
            torch.tensor(g.j, dtype=torch.long, device=dev),
            torch.tensor(g.rest, dtype=dtype, device=dev),
            float(g.compliance),
        )
        for g in problem.groups
    ]

    h = problem.dt / problem.substeps
    retain = 1.0 - problem.damping
    eps = torch.tensor(1e-12, dtype=dtype, device=dev)

    for _ in range(frames):
        for _ in range(problem.substeps):
            prev = x.clone()
            v = (v + gravity * h) * retain
            x = x + v * h
            for i, j, rest, compliance in groups:
                xi, xj = x[i], x[j]
                delta = xi - xj
                length = torch.linalg.vector_norm(delta, dim=1).clamp_min(eps)
                direction = delta / length.unsqueeze(1)
                error = length - rest
                alpha = compliance / (h * h)
                denom = w[i] + w[j] + alpha
                scale = (-error / denom).unsqueeze(1) * direction
                x[i] = xi + w[i].unsqueeze(1) * scale
                x[j] = xj - w[j].unsqueeze(1) * scale
            offset = x - centre
            distance = torch.linalg.vector_norm(offset, dim=1).clamp_min(eps)
            inside = distance < radius
            if bool(inside.any()):
                pushed = centre + offset / distance.unsqueeze(1) * radius
                x = torch.where(inside.unsqueeze(1), pushed, x)
            v = (x - prev) / h
    if device == "mps":
        torch.mps.synchronize()
    # off the device FIRST: MPS refuses a float64 cast, and asking for one
    # there is how a working backend reads as broken.
    return x.detach().cpu().to(torch.float64).numpy()
