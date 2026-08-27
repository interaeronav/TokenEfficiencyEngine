---
id: namibia.climate_responsive_design
title: Climate-responsive design for hot semi-arid northern Namibia
domain: 18_namibia_context
tags: [namibia, ohangwena, okongo, passive-design, orientation, shading, sun-angles, thermal-mass, ventilation, stack-effect, courtyard, veranda, glazing, insulation, albedo, rainwater, checklist]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "PVGIS v5.2 TMY at 17.567°S 17.217°E", url: "https://re.jrc.ec.europa.eu/api/v5_2/tmy?lat=-17.567&lon=17.217&outputformat=json", publisher: "European Commission Joint Research Centre", accessed: 2026-08-25}
  - {title: "PVGIS v5.2 monthly horizontal irradiation, 2016–2020", url: "https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json", publisher: "European Commission Joint Research Centre", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Temperature (diurnal range)", url: "https://atlasofnamibia.online/chapter-3/temperature", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Wind (frequency of calms)", url: "https://atlasofnamibia.online/chapter-3/wind", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Atlas of Namibia — Humidity", url: "https://atlasofnamibia.online/chapter-3/humidity", publisher: "Atlas of Namibia", accessed: 2026-08-25}
  - {title: "Klimatafel von Eenhana (Deutscher Wetterdienst) via Wikipedia", url: "https://en.wikipedia.org/wiki/Eenhana", publisher: "Deutscher Wetterdienst", accessed: 2026-08-25}
  - {title: "Ondangwa climate chart", url: "https://en.wikipedia.org/wiki/Ondangwa", publisher: "Wikipedia", accessed: 2026-08-25}
related: [namibia.climate, namibia.architecture, namibia.geology_soils, namibia.infrastructure, arch.passive_design]
unit_system: SI
applies_to: [okongo, ohangwena, northern-namibia, latitude-17-6-south]
---

# Climate-responsive design for hot semi-arid northern Namibia

**Summary.** At **17.57°S**, with **2 263 kWh/m²/yr on the horizontal**, a **590 mm** wet season compressed into four months, a **dry-season diurnal swing of 18–20 K**, midday humidity below **20 %** for three months of the year, and **calm air more than half the time**, the design problem has a specific and quantifiable shape. Ranked by leverage: **(1) shade the roof and ventilate it; (2) shade the east and west; (3) provide stack ventilation that works without wind; (4) use mass with night purging in the dry season and switch to air movement in the wet; (5) keep glazing small, shaded and oriented north.** This file gives the sun angles, the per-orientation solar loads, the shading geometry and a checklist of quantified rules.

## Key facts — the design climate at a glance

| Quantity | Value |
|---|---|
| Latitude / longitude | **17.57°S, 17.22°E** |
| Elevation | **≈1 151 m** |
| Köppen | **BSh** — hot semi-arid |
| Annual rainfall (Eenhana) | **590 mm**; 63 % in Jan–Mar; <25 mm May–Oct |
| Mean annual temperature (Eenhana) | **22.7 °C** |
| Hottest month | **October** (Ondangwa mean max **34 °C**; record **43.2 °C**) |
| Coolest month | **July** (Ondangwa mean min **8 °C**) |
| Dry-season diurnal swing | **18–20 K** (Ondangwa, Jul–Sep) |
| Wet-season diurnal swing | **~12 K** (Jan–Mar) |
| RH range | **~15–20 % (Sep/Oct, 14h00)** to **~80 % (Feb, 08h00)** |
| Calms at Ondangwa | **53–68 % of observations** |
| Prevailing wind | **Easterly (E/ENE)**, light — 2–3.5 m/s at 10 m |
| Global horizontal irradiance | **2 263–2 275 kWh/m²/yr** |
| Noon sun altitude | **49.0° (21 Jun, N)** → **84.1° (21 Dec, S)**; overhead **≈12 Nov and ≈31 Jan** |
| Sunrise azimuth range | **65.3° (Jun)** to **114.7° (Dec)** from north |
| Day length range | **10.95 h (Jun)** to **13.05 h (Dec)** — only ~2 h |

---

## 1. Solar geometry at 17.57°S — the numbers to design with

| Date | Declination | Noon altitude | Noon sun bearing | Sunrise azimuth | Day length |
|---|---|---|---|---|---|
| 21 Jun | +23.4° | **49.0°** | **North** | 65.3° (ENE) | 10.95 h |
| 15 Aug | +14.1° | 58.4° | North | 75.2° | 11.39 h |
| 21 Sep | +0.7° | 71.7° | North | 89.2° (E) | 11.97 h |
| 15 Oct | −8.5° | 80.9° | North | 98.9° | 12.36 h |
| **12 Nov** | −17.6° | **90.0°** | **Zenith** | — | ~12.8 h |
| 21 Dec | −23.4° | **84.1°** | **South** | 114.7° (ESE) | 13.05 h |
| **31 Jan** | −17.6° | **90.0°** | **Zenith** | — | ~12.9 h |
| 15 Feb | −12.7° | 85.1° | North | 103.3° | 12.54 h |
| 21 Mar | +0.2° | 72.2° | North | 89.8° (E) | 11.99 h |
| 15 Apr | +9.8° | 62.7° | North | 79.8° | 11.58 h |

**Three facts that govern the design:**
1. **The sun is nearly overhead for a third of the year.** Between mid-October and mid-February the noon altitude never falls below ~81°. A horizontal roof takes the full load; a horizontal overhang shades a wall almost completely at noon.
2. **The noon sun crosses to the south of the zenith between ≈12 November and ≈31 January.** South-facing walls are not "safe" in the way they are at higher southern latitudes.
3. **The sun rises and sets well south of east/west in summer** (azimuth 114.7° at the December solstice, i.e. 24.7° south of east). Low, intense sun strikes the **east, west and south-east/south-west** faces morning and evening.

---

## 2. Solar load by orientation — computed, not assumed

Annual and monthly irradiation on vertical surfaces at Okongo, computed from the **PVGIS TMY hourly record** (isotropic sky, ground albedo 0.30 — pale sand may be higher):

| Month | Horizontal | North wall | South wall | East wall | West wall |
|---|---|---|---|---|---|
| Jan | 212.0 | 71.5 | **97.7** | **127.6** | 110.3 |
| Feb | 170.7 | 65.6 | 68.4 | 103.1 | 93.7 |
| Mar | 160.7 | 84.0 | 58.1 | 92.0 | 90.9 |
| Apr | 178.9 | 129.8 | 50.0 | 109.0 | 103.8 |
| May | 169.9 | 164.0 | 43.3 | 106.9 | 99.3 |
| Jun | 159.0 | **178.5** | 38.2 | 98.9 | 97.3 |
| Jul | 163.0 | 170.3 | 40.6 | 100.6 | 97.5 |
| Aug | 189.5 | 151.2 | 50.8 | 111.6 | 110.5 |
| Sep | 205.5 | 111.8 | 59.7 | 116.2 | 117.9 |
| Oct | **228.4** | 83.7 | 71.6 | **133.1** | 120.8 |
| Nov | 198.8 | 66.9 | 85.5 | 117.0 | 106.1 |
| Dec | 226.8 | 68.5 | **106.1** | **135.5** | 113.6 |
| **Year** | **2 263** | **1 346** | **770** | **1 351** | **1 261** |

*(units: kWh/m²/month and kWh/m²/year)*

**Read this table and the design follows:**

- **The roof is the problem.** At **2 263 kWh/m²/yr** it receives **1.7×** the annual load of the north wall and **2.9×** that of the south wall — and in the hot months (October 228, December 227) it is far ahead of every wall. **Roof design outranks everything.**
- **East and west are the worst walls, not north.** East takes **1 351 kWh/m²/yr** and west **1 261**, against north's **1 346** — but the *timing* differs completely. The north wall's load peaks in **June (178)**, when heat is welcome, and falls to **67–72 in November–January**, when it is not. The east and west walls peak in **October (133/121) and December (136/114)** — exactly when overheating occurs.
- **The north wall is self-regulating and easy to shade.** Its winter peak coincides with the need for heat, and a modest overhang excludes the high summer sun.
- **The south wall is not negligible in summer.** In December it takes **106 kWh/m²** — **55 % more than the north wall in the same month**. Small south openings still need shading.

### Ranking by design priority
1. **Roof** — 2 263 kWh/m²/yr, always the dominant load.
2. **West wall** — 114 kWh/m² in December, arriving in the late afternoon when the building is already hot and when peak indoor temperature is set. Worst timing of any surface.
3. **East wall** — 136 kWh/m² in December, arriving in the morning; slightly more forgiving because the building starts cool.
4. **South wall** — significant only Nov–Feb.
5. **North wall** — the easy one, and the useful one.

---

## 3. Orientation and plan

**Orient the long axis east–west.** This maximises north and south façade area (the controllable ones) and minimises east and west façade area (the uncontrollable ones). Aim for a **plan aspect ratio of about 1.5:1 to 2.5:1** on the east–west axis.

**Keep the plan shallow.** A **maximum depth of about 6–7 m between opposite external walls** allows cross-ventilation to work and daylight to reach the middle. Deeper plans need a courtyard or a ventilated spine.

**Do not build a compact cube.** Compactness is a cold-climate strategy. In a hot climate with a large diurnal swing and abundant land, a **dispersed, thin, shaded plan** — the Owambo homestead logic — outperforms a compact one, because it can lose heat at night and be shaded by day.

**Design the outdoor rooms first.** In this climate, the veranda, the courtyard and the shaded yard are the primary living spaces for most of the year. The enclosed rooms are for sleeping, storage and the four wet months.

**Zone by orientation:**

| Orientation | Best use |
|---|---|
| **North** | Living spaces, main veranda, principal glazing |
| **South** | Bedrooms (coolest façade for 8 months), service rooms, small openings |
| **East** | Kitchen (hot in the morning, cooling by afternoon), utility, garages |
| **West** | **Buffer zones only** — stores, bathrooms, garages, thick walls, no habitable glazing if avoidable |

---

## 4. Roof — the highest-leverage decision

The default Namibian northern roof — a single-skin corrugated iron sheet, no ceiling, no insulation, dark or unpainted — is a solar collector directly above the occupants. Under 6.9 kWh/m²/day in October it will drive an unshaded interior well above outdoor air temperature.

**The five-part roof specification:**

1. **High albedo.** Specify a light-coloured finish with a **solar absorptance ≤ 0.4, preferably ≤ 0.3** (white, off-white, light grey, pale galvanised). This is the cheapest single intervention available. Note that dust reduces reflectance — assume real-world performance below the specified value and design the roof to be washable by rain (adequate pitch).
2. **A ventilated cavity.** A **continuous air gap between the outer sheet and the insulated ceiling plane**, open at the eaves and exhausting at the ridge. This is what removes the heat that the reflective surface did not reject. Provide **continuous eaves ventilation (a minimum free area of roughly 1/300 of the ceiling area is a common rule of thumb — `needs-verification` against SANS)** and a **ridge vent or roof ventilators**.
3. **Insulation at the ceiling plane.** Target a **roof/ceiling assembly R-value of at least 2.5–3.0 m²K/W**. `needs-verification`: check the required minimum against **SANS 10400-XA** for the applicable climatic zone — see domain 03.
4. **A radiant barrier.** A **low-emissivity foil sarking facing the ventilated cavity** is disproportionately effective against radiant gain from a hot sheet, and it doubles as the **anti-condensation membrane** needed for clear wet-season nights when the sheet radiates below dew point and drips.
5. **Overhang.** **Minimum 900 mm eaves overhang all round; 1 200–1 500 mm on north, east and west** where a veranda does not already provide it. Overhangs shade walls, keep rain off, protect the wall–ground junction, and are cheap.

**Hold the roof down.** Convective downdraughts are the real wind hazard. Continuous hold-down straps from roof to foundation, close fixing centres at eaves, verge and ridge, and through-fixings with proper washers.

---

## 5. Thermal mass versus lightweight — and when to switch

**The dry season (April–October): mass wins.** With an **18–20 K diurnal swing**, heavyweight construction can absorb the day's heat, hold indoor temperature near the daily mean, and discharge it overnight through purge ventilation. This is the classic hot-arid strategy and it works here for seven months.

**The wet season (December–March): mass loses.** The swing collapses to **~12 K**, night temperatures stay near 19–21 °C, and humidity reaches ~80 % in the morning. Mass now stays warm at night, and the only comfort mechanism left is **air movement over skin**.

**The design conclusion is a hybrid, not a compromise:**
- **Mass on the walls and floor** — a masonry or block envelope with a concrete floor slab. Aim for **at least 100–150 mm of effective mass thickness** on internal surfaces. Mass must be **on the inside of insulation** and **must not be sun-exposed on the outside**, or it becomes a heat store working against you.
- **Lightweight, insulated, ventilated roof** — never a heavyweight roof, which would radiate downward all night.
- **Large operable openings and ceiling fans** so the building can switch to the air-movement mode in February.
- **A shaded, well-ventilated outdoor room** (veranda or courtyard) that is comfortable in the wet season when the interior is not.

**Ceiling fans are the highest comfort-per-rand item in the building.** Air movement of **0.5–1.0 m/s** shifts the perceived temperature down by roughly 2–3 K, at trivial energy cost, and works when nothing else does.

---

## 6. Shading geometry — quantified

### North façade (equator-facing) — easy
Let **H** = vertical distance from the underside of the shading device to the window sill.

| Design intent | Overhang projection **P** | Effect |
|---|---|---|
| Fully shaded at equinox noon (alt 72.2°) | **P = 0.32 H** | Full shade 21 Sep – 21 Mar at noon; **63 % of the window sunlit at winter noon** |
| Robust summer shading, some winter sun | **P = 0.35–0.45 H** | Recommended default |
| Full-time veranda | **P = 0.7–1.0 H** (typically **1.8–2.4 m** deep at 2.4–3.0 m eaves height) | Permanent shade; a usable outdoor room; some low winter sun reaches the back |

Off-noon summer sun on the north façade arrives at a *higher* profile angle than the noon altitude, so the same overhang shades **more**, not less. The north façade is genuinely solved by a horizontal device.

### East and west façades — hard
A horizontal overhang is nearly useless. At **08h00 in December** the sun is at roughly **25–30° altitude on an azimuth near due east**, so the profile angle on an east wall is also 25–30°, and full shading would require a projection of **1.7–2.1 × H** — a 3.6–4.4 m overhang for a 2.1 m opening. Not buildable.

**Use instead, in order of effectiveness:**
1. **Do not put habitable glazing on east and west.** This is the real answer.
2. **Vertical fins or a deep vertical-louvred screen**, angled to reject the sunrise/sunset azimuth band (65°–115° from north).
3. **Operable external shutters** — the Nama *pontok* principle: closed against the sun, open for air. Cheap, locally makeable, and effective.
4. **Deep verandas wrapping the corners**, which convert the problem into a shaded outdoor room.
5. **Deciduous or evergreen shade trees** at the correct distance — see §11.
6. **Blank or heavily massed walls** — a store, garage or thick-walled service zone as a thermal buffer.

### South façade
Small horizontal overhangs handle the near-vertical November–January noon sun easily (**P = 0.11 H** shades at 84° altitude), but the low ESE/WSW morning and evening sun in summer needs vertical devices or small, deeply recessed openings. **A 600–900 mm overhang plus modest opening sizes is sufficient.**

### General shading rules
- **Shading must be external.** Internal blinds stop glare, not heat. (See the hundred-year mistake with the Christuskirche windows in `05_namibian-architecture.md`.)
- **Shade the wall, not just the window.** Wall surface temperature drives conduction and re-radiation into the veranda.
- **Shade the ground.** Bare pale sand reflects strongly into the underside of verandas and onto low glazing. Plant, gravel, or shade it.

---

## 7. Ventilation — cross, stack and night purge

> ⚠️ **Design rule: the wind is calm 53–68 % of the time at Ondangwa. Never depend on cross-ventilation alone.**

**Cross ventilation** — still worth having, and the prevailing direction is **easterly (E/ENE, ~59 % of hours from the NE–ESE quadrant)**.
- Inlet on the **east**, outlet on the **west** or north-west.
- **Outlet area ≥ inlet area** (a larger outlet increases flow through the inlet).
- Keep the path short and unobstructed: **plan depth ≤ 6–7 m** for effective cross flow.
- Openable area target: **10–20 % of floor area** as *free* (not gross) opening.

**Stack ventilation** — the one that works when the wind does not.
- Provide a **height difference of at least 2–3 m** between low inlets and high outlets. More is better.
- Devices: **high-level clerestory openings, roof ventilators, a ventilated ridge, a solar chimney, or a double-height space**.
- A **solar chimney** — a dark, sun-exposed, insulated-from-the-interior vertical duct — is very effective at 2 263 kWh/m²/yr, and it costs almost nothing to build in blockwork.
- The **ventilated roof cavity** exhausting at the ridge is itself a stack device and should be detailed to draw from the rooms where possible.

**Night purge ventilation** — the mechanism that makes mass work.
- From **April to October**, open the building fully after sunset to flush the day's heat out of the mass, and close it at sunrise.
- This requires **secure, insect-screened, weather-protected night openings** — a security grille with an operable louvre or shutter behind it. If the occupants cannot leave openings open at night safely, the mass strategy fails. **Design the security, or the physics does not happen.**

---

## 8. Evaporative cooling

**Highly effective from August to November**, when midday relative humidity falls to **17–20 %**. Largely ineffective in February–March at ~80 % morning humidity.

Passive and low-cost measures:
- **A shaded water body or fountain in a courtyard**, upwind of the living space.
- **Planting and irrigated ground** — transpiration is evaporative cooling.
- **Wetted surfaces**: a damp floor or a wetted screen in the airflow path.
- **Direct evaporative coolers** ("desert coolers") are genuinely appropriate here for the hot dry months, and use a fraction of the energy of refrigerative air conditioning. They are counter-productive in February.
- **Water cost is the constraint.** Use harvested rainwater or greywater, never potable borehole water, for evaporative cooling.

---

## 9. Glazing

**The rules, in order:**
1. **Total glazing area: 10–20 % of floor area.** Above 20 %, cooling loads rise faster than daylight benefits in this climate.
2. **Orientation split:** put **60–80 % of the glazing on the north**, the remainder on the south. **East ≤ 5 % of floor area, west ≤ 3 %, both shaded.**
3. **Every piece of glass must be externally shaded**, including the north.
4. **Prefer many small, well-distributed, operable openings over one large fixed one.** Namibia's northern climate needs ventilation and daylight, not view-walls.
5. **Glass specification:** single glazing with good external shading outperforms unshaded double glazing in this climate and costs a fraction. Where high-performance glass is used, prefer a **low solar heat gain coefficient** for east and west and **higher visible transmittance with a lower SHGC** for north. `needs-verification`: available glazing products and specifications in the Namibian market — see domain 08 (glass and façades).
6. **Daylight without sun:** clerestories facing south, and light shelves on the north, deliver daylight deep into the plan without beam radiation.
7. **Glare from bare sand is severe.** Low-level glazing takes strong reflected light; shade the ground in front of it.

---

## 10. Insulation, colour and albedo

**Insulation priority order (highest return first):**
1. **Roof/ceiling** — target **R ≥ 2.5–3.0 m²K/W** for the assembly.
2. **West wall** — the late-afternoon load. Insulate, mass, or buffer it.
3. **East wall.**
4. **North and south walls** — lower priority; mass matters more than R-value here.
5. **Floor** — generally leave the slab uninsulated and in contact with the ground; the ground is a useful heat sink in this climate. Insulate the perimeter edge only if required for a specific reason.

> `needs-verification`: **the applicable minimum R-values.** Namibia has no independent thermal building regulation known to this domain and in practice **SANS 10400-XA / SANS 204** are referenced. Confirm the zone classification and the required values in domain 03.

**Colour and albedo:**
- **Roof: solar absorptance ≤ 0.4, ideally ≤ 0.3.** Light colours only.
- **Walls: light colours on east and west.** Absorptance ≤ 0.5.
- **Do not use dark colours on any sun-exposed surface.** The temptation to use dark "natural" or "earth" tones is an aesthetic import from cooler climates.
- **The ground is part of the envelope.** Bare pale sand has a high albedo and reflects load onto soffits and glazing; dark paving absorbs and re-radiates. **Shaded, planted or lightly-coloured shaded ground is the target.**

---

## 11. Landscape and shade trees

Trees are the cheapest, most effective and most locally appropriate shading device available in eastern Ohangwena — and this is a wooded region ("a place or forest for hunting"), so the resource exists.

- **Plant to shade the east and west façades**, where built shading fails. Position trees so that their canopy intercepts the **65°–115° sunrise/sunset azimuth band**.
- **Distance:** a tree at roughly **0.5–1.0 × its mature height** from the wall shades the wall through the critical low-sun hours without dropping litter into gutters or roots into foundations. Keep **large trees at least 3–5 m from foundations** on sandy soil, more for species with aggressive roots.
- **Shade the outdoor living space**, not just the building. A large shade tree over the yard is the traditional and correct primary living-space cooling device.
- **Use indigenous, drought-tolerant species.** Marula (*Sclerocarya birrea*), mopane (*Colophospermum mopane*), *Faidherbia albida*, and the fruit trees already grown around homesteads. `needs-verification`: a recommended species list for eastern Ohangwena.
- **Do not plant lawn.** It is an evaporative liability in a 590 mm/yr climate.
- **Ground cover reduces reflected radiation and dust.** Even low scrub or a gravel mulch is a large improvement on bare sand.
- **Windbreak:** a planted or palisade screen on the **east** intercepts the prevailing dust-laden wind, exactly as the traditional homestead palisade does.

---

## 12. Rainwater harvesting

At **590 mm/yr**, harvesting is genuinely worthwhile — and on a saline-groundwater site it is a **quality** strategy as well as a quantity one.

**Sizing arithmetic:**
- Gross yield = roof plan area × annual rainfall. **100 m² × 0.590 m = 59 m³/yr.**
- Apply a **runoff coefficient of ~0.8** for a metal roof after first-flush and evaporation losses: **≈47 m³/yr**.
- **Size the tank for the dry season, not the annual total.** May–October delivers **<25 mm**. To carry a household through six dry months at, say, 60 L/day, you need **~11 m³** of storage — a realistic and affordable target with two or three standard tanks.
- **February alone yields ~10.6 m³ from a 100 m² roof** at 133 mm — so tank overflow management and a designed overflow path away from the foundations is essential.

**Detailing:**
- **Metal roof, not thatch or unsealed fibre-cement**, for potable harvesting.
- **First-flush diverter** — essential given six months of dust accumulation before the first rain.
- **Screened, sealed, opaque tanks** to exclude mosquitoes, light and algae.
- **Shade the tanks** — UV degrades plastic tanks fast at this irradiance, and warm water grows organisms.
- **Gutters sized for burst intensity, not for the monthly average.** Convective downpours are the design case.
- **Overflow piped clear of the building** onto a hard or planted surface, never onto bare sand at the foundation, which will erode.
- **Greywater** to shade trees and planting closes the loop.

---

## 13. The checklist — quantified design rules for Okongo

| # | Rule | Target |
|---|---|---|
| 1 | Long axis orientation | **East–west**, plan ratio **1.5:1 to 2.5:1** |
| 2 | Plan depth | **≤ 6–7 m** between opposite external walls |
| 3 | Roof solar absorptance | **≤ 0.4**, preferably **≤ 0.3** |
| 4 | Roof/ceiling assembly R-value | **≥ 2.5–3.0 m²K/W** (verify against SANS 10400-XA) |
| 5 | Ventilated roof cavity | **Continuous**, eaves inlet + ridge/ventilator outlet |
| 6 | Radiant barrier / anti-condensation membrane | **Low-e foil facing the ventilated cavity** |
| 7 | Eaves overhang | **≥ 900 mm** all round; **1 200–1 500 mm** N/E/W |
| 8 | North overhang | **P = 0.35–0.45 × H** (sill to device) |
| 9 | North veranda depth | **1.8–2.4 m** at 2.4–3.0 m soffit height |
| 10 | South overhang | **600–900 mm** plus modest opening sizes |
| 11 | East/west shading | **Vertical fins, shutters, verandas or trees** — not overhangs |
| 12 | Total glazing | **10–20 % of floor area** |
| 13 | Glazing split | **N 60–80 %**, **E ≤ 5 % of floor area**, **W ≤ 3 %** |
| 14 | All glazing | **Externally shaded** |
| 15 | Free openable area | **10–20 % of floor area** |
| 16 | Ventilation outlet vs inlet | **Outlet ≥ inlet** |
| 17 | Stack height | **≥ 2–3 m** between low inlet and high outlet |
| 18 | Night purge | **Secure, screened, operable night openings** on every habitable room |
| 19 | Ceiling fans | **Every habitable room** — target 0.5–1.0 m/s air speed |
| 20 | Internal thermal mass | **≥ 100–150 mm** effective thickness, inboard of insulation, never sun-exposed externally |
| 21 | Roof form | **Lightweight**, never heavyweight |
| 22 | Wall colour, E and W | Solar absorptance **≤ 0.5**, light |
| 23 | Floor level above ground | **≥ 300–450 mm** in the Cuvelai |
| 24 | Apron / hardstanding | **≥ 1.0 m wide**, falling away at ≥ 1:50 |
| 25 | Rainwater storage | **≈11 m³** for a household on a 100 m² roof (six dry months) |
| 26 | First-flush diverter | **Mandatory** |
| 27 | Gutters | Sized for **burst intensity**; overflow piped clear of foundations |
| 28 | Shade trees, E and W | Canopy intercepting the **65°–115°** azimuth band; **3–5 m minimum from foundations** |
| 29 | Ground surface | **Shaded, planted or light-coloured** — not bare dark paving, not unshaded bare sand |
| 30 | PV array | Tilt **~17–20°** (minimum 10–15° for rain washing), north-facing, ventilated, accessible for cleaning |
| 31 | Batteries | **Shaded, ventilated, insulated enclosure** — never an unventilated box in the sun |
| 32 | Lightning protection | **Extended earth electrode arrangement** (dry sand is a poor earth) + surge protection on power and comms |
| 33 | Roof hold-down | **Continuous straps to foundation**; close fixing centres at eaves, verge and ridge |
| 34 | Construction season | Envelope weathertight by **late November**; concrete and earthworks **May–September** |
| 35 | Concrete curing | **≥ 7 days** wet or membrane cure; shade fresh work; no afternoon placement in October |
| 36 | Termite protection | **Physical barrier**; no ground-contact timber |
| 37 | Dust detailing | Hinged not sliding; brush seals; IP-rated electrics; intakes **high and to the west** |
| 38 | UV specification | UV-stable plastics, sealants and cable management; shade PVC rainwater goods |
| 39 | Staging | **Every construction stage habitable and weathertight on its own**; roof built early, walls infilled later |
| 40 | Ceilings and insulation | Part of the **enclosure stage**, never deferred to "finishing" |

---

## 14. The one-paragraph version

Put the long axis east–west on the highest ground available. Raise the floor. Build a light-coloured, ventilated, insulated, big-overhanging roof over more area than you enclose, and hold it down properly. Make the north façade the front, with a 2 m veranda; make the west a wall of stores and bathrooms; put nothing you care about on the east or west without shutters or trees. Keep the plan one room deep. Give every room a high outlet as well as a low inlet, and a ceiling fan. Use block walls and a concrete floor for mass, and let the occupants purge the heat out of them every night through secure louvres. Keep the glass small, on the north, and shaded from outside. Harvest the roof water into shaded tanks with a first-flush diverter, and pipe the overflow well away from the sand. Plant trees to the east and west and over the yard. Build in the dry season, cure the concrete properly, and design it so the family can finish it over five years without ever having an unusable building.

## Sources

- [PVGIS v5.2 TMY at 17.567°S, 17.217°E (JRC)](https://re.jrc.ec.europa.eu/api/v5_2/tmy?lat=-17.567&lon=17.217&outputformat=json) — hourly G(h), Gb(n), Gd(h), T2m, RH, WS10m, WD10m used to compute the per-orientation vertical-surface irradiation table in §2
- [PVGIS v5.2 monthly horizontal irradiation, 2016–2020 (JRC)](https://re.jrc.ec.europa.eu/api/v5_2/MRcalc?lat=-17.567&lon=17.217&horirrad=1&startyear=2016&endyear=2020&outputformat=json)
- [Atlas of Namibia — Temperature (Ondangwa diurnal range 18–20 K dry / ~12 K wet)](https://atlasofnamibia.online/chapter-3/temperature)
- [Atlas of Namibia — Wind (frequency of calms at Ondangwa 53–68 %)](https://atlasofnamibia.online/chapter-3/wind)
- [Atlas of Namibia — Humidity (<20 % least humid months; ~80 % most humid, northern Namibia)](https://atlasofnamibia.online/chapter-3/humidity)
- [Atlas of Namibia — Evaporation and aridity](https://atlasofnamibia.online/chapter-3/evaporation-and-aridity)
- [Eenhana — Wikipedia (Deutscher Wetterdienst Klimatafel: 590 mm, 22.7 °C)](https://en.wikipedia.org/wiki/Eenhana)
- [Ondangwa — Wikipedia (monthly max/min, 43.2 °C record, 1 080 m, BSh)](https://en.wikipedia.org/wiki/Ondangwa)

## Open questions

- `needs-verification`: **required minimum R-values and the applicable climatic zone** under SANS 10400-XA / SANS 204 as applied in Namibia, and whether any Namibian national building regulation supersedes them. See domain 03.
- `needs-verification`: **rainfall intensity–duration–frequency data** for northern Namibia, needed to size gutters and downpipes numerically rather than by rule of thumb.
- `needs-verification`: **design wind speed** for northern Namibia for roof uplift calculation.
- `needs-verification`: recommended **indigenous shade tree species** for eastern Ohangwena and their mature dimensions and root behaviour.
- `needs-verification`: **glazing products and specifications available in the Namibian market** — see domain 08.
- `needs-verification`: eaves ventilation free-area ratios required or recommended by the applicable standard.
- The §2 vertical-surface irradiation table is computed with an **isotropic sky model and a ground albedo of 0.30**. Pale bare Kalahari sand may have an albedo of 0.35–0.45, which would raise all vertical-surface figures; the *relative ranking between orientations* is robust, the absolute values are indicative.
- All Okongo figures derive from reanalysis or from the nearest stations (Eenhana ~120 km, Ondangwa ~180 km). There is no station record at Okongo.
