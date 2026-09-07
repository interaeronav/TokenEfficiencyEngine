"""Per-engine mechanics behind the tools: prepare a run directory, compose
the argv, read progress cheaply while it runs, and read the result when it
is done. `tools.py` owns the conversation; this module owns the files.

OpenFOAM runs live in `runs/<run_id>/` with `constant/polyMesh` symlinked
to the case's mesh and their own `system/`, `constant/*Properties` and `0/`
for the angle of attack asked for. SU2 runs hold a `.cfg` pointing at the
case's `.su2` mesh by absolute path. VSPAERO runs copy the `.vsp3` in so the
solver's outputs (`.polar`, `.lod`, `.history`) land in the run directory.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.windtunnel import airfoil, foam, mesh2d, physics, su2, verdict, vsp
from tee.windtunnel.runner import read_json, tail_text

# ---------------------------------------------------------------------------
# Meshing
# ---------------------------------------------------------------------------


def omesh_for(
    case: dict[str, Any], *, first_cell_m: float, nj: int, radius_c: float
) -> mesh2d.OMesh:
    geom = case["geometry"]
    loop = [tuple(p) for p in geom["loop"]]
    chord = float(case["refs"]["cref"])
    # `omesh` takes the first cell in METRES and normalises by the chord
    # itself; dividing here too made a 0.3 m chord's first cell 0.3x too
    # small (caught by the chord-scaling test, never by a 1 m chord)
    return mesh2d.omesh(loop, first_cell=first_cell_m, nj=nj, radius_c=radius_c, chord=chord)


def mesh_airfoil_openfoam(
    case: dict[str, Any], engine_dir: Path, *, yplus: float, nj: int, radius_c: float
) -> dict[str, Any]:
    cond = case["conditions"]
    chord = float(case["refs"]["cref"])
    fc = physics.first_cell_height(
        y_plus=yplus, rho=cond["rho"], V=cond["V"], L=chord, mu=cond["mu"], cell_centred=True
    )
    t0 = time.time()
    mesh = omesh_for(case, first_cell_m=fc["first_cell_m"], nj=nj, radius_c=radius_c)
    counts = mesh2d.write_polymesh(engine_dir, mesh)
    _lo, hi = mesh.first_layer_heights()
    return {
        "kind": "omesh_polymesh",
        "cells": mesh.cells,
        "points": counts["points"],
        "ni": mesh.ni,
        "nj": mesh.nj,
        "growth": round(mesh.growth, 4),
        "first_cell_m": round(hi, 9),
        "y_plus_target": yplus,
        "farfield_c": radius_c,
        "thickness_m": counts["thickness"],
        "min_jacobian": mesh.min_jacobian(),
        "wall_s": round(time.time() - t0, 2),
        "notes": [
            *mesh.notes,
            "a sharp-TE O-mesh has a few skewed faces on the trailing-edge seam; the solver "
            "tolerates them",
        ],
        "mesh_hash": _polymesh_hash(engine_dir),
    }


def mesh_airfoil_su2(
    case: dict[str, Any], engine_dir: Path, *, first_cell_c: float, nj: int, radius_c: float
) -> dict[str, Any]:
    chord = float(case["refs"]["cref"])
    t0 = time.time()
    mesh = omesh_for(case, first_cell_m=first_cell_c * chord, nj=nj, radius_c=radius_c)
    engine_dir.mkdir(parents=True, exist_ok=True)
    path = engine_dir / "mesh.su2"
    nbytes = mesh2d.write_su2(path, mesh)
    return {
        "kind": "omesh_su2",
        "cells": mesh.cells,
        "points": mesh.nodes,
        "ni": mesh.ni,
        "nj": mesh.nj,
        "growth": round(mesh.growth, 4),
        "first_cell_c": first_cell_c,
        "farfield_c": radius_c,
        "min_jacobian": mesh.min_jacobian(),
        "su2_file": str(path),
        "bytes": nbytes,
        "wall_s": round(time.time() - t0, 2),
        "mesh_hash": _file_hash(path),
        "notes": mesh.notes,
    }


def _file_hash(path: Path) -> str:
    from tee.windtunnel.case import file_hash

    return file_hash(path)


def _polymesh_hash(case_dir: Path) -> str:
    from tee.windtunnel.case import file_hash

    pm = case_dir / "constant" / "polyMesh"
    parts = [
        file_hash(pm / n)
        for n in ("points", "faces", "owner", "neighbour", "boundary")
        if (pm / n).is_file()
    ]
    from tee.windtunnel.case import text_hash

    return text_hash("|".join(parts)) if parts else ""


def write_tunnel_3d(
    case: dict[str, Any],
    engine_dir: Path,
    *,
    base_cell_m: float,
    levels: tuple[int, int],
    layers: int,
) -> dict[str, Any]:
    """The blockMesh box + snappyHexMesh dictionaries around the case's STL."""
    geom = case["geometry"]
    stl_src = Path(geom["stl"])
    tri = engine_dir / "constant" / "triSurface"
    tri.mkdir(parents=True, exist_ok=True)
    body_name = "body"
    shutil.copyfile(stl_src, tri / f"{body_name}.stl")
    dom = case["domain"]
    t = foam.Tunnel3D(
        xmin=dom["xmin"],
        xmax=dom["xmax"],
        ymin=dom["ymin"],
        ymax=dom["ymax"],
        zmin=dom["zmin"],
        zmax=dom["zmax"],
        base_cell=base_cell_m,
        body_name=body_name,
        body_bbox=(tuple(geom["bbox"][0]), tuple(geom["bbox"][1])),
        surface_levels=levels,
        layers=layers,
        ground=bool(dom.get("ground")),
    )
    sysd = engine_dir / "system"
    sysd.mkdir(parents=True, exist_ok=True)
    foam.write_mesh_system(engine_dir)  # blockMesh and friends insist on controlDict
    (sysd / "blockMeshDict").write_text(foam.block_mesh_dict(t))
    (sysd / "snappyHexMeshDict").write_text(foam.snappy_dict(t))
    (sysd / "meshQualityDict").write_text(foam.mesh_quality_dict())
    (sysd / "surfaceFeatureExtractDict").write_text(foam.surface_feature_extract_dict(body_name))
    nx = max(round((t.xmax - t.xmin) / base_cell_m), 4)
    ny = max(round((t.ymax - t.ymin) / base_cell_m), 4)
    nz = max(round((t.zmax - t.zmin) / base_cell_m), 4)
    return {
        "body": body_name,
        "background_cells": nx * ny * nz,
        "levels": list(levels),
        "layers": layers,
    }


Step = tuple[str, list[str]]  # (application name, argv)


def mesh_sequence_3d(install: Any, engine_dir: Path, cores: int) -> list[Step]:
    c = str(engine_dir)
    seq: list[Step] = [
        ("blockMesh", install.argv("blockMesh", "-case", c)),
        ("surfaceFeatureExtract", install.argv("surfaceFeatureExtract", "-case", c)),
    ]
    if cores > 1:
        seq.append(("decomposePar", install.argv("decomposePar", "-case", c, "-force")))
        seq.append(
            (
                "snappyHexMesh",
                install.parallel_argv("snappyHexMesh", cores, "-overwrite", "-case", c),
            )
        )
        seq.append(
            ("reconstructParMesh", install.argv("reconstructParMesh", "-case", c, "-constant"))
        )
    else:
        seq.append(("snappyHexMesh", install.argv("snappyHexMesh", "-overwrite", "-case", c)))
    seq.append(("checkMesh", install.argv("checkMesh", "-case", c)))
    return seq


# ---------------------------------------------------------------------------
# Run preparation
# ---------------------------------------------------------------------------


def prepare_openfoam_run(
    case: dict[str, Any], run_dir: Path, engine_dir: Path, *, aoa_deg: float, iters: int, cores: int
) -> dict[str, Any]:
    cond = case["conditions"]
    refs = case["refs"]
    axes = physics.wind_axes(aoa_deg)
    V = float(cond["V"])
    nu = float(cond["mu"]) / float(cond["rho"])
    run_dir.mkdir(parents=True, exist_ok=True)
    const = run_dir / "constant"
    const.mkdir(exist_ok=True)
    link = const / "polyMesh"
    if link.is_symlink() or link.exists():
        if link.is_symlink():
            link.unlink()
        else:
            shutil.rmtree(link)
    os.symlink(engine_dir / "constant" / "polyMesh", link, target_is_directory=True)
    tri = engine_dir / "constant" / "triSurface"
    if tri.is_dir() and not (const / "triSurface").exists():
        os.symlink(tri, const / "triSurface", target_is_directory=True)
    two_d = case["kind"] == "airfoil2d"
    mesh = case.get("mesh", {})
    Aref = float(refs["Sref"]) * (float(mesh.get("thickness_m", 1.0)) if two_d else 1.0)
    if two_d:
        wall, free, empty, inlet, outlet, slip = (
            ("airfoil",),
            ("farfield",),
            ("frontAndBack",),
            (),
            (),
            (),
        )
    else:
        body = mesh.get("body", "body")
        wall = (body,)
        free, empty = (), ()
        inlet, outlet = ("inlet",), ("outlet",)
        slip = ("sides", "top") + (() if case.get("domain", {}).get("ground") else ("ground",))
        if case.get("domain", {}).get("ground"):
            wall = (*wall, "ground")
    setup = foam.FoamSetup(
        U_inf=tuple(V * c for c in axes["U"]),
        nu=nu,
        turbulence=case.get("turbulence", "kOmegaSST"),
        wall_treatment="low_re" if two_d else "wall_function",
        end_time=iters,
        write_interval=iters,
        Aref=Aref,
        lRef=float(refs["cref"]),
        CofR=(float(refs["cref"]) * 0.25, 0.0, 0.0),
        liftDir=axes["lift"],
        dragDir=axes["drag"],
        pitchAxis=(0.0, 0.0, 1.0) if two_d else (0.0, -1.0, 0.0),
        cores=cores,
        wall_patches=wall,
        freestream_patches=free,
        inlet_patches=inlet,
        outlet_patches=outlet,
        slip_patches=slip,
        empty_patches=empty,
    )
    files = foam.write_case(run_dir, setup)
    return {"files": files, "Aref": Aref, "U": list(setup.U_inf), "two_d": two_d}


def prepare_adopted_openfoam_run(
    case: dict[str, Any],
    run_dir: Path,
    engine_dir: Path,
    *,
    forces: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """An adopted case runs its OWN dictionaries. Its system/, constant
    properties and 0/ (or 0.orig/) are copied into the run directory, the
    mesh and surfaces are linked, and the adopted copy itself is never
    written into - one case, many runs, each with its own log."""
    run_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("system", "0", "0.orig"):
        src = engine_dir / sub
        if src.is_dir():
            dst = run_dir / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    const_src = engine_dir / "constant"
    const = run_dir / "constant"
    const.mkdir(exist_ok=True)
    if const_src.is_dir():
        for item in const_src.iterdir():
            target = const / item.name
            if target.exists() or target.is_symlink():
                continue
            if item.is_dir():  # polyMesh, triSurface, extendedFeatureEdgeMesh: link, never copy
                os.symlink(item, target, target_is_directory=True)
            else:
                shutil.copyfile(item, target)
    if not (run_dir / "0").is_dir() and (run_dir / "0.orig").is_dir():
        shutil.copytree(run_dir / "0.orig", run_dir / "0")
    control = run_dir / "system" / "controlDict"
    text = control.read_text(errors="replace") if control.is_file() else ""
    app = foam.controldict_application(text) if text else None
    out: dict[str, Any] = {
        "application": app or "simpleFoam",
        "dialect": case.get("adopted", {}).get("dialect"),
    }
    if forces:
        out["forces"] = _add_adopted_forces(case, run_dir, text, forces)
    return out


def check_forces(
    case: dict[str, Any], forces: dict[str, Any]
) -> tuple[list[str], tuple[float, float, float]]:
    """The part of `forces=` that can be judged before the job starts: which
    patches to integrate and which freestream velocity to build the wind
    axes from. Refuses at submit time, never inside the job."""
    adopted = case.get("adopted", {})
    walls = [n for n, t in adopted.get("patches", []) if t == "wall"]
    patches = [str(p) for p in (forces.get("patches") or walls)]
    if not patches:
        raise TeeError(
            "wt_refs_needed",
            "forces= needs the wall patches to integrate (the case declares none of type wall).",
            fix='forces={"patches": ["walls"], "lRef": 1.0}',
        )
    U = forces.get("U") or adopted.get("inlet_U")
    if not U or len(U) < 2:
        raise TeeError(
            "wt_refs_needed",
            "forces= needs the freestream velocity (the 0/U file had no uniform value).",
            fix='forces={"patches": [...], "U": [25.75, 3.62, 0]}',
        )
    ux, uy = float(U[0]), float(U[1])
    uz = float(U[2]) if len(U) > 2 else 0.0
    if math.sqrt(ux * ux + uy * uy + uz * uz) <= 0:
        raise TeeError("wt_refs_needed", "forces= velocity is zero.", fix="Give U=[...].")
    return patches, (ux, uy, uz)


def _add_adopted_forces(
    case: dict[str, Any], run_dir: Path, control_text: str, forces: dict[str, Any]
) -> dict[str, Any]:
    """`wt_run forces={patches, lRef, Aref?, U?, CofR?}` on an adopted case:
    a forceCoeffs function object goes into the RUN copy's controlDict (the
    adopted source is never touched). Wind axes come from the inlet velocity
    the adoption summary read; a 2-D slab's Aref is lRef x the mesh depth."""
    adopted = case.get("adopted", {})
    patches, (ux, uy, uz) = check_forces(case, forces)
    mag = math.sqrt(ux * ux + uy * uy + uz * uz)
    drag = (ux / mag, uy / mag, uz / mag)
    lift = (-uy / mag, ux / mag, 0.0)  # normal to the freestream in the x-y plane
    # the reference length is MEASURED from the wall patches when not given:
    # the apt airFoil2D tutorial's section is 35 m long, and lRef = 1 there
    # returned Cl 34 (a declaration is a claim; the mesh is the evidence)
    bbox = foam.patch_bbox(run_dir / "constant" / "polyMesh", patches)
    lref_source = "given"
    lref = forces.get("lRef")
    if lref is None:
        if bbox:
            lref = bbox[1][0] - bbox[0][0]
            lref_source = "measured: x extent of the wall patches"
        else:
            lref = 1.0
            lref_source = "assumed 1.0 (binary mesh or unknown patch: give lRef)"
    lref = float(lref)
    two_d = any(t == "empty" for _, t in adopted.get("patches", []))
    aref = forces.get("Aref")
    depth = None
    if aref is None and two_d:
        depth = (bbox[1][2] - bbox[0][2]) if bbox else None
        if not depth:
            depth = foam.slab_thickness(run_dir / "constant" / "polyMesh")
        if depth:
            aref = lref * depth
    if aref is None:
        raise TeeError(
            "wt_refs_needed",
            "forces= needs Aref for this case (not a 2-D slab with an ASCII mesh).",
            fix='forces={"patches": [...], "lRef": 1.0, "Aref": <m^2>}',
        )
    if forces.get("CofR"):
        cofr = tuple(float(x) for x in forces["CofR"])
    elif bbox:
        cofr = (
            bbox[0][0] + 0.25 * lref,
            0.5 * (bbox[0][1] + bbox[1][1]),
            0.5 * (bbox[0][2] + bbox[1][2]),
        )
    else:
        cofr = (0.25 * lref, 0.0, 0.0)
    block = foam.force_coeffs_block(
        patches=patches,
        magUInf=mag,
        lRef=lref,
        Aref=float(aref),
        liftDir=lift,
        dragDir=drag,
        CofR=cofr,
    )
    try:
        new_text = foam.add_functions(control_text, block)
    except ValueError as exc:
        raise TeeError(
            "wt_refs_needed",
            str(exc),
            fix="Edit the case's own controlDict, then adopt it again.",
        ) from exc
    (run_dir / "system" / "controlDict").write_text(new_text)
    return {
        "patches": patches,
        "magUInf": round(mag, 6),
        "lRef": round(lref, 6),
        "lRef_source": lref_source,
        "Aref": round(float(aref), 9),
        "slab_depth_m": depth,
        "wall_bbox": [[round(v, 6) for v in bbox[0]], [round(v, 6) for v in bbox[1]]]
        if bbox
        else None,
        "CofR": [round(x, 6) for x in cofr],
        "liftDir": [round(x, 6) for x in lift],
        "dragDir": [round(x, 6) for x in drag],
    }


def mpi_env(cores: int) -> dict[str, str]:
    """Open MPI refuses to run as root unless told twice (measured 2026-09-06:
    a 2-core simpleFoam died in 1.1 s inside this root container with its
    'We strongly suggest that you run mpirun as a non-root user' banner).
    Containers and CI runners are root; a workstation is not. The override
    is set only for root and only for a parallel run, and the run record
    says so."""
    if cores > 1 and hasattr(os, "geteuid") and os.geteuid() == 0:
        return {"OMPI_ALLOW_RUN_AS_ROOT": "1", "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1"}
    return {}


def openfoam_argv(install: Any, run_dir: Path, cores: int, app: str = "simpleFoam") -> list[Step]:
    c = str(run_dir)
    if cores > 1:
        return [
            ("decomposePar", install.argv("decomposePar", "-case", c, "-force")),
            (app, install.parallel_argv(app, cores, "-case", c)),
            ("reconstructPar", install.argv("reconstructPar", "-case", c, "-latestTime")),
        ]
    return [(app, install.argv(app, "-case", c))]


def openfoam_progress(run_dir: Path, log_tail: str) -> dict[str, Any]:
    parsed = foam.parse_log(log_tail)
    out: dict[str, Any] = {}
    if parsed["times"]:
        out["iter"] = int(parsed["times"][-1])
        out["residuals"] = {k: v[-1] for k, v in list(parsed["residuals"].items())[:8]}
    if parsed["fatal"]:
        out["fatal"] = True
    if parsed["bounded"]:
        out["bounded"] = parsed["bounded"]
    files = foam.find_coefficient_files(run_dir)
    if files:
        try:
            data = foam.read_coefficients(files[-1])
        except ValueError:
            data = {"rows": []}
        rows = data["rows"]
        if rows:
            last = rows[-1]
            out["coeffs"] = {k: round(last[k], 5) for k in ("cl", "cd", "cm") if k in last}
            out["iter"] = int(last.get("Time", out.get("iter", 0)))
            if len(rows) >= 50:
                a, b = rows[-50], rows[-1]
                out["trend"] = {
                    "cl_delta_50": round(b.get("cl", 0) - a.get("cl", 0), 5),
                    "cd_delta_50": round(b.get("cd", 0) - a.get("cd", 0), 5),
                }
    return out


def openfoam_result(
    run_dir: Path,
    *,
    iters: int,
    window_pct: float = 20.0,
    ended: bool,
    fatal: bool,
    cancelled: bool,
    app: str = "simpleFoam",
) -> dict[str, Any]:
    log_path = run_dir / f"log.{app}"
    log_text = log_path.read_text(errors="replace") if log_path.is_file() else ""
    parsed = foam.parse_log(log_text)
    files = foam.find_coefficient_files(run_dir)
    if not files:
        if not parsed["times"]:
            raise TeeError(
                "wt_no_results",
                f"No coefficient file under {run_dir}/postProcessing and no time step in "
                "the log yet.",
                fix="Poll wt_status; the first row appears after the first iteration.",
            )
        # the solver ran but nothing integrated forces (an adopted case without
        # a forceCoeffs entry): a residual-only verdict, never an invented number
        ver = verdict.verdict(
            parsed["residuals"],
            {},
            ended=ended or parsed["ended"],
            fatal=fatal or parsed["fatal"],
            cancelled=cancelled,
            window_pct=window_pct,
        )
        ver["notes"].append("residuals only: the case wrote no force coefficients")
        return {
            "cl": None,
            "cd": None,
            "cm": None,
            "iters_used": len(parsed["times"]),
            "verdict": ver,
            "note": "no forceCoeffs function object in this case; on an adopted case "
            'wt_run forces={"patches": [...], "lRef": ...} adds one to the run copy',
            "residuals_last": {k: v[-1] for k, v in parsed["residuals"].items()},
        }
    data = foam.read_coefficients(files[-1])
    rows = data["rows"]
    if not rows:
        raise TeeError(
            "wt_no_results",
            f"{files[-1].name} has a header but no rows yet.",
            fix="Poll wt_status; the first row appears after the first iteration.",
        )
    coeffs = {k: [r[k] for r in rows if k in r] for k in ("cl", "cd", "cm")}
    coeffs = {k: v for k, v in coeffs.items() if v}
    ver = verdict.verdict(
        parsed["residuals"],
        coeffs,
        ended=ended or parsed["ended"],
        fatal=fatal or parsed["fatal"],
        cancelled=cancelled,
        window_pct=window_pct,
    )
    window = max(50, int(len(rows) * window_pct / 100.0))
    tail = rows[-window:]

    def mean(key: str) -> float | None:
        vals = [r[key] for r in tail if key in r]
        return round(sum(vals) / len(vals), 6) if vals else None

    cl, cd, cm = mean("cl"), mean("cd"), mean("cm")
    res: dict[str, Any] = {
        "cl": cl,
        "cd": cd,
        "cm": cm,
        "iters_used": len(rows),
        "coefficient_file": str(files[-1].relative_to(run_dir)),
        "columns": data["columns"][:16],
    }
    if "Cd(f)" in rows[-1] or "Cd(r)" in rows[-1]:
        res["cd_front"] = mean("Cd(f)")
        res["cd_rear"] = mean("Cd(r)")
    if cl is not None and cd:
        res["l_over_d"] = round(cl / cd, 3)
    res["verdict"] = ver
    res["residuals_last"] = {k: v[-1] for k, v in parsed["residuals"].items()}
    return res


def prepare_su2_run(
    case: dict[str, Any],
    run_dir: Path,
    engine_dir: Path,
    *,
    aoa_deg: float,
    iters: int,
    solver: str,
) -> dict[str, Any]:
    cond = case["conditions"]
    refs = case["refs"]
    mesh_file = case["mesh"]["su2_file"]
    run_dir.mkdir(parents=True, exist_ok=True)
    viscous = solver in ("RANS", "NAVIER_STOKES")
    setup = su2.Su2Setup(
        mesh_file=str(mesh_file),
        solver=solver,
        mach=float(cond["mach"]),
        aoa_deg=aoa_deg,
        reynolds=float(cond["Re"]) if viscous else None,
        turbulence=case.get("turbulence_su2", "SA"),
        freestream_T_K=float(cond["T_K"]),
        freestream_p_Pa=float(cond["p_Pa"]),
        ref_length=float(refs["cref"]),
        ref_area=float(refs["Sref"]),
        ref_origin=(0.25 * float(refs["cref"]), 0.0, 0.0),
        iters=iters,
        conv_residual_minval=-8.0 if not viscous else -7.0,
    )
    lines = su2.write_cfg(run_dir / "case.cfg", setup)
    return {"cfg_lines": len(lines), "solver": solver}


def su2_argv(su2_bin: str, run_dir: Path, cores: int) -> list[Step]:
    if cores > 1 and shutil.which("mpirun"):
        return [("SU2_CFD", ["mpirun", "-np", str(cores), su2_bin, "case.cfg"])]
    return [("SU2_CFD", [su2_bin, "case.cfg"])]


def su2_progress(run_dir: Path, log_tail: str) -> dict[str, Any]:
    scr = su2.parse_screen_log(log_tail)
    out: dict[str, Any] = {}
    if scr["rows"]:
        last = scr["rows"][-1]
        out["iter"] = int(last.get("Inner_Iter", 0))
        out["residuals"] = {k: round(v, 3) for k, v in last.items() if k.startswith("rms[")}
        out["coeffs"] = {k: round(last[k], 5) for k in ("cl", "cd") if k in last}
        if len(scr["rows"]) >= 50:
            a, b = scr["rows"][-50], last
            out["trend"] = {
                "cl_delta_50": round(b.get("cl", 0) - a.get("cl", 0), 5),
                "cd_delta_50": round(b.get("cd", 0) - a.get("cd", 0), 5),
            }
    if scr["error"]:
        out["fatal"] = True
        out["error"] = scr["error"]
    return out


def su2_result(
    run_dir: Path, *, window_pct: float = 20.0, ended: bool, fatal: bool, cancelled: bool
) -> dict[str, Any]:
    hist = run_dir / "history.csv"
    if not hist.is_file():
        raise TeeError(
            "wt_no_results", "SU2 has not written history.csv yet.", fix="Poll wt_status."
        )
    data = su2.read_history(hist)
    rows = data["rows"]
    if not rows:
        raise TeeError("wt_no_results", "history.csv has no rows yet.", fix="Poll wt_status.")
    log_text = (
        tail_text(run_dir / "log.SU2_CFD", 2_000_000) if (run_dir / "log.SU2_CFD").is_file() else ""
    )
    scr = su2.parse_screen_log(log_text)
    residuals = {
        k: [10.0 ** r[k] for r in rows if k in r] for k in data["columns"] if k.startswith("rms[")
    }
    coeffs = {k: [r[k] for r in rows if k in r] for k in ("cl", "cd", "cm")}
    coeffs = {k: v for k, v in coeffs.items() if v}
    ver = verdict.verdict(
        residuals,
        coeffs,
        ended=ended or scr["converged"] or scr["max_iter"],
        fatal=fatal or bool(scr["error"]),
        cancelled=cancelled,
        window_pct=window_pct,
        orders_required=3.0,
    )
    if scr["converged"] and ver["state"] in ("stalled", "insufficient"):
        ver["state"] = "converged"
        ver["notes"].append("SU2's own convergence criterion was met")
    window = max(50, int(len(rows) * window_pct / 100.0))
    tail = rows[-window:]

    def mean(key: str) -> float | None:
        vals = [r[key] for r in tail if key in r]
        return round(sum(vals) / len(vals), 6) if vals else None

    cl, cd, cm = mean("cl"), mean("cd"), mean("cm")
    res: dict[str, Any] = {
        "cl": cl,
        "cd": cd,
        "cm": cm,
        "iters_used": len(rows),
        "columns": data["columns"][:20],
        "verdict": ver,
    }
    if cl is not None and cd:
        res["l_over_d"] = round(cl / cd, 3)
    res["residuals_last"] = {k: rows[-1][k] for k in data["columns"] if k.startswith("rms[")}
    vol = run_dir / "flow.vtu"
    if vol.is_file():
        res["volume_file"] = str(vol)
    return res


def prepare_vsp_run(
    case: dict[str, Any],
    run_dir: Path,
    engine_dir: Path,
    *,
    alphas: list[float],
    mach: float,
    re_cref: float | None,
    ncpu: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    src = Path(case["geometry"]["vsp3"])
    dst = run_dir / "model.vsp3"
    shutil.copyfile(src, dst)
    script = vsp.sweep_script("model.vsp3", alphas=alphas, mach=mach, re_cref=re_cref, ncpu=ncpu)
    (run_dir / "sweep.vspscript").write_text(script)
    return {"alphas": alphas, "mach": mach}


def vsp_argv(vspscript: str, run_dir: Path) -> list[Step]:
    return [("vspscript", [vspscript, "-script", "sweep.vspscript"])]


def vsp_progress(run_dir: Path, log_tail: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if "DONE" in log_tail:
        out["phase"] = "done"
    elif "POLAR=" in log_tail:
        out["phase"] = "results"
    elif "VSPAERO" in log_tail:
        out["phase"] = "solving"
    else:
        out["phase"] = "geometry"
    if "ERROR" in log_tail or "Error" in log_tail:
        out["warnings"] = [ln.strip()[:120] for ln in log_tail.splitlines() if "rror" in ln][:4]
    return out


def vsp_result(run_dir: Path, *, ended: bool, fatal: bool, cancelled: bool) -> dict[str, Any]:
    polars = sorted(run_dir.glob("*.polar"))
    if not polars:
        log = tail_text(run_dir / "log.vspscript", 4000)
        raise TeeError(
            "wt_no_results",
            "VSPAERO wrote no .polar file.",
            fix=f"Last log lines: {' | '.join(log.strip().splitlines()[-3:])[:300]}",
        )
    data = vsp.read_polar(polars[-1])
    rows = data["rows"]
    # vspscript exits 2 after a complete run (measured 2026-09-06, OpenVSP
    # 3.51.3): the exit code is a claim, the polar and the script's own DONE
    # line are the evidence.
    if fatal and "DONE" in tail_text(run_dir / "log.vspscript", 2000):
        fatal = False
    polar = [
        {
            "aoa_deg": r.get("alpha"),
            "mach": r.get("mach"),
            "cl": round(r.get("cl", 0.0), 6),
            "cd": round(r.get("cd", 0.0), 6),
            "cdi": round(r.get("cdi", 0.0), 6),
            "cdo": round(r.get("cdo", 0.0), 6),
            "l_over_d": round(r.get("l_over_d", 0.0), 3),
            "e": round(r.get("e", 0.0), 4),
            "state": "converged",
        }
        for r in rows
    ]
    state = "converged" if rows and not fatal else ("cancelled" if cancelled else "error")
    res: dict[str, Any] = {
        "polar": polar,
        "points": len(polar),
        "verdict": {
            "state": state,
            "notes": [
                "vortex lattice: no iteration history; wake relaxed for the configured iterations"
            ],
        },
    }
    if len(polar) >= 2:
        a, b = polar[0], polar[-1]
        da = math.radians(b["aoa_deg"] - a["aoa_deg"])
        if abs(da) > 1e-9:
            res["cl_alpha_per_rad"] = round((b["cl"] - a["cl"]) / da, 4)
    if polar:
        last = polar[-1]
        res.update(
            {
                "cl": last["cl"],
                "cd": last["cd"],
                "cm": None,
                "l_over_d": last["l_over_d"],
                "aoa_deg": last["aoa_deg"],
            }
        )
        res["cd_min"] = min(p["cd"] for p in polar)
    return res


# ---------------------------------------------------------------------------
# Geometry intake
# ---------------------------------------------------------------------------


def section_from(args: dict[str, Any], geom_dir: Path) -> dict[str, Any]:
    """`naca=` or `dat=` -> a chord-normalised loop stored with the case."""
    if args.get("naca"):
        code = str(args["naca"])
        loop = airfoil.naca4(code, int(args.get("n_surface", 100)))
        name = f"NACA {code}"
    elif args.get("dat"):
        name, loop = airfoil.read_selig(Path(str(args["dat"])).expanduser())
        xs = [p[0] for p in loop]
        chord = max(xs) - min(xs)
        x0 = min(xs)
        loop = [((x - x0) / chord, y / chord) for x, y in loop]
    else:
        raise TeeError(
            "wt_geometry_missing",
            "A 2-D section needs naca= (four digits) or dat= (a Selig file).",
            fix="e.g. naca='0012' or dat='~/foils/e387.dat'",
        )
    loop = airfoil.ccw(loop)
    props = airfoil.properties(loop)
    airfoil.write_selig(geom_dir / "section.dat", loop, name)
    return {
        "kind": "airfoil2d",
        "name": name,
        "loop": loop,
        "properties": props,
        "dat": str(geom_dir / "section.dat"),
    }


def body_from_stl(path: Path, geom_dir: Path, units: str) -> dict[str, Any]:
    scale = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254, "ft": 0.3048}.get(units)
    if scale is None:
        raise TeeError(
            "wt_bad_units",
            f"'{units}' is not a unit this lane knows.",
            fix="One of: m, cm, mm, in, ft.",
        )
    surf = physics.read_stl(path)
    if scale != 1.0:
        surf.tris = [
            tuple((p[0] * scale, p[1] * scale, p[2] * scale) for p in t) for t in surf.tris
        ]
    bbox = surf.bbox
    warn = physics.units_sanity(bbox)
    watertight, open_edges = surf.watertight()
    dst = geom_dir / "body.stl"
    physics.write_stl_ascii(dst, surf.tris, name="body")
    frontal = surf.projected_area(axis=0)
    planform = surf.projected_area(axis=2)
    (x0, y0, z0), (x1, y1, z1) = bbox
    return {
        "kind": "body3d",
        "name": path.stem,
        "stl": str(dst),
        "source": str(path),
        "units": units,
        "bbox": [list(bbox[0]), list(bbox[1])],
        "length_m": x1 - x0,
        "width_m": y1 - y0,
        "height_m": z1 - z0,
        "tris": len(surf.tris),
        "watertight": watertight,
        "open_edges": open_edges,
        "frontal_area_m2": round(frontal, 6),
        "planform_area_m2": round(planform, 6),
        "wetted_area_m2": round(surf.area, 6),
        "warning": warn,
    }


def wing_from_spec(args: dict[str, Any]) -> vsp.WingSpec:
    w = args.get("wing") or {}
    if not isinstance(w, dict) or "span" not in w or "root_chord" not in w:
        raise TeeError(
            "wt_geometry_missing",
            "wing= needs at least span and root_chord (metres).",
            fix='e.g. wing={"span": 1.2, "root_chord": 0.25, "taper": 0.6, "sweep_deg": 5, '
            '"airfoil": "2412"}',
        )
    root = float(w["root_chord"])
    tip = float(w["tip_chord"]) if "tip_chord" in w else root * float(w.get("taper", 1.0))
    return vsp.WingSpec(
        span=float(w["span"]),
        root_chord=root,
        tip_chord=tip,
        sweep_deg=float(w.get("sweep_deg", 0.0)),
        dihedral_deg=float(w.get("dihedral_deg", 0.0)),
        twist_deg=float(w.get("twist_deg", 0.0)),
        airfoil=str(w.get("airfoil", "0012")),
    )


def load_progress(run_dir: Path) -> dict[str, Any] | None:
    return read_json(run_dir / "progress.json")


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=1, default=str))
