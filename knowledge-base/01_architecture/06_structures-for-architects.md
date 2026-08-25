---
id: arch.structures
title: Structures for architects — load paths and preliminary sizing
domain: architecture
tags: [structures, load-path, dead-load, live-load, wind-load, spans, beams, columns, slabs, foundations, lintels, lateral-stability, movement-joints, sans-10160, sans-10400-k]
jurisdiction: southern-africa
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SANS 10160-4 (draft) — Seismic actions and general requirements for buildings", url: "https://civils.org.za/Portals/0/pdf/publications/sans/SANS10160-4_dss.pdf", publisher: "SABS / SAICE", accessed: 2026-08-25}
  - {title: "Review of compatibility between SANS 10400 deemed-to-satisfy masonry wall provisions and loading code", url: "https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1021-20192021000100005", publisher: "Journal of the South African Institution of Civil Engineering (SciELO SA)", accessed: 2026-08-25}
  - {title: "Span to depth ratio of slabs and beams", url: "https://sheerforceeng.com/2021/11/26/span-to-depth-ratio-of-slabs-and-beams/", publisher: "Sheer Force Engineering", accessed: 2026-08-25}
  - {title: "SANS 10160 loading — transcription", url: "https://pdfcoffee.com/sans10160-loadings-pdf-free.html", publisher: "SABS (third-party transcription)", accessed: 2026-08-25}
related: [arch.design_fundamentals, arch.building_science]
unit_system: metric
---

# Structures for architects — load paths and preliminary sizing

**Summary.** An architect does not design structure, but must be able to (a) trace a load path from roof to soil, (b) reserve realistic depths and column positions at concept stage, and (c) argue with an engineer using the right vocabulary and the right order of magnitude. This file gives characteristic loads, span-to-depth rules of thumb for timber, steel, concrete and masonry, guidance on lintels, columns, foundations, lateral stability and movement joints — enough to size elements to about ±25%, which is the right accuracy for a concept.

> ⚠️ **Nothing in this file is a design.** Every element must be designed and signed off by a registered professional engineer. Preliminary sizing is for coordination, not for construction.

## 1. Load path

Every load must reach the ground by a continuous, downward, resolvable path:

`Cladding/finish → secondary member (purlin, joist, rib) → primary member (beam, truss, rafter) → vertical element (column, wall) → foundation → soil`

Three tests at concept stage:
1. **Continuity.** Does every column land on something below, all the way down? A column that dies on a beam is a *transfer*, and transfer beams are large and expensive.
2. **Directness.** Cantilevers and transfers cost depth and money. A cantilever costs about the same depth as a back-span **2,5–3 ×** its length.
3. **Stability.** Is there a lateral system in **both orthogonal directions** on every level?

## 2. Loads

**Dead (permanent) loads** — self-weight, typical:

| Element | Load |
|---|---|
| Reinforced concrete | 24 kN/m³ |
| Solid clay brickwork | 18–20 kN/m³ |
| Concrete masonry (solid) | 20–22 kN/m³ |
| Softwood timber | 5–6 kN/m³ |
| Structural steel | 78,5 kN/m³ |
| 230 mm brick wall, plastered both sides | ≈ 4,5–5,0 kN/m² of wall |
| 150 mm RC slab + screed + finishes | ≈ 4,5–5,0 kPa |
| Sheet metal roof, purlins, insulation, ceiling | ≈ 0,3–0,5 kPa |
| Concrete roof tiles on timber, with ceiling | ≈ 0,8–1,0 kPa |
| Services and ceiling allowance | 0,3–0,5 kPa |
| Movable partitions allowance | 1,0 kPa |

**Imposed (live) loads — [ZA] SANS 10160-2:**

| Use | q_k (kPa) | Concentrated Q_k |
|---|---|---|
| Residential | 1,5 | 1,0 kN over 100 × 100 mm |
| Offices, general | 2,3 | 3,0 kN over 100 × 100 mm |
| Offices with data-processing equipment | 4,0 | 3,0 kN |
| Assembly, fixed seating | 4,0 | 3,0 kN |
| Assembly, no fixed seating | 5,0 | 3,0 kN |
| Retail sales and display | 5,0 | 0,75 kN over 750 × 750 mm |
| Storage | ≥ 5,0, by material and stacking | — |
| Flat roof, accessible | 2,0 | — |
| Roof, inaccessible except for maintenance | 0,3–0,5, by tributary area | — |

*(1 kN/m² = 1 kPa.)*

**Wind — [ZA] SANS 10160-3.** Fundamental basic wind speeds of **36, 40 and 44 m/s** are used across South Africa. The deemed-to-satisfy masonry route in SANS 10400-K assumes minimum design pressures of **370 N/m² for housing structural systems** and **450 N/m² for housing elements**. Wind governs light roofs: **uplift** on a sheet roof at the edges and corners routinely exceeds the dead load, which is why holding-down straps and correctly specified fixings — not the sheets themselves — are the critical items.

**Seismic — [ZA] SANS 10160-4.** Zone I (natural seismicity) uses a reference peak ground acceleration of **0,1 g**; Zone II covers mining-induced and natural seismicity. Importance factors γ_I: Class I 0,8; Class II 1,0; Class III (schools, assembly halls) 1,2; Class IV (hospitals, power plants) 1,4. Behaviour factor q ranges 1,0 (elastic) to 5,0 (RC walls with special detailing). Storey drift limits: ≤ 0,025 h_s if T < 0,7 s; ≤ 0,020 h_s if T ≥ 0,7 s. Simple masonry buildings: minimum wall thickness **190 mm solid / 150 mm cavity**; height-to-thickness ratio ≤ 17; minimum shear wall area **2,5% of floor area (2 storeys), 5% (3 storeys)**. Namibia's seismicity is low but non-zero; confirm the applicable regime with the engineer.

**Load combinations** are the engineer's responsibility, but note that ultimate limit state factors (typically ~1,2 dead + 1,6 imposed in the SA convention) size the members, while serviceability (deflection, cracking, vibration) frequently governs the *depth* — which is what the architect cares about.

## 3. Span-to-depth rules of thumb

Structural depth ≈ span / ratio. Use these to reserve space in section at concept.

**Reinforced concrete:**

| Element | Single span | One end continuous | Both ends continuous | Cantilever |
|---|---|---|---|---|
| One-way slab | L/22 | L/28 | L/33 | L/10 |
| Band beam | L/15 | L/20 | L/25 | L/7 |
| Flat slab (with drops) | — | L/29 | L/35 | — |
| Flat plate (no drops) | — | L/27 | L/32 | — |
| Beam, normal | L/12 – L/15 | L/15 – L/18 | L/18 – L/20 | L/6 |
| Two-way slab (on beams) | L/30 – L/35 (short span) | | | |

**Post-tensioned concrete:**

| Element | Single span | One end continuous | Both ends continuous | Cantilever |
|---|---|---|---|---|
| One-way slab | L/28 | L/35 | L/40 | L/12 |
| Band beam | L/18 | L/25 | L/30 | L/8 |
| Flat slab | — | L/38 | L/45 | — |
| Flat plate | — | L/33 | L/40 | — |

**Steel:**

| Element | Depth |
|---|---|
| Floor beam | L/20 – L/23 |
| Roof beam / purlin | L/32 – L/35 |
| Composite beam (steel + slab) | L/24 – L/27 |
| Plate girder | L/10 – L/14 |
| Trussed girder | L/6 – L/10 |
| Roof truss (pitched) | L/5 – L/8 overall |
| Space frame | L/15 – L/25 |
| Portal frame rafter | L/40 – L/55 (haunched at knee) |

**Timber (rules of thumb; always confirm against a species/grade span table):**

| Element | Depth |
|---|---|
| Floor joist | L/15 – L/20 |
| Roof rafter | L/20 – L/24 |
| Glulam beam | L/16 – L/20 |
| Timber truss (nail-plated, pitched) | L/4 – L/6 overall |
| Purlin | L/25 – L/30 |

**Masonry:**
- Loadbearing wall slenderness ratio (effective height / effective thickness) typically limited to **≤ 27** in design, and to **≤ 17** for simple seismic-rule buildings **[ZA]** SANS 10160-4.
- **[ZA]** SANS 10400-K deemed-to-satisfy route for Category 1 buildings: floor area ≤ **80 m²**, wall lengths < **6 m** between lateral supports, **single storey, no basement**, wall thickness as little as **90 mm**. Non-Category-1 buildings require **140 mm**. Maximum window opening length **3 m**; total openings **< one third** of the wall area.

### Typical concept-stage depths

| Span | RC flat slab | RC beam | Steel beam | Timber joist |
|---|---|---|---|---|
| 3,0 m | 110–130 mm | 200–250 mm | 150 mm | 150–200 mm |
| 4,5 m | 160–180 mm | 300–375 mm | 200–250 mm | 225–250 mm |
| 6,0 m | 200–230 mm | 400–500 mm | 250–300 mm | 300 mm (glulam) |
| 7,5 m | 250–280 mm | 500–625 mm | 350 mm | glulam / truss |
| 9,0 m | 300–330 mm (PT preferable) | 600–750 mm | 400–450 mm | truss |
| 12,0 m | PT slab 300–350 mm | 800–1 000 mm | 530–610 mm | truss / portal |

Add **50–150 mm** to any structural depth for services zone plus ceiling when setting floor-to-floor heights. A 3 000 mm clear ceiling with a 250 mm slab and a 400 mm services zone means a **3 650 mm floor-to-floor**, not 3 250 mm — get this right before fixing levels.

## 4. Lintels, beams, columns

**Lintels.** Bearing: minimum **150 mm each end** for openings up to about 1,2 m; **200 mm** beyond. Precast prestressed concrete lintels in **[ZA]/[NA]** come in standard 110 mm and 220 mm depths; combine with a composite brick course above for larger spans. For openings above ~2,4 m, or where a slab or roof bears directly over, use a designed RC or steel lintel. Above every external lintel in a cavity wall, place a **cavity tray with weep holes at ≤ 900 mm centres**.

**Beam proportion.** Practical RC beam width ≈ **0,4–0,6 × depth**, and ≥ the wall thickness it sits in (230 mm is the natural minimum in brick construction). Steel beams: check lateral-torsional buckling — an unrestrained top flange over 6 m needs restraint or a larger section.

**Columns.** Preliminary RC column size: area ≈ `N / (0,4 f_cu)` where N is the ultimate axial load. Simpler concept rule: a square RC column carrying a tributary floor area of A m² over n storeys, at ~10 kPa total ultimate load, needs roughly **√(10 × A × n / 12) × 1 000 mm** per side for 30 MPa concrete — round up to 230, 300, 400, 500 mm. Slenderness: keep effective length / least dimension ≤ 15 for a "short" column.

**Grid selection.** Efficient RC flat-slab grids: 6,0 × 6,0 to 8,4 × 8,4 m. Steel office grids: 7,5 × 15,0 or 9,0 × 12,0 m. Parking: **7,8–8,4 m** bays (three cars) × 15,6–16,0 m (two bays plus aisle). Choosing a grid that suits both the parking and the floor above avoids transfer structure — the single largest structural cost saving available to an architect.

## 5. Slabs and floors

| System | Economic span | Notes |
|---|---|---|
| Suspended timber floor | 3–5 m | Light, fast, needs ventilation beneath |
| Precast hollow-core | 6–12 m | Fast, no propping, needs crane access |
| Rib-and-block (beam-and-block) | 4–7 m | Common in **[ZA]/[NA]** residential; minimal formwork |
| In-situ one-way slab on beams | 4–7 m | |
| Flat plate | 5–7,5 m | Flat soffit; punching shear governs |
| Flat slab with drops | 6–9 m | |
| Post-tensioned flat slab | 8–12 m | Thin, but requires specialist contractor |
| Composite steel deck | 3–4 m (deck) / 9–12 m (beams) | |
| Waffle / coffered slab | 9–15 m | Deep but light; expressive soffit |

## 6. Foundations

| Type | Use | Typical dimension |
|---|---|---|
| Strip footing | Loadbearing masonry on competent soil | Width 600–900 mm, thickness ≥ 200 mm, projection ≤ thickness for unreinforced |
| Pad footing | Isolated columns | Sized on `Area = N / allowable bearing pressure` |
| Raft | Poor or variable soil, expansive clay, light structures | 200–400 mm with edge beams/stiffeners |
| Piled | Deep competent stratum, high loads, collapsible soils | Design by specialist |

Indicative allowable bearing pressures: soft clay 75–100 kPa; firm clay 100–150 kPa; stiff clay 150–300 kPa; loose sand 100 kPa; dense sand 300–600 kPa; weathered rock 600 kPa+; sound rock ≫ 1 000 kPa. **These are for concept only — a geotechnical investigation is mandatory.**

Founding depth: below the zone of seasonal moisture movement and below any topsoil — commonly **≥ 600 mm** in stable ground, deeper in expansive clay. Southern African hazards to raise with the engineer: **expansive (heaving) clays**, **collapsible sands** (widespread in Namibia and the SA interior), **dolomite** (sinkhole risk, **[ZA]** parts of Gauteng and North West), and **calcrete** (hard, variable, difficult to excavate).

## 7. Lateral stability

Every building needs a lateral load-resisting system in **two orthogonal directions**, on **every storey**, with a continuous path to the foundations. Options:
- **Shear walls** — most efficient; stair and lift cores are the natural location. Reserve them at concept.
- **Braced frames** — cross, K, or eccentric bracing; cheap in steel, visually intrusive.
- **Moment frames** — architecturally free, but heavy members and large connections.
- **Diaphragm action** — floor slabs distribute load to the vertical elements; large floor openings (atria, voids) break the diaphragm and need a designed collector.

Rules: keep the **centre of rigidity close to the centre of mass** (offset creates torsion); provide bracing **symmetrically**; avoid a **soft storey** (an open ground floor under stiff floors above) — this is a classic collapse mechanism; **[ZA]** for simple masonry buildings SANS 10160-4 requires shear wall area ≥ 2,5% of floor area at 2 storeys and 5% at 3 storeys.

## 8. Movement joints

| Material | Typical joint spacing |
|---|---|
| Clay brickwork (expands, irreversibly) | 10–12 m; within 3–6 m of a corner |
| Concrete masonry (shrinks) | ≈ 6 m; at changes in wall height/thickness and at openings |
| In-situ concrete (shrinkage) | Pour strips or joints at 25–40 m |
| Structural movement joint (whole building) | 30–50 m, or at any change in height, foundation type or structural system |
| Screeds and tiling | Bay size ≤ 5 × 5 m; joint over every structural joint |
| Profiled metal roof sheeting | Slotted fixings; expansion ≈ 0,024 mm/m·K for steel |

Joints must pass **through every layer** — structure, masonry, screed, finish, waterproofing — or they will simply relocate the crack. Detail them from the outset; a movement joint retrofitted after cracking is a repair, not a design.

## 9. Talking to the engineer — the checklist

Bring these to the first structural meeting:
1. Proposed grid and column positions, with the parking grid overlaid.
2. Floor-to-floor heights and the required clear ceiling height.
3. Spans you want and the ones you will accept.
4. Cantilevers and transfers you are proposing, with lengths.
5. Locations you are reserving for shear walls or bracing.
6. Loads that are not standard — plant, water tanks, green roof, library stacks, vehicles.
7. Locations where structure will be exposed (this changes finish, cover, and cost).
8. The geotechnical report, or a commitment to commission one.
9. Service zone depths agreed with the mechanical and electrical engineers.
10. Movement joint strategy.

## Sources

- [SANS 10160-4 (draft) — Seismic actions](https://civils.org.za/Portals/0/pdf/publications/sans/SANS10160-4_dss.pdf) — SABS / SAICE
- [Review of compatibility between SANS 10400 deemed-to-satisfy masonry wall provisions and loading code](https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1021-20192021000100005) — Journal of the SAICE, SciELO SA
- [Span to depth ratio of slabs and beams](https://sheerforceeng.com/2021/11/26/span-to-depth-ratio-of-slabs-and-beams/) — Sheer Force Engineering
- [SANS 10160 loading — third-party transcription](https://pdfcoffee.com/sans10160-loadings-pdf-free.html) — SABS (transcription)
- [SANS 10400-M: Stairways](https://ndlambe.gov.za/wp-content/uploads/2023/07/SANS-10400-PART-M-STAIRWAYS.pdf) — SABS via Ndlambe Municipality

## Open questions

- The SANS 10160-2 imposed-load table was read from a **third-party transcription**, not from SABS. Values (including the unusual 2,3 kPa for general offices) must be checked against the published standard before use. This is why the file is marked `status: draft`, `confidence: medium`.
- SANS 10160-3 wind pressure coefficients, terrain categories and the map of fundamental basic wind speeds were not obtained; only the three basic wind speeds (36/40/44 m/s) and the SANS 10400-K minimum pressures are cited.
- SANS 10400-K deemed-to-satisfy tables (wall height/length/thickness matrices) were not read directly; the Category 1 limits quoted come from a peer-reviewed review paper, not the standard itself.
- Dead-load, bearing-pressure, column-sizing and movement-joint figures are conventional engineering practice values and are **not** cited to a standard. Treat as order-of-magnitude only.
- **[NA]** Namibia's applicable loading code (whether SANS 10160 is adopted, or another regime applies) was not established.

