"""A68 P0 row L5b: the QuickStart NACA 0012 Euler case (M 0.8, alpha 1.25) on TEE's own O-mesh."""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from tee.windtunnel import airfoil, mesh2d, su2

out = Path(sys.argv[1])
su2_bin = sys.argv[2]
n_surface = int(sys.argv[3]) if len(sys.argv) > 3 else 100
nj = int(sys.argv[4]) if len(sys.argv) > 4 else 60
out.mkdir(parents=True, exist_ok=True)

loop = airfoil.naca4("0012", n_surface)
# Euler: no boundary layer, so a first cell of ~2e-3 chord is plenty
mesh = mesh2d.omesh(loop, first_cell=2e-3, nj=nj, radius_c=50.0)
mesh2d.write_su2(out / "mesh.su2", mesh)
print(json.dumps({"ni": mesh.ni, "nj": mesh.nj, "cells": mesh.cells, "nodes": mesh.nodes, "growth": round(mesh.growth, 4),
                  "min_jacobian": mesh.min_jacobian(), "counts": mesh2d.read_su2_counts(out / "mesh.su2")}))
setup = su2.Su2Setup(mesh_file="mesh.su2", solver="EULER", mach=0.8, aoa_deg=1.25, iters=1500)
su2.write_cfg(out / "case.cfg", setup)
t = time.time()
res = subprocess.run(["/usr/bin/time", "-f", "TIME_WALL=%e TIME_RSS_KB=%M", su2_bin, "case.cfg"], cwd=out, capture_output=True, text=True)
wall = time.time() - t
(out / "log.SU2_CFD").write_text(res.stdout + res.stderr)
m = re.search(r"TIME_WALL=(\S+) TIME_RSS_KB=(\d+)", res.stderr)
scr = su2.parse_screen_log(res.stdout)
print("rc", res.returncode, "wall", round(wall, 2), "time/rss", m.groups() if m else None, "rows", len(scr["rows"]), "converged", scr["converged"], "max_iter", scr["max_iter"], "error", scr["error"])
if scr["rows"]:
    last = scr["rows"][-1]
    print("screen last:", {k: last.get(k) for k in ("Inner_Iter", "rms[Rho]", "CL", "CD")})
if (out / "history.csv").exists():
    h = su2.read_history(out / "history.csv")
    print("history columns:", h["columns"])
    if h["rows"]:
        r = h["rows"][-1]
        print("history last:", {k: round(v, 6) for k, v in r.items() if k in ("Inner_Iter", "cl", "cd", "cm", "rms[Rho]")})
print("outputs:", sorted(p.name for p in out.iterdir()))
print("log bytes/row", round(len(res.stdout) / max(len(scr["rows"]), 1)))
