---
id: walls.specifying
title: Specifying and costing a boundary wall
domain: 16_walls_and_boundaries
tags: [measurement, take-off, quantities, bill-of-quantities, boq, rates, build-rates, tolerances, quality-clauses, specification-template, preliminaries, provisional-sums]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SANS 10400-K:2011 The application of the National Building Regulations Part K: Walls", url: "https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html", publisher: "SABS / Internet Archive", accessed: 2026-08-25}
  - {title: "Quantities for ordering building materials", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Concrete, plaster and mortar mixes for builders", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Successful plastering", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Successful-plastering-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Ohorongo Cement — products", url: "https://ohorongo-cement.com/products/", publisher: "Ohorongo Cement (Pty) Ltd", accessed: 2026-08-25}
  - {title: "CENTURION sliding gate motors", url: "https://www.centsys.co.za/demo/centurion-systems-sliding-gate-motors/", publisher: "Centurion Systems", accessed: 2026-08-25}
related: [walls.boundary_design, walls.construction, walls.companies, walls.namibia]
unit_system: SI
---

# Specifying and costing a boundary wall

**Summary.** A boundary wall is priced badly more often than it is built badly, and the two are related — a price that omits the foundation, the control joints, the curing and the coping buys a wall that omits them. This file gives a complete method: how to measure the run, quantities per linear metre for each wall type (built from the Cement & Concrete SA tables), foundation quantities, gate and pier allowances, build rates for programming labour, a bill-of-quantities structure, quality clauses and tolerances, and a reusable specification template you can copy and fill in.

## Key facts — the quantity constants

| Constant | Value | Source |
|---|---|---|
| Class II mortar per m³ (common cement) | **7 × 50 kg bags + 1,35 m³ sand** | C&CSA Table 2 |
| Class II mortar per m³ (masonry cement 22,5X) | **10 bags + 1,25 m³ sand** | C&CSA Table 2 |
| Class I mortar per m³ (common cement) | **10 bags + 1,25 m³ sand** | C&CSA Table 2 |
| External plaster per 100 m² at 15 mm (common cement) | **700 kg (14 bags) + 2,25 m³ sand** | C&CSA |
| Internal plaster per 100 m² at 15 mm (common cement) | **600 kg (12 bags) + 2,3 m³ sand** | C&CSA |
| 15 MPa concrete per m³ (32,5 cement, 19 mm stone) | **5,8 bags + 0,65 m³ sand + 0,65 m³ stone** | C&CSA Table 1a |
| 25 MPa concrete per m³ (32,5 cement, 19 mm stone) | **7,7 bags + 0,62 m³ sand + 0,62 m³ stone** | C&CSA Table 1a |
| 30 MPa concrete per m³ (32,5 cement, 19 mm stone) | **9,2 bags + 0,60 m³ sand + 0,60 m³ stone** | C&CSA Table 1a |
| 15 MPa 2-bag batch yield | **0,35 m³** (3½ barrows sand + 3½ barrows stone) | C&CSA Table 1a |
| Builder's type 5 wheelbarrow (SANS 795) | **65 ℓ** | C&CSA |
| Mortar wastage allowance | **20–50 %** | C&CSA |
| Mortar reduction for hollow units | 90–110 mm: **−20 %**; 140 mm: **−30 %**; 190–220 mm: **−40 %** | C&CSA |
| Mortar increase, perforated units or frog laid up | **+15 %** | C&CSA |
| Mortar for 15 mm joints / 20 mm joints | **× 1,5** / **× 2,0** | C&CSA |
| Ready-mixed mortar delivered in watertight containers | **−20 %** vs site-mixed | C&CSA |
| Curing | **≥ 7 days**, longer in cold weather | C&CSA |

## 1. Measuring the run

Do this on site, with a tape and a level, not off a plan.

1. **Walk and chain the whole boundary**, recording distances between changes of direction. Record the bearing or the internal angle at each corner.
2. **Level along the run** at 5 m intervals and at every change of grade, from a single site datum. This produces the long section, which is what determines the stepping (file `04`, §2) and the true wall area.
3. **Record ground level on both sides** at each station. The difference `x` matters: SANS 10400-K reduces the permitted freestanding height by `(x − 0,3 m)` wherever `x` exceeds 0,3 m.
4. **Record obstructions** — trees to be kept or removed, existing structures, services, the driveway, the water line, drainage crossings.
5. **Fix the gate positions and widths** now. They change the measured length and they change the pier schedule.
6. **Photograph** every station with a ranging rod in shot.

**Measured length** is the **centre-line length** of the wall for masonry, taken through corners; deduct the clear opening width of each gate. Piers are measured as **extra over** the wall, in number, not by length.

**Measured area** is `length × average height above finished ground`. Use the long section, not the maximum height, or you will over-order by 10–20 % on a sloping run.

## 2. Quantities per linear metre — masonry walls

All figures are **per metre run of wall**, for **10 mm joints**, **before wastage**, using Cement & Concrete SA Table 3 unit densities and Class II mortar. Multiply by the number of metres, then add wastage.

### At 1,8 m high

| Wall | Unit size (mm) | Units/m² | Units/m run | Mortar m³/100 m² | Mortar m³/m run | Cement bags/m run | Sand m³/m run |
|---|---|---|---|---|---|---|---|
| 110 mm solid | 440 × 110 × 220 | 10 | **18,0** | 0,75 | 0,0135 | 0,095 | 0,018 |
| 140 mm hollow | 390 × 190 × 140 | 13 | **23,4** | 1,05 − 30 % = 0,735 | 0,0132 | 0,093 | 0,018 |
| 190 mm hollow | 390 × 190 × 190 | 13 | **23,4** | 1,43 − 40 % = 0,858 | 0,0154 | 0,108 | 0,021 |
| 220 mm solid | 440 × 220 × 220 | 10 | **18,0** | 1,50 | 0,0270 | 0,189 | 0,036 |
| 220 mm, two leaves imperial brick | 222 × 106 × 73 | 2 × 52 = 104 | **187** | 2 × 1,51 = 3,02 | 0,0544 | 0,381 | 0,073 |
| 290 mm solid | 290 × 140 × 140 | 23 | **41,4** | 1,41 | 0,0254 | 0,178 | 0,034 |
| 90 mm | 390 × 190 × 90 | 25 | **45,0** | 2,38 − 20 % = 1,90 | 0,0342 | 0,239 | 0,046 |

### At 2,1 m high

Multiply the "units/m run" and "per m run" columns above by **2,1 / 1,8 = 1,167**. Then add the pier quantity.

| Wall | Units/m run at 2,1 m | Mortar m³/m run |
|---|---|---|
| 110 mm solid (440 × 110 × 220) | 21,0 | 0,0158 |
| 190 mm hollow (390 × 190 × 190) | 27,3 | 0,0180 |
| 220 mm solid (440 × 220 × 220) | 21,0 | 0,0315 |

### Piers — extra over

A pier is measured as **number**, priced as extra over the wall it replaces.

For a **660 × 440 mm** pier on a **220 mm** wall at **2,1 m** high, the projecting part is 440 × 440 mm:
- Projecting masonry volume = 0,440 × 0,440 × 2,1 = **0,407 m³ per pier**
- At 10 units/m² × 2,1 m² of extra face ≈ **9 extra units per face**; for a full-height pier expect **18–24 extra units per pier** including bonding into the wall
- Infill concrete to fill hollow pier cores, if hollow units: allow **0,10–0,15 m³ per pier** of grade 10 infill concrete
- Reinforcement: **2 × Y12 × (2,1 + 0,48 lap) = 5,2 m per pier**

For a **550 × 330 mm** pier on a **110 mm** wall at **1,9 m**: projecting part 440 × 330 mm, volume 0,276 m³/pier.

**Pier count** = (wall length ÷ permitted spacing) + 1, **plus** one at every free end, **plus** two at every gate opening, **plus** one at every corner. Do not economise on this count.

### Wastage

| Item | Allowance |
|---|---|
| Masonry units, machine-made, palletised | **5 %** |
| Masonry units, locally made, loose-loaded | **8–12 %** |
| Mortar, good supervision | **20 %** |
| Mortar, ordinary supervision | **30 %** |
| Mortar, poor supervision | **50 %** |
| Plaster | **15–20 %** |
| Concrete, hand-batched into trench | **7,5–10 %** |
| Brickforce, coping, sundries | **5 %** |

## 3. Quantities per linear metre — foundations

For a strip footing `B` wide × `d` thick at founding depth `D`:

- **Excavation (m³/m)** = `B × D`
- **Concrete (m³/m)** = `B × d`
- **Cement (bags/m)** = concrete m³ × 5,8 (15 MPa) or × 7,7 (25 MPa)
- **Sand and stone (m³/m)** = concrete m³ × 0,65 each (15 MPa)
- **Backfill (m³/m)** = `B × (D − d)` less the wall thickness × its buried height
- **Cart away (m³/m)** = excavation − backfill, **bulked by 25–35 %** for sand

Worked, for the file `03` example 1 footing (800 × 250 at 450 mm depth):

| Item | Per m run |
|---|---|
| Excavation | 0,800 × 0,450 = **0,360 m³** |
| Concrete 15 MPa | 0,800 × 0,250 = **0,200 m³** |
| Cement | 0,200 × 5,8 = **1,16 bags** |
| Concrete sand | 0,200 × 0,65 = **0,130 m³** |
| Stone 19 mm | 0,200 × 0,65 = **0,130 m³** |
| Backfill | ≈ **0,12 m³** |
| Cart away (bulked) | ≈ **0,05 m³** |

**Pier pads** (1 000 × 1 000 × 300): excavation 0,30 m³ each (plus working space), concrete **0,30 m³** each, 25 MPa = **2,31 bags** each, reinforcement 4 × Y12 each way = 8 × 0,90 m = **7,2 m** each.

## 4. Quantities per linear metre — finishes and sundries

| Item | Quantity |
|---|---|
| Plaster, both sides, 1,8 m wall | 3,60 m²/m → **0,504 bag cement + 0,081 m³ sand** per m run (external mix) |
| Plaster, both sides, 2,1 m wall | 4,20 m²/m → **0,588 bag + 0,095 m³ sand** |
| Bagging (rub-up), both sides, 1,8 m | 3,60 m²/m → allow **0,10 bag cement + 0,015 m³ fine sand** per m run `needs-verification` |
| Paint, 2 coats, both sides, 1,8 m | 3,60 m²/m → at 6 m²/ℓ/coat = **1,2 ℓ/m run** |
| Brickforce at 400 mm centres, 1,8 m wall | 4 courses reinforced → **4,2 m/m run** including 150 mm laps |
| Brickforce at 400 mm centres, 2,1 m wall | 5 courses → **5,3 m/m run** |
| Coping / capping units | **1 m/m run** + 5 % |
| Control joints | 1 no. per 7,0 m (concrete masonry, unreinforced) or per 10 m (with brickforce) |
| Control joint materials | backer rod + sealant: **1,8–2,1 m of joint** per joint per side |
| Curing water | allow **5–8 ℓ/m² of wall** over the 7-day cure `needs-verification` |

## 5. Gate and pier allowances

Gates are priced as **items**, not by the metre, and they routinely carry 25–40 % of the cost of a residential boundary contract.

| Item | Basis | Notes |
|---|---|---|
| Vehicle gate leaf | Item, per gate | State clear opening, height, frame section, infill, finish, and **mass** |
| Pedestrian gate leaf | Item | Include lock, keeps, and closer if wanted |
| Gate piers | Number | 440 × 440 min., filled cores, 4 × Y12, on 1 000 × 1 000 × 400 pad |
| Gate pier pads | Number | Reinforced 25 MPa |
| Hinges / rollers | Item, per gate | Adjustable, sealed bearings, bottom pin retainer |
| Sliding gate track or cantilever brackets | Item | Cantilever needs **1,4–1,5 × opening** of run-back |
| Gate operator | Item | Model sized on **actual mass** (file `04`, §8) |
| Safety infrared beams | Item, per pair | **Never** an optional extra |
| Remotes | Number | Code-hopping only |
| Intercom | Item | Hard-wired or GSM |
| Battery + PV maintenance panel | Item | Essential where supply is intermittent |
| Sleeves under driveway | m | 32 mm + 25 mm, **before paving** |
| Electrical connection to operator | Item | By a competent electrician |
| Commissioning and handover | Item | Force settings recorded, beams tested, demonstration |

**Provisional sum items** worth carrying separately: electric fence installation and certification; lighting; landscaping and making good; and any rock excavation.

## 6. Labour and build rates

Planning rates for programming and for checking a contractor's resourcing. `needs-verification` — calibrate against local performance.

| Activity | Output per person-day (8 h) |
|---|---|
| Hand excavation in sand, trench ≤ 600 mm deep | 3–5 m³ |
| Hand excavation in calcrete or hard material | 0,8–1,5 m³ |
| Hand-mixing and placing concrete in trench | 1,5–2,5 m³ (mixer + gang of 4) |
| Bricklaying, 440 × 220 × 220 solid blocks | 100–140 blocks (10–14 m²) |
| Bricklaying, 390 × 190 × 190 hollow blocks | 130–180 blocks (17–24 m²) |
| Bricklaying, imperial brick, half-brick wall | 400–550 bricks (8–11 m²) |
| Bricklaying, imperial brick, one-brick wall | 450–600 bricks (4–6 m²) |
| Face brickwork, fair one side | 300–400 bricks |
| Piers and cut work | Deduct **25–35 %** from the straight-run rate |
| Plastering, 15 mm on masonry | 15–22 m² |
| Bagging / rub-up | 40–60 m² |
| Painting, 1 coat | 60–90 m² |
| Bedding coping units | 25–40 m |
| Fixing brickforce | Incidental to bricklaying |
| Setting precast walling posts and panels | 8–15 m of wall (2-person crew) |
| Erecting palisade fencing | 8–12 m (2-person crew) |

**Gang composition** for masonry: 1 bricklayer : 1 labourer for blockwork; 1 : 1,5 for brickwork; plus 1 chargehand per 4–6 bricklayers; plus one mixer operator per 3 bricklayers.

## 7. Bill of quantities structure

Use this structure whether you are producing a BoQ or checking a contractor's quotation. Anything missing from a quotation is a variation waiting to happen.

**A — Preliminaries and general**
1. Site establishment, storage, security of materials
2. Setting out, profiles, datum peg, boundary confirmation
3. Water for the works, including curing water (state source and who pays)
4. Temporary works, propping and bracing
5. Health and safety, PPE, first aid
6. Insurances and guarantees
7. Sample panel — build, approve, retain until practical completion
8. Cleaning and making good on completion

**B — Site clearance and earthworks**
9. Clear and grub the wall line, 1,5 m each side — m
10. Grub up and remove tree stumps — number, by girth band
11. Excavate trench for strip footings, not exceeding 1,0 m deep — m³
12. Excavate for pier and gate pier pads — m³
13. Extra over all excavation for excavation in hard material — m³ (provisional)
14. Keep excavations free of water — item
15. Compact trench bottoms — m²
16. Backfill and compact in 150 mm layers — m³
17. Cart away surplus spoil — m³

**C — Concrete, formwork and reinforcement**
18. 15 MPa/19 mm concrete in strip footings — m³
19. 25 MPa/19 mm concrete in pier pads and gate pier pads — m³
20. Grade 10 infill concrete to pier cores — m³
21. Formwork to footing steps and edges — m²
22. High-tensile bar reinforcement, Y10 / Y12 — kg or m
23. Starter bars cast into footings, including laps — number

**D — Masonry**
24. Concrete masonry, [thickness] mm, in Class II mortar, in freestanding wall — m²
25. Extra over walls for piers, [size], full height, cores filled — number
26. Extra over walls for gate piers, [size], reinforced — number
27. Bed-joint reinforcement (brickforce), [type], at 400 mm centres — m
28. Vertical control joints, [width], including backer rod and sealant both sides, extending to top of foundation — m
29. Coping / capping units, bedded and jointed, including joints over control joints — m
30. Building in sleeves, conduits and pipe ducts — number

**E — Finishes**
31. External cement plaster, 15 mm, to walls — m²
32. Bagging / rub-up to walls — m²
33. Prepare and apply [system] paint, 2 coats — m²
34. Curing — item (or included in the above rates, **stated explicitly**)

**F — Gates and metalwork**
35. Vehicle gate, [width] × [height], to detail — item
36. Pedestrian gate, [width] × [height], to detail — item
37. Hinges, rollers, guides, locks, keeps — item
38. Hot-dip galvanizing / paint system to all steelwork — item

**G — Fencing (if applicable)**
39. Palisade / mesh fencing, [height], including posts and footings — m
40. Straining posts, corner posts, end posts — number
41. Precast panel-and-post walling, [height], including post footings — m

**H — Electrical and access control**
42. Sleeves under driveway and paving — m
43. Supply and install gate operator, [model] — item
44. Safety infrared beams — pair
45. Intercom / keypad / remotes — item
46. Battery and PV maintenance panel — item
47. Boundary lighting — number
48. Commissioning, testing and handover — item

**J — Provisional sums and contingencies**
49. Electric fence installation and certification — provisional sum
50. Rock excavation — provisional sum
51. Landscaping and making good — provisional sum
52. Contingency — **10 %** of the measured work, **15 %** where no trial holes have been dug

> ⚠️ The measurement conventions above follow ordinary southern African building-measurement practice. The formal reference is the **ASAQS Standard System of Measuring Building Work**; that document was not obtained in this pass, so the item descriptions here are practical rather than SMM-compliant. `needs-verification`

## 8. Worked take-off — 40 m boundary, 1,8 m, 220 mm blockwork

Basis: file `03` worked example 1. Total boundary 40,0 m; two vehicle gate openings of 4,0 m; one pedestrian opening of 1,0 m. Net wall length **31,0 m**. Blocks 440 × 220 × 220 solid, 10/m². Footing 800 × 250 at 450 mm. Six piers (2 ends + 4 at gates), 660 × 440. Plastered both sides. Precast coping.

| Item | Calculation | Quantity |
|---|---|---|
| Clear and grub | 40 m | **40 m** |
| Trench excavation | 0,800 × 0,450 × 31,0 | **11,16 m³** |
| Pier pad excavation | 6 × 1,0 × 1,0 × 0,30 | **1,80 m³** |
| Compact trench bottom | 0,800 × 31,0 | **24,8 m²** |
| 15 MPa concrete, strip | 0,800 × 0,250 × 31,0 | **6,20 m³** |
| — cement | 6,20 × 5,8 | **36 bags** |
| — concrete sand | 6,20 × 0,65 | **4,03 m³** |
| — 19 mm stone | 6,20 × 0,65 | **4,03 m³** |
| 25 MPa concrete, pier pads | 6 × 0,30 | **1,80 m³** |
| — cement | 1,80 × 7,7 | **14 bags** |
| Y12 reinforcement, pads | 6 × 7,2 m | **43 m** |
| Y12 starters, piers | 6 × 2 × 2,3 m | **28 m** |
| Backfill | ≈ 0,12 × 31 | **3,7 m³** |
| Cart away (bulked 30 %) | (11,16 + 1,80 − 3,7 − 8,0) × 1,3 | **1,6 m³** |
| Masonry area | 31,0 × 1,8 | **55,8 m²** |
| Blocks | 55,8 × 10 × 1,05 waste | **586 no.** |
| Extra-over pier blocks | 6 × 22 | **132 no.** |
| Mortar | (55,8/100 × 1,50) × 1,30 waste | **1,09 m³** |
| — cement | 1,09 × 7 | **8 bags** |
| — building sand | 1,09 × 1,35 | **1,47 m³** |
| Infill concrete, pier cores | 6 × 0,12 | **0,72 m³** |
| Brickforce | 31,0 × 4,2 | **131 m** |
| Control joints (@ 7,0 m) | 31,0 ÷ 7,0 + gate-adjacent | **6 no. = 11 m of joint** |
| Coping | 31,0 + pier returns 6 × 0,9 | **37 m** |
| Plaster, both sides | 55,8 × 2 + pier returns ≈ 12 | **124 m²** |
| — cement | 124/100 × 14 | **18 bags** |
| — plaster sand | 124/100 × 2,25 × 1,2 waste | **3,35 m³** |
| Paint, 2 coats both sides | 124 m² | **≈ 42 ℓ** |
| Curing water | 124 m² × 6 ℓ | **≈ 750 ℓ** |
| Gate piers | | **4 no.** |
| Vehicle gates | 2 × 4,0 m | **2 no.** |
| Pedestrian gate | 1,0 m | **1 no.** |
| Gate operator | Sized on mass | **1–2 no.** |

**Cement total: 36 + 14 + 8 + 18 ≈ 76 bags (3,8 tonnes).** Order in whole pallets from the Ohorongo Ondangwa depot, keep dry and off the ground.

**Labour:** masonry 55,8 m² ÷ 12 m²/day ≈ 5 bricklayer-days + piers 6 × 0,5 = 3 days = **8 bricklayer-days**; plaster 124 m² ÷ 18 ≈ **7 plasterer-days**; excavation 13 m³ ÷ 4 ≈ **3–4 labourer-days**. See file `04`, §10 for the programme.

> ⚠️ **No rates.** No verified Namibian or South African unit rates were obtained in this research pass. Every rate must come from a live quotation. Price at least three contractors on the same BoQ, and reject any quotation that does not price every item. `needs-verification`

## 9. Quality clauses and tolerances

Put these in the specification, and inspect against them.

### Tolerances

| Item | Permissible deviation |
|---|---|
| Wall face against setting-out line | **± 10 mm** |
| Verticality over full height | **± 10 mm**, and ≤ ± 5 mm in any 1 m |
| Straightness in plan, over 5 m | **± 10 mm** |
| Level of coping, over 5 m | **± 5 mm** |
| Coursing gauge accumulated over 8 courses | **± 5 mm** |
| Bed and perpend joint thickness | 10 mm nominal, **± 3 mm** |
| Plaster flatness under a 2 m straightedge | **± 4 mm** |
| Plaster thickness | 12–15 mm; **≤ 20 mm** in any one pass |
| Foundation width | **+ 25 mm / − 0 mm** |
| Foundation founding depth | **+ 50 mm / − 0 mm** |
| Control joint width | 10–12 mm (clay), ≤ 12 mm (concrete) |
| Pier position along the wall | **± 25 mm** |
| Gate opening clear width | **± 10 mm** |

> These are specification values assembled from the code requirements and ordinary good practice. The formal deviations in **SANS 2001-CM1** were not obtained in this pass. `needs-verification`

### Hold points — work must not proceed past these without inspection

1. **Trial holes** examined and founding depth confirmed.
2. **Trench excavation** — depth, width, bottom compacted, no loose material, no roots.
3. **Reinforcement in pier pads** — before concrete.
4. **Sample panel** — 2 m of wall, full height, with one pier, one control joint and the coping — approved in writing before the main run starts.
5. **First lift of masonry** — joints, gauge, brickforce, plumb.
6. **Before plastering** — control joints formed and clean, brickforce complete, coping bedded.
7. **Before backfilling any retaining wall** — drainage layer, filter fabric, subsoil drain and weepholes all in place and clear.
8. **Gate commissioning** — beams tested, force limits set and recorded.

### Standard quality clauses to include

1. All masonry units shall comply with **SANS 1215** (concrete) or **SANS 227** (clay), and shall have an average compressive strength of not less than **5,0 MPa (solid)** or **3,0 MPa (hollow)** for freestanding walls, and not less than **3,0 MPa hollow / 4,0 MPa solid** elsewhere, in accordance with **SANS 10400-K 4.2.1.1**.
2. Concrete masonry units shall be **not less than 28 days old** at the time of building in.
3. All mortar shall be **Class II** complying with **SANS 2001-CM1**, batched at **50 kg cement : 200 ℓ building sand** using common cement complying with **SANS 50197**. Masonry cement complying with SANS 50413 shall not be used in concrete.
4. Lime, if used, shall not exceed **25 kg per 50 kg of common cement**, and shall not be used with masonry cement.
5. Mortar shall be used within **2 hours** of mixing and shall not be re-tempered after initial stiffening.
6. **Burnt clay units shall be wetted before laying. Concrete units shall not be wetted.**
7. All bed and perpend joints shall be **solidly filled**. Furrowing of bed joints is not permitted.
8. **No horizontal damp-proof course shall be provided in the freestanding wall** (SANS 10400-K 4.2.4.3).
9. Piers shall extend to the top of the wall **without reduction in size**, and the cores of hollow units in piers shall be **solidly filled with mortar or infill concrete** (SANS 10400-K 4.2.4.2).
10. The wall shall **terminate in a pier or a return** at every free end (SANS 10400-K 4.2.4.2).
11. Vertical control joints shall be provided at not more than the spacing given in **SANS 10400-K Table 19** and shall **extend to the top of the foundation** (4.2.6.3), formed as butt joints across the full width of the masonry, with a gap of **10–12 mm** (clay) or **not exceeding 12 mm** (concrete).
12. Control joint backing shall be **flexible cellular polyethylene, cellular polyurethane or foam rubber**. Hemp, fibreboard, cork and semi-rigid foams shall not be used. Sealant width-to-depth ratio shall be between **2:1 and 1:1**.
13. Masonry and plaster shall be **protected and kept damp for not less than 7 days** after completion. The Contractor shall include for all water required for curing.
14. Not more than **1,5 m** of freestanding wall shall be built in one day, and newly built wall shall be braced against wind until the mortar has gained adequate strength.
15. Copings shall overhang the wall face by not less than **40 mm** each side and shall incorporate a **continuous drip groove** on the underside, set back not less than 15 mm from the arris. A joint shall be formed in the coping over every control joint.
16. Where earth is retained, **subsoil drainage shall be provided by 50 mm diameter plastic weepholes**, geofabric-covered on the buried end, at not more than **300 mm** above the lower ground level and at not more than **1,5 m** centres (SANS 10400-K 4.2.4.1).
17. All steelwork shall be **hot-dip galvanized to SANS 121 (ISO 1461)** unless otherwise specified.
18. **Safety infrared beams shall be fitted to every powered gate** and the operator's force limits shall be set, tested and recorded at commissioning.

## 10. Reusable specification template

Copy, fill the brackets, delete what does not apply.

```
BOUNDARY WALL SPECIFICATION
Project: ......................................................
Site: ......................................................
Client: ......................................................
Date: ................  Rev: ......

1.  SCOPE
    Construction of [    ] m of boundary wall, [    ] m high above finished
    ground level, with [    ] no. vehicle gate(s) of [    ] m clear opening
    and [    ] no. pedestrian gate(s) of [    ] m clear opening, complete
    with foundations, piers, coping, finishes, gates, automation and
    making good, as shown on drawing(s) [    ].

2.  STANDARDS
    The work shall comply with SANS 10400-K:2011 (Walls), SANS 10400-H
    (Foundations), SANS 2001-CM1 (Masonry walling), SANS 2001-EM1
    (Plasterwork), SANS 1215 / SANS 227 (masonry units), SANS 50197
    (common cement) and SANS 121 / ISO 1461 (galvanizing).
    [NA] Local authority: ......................................

3.  DESIGN BASIS
    Wall type:              [freestanding / retaining / hybrid]
    Nominal thickness:      [    ] mm
    Height above ground:    [    ] m
    Max. ground-level difference x across wall:  [    ] m
    Pier type and size:     [none / Z-offset / one side / both sides /
                             diaphragm]  [    ] x [    ] mm
    Pier spacing:           [    ] m centres
    SANS 10400-K table and row relied on:  Table [17/18], row [        ]
    Design net wind pressure: [    ] kN/m²  (source: ................)
    Where the deemed-to-satisfy conditions of SANS 10400-K 4.2.4.2 are not
    met, the wall shall be designed by a registered engineer.

4.  GROUND AND FOUNDATIONS
    Trial holes: [    ] no., to [    ] m depth, at [locations].
    Founding stratum:       [                                    ]
    Minimum founding depth: [    ] mm below finished ground level, and not
                            less than 150 mm into undisturbed competent
                            material.
    Strip footing:          [    ] mm wide x [    ] mm thick, [15/25] MPa
    Pier pads:              [    ] x [    ] x [    ] mm, 25 MPa,
                            reinforced [    ]
    Steps in foundation:    in whole courses, overlap not less than twice
                            the footing thickness or 300 mm; control joint
                            at every step.

5.  MASONRY
    Units:                  [type, size, manufacturer]
    Minimum strength:       [5,0 MPa solid / 3,0 MPa hollow]
    Bond:                   [stretcher / English / Flemish / collar-jointed]
    Mortar:                 Class II to SANS 2001-CM1,
                            50 kg common cement : 200 l building sand
    Joints:                 10 mm, solidly filled, [finish]
    Bed-joint reinforcement: [type], at [400] mm vertical centres
    Vertical reinforcement:  [    ] in filled cores at piers, starters
                            lapped [    ] mm
    Control joints:         at not more than [    ] m centres, to top of
                            foundation, [10-12] mm butt joints with
                            [backer rod] and [sealant]
    DPC:                    NONE in the freestanding wall
    Maximum daily lift:     1,5 m; brace until cured

6.  COPING
    Type:                   [precast capping / brick on edge / in situ]
    Overhang:               not less than 40 mm each side
    Drip groove:            continuous, [8 x 8] mm, set back [15] mm
    Bedding:                full bed in Class II mortar
    Joints:                 over every control joint, sealed

7.  FINISHES
    [ ] External cement plaster, [15] mm, 50 kg common cement : 150 l
        plaster sand; stopped [150] mm above ground with a bell-cast
    [ ] Bagging / rub-up
    [ ] Face brickwork, joints [weather-struck / bucket-handle]
    [ ] Limewash, [4-6] thin coats over damped substrate
    Paint system:           [                                    ]
    Colour(s):              [                                    ]

8.  RETAINING (where applicable)
    Retained height:        [    ] m
    Backfill:               free-draining, [19] mm clean stone, [300] mm
                            zone, wrapped in geotextile
    Subsoil drain:          [100] mm slotted uPVC to fall, discharging to
                            [                    ]
    Weepholes:              50 mm dia., geofabric on buried end, not more
                            than 300 mm above lower ground level, at not
                            more than 1,5 m centres
    Waterproofing to retained face: [                    ]
    Control joints:         not more than 10 m
    No surcharge within a distance equal to the retained height.

9.  GATES
    Vehicle gate:  [sliding-tracked / sliding-cantilever / swing]
                   Clear opening [    ] m, height [    ] m
                   Frame [    ] x [    ] x [    ] mm RHS, brace from
                   bottom hinge corner to top latch corner
                   Infill [                    ]
                   Estimated mass [    ] kg
    Pedestrian gate: [    ] m x [    ] m, [                    ]
    Gate piers:    [    ] x [    ] mm, filled cores, [4] x Y12, on
                   [    ] x [    ] x [    ] mm reinforced pad;
                   articulation joint both sides
    Hinges:        adjustable in three axes, [    ] no. per leaf,
                   with bottom pin retainer, greaseable
    Rollers:       sealed bearing
    Finish:        hot-dip galvanized to SANS 121 / ISO 1461, then
                   [                    ]

10. AUTOMATION AND ACCESS CONTROL
    Operator:      [make / model], rated [    ] kg, [12/24] V DC with
                   battery backup
    Battery:       [    ] Ah, maintained by [mains / PV panel [    ] W]
    Safety:        infrared beam pair(s) across the opening — MANDATORY
    Remotes:       [    ] no., code-hopping
    Intercom:      [hard-wired / GSM]
    Sleeves:       [32] mm and [25] mm under all paving, laid before
                   paving, with draw boxes at every pier
    Commissioning: force limits set, recorded and demonstrated; beams
                   tested; handover documentation provided

11. ELECTRIC FENCE (where applicable)
    Strands:       [    ] no., [    ] mm above coping, angled outward
    Energiser:     [make / model], [mains / battery / solar-maintained]
    Signage:       warning signs at [    ] m centres and at every gate
    Certification: installer competent and certificated;
                   certificate of compliance to be provided

12. WORKMANSHIP AND TOLERANCES
    As clause 9 of kb file 16/10. Sample panel to be built and approved in
    writing before the main run commences, and retained until practical
    completion.

13. CURING AND PROTECTION
    All masonry and plaster to be protected and kept damp for not less
    than 7 days. The Contractor shall allow for all water required.
    Curing shall be the named responsibility of [                  ].

14. HOLD POINTS
    Trial holes / trench / pad reinforcement / sample panel / first lift /
    before plastering / before backfilling any retaining wall /
    gate commissioning.

15. COMPLETION
    Clean down, make good ground both sides, remove all surplus material,
    hand over as-built dimensions, commissioning records, warranties and
    operating instructions.
```

## Sources

- [SANS 10400-K:2011 — Part K: Walls](https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html) — SABS, via Internet Archive
- [Quantities for ordering building materials](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf) — Cement & Concrete SA (Tables 1a–1d, 2, 3 and the wastage/adjustment notes)
- [Concrete, plaster and mortar mixes for builders](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf) — Cement & Concrete SA
- [Successful plastering](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Successful-plastering-2024.pdf) — Cement & Concrete SA
- [Ohorongo Cement — products](https://ohorongo-cement.com/products/) — Ohorongo Cement (Pty) Ltd
- [CENTURION sliding gate motors](https://www.centsys.co.za/demo/centurion-systems-sliding-gate-motors/) — Centurion Systems

## Open questions

- **No unit rates or prices of any kind were obtained.** All costing must be done from live quotations. `needs-verification`
- The **ASAQS Standard System of Measuring Building Work** was not obtained; BoQ item descriptions here are practical, not SMM-compliant. `needs-verification`
- **SANS 2001-CM1** permissible deviations were not obtained; the tolerance table is assembled from code requirements and good practice. `needs-verification`
- Bagging material quantities and curing water allowances are estimates, not source-backed. `needs-verification`
- Labour output rates are planning figures; calibrate against actual gang performance on the first 5 m of wall.
- Paint spreading rate (6 m²/ℓ/coat) is a generic figure; use the manufacturer's stated rate for the actual product.
