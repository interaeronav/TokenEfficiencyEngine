"""The cloth problem, and the colour groups that let a backend vectorise it.

XPBD (Macklin et al.) over distance constraints. A garment is not a grid,
but a grid is the honest way to compare *backends*: identical particle
count, identical constraint count, identical arithmetic, so the number
that comes back is the backend's and not the mesh's.

The colour groups are the load-bearing idea and they survive into P2. A
Gauss-Seidel constraint pass cannot be vectorised while two constraints in
the same batch touch the same particle. Split the constraints into groups
that are internally disjoint and every group becomes one wide, ordered,
deterministic gather/scatter. A regular grid colours analytically (axis x
parity); a real garment mesh needs a greedy colouring, which `colour_edges`
provides and the grid path skips.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

GRAVITY = np.array([0.0, -9.81, 0.0], dtype=np.float64)


@dataclass
class ConstraintGroup:
    """Distance constraints with no particle repeated inside the group."""

    i: np.ndarray  # int32 [m]
    j: np.ndarray  # int32 [m]
    rest: np.ndarray  # float64 [m]
    compliance: float  # XPBD alpha; 0.0 = infinitely stiff
    kind: str  # structural | shear | bending

    def __len__(self) -> int:
        return int(self.i.shape[0])


@dataclass
class ClothProblem:
    """Everything a backend needs, and nothing about how it steps."""

    positions: np.ndarray  # float64 [n, 3]
    inv_mass: np.ndarray  # float64 [n]
    groups: list[ConstraintGroup]
    sphere_center: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 0.0]))
    sphere_radius: float = 0.35
    dt: float = 1.0 / 60.0
    substeps: int = 8
    damping: float = 0.01

    @property
    def n_particles(self) -> int:
        return int(self.positions.shape[0])

    @property
    def n_constraints(self) -> int:
        return sum(len(g) for g in self.groups)

    def fingerprint(self, positions: np.ndarray) -> str:
        """A stable hash of a result, for the determinism law.

        Rounded to 1e-6 m (a micron) before hashing: float noise below a
        micron is not a behaviour change, and an unrounded hash would make
        the determinism test a coin flip about the last mantissa bit.
        """
        from hashlib import sha256

        quantised = np.round(np.asarray(positions, dtype=np.float64), 6) + 0.0  # kill -0.0
        return sha256(quantised.tobytes()).hexdigest()[:16]


def colour_edges(edges: np.ndarray, n_particles: int) -> list[np.ndarray]:
    """Greedy edge colouring: no two edges in a colour share a particle.

    O(E) with a per-colour occupancy stamp. Used by real garment meshes in
    P2; the grid builder below colours analytically because it can.
    """
    colours: list[list[int]] = []
    stamps: list[np.ndarray] = []
    for index, (a, b) in enumerate(edges):
        placed = False
        for colour in range(len(colours)):
            stamp = stamps[colour]
            if stamp[a] == 0 and stamp[b] == 0:
                stamp[a] = stamp[b] = 1
                colours[colour].append(index)
                placed = True
                break
        if not placed:
            stamp = np.zeros(n_particles, dtype=np.int8)
            stamp[a] = stamp[b] = 1
            stamps.append(stamp)
            colours.append([index])
    return [np.asarray(c, dtype=np.int32) for c in colours]


def _axis_pairs(
    idx: np.ndarray, axis: int, step: int, offset: int
) -> tuple[np.ndarray, np.ndarray]:
    """Edges of length `step` along `axis`, taken every 2*step from `offset`.

    Stride 2*step is what makes the group disjoint: consecutive kept edges
    are (offset -> offset+step) and (offset+2*step -> offset+3*step), which
    share no endpoint. So a stride-`step` family needs exactly 2*step
    groups per axis - 2 for structural, 4 for bending. Taking only 2 for
    bending silently drops half its constraints, which is a softer cloth
    that still looks plausible: the failure mode this arithmetic exists to
    make impossible.
    """
    n = idx.shape[0]
    starts = np.arange(offset, n - step, 2 * step)
    if axis == 0:
        return idx[starts, :].ravel(), idx[starts + step, :].ravel()
    return idx[:, starts].ravel(), idx[:, starts + step].ravel()


def _grid_groups(
    n: int, spacing: float, positions: np.ndarray, *, compliances: dict[str, float]
) -> list[ConstraintGroup]:
    """Analytic colouring of a grid: axis x offset is disjoint by construction."""
    idx = np.arange(n * n, dtype=np.int32).reshape(n, n)
    groups: list[ConstraintGroup] = []

    def add(a: np.ndarray, b: np.ndarray, kind: str) -> None:
        if a.size == 0:
            return
        rest = np.linalg.norm(positions[a] - positions[b], axis=1)
        groups.append(ConstraintGroup(a, b, rest, compliances[kind], kind))

    for step, kind in ((1, "structural"), (2, "bending")):
        for axis in (0, 1):
            for offset in range(2 * step):
                add(*_axis_pairs(idx, axis, step, offset), kind)

    # shear: both diagonals, parity on the row so no particle repeats
    for dcol in (1, -1):
        cols = np.arange(0, n - 1) if dcol > 0 else np.arange(1, n)
        for parity in (0, 1):
            rows = np.arange(parity, n - 1, 2)
            a = idx[np.ix_(rows, cols)]
            b = idx[np.ix_(rows + 1, cols + dcol)]
            add(a.ravel(), b.ravel(), "shear")

    expected = 2 * n * (n - 1) + 2 * n * (n - 2) + 2 * (n - 1) * (n - 1)
    total = sum(len(g) for g in groups)
    if total != expected:  # arithmetic, not opinion
        raise AssertionError(f"grid colouring lost constraints: {total} != {expected}")
    return groups


def make_grid(
    n: int,
    *,
    size: float = 1.0,
    height: float = 0.6,
    density: float = 0.2,
    compliances: dict[str, float] | None = None,
) -> ClothProblem:
    """An n x n cloth sheet released above a sphere - the drape workload.

    Nothing is pinned: the sheet falls, lands, and settles, so collision
    and self-weight dominate exactly as they do on a garment.
    """
    compliances = compliances or {"structural": 0.0, "shear": 5e-6, "bending": 2e-5}
    spacing = size / (n - 1)
    xs = np.linspace(-size / 2, size / 2, n)
    zs = np.linspace(-size / 2, size / 2, n)
    grid_x, grid_z = np.meshgrid(xs, zs, indexing="ij")
    positions = np.stack([grid_x.ravel(), np.full(n * n, height), grid_z.ravel()], axis=1).astype(
        np.float64
    )
    area = spacing * spacing
    inv_mass = np.full(n * n, 1.0 / (density * area), dtype=np.float64)
    return ClothProblem(
        positions=positions,
        inv_mass=inv_mass,
        groups=_grid_groups(n, spacing, positions, compliances=compliances),
        sphere_center=np.array([0.0, 0.0, 0.0]),
        sphere_radius=0.35,
    )
