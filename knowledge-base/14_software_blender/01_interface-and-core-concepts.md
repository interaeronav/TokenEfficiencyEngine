---
id: blender.interface_core_concepts
title: Blender interface and core data model
domain: software_blender
tags: [blender, datablocks, collections, view-layer, depsgraph, modifiers, units, metric, clipping, outliner, workspaces]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; valid for 4.5 LTS except where noted"
unit_system: metric
sources:
  - {title: "Blender Manual — Scene Properties: Units", url: "https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — 3D Viewport Sidebar (Clip Start/End)", url: "https://docs.blender.org/manual/en/latest/editors/3dview/sidebar.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — UnitSettings", url: "https://docs.blender.org/api/current/bpy.types.UnitSettings.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — Object (to_mesh, evaluated_get)", url: "https://docs.blender.org/api/current/bpy.types.Object.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Data-Blocks", url: "https://docs.blender.org/manual/en/latest/files/data_blocks.html", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.overview, blender.python_api, blender.modelling]
---

# Blender interface and core data model

**Summary.** Blender's UI is a thin skin over a datablock database. Every scene, object, mesh, material, image, node group and collection is an ID datablock with a name, a user count and a place in `bpy.data`. Objects are *transforms plus a pointer to object data*; the same mesh can back twenty objects. Collections organise, view layers filter, and the dependency graph turns the raw data plus modifiers into the evaluated geometry you actually see and render. Getting this model straight is the difference between an automation script that works and one that silently edits the wrong copy of something.

## Key facts

| Concept | Python entry point | Note |
|---|---|---|
| File database | `bpy.data` | `objects`, `meshes`, `materials`, `collections`, `scenes`, `node_groups`, `images`, `worlds`, `cameras`, `lights`, `curves`, `texts` |
| Active scene | `bpy.context.scene` | A `.blend` may hold several scenes |
| View layer | `bpy.context.view_layer` | Per-scene render/visibility filter over collections |
| Scene root collection | `scene.collection` | Every other collection hangs below it |
| Object transform | `obj.location`, `obj.rotation_euler`, `obj.scale`, `obj.matrix_world` | Object-level, not baked into the mesh |
| Object data | `obj.data` | A `Mesh`, `Curve`, `Camera`, `Light`, `Volume`, `GreasePencilv3`… |
| Users of a datablock | `datablock.users` | 0 users = purged at next save/reload unless `use_fake_user` |
| Dependency graph | `bpy.context.evaluated_depsgraph_get()` | Then `obj.evaluated_get(depsgraph)` for the modifier result |
| Units panel | `Properties ▸ Scene ▸ Units` → `scene.unit_settings` | `system`, `scale_length`, `length_unit`, `system_rotation`, `use_separate` |
| Viewport clipping | `View3D` sidebar (N) ▸ View ▸ Clip Start/End → `SpaceView3D.clip_start` / `clip_end` | |
| Camera clipping | `Properties ▸ Object Data (camera) ▸ Lens ▸ Clip Start/End` → `camera.clip_start` / `clip_end` | |
| Blender axes | +X right, +Y forward (into the screen from front view), **+Z up** | Front view looks along +Y |

## Datablocks, users and linked duplicates

An ID datablock is anything with a name field in the Outliner. Datablocks reference each other and Blender reference-counts those references. Three consequences matter for automation:

1. **A datablock with zero users disappears.** If you create a mesh with `bpy.data.meshes.new("Panel")` and never link an object to it, it is garbage on the next file reload. Set `mesh.use_fake_user = True` to keep an unused datablock alive deliberately (a material library, a node group).
2. **Object vs object data is the single most important distinction.** `bpy.data.objects["Shelf"]` holds position, rotation, scale, modifiers, material *slots*, parent and collection membership. `bpy.data.meshes["ShelfPanel"]` holds vertices, edges, faces, UV maps, attributes and the material *list*. Duplicating with `Alt-D` (Python: creating a new object pointing at the same `mesh`) gives a **linked duplicate**: editing one edits all. Duplicating with `Shift-D` (`mesh.copy()`) gives an independent copy. For a wardrobe with 12 identical shelves you want linked duplicates or, better, an Array modifier or geometry-node instances — 12 independent meshes is 12× the memory and 12 places to edit a thickness.
3. **Names are unique per collection and are the API key.** `bpy.data.objects["Wall.001"]`. Blender auto-suffixes collisions with `.001`, so a script that assumes `bpy.data.objects["Wall"]` exists after creating a second wall is a bug waiting to happen. In 5.x, `ID.rename(name, mode=...)` gives explicit collision handling (`'NEVER'`, `'ALWAYS'`, `'SAME_ROOT'`).

Material slots are a further indirection worth memorising: `obj.material_slots[i].link` is either `'DATA'` (the material lives on the mesh, shared by all objects using it) or `'OBJECT'` (per-object override). For a linked-duplicate carcass where one panel must be melamine and another oak, `'OBJECT'` linking is the mechanism.

## Scenes, view layers, collections

- **Scene** — an independent world: its own objects, its own render settings, its own frame range, its own world shader. Use separate scenes for genuinely separate deliverables (e.g. a "Presentation" scene and a "Technical" scene with flat clay shading and orthographic cameras).
- **Collection** — a named, nestable group of objects. Collections are datablocks, so a collection can be *instanced* into a scene as a single empty (an "Collection Instance" object). That is how you place ten identical window units, or the same fence bay along a boundary, with one editable master.
- **View Layer** — a per-scene filter over the collection tree with per-collection flags: `exclude` (not evaluated at all), `holdout` (cuts a hole in the alpha), `indirect_only` (contributes bounce light but is not visible), plus `hide_viewport` and `hide_render`. A single scene can therefore render an "exterior" layer and an "interior" layer with different collections enabled, and the compositor can recombine them.

For an architectural project, a workable collection scheme is:

```
Scene Collection
├── 00_Reference        (imported DXF/SVG plans, survey points; excluded at render)
├── 01_Site             (ground, boundary wall, paving, planting)
├── 02_Shell            (walls, slabs, roof, openings)
├── 03_Joinery          (kitchen, wardrobes, doors, skirtings)
│   ├── Kitchen
│   └── BedroomWardrobe
├── 04_Furniture        (loose furniture, mostly collection instances)
├── 05_Lighting         (sun, portals, practicals, HDRI helpers)
└── 06_Cameras
```

Collection **exporters** (5.x) let you attach an export operator to a collection and fire them all with `bpy.ops.wm.collection_export_all()` — a clean way to keep `03_Joinery` continuously exported to STL/DXF for the workshop.

## Objects vs object data in practice

```python
import bpy

mesh = bpy.data.meshes.new("Carcass_Side")          # object data, 0 users
obj  = bpy.data.objects.new("Carcass_Side_L", mesh) # object, mesh now has 1 user
bpy.data.collections["03_Joinery"].objects.link(obj)  # object now in the scene

# linked duplicate: same mesh, mirrored position
obj_r = bpy.data.objects.new("Carcass_Side_R", mesh) # mesh now has 2 users
obj_r.location.x = 0.600
bpy.data.collections["03_Joinery"].objects.link(obj_r)
```

Note that nothing here touched `bpy.context`, no object was selected, no mode was changed, and the code runs identically in `blender -b`. This is the pattern to reach for.

`obj.dimensions` is a convenience that reports the world-space bounding box of the *evaluated* object. Setting it rescales the object (changing `obj.scale`), which is usually **not** what you want for joinery — a scaled object exports with non-unit scale and confuses downstream CAD. Build panels at true size in the mesh and keep `obj.scale == (1,1,1)`. If you must scale, apply it (`bpy.ops.object.transform_apply(scale=True)`, or in data terms bake the matrix into the vertices).

## The dependency graph

The depsgraph is the evaluator. It takes the *original* data (what you edit, what `bpy.data` exposes) plus modifiers, constraints, drivers, parenting, geometry nodes and animation, and produces the *evaluated* data (what is drawn and rendered). Original data never contains modifier results.

```python
deps = bpy.context.evaluated_depsgraph_get()
eval_obj = obj.evaluated_get(deps)
me = eval_obj.to_mesh()            # modifier stack applied, temporary
print(len(me.vertices))
eval_obj.to_mesh_clear()           # free it
```

`to_mesh(preserve_all_data_layers=True, depsgraph=deps)` keeps UVs and vertex groups, at a cost. This is how you measure a wall *after* Solidify, or count pavers *after* an Array, or write a cutting list from a parametric carcass. Two rules:

- The depsgraph is not automatically re-evaluated inside a script after you change data. Call `bpy.context.view_layer.update()` or re-fetch the depsgraph if you need fresh results mid-script.
- The mesh returned by `to_mesh()` is temporary and owned by the object. Do not store references to it; copy the numbers you need out.

## Modifiers vs geometry nodes vs operators

Three different mechanisms, constantly confused:

| | What it is | Destructive? | Best for |
|---|---|---|---|
| **Modifier** | A named, ordered, parameterised operation on the object's data, evaluated by the depsgraph | No | Repeatable construction: thickness, mirroring, arrays, bevels, booleans |
| **Geometry node group** | A node graph, applied via a `'NODES'` modifier, that can generate geometry from nothing or transform incoming geometry, with typed inputs exposed on the modifier | No | True procedural systems with parameters: wall generators, staircases, fences, paver fields |
| **Operator** (`bpy.ops`) | A recorded user action that mutates data immediately | Yes | Interactive editing; one-shot conversions; anything with no data-level equivalent |

The modifier stack is evaluated **top to bottom** and the order changes the result profoundly. `object.modifiers.new(name, type)` appends; `object.modifiers.move(from_index, to_index)` reorders. Modifier order gotchas are covered in file `02`.

Geometry-node modifiers expose the node group's interface sockets as modifier properties keyed by socket **identifier** (e.g. `mod["Socket_2"]`), not by label. Get the identifier from `node_group.interface.items_tree[...].identifier`. File `03` and file `06` cover this in full.

## Editors, workspaces and the areas that matter

A Blender window is a tree of *areas*, each showing an *editor*. A **workspace** is a saved arrangement plus a mode. The defaults across the top tab bar: Layout, Modeling, Sculpting, UV Editing, Texture Paint, Shading, Animation, Rendering, Compositing, Geometry Nodes, Scripting.

For this domain, five editors carry the load:

- **3D Viewport** — modelling. `N` toggles the sidebar (Item / Tool / View / and add-on tabs); `T` toggles the toolbar. The Item tab holds Transform (Location/Rotation/Scale) and **Dimensions** — the numeric entry that makes CAD-accurate work possible.
- **Outliner** — the datablock browser. Switch its Display Mode from "View Layer" to **"Blender File"** or **"Orphan Data"** to see the real database, including datablocks with zero users. Indispensable for diagnosing duplicated materials (`Wood.001`, `Wood.002`…).
- **Properties** — tabs for Render, Output, View Layer, Scene, World, Object, Modifiers, Particles, Physics, Constraints, Object Data, Material. `Properties ▸ Scene ▸ Units` is where unit setup lives.
- **Shader Editor / Geometry Node Editor** — node graphs for materials and geometry.
- **Text Editor / Python Console** — the Scripting workspace. The Python Console is the fastest way to interrogate the live scene; `bpy.context.object` and tab-completion answer most API questions in seconds. Enable `Preferences ▸ Interface ▸ Display ▸ Python Tooltips` and `Developer Extras` so every button reveals its data path, and right-click ▸ *Copy Full Data Path* to get the exact `bpy` expression.

The **Info** editor logs the operator calls corresponding to your GUI actions. It is a good discovery tool and a bad code generator: what it prints is `bpy.ops` with context assumptions baked in. Read it, then rewrite as data manipulation.

## Units, scale and clipping for building-sized scenes

This section is load-bearing. Get it wrong and every measurement, export and photometric light value in the project is wrong.

**Set the units.** `Properties ▸ Scene ▸ Units`:

| Field | Value for building work | Python |
|---|---|---|
| Unit System | Metric | `scene.unit_settings.system = 'METRIC'` |
| Unit Scale | `1.0` | `scene.unit_settings.scale_length = 1.0` |
| Length | Metres (or Millimetres for joinery-only files) | `scene.unit_settings.length_unit = 'METERS'` |
| Separate Units | Off | `scene.unit_settings.use_separate = False` |
| Rotation | Degrees | `scene.unit_settings.system_rotation = 'DEGREES'` |

With Unit Scale 1.0, **1 Blender unit = 1 metre**, always, regardless of the display unit. Changing `length_unit` to millimetres only changes how numbers are *displayed and typed*; the underlying float is still metres. Changing `scale_length` changes the meaning of a unit and is intended for microscopic or astronomical work where float precision fails; for a house it should stay at 1.0. If you inherit a file where `scale_length` is 0.001, everything you type will be a thousand times off.

Once set, you can type real dimensions anywhere a length is accepted: `2.7` (metres), `2700mm`, `2.7m`, `18mm`, and even arithmetic — `2400/3`, `0.6*4`. This is what makes exact joinery possible without a CAD package.

**Set the clipping.** Blender's default viewport clip range is tuned for a 2 m character, and a 1 mm shelf edge in a 40 m site will z-fight or vanish.

- Viewport: `N` ▸ View ▸ Clip Start `0.01 m`, Clip End `1000 m`.
- Camera: `Properties ▸ Object Data ▸ Lens ▸ Clip Start 0.01 m`, `Clip End 1000 m`.

Do not simply set Start to `0.0001` and End to `100000`: the manual is explicit that a large clipping range reduces depth precision and produces artifacts, and can make depth-buffer-dependent operations (snapping, some overlays, EEVEE effects) unreliable. Pick the tightest range that contains the work. For a residential erf, 0.01 m to 1000 m is comfortable; for a joinery-only file, 0.001 m to 100 m.

```python
import bpy

sc = bpy.context.scene
sc.unit_settings.system        = 'METRIC'
sc.unit_settings.scale_length  = 1.0
sc.unit_settings.length_unit   = 'METERS'
sc.unit_settings.system_rotation = 'DEGREES'

for cam in bpy.data.cameras:
    cam.clip_start, cam.clip_end = 0.01, 1000.0

for scr in bpy.data.screens:            # every 3D viewport in every workspace
    for area in scr.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.clip_start, space.clip_end = 0.01, 1000.0
```

**Grid and overlays.** In `Overlays ▸ Guides`, set Grid Scale to `1 m` and Subdivisions to `10` so the floor grid reads in metres and 100 mm. Enable `Overlays ▸ Measurement ▸ Edge Length / Face Area` in Edit Mode to display live dimensions on selected geometry — the manual notes these follow the scene unit settings and never appear in renders.

**Origin discipline.** Put the model origin at a meaningful survey point (a building corner, the intersection of two grid lines) and keep it there. Very large coordinates (e.g. real UTM eastings in the hundreds of thousands) destroy 32-bit float precision and produce jittering geometry and z-fighting; if you import survey data in absolute coordinates, translate it to a local origin immediately and record the offset in a custom property on the scene:

```python
bpy.context.scene["survey_offset_m"] = [612345.0, 8067890.0, 1105.0]
```

Custom properties are first-class, are saved in the `.blend`, survive round-trips through glTF/USD `extras`, and are the correct place for project metadata (panel thickness, material code, room name) that later scripts will read.

## Sources

- [Manual — Scene Properties: Units](https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — 3D Viewport Sidebar: Clip Start/End](https://docs.blender.org/manual/en/latest/editors/3dview/sidebar.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Measure tool and unit display](https://docs.blender.org/manual/en/latest/editors/3dview/toolbar/measure.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Custom Properties](https://docs.blender.org/manual/en/latest/files/custom_properties.html) — accessed 2026-08-25 via the local manual bundle
- [API — `bpy.types.UnitSettings`](https://docs.blender.org/api/current/bpy.types.UnitSettings.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.Object.to_mesh`](https://docs.blender.org/api/current/bpy.types.Object.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.ID.evaluated_get` / `rename`](https://docs.blender.org/api/current/bpy.types.ID.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.ObjectModifiers`](https://docs.blender.org/api/current/bpy.types.ObjectModifiers.html) — accessed 2026-08-25 via the local API bundle

## Open questions

- The precise set of `length_unit` enum values is reported as `Literal['DEFAULT']` in the generated API docs because it is a dynamic enum; `'METERS'`, `'MILLIMETERS'`, `'CENTIMETERS'`, `'KILOMETERS'` and `'MICROMETERS'` are the values exposed in the UI. Confirm at runtime with `bpy.types.UnitSettings.bl_rna.properties['length_unit'].enum_items` before hard-coding.
