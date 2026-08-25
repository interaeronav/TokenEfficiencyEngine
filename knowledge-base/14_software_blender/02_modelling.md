---
id: blender.modelling
title: Mesh modelling for architecture and joinery in Blender
domain: software_blender
tags: [blender, modelling, modifiers, array, mirror, solidify, bevel, boolean, screw, subdivision, weld, remesh, snapping, precision, curves, carcass, joinery]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; valid for 4.5 LTS except the Manifold boolean solver"
unit_system: metric
sources:
  - {title: "Blender Manual — Boolean Modifier", url: "https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Solidify Modifier", url: "https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/solidify.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Screw Modifier", url: "https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/screw.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Bevel", url: "https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bevel.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Transform Modal Map (snapping)", url: "https://docs.blender.org/manual/en/latest/modeling/transform/modal_map.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Python API — ArrayModifier", url: "https://docs.blender.org/api/current/bpy.types.ArrayModifier.html", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.interface_core_concepts, blender.geometry_nodes, blender.python_api, joinery.cabinetmaking]
---

# Mesh modelling for architecture and joinery in Blender

**Summary.** Blender models buildings and cabinetry as polygon meshes, but the discipline that makes it CAD-accurate is not in the mesh tools — it is in typing exact numbers, snapping to real geometry, and pushing as much construction as possible into a non-destructive modifier stack. A well-built wardrobe in Blender is a handful of flat panels driven by Solidify, Array and Mirror, with a Boolean cutting the service voids, and every dimension typed as a millimetre value. This file covers topology, the modifier stack in the order it should be used, precision entry, curves for mouldings, and the carcass conventions that let a model produce a real cutting list.

## Key facts

| Item | Value |
|---|---|
| Modifier stack evaluation | Top to bottom; order changes the result |
| Add modifier (Python) | `obj.modifiers.new(name, type)` with types `'ARRAY'`, `'MIRROR'`, `'SOLIDIFY'`, `'BEVEL'`, `'BOOLEAN'`, `'SCREW'`, `'SUBSURF'`, `'WELD'`, `'REMESH'`, `'TRIANGULATE'`, `'NODES'` |
| Reorder modifier | `obj.modifiers.move(from_index, to_index)` |
| Boolean solvers | **Float** (fast, no overlapping geometry), **Exact** (best, slow, handles overlap), **Manifold** (usually fastest, manifold meshes only) |
| Solidify modes | **Simple** (extrude; fails where an edge has >2 adjacent faces) and **Complex** (guarantees manifold output; the manual names "architectural wall layouts" as a target case) |
| Solidify thickness caveat | Computed from **local** vertex coordinates — non-uniform object scale produces uneven thickness. Apply or clear scale. |
| Bevel width types | Offset, Width, Depth, Percent, Absolute |
| Screw modifier fields | Angle (degrees per revolution), Screw (height per iteration), Iterations, Axis, Steps Viewport / Render, Merge |
| Snap toggle | `Shift-Tab`; hold `Ctrl` during a transform to snap momentarily |
| Numeric entry | Type a number during any transform; `Tab` moves between axis fields; expressions and units accepted (`2400/3`, `18mm`) |
| Dimensions readout | `N` sidebar ▸ Item ▸ Dimensions |
| Edit-mode measurement overlay | Overlays ▸ Measurement ▸ Edge Length / Face Angle / Face Area |

## Topology principles for this kind of work

Architectural and furniture geometry is overwhelmingly flat, rectilinear and hard-edged. That changes the usual advice.

- **Quads are preferred but not sacred.** Quad-only topology matters when you subdivide or deform. A cabinet side panel is a flat rectangle; an n-gon is fine and often cleaner. Where you *do* use Subdivision Surface (a moulded door, a shaped handle, upholstery), quads become mandatory.
- **Never leave interior faces.** Two boxes butted together and joined leave hidden coincident faces that produce z-fighting, break booleans and inflate the cutting list. Use Boolean Union with the Exact solver, or model the join properly.
- **Manifold matters more than beauty.** Every solid you intend to export to STL, DXF or a CAM package must be watertight: every edge bordered by exactly two faces, all normals outward. `Mesh ▸ Normals ▸ Recalculate Outside` (`Shift-N`) and the Statistics overlay are the routine checks. The **Manifold** boolean solver, the fastest of the three, only works on manifold input — a good reason to keep meshes clean.
- **Scale must be applied.** Non-uniform object scale corrupts Solidify thickness, Bevel width, Array offsets and every exported dimension. `Ctrl-A ▸ Scale` after any object-level scaling, or better, never object-scale at all.
- **Edge flow is for bevels, not for beauty.** The reason to add supporting loops around a panel edge is so a Bevel or Subdivision produces a crisp arris rather than a mushy one.
- **Density budget.** A wall with an opening needs about 12 vertices, not 12 000. Keep the source mesh minimal and let modifiers generate the detail; the depsgraph regenerates it every frame, and a 40-object house at 200 verts each is instantaneous while the same house pre-subdivided is not.

## The modifier stack, in the order it should be used

The stack is a construction sequence. A workable default order for a joinery or building element:

```
1. Mirror            symmetry first, so everything downstream is symmetric
2. Array             repetition second
3. Screw             (only for helical/turned/revolved parts — replaces 1-2)
4. Boolean           cut openings and joints into the assembled form
5. Solidify          give thickness to surfaces
6. Weld              merge the seams the above created
7. Bevel             break the arrises last, so bevels are not arrayed or duplicated
8. Subdivision       smoothing last of all (rarely used here)
9. Triangulate       only immediately before export, if the target demands it
```

There are legitimate reversals — Solidify before Boolean when you are cutting *through* a thickened wall, Bevel before Boolean when the cutting tool itself must have a rounded edge — but if you cannot articulate why you deviated, use the order above.

### Array

Duplicates the mesh at a regular offset. Three fit types: **Fixed Count**, **Fit Length** (duplicate as many times as fit a given length), **Fit Curve** (fit along a curve object).

Offsets stack additively:

- **Relative Offset** — a multiple of the object's bounding box (`relative_offset_displace`, default `(1,0,0)`). Convenient, but it changes when the mesh changes. Avoid for dimensioned work.
- **Constant Offset** — an absolute distance in metres (`constant_offset_displace`). **Use this.** For 200 mm-wide slats at 250 mm centres, set Relative Offset off and Constant Offset X = `0.25`.
- **Object Offset** — take the transform of another object (usually an Empty) as the step. Rotation included, so this is how you array balusters around a curved stair or fence panels around a corner.

`Merge` (`use_merge_vertices`) with a small `merge_threshold` welds neighbouring copies — essential for a continuous handrail, wrong for discrete fence pickets. `Start Cap` / `End Cap` accept mesh objects for the first and last element, which is how you terminate a run of shelves with a different end panel.

> Gotcha: Array + Bevel in the wrong order bevels the *source* mesh and then arrays the bevelled result, which is what you want; Array *after* Bevel with merge on can produce doubled bevel geometry at the seams. Keep Bevel last.

### Mirror

Reflects across one or more local axes about the object origin (or about a **Mirror Object**'s origin, which is the correct approach for a building symmetric about a grid line rather than about its own origin). `use_clip` prevents vertices crossing the mirror plane — indispensable when hand-editing. `use_mirror_merge` with `merge_threshold` closes the seam. Bisect and Flip options control which half survives.

For joinery, mirror a single cabinet side to get both sides, then place the origin exactly on the carcass centre line. For a house, use a Mirror Object empty on the axis of symmetry.

### Solidify

Turns a surface into a solid of given thickness. This is *the* architectural modifier: draw a wall as a flat plane or a single-thickness ribbon in plan, then Solidify to 230 mm.

- **Mode: Simple** extrudes along normals. Fast. Fails where an edge has more than two adjacent faces — i.e. at a wall junction where three walls meet.
- **Mode: Complex** guarantees manifold output and, in the manual's own words, handles "architectural wall layouts". Slower. Use it the moment your wall network has T- or cross-junctions.
- **Thickness** is in metres; `0.23` for a 230 mm wall, `0.016` for 16 mm melamine, `0.018` for 18 mm MDF.
- **Offset** ranges −1 to 1 and positions the solid relative to the original surface: `-1` = all thickness on the negative-normal side, `0` = centred, `1` = all on the positive side. For a wall drawn on its **inner face line**, use Offset `1` or `-1` (whichever pushes the material outward) so the drawn line stays the setting-out line. This single setting is what makes a Blender wall agree with a survey.
- **Rim ▸ Fill** closes the ends. Leave it on unless you know you want an open shell.
- Thickness is calculated in **local coordinates**: if the object has non-uniform scale, thickness varies per side. Apply the scale.
- Complex mode has three **Thickness Modes**: Fixed, Even, Constraints. Constraints is the most accurate for up to three meeting faces; use it for junction-heavy wall layouts.

### Bevel

Rounds or chamfers edges. Parameters that matter:

- **Width Type**: `Offset` (distance from the original edge along each face — the intuitive one), `Width`, `Depth`, `Percent`, `Absolute`.
- **Amount**: real distance. A machined MDF arris is 0.5–1 mm; a solid-timber eased edge is 2–3 mm; a bullnose worktop is 10–20 mm with 8+ segments.
- **Segments**: 1 for a chamfer, 3–8 for a radius.
- **Limit Method**: `Angle` (default 30°) bevels only edges sharper than the threshold — right for whole-object edge breaking; `Weight` uses per-edge bevel weight so you control exactly which arrises are eased; `Vertex Group`; `None`.
- **Clamp Overlap** prevents a bevel overshooting a short edge and self-intersecting. Leave on.
- **Harden Normals** assigns custom split normals so the bevel shades smoothly without smoothing the whole panel — the standard trick for realistic sheet-goods edges.
- **Miter Outer / Inner** (`Sharp` / `Patch` / `Arc`) control corner geometry where three or more bevelled edges meet. `Arc` outer miters give the cleanest cabinet corners.

Every visible edge in a render needs *some* bevel. A perfectly sharp 90° arris catches no light and reads as CG immediately. 0.5 mm with 2 segments on everything is a good baseline.

### Boolean

Difference, Union or Intersect against another object or a whole collection.

- **Solver: Exact** — the workhorse. Handles overlapping geometry, has `Self Intersection` and `Hole Tolerant` sub-options for dirty meshes, and `Materials` handling (`Index Based` or `Transfer`) that determines which material lands on the newly cut faces. Use `Transfer` when the cutter carries the reveal material.
- **Solver: Manifold** — usually the fastest, but requires manifold inputs (plus the special case of Difference with a plane). Try it first on clean geometry.
- **Solver: Float** — fast, no overlap support, and Intersect is not allowed with a Collection operand.
- **Operand Type: Collection** — point one Boolean modifier at a collection of cutters. This is the correct way to punch a house full of window and door openings: one `Boolean` modifier on the wall object, one collection `Cutters_Openings` holding a box per opening. Add an opening by adding a box to the collection. With the Exact solver the collection may even be empty, in which case the modifier just removes self-intersecting interior geometry — a useful cleanup.
- Set cutter objects' viewport display to `Bounds` or `Wire` and disable their render visibility so they do not clutter the scene.

> ⚠️ Boolean is the most common source of broken geometry in architectural Blender files. Before blaming the solver: check both meshes are manifold, have consistent outward normals, have applied scale, and do not have coplanar faces exactly touching. Offset a cutter by 1 mm beyond the surface rather than ending it exactly flush.

### Screw

Revolves a profile around an axis. `Angle` = degrees per revolution (360 for a full lathe turn), `Screw` = rise per revolution (0 for a lathe, non-zero for a helix), `Iterations` = number of revolutions, `Steps Viewport` / `Steps Render` = tessellation. The manual notes the profile should be aligned to the object's cardinal direction, not to the screw axis.

Uses here: turned legs and finials from a drawn half-profile; a spiral staircase stringer (Angle 360, Screw = total rise per turn, Iterations = turns); threaded fixings; a rolled-steel section swept along a helix.

### Subdivision Surface

Catmull-Clark smoothing. Rare in architecture, occasionally essential for: shaped door rails and stiles, upholstered seating, curved reception counters, moulded handles. Requires quads and supporting loops. Keep `Levels Viewport` low (1) and `Render` at 2–3.

### Weld

Merges vertices within a distance. Two placements matter: after Array with merge disabled when you want control over the threshold, and after Boolean to clean up near-coincident vertices before Bevel. `merge_threshold` of `0.0001` (0.1 mm) is a safe default for joinery — large enough to catch float noise, small enough not to collapse a real 0.5 mm gap.

### Remesh

Rebuilds topology. `Voxel` mode is the useful one: it produces a uniform manifold mesh at a chosen voxel size, destroying all detail smaller than that. For this domain it is a repair tool of last resort — for example, salvaging a downloaded model that will not boolean. `Adaptivity` reduces polygon count on flat areas. Never use it on geometry whose dimensions must survive; voxelisation moves every vertex.

## Precision modelling: exact dimensions and snapping

**Typed transforms.** Press `G`/`R`/`S`, then an axis key (`X`/`Y`/`Z`, or `Shift-Z` for "in the XY plane"), then type the number. `G Y 2.4 Enter` moves 2.4 m along +Y. Type `-` to negate, `Tab` to jump between axis fields, and full arithmetic is accepted: `G X 2400/3 Enter`. With `length_unit` set to millimetres you can type `G X 18 Enter` and get 18 mm.

**The N-panel.** `N` ▸ Item shows Location, Rotation, Scale and **Dimensions** for the active object, and, in Edit Mode, the median or individual coordinates of the selection. Click any field and type an exact value, including units and expressions. This is where you verify that a cabinet is exactly 600 × 580 × 720 and not 599.7.

**Snapping.** `Shift-Tab` toggles it; the magnet dropdown in the header chooses targets: Increment, Vertex, Edge, Face, Face Project, Edge Center, Edge Perpendicular, Volume. Hold `Ctrl` during a transform to snap momentarily without toggling the global setting.

- **Increment** with *Absolute Grid Snap* enabled snaps to world grid multiples rather than to relative steps — set the grid to 100 mm and every move lands on a 100 mm module.
- **Vertex / Edge Center / Edge Perpendicular** are how you place joinery against real building geometry.
- **Snap Base** (`B` during a transform, per the transform modal map) lets you nominate the point on the moving object that will be snapped, instead of its origin — the difference between "put this cabinet's corner on that wall corner" and "put its origin somewhere near it". Press `A` on a highlighted snap target to mark it; with several marked, the selection snaps to their average.
- `Snap With: Closest / Center / Median / Active` further refines the source point.

**Other precision tools.** `Shift-S` (Snap pie) moves the cursor or selection to exact places (Cursor to World Origin, Selection to Cursor, Cursor to Selected). The 3D cursor is a placement datum: put it on a wall corner, then `Shift-A` adds new objects there. `Ctrl-Shift-Alt-C`-era origin operations now live under `Object ▸ Set Origin` — *Origin to 3D Cursor* is how you give a cabinet a sensible datum (front-bottom-left corner is the joinery convention).

**Edit-mode essentials.** `E` extrude (then axis + number), `I` inset (then number; `I I` for per-face), `Ctrl-R` loop cut (scroll for count, then `Right-click` to leave centred, or slide and type a number), `Ctrl-B` bevel, `K` knife (hold `Ctrl` to snap to midpoints, `Z` to cut through), `J` connect vertices, `F` make face, `M` merge, `Alt-M` split, `P` separate, `Ctrl-J` join. `Ctrl-Numpad+/-` grows and shrinks the selection. `Shift-N` recalculates normals outward.

## Non-destructive workflow discipline

Keep the parametric intent alive as long as possible:

1. Model the **profile or footprint** as the smallest possible mesh or curve.
2. Express thickness, repetition and symmetry as **modifiers**, not as geometry.
3. Keep **cutters in a dedicated collection**, excluded from render.
4. Store the **driving numbers as custom properties** on the object (`obj["panel_t"] = 0.018`) and, where it pays, wire them to modifier fields with **drivers** so one edit propagates.
5. Apply modifiers only at the export boundary, on a duplicate, never on the master.

Drivers are the cheap route to parametrics without Geometry Nodes: right-click a modifier field ▸ *Add Driver*, set the driver to a Single Property pointing at `["panel_t"]` on the same object. One custom property then controls Solidify thickness, an Array offset and a Boolean cutter's dimension simultaneously. For anything more ambitious, move to Geometry Nodes (file `03`).

## Curves for mouldings, skirtings and handrails

Curve objects (Bézier or NURBS) plus two settings generate swept profiles without any mesh modelling:

- **Bevel Object** — point a path curve at a second, closed curve that describes the section. That is a skirting, an architrave, a cornice, a handrail, a window bead, a picture rail. Draw the profile once at true size in the XY plane, then reuse it on every run.
- **Taper Object** — a third curve scaling the section along the path.
- **Bevel ▸ Round / Object / Profile** — the built-in `Round` bevel with a Depth gives a simple rod (handrail, conduit, reinforcing bar) with no second curve at all.
- **Extrude** — a flat ribbon of given half-width.
- **Fill Caps** — closes the ends.
- **Resolution Preview U / Render U** — tessellation. Keep preview low.

Practical notes for joinery: draw the moulding profile in millimetres, with the origin at the wall-and-floor corner of the section, so that placing the path at floor level puts the skirting exactly where it belongs. Curves respect the same snapping as meshes. `Object ▸ Convert ▸ Mesh` bakes the sweep when you need to export or boolean it. For mitred internal and external corners, sweep a single continuous curve around the room rather than butting separate runs — the sweep miters itself.

SVG import (file `07`) brings a drawn profile straight from Inkscape or a manufacturer's detail as a curve, at which point it becomes a Bevel Object.

## CAD-accurate practice for joinery

The model is only useful if it can be read as a cutting list and a set of joints. Conventions that make that possible:

**Panel thicknesses.** Model at real board thickness, never nominal-rounded: 16 mm and 18 mm melamine-faced chipboard, 18 mm MDF, 12 mm and 18 mm birch ply, 6 mm hardboard or 3.2 mm ply backs, 20–40 mm solid timber. Store the value as a custom property and drive Solidify from it, so switching a job from 16 to 18 mm is one edit.

**Carcass construction.** Decide and stick to one system:

- *Butt-and-dowel / confirmat*: sides run full height, top and bottom rails sit **between** the sides. Internal width = external width − 2 × panel thickness.
- *Top-over-side*: top laps over the sides. Height arithmetic changes accordingly.
- Back: either a 3–6 mm panel in a groove set in from the rear edge, or a full rebated back. Model the groove only if you will CNC from the model.

Whichever you choose, **model each panel as its own object**, named systematically (`WD01_Side_L`, `WD01_Top`, `WD01_Shelf.001`), each a flat rectangle with Solidify, each with its origin at a repeatable corner, and each with a custom property carrying grain direction and edging. That naming plus `to_mesh()` bounding-box measurement is exactly what the cutting-list script in file `06` consumes.

**Joints.** Model joints only to the depth your downstream process needs:

- For *visualisation*, do not model joints at all — a 0.5 mm bevel on the arris reads as a joint line.
- For *shop drawings*, model the visible geometry: rebates, grooves, mitres, exposed dovetails.
- For *CNC*, model every machining operation as a Boolean cutter with real tool geometry, including the corner radius a router bit actually leaves (a 6 mm cutter cannot produce a sharp internal corner — model a 3 mm radius or a dog-bone relief).

**Gaps and tolerances.** Real cabinetry has 2–3 mm gaps between doors, 1 mm shadow gaps at scribes, and 10–20 mm of scribe allowance against a wall that is never straight. Model them. A drawing with zero clearance is a drawing that cannot be built, and a render with zero door gaps looks like plastic.

**Hardware.** Model hinge cup bores (35 mm diameter, typically 12.5 mm deep, 4–6 mm from the door edge) and drawer-runner screw positions as Boolean cutters in a `Cutters_Hardware` collection if you will machine from the model; otherwise place low-poly hardware proxies as linked duplicates or collection instances so a change to the hinge model updates all 40 of them.

**Verification.** Before issuing anything, check: applied scale on every object; all normals outward; no interior faces; N-panel Dimensions matching the schedule; and, for fabrication, the mesh statistics showing a manifold result. A quick script that walks every object in the joinery collection and prints `dimensions` in millimetres catches more errors than any amount of visual inspection.

## Sources

- [Manual — Boolean Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — Solidify Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/solidify.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Screw Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/screw.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Bevel (tool options, shared with the modifier)](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/bevel.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Transform Modal Map: snapping and Snap Base](https://docs.blender.org/manual/en/latest/modeling/transform/modal_map.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Mesh Analysis (thickness / overhang checks for fabrication)](https://docs.blender.org/manual/en/latest/modeling/meshes/mesh_analysis.html) — accessed 2026-08-25 via the local manual bundle
- [API — `bpy.types.ArrayModifier`](https://docs.blender.org/api/current/bpy.types.ArrayModifier.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.types.ObjectModifiers.new`](https://docs.blender.org/api/current/bpy.types.ObjectModifiers.html) — accessed 2026-08-25 via the local API bundle

## Open questions

- The exact default `merge_threshold` on the Weld modifier is not restated here from source; the 0.1 mm figure given is a working recommendation, not a documented default.
- Hinge cup bore dimensions (35 mm × ~12.5 mm) are industry-standard European hardware figures carried over from the joinery domain, not sourced from Blender documentation — confirm against the specific hardware manufacturer's data sheet before machining.

