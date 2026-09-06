"""A72 P0 row L2: TEE-written NACA 0012 O-mesh case, kOmegaSST, on apt OpenFOAM v1912.

Runs: checkMesh, simpleFoam (timed), then reads the coefficient file and the log
through the lane's own readers. Every number printed goes into PROGRESS.
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from tee.windtunnel import airfoil, engines, foam, mesh2d, physics
from tee.windtunnel.atmosphere import conditions

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("l2_case")
V = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
aoa = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
nj = int(sys.argv[4]) if len(sys.argv) > 4 else 80
n_surface = int(sys.argv[5]) if len(sys.argv) > 5 else 80
end_time = int(sys.argv[6]) if len(sys.argv) > 6 else 1500
out.mkdir(parents=True, exist_ok=True)

cond = conditions(L_m=1.0, V_mps=V)
nu = cond["mu"] / cond["rho"]
yplus = physics.first_cell_height(y_plus=1.0, rho=cond["rho"], V=V, L=1.0, mu=cond["mu"], cell_centred=True)
loop = airfoil.naca4("0012", n_surface)
t0 = time.time()
mesh = mesh2d.omesh(loop, first_cell=yplus["first_cell_m"], nj=nj, radius_c=50.0)
counts = mesh2d.write_polymesh(out, mesh)
t_mesh = time.time() - t0
axes = physics.wind_axes(aoa)
setup = foam.FoamSetup(
    U_inf=tuple(V * c for c in axes["U"]),
    nu=nu,
    turbulence="kOmegaSST",
    wall_treatment="low_re",
    end_time=end_time,
    write_interval=end_time,
    Aref=1.0 * counts["thickness"],  # 2-D slab: chord x thickness
    lRef=1.0,
    CofR=(0.25, 0.0, 0.0),
    liftDir=axes["lift"],
    dragDir=axes["drag"],
)
files = foam.write_case(out, setup)
print(json.dumps({
    "Re": round(cond["Re"]), "mach": cond["mach"], "first_cell_m": yplus["first_cell_m"],
    "mesh": {"ni": mesh.ni, "nj": mesh.nj, "cells": mesh.cells, "growth": round(mesh.growth, 4),
              "min_jacobian": mesh.min_jacobian(), "first_layer": mesh.first_layer_heights(), "notes": mesh.notes},
    "polymesh": counts, "mesh_write_s": round(t_mesh, 2), "files": files,
}, indent=1))

inst = engines.find_openfoam({})
print("route:", inst.to_dict())


def run(app, *args, log=None):
    argv = inst.argv(app, "-case", str(out), *args)
    t = time.time()
    res = subprocess.run(["/usr/bin/time", "-f", "TIME_WALL=%e TIME_RSS_KB=%M", *argv], capture_output=True, text=True)
    wall = time.time() - t
    text = res.stdout + res.stderr
    if log:
        (out / log).write_text(text)
    m = re.search(r"TIME_WALL=(\S+) TIME_RSS_KB=(\d+)", res.stderr)
    return res.returncode, wall, (float(m.group(1)), int(m.group(2))) if m else None, text


rc, wall, tm, text = run("checkMesh", log="log.checkMesh")
cm = foam.parse_checkmesh(text)
print("checkMesh:", rc, round(wall, 2), tm, json.dumps(cm))
if rc != 0:
    print(text[-3000:])
    sys.exit(1)

rc, wall, tm, text = run("simpleFoam", log="log.simpleFoam")
log = foam.parse_log(text)
n = len(log["times"])
print("simpleFoam:", "rc", rc, "wall", round(wall, 2), "time/rss", tm, "iterations", n, "ended", log["ended"], "fatal", log["fatal"], "bounded", log["bounded"])
if rc != 0 or log["fatal"]:
    print("\n".join(foam.last_error_lines(text, 6)))
    sys.exit(1)
for k, v in log["residuals"].items():
    print(f"  residual {k}: first {v[0]:.3e} last {v[-1]:.3e}")
files = foam.find_coefficient_files(out)
print("coefficient files:", [str(p.relative_to(out)) for p in files])
for p in files:
    head = [ln for ln in p.read_text().splitlines()[:12] if ln.startswith("#")]
    print("  header lines:", head)
    data = foam.read_coefficients(p)
    rows = data["rows"]
    print("  columns:", data["columns"], "rows:", len(rows))
    if rows:
        last = rows[-1]
        print("  last:", {k: round(v, 5) for k, v in last.items() if k in ("Time", "cl", "cd", "cm")})
        tail = rows[-max(1, n // 5):]
        cls = [r["cl"] for r in tail if "cl" in r]
        cds = [r["cd"] for r in tail if "cd" in r]
        if cls:
            print("  window mean cl", round(sum(cls) / len(cls), 5), "cd", round(sum(cds) / len(cds), 5),
                  "cl spread", round(max(cls) - min(cls), 6))
print("log bytes", len(text), "bytes/iteration", round(len(text) / max(n, 1)))
print("cell-iterations", mesh.cells * n, "us per cell-iteration", round(1e6 * tm[0] / (mesh.cells * n), 3) if tm else None)
