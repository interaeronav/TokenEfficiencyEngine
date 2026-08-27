---
id: blender.overview
title: Blender domain overview
domain: software_blender
tags: [blender, overview, licensing, gpl, lts, gpu, cycles, eevee, architectural-visualisation, joinery, python]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Blender 5.2 LTS (July 2026). Content also valid for 5.0/5.1; differences from 4.5 LTS flagged inline."
unit_system: metric
sources:
  - {title: "Blender LTS releases", url: "https://www.blender.org/download/lts/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender releases", url: "https://www.blender.org/download/releases/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender 5.0 release notes", url: "https://www.blender.org/download/releases/5-0/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender 5.2 LTS release notes", url: "https://www.blender.org/download/releases/5-2/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "About Blender's licence", url: "https://www.blender.org/about/license/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender system requirements", url: "https://www.blender.org/download/requirements/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — GPU Rendering", url: "https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — Preferences: System (Cycles Render Devices)", url: "https://docs.blender.org/manual/en/latest/editors/preferences/system.html", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.interface_core_concepts, blender.python_api, blender.addons_architecture]
---

# Blender domain overview

**Summary.** Blender is a free, GPL-licensed, cross-platform 3D creation suite that covers modelling, procedural geometry, shading, lighting, rendering, compositing, animation and video editing in one binary, and exposes almost all of it through an embedded Python 3 interpreter (`bpy`). For architectural and joinery work its decisive advantages are: exact metric units, a non-destructive modifier stack, the Geometry Nodes procedural system, and a scripting API complete enough that an AI agent can build, measure, render and export a building without touching the GUI. Its decisive weakness is that it is not a parametric solid-body CAD system — there is no history tree, no constraint solver in the core, and no native BIM data model; those come from add-ons. This domain is written for driving Blender from code.

## Key facts

| Fact | Value |
|---|---|
| Current version | **5.2 LTS**, released 14 July 2026, supported until July 2028 |
| Previous LTS still supported | 4.5 LTS (4.5.12 as of 21 July 2026) |
| Release cadence | Feature release roughly every 4 months (Mar / Jul / Nov); the July release of each major series is designated **LTS** with 2 years of critical fixes |
| Recent releases | 5.2 LTS (Jul 2026), 5.1 (17 Mar 2026), 5.0 (18 Nov 2025), 4.5 LTS (15 Jul 2025), 4.4 (18 Mar 2025), 4.3 (19 Nov 2024), 4.2 LTS (16 Jul 2024) |
| Licence (application) | GNU GPL v2 **or later** |
| Licence (Cycles renderer) | Apache 2.0 |
| Licence (your artwork) | Yours entirely — "What you create with Blender is your sole property" |
| Licence (Python add-ons) | Must be GPL-compatible if published; may be sold, but the buyer receives full GPL rights |
| Embedded Python | 3.13 in the 5.x series (manifest wheel examples in the manual target `cp313`) — verify with `import sys; sys.version` |
| Render engines | Cycles (path tracer), EEVEE (real-time rasteriser + screen-space ray tracing), Workbench (solid/preview) |
| GPU backends | CUDA, OptiX (NVIDIA); HIP + HIP-RT (AMD); oneAPI + Embree-on-GPU (Intel); Metal + MetalRT (Apple Silicon) |
| Minimum hardware | 4-core CPU with SSE4.2, 8 GB RAM, 2 GB VRAM with OpenGL 4.3 or Vulkan 1.3 |
| Recommended hardware | 8-core CPU, 32 GB RAM, 8 GB VRAM |
| OS floor | Windows 8.1 64-bit; macOS 13 Ventura (**Apple Silicon required from Blender 5.0**); Linux with glibc ≥ 2.28 |
| Native file | `.blend` — a self-contained, forward/backward-tolerant binary database of datablocks |
| Default unit | 1 Blender unit = 1 metre when Unit System is Metric with Unit Scale 1.0 |

## Which version to install for this work

Run **5.2 LTS** unless a required add-on pins you lower. LTS matters here because architectural projects outlive feature releases: a house model started in August 2026 on 5.2 will still receive fixes in mid-2028, whereas 5.1 stopped receiving them the moment 5.2 shipped. Keep 4.5 LTS installed side by side only if you depend on an add-on that has not been ported.

Blender installs are portable and can coexist. Each version keeps its own configuration directory, so upgrading does not disturb an older setup, and a `config` folder placed next to the executable makes an install fully self-contained (native portable installation was added in 4.2 LTS).

Version-relevant features for this domain:

- **4.2 LTS** — EEVEE Next (the current EEVEE) replaced legacy EEVEE; the Blender Extensions platform launched; Khronos PBR Neutral view transform.
- **4.3** — light and shadow linking in EEVEE; Metallic BSDF; `for-each` zones in Geometry Nodes; SLIM minimum-stretch UV unwrapping (very useful for texturing curved joinery).
- **4.5 LTS** — conservative baseline; still widely targeted by add-ons.
- **5.0** — overhauled colour management with wide-gamut/HDR support, ACES 1.3 and 2.0 views, ACEScg working space; Cycles unbiased volumes and multi-bounce subsurface; adaptive subdivision out of experimental; Geometry Nodes Bundles and Closures, Volume Grid and SDF nodes, six new procedural modifiers (including Array and Scatter on Surface as node-based modifiers); native C++ FBX importer; up to 4× faster EEVEE material compilation on NVIDIA/Vulkan.
- **5.1** — incremental.
- **5.2 LTS** — node-based physics with an XPBD solver; Texture Cache (large reduction in memory and start-up time on texture-heavy archviz scenes); **Thin Wall** mode on the Principled BSDF (correct rendering of glass panes, blinds, paper, leaves); ~2× EEVEE speed-up on instance-heavy scenes (i.e. exactly the pavers/bricks/fence-post case); 35 new compositor nodes; online Essentials asset library with parametric materials and HDRIs downloaded on demand.

## GPL: what it actually constrains

Three separate questions get conflated constantly. Keep them apart.

1. **Your models, drawings and renders.** Not affected. The GPL covers the program, not its output. A `.blend` of a Namibian house, a cutting list generated from it, and a 4K render are all your property and can be sold, licensed or kept private without restriction. This is the point on which Blender differs most sharply from restrictive "learning edition" or "personal use" licences elsewhere.

2. **Python scripts and add-ons.** A script that imports `bpy` links against Blender and is a derivative work. If you **distribute** it, it must be released under a GPL-compatible licence, and your customers receive the same freedoms — including the right to redistribute. You may absolutely charge money for it; what you cannot do is forbid onward sharing. If you never distribute the script (it only runs on your own machines, or on your own render farm, or behind your own service), the GPL imposes nothing at all. This is the normal case for an agent-driven workflow: the automation scripts are internal tooling.

3. **Blender's own name and logo.** Governed by a separate trademark policy, not the GPL. Do not brand a product "Blender X" without checking that policy.

> ⚠️ If you intend to ship a commercial add-on to Namibian or South African clients, plan for the GPL from the start: put the licence header in every file, and price on service, support and updates rather than on copy restriction, because copy restriction is unenforceable.

## Hardware and GPU backends

Cycles is the physically based path tracer used for final architectural stills. It renders on CPU or GPU; GPU is normally 5–20× faster but is bounded by VRAM. EEVEE is a rasteriser with screen-space and ray-traced effects that renders a frame in milliseconds to a couple of seconds; it is the right engine for design iteration, client walkthroughs and animation.

Choose the backend in `Edit ▸ Preferences ▸ System ▸ Cycles Render Devices`, tick the individual devices, then set the per-scene device in `Properties ▸ Render ▸ Device`.

| Backend | Vendor / OS | Requirement |
|---|---|---|
| **CUDA** | NVIDIA, Windows + Linux | Compute capability ≥ 5.0 |
| **OptiX** | NVIDIA, Windows + Linux | Compute capability ≥ 5.0 **and driver ≥ 535**. Uses RTX hardware ray-tracing cores. The only GPU backend that supports OSL. |
| **HIP** | AMD, Windows + Linux | RDNA1 architecture or newer, discrete GPUs and APUs. `HIP RT` preference enables hardware ray tracing on RDNA2 and above. |
| **oneAPI** | Intel, Windows + Linux | Intel discrete GPUs (Arc). `Embree on GPU` preference enables hardware ray tracing. |
| **Metal** | Apple Silicon, macOS | macOS 13.0 or newer for all features. `MetalRT` = Off / On / Auto; it lowers memory on curve-heavy scenes. |

Practical notes:

- **OpenImageDenoise (OIDN)** is the default denoiser and is usually the highest quality. GPU acceleration for OIDN requires NVIDIA compute capability ≥ 7.0 (all RTX cards); it is available on all supported AMD, Intel and Apple Silicon GPUs. The OptiX denoiser remains useful on older NVIDIA hardware.
- `Distribute Memory Across Devices` lets a multi-GPU rig hold one copy of the scene instead of N copies, but currently only over **NVLink**.
- **Path Guiding is CPU-only** on every backend. If you use it for tricky interior daylight, you lose GPU speed.
- Command line: `blender -b file.blend -f 20 -- --cycles-device OPTIX`, with `+CPU` appended (e.g. `OPTIX+CPU`) to use both.

For a Namibian residential project — a house plus boundary wall, paving, and a joinery package — an 8-core CPU with 32 GB RAM and a 12–16 GB NVIDIA RTX card is the comfortable target. VRAM, not core count, is what fails first: 4K PBR texture sets on twenty materials will exhaust an 8 GB card long before geometry does. Blender 5.2's Texture Cache substantially relieves this.

## What Blender is good and bad at, for this project

**Good at**

- Exact metric modelling at building scale once units and clipping are set correctly.
- Non-destructive parametric-ish workflows via the modifier stack (Array/Mirror/Solidify/Bevel/Boolean/Screw).
- Genuinely procedural generation via Geometry Nodes — a wall generator, a staircase, a fence, a paver layout, a wardrobe driven by three numbers.
- Photoreal stills and animation, with free CC0 material and HDRI libraries.
- Total scriptability: every datablock is reachable from Python, and `blender -b -P script.py` runs headless with no display.
- Interoperability breadth: FBX, OBJ, glTF, USD, Alembic, STL, PLY natively; IFC, DXF and SVG through add-ons.

**Bad at (without add-ons)**

- Dimensioned, annotated 2D construction drawings. Bonsai and MeasureIt help; a dedicated CAD package is still better.
- Constraint-driven parametric sketching. CAD Sketcher adds it but is explicitly experimental.
- Boolean robustness on dirty CAD imports — Blender's mesh boolean is far better than it was, but triangulated non-manifold imports still break it.
- True solid modelling, fillets on arbitrary topology, and manufacturing tolerances. For CNC-bound joinery, model intent in Blender and take the fabrication geometry through Fusion or a CAM package.
- Native quantity take-off. You can script a cutting list (see file `06`), but nothing does it for you.

## Domain map

| File | Answers |
|---|---|
| `00_overview.md` | What Blender is, which version, what the licence permits, what hardware to buy |
| `01_interface-and-core-concepts.md` | The data model an automation script must understand: datablocks, users, collections, view layers, depsgraph, units, clipping |
| `02_modelling.md` | Mesh modelling for buildings and cabinetry: topology, the modifier stack in order, precision entry, snapping, curves for mouldings, carcass construction |
| `03_geometry-nodes.md` | Fields, domains, instancing, and five rebuildable architectural node graphs |
| `04_materials-and-shading.md` | Principled BSDF, procedural wood, UV strategy and texel density, free PBR sources and their licences, asset libraries |
| `05_lighting-and-rendering.md` | Cycles vs EEVEE, sampling and denoising, photometric light values, HDRIs, sun position for Okongo, colour management, passes, output |
| `06_python-api-and-automation.md` | `bpy` in depth, data-vs-operators, bmesh, mathutils, headless runs, add-on structure, MCP, four complete scripts |
| `07_import-export-and-interoperability.md` | Every format, its operator ID, and the axis/unit traps on the way to Unreal, Fusion, SketchUp, Revit and AutoCAD |
| `08_architecture-addons-and-tools.md` | The add-on shortlist with licence, cost, URL and maintenance status |
| `09_resources-and-learning.md` | Verified links: manual, API reference, training, forums, asset sources |

## How an AI agent should drive Blender

The recurring mistake is to script the GUI. Blender's operators (`bpy.ops.*`) are recordings of user gestures: they depend on the active object, the current mode, the mouse-hovered editor and the selection state, and they are slow because each call pushes an undo step and re-evaluates the dependency graph. Direct data manipulation (`bpy.data.*`, `object.modifiers.new()`, `mesh.from_pydata()`) is context-free, deterministic, orders of magnitude faster, and works identically in background mode. File `06` is the authority on this and should be read before any other file in the domain.

The second recurring mistake is unit drift. Set `scene.unit_settings.system = 'METRIC'`, `scale_length = 1.0`, `length_unit = 'METERS'`, and set camera and viewport clip start to ~0.01 m and clip end to ~1000 m before modelling anything at building scale. Everything downstream — exports, cutting lists, photometric lighting, IFC — depends on 1 unit meaning 1 metre.

## Sources

- [Blender LTS releases](https://www.blender.org/download/lts/) — Blender Foundation, accessed 2026-08-25
- [Blender releases index](https://www.blender.org/download/releases/) — Blender Foundation, accessed 2026-08-25
- [Blender 5.0 release notes](https://www.blender.org/download/releases/5-0/) — Blender Foundation, accessed 2026-08-25
- [Blender 5.2 LTS release notes](https://www.blender.org/download/releases/5-2/) — Blender Foundation, accessed 2026-08-25
- [Blender licence](https://www.blender.org/about/license/) — Blender Foundation, accessed 2026-08-25
- [System requirements](https://www.blender.org/download/requirements/) — Blender Foundation, accessed 2026-08-25
- [Manual — GPU Rendering](https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — Preferences ▸ System](https://docs.blender.org/manual/en/latest/editors/preferences/system.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Command Line Arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) — accessed 2026-08-25 via the local manual bundle
- [Manual — Blender's History](https://docs.blender.org/manual/en/latest/getting_started/about/history.html) — accessed 2026-08-25 via the local manual bundle

## Open questions

- The exact embedded Python version for 5.2 is inferred from the manual's Python-wheel example (`--python-version=3.13`); confirm at runtime with `sys.version` before pinning wheels in an extension manifest.
- Whether the EEVEE render-engine enum identifier is still `'BLENDER_EEVEE_NEXT'` in 5.x or has reverted to `'BLENDER_EEVEE'`. Confirm with `blender -E help` or by reading `bpy.context.scene.render.engine` on a default scene before hard-coding it in a script.
