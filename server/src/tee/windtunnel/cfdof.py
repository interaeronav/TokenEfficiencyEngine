"""Adopting a case somebody else wrote: FreeCAD's CfdOF workbench, a hand-made
case, a tutorial. The case directory is the interface.

TEE never executes a case's own `Allrun`/`Allmesh`: it reads the
`runApplication <binary>` lines to learn the intended sequence and later
runs those KNOWN binaries with argv it composed itself (the pipeline lane's
argv-only law). What adoption reports is what the dictionaries say - the
solver, the turbulence model, the patches and their conditions, the inlet
velocity, whether a forceCoeffs function object exists - never a cell.

The optional RPC route (asking a running FreeCAD, through TEE's one bridge,
where a CfdAnalysis wrote its case) is imported lazily and only when asked;
whether CfdOF's writer runs headless is an owner-session probe (script §M,
rows C1-C3), so nothing here assumes it.
"""

from __future__ import annotations

import contextlib
import re
import shutil
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.windtunnel import foam

KNOWN_BINARIES = {
    "blockMesh",
    "snappyHexMesh",
    "surfaceFeatureExtract",
    "surfaceFeatures",
    "cartesianMesh",
    "checkMesh",
    "decomposePar",
    "reconstructPar",
    "renumberMesh",
    "potentialFoam",
    "simpleFoam",
    "pisoFoam",
    "pimpleFoam",
    "rhoSimpleFoam",
    "rhoPimpleFoam",
    "hisa",
    "gmsh",
    "extrudeMesh",
    "createPatch",
    "transformPoints",
    "foamDictionary",
    "postProcess",
}


def detect(path: Path) -> str:
    """'openfoam' | 'su2' | 'vsp3' | refuse."""
    if path.is_dir() and (path / "system" / "controlDict").is_file():
        return "openfoam"
    if path.is_file() and path.suffix == ".cfg":
        text = path.read_text(errors="replace")
        if "MESH_FILENAME" in text:
            return "su2"
    if path.is_file() and path.suffix == ".vsp3":
        from tee.windtunnel.vsp import vsp3_is_model

        if vsp3_is_model(path):
            return "vsp3"
    raise TeeError(
        "wt_not_a_case",
        f"{path} is not an OpenFOAM case (system/controlDict), an SU2 .cfg (MESH_FILENAME=) "
        "or an OpenVSP .vsp3.",
        fix="Point adopt= at the case directory itself, the .cfg, or the .vsp3.",
    )


def summarise_openfoam(case_dir: Path) -> dict[str, Any]:
    control = (case_dir / "system" / "controlDict").read_text(errors="replace")
    out: dict[str, Any] = {"solver": foam.controldict_application(control)}
    out["has_forceCoeffs"] = "forceCoeffs" in control or any(
        "forceCoeffs" in p.read_text(errors="replace")
        for p in (case_dir / "system").glob("*")
        if p.is_file() and p.stat().st_size < 200_000
    )
    turb = case_dir / "constant" / "turbulenceProperties"
    momentum = case_dir / "constant" / "momentumTransport"
    if turb.is_file():
        m = re.search(r"RASModel\s+(\w+)", turb.read_text(errors="replace"))
        out["turbulence"] = (
            m.group(1)
            if m
            else ("laminar" if "laminar" in turb.read_text(errors="replace") else "unknown")
        )
        out["dialect"] = "com"
    elif momentum.is_file():
        m = re.search(r"model\s+(\w+)", momentum.read_text(errors="replace"))
        out["turbulence"] = m.group(1) if m else "unknown"
        out["dialect"] = "org"
    else:
        out["dialect"] = "unknown"
    boundary = case_dir / "constant" / "polyMesh" / "boundary"
    out["has_mesh"] = boundary.is_file()
    if boundary.is_file():
        out["patches"] = foam.patch_names(boundary.read_text(errors="replace"))[:64]
    tri = case_dir / "constant" / "triSurface"
    out["stl_files"] = sorted(p.name for p in tri.glob("*.stl"))[:16] if tri.is_dir() else []
    out["has_snappy"] = (case_dir / "system" / "snappyHexMeshDict").is_file()
    out["has_blockMesh"] = (case_dir / "system" / "blockMeshDict").is_file()
    zero = case_dir / "0"
    if not zero.is_dir() and (case_dir / "0.orig").is_dir():
        zero = case_dir / "0.orig"
    if (zero / "U").is_file():
        text = (zero / "U").read_text(errors="replace")
        m = re.search(r"internalField\s+uniform\s*\(([^)]*)\)", text)
        if m:
            with contextlib.suppress(ValueError):
                out["inlet_U"] = [float(x) for x in m.group(1).split()]
        out["U_bcs"] = foam.field_bcs(text)
    seq: list[list[str]] = []
    for name in ("Allrun", "Allmesh", "Allrun.pre", "Allrun-parallel"):
        script = case_dir / name
        if script.is_file():
            seq += foam.solver_sequence(script.read_text(errors="replace"))
    out["sequence"] = [s for s in seq if s and s[0] in KNOWN_BINARIES][:16]
    out["unknown_in_scripts"] = sorted({s[0] for s in seq if s and s[0] not in KNOWN_BINARIES})[:8]
    out["cfdof"] = any(
        ("CfdOF" in (case_dir / n).read_text(errors="replace"))
        for n in ("Allrun", "Allmesh")
        if (case_dir / n).is_file()
    )
    return out


def copy_case(src: Path, dst: Path) -> dict[str, Any]:
    """Copy the case (never mutate the source); skip nothing but a huge
    processor*/ decomposition and VTK dumps."""
    if dst.exists():
        shutil.rmtree(dst)

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n.startswith("processor") or n in ("VTK", "postProcessing.old")}

    shutil.copytree(src, dst, ignore=ignore, symlinks=True)
    size = sum(p.stat().st_size for p in dst.rglob("*") if p.is_file())
    return {"copied_from": str(src), "bytes": size}


def rpc_case_path(document: str) -> str:
    """Ask a running FreeCAD (through TEE's one bridge) where a CfdOF
    analysis in `document` writes its case. Lazy import; refuses with the
    bridge's own error when FreeCAD is not up."""
    from tee.adapters.freecad.wire import FreeCADWire

    wire = FreeCADWire()
    code = (
        "import FreeCAD, json\n"
        f"doc = FreeCAD.getDocument({document!r})\n"
        "paths = [o.OutputPath for o in doc.Objects if hasattr(o, 'OutputPath')]\n"
        "print(json.dumps({'paths': paths}))\n"
    )
    result = wire.py_json(code)
    paths = result.get("paths") or []
    if not paths:
        raise TeeError(
            "wt_not_a_case",
            f"FreeCAD document {document} has no CfdOF analysis with an OutputPath.",
            fix="Create the CfdAnalysis in CfdOF and write the case once; then adopt its "
            "directory.",
        )
    return str(paths[0])
