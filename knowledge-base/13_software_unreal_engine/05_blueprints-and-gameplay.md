---
id: ue.blueprints
title: Blueprints and gameplay scripting for archviz
domain: software_unreal_engine
tags: [blueprint, visual-scripting, construction-script, event-graph, macro, function, interface, event-dispatcher, casting, umg, widget, material-switcher, configurator, measurement-tool]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8; Blueprint fundamentals unchanged since UE4."
sources:
  - {title: "Blueprints Visual Scripting", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blueprint Communication Usage", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-communication-usage-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Creating User Interfaces with UMG and Slate", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-user-interfaces-with-umg-and-slate-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Editor Utility Widgets", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/editor-utility-widgets-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.core_concepts, ue.archviz_workflow, ue.python_automation, ue.cpp_extension]
---

# Blueprints and gameplay scripting for archviz

**Summary.** Blueprint is Unreal's node-based visual scripting system. It defines object-oriented classes in the engine, gives designers access to essentially the whole toolset normally reserved for programmers, and — through Blueprint markup in C++ — lets programmers build systems that designers extend. For archviz it is the right tool for every piece of runtime interactivity: door opening, material switching, measurement, room navigation, UI. This file covers graph types, variables, control flow, the functions/macros/events distinction, the Construction Script, the four communication patterns, the archviz interactions you will actually build, UMG, and the honest signals that it is time to move to C++.

## Key facts

| Concept | Summary |
|---|---|
| Blueprint Class | An asset deriving from a `UObject`/`AActor` class, compiled to bytecode |
| Level Blueprint | One per level; direct references to level Actors; no reuse |
| Graph types | Event Graph, Function graph, Macro graph, Construction Script, Interface graph |
| Construction Script | Runs in the editor whenever a property changes or the Actor moves, and on spawn |
| Event Graph | Runs at runtime only |
| Communication patterns | Direct reference, Casting, Blueprint Interface, Event Dispatcher |
| UI framework | UMG (Widget Blueprints, `WBP_`), built on Slate |
| Editor-only Blueprints | Editor Utility Blueprint, Editor Utility Widget — these can execute Python |
| Compilation | Blueprint → bytecode run by a VM; roughly an order of magnitude slower per node than C++ |

## Blueprint types

- **Blueprint Class** (`BP_`) — the workhorse. Derives from Actor, Pawn, Character, Player Controller, Game Mode, Actor Component, or any `UObject`-derived C++ class you expose. Reusable, instanceable, self-contained.
- **Level Blueprint** — one per level, opened via `Blueprints > Open Level Blueprint`. Holds direct references to Actors placed in that level. Convenient and non-reusable; keep it thin. In an archviz project it is a reasonable place for "this specific level's start-up sequence" and nothing else.
- **Blueprint Interface** (`BI_`) — a set of function signatures with no implementation.
- **Blueprint Macro Library** — a collection of macros, shared across Blueprints.
- **Blueprint Function Library** — a collection of static functions, callable from anywhere.
- **Widget Blueprint** (`WBP_`) — UMG UI.
- **Editor Utility Blueprint / Editor Utility Widget** — editor-only. The only Blueprints that can run Python nodes.
- **Data-only Blueprint** — a Blueprint with no graph logic, just overridden defaults. Cheap. A whole furniture library can be data-only Blueprints of one parent.

## Variables and types

Blueprint variables have a **Type**, a **Container Type** (single, Array, Set, Map) and a set of flags:

- **Instance Editable** — exposed on placed instances in the details panel. This is what makes a Blueprint parametric for an artist.
- **Blueprint Read Only**
- **Expose on Spawn** — appears as a pin on `Spawn Actor from Class`
- **Private**
- **Category** — organises the details panel. Use it; a fifteen-variable configurator Blueprint with no categories is unusable.

Types you will actually use in archviz: `Float`/`Double`, `Integer`, `Boolean`, `String`, `Text` (localisable — use this for anything shown to a user), `Name`, `Vector`, `Rotator`, `Transform`, `LinearColor`, object references (`Static Mesh`, `Material Interface`, `Actor`, `Texture 2D`), class references (`Class` pins, for `Spawn Actor from Class`), soft object/class references (load on demand — important for a configurator with many options), enums (`E_`), and structs (`F_`).

**Data Tables** (`DT_`) driven by a struct are the correct home for a finishes schedule, a room schedule or an option list. Author the CSV outside Unreal, reimport when it changes, and let a Blueprint read rows by name. This is also the natural bridge to Python-driven level generation (file `06`).

## Flow control

`Branch` (if), `Sequence` (do A then B then C from one exec pulse), `ForEachLoop`, `ForLoop`, `WhileLoop`, `Do Once`, `Do N`, `Gate`, `MultiGate`, `FlipFlop`, `Switch on Int/String/Enum`, `Select` (a value-level ternary), `IsValid`, `Delay`, `Retriggerable Delay`, `Timeline`.

**`Timeline`** deserves a callout: it is the standard mechanism for any animated transition — a door swinging, a curtain drawing, a camera easing between viewpoints, a material parameter blending. Add a float track, set a curve (ease in/out), drive the update pin into `Lerp` or `Set Relative Rotation`. Nearly every archviz interaction is a Timeline plus a `Lerp`.

`Delay` does not work inside Functions — only in Event Graphs and Macros. This trips people constantly.

## Functions vs Macros vs Events

| | Function | Macro | Event |
|---|---|---|---|
| Own graph | Yes | Yes | No — lives in the Event Graph |
| Return values | Yes | Yes (multiple exec outputs) | No |
| Multiple exec outputs | No | Yes | — |
| Latent nodes (`Delay`, `Timeline`) | **No** | Yes | Yes |
| Local variables | Yes | No | Uses Blueprint variables |
| Overridable in child Blueprints | Yes | No | Yes (via Event override) |
| Callable from other Blueprints | Yes (if public) | No (only within its library scope) | Yes (via `Call Function`/interface) |
| Compiled | Real call | **Inlined at every call site** | Real entry point |
| Debuggable with breakpoints | Yes | Poorly | Yes |

Rules of thumb: use a **Function** by default. Use a **Macro** only when you need latent nodes or multiple exec outputs in a reusable block, and remember it is copied into every call site (so a heavy macro used in twenty places is twenty copies of that logic). Use an **Event** for anything triggered externally or asynchronously.

**Custom Events** are entry points you can call by name and bind to dispatchers. **Event Dispatchers** are the outbound half.

## The Construction Script

The Construction Script is a Blueprint's editor-time graph. It re-runs whenever you move the Actor or change one of its Instance Editable variables in the editor, and again when the Actor is spawned. It can add components.

Archviz uses for it:

- A **parametric window or door**: expose Width, Height, Frame Depth, Glazing Type; the Construction Script builds the frame from scaled mesh pieces and sets the glass material instance. The architect changes a number in the details panel and the geometry updates.
- A **fence, balustrade or pergola along a spline**: `Add Spline Mesh Component` in a loop over spline points.
- A **room dresser**: read a Data Table row for the room type and spawn Instanced Static Mesh transforms for the furniture set.
- A **measurement / setting-out marker** that draws its own labels from its transform.

Two warnings: the Construction Script runs in the editor, so heavy scripts make the viewport sluggish and slow every level load; and it runs *before* `BeginPlay`, so it cannot reference other Actors' runtime state.

## Blueprint communication

Epic documents four patterns. Choosing correctly is most of what separates a maintainable archviz project from an unmaintainable one.

### 1. Direct Blueprint communication

A one-to-one relationship: your working Actor holds a reference to the target Actor and reads or calls its members directly. Epic's own example is a switch in the level that opens a specific door or turns on a specific light. Simple, explicit, and creates a hard dependency.

Use it when: two specific Actors in one level must talk, and the relationship will not be reused.

### 2. Casting

`Cast To BP_Door` converts a generic `Actor` reference into a specific class reference so you can call that class's members. It succeeds only if the object really is of (or derives from) that class.

The cost people forget: **a cast creates a hard reference from the casting Blueprint to the target class**, which means the target class (and everything it references — meshes, materials, textures) is loaded whenever the casting Blueprint loads. In a configurator with fifty option Blueprints, a chain of casts loads all fifty on start-up. Prefer interfaces where the relationship is polymorphic.

### 3. Blueprint Interfaces

An Interface is a set of function signatures with no implementation. Any class can implement it. Epic's example: a car and a tree both implement `OnTakeWeaponFire`, so you can treat them identically.

The archviz equivalent is exactly the right pattern: `BI_Interactable` with `OnFocus`, `OnLoseFocus`, `OnInteract`, `GetDisplayName`. Doors, light switches, cupboards, taps, information hotspots and material-swap surfaces each implement it in their own way. The player's interaction trace calls `OnInteract` on whatever it hit without knowing or caring what it is — and **without creating a hard reference to any of those classes**.

Use it when: many different classes need to respond to the same message.

### 4. Event Dispatchers

An Event Dispatcher lets a Blueprint announce that something happened; any number of other Blueprints **bind** to it and react independently. Epic's examples include communicating from a character Blueprint to the Level Blueprint, and firing events when a spawned Actor is acted upon.

Archviz uses: a `ConfiguratorState` object dispatches `OnOptionChanged(OptionID, ValueID)`; the geometry manager, the price panel, the specification list and the camera controller each bind to it and update themselves. Adding a new listener requires no change to the dispatcher.

Use it when: one event, many unknown listeners; or when you need to call *upward* (from an owned object to its owner) without a hard reference.

**A fifth pattern worth knowing:** a **Game Instance Subsystem** or **World Subsystem** holding shared state, reachable from anywhere with `Get Game Instance Subsystem`. This is cleaner than a Blueprint singleton and is the modern answer to "where does the configurator's current state live".

## Common archviz interactions

### Material switcher / finishes configurator

```
Event: OnFinishSelected (FinishID: Name)
  → Get Data Table Row (DT_Finishes, FinishID)   → struct { MaterialInstance, DisplayName, Price }
  → For Each (TargetMeshComponents)
      → Set Material (ElementIndex = SlotIndex, Material = struct.MaterialInstance)
  → Call Event Dispatcher: OnConfigurationChanged
```

For a smooth crossfade rather than a hard swap, create a **Dynamic Material Instance** (`Create Dynamic Material Instance`) on `BeginPlay`, store it, and drive a `Blend` scalar parameter from a Timeline.

Which meshes to target is the interesting half. Either tag them (`Actor Tags` / `Component Tags`) at import time via Python, or find them by Datasmith metadata. Do not hard-code Actor references; the model will be reimported.

### Door opening

```
BP_Door (Actor)
  Components: DoorFrame (Static Mesh), DoorLeaf (Static Mesh, attached), Trigger (Box Collision)
  Variables: bIsOpen (bool), OpenAngle (float, Instance Editable, default 95),
             OpenDuration (float, default 1.2), bOpensInward (bool)
  Implements: BI_Interactable

  Event OnInteract (from BI_Interactable)
    → Flip bIsOpen
    → Timeline "DoorSwing" (float 0→1, ease in/out, length = OpenDuration)
        Play if bIsOpen, Reverse if not
    → Update: Lerp (0, OpenAngle * (bOpensInward ? -1 : 1)) by Timeline alpha
        → Set Relative Rotation (DoorLeaf, Yaw = result)
```

Sliding doors are the same graph with `Set Relative Location` and a distance instead of an angle. Automatic doors replace `OnInteract` with `On Component Begin Overlap` on the trigger.

### Measurement tool

```
BP_MeasureTool (Actor Component on the Player Controller)
  Variables: PointA (Vector), PointB (Vector), bHasFirstPoint (bool)

  Event OnMeasureClick
    → Get Player Camera Manager → Camera Location / Rotation
    → Line Trace By Channel (Start = CameraLoc, End = CameraLoc + Forward * 5000, Visibility)
    → Branch on Hit
        false: return
        true:  Branch on bHasFirstPoint
                 false: PointA = HitLocation; bHasFirstPoint = true;
                        Spawn marker decal at PointA
                 true:  PointB = HitLocation; bHasFirstPoint = false
                        Distance = VectorLength(PointB - PointA)          // in uu = cm
                        DisplayText = Format Text "{0} mm" with Distance * 10
                        Draw Debug Line / spawn a WBP_MeasureLabel at midpoint
```

Two details that make it usable: snap the hit to the nearest surface normal-aligned axis when the surface is nearly orthogonal, and display in millimetres (`uu × 10`) because that is what the drawings use.

### Interaction trace and focus

Put the trace on Tick in the Player Controller (or, better, on a 10 Hz timer):

```
Line Trace By Channel from camera forward 300 uu
  → Does Implement Interface (BI_Interactable)?
      → If the hit Actor differs from LastFocused:
            call OnLoseFocus on LastFocused
            call OnFocus on new
            set LastFocused
      → Show/hide the prompt widget with GetDisplayName
```

Highlight on focus is best done with a **Custom Depth Stencil** value plus a post-process outline material — it works on any mesh without touching its material.

### Room / viewpoint navigation

A `BP_Viewpoint` Actor per room with a Camera Component and a `DisplayName`. A UMG list built from `Get All Actors of Class (BP_Viewpoint)` sorted by an index. Clicking an entry calls `Set View Target with Blend` on the Player Controller with a 0.8–1.2 s blend and an ease-in-out function. This reads far better than teleporting.

### Sun control at runtime

Expose the SunSky Actor's Solar Time, Month and Day to a UMG slider. Under Lumen this updates the whole lighting solution live, which is the single most persuasive thing you can hand a client. Watch the VSM invalidation cost (file `03`) — clamp the slider's update rate if the frame rate drops while dragging.

## UMG

Widget Blueprints (`WBP_`) are built in the UMG Designer: a Designer tab for layout and a Graph tab for logic. Structure:

- **Canvas Panel** — absolute positioning with anchors. Use sparingly; anchor everything or it breaks at other resolutions.
- **Layout panels** — Vertical Box, Horizontal Box, Grid Panel, Scroll Box, Size Box, Overlay, Wrap Box. Prefer these to Canvas.
- **Common widgets** — Text Block, Rich Text Block, Image, Button, Border, Slider, Check Box, Combo Box (String), Progress Bar, List View / Tile View (virtualised — use these for a long finishes list, not a Vertical Box).
- **Property Binding** — a function evaluated every frame to supply a widget property. Convenient, and a performance trap. Prefer pushing values on change via an Event Dispatcher.
- **Named Slots** and **User Widgets** — build one `WBP_OptionRow` and reuse it, do not copy the layout fifty times.

Displaying a widget: `Create Widget` → `Add to Viewport`. For a widget in world space (a room label floating over a doorway, a spec panel mounted on a wall) use a **Widget Component** on an Actor with Space = World.

Input mode matters: `Set Input Mode Game and UI` with `Show Mouse Cursor` for a configurator; `Set Input Mode Game Only` for a walkthrough. Getting this wrong produces the classic "my buttons do not respond" bug.

**Editor Utility Widgets** are the same technology aimed at the editor. Create with right-click in the Content Browser → *Editor Utilities > Editor Utility Widget*, run with right-click → **Run Editor Utility Widget**; once run, the widget appears in the Level Editor's **Tools** dropdown under *Editor Utility Widgets*, and its tab docks with Level Editor tabs. These are the only Blueprints that can host the `Execute Python Script` node, which makes them the natural front end for the automation in file `06`.

## When to move Blueprint logic to C++

Blueprint compiles to bytecode executed by a VM. It is roughly an order of magnitude slower per node than equivalent C++. That almost never matters in archviz — but these signals do:

1. **Per-frame work over many objects.** A Tick that iterates hundreds of Actors. Move it, or move it off Tick.
2. **Tight numeric loops.** Procedural geometry generation, mesh analysis, pathfinding over a large graph.
3. **A graph you cannot read on one screen.** This is the most common real reason. Blueprint has no diff, no merge and no text search across projects. A 300-node Event Graph is unmaintainable by anyone, including its author in six months.
4. **Shared framework code** that several Blueprints derive from. Write the base class in C++ with `BlueprintCallable` functions and `BlueprintImplementableEvent` hooks, then let Blueprints extend it. This is Epic's recommended division and it works.
5. **Anything you want under source control diffing.** `.uasset` Blueprints do not merge.
6. **Editor tooling that must run headless.** Python or C++, not Blueprint.

The counter-argument, which is strong for a small archviz practice: C++ adds a compiler dependency, a build step, longer iteration, and a hiring constraint. **Stay in Blueprint until one of the six signals above actually fires**, and use Python for editor-side batch work rather than reaching for C++ prematurely.

## Debugging

- **Breakpoints** (F9) on nodes; step through with F10.
- **Watch Values** on pins, visible while the game runs.
- **Print String** — set a Key so repeated prints overwrite rather than stack.
- **Blueprint Debugger** (`Window > Developer Tools > Blueprint Debugger`) — call stack and watched values.
- The **Debug Filter** dropdown in the Blueprint editor toolbar selects which instance you are debugging.
- `Window > Developer Tools > Message Log` catches compile and runtime warnings.
- **Blueprint Nativization** was removed in UE5; do not look for it.

## Open questions

- None material. Blueprint fundamentals are stable and the cited pages are current for 5.8.

## Sources

- [Blueprints Visual Scripting](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Blueprint Communication Usage](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-communication-usage-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Creating User Interfaces with UMG and Slate](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-user-interfaces-with-umg-and-slate-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Editor Utility Widgets](https://dev.epicgames.com/documentation/en-us/unreal-engine/editor-utility-widgets-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Scripting the Unreal Editor Using Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python) — Epic Games, accessed 2026-08-25
- [Gameplay Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Product Configurator Template](https://dev.epicgames.com/documentation/en-us/unreal-engine/product-configurator-template-in-unreal-engine) — Epic Games, accessed 2026-08-25
