"""OpenFOAM at arm's length: the case TEE writes, the files TEE reads, and
the one invocation form that works on both platforms.

OpenFOAM is GPL-3 and stays a separate process; nothing here imports it and
no tutorial file is copied. The dictionaries below are written from scratch
in the openfoam.com dialect that was MEASURED (v1912 in the Linux container,
v2606 in the Mac app - research doc 72 §3); the Foundation dialect (OpenFOAM
11+ renamed the solvers and the property files) is refused by name until it
is measured too.

Readers never trust a column position: the coefficient file's own header
line names the columns, and the residual scraper reads the solver's log.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Vec3 = tuple[float, float, float]

GENERATED_BY = "generated-by: tee.windtunnel.foam"

# ---------------------------------------------------------------------------
# Dictionary serialiser (a strict subset of the OpenFOAM dictionary syntax)
# ---------------------------------------------------------------------------


def _fmt(value: Any, indent: int = 0) -> str:
    pad = "    " * indent
    if isinstance(value, dict):
        out = ["{"]
        width = max((len(k) for k in value), default=0)
        for k, v in value.items():
            if isinstance(v, dict):
                out.append(f"{pad}    {k}")
                out.append(f"{pad}    " + _fmt(v, indent + 1))
            else:
                out.append(f"{pad}    {k.ljust(width + 2)}{_fmt(v, indent + 1)};")
        out.append(f"{pad}}}")
        return "\n".join(out)
    if isinstance(value, tuple):  # a vector / a bare list of words
        return "(" + " ".join(_scalar(v) for v in value) + ")"
    if isinstance(value, list):  # an OpenFOAM list, one entry per line
        if not value:
            return "()"
        inner = []
        for v in value:
            if isinstance(v, dict):
                inner.append(f"{pad}    " + _fmt(v, indent + 1))
            else:
                inner.append(f"{pad}    {_fmt(v, indent + 1)}")
        return "(\n" + "\n".join(inner) + f"\n{pad})"
    return _scalar(value)


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.10g}"
    if isinstance(v, tuple):
        return "(" + " ".join(_scalar(x) for x in v) + ")"
    return str(v)


def foam_file(
    cls: str, obj: str, body: dict[str, Any], location: str | None = None, preamble: str = ""
) -> str:
    """A complete OpenFOAM file: banner comment, FoamFile header, entries."""
    header = {"version": "2.0", "format": "ascii", "class": cls}
    if location:
        header["location"] = f'"{location}"'
    header["object"] = obj
    lines = [
        "/*--------------------------------*- C++ -*----------------------------------*\\",
        f"| {GENERATED_BY:<76} |",
        "\\*---------------------------------------------------------------------------*/",
        "FoamFile",
        _fmt(header),
        "",
    ]
    if preamble:
        lines.append(preamble.rstrip("\n"))
        lines.append("")
    for k, v in body.items():
        if isinstance(v, dict):
            lines.append(k)
            lines.append(_fmt(v))
        elif isinstance(v, str) and v.startswith("#"):
            lines.append(v)  # a directive line such as #includeEtc
        else:
            lines.append(f"{k.ljust(max(16, len(k) + 1))}{_fmt(v)};")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# What a case is, physically
# ---------------------------------------------------------------------------


@dataclass
class FoamSetup:
    U_inf: Vec3  # m/s, wind axes already applied (see physics.wind_axes)
    nu: float  # m^2/s
    turbulence: str = "kOmegaSST"  # or "laminar"
    wall_treatment: str = "low_re"  # "low_re" (y+ ~ 1) or "wall_function" (y+ 30..300)
    turbulence_intensity: float = 0.01
    viscosity_ratio: float = 10.0  # nut / nu in the freestream (ERCOFTAC BPG range 1..100)
    end_time: int = 2000
    write_interval: int = 500
    residual_target: float = 1e-5
    # force coefficient reference (forceCoeffs function object)
    Aref: float = 1.0
    lRef: float = 1.0
    CofR: Vec3 = (0.25, 0.0, 0.0)
    liftDir: Vec3 = (0.0, 1.0, 0.0)
    dragDir: Vec3 = (1.0, 0.0, 0.0)
    pitchAxis: Vec3 = (0.0, 0.0, 1.0)
    rho_inf: float = 1.0
    cores: int = 1
    # patch names by role
    wall_patches: tuple[str, ...] = ("airfoil",)
    freestream_patches: tuple[str, ...] = ("farfield",)
    inlet_patches: tuple[str, ...] = ()
    outlet_patches: tuple[str, ...] = ()
    slip_patches: tuple[str, ...] = ()
    empty_patches: tuple[str, ...] = ("frontAndBack",)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def magU(self) -> float:
        return math.sqrt(sum(c * c for c in self.U_inf))

    @property
    def k_inf(self) -> float:
        return 1.5 * (self.turbulence_intensity * self.magU) ** 2

    @property
    def omega_inf(self) -> float:
        return self.k_inf / (self.viscosity_ratio * self.nu)


def write_case(case_dir: str | Path, setup: FoamSetup) -> list[str]:
    """Write system/, constant/ (properties only; the mesh is someone else's)
    and 0/. Returns the files written, relative to the case."""
    root = Path(case_dir)
    written: list[str] = []

    def put(rel: str, text: str) -> None:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        written.append(rel)

    put("system/controlDict", control_dict(setup))
    put("system/fvSchemes", fv_schemes(setup))
    put("system/fvSolution", fv_solution(setup))
    put("constant/transportProperties", transport_properties(setup))
    put("constant/turbulenceProperties", turbulence_properties(setup))
    if setup.cores > 1:
        put("system/decomposeParDict", decompose_par_dict(setup.cores))
    for name, text in fields_0(setup).items():
        put(f"0/{name}", text)
    return written


def write_mesh_system(case_dir: str | Path) -> list[str]:
    """The three `system/` files every OpenFOAM utility insists on, for a
    directory that only holds a mesh: blockMesh, snappyHexMesh and checkMesh
    run here, the solver runs elsewhere with dictionaries of its own. No
    function objects - the patches they would name do not exist yet."""
    stub = FoamSetup(U_inf=(1.0, 0.0, 0.0), nu=1.5e-5)
    root = Path(case_dir)
    written: list[str] = []
    for rel, text in (
        ("system/controlDict", control_dict(stub, functions=False)),
        ("system/fvSchemes", fv_schemes(stub)),
        ("system/fvSolution", fv_solution(stub)),
    ):
        p = root / rel
        if p.is_file():
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        written.append(rel)
    return written


def slab_thickness(polymesh_dir: str | Path) -> float | None:
    """The z extent of an ASCII polyMesh's points: a 2-D case is one cell
    thick, and forceCoeffs' Aref for it is chord x that depth. None for a
    binary points file (the caller then asks for Aref)."""
    pts = Path(polymesh_dir) / "points"
    if not pts.is_file():
        return None
    zmin, zmax = math.inf, -math.inf
    with open(pts, errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("(") and s.endswith(")"):
                parts = s[1:-1].split()
                if len(parts) == 3:
                    try:
                        z = float(parts[2])
                    except ValueError:
                        continue
                    zmin, zmax = min(zmin, z), max(zmax, z)
    return zmax - zmin if zmax >= zmin else None


def _list_body(text: str) -> list[str]:
    """The entries of an ASCII OpenFOAM list file: the lines between the
    `(` that follows the count and the closing `)`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().isdigit() and i + 1 < len(lines) and lines[i + 1].strip() == "(":
            body: list[str] = []
            for entry in lines[i + 2 :]:
                if entry.strip() == ")":
                    return body
                body.append(entry)
            return body
    return []


def patch_bbox(polymesh_dir: str | Path, patches: Sequence[str]) -> tuple[Vec3, Vec3] | None:
    """The bounding box of the points on the named patches of an ASCII
    polyMesh: a wall's chord, its span and a 2-D slab's depth MEASURED from
    the mesh rather than declared (the apt airFoil2D tutorial's section is
    35 m long, which no default could have guessed). None for a binary mesh
    or an unknown patch."""
    pm = Path(polymesh_dir)
    try:
        boundary = (pm / "boundary").read_text(errors="replace")
        faces = _list_body((pm / "faces").read_text(errors="replace"))
        points = _list_body((pm / "points").read_text(errors="replace"))
    except OSError:
        return None
    ranges: list[tuple[int, int]] = []
    for name in patches:
        m = re.search(rf"^\s*{re.escape(name)}\s*\n\s*\{{(.*?)\}}", boundary, re.M | re.S)
        if not m:
            continue
        nf = re.search(r"nFaces\s+(\d+)\s*;", m.group(1))
        sf = re.search(r"startFace\s+(\d+)\s*;", m.group(1))
        if nf and sf:
            ranges.append((int(sf.group(1)), int(nf.group(1))))
    if not ranges or not faces or not points:
        return None
    ids: set[int] = set()
    for start, count in ranges:
        for face in faces[start : start + count]:
            inner = face[face.find("(") + 1 : face.rfind(")")]
            for tok in inner.split():
                if tok.isdigit():
                    ids.add(int(tok))
    lo = [math.inf, math.inf, math.inf]
    hi = [-math.inf, -math.inf, -math.inf]
    for pid in ids:
        if pid >= len(points):
            return None
        raw = points[pid].strip()
        parts = raw[1:-1].split() if raw.startswith("(") else []
        if len(parts) != 3:
            return None
        try:
            xyz = [float(p) for p in parts]
        except ValueError:
            return None
        for k in range(3):
            lo[k] = min(lo[k], xyz[k])
            hi[k] = max(hi[k], xyz[k])
    if not ids or lo[0] == math.inf:
        return None
    return (lo[0], lo[1], lo[2]), (hi[0], hi[1], hi[2])


def force_coeffs_block(
    *,
    patches: Sequence[str],
    magUInf: float,
    lRef: float,
    Aref: float,
    liftDir: Vec3,
    dragDir: Vec3,
    CofR: Vec3 = (0.0, 0.0, 0.0),
    pitchAxis: Vec3 = (0.0, 0.0, 1.0),
    rho_inf: float = 1.0,
    name: str = "forceCoeffs1",
) -> str:
    """A `functions { <name> { type forceCoeffs; ... } }` entry, the same
    shape control_dict writes, for a case that has none."""
    fo = {
        "type": "forceCoeffs",
        "libs": ('"libforces.so"',),
        "writeControl": "timeStep",
        "writeInterval": 1,
        "log": "no",
        "patches": tuple(patches),
        "rho": "rhoInf",
        "rhoInf": rho_inf,
        "liftDir": tuple(liftDir),
        "dragDir": tuple(dragDir),
        "CofR": tuple(CofR),
        "pitchAxis": tuple(pitchAxis),
        "magUInf": magUInf,
        "lRef": lRef,
        "Aref": Aref,
    }
    return "functions\n" + _fmt({name: fo}) + "\n"


def add_functions(controldict_text: str, block: str) -> str:
    """Append a functions block to a controlDict that has none, or merge
    into an existing one by inserting the new entry right after its opening
    brace - dictionary entries are order-insensitive, and the case's own
    function objects are kept untouched. (The v2606 app's airFoil2D ships a
    `functions { momErr ... }` block where the apt copy shipped none;
    measured 2026-09-06.)"""
    m = re.search(r"^\s*functions\b", controldict_text, re.M)
    if m is None:
        return controldict_text.rstrip("\n") + "\n\n" + block
    brace = controldict_text.find("{", m.end())
    if brace < 0:
        raise ValueError("the case has a functions entry with no { block")
    inner = block[block.find("{") + 1 : block.rfind("}")].strip("\n")
    return controldict_text[: brace + 1] + "\n" + inner + "\n" + controldict_text[brace + 1 :]


def control_dict(setup: FoamSetup, *, functions: bool = True) -> str:
    function_objects = {
        "forceCoeffs1": {
            "type": "forceCoeffs",
            "libs": ('"libforces.so"',),
            "writeControl": "timeStep",
            "writeInterval": 1,
            "log": "no",
            "patches": tuple(setup.wall_patches),
            "rho": "rhoInf",
            "rhoInf": setup.rho_inf,
            "liftDir": setup.liftDir,
            "dragDir": setup.dragDir,
            "CofR": setup.CofR,
            "pitchAxis": setup.pitchAxis,
            "magUInf": setup.magU,
            "lRef": setup.lRef,
            "Aref": setup.Aref,
        }
    }
    body: dict[str, Any] = {
        "application": "simpleFoam",
        "startFrom": "startTime",
        "startTime": 0,
        "stopAt": "endTime",
        "endTime": setup.end_time,
        "deltaT": 1,
        "writeControl": "timeStep",
        "writeInterval": setup.write_interval,
        "purgeWrite": 2,
        "writeFormat": "ascii",
        "writePrecision": 8,
        "writeCompression": "off",
        "timeFormat": "general",
        "timePrecision": 6,
        "runTimeModifiable": "true",
    }
    if functions:
        body["functions"] = function_objects
    return foam_file("dictionary", "controlDict", body, "system")


def fv_schemes(setup: FoamSetup) -> str:
    turb = setup.turbulence != "laminar"
    div: dict[str, Any] = {"default": "none", "div(phi,U)": "bounded Gauss linearUpwindV grad(U)"}
    if turb:
        div["div(phi,k)"] = "bounded Gauss upwind"
        div["div(phi,omega)"] = "bounded Gauss upwind"
    div["div((nuEff*dev2(T(grad(U)))))"] = "Gauss linear"
    body = {
        "ddtSchemes": {"default": "steadyState"},
        "gradSchemes": {"default": "Gauss linear", "grad(U)": "cellLimited Gauss linear 1"},
        "divSchemes": div,
        "laplacianSchemes": {"default": "Gauss linear corrected"},
        "interpolationSchemes": {"default": "linear"},
        "snGradSchemes": {"default": "corrected"},
        "wallDist": {"method": "meshWave"},
    }
    return foam_file("dictionary", "fvSchemes", body, "system")


def fv_solution(setup: FoamSetup) -> str:
    turb = setup.turbulence != "laminar"
    smooth = {
        "solver": "smoothSolver",
        "smoother": "GaussSeidel",
        "tolerance": 1e-8,
        "relTol": 0.1,
        "nSweeps": 1,
    }
    solvers: dict[str, Any] = {
        "p": {"solver": "GAMG", "smoother": "GaussSeidel", "tolerance": 1e-7, "relTol": 0.01},
        "Phi": {"$p": ""},
        "U": dict(smooth),
    }
    residual: dict[str, Any] = {"p": setup.residual_target, "U": setup.residual_target}
    relax: dict[str, Any] = {"U": 0.9}
    if turb:
        solvers["k"] = dict(smooth)
        solvers["omega"] = dict(smooth)
        residual['"(k|omega)"'] = setup.residual_target
        relax["k"] = 0.7
        relax["omega"] = 0.7
    body = {
        "solvers": solvers,
        "SIMPLE": {"nNonOrthogonalCorrectors": 0, "consistent": "yes", "residualControl": residual},
        "potentialFlow": {"nNonOrthogonalCorrectors": 10},
        "relaxationFactors": {"equations": relax},
        "cache": {"grad(U)": ""},
    }
    text = foam_file("dictionary", "fvSolution", body, "system")
    # `$p;` and `grad(U);` are bare entries; the serialiser wrote `$p ;`
    return text.replace("$p  ;", "$p;").replace("grad(U)  ;", "grad(U);")


def transport_properties(setup: FoamSetup) -> str:
    return foam_file(
        "dictionary",
        "transportProperties",
        {"transportModel": "Newtonian", "nu": setup.nu},
        "constant",
    )


def turbulence_properties(setup: FoamSetup) -> str:
    if setup.turbulence == "laminar":
        body: dict[str, Any] = {"simulationType": "laminar"}
    else:
        body = {
            "simulationType": "RAS",
            "RAS": {"RASModel": setup.turbulence, "turbulence": "on", "printCoeffs": "on"},
        }
    return foam_file("dictionary", "turbulenceProperties", body, "constant")


def decompose_par_dict(cores: int) -> str:
    return foam_file(
        "dictionary",
        "decomposeParDict",
        {"numberOfSubdomains": cores, "method": "scotch"},
        "system",
    )


def _field(
    cls: str, name: str, dims: str, internal: str, patches: dict[str, dict[str, Any]]
) -> str:
    return foam_file(
        cls,
        name,
        {"dimensions": dims, "internalField": internal, "boundaryField": patches},
        "0",
    )


def fields_0(setup: FoamSetup) -> dict[str, str]:
    """The initial and boundary conditions per patch role.

    Freestream patches: freestreamVelocity / freestreamPressure (inlet-outlet
    switching on the local flux, present in both forks); inlets fixedValue;
    outlets inletOutlet / fixedValue p; slip walls `slip`; empty `empty`;
    body walls noSlip with the wall treatment chosen.
    """
    U = tuple(setup.U_inf)
    Ustr = f"uniform ({U[0]:.8g} {U[1]:.8g} {U[2]:.8g})"
    fields: dict[str, str] = {}

    def per_patch(role_map: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for role, entry in role_map.items():
            for name in getattr(setup, role):
                out[name] = dict(entry)
        return out

    u_patches = per_patch(
        {
            "freestream_patches": {"type": "freestreamVelocity", "freestreamValue": Ustr},
            "inlet_patches": {"type": "fixedValue", "value": Ustr},
            "outlet_patches": {
                "type": "inletOutlet",
                "inletValue": "uniform (0 0 0)",
                "value": Ustr,
            },
            "slip_patches": {"type": "slip"},
            "wall_patches": {"type": "noSlip"},
            "empty_patches": {"type": "empty"},
        }
    )
    fields["U"] = _field("volVectorField", "U", "[0 1 -1 0 0 0 0]", Ustr, u_patches)

    p_patches = per_patch(
        {
            "freestream_patches": {"type": "freestreamPressure", "freestreamValue": "uniform 0"},
            "inlet_patches": {"type": "zeroGradient"},
            "outlet_patches": {"type": "fixedValue", "value": "uniform 0"},
            "slip_patches": {"type": "slip"},
            "wall_patches": {"type": "zeroGradient"},
            "empty_patches": {"type": "empty"},
        }
    )
    fields["p"] = _field("volScalarField", "p", "[0 2 -2 0 0 0 0]", "uniform 0", p_patches)

    if setup.turbulence == "laminar":
        return fields

    k = f"uniform {setup.k_inf:.8g}"
    om = f"uniform {setup.omega_inf:.8g}"
    low_re = setup.wall_treatment == "low_re"
    k_wall = (
        {"type": "fixedValue", "value": "uniform 1e-10"}
        if low_re
        else {"type": "kqRWallFunction", "value": k}
    )
    nut_wall = (
        {"type": "nutLowReWallFunction", "value": "uniform 0"}
        if low_re
        else {"type": "nutkWallFunction", "value": "uniform 0"}
    )
    fields["k"] = _field(
        "volScalarField",
        "k",
        "[0 2 -2 0 0 0 0]",
        k,
        per_patch(
            {
                "freestream_patches": {"type": "freestream", "freestreamValue": k},
                "inlet_patches": {"type": "fixedValue", "value": k},
                "outlet_patches": {"type": "inletOutlet", "inletValue": k, "value": k},
                "slip_patches": {"type": "slip"},
                "wall_patches": k_wall,
                "empty_patches": {"type": "empty"},
            }
        ),
    )
    fields["omega"] = _field(
        "volScalarField",
        "omega",
        "[0 0 -1 0 0 0 0]",
        om,
        per_patch(
            {
                "freestream_patches": {"type": "freestream", "freestreamValue": om},
                "inlet_patches": {"type": "fixedValue", "value": om},
                "outlet_patches": {"type": "inletOutlet", "inletValue": om, "value": om},
                "slip_patches": {"type": "slip"},
                "wall_patches": {"type": "omegaWallFunction", "value": om},
                "empty_patches": {"type": "empty"},
            }
        ),
    )
    fields["nut"] = _field(
        "volScalarField",
        "nut",
        "[0 2 -1 0 0 0 0]",
        "uniform 0",
        per_patch(
            {
                "freestream_patches": {"type": "calculated", "value": "uniform 0"},
                "inlet_patches": {"type": "calculated", "value": "uniform 0"},
                "outlet_patches": {"type": "calculated", "value": "uniform 0"},
                "slip_patches": {"type": "slip"},
                "wall_patches": nut_wall,
                "empty_patches": {"type": "empty"},
            }
        ),
    )
    return fields


# ---------------------------------------------------------------------------
# The 3-D tunnel: blockMesh box + snappyHexMesh around an STL
# ---------------------------------------------------------------------------


@dataclass
class Tunnel3D:
    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float
    base_cell: float  # background cell size, m
    body_name: str  # STL stem under constant/triSurface
    body_bbox: tuple[Vec3, Vec3]
    surface_levels: tuple[int, int] = (3, 4)
    region_level: int = 2
    layers: int = 5
    layer_expansion: float = 1.2
    final_layer_rel: float = 0.5
    feature_angle: float = 150.0
    ground: bool = False
    location_in_mesh: Vec3 | None = None


def block_mesh_dict(t: Tunnel3D) -> str:
    nx = max(round((t.xmax - t.xmin) / t.base_cell), 4)
    ny = max(round((t.ymax - t.ymin) / t.base_cell), 4)
    nz = max(round((t.zmax - t.zmin) / t.base_cell), 4)
    verts = [
        (t.xmin, t.ymin, t.zmin),
        (t.xmax, t.ymin, t.zmin),
        (t.xmax, t.ymax, t.zmin),
        (t.xmin, t.ymax, t.zmin),
        (t.xmin, t.ymin, t.zmax),
        (t.xmax, t.ymin, t.zmax),
        (t.xmax, t.ymax, t.zmax),
        (t.xmin, t.ymax, t.zmax),
    ]
    floor_type = "wall" if t.ground else "patch"
    boundary = [
        {"inlet": {"type": "patch", "faces": [(0, 4, 7, 3)]}},
        {"outlet": {"type": "patch", "faces": [(1, 2, 6, 5)]}},
        {"sides": {"type": "patch", "faces": [(0, 1, 5, 4), (3, 7, 6, 2)]}},
        {"top": {"type": "patch", "faces": [(4, 5, 6, 7)]}},
        {"ground": {"type": floor_type, "faces": [(0, 3, 2, 1)]}},
    ]
    body: dict[str, Any] = {
        "scale": 1,
        "vertices": [tuple(v) for v in verts],
        "blocks": [f"hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)"],
        "edges": [],
        "boundary": _boundary_list(boundary),
        "mergePatchPairs": [],
    }
    return foam_file("dictionary", "blockMeshDict", body, "system")


def _boundary_list(entries: list[dict[str, dict[str, Any]]]) -> str:
    """blockMesh's boundary list is `( name { type ..; faces (...); } ... )`."""
    parts = ["("]
    for entry in entries:
        for name, spec in entry.items():
            faces = " ".join("(" + " ".join(str(i) for i in f) + ")" for f in spec["faces"])
            parts.append(
                f"    {name}\n    {{\n        type {spec['type']};\n        faces\n"
                f"        (\n            {faces}\n        );\n    }}"
            )
    parts.append(")")
    return "\n".join(parts)


def snappy_dict(t: Tunnel3D) -> str:
    (bx0, by0, bz0), (bx1, by1, bz1) = t.body_bbox
    L = max(bx1 - bx0, by1 - by0, bz1 - bz0)
    loc = t.location_in_mesh or (
        t.xmin + 0.37 * (t.xmax - t.xmin),
        t.ymin + 0.53 * (t.ymax - t.ymin),
        t.zmin + 0.61 * (t.zmax - t.zmin),
    )
    body: dict[str, Any] = {
        "castellatedMesh": "true",
        "snap": "true",
        "addLayers": "true" if t.layers > 0 else "false",
        "geometry": {
            f"{t.body_name}.stl": {"type": "triSurfaceMesh", "name": t.body_name},
            "wakeBox": {
                "type": "box",
                "min": (bx0 - 0.5 * L, by0 - 0.5 * L, bz0 - 0.5 * L if not t.ground else bz0),
                "max": (bx1 + 3.0 * L, by1 + 0.5 * L, bz1 + 0.5 * L),
            },
        },
        "castellatedMeshControls": {
            "maxLocalCells": 2_000_000,
            "maxGlobalCells": 8_000_000,
            "minRefinementCells": 10,
            "maxLoadUnbalance": 0.10,
            "nCellsBetweenLevels": 3,
            "features": [{"file": f'"{t.body_name}.eMesh"', "level": t.surface_levels[1]}],
            "refinementSurfaces": {
                t.body_name: {
                    "level": tuple(t.surface_levels),
                    "patchInfo": {"type": "wall", "inGroups": (t.body_name + "Group",)},
                }
            },
            "resolveFeatureAngle": 30,
            "refinementRegions": {
                "wakeBox": {"mode": "inside", "levels": ((1e15, t.region_level),)}
            },
            "locationInMesh": loc,
            "allowFreeStandingZoneFaces": "true",
        },
        "snapControls": {
            "nSmoothPatch": 3,
            "tolerance": 2.0,
            "nSolveIter": 30,
            "nRelaxIter": 5,
            "nFeatureSnapIter": 10,
            "implicitFeatureSnap": "false",
            "explicitFeatureSnap": "true",
            "multiRegionFeatureSnap": "false",
        },
        "addLayersControls": {
            "relativeSizes": "true",
            "layers": {t.body_name: {"nSurfaceLayers": t.layers}},
            "expansionRatio": t.layer_expansion,
            "finalLayerThickness": t.final_layer_rel,
            "minThickness": 0.1,
            "nGrow": 0,
            "featureAngle": 60,
            "slipFeatureAngle": 30,
            "nRelaxIter": 3,
            "nSmoothSurfaceNormals": 1,
            "nSmoothNormals": 3,
            "nSmoothThickness": 10,
            "maxFaceThicknessRatio": 0.5,
            "maxThicknessToMedialRatio": 0.3,
            "minMedialAxisAngle": 90,
            "nBufferCellsNoExtrude": 0,
            "nLayerIter": 50,
        },
        "meshQualityControls": {
            "#include": '"meshQualityDict"',
            "nSmoothScale": 4,
            "errorReduction": 0.75,
        },
        "writeFlags": ("scalarLevels", "layerSets", "layerFields"),
        "mergeTolerance": 1e-6,
    }
    text = foam_file("dictionary", "snappyHexMeshDict", body, "system")
    return text.replace('#include        "meshQualityDict";', '#include "meshQualityDict"')


def mesh_quality_dict() -> str:
    return foam_file(
        "dictionary",
        "meshQualityDict",
        {"#includeEtc": '#includeEtc "caseDicts/meshQualityDict"', "minFaceWeight": 0.02},
        "system",
    )


def surface_feature_extract_dict(body_name: str, angle: float = 150.0) -> str:
    body = {
        f"{body_name}.stl": {
            "extractionMethod": "extractFromSurface",
            "includedAngle": angle,
            "subsetFeatures": {"nonManifoldEdges": "no", "openEdges": "yes"},
            "writeObj": "no",
        }
    }
    return foam_file("dictionary", "surfaceFeatureExtractDict", body, "system")


# ---------------------------------------------------------------------------
# Readers - header-driven, never positional
# ---------------------------------------------------------------------------

_COEFF_ALIASES = {
    "cd": ("Cd", "CD", "cd"),
    "cl": ("Cl", "CL", "cl"),
    "cm": ("CmPitch", "Cm", "CM", "cm"),
    "cd_f": ("Cd(f)",),
    "cd_r": ("Cd(r)",),
    "cl_f": ("Cl(f)",),
    "cl_r": ("Cl(r)",),
}


def find_coefficient_files(case_dir: str | Path) -> list[Path]:
    root = Path(case_dir) / "postProcessing"
    if not root.is_dir():
        return []
    files = [p for p in root.rglob("*.dat") if p.name in ("coefficient.dat", "forceCoeffs.dat")]
    return sorted(files, key=lambda p: (p.parent.name, p.name))


def read_coefficients(path: str | Path) -> dict[str, Any]:
    """Parse a forceCoeffs output file. Returns {"columns": [...], "rows": [dict], "source": ...}
    with every row keyed by the header's own names plus the canonical
    cl/cd/cm keys when they can be mapped."""
    columns: list[str] = []
    rows: list[dict[str, float]] = []
    for line in Path(path).read_text().splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            body = s.lstrip("#").strip()
            parts = body.split()
            if parts and parts[0] in ("Time", "time") and len(parts) > 1:
                columns = parts
            continue
        vals = s.replace("\t", " ").split()
        if not columns or len(vals) != len(columns):
            continue
        try:
            row = {c: float(v) for c, v in zip(columns, vals, strict=True)}
        except ValueError:
            continue
        for canon, names in _COEFF_ALIASES.items():
            for n in names:
                if n in row:
                    row[canon] = row[n]
                    break
        rows.append(row)
    if not columns:
        raise ValueError(
            f"{Path(path).name}: no '# Time ...' header line - "
            "not a forceCoeffs file this reader knows"
        )
    return {"columns": columns, "rows": rows, "source": str(path)}


_RE_TIME = re.compile(r"^Time = (\S+)")
_RE_RESID = re.compile(
    r"Solving for (\w+), Initial residual = ([-+0-9.eE]+), "
    r"Final residual = ([-+0-9.eE]+), No Iterations (\d+)"
)
_RE_BOUND = re.compile(r"^bounding (\w+)")
_RE_FATAL = re.compile(r"FOAM FATAL")
_RE_END = re.compile(r"^End$")


def parse_log(text: str) -> dict[str, Any]:
    """Residual history from a solver log: per time step the INITIAL residual
    of every field (the number OpenFOAM's residualControl watches)."""
    times: list[float] = []
    residuals: dict[str, list[float]] = {}
    current: dict[str, float] = {}
    t: float | None = None
    bounded: dict[str, int] = {}
    fatal = False
    ended = False
    for line in text.splitlines():
        m = _RE_TIME.match(line)
        if m:
            if t is not None:
                times.append(t)
                for k, v in current.items():
                    residuals.setdefault(k, []).append(v)
            try:
                t = float(m.group(1))
            except ValueError:
                t = None
            current = {}
            continue
        m = _RE_RESID.search(line)
        if (
            m and m.group(1) not in current
        ):  # first solve of a field in a step is the initial residual
            current[m.group(1)] = float(m.group(2))
            continue
        m = _RE_BOUND.match(line)
        if m:
            bounded[m.group(1)] = bounded.get(m.group(1), 0) + 1
            continue
        if _RE_FATAL.search(line):
            fatal = True
        if _RE_END.match(line.strip()):
            ended = True
    if t is not None and current:
        times.append(t)
        for k, v in current.items():
            residuals.setdefault(k, []).append(v)
    return {
        "times": times,
        "residuals": residuals,
        "bounded": bounded,
        "fatal": fatal,
        "ended": ended,
    }


def last_error_lines(text: str, limit: int = 3) -> list[str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if "FOAM FATAL" in ln:
            return [x.strip() for x in lines[i : i + 6]][: limit + 3]
    return [x.strip() for x in lines[-limit:]]


_RE_CELLS = re.compile(r"^\s*cells:\s*(\d+)", re.M)
_RE_NONORTH = re.compile(r"Max non-orthogonality = ([-+0-9.eE]+)")
_RE_SKEW = re.compile(r"Max skewness = ([-+0-9.eE]+)")
_RE_ASPECT = re.compile(r"Max aspect ratio = ([-+0-9.eE]+)")
_RE_FAILED = re.compile(r"Failed (\d+) mesh checks")
_RE_CHECK_FAIL = re.compile(r"\*\*\*(.+)")


def parse_checkmesh(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": "Mesh OK" in text}
    if m := _RE_CELLS.search(text):
        out["cells"] = int(m.group(1))
    if m := _RE_NONORTH.search(text):
        out["max_nonortho"] = float(m.group(1))
    if m := _RE_SKEW.search(text):
        out["max_skew"] = float(m.group(1))
    if m := _RE_ASPECT.search(text):
        out["max_aspect"] = float(m.group(1))
    if m := _RE_FAILED.search(text):
        out["failed_checks"] = int(m.group(1))
    out["failed"] = [x.strip()[:80] for x in _RE_CHECK_FAIL.findall(text)][:8]
    return out


# ---------------------------------------------------------------------------
# Forks and dialects
# ---------------------------------------------------------------------------

SUPPORTED_DIALECTS = ("com",)  # measured: v1912 (apt), v2606 (OpenFOAM.app)


def fork_of(version: str) -> tuple[str, str]:
    """('com', 'v2606') for openfoam.com versions, ('org', '12') for the
    Foundation's, ('unknown', text) otherwise."""
    v = version.strip()
    if re.fullmatch(r"v\d{4}(\.\d+)?", v):
        return "com", v
    if re.fullmatch(r"\d{1,2}(\.\d+)?", v):
        return "org", v
    if v.lower().startswith("dev"):
        return "org", v
    return "unknown", v


def solver_sequence(text: str) -> list[list[str]]:
    """The `runApplication`/`runParallel` lines of an Allrun/Allmesh script,
    as argv lists of KNOWN binaries - TEE runs those, never the script."""
    seq: list[list[str]] = []
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^(runApplication|runParallel)\s+(.*)$", s)
        if not m:
            continue
        tokens = m.group(2).replace("$", "").split()
        args: list[str] = []
        skip_next = False
        for tok in tokens:
            if skip_next:  # the suffix after RunFunctions' own `-s`
                skip_next = False
                continue
            if tok in ("-s", "-a", "-o"):  # runApplication's own options
                skip_next = tok == "-s"
                continue
            if tok.startswith((">", "2>", "|", "&")):
                break  # a redirection ends the argv
            args.append(tok)
        if args:
            seq.append(args)
    return seq


def controldict_application(text: str) -> str | None:
    m = re.search(r"^\s*application\s+(\w+)\s*;", text, re.M)
    return m.group(1) if m else None


def field_bcs(text: str) -> dict[str, str]:
    """patch -> type from a 0/ field file (adoption's summary)."""
    out: dict[str, str] = {}
    in_bf = False
    name: str | None = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("boundaryField"):
            in_bf = True
            continue
        if not in_bf:
            continue
        m = re.match(r"^([\w\"|().*]+)\s*$", s)
        if m and not s.startswith(("type", "value", "{", "}")):
            name = m.group(1)
        m = re.match(r"^type\s+(\w+)\s*;", s)
        if m and name:
            out[name] = m.group(1)
            name = None
    return out


def patch_names(boundary_text: str) -> list[tuple[str, str]]:
    """(patch, type) pairs from constant/polyMesh/boundary."""
    pairs: list[tuple[str, str]] = []
    name: str | None = None
    for line in boundary_text.splitlines():
        s = line.strip()
        if re.fullmatch(r"[\w.-]+", s) and s not in ("FoamFile",):
            name = s
        m = re.match(r"^type\s+(\w+)\s*;", s)
        if m and name and name not in ("FoamFile",):
            if (
                name != "version"
                and name != "format"
                and name != "class"
                and name != "object"
                and name != "location"
            ):
                pairs.append((name, m.group(1)))
            name = None
    return pairs


def default_sequence(has_stl: bool, cores: int = 1) -> Sequence[list[str]]:
    seq: list[list[str]] = [["blockMesh"]]
    if has_stl:
        seq += [["surfaceFeatureExtract"], ["snappyHexMesh", "-overwrite"]]
    seq.append(["checkMesh"])
    return seq
