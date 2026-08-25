---
id: fusion.sketching
title: Sketching, constraints and design intent in Fusion
domain: 15_software_autodesk_fusion
tags: [fusion, sketch, constraints, solver, parametric, design-intent, projection, construction-geometry]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release. Menu paths are for the current Design workspace ribbon."
unit_system: metric
sources:
  - {title: "Fusion API Reference — Sketch object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Sketch.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — SketchLines", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/SketchLines.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "SketchChecker_Python", url: "https://github.com/AutodeskFusion360/SketchChecker_Python", publisher: "Autodesk (GitHub)", accessed: 2026-08-25}
  - {title: "Fusion API Reference — SketchDimensions.addDistanceDimension", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/SketchDimensions_addDistanceDimension.htm", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.modelling, fusion.api, fusion.joinery_workflow]
---

# Sketching, constraints and design intent in Fusion

**Summary.** Everything parametric in Fusion rests on the sketch solver. A sketch is a set of 2D curves on a plane, plus geometric constraints (relationships) and dimensional constraints (numbers), which the solver resolves into a unique position. Sketches that are under-constrained will move unpredictably when a parameter changes; sketches that are over-constrained refuse to solve; and sketches whose constraints reference the wrong geometry break silently when upstream features are edited. For joinery work — where a carcass must survive `Width` going from 600 to 900 mm without exploding — the sketching discipline in this file is what separates a model you can drive from a data file from a model you rebuild by hand every time.

## Key facts

- A sketch is created on a **construction plane**, a **planar face**, or an **origin plane** (XY, XZ, YZ under the Origin folder in the browser).
- Sketch curve types: line, arc (3-point, centre-point, tangent), circle (centre, 2-point, 3-point, 2-tangent, 3-tangent), ellipse, spline (fit-point and control-point), conic curve, slot (5 variants), polygon (circumscribed, inscribed, edge), rectangle (2-point, 3-point, centre), point, text.
- Geometric constraints available: **Horizontal/Vertical, Coincident, Tangent, Equal, Parallel, Perpendicular, Fix/Unfix, Midpoint, Concentric, Collinear, Symmetry, Curvature (G2), Smooth**.
- Dimensional constraint: one command, **Sketch Dimension** (shortcut `D`), which infers the dimension type from what you pick.
- A **fully constrained** sketch is drawn in a distinct colour (black by default; blue = under-constrained) and its geometry cannot be dragged.
- Internal API units for sketch geometry are **centimetres** (`Point3D(9.0, 0, 0)` is 90 mm).

## Sketch planes: where a sketch lives, and why it matters

The plane you choose is a permanent dependency. Three options, in descending order of robustness:

1. **An origin plane** (XY / XZ / YZ). Never moves, never fails. Use for the base sketch of any component.
2. **A construction plane** created from a parametric input — offset from a plane, at an angle, through two edges, tangent to a face, midplane between two faces. Robust *if* the input it references is robust.
3. **A planar face of an existing body.** Convenient and dangerous. If a later edit removes or resurfaces that face, the sketch is orphaned and everything downstream fails. This is the single commonest cause of "my model exploded" in Fusion.

**Rule for joinery models: base sketches on origin planes and offset construction planes driven by user parameters, not on model faces.** A cabinet side panel sketched on `XZ` and extruded by `-BoardThickness` will survive any change to the carcass. The same sketch placed on the inner face of the opposite side will not survive that side being deleted and re-made.

Menu: **Design workspace → Construct → Offset Plane / Plane at Angle / Tangent Plane / Midplane / Plane Through Two Edges / Plane Through Three Points / Plane Through Point at Angle / Plane Along Path.**

## Geometric constraints and how the solver behaves

Fusion uses a variational sketch solver: it takes the curves' current positions as a starting guess and iterates to a state satisfying all constraints. Consequences you must internalise:

**Constraints have no order.** Unlike features in the timeline, constraints are a simultaneous system. Adding one late can flip geometry that was already settled. If a rectangle inverts when you add a dimension, drag it roughly into the intended shape *first*, then dimension.

**The solver picks the nearest solution, not the intended one.** A tangent constraint between a line and a circle has two solutions; the solver takes the one closer to the current sketch state. When a parameter change moves geometry a long way, the solver can jump to the other branch. Symptom: a fillet flips to the wrong side at `Width = 1200` but is fine at `Width = 600`. Cure: constrain more tightly, or add a symmetry/collinear constraint that removes the ambiguity.

**Auto-constraints are applied while you draw.** Fusion infers horizontal, vertical, coincident, tangent and perpendicular from cursor behaviour. This is fast and it is also how unwanted constraints get in. Hold `Ctrl` (Windows) / `Cmd` (macOS) while drawing to suppress inference. Turn on **Sketch Palette → Show Constraints** to see what you actually got.

**Over-constrained sketches are rejected, not resolved.** Fusion will tell you the constraint would over-constrain and refuse. It does *not* tell you which existing constraint conflicts — you must find it. Practical method: switch on constraint display, delete the suspect dimension, add the new one, then re-add.

**"Fix" is an anti-pattern.** The Fix/Unfix constraint pins geometry to absolute coordinates. It is the quickest way to make a blue sketch black and the quickest way to build a model that will not scale. Use it only for genuinely fixed datums (e.g. the outer corner of a worktop at the origin).

## Dimensional constraints

The single **Sketch Dimension** command (`D`) produces:

- Linear (horizontal, vertical or aligned, chosen by cursor position after picking)
- Diameter (pick a circle), radius (pick an arc)
- Angular (pick two lines)
- Distance between a point and a line, or two parallel lines

Type an **expression**, not a number, wherever the value is derived: `CarcassWidth - 2 * BoardThickness`, `ShelfPitch * 3`, `HingeInset + 5 mm`. Expressions are what make the model driveable. Fusion's expression language supports `+ - * / ^`, parentheses, `sin cos tan asin acos atan`, `sqrt`, `abs`, `min`, `max`, `PI`, and unit suffixes (`mm`, `cm`, `in`, `deg`, `rad`).

Units in expressions are explicit and mixable: `18 mm + 0.5 in` is valid. If you omit units, the document's default length unit is assumed — set it once at **Document Settings → Units** in the browser, and set it to **mm** for joinery.

## Fully constrained vs under-constrained

A fully constrained sketch has zero degrees of freedom: every curve endpoint is determined by constraints and dimensions relative to the origin or to projected geometry. Fusion shows the state in the **Sketch Palette** and colours fully constrained curves differently.

**Should every sketch be fully constrained?** For production joinery models: yes, with one exception. The cost of a partially constrained sketch is that a parameter change can move geometry in a way you did not intend, and you will not notice until the cut list is wrong. The exception is genuinely free-form profiles (a curved reception desk front) where full constraint is either impossible or so laborious it defeats the purpose; there, isolate the free-form sketch into its own component and treat it as a fixed input.

Diagnostic habit: after building a sketch, drag every curve. If nothing moves, it is fully constrained. Autodesk publishes a **SketchChecker** sample add-in that "checks the currently active sketch for curves with open ends" — open ends are the other silent killer, because a profile with a 0.001 mm gap will not form a closed region and Extrude will find no profile.

## Construction geometry

Toggle any sketch curve to construction with the **Normal/Construction** button in the Sketch Palette (or `X`). Construction geometry:

- does not form profiles, so it never confuses Extrude
- is fully constrainable and dimensionable
- shows as a dashed line

Uses in joinery models:

- **Centrelines** for symmetry constraints — draw a construction line on the sketch's axis of symmetry, then apply Symmetry between mirrored features. This halves the number of dimensions and makes the sketch behave properly under parameter change.
- **A construction rectangle representing the overall carcass envelope**, dimensioned to `Width` × `Height`, with the real geometry constrained to it. Change the two dimensions and everything follows.
- **Hole pitch lines** for the 32 mm system: a construction line from the reference edge, dimensioned `FirstHoleOffset`, with a linear sketch pattern of points at `32 mm` spacing.
- **Axes for Revolve**, which need a line but must not be part of the profile.

## Projection and reference geometry

**Create → Project/Include → Project** (`P`) copies edges, faces or sketch curves from elsewhere into the active sketch as reference curves. Related commands in the same flyout: **Intersect** (curves where a body crosses the sketch plane), **Include 3D Geometry**, **Project to Surface**.

Projected curves are **associative by default**: change the source and the projection updates. This is powerful and it is the second-commonest source of broken models, because it creates a dependency on a specific edge that a later feature may destroy. Fusion identifies edges by an internal token; delete and re-create the parent feature and the token changes.

Rules that hold up in practice:

- **Project the origin planes and construction geometry freely.** They are stable.
- **Project a body edge only when the relationship is genuinely geometric** — e.g. a shelf front edge that must always follow the carcass front, whatever the carcass depth.
- **Never project across components** if you can instead reference a shared user parameter. `ShelfWidth = CarcassWidth - 2*BoardThickness` is a far more robust statement of intent than projecting the inner faces of the two side panels.
- If a projection must cross components, do it deliberately and document it in the component description. See `04_assemblies-and-joints.md` on the dangers of inter-component references.
- The **"Project geometry" link icon** in the browser and the `isLinked`/`breakLink` behaviour let you sever the association if you want a frozen copy.

## Design intent: the question every sketch answers

"Design intent" is a real engineering concept and not marketing. It is the answer to: *when this thing changes, what should follow, and what should stay put?*

For a kitchen base unit:

- The **carcass width** is the driver. Rails, shelves and the back all follow it.
- The **board thickness** is a driver. Every rebate, dado and internal dimension follows it. Never type `18` anywhere — type `BoardThickness`.
- The **plinth height** is independent of carcass height; the two must not be chained.
- The **32 mm hole line** is referenced from the *front* edge and the *bottom* of the carcass — that is how the drilling machine works, so that is how the model must be dimensioned. Dimension from the datum the shop uses.
- The **door gap** is a design decision, not a consequence: `DoorGap = 3 mm` as a user parameter, and door width = `(CarcassWidth - 3*DoorGap)/2` for a pair.

Encode that in the dimension scheme. A dimension chain that runs `left side → shelf → right side` will accumulate; a scheme that dimensions everything from a single datum edge will not. **Prefer baseline dimensioning from a datum over chained dimensioning**, for the same reason a joiner sets out from one face and one edge.

## Best practice checklist for sketches that survive parameter changes

1. **One sketch, one purpose.** Do not build the whole cabinet in one sketch. A sketch that produces one extrude is trivially editable; a sketch feeding six features is a liability.
2. **Sketch on origin planes and parametric construction planes.**
3. **Start at the origin.** Constrain one point of the sketch to the origin (or to a projected origin point) so the sketch cannot float.
4. **Use a construction centreline plus Symmetry** wherever the part is symmetric.
5. **Name every driving dimension** — click the dimension, and in the Change Parameters dialog give it a real name (`d17` is not a name). See `03_modelling-and-parameters.md`.
6. **Type expressions, not numbers**, for anything derived.
7. **Fully constrain, then drag-test.**
8. **Close every profile.** No open ends, no duplicate overlapping lines. Run a sketch checker if in doubt.
9. **Avoid `Fix`.** Avoid projecting model faces. Avoid cross-component projection.
10. **Test the extremes.** Before you trust a parametric cabinet, set `Width` to its minimum and maximum and recompute (**Modify → Compute All**). Most breakage appears at the extremes, not the nominal.
11. **Keep sketch curve counts low.** Hundreds of curves in one sketch make the solver slow and constraint diagnosis impossible. Pattern in 3D (`Create → Pattern → Rectangular Pattern` on a feature) rather than sketching 40 shelf-pin holes.

## Doing it from the API

The sketch object model is direct. A minimal fully-dimensioned rectangle, in Python (note: **centimetres**):

```python
import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # A named user parameter drives the sketch.
        params = design.userParameters
        if not params.itemByName('PanelWidth'):
            params.add('PanelWidth',
                       adsk.core.ValueInput.createByString('600 mm'),
                       'mm', 'Carcass panel width')

        sk = root.sketches.add(root.xYConstructionPlane)
        lines = sk.sketchCurves.sketchLines
        rect = lines.addTwoPointRectangle(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(60, 40, 0))   # 600 x 400 mm, in cm

        # Constrain the lower-left corner to the sketch origin.
        cons = sk.geometricConstraints
        cons.addCoincident(rect.item(0).startSketchPoint, sk.originPoint)

        # Dimension the horizontal line to the user parameter.
        dims = sk.sketchDimensions
        d = dims.addDistanceDimension(
            rect.item(0).startSketchPoint,
            rect.item(0).endSketchPoint,
            adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
            adsk.core.Point3D.create(30, -5, 0))
        d.parameter.expression = 'PanelWidth'

        ui.messageBox('Fully constrained: {}'.format(sk.isFullyConstrained))
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`Sketch.isFullyConstrained` is the programmatic version of the drag test and is the right assertion to put in an automated model-quality check. See `09_api-and-automation.md` for the full object model, and note that `SketchLines.addTwoPointRectangle` "creates four sketch lines representing a rectangle where the two points are the opposing corners" — it returns a collection of four lines, not a single object.

## Sources

- [Fusion API Reference — SketchLines](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/SketchLines.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — SketchDimensions.addDistanceDimension](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/SketchDimensions_addDistanceDimension.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — DimensionOrientations enum](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/DimensionOrientations.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference index](https://autodeskfusion360.github.io/FusionAPIReference/) — Autodesk, accessed 2026-08-25
- [SketchChecker_Python sample add-in](https://github.com/AutodeskFusion360/SketchChecker_Python) — Autodesk on GitHub, accessed 2026-08-25
- [Fusion API and Scripts forum](https://forums.autodesk.com/t5/fusion-api-and-scripts/bd-p/22) — Autodesk, accessed 2026-08-25

## Open questions

- The exact ribbon labels for the Project/Include flyout and the Sketch Palette options were not verified against a live Autodesk help page (help.autodesk.com renders client-side and could not be scraped on 2026-08-25). They are stated from working knowledge; confirm in the application. `needs-verification` on labels, not on behaviour.

