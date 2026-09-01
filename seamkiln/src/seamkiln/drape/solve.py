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
from seamkiln.drape.environment import Environment, WindField
from seamkiln.drape.garment import GarmentMesh
from seamkiln.pattern.fabric import Fabric
from seamkiln.pattern.fabric import fabric as fabric_by_name
from seamkiln.solver import threads as _threads  # noqa: F401  - sizes the pool first
from seamkiln.solver.problem import colour_edges, colour_simplices

# Simulation quality tiers - "adjusting material quality" as one named knob
# instead of four numbers a caller has to balance. Measured cost, not a guess:
# see the P0b bake-off and A54's own timings.
# MEASURED, and the reason this table is not cosmetic: substeps set how
# stiff cloth is ALLOWED to be, because bending converges over substeps. On
# the BS 5058 drape test, a 12 oz denim scores
#
#     substeps    8      20      34      50
#     drape DC   0.431  0.876  0.970  0.995     (published band 0.75-0.90)
#
# so a "draft" drape is not a rougher picture of the same cloth - it is
# SOFTER cloth. Anything meant to be believed runs at `standard` or better.
QUALITY: dict[str, dict[str, float]] = {
    "draft": {"substeps": 8, "frames": 120},
    "standard": {"substeps": 20, "frames": 250},
    "fine": {"substeps": 34, "frames": 400},
    "final": {"substeps": 50, "frames": 600},
}


@dataclass(slots=True)
class DrapeSettings:
    frames: int = 120
    substeps: int = 20
    dt: float = 1.0 / 60.0
    damping: float = 0.02
    friction: float = 0.35
    thickness_mm: float = 1.0  # cloth stays this far off the body surface
    seam_compliance: float = 0.0  # a sewn seam is not stretchy
    grain_angle_deg: float = 90.0  # pattern +Y is the warp direction
    environment: Environment | None = None  # None = the standard atmosphere
    fibre: str = "cotton"  # which sorption curve conditioning uses

    @classmethod
    def at_quality(cls, quality: str = "standard", **kwargs) -> DrapeSettings:
        if quality not in QUALITY:
            raise ValueError(f"no quality {quality!r}; known: {', '.join(QUALITY)}.")
        preset = {k: int(v) for k, v in QUALITY[quality].items()}
        return cls(**{**preset, **kwargs})

    @property
    def room(self) -> Environment:
        return self.environment or Environment()

    def as_dict(self) -> dict[str, Any]:
        return {
            "frames": self.frames,
            "substeps": self.substeps,
            "dt": self.dt,
            "damping": self.damping,
            "friction": self.friction,
            "thickness_mm": self.thickness_mm,
            "grain_angle_deg": self.grain_angle_deg,
            "environment": self.room.describe(),
        }


# What a drape has to achieve before its numbers may be quoted. Measured on
# the tee block against particle distance, with the topology correct:
#
#   pd mm    26     20     16     12      9
#   mean    2.23   1.60   1.52   0.99   0.74      (mm)
#   max    71.0   74.5   60.1   32.6   19.0
#
# and against substeps, on the BS 5058 drape test: a 12 oz denim scores 0.431
# at 8 substeps and 0.876 at 20, where the published band is 0.75-0.90. So a
# draft run is not a rougher picture of the same cloth, it is softer cloth -
# which is why this verdict is computed and reported rather than left to
# whoever reads the output to remember.
CONVERGED = {
    "substeps": 20,
    "mean_gap_mm": 1.5,
    "max_gap_mm": 40.0,
}


def _converged(seam_gaps: dict, penetration: dict, settings: DrapeSettings) -> dict[str, Any]:
    """Whether this result may be quoted, and if not, why not."""
    reasons: list[str] = []
    if settings.substeps < CONVERGED["substeps"]:
        reasons.append(
            f"substeps {settings.substeps} < {CONVERGED['substeps']}: bending has not "
            "converged, so the cloth is softer than its card says"
        )
    mean_gap = seam_gaps.get("mean_gap_mm")
    if mean_gap is not None and mean_gap > CONVERGED["mean_gap_mm"]:
        reasons.append(
            f"mean seam gap {mean_gap:.2f} mm > {CONVERGED['mean_gap_mm']} mm: "
            "use a finer particle distance"
        )
    max_gap = seam_gaps.get("max_gap_mm")
    if max_gap is not None and max_gap > CONVERGED["max_gap_mm"]:
        reasons.append(
            f"worst seam gap {max_gap:.0f} mm > {CONVERGED['max_gap_mm']:.0f} mm: "
            "one seam is open - check its orientation, not just the resolution"
        )
    voxel = penetration.get("voxel_mm", 0.0)
    depth = penetration.get("deepest_penetration_mm", 0.0)
    if voxel and depth > voxel:
        reasons.append(
            f"penetration {depth:.1f} mm exceeds the field's own {voxel:.0f} mm voxel: "
            "bake the body finer"
        )
    if not reasons:
        return {"converged": True}
    return {"converged": False, "not_converged": reasons}


def _room_note(environment: dict, conditioning: dict) -> dict:
    """Only what differs from a laboratory's default conditions."""
    if not environment:
        return {}
    note: dict[str, Any] = {"room": environment.get("name", "standard")}
    if not environment.get("standard_atmosphere", True):
        note["atmosphere"] = {
            "temperature_c": environment["temperature_c"],
            "humidity_pct": environment["humidity_pct"],
            "pressure_kpa": environment["pressure_kpa"],
        }
    if abs(environment.get("gravity_vs_earth", 1.0) - 1.0) > 1e-6:
        note["gravity"] = environment["gravity_vector"]
    if environment.get("wind_speed_ms", 0.0) > 0.0:
        note["wind_ms"] = environment["wind_ms"]
    if abs(conditioning.get("compliance_factor", 1.0) - 1.0) > 0.005:
        note["conditioning"] = {
            "fibre": conditioning.get("fibre"),
            "regain": conditioning.get("regain"),
            "mass_factor": conditioning.get("mass_factor"),
            "compliance_factor": conditioning.get("compliance_factor"),
        }
    return note


@dataclass(slots=True)
class DrapeResult:
    points: np.ndarray
    settings: DrapeSettings
    fabric: str
    seam_gaps: dict[str, float] = field(default_factory=dict)
    penetration: dict[str, float] = field(default_factory=dict)
    contact: dict[str, float] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    conditioning: dict[str, Any] = field(default_factory=dict)
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
            # Never rely on a coarse preview: a result that has not converged
            # says so here rather than depending on the reader to remember.
            **_converged(self.seam_gaps, self.penetration, self.settings),
            # Report the EXCEPTION, not the default. A drape in the standard
            # atmosphere at earth gravity with no wind says so in three words;
            # a drape on the moon in a gale prints the room. Spelling out an
            # unchanged room in every report cost 62 characters and pushed the
            # response past the compact-report budget - which is a test here.
            **_room_note(self.environment, self.conditioning),
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


MAX_BEND_STEP = 0.20  # radians per iteration; see the note in the kernel


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
        bq,
        bend_rest,
        bend_starts,
        bend_alphas,
        grid,
        origin,
        spacing,
        sdf_rot,
        sdf_trans,
        offset,
        tri,
        tri_start,
        tri_index,
        area_share,
        gravity,
        wind,
        air_density,
        drag_cd,
        pin_mask,
        pin_target,
        restitution,
        contact_n,
        h,
        retain,
        frames,
        substeps,
        friction,
    ):
        n = x.shape[0]
        nx, ny, nz = grid.shape
        step = 0
        for _frame in range(frames):
            for _sub in range(substeps):
                gx_w = wind[step, 0]
                gy_w = wind[step, 1]
                gz_w = wind[step, 2]
                step += 1

                for k in prange(n):
                    # --- wind, as a force on this vertex's share of surface
                    ax = gravity[0]
                    ay = gravity[1]
                    az = gravity[2]
                    if air_density > 0.0 and area_share[k] > 0.0:
                        # area-weighted vertex normal from the incident faces
                        nxs = 0.0
                        nys = 0.0
                        nzs = 0.0
                        for t in range(tri_start[k], tri_start[k + 1]):
                            f = tri_index[t]
                            a = tri[f, 0]
                            b = tri[f, 1]
                            c = tri[f, 2]
                            e1x = x[b, 0] - x[a, 0]
                            e1y = x[b, 1] - x[a, 1]
                            e1z = x[b, 2] - x[a, 2]
                            e2x = x[c, 0] - x[a, 0]
                            e2y = x[c, 1] - x[a, 1]
                            e2z = x[c, 2] - x[a, 2]
                            nxs += e1y * e2z - e1z * e2y
                            nys += e1z * e2x - e1x * e2z
                            nzs += e1x * e2y - e1y * e2x
                        length = np.sqrt(nxs * nxs + nys * nys + nzs * nzs)
                        if length > 1e-12:
                            nxs /= length
                            nys /= length
                            nzs /= length
                            rx = gx_w - v[k, 0]
                            ry = gy_w - v[k, 1]
                            rz = gz_w - v[k, 2]
                            along = rx * nxs + ry * nys + rz * nzs
                            # F = 1/2 rho Cd A |c| c n  - signed, so it pushes
                            # with the flow rather than always outward
                            press = (
                                0.5 * air_density * drag_cd * area_share[k] * np.abs(along) * along
                            )
                            ax += press * nxs * w[k]
                            ay += press * nys * w[k]
                            az += press * nzs * w[k]

                    prev[k, 0] = x[k, 0]
                    prev[k, 1] = x[k, 1]
                    prev[k, 2] = x[k, 2]
                    v[k, 0] = (v[k, 0] + ax * h) * retain
                    v[k, 1] = (v[k, 1] + ay * h) * retain
                    v[k, 2] = (v[k, 2] + az * h) * retain
                    x[k, 0] += v[k, 0] * h
                    x[k, 1] += v[k, 1] * h
                    x[k, 2] += v[k, 2] * h

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

                for g in range(bend_starts.shape[0] - 1):
                    lo = bend_starts[g]
                    balpha = bend_alphas[g]
                    for t in prange(bend_starts[g + 1] - lo):
                        e = lo + t
                        i1 = bq[e, 0]
                        i2 = bq[e, 1]
                        i3 = bq[e, 2]
                        i4 = bq[e, 3]
                        # everything relative to p1 (Mueller et al., PBD 2006)
                        p2x = x[i2, 0] - x[i1, 0]
                        p2y = x[i2, 1] - x[i1, 1]
                        p2z = x[i2, 2] - x[i1, 2]
                        p3x = x[i3, 0] - x[i1, 0]
                        p3y = x[i3, 1] - x[i1, 1]
                        p3z = x[i3, 2] - x[i1, 2]
                        p4x = x[i4, 0] - x[i1, 0]
                        p4y = x[i4, 1] - x[i1, 1]
                        p4z = x[i4, 2] - x[i1, 2]

                        n1x = p2y * p3z - p2z * p3y
                        n1y = p2z * p3x - p2x * p3z
                        n1z = p2x * p3y - p2y * p3x
                        n2x = p2y * p4z - p2z * p4y
                        n2y = p2z * p4x - p2x * p4z
                        n2z = p2x * p4y - p2y * p4x
                        l1 = np.sqrt(n1x * n1x + n1y * n1y + n1z * n1z)
                        l2 = np.sqrt(n2x * n2x + n2y * n2y + n2z * n2z)
                        if l1 < 1e-12 or l2 < 1e-12:
                            continue
                        n1x /= l1
                        n1y /= l1
                        n1z /= l1
                        n2x /= l2
                        n2y /= l2
                        n2z /= l2
                        d = n1x * n2x + n1y * n2y + n1z * n2z
                        if d > 1.0:
                            d = 1.0
                        elif d < -1.0:
                            d = -1.0
                        sin_t = np.sqrt(1.0 - d * d)
                        if sin_t < 1e-7:
                            continue  # already flat: no gradient to follow

                        q3x = (p2y * n2z - p2z * n2y + (n1y * p2z - n1z * p2y) * d) / l1
                        q3y = (p2z * n2x - p2x * n2z + (n1z * p2x - n1x * p2z) * d) / l1
                        q3z = (p2x * n2y - p2y * n2x + (n1x * p2y - n1y * p2x) * d) / l1
                        q4x = (p2y * n1z - p2z * n1y + (n2y * p2z - n2z * p2y) * d) / l2
                        q4y = (p2z * n1x - p2x * n1z + (n2z * p2x - n2x * p2z) * d) / l2
                        q4z = (p2x * n1y - p2y * n1x + (n2x * p2y - n2y * p2x) * d) / l2
                        r3x = (p3y * n2z - p3z * n2y + (n1y * p3z - n1z * p3y) * d) / l1
                        r3y = (p3z * n2x - p3x * n2z + (n1z * p3x - n1x * p3z) * d) / l1
                        r3z = (p3x * n2y - p3y * n2x + (n1x * p3y - n1y * p3x) * d) / l1
                        r4x = (p4y * n1z - p4z * n1y + (n2y * p4z - n2z * p4y) * d) / l2
                        r4y = (p4z * n1x - p4x * n1z + (n2z * p4x - n2x * p4z) * d) / l2
                        r4z = (p4x * n1y - p4y * n1x + (n2x * p4y - n2y * p4x) * d) / l2
                        q2x = -r3x - r4x
                        q2y = -r3y - r4y
                        q2z = -r3z - r4z
                        q1x = -q2x - q3x - q4x
                        q1y = -q2y - q3y - q4y
                        q1z = -q2z - q3z - q4z

                        denom = (
                            w[i1] * (q1x * q1x + q1y * q1y + q1z * q1z)
                            + w[i2] * (q2x * q2x + q2y * q2y + q2z * q2z)
                            + w[i3] * (q3x * q3x + q3y * q3y + q3z * q3z)
                            + w[i4] * (q4x * q4x + q4y * q4y + q4z * q4z)
                        )
                        if denom < 1e-12:
                            continue
                        # Clamp how far one iteration may unfold an element.
                        # A stiff dihedral at full correction overshoots, the
                        # overshoot feeds the next substep and the mesh
                        # implodes - MEASURED: outside a narrow band of
                        # stiffness every fabric collapsed to a drape
                        # coefficient of exactly 0.000, which reads as
                        # "infinitely limp" and is in fact "the solver
                        # exploded". Bounding the angular step costs
                        # convergence rate, not correctness: the rest angle is
                        # still reached, over more substeps.
                        error = np.arccos(d) - bend_rest[e]
                        if error > MAX_BEND_STEP:
                            error = MAX_BEND_STEP
                        elif error < -MAX_BEND_STEP:
                            error = -MAX_BEND_STEP
                        lam = -sin_t * error / (denom * (1.0 + balpha))
                        x[i1, 0] += lam * w[i1] * q1x
                        x[i1, 1] += lam * w[i1] * q1y
                        x[i1, 2] += lam * w[i1] * q1z
                        x[i2, 0] += lam * w[i2] * q2x
                        x[i2, 1] += lam * w[i2] * q2y
                        x[i2, 2] += lam * w[i2] * q2z
                        x[i3, 0] += lam * w[i3] * q3x
                        x[i3, 1] += lam * w[i3] * q3y
                        x[i3, 2] += lam * w[i3] * q3z
                        x[i4, 0] += lam * w[i4] * q4x
                        x[i4, 1] += lam * w[i4] * q4y
                        x[i4, 2] += lam * w[i4] * q4z

                for k in prange(n):
                    # --- collision, in the SUBJECT's frame. The field is baked
                    # once; a moved or turned subject is a 3x3 multiply here,
                    # not a 1.5 s rebake.
                    wx = x[k, 0] - sdf_trans[0]
                    wy = x[k, 1] - sdf_trans[1]
                    wz = x[k, 2] - sdf_trans[2]
                    lx = sdf_rot[0, 0] * wx + sdf_rot[1, 0] * wy + sdf_rot[2, 0] * wz
                    ly = sdf_rot[0, 1] * wx + sdf_rot[1, 1] * wy + sdf_rot[2, 1] * wz
                    lz = sdf_rot[0, 2] * wx + sdf_rot[1, 2] * wy + sdf_rot[2, 2] * wz
                    fx = (lx - origin[0]) / spacing
                    fy = (ly - origin[1]) / spacing
                    fz = (lz - origin[2]) / spacing
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
                        wxx = tx if di == 1 else 1.0 - tx
                        for dj in range(2):
                            wyy = ty if dj == 1 else 1.0 - ty
                            for dk in range(2):
                                wzz = tz if dk == 1 else 1.0 - tz
                                d += wxx * wyy * wzz * grid[i0 + di, j0 + dj, k0 + dk]
                    if d >= offset:
                        continue
                    gx = grid[min(i0 + 1, nx - 1), j0, k0] - grid[max(i0 - 1, 0), j0, k0]
                    gy = grid[i0, min(j0 + 1, ny - 1), k0] - grid[i0, max(j0 - 1, 0), k0]
                    gz = grid[i0, j0, min(k0 + 1, nz - 1)] - grid[i0, j0, max(k0 - 1, 0)]
                    norm = np.sqrt(gx * gx + gy * gy + gz * gz)
                    if norm < 1e-12:
                        continue
                    # the normal is in the field's frame; rotate it back out
                    lnx = gx / norm
                    lny = gy / norm
                    lnz = gz / norm
                    wnx = sdf_rot[0, 0] * lnx + sdf_rot[0, 1] * lny + sdf_rot[0, 2] * lnz
                    wny = sdf_rot[1, 0] * lnx + sdf_rot[1, 1] * lny + sdf_rot[1, 2] * lnz
                    wnz = sdf_rot[2, 0] * lnx + sdf_rot[2, 1] * lny + sdf_rot[2, 2] * lnz
                    push = offset - d
                    x[k, 0] += wnx * push
                    x[k, 1] += wny * push
                    x[k, 2] += wnz * push
                    # Restitution is applied to the VELOCITY, in the pass
                    # below - not here as an extra position push. Pushing the
                    # particle out a second time double-counts the separation:
                    # at a restitution of 0.02, which is barely a bounce, it
                    # took the tee's worst seam gap from 33 mm to 248 mm.
                    contact_n[k, 0] = wnx
                    contact_n[k, 1] = wny
                    contact_n[k, 2] = wnz
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
                        dot = mx * wnx + my * wny + mz * wnz
                        tx2 = mx - dot * wnx
                        ty2 = my - dot * wny
                        tz2 = mz - dot * wnz
                        tangent = np.sqrt(tx2 * tx2 + ty2 * ty2 + tz2 * tz2)
                        if tangent > 1e-12:
                            limit = friction * push
                            take = 1.0 if tangent <= limit else limit / tangent
                            x[k, 0] -= take * tx2
                            x[k, 1] -= take * ty2
                            x[k, 2] -= take * tz2

                for k in prange(n):
                    # restitution, on the velocity, where it belongs
                    if restitution > 0.0 and (
                        contact_n[k, 0] != 0.0 or contact_n[k, 1] != 0.0 or contact_n[k, 2] != 0.0
                    ):
                        approach = (
                            v[k, 0] * contact_n[k, 0]
                            + v[k, 1] * contact_n[k, 1]
                            + v[k, 2] * contact_n[k, 2]
                        )
                        if approach < 0.0:
                            give = -(1.0 + restitution) * approach
                            v[k, 0] += contact_n[k, 0] * give
                            v[k, 1] += contact_n[k, 1] * give
                            v[k, 2] += contact_n[k, 2] * give
                        contact_n[k, 0] = 0.0
                        contact_n[k, 1] = 0.0
                        contact_n[k, 2] = 0.0

                    # pins last, so nothing the substep did can drag a pinned
                    # particle off its target - that is what a pin means
                    if pin_mask[k] > 0.0:
                        x[k, 0] = pin_target[k, 0]
                        x[k, 1] = pin_target[k, 1]
                        x[k, 2] = pin_target[k, 2]
                    v[k, 0] = (x[k, 0] - prev[k, 0]) / h
                    v[k, 1] = (x[k, 1] - prev[k, 1]) / h
                    v[k, 2] = (x[k, 2] - prev[k, 2]) / h

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


def _flatten_quads(quads: np.ndarray, rest: np.ndarray, compliance: float, n_points: int):
    """Dihedral constraints, coloured and flattened for the kernel."""
    if quads.shape[0] == 0:
        empty = np.zeros((0, 4), dtype=np.int64)
        return empty, np.zeros(0), np.zeros(1, dtype=np.int64), np.zeros(0)
    order: list[np.ndarray] = []
    starts = [0]
    alphas: list[float] = []
    for colour in colour_simplices(quads, n_points):
        order.append(colour)
        starts.append(starts[-1] + colour.shape[0])
        alphas.append(float(compliance))
    index = np.concatenate(order)
    return (
        np.ascontiguousarray(quads[index], dtype=np.int64),
        np.ascontiguousarray(rest[index], dtype=np.float64),
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


def vertex_areas(rest_points_mm: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Each vertex's share of surface, in m^2 - a third of its faces.

    Measured on the FLAT pattern, so it is the area of cloth that vertex
    represents, which is what its weight and its wind loading both depend on.
    """
    p = np.asarray(rest_points_mm, dtype=np.float64) * 1e-3
    a, b, c = p[triangles[:, 0]], p[triangles[:, 1]], p[triangles[:, 2]]
    face = 0.5 * np.abs(
        (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    )
    share = np.zeros(p.shape[0], dtype=np.float64)
    for column in range(3):
        np.add.at(share, triangles[:, column], face / 3.0)
    return share


def vertex_triangle_csr(n_points: int, triangles: np.ndarray):
    """Vertex -> incident faces, as CSR. Conflict-free, so the wind pass can
    run wide: every vertex reads its own faces and writes only itself."""
    counts = np.zeros(n_points + 1, dtype=np.int64)
    for column in range(3):
        np.add.at(counts, triangles[:, column] + 1, 1)
    starts = np.cumsum(counts)
    index = np.zeros(int(starts[-1]), dtype=np.int64)
    cursor = starts[:-1].copy()
    for face, tri in enumerate(triangles):
        for vertex in tri:
            index[cursor[vertex]] = face
            cursor[vertex] += 1
    return starts, index


def drape(
    garment: GarmentMesh,
    sdf: BodySDF,
    *,
    fabric: str | Fabric = "cotton_jersey",
    settings: DrapeSettings | None = None,
    pins: np.ndarray | None = None,
    pin_target: np.ndarray | None = None,
) -> DrapeResult:
    """Run the drape. Returns positions and a compact report.

    `pins` is a mask over particles: a pinned particle is held at its target
    and nothing in a substep can move it. With `pin_target` it is pulled
    somewhere instead of held - which is what a pinch, a lacing anchor and a
    hand on a hem all reduce to.
    """
    import time

    cloth = fabric if isinstance(fabric, Fabric) else fabric_by_name(fabric)
    opts = settings or DrapeSettings()
    room = opts.room
    conditioning = room.conditioning(opts.fibre)
    n = garment.n_points

    # --- weight, per particle, from the fabric's own g/m^2.
    # The first version gave every particle the SAME inverse mass, computed
    # from the garment's total mass over its vertex count. That is only right
    # on a uniform mesh: where the mesh is fine, particles were too heavy;
    # where it is coarse, too light. Now a particle weighs what its share of
    # cloth weighs - which is also what makes GSM a real input rather than a
    # label on a card.
    share = vertex_areas(garment.rest_points_mm, garment.triangles)
    mass = np.maximum(share * cloth.areal_density_kg_m2 * conditioning["mass_factor"], 1e-9)
    inv_mass = 1.0 / mass

    stretch = anisotropic_compliance(
        garment.rest_points_mm, garment.structural, cloth, opts.grain_angle_deg
    )
    softening = float(conditioning["compliance_factor"])
    bend = cloth.compliances()["bending"] * softening
    stretch = stretch * softening

    groups: list[tuple[np.ndarray, np.ndarray, float]] = []
    groups += _coloured_groups(garment.structural, garment.structural_rest, stretch, n)
    groups += _coloured_groups(garment.seams, garment.seam_rest, opts.seam_compliance, n)
    if garment.extra is not None and garment.extra.shape[0]:
        # lacing and anything else added after the pattern was built. A lace
        # is barely stretchy, so it joins on the seam's compliance.
        groups += _coloured_groups(garment.extra, garment.extra_rest, opts.seam_compliance, n)

    h = opts.dt / opts.substeps
    ii, jj, rest, starts, alphas = _flatten(groups)
    bq, bend_rest, bend_starts, bend_alphas = _flatten_quads(
        garment.bending, garment.bending_rest, bend, n
    )

    x = np.ascontiguousarray(garment.points, dtype=np.float64)
    v = np.zeros_like(x)
    prev = np.zeros_like(x)

    tri = np.ascontiguousarray(garment.triangles, dtype=np.int64)
    tri_start, tri_index = vertex_triangle_csr(n, tri)
    wind_schedule = WindField.of(room).samples(opts.frames * opts.substeps + 1)
    air_density = room.air_density() if float(np.linalg.norm(room.wind)) > 0.0 else 0.0

    pin_mask = (
        np.ascontiguousarray(pins, dtype=np.float64)
        if pins is not None
        else np.zeros(n, dtype=np.float64)
    )
    # Where the pins hold. Default: where the particle already is (a hold).
    # Give it somewhere else and the pin PULLS - which is what a pinch, a
    # lacing anchor and a hand on a hem all are.
    targets = np.ascontiguousarray(
        x.copy() if pin_target is None else np.asarray(pin_target, dtype=np.float64)
    )

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
        bq,
        bend_rest,
        bend_starts,
        bend_alphas,
        np.ascontiguousarray(sdf.grid),
        np.ascontiguousarray(sdf.origin),
        sdf.spacing,
        np.ascontiguousarray(sdf.rotation),
        np.ascontiguousarray(sdf.translation),
        opts.thickness_mm / 1000.0,
        tri,
        tri_start,
        tri_index,
        np.ascontiguousarray(share),
        np.ascontiguousarray(room.gravity_vector()),
        np.ascontiguousarray(wind_schedule),
        air_density,
        opts.drag if hasattr(opts, "drag") else room.drag_coefficient,
        pin_mask,
        targets,
        float(getattr(cloth, "restitution", 0.0)),
        np.zeros_like(x),
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
        environment=room.describe(),
        conditioning=conditioning,
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
