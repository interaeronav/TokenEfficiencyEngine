"""Fabrication virtual tools (A37 P4): fc_drawing + fc_export.

fc_drawing derives a dimensioned TechDraw page FROM the model and reads
every dimension's value back FROM THE DOCUMENT - the research-52 fix for
"blueprints as pixels": numbers on the sheet are the model's numbers by
construction, asserted from data, never from a picture. SVG/PDF render
via TechDrawGui THROUGH the one bridge (the P0 probe: page SVG/PDF is
GUI-bound, #5710); DXF works anywhere.

fc_export writes fabricator/engine files (STEP, glTF/GLB, page DXF).
Long-tail tools: zero always-loaded cost.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.adapters.freecad.adapter import FreeCADAdapter
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

_VIEW_DIRECTIONS = {
    "front": "(0, -1, 0)",
    "back": "(0, 1, 0)",
    "top": "(0, 0, 1)",
    "bottom": "(0, 0, -1)",
    "left": "(-1, 0, 0)",
    "right": "(1, 0, 0)",
    "iso": "(1, -1, 1)",
}

_DRAWING_CODE = """\
import FreeCAD, TechDraw, json, os
doc = FreeCAD.getDocument({doc!r})
page = doc.addObject('TechDraw::DrawPage', {page_name!r})
template = doc.addObject('TechDraw::DrawSVGTemplate', {page_name!r} + '_tpl')
template.Template = os.path.join(FreeCAD.getResourceDir(), 'Mod', 'TechDraw',
                                 'Templates', 'Default_Template_A4_Landscape.svg')
page.Template = template
sources = [doc.getObject(n) for n in {objects!r}]
missing = [n for n, o in zip({objects!r}, sources) if o is None]
if missing:
    print(json.dumps({{"error": "no objects: %s" % ", ".join(missing)}}))
else:
    views = []
    for spec in {views!r}:
        v = doc.addObject('TechDraw::DrawViewPart', 'View_' + spec['dir'])
        page.addView(v)
        v.Source = sources
        v.Direction = FreeCAD.Vector(*spec['vec'])
        v.ScaleType = 'Custom'; v.Scale = spec.get('scale', 1.0)
        if 'at' in spec: v.X, v.Y = spec['at'][0], spec['at'][1]
        views.append(v)
    doc.recompute()
    dims = []
    for d in {dimensions!r}:
        view = views[int(d.get('view', 0))]
        if d['type'] in ('ExtentX', 'ExtentY'):
            # overall extent of the whole view - no edge guessing
            dim = TechDraw.makeExtentDim(view, [], 0 if d['type'] == 'ExtentX' else 1)
        else:
            dim = doc.addObject('TechDraw::DrawViewDimension', 'Dim%d' % len(dims))
            dim.Type = d['type']
            dim.References2D = [(view, r) for r in d['refs']]
            page.addView(dim)
        dims.append(dim)
    doc.recompute()
    out = {{"page": page.Name,
            "views": [v.Name for v in views],
            "dims": [d.Name for d in dims]}}
    print(json.dumps(out))
"""

# A dimension created in the same dispatch as its view binds before the
# view's projection exists and CACHES 0.0 (verified live on 1.1.3:
# dispatch1 = 0.0, plain dispatch2 = 0.0, dispatch2 after touch+recompute
# = the true value). The read-back is therefore a second call that
# touches the dims first.
_READBACK_CODE = """\
import FreeCAD, json
doc = FreeCAD.getDocument({doc!r})
dims = [doc.getObject(n) for n in {dims!r}]
for d in dims:
    d.touch()
doc.recompute()
out = []
for d in dims:
    out.append({{"name": d.Name,
                 "type": str(getattr(d, 'Type', d.TypeId.split('::')[-1])),
                 "value_mm": round(float(d.getRawValue()), 3)}})
print(json.dumps(out))
"""


def register_freecad_tools(app, adapter: FreeCADAdapter) -> None:
    def fc_drawing(args: dict[str, Any]) -> dict[str, Any]:
        adapter._ensure_doc()
        objects = [str(o) for o in (args.get("objects") or [])]
        if not objects:
            raise TeeError(
                "bad_op", "fc_drawing needs objects.", fix='Give {"objects": ["<id>", ...]}.'
            )
        view_names = [str(v) for v in (args.get("views") or ["front", "top"])]
        bad = [v for v in view_names if v not in _VIEW_DIRECTIONS]
        if bad:
            raise TeeError(
                "bad_op",
                f"Unknown view(s): {', '.join(bad)}.",
                fix=f"Views: {', '.join(_VIEW_DIRECTIONS)}.",
            )
        spacing = 90
        views = [
            {
                "dir": name,
                "vec": _direction(name),
                "scale": float(args.get("scale") or 1.0),
                "at": [40 + i * spacing, 140],
            }
            for i, name in enumerate(view_names)
        ]
        dimensions = [
            {
                "view": int(d.get("view", 0)),
                "type": str(d.get("type", "DistanceX")),
                "refs": [str(r) for r in (d.get("refs") or ["Edge0"])],
            }
            for d in (args.get("dimensions") or [])
        ]
        name = str(args.get("name") or "Sheet")
        result = adapter.wire.py_json(
            _DRAWING_CODE.format(
                doc=adapter.doc,
                page_name=name,
                objects=objects,
                views=views,
                dimensions=dimensions,
            )
        )
        if "error" in result:
            raise TeeError(
                "freecad_op_failed",
                f"fc_drawing: {result['error']}",
                fix="tee_scene_summary lists current ids.",
            )
        dim_rows = (
            adapter.wire.py_json(_READBACK_CODE.format(doc=adapter.doc, dims=result["dims"]))
            if result.get("dims")
            else []
        )
        out_dir = Path(str(args.get("out_dir") or adapter._spill()))
        out_dir.mkdir(parents=True, exist_ok=True)
        exports: dict[str, str] = {}
        for fmt in [str(f) for f in (args.get("formats") or ["svg"])]:
            exports[fmt] = _export_page(adapter, str(result["page"]), fmt, out_dir / name)
        return {
            "page": result["page"],
            "views": result["views"],
            "dimensions": dim_rows,
            "files": exports,
            "note": "dimension values are read from the document - the sheet "
            "carries the model's numbers by construction",
        }

    def fc_export(args: dict[str, Any]) -> dict[str, Any]:
        adapter._ensure_doc()
        objects = [str(o) for o in (args.get("objects") or [])]
        fmt = str(args.get("format") or "step").lower()
        path = args.get("path")
        if not objects or not path:
            raise TeeError(
                "bad_op",
                "fc_export needs objects and path.",
                fix='{"objects": ["<id>"], "format": "step|glb", "path": "/out/part.step"}',
            )
        if fmt not in ("step", "glb", "gltf"):
            raise TeeError("bad_op", f"Unknown format '{fmt}'.", fix="Formats: step, glb, gltf.")
        target = str(Path(path))
        code = (
            "import FreeCAD, json\n"
            f"doc = FreeCAD.getDocument({adapter.doc!r})\n"
            f"objs = [doc.getObject(n) for n in {objects!r}]\n"
            f"missing = [n for n, o in zip({objects!r}, objs) if o is None]\n"
            "if missing:\n"
            "    print(json.dumps({'error': 'no objects: %s' % ', '.join(missing)}))\n"
            "else:\n"
        )
        if fmt == "step":
            code += f"    import Part\n    Part.export(objs, {target!r})\n"
        else:
            code += f"    import ImportGui\n    ImportGui.export(objs, {target!r})\n"
        code += (
            "    import os\n"
            f"    print(json.dumps({{'path': {target!r}, "
            f"'bytes': os.path.getsize({target!r})}}))\n"
        )
        result = adapter.wire.py_json(code)
        if "error" in result:
            raise TeeError(
                "freecad_op_failed",
                f"fc_export: {result['error']}",
                fix="tee_scene_summary lists current ids.",
            )
        out = {"ok": True, **result, "format": fmt}
        into = args.get("into")
        if into:
            # A68 P3: land the file in a served scene lane as one checkpointed
            # batch. FreeCAD's document is millimetres; a GLB declares its own.
            from tee.kernel.handoff_import import land

            out["landed"] = land(
                app,
                files={Path(target).stem: target},
                into=str(into),
                units="mm",
                caller="fc_export",
            )
        return out

    for tool in [
        VirtualTool(
            "fc_drawing",
            "Derive a dimensioned TechDraw sheet FROM the FreeCAD model: "
            "projection views (front/top/iso...), dimensions per view - "
            "ExtentX/ExtentY (overall size, no edge refs needed) or "
            "Distance/DistanceX/DistanceY with 2D edge refs - and the "
            "title-block template; exports svg/pdf (via the GUI bridge - "
            "headless page export is #5710) and dxf. Every dimension VALUE "
            "is read back from the document, so the sheet's numbers are the "
            "model's numbers by construction.",
            {
                "type": "object",
                "properties": {
                    "objects": {"type": "array", "items": {"type": "string"}},
                    "views": {"type": "array", "items": {"type": "string"}},
                    "dimensions": {"type": "array", "items": {"type": "object"}},
                    "formats": {"type": "array", "items": {"type": "string"}},
                    "name": {"type": "string"},
                    "scale": {"type": "number"},
                    "out_dir": {"type": "string"},
                },
                "required": ["objects"],
            },
            fc_drawing,
            tags=["freecad", "drawing", "techdraw", "sheet", "dimension", "fabrication"],
            examples=[
                {
                    "objects": ["slab"],
                    "views": ["front", "top"],
                    "dimensions": [{"view": 0, "type": "DistanceX", "refs": ["Edge0"]}],
                    "formats": ["svg", "pdf"],
                }
            ],
        ),
        VirtualTool(
            "fc_export",
            "Export FreeCAD solids for fabricators and engines: STEP "
            "(geometry, opens everywhere) or glTF/GLB. into=<lane|auto> lands a "
            "GLB in a served scene lane as one checkpointed batch with read-back; "
            "as_ingest + as_import remain the asset-library route.",
            {
                "type": "object",
                "properties": {
                    "objects": {"type": "array", "items": {"type": "string"}},
                    "format": {"type": "string"},
                    "path": {"type": "string"},
                    "into": {
                        "type": "string",
                        "description": "land the file in this served lane (or auto); glb only",
                    },
                },
                "required": ["objects", "path"],
            },
            fc_export,
            tags=["freecad", "export", "step", "gltf", "glb", "land", "handoff", "fabrication"],
        ),
    ]:
        app.registry.register(tool)


def _direction(name: str) -> list[float]:
    text = _VIEW_DIRECTIONS[name].strip("()")
    return [float(p) for p in text.split(",")]


def _export_page(adapter: FreeCADAdapter, page: str, fmt: str, base: Path) -> str:
    path = str(base) + "." + fmt
    if fmt == "dxf":
        code = (
            "import FreeCAD, TechDraw, json\n"
            f"doc = FreeCAD.getDocument({adapter.doc!r})\n"
            f"TechDraw.writeDXFPage(doc.getObject({page!r}), {path!r})\n"
            f"import os; print(json.dumps({{'ok': os.path.getsize({path!r}) > 0}}))"
        )
    elif fmt in ("svg", "pdf"):
        exporter = "exportPageAsSvg" if fmt == "svg" else "exportPageAsPdf"
        code = (
            "import FreeCAD, TechDrawGui, json\n"
            f"doc = FreeCAD.getDocument({adapter.doc!r})\n"
            f"TechDrawGui.{exporter}(doc.getObject({page!r}), {path!r})\n"
            f"import os; print(json.dumps({{'ok': os.path.getsize({path!r}) > 0}}))"
        )
    else:
        raise TeeError("bad_op", f"Unknown page format '{fmt}'.", fix="Formats: svg, pdf, dxf.")
    adapter.wire.py_json(code)
    return path
