"""A74 P3: can feature edges clear the twelve skew faces at the trailing edge?

Prints, never asserts. Four variants of the same case, all else equal - and
each one meshed TWICE, because the first version of this script did not pin
`OMP_NUM_THREADS` and its 45-degree row moved between runs (2.2391098, then
2.6517441). A74 P2 had already recorded that a threaded cfMesh builds a
different mesh each time; measuring a mesher with that unpinned is measuring
whichever run happened to be luckiest, twice in one campaign.
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
from tee.windtunnel import airfoil, foam, physics, runs  # noqa: E402

WORK = Path(sys.argv[1])
WRAP = "/usr/bin/openfoam2606"
CHORD, SPAN = 0.3, 0.4
DOM = dict(xmin=-1.5, xmax=4.8, ymin=-2.018, ymax=2.018, zmin=-2.2, zmax=2.2)


def build_surface(case: Path) -> Path:
    tri = case / "constant" / "triSurface"
    tri.mkdir(parents=True, exist_ok=True)
    parts = []
    for name, tris in physics.box_faces(**DOM).items():
        physics.write_stl_ascii(tri / f"{name}.stl", tris, name=name)
        parts.append(tri / f"{name}.stl")
    body = tri / "body.stl"
    airfoil.extrude_stl(body, airfoil.naca4("0012", 24), span=SPAN, chord=CHORD, name="body")
    parts.append(body)
    out = tri / "domain.stl"
    out.write_text("".join(p.read_text() for p in parts))
    return out


ENV = {**os.environ, "OMP_NUM_THREADS": "1"}  # what the lane pins; see the docstring


def run(app_name, *args, case, timeout=900):
    t0 = time.time()
    res = subprocess.run(
        [WRAP, app_name, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(case),
        env=ENV,
    )
    (case / f"log.{app_name}").write_text(res.stdout + res.stderr)
    return res.returncode, round(time.time() - t0, 1), res.stdout + res.stderr


def check(case):
    rc, wall, text = run("checkMesh", "-case", str(case), case=case)
    d = foam.parse_checkmesh(text)
    return {
        "cells": d.get("cells"),
        "max_skew": d.get("max_skew"),
        "max_aspect": d.get("max_aspect"),
        "failed": d.get("failed") or [],
    }


VARIANTS = {
    # name: (surface suffix, extra meshDict body)
    "stl-plain": (None, ""),
    "fms-30deg": (30, ""),
    "fms-30deg-edge-refine": (30, "edgeMeshRefinement\n{\n    body\n    {\n        cellSize 0.01;\n        edgeMesh \"domain.fms\";\n    }\n}\n"),
    "fms-45deg": (45, ""),
}

RUNS = [(f"{n} run{i}", v) for n, v in VARIANTS.items() for i in (1, 2)]

for name, (angle, extra) in RUNS:
    case = WORK / name.replace(" ", "-")
    shutil.rmtree(case, ignore_errors=True)
    (case / "system").mkdir(parents=True, exist_ok=True)
    foam.write_mesh_system(case)
    surface = build_surface(case)
    surface_file = "constant/triSurface/domain.stl"
    prep_wall = 0.0
    if angle is not None:
        fms = surface.with_suffix(".fms")
        rc, prep_wall, text = run(
            "surfaceFeatureEdges", "-angle", str(angle), str(surface), str(fms), case=case
        )
        if rc != 0 or not fms.is_file():
            print(f"{name:24s} surfaceFeatureEdges rc={rc}: {text.strip().splitlines()[-1][:90]}")
            continue
        surface_file = f"constant/triSurface/{fms.name}"
    t = foam.Tunnel3D(
        xmin=DOM["xmin"], xmax=DOM["xmax"], ymin=DOM["ymin"], ymax=DOM["ymax"],
        zmin=DOM["zmin"], zmax=DOM["zmax"], base_cell=0.15, body_name="body",
        body_bbox=((0.0, -0.018, -0.2), (0.3, 0.018, 0.2)), layers=2,
    )
    text = foam.cfmesh_dict(t, surface_file=surface_file, body_cell=0.0375, layers=2)
    if extra:
        text = text.rstrip("\n") + "\n\n" + extra
    (case / "system" / "meshDict").write_text(text)
    rc, wall, log = run("cartesianMesh", "-case", str(case), case=case)
    if rc != 0:
        print(f"{name:24s} cartesianMesh rc={rc}: {log.strip().splitlines()[-1][:90]}")
        continue
    c = check(case)
    print(
        f"{name:24s} cells {c['cells']:>7}  skew {c['max_skew']}  aspect {c['max_aspect']}  "
        f"failed {len(c['failed'])}  mesh {wall} s (+{prep_wall} s features)",
        flush=True,
    )
    for f in c["failed"]:
        print(f"    {f[:110]}")
