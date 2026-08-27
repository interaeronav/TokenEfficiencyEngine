---
id: ue.project_setup
title: Unreal Engine project setup and content pipeline
domain: software_unreal_engine
tags: [project-settings, folder-structure, naming-convention, source-control, perforce, git-lfs, plugins, packaging, cooking, datasmith, revit, rhino, sketchup, 3ds-max, blender, gltf, fbx, usd, interchange]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Datasmith version-support table is as published for 5.8 and changes each release."
sources:
  - {title: "Datasmith", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/datasmith-plugins-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Datasmith Supported Software and File Types", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/datasmith-supported-software-and-file-types", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Recommended Asset Naming Conventions", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Source Control", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/source-control-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Using Datasmith Direct Link", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/using-datasmith-direct-link-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.overview, ue.core_concepts, ue.archviz_workflow, ue.python_automation]
---

# Unreal Engine project setup and content pipeline

**Summary.** A project's first hour determines how painful the next six months are. This file covers creating an archviz project on the right template, the project settings that actually change behaviour, folder and asset naming conventions, choosing between Perforce and Git+LFS (the answer is not the obvious one), the plugin set an archviz project needs, packaging and cooking, and — the largest section — getting a building model in through Datasmith from Revit, Rhino, SketchUp, 3ds Max, Archicad, Navisworks or IFC, plus the FBX / glTF / USD alternatives.

## Key facts

| Item | Value |
|---|---|
| ArchViz project template | `Architecture, Engineering, and Construction` category → **ArchVis** template |
| Other AEC templates | Collab Viewer, Product Configurator, VR, Handheld AR, nDisplay |
| Project file | `MyProject.uproject` (JSON) |
| Content root | `MyProject/Content/` → virtual path `/Game/` |
| Python auto-discovered folder | `MyProject/Content/Python/` |
| Config files | `MyProject/Config/DefaultEngine.ini`, `DefaultGame.ini`, `DefaultEditor.ini`, `DefaultInput.ini` |
| Datasmith scene file | `.udatasmith` (plus a sibling assets folder) |
| Datasmith importer plugins | Datasmith Importer, Datasmith CAD Importer, Datasmith C4D Importer, Datasmith FBX Importer |
| Naming pattern | `[AssetTypePrefix]_[AssetName]_[Descriptor]_[OptionalVariant]` |
| Built-in source control providers | Perforce and Subversion supported by default; Git via plugin |
| Unreal unit | 1 uu = 1 cm |
| Cook/package CLI | `RunUAT.bat BuildCookRun` |

> ⚠️ Set your working units in **every** upstream application to metres or millimetres and confirm the scale of the first imported object against a known dimension (a 900 mm door leaf, a 2 400 mm ceiling) before you build anything on top of it. A scale error found after the lighting is done costs a week. Unreal's world unit is one centimetre; Datasmith handles the conversion, but a Rhino file authored in "no units" or a SketchUp model in inches will arrive wrong.

## Creating the project

`Epic Games Launcher > Unreal Engine > Library > Launch` → the Unreal Project Browser. Choose:

- **Category:** Architecture, Engineering, and Construction
- **Template:** **ArchVis** — ships example levels for sun studies, interior rendering and stylised non-photorealistic renders, with the Sun Position Calculator and Datasmith plugins already enabled, cameras and Sequencer set up, and a configured Post Process Volume. Content lives under `Content/ArchVisProject`.
- **Blueprint** (not C++) unless you already know you need C++. You can add C++ later; you cannot easily remove it.
- **Target Platform:** Desktop. **Quality Preset:** Maximum. **Starter Content:** off (it is game-oriented clutter). **Raytracing:** on if your GPU supports it.

Other templates worth knowing:

- **Collab Viewer** — a multi-user review application with markup, measurement and Datasmith Direct Link source switching built in. The fastest route to "client and consultant walk the model together".
- **Product Configurator** — a variant-switching framework. The archviz application is a finishes/options configurator: swap floor, worktop, joinery colour at runtime.
- **VR** — the standard OpenXR pawn with teleport locomotion.

If you must start from Blank, enable the plugins listed below and expect to configure exposure and units yourself.

## Project settings that matter

`Edit > Project Settings`. The ones that change results, not preferences:

**Engine > Rendering**
- *Dynamic Global Illumination Method*: **Lumen**. *Reflection Method*: **Lumen**. Setting Lumen enables *Generate Mesh Distance Fields* (required for Lumen software ray tracing) and requires a restart. **When Lumen is enabled, precomputed static lighting contributions are disabled and all lightmaps are hidden.**
- *Support Hardware Ray Tracing* + *Use Hardware Ray Tracing when available* — better quality, but Epic warns of significant scene-update costs above ~100 000 instances.
- *Shader Model 6 (SM6)* — required for Lumen, MegaLights, Nanite and Virtual Shadow Maps. On by default in new projects.
- *Shadow Map Method*: **Virtual Shadow Maps**.
- *Default Settings > Extend default luminance range in Auto Exposure settings* — **required** for the SunSky Actor to display correctly without editing its properties. Turn this on at project creation; changing it later breaks every existing exposure setup and forces manual migration.
- *Default Settings > Light Units* for Point/Spot/Rect lights — set to **Lumen** or **Candela** so lighting designers can enter datasheet values.
- *Postprocessing > Enable alpha channel support in post processing* — set to *Linear color space only* if you need transparent-background PNG/EXR output from Movie Render Queue. Requires a restart.
- *Anti-Aliasing Method*: **TSR** for real-time; overridden per-render in Movie Render Graph.

**Engine > General Settings** — *Near Clip Plane*. The default (typically 10 uu = 10 cm) causes visible clipping when a camera is pushed against a wall in a tight interior. Lower it cautiously; too low costs depth precision.

**Project > Description / Maps & Modes** — set the default game map and editor startup map to your working level so command-line and headless runs open the right world.

**Plugins > Python** — *Startup scripts*, *Additional Paths*, *Isolate Interpreter Environment*. See file `06`.

**Plugins > Remote Control** — *Remote Control WebSocket Server Port* (default 30020) and *Remote Control HTTP Server Port* (default 30010).

**Editor Preferences > General > Performance > Use Less CPU when in Background** — turn **off** when using Datasmith Direct Link, so the viewport updates while Revit or Rhino has focus.

**Editor Preferences > General > Model Context Protocol** — *Auto Start Server*, *Server Port Number* (default 8000), *Server URL Path* (default `/mcp`).

## Folder structure

Epic does not mandate one. The convention that survives contact with a real archviz project:

```
Content/
  _Project/            # your project's own assets, underscore sorts first
    Blueprints/
    Levels/
      L_Main.umap
      L_Sublevels/
    Materials/
      MasterMaterials/
      Instances/
    Meshes/
      Building/
      Furniture/
      Landscape/
    Textures/
    Sequences/
    UI/
  _Imports/            # raw Datasmith drops, per revision
    Revit_2026-08-25/
  Developers/          # per-artist sandbox, excluded from cooks
  ThirdParty/          # Fab / Megascans purchases, never edited in place
Config/
Python/                # NOT auto-discovered; Content/Python is
Source/                # only if C++
```

Two rules that matter more than the shape of the tree:

1. **Never edit purchased or imported assets in place.** Duplicate into `_Project/` first. A Datasmith reimport will overwrite in-place edits.
2. **Keep the Datasmith drop folder separate from your working folder.** Reimport writes there; your material instances, collision and Blueprints reference outward from your own folder.

## Asset naming convention

Epic's recommended pattern, as used in its own sample projects:

```
[AssetTypePrefix]_[AssetName]_[Descriptor]_[OptionalVariantLetterOrNumber]
```

| Asset | Prefix | | Asset | Prefix |
|---|---|---|---|---|
| Static Mesh | `SM_` | | Blueprint | `BP_` |
| Skeletal Mesh | `SK_` | | Actor Component | `AC_` |
| Material | `M_` | | Blueprint Interface | `BI_` |
| Material Instance | `MI_` | | Widget Blueprint | `WBP_` |
| Post Process Material | `PPM_` | | Data Table | `DT_` |
| Texture | `T_` | | Curve Table | `CT_` |
| HDRI | `HDR_` | | Enum | `E_` |
| Physics Asset | `PHYS_` | | Structure | `F_` |
| Physics Material | `PM_` | | Level Sequence | `LS_` |
| OCIO Profile | `OCIO_` | | Sequencer Edits | `EDIT_` |
| Niagara System | `FXS_` | | Level Snapshots | `SNAP_` |
| Niagara Emitter | `FXE_` | | Remote Control Preset | `RCP_` |

Texture descriptors in common use: `_D` or `_BC` base colour, `_N` normal, `_ORM` (occlusion/roughness/metallic packed), `_M` mask, `_E` emissive. So `T_Brick_Facebrick_ORM`, `MI_Brick_Facebrick_Grey`, `SM_Window_Casement_1200x900`.

Levels are not in Epic's table; `L_` for a level and `LI_` for a level instance is the widespread community practice. Mark as convention, not standard.

Why bother: the naming convention is what makes automated batch operations in file `06` possible. A script that assigns materials by matching `SM_Wall_*` to `MI_Plaster_*` only works if the names are disciplined.

## Source control: Perforce versus Git + LFS

Epic supports **Perforce and Subversion by default**; Git is available through a plugin. The honest guidance:

| | Perforce (Helix Core) | Git + LFS |
|---|---|---|
| Binary assets | Designed for them | Tolerated via LFS |
| File locking (exclusive checkout) | Native, integrated into the Content Browser | Only via `git lfs lock`, weakly integrated |
| Repository size | Server-side, streams what you need | Full history clones locally by default |
| Cost for a small team | Free for up to 5 users / 20 workspaces on Helix Core | Free |
| Editor integration quality | Excellent — status icons, check out, check in, history, diff against depot | Functional but limited |
| One File Per Actor levels | Handles thousands of small files well | Handles them, but `.gitattributes` discipline is essential |

For a one- or two-person archviz practice, **Git + LFS is adequate and free**, provided you:

- `.gitignore` `Binaries/`, `DerivedDataCache/`, `Intermediate/`, `Saved/`, `.vs/`, `Build/`
- LFS-track `*.uasset`, `*.umap`, `*.fbx`, `*.udatasmith`, `*.png`, `*.tga`, `*.exr`, `*.hdr`
- Never let two people edit the same `.umap` at once (use One File Per Actor / World Partition, which reduces but does not eliminate the problem)

For three or more people editing the same level, **Perforce is the right answer** and the exclusive-checkout model is the reason. `.uasset` files do not merge.

In-editor activation: `Edit > Editor Preferences > Loading & Saving` (for *Automatically Checkout on Asset Modification*, *Prompt for Checkout on Package Modification*, *Add New Files when Modified*, *Use Global Settings*, *Tool for diffing text*), or right-click any asset in the Content Browser → *Source Control > Connect to Source Control*. Content Browser status icons show checked out by you, checked out by another user, marked for add, not in depot, and newer version exists in source control.

The Python API mirrors this: `unreal.EditorAssetLibrary.checkout_asset()`, `.checkout_directory()`, `.checkout_loaded_assets()`.

## Plugins for an archviz project

`Edit > Plugins`. Enable and restart:

| Plugin | Category | Why |
|---|---|---|
| Datasmith Importer | Importers | `.udatasmith` scenes |
| Datasmith CAD Importer | Importers | STEP, IGES, JT, Parasolid, IFC, CATIA, Creo, NX, ACIS |
| Sun Position Calculator | Misc | The SunSky Actor and geographically accurate sun |
| Python Editor Script Plugin | Scripting | The `unreal` module |
| Editor Scripting Utilities | Scripting | `EditorAssetLibrary` and friends |
| Movie Render Pipeline | Rendering | Movie Render Queue / Movie Render Graph |
| Remote Control API | Messaging | HTTP/WebSocket control (Beta) |
| Unreal MCP + All Toolsets | AI | MCP server for agent control (Experimental, 5.8+) |
| Editor Utility Widgets | (built in) | Custom editor tool UIs |
| Variant Manager | Runtime | Design options / finishes variants |
| Volumetrics | Rendering | Volumetric fog quality |
| glTF Exporter / Interchange glTF | Importers | glTF round-trip |
| USD Importer | Importers | USD stages and layers |

Do **not** enable plugins speculatively. Every enabled plugin adds Blueprint- and Python-visible API surface, editor startup time, and package size.

## Datasmith — getting the building in

Datasmith imports **entire scenes**: thousands of objects with their materials, pivots, scale, hierarchy and metadata. That is the difference from FBX, which Epic describes as optimised for individual objects.

### The three workflow types

- **Direct** — the Datasmith importer in Unreal reads the source file format directly. No plugin needed on the authoring side.
- **Export** — you export to an intermediate format using functionality already in the application.
- **Export Plugin** — you install a Datasmith exporter plugin into the authoring application, which writes `.udatasmith`.

### Support matrix (as published for UE 5.8)

| Application / format | Versions | Workflow | Importer plugin |
|---|---|---|---|
| Autodesk Revit | 2016.3–2023* | Export Plugin | Datasmith |
| Autodesk 3ds Max | 2016–2026 | Export Plugin | Datasmith |
| Autodesk Navisworks | 2019–2026 | Export Plugin | Datasmith |
| Autodesk AutoCAD | — | Direct | CAD |
| Autodesk Alias / Inventor | up to 2025 | Direct | CAD |
| Autodesk VRED | Professional 2018–2026 | Export Plugin | FBX |
| Graphisoft Archicad | 23–28 | Export Plugin | Datasmith |
| Trimble SketchUp Pro | 2019–2025 | Export Plugin, **Direct Link** | Datasmith |
| McNeel Rhinoceros | up to 8 | Export Plugin **or** Direct (`.3dm`) | Datasmith |
| Dassault SOLIDWORKS | up to 2025 / 2020–2025 | Export Plugin (CAD) or Direct (Datasmith) | CAD / Datasmith |
| Maxon Cinema 4D | — | Direct | C4D |
| 3DEXCITE DELTAGEN | 2017–2024 | Export (FBX only) | FBX |
| ArcGIS CityEngine | — | Export Plugin | Datasmith |
| IFC | IFC2x Editions 2–4, 4x3 (Beta) | Direct | CAD |
| STEP | AP203, AP214, AP242 Ed2/Ed3 | Direct | CAD |
| IGES | 5.1, 5.2, 5.3 | Direct | CAD |
| Parasolid `.x_t` | up to 37.1 | Direct | CAD |
| JT Open | up to 10.9 | Direct | CAD |
| CATIA V5 | up to V5_6 R2024 | Direct | CAD |
| PTC Creo | Pro/E 19.0 to Creo 11.0 | Direct | CAD |
| Siemens NX | V11–V18, NX–NX12, NX1847–NX2412 | Direct | CAD |

\* As of UE 5.3 Autodesk manages newer Revit exporter versions and ships them directly in Revit 2024+. Unreal still supports the plugin; older versions are on Epic's download page.

**macOS export plugins** exist only for SketchUp Pro 2019–2025, Archicad 23–28 and Rhinoceros 6/7/8. All Datasmith *importers* in the editor are Windows-only.

**No Blender exporter.** Blender is not on the Datasmith list. The Blender route is glTF 2.0 (best material fidelity, correct PBR), FBX (widest compatibility, unit and axis traps), or USD (best for large scenes and layered overrides). See domain `14`.

**Backward compatibility is not guaranteed** between Datasmith file-format versions. Keep the exporter plugin version aligned with the engine version, and re-export rather than reusing an old `.udatasmith` after an engine upgrade.

### The two-stage import — and why it matters for automation

Datasmith import is internally two steps:

1. Read the source file into an in-memory **Datasmith Scene** — a representation of the objects, their relationships and every property Datasmith could extract.
2. **Finalise** the scene into Unreal assets in the Content Browser, then spawn the Datasmith Scene Asset in the current level, which in turn spawns all its children (Actors, Static Mesh Actors, Lights, Cameras).

Scripting lets you deconstruct these two steps and insert processing between them — filter out objects you do not need, merge elements, or use metadata to make decisions. See file `06` for runnable code.

Epic's own advice is worth repeating: **prefer post-import modification.** Modify the Datasmith Scene during import only when you need to prevent asset creation entirely. Pre-import filtering also breaks the reimport workflow — objects you filtered out are detected as newly added on reimport and come back.

### Direct Link

Datasmith Direct Link keeps a live connection between one or more source applications and one or more destinations (an Unreal-based application, the Collab Viewer template, or Twinmotion), so design changes push with a **Synchronize with Direct Link** button instead of a re-export. Available for SketchUp Pro, Rhino, Revit, Archicad, 3ds Max and Navisworks via their exporter plugins.

For a packaged project, Direct Link needs UDP messaging: create a shortcut to the packaged `.exe` and add `-messaging` to the Target. And disable *Editor Preferences > General > Performance > Use Less CPU when in Background* so the viewport updates while the source application has focus.

### Datasmith metadata

Datasmith carries source-application metadata (Revit parameters, IFC property sets, layer names, object IDs) into Unreal as asset metadata, readable from Blueprint and Python at edit time and at runtime. This is the mechanism behind automated batch operations: select every element whose Revit *Type Name* contains "Facebrick", assign `MI_Brick_Facebrick`, done. It is also how you build a click-to-inspect information overlay in a delivered walkthrough.

### The realistic Revit → Unreal sequence

1. In Revit, create a dedicated 3D view for export. Hide analytical, annotation and unwanted categories. Section the model if the site is huge. Purge unused.
2. Datasmith exporter → export the view to `.udatasmith` into `Content/_Imports/Revit_YYYY-MM-DD/`.
3. In Unreal, `Datasmith` button in the toolbar → import → destination `/Game/_Imports/Revit_YYYY_MM_DD`.
4. Expect: correct hierarchy, correct scale, one material per Revit material (usually flat and wrong-looking), no UV2 for lightmaps unless requested, triangulated geometry, and pivots at world origin for many elements.
5. Batch-enable Nanite on the architectural meshes (Content Browser multi-select → right-click → *Nanite > Enable*).
6. Replace the imported materials with your own material instances, driven by metadata or by name pattern (file `06`).
7. Delete what you do not need. Revit exports a great deal you will never see.

## FBX, glTF and USD

**FBX** — built into Unreal for import and export, optimised for individual objects. Use it for set dressing and furniture that augments a Datasmith scene. Watch: unit scale, up-axis, smoothing groups, and whether the exporter wrote a UV channel 1 for lightmaps. UE 5.8 adds an experimental **uFBX** library that noticeably reduces import time on heavy `.fbx` files with large meshes.

**glTF 2.0** — the cleanest PBR interchange. Materials map to Unreal's metallic/roughness model with the least translation loss, which makes it the best route out of Blender. The glTF Exporter plugin also writes glTF *from* Unreal, useful for web viewers.

**USD** — Pixar's Universal Scene Description. Unreal's USD Importer can open a USD stage as a live, layered reference rather than a one-shot import, which means an upstream layer edit propagates. For a large multi-discipline model with several authors this is strategically the best answer, and Epic notes glTF and USD usage is intensifying while FBX remains the volume format.

**Interchange** is the newer, extensible import framework gradually replacing the legacy importers. UE 5.8 reworked its import dialog, regrouping and renaming asset-type conversion options and clarifying material creation versus reuse of existing materials.

## Packaging and cooking

**Cooking** converts editor assets into platform-optimised binary form — compiling shaders for the target's feature level, converting textures to platform formats, and stripping editor-only data. **Packaging** cooks and then assembles a runnable application.

In-editor: `Platforms > Windows > Package Project`. From the command line, via the Unreal Automation Tool:

```
Engine\Build\BatchFiles\RunUAT.bat BuildCookRun ^
  -project="C:\Projects\Okongo\Okongo.uproject" ^
  -noP4 -platform=Win64 -clientconfig=Shipping ^
  -cook -allmaps -build -stage -pak -archive ^
  -archivedirectory="C:\Builds\Okongo"
```

Notes that bite in archviz:

- **Shader compilation dominates the first cook.** Hours, not minutes, on a material-heavy interior. A shared DDC makes the second cook and every colleague's first cook fast.
- Assets not referenced by a cooked map are **not** included. If a Blueprint loads a material by soft path at runtime (a configurator!), add its folder to `Project Settings > Packaging > Additional Asset Directories to Cook`.
- `Development` builds keep the console (backtick) and `stat` commands. `Shipping` strips them. Deliver Shipping; debug in Development.
- Nanite streams from disk — put the delivered build on an SSD and say so in the handover note.

## Open questions

- The Revit exporter version table lists 2016.3–2023 with a note that Autodesk ships newer versions inside Revit 2024+; the practical upper bound for Revit 2025/2026 is therefore governed by Autodesk, not Epic — **needs verification** per Revit release.
- Level asset prefixes (`L_`, `LI_`) are community convention, not in Epic's published table.
- Exact default value of the Near Clip Plane in 5.8 was not verified on the pages fetched.

## Sources

- [Datasmith](https://dev.epicgames.com/documentation/en-us/unreal-engine/datasmith-plugins-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Datasmith Supported Software and File Types](https://dev.epicgames.com/documentation/en-us/unreal-engine/datasmith-supported-software-and-file-types) — Epic Games, accessed 2026-08-25
- [Customizing the Datasmith Import Process](https://dev.epicgames.com/documentation/en-us/unreal-engine/customizing-the-datasmith-import-process-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Using Datasmith Direct Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-datasmith-direct-link-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Recommended Asset Naming Conventions](https://dev.epicgames.com/documentation/en-us/unreal-engine/recommended-asset-naming-conventions-in-unreal-engine-projects) — Epic Games, accessed 2026-08-25
- [Source Control](https://dev.epicgames.com/documentation/en-us/unreal-engine/source-control-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Sun and Sky Actor](https://dev.epicgames.com/documentation/en-us/unreal-engine/sun-and-sky-actor-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Engine Templates Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-templates-reference) — Epic Games, accessed 2026-08-25
- [Universal Scene Description](https://dev.epicgames.com/documentation/en-us/unreal-engine/universal-scene-description-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Interchange Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/interchange-framework-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Cooking Content](https://dev.epicgames.com/documentation/en-us/unreal-engine/cooking-content-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal Engine 5.8 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) — Epic Games, accessed 2026-08-25
