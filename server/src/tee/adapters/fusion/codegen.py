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
import re
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

OPS = ("create", "set", "delete", "param_set", "import_file")
KINDS = (
    "sketch",
    "extrude",
    "fillet",
    "component",
    "param",
    "constraint",
    "dimension",
    "hole",
    "chamfer",
    "revolve",
    "joint",
)
# A70 P2 (doc 71 section 10.2): a face is named by its outward normal.
FACES = ("+x", "-x", "+y", "-y", "+z", "-z")
HOLE_TYPES = ("simple", "counterbore", "countersink")
AXES = {"x": "xConstructionAxis", "y": "yConstructionAxis", "z": "zConstructionAxis"}
# A70 P3 (doc 71 row 45): motion -> the JointInput setter and which of
# `axis` / `slide` it takes. Ball uses pitch Z and yaw X, the enum's own
# defaults; no custom-direction entities in v2.
MOTIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "rigid": ("setAsRigidJointMotion", ()),
    "revolute": ("setAsRevoluteJointMotion", ("axis",)),
    "slider": ("setAsSliderJointMotion", ("axis",)),
    "cylindrical": ("setAsCylindricalJointMotion", ("axis",)),
    "pin_slot": ("setAsPinSlotJointMotion", ("axis", "slide")),
    "planar": ("setAsPlanarJointMotion", ("axis",)),
    "ball": ("setAsBallJointMotion", ("pitch", "yaw")),
}
DIRECTIONS = {"x": "XAxisJointDirection", "y": "YAxisJointDirection", "z": "ZAxisJointDirection"}
_SET_KEYS = (
    "name",
    "expression",
    "suppressed",
    "visible",
    "angle",
    "offset",
    "flipped",
    "rotation",
    "slide",
)
IMPORT_SUFFIXES = ("step", "stp", "f3d", "igs", "iges", "sat")
# A70 (doc 71 row 40): constraint type -> (arity, the GeometricConstraints call).
# coincident is (point, entity), midpoint (point, curve), symmetry (a, b, line).
CONSTRAINTS: dict[str, tuple[int, str]] = {
    "horizontal": (1, "addHorizontal"),
    "vertical": (1, "addVertical"),
    "parallel": (2, "addParallel"),
    "perpendicular": (2, "addPerpendicular"),
    "collinear": (2, "addCollinear"),
    "equal": (2, "addEqual"),
    "tangent": (2, "addTangent"),
    "concentric": (2, "addConcentric"),
    "coincident": (2, "addCoincident"),
    "midpoint": (2, "addMidPoint"),
    "symmetry": (3, "addSymmetry"),
}
# Row 41: dimension type -> (arity, the SketchDimensions call).
DIMENSIONS: dict[str, tuple[int, str]] = {
    "distance": (2, "addDistanceDimension"),
    "diameter": (1, "addDiameterDimension"),
    "radius": (1, "addRadialDimension"),
    "angle": (2, "addAngularDimension"),
}
ORIENTATIONS = {
    "aligned": "AlignedDimensionOrientation",
    "horizontal": "HorizontalDimensionOrientation",
    "vertical": "VerticalDimensionOrientation",
}
_ADDRESS_HELP = (
    "an address is r0.bottom|top|left|right, r0.bl|br|tl|tr, l0, l0.start|end, c0, "
    "c0.center, p0 or origin - prefixed sk1/ outside the sketch op"
)
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
    _subs = _tee.setdefault("subs", {}); _names = _tee.setdefault("names", {})
    def _mint(prefix, token):
        sid = _toks.get(token)
        if sid is None:
            n = _counts.get(prefix, 0) + 1; _counts[prefix] = n
            sid = "%s%d" % (prefix, n); _ids[sid] = token; _toks[token] = sid
        return sid
    def _forget(sid):
        token = _ids.pop(sid, None); _toks.pop(token, None); _kinds.pop(sid, None)
        _subs.pop(sid, None); _names.pop(sid, None)
    def _sub(skid, ref, index=-1):
        # a sketch-local address (doc 71 section 10.1): r0.bottom, l1.start, c0.center, p2, origin
        m = _subs.get(skid, {}); token = m.get(ref)
        if token is None:
            raise _OpError(index, "sketch %r has no entity %r (it has: %s)"
                           % (skid, ref, ", ".join(sorted(m)) or "-"), "fusion_unknown_entity")
        ents = _design.findEntityByToken(token)
        if not ents:
            raise _OpError(index, "sketch entity %s/%s no longer exists" % (skid, ref),
                           "fusion_unknown_entity")
        return ents[0]
    def _rect_subs(m, key, lines):
        # Law 8: the sides are named by where their midpoints lie, never by the
        # order Fusion returned them (row 38 leaves it unstated)
        mids = []
        for _i in range(lines.count):
            _l = lines.item(_i); _a = _l.startSketchPoint.geometry; _b = _l.endSketchPoint.geometry
            mids.append(((_a.x + _b.x) / 2.0, (_a.y + _b.y) / 2.0, _l))
        by_y = sorted(mids, key=lambda t: t[1]); by_x = sorted(mids, key=lambda t: t[0])
        sides = {"bottom": by_y[0][2], "top": by_y[-1][2]}
        sides.update({"left": by_x[0][2], "right": by_x[-1][2]})
        for _n, _l in sides.items(): m[key + "." + _n] = _l.entityToken
        def _ends(l):
            return sorted([l.startSketchPoint, l.endSketchPoint], key=lambda p: p.geometry.x)
        _bot = _ends(sides["bottom"]); _top = _ends(sides["top"])
        m[key + ".bl"] = _bot[0].entityToken; m[key + ".br"] = _bot[1].entityToken
        m[key + ".tl"] = _top[0].entityToken; m[key + ".tr"] = _top[1].entityToken
    def _mid(e):
        t = e.objectType.split("::")[-1]
        if t == "SketchPoint": g = e.geometry; return (g.x, g.y)
        if t == "SketchLine":
            a = e.startSketchPoint.geometry; b = e.endSketchPoint.geometry
            return ((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)
        if t == "SketchCircle":
            c = e.centerSketchPoint.geometry; return (c.x + e.radius, c.y + e.radius)
        return (0.0, 0.0)
    def _text_for(ents):
        pts = [_mid(e) for e in ents]
        return adsk.core.Point3D.create(sum(p[0] for p in pts) / len(pts) + 0.5,
                                        sum(p[1] for p in pts) / len(pts) + 0.5, 0.0)
    _AXIS = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0),
             "+z": (0, 0, 1), "-z": (0, 0, -1)}
    def _normal(face):
        # row 47: a planar face's outward normal is the plane's, flipped when reversed
        g = face.geometry
        if g.surfaceType != adsk.core.SurfaceTypes.PlaneSurfaceType: return None
        n = g.normal; s = -1.0 if face.isParamReversed else 1.0
        return (n.x * s, n.y * s, n.z * s)
    def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
    def _face(body, sel, at=None, index=-1):
        # doc 71 section 10.2: the planar face facing `sel`, outermost along that
        # axis - or, with a 3-vector `at` (cm), the one whose plane passes nearest it
        axis = _AXIS[sel]; hits = []; have = set()
        for _i in range(body.faces.count):
            f = body.faces.item(_i); n = _normal(f)
            if n is None: continue
            for k, v in _AXIS.items():
                if _dot(n, v) > 0.9998: have.add(k)
            if _dot(n, axis) > 0.9998:
                c = f.centroid; hits.append((_dot((c.x, c.y, c.z), axis), f))
        if not hits:
            raise _OpError(index, "body has no planar face facing %s (it has: %s)"
                           % (sel, ", ".join(sorted(have)) or "none"), "fusion_no_face")
        if at is not None and len(at) == 3:
            want = _dot(at, axis); hits.sort(key=lambda t: abs(t[0] - want))
        else:
            hits.sort(key=lambda t: -t[0])
        return hits[0][1]
    def _at_point(face, sel, at):
        # `at` in cm: three coordinates as given (Fusion projects them onto the
        # face, row 32); two fill the normal's axis from the face's centroid
        if len(at) == 3: return adsk.core.Point3D.create(at[0], at[1], at[2])
        axis = _AXIS[sel]; c = [face.centroid.x, face.centroid.y, face.centroid.z]
        vals = list(at); out = [c[k] if axis[k] else vals.pop(0) for k in range(3)]
        return adsk.core.Point3D.create(out[0], out[1], out[2])
    def _edges_of(body, sel, index=-1):
        col = adsk.core.ObjectCollection.create()
        src = body if sel in (None, "all") else _face(body, sel["face"], None, index)
        for _i in range(src.edges.count): col.add(src.edges.item(_i))
        return col
    def _joint_geom(side, index=-1):
        # doc 71 section 10.5: the centre of a planar face of an occurrence's body
        # (rows 44, 47; the bodies under occ.bRepBodies are proxies already, row 12),
        # the occurrence's origin point in its context (rows 37, 44, 47), or a
        # face of a root body
        comp, face, body = side.get("component"), side.get("face"), side.get("body")
        if comp:
            occ = _find(comp, index)
            if _kind_of(occ) != "component":
                raise _OpError(index, "%r is not a component" % comp)
            if face is None:
                pt = occ.component.originConstructionPoint.createForAssemblyContext(occ)
                return adsk.fusion.JointGeometry.createByPoint(pt)
            if body:
                b = _find(body, index)
            elif occ.bRepBodies.count:
                b = occ.bRepBodies.item(0)
            else:
                raise _OpError(index, "component %r has no body to joint by a face - give it "
                               "one, or joint by its origin (omit face)" % comp)
        else:
            b = _find(body, index)
        return adsk.fusion.JointGeometry.createByPlanarFace(
            _face(b, face, None, index), None, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
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
        if t.endswith("Dimension"): return "dimension"
        return {"BRepBody": "body", "Sketch": "sketch", "Occurrence": "component", "Joint": "joint",
                "UserParameter": "param", "ModelParameter": "param"}.get(t, t.lower())
    _PREFIX = {"body": "b", "sketch": "sk", "component": "c", "feature": "f", "dimension": "dim",
               "joint": "j"}
    _MOTION_WORDS = {"RigidJointMotion": "rigid", "RevoluteJointMotion": "revolute",
                     "SliderJointMotion": "slider", "CylindricalJointMotion": "cylindrical",
                     "PinSlotJointMotion": "pin_slot", "PlanarJointMotion": "planar",
                     "BallJointMotion": "ball"}
    def _occ_id(occ): return "root" if occ is None else _mint("c", occ.entityToken)
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
            s["constraints"] = ent.geometricConstraints.count
            s["dims"] = ent.sketchDimensions.count
            s["constrained"] = bool(ent.isFullyConstrained)
        elif kind == "joint":  # row 46
            m = ent.jointMotion; t = m.objectType.split("::")[-1]
            s["motion"] = _MOTION_WORDS.get(t, t)
            s["between"] = [_occ_id(ent.occurrenceOne), _occ_id(ent.occurrenceTwo)]
            s["angle_deg"] = _param_value(ent.angle); s["offset_mm"] = _param_value(ent.offset)
            rv = getattr(m, "rotationValue", None)
            if rv is not None: s["rotation_deg"] = round(float(rv) * 57.29577951308232, 4)
            sv = getattr(m, "slideValue", None)
            if sv is not None: s["slide_mm"] = _mm(sv)
            if ent.isFlipped: s["flipped"] = True
            if ent.isSuppressed: s["suppressed"] = True
            if ent.isLocked: s["locked"] = True
        elif kind == "dimension":
            t = ent.objectType.split("::")[-1]; s["type"] = t; p = ent.parameter
            s["expression"] = str(p.expression) if p is not None else None
            s["value"] = (round(float(ent.value) * 57.29577951308232, 4)
                          if t == "SketchAngularDimension" else _mm(ent.value))
            s["driving"] = bool(ent.isDriving)
        elif kind == "feature":
            s["type"] = ent.objectType.split("::")[-1]; s["bodies"] = ent.bodies.count
            if s["type"] == "HoleFeature":  # row 34
                s["diameter_mm"] = _mm(ent.holeDiameter.value); s["position_mm"] = _pt(ent.position)
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
        if kind == "component": return str(ent.component.name)
        if kind == "dimension":
            return str(ent.parameter.name) if ent.parameter is not None else "dim"
        return str(ent.name)
    def _sid_of(kind, ent):
        if kind == "param": return "param:" + str(ent.name)
        return _mint(_prefix_for(kind), ent.entityToken)
"""

_BATCH_HEAD = """\
    created, modified, deleted, details = [], [], [], {}
    def _note(sid, kind, ent, parent=None):
        row = {"name": _names.get(sid) or _name_of(kind, ent), "kind": _kinds.get(sid, kind)}
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
                for key, value in props.items():
                    if key not in _SET_KEYS:
                        raise _bad(
                            index,
                            f"Property {key!r} is not settable",
                            "set takes name, expression (parameters, dimensions, extrudes, "
                            "holes), suppressed (features, joints), visible (bodies, sketches), "
                            "and on a joint angle (deg), offset (mm), flipped, rotation (deg), "
                            "slide (mm).",
                        )
                    if key in ("angle", "offset") and not (
                        _number(value) or isinstance(value, str)
                    ):
                        raise _bad(index, f"{key} is a number or an expression", '"30 deg"')
                    if key in ("rotation", "slide") and not _number(value):
                        raise _bad(index, f"{key} is a number", "rotation in deg, slide in mm")
                    if key == "flipped" and not isinstance(value, bool):
                        raise _bad(index, "flipped is true or false", '"flipped": true')
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


def _nums(value: Any, n: int) -> bool:
    return isinstance(value, (list, tuple)) and len(value) == n and all(_number(v) for v in value)


_ADDRESS = re.compile(
    r"^(r\d+\.(bottom|top|left|right|bl|br|tl|tr)|l\d+(\.(start|end))?|c\d+(\.center)?|p\d+|origin)$"
)


def _refs(
    index: int, props: dict[str, Any], arity: int, *, inline: bool, what: str
) -> tuple[str | None, list[str]]:
    """The addresses a constraint or dimension names, validated: `of` holds
    exactly `arity` addresses; inside a sketch op they are bare, outside it
    they are bare with `sketch` given or `sk1/`-prefixed, all on one sketch."""
    of = props.get("of")
    if (
        not isinstance(of, list)
        or len(of) != arity
        or not all(isinstance(r, str) and r for r in of)
    ):
        plural = "es" if arity != 1 else ""
        raise _bad(index, f"A {what} takes {arity} address{plural} in `of`", _ADDRESS_HELP)
    skid = props.get("sketch")
    bare: list[str] = []
    for ref in of:
        if "/" in ref:
            prefix, ref = ref.split("/", 1)
            if inline:
                raise _bad(
                    index,
                    f"Inside a sketch op an address is bare: '{ref}', not '{prefix}/{ref}'",
                    _ADDRESS_HELP,
                )
            if skid is None:
                skid = prefix
            elif prefix != skid:
                raise _bad(
                    index,
                    f"Address '{prefix}/{ref}' names another sketch than '{skid}'",
                    "One sketch per constraint or dimension.",
                )
        if not _ADDRESS.match(ref):
            raise _bad(index, f"Bad sketch address '{ref}'", _ADDRESS_HELP)
        bare.append(ref)
    if not inline and not skid:
        raise _bad(
            index,
            f"A {what} needs sketch (id) or sk1/-prefixed addresses",
            '{"op":"create","kind":"constraint","props":{"sketch":"sk1","type":"horizontal",'
            '"of":["r0.bottom"]}}',
        )
    return (None if inline else str(skid)), bare


def _check_constraint(index: int, props: dict[str, Any], *, inline: bool) -> None:
    ctype = str(props.get("type") or "")
    if ctype not in CONSTRAINTS:
        raise _bad(index, f"Unknown constraint type '{ctype}'", f"Types: {', '.join(CONSTRAINTS)}.")
    _refs(index, props, CONSTRAINTS[ctype][0], inline=inline, what=f"{ctype} constraint")


def _check_dimension(index: int, props: dict[str, Any], *, inline: bool) -> None:
    dtype = str(props.get("type") or "")
    if dtype not in DIMENSIONS:
        raise _bad(index, f"Unknown dimension type '{dtype}'", f"Types: {', '.join(DIMENSIONS)}.")
    _refs(index, props, DIMENSIONS[dtype][0], inline=inline, what=f"{dtype} dimension")
    orientation = props.get("orientation")
    if orientation is not None and (dtype != "distance" or str(orientation) not in ORIENTATIONS):
        raise _bad(
            index,
            f"orientation '{orientation}' is not one a {dtype} dimension takes",
            "A distance dimension takes orientation aligned, horizontal or vertical.",
        )
    if "expression" in props and not isinstance(props["expression"], str):
        raise _bad(index, "A dimension expression is a string", '"width" or "120 mm"')
    if "text" in props and not _nums(props["text"], 2):
        raise _bad(index, "text is [x, y] in mm", "e.g. [60, -10]")
    if "driving" in props and not isinstance(props["driving"], bool):
        raise _bad(index, "driving is true or false", "omit it for a driving dimension")


_POINT_ADDRESS = re.compile(r"^(p\d+|r\d+\.(bl|br|tl|tr)|l\d+\.(start|end)|c\d+\.center|origin)$")
_LINE_ADDRESS = re.compile(r"^(r\d+\.(bottom|top|left|right)|l\d+)$")


def _split_address(index: int, text: Any, pattern: re.Pattern[str], what: str) -> tuple[str, str]:
    """'sk2/p0' -> ('sk2', 'p0'), the sketch prefix required outside a sketch op."""
    if not isinstance(text, str) or "/" not in text:
        raise _bad(index, f"{what} is a sketch address with its sketch, e.g. sk2/p0", _ADDRESS_HELP)
    skid, ref = text.split("/", 1)
    if not skid or not pattern.match(ref):
        raise _bad(index, f"{what} '{text}' is not a {what.split()[-1]} address", _ADDRESS_HELP)
    return skid, ref


def _check_edges(index: int, props: dict[str, Any]) -> None:
    edges = props.get("edges", "all")
    if edges == "all":
        return
    if not (isinstance(edges, dict) and str(edges.get("face")) in FACES):
        raise _bad(
            index,
            "edges is 'all' or {face: <direction>}",
            f'e.g. "edges": {{"face": "+z"}} - directions: {", ".join(FACES)}',
        )


def _check_hole(index: int, props: dict[str, Any]) -> None:
    example = (
        '{"op":"create","kind":"hole","props":{"body":"b1","face":"+z","at":[20,20],'
        '"diameter":6.6,"through":true}}'
    )
    diameter = props.get("diameter")
    if not _number(diameter) or float(diameter) <= 0:
        raise _bad(index, "A hole needs diameter (mm > 0)", example)
    htype = str(props.get("type") or "simple")
    if htype not in HOLE_TYPES:
        raise _bad(index, f"Unknown hole type '{htype}'", f"Types: {', '.join(HOLE_TYPES)}.")
    if htype == "counterbore":
        cb_d, cb_depth = props.get("cbore_diameter"), props.get("cbore_depth")
        if not (_number(cb_d) and cb_d > diameter and _number(cb_depth) and cb_depth > 0):
            raise _bad(
                index,
                "A counterbore needs cbore_diameter (mm > diameter) and cbore_depth (mm > 0)",
                '"type":"counterbore","cbore_diameter":11,"cbore_depth":6',
            )
    elif htype == "countersink":
        cs_d, cs_angle = props.get("csink_diameter"), props.get("csink_angle", 90)
        if not (_number(cs_d) and cs_d > diameter and _number(cs_angle) and 0 < cs_angle < 180):
            raise _bad(
                index,
                "A countersink needs csink_diameter (mm > diameter) and csink_angle (deg, "
                "default 90)",
                '"type":"countersink","csink_diameter":12,"csink_angle":90',
            )
    if "point" in props:
        _split_address(index, props["point"], _POINT_ADDRESS, "A hole point")
    else:
        face, at = props.get("face"), props.get("at")
        if not props.get("body") or str(face) not in FACES:
            raise _bad(
                index,
                f"A hole needs body (id) and face (one of {', '.join(FACES)}), or point (a "
                "sketch point address)",
                example,
            )
        if not (_nums(at, 2) or _nums(at, 3)):
            raise _bad(index, "A hole needs at: [u, v] on the face or [x, y, z], in mm", example)
    through, depth = bool(props.get("through", False)), props.get("depth")
    if through == (depth is not None):
        raise _bad(index, "A hole is through: true OR depth (mm > 0), not both", example)
    if depth is not None and (not _number(depth) or float(depth) <= 0):
        raise _bad(index, "depth is mm > 0", example)
    if "flip" in props and not isinstance(props["flip"], bool):
        raise _bad(index, "flip is true or false", "omit it for the default direction")


def _check_revolve(index: int, props: dict[str, Any]) -> None:
    example = '{"op":"create","kind":"revolve","props":{"sketch":"sk1","axis":"x","angle":360}}'
    if not props.get("sketch"):
        raise _bad(index, "A revolve needs sketch (id) and axis", example)
    axis = props.get("axis")
    if axis not in AXES:
        skid, _ = _split_address(index, axis, _LINE_ADDRESS, "A revolve axis")
        if skid != props["sketch"]:
            raise _bad(
                index, f"axis '{axis}' is a line of another sketch than {props['sketch']}", example
            )
    angle = props.get("angle", 360)
    if not _number(angle) or not 0 < float(angle) <= 360:
        raise _bad(index, "angle is degrees in (0, 360]", example)
    if "symmetric" in props and not isinstance(props["symmetric"], bool):
        raise _bad(index, "symmetric is true or false", example)
    op = str(props.get("operation") or "new_body")
    if op not in OPERATIONS:
        raise _bad(index, f"Unknown operation '{op}'", f"Use: {', '.join(OPERATIONS)}.")
    profile = props.get("profile", "all")
    if not (profile == "all" or (isinstance(profile, int) and profile >= 0)):
        raise _bad(index, "profile is 'all' or a profile index", 'e.g. "profile": 0')


def _check_joint(index: int, props: dict[str, Any]) -> None:
    example = (
        '{"op":"create","kind":"joint","props":{"one":{"component":"c1","face":"+z"},'
        '"two":{"component":"c2","face":"-z"},"motion":"revolute","axis":"z"}}'
    )
    for which in ("one", "two"):
        side = props.get(which)
        if not isinstance(side, dict):
            raise _bad(index, f"A joint needs {which}: a side", example)
        if not side.get("component") and not side.get("body"):
            raise _bad(
                index,
                f"Side {which} names a component (with an optional face) or a body with a face",
                example,
            )
        if "face" in side and str(side["face"]) not in FACES:
            raise _bad(index, f"Side {which}: face is one of {', '.join(FACES)}", example)
        if side.get("body") and not side.get("component") and "face" not in side:
            raise _bad(index, f"Side {which}: a root body needs a face", example)
    motion = str(props.get("motion") or "rigid")
    if motion not in MOTIONS:
        raise _bad(index, f"Unknown joint motion '{motion}'", f"Motions: {', '.join(MOTIONS)}.")
    for key in ("axis", "slide"):
        if key in props and str(props[key]) not in DIRECTIONS:
            raise _bad(index, f"{key} is x, y or z", example)
    for key in ("angle", "offset"):
        if key in props and not (_number(props[key]) or isinstance(props[key], str)):
            raise _bad(index, f"{key} is a number or an expression", '"angle": 30')
    if "flip" in props and not isinstance(props["flip"], bool):
        raise _bad(index, "flip is true or false", "omit it for the default")


def _check_create(index: int, kind: str, props: dict[str, Any]) -> None:
    if kind == "sketch":
        plane = str(props.get("plane") or "XY").upper()
        if plane not in PLANES:
            raise _bad(index, f"Unknown sketch plane '{plane}'", "Use XY, XZ or YZ.")
        rects, circles = props.get("rects") or [], props.get("circles") or []
        lines, points = props.get("lines") or [], props.get("points") or []
        if not rects and not circles and not lines and not points:
            raise _bad(
                index,
                "A sketch needs geometry",
                'props: {"plane":"XY","rects":[[x1,y1,x2,y2]],"circles":[[cx,cy,r]],'
                '"lines":[[x1,y1,x2,y2]],"points":[[x,y]]} in mm',
            )
        for r in rects:
            if not _nums(r, 4):
                raise _bad(index, "A rect is [x1, y1, x2, y2] in mm", "e.g. [0, 0, 120, 80]")
            if r[0] == r[2] or r[1] == r[3]:
                raise _bad(index, "A rect needs a nonzero width and height", "e.g. [0, 0, 120, 80]")
        for c in circles:
            if not (_nums(c, 3) and c[2] > 0):
                raise _bad(index, "A circle is [cx, cy, r] in mm with r > 0", "e.g. [60, 40, 5]")
        for ln in lines:
            if not _nums(ln, 4) or (ln[0] == ln[2] and ln[1] == ln[3]):
                raise _bad(
                    index,
                    "A line is [x1, y1, x2, y2] in mm with two distinct points",
                    "e.g. [0, 0, 50, 0]",
                )
        for p in points:
            if not _nums(p, 2):
                raise _bad(index, "A point is [x, y] in mm", "e.g. [20, 20]")
        for c in props.get("constraints") or []:
            _check_constraint(index, c if isinstance(c, dict) else {}, inline=True)
        for d in props.get("dims") or []:
            _check_dimension(index, d if isinstance(d, dict) else {}, inline=True)
    elif kind == "constraint":
        _check_constraint(index, props, inline=False)
    elif kind == "dimension":
        _check_dimension(index, props, inline=False)
    elif kind == "hole":
        _check_hole(index, props)
    elif kind == "chamfer":
        distance = props.get("distance")
        if not props.get("body") or not _number(distance) or float(distance) <= 0:
            raise _bad(
                index,
                "A chamfer needs body (id) and distance (mm > 0)",
                '{"op":"create","kind":"chamfer","props":{"body":"b1","distance":1}}',
            )
        _check_edges(index, props)
    elif kind == "revolve":
        _check_revolve(index, props)
    elif kind == "joint":
        _check_joint(index, props)
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
        _check_edges(index, props)
    elif kind == "param":
        value = props.get("value")
        if not (isinstance(value, str) or _number(value)):
            raise _bad(
                index,
                'A param needs value (an expression such as "120 mm")',
                '{"op":"create","kind":"param","name":"width","props":{"value":"120 mm"}}',
            )


# -- emitters -------------------------------------------------------------------


def _p3(x: float, y: float) -> str:
    return f"adsk.core.Point3D.create({_cm(x)!r}, {_cm(y)!r}, 0.0)"


def _emit_sketch(index: int, name: str, props: dict[str, Any]) -> list[str]:
    """A sketch and its addressable geometry (doc 71 section 10.1): every
    line, circle and point is registered in the bridge's `_subs` map under a
    sketch-local address as it is created; inline constraints and dims run
    against the same map."""
    plane = PLANES[str(props.get("plane") or "XY").upper()]
    lines = [
        f"    _sk = _root.sketches.add(_root.{plane})",
        f"    _sk.name = {_lit(name)}",
        '    _sid = _mint("sk", _sk.entityToken); _mark(_sid, True)',
        '    _m = _subs.setdefault(_sid, {}); _m["origin"] = _sk.originPoint.entityToken',
    ]
    for k, (x1, y1, x2, y2) in enumerate(props.get("rects") or []):
        lines += [
            "    _ls = _sk.sketchCurves.sketchLines.addTwoPointRectangle("
            f"{_p3(x1, y1)}, {_p3(x2, y2)})",
            f'    _rect_subs(_m, "r{k}", _ls)',
        ]
    for n, (x1, y1, x2, y2) in enumerate(props.get("lines") or []):
        lines += [
            f"    _l = _sk.sketchCurves.sketchLines.addByTwoPoints({_p3(x1, y1)}, {_p3(x2, y2)})",
            f'    _m["l{n}"] = _l.entityToken; _m["l{n}.start"] = _l.startSketchPoint.entityToken',
            f'    _m["l{n}.end"] = _l.endSketchPoint.entityToken',
        ]
    for n, (cx, cy, r) in enumerate(props.get("circles") or []):
        lines += [
            f"    _c = _sk.sketchCurves.sketchCircles.addByCenterRadius({_p3(cx, cy)}, {_cm(r)!r})",
            f'    _m["c{n}"] = _c.entityToken',
            f'    _m["c{n}.center"] = _c.centerSketchPoint.entityToken',
        ]
    for n, (x, y) in enumerate(props.get("points") or []):
        lines += [
            f"    _p = _sk.sketchPoints.add({_p3(x, y)})",
            f'    _m["p{n}"] = _p.entityToken',
        ]
    for c in props.get("constraints") or []:
        lines += _constraint_lines(index, c, inline=True)
    for d in props.get("dims") or []:
        lines += _dimension_lines(index, d.get("name"), d, inline=True)
    lines.append('    _note(_sid, "sketch", _sk)')
    return lines


def _constraint_lines(index: int, props: dict[str, Any], *, inline: bool) -> list[str]:
    """Assumes `_sk` (the Sketch) and `_sid` (its id) are bound. Row 40."""
    ctype = str(props["type"])
    arity, call = CONSTRAINTS[ctype]
    _, refs = _refs(index, props, arity, inline=inline, what=f"{ctype} constraint")
    args = ", ".join(f"_sub(_sid, {_lit(r)}, {index})" for r in refs)
    return [
        f"    _gc = _sk.geometricConstraints.{call}({args})",
        f"    if _gc is None: raise _OpError({index}, 'Fusion refused the {ctype} constraint on "
        f"%s (the geometry contradicts it, or it is over-constrained)' % {_lit(' + '.join(refs))})",
    ]


def _dimension_lines(
    index: int, name: str | None, props: dict[str, Any], *, inline: bool
) -> list[str]:
    """Assumes `_sk` and `_sid` are bound. Rows 41-42: the dimension, its
    text point (given in mm, or beside the geometry), and the expression that
    binds it to a parameter."""
    dtype = str(props["type"])
    arity, call = DIMENSIONS[dtype]
    _, refs = _refs(index, props, arity, inline=inline, what=f"{dtype} dimension")
    ents = ", ".join(f"_sub(_sid, {_lit(r)}, {index})" for r in refs)
    lines = [f"    _ents = [{ents}]"]
    text = props.get("text")
    if text:
        lines.append(f"    _tp = {_p3(text[0], text[1])}")
    else:
        lines.append("    _tp = _text_for(_ents)")
    driving = bool(props.get("driving", True))
    if dtype == "distance":
        orient = ORIENTATIONS[str(props.get("orientation") or "aligned")]
        made = (
            f"_sk.sketchDimensions.addDistanceDimension(_ents[0], _ents[1], "
            f"adsk.fusion.DimensionOrientations.{orient}, _tp, {driving!r})"
        )
    elif dtype == "angle":
        made = f"_sk.sketchDimensions.addAngularDimension(_ents[0], _ents[1], _tp, {driving!r})"
    else:
        made = f"_sk.sketchDimensions.{call}(_ents[0], _tp, {driving!r})"
    lines += [
        f"    _d = {made}",
        f"    if _d is None: raise _OpError({index}, 'Fusion refused the {dtype} dimension on %s' "
        f"% {_lit(' + '.join(refs))})",
    ]
    expression = props.get("expression")
    if expression is not None:
        lines += [
            f"    if _d.parameter is None: raise _OpError({index}, 'a driven dimension has no "
            "parameter to set')",
            f"    _d.parameter.expression = {_lit(str(expression))}",
        ]
    lines.append('    _did = _mint("dim", _d.entityToken); _mark(_did, True)')
    if name:
        lines.append(f"    _names[_did] = {_lit(str(name))}")
    lines.append('    _note(_did, "dimension", _d, parent=_sid)')
    return lines


def _bind_sketch(index: int, props: dict[str, Any], arity: int, what: str) -> list[str]:
    skid, _ = _refs(index, props, arity, inline=False, what=what)
    return [
        f"    _sid = {_lit(skid)}; _sk = _find(_sid, {index})",
        f'    if _kind_of(_sk) != "sketch": raise _OpError({index}, "%r is not a sketch" % _sid)',
    ]


def _emit_constraint(index: int, props: dict[str, Any]) -> list[str]:
    ctype = str(props["type"])
    lines = _bind_sketch(index, props, CONSTRAINTS[ctype][0], f"{ctype} constraint")
    lines += _constraint_lines(index, props, inline=False)
    lines.append('    _mark(_sid, False); _note(_sid, "sketch", _sk)')
    return lines


def _emit_dimension(index: int, name: str | None, props: dict[str, Any]) -> list[str]:
    dtype = str(props["type"])
    lines = _bind_sketch(index, props, DIMENSIONS[dtype][0], f"{dtype} dimension")
    lines += _dimension_lines(index, name, props, inline=False)
    lines.append('    _mark(_sid, False); _note(_sid, "sketch", _sk)')
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
    ]
    if operation == "NewComponentFeatureOperation":
        # the occurrence Fusion made for the new component (rows 12, 50): the
        # one under the root whose component is the feature's parent
        lines += [
            "    _pc = _f.parentComponent",
            "    for _i in range(_root.occurrences.count):",
            "        _o = _root.occurrences.item(_i)",
            "        if _o.component.entityToken == _pc.entityToken:",
            '            _cid = _mint("c", _o.entityToken); _mark(_cid, True)',
            '            _note(_cid, "component", _o)',
        ]
    lines.append("    _mark_bodies(_f)")
    return lines


def _edge_feature(index: int, name: str, props: dict[str, Any], *, chamfer: bool) -> list[str]:
    """A fillet (row 11) or a chamfer (row 35) on a body's edges - all of
    them, or the edges of one face named by direction (section 10.3)."""
    body = str(props["body"])
    lines = [
        f"    _b = _find({_lit(body)}, {index})",
        f"    _edges = _edges_of(_b, {_lit(props.get('edges', 'all'))}, {index})",
    ]
    if chamfer:
        value = _mm_expr(float(props["distance"]))
        lines += [
            "    _inp = _root.features.chamferFeatures.createInput2()",
            "    _inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(_edges, "
            f"adsk.core.ValueInput.createByString({_lit(value)}), True)",
            "    _f = _root.features.chamferFeatures.add(_inp)",
            f"    if _f is None: raise _OpError({index}, 'chamfer failed: Fusion returned null')",
        ]
    else:
        value = _mm_expr(float(props["radius"]))
        lines += [
            "    _inp = _root.features.filletFeatures.createInput()",
            "    _inp.edgeSetInputs.addConstantRadiusEdgeSet(_edges, "
            f"adsk.core.ValueInput.createByString({_lit(value)}), True)",
            "    _f = _root.features.filletFeatures.add(_inp)",
            f"    if _f is None: raise _OpError({index}, 'fillet failed: Fusion returned null')",
        ]
    lines += [
        f"    _f.name = {_lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
        '    details[_fid]["edges"] = _edges.count',
        '    _bid = _mint("b", _b.entityToken); _mark(_bid, False); _note(_bid, "body", _b)',
        "    _mark_bodies(_f)",
    ]
    return lines


def _emit_fillet(index: int, name: str, props: dict[str, Any]) -> list[str]:
    return _edge_feature(index, name, props, chamfer=False)


def _emit_chamfer(index: int, name: str, props: dict[str, Any]) -> list[str]:
    return _edge_feature(index, name, props, chamfer=True)


def _emit_hole(index: int, name: str, props: dict[str, Any]) -> list[str]:
    """Rows 31-34: the input for the hole type, its placement (a face and a
    point Fusion projects, or a sketch point), its extent and direction."""
    htype = str(props.get("type") or "simple")
    d = _lit(_mm_expr(float(props["diameter"])))
    if htype == "counterbore":
        cb_d = _lit(_mm_expr(float(props["cbore_diameter"])))
        cb_depth = _lit(_mm_expr(float(props["cbore_depth"])))
        made = (
            "_root.features.holeFeatures.createCounterboreInput("
            f"adsk.core.ValueInput.createByString({d}), "
            f"adsk.core.ValueInput.createByString({cb_d}), "
            f"adsk.core.ValueInput.createByString({cb_depth}))"
        )
    elif htype == "countersink":
        cs_d = _lit(_mm_expr(float(props["csink_diameter"])))
        cs_angle = _lit(f"{float(props.get('csink_angle', 90)):g} deg")
        made = (
            "_root.features.holeFeatures.createCountersinkInput("
            f"adsk.core.ValueInput.createByString({d}), "
            f"adsk.core.ValueInput.createByString({cs_d}), "
            f"adsk.core.ValueInput.createByString({cs_angle}))"
        )
    else:
        made = (
            "_root.features.holeFeatures.createSimpleInput("
            f"adsk.core.ValueInput.createByString({d}))"
        )
    lines = [f"    _inp = {made}"]
    if "point" in props:
        skid, ref = _split_address(index, props["point"], _POINT_ADDRESS, "A hole point")
        lines += [
            f"    _spt = _sub({_lit(skid)}, {_lit(ref)}, {index})",
            "    _inp.setPositionBySketchPoint(_spt)",
        ]
    else:
        face = str(props["face"])
        at = [_cm(v) for v in props["at"]]
        lines += [
            f"    _b = _find({_lit(str(props['body']))}, {index})",
            f"    _fc = _face(_b, {_lit(face)}, {_lit(at if len(at) == 3 else None)}, {index})",
            f"    _inp.setPositionByPoint(_fc, _at_point(_fc, {_lit(face)}, {_lit(at)}))",
        ]
    if props.get("through"):
        lines.append("    _inp.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)")
    else:
        depth = _lit(_mm_expr(float(props["depth"])))
        lines.append(f"    _inp.setDistanceExtent(adsk.core.ValueInput.createByString({depth}))")
    if props.get("flip"):
        lines.append("    _inp.isDefaultDirection = False")
    lines += [
        "    _f = _root.features.holeFeatures.add(_inp)",
        f"    if _f is None: raise _OpError({index}, 'hole failed: Fusion returned null (is the "
        "point on the face, and the extent inside a body?)')",
        f"    _f.name = {_lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
        "    _mark_bodies(_f)",
    ]
    return lines


def _emit_joint(index: int, name: str, props: dict[str, Any]) -> list[str]:
    """Rows 43-46: geometry per side, the motion's setter, angle / offset
    with their units written, the flip, then `joints.add`."""
    motion = str(props.get("motion") or "rigid")
    setter, wants = MOTIONS[motion]
    axis = DIRECTIONS[str(props.get("axis") or "z")]
    slide = DIRECTIONS[str(props.get("slide") or "x")]
    picks = {
        "axis": axis,
        "slide": slide,
        "pitch": "ZAxisJointDirection",
        "yaw": "XAxisJointDirection",
    }
    args = ", ".join(f"adsk.fusion.JointDirections.{picks[w]}" for w in wants)
    lines = [
        f"    _g1 = _joint_geom({_lit(dict(props['one']))}, {index})",
        f"    _g2 = _joint_geom({_lit(dict(props['two']))}, {index})",
        f"    if _g1 is None or _g2 is None: raise _OpError({index}, 'joint geometry could not be "
        "built: a planar face with a centre, or an origin point')",
        "    _inp = _root.joints.createInput(_g1, _g2)",
        f"    _inp.{setter}({args})",
    ]
    for key, unit in (("angle", "deg"), ("offset", "mm")):
        if key in props:
            value = props[key]
            expr = value if isinstance(value, str) else f"{float(value):g} {unit}"
            lines.append(f"    _inp.{key} = adsk.core.ValueInput.createByString({_lit(expr)})")
    if props.get("flip"):
        lines.append("    _inp.isFlipped = True")
    lines += [
        "    _j = _root.joints.add(_inp)",
        f"    if _j is None: raise _OpError({index}, 'joint failed: Fusion returned null (are the "
        "two sides in different components?)')",
        f"    _j.name = {_lit(name)}",
        '    _jid = _mint("j", _j.entityToken); _mark(_jid, True); _note(_jid, "joint", _j)',
    ]
    return lines


def _profile_lines(index: int, sketch: str, profile: Any) -> list[str]:
    """`_sk` bound to the sketch and `_prof` to its profile(s) - shared by
    extrude and revolve."""
    lines = [
        f"    _sk = _find({_lit(sketch)}, {index})",
        "    if _sk.profiles.count == 0:",
        f"        raise _OpError({index}, 'sketch %r has no closed profile' % {_lit(sketch)})",
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
    return lines


def _emit_revolve(index: int, name: str, props: dict[str, Any]) -> list[str]:
    """Row 36: a revolve about a root construction axis (row 37) or a sketch
    line, through an angle written in degrees."""
    sketch = str(props["sketch"])
    operation = OPERATIONS[str(props.get("operation") or "new_body")]
    angle = _lit(f"{float(props.get('angle', 360)):g} deg")
    lines = _profile_lines(index, sketch, props.get("profile", "all"))
    axis = props["axis"]
    if axis in AXES:
        lines.append(f"    _ax = _root.{AXES[axis]}")
    else:
        skid, ref = _split_address(index, axis, _LINE_ADDRESS, "A revolve axis")
        lines.append(f"    _ax = _sub({_lit(skid)}, {_lit(ref)}, {index})")
    lines += [
        "    _inp = _root.features.revolveFeatures.createInput("
        f"_prof, _ax, adsk.fusion.FeatureOperations.{operation})",
        f"    _inp.setAngleExtent({bool(props.get('symmetric', False))!r}, "
        f"adsk.core.ValueInput.createByString({angle}))",
        "    _f = _root.features.revolveFeatures.add(_inp)",
        f"    if _f is None: raise _OpError({index}, 'revolve failed: Fusion returned null (does "
        "the profile cross its axis, or the axis leave the sketch plane?)')",
        f"    _f.name = {_lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
        "    _mark_bodies(_f)",
    ]
    return lines


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
    if kind == "constraint":
        return _emit_constraint(index, props)
    if kind == "dimension":
        return _emit_dimension(index, op.get("name"), props)
    if kind == "extrude":
        return _emit_extrude(index, name, props)
    if kind == "fillet":
        return _emit_fillet(index, name, props)
    if kind == "hole":
        return _emit_hole(index, name, props)
    if kind == "chamfer":
        return _emit_chamfer(index, name, props)
    if kind == "revolve":
        return _emit_revolve(index, name, props)
    if kind == "joint":
        return _emit_joint(index, name, props)
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
                '    elif _k == "dimension":',
                f"        if _e.parameter is None: raise _OpError({index}, 'a driven dimension has "
                "no parameter to set')",
                f"        _e.parameter.expression = {_lit(str(value))}",
                f'    elif _k == "feature" and hasattr(_e, "extentOne"): '
                f"_e.extentOne.distance.expression = {_lit(str(value))}",
                f'    elif _k == "feature" and hasattr(_e, "holeDiameter"): '
                f"_e.holeDiameter.expression = {_lit(str(value))}",
                f"    else: raise _OpError({index}, 'only user parameters, dimensions, extrudes "
                "and holes take an expression')",
            ]
        elif key == "suppressed":
            lines += [
                f'    if _k not in ("feature", "joint"): raise _OpError({index}, '
                '"only a feature or a joint can be suppressed")',
                f"    _e.isSuppressed = {bool(value)!r}",
            ]
        elif key in ("angle", "offset"):  # row 46: the joint's own parameters
            unit = "deg" if key == "angle" else "mm"
            expr = value if isinstance(value, str) else f"{float(value):g} {unit}"
            lines += [
                f'    if _k != "joint": raise _OpError({index}, "only a joint takes {key}")',
                f"    _e.{key}.expression = {_lit(expr)}",
            ]
        elif key == "flipped":
            lines += [
                f'    if _k != "joint": raise _OpError({index}, "only a joint takes flipped")',
                f"    _e.isFlipped = {bool(value)!r}",
            ]
        elif key == "rotation":  # RevoluteJointMotion.rotationValue, radians (row 46)
            lines += [
                f'    if _k != "joint" or not hasattr(_e.jointMotion, "rotationValue"): '
                f'raise _OpError({index}, "rotation drives a revolute, cylindrical or pin-slot '
                'joint")',
                f"    _e.jointMotion.rotationValue = {float(value) * 3.141592653589793 / 180.0!r}",
            ]
        elif key == "slide":  # SliderJointMotion.slideValue, centimetres (row 46)
            lines += [
                f'    if _k != "joint" or not hasattr(_e.jointMotion, "slideValue"): '
                f'raise _OpError({index}, "slide drives a slider, cylindrical or pin-slot joint")',
                f"    _e.jointMotion.slideValue = {_cm(float(value))!r}",
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
        row = {"id": sid, "name": _names.get(sid) or _name_of(kind, ent),
               "kind": _kinds.get(sid, kind)}
        if parent: row["parent"] = parent
        rows.append([row, _summary(kind, ent)]); return sid
    def _sketch_rows(sk, parent=None):
        sid = _emit("sketch", sk, parent)
        for _j in range(sk.sketchDimensions.count):
            _emit("dimension", sk.sketchDimensions.item(_j), sid)
    for _i in range(_root.sketches.count): _sketch_rows(_root.sketches.item(_i))
    for _i in range(_root.features.count): _emit("feature", _root.features.item(_i))
    for _i in range(_root.bRepBodies.count): _emit("body", _root.bRepBodies.item(_i))
    for _i in range(_root.occurrences.count):
        _occ = _root.occurrences.item(_i); _cid = _emit("component", _occ); _comp = _occ.component
        for _j in range(_comp.bRepBodies.count): _emit("body", _comp.bRepBodies.item(_j), _cid)
        for _j in range(_comp.sketches.count): _sketch_rows(_comp.sketches.item(_j), _cid)
    for _i in range(_root.joints.count): _emit("joint", _root.joints.item(_i))
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
