---
id: equipment.manual_library
title: Manual and documentation library — tested link register for construction equipment
domain: 09_equipment_manufacturers
tags: [manuals, spec-sheets, technical-library, parts-catalogue, documentation, link-register, lectura, ritchiespecs, machinery-trader, oem-portals, safety-data]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
paywalled: false
sources:
  - {title: "Hilti Technical Library", url: "https://www.hilti.co.za/technical-library", publisher: "Hilti", accessed: 2026-08-25}
  - {title: "Wirtgen Group Parts Media library", url: "https://parts.wirtgen-group.com/parts-media/", publisher: "Wirtgen Group", accessed: 2026-08-25}
  - {title: "Genie parts, service and operations manuals", url: "https://www.genielift.com/en/support/manuals", publisher: "Genie / Terex", accessed: 2026-08-25}
  - {title: "BOMAG machine documents", url: "https://www.bomag.com/ww-en/services/parts-options/machine-documents/", publisher: "BOMAG", accessed: 2026-08-25}
  - {title: "RitchieSpecs", url: "https://www.ritchiespecs.com/", publisher: "Ritchie Bros.", accessed: 2026-08-25}
  - {title: "Cummins QuickServe Online", url: "https://quickserve.cummins.com/", publisher: "Cummins Inc.", accessed: 2026-08-25}
related: [equipment.overview, equipment.earthmoving, equipment.cranes, equipment.concrete, equipment.compaction, equipment.power_tools, equipment.woodworking, equipment.survey, equipment.site_services, equipment.maintenance]
unit_system: SI
---

# Manual and documentation library — tested link register for construction equipment

**Summary.** This is the navigable link library for the whole domain: for every manufacturer covered in files 01–08, the entry point to their manuals, technical library, spec-sheet portal, parts catalogue or safety data. Every URL below was requested with an HTTP client on **2026-08-25** and its status recorded. Rows marked **verified** returned HTTP 200/202. Rows marked **WAF-blocked** are real, correct URLs whose servers reject automated requests (HTTP 403/429) but which open normally in a browser — they are flagged, not hidden. Nothing in this file is an unchecked guess.

## How this register was verified

Each URL was fetched with `curl -L` following redirects, with a desktop browser user-agent and a 30-second timeout. Outcomes were classified:

| Marker | Meaning |
|---|---|
| **verified** | HTTP 200/202 returned at the final URL |
| **WAF-blocked** | HTTP 403/429 — bot protection, not a dead link; correct in a browser |
| **redirect-loop** | The site's country/cookie redirect cannot be satisfied by a stateless client; opens in a browser |

> ⚠️ **Soft-404 caveat.** Several manufacturer sites (notably `bellequipment.com`) return HTTP 200 with the homepage for *any* unknown path. Bell URLs below were therefore additionally content-checked — each returns the specific model or product page named. Treat a bare 200 on an unfamiliar OEM site as weak evidence and confirm the page content.

## Access key

| Code | Meaning |
|---|---|
| **Free** | Public, no login |
| **Reg.** | Free but requires registration / account creation |
| **Dealer** | Restricted to authorised dealers, service partners or fleet customers |
| **Mixed** | Public catalogue with some restricted documents |

---

## A. Earthmoving and excavation

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| Caterpillar | Earthmoving | Corporate / product entry | https://www.cat.com/ | Free | **WAF-blocked** to automated fetch; opens in browser. Spec sheets are per-model PDFs (AEHQ codes) reached from the model page |
| Caterpillar | Earthmoving | Parts catalogue (Parts.cat.com) | https://parts.cat.com/ | Reg. | **WAF-blocked**; account gives serial-number-linked parts lookup and SIS |
| Caterpillar | Earthmoving | Safety services and resources | https://safety.cat.com/ | Free | **WAF-blocked**; operator safety material, MSDS routes |
| Caterpillar | Earthmoving | Southern African dealer (Barloworld) | https://www.barloworld-equipment.com/ | Free | **verified** — regional parts, service and used equipment |
| Komatsu | Earthmoving | Global corporate entry | https://www.komatsu.com/en/ | Free | **verified** |
| Komatsu | Earthmoving | Product index | https://www.komatsu.com/en/products/ | Free | **verified** |
| Komatsu | Excavators | Category + model spec pages | https://www.komatsu.com/en-us/products/equipment/excavators | Free | **verified** — model pages carry spec sheets |
| Komatsu | Wheel loaders | Category + model spec pages | https://www.komatsu.com/en-us/products/equipment/wheel-loaders | Free | **verified** |
| Komatsu | Dozers | Category + model spec pages | https://www.komatsu.com/en-us/products/equipment/dozers | Free | **verified** |
| Komatsu | Motor graders | Category + model spec pages | https://www.komatsu.com/en-us/products/equipment/motor-graders | Free | **verified** |
| Komatsu | Earthmoving | North America site | https://www.komatsuamerica.com/ | Free | **verified** — often the richest spec-sheet PDFs |
| Komatsu | Earthmoving | Europe site | https://www.komatsu.eu/en | Free | **verified** — EU Stage V configurations |
| Komatsu | Earthmoving | South Africa | https://www.komatsu.co.za/ | Free | **verified** — local parts, service, training |
| Volvo CE | Earthmoving | Global site | https://www.volvoce.com/global/en/ | Free | **verified** |
| Volvo CE | Earthmoving | Products and services hub | https://www.volvoce.com/global/en/products-and-services/ | Free | **verified** — route to per-model brochures and the product archive for discontinued models |
| Volvo CE | Earthmoving | Special applications | https://www.volvoce.com/global/en/products-and-services/special-applications/ | Free | **verified** |
| Hitachi Construction Machinery | Excavators | Global site | https://www.hitachicm.com/global/en/ | Free | **verified** |
| Hitachi Construction Machinery | Excavators | Europe site | https://www.hitachicm.com/eu/en/ | Free | **verified** — EU spec sheets and brochures |
| Hitachi Construction Machinery | Excavators | EU machinery index | https://www.hitachicm.eu/machinery/ | Free | **verified** (redirects to hitachicm.com/eu/en) |
| JCB | Backhoes, excavators, telehandlers | Corporate | https://www.jcb.com/en-gb | Free | **verified** |
| JCB | All | Support hub | https://www.jcb.com/en-gb/support | Free | **verified** — routes to parts, service, quick start guides |
| JCB | All | Product index (spec sheets per model) | https://www.jcb.com/en-gb/products | Free | **verified** |
| JCB | Backhoe loaders | Category page | https://www.jcb.com/en-gb/products/backhoe-loaders | Free | **verified** |
| JCB | All | South Africa | https://www.jcb.co.za/ | Free | **verified** |
| Liebherr | Earthmoving | Earthmoving division | https://www.liebherr.com/en-gb/earthmoving/earthmoving-4207106 | Free | **verified** — model pages carry technical data PDFs |
| Liebherr | All construction | Construction machines overview | https://www.liebherr.com/en/gbr/products/construction-machines/construction-machines.html | Free | **verified** — the top-level route into all divisions |
| Liebherr | Deep foundation | Division page | https://www.liebherr.com/en-gb/deep-foundation/deep-foundation-4296589 | Free | **verified** |
| Develon (ex-Doosan) | Earthmoving | Global entry | https://www.develon-ce.com/en/ | Free | **verified** |
| Develon | Earthmoving | Europe | https://eu.develon-ce.com/en/ | Free | **verified** — EU spec sheets |
| Develon | Earthmoving | North America | https://www.na.develon-ce.com/en/ | Free | **verified** |
| CASE Construction | Earthmoving | North America site | https://www.casece.com/en-us/north-america | Free | **verified** — model pages carry spec sheets and brochures |
| New Holland Construction | Earthmoving | Global construction site | https://construction.newholland.com/en-us | Free | **verified** |
| New Holland | Group | Corporate | https://www.newholland.com/ | Free | **verified** |
| XCMG | All | Corporate / product entry | https://www.xcmg.com/ | Free | **verified** — English content varies by section |
| SANY | All | Global site | https://www.sanyglobal.com/ | Free | **verified** |
| SANY | All | Product index | https://www.sanyglobal.com/product/ | Free | **verified** |
| SANY | All | China corporate (EN) | https://www.sany.com.cn/en/ | Free | **verified** |
| SANY | All | South Africa | https://www.sanysouthafrica.com/ | Free | **verified** — local parts and service |
| Zoomlion | Cranes, concrete, earthmoving | International site | https://en.zoomlion.com/ | Free | **verified** |
| Zoomlion | All | Corporate | https://www.zoomlion.com/ | Free | **verified** |
| **Bell Equipment** | ADTs, graders | Group entry | https://www.bellequipment.com/ | Free | **verified** — note soft-404 behaviour on unknown paths |
| **Bell Equipment** | ADTs | Africa & Middle East product index | https://www.bellequipment.com/mining-construction/africa-and-middle-east/products/ | Free | **verified**, content-checked — the correct regional index for **[ZA] [NA]** |
| **Bell Equipment** | ADTs | 6×6 ADT family | https://www.bellequipment.com/mining-construction/africa-and-middle-east/products/6x6-articulated-dump-trucks/ | Free | **verified**, content-checked |
| **Bell Equipment** | ADTs | 4×4 ADT family | https://www.bellequipment.com/mining-construction/africa-and-middle-east/products/4x4-articulated-dump-trucks/ | Free | **verified** |
| **Bell Equipment** | ADT | B18E 6×4 spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b18e-6x4-adt/ | Free | **verified**, content-checked: 163 kW, 18 000 kg payload, Euro III |
| **Bell Equipment** | ADT | B25E spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b25e-adt/ | Free | **verified**: 205 kW, 24 000 kg payload |
| **Bell Equipment** | ADT | B30E spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b30e-adt/ | Free | **verified**: OM926LA, 240 kW, 28 000 kg, Stage II/Tier 2 |
| **Bell Equipment** | ADT | B40E spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b40e-adt/ | Free | **verified**: 380 kW, 39 000 kg |
| **Bell Equipment** | ADT | B45E spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b45e-adt/ | Free | **verified**: OM471LA, 390 kW, 41 000 kg, 25 m³ SAE 2:1 |
| **Bell Equipment** | ADT | B50E spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/6x6-articulated-dump-trucks/b50e-adt/ | Free | **verified**: 430 kW, 45 400 kg |
| **Bell Equipment** | ADT | B60E 4×4 spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/4x4-articulated-dump-trucks/b60e-4x4-adt/ | Free | **verified**: 430 kW, 55 000 kg |
| **Bell Equipment** | Graders | G140 spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/motor-graders/g140/ | Free | **verified**: 179 kW, 21 289 kg |
| **Bell Equipment** | Graders | G160 spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/motor-graders/g160/ | Free | **verified**: 209 kW, 21 638 kg |
| **Bell Equipment** | Graders | G200 spec + brochure/data sheet | https://www.bellequipment.com/mining-construction/products/motor-graders/g200/ | Free | **verified**: 231 kW, 22 538 kg |
| **Bell Equipment** | Tracked carriers | TC11A spec sheet | https://www.bellequipment.com/mining-construction/products/tracked-carriers/tc11a/ | Free | **verified**: 177 kW, 11 000 kg payload |
| **Bell Equipment** | All | South Africa business unit | https://www.bellequipment.com/bell-south-africa/ | Free | **verified** |
| **Bell Equipment** | All | Dealer locator (Africa & ME) | https://www.bellequipment.com/mining-construction/africa-and-middle-east/dealerships/ | Free | **verified** |
| Babcock | Volvo CE dealer (SA) | Dealer / parts | https://www.babcock.co.za/ | Free | **verified** |
| Eqstra | Plant hire and fleet (SA) | Fleet services | https://www.eqstra.co.za/ | Free | **verified** |

---

## B. Cranes, lifting, MEWPs and telehandlers

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| Liebherr | Mobile & crawler cranes | Division page + model technical data | https://www.liebherr.com/en-gb/mobile-and-crawler-cranes/mobile-and-crawler-cranes-4284433 | Free | **verified** — LTM/LTC/LR/LG technical data and load charts by model |
| Liebherr | Tower cranes | Division page | https://www.liebherr.com/en-gb/tower-cranes/tower-cranes-4214732 | Free | **verified** — EC-B, EC-H, HC-L, K-series data |
| Manitowoc | Cranes | Group entry | https://www.manitowoc.com/ | Free | **verified** |
| Potain (Manitowoc) | Tower cranes | Brand hub | https://www.manitowoc.com/potain | Free | **verified** — MDT/MD/MR/Igo model data |
| Grove (Manitowoc) | Mobile cranes | Brand hub | https://www.manitowoc.com/grove | Free | **verified** — GMK/RT/TMS load charts by model |
| Tadano | Mobile cranes | Corporate | https://www.tadano.com/ | Free | **verified** |
| Tadano | Mobile cranes | Product index | https://www.tadano.com/products/ | Free | **verified** |
| Tadano | Mobile cranes | Support / service | https://www.tadano.com/support/ | Free | **verified** |
| Tadano America | Mobile cranes | Support and literature | https://www.tadanoamerica.com/support/ | Free | **verified** |
| Tadano America | Mobile cranes | Product site | https://www.tadanoamerica.com/ | Free | **verified** |
| Tadano Demag | Mobile cranes | Brand site | https://www.tadanodemag.com/ | Free | **verified** |
| Demag Mobile Cranes | Mobile cranes | Corporate | https://www.demagmobilecranes.com/ | Free | **verified** |
| Demag Mobile Cranes | Mobile cranes | Service and support | https://www.demagmobilecranes.com/en/service | Free | **verified** |
| Terex | Cranes, MP, aerials | Corporate | https://www.terex.com/ | Free | **verified** |
| Terex | All | Equipment index | https://www.terex.com/en/products-solutions/equipment | Free | **verified** |
| Terex | All | Parts portal | https://parts.terex.com/ | Mixed | **verified** — parts lookup; some functions need an account |
| Terex | All | Dealer locator | https://www.terex.com/en/find-a-dealer | Free | **verified** |
| **Genie** (Terex) | MEWPs, telehandlers | **Operator, service and parts manuals** | https://www.genielift.com/en/support/manuals | **Free** | **verified** — one of the best public manual libraries in the industry; download by model |
| Genie | MEWPs | Parts and serial-number lookup | https://www.genielift.com/en/support/parts | Free | **verified** |
| Genie | MEWPs | Product entry | https://www.genielift.com/en | Free | **verified** |
| **JLG** | MEWPs, telehandlers | **Technical publications (Online Express)** | https://onlineexpress.jlg.com/technical-publications | Reg. | **WAF-blocked** to automated fetch; the canonical JLG manuals route — operator, service, parts, illustrated parts |
| JLG | MEWPs | Online Express portal | https://onlineexpress.jlg.com/ | Reg. | **WAF-blocked**; parts ordering, warranty, publications |
| JLG | MEWPs | Corporate / product | https://www.jlg.com/en | Free | **verified** |
| JLG | MEWPs | BIM files | https://www.jlg.com/en/resources/bim-files | Free | **verified** |
| Haulotte | MEWPs | Corporate | https://www.haulotte.com/ | Free | **verified** |
| Haulotte | MEWPs | Product index | https://www.haulotte.com/en/products/ | Free | **verified** |
| Manitou | Telehandlers, MEWPs | Corporate (EN) | https://www.manitou.com/en | Free | **verified** |
| Manitou | Telehandlers | Product index | https://www.manitou.com/en/products | Free | **verified** |
| Manitou | Telehandlers | Documentation service page | https://www.manitou.com/en/services/documentation | Free | **verified** (routes via a country selector) |
| Manitou | Telehandlers | UK site | https://www.manitou.com/en-GB | Free | **verified** |
| Manitou | Telehandlers | South Africa site | https://www.manitou.com/en-ZA | Free | **verified** |
| Palfinger | Loader cranes, access | Corporate | https://www.palfinger.com/en | Free | **verified** |
| Palfinger | Loader cranes | Product index | https://www.palfinger.com/en/products | Free | **verified** |
| SARPA | Plant hire (SA) | Rental and plant association | https://www.sarpa.co.za/ | Free | **verified** — hire industry standards and members **[ZA]** |
| CPA | Plant hire (UK) | Construction Plant-hire Association | https://www.cpa.uk.net/ | Free | **verified** — good practice guides, incl. lifting and MEWP |
| IPAF | MEWPs | Operator training standard | https://www.ipaf.org/ | Free | **WAF-blocked**; the de facto MEWP operator categories (1a/1b/3a/3b) |
| HSE (UK) | All | Construction guidance | https://www.hse.gov.uk/construction/index.htm | Free | **verified** — free, high-quality guidance widely used as a reference in SADC |

---

## C. Concrete equipment and formwork

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| Putzmeister | Concrete pumps | Corporate | https://www.putzmeister.com/ | Free | **redirect-loop** under automated fetch (country cookie); opens normally in a browser |
| Schwing Stetter | Pumps, plants, mixers | Corporate | https://www.schwing-stetter.com/en/ | Free | **verified** |
| Schwing Stetter | Pumps, plants | Product index | https://www.schwing-stetter.com/en/products/ | Free | **verified** |
| Schwing | Concrete pumps | US/global site | https://www.schwing.com/ | Free | **verified** |
| CIFA | Pumps, mixers | Corporate | https://www.cifa.com/en/ | Free | **verified** |
| CIFA | Pumps, mixers | Product index | https://www.cifa.com/en/products/ | Free | **verified** |
| SANY | Concrete pumps | Global product index | https://www.sanyglobal.com/product/ | Free | **verified** |
| Liebherr | Concrete technology | Division page (mixers, plants, truck mixers) | https://www.liebherr.com/en-gb/concrete-technology/concrete-technology-4225787 | Free | **verified** |
| Ammann | Concrete/asphalt plants | Plants index | https://www.ammann.com/en-US/plants/asphalt-plants/ | Free | **verified** |
| Elkon | Batching plants | Corporate + product data | https://www.elkon.com/en/ | Free | **verified** — mobile and compact plants, common in Africa |
| Simem | Batching plants | Corporate | https://www.simem.com/ | Free | **verified** |
| Constmach | Batching plants, crushers | Corporate | https://www.constmach.com/ | Free | **verified** |
| **PERI** | Formwork, scaffolding | Group formwork products | https://www.peri.com/en/products/formwork.html | Free | **verified** |
| PERI | Scaffolding | Group scaffolding products | https://www.peri.com/en/products/scaffolding.html | Free | **verified** |
| PERI | Formwork | Group entry | https://www.peri.com/en.html | Free | **verified** — note: `/en/downloads.html` now redirects to a "content moved" page; use the country site |
| **PERI South Africa** | Formwork, scaffolding | **Local products + engineering** | https://www.peri.co.za/products.html | Free | **verified** — the correct route for **[ZA] [NA]** projects |
| PERI South Africa | Formwork | Services (design, hire) | https://www.peri.co.za/services.html | Free | **verified** |
| PERI UK | Formwork | UK country site | https://www.peri.co.uk/ | Free | **verified** — often has the fullest English download set |
| Doka | Formwork, scaffolding | Corporate entry | https://www.doka.com/en/index | Free | **verified** — user information (instructions for assembly and use) is reached from each system page |
| ULMA Construction | Formwork, scaffolding | Global site | https://www.ulmaconstruction.com/en | Free | **verified** |
| ULMA Construction | Formwork | **South Africa** | https://www.ulmaconstruction.co.za/ | Free | **verified** |
| Form-Scaff (Waco Africa) | Formwork, scaffolding | Corporate **[ZA]** | https://formscaff.com/ | Free | **verified** — the largest local formwork/scaffold hire company |
| Waco Africa | Scaffolding group | Group site **[ZA]** | https://waco.africa/ | Free | **verified** — note: `waco.co.za` is a parked domain, do not use |
| Waco Africa | Scaffolding | Alternate group domain | https://www.wacoafrica.co.za/ | Free | **verified** |
| UCO / Uco Group | Formwork, scaffolding | SA supplier | https://www.uco.co.za/ | Free | **verified** |
| Somero | Laser screeds | Corporate + product data | https://www.somero.com/ | Free | **verified** |
| Multiquip | Floats, screeds, pumps | Corporate | https://www.multiquip.com/ | Free | **verified** — Whiteman power trowels |
| Enar | Concrete vibrators | Corporate (EN) | https://www.enar.es/en | Free | **verified** |
| Husqvarna Construction | Cutting, drilling, floors | Global | https://www.husqvarnaconstruction.com/ | Free | **verified** |
| Husqvarna Construction | Cutting, drilling | **South Africa** | https://www.husqvarnaconstruction.com/za/ | Free | **verified** |

---

## D. Compaction, roads, paving, crushing

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| **Wirtgen Group** | Road machinery | Group entry (US/EN) | https://www.wirtgen-group.com/en-us/ | Free | **verified** — hub for all five brands |
| Wirtgen Group | Road machinery | International entry | https://www.wirtgen-group.com/international/en/ | Free | **verified** |
| Wirtgen Group | Road machinery | **Southern Africa** | https://www.wirtgen-group.com/en-za/ | Free | **verified** — regional parts and service **[ZA]** |
| **Wirtgen Group** | All brands | **Parts portal** | https://parts.wirtgen-group.com/ | Mixed | **verified** — parts search across Wirtgen, Vögele, Hamm, Kleemann, Benninghoven |
| **Wirtgen Group** | All brands | **Parts Media library** | https://parts.wirtgen-group.com/parts-media/ | Mixed | **verified** — parts documentation and media |
| Wirtgen Group | All brands | Hands-on equipment guides | https://www.wirtgen-group.com/en-us/parts-and-service/training/hands-on-manuals/ | Free | **verified** — practical operating guides |
| HAMM | Rollers | Product index + technical data | https://www.hamm.eu/en/products | Free | **verified** |
| HAMM | Rollers | Brand entry | https://www.hamm.eu/en/ | Free | **verified** |
| VÖGELE | Asphalt pavers | Product index + technical data | https://www.voegele.info/en/products/ | Free | **verified** |
| VÖGELE | Asphalt pavers | Brand entry | https://www.voegele.info/en/ | Free | **verified** |
| KLEEMANN | Crushers, screens | Product index | https://www.kleemann.info/en/products/ | Free | **verified** — MOBICAT, MOBIREX, MOBICONE, MOBISCREEN |
| KLEEMANN | Crushers | Brand entry | https://www.kleemann.info/en/ | Free | **verified** |
| BENNINGHOVEN | Asphalt plants | Brand entry | https://www.benninghoven.com/en/ | Free | **verified** |
| **BOMAG** | Compaction, paving, milling | Group entry | https://www.bomag.com/ww-en/ | Free | **verified** |
| **BOMAG** | All | **Machine documents** | https://www.bomag.com/ww-en/services/parts-options/machine-documents/ | Mixed | **verified** — the documented route to machine papers |
| BOMAG | All | Machinery categories + spec data | https://www.bomag.com/ww-en/machinery/categories/ | Free | **verified** |
| BOMAG | All | Extranet (parts catalogue) | https://extranet.bomag.com/ | Dealer | **verified** — login required; parts and service documentation |
| Dynapac | Rollers, pavers, planers | Corporate | https://dynapac.com/en | Free | **verified** |
| Dynapac | All | Product index | https://dynapac.com/en/products/ | Free | **verified** |
| Dynapac | All | Services / support | https://dynapac.com/en/services | Free | **verified** |
| Ammann | Compaction, pavers, plants | Corporate | https://www.ammann.com/en | Free | **verified** |
| Ammann | Soil & asphalt compactors | Product category | https://www.ammann.com/en-US/machines/soil-and-asphalt-compactors/ | Free | **verified** |
| Ammann | Light equipment | Product category | https://www.ammann.com/en-US/machines/light-equipment/ | Free | **verified** |
| Ammann | Asphalt pavers | Product category | https://www.ammann.com/en-US/machines/asphalt-pavers/ | Free | **verified** |
| Ammann | All machines | Machines index | https://www.ammann.com/en/machines | Free | **verified** |
| Wacker Neuson | Light equipment | Global gateway | https://www.wackerneuson.com/ | Free | **verified** — country selector; pick a regional site for manuals |
| Wacker Neuson | Light equipment | US site | https://www.wackerneuson.com/us | Free | **verified** |
| Wacker Neuson | Light equipment | US product index (spec sheets) | https://www.wackerneuson.com/us/products | Free | **verified** |
| Wacker Neuson | Light equipment | **South Africa** | https://www.wackerneuson.co.za/ | Free | **verified** |
| Weber MT | Plates, rammers | Corporate (EN) | https://www.webermt.com/en/ | Free | **verified** |
| Metso | Crushing, screening | Corporate | https://www.metso.com/ | Free | **verified** — Lokotrack, Nordberg |
| Sandvik | Rock processing | Rock Technology site | https://www.rocktechnology.sandvik/en/ | Free | **verified** |
| Terex Finlay | Crushing, screening | Brand hub | https://www.terex.com/finlay | Free | **verified** |
| Finlay | Crushing, screening | Brand site | https://www.finlay.com/ | Free | **verified** |
| Powerscreen | Crushing, screening | Corporate | https://www.powerscreen.com/ | Free | **verified** |

---

## E. Power tools, fixings and diamond tooling

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| **Hilti** | Tools, anchors, firestop | **Technical Library (ZA)** | https://www.hilti.co.za/technical-library | Free | **verified** — **6 406 documents**: 1 949 Operating Instructions, 1 363 Approvals, 1 147 CAD/BIM typicals, 248 Instructions for Use, 213 Technical Information, 60 MSDS, 35 Certificates. Filter by category, document type and language |
| **Hilti** | Tools, anchors | **Technical Library (global)** | https://www.hilti.com/technical-library | Free | **verified** — same library, global entry |
| Hilti | Anchors, engineering | Engineering solutions **[ZA]** | https://www.hilti.co.za/content/hilti/META/ZA/en/business/business/engineering.html | Free | **verified** — route to PROFIS Engineering |
| Hilti | Engineering | Engineering support **[ZA]** | https://www.hilti.co.za/content/hilti/META/ZA/en/support/support/engineering-support.html | Free | **verified** |
| Hilti | Chemical anchors | Product catalogue **[ZA]** | https://www.hilti.co.za/c/CLS_FASTENER_7135/CLS_CHEMICAL_ANCHORS_7135 | Free | **verified** — HIT-HY 200 / RE 500 / HY 170 family |
| Hilti | Mechanical anchors | Product catalogue **[ZA]** | https://www.hilti.co.za/c/CLS_FASTENER_7135/CLS_MECHANICAL_ANCHORS_7135 | Free | **verified** |
| Hilti | Firestop | Product catalogue **[ZA]** | https://www.hilti.co.za/c/CLS_FIRESTOP_PROTECTION_7131 | Free | **verified** — 3 072 firestop documents in the technical library |
| Hilti | Corporate | Global entry | https://www.hilti.com/ | Free | **verified** |
| Hilti | Corporate | South Africa entry | https://www.hilti.co.za/ | Free | **verified** |
| **Bosch Professional** | Power tools | **User manuals download (ZA)** | https://www.bosch-professional.com/za/en/services/downloads/user-manuals/index.html | Free | **verified** — operating instructions by model, no registration |
| Bosch Professional | Power tools | Catalogues download | https://www.bosch-professional.com/za/en/services/downloads/catalogues/ | Free | **verified** |
| Bosch Professional | Power tools | Downloads index | https://www.bosch-professional.com/za/en/services/downloads/ | Free | **verified** |
| Bosch Professional | Cordless | 18V Professional System | https://www.bosch-professional.com/za/en/18v-cordless-system/ | Free | **verified** — battery platform reference |
| Bosch Professional | Power tools | South Africa entry | https://www.bosch-professional.com/za/en/ | Free | **verified** |
| Bosch Professional | Power tools | UK entry | https://www.bosch-professional.com/gb/en/ | Free | **verified** |
| **Makita** | Power tools | **Manuals library (UK)** | https://www.makita.co.uk/support/manuals.html | Free | **verified** — download by model |
| Makita | Power tools | UK entry | https://www.makita.co.uk/ | Free | **verified** |
| Makita | Power tools | Global entry | https://www.makita.com/ | Free | **verified** |
| Makita | Power tools | **South Africa** | https://www.makita.co.za/ | Free | **verified** |
| DEWALT | Power tools | Support and manuals | https://www.dewalt.com/support | Free | **verified** — manuals, parts diagrams, service centres |
| DEWALT | Power tools | US entry | https://www.dewalt.com/ | Free | **verified** |
| DEWALT | Power tools | UK entry | https://www.dewalt.co.uk/ | Free | **verified** |
| Milwaukee Tool | Power tools | Support / manuals | https://www.milwaukeetool.com/Support | Free | **verified** — operator manuals, parts lists, ONE-KEY |
| Milwaukee Tool | Power tools | US entry | https://www.milwaukeetool.com/ | Free | **verified** |
| Milwaukee Tool | Power tools | Europe support | https://www.milwaukeetool.eu/support/ | Free | **verified** |
| Milwaukee Tool | Power tools | Europe entry | https://www.milwaukeetool.eu/ | Free | **verified** |
| Metabo | Power tools | Global (EN) | https://www.metabo.com/com/en/ | Free | **verified** — CAS battery alliance |
| Metabo | Power tools | **South Africa** | https://www.metabo.com/za/en/ | Free | **verified** |
| Metabo | Power tools | Corporate entry | https://www.metabo.com/ | Free | **verified** |
| Festool | Power tools | UK entry | https://www.festool.co.uk/ | Free | **verified** |
| Festool | Power tools | Service all-inclusive | https://www.festool.co.uk/services/service-all-inclusive | Free | **verified** |
| Festool | Power tools | Services index | https://www.festool.co.uk/services | Free | **verified** |
| Festool | Power tools | Global entry | https://www.festool.com/ | Free | **verified** |
| Festool | Power tools | US entry | https://www.festoolusa.com/ | Free | **verified** |
| Ryobi | Power tools | Support and manuals | https://www.ryobitools.com/support | Free | **verified** |
| Ryobi | Power tools | Product entry | https://www.ryobitools.com/ | Free | **verified** |
| Leica (Disto) | Laser measuring | DISTO brand site | https://www.disto.com/ | Free | **verified** |
| RS Components | Tools, electrical | SA trade catalogue | https://za.rs-online.com/ | Free | **verified** — datasheets attached to most line items |

---

## F. Woodworking and joinery machinery

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| SCM Group | Woodworking | Group entry | https://www.scmgroup.com/en_US/ | Free | **verified** |
| SCM Group | Woodworking | SCM Wood division | https://www.scmgroup.com/en_US/scmwood | Free | **verified** |
| SCM Group | Woodworking | Product index (spec sheets) | https://www.scmgroup.com/en_US/scmwood/products | Free | **verified** |
| SCM Group | Woodworking | Services / support | https://www.scmgroup.com/en_US/scmwood/services | Free | **verified** |
| **Felder Group** | Woodworking | **South Africa (direct subsidiary)** | https://www.felder-group.com/en-za | Free | **verified** — Felder, Format-4, Hammer, MAYER; +27 12 643 0515 **[ZA] [NA]** |
| Felder Group | Woodworking | Products (ZA) | https://www.felder-group.com/en-za/products | Free | **verified** |
| Felder Group | Woodworking | Service and support (ZA) | https://www.felder-group.com/en-za/service | Free | **verified** — free catalogue, warranty, how-to videos |
| Format-4 | Woodworking | Brand site | https://www.format4.com/ | Free | **verified** |
| Format-4 | Woodworking | International entry | https://www.format4.com/en-int | Free | **verified** |
| Hammer | Woodworking | Brand site | https://www.hammer.at/en | Free | **verified** |
| Hammer | Woodworking | Product index | https://www.hammer.at/en/products | Free | **verified** |
| Altendorf | Sliding table saws | Group entry | https://www.altendorfgroup.com/en | Free | **verified** |
| Altendorf | Sliding table saws | Product index | https://www.altendorfgroup.com/en/products | Free | **verified** |
| Altendorf | Sliding table saws | Service | https://www.altendorfgroup.com/en/service | Free | **verified** |
| Altendorf | Sliding table saws | Contact / agents | https://www.altendorfgroup.com/en/contact | Free | **verified** — use to find the current SA agent |
| Altendorf | Sliding table saws | Alternate domain | https://www.altendorf.com/en/ | Free | **verified** |
| HOMAG | Industrial woodworking | Corporate | https://www.homag.com/en | Free | **verified** |
| HOMAG | Industrial woodworking | Service | https://www.homag.com/en/service | Free | **verified** |
| HOMAG | Industrial woodworking | Locations (find local service) | https://www.homag.com/en/company/locations | Free | **verified** |
| Biesse | Woodworking, CNC | Corporate | https://www.biesse.com/ | Free | **verified** |
| MARTIN | Precision woodworking | Corporate (EN) | https://www.martin.info/en/ | Free | **verified** |
| MARTIN | Precision woodworking | Product index | https://www.martin.info/en/products/ | Free | **verified** |
| MARTIN | Precision woodworking | Service | https://www.martin.info/en/service/ | Free | **verified** |
| Laguna Tools | Woodworking | Corporate | https://lagunatools.com/ | Free | **verified** |
| Laguna Tools | Woodworking | Support / manuals | https://lagunatools.com/support/ | Free | **verified** |
| Laguna Tools | Woodworking | Full product catalogue | https://lagunatools.com/collections/all | Free | **verified** |

---

## G. Survey and measurement instruments

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| Leica Geosystems | Survey | Corporate entry | https://leica-geosystems.com/ | Free | **verified** |
| Leica Geosystems | Survey | UK/EN entry | https://leica-geosystems.com/en-gb | Free | **verified** |
| Leica Geosystems | Survey | Products index | https://leica-geosystems.com/products | Free | **verified** |
| Leica Geosystems | Total stations | Product category + data sheets | https://leica-geosystems.com/products/total-stations | Free | **verified** |
| Leica Geosystems | GNSS | Product category + data sheets | https://leica-geosystems.com/products/gnss-systems | Free | **verified** |
| Leica Geosystems | Laser scanners | Product category + data sheets | https://leica-geosystems.com/products/laser-scanners | Free | **verified** |
| Leica Geosystems | Levels | Product category + data sheets | https://leica-geosystems.com/products/levels | Free | **verified** |
| **Leica Geosystems** | All | **myWorld customer portal** | https://myworld.leica-geosystems.com/ | Reg. | **verified** — the manuals, firmware and licence portal for registered instruments |
| Hexagon | Geospatial | GeoCloud platform | https://geocloud.hexagon.com/ | Reg. | **verified** |
| Trimble | Survey, construction | Corporate | https://www.trimble.com/ | Free | **verified** |
| Trimble | Construction | Construction division | https://construction.trimble.com/ | Free | **verified** |
| **Trimble** | Geospatial | **Help / documentation portal** | https://help.trimblegeospatial.com/ | Free | **verified** — product help, user guides and release notes |
| Topcon | Survey, machine control | Corporate | https://www.topconpositioning.com/ | Free | **verified** |
| Topcon | Survey | Support hub | https://www.topconpositioning.com/support | Free | **verified** |
| **Topcon** | Survey | **myTopcon NOW! self-service** | https://mytopcon.topconpositioning.com/ | Reg. | **verified** — product manuals, e-learning, firmware, troubleshooting |
| Topcon | Survey | myTopcon support section | https://mytopcon.topconpositioning.com/support | Reg. | **verified** |
| Sokkia | Survey | Corporate | https://sokkia.com/ | Free | **verified** |
| Sokkia | Survey | US site | https://us.sokkia.com/ | Free | **verified** — manuals and data sheets by model |
| Sokkia | Survey | Europe site | https://eu.sokkia.com/ | Free | **verified** |
| Leica (Disto) | Laser measuring | DISTO product site | https://www.disto.com/ | Free | **verified** |

---

## H. Generators, pumps, compressors, welding

| Manufacturer | Category | Resource type | URL | Access | Notes |
|---|---|---|---|---|---|
| **Cummins** | Engines, gensets | **QuickServe Online (service info)** | https://quickserve.cummins.com/ | Reg. | **verified** — serial-number-driven service manuals, wiring diagrams, specs. The single best engine documentation portal in the industry |
| **Cummins** | Engines, gensets | **Cummins Mart (parts catalogue)** | https://mart.cummins.com/ | Reg. | **verified** — parts lookup by engine serial |
| Cummins | Gensets | Corporate | https://www.cummins.com/ | Free | **WAF-blocked**; product data and brochures |
| Perkins | Engines | Corporate | https://www.perkins.com/ | Free | **WAF-blocked**; engine spec sheets and the SPI²/Perkins parts route |
| Caterpillar | Gensets | Corporate | https://www.cat.com/ | Free | **WAF-blocked**; Cat generator set spec sheets |
| MTU (Rolls-Royce) | Engines, gensets | Corporate | https://www.mtu-solutions.com/ | Free | **verified** |
| Smith Power Equipment | Gensets, engines | **SA distributor** | https://www.smithpower.co.za/ | Free | **verified** — multi-brand SA distributor **[ZA]** |
| **LORENTZ** | Solar pumps | Product index | https://www.lorentz.de/products/ | Free | **verified** — PS2/PSk solar submersibles |
| **LORENTZ** | Solar pumps | **partnerNET technical portal** | https://partnernet.lorentz.de/ | Dealer | **verified** — sizing (COMPASS), manuals, partner technical data |
| LORENTZ | Solar pumps | Corporate | https://www.lorentz.de/ | Free | **verified** |
| Franklin Electric | Submersible pumps/motors | Corporate | https://www.franklin-electric.com/ | Free | **verified** — motor and pump technical data, AIM manual |
| Franklin Electric | Water systems | Franklin Water | https://www.franklinwater.com/ | Free | **verified** |
| Pump Solutions | Pumps | SA supplier | https://www.pumpsolutions.co.za/ | Free | **verified** **[ZA]** |
| Grundfos | Pumps | Product Center (selection tool) | https://product-selection.grundfos.com/ | Free | **not reachable from this environment** — status `needs-verification`; the standard pump selection and documentation tool, open it directly in a browser |
| Atlas Copco | Compressors, gensets, lighting | **South Africa** | https://www.atlascopco.com/en-za | Free | **verified** **[ZA]** |
| Atlas Copco | Compressors | UK entry | https://www.atlascopco.com/en-uk | Free | **verified** |
| Atlas Copco | Construction equipment | Construction range | https://www.atlascopco.com/en-uk/construction-equipment | Free | **verified** — portable compressors, lighting towers, gensets |
| Ingersoll Rand | Compressors | Corporate | https://www.ingersollrand.com/ | Free | **WAF-blocked** (rate-limited); product literature and parts |
| Lincoln Electric | Welding | Corporate | https://www.lincolnelectric.com/ | Free | **WAF-blocked**; operator manuals and welding procedure resources |
| ESAB | Welding | Corporate | https://esab.com/ | Free | **WAF-blocked**; manuals and consumable data sheets |
| Miller (ITW) | Welding | Corporate | https://www.millerwelds.com/ | Free | **WAF-blocked** (rate-limited); Miller publishes owner's manuals free by model |
| WearCheck | Oil analysis | SA condition-monitoring lab | https://www.wearcheck.co.za/ | Free | **verified** — oil and fluid analysis for plant fleets **[ZA] [NA]** |

---

## I. Aggregators and third-party spec databases

These are the fallback when a manufacturer has withdrawn a model or when you need to compare across brands. **None of them is a primary source.** Always prefer the OEM PDF; where you must use an aggregator, record which one and treat the figure as indicative.

| Site | URL | Access | Coverage | Reliability assessment |
|---|---|---|---|---|
| **RitchieSpecs** (Ritchie Bros.) | https://www.ritchiespecs.com/ | Free | Very broad — construction, mining, agricultural, lifting; includes long-discontinued models | **Good.** Data is transcribed from OEM literature by an auctioneer that must describe machines accurately for sale. Best free source for **older models** no longer on OEM sites. Occasional unit-conversion and configuration ambiguity (which bucket, which undercarriage) — the configuration is often not stated |
| RitchieSpecs | https://www.ritchiespecs.com/manufacturers | Free | Manufacturer index | **verified** — useful as a browse entry point |
| **LECTURA Specs** | https://www.lectura-specs.com/en | Mixed | Very broad European coverage, with valuations | **Good for Europe.** German publisher, long-established, with a paid valuation product behind it. **WAF-blocked** to automated fetch. Free tier gives specs; deeper data and valuations are paid |
| LECTURA (group) | https://www.lectura.de/ | Mixed | Publisher site | **WAF-blocked** |
| **Machinery Trader** | https://www.machinerytrader.com/ | Free | North American listings with attached spec pages | **Moderate.** Spec pages are useful but listing data is seller-entered and frequently wrong on hours, configuration and year. Use the *spec* pages, not the *listing* data. **WAF-blocked** |
| **Mascus** | https://www.mascus.com/ | Free | Global used-equipment marketplace | **Moderate.** Excellent for market pricing and for seeing what actually circulates in a region; specs are seller-entered and unreliable |
| Mascus South Africa | https://www.mascus.co.za/ | Free | SADC used market | **verified** — the best single view of the **[ZA]** used plant market |
| **Konedata** | https://www.konedata.net/ | Free | Machine model histories, production years, variants | **Good for provenance.** Community-maintained; strongest on model chronology and variant identification, weaker on precise specs |
| Bauforum24 | https://www.bauforum24.biz/ | Free | German-language forum, brochures archive, technical discussion | **Moderate but valuable.** The brochure archive and the practitioner discussion are genuinely useful; forum posts are not citable |
| Construction Equipment (magazine) | https://www.constructionequipment.com/ | Free | US trade press, spec guides | **Moderate.** Editorial spec guides are compiled from OEM data; good for market context |
| Diggers & Dozers | https://www.diggersanddozers.com/ | Free | UK plant news and spec content | **Low-moderate.** Useful for news, not for authoritative specs |
| Plant & Equipment | https://www.plantandequipment.com/ | Free | Middle East / global marketplace | **Low-moderate.** Listing-driven |
| Machines4U | https://www.machines4u.com.au/ | Free | Australian marketplace with spec pages | **Low-moderate.** Listing-driven |
| Equipment World | https://www.equipmentworld.com/ | Free | US trade press | **Moderate.** **WAF-blocked**; good editorial, spec data is secondary |
| ForConstructionPros | https://www.forconstructionpros.com/ | Free | US trade press and product database | **Moderate.** **WAF-blocked** |

### Rule for citing an aggregator
1. Prefer the OEM PDF. If the model is current, there is almost always one.
2. If the model is discontinued, try **RitchieSpecs** first, then **LECTURA**, then **Konedata** for the variant history.
3. Record **which** aggregator and the date. Aggregator pages change silently.
4. Never use a marketplace *listing* as a spec source. Seller-entered hours, year and configuration are wrong often enough to matter.
5. Cross-check any figure you are going to use structurally (lift capacity, payload, GBP) against a second source or the OEM directly.

---

## J. Regulatory, standards and industry bodies

| Body | URL | Access | Notes |
|---|---|---|---|
| SA Department of Employment and Labour | https://www.labour.gov.za/ | Free | **verified** — OHS Act 85/1993, Construction Regulations, Driven Machinery Regulations **[ZA]** |
| CIDB (SA) | https://www.cidb.org.za/ | Free | **verified** — contractor grading, standards for uniformity **[ZA]** |
| Master Builders South Africa | https://www.mbsa.org.za/ | Free | **verified** **[ZA]** |
| SARPA | https://www.sarpa.co.za/ | Free | **verified** — plant hire standards **[ZA]** |
| SAIOSH | https://www.saiosh.co.za/ | Free | **WAF-blocked** — SA institute of OSH; competence and CPD **[ZA]** |
| HSE (UK) | https://www.hse.gov.uk/construction/index.htm | Free | **verified** — freely available, technically strong guidance widely used in SADC |
| CPA (UK) | https://www.cpa.uk.net/ | Free | **verified** — plant-hire good practice guides |
| IPAF | https://www.ipaf.org/ | Free | **WAF-blocked** — MEWP operator training standard |

---

## Register statistics

- **Unique URLs in this register: 283**, every one requested on 2026-08-25.
- **263 returned HTTP 200/202 (verified).** **19** are real URLs behind bot protection or a country-cookie redirect (**WAF-blocked** / **redirect-loop**): Caterpillar (cat.com, parts.cat.com, safety.cat.com), Cummins corporate, Perkins, JLG Online Express (×2), LECTURA (×2), Machinery Trader, Equipment World, ForConstructionPros, IPAF, SAIOSH, Lincoln Electric, ESAB, Miller, Ingersoll Rand, Putzmeister. **1** (Grundfos Product Center) was not reachable from this environment at all and is marked `needs-verification`.
- **Table rows: 290** (a few resources appear under more than one category by design, e.g. Bell model pages and the Leica DISTO).
- **Categories covered:** earthmoving, cranes/lifting, concrete/formwork, compaction/roads/crushing, power tools/fixings, woodworking, survey, generators/pumps/compressors/welding, aggregators, regulatory.
- **Manufacturers with a genuinely open, model-level manual library (no login):** Genie, Bosch Professional, Makita, DEWALT, Milwaukee, Hilti (Technical Library), BOMAG (machine documents), Wirtgen Group (hands-on manuals), Bell Equipment (per-model brochure + data sheet).
- **Manufacturers requiring registration for the real documentation:** JLG (Online Express), Cummins (QuickServe), Leica (myWorld), Topcon (myTopcon NOW!), LORENTZ (partnerNET), BOMAG (extranet), Caterpillar (parts.cat.com).

## Sources

All URLs in the tables above were requested on 2026-08-25 and are cited in place. The principal documentation portals, restated:

- [Hilti Technical Library](https://www.hilti.co.za/technical-library) — Hilti, accessed 2026-08-25
- [Genie manuals](https://www.genielift.com/en/support/manuals) — Genie/Terex, accessed 2026-08-25
- [Bosch Professional user manuals](https://www.bosch-professional.com/za/en/services/downloads/user-manuals/index.html) — Robert Bosch, accessed 2026-08-25
- [Makita UK manuals](https://www.makita.co.uk/support/manuals.html) — Makita, accessed 2026-08-25
- [BOMAG machine documents](https://www.bomag.com/ww-en/services/parts-options/machine-documents/) — BOMAG, accessed 2026-08-25
- [Wirtgen Group Parts Media](https://parts.wirtgen-group.com/parts-media/) — Wirtgen Group, accessed 2026-08-25
- [Cummins QuickServe Online](https://quickserve.cummins.com/) — Cummins, accessed 2026-08-25
- [Leica myWorld](https://myworld.leica-geosystems.com/) — Leica Geosystems, accessed 2026-08-25
- [myTopcon NOW!](https://mytopcon.topconpositioning.com/) — Topcon, accessed 2026-08-25
- [Trimble Geospatial help](https://help.trimblegeospatial.com/) — Trimble, accessed 2026-08-25
- [LORENTZ partnerNET](https://partnernet.lorentz.de/) — Bernt Lorentz, accessed 2026-08-25
- [RitchieSpecs](https://www.ritchiespecs.com/) — Ritchie Bros., accessed 2026-08-25
- [Konedata](https://www.konedata.net/) — accessed 2026-08-25
- [Mascus South Africa](https://www.mascus.co.za/) — accessed 2026-08-25

## Open questions

- **Grundfos**: neither `grundfos.com` nor `product-selection.grundfos.com` was reachable from this environment (DNS/proxy level, not a 403). The Grundfos Product Center is the industry-standard pump selection and documentation tool and should be opened directly. Status `needs-verification`.
- **Caterpillar**: cat.com, parts.cat.com and safety.cat.com all return 403 to automated clients. The URLs are correct and current but could not be status-verified here.
- **PERI**: the group-level `/en/downloads.html` path now serves a "content has moved" notice; downloads have been devolved to country sites. Use `peri.co.za` for **[ZA] [NA]**.
- **Doka**: no stable public downloads URL was found at group level; user information (instructions for assembly and use) is reached from each system's product page. Worth re-checking.
- **JCB**: JCB does not publish a general public operator-manual library; literature is dealer-routed. `jcb.com/en-gb/support` is the correct entry point.
- Several sites are single-page applications that return HTTP 200 for unknown paths. Where a URL below is used programmatically, content-check the response, do not trust the status code alone.
