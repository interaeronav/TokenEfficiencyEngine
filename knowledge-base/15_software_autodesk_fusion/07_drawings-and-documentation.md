---
id: fusion.drawings
title: The Drawing workspace — shop drawings, parts lists and DXF/PDF output
domain: 15_software_autodesk_fusion
tags: [fusion, drawing, shop-drawings, sheets, templates, sections, dimensions, parts-list, balloons, exploded-view, dxf, pdf]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release. Drawing API is PDF-export only."
unit_system: metric
sources:
  - {title: "Fusion API Reference — Drawing object (adsk::drawing)", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Drawing.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — DrawingDocument", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/DrawingDocument.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — DrawingExportManager", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/DrawingExportManager.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Component object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.assemblies, fusion.joinery_workflow, joinery.specifying]
---

# The Drawing workspace — shop drawings, parts lists and DXF/PDF output

**Summary.** Fusion's Drawing workspace produces associative 2D documentation from a 3D design: sheets, base and projected views, sections and details, dimensions, hole and thread notes, parts lists with balloons, and exploded views taken from an Animation. It is competent for mechanical parts and adequate for joinery, with two significant limitations you must plan around — the **parts list enumerates components, not bodies**, and the **drawing API is essentially write-only PDF export**, so drawing production cannot be automated the way modelling can. This file covers how to get a drawing a joiner can actually build from.

## Key facts

- Enter with **File → New Drawing → From Design** (or **From Animation** for an exploded view). A drawing is a **separate document** (`.f2d`-class) that references the design.
- API namespace is **`adsk::drawing`** (Python `adsk.drawing`), reached via `DrawingDocument.drawing`. Introduced December 2020.
- **The `Drawing` object exposes only**: `attributes`, `exportManager`, `namedViews`, `selectionSets`, `unitsManager`, `workspaces`, plus `deleteEntities` and `findAttributes`. There is **no `sheets` collection, no view creation, no dimension creation** in the API.
- `DrawingExportManager` exposes **only `createPDFExportOptions()`** and `execute()`. DWG/DXF/CSV export is UI-only.
- Standards supported: **ISO**, **ASME**. Set per drawing at creation.
- Component fields that flow into the parts list: `name`, `partNumber`, `description`, plus material and mass.

> ⚠️ **Drawing creation cannot be scripted.** If your workflow depends on generating 40 panel drawings automatically, Fusion is the wrong tool for that step — generate DXFs and a cut list from the model instead (see `09_api-and-automation.md`), or produce the drawing sheets by hand from a template.

## Creating a drawing and setting it up

**File → New Drawing → From Design.** The creation dialog asks for:

- **Contents**: Full Assembly, or Select (pick specific components — this is how you make a single-panel drawing).
- **Drawing**: Create New, or Insert into Existing.
- **Template**: From Scratch, or a saved `.dwt`-equivalent Fusion drawing template.
- **Standard**: ISO or ASME. **[NA]/[ZA]** Use **ISO** — first-angle projection, metric, decimal comma or point per house style.
- **Units**: mm.
- **Sheet Size**: A0–A4 or custom. For joinery, **A3 landscape** is the practical default: it prints on the shop's printer and is readable on a phone.

### Sheets and templates

Once open, the **Sheets** tab at the bottom manages multiple sheets. **Right-click a sheet tab → New Sheet / Rename / Delete / Reorder**.

**Build a template once.** A joinery template should carry:

- A title block with: project, client, drawing title, drawing number, revision, scale, date, drawn-by, checked-by, material note, units note, and **"Do not scale — dimensions in mm"**.
- A revision table.
- Standard notes: tolerance convention, edging convention, grain convention, board thickness reference.
- Your practice's logo and the sheet border.

Save it with **File → Save As Template**. Every subsequent drawing starts from it. This is the single highest-return hour you will spend in the Drawing workspace.

**[NA]** For a Namibian residential job, put the **site address and the room name** in the title block. Joinery drawings get separated from their covering letter within a day of reaching site.

## Views

**Create panel:**

| Command | Use |
|---|---|
| **Base View** | The first view. Choose orientation (Front/Top/Right/Iso/Current), style (Visible edges / Visible and hidden edges / Shaded / Shaded with visible edges), scale, tangent edges, interference edges, thread edges |
| **Projected View** | Drag from an existing view to create orthographic and isometric projections that stay aligned |
| **Section View** | Full, half, offset or aligned section through a parent view. **The essential joinery view** — a vertical section through a base unit shows the carcass, the shelf, the plinth and the worktop junction in one picture |
| **Detail View** | A circular or rectangular blow-up at a larger scale. Use for hardware junctions and edge details at 1:2 or 1:1 |
| **Break View** | Compresses a long uniform part. Useful for a 3 m plinth or a long shelf |
| **Break Out** | Cuts away part of a view to reveal interior. Good for showing a dowel inside a joint |
| **Auxiliary View** | Projection normal to a sloped face. Splayed corner units |

**Scales for joinery drawings:**

| Drawing | Scale |
|---|---|
| Elevation of a kitchen run | 1:20 or 1:25 |
| Individual cabinet | 1:10 |
| Vertical section through carcass | 1:10, sometimes 1:5 |
| Hardware / edge detail | 1:2 or 1:1 |
| Panel cutting drawing | 1:10 with all dimensions |

Set the view scale in the view's dialog; override the sheet scale per view where needed and **always show the scale next to the view title**.

**Style advice for joinery:** use **Visible edges only** for assembly views (hidden lines make a cabinet unreadable) and **Visible and hidden** only on section and detail views where the concealed joint is the point. Turn **tangent edges** off — they add noise on filleted edges.

## Dimensioning

**Dimensions panel: Dimension** (`D`), **Ordinate Dimension**, **Baseline Dimension**, **Chain Dimension**.

Rules that make a joinery drawing buildable:

1. **Dimension from the datum the maker uses.** For a panel, that is one long edge and one end. Use **Baseline** or **Ordinate** from a single datum, not chained dimensions that accumulate.
2. **Ordinate dimensioning is ideal for hole patterns.** A column of 32 mm system holes as ordinate dimensions from the panel bottom is unambiguous and compact; twenty chained 32s are neither.
3. **Dimension the thing that is made, not the thing that results.** A dado is dimensioned by its distance from the datum edge and its width and depth — not by the resulting internal opening.
4. **One dimension, one place.** A dimension repeated on two views will eventually disagree.
5. **Overall dimensions on the assembly view; component dimensions on the component drawing.**
6. **Never leave a dimension that Fusion could not resolve** (it shows as a broken reference). Fix or delete.

Dimension style — text height, arrowheads, precision, unit display — is set in **Document Settings** (browser, top of the tree) or per-dimension in the palette. Set precision to **0 decimal places for mm** on joinery drawings; 705.3 mm is a fiction on a panel saw. Reserve one decimal for machined parts.

**Tolerance**: Fusion supports symmetric, deviation, limits, basic and reference tolerance display per dimension. For sheet goods, put a general note in the title block (`Unless noted: ±0.5 mm on panel sizes, ±0.2 mm on machined features`) rather than tolerancing every dimension.

## Hole and thread notes

**Dimensions panel → Hole/Thread Note** (in some layouts under the same flyout as Dimension). Select a hole created with the **Hole feature** and Fusion writes a note carrying diameter, depth, counterbore/countersink and quantity, e.g. `4× Ø5 ▼12`.

**This only works for true Hole features.** A hole made with an extrude-cut circle produces no note — which is the practical reason `05_sheet-goods-and-joinery-workflow.md` insists on the Hole feature for shelf pins, dowels and hinge cups.

Thread notes similarly read from the **Thread** feature and emit `M8×1.25 ▼20`.

## Parts lists and balloons

**Tables panel → Parts List.** Fusion generates a table from the components in the referenced design.

Default columns include Item, Part Number, Description, Quantity, Material and Mass; the column set is configurable (right-click the table → **Edit Parts List** / column chooser). Sort order and row grouping are editable.

**Balloon** (Tables panel) attaches an item number to a component in a view. **Auto Balloon** balloons everything in a view at once, then you drag them into a readable arrangement.

**How to make the parts list useful for joinery:**

- Put the **cut-list code** in `Component.partNumber` (`BU600-SIDE-L`).
- Put **material, thickness, edging and grain** in `Component.description` — e.g. `18 mm MFC Snowdrift / EB 2L1S / grain: length`. The description column then *is* the specification.
- Set **physical material** on every component so the Mass column is real; total mass tells you how many people are needed to lift the unit.
- Add a **custom column** for area if your costing works per m² **[NA]** — parts-list custom columns are limited; if you need computed area, generate the cut list from the API instead (`09_api-and-automation.md`) and place it as a table.

> ⚠️ **The parts list counts components.** Bodies are invisible to it. A carcass modelled as six bodies in one component produces a parts list with one line. This is the practical consequence of the structure rules in `04_assemblies-and-joints.md`.

## Exploded views from animations

Fusion has no explode command in the Drawing workspace. The route is:

1. In the design, switch to the **Animation** workspace.
2. **Transform Components** / **Auto Explode: One Level / All Levels** to move parts apart along a timeline.
3. Add **callouts** if wanted; save the animation.
4. **File → New Drawing → From Animation**, and pick the storyboard point you want as a view.

The resulting view is an ordinary drawing view — you can balloon it and attach it to the parts list. For a flat-pack cabinet issued to a fitter, an exploded isometric with balloons and a parts list is worth more than three orthographic views.

## Exporting

**Output panel** (or **File → Export**):

- **PDF** — the deliverable. Options for sheet range, line weights, and whether to include the border. Vector output; text is selectable.
- **DWG** — for the architect or the client's AutoCAD. Round-trips reasonably; expect line weights and text styles to need tidying.
- **DXF** — for machine consumption or another CAD.
- **CSV** — exports the parts list as data. This is the officially supported route to a costing spreadsheet.

**PDF is the only format exposed to the API** (`DrawingExportManager.createPDFExportOptions()` then `execute()`), so a batch "re-export every drawing to PDF after a revision" script is possible; a batch DXF export from drawings is not.

Programmatically:

```python
import adsk.core, adsk.drawing, traceback, os

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.activeDocument
        drawDoc = adsk.drawing.DrawingDocument.cast(doc)
        if not drawDoc:
            ui.messageBox('Active document is not a drawing.')
            return
        em = drawDoc.drawing.exportManager
        opts = em.createPDFExportOptions(
            os.path.expanduser('~/Desktop/{}.pdf'.format(doc.name)))
        em.execute(opts)
        ui.messageBox('Exported.')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`needs-verification` on the exact `createPDFExportOptions` argument list, which the reference page did not spell out.

## What a joiner can actually build from — the drawing set

A defensible joinery drawing package for one residential kitchen:

**Sheet 1 — General arrangement.** Plan at 1:50 with cabinet references, elevations of each run at 1:20 or 1:25, with unit widths and heights, appliance positions, and services. Title block, revision, and a schedule of finishes.

**Sheet 2..n — Unit drawings, one unit type per sheet, 1:10.** Front elevation, plan, vertical section, exploded isometric, parts list with balloons. All carcass dimensions, door/drawer front sizes with gaps shown, hardware called out by manufacturer part number.

**Sheet — Details, 1:2 or 1:1.** Worktop-to-carcass junction, plinth detail, scribe detail, end panel return, drawer front fixing, hinge and runner positions with drilling dimensions.

**Sheet — Setting out.** Wall dimensions as surveyed, with a note stating the tolerance assumed and who is responsible for site check. **[NA]** On a Namibian residential build with block-and-plaster walls, out-of-square of 15–25 mm across a 4 m run is common; the drawing must say what scribe allowance is designed in.

**Appendix — Cut list.** Generated from the model (see `09_api-and-automation.md`), issued as PDF and CSV.

Practical issues that separate a usable set from a decorative one:

- **Every dimension a fitter needs must be on the drawing.** If they have to add two numbers, they will occasionally add them wrong.
- **State the datum**, e.g. "all heights from finished floor level (FFL)".
- **Show the handing.** Left-hand and right-hand units get built wrong more often than anything else. Mark `LH`/`RH` on the elevation and in the part number.
- **Number the units and match the numbers to the labels on the panels.** The cut list, the parts list, the label on the panel and the drawing must all say `BU600-3`.
- **Revision-control the PDFs.** Re-issue the whole sheet with a revision cloud and a revision note; never issue a "corrected" sheet with the same number.

## Sources

- [Fusion API Reference — Drawing object (adsk::drawing)](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Drawing.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — DrawingDocument](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/DrawingDocument.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — DrawingExportManager](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/DrawingExportManager.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Component object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm) — Autodesk, accessed 2026-08-25

## Open questions

- Exact ribbon panel and command labels in the Drawing workspace were not verified against a scraped Autodesk help page (help.autodesk.com renders client-side). `needs-verification` on labels; the capability descriptions are from working knowledge.
- The argument list of `DrawingExportManager.createPDFExportOptions()`.
- Whether custom computed columns (e.g. panel area) can be added to a Fusion parts list in the May 2026 release.
- Whether drawing templates can be shared across an Autodesk hub team, or are per-user.

