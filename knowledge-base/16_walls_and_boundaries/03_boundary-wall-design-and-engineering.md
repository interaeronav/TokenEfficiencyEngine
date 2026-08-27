---
id: walls.boundary_design
title: Boundary wall design and engineering
domain: 16_walls_and_boundaries
tags: [freestanding-wall, wind-load, slenderness, piers, buttress, foundation, control-joint, brickforce, coping, retaining-wall, earth-pressure, rankine, drainage, failure-modes, worked-example]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "SANS 10400-K:2011 The application of the National Building Regulations Part K: Walls", url: "https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html", publisher: "SABS / Internet Archive", accessed: 2026-08-25}
  - {title: "Quantities for ordering building materials", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Concrete, plaster and mortar mixes for builders", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Lateral earth pressure", url: "https://en.wikipedia.org/wiki/Lateral_earth_pressure", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Mechanically stabilized earth", url: "https://en.wikipedia.org/wiki/Mechanically_stabilized_earth", publisher: "Wikipedia", accessed: 2026-08-25}
related: [walls.typology, walls.construction, walls.specifying]
unit_system: SI
applies_to: [freestanding-wall, retaining-wall, boundary-wall]
---

# Boundary wall design and engineering

**Summary.** A freestanding boundary wall is a vertical cantilever with essentially no vertical load. Wind governs everything. Two checks decide the wall: **flexural tension in the bed joint at the base** and **overturning of the wall-plus-foundation about the toe**. The southern African deemed-to-satisfy route is **SANS 10400-K:2011 clause 4.2.4 with Tables 17 (solid units) and 18 (hollow units)**, which fix a maximum height for each combination of thickness, pier geometry and pier spacing. This file gives the tables in full, the physics behind them, foundation sizing, movement-joint spacing, reinforcement options, coping and weathering, retaining-wall fundamentals with earth pressure and drainage, and two fully worked examples — a **1,8 m** and a **2,1 m** masonry boundary wall — with the arithmetic shown.

## Key facts

| Item | Value | Reference |
|---|---|---|
| Freestanding wall, code definition | "wall (that is not a retaining wall) without lateral support" | SANS 10400-K 3.22 |
| Minimum unit strength, freestanding/retaining/parapet/balustrade | **3,0 MPa** hollow, **5,0 MPa** solid | 4.2.1.1 |
| Mortar | **Class II** to SANS 2001-CM1 | 4.2.1.1 |
| Class II mortar, common cement | **50 kg cement : 200 ℓ building sand**; 7 bags + 1,35 m³ sand per m³ | C&CSA |
| Class II strength, works test / preliminary lab | **5 MPa / 7 MPa** at 28 d | C&CSA Table 2 |
| Horizontal DPC in a freestanding wall | **Shall not be provided** | 4.2.4.3 |
| Ground-level difference *x* across the wall | If *x* > 0,3 m, reduce permitted height by (*x* − 0,3 m) | 4.2.4.1, 4.2.4.2 |
| Piers | Must run **full height with no reduction in size**; hollow pier cores solidly filled | 4.2.4.2 |
| Wall ends | Wall must **terminate in a pier or a return** | 4.2.4.2 |
| Control joints, freestanding wall | Clay: **16 / 10 / 6 m** by moisture expansion; concrete: **5,0–7,0 m** | Table 19 |
| Control joints, freestanding wall with bed-joint reinforcement ≤ 450 mm c/c | Clay: **6 / 12 / 8 m**; concrete: **10 m** | Table 19 |
| Control joints in freestanding walls | Extend **to the top of the foundation** | 4.2.6.3 |
| Control joint gap | Concrete units ≤ **12 mm**; clay units **10–12 mm** | 4.2.6.5 |
| Retaining wall weepholes | **50 mm dia.**, geofabric on buried end, ≤ **300 mm** above lower ground, ≤ **1,5 m** centres | 4.2.4.1 |
| Retaining wall control joints | ≤ **10 m** | 4.2.4.1 |
| Retaining wall surcharge exclusion zone | No surcharge within a distance equal to the retained height | 4.2.4.1 |
| DTS tables exclusion | Do **not** apply to walls "exposed to severe wind loadings at crests of steep hills, ridges and escarpments" | 4.2.1.1 |

> ⚠️ The SANS 10400-K freestanding-wall tables are a **deemed-to-satisfy** route, not a design. If any condition of 4.2.4.2 is not met — earth retained, ground step > 0,3 m, reduced piers, a free end without a pier or return, a wall on an exposed crest, or a wall carrying a gate, sign or heavy planter — the tables lapse and the wall must be designed by a competent person to SANS 10400-B / SANS 10160.

## 1. Why wind governs

For a freestanding wall, self-weight produces almost no pre-compression at the base. A 220 mm masonry wall 1,8 m high weighs about 7,8 kN per metre run, giving a base compressive stress of only about **0,035 MPa**. That is one-fortieth of the compressive strength of the masonry, so crushing is never the issue. What the 0,035 MPa does do is offset a small part of the flexural tension caused by wind — and flexural tension in a bed joint is the weakest thing in masonry.

The load path is short and brutal: wind pressure on the windward face plus suction on the leeward face → out-of-plane bending → maximum moment at the base course → tension in the bed joint at the base → the wall hinges and falls as a slab.

### Design wind pressure

Net wind pressure on a freestanding wall is
`w_net = q_p(z) × c_f × c_s c_d`
where `q_p` is peak velocity pressure at reference height and `c_f` is the net force coefficient for the wall. Key behaviours to know:

- **Force coefficients are highest near a free end.** In the Eurocode family (which SANS 10160-3 follows in structure), a solid wall is divided into zones A, B, C, D from the free end, with the coefficient in the end zone typically **2–3 times** that in the far field. This is why the code insists a wall terminates in a pier or return, and why walls fall down starting at gate openings and corners.
- **Long walls are relieved.** As length/height increases, the far-field coefficient falls towards about 1,2.
- **Porosity relieves.** A wall with 20–50 % open area sees a substantially reduced coefficient — the physical basis of the Galloway dyke and of screen-block walling.
- **Open flat terrain is worse than suburbia at low level.** Ohangwena is flat and open; the terrain roughness factor at 2 m above ground is *higher* there than in a built-up suburb, so do not borrow a Windhoek suburban design pressure.

> ⚠️ The fundamental basic wind speed for Okongo/Ohangwena must be read from **SANS 10160-3 Annex A** (the regional wind map). That map was not available to this pass. The worked examples below use an assumed **net design wind pressure of 0,70 kN/m²** in the general zone and **1,40 kN/m²** within a distance equal to the wall height of any free end, gate opening or corner. `needs-verification` — confirm against SANS 10160-3 before construction.

### What the SANS tables imply about wind

A useful sanity check, derived here rather than quoted: take the DTS limit of a **220 mm solid wall at 1,8 m with no piers**. Section modulus per metre run `Z = 1000 × 220² / 6 = 8,07 × 10⁶ mm³`. Self-weight compression is 0,035 MPa. If the permissible net flexural tension is taken as 0,10 MPa (a common conservative value for masonry normal to bed joints with Class II mortar), the resisting moment is
`M = (0,10 + 0,035) MPa × 8,07 × 10⁻³ m³ = 1,09 kNm/m`
and the wind pressure that produces it is
`w = 2M / h² = 2 × 1,09 / 1,8² = 0,67 kN/m²`.

So the code's DTS heights are broadly consistent with a **net design wind pressure of about 0,65–0,70 kN/m²** and a modest reliance on mortar bond. Two conclusions follow:

1. The tables **do rely on flexural bond**. A wall with no bond — dry-stacked, poorly filled perpends, mortar allowed to stiffen before laying, dusty units — has no reserve. Under pure gravity (no tension permitted anywhere), the same 220 mm × 1,8 m wall would only resist about **0,18 kN/m²** — a quarter of the design wind. **Workmanship is not a finishing issue on a boundary wall; it is the structure.**
2. In genuinely exposed terrain, or on an escarpment, or where the client wants 2,4 m, the tables are the wrong tool.

## 2. Slenderness — the height-to-thickness rules

The code expresses slenderness as an explicit height limit rather than a ratio, but the ratios are worth carrying in your head. From **Table 17 (solid units)** and **Table 18 (hollow units)**:

### No piers

| Nominal thickness T (mm) | Solid units, max h (m) | h/T | Hollow units, max h (m) | h/T |
|---|---|---|---|---|
| 90 | 0,8 | 8,9 | 0,8 | 8,9 |
| 110 | 1,0 | 9,1 | — | — |
| 140 | 1,3 | 9,3 | 1,2 | 8,6 |
| 190 | 1,5 | 7,9 | 1,4 | 7,4 |
| 220 | 1,8 | 8,2 | — | — |
| 290 | 2,2 | 7,6 | — | — |

The unpiered rule of thumb: **h ≈ 8 × T** for solid units, **h ≈ 7,5 × T** for hollow. Note that this is *not* a constant ratio — it drops as the wall gets thicker, because self-weight compression grows linearly with thickness while section modulus grows with the square.

### Z-shaped walls (staggered plan)

| T (mm) | max h (m) | Pier/offset D × W (mm) | Max spacing s (m) |
|---|---|---|---|
| 90 | 1,8 | 390 × 90 | 1,2 |
| 90 | 2,0 | 490 × 90 | 1,4 |
| 110 | 1,6 | 330 × 110 | 1,5 |
| **110** | **2,1** | **440 × 110** | **1,5** |
| 140 | 2,2 | 440 × 140 | 2,0 |
| 140 | 2,5 | 590 × 140 | 2,5 |
| 190 | 2,1 | 390 × 190 | 2,5 |
| 190 | 2,5 | 490 × 190 | 3,0 |
| 220 | 2,4 | 440 × 220 | 3,0 |
| 220 | 2,8 | 550 × 220 | 4,0 |

Hollow units, Z-shaped: 90 → 1,6 m (390 × 90 @ 1,2 m) and 1,8 m (490 × 90 @ 1,4 m); 140 → 1,8 m (440 × 140 @ 2,0 m) and 2,1 m (540 × 140 @ 2,2 m); 190 → 2,3 m (590 × 190 @ 2,8 m).

### Piers projecting on one side

| T (mm) | max h (m) | Pier D × W (mm) | s (m) |
|---|---|---|---|
| 90 | 1,4 | 290 × 290 | 1,4 |
| 90 | 1,5 | 390 × 290 | 1,6 |
| 90 | 1,7 | 490 × 290 | 1,6 |
| **110** | **1,5** | 330 × 330 | 1,8 |
| 110 | 1,5 | 440 × 330 | 1,8 |
| **110** | **1,9** | **550 × 330** | **2,0** |
| 140 | 1,7 | 440 × 440 | 2,2 |
| 140 | 1,8 | 590 × 390 | 2,5 |
| 190 | 2,0 | 590 × 390 | 2,8 |
| **220** | **2,3** | **660 × 440** | **3,2** |

Hollow units: 90 → 1,2 m (390 × 390 @ 1,4 m), 1,7 m (490 × 390 @ 1,7 m); 140 → 1,4 m (440 × 290 @ 2,1 m), 1,5 m (540 × 390 @ 2,3 m); 190 → 1,6 m (590 × 390 @ 2,8 m).

### Piers projecting on both sides

Solid: 90 → 1,5 m (490 × 290 @ 1,4 m); 110 → 1,6 m (550 × 330 @ 1,8 m); 140 → 1,6 m (440 × 440 @ 2,2 m); 190 → 1,8 m (590 × 390 @ 2,8 m); 220 → 2,1 m (660 × 440 @ 3,2 m).
Hollow: 90 → 1,0 m (490 × 290 @ 1,4 m); 140 → 1,4 m (440 × 440 @ 2,2 m); 220 → 1,7 m (660 × 440 @ 2,9 m).

**Note the counter-intuitive result:** two-sided piers give *lower* permitted heights than one-sided piers of the same overall depth (220 mm: 2,1 m vs 2,3 m), because the section's neutral axis sits in the middle instead of being pushed towards the compression face. Use two-sided piers for appearance and for walls that must look the same from both sides; use one-sided piers, on the leeward side, for structural efficiency.

### Diaphragm walls — the efficient option

Solid units: 90 mm leaves → **2,1 m** with 290 × 190 ribs at 1,4 m, or **2,7 m** with 390 × 190 ribs at 1,4 m; 110 mm → **2,6 m** with 330 × 220 ribs at 1,6 m.
Hollow units: 90 mm → 1,8 m with 290 × 190 at 1,4 m, or **2,3 m** with 390 × 190 at 1,4 m.

A 90 mm diaphragm wall reaching 2,7 m uses roughly the same masonry per metre run as a 190 mm solid wall that only reaches 1,5 m. If height is the requirement and money is short, this is the answer — at the cost of a more demanding bricklayer.

### The classic rules for 110 mm and 220 mm walls

Southern African practice reduces the tables to two remembered cases:

- **110 mm (single-brick-on-edge / half-brick) wall.** 1,0 m free-standing unpiered. With **330 × 330 mm piers at 1,8 m centres**, 1,5 m. With **550 × 330 mm piers at 2,0 m centres**, 1,9 m. As a Z-wall with **440 × 110 offsets at 1,5 m**, **2,1 m**. As a diaphragm with 330 × 220 ribs at 1,6 m, 2,6 m.
- **220 mm (one-brick) wall.** 1,8 m free-standing unpiered — the workhorse dimension for a southern African boundary. With **660 × 440 mm piers at 3,2 m centres**, 2,3 m. As a Z-wall with **550 × 220 offsets at 4,0 m**, 2,8 m.

If someone proposes a 2,1 m boundary wall in 110 mm masonry with piers "every three metres", they are outside the code by a wide margin: 110 mm one-sided piers reach 1,9 m only at 2,0 m centres.

## 3. Foundations

SANS 10400-K refers foundations to **SANS 10400-H**. That standard's tables were not readable in this pass (`needs-verification`), so the following is derived from first principles and stated as such.

### What the foundation has to do

1. Spread load onto the soil — trivial for a boundary wall (bearing pressures of 15–30 kPa).
2. Resist **overturning** with an adequate factor of safety.
3. Keep the resultant within the base so the footing does not lift at the heel.
4. Found **below the zone of seasonal moisture change and below loose or disturbed material**.

Overturning is the governing check, and it is the one routinely ignored on site.

### Sizing rules derived

For a wall of height `h`, thickness `t`, masonry unit weight `γ_m ≈ 19,6 kN/m³` (2 000 kg/m³ including mortar), a strip footing of width `B`, thickness `d`, founded with its underside at depth `D` below ground:

- Wall weight per metre: `W_w = t · h · γ_m`
- Footing weight per metre: `W_f = B · d · 24 kN/m³`
- Overturning moment about the footing underside: `M_ot = w · h · (h/2 + D)`
- Restoring moment about the toe: `M_r = (W_w + W_f + W_s) · B/2`, where `W_s` is soil weight on the buried offsets
- Require **FoS ≥ 2,0** on overturning, and eccentricity `e = M_ot / N ≤ B/6` (resultant in the middle third)

### Founding depth **[NA]**

In the deep aeolian Kalahari sands around Okongo:

- Minimum founding depth **450 mm** below finished ground level, and always **at least 150 mm into undisturbed, competent material**.
- Increase to **600 mm** where the trench passes through loose windblown sand, backfilled services, or an old cultivated layer.
- In or near an *oshana* (seasonal drainage line) with a high water table, do not found in saturated sand; either deepen to firm material, or spread the load with a wider, thicker, lightly reinforced raft strip, or move the wall.
- Where calcrete is met, found **on** it, not partly on it and partly on sand — differential stiffness cracks the wall. Step the foundation.

### Concrete

Low-strength (15 MPa) concrete is suitable for unreinforced foundations of single-storey work. From Cement & Concrete SA: 15 MPa with 32,5N/R common cement and 19 mm stone requires **5,8 bags (290 kg) of cement, 0,65 m³ sand and 0,65 m³ stone per m³**, or as a 2-bag batch, 2 bags + 3½ barrows sand + 3½ barrows stone yielding **0,35 m³**. Use 25 MPa (7,7 bags/m³) where the footing is lightly reinforced or where the wall exceeds 2,0 m.

### Practical foundation schedule (derived — verify with SANS 10400-H and local soils)

| Wall | Footing B × d (mm) | Founding depth D (mm) | Notes |
|---|---|---|---|
| ≤ 1,2 m, 140 mm wall | 450 × 200 | 450 | Unreinforced 15 MPa |
| 1,8 m, 220 mm, no piers | **800 × 250** | 450 | See worked example 1 |
| 2,1 m, 220 mm with 660 × 440 piers @ 3,2 m | **800 × 250** strip, **1 000 × 1 000 × 300** pads under piers | 500 | See worked example 2 |
| 2,1 m, 110 mm Z-wall @ 1,5 m | 600 × 250 following the Z-plan | 450 | Footing must follow the stagger |
| Precast panel-and-post, 2,0 m | Post holes **400 × 400 × 700** deep, filled 15 MPa | 700 | Post fixity is the whole design |

## 4. Movement and control joints

From **Table 19**, maximum length of freestanding wall between vertical control joints:

| Unit type | Moisture expansion (%) | Unreinforced (m) | With bed-joint reinforcement ≤ 450 mm c/c (m) |
|---|---|---|---|
| Burnt clay | < 0,05 | 16 | 6 |
| Burnt clay | 0,05–0,10 | 10 | 12 |
| Burnt clay | 0,11–0,20 | 6 | 8 |
| Concrete | — | 5,0–7,0 | 10 |

(The clay/reinforced row values are reproduced as printed in the standard; the 16 → 6 m entry appears anomalous and should be checked against a clean copy. `needs-verification`)

Rules that go with them:
- In a **freestanding** wall, control joints **extend to the top of the foundation** (4.2.6.3) — unlike in buildings, where they need not continue below ground floor level.
- Joints are **butt joints across the full width** (4.2.6.4), gap ≤ 12 mm for concrete units, 10–12 mm for clay (4.2.6.5).
- Backing material for the sealant must be **flexible cellular polyethylene, cellular polyurethane or foam rubber**. Hemp, softboard, cork and semi-rigid foams are explicitly unsuitable (4.2.6.7 NOTE 1).
- Sealant width-to-depth ratio between **2:1 and 1:1** — the depth of seal must not exceed the joint width.
- Put a control joint at **every change in wall height, at every step in a stepped foundation, and immediately adjacent to every gate pier** — those are the three places boundary walls actually crack.

Because concrete masonry needs joints at only 5–7 m unreinforced, a typical 40 m boundary run needs **6–8 control joints**. Contractors leave them out because they are ugly and fiddly. The wall then cracks at 6 m intervals anyway — just not where you chose.

## 5. Reinforcement options

- **Brickforce / truss-type bed-joint reinforcement.** SANS 10400-K's NOTE 2 to the panel tables allows hollow-unit walls to use solid-unit values if truss-type brickforce with **main wires ≥ 3,55 mm diameter** is built in at vertical centres **not exceeding 400 mm**. For freestanding walls, brickforce at 400–450 mm centres also lets you double the control-joint spacing (Table 19).
- **Rod reinforcement** — hard-drawn wire 4,0–6,0 mm diameter, pre-straightened, proof stress **485 MPa** (3.38, 4.2.1.2).
- **Y8 bars in bond blocks / bond beams.** In hollow-unit construction, a single Y8 in bond beams at centres not exceeding **1 200 mm** may be treated as equivalent to bed-joint reinforcement (Table 19 NOTE 2). For a freestanding wall this is the cheapest way to buy both joint spacing and robustness.
- **Vertical reinforcement grouted into cores.** Y10 or Y12 bars in filled cores at pier positions, starter bars cast into the footing with a lap of at least 40 diameters, cores filled with **grade 10 infill concrete** (as required for foundation walls in 4.2.2.7). This converts the wall from a gravity element into a genuine reinforced cantilever and is the correct approach for anything above the DTS heights.
- **Galvanizing. [ZA]/[NA]** Within 1 km of the coast or 3 km of corrosive industry, brickforce must be pre-galvanized to SANS 935 grade 2. Not relevant at Okongo, but relevant for Walvis Bay or Lüderitz work.

## 6. Damp-proof courses — the counter-intuitive rule

> ⚠️ **SANS 10400-K 4.2.4.3: "No horizontal damp-proof course (DPC) shall be provided in free-standing walls."**

This surprises builders who put a DPC in everything. The reason is structural: a DPC is a **bond breaker**. It reduces the flexural tensile capacity of the bed joint at exactly the level of maximum moment, and it can act as a slip plane in shear. The code confirms the effect elsewhere: for balustrade and parapet walls, minimum thickness is height ÷ 5,0 with no DPC at the base but height ÷ 4,5 **with** a DPC — a 10 % thickness penalty just for having one.

The moisture problem is therefore solved differently in a freestanding wall:

- Use units and mortar that tolerate saturation — Class II mortar and units of ≥ 5,0 MPa (solid) / 3,0 MPa (hollow).
- Keep the ground clear of the wall: a **150 mm** minimum from finished ground to the first course above the footing, with the ground falling away.
- If rising damp staining is a concern on a rendered wall, stop the render **150 mm above ground** with a bell-cast drip and leave the base bare, rather than inserting a DPC.
- **Never** carry a house DPC through into a boundary wall that abuts it — put a control joint at the junction instead.

## 7. Copings, cappings and weathering

The coping is the single most cost-effective durability item on a boundary wall. Its jobs: shed water clear of the face, protect the top course from saturation and frost/salt cycling, resist being levered off, and finish the wall visually.

Requirements:

- **Overhang** at least **40 mm** each side of the wall face, with a **throat / drip groove** at least 8 × 8 mm set back 15–20 mm from the arris. Without a drip, water tracks back under the coping and runs down the face, staining it and saturating the top courses.
- **Fall** — either a twice-weathered (saddleback) profile, a single fall of not less than 1:12 towards the less important side, or a chamfered *in situ* concrete capping.
- **Bedding** — full bed in Class II mortar. Coping units are the most common wind-blown loose object on a wall.
- **Anchorage** — for units over ~600 mm long or on walls over 2,0 m, dowel the coping into the wall with stainless or galvanized cramps, or lay it on a continuous bed with brickforce.
- **A joint in the coping over every control joint** in the wall, sealed, not pointed solid.
- **Anti-climb** — a smooth, round or overhanging coping is markedly harder to grip than a flat one. This is the legitimate design descendant of the Berlin Wall pipe coping.

Typical coping options in southern Africa: precast concrete saddleback or chamfered capping units; a bullnosed brick-on-edge course; an *in situ* 75 mm concrete capping cast with a 12 mm chamfer and a drip on both sides; or a slate/stone flag on a masonry wall.

## 8. Worked example 1 — 1,8 m masonry boundary wall

**Brief.** 40 m of boundary wall, 1,8 m high above finished ground, solid concrete masonry, plastered both sides, precast coping. Flat open ground, Okongo. Two 4,0 m vehicle gate openings and one 1,0 m pedestrian gate.

**Step 1 — choose the section from Table 17.**
220 mm solid units, no piers → maximum height **1,8 m**. ✔ Exactly at the DTS limit.
Ground level difference across the wall *x* must be ≤ 0,3 m. Confirm by survey; if a level difference of, say, 0,55 m exists at one point, the permitted height there drops to 1,8 − (0,55 − 0,3) = **1,55 m**.
Units: 220 mm nominal is achieved with 222 × 90 × 114 maxi units laid in two leaves collar-jointed, or with 390 × 220 × 190 blocks. Take **440 × 220 × 220 solid blocks, 10 per m², 1,50 m³ mortar per 1 000 units** (C&CSA Table 3).

**Step 2 — loads.**
Assumed net design wind pressure `w = 0,70 kN/m²` (general zone). `needs-verification` against SANS 10160-3.
Per metre run: `F = 0,70 × 1,8 = 1,26 kN/m`, acting at `1,8/2 = 0,90 m` above ground.

**Step 3 — flexural check at the base course.**
`Z = 1 000 × 220² / 6 = 8,07 × 10⁶ mm³ = 8,07 × 10⁻³ m³`
`M = w h² / 2 = 0,70 × 1,8² / 2 = 1,13 kNm/m`
`σ_bending = M / Z = 1,13 / 8,07 × 10⁻³ = 140 kPa = 0,140 MPa`
Self-weight: `W = 0,220 × 1,8 × 19,6 = 7,76 kN/m`; `σ_c = 7,76 / 0,220 = 35,3 kPa = 0,035 MPa`
**Net tension = 0,140 − 0,035 = 0,105 MPa.**
Against a permissible flexural tension of 0,10 MPa this is marginal — which is exactly what you would expect at the DTS limit. Accept, but with two conditions: (a) full, solidly filled bed and perpend joints, and (b) at gate openings and the two free ends, where the end-zone coefficient roughly doubles the pressure, **add a pier** (660 × 440 mm, full height) or a **1,0 m return**.

**Step 4 — foundation.**
Try `B = 600 mm, d = 250 mm, D = 450 mm`.
`W_f = 0,600 × 0,250 × 24 = 3,60 kN/m`; `N = 7,76 + 3,60 = 11,36 kN/m`
`M_ot = 1,26 × (0,90 + 0,45) = 1,70 kNm/m`
`M_r = 11,36 × 0,300 = 3,41 kNm/m` → **FoS = 2,00** (bare minimum)
`e = 1,70 / 11,36 = 0,150 m`; `B/6 = 0,100 m` → **resultant outside the middle third — heel lifts.** Reject.

Try `B = 800 mm, d = 250 mm, D = 450 mm`.
`W_f = 0,800 × 0,250 × 24 = 4,80 kN/m`; soil on the two 290 mm offsets, 200 mm deep at 17 kN/m³: `W_s = 2 × 0,290 × 0,200 × 17 = 1,97 kN/m`; `N = 7,76 + 4,80 + 1,97 = 14,53 kN/m`
`M_r = 14,53 × 0,400 = 5,81 kNm/m` → **FoS = 3,42** ✔
`e = 1,70 / 14,53 = 0,117 m`; `B/6 = 0,133 m` → **inside the middle third** ✔
Bearing: `q_max = N/B × (1 + 6e/B) = (14,53/0,80) × (1 + 6 × 0,117/0,80) = 18,2 × 1,88 = 34 kPa` — comfortable on any competent sand. ✔

**Adopt: 800 × 250 mm unreinforced 15 MPa strip, underside 450 mm below finished ground.**
Where the wall crosses loose or made ground, deepen to 600 mm and add 2 × Y10 top and bottom over that length.

**Step 5 — control joints.**
Concrete masonry, unreinforced: maximum **7,0 m**. With brickforce at 400 mm centres: **10 m**.
For a 40 m run with brickforce: joints at 0 (gate pier), 10, 20, 30, 40 m, plus a joint each side of every gate pier and at every foundation step. Take **6 joints**, 10 mm gap, backer rod plus polyurethane sealant, extending to the top of the foundation.

**Step 6 — reinforcement and detailing.**
Brickforce, 3,55 mm main wire truss type, at **400 mm** vertical centres (i.e. every second course of 220 mm blocks), lapped 150 mm, stopped 50 mm short of each control joint.
Piers 660 × 440 at both free ends and both sides of each gate opening, cores filled with grade 10 infill concrete, with 2 × Y12 starter bars from the footing lapped 480 mm.
Mortar: **Class II** — 50 kg cement : 200 ℓ building sand, i.e. 7 bags cement + 1,35 m³ sand per m³ of mortar.
Coping: precast chamfered capping, 40 mm overhang each side, drip groove, bedded solid, jointed over each control joint.

**Step 7 — quantities per metre run (see file `10` for the full BoQ).**
Wall area 1,8 m²/m. At 10 blocks/m² (440 × 220 × 220) = **18 blocks/m**.
Mortar at 1,50 m³ per 1 000 units = 0,027 m³/m + 30 % wastage = **0,035 m³/m** → about 0,25 bag cement and 0,047 m³ sand per metre.
Excavation: 0,800 × 0,450 = 0,36 m³/m. Concrete: 0,800 × 0,250 = **0,20 m³/m** → at 5,8 bags/m³, **1,16 bags cement/m**.
Plaster both sides at 15 mm: 3,6 m²/m → at 700 kg cement + 2,25 m³ sand per 100 m² (external, common cement), **0,50 bag cement and 0,081 m³ plaster sand per metre**.

## 9. Worked example 2 — 2,1 m masonry boundary wall

**Brief.** Same site, client wants 2,1 m for security and privacy.

**Step 1 — the 1,8 m section will not do.** 220 mm unpiered is capped at 1,8 m. Options from Table 17 that reach 2,1 m:

| Option | Section | Piers | Masonry per m run |
|---|---|---|---|
| A | 220 mm | 660 × 440 @ 3,2 m one side (rated 2,3 m) | 0,462 + 0,061 = 0,523 m³ |
| B | 220 mm | 660 × 440 @ 3,2 m both sides (rated 2,1 m) | as A |
| C | 110 mm | 440 × 110 Z-offset @ 1,5 m (rated 2,1 m) | ~0,29 m³ |
| D | 190 mm | 390 × 190 Z-offset @ 2,5 m (rated 2,1 m) | ~0,44 m³ |
| E | 110 mm diaphragm | 330 × 220 ribs @ 1,6 m (rated 2,6 m) | ~0,32 m³ |
| F | 290 mm | none (rated 2,2 m) | 0,609 m³ |

Option **C** uses 45 % less masonry than option A and is the cheapest in material; it costs more in setting-out and cutting and produces a strongly articulated wall. Option **A** is what most southern African contractors will price. Take **Option A** for the worked example because it is the common case, and note C as the value-engineered alternative.

**Step 2 — pier design check (Option A).**
Pier 660 mm overall depth × 440 mm wide, projecting 440 mm beyond a 220 mm wall, at 3,2 m centres.
Treat as a T-section with the wall acting as a flange of width equal to the pier spacing (3 200 mm) and thickness 220 mm, and a web 440 × 440 mm.

`A_flange = 3 200 × 220 = 704 000 mm²`, centroid 110 mm from the wall's outer face
`A_web = 440 × 440 = 193 600 mm²`, centroid 440 mm from the wall's outer face
`A_total = 897 600 mm²`
`ȳ = (704 000 × 110 + 193 600 × 440) / 897 600 = 162,6 × 10⁶ / 897 600 = 181 mm`

`I_flange = 3 200 × 220³/12 + 704 000 × (181 − 110)² = 2,84 × 10⁹ + 3,57 × 10⁹ = 6,41 × 10⁹ mm⁴`
`I_web = 440 × 440³/12 + 193 600 × (440 − 181)² = 3,12 × 10⁹ + 12,97 × 10⁹ = 16,09 × 10⁹ mm⁴`
`I_total = 22,5 × 10⁹ mm⁴`

Critical fibre is the **pier tip**, at `660 − 181 = 479 mm` from the neutral axis:
`Z_tip = 22,5 × 10⁹ / 479 = 4,70 × 10⁷ mm³`

Load on one pier: `F = 0,70 kN/m² × 3,2 m × 2,1 m = 4,70 kN`, at 1,05 m
`M = 4,70 × 1,05 = 4,94 kNm = 4,94 × 10⁶ Nmm`
`σ_bending = 4,94 × 10⁶ / 4,70 × 10⁷ = 0,105 MPa`

Self-weight compression: `W = 0,8976 m² × 2,1 m × 19,6 kN/m³ = 36,9 kN`; `σ_c = 36,9 / 0,8976 = 41,1 kPa = 0,041 MPa`
**Net tension = 0,105 − 0,041 = 0,064 MPa** — comfortably under 0,10 MPa. ✔

Wind from the other direction puts tension at the wall face, where `Z = 22,5 × 10⁹ / 181 = 1,24 × 10⁸ mm³` and `σ = 0,040 MPa` — offset entirely by self-weight. ✔ Not critical.

**Step 3 — panel check between piers.**
The wall panel spans horizontally 3,2 m between piers and vertically 2,1 m as a cantilever. Two-way action means the vertical cantilever moment reduces substantially, but as a conservative check treat a 1 m-high strip spanning 3,2 m horizontally:
`M = w L² / 8 = 0,70 × 3,2² / 8 = 0,90 kNm/m`
`Z = 1 000 × 220²/6 = 8,07 × 10⁻³ m³` → `σ = 0,111 MPa` **parallel** to the bed joints, where masonry flexural strength is roughly **2–3 × the normal-to-bed value** (typically 0,2–0,5 MPa). ✔
This is why piers work: they turn a hard vertical-cantilever problem into an easy horizontal-span problem.

**Step 4 — foundation.**
Per metre of wall, including the pier averaged over 3,2 m:
`W_wall = 0,220 × 2,1 × 19,6 = 9,06 kN/m`
`W_pier = (0,440 × 0,440 × 2,1 × 19,6) / 3,2 = 7,96 / 3,2 = 2,49 kN/m`
`W_masonry = 11,55 kN/m`
Try `B = 800 mm, d = 250 mm, D = 500 mm`:
`W_f = 4,80 kN/m`; `W_s ≈ 1,97 kN/m`; `N = 18,32 kN/m`
`F = 0,70 × 2,1 = 1,47 kN/m` at `1,05 + 0,50 = 1,55 m`
`M_ot = 2,28 kNm/m`; `M_r = 18,32 × 0,40 = 7,33 kNm/m` → **FoS = 3,21** ✔
`e = 2,28 / 18,32 = 0,124 m < 0,133 m` ✔

Under each pier, thicken locally: **1 000 × 1 000 × 300 pad**, cast monolithically with the strip, with 4 × Y12 each way bottom, cover 50 mm.
**Adopt: 800 × 250 strip at 500 mm depth, with 1 000 × 1 000 × 300 pads under piers.**

**Step 5 — everything else.**
Control joints at 7,0 m unreinforced or 10 m with brickforce; place them **mid-panel between piers, never at a pier**. Brickforce at 400 mm centres. Pier cores filled with grade 10 infill concrete over the full height, with 2 × Y12 starters lapped 480 mm from the pad. Coping as example 1, returned around the piers.

**Step 6 — quantities per metre run.**
Blocks: wall 2,1 m² + pier 0,44 × 2,1/3,2 = 0,29 m² → 2,39 m²/m at 10/m² ≈ **24 blocks/m**.
Concrete: strip 0,20 m³/m + pads 0,30/3,2 = 0,094 m³/m → **0,29 m³/m** ≈ 1,7 bags cement/m at 15 MPa (use 25 MPa for the pads).
Plaster: 4,2 m²/m plus pier returns ≈ 4,8 m²/m → **0,67 bag cement and 0,108 m³ sand per metre**.

## 10. Retaining-wall design basics

### Earth pressure fundamentals

Three states, all functions of the effective angle of internal friction `φ'`:

- **At rest** (rigid wall that cannot yield): Jaky's formula, `K₀ = 1 − sin φ'`. For φ' = 30°, `K₀ = 0,50`.
- **Active** (wall yields away from the soil by a few mm): Rankine, `K_a = tan²(45° − φ'/2) = (1 − sin φ')/(1 + sin φ')`. For φ' = 30°, `K_a = 0,333`.
- **Passive** (wall pushed into the soil): `K_p = tan²(45° + φ'/2) = (1 + sin φ')/(1 − sin φ')`. For φ' = 30°, `K_p = 3,0`.

Thrust on a wall of retained height `H` with backfill unit weight `γ`:
`P_a = ½ K_a γ H²`, acting at `H/3` above the base.

**Worked number.** Retained height 1,5 m, clean Kalahari sand, `γ = 18 kN/m³`, `φ' = 32°` → `K_a = 0,307`:
`P_a = 0,5 × 0,307 × 18 × 1,5² = 6,22 kN/m` at 0,50 m → `M = 3,11 kNm/m`.
If the wall is **rigid and cannot yield** (a masonry wall tied to a house, or a wall compacted hard against), use `K₀ = 1 − sin 32° = 0,470`: `P₀ = 9,52 kN/m`, `M = 4,76 kNm/m` — **53 % more**. This is the commonest silent error in small retaining walls.

Add to that:
- **Surcharge** `q`: uniform pressure `K_a q` over the full height. A car parked behind a wall is ~10 kPa; a truck 20 kPa. SANS 10400-K 4.2.4.1 sidesteps this by forbidding any surcharge within a distance equal to the retained height.
- **Water.** If the backfill saturates, hydrostatic pressure at 9,81 kN/m³ acts in full **plus** the buoyant soil pressure. A 1,5 m wall with a drowned backfill sees roughly `0,5 × 9,81 × 1,5² = 11,0 kN/m` of water thrust on top of about 3,5 kN/m of buoyant soil thrust — **more than double** the drained case. Nearly every small retaining wall failure is a drainage failure.
- **Compaction stresses.** Over-compacting behind a stiff wall with a heavy roller locks in pressures well above `K₀`. Use a light plate compactor within 1 m of the wall.

### Gravity, cantilever, reinforced soil, gabion

**Gravity.** Proportioning start: base width `B ≈ 0,5–0,7 H`, stem battered 1:12 to 1:6 into the fill, base thickness `≈ H/8`. Check overturning (FoS ≥ 2,0), sliding (FoS ≥ 1,5, using `μ ≈ tan(2φ'/3)` at the base), bearing (resultant in the middle third), and global stability.

**DTS masonry retaining walls (SANS 10400-K Table 16):**

| T (mm) | Type | Max height retained h (m) | Pier D × W (mm) | Max pier spacing (m) |
|---|---|---|---|---|
| 140 | Single-leaf | 1,3 | 600 × 300 | 1,8 |
| 190 | Collar-jointed | 1,3 | 600 × 300 | 2,5 |
| 190 | Collar-jointed | 1,6 | 600 × 400 | 2,6 |
| 220 | Collar-jointed | 1,7 | 660 × 330 | 3,0 |
| 220 | Collar-jointed | 1,8 | 880 × 440 | 3,1 |
| 290 | Collar-jointed | 1,0 | — | — |
| 300 | Collar-jointed | 1,2 | — | — |
| 140 (hollow) | Single-leaf | 1,1 | 600 × 300 | 1,8 |
| 190 (hollow) | Single-leaf | 1,1 | 600 × 300 | 2,5 |
| 190 (hollow) | Single-leaf | 1,4 | 800 × 400 | 2,6 |

Piers must project on the **side away from the fill**. Where the ground-level difference `x` exceeds 0,3 m, reduce the retained height by `(x − 0,3)`.

**Cantilever RC.** Base ≈ 0,5–0,7 H, heel long enough that soil weight on it provides the restoring moment, stem tapering from `H/12` at the base. Requires design; economic to ~6–8 m.

**Reinforced soil.** Geogrid layers at 400–600 mm vertical spacing, length ≈ 0,7 H, in granular fill compacted in 200 mm layers. Facing by segmental block, panel, or wrapped geotextile. Tolerant of settlement; fast; no formwork or curing.

**Gabion.** Base width ≈ 0,5 H for a vertical face, less if stepped and battered. Fill with hard, durable, angular rock 100–200 mm, hand-placed at the faces. Free-draining by nature — but still put a geotextile filter between the gabion and the retained soil or the fines will wash through and the fill will settle.

### Drainage — the non-negotiable

For any retaining wall, whatever the material:
1. **Free-draining backfill** — 19 mm clean stone or single-sized gravel in a zone at least 300 mm wide against the back of the wall, wrapped in geotextile.
2. **A perforated subsoil drain** (100 mm slotted uPVC) at the base of the drainage layer, laid to fall, discharging to daylight or a soakaway — not into the ground behind the wall.
3. **Weepholes** through the wall: SANS 10400-K requires **50 mm diameter plastic pipes** with geofabric on the buried end, **not more than 300 mm above the lower ground level**, at **not more than 1,5 m centres**.
4. **A surface seal** — the top of the backfill graded and either paved or sealed with a low-permeability layer so surface water does not enter the drainage zone.
5. **Waterproofing** on the retained face of a masonry or concrete wall, to stop damp and efflorescence bleeding through to the exposed face.

## 11. Failure modes that actually occur

Ranked roughly by frequency in southern African residential work:

1. **Foundation rotation in loose or wet ground.** The wall does not break; the footing tilts. Diagnostic: the wall is out of plumb but has no cracks, and the tilt increases after rain. Cause: shallow founding in loose sand, undersized base, no check on eccentricity. **This is the number-one boundary-wall defect and it is a design failure, not a workmanship one.**
2. **Overturning at a free end or gate opening.** The end-zone wind coefficient is 2–3 × the far field. A wall that stops without a pier or return falls first at that end. The code's requirement to terminate in a pier or return exists precisely for this.
3. **Shrinkage/expansion cracking at 5–8 m intervals** because control joints were omitted or spaced at building rather than freestanding-wall centres. Vertical, full-height, often at a weak point such as a small pier.
4. **Base bed-joint failure from poor mortar bond.** Dry, dusty, or over-stiff mortar; laying concrete units wet (which must not be done) or clay units dry (which must not be done); furrowed bed joints instead of full beds. The wall snaps off at or near the base in wind.
5. **Coping failure** — no drip, no overhang, unbedded units. Staining first, saturation of the top courses next, then units lifting in wind.
6. **Retaining-wall drainage failure.** Weepholes blocked at construction with mortar droppings, no filter fabric, no drainage layer. Failure is progressive: bulge, then rotation, then collapse — usually in the first heavy rain after a dry year.
7. **Differential movement where the wall abuts a building or a gate pier**, because the two are founded differently and no articulation joint was provided.
8. **Post rotation in precast panel walls.** Post holes too small and too shallow, filled with weak concrete or with soil. The whole run leans.
9. **Impact damage** — a vehicle at a gate, a fallen tree. Precast panel walls take this best (replace one panel); face brickwork takes it worst.
10. **Corrosion of brickforce, ties and cramps** near the coast or in polluted air, causing horizontal cracking along a bed joint.

## Sources

- [SANS 10400-K:2011 — Part K: Walls](https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html) — SABS, via Internet Archive (clauses 3.22, 4.2.1.1–4.2.1.5, 4.2.4.1–4.2.4.3, 4.2.5, 4.2.6.1–4.2.6.9, Tables 16, 17, 18, 19)
- [Quantities for ordering building materials](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf) — Cement & Concrete SA (Tables 1a–1d, 2, 3)
- [Concrete, plaster and mortar mixes for builders](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf) — Cement & Concrete SA
- [Lateral earth pressure](https://en.wikipedia.org/wiki/Lateral_earth_pressure) — Wikipedia (Jaky, Rankine, Coulomb coefficients)
- [Mechanically stabilized earth](https://en.wikipedia.org/wiki/Mechanically_stabilized_earth) — Wikipedia
- Watermeyer, R.B. *Free-standing walls — a design guide.* Concrete Masonry Association, 1993 — cited in the bibliography of SANS 10400-K; **not obtained**, and it is the definitive southern African reference on this subject. Obtain it.

## Open questions

- **Design wind pressure.** The 0,70 kN/m² used in the worked examples is an assumption. Read the fundamental basic wind speed for Ohangwena from **SANS 10160-3 Annex A** and derive `q_p` and `c_f` properly, including the end-zone coefficients. `needs-verification`
- **Permissible flexural tensile stress** for masonry normal to bed joints with Class II mortar in the SANS framework was not obtained from a primary source; 0,10 MPa is used as a conservative working value. `needs-verification`
- **SANS 10400-H foundation tables** were not machine-readable in this pass. The foundation schedule here is derived from first principles and should be checked against Part H. `needs-verification`
- Table 19's clay/reinforced row (16 → 6 m) reads anomalously in the transcribed text; verify against a clean copy of the standard.
- Watermeyer's *Free-standing walls — a design guide* (CMA, 1993) should be obtained and this file reconciled with it.
