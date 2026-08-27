---
id: blender.geometry_nodes
title: Geometry Nodes for parametric architecture and joinery
domain: software_blender
tags: [blender, geometry-nodes, procedural, fields, attributes, instancing, parametric-wall, staircase, fence, paving, wardrobe]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; graphs work in 4.5 LTS except Bundles/Closures and the new node-based Array/Scatter modifiers (5.0+)"
unit_system: metric
sources:
  - {title: "Blender Manual — Geometry Nodes", url: "https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/index.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Instance on Points Node", url: "https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/instance_on_points.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Repeat Zone", url: "https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/repeat_zone.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Mesh Boolean Node", url: "https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/mesh/operations/mesh_boolean.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — NodeTreeInterface", url: "https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender 5.0 release notes", url: "https://www.blender.org/download/releases/5-0/", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.modelling, blender.python_api, blender.materials]
---

# Geometry Nodes for parametric architecture and joinery

**Summary.** Geometry Nodes is Blender's procedural geometry system: a node graph, applied through a `'NODES'` modifier, that reads geometry in and writes geometry out, with typed inputs exposed on the modifier panel so a wall, a stair or a wardrobe becomes a set of numbers you can type. For architectural work it replaces most repetitive modelling: walls with openings, balustrades, fences, paving fields, shelving, louvres, roof battens. This file explains the two ideas that trip everyone up — **fields** and **domains** — then gives five worked graphs specified precisely enough to rebuild node by node.

## Key facts

| Item | Value |
|---|---|
| Editor | Geometry Node Editor (Geometry Nodes workspace) |
| Applied via | Geometry Nodes modifier, `obj.modifiers.new("GN", 'NODES')`, then `mod.node_group = ng` |
| Node group type | `bpy.data.node_groups.new(name, 'GeometryNodeTree')` |
| Interface sockets | `ng.interface.new_socket(name, in_out='INPUT'|'OUTPUT', socket_type='NodeSocketFloat', ...)` |
| Modifier input access | `mod["Socket_2"]` — keyed by socket **identifier**, not label |
| Geometry domains | Point, Edge, Face, Face Corner, Curve, Instance, Layer |
| Attribute types | Float, Integer, Vector, Color, Boolean, 2D Vector, Quaternion, 4×4 Matrix |
| Field sockets | Drawn as **diamonds**; single values as **circles**; diamond-with-dot = accepts either |
| Zones | Repeat Zone, Simulation Zone, For Each Element Zone (4.3+), Closure/Bundle (5.0+) |
| Import nodes (5.x) | Import STL / OBJ / PLY / CSV / Text / OpenVDB directly inside a graph |
| Node-based modifiers (5.0+) | Array, Scatter on Surface, Curve to Tube and three others ship as built-in procedural modifiers |

## Fields, in one page

A socket in Geometry Nodes carries either a **single value** or a **field**. A single value is one number: "extrude by 0.1". A field is a *function* that will be evaluated once per element of some domain: "extrude by (the Z coordinate of each vertex × 0.1)".

- Round socket = single value only.
- Diamond socket = field.
- Diamond-with-a-dot = takes either; if you plug a field in, the node evaluates it per element.

Nodes such as **Position** (`GeometryNodeInputPosition`), **Normal**, **Index**, **Random Value** (`FunctionNodeRandomValue`) and **Named Attribute** (`GeometryNodeInputNamedAttribute`) *produce* fields. Nodes such as **Set Position** (`GeometryNodeSetPosition`), **Store Named Attribute** (`GeometryNodeStoreNamedAttribute`), **Delete Geometry** (`GeometryNodeDeleteGeometry`) and **Instance on Points** *consume* them, and the consuming node decides the domain the field is evaluated on.

The one rule to remember: **a field has no meaning until a geometry node evaluates it.** You cannot "look at" the position of a vertex in the middle of a graph; you can only build a recipe and hand it to a node that has geometry to apply it to. When you genuinely need to freeze a field into stored data at a specific point in the graph, use **Capture Attribute** (`GeometryNodeCaptureAttribute`) — for example, capture each fence-post's index *before* instancing so that the instanced geometry can still read it.

## Domains and attributes

Geometry carries named attributes on domains:

| Domain | Meshes | Curves | Points | Instances |
|---|---|---|---|---|
| Point | vertices | control points | points | — |
| Edge | edges | — | — | — |
| Face | faces | — | — | — |
| Face Corner | per-vertex-per-face (UVs, split normals, vertex colours) | — | — | — |
| Curve | — | whole splines | — | — |
| Instance | — | — | — | one per instance |

Built-in attributes have reserved names: `position`, `id`, `material_index`, `radius`, `sharp_face`, `sharp_edge`, plus UV maps and colour attributes by user name. Anything you invent (`panel_thickness`, `opening_id`, `course`) is a custom attribute stored with Store Named Attribute and read back with Named Attribute.

Attributes **interpolate** when a node changes domain: a Face attribute read on the Point domain is averaged from the adjacent faces; a Point attribute read on Face is averaged from the face's vertices. Booleans use "any"/"all" logic. Most domain-changing nodes have an explicit Domain dropdown; set it deliberately rather than relying on implicit conversion.

The **Spreadsheet editor** is the debugger. Open it, select the object, choose the domain, and you see every attribute value on every element at the currently-viewed node (with the node's "viewer" active, or at the modifier output). Nothing else in Blender tells you this much this fast. Pair it with **Viewer** node + `Ctrl-Shift-LMB` (the Node Wrangler preview shortcut for geometry is `Shift-Alt-LMB`).

## Instancing

Instances are references, not copies. `GeometryNodeInstanceOnPoints` places a reference to some geometry at every point of an incoming geometry that has a Point domain — meshes, point clouds, curve control points all qualify. A thousand pavers instanced from one paver mesh cost one paver's memory. Blender 5.2 specifically claims a ~2× EEVEE speed-up on instance-heavy scenes, which is exactly the paving/brickwork/fence case.

Downstream instance nodes: `GeometryNodeRotateInstances`, `GeometryNodeScaleInstances`, `GeometryNodeTranslateInstances`, and `GeometryNodeRealizeInstances`.

**Realize Instances converts references into real geometry.** It is necessary before mesh booleans, before most attribute writes on the resulting mesh, and before some exporters (USD instancing is only partially supported). It is also the fastest way to destroy performance — realizing 50 000 pavers produces a multi-million-vertex mesh. Realize as late as possible, ideally never.

## Essential nodes for this domain

**Input / primitives** — Grid (`GeometryNodeMeshGrid`), Cube (`GeometryNodeMeshCube`), Mesh Line (`GeometryNodeMeshLine`), Curve Line (`GeometryNodeCurvePrimitiveLine`), Quadrilateral (`GeometryNodeCurvePrimitiveQuadrilateral`).

**Geometry ops** — Join Geometry (`GeometryNodeJoinGeometry`), Transform Geometry (`GeometryNodeTransform`), Mesh Boolean (`GeometryNodeMeshBoolean`), Extrude Mesh (`GeometryNodeExtrudeMesh`), Delete Geometry, Separate Geometry, Set Material (`GeometryNodeSetMaterial`), Set Shade Smooth (`GeometryNodeSetShadeSmooth`), Set Position.

**Distribution** — Distribute Points on Faces (`GeometryNodeDistributePointsOnFaces`), Instance on Points, Realize Instances.

**Curves** — Curve to Mesh (`GeometryNodeCurveToMesh`) — the procedural equivalent of a Bevel Object, and the node that produces skirtings, handrails, gutters and glazing bars.

**Utilities** — Math (`ShaderNodeMath`), Vector Math (`ShaderNodeVectorMath`), Combine XYZ (`ShaderNodeCombineXYZ`), Separate XYZ, Compare, Switch, Random Value, Repeat Zone (`GeometryNodeRepeatInput` / `GeometryNodeRepeatOutput`).

**Attribute** — Capture Attribute, Store Named Attribute, Named Attribute.

Group everything reusable: select nodes, `Ctrl-G`, name it, expose inputs on the group interface. A `Panel` group that takes W/H/T and returns a solid board is worth more than any single graph.

---

## Worked graph 1 — Parametric wall with openings

**Goal.** A straight wall of given length, height and thickness, with an arbitrary number of openings placed by X-offset, width, height and sill height, correctly cut, with a distinct material on the reveals.

**Modifier inputs** (create on the group interface, in order):

| Label | Type | Default |
|---|---|---|
| Length | Float (Distance) | 6.0 |
| Height | Float (Distance) | 2.7 |
| Thickness | Float (Distance) | 0.23 |
| Openings | Object (an object whose vertices mark opening centres) | — |
| Opening W | Float (Distance) | 1.2 |
| Opening H | Float (Distance) | 1.5 |
| Sill H | Float (Distance) | 0.9 |
| Wall Material | Material | — |
| Reveal Material | Material | — |

**Nodes and links.**

1. **Cube** (`GeometryNodeMeshCube`). Size ← Combine XYZ (X = `Length`, Y = `Thickness`, Z = `Height`).
2. **Transform Geometry** #1. Geometry ← Cube. Translation ← Combine XYZ (X = `Length ÷ 2`, Y = 0, Z = `Height ÷ 2`). This puts the wall's origin at its bottom-left-front corner, which is the setting-out convention that matches a survey.
   - Use a **Math (Divide)** node with `Length` and 2.0 for the X term; likewise `Height`.
3. **Object Info** (`GeometryNodeObjectInfo`) with Transform Space = **Relative**. Object ← `Openings`. Its Geometry output is a small mesh whose *vertices* are the opening centre positions — model it as a set of loose vertices in plan.
4. **Cube** #2 — the cutter block. Size ← Combine XYZ (X = `Opening W`, Y = `Thickness + 0.2`, Z = `Opening H`). The +0.2 (a **Math Add** node) makes the cutter overshoot the wall on both faces, which is the single most reliable way to avoid coplanar-face boolean failures.
5. **Transform Geometry** #2. Geometry ← Cube #2. Translation ← Combine XYZ (X = 0, Y = 0, Z = `Sill H + Opening H ÷ 2`). Now the cutter's own origin sits at the opening's plan centre and its base at sill level.
6. **Instance on Points**. Points ← Object Info ▸ Geometry. Instance ← Transform Geometry #2.
7. **Realize Instances**. Geometry ← Instance on Points. (Required: Mesh Boolean cannot consume instances.)
8. **Mesh Boolean** (`GeometryNodeMeshBoolean`), Operation = **Difference**, Solver = **Exact** (switch to **Manifold** once you trust the inputs — it is usually faster). Mesh 1 ← Transform Geometry #1. Mesh 2 ← Realize Instances.
9. **Set Material** #1. Geometry ← Mesh Boolean ▸ Mesh. Material ← `Wall Material`.
10. **Set Material** #2, with a **Selection** field, to paint the reveals. Selection ← Mesh Boolean ▸ **Intersecting Edges**… in practice the simplest reliable route is: Selection ← a **Compare** node testing that the face normal's Z component is near zero *and* the face is not on the outer plane. For a first pass, feed Selection from `GeometryNodeInputNormal` → Separate XYZ → Z → **Compare (Less Than, 0.001, absolute)** combined with a position test. Material ← `Reveal Material`.
11. **Group Output** ← Set Material #2.

**Notes.** Per-opening sizes require the sizes to come from the openings object rather than from single modifier inputs: store `op_w`, `op_h`, `op_sill` as named attributes on the marker vertices (in Edit Mode, via the Spreadsheet or a small script), then read them with **Named Attribute** nodes and wire them into the Combine XYZ feeding the cutter's Size and the Transform's Translation. Because those are fields on the Point domain, Instance on Points evaluates them per point and every opening gets its own dimensions. This is the whole trick, and it generalises to windows, doors and vents in one graph.

---

## Worked graph 2 — Parametric straight staircase

**Goal.** A straight flight from total rise, going, tread thickness and riser count, with correctly proportioned steps and an optional open riser.

**Modifier inputs:** `Total Rise` (2.7), `Total Going` (3.0), `Steps` (Integer, 15), `Tread Thickness` (0.04), `Tread Width` (1.0), `Nosing` (0.025), `Open Riser` (Boolean).

Derived by Math nodes: `Riser = Total Rise ÷ Steps`, `Going = Total Going ÷ Steps`.

> ⚠️ Check the derived riser and going against the building regulation applicable to the project before issuing anything. A generator will happily produce a 240 mm riser.

**Nodes and links.**

1. **Mesh Line** (`GeometryNodeMeshLine`), Mode = **Offset**, Count Mode = **Total**. Count ← `Steps`. Start Location = (0,0,0). Offset ← Combine XYZ (X = `Going`, Y = 0, Z = `Riser`). This creates one point per step, marching up and along.
2. **Cube** — the tread. Size ← Combine XYZ (X = `Going + Nosing`, Y = `Tread Width`, Z = `Tread Thickness`).
3. **Transform Geometry** #1 on the tread: Translation ← Combine XYZ (X = `(Going + Nosing) ÷ 2 − Nosing`, Y = 0, Z = `−Tread Thickness ÷ 2`). This puts the tread's top surface at the point and its nosing projecting backwards over the step below.
4. **Instance on Points** #1. Points ← Mesh Line. Instance ← Transform Geometry #1.
5. **Cube** — the riser. Size ← Combine XYZ (X = 0.018, Y = `Tread Width`, Z = `Riser`).
6. **Transform Geometry** #2 on the riser: Translation ← Combine XYZ (X = 0.009, Y = 0, Z = `−Riser ÷ 2 − Tread Thickness`).
7. **Instance on Points** #2. Points ← Mesh Line. Instance ← Transform Geometry #2.
8. **Switch** (Geometry). Switch ← `Open Riser`. False ← Instance on Points #2. True ← nothing (leave the socket empty). Output feeds the join.
9. **Join Geometry**. Inputs: Instance on Points #1, Switch output.
10. **Set Material**, then **Group Output**.

**Stringers.** Add a second branch: a **Curve Line** from (0, ±Tread Width/2, −0.05) to (`Total Going`, ±Tread Width/2, `Total Rise` − 0.05), fed into **Curve to Mesh** with a **Quadrilateral** profile of 0.05 × 0.25, and joined in. For a cut string, boolean the stair profile out of a solid instead.

**Winders and spirals** are the Screw modifier's territory (file `02`) or a Repeat Zone rotating each tread about a central axis: inside the zone, rotate the accumulated geometry by `360 ÷ Steps` degrees and translate by `Riser`, joining a tread each iteration.

---

## Worked graph 3 — Boundary wall / fence generator along a curve

**Goal.** Drive posts, rails and infill along any drawn curve — the standard Namibian erf boundary condition: plastered masonry piers at centres with panels between, or steel posts with palisade infill.

**Modifier inputs:** `Post Spacing` (2.5), `Post Size` (0.35), `Wall Height` (2.1), `Panel Thickness` (0.22), `Coping Height` (0.06), `Post Material`, `Panel Material`.

The object this modifier sits on is a **curve** drawn along the boundary line, in plan, at ground level.

**Nodes and links.**

1. **Group Input ▸ Geometry** (the boundary curve) → **Resample Curve** (`GeometryNodeResampleCurve`), Mode = **Length**, Length ← `Post Spacing`. This gives evenly spaced control points, one per pier, following the curve exactly including corners.
2. **Cube** — pier. Size ← Combine XYZ (X = `Post Size`, Y = `Post Size`, Z = `Wall Height + Coping Height`).
3. **Transform Geometry** on the pier: Translation Z ← `(Wall Height + Coping Height) ÷ 2`.
4. **Instance on Points** #1. Points ← Resample Curve. Instance ← the transformed pier. **Rotation** ← the curve's **Curve Tangent** (`GeometryNodeInputTangent`) fed through **Align Rotation to Vector** (`FunctionNodeAlignRotationToVector`) with Axis = Z, Pivot Axis = Z. Without this, piers do not turn at corners.
5. **Curve to Mesh** for the infill panel: Curve ← Resample Curve (or the original curve for a smoother panel). Profile Curve ← **Quadrilateral** (`GeometryNodeCurvePrimitiveQuadrilateral`), Mode = Rectangle, Width ← `Panel Thickness`, Height ← `Wall Height`. Fill Caps on.
6. **Transform Geometry** on the panel: Translation Z ← `Wall Height ÷ 2`.
7. **Curve to Mesh** #2 for the coping: same curve, Quadrilateral Width ← `Panel Thickness + 0.06`, Height ← `Coping Height`; Transform Z ← `Wall Height + Coping Height ÷ 2`.
8. **Set Material** on each branch; **Join Geometry**; **Group Output**.

**Variations.**
- *Palisade*: replace step 5 with a second Resample Curve at 0.12 m spacing feeding an Instance on Points of a thin vertical cube; add Random Value on the Z rotation for a hand-built look.
- *Gates*: use a **Selection** on Delete Geometry to remove piers and panel within a range of the curve's **Spline Parameter** (`GeometryNodeSplineParameter` ▸ Length), leaving a gap for the gate.
- *Sloping ground*: run the whole result through **Set Position** with an Offset field sampling a terrain mesh via **Raycast** (`GeometryNodeRaycast`) straight down, so posts follow the ground while the coping steps.

---

## Worked graph 4 — Paver / tile layout distributor

**Goal.** Fill an arbitrary plan boundary with a running-bond paver field of specified unit size and joint width, with per-unit colour variation and correct edge cutting.

**Modifier inputs:** `Paver L` (0.22), `Paver W` (0.11), `Paver T` (0.06), `Joint` (0.003), `Bond Offset` (0.5), `Field Size` (30.0), `Boundary` (Object — a flat mesh describing the paved area).

**Nodes and links.**

1. **Grid** (`GeometryNodeMeshGrid`). Size X ← `Field Size`, Size Y ← `Field Size`. Vertices X ← `Field Size ÷ (Paver L + Joint)` rounded (Math ▸ Divide, then Math ▸ Round, then Float to Integer). Vertices Y ← `Field Size ÷ (Paver W + Joint)` rounded. Set the grid's **Domain** consumer to Face: use **Mesh to Points** (`GeometryNodeMeshToPoints`), Mode = **Faces**, so you get one point at each cell centre.
2. **Capture Attribute** on the points, capturing **Index** (or better, the row number). Row number: **Position** → Separate XYZ → Y → Math ▸ Divide by `(Paver W + Joint)` → Math ▸ Round.
3. **Running bond offset**: Math ▸ **Modulo** (row, 2) → Math ▸ **Multiply** by `Bond Offset × (Paver L + Joint)`. Feed the result into a **Set Position** Offset via Combine XYZ (X = that value, Y = 0, Z = 0). Alternate rows now shift by half a paver.
4. **Cube** — the paver. Size ← Combine XYZ (X = `Paver L`, Y = `Paver W`, Z = `Paver T`).
5. **Instance on Points**. Points ← Set Position output. Instance ← the paver cube.
6. **Random Value** (Float, Min 0, Max 1, Seed = 0), evaluated on the Instance domain → **Store Named Attribute** named `paver_var` on the Instance domain. The material reads this with an **Attribute** node to vary colour per paver — this is how you avoid the tell-tale identical-tile look.
7. **Random Value** (Float, Min −0.5°, Max 0.5° in radians) → **Rotate Instances** (`GeometryNodeRotateInstances`) about Z, plus a small Random Value into **Translate Instances** on Z (±1 mm) so the field is not perfectly flat.
8. **Trim to the boundary.** Two options:
   - *Cheap and correct-looking*: **Delete Geometry** on the Instance domain, Selection ← a **Geometry Proximity** (`GeometryNodeProximity`) test against the boundary object's edges combined with an inside/outside test. Pavers whose centres fall outside are deleted. Edges stay uncut — acceptable where a kerb or edge restraint covers the line.
   - *Accurate*: **Realize Instances**, then **Mesh Boolean ▸ Intersect** with a solid extruded from the boundary object. Correct cut pavers, at the cost of a heavy mesh. Do this on a duplicate at the end, not in the working graph.
9. **Set Material**, **Group Output**.

**Sanity check.** With `Paver L` 0.22, `Paver W` 0.11 and `Joint` 0.003, a 30 × 30 m field is about 30/0.223 × 30/0.113 ≈ 134 × 265 ≈ 35 500 instances. That is fine as instances and catastrophic if realized.

---

## Worked graph 5 — Shelving / wardrobe generator

**Goal.** From external width, height, depth, panel thickness, bay count and shelf count, produce a correct carcass with vertical dividers and shelves, each panel a real board of real thickness.

**Modifier inputs:** `Width` (1.8), `Height` (2.4), `Depth` (0.6), `Panel T` (0.018), `Back T` (0.006), `Bays` (Integer, 3), `Shelves per Bay` (Integer, 4), `Toe Kick` (0.1), `Board Material`.

Derived: `Inner H = Height − Toe Kick − 2 × Panel T`; `Bay W = (Width − (Bays + 1) × Panel T) ÷ Bays`.

Build a reusable **Panel** node group first: inputs W, D, T and a Location vector; internally a **Cube** with Size = Combine XYZ(W, D, T) and a **Transform Geometry** applying Location. Everything below instantiates it.

**Nodes and links.**

1. **Sides.** Panel group with W ← `Panel T`, D ← `Depth`, T ← `Inner H + 2 × Panel T`… in practice it is cleaner to make the Panel group take three *dimensions* (X, Y, Z) and a location. Left side at X = `Panel T ÷ 2`, Z = `Toe Kick + Height_carcass ÷ 2`. Right side at X = `Width − Panel T ÷ 2`.
2. **Top and bottom.** Panel with X-dim `Width`, Y-dim `Depth`, Z-dim `Panel T`; bottom at Z = `Toe Kick + Panel T ÷ 2`, top at Z = `Height − Panel T ÷ 2`.
3. **Back.** Panel with X-dim `Width`, Y-dim `Back T`, Z-dim = carcass height; located at Y = `Depth ÷ 2 − Back T ÷ 2` (i.e. at the rear face). Set its material separately if the back is a different board.
4. **Vertical dividers.** **Mesh Line**, Count ← `Bays − 1`, Mode = Offset, Start = Combine XYZ(`Panel T + Bay W + Panel T ÷ 2`, 0, `Toe Kick + carcass height ÷ 2`), Offset = Combine XYZ(`Bay W + Panel T`, 0, 0). Feed into **Instance on Points** with a divider panel (X-dim `Panel T`, Y-dim `Depth`, Z-dim inner height) as the instance.
5. **Shelves.** Nested distribution. Two clean approaches:
   - *Repeat Zone*: iterate `Bays` times; inside, compute the bay's X centre from the iteration index, build a **Mesh Line** of `Shelves per Bay` points up that bay, instance a shelf panel (X-dim `Bay W`, Y-dim `Depth − Back T`, Z-dim `Panel T`) on it, and **Join Geometry** into the accumulating geometry socket.
   - *Two-stage grid*: build a **Grid** of `Bays` × `Shelves per Bay` cells sized `Width − 2×Panel T` by inner height, take its face centres with **Mesh to Points**, and instance the shelf there. Simpler, but shelf width must then be uniform.
   The Repeat Zone version is the one to build, because it also lets you vary shelves per bay by reading a per-bay attribute.
6. **Toe kick / plinth.** Panel with X-dim `Width`, Y-dim `Panel T`, Z-dim `Toe Kick`, at Y = `−Depth ÷ 2 + 0.05` (set back 50 mm), Z = `Toe Kick ÷ 2`.
7. **Join Geometry** everything → **Set Material** ← `Board Material` → **Group Output**.

**Making it produce a cutting list.** Before joining, run each branch through **Store Named Attribute** writing a String or Integer `part_code` on the Face domain (`1` = side, `2` = top/bottom, `3` = shelf, `4` = divider, `5` = back). After the modifier, the script in file `06` reads the evaluated mesh, groups faces by `part_code`, and computes each part's bounding box — giving a real cutting list from a parametric model. Alternatively, and more robustly, generate the parts as separate objects from Python rather than as one node graph; Geometry Nodes is superb at *showing* the wardrobe and mediocre at *itemising* it.

---

## Driving graphs from Python

```python
import bpy

ng  = bpy.data.node_groups["Wardrobe"]
obj = bpy.data.objects["WD01"]
mod = obj.modifiers.new("Wardrobe", 'NODES')
mod.node_group = ng

# map human labels -> socket identifiers once
ids = {it.name: it.identifier
       for it in ng.interface.items_tree
       if getattr(it, "in_out", None) == 'INPUT'}

mod[ids["Width"]]  = 1.800
mod[ids["Height"]] = 2.400
mod[ids["Bays"]]   = 3
obj.update_tag()
bpy.context.view_layer.update()
```

Never hard-code `"Socket_2"`. Socket identifiers are stable for an existing group but are assigned in creation order, so the label→identifier map above is the only safe addressing scheme. Full node-graph construction from scratch in Python is covered in file `06`.

## Practical guidance

- **Name every node group and every socket** the way a drawing schedule would. `Wall_Straight_v3` beats `Geometry Nodes.004`.
- **Set socket subtypes.** A Float socket with subtype `DISTANCE` displays and accepts metres/millimetres in the modifier panel. Without it you get raw floats and unit errors.
- **Set min/max on inputs** so a wall thickness cannot be typed as −0.23.
- **Mark node groups as assets** (right-click ▸ Mark as Asset) and keep them in a project asset library so every file in the job shares one wall generator.
- **Keep instances until the last moment.** Realize only for boolean, export or measurement.
- **Watch the modifier evaluation time.** `Modifier ▸ dropdown ▸ Execution Time` shows per-modifier cost; the Spreadsheet shows element counts.
- **Node Tools** (Geometry Nodes run as operators from the 3D Viewport menus) are worth knowing for repetitive edits — a "bevel all vertical arrises 0.5 mm" tool applied to a selection.

## Sources

- [Manual — Geometry Nodes index](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/index.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — Instance on Points](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/instance_on_points.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Realize Instances](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/realize_instances.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Mesh Boolean node](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/mesh/operations/mesh_boolean.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Repeat Zone](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/utilities/repeat_zone.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Capture Attribute / Store Named Attribute / Named Attribute](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/attribute/index.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Import nodes (STL/OBJ/PLY)](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/input/import/stl.html) — accessed 2026-08-25 via the local manual bundle
- [API — `bpy.types.NodeTreeInterface`](https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html) — accessed 2026-08-25 via the local API bundle
- [Blender 5.0 release notes (Bundles, Closures, node-based modifiers)](https://www.blender.org/download/releases/5-0/) — accessed 2026-08-25

## Open questions

- All node identifiers used above (`GeometryNodeObjectInfo`, `GeometryNodeResampleCurve`, `GeometryNodeInputTangent`,
  `FunctionNodeAlignRotationToVector`, `GeometryNodeSplineParameter`, `GeometryNodeRaycast`, `GeometryNodeProximity`,
  `GeometryNodeMeshToPoints`, `GeometryNodeRotateInstances`) were confirmed against the manual's reference labels.
  `GeometryNodeRepeatOutput` and `GeometryNodeSeparateGeometry` were not individually confirmed — check with
  Python Tooltips before scripting them.
- The reveal-material selection in graph 1 (step 10) is described as a strategy rather than an exact wiring; the robust production approach is to assign reveal material inside the opening cutter and use Mesh Boolean's `Materials: Transfer` option instead.
