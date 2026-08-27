---
id: blender.import_export
title: Import, export and interoperability
domain: software_blender
tags: [blender, fbx, obj, gltf, usd, alembic, dxf, svg, ifc, stl, 3mf, unreal, fusion, sketchup, revit, autocad, axis-conventions, units]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; the native FBX importer (bpy.ops.wm.fbx_import) is 5.x — in 4.5 LTS use the Python add-on importer"
unit_system: metric
sources:
  - {title: "Blender Manual — Wavefront OBJ", url: "https://docs.blender.org/manual/en/latest/files/import_export/obj.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — FBX (native importer)", url: "https://docs.blender.org/manual/en/latest/files/import_export/fbx.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — FBX add-on (legacy import / export)", url: "https://docs.blender.org/manual/en/latest/addons/import_export/scene_fbx.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — glTF 2.0", url: "https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Universal Scene Description", url: "https://docs.blender.org/manual/en/latest/files/import_export/usd.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Alembic", url: "https://docs.blender.org/manual/en/latest/files/import_export/alembic.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — STL", url: "https://docs.blender.org/manual/en/latest/files/import_export/stl.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Stanford PLY", url: "https://docs.blender.org/manual/en/latest/files/import_export/ply.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — SVG (curve import add-on)", url: "https://docs.blender.org/manual/en/latest/addons/import_export/curve_svg.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "ezdxf on PyPI", url: "https://pypi.org/project/ezdxf/", publisher: "Manfred Moitzi", accessed: 2026-08-25}
  - {title: "Bonsai (formerly BlenderBIM)", url: "https://bonsaibim.org/", publisher: "IfcOpenShell contributors", accessed: 2026-08-25}
related: [blender.python_api, blender.addons_architecture, blender.overview]
---

# Import, export and interoperability

**Summary.** Blender's own coordinate convention is **+Y forward, +Z up, right-handed, 1 unit = 1 metre**. Almost every interoperability problem — models arriving 100× too big, lying on their side, or mirrored — is a failure to reconcile that with the other application's convention. This file lists every relevant format with its exact operator ID, states which are core and which are add-ons, and gives the axis and unit rules for round-tripping with Unreal Engine, Autodesk Fusion, SketchUp, Revit and AutoCAD.

## Key facts

| Format | Import operator | Export operator | Status |
|---|---|---|---|
| **Wavefront OBJ** | `bpy.ops.wm.obj_import` | `bpy.ops.wm.obj_export` | Core (C++) |
| **FBX** | `bpy.ops.wm.fbx_import` (native, 5.x) | `bpy.ops.export_scene.fbx` | Importer core; exporter is the bundled Python add-on. `bpy.ops.import_scene.fbx` is the **deprecated legacy** importer, shown in the menu as *FBX (.fbx) (Legacy)* |
| **glTF 2.0** | `bpy.ops.import_scene.gltf` | `bpy.ops.export_scene.gltf` | Bundled add-on (`io_scene_gltf2`), maintained with Khronos |
| **USD / USDZ** | `bpy.ops.wm.usd_import` | `bpy.ops.wm.usd_export` | Core |
| **Alembic** | `bpy.ops.wm.alembic_import` | `bpy.ops.wm.alembic_export` | Core |
| **STL** | `bpy.ops.wm.stl_import` | `bpy.ops.wm.stl_export` | Core |
| **Stanford PLY** | `bpy.ops.wm.ply_import` | `bpy.ops.wm.ply_export` | Core |
| **SVG → curves** | `bpy.ops.import_curve.svg` | — | Bundled add-on `io_curve_svg`; **paths only** |
| **SVG ↔ Grease Pencil** | `bpy.ops.wm.grease_pencil_import_svg` | `bpy.ops.wm.grease_pencil_export_svg` | Core |
| **DXF / DWG** | third-party add-on or `ezdxf` scripting | same | **Not core** |
| **IFC** | Bonsai add-on (IfcOpenShell) | Bonsai | Third-party, free |
| **3MF** | third-party add-on | third-party | **Not core** |

**Blender's convention:** *Y Forward, Z Up* — the manual repeats this on every importer page, and adds the standard remedy: "it's common for applications to use Y as the up axis, in that case **−Z Forward, Y Up** is needed."

## Format by format

### Wavefront OBJ

Core, fast, and the most reliable dumb-geometry exchange there is. Import options: `Scale`, `Clamp Bounding Box` (clamps a wildly-scaled file to a fixed size), `Forward Axis` / `Up Axis`, `Split By Object` (`o`) and `Split By Group` (`g`), `Vertex Groups`, `Validate Meshes` (leave on — the manual warns erroneous data can crash display or editing), `Detect Cyclic Curves`, `Path Separator` (splits object names into a collection hierarchy — useful for structured CAD exports).

Export options: `Selected Only`, `Scale`, `Forward/Up Axis`, `UV Coordinates`, `Normals`, `Colors` (xyzrgb extension), `Curves as NURBS`, `Triangulated Mesh`, `Apply Modifiers`, **`Apply Transform`** (writes vertices in world space; without it, vertices are in local object space), and `Properties: Viewport / Render` to choose which modifier level is evaluated.

Carries: geometry, UVs, normals, per-face material assignment via a `.mtl` sidecar. Does **not** carry: PBR material graphs, animation, instances, custom properties.

### FBX

Widely used, especially towards Autodesk products and game engines. Blender 5.x has a **new native importer** (`bpy.ops.wm.fbx_import`, `File ▸ Import ▸ FBX (.fbx)`) described as fast, memory-efficient and compatible with both modern and legacy FBX; the old Python importer remains only as *FBX (.fbx) (Legacy)* and is deprecated. **Export is still the Python add-on** (`bpy.ops.export_scene.fbx`).

Export options that matter: `Path Mode` (Auto / Absolute / Relative / Match / Strip Path / Copy, with `Embed Textures`), `Batch Mode` (one file per collection or scene), `Apply Modifiers`, `Apply Scalings`, `Forward` / `Up`, and `Apply Transform` — which the manual flags as **experimental and known to be broken with armatures and animations**, so avoid it for anything rigged.

Documented export gaps: object instancing is not preserved (each instance is written with its own data, and instanced objects are only written in static scenes), vertex shape keys are not written, constraints are baked to keyframes rather than exported as constraints, and animated fluid simulation is unsupported.

### glTF 2.0

The best-supported modern interchange format for materials. Three file variants:

- **glTF Binary (.glb)** — one self-contained binary file. Default choice.
- **glTF Separate (.gltf + .bin + textures)** — editable JSON plus data; must be shipped as a group.
- **glTF Embedded (.gltf)** — everything base64'd into the JSON; least efficient, only for plain-text-only channels, and must be enabled in add-on preferences.

Supported extensions include `KHR_draco_mesh_compression`, `KHR_lights_punctual`, `KHR_materials_clearcoat`, `KHR_materials_transmission`, `KHR_materials_unlit`, `KHR_materials_emissive_strength`, `KHR_materials_volume`, `KHR_materials_sheen`, `KHR_materials_specular`, `KHR_materials_anisotropy`, `KHR_materials_ior`, `KHR_materials_variants`, `KHR_texture_transform` and `EXT_mesh_gpu_instancing`.

Material rules to obey if you want a clean export:

- Metallic and Roughness must be in the **B** and **G** channels of one image; wire an Image Texture through a Separate RGB with G→Roughness and B→Metallic and the exporter copies the image verbatim. Set that image to **Non-Color**.
- Normal maps must go Image Texture → **Normal Map node (Tangent space)** → Principled Normal, with the image Non-Color.
- Transmission needs a non-zero Transmission value or a texture in the **R** channel, Non-Color.
- Baked ambient occlusion is picked up only if you create a node group literally named **`glTF Material Output`** with an input named **`Occlusion`**.
- Volume export requires some transmission on the Principled BSDF; the Volume Absorption node's Color becomes glTF attenuation colour and its Density the inverse attenuation distance.
- **Custom properties** are always imported and, with `Include ▸ Custom Properties` ticked, exported into the glTF `extras` field. This is the channel for carrying a panel's `part`, `grain` and `material_code` metadata to another application.

Third-party glTF extensions can be added by a separate Python add-on without patching the exporter.

### USD

Core import and export, `File ▸ Import/Export ▸ Universal Scene Description`. Imports prims as a hierarchy of Blender objects; `Xform` prims become empties and `Scope` prims become empties at the origin (an imperfect but structure-preserving mapping). Time-varying meshes get a **Mesh Sequence Cache** modifier; time-varying transforms get a **Transform Cache** constraint. Bound materials with a `UsdPreviewSurface` source populate viewport-display colour, metallic and roughness.

Documented limitations you must plan around:

- Layers, references and variants are **not** handled by the importer.
- The exporter writes all visible supported objects; invisible objects, USD layers and variants are not exported.
- Double-sidedness is taken from the **first material** and applied to the whole mesh.
- Only **perspective** cameras export.
- Geometry-node objects must output **only** the component type matching the original object (a Mesh object's modifier must output only mesh) — use Separate Components to guarantee it.
- Instancing: collection/object instances become USD references; geometry-node point instances export as `UsdGeomPointInstancer` but only for simple Object Info / Collection Info cases; nested or excluded collections may export incorrectly. Realize Instances is the escape hatch.
- **USDZ cannot include UDIM textures** (a USD library limitation).
- Only attribute types that Blender's attribute system supports natively are converted as primvars.
- Blender 5.x can author the `UsdUIAccessibilityAPI` schema from custom properties.

USD is the right choice when you need hierarchy, instancing and material assignments to survive into a modern DCC or engine pipeline. It is **not** yet the right choice for CAD-precision round-trips.

### Alembic

Core. Geometry caches, not editable scenes. Import adds Mesh Sequence Cache modifiers and Transform Cache constraints automatically; options include `Scale`, `Set Frame Range`, `Is Sequence`, `Validate Meshes` and `Always Add Cache Reader`. Use it for handing a baked animated scene to a compositor or a renderer; it is irrelevant to static architectural work except as a way to move heavy deforming geometry.

### STL and 3MF — fabrication

**STL** is core (`bpy.ops.wm.stl_import` / `stl_export`). The manual notes it is useful for CAD interchange and standard for 3D printing. Options: `Scale`, **`Scene Unit`** (apply the scene's unit scale to the data — the setting that makes a millimetre-based slicer agree with a metre-based Blender file), `Forward/Up Axis`, `Facet Normals`, `Validate Mesh`, ASCII vs binary format, `Batch` (one file per object) and `Apply Modifiers`.

STL carries triangles and nothing else: no units (the file has no unit declaration — the receiving application assumes millimetres, which is why `Scene Unit` matters), no colour, no materials, no metadata.

**3MF** carries units, colour, materials and multiple objects, and is the better modern fabrication format — but Blender has **no core 3MF support**; you need a third-party add-on. For CNC joinery, DXF (below) is more relevant than either.

Before exporting for fabrication, run the mesh analysis tools (`Overlays ▸ Mesh Analysis` in Edit Mode) for **Thickness** (walls too thin to print or machine), **Overhang**, **Intersections**, **Distorted Faces** and **Sharp Edges**, and confirm the mesh is manifold.

### DXF and DWG

**Blender has no core DXF or DWG support.** Options, best first:

1. **Bonsai / IfcOpenShell** — its drawing module produces 2D documentation and can round-trip through DXF/SVG. If you are already working in IFC, use this.
2. **`ezdxf` (MIT, Python, v1.4.4 as of May 2026, Python ≥ 3.10)** — read and write R12, R2000, R2004, R2007, R2010, R2013 and R2018, ASCII and binary; R13/R14 and pre-R12 are read-only and upgraded on read. Bundle it as a wheel in an extension (file `06`) and you can write a proper dimensioned DXF cutting list, a setting-out plan, or a nesting file directly from a Blender scene. This is the most robust route for joinery: you control layers, line types and exact coordinates.
3. **Legacy community add-ons** — `io_import_dxf` and `io_export_dxf` existed in the old `blender-addons-contrib` tree. They are unmaintained relative to current Blender and their availability for 5.x should be checked before relying on them.
4. **Convert upstream** — export DXF to SVG or OBJ from the CAD package and import that instead. For plan underlays, SVG is entirely adequate.

**DWG is a proprietary Autodesk format.** Nothing in the Blender ecosystem reads it directly. Convert to DXF in AutoCAD, or with the free ODA File Converter, before touching Blender.

### SVG — plans and profiles

Two separate importers:

- `bpy.ops.import_curve.svg` — *File ▸ Import ▸ Scalable Vector Graphics (.svg)*, from the bundled `io_curve_svg` add-on. It imports **paths only** and produces **curve objects**, which is exactly what you want: a plan outline becomes a curve you can extrude, and a moulding section becomes a Bevel Object (file `02`).
- `bpy.ops.wm.grease_pencil_import_svg` / `grease_pencil_export_svg` — SVG as Grease Pencil strokes, with Resolution and Scale on import. The export side writes strokes from the largest 3D Viewport's view and can clip to camera — a route to a line drawing from a 3D model.

> SVG has no real-world units in the way DXF does. After importing a plan, measure a known dimension in Blender and scale the whole import by the ratio. Do this once, apply the scale, and note the factor.

### IFC — Bonsai

**Bonsai** (formerly the **BlenderBIM Add-on**) is a native IFC authoring platform inside Blender, built on IfcOpenShell. GPL-3.0-or-later, free, v0.8.5 as of the latest listing, minimum Blender 4.2 LTS, installable from `Preferences ▸ Get Extensions`. It covers IFC authoring and auditing, drawing generation, structural analysis, MEP, costing and scheduling, facility management and clash detection.

Crucially, Bonsai does not "export to IFC" — it **edits the IFC file directly**. The Blender scene is a view onto an IFC model. That makes it the only route in Blender that produces a genuinely coordinatable BIM deliverable for a Namibian or South African consultant team. It also means Bonsai objects should not be treated as ordinary Blender objects: editing them with plain mesh tools desynchronises them from the IFC data.

## Axis and unit conventions — the actual rules

| Application | Up | Forward | Handedness | Default unit |
|---|---|---|---|---|
| **Blender** | +Z | +Y | Right | metre |
| Unreal Engine | +Z | +X | **Left** | centimetre |
| Unity | +Y | +Z | Left | metre |
| Autodesk Fusion | +Z | +Y (configurable) | Right | millimetre (default) |
| 3ds Max | +Z | +Y | Right | configurable (often inch) |
| Maya | +Y | +Z | Right | centimetre |
| SketchUp | +Z | +Y | Right | inch internally, displayed as chosen |
| Revit | +Z | project north | Right | millimetre / feet-inches by project |
| AutoCAD | +Z | +Y | Right | unitless drawing units + `INSUNITS` |

**The three rules.**

1. **Set Blender's units before anything else** (`METRIC`, `scale_length = 1.0`, file `01`). Every exporter's `Scale` and `Scene Unit` option is relative to that.
2. **Change the axis on export, not the object.** Rotating a model 90° and applying the rotation "fixes" the viewport and breaks every subsequent round-trip. Use the exporter's `Forward` / `Up` fields.
3. **Verify with a reference cube.** Put a 1000 × 1000 × 1000 mm cube named `SCALE_REF_1m` in every exchange file. Import it at the far end and measure it. If it is 1 m you are done; if it is 100 or 0.01, you have a unit-scale problem, not an axis problem; if it is a different shape, you have an axis problem.

## Round-trip workflows

### Blender ↔ Unreal Engine

Unreal is Z-up like Blender but X-forward, left-handed and centimetre-based, so a straight FBX will usually arrive rotated 90° about Z and, depending on settings, at 100× or 0.01× scale.

- **Preferred: glTF 2.0 (.glb)** — materials, PBR channel packing and hierarchy survive better than FBX, and the axis conversion is defined by the spec rather than by two applications guessing.
- **Also good: USD** — Unreal's USD support is mature and handles instancing and hierarchy well.
- **FBX** remains common. Export with `Apply Modifiers` on, `Apply Scalings` chosen deliberately, and **`Apply Transform` off** if anything is rigged (the manual marks it experimental and broken with armatures).
- Set object origins sensibly before export: Unreal pivots come from Blender object origins.
- Apply all object scale (`Ctrl-A ▸ Scale`) — non-unit scale is the most common source of "why is my collision wrong".
- Name meshes with a prefix scheme (`SM_Wall_01`) so the Unreal content browser is navigable.
- Lightmap UVs: create a second UV map with non-overlapping islands, or let Unreal generate one. Blender's SLIM/minimum-stretch unwrap (4.3+) produces good lightmap UVs.
- Always import the `SCALE_REF_1m` cube first and check it measures 100 uu.

### Blender ↔ Autodesk Fusion

Fusion is a parametric solid modeller; Blender is a mesh modeller. The exchange is lossy in both directions and there is no history round-trip.

- **Fusion → Blender**: export **STEP** and convert, or export **OBJ/STL** from Fusion with a fine refinement setting. STL/OBJ arrive as triangulated meshes with no editable topology — good for visualisation, useless for further parametric editing. Set Fusion's export units to millimetres and Blender's import Scale to `0.001`, or use STL's `Scene Unit` option.
- **Blender → Fusion**: export **STL** (`Scene Unit` on, ASCII off, `Apply Modifiers` on) or OBJ. Fusion imports meshes as mesh bodies; converting a mesh body to a BRep solid is possible for simple shapes and unreliable for complex ones. Keep polygon counts low and geometry manifold.
- For joinery destined for CNC, do the fabrication geometry in Fusion and use Blender only for visualisation and layout — not the other way round.

### Blender ↔ SketchUp

- **SketchUp → Blender**: SketchUp Pro exports **DAE (Collada)**, **FBX**, **OBJ**, **STL** and, in recent versions, **glTF**. glTF or FBX preserve materials best. SketchUp geometry is triangulated and often has reversed faces and duplicated coincident geometry; expect to run `Mesh ▸ Normals ▸ Recalculate Outside`, `Merge by Distance`, and `Select ▸ Select All by Trait ▸ Interior Faces` cleanup before booleaning anything.
- SketchUp's internal unit is the inch. Set the export units explicitly and verify with the reference cube.
- **Blender → SketchUp**: DAE or OBJ. SketchUp Free (web) has very limited import; SketchUp Pro is required for most formats.
- SketchUp components map naturally onto Blender collection instances, but no exporter preserves that relationship — instances are flattened.

### Blender ↔ Revit

There is no direct link. Practical routes:

- **Revit → Blender**: export **FBX** (geometry and materials, no parameters) or **IFC** (geometry *and* data, read with Bonsai). IFC is the better route if you care about element classification, and the only route that keeps the model coordinatable. Revit's FBX export can produce very heavy meshes; use a coarse detail level and a section box.
- **Blender → Revit**: essentially one-way in practice. You can bring geometry in as a linked **DWG/SAT** or as an in-place family from **SAT**, but nothing round-trips as parametric Revit elements. If the deliverable must be Revit-native, model it in Revit.
- **Shared coordinates**: get the project base point and survey point from the Revit team, and translate the Blender model to a local origin as described in file `01`. Never model at real survey coordinates.

### Blender ↔ AutoCAD

- **AutoCAD → Blender**: export **DXF** (R2000 or later ASCII is the most portable), then read it with `ezdxf` in a script or with a DXF add-on. For a plan underlay, the simplest reliable route is to plot the DXF to **SVG** or **PDF** and import the SVG as curves.
- **Blender → AutoCAD**: write DXF with `ezdxf` from a script. For 2D output — setting-out plans, cutting diagrams, nesting sheets — this gives complete control over layers, colours, line types and text, and is far more predictable than any mesh-based exporter.
- AutoCAD drawings carry no intrinsic unit; the `INSUNITS` system variable declares one. Confirm with the drawing's author whether 1 drawing unit is 1 mm or 1 m before scaling anything.

## Automation snippets

```python
import bpy, math

# --- import a plan as curves and scale it to real size -------------------
bpy.ops.import_curve.svg(filepath="/jobs/okongo/plans/ground_floor.svg")
# measure a known dimension, then:
for ob in bpy.context.scene.collection.children[-1].objects:
    ob.scale = (12.34, 12.34, 12.34)          # ratio you measured

# --- export the joinery collection to STL in millimetres -----------------
bpy.ops.wm.stl_export(filepath="//out/WD01.stl",
                      export_selected_objects=False,
                      apply_modifiers=True,
                      use_scene_unit=True,
                      ascii_format=False,
                      forward_axis='Y', up_axis='Z')

# --- export a glb for a web viewer, keeping custom properties ------------
bpy.ops.export_scene.gltf(filepath="//out/house.glb",
                          export_format='GLB',
                          export_apply=True,
                          export_extras=True,
                          use_selection=False)

# --- export USD for a downstream engine ----------------------------------
bpy.ops.wm.usd_export(filepath="//out/house.usdc",
                      export_materials=True,
                      export_textures=True)
```

> ⚠️ Operator keyword names differ between Blender versions more than operator names do. Before hard-coding a keyword, check it: `print(bpy.ops.wm.stl_export.get_rna_type().properties.keys())`. The examples above show the shape of the call, not a guarantee of every keyword on your build.

## Sources

- [Manual — Wavefront OBJ](https://docs.blender.org/manual/en/latest/files/import_export/obj.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — FBX (native importer)](https://docs.blender.org/manual/en/latest/files/import_export/fbx.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — FBX add-on (legacy import, export, compatibility gaps)](https://docs.blender.org/manual/en/latest/addons/import_export/scene_fbx.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — glTF 2.0 (file variants, extensions, material conventions)](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Universal Scene Description (import/export limitations)](https://docs.blender.org/manual/en/latest/files/import_export/usd.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Alembic](https://docs.blender.org/manual/en/latest/files/import_export/alembic.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — STL](https://docs.blender.org/manual/en/latest/files/import_export/stl.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Stanford PLY](https://docs.blender.org/manual/en/latest/files/import_export/ply.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — SVG as Grease Pencil](https://docs.blender.org/manual/en/latest/files/import_export/grease_pencil_svg.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Scalable Vector Graphics curve import add-on](https://docs.blender.org/manual/en/latest/addons/import_export/curve_svg.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Mesh Analysis (fabrication checks)](https://docs.blender.org/manual/en/latest/modeling/meshes/mesh_analysis.html) — accessed 2026-08-25 via the local manual bundle
- [API — `bpy.ops.import_curve.svg`](https://docs.blender.org/api/current/bpy.ops.import_curve.html) — accessed 2026-08-25 via the local API bundle
- [API — `bpy.ops.import_scene` / `bpy.ops.export_scene`](https://docs.blender.org/api/current/bpy.ops.import_scene.html) — accessed 2026-08-25 via the local API bundle
- [ezdxf on PyPI](https://pypi.org/project/ezdxf/) — accessed 2026-08-25
- [Bonsai](https://bonsaibim.org/) — accessed 2026-08-25
- [Bonsai on Blender Extensions](https://extensions.blender.org/add-ons/bonsai/) — accessed 2026-08-25

## Open questions

- The axis/unit table for Unreal, Unity, Fusion, Max, Maya, SketchUp, Revit and AutoCAD is compiled from general working knowledge, **not** from each vendor's documentation in this pass — **needs-verification** per application before it is used as a specification. The reference-cube test is the safeguard.
- The current availability and maintenance status of a DXF import/export add-on for Blender 5.x could not be confirmed; the extensions platform search did not surface one. Treat `ezdxf` scripting as the supported route.
- 3MF add-on availability for 5.x is likewise unconfirmed.
- Exporter keyword arguments in the automation snippets (`export_selected_objects`, `use_scene_unit`, `ascii_format`, `export_extras`) are from working knowledge of the current C++ exporters and were not individually confirmed against the API reference; enumerate them at runtime before scripting.
