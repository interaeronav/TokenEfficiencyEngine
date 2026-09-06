# 71 — The Fusion lane (A69): Autodesk Fusion as a live, first-class TEE lane

**Owner directive (2026-09-06, verbatim):** *"Create a lane dedicated to
autodesk fusion."*

Status: design of record for `CLAUDE_A69_SCRIPT.md`. Every API fact in §3
was read from Autodesk's Fusion API reference or from Autodesk's own
`FusionMCPSample` on 2026-09-06 (the URLs are in the table). **None of it
has run against a live Fusion on this machine** — Fusion has no Linux
build — so §3 separates "verified in the reference" from "measured live",
and the live column is filled by the smoke procedure in the script (P4)
on the owner's Mac. The rule in `CLAUDE.md` outranks memory: an API call
that is not in §3 does not go into the codegen.

## 1. What a Fusion lane is, and is not

Fusion is a **live, GUI-only, cloud-saved** parametric CAD application. There
is no headless Fusion, and no official local HTTP surface: code runs inside
the application as a script or an add-in, in Fusion's embedded Python, and
the API must be touched **only from the primary thread** (§3, rows 1–3).
So the lane is the Blender shape, not the partkiln shape:

- **A bridge add-in** (`adapters/fusion/tee_bridge/TEE/`) runs inside Fusion,
  listens on `127.0.0.1:9881`, and executes what TEE sends on the primary
  thread through Fusion's custom-event queue.
- **The adapter** (`server/src/tee/adapters/fusion/`) is the seven kit
  methods plus `vocab()`: a batch compiles to ONE Python script executed in
  ONE round trip (the FreeCAD precedent, `adapters/freecad/codegen.py`), the
  script prints ONE JSON diff, and the kernel supplies checkpoints, diffs,
  the compact summary, search, the trust check and routing.
- **Zero new always-loaded tools.** The `fu_*` long tail lives behind
  `tee_search_tools`; the surface stays 17 tools.

What it is not: it is not partkiln. partkiln is headless, deterministic and
owned by TEE; Fusion is the owner's open document. The two share vocabulary
(sketch, extrude, fillet) on purpose — the words mean the same thing — and
A68's router refuses an ambiguous batch naming both lanes when both are
live; §4.9 refines the router so a lane whose application is not running is
never a candidate.

## 2. Prior art, and what was taken from it

**`AutodeskFusion360/FusionMCPSample` (MIT).** Autodesk's own MCP server
add-in: a threaded HTTP server inside Fusion, a `TaskManager` that marshals
work onto the primary thread with `Application.registerCustomEvent` /
`fireCustomEvent` and a `CustomEventHandler.notify(args)` that reads
`args.additionalInfo`, and three tools — `execute_api_script`,
`get_screenshot`, `get_api_documentation`. Its marshalling code was read in
full (§3 row 3) and the same mechanism is used here. Its *posture* is the
opposite of TEE's: the model-facing tool is "run this Python". TEE fronts the
same API with typed ops and diffs, and keeps "run this Python" as
`fu_execute_python` behind `exec-code`, denied by default.

**`knowledge-base/15_software_autodesk_fusion/09_api-and-automation.md`**
(the owner's imported reference, `confidence: high`, sources cited). Used
for orientation only, per the `CLAUDE.md` rule about API prose in `13_*`,
`14_*` and `15_*`: every call it names that this lane uses was re-checked
against the reference it cites. Two of its facts survived re-checking and
matter most: **internal units are centimetres and radians**, and
`Sketch.saveAsDXF` / `Sketch.project` / `CAM.postProcess` are **retired** —
and re-checking found a third retirement the KB does not list:
`ExtrudeFeatureInput.setDistanceExtent` (retired September 2022, §3 row 8).

**TEE's own precedents.** The FreeCAD adapter (script per batch, hermetic
shim that `exec`s the generated scripts), the Blender wire (NUL-framed JSON,
`result` dict convention, per-call connections), the Godot bridge (one
request per connection, declarative payloads), partkiln's static vocabulary
(routing never waits on anything), and A68's `handoff_import.land()` (an
export lands in a scene lane only when `into=` says so).

## 3. API facts (reference-verified 2026-09-06; live column: the Mac smoke)

Base URL: `https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/`

| # | Call (as the codegen emits it) | Verified from | What the reference says | Live |
|---|---|---|---|---|
| 1 | `app.registerCustomEvent(id) -> CustomEvent` | `Application_registerCustomEvent.htm` | "intended to be primarily used to send an event from a worker thread you've created back to your add-in running in the primary thread"; null if the id is not unique | ○ |
| 2 | `app.fireCustomEvent(id, additionalInfo)` | `Application_fireCustomEvent.htm` | queues; "does not immediately result in the event handler being called" — runs when the application is idle, in the primary thread | ○ |
| 3 | `class H(adsk.core.CustomEventHandler): notify(self, args)`; `args.additionalInfo` | `CustomEventArgs.htm` + FusionMCPSample `server/task_manager.py` (read in full) | the sample subclasses `CustomEventHandler`, reads `json.loads(args.additionalInfo)`, and fires with `app.fireCustomEvent(event.eventId, json.dumps(...))` | ○ |
| 4 | `adsk.core.Application.get()`; `app.activeProduct`, `app.activeDocument`, `app.activeViewport`, `app.importManager`, `app.version`, `app.log` | `Application.htm` | activeProduct/Document/Viewport are null with no document open | ○ |
| 5 | `design = adsk.fusion.Design.cast(app.activeProduct)`; `design.rootComponent`, `.timeline`, `.userParameters`, `.allParameters`, `.exportManager`, `.designType`, `.findEntityByToken(token) -> Base[]` | `Design.htm`, `Design_findEntityByToken.htm` | designType is Direct or Parametric; findEntityByToken returns an array (a split face yields several) | ○ |
| 6 | `comp.sketches.add(comp.xYConstructionPlane)`; `comp.xZConstructionPlane`, `comp.yZConstructionPlane`, `comp.features`, `comp.bRepBodies`, `comp.occurrences`, `comp.allOccurrences`, `comp.name`, `comp.entityToken`, `comp.physicalProperties`, `comp.boundingBox` | `Component.htm` | | ○ |
| 7 | `sketch.sketchCurves.sketchLines.addTwoPointRectangle(Point3D, Point3D)`; `sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D, r_cm)`; `sketch.profiles`, `sketch.name`, `sketch.isVisible`, `sketch.entityToken`, `sketch.deleteMe()`, `sketch.timelineObject` | `SketchLines_addTwoPointRectangle.htm`, `SketchCircles_addByCenterRadius.htm`, `Sketch.htm` | radius "in centimeters"; points are Point3D in sketch space | ○ |
| 8 | `ext = comp.features.extrudeFeatures.createInput(profile, op)`; `ext.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(ValueInput), adsk.fusion.ExtentDirections.PositiveExtentDirection)`; `comp.features.extrudeFeatures.add(ext)` | `ExtrudeFeatures_createInput.htm`, `ExtrudeFeatureInput_setOneSideExtent.htm`, `DistanceExtentDefinition_create.htm` | **`setDistanceExtent` is retired (Sept 2022)**; profile may be a Profile or an ObjectCollection of profiles | ○ |
| 9 | `adsk.fusion.FeatureOperations.{Join,Cut,Intersect,NewBody,NewComponent}FeatureOperation` | `FeatureOperations.htm` | values 0,1,2,3,4 | ○ |
| 10 | `adsk.core.ValueInput.createByString("120 mm")` | `ValueInput_createByString.htm` | units in the string are respected; a unitless string takes the document's active unit — so the codegen ALWAYS writes the unit | ○ |
| 11 | `fi = comp.features.filletFeatures.createInput()`; `fi.edgeSetInputs.addConstantRadiusEdgeSet(ObjectCollection, ValueInput, isTangentChain)`; `filletFeatures.add(fi)` | `FilletFeatures_createInput.htm`, `FilletEdgeSetInputs_addConstantRadiusEdgeSet.htm` | edges may be BRepEdge/BRepFace/Feature objects; real radius values default to cm, strings carry units | ○ |
| 12 | `occ = comp.occurrences.addNewComponent(adsk.core.Matrix3D.create())`; `occ.component.name = ...`; `occ.entityToken`, `occ.deleteMe()`, `occ.timelineObject`, `occ.bRepBodies` | `Occurrences_addNewComponent.htm`, `Occurrence.htm` | the new Component is reached through `occurrence.component` | ○ |
| 13 | `design.userParameters.add(name, ValueInput, "mm", comment) -> UserParameter`; `param.expression` (settable), `param.value` (internal cm/rad), `param.unit`, `param.name`, `param.isDeletable`, `param.deleteMe()` | `UserParameters_add.htm`, `Parameter.htm` | boolean ValueInputs unsupported; empty units = unitless | ○ |
| 14 | `body.name`, `body.volume` (cm³), `body.area` (cm²), `body.boundingBox` (min/maxPoint, cm), `body.physicalProperties` (mass kg, centerOfMass cm), `body.faces`, `body.edges`, `body.isSolid`, `body.isVisible`, `body.entityToken`, `body.deleteMe()` | `BRepBody.htm`, `PhysicalProperties.htm` | | ○ |
| 15 | `feature.name`, `feature.entityToken`, `feature.deleteMe()`, `feature.timelineObject`, `feature.isSuppressed`, `feature.bodies`, `feature.healthState`, `feature.errorOrWarningMessage`; `extrude.extentOne` distance is a ModelParameter with a settable `expression` | `Feature.htm`, `Parameter.htm` | deleteMe "works for both parametric and non-parametric features" | ○ |
| 16 | `timeline.markerPosition` (settable, 0..count), `timeline.count`, `timeline.item(i)`, `timeline.deleteAllAfterMarker()`, `timeline.moveToEnd()`; `TimelineObject.entity/name/index/isSuppressed/isRolledBack/isGroup/healthState` | `Timeline.htm`, `TimelineObject.htm` | | ○ |
| 17 | `design.exportManager.createSTEPExportOptions(filename, geometry=None)`, `createSTLExportOptions(geometry, filename)`, `createOBJExportOptions(geometry, filename)` (Oct 2022), `createFusionArchiveExportOptions(filename, geometry=None)`, `createC3MFExportOptions`, `createIGESExportOptions`, `createSATExportOptions`, `createUSDExportOptions`; `exportManager.execute(options)` | `ExportManager.htm` + the four member pages | **parameter order differs by method** (STEP/archive: filename first; STL/OBJ: geometry first) — the codegen keeps a per-format table | ○ |
| 18 | `app.importManager.createSTEPImportOptions(path)`, `createFusionArchiveImportOptions`, `createIGESImportOptions`, `createSATImportOptions`; `importManager.importToTarget2(options, component) -> ObjectCollection` | `ImportManager.htm`, `ImportManager_importToTarget2.htm` | no OBJ/STL import in the manager; importToTarget2 "cannot be used within any of the Command related events" (the bridge is not a command event) | ○ |
| 19 | `app.activeViewport.fit()`; `viewport.saveAsImageFile(filename, width, height) -> bool` | `Viewport.htm`, `Viewport_saveAsImageFile.htm` | format inferred from the extension (which extensions is NOT stated — the smoke tries `.jpg`, then `.png`); re-rendered at the requested size | ○ |
| 20 | add-in manifest keys `autodeskProduct`, `type: "addin"`, `author`, `description`, `version`, `runOnStartup`, `supportedOS`, `editEnabled`, `iconFilename` | FusionMCPSample `Fusion MCP Addin.manifest` (verbatim) | | ○ |
| 21 | `adsk.fusion.DesignTypes.DirectDesignType` (0), `.ParametricDesignType` (1) | `DesignTypes.htm` | | ○ |
| 22 | `adsk.core.Point3D.create(x, y, z)` (defaults 0.0) | `Point3D_create.htm` | | ○ |
| 23 | `adsk.core.ObjectCollection.create()`; `.add(entity)` | `ObjectCollection_create.htm` (add: the class page) | | ○ |
| 24 | `adsk.core.Matrix3D.create()` — an identity matrix | `Matrix3D_create.htm` | | ○ |
| 25 | `doc.name`, `doc.isSaved`, `doc.isModified` — read only by the lane (Law 5: `close`/`save`/`saveAs` are never called) | `Document.htm` | | ○ |
| 26 | the collection convention `.count` / `.item(i)` on Sketches, Features, BRepBodies, Occurrences, Profiles, BRepEdges, UserParameters, ParameterList | `BRepEdges.htm`, `UserParameters.htm` (read); the others are the same class family | `UserParameters.itemByName(name)` too | ○ |
| 27 | `extrude.extentOne` (gets/sets the extent) → `DistanceExtentDefinition.distance` — "the parameter controlling the distance. You can edit the distance by editing the value of the parameter object" | `ExtrudeFeature.htm`, `DistanceExtentDefinition.htm` | a `set` of `expression` on an extrude edits that parameter | ○ |
| 28 | `body.isVisible`, `sketch.isVisible` — read/write | `BRepBody_isVisible.htm`, `Sketch_isVisible.htm` | | ○ |
| 29 | `UserParameter.deleteMe()` ("only if it is a UserParameter and it is not referenced by other parameters"); `UserParameter.name` settable, must be unique | `UserParameter.htm` | | ○ |
| 30 | `STLExportOptions.unitType` (default: the design's default units), `OBJExportOptions.unitType` (default: centimetres) | `STLExportOptions.htm`, `OBJExportOptions.htm` | the enum's name was not in the page read, so v1 never SETS it: `fu_export` declares `units: cm` for obj and reads `unitType` back raw for the record | ○ |
| 31 | `_root.features.holeFeatures.createSimpleInput(ValueInput)`, `.createCounterboreInput(d, cbDiameter, cbDepth)`, `.createCountersinkInput(d, csDiameter, csAngle)`; `holeFeatures.add(input) -> HoleFeature` | `HoleFeatures.htm`, `HoleFeatures_createSimpleInput.htm`, `HoleFeatures_createCounterboreInput.htm`, `HoleFeatures_createCountersinkInput.htm` | reals are centimetres (the countersink angle: radians), strings carry their units — the codegen writes `mm` and `deg`; `add` returns null on failure | ○ |
| 32 | `hole.setPositionByPoint(planarEntity, point)`; `hole.setPositionBySketchPoint(sketchPoint)` | `HoleFeatureInput_setPositionByPoint.htm`, `HoleFeatureInput_setPositionBySketchPoint.htm` | planarEntity is a planar BRepFace or a ConstructionPlane, point a Point3D or a vertex; a Point3D "will be projected onto the plane along the planes normal" (non-associative); a sketch point orients the hole by its sketch's normal and "the natural direction will be opposite the normal of the sketch" | ○ |
| 33 | `hole.setDistanceExtent(ValueInput)`; `hole.setAllExtent(ExtentDirections)`; `hole.isDefaultDirection` (settable); `hole.tipAngle`; `adsk.fusion.ExtentDirections.{Positive,Negative,Symmetric}ExtentDirection` (0, 1, 2) | `HoleFeatureInput_setDistanceExtent.htm`, `HoleFeatureInput_setAllExtent.htm`, `HoleFeatureInput.htm`, `ExtentDirections.htm` | **`setDistanceExtent` is NOT retired for holes** (August 2014, still current — the extrude retirement of row 8 does not carry over); through-all takes a direction "relative to the normal of the sketch plane"; the tip angle defaults to 118 deg | ○ |
| 34 | `HoleFeature.holeDiameter` (Parameter), `.position` (Point3D), `.holeType`, `.direction` (Vector3D), `.counterboreDiameter` / `.counterboreDepth` / `.countersinkDiameter` / `.countersinkAngle` (Parameters) | `HoleFeature.htm` | a `set` of `diameter` on a hole edits `holeDiameter.expression` | ○ |
| 35 | `_root.features.chamferFeatures.createInput2()`; `inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(ObjectCollection, ValueInput, isTangentChain)`; `chamferFeatures.add(inp)`; `ChamferFeature.edgeSets`, `.faces` | `ChamferFeatures.htm`, `ChamferFeatures_createInput2.htm`, `ChamferEdgeSets_addEqualDistanceChamferEdgeSet.htm`, `ChamferFeatureInput.htm`, `ChamferFeature.htm` | **`ChamferFeatures.createInput` is RETIRED** (`createInput2`, December 2020), as are `ChamferFeatureInput.edges` / `.isTangentChain` / `.setToEqualDistance` and `ChamferFeature.edges` / `.chamferType` / `.setEqualDistance`; the edge collection may hold BRepEdge, BRepFace or Feature objects | ○ |
| 36 | `_root.features.revolveFeatures.createInput(profile, axis, operation)`; `inp.setAngleExtent(isSymmetric, ValueInput)`; `revolveFeatures.add(inp)`; `RevolveFeature.axis` / `.profile` / `.extentDefinition` | `RevolveFeatures_createInput.htm`, `RevolveFeatureInput_setAngleExtent.htm`, `RevolveFeatureInput.htm`, `RevolveFeatures.htm`, `RevolveFeature.htm` | the axis "can be a sketch line, construction axis, linear edge or a face that defines an axis"; the profile a Profile, a planar face or an ObjectCollection; `setAngleExtent` carries no retirement note ("A 360-degree or 2π radian angle produces a complete revolution"; symmetric applies the angle to each side) | ○ |
| 37 | `_root.xConstructionAxis` / `.yConstructionAxis` / `.zConstructionAxis`, `_root.originConstructionPoint`, `_root.joints`, `_root.jointOrigins`, `_root.constructionAxes`, `_root.constructionPoints` | `Component.htm` | | ○ |
| 38 | `sketch.sketchCurves.sketchLines.addByTwoPoints(start, end) -> SketchLine`; `addTwoPointRectangle(p1, p2) -> SketchLineList` (`.count` / `.item(i)`); `sketch.sketchPoints.add(Point3D) -> SketchPoint`; `sketch.originPoint`; `sketch.geometricConstraints`; `sketch.sketchDimensions`; `sketch.isFullyConstrained` | `SketchLines_addByTwoPoints.htm`, `SketchLines_addTwoPointRectangle.htm`, `SketchLineList.htm`, `SketchPoints_add.htm`, `Sketch.htm` | end points may be SketchPoints or Point3Ds (a line on a SketchPoint follows it); **the order of a rectangle's four lines is NOT stated**, so the codegen names the sides by where their midpoints lie, never by index | ○ |
| 39 | `SketchLine.startSketchPoint` / `.endSketchPoint` / `.length` (cm) / `.isConstruction` / `.isFullyConstrained` / `.entityToken` / `.deleteMe()`; `SketchCircle.centerSketchPoint` / `.radius` (settable, cm) / `.isFullyConstrained`; `SketchPoint.geometry` (Point3D "always in sketch space") / `.worldGeometry` / `.isFullyConstrained` / `.entityToken` | `SketchLine.htm`, `SketchCircle.htm`, `SketchPoint.htm` | | ○ |
| 40 | `sketch.geometricConstraints.addHorizontal(line)`, `addVertical(line)`, `addParallel(l1, l2)`, `addPerpendicular(l1, l2)`, `addCollinear(l1, l2)`, `addEqual(c1, c2)`, `addTangent(c1, c2)`, `addConcentric(e1, e2)`, `addCoincident(point, entity)`, `addMidPoint(point, curve)`, `addSymmetry(e1, e2, line)` | the eleven `GeometricConstraints_add*.htm` pages, `GeometricConstraints.htm` | each "returns the newly created … object or null if the creation failed"; coincident's first argument is a SketchPoint and its second "a sketch curve or point"; equal takes two lines or arcs/circles; concentric circles, arcs, ellipses; `addOffset` is RETIRED | ○ |
| 41 | `sketch.sketchDimensions.addDistanceDimension(p1, p2, DimensionOrientations, textPoint, isDriving=True) -> SketchLinearDimension`; `addDiameterDimension(circle, textPoint, isDriving=True)`; `addRadialDimension(circle, textPoint, isDriving=True)`; `addAngularDimension(l1, l2, textPoint, isDriving=True)`; `adsk.fusion.DimensionOrientations.{Aligned,Horizontal,Vertical}DimensionOrientation` (0, 1, 2) | `SketchDimensions_addDistanceDimension.htm`, `SketchDimensions_addDiameterDimension.htm`, `SketchDimensions_addRadialDimension.htm`, `SketchDimensions_addAngularDimension.htm`, `DimensionOrientations.htm` | the points are SketchPoints, the text point a Point3D in sketch space; for an angle "the position of the text also defines which quadrant will be dimensioned" | ○ |
| 42 | `SketchDimension.parameter` (Parameter, or null), `.value` (cm / rad, settable), `.isDriving`, `.textPosition`, `.isDeletable`, `.deleteMe()`, `.entityToken` | `SketchDimension.htm` | a driving dimension's `parameter.expression` is where a user parameter binds (`"width"`) — the parametric truth v1 left to feature expressions | ○ |
| 43 | `_root.joints.createInput(geometryOrOriginOne, geometryOrOriginTwo) -> JointInput`; `_root.joints.add(JointInput) -> Joint` | `Joints_createInput.htm`, `Joints_add.htm`, `Joints.htm` | either argument "a JointGeometry or JointOrigin object"; `add` returns null on failure | ○ |
| 44 | `adsk.fusion.JointGeometry.createByPlanarFace(face, edge, JointKeyPointTypes)`; `adsk.fusion.JointGeometry.createByPoint(ConstructionPoint \| SketchPoint \| BRepVertex)`; `adsk.fusion.JointKeyPointTypes.{Start,Middle,End,Center}KeyPoint` (0–3) | `JointGeometry_createByPlanarFace.htm`, `JointGeometry_createByPoint.htm`, `JointKeyPointTypes.htm`, `JointGeometry.htm` | the edge "can be null in the case where the keyPointType is CenterKeypoint indicating the center of the face is to be used" | ○ |
| 45 | `JointInput.setAsRigidJointMotion()`, `.setAsRevoluteJointMotion(JointDirections, customAxis=None)`, `.setAsSliderJointMotion(JointDirections, customDir=None)`, `.setAsCylindricalJointMotion(JointDirections, customAxis=None)`, `.setAsPinSlotJointMotion(rotationAxis, slideDirection, …)`, `.setAsPlanarJointMotion(normalDirection, …)`, `.setAsBallJointMotion(pitchDirection, yawDirection, …)`; `JointInput.angle` / `.offset` (ValueInput: a real is radians / centimetres, a string takes the document's unit) ; `.isFlipped`; `adsk.fusion.JointDirections.{X,Y,Z}AxisJointDirection` (0, 1, 2), `CustomJointDirection` (3) | `JointInput.htm`, the seven `JointInput_setAs*JointMotion.htm` pages, `JointInput_angle.htm`, `JointInput_offset.htm`, `JointDirections.htm` | ball's pitch is Z-or-custom and yaw X-or-custom; the codegen writes `deg` and `mm` into the angle and offset strings | ○ |
| 46 | `Joint.jointMotion`, `.occurrenceOne` / `.occurrenceTwo`, `.name`, `.isSuppressed`, `.isFlipped`, `.isLocked`, `.angle` / `.offset` (Parameters), `.healthState`, `.entityToken`, `.deleteMe()`, `.timelineObject`; `RevoluteJointMotion.rotationValue` (radians, settable — "the same as using the Drive Joints command"), `.rotationAxis`; `SliderJointMotion.slideValue` (cm, settable), `.slideDirection` | `Joint.htm`, `RevoluteJointMotion.htm`, `SliderJointMotion.htm` | | ○ |
| 47 | `BRepFace.geometry` (a Surface: `.surfaceType` against `adsk.core.SurfaceTypes.PlaneSurfaceType` = 0; a Plane's `.normal` / `.origin`), `.isParamReversed`, `.centroid`, `.area` (cm²), `.edges`, `.vertices`, `.pointOnFace`, `.boundingBox`, `.createForAssemblyContext(occ)`; `BRepEdge.startVertex` / `.endVertex` / `.length` (cm) / `.faces` / `.pointOnEdge`; `BRepVertex.geometry`; `ConstructionPoint.geometry` / `.createForAssemblyContext(occ)` | `BRepFace.htm`, `BRepFace_isParamReversed.htm`, `BRepFace_createForAssemblyContext.htm`, `Surface.htm`, `SurfaceTypes.htm`, `Plane.htm`, `BRepEdge.htm`, `BRepVertex.htm`, `ConstructionPoint.htm` | `isParamReversed`: "the normal of this face is reversed with respect to the surface geometry" — the outward normal is the plane's, flipped when set; a proxy "or null if this isn't the NativeObject" (the bodies under `occ.bRepBodies`, row 12, are already in occurrence context) | ○ |
| 48 | `exportManager.createIGESExportOptions(filename, geometry=None)`, `createSATExportOptions(filename, geometry=None)`, `createUSDExportOptions(filename, geometry=None)` — geometry "currently a Component object", None exports the root; `createC3MFExportOptions(geometry, filename="")` — geometry "a BRepBody, Occurrence, or Component" | `ExportManager_createIGESExportOptions.htm`, `ExportManager_createSATExportOptions.htm`, `ExportManager_createUSDExportOptions.htm`, `ExportManager_createC3MFExportOptions.htm`, `C3MFExportOptions.htm`, `USDExportOptions.htm` | 3MF is geometry-first like STL/OBJ and REQUIRES a geometry; its options carry mesh refinement and no unit property; USD's carry only filename and geometry — the units are whatever each file declares inside, which the smoke reads | ○ |
| 49 | **The drawing surface, read for its absence.** `adsk.core.DocumentTypes` has ONE member, `FusionDesignDocumentType` (0), so `Documents.add(documentType, visible=True, options=None)` cannot create a drawing; `adsk.drawing.Drawing` exposes `exportManager`, `namedViews`, `attributes` and no sheets or views collection; `DrawingViews.htm` and `DrawingSheets.htm` do not exist (404); `DrawingDocument.drawing.exportManager.createPDFExportOptions(filename) -> PDFExportOptions` and `.execute(options)` exist for a drawing the owner has OPEN | `DocumentTypes.htm`, `Documents_add.htm`, `Drawing.htm`, `DrawingDocument.htm`, `DrawingExportManager.htm`, `DrawingExportManager_createPDFExportOptions.htm` | the API can export a drawing that already exists; it cannot create one — v2's drawings come from partkiln (§10.7) | ○ |
| 50 | `feature.parentComponent` — "the owning component of this feature"; for an extrude with `NewComponentFeatureOperation` the codegen finds the occurrence Fusion made as the one under the root whose `occurrence.component.entityToken` equals the feature's parent's | `ChamferFeature.htm` (the base Feature property, listed on every feature page read) | how a new-component extrude reports the `c{n}` it created | ○ |

Two facts the reference does NOT settle and the smoke must: which image
extensions `saveAsImageFile` writes (row 19), and the add-in folder on this
machine (`~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
per the KB, or any folder registered through Scripts and Add-Ins).

## 4. Design

### 4.1 The bridge add-in (`adapters/fusion/tee_bridge/TEE/TEE.py`, MIT)

- `run(context)`: register the custom event `tee.bridge.execute`, add the
  handler, start ONE daemon thread that binds `127.0.0.1:<port>` (default
  9881; `TEE_FUSION_PORT` env overrides) and accepts one NUL-framed JSON
  request per connection: `{"type": "execute", "code": ..., "strict_json":
  bool}` or `{"type": "ping"}`. `adsk.autoTerminate(False)` is not needed
  for an add-in (it stays resident by definition); `stop(context)` closes
  the listener and unregisters the event.
- The I/O thread never touches `adsk` beyond `fireCustomEvent`. It stores
  `(code, Event, slot)` under a uuid, fires the event with the uuid as
  `additionalInfo`, and waits on the Event (with a deadline). The handler,
  on the primary thread, pops the task, `exec`s the code in a namespace that
  carries a persistent `_tee` dict (the id map, §4.4) and a `result` dict,
  captures stdout/stderr, and sets the Event. Reply shapes are the Blender
  bridge's exactly: `{"status": "ok", "result": {...}}` /
  `{"status": "error", "message": "<traceback>"}` (+ optional stdout/stderr).
- Why exec and not declarative commands: Fusion's API IS Python, the
  primary-thread constraint makes any interpreter a queue-and-wait anyway,
  and FreeCAD's script-per-batch precedent keeps all `adsk` knowledge in the
  server's codegen where it is tested against a shim. The trust posture is
  the Blender bridge's: localhost only, not a sandbox, the escape hatch
  gated by `exec-code`.
- Not copied: the Blender bridge's `_IOLoop` is GPL-3.0-or-later (a Blender
  add-on must be); the Fusion add-in is a fresh, smaller MIT file.

### 4.2 The wire (`adapters/fusion/wire.py`)

`FusionWire(host, port, connect_timeout, call_timeout)` with `probe()` and
`execute(code, strict_json=True, timeout=None)` — the Blender wire's shape
and framing, its own codes: `fusion_unreachable` (fix: the add-in install
and start steps), `fusion_bridge_error` (the primary-thread traceback,
compacted), `fusion_bad_readback`. Per-call connections, fail fast.

### 4.3 Codegen (`adapters/fusion/codegen.py`) — one batch, one script, one JSON line

Same prelude/epilogue discipline as FreeCAD's: resolve the active design
(refuse `fusion_no_design` when `app.activeProduct` is not a Design),
apply ops in order, stop at the first failure with `{"error": {"op_index",
"message"}}`, else print `{"created", "modified", "deleted", "details"}`.
**Millimetres on the wire, centimetres inside**: every length is emitted as
`ValueInput.createByString("<n> mm")` (row 10) or divided by 10 for Point3D
sketch coordinates; every read-back multiplies cm by 10, cm² by 100, cm³ by
1000; mass stays kg. Angles are degrees on the wire (`"<n> deg"`).

| op | shape | Fusion calls (§3 rows) |
|---|---|---|
| `create sketch` | `{plane: XY\|XZ\|YZ, rects: [[x1,y1,x2,y2]...], circles: [[cx,cy,r]...]}` mm | 6, 7 |
| `create extrude` | `{sketch: id, profile: index\|"all", distance: mm, operation: join\|cut\|intersect\|new_body\|new_component}` | 8, 9, 10 |
| `create fillet` | `{body: id, radius: mm, edges: "all"}` | 11 |
| `create component` | `{}` — an empty component; also the generic fallback for any unknown kind (the kit contract's `object`), the kind kept in the component's name attribute | 12 |
| `create param` | `{value: "120 mm", units: "mm", comment}` | 13 |
| `set` | `{id, props: {name, expression (params / extrude distance), suppressed (features), visible (bodies, sketches)}}` | 13, 15 |
| `delete` | `{id}` — sketch, body, feature, occurrence, parameter | 7, 12, 13, 14, 15 |
| `param_set` | `{name, expression}` (partkiln's verb, same shape) | 13 |
| `import_file` | `{path, name}` — step/stp/f3d/igs/iges/sat into the root component | 18 |

Kinds not in v1 (named in §7): hole, chamfer, revolve, shell, sweep, loft,
sketch constraints and dimensions, joints.

### 4.4 Ids: short, prefixed, stable for the session

Fusion's stable identity is `entityToken` — long, opaque, resolvable with
`Design.findEntityByToken` (row 5). Every diff and summary row would pay for
it, so the add-in's persistent `_tee` namespace mints short ids on first
sight — `sk1`, `b1`, `f1`, `c1`, `param:width` — and keeps `id -> token`.
The listing re-derives the map (a token seen before keeps its id; a new
token gets the next id; a token that no longer resolves is dropped), so ids
are stable for the bridge's life and survive a rollback (the document is
the same document). A bridge restart renumbers; `tee_scene_summary
refresh=true` is the recovery, as for every lane.

### 4.5 Checkpoints: the timeline marker plus every parameter expression

Fusion exposes no scriptable undo. A **parametric** design has a timeline
(row 16): `snapshot()` records `{marker: timeline.markerPosition, count,
params: {name: expression for allParameters}}`; `restore()` sets the marker
back, calls `deleteAllAfterMarker()`, and re-applies every recorded
expression that still names a parameter. That restores: features, sketches,
bodies and components created after the checkpoint (deleted), and
dimensions edited since (expressions restored). It does NOT restore:
entities *deleted* after the checkpoint, or sketch geometry edited in
place — the adapter says so in `snapshot()`'s payload (`"restores":
"timeline+parameters"`) and in the lane guide. A **direct** design has no
timeline: `snapshot()` refuses `fusion_direct_design` with the fix (switch
the design to parametric, or accept no rollback).

### 4.6 Capture: the live viewport, budgeted

`viewport.fit()` then `saveAsImageFile(path, w, h)` (row 19) at the Blender
rungs (full, small, floor); the script tries `.jpg` and falls back to
`.png`, reporting which; a PNG is re-encoded to JPEG on the server (Pillow,
already a dependency of the extract extra) and the reply stays a bare
JPEG under `max_bytes` or refuses `capture_over_budget`. The viewport shows
whatever the owner has open — capture never changes the camera except
`fit()`.

### 4.7 Vocabulary (routing) and what the lane claims

```
LaneVocab(ops=("create", "set", "delete", "param_set", "import_file"),
          kinds=("sketch", "extrude", "fillet", "component", "param"),
          kind_optional=False,
          imports=("step", "stp", "f3d", "igs", "iges", "sat"),
          renders=True,
          purpose="Autodesk Fusion, live: parametric CAD in the open design; renders pixels")
```

The kinds tuple is what the lane CLAIMS for routing; the generic fallback
(any other word → a named empty component) exists for the kit contract and
is reachable with `adapter=fusion`. `test_lane_vocab.py` holds the tuple
equal to the codegen's dispatcher.

### 4.8 The `fu_*` long tail (tabled individually in `kernel/trust.py`)

| tool | capability | what |
|---|---|---|
| `fu_probe` | read-compute | bridge reachable, Fusion version, active document and design type, units, id-map size; never spawns anything |
| `fu_export` | write-artifacts | step, stl, obj, f3d, 3mf, iges, sat, usd via the ExportManager table (row 17); `of=` a body/component id or the root; `into=<lane\|auto>` lands the file through `handoff_import.land()` (units mm declared; glb is not a Fusion export, so a landing into Blender goes obj→scale from mm) |
| `fu_measure` | read-compute | volume mm³, area mm², mass kg, bbox mm, centre of mass mm for a body, a component or the root (rows 6, 14) |
| `fu_params` | read-scene | every parameter: name, expression, value (mm/deg/unitless), unit, user vs model |
| `fu_timeline` | read-scene | the history: index, name, kind, suppressed/rolled-back, health; the marker |
| `fu_execute_python` | exec-code | the escape hatch, denied unless granted; the same `result` dict convention |

Families: `("fu_", "fusion")` in `kernel/lanes.py`; no `fu_` family row in
the trust table (three writers among six — the `pk_` rule).

### 4.9 A router refinement: a lane whose application is not running is not a candidate

A68's `route_batch` intersects candidate lanes by vocabulary. Fusion is the
first lane whose vocabulary overlaps partkiln's on the words that matter
(`sketch`, `extrude`, `fillet`), so on `--adapter partkiln --adapter fusion`
every adapter-less `create sketch` would be ambiguous — even with Fusion
closed. The refinement: when several lanes take a batch and at least one of
them is connected, the disconnected ones drop out before the tie is judged
("route where the work can run"). With both live the batch is genuinely
ambiguous and refuses naming both, as A68 designed; `probe()` is only asked
when more than one lane took the batch, so the single-taker path pays
nothing. Tested in `test_lane_routing.py`.

### 4.10 CLI, config, manifest

`tee serve --adapter fusion [--fusion-port 9881]`; `.tee/config.toml`
`[fusion] port = 9881`; `ADAPTER_NAMES` gains `fusion`; `tee doctor` reports
the bridge. **The Desktop manifest is unchanged** until the lane has been
seen live (a decision, not an oversight: the manifest lists what the owner's
machine is known to serve).

## 5. Laws for this lane

1. Nothing in the codegen that is not in §3. A new call goes into the table
   with its page first.
2. Millimetres on the wire, always with the unit in the string; a read-back
   converts at the boundary, once.
3. The primary thread is the only thread that touches `adsk`; the I/O
   thread fires events and waits.
4. A checkpoint says what it restores; a refusal names the design type.
5. The owner's document is the owner's: no document is created, closed,
   saved or uploaded by the lane; exports and captures write to paths the
   caller names or the workdir.
6. Zero new always-loaded tools; every `fu_*` tool is tabled individually.
7. Nothing is claimed live until the Mac smoke ran; the shim proves the
   protocol and the codegen, not Fusion.

## 6. Phases (the script carries the acceptance)

P0 this document, the script, DECISIONS/PROGRESS. P1 the add-in and the
wire, with a protocol test that runs the add-in's framing and marshalling
against a stub executor. P2 codegen, adapter, the fake `adsk` shim that
`exec`s the generated scripts, the kit contract suite, the vocab test. P3
tools, tables, CLI, config, the router refinement, docs. P4 measured on the
shim (tokens per task against the script a model would otherwise write and
the listing it would read back), the Mac smoke procedure, PROGRESS,
CHANGELOG.

## 7. Deliberately not built

*(v1, 2026-09-06 morning)* Holes, chamfers, revolves, shells, sweeps, lofts;
sketch constraints and dimensions; joints; drawings and CAM; document
management; direct-modeling rollback; a seamkiln handoff target named
`fusion`; OBJ/STL import; the manifest change (§4.10).

*(after v2, §10)* Still not built, each for its named reason: shells, sweeps,
lofts, threads and tapped holes, sketch arcs and splines, joint origins,
as-built joints and motion links, rigid groups (one more row and one more
emitter each — the v2 additions are the proof that the shape holds);
drawings made BY Fusion (the API cannot, row 49) and the PDF export of a
drawing the owner has open (its rows are verified in 49; the emitter waits
for a smoke that can open a drawing); CAM; document management (Law 5);
direct-modeling rollback; OBJ/STL import (row 18); the manifest change
(§4.10, until the smoke).

## 8. Measured

### 8.1 On the shim (P4, 2026-09-06)

`benchmarks/run_benchmarks.py::run_fusion_scenario`, recorded in
`benchmarks/RESULTS.md` under "Fusion lane: sketch, extrude, fillet, measure
(A69)". The task: a 120 × 80 × 10 mm plate with a 2 mm fillet, then its
volume and bounding box. Both arms run on `tests/fixtures_fusion.py`'s fake
`adsk`: the scripts are the ones a live Fusion receives; only the geometry
is arithmetic.

| arm | tokens | calls |
|---|---:|---:|
| naive — the model writes the Fusion API script, runs it through an execute door, reads the design back as a listing | 8,833 | 2 |
| TEE — one `tee_batch`, its diff, one `fu_measure` | 270 | 2 |
| **saved** | **96.9%** | |

*(Re-measured in A70 P5. The A69 run reported 1,776 vs 254 tokens and
85.7%, with "a 140-token script": the runner had taken the first script the
wire saw — the checkpoint's snapshot program that `run_batch` runs before
the batch — for the batch script. The real script is what is counted now.)*

The compiled batch script is 4,282 tokens the model never reads; the diff
it reads instead is 147. Read-back: 96,000 mm³, bbox [120, 80, 10] mm — the
number the smoke must answer before the fillet (`docs/fusion-lane.md`,
step 3). The always-loaded surface stayed at 17 tools
(`tests/test_server_lint.py`); the lane adds zero wire tokens, joining
through the Adapter protocol and six `fu_*` virtual tools. The full suite on
the P3 tree: 1,579 passed, 66 skipped, 115 deselected.

What this measures and what it does not. The naive arm's script is the one
TEE compiles, which is the fairest stand-in: a model writing it by hand
spends more tokens and, on the retired `setDistanceExtent`, sometimes gets it
wrong, so the saving is a floor on that side. It measures nothing about
Fusion itself — latency, the event hop under load, which extensions
`saveAsImageFile` writes, the OBJ's actual unit — those are the smoke's.

### 8.3 v2 on the shim (A70 P5, 2026-09-06)

`run_fusion_v2_scenario` (RESULTS: "Fusion lane v2: a dimensioned bracket
with holes, a chamfer, a revolve and a joint"): a rectangle constrained and
dimensioned to `width` / `height` user parameters and extruded into its own
component, two Ø6.6 through holes on `+z`, a chamfer on that face's edges,
a post extruded into a second component, a pin revolved about x, and a
revolute joint between the two components — twelve ops in one batch.

| arm | tokens | calls |
|---|---:|---:|
| naive — the script, the execute door, the listing | 12,168 | 2 |
| TEE — one `tee_batch`, its diff, one `fu_measure` | 1,144 | 2 |
| **saved** | **90.6%** | |

Twelve ops made nineteen entities; the script is 6,582 tokens the model
never reads, the diff 629. The plate reads back 95,315.8 mm³ (96,000 less
two holes) in a [120, 80, 10] box — the dimensions drove the 100×50
rectangle to 120×80 before the extrude. The saving is lower than v1's
because the diff now carries nineteen rows a model would want (the joint's
motion, each hole's diameter and position, the sketch's constraint count);
it is still one round trip against a listing the naive arm must read in
full.

### 8.2 Live — the Mac smoke has not run

Every §3 row is ○ in its live column until the procedure in
`docs/fusion-lane.md` has run on the machine that has Fusion. The smoke fills
the column, answers §9, and decides the manifest (§4.10). Until then this
lane is verified against the reference and proven on the shim, and claimed
nowhere else.

## 9. Open questions for the smoke

1. Which extensions `saveAsImageFile` writes on the owner's build (jpg?
   png?) — the capture script reports which succeeded.
2. Whether `fireCustomEvent` is serviced while a modal dialog is up (the
   FreeCAD SI-B12 lesson) — the wire's call timeout is the guard, and
   `fusion_unreachable`'s fix names it.
3. The add-in folder on the owner's Mac, and whether `runOnStartup` is
   wanted (the manifest ships it `true`, as Autodesk's sample does).
4. *(v2)* A hole placed on a face with `setPositionByPoint`: is its default
   direction into the material, and which way does `setAllExtent(Positive…)`
   run? The codegen assumes "into the material" and exposes `flip`; the
   smoke's step 8 measures the volume after a through hole.
5. *(v2)* After `joints.add`, which occurrence Fusion moves, and what
   `fu_measure` of an occurrence reads afterwards (the shim moves nothing).
6. *(v2)* The unit each of IGES, SAT, 3MF and USD declares inside the file
   Fusion writes (the options carry none); `fu_export` declares `units:
   null` until the smoke has read them.
7. *(v2)* Whether `addTwoPointRectangle` adds horizontal/vertical
   constraints of its own (the page does not say); the sketch row's
   `constraints` count after step 7 answers it.

## 10. v2 (A70, 2026-09-06): the long tail becomes rows and emitters

**Owner directive (verbatim):** *"v2 should add holes, chamfers, revolves,
sketch constraints, joints, drawings or the iges/sat/3mf/usd exports, each of
which is one more verified row and one more emitter."*

Rows 31–49 were read before any emitter was written. One premise inverted on
the way: **the Fusion API cannot create a drawing** (row 49) — §10.7 says what
v2 does instead. Everything below keeps §4's shape: one batch, one script,
one diff; millimetres on the wire with the unit written; ids minted over
entityTokens; the shim executes the real scripts.

### 10.1 Sketch geometry gets addresses; constraints and dimensions become ops

- `create sketch` props grow `lines: [[x1, y1, x2, y2]]`, `points: [[x, y]]`,
  and optional inline `constraints` / `dims` lists (the shapes of the two ops
  below, minus `sketch`).
- Every piece of sketch geometry has a **sketch-local address**, minted in
  creation order and kept in the bridge's `_tee["subs"][<sketch id>]` map
  over entityTokens: `r0.bottom | top | left | right` (a rectangle's sides,
  **named by where their midpoints lie**, because row 38 leaves the line
  order unspecified — Law 8), `r0.bl | br | tl | tr` (its corners, likewise),
  `l0…` (explicit lines) with `.start` / `.end`, `c0…` (circles) with
  `.center`, `p0…` (explicit points), and `origin` (the sketch's projected
  origin point, row 38). An op names them as `"sk1/r0.bottom"`; inside the
  sketch op itself they are bare.
- `create constraint {sketch, type, of: [address…]}` — types and arity:
  horizontal / vertical (one line); parallel / perpendicular / collinear (two
  lines); equal / tangent (two curves); concentric (two circles); coincident
  (a point, then an entity); midpoint (a point, then a curve); symmetry (two
  entities, then the line). Row 40. A constraint is **not an entity**: no id,
  never `set`; the sketch row reports `constraints` (a count) and
  `constrained` (`isFullyConstrained`), and a rollback removes them with the
  sketch's later history.
- `create dimension {sketch, type, of, orientation?, expression?, text?,
  driving?}` — distance (two points; orientation aligned | horizontal |
  vertical), diameter / radius (one circle), angle (two lines). Rows 41–42. A
  dimension IS an entity, `dim1` (kind `dimension`, parent the sketch),
  reporting `expression`, `value` (mm or deg) and `driving`;
  `set dim1 {expression: "width"}` writes `parameter.expression` — the
  binding to a user parameter that makes a sketch parametric; `delete dim1`
  is `deleteMe()`. `text` is the label position in mm (default: beside the
  geometry); `driving` defaults to true.

### 10.2 Faces by direction; holes

- There are no face ids. A face is addressed by its **outward normal** on a
  body: `"+z"`, `"-z"`, `"+x"`, `"-x"`, `"+y"`, `"-y"`. The prelude's
  `_face(body, sel, at)` walks `body.faces`, keeps the planar ones
  (`geometry.surfaceType == PlaneSurfaceType`), takes each plane's normal
  flipped by `isParamReversed` (row 47), keeps the faces within a degree of
  the axis and picks the outermost along it — or, when `at` has three
  coordinates, the one whose plane passes nearest `at`. None →
  `fusion_no_face`, naming the directions the body does have.
- `create hole {body, face, at | point, diameter, depth | through, type?,
  cbore_diameter?, cbore_depth?, csink_diameter?, csink_angle?, flip?}` — `at`
  is `[u, v]` (the two world axes other than the normal's, in x-y-z order)
  or `[x, y, z]`, in mm; Fusion projects the point onto the face (row 32);
  `point: "sk2/p0"` places by a sketch point instead (row 32). `type` is
  simple (default), counterbore or countersink (row 31); `depth` →
  `setDistanceExtent`, `through: true` → `setAllExtent(Positive…)`; `flip`
  clears `isDefaultDirection` (row 33). The hole is a feature (`f{n}`, type
  HoleFeature) reporting `diameter_mm`, `position_mm` and `hole_type`; the
  body's row is marked modified with its new volume. What the reference does
  not settle is §9 item 4.

### 10.3 Chamfers, and an edge selector shared with fillets

- `create chamfer {body, distance, edges?}` — `createInput2()` and one
  `addEqualDistanceChamferEdgeSet(edges, "d mm", True)` (row 35; the retired
  `createInput` never appears and the shim raises on it). `edges` is `"all"`
  (default) or `{"face": "+z"}` — that face's edges (row 47). The same
  selector lands on `create fillet`, whose default stays "every edge".

### 10.4 Revolves

- `create revolve {sketch, axis, angle?, symmetric?, operation?, profile?}` —
  `axis` is `"x" | "y" | "z"` (the root's construction axes, row 37) or a
  sketch line address (`"sk1/l0"`, row 36); `angle` defaults to 360 and is
  written as `"<a> deg"`; `setAngleExtent(symmetric, angle)`. A profile that
  crosses its axis is Fusion's failure and comes back as one refusal.

### 10.5 Joints

- `create joint {one, two, motion, axis?, slide?, angle?, offset?, flip?}` —
  each side is `{component: "c1", face: "+z", body?: "b3"}` (the centre of a
  planar face of that occurrence's body, in occurrence context: the bodies
  under `occ.bRepBodies` are proxies already (row 12), and the geometry is
  `createByPlanarFace(face, None, CenterKeyPoint)` (row 44)), or
  `{component: "c1"}` (the occurrence's origin construction point through
  `createForAssemblyContext(occ)`, rows 37 and 47), or `{body: "b1", face:
  "+z"}` on the root. `motion` is rigid | revolute | slider | cylindrical |
  pin_slot | planar | ball (row 45); `axis` (x | y | z, default z) is the
  rotation axis, slide direction or plane normal as the motion needs, and
  pin_slot takes `slide` as well; ball uses pitch z and yaw x. `angle` (deg)
  and `offset` (mm) are written with their units; `flip` sets `isFlipped`.
- A joint is an entity `j{n}` (kind `joint`) reporting `motion`, `between`
  (the two occurrences' ids), `angle_deg`, `offset_mm`, `flipped` and
  `health`. `set j1 {angle, offset, suppressed, flipped, rotation (deg, a
  revolute or cylindrical joint), slide (mm, a slider)}` (row 46).
- Fusion moves an occurrence to satisfy a joint; the shim records the joint
  and moves nothing (§9 item 5).

### 10.6 Exports

`fu_export format=iges | sat | usd | 3mf` (row 48). iges/sat/usd export a
component or the root, so a body id is refused with the fix; 3mf takes a
body, an occurrence or a component. All four declare their units inside the
file, so `fu_export` answers `declares_units: true` and `units: null` with a
note — the receiver reads the file's own unit; `into=` still refuses when no
served lane imports the suffix.

### 10.7 Drawings: the API cannot make one; partkiln can

Row 49 is the finding. `fu_drawing {out, of?, name?, sheet?, standard?,
angle?, scale?, views?, dims?, hole_table?, formats?}` exports STEP from
Fusion into the lane's workdir, imports it into the served partkiln lane
(`pk_import`: fingerprint-named faces, the file's declared unit reported)
and writes the sheet with `pk_drawing` — every dimension READ from the model
(partkiln's Law 15), SVG / DXF / PDF. No partkiln lane served →
`partkiln_not_served`, fix `tee serve --adapter fusion --adapter partkiln`.
The import into partkiln's document is a scene write on that lane, decided
as one through `registry.require` (the A68 precedent for `land()`), so a
tainted task cannot reach it through a write-artifacts tool.

### 10.8 What the shim models, and what only the smoke can tell

The shim gains: sketch lines with shared endpoints, circles with centres,
points, constraints (counted; horizontal / vertical / coincident checked
against the geometry they name), dimensions whose parameter drives the
geometry **for rectangles and circles only** (Law 10); a box body's six
faces with normals, centroids, areas and edges; holes that subtract a
cylinder (plus the counterbore ring or the countersink frustum); chamfers
that touch nothing but the timeline; revolves by Pappus (the volume of a
profile of area A revolved through θ about an axis at distance d from its
centroid is θ·A·d); joints with motions, angle and offset parameters, rotation
and slide values; the four export constructors with their argument orders.
It does not solve a general sketch, move an occurrence for a joint, or know a
hole's live direction — §9 items 4–7 are the smoke's.

### 10.9 Laws added

8. A sub-entity is addressed by where it is (a rectangle's `bottom`), never
   by the order Fusion returned it.
9. A behaviour the reference does not settle (a hole's direction, which
   occurrence a joint moves) is an open question in §9 and a smoke step,
   never a guess written into the codegen as fact.
10. The shim solves rectangles and circles only; a dimension it cannot solve
    is recorded, not faked, and the test says which.
