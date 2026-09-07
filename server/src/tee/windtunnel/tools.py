"""The wt_* virtual tools (A72).

Registered into the progressive-disclosure registry, so this lane adds ZERO
tools to the always-loaded surface. Every response is a digest - no array
over 64 elements, no string over 2 KB (case.digest) - and every result
carries the engine, its version, the mesh hash, a convergence verdict and
an uncertainty label. Long work (meshing a 3-D body, any solve, a sweep,
the verification battery) is a job on the machine ledger; a tool call never
waits on a solver, and `tee_job cancel` kills the solver process through
the kernel's on_cancel hook.
"""

from __future__ import annotations

import math
import shutil
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.windtunnel import (
    atmosphere,
    engines,
    fidelity,
    foam,
    physics,
    report,
    runs,
    verdict,
    vsp,
)
from tee.windtunnel import (
    case as case_mod,
)
from tee.windtunnel.case import CaseStore, digest
from tee.windtunnel.runner import (
    RunSpec,
    SolverRun,
    forget,
    kill_orphan,
    live_run_for_case,
    orphan_check,
    register,
)

PROBE_TTL_S = 3600.0
# checkMesh failures a solver runs through: the trailing-edge seam of a sharp
# section always shows a few skewed faces, and a mesh whose faces are not in
# upper-triangular order (the apt airFoil2D tutorial, measured 2026-09-06) is
# a matrix-ordering remark that `renumberMesh` fixes, not a geometry defect.
TOLERATED_CHECKS = ("skew", "upper triangular")
DEFAULT_ITERS = {"openfoam": 2000, "su2": 3000}
DEFAULT_TIMEOUT_S = 600.0
MAX_WALL_S = 14_400.0
UNITS = ("m", "cm", "mm", "in", "ft")


def register_windtunnel_tools(app, project_root: Path | str) -> CaseStore:
    store = CaseStore(project_root)
    cfg: dict[str, Any] = dict(getattr(getattr(app, "config", None), "windtunnel", {}) or {})
    reg = app.registry
    lane = _Lane(app, store, cfg)

    specs = [
        (
            "wt_probe",
            "Which wind-tunnel engines this machine has: OpenFOAM, SU2, OpenVSP/VSPAERO, "
            "ParaView's pvpython - version probes only, never a solve. Absent engines come "
            "back with their install line.",
            {
                "type": "object",
                "properties": {
                    "refresh": {
                        "type": "boolean",
                        "description": "Re-probe instead of the cached answer.",
                    }
                },
            },
            lane.probe,
            [
                "windtunnel",
                "cfd",
                "aerodynamics",
                "openfoam",
                "su2",
                "openvsp",
                "vspaero",
                "paraview",
                "solver",
                "installed",
                "engines",
            ],
            [{}],
        ),
        (
            "wt_conditions",
            "Standard atmosphere and the three numbers a case needs: Reynolds number, Mach and "
            "dynamic pressure for a speed OR a Mach number, a reference length and an altitude "
            "(ISA / US76, Sutherland viscosity).",
            {
                "type": "object",
                "properties": {
                    "V_mps": {
                        "type": "number",
                        "description": "True airspeed, m/s (or give mach).",
                    },
                    "mach": {"type": "number"},
                    "L_m": {
                        "type": "number",
                        "description": "Reference length, m (chord, diameter, body length).",
                    },
                    "alt_m": {"type": "number", "description": "Altitude, m (0..20000)."},
                    "dT_K": {"type": "number", "description": "ISA temperature offset, K."},
                },
                "required": ["L_m"],
            },
            lane.conditions,
            [
                "windtunnel",
                "reynolds",
                "mach",
                "altitude",
                "atmosphere",
                "isa",
                "dynamic pressure",
                "airspeed",
                "viscosity",
            ],
            [{"V_mps": 45, "L_m": 1.2, "alt_m": 1500}],
        ),
        (
            "wt_case",
            "Create a wind-tunnel case from a NACA section, a Selig .dat, an STL body, an OpenVSP "
            "wing, or ADOPT an existing OpenFOAM case directory / SU2 .cfg / .vsp3 (copied, never "
            "mutated). The fidelity ladder picks the cheapest capable engine and says why; every "
            "answer is a digest. Actions: create, adopt, show, list, stop.",
            {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "adopt", "show", "list", "stop"],
                    },
                    "case_id": {"type": "string"},
                    "path": {
                        "type": "string",
                        "description": "adopt: the case dir, .cfg or .vsp3.",
                    },
                    "naca": {"type": "string", "description": "Four digits, e.g. '2412'."},
                    "circle": {
                        "type": "boolean",
                        "description": "A circular cylinder section (the bluff-body benchmark).",
                    },
                    "n_surface": {
                        "type": "integer",
                        "description": "Points per surface on a generated section (default 100); "
                        "it fixes the O-mesh's azimuthal count, so it is set here, not at mesh "
                        "time.",
                    },
                    "dat": {"type": "string", "description": "A Selig airfoil file."},
                    "stl": {
                        "type": "string",
                        "description": "A body (an STL from pk_export, Blender, anywhere).",
                    },
                    "geom": {"type": "string", "description": "A geom_id from wt_geom."},
                    "wing": {
                        "type": "object",
                        "description": "{span, root_chord, taper|tip_chord, sweep_deg, airfoil}.",
                    },
                    "units": {
                        "type": "string",
                        "description": "STL units: m (default), cm, mm, in, ft.",
                    },
                    "V_mps": {"type": "number"},
                    "mach": {"type": "number"},
                    "alt_m": {"type": "number"},
                    "aoa_deg": {"type": "number"},
                    "chord_m": {
                        "type": "number",
                        "description": "2-D section chord, m (default 1).",
                    },
                    "fidelity": {"type": "string", "enum": ["auto", "panel", "euler", "rans"]},
                    "need_viscous": {
                        "type": "boolean",
                        "description": "Ask for friction drag (RANS).",
                    },
                    "turbulence": {
                        "type": "string",
                        "description": "OpenFOAM: kOmegaSST (default) or laminar.",
                    },
                    "refs": {
                        "type": "object",
                        "description": "{Sref, cref, bref} overrides (m^2, m, m).",
                    },
                    "ground": {
                        "type": "boolean",
                        "description": "3-D: floor at the body's lowest point.",
                    },
                    "strict": {
                        "type": "boolean",
                        "description": "Refuse blockage > 5 % instead of warning.",
                    },
                },
                "required": ["action"],
            },
            lane.case,
            [
                "windtunnel",
                "cfd",
                "case",
                "airfoil",
                "wing",
                "body",
                "adopt",
                "openfoam",
                "su2",
                "vsp3",
                "airflow",
                "aerodynamic",
                "simulate",
                "setup",
                "angle of attack",
            ],
            [
                {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4},
                {"action": "create", "stl": "out/fairing.stl", "V_mps": 40},
                {"action": "adopt", "path": "~/cases/cfdof_car"},
            ],
        ),
        (
            "wt_geom",
            "Parametric geometry through OpenVSP: a wing (span, chords, sweep, NACA airfoil) built "
            "by vspscript into .vsp3 + STL + DegenGeom, or the facts of an STL (bbox, frontal and "
            "planform areas, watertightness).",
            {
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "enum": ["wing", "from_stl"]},
                    "wing": {"type": "object"},
                    "stl": {"type": "string"},
                    "units": {"type": "string"},
                    "name": {"type": "string"},
                },
                "required": ["kind"],
            },
            lane.geom,
            [
                "windtunnel",
                "openvsp",
                "wing",
                "parametric",
                "geometry",
                "aircraft",
                "planform",
                "span",
                "chord",
                "sweep",
                "airfoil",
                "stl",
            ],
            [
                {
                    "kind": "wing",
                    "wing": {
                        "span": 1.2,
                        "root_chord": 0.25,
                        "taper": 0.6,
                        "sweep_deg": 5,
                        "airfoil": "2412",
                    },
                }
            ],
        ),
        (
            "wt_mesh",
            "Mesh the case: a structured O-mesh for a 2-D section (seconds, written as OpenFOAM "
            "polyMesh or SU2 .su2), or blockMesh + snappyHexMesh around a 3-D body (a job). "
            "Returns the checkMesh digest, never a cell.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "y_plus": {
                        "type": "number",
                        "description": "Target y+ for the first cell (default 1 for low-Re walls).",
                    },
                    "nj": {
                        "type": "integer",
                        "description": "Radial layers of the O-mesh (default 80).",
                    },
                    "n_surface": {"type": "integer"},
                    "radius_c": {
                        "type": "number",
                        "description": "Farfield radius in chords (default 50).",
                    },
                    "first_cell_c": {
                        "type": "number",
                        "description": "O-mesh first cell, chords. SU2 default 0.005; on "
                        "OpenFOAM it overrides the y+ sizing (which a laminar case ignores "
                        "anyway - y+ is a turbulent idea).",
                    },
                    "base_cell_m": {"type": "number", "description": "3-D background cell, m."},
                    "levels": {
                        "type": "array",
                        "description": "3-D surface refinement levels, e.g. [3, 4].",
                    },
                    "layers": {"type": "integer", "description": "3-D prism layers (default 5)."},
                    "cores": {"type": "integer"},
                },
                "required": ["case_id"],
            },
            lane.mesh,
            [
                "windtunnel",
                "mesh",
                "grid",
                "snappyhexmesh",
                "blockmesh",
                "omesh",
                "cells",
                "refinement",
                "layers",
                "y plus",
            ],
            [{"case_id": "wt_1a2b3c4d5e"}],
        ),
        (
            "wt_run",
            "Solve the case as a job (poll with tee_job, watch with wt_status). Cost-gated: above "
            "the measured threshold it asks once for confirm_cost=true with the estimate. "
            "tee_job cancel kills the solver.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "aoa_deg": {"type": "number"},
                    "iters": {
                        "type": "integer",
                        "description": "Iteration cap (residual control may stop earlier).",
                    },
                    "cores": {"type": "integer"},
                    "confirm_cost": {"type": "boolean"},
                    "timeout_s": {"type": "number"},
                    "solver": {
                        "type": "string",
                        "description": "SU2: EULER (default for euler) or RANS.",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Run on a mesh checkMesh flagged.",
                    },
                    "forces": {
                        "type": "object",
                        "description": (
                            "Adopted OpenFOAM case only: add a forceCoeffs function object to "
                            "the run copy - {patches, lRef, Aref?, U?, CofR?}."
                        ),
                    },
                },
                "required": ["case_id"],
            },
            lane.run,
            [
                "windtunnel",
                "run",
                "solve",
                "simulation",
                "simplefoam",
                "su2_cfd",
                "vspaero",
                "job",
                "cfd",
                "compute",
            ],
            [{"case_id": "wt_1a2b3c4d5e", "confirm_cost": True}],
        ),
        (
            "wt_status",
            "Where a run is, in a few dozen tokens: iteration, last residuals, last lift/drag with "
            "trend, elapsed and ETA, and whether the solver is still alive (an orphan after a "
            "server restart is named as such).",
            {
                "type": "object",
                "properties": {"case_id": {"type": "string"}, "run_id": {"type": "string"}},
                "required": ["case_id"],
            },
            lane.status,
            [
                "windtunnel",
                "status",
                "progress",
                "residuals",
                "convergence",
                "running",
                "eta",
                "poll",
            ],
            [{"case_id": "wt_1a2b3c4d5e"}],
        ),
        (
            "wt_result",
            "Lift, drag and moment coefficients with the convergence verdict and the uncertainty "
            "label (RANS is comparative, not absolute). compare_to gives same-mesh deltas in "
            "drag counts.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "allow_partial": {
                        "type": "boolean",
                        "description": "Answer from an unfinished run, labelled.",
                    },
                    "compare_to": {
                        "type": "string",
                        "description": "case_id[/run_id] to difference against.",
                    },
                    "window_pct": {"type": "number"},
                },
                "required": ["case_id"],
            },
            lane.result,
            [
                "windtunnel",
                "result",
                "lift",
                "drag",
                "coefficient",
                "cl",
                "cd",
                "cm",
                "moment",
                "polar",
                "verdict",
                "converged",
                "uncertainty",
            ],
            [{"case_id": "wt_1a2b3c4d5e"}],
        ),
        (
            "wt_sweep",
            "An angle-of-attack sweep as ONE job: a VSPAERO polar in seconds, or sequential "
            "OpenFOAM/SU2 runs. "
            "Returns at most 64 rows; the full polar goes to CSV.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "aoa": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Evenly spaced for VSPAERO.",
                    },
                    "iters": {"type": "integer"},
                    "cores": {"type": "integer"},
                    "confirm_cost": {"type": "boolean"},
                },
                "required": ["case_id", "aoa"],
            },
            lane.sweep,
            [
                "windtunnel",
                "sweep",
                "polar",
                "angle of attack",
                "alpha",
                "lift curve",
                "drag polar",
                "stall",
            ],
            [{"case_id": "wt_1a2b3c4d5e", "aoa": [-2, 0, 2, 4, 6, 8]}],
        ),
        (
            "wt_probe_field",
            "Numbers from the flow field: a line of at most 64 samples (velocity, pressure, k, "
            "omega) through pvpython with no rendering, or the statistics of a field on a slice. "
            "Text over pixels.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "what": {"type": "string", "enum": ["line", "slice"]},
                    "field": {
                        "type": "string",
                        "description": (
                            "U, p, k, omega, nut (OpenFOAM) or Pressure, Velocity... (SU2)."
                        ),
                    },
                    "p1": {"type": "array", "items": {"type": "number"}},
                    "p2": {"type": "array", "items": {"type": "number"}},
                    "n": {"type": "integer"},
                    "origin": {"type": "array", "items": {"type": "number"}},
                    "normal": {"type": "array", "items": {"type": "number"}},
                    "components": {
                        "type": "boolean",
                        "description": "A vector's x/y/z arrays too (default: magnitude only).",
                    },
                },
                "required": ["case_id"],
            },
            lane.probe_field,
            [
                "windtunnel",
                "sample",
                "velocity",
                "pressure",
                "profile",
                "line",
                "slice",
                "field",
                "wake",
                "boundary layer",
                "paraview",
            ],
            [
                {
                    "case_id": "wt_1a2b3c4d5e",
                    "what": "line",
                    "field": "U",
                    "p1": [0.5, 0, 0.05],
                    "p2": [0.5, 0.3, 0.05],
                    "n": 32,
                }
            ],
        ),
        (
            "wt_view",
            "Render a picture of the flow to disk through pvpython (pressure, velocity, cp, mesh) "
            "and return its path and the colour range - never pixels on the wire. Opt-in, last "
            "resort after the numbers.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "view": {"type": "string", "enum": list(_views())},
                    "plane": {"type": "string", "enum": ["x", "y", "z"]},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"},
                },
                "required": ["case_id"],
            },
            lane.view,
            [
                "windtunnel",
                "render",
                "picture",
                "png",
                "contour",
                "pressure field",
                "velocity field",
                "streamlines",
                "visualise",
                "paraview",
            ],
            [{"case_id": "wt_1a2b3c4d5e", "view": "pressure"}],
        ),
        (
            "wt_export",
            "Write the result out: json, csv (polar), md, pdf (through the pdf lane), a .foam "
            "stub for ParaView, "
            "vtu (meshio, the optional extra), or a pipeline.toml fragment.",
            {
                "type": "object",
                "properties": {
                    "case_id": {"type": "string"},
                    "run_id": {"type": "string"},
                    "format": {"type": "string", "enum": list(report.FORMATS)},
                    "out_dir": {"type": "string"},
                },
                "required": ["case_id", "format"],
            },
            lane.export,
            ["windtunnel", "export", "csv", "json", "pdf", "report", "vtu", "foam", "pipeline"],
            [{"case_id": "wt_1a2b3c4d5e", "format": "csv"}],
        ),
        (
            "wt_verify",
            "Run the canonical validation battery against references verified at their source "
            "(a wing's lift slope against lifting line; the SU2 quick-start NACA 0012 figure) "
            "and report pass/fail per case.",
            {
                "type": "object",
                "properties": {
                    "case": {
                        "type": "string",
                        "description": (
                            "wing_liftslope | naca0012_euler | cylinder_re40 | flatplate | all"
                        ),
                    },
                    "confirm_cost": {"type": "boolean"},
                },
            },
            lane.verify,
            [
                "windtunnel",
                "verify",
                "validation",
                "reference",
                "benchmark",
                "lifting line",
                "naca 0012",
                "calibration",
            ],
            [{"case": "wing_liftslope"}],
        ),
    ]
    for name, description, schema, handler, tags, examples in specs:
        reg.register(
            VirtualTool(
                name=name,
                description=description,
                schema=schema,
                handler=handler,
                tags=tags,
                examples=examples,
            )
        )
    return store


def _mesh_ok(check: dict[str, Any]) -> bool:
    """checkMesh said OK, or its one failure is a tolerated one."""
    if check.get("ok"):
        return True
    failed = " ".join(check.get("failed", [])).lower()
    return check.get("failed_checks", 0) == 1 and any(t in failed for t in TOLERATED_CHECKS)


def _views() -> tuple[str, ...]:
    from tee.windtunnel.paraview import VIEWS

    return VIEWS


class _Lane:
    """The handlers, sharing the store, the config and the engine probe."""

    def __init__(self, app, store: CaseStore, cfg: dict[str, Any]) -> None:
        self.app = app
        self.store = store
        self.cfg = cfg
        self._probe: dict[str, Any] | None = None
        self._probe_at = 0.0

    # -- engines -------------------------------------------------------------
    def probe(self, args: dict[str, Any]) -> dict[str, Any]:
        if args.get("refresh") or self._probe is None or time.time() - self._probe_at > PROBE_TTL_S:
            self._probe = engines.probe(self.cfg)
            self._probe_at = time.time()
            runs.dump_json(self.store.root / "probe.json", self._probe)
        return digest(self._probe)

    def _available(self) -> dict[str, bool]:
        p = self._probe if self._probe is not None else self.probe({})
        e = p["engines"]
        return {
            "openfoam": bool(e["openfoam"].get("found")),
            "su2": bool(e["su2"].get("found")),
            "vspaero": bool(
                e["vspaero"].get("found") and e["vspaero"].get("extra", {}).get("vspaero")
            ),
        }

    def _openfoam(self, *, for_writer: bool = False):
        """The install route. `for_writer=True` means TEE's own dictionaries
        will run on it, and those are the openfoam.com dialect (v1912 and
        v2606 measured): a Foundation install refuses rather than failing
        deep inside simpleFoam. Adopted cases carry their own dialect and
        run on whatever wrote them."""
        route = engines.find_openfoam(self.cfg, probe_version=False)
        if for_writer:
            probed = (self._probe or {}).get("engines", {}).get("openfoam", {})
            fork = str(probed.get("fork") or route.fork or "")
            if fork and fork not in ("unknown", *foam.SUPPORTED_DIALECTS):
                raise TeeError(
                    "wt_fork_unsupported",
                    f"OpenFOAM {probed.get('version') or route.version} is the '{fork}' "
                    "fork; TEE writes the openfoam.com dialect (transportProperties, "
                    "turbulenceProperties, forceCoeffs with libforces).",
                    fix="Install openfoam.com's build (wt_probe names the line), or write the "
                    "case with its own tools and wt_case action=adopt it: an adopted case "
                    "runs as-is.",
                )
        return route

    def _su2(self) -> str:
        return engines.find_su2(self.cfg, probe_version=False).path

    def _vsp(self) -> engines.Binary:
        b = engines.find_openvsp(self.cfg, probe_version=False)
        if not b.extra.get("vspaero"):
            raise TeeError(
                "wt_openvsp_missing",
                "vspscript was found but vspaero was not beside it.",
                fix=engines._install_line("openvsp"),
            )
        return b

    def _pvpython(self) -> str:
        return engines.find_pvpython(self.cfg, probe_version=False).path

    # -- conditions ----------------------------------------------------------
    def conditions(self, args: dict[str, Any]) -> dict[str, Any]:
        try:
            return digest(
                atmosphere.conditions(
                    L_m=float(args.get("L_m") or 0.0),
                    V_mps=_opt_float(args, "V_mps"),
                    mach=_opt_float(args, "mach"),
                    alt_m=float(args.get("alt_m", 0.0)),
                    dT_K=float(args.get("dT_K", 0.0)),
                )
            )
        except (ValueError, TypeError) as exc:
            raise TeeError(
                "wt_bad_conditions",
                str(exc),
                fix="Give V_mps or mach (one of them), a positive L_m and 0 <= alt_m <= 20000.",
            ) from exc

    # -- cases ---------------------------------------------------------------
    def case(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action") or "create")
        if action == "list":
            return digest({"cases": self.store.list()[-64:]})
        if action == "show":
            rec = self.store.load(_case_id(args))
            return digest(_show(rec))
        if action == "stop":
            return digest(self._stop(_case_id(args)))
        if action == "adopt":
            return digest(self._adopt(args))
        if action == "create":
            return digest(self._create(args))
        raise TeeError(
            "wt_bad_action",
            f"'{action}' is not an action.",
            fix="One of: create, adopt, show, list, stop.",
        )

    def _create(self, args: dict[str, Any]) -> dict[str, Any]:
        tmp_id = "wt_pending"
        geom_dir = self.store.root / "tmp_geometry" / str(time.time_ns())
        geom_dir.mkdir(parents=True, exist_ok=True)
        # geometry
        if args.get("naca") or args.get("dat") or args.get("circle"):
            geometry = runs.section_from(args, geom_dir)
            chord = float(args.get("chord_m", 1.0))
            L = chord
            refs = {"Sref": chord, "cref": chord, "bref": 1.0}
            kind = "airfoil2d"
        elif args.get("stl"):
            path = Path(str(args["stl"])).expanduser()
            if not path.is_file():
                raise TeeError(
                    "wt_geometry_missing",
                    f"{path} does not exist.",
                    fix="Give the STL's path (pk_export format=stl writes one).",
                )
            geometry = runs.body_from_stl(path, geom_dir, str(args.get("units", "m")))
            L = geometry["length_m"]
            refs = {"Sref": geometry["frontal_area_m2"], "cref": L, "bref": geometry["width_m"]}
            kind = "body3d"
        elif args.get("wing") or args.get("geom"):
            geometry = self._wing_geometry(args, geom_dir)
            L = geometry["mac"]
            refs = {
                "Sref": geometry["area_ref_m2"],
                "cref": geometry["mac"],
                "bref": geometry["span"],
            }
            kind = "wing3d"
        else:
            raise TeeError(
                "wt_geometry_missing",
                "A case needs naca=, dat=, stl=, wing= or geom=.",
                fix="e.g. naca='0012' V_mps=30 aoa_deg=4",
            )
        if isinstance(args.get("refs"), dict):
            for k in ("Sref", "cref", "bref"):
                if k in args["refs"]:
                    refs[k] = float(args["refs"][k])
        if refs["Sref"] <= 0:
            raise TeeError(
                "wt_refs_needed",
                "The reference area came out zero (a flat STL seen edge-on?).",
                fix="Give refs={'Sref': <m^2>}.",
            )
        # conditions
        try:
            cond = atmosphere.conditions(
                L_m=refs["cref"],
                V_mps=_opt_float(args, "V_mps"),
                mach=_opt_float(args, "mach"),
                alt_m=float(args.get("alt_m", 0.0)),
            )
        except ValueError as exc:
            raise TeeError(
                "wt_bad_conditions", str(exc), fix="Give V_mps or mach and a positive chord/length."
            ) from exc
        aoa = float(args.get("aoa_deg", 0.0))
        need_viscous = bool(args.get("need_viscous", kind != "wing3d"))
        try:
            choice = fidelity.choose(
                kind,
                mach=float(cond["mach"]),
                need_viscous=need_viscous,
                aoa_max_deg=abs(aoa),
                fidelity=str(args.get("fidelity", "auto")),
                available=self._available(),
            )
        except ValueError as exc:
            raise TeeError(
                "wt_regime",
                str(exc),
                fix="Pick another fidelity, or install the engine wt_probe names.",
            ) from exc
        record: dict[str, Any] = {
            "engine": choice.engine,
            "fidelity": {"chosen": choice.fidelity, "reason": choice.reason},
            "conditions": {**cond, "aoa_deg": aoa},
            "refs": refs,
            "geometry": geometry,
            "turbulence": str(args.get("turbulence", "kOmegaSST")),
        }
        if kind in ("body3d", "wing3d") and choice.engine == "openfoam":
            bbox = (tuple(geometry["bbox"][0]), tuple(geometry["bbox"][1]))
            dom = physics.domain_3d(bbox, refs["Sref"], ground=bool(args.get("ground")))
            verdict_b = physics.blockage_verdict(dom.blockage)
            if verdict_b == "refuse" or (verdict_b == "warn" and args.get("strict")):
                raise TeeError(
                    "wt_blockage",
                    f"Blockage {100 * dom.blockage:.1f} % of the tunnel cross-section.",
                    fix="Give refs={'Sref': ...} if the frontal area is wrong, or a smaller body; "
                    "the tunnel is sized from the body bbox.",
                )
            record["domain"] = {**dom.__dict__, "verdict": verdict_b}
        case_id = self.store.mint(kind, record)
        cdir = self.store.case_dir(case_id)
        dst = cdir / "geometry"
        if dst.is_dir():  # mint made an empty one; a move INTO it would nest the files
            dst.rmdir()
        shutil.move(str(geom_dir), str(dst))
        # fix paths that pointed into the temporary geometry dir
        rec = self.store.load(case_id)
        for key in ("dat", "stl", "vsp3", "degen"):
            if key in rec["geometry"]:
                rec["geometry"][key] = str(cdir / "geometry" / Path(rec["geometry"][key]).name)
        if "loop" in rec["geometry"]:
            rec["geometry"]["loop"] = [list(p) for p in rec["geometry"]["loop"]]
        rec["engine_dir"] = str(cdir / rec["engine"])
        self.store.save(case_id, rec)
        del tmp_id
        out = _show(rec)
        out["next"] = "wt_mesh" if choice.engine != "vspaero" else "wt_sweep or wt_run"
        return out

    def _wing_geometry(self, args: dict[str, Any], geom_dir: Path) -> dict[str, Any]:
        if args.get("geom"):
            src = self.store.root / "geometry" / str(args["geom"])
            if not (src / "geom.json").is_file():
                raise TeeError(
                    "wt_geometry_missing",
                    f"No geometry '{args['geom']}'.",
                    fix="wt_geom kind=wing first.",
                )
            import json

            g = json.loads((src / "geom.json").read_text())
            for key in ("vsp3", "stl", "degen"):
                if key in g and Path(g[key]).is_file():
                    shutil.copyfile(g[key], geom_dir / Path(g[key]).name)
                    g[key] = str(geom_dir / Path(g[key]).name)
            return g
        return self._build_wing(runs.wing_from_spec(args), geom_dir, stem="wing")

    def _build_wing(self, spec: vsp.WingSpec, out_dir: Path, *, stem: str) -> dict[str, Any]:
        b = engines.find_openvsp(self.cfg, probe_version=False)
        script = vsp.wing_script(stem, spec)
        (out_dir / f"{stem}.vspscript").write_text(script)
        run = SolverRun(
            RunSpec(
                run_id="geom",
                case_id="geom",
                engine="vspscript",
                argv=[b.path, "-script", f"{stem}.vspscript"],
                cwd=out_dir,
                log_name="log.vspscript",
                timeout_s=120.0,
            )
        )
        res = run.run()
        log = (out_dir / "log.vspscript").read_text(errors="replace")
        if "DONE" not in log or not (out_dir / f"{stem}.vsp3").is_file():
            raise TeeError(
                "wt_vsp_script_failed",
                "vspscript did not finish the wing.",
                fix=f"Last lines: {' | '.join(log.strip().splitlines()[-3:])[:300]}",
            )
        facts = vsp.script_facts(log)
        stl = out_dir / f"{stem}.stl"
        surf = physics.read_stl(stl) if stl.is_file() else None
        bbox = surf.bbox if surf else ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        return {
            "kind": "wing3d",
            "name": f"wing AR {spec.aspect_ratio:.1f}",
            "vsp3": str(out_dir / f"{stem}.vsp3"),
            "stl": str(stl) if stl.is_file() else None,
            "degen": str(next(out_dir.glob("*_DegenGeom.csv"), "")) or None,
            "span": facts.get("TotalSpan", spec.span),
            "area_ref_m2": facts.get("TotalArea", spec.area),
            "mac": spec.mac,
            "aspect_ratio": round(spec.aspect_ratio, 3),
            "wetted_area_m2": round(surf.area, 6) if surf else None,
            "tris": len(surf.tris) if surf else 0,
            "bbox": [list(bbox[0]), list(bbox[1])],
            "wing": spec.__dict__,
            "vsp_wall_s": res["wall_s"],
        }

    def _adopt(self, args: dict[str, Any]) -> dict[str, Any]:
        from tee.windtunnel import cfdof

        raw = str(args.get("path") or "")
        if raw.startswith("freecad:"):
            raw = cfdof.rpc_case_path(raw.split(":", 1)[1])
        path = Path(raw).expanduser()
        if not path.exists():
            raise TeeError(
                "wt_not_a_case",
                f"{path} does not exist.",
                fix="Give the case directory, the .cfg or the .vsp3.",
            )
        kind = cfdof.detect(path)
        record: dict[str, Any] = {"adopted_from": str(path)}
        if kind == "openfoam":
            case_id = self.store.mint("adopted", {**record, "engine": "openfoam"})
            edir = self.store.case_dir(case_id) / "openfoam"
            copied = cfdof.copy_case(path, edir)
            summary = cfdof.summarise_openfoam(edir)
            rec = self.store.update(
                case_id,
                engine_dir=str(edir),
                adopted=summary,
                copy=copied,
                fidelity={"chosen": "rans", "reason": "adopted: the case decides"},
                mesh={
                    "kind": "adopted",
                    "has_mesh": summary.get("has_mesh"),
                    "mesh_hash": runs._polymesh_hash(edir) if summary.get("has_mesh") else "",
                },
            )
            out = _show(rec)
            out.update(
                {
                    "solver": summary.get("solver"),
                    "turbulence": summary.get("turbulence"),
                    "dialect": summary.get("dialect"),
                    "patches": summary.get("patches", [])[:64],
                    "inlet_U": summary.get("inlet_U"),
                    "has_forceCoeffs": summary.get("has_forceCoeffs"),
                    "sequence": summary.get("sequence"),
                    "cfdof": summary.get("cfdof"),
                }
            )
            warnings = []
            if not summary.get("has_forceCoeffs"):
                warnings.append(
                    "no forceCoeffs function object: wt_result will have nothing to read unless "
                    "you add one"
                )
            if summary.get("dialect") == "org":
                warnings.append(
                    "Foundation dialect (momentumTransport): TEE runs it as-is but writes nothing "
                    "for it"
                )
            if summary.get("unknown_in_scripts"):
                warnings.append(
                    f"Allrun names binaries TEE will not run: {summary['unknown_in_scripts']}"
                )
            out["warnings"] = warnings
            out["next"] = (
                "wt_run"
                if summary.get("has_mesh")
                else "wt_mesh (the case's own blockMesh/snappy sequence)"
            )
            return out
        if kind == "su2":
            case_id = self.store.mint("adopted", {**record, "engine": "su2"})
            edir = self.store.case_dir(case_id) / "su2"
            edir.mkdir(parents=True, exist_ok=True)
            from tee.windtunnel import su2 as su2_mod

            cfg = su2_mod.read_cfg(path)
            mesh_name = cfg.get("MESH_FILENAME", "")
            mesh_src = (path.parent / mesh_name) if mesh_name else None
            if not mesh_src or not mesh_src.is_file():
                raise TeeError(
                    "wt_not_a_case",
                    f"{path.name} names MESH_FILENAME= {mesh_name!r}, which is not beside it.",
                    fix="Keep the .cfg and its mesh together.",
                )
            shutil.copyfile(path, edir / "adopted.cfg")
            shutil.copyfile(mesh_src, edir / mesh_src.name)
            rec = self.store.update(
                case_id,
                engine_dir=str(edir),
                adopted={
                    "cfg": str(path),
                    "solver": cfg.get("SOLVER"),
                    "mach": cfg.get("MACH_NUMBER"),
                    "aoa": cfg.get("AOA"),
                    "markers": su2_mod.mesh_markers(edir / mesh_src.name)[:16],
                },
                mesh={
                    "kind": "adopted",
                    "su2_file": str(edir / mesh_src.name),
                    "mesh_hash": case_mod.file_hash(edir / mesh_src.name),
                },
                fidelity={
                    "chosen": "rans" if "RANS" in str(cfg.get("SOLVER", "")) else "euler",
                    "reason": "adopted: the case decides",
                },
            )
            out = _show(rec)
            out.update(rec["adopted"])
            out["next"] = "wt_run"
            return out
        case_id = self.store.mint(
            "wing3d",
            {
                **record,
                "engine": "vspaero",
                "fidelity": {"chosen": "panel", "reason": "adopted OpenVSP model: vortex lattice"},
            },
        )
        cdir = self.store.case_dir(case_id)
        dst = cdir / "geometry" / path.name
        shutil.copyfile(path, dst)
        rec = self.store.update(
            case_id,
            engine_dir=str(cdir / "vspaero"),
            geometry={"kind": "wing3d", "vsp3": str(dst), "name": path.stem},
            refs={"Sref": 1.0, "cref": 1.0, "bref": 1.0},
            conditions={"mach": 0.1, "aoa_deg": 0.0, "V": 34.0, "regime": "incompressible"},
        )
        out = _show(rec)
        out["note"] = (
            "references come from the model (RefFlag=1 uses its wing); set V_mps/mach on wt_sweep"
        )
        out["next"] = "wt_sweep"
        return out

    def _stop(self, case_id: str) -> dict[str, Any]:
        rec = self.store.load(case_id)
        live = live_run_for_case(case_id)
        if live is not None:
            gone = live.terminate()
            return {
                "case_id": case_id,
                "run_id": live.spec.run_id,
                "stopped": gone,
                "how": "in-process",
            }
        runs_ = rec.get("runs", [])
        if not runs_:
            raise TeeError("wt_no_orphan", f"Case {case_id} has no runs.", fix="Nothing to stop.")
        run_dir = self.store.run_dir(case_id, runs_[-1]["run_id"])
        info = kill_orphan(run_dir)
        if not info.get("killed"):
            raise TeeError(
                "wt_no_orphan",
                f"No live solver for {case_id}/{runs_[-1]['run_id']} (pid {info.get('pid')} "
                f"{'reused' if info.get('pid_reused') else 'gone'}).",
                fix="Nothing to stop.",
            )
        runs_[-1]["state"] = "cancelled"
        self.store.add_run(case_id, runs_[-1])
        return {
            "case_id": case_id,
            "run_id": runs_[-1]["run_id"],
            "stopped": True,
            "how": "orphan",
            "pid": info.get("pid"),
        }

    # -- geometry ------------------------------------------------------------
    def geom(self, args: dict[str, Any]) -> dict[str, Any]:
        kind = str(args.get("kind") or "wing")
        gid = "geom_" + str(time.time_ns())[-10:]
        out_dir = self.store.root / "geometry" / gid
        out_dir.mkdir(parents=True, exist_ok=True)
        if kind == "wing":
            g = self._build_wing(
                runs.wing_from_spec(args), out_dir, stem=str(args.get("name") or "wing")
            )
        elif kind == "from_stl":
            path = Path(str(args.get("stl") or "")).expanduser()
            if not path.is_file():
                raise TeeError(
                    "wt_geometry_missing", f"{path} does not exist.", fix="Give the STL's path."
                )
            g = runs.body_from_stl(path, out_dir, str(args.get("units", "m")))
        else:
            raise TeeError(
                "wt_bad_action",
                f"kind '{kind}' is not wing or from_stl.",
                fix="kind=wing with wing={...}, or kind=from_stl with stl=path.",
            )
        g["geom_id"] = gid
        runs.dump_json(out_dir / "geom.json", g)
        return digest({k: v for k, v in g.items() if k != "loop"})

    # -- meshing -------------------------------------------------------------
    def mesh(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        engine = rec["engine"]
        edir = Path(rec["engine_dir"])
        edir.mkdir(parents=True, exist_ok=True)
        if engine == "vspaero":
            return digest(
                {
                    "case_id": case_id,
                    "kind": "vlm",
                    "note": "a vortex-lattice case has no volume mesh; wt_sweep runs it",
                    "next": "wt_sweep",
                }
            )
        if rec["kind"] == "airfoil2d":
            if engine == "openfoam":
                install = self._openfoam()
                mesh = runs.mesh_airfoil_openfoam(
                    rec,
                    edir,
                    yplus=float(args.get("y_plus", 1.0)),
                    nj=int(args.get("nj", 80)),
                    radius_c=float(args.get("radius_c", 50.0)),
                    first_cell_c=(
                        float(args["first_cell_c"]) if args.get("first_cell_c") else None
                    ),
                )
                check = self._checkmesh(install, edir)
                mesh["checkMesh"] = check
                mesh["ok"] = _mesh_ok(check)
            else:
                mesh = runs.mesh_airfoil_su2(
                    rec,
                    edir,
                    first_cell_c=float(args.get("first_cell_c", 0.005)),
                    nj=int(args.get("nj", 50)),
                    radius_c=float(args.get("radius_c", 50.0)),
                )
                mesh["ok"] = mesh["min_jacobian"] > 0
            self.store.update(case_id, mesh=mesh, state="meshed")
            out = {"case_id": case_id, **mesh}
            out["next"] = "wt_run"
            return digest(out)
        if rec["kind"] == "adopted":
            return digest(self._mesh_adopted(rec, args))
        # 3-D: a job
        return digest(self._mesh_3d(rec, args))

    def _checkmesh(self, install, case_dir: Path) -> dict[str, Any]:
        import subprocess

        foam.write_mesh_system(case_dir)  # checkMesh insists on system/controlDict
        res = subprocess.run(
            install.argv("checkMesh", "-case", str(case_dir)),
            capture_output=True,
            text=True,
            timeout=600,
        )
        text = res.stdout + res.stderr
        (case_dir / "log.checkMesh").write_text(text)
        check = foam.parse_checkmesh(text)
        if "cells" not in check:  # it did not even count the cells: say why
            check["error"] = " | ".join(foam.last_error_lines(text, 3))[:300]
            check["log"] = str(case_dir / "log.checkMesh")
        return check

    def _mesh_3d(self, rec: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        case_id = rec["case_id"]
        install = self._openfoam(for_writer=True)  # snappy dictionaries are TEE's dialect
        edir = Path(rec["engine_dir"])
        rec["domain"]
        L = max(rec["geometry"]["length_m"], 1e-6)
        # the background box is uniform, so it stays coarse (a quarter of the
        # body length) and the surface levels do the refining: level 3-4 on
        # L/4 is L/32..L/64 at the wall, the usual snappy practice
        base = float(args.get("base_cell_m", L / 4.0))
        levels = tuple(int(x) for x in (args.get("levels") or (3, 4)))
        layers = int(args.get("layers", 5))
        cores = int(args.get("cores", 1))
        prep = runs.write_tunnel_3d(rec, edir, base_cell_m=base, levels=levels, layers=layers)
        seq = runs.mesh_sequence_3d(install, edir, cores)
        est_cells = prep["background_cells"] * 4
        ledger_key = f"{case_id}@mesh"
        self.app.machine.register_job(ledger_key, "cfd-mesh")
        run_dir = edir
        current: dict[str, SolverRun | None] = {"run": None}

        def worker() -> dict[str, Any]:
            try:
                for app_name, argv in seq:
                    r = SolverRun(
                        RunSpec(
                            run_id="mesh",
                            case_id=case_id,
                            engine="cfd-mesh",
                            argv=argv,
                            cwd=run_dir,
                            log_name=f"log.{app_name}",
                            timeout_s=float(args.get("timeout_s", 7200)),
                        )
                    )
                    current["run"] = r
                    res = r.run()
                    if res["rc"] != 0 or res["state"] != "done":
                        text = (run_dir / f"log.{app_name}").read_text(errors="replace")
                        raise TeeError(
                            "wt_mesh_failed",
                            f"{app_name} failed ({res['state']}).",
                            fix=" | ".join(foam.last_error_lines(text, 3))[:300]
                            + f" - full log: {run_dir / ('log.' + app_name)}",
                        )
                check = foam.parse_checkmesh(
                    (run_dir / "log.checkMesh").read_text(errors="replace")
                )
                mesh = {
                    "kind": "snappy",
                    "body": prep["body"],
                    **check,
                    "levels": list(levels),
                    "layers": layers,
                    "base_cell_m": base,
                    "mesh_hash": runs._polymesh_hash(run_dir),
                    "ok": _mesh_ok(check),
                }
                self.store.update(case_id, mesh=mesh, state="meshed")
                return {
                    "case_id": case_id,
                    **mesh,
                    "next": "wt_run"
                    if mesh["ok"]
                    else "wt_run force=true, or re-mesh with other levels/layers",
                }
            finally:
                self.app.machine.release_job(ledger_key)

        def on_cancel() -> None:
            r = current["run"]
            if r is not None:
                r.terminate()

        try:
            job = self.app.jobs.submit(
                f"wt_mesh {case_id}", worker, qos="batch", engine="cfd-mesh", on_cancel=on_cancel
            )
        except TeeError:
            self.app.machine.release_job(ledger_key)
            raise
        self.store.update(case_id, state="meshing", mesh_job=job)
        return {
            "job": job,
            "case_id": case_id,
            "engine": "cfd-mesh",
            "sequence": [n for n, _ in seq],
            "est_cells": est_cells,
            "note": "poll tee_job; blockMesh + surfaceFeatureExtract + snappyHexMesh + checkMesh",
        }

    def _mesh_adopted(self, rec: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        if rec["engine"] != "openfoam":
            return {
                "case_id": rec["case_id"],
                "note": "an adopted SU2/OpenVSP case carries its mesh",
                "next": "wt_run",
            }
        install = self._openfoam()
        edir = Path(rec["engine_dir"])
        if (rec.get("mesh") or {}).get("has_mesh") and not args.get("remesh"):
            # the case arrived with a polyMesh: never re-run its meshing
            # sequence unasked, just measure what it has
            check = self._checkmesh(install, edir)
            mesh = {
                "kind": "adopted",
                "has_mesh": True,
                "checkMesh": check,
                "mesh_hash": runs._polymesh_hash(edir),
                "ok": _mesh_ok(check),
                "cells": check.get("cells"),
            }
            self.store.update(rec["case_id"], mesh=mesh, state="meshed")
            return {
                "case_id": rec["case_id"],
                **mesh,
                "note": "the adopted mesh was checked, not rebuilt (remesh=true reruns its "
                "sequence)",
                "next": "wt_run",
            }
        seq_names = rec.get("adopted", {}).get("sequence") or []
        mesh_steps = [
            s
            for s in seq_names
            if s[0]
            in (
                "blockMesh",
                "surfaceFeatureExtract",
                "surfaceFeatures",
                "snappyHexMesh",
                "cartesianMesh",
                "extrudeMesh",
                "createPatch",
                "renumberMesh",
            )
        ]
        if not mesh_steps:
            mesh_steps = [
                list(s)
                for s in foam.default_sequence((edir / "system" / "snappyHexMeshDict").is_file())
            ]
        argvs = [
            (s[0], install.argv(s[0], "-case", str(edir), *[a for a in s[1:] if a != "-case"]))
            for s in mesh_steps
        ]
        if not any(s[0] == "checkMesh" for s in mesh_steps):
            argvs.append(("checkMesh", install.argv("checkMesh", "-case", str(edir))))
        case_id = rec["case_id"]
        ledger_key = f"{case_id}@mesh"
        self.app.machine.register_job(ledger_key, "cfd-mesh")
        current: dict[str, SolverRun | None] = {"run": None}

        def worker() -> dict[str, Any]:
            try:
                for app_name, argv in argvs:
                    r = SolverRun(
                        RunSpec(
                            run_id="mesh",
                            case_id=case_id,
                            engine="cfd-mesh",
                            argv=argv,
                            cwd=edir,
                            log_name=f"log.{app_name}",
                            timeout_s=7200.0,
                        )
                    )
                    current["run"] = r
                    res = r.run()
                    if res["rc"] != 0:
                        text = (edir / f"log.{app_name}").read_text(errors="replace")
                        raise TeeError(
                            "wt_mesh_failed",
                            f"{app_name} failed.",
                            fix=" | ".join(foam.last_error_lines(text, 3))[:300],
                        )
                check = foam.parse_checkmesh((edir / "log.checkMesh").read_text(errors="replace"))
                mesh = {
                    "kind": "adopted",
                    **check,
                    "mesh_hash": runs._polymesh_hash(edir),
                    "ok": _mesh_ok(check),
                    "has_mesh": True,
                }
                self.store.update(case_id, mesh=mesh, state="meshed")
                return {"case_id": case_id, **mesh, "next": "wt_run"}
            finally:
                self.app.machine.release_job(ledger_key)

        def on_cancel() -> None:
            if current["run"] is not None:
                current["run"].terminate()

        try:
            job = self.app.jobs.submit(
                f"wt_mesh {case_id}", worker, qos="batch", engine="cfd-mesh", on_cancel=on_cancel
            )
        except TeeError:
            self.app.machine.release_job(ledger_key)
            raise
        return {
            "job": job,
            "case_id": case_id,
            "sequence": [s[0] for s in mesh_steps],
            "note": "poll tee_job; the case's own meshing sequence, run binary by binary",
        }

    # -- solving -------------------------------------------------------------
    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        aoa = float(args.get("aoa_deg", rec.get("conditions", {}).get("aoa_deg", 0.0)))
        return digest(self._submit_runs(rec, [aoa], args, label="wt_run"))

    def sweep(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        alphas = [float(a) for a in (args.get("aoa") or [])]
        if not alphas:
            raise TeeError(
                "wt_bad_conditions", "aoa= needs at least one angle.", fix="aoa=[-2, 0, 2, 4, 6]"
            )
        if len(alphas) > case_mod.MAX_ARRAY:
            raise TeeError(
                "wt_sweep_too_long",
                f"{len(alphas)} points; the digest law allows 64.",
                fix="Split the sweep, or coarsen it.",
            )
        return digest(self._submit_runs(rec, alphas, args, label="wt_sweep"))

    def _live_job(self, rec: dict[str, Any]) -> str | None:
        """The job id of a run of this case that the job manager still holds
        as queued or running - a run record alone is a claim; the manager
        is the evidence (a server restart leaves records, not jobs)."""
        for r in rec.get("runs", []):
            job = r.get("job")
            if r.get("state") in ("queued", "running") and job:
                try:
                    st = self.app.jobs.status(job)
                except TeeError:
                    continue
                if st.get("state") in ("queued", "running"):
                    return str(job)
        return None

    def _submit_runs(
        self, rec: dict[str, Any], alphas: list[float], args: dict[str, Any], *, label: str
    ) -> dict[str, Any]:
        case_id = rec["case_id"]
        engine = rec["engine"]
        live_job = self._live_job(rec)
        if live_job or live_run_for_case(case_id) is not None:
            raise TeeError(
                "wt_already_running",
                f"Case {case_id} already has a live run"
                + (f" (job {live_job})" if live_job else " (a solver process)")
                + ".",
                fix="Wait for it (tee_job / wt_status), cancel it (tee_job action=cancel), "
                "or wt_case action=stop for an orphan.",
            )
        cores = int(args.get("cores", self.cfg.get("cores", 1)) or 1)
        edir = Path(rec["engine_dir"])
        mesh = rec.get("mesh") or {}
        if engine in ("openfoam", "su2") and not mesh:
            raise TeeError("wt_no_mesh", f"Case {case_id} has no mesh yet.", fix="wt_mesh first.")
        if engine == "openfoam" and mesh and not mesh.get("ok", True) and not args.get("force"):
            chk = mesh.get("checkMesh") or mesh
            what = (
                f"checkMesh failed {chk.get('failed_checks', '?')} checks: "
                f"{chk.get('failed', [])[:3]}"
                if "cells" in chk
                else f"checkMesh did not run: {chk.get('error', 'no output')}"
            )
            raise TeeError(
                "wt_mesh_unhealthy",
                what,
                fix="Re-mesh with other levels/layers, or wt_run force=true to run on it anyway.",
            )
        if isinstance(args.get("forces"), dict):
            if engine != "openfoam" or rec.get("kind") != "adopted":
                raise TeeError(
                    "wt_bad_action",
                    "forces= is for an ADOPTED OpenFOAM case; TEE-written cases already "
                    "integrate forces.",
                    fix="Drop forces=, or adopt the case first.",
                )
            runs.check_forces(rec, args["forces"])  # refuse now, never inside the job
        cells = int(mesh.get("cells", 0) or 0)
        iters = int(args.get("iters", DEFAULT_ITERS.get(engine, 2000)))
        est = fidelity.estimate(
            engine, cells=cells, iters=iters, cores=cores, sweep_points=len(alphas)
        )
        why = fidelity.needs_confirmation(
            est,
            cells,
            confirm_above_s=float(self.cfg.get("confirm_above_s", fidelity.CONFIRM_ABOVE_S)),
        )
        if why and not args.get("confirm_cost"):
            raise TeeError(
                "wt_cost_confirmation_required",
                f"{label}: {why}.",
                fix=f"Re-call with confirm_cost=true; estimate {est['wall_s']} s, "
                f"{est['footprint_gb']} GB, {cells:,} cells x {iters} iterations x "
                f"{len(alphas)} point(s) ({est['measured_on']}).",
            )
        timeout = min(
            float(args.get("timeout_s", max(2.0 * est["wall_s"], DEFAULT_TIMEOUT_S))),
            float(self.cfg.get("max_wall_s", MAX_WALL_S)),
        )
        # engine binaries resolved NOW so the refusal is immediate, not inside the job
        if engine == "openfoam":
            install = self._openfoam(for_writer=rec.get("kind") != "adopted")
            su2_bin = vspb = None
        elif engine == "su2":
            install = None
            su2_bin = self._su2()
            vspb = None
        else:
            install = su2_bin = None
            vspb = self._vsp()
        run_ids = [self.store.new_run_id(case_id)] if engine == "vspaero" else []
        if engine != "vspaero":
            base = int(self.store.new_run_id(case_id).split("_")[1])
            run_ids = [f"run_{base + k:03d}" for k in range(len(alphas))]
        ledger_engine = "aero-panel" if engine == "vspaero" else "cfd-solve"
        ledger_key = f"{case_id}@{run_ids[0]}"
        try:
            self.app.machine.register_job(
                ledger_key, ledger_engine, footprint_gb=est["footprint_gb"]
            )
        except TypeError:
            self.app.machine.register_job(ledger_key, ledger_engine)
        current: dict[str, SolverRun | None] = {"run": None}
        cancelled = {"flag": False}
        for rid in run_ids:
            self.store.add_run(
                case_id,
                {"run_id": rid, "state": "queued", "engine": engine, "submitted_at": time.time()},
            )

        def worker() -> dict[str, Any]:
            try:
                results = []
                for rid, aoa in (
                    zip(run_ids, alphas, strict=True)
                    if engine != "vspaero"
                    else [(run_ids[0], None)]
                ):
                    if cancelled["flag"]:
                        break
                    results.append(
                        self._one_run(
                            rec,
                            rid,
                            aoa if aoa is not None else alphas,
                            engine,
                            edir,
                            install,
                            su2_bin,
                            vspb,
                            iters=iters,
                            cores=cores,
                            timeout=timeout,
                            current=current,
                            cancelled=cancelled,
                            sweep=(engine == "vspaero"),
                            strict=(len(alphas) == 1 or engine == "vspaero"),
                            forces=args.get("forces")
                            if isinstance(args.get("forces"), dict)
                            else None,
                        )
                    )
                if engine == "vspaero" or len(results) == 1:
                    return results[0] if results else {"state": "cancelled"}
                polar = [
                    {
                        "aoa_deg": a,
                        "run_id": r["run_id"],
                        **{k: r.get(k) for k in ("cl", "cd", "cm", "l_over_d")},
                        "state": r.get("verdict", {}).get("state"),
                    }
                    for a, r in zip(alphas, results, strict=False)
                ]
                sweep_res = {
                    "case_id": case_id,
                    "sweep": True,
                    "points": len(polar),
                    "polar": polar,
                    "engine": engine,
                }
                if len(polar) >= 2 and all(p.get("cl") is not None for p in polar):
                    da = math.radians(polar[-1]["aoa_deg"] - polar[0]["aoa_deg"])
                    if abs(da) > 1e-9:
                        sweep_res["cl_alpha_per_rad"] = round(
                            (polar[-1]["cl"] - polar[0]["cl"]) / da, 4
                        )
                self.store.update(case_id, last_sweep=sweep_res)
                return digest(sweep_res)
            finally:
                self.app.machine.release_job(ledger_key)
                for rid in run_ids:
                    forget(case_id, rid)

        def on_cancel() -> None:
            cancelled["flag"] = True
            r = current["run"]
            if r is not None:
                r.terminate()
                # The worker still has a harvest to finish before its own
                # write and release; a reader right after cancel must not
                # see `running`, and a dead solver must stop deferring LLM
                # engine swaps at once - release_job is an idempotent pop,
                # so the worker's finally stays the backstop. (The Mac loses
                # both races where Linux happened to win them.)
                self.store.add_run(case_id, {"run_id": r.spec.run_id, "state": "cancelled"})
                self.app.machine.release_job(ledger_key)

        try:
            job = self.app.jobs.submit(
                f"{label} {case_id}",
                worker,
                qos="standard" if engine == "vspaero" else "batch",
                engine=ledger_engine,
                on_cancel=on_cancel,
            )
        except TeeError:
            self.app.machine.release_job(ledger_key)
            for rid in run_ids:  # never leave a phantom `queued` run behind
                forget(case_id, rid)
                self.store.add_run(case_id, {"run_id": rid, "state": "refused", "engine": engine})
            self.store.update(case_id, state="meshed" if rec.get("mesh") else rec.get("state"))
            raise
        for rid in run_ids:  # the manager's id travels with the record (merge keeps it)
            self.store.add_run(case_id, {"run_id": rid, "job": job})
        out = {
            "job": job,
            "case_id": case_id,
            "run_id": run_ids[0],
            "run_ids": run_ids,
            "engine": ledger_engine,
            "est": est,
            "cells": cells,
            "iters": iters,
            "points": len(alphas),
            "note": "poll tee_job for the result; wt_status for residuals and coefficients while "
            "it runs; tee_job cancel kills the solver",
        }
        if why:
            out["confirmed"] = why
        return out

    def _one_run(
        self,
        rec,
        rid,
        aoa,
        engine,
        edir,
        install,
        su2_bin,
        vspb,
        *,
        iters,
        cores,
        timeout,
        current,
        cancelled,
        sweep,
        strict=True,
        forces=None,
    ) -> dict[str, Any]:
        case_id = rec["case_id"]
        run_dir = self.store.run_dir(case_id, rid)
        started = time.time()
        record: dict[str, Any] = {
            "run_id": rid,
            "state": "running",
            "engine": engine,
            "run_dir": str(run_dir),
            "started_at": started,
        }
        solver_app = "simpleFoam"
        if engine == "openfoam" and rec.get("kind") == "adopted":
            # the case's own dictionaries, its own solver, never TEE's
            prep = runs.prepare_adopted_openfoam_run(rec, run_dir, edir, forces=forces)
            solver_app = prep["application"]
            argvs = runs.openfoam_argv(install, run_dir, cores, app=solver_app)
            progress = runs.openfoam_progress
            record.update(
                {"application": solver_app, "adopted": True, "engine_version": install.version}
            )
            if prep.get("forces"):
                record["forces"] = prep["forces"]
        elif engine == "openfoam":
            prep = runs.prepare_openfoam_run(
                rec, run_dir, edir, aoa_deg=float(aoa), iters=iters, cores=cores
            )
            argvs = runs.openfoam_argv(install, run_dir, cores)
            progress = runs.openfoam_progress
            record.update(
                {"aoa_deg": float(aoa), "Aref": prep["Aref"], "engine_version": install.version}
            )
        elif engine == "su2":
            solver = "EULER" if rec.get("fidelity", {}).get("chosen") == "euler" else "RANS"
            prep = runs.prepare_su2_run(
                rec, run_dir, edir, aoa_deg=float(aoa), iters=iters, solver=solver
            )
            argvs = runs.su2_argv(su2_bin, run_dir, cores)
            progress = runs.su2_progress
            record.update({"aoa_deg": float(aoa), "solver": solver})
        else:
            alphas = list(aoa)
            cond = rec.get("conditions", {})
            prep = runs.prepare_vsp_run(
                rec,
                run_dir,
                edir,
                alphas=alphas,
                mach=float(cond.get("mach", 0.1)),
                re_cref=float(cond["Re"]) if cond.get("Re") else None,
                ncpu=max(cores, 1),
            )
            argvs = runs.vsp_argv(vspb.path, run_dir)
            progress = runs.vsp_progress
            record.update({"alphas": alphas})
        # the SOLVER's argv (a parallel run is decomposePar / solver / reconstructPar)
        record["argv"] = next((a for n, a in argvs if n == solver_app), argvs[-1][1])
        record["steps"] = [n for n, _ in argvs]
        if engine == "openfoam" and not record.get("engine_version"):
            probed = (self._probe or {}).get("engines", {}).get("openfoam", {})
            record["engine_version"] = str(probed.get("version") or "")
        env_extra = runs.mpi_env(cores) if engine in ("openfoam", "su2") else {}
        if env_extra:
            record["mpi_root_override"] = True  # a root container: Open MPI told twice
        self.store.add_run(case_id, record)
        fatal = False
        state = "done"
        for app_name, argv in argvs:
            r = SolverRun(
                RunSpec(
                    run_id=rid,
                    case_id=case_id,
                    engine=engine,
                    argv=argv,
                    cwd=run_dir,
                    log_name=f"log.{app_name}",
                    timeout_s=timeout,
                    env=env_extra,
                    label=f"{case_id}/{rid}",
                ),
                progress_fn=progress,
            )
            current["run"] = r
            register(r)
            res = r.run()
            state = res["state"]
            if state != "done":
                fatal = state == "error"
                break
        record.update(
            {"state": state, "wall_s": round(time.time() - started, 2), "finished_at": time.time()}
        )
        try:
            if engine == "openfoam":
                result = runs.openfoam_result(
                    run_dir,
                    iters=iters,
                    ended=True,
                    fatal=fatal,
                    cancelled=cancelled["flag"] or state == "cancelled",
                    app=solver_app,
                )
            elif engine == "su2":
                result = runs.su2_result(
                    run_dir,
                    ended=True,
                    fatal=fatal,
                    cancelled=cancelled["flag"] or state == "cancelled",
                )
            else:
                result = runs.vsp_result(
                    run_dir,
                    ended=True,
                    fatal=fatal,
                    cancelled=cancelled["flag"] or state == "cancelled",
                )
        except TeeError as exc:
            if state == "cancelled":
                record["result"] = {"verdict": {"state": "cancelled"}}
                self.store.add_run(case_id, record)
                return {**record, "case_id": case_id}
            record["error"] = f"{exc.code}: {exc.message}"
            self.store.add_run(case_id, record)
            raise
        result["uncertainty"] = self._label(
            rec, result, aoa if not sweep else (alphas[-1] if alphas else 0.0)
        )
        if state == "error" and result.get("verdict", {}).get("state") not in ("error", None):
            # the exit code was a claim and the outputs are the evidence:
            # vspscript exits 2 after a complete sweep (measured 2026-09-06)
            state = "done"
            record["state"] = "done"
            record["exit_code_overruled"] = True
        record["result"] = result
        if "polar" in result:
            record["polar"] = result["polar"]
        self.store.add_run(case_id, record)
        if state == "error" and strict:
            # a single run that crashed is a failed job, not a result with a
            # sad verdict; a sweep carries on and marks the point instead
            log = run_dir / f"log.{argvs[-1][0]}"
            tail = foam.last_error_lines(log.read_text(errors="replace") if log.is_file() else "")
            raise TeeError(
                "wt_solver_failed",
                f"{case_id}/{rid}: {argvs[-1][0]} exited with an error.",
                fix=(" | ".join(tail)[:300] + f" - full log: {log}") if tail else f"See {log}.",
            )
        out = {
            "case_id": case_id,
            "run_id": rid,
            "engine": engine,
            "state": state,
            "wall_s": record["wall_s"],
            **{k: v for k, v in result.items() if k not in ("residuals_last",)},
        }
        if engine == "openfoam":
            out["mesh_hash"] = rec.get("mesh", {}).get("mesh_hash")
        return digest(out)

    def _label(self, rec: dict[str, Any], result: dict[str, Any], aoa: float) -> dict[str, str]:
        fid = rec.get("fidelity", {}).get("chosen", "rans")
        regime = rec.get("conditions", {}).get("regime", "incompressible")
        state = result.get("verdict", {}).get("state", "insufficient")
        mesh = rec.get("mesh") or {}
        yplus_ok = None
        if rec["engine"] == "openfoam" and mesh.get("kind") == "omesh_polymesh":
            yplus_ok = float(mesh.get("y_plus_target", 1.0)) <= 5.0
        return verdict.uncertainty(
            fidelity=fid, regime=regime, aoa_deg=float(aoa), state=state, yplus_ok=yplus_ok
        )

    # -- reading -------------------------------------------------------------
    def status(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        run = self.store.find_run(case_id, args.get("run_id"))
        run_dir = self.store.run_dir(case_id, run["run_id"])
        prog = runs.load_progress(run_dir) or {}
        out: dict[str, Any] = {
            "case_id": case_id,
            "run_id": run["run_id"],
            "state": prog.get("state") or run.get("state"),
        }
        for key in (
            "iter",
            "elapsed_s",
            "residuals",
            "coeffs",
            "trend",
            "phase",
            "fatal",
            "error",
            "bounded",
            "warnings",
        ):
            if key in prog:
                out[key] = prog[key]
        if out["state"] == "queued" and run.get("job"):
            # the record says queued; the job manager is the evidence
            out["job"] = run["job"]
            try:
                st = self.app.jobs.status(str(run["job"]))
            except TeeError:
                st = {}
            if st.get("state") in ("error", "cancelled"):
                out["state"] = st["state"]
                if st.get("error"):
                    out["error"] = str(st["error"])[:300]
            elif st.get("state") == "queued":
                out["note"] = "queued behind other work; tee_job shows the queue"
        if out["state"] == "running":
            live = live_run_for_case(case_id)
            if live is None:
                info = orphan_check(run_dir)
                out["state"] = (
                    "orphan"
                    if info.get("alive")
                    else ("dead" if info.get("known") else out["state"])
                )
                if info.get("pid"):
                    out["pid"] = info["pid"]
            iters_cap = run.get("iters") or DEFAULT_ITERS.get(rec["engine"], 2000)
            it = out.get("iter")
            el = out.get("elapsed_s")
            if it and el and it > 5:
                out["eta_s"] = round(el * (iters_cap - it) / it, 1)
        if run.get("result") and "verdict" in run["result"]:
            out["verdict"] = run["result"]["verdict"].get("state")
        return digest(out)

    def result(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        run = self.store.find_run(case_id, args.get("run_id"))
        run_dir = self.store.run_dir(case_id, run["run_id"])
        result = run.get("result")
        partial = False
        if run.get("state") == "error" and not args.get("allow_partial"):
            # a crashed solver is a failure to report, never a number to quote
            log_name = {"openfoam": "log.simpleFoam", "su2": "log.SU2_CFD"}.get(
                rec["engine"], "log.vspscript"
            )
            log = Path(run.get("run_dir") or run_dir) / log_name
            tail = foam.last_error_lines(
                log.read_text(errors="replace") if log.is_file() else "", 3
            )
            raise TeeError(
                "wt_solver_failed",
                f"{case_id}/{run['run_id']} failed: {run.get('error') or 'the solver exited'}.",
                fix=(" | ".join(tail)[:300] + f" - full log: {log}")
                if tail
                else f"See {log}; allow_partial=true returns whatever was written.",
            )
        if result is None:
            if not args.get("allow_partial"):
                raise TeeError(
                    "wt_unconverged",
                    f"{case_id}/{run['run_id']} is {run.get('state')}: no final result yet.",
                    fix="Poll wt_status, or allow_partial=true for the current numbers, labelled.",
                )
            partial = True
            # the store's terminal state is authoritative: right after a
            # cancel the worker may still be harvesting, and a partial read
            # must not call a cancelled run `running`
            was_cancelled = run.get("state") == "cancelled"
            if rec["engine"] == "openfoam":
                result = runs.openfoam_result(
                    run_dir,
                    iters=run.get("iters", 0),
                    ended=False,
                    fatal=False,
                    cancelled=was_cancelled,
                    window_pct=float(args.get("window_pct", 20.0)),
                )
            elif rec["engine"] == "su2":
                result = runs.su2_result(
                    run_dir,
                    ended=False,
                    fatal=False,
                    cancelled=was_cancelled,
                    window_pct=float(args.get("window_pct", 20.0)),
                )
            else:
                result = runs.vsp_result(run_dir, ended=False, fatal=False, cancelled=was_cancelled)
            result["uncertainty"] = self._label(rec, result, float(run.get("aoa_deg", 0.0)))
        out: dict[str, Any] = {
            "case_id": case_id,
            "run_id": run["run_id"],
            "engine": rec["engine"],
            "engine_version": run.get("engine_version"),
            "fidelity": rec.get("fidelity", {}).get("chosen"),
            "aoa_deg": run.get("aoa_deg"),
            "mach": rec.get("conditions", {}).get("mach"),
            "Re": rec.get("conditions", {}).get("Re"),
            "mesh_hash": rec.get("mesh", {}).get("mesh_hash"),
            "partial": partial,
            "wall_s": run.get("wall_s"),
        }
        out.update({k: v for k, v in result.items() if k not in ("residuals_last", "columns")})
        if result.get("verdict", {}).get("state") == "diverged" and not args.get("allow_partial"):
            raise TeeError(
                "wt_diverged",
                f"{case_id}/{run['run_id']} diverged: {result['verdict'].get('notes')}.",
                fix="Usual causes: a mesh checkMesh flagged, too aggressive relaxation, or a "
                "first-order start skipped; re-mesh or lower the relaxation; allow_partial=true "
                "returns the last finite numbers.",
            )
        if args.get("compare_to"):
            other_case, other_run = self.store.resolve(str(args["compare_to"]))
            orec = self.store.load(other_case)
            orun = self.store.find_run(other_case, other_run)
            if orun.get("result"):
                out["compare"] = {
                    "to": f"{other_case}/{orun['run_id']}",
                    "same_mesh": orec.get("mesh", {}).get("mesh_hash")
                    == rec.get("mesh", {}).get("mesh_hash"),
                    **verdict.compare(orun["result"], result),
                }
        return digest(out)

    # -- post-processing -----------------------------------------------------
    def _volume_source(self, rec: dict[str, Any], run: dict[str, Any]) -> Path:
        from tee.windtunnel import paraview as pv

        run_dir = Path(run["run_dir"])
        if rec["engine"] == "openfoam":
            return pv.foam_stub(run_dir)
        if rec["engine"] == "su2":
            vol = run_dir / "flow.vtu"
            if not vol.is_file():
                raise TeeError(
                    "wt_no_results",
                    "SU2 has not written flow.vtu yet.",
                    fix="Wait for the run to finish (OUTPUT_WRT_FREQ).",
                )
            return vol
        raise TeeError(
            "wt_field_missing",
            "A vortex-lattice run has no volume field.",
            fix="Use wt_result's polar and span loads; fields need a RANS/Euler case.",
        )

    def probe_field(self, args: dict[str, Any]) -> dict[str, Any]:
        from tee.windtunnel import paraview as pv

        case_id = _case_id(args)
        rec = self.store.load(case_id)
        run = self.store.find_run(case_id, args.get("run_id"))
        src = self._volume_source(rec, run)
        pvpython = self._pvpython()
        work = Path(run["run_dir"]) / "probe"
        field = str(args.get("field", "U"))
        what = str(args.get("what", "line"))
        if what == "line":
            p1 = tuple(float(x) for x in (args.get("p1") or (0.0, 0.0, 0.0)))
            p2 = tuple(float(x) for x in (args.get("p2") or (1.0, 0.0, 0.0)))
            n = min(int(args.get("n", 32)), case_mod.MAX_ARRAY)
            out_csv = work / "line.csv"
            pv.run_script(pvpython, pv.line_script(src, p1, p2, n, out_csv), work, render=False)
            cols = pv.read_csv_columns(out_csv)
            sample = pv.csv_sample(cols, field, limit=n, components=bool(args.get("components")))
            return digest(
                {
                    "case_id": case_id,
                    "run_id": run["run_id"],
                    "what": "line",
                    "field": field,
                    "p1": list(p1),
                    "p2": list(p2),
                    **sample,
                    "engine": "pvpython",
                }
            )
        origin = tuple(float(x) for x in (args.get("origin") or (0.5, 0.0, 0.0)))
        normal = tuple(float(x) for x in (args.get("normal") or (0.0, 0.0, 1.0)))
        out_csv = work / "slice.csv"
        pv.run_script(
            pvpython, pv.slice_stats_script(src, origin, normal, field, out_csv), work, render=False
        )
        cols = pv.read_csv_columns(out_csv)
        keys = [k for k in cols if k == field or k.startswith(field + ":")]
        if not keys:
            raise TeeError(
                "wt_field_missing",
                f"'{field}' is not on the slice ({', '.join(list(cols)[:10])}).",
                fix="Use one of the listed names.",
            )
        vals = (
            cols[keys[0]]
            if len(keys) == 1
            else [sum(cols[k][i] ** 2 for k in keys) ** 0.5 for i in range(len(cols[keys[0]]))]
        )
        return digest(
            {
                "case_id": case_id,
                "run_id": run["run_id"],
                "what": "slice",
                "field": field,
                "origin": list(origin),
                "normal": list(normal),
                "stats": pv.stats(vals),
                "engine": "pvpython",
            }
        )

    def view(self, args: dict[str, Any]) -> dict[str, Any]:
        from tee.windtunnel import paraview as pv

        case_id = _case_id(args)
        rec = self.store.load(case_id)
        run = self.store.find_run(case_id, args.get("run_id"))
        src = self._volume_source(rec, run)
        pvpython = self._pvpython()
        view = str(args.get("view", "pressure"))
        work = Path(run["run_dir"]) / "views"
        size = (int(args.get("width", 1200)), int(args.get("height", 800)))
        png = work / f"{view}.png"
        out = pv.run_script(
            pvpython,
            pv.render_script(src, view, png, size=size, plane_normal=str(args.get("plane", "z"))),
            work,
            render=True,
        )
        rng = None
        for line in out.splitlines():
            if line.startswith("RANGE"):
                parts = line.split()
                rng = {"min": float(parts[1]), "max": float(parts[2])}
        return digest(
            {
                "case_id": case_id,
                "run_id": run["run_id"],
                "view": view,
                "png": str(png),
                "bytes": png.stat().st_size if png.is_file() else 0,
                "size": list(size),
                "colour_range": rng,
                "caption": f"{view} on the {args.get('plane', 'z')}-normal mid-plane of "
                f"{case_id}/{run['run_id']}",
            }
        )

    def export(self, args: dict[str, Any]) -> dict[str, Any]:
        case_id = _case_id(args)
        rec = self.store.load(case_id)
        run = self.store.find_run(case_id, args.get("run_id"))
        out_dir = Path(
            str(args.get("out_dir") or (self.store.case_dir(case_id) / "exports"))
        ).expanduser()
        return digest(report.export(self.app, str(args.get("format", "json")), rec, run, out_dir))

    # -- verification --------------------------------------------------------
    def verify(self, args: dict[str, Any]) -> dict[str, Any]:
        from tee.windtunnel import verify as verify_mod

        return digest(
            verify_mod.run(
                self, str(args.get("case") or "all"), confirm_cost=bool(args.get("confirm_cost"))
            )
        )


# ---------------------------------------------------------------------------


def _case_id(args: dict[str, Any]) -> str:
    cid = str(args.get("case_id") or "")
    if not cid:
        raise TeeError(
            "wt_unknown_case", "case_id is required.", fix="wt_case action=list shows the ids."
        )
    return cid


def _opt_float(args: dict[str, Any], key: str) -> float | None:
    v = args.get(key)
    return None if v is None or v == "" else float(v)


def _show(rec: dict[str, Any]) -> dict[str, Any]:
    geom = dict(rec.get("geometry") or {})
    geom.pop("loop", None)
    out = {
        "case_id": rec["case_id"],
        "kind": rec.get("kind"),
        "engine": rec.get("engine"),
        "fidelity": rec.get("fidelity"),
        "state": rec.get("state"),
        "conditions": {
            k: rec["conditions"].get(k)
            for k in ("V", "mach", "Re", "q_Pa", "alt_m", "aoa_deg", "regime")
            if k in rec.get("conditions", {})
        },
        "refs": rec.get("refs"),
        "geometry": {
            k: v
            for k, v in geom.items()
            if k
            in (
                "kind",
                "name",
                "properties",
                "bbox",
                "length_m",
                "width_m",
                "height_m",
                "tris",
                "watertight",
                "open_edges",
                "frontal_area_m2",
                "planform_area_m2",
                "wetted_area_m2",
                "warning",
                "span",
                "area_ref_m2",
                "mac",
                "aspect_ratio",
                "vsp3",
                "stl",
                "dat",
            )
        },
        "runs": [
            {k: r.get(k) for k in ("run_id", "state", "aoa_deg", "wall_s")}
            for r in rec.get("runs", [])
        ][-16:],
    }
    if rec.get("domain"):
        d = rec["domain"]
        out["domain"] = {
            "blockage_pct": round(100.0 * d["blockage"], 2),
            "verdict": d.get("verdict"),
            "size_m": [
                round(d["xmax"] - d["xmin"], 3),
                round(d["ymax"] - d["ymin"], 3),
                round(d["zmax"] - d["zmin"], 3),
            ],
        }
    if rec.get("mesh"):
        m = rec["mesh"]
        out["mesh"] = {
            k: m.get(k)
            for k in (
                "kind",
                "cells",
                "ok",
                "max_skew",
                "max_nonortho",
                "failed_checks",
                "mesh_hash",
                "first_cell_m",
                "y_plus_target",
            )
            if k in m
        }
    return out
