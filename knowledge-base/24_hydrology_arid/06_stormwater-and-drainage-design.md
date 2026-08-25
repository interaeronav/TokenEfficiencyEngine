---
id: hydrology.stormwater
title: Stormwater and drainage design for arid sites
domain: 24_hydrology_arid
tags: [stormwater, idf-curves, rational-method, time-of-concentration, curve-number, culvert, swale, erosion-control, suds, freeboard, flood-risk, oshana, namibia]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SANRAL (South African National Roads Agency) — Drainage Manual publisher", url: "https://www.sanral.co.za/", publisher: "SANRAL", accessed: 2026-08-25}
  - {title: "Roads Authority of Namibia", url: "https://www.ra.org.na/", publisher: "Roads Authority, Namibia", accessed: 2026-08-25}
  - {title: "Water Research Commission (South Africa)", url: "https://www.wrc.org.za/", publisher: "WRC", accessed: 2026-08-25}
  - {title: "susdrain — SuDS guidance", url: "https://www.susdrain.org/", publisher: "CIRIA / susdrain", accessed: 2026-08-25}
  - {title: "Runoff curve number", url: "https://en.wikipedia.org/wiki/Runoff_curve_number", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "EPA Storm Water Management Model (SWMM)", url: "https://www.epa.gov/water-research/storm-water-management-model-swmm", publisher: "US EPA", accessed: 2026-08-25}
  - {title: "NASA POWER monthly series, Okongo point", url: "https://power.larc.nasa.gov/", publisher: "NASA LaRC", accessed: 2026-08-25}
related: [hydrology.arid_zone, hydrology.namibia_cuvelai, hydrology.water_supply]
unit_system: SI
applies_to: [okongo, ohangwena, cuvelai-etosha-basin]
---

# Stormwater and drainage design for arid sites

**Summary.** Site-scale drainage engineering for a semi-arid, extremely flat, sandy landscape. Covers where to get design rainfall for Namibia (and the honest answer that you will probably be borrowing South African methods), the rational method and its limits, time of concentration, the SCS curve number method and why it misbehaves in drylands, sizing culverts, channels and swales, erosion control in sand, infiltration-based SuDS in arid contexts, flood-risk assessment and freeboard, and how to site a building above flood level in an oshana landscape.

## Key facts

| Design item | Value / rule | Basis |
|---|---|---|
| Rational method validity | catchments up to ~50–200 ha (some authorities 15 ha) | standard practice |
| Rational formula (SI) | `Q = C·i·A / 3.6` with i in mm/h, A in km² | standard |
| Minimum time of concentration | commonly floored at 5–10 min | standard practice |
| Manning n, sandy channel with light vegetation | 0.030–0.045 | textbook range |
| Permissible velocity, fine sand, unlined | **0.3–0.6 m/s** | erosion threshold |
| Permissible velocity, grassed channel (good cover) | 1.2–1.8 m/s | erosion threshold |
| Typical residential culvert design return period | 1:10 to 1:25 year | standard practice |
| Building floor level freeboard above design flood | **≥ 0.3 m**, commonly 0.5 m | standard practice |
| Okongo mean annual rainfall (reanalysis) | ~550 mm; wettest modelled month 751 mm (Nov 2007) | NASA POWER |

> ⚠️ Every numeric design rule in this file is a standard-practice range, not a Namibian legal requirement. Namibia has no published national site-drainage code equivalent to SANS 10400. Confirm the requirements of the Ohangwena Regional Council / Okongo Village Council and, where a road crossing is involved, the Roads Authority, before finalising any design.

## 1. Design rainfall: IDF curves for Namibia

An intensity-duration-frequency (IDF) curve gives the rainfall intensity `i` (mm/h) for a chosen duration and return period. You need it for the rational method, and you cannot honestly do site drainage without one.

**Where to get it, in order of preference:**

1. **Namibia Meteorological Service** daily and (where available) sub-daily records for the nearest long-record station. Sub-daily records in northern Namibia are scarce; you may only get daily depth.
2. **SASSCAL WeatherNet** — the SASSCAL automatic weather station network across Namibia, Angola, Botswana and Zambia records at high frequency and is the most likely source of genuine sub-hourly northern-Namibian rainfall data. Several SASSCAL stations sit inside the Cuvelai alluvial plain.
3. **Regional South African methods.** In the absence of Namibian IDF, southern African practice borrows: the **SANRAL Drainage Manual** (6th edition; the standard road-drainage reference across the region and used by consultants working in Namibia) and the Water Research Commission's design-rainfall work (Smithers & Schulze's *Design Rainfall Estimation in South Africa*, WRC report and associated software). Both are calibrated on South African data; applying them across the border is defensible for method but not for the rainfall statistics themselves.
4. **Deriving DDF from daily data.** With only daily maxima, fit an extreme-value distribution to the annual daily maximum series, then disaggregate to shorter durations with an empirical ratio relationship (e.g. Bell's equation, or a regional depth-duration ratio set). This is approximate and should be stated as such in any report.
5. **Satellite/reanalysis products** (IMERG at 30 min, CHIRPS daily) can supplement a sparse gauge network but under-resolve convective intensity peaks — they are not a substitute for a rain gauge when sizing a culvert.

> `needs-verification` — **no Namibian IDF curve set was located during this research pass.** Do not use a borrowed South African intensity as though it were local. If the design matters, install a tipping-bucket gauge at the site (see `07`) and start a record; two seasons of local data plus a regional method is far better than a regional method alone.

## 2. The rational method and its limits

```
Q = C · i · A / 3.6          [Q in m³/s, i in mm/h, A in km²]
```
or, in hectare form, `Q (m³/s) = C · i (mm/h) · A (ha) / 36,000`.

`C` is the runoff coefficient — the fraction of rainfall that becomes peak runoff:

| Surface | C |
|---|---|
| Roof, metal or tile | 0.85–0.95 |
| Asphalt / concrete paving | 0.80–0.95 |
| Gravel / compacted earth road | 0.40–0.65 |
| Bare compacted sand | 0.25–0.50 |
| Deep loose sand, vegetated | **0.05–0.15** |
| Grassed area, sandy soil, flat | 0.10–0.20 |
| Cultivated mahangu field, sandy | 0.10–0.25 |

Note how low the natural values are on Kalahari sand — this is the central fact of drainage design at Okongo. **Almost all runoff on a Cuvelai plot comes from what you build**, not from the ground you build on. Roofs, paving and compacted vehicle areas are the sources; the surrounding sand is a sink.

**Assumptions the rational method makes** (and where they break in drylands):
- Rainfall is uniform over the catchment and constant for the duration `t_c`. Fails badly for convective cells over anything but a very small area.
- The whole catchment contributes by time `t_c`. In drylands, transmission losses and infiltration on the way mean the far end may never contribute.
- `C` is constant. In reality `C` rises sharply with storm depth and with antecedent surface crusting, and a single value cannot represent both a 1:2 and a 1:100 event. Some manuals apply a frequency factor `C_T` increasing `C` for rarer events; do this.
- Return period of rainfall = return period of runoff. Approximately true for impervious catchments, poor for pervious ones.

**Use it for:** plot-scale drainage, roof and yard runoff, small culverts, road side-drains, up to a few tens of hectares.
**Do not use it for:** anything where storage matters (detention basins), anything with a hydrograph shape requirement, or catchments beyond a couple of km².

## 3. Time of concentration

`t_c` is the time for runoff to travel from the hydraulically most distant point to the outlet. In the rational method the design storm duration is set equal to `t_c`.

**Kirpich (small, steep, natural catchments):**
```
t_c (min) = 0.0195 · L^0.77 · S^(−0.385)        [L in m, S in m/m]
```

**Kerby / Hathaway** for overland flow:
```
t_c (min) = 1.44 · (L · n / √S)^0.467           [L in m, retardance n]
```

**Segmented (recommended)** — split the flow path into sheet flow, shallow concentrated flow and channel flow and sum the travel times. Sheet flow (SCS/NRCS kinematic form):
```
t = 0.091 · (n·L)^0.8 / (P2^0.5 · S^0.4)        [hours; L ≤ 30 m; P2 = 2-yr 24-h rainfall in mm]
```
Channel flow travel time is simply `L / V` with `V` from Manning.

> ⚠️ **The flat-terrain problem.** Kirpich and most empirical formulas contain `S^(−0.385)` or similar. On a Cuvelai gradient of 1:5,000 (S = 0.0002), these formulas return absurdly long times of concentration and therefore absurdly low intensities and design flows. On very flat ground, use the segmented method with realistic velocities (sheet flow on flat sand: 0.1–0.3 m/s), impose a sensible maximum `t_c`, and cross-check the result against a simple volume argument: how much water falls on the contributing area in the storm, and where can it physically go?

Standard practice also imposes a **minimum** `t_c` of 5–10 minutes so that very small plots do not get assigned physically impossible intensities.

## 4. SCS curve number method

```
Q = (P − I_a)² / (P − I_a + S)      for P > I_a,  else Q = 0
S = 25400/CN − 254                  [mm]
I_a = 0.2·S    (traditional)  or  I_a = 0.05·S   (modern recommendation)
```
`CN` runs from ~30 (deep sand, good cover) to 98 (impervious). Hydrologic soil group A (deep sand, high infiltration, low runoff potential) is the correct group for most of the Eastern Sand Zone around Okongo — CN values in the 30s to 50s for vegetated conditions.

**Why it misbehaves in drylands:**
- The method was derived from small US agricultural catchments and is fundamentally a **saturation-excess**, storm-total formulation. It has no rainfall-intensity term at all, so it cannot represent infiltration-excess runoff — the dominant dryland mechanism.
- The initial abstraction `I_a = 0.2S` is now widely regarded as too high; `0.05S` fits observed data better and matters more in dry conditions where the abstraction is a large fraction of a small storm.
- Antecedent moisture condition (AMC I/II/III) adjustments swing CN by 15–20 points and are essentially unconstrained in a dryland where the soil is usually AMC I.
- For low-CN sandy catchments the method returns zero runoff for most storms — which is often *correct* physically, but means the design flow is entirely determined by the tail of the CN distribution you assumed.

**Use it for:** volume estimation on a plot with known impervious fractions, and where a hydrograph is needed via a unit hydrograph in HEC-HMS. **Be sceptical of it for:** natural sandy catchments, and any case where storm intensity rather than depth drives the response.

## 5. Sizing culverts, channels and swales

### 5.1 Culverts
Two control conditions; size for the worse:

- **Inlet control** — the barrel can carry more than the inlet admits. Capacity depends on headwater depth `HW`, inlet geometry and barrel area. Governed by the inlet-control nomographs (HDS-5 / SANRAL Drainage Manual). Typical design constraint: `HW/D ≤ 1.2–1.5`.
- **Outlet control** — the barrel and tailwater govern. Energy equation:
```
HW = TW + H_L − ΔZ ,   H_L = (1 + k_e + 19.63·n²·L/R^(4/3)) · V²/2g
```
with `k_e` the entrance loss coefficient (0.2 for a bevelled/headwall inlet, 0.5 for a projecting pipe end, 0.7 for a mitred end).

**Practical rules for a sandy, flat site:**
- Minimum diameter 450 mm for a driveway culvert; 600 mm if there is any chance of debris or sediment. Anything smaller blocks.
- Provide **headwalls and wingwalls** — in sand, a projecting pipe end will undermine and collapse within a few seasons.
- **Scour protection** at the outlet (riprap apron, gabion mattress, or concrete apron sized to about 3–4 × the pipe diameter in length). This is where sandy sites fail first.
- Set the invert **at or slightly below** the natural bed so sediment passes through rather than accumulating.
- Design for **blockage**: a 1:25 flow through a 50%-blocked culvert should not flood the house.

### 5.2 Open channels and swales
Size with Manning (see `02`), then check velocity against the erosion threshold:

| Lining | Permissible mean velocity |
|---|---|
| Fine sand, unlined | **0.3–0.6 m/s** |
| Sandy loam | 0.5–0.8 m/s |
| Grass, good cover, sandy soil | 1.2–1.8 m/s |
| Riprap (D50 150 mm) | 2.5–3.0 m/s |
| Concrete | 4–6 m/s (check abrasion) |

If the required velocity exceeds the lining's tolerance, either flatten the grade with **check dams / drop structures**, widen the section, or upgrade the lining. On a Cuvelai plot the natural grade is so flat that the usual problem is the opposite: velocity too **low** to keep sediment moving, so the swale silts up and stops working. Design a self-cleansing minimum velocity (~0.6 m/s at design flow) and accept that on a 1:1,000 slope you will need a wide, shallow, grassed section.

**Swale geometry that works here:** trapezoidal, side slopes 1:4 or flatter (mowable, safe, and stable in sand), bottom width ≥ 0.6 m, depth 0.3–0.6 m, longitudinal grade 0.5–2%, densely grassed.

## 6. Erosion control in sandy soils

Sand has essentially no cohesion; once flow concentrates, a rill becomes a donga in a single season. The principles:

1. **Never concentrate flow you do not have to.** Sheet flow over grass is stable; the same volume in a 300 mm rill is not.
2. **Disperse at the source.** Level spreaders, gravel aprons, or simply discharging a downpipe onto a splash slab and letting it spread.
3. **Cover is everything.** Established grass is the cheapest and most effective erosion control in sand. Plan for a full growing season to establish it before the first big storm, and protect it while it establishes (mulch, jute netting, brush packing).
4. **Slow the water.** Check dams (rock, gabion, brushwood) at intervals such that the crest of one is level with the toe of the next.
5. **Protect every transition** — pipe outlets, kerb inlets, swale confluences, the toe of every embankment.
6. **Manage the road.** In sandy terrain the graded road, its borrow ditch and its culverts are usually the largest single erosion source on a rural plot. Crown the road, provide frequent mitre drains (turnouts) discharging to vegetated areas, and never let a road ditch run more than ~50–80 m without a turnout.
7. **Wind erosion is the other half.** Bare sand between structures deflates in the dry season; the sand ends up in your swales and your gutters. Vegetate, mulch, or gravel every disturbed surface.

## 7. SuDS and infiltration devices in an arid context

Sustainable drainage systems (SuDS) — soakaways, infiltration trenches, permeable paving, swales, bioretention, rainwater harvesting — fit dryland conditions **better** than conventional piped drainage, for three reasons: deep sand has enormous infiltration capacity; runoff volumes are small and infrequent; and every litre infiltrated is a litre added to shallow storage rather than exported.

The adaptations that matter:

- **Infiltration is easy; the problem is the water table.** Standard SuDS guidance requires ≥1 m of unsaturated soil beneath an infiltration device. In the Cuvelai the seasonal high water table can be within 1–3 m of the surface in the iishana; site infiltration devices on the higher sandy ground, and survey the wet-season water level before designing.
- **Contamination pathway.** Rapid infiltration through clean sand into a shallow aquifer that you also drink from is a direct contamination route. Keep infiltration devices well away from and downgradient of any well, and never infiltrate runoff from a vehicle yard, a workshop or a livestock kraal without pre-treatment.
- **Size on a design storm, not on a continuous simulation.** Soakaway volume `V = A_imp × (design rainfall depth) × C − (infiltration during the storm)`; check the half-drain time (`≤ 24 h` is the usual criterion, easily met in sand).
- **Sediment is the killer.** Every infiltration device in a sandy, windy environment silts up. Provide a pre-treatment forebay or filter strip, and make the device excavatable for maintenance.
- **Vegetated SuDS need water.** A bioretention cell planted with species that need year-round moisture will die in the eight-month dry season and stop functioning. Use indigenous, drought-tolerant species and design for a dry, dormant state as the normal condition.
- **Harvesting is the highest-value SuDS component here** because it substitutes for supply as well as attenuating runoff (see `05`).

## 8. Flood risk, freeboard and siting in an oshana landscape

The Cuvelai is the hardest flood-risk setting to read, because the topographic signal is tiny. A 300 mm rise floods square kilometres.

**How to establish the design flood level on a plot:**
1. **Ask.** Local knowledge of the 2008, 2009 and 2011 efundja is the single best dataset available. Ask neighbours and elders where the water reached in those years and mark it.
2. **Look for the evidence.** Debris lines, silt staining on trees and structures, changes in grass species, the edge of the *omahenene* grassland. In an oshana the vegetation boundary is a flood-frequency map.
3. **Satellite flood mapping.** Sentinel-1 SAR and MODIS/Landsat imagery from February–April of 2008, 2009, 2011 and 2017 show the actual inundated extent. Free, and far more reliable than any model at this scale. Sentinel-1 in particular sees through cloud, which matters during a flood season.
4. **A high-resolution DEM.** SRTM and Copernicus 30 m DEMs have vertical errors of the same order as the entire flood depth here and are **not adequate** on their own. A drone photogrammetry or RTK-GNSS survey of the plot, tied to a local benchmark, is the only way to get useful contours.
5. **Do not rely on a hydraulic model** unless you have a survey-grade DEM and a defensible upstream inflow. In this terrain a 2-D model on a poor DEM produces confident nonsense.

**Freeboard and siting rules:**
- Set the finished floor level **at least 0.3 m, preferably 0.5 m, above the highest known flood level**, and add more if the evidence is thin.
- Build on the **oshana-margin sand rises**, not on the oshana floor — which is also where the traditional homestead pattern places buildings, for exactly this reason. The traditional siting logic is a flood-risk assessment refined over centuries; do not discard it.
- Keep **access** above flood level too: a house you cannot reach for three weeks is a house you cannot live in.
- Site the **pit latrine / septic soakaway** above the flood level and well downgradient of the well. Latrines flooding is the primary mechanism by which an efundja becomes a cholera and diarrhoeal-disease event.
- Put the **pump, switchgear and generator** above flood level, on a plinth.
- **Do not build across an oshana.** Even a low earth causeway will pond water upstream, redirect flow, and eventually be destroyed. If you must cross, use adequate culverts sized on the flow width, not the channel depth.

## 9. Stormwater management on a residential plot — a working scheme

For a homestead on sandy ground near Okongo:

1. **Roofs** → gutters → first-flush diverters → rainwater tanks (see `05`). This removes the largest impervious area from the runoff problem entirely and converts it into supply.
2. **Tank overflow** → a level spreader or a gravel-filled soakaway/infiltration trench **at least 5 m from the building footings**, discharging into a vegetated area. Never against the wall.
3. **Paved areas** kept small and permeable where possible (gravel, permeable block paving, or simply a compacted-sand vehicle area with a grass verge).
4. **Yard and driveway runoff** → shallow grassed swales at 0.5–2% grade → an infiltration basin or a shallow depression planted with indigenous species. Size the basin for the 1:10 24-hour depth from the contributing impervious area.
5. **Building platform** raised 0.3–0.5 m above surrounds, with the ground graded to fall away from the building for the first 2 m at ~1:20.
6. **Sub-surface drainage** is usually unnecessary in deep sand, but where a plot sits on shallow calcrete a perched water table can develop and a shallow French drain around the platform is worthwhile.
7. **Erosion protection** at every discharge point, and grass cover on every disturbed surface established before the first wet season.
8. **Do not export a problem.** Whatever you build should not increase runoff crossing your boundary. In a flat landscape where everyone's water is everyone else's, this is a neighbourly obligation as much as an engineering one.

## Sources

- [SANRAL](https://www.sanral.co.za/) — publisher of the *Drainage Manual*, the standard road-drainage reference used across southern Africa including in Namibian practice.
- [Roads Authority, Namibia](https://www.ra.org.na/) — the Namibian roads authority whose standards govern road crossings.
- [Water Research Commission, South Africa](https://www.wrc.org.za/) — publisher of the South African design-rainfall research (Smithers & Schulze).
- [susdrain / CIRIA](https://www.susdrain.org/) — SuDS design guidance.
- [Runoff curve number](https://en.wikipedia.org/wiki/Runoff_curve_number), Wikipedia — cross-check of the CN formulation.
- [EPA SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm) — the free model for plot- and neighbourhood-scale stormwater simulation (currently SWMM 5.2.4).
- [NASA POWER](https://power.larc.nasa.gov/) — Okongo rainfall series used for the wet/dry context figures.

## Open questions

- **No Namibian IDF curves were located.** This is the single largest gap for practical design in this domain.
- SANRAL Drainage Manual edition number and its current download URL were not verified; the SANRAL homepage responds but the manual page was not located.
- Runoff coefficients, permissible velocities and entrance-loss coefficients above are standard textbook ranges, not values verified against a primary manual in this pass.
- Namibian statutory requirements for site drainage, floor levels and freeboard (if any exist beyond local authority by-laws) were not established.

