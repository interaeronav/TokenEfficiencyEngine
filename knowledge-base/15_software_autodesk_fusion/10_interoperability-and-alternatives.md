---
id: fusion.alternatives
title: File formats, round-tripping and honest alternatives to Fusion
domain: 15_software_autodesk_fusion
tags: [fusion, interoperability, step, iges, dxf, dwg, stl, 3mf, obj, usd, sketchup, blender, unreal, solidworks, onshape, rhino, grasshopper, freecad, shapr3d, polyboard, cabinet-vision, mozaik]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release. Competitor pricing checked 2026-08-25."
sources:
  - {title: "Fusion API Reference — ExportManager", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Onshape pricing", url: "https://www.onshape.com/en/pricing", publisher: "PTC Onshape", accessed: 2026-08-25}
  - {title: "Rhino pricing (US)", url: "https://www.rhino3d.com/sales/north-america/United_States/", publisher: "Robert McNeel & Associates", accessed: 2026-08-25}
  - {title: "SketchUp plans and pricing", url: "https://sketchup.trimble.com/en/plans-and-pricing", publisher: "Trimble", accessed: 2026-08-25}
  - {title: "Shapr3D pricing", url: "https://www.shapr3d.com/pricing", publisher: "Shapr3D", accessed: 2026-08-25}
  - {title: "FreeCAD downloads", url: "https://www.freecad.org/downloads.php", publisher: "FreeCAD", accessed: 2026-08-25}
  - {title: "SOLIDWORKS how to buy", url: "https://www.solidworks.com/how-to-buy", publisher: "Dassault Systèmes", accessed: 2026-08-25}
  - {title: "Autodesk Fusion pricing", url: "https://www.autodesk.com/products/fusion-360/pricing", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.licensing, fusion.overview, fusion.joinery_workflow]
---

# File formats, round-tripping and honest alternatives to Fusion

**Summary.** Fusion reads and writes the usual mechanical CAD formats and a reasonable set of mesh and cloud formats, but it is not a good archive format and it is a poor citizen in an architectural workflow. This file covers what actually survives each conversion, how to round-trip with Blender, Unreal, AutoCAD, Inventor and SolidWorks, and then compares Fusion honestly against the tools a joiner or architect would realistically choose instead — including the cabinet-specific packages (Polyboard, Cabinet Vision, Mozaik) whose whole reason for existing is that a general CAD tool is the wrong shape for a cabinet shop.

## Key facts

| Format | In | Out | What survives |
|---|---|---|---|
| **`.f3d` / `.f3z`** | yes | yes | Everything. `.f3z` is an archive including externally referenced components |
| **STEP** (`.stp`, `.step`) | yes | yes | Exact B-rep solids, assembly structure, component names. **No features, no parameters** |
| **IGES** (`.igs`) | yes | yes | Surfaces; solids often arrive as unstitched surface sets. Use STEP instead |
| **SAT** (`.sat`, ACIS) | yes | yes | Exact solids. Good for older Autodesk/ACIS-based tools |
| **SMT** (Autodesk ShapeManager) | yes | yes | Exact solids; Autodesk-internal |
| **DWG** | yes | yes (from Drawing; also 2D) | 2D geometry, layers, text. 3D DWG import is limited |
| **DXF** | yes | yes (sketch / flat pattern / drawing) | 2D curves. **The CNC deliverable** |
| **STL** | yes (as mesh) | yes | Triangles only. Lossy, one-way in practice |
| **3MF** (`C3MFExportOptions`) | yes | yes | Triangles + colour + units. Better than STL for 3D printing |
| **OBJ** | yes (mesh) | yes | Triangles + UVs + material references. The Blender bridge |
| **USD** (`USDExportOptions`) | — | yes | Scene graph, transforms, materials. **The modern route into Omniverse/Unreal/Blender** |
| **SketchUp** (`.skp`) | yes (import) | no | Faces become a mesh body. One-way |
| **Inventor** (`.ipt`, `.iam`) | yes | no | Solids and assembly; not features |
| **SolidWorks** (`.sldprt`, `.sldasm`) | yes | no | Solids and assembly; not features |
| **Rhino** (`.3dm`) | yes | no | NURBS surfaces and solids |
| **CATIA / NX / Creo / Solid Edge / Pro-E** | yes | no | Solids |

> ⚠️ **Fusion imports far more than it exports.** It reads native SolidWorks, Inventor, Rhino, SketchUp, CATIA, NX and Creo files; it exports only neutral formats. That asymmetry is deliberate and it is a lock-in mechanism. Plan your exit before you need it.

## The archive problem

A `.f3d` file is only readable by Fusion, and Fusion only runs while you pay. For any project with a contractual life beyond your subscription — which is every building project — you need a second archive.

**Minimum archive set per milestone, stored outside Autodesk:**

1. **`.f3z` Fusion archive** — full fidelity if you ever return to Fusion.
2. **STEP AP214** of the whole assembly, and per major component. Readable by everything, forever.
3. **DXF per panel** — the manufacturing intent.
4. **PDF drawing set** — the contractual document.
5. **CSV cut list and parts list** — the data.
6. A short **README** naming the software version, the units, the board thicknesses assumed and the date.

`ExportManager` makes items 1–3 a twenty-line script (`09_api-and-automation.md`). Run it as a pre-commit hook on your project repository.

## Round-tripping with the tools next to Fusion

### Blender

**Fusion → Blender**, for rendering and client visuals:
- **Best route: OBJ or USD.** Both carry the tessellated geometry with material assignments. USD additionally carries the scene hierarchy and transforms.
- **STEP into Blender** needs an importer add-on (STEPper, or via FreeCAD conversion). Worth it when you want to re-tessellate at a chosen quality rather than accepting Fusion's mesh.
- **Mesh quality** is the whole game. Export at a fine refinement or you get faceted curves on a shelf edge. In the STL/OBJ dialog, use **High** or a custom refinement with a small surface deviation.
- **Scale**: Fusion exports in mm by default and Blender's default unit is metres. Set the export unit explicitly and check a known dimension after import.
- Fusion's materials do **not** translate meaningfully. Re-author PBR materials in Blender; see the `14_software_blender` domain.

**Blender → Fusion**: only as mesh. Fusion can convert a mesh body to a B-rep (**Mesh tab → Modify → Convert Mesh**) but the result on anything organic is unusable. Treat this as one-way.

### Unreal Engine

- **Datasmith** is the supported bridge for architectural visualisation; Fusion has no Datasmith exporter, so the practical routes are **USD** or **FBX via Blender**.
- For an interactive kitchen walkthrough: Fusion → USD → Blender (clean up, assign materials, decimate) → FBX/USD → Unreal. See the `13_software_unreal_engine` domain.
- Keep the Fusion model as the dimensional master; never edit geometry downstream and expect it to come back.

### AutoCAD

- **Fusion → DWG** from the Drawing workspace is the standard hand-off to an architect. Expect to fix layers, line weights and text styles; Fusion's drawing standards do not map cleanly onto an architectural template.
- **AutoCAD → Fusion**: import a DWG or DXF as a **sketch** (`Insert → Insert DXF`) to trace a site survey or a supplied elevation. Explode blocks and purge before importing — Fusion chokes on heavy architectural DWGs and will import thousands of curves you do not want.
- **[NA]** Architects in Namibia and South Africa mostly issue DWG or PDF. A dimensioned PDF plus a site check beats a DWG you have not verified.

### Inventor

Same-vendor, but **not** the same kernel workflow. Fusion reads `.ipt`/`.iam` directly; it cannot write them. Autodesk positions Inventor as the mechanical-engineering product and Fusion as the integrated one; there is no feature-level round trip. If your client's engineer works in Inventor, exchange STEP and accept the loss of history.

### SolidWorks

Fusion imports `.sldprt` and `.sldasm` natively, geometry and assembly structure only. Going the other way is STEP. Feature-level translation between the two does not exist in either direction; anyone claiming otherwise is selling something.

## The alternatives, honestly compared

Prices checked **2026-08-25**, USD unless stated. Re-verify before quoting.

### SolidWorks (Dassault Systèmes)

The mechanical-engineering default. Deeper assembly tools, better drawings, far better sheet metal and weldments, a huge ecosystem of add-ins, and a genuine offline perpetual option.

**Cost:** Dassault no longer publishes list prices; the "How to Buy" page directs you to a reseller and says only that "yearly, quarterly, and perpetual options" exist. Historically Standard was around US$4,000 perpetual plus ~US$1,300/yr maintenance, with term licences in the low thousands per year. **`needs-verification`.**

**Where it wins:** large assemblies, drawings that meet a manufacturing standard, weldments and steel frames, a deep local reseller/support network, offline working, and the ability to hand a file to almost any subcontractor.

**Where it loses for a joinery practice:** cost, no integrated CAM at that price (CAM is an add-on or a separate product), Windows-only, and vastly more capability than a cabinet shop uses.

### Onshape (PTC)

Fully browser-based, genuinely multi-user real-time, with the best version control in CAD (branching and merging, like git). FeatureScript lets you write custom features in a typed language — a more principled automation story than Fusion's, though with a smaller surface.

**Cost (checked 2026-08-25):** Free plan **$0** with "unlimited **public** storage" — every document is public, non-commercial only. **Standard $1,500/user/year**, **Professional $2,500/user/year** (adds advanced PDM, simulation, rendering and CAM), Enterprise on application.

**Where it wins:** collaboration, no installs, no file management, runs on anything including a Chromebook, and branch/merge for design variants.

**Where it loses:** more than twice Fusion's price; CAM only at the Professional tier; nothing cabinet-specific; and the free tier's public-by-default storage disqualifies it for client work.

### Rhino + Grasshopper (McNeel)

**Cost (checked 2026-08-25):** Rhino 8 commercial **US$995** full, **US$595** upgrade; educational **US$195** full, **US$95** upgrade. "All purchased licenses are permanent and do not expire" — **a perpetual licence, no subscription.** Grasshopper is included with Rhino 6 and later.

**Where it wins:** the best price-to-capability ratio in the list; superb NURBS surfacing for anything shaped; **Grasshopper** is the strongest visual parametric environment available and has a mature furniture/fabrication ecosystem (OpenNest for nesting, Lunchbox, Karamba for structure); reads and writes almost everything; runs on Windows and macOS; enormous architectural user base, so your architect probably has it.

**Where it loses:** **no history-based parametric modelling** — Rhino is a direct modeller, and Grasshopper is a separate definition rather than an editable feature tree; **no integrated CAM** (RhinoCAM/MadCAM are paid add-ons); drawings are weaker than Fusion's; and Grasshopper is a real programming environment with a real learning curve.

**Verdict for a Namibian joinery/architecture practice:** Rhino + Grasshopper is the strongest *alternative* to Fusion, and arguably the strongest *complement*. A perpetual US$995 licence that will still open your files in 2040 answers Fusion's archive problem directly.

### FreeCAD

Open source (LGPL), current stable **1.1.3** (checked 2026-08-25). Part Design and Sketcher for parametric solids, an Assembly workbench, FEM, a CAM/Path workbench, plus BIM and Geodata workbenches. Everything is scriptable in Python and the whole application is Python-extensible.

**Cost:** free. Runs on Linux, which Fusion does not.

**Where it wins:** zero cost, no lock-in, real Python automation, Linux support, and a file format you will always be able to open.

**Where it loses:** the sketcher and the topological naming behaviour have historically been the weak points (the 1.0 release addressed much of this, but a complex model still breaks more readily than in Fusion); the CAM workbench is usable but immature next to Fusion's; drawings are basic; and you will spend hours on things Fusion does in minutes.

**Honest use:** excellent as a **format converter and a scripting host** (FreeCAD's Python can read STEP and write DXF headlessly on a server) even if you model in Fusion. Viable as a primary tool if you are ideologically committed and patient.

### Shapr3D

**Cost (checked 2026-08-25):** Free tier — up to 2 projects, basic imports (XT, STEP, IGES, DWG, STL), low-resolution 3MF/STL export only. **Pro from US$228/year billed annually** (the site also advertises a monthly option; the rendered figure was US$19/month, so re-verify the monthly rate). Enterprise on application. Runs on iPad, Mac, Windows and Vision Pro, three devices per account.

**Where it wins:** the best direct-modelling touch/pencil interface in existence; extraordinary for sketching a piece of furniture in front of a client on an iPad; Parasolid kernel, so exports are clean; technical drawings included at Pro.

**Where it loses:** **no history-based parametrics**, **no CAM**, **no API/scripting**. It is a concept and communication tool, not a production tool.

**Use it as:** the front end. Shape the idea on an iPad with the client, export STEP, build the production model in Fusion.

### SketchUp (Trimble)

**Cost (checked 2026-08-25):** free web version; **Go US$129/year** (iPad and web only); **Pro US$399/year** — includes **LayOut** and "1000+ extensions"; **Studio US$819/year** (Windows only, adds rendering).

**Where it wins:** the fastest tool in the world for blocking out a room, and the one your interior designer and your architect already use. LayOut produces decent presentation documents. The extension ecosystem includes real cabinet tools — **CutList Bridge**, **OpenCutList** (free), **Estimator**, and several cabinet generators.

**Where it loses:** it is a **surface/mesh modeller**, not a solid modeller. There is no parametric history, no constraint solver, no real dimensional rigour, no CAM. A SketchUp "cabinet" is a box of faces that happens to look right; nothing enforces that the panels are 17.9 mm or that the dado matches.

**Verdict:** superb for design communication, dangerous as a production source. Many small joinery shops do run on SketchUp + OpenCutList and produce good work — but the discipline lives in the joiner's head, not in the model.

### Cabinet-specific software

These exist because a general CAD tool models *shapes* while a cabinet shop needs *products with rules*: a library of cabinet types where changing the width automatically re-derives the panels, the hardware, the drilling, the edging, the labels, the nest and the price.

| Product | Model | Indicative cost | Where it wins |
|---|---|---|---|
| **Polyboard** (Wood Designer, FR/UK) | Perpetual, tiered by module (design → cutting lists → CNC/DXF → nesting) | Low four figures EUR/GBP for a working configuration; **`needs-verification`** | Rule-based cabinet library, method-driven construction, cutting lists and DXF/CNC output, small-shop pricing. Widely used by one- and two-person shops |
| **Cabinet Vision** (Hexagon) | Subscription/perpetual, tiered | Serious money — five figures for a full CNC-enabled seat; **`needs-verification`** | Industry standard for mid-size cabinet manufacturing. Full drawing, costing, labelling, nesting, machine-native output |
| **Mozaik** | Subscription | Mid four figures/yr; **`needs-verification`** | Popular in North America, strong CNC output, easier than Cabinet Vision |
| **Microvellum** | Subscription, AutoCAD-based | Enterprise | Deep manufacturing automation, ties into ERP |
| **imos, ARDIS, SmartWOP, WoodWOP** | Vendor/enterprise | Enterprise | Tied to specific machine makers (Homag, Biesse) |

**When to buy one of these instead of Fusion:** when you make cabinets *repeatedly* to a house standard and your bottleneck is the office, not the design. If you produce 20+ kitchens a year, a rule-based cabinet package will pay for itself in a season, because the operator draws a wall and the software emits the panels, the hardware schedule, the labels, the nest and the price.

**When Fusion is still right:** when the work is bespoke rather than modular — a one-off reception desk, a curved bar front, a piece with real geometry in it — or when you need CAM for things that are not cabinets, or when you want to *program* your own rules rather than buy someone else's.

## The decision, for this project

For a Namibian residential/joinery practice that drives software from AI agents, the defensible stack is:

- **Fusion** as the production CAD/CAM master, at ~US$684/yr, because of the parametric model, the integrated CAM, and — decisively — the Python API that an agent can drive. Nothing else in the price band offers all three.
- **Rhino** (US$995, perpetual) as insurance and as the surfacing/Grasshopper tool. It reads Fusion's STEP forever, regardless of subscription state.
- **Blender** (free) for visualisation, fed by USD or OBJ.
- **A scripted archive step** producing `.f3z` + STEP + DXF + PDF + CSV at every milestone.
- **Revisit a cabinet-specific package** (Polyboard first, on cost) once the kitchen count per year passes about 15.

The one thing not to do is to model production joinery in SketchUp because it is fast, and then discover at cutting time that nothing in the model is dimensionally trustworthy.

## Sources

- [Fusion API Reference — ExportManager](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager.htm) — Autodesk, accessed 2026-08-25
- [Onshape pricing](https://www.onshape.com/en/pricing) — PTC Onshape, accessed 2026-08-25
- [Rhino pricing (United States)](https://www.rhino3d.com/sales/north-america/United_States/) — Robert McNeel & Associates, accessed 2026-08-25
- [SketchUp plans and pricing](https://sketchup.trimble.com/en/plans-and-pricing) — Trimble, accessed 2026-08-25
- [Shapr3D pricing](https://www.shapr3d.com/pricing) — Shapr3D, accessed 2026-08-25
- [FreeCAD downloads](https://www.freecad.org/downloads.php) — FreeCAD, accessed 2026-08-25
- [SOLIDWORKS how to buy](https://www.solidworks.com/how-to-buy) — Dassault Systèmes, accessed 2026-08-25
- [Autodesk Fusion pricing](https://www.autodesk.com/products/fusion-360/pricing) — Autodesk, accessed 2026-08-25

## Open questions

- **SOLIDWORKS list pricing** is no longer published; the historical figures given are `needs-verification`.
- **Polyboard, Cabinet Vision, Mozaik and Microvellum pricing** could not be fetched (Polyboard's site refused automated access). All marked `needs-verification`; get quotes directly.
- FreeCAD's exact licence (believed LGPL-2.1-or-later) was not confirmed on the pages fetched.
- Shapr3D's monthly price — the page rendered "$19/month" alongside "$228/year, 34% savings", which is internally inconsistent. Re-check.
- Whether Fusion's USD export currently carries materials in a form Unreal or Omniverse consumes without rework.
