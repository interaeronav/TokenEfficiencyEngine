---
id: blender.addons_architecture
title: Architecture and joinery add-ons for Blender
domain: software_blender
tags: [blender, addons, extensions, bonsai, blenderbim, archipack, building-tools, cad-sketcher, measureit, sun-position, node-wrangler, hard-ops, boxcutter, fluent, polyhaven, ifc]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Blender 5.2 LTS; each entry states its own minimum version where known"
unit_system: metric
sources:
  - {title: "Blender Extensions platform", url: "https://extensions.blender.org/", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Bonsai on Blender Extensions", url: "https://extensions.blender.org/add-ons/bonsai/", publisher: "IfcOpenShell", accessed: 2026-08-25}
  - {title: "Bonsai project site", url: "https://bonsaibim.org/", publisher: "IfcOpenShell contributors", accessed: 2026-08-25}
  - {title: "CAD Sketcher", url: "https://github.com/hlorus/CAD_Sketcher", publisher: "hlorus", accessed: 2026-08-25}
  - {title: "Building Tools", url: "https://github.com/ranjian0/building_tools", publisher: "ranjian0", accessed: 2026-08-25}
  - {title: "MeasureIt on Blender Extensions", url: "https://extensions.blender.org/add-ons/measureit/", publisher: "Antonio Vazquez", accessed: 2026-08-25}
  - {title: "MeasureIt_ARCH", url: "https://github.com/kevancress/MeasureIt_ARCH", publisher: "Kevan Cress", accessed: 2026-08-25}
  - {title: "Sun Position on Blender Extensions", url: "https://extensions.blender.org/add-ons/sun-position/", publisher: "Damien Picard", accessed: 2026-08-25}
  - {title: "Poly Haven Assets add-on", url: "https://github.com/Poly-Haven/polyhavenassets", publisher: "Poly Haven", accessed: 2026-08-25}
  - {title: "Fluent on Superhive", url: "https://superhivemarket.com/products/fluent", publisher: "CG Thoughts", accessed: 2026-08-25}
  - {title: "Blender Manual — Node Wrangler", url: "https://docs.blender.org/manual/en/latest/addons/node/node_wrangler.html", publisher: "Blender Foundation", accessed: 2026-08-25}
  - {title: "Blender Manual — How to Create Extensions", url: "https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [blender.import_export, blender.python_api, blender.resources]
---

# Architecture and joinery add-ons for Blender

**Summary.** Blender's core is deliberately general; the architectural capabilities — IFC, dimensioned drawings, constraint sketching, parametric building elements — come from add-ons. Since Blender 4.2 these are distributed as **extensions**, installed from `Edit ▸ Preferences ▸ Get Extensions` with no zip handling, and the official platform is https://extensions.blender.org. This file is a shortlist with licence, cost, URL and maintenance status for each. It is graded `confidence: medium` because add-on version support and pricing move faster than documentation does; verify before relying on any single entry.

## Key facts

| Add-on | Licence | Cost | Min. Blender | Maintained | Verdict |
|---|---|---|---|---|---|
| **Bonsai** (was BlenderBIM) | GPL-3.0-or-later | Free | 4.2 LTS | Yes (v0.8.5-post1) | **Essential** if IFC matters |
| **MeasureIt_ARCH** | GPL-3.0-or-later | Free | not stated | Yes (active dev branch) | **Essential** for drawings |
| **MeasureIt** (original) | GPL-3.0-or-later | Free | 5.0+ | Limited support (v1.8.4, Oct 2025) | Good for quick checks |
| **Sun Position** | GPL-3.0-or-later | Free | bundled | Yes (v4.4.0, Nov 2025) | **Essential** for daylight |
| **Node Wrangler** | GPL (bundled with Blender) | Free | bundled | Yes | **Essential** for shading |
| **CAD Sketcher** | GPL-3.0 | Free | 4.2 | Yes, but **experimental** | Promising, not production-safe |
| **Building Tools** | MIT | Free | 4.0 | Yes (v1.0.13, May 2025) | Good for massing/blockout |
| **Archipack** (Pro) | GPL-3.0 (open repo) | Paid (see notes) | see notes | Commercial version maintained | Strong parametric elements |
| **Poly Haven Assets** | GPL-3.0 | $5/mo Patreon or $69 Superhive | not stated | Yes (v1.2.2, Jul 2026) | Convenience, not necessity |
| **Fluent** | Proprietary | US$20 (US$29.90 Power Trip) | 3.6–5.1 | Yes | Best-in-class boolean cutter |
| **Hard Ops + Boxcutter** | Proprietary | US$38 bundle | not stated | Yes | Hard-surface workhorse |

## The extensions platform

From Blender 4.2, add-ons are **extensions**: a zip containing a `blender_manifest.toml` (SPDX licence, declared permissions for `files` / `network` / `clipboard` / `camera` / `microphone`, optional bundled Python wheels) and the code. Install from `Edit ▸ Preferences ▸ Get Extensions`, search, click Install — no manual file handling, and updates are handled by the platform. `Install from Disk` in the same dropdown handles a local zip.

Extensions are namespaced by repository, so a `user_default` extension and a bundled one can coexist. Legacy `bl_info`-based add-ons still load in 5.x, but new distribution should be an extension (file `06` covers authoring one).

For a practice, a **custom extension repository** — a directory or URL listed under `Preferences ▸ Extensions` — is the clean way to distribute in-house tools to a team. `blender --command extension server-generate` builds the listing file for a static-hosted repository.

---

## Bonsai (formerly BlenderBIM)

**What it does.** A native IFC authoring platform inside Blender, built on IfcOpenShell. It does not export to IFC — it edits the IFC file directly, so the Blender scene is a live view onto an IFC model. Feature areas: IFC model authoring (walls, slabs, doors, windows) and auditing, 2D drawing generation, structural analysis, MEP systems, costing and scheduling, facility management, clash detection, and integration with live building sensors.

**Licence.** GPL-3.0-or-later. **Cost.** Free and open source (funded through Open Collective).
**Version.** 0.8.5-post1 on the extensions platform; **minimum Blender 4.2 LTS**.
**Maintainer.** IfcOpenShell contributors. Actively maintained; 141 000+ downloads listed.
**Install.** `Preferences ▸ Get Extensions ▸` search "Bonsai". No administrator rights needed.
**URLs.** https://bonsaibim.org · https://docs.bonsaibim.org · https://extensions.blender.org/add-ons/bonsai/

**Why it matters here.** It is the only route in Blender that produces a coordinatable BIM deliverable — the format a Namibian or South African consultant team will actually accept alongside Revit and ArchiCAD models. It is also, effectively, the DXF/SVG documentation engine of last resort, because its drawing module produces real 2D output from the model.

**Caveats.** Bonsai objects are IFC-backed; editing them with ordinary mesh tools desynchronises the geometry from the IFC data. It is a substantial application in its own right and has a real learning curve. Renaming from "BlenderBIM Add-on" to "Bonsai" happened in 2024, so older tutorials use the old name.

## MeasureIt_ARCH

**What it does.** Adds dimensions, annotations, bar scales, text and tables, material hatching, view orientations and schedules to Blender, previewed live in the viewport and **exported as images, vector graphics or `.dxf` files**. This is the closest thing Blender has to a drafting layer.

**Licence.** GPL-3.0-or-later (confirmed from the repository LICENSE). **Cost.** Free.
**Maintainer.** Kevan Cress. Active — 1200+ commits on the `development` branch.
**URLs.** https://github.com/kevancress/MeasureIt_ARCH · docs at https://kevancress.github.io/MeasureIt_ARCH/

**Why it matters here.** It solves two of this domain's hardest problems at once: producing a dimensioned drawing from a Blender model, and getting vector output (SVG/DXF) out of Blender without writing an exporter. For a joinery shop drawing or a setting-out plan, this plus an orthographic camera is a workable documentation pipeline.

**Caveats.** Minimum Blender version is not stated on the repository page — check before installing on 5.2. It is a large add-on and its styling system takes time to learn.

## MeasureIt (original)

**What it does.** Lightweight measurement display in the 3D viewport sidebar (`View3D ▸ N ▸ View` tab): monitor multiple dimensions while editing, compare edge lengths, confirm unit scale.

**Licence.** GPL-3.0-or-later. **Cost.** Free. **Version.** 1.8.4 (24 Oct 2025), **Blender 5.0 and newer**.
**Maintainer.** Antonio Vazquez (antoniov). Was bundled with Blender up to 4.1; now offered on the extensions platform with limited support.
**URL.** https://extensions.blender.org/add-ons/measureit/

**Verdict.** Use it for quick sanity checks during modelling. Use MeasureIt_ARCH for anything that will be printed. Note that Blender's own `Overlays ▸ Measurement ▸ Edge Length / Face Area` and the Measure tool cover much of the same ground with no add-on at all.

## Sun Position

**What it does.** Computes real solar position from latitude, longitude, date, time and UTC zone using NOAA's solar calculator algorithms and Jean Meeus' *Astronomical Algorithms*. Two modes: **Sun Object Mode** (drive a Sun light and/or Sky Texture from location and time, animatable) and **Environment Mode** (synchronise an HDRI environment texture with a sun light so both rotate together). Panel lives in **World Properties**.

**Licence.** GPL-3.0-or-later. **Cost.** Free. **Version.** 4.4.0 (3 Nov 2025).
**Maintainer.** Damien Picard (originally Michael Martin). Ships with Blender as a bundled extension.
**URL.** https://extensions.blender.org/add-ons/sun-position/

**Why it matters here.** Direct answer to the shading question for a specific site — see file `05` for the Okongo, Ohangwena setup (≈17.4° S, 17.6° E, UTC+2 year-round) and for a dependency-free Python alternative that computes the same thing in a script.

## Node Wrangler

**What it does.** Bundled with Blender (`Preferences ▸ Add-ons`, search "Node Wrangler"). The two operations you will use daily:

- **`Shift-Ctrl-T` — Add Principled Setup.** Select a Principled BSDF, choose a folder of texture files, and it creates the Image Texture nodes, loads the images, **selects the appropriate colour space**, and wires them to the right inputs. Filename tag matching is configurable in the add-on preferences.
- **`Shift-Ctrl-LMB` — Preview Node Output** (Shader editor; `Shift-Alt-LMB` in Geometry Nodes). Instantly view any node's output.

Plus `Ctrl-T` texture setup with Texture Coordinate and Mapping, node merging with `Ctrl-=` / `Ctrl-Minus` / `Ctrl-8` / `Ctrl-0`, and lazy connect.

**Licence.** GPL, bundled. **Cost.** Free.
**URL.** https://docs.blender.org/manual/en/latest/addons/node/node_wrangler.html

## CAD Sketcher

**What it does.** Constraint-based 2D sketching inside Blender: define geometry with tangent, distance, angle and equal constraints; sketches stay editable and non-destructive.

**Licence.** GPL-3.0. **Cost.** Free. **Minimum Blender 4.2.**
**Maintainer.** hlorus. Active (888 commits, published roadmap, Discord, 71 open issues) — but the README is explicit: **"Experimental extension: This is still work in progress"**, and the developers caution against using it on production files without backups.
**URL.** https://github.com/hlorus/CAD_Sketcher

**Verdict.** The most interesting thing happening in Blender CAD, and the closest Blender gets to Fusion's sketch environment. Not yet something to bet a joinery package on. Prototype with it; keep backups; do not make it load-bearing.

## Building Tools

**What it does.** Rapid parametric building generation from a floorplan: floors, doors, windows, "multigroup" door-window combinations, roofs, stairs and balconies. Operates on selected geometry and generates the rest.

**Licence.** **MIT** (unusually permissive for a Blender add-on). **Cost.** Free.
**Version.** v1.0.13 (16 May 2025); stated support Blender 4.0.
**Maintainers.** ranjian0, luckykadam, MCrafterzz and others. 1607 commits, 1.5k stars, active Discord.
**URL.** https://github.com/ranjian0/building_tools

**Verdict.** Excellent for massing and blockout — generating a plausible building envelope in minutes for a context model or an early option study. The output is ordinary editable mesh, so it composes well with normal Blender workflow. Not a documentation or BIM tool. Verify 5.2 compatibility before installing.

## Archipack

**What it does.** Parametric architectural elements — walls with automatic junctions, windows, doors, stairs, roofs, fences, floors, kitchens — as fully editable objects with a proper parameter UI, plus a 2D layout/drawing capability in the Pro version.

**Licence.** The open repository (`s-leger/archipack`) is **GPL-3.0**, but it is old: the repository title states "Archipack for Blender 2.78 / 2.79". The actively maintained product is the commercial **Archipack Pro**, distributed from https://blender-archipack.org.
**Cost.** Paid — **price not verified** (the vendor site could not be fetched in this pass).
**URL.** https://blender-archipack.org · legacy source https://github.com/s-leger/archipack

**Verdict.** The most complete parametric-architecture toolset for Blender, and the one that behaves most like an architectural application. Verify current price, licence terms and Blender version support directly with the vendor before purchase. It is **not** listed on the Blender Extensions platform as far as could be checked.

## Poly Haven Assets

**What it does.** Puts Poly Haven's CC0 library (models, textures, HDRIs) directly into Blender's Asset Browser, with post-import resolution switching up to 8K, correct real-world texture scaling, displacement with adaptive subdivision, and HDRI rotation/brightness/colour-temperature control.

**Licence.** GPL-3.0 (the add-on). The **assets themselves are CC0** — free for any purpose including commercial, redistributable, no attribution required.
**Cost.** US$5/month on Patreon or US$69 on Superhive; Poly Haven state they will release it free once it reaches 5000 patrons.
**Version.** v1.2.2 (14 July 2026). Actively maintained.
**URL.** https://github.com/Poly-Haven/polyhavenassets · assets at https://polyhaven.com

**Verdict.** A convenience, not a necessity — you can download from polyhaven.com and build your own asset library for nothing (file `04`). The real-world scaling and resolution switching are worth the money if you texture a lot of buildings. Note the BlenderMCP server also offers Poly Haven downloading, free.

## Fluent

**What it does.** Non-destructive hard-surface modelling built on booleans — described as "the most accurate cutter add-on" for Blender. The **Power Trip** bundle adds plate, wire, pipe, grid, screw and cloth-panel generators.

**Licence.** Proprietary. **Cost.** US$20 base, US$29.90 for Power Trip.
**Version support.** Blender **3.6 through 5.1**, distributed as a Blender extension. Works with Cycles, EEVEE and third-party engines.
**Maintainer.** CG Thoughts. 16 100+ sales, 130 ratings.
**URL.** https://superhivemarket.com/products/fluent

**Verdict.** Directly relevant to joinery: rebates, grooves, service cut-outs, hinge bores and hardware recesses are all boolean operations, and Fluent makes them fast and non-destructive. Confirm 5.2 support before buying — the listing states up to 5.1.

## Hard Ops + Boxcutter

**What it does.** The long-established hard-surface modelling pair: Hard Ops is a workflow layer over modifiers, bevels, booleans and sharpening; Boxcutter is an interactive cutting tool. Sold as an "Ultimate Bundle".

**Licence.** Proprietary. **Cost.** US$38 (bundle). **Maintainer.** TeamC (masterxeon1001 et al.).
**URL.** https://superhivemarket.com/products/hardops-softools-blender-addon

**Verdict.** More than most architectural work needs, but if you also model hardware, ironmongery, light fittings or machinery, it pays for itself. Version support is not stated on the product listing — check before purchase.

## Also worth knowing

- **Blender's own Essentials asset library** — bundled, and from 5.2 extended with an **online** component: parametric materials, compositing effects and HDR backgrounds downloaded on demand, which keeps the install lean.
- **BlenderMCP** (MIT, free) — the agent bridge, covered in file `06`. Also provides Poly Haven, Sketchfab and Hyper3D asset access.
- **`ezdxf`** (MIT, Python library, not an add-on) — bundle it as a wheel in your own extension and write real DXF from a Blender scene. The most reliable DXF route available (file `07`).
- **Node Arrange / Node Pie / Ucupaint** — quality-of-life extensions visible on the platform; Ucupaint in particular is a layered-texture-painting system worth a look for weathered architectural surfaces.
- **Blender's built-in 3D-Print Toolbox equivalents** — `Overlays ▸ Mesh Analysis` (Thickness, Overhang, Intersections, Distorted Faces, Sharp Edges) covers the fabrication checks that used to need an add-on.

## Choosing a stack

For a Namibian residential project driven from an AI agent, the minimum viable stack is:

1. **Blender 5.2 LTS** + **Node Wrangler** + **Sun Position** (all bundled — zero installs).
2. **MeasureIt_ARCH** if drawings are a deliverable.
3. **Bonsai** if the consultant team works in IFC, or if the model must be coordinated.
4. **Building Tools** for fast massing, if early options matter.
5. **Fluent** only once boolean joinery detail becomes a daily task.

Everything else is optional. Resist installing more: every add-on is a version-compatibility liability at the next LTS upgrade, and an agent-driven workflow can replace most add-on convenience with a script.

## Sources

- [Blender Extensions platform](https://extensions.blender.org/) — accessed 2026-08-25
- [Bonsai on Blender Extensions](https://extensions.blender.org/add-ons/bonsai/) — accessed 2026-08-25
- [Bonsai project site](https://bonsaibim.org/) and [documentation](https://docs.bonsaibim.org/) — accessed 2026-08-25
- [CAD Sketcher](https://github.com/hlorus/CAD_Sketcher) — accessed 2026-08-25
- [Building Tools](https://github.com/ranjian0/building_tools) — accessed 2026-08-25
- [MeasureIt on Blender Extensions](https://extensions.blender.org/add-ons/measureit/) — accessed 2026-08-25
- [MeasureIt_ARCH](https://github.com/kevancress/MeasureIt_ARCH) and its [LICENSE](https://raw.githubusercontent.com/kevancress/MeasureIt_ARCH/development/LICENSE) — accessed 2026-08-25
- [Sun Position on Blender Extensions](https://extensions.blender.org/add-ons/sun-position/) — accessed 2026-08-25
- [Poly Haven Assets add-on](https://github.com/Poly-Haven/polyhavenassets) — accessed 2026-08-25
- [Fluent on Superhive](https://superhivemarket.com/products/fluent) — accessed 2026-08-25
- [Hard Ops / Boxcutter Ultimate Bundle on Superhive](https://superhivemarket.com/products/hardops-softools-blender-addon) — accessed 2026-08-25
- [Archipack legacy source](https://github.com/s-leger/archipack) — accessed 2026-08-25
- [Manual — Node Wrangler](https://docs.blender.org/manual/en/latest/addons/node/node_wrangler.html) — accessed 2026-08-25 via the version-matched local manual bundle
- [Manual — How to Create Extensions](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html) — accessed 2026-08-25 via the local manual bundle
- [Blender 5.2 LTS release notes (online Essentials library)](https://www.blender.org/download/releases/5-2/) — accessed 2026-08-25

## Open questions

- **Archipack Pro price, current version and Blender version support are unverified** — https://blender-archipack.org could not be fetched (robots.txt timeout). Confirm with the vendor before purchase.
- MeasureIt_ARCH's minimum Blender version is not stated on its repository page — **needs-verification** against 5.2.
- Building Tools states Blender 4.0 support; 5.2 compatibility is **unverified**.
- Hard Ops / Boxcutter Blender version support is not stated on the product listing — **unverified**.
- Fluent's listing states support up to Blender 5.1; 5.2 support is **unverified**.
- Blender Market has been rebranded **Superhive** (`blendermarket.com` redirects to `superhivemarket.com`); older links and tutorials still say Blender Market.
- No DXF import/export extension surfaced on the extensions platform in this pass; if one exists, this list misses it.
