"""XPBD on the CPU via numba - 18 cores on this machine, float64 throughout.

The disjoint colour groups pay off twice: they make the torch path exact,
and they make this path safely `prange`-parallel with no atomics, because
no two iterations of the inner loop touch the same particle.
"""

from __future__ import annotations

import os
import sys

import numpy as np

from seamkiln.solver.problem import GRAVITY, ClothProblem

# Measured on this machine (Apple M5 Max, 18 cores, 2026-09-01), sweeping
# thread count against particle count. The result inverts the obvious
# default: MORE THREADS IS SLOWER at every garment size. Eighteen cores
# never win; four is the optimum from ~50k particles up, and at 5k a single
# thread beats eighteen by 8.7x.
#
#   threads |   5k    10k    30k    60k   120k   240k   500k   (ms/frame)
#         1 |  2.3    3.2    6.3   10.4   18.0   33.3   67.1
#         2 |  2.5    3.0    4.9    7.0   10.9   19.3   39.0
#         4 |  4.2    4.4    5.3    6.6    9.1   13.7   24.6
#         8 |  9.0      -      -      -   13.4      -   29.1
#        18 | 20.1      -      -      -   22.3   32.6      -
#
# The cost is the fork/join barrier around each parallel region: a frame has
# 8 substeps x (1 integrate + 16 groups + 1 collide) = 144 of them, and the
# barrier scales with POOL size while the work per region does not. Two
# things had to be measured to know that, and both are load-bearing:
#
#   1. Fusing the Python-side dispatches into one njit call per frame
#      changed NOTHING - bit-identical positions, same wall clock. So the
#      overhead is inside numba's parallel runtime, not the call.
#   2. `numba.set_num_threads(1)` on a pool of 18 costs 11.6 ms where
#      `NUMBA_NUM_THREADS=1` at process start costs 2.3 - a 5x gap at the
#      same nominal thread count. set_num_threads MASKS threads; it does not
#      shrink the barrier. The pool size is fixed when numba is imported.
#
# Hence an environment variable, set before numba is first imported, and a
# single value rather than a per-problem one: 4 is within 2 ms of the
# best-possible at every size above 10k and beats every other backend here.
DEFAULT_THREADS = "4"

if "numba" not in sys.modules:
    os.environ.setdefault("NUMBA_NUM_THREADS", DEFAULT_THREADS)
    _POOL_NOTE = ""
else:  # someone imported numba first; the pool is already sized and we say so
    _POOL_NOTE = (
        " (numba was imported before seamkiln, so NUMBA_NUM_THREADS could not "
        "be set - expect the barrier cost documented in numba_xpbd.py)"
    )


def available() -> tuple[bool, str]:
    try:
        import numba
    except ImportError:
        return False, "numba is not installed"
    return True, f"numba {numba.__version__} cpu x{numba.config.NUMBA_NUM_THREADS}thr{_POOL_NOTE}"


def _kernels():
    import numba
    from numba import njit, prange

    @njit(cache=True, parallel=True, fastmath=False)
    def solve_group(x, w, ii, jj, rest, alpha):
        for k in prange(ii.shape[0]):
            a = ii[k]
            b = jj[k]
            dx = x[a, 0] - x[b, 0]
            dy = x[a, 1] - x[b, 1]
            dz = x[a, 2] - x[b, 2]
            length = np.sqrt(dx * dx + dy * dy + dz * dz)
            if length < 1e-12:
                continue
            error = length - rest[k]
            denom = w[a] + w[b] + alpha
            scale = -error / (denom * length)
            wa = w[a] * scale
            wb = w[b] * scale
            x[a, 0] += wa * dx
            x[a, 1] += wa * dy
            x[a, 2] += wa * dz
            x[b, 0] -= wb * dx
            x[b, 1] -= wb * dy
            x[b, 2] -= wb * dz

    @njit(cache=True, parallel=True, fastmath=False)
    def integrate(x, v, prev, gravity, h, retain):
        for k in prange(x.shape[0]):
            for axis in range(3):
                prev[k, axis] = x[k, axis]
                v[k, axis] = (v[k, axis] + gravity[axis] * h) * retain
                x[k, axis] += v[k, axis] * h

    @njit(cache=True, parallel=True, fastmath=False)
    def collide_and_finish(x, v, prev, centre, radius, h):
        for k in prange(x.shape[0]):
            dx = x[k, 0] - centre[0]
            dy = x[k, 1] - centre[1]
            dz = x[k, 2] - centre[2]
            distance = np.sqrt(dx * dx + dy * dy + dz * dz)
            if distance < radius and distance > 1e-12:
                factor = radius / distance
                x[k, 0] = centre[0] + dx * factor
                x[k, 1] = centre[1] + dy * factor
                x[k, 2] = centre[2] + dz * factor
            for axis in range(3):
                v[k, axis] = (x[k, axis] - prev[k, axis]) / h

    return numba, solve_group, integrate, collide_and_finish


def _fused_kernel():
    """Whole frames inside ONE njit call.

    The naive shape - one dispatch per group per substep - is 8 substeps x
    (1 integrate + 16 groups + 1 collide) = 144 dispatches per frame, and at
    garment sizes that overhead IS the measurement: 5k and 120k particles
    both cost ~20 ms, which is not a physics result, it is a dispatch count.
    Flattening the groups into one ragged array and moving the substep loop
    inside costs 1 dispatch per frame instead.
    """
    from numba import njit, prange

    @njit(cache=True, parallel=True, fastmath=False)
    def run(
        x,
        v,
        prev,
        w,
        ii,
        jj,
        rest,
        starts,
        alphas,
        gravity,
        centre,
        radius,
        h,
        retain,
        frames,
        substeps,
    ):
        n = x.shape[0]
        for _f in range(frames):
            for _s in range(substeps):
                for k in prange(n):
                    for axis in range(3):
                        prev[k, axis] = x[k, axis]
                        v[k, axis] = (v[k, axis] + gravity[axis] * h) * retain
                        x[k, axis] += v[k, axis] * h
                for g in range(starts.shape[0] - 1):
                    lo = starts[g]
                    alpha = alphas[g]
                    for t in prange(starts[g + 1] - lo):
                        e = lo + t
                        a = ii[e]
                        b = jj[e]
                        dx = x[a, 0] - x[b, 0]
                        dy = x[a, 1] - x[b, 1]
                        dz = x[a, 2] - x[b, 2]
                        length = np.sqrt(dx * dx + dy * dy + dz * dz)
                        if length < 1e-12:
                            continue
                        scale = -(length - rest[e]) / ((w[a] + w[b] + alpha) * length)
                        wa = w[a] * scale
                        wb = w[b] * scale
                        x[a, 0] += wa * dx
                        x[a, 1] += wa * dy
                        x[a, 2] += wa * dz
                        x[b, 0] -= wb * dx
                        x[b, 1] -= wb * dy
                        x[b, 2] -= wb * dz
                for k in prange(n):
                    dx = x[k, 0] - centre[0]
                    dy = x[k, 1] - centre[1]
                    dz = x[k, 2] - centre[2]
                    distance = np.sqrt(dx * dx + dy * dy + dz * dz)
                    if distance < radius and distance > 1e-12:
                        factor = radius / distance
                        x[k, 0] = centre[0] + dx * factor
                        x[k, 1] = centre[1] + dy * factor
                        x[k, 2] = centre[2] + dz * factor
                    for axis in range(3):
                        v[k, axis] = (x[k, axis] - prev[k, axis]) / h

    return run


def simulate_fused(problem: ClothProblem, frames: int, *, threads: int | None = None) -> np.ndarray:
    """One njit dispatch per frame. Same arithmetic, same order, same result."""
    import numba

    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    if threads:  # explicit override; note it can only mask, never resize
        numba.set_num_threads(min(threads, numba.config.NUMBA_NUM_THREADS))
    run = _fused_kernel()

    x = np.ascontiguousarray(problem.positions, dtype=np.float64)
    v = np.zeros_like(x)
    prev = np.zeros_like(x)
    w = np.ascontiguousarray(problem.inv_mass, dtype=np.float64)
    ii = np.concatenate([g.i for g in problem.groups]).astype(np.int64)
    jj = np.concatenate([g.j for g in problem.groups]).astype(np.int64)
    rest = np.concatenate([g.rest for g in problem.groups]).astype(np.float64)
    starts = np.zeros(len(problem.groups) + 1, dtype=np.int64)
    starts[1:] = np.cumsum([len(g) for g in problem.groups])
    h = problem.dt / problem.substeps
    alphas = np.array([g.compliance / (h * h) for g in problem.groups], dtype=np.float64)

    run(
        x,
        v,
        prev,
        w,
        ii,
        jj,
        rest,
        starts,
        alphas,
        np.ascontiguousarray(GRAVITY, dtype=np.float64),
        np.ascontiguousarray(problem.sphere_center, dtype=np.float64),
        problem.sphere_radius,
        h,
        1.0 - problem.damping,
        frames,
        problem.substeps,
    )
    return x


def simulate(problem: ClothProblem, frames: int) -> np.ndarray:
    ok, why = available()
    if not ok:
        raise RuntimeError(why)
    _, solve_group, integrate, collide_and_finish = _kernels()

    x = np.ascontiguousarray(problem.positions, dtype=np.float64)
    v = np.zeros_like(x)
    prev = np.zeros_like(x)
    w = np.ascontiguousarray(problem.inv_mass, dtype=np.float64)
    centre = np.ascontiguousarray(problem.sphere_center, dtype=np.float64)
    gravity = np.ascontiguousarray(GRAVITY, dtype=np.float64)
    groups = [
        (
            np.ascontiguousarray(g.i, dtype=np.int64),
            np.ascontiguousarray(g.j, dtype=np.int64),
            np.ascontiguousarray(g.rest, dtype=np.float64),
            float(g.compliance),
        )
        for g in problem.groups
    ]

    h = problem.dt / problem.substeps
    retain = 1.0 - problem.damping
    for _ in range(frames):
        for _ in range(problem.substeps):
            integrate(x, v, prev, gravity, h, retain)
            for ii, jj, rest, compliance in groups:
                solve_group(x, w, ii, jj, rest, compliance / (h * h))
            collide_and_finish(x, v, prev, centre, problem.sphere_radius, h)
    return x
