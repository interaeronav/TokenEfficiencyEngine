"""The drape: XPBD over the garment, against the body's signed distance field.

Tier one of the two-tier plan. Small-steps XPBD, one iteration per
constraint per substep, multipliers reset each substep - the same kernel the
P0b bake-off chose, extended with the three things a garment needs that a
square of cloth does not:

  * **seam constraints**, which pull the panels together into a garment;
  * **anisotropic compliance**, so warp, weft and bias behave differently -
    without it a bias-cut skirt hangs exactly like a straight-grain one and
    the fabric card is decoration;
  * **SDF collision with friction**, so cloth rests on a body instead of
    passing through it.

Rest lengths come from the flat pattern (see garment.py). The solve pulls
the arrangement toward the garment the pattern describes; it does not
measure the garment off the arrangement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.body import BodySDF, measure_contact, measure_penetration
from seamkiln.drape.garment import GarmentMesh
from seamkiln.pattern.fabric import Fabric
from seamkiln.pattern.fabric import fabric as fabric_by_name
from seamkiln.solver import threads as _threads  # noqa: F401  - sizes the pool first
from seamkiln.solver.problem import colour_edges

GRAVITY = np.array([0.0, -9.81, 0.0], dtype=np.float64)


@dataclass(slots=True)
class DrapeSettings:
    frames: int = 120
    substeps: int = 8
    dt: float = 1.0 / 60.0
    damping: float = 0.02
    friction: float = 0.35
    thickness_mm: float = 1.0  # cloth stays this far off the body surface
    seam_compliance: float = 0.0  # a sewn seam is not stretchy
    grain_angle_deg: float = 90.0  # pattern +Y is the warp direction

    def as_dict(self) -> dict[str, Any]:
        return {
            "frames": self.frames,
            "substeps": self.substeps,
            "dt": self.dt,
            "damping": self.damping,
            "friction": self.friction,
            "thickness_mm": self.thickness_mm,
            "grain_angle_deg": self.grain_angle_deg,
        }


@dataclass(slots=True)
class DrapeResult:
    points: np.ndarray
    settings: DrapeSettings
    fabric: str
    seam_gaps: dict[str, float] = field(default_factory=dict)
    penetration: dict[str, float] = field(default_factory=dict)
    contact: dict[str, float] = field(default_factory=dict)
    seconds: float = 0.0
    fingerprint: str = ""

    def report(self) -> dict[str, Any]:
        """The compact drape report - never a vertex dump (hard rule 1)."""
        return {
            "fabric": self.fabric,
            "seconds": round(self.seconds, 3),
            "frames": self.settings.frames,
            "seam_gaps": self.seam_gaps,
            "penetration": self.penetration,
            "contact": self.contact,
            "fingerprint": self.fingerprint,
        }


def anisotropic_compliance(
    rest2d: np.ndarray, pairs: np.ndarray, cloth: Fabric, grain_angle_deg: float
) -> np.ndarray:
    """Per-edge compliance from the edge's angle to the grain.

    Warp along the grain, weft across it, and the bias between them softened
    by the shear term - which is why a 45-degree cut drapes differently from
    a straight one. Computed in PATTERN space, because the grain is a
    property of the flat cloth and survives whatever the garment does in 3D.
    """
    if pairs.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)
    delta = rest2d[pairs[:, 1]] - rest2d[pairs[:, 0]]
    angle = np.arctan2(delta[:, 1], delta[:, 0]) - np.radians(grain_angle_deg)
    warp = np.cos(angle) ** 2
    weft = np.sin(angle) ** 2
    bias = np.sin(2.0 * angle) ** 2

    base = cloth.compliances()
    return warp * base["stretch_warp"] + weft * base["stretch_weft"] + bias * base["shear"]


def _kernel():
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
        grid,
        origin,
        spacing,
        offset,
        gravity,
        h,
        retain,
        frames,
        substeps,
        friction,
    ):
        n = x.shape[0]
        nx, ny, nz = grid.shape
        for _frame in range(frames):
            for _step in range(substeps):
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
                        # RELATIVE compliance: alpha softens the correction
                        # rather than being a textbook m/N stiffness. See the
                        # note in fabric.py - with absolute compliance, a
                        # garment's inverse masses run to ~1e4 and every
                        # physically-plausible alpha rounds to zero, so every
                        # fabric behaves identically and inextensible.
                        denom = (w[a] + w[b]) * (1.0 + alpha)
                        scale = -(length - rest[e]) / (denom * length)
                        wa = w[a] * scale
                        wb = w[b] * scale
                        x[a, 0] += wa * dx
                        x[a, 1] += wa * dy
                        x[a, 2] += wa * dz
                        x[b, 0] -= wb * dx
                        x[b, 1] -= wb * dy
                        x[b, 2] -= wb * dz

                for k in prange(n):
                    # trilinear signed distance, inline: a function call per
                    # particle per substep is 300 million calls in a drape
                    fx = (x[k, 0] - origin[0]) / spacing
                    fy = (x[k, 1] - origin[1]) / spacing
                    fz = (x[k, 2] - origin[2]) / spacing
                    if fx < 0.0 or fy < 0.0 or fz < 0.0:
                        continue
                    if fx > nx - 1.001 or fy > ny - 1.001 or fz > nz - 1.001:
                        continue
                    i0 = int(fx)
                    j0 = int(fy)
                    k0 = int(fz)
                    tx = fx - i0
                    ty = fy - j0
                    tz = fz - k0
                    d = 0.0
                    for di in range(2):
                        wx = tx if di == 1 else 1.0 - tx
                        for dj in range(2):
                            wy = ty if dj == 1 else 1.0 - ty
                            for dk in range(2):
                                wz = tz if dk == 1 else 1.0 - tz
                                d += wx * wy * wz * grid[i0 + di, j0 + dj, k0 + dk]
                    if d >= offset:
                        continue
                    # outward normal by central difference on the grid
                    gx = grid[min(i0 + 1, nx - 1), j0, k0] - grid[max(i0 - 1, 0), j0, k0]
                    gy = grid[i0, min(j0 + 1, ny - 1), k0] - grid[i0, max(j0 - 1, 0), k0]
                    gz = grid[i0, j0, min(k0 + 1, nz - 1)] - grid[i0, j0, max(k0 - 1, 0)]
                    norm = np.sqrt(gx * gx + gy * gy + gz * gz)
                    if norm < 1e-12:
                        continue
                    push = offset - d
                    x[k, 0] += gx / norm * push
                    x[k, 1] += gy / norm * push
                    x[k, 2] += gz / norm * push
                    # Coulomb friction, not viscous drag. The first version
                    # removed a fixed FRACTION of the tangential motion each
                    # substep, which is drag: it slows a slide without ever
                    # stopping one, and over 2,400 substeps the surviving 65%
                    # walked the garment off the body a fraction of a
                    # millimetre at a time. Coulomb has a static regime - if
                    # the tangential motion is within mu times the normal
                    # correction it is cancelled OUTRIGHT - which is what lets
                    # a shoulder actually carry a garment's weight.
                    if friction > 0.0:
                        mx = x[k, 0] - prev[k, 0]
                        my = x[k, 1] - prev[k, 1]
                        mz = x[k, 2] - prev[k, 2]
                        dot = (mx * gx + my * gy + mz * gz) / norm
                        tx2 = mx - dot * gx / norm
                        ty2 = my - dot * gy / norm
                        tz2 = mz - dot * gz / norm
                        tangent = np.sqrt(tx2 * tx2 + ty2 * ty2 + tz2 * tz2)
                        if tangent > 1e-12:
                            limit = friction * push
                            take = 1.0 if tangent <= limit else limit / tangent
                            x[k, 0] -= take * tx2
                            x[k, 1] -= take * ty2
                            x[k, 2] -= take * tz2

                for k in prange(n):
                    for axis in range(3):
                        v[k, axis] = (x[k, axis] - prev[k, axis]) / h

    return run


def _flatten(groups: list[tuple[np.ndarray, np.ndarray, float]]):
    """Constraint groups -> flat arrays + group offsets + per-group alpha."""
    ii: list[np.ndarray] = []
    jj: list[np.ndarray] = []
    rest: list[np.ndarray] = []
    alphas: list[float] = []
    starts = [0]
    for pairs, rests, alpha in groups:
        if pairs.shape[0] == 0:
            continue
        ii.append(pairs[:, 0].astype(np.int64))
        jj.append(pairs[:, 1].astype(np.int64))
        rest.append(rests.astype(np.float64))
        alphas.append(float(alpha))
        starts.append(starts[-1] + pairs.shape[0])
    if not ii:
        raise ValueError("the garment has no constraints at all")
    return (
        np.concatenate(ii),
        np.concatenate(jj),
        np.concatenate(rest),
        np.asarray(starts, dtype=np.int64),
        np.asarray(alphas, dtype=np.float64),
    )


def _coloured_groups(
    pairs: np.ndarray, rests: np.ndarray, compliance: np.ndarray | float, n_points: int
) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """Split one constraint family into disjoint colours.

    Per-edge compliance is averaged within a colour. That is a real
    approximation and it is bounded: a colour holds edges from all over the
    mesh, so the average is over a representative mix rather than a local
    one, and the anisotropy that matters is preserved because the colours
    are not aligned with the grain.
    """
    if pairs.shape[0] == 0:
        return []
    out = []
    for colour in colour_edges(pairs, n_points):
        alpha = (
            float(np.mean(np.asarray(compliance)[colour]))
            if np.ndim(compliance)
            else float(compliance)
        )
        out.append((pairs[colour], rests[colour], alpha))
    return out


def drape(
    garment: GarmentMesh,
    sdf: BodySDF,
    *,
    fabric: str | Fabric = "cotton_jersey",
    settings: DrapeSettings | None = None,
) -> DrapeResult:
    """Run the drape. Returns positions and a compact report."""
    import time

    cloth = fabric if isinstance(fabric, Fabric) else fabric_by_name(fabric)
    opts = settings or DrapeSettings()
    n = garment.n_points

    area_m2 = float(np.abs(_triangle_areas(garment)).sum())
    mass = max(cloth.areal_density_kg_m2 * area_m2, 1e-6)
    inv_mass = np.full(n, n / mass, dtype=np.float64)

    stretch = anisotropic_compliance(
        garment.rest_points_mm, garment.structural, cloth, opts.grain_angle_deg
    )
    bend = cloth.compliances()["bending"]

    groups: list[tuple[np.ndarray, np.ndarray, float]] = []
    groups += _coloured_groups(garment.structural, garment.structural_rest, stretch, n)
    groups += _coloured_groups(garment.bending, garment.bending_rest, bend, n)
    groups += _coloured_groups(garment.seams, garment.seam_rest, opts.seam_compliance, n)

    h = opts.dt / opts.substeps
    ii, jj, rest, starts, alphas = _flatten(groups)

    x = np.ascontiguousarray(garment.points, dtype=np.float64)
    v = np.zeros_like(x)
    prev = np.zeros_like(x)

    run = _kernel()
    started = time.perf_counter()
    run(
        x,
        v,
        prev,
        inv_mass,
        ii,
        jj,
        rest,
        starts,
        alphas,
        np.ascontiguousarray(sdf.grid),
        np.ascontiguousarray(sdf.origin),
        sdf.spacing,
        opts.thickness_mm / 1000.0,
        np.ascontiguousarray(GRAVITY),
        h,
        1.0 - opts.damping,
        opts.frames,
        opts.substeps,
        opts.friction,
    )
    seconds = time.perf_counter() - started

    from hashlib import sha256

    return DrapeResult(
        points=x,
        settings=opts,
        fabric=cloth.name,
        seam_gaps=garment.seam_gaps_mm(x),
        penetration=measure_penetration(x, sdf),
        contact=measure_contact(x, sdf),
        seconds=seconds,
        fingerprint=sha256(np.round(x, 6).tobytes()).hexdigest()[:16],
    )


def _triangle_areas(garment: GarmentMesh) -> np.ndarray:
    p = garment.rest_points_mm * 1e-3
    tri = garment.triangles
    a, b, c = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
    return 0.5 * (
        (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    )
