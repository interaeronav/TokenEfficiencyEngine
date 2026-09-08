"""A74 P5 probe 5: solve on the cartesian 2-D mesh and compare to the O-mesh.

Law 3: a better mesh must show up in the answer. The lane's 2-D path is its
own structured O-mesh - body-fitted, graded, low-Re by design - and the
question is whether a cartesian 2-D mesh earns a place beside it.

Both arms are solved here rather than quoted: the O-mesh arm THROUGH THE LANE
(what a user gets) and the cartesian arm by hand, since the lane has no 2-D
cfMesh route yet. Prints, never asserts.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/tests")
sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/src")
from tee.windtunnel import airfoil, foam, physics  # noqa: E402

WORK = Path(sys.argv[1])
AOA = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
LAYERS = int(sys.argv[3]) if len(sys.argv) > 3 else 8
BODY_CELL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0125
TREATMENT = sys.argv[5] if len(sys.argv) > 5 else "wall_function"
WRAP = "/usr/bin/openfoam2606"
CHORD, FAR, SLAB = 1.0, 20.0, 0.1
V, RHO, MU = 30.0, 1.225, 1.81e-5
ITERS = 600
ENV = {**os.environ, "OMP_NUM_THREADS": "1"}


def ribbon(loop, z0, z1):
    tris = []
    for i in range(len(loop)):
        (x0, y0), (x1, y1) = loop[i], loop[(i + 1) % len(loop)]
        a, b, c, d = (x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)
        tris += [(a, b, c), (a, c, d)]
    return tris


def run(app, case, *args, timeout=3600):
    t0 = time.time()
    res = subprocess.run([WRAP, app, "-case", str(case), *args], capture_output=True,
                         text=True, timeout=timeout, cwd=str(case), env=ENV)
    (case / f"log.{app}").write_text(res.stdout + res.stderr)
    return res.returncode, round(time.time() - t0, 1), res.stdout + res.stderr


case = WORK / f"cart2d-a{AOA:g}-l{LAYERS}-c{BODY_CELL}-{TREATMENT}"
shutil.rmtree(case, ignore_errors=True)
(case / "system").mkdir(parents=True, exist_ok=True)
foam.write_mesh_system(case)
tri = case / "constant" / "triSurface"
tri.mkdir(parents=True, exist_ok=True)
z0, z1 = -SLAB / 2, SLAB / 2
physics.write_stl_ascii(tri / "farfield.stl",
                        ribbon([(-FAR, -FAR), (FAR, -FAR), (FAR, FAR), (-FAR, FAR)], z0, z1),
                        name="farfield")
airfoil.extrude_stl(tri / "airfoil.stl", airfoil.naca4("0012", 80), span=SLAB, chord=CHORD,
                    name="airfoil")
(tri / "domain.stl").write_text("".join((tri / f"{n}.stl").read_text()
                                        for n in ("farfield", "airfoil")))
t = foam.Tunnel3D(xmin=-FAR, xmax=FAR, ymin=-FAR, ymax=FAR, zmin=z0, zmax=z1,
                  base_cell=0.499, body_name="airfoil",
                  body_bbox=((0.0, -0.06, z0), (CHORD, 0.06, z1)), layers=LAYERS)
(case / "system" / "meshDict").write_text(
    foam.cfmesh_dict(t, surface_file="constant/triSurface/domain.stl",
                     body_cell=BODY_CELL, layers=LAYERS))
rc, mesh_wall, log = run("cartesian2DMesh", case)
print(f"cartesian2DMesh rc={rc} in {mesh_wall} s")
if rc != 0:
    print("\n".join(log.splitlines()[-6:]))
    raise SystemExit(1)

# cfMesh writes EVERY patch `empty`; the caller owns the types (A74 P5)
b = case / "constant" / "polyMesh" / "boundary"
text = b.read_text()
for name, want in (("airfoil", "wall"), ("farfield", "patch")):
    text = re.sub(rf"(^\s*{name}\s*\n\s*\{{\s*\n\s*type\s+)\w+;", rf"\g<1>{want};",
                  text, flags=re.M)
b.write_text(text)
rc, _w, chk = run("checkMesh", case)
d = foam.parse_checkmesh(chk)
print(f"checkMesh: cells {d.get('cells')} skew {d.get('max_skew')} "
      f"aspect {d.get('max_aspect')} failed {d.get('failed') or 'NONE'}")

axes = physics.wind_axes(AOA)
setup = foam.FoamSetup(
    U_inf=tuple(V * c for c in axes["U"]),
    nu=MU / RHO,
    turbulence="kOmegaSST",
    wall_treatment=TREATMENT,
    end_time=ITERS,
    write_interval=ITERS,
    Aref=CHORD * SLAB,                # a 2-D slab's Aref is chord x thickness (A72)
    lRef=CHORD,
    CofR=(CHORD * 0.25, 0.0, 0.0),
    liftDir=axes["lift"],
    dragDir=axes["drag"],
    pitchAxis=(0.0, 0.0, 1.0),
    wall_patches=("airfoil",),
    freestream_patches=("farfield",),
    empty_patches=("bottomEmptyFaces", "topEmptyFaces"),
)
foam.write_case(case, setup)
rc, solve_wall, slog = run("simpleFoam", case)
print(f"simpleFoam rc={rc} in {solve_wall} s")
coeff = next(iter(sorted(case.glob("postProcessing/forceCoeffs*/*/coefficient*.dat"))), None)
if coeff is None:
    print("no coefficient file; last lines:")
    print("\n".join(slog.splitlines()[-8:]))
    raise SystemExit(1)
rows = foam.read_coefficients(coeff) if hasattr(foam, "read_coefficients") else None
last = [ln for ln in coeff.read_text().splitlines() if ln and not ln.startswith("#")][-1]
head = [ln for ln in coeff.read_text().splitlines() if ln.startswith("#")][-1]
cols = head.lstrip("#").split()
vals = dict(zip(cols, last.split()))
print(f"\nCARTESIAN 2-D  cells {d.get('cells')}  mesh {mesh_wall} s  solve {solve_wall} s")
print(f"  iteration {vals.get('Time')}  Cl {vals.get('Cl')}  Cd {vals.get('Cd')}  "
      f"Cm {vals.get('CmPitch')}")
