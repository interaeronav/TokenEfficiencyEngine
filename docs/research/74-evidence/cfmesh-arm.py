"""The cfMesh arm: same geometry, same domain, boundary layers requested."""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/tests")
from tee.windtunnel import airfoil, foam  # noqa: E402
from tee.windtunnel.physics import write_stl_ascii  # noqa: E402

WORK = Path(sys.argv[1])
CASE = WORK / "cfmesh_case2"
(CASE / "system").mkdir(parents=True, exist_ok=True)
(CASE / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
CHORD, SPAN = 0.3, 0.4
DOM = dict(xmin=-1.5, xmax=4.8, ymin=-2.01799653, ymax=2.01799653, zmin=-2.2, zmax=2.2)


def box_tris(d):
    x0, x1, y0, y1, z0, z1 = d["xmin"], d["xmax"], d["ymin"], d["ymax"], d["zmin"], d["zmax"]
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    return [(v[a], v[b], v[c]) for a, b, c in faces]


# one multi-solid surface: the domain box and the body, each its own patch
box = WORK / "_box.stl"
body = WORK / "_body.stl"
write_stl_ascii(box, box_tris(DOM), name="farfield")
airfoil.extrude_stl(body, airfoil.naca4("0012", 24), span=SPAN, chord=CHORD, name="body")
surface = CASE / "constant" / "triSurface" / "domain.stl"
surface.write_text(box.read_text() + body.read_text())
solids = re.findall(r"^solid (\S+)", surface.read_text(), re.M)
print("surface:", surface.name, surface.stat().st_size, "B, solids:", solids)

foam.write_mesh_system(CASE)  # controlDict/fvSchemes/fvSolution stubs
(CASE / "system" / "meshDict").write_text(
    """FoamFile
{
    version         2;
    format          ascii;
    class           dictionary;
    object          meshDict;
}

surfaceFile     "constant/triSurface/domain.stl";

maxCellSize     0.15;

localRefinement
{
    "body.*"
    {
        cellSize    0.0375;
    }
}

boundaryLayers
{
    patchBoundaryLayers
    {
        "body.*"
        {
            nLayers         2;
            thicknessRatio  1.2;
        }
    }
}
"""
)

WRAP = "/usr/bin/openfoam2606"
for app_name, timeout_s in (("cartesianMesh", 1500), ("checkMesh", 300)):
    t0 = time.time()
    res = subprocess.run(
        [WRAP, app_name, "-case", str(CASE)],
        capture_output=True, text=True, timeout=timeout_s, cwd=str(WORK),
    )
    out = res.stdout + res.stderr
    (WORK / f"log.{app_name}").write_text(out)
    print(f"\n--- {app_name}: rc={res.returncode}, {time.time() - t0:.1f} s ---")
    if app_name == "cartesianMesh":
        for pat in (r"Number of cells.*", r"Cells:.*", r"cells:.*", r"boundary layer.*",
                    r"Layer.*", r"FATAL.*", r"error.*"):
            for m in re.findall(pat, out, re.I)[-3:]:
                print("   ", m[:150])
    else:
        for pat in (r"cells:.*", r"Max cell openness.*", r"Max aspect ratio.*",
                    r"Mesh non-orthogonality Max.*", r"Max skewness.*", r"Mesh OK.*",
                    r"\*\*\*.*"):
            for m in re.findall(pat, out)[-2:]:
                print("   ", m.strip()[:150])
