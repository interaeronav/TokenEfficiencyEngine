---
id: ue.overview
title: Unreal Engine domain overview
domain: software_unreal_engine
tags: [unreal-engine, ue5, licensing, royalty, seat-licence, hardware, archviz, overview]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8 (current release). Content is broadly valid for 5.4–5.8; version-specific items are flagged."
unit_system: metric
sources:
  - {title: "Unreal Engine 5.8 Documentation", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal Engine 5.8 Release Notes", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal Engine licensing options", url: "https://www.unrealengine.com/en-US/license", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Hardware and Software Specifications", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal MCP", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.core_concepts, ue.project_setup, ue.materials_rendering, ue.archviz_workflow, ue.blueprints, ue.python_automation, ue.cpp_extension, ue.performance, ue.resources]
---

# Unreal Engine domain overview

**Summary.** Unreal Engine (UE) is Epic Games' real-time 3D engine: a C++ runtime, a large editor application, and an asset pipeline, distributed free and with full source. For architectural visualisation it is the leading real-time alternative to offline renderers — a single scene serves stills, animated walkthroughs, VR and interactive configurators without re-lighting. The current release is **Unreal Engine 5.8**. Licensing has two distinct arms: a 5% royalty for games and runtime-code applications above US$1M lifetime gross revenue, and a **US$1,850 per seat per year** licence for non-game commercial use once the business passes US$1M revenue in the trailing 12 months — the arm that architecture and construction practices fall under. This domain is written for an agent-driven workflow: file `06` (Python and automation) is the operational centre, and UE 5.8 now ships an **official experimental MCP server plugin** that lets Claude Code drive the editor directly.

## Key facts

| Fact | Value |
|---|---|
| Current version | Unreal Engine 5.8 |
| Vendor | Epic Games, Inc. |
| Source access | Full C++ source via GitHub (EpicGames/UnrealEngine, account linking required) |
| Cost to download and use | Free |
| Royalty (games / apps shipping engine code) | 5% of gross revenue above US$1,000,000 lifetime gross product revenue |
| Epic Games Store sales | Royalty-free |
| Seat licence (non-game commercial use) | US$1,850 per seat per year, required once the entity has generated over US$1M in the past 12 months |
| Free for | Individuals and small businesses under US$1M annual gross revenue; educators and schools; students |
| Embedded Python | 3.11.8 (VFX Reference Platform aligned) |
| Recommended workstation | Windows 11, quad-core 2.5 GHz+, 32 GB RAM, 8 GB+ VRAM, DirectX 12 GPU |
| Minimum OS | Windows 10 version 22H2 (64-bit) or Windows 10 Enterprise 21H2 (64-bit) |
| Compiler (Windows) | Visual Studio 2026 for general development; VS 2022 for Nintendo / AGDE below v26.1.102 |
| 32-bit platforms | Removed in UE5 |
| Editor scripting languages | Blueprint (visual), Python 3.11 (editor-only), C++ |
| Remote control transports | HTTP (default port 30010), WebSocket (default port 30020), MCP over HTTP (default port 8000) |

> ⚠️ The seat licence is the arm that matters for an architecture, engineering or construction practice. If you use Unreal to produce visualisations as a *service* — you are not shipping a product containing engine code — you are on the seat track, not the royalty track. Below US$1M trailing-twelve-month revenue the seat fee is zero. The threshold is measured on the *entity's* revenue, not on revenue attributable to Unreal work. Confirm current terms against the licence page before signing a client contract that assumes zero licence cost.

## What Unreal Engine actually is

Three things share the name:

1. **The runtime** — a C++ engine (renderer, physics, audio, networking, gameplay framework) that compiles into your packaged application. This is what a shipped configurator or VR walkthrough contains.
2. **The editor** (`UnrealEditor.exe` / `UnrealEditor-Cmd.exe`) — a very large authoring application built on the same runtime plus the Slate UI framework. Everything an archviz artist does happens here. Python only exists here; it is not a runtime scripting language.
3. **The content pipeline** — Datasmith importers, Interchange, the Derived Data Cache, the cooker, and the packaging system that converts editor assets into platform-native cooked data.

For architectural visualisation the pitch is specific: geometry from Revit, Rhino, SketchUp, 3ds Max, Archicad, Navisworks or IFC comes in through Datasmith with materials and metadata intact; Lumen gives physically plausible global illumination without a bake; Nanite removes the polygon budget conversation; and one lit scene then feeds stills (Movie Render Graph), animation (Sequencer), VR and a runtime configurator with no separate lighting solve for each.

## Release cadence

Epic ships roughly two feature releases per year, each with a long tail of hotfix point releases (5.8.0 → 5.8.1 → …). Major versions carry a maturity ladder that you must read before committing a feature to a client project:

| Status | Meaning | Treatment in production |
|---|---|---|
| Experimental | In flux, APIs and data formats can change without notice | Prototype only. Never on a deadline. |
| Beta | Functional and stable enough to use, but not final | Acceptable with a fallback plan. Remote Control and Editor Utility Widgets sit here. |
| Production Ready | Supported for shipping | Default choice. |

Notable status changes in **UE 5.8** relevant to this domain:

- **Movie Render Graph** reached Production Ready. Preset-based Movie Render Queue configurations still work, but Epic has stated new features will be graph-only. New archviz pipelines should be authored on the graph.
- **MegaLights** reached Production Ready, with transmission (subsurface), froxel-based translucency, IES support for volumetrics, lighting channels and cloud shadows.
- **Lumen Lite** (Beta) — an irradiance-field medium-quality GI path, roughly twice as fast as high-quality Lumen; the new default on current-generation handheld consoles and available on PC.
- **MCP Server** (Experimental) — an in-editor Model Context Protocol server, plugin identifier `ModelContextProtocol`, friendly name **Unreal MCP**. See file `06`.
- **Sandboxes** — isolated editor workspaces you can experiment in and then selectively persist, without branching source control.
- **X-Rite AxF measured materials** import into the Substrate material system — of direct interest for accurate scanned finishes.
- **uFBX** (Experimental) alternative FBX import library, noticeably faster on heavy `.fbx` files.

Upgrading an in-flight archviz project across a minor version is usually safe; across a major version it is a project decision, not a click. Lighting, especially Lumen and exposure defaults, is the usual source of visual drift.

## Editions and licensing in detail

There is one engine binary. The licence you need depends on what you do with it.

**Free tier.** Full engine, full source, all platforms and features. Applies to game developers below the royalty threshold, to individuals and small businesses with less than US$1M annual gross revenue, and to educators and schools.

**Royalty track.** If you create a game or application that relies on engine code at runtime and license it to third parties, you owe **5% of gross revenue above US$1,000,000** in lifetime gross product revenue. Revenue from sales through the Epic Games Store is royalty-free. This is the track a shipped interactive apartment configurator sold as a product would sit on.

**Seat track (the 2024 change).** Since 2024 Epic separates non-game commercial use into a per-seat model. If you use Unreal Engine commercially, have generated more than **US$1M in the past 12 months**, and are *not* creating a game or application that ships engine code to third parties, you buy licences at **US$1,850 per seat per year**. This covers architecture, engineering and construction, automotive, product design, manufacturing, broadcast, film and simulation. The practical consequences:

- A small Namibian or South African practice under the revenue threshold pays nothing. **[NA]** **[ZA]**
- A practice that crosses the threshold pays per person who uses the editor, not per project or per render.
- Delivering a *video file* or *still images* to a client is service work, not a shipped product — seat track.
- Delivering a *packaged executable or VR build* that the client runs is closer to the royalty definition; the deciding question is whether engine code is licensed to a third party. Get this in writing from Epic before assuming.

**Fab** (Epic's asset marketplace, successor to the Unreal Marketplace and Quixel's storefront) has its own licence tiers — Personal, Professional, and Reference-Only — plus CC-BY content. Personal and Professional grant the same rights and access to source-format assets; Reference-Only grants a referenced asset rather than its source. All standard tiers permit commercial use, modification, incorporation into projects and commercial distribution of the resulting project, and all prohibit standalone resale of the asset itself. Epic states there is no need to upgrade Personal to Professional if you later cross the revenue threshold. See file `09`.

## Hardware

Epic's published **recommended** specification is modest and should be read as "the editor will open", not "you will render an interior at 60 fps":

- Windows 11, quad-core Intel or AMD at 2.5 GHz or faster
- 32 GB RAM
- 8 GB or more graphics RAM
- DirectX 12 compatible GPU with current drivers

The realistic archviz specification is higher. Epic publishes its own reference workstation as a guideline — a Lenovo P620-class machine with a Threadripper PRO 7985WX, 256 GB DDR5 ECC, an RTX 4080 16 GB, and separate 2 TB OS and 4 TB data NVMe drives. Epic also notes that **12 to 16 cores is a practical local-compile baseline** if you are not using a distributed build solution, and recommends Unreal Build Accelerator (UBA) for distributed compilation.

Feature-level requirements, which are the ones that actually bite:

| Feature | Requirement |
|---|---|
| Lumen GI, Lumen Reflections, MegaLights | Windows 10 build 1909.1350+ with DX12; **SM6 enabled in Project Settings**; AMD RX-6000 series or newer, Intel Arc A-Series or newer, or NVIDIA RTX-2000 series or newer |
| Nanite, Virtual Shadow Maps | DX12 with Shader Model 6.6 atomics, or Vulkan with `VK_KHR_shader_atomic_int64`; SM6 enabled (default in new projects) |
| Temporal Super Resolution | Any SM5 card, but the 8-UAV-per-shader limit has performance implications; TSR shaders compile with 16-bit types on D3D12 SM6 |
| Nanite streaming | SSD strongly recommended for runtime storage — Nanite streams mesh clusters from disk on demand |
| Lumen Hardware Ray Tracing | Requires SM6 set in Project Settings |

Practical guidance for a small practice: VRAM is the binding constraint for interiors with 4K textures and virtual shadow maps. 12 GB is a working floor, 16 GB comfortable, 24 GB removes the anxiety. System RAM matters at *import* time far more than at render time — a large Revit or Navisworks model through Datasmith can peak well above 32 GB. Put the project, the Derived Data Cache and the engine on NVMe.

macOS and Linux are supported for development but the archviz feature set is weaker: Nanite and Lumen paths on Metal have historically lagged, and Datasmith exporter plugins for Revit, 3ds Max and Navisworks are Windows-only because the host applications are. Treat Windows as the archviz platform.

## How this domain is organised

| File | Covers | Read it when |
|---|---|---|
| `00_overview.md` | This file: what UE is, versions, licensing, hardware | Orienting, or checking a licence question |
| `01_core-concepts.md` | UObject, AActor, components, the Gameplay Framework, World Partition, reflection, GC, editor vs runtime | Before writing any script or C++ |
| `02_project-setup-and-pipeline.md` | Project creation, settings, folder and naming conventions, source control, plugins, packaging, Datasmith and CAD/BIM import, glTF/FBX/USD | Starting a project or bringing a building in |
| `03_materials-and-rendering.md` | Material editor, PBR, instances, Nanite, Lumen, VSM, path tracing, TSR, lightmaps, post-process, profiling | Making it look right |
| `04_archviz-workflow.md` | The end-to-end archviz pipeline, real-world scale, sun and sky for Okongo, physical lighting units, cameras, Sequencer, Movie Render Graph, VR and configurators | The actual job |
| `05_blueprints-and-gameplay.md` | Blueprint graphs, communication patterns, common archviz interactions, UMG | Building interactivity |
| `06_python-and-automation.md` | **The key file.** Python API, Editor Utility Widgets, asset import automation, headless commandlets, Remote Control, MCP | Driving Unreal from an agent |
| `07_cpp-and-extension.md` | Modules, `UCLASS`/`UPROPERTY`/`UFUNCTION`, `Build.cs`, editor extensions, Slate, plugins, Live Coding | When Blueprint or Python runs out |
| `08_performance-and-optimisation.md` | Budgets, LODs, instancing, draw calls, streaming, virtual textures, culling, profiling for modest hardware | Making it run |
| `09_resources-and-learning.md` | Tested link register: docs, learning paths, Fellowship, courses, Fab, samples, forums, books | Finding the authoritative source |

## Positioning against the alternatives

For a Namibian residential project the honest comparison is:

- **Unreal Engine** — best-in-class real-time GI, strongest CAD/BIM ingest through Datasmith, mature cinematic output, first-class Python and now MCP automation. Steepest editor learning curve. Free below the revenue threshold. Windows-centric for archviz.
- **Twinmotion** (also Epic, built on Unreal) — dramatically faster to a result, far less control. Uses the same Datasmith ingest. A sensible front end when the deliverable is a quick client-facing walkthrough rather than a controlled hero image. Separate licence terms.
- **Blender + Cycles** (see domain `14`) — free, excellent for asset authoring and offline stills, no real-time GI of comparable quality, weak BIM ingest.
- **D5 Render / Lumion / Enscape** — faster to a competent result, closed pipelines, no scripting surface worth automating, licence cost per seat regardless of revenue.

Unreal wins when the same scene must serve stills, film, VR and an interactive model, and when you want the pipeline itself to be programmable. That is precisely the case here.

## Open questions

- Whether delivering a *packaged interactive build* to a client places the work on the royalty track or the seat track is a contract question. Epic's public wording turns on whether engine code is licensed to a third party; confirm in writing before pricing.
- Exact Fab licence-tier revenue thresholds were not retrievable from the licence page at the time of writing — **needs verification** against `https://www.fab.com/eula`.
- UE 5.8 release date was not stated on the pages fetched; only that 5.8 is the current documented release.

## Sources

- [Unreal Engine 5.8 Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation) — Epic Games, accessed 2026-08-25
- [Unreal Engine 5.8 Release Notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) — Epic Games, accessed 2026-08-25
- [Unreal Engine licensing options](https://www.unrealengine.com/en-US/license) — Epic Games, accessed 2026-08-25
- [Download Unreal Engine](https://www.unrealengine.com/en-US/download) — Epic Games, accessed 2026-08-25
- [Hardware and Software Specifications](https://dev.epicgames.com/documentation/en-us/unreal-engine/hardware-and-software-specifications-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [What's New](https://dev.epicgames.com/documentation/en-us/unreal-engine/whats-new) — Epic Games, accessed 2026-08-25
- [Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) — Epic Games, accessed 2026-08-25
- [Fab EULA](https://www.fab.com/eula) — Epic Games, accessed 2026-08-25
- [Scripting the Unreal Editor Using Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python) — Epic Games, accessed 2026-08-25
