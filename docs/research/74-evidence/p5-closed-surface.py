"""A74 P5 probe 2: which (maxCellSize, slab) does cartesian2DMesh accept?

"There are no cells in the mesh!" names two possible causes. Rather than pick
one from the wording, vary both and read the answer off. Prints, never asserts.
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
CHORD, FAR = 1.0, 20.0
ENV = {**os.environ, "OMP_NUM_THREADS": "1"}


def normal(t):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
    m = sum(c * c for c in n) ** 0.5 or 1.0
    return tuple(c / m for c in n)


def build(case: Path, slab: float, cell: float, body_cell: float):
    shutil.rmtree(case, ignore_errors=True)
    (case / "system").mkdir(parents=True, exist_ok=True)
    foam.write_mesh_system(case)
    tri = case / "constant" / "triSurface"
    tri.mkdir(parents=True, exist_ok=True)
    faces = physics.box_faces(-FAR, FAR, -FAR, FAR, -slab / 2, slab / 2)
    fb, ff = [], []
    for tris in faces.values():
        for t in tris:
            (fb if abs(abs(normal(t)[2]) - 1.0) < 1e-6 else ff).append(t)
    physics.write_stl_ascii(tri / "frontAndBack.stl", fb, name="frontAndBack")
    physics.write_stl_ascii(tri / "farfield.stl", ff, name="farfield")
    airfoil.extrude_stl(tri / "airfoil.stl", airfoil.naca4("0012", 80), span=slab,
                        chord=CHORD, name="airfoil")
    (tri / "domain.stl").write_text(
        "".join((tri / f"{n}.stl").read_text() for n in ("farfield", "frontAndBack", "airfoil"))
    )
    t = foam.Tunnel3D(xmin=-FAR, xmax=FAR, ymin=-FAR, ymax=FAR, zmin=-slab / 2, zmax=slab / 2,
                      base_cell=cell, body_name="airfoil",
                      body_bbox=((0.0, -0.06, -slab / 2), (CHORD, 0.06, slab / 2)), layers=3)
    (case / "system" / "meshDict").write_text(
        foam.cfmesh_dict(t, surface_file="constant/triSurface/domain.stl",
                         body_cell=body_cell, layers=3))


def run(app, case, timeout=2400):
    t0 = time.time()
    res = subprocess.run([WRAP, app, "-case", str(case)], capture_output=True, text=True,
                         timeout=timeout, cwd=str(case), env=ENV)
    (case / f"log.{app}").write_text(res.stdout + res.stderr)
    return res.returncode, round(time.time() - t0, 1), res.stdout + res.stderr


# (label, slab, maxCellSize, bodyCell)
TRIALS = [
    ("cell 1.0 slab 0.1   (the first try)", 0.1, 1.0, 0.0125),
    ("cell 0.999 slab 0.1  (not a divisor)", 0.1, 0.999, 0.0125),
    ("cell 0.1  slab 0.1   (cell = slab)", 0.1, 0.1, 0.0125),
    ("cell 0.999 slab 1.0  (slab = cell)", 1.0, 0.999, 0.0125),
]
for label, slab, cell, body_cell in TRIALS:
    case = WORK / re.sub(r"[^a-z0-9]+", "-", label.lower())
    build(case, slab, cell, body_cell)
    rc, wall, log = run("cartesian2DMesh", case)
    if rc != 0:
        why = [ln for ln in log.splitlines() if "no cells" in ln or "FATAL" in ln]
        print(f"{label:38s} rc={rc} in {wall:>5} s   {(why[0][:70] if why else '')}")
        continue
    rc2, wall2, text = run("checkMesh", case)
    d = foam.parse_checkmesh(text)
    b = (case / "constant" / "polyMesh" / "boundary").read_text()
    patches = re.findall(r"^\s*(\w+)\s*\n\s*\{\s*\n\s*type\s+(\w+);", b, re.M)
    print(f"{label:38s} rc=0 in {wall:>5} s  cells {d.get('cells'):>7}  "
          f"skew {d.get('max_skew')}  failed {len(d.get('failed') or [])}  "
          f"patches {patches}", flush=True)
