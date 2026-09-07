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


# the two cases whose runners exist; a verified reference without a runner is
# reported as skipped_unimplemented by `all` and refuses when named directly
_RUNNABLE = ("wing_liftslope", "naca0012_euler")


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
    raise TeeError(
        "wt_reference_unverified", f"{name} is not runnable yet.", fix="See verify.REFERENCES."
    )


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
