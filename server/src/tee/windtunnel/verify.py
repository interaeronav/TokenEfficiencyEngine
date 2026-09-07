"""The validation battery behind `wt_verify`: a reference is not a
tolerance until it has been verified at its source, with a date.

Each case below names its reference, where it comes from, and the date it
was checked. A case whose `verified` is None refuses with
`wt_reference_unverified` rather than pretending; a case that is verified
but has no runner yet refuses the same way and is reported separately by
`case=all`, because a reference nobody can run is still not a test.

Both owner-session rows (R3/R4) closed 2026-09-06/07. R3 changed what it
validates against rather than what it claims: the two JFM originals it
first named are paywalled and were never read, so the target is now an
open, peer-reviewed paper written to BE a reference solution, with its own
convergence study. An unreadable citation is not a source, and quoting one
second-hand would have been the thing this module exists to prevent.
"""

from __future__ import annotations

import math
from typing import Any

from tee.kernel.errors import TeeError
from tee.windtunnel import physics

REFERENCES: dict[str, dict[str, Any]] = {
    "wing_liftslope": {
        "engine": "vspaero",
        "what": "rectangular NACA 0012 wing, AR 10, M 0.1, alpha 0..6 deg (VLM)",
        "reference": (
            "Prandtl lifting line a = a0 / (1 + a0 / (pi e AR)) with e = 0.95; "
            "CDi = CL^2 / (pi e AR)"
        ),
        "source": (
            "Anderson, Fundamentals of Aerodynamics, §5.3-5.4 "
            "(a textbook formula, not a measurement)"
        ),
        "verified": (
            "2026-09-06 (formula) - VLM measured 4.905/rad vs 5.19/rad, -5.5 %, on this machine"
        ),
        "tolerance": {"cl_alpha_pct": 8.0, "cdi_pct": 15.0, "cl0_abs": 0.005},
    },
    "naca0012_euler": {
        "engine": "su2",
        "what": "NACA 0012, SU2 Euler, M 0.8, alpha 1.25 deg on TEE's O-mesh",
        "reference": (
            "CL 0.328486, CD 0.021481: the SU2 8.4.0 QuickStart case on its official mesh "
            "(10,216 elements)"
        ),
        "source": (
            "su2code/SU2 QuickStart inv_NACA0012.cfg + mesh_NACA0012_inv.su2, run 2026-09-06 "
            "on this machine (147 iterations, 9.85 s); AGARD AR-211 Test Case 01 cross-check "
            "still owed"
        ),
        "verified": (
            "2026-09-06 (run on the official mesh) - TEE's O-mesh measured CL +2.3 %, CD -1.2 %"
        ),
        "tolerance": {"cl_pct": 5.0, "cd_pct": 15.0},
        "cl": 0.328486,
        "cd": 0.021481,
    },
    "cylinder_re40": {
        "engine": "openfoam",
        "what": "2-D cylinder, Re 40, laminar, O-grid",
        "reference": (
            "CD 1.4931, wake length Lw/D 2.2360, separation angle 126.3945 deg: the reference "
            "case of Gautier, Biau & Lamballais (pseudo-spectral, fine grid Nr 200 x Ntheta "
            "1024, r_inf 40 D). Historical context, NOT the target: the same paper's table 1 "
            "puts the literature at 1.48 < CD < 1.62 and 2.13 < Lw/D < 2.35 - about 10 % "
            "scatter - including Dennis & Chang 1970 at 1.52 and Fornberg 1980 at 1.50"
        ),
        "source": (
            "Computers & Fluids 75 (2013) 103-111, open at https://hal.science/hal-00876327 "
            "(the authors' own deposit) and arXiv:1310.6641; table 2 for the reference case, "
            "table 1 for the literature spread. A paper written to BE a validation reference, "
            "with its own convergence study - which is why it replaced the two paywalled "
            "originals the script first named (script §M row R3)"
        ),
        "verified": (
            "2026-09-07 at https://hal.science/hal-00876327 (values pasted from the PDF's "
            "tables 1-2, owner session; the JFM originals are paywalled and were never read, "
            "so they are context here and never the tolerance)"
        ),
        "tolerance": {"cd_pct": 5.0, "wake_pct": 15.0},
        "cd": 1.4931,
        "wake_lw_over_d": 2.2360,
        "separation_deg": 126.3945,
    },
    "flatplate": {
        "engine": "openfoam",
        "what": "NASA TMR 2-D zero-pressure-gradient flat plate, Re_L 5e6, kOmegaSST",
        "reference": (
            "Cf 2.690853551e-03 at x = 0.9700840712 m (CFL3D, 545x385 grid; FUN3D reads "
            "2.690546447e-03 at the same x), SST-Vm, M 0.2, Re 5e6"
        ),
        "source": (
            "tmbwg.github.io/turbmodels flatplate_sst.html + FlatPlate/SST/cf_plate_sstv.dat "
            "(the live successor of turbmodels.larc.nasa.gov, which now 301s to a nasa.gov "
            "landing page pointing there)"
        ),
        "verified": (
            "2026-09-06 at https://tmbwg.github.io/turbmodels/flatplate_sst.html "
            "(values pasted from FlatPlate/SST/cf_plate_sstv.dat, owner session)"
        ),
        "tolerance": {"cf_pct": 5.0},
        "cf": 2.690853551e-03,
    },
}


# the cases whose runners exist; a verified reference without a runner is
# reported as skipped_unimplemented by `all` and refuses when named directly
# (flatplate is the one left: the NASA TMR plate needs a blockMesh writer
# this lane does not have yet)
_RUNNABLE = ("wing_liftslope", "naca0012_euler", "cylinder_re40")


def run(lane: Any, which: str, *, confirm_cost: bool) -> dict[str, Any]:
    names = list(REFERENCES) if which == "all" else [which]
    unknown = [n for n in names if n not in REFERENCES]
    if unknown:
        raise TeeError(
            "wt_bad_action",
            f"No verification case {unknown}.",
            fix=f"One of: {', '.join(REFERENCES)}, all.",
        )
    for n in names:
        if REFERENCES[n]["verified"] is None and which != "all":
            raise TeeError(
                "wt_reference_unverified",
                f"{n}: its reference ({REFERENCES[n]['reference']}) has not been verified "
                "at its source.",
                fix=f"Verify {REFERENCES[n]['source']} and record the date in "
                "verify.REFERENCES; until then the case is not a test.",
            )
        if n not in _RUNNABLE and which != "all":
            raise TeeError(
                "wt_reference_unverified",
                f"{n} is not runnable yet: its reference is verified but its runner is not built.",
                fix="See verify.REFERENCES and verify._RUNNABLE.",
            )
    runnable = [n for n in names if REFERENCES[n]["verified"] is not None and n in _RUNNABLE]
    skipped = [n for n in names if REFERENCES[n]["verified"] is None]
    unbuilt = [n for n in names if REFERENCES[n]["verified"] is not None and n not in _RUNNABLE]
    results = [_run_one(lane, n, confirm_cost=confirm_cost) for n in runnable]
    return {
        "results": results,
        "skipped_unverified": skipped,
        "skipped_unimplemented": unbuilt,
        "all_pass": all(r["pass"] for r in results) if results else False,
    }


def _run_one(lane: Any, name: str, *, confirm_cost: bool) -> dict[str, Any]:
    ref = REFERENCES[name]
    if name == "wing_liftslope":
        return _wing_liftslope(lane, ref, confirm_cost=confirm_cost)
    if name == "naca0012_euler":
        return _naca0012_euler(lane, ref, confirm_cost=confirm_cost)
    if name == "cylinder_re40":
        return _cylinder_re40(lane, ref, confirm_cost=confirm_cost)
    raise TeeError(
        "wt_reference_unverified", f"{name} is not runnable yet.", fix="See verify.REFERENCES."
    )


# The Re 40 cylinder's own constants, each one measured rather than chosen.
#
# `V` is 0.001 m/s because the case record rounds V to four decimals: asking
# for D = 1 m instead makes V = 5.842874e-04 round to 0.0006 and the case runs
# at **Re 41.08**, a 2.7 % error smuggled in by a round(). Fixing V at a value
# that survives the rounding and solving for the diameter lands Re on exactly
# 40.0000 (measured 2026-09-07).
#
# The grid is where a convergence study on this machine stopped moving, not a
# guess (CD against the 1.4931 reference):
#
#     ni x nj    r_inf     CD        vs ref
#     128 x 200    60    1.5228     +1.99 %
#     256 x 200    60    1.5183     +1.69 %     <- adopted
#     384 x 200    60    1.5181     +1.68 %
#     256 x 200   100    1.5138     +1.39 %
#
# Azimuthally converged by ni 256 and radially by nj 200; what is left drifts
# with the DOMAIN, which is the very thing the reference paper was written to
# fix (it reports CD 1.4906 / 1.4931 / 1.4943 at r_inf 30 / 40 / 50, and quotes
# Posdziec & Grundmann needing 4,000 diameters). A second-order finite-volume
# O-mesh landing +1.7 % from a spectral solution with asymptotic far-field
# conditions is the expected size of that gap, not a defect - and it is why the
# tolerance is 5 % rather than something tighter.

_CYL_V_MPS = 0.001
_CYL_RE = 40.0
_CYL_N_SURFACE = 128  # -> ni 256
_CYL_NJ = 200
_CYL_RADIUS_D = 60.0
_CYL_ITERS = 8000


def _cylinder_diameter() -> float:
    """The diameter that puts Re on 40 exactly, given sea-level ISA and a V
    that survives the case record's rounding."""
    from tee.windtunnel import atmosphere

    air = atmosphere.isa(0.0)
    return _CYL_RE * (air.mu / air.rho) / _CYL_V_MPS


def _cylinder_wake(lane: Any, case_id: str, diameter: float) -> dict[str, Any]:
    """Wake length from the centreline: the recirculation closes where the
    streamwise velocity changes sign. Needs ParaView, so it is OPTIONAL -
    a missing pvpython makes this check `skipped`, never a failure, because
    CD is what the tolerance gates.
    """
    try:
        probe = lane.probe_field(
            {
                "case_id": case_id,
                "what": "line",
                "field": "U",
                "components": True,
                "p1": [0.5 * diameter, 0.0, 0.0],
                "p2": [4.0 * diameter, 0.0, 0.0],
                "n": 64,
            }
        )
    except TeeError as exc:
        return {"measured": None, "skipped": f"{exc.code}: {exc.message[:120]}"}
    xs, us = _centreline_u(probe, diameter)
    if len(xs) < 4:
        return {"measured": None, "skipped": "the centreline probe returned too few samples"}
    for k in range(1, len(xs)):
        if us[k - 1] < 0.0 <= us[k]:  # the sign change closes the bubble
            span = us[k] - us[k - 1]
            frac = 0.0 if span == 0 else (0.0 - us[k - 1]) / span
            x_re = xs[k - 1] + frac * (xs[k] - xs[k - 1])
            return {"measured": round((x_re - 0.5 * diameter) / diameter, 4)}
    return {"measured": None, "skipped": "no reversed flow on the centreline (no closed bubble)"}


def _centreline_u(probe: dict[str, Any], diameter: float) -> tuple[list[float], list[float]]:
    """(x, u_x) pairs out of a probe_field line sample, whatever shape the
    reader gave the components."""
    samples = probe.get("samples") or []
    xs: list[float] = []
    us: list[float] = []
    p1 = (probe.get("p1") or [0.0])[0]
    p2 = (probe.get("p2") or [1.0])[0]
    n = max(len(samples) - 1, 1)
    for i, s in enumerate(samples):
        if isinstance(s, dict):
            u = s.get("U_x", s.get("Ux", s.get("x")))
            x = s.get("Points_0", s.get("arc_length"))
            x = p1 + (p2 - p1) * i / n if x is None else float(x)
        elif isinstance(s, list | tuple) and s:
            u, x = s[0], p1 + (p2 - p1) * i / n
        else:
            u, x = s, p1 + (p2 - p1) * i / n
        if u is None:
            continue
        xs.append(float(x))
        us.append(float(u))
    return xs, us


def _cylinder_re40(lane: Any, ref: dict[str, Any], *, confirm_cost: bool) -> dict[str, Any]:
    diameter = _cylinder_diameter()
    created = lane._create(
        {
            "circle": True,
            "chord_m": diameter,
            "V_mps": _CYL_V_MPS,
            "aoa_deg": 0.0,
            "n_surface": _CYL_N_SURFACE,
            "fidelity": "rans",
            "turbulence": "laminar",
            "need_viscous": True,
        }
    )
    case_id = created["case_id"]
    re_actual = float(created.get("conditions", {}).get("Re") or 0.0)
    if abs(re_actual - _CYL_RE) > 0.05:
        raise TeeError(
            "wt_verify_failed",
            f"the case came out at Re {re_actual:g}, not {_CYL_RE:g}.",
            fix="A benchmark run at the wrong Reynolds number is not a test; check "
            "atmosphere.conditions and the rounding of V.",
        )
    lane.mesh({"case_id": case_id, "nj": _CYL_NJ, "radius_c": _CYL_RADIUS_D})
    rec = lane.store.load(case_id)
    sub = lane._submit_runs(
        rec,
        [0.0],
        # one core on purpose: cores > 1 routes through decomposePar and
        # mpirun, which buys about a second on a case this size and costs
        # the battery its portability (the hermetic fakes ship no mpirun)
        {"confirm_cost": confirm_cost, "iters": _CYL_ITERS, "cores": 1},
        label="wt_verify",
    )
    res = _wait(lane, sub["job"], timeout_s=3600.0)
    cd = res.get("cd")
    if cd is None:
        raise TeeError(
            "wt_verify_failed",
            "OpenFOAM returned no drag coefficient.",
            fix="See the run log in the case directory.",
        )
    tol = ref["tolerance"]
    checks: dict[str, Any] = {
        "cd": {
            "measured": cd,
            "reference": ref["cd"],
            "pct": round(100 * (cd - ref["cd"]) / ref["cd"], 2),
            "tol_pct": tol["cd_pct"],
        }
    }
    ok = abs(checks["cd"]["pct"]) <= tol["cd_pct"]
    wake = _cylinder_wake(lane, case_id, diameter)
    if wake.get("measured") is not None:
        lw = float(wake["measured"])
        ref_lw = float(ref["wake_lw_over_d"])
        checks["wake_lw_over_d"] = {
            "measured": lw,
            "reference": ref_lw,
            "pct": round(100 * (lw - ref_lw) / ref_lw, 2),
            "tol_pct": tol["wake_pct"],
        }
        ok = ok and abs(checks["wake_lw_over_d"]["pct"]) <= tol["wake_pct"]
    else:
        checks["wake_lw_over_d"] = {"measured": None, "skipped": wake.get("skipped")}
    ok = ok and res.get("verdict", {}).get("state") in ("converged", "stalled")
    return {
        "case": "cylinder_re40",
        "case_id": case_id,
        "engine": "openfoam",
        "Re": re_actual,
        "diameter_m": round(diameter, 6),
        "checks": checks,
        "verdict": res.get("verdict", {}).get("state"),
        "pass": ok,
        "cite": ref["source"],
        "verified": ref["verified"],
    }


def _wait(lane: Any, job_id: str, timeout_s: float = 3600.0) -> dict[str, Any]:
    from tee.kernel.waiting import wait_until

    def done() -> bool:
        return lane.app.jobs.status(job_id)["state"] in ("done", "error", "cancelled")

    wait_until(done, timeout_s, max_delay_s=2.0)
    st = lane.app.jobs.status(job_id)
    if st["state"] != "done":
        raise TeeError(
            "wt_verify_failed",
            f"job {job_id} ended {st['state']}: {st.get('error')}",
            fix="See the run's log in the case directory.",
        )
    return st["result"]


def _wing_liftslope(lane: Any, ref: dict[str, Any], *, confirm_cost: bool) -> dict[str, Any]:
    created = lane._create(
        {
            "wing": {"span": 10.0, "root_chord": 1.0, "airfoil": "0012"},
            "V_mps": 34.0,
            "aoa_deg": 4.0,
            "fidelity": "panel",
        }
    )
    case_id = created["case_id"]
    rec = lane.store.load(case_id)
    sub = lane._submit_runs(
        rec, [0.0, 2.0, 4.0, 6.0], {"confirm_cost": confirm_cost, "cores": 4}, label="wt_verify"
    )
    res = _wait(lane, sub["job"])
    polar = res.get("polar") or []
    if len(polar) < 2:
        raise TeeError(
            "wt_verify_failed",
            "VSPAERO returned fewer than two polar points.",
            fix="See the run log.",
        )
    AR = 10.0
    e = 0.95
    a_ll = physics.cl_alpha_3d(AR, e)
    cl_alpha = res.get("cl_alpha_per_rad") or 0.0
    last = polar[-1]
    cdi_ll = physics.induced_drag(last["cl"], AR, last.get("e") or e)
    cl0 = polar[0]["cl"]
    tol = ref["tolerance"]
    checks = {
        "cl_alpha": {
            "measured": cl_alpha,
            "reference": round(a_ll, 4),
            "pct": round(100 * (cl_alpha - a_ll) / a_ll, 2),
            "tol_pct": tol["cl_alpha_pct"],
        },
        "cdi_at_6deg": {
            "measured": last["cdi"],
            "reference": round(cdi_ll, 6),
            "pct": round(100 * (last["cdi"] - cdi_ll) / cdi_ll, 2),
            "tol_pct": tol["cdi_pct"],
        },
        "cl_at_0deg": {
            "measured": cl0,
            "reference": 0.0,
            "abs": abs(cl0),
            "tol_abs": tol["cl0_abs"],
        },
    }
    ok = (
        abs(checks["cl_alpha"]["pct"]) <= tol["cl_alpha_pct"]
        and abs(checks["cdi_at_6deg"]["pct"]) <= tol["cdi_pct"]
        and abs(cl0) <= tol["cl0_abs"]
    )
    return {
        "case": "wing_liftslope",
        "case_id": case_id,
        "engine": "vspaero",
        "checks": checks,
        "pass": ok,
        "cite": ref["source"],
        "verified": ref["verified"],
    }


def _naca0012_euler(lane: Any, ref: dict[str, Any], *, confirm_cost: bool) -> dict[str, Any]:
    created = lane._create(
        {"naca": "0012", "mach": 0.8, "aoa_deg": 1.25, "fidelity": "euler", "need_viscous": False}
    )
    case_id = created["case_id"]
    lane.mesh({"case_id": case_id, "first_cell_c": 0.005, "nj": 50})
    rec = lane.store.load(case_id)
    sub = lane._submit_runs(
        rec, [1.25], {"confirm_cost": confirm_cost, "iters": 3000}, label="wt_verify"
    )
    res = _wait(lane, sub["job"], timeout_s=3600.0)
    cl, cd = res.get("cl"), res.get("cd")
    if cl is None or cd is None:
        raise TeeError("wt_verify_failed", "SU2 returned no coefficients.", fix="See the run log.")
    tol = ref["tolerance"]
    checks = {
        "cl": {
            "measured": cl,
            "reference": ref["cl"],
            "pct": round(100 * (cl - ref["cl"]) / ref["cl"], 2),
            "tol_pct": tol["cl_pct"],
        },
        "cd": {
            "measured": cd,
            "reference": ref["cd"],
            "pct": round(100 * (cd - ref["cd"]) / ref["cd"], 2),
            "tol_pct": tol["cd_pct"],
        },
    }
    ok = (
        abs(checks["cl"]["pct"]) <= tol["cl_pct"]
        and abs(checks["cd"]["pct"]) <= tol["cd_pct"]
        and res.get("verdict", {}).get("state") in ("converged", "stalled")
    )
    return {
        "case": "naca0012_euler",
        "case_id": case_id,
        "engine": "su2",
        "checks": checks,
        "verdict": res.get("verdict", {}).get("state"),
        "pass": ok,
        "cite": ref["source"],
        "verified": ref["verified"],
    }


def reference_table() -> list[dict[str, Any]]:
    return [
        {"case": k, "engine": v["engine"], "verified": v["verified"], "reference": v["reference"]}
        for k, v in REFERENCES.items()
    ]


__all__ = ["REFERENCES", "math", "reference_table", "run"]
