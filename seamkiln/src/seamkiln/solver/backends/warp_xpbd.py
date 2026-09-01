"""XPBD via NVIDIA Warp (Apache-2.0).

Kept because Warp is the right answer on a CUDA machine and this code is
meant to outlive this Mac. On macOS its wheels are CPU-only - "The macOS
wheels support CPU execution but not Metal acceleration" (Warp README,
2026-09-01) - so `available()` reports the device it actually got rather
than letting a reader assume "warp" means "GPU".

Not a TEE dependency: run it through `uv run --with warp-lang` so the
measurement costs nothing permanent.
"""

from __future__ import annotations

import numpy as np

from seamkiln.solver.problem import GRAVITY, ClothProblem


def available() -> tuple[bool, str]:
    try:
        import warp as wp
    except ImportError:
        return False, "warp-lang is not installed (uv run --with warp-lang)"
    try:
        wp.init()
    except Exception as exc:  # a broken toolchain must not read as "absent"
        return False, f"warp failed to initialise: {exc}"
    cuda = bool(wp.get_cuda_device_count())
    return True, f"warp {wp.config.version} {'cuda' if cuda else 'cpu'}"


def simulate(problem: ClothProblem, frames: int, *, device: str | None = None) -> np.ndarray:
    import warp as wp

    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    dev = device or ("cuda" if wp.get_cuda_device_count() else "cpu")

    @wp.kernel
    def integrate(
        x: wp.array(dtype=wp.vec3),
        v: wp.array(dtype=wp.vec3),
        prev: wp.array(dtype=wp.vec3),
        gravity: wp.vec3,
        h: float,
        retain: float,
    ):
        k = wp.tid()
        prev[k] = x[k]
        v[k] = (v[k] + gravity * h) * retain
        x[k] = x[k] + v[k] * h

    @wp.kernel
    def solve_group(
        x: wp.array(dtype=wp.vec3),
        w: wp.array(dtype=float),
        ii: wp.array(dtype=wp.int32),
        jj: wp.array(dtype=wp.int32),
        rest: wp.array(dtype=float),
        alpha: float,
    ):
        k = wp.tid()
        a = ii[k]
        b = jj[k]
        delta = x[a] - x[b]
        length = wp.length(delta)
        if length < 1.0e-12:
            return
        error = length - rest[k]
        denom = w[a] + w[b] + alpha
        scale = -error / (denom * length)
        x[a] = x[a] + delta * (w[a] * scale)
        x[b] = x[b] - delta * (w[b] * scale)

    @wp.kernel
    def collide_and_finish(
        x: wp.array(dtype=wp.vec3),
        v: wp.array(dtype=wp.vec3),
        prev: wp.array(dtype=wp.vec3),
        centre: wp.vec3,
        radius: float,
        h: float,
    ):
        k = wp.tid()
        offset = x[k] - centre
        distance = wp.length(offset)
        if distance < radius and distance > 1.0e-12:
            x[k] = centre + offset * (radius / distance)
        v[k] = (x[k] - prev[k]) / h

    n = problem.n_particles
    x = wp.array(problem.positions.astype(np.float32), dtype=wp.vec3, device=dev)
    v = wp.zeros(n, dtype=wp.vec3, device=dev)
    prev = wp.zeros(n, dtype=wp.vec3, device=dev)
    w = wp.array(problem.inv_mass.astype(np.float32), dtype=float, device=dev)
    groups = [
        (
            wp.array(g.i.astype(np.int32), dtype=wp.int32, device=dev),
            wp.array(g.j.astype(np.int32), dtype=wp.int32, device=dev),
            wp.array(g.rest.astype(np.float32), dtype=float, device=dev),
            float(g.compliance),
            len(g),
        )
        for g in problem.groups
    ]
    gravity = wp.vec3(*GRAVITY.astype(np.float32))
    centre = wp.vec3(*problem.sphere_center.astype(np.float32))
    h = problem.dt / problem.substeps
    retain = 1.0 - problem.damping

    for _ in range(frames):
        for _ in range(problem.substeps):
            wp.launch(integrate, dim=n, inputs=[x, v, prev, gravity, h, retain], device=dev)
            for ii, jj, rest, compliance, count in groups:
                wp.launch(
                    solve_group,
                    dim=count,
                    inputs=[x, w, ii, jj, rest, compliance / (h * h)],
                    device=dev,
                )
            wp.launch(
                collide_and_finish,
                dim=n,
                inputs=[x, v, prev, centre, problem.sphere_radius, h],
                device=dev,
            )
    wp.synchronize_device(dev)
    return x.numpy().astype(np.float64)
