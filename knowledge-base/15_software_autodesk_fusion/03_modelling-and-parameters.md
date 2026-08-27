---
id: fusion.modelling
title: Solid modelling, the timeline and parameters in Fusion
domain: 15_software_autodesk_fusion
tags: [fusion, modelling, extrude, timeline, parameters, expressions, configurations, parametric-cabinet, direct-modelling]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release."
unit_system: metric
sources:
  - {title: "Fusion API Reference — Design object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — UserParameters", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/UserParameters.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — UserParameters.add", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/UserParameters_add.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Design.modifyParameters", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design_modifyParameters.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — ExtrudeFeatures", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExtrudeFeatures.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "ParameterIO_Python", url: "https://github.com/AutodeskFusion360/ParameterIO_Python", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
related: [fusion.sketching, fusion.assemblies, fusion.api, fusion.joinery_workflow]
---

# Solid modelling, the timeline and parameters in Fusion

**Summary.** Fusion's Design workspace builds solids by applying **features** to sketches and existing bodies, recording each step in a **timeline** at the bottom of the window. Because the timeline replays on every change, a model is only as robust as the order and the references of its features. Layered on top is a **parameter system**: named user parameters, model parameters created by each feature, and expressions that link them. A joinery model that is properly parameterised can be regenerated at a new width, thickness or shelf count either by editing three numbers in one dialog or by an external script writing those numbers — which is the point of this whole domain.

## Key facts

- Design has two modes: **Parametric** (timeline on) and **Direct** (timeline off). `Design.designType` in the API; **Design workspace → browser → right-click the document root → Do not capture Design History / Capture Design History** in the UI.
- Parameter dialog: **Design workspace → Solid tab → Modify → Change Parameters** (also `Modify → Change Parameters` on other tabs).
- Parameter kinds: **User Parameters** (you create, you name) and **Model Parameters** (created automatically by every feature and sketch dimension, named `d1`, `d2`, … until you rename them).
- API: `design.userParameters` (add / item / itemByName / asArray / **importUserParameters** / **exportUserParameters**), `design.allParameters`, `design.modifyParameters(parameters, values)`.
- `UserParameters.add(name, value, units, comment)` where `value` is a `ValueInput`; `units` is a string (`'mm'`, `''` for unitless, `'Text'` for a text parameter).
- **Internal API units are centimetres and radians.** `ValueInput.createByReal(1.8)` means 18 mm. `ValueInput.createByString('18 mm')` means 18 mm. Use the string form.
- `Design.modifyParameters` is **all-or-nothing**: "If it fails to set any parameters, none of them are updated."

## The feature set

Fusion's parametric feature set on the **Solid** tab. Named here with the ribbon panel they sit under.

**Create panel — additive/generative features**

| Feature | What it does | Joinery use |
|---|---|---|
| **Extrude** (`E`) | Sweeps a profile normal to its plane. Distance, To Object, Symmetric, Two Sides; taper angle | Every panel. Extrude a face rectangle by `BoardThickness` |
| **Revolve** | Rotates a profile about an axis | Turned legs, knobs |
| **Sweep** | Drives a profile along a path; optional guide rail; twist | Mouldings, handrails, curved skirtings |
| **Loft** | Blends between profiles/rails, with tangency options | Tapered or shaped carcass fronts |
| **Rib** | Thin wall from an open sketch, thickened to a body | Rare in wood; common in printed jigs |
| **Web** | Rib network from multiple open sketches | As above |
| **Hole** | A true hole feature — simple, counterbore, countersink; sizes from a standard, depth by value or "To" | **Shelf-pin and system holes, hinge cup bores, dowel holes**. Use this, not an extrude-cut |
| **Thread** | Modelled or cosmetic thread on a cylindrical face, from a thread library | Insert nuts, levelling feet |
| **Box / Cylinder / Sphere / Torus / Coil / Pipe** | Primitive creation | Quick blocking; rarely in production models |
| **Pattern → Rectangular / Circular / Path / Pattern on Path** | Repeats features, faces, bodies or components | **32 mm system hole lines**, shelf pin columns, drawer runner holes |
| **Mirror** | Mirrors features, faces, bodies or components about a plane | Left/right cabinet sides |
| **Thicken** | Turns a surface into a solid | Vacuum-formed or laminated shapes |
| **Boundary Fill** | Solid from intersecting surfaces/planes | Advanced |
| **Create Form** | Enters the T-Spline sculpt environment | Organic furniture shapes |

**Modify panel — subtractive/altering features**

| Feature | Notes |
|---|---|
| **Press Pull** (`Q`) | Context-sensitive: offsets faces, extrudes profiles, offsets edges. Convenient; can create hard-to-trace history |
| **Fillet** / **Rule Fillet** | Constant, variable, chord-length; rule fillet applies by rule to many edges | 
| **Chamfer** | Equal distance, two distances, distance and angle |
| **Shell** | Hollows a body to a wall thickness, optionally removing faces | Drawer boxes cut from a solid, quick carcass blocking |
| **Draft** | Adds draft angle to faces from a neutral plane | Moulds, not joinery |
| **Scale** | Uniform or non-uniform | **Breaks parametric intent — avoid** |
| **Combine** | Join, Cut, Intersect between bodies, with "Keep Tools" | **The joinery workhorse**: cut a dado by combining a tool body |
| **Offset Face**, **Replace Face**, **Split Face**, **Split Body**, **Silhouette Split** | Face-level edits |
| **Move/Copy** (`M`) | Moves bodies/faces/components; creates a timeline feature |
| **Align** | Aligns by face/edge/point |
| **Physical Material** / **Appearance** (`A`) | Assigns density and looks. **Physical Material drives mass in the parts list** |
| **Change Parameters** | The parameter dialog |
| **Compute All** | Forces a full recompute of the timeline |

## Direct vs parametric mode

**Parametric** (default, timeline visible): every operation is recorded and replayed. Editable, driveable, slower on huge models.

**Direct** (timeline off): operations act on the current geometry with no history. Fast, and the only sane way to work on imported STEP geometry from a hardware supplier where there is no history to preserve.

You can switch a design from parametric to direct (**right-click the document root in the browser → Do not capture Design History**) — this **discards the timeline irreversibly**. Going the other way (**Capture Design History**) turns history on from the current state; it does not reconstruct the past.

> ⚠️ Turning off design history destroys the timeline and every parameter link built on it. Save a copy first. For a joinery project this is almost never what you want; the exception is a one-off worktop template derived from a laser scan.

A better pattern for mixed work: keep the parametric design as the master, and **derive** or link imported direct-modelled geometry in as a separate component (**Insert → Insert Derive**).

## The timeline, and how to edit history safely

The timeline is the strip of feature icons across the bottom. Behaviour worth knowing:

- **Double-click a feature** to re-open its dialog and edit its inputs. Fusion rolls back to that point, applies the change and replays forward.
- **Drag the end marker** back to inspect an earlier state, or to insert a new feature in the middle of history. Drag it forward again afterwards — leaving it back is a classic cause of "my new features vanished".
- **Right-click a feature → Move** to reorder. Only legal where dependencies allow.
- **Right-click → Suppress** to skip a feature without deleting it. Useful for optional design variants (a version with and without a top drawer), though **Configurations** are a better mechanism.
- **Right-click → Roll History Marker Here**.
- **Errors** show as a yellow/red badge on the timeline icon. Fusion will list the failed feature and usually name the missing reference.

**Safe editing rules:**

1. **Edit the sketch or the parameter, not the feature, wherever possible.** Changing a sketch dimension is safe; changing an extrude's "To Object" reference is not.
2. **Do not delete features from the middle of a long timeline.** Suppress first, confirm nothing downstream breaks, then delete.
3. **Group related features** (select several → right-click → Group) so a cabinet's twenty operations read as one block.
4. **Rename features.** `Extrude12` tells nobody anything; `Left side panel` does.
5. **Keep the timeline short per component.** Long chains are slow and fragile. If a component needs 60 features, it probably wants splitting.
6. **After any structural edit, run Modify → Compute All** and check the timeline for badges before you trust the cut list.

## User parameters, model parameters and the Change Parameters dialog

Open **Modify → Change Parameters**. The dialog has two sections:

- **User Parameters** — created with the `+` button. Each has a **Name**, **Unit**, **Expression**, **Value** and **Comment**. Names must start with a letter, contain letters, digits and underscores, and are case-sensitive.
- **Model Parameters** — grouped by component and by feature. Every sketch dimension and every feature input appears here. You can rename them and edit their expressions in place.

Discipline that pays off:

- **Create the user parameters before you model anything.** For a cabinet: `BoardThickness`, `BackThickness`, `CarcassWidth`, `CarcassHeight`, `CarcassDepth`, `PlinthHeight`, `DoorGap`, `ShelfCount`, `SystemHolePitch`, `FirstHoleOffset`, `HoleFromFrontEdge`.
- **Add a comment to every parameter.** The comment is what an agent or a colleague reads to know what it means.
- **Rename the model parameters that matter.** After creating the side-panel extrude, rename its distance parameter from `d3` to `SidePanelThickness_d` if you will reference it elsewhere — or better, set its expression to `BoardThickness` so you never need to.
- **Never type a raw number that has a meaning.** `18` appears in a cabinet in at least six places and they are not all the same 18.

### Expressions

Expressions live in any parameter's Expression cell and in any sketch dimension. Supported: arithmetic `+ - * / ^`, parentheses, unit suffixes, trigonometric functions in degrees or radians, `sqrt()`, `abs()`, `min()`, `max()`, `floor()`, `ceil()`, `round()`, and `PI`.

Worked joinery expressions:

```
BoardThickness      = 18 mm
CarcassWidth        = 600 mm
CarcassHeight       = 720 mm
CarcassDepth        = 560 mm
BackThickness       = 6 mm
BackRebate          = BackThickness + 1 mm
InternalWidth       = CarcassWidth - 2 * BoardThickness
ShelfWidth          = InternalWidth - 1 mm            // 0.5 mm clearance each side
ShelfCount          = 2                                // unitless
ShelfPitch          = (CarcassHeight - 2*BoardThickness) / (ShelfCount + 1)
DoorGap             = 3 mm
DoorWidth           = (CarcassWidth - 3 * DoorGap) / 2 // pair of doors
HingeCupDia         = 35 mm
HingeCupDepth       = 12.8 mm
HingeCupFromEdge    = 22.5 mm                          // centre of cup from door edge
SystemHolePitch     = 32 mm
FirstHoleOffset     = 37 mm
HoleFromFrontEdge   = 37 mm
ShelfPinDia         = 5 mm
```

A unitless parameter such as `ShelfCount` must be created with `units = ''`. Use it directly as a pattern quantity.

> ⚠️ **Pattern quantities must be integers.** `ShelfCount` as a real number will silently truncate. Use `floor()` in the expression if it derives from a division: `HoleCount = floor((CarcassHeight - 2*FirstHoleOffset) / SystemHolePitch) + 1`.

### Importing and exporting parameters

`UserParameters` exposes **`exportUserParameters()`** and **`importUserParameters()`** — the latter "imports a list of user parameters from a csv file". Autodesk also publishes the **ParameterIO_Python** add-in, which "enable[s] CSV file selection and attribute editing". This is the officially supported bridge between a spreadsheet cutting schedule and a Fusion model, and it is the low-code alternative to the script in `09_api-and-automation.md`.

## Configurations (design variants)

Fusion's **Configurations** turn one design into a table of variants — the equivalent of SolidWorks configurations. In the browser, **right-click the document root → Create Configuration** (API: `Design.createConfiguredDesign()`, which "converts design into a configured design with single row and no columns"). You then add:

- **Rows** = variants (`600 base unit`, `900 base unit`, `1200 base unit`)
- **Columns** = configurable inputs: user parameters, feature suppression states, component substitutions, appearances, physical materials, part number and description.

Configured designs expose `Design.isConfiguration`, `Design.isConfiguredDesign`, `Design.configurationTopTable` and `Design.configurationRowId` in the API, and `Occurrences.addFromConfiguration` inserts a specific configuration row as a component in an assembly.

For a kitchen this is genuinely useful: one configured **base unit** design with rows for every width in the run, inserted repeatedly into the kitchen assembly, each carrying its own part number into the parts list. The alternative — twelve separate documents — makes a late change to the plinth detail a twelve-file edit.

Caveat: configurations interact awkwardly with downstream CAM and with drawings; test the whole chain on one small run before committing a kitchen to it. `needs-verification` on current configuration/CAM interoperability.

## Worked example: a fully parametric carcass

The target: a base unit driven by `CarcassWidth`, `CarcassHeight`, `CarcassDepth` and `BoardThickness`, with a rebated back and a system hole line.

**1. Parameters.** Create the block above in Change Parameters before touching a sketch.

**2. Skeleton.** On the XZ origin plane, sketch a construction rectangle `CarcassWidth` × `CarcassHeight` with its lower-left corner coincident with the origin. This is the carcass envelope; nothing else is dimensioned in absolute terms.

**3. Sides.** New component (`Assemble → New Component`, named `Side L`). Sketch on the YZ plane a rectangle `CarcassDepth` × `CarcassHeight`, extrude `BoardThickness`. Repeat mirrored, or model one and use **Create → Mirror** on the *component* about the YZ plane at `CarcassWidth/2` — but see `04_assemblies-and-joints.md` on mirroring components properly.

**4. Top rails / bottom.** New component. Sketch on XY, width `InternalWidth`, depth `CarcassDepth - BackRebate`, extrude `BoardThickness`. Position by joint, not by sketch offset.

**5. Back.** Sketch on the XZ plane at `CarcassDepth - BackRebate`, size `CarcassWidth - 2*(BoardThickness - BackRebate)` × `CarcassHeight - ...` depending on your rebate scheme; extrude `BackThickness`.

**6. Rebates and dados.** Model them as features on the panel that receives them, driven by `BoardThickness` — never by a typed 18. A dado for a fixed shelf: sketch a rectangle `BoardThickness` wide on the inner face's *sketch plane* (an offset construction plane, not the face), extrude-cut to `DadoDepth = BoardThickness / 3`.

**7. System holes.** On each side panel: a **Hole** feature, simple, Ø`ShelfPinDia`, depth `12 mm`, positioned `HoleFromFrontEdge` from the front and `FirstHoleOffset` from the bottom. Then **Create → Pattern → Rectangular Pattern** on that hole feature, direction = the panel's vertical edge, quantity = `HoleCount`, distance type **Spacing**, spacing = `SystemHolePitch`. Mirror the column to the rear line at `HoleFromFrontEdge` from the back.

**8. Test.** Change `CarcassWidth` to 300 and to 1200; change `BoardThickness` to 16 and to 25. Run **Compute All**. Fix what breaks. Only then build the rest of the kitchen from it.

## Driving it from the API

```python
import adsk.core, adsk.fusion, traceback

def set_params(design, values: dict) -> bool:
    """values: {'CarcassWidth': '900 mm', 'ShelfCount': '3'} — all or nothing."""
    params, inputs = [], []
    for name, expr in values.items():
        p = design.allParameters.itemByName(name)
        if p is None:
            raise ValueError('No parameter named ' + name)
        params.append(p)
        inputs.append(adsk.core.ValueInput.createByString(str(expr)))
    return design.modifyParameters(params, inputs)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        ok = set_params(design, {
            'CarcassWidth': '900 mm',
            'CarcassHeight': '720 mm',
            'ShelfCount': '3',
        })
        design.computeAll()
        ui.messageBox('Parameters updated: {}'.format(ok))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`Design.modifyParameters` is preferable to setting each parameter individually because it recomputes once, not `n` times, and because it will not leave the model in a half-updated state. `Design.computeAll()` "forces a recompute of the entire design ... the equivalent of the 'Compute All' command".

## Sources

- [Fusion API Reference — Design object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — UserParameters](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/UserParameters.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — UserParameters.add](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/UserParameters_add.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Design.modifyParameters](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design_modifyParameters.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — ExtrudeFeatures](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExtrudeFeatures.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — HoleFeatures](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/HoleFeatures.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — RectangularPatternFeatures.createInput](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/RectangularPatternFeatures_createInput.htm) — Autodesk, accessed 2026-08-25
- [ParameterIO_Python add-in](https://github.com/AutodeskFusion360/ParameterIO_Python) — Autodesk on GitHub, accessed 2026-08-25

## Open questions

- The complete list of functions supported in Fusion's expression parser was not verified against a live Autodesk help page; `floor`, `ceil` and `round` are stated from working knowledge. `needs-verification`.
- Current interaction between Configurations and the Manufacture workspace (do toolpaths follow a configuration row?). `needs-verification`.
- Exact ribbon panel names on the Solid tab were not verified against a scraped help page.
