---
id: fusion.cam
title: The Manufacture workspace — CAM, toolpaths, posts and G-code
domain: 15_software_autodesk_fusion
tags: [fusion, cam, manufacture, toolpath, adaptive, contour, pocket, post-processor, gcode, feeds-and-speeds, cnc-router, tabs, simulation]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release. CAM API: NCPrograms (CAM.postProcess and CAM.postProcessAll are RETIRED)."
unit_system: metric
sources:
  - {title: "Autodesk Post Processor Library", url: "https://cam.autodesk.com/hsmposts", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — CAM object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/CAM.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — NCPrograms", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/NCPrograms.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — NCProgram", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/NCProgram.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — CAM Setups", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Setups.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Fusion Manufacturing Extension", url: "https://www.autodesk.com/products/fusion-360/manufacturing-extension", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.joinery_workflow, fusion.licensing, fusion.api, joinery.machinery]
---

# The Manufacture workspace — CAM, toolpaths, posts and G-code

**Summary.** Fusion's Manufacture workspace is a full CAM system: you define a **setup** (which model, which work coordinate system, what stock), attach **operations** (toolpaths) that reference a **tool** from a **tool library**, **simulate** them, then **post-process** them through a machine-specific `.cps` post into G-code. For a joinery shop with a 3-axis router this is a complete solution in the base subscription; 4/5-axis, probing, automatic hole recognition and associative nesting require the Manufacturing Extension. The two things that most often go wrong are the WCS (cutting in the wrong place) and the post-processor (correct toolpath, wrong dialect), and both are addressed below.

## Key facts

- Workspace switch: top-left selector → **Manufacture**.
- Object hierarchy: **Machine** (optional) → **Setup** → **Folder / Pattern** → **Operation**; separately **NC Program** collects operations for posting.
- Post-processor files are **`.cps`** (JavaScript). Two folders: `genericPostFolder` (Autodesk's installed posts) and `personalPostFolder` (yours). Both are exposed in the API as `CAM.genericPostFolder` and `CAM.personalPostFolder`.
- Post library: **https://cam.autodesk.com/hsmposts** — filterable by Milling, Turning, Mill/Turn, Waterjet, Laser, Plasma, Additive, plus Setup Sheet and Intermediate/Interoperability categories, and by vendor.
- **API change:** `CAM.postProcess` and `CAM.postProcessAll` are **RETIRED**. Use `cam.ncPrograms` → `NCPrograms.createInput()` → `NCPrograms.add(input)` → `NCProgram.postProcess()`. `CAM.export3MFForDefaultAdditiveSetup` is also retired.
- Still current: `cam.generateAllToolpaths(skipValid)`, `cam.generateToolpath(...)`, `cam.checkAllToolpaths(...)`, `cam.clearAllToolpaths()`, `cam.getMachiningTime(...)`, `cam.generateAllSetupSheets()`, `cam.documentToolLibrary`, `cam.documentStockMaterialLibrary`, `cam.setups`, `cam.allOperations`, `cam.allMachines`, `cam.manufacturingModels`.

> ⚠️ **A post-processed program is not verified until you have watched it cut air.** Simulation in Fusion verifies the *toolpath*, not the *post output*. Dry-run every new post and every new machine at Z+50 before you put material on the table.

## Setups and the WCS

**Manufacture → Milling tab → Setup panel → Setup** (or **New Setup**).

The Setup dialog has three tabs:

**Setup tab**
- **Operation Type**: Milling / Turning or Mill/Turn / Cutting / Additive.
- **Model**: which bodies or components this setup machines. For a nested sheet, select the nest; for a per-part setup, select the component.
- **Fixture** (optional): bodies representing clamps and the spoilboard, so simulation can flag collisions.
- **Work Coordinate System (WCS)** — the critical block:
  - **Orientation**: Model orientation, Select Z axis/plane & X axis, Select X&Y axes, Select coordinate system.
  - **Origin**: Model origin, Selected point, Stock box point, Model box point.

**For a CNC router cutting sheet goods, the near-universal convention is:**
- Z **zero at the top of the spoilboard** if you are cutting through and your spoilboard is flat, or **top of the material** if you are pocketing to a depth referenced from the face. Pick one, write it on the setup sheet, and never mix them in one job.
- X0 Y0 at the **front-left corner of the sheet**, matching the machine's home/fence.
- Z+ up, X+ right, Y+ away from the operator.

Set the origin using **Stock box point** and click the correct corner vertex — this stays correct when the sheet size changes, whereas a selected model vertex does not.

**Stock tab**
- **Mode**: Relative size box, Fixed size box, Fixed size cylinder, From solid.
- For sheet goods: **Fixed size box**, dimensions = your actual sheet (2750 × 1830 × `BoardThickness`), with **Model Position** set so the parts sit where they will actually sit.
- For a solid-timber part: **Relative size box** with stock offsets for the planing allowance.
- `cam.documentStockMaterialLibrary` gives API access to stock materials, which the Manufacturing Extension uses for nesting grouping.

**Post Process tab**
- **Program Name/Number**, **Program Comment**, **Machine WCS** (`WCS offset` → 0 = G54, 1 = G55, …).

## Tool library management

**Manufacture → Manage panel → Tool Library** (also reachable from any operation dialog's tool selector).

Three library scopes:
- **Local** — this machine.
- **Cloud** — your Autodesk hub, synced across machines.
- **Document** — `cam.documentToolLibrary`, "contains all tools used by any operation inside the document". This is the one that travels with the file.

Each tool carries: type (flat end mill, ball, bull nose, chamfer, drill, thread mill, slot mill, face mill, dovetail…), diameter, flute count, shaft/holder geometry, and — importantly — a set of **presets**. A preset stores spindle speed, cutting feed, plunge feed, ramp feed, lead-in/out feed, and the stepdown/stepover for a named operation type.

**Build presets, not one-off numbers.** A "Ø6 2-flute compression — 18 mm MFC through-cut" preset is reusable, auditable and correctable in one place. When the shop learns that the feed is 10 % too fast, you fix the preset, regenerate and re-post.

Tool libraries import/export as `.tools` (JSON) files. Keep yours in version control alongside your posts.

## 2D toolpaths — what a joinery shop actually uses

All on the **Milling tab → 2D panel** unless noted.

| Strategy | What it does | Joinery use |
|---|---|---|
| **Face** | Flattens the top of stock | Skimming a spoilboard flat — do this before every accurate job |
| **2D Contour** | Follows a selected contour at one or more depths | **The workhorse.** Panel outlines, through-cuts, rebates by side offset. Supports tabs, multiple depths, finishing passes, tool compensation |
| **2D Pocket** | Clears a closed region, offset-inward | Dados, hinge cup bores (with a Ø35 mm cutter it is a bore; with a smaller one, a pocket), recesses for hardware |
| **2D Adaptive Clearing** | Constant tool engagement clearing with trochoidal moves | Deep pockets and hardwood; much kinder to tools than a full-slot pocket |
| **Slot** | Cuts an open slot along a centreline | Grooves, T-slots |
| **Trace** | Follows a curve exactly with no offset | **V-carving text and engraving**, marking cut lines |
| **Bore** | Helical bore of a circular hole with a smaller tool | Hinge cups with a Ø6 mm cutter when you have no Ø35 mm boring bit |
| **Circular** | Circular pocket/profile | Round holes |
| **Thread** | Thread milling | Insert threads in jigs |
| **Engrave** | V-bit engraving in a contour | Signage, branded panels |
| **Drill** (Drilling panel) | Drilling cycles — G81/G83 peck, G73, tapping, boring | **32 mm system holes**, dowel holes. Select the hole faces and Fusion picks up diameter and depth |

**3D toolpaths** (Milling tab → 3D panel): Adaptive Clearing, Pocket Clearing, Parallel, Contour, Ramp, Horizontal, Pencil, Scallop, Spiral, Radial, Morphed Spiral, Project, Flow. For joinery these matter only for carved or shaped work — a moulded door panel, a dished handle, a shaped worktop edge. The usual pairing is **3D Adaptive Clearing** to rough, then **Parallel** or **Scallop** to finish, with a ball nose.

Multi-axis strategies (Swarf, Multi-Axis Contour, Rotary, Flow) are **Manufacturing Extension** territory.

## Feeds and speeds

Two equations do all the work:

```
Feed (mm/min)  = RPM × number of flutes × chipload (mm/tooth)
Vc (m/min)     = π × tool diameter (mm) × RPM / 1000
```

Wood is chipload-limited (too small a chip and you burn the material and the tool); metal is surface-speed-limited.

### Wood, plywood, MDF — starting points for a 3-axis router

| Material | Tool | RPM | Chipload (mm/tooth) | Feed (mm/min) | Stepdown |
|---|---|---|---|---|---|
| 18 mm MFC / melamine chipboard | Ø6 2-flute compression spiral | 18,000 | 0.15–0.22 | 5,400–7,900 | full depth in one pass, or 2 × 9 mm |
| 18 mm MDF | Ø6 2-flute upcut | 18,000 | 0.20–0.30 | 7,200–10,800 | full depth |
| 18 mm birch ply | Ø6 2-flute compression | 16,000–18,000 | 0.15–0.25 | 4,800–9,000 | full depth |
| Hardwood (kiaat, oak) | Ø6 2-flute upcut | 15,000–18,000 | 0.15–0.25 | 4,500–9,000 | 6–9 mm |
| Softwood | Ø6 2-flute upcut | 18,000 | 0.25–0.40 | 9,000–14,400 | full depth |
| Acrylic / Perspex | Ø6 1-flute O-flute | 12,000–16,000 | 0.10–0.20 | 1,200–3,200 | 3–6 mm |

> ⚠️ These are **starting points for a rigid industrial router with vacuum hold-down**, not a specification. A light hobby gantry will need half these feeds. **Always cut a test part in the actual material and measure it.** Chipload too low = burning, glazing and premature tool wear; too high = tear-out and broken tools.

Practical notes for sheet goods:
- **Compression (up-down) spirals** are the correct tool for double-sided melamine and veneered ply — they pull the top face down and the bottom face up, so neither edge chips. They need to cut at least the length of the down-cut portion in one pass to work.
- **Down-cut** for a clean top edge in a pocket; it packs chips into the cut, so not for deep slotting.
- **Up-cut** clears chips and lifts the part — only with good hold-down.
- **Climb milling** gives a better finish in wood; conventional in metal. Fusion sets this per operation (Passes → **Both Ways / Climb / Conventional**).
- **Ramp** into every pocket rather than plunging. Set **Linking → Ramp → Ramp type: Helix** with 2–3° ramp angle.

### Aluminium on a router

Possible on a rigid machine, painful on a light one.

| Material | Tool | RPM | Chipload (mm/tooth) | Feed (mm/min) | DOC / WOC |
|---|---|---|---|---|---|
| 6082/6061 aluminium | Ø6 3-flute ZrN-coated carbide | 12,000–18,000 (Vc ≈ 225–340 m/min) | 0.03–0.05 | 1,100–2,700 | Adaptive: DOC 6–12 mm, WOC 0.6–1.2 mm |
| 6082/6061, slotting | Ø6 2-flute | 12,000 | 0.02–0.04 | 480–960 | DOC 1–2 mm full slot |

Rules: **use 2D/3D Adaptive Clearing, not pocket** — constant engagement is what makes aluminium possible on a wood machine. Use **flood or mist lubrication or at minimum an air blast with WD-40/alcohol**; aluminium welds to a dry cutter in seconds. Never use a 4-flute in a slot; chips have nowhere to go.

## Tabs and holding

**Hold-down decides the feeds, not the other way round.**

- **Vacuum table**: the professional answer. Small parts still need care — below roughly 150 × 150 mm a single-zone vacuum will not hold against a full-depth cut.
- **Screws into the spoilboard**: reliable, leaves holes, needs the screw positions modelled so a toolpath does not hit one.
- **Tabs**: in **2D Contour → Passes → Tabs**, choose **Distance** (Fusion spaces them) or **Manual** (you click positions). For 18 mm MFC: tab width 8–10 mm, tab height 3–4 mm, 3–5 tabs on a cabinet side. Tabs must be cleaned up with a flush-trim router or a chisel afterwards, so put them on edges that will not show or that get edgebanded.
- **Onion skin**: leave 0.3–0.5 mm of material across the whole bottom instead of tabs, then sand or knife the parts out. Cleaner than tabs on small parts; only viable with a genuinely flat spoilboard and accurate Z.
- **Double-sided tape / low-tack** for one-offs.

Model the fixture (clamps, screws, vacuum pods) as bodies and add them to the setup's **Fixture** selection so simulation catches collisions.

## Simulation and verification

**Manufacture → Actions panel → Simulate.**

The simulation panel gives:
- **Toolpath display** — coloured by feed type (rapid, cutting, lead-in/out). **Look for rapid moves through the stock** — the classic symptom of a wrong retract height.
- **Stock** — material removal simulation, with **Stock Comparison** (colour map against the design model) to find gouges and uncut material.
- **Collision detection** — flags tool-holder and shaft collisions when the holder geometry is defined. Define your collets and holders in the tool library or this does nothing.
- **Machine** — if a machine definition is assigned, simulates the physical machine including axis limits.

`cam.checkAllToolpaths()` and `cam.checkValidity()` are the API equivalents of the sanity checks; `cam.getMachiningTime(...)` returns the estimated cycle time, which is what you should be quoting from.

**A verification checklist before posting:**
1. Every operation generated without warnings (no red/yellow badges in the browser).
2. Simulation shows no rapids below the clearance height.
3. Stock comparison shows no red (gouge) anywhere.
4. Tool list matches the tools actually in the shop, in the right pockets.
5. WCS origin is where you will actually touch off.
6. Total machining time is plausible — a 4-minute estimate for a full sheet means an operation did not generate.

## Post-processors

A post-processor is a JavaScript file (`.cps`) that translates Fusion's internal toolpath into your control's dialect. Getting the right one is not optional: the same toolpath posted for a Mach3 router and a Fanuc mill produces incompatible files.

**Getting a post:**

1. **Autodesk's library at https://cam.autodesk.com/hsmposts** — filter by machine type and vendor. Covers Mach3/Mach4, LinuxCNC, GRBL, Fanuc, Haas, Siemens, Heidenhain, Centroid, Masso, and most Chinese router controls (Syntec, NcStudio, RichAuto) either directly or via a close generic. Autodesk's own caveat is worth quoting: "it is your sole responsibility to make sure you use components that are compatible with your CNC."
2. **Your machine vendor.** Most router OEMs ship or will supply a Fusion post.
3. **The Autodesk CAM Post Processor Forum**, where the Autodesk post team answers modification requests — historically the most effective route to a working post for an odd machine.

**Installing a post:** download the `.cps`, then in Fusion's **Post Process** dialog set the **Source** to **Personal posts** and use **Setup → Post Library** to import it, or copy the file directly into the personal post folder. The folder path is exposed programmatically as `CAM.personalPostFolder`; if you need it, print it from a script rather than guessing.

**Editing a post.** `.cps` files are readable JavaScript with a documented API (Autodesk publishes a Post Processor Training Guide and API documentation, both linked from the post library page). Common, safe edits for a joinery shop:

- Change the **file extension** and header comment format.
- Suppress or add **M-codes** for a dust shoe, vacuum pump or spindle warm-up.
- Force **G0 as G1 at a fixed rate** if the machine's rapids are unsafe near the table.
- Change **arc output** from G2/G3 to linearised moves if your control's arc support is poor.
- Adjust the **tool change** block for a manual-tool-change router (`M0` pause and a message).
- Change **units** or coolant behaviour.

Riskier edits (work offsets, cycle emission, multi-axis kinematics) belong to whoever supports the machine.

> ⚠️ **Version-control your posts and tool libraries.** A shop with three routers and no record of which post cut which job will eventually scrap a sheet. Keep `posts/` and `tools/` in a git repository with the machine name and date in the commit.

## The practical shop workflow, model to G-code

1. Finish and check the model (`05_sheet-goods-and-joinery-workflow.md` steps 1–5).
2. Switch to **Manufacture**. Create a **Setup** per sheet, with fixed-size stock and a stock-box-corner WCS origin.
3. Add operations in cutting order: **drilling first** (system holes, dowels), then **pockets/dados**, then **inner through-cuts**, then **outer profiles last** — so the part stays rigid as long as possible.
4. Assign tools from a preset-backed library.
5. Add **tabs** on the outer profile only.
6. **Generate** all toolpaths (`cam.generateAllToolpaths(True)` skips already-valid ones).
7. **Simulate** with fixtures and stock comparison.
8. Create an **NC Program**, assign the post and the operations, set the output folder and filename, **Post Process**.
9. **Setup Sheet** (`cam.generateAllSetupSheets()`) — an HTML sheet listing tools, WCS, stock and times. Print it and tape it to the machine.
10. Transfer, dry-run above the material, touch off, cut one part, measure, adjust `JointClearance`, regenerate, re-post.

## Automating the post from Python

The retired API is the thing most tutorials get wrong. Current pattern:

```python
import adsk.core, adsk.fusion, adsk.cam, traceback, os

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.activeDocument
        # Ensure the Manufacture product exists.
        cam = adsk.cam.CAM.cast(doc.products.itemByProductType('CAMProductType'))
        if not cam:
            ui.messageBox('No Manufacture data in this document.')
            return

        # 1. Regenerate everything that is out of date.
        future = cam.generateAllToolpaths(True)   # True = skip valid toolpaths
        while not future.isGenerationCompleted:
            adsk.doEvents()

        # 2. Build an NC program for the whole document.
        ncInput = cam.ncPrograms.createInput()
        ncInput.displayName = 'Sheet 1'
        ncInput.operations = [cam.setups.item(i) for i in range(cam.setups.count)]
        ncProgram = cam.ncPrograms.add(ncInput)

        # 3. Point it at a post. genericPostFolder / personalPostFolder are exposed.
        postFolder = cam.personalPostFolder
        ncProgram.postConfiguration = os.path.join(postFolder, 'my_router.cps')

        # 4. Post.
        ncProgram.postProcess()
        ui.messageBox('Posted. Personal post folder:\n{}'.format(postFolder))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`NCProgram` exposes `postProcess()`, `updatePostParameters()`, `parameters` (a `CAMParameters` collection), `postConfiguration`, `postParameters`, `machine`, `operations`, `filteredOperations`, `hasError`/`error`, `hasWarning`/`warning`. The **output folder and filename are set through the `parameters` collection**, not through a dedicated property — enumerate `ncProgram.parameters` in the Text Commands window (see `09_api-and-automation.md`) to find the current parameter names for your Fusion version rather than hard-coding them. `needs-verification` on the exact parameter names, which have changed between releases.

## Sources

- [Autodesk Post Processor Library](https://cam.autodesk.com/hsmposts) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — CAM object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/CAM.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — NCPrograms](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/NCPrograms.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — NCProgram](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/NCProgram.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — CAM Setups](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Setups.htm) — Autodesk, accessed 2026-08-25
- [Autodesk Fusion Manufacturing Extension](https://www.autodesk.com/products/fusion-360/manufacturing-extension) — Autodesk, accessed 2026-08-25

## Open questions

- **All feeds and speeds tables above are starting points**, synthesised from standard chipload practice, not quoted from a source. They are `needs-verification` against your own test cuts and your tool manufacturer's data sheet.
- Exact `NCProgram.parameters` names for output folder and filename in the May 2026 release.
- Whether the base (non-extension) subscription currently includes 3D Adaptive Clearing — this has moved between tiers historically. `needs-verification`.
- Exact ribbon panel names in the Manufacture workspace were not verified against a scraped help page.

