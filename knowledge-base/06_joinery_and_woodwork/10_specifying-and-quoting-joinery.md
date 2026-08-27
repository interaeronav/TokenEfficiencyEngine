---
id: joinery.specifying
title: Specifying and quoting joinery
domain: 06_joinery_and_woodwork
tags: [specification, quoting, cutting-list, take-off, board-yield, waste-factor, hardware-schedule, labour-hours, shop-drawings, tolerances, payment-stages, contract]
jurisdiction: southern-africa
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "A Sustainable Future — Quality Assurance & Technical Information", url: "https://www.pgbison.co.ke/assets/images/content/sustainability_document_705051.pdf", publisher: "PG Bison", accessed: 2026-08-25}
  - {title: "It's the Formica LifeSeal Worktops Guide", url: "https://www.pgbison.co.ke/assets/images/content/Its_the_Formica_LifeSeal_Worktops_Guide_990144.pdf", publisher: "PG Bison", accessed: 2026-08-25}
  - {title: "LEGRABOX range", url: "https://www.blum.com/gb/en/products/boxsystems/legrabox/programme/", publisher: "Blum", accessed: 2026-08-25}
  - {title: "InnoTech Atira catalogue", url: "https://designwithhettich.au/wp-content/uploads/2023/12/IT-Atira-catalogue-NEW.pdf", publisher: "Hettich", accessed: 2026-08-25}
  - {title: "Edging", url: "https://www.nationaledging.co.za/edging/", publisher: "National Edging", accessed: 2026-08-25}
related: [joinery.cabinetmaking, joinery.hardware, joinery.sheet_goods]
unit_system: SI
---

# Specifying and quoting joinery

**Summary.** A joinery package is priced from four independent take-offs — **board**, **edging**, **hardware** and **labour** — plus finishing, transport and installation. The commonest cause of a loss-making joinery contract is not a pricing error but a **specification gap**: an undefined board grade, an unnamed hardware model, or a missing site-dimension clause that leaves the joiner carrying the builder's tolerances. This file gives a reusable specification structure, the take-off arithmetic, and indicative labour bases. **Every rate in this file is a placeholder — populate with your own measured figures.**

## Key facts

- Standard local sheet **2750 × 1830 mm = 5.0325 m²**; the 12 ft sheet **3660 × 1830 mm = 6.6978 m²**. MelaWood faced sheets are supplied at **2750 × 1840 mm** (trim allowance).
- **Board waste factors:** 10 % for a well-nested CNC job on plain board; 15 % for mixed sizes on a panel saw; **20–25 %** for grain-directional or synchronised-texture décors where parts cannot be rotated; 30 %+ for solid timber from rough-sawn stock.
- **Edging take-off:** total perimeter of edged edges + 10 % (start/stop waste), by thickness and décor.
- **Formica LifeSeal worktop** module: 3660 × 600 × 32 mm — price by the length, not the m².
- Standard cabinet widths for costing: 150, 300, 400, 450, 500, 600, 800, 1000, 1200 mm.

## 1. The schedule of joinery items

Everything starts here. One row per **item**, where an item is a thing that gets made, delivered and installed as a unit.

| Field | Example |
|---|---|
| Item ref | KIT-B-06 |
| Location | Kitchen, north run |
| Description | Base unit, 3-drawer |
| Qty | 2 |
| Size W × D × H (mm) | 600 × 570 × 720 |
| Carcass material | 16 mm MelaWood, décor X, ABS 1 mm matching |
| Front material | 18 mm MelaWood, décor Y, ABS 2 mm matching |
| Hardware | 3 × Blum LEGRABOX pure M, NL 500, 40 kg, BLUMOTION |
| Finish | factory melamine, no site finish |
| Handles | client-supplied, 160 mm c/c |
| Notes | scribe to wall at east end |

Number items by room and type (`KIT-`, `SCU-`, `DRS-`, `BED-`, `GAR-`) so that a drawing, a cutting list, a delivery note and a snag list all key to the same reference. Group the schedule into **kitchen, scullery, dressing room, bedroom wardrobes, garage stores** and price each group separately — clients cut scope by room.

## 2. Materials take-off from a cutting list

**Step 1 — cutting list.** Every part, by item: part name, quantity, finished length × width × thickness, material, grain/texture direction, and which edges are banded (front/back/left/right). Add machining notes (system holes, hinge cups, runner holes, grooves).

**Step 2 — board area.** Sum the part areas by material and thickness. Add the waste factor. Divide by sheet area and **round up to whole sheets**.

*Worked example — one 600 mm 3-drawer base unit, 16 mm carcass:*

| Part | Qty | Size (mm) | Area (m²) |
|---|---|---|---|
| Sides | 2 | 720 × 570 | 0.821 |
| Bottom | 1 | 568 × 570 | 0.324 |
| Top rails | 2 | 568 × 100 | 0.114 |
| Back (16 mm, hanging) | 1 | 568 × 720 | 0.409 |
| **Carcass subtotal** | | | **1.668** |
| Fronts (18 mm) | 3 | 597 × 140 / 285 / 285 | 0.424 |

Carcass: 1.668 m² × 1.15 (waste) = 1.918 m² → **0.38 of a 2750 × 1830 sheet**. Across 12 base units that is 4.6 sheets of 16 mm; buy 5. Never price fractions of a sheet as if they can be bought.

**Step 3 — nesting reality check.** A 720 × 570 mm side does not tile perfectly into 2750 × 1830. Run the actual optimisation (any cutting-optimiser software, or the panel saw's own optimiser) before committing on a job over about 20 sheets. The difference between a naive area calculation and a real nest is routinely 8–12 % of the board cost.

**Step 4 — edging.** Sum the banded edge lengths by thickness. For the example unit: front edges of the two sides = 2 × 720 = **1.44 m of 1 mm**; perimeters of the three fronts = 2×(597+140) + 2×(597+285) + 2×(597+285) = **5.00 m of 2 mm**. Add 10 % for start/stop waste.

**Step 5 — solid timber.** Take off in **m³ of rough-sawn**, not finished. Convert: finished volume × 1.35 to 1.6 depending on stock quality and how much is short/narrow. Add separately for defect cutting in figured or knotty material.

**Step 6 — worktops.** By running metre of the 3660 mm module, plus cut-outs, joints, upstands and edging strips as separate line items. Price the **offcut you cannot use** as part of the job.

## 3. Hardware schedule

A separate schedule, one row per hardware type:

| Field | Example |
|---|---|
| Ref | HW-04 |
| Manufacturer / range / model | Blum LEGRABOX pure |
| Full designation | Height M (90.5 mm), NL 500 mm, 40 kg, BLUMOTION, orion grey |
| Components per set | 2 × side, 1 × back, 1 × bottom, 2 × front fixing bracket, 2 × runner |
| Qty (sets) | 34 |
| Used on items | KIT-B-03/04/06, SCU-B-02, DRS-D-01 |
| Lead time | confirm before order |
| Spares allowance | 5 % |

**Rules:**
- Price at set level, not component level, or you will miss the front-fixing brackets and the covers.
- **Confirm lead times before quoting.** **[NA]** Non-stock Blum/Hettich items ship from South Africa and can add weeks.
- Hardware is typically **20–35 % of the material cost** of a modern kitchen, and can exceed the board cost on a drawer-heavy design. Never fold it into a "per linear metre" rate.
- Carry hinges, plates, runner clips, shelf pins, cabinet connectors and adjustable feet as a **consumables allowance** rather than counting each one.

## 4. Labour hours by item type

> ⚠️ The figures below are **indicative planning bases only**, for a two-person small shop with a panel saw, an edgebander and a line borer. They exclude design, delivery, finishing and site installation. Replace them with your own measured hours as soon as you have three jobs of data.

| Item | Shop hours (make) | Install hours |
|---|---|---|
| Base unit, doors only, 600 mm | 2.5–3.5 | 0.75 |
| Base unit, 3-drawer, 600 mm | 4.5–6.0 | 1.0 |
| Corner base / carousel unit | 5.0–7.0 | 1.5 |
| Wall unit, 600 × 720 mm | 2.0–3.0 | 0.75 |
| Wall unit with lift system | 3.0–4.5 | 1.25 |
| Tall / oven housing, 600 × 2140 mm | 6.0–8.0 | 1.5 |
| Wardrobe bay, 900 mm, hanging + shelves | 5.0–7.0 | 1.5 |
| Dressing-room run, per linear metre | 6.0–9.0 | 2.0 |
| Garage store unit, 900 mm, utility | 2.5–3.5 | 0.75 |
| Laminate worktop, per linear metre incl. one joint | 1.0–1.5 | 1.0 |
| Solid-timber door, framed and panelled | 5.0–8.0 | 1.0 |
| Scribing / filler / infill panel, each | 0.5–1.0 | 0.5 |
| Spray finishing, per m² of surface (2K PU, 3 coats) | 0.35–0.6 | — |

**Multipliers:** painted/sprayed rather than melamine **× 1.4–1.8**; solid-timber components **× 2–3**; curved, angled or non-modular **× 1.5–2**; one-off with no repetition **× 1.3**; site-built rather than shop-built **× 1.5–2**. For a remote site (Namibian farm, long travel), price mobilisation, accommodation and return visits as separate line items — never buried in an hourly rate.

**Overhead and margin.** Price labour at a **charge-out rate** that recovers shop overhead (rent, machines, power, extraction, consumables, insurance, non-productive time), not at a wage. A shop rate of 2.5–3.5 × the tradesman's wage is the conventional starting point; verify against your own accounts.

## 5. Shop drawings — what they must show

A shop drawing is not the architect's drawing redrawn. It must be buildable from without any other document.

1. **Elevations** of every run at 1:20, with every item referenced and every dimension shown, including reveals and gaps.
2. **Plans** at 1:20 showing wall lines, out-of-square, services, appliance positions and the scribe/filler strategy.
3. **Vertical and horizontal sections** at 1:5 through each typical condition: base unit with worktop, wall unit, tall unit, drawer stack, wardrobe hanging bay.
4. **Details at 1:1 or 1:2** for every non-standard junction: scribes, mitres, worktop-to-splashback, plinth returns, end panels, shadow gaps.
5. **A carcass construction note** stating panel thicknesses, fixing system, back type and edging by thickness and décor.
6. **The hardware schedule reference** on every door and drawer.
7. **Setting-out datum**: the finished floor level datum and the wall from which horizontal setting-out runs.
8. **Services coordination**: exact positions of waste, water, gas, sockets, isolators and extract ducts, with tolerances.
9. **Grain/texture direction arrows** on every faced part where the décor is directional.
10. **A revision block and a status** (Preliminary / For Comment / For Construction). Nothing gets cut off a "Preliminary" drawing.

## 6. Tolerance and site-dimension clauses

These clauses protect the joiner from the builder's inaccuracy and the client from the joiner's optimism. Include them verbatim in the quotation.

- **Site dimensions.** "All dimensions are to be verified on site by the joinery contractor after plastering/screeding and before manufacture. Any dimension shown on tender drawings is indicative only."
- **Required builder's tolerances.** "The joinery contractor's price assumes walls plumb within ±5 mm over 2400 mm, floors level within ±5 mm over 3000 mm, and openings square within ±3 mm. Deviations exceeding these will be measured and charged as a variation."
- **Scribes and fillers.** "All runs abutting walls include a scribe strip of not less than 20 mm. Where the deviation exceeds the scribe allowance, additional infill will be required."
- **Sequence dependency.** "Manufacture commences only after (a) site dimensions are taken, (b) the appliance schedule with model numbers is confirmed and (c) worktop and handle selections are confirmed. Delay in any of these extends the programme day-for-day."
- **Moisture and storage.** "The building must be weathertight, dry and lockable before delivery; joinery will not be delivered while wet trades are working."
- **Appliance apertures.** "Apertures are formed to the appliance manufacturer's published installation dimensions for the models listed. Substitution after manufacture is a variation."
- **Setting out.** "All levels are taken from a single datum established from the highest point of the finished floor within the room."
- **Timber movement and natural variation.** "Solid-timber components are manufactured at 7 % ± 2 % MC; seasonal movement within the design range is not a defect. Signed-off timber and décor samples are indicative — natural variation in colour, grain and figure is inherent and is not a defect."

## 7. Payment stages

A defensible structure for a residential joinery package:

| Stage | % | Trigger |
|---|---|---|
| 1. Deposit / design | 15 % | Order acceptance; shop drawings commence |
| 2. Materials | 35 % | Shop drawings signed "For Construction"; board and hardware ordered |
| 3. Manufacture complete | 30 % | Carcasses, fronts and finishing complete, ready for delivery |
| 4. Installation complete | 15 % | Installation complete, snag list issued |
| 5. Retention / snags | 5 % | Snags cleared, handover signed |

Notes: stage 2 must at minimum cover the hardware and board invoices — those are irrecoverable once ordered to a bespoke specification. Retention of 5 % for 30–90 days is normal; longer retention on joinery is unreasonable and should be resisted.

## 8. Template specification structure

A reusable structure a builder or architect can copy:

```
J01  SCOPE AND GENERAL
     J01.1  Extent of the joinery works (by room)
     J01.2  Documents forming part of the specification
     J01.3  Standards referenced (SANS 50312 / EN 312, EN 622-5, SANS 929, EN 438, EN 204)
     J01.4  Definitions and item numbering convention
J02  MATERIALS
     J02.1  Board: manufacturer, product, grade, thickness, MR requirement, E1 emission class
     J02.2  Edging: material, thickness by application, décor, adhesive (EVA / PUR)
     J02.3  Solid timber: species, grade, moisture content, cut, sapwood exclusion, permits (CITES / NA Forest Regulations)
     J02.4  Worktops: product, thickness, edge profile, jointing and sealing
     J02.5  Adhesives: EN 204 class by application
     J02.6  Coatings: system, number of coats, dry film thickness, sheen
J03  HARDWARE
     J03.1  Hardware schedule (attached)
     J03.2  Substitution: written approval required; equal-or-better must be demonstrated
     J03.3  Spares to be handed over
J04  WORKMANSHIP
     J04.1  Carcass construction system and fixing
     J04.2  32 mm system boring
     J04.3  Reveals and gaps (state the target, e.g. 3 mm ± 0.5 mm)
     J04.4  Edging quality: no glue line visible, flush and radiused where specified
     J04.5  Finishing preparation and application
J05  SHOP DRAWINGS AND SAMPLES
     J05.1  Drawings required and scales
     J05.2  Samples: board décor, edging, timber, finish, handle — signed off before manufacture
     J05.3  Approval period and consequences of delay
J06  SITE DIMENSIONS AND TOLERANCES
     J06.1  Verification of site dimensions
     J06.2  Required builder's tolerances
     J06.3  Scribes, fillers and infills
J07  DELIVERY, INSTALLATION AND PROTECTION
     J07.1  Building readiness conditions
     J07.2  Installation sequence and coordination with other trades
     J07.3  Protection of finished work
J08  COMPLETION
     J08.1  Snagging procedure
     J08.2  Handover: as-built drawings, care instructions, spares, warranties
     J08.3  Defects liability period
J09  SCHEDULE OF JOINERY ITEMS (attached)
J10  PRICING SCHEDULE (attached, priced by item and by room)
```

## 9. Quoting checklist

- [ ] Every item on the schedule has a size, a material, a hardware reference and a finish
- [ ] Board take-off from a real cutting list; waste factor applied; rounded to whole sheets
- [ ] Edging taken off by thickness and décor, +10 %
- [ ] Hardware priced at set level, lead times confirmed, 5 % spares
- [ ] Worktops priced by module, with cut-outs, joints and unusable offcut
- [ ] Finishing priced by m² of actual coated surface, both faces where applicable
- [ ] Labour hours from your own data, with multipliers applied
- [ ] Delivery, mobilisation, accommodation and return visits priced separately
- [ ] Site-dimension, tolerance and sequence clauses included
- [ ] Exclusions listed explicitly (stone worktops, appliances, handles, plumbing, electrical, tiling, wall painting)
- [ ] Validity period stated — board and hardware prices move
- [ ] Payment stages stated

## Sources

- [PG Bison — Quality Assurance & Technical Information](https://www.pgbison.co.ke/assets/images/content/sustainability_document_705051.pdf) (sheet sizes and thicknesses used in the take-off arithmetic)
- [PG Bison — Formica LifeSeal Worktops Guide](https://www.pgbison.co.ke/assets/images/content/Its_the_Formica_LifeSeal_Worktops_Guide_990144.pdf) (worktop module and sealing requirements)
- [Blum LEGRABOX range](https://www.blum.com/gb/en/products/boxsystems/legrabox/programme/) (hardware designation format)
- [Hettich InnoTech Atira catalogue](https://designwithhettich.au/wp-content/uploads/2023/12/IT-Atira-catalogue-NEW.pdf) (panel-size formulas that drive the cutting list)
- [National Edging — Edging range](https://www.nationaledging.co.za/edging/) (edging thicknesses and widths for take-off)

## Open questions

- **All labour hours, multipliers, overhead multiples and payment percentages in this file are practitioner conventions, not sourced data.** They are marked `draft` for that reason. Replace with measured figures from your own completed jobs.
- Waste factors are typical industry ranges; the actual figure for a given job depends entirely on the nesting result and the décor's grain constraints.
- No standard South African or Namibian joinery specification template (equivalent to NBS or the JBCC preliminaries) was located and incorporated; if a JBCC-based contract is being used, the tolerance and payment clauses here must be reconciled with the main contract terms.
- Current board, edging and hardware prices are not included and must be quoted fresh — see also the open questions in `02_timber-species-southern-africa.md`.
