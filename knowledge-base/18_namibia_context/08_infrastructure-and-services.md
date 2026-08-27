---
id: namibia.infrastructure
title: Namibian infrastructure and services — power, water, telecoms, roads, fuel, waste
domain: 18_namibia_context
tags: [namibia, ohangwena, okongo, nampower, nored, namwater, boreholes, ohangwena-aquifer, mtc, telecom-namibia, roads, fuel, waste, off-grid-solar, electrification]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "NamPower", url: "https://en.wikipedia.org/wiki/NamPower", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "NamPower corporate site", url: "https://www.nampower.com.na/Page.aspx?p=181", publisher: "NamPower", accessed: 2026-08-25}
  - {title: "NORED — Northern Regional Electricity Distributor", url: "https://www.nored.com.na/", publisher: "NORED", accessed: 2026-08-25}
  - {title: "Water supply and sanitation in Namibia", url: "https://en.wikipedia.org/wiki/Water_supply_and_sanitation_in_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Telecom Namibia", url: "https://en.wikipedia.org/wiki/Telecom_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "MTC Namibia", url: "https://en.wikipedia.org/wiki/MTC_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Namibia 2023 Census Dissemination Portal", url: "https://census.nsa.org.na/", publisher: "Namibia Statistics Agency", accessed: 2026-08-25}
  - {title: "PVGIS v5.2 irradiation at Okongo", url: "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json", publisher: "European Commission JRC", accessed: 2026-08-25}
related: [namibia.overview, namibia.geology_soils, namibia.climate, namibia.economy, logistics.last_mile, paving.overview]
unit_system: SI
---

# Namibian infrastructure and services — power, water, telecoms, roads, fuel, waste

**Summary.** Namibia's service infrastructure is a national-scale system serving a very small, very dispersed population, and it thins dramatically with distance from Windhoek and the coast. **NamPower** generates and transmits (**563.5 MW installed capacity, 12 043 km of transmission lines**) and sells bulk power to **Regional Electricity Distributors** — in the north, **NORED**, the Northern Regional Electricity Distributor. **NamWater** is the bulk water supplier; rural water supply is the responsibility of the ministry's rural water directorate, and in Ohangwena it means **boreholes and the Kunene pipeline**, with the deep **Ohangwena II aquifer** as the strategic reserve. **MTC** and **Telecom Namibia** cover the villages well and the sandveld patchily. Roads to Okongo are tarred; roads beyond it are sand. And with **2 275 kWh/m²/yr** of irradiance, **off-grid solar is not a compromise here — it is frequently the rational primary supply.**

## Key facts

| Parameter | Value | Source |
|---|---|---|
| NamPower installed capacity | **563.50 MW** | NamPower site |
| NamPower transmission lines | **12 043 km** | NamPower site |
| Ruacana Hydroelectric Power Station | **347 MW**, Kunene River at the Angolan border | Wikipedia |
| Van Eck Power Station, Windhoek | **120 MW**, coal-fired thermal | Wikipedia |
| Anixas Thermal Power Station, Walvis Bay | **22.5 MW**, diesel | Wikipedia |
| Regulator | **Electricity Control Board (ECB)** | Wikipedia |
| Northern distributor | **NORED — Northern Regional Electricity Distributor**; toll-free **0800 000 100** | NORED site |
| NORED coverage confirmed | Northern Namibia, including **Oshikoto and Ohangwena** | NORED outage notices |
| Bulk water utility | **NamWater** (created 1997); **16 dams, 14 transmission lines, 16 water treatment plants** | Wikipedia |
| Sector law | **Water Resources Management Act, 2013 (No. 11 of 2013)** | FAOLEX via Wikipedia |
| Rural water supply responsibility | **Directorate of Rural Water Supply**, Ministry responsible for water | Wikipedia |
| Namibia households (2023 census) | **756 339** | NSA census portal |
| Boreholes drilled in Namibia | **>100 000**, about half still operating | GIZ/Atlas |
| Ohangwena II aquifer | **~5 bn m³**, ~300 m deep, artesian, ~400 years of northern supply | BGR / BBC |
| Telecom Namibia | Established **August 1992**; **>396 000 fixed and mobile customers**; **>13 000 km backbone fibre**; **>300 towers**; **986 employees**; ~**N$1.5 bn** revenue | Wikipedia |
| MTC | Established **1995**; **>2 million active subscribers**; largest mobile carrier | Wikipedia |
| Subsea cables landed/used | **SAT-3, SEACOM, WACS, Equiano** | Telecom Namibia |
| Okongo GHI | **2 275 kWh/m²/yr; 6.23 kWh/m²/day** | PVGIS |
| Okongo services | Electricity, water and sanitation in the village; **62-bed district hospital**; landing strip | Wikipedia |

---

## 1. Electricity

### 1.1 Generation and the national position
NamPower — founded in **1964 as SWAWEK** and renamed in **1996** — is licensed to generate, transmit, supply and trade electricity, including import and export. Its three major generating stations are:

| Station | Type | Capacity |
|---|---|---|
| **Ruacana** | Hydroelectric, Kunene River | **347 MW** |
| **Van Eck** (Windhoek) | Coal thermal | **120 MW** |
| **Anixas** (Walvis Bay) | Diesel | **22.5 MW** |

Total published installed capacity is **563.50 MW** and the transmission network runs to **12 043 km**.

Two structural facts follow. First, **Ruacana dominates domestic generation and depends on Kunene River flow** — NamPower publishes the river flow (e.g. **120.20 m³/s**) as a headline operational indicator, because a poor rainy season in Angola directly reduces Namibian generating capacity. Second, **Namibia imports a substantial share of its electricity**, principally from South Africa and the Southern African Power Pool, which makes national supply security dependent on Eskom's condition.

> **Implication for a builder:** **assume supply interruptions.** Even on a grid-connected site in Okongo, design for outages: a battery or generator changeover for critical loads, no total dependence on mains for water pumping, and surge protection at the point of entry.

### 1.2 Distribution and NORED
NamPower sells bulk power to **Regional Electricity Distributors (REDs)** and retains a direct distribution role "particularly in areas where Regional Electricity Distributors have not yet been established". Activities are licensed and regulated by the **Electricity Control Board (ECB)**.

**NORED — the Northern Regional Electricity Distributor — is the utility serving northern Namibia, including Ohangwena.** This is confirmed directly by NORED's own outage notices, which reference the **Oshikoto and Ohangwena Regions**, and by its joint operational announcements with NamPower.

NORED's published customer-facing services include a **Customer Service Charter**, **Conditions of Supply**, **Electricity Tariffs**, **New Connections Applications**, payment methods, and fault reporting. Contact: **toll-free 0800 000 100**; head office switchboard **083 282 2100**.

> `needs-verification`: **NORED's exact regional footprint, tariff schedule and connection fees.** The published tariff and connection-cost pages could not be read in this session. **Obtain the current ECB-approved NORED tariff schedule and the New Connections application pack before budgeting any connection.**

**The connection process, in outline** (confirm each step with NORED):
1. Application for a new connection, with proof of land right / erf ownership and a site plan.
2. Quotation for the connection — for a rural site this is dominated by **distance to the nearest reticulation and the cost of poles, conductor and a transformer**, and can easily exceed the cost of the building.
3. Payment of the connection charge and any capital contribution.
4. An approved electrical **Certificate of Compliance (COC)** for the installation, issued by a registered electrician.
5. Meter installation — **prepaid metering is the norm** for residential customers in Namibia.

> ⚠️ **The single most important electricity decision at Okongo is made before design: is the site within economic reach of NORED reticulation, or not?** A village erf is; a homestead 8 km down a sand track very likely is not, and the transformer-and-line quotation will confirm it. **Get the quotation early**, because it determines whether the project is grid-connected, hybrid, or fully off-grid — and that determines the electrical design, the appliance selection, the water pumping strategy and the cooling strategy.

### 1.3 Rural electrification in Ohangwena
Rural electrification has expanded substantially since independence through NamPower's rural electrification programme and REDs, but Ohangwena remains among the least-served regions: it is **85.5 % rural** with a **dispersed homestead settlement pattern**, which is the most expensive possible geometry for grid extension.

> `needs-verification`: **the current proportion of Ohangwena households with grid electricity.** A figure of **20.7 % of households using electricity for lighting** appears in domain 11 from earlier census reporting; the 2023 census figure was not retrievable in this session and should be obtained from the NSA census portal or the Ohangwena Regional Profile.

---

## 2. Water

### 2.1 Institutions
- **NamWater** — state-owned bulk water supplier, created **1997**, operating **16 dams, 14 water transmission lines and 16 water treatment plants**. It sells to mines and to municipalities, which reticulate and resell.
- **The Directorate of Rural Water Supply** in the responsible ministry handles **rural** water supply and sanitation — which is what applies outside proclaimed local authority areas.
- **The Water Resources Management Act, 2013 (No. 11 of 2013)** is the governing statute.

### 2.2 How the north is supplied
The Cuvelai regions are supplied principally by **canal and pipeline from the Cunene River at Ruacana** — a scheme the BBC described in 2012 as "a 40-year-old canal that brings the scarce resource across the border from Angola", serving about **800 000 people**. Namibia's allocation from the Cunene is **180 Mm³/yr**, far more than the ~23 Mm³ actually abstracted at Ruacana as of 1999.

Piped supply reaches the towns and the main settlements along the tarred road. **It thins rapidly with distance**, and the further east one goes in Ohangwena — toward Okongo — the more supply depends on boreholes and on rainwater.

### 2.3 Boreholes and the Ohangwena aquifer
See `03_geology-and-soils.md` for the geology. The operational summary:

- **Shallow groundwater in the Cuvelai is generally saline**, which is exactly why so few boreholes were ever drilled there and why the Kunene pipeline was built instead.
- **Ohangwena II** — identified in 2012 by BGR with the Namibian government — is a **~70 × 40 km, ~300 m deep, artesian, fresh-water aquifer holding roughly 5 billion m³ of water up to 10 000 years old**, capable of supplying the north for about **400 years** at current consumption and of buffering **up to 15 years of drought**.
- **A saline aquifer sits directly on top of it.** Badly cased boreholes can create a hydraulic short circuit and contaminate the deep water.
- **Sustainable management** guidance is to limit normal abstraction to the recharge inflow from Angola and treat the store as a drought reserve.

> ⚠️ **If you drill in Ohangwena, case and grout-seal properly through the saline horizon.** This is a regional public-good obligation, not just a site issue.

### 2.4 What to plan for on a rural Okongo site
1. **Establish the actual source first**: village reticulation, an existing community borehole, or a new borehole.
2. **Test the water before designing around it.** Salinity determines pipework material, appliance life and whether the water can be used for concrete.
3. **Store.** Whatever the source, storage is mandatory — supply is interruptible and rainfall is seasonal. Elevated tanks give pressure without a pump; ground tanks with a pressure pump give more capacity.
4. **Harvest rainwater.** At 590 mm/yr on a 100 m² roof, gross yield is about **59 m³/yr**; after a runoff coefficient of ~0.8 and first-flush losses, budget roughly **45–47 m³/yr** — enough to make a real contribution to a household. It is also the **best-quality water available** on a saline-groundwater site. Size storage for the six-month dry season, not for the annual total.
5. **Sanitation.** Free-draining Kalahari sand is good for soakaways in the dry season and problematic where the water table rises seasonally. In the Cuvelai, an elevated or sealed system may be necessary. **Do not site a soakaway or pit latrine upgradient of a borehole**, and observe the minimum separation distance required by the local authority.
6. **Greywater** reuse for planting and shade trees is worth designing in from the start.

---

## 3. Telecommunications

**MTC** (Mobile Telecommunications Limited), established **1995**, is the largest mobile carrier with **over two million active subscribers**. **Telecom Namibia**, established **August 1992** and wholly state-owned, serves **over 396 000 fixed and mobile customers**, employs **986 people**, and operates **more than 13 000 km of backbone fibre**, **500+ IP/MPLS points of presence** and **over 300 towers**. It acquired **TN Mobile** in 2013. Other operators include **Paratus Telecom** and **MTN Namibia**.

Namibia is well connected internationally: Telecom Namibia has invested in the **SAT-3, SEACOM, WACS and Google Equiano** subsea cables, positioning itself as a regional internet hub for SADC.

**Coverage reality in Ohangwena:**
- **Villages and the tarred road corridor are well covered** by MTC, generally with 4G/LTE.
- **Coverage away from the road is patchy and terrain-independent** — the land is flat, so coverage is a function of tower spacing, not shadowing. Signal degrades with distance from the village.
- **Fixed-line and fibre are essentially urban.** Do not assume fibre at Okongo.
- **Practical solution for a rural site:** an **external directional antenna on a mast** feeding an LTE router, which will frequently convert an unusable indoor signal into a workable connection. Design in a mast position and a cable route.
- **Satellite** (VSAT or LEO constellation services) is the fallback where cellular fails. `needs-verification`: current licensing and availability of LEO satellite internet in Namibia.

> **Design implication:** provide a **communications position** — a mast or a high point on the building with a clear cable route and surge protection — as a designed element. Retrofitting it means drilling through a finished roof.

---

## 4. Roads and access

Cross-reference **domain 17 (paving and roads)** and **domain 11 (logistics)**. In summary:

- **Okongo is on a tarred road**, roughly **120 km east of Eenhana**, continuing toward **Nkurenkuru** in Kavango West. The **Roads Authority** manages the national network.
- Ohangwena's main settlements "straddle the good paved road from the Angolan border to Ondangwa", where it meets the **Oshakati–Tsumeb trunk road**.
- **Beyond the tar, the network is unsealed sand track** — passable to 4×4 and to light commercial vehicles in the dry season, difficult after rain, and effectively the binding constraint on delivery of anything heavy to a rural homestead.
- **The eastern part of Ohangwena has good grazing but "shortage of water and poor communications"** — the region's own description of why it is thinly settled.
- **Okongo has a landing strip for small aircraft** — relevant for medical evacuation and for very high-value, very light freight, not for materials.
- **Legal load limits** (see domain 11): permissible gross vehicle mass **56 000 kg**, tandem-axle-unit limit **24 000 kg**, enforced at Roads Authority weighbridges.

**Practical rule:** plan heavy deliveries to arrive **May–November**. In February–April, assume the last few kilometres may be impassable.

---

## 5. Fuel

- Namibia **imports essentially all refined fuel**; **petroleum oils were 14.9 % of 2025 imports** by value, the single largest import category.
- Fuel prices are **regulated nationally** by the responsible ministry and adjusted periodically, with a **zone differential** that makes fuel progressively more expensive further from Walvis Bay. **Northern Namibia pays a premium.**
- **Diesel** is the working fuel for generators, pumps, compressors and plant. **Petrol** for light vehicles.
- **Okongo has fuel retail** (it has supermarkets and banking; a filling station is present), but **do not assume unlimited availability or out-of-hours service**. For a construction site, carry bulk storage — a bunded diesel bowser — and manage it, because a plant fleet that runs dry 120 km from the nearest reliable supply loses a day per incident.
- **LPG** is the practical cooking and water-heating fuel where there is no reliable grid; it is distributed through the northern towns. `needs-verification`: LPG availability and pricing at Okongo.
- **Firewood and charcoal** remain the primary domestic cooking fuel for most rural households in Ohangwena — with implications for kitchen design (external or well-ventilated), for fire risk, and for the local woodland resource.

---

## 6. Waste

- **Solid waste** in proclaimed villages is a local authority function; **Okongo village council** is responsible within the village. Facilities are typically a fenced tip rather than an engineered landfill.
- **Outside the village there is no collection.** Rural waste management is burning, burying and reuse.
- **Construction waste** must therefore be planned for on site: minimise packaging, return pallets and reels where possible, segregate scrap metal (which has value and will be collected informally), and do not assume anything will be taken away.
- **Hazardous waste** — waste oil, solvents, paint, batteries — has no rural disposal route. **Plan to backload it** to Ondangwa or Windhoek.
- **Sanitation** is the largest waste issue: national improved sanitation coverage was **54 % urban and only 17 % rural (2015)**, and Ohangwena is 85.5 % rural. On-site sanitation design is a primary, not secondary, part of a rural building project.

---

## 7. Off-grid solar as a mainstream option

**This is the most important service-design conclusion for Okongo.**

Okongo receives **2 275 kWh/m²/yr of global horizontal irradiance (6.23 kWh/m²/day)**, with a **June minimum of 5.23 kWh/m²/day** — only **16 % below the annual mean**. That seasonal flatness is unusual and extremely favourable: a system sized for the June minimum is barely oversized for the rest of the year, unlike in temperate latitudes where winter sizing doubles the array.

**Why off-grid is often the rational primary choice here, not a fallback:**
1. **The grid connection cost for a dispersed rural site frequently exceeds the cost of a PV system that meets the same demand.** Get both quotations and compare honestly.
2. **Grid reliability is imperfect**, so a grid-connected site needs battery backup anyway — at which point the marginal cost of a larger array is small.
3. **Solar pumping** for a borehole is mature, cheap, and matches demand to supply (pump when the sun shines, store water not electricity). A raised tank is a cheaper battery than a battery.
4. **Solar water heating** is trivially viable and displaces the largest single electrical load in most households.
5. **The precedent exists in the region:** the CuveWaters project installed **solar-powered brackish-water desalination plants** in Omusati in 2010.

**Design guidance:**
- **Size for the June minimum** (5.23 kWh/m²/day).
- **Mount panels facing north** at a tilt near the latitude (**~17–20°**) for best annual yield; a steeper tilt favours winter but at this latitude the difference is small, and a **minimum ~10–15° tilt is needed anyway to let rain wash dust off**.
- **Dust is the dominant maintenance issue.** Fine easterly-blown sand will cut output measurably. Design for safe access to clean the array — an accessible, walkable mounting position, not a fragile roof pitch.
- **Heat derates panels.** With October air temperatures of 34–37 °C, module temperatures will be very high; allow for the temperature coefficient and provide **ventilated mounting with a clear air gap behind the modules**.
- **Batteries hate heat.** Site battery storage in a **shaded, ventilated, insulated** enclosure — not in an unventilated steel box in the sun, which is the most common installation error in the region.
- **Hail and UV**: specify hail-rated modules and UV-stable cabling and cable management.
- **Lightning**: bond and surge-protect the array. See `02_climate-and-weather.md`.

## Sources

- [NamPower — Wikipedia (Ruacana 347 MW, Van Eck 120 MW, Anixas 22.5 MW, SWAWEK 1964, ECB regulation)](https://en.wikipedia.org/wiki/NamPower)
- [NamPower corporate site (563.50 MW installed capacity; 12 043 km transmission; Ruacana river flow; role of REDs)](https://www.nampower.com.na/Page.aspx?p=181)
- [NORED — Northern Regional Electricity Distributor (services, contact, Ohangwena and Oshikoto outage notices)](https://www.nored.com.na/)
- [Water supply and sanitation in Namibia — Wikipedia (NamWater, Water Resources Management Act 2013, sanitation coverage, Cunene supply, CuveWaters)](https://en.wikipedia.org/wiki/Water_supply_and_sanitation_in_Namibia)
- [BBC News — Ohangwena II aquifer (2012)](https://www.bbc.com/news/science-environment-18875385)
- [Telecom Namibia — Wikipedia](https://en.wikipedia.org/wiki/Telecom_Namibia)
- [MTC Namibia — Wikipedia](https://en.wikipedia.org/wiki/MTC_Namibia)
- [Namibia 2023 Census Dissemination Portal (3 022 401 people, 756 339 households)](https://census.nsa.org.na/)
- [Ohangwena Region — Wikipedia (road network description)](https://en.wikipedia.org/wiki/Ohangwena_Region)
- [Okongo — Wikipedia (village services, hospital, airstrip)](https://en.wikipedia.org/wiki/Okongo)
- [Economy of Namibia — Wikipedia (petroleum oils 14.9 % of imports)](https://en.wikipedia.org/wiki/Economy_of_Namibia)
- [PVGIS v5.2 monthly irradiation at Okongo (JRC)](https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json)

## Open questions

- `needs-verification`: **NORED's exact regional footprint** (which of Ohangwena, Omusati, Oshana, Oshikoto, Kavango East/West and Zambezi it serves), its **current ECB-approved tariff schedule**, and **new-connection charges**.
- `needs-verification`: **the share of Ohangwena households with grid electricity in the 2023 census.** The 20.7 % figure carried in domain 11 is from earlier reporting.
- `needs-verification`: whether NamPower's 563.50 MW figure includes recent solar and wind IPP additions; Namibia has commissioned several utility-scale PV plants since 2018 that are not reflected in the three-station list.
- `needs-verification`: Namibia's electricity import share and the current import agreements.
- `needs-verification`: MTC/TN Mobile coverage maps for Okongo Constituency and actual signal quality off the tarred road.
- `needs-verification`: availability and licensing of LEO satellite internet in Namibia.
- `needs-verification`: current Namibian regulated fuel prices and the northern zone differential; LPG availability at Okongo.
- `needs-verification`: Okongo village council waste and sanitation arrangements, and the local authority's minimum borehole/soakaway separation distance.
- `needs-verification`: the water source and reticulation arrangement actually serving Okongo village (Kunene pipeline extension, local borehole field, or both).
