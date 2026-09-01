"""The XPBD kernel and its backends (A53 P0b).

Fast by design: every case runs at a size where a backend takes
milliseconds, because the bake-off is where speed is measured and this is
where *correctness* is. Two independent implementations agreeing to float64
rounding is the strongest signal available without an analytic solution.
"""

from __future__ import annotations

import numpy as np
import pytest

from seamkiln.solver.backends import numba_xpbd, torch_xpbd
from seamkiln.solver.problem import ClothProblem, colour_edges, make_grid

SMALL = 16


def test_grid_colouring_is_disjoint_and_loses_no_constraint() -> None:
    for n in (5, 12, 33):
        problem = make_grid(n)
        for group in problem.groups:
            touched = np.concatenate([group.i, group.j])
            assert touched.size == np.unique(touched).size, f"{group.kind} repeats a particle"
        expected = 2 * n * (n - 1) + 2 * n * (n - 2) + 2 * (n - 1) * (n - 1)
        assert problem.n_constraints == expected


def test_greedy_colouring_handles_a_mesh_that_is_not_a_grid() -> None:
    # a fan: every edge touches particle 0, so every edge needs its own colour
    edges = np.array([[0, k] for k in range(1, 7)], dtype=np.int32)
    colours = colour_edges(edges, 7)
    assert len(colours) == 6
    for colour in colours:
        touched = edges[colour].ravel()
        assert touched.size == np.unique(touched).size


def _backends():
    out = []
    if numba_xpbd.available()[0]:
        out.append(("numba", lambda p, f: numba_xpbd.simulate_fused(p, f)))
    for device in ("cpu", "mps"):
        if torch_xpbd.available(device)[0]:
            out.append(
                (f"torch-{device}", lambda p, f, d=device: torch_xpbd.simulate(p, f, device=d))
            )
    return out


@pytest.mark.parametrize("name,run", _backends(), ids=lambda v: v if isinstance(v, str) else "")
def test_backend_drapes_without_entering_the_body(name, run) -> None:
    problem = make_grid(SMALL)
    positions = run(make_grid(SMALL), 40)
    assert np.isfinite(positions).all(), "the solver diverged"

    radius = np.linalg.norm(positions - problem.sphere_center, axis=1).min()
    tolerance = 1e-4 if "mps" in name else 1e-9  # float32 rounds; it does not tunnel
    assert radius >= problem.sphere_radius - tolerance, f"{name} pushed cloth inside the body"

    span = positions[:, 1].max() - positions[:, 1].min()
    assert span > 0.05, "the sheet never landed - the fixture is timing free fall"


@pytest.mark.parametrize("name,run", _backends(), ids=lambda v: v if isinstance(v, str) else "")
def test_backend_is_reproducible(name, run) -> None:
    """Law 7. A solver that cannot repeat itself cannot be benchmarked."""
    reference = make_grid(SMALL)
    hashes = {reference.fingerprint(run(make_grid(SMALL), 12)) for _ in range(2)}
    assert len(hashes) == 1, f"{name} produced two different results from one fixture"


@pytest.mark.skipif(not numba_xpbd.available()[0], reason="numba not installed")
def test_independent_implementations_agree() -> None:
    if not torch_xpbd.available("cpu")[0]:
        pytest.skip("torch not installed")
    numba_result = numba_xpbd.simulate_fused(make_grid(SMALL), 20)
    torch_result = torch_xpbd.simulate(make_grid(SMALL), 20, device="cpu")
    assert np.abs(numba_result - torch_result).max() < 1e-12


@pytest.mark.skipif(not numba_xpbd.available()[0], reason="numba not installed")
def test_fusing_the_dispatches_changes_nothing() -> None:
    """The measurement that killed the dispatch-overhead theory, kept as a test:
    if these ever diverge, the fused kernel has drifted from the naive one."""
    naive = numba_xpbd.simulate(make_grid(SMALL), 15)
    fused = numba_xpbd.simulate_fused(make_grid(SMALL), 15)
    assert np.array_equal(naive, fused)


def test_fingerprint_ignores_noise_below_a_micron() -> None:
    problem = make_grid(4)
    base = problem.positions
    nudged = base + 1e-9
    assert problem.fingerprint(base) == problem.fingerprint(nudged)
    moved = base.copy()
    moved[0, 0] += 1e-3
    assert problem.fingerprint(base) != problem.fingerprint(moved)


def test_problem_reports_its_own_shape() -> None:
    problem = make_grid(10)
    assert isinstance(problem, ClothProblem)
    assert problem.n_particles == 100
    assert problem.n_constraints == sum(len(g) for g in problem.groups)
