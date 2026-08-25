---
id: walls.overview
title: Walls and boundaries — domain map
domain: 16_walls_and_boundaries
tags: [wall, boundary-wall, enclosure, security, privacy, thermal-mass, acoustic, precast-walling, overview]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "SANS 10400-K:2011 The application of the National Building Regulations Part K: Walls", url: "https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html", publisher: "SABS / Internet Archive", accessed: 2026-08-25}
  - {title: "Quantities for ordering building materials", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Concrete, plaster and mortar mixes for builders", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Okongo", url: "https://en.wikipedia.org/wiki/Okongo", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Ohangwena Region", url: "https://en.wikipedia.org/wiki/Ohangwena_Region", publisher: "Wikipedia", accessed: 2026-08-25}
related: [walls.history, walls.typology, walls.boundary_design, walls.construction, walls.namibia, walls.specifying]
unit_system: SI
applies_to: [residential, boundary-wall, gate, retaining-wall]
---

# Walls and boundaries — domain map

**Summary.** A wall is the oldest piece of built technology that is still a live design problem. This folder treats walls as seven overlapping things at once — structure, enclosure, security barrier, privacy screen, acoustic barrier, thermal mass, and cultural statement — and works from that down to the specific problem in hand: a freestanding masonry or precast boundary wall with vehicle and pedestrian gates on a residential plot at **Okongo, Ohangwena Region, northern Namibia**. The governing technical document for the region is **SANS 10400-K:2011**, whose clause 4.2.4 and Tables 17 and 18 give deemed-to-satisfy heights, thicknesses and pier spacings for freestanding walls; the practical core of this folder is file `03`.

## Key facts

| Item | Value | Source |
|---|---|---|
| Governing deemed-to-satisfy code **[ZA]**, followed in practice **[NA]** | SANS 10400-K:2011, clause 4.2.4 | SANS 10400-K |
| Definition, freestanding wall | "wall (that is not a retaining wall) without lateral support" — cl. 3.22 | SANS 10400-K |
| Max height, 220 mm solid wall, **no piers** | **1,8 m** | Table 17 |
| Max height, 110 mm solid wall, **no piers** | **1,0 m** | Table 17 |
| Max height, 110 mm solid wall with 440 × 110 mm piers at 1,5 m c/c (Z-wall) | **2,1 m** | Table 17 |
| Minimum unit strength, freestanding walls | **3,0 MPa** hollow, **5,0 MPa** solid | cl. 4.2.1.1 |
| Mortar for freestanding walls | **Class II** to SANS 2001-CM1 (50 kg cement : 200 ℓ sand) | cl. 4.2.1.1; C&CSA |
| Horizontal DPC in a freestanding wall | **Shall not be provided** — cl. 4.2.4.3 | SANS 10400-K |
| Control joints, freestanding concrete masonry | **5,0 to 7,0 m** maximum spacing | Table 19 |
| Control joints, freestanding clay masonry | **16 / 10 / 6 m** by moisture expansion class | Table 19 |
| Okongo population (2023) / climate | 3 564 / Köppen **BSh** hot semi-arid | Wikipedia, NSA census |
| Ohangwena Region population / area | 337 729 over 10 706 km²; 85,5 % rural | Wikipedia, NSA census |

> ⚠️ A boundary wall is the one structure on a residential site most likely to fall on a person. It is a slender, unbraced cantilever with no roof to restrain it, carrying almost no vertical load to resist overturning, and it is the element most often built by the least supervised labour. Wall collapses kill children. Design it, do not eyeball it.

## The seven jobs a wall does

**1. Structure.** A loadbearing wall carries vertical load to the foundation and resists lateral load in-plane. A *freestanding* boundary wall does the opposite: it carries almost no vertical load, and its entire structural problem is resisting out-of-plane wind while relying on its own self-weight for stability. This inversion is why boundary-wall design has its own rules (file `03`) and why intuition from house building misleads.

**2. Enclosure.** The wall defines a legal and social boundary. In Namibian communal-land contexts the boundary is frequently defined socially and by traditional authority rather than by a cadastral peg, which changes both the alignment problem and the diplomacy of building on it (file `09`).

**3. Security.** In southern Africa this is usually the client's stated reason for the wall. Security is a *system* — height, climbability, sightline, lighting, detection, response — and a solid 2,1 m wall that hides an intruder can reduce security relative to a 1,8 m see-through palisade. File `06` covers layering; file `04` covers electric fencing and access control.

**4. Privacy.** Visual privacy is governed by geometry, not by wall height alone: sightline angle from the observer's eye to the point to be screened. A 1,8 m wall gives full privacy at ground level but none from a neighbour's first floor.

**5. Acoustic barrier.** A wall attenuates noise only if it is (a) massive — surface density matters, roughly 10–14 dB insertion loss for a well-sited solid barrier is a realistic ceiling — and (b) **imperforate**. Gaps under precast panels or at gates destroy the effect. `needs-verification` on specific dB figures; treat acoustic performance as requiring a proper barrier calculation.

**6. Thermal mass.** A masonry or earth wall stores heat and releases it out of phase. In a **BSh** climate with large diurnal swing, a thick earth or masonry wall on the west boundary can shade and buffer a courtyard. Rammed earth 350 mm thick has a thermal lag of roughly 12 hours (file `02`).

**7. Cultural statement.** Every wall tradition in file `01` encodes a claim about who is inside. Great Zimbabwe's freestanding drystone, the Owambo palisade homestead, the Andalusian whitewashed *tapia*, the Johannesburg 2,4 m precast-and-electric-fence — each is a legible statement, and choosing between them on a Namibian village plot is a design decision, not a default.

## How this folder is organised

| # | File | What it makes you able to do |
|---|---|---|
| 00 | `00_overview.md` | Orient; find the right file |
| 01 | `01_history-of-walls.md` | Understand what each historic tradition actually *knew* technically |
| 02 | `02_wall-typologies-and-structure.md` | Choose a wall type on structure, cost, lifespan and maintenance |
| 03 | `03_boundary-wall-design-and-engineering.md` | **Design a freestanding or retaining boundary wall with real numbers** |
| 04 | `04_construction-methods-and-workmanship.md` | Set out, build, and sequence the work; specify gates and automation |
| 05 | `05_spanish-and-mediterranean-walls.md` | Achieve a Mediterranean wall authentically rather than as pastiche |
| 06 | `06_contemporary-wall-design.md` | Use contemporary wall languages with named precedents |
| 07 | `07_wall-trades-and-skills.md` | Assess and hire a competent waller, mason, plasterer or fencer |
| 08 | `08_wall-companies-and-manufacturers.md` | Identify suppliers and know what to ask when quoting |
| 09 | `09_namibia-wall-context.md` | Build something appropriate to Ohangwena, not imported urban practice |
| 10 | `10_specifying-and-costing-a-boundary-wall.md` | Measure, quantify, specify and price the work |

## The decision the Okongo project actually faces

For a residential boundary at Okongo the realistic options reduce to five, in ascending capital cost:

1. **Traditional/hybrid timber palisade** (`omupanda`-type stockade of mopane or similar poles). Culturally rooted, near-zero cash cost if poles are available, but termite- and fire-vulnerable and now legally weak as a permanent boundary. File `09`.
2. **Diamond mesh or welded mesh on steel or concrete posts.** Cheapest permanent option; no privacy; poor security alone.
3. **Concrete precast panel-and-post walling** (the dominant southern African product, panels typically 350 mm high × ~2,4–3,0 m span slotting into grooved posts). Fast, imported from Oshakati/Ondangwa or trucked from South Africa. File `08`.
4. **Concrete block masonry wall, 140 or 190 mm, plastered or bagged, with piers.** Uses local blocks, local labour, local sand; the option that circulates the most money locally. Files `03`, `04`, `09`.
5. **Steel palisade or welded-mesh security fencing on a masonry plinth**, with electric fence topping. Highest security, highest cost, most imported content.

The engineering constraint that decides between them is in file `03`; the availability constraint is in file `09`; the money is in file `10`.

## What makes Okongo different

- **Wind.** Freestanding walls fail in wind, and the DTS tables in SANS 10400-K explicitly exclude walls "exposed to severe wind loadings at crests of steep hills, ridges and escarpments" (cl. 4.2.1.1). Ohangwena is flat, which helps; but the terrain is open with low roughness, and open flat terrain gives *higher* design wind pressures at low level than a suburb does. See file `03`.
- **Ground.** Deep aeolian Kalahari sands, locally over calcrete, with seasonally wet *oshana* drainage lines. Sands are free-draining and non-expansive but loose, and a wall founded in loose sand at 400 mm depth will rock. Founding depth and width matter more here than reinforcement does.
- **Water.** Curing water is the scarce input. A wall built and left uncured in a **BSh** climate loses most of the mortar strength you paid for.
- **Supply.** Cement is domestically produced (Ohorongo Cement, Otavi, >1 Mt/yr capacity); almost everything else — steel, mesh, gate hardware, motors — comes up the B1 from Windhoek or across from Tsumeb, most of it originating in South Africa. Lead times of 2–6 weeks on non-stock items are normal.
- **Labour.** Blockmaking and block-laying skills are locally available; welding and steel fixing less so; automation and electric-fence commissioning generally must come from Oshakati, Ondangwa or Windhoek.

## Cross-references to other domains in this knowledge base

- Masonry units, mortar classes, coursing, control joints and lintels: `02_building_construction/05_masonry-and-brickwork.md`.
- Foundations, trial holes, DPC and DPM: `02_building_construction/03_groundworks-and-foundations.md`.
- Concrete mixes, batching, compaction and curing: `02_building_construction/04_concrete-technology.md`.
- Plaster and render defects: `02_building_construction/07_finishes-plaster-screed-paint.md`.
- Measurement and pricing method: `02_building_construction/11_estimating-and-measurement.md`.

## Sources

- [SANS 10400-K:2011 — Part K: Walls (full text)](https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html) — SABS, via Internet Archive
- [Quantities for ordering building materials](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf) — Cement & Concrete SA
- [Concrete, plaster and mortar mixes for builders](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Concrete-mortar-and-plaster-mixes-2024.pdf) — Cement & Concrete SA
- [Okongo](https://en.wikipedia.org/wiki/Okongo) — Wikipedia (citing Namibia Statistics Agency 2023 Census)
- [Ohangwena Region](https://en.wikipedia.org/wiki/Ohangwena_Region) — Wikipedia (citing Namibia Statistics Agency 2023 Census)
- [Ohorongo Cement](https://www.ohorongo-cement.com/) — company site

## Open questions

- Namibia's building-control regime is administered by local authorities under the Local Authorities Act; whether Okongo Village Council has adopted SANS 10400 by reference, and what its by-law says about boundary-wall height, needs confirmation with the Council. `needs-verification`
- Acoustic insertion-loss figures for typical precast and masonry boundary walls are quoted from general practice and are not source-backed here. `needs-verification`
