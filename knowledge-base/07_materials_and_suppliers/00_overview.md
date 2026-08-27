---
id: materials.overview
title: Materials and suppliers — domain overview
domain: 07_materials_and_suppliers
tags: [materials, suppliers, southern-africa, namibia, procurement, hot-semi-arid, remote-site, supply-chain]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Cementitious materials for concrete: standards, selection and properties", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Cementitious-materials-for-concrete-standards-selection-and-properties-2024-2.pdf", publisher: "Concrete Society of Southern Africa / Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Safintra Product Specification Manual (Dec 2025)", url: "https://www.safintra.co.za/wp-content/uploads/2026/02/SAF_Product_Specification_Manual_Dec_2025.pdf", publisher: "Safintra South Africa (Safal Group)", accessed: 2026-08-25}
  - {title: "Eenhana — climate data", url: "https://en.wikipedia.org/wiki/Eenhana", publisher: "Wikipedia, citing Deutscher Wetterdienst", accessed: 2026-08-25}
  - {title: "Namibia, Republic of — Corporate — Other taxes", url: "https://taxsummaries.pwc.com/republic-of-namibia/corporate/other-taxes", publisher: "PwC Worldwide Tax Summaries", accessed: 2026-08-25}
  - {title: "Megabuild Branches", url: "https://www.megabuild.com.na/main/branches/", publisher: "Pupkewitz Megabuild", accessed: 2026-08-25}
related: [materials.selection_principles, materials.procurement_pricing, materials.suppliers.namibia]
unit_system: SI
---

# Materials and suppliers — domain overview

**Summary.** This domain covers construction material science as practised in southern Africa and the real supplier landscape that serves a project in Namibia — with particular attention to the northern regions (Ohangwena, Oshana, Oshikoto, Kavango) where the supply line is long, the climate is hot semi-arid, and a wrong specification cannot be corrected by a quick trip to the merchant. It maps the eleven detailed files in this folder, sets out how to reason about material selection under those constraints, and gives an agent the entry points it needs to answer a material or supplier question without guessing.

## Key facts

| Item | Value | Note |
|---|---|---|
| Reference site climate (Eenhana, Ohangwena) | Köppen **BSh** (hot semi-arid) | annual mean 22.7 °C; annual precipitation 590 mm |
| Rainfall distribution | Nov–Apr wet, Jun–Sep effectively zero | Jan 125 mm, Feb 133 mm, Jul 0 mm |
| Atmospheric corrosivity, inland Namibia | **C1 (desert)** on Safintra's classification | uncoated mild steel < 5 µm/year; zinc < 0.5 µm/year |
| Coastal Namibia (Walvis Bay, Swakopmund) | Exposure **Zone 4 "Very Severe"** for clay masonry | a completely different specification regime |
| Governing cement standard | SANS 50197-1 (common cement), SANS 50413 (masonry cement) | **[ZA]**, and adopted in practice **[NA]** |
| VAT | 15% **[NA]**, 15% **[ZA]** | |
| Customs duty on NA↔ZA movement | Nil — both are SACU members | import VAT still applies |
| Nearest large builders' merchant cluster to Ohangwena | Oshakati / Ongwediva / Ondangwa | ~19 Pupkewitz Megabuild branches nationally; ~23 Build it stores in Namibia |

## Files in this domain

| File | Covers |
|---|---|
| `01_material-selection-principles.md` | Performance criteria, compatibility and galvanic interactions, life-cycle thinking, a decision framework |
| `02_cement-concrete-aggregates.md` | SANS 50197 cement types, extenders, aggregates, admixtures, ready-mix vs site batch, concrete products, producers |
| `03_masonry-units.md` | Clay brick classes (FBX/FBS/FBA/NFP/NFX/E), concrete units, stock bricks, earth blocks, sizes and strengths |
| `04_steel-and-reinforcement.md` | Rebar grades and sizes, mesh references, sections, sheet steel and coatings, fixings, corrosion classes, merchants |
| `05_timber-and-boards.md` | Structural grades, H2–H6 treatment, standard sizes, boards, trusses, shutter ply, treatment plants |
| `06_roofing-and-cladding.md` | Profiles, gauges, spans, pitches, coatings, tiles, thatch, translucent, manufacturers |
| `07_insulation-membranes-and-sealants.md` | Bulk and reflective insulation R-values, DPC/DPM, membranes, sealants and movement capability |
| `08_finishes-and-chemicals.md` | Plaster and screed, tile adhesives and grouts, paint systems, primers, construction chemicals, brands |
| `09_suppliers-namibia.md` | The Namibian supply landscape, branch by branch, with a northern-Namibia service assessment |
| `10_suppliers-south-africa.md` | The SA merchants and specialist trade suppliers Namibian projects import from, and how cross-border buying works |
| `11_procurement-and-pricing.md` | Specification writing, RFQs, quote comparison, trade accounts, VAT/SACU, delivery terms, lead times |

## How to reason about materials for a hot semi-arid, remote, long-supply-line site

The default southern-African specification is written for Gauteng or the Cape. Four site conditions invalidate parts of it.

### 1. The climate is hot, dry, and swings hard between day and night

The reference climate is BSh: seven months with almost no rain, a summer wet season concentrated into four months, and a large diurnal temperature range. Consequences for material choice:

- **Thermal mass is genuinely useful.** In a climate where the day/night swing is large and nights cool, heavy masonry that absorbs heat by day and re-radiates it at night flattens the internal temperature curve. This is the one climate where the clay-brick industry's thermal-capacity claim is actually the right argument. Combine mass with a light-coloured, high-reflectance roof and a ventilated roof space.
- **Concrete and mortar cure badly.** Low relative humidity plus high temperature plus wind gives high evaporation rates from fresh concrete. Plastic shrinkage cracking, poor surface durability and strength loss follow. This drives the specification towards extended cements (fly ash, slag) that generate less heat, retarders, evening or night placement, and non-negotiable curing (see `02`).
- **Movement is large.** Long metal roof sheets, unrelieved plaster runs and rigid joints all fail from thermal cycling. Design for movement; specify sealants by movement capability, not by brand (see `07`).
- **UV load is high.** Polymer components — geotextiles, DPC left exposed, plastic rainwater goods, uncoated polycarbonate — degrade fast. Protect or upgrade.

### 2. The atmosphere is not corrosive — but the specification usually assumes it is

Inland Namibian sites sit in the least corrosive category on the standard scales: Safintra classifies desert inland conditions as **C1**, with uncoated mild steel losing under 5 µm/year and zinc under 0.5 µm/year. This matters commercially: a coastal-grade AZ200 sheet or a marine-grade fastener is money spent on a risk that is not present. Conversely, **do not carry an inland specification to Walvis Bay or Swakopmund**, where clay masonry sits in exposure Zone 4 and metalwork is in C5/C5M. Namibia contains both extremes within one country; always state the exposure category in the specification.

The real durability threats inland are different: aggressive groundwater and soil sulfates in some pans and depressions, wind-blown sand abrasion at low level, and termites — which are a design case for timber (H-class) and for slab detailing, not a nuisance.

### 3. Water is scarce and often saline

Mix water, curing water and wash water all compete with drinking water. Design for low water consumption: fewer wet trades, dry-jointed or thin-joint systems where feasible, and curing methods that conserve water (curing compounds, plastic sheeting, wet hessian rather than continuous spray). Test borehole water before using it for concrete — chlorides and sulfates in bore water are a recurrent problem in the north and will attack reinforcement.

### 4. The supply line is the binding constraint

For a site in Ohangwena Region, three supply tiers exist and they behave very differently:

| Tier | Where | What it reliably holds | Practical lead time |
|---|---|---|---|
| **Local** | Okongo, Eenhana, Oshikango, Ondangwa, Oshakati, Ongwediva | Cement, sand, stone, standard blocks, common rebar sizes, IBR/corrugated sheet, standard timber, basic hardware, common paints | Same day to a few days |
| **Regional** | Windhoek, Walvis Bay, Tsumeb | Full merchant range, structural sections, cut-and-bend rebar, boards, specialist chemicals, glass and aluminium | Days to 2 weeks including transport north |
| **Cross-border** | Gauteng / Western Cape / KZN | Anything specialised: architectural ironmongery, engineered hardware, specific board finishes, imported fittings, technical membranes | 3–8 weeks door to door, plus customs |

Three planning rules follow:

1. **Specify what tier 1 stocks, unless there is a performance reason not to.** Every substitution to a locally stocked equivalent that you make at design stage is a substitution you do not make under pressure at build stage.
2. **Front-load the long-lead items.** Anything that must come from South Africa should be ordered before the foundations are complete. Roof sheeting cut to length, joinery hardware, glazing and specialist chemicals are the usual culprits.
3. **Consolidate loads.** Freight north from Windhoek or Oshakati is charged by the trip more than by the kilogram for many carriers. A single planned load beats five reactive ones, and the difference is often larger than the material discount you were negotiating.

### The order in which to make decisions

1. **Fix the exposure and service conditions first** (inland C1 vs coastal C5; ground-contact vs above-ground; wet area vs dry). Half of all material errors are exposure errors.
2. **Choose the structural and enclosure system** — this sets the material families, and it is much cheaper to change here than later.
3. **Check availability at tier 1 and tier 2** before writing the specification, not after.
4. **Check compatibility** across every material interface — galvanic, chemical, thermal movement, and moisture (see `01`).
5. **Write the specification so it can be priced like-for-like** (see `11`) — performance clause plus a named reference product plus "or approved equivalent", with the equivalence test stated.
6. **Plan the logistics as part of the specification**, including packaging, storage on site and protection from sun and sand.

## Conventions used in this domain

- Standards are cited as SANS numbers where SANS applies. Namibia does not maintain a full parallel building-materials standards suite; Namibian practice, the Namibian Standards Institution (NSI) certification scheme, and Namibian merchants all work to SANS and to EN-derived SANS numbers. Where a requirement is specifically Namibian it is marked **[NA]**; South-Africa-specific requirements are marked **[ZA]**.
- Prices are given only where a dated, sourced figure exists. No price in this domain is a current quotation; treat every one as an order-of-magnitude anchor and re-quote.
- Supplier branch lists are as published by the supplier at the accessed date. Namibian merchant networks change quickly; branch details flagged as unverified must be confirmed by telephone before they are relied on.

> ⚠️ Nothing in this domain replaces a structural engineer's design, a fire rational design, or the manufacturer's current technical data sheet. Product formulations and gauges change; always check the current TDS for the batch you are buying.

## Sources

- [Cementitious materials for concrete: standards, selection and properties (2024)](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Cementitious-materials-for-concrete-standards-selection-and-properties-2024-2.pdf) — Concrete Society of Southern Africa / Cement & Concrete SA
- [Safintra Product Specification Manual, December 2025](https://www.safintra.co.za/wp-content/uploads/2026/02/SAF_Product_Specification_Manual_Dec_2025.pdf) — Safintra South Africa (corrosion category table, profile data)
- [Clay Brick Technical Guide, Chapter 3: Product specification and physical properties](https://claybrick.org/wp-content/uploads/2024/07/0004-Clay-Brick-Technical-Guide_web.pdf) — Clay Brick Association of Southern Africa (exposure zones)
- [Eenhana, Namibia — climate data (Deutscher Wetterdienst)](https://en.wikipedia.org/wiki/Eenhana)
- [Ohangwena Region](https://en.wikipedia.org/wiki/Ohangwena_Region)
- [Namibia — Corporate — Other taxes (VAT, SACU, customs)](https://taxsummaries.pwc.com/republic-of-namibia/corporate/other-taxes) — PwC Worldwide Tax Summaries
- [Pupkewitz Megabuild — Branch locator](https://www.megabuild.com.na/main/branches/)
- [Build it — Store finder entries for Namibian stores](https://www.buildit.co.za/Stores/View/Build-it-Oshakati-Namibia)

## Open questions

- No single authoritative published list of all Namibian Build it stores was found; the count of 23 comes from a SPAR Group 2025 capital-markets-day slide ("Western Region — RSA 39 & Namibia 23") and has not been reconciled store-by-store.
- Road distances between Okongo, Eenhana, Ondangwa and Oshakati are not stated in any source verified here, so no distance figures are asserted in this domain.
- Whether Namibian building-materials certification is governed by NSI marks, SABS marks, or both in practice for imported products needs verification against a current NSI directory.
