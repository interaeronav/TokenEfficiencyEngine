---
id: fusion.simulation
title: The Simulation workspace — FEA for furniture and fixings
domain: 15_software_autodesk_fusion
tags: [fusion, simulation, fea, static-stress, modal, thermal, buckling, nonlinear, event-simulation, mesh, shelf-deflection, bracket]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion, May 2026 major release. Study availability depends on the Simulation Extension."
unit_system: metric
sources:
  - {title: "Autodesk Fusion Simulation Extension", url: "https://www.autodesk.com/products/fusion-360/simulation-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Fusion overview", url: "https://www.autodesk.com/products/fusion-360/overview", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion API Reference — Design object (analyses property)", url: "https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.licensing, fusion.modelling, joinery.wood_science, joinery.sheet_goods]
---

# The Simulation workspace — FEA for furniture and fixings

**Summary.** Fusion's Simulation workspace runs finite element analysis on the design in the same document. Autodesk's overview page advertises "11 advanced simulation studies"; the Simulation Extension page names nonlinear static stress, structural buckling, event simulation, modal frequencies, injection moulding, electronics cooling, thermal and thermal stress, and generative design as extension capabilities, adding "unlimited cloud-based solving for those studies." For joinery the honest position is that **FEA is rarely the right tool for wood** — anisotropy, creep, moisture movement and joint slip dominate real furniture failures and none of them are in a linear static solve — but it is genuinely useful for **metal brackets, fixings, and for sanity-checking a span before you cantilever a 1.2 m shelf over someone's head**.

## Key facts

| Study type | In extension per Autodesk's page | Notes |
|---|---|---|
| **Static Stress** | Not listed as extension-only | Linear elastic. The base capability; the one you will use |
| **Modal Frequencies** | Listed under the extension | Natural frequencies and mode shapes |
| **Thermal / Thermal Stress** | Listed under the extension | Steady-state heat and resulting stress |
| **Structural Buckling** | Listed under the extension | Critical buckling load factor |
| **Nonlinear Static Stress** | Listed under the extension | Large deflection, plasticity, contact |
| **Event Simulation** | Listed under the extension | Explicit dynamics — drop tests, impacts |
| **Injection Moulding (plastic fill)** | Listed under the extension | Not relevant to joinery |
| **Electronics Cooling** | Listed under the extension | Not relevant to joinery |
| **Generative Design** | Listed under the extension | Goal-driven geometry synthesis |
| **Shape Optimization** | **Not** named on the extension page | Status `needs-verification` |

> ⚠️ Which studies are in the base subscription and which need the Simulation Extension has moved between releases, and Autodesk's own extension page does not state the base line-up. **Check in the application** — the study-type chooser greys out what you cannot run — before promising a client an analysis. `needs-verification`.

## The workflow

Switch to the **Simulation** workspace. The sequence is always the same:

1. **New Study** — pick a study type from the gallery. Multiple studies can coexist in one document.
2. **Simplify** (optional) — a dedicated modelling environment for removing fillets, holes and cosmetic detail that would wreck the mesh. Simplification is stored per study and does not alter the design.
3. **Materials** (Study Materials) — assign a physical material per body, or override with a study-specific material.
4. **Constraints** — Structural Constraints: Fixed, Pin, Frictionless, Prescribed Displacement.
5. **Loads** — Structural Loads: Force, Pressure, Moment, Bearing Load, Remote Force, Hydrostatic Pressure, Gravity, Linear/Angular Global Acceleration/Velocity, Toolpath forces.
6. **Contacts** — Manage Contacts / Automatic Contacts. Bonded, Separation, Sliding, Rough, Offset Bonded. Automatic contact is generated on solve if you do nothing; check what it produced.
7. **Mesh** — Generate Mesh, or accept the adaptive default. Local Mesh Control refines specific faces.
8. **Pre-check** — Fusion validates that the model is fully constrained and loaded.
9. **Solve** — locally or in the cloud.
10. **Results** — Safety Factor, Stress (von Mises, principal, normal, shear), Displacement, Reaction Force, Strain, Contact Pressure; plus Adaptive Mesh Refinement and Convergence plots.

`Design.analyses` in the API "gets the collection of design analyses associated with this design"; there is also a separate `CAM.analyses` for Manufacture-workspace analyses. Automation of simulation via the API is limited — treat simulation as an interactive activity.

## Meshing

Fusion meshes with 2nd-order tetrahedra by default. The parameters that matter:

- **Average element size**, as a percentage of the model's bounding-box diagonal (default around 10 %). Reduce it globally only if you must — it is expensive.
- **Minimum element size** as a fraction of average.
- **Grading factor** — how quickly element size changes between refined and coarse regions.
- **Maximum turn angle** — how finely curves are approximated.
- **Local Mesh Control** — refine only where you need it: the fillet at a bracket root, the bearing face of a fixing, the edge where you expect the peak stress.
- **Adaptive Mesh Refinement** — Fusion re-solves and re-meshes until a chosen result converges to a tolerance. **Use this** rather than guessing an element size; it is the difference between a defensible number and a picture.

Rules of thumb: at least **two to three elements through the thickness** of any part carrying bending; at least **three elements across a fillet radius**; never trust a stress reading at a sharp re-entrant corner (it is a mathematical singularity, and it will keep rising as you refine the mesh — round the corner in the model instead).

## Constraints and loads — where analyses go wrong

**Over-constraining is the commonest error.** A shelf "Fixed" on its whole rear face is enormously stiffer than a shelf sitting on two pins. Fixed removes all six degrees of freedom on every node of the selected face; the result is a deflection number that is optimistic by a factor of two or more.

Better patterns for furniture:

- A shelf on shelf pins: **Pin** or **Frictionless** constraints on the small contact patches, or model the pins and use contact.
- A wall-fixed bracket: **Fixed** on the bolt-hole cylindrical faces only, not the whole back plate; or a **Bearing Load** if you want to see bolt shear.
- A carcass on the floor: **Frictionless** on the base, plus one point restrained laterally to stop rigid-body motion.

**Loads:** for furniture, a distributed load on the top face is right (`Pressure` or `Force` over an area), not a point force. Convert a design load: 40 kg over a 900 × 300 mm shelf = 392 N over 0.27 m² = **1.45 kPa**. Add **Gravity** as a separate load so self-weight is included.

**Always run the pre-check.** A model with no constraint solves to garbage or fails to solve at all.

## Material properties for wood-based panels

Fusion's material library contains generic woods; it does **not** contain the southern African MFC and MDF you will actually cut. Create custom materials with measured or published data. Indicative values (see `joinery.wood_science` and `joinery.sheet_goods`; treat as `needs-verification` for any specific board):

| Material | Density (kg/m³) | E (MPa) | MOR (MPa) | Poisson |
|---|---|---|---|---|
| Particleboard / MFC, 18 mm | 650–720 | 2,500–3,500 | 11–16 | ~0.25 |
| MDF, 18 mm | 700–780 | 2,700–3,700 | 20–30 | ~0.25 |
| Birch plywood, 18 mm (parallel to face grain) | 650–700 | 8,000–10,000 | 40–60 | ~0.20 |
| Solid hardwood, along grain | 600–900 | 9,000–14,000 | 70–110 | ~0.35 |
| Mild steel bracket | 7,850 | 200,000 | 250 (yield) | 0.29 |
| Aluminium 6082-T6 | 2,700 | 70,000 | 260 (yield) | 0.33 |

> ⚠️ **Fusion's static stress solver is isotropic and linear.** Wood is orthotropic (stiffness along the grain can be 20× that across it), it creeps (a loaded shelf keeps sagging for years), and it changes dimension with moisture. An FEA of a timber shelf gives you a *lower bound on deflection at time zero*. Real long-term sag in particleboard is commonly **2–3× the instantaneous elastic deflection**. Design to that.

## Worked example: a cantilevered shelf, and why the bracket is the problem

**The question.** A client wants a 900 mm wide × 300 mm deep floating shelf in 18 mm MFC, wall-mounted with concealed brackets, carrying books.

### Step 1 — hand calculation first, always

Design load: 30 kg of books = 294 N, distributed over the 300 mm projection. As a uniformly distributed load along the cantilever, `w = 294 / 0.3 = 980 N/m`.

Section, taking the full 900 mm width as the beam width:
```
I = b·h³/12 = 0.900 × 0.018³ / 12 = 4.374 × 10⁻⁷ m⁴
Z = b·h²/6  = 0.900 × 0.018² / 6  = 4.86  × 10⁻⁵ m³
E = 3.0 GPa (MFC, mid-range)   →  EI = 1,312 N·m²
```

Cantilever with UDL:
```
δ_max = w·L⁴ / (8·EI) = 980 × 0.3⁴ / (8 × 1312) = 0.00076 m = 0.76 mm
M_root = w·L² / 2     = 980 × 0.09 / 2 = 44.1 N·m
σ_root = M/Z          = 44.1 / 4.86e-5 = 0.91 MPa
```

0.91 MPa against a modulus of rupture around 13 MPa is a factor of ~14 — the **panel is not the problem**. 0.76 mm instantaneous, perhaps 2 mm after creep, is acceptable.

### Step 2 — the comparison case that fails

The same 18 mm MFC as a **simply supported shelf on a 900 mm span** carrying 40 kg:
```
w = 392 / 0.9 = 436 N/m,  I = 0.300 × 0.018³/12 = 1.458e-7 m⁴,  EI = 437 N·m²
δ = 5·w·L⁴/(384·EI) = 5 × 436 × 0.6561 / (384 × 437) = 0.0085 m = 8.5 mm
```

8.5 mm instantaneous — about span/106 — becoming 17–25 mm with creep. That is a visibly sagging shelf. **This is the calculation nobody does, and it is why so many wardrobes have bowed shelves.** Fixes: reduce the span to 600 mm, go to 25 mm board, add a front lipping (a 40 × 18 mm solid lipping glued on edge multiplies `I` dramatically), or use plywood.

### Step 3 — where FEA earns its keep: the bracket

The cantilever's real load path is a **44.1 N·m moment plus a 294 N shear at the wall**. A pair of steel plate brackets at 600 mm centres each take ~22 N·m and ~150 N. That moment tries to pull the top fixing out of the wall and push the bottom of the bracket into it.

Model the bracket and run **Static Stress**:

1. Model the bracket as a component: 6 mm mild steel plate, 150 mm wall plate, two 250 mm × 12 mm blades, two Ø8 mm fixing holes at 100 mm vertical centres.
2. **Study Materials** → Steel, AISI 1020 (or a custom material at E = 200 GPa, yield 250 MPa).
3. **Constraint**: `Fixed` on the two Ø8 mm bolt-hole cylindrical faces only.
4. **Load**: `Force` of 147 N (half the shelf load) applied as a distributed load along the top edge of each blade, plus `Gravity`.
5. **Mesh**: adaptive refinement, convergence target on von Mises stress, local refinement at the blade-to-plate fillet.
6. **Solve**, then read **Safety Factor** (yield-based).

What to look for:
- **Peak von Mises at the fillet root.** If the fillet is modelled as a sharp corner you will get a singularity; put a 4–6 mm radius in the model and refine there.
- **Safety factor.** For furniture that people may sit or pull on, target **≥ 3** against yield, not 1.5.
- **Displacement at the blade tip.** Add it to the panel's own 0.76 mm — a bracket that flexes 2 mm makes the shelf look bad even though the panel is fine.
- **Reaction forces at the constraints.** This is the number you take to the wall-fixing selection: the top bolt is in **tension**, and the tension is `M / (bolt spacing)` = 22 / 0.1 = **220 N per bracket**, plus prying.

**[NA]** The wall matters more than the bracket. In a Namibian house, a shelf may be fixed into: solid burnt-clay brick (good), hollow cement block (poor — the shell is often 20–25 mm and a standard plug pulls straight through), or drywall/gypsum on studs (only into the studs). A 220 N tension is trivial in solid brick and marginal in a hollow block with a conventional plug. Specify a chemical anchor or a proper hollow-block toggle, and say so on the drawing.

### Step 4 — what FEA did not tell you

- Creep in the panel over 5 years.
- Moisture movement of a solid front lipping in a dry Windhoek interior at 5–8 % EMC (`joinery.wood_science`).
- Whether the fixing will hold in *that* wall.
- What happens when a child hangs on the shelf — that is an **Event Simulation** (extension) or, honestly, a design decision to over-specify.

That list is why the hand calculation and the material knowledge come first, and the FEA second.

## When to bother with simulation at all

**Do simulate:** steel or aluminium brackets and connectors; a metal frame for a large table or reception desk; a folding or lifting mechanism's arm; anything where failure hurts someone; anything you will make many of and want to lighten.

**Do not simulate:** ordinary carcass panels (use span tables and hand calculations); anything jointed with glue and dowels where joint stiffness dominates and you cannot characterise it; anything where you would need orthotropic timber properties you do not have.

**Always do instead:** the hand calculation. `δ = 5wL⁴/384EI` for a simply supported shelf and `δ = wL⁴/8EI` for a cantilever will answer 90 % of the furniture questions in thirty seconds, and — unlike an FEA — you can check them.

## Sources

- [Autodesk Fusion Simulation Extension](https://www.autodesk.com/products/fusion-360/simulation-extension) — Autodesk, accessed 2026-08-25
- [Autodesk Fusion overview](https://www.autodesk.com/products/fusion-360/overview) — Autodesk, accessed 2026-08-25
- [Fusion API Reference — Design object](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/Design.htm) — Autodesk, accessed 2026-08-25

## Open questions

- **Exactly which study types are in the base subscription.** Autodesk's extension page lists what the extension adds but does not state the base line-up. Static Stress is not named as extension-only, which implies it is included, but this is inference. `needs-verification` in the application.
- Whether Shape Optimization still exists as a study type in the May 2026 release.
- Whether Fusion supports orthotropic material definitions for timber in Static Stress. Believed not; `needs-verification`.
- Menu/panel labels in the Simulation workspace were not verified against a scraped Autodesk help page.
- Material property ranges in the table above are indicative trade values, not board-specific published data. Get the manufacturer's technical data sheet for the actual board.
