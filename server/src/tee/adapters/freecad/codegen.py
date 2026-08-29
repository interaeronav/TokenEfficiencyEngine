"""Batch-op codegen for the FreeCAD adapter (A37 P4).

One tee_batch compiles to ONE Python script executed in ONE bridge round
trip (batch over chatter, applied at the wire). The script applies ops
in order, recomputes once, and prints a single JSON diff; the first
failing op prints a JSON error and stops, and the kernel's checkpoint
restores (run_batch's atomicity contract).

Units: the fabrication lane speaks millimetres end to end (FreeCAD's
native unit; the 32 mm joinery world's too). sketch geometry arrives
SOLVED - see tools/adapter - so scripts place final coordinates and
never lean on FreeCAD's solver converging from guesses.

API notes (verified live on 1.1.3 by the P4 smoke, not from memory):
Part primitives via doc.addObject + property assignment; solids from
sketches via Part::Extrusion (DirMode/LengthFwd/Solid); pockets via a
generated tool extrusion + Part::Cut. PartDesign bodies are deliberately
NOT used in v1 - Part-workbench objects have the stabler scripting
surface; recorded as a limitation with the upgrade path.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError

PRIMITIVES = {
    "box": "Part::Box",
    "cylinder": "Part::Cylinder",
    "sphere": "Part::Sphere",
    "cone": "Part::Cone",
    "part": "App::Part",
}
KNOWN_KINDS = (*PRIMITIVES, "sketch", "pad", "pocket")

_PRELUDE = """\
import FreeCAD, Part, Sketcher, json
doc = FreeCAD.getDocument({doc!r})
created, modified, deleted, details = [], [], [], {{}}
def _detail(o):
    d = {{}}
    for p in ("Length", "Width", "Height", "Radius", "LengthFwd"):
        if hasattr(o, p):
            try: d[p.lower()] = float(getattr(o, p))
            except Exception: pass
    if hasattr(o, "Shape") and o.Shape is not None and o.Shape.Faces:
        d["faces"] = len(o.Shape.Faces); d["volume_mm3"] = round(o.Shape.Volume, 1)
    return d
try:
"""

_EPILOGUE = """\
        doc.recompute()
        for _n in created + modified:
            _o = doc.getObject(_n)
            if _o is not None: details[_n] = _detail(_o)
        print(json.dumps({"created": created, "modified": modified,
                          "deleted": deleted, "details": details}))
except _OpError as exc:
    print(json.dumps({"error": {"op_index": exc.index, "message": str(exc)[:300]}}))
except Exception as exc:
    print(json.dumps({"error": {"op_index": -1, "message": str(exc)[:300]}}))
"""

_OP_ERROR = """\
class _OpError(Exception):
    def __init__(self, index, message):
        super().__init__(message); self.index = index
"""


def _lit(value: Any) -> str:
    return repr(value)


def _emit_create(op: dict[str, Any], index: int) -> list[str]:
    kind = str(op.get("kind") or "")
    name = str(op.get("name") or f"obj{index}")
    props = dict(op.get("props") or {})
    if kind in PRIMITIVES:
        lines = [
            f"        _o = doc.addObject({PRIMITIVES[kind]!r}, {name!r})",
            f"        _o.Label = {name!r}",
        ]
        for key, value in props.items():
            if key == "at":
                x, y, z = (float(v) for v in value)
                lines.append(f"        _o.Placement.Base = FreeCAD.Vector({x!r}, {y!r}, {z!r})")
            elif key.isidentifier():
                lines.append(f"        setattr(_o, {key!r}, {_lit(value)})")
            else:
                raise TeeError(
                    "bad_op",
                    f"Property {key!r} is not assignable (batch index {index}).",
                    fix="Property names are FreeCAD attribute names (Length, Radius, ...).",
                )
        lines.append("        created.append(_o.Name)")
        return lines
    if kind == "sketch":
        return _emit_sketch(name, props, index)
    if kind == "pad":
        return _emit_pad(name, props, index)
    if kind == "pocket":
        return _emit_pocket(name, props, index)
    if kind and kind.replace("_", "").isalnum():
        # generic kind (the kit contract's plain "object", assembly
        # metadata, jigs): a FeaturePython carrying dynamic properties
        return _emit_generic(kind, name, props, index)
    raise TeeError(
        "bad_op",
        f"Unknown create kind '{kind}' at batch index {index}.",
        fix=f"Kinds: {', '.join(KNOWN_KINDS)} or a plain word for a generic object.",
    )


_PROP_TYPES = (
    (bool, "App::PropertyBool"),
    (int, "App::PropertyInteger"),
    (float, "App::PropertyFloat"),
    (str, "App::PropertyString"),
)


def _emit_generic(kind: str, name: str, props: dict[str, Any], index: int) -> list[str]:
    lines = [
        f"        _o = doc.addObject('App::FeaturePython', {name!r})",
        f"        _o.Label = {name!r}",
        f"        _o.addProperty('App::PropertyString', 'tee_kind'); _o.tee_kind = {kind!r}",
    ]
    for key, value in props.items():
        if not key.isidentifier():
            raise TeeError(
                "bad_op",
                f"Property {key!r} is not assignable (batch index {index}).",
                fix="Property names must be identifiers.",
            )
        for py_type, fc_type in _PROP_TYPES:
            if isinstance(value, py_type):
                lines.append(
                    f"        _o.addProperty({fc_type!r}, {key!r}); "
                    f"setattr(_o, {key!r}, {_lit(value)})"
                )
                break
        else:
            lines.append(
                f"        _o.addProperty('App::PropertyString', {key!r}); "
                f"setattr(_o, {key!r}, {str(value)!r})"
            )
    lines.append("        created.append(_o.Name)")
    return lines


def _emit_sketch(name: str, props: dict[str, Any], index: int) -> list[str]:
    """SOLVED points arrive from the adapter (sketch_solve ran already);
    the script places final line geometry - closure by construction."""
    points = props.get("_solved_points")
    lines_spec = props.get("lines") or []
    if not isinstance(points, dict) or not lines_spec:
        raise TeeError(
            "bad_op",
            f"Sketch op needs points+lines (batch index {index}).",
            fix="Give points/lines/constraints per the sketch_solve contract (mm).",
        )
    out = [f"        _sk = doc.addObject('Sketcher::SketchObject', {name!r})"]
    plane = str(props.get("plane") or "XY")
    placements = {
        "XY": None,
        "XZ": "FreeCAD.Placement(FreeCAD.Vector(0,0,0), "
        "FreeCAD.Rotation(FreeCAD.Vector(1,0,0), 90))",
        "YZ": "FreeCAD.Placement(FreeCAD.Vector(0,0,0), "
        "FreeCAD.Rotation(FreeCAD.Vector(0,1,0), -90) * "
        "FreeCAD.Rotation(FreeCAD.Vector(0,0,1), -90))",
    }
    if plane not in placements:
        raise TeeError("bad_op", f"Unknown sketch plane '{plane}'.", fix="Use XY, XZ or YZ.")
    if placements[plane]:
        out.append(f"        _sk.Placement = {placements[plane]}")
    for line in lines_spec:
        a, b = points[str(line["from"])], points[str(line["to"])]
        out.append(
            "        _sk.addGeometry(Part.LineSegment("
            f"FreeCAD.Vector({a[0]!r}, {a[1]!r}, 0), "
            f"FreeCAD.Vector({b[0]!r}, {b[1]!r}, 0)), False)"
        )
    out.append("        created.append(_sk.Name)")
    return out


def _emit_pad(name: str, props: dict[str, Any], index: int) -> list[str]:
    sketch = props.get("sketch")
    length = props.get("length")
    if not sketch or not length:
        raise TeeError(
            "bad_op",
            f"Pad needs sketch and length (batch index {index}).",
            fix='{"op":"create","kind":"pad","props":{"sketch":"<id>","length":mm}}',
        )
    return [
        f"        _base = doc.getObject({str(sketch)!r})",
        f"        if _base is None: raise _OpError({index}, 'no sketch %r' % {str(sketch)!r})",
        f"        _o = doc.addObject('Part::Extrusion', {name!r})",
        "        _o.Base = _base; _o.DirMode = 'Normal'; _o.Solid = True",
        f"        _o.LengthFwd = {float(length)!r}",
        "        _base.Visibility = False",
        "        created.append(_o.Name)",
    ]


def _emit_pocket(name: str, props: dict[str, Any], index: int) -> list[str]:
    sketch, target, depth = props.get("sketch"), props.get("target"), props.get("depth")
    if not sketch or not target or not depth:
        raise TeeError(
            "bad_op",
            f"Pocket needs sketch, target and depth (batch index {index}).",
            fix='{"op":"create","kind":"pocket","props":{"sketch":"<id>","target":"<id>","depth":mm}}',
        )
    return [
        f"        _base = doc.getObject({str(sketch)!r})",
        f"        _tgt = doc.getObject({str(target)!r})",
        f"        if _base is None or _tgt is None:\n"
        f"            raise _OpError({index}, 'pocket needs existing sketch+target')",
        f"        _tool = doc.addObject('Part::Extrusion', {name!r} + '_tool')",
        "        _tool.Base = _base; _tool.DirMode = 'Normal'; _tool.Solid = True",
        f"        _tool.LengthFwd = {float(depth)!r}; _tool.LengthRev = 1.0",
        f"        _o = doc.addObject('Part::Cut', {name!r})",
        "        _o.Base = _tgt; _o.Tool = _tool",
        "        _base.Visibility = False",
        "        created.append(_o.Name)",
    ]


def compile_batch(doc: str, ops: list[dict[str, Any]]) -> str:
    """ops -> one script printing one JSON diff line."""
    body: list[str] = []
    for index, op in enumerate(ops):
        action = str(op.get("op") or "")
        body.append(f"        # op {index}: {action}")
        if action == "create":
            body.extend(_emit_create(op, index))
        elif action == "set":
            eid = str(op.get("id") or "")
            body.append(f"        _o = doc.getObject({eid!r})")
            body.append(f"        if _o is None: raise _OpError({index}, 'no entity %r' % {eid!r})")
            for key, value in dict(op.get("props") or {}).items():
                if key == "at":
                    x, y, z = (float(v) for v in value)
                    body.append(f"        _o.Placement.Base = FreeCAD.Vector({x!r}, {y!r}, {z!r})")
                elif key == "name":
                    body.append(f"        _o.Label = {str(value)!r}")
                elif key.isidentifier():
                    body.append(f"        setattr(_o, {key!r}, {_lit(value)})")
                else:
                    raise TeeError(
                        "bad_op",
                        f"Property {key!r} is not assignable (batch index {index}).",
                        fix="Property names are FreeCAD attribute names.",
                    )
            body.append("        modified.append(_o.Name)")
        elif action == "delete":
            eid = str(op.get("id") or "")
            body.append(f"        _o = doc.getObject({eid!r})")
            body.append(f"        if _o is None: raise _OpError({index}, 'no entity %r' % {eid!r})")
            body.append(f"        doc.removeObject({eid!r}); deleted.append({eid!r})")
        else:
            raise TeeError(
                "bad_op",
                f"Unknown op '{action}' at batch index {index}.",
                fix="Use one of: create, set, delete.",
            )
    return (
        _OP_ERROR
        + _PRELUDE.format(doc=doc)
        + ("\n".join(body) + "\n" if body else "        pass\n")
        + _EPILOGUE
    )


LIST_CODE = """\
import FreeCAD, json
doc = FreeCAD.getDocument({doc!r})
rows = []
for o in doc.Objects:
    row = {{"id": o.Name, "name": o.Label, "kind": o.TypeId}}
    s = {{}}
    for p in ("Length", "Width", "Height", "Radius", "LengthFwd"):
        if hasattr(o, p):
            try: s[p.lower()] = float(getattr(o, p))
            except Exception: pass
    if hasattr(o, "Placement"):
        b = o.Placement.Base
        s["at"] = [round(b.x, 3), round(b.y, 3), round(b.z, 3)]
    try:
        if hasattr(o, "Shape") and o.Shape is not None and o.Shape.Faces:
            s["faces"] = len(o.Shape.Faces)
            s["volume_mm3"] = round(o.Shape.Volume, 1)
    except Exception:
        pass
    rows.append([row, s])
print(json.dumps(rows))
"""
