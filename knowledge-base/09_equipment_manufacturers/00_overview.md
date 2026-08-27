---
id: equipment.overview
title: Equipment manufacturers — domain overview and how to read a spec sheet
domain: 09_equipment_manufacturers
tags: [construction-equipment, plant, machinery, spec-sheet, operating-weight, iso-9249, sae-j1349, emissions-tier, bucket-capacity, load-chart, southern-africa]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Bell Equipment — B30E ADT product page (technical data)", url: "https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b30e-adt/", publisher: "Bell Equipment", accessed: 2026-08-25}
  - {title: "Bell Equipment — B45E ADT product page (technical data)", url: "https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b45e-adt/", publisher: "Bell Equipment", accessed: 2026-08-25}
  - {title: "Hilti Technical Library", url: "https://www.hilti.co.za/technical-library", publisher: "Hilti South Africa", accessed: 2026-08-25}
  - {title: "RitchieSpecs equipment specifications", url: "https://www.ritchiespecs.com/", publisher: "Ritchie Bros.", accessed: 2026-08-25}
  - {title: "Wirtgen Group parts and media library", url: "https://parts.wirtgen-group.com/parts-media/", publisher: "Wirtgen Group / John Deere", accessed: 2026-08-25}
related: [equipment.earthmoving, equipment.cranes, equipment.concrete, equipment.compaction, equipment.power_tools, equipment.woodworking, equipment.survey, equipment.site_services, equipment.manual_library, equipment.maintenance]
unit_system: SI
---

# Equipment manufacturers — domain overview and how to read a spec sheet

**Summary.** This domain is the machine side of construction: who makes the plant, what the model numbers mean, what the published numbers actually measure, and — critically — where the manufacturer keeps its manuals, spec sheets and parts catalogues so an agent can go straight to the primary document instead of guessing. It is written for a southern African context, where the machine population is a mix of current-tier European/Japanese product, lower-emissions-tier variants built specifically for non-regulated markets, and a large Chinese-brand intake. The single most important file here is `09_manual-and-documentation-library.md`, a tested link register.

## Key facts

| Item | Value | Note |
|---|---|---|
| Engine power standard, most global OEMs | **ISO 9249** (net) or **SAE J1349** (net) | figures differ from "gross"; always check which is quoted |
| Alternative net-power standard on ADTs/trucks | **UN ECE R120** | e.g. Bell E-series ADTs quote max net power to ECE R120 |
| Excavator bucket capacity | **SAE J296 heaped (1:1)** | heaped ≠ struck; struck is ~15–25% smaller |
| Loader bucket capacity | **SAE J742 / ISO 7546 heaped** | rated at 2:1 for loaders in some markets |
| ADT body capacity | **SAE 2:1 heaped** | e.g. Bell B45E: 25 m³ SAE 2:1 |
| Emissions tiers, regulated markets | EPA Tier 4 Final / EU Stage V | current for EU, US, Japan, Korea |
| Emissions tiers, non-regulated markets **[NA] [ZA]** | typically **Tier 2 / Stage II** to **Tier 3 / Stage IIIA** | verified example: Bell B30E for Africa runs OM926LA at **EU Stage II / EPA Tier 2** |
| Fuel sulphur constraint driving the above | Tier 4F/Stage V requires ≤15 ppm S ULSD | not universally available in the SADC region |
| Crane capacity convention | rated load at a **stated radius and boom/jib configuration** | never a single "tonnage" number |
| Standard crane rating margin | typically **75% of tipping load** on outriggers (mobile), 85% for structural-limited | check the chart's own footnotes |

## Files in this domain

| File | Covers |
|---|---|
| `01_earthmoving-and-excavation.md` | Cat, Komatsu, Volvo CE, Hitachi, JCB, Liebherr, Develon, Case, New Holland, XCMG, SANY, Bell; excavators, backhoes, loaders, dozers, graders, ADTs, skid steers; size classes and selection |
| `02_cranes-and-lifting.md` | Tower, mobile, crawler cranes; telehandlers, MEWPs, hoists; load charts, GBP, rigging, lift plans |
| `03_concrete-equipment.md` | Batch plants, truck mixers, pumps, placing booms, vibrators, floats, screeds, formwork, shoring, precast |
| `04_compaction-roads-and-paving.md` | Wirtgen Group, Bomag, Dynapac, Ammann, Cat paving, Weber MT, Wacker Neuson; rollers, pavers, milling, crushing, compaction specification |
| `05_power-tools-and-fixings.md` | Hilti, Bosch, Makita, DeWalt, Milwaukee, Metabo, Festool, Ryobi, Stanley; battery platforms, diamond tooling, anchors and load data |
| `06_woodworking-and-joinery-machinery.md` | SCM, Felder/Format-4, Altendorf, Homag, Biesse, Martin, Hammer, Laguna, Lamello, Festool; CNC, edgebanders, shop scaling, SADC dealers |
| `07_survey-and-measurement-instruments.md` | Leica, Trimble, Topcon, Sokkia, Hexagon, Disto; GNSS/RTK, total stations, levels, scanners; accuracy classes and calibration |
| `08_generators-pumps-and-site-services.md` | Generators and sizing, boreholes and solar pumping, compressors, welding plant, site lighting, off-grid design |
| `09_manual-and-documentation-library.md` | **The tested link register** — manuals, spec portals, parts catalogues, aggregators |
| `10_maintenance-and-operating-practice.md` | Service regimes, fluids, tyres and tracks, hour-based planning, plant records, competence, risk assessment, log template |

## How to read a machine spec sheet

A spec sheet is a legal-ish document written by a marketing department under engineering supervision. Every number on it is true under a stated condition, and the condition is what matters.

### 1. Operating weight

**Operating weight** is the machine as configured, with a full fuel tank, all lubricants and coolant, and a 75 kg operator — but the *configuration* is the variable. On an excavator it includes a stated boom, stick, bucket and shoe width; change from 600 mm to 900 mm triple-grouser shoes and the weight and ground pressure both change. A "20-tonne excavator" is a class, not a measurement.

What to actually use operating weight for:
- **Transport planning** — add the trailer. A 21 t excavator on a 10 t tri-axle low-bed needs a permit in most SADC jurisdictions.
- **Ground bearing pressure** — GBP = weight ÷ track contact area; a track-mounted 20 t excavator on 600 mm shoes runs roughly 45–55 kPa, comparable to a walking adult, but concentrates enormously when tracking over an obstruction or when the boom swings over the side.
- **Stability** — lift capacity charts are derived from weight distribution, so a lighter counterweight option silently reduces every number in the chart.

> ⚠️ Operating weight excludes attachments beyond the quoted one. A hydraulic breaker, tilt-rotator or quick-hitch adds mass at the worst possible moment arm.

### 2. Engine power ratings — ISO 9249 vs SAE J1349 vs gross

- **Gross power** (SAE J1995, ISO 14396 in some presentations) is measured at the flywheel *without* the engine-driven fan, alternator load, air cleaner and exhaust system that the machine actually carries.
- **Net power** (**ISO 9249** in Europe, **SAE J1349** in North America) is measured with the full production installation — fan, filters, aftertreatment, charging. This is the honest number and is typically **4–10% below gross**, more on machines with aggressive fan drives.
- **UN ECE R120** is a road-vehicle-derived net rating used on articulated haulers and some trucks. Bell quotes it explicitly: the B30E is **240 kW (322 hp) @ 2 200 rpm in accordance with UN ECE R120**.

When comparing two machines, force both onto the same standard. A Chinese-brand loader quoted at 162 kW gross and a European loader quoted at 145 kW net (ISO 9249) may be the same engine performance.

Also note that **rated speed** matters: 240 kW @ 2 200 rpm and 240 kW @ 1 600 rpm are different machines. The Bell B45E makes **390 kW @ 1 600 rpm** — a low-speed, high-torque highway-derived engine (peak torque, not peak power, does the work on a haul road).

### 3. Bucket capacity — SAE heaped vs struck

- **Struck capacity** is the volume held with material level with the bucket rim.
- **SAE heaped** adds the material that will stand above the rim at a stated angle of repose: **1:1 for excavators (SAE J296)**, **2:1 for loaders and truck bodies**.

Two consequences:
1. A "1.2 m³ bucket" delivers 1.2 m³ only of a material that will heap. Wet clay heaps beyond 1:1; dry sand collapses below it.
2. **Fill factor** converts nominal to real: ~1.0–1.1 for loose sand and topsoil, 0.85–0.95 for well-blasted rock, 0.6–0.75 for poorly fragmented rock or sticky clay. Productivity estimates that ignore fill factor are wrong by a third.

Convert to mass before you check payload: bulk density (loose) of common materials — sand/gravel ~1.5–1.7 t/m³, well-graded G5/G7 gravel ~1.8–2.0 t/m³, blasted granite ~1.6 t/m³ loose, topsoil ~1.2–1.4 t/m³. Verified example: a Bell **B45E** with a **25 m³ SAE 2:1** body and **41 000 kg rated payload** is payload-limited at any material denser than ~1.64 t/m³ loose, and volume-limited below that.

### 4. Lift capacity charts

For excavators, the chart is a grid of **reach (horizontal distance from swing centre) × height above/below ground**, with separate columns for **over-front** and **over-side**. Over-side is always the smaller number because the undercarriage is narrower across the tracks than along them. Every value is normally limited to **87% of hydraulic capacity or 75% of tipping load**, whichever is lower — that footnote is on the chart and is the whole basis of the rating.

For cranes see `02_cranes-and-lifting.md`: the chart is **radius × boom length × counterweight × outrigger spread**, and the four are not independent.

> ⚠️ A machine lifting at its chart limit has no margin for a snatch load, a soft outrigger pad, or an out-of-level base. Standard practice is to plan lifts at ≤75–80% of chart, and treat anything above 90% as a critical lift requiring an engineered plan.

### 5. Emissions tiers — and why the SADC region is different

Regulated markets have marched EPA Tier 1 → 2 → 3 → 4 Interim → 4 Final, and the EU Stage I → V. Stage V/Tier 4F machines use SCR (needing AdBlue/DEF), DPF and cooled EGR, and they **require ultra-low-sulphur diesel (≤15 ppm S)**. Where that fuel is not reliably available, OEMs supply lower-tier variants.

This is not theoretical. Bell's Africa-and-Middle-East configurations are explicitly built to lower tiers: the **B18E is Euro III**, the **B30E is EU Stage II / EPA Tier 2**, the **B45E is EU Stage IIIA / EPA Tier 3 equivalent**. **[NA] [ZA]** When importing a used machine from Europe, check its tier: a Stage V machine on high-sulphur diesel will destroy its DPF and derate.

Practical rules:
- Match the machine tier to the fuel you can actually buy, not to the tier you'd prefer.
- If you inherit a Stage V machine, budget for DEF supply and DPF regeneration cycles, and never run it on unfiltered bunkered fuel.
- Lower-tier machines are mechanically simpler and easier to field-service — a genuine advantage on a remote site, and one reason low-tier variants remain in production.

### 6. The rest of the sheet

- **Travel/gradeability** — max gradient is a traction figure, not a stability figure.
- **Swing torque and swing speed** — governs cycle time more than engine power on a 20 t excavator.
- **Hydraulic flow and pressure** — the real constraint on attachment selection. A breaker needs a stated l/min at a stated bar; check the auxiliary circuit before buying the hammer.
- **Sound power (LwA) and operator ear (LpA)** — dB(A) figures to ISO 6395/6396, needed for occupational noise assessments.
- **Vibration (HAV/WBV)** to ISO 5349 / ISO 2631 — needed for exposure calculations on hand tools and ride-on plant.

## How to use this domain

1. **Identify the machine class first** (file 01–08), not the brand.
2. **Get the size class right** using operating weight and the task's real constraint (access width, reach, payload, ground bearing).
3. **Go to the primary document** via `09_manual-and-documentation-library.md`. Never quote a spec from a dealer advert or a marketplace listing; go to the OEM PDF or, failing that, a reputable aggregator, and record which.
4. **Check the regional variant.** The same model designation can carry a different engine, tier and even transmission in Africa, Europe and North America.
5. **Plan the maintenance and records** from day one using `10_maintenance-and-operating-practice.md`.

## Sources

- [Bell Equipment — B30E ADT technical data](https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b30e-adt/) — Bell Equipment, accessed 2026-08-25 (240 kW net to UN ECE R120; 28 000 kg rated payload; 49 155 kg operating weight; Mercedes-Benz OM926LA at EU Stage II / EPA Tier 2)
- [Bell Equipment — B45E ADT technical data](https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b45e-adt/) — Bell Equipment, accessed 2026-08-25 (390 kW @ 1 600 rpm; 41 000 kg payload; 25 m³ SAE 2:1 body; EU Stage IIIA / EPA Tier 3 equivalent)
- [Bell Equipment — B18E 6×4 ADT technical data](https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b18e-6x4-adt/) — Bell Equipment, accessed 2026-08-25 (Euro III; 163 kW; 18 000 kg payload; 11 m³ SAE 2:1)
- [Bell Equipment — Africa & Middle East product index](https://www.bellequipment.com/mining-construction/africa-and-middle-east/products/) — Bell Equipment, accessed 2026-08-25
- [Hilti Technical Library](https://www.hilti.co.za/technical-library) — Hilti, accessed 2026-08-25 (6 406 technical documents; the document-type taxonomy used in file 09)
- [Wirtgen Group — Parts Media library](https://parts.wirtgen-group.com/parts-media/) — Wirtgen Group, accessed 2026-08-25
- [BOMAG — machine documents](https://www.bomag.com/ww-en/services/parts-options/machine-documents/) — BOMAG, accessed 2026-08-25
- [Genie — parts, service and operations manuals](https://www.genielift.com/en/support/manuals) — Genie/Terex, accessed 2026-08-25
- [RitchieSpecs](https://www.ritchiespecs.com/) — Ritchie Bros., accessed 2026-08-25
- [Komatsu — equipment product categories](https://www.komatsu.com/en-us/products/equipment/excavators) — Komatsu, accessed 2026-08-25
- [Liebherr — construction machines overview](https://www.liebherr.com/en/gbr/products/construction-machines/construction-machines.html) — Liebherr, accessed 2026-08-25

## Open questions

- Regional Namibian dealer coverage for the Chinese brands (XCMG, SANY, Zoomlion) changes rapidly and is not fully captured here — verify current appointments before specifying.
- Several OEM sites (Caterpillar, Cummins, Perkins, LECTURA, Machinery Trader) block automated fetching; their URLs are recorded and are correct in a browser but could not be status-verified by script. This is flagged per row in file 09.
