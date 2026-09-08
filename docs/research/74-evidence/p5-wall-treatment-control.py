"""A74 P5, the control: the SAME O-mesh solved with WALL FUNCTIONS.

The cartesian 2-D arm gave Cd 0.0207 where the O-mesh gave 0.0109 - but the
two differ in TWO ways at once, the mesh and the near-wall treatment (the
lane's 2-D path is low-Re by design; a cartesian mesh's near-wall cell only
supports wall functions). Change one variable: the O-mesh, wall functions.
If Cd moves to ~0.02 the difference is the treatment, not the mesher.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/src")
from tee.windtunnel import foam, physics  # noqa: E402

ENGINE = Path(sys.argv[1])          # the O-mesh engine dir
DST = Path(sys.argv[2])
AOA, V, RHO, MU, CHORD = 4.0, 30.0, 1.225, 1.81e-5, 1.0
WRAP = "/usr/bin/openfoam2606"
ENV = {**os.environ, "OMP_NUM_THREADS": "1"}

shutil.rmtree(DST, ignore_errors=True)
(DST / "constant").mkdir(parents=True, exist_ok=True)
shutil.copytree(ENGINE / "constant" / "polyMesh", DST / "constant" / "polyMesh")
# READ off the case record, not assumed: the lane's O-mesh writes a slab
# 0.1 m thick and Aref = Sref x thickness (A72's 2-D rule). Guessing 1.0
# made every coefficient exactly 10x too small on the first run.
thickness = 0.1
axes = physics.wind_axes(AOA)
for treatment in ("low_re", "wall_function"):
    case = DST.parent / f"{DST.name}-{treatment}"
    shutil.rmtree(case, ignore_errors=True)
    shutil.copytree(DST, case)
    setup = foam.FoamSetup(
        U_inf=tuple(V * c for c in axes["U"]),
        nu=MU / RHO,
        turbulence="kOmegaSST",
        wall_treatment=treatment,
        end_time=600,
        write_interval=600,
        Aref=CHORD * thickness,
        lRef=CHORD,
        CofR=(CHORD * 0.25, 0.0, 0.0),
        liftDir=axes["lift"],
        dragDir=axes["drag"],
        pitchAxis=(0.0, 0.0, 1.0),
        wall_patches=("airfoil",),
        freestream_patches=("farfield",),
        empty_patches=("frontAndBack",),
    )
    foam.write_case(case, setup)
    t0 = time.time()
    res = subprocess.run([WRAP, "simpleFoam", "-case", str(case)], capture_output=True,
                         text=True, timeout=3600, cwd=str(case), env=ENV)
    (case / "log.simpleFoam").write_text(res.stdout + res.stderr)
    wall = round(time.time() - t0, 1)
    coeff = next(iter(sorted(case.glob("postProcessing/forceCoeffs*/*/coefficient*.dat"))), None)
    if res.returncode != 0 or coeff is None:
        print(f"{treatment:14s} rc={res.returncode}: "
              f"{' | '.join(res.stdout.splitlines()[-3:])[:160]}")
        continue
    lines = [ln for ln in coeff.read_text().splitlines() if ln.strip()]
    head = [ln for ln in lines if ln.startswith("#")][-1].lstrip("#").split()
    vals = dict(zip(head, [ln for ln in lines if not ln.startswith("#")][-1].split()))
    print(f"{treatment:14s} iter {vals.get('Time'):>5}  Cl {float(vals['Cl']):.6f}  "
          f"Cd {float(vals['Cd']):.6f}  Cm {float(vals.get('CmPitch', 0)):.6f}  {wall} s",
          flush=True)
