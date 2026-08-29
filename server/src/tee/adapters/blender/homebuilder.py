"""Home Builder joinery lane (A37 P5.1): hb_* virtual tools.

Drives Home Builder 5.1's OWN programmatic layer (GeoNodeWall, the
frameless cabinet types, CABINET_PART cut-parts, layout views) through
the EXISTING Blender adapter's bridge - no new adapter, one script per
tool call, `result` dict back (the bridge contract). Units: the lane
speaks millimetres end to end; Blender/HB store meters.

Honesty rules: every tool probes for the extension and refuses with the
install fix when absent; the cut list is read FROM the model's geometry-
node inputs (never re-derived); layouts are HB's own dimensioned scenes
rendered to files. HB models no 32 mm system holes in 5.1.0 - the cut
list says so rather than inventing them (joinery_check's missing-data
rule rides on that honesty).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

HB_MODULE = "bl_ext.blender_org.home_builder_5"
INSTALL_FIX = (
    "Install/enable Home Builder 5.1 from extensions.blender.org "
    "(add-on id home_builder_5) in the served Blender, then retry."
)

_PROBE = f"""
import importlib
try:
    hb = importlib.import_module("{HB_MODULE}")
    result = {{"ok": True}}
except Exception as exc:
    result = {{"ok": False, "why": str(exc)[:120]}}
"""

# Blender 5.2 moved NodesModifier input writes from `mod[identifier] = v`
# (IDProperties) to `mod.properties.inputs.<identifier>.value` - HB 5.1.0's
# own set_input/get_input still use the removed idiom and raise
# "id properties not supported for this type" (found live 2026-08-29 by
# this lane's first run). This shim patches HB's two accessor owners for
# the session, old-idiom-first so it stays correct on older Blenders.
# Candidate upstream patch for HB; recorded in PROGRESS.
_COMPAT = f"""
import importlib
hb_types = importlib.import_module("{HB_MODULE}.hb_types")
if not getattr(hb_types, "_tee_52_compat", False):
    def _write(mod, input_name, value):
        ident = mod.node_group.interface.items_tree[input_name].identifier
        try:
            mod[ident] = value
        except TypeError:
            getattr(mod.properties.inputs, ident).value = value
    def _read(mod, input_name):
        ident = mod.node_group.interface.items_tree[input_name].identifier
        try:
            return mod[ident]
        except TypeError:
            return getattr(mod.properties.inputs, ident).value
    def _obj_set(self, input_name, value):
        _write(self.obj.modifiers[self.obj.home_builder.mod_name], input_name, value)
    def _obj_get(self, input_name):
        return _read(self.obj.modifiers[self.obj.home_builder.mod_name], input_name)
    def _cpm_set(self, input_name, value):
        _write(self.mod, input_name, value)
    def _cpm_get(self, input_name):
        return _read(self.mod, input_name)
    def _path(mod, input_name):
        ident = mod.node_group.interface.items_tree[input_name].identifier
        try:
            mod[ident]
            return 'modifiers["' + mod.name + '"]["' + ident + '"]'
        except TypeError:
            return 'modifiers["' + mod.name + '"].properties.inputs.' + ident + '.value'
    hb_utils = importlib.import_module("{HB_MODULE}.hb_utils")
    def _obj_var_input(self, input_name, name):
        mod = self.obj.modifiers[self.obj.home_builder.mod_name]
        return hb_types.Variable(self.obj.id_data, _path(mod, input_name), name)
    def _obj_driver_input(self, input_name, expression, variables=[]):
        mod = self.obj.modifiers[self.obj.home_builder.mod_name]
        driver = self.obj.driver_add(_path(mod, input_name))
        hb_utils.add_driver_variables(driver, variables)
        driver.driver.expression = expression
    def _cpm_driver_input(self, input_name, expression, variables=[]):
        driver = self.obj.driver_add(_path(self.mod, input_name))
        hb_utils.add_driver_variables(driver, variables)
        driver.driver.expression = expression
    hb_types.GeoNodeObject.set_input = _obj_set
    hb_types.GeoNodeObject.get_input = _obj_get
    hb_types.GeoNodeObject.var_input = _obj_var_input
    hb_types.GeoNodeObject.driver_input = _obj_driver_input
    hb_types.CabinetPartModifier.set_input = _cpm_set
    hb_types.CabinetPartModifier.get_input = _cpm_get
    hb_types.CabinetPartModifier.driver_input = _cpm_driver_input
    hb_types._tee_52_compat = True
result = {{"ok": True}}
"""

_ROOM = """
import importlib, math
hb_types = importlib.import_module("{hb}.hb_types")
walls_spec = {walls!r}
height = {height_m!r}
thickness = {thickness_m!r}
prev = None
heading = 0.0
made = []
x = y = 0.0
for spec in walls_spec:
    heading += math.radians(spec.get("angle_deg", 0.0))
    wall = hb_types.GeoNodeWall()
    wall.create("Wall")
    wall.set_input("Length", spec["length_m"])
    wall.set_input("Height", height)
    wall.set_input("Thickness", thickness)
    wall.obj.rotation_euler = (0.0, 0.0, heading)
    if prev is None:
        wall.obj.location = (0.0, 0.0, 0.0)
    else:
        wall.obj.location = prev.obj.matrix_world @ prev.obj_x.location
        wall.connect_to_wall(prev)
    prev = wall
    made.append(wall.obj.name)
import bpy
bpy.context.view_layer.update()
result = {{"walls": made}}
"""

_CABINET = """
import importlib
tf = importlib.import_module("{hb}.product_libraries.frameless.types_frameless")
import bpy
kinds = {{"tall": tf.TallCabinet, "base": tf.BaseCabinet, "upper": tf.UpperCabinet}}
cab = kinds[{kind!r}]()
cab.width = {width_m!r}
cab.height = {height_m!r}
cab.depth = {depth_m!r}
cab.create({name!r})
wall_name = {wall!r}
if wall_name:
    wall_obj = bpy.data.objects.get(wall_name)
    if wall_obj is None:
        raise RuntimeError("no wall %r" % wall_name)
    cab.obj.parent = wall_obj
    cab.obj.location = ({offset_m!r}, 0.0, 0.0)
    cab.obj.rotation_euler = (0.0, 0.0, 0.0)
bpy.context.view_layer.update()
parts = [o.name for o in cab.obj.children_recursive if o.get("CABINET_PART")]
result = {{"cabinet": cab.obj.name, "parts": len(parts)}}
"""

_CUTLIST = """
import importlib
hb_types = importlib.import_module("{hb}.hb_types")
import bpy
product = {product!r}
if product:
    root = bpy.data.objects.get(product)
    if root is None:
        raise RuntimeError("no product %r" % product)
    pool = [o for o in root.children_recursive if o.get("CABINET_PART")]
else:
    pool = [o for o in bpy.data.objects if o.get("CABINET_PART")]
rows = {{}}
for obj in pool:
    part = hb_types.GeoNodeCutpart(obj)
    try:
        length = float(part.get_input("Length"))
        width = float(part.get_input("Width"))
        thickness = float(part.get_input("Thickness"))
    except Exception:
        continue
    root_name = obj.name
    parent = obj.parent
    while parent is not None:
        if parent.get("IS_FRAMELESS_CABINET_CAGE"):
            root_name = parent.name
            break
        parent = parent.parent
    base = obj.name.split(".")[0]
    key = (base, root_name, round(length, 4), round(width, 4), round(thickness, 4))
    rows[key] = rows.get(key, 0) + 1
result = {{
    "rows": [
        [k[0], k[1], round(k[2] * 1000, 1), round(k[3] * 1000, 1),
         round(k[4] * 1000, 1), qty]
        for k, qty in sorted(rows.items())
    ],
    "parts": sum(rows.values()),
}}
"""

_LAYOUT = """
import importlib
hb_layouts = importlib.import_module("{hb}.hb_layouts")
layout_ops = importlib.import_module("{hb}.operators.layouts")
import bpy
out_dir = {out_dir!r}
resolution = {resolution!r}
files = []
made = []
def render(scene, stem):
    # HB configures the layout scene (engine, Freestyle linework, paper
    # size, title block) - honor it; only scale the output resolution.
    layout_ops.apply_default_layout_settings(scene)
    if resolution:
        aspect = scene.render.resolution_y / max(1, scene.render.resolution_x)
        scene.render.resolution_x = resolution
        scene.render.resolution_y = int(resolution * aspect)
    scene.render.filepath = out_dir + "/" + stem + ".png"
    bpy.ops.render.render(write_still=True, scene=scene.name)
    files.append(scene.render.filepath)
if {plan!r}:
    view = hb_layouts.PlanView()
    scene = view.create()
    made.append(scene.name)
    render(scene, "plan")
if {elevations!r}:
    views = hb_layouts.create_all_elevations()
    for i, view in enumerate(views):
        made.append(view.scene.name)
        render(view.scene, "elevation_%d" % i)
result = {{"scenes": made, "files": files}}
"""


_SPEC = """
import importlib, bpy
hb_types = importlib.import_module("{hb}.hb_types")
cabinets, parts = [], []
for o in bpy.data.objects:
    if o.get("IS_FRAMELESS_CABINET_CAGE"):
        g = hb_types.GeoNodeObject(o)
        row = {{"id": o.name, "kind": str(o.get("CABINET_TYPE", "")).lower() or "cabinet"}}
        for inp, key in (("Dim X", "width_mm"), ("Dim Y", "depth_mm"), ("Dim Z", "height_mm")):
            try:
                row[key] = round(abs(float(g.get_input(inp))) * 1000, 1)
            except Exception:
                pass
        cabinets.append(row)
for o in bpy.data.objects:
    if o.get("CABINET_PART"):
        part = hb_types.GeoNodeCutpart(o)
        try:
            L = float(part.get_input("Length"))
            W = float(part.get_input("Width"))
            T = float(part.get_input("Thickness"))
        except Exception:
            continue
        cab = None
        p = o.parent
        while p is not None:
            if p.get("IS_FRAMELESS_CABINET_CAGE"):
                cab = p.name
                break
            p = p.parent
        base = o.name.split(".")[0].lower()
        if "door" in base or "front" in base:
            role = "door"
        else:
            role = "shelf" if "shelf" in base else base
        parts.append({{"id": o.name, "cabinet": cab, "role": role,
                      "length_mm": round(L * 1000, 1), "width_mm": round(W * 1000, 1),
                      "thickness_mm": round(T * 1000, 1)}})
result = {{"spec": {{"cabinets": cabinets, "parts": parts, "hardware": []}},
           "note": "HB 5.1 models pulls only - hinges/runners/system holes are "
                   "absent, so those joinery_check rules answer not_evaluated"}}
"""


def _mm(args: dict[str, Any], key: str, default: float | None = None) -> float:
    raw = args.get(key, default)
    if raw is None:
        raise TeeError("bad_op", f"{key} is required.", fix=f"Give {key} in millimetres.")
    return float(raw) / 1000.0


def register_hb_tools(app, adapter) -> None:
    """Attach the hb_* lane over an existing Blender adapter."""
    state = {"probed": None}

    def _run(code: str, *, timeout: float | None = None) -> dict[str, Any]:
        response = adapter.wire.execute(code, timeout=timeout)
        if response.get("status") != "ok":
            message = str(response.get("message") or "bridge error")
            if HB_MODULE in message and (
                "ModuleNotFoundError" in message or "ImportError" in message
            ):
                raise TeeError("hb_missing", "Home Builder is not available.", fix=INSTALL_FIX)
            raise TeeError(
                "hb_failed",
                f"Home Builder op failed: {message.splitlines()[-1][:250]}",
                fix="The line above is Blender's own; fix what it names and retry.",
            )
        return response.get("result") or {}

    def _ensure_hb() -> None:
        if state["probed"] is None:
            state["probed"] = bool(_run(_PROBE).get("ok"))
            if state["probed"]:
                _run(_COMPAT)  # the Blender-5.2 input-write shim, once
        if not state["probed"]:
            raise TeeError("hb_missing", "Home Builder is not available.", fix=INSTALL_FIX)

    def hb_status(args: dict[str, Any]) -> dict[str, Any]:
        probe = _run(_PROBE)
        return {
            "installed": bool(probe.get("ok")),
            **({} if probe.get("ok") else {"why": probe.get("why"), "fix": INSTALL_FIX}),
            "units": "the hb_* lane speaks millimetres end to end",
            "note": "HB 5.1 models no 32 mm system holes; hb_cutlist reports "
            "dimensions only and says so",
        }

    def hb_room(args: dict[str, Any]) -> dict[str, Any]:
        _ensure_hb()
        walls_arg = args.get("walls") or []
        if not walls_arg:
            raise TeeError(
                "bad_op",
                "hb_room needs walls.",
                fix='Give {"walls": [{"length_mm": 3000}, {"length_mm": 2000, "angle_deg": -90}]}.',
            )
        walls = [
            {
                "length_m": float(w.get("length_mm", 0)) / 1000.0,
                "angle_deg": float(w.get("angle_deg", 0.0)),
            }
            for w in walls_arg
        ]
        if any(w["length_m"] <= 0 for w in walls):
            raise TeeError("bad_op", "Every wall needs length_mm > 0.", fix="Check the list.")
        out = _run(
            _ROOM.format(
                hb=HB_MODULE,
                walls=walls,
                height_m=_mm(args, "height_mm", 2438.0),
                thickness_m=_mm(args, "thickness_mm", 114.0),
            )
        )
        return {"ok": True, **out}

    def hb_cabinet(args: dict[str, Any]) -> dict[str, Any]:
        _ensure_hb()
        kind = str(args.get("type") or "tall").lower()
        if kind not in ("tall", "base", "upper"):
            raise TeeError(
                "bad_op", f"Unknown cabinet type '{kind}'.", fix="Types: tall, base, upper."
            )
        out = _run(
            _CABINET.format(
                hb=HB_MODULE,
                kind=kind,
                width_m=_mm(args, "width_mm", 1000.0),
                height_m=_mm(args, "height_mm", 2200.0 if kind == "tall" else 870.0),
                depth_m=_mm(args, "depth_mm", 600.0 if kind != "upper" else 320.0),
                name=str(args.get("name") or f"{kind}_cabinet"),
                wall=str(args.get("wall") or ""),
                offset_m=_mm(args, "offset_mm", 0.0),
            )
        )
        return {"ok": True, **out}

    def hb_cutlist(args: dict[str, Any]) -> dict[str, Any]:
        _ensure_hb()
        out = _run(_CUTLIST.format(hb=HB_MODULE, product=str(args.get("product") or "")))
        payload: dict[str, Any] = {
            "cols": ["part", "product", "length_mm", "width_mm", "thickness_mm", "qty"],
            "rows": out.get("rows", []),
            "parts": out.get("parts", 0),
            "note": "dimensions read from the parts' geometry-node inputs; "
            "HB 5.1 models no 32 mm system holes (none reported)",
        }
        csv_path = args.get("csv")
        if csv_path:
            path = Path(str(csv_path))
            path.parent.mkdir(parents=True, exist_ok=True)
            lines = [",".join(payload["cols"])]
            lines += [",".join(str(v) for v in row) for row in payload["rows"]]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            payload["csv"] = str(path)
        return payload

    def hb_layout(args: dict[str, Any]) -> dict[str, Any]:
        _ensure_hb()
        out_dir = Path(str(args.get("out_dir") or (app.project_root / ".tee" / "hb-layouts")))
        out_dir.mkdir(parents=True, exist_ok=True)
        views = [str(v) for v in (args.get("views") or ["plan", "elevations"])]
        bad = [v for v in views if v not in ("plan", "elevations")]
        if bad:
            raise TeeError(
                "bad_op",
                f"Unknown layout view(s): {', '.join(bad)}.",
                fix="Views: plan, elevations.",
            )
        out = _run(
            _LAYOUT.format(
                hb=HB_MODULE,
                out_dir=str(out_dir),
                resolution=int(args.get("resolution") or 1600),
                plan="plan" in views,
                elevations="elevations" in views,
            ),
            timeout=300.0,  # layout scenes render
        )
        return {
            "ok": True,
            **out,
            "note": "HB's own dimensioned layout scenes, rendered to files "
            "(read them budgeted via tee_media)",
        }

    def hb_joinery_spec(args: dict[str, Any]) -> dict[str, Any]:
        _ensure_hb()
        return _run(_SPEC.format(hb=HB_MODULE))

    for tool in [
        VirtualTool(
            "hb_status",
            "Home Builder lane health: is the extension available in the "
            "served Blender, plus the lane's unit and data-honesty notes.",
            {"type": "object", "properties": {}},
            hb_status,
            tags=["homebuilder", "joinery", "status", "closet", "cabinet"],
        ),
        VirtualTool(
            "hb_room",
            "Create a connected run of Home Builder walls (mm; angle_deg "
            "turns each wall relative to the previous). The room every "
            "closet run starts with.",
            {
                "type": "object",
                "properties": {
                    "walls": {"type": "array", "items": {"type": "object"}},
                    "height_mm": {"type": "number"},
                    "thickness_mm": {"type": "number"},
                },
                "required": ["walls"],
            },
            hb_room,
            tags=["homebuilder", "wall", "room", "joinery"],
            examples=[{"walls": [{"length_mm": 3000}, {"length_mm": 2000, "angle_deg": -90}]}],
        ),
        VirtualTool(
            "hb_cabinet",
            "Place a Home Builder frameless cabinet (type tall/base/upper - "
            "tall is the wardrobe class) with mm dimensions, optionally "
            "parented onto a wall at offset_mm. Answers the cabinet id and "
            "its cut-part count.",
            {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "width_mm": {"type": "number"},
                    "height_mm": {"type": "number"},
                    "depth_mm": {"type": "number"},
                    "wall": {"type": "string"},
                    "offset_mm": {"type": "number"},
                    "name": {"type": "string"},
                },
            },
            hb_cabinet,
            tags=["homebuilder", "cabinet", "closet", "wardrobe", "joinery", "frameless"],
            examples=[{"type": "tall", "width_mm": 1200, "height_mm": 2200, "depth_mm": 600}],
        ),
        VirtualTool(
            "hb_joinery_spec",
            "Collect a joinery_check spec from the live Home Builder scene: "
            "cabinets (mm envelopes) + cut parts with roles, read from the "
            "model's own geometry-node inputs. HB models no hinges/runners/"
            "system holes - the response says so, and joinery_check answers "
            "not_evaluated on those rules instead of passing them.",
            {"type": "object", "properties": {}},
            hb_joinery_spec,
            tags=["homebuilder", "joinery", "spec", "check", "collect"],
        ),
        VirtualTool(
            "hb_cutlist",
            "The cut-part report: every CABINET_PART's length/width/thickness "
            "(mm) read from its geometry-node inputs, grouped with "
            "quantities - columnar rows plus optional csv file-out. The "
            "fabricator's list, from the model, never re-derived.",
            {
                "type": "object",
                "properties": {
                    "product": {"type": "string"},
                    "csv": {"type": "string"},
                },
            },
            hb_cutlist,
            tags=["homebuilder", "cutlist", "cut", "parts", "fabrication", "csv", "joinery"],
        ),
        VirtualTool(
            "hb_layout",
            "Render Home Builder's OWN dimensioned 2D layout scenes - plan "
            "and per-wall elevations - to PNG files (out_dir, resolution). "
            "The layouts carry HB's dimensions; read results budgeted via "
            "tee_media.",
            {
                "type": "object",
                "properties": {
                    "views": {"type": "array", "items": {"type": "string"}},
                    "out_dir": {"type": "string"},
                    "resolution": {"type": "integer"},
                },
            },
            hb_layout,
            tags=["homebuilder", "layout", "plan", "elevation", "drawing", "joinery"],
        ),
    ]:
        app.registry.register(tool)
