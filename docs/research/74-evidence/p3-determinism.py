"""Does the FMS route stay reproducible under OMP_NUM_THREADS=1?"""
import hashlib, os, shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, "/home/user/TokenEfficiencyEngine/server/tests")
from tee.windtunnel import airfoil, foam, physics

WORK = Path(sys.argv[1]); WRAP = "/usr/bin/openfoam2606"
DOM = dict(xmin=-1.5, xmax=4.8, ymin=-2.018, ymax=2.018, zmin=-2.2, zmax=2.2)
env = {**os.environ, "OMP_NUM_THREADS": "1"}

def polymesh_hash(case):
    h = hashlib.sha256()
    for name in ("points", "faces", "owner", "neighbour", "boundary"):
        p = case / "constant" / "polyMesh" / name
        h.update(p.read_bytes() if p.is_file() else b"")
    return h.hexdigest()[:16]

for i in (1, 2):
    case = WORK / f"det{i}"
    shutil.rmtree(case, ignore_errors=True)
    (case / "system").mkdir(parents=True, exist_ok=True)
    foam.write_mesh_system(case)
    tri = case / "constant" / "triSurface"; tri.mkdir(parents=True, exist_ok=True)
    parts = []
    for name, tris in physics.box_faces(**DOM).items():
        physics.write_stl_ascii(tri / f"{name}.stl", tris, name=name); parts.append(tri / f"{name}.stl")
    body = tri / "body.stl"
    airfoil.extrude_stl(body, airfoil.naca4("0012", 24), span=0.4, chord=0.3, name="body")
    parts.append(body)
    (tri / "domain.stl").write_text("".join(p.read_text() for p in parts))
    subprocess.run([WRAP, "surfaceFeatureEdges", "-angle", "30",
                    str(tri / "domain.stl"), str(tri / "domain.fms")],
                   capture_output=True, text=True, timeout=300, cwd=str(case), env=env)
    t = foam.Tunnel3D(xmin=DOM["xmin"], xmax=DOM["xmax"], ymin=DOM["ymin"], ymax=DOM["ymax"],
                      zmin=DOM["zmin"], zmax=DOM["zmax"], base_cell=0.15, body_name="body",
                      body_bbox=((0.0, -0.018, -0.2), (0.3, 0.018, 0.2)), layers=2)
    (case / "system" / "meshDict").write_text(
        foam.cfmesh_dict(t, surface_file="constant/triSurface/domain.fms", body_cell=0.0375, layers=2))
    r = subprocess.run([WRAP, "cartesianMesh", "-case", str(case)],
                       capture_output=True, text=True, timeout=900, cwd=str(case), env=env)
    print(f"run {i}: rc={r.returncode}  polyMesh hash {polymesh_hash(case)}")
