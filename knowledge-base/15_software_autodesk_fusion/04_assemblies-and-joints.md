---
id: fusion.assemblies
title: Assemblies, components and joints in Fusion
domain: 15_software_autodesk_fusion
tags: [fusion, assembly, components, bodies, joints, as-built-joints, rigid-group, contact-sets, interference, motion-study]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release."
unit_system: metric
sources:
  - {title: "Fusion API Reference — Component object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Occurrences", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Occurrences.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — JointGeometry", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/JointGeometry.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — JointTypes enum", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/JointTypes.htm", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Design object", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.modelling, fusion.joinery_workflow, fusion.drawings, fusion.api]
---

# Assemblies, components and joints in Fusion

**Summary.** Fusion collapses "part file" and "assembly file" into one document: a design has a **root component** which can contain **bodies**, **sketches**, **features** and **occurrences** of other components, recursively. That flexibility is why beginners build a whole kitchen as twenty bodies in the root component and then discover they cannot make a parts list, cannot move a cabinet, cannot export a single panel, and cannot make a drawing view of one door. The distinction between a **body** and a **component** is the single most consequential structural decision in a Fusion project, and it is almost impossible to fix retroactively at scale.

## Key facts

- **Body** = a lump of geometry (`BRepBody`). Has no origin of its own, cannot be jointed, does not appear in a parts list, cannot be individually exported as a component.
- **Component** = a container with its own **origin and construction planes**, its own sketches, features, bodies, joints and sub-components. Appears in the parts list. Can be jointed. Can carry `name`, `partNumber`, `description`, `material`.
- **Occurrence** = an *instance* of a component in an assembly. Twelve identical drawer boxes = one component, twelve occurrences.
- Component creation: **Design workspace → Assemble → New Component** (empty, or from selected bodies).
- API: `root.occurrences.addNewComponent(transform)`, `addExistingComponent`, `addNewComponentCopy`, `addNewExternalComponent` (X-Ref), `addFromConfiguration`, `addByInsert`.
- **Joint types** (`adsk.fusion.JointTypes`): `RigidJointType`, `RevoluteJointType`, `SliderJointType`, `CylindricalJointType`, `PinSlotJointType`, `PlanarJointType`, `BallJointType`, `InferredJointType`.
- Interference: `Design.createInterferenceInput(...)` then `Design.analyzeInterference(...)`; UI at **Inspect → Interference**.
- Contact: `Design.contactSets`, `Design.isContactAnalysisEnabled`, `Design.isContactSetAnalysis`.

## Bodies vs components — and why misuse breaks projects

Model everything as bodies in the root component and you lose, in order of how much it will hurt:

1. **No parts list.** The Drawing workspace's Parts List enumerates *components*, not bodies. A body-only model cannot produce a bill of materials or a balloon-referenced shop drawing. (See `07_drawings-and-documentation.md`.)
2. **No cut list.** Every cut-list script and add-in walks `allOccurrences` and reads component name, part number and bounding box. Bodies are anonymous.
3. **No joints.** `Joints` connect components. Bodies can only be moved by a Move/Copy feature, which is a timeline operation, not an assembly relationship.
4. **No isolated editing.** Activating a component (double-click it in the browser) scopes new sketches and features to it. In a body-only model every new sketch lands in the root and every feature can accidentally consume the wrong profile.
5. **Export is all-or-nothing.** `Component.saveCopyAs` and per-component STEP/DXF export need components.
6. **CAM setups get messy.** A Manufacture setup selects a model; per-part setups are cleanest when each part is a component.

### The rule for joinery

> **One physical piece that will be cut, machined and handled = one component.** One carcass = one component containing the panel components. One kitchen = one assembly of carcass components.

A base unit therefore looks like:

```
Kitchen (root)
├─ Base unit 600 (component)      <- occurrence 1..n
│   ├─ Side L (component)  ─ body: 18 mm panel
│   ├─ Side R (component)
│   ├─ Bottom (component)
│   ├─ Top rail front (component)
│   ├─ Top rail back (component)
│   ├─ Back (component)   ─ body: 6 mm panel
│   ├─ Shelf (component)  <- 2 occurrences
│   └─ Door (component)   <- 2 occurrences
├─ Base unit 900 (component)
└─ Worktop (component)
```

Names should be what the shop calls them. `partNumber` should be your cut-list code. `description` should carry the material and edging spec — those three fields flow straight into the parts list.

**Converting bodies to components later:** select the bodies in the browser → right-click → **Create Components from Bodies**. This works, but the resulting components have their origins at the root origin (not at the part), and any existing timeline features that referenced the bodies now cross component boundaries. It is a rescue, not a plan.

## Joints vs as-built joints

Both create an assembly relationship. They differ in whether they *move* anything.

**Joint** (**Assemble → Joint**, `J`): you pick a **joint origin** on component 1 and a joint origin on component 2; Fusion **moves component 2 to align them** and then constrains the remaining degrees of freedom according to the joint type. Offsets, angle and flip are parameters of the joint and appear in Change Parameters.

Use Joint when a part is modelled in a convenient place and needs to be positioned — e.g. a drawer box modelled at the origin, jointed into the carcass.

**As-built Joint** (**Assemble → As-built Joint**): you pick two components that are **already in the correct relative position** and specify the joint type and, for moving joints, the axis geometry. Nothing moves; the relationship is simply recorded.

Use As-built Joint when the parts were modelled in place — which is the normal case for a carcass built top-down from a skeleton sketch. **For sheet-goods joinery, as-built joints are usually the right answer for the fixed panels** (all `RigidJointType`), and real joints for the moving parts (doors, drawers).

Both appear under the **Joints** folder in the browser. `Component.joints`, `Component.asBuiltJoints`, `Component.allJoints`, `Component.allAsBuiltJoints` in the API.

> ⚠️ A common failure: applying a Joint to a component that is already positioned. Fusion moves it, you undo, the joint remains but the geometry has shifted. Check the position after every joint, and prefer As-built for in-place parts.

## Joint origins

A **joint origin** is a named, reusable point-plus-orientation on a component. Create with **Assemble → Joint Origin**. It has:

- a **position** — from a face centre, edge midpoint, vertex, sketch point, or between two faces
- an **orientation** — X, Y, Z axes you can flip and rotate
- **offset** parameters in X, Y, Z and an angle

Why bother, when Joint can snap to geometry directly? Because **a joint that snaps to a model face is bound to that face's internal token**. Delete and re-make the face and the joint fails. A joint origin is a first-class entity you can re-attach in one place, and every joint referencing it survives.

**For any component that will be jointed more than once, or that will be revised, define explicit joint origins.** For hardware — a hinge, a drawer runner, a leg — the joint origin *is* the mounting datum, and it should sit exactly where the manufacturer's drilling dimension says it does (see `05_sheet-goods-and-joinery-workflow.md`).

The API mirrors this: `JointGeometry` has static constructors `createByPlanarFace`, `createByNonPlanarFace`, `createByPoint`, `createByCurve`, `createByBetweenTwoPlanes`, `createByProfile`, `createByCylinderOrConeFace`, `createBySphereFace`, `createByTorusFace`, `createBySplineFace`, `createByTangentFaceEdge`, `createByTwoEdgeIntersection`.

## Joint types and motion

| Type | Degrees of freedom | Joinery example |
|---|---|---|
| `RigidJointType` | 0 | Every fixed panel in a carcass; a fixed shelf |
| `RevoluteJointType` | 1 rotation | **A door on its hinge line**; a flap-down desk front |
| `SliderJointType` | 1 translation | **A drawer on its runners**; a sliding wardrobe door |
| `CylindricalJointType` | 1 rotation + 1 translation along the same axis | A rotating/sliding pole |
| `PinSlotJointType` | 1 rotation + 1 translation on different axes | A pivot in a slot; a lift-up flap mechanism approximation |
| `PlanarJointType` | 2 translations + 1 rotation in a plane | A castor foot on the floor; a loose item on a shelf |
| `BallJointType` | 3 rotations | Rare in furniture |
| `InferredJointType` | Fusion guesses from geometry | Convenience only |

**Joint limits** (in the joint's dialog, "Motion" section) constrain the range: a door hinge limited to 0–110° reproduces a Blum clip-top's opening angle and lets you check that the door clears the adjacent worktop return. Set them; they are the cheapest clash check you will ever do.

**Drive Joints** (**Assemble → Drive Joints**) animates a single joint through its range interactively. Use it to check a drawer's full extension against a wall or a corner unit.

**Motion Link** (`Component.motionLinks`) ties two joints together with a ratio — e.g. a bifold door where the second leaf rotates twice the first.

## Rigid groups

**Assemble → Rigid Group** locks a set of components together as one rigid body for motion purposes, without creating pairwise joints. `Component.rigidGroups`, `Component.allRigidGroups`.

This is the pragmatic answer to "I have a 22-panel carcass and I do not want 21 as-built rigid joints." Select all the fixed panels of a carcass → Rigid Group. Then joint the *carcass* to the next carcass, and joint only the doors and drawers individually.

Caveat: a rigid group is not a hierarchy. It does not group the parts in the browser, does not affect the parts list, and does not survive a component being deleted cleanly. Use component nesting for structure and rigid groups only for motion.

## Contact sets

By default Fusion's joint motion ignores geometry — a drawer will happily slide through the back of a carcass. **Contact** makes bodies collide.

- **Assemble → Enable Contact Sets** turns the system on.
- **Assemble → New Contact Set** defines a specific pair or group of components that should collide.
- **Enable All Contact** makes everything collide — correct, and very slow on a kitchen.

API: `Design.contactSets`, `Design.isContactAnalysisEnabled`, `Design.isContactSetAnalysis` ("gets/sets contact analysis using sets versus all bodies").

**Practical use:** a contact set between a drawer box and the carcass sides proves the box clears the runners; a contact set between a door and the adjacent carcass proves the hinge opening angle is achievable. Enable contact only for the pair under test, then turn it off — contact analysis is the main reason a Fusion assembly becomes unusably slow.

## Motion study

**Assemble → Motion Study** builds a timeline of joint positions and plays the assembly through them, plotting joint values against steps. It is the tool for demonstrating a mechanism to a client (a pull-out larder, a lift-up flap) and for capturing the exploded/animated views used in `07_drawings-and-documentation.md`.

For furniture it is a presentation tool more than an engineering one. The engineering questions — does it fit, does it clash — are answered by joint limits, contact sets and interference.

## Interference detection

**Inspect → Interference**. Select components or bodies, choose whether to include coincident faces, compute. Fusion lists interfering pairs with the interference volume, and can create the interference volumes as bodies.

API: `design.createInterferenceInput(entities)` → set options → `design.analyzeInterference(input)`.

For joinery this catches:

- A dado cut into a panel that is 1 mm too shallow for the shelf
- A hinge cup bore that breaks through a 16 mm door
- Two cabinets whose scribes overlap
- A drawer runner fouling a carcass rebate

**Include coincident faces = off** for normal checking, or every butted panel reports as touching. Turn it **on** deliberately when you want to verify that mating faces really are coincident and not 0.2 mm apart.

## Structuring a furniture assembly correctly — a checklist

1. **Top-down skeleton.** Model the room or the run envelope as a skeleton sketch in the root component. Every cabinet's position derives from it.
2. **One component per manufactured part**, named as the shop names it, with `partNumber` and `description` filled in.
3. **One component per assembly unit** (a base unit, a wall unit), containing its parts.
4. **Doors, drawer fronts and shelves are components with multiple occurrences** where they are identical — not copies. An occurrence costs nothing; a copy doubles the edit work.
5. **Use `addNewExternalComponent` / Insert → Insert Derive** for parts shared across projects (a standard drawer box, a standard plinth section). External components are separate documents referenced in, so a fix propagates to every project.
6. **Hardware from the supplier's STEP** goes in as a component, direct-modelled, marked as a purchased part in `description`, and jointed by a joint origin at the manufacturer's datum.
7. **Rigid-group the fixed panels; joint the moving parts** with limits.
8. **Set physical material on every component.** It drives mass in the parts list and, more importantly, forces you to decide the material.
9. **Run Inspect → Interference before every issue of drawings.**
10. **Never let a feature in one component reference geometry in another** unless you mean it. Cross-component references are legal, are recorded as an "inter-component reference" in the browser, and are the reason an innocent edit to cabinet 3 breaks cabinet 7. Prefer shared user parameters.

## API sketch: build an assembly

```python
import adsk.core, adsk.fusion, traceback

def new_component(parent: adsk.fusion.Component, name: str,
                  x_mm=0.0, y_mm=0.0, z_mm=0.0) -> adsk.fusion.Occurrence:
    """Create a child component at an offset. API units are centimetres."""
    m = adsk.core.Matrix3D.create()
    m.translation = adsk.core.Vector3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0)
    occ = parent.occurrences.addNewComponent(m)
    occ.component.name = name
    return occ

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        unit = new_component(root, 'Base unit 600')
        for name, x in (('Side L', 0), ('Side R', 582)):
            occ = new_component(unit.component, name, x_mm=x)
            occ.component.partNumber = 'BU600-' + name.replace(' ', '')
            occ.component.description = '18 mm MFC, 1 long edge banded'

        # Report the structure.
        lines = ['{}  ({} occurrences)'.format(o.component.name,
                 o.component.occurrences.count)
                 for o in root.allOccurrences]
        ui.messageBox('\n'.join(lines) or 'empty')
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

`Component.allOccurrences` "returns all of the occurrences in the assembly regardless of their level", which is what a cut-list walker wants; `Component.occurrences` returns only the immediate children.

## Sources

- [Fusion API Reference — Component object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Component.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Occurrences](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Occurrences.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — JointGeometry](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/JointGeometry.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — JointTypes enum](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/JointTypes.htm) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Design object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm) — Autodesk, accessed 2026-08-25

## Open questions

- Exact ribbon labels under the Assemble panel ("Enable Contact Sets" vs "Enable All Contact") were not verified against a scraped Autodesk help page. `needs-verification` on wording.
- Whether Motion Study results can be exported as data (joint value tables) via the API.
- Behaviour of rigid groups when a member component is replaced by a configuration row.

