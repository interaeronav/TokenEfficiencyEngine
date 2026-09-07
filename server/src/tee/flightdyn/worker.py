"""The child process that is allowed to import JSBSim.

Run as `python -m tee.flightdyn.worker`, reading one JSON job on stdin and
writing one JSON result on stdout. It lives in a separate process because
`FGLinearization` on an aircraft with no engine does not raise - it SIGSEGVs,
and a server that called it in-process would go with it.

numpy is imported here and nowhere else in the lane; it is the `flightdyn`
extra's only member.
"""

from __future__ import annotations

import json
import math
import sys
from typing import Any

TOL = {"udot": 1e-3, "wdot": 1e-3, "qdot": 1e-4}
SPOOL_S = 2.0


def _mute(jsbsim: Any) -> None:
    """192 bytes of banner go to stdout otherwise, and stdout is our channel."""

    class Mute(jsbsim.FGLogger):
        def Message(self, msg):
            pass

        def FileLocation(self, path, line):
            pass

        def Format(self, fmt):
            pass

        def Flush(self):
            pass

        def SetLevel(self, lvl):
            pass

    jsbsim.set_logger(Mute())


def _open(jsbsim: Any, job: dict) -> Any:
    fdm = jsbsim.FGFDMExec(job["root"])
    fdm.set_debug_level(0)
    if not fdm.load_model(job["aircraft"]):
        raise RuntimeError(f"JSBSim would not load aircraft {job['aircraft']!r}")
    if fdm.get_propulsion().get_num_engines() < 1:
        # The SIGSEGV guard, in our code, before any linearisation can reach it.
        raise RuntimeError("aircraft has no engines; FGLinearization would kill the process")
    return fdm


def _set_ic(fdm: Any, cond: dict, alpha_deg: float | None = None) -> None:
    fdm.set_property_value("ic/h-sl-ft", cond["altitude_ft"])
    fdm.set_property_value("ic/vc-kts", cond["kcas"])
    fdm.set_property_value("ic/gamma-deg", cond.get("gamma_deg", 0.0))
    if alpha_deg is not None:
        fdm.set_property_value("ic/alpha-deg", alpha_deg)
    fdm.run_ic()


def _spool(fdm: Any, throttle: float = 0.5) -> None:
    """Once. `run_ic` does not reset the spool, so later ICs keep it.

    Without this the turbine sits near 100% N2 whatever the throttle says, and
    a trim over udot finds no authority. It is why JSBSim's own do_trim fails
    on a generated aircraft and blames qdot.
    """
    fdm.set_property_value("propulsion/set-running", -1)
    fdm.set_property_value("fcs/throttle-cmd-norm", throttle)
    for _ in range(int(SPOOL_S / fdm.get_delta_t())):
        fdm.run()


def _residual(fdm: Any, cond: dict, x) -> list[float]:
    _set_ic(fdm, cond, alpha_deg=x[0])
    fdm.set_property_value("fcs/elevator-cmd-norm", x[1])
    fdm.set_property_value("fcs/throttle-cmd-norm", x[2])
    fdm.run()
    return [
        fdm.get_property_value("accelerations/udot-ft_sec2"),
        fdm.get_property_value("accelerations/wdot-ft_sec2"),
        fdm.get_property_value("accelerations/qdot-rad_sec2"),
    ]


def trim(fdm: Any, cond: dict, itmax: int = 60) -> dict:
    """A 3x3 Newton over (alpha, elevator, throttle). Ours, not JSBSim's."""
    import numpy as np

    names = ("udot", "wdot", "qdot")
    tol = np.array([TOL[n] for n in names])
    x = np.array([2.0, 0.0, 0.5])
    step = np.array([0.05, 0.005, 0.005])
    lo = np.array([-10.0, -1.0, 0.0])
    hi = np.array([18.0, 1.0, 1.0])
    for it in range(itmax):
        r = np.array(_residual(fdm, cond, x))
        if np.all(np.abs(r) < tol):
            return {
                "converged": True,
                "iterations": it,
                "alpha_deg": float(x[0]),
                "elevator": float(x[1]),
                "throttle": float(x[2]),
                "residual": {n: float(v) for n, v in zip(names, r, strict=True)},
                "thrust_lbs": fdm.get_property_value("propulsion/engine/thrust-lbs"),
                "gamma_deg": fdm.get_property_value("flight-path/gamma-deg"),
                "theta_deg": fdm.get_property_value("attitude/theta-deg"),
            }
        J = np.empty((3, 3))
        for j in range(3):
            xp = x.copy()
            xp[j] += step[j]
            J[:, j] = (np.array(_residual(fdm, cond, xp)) - r) / step[j]
        try:
            dx = np.linalg.solve(J, -r)
        except np.linalg.LinAlgError as exc:
            worst = names[int(np.argmax(np.abs(r) / tol))]
            raise RuntimeError(
                f"trim is singular at iteration {it}: no control moves {worst}"
            ) from exc
        cap = np.array([2.0, 0.2, 0.2])
        x = np.clip(x + np.clip(dx, -cap, cap), lo, hi)
    worst = int(np.argmax(np.abs(r) / tol))
    raise RuntimeError(
        f"trim did not converge in {itmax} iterations: {names[worst]} residual "
        f"{r[worst]:.3e} exceeds {tol[worst]:.0e}"
    )


def modes(fdm: Any) -> dict:
    """A, B and the oscillatory modes by modal participation factor."""
    import jsbsim
    import numpy as np

    # FGLinearization PERTURBS the model to build its Jacobian and leaves it
    # perturbed (it also leaves dt at 0). Anything the cross-check needs from
    # the trim state must be read BEFORE it runs, or L/D comes back at 125.
    snap = {
        "vt_fps": fdm.get_property_value("velocities/vt-fps"),
        # WIND axes, not body: fbx/fbz carry lift's component at alpha and
        # give L/D 125 where the truth is 31. JSBSim publishes the ratio.
        "lift_lbs": fdm.get_property_value("forces/fwz-aero-lbs"),
        "drag_lbs": fdm.get_property_value("forces/fwx-aero-lbs"),
        "lod": fdm.get_property_value("forces/lod-norm"),
    }
    lin = jsbsim.FGLinearization(fdm)
    A = np.array(lin.system_matrix)
    ev, V = np.linalg.eig(A)
    W = np.linalg.inv(V)
    P = np.abs(V * W.T)
    P = P / P.sum(axis=0, keepdims=True)
    out, dropped = [], 0
    for i, e in enumerate(ev):
        if e.imag <= 1e-6:
            continue
        if abs(e) <= 1e-4:
            dropped += 1  # a polar carries no lateral terms: Phi/P come back degenerate
            continue
        top = np.argsort(-P[:, i])[:2]
        wn = abs(e)
        out.append(
            {
                "period_s": round(2 * math.pi / e.imag, 4),
                "wn_rad_s": round(float(wn), 5),
                "zeta": round(float(-e.real / wn), 5),
                "eigenvalue": f"{e.real:.5f}{e.imag:+.5f}j",
                "participation": [f"{lin.x_names[k]} {P[k, i]:.0%}" for k in top],
            }
        )
    out.sort(key=lambda m: m["period_s"])
    return {
        "cross_check": _phugoid_check(snap, out),
        "states": list(lin.x_names),
        "inputs": list(lin.u_names),
        "A_shape": list(A.shape),
        "B_shape": list(np.shape(lin.input_matrix)),
        "modes": out,
        "degenerate_pairs_dropped": dropped,
    }


def _phugoid_check(snap: dict, found: list[dict]) -> dict:
    """Compare the phugoid against closed form, so a number carries a witness.

    Lanchester: T = pi*sqrt(2)*V/g on TRUE airspeed (using calibrated instead
    flatters the result at altitude). Damping: zeta ~ 1/(sqrt(2)*L/D). Both are
    approximations that neglect thrust and compressibility - they are a sanity
    witness, not a tolerance.
    """
    ph = [
        m
        for m in found
        if any(n.startswith("Vt") for n in m["participation"])
        and any(n.startswith("Theta") for n in m["participation"])
    ]
    if not ph:
        return {"phugoid": "not identified"}
    m = ph[0]
    vt_fps = snap["vt_fps"]
    v_ms = vt_fps * 0.3048
    t_lanchester = math.pi * math.sqrt(2.0) * v_ms / 9.80665
    ld = snap["lod"]
    zeta_theory = 1.0 / (math.sqrt(2.0) * ld) if ld == ld and ld > 0 else float("nan")
    return {
        "phugoid_period_s": m["period_s"],
        "lanchester_period_s": round(t_lanchester, 3),
        "period_error_pct": round(100.0 * (m["period_s"] - t_lanchester) / t_lanchester, 1),
        "true_airspeed_kt": round(vt_fps * 0.592484, 2),
        "phugoid_zeta": m["zeta"],
        "zeta_theory": round(zeta_theory, 5) if zeta_theory == zeta_theory else None,
        "lift_over_drag": round(ld, 2) if ld == ld else None,
        "basis": "Lanchester T=pi*sqrt(2)*V/g on TRUE airspeed; zeta~1/(sqrt(2)*L/D)",
    }


def hold(fdm: Any, seconds: float) -> dict:
    """Fly the trimmed state and report whether it stayed there."""
    dt = fdm.get_delta_t()
    if dt == 0.0:
        fdm.set_dt(1.0 / 120.0)  # FGLinearization leaves dt at 0
        dt = fdm.get_delta_t()
    start_alt = fdm.get_property_value("position/h-sl-ft")
    for _ in range(int(seconds / dt)):
        fdm.run()
    return {
        "seconds": seconds,
        "altitude_ft": round(fdm.get_property_value("position/h-sl-ft"), 1),
        "altitude_drift_ft": round(fdm.get_property_value("position/h-sl-ft") - start_alt, 1),
        "kcas": round(fdm.get_property_value("velocities/vc-kts"), 2),
        "nz": round(fdm.get_property_value("accelerations/Nz"), 4),
        "theta_deg": round(fdm.get_property_value("attitude/theta-deg"), 3),
    }


def main() -> int:
    job = json.load(sys.stdin)
    try:
        import jsbsim
    except ImportError as exc:
        json.dump({"error": "fd_jsbsim_missing", "detail": str(exc)}, sys.stdout)
        return 0
    try:
        _mute(jsbsim)
        fdm = _open(jsbsim, job)
        cond = job.get("condition", {"altitude_ft": 5000.0, "kcas": 90.0})
        _spool(fdm)
        out: dict[str, Any] = {"jsbsim": jsbsim.__version__}
        want = job.get("want", ["trim"])
        if "trim" in want:
            out["trim"] = trim(fdm, cond)
        if "modes" in want:
            out["modes"] = modes(fdm)
        if "hold" in want:
            out["hold"] = hold(fdm, float(job.get("hold_s", 60.0)))
        json.dump(out, sys.stdout)
    except Exception as exc:  # the child reports; the parent never guesses
        json.dump({"error": "fd_worker_failed", "detail": str(exc)[:600]}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
