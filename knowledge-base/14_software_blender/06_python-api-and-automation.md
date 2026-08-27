---
id: blender.python_api
title: The Blender Python API and automation
domain: software_blender
tags: [blender, bpy, python, bmesh, mathutils, automation, headless, background, addon, extension, mcp, cutting-list, batch-render]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; scripts are 4.5-LTS compatible unless noted"
unit_system: metric
sources:
  - {title: "Blender Python API — Operators (bpy.ops) and context overriding", url: "https://docs.blender.org/api/current/bpy.ops.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — Context.temp_override", url: "https://docs.blender.org/api/current/bpy.types.Context.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — Gotchas: Operators", url: "https://docs.blender.org/api/current/info_gotchas_operators.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — Mesh.from_pydata", url: "https://docs.blender.org/api/current/bpy.types.Mesh.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — bmesh.ops", url: "https://docs.blender.org/api/current/bmesh.ops.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — NodeTreeInterface", url: "https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Command Line Arguments", url: "https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — How to Create Extensions", url: "https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "BlenderMCP (ahujasid/blender-mcp)", url: "https://github.com/ahujasid/blender-mcp", publisher: "Siddharth Ahuja", accessed: 2026-08-25}
related: [blender.interface_core_concepts, blender.geometry_nodes, blender.import_export]
---

# The Blender Python API and automation

**Summary.** `bpy` is a full binding to Blender's internals. Anything the UI can do, Python can do — usually better, because Python can address data directly instead of going through the operator layer that the UI is built on. This file is the operating manual for driving Blender from an agent: the four sub-modules that matter, why operators are the wrong default, how to build geometry from raw coordinates, how to add modifiers and materials without touching the selection, how to run headless, how to package an extension, and four complete scripts that build a wall, build a wardrobe, batch-render a camera set and export a cutting list.

## Key facts

| Item | Value |
|---|---|
| `bpy.data` | The file's datablock database. Read/write, context-free, works in background mode. **Prefer this.** |
| `bpy.context` | The current UI state: active object, selection, mode, scene, view layer. Mostly read-only, mostly absent in `-b`. |
| `bpy.ops` | Operators — recorded user actions. Context-dependent, slow, push undo steps. |
| `bpy.types` | RNA class definitions; the base classes you subclass for panels, operators and property groups. |
| Other modules | `bmesh`, `mathutils`, `bpy_extras`, `bl_math`, `gpu`, `blf`, `imbuf`, `idprop` |
| Context override | `with bpy.context.temp_override(**kwargs): bpy.ops.…` (the `bpy.ops.foo(override_dict, …)` form was removed in 3.2) |
| Mesh from data | `mesh.from_pydata(vertices, edges, faces, shade_flat=True)` then `mesh.validate()` |
| Evaluated geometry | `deps = bpy.context.evaluated_depsgraph_get()`; `obj.evaluated_get(deps).to_mesh()`; `to_mesh_clear()` |
| Headless run | `blender -b file.blend -P script.py -- arg1 arg2` |
| Expression run | `blender -b --python-expr "import bpy; print(len(bpy.data.objects))"` |
| Exit on error | `--python-exit-code 1` |
| Clean environment | `--factory-startup` (ignore user prefs and add-ons), `--addons name1,name2` to enable specific ones |
| Extension manifest | `blender_manifest.toml` with `schema_version`, `id`, `version`, `name`, `tagline`, `maintainer`, `type`, `blender_version_min` (≥ 4.2.0), `license` (SPDX) |
| Build an extension | `blender --command extension build --source-dir . --output-dir dist` |
| Validate | `blender --command extension validate .` |
| BlenderMCP default port | 9876 (`BLENDER_HOST` / `BLENDER_PORT` env vars) |

## `bpy.data` vs `bpy.context` vs `bpy.ops`

### Why operators are the wrong default

`bpy.ops.mesh.primitive_cube_add()` looks like an API call. It is not; it is the same code path the *Add ▸ Mesh ▸ Cube* menu item runs. That means it:

- reads `bpy.context` for the active scene, collection, 3D cursor and mode, and fails or misbehaves if any of those are not what it expects;
- has a `poll()` function that can refuse to run, producing `RuntimeError: Operator … .poll() failed, context is incorrect`;
- pushes an undo step and triggers a full dependency-graph re-evaluation and UI redraw on every call;
- in background mode (`-b`) has no window, no area and no region, so any operator that needs one simply cannot run.

The API's own gotchas page is blunt: when an operator's poll fails, the only reliable way to find out why is to read its poll function; certain operators exist only for a specific editor context.

Concretely, adding 500 objects with `bpy.ops.mesh.primitive_cube_add()` takes seconds to minutes and can blow up; adding 500 objects with `bpy.data.meshes.new()` + `bpy.data.objects.new()` + `collection.objects.link()` takes milliseconds and cannot fail on context.

### When operators are the right tool

Some things have no data-level equivalent and you should use the operator, ideally once, on a prepared context:

- Import and export (`bpy.ops.wm.obj_import`, `bpy.ops.wm.usd_export`, `bpy.ops.export_scene.gltf`, …).
- UV unwrapping (`bpy.ops.uv.smart_project`, `bpy.ops.uv.cube_project`).
- Rendering (`bpy.ops.render.render(write_still=True)`).
- Some edit-mode operations where writing the bmesh equivalent is not worth it.
- `bpy.ops.object.transform_apply()`, `bpy.ops.object.convert()`, `bpy.ops.object.modifier_apply()`.

### Context overrides

When you must call an operator on specific data rather than on "whatever is selected", override the context:

```python
import bpy

obj = bpy.data.objects["Wall_01"]

with bpy.context.temp_override(object=obj, active_object=obj,
                               selected_objects=[obj],
                               selected_editable_objects=[obj]):
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
```

Rules from the API documentation:

- Overrides are passed as keyword arguments whose names match `bpy.context` member names.
- `window`, `area` and `region` must be mutually consistent — a region must belong to the area, the area to the window.
- Overrides nest; members are restored when the `with` block exits.
- Switching to or away from full-screen or temporary screens is not supported.
- If you cannot work out which member an operator needs, call `logging_set(True)` on the `with` target to log every context member the operator accesses:

```python
with bpy.context.temp_override(object=obj) as ctx:
    ctx.logging_set(True)
    bpy.ops.object.some_operator()
```

To find a 3D viewport to override with (needed for viewport-only operators, and only meaningful when a UI exists):

```python
def first_view3d():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                region = next(r for r in area.regions if r.type == 'WINDOW')
                return dict(window=window, area=area, region=region)
    return {}
```

## Creating geometry from data

### `from_pydata` — the simple route

```python
import bpy

def make_box(name, size, location=(0, 0, 0), collection=None):
    """Axis-aligned box with its origin at the min corner. size = (x, y, z) in metres."""
    sx, sy, sz = size
    verts = [(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0),
             (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7),
             (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)     # edges inferred from faces when [] is passed
    me.validate()                        # ALWAYS, if the data is not provably clean
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    (collection or bpy.context.scene.collection).objects.link(ob)
    return ob
```

The API documentation is explicit that `from_pydata` does **not** prevent invalid mesh data — out-of-range indices, degenerate edges, two-sided faces — and that `Mesh.validate()` should be run whenever the input is not known to be valid. Passing an empty edge list makes Blender infer the edges from the faces.

Face winding determines the normal. The order above gives outward normals for a box built in the +X/+Y/+Z octant; if you generate faces algorithmically, either be careful or run a normals recalculation afterwards.

### `bmesh` — the powerful route

`bmesh` is Blender's editable mesh structure, with connectivity (each vertex knows its edges, each edge its faces). Use it when you need topology operations — bevel, inset, extrude, bridge, dissolve — outside Edit Mode.

```python
import bpy, bmesh
from mathutils import Matrix

def make_panel(name, w, d, t, bevel=0.0005):
    """A board of w x d x t metres, centred on its own origin, with eased arrises."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, t), verts=bm.verts)
    if bevel > 0.0:
        bmesh.ops.bevel(bm, geom=list(bm.verts) + list(bm.edges),
                        offset=bevel, offset_type='OFFSET', segments=2,
                        profile=0.5, affect='EDGES', clamp_overlap=True)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    return ob
```

Notes:

- `bmesh.new()` for a fresh mesh; `bm.from_mesh(mesh)` to load an existing one; `bm.to_mesh(mesh)` to write it back; **always `bm.free()`**.
- In Edit Mode use `bmesh.from_edit_mesh(obj.data)` and `bmesh.update_edit_mesh(obj.data)` instead — do not `to_mesh()` a mesh that is being edited.
- After adding or removing elements, call `bm.verts.ensure_lookup_table()` (and the edge/face equivalents) before indexing `bm.verts[i]`.
- `bmesh.ops.*` mirror the modifiers and edit-mode tools: `create_cube`, `create_circle`, `bevel`, `inset_region`, `extrude_face_region`, `solidify`, `mirror`, `bisect_plane`, `remove_doubles`, `recalc_face_normals`, `triangulate`. Their signatures are documented with the same enums as the UI (`offset_type='OFFSET'`, `miter_outer='ARC'`, and so on).

### `mathutils` — transforms done properly

```python
import math
from mathutils import Vector, Matrix, Euler, Quaternion

loc   = Matrix.Translation(Vector((2.4, 0.0, 0.0)))
rot   = Euler((0.0, 0.0, math.radians(45.0)), 'XYZ').to_matrix().to_4x4()
scale = Matrix.Diagonal(Vector((1.0, 1.0, 1.0, 1.0)))

obj.matrix_world = loc @ rot @ scale        # note: matrices compose left-to-right with @

# world-space bounding box of an object
corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]

# point a camera at a target
direction = (target.location - cam.location)
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

`to_track_quat(track_axis, up_axis)` is the workhorse for aiming cameras (`'-Z'`, `'Y'`), sun lamps (`'Z'`, `'Y'` to aim +Z at the sun), and instanced objects along a curve.

## Modifiers, materials and geometry nodes in code

```python
import bpy

obj = bpy.data.objects["Wall_01"]

# --- modifiers -----------------------------------------------------------
sol = obj.modifiers.new("Thickness", 'SOLIDIFY')
sol.solidify_mode = 'NON_MANIFOLD'    # the "Complex" mode, for wall junctions
sol.thickness = 0.23
sol.offset    = 1.0                   # keep the drawn line as the inner face

bev = obj.modifiers.new("Arris", 'BEVEL')
bev.width = 0.002
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = 0.5236              # 30 degrees, in radians
bev.harden_normals = True

boo = obj.modifiers.new("Openings", 'BOOLEAN')
boo.operation      = 'DIFFERENCE'
boo.operand_type   = 'COLLECTION'
boo.collection     = bpy.data.collections["Cutters_Openings"]
boo.solver         = 'EXACT'
boo.material_mode  = 'TRANSFER'

obj.modifiers.move(obj.modifiers.find("Openings"), 0)   # booleans before solidify

# --- materials -----------------------------------------------------------
mat = bpy.data.materials.get("Plaster_White") or bpy.data.materials.new("Plaster_White")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.82, 0.81, 0.78, 1.0)
bsdf.inputs["Roughness"].default_value  = 0.75
if mat.name not in obj.data.materials:
    obj.data.materials.append(mat)     # material on the MESH -> shared by linked duplicates

# --- geometry nodes ------------------------------------------------------
ng  = bpy.data.node_groups["Wall_Straight_v3"]
gn  = obj.modifiers.new("WallGen", 'NODES')
gn.node_group = ng
ids = {it.name: it.identifier for it in ng.interface.items_tree
       if getattr(it, "in_out", None) == 'INPUT'}
gn[ids["Length"]]    = 6.0
gn[ids["Height"]]    = 2.7
gn[ids["Thickness"]] = 0.23
obj.update_tag()
```

Building a node group from scratch:

```python
import bpy

ng = bpy.data.node_groups.new("Panel", 'GeometryNodeTree')
ng.interface.new_socket("Width",  in_out='INPUT',  socket_type='NodeSocketFloat')
ng.interface.new_socket("Depth",  in_out='INPUT',  socket_type='NodeSocketFloat')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

n_in   = ng.nodes.new('NodeGroupInput');  n_in.location  = (-400, 0)
n_cube = ng.nodes.new('GeometryNodeMeshCube'); n_cube.location = (-150, 0)
n_out  = ng.nodes.new('NodeGroupOutput'); n_out.location = (150, 0)

ng.links.new(n_cube.outputs["Mesh"], n_out.inputs[0])
```

Socket subtypes (so the modifier shows metres, not bare floats) are set on the interface item, e.g. `sock = ng.interface.new_socket(...); sock.subtype = 'DISTANCE'; sock.min_value = 0.0`.

## Scene and render setup in code

```python
import bpy

def setup_scene(scene=None, engine='CYCLES'):
    sc = scene or bpy.context.scene

    sc.unit_settings.system          = 'METRIC'
    sc.unit_settings.scale_length    = 1.0
    sc.unit_settings.length_unit     = 'METERS'
    sc.unit_settings.system_rotation = 'DEGREES'

    sc.render.engine            = engine        # confirm identifiers with `blender -E help`
    sc.render.resolution_x      = 3840
    sc.render.resolution_y      = 2160
    sc.render.resolution_percentage = 100
    sc.render.film_transparent  = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode  = 'RGBA'
    sc.render.image_settings.color_depth = '16'

    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look           = 'AgX - Base Contrast'
    sc.view_settings.exposure       = 0.0

    if engine == 'CYCLES':
        cy = sc.cycles
        cy.device            = 'GPU'
        cy.samples           = 2048
        cy.use_adaptive_sampling = True
        cy.adaptive_threshold    = 0.005
        cy.adaptive_min_samples  = 64
        cy.time_limit            = 0
        cy.use_denoising         = True
        cy.denoiser              = 'OPENIMAGEDENOISE'
        cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        cy.max_bounces = 12
        cy.transmission_bounces = 12
        cy.caustics_reflective = False
        cy.caustics_refractive = False
        cy.blur_glossy = 1.0

    for cam in bpy.data.cameras:
        cam.clip_start, cam.clip_end = 0.01, 1000.0
    return sc


def enable_gpu(backend='OPTIX'):
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = backend          # 'CUDA' 'OPTIX' 'HIP' 'ONEAPI' 'METAL'
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = (dev.type != 'CPU')
    bpy.context.scene.cycles.device = 'GPU'
```

## Headless / background execution

```bash
# run a script against an existing file
blender -b house.blend -P build_joinery.py -- --width 1800 --bays 3

# run a script with no file, in a clean environment, failing the shell on error
blender -b --factory-startup --python-exit-code 1 -P generate.py

# one-liner
blender -b house.blend --python-expr "import bpy; print(bpy.app.version_string)"

# render frame 1 of a named scene on OptiX
blender -b house.blend -S Presentation -o //out/still_#### -F PNG -x 1 -f 1 -- --cycles-device OPTIX
```

Arguments after a bare `--` are ignored by Blender and passed to your script:

```python
import sys
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
```

Background-mode realities:

- `bpy.context.window`, `.area`, `.region` are `None`. Any operator needing them fails.
- `bpy.context.scene` and `bpy.context.view_layer` **do** exist.
- `bpy.ops.wm.save_as_mainfile(filepath=...)` works; `bpy.ops.wm.open_mainfile(filepath=...)` works.
- Add-ons are loaded unless you pass `--factory-startup`; use `--addons` to enable a specific set.
- Auto-execution of Python drivers is **disabled by default** (`-Y`); pass `-y` / `--enable-autoexec` if your file relies on driver expressions.
- Set `--python-exit-code 1` so a traceback becomes a non-zero shell exit and your batch script notices.

## Add-on and extension structure

Blender 4.2 introduced **extensions**: a zipped folder with a `blender_manifest.toml`, installable from the platform or from disk, with declared permissions and optional bundled Python wheels. Legacy `bl_info`-based add-ons still load, but new work should be an extension.

Minimum layout:

```
my_joinery_tools/
├── blender_manifest.toml
└── __init__.py
```

`blender_manifest.toml` (required keys per the manual):

```toml
schema_version = "1.0.0"

id = "joinery_tools"
version = "0.1.0"
name = "Joinery Tools"
tagline = "Cutting lists and carcass generators for cabinetwork"
maintainer = "Your Name <you@example.com>"
type = "add-on"

blender_version_min = "4.2.0"

license = ["SPDX:GPL-3.0-or-later"]

tags = ["Modeling", "Object"]

[permissions]
files = "Write cutting lists to disk"
```

`__init__.py`:

```python
import bpy


class JOINERY_OT_cutting_list(bpy.types.Operator):
    bl_idname = "joinery.cutting_list"
    bl_label  = "Export Cutting List"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH', default="//cutting_list.csv")

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        from . import cutlist                      # your own module
        n = cutlist.write_csv(context, bpy.path.abspath(self.filepath))
        self.report({'INFO'}, f"Wrote {n} parts")
        return {'FINISHED'}


class JOINERY_PT_panel(bpy.types.Panel):
    bl_idname = "JOINERY_PT_panel"
    bl_label  = "Joinery"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Joinery"

    def draw(self, context):
        self.layout.operator("joinery.cutting_list", icon='FILE_TEXT')


classes = (JOINERY_OT_cutting_list, JOINERY_PT_panel)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
```

Build, validate and install:

```bash
blender --command extension validate .
blender --command extension build --source-dir . --output-dir dist
# then: Preferences > Get Extensions > dropdown > Install from Disk
```

Bundle third-party pure-Python dependencies as wheels listed in `wheels = [...]`; for compiled wheels, download one per supported platform (`--python-version=3.13` for the 5.x series) and consider `--split-platforms` at build time.

If the add-on reaches the network, list `network` under `[permissions]` and check `bpy.app.online_access` before making a request.

## The Blender MCP ecosystem

Several Model Context Protocol servers expose Blender to an LLM agent. The best known is **BlenderMCP** (`ahujasid/blender-mcp`, MIT): a Blender add-on opens a socket server (default `localhost:9876`, configurable through `BLENDER_HOST` / `BLENDER_PORT`), and a Python MCP server relays tool calls to it. Client configuration is:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uvx",
      "args": ["blender-mcp"]
    }
  }
}
```

Its tools cover scene inspection, object information, object creation/deletion/modification, material assignment, arbitrary Python execution inside Blender, and asset downloading, with integrations for Poly Haven (models, textures, HDRIs), Sketchfab, Hyper3D Rodin and Hunyuan3D. Requirements: Blender 3.0+, Python 3.10+, and the `uv` package manager.

Other servers in this space expose a richer read side — blend-file summaries (datablocks, missing files, linked libraries), object detail dumps, viewport screenshots, thumbnail and viewport renders, and bundled full-text search over the version-matched Blender manual and Python API reference. That last capability is the single most useful one for an agent: it lets you *verify* an operator ID or a node `bl_idname` against the exact documentation for the running build instead of guessing.

Practical guidance for agent-driven Blender:

1. **Prefer executing a whole script over many small tool calls.** Each round trip is expensive; one `execute_blender_code` call that builds a wardrobe is far cheaper and more atomic than forty.
2. **Return structured data.** Most servers let you assign a JSON-serialisable `dict` to a variable named `result`. Use it — return dimensions, object names and counts so the next step reasons on facts rather than on a screenshot.
3. **Verify before you write.** Search the bundled API/manual docs for an identifier rather than trusting memory; identifiers move between versions (`bpy.ops.import_scene.fbx` is now the *legacy* importer; `bpy.ops.wm.fbx_import` is the native one).
4. **Take a screenshot or viewport render after a structural change**, not after every property tweak.
5. **Save incrementally.** `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)` before a destructive step.
6. **Never `bpy.ops.wm.read_homefile()`** in a session the user has unsaved work in.

---

## Script 1 — Build a parametric wall

```python
"""Build a straight wall with openings, entirely from data.
Run:  blender -b -P wall.py -- --length 6.0 --height 2.7 --thickness 0.23
"""
import bpy, sys


def arg(name, default, cast=float):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if name in argv:
        return cast(argv[argv.index(name) + 1])
    return default


def ensure_collection(name, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(col)
    return col


def box(name, size, location, collection):
    sx, sy, sz = size
    verts = [(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0),
             (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    collection.objects.link(ob)
    return ob


def build_wall(length=6.0, height=2.7, thickness=0.23,
               openings=((0.9, 0.0, 1.0, 2.1),          # (x, sill, width, height) - door
                         (3.2, 0.9, 1.5, 1.2))):        # window
    scene   = bpy.context.scene
    walls   = ensure_collection("02_Shell")
    cutters = ensure_collection("Cutters_Openings")

    wall = box("Wall_01", (length, thickness, height), (0, 0, 0), walls)
    wall["thickness_m"] = thickness

    for i, (x, sill, w, h) in enumerate(openings, start=1):
        c = box(f"Cut_Opening_{i:02d}",
                (w, thickness + 0.2, h),
                (x, -0.1, sill),
                cutters)
        c.display_type = 'WIRE'
        c.hide_render  = True
        c["opening_w"], c["opening_h"], c["sill_h"] = w, h, sill

    m = wall.modifiers.new("Openings", 'BOOLEAN')
    m.operation     = 'DIFFERENCE'
    m.operand_type  = 'COLLECTION'
    m.collection    = cutters
    m.solver        = 'EXACT'

    b = wall.modifiers.new("Arris", 'BEVEL')
    b.width, b.segments, b.limit_method = 0.002, 2, 'ANGLE'
    b.harden_normals = True

    # exclude the cutter collection from the view layer so it is never rendered
    lc = scene.view_layers[0].layer_collection.children.get(cutters.name)
    if lc:
        lc.exclude = True
    return wall


if __name__ == "__main__":
    w = build_wall(length=arg("--length", 6.0),
                   height=arg("--height", 2.7),
                   thickness=arg("--thickness", 0.23))
    deps = bpy.context.evaluated_depsgraph_get()
    me = w.evaluated_get(deps).to_mesh()
    print(f"{w.name}: {len(me.vertices)} verts after modifiers")
    w.evaluated_get(deps).to_mesh_clear()
```

## Script 2 — Build a wardrobe carcass from dimensions

```python
"""Build a wardrobe carcass as discrete, correctly-named, correctly-dimensioned panels.
Every panel is a real board so the cutting list in script 4 is truthful.
"""
import bpy

PANEL_T = 0.018      # 18 mm MDF / melamine
BACK_T  = 0.006      # 6 mm back
TOE     = 0.100      # plinth height


def _collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _panel(name, size, location, collection, part, grain="length"):
    sx, sy, sz = size
    verts = [(0, 0, 0), (sx, 0, 0), (sx, sy, 0), (0, sy, 0),
             (0, 0, sz), (sx, 0, sz), (sx, sy, sz), (0, sy, sz)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate(); me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = location
    ob["part"]  = part            # 'SIDE' 'TOP' 'BOTTOM' 'SHELF' 'DIVIDER' 'BACK' 'PLINTH'
    ob["grain"] = grain           # 'length' | 'width' | 'none'
    collection.objects.link(ob)
    return ob


def build_wardrobe(code="WD01", width=1.800, height=2.400, depth=0.600,
                   bays=3, shelves_per_bay=4,
                   panel_t=PANEL_T, back_t=BACK_T, toe=TOE):
    col = _collection(f"03_Joinery_{code}")
    parts = []

    carcass_h = height - toe
    inner_h   = carcass_h - 2 * panel_t
    bay_w     = (width - (bays + 1) * panel_t) / bays

    # sides
    parts.append(_panel(f"{code}_Side_L", (panel_t, depth, carcass_h),
                        (0.0, 0.0, toe), col, 'SIDE'))
    parts.append(_panel(f"{code}_Side_R", (panel_t, depth, carcass_h),
                        (width - panel_t, 0.0, toe), col, 'SIDE'))

    # bottom and top, running between the sides
    inner_w = width - 2 * panel_t
    parts.append(_panel(f"{code}_Bottom", (inner_w, depth, panel_t),
                        (panel_t, 0.0, toe), col, 'BOTTOM', grain="width"))
    parts.append(_panel(f"{code}_Top", (inner_w, depth, panel_t),
                        (panel_t, 0.0, toe + carcass_h - panel_t), col, 'TOP', grain="width"))

    # vertical dividers
    for i in range(1, bays):
        x = panel_t + i * (bay_w + panel_t) - panel_t
        parts.append(_panel(f"{code}_Divider_{i:02d}", (panel_t, depth, inner_h),
                            (x, 0.0, toe + panel_t), col, 'DIVIDER'))

    # shelves
    shelf_d = depth - back_t - 0.010          # 10 mm clear of the back panel
    for b in range(bays):
        x0 = panel_t + b * (bay_w + panel_t)
        pitch = inner_h / (shelves_per_bay + 1)
        for s in range(1, shelves_per_bay + 1):
            z = toe + panel_t + s * pitch
            parts.append(_panel(f"{code}_Shelf_B{b+1:02d}_{s:02d}",
                                (bay_w, shelf_d, panel_t),
                                (x0, 0.0, z), col, 'SHELF', grain="width"))

    # back
    parts.append(_panel(f"{code}_Back", (width, back_t, carcass_h),
                        (0.0, depth - back_t, toe), col, 'BACK', grain="none"))

    # plinth
    parts.append(_panel(f"{code}_Plinth", (width, panel_t, toe),
                        (0.0, 0.050, 0.0), col, 'PLINTH', grain="width"))

    # metadata for downstream scripts
    for p in parts:
        p["unit"] = code
        p["material_code"] = "MFC18_WHITE"
        b = p.modifiers.new("Arris", 'BEVEL')
        b.width, b.segments, b.limit_method = 0.0005, 2, 'ANGLE'
        b.harden_normals = True

    print(f"{code}: {len(parts)} panels, bay width {bay_w*1000:.1f} mm, inner height {inner_h*1000:.1f} mm")
    return parts


if __name__ == "__main__":
    build_wardrobe()
```

## Script 3 — Batch-render a camera set

```python
"""Render every camera in a named collection to its own file.
Run: blender -b house.blend -P batch_render.py -- --out //renders --samples 1024
"""
import bpy, os, sys, time


def argv_get(flag, default, cast=str):
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return cast(a[a.index(flag) + 1]) if flag in a else default


def batch_render(collection_name="06_Cameras", out_dir="//renders",
                 samples=1024, res=(3840, 2160), fmt='PNG'):
    scene = bpy.context.scene
    col = bpy.data.collections.get(collection_name)
    if col is None:
        raise SystemExit(f"collection '{collection_name}' not found")

    cams = sorted((o for o in col.objects if o.type == 'CAMERA'), key=lambda o: o.name)
    if not cams:
        raise SystemExit("no cameras in collection")

    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = fmt
    if scene.render.engine == 'CYCLES':
        scene.cycles.samples = samples
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.005
        scene.cycles.use_denoising = True

    out_abs = bpy.path.abspath(out_dir)
    os.makedirs(out_abs, exist_ok=True)

    original_cam = scene.camera
    manifest = []
    try:
        for cam in cams:
            scene.camera = cam
            path = os.path.join(out_abs, f"{cam.name}.{fmt.lower()}")
            scene.render.filepath = path
            t0 = time.time()
            bpy.ops.render.render(write_still=True)
            dt = time.time() - t0
            manifest.append({"camera": cam.name, "file": path, "seconds": round(dt, 1)})
            print(f"[{len(manifest)}/{len(cams)}] {cam.name} -> {path}  ({dt:.1f}s)")
    finally:
        scene.camera = original_cam

    return manifest


if __name__ == "__main__":
    result = batch_render(out_dir=argv_get("--out", "//renders"),
                          samples=argv_get("--samples", 1024, int))
    total = sum(r["seconds"] for r in result)
    print(f"done: {len(result)} images in {total/60:.1f} min")
```

## Script 4 — Export a cutting list from the scene

```python
"""Walk a joinery collection, measure every panel AFTER modifiers, and write a CSV
cutting list with sizes in millimetres, grain direction and quantity roll-up.
Run: blender -b job.blend -P cutlist.py -- --collection 03_Joinery_WD01 --out //WD01_cutlist.csv
"""
import bpy, csv, sys, os
from collections import defaultdict
from mathutils import Vector


def argv_get(flag, default):
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return a[a.index(flag) + 1] if flag in a else default


def world_dimensions_mm(obj, depsgraph):
    """True dimensions of the evaluated object, in millimetres, sorted long->short."""
    ev = obj.evaluated_get(depsgraph)
    me = ev.to_mesh()
    try:
        if not me.vertices:
            return None
        mw = obj.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    finally:
        ev.to_mesh_clear()
    d = [(hi.x - lo.x) * 1000.0, (hi.y - lo.y) * 1000.0, (hi.z - lo.z) * 1000.0]
    d.sort(reverse=True)
    return d          # [length, width, thickness] in mm


def collect(collection_name):
    col = bpy.data.collections.get(collection_name)
    if col is None:
        raise SystemExit(f"collection '{collection_name}' not found")
    deps = bpy.context.evaluated_depsgraph_get()

    rows = []
    for obj in col.all_objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        dims = world_dimensions_mm(obj, deps)
        if dims is None:
            continue
        length, width, thickness = (round(x, 1) for x in dims)
        rows.append({
            "unit":     obj.get("unit", collection_name),
            "part":     obj.get("part", "UNKNOWN"),
            "name":     obj.name,
            "length_mm": length,
            "width_mm":  width,
            "thick_mm":  thickness,
            "grain":     obj.get("grain", "none"),
            "material":  obj.get("material_code",
                                 obj.data.materials[0].name if obj.data.materials else ""),
        })
    return rows


def roll_up(rows):
    """Group identical parts into quantities."""
    buckets = defaultdict(lambda: {"qty": 0, "names": []})
    for r in rows:
        key = (r["unit"], r["part"], r["length_mm"], r["width_mm"],
               r["thick_mm"], r["grain"], r["material"])
        buckets[key]["qty"] += 1
        buckets[key]["names"].append(r["name"])
    out = []
    for key, v in sorted(buckets.items()):
        unit, part, l, w, t, grain, mat = key
        out.append({"unit": unit, "part": part, "qty": v["qty"],
                    "length_mm": l, "width_mm": w, "thick_mm": t,
                    "grain": grain, "material": mat,
                    "examples": "; ".join(sorted(v["names"])[:3])})
    return out


def write_csv(rows, path):
    path = bpy.path.abspath(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fields = ["unit", "part", "qty", "length_mm", "width_mm", "thick_mm",
              "grain", "material", "examples"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


if __name__ == "__main__":
    coll = argv_get("--collection", "03_Joinery_WD01")
    out  = argv_get("--out", "//cutting_list.csv")
    detail = collect(coll)
    summary = roll_up(detail)
    p = write_csv(summary, out)
    total_area = sum(r["qty"] * r["length_mm"] * r["width_mm"] for r in summary) / 1e6
    print(f"{len(detail)} panels -> {len(summary)} line items -> {p}")
    print(f"total board area {total_area:.2f} m2 (before waste allowance)")
```

> ⚠️ The cutting list measures the **world-space bounding box of the evaluated mesh**, so a 0.5 mm bevel adds nothing measurable but a Solidify or Array modifier is correctly included. It will silently mis-measure a panel that is rotated off-axis (the bounding box then exceeds the board) — model panels axis-aligned, or extend the function to measure in the object's local frame. Always add a waste allowance and check against the board sizes actually available before ordering.

## Sources

- [API — Operators (`bpy.ops`) and overriding context](https://docs.blender.org/api/current/bpy.ops.html) — accessed 2026-08-25 via the version-matched local API bundle
- [API — `bpy.types.Context.temp_override` and `logging_set`](https://docs.blender.org/api/current/bpy.types.Context.html) — accessed 2026-08-25 via the local API bundle
- [API — Gotchas: why an operator's poll fails](https://docs.blender.org/api/current/info_gotchas_operators.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.Mesh.from_pydata`](https://docs.blender.org/api/current/bpy.types.Mesh.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.Object.to_mesh` / `to_mesh_clear`](https://docs.blender.org/api/current/bpy.types.Object.html) — accessed 2026-08-25 via the local API bundle
- [API — `bmesh.ops` (`create_cube`, `bevel`, …)](https://docs.blender.org/api/current/bmesh.ops.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.NodeTreeInterface.new_socket`](https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.BlendDataNodeTrees.new`](https://docs.blender.org/api/current/bpy.types.BlendData.html) — accessed 2026-08-25 via the local API bundle
- [Manual — Command Line Arguments (Python options, background, exit code)](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — How to Create Extensions and the manifest](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Extensions Command Line Arguments (`build`, `validate`, `install`)](https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Python Wheels in extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html) — accessed 2026-08-25 via the local manual bundle
- [BlenderMCP — ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) — accessed 2026-08-25

## Open questions

- Modifier property identifiers used above were confirmed against the API reference: `SolidifyModifier.solidify_mode` is `'EXTRUDE'` (Simple) / `'NON_MANIFOLD'` (Complex); `BooleanModifier.solver` is `'FLOAT'` / `'EXACT'` / `'MANIFOLD'` and `material_mode` is `'INDEX'` / `'TRANSFER'`; `BevelModifier.limit_method` is `'NONE'` / `'ANGLE'` / `'WEIGHT'` / `'VGROUP'`.
- `cycles.adaptive_min_samples`, `cycles.denoising_input_passes` and `cycles.blur_glossy` property names are used from working knowledge; the Cycles add-on's properties are not in the core RNA docs. Verify against `bpy.context.scene.cycles.bl_rna.properties` on the target build.
- `scene.view_settings.look = 'AgX - Base Contrast'` — the exact Look string depends on the active OCIO config; enumerate `bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items` rather than hard-coding.
- The render-engine identifier passed to `scene.render.engine` (`'BLENDER_EEVEE_NEXT'` vs `'BLENDER_EEVEE'`) differs between the 4.2–4.5 and 5.x series; resolve it at runtime.
