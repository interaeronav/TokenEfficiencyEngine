# Advanced Blender lessons through TEE

TEE now provides nine executable Blender lessons: the six mechanical studies
previously demonstrated in Fusion, a compact modern house, a texture workshop,
and a dedicated woven-fabric study. Each lesson exposes separate build, revision
and inspection stages through the existing Blender guide. The programs create
native editable meshes, retained cutters, drivers and materials in their own
named collections.

These are original authored examples for an AI to study and replay. They do not
train a separate model or establish independent agent performance. Blender
meshes approximate curved CAD surfaces; mesh exchange files do not retain the
feature history carried by an editable `.blend`.

Open the [editable lesson library](../output/blender-lessons/TEE_Blender_Lessons_With_Fabric.blend)
or the [rendered gallery and individual files](../output/blender-lessons/index.html).
All nine lessons passed guarded execution, driven revisions, native save/reopen
and independent geometry export checks on **Blender 5.2.0 LTS**. The minimum-version
check does not establish compatibility with every later build.
The [dated delivery evidence](../output/blender-lessons/delivery.json) records
accepted cases, native reopen checks, independent geometry exports and timings.

## Choose a lesson

| Guide topic | Build and driven revision | Evidence to inspect |
| --- | --- | --- |
| `cadagent_enclosure` | Open 120 × 80 × 30 mm enclosure, 3 mm shell and fifteen 6 mm vents; grow width to 140 mm and height to 40 mm. | The centred vent grid moves +10 mm in x; all fifteen full inner walls, shell volume, bounds and dependencies remain valid. |
| `cadagent_flange` | Stepped flanged hub with a 12 mm centre bore and six 6 mm mounting holes on a 60 mm pitch circle; grow them to 16 and 8 mm. | All seven real bores, their complete inner walls, overall dimensions and retained diameter drivers. |
| `cadagent_joint` | A 60 × 12 × 4 mm lever over a 40 × 30 × 8 mm base with a 2 mm gap; sweep 0/45/90/0/45°. | Evaluated world coordinates, individual volumes and clearance at every pose. A frozen driver fails even if its last pose looks right. |
| `cadagent_f1_wing` | Two authored faceted airfoil sections with a hinged flap; a common span grows from 1 to 1.2 m and the flap command becomes 25°. | Both span dependencies, signed flap motion, transformed section vertices and conservative clearance over the continuous movement. |
| `cadagent_f1_brake` | A 280 mm outside/180 mm inside diameter disc, 28 mm thick, with sixty radial passages in two staggered rows; row diameters grow from 6/6 to 7/8 mm. | Actual passage openings, row dimensions, evaluated material volume, closed mesh and independent diameter drivers. |
| `cadagent_f1_wishbone` | Triangular lightened web with three integral bosses and stepped mounting bores; web thickness grows 6→8 mm and boss height 20→24 mm. | The lightening cut remains through, mounting bores change with the controls, and evaluated dimensions/volume remain within the declared mesh bound. |
| `house` | A compact modern 10 × 8 m house with living/kitchen area, bedroom, bathroom, openings and a sloping roof; widen it to 11.2 m, move a room partition and enlarge a window/roof overhang. | Room and opening dimensions, partition/floor dependencies, roof geometry and the rendered layout. |
| `textures` | Brick, carbon-weave and UV/normal-map studies; revise texture scale, roughness, weave pitch and image repeat size. | Coordinates and UV orientation, physical scale, shader links, colour/data spaces, packed assets and actual before/after appearance. |
| `fabric` | Two 450 × 600 mm flat-pattern swatches displayed as authored folds; change checker cell width 4→6 mm, roughness, sheen weight and sheen roughness. | Metre UV edge lengths on every base triangle, unchanged geometry, active shader links/drivers and before/after fabric appearance. |

The F1 examples share the authored geometry and intent of the
[Fusion F1 studies](cadagent-f1-fusion.md). The airfoil is a faceted reference
section, and the brake and wishbone are modelling studies. No aerodynamic,
braking, structural, material layup or competition-compliance result is claimed.
The house is an authored concept, with no structural, services, building-code or
weatherproofing verification.

## Run a complete lesson

Use the verified **Blender 5.2.0 LTS** build and a dedicated lesson scene.
The programs refuse versions below 5.2; later versions require their own replay
checks. The mechanical programs use metres directly, with scene unit scale 1.0: **120 mm = 0.12 m**.
Blender transforms use radians; the named angle controls are explicitly degrees
and their drivers perform the conversion. Do not copy Fusion's numeric
millimetres directly into Blender coordinates.

1. Request the short overview with `lane_guide(adapter="blender", topic="house")`
   or another table topic. The default index and overviews do not load a program.
2. Discover `bl_execute_python` through TEE's existing tool discovery. Python
   execution remains subject to the existing host policy and version guard.
3. Request `house.build`, then send the returned `call.name` and `call.args` to
   `tee_call` unchanged. The card contains the complete standalone program,
   a source hash and the requested final stage call.
4. Request and execute `house.inspect`. Read its measured checks and `passed`
   result. A successful build reply or an object count alone is insufficient.
5. Request `house.revise`, then execute `house.inspect` again. Inspect the changed
   geometry and its dependencies; a stored parameter value alone is insufficient.
6. Save an editable `.blend`, reopen it and run inspection again. Render meaningful
   views and inspect their appearance. Keep the controls, cutters and materials
   in the saved file. Exchange exports are additional geometry deliverables.

For an AI client, the call sequence is:

```python
# Client-side pseudocode: card/reply are returned structured data, not Blender names.
for stage in ("build", "inspect", "revise", "inspect"):
    card = tee_call(
        name="lane_guide",
        args={"adapter": "blender", "topic": f"house.{stage}"},
    )
    reply = tee_call(name=card["call"]["name"], args=card["call"]["args"])
    # Check each reply before advancing; inspect must report passed=True.
```

Choose the full topic before adding the stage: for example,
`cadagent_f1_brake.revise`, `textures.inspect` or `fabric.inspect`. A source
program is fetched only for an explicit stage. The complete stage belongs in `bl_execute_python`; typed
`lane_preflight` accepts operation lists and does not validate these Python
programs. No new always-loaded tool is added.

The existing desktop TEE connection was measured with the earlier eight-lesson
index on 2026-09-10. Restart or reconnect that TEE server to expose `fabric`;
new source servers load the nine-lesson catalogue.

Build refuses when its lesson collection already exists. To examine an existing
delivery file, start with `.inspect`; use `.revise` to replay its declared edit.
Do not reset the scene or delete unrelated objects to make a repeated build pass.
The programs identify their owned data explicitly and leave other collections
and materials alone.

## What the mechanical lessons teach

The enclosure keeps wall thickness independent of its outside dimensions. Its
interior cutter and vent positions follow the control Empty through drivers;
retaining those cutters is what makes the revision editable. The flange separates
its two diameter controls, so changing one mounting-hole parameter changes all
six cuts. The joint compares the actual transformed long-edge endpoint, which
proves rotation direction as well as bounding-box dimensions.

Inspection measures evaluated meshes, including unapplied Boolean modifiers.
The enclosure and flange compare every angular strip of each inner bore wall,
its area and its two rim planes. A later Boolean can split one original polygon
side into several faces, so raw face counts do not define a complete bore.

The returned mesh error bound is part of the evidence. A cylinder represented
by a regular polygon differs from a true circular cylinder even when Blender's
Boolean solver is called `EXACT`. The enclosure and flange derive their curved
area difference from `sin(2π/N)/(2π/N)` and add a stated floating-point allowance.
The F1 examples carry their own mesh resolution and measured checks. These are
not interchangeable with the Fusion BRep/STEP accuracy gates.

## House design

The house keeps living/kitchen space, bedroom and bathroom distinct, with a real
entrance, window openings, glazing, interior door gaps and a sloping roof. The
revision changes overall width from 10 to 11.2 m, the room divider, front window
width to 2.5 m, and roof overhang to 0.6 m. Inspect the opening geometry and room
relationships after resizing instead of trusting the control values.

Use both an exterior view and an interior or roof-hidden view to judge the
layout. Keep the roof object in the editable file: hiding a roof for inspection
is a presentation choice, not a reason to remove it from the model. The lesson
teaches connected dimensional decisions; it is not a permit drawing or a
construction specification.

## Texture skills

The workshop demonstrates three complementary workflows:

- **Procedural brick:** coordinates tied to a metre-scale reference object;
  240 × 75 mm authored brick dimensions, mortar and bump. Raising the scale
  control to 1.25 produces 192 × 60 mm bricks, while roughness changes from
  0.62 to 0.48. Judge both repetition size and response to lighting.
- **Carbon weave study:** explicit UV tangent direction, alternating fibre
  direction, shallow relief and a coated surface. The teaching pitch changes
  from 24 to 32 mm and roughness from 0.30 to 0.22. The enlarged pattern makes
  the mechanism visible; it is not a measured fibre/BRDF or laminate model.
- **Image colour and tangent normals:** authored orientation pixels use `sRGB`;
  the tangent normal image uses `Non-Color` data and a Normal Map node tied to
  `LessonUV`. Both images are generated locally and packed inside the blend.
  Repeat size changes from 0.25 to 0.40 m without changing object geometry.

The texture inspection checks node links, UV orientation, physical scale,
colour/data spaces and portable packed images. Those checks establish a coherent
shader setup; they do not grade visual quality. Inspect matched before/after
renders under the same lighting, then reopen the `.blend` and render again to
confirm the appearance survives independently of external image files. Material
names alone prove neither wiring nor appearance.

## Fabric skills

The dedicated `fabric` lesson presents linen-coloured and indigo-cotton-coloured
woven studies. Each begins with a **450 × 600 mm flat pattern** and a 32 × 40
cell grid, triangulated into 2,560 base faces. An authored sequence of fold
angles positions the vertices while preserving the pattern's edge lengths;
inspection compares the 3D and metre-based `FabricUV` lengths on every triangle.
The quoted width is the flat-pattern width, not the narrower folded bounding box.

Crossing warp and weft nodes provide woven colour and bump relief. A Principled
shader supplies the grazing-angle sheen. Both swatches share controls that change
checker cell width **4→6 mm**, roughness **0.65→0.45**, sheen weight **0.30→0.60**
and sheen roughness **0.70→0.40**. The full two-colour repeat is therefore
**8→12 mm**; the control named `pitch` denotes one checker cell. The revision
keeps the actual geometry unchanged, checked by a geometry signature. The enlarged weave makes the lesson readable;
its cell width and shader values are authored choices, not measured textile data.

Inspect the active UV route, complete shader links and all eight live shader
drivers, then compare matched rendered views. The geometry is an authored drape
study, **not a cloth simulation**: no gravity, elasticity, collision response or
calibrated textile mechanics are solved. The 1 mm Solidify modifier provides
closed presentation geometry and remains editable; it does not certify actual
fabric thickness. These procedural materials remain complete in the native blend.

## Files and validation

- [Editable library with fabric](../output/blender-lessons/TEE_Blender_Lessons_With_Fabric.blend):
  the native lesson scenes, geometry, controls and authored materials.
- [Rendered gallery](../output/blender-lessons/index.html): individual `.blend`
  and `.glb` files, the house interior view, and material revision previews.
- [Delivery evidence, 2026-09-10](../output/blender-lessons/delivery.json): accepted
  lesson records, source/file hashes, native measurements, PLY and GLB checks,
  preservation evidence and timing scope. Follow the per-case evidence links for
  complete readbacks; timings come from individual successful runs.

The accepted cases cover **61 exported meshes**. Their successful individual
runs total **108.258 s**, including exports, readbacks and renders; measured
build/revision/inspection stages account for **21.365 s**. This is a sum of
separate successful cases, not a single uninterrupted suite. Subsequent inspector
and gallery checks are recorded separately in the evidence.

**GLB checks establish geometry only.** Bounds, mesh inventory, volume and
orientation are independently checked. Procedural Blender shader appearance is
unbaked and unverified in GLB; PLY is also a geometry deliverable. Use the native
`.blend` for complete materials, packed images, drivers and retained modifiers.
Matching an exported mesh does not establish matching material appearance.

The standalone sources are packaged under
`server/src/tee/adapters/blender/recipes/`. The offline gates are in
`server/tests/test_blender_lessons.py`; they check lazy disclosure, fixed resource
paths, invalid-stage refusal before file I/O, source hashes, version guards,
server import isolation and definition-only program loading. Native geometry,
reopen and rendering evidence is recorded separately by the live harness.

TEE's [local continuous learning](continuous-learning.md) records these tool
executions and accepts separate quality feedback on the result. The lesson
inspector's `passed` field remains a geometry or shader check; a successful tool
call does not by itself establish that the result meets the user's design brief.
