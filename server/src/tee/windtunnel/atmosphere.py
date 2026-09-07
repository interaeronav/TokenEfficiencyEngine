"""The standard atmosphere and the three numbers every case needs.

International Standard Atmosphere / U.S. Standard Atmosphere 1976 (identical
below 32 km): a linear troposphere to 11 km, an isothermal layer to 20 km.
Constants are the standard's own (ISO 2533:1975 §2; NASA-TM-X-74335 table 2):
T0 288.15 K, p0 101 325 Pa, lapse 6.5 K/km, R 287.05287 J/(kg K),
g0 9.80665 m/s², gamma 1.4. Sutherland's viscosity law uses beta 1.458e-6 and
S 110.4 K (US76 eq. 51). The tests pin the tabulated rows the standard
publishes, so a wrong constant here fails a test rather than a case.

Stdlib only, on purpose: `wt_conditions` must answer with nothing installed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

T0_K = 288.15
P0_PA = 101_325.0
LAPSE_K_PER_M = 0.0065
R_AIR = 287.05287
G0 = 9.80665
GAMMA = 1.4
T11_K = 216.65
H11_M = 11_000.0
H_MAX_M = 20_000.0
SUTHERLAND_BETA = 1.458e-6
SUTHERLAND_S = 110.4

P11_PA = P0_PA * (T11_K / T0_K) ** (G0 / (LAPSE_K_PER_M * R_AIR))


@dataclass(frozen=True)
class Air:
    alt_m: float
    T_K: float
    p_Pa: float
    rho: float
    mu: float
    a: float


def mu_sutherland(T_K: float) -> float:
    """Dynamic viscosity of air, Pa s (US76 eq. 51; White, Viscous Fluid Flow §1-3)."""
    return SUTHERLAND_BETA * T_K**1.5 / (T_K + SUTHERLAND_S)


def isa(alt_m: float = 0.0, dT_K: float = 0.0) -> Air:
    """ISA state at geopotential altitude `alt_m` with a temperature offset.

    The offset shifts T and rho the way a hot or cold day does (ISA+dT); the
    pressure profile is the standard one (ICAO Doc 7488 convention).
    """
    if not (0.0 <= alt_m <= H_MAX_M):
        raise ValueError(
            f"alt_m {alt_m} outside 0..{H_MAX_M:.0f} m (the two layers this lane knows)"
        )
    if alt_m <= H11_M:
        T_std = T0_K - LAPSE_K_PER_M * alt_m
        p = P0_PA * (T_std / T0_K) ** (G0 / (LAPSE_K_PER_M * R_AIR))
    else:
        T_std = T11_K
        p = P11_PA * math.exp(-G0 * (alt_m - H11_M) / (R_AIR * T11_K))
    T = T_std + dT_K
    rho = p / (R_AIR * T)
    return Air(
        alt_m=alt_m, T_K=T, p_Pa=p, rho=rho, mu=mu_sutherland(T), a=math.sqrt(GAMMA * R_AIR * T)
    )


def regime(mach: float) -> str:
    """The word the fidelity router keys on (Anderson, Fundamentals of Aerodynamics §1.10)."""
    if mach < 0.3:
        return "incompressible"
    if mach < 0.8:
        return "subsonic"
    if mach < 1.2:
        return "transonic"
    return "supersonic"


def conditions(
    *,
    L_m: float,
    V_mps: float | None = None,
    mach: float | None = None,
    alt_m: float = 0.0,
    dT_K: float = 0.0,
) -> dict[str, float | str]:
    """Re, Mach and q for a speed OR a Mach number at an altitude.

    Re = rho V L / mu, M = V / a, q = 1/2 rho V^2 (Anderson §1.4-1.5).
    Exactly one of `V_mps` / `mach` is given; the other is derived.
    """
    if (V_mps is None) == (mach is None):
        raise ValueError("give exactly one of V_mps or mach")
    if L_m <= 0:
        raise ValueError("L_m must be positive (the reference length Re is built on)")
    air = isa(alt_m, dT_K)
    V = float(V_mps) if V_mps is not None else float(mach) * air.a
    if V <= 0:
        raise ValueError("speed must be positive")
    M = V / air.a
    return {
        "alt_m": alt_m,
        "dT_K": dT_K,
        "T_K": round(air.T_K, 3),
        "p_Pa": round(air.p_Pa, 1),
        "rho": round(air.rho, 5),
        "mu": air.mu,
        "a": round(air.a, 3),
        "V": round(V, 4),
        "mach": round(M, 5),
        "q_Pa": round(0.5 * air.rho * V * V, 3),
        "Re": air.rho * V * L_m / air.mu,
        "L_m": L_m,
        "regime": regime(M),
    }
