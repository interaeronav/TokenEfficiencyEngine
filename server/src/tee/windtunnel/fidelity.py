"""The fidelity ladder: the cheapest capable engine first, and the router
says why (TEE's own routing pillar applied to solvers).

`panel`  - VSPAERO vortex lattice: seconds; lift slope, induced drag, span
           loading of an attached lifting surface.
`euler`  - SU2 Euler: minutes; compressible, shocks, wave drag; no viscous drag.
`rans`   - OpenFOAM simpleFoam kOmegaSST (incompressible) or SU2 RANS
           (compressible): tens of minutes to hours; friction drag, separation
           onset - and the DPW caveats verdict.uncertainty carries.

The cost constants are MEASURED (2026-09-06, this container, one core) and
dated; they decide only whether to ask before a run, and every run writes
its real wall time back so the next estimate for that case is its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# seconds per cell (node) per iteration per core, measured 2026-09-06
K_ENGINE = {
    "openfoam": 2.36e-6,  # simpleFoam kOmegaSST, 12,800-cell 2-D O-mesh, v2606: 189 it in 5.7 s
    "su2": 6.1e-6,  # SU2_CFD 8.4.0 Euler, 12,000-cell O-mesh: 1,329 it in 97.8 s
    "vspaero": 0.0,  # a sweep is seconds; see PANEL_SWEEP_S
}
PANEL_SWEEP_S = 6.0  # measured 5.3 s for a 33x20 wing, four alphas, four threads
BYTES_PER_CELL = {
    "openfoam": 3_000,
    "su2": 3_000,
}  # RSS 80 MB / 12.8k cells, 67 MB / 12.2k nodes, minus the ~50 MB baseline
BASE_RSS_GB = 0.1
MEASURED_ON = "2026-09-06 Linux x86_64 container, 1 core"

CONFIRM_ABOVE_S = 300.0
CONFIRM_ABOVE_GB = 8.0
CONFIRM_ABOVE_CELLS = 2_000_000


@dataclass(frozen=True)
class Choice:
    engine: str  # openfoam | su2 | vspaero
    fidelity: str  # panel | euler | rans
    reason: str


def choose(
    geometry_kind: str,
    *,
    mach: float,
    need_viscous: bool,
    aoa_max_deg: float,
    fidelity: str = "auto",
    available: dict[str, bool] | None = None,
) -> Choice:
    """`geometry_kind` is airfoil2d | wing3d | body3d | adopted."""
    av = available or {"openfoam": True, "su2": True, "vspaero": True}
    if fidelity not in ("auto", "panel", "euler", "rans"):
        raise ValueError(f"fidelity '{fidelity}' is not auto/panel/euler/rans")
    if geometry_kind == "adopted":
        return Choice("adopted", "rans", "adopted: the case decides its own solver")
    if fidelity == "auto":
        if geometry_kind == "airfoil2d":
            fidelity = "rans" if need_viscous or mach < 0.3 else "euler"
        elif geometry_kind == "wing3d":
            fidelity = (
                "panel" if (mach <= 0.6 and aoa_max_deg <= 10.0 and not need_viscous) else "rans"
            )
        else:
            fidelity = "rans"
    if fidelity == "panel":
        if geometry_kind == "body3d":
            raise ValueError("a bluff body has no panel answer; use rans")
        if av.get("vspaero"):
            return Choice(
                "vspaero",
                "panel",
                "attached lifting surface: VLM lift slope, induced drag, span load in seconds",
            )
        return Choice(
            "openfoam",
            "rans",
            "panel asked but OpenVSP is absent: RANS on the exported surface instead",
        )
    if fidelity == "euler":
        if geometry_kind != "airfoil2d":
            raise ValueError("euler is a 2-D section option in v1 (3-D SU2 meshing needs gmsh)")
        if av.get("su2"):
            return Choice(
                "su2",
                "euler",
                "compressible inviscid: wave drag and lift in minutes, no viscous drag",
            )
        raise ValueError("euler needs SU2, which is not installed")
    # rans
    if geometry_kind == "airfoil2d":
        if mach >= 0.3 and av.get("su2"):
            return Choice("su2", "rans", "2-D viscous, compressible: SU2 RANS on the O-mesh")
        if av.get("openfoam"):
            return Choice(
                "openfoam",
                "rans",
                "2-D viscous, incompressible: simpleFoam kOmegaSST on the O-mesh, minutes",
            )
        if av.get("su2"):
            return Choice("su2", "rans", "OpenFOAM absent: SU2 RANS on the O-mesh")
        raise ValueError("rans needs OpenFOAM or SU2, neither is installed")
    if av.get("openfoam"):
        why = (
            "bluff body: no panel or Euler answer exists"
            if geometry_kind == "body3d"
            else "viscous/separated/transonic lifting surface: RANS on the STL"
        )
        return Choice("openfoam", "rans", why + " (snappyHexMesh + simpleFoam, tens of minutes)")
    raise ValueError("a 3-D RANS case needs OpenFOAM, which is not installed")


def estimate(
    engine: str, *, cells: int, iters: int, cores: int = 1, sweep_points: int = 1
) -> dict[str, Any]:
    if engine == "vspaero":
        wall = PANEL_SWEEP_S * max(1.0, sweep_points / 4.0)
        return {"wall_s": round(wall, 1), "footprint_gb": 0.2, "measured_on": MEASURED_ON}
    k = K_ENGINE.get(engine, K_ENGINE["openfoam"])
    wall = cells * iters * k / max(cores, 1) * sweep_points
    gb = BASE_RSS_GB + cells * BYTES_PER_CELL.get(engine, 3_000) / 1e9
    return {"wall_s": round(wall, 1), "footprint_gb": round(gb, 3), "measured_on": MEASURED_ON}


def needs_confirmation(
    est: dict[str, Any], cells: int, *, confirm_above_s: float = CONFIRM_ABOVE_S
) -> str | None:
    if est["wall_s"] > confirm_above_s:
        return f"estimated {est['wall_s']:.0f} s of solver time (> {confirm_above_s:.0f} s)"
    if est["footprint_gb"] > CONFIRM_ABOVE_GB:
        return f"estimated {est['footprint_gb']:.1f} GB (> {CONFIRM_ABOVE_GB:.0f} GB)"
    if cells > CONFIRM_ABOVE_CELLS:
        return f"{cells:,} cells (> {CONFIRM_ABOVE_CELLS:,})"
    return None
