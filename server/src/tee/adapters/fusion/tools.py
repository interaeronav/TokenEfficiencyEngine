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
from tee.adapters.fusion.docs import FusionDocs
from tee.adapters.fusion.wire import START_FIX
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

# What each export declares about its units - measured on Fusion 2704.1.53
# (A71, 2026-09-06, docs/research/71-fusion-live-facts.json): STEP and the
# archive carry their own; OBJ is written in centimetres (a 120 mm plate spans
# 12 units); STL carries no unit and follows the design's default length unit,
# which the export program reads from the design (UnitsManager.defaultLengthUnits,
# row 53) rather than guessing; IGES declares MM in its global section, SAT one
# millimetre per unit in its header, 3MF unit="millimeter" on the model element;
# USD is a USDZ package whose binary usdc declares metersPerUnit - a value the
# lane cannot read without the USD library, so it stays declared and unread.
_EXPORT_UNITS: dict[str, str | None] = {
    "step": "mm",
    "f3d": "mm",
    "obj": "cm",
    "stl": None,  # the design's unit, read at export time
    "iges": "mm",
    "sat": "mm",
    "usd": None,
    "3mf": "mm",
}
_EXPORT_NOTES = {
    "obj": "OBJ is written in Fusion's centimetres (measured: a 120 mm plate spans 12 units)",
    "stl": "STL carries no unit; `units` is the design's default length unit, read from the "
    "design at export time",
    "iges": "IGES global section declares MM (measured: unit flag 2, name MM)",
    "sat": "SAT header declares 1 mm per unit (measured: line 3 begins '1 ')",
    "usd": "Fusion writes a USDZ package (the path reported ends in .usdz): one binary usdc "
    "declaring metersPerUnit and upAxis Z; read the value with the USD library before scaling",
    "3mf": '3MF model element declares unit="millimeter" (measured)',
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


def register_fusion_tools(app: Any, adapter: FusionAdapter, docs_cache_dir=None) -> None:
    lane = next((name for name, a in app.adapters.items() if a is adapter), "fusion")
    docs = FusionDocs(adapter, cache_dir=docs_cache_dir)

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
                f"{fmt} exports a component or the whole design, never a body (doc 71 rows 17 "
                "and 48; Fusion itself answers '3 : invlid argument geometry').",
                fix="Pass a component id (c1) or omit of; 3mf, stl and obj take a body.",
            )
        path = str(Path(str(out)).expanduser())
        suffix = codegen.EXPORT_FORMATS[fmt][2]
        if not path.lower().endswith("." + suffix):
            path += "." + suffix
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        result = adapter.run(codegen.export_program(fmt, path, str(of) if of else None))
        design_unit = result.pop("design_unit", None)
        units = _EXPORT_UNITS[fmt]
        if fmt == "stl":  # measured from the design, never declared by the file
            units = design_unit
        result["units"] = units
        result["declares_units"] = fmt not in ("stl", "obj")
        path = str(result.get("path") or path)  # USD: Fusion appended .usdz
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

    def design_stats(args: dict[str, Any]) -> dict[str, Any]:
        return adapter.run(codegen.STATS_PROGRAM)

    def search_docs(args: dict[str, Any]) -> dict[str, Any]:
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            raise TeeError(
                "bad_op",
                "fu_search_docs needs a query.",
                fix='query="extrude profile distance"',
            )
        return docs.search(query, limit=int(args.get("limit") or 10))

    def api_detail(args: dict[str, Any]) -> dict[str, Any]:
        path = args.get("path")
        if not isinstance(path, str) or not path.strip():
            raise TeeError(
                "bad_op",
                "fu_api_detail needs a path.",
                fix='path="adsk.fusion.ExtrudeFeatures.addSimple"',
            )
        return docs.detail(path.strip())

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
        VirtualTool(
            name="fu_design_stats",
            description=(
                "One health read of the whole design: body count, total volume and mass, the "
                "overall bounding box in mm, bodies still called Body1, non-solid bodies, "
                "overlapping body pairs, feature and suppressed counts, and every timeline "
                "item Fusion marks warning or error. Text evidence before any pixel."
            ),
            schema={"type": "object", "properties": {}},
            handler=design_stats,
            tags=[
                "fusion",
                "autodesk",
                "stats",
                "health",
                "overlap",
                "problems",
                "audit",
                "check",
                "design",
                "cad",
            ],
            examples=[{}],
        ),
        VirtualTool(
            name="fu_search_docs",
            description=(
                "Search the Fusion API of the Fusion you are connected to - introspected "
                "live from adsk.core and adsk.fusion, cached per version - and get back "
                "paths, one-line docs and signatures. The cure for a hallucinated call: the "
                "API drifts between builds, so ask this build rather than remembering."
            ),
            schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "keywords, e.g. 'extrude extent'"},
                    "limit": {"type": "integer", "description": "1-25, default 10"},
                },
                "required": ["query"],
            },
            handler=search_docs,
            tags=[
                "fusion",
                "autodesk",
                "docs",
                "api",
                "search",
                "reference",
                "signature",
                "adsk",
                "cad",
            ],
            examples=[{"query": "extrude distance extent"}, {"query": "sketch circle", "limit": 5}],
        ),
        VirtualTool(
            name="fu_api_detail",
            description=(
                "One Fusion API symbol in full from the live build: its docstring, its "
                "signature and, for a class, its members. Follows a fu_search_docs hit."
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "adsk.fusion.ExtrudeFeatures.add"}
                },
                "required": ["path"],
            },
            handler=api_detail,
            tags=["fusion", "autodesk", "api", "detail", "signature", "docstring", "adsk", "cad"],
            examples=[{"path": "adsk.fusion.ExtrudeFeatures.addSimple"}],
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
