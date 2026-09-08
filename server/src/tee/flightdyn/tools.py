"""The fd_* virtual tools (A75).

Registered into the progressive-disclosure registry, so this lane adds ZERO
tools to the always-loaded surface. Every reply is a digest: the trim state,
the verdict and the mode table - never a time history, which doc 76 measured at
2,152x the useful answer. Heavy work runs OUT OF PROCESS, because
`FGLinearization` on an aircraft with no engine SIGSEGVs rather than raising.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tee.flightdyn import aircraft as ac
from tee.flightdyn import probe as probe_mod
from tee.flightdyn.store import AircraftStore
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

WORKER_TIMEOUT_S = 300


class _Lane:
    def __init__(self, app, store: AircraftStore, cfg: dict[str, Any]) -> None:
        self.app = app
        self.store = store
        self.cfg = cfg

    # -- the child process ------------------------------------------------
    def _call_worker(self, job: dict[str, Any]) -> dict[str, Any]:
        try:
            r = subprocess.run(
                [sys.executable, "-m", "tee.flightdyn.worker"],
                input=json.dumps(job),
                capture_output=True,
                text=True,
                timeout=self.cfg.get("timeout_s", WORKER_TIMEOUT_S),
            )
        except subprocess.TimeoutExpired as exc:
            raise TeeError(
                "fd_worker_timeout",
                "The flight-dynamics worker did not answer in "
                f"{self.cfg.get('timeout_s', WORKER_TIMEOUT_S)} s.",
                fix="Raise [flightdyn] timeout_s, or trim at a gentler condition.",
            ) from exc
        if r.returncode != 0:
            tail = (r.stderr or "").strip().splitlines()[-3:]
            died = r.returncode < 0 or r.returncode == 139
            raise TeeError(
                "fd_worker_died" if died else "fd_worker_failed",
                (
                    "The flight-dynamics worker was killed by the engine "
                    f"(rc={r.returncode}). This is the SIGSEGV class JSBSim can "
                    "raise on an ill-formed aircraft; the server survived because "
                    "the call was out of process."
                    if died
                    else f"The worker exited {r.returncode}: {' | '.join(tail)}"
                ),
                fix="Check the aircraft with fd_aircraft action=show, or regenerate it.",
            )
        try:
            out = json.loads(r.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise TeeError(
                "fd_worker_garbled",
                f"The worker printed something that is not JSON: {r.stdout[:200]!r}",
                fix="Re-run; if it repeats, the jsbsim install is suspect (fd_probe).",
            ) from exc
        if "error" in out:
            if out["error"] == "fd_jsbsim_missing":
                raise TeeError(
                    "fd_jsbsim_missing",
                    "JSBSim is not installed, so nothing can be flown.",
                    fix=probe_mod.INSTALL,
                )
            raise TeeError(
                "fd_flight_failed",
                out.get("detail", "the worker reported a failure"),
                fix="fd_aircraft action=show prints what was generated.",
            )
        return out

    # -- tools -------------------------------------------------------------
    def probe(self, args: dict[str, Any]) -> dict[str, Any]:
        out = probe_mod.probe()
        out["licence"] = {
            "route": "in-process, LGPL-2.0-or-later (DECISIONS 2026-09-07)",
            "note": "the wheel's own CLI is GPL-3.0-or-later and is never used",
        }
        return out

    def aircraft(self, args: dict[str, Any]) -> dict[str, Any]:
        action = args.get("action", "create")
        aircraft_id = args.get("aircraft_id")
        polar = args.get("polar")
        mass = args.get("mass")
        geometry = args.get("geometry")
        design = args.get("design")
        if action == "list":
            ids = self.store.list_ids()
            return {"aircraft": ids, "count": len(ids)}
        if action == "show":
            aid = aircraft_id or ""
            self.store.require(aid)
            rec = self.store.read_record(aid)
            return {"aircraft": aid, **rec}
        if action != "create":
            raise TeeError(
                "fd_bad_action",
                f"Unknown action {action!r}.",
                fix="Use action=create, show or list.",
            )
        missing = [
            n for n, v in (("polar", polar), ("mass", mass), ("geometry", geometry)) if not v
        ]
        if missing:
            raise TeeError(
                "fd_aircraft_needs",
                f"create needs {', '.join(missing)}.",
                fix="polar={alpha_deg,cl,cd}, mass={mass_kg,ixx,iyy,izz}, "
                "geometry={wing_area_m2,span_m,chord_m}. SI throughout.",
            )
        aid = aircraft_id or "fd_aircraft"
        p = ac.Polar(
            alpha_deg=tuple(float(v) for v in polar["alpha_deg"]),
            cl=tuple(float(v) for v in polar["cl"]),
            cd=tuple(float(v) for v in polar["cd"]),
            cm_alpha=float(polar.get("cm_alpha", -0.5)),
            cm_q=float(polar.get("cm_q", -12.0)),
            cm_de=float(polar.get("cm_de", -1.1)),
            source=str(polar.get("source", "given")),
        )
        m = ac.Mass(
            mass_kg=float(mass["mass_kg"]),
            ixx=float(mass["ixx"]),
            iyy=float(mass["iyy"]),
            izz=float(mass["izz"]),
            cg_m=tuple(float(v) for v in mass.get("cg_m", (0.0, 0.0, 0.0))),
        )
        g = ac.Geometry(
            wing_area_m2=float(geometry["wing_area_m2"]),
            span_m=float(geometry["span_m"]),
            chord_m=float(geometry["chord_m"]),
        )
        d = ac.Design(**{k: float(v) for k, v in (design or {}).items()})
        root = self.store.path(aid)
        digest = ac.write(root, aid, p, m, g, d)
        digest["id"] = aid
        self.store.write_record(aid, digest)
        digest["next"] = "fd_trim"
        return digest

    def _flight(self, aircraft_id: str, condition: dict | None, want: list[str], hold_s: float):
        root = self.store.require(aircraft_id)
        cond = {
            "altitude_ft": float((condition or {}).get("altitude_ft", 5000.0)),
            "kcas": float((condition or {}).get("kcas", 90.0)),
            "gamma_deg": float((condition or {}).get("gamma_deg", 0.0)),
        }
        out = self._call_worker(
            {
                "root": str(root),
                "aircraft": aircraft_id,
                "condition": cond,
                "want": want,
                "hold_s": hold_s,
            }
        )
        out["aircraft"] = aircraft_id
        out["condition"] = cond
        return out

    def trim(self, args: dict[str, Any]):
        out = self._flight(args.get("aircraft_id", ""), args.get("condition"), ["trim"], 0.0)
        out["next"] = "fd_modes"
        return out

    def modes(self, args: dict[str, Any]):
        return self._flight(
            args.get("aircraft_id", ""), args.get("condition"), ["trim", "modes"], 0.0
        )

    def fly(self, args: dict[str, Any]):
        seconds = args.get("seconds", 60.0)
        if not (0 < float(seconds) <= 3600):
            raise TeeError(
                "fd_bad_duration",
                f"seconds must be in (0, 3600]; got {seconds}.",
                fix="Ask for a shorter flight; the answer is a digest either way.",
            )
        return self._flight(
            args.get("aircraft_id", ""), args.get("condition"), ["trim", "hold"], float(seconds)
        )


_POLAR_SCHEMA = {
    "type": "object",
    "description": "What wt_sweep returns: cl and cd over angle of attack.",
    "properties": {
        "alpha_deg": {"type": "array", "items": {"type": "number"}, "maxItems": 64},
        "cl": {"type": "array", "items": {"type": "number"}, "maxItems": 64},
        "cd": {"type": "array", "items": {"type": "number"}, "maxItems": 64},
        "cm_alpha": {"type": "number", "description": "Per radian. Default -0.5."},
        "cm_q": {"type": "number", "description": "Pitch damping. Default -12."},
        "cm_de": {"type": "number", "description": "Control power. Default -1.1."},
        "source": {"type": "string"},
    },
    "required": ["alpha_deg", "cl", "cd"],
}
_COND_SCHEMA = {
    "type": "object",
    "properties": {
        "altitude_ft": {"type": "number"},
        "kcas": {"type": "number"},
        "gamma_deg": {"type": "number"},
    },
}
_ID = {"type": "string", "description": "The aircraft id fd_aircraft returned."}


def register_flightdyn_tools(app, project_root: Path | str) -> AircraftStore:
    store = AircraftStore(project_root)
    cfg: dict[str, Any] = dict(getattr(getattr(app, "config", None), "flightdyn", {}) or {})
    reg = app.registry
    lane = _Lane(app, store, cfg)

    specs: list[tuple[str, str, dict, Any, list[str], list[dict]]] = [
        (
            "fd_probe",
            "Is JSBSim here, at what version, with how many bundled aircraft - and which "
            "licence route this lane uses. Never flies anything; absent, it answers with "
            "its install line.",
            {"type": "object", "properties": {"refresh": {"type": "boolean"}}},
            lane.probe,
            ["flight", "dynamics", "jsbsim", "probe", "install"],
            [{"summary": "what can this machine fly", "arguments": {}}],
        ),
        (
            "fd_aircraft",
            "Turn a polar and a mass into a JSBSim aircraft that flies. The polar is "
            "what wt_sweep returns; SI units throughout. action=show or list to see "
            "what exists.",
            {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "show", "list"]},
                    "aircraft_id": _ID,
                    "polar": _POLAR_SCHEMA,
                    "mass": {
                        "type": "object",
                        "properties": {
                            "mass_kg": {"type": "number"},
                            "ixx": {"type": "number"},
                            "iyy": {"type": "number"},
                            "izz": {"type": "number"},
                            "cg_m": {"type": "array", "items": {"type": "number"}, "maxItems": 3},
                        },
                        "required": ["mass_kg", "ixx", "iyy", "izz"],
                    },
                    "geometry": {
                        "type": "object",
                        "properties": {
                            "wing_area_m2": {"type": "number"},
                            "span_m": {"type": "number"},
                            "chord_m": {"type": "number"},
                        },
                        "required": ["wing_area_m2", "span_m", "chord_m"],
                    },
                    "design": {
                        "type": "object",
                        "properties": {
                            "speed_mps": {"type": "number"},
                            "altitude_m": {"type": "number"},
                            "thrust_margin": {"type": "number"},
                        },
                    },
                },
            },
            lane.aircraft,
            ["flight", "aircraft", "generate", "polar", "mass", "dynamics"],
            [
                {
                    "summary": "an aircraft from a swept polar",
                    "arguments": {
                        "action": "create",
                        "aircraft_id": "demo",
                        "polar": {
                            "alpha_deg": [0, 6, 12],
                            "cl": [0.26, 0.89, 1.4],
                            "cd": [0.012, 0.021, 0.047],
                        },
                        "mass": {
                            "mass_kg": 850,
                            "ixx": 1290,
                            "iyy": 1820,
                            "izz": 2670,
                        },
                        "geometry": {
                            "wing_area_m2": 16.2,
                            "span_m": 10.9,
                            "chord_m": 1.49,
                        },
                    },
                }
            ],
        ),
        (
            "fd_trim",
            "Trim the aircraft at a condition: our own Newton over angle of attack, "
            "elevator and throttle. A failure names the axis that would not converge "
            "and by how much.",
            {
                "type": "object",
                "properties": {"aircraft_id": _ID, "condition": _COND_SCHEMA},
                "required": ["aircraft_id"],
            },
            lane.trim,
            ["flight", "trim", "equilibrium", "dynamics"],
            [
                {
                    "summary": "trim at 5000 ft and 90 knots",
                    "arguments": {
                        "aircraft_id": "demo",
                        "condition": {"altitude_ft": 5000, "kcas": 90},
                    },
                }
            ],
        ),
        (
            "fd_modes",
            "The dynamic modes at a trim point: A and B, then every oscillatory mode with its "
            "period, damping and modal participation, plus a closed-form cross-check.",
            {
                "type": "object",
                "properties": {"aircraft_id": _ID, "condition": _COND_SCHEMA},
                "required": ["aircraft_id"],
            },
            lane.modes,
            ["flight", "modes", "phugoid", "stability", "eigenvalue", "damping"],
            [{"summary": "short period and phugoid", "arguments": {"aircraft_id": "demo"}}],
        ),
        (
            "fd_fly",
            "Trim, then fly the trimmed state and report whether it stayed there: altitude "
            "drift, speed, load factor. The history stays on disk; the reply is the verdict.",
            {
                "type": "object",
                "properties": {
                    "aircraft_id": _ID,
                    "condition": _COND_SCHEMA,
                    "seconds": {"type": "number", "description": "Up to 3600."},
                },
                "required": ["aircraft_id"],
            },
            lane.fly,
            ["flight", "fly", "simulate", "hold", "dynamics"],
            [
                {
                    "summary": "does the trim hold for a minute",
                    "arguments": {"aircraft_id": "demo", "seconds": 60},
                }
            ],
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
