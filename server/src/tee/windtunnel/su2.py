"""SU2 at arm's length: the `.cfg` TEE writes, the files TEE reads.

SU2 is LGPL-2.1 and is only ever a subprocess (`SU2_CFD`); the Python
wrapper `pysu2` exists only in source builds and is never imported. The
configuration keys are the ones the QuickStart `inv_NACA0012.cfg` uses
(verified 2026-09-06, SU2 8.4.0) plus the RANS keys the user guide names;
two facts were MEASURED rather than assumed: `history.csv` carries only
residual columns unless `HISTORY_OUTPUT` asks for `AERO_COEFF`, and the
screen table's `|`-delimited rows name their columns in a header row that
this reader keys on, never a column index.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GENERATED_BY = "generated-by: tee.windtunnel.su2"


@dataclass
class Su2Setup:
    mesh_file: str
    solver: str = "EULER"  # EULER | RANS | NAVIER_STOKES | INC_RANS
    mach: float = 0.8
    aoa_deg: float = 1.25
    reynolds: float | None = None  # RANS only; length = REF_LENGTH
    turbulence: str = "SA"  # SA | SST (RANS)
    freestream_T_K: float = 288.15
    freestream_p_Pa: float = 101325.0
    ref_length: float = 1.0
    ref_area: float = 1.0
    ref_origin: tuple[float, float, float] = (0.25, 0.0, 0.0)
    wall_marker: str = "airfoil"
    far_marker: str = "farfield"
    iters: int = 2000
    conv_field: str = "RMS_DENSITY"
    conv_residual_minval: float = -8.0
    cfl: float = 4.0
    restart: bool = False
    output_wrt_freq: int = 250


def write_cfg(path: str | Path, s: Su2Setup) -> list[str]:
    viscous = s.solver in ("RANS", "NAVIER_STOKES", "INC_RANS")
    wall_key = "MARKER_HEATFLUX" if viscous else "MARKER_EULER"
    lines = [
        f"% {GENERATED_BY}",
        f"SOLVER= {s.solver}",
        "MATH_PROBLEM= DIRECT",
        f"RESTART_SOL= {'YES' if s.restart else 'NO'}",
        f"MACH_NUMBER= {s.mach:.6g}",
        f"AOA= {s.aoa_deg:.6g}",
        f"FREESTREAM_PRESSURE= {s.freestream_p_Pa:.6g}",
        f"FREESTREAM_TEMPERATURE= {s.freestream_T_K:.6g}",
    ]
    if viscous:
        lines += [
            f"KIND_TURB_MODEL= {s.turbulence}",
            f"REYNOLDS_NUMBER= {s.reynolds or 1e6:.6g}",
            f"REYNOLDS_LENGTH= {s.ref_length:.6g}",
        ]
        if s.turbulence == "SST":
            lines.append("SST_OPTIONS= V2003m")
    lines += [
        f"REF_ORIGIN_MOMENT_X= {s.ref_origin[0]:.6g}",
        f"REF_ORIGIN_MOMENT_Y= {s.ref_origin[1]:.6g}",
        f"REF_ORIGIN_MOMENT_Z= {s.ref_origin[2]:.6g}",
        f"REF_LENGTH= {s.ref_length:.6g}",
        f"REF_AREA= {s.ref_area:.6g}",
        "REF_DIMENSIONALIZATION= DIMENSIONAL",
        f"{wall_key}= ( {s.wall_marker}, 0.0 )" if viscous else f"{wall_key}= ( {s.wall_marker} )",
        f"MARKER_FAR= ( {s.far_marker} )",
        f"MARKER_PLOTTING= ( {s.wall_marker} )",
        f"MARKER_MONITORING= ( {s.wall_marker} )",
        "NUM_METHOD_GRAD= WEIGHTED_LEAST_SQUARES",
        f"CFL_NUMBER= {s.cfl:.6g}",
        "CFL_ADAPT= NO",
        f"ITER= {s.iters}",
        "LINEAR_SOLVER= FGMRES",
        "LINEAR_SOLVER_PREC= ILU",
        "LINEAR_SOLVER_ERROR= 1E-6",
        "LINEAR_SOLVER_ITER= 10",
        "MGLEVEL= 3",
        "MGCYCLE= W_CYCLE",
        "CONV_NUM_METHOD_FLOW= JST",
        "JST_SENSOR_COEFF= ( 0.5, 0.02 )",
        "TIME_DISCRE_FLOW= EULER_IMPLICIT",
    ]
    if viscous:
        lines += [
            "CONV_NUM_METHOD_TURB= SCALAR_UPWIND",
            "TIME_DISCRE_TURB= EULER_IMPLICIT",
            "CFL_REDUCTION_TURB= 1.0",
        ]
    lines += [
        f"CONV_FIELD= {s.conv_field}",
        f"CONV_RESIDUAL_MINVAL= {s.conv_residual_minval:.6g}",
        "CONV_STARTITER= 10",
        "CONV_CAUCHY_ELEMS= 100",
        "CONV_CAUCHY_EPS= 1E-6",
        f"MESH_FILENAME= {s.mesh_file}",
        "MESH_FORMAT= SU2",
        "SOLUTION_FILENAME= solution_flow.dat",
        "TABULAR_FORMAT= CSV",
        "CONV_FILENAME= history",
        "RESTART_FILENAME= restart_flow.dat",
        "VOLUME_FILENAME= flow",
        "SURFACE_FILENAME= surface_flow",
        f"OUTPUT_WRT_FREQ= {s.output_wrt_freq}",
        "SCREEN_OUTPUT= (INNER_ITER, WALL_TIME, RMS_RES, LIFT, DRAG)",
        "HISTORY_OUTPUT= (ITER, WALL_TIME, RMS_RES, AERO_COEFF)",
        "OUTPUT_FILES= (RESTART, PARAVIEW, SURFACE_CSV)",
    ]
    Path(path).write_text("\n".join(lines) + "\n")
    return lines


def read_cfg(path: str | Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        s = line.split("%")[0].strip()
        if "=" in s:
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip()
    return out


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

_COEFF_KEYS = {"cl": ("CL", '"CL"'), "cd": ("CD", '"CD"'), "cm": ("CMz", '"CMz"', "CMy", '"CMy"')}


def read_history(path: str | Path) -> dict[str, Any]:
    """`history.csv`: the header names the columns (quoted, padded)."""
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{Path(path).name}: empty history file")
        cols = [h.strip().strip('"') for h in header]
        rows: list[dict[str, float]] = []
        for raw in reader:
            if len(raw) != len(cols):
                continue
            try:
                row = {c: float(v) for c, v in zip(cols, raw, strict=True)}
            except ValueError:
                continue
            for canon, names in _COEFF_KEYS.items():
                for n in names:
                    if n.strip('"') in row:
                        row[canon] = row[n.strip('"')]
                        break
            rows.append(row)
    return {"columns": cols, "rows": rows, "source": str(path)}


_RE_HEADER = re.compile(r"^\|\s*Inner_Iter\s*\|")
_RE_ROW = re.compile(r"^\|\s*(\d+)\s*\|")


def parse_screen_log(text: str) -> dict[str, Any]:
    """The `|`-table SU2 prints: header row -> column names; every data row
    keyed by them. Also whether it converged, and any error banner."""
    cols: list[str] = []
    rows: list[dict[str, float]] = []
    converged = "All convergence criteria satisfied" in text
    max_iter = "Maximum number of iterations reached" in text
    error = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _RE_HEADER.match(line):
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            continue
        if cols and _RE_ROW.match(line):
            vals = [v.strip() for v in line.strip().strip("|").split("|")]
            if len(vals) == len(cols):
                try:
                    row = {c: float(v) for c, v in zip(cols, vals, strict=True)}
                except ValueError:
                    continue
                if "CL" in row:
                    row["cl"] = row["CL"]
                if "CD" in row:
                    row["cd"] = row["CD"]
                rows.append(row)
        if "Error in" in line or "Error Exit" in line:
            error = " ".join(x.strip() for x in lines[i : i + 4] if x.strip())[:300]
    return {
        "columns": cols,
        "rows": rows,
        "converged": converged,
        "max_iter": max_iter,
        "error": error,
    }


def read_surface_csv(path: str | Path, limit: int | None = None) -> dict[str, Any]:
    """`surface_flow.csv`: PointID, x, y, then the flow variables SU2 chose
    (Density, Momentum_x, ..., Pressure, Pressure_Coefficient when present)."""
    with open(path, newline="") as fh:
        reader = csv.reader(fh)
        header = [h.strip().strip('"') for h in next(reader)]
        rows = []
        for raw in reader:
            try:
                rows.append({c: float(v) for c, v in zip(header, raw, strict=True)})
            except ValueError:
                continue
            if limit and len(rows) >= limit:
                break
    return {"columns": header, "rows": rows}


def mesh_markers(path: str | Path) -> list[str]:
    tags = []
    with open(path) as fh:
        for line in fh:
            if line.startswith("MARKER_TAG="):
                tags.append(line.split("=", 1)[1].strip())
    return tags
