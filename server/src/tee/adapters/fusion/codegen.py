"""Batch-op codegen for the Fusion adapter (A69).

One tee_batch compiles to ONE Python script executed in ONE bridge round
trip on Fusion's primary thread (batch over chatter, applied at the wire).
The script applies ops in order and hands back one JSON-shaped `result`:
the diff, or `{"error": {op_index, code, message}}` from the first failing
op - nothing after it ran, and the kernel's checkpoint restores.

Every adsk call emitted here is a row in docs/research/71-fusion-lane.md
section 3 (Law 1 of that document): a call that is not in the table does
not go in this file. The two facts that shape the arithmetic:

- Fusion's internal units are centimetres and radians, and a unitless
  expression takes the DOCUMENT's active unit, which this lane cannot know.
  So every length leaves here as ``ValueInput.createByString("<n> mm")``,
  sketch points are divided by ten into cm, and every read-back multiplies
  once at the boundary (cm -> mm, cm² -> mm², cm³ -> mm³; kg stays kg).
- ``ExtrudeFeatureInput.setDistanceExtent`` is retired (September 2022);
  the extent is ``setOneSideExtent(DistanceExtentDefinition.create(v),
  ExtentDirections.PositiveExtentDirection)``.

Ids: Fusion's stable identity is the entityToken - long and opaque - so the
bridge's persistent ``_tee`` dict mints short prefixed ids on first sight
(``sk1``, ``f1``, ``b1``, ``c1``; user parameters are ``param:<name>``) and
keeps the map both ways. A listing prunes ids whose token no longer resolves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

OPS = ("create", "set", "delete", "param_set", "import_file")
KINDS = ("sketch", "extrude", "fillet", "component", "param")
IMPORT_SUFFIXES = ("step", "stp", "f3d", "igs", "iges", "sat")
# Row 17: the option constructors differ in argument order by format. Only
# the four whose pages were read ship; iges/sat/3mf/usd exist and wait for
# their rows.
EXPORT_FORMATS: dict[str, tuple[str, str, str]] = {
    "step": ("createSTEPExportOptions", "filename_first", "step"),
    "f3d": ("createFusionArchiveExportOptions", "filename_first", "f3d"),
    "stl": ("createSTLExportOptions", "geometry_first", "stl"),
    "obj": ("createOBJExportOptions", "geometry_first", "obj"),
}
OPERATIONS = {
    "join": "JoinFeatureOperation",
    "cut": "CutFeatureOperation",
    "intersect": "IntersectFeatureOperation",
    "new_body": "NewBodyFeatureOperation",
    "new_component": "NewComponentFeatureOperation",
}
PLANES = {"XY": "xYConstructionPlane", "XZ": "xZConstructionPlane", "YZ": "yZConstructionPlane"}
_IMPORT_OPTIONS = {
    "step": "createSTEPImportOptions",
    "stp": "createSTEPImportOptions",
    "f3d": "createFusionArchiveImportOptions",
    "igs": "createIGESImportOptions",
    "iges": "createIGESImportOptions",
    "sat": "createSATImportOptions",
}

# -- the shared prelude: the design, the id map, the unit boundary -------------

_PRELUDE = """\
import json
import adsk.core, adsk.fusion
class _OpError(Exception):
    def __init__(self, index, message, code="fusion_op_failed"):
        super().__init__(message); self.index = index; self.code = code
try:
    _app = adsk.core.Application.get()
    _design = adsk.fusion.Design.cast(_app.activeProduct)
    if _design is None:
        raise _OpError(-1, "no active Fusion design (open or create one: File > New Design)",
                       "fusion_no_design")
    _root = _design.rootComponent
    _ids = _tee.setdefault("ids", {}); _toks = _tee.setdefault("toks", {})
    _counts = _tee.setdefault("counts", {}); _kinds = _tee.setdefault("kinds", {})
    def _mint(prefix, token):
        sid = _toks.get(token)
        if sid is None:
            n = _counts.get(prefix, 0) + 1; _counts[prefix] = n
            sid = "%s%d" % (prefix, n); _ids[sid] = token; _toks[token] = sid
        return sid
    def _forget(sid):
        token = _ids.pop(sid, None); _toks.pop(token, None); _kinds.pop(sid, None)
    def _find(sid, index=-1):
        if sid.startswith("param:"):
            p = _design.userParameters.itemByName(sid[6:])
            if p is None:
                raise _OpError(index, "no user parameter %r" % sid[6:], "fusion_unknown_entity")
            return p
        token = _ids.get(sid)
        ents = _design.findEntityByToken(token) if token else []
        if not ents:
            raise _OpError(index, "no entity %r (tee_scene_summary refresh=true lists ids)" % sid,
                           "fusion_unknown_entity")
        return ents[0]
    def _mm(v): return round(float(v) * 10.0, 4)
    def _pt(p): return [_mm(p.x), _mm(p.y), _mm(p.z)]
    def _bbox_mm(bb):
        lo, hi = bb.minPoint, bb.maxPoint
        return [round(_mm(hi.x - lo.x), 4), round(_mm(hi.y - lo.y), 4), round(_mm(hi.z - lo.z), 4)]
    def _kind_of(ent):
        t = ent.objectType.split("::")[-1]
        if t.endswith("Feature"): return "feature"
        return {"BRepBody": "body", "Sketch": "sketch", "Occurrence": "component",
                "UserParameter": "param", "ModelParameter": "param"}.get(t, t.lower())
    _PREFIX = {"body": "b", "sketch": "sk", "component": "c", "feature": "f"}
    def _prefix_for(kind): return _PREFIX.get(kind, "e")
    def _param_value(p):
        u = str(p.unit)
        if u in ("mm", "cm", "m", "in", "ft"): return _mm(p.value)
        if u in ("deg", "rad"): return round(float(p.value) * 57.29577951308232, 4)
        return p.value
    def _summary(kind, ent):
        s = {}
        if kind == "body":
            s["volume_mm3"] = round(float(ent.volume) * 1000.0, 3)
            s["bbox_mm"] = _bbox_mm(ent.boundingBox)
            s["faces"] = ent.faces.count; s["edges"] = ent.edges.count
            s["solid"] = bool(ent.isSolid)
        elif kind == "sketch":
            s["profiles"] = ent.profiles.count; s["curves"] = ent.sketchCurves.count
        elif kind == "feature":
            s["type"] = ent.objectType.split("::")[-1]; s["bodies"] = ent.bodies.count
            if ent.isSuppressed: s["suppressed"] = True
            msg = ent.errorOrWarningMessage
            if msg: s["health"] = str(msg)[:120]
            try: s["distance_mm"] = _mm(ent.extentOne.distance.value)
            except Exception: pass
        elif kind == "component":
            s["bodies"] = ent.component.bRepBodies.count
            s["sketches"] = ent.component.sketches.count
        elif kind == "param":
            s["expression"] = str(ent.expression); s["unit"] = str(ent.unit)
            s["value"] = _param_value(ent)
        return s
    def _name_of(kind, ent):
        return str(ent.component.name) if kind == "component" else str(ent.name)
    def _sid_of(kind, ent):
        if kind == "param": return "param:" + str(ent.name)
        return _mint(_prefix_for(kind), ent.entityToken)
"""

_BATCH_HEAD = """\
    created, modified, deleted, details = [], [], [], {}
    def _note(sid, kind, ent, parent=None):
        row = {"name": _name_of(kind, ent), "kind": _kinds.get(sid, kind)}
        if parent: row["parent"] = parent
        row.update(_summary(kind, ent)); details[sid] = row
    def _mark(sid, new):
        if new:
            if sid not in created: created.append(sid)
        elif sid not in created and sid not in modified:
            modified.append(sid)
    def _mark_bodies(feature):
        for _i in range(feature.bodies.count):
            _b = feature.bodies.item(_i); _new = _b.entityToken not in _toks
            _bid = _mint("b", _b.entityToken); _mark(_bid, _new); _note(_bid, "body", _b)
"""

_BATCH_TAIL = """\
    result = {"created": created, "modified": modified, "deleted": deleted, "details": details}
"""

_EPILOGUE = """\
except _OpError as exc:
    result = {"error": {"op_index": exc.index, "code": exc.code, "message": str(exc)[:300]}}
except Exception as exc:
    result = {"error": {"op_index": -1, "code": "fusion_op_failed",
                        "message": (type(exc).__name__ + ": " + str(exc))[:300]}}
"""


def _lit(value: Any) -> str:
    return repr(value)


def _mm_expr(value: float) -> str:
    """A length the way Fusion must receive it: a string carrying the unit."""
    return f"{float(value):g} mm"


def _cm(value: float) -> float:
    return round(float(value) / 10.0, 6)


# -- server-side validation: refuse before the wire, naming the fix -------------


def _bad(index: int, message: str, fix: str) -> TeeError:
    return TeeError("bad_op", f"{message} (batch index {index}).", fix=fix)


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_batch(ops: list[dict[str, Any]]) -> None:
    """Every refusal a script would have produced for a malformed op, raised
    here instead - no wire trip, no traceback (the Blender precedent)."""
    for index, op in enumerate(ops):
        action = str(op.get("op") or "")
        if action not in OPS:
            raise TeeError(
                "bad_op",
                f"Unknown op '{action}' at batch index {index}.",
                fix=f"Fusion accepts: {', '.join(OPS)}.",
            )
        props = op.get("props") or {}
        if not isinstance(props, dict):
            raise _bad(index, "props must be an object", "{op, kind, name, props: {...}}")
        if action == "create":
            kind = str(op.get("kind") or "")
            if not kind or not kind.replace("_", "").isalnum():
                raise TeeError(
                    "bad_kind",
                    f"A create needs a kind at batch index {index}.",
                    fix=f"Kinds: {', '.join(KINDS)}, or a plain word for a named component.",
                )
            _check_create(index, kind, props)
        elif action in ("set", "delete"):
            if not op.get("id"):
                raise _bad(index, f"{action} needs id", "tee_scene_summary lists ids")
            if action == "set":
                for key in props:
                    if key not in ("name", "expression", "suppressed", "visible"):
                        raise _bad(
                            index,
                            f"Property {key!r} is not settable",
                            "set takes name, expression (parameters and extrudes), suppressed "
                            "(features) and visible (bodies, sketches).",
                        )
        elif action == "param_set":
            if not op.get("name") or op.get("expression") is None:
                raise _bad(
                    index,
                    "param_set needs name and expression",
                    '{"op":"param_set","name":"width","expression":"120 mm"}',
                )
        elif action == "import_file":
            path = str(op.get("path") or "")
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext not in IMPORT_SUFFIXES:
                raise _bad(
                    index,
                    f"Fusion does not import '.{ext or '?'}' files",
                    f"Suffixes the ImportManager reads: {', '.join(IMPORT_SUFFIXES)} - meshes "
                    "(obj/stl/glb) are not among them.",
                )
            scale = props.get("scale")
            if scale and any(abs(float(s) - 1.0) > 1e-9 for s in scale):
                raise _bad(
                    index,
                    "Fusion imports carry their own units; a scale is not applied",
                    "Drop props.scale - STEP/IGES/SAT/f3d files declare their units.",
                )


def _check_create(index: int, kind: str, props: dict[str, Any]) -> None:
    if kind == "sketch":
        plane = str(props.get("plane") or "XY").upper()
        if plane not in PLANES:
            raise _bad(index, f"Unknown sketch plane '{plane}'", "Use XY, XZ or YZ.")
        rects, circles = props.get("rects") or [], props.get("circles") or []
        if not rects and not circles:
            raise _bad(
                index,
                "A sketch needs geometry",
                'props: {"plane":"XY","rects":[[x1,y1,x2,y2]],"circles":[[cx,cy,r]]} in mm',
            )
        for r in rects:
            if not (isinstance(r, (list, tuple)) and len(r) == 4 and all(_number(v) for v in r)):
                raise _bad(index, "A rect is [x1, y1, x2, y2] in mm", "e.g. [0, 0, 120, 80]")
        for c in circles:
            if not (
                isinstance(c, (list, tuple))
                and len(c) == 3
                and all(_number(v) for v in c)
                and c[2] > 0
            ):
                raise _bad(index, "A circle is [cx, cy, r] in mm with r > 0", "e.g. [60, 40, 5]")
    elif kind == "extrude":
        if not props.get("sketch") or not _number(props.get("distance")):
            raise _bad(
                index,
                "An extrude needs sketch (id) and distance (mm)",
                '{"op":"create","kind":"extrude","props":{"sketch":"sk1","distance":10}}',
            )
        if float(props["distance"]) == 0:
            raise _bad(index, "An extrude distance cannot be 0", "Give a distance in mm.")
        op = str(props.get("operation") or "new_body")
        if op not in OPERATIONS:
            raise _bad(index, f"Unknown operation '{op}'", f"Use: {', '.join(OPERATIONS)}.")
        profile = props.get("profile", "all")
        if not (profile == "all" or (isinstance(profile, int) and profile >= 0)):
            raise _bad(index, "profile is 'all' or a profile index", 'e.g. "profile": 0')
    elif kind == "fillet":
        radius = props.get("radius")
        if not props.get("body") or not _number(radius) or float(radius) <= 0:
            raise _bad(
                index,
                "A fillet needs body (id) and radius (mm > 0)",
                '{"op":"create","kind":"fillet","props":{"body":"b1","radius":2}}',
            )
    elif kind == "param":
        value = props.get("value")
        if not (isinstance(value, str) or _number(value)):
            raise _bad(
                index,
                'A param needs value (an expression such as "120 mm")',
                '{"op":"create","kind":"param","name":"width","props":{"value":"120 mm"}}',
            )


# -- emitters -------------------------------------------------------------------


def _emit_sketch(index: int, name: str, props: dict[str, Any]) -> list[str]:
    plane = PLANES[str(props.get("plane") or "XY").upper()]
    lines = [
        f"    _sk = _root.sketches.add(_root.{plane})",
        f"    _sk.name = {_lit(name)}",
    ]
    for x1, y1, x2, y2 in props.get("rects") or []:
        lines.append(
            "    _sk.sketchCurves.sketchLines.addTwoPointRectangle("
            f"adsk.core.Point3D.create({_cm(x1)!r}, {_cm(y1)!r}, 0.0), "
            f"adsk.core.Point3D.create({_cm(x2)!r}, {_cm(y2)!r}, 0.0))"
        )
    for cx, cy, r in props.get("circles") or []:
        lines.append(
            "    _sk.sketchCurves.sketchCircles.addByCenterRadius("
            f"adsk.core.Point3D.create({_cm(cx)!r}, {_cm(cy)!r}, 0.0), {_cm(r)!r})"
        )
    lines += [
        '    _sid = _mint("sk", _sk.entityToken); _mark(_sid, True); _note(_sid, "sketch", _sk)',
    ]
    return lines


def _emit_extrude(index: int, name: str, props: dict[str, Any]) -> list[str]:
    sketch = str(props["sketch"])
    distance = float(props["distance"])
    operation = OPERATIONS[str(props.get("operation") or "new_body")]
    direction = "PositiveExtentDirection" if distance > 0 else "NegativeExtentDirection"
    profile = props.get("profile", "all")
    lines = [
        f"    _sk = _find({_lit(sketch)}, {index})",
        "    if _sk.profiles.count == 0:",
        f"        raise _OpError({index}, 'sketch %r has no closed profile to extrude' "
        f"% {_lit(sketch)})",
    ]
    if profile == "all":
        lines += [
            "    _prof = adsk.core.ObjectCollection.create()",
            "    for _i in range(_sk.profiles.count): _prof.add(_sk.profiles.item(_i))",
        ]
    else:
        lines += [
            f"    if _sk.profiles.count <= {int(profile)}:",
            f"        raise _OpError({index}, 'sketch %r has %d profiles, none at index "
            f"{int(profile)}' "
            f"% ({_lit(sketch)}, _sk.profiles.count))",
            f"    _prof = _sk.profiles.item({int(profile)})",
        ]
    lines += [
        "    _inp = _root.features.extrudeFeatures.createInput("
        f"_prof, adsk.fusion.FeatureOperations.{operation})",
        f"    _dist = adsk.core.ValueInput.createByString({_lit(_mm_expr(abs(distance)))})",
        "    _inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(_dist), "
        f"adsk.fusion.ExtentDirections.{direction})",
        "    _f = _root.features.extrudeFeatures.add(_inp)",
        f"    if _f is None: raise _OpError({index}, 'extrude failed: Fusion returned null')",
        f"    _f.name = {_lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
        "    _mark_bodies(_f)",
    ]
    return lines


def _emit_fillet(index: int, name: str, props: dict[str, Any]) -> list[str]:
    body = str(props["body"])
    return [
        f"    _b = _find({_lit(body)}, {index})",
        "    _edges = adsk.core.ObjectCollection.create()",
        "    for _i in range(_b.edges.count): _edges.add(_b.edges.item(_i))",
        "    _inp = _root.features.filletFeatures.createInput()",
        "    _inp.edgeSetInputs.addConstantRadiusEdgeSet(_edges, "
        f"adsk.core.ValueInput.createByString({_lit(_mm_expr(float(props['radius'])))}), True)",
        "    _f = _root.features.filletFeatures.add(_inp)",
        f"    if _f is None: raise _OpError({index}, 'fillet failed: Fusion returned null')",
        f"    _f.name = {_lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
        '    _bid = _mint("b", _b.entityToken); _mark(_bid, False); _note(_bid, "body", _b)',
        "    _mark_bodies(_f)",
    ]


def _emit_component(index: int, name: str, kind: str) -> list[str]:
    lines = [
        "    _occ = _root.occurrences.addNewComponent(adsk.core.Matrix3D.create())",
        f"    _occ.component.name = {_lit(name)}",
        '    _cid = _mint("c", _occ.entityToken); _mark(_cid, True)',
    ]
    if kind != "component":
        lines.append(f"    _kinds[_cid] = {_lit(kind)}")
    lines.append('    _note(_cid, "component", _occ)')
    return lines


def _emit_param(index: int, name: str, props: dict[str, Any]) -> list[str]:
    units = str(props.get("units", "mm"))
    value = props["value"]
    expression = value if isinstance(value, str) else f"{value:g} {units}".strip()
    comment = str(props.get("comment") or "")
    return [
        f"    _p = _design.userParameters.add({_lit(name)}, "
        f"adsk.core.ValueInput.createByString({_lit(expression)}), {_lit(units)}, {_lit(comment)})",
        f"    if _p is None: raise _OpError({index}, 'parameter %r was not created (name taken, or "
        f"a bad expression?)' % {_lit(name)})",
        '    _pid = "param:" + str(_p.name); _mark(_pid, True); _note(_pid, "param", _p)',
    ]


def _emit_create(index: int, op: dict[str, Any]) -> list[str]:
    kind = str(op.get("kind") or "")
    name = str(op.get("name") or f"{kind}{index}")
    props = dict(op.get("props") or {})
    if kind == "sketch":
        return _emit_sketch(index, name, props)
    if kind == "extrude":
        return _emit_extrude(index, name, props)
    if kind == "fillet":
        return _emit_fillet(index, name, props)
    if kind == "param":
        return _emit_param(index, name, props)
    # `component`, and the kit contract's generic kind: a named empty
    # component, the kind kept in the bridge's map
    return _emit_component(index, name, kind)


def _emit_set(index: int, op: dict[str, Any]) -> list[str]:
    sid = str(op["id"])
    lines = [
        f"    _e = _find({_lit(sid)}, {index})",
        f'    _k = "param" if {_lit(sid)}.startswith("param:") else _kind_of(_e)',
    ]
    for key, value in dict(op.get("props") or {}).items():
        if key == "name":
            lines += [
                f'    if _k == "component": _e.component.name = {_lit(str(value))}',
                f"    else: _e.name = {_lit(str(value))}",
            ]
        elif key == "expression":
            lines += [
                f'    if _k == "param": _e.expression = {_lit(str(value))}',
                f'    elif _k == "feature" and hasattr(_e, "extentOne"): '
                f"_e.extentOne.distance.expression = {_lit(str(value))}",
                f"    else: raise _OpError({index}, 'only user parameters and extrudes take an "
                "expression')",
            ]
        elif key == "suppressed":
            lines += [
                f'    if _k != "feature": raise _OpError({index}, '
                '"only a feature can be suppressed")',
                f"    _e.isSuppressed = {bool(value)!r}",
            ]
        elif key == "visible":
            lines += [
                f'    if _k not in ("body", "sketch"): raise _OpError({index}, "only bodies and '
                'sketches take visible")',
                f"    _e.isVisible = {bool(value)!r}",
            ]
    lines += [
        f"    _mark({_lit(sid)}, False); _note({_lit(sid)}, _k, _e)",
    ]
    return lines


def _emit_delete(index: int, op: dict[str, Any]) -> list[str]:
    sid = str(op["id"])
    return [
        f"    _e = _find({_lit(sid)}, {index})",
        "    _ok = _e.deleteMe()",
        f"    if _ok is False: raise _OpError({index}, 'Fusion refused to delete %r' "
        f"% {_lit(sid)})",
        f"    deleted.append({_lit(sid)}); _forget({_lit(sid)})",
    ]


def _emit_param_set(index: int, op: dict[str, Any]) -> list[str]:
    name = str(op["name"])
    return [
        f"    _p = _design.userParameters.itemByName({_lit(name)})",
        f"    if _p is None: raise _OpError({index}, 'no user parameter %r' % {_lit(name)}, "
        "'fusion_unknown_entity')",
        f"    _p.expression = {_lit(str(op['expression']))}",
        '    _pid = "param:" + str(_p.name); _mark(_pid, False); _note(_pid, "param", _p)',
    ]


def _emit_import(index: int, op: dict[str, Any]) -> list[str]:
    path = str(op["path"])
    ext = path.rsplit(".", 1)[-1].lower()
    name = op.get("name")
    lines = [
        f"    _opts = _app.importManager.{_IMPORT_OPTIONS[ext]}({_lit(path)})",
        "    _res = _app.importManager.importToTarget2(_opts, _root)",
        f"    if _res is None: raise _OpError({index}, 'import of %r failed (Fusion returned "
        "null)' "
        f"% {_lit(path)})",
        "    for _i in range(_res.count):",
        "        _e = _res.item(_i); _k = _kind_of(_e)",
        '        if _k in ("body", "component", "sketch"):',
        "            _sid = _mint(_prefix_for(_k), _e.entityToken); _mark(_sid, True)",
    ]
    if name:
        lines += [
            f"            if _i == 0 and _k == 'component': _e.component.name = {_lit(str(name))}",
            f"            elif _i == 0: _e.name = {_lit(str(name))}",
        ]
    lines.append("            _note(_sid, _k, _e)")
    return lines


def compile_batch(ops: list[dict[str, Any]]) -> str:
    """ops -> one script assigning one JSON-shaped `result`."""
    check_batch(ops)
    body: list[str] = []
    for index, op in enumerate(ops):
        action = str(op.get("op") or "")
        body.append(f"    # op {index}: {action}")
        if action == "create":
            body.extend(_emit_create(index, op))
        elif action == "set":
            body.extend(_emit_set(index, op))
        elif action == "delete":
            body.extend(_emit_delete(index, op))
        elif action == "param_set":
            body.extend(_emit_param_set(index, op))
        elif action == "import_file":
            body.extend(_emit_import(index, op))
    return _PRELUDE + _BATCH_HEAD + "\n".join(body) + "\n" + _BATCH_TAIL + _EPILOGUE


# -- standalone programs: reads, checkpoints, capture, export ---------------------

LIST_PROGRAM = (
    _PRELUDE
    + """\
    for _sid, _token in list(_ids.items()):
        if not _design.findEntityByToken(_token): _forget(_sid)
    rows = []
    def _emit(kind, ent, parent=None):
        sid = _sid_of(kind, ent)
        row = {"id": sid, "name": _name_of(kind, ent), "kind": _kinds.get(sid, kind)}
        if parent: row["parent"] = parent
        rows.append([row, _summary(kind, ent)]); return sid
    for _i in range(_root.sketches.count): _emit("sketch", _root.sketches.item(_i))
    for _i in range(_root.features.count): _emit("feature", _root.features.item(_i))
    for _i in range(_root.bRepBodies.count): _emit("body", _root.bRepBodies.item(_i))
    for _i in range(_root.occurrences.count):
        _occ = _root.occurrences.item(_i); _cid = _emit("component", _occ); _comp = _occ.component
        for _j in range(_comp.bRepBodies.count): _emit("body", _comp.bRepBodies.item(_j), _cid)
        for _j in range(_comp.sketches.count): _emit("sketch", _comp.sketches.item(_j), _cid)
    for _i in range(_design.userParameters.count): _emit("param", _design.userParameters.item(_i))
    result = {"rows": rows}
"""
    + _EPILOGUE
)

PROBE_PROGRAM = (
    _PRELUDE
    + """\
    _doc = _app.activeDocument
    _parametric = _design.designType == adsk.fusion.DesignTypes.ParametricDesignType
    result = {
        "version": str(_app.version), "document": str(_doc.name) if _doc is not None else None,
        "saved": bool(_doc.isSaved) if _doc is not None else None,
        "design": "parametric" if _parametric else "direct",
        "root": str(_root.name), "bodies": _root.bRepBodies.count, "sketches": _root.sketches.count,
        "features": _root.features.count, "components": _root.occurrences.count,
        "user_parameters": _design.userParameters.count, "timeline": _design.timeline.count,
        "ids": len(_ids),
    }
"""
    + _EPILOGUE
)

SNAPSHOT_PROGRAM = (
    _PRELUDE
    + """\
    if _design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
        raise _OpError(-1, "this design is direct-modeling: it has no timeline to roll back",
                       "fusion_direct_design")
    _tl = _design.timeline; _params = {}
    for _i in range(_design.allParameters.count):
        _p = _design.allParameters.item(_i); _params[str(_p.name)] = str(_p.expression)
    result = {"marker": _tl.markerPosition, "count": _tl.count, "params": _params}
"""
    + _EPILOGUE
)


def restore_program(marker: int, params: dict[str, str]) -> str:
    return (
        _PRELUDE
        + f"""\
    _tl = _design.timeline
    if _tl.count > {int(marker)}:
        _tl.markerPosition = {int(marker)}; _tl.deleteAllAfterMarker()
    _tl.moveToEnd()
    _want = {_lit(dict(params))}; _restored = 0
    for _i in range(_design.allParameters.count):
        _p = _design.allParameters.item(_i); _e = _want.get(str(_p.name))
        if _e is not None and str(_p.expression) != _e: _p.expression = _e; _restored += 1
    result = {{"count": _tl.count, "restored_params": _restored}}
"""
        + _EPILOGUE
    )


def capture_program(jpg_path: str, png_path: str, width: int, height: int) -> str:
    return (
        _PRELUDE
        + f"""\
    _vp = _app.activeViewport
    if _vp is None: raise _OpError(-1, "no viewport: no document is open", "fusion_no_design")
    _vp.fit()
    _ext = "jpg"
    if not _vp.saveAsImageFile({_lit(jpg_path)}, {int(width)}, {int(height)}):
        _ext = "png"
        if not _vp.saveAsImageFile({_lit(png_path)}, {int(width)}, {int(height)}):
            raise _OpError(-1, "Viewport.saveAsImageFile refused both .jpg and .png",
                           "fusion_capture_failed")
    result = {{"ext": _ext}}
"""
        + _EPILOGUE
    )


def measure_program(of: str | None) -> str:
    target = f"_find({_lit(of)})" if of else "_root"
    return (
        _PRELUDE
        + f"""\
    _ent = {target}
    if _ent.objectType.endswith("Occurrence"): _ent = _ent.component
    _pp = _ent.physicalProperties; _bb = _ent.boundingBox
    result = {{"volume_mm3": round(float(_pp.volume) * 1000.0, 3),
              "area_mm2": round(float(_pp.area) * 100.0, 3),
              "mass_kg": round(float(_pp.mass), 6), "centre_of_mass_mm": _pt(_pp.centerOfMass),
              "bbox_mm": _bbox_mm(_bb), "of": {_lit(of or "root")}}}
"""
        + _EPILOGUE
    )


PARAMS_PROGRAM = (
    _PRELUDE
    + """\
    rows = []
    for _i in range(_design.allParameters.count):
        _p = _design.allParameters.item(_i)
        rows.append({"name": str(_p.name), "expression": str(_p.expression), "unit": str(_p.unit),
                     "value": _param_value(_p),
                     "user": _design.userParameters.itemByName(str(_p.name)) is not None})
    result = {"rows": rows}
"""
    + _EPILOGUE
)

TIMELINE_PROGRAM = (
    _PRELUDE
    + """\
    _tl = _design.timeline; rows = []
    for _i in range(_tl.count):
        _o = _tl.item(_i)
        _ent = None if _o.isGroup else _o.entity
        row = {"index": _o.index, "name": str(_o.name),
               "type": ("group" if _o.isGroup else
                        (_ent.objectType.split("::")[-1] if _ent is not None else None))}
        if _o.isSuppressed: row["suppressed"] = True
        if _o.isRolledBack: row["rolled_back"] = True
        _msg = _o.errorOrWarningMessage
        if _msg: row["health"] = str(_msg)[:120]
        rows.append(row)
    result = {"rows": rows, "marker": _tl.markerPosition, "count": _tl.count}
"""
    + _EPILOGUE
)


def export_program(fmt: str, path: str, of: str | None) -> str:
    method, order, _suffix = EXPORT_FORMATS[fmt]
    geometry = f"_find({_lit(of)})" if of else "None"
    if order == "filename_first":
        make = (
            f"    _opts = _mgr.{method}({_lit(path)}, _geom) if _geom is not None "
            f"else _mgr.{method}({_lit(path)})"
        )
    else:
        make = f"    _opts = _mgr.{method}(_geom if _geom is not None else _root, {_lit(path)})"
    return (
        _PRELUDE
        + f"""\
    import os
    _geom = {geometry}
    if _geom is not None and _geom.objectType.endswith("Occurrence"): _geom = _geom.component
    _mgr = _design.exportManager
{make}
    if not _mgr.execute(_opts):
        raise _OpError(-1, "ExportManager.execute returned false", "fusion_export_failed")
    result = {{"path": {_lit(path)}, "bytes": os.path.getsize({_lit(path)}), "format": {_lit(fmt)}}}
"""
        + _EPILOGUE
    )


def path_suffix(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")


def as_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))
