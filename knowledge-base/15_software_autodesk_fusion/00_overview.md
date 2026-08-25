---
id: fusion.overview
title: Autodesk Fusion — what it is, how it is licensed, and the domain map
domain: 15_software_autodesk_fusion
tags: [fusion, fusion-360, autodesk, cad, cam, cae, parametric, cloud, overview, domain-map]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release; cloud product, continuously updated. Facts checked 2026-08-25."
unit_system: metric
sources:
  - {title: "Autodesk Fusion overview", url: "https://www.autodesk.com/products/fusion-360/overview", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion for personal use", url: "https://www.autodesk.com/products/fusion-360/personal", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "System requirements for Autodesk Fusion", url: "https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-Fusion-360.html", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion extensions", url: "https://www.autodesk.com/products/fusion-360/extensions", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "FusionAPIReference", url: "https://github.com/AutodeskFusion360/FusionAPIReference", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
related: [fusion.licensing, fusion.api, joinery.overview, joinery.cabinetmaking]
---

# Autodesk Fusion — what it is, how it is licensed, and the domain map

**Summary.** Autodesk Fusion (called **Fusion 360** until Autodesk dropped the "360" during 2024) is a cloud-connected, subscription-only product development platform that puts parametric solid modelling, surface and mesh modelling, assembly and motion, 2D drawings, FEA simulation, ECAD/PCB and 2.5- to 5-axis CAM into one application and one file. For a joinery and residential-fitout practice its value is very specific: it is the cheapest credible route from a parametric cabinet model to a nested, post-processed G-code file, and its Python API is good enough that an AI agent can drive the whole chain. Its costs are equally specific: it is subscription-only, it will not work usefully offline for long, and several capabilities a shop actually needs (true-shape nesting, advanced toolpaths) sit behind a paid extension.

## Key facts

| Item | Value | Verified |
|---|---|---|
| Current name | **Autodesk Fusion** (formerly Fusion 360) | autodesk.com product page, 2026-08-25 |
| Headline commercial price | **US$57 / month, billed annually** | autodesk.com pricing, 2026-08-25 |
| Personal-use licence | Free, renewable, **3-year** term; user must generate **< US$1,000/yr** from it | autodesk.com/products/fusion-360/personal, 2026-08-25 |
| Platforms | Windows, macOS, and a browser client | Autodesk system requirements page, 2026-08-25 |
| Native file | `.f3d` (design), `.f3z` (archive with references) | see `10_interoperability-and-alternatives.md` |
| Scripting languages | **Python** and **C++** | Fusion API reference |
| API reference corpus version | "Updated as of Fusion **May 2026** Major Release" | github.com/AutodeskFusion360/FusionAPIReference |
| Internal API units | **centimetres** for length, **radians** for angle | `Design.modifyParameters` docs |
| Extension consolidation | Machining + Nesting & Fabrication + Additive → one **Manufacturing Extension** | autodesk.com extension pages, 2026-08-25 |

> ⚠️ Fusion is **rental software with a hard cloud dependency**. There is no perpetual licence and no meaningful long-term offline mode. If a client contract requires you to hand over editable design files that outlive your subscription, plan the STEP/DXF/PDF deliverable from day one (see `10_interoperability-and-alternatives.md`).

## The unified model: one file, many workspaces

Fusion's central architectural claim is that CAD, CAM, CAE, ECAD and documentation all live in a single document and a single feature timeline. In practice you switch **workspaces** from the selector at the top-left of the window:

- **Design** — parametric solid, surface, mesh, sheet metal, plastic and form (T-Spline/sculpt) modelling, plus the Assemble tools (components, joints, contact sets, motion study). This is where 95 % of joinery work happens.
- **Generative Design** — goal-driven geometry synthesis. Irrelevant to cabinetmaking, occasionally relevant to bracketry.
- **Render** — local and cloud raytracing. Adequate for client presentation of a kitchen, though Blender or Unreal will do better (see the sibling domains).
- **Animation** — exploded views and assembly sequences. The exploded state can be pulled into a drawing.
- **Simulation** — FEA. Static stress is the one you will actually use; see `08_simulation-and-analysis.md`.
- **Manufacture** — CAM. Setups, stock, toolpaths, simulation, post-processing to G-code. See `06_cam-and-manufacturing.md`.
- **Drawing** — 2D shop drawings, sections, parts lists, DXF/PDF output. See `07_drawings-and-documentation.md`.
- **Electronics** — schematic and PCB (the former Eagle). Out of scope for this domain except as a licensing line item.

The practical consequence for a joinery shop: **a change to the `CarcassWidth` user parameter propagates through the model, the assembly, the drawing dimensions, the parts list and — if the toolpaths are still associative — the CAM operations**, in one recompute. No other tool in this price band does that end-to-end.

The practical *cost* of that unification is that everything is coupled. A sloppy sketch that fails to solve at parameter `W = 900` will break the drawing and invalidate the toolpaths in the same instant. The discipline described in `02_sketching-and-constraints.md` is not pedantry; it is what makes the parametric promise survive contact with a real project.

## Cloud dependency and offline behaviour

Fusion is a desktop application with a mandatory cloud back end.

- **Data lives in Autodesk's cloud** (a "hub", with projects and folders) by default. The desktop app maintains a local cache under the user profile.
- **Licence checks** are periodic. You can work offline for a limited period, but the entitlement re-check will eventually block you. Autodesk has historically documented an offline grace window measured in days, not weeks; treat "two weeks of no internet" as a hard planning risk, not a supported mode. `needs-verification` on the exact current number of days.
- **Saving while offline** queues the save locally and uploads when connectivity returns. This works, but conflicts are resolved crudely and multi-machine editing while offline is a reliable way to lose work.
- **Some functions are cloud-only**: cloud rendering, most simulation solves, generative design, and certain heavy CAM/nesting operations. These historically consumed *cloud credits* / *tokens*; Autodesk has since moved most simulation solving into the Simulation Extension as "unlimited cloud-based solving". See `01_licensing-and-editions.md`.

**[NA]** This matters more in Namibia than in Europe. On a Windhoek fibre line Fusion is fine; on an LTE link at a site outside Otjiwarongo, expect slow first-open of large assemblies and stalled uploads. Practical mitigations: keep site work in a small number of small documents, use `.f3z` archives as a genuine local backup after every milestone, and never let the only copy of a week's modelling sit in the upload queue.

> ⚠️ **Export a `.f3d`/`.f3z` archive and a STEP file at every project milestone and store them off-Autodesk.** A lapsed subscription, a hub migration or a lost login makes cloud-only data unreachable.

## System requirements

Autodesk's requirements page (checked 2026-08-25) lists Windows, macOS and a web browser client as supported platforms, and warns that a "minimum" specification is "generally sufficient for basic modeling activities like learning CAD or slicing STLs, but may struggle to navigate hundred-component assemblies, long chains of parametric design history, or mission-critical toolpaths." The page is JavaScript-rendered and the exact figures could not be extracted programmatically; the following working figures are the practical shop guidance rather than a quotation, and the exact numbers are `needs-verification` against the live page:

- **CPU**: a modern 4-core x86-64 with good single-thread performance. Fusion's solver and timeline recompute are largely single-threaded; clock speed beats core count for modelling. CAM toolpath generation *does* use multiple cores.
- **RAM**: 16 GB is the realistic floor for a kitchen-sized assembly; 32 GB if you also run Blender or a slicer alongside.
- **GPU**: any DirectX 11/Metal-capable discrete GPU with ≥ 4 GB VRAM. Fusion's viewport is not demanding; integrated graphics work but stutter on large assemblies.
- **Apple Silicon**: natively supported. Fusion runs well on M-series Macs.
- **Linux**: **not supported.** There is no Linux build. Community WINE/Bottles installs exist and break regularly. If your studio is Linux-first, this alone may decide against Fusion — see `10_interoperability-and-alternatives.md`.
- **Display**: 1920 × 1080 minimum in practice. Fusion's dialogs assume horizontal room.
- **Network**: a stable connection with reasonable latency to Autodesk's servers matters more than raw bandwidth.

## Where Fusion sits for a joinery / residential practice

Fusion is the right tool when **the geometry must be manufactured**, and the wrong tool when the geometry is architectural or presentational.

**Fusion wins at:** parametric carcasses driven by width/height/depth; hardware placement to a real drilling pattern; dogbone-corrected CNC pockets; nested cut lists; associative shop drawings; and a Python API that can generate a whole cabinet run from a spreadsheet.

**Fusion loses at:** building-scale modelling (use Revit/Archicad or a BIM tool), free-form visualisation and materials (Blender/Unreal), site-scale surveying and setting-out (AutoCAD/Civil), and cabinet-industry production management with pricing, labels and machine-native output (Polyboard, Cabinet Vision, Mozaik — see `10_interoperability-and-alternatives.md`).

A realistic Namibian residential-joinery stack looks like: architectural model and drawings in the architect's tool → joinery package modelled parametrically in Fusion → cut list and nested DXF out of Fusion → CNC router driven by Fusion CAM or by the machine vendor's own CAM → renders in Blender from a STEP or OBJ export.

## The domain map

| File | Covers | Read it when |
|---|---|---|
| `00_overview.md` | This file: product, cloud model, requirements, map | Orientation |
| `01_licensing-and-editions.md` | Subscription, personal use, education, startup, extensions, prices with dates | Before you commit money or a client deliverable |
| `02_sketching-and-constraints.md` | Sketch planes, constraints, solver behaviour, robust sketching | Every time a model breaks on a parameter change |
| `03_modelling-and-parameters.md` | Features, timeline, user parameters, expressions, configurations, a parametric cabinet | Building the carcass |
| `04_assemblies-and-joints.md` | Components vs bodies, joints, rigid groups, contact sets, interference | Structuring a multi-cabinet run |
| `05_sheet-goods-and-joinery-workflow.md` | Board thicknesses, dogbones, dado/rabbet/finger joints, 32 mm system, nesting, cut lists, DXF out | The daily joinery pipeline |
| `06_cam-and-manufacturing.md` | Setups, WCS, stock, 2D/3D toolpaths, feeds and speeds, tabs, simulation, post-processors | Cutting anything |
| `07_drawings-and-documentation.md` | Sheets, views, sections, dimensions, parts lists, balloons, DXF/PDF | Handing work to a joiner |
| `08_simulation-and-analysis.md` | FEA study types, meshing, loads, a cantilever shelf worked example | Justifying a shelf span or a bracket |
| `09_api-and-automation.md` | **The key file.** Python API, object model, scripts vs add-ins, runnable examples, APS | Driving Fusion from an agent |
| `10_interoperability-and-alternatives.md` | Formats in/out, round-tripping, honest comparison with SolidWorks, Onshape, Rhino, FreeCAD, Shapr3D, SketchUp, Polyboard | Choosing or defending the tool |
| `11_resources-and-learning.md` | Tested link register: docs, API reference, forums, add-in repos, channels, books | Getting unstuck |

## Naming and version conventions used in this domain

Autodesk ships Fusion continuously and names releases by month ("the May 2026 major release"). There are no version numbers a user should quote in a specification. Where this domain cites API behaviour, it is against the API reference corpus dated **May 2026**. Where a feature has been **retired** — and several have, notably `Sketch.saveAsDXF` (retired July 2025) and `CAM.postProcess` / `CAM.postProcessAll` — the file says so and gives the replacement.

When writing specifications or contracts, name the deliverable format, not the software version: "STEP AP214 solid model plus dimensioned PDF drawings at 1:10 and DXF cutting files per panel" is enforceable; "a Fusion file" is not.

## Sources

- [Autodesk Fusion overview](https://www.autodesk.com/products/fusion-360/overview) — Autodesk, accessed 2026-08-25
- [Fusion for personal use](https://www.autodesk.com/products/fusion-360/personal) — Autodesk, accessed 2026-08-25
- [System requirements for Autodesk Fusion](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/System-requirements-for-Autodesk-Fusion-360.html) — Autodesk, accessed 2026-08-25
- [Fusion extensions](https://www.autodesk.com/products/fusion-360/extensions) — Autodesk, accessed 2026-08-25
- [FusionAPIReference repository](https://github.com/AutodeskFusion360/FusionAPIReference) — Autodesk on GitHub, accessed 2026-08-25
- [Fusion API reference, browsable](https://autodeskfusion360.github.io/FusionAPIReference/) — Autodesk, accessed 2026-08-25

## Open questions

- Exact current offline grace period before the licence check blocks use. The autodesk.com pages are JavaScript-rendered and the number could not be extracted. `needs-verification`.
- Exact minimum/recommended CPU, RAM, GPU and VRAM figures from the live system requirements page (same rendering problem).
- Whether cloud credits still exist as a purchasable unit for any Fusion function after the 2025–26 extension consolidation, or whether all cloud solving is now bundled into extensions.

