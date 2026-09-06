"""The `fu_*` tools (A69 P3): what a batch is the wrong shape for.

Modelling IS `tee_batch` - sketch, extrude, fillet, component, parameters,
imports are wire ops on the `FusionAdapter`, so the loop arrives through the
surface TEE already has and the always-loaded surface stays 17 tools. What
is left over: health, measurements, the parameter and history tables, the
exporters, and the escape hatch. Every one is tabled individually in
`kernel/trust.py` (no `fu_` family row: one writer and one `exec-code` among
six). The escape hatch registers only when the operator allowed code
execution, exactly as `bl_execute_python` does, and the trust kernel still
decides it per call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.wire import START_FIX
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

# What each export declares about its units (doc 71 rows 17, 30 and 48): STEP
# and the archive carry their own; OBJ defaults to centimetres; STL takes the
# design's default units, which this lane cannot know without reading them
# back - so it declares nothing rather than guessing. IGES, SAT, 3MF and USD
# declare a unit inside the file and their option objects carry none, so the
# lane answers `units: null, declares_units: true` until the smoke has read
# what Fusion writes (doc 71 section 9, item 6).
_EXPORT_UNITS: dict[str, str | None] = {
    "step": "mm",
    "f3d": "mm",
    "obj": "cm",
    "stl": None,
    "iges": None,
    "sat": None,
    "usd": None,
    "3mf": None,
}
_EXPORT_NOTES = {
    "obj": "OBJ is written in Fusion's default of centimetres (unitType unset)",
    "stl": "STL takes the design's default units; read them back before trusting a scale",
    "iges": "IGES declares its unit in its global section; read it before scaling",
    "sat": "SAT declares its unit inside the file; read it before scaling",
    "usd": "USD carries metersPerUnit; read it before scaling",
    "3mf": "3MF names its unit on the model element (millimetre by default); read it",
}
_DRAWING_KEYS = (
    "sheet",
    "standard",
    "angle",
    "scale",
    "views",
    "dims",
    "hole_table",
    "parts_list",
    "title",
    "formats",
)


def register_fusion_tools(app: Any, adapter: FusionAdapter) -> None:
    lane = next((name for name, a in app.adapters.items() if a is adapter), "fusion")

    def probe(args: dict[str, Any]) -> dict[str, Any]:
        """Never spawns anything: the add-in is Fusion's to run."""
        info = adapter.info().to_payload()
        if not info.get("connected"):
            raise TeeError(
                "fusion_unreachable",
                f"The TEE bridge add-in is not answering on 127.0.0.1:{adapter.wire.port}.",
                fix=START_FIX,
            )
        out: dict[str, Any] = {
            "connected": True,
            "lane": lane,
            "port": adapter.wire.port,
            "version": info.get("version"),
            "units": "mm on the wire, cm inside Fusion; every expression carries its unit",
        }
        try:
            out.update(adapter.run(codegen.PROBE_PROGRAM))
        except TeeError as exc:
            if exc.code != "fusion_no_design":
                raise
            out.update({"document": None, "design": None, "note": exc.fix})
        return out

    def export(args: dict[str, Any]) -> dict[str, Any]:
        fmt = str(args.get("format") or "step").lower()
        if fmt not in codegen.EXPORT_FORMATS:
            raise TeeError(
                "bad_op",
                f"Unknown export format '{fmt}'.",
                fix=f"Formats: {', '.join(codegen.EXPORT_FORMATS)}.",
            )
        out = args.get("out")
        if not out:
            raise TeeError("bad_op", "fu_export needs out: a path.", fix='out="parts/bracket.step"')
        of = args.get("of")
        if fmt in codegen.COMPONENT_ONLY_EXPORTS and of and str(of).startswith("b"):
            raise TeeError(
                "bad_op",
                f"{fmt} exports a component or the whole design, not a body (doc 71 row 48).",
                fix="Pass a component id (c1) or omit of; 3mf, stl and obj take a body.",
            )
        path = str(Path(str(out)).expanduser())
        suffix = codegen.EXPORT_FORMATS[fmt][2]
        if not path.lower().endswith("." + suffix):
            path += "." + suffix
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        result = adapter.run(codegen.export_program(fmt, path, str(of) if of else None))
        units = _EXPORT_UNITS[fmt]
        result["units"] = units
        result["declares_units"] = fmt not in ("stl", "obj")
        if fmt in _EXPORT_NOTES:
            result["note"] = _EXPORT_NOTES[fmt]
        into = args.get("into")
        if into:
            from tee.kernel.handoff_import import land

            result["landed"] = land(
                app,
                files={Path(path).stem: path},
                into=str(into),
                units=units,
                caller="fu_export",
            )
        return result

    def drawing(args: dict[str, Any]) -> dict[str, Any]:
        """The Fusion API cannot create a drawing (doc 71 row 49): STEP out of
        Fusion, into the served partkiln lane, then its `pk_drawing` - every
        dimension read from the model (partkiln's Law 15). The import into
        partkiln's document is a scene write on that lane and is decided as
        one before anything is written (the A68 `land()` precedent)."""
        if not any(type(a).__name__ == "PartkilnAdapter" for a in app.adapters.values()):
            raise TeeError(
                "partkiln_not_served",
                "fu_drawing draws through partkiln, and no partkiln lane is served.",
                fix="tee serve --adapter fusion --adapter partkiln; the Fusion API itself "
                "cannot create a drawing (doc 71 row 49).",
            )
        out = args.get("out")
        if not out:
            raise TeeError("bad_op", "fu_drawing needs out: a directory.", fix='out="sheets"')
        name = str(args.get("name") or "sheet")
        app.registry.require("write-scene", name="fu_drawing")
        step = str(Path(adapter.workdir) / "drawings" / f"{name}.step")
        Path(step).parent.mkdir(parents=True, exist_ok=True)
        of = args.get("of")
        exported = adapter.run(codegen.export_program("step", step, str(of) if of else None))
        imported = app.registry.call("pk_import", {"path": step, "name": name})
        part = str(imported.get("id") or f"part:{name}")
        passthrough = {k: args[k] for k in _DRAWING_KEYS if k in args}
        drawn = app.registry.call(
            "pk_drawing", {"of": part, "out": str(out), "name": name, **passthrough}
        )
        return {
            "step": step,
            "bytes": exported.get("bytes"),
            "part": part,
            "imported": imported,
            "drawing": drawn,
            "note": "dimensions are read from the STEP by partkiln (its Law 15); the Fusion API "
            "cannot create a drawing (doc 71 row 49)",
        }

    def measure(args: dict[str, Any]) -> dict[str, Any]:
        of = args.get("of")
        return adapter.run(codegen.measure_program(str(of) if of else None))

    def params(args: dict[str, Any]) -> dict[str, Any]:
        return adapter.run(codegen.PARAMS_PROGRAM)

    def timeline(args: dict[str, Any]) -> dict[str, Any]:
        return adapter.run(codegen.TIMELINE_PROGRAM)

    def execute_python(args: dict[str, Any]) -> dict[str, Any]:
        code = args.get("code")
        if not isinstance(code, str) or not code.strip():
            raise TeeError("bad_op", "fu_execute_python needs code.", fix='code="result = {...}"')
        result = adapter.wire.execute(
            code, strict_json=False, timeout=float(args.get("timeout") or 60.0)
        )
        return {"ok": True, "result": result}

    tools = [
        VirtualTool(
            name="fu_probe",
            description=(
                "Fusion bridge health: add-in reachable, Fusion version, the active document "
                "and design type (parametric or direct), entity counts, the id map. Never "
                "starts anything - the add-in is Fusion's to run."
            ),
            schema={"type": "object", "properties": {}},
            handler=probe,
            tags=["fusion", "autodesk", "probe", "health", "bridge", "version", "document", "cad"],
            examples=[{}],
        ),
        VirtualTool(
            name="fu_export",
            description=(
                "Export the design, a body or a component from Fusion: step, stl, obj, f3d "
                "(the Fusion archive), iges, sat, 3mf or usd. into=<lane|auto> lands the "
                "file in a served scene lane as one checkpointed batch with a read-back "
                "verdict. STEP, f3d, iges, sat, 3mf and usd carry their units inside; OBJ is "
                "centimetres; STL takes the design's default units. iges/sat/usd export a "
                "component or the whole design, not a body."
            ),
            schema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "step|stl|obj|f3d|iges|sat|3mf|usd (default step)",
                    },
                    "out": {"type": "string", "description": "output path"},
                    "of": {"type": "string", "description": "body or component id; omit = root"},
                    "into": {
                        "type": "string",
                        "description": "land the file in this lane (or auto)",
                    },
                },
                "required": ["out"],
            },
            handler=export,
            tags=[
                "fusion",
                "autodesk",
                "export",
                "step",
                "stl",
                "obj",
                "f3d",
                "iges",
                "sat",
                "3mf",
                "usd",
                "archive",
                "handoff",
                "land",
                "interchange",
                "cad",
            ],
            examples=[
                {"format": "step", "out": "parts/bracket.step"},
                {"format": "obj", "out": "parts/bracket.obj", "of": "b1", "into": "auto"},
            ],
        ),
        VirtualTool(
            name="fu_drawing",
            description=(
                "A dimensioned sheet of the Fusion design, a body or a component, through "
                "partkiln: STEP out of Fusion, into the served partkiln lane, then pk_drawing "
                "- views, dimensions read from the model, hole table, parts list, SVG/DXF/PDF. "
                "The Fusion API cannot create a drawing (doc 71 row 49); this is the route "
                "that can. Needs a partkiln lane served."
            ),
            schema={
                "type": "object",
                "properties": {
                    "out": {"type": "string", "description": "output directory"},
                    "of": {"type": "string", "description": "body or component id; omit = design"},
                    "name": {"type": "string", "description": "sheet and part name"},
                    "sheet": {"type": "string", "description": "A4L..A0L|ANSI_B"},
                    "standard": {"type": "string", "description": "ISO|ANSI|DIN"},
                    "angle": {"type": "string", "description": "first|third"},
                    "scale": {"type": "string", "description": "e.g. 1:2"},
                    "views": {"type": "array", "description": "[{name, dir}] front|top|right|iso"},
                    "dims": {"type": "array", "description": "[{name, view, kind, of|a, b}]"},
                    "hole_table": {"type": "boolean"},
                    "formats": {"type": "array", "description": "svg|dxf|pdf (default svg)"},
                },
                "required": ["out"],
            },
            handler=drawing,
            tags=[
                "fusion",
                "autodesk",
                "drawing",
                "drawings",
                "sheet",
                "views",
                "dimensioned",
                "blueprint",
                "partkiln",
                "svg",
                "dxf",
                "pdf",
                "cad",
            ],
            examples=[
                {"out": "sheets", "name": "bracket", "views": [{"name": "top", "dir": "top"}]}
            ],
        ),
        VirtualTool(
            name="fu_measure",
            description=(
                "Volume mm3, area mm2, mass kg, centre of mass and bounding box in mm of a "
                "body, a component or the whole design - Fusion's own physical properties, "
                "converted once at the boundary."
            ),
            schema={
                "type": "object",
                "properties": {
                    "of": {"type": "string", "description": "body or component id; omit = root"}
                },
            },
            handler=measure,
            tags=[
                "fusion",
                "autodesk",
                "measure",
                "mass",
                "volume",
                "area",
                "bbox",
                "bounding",
                "dimensions",
                "physical",
                "cad",
            ],
            examples=[{"of": "b1"}],
        ),
        VirtualTool(
            name="fu_params",
            description=(
                "Every parameter of the design - user and model - with name, expression, unit "
                "and value (mm, deg or unitless). Set one with a tee_batch param_set op."
            ),
            schema={"type": "object", "properties": {}},
            handler=params,
            tags=[
                "fusion",
                "autodesk",
                "parameters",
                "parameter",
                "expression",
                "dimension",
                "cad",
            ],
            examples=[{}],
        ),
        VirtualTool(
            name="fu_timeline",
            description=(
                "The design's history as Fusion holds it: every timeline item with its type, "
                "suppressed and rolled-back flags and health message, plus the marker - what "
                "a checkpoint rolls back to."
            ),
            schema={"type": "object", "properties": {}},
            handler=timeline,
            tags=["fusion", "autodesk", "timeline", "history", "features", "marker", "cad"],
            examples=[{}],
        ),
    ]
    if app.allow_code_exec:
        tools.append(
            VirtualTool(
                name="fu_execute_python",
                description=(
                    "Run arbitrary Python against the Fusion API on Fusion's primary thread; "
                    "assign a dict to `result`. The escape hatch for the long tail the typed "
                    "ops do not cover - exec-code, denied unless granted."
                ),
                schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python; set result = {...}"},
                        "timeout": {"type": "number", "description": "seconds (default 60)"},
                    },
                    "required": ["code"],
                },
                handler=execute_python,
                tags=["fusion", "autodesk", "python", "execute", "script", "api", "escape", "cad"],
                examples=[{"code": "result = {'bodies': _root.bRepBodies.count}"}],
            )
        )
    for tool in tools:
        app.registry.register(tool)
