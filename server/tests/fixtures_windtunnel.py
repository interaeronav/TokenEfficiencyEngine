"""Fake engines for the wt_* lane (A72).

Shell-outs that behave like OpenFOAM, SU2, vspscript/vspaero and pvpython
well enough for every parser, refusal and job path to run in CI with no
engine installed. Each fake is the same small Python script dispatching on
its own basename (argv[0]); `install_fakes` lays them out the way the real
installs look and returns the `[windtunnel]` config that points at them:

    fake-foam/   blockMesh surfaceFeatureExtract snappyHexMesh checkMesh
                 simpleFoam decomposePar reconstructPar reconstructParMesh
    fake-su2/    SU2_CFD
    fake-vsp/    vspscript vspaero vsp
    fake-pv/     pvpython paraview

Modes come from the environment so a test can pick the story it needs:

    TEE_FAKE_FOAM_MODE   converge | stall | oscillate | diverge | crash | slow
    TEE_FAKE_CHECKMESH   ok | skew | bad
    TEE_FAKE_SU2_MODE    converge | maxiter | crash | slow
    TEE_FAKE_VSP_MODE    ok | crash
    TEE_FAKE_PV_MODE     ok | crash

Every header the fakes write was transcribed from a run TEE made on the
real engine on 2026-09-06 (research doc 72 §3): `coefficient.dat` from
OpenFOAM v2606, `history.csv` from SU2 8.4.0 with
HISTORY_OUTPUT=(ITER, WALL_TIME, RMS_RES, AERO_COEFF), the `.polar` from
VSPAERO 7.2.2, the PlotOverLine CSV from ParaView 5.11.2. No upstream file
is copied: the numbers are made up by the fake to tell its story.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# The headers, verbatim from the real files (the readers key on these).
FAKE_FOAM_HEADER = "# Time Cd Cd(f) Cd(r) Cl Cl(f) Cl(r) CmPitch CmRoll CmYaw Cs Cs(f) Cs(r)"
FAKE_SU2_HISTORY_HEADER = (
    '"Time_Iter","Outer_Iter","Inner_Iter","Time(sec)","rms[Rho]","rms[RhoU]","rms[RhoV]",'
    '"rms[RhoE]","RefForce","CD","CL","CSF","CMx","CMy","CMz","CFx","CFy","CFz","CEff"'
)
FAKE_SU2_SCREEN_HEADER = (
    "|  Inner_Iter|   Time(sec)|    rms[Rho]|   rms[RhoU]|   rms[RhoV]|   rms[RhoE]|"
    "          CL|          CD|"
)
FAKE_POLAR_HEADER = (
    "Beta Mach AoA Re/1e6 CLo CLi CLtot CDo CDi CDtot CSo CSi CStot L/D E CFx CFy CFz "
    "CMx CMy CMz CMl CMm CMn FOpt"
)
FAKE_LOD_HEADER = "Wing S Yavg Chord V/Vinf Cl Cd Cs Cx Cy Cz Cmx Cmy Cmz"
FAKE_PV_LINE_HEADER = (
    '"U:0","U:1","U:2","p","k","omega","nut","vtkValidPointMask","arc_length",'
    '"Points:0","Points:1","Points:2"'
)

FOAM_APPS = (
    "blockMesh",
    "surfaceFeatureExtract",
    "snappyHexMesh",
    "cartesianMesh",
    "checkMesh",
    "simpleFoam",
    "decomposePar",
    "reconstructPar",
    "reconstructParMesh",
)

# A 1x1 white PNG (67 bytes): what the fake pvpython "renders".
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cfc00000030101002e1a0c8f0000000049454e44ae426082"
)

FAKE_ENGINE_SRC = r'''
"""The one fake engine; behaviour follows the basename it was called by."""
import json
import math
import os
import re
import signal
import sys
import time
from pathlib import Path

NAME = Path(sys.argv[0]).name
ARGS = sys.argv[1:]
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cfc00000030101002e1a0c8f0000000049454e44ae426082"
)


def out(line=""):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def case_dir():
    if "-case" in ARGS:
        return Path(ARGS[ARGS.index("-case") + 1])
    return Path.cwd()


def read(path):
    try:
        return path.read_text(errors="replace")
    except OSError:
        return ""


def need_control_dict(case):
    if not (case / "system" / "controlDict").is_file():
        out("--> FOAM FATAL IO ERROR:")
        out("cannot find file " + str(case / "system" / "controlDict"))
        out("FOAM exiting")
        sys.exit(1)


# -- OpenFOAM -----------------------------------------------------------------

BOUNDARY_TEMPLATE = """FoamFile
{{
    version     2.0;
    format      ascii;
    class       polyBoundaryMesh;
    object      boundary;
}}
{n}
(
{body}
)
"""


def write_polymesh(case, patches, ncells):
    pm = case / "constant" / "polyMesh"
    pm.mkdir(parents=True, exist_ok=True)
    body = []
    start = ncells * 3
    for name, ptype in patches:
        body.append(
            "    %s\n    {\n        type            %s;\n        nFaces          %d;\n"
            "        startFace       %d;\n    }" % (name, ptype, 100, start)
        )
        start += 100
    (pm / "boundary").write_text(BOUNDARY_TEMPLATE.format(n=len(patches), body="\n".join(body)))
    note = '    note        "nPoints:%d nCells:%d nFaces:%d nInternalFaces:%d";\n' % (
        ncells * 2, ncells, ncells * 4, ncells * 3)
    (pm / "owner").write_text(
        "FoamFile\n{\n    version     2.0;\n    format      ascii;\n    class       labelList;\n"
        + note + "    object      owner;\n}\n\n0\n(\n)\n"
    )
    for name in ("points", "faces", "neighbour"):
        (pm / name).write_text(
            "FoamFile\n{\n    class       list;\n    object      %s;\n}\n0()\n" % name
        )


def cells_of(case):
    m = re.search(r"nCells:\s*(\d+)", read(case / "constant" / "polyMesh" / "owner"))
    return int(m.group(1)) if m else 0


def foam_banner(app):
    out("/*---------------------------------------------------------------------------*\\")
    out("| =========                 |                                                 |")
    out("| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |")
    out("|  \\\\    /   O peration     | Version:  v2606 (fake)                          |")
    out("\\*---------------------------------------------------------------------------*/")
    out("Exec   : " + app + " " + " ".join(ARGS))
    out("Case   : " + str(case_dir()))
    out("")


def block_mesh():
    case = case_dir()
    need_control_dict(case)
    foam_banner("blockMesh")
    text = read(case / "system" / "blockMeshDict")
    if not text:
        out("--> FOAM FATAL IO ERROR:")
        out("cannot find file " + str(case / "system" / "blockMeshDict"))
        sys.exit(1)
    names = re.findall(r"^\s+(\w+)\s*\n\s*\{\s*\n\s*type\s+(\w+);", text, re.M)
    patches = [(n, t) for n, t in names] or [("inlet", "patch"), ("outlet", "patch")]
    m = re.search(r"hex \([^)]*\) \((\d+) (\d+) (\d+)\)", text)
    ncells = int(m.group(1)) * int(m.group(2)) * int(m.group(3)) if m else 1000
    write_polymesh(case, patches, ncells)
    out("Creating polyMesh from blockMesh")
    out("Writing polyMesh")
    out("End")


def surface_feature_extract():
    case = case_dir()
    need_control_dict(case)
    foam_banner("surfaceFeatureExtract")
    tri = case / "constant" / "triSurface"
    stls = sorted(tri.glob("*.stl")) if tri.is_dir() else []
    if not stls:
        out("--> FOAM FATAL ERROR:")
        out("no surfaces under " + str(tri))
        sys.exit(1)
    for stl in stls:
        (tri / (stl.stem + ".eMesh")).write_text("fake eMesh\n")
        out("Reading surface " + stl.name)
    out("End")


def snappy():
    case = case_dir()
    need_control_dict(case)
    foam_banner("snappyHexMesh")
    if not (case / "system" / "snappyHexMeshDict").is_file():
        out("--> FOAM FATAL IO ERROR: cannot find file snappyHexMeshDict")
        sys.exit(1)
    m = re.search(r"(\w+)\.eMesh", read(case / "system" / "snappyHexMeshDict"))
    body = m.group(1) if m else "body"
    boundary = read(case / "constant" / "polyMesh" / "boundary")
    names = re.findall(r"^\s+(\w+)\s*\n\s*\{\s*\n\s*type\s+(\w+);", boundary, re.M)
    patches = [(n, t) for n, t in names if n != body] + [(body, "wall")]
    write_polymesh(case, patches, max(cells_of(case), 1000) * 4)
    for phase in ("Castellation", "Snapping", "Layer addition"):
        out(phase + " ...")
    out("Layer mesh : cells:%d" % cells_of(case))
    out("End")


def cartesian_mesh():
    """cfMesh's `cartesianMesh`, faked at the level that matters.

    What a test needs to be able to catch: the dictionary must exist, the
    surface it names must exist, and the PATCHES COME FROM THE STL's `solid`
    names - which is the whole reason `runs.domain_surface` rewrites the body
    rather than copying it. Everything else is log shape.
    """
    case = case_dir()
    need_control_dict(case)
    foam_banner("cartesianMesh")
    out("(cfmesh)")
    mesh_dict = case / "system" / "meshDict"
    if not mesh_dict.is_file():
        out("--> FOAM FATAL IO ERROR: cannot find file meshDict")
        sys.exit(1)
    text = read(mesh_dict)
    m = re.search(r'surfaceFile\s+"([^"]+)"', text)
    surface = case / m.group(1) if m else None
    if surface is None or not surface.is_file():
        out("--> FOAM FATAL ERROR: cannot read surface file " + str(surface))
        sys.exit(1)
    solids = re.findall(r"^solid\s+(\S+)", read(surface), re.M)
    if not solids:
        out("--> FOAM FATAL ERROR: no solids in " + surface.name)
        sys.exit(1)
    cell = re.search(r"maxCellSize\s+([0-9.eE+-]+)", text)
    layers = re.search(r"nLayers\s+(\d+)", text)
    out("Reading " + surface.name + ": " + str(len(solids)) + " patches")
    out("Requested cell size " + (cell.group(1) if cell else "?"))
    # the farfield solids are patches, the body a wall - the same shape snappy
    # leaves behind, so everything downstream reads one mesh either way
    body = solids[-1]
    patches = [(s, "patch") for s in solids[:-1]] + [(body, "wall")]
    n = int(os.environ.get("TEE_FAKE_CFMESH_CELLS", "40000"))
    write_polymesh(case, patches, n)
    out("Starting creating layer cells")
    out("Adding %d cells to the mesh" % (n // 8))
    if layers:
        out("Starting refining boundary layers")
        out("Number of newly generated cells %d" % (int(layers.group(1)) * 150))
        out("Finished refining boundary layers")
    out("Finished generating the mesh")
    out("End")


def check_mesh():
    case = case_dir()
    need_control_dict(case)
    foam_banner("checkMesh")
    mode = os.environ.get("TEE_FAKE_CHECKMESH", "ok")
    n = cells_of(case)
    out("Mesh stats")
    out("    points:           %d" % (n * 2))
    out("    faces:            %d" % (n * 4))
    out("    internal faces:   %d" % (n * 3))
    out("    cells:            %d" % n)
    out("")
    out("Checking geometry...")
    out("    Max aspect ratio = 242.9 OK.")
    out("    Max non-orthogonality = 34.1 average: 4.2")
    if mode == "ok":
        out("    Max skewness = 1.9 OK.")
        out("")
        out("Mesh OK.")
    elif mode == "skew":
        out("  ***Max skewness = 12.739298, 6 highly skew faces detected which may "
            "impair the quality of the results")
        out("")
        out("Failed 1 mesh checks.")
    else:
        out("  ***Boundary openness (0.3 0.1 0.2) possible hole in boundary description.")
        out("  ***Zero or negative cell volume detected.  Minimum negative volume: -1e-9")
        out("")
        out("Failed 2 mesh checks.")
    out("End")


def parse_control(case):
    control = read(case / "system" / "controlDict")
    m = re.search(r"^endTime\s+(\d+)\s*;", control, re.M)
    end = int(m.group(1)) if m else 500
    m = re.search(
        r"residualControl\s*\{[^}]*?\bp\s+([0-9.eE+-]+)\s*;",
        read(case / "system" / "fvSolution"),
        re.S,
    )
    target = float(m.group(1)) if m else 1e-5
    return end, target, "forceCoeffs" in control


def simple_foam():
    case = case_dir()
    need_control_dict(case)
    foam_banner("simpleFoam")
    mode = os.environ.get("TEE_FAKE_FOAM_MODE", "converge")
    end, target, coeffs = parse_control(case)
    coeff_path = case / "postProcessing" / "forceCoeffs1" / "0" / "coefficient.dat"
    fh = None
    if coeffs:
        coeff_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(coeff_path, "w")
        fh.write("# Force coefficients\n# dragDir : (1 0 0)\n# liftDir : (0 1 0)\n# Aref : 0.1\n")
        fh.write("# Time Cd Cd(f) Cd(r) Cl Cl(f) Cl(r) CmPitch CmRoll CmYaw Cs Cs(f) Cs(r)\n")
    cl_final, cd_final, cm_final = 0.4356, 0.01091, 0.00056
    if "laminar" in read(case / "constant" / "turbulenceProperties"):
        # A laminar case here means the Re 40 cylinder benchmark, whose drag
        # is two orders larger than the airfoil's. Real numbers from a real
        # simpleFoam run of TEE's own O-mesh on this machine, 2026-09-07 -
        # the fake answers what the engine answered, so verify.py's
        # tolerances are exercised rather than dodged.
        cl_final, cd_final, cm_final = 0.00003, 1.518301, 0.0
    limit = end if mode != "slow" else 10 ** 9
    for t in range(1, limit + 1):
        if mode == "slow":
            time.sleep(0.1)
        if mode == "crash" and t > 3:
            out("--> FOAM FATAL ERROR:")
            out("Floating point exception")
            out("FOAM aborting")
            sys.exit(1)
        decay = 0.93 ** t
        if mode == "stall":
            decay = max(decay, 2e-3)
        if mode == "diverge" and t > 40:
            decay = 0.1 * 1.15 ** (t - 40)
        r_u = 0.1 * decay
        r_p = 0.3 * decay
        settle = 1.0 - math.exp(-t / 12.0)
        cl = cl_final * settle
        cd = cd_final * settle + 0.02 * (1 - settle)
        cm = cm_final * settle
        if mode == "oscillate":  # a limit cycle: zero-mean, short period, 3 % amplitude
            cl *= 1.0 + 0.03 * math.sin(t * 1.0)
            cd *= 1.0 + 0.03 * math.cos(t * 1.0)
        out("Time = %d" % t)
        out("")
        solve = (
            "%s:  Solving for %s, Initial residual = %.6g, Final residual = %.6g, "
            "No Iterations %d"
        )
        out(solve % ("smoothSolver", "Ux", r_u, r_u / 10, 1))
        out(solve % ("smoothSolver", "Uy", r_u * 3, r_u / 3, 1))
        out(solve % ("GAMG", "p", r_p, r_p / 100, 3))
        out("time step continuity errors : sum local = 1e-05, global = 1e-07, cumulative = 1e-05")
        out(solve % ("smoothSolver", "omega", r_u / 100, r_u / 1000, 1))
        out(solve % ("smoothSolver", "k", r_u / 10, r_u / 100, 1))
        if mode == "diverge" and t > 60:
            out("bounding k, min: -1e-3 max: 2 average: 0.1")
        out("ExecutionTime = %.2f s  ClockTime = %d s" % (t * 0.03, int(t * 0.03) + 1))
        out("")
        if fh is not None:
            fh.write(
                "%d\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t%.6g\t0\t0\t0\t0\t0\n"
                % (t, cd, cd * 0.9, cd * 0.1, cl, cl * 0.5, cl * 0.5, cm)
            )
            fh.flush()
        if mode in ("converge", "stall", "oscillate") and max(r_u, r_p) < target and t > 50:
            out("SIMPLE solution converged in %d iterations" % t)
            break
    if fh is not None:
        fh.close()
    last = t
    tdir = case / str(last)
    tdir.mkdir(exist_ok=True)
    for name in ("U", "p", "k", "omega", "nut"):
        (tdir / name).write_text(
            "FoamFile { object %s; }\ninternalField uniform 0;\n" % name
        )
    if "wallShearStress" in read(case / "system" / "controlDict"):
        write_wall_shear(case, last)
    out("End")


def write_wall_shear(case, last):
    """The raw `surfaces` sample the flat-plate benchmark reads.

    Shaped like a real turbulent plate, Cf ~ x^-0.2, and calibrated so the
    reference station x = 0.9700840712 carries 2.646754e-03 - what live
    OpenFOAM v2606 actually produced on the adopted grid, 2026-09-07. The
    fake answers what the engine answered, so verify.py's tolerance is
    exercised rather than dodged.
    """
    u = 1.0
    m = re.search(r"internalField\s+uniform\s*\(([-0-9.eE+]+)", read(case / "0" / "U"))
    if m:
        u = abs(float(m.group(1))) or 1.0
    x_ref, cf_ref = 0.9700840712, 2.646754e-03
    c = cf_ref * (x_ref**0.2)
    out_dir = case / "postProcessing" / "plateSample" / str(last)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["# x  y  z  tau_x  tau_y  tau_z"]
    for i in range(320):
        x = 2.0 * (i + 0.5) / 320.0
        cf = c * x ** (-0.2)
        tau = -0.5 * cf * u * u  # OpenFOAM reports it negative in the flow direction
        lines.append(f"{x:.8f} 0 0 {tau:.9e} 0 0")
    (out_dir / "wallShearStress_plate.raw").write_text("\n".join(lines) + "\n")


def decompose_par():
    case = case_dir()
    need_control_dict(case)
    foam_banner("decomposePar")
    m = re.search(r"numberOfSubdomains\s+(\d+)", read(case / "system" / "decomposeParDict"))
    n = int(m.group(1)) if m else 2
    for k in range(n):
        (case / ("processor%d" % k)).mkdir(exist_ok=True)
    out("Processor %d: field transfer" % n)
    out("End")


def reconstruct():
    case = case_dir()
    need_control_dict(case)
    foam_banner(NAME)
    out("Reconstructing fields")
    out("End")


# -- SU2 -----------------------------------------------------------------------

def su2_cfd():
    if ARGS and ARGS[0] in ("-h", "--help", "--version", "-v"):
        out("SU2 v8.4.0 (fake) - The Open-Source CFD Code")
        sys.exit(0)
    mode = os.environ.get("TEE_FAKE_SU2_MODE", "converge")
    cfg_path = Path(ARGS[-1]) if ARGS else Path("case.cfg")
    cfg = {}
    for line in read(cfg_path).splitlines():
        s = line.split("%")[0].strip()
        if "=" in s:
            k, v = s.split("=", 1)
            cfg[k.strip()] = v.strip()
    out("-------------------------------------------------------------------------")
    out("|    ___ _   _ ___                                                      |")
    out("|   / __| | | |_  )   Release 8.4.0 (fake)                              |")
    out("-------------------------------------------------------------------------")
    mesh = cfg.get("MESH_FILENAME", "")
    if not mesh or not Path(mesh).is_file():
        out("Error in \"void CConfig::SetPostprocessing\":")
        out("-------------------------------------------------------------------------")
        out("Error Exit: mesh file not found: " + mesh)
        sys.exit(1)
    if mode == "crash":
        out("Error in \"CSolver::CheckConvergence\":")
        out("Error Exit: NaN residual detected")
        sys.exit(1)
    iters = int(cfg.get("ITER", "1500"))
    minval = float(cfg.get("CONV_RESIDUAL_MINVAL", "-8"))
    hist = open("history.csv", "w")
    hist.write(
        '"Time_Iter","Outer_Iter","Inner_Iter","Time(sec)","rms[Rho]","rms[RhoU]",'
        '"rms[RhoV]","rms[RhoE]","RefForce","CD","CL","CSF","CMx","CMy","CMz",'
        '"CFx","CFy","CFz","CEff"\n'
    )
    hist.flush()
    out("+----------------------------------------------------------------+")
    out(
        "|  Inner_Iter|   Time(sec)|    rms[Rho]|   rms[RhoU]|   rms[RhoV]|   rms[RhoE]|"
        "          CL|          CD|"
    )
    out("+----------------------------------------------------------------+")
    cl_final, cd_final = 0.3345, 0.01992
    limit = iters if mode != "slow" else 10 ** 9
    for it in range(limit):
        if mode == "slow":
            time.sleep(0.1)
        rho = -2.0 - it * 0.01 if mode != "maxiter" else max(-2.0 - it * 0.01, -5.0)
        settle = 1.0 - math.exp(-it / 60.0)
        cl, cd = cl_final * settle, cd_final * settle + 0.03 * (1 - settle)
        out(
            "|%12d|%12.4f|%12.6f|%12.6f|%12.6f|%12.6f|%12.6f|%12.6f|"
            % (it, it * 0.05, rho, rho - 0.3, rho - 0.5, rho + 0.2, cl, cd)
        )
        hist.write(
            "0,0,%d,%.4f,%.6f,%.6f,%.6f,%.6f,1.0,%.6f,%.6f,0,0,0,0.001,%.6f,%.6f,0,%.4f\n"
            % (it, it * 0.05, rho, rho - 0.3, rho - 0.5, rho + 0.2, cd, cl, cd, cl, cl / cd)
        )
        hist.flush()
        if mode == "converge" and rho < minval and it > 100:
            out("")
            out("----------------------------- Solver Exit -------------------------------")
            out("All convergence criteria satisfied.")
            out("+-----------------------------------------------------------------------+")
            break
    else:
        if mode == "maxiter":
            out("Maximum number of iterations reached (ITER = %d) before convergence." % iters)
    hist.close()
    Path("flow.vtu").write_text(
        '<?xml version="1.0"?>\n<VTKFile type="UnstructuredGrid" version="0.1">\n'
        '<UnstructuredGrid><Piece NumberOfPoints="0" NumberOfCells="0"/>'
        "</UnstructuredGrid></VTKFile>\n"
    )
    Path("surface_flow.csv").write_text(
        '"PointID","x","y","Pressure","Pressure_Coefficient"\n0,0.0,0.0,101325,0.5\n'
    )
    Path("restart_flow.dat").write_bytes(b"fake restart\n")
    out("")
    out("------------------------- Exit Success (SU2_CFD) ------------------------")


# -- OpenVSP -------------------------------------------------------------------

def vsp_stl(path, span, chord):
    """A watertight box: 12 triangles, outward normals (a wing's bbox)."""
    x0, x1, y0, y1 = 0.0, chord, -span / 2.0, span / 2.0
    z0, z1 = -0.06 * chord, 0.06 * chord
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
             (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    lines = ["solid wing"]
    for a, b, c in faces:
        lines.append("  facet normal 0 0 0\n    outer loop")
        for p in (v[a], v[b], v[c]):
            lines.append("      vertex %.6g %.6g %.6g" % p)
        lines.append("    endloop\n  endfacet")
    lines.append("endsolid wing")
    path.write_text("\n".join(lines) + "\n")


def vspscript():
    if ARGS and ARGS[0] in ("-help", "-h", "--help", "-v", "--version"):
        out("Vehicle Sketch Pad 3.51.3 (fake)")
        sys.exit(0)
    mode = os.environ.get("TEE_FAKE_VSP_MODE", "ok")
    script = Path(ARGS[ARGS.index("-script") + 1]) if "-script" in ARGS else None
    text = read(script) if script else ""
    if mode == "crash" or not text:
        out("ERROR: script failed to compile")
        sys.exit(1)
    m = re.search(r'WriteVSPFile\( "([^"]+)\.vsp3"', text)
    if m:  # the wing build
        stem = m.group(1)
        span = float(re.search(r'"Span", "XSec_1", ([-0-9.eE]+)', text).group(1)) * 2.0
        chord = float(re.search(r'"Root_Chord", "XSec_1", ([-0-9.eE]+)', text).group(1))
        Path(stem + ".vsp3").write_text(
            '<?xml version="1.0"?>\n<Vsp_Geometry>\n<Version>3.51.3</Version>\n</Vsp_Geometry>\n'
        )
        if "EXPORT_STL" in text:
            vsp_stl(Path(stem + ".stl"), span, chord)
        if "ComputeDegenGeom" in text:
            Path(stem + "_DegenGeom.csv").write_text(
                "# DegenGeom Type,nXsecs,nPnts\nLIFTING_SURFACE,4,3\n"
            )
        out("TotalSpan=%.6g" % span)
        out("TotalArea=%.6g" % (span * chord))
        out("DONE")
        sys.exit(0)
    m = re.search(r'ReadVSPFile\( "([^"]+)" \)', text)
    if not m or not Path(m.group(1)).is_file():
        out("ERROR: model not found")
        sys.exit(1)
    stem = Path(m.group(1)).stem
    a0 = float(re.search(r"a0\.push_back\( ([-0-9.eE]+) \)", text).group(1))
    a1 = float(re.search(r"a1\.push_back\( ([-0-9.eE]+) \)", text).group(1))
    n = int(re.search(r"an_pts\.push_back\( (\d+) \)", text).group(1))
    mach = float(re.search(r"m0\.push_back\( ([-0-9.eE]+) \)", text).group(1))
    alphas = [a0 + k * (a1 - a0) / (n - 1) for k in range(n)] if n > 1 else [a0]
    AR, e, a_rad, cdo = 10.0, 0.96, 4.905, 0.0063
    rows = []
    for a in alphas:
        cl = a_rad * math.radians(a)
        cdi = cl * cl / (math.pi * e * AR)
        cd = cdo + cdi
        rows.append((0.0, mach, a, 2.3, 0.0, cl, cl, cdo, cdi, cd, 0.0, 0.0, 0.0,
                     (cl / cd if cd else 0.0), (e if abs(cl) > 1e-9 else 0.0)))
    with open(stem + ".polar", "w") as fh:
        fh.write(
            "Beta Mach AoA Re/1e6 CLo CLi CLtot CDo CDi CDtot CSo CSi CStot L/D E "
            "CFx CFy CFz CMx CMy CMz CMl CMm CMn FOpt\n"
        )
        for r in rows:
            fh.write(" ".join("%.6f" % x for x in r) + " 0 0 0 0 0 0 0 0 0 0\n")
    with open(stem + ".lod", "w") as fh:
        for r in rows:
            fh.write("Wing S Yavg Chord V/Vinf Cl Cd Cs Cx Cy Cz Cmx Cmy Cmz\n")
            for k in range(8):
                fh.write(
                    "1 1.25 %.3f 1.0 1.0 %.5f %.5f 0 0 0 0 0 0 0\n"
                    % (-4.4 + k * 1.25, r[6] * 1.1, r[9])
                )
    Path(stem + ".history").write_text("Iter Mach AoA Beta CL CDo CDi CDtot CS L/D\n")
    Path(stem + ".vspgeom").write_text("fake vspgeom\n")
    Path(stem + ".vspaero").write_text("Sref = 10\nCref = 1\nBref = 10\n")
    out("VSPAERO v.7.2.2 (fake) ... Wake Iter: 3 / 3")
    out("POLAR=%s.polar" % stem)
    out("DONE")
    sys.exit(2)  # measured: vspscript exits 2 after a COMPLETE sweep


def vspaero():
    out("VSPAERO v.7.2.2 (fake)")
    sys.exit(0)


# -- ParaView ------------------------------------------------------------------

def pvpython():
    if ARGS and ARGS[0] == "--version":
        out("paraview version 5.11.2 (fake)")
        sys.exit(0)
    mode = os.environ.get("TEE_FAKE_PV_MODE", "ok")
    script = Path(ARGS[-1])
    text = read(script)
    if mode == "crash" or not text:
        sys.stderr.write("Segmentation fault (core dumped)\n")
        sys.exit(139)
    m = re.search(r"SaveData\('([^']+)', proxy=pol\)", text)
    if m:
        n = int(re.search(r"pol\.Resolution = (\d+)", text).group(1)) + 1
        with open(m.group(1), "w") as fh:
            fh.write(
                '"U:0","U:1","U:2","p","k","omega","nut","vtkValidPointMask",'
                '"arc_length","Points:0","Points:1","Points:2"\n'
            )
            for k in range(n):
                s = k / max(n - 1, 1)
                valid = 0 if k < 2 else 1  # the first two points sit inside the body
                # ParaView writes 0 with vtkValidPointMask 0 for a point outside the mesh
                fh.write(
                    "%.6f,%.6f,0,%.4f,0.01,120,1e-5,%d,%.6f,0.5,%.6f,0.05\n"
                    % (
                        34.9 - 1.5 * s if valid else 0.0,
                        0.3 * s if valid else 0.0,
                        -120 + 300 * s if valid else 0.0,
                        valid,
                        s * 0.3,
                        s * 0.3,
                    )
                )
        out("OK")
        sys.exit(0)
    m = re.search(r"SaveData\('([^']+)', proxy=cd, PointDataArrays=\['([^']+)'\]\)", text)
    if m:
        field = m.group(2)
        known = {
            "U": ["U:0", "U:1", "U:2"],
            "p": ["p"],
            "k": ["k"],
            "omega": ["omega"],
            "nut": ["nut"],
            "Pressure": ["Pressure"],
            "Density": ["Density"],
            "Pressure_Coefficient": ["Pressure_Coefficient"],
            "Velocity": ["Velocity:0", "Velocity:1", "Velocity:2"],
        }
        cols = known.get(field, [])  # an unknown field: ParaView writes the points and nothing else
        with open(m.group(1), "w") as fh:
            names = cols + ["Points:0", "Points:1", "Points:2"]
            fh.write(",".join('"%s"' % c for c in names) + "\n")
            for k in range(100):
                vals = [30.0 + k * 0.05] + ([0.1, 0.0] if len(cols) == 3 else [])
                vals = vals[: len(cols)]
                fh.write(",".join("%.4f" % v for v in vals + [k * 0.01, 0.0, 0.0]) + "\n")
        out("OK")
        sys.exit(0)
    m = re.search(r"SaveState\('([^']+)'\)", text)
    if m:
        # A73: a state file is XML ParaView writes for itself. The fake writes
        # the two things the lane actually reads back - the size, and the
        # source path appearing EXACTLY ONCE, which is what relocate() relies
        # on. A "full" state (one that rendered) is an order of magnitude
        # bigger than a pipeline-only one, so the fake keeps that proportion.
        src = re.search(
            r"(?:OpenFOAMReader|XMLUnstructuredGridReader)\(FileName=\[?'([^']+)'", text
        )
        full = "Render(rv)" in text
        pad = "  <Padding/>\n" * (900 if full else 60)
        Path(m.group(1)).write_text(
            '<?xml version="1.0"?>\n<ParaView>\n'
            '  <ServerManagerState version="5.11.2">\n'
            '    <Proxy group="sources" type="OpenFOAMReader" '
            f'filename="{src.group(1) if src else ""}"/>\n'
            + ('    <Proxy group="views" type="RenderView"/>\n' if full else "")
            + pad
            + "  </ServerManagerState>\n</ParaView>\n"
        )
        out("OK")
        sys.exit(0)
    m = re.search(r"SaveScreenshot\('([^']+)'", text)
    if m:
        Path(m.group(1)).write_bytes(PNG_1X1)
        if "print('RANGE'" in text:
            out("RANGE -630.957 454.512")
        out("OK")
        sys.exit(0)
    sys.stderr.write("Traceback: unknown script\n")
    sys.exit(1)


def paraview_app():
    """The ParaView APPLICATION, not pvpython: a window, faked.

    It writes a marker beside the state it was handed and exits, so a test can
    prove WHAT was opened without a display anywhere. The real client would
    hold the window; nothing in the lane waits for it, which is the point of
    start_new_session.
    """
    state = ""
    for a in ARGS:
        if a.startswith("--state="):
            state = a.split("=", 1)[1]
        elif a == "--state":
            state = ARGS[ARGS.index(a) + 1]
    if not state:
        sys.stderr.write("no --state given\n")
        sys.exit(1)
    Path(state + ".opened").write_text(" ".join(ARGS) + "\n")
    out("paraview (fake) opened " + state)
    sys.exit(0)


def vsp_gui():
    """OpenVSP's GUI: `vsp [inputfile.vsp3]`, the model positional."""
    if not ARGS or not ARGS[0].endswith(".vsp3"):
        sys.stderr.write("usage: vsp [inputfile.vsp3]\n")
        sys.exit(1)
    Path(ARGS[0] + ".opened").write_text(" ".join(ARGS) + "\n")
    out("vsp (fake) opened " + ARGS[0])
    sys.exit(0)


DISPATCH = {
    "blockMesh": block_mesh,
    "surfaceFeatureExtract": surface_feature_extract,
    "snappyHexMesh": snappy,
    "cartesianMesh": cartesian_mesh,
    "checkMesh": check_mesh,
    "simpleFoam": simple_foam,
    "decomposePar": decompose_par,
    "reconstructPar": reconstruct,
    "reconstructParMesh": reconstruct,
    "SU2_CFD": su2_cfd,
    "vspscript": vspscript,
    "vspaero": vspaero,
    "pvpython": pvpython,
    "paraview": paraview_app,
    "vsp": vsp_gui,
}

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    fn = DISPATCH.get(NAME)
    if fn is None:
        sys.stderr.write("fake engine: no behaviour for %r\n" % NAME)
        sys.exit(2)
    fn()
'''


def install_fakes(root: Path) -> dict[str, Any]:
    """Lay the fakes out under `root` and return the `[windtunnel]` config
    that points the lane at them (bindir route for OpenFOAM, a directory for
    the others - `_binary` appends the executable name to a directory)."""
    root = Path(root)
    src = FAKE_ENGINE_SRC.lstrip("\n")
    layout = {
        "fake-foam": FOAM_APPS,
        "fake-su2": ("SU2_CFD",),
        "fake-vsp": ("vspscript", "vspaero", "vsp"),
        "fake-pv": ("pvpython", "paraview"),
    }
    for folder, names in layout.items():
        d = root / folder
        d.mkdir(parents=True, exist_ok=True)
        engine = d / "fake_engine.py"
        engine.write_text(f"#!{sys.executable}\n{src}")
        engine.chmod(0o755)
        for name in names:
            link = d / name
            if link.exists() or link.is_symlink():
                link.unlink()
            os.symlink("fake_engine.py", link)
    return {
        "openfoam": str(root / "fake-foam"),
        "su2": str(root / "fake-su2"),
        "openvsp": str(root / "fake-vsp"),
        "pvpython": str(root / "fake-pv" / "pvpython"),
    }


def make_app(tmp_path: Path, *, fakes: bool = True, extra_cfg: dict[str, Any] | None = None):
    """A TeeApp with the wind-tunnel lane registered against the fakes
    (or against nothing, for the refusal tests)."""
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.windtunnel.tools import register_windtunnel_tools

    project = Path(tmp_path) / "project"
    project.mkdir(exist_ok=True)
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    cfg = install_fakes(Path(tmp_path) / "engines") if fakes else {}
    cfg.update(extra_cfg or {})
    app.config.windtunnel = cfg
    store = register_windtunnel_tools(app, project)
    app._wt_store = store
    return app


def wait_job(app, job_id: str, timeout_s: float = 60.0) -> dict[str, Any]:
    from tee.kernel.waiting import wait_until

    wait_until(
        lambda: app.jobs.status(job_id)["state"] in ("done", "error", "cancelled"),
        timeout_s,
        max_delay_s=0.1,
    )
    return app.jobs.status(job_id)
