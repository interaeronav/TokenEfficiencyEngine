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

import json
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from seamkiln.drape.body import BodyMotion, BodySDF, measure_contact, measure_penetration
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


def friction_for(opts: Any, cloth: Any) -> float:
    """The friction a drape runs with: the settings' if given, else the card's."""
    if getattr(opts, "friction", None) is not None:
        return float(opts.friction)
    return float(getattr(cloth, "friction", 0.35))


@dataclass(slots=True)
class DrapeSettings:
    frames: int = 120
    substeps: int = 20
    dt: float = 1.0 / 60.0
    damping: float = 0.02
    # None means THE FABRIC CARD'S friction. The solver used to take 0.35 from
    # here for every cloth while the card's `friction` - validated, derived,
    # printed on the tech pack - was never read: a shearling at 0.53 slid
    # like a suiting, and a fur sleeve slid off an arm because of it.
    friction: float | None = None
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
            "friction": self.friction if self.friction is not None else "fabric card",
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
    # Carried out so an interactive step can carry it back IN. Without it a
    # drag restarts the cloth from rest on every step, which does not look
    # like heavy fabric - it looks like the integrator forgetting.
    velocity: np.ndarray | None = None
    # What dressing did to get here (pins, standoff, targets moved out of the
    # body); empty for a plain drape. See drape/dressing.py.
    dressing: dict[str, Any] = field(default_factory=dict)
    # How the body moved during this call (travel, blend); empty when it did
    # not, so a static report is unchanged to the byte.
    body_motion: dict[str, Any] = field(default_factory=dict)

    def report(self) -> dict[str, Any]:
        """The compact drape report - never a vertex dump (hard rule 1)."""
        return {
            "fabric": self.fabric,
            "seconds": round(self.seconds, 3),
            "frames": self.settings.frames,
            "seam_gaps": self.seam_gaps,
            "penetration": self.penetration,
            "contact": self.contact,
            **({"body_motion": self.body_motion} if self.body_motion else {}),
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


# The blended field's distance and normalised gradient at a field-frame
# point, for the moving path's second evaluations (see the kernel). It is
# compiled ONCE per process and referenced by the kernel as a module global:
# a helper created inside `_kernel()` was a closure variable of `run`, and a
# kernel that captures a closure cannot use numba's on-disk cache - every
# `drape()` recompiled it, 6.5 s a call, which turned a 23 ms interactive
# step into 6,557 ms and a 15-minute suite into 51.
field_at = None
_RUN = None


def _field_at_impl(grid, grid1, blend, mix, origin, spacing, px, py, pz):
    """The blended field's distance and normalised gradient at a
    field-frame point. Returns (d, nx, ny, nz, ok); ok is 0 off the
    lattice or on a flat spot. Only the moving path calls this - the
    static path keeps its inline evaluation, untouched."""
    nx, ny, nz = grid.shape
    fx = (px - origin[0]) / spacing
    fy = (py - origin[1]) / spacing
    fz = (pz - origin[2]) / spacing
    if fx < 0.0 or fy < 0.0 or fz < 0.0:
        return 0.0, 0.0, 0.0, 0.0, 0
    if fx > nx - 1.001 or fy > ny - 1.001 or fz > nz - 1.001:
        return 0.0, 0.0, 0.0, 0.0, 0
    i0 = int(fx)
    j0 = int(fy)
    k0 = int(fz)
    tx = fx - i0
    ty = fy - j0
    tz = fz - k0
    d = 0.0
    gx = 0.0
    gy = 0.0
    gz = 0.0
    for di in range(2):
        wxx = tx if di == 1 else 1.0 - tx
        sx = 1.0 if di == 1 else -1.0
        for dj in range(2):
            wyy = ty if dj == 1 else 1.0 - ty
            sy = 1.0 if dj == 1 else -1.0
            for dk in range(2):
                wzz = tz if dk == 1 else 1.0 - tz
                sz = 1.0 if dk == 1 else -1.0
                corner = grid[i0 + di, j0 + dj, k0 + dk]
                if blend == 1:
                    corner = corner + mix * (grid1[i0 + di, j0 + dj, k0 + dk] - corner)
                d += wxx * wyy * wzz * corner
                gx += sx * wyy * wzz * corner
                gy += wxx * sy * wzz * corner
                gz += wxx * wyy * sz * corner
    norm = np.sqrt(gx * gx + gy * gy + gz * gz)
    if norm < 1e-12:
        return d, 0.0, 0.0, 0.0, 0
    return d, gx / norm, gy / norm, gz / norm, 1


def _kernel():
    global field_at, _RUN

    if _RUN is not None:
        return _RUN
    from numba import njit, prange

    if field_at is None:
        field_at = njit(cache=True, fastmath=False)(_field_at_impl)

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
        grid1,
        origin,
        spacing,
        body_rot,
        body_trans,
        body_mix,
        moving,
        blend,
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
        pin_from,
        restitution,
        contact_n,
        contact_u,
        touch,
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
                # The body's schedule. Entry `si` is the body at the END of
                # this substep, entry `si - 1` where it was at the start; on
                # the static path `moving` is 0, `si` stays 0 and the arrays
                # are one entry long, so nothing below reads anything new.
                si = step * moving
                r00 = body_rot[si, 0, 0]
                r01 = body_rot[si, 0, 1]
                r02 = body_rot[si, 0, 2]
                r10 = body_rot[si, 1, 0]
                r11 = body_rot[si, 1, 1]
                r12 = body_rot[si, 1, 2]
                r20 = body_rot[si, 2, 0]
                r21 = body_rot[si, 2, 1]
                r22 = body_rot[si, 2, 2]
                t0 = body_trans[si, 0]
                t1 = body_trans[si, 1]
                t2 = body_trans[si, 2]
                mix = 0.0
                dmix = 0.0
                dr00 = 0.0
                dr01 = 0.0
                dr02 = 0.0
                dr10 = 0.0
                dr11 = 0.0
                dr12 = 0.0
                dr20 = 0.0
                dr21 = 0.0
                dr22 = 0.0
                dt0 = 0.0
                dt1 = 0.0
                dt2 = 0.0
                bvx = 0.0
                bvy = 0.0
                bvz = 0.0
                if moving == 1:
                    mix = body_mix[si]
                    dmix = body_mix[si] - body_mix[si - 1]
                    dr00 = r00 - body_rot[si - 1, 0, 0]
                    dr01 = r01 - body_rot[si - 1, 0, 1]
                    dr02 = r02 - body_rot[si - 1, 0, 2]
                    dr10 = r10 - body_rot[si - 1, 1, 0]
                    dr11 = r11 - body_rot[si - 1, 1, 1]
                    dr12 = r12 - body_rot[si - 1, 1, 2]
                    dr20 = r20 - body_rot[si - 1, 2, 0]
                    dr21 = r21 - body_rot[si - 1, 2, 1]
                    dr22 = r22 - body_rot[si - 1, 2, 2]
                    dt0 = t0 - body_trans[si - 1, 0]
                    dt1 = t1 - body_trans[si - 1, 1]
                    dt2 = t2 - body_trans[si - 1, 2]
                    # the body's rigid velocity, the frame the damping acts in
                    bvx = dt0 / h
                    bvy = dt1 / h
                    bvz = dt2 / h

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
                    if moving == 1 and touch[k] > 0.0:
                        # Numerical damping in the BODY's frame, for cloth
                        # that touched the body last substep. This is the
                        # integrator's 2 % per substep - 29 /s at 24 substeps
                        # - and in the world frame it would brake a garment
                        # carried at 1.35 m/s at 39 m/s^2 while shoulder
                        # friction can hold 3.4: the body would walk out from
                        # under its own shirt. The animator's teleport was
                        # hiding exactly this. Cloth in the air keeps the
                        # world frame: a cape trailing a runner is pulled by
                        # its clasp, not by the frame its numerics live in.
                        # The static branch below is the old line, untouched:
                        # adding a zero velocity back is not an identity for
                        # a negative zero.
                        touch[k] = 0.0
                        v[k, 0] = (v[k, 0] + ax * h - bvx) * retain + bvx
                        v[k, 1] = (v[k, 1] + ay * h - bvy) * retain + bvy
                        v[k, 2] = (v[k, 2] + az * h - bvz) * retain + bvz
                    else:
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
                    ubx = 0.0
                    uby = 0.0
                    ubz = 0.0
                    wx = x[k, 0] - t0
                    wy = x[k, 1] - t1
                    wz = x[k, 2] - t2
                    lx = r00 * wx + r10 * wy + r20 * wz
                    ly = r01 * wx + r11 * wy + r21 * wz
                    lz = r02 * wx + r12 * wy + r22 * wz
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
                    d0 = 0.0
                    for di in range(2):
                        wxx = tx if di == 1 else 1.0 - tx
                        for dj in range(2):
                            wyy = ty if dj == 1 else 1.0 - ty
                            for dk in range(2):
                                wzz = tz if dk == 1 else 1.0 - tz
                                d0 += wxx * wyy * wzz * grid[i0 + di, j0 + dj, k0 + dk]
                    # A deforming body is two fields on one lattice and a
                    # blend: d = d0 + mix (d1 - d0) is one trilinear
                    # interpolant, so its gradient below is the normal of
                    # the same surface the distance came from - the lesson
                    # of the floor-corner bias, kept for a moving surface.
                    d1 = 0.0
                    if blend == 1:
                        for di in range(2):
                            wxx = tx if di == 1 else 1.0 - tx
                            for dj in range(2):
                                wyy = ty if dj == 1 else 1.0 - ty
                                for dk in range(2):
                                    wzz = tz if dk == 1 else 1.0 - tz
                                    d1 += wxx * wyy * wzz * grid1[i0 + di, j0 + dj, k0 + dk]
                        d = d0 + mix * (d1 - d0)
                    else:
                        d = d0
                    if d >= offset:
                        continue
                    # The normal is the gradient of the SAME trilinear
                    # interpolant the distance came from, at the particle.
                    # It used to be a central difference at the cell's floor
                    # corner - the surface normal half a voxel toward -x, -y
                    # and -z of where the particle is - and on a curved body
                    # that tilt is systematic: on the right shoulder the
                    # sampling point sat inboard and the push hooked a sleeve
                    # cap over the crest of the deltoid; on the left it sat
                    # outboard and the push tipped the cap off. Measured on a
                    # walk: one cap climbed 40 mm onto the ball, the other
                    # slid 60 mm down the arm, and swapping every piece of
                    # geometry left and right moved nothing - the bias lived
                    # here, in the field's frame.
                    g0x = 0.0
                    g0y = 0.0
                    g0z = 0.0
                    for di in range(2):
                        wxx = tx if di == 1 else 1.0 - tx
                        sx = 1.0 if di == 1 else -1.0
                        for dj in range(2):
                            wyy = ty if dj == 1 else 1.0 - ty
                            sy = 1.0 if dj == 1 else -1.0
                            for dk in range(2):
                                wzz = tz if dk == 1 else 1.0 - tz
                                sz = 1.0 if dk == 1 else -1.0
                                corner = grid[i0 + di, j0 + dj, k0 + dk]
                                g0x += sx * wyy * wzz * corner
                                g0y += wxx * sy * wzz * corner
                                g0z += wxx * wyy * sz * corner
                    if blend == 1:
                        g1x = 0.0
                        g1y = 0.0
                        g1z = 0.0
                        for di in range(2):
                            wxx = tx if di == 1 else 1.0 - tx
                            sx = 1.0 if di == 1 else -1.0
                            for dj in range(2):
                                wyy = ty if dj == 1 else 1.0 - ty
                                sy = 1.0 if dj == 1 else -1.0
                                for dk in range(2):
                                    wzz = tz if dk == 1 else 1.0 - tz
                                    sz = 1.0 if dk == 1 else -1.0
                                    corner = grid1[i0 + di, j0 + dj, k0 + dk]
                                    g1x += sx * wyy * wzz * corner
                                    g1y += wxx * sy * wzz * corner
                                    g1z += wxx * wyy * sz * corner
                        gx = g0x + mix * (g1x - g0x)
                        gy = g0y + mix * (g1y - g0y)
                        gz = g0z + mix * (g1z - g0z)
                    else:
                        gx = g0x
                        gy = g0y
                        gz = g0z
                    norm = np.sqrt(gx * gx + gy * gy + gz * gz)
                    if norm < 1e-12:
                        continue
                    # the normal is in the field's frame; rotate it back out
                    lnx = gx / norm
                    lny = gy / norm
                    lnz = gz / norm
                    wnx = r00 * lnx + r01 * lny + r02 * lnz
                    wny = r10 * lnx + r11 * lny + r12 * lnz
                    wnz = r20 * lnx + r21 * lny + r22 * lnz
                    push = offset - d
                    x[k, 0] += wnx * push
                    x[k, 1] += wny * push
                    x[k, 2] += wnz * push
                    if moving == 1 and push > 0.25 * spacing:
                        # A large push means the particle was thrown deep -
                        # on a run, a sliver-fringe vertex forty times
                        # lighter than its neighbours, flung 20 mm into the
                        # crease of the shoulder ball and the arm by its
                        # 2.5 mm rest edges. The push itself gets it out
                        # (+2.9 mm, measured). What put it back was
                        # FRICTION, which took its tangent plane from the
                        # normal at the pre-push point, 20 mm inside the
                        # union where the interior gradient is 97 degrees
                        # off the surface: it cancelled the "tangential"
                        # motion outright (the limit scales with the push)
                        # and moved the particle straight back in, to a
                        # fixed point that rode the surface at the body's
                        # normal advance - 7.8, 9.7 and 9.6 mm at 24, 48 and
                        # 96 substeps. So the plane friction acts in, the
                        # contact normal it stores and the damping's touch
                        # gate all come from the PUSHED point, where the
                        # particle actually is.
                        _dd, rnx, rny, rnz, ok = field_at(
                            grid,
                            grid1,
                            blend,
                            mix,
                            origin,
                            spacing,
                            lx + lnx * push,
                            ly + lny * push,
                            lz + lnz * push,
                        )
                        if ok == 1:
                            wnx = r00 * rnx + r01 * rny + r02 * rnz
                            wny = r10 * rnx + r11 * rny + r12 * rnz
                            wnz = r20 * rnx + r21 * rny + r22 * rnz
                    if moving == 1:
                        # How far the body's surface moved under this
                        # particle during the substep: the rigid part is
                        # exact (p = M l + t, so u = dM l + dt) and the
                        # deforming part is the level set's advance along
                        # its own normal, -(d1 - d0) dmix. A level set is
                        # blind to tangential skin slide, which is why a
                        # walk's bob belongs in the rigid schedule.
                        ubx = dr00 * lx + dr01 * ly + dr02 * lz + dt0
                        uby = dr10 * lx + dr11 * ly + dr12 * lz + dt1
                        ubz = dr20 * lx + dr21 * ly + dr22 * lz + dt2
                        if blend == 1:
                            un = -(d1 - d0) * dmix
                            ubx += wnx * un
                            uby += wny * un
                            ubz += wnz * un
                        contact_u[k, 0] = ubx
                        contact_u[k, 1] = uby
                        contact_u[k, 2] = ubz
                        # The body's frame damps this particle next substep
                        # only if the surface is advancing on it or sliding
                        # under it. A surface moving AWAY cannot drag cloth:
                        # coupled regardless, a run's 2.3 g descent pulled
                        # the touching tee down with the body faster than
                        # gravity and left it 10 mm inside at the bottom of
                        # the bob, which the one-sided contact then had to
                        # dig out. Now the cloth falls at 1 g and separates,
                        # which is what a shirt does on a run.
                        if ubx * wnx + uby * wny + ubz * wnz >= 0.0:
                            touch[k] = 1.0
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
                        if moving == 1:
                            # slip RELATIVE to the body at the contact: the
                            # static regime then pins cloth to the BODY,
                            # not to world space, which is what lets a
                            # travelling body carry its garment - and lets
                            # one accelerating faster than mu g slide out
                            # from under it, which is Coulomb too
                            mx -= ubx
                            my -= uby
                            mz -= ubz
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
                            if moving == 1 and push > 0.25 * spacing:
                                # Friction is tangential; it must never put
                                # a particle INSIDE the body. On a curved
                                # surface a tangential move of a few
                                # millimetres dips below the standoff, and
                                # on a thrown fringe vertex the plane can be
                                # off: re-sample the field where the
                                # particle now is and, if it is inside, put
                                # it back on the surface THERE.
                                cx = x[k, 0] - t0
                                cy = x[k, 1] - t1
                                cz = x[k, 2] - t2
                                clx = r00 * cx + r10 * cy + r20 * cz
                                cly = r01 * cx + r11 * cy + r21 * cz
                                clz = r02 * cx + r12 * cy + r22 * cz
                                cd, cnx, cny, cnz, cok = field_at(
                                    grid, grid1, blend, mix, origin, spacing, clx, cly, clz
                                )
                                if cok == 1 and cd < offset:
                                    fix = offset - cd
                                    x[k, 0] += (r00 * cnx + r01 * cny + r02 * cnz) * fix
                                    x[k, 1] += (r10 * cnx + r11 * cny + r12 * cnz) * fix
                                    x[k, 2] += (r20 * cnx + r21 * cny + r22 * cnz) * fix

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
                        if moving == 1:
                            approach -= (
                                contact_u[k, 0] * contact_n[k, 0]
                                + contact_u[k, 1] * contact_n[k, 1]
                                + contact_u[k, 2] * contact_n[k, 2]
                            ) / h
                        if approach < 0.0:
                            give = -(1.0 + restitution) * approach
                            v[k, 0] += contact_n[k, 0] * give
                            v[k, 1] += contact_n[k, 1] * give
                            v[k, 2] += contact_n[k, 2] * give
                        contact_n[k, 0] = 0.0
                        contact_n[k, 1] = 0.0
                        contact_n[k, 2] = 0.0
                    if moving == 1:
                        contact_u[k, 0] = 0.0
                        contact_u[k, 1] = 0.0
                        contact_u[k, 2] = 0.0

                    # pins last, so nothing the substep did can drag a pinned
                    # particle off its target - that is what a pin means. On
                    # a moving body the target is reached along a ramp from
                    # `pin_from`, so a clasp rides the hero through the frame
                    # instead of leading him by a whole frame's travel.
                    if pin_mask[k] > 0.0:
                        if moving == 1:
                            x[k, 0] = pin_from[k, 0] + (pin_target[k, 0] - pin_from[k, 0]) * mix
                            x[k, 1] = pin_from[k, 1] + (pin_target[k, 1] - pin_from[k, 1]) * mix
                            x[k, 2] = pin_from[k, 2] + (pin_target[k, 2] - pin_from[k, 2]) * mix
                        else:
                            x[k, 0] = pin_target[k, 0]
                            x[k, 1] = pin_target[k, 1]
                            x[k, 2] = pin_target[k, 2]
                    v[k, 0] = (x[k, 0] - prev[k, 0]) / h
                    v[k, 1] = (x[k, 1] - prev[k, 1]) / h
                    v[k, 2] = (x[k, 2] - prev[k, 2]) / h

    _RUN = run
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


@dataclass(slots=True)
class Prepared:
    """Everything a solve needs that does NOT change while you drag cloth.

    Colouring the constraint graph, flattening it, building the bending quads
    and the vertex->triangle index cost about 30 ms on a 4,500-particle
    garment, and `drape` rebuilt all of it on every call. That is invisible on
    a 280-frame settle and it is most of the budget on a one-frame drag step:
    measured, a single frame cost 54 ms rebuilt and 24 ms prepared, which is
    18 fps against 42.

    What invalidates it is exactly what it is keyed on - the topology, the
    fabric, the attachments and the solver settings. Anything else (positions,
    velocities, pins, the body) is passed in fresh every step, which is why a
    drag can reuse one of these and a re-mesh cannot.
    """

    key: tuple
    inv_mass: np.ndarray
    share: np.ndarray
    ii: np.ndarray
    jj: np.ndarray
    rest: np.ndarray
    starts: np.ndarray
    alphas: np.ndarray
    bq: np.ndarray
    bend_rest: np.ndarray
    bend_starts: np.ndarray
    bend_alphas: np.ndarray
    tri: np.ndarray
    tri_start: np.ndarray
    tri_index: np.ndarray
    conditioning: dict
    cloth: Fabric
    opts: DrapeSettings


def _prepare_key(garment: GarmentMesh, cloth: Fabric, opts: DrapeSettings) -> tuple:
    return (
        id(garment),
        garment.n_points,
        int(garment.triangles.shape[0]),
        int(garment.structural.shape[0]),
        int(garment.seams.shape[0]),
        tuple(sorted((k, len(v), v.compliance) for k, v in garment.attachments.items())),
        cloth.name,
        opts.grain_angle_deg,
        opts.seam_compliance,
        opts.dt,
        opts.substeps,
        opts.fibre,
        # By CONTENT, not identity: `DrapeSettings.room` builds a fresh
        # Environment on every access when none was set, so keying on
        # `id(opts.room)` meant a prepared solve could never match anything -
        # including the settings object it was built from.
        #
        # And by the room's CONDITIONING, not the whole room. Only temperature,
        # humidity and fibre reach the prepared arrays, through the moisture
        # regain that sets particle mass. Gravity and wind are applied per
        # call, inside the kernel. Keying on the whole room meant an animated
        # wind invalidated the cache on EVERY frame - which is precisely the
        # case the cache exists for, and it was found by animating a cape in a
        # gust and watching the solver refuse its own prepared graph.
        json.dumps(opts.room.conditioning(opts.fibre), sort_keys=True, default=str),
    )


def prepare(
    garment: GarmentMesh,
    *,
    fabric: str | Fabric = "cotton_jersey",
    settings: DrapeSettings | None = None,
) -> Prepared:
    """Build everything a solve needs that survives a change of POSITION.

    Call it once and hand it to `drape` repeatedly - that is what makes a drag
    interactive. See `Prepared` for the measured saving and for what
    invalidates it.
    """
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
    # ... plus anything bolted to it. A zipper, a button and a rivet are not
    # cloth and do not weigh what the cloth under them weighs.
    mass = mass + garment.added_mass_kg()
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
    for block in garment.attachments.values():
        # a lace, a zipper chain, a button's thread - each at ITS OWN
        # stiffness, because a brass chain and a shoelace are not the same
        # thing and neither is the cloth they are attached to.
        if len(block):
            groups += _coloured_groups(block.pairs, block.rest, block.compliance, n)

    ii, jj, rest, starts, alphas = _flatten(groups)
    bq, bend_rest, bend_starts, bend_alphas = _flatten_quads(
        garment.bending, garment.bending_rest, bend, n
    )

    tri = np.ascontiguousarray(garment.triangles, dtype=np.int64)
    tri_start, tri_index = vertex_triangle_csr(n, tri)

    return Prepared(
        key=_prepare_key(garment, cloth, opts),
        inv_mass=inv_mass,
        share=np.ascontiguousarray(share),
        ii=ii,
        jj=jj,
        rest=rest,
        starts=starts,
        alphas=alphas,
        bq=bq,
        bend_rest=bend_rest,
        bend_starts=bend_starts,
        bend_alphas=bend_alphas,
        tri=np.ascontiguousarray(garment.triangles, dtype=np.int64),
        tri_start=tri_start,
        tri_index=tri_index,
        conditioning=conditioning,
        cloth=cloth,
        opts=opts,
    )


def drape(
    garment: GarmentMesh,
    sdf: BodySDF,
    *,
    fabric: str | Fabric = "cotton_jersey",
    settings: DrapeSettings | None = None,
    pins: np.ndarray | None = None,
    pin_target: np.ndarray | None = None,
    prepared: Prepared | None = None,
    velocity: np.ndarray | None = None,
    pin_from: np.ndarray | None = None,
    motion: BodyMotion | None = None,
) -> DrapeResult:
    """Run the drape. Returns positions and a compact report.

    `pins` is a mask over particles: a pinned particle is held at its target
    and nothing in a substep can move it. With `pin_target` it is pulled
    somewhere instead of held - which is what a pinch, a lacing anchor and a
    hand on a hem all reduce to. `pin_from` is where a pinned particle starts
    its ramp toward the target when the body moves (default: the target).

    `motion` moves the body THROUGH the call: `sdf` is where it is at the
    start and `motion.end` where it is `frames * dt` later, with the body's
    placement and, for a deforming body, its field blended at every substep.
    Collision, friction, damping, restitution, the pins and the report all
    see the moving body. Without one the solve is the static one, bit for
    bit - the schedule is one entry long and nothing in the kernel reads it.
    """
    import time

    cloth = fabric if isinstance(fabric, Fabric) else fabric_by_name(fabric)
    opts = settings or DrapeSettings()
    room = opts.room
    n = garment.n_points
    if prepared is not None and prepared.key != _prepare_key(garment, cloth, opts):
        raise ValueError(
            "this Prepared solve does not match this garment, fabric or settings. It "
            "caches the constraint GRAPH, so anything that changes the graph - a "
            "re-mesh, a different fabric, a new attachment, a changed timestep - needs "
            "a fresh one. Rebuild it rather than solving against a stale graph."
        )
    if prepared is None:
        prepared = prepare(garment, fabric=cloth, settings=opts)
    conditioning = prepared.conditioning
    share, inv_mass = prepared.share, prepared.inv_mass
    ii, jj, rest, starts, alphas = (
        prepared.ii,
        prepared.jj,
        prepared.rest,
        prepared.starts,
        prepared.alphas,
    )
    bq, bend_rest, bend_starts, bend_alphas = (
        prepared.bq,
        prepared.bend_rest,
        prepared.bend_starts,
        prepared.bend_alphas,
    )
    tri, tri_start, tri_index = prepared.tri, prepared.tri_start, prepared.tri_index

    # A COPY, always. `ascontiguousarray` hands back the caller's own array
    # when it already is one, and the kernel writes positions in place - so a
    # caller who kept a reference to the points it passed in found them
    # solved out from under it (a "lifted 0.0 mm" that was two names for one
    # array). The copy is n x 3 floats; the surprise was not worth it.
    x = np.array(garment.points, dtype=np.float64, order="C", copy=True)
    v = np.zeros_like(x) if velocity is None else np.ascontiguousarray(velocity, dtype=np.float64)
    prev = np.zeros_like(x)
    h = opts.dt / opts.substeps
    # per-CALL: these depend on how many frames THIS call runs
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
    ramp_from = targets if pin_from is None else np.ascontiguousarray(pin_from, dtype=np.float64)

    grid0 = np.ascontiguousarray(sdf.grid)
    steps = opts.frames * opts.substeps
    if motion is None or not motion.moving:
        # the static path: the same float64 bits the old call passed, one
        # entry each, and flags that keep every new instruction unexecuted
        grid1 = grid0
        body_rot = np.ascontiguousarray(sdf.rotation, dtype=np.float64)[None]
        body_trans = np.ascontiguousarray(sdf.translation, dtype=np.float64)[None]
        body_mix = np.zeros(1, dtype=np.float64)
        moving = 0
        blend = 0
        contact_u = np.zeros((1, 3), dtype=np.float64)
        touch = np.zeros(1, dtype=np.float64)
        report_against = sdf
        motion_report: dict[str, Any] = {}
    else:
        end = motion.end
        if (
            end.grid.shape != sdf.grid.shape
            or not np.array_equal(end.origin, sdf.origin)
            or end.spacing != sdf.spacing
        ):
            raise ValueError(
                "the body's two fields are not on one lattice "
                f"({sdf.grid.shape} at {np.round(sdf.origin, 4).tolist()} vs "
                f"{end.grid.shape} at {np.round(end.origin, 4).tolist()}): bake both "
                "with the same `bounds=` and voxel size."
            )
        if motion.steps != steps:
            raise ValueError(
                f"this motion spans {motion.steps} substeps; these settings run "
                f"{steps} (frames x substeps). Build it with steps=frames*substeps "
                "for THESE settings."
            )
        if not (
            np.array_equal(motion.rotation[0], sdf.rotation)
            and np.array_equal(motion.translation[0], sdf.translation)
        ):
            raise ValueError(
                "the motion does not start where the body is: its first entry must "
                "equal `sdf`'s rotation and translation (build it from this `sdf`)."
            )
        grid1 = np.ascontiguousarray(end.grid) if motion.blend else grid0
        body_rot = np.ascontiguousarray(motion.rotation, dtype=np.float64)
        body_trans = np.ascontiguousarray(motion.translation, dtype=np.float64)
        body_mix = np.ascontiguousarray(motion.mix, dtype=np.float64)
        moving = 1
        blend = 1 if motion.blend else 0
        contact_u = np.zeros_like(x)
        touch = np.zeros(n, dtype=np.float64)
        report_against = end
        travel = float(np.linalg.norm(motion.translation[-1] - motion.translation[0]))
        motion_report = {
            "travel_mm": round(travel * 1000.0, 1),
            "blend": bool(motion.blend),
        }

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
        grid0,
        grid1,
        np.ascontiguousarray(sdf.origin),
        sdf.spacing,
        body_rot,
        body_trans,
        body_mix,
        moving,
        blend,
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
        ramp_from,
        float(getattr(cloth, "restitution", 0.0)),
        np.zeros_like(x),
        contact_u,
        touch,
        h,
        1.0 - opts.damping,
        opts.frames,
        opts.substeps,
        friction_for(opts, cloth),
    )
    seconds = time.perf_counter() - started

    from hashlib import sha256

    return DrapeResult(
        points=x,
        settings=opts,
        fabric=cloth.name,
        seam_gaps=garment.seam_gaps_mm(x),
        penetration=measure_penetration(x, report_against),
        contact=measure_contact(x, report_against),
        environment=room.describe(),
        conditioning=conditioning,
        seconds=seconds,
        fingerprint=sha256(np.round(x, 6).tobytes()).hexdigest()[:16],
        velocity=v,
        body_motion=motion_report,
    )


def _triangle_areas(garment: GarmentMesh) -> np.ndarray:
    p = garment.rest_points_mm * 1e-3
    tri = garment.triangles
    a, b, c = p[tri[:, 0]], p[tri[:, 1]], p[tri[:, 2]]
    return 0.5 * (
        (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
    )
