---
id: building.overview
title: Building construction competence map
domain: 02_building_construction
tags: [builder, competence, overview, roadmap, residential, small-commercial, namibia, south-africa]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Free leaflets (technical library)", url: "https://concretesocietysa.org.za/free-leaflets/", publisher: "Cement & Concrete SA / Concrete Society of Southern Africa", accessed: 2026-08-25}
  - {title: "SANS 10400-K:2011 The application of the National Building Regulations Part K: Walls", url: "https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html", publisher: "SABS / Internet Archive", accessed: 2026-08-25}
  - {title: "Regulations relating to the Health and Safety of Employees at Work, GN 156 of 1997", url: "https://www.lac.org.na/laws/annoREG/Labour%20Act%2011%20of%202007-Regulations%201997-156.pdf", publisher: "Legal Assistance Centre, Namibia", accessed: 2026-08-25}
related: [building.roadmap, building.setting_out, building.foundations, building.concrete, building.masonry]
unit_system: SI
---

# Building construction competence map

**Summary.** This folder is the practical body of knowledge required to build residential and small-commercial work competently in northern Namibia (Okongo, Ohangwena Region) and, by extension, anywhere in southern Africa. It is ordered the way a building is actually built — from the trade path and site establishment through groundworks, concrete, masonry, roof, finishes, services, and finally the commercial and management skills that turn a tradesman into a contractor. Every file is dense with the numbers a builder must carry in their head: mix ratios, dimensions, gradients, tolerances and clause references. Materials, standards and trades assume the South African supply chain, because Namibia imports most of its cement, steel, timber, sheeting and sanitaryware from South Africa and its technical practice follows SANS.

## Key facts

| # | File | What it makes you able to do |
|---|---|---|
| 01 | `01_builder-competency-roadmap.md` | Get formally qualified and legally registered to trade **[NA]** and **[ZA]**; self-assess competence |
| 02 | `02_site-establishment-and-setting-out.md` | Clear, secure and set out a site accurately from a datum |
| 03 | `03_groundworks-and-foundations.md` | Read the ground, size and cast foundations, place DPC/DPM, backfill |
| 04 | `04_concrete-technology.md` | Specify, batch, place, compact, cure and test concrete |
| 05 | `05_masonry-and-brickwork.md` | Build walls that are plumb, bonded, jointed and correctly sized |
| 06 | `06_roofing-and-carpentry.md` | Specify timber, set out and fix a roof structure and covering |
| 07 | `07_finishes-plaster-screed-paint.md` | Plaster, screed, tile and paint to an acceptable standard |
| 08 | `08_waterproofing-and-damp.md` | Keep water out and diagnose damp when it gets in |
| 09 | `09_plumbing-and-drainage.md` | Lay out water and drainage, including off-grid septic systems |
| 10 | `10_electrical-fundamentals.md` | Coordinate with electricians; size an off-grid PV or generator supply |
| 11 | `11_estimating-and-measurement.md` | Take off quantities, price work, forecast cash flow |
| 12 | `12_programme-and-site-management.md` | Sequence and run a house build to handover |
| 13 | `13_quality-defects-and-tolerances.md` | Diagnose defects and apply permissible deviations |
| 14 | `14_health-and-safety.md` | Comply with construction OHS law and keep people alive |

## The order of learning

Competence in building is not a single skill but four stacked layers. Skipping a layer is the commonest reason a capable tradesman fails as a contractor.

**Layer 1 — Hand skills (months 0–24).** Setting out with a tape, line and square; mixing to a ratio; laying to a line and gauge; cutting and fixing timber; hanging a door; plastering to a screed. These are learned by repetition under a competent artisan, not from a book. Everything in files 02, 04, 05, 06 and 07 assumes you will practise it.

**Layer 2 — Technical judgement (years 1–5).** Knowing *why* a 1:4:4 mix is wrong for a slab, why a 25 mm plaster coat crazes, why a lintel needs 150 mm bearing, why a 110 mm drain must not be laid at 1:20 near a septic tank. This is where standards enter: SANS 10400 (the deemed-to-satisfy application of the National Building Regulations), SANS 2001 construction standards, SANS 10252 for water and drainage, and manufacturers' technical literature.

**Layer 3 — Commercial control (years 3–8).** Measurement, pricing, cash flow, retention, variations, programme, subcontractor management. Most small builders in Namibia and South Africa are technically adequate and commercially fatal. Files 11 and 12 carry this.

**Layer 4 — Legal and organisational standing (ongoing).** Trade certification, contractor registration, OHS compliance, warranties. File 01 and file 14.

## What is different about building at Okongo

- **Climate.** Hot semi-arid. Summer maxima routinely above 35 °C with very low relative humidity and steady wind. This attacks concrete and plaster at exactly the moment they are most vulnerable — the first 6 hours. Curing is not optional here; it is the single largest determinant of whether the work lasts. See `04_concrete-technology.md` §Curing and `07_finishes-plaster-screed-paint.md`.
- **Ground.** Deep aeolian (wind-blown) Kalahari sands over calcrete in places, with a seasonally high water table in the oshana drainage lines. Sands are generally free-draining and non-expansive but can be loose and collapsible on wetting. Trial holes are cheap; foundation failure is not. See `03_groundworks-and-foundations.md`.
- **Supply lines.** Ondangwa and Oshakati are the nearest material depots of scale; heavy items (cement, steel, sheeting, sanitaryware) come up the B1 from Windhoek or across from Tsumeb, and much of it originates in South Africa. Lead times of 2–6 weeks on non-stock items are normal. This makes accurate take-off (file 11) and lead-time-aware programming (file 12) disproportionately valuable.
- **Water.** Piped supply is unreliable or absent on many sites; borehole or trucked water is the norm. Concrete and mortar water must be fit to drink. Budget water into the programme — a slab you cannot cure is a slab you should not cast.
- **Labour.** A mixed pool of trade-tested artisans and informally trained builders. Formal trade testing goes through the Namibia Training Authority; see file 01.

## How to use these files with an AI agent

Each file opens with a `## Key facts` block of hard numbers so a retrieval system surfaces the number, not the prose. Jurisdiction-specific requirements are tagged inline with **[NA]** or **[ZA]**. Where a value could not be traced to a primary source it is flagged in `## Open questions` at the foot of the file and the frontmatter `status` is set to `needs-verification`.

> ⚠️ Nothing in this folder replaces a rational design by a professional engineer where one is required, nor a statutory approval. Deemed-to-satisfy rules (SANS 10400) apply only within their stated scope: broadly, one- and two-storey buildings on non-problem soils with imposed floor loads not exceeding 3,0 kN/m². Outside that scope, design it or get it designed.

## Cross-cutting principles

1. **Batch by mass or by whole bags, never by "a bit more cement".** A builder's wheelbarrow complying with SANS 795 holds about 65 ℓ struck level; that is the only volume measure worth trusting on site.
2. **Water is the enemy of strength and the friend of workability.** Every extra litre of mixing water costs strength and adds shrinkage.
3. **Cure everything cementitious for at least 7 days.** Concrete, plaster, screed, mortar in hot weather.
4. **Set out once, check twice, measure diagonals.** Almost every downstream tolerance problem originates in setting out.
5. **Detail for water before you detail for looks.** DPC, DPM, falls, laps, drips and flashings decide the life of the building.
6. **Write it down.** A site diary, a delivery register and a photograph of every trench before concrete are worth more than any argument later.

## Sources

- [Cement & Concrete SA — free technical leaflets](https://concretesocietysa.org.za/free-leaflets/) — the single most useful free technical library for southern African site practice.
- [SANS 10400-K:2011 Walls (full text)](https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html)
- [Namibia: Regulations relating to the Health and Safety of Employees at Work, GN 156 of 1997 (Labour Act)](https://www.lac.org.na/laws/annoREG/Labour%20Act%2011%20of%202007-Regulations%201997-156.pdf)

## Open questions

- Current Namibian building control practice at regional/local authority level in Ohangwena (plan approval, inspections) is not documented in an accessible primary source and should be confirmed with the Ohangwena Regional Council and the relevant town council before relying on any assumption of SANS-based approval.

