---
id: fusion.api
title: The Fusion API — Python scripting, add-ins and automation
domain: 15_software_autodesk_fusion
tags: [fusion, api, python, scripts, add-ins, adsk-core, adsk-fusion, adsk-cam, automation, mcp, aps, fusion-data-api, cutlist, dxf-export]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Autodesk Fusion API, reference corpus dated May 2026 major release. Notes retirements up to July 2025."
unit_system: metric
sources:
  - {title: "Fusion API Reference (browsable)", url: "https://autodeskfusion360.github.io/FusionAPIReference/", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "FusionAPIReference repository", url: "https://github.com/AutodeskFusion360/FusionAPIReference", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
  - {title: "FusionMCPSample — MCP server add-in", url: "https://github.com/AutodeskFusion360/FusionMCPSample", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Design.modifyParameters", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design_modifyParameters.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — ExportManager.createDXFSketchExportOptions", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager_createDXFSketchExportOptions.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Sketch.project2", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch_project2.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — TextCommandPalette", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/TextCommandPalette.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API and Scripts forum", url: "https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "DesignAutomationSamples", url: "https://github.com/AutodeskFusion360/DesignAutomationSamples", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
related: [fusion.modelling, fusion.assemblies, fusion.joinery_workflow, fusion.cam, fusion.resources]
---

# The Fusion API — Python scripting, add-ins and automation

**Summary.** Fusion exposes a complete client-side API in **Python** and **C++**, organised into `adsk.core`, `adsk.fusion`, `adsk.cam`, `adsk.drawing` and `adsk.electron`. Anything the UI can do to a model, the API can do — create sketches and features, walk assemblies, read and set parameters, generate and post toolpaths, export files — with the notable exception of **creating drawing views and dimensions**, which is not exposed. Code runs **inside** Fusion, as a **script** (runs once) or an **add-in** (loads at startup and adds UI). For an agent-driven workflow this is the crucial file: it is how a language model turns a specification into a cut, nested, priced kitchen.

## Key facts

- Reference: **https://autodeskfusion360.github.io/FusionAPIReference/** — class pages follow the pattern `.../Fusion_API_Documentation/files/<ClassName>.htm` and member pages `.../files/<ClassName>_<member>.htm`. Autodesk also ships the whole corpus (HTML docs, C++ headers, **Python stubs**) in the `FusionAPIReference` repo with an `llms.txt` "for LLM ingestion", updated as of the **May 2026** release.
- **Internal units are centimetres and radians.** `ValueInput.createByReal(1.8)` = 18 mm. Always prefer `ValueInput.createByString('18 mm')`.
- Script/add-in folders:
  - Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\Scripts\` and `...\API\AddIns\`
  - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts/` and `.../API/AddIns/`
  - Folder names must be alphanumeric; on macOS, resource sub-folders are case-sensitive (`resource`, lowercase).
- UI entry: **Utilities tab → ADD-INS panel → Scripts and Add-Ins** (shortcut `Shift+S`).
- **Retired API to avoid**: `Sketch.saveAsDXF` (July 2025 → `ExportManager.createDXFSketchExportOptions`), `Sketch.project` (May 2025 → `Sketch.project2`), `CAM.postProcess` and `CAM.postProcessAll` (→ `NCPrograms`/`NCProgram.postProcess`), `CAM.export3MFForDefaultAdditiveSetup`.

## Python vs C++

| | Python | C++ |
|---|---|---|
| Ships with Fusion | Yes — an embedded CPython | No, you build a plugin DLL/dylib |
| Speed | Adequate; API round-trips dominate | Faster for heavy geometry loops |
| Debugging | VS Code attach, `print()`, Text Commands | Native debugger |
| Ecosystem | Bundled stdlib; **third-party packages are awkward** | Full C++ toolchain |
| Use it for | Everything, unless profiling says otherwise | Custom features, thousands of geometric operations |

**Use Python.** The one real friction is third-party packages: Fusion's embedded interpreter has its own `site-packages` and `pip` is not officially supported. Workarounds are to vendor pure-Python dependencies into the add-in folder and add them to `sys.path`, or to keep heavy dependencies out of Fusion and communicate over a file or a local socket. For a nesting or costing engine, running it **outside** Fusion and exchanging CSV/JSON is usually cleaner than fighting the interpreter.

## The object model

```
adsk.core.Application            .get()  — the root
├─ userInterface (UserInterface) — messageBox, palettes, commandDefinitions, workspaces,
│                                  toolbarPanels, activeSelections, createFileDialog
├─ documents (Documents)         — add(), item()
├─ activeDocument (Document)     — products, save, close, dataFile
├─ activeProduct (Product)       — cast to Design / CAM / Drawing
├─ measureManager (MeasureManager) — getOrientedBoundingBox, measureMinimumDistance, measureAngle
└─ preferences, log(), executeTextCommand()

adsk.fusion.Design               (cast from activeProduct)
├─ rootComponent (Component)
├─ designType                    — ParametricDesignType | DirectDesignType
├─ userParameters (UserParameters) / allParameters / derivedParameters
├─ modifyParameters(params, values) / computeAll()
├─ timeline (Timeline)
├─ exportManager (ExportManager)
├─ allComponents, activeComponent, contactSets, analyses
├─ createInterferenceInput() / analyzeInterference()
└─ configurationTopTable, isConfiguredDesign, createConfiguredDesign()

adsk.fusion.Component
├─ sketches (Sketches)           — add(planarEntity) [projects face edges],
│                                  addWithoutEdges(planarEntity)
├─ features (Features)           — extrudeFeatures, revolveFeatures, sweepFeatures,
│                                  loftFeatures, holeFeatures, filletFeatures,
│                                  chamferFeatures, shellFeatures, ribFeatures, webFeatures,
│                                  rectangularPatternFeatures, circularPatternFeatures,
│                                  mirrorFeatures, combineFeatures, moveFeatures,
│                                  threadFeatures, splitBodyFeatures, ...
├─ bRepBodies (BRepBodies)       — item(i) -> BRepBody (faces, edges, vertices, volume)
├─ occurrences / allOccurrences  — assembly instances
├─ joints / asBuiltJoints / jointOrigins / rigidGroups / motionLinks
├─ constructionPlanes / constructionAxes / constructionPoints
├─ xYConstructionPlane, xZConstructionPlane, yZConstructionPlane, originConstructionPoint
├─ name, partNumber, description, material, opacity, id, entityToken
├─ physicalProperties / getPhysicalProperties(accuracy)
├─ boundingBox, preciseBoundingBox, orientedMinimumBoundingBox
└─ createFlatPattern(), saveCopyAs(), transformOccurrences()

adsk.cam.CAM                     (cast from a CAMProductType product)
├─ setups (Setups) → Setup → operations
├─ ncPrograms (NCPrograms) → NCProgram.postProcess()
├─ generateAllToolpaths(skipValid), checkAllToolpaths(), clearAllToolpaths()
├─ documentToolLibrary, documentStockMaterialLibrary, allMachines
├─ genericPostFolder, personalPostFolder
└─ getMachiningTime(), generateAllSetupSheets(), exportManager

adsk.drawing.Drawing             — exportManager only (PDF). No view/dimension API.
adsk.electron                    — ECAD (schematic/PCB) namespace.
```

Two idioms you will use constantly:

```python
design = adsk.fusion.Design.cast(app.activeProduct)   # safe cast, returns None on mismatch
cam    = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType('CAMProductType'))
```

`ObjectCollection.create()` builds the collections that feature inputs expect.

## Scripts vs add-ins

**A script** is a folder containing `MyScript.py` and `MyScript.manifest`. It exposes `def run(context):` and optionally `def stop(context):`. It runs once when you press Run, then unloads. This is what you write for a one-shot job: generate a cabinet, export a cut list, batch a DXF set.

**An add-in** is the same shape but with `"type": "addin"` in its manifest and `"supportedOS"` etc. It loads when Fusion starts (if "Run on Startup" is ticked), stays resident, creates **command definitions** and **UI controls**, and subscribes to **events**. This is what you write for a tool the shop uses daily.

Both live under `API/Scripts/` or `API/AddIns/`. **Utilities → ADD-INS → Scripts and Add-Ins** lists them, lets you create a new one from a template, and has a green `+` to point at a folder elsewhere on disk (useful for keeping your code in a git repo).

Minimal manifest (`MyAddIn.manifest`):

```json
{
    "autodeskProduct": "Fusion",
    "type": "addin",
    "author": "Your practice",
    "description": { "": "Joinery tools" },
    "supportedOS": "windows|mac",
    "runOnStartup": true,
    "version": "1.0.0"
}
```

### The Command / CommandDefinition / UI framework

A Fusion command is built in three layers:

1. **CommandDefinition** — the button. `ui.commandDefinitions.addButtonDefinition(id, name, tooltip, resourceFolder)`, where `id` is a unique string of `[A-Za-z0-9_]`, and `resourceFolder` points at a folder of PNG/SVG icons (`16x16.png`, `32x32.png`, `64x64.png`).
2. **A control** placed in a toolbar panel, so the user can find it.
3. **Event handlers** — Fusion's API is event-driven and, critically, **handler objects must be kept alive**. A handler that goes out of scope is garbage-collected and the command silently does nothing. The universal idiom is a module-level `handlers = []` list that you append every handler to.

Handler chain for a command:

- `commandDefinition.commandCreated` → `CommandCreatedEventHandler` — build the dialog inputs here (`args.command.commandInputs`)
- `command.inputChanged` → `InputChangedEventHandler` — react to the user changing a field
- `command.validateInputs` → `ValidateInputsEventHandler` — enable/disable OK
- `command.executePreview` → `CommandEventHandler` — live preview
- `command.execute` → `CommandEventHandler` — do the work
- `command.destroy` → `CommandEventHandler` — clean up

Other useful events: `app.documentOpened`, `app.documentSaving`, `design.timeline` changes via `CustomEvent`, and **custom events** (`app.registerCustomEvent` / `fireCustomEvent`) — the mechanism the MCP sample uses to marshal calls from a background thread onto Fusion's main thread.

Here is a complete, minimal add-in skeleton:

```python
# JoineryTools.py  —  place in API/AddIns/JoineryTools/ with JoineryTools.manifest
import adsk.core, adsk.fusion, traceback

handlers = []          # MUST be module-level, or handlers are garbage-collected
CMD_ID = 'JoineryCutListCmd'
PANEL_ID = 'SolidScriptsAddinsPanel'      # Utilities > ADD-INS panel

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        inputs = cmd.commandInputs
        inputs.addStringValueInput('outdir', 'Output folder', '')
        inputs.addBoolValueInput('bydesc', 'Group by description', True, '', True)

        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        app = adsk.core.Application.get()
        inputs = args.command.commandInputs
        outdir = inputs.itemById('outdir').value
        # ... call your worker function here ...
        app.userInterface.messageBox('Cut list written to ' + outdir)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        cmdDef = ui.commandDefinitions.itemById(CMD_ID)
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition(
                CMD_ID, 'Cut list', 'Generate a joinery cut list from this design', '')

        onCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCreated)
        handlers.append(onCreated)

        ws = ui.workspaces.itemById('FusionSolidEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        if panel and not panel.controls.itemById(CMD_ID):
            panel.controls.addCommand(cmdDef)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ws = ui.workspaces.itemById('FusionSolidEnvironment')
        panel = ws.toolbarPanels.itemById(PANEL_ID)
        if panel:
            ctrl = panel.controls.itemById(CMD_ID)
            if ctrl:
                ctrl.deleteMe()
        cmdDef = ui.commandDefinitions.itemById(CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

> ⚠️ **`stop()` must remove everything `run()` created.** Otherwise reloading the add-in during development leaves duplicate buttons and stale command definitions, and Fusion eventually refuses to register the ID.

**Workspace and panel IDs are not formally documented.** `'FusionSolidEnvironment'` and `'SolidScriptsAddinsPanel'` are the long-standing IDs for the Design workspace and the Utilities → Add-Ins panel, but rather than trusting them, enumerate at runtime — see the Text Commands section below.

## Debugging and the Text Commands window

**Three tools, in increasing order of power:**

1. **`ui.messageBox(str)`** — blocking, crude, always works.
2. **The Text Commands palette.** `ui.palettes.itemById('TextCommands')`, then `palette.isVisible = True` and `palette.writeText('...')`. It is Fusion's console: `print()` from a script also lands there. It additionally accepts internal text commands typed by hand — the most useful being those that dump UI IDs.
3. **VS Code attach.** In **Scripts and Add-Ins**, select your script and click **Debug** (or the `⋮` menu → **Debug**); Fusion launches VS Code with a `launch.json` attached to its embedded Python, and breakpoints, watches and stepping all work. This is the correct way to develop anything non-trivial.

A logging helper worth pasting into every project:

```python
import adsk.core

def log(msg):
    app = adsk.core.Application.get()
    pal = app.userInterface.palettes.itemById('TextCommands')
    if pal:
        pal.isVisible = True
        pal.writeText(str(msg))
```

And the ID-discovery snippet that saves an hour every time the UI changes:

```python
def dump_panels():
    app = adsk.core.Application.get()
    for ws in app.userInterface.workspaces:
        if not ws.isValid:
            continue
        try:
            log('WORKSPACE {}  ({})'.format(ws.id, ws.name))
            for p in ws.toolbarPanels:
                log('    PANEL {}  ({})'.format(p.id, p.name))
        except:
            pass
```

Other essentials:

- `adsk.doEvents()` — yield to Fusion's message loop inside a long operation, so the UI does not freeze and so asynchronous futures (e.g. `generateAllToolpaths`) can progress.
- `adsk.terminate()` — end a script that started an event loop.
- `adsk.autoTerminate(False)` in `run()` when a *script* needs to stay alive for event handlers; call `adsk.terminate()` when done.
- Wrap **everything** in `try/except` and report `traceback.format_exc()`. An unhandled exception in a handler is swallowed silently.
- `design.timeline.timelineGroups` and `TimelineObject.isSuppressed` let a script reason about history.

## Example 1 — parametric carcass generator

Creates parameters, builds four panels as separate components, and drills a 32 mm system hole line. Run as a script in an empty design.

```python
# Carcass.py
import adsk.core, adsk.fusion, traceback

MM = 0.1   # multiply millimetres by this to get Fusion's internal centimetres

PARAMS = [
    ('BoardThickness',  '17.9 mm', 'mm', 'Measured board thickness'),
    ('CarcassWidth',    '600 mm',  'mm', 'Overall carcass width'),
    ('CarcassHeight',   '720 mm',  'mm', 'Overall carcass height'),
    ('CarcassDepth',    '560 mm',  'mm', 'Overall carcass depth'),
    ('SystemHolePitch', '32 mm',   'mm', '32 mm system pitch'),
    ('SystemHoleDia',   '5 mm',    'mm', 'Shelf pin diameter'),
    ('SystemHoleDepth', '12 mm',   'mm', 'Shelf pin hole depth'),
    ('HoleFromFront',   '37 mm',   'mm', 'Front hole line from front edge'),
    ('FirstHoleFromBase','37 mm',  'mm', 'First hole above carcass base'),
]

def ensure_params(design):
    up = design.userParameters
    for name, expr, units, comment in PARAMS:
        p = design.allParameters.itemByName(name)
        if p is None:
            up.add(name, adsk.core.ValueInput.createByString(expr), units, comment)
        else:
            p.expression = expr

def value(design, name):
    """Parameter value in internal units (cm)."""
    return design.allParameters.itemByName(name).value

def panel(parent, name, w_cm, h_cm, t_cm, plane, x_cm=0.0, y_cm=0.0, z_cm=0.0):
    """Create a child component containing one rectangular panel."""
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(x_cm, y_cm, z_cm)
    occ = parent.occurrences.addNewComponent(m)
    comp = occ.component
    comp.name = name

    sk = comp.sketches.addWithoutEdges(plane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(w_cm, h_cm, 0))
    prof = sk.profiles.item(0)
    ext = comp.features.extrudeFeatures.addSimple(
        prof,
        adsk.core.ValueInput.createByReal(t_cm),
        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    return occ, ext

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox('Open a Design document first.')
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType

        ensure_params(design)
        W = value(design, 'CarcassWidth')
        H = value(design, 'CarcassHeight')
        D = value(design, 'CarcassDepth')
        T = value(design, 'BoardThickness')

        root = design.rootComponent
        unitOcc = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        unit = unitOcc.component
        unit.name = 'Base unit {:.0f}'.format(W * 10)

        # Sides on the YZ plane (depth x height), extruded in +X by T.
        panel(unit, 'Side L', D, H, T, unit.yZConstructionPlane, x_cm=0)
        panel(unit, 'Side R', D, H, T, unit.yZConstructionPlane, x_cm=W - T)
        # Bottom and top rail on the XY plane (width x depth).
        panel(unit, 'Bottom',  W - 2 * T, D, T, unit.xYConstructionPlane,
              x_cm=T, z_cm=0)
        panel(unit, 'Top rail', W - 2 * T, 10.0, T, unit.xYConstructionPlane,
              x_cm=T, z_cm=H - T)

        # --- 32 mm system holes on the left side panel ---
        sideL = unit.occurrences.itemByName('Side L:1')
        if sideL:
            comp = sideL.component
            body = comp.bRepBodies.item(0)
            # Largest planar face = the inner/outer face of the panel.
            face = max((f for f in body.faces
                        if f.geometry.objectType == adsk.core.Plane.classType()),
                       key=lambda f: f.area)
            sk = comp.sketches.addWithoutEdges(face)
            pt = sk.modelToSketchSpace(
                adsk.core.Point3D.create(0, value(design, 'HoleFromFront'),
                                         value(design, 'FirstHoleFromBase')))
            sk.sketchPoints.add(pt)

            holes = comp.features.holeFeatures
            hin = holes.createSimpleInput(
                adsk.core.ValueInput.createByString('SystemHoleDia'))
            hin.setPositionBySketchPoint(sk.sketchPoints.item(sk.sketchPoints.count - 1))
            hin.setDistanceExtent(
                adsk.core.ValueInput.createByString('SystemHoleDepth'))
            hole = holes.add(hin)

            # Pattern it up the panel.
            entities = adsk.core.ObjectCollection.create()
            entities.add(hole)
            edge = max(body.edges, key=lambda e: e.length)
            count = int((H - 2 * value(design, 'FirstHoleFromBase'))
                        / value(design, 'SystemHolePitch')) + 1
            pats = comp.features.rectangularPatternFeatures
            pin = pats.createInput(
                entities, edge,
                adsk.core.ValueInput.createByReal(count),
                adsk.core.ValueInput.createByString('SystemHolePitch'),
                adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            pats.add(pin)

        design.computeAll()
        ui.messageBox('Carcass built.')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`ExtrudeFeatures` supports `addSimple(profile, distance, operation)` for the trivial case and `createInput(profile)` → configure → `add(input)` for anything with symmetry, two sides, taper or a "to object" extent. `HoleFeatures` offers `createSimpleInput`, `createCounterboreInput` and `createCountersinkInput`. `RectangularPatternFeatures.createInput(inputEntities, directionOneEntity, quantityOne, distanceOne, patternDistanceType)` is the verified signature.

> ⚠️ Picking geometry by "largest face" or "longest edge" is convenient in a generator script but **fragile in a maintained model**, because face and edge indices change when the model changes. For anything that must survive edits, capture `entityToken` values (`BRepFace.entityToken`, `Component.entityToken`) and resolve them with `Design.findEntityByToken`.

## Example 2 — drive user parameters from a data file

A CSV of cabinet variants, applied one at a time, with a saved export per variant. Note `Design.modifyParameters` is **all-or-nothing** — "if it fails to set any parameters, none of them are updated" — which is exactly the transactional behaviour you want.

```python
# DriveFromCsv.py
import adsk.core, adsk.fusion, traceback, csv, os

def apply_row(design, row: dict) -> bool:
    params, values = [], []
    for name, expr in row.items():
        if name.startswith('#') or not expr:
            continue
        p = design.allParameters.itemByName(name)
        if p is None:
            raise ValueError('No parameter "{}" in this design'.format(name))
        params.append(p)
        values.append(adsk.core.ValueInput.createByString(str(expr)))
    return design.modifyParameters(params, values)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        dlg = ui.createFileDialog()
        dlg.title = 'Select the variants CSV'
        dlg.filter = 'CSV files (*.csv)'
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK:
            return
        path = dlg.filename
        outdir = os.path.join(os.path.dirname(path), 'variants')
        os.makedirs(outdir, exist_ok=True)

        em = design.exportManager
        made = []
        with open(path, newline='', encoding='utf-8-sig') as fh:
            for row in csv.DictReader(fh):
                label = row.pop('Variant', 'variant')
                if not apply_row(design, row):
                    raise RuntimeError('Parameter set failed for ' + label)
                design.computeAll()
                adsk.doEvents()
                opts = em.createSTEPExportOptions(
                    os.path.join(outdir, '{}.step'.format(label)))
                em.execute(opts)
                made.append(label)
        ui.messageBox('Exported {} variants:\n{}'.format(len(made), '\n'.join(made)))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

CSV shape:

```csv
Variant,CarcassWidth,CarcassHeight,CarcassDepth,BoardThickness
BU300,300 mm,720 mm,560 mm,17.9 mm
BU600,600 mm,720 mm,560 mm,17.9 mm
BU900,900 mm,720 mm,560 mm,17.9 mm
WU600,600 mm,720 mm,320 mm,17.9 mm
```

The lower-code alternative is `UserParameters.importUserParameters()` / `exportUserParameters()`, or Autodesk's **ParameterIO_Python** add-in, which does CSV parameter round-tripping through a dialog.

## Example 3 — export every component to DXF

For each component, find the largest planar face, sketch on it (which projects the face's edges — `Sketches.add` on a `BRepFace` projects the edges; `addWithoutEdges` does not), and export that sketch as DXF.

```python
# ExportPanelsDxf.py
import adsk.core, adsk.fusion, traceback, os, re

def safe(name):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)

def largest_planar_face(body):
    planar = [f for f in body.faces
              if f.geometry.objectType == adsk.core.Plane.classType()]
    return max(planar, key=lambda f: f.area) if planar else None

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        em = design.exportManager

        dlg = ui.createFolderDialog()
        dlg.title = 'Choose an output folder for the DXFs'
        if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        outdir = dlg.folder

        done, skipped = [], []
        seen = set()
        for occ in root.allOccurrences:
            comp = occ.component
            if comp.id in seen:          # one DXF per component, not per occurrence
                continue
            seen.add(comp.id)
            if comp.bRepBodies.count == 0:
                continue
            for i in range(comp.bRepBodies.count):
                body = comp.bRepBodies.item(i)
                face = largest_planar_face(body)
                if face is None:
                    skipped.append(comp.name)
                    continue
                # Sketches.add(BRepFace) projects the face edges into the sketch.
                sk = comp.sketches.add(face)
                sk.name = 'DXF_{}_{}'.format(safe(comp.name), i)
                fn = os.path.join(outdir, '{}_{}.dxf'.format(safe(comp.name), i))
                # Sketch.saveAsDXF was RETIRED in July 2025 — use ExportManager.
                opts = em.createDXFSketchExportOptions(fn, sk)
                em.execute(opts)
                done.append(os.path.basename(fn))

        ui.messageBox('Exported {} DXF files to\n{}\n\nSkipped (no planar face): {}'
                      .format(len(done), outdir, ', '.join(skipped) or 'none'))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

Refinements for real shop use:

- **Project the through-features too.** `sk.project2([edge_or_face, ...], False)` brings additional geometry in unlinked (`Sketch.project` was retired in May 2025 in favour of `project2(entities, isLinked)`).
- **Put pockets and drillings on named layers.** Fusion's DXF export writes sketch geometry; controlling layers requires post-processing the DXF (e.g. with `ezdxf` outside Fusion) or exporting one DXF per feature class and merging.
- **Delete the temporary sketches afterwards** (`sk.deleteMe()`) so the model is not littered — or create them inside a base feature you can roll back.
- The other `ExportManager` factories are `createDXFFlatPatternExportOptions(filename, flatPattern)`, `createSTEPExportOptions`, `createIGESExportOptions`, `createSATExportOptions`, `createSMTExportOptions`, `createSTLExportOptions`, `createOBJExportOptions`, `createC3MFExportOptions`, `createUSDExportOptions`, `createFusionArchiveExportOptions`, each followed by `exportManager.execute(options)`.

## Example 4 — generate a joinery cut list

Uses `Component.orientedMinimumBoundingBox` (which "returns an oriented bounding box that is best oriented to tightly [fit]" the component) and `PhysicalProperties` (mass in **kg**, volume in **cm³**, area in **cm²**).

```python
# CutList.py
import adsk.core, adsk.fusion, traceback, os, csv
from collections import defaultdict

def mm(cm):
    return round(cm * 10.0, 1)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # Count occurrences per component.
        qty = defaultdict(int)
        comps = {}
        for occ in root.allOccurrences:
            c = occ.component
            if c.bRepBodies.count == 0:
                continue                      # skip pure sub-assemblies
            qty[c.id] += 1
            comps[c.id] = c

        rows = []
        for cid, comp in comps.items():
            obb = comp.orientedMinimumBoundingBox
            if obb is None:
                continue
            dims = sorted([obb.length, obb.width, obb.height], reverse=True)
            L, W, T = mm(dims[0]), mm(dims[1]), mm(dims[2])
            try:
                props = comp.getPhysicalProperties(
                    adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy)
                mass = round(props.mass, 3)          # kg
            except:
                mass = ''
            material = comp.material.name if comp.material else ''
            rows.append({
                'PartNumber': comp.partNumber or comp.name,
                'Name': comp.name,
                'Qty': qty[cid],
                'Length_mm': L,
                'Width_mm': W,
                'Thickness_mm': T,
                'Material': material,
                'Description': comp.description or '',
                'Area_m2': round(L * W / 1e6, 4),
                'TotalArea_m2': round(qty[cid] * L * W / 1e6, 4),
                'Mass_kg_each': mass,
            })

        rows.sort(key=lambda r: (-r['Thickness_mm'], -r['Length_mm']))

        dlg = ui.createFolderDialog()
        dlg.title = 'Where should the cut list go?'
        if dlg.showDialog() != adsk.core.DialogResults.DialogOK:
            return
        path = os.path.join(dlg.folder, '{}_cutlist.csv'.format(
            app.activeDocument.name.replace(' ', '_')))

        with open(path, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

        total = sum(r['TotalArea_m2'] for r in rows)
        sheets = total / (2.750 * 1.830)
        ui.messageBox(
            '{} distinct parts, {} pieces.\n'
            'Total panel area {:.2f} m^2 = {:.1f} sheets at 2750x1830 '
            '(before waste).\n\nWritten to:\n{}'.format(
                len(rows), sum(r['Qty'] for r in rows), total, sheets, path))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

Add 10–20 % for nesting waste (`joinery.specifying`). Encode edging and grain in `Component.description` with a convention you parse — e.g. `18MFC|EB:2L1S|GRAIN:L` — so the cut list, the labels and the nester all agree.

`needs-verification`: the exact member name of the calculation-accuracy enum (`CalculationAccuracy.MediumCalculationAccuracy`) was not individually confirmed; if it errors, call `comp.physicalProperties` instead, which takes no argument.

## Driving Fusion from an AI agent

Autodesk publishes **`AutodeskFusion360/FusionMCPSample`** (MIT) — a Fusion add-in that runs an **HTTP Model Context Protocol server inside Fusion**, so an external agent can call into the live application. Its architecture is instructive:

- **TaskManager** — marshals Fusion API calls from background threads onto Fusion's main thread using **Fusion's custom event system**. This is mandatory: the Fusion API is not thread-safe and must be touched only from the main thread.
- **McpServer** — a threaded HTTP server.
- **Main add-in** — exposes MCP endpoints.

The three tools it offers an agent are exactly the right primitives:

1. **`execute_api_script`** — run arbitrary Python against the Fusion API.
2. **`get_screenshot`** — capture the viewport in a chosen orientation, so the agent can *see* what it made.
3. **`get_api_documentation`** — search the Fusion API reference for classes, methods and properties.

That third tool matters more than it looks: the API surface is large and an agent that guesses class names will hallucinate. Pair it with the **`FusionAPIReference`** repo, which bundles the HTML docs, C++ headers and **Python stubs** into "a single, local reference corpus intended for both developers and tooling (including LLMs/RAG)" and ships an `llms.txt`.

**Practical agent patterns:**

- **Generate-and-verify.** Have the agent write a script, run it, then read back `sketch.isFullyConstrained`, `design.timeline` error states, and an oriented bounding box — numeric assertions, not screenshots.
- **Keep the source of truth outside Fusion.** A YAML or CSV specification of the joinery package, versioned in git, with Fusion as a renderer of it. Then a rebuild is reproducible.
- **Idempotent scripts.** Every generator should check whether the parameter/component/sketch already exists and update rather than duplicate, so re-running is safe.
- **Never let an agent post G-code unattended.** Generation and simulation, yes; the transfer to the machine is a human decision (`06_cam-and-manufacturing.md`).

## The cloud side: Fusion Data API, APS and Design Automation

Everything above runs **inside** the desktop app. Autodesk also offers server-side access under **Autodesk Platform Services (APS)**, formerly Forge:

- **Fusion Data API** — a **GraphQL** API over the data in your Autodesk hubs: hubs, projects, folders, components, component versions, custom properties and thumbnails. It reads and writes *metadata and structure*, not geometry features. The natural use is a dashboard or an ERP link — "list every component in this project with its part number, material and last revision" — without opening Fusion. Authentication is standard APS OAuth (2-legged for app-only, 3-legged for user data). Docs at `https://aps.autodesk.com/en/docs/fusiondata/v1/developers_guide/overview/`; the pages render client-side and could not be captured verbatim here, so treat the specifics as `needs-verification`.
- **Design Automation for Fusion** — runs Fusion headlessly in Autodesk's cloud against a script you supply. Autodesk publishes **`AutodeskFusion360/DesignAutomationSamples`** ("Various Design Automation for Fusion samples", MIT). This is the mechanism for "a customer configures a cabinet on our website and gets a price and a DXF" without a workstation in the loop. Access has historically been gated — enquire through APS.
- **Data Management API / OSS / Model Derivative** — the general APS services for file storage, translation and viewing. Model Derivative can turn an `.f3d` into a web-viewable SVF for the Autodesk Viewer, which is a cheap way to show a client a 3D kitchen in a browser.

For a small practice the honest recommendation is: **use the client-side Python API for everything, and reach for APS only when you need a web service.** APS involves app registration, OAuth, quotas and real engineering effort.

## Sources

- [Fusion API Reference (browsable)](https://autodeskfusion360.github.io/FusionAPIReference/) — Autodesk, accessed 2026-08-25
- [FusionAPIReference repository](https://github.com/AutodeskFusion360/FusionAPIReference) — Autodesk on GitHub, accessed 2026-08-25
- [FusionMCPSample — MCP server add-in](https://github.com/AutodeskFusion360/FusionMCPSample) — Autodesk on GitHub, accessed 2026-08-25
- [DesignAutomationSamples](https://github.com/AutodeskFusion360/DesignAutomationSamples) — Autodesk on GitHub, accessed 2026-08-25
- [Fusion API Reference — Design.modifyParameters](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design_modifyParameters.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — UserParameters.add](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/UserParameters_add.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — ExportManager](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — ExportManager.createDXFSketchExportOptions](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/ExportManager_createDXFSketchExportOptions.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Sketch.saveAsDXF (retired)](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch_saveAsDXF.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Sketch.project2](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch_project2.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Sketches](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketches.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Component](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — PhysicalProperties](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/PhysicalProperties.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — MeasureManager.getOrientedBoundingBox](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/MeasureManager_getOrientedBoundingBox.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — CommandDefinitions.addButtonDefinition](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/CommandDefinitions_addButtonDefinition.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — TextCommandPalette](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/TextCommandPalette.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — NCPrograms](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/NCPrograms.htm) — Autodesk, accessed 2026-08-25
- [Fusion API and Scripts forum](https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22) — Autodesk, accessed 2026-08-25
- [Fusion Data API developer guide](https://aps.autodesk.com/en/docs/fusiondata/v1/developers_guide/overview/) — Autodesk Platform Services, accessed 2026-08-25 (page renders client-side; content not captured)

## Open questions

- Workspace and panel IDs (`FusionSolidEnvironment`, `SolidScriptsAddinsPanel`) are long-standing community knowledge, not quoted documentation. Enumerate at runtime rather than trusting them. `needs-verification`.
- `adsk.fusion.CalculationAccuracy` member names, and `HoleFeatureInput.setPositionBySketchPoint` / `setDistanceExtent` exact names, were not individually verified against reference pages.
- Fusion Data API specifics (endpoint URL, entity names, auth scopes) — APS docs render client-side and could not be captured. `needs-verification`.
- Current availability and access process for Design Automation for Fusion.
- Whether `pip`-installed third-party packages are supported in the embedded interpreter in the May 2026 release.
