"""A74 P5 probe 3: does cartesian2DMesh want an OPEN surface (a ribbon)?

The 3-D mesher takes the volume bounded by a CLOSED surface (doc 74 2.4).
Every closed variant tried so far dies with "There are no cells in the mesh!"
in under a second, before meshing starts - so the hypothesis is that the 2-D
mesher wants the opposite: the 2-D outline extruded, with NO caps in z, and it
supplies the single cell through the thickness itself. Prints, never asserts.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/src")
from tee.windtunnel import airfoil, foam, physics  # noqa: E402

WORK = Path(sys.argv[1])
WRAP = "/usr/bin/openfoam2606"
CHORD, FAR, SLAB = 1.0, 20.0, 0.1
ENV = {**os.environ, "OMP_NUM_THREADS": "1"}


def ribbon(loop, z0, z1, *, close=False):
    """A closed 2-D outline extruded into a wall band: two triangles per edge,
    and no caps. `close=True` adds the caps, which is what extrude_stl does."""
    tris = []
    n = len(loop)
    for i in range(n):
        (x0, y0), (x1, y1) = loop[i], loop[(i + 1) % n]
        a, b = (x0, y0, z0), (x1, y1, z0)
        c, d = (x1, y1, z1), (x0, y0, z1)
        tris.append((a, b, c))
        tris.append((a, c, d))
    return tris


def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def build(case: Path, *, caps_on_airfoil: bool, cell: float, body_cell: float):
    shutil.rmtree(case, ignore_errors=True)
    (case / "system").mkdir(parents=True, exist_ok=True)
    foam.write_mesh_system(case)
    tri = case / "constant" / "triSurface"
    tri.mkdir(parents=True, exist_ok=True)
    z0, z1 = -SLAB / 2, SLAB / 2
    far = ribbon(rect(-FAR, FAR, -FAR, FAR), z0, z1)
    physics.write_stl_ascii(tri / "farfield.stl", far, name="farfield")
    parts = ["farfield"]
    sec = [(p[0] * CHORD, p[1] * CHORD) for p in airfoil.naca4("0012", 80)]
    if caps_on_airfoil:
        airfoil.extrude_stl(tri / "airfoil.stl", airfoil.naca4("0012", 80), span=SLAB,
                            chord=CHORD, name="airfoil")
    else:
        physics.write_stl_ascii(tri / "airfoil.stl", ribbon(sec, z0, z1), name="airfoil")
    parts.append("airfoil")
    (tri / "domain.stl").write_text(
        "".join((tri / f"{n}.stl").read_text() for n in parts))
    t = foam.Tunnel3D(xmin=-FAR, xmax=FAR, ymin=-FAR, ymax=FAR, zmin=z0, zmax=z1,
                      base_cell=cell, body_name="airfoil",
                      body_bbox=((0.0, -0.06, z0), (CHORD, 0.06, z1)), layers=3)
    (case / "system" / "meshDict").write_text(
        foam.cfmesh_dict(t, surface_file="constant/triSurface/domain.stl",
                         body_cell=body_cell, layers=3))


def run(app, case, timeout=2400):
    t0 = time.time()
    res = subprocess.run([WRAP, app, "-case", str(case)], capture_output=True, text=True,
                         timeout=timeout, cwd=str(case), env=ENV)
    (case / f"log.{app}").write_text(res.stdout + res.stderr)
    return res.returncode, round(time.time() - t0, 1), res.stdout + res.stderr


TRIALS = [
    ("ribbon box + ribbon airfoil", False, 0.499, 0.0125),
    ("ribbon box + capped airfoil", True, 0.499, 0.0125),
]
for label, caps_foil, cell, body_cell in TRIALS:
    case = WORK / re.sub(r"[^a-z0-9]+", "-", label.lower())
    build(case, caps_on_airfoil=caps_foil, cell=cell, body_cell=body_cell)
    rc, wall, log = run("cartesian2DMesh", case)
    if rc != 0:
        why = [ln.strip() for ln in log.splitlines()
               if "no cells" in ln or "annot" in ln or "must" in ln.lower()]
        print(f"{label:30s} rc={rc} {wall:>5} s  {(why[0][:90] if why else 'see log')}")
        continue
    rc2, _w, text = run("checkMesh", case)
    d = foam.parse_checkmesh(text)
    b = (case / "constant" / "polyMesh" / "boundary").read_text()
    patches = re.findall(r"^\s*(\w+)\s*\n\s*\{\s*\n\s*type\s+(\w+);", b, re.M)
    print(f"{label:30s} rc=0 {wall:>5} s  cells {d.get('cells')}  skew {d.get('max_skew')}  "
          f"failed {len(d.get('failed') or [])}  patches {patches}", flush=True)
