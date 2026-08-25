---
id: arch.building_science
title: Building science — thermal, moisture, ventilation, light, sound, sun
domain: architecture
tags: [thermal, u-value, r-value, thermal-mass, condensation, ventilation, daylighting, acoustics, solar-geometry, shading, windhoek, ohangwena, hot-dry, sans-10400-xa]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "SANS 10400-XA:2021 — Energy usage in buildings", url: "https://www.uj.ac.za/wp-content/uploads/2023/11/sans-10400-xa-the-application-of-the-national-building-regulations-environmental-sustainability-energy-usage-in-buildings-2021.pdf", publisher: "SABS (copy hosted by University of Johannesburg)", accessed: 2026-08-25}
  - {title: "BR 443 Conventions for U-value calculations", url: "https://www.cibse.org/media/wzrjrf3l/conventions-for-u-value-calculations.pdf", publisher: "BRE / CIBSE", accessed: 2026-08-25}
  - {title: "ISO 6946:2007 — Thermal resistance and thermal transmittance", url: "https://cdn.standards.iteh.ai/samples/40968/eef030b005bd4146b90cddaf78c64f06/ISO-6946-2007.pdf", publisher: "ISO", accessed: 2026-08-25}
  - {title: "Windhoek — climate data", url: "https://en.wikipedia.org/wiki/Windhoek", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Eenhana — climate data", url: "https://en.wikipedia.org/wiki/Eenhana", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Daylight design rules of thumb", url: "https://www.irbnet.de/daten/iconda/CIB_DC23487.pdf", publisher: "CIB / IRBnet", accessed: 2026-08-25}
  - {title: "Acoustic design requirements by space type", url: "https://datadrivenaec.com/insights/acoustic-design-requirements", publisher: "DataDrivenAEC", accessed: 2026-08-25}
related: [arch.design_fundamentals, arch.structures]
unit_system: metric
---

# Building science — thermal, moisture, ventilation, light, sound, sun

**Summary.** In the Southern African interior, comfort is won or lost by orientation, shading, mass and ventilation long before any machine is installed. This file gives the calculation methods (U-value, R-value, condensation risk, ventilation rate, daylight factor, reverberation), the statutory thermal targets under **[ZA]** SANS 10400-XA:2021, and worked solar-geometry and shading examples for **Windhoek (22,56° S, ~1 700 m)** and **Ohangwena / Eenhana (17,48° S)**. Both sites lie inside the tropics, so the sun passes *north of zenith* for most of the year and *south of zenith* around midsummer — a fact that changes shading design.

## 1. Thermal fundamentals

**Definitions.**
- **λ (thermal conductivity)**, W/m·K — property of a material.
- **R (thermal resistance)**, m²·K/W — of a layer: `R = thickness (m) / λ`.
- **R_total** = R_si + ΣR_layers + R_cavity + R_se.
- **U (thermal transmittance)**, W/m²·K = `1 / R_total`. Lower U = better.

**Standard surface resistances (BS EN ISO 6946):**

| Heat flow | R_si (m²·K/W) | R_se (m²·K/W) |
|---|---|---|
| Horizontal (walls, windows) | 0,13 | 0,04 |
| Upward (roofs) | 0,10 | 0,04 |
| Downward (floors) | 0,17 | 0,04 |
| Unventilated masonry cavity | R = **0,18** | — |

**Design thermal conductivities (W/m·K):**

| Material | λ |
|---|---|
| Brick, outer leaf | 0,77 |
| Brick, inner leaf | 0,56 |
| Mortar, outer / inner | 0,94 / 0,88 |
| Reinforced concrete (1% steel) | 2,30 |
| Limestone (2 000 kg/m³) | 1,40 |
| Sandstone / granite (2 600 kg/m³) | 2,30 |
| Softwood, joists | 0,13 |
| Hardwood | 0,18 |
| OSB / plywood | 0,13 |
| Gypsum plasterboard | 0,21 |
| Mineral wool | ≈ 0,040 |
| EPS | ≈ 0,040 |
| PIR | ≈ 0,025 |

**Worked example — 280 mm cavity brick wall, plastered both sides:**

| Layer | Thickness | λ | R |
|---|---|---|---|
| R_si | — | — | 0,130 |
| Plaster | 0,015 m | 0,50 | 0,030 |
| Brick inner leaf | 0,106 m | 0,56 | 0,189 |
| Unventilated cavity | 0,050 m | — | 0,180 |
| Brick outer leaf | 0,106 m | 0,77 | 0,138 |
| Plaster | 0,015 m | 0,50 | 0,030 |
| R_se | — | — | 0,040 |
| **R_total** | | | **0,737** |

U = 1/0,737 = **1,36 W/m²·K**. Adding 50 mm PIR (R = 0,05/0,025 = 2,00) in the cavity gives R_total = 2,737 → **U = 0,37 W/m²·K**.

### [ZA] Statutory targets — SANS 10400-XA:2021
The 2021 edition replaced the six climatic zones with **seven Energy Zones plus Zone 5H** (high-humidity coastal). Towns are listed alphabetically by zone in Annex C.

| Element | Requirement | Clause/Table |
|---|---|---|
| Roof assembly, minimum total R | **3,7 m²·K/W** (Zones 1, 2, 4, 6, 7; and Zones 3, 5 upward heat flow); **2,7** for Zones 3, 5 downward and for Zone 5H | Table 8 |
| External wall, surface density ≥ 270 kg/m² | R ≥ **0,6** (Zones 1, 2, 6, 7 — i.e. 50 mm cavity wall); R ≥ **0,4** (Zones 3, 4, 5, 5H — collar-jointed) | Table 6 |
| External wall, surface density < 270 kg/m² | R ≥ **2,2** or CR ≥ 100 h (Zones 1, 2, 6, 7); R ≥ **1,9** or CR ≥ 80 h (Zones 3, 4, 5, 5H) | Table 7 |
| Fenestration | Area-weighted U-value and SHGC by fenestration percentage and orientation; calculation triggered above **20%** of storey floor area | Table 4 |
| Hot water | ≥ **50%** (volume fraction) of the annual average hot-water heating requirement by means other than electrical resistance heating | Reg. XA2 |
| Hot water storage | 6 L/person (sedentary) to 75 L/person (institutional residential); H4 dwellings 50 L/person per 24 h | Table 10 |

> ⚠️ **[NA]** Namibia has no confirmed national equivalent of SANS 10400-XA. SANS 10400-XA is the nearest published benchmark and is widely used by Namibian consultants, but it is **not law in Namibia**. Check with the relevant local authority.

### Thermal mass
Mass does not reduce heat *transfer*; it delays and damps it. Two metrics:
- **Time lag (φ)** — hours between the outside peak and the inside peak.
- **Decrement factor (f)** — the fraction of the outside swing that reaches the inside.

| Construction | Approx. time lag | Decrement factor |
|---|---|---|
| 100 mm brick | 2,5–3 h | 0,7 |
| 230 mm brick | 6–7 h | 0,4 |
| 300 mm rammed earth / adobe | 8–10 h | 0,3 |
| 450 mm stone/earth | 11–13 h | 0,1–0,2 |
| Lightweight steel/timber, insulated | < 1 h | ~0,9 |

Mass works **only when the diurnal swing is large and the night is cool enough to purge the stored heat**. Both design sites qualify — but Ohangwena's swing is smaller and its humid January–March period reduces night-purge effectiveness, so mass alone is less reliable there than in Windhoek.

## 2. Hot-dry climate strategy — Windhoek and northern Namibia

**Windhoek** (~1 700 m, Köppen **BSh**, hot semi-arid): mean daily max 30,7 °C (Dec) to 20,2 °C (Jun); mean daily min 17,2 °C (Jan) to 6,3 °C (Jul); annual rainfall **367 mm**, concentrated Dec–Mar; **3 605 sunshine hours/year**. Diurnal swing is large (≈ 13–14 K) and winter nights approach freezing — **heating is a real requirement**, not only cooling.

**Eenhana, Ohangwena** (17,48° S, Köppen approximately **BSh/Aw** — subtropical with a marked wet season): annual mean **22,7 °C**; warmest months Nov–Jan 25–26 °C; coolest Jun–Jul ~17 °C; annual rainfall ~**589 mm**, essentially all falling Nov–Apr with **no recorded precipitation Jun–Aug**. Hotter, wetter, flatter diurnal swing, higher humidity in the rains.

**Strategy stack, in priority order:**

1. **Orientation.** Long axis east–west; principal glazing north (equator-facing), which is easy to shade with a horizontal overhang. Minimise **west** glazing above all — late-afternoon low western sun coincides with peak internal temperature and cannot be shaded by an overhang.
2. **Shade before glass.** Verandas, deep reveals, brise-soleil, screens, planted shade. In Windhoek an 1 500–1 800 mm veranda on the north face is the single most effective move (see §5 for the derivation).
3. **Roof first.** Roofs receive the most solar radiation. Target R ≥ 3,7 m²·K/W; use a light-coloured, high-emissivity roof surface; ventilate the roof space; use a radiant barrier under sheet roofing.
4. **Mass on the inside** of any insulation, exposed to the room (not carpeted, not suspended-ceilinged away).
5. **Night purge ventilation.** Secure, insect-screened, high-level openings that can stay open overnight. Aim for 10–30 air changes per hour during the purge — this is the mechanism that makes mass work.
6. **Reduce and control glazing.** Openings sized for daylight and view, not for area. Under a 3 605-hour sunshine regime, glass is a liability unless shaded.
7. **Evaporative cooling** works well in Windhoek's low humidity and much less well in Ohangwena during the rains.
8. **Winter solar gain** — in Windhoek, admit low north sun in June–August through the same north glazing whose summer sun is cut by the overhang. This is the geometric payoff of equator-facing glazing.
9. **Rainwater and dust.** Overhangs must also handle intense, short-duration rainfall and wind-blown dust; design generous eaves and accessible gutters, or omit gutters and detail the ground drip line.

## 3. Moisture and condensation

- **Surface condensation** occurs where a surface falls below the room-air dew point. Thermal bridges (concrete lintels, ring beams, slab edges, steel columns) are the usual sites.
- **Interstitial condensation** occurs inside the assembly where the vapour pressure profile meets the temperature profile at saturation. Check by the Glaser method (BS EN ISO 13788).
- **Rule:** vapour control layer on the **warm side** of the insulation; ventilated cavity or drainage plane on the **cold side**. In a predominantly cooling climate the "warm side" is the *outside* for air-conditioned spaces — the vapour retarder position inverts. In mixed-mode Namibian buildings, prefer **vapour-open assemblies that can dry in both directions**.
- **Rising damp:** DPC minimum **150 mm above finished external ground level**; DPM under slabs, lapped and sealed to the DPC.
- **Rain penetration:** cavity walls need cavity trays and weep holes over every opening and at the DPC; single-leaf walls rely entirely on render integrity and are high-risk in driving rain.
- Design relative humidity for comfort: **30–60%**. Below 30% causes discomfort and dust; Namibia's dry season regularly sits below this.

## 4. Ventilation

| Purpose | Rate |
|---|---|
| **[ZA]** Natural ventilation opening | ≥ 5% of room floor area (SANS 10400-O) |
| Bathrooms, shower rooms, WCs | **10 air changes/hour**; 25,0 L/s per person **[ZA]** SANS 10400-O |
| Fresh air, sedentary occupancy | 7,5–10 L/s per person |
| Classroom | 8–10 L/s per person |
| Kitchen (domestic) extract | 30–60 L/s intermittent over hob |
| Night purge (cooling mass) | 10–30 ach |

**Cross ventilation** requires openings on **two different pressure zones** — opposite or adjacent façades, or high and low on the same façade. A single-sided room ventilates to a depth of about **2,0–2,5 × its ceiling height**; cross-ventilated, about **5 × ceiling height**.

**Stack ventilation** driving force increases with height difference and temperature difference. A useful rule: for every 1 m of height between inlet and outlet and every 1 K of temperature difference, expect a small but usable pressure; practical stacks need ≥ 3 m of height. Outlet area should be **equal to or larger than** inlet area for maximum flow.

## 5. Solar geometry — worked examples

Solar noon altitude: `α = 90° − |φ − δ|`, where φ is latitude (negative south) and δ is solar declination (± 23,44° at the solstices, 0° at the equinoxes).

### Windhoek — φ = −22,56°

| Date | δ | Noon altitude α | Sun bearing at noon |
|---|---|---|---|
| 21 June (winter solstice) | +23,44° | **44,0°** | Due north |
| 21 Mar / 23 Sep (equinox) | 0° | **67,4°** | Due north |
| 21 December (summer solstice) | −23,44° | **89,1°** | Due south (0,9° off vertical) |

Sunrise/sunset azimuths (from north): equinox **90° / 270°**; 21 Dec **≈ 115,5° / 244,5°**; 21 Jun **≈ 64,5° / 295,5°**.
Zenith passage (sun exactly overhead at noon) ≈ **5 December** and **6 January**.

### Eenhana, Ohangwena — φ = −17,48°

| Date | δ | Noon altitude α | Sun bearing at noon |
|---|---|---|---|
| 21 June | +23,44° | **49,1°** | Due north |
| Equinox | 0° | **72,5°** | Due north |
| 21 December | −23,44° | **84,0°** | Due south |

Sunrise/sunset azimuths: equinox **90° / 270°**; 21 Dec **≈ 114,6° / 245,4°**; 21 Jun **≈ 65,4° / 294,6°**.
Zenith passage ≈ **8 November** and **1 February**.

> ⚠️ Both sites are **inside the Tropic of Capricorn (23,44° S)**. For roughly 5 weeks either side of midsummer at Windhoek, and for roughly 12 weeks at Eenhana, the noon sun is **south of vertical** — meaning the *south* façade receives direct high-angle sun in high summer. A north-only shading strategy leaves a real gap. Provide modest overhangs or high-level screening to south glazing at these latitudes.

### Sizing a north-facing overhang

For an overhang of projection **P** at the head of a window of height **H**, the shadow drops down the wall a distance `d = P × tan α`. Full shading requires `P ≥ H / tan α`.

**Windhoek, window H = 2 100 mm:**

| Design cut-off | α | Required P | Winter (21 Jun) sunlit window height |
|---|---|---|---|
| Equinox (shade 21 Sep → 21 Mar) | 67,4° | **875 mm** | 2 100 − (0,875 × tan 44,0°) = **1 255 mm** sunlit |
| Early August (δ ≈ +18°, α ≈ 49,5°) — shade Aug → Apr | 49,5° | **1 795 mm** | ~0 mm — no winter gain from this window |
| 21 December only | 89,1° | 33 mm | irrelevant |

**Recommendation for Windhoek:** overhang **≈ 900–1 200 mm** on north glazing. This shades the whole opening from about the September equinox to the March equinox and still admits low June–August sun over roughly the lower 1,2 m of the window — the winter heating that Windhoek genuinely needs. Extend to a **1 500–1 800 mm veranda** where the space beneath is itself used, accepting reduced winter gain to the room behind.

**Eenhana, window H = 2 100 mm:**

| Design cut-off | α | Required P | Winter (21 Jun) sunlit window height |
|---|---|---|---|
| Equinox | 72,5° | **660 mm** | 2 100 − (0,660 × tan 49,1°) = **1 340 mm** sunlit |
| Shade year-round on north face | 49,1° | **1 815 mm** | 0 mm |

**Recommendation for Ohangwena:** because winter heating demand is minimal (coolest month mean 17 °C) but the hot season is long, size for **year-round shading**: a **1 500–1 800 mm veranda**, or a 700 mm overhang combined with a vertical screen or deep reveal. East and west façades cannot be shaded by horizontal overhangs at any latitude — use vertical fins, screens, deep recesses, or simply omit the openings.

**Vertical shadow angle (VSA)** for non-noon conditions: `tan(VSA) = tan α / cos(γ)`, where γ is the horizontal angle between the sun's azimuth and the normal to the façade. **Horizontal shadow angle (HSA)** = γ, and governs the depth of vertical fins.

## 6. Daylighting

- Room depth from window wall ≈ **2,0–2,5 × window head height** (overcast); **3,0–3,5 ×** under a clear sky, which is the Namibian norm; **1,5 ×** where uniformity matters; **2,5 ×** with a light shelf.
- Average daylight factor ≈ **32 × (window area / floor area)** %.
- Average illuminance ≈ **3 800 × (window area / floor area)** lux under overcast sky; **4 800 ×** under clear sky.
- Window-to-floor ratio: **10%** ≈ 100 lux minimum; **13%** ≈ 5% average DF ("cheerfully lit"); **20%** ≈ 200 lux minimum overcast.
- Target daylight factors: office 5% average / 2% minimum; kitchen 2% at work surfaces; living room 1%; bedroom 0,5%.
- Windows should span **≥ 50% of the window-wall width**; room depth ≤ **2 × room width** for full-width glazing.
- Under a bright clear sky, **glare, not quantity, is the design problem.** Use indirect and reflected light — light shelves, splayed reveals, light-coloured soffits and window walls, clerestories bouncing off a ceiling. Never place a task facing an unshaded window.
- **[ZA]** Statutory minimum: glazing ≥ **5%** of floor area (SANS 10400-O 4.3.1.1.2) — far below any comfort target.

## 7. Acoustics

**Reverberation** — Sabine: `T60 = 0,161 V / A`, with V the room volume (m³) and A the total absorption (m² sabins) = Σ(surface area × absorption coefficient α).

| Space | Target T60 (s) |
|---|---|
| Classroom (unoccupied, ≤ 280 m³) | 0,4–0,6 |
| Open-plan office | 0,4–0,6 |
| Meeting room | 0,6–0,8 |
| Lecture theatre | 0,8–1,0 |
| Multipurpose hall | 1,0–1,4 |
| Concert hall (symphonic) | 1,8–2,2 |
| Place of worship (speech-led) | 1,0–1,5 |

**Sound insulation (STC / R_w)** — practice targets:

| Partition | Target |
|---|---|
| Private office, normal privacy | STC 40 |
| Conference room, confidential | STC 45 |
| Videoconference / training room | STC 53 |
| School classroom | STC 50 |
| Residential party wall | STC/R_w 50+ |

**Background noise (NC):** private offices, boardrooms, patient rooms **NC 25–30**; open-plan offices, banks, libraries **NC 30–35**; general offices and reception **NC 35–40**.

**Absorption (NRC):** open-plan office ceiling ≥ **0,9**; meeting rooms ≥ 0,8; workstation screens ≥ 0,7.

Design rules: a partition is only as good as its weakest path — flanking through a continuous ceiling void, a shared floor screed, or an unsealed service penetration will negate the wall. Take acoustic partitions **slab to slab**. Mass law: each doubling of mass gains about **5–6 dB**; a discontinuous double-leaf construction outperforms a single leaf of the same mass.

## Sources

- [SANS 10400-XA:2021 — Energy usage in buildings](https://www.uj.ac.za/wp-content/uploads/2023/11/sans-10400-xa-the-application-of-the-national-building-regulations-environmental-sustainability-energy-usage-in-buildings-2021.pdf) — SABS (UJ-hosted copy)
- [Summary of the revised SANS 10400-XA (2021 edition)](https://roosarchitects.co.za/work/a-summary-of-the-revised-sans-10400-xa-standard-2021-edition/) — Roos Architects
- [BR 443 Conventions for U-value calculations](https://www.cibse.org/media/wzrjrf3l/conventions-for-u-value-calculations.pdf) — BRE / CIBSE
- [ISO 6946:2007](https://cdn.standards.iteh.ai/samples/40968/eef030b005bd4146b90cddaf78c64f06/ISO-6946-2007.pdf) — ISO
- [SANS 10400-O: Lighting and ventilation](https://www.sans10400.co.za/lighting-and-ventilation/) — sans10400.co.za
- [Windhoek — climate and elevation](https://en.wikipedia.org/wiki/Windhoek) — Wikipedia
- [Eenhana — climate](https://en.wikipedia.org/wiki/Eenhana) — Wikipedia
- [Eenhana Airport — coordinates](https://en.wikipedia.org/wiki/Eenhana_Airport) — Wikipedia
- [Daylight design rules of thumb](https://www.irbnet.de/daten/iconda/CIB_DC23487.pdf) — CIB / IRBnet
- [Acoustic design requirements by space type](https://datadrivenaec.com/insights/acoustic-design-requirements) — DataDrivenAEC

## Open questions

- **All solar altitudes, azimuths, overhang projections and zenith-passage dates in §5 are computed by the standard declination formulae, not taken from a published almanac.** They are accurate to roughly ±0,5° / ±2 days and are adequate for shading design, but should be confirmed against an ephemeris or sun-path tool for critical work.
- Eenhana's Köppen classification is not stated in the cited source; "BSh/Aw" is inferred from the temperature and rainfall pattern and is **not verified**.
- Time-lag and decrement-factor values in §1 are conventional practice figures, not drawn from a cited standard.
- **[NA]** No Namibian statutory thermal performance requirement was found. Whether SANS 10400-XA has been formally adopted in Namibia is unresolved.
- SANS 10400-XA Table 4 fenestration U-value and SHGC values were not extracted line-by-line; consult the standard for compliance calculations.
- Reverberation-time targets are drawn from general acoustic practice; ANSI S12.60 and equivalent SANS provisions should be checked for regulated building types.

