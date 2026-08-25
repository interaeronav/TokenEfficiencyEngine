---
id: fusion.joinery_workflow
title: Sheet goods, joinery details and the CNC pipeline in Fusion
domain: 15_software_autodesk_fusion
tags: [fusion, joinery, sheet-goods, dogbone, dado, rabbet, finger-joint, 32mm-system, hinge-cup, nesting, cutlist, dxf, cnc-router]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release; 3-axis CNC router, sheet-goods joinery."
unit_system: metric
sources:
  - {title: "Dogbone add-in for Fusion 360", url: "https://github.com/DVE2000/Dogbone", publisher: "DVE2000 (GitHub)", accessed: 2026-08-25}
  - {title: "Autodesk Fusion Manufacturing Extension", url: "https://www.autodesk.com/products/fusion-360/manufacturing-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Nesting & Fabrication Extension", url: "https://www.autodesk.com/products/fusion-360/nesting-fabrication-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — ExportManager", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Sketch.saveAsDXF (retired)", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch_saveAsDXF.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Component object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "DXFBulkImport", url: "https://github.com/AutodeskFusion360/DXFBulkImport", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
related: [fusion.modelling, fusion.assemblies, fusion.cam, joinery.sheet_goods, joinery.hardware, joinery.cabinetmaking]
---

# Sheet goods, joinery details and the CNC pipeline in Fusion

**Summary.** This is the file that connects the CAD to the shop. It covers modelling from real board thicknesses rather than nominal ones, the corner-relief geometry (dogbone and T-bone) that a round cutter forces on every internal corner, how to model dado, rabbet, finger and dowel joints so they survive a thickness change, how to place 32 mm system holes and hinge bores at the manufacturer's datum, what the Manufacturing Extension's nesting actually gives you, and how to get a cut list and per-panel DXFs out of the model. Cross-reference the material and hardware facts in the `06_joinery_and_woodwork` domain; this file is about how to represent them in Fusion.

## Key facts

| Item | Value | Note |
|---|---|---|
| Standard board sheet **[ZA]/[NA]** | 2750 × 1830 mm and 3660 × 1830 mm | See `joinery.sheet_goods` |
| Nominal 16 mm MFC, real thickness | typically 15.6–16.2 mm | **Measure the delivered board** |
| Nominal 18 mm MFC, real thickness | typically 17.6–18.3 mm | Same |
| System hole pitch | **32 mm** | 32 mm cabinetmaking system |
| System hole diameter | **Ø5 mm** | Shelf pin / fitting |
| System hole line from front edge | **37 mm** to hole centre | Front line; rear line usually 37 mm from back |
| Concealed hinge cup | **Ø35 mm × ~12.8 mm deep** | Blum/Hettich/Grass/Salice |
| Typical cutter for 18 mm board | Ø6 mm or Ø8 mm compression spiral | Determines dogbone radius |
| Dogbone radius | = cutter radius (+ a few hundredths clearance) | See below |
| Kerf / cutter offset in nesting | = cutter diameter | Plus 8–12 mm part spacing |

> ⚠️ **Never model to the nominal thickness.** An 18 mm dado cut for a board that measures 17.7 mm gives a sloppy joint; a 17.7 mm dado for a board that measures 18.2 mm will not assemble. Create `BoardThickness` as a user parameter, measure the delivered pallet with a vernier, and set it before generating toolpaths.

## Modelling from real board thicknesses

Set up every joinery document with these parameters before modelling (see `03_modelling-and-parameters.md`):

```
BoardThickness   = 17.9 mm    // measured, per delivery
BackThickness    =  5.8 mm    // measured
CutterDia        =  6 mm      // the router bit that will cut the joints
CutterRad        = CutterDia / 2
JointClearance   =  0.1 mm    // per side, for a press fit in MFC
DadoDepth        = BoardThickness / 3
```

Then:

- Every panel extrudes by `BoardThickness`, never by 18.
- Every dado, groove and rebate is `BoardThickness + 2*JointClearance` wide, or `BoardThickness` exactly if you want an interference fit and will sand.
- Every back rebate is `BackThickness` deep and `BackThickness` wide (or deeper, if you rebate for a loose back).

When the next delivery measures differently, change one parameter, run **Modify → Compute All**, regenerate toolpaths, re-post. That is the entire value proposition of parametric joinery.

**Two boards in one job.** If the carcasses are 18 mm and the backs 6 mm, that is two parameters. If the carcasses are 18 mm white and 18 mm oak from different suppliers with different real thicknesses, that is *two more*. Name them for the material: `MFC_White_T`, `MFC_Oak_T`, `MDF_Back_T`.

## Dogbone and T-bone fillets — the geometry a round cutter forces

A router cuts with a round tool. A 90° internal corner in a pocket comes out with the cutter's radius left in it, so a square tenon or a square-cornered panel will not seat. The fix is to relieve the corner.

**Dogbone**: an extra circular cut of the cutter's radius, centred on the corner and swung diagonally into it. The relief is on the diagonal, so it removes material from both faces of the corner equally.

**T-bone (or I-bone)**: the same relief circle, but pushed straight out along one wall of the pocket rather than on the diagonal. It puts all the relief in one face. Preferred where the diagonal relief would be visible on a show face, and where the mating part's corner is chamfered.

**"Minimal" / "corner" dogbone**: a reduced relief that removes only enough material for the mating corner, sacrificing a little strength for a much less visible notch.

Sizing:

```
DogboneRad = CutterRad + 0.05 mm      // a few hundredths so the tool clears
```

Do **not** make the dogbone radius smaller than the cutter — the cutter cannot enter it. Do not make it much larger than needed — you are removing glue surface.

**How to do it in Fusion.** There is no native dogbone command. Three routes:

1. **The Dogbone add-in** (`DVE2000/Dogbone` on GitHub, MIT licence). Select the internal edges, choose **normal**, **minimal** or **mortise** dogbones, set the tool diameter, and it cuts the reliefs as a timeline feature. "Mortise dogbones" are "positioned along sides to remain hidden under connecting tenon pieces" — the right choice for a visible finger joint. Install by copying the add-in folder into the Fusion add-ins directory; on macOS that is `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/Dogbone` (the repo notes recent macOS versions enforce case-sensitive folder names — use lowercase `resource`). On Windows the equivalent path is under `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`. Folder names must be alphanumeric.
2. **Model them parametrically yourself**: at each internal corner, a sketch circle of `DogboneRad` centred `CutterRad*sqrt(2) - CutterRad` along the diagonal from the corner, extrude-cut through. Tedious but fully parametric and it survives a cutter change.
3. **Leave them to CAM**: some post-processors and some CAM strategies can add corner relief at toolpath time. Fusion's 2D Contour has a **Preserve Order / Corner** section with smoothing but does **not** add dogbones. Do it in CAD.

> ⚠️ Decide dogbone vs T-bone per joint, not per project. A dogbone in a drawer-side finger joint shows as a notch on the outside of the drawer; a T-bone pushed into the *tail* rather than the *pin* hides it.

## Modelling the joints

### Dado / housing / groove

The joint that carries most sheet-goods carcasses. Model it on the **receiving** panel:

1. Sketch on an offset construction plane (not the panel face — see `02_sketching-and-constraints.md`), a rectangle `BoardThickness + 2*JointClearance` wide by `DadoDepth` deep, positioned by a dimension from the panel's datum edge.
2. **Extrude → Cut**, extent **All** or a dimension.
3. Add dogbones at the two internal corners of the *through* dado (a stopped dado has four).

For a **stopped dado**, the far end also needs relief, and the mating panel needs a notch cut back by `CutterRad` at the front corner. Model that notch on the mating panel driven by the same `CutterRad` parameter — this is precisely the kind of cross-part relationship a shared user parameter handles well and a projected edge handles badly.

### Rabbet / rebate

A rebate is a dado at an edge. Same modelling, one wall. The back rebate is the standard case:

```
BackRebateDepth = BackThickness      // flush back
BackRebateWidth = BackThickness + 0.2 mm
```

Cut it on all four carcass members, and remember the back panel's overall size is then `CarcassWidth - 2*BoardThickness + 2*BackRebateDepth`.

### Finger / box joints

Model as a patterned cut. On panel A, sketch one finger of width `FingerWidth`, cut it, then **Create → Pattern → Rectangular Pattern** with quantity `FingerCount` and spacing `2*FingerWidth`. On panel B, the same pattern offset by `FingerWidth`. Drive `FingerCount = floor(PanelWidth / (2*FingerWidth))` and add dogbones to every internal corner — a finger joint has a lot of them, which is why the Dogbone add-in earns its keep here.

Fit: on a CNC router, cut the sockets `0.1–0.15 mm` oversize per side in MFC and MDF, `0.05 mm` in ply, and test on offcuts before committing a sheet.

### Dowel joints

Model dowels as a **Hole** feature (not an extrude-cut) so the drilling shows correctly in a parts list and can be recognised by CAM's hole recognition. Ø8 × 30 mm dowels at 32 mm multiples is the common cabinet standard. Parameters: `DowelDia`, `DowelDepthEnd`, `DowelDepthFace`, `DowelPitch`.

**Model the dowel itself as a component** if you want it in the parts list as a bought item; omit it if your BOM handles consumables separately.

### Mitre, biscuit, Domino, Lamello

For solid-timber and visible work. Mitres are a simple angled cut; biscuit and Domino slots are best modelled as a sketch-and-cut on a joint origin so they can be repositioned as a set. Lamello Clamex connectors have published geometry — model the pocket to the published dimensions and place it from a joint origin.

## Hardware placement

The rule: **place hardware from the datum the fitter uses, using a joint origin, with the manufacturer's numbers as parameters.**

### 32 mm system holes

```
SystemHolePitch    = 32 mm
SystemHoleDia      =  5 mm
SystemHoleDepth    = 12 mm       // in an 18 mm panel
FrontLineFromEdge  = 37 mm
RearLineFromEdge   = 37 mm       // from the back edge
FirstHoleFromBase  = 37 mm       // or whatever your line-borer datum is
HoleCount          = floor((PanelHeight - 2*FirstHoleFromBase) / SystemHolePitch) + 1
```

Model **one** hole with the Hole feature, then a **Rectangular Pattern** with `HoleCount` at `SystemHolePitch` spacing, then a second pattern (or a mirror) for the rear line. Do not sketch 40 circles.

### Concealed hinge cup

Blum/Hettich/Grass/Salice full-overlay clip-top geometry:

```
CupDia        = 35 mm
CupDepth      = 12.8 mm      // check the specific hinge — 11.3–13.5 mm range exists
CupFromEdge   = 22.5 mm      // centre of cup from the door edge; 21–24 mm depending on overlay/reveal
CupFromEnd    = 100 mm       // top and bottom hinge positions; scales with door height
```

Model with a **Hole** feature, simple, `CupDia` diameter, `CupDepth` depth, flat-bottomed. Add the two Ø8 × 11 mm dowel holes or the Ø2.5 mm screw pilots at ±`CupScrewPitch/2` (commonly 45 mm or 48 mm apart, 9.5 mm from cup centre) — check the specific hinge's technical sheet and record the source in the parameter comment.

> ⚠️ In a 16 mm door with a 12.8 mm cup you have 3.2 mm of material behind the cup. In a 15.6 mm real-thickness board that is 2.8 mm. Do the arithmetic parametrically (`CupResidual = DoorThickness - CupDepth`) and put a warning in the model if it goes below 3 mm.

### Drawer runners

Model the runner as a component derived from the supplier's STEP file, jointed by a joint origin at the manufacturer's fixing datum (usually the front face of the carcass side, at a stated height). The carcass-side fixing holes then come from the runner's own geometry or from a patterned Hole feature at the published pitch. Blum Tandem/Movento and Hettich Quadro/Actro all publish drilling patterns as dimensioned PDFs and most publish STEP models.

Parameterise the **drawer box width** from the runner's required side clearance: `DrawerBoxWidth = InternalWidth - 2*RunnerSideClearance` (typically 12.5 mm or 13 mm per side for full-extension runners — check the model).

## The Nesting & Fabrication capability (now in the Manufacturing Extension)

Autodesk consolidated the former Nesting & Fabrication Extension into the **Manufacturing Extension** (verified 2026-08-25). What it provides, in Autodesk's words:

- **Associative nesting** — "Convert 3D assemblies into precise 2D nested solutions ready for CAM programming, and automatically update nests if your original 3D design changes."
- **Multi-sheet nesting** — "Smart nesting groups parts together based on thickness and other material-specific parameters giving instant insights for costing, quoting, and ordering."
- Sheet-metal design/documentation with 2D drawings and DXFs, material yield optimisation and setup generation.

The workflow it enables: model the kitchen as components → define a nest with your sheet size (2750 × 1830) and cutter offset → Fusion arranges the panels by thickness across the minimum number of sheets → the nest result becomes a manufacturing model you can put a CAM setup on directly. Change a cabinet width, and the nest updates.

**If you do not have the extension**, the alternatives, in order of practicality for a small shop:

1. **Export per-panel DXFs and nest in a free/cheap external nester** (SVGnest / Deepnesting, or the nesting built into your machine's control software). Most Chinese and Taiwanese router controllers ship with a nesting module.
2. **Nest manually in a Fusion sketch.** Create a "sheet" component with a 2750 × 1830 rectangle, insert each panel's flat outline as a sketch, drag into place. Tedious, exact, free, and completely under your control. Practical up to ~40 parts.
3. **Script it.** A rectangle-packing heuristic (shelf/guillotine/MaxRects) over the panel bounding boxes from `Component.orientedMinimumBoundingBox`, writing back either a DXF or a set of sketch positions, is maybe 300 lines of Python. Panel goods are almost all rectangles, so true-shape nesting buys little; a first-fit-decreasing shelf packer gets within a few per cent of optimal on rectangular parts. See `09_api-and-automation.md`.

**Grain direction is not automatic.** If the material has a directional finish (woodgrain MFC, veneered ply), a nester that rotates parts freely will produce a kitchen with sideways grain. Tag every component's `description` with `GRAIN:LENGTH` or `GRAIN:FREE` and honour it in your nesting rules.

## Flat patterns and cut lists

**Flat pattern** in Fusion is a **sheet metal** concept: `Component.createFlatPattern()` unfolds a folded sheet-metal body, and `ExportManager.createDXFFlatPatternExportOptions(filename, flatPattern)` exports it. It is **not** what you use for a flat panel of MFC — a panel is already flat.

For sheet goods, the "cut list" is: for every component, the length × width × thickness of its oriented minimum bounding box, plus material, edging and quantity.

`Component.orientedMinimumBoundingBox` "returns an oriented bounding box that is best oriented to tightly [fit]" the component — exactly the right primitive. Its `length`, `width` and `height` are in **centimetres**. Multiply by 10 for millimetres.

Fields a joinery cut list needs, and where they come from:

| Field | Source |
|---|---|
| Part name | `Component.name` |
| Part code | `Component.partNumber` |
| Qty | count of occurrences of that component |
| Length / Width / Thickness | `orientedMinimumBoundingBox` sorted descending |
| Material | `Component.material.name` |
| Edging | parsed from `Component.description` (`EB:L1` = one long edge) |
| Grain | parsed from `Component.description` |
| Area | L × W, for costing |

The complete runnable script is in `09_api-and-automation.md`.

**Community add-ins.** Several cut-list add-ins exist on the Autodesk marketplace (now at `marketplace.autodesk.com`, which has replaced `apps.autodesk.com`) and on GitHub. Their quality varies and most break on Fusion UI changes. For a shop that will use this daily, writing and owning ~150 lines of Python is more reliable than depending on a free add-in with one maintainer. See `11_resources-and-learning.md`.

## Exporting for a CNC router

Three legitimate outputs, in increasing order of shop maturity:

**1. Per-panel DXF.** For a machine whose own CAM you prefer, or for an external nester.

> ⚠️ **`Sketch.saveAsDXF` was retired in July 2025.** Any tutorial or script using it is out of date. The replacement is `ExportManager.createDXFSketchExportOptions(filename, sketch)` followed by `exportManager.execute(options)`. `ExportManager` also offers `createDXFFlatPatternExportOptions`, `createSTEPExportOptions`, `createIGESExportOptions`, `createSATExportOptions`, `createSMTExportOptions`, `createSTLExportOptions`, `createOBJExportOptions`, `createC3MFExportOptions`, `createUSDExportOptions` and `createFusionArchiveExportOptions`.

The DXF must contain, per panel: the outer profile, every through cut, every pocket outline **with its depth carried somewhere** (layer name is the usual convention: `CUT_THROUGH`, `POCKET_6.0`, `DRILL_5.0_D12`), and the dogbones already applied. Establish the layer convention with the machine operator before you export the first file.

Autodesk's **DXFBulkImport** add-in (MIT, on GitHub) does the reverse — "allows import of DXF files in bulk" — which is useful for bringing a supplier's hardware profiles or an architect's setting-out into Fusion.

**2. G-code direct from Fusion CAM.** The full pipeline in `06_cam-and-manufacturing.md`. Best when you control the machine and can maintain a post-processor.

**3. STEP to the machine vendor's CAM.** When the router comes with software the operator already trusts (Vectric, Alphacam, WoodWOP, Biesse bSolid). Export the whole nest or per-panel STEP; the vendor CAM does the toolpathing. This loses associativity but often wins on shop-floor reliability.

## Shop pipeline, end to end

1. Measure the delivered board; set `BoardThickness` and `BackThickness`.
2. Set `CutterDia` to the bit that will actually be in the spindle.
3. Model / regenerate the run. **Compute All**. Check the timeline for errors.
4. **Inspect → Interference** across the whole assembly.
5. Apply dogbones (add-in or parametric) to every internal corner that a cutter must reach.
6. Generate the cut list. Sanity-check total sheet area against the number of sheets you intend to buy, plus 10–20 % waste (`joinery.specifying`).
7. Nest (extension, external, or scripted). Honour grain.
8. Toolpath and simulate (`06_cam-and-manufacturing.md`), or export DXF/STEP.
9. Post-process, transfer, cut one test part, measure it, adjust `JointClearance`, re-post.
10. Issue shop drawings for assembly (`07_drawings-and-documentation.md`).

Steps 3, 6, 7 and 8 are all scriptable. That is the argument for the API file.

## Sources

- [Dogbone add-in for Fusion 360](https://github.com/DVE2000/Dogbone) — DVE2000 on GitHub, accessed 2026-08-25
- [Autodesk Fusion Manufacturing Extension](https://www.autodesk.com/products/fusion-360/manufacturing-extension) — Autodesk, accessed 2026-08-25
- [Nesting & Fabrication Extension](https://www.autodesk.com/products/fusion-360/nesting-fabrication-extension) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — ExportManager](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Sketch.saveAsDXF (retired July 2025)](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch_saveAsDXF.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Component object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm) — Autodesk, accessed 2026-08-25
- [DXFBulkImport add-in](https://github.com/AutodeskFusion360/DXFBulkImport) — Autodesk on GitHub, accessed 2026-08-25

## Open questions

- Hinge cup depth, cup-from-edge and cup screw pitch vary by manufacturer and hinge series. The values above are typical ranges, not a specification. **Take them from the specific hinge's technical drawing** — see `joinery.hardware`. `needs-verification` per project.
- Exact real thicknesses of PG Bison and Sonae Arauco MFC as delivered in Namibia — measure, do not assume.
- The Manufacturing Extension's nesting UI workflow (menu paths, sheet library setup) was not verified against a live help page; the capability description is quoted from Autodesk's product page.
- Whether the marketplace cut-list add-ins are currently maintained against the May 2026 release.

