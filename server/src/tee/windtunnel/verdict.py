"""A coefficient without a verdict is not a result.

The convergence verdict follows the NPARC Alliance's iterative-convergence
guidance ("Examining Iterative Convergence", NASA Glenn) and AIAA G-077-1998:
the residuals must have dropped by a stated number of orders from their
early peak AND the quantities of interest must be stationary over the final
window - split into halves whose means agree and whose scatter is small.
A run whose residuals stall while the coefficients sit still is `stalled`
(usable, labelled); one whose coefficients keep oscillating is
`oscillating`; anything non-finite or with residuals climbing back up is
`diverged`.

The uncertainty label is the DPW/HiLiftPW calibration the field itself
publishes (Vassberg et al., AIAA 2010-4547; the HiLiftPW summaries): RANS
on attached cruise flow is a COMPARATIVE tool trustworthy to a few counts
between similar cases and an ABSOLUTE tool of limited value; separated
flow, buffet and CLmax are not predicted. The label travels with every
number; the exact drag-count figures are quoted from those sources and are
re-verified in doc 70 §8 before any tolerance is built on them.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

STATES = (
    "converged",
    "stalled",
    "oscillating",
    "diverged",
    "insufficient",
    "running",
    "error",
    "cancelled",
)


def orders_dropped(series: list[float]) -> float | None:
    """log10(early peak / last), the early peak being the max of the first
    ten samples (the first iteration is often an artefact)."""
    finite = [v for v in series if v == v and v > 0 and v != math.inf]
    if len(finite) < 3:
        return None
    peak = max(finite[: min(10, len(finite))])
    return math.log10(peak / finite[-1]) if finite[-1] > 0 else None


# A relative test on a coefficient that is nearly zero (Cm about the quarter
# chord of a symmetric section, CL at zero incidence) is meaningless, so the
# scale has a floor: above it the tolerance is relative, below it absolute -
# 0.5 % of 0.1 is 0.0005 in CL, 1 % of 0.01 is one drag count in CD.
SCALE_FLOOR = {"cl": 0.1, "cd": 0.01, "cm": 0.01}


def stationarity(
    series: list[float], window: int, *, floor: float = 1e-9
) -> dict[str, float] | None:
    """Over the final `window` samples: half-mean shift and standard
    deviation, both relative to max(|mean|, floor)."""
    tail = [v for v in series[-window:] if v == v]
    if len(tail) < 4:
        return None
    half = len(tail) // 2
    m1 = statistics.fmean(tail[:half])
    m2 = statistics.fmean(tail[half:])
    m = statistics.fmean(tail)
    sd = statistics.pstdev(tail)
    scale = max(abs(m), floor, 1e-9)
    return {"shift": abs(m2 - m1) / scale, "scatter": sd / scale, "mean": m, "n": len(tail)}


def verdict(
    residuals: dict[str, list[float]],
    coeffs: dict[str, list[float]],
    *,
    ended: bool,
    fatal: bool = False,
    cancelled: bool = False,
    orders_required: float = 3.0,
    window_pct: float = 20.0,
    min_window: int = 50,
    cl_tol: float = 0.005,
    cd_tol: float = 0.01,
    scatter_tol: float = 0.01,
) -> dict[str, Any]:
    n = max((len(v) for v in list(residuals.values()) + list(coeffs.values())), default=0)
    out: dict[str, Any] = {"iters_used": n, "notes": []}
    if fatal:
        out["state"] = "error"
        return out
    for name, series in coeffs.items():
        if any(v != v or v in (math.inf, -math.inf) for v in series):
            out["state"] = "diverged"
            out["notes"].append(f"{name} became non-finite")
            return out
    drops = {k: orders_dropped(v) for k, v in residuals.items()}
    drops = {k: v for k, v in drops.items() if v is not None}
    out["residual_drop_orders"] = round(min(drops.values()), 2) if drops else None
    # climbing residuals: the last value more than 2 orders above the minimum seen
    for name, series in residuals.items():
        finite = [v for v in series if v == v and v > 0]
        if len(finite) >= 10 and finite[-1] > 100.0 * min(finite):
            out["state"] = "diverged"
            out["notes"].append(f"{name} residual climbed back 2 orders")
            return out
    if cancelled:
        out["state"] = "cancelled"
        return out
    window = max(min_window, int(n * window_pct / 100.0))
    if n < min_window:
        out["state"] = "running" if not ended else "insufficient"
        return out
    stats = {k: stationarity(v, window, floor=SCALE_FLOOR.get(k, 0.01)) for k, v in coeffs.items()}
    stats = {k: v for k, v in stats.items() if v is not None}
    out["stationarity_pct"] = round(
        100.0 * max((s["shift"] for s in stats.values()), default=0.0), 3
    )
    out["scatter_pct"] = round(100.0 * max((s["scatter"] for s in stats.values()), default=0.0), 3)
    tol = {"cl": cl_tol, "cd": cd_tol}
    stationary = all(s["shift"] <= tol.get(k, cd_tol) for k, s in stats.items())
    quiet = all(s["scatter"] <= scatter_tol for k, s in stats.items())
    residual_ok = bool(drops) and min(drops.values()) >= orders_required
    if residual_ok and stationary and quiet:
        out["state"] = "converged"
    elif stationary and quiet:
        out["state"] = "stalled" if ended else "running"
        if ended:
            out["notes"].append(
                f"residuals dropped {out['residual_drop_orders']} orders "
                f"(target {orders_required}) while the coefficients sat still"
            )
    elif stationary and not quiet:
        out["state"] = "oscillating" if ended else "running"
    else:
        out["state"] = "insufficient" if ended else "running"
    return out


# ---------------------------------------------------------------------------
# The uncertainty label
# ---------------------------------------------------------------------------

CITE = (
    "AIAA Drag Prediction Workshop summaries (Vassberg et al., AIAA 2010-4547) and the "
    "High-Lift Prediction Workshop summaries: RANS is comparative, not absolute"
)

LABELS = {
    "comparative": (
        "RANS, attached flow, converged: trust deltas between similar cases on the same mesh "
        "to a few drag counts; absolute drag is +-1-3 % at best with 10-20 counts of scatter "
        "between competent setups"
    ),
    "indicative": (
        "lift slope, pressure distribution and trends are usable; drag is not absolute "
        "(no viscous drag from a panel or Euler method; RANS without a wall-spacing check)"
    ),
    "not-predictive": (
        "separated flow, buffet, CLmax or an unconverged run: RANS is not predictive here "
        "(HiLiftPW scatter of several tenths in CLmax); treat the number as a bound at most"
    ),
}


def uncertainty(
    *,
    fidelity: str,
    regime: str,
    aoa_deg: float,
    state: str,
    yplus_ok: bool | None = None,
) -> dict[str, str]:
    """`fidelity` is panel | euler | rans; `regime` the atmosphere.regime word."""
    a = abs(aoa_deg)
    if (
        state not in ("converged", "stalled")
        or a > 12.0
        or (regime == "transonic" and fidelity != "euler")
    ):
        trust = "not-predictive"
    elif fidelity in ("panel", "euler"):
        trust = "indicative" if a <= 10.0 else "not-predictive"
    elif fidelity == "rans":
        trust = (
            "comparative"
            if (yplus_ok is not False and a <= 10.0 and state == "converged")
            else "indicative"
        )
    else:
        trust = "indicative"
    return {"trust": trust, "label": LABELS[trust], "cite": CITE}


def compare(a: dict[str, float], b: dict[str, float]) -> dict[str, Any]:
    """Same-mesh deltas, in coefficient units and drag counts (1 count = 1e-4)."""
    out: dict[str, Any] = {}
    for key in ("cl", "cd", "cm"):
        if key in a and key in b:
            d = b[key] - a[key]
            out[f"d_{key}"] = round(d, 6)
            if key == "cd":
                out["d_cd_counts"] = round(d * 1e4, 2)
    return out
