---
id: hydrology.water_supply
title: Water supply, rainwater harvesting, boreholes and pumps
domain: 24_hydrology_arid
tags: [rainwater-harvesting, tank-sizing, borehole-siting, geophysics, drilling, pump-selection, solar-pumping, water-quality, fluoride, nitrate, greywater, namibia]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "The Texas Manual on Rainwater Harvesting, 3rd edition", url: "https://www.twdb.texas.gov/publications/brochures/conservation/doc/RainwaterHarvestingManual_3rdedition.pdf", publisher: "Texas Water Development Board", accessed: 2026-08-25}
  - {title: "Water Resources Management Act 11 of 2013 (annotated)", url: "https://www.lac.org.na/laws/annoSTAT/Water%20Resources%20Management%20Act%2011%20of%202013.pdf", publisher: "Legal Assistance Centre, Namibia", accessed: 2026-08-25}
  - {title: "The long road to sustainability: Cuvelai-Etosha Basin (Wanke et al. 2018)", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307", publisher: "Biodiversity & Ecology 6", accessed: 2026-08-25}
  - {title: "Fluoride in Groundwater (Nordstrom, free book)", url: "https://gw-project.org/books/fluoride-in-groundwater/", publisher: "The Groundwater Project", accessed: 2026-08-25}
  - {title: "Managed Aquifer Recharge in Southern Africa (Braune, free book)", url: "https://gw-project.org/books/managed-aquifer-recharge-southern-africa/", publisher: "The Groundwater Project", accessed: 2026-08-25}
  - {title: "NASA POWER monthly series, Okongo point", url: "https://power.larc.nasa.gov/", publisher: "NASA LaRC", accessed: 2026-08-25}
related: [hydrology.namibia_cuvelai, hydrology.stormwater, hydrology.equipment]
unit_system: SI
applies_to: [okongo, ohangwena]
---

# Water supply, rainwater harvesting, boreholes and pumps

**Summary.** The practical engineering of getting water to a dryland homestead: sizing a rainwater harvesting system with a real month-by-month mass balance for Okongo, siting and drilling a borehole, selecting a pump, testing and treating the water (fluoride and nitrate are real problems in northern Namibia), storing and distributing it, and reusing greywater. The recurring theme is that in a semi-arid climate with an eight-month dry season, **storage and reliability dominate the design, not average yield**.

## Key facts

| Design parameter | Value | Basis |
|---|---|---|
| Roof runoff coefficient / collection efficiency | **0.85** | Texas Manual on Rainwater Harvesting |
| Yield per m² per mm rain (at C = 0.85) | **0.85 L** | derived |
| First-flush diversion, rule of thumb | ~10 US gal per 1,000 ft² ≈ **0.4 L/m²**; up to 1–2 gal/100 ft² ≈ **0.4–0.8 L/m²** | Texas Manual |
| Rain intensity needed to wash a sloped roof | 0.1 in/h ≈ **2.5 mm/h** (flat roof 0.18 in/h ≈ 4.6 mm/h) | Texas Manual |
| Okongo mean annual rainfall (reanalysis) | ~550 mm; driest modelled year ~210 mm | NASA POWER 1991–2024 |
| WHO guideline value, fluoride | 1.5 mg/L | WHO GDWQ |
| WHO guideline value, nitrate (as NO₃⁻) | 50 mg/L | WHO GDWQ |
| Ohangwena shallow groundwater EC | 50–1,200 µS/cm; turbidity to 255 NTU | Wanke et al. 2018 |

> ⚠️ **[NA]** Section 40 of the Water Resources Management Act 11 of 2013 permits collecting rainwater falling on your land for **own domestic use** without a licence, including on communal land. Section 39 permits a well for own domestic use outside a local authority area and outside a water protection area. Anything beyond that — irrigation, sale, supply to neighbours — needs a licence, and a borehole outside the s. 39 exemption needs a borehole licence (s. 56) drilled by a licensed driller (s. 67).

## 1. Rainwater harvesting design

### 1.1 The yield equation

```
V_annual (L) = P (mm) × A (m²) × C
```
where `A` is the **plan (horizontal projected) area** of the catchment surface — not the sloping roof area — and `C` is the runoff coefficient / collection efficiency. Use `C = 0.85` for a clean metal or tiled roof after allowing for first flush, splash, wetting and gutter overshoot. Rough or porous surfaces (thatch, unsealed concrete) are far lower and should not be used for potable collection.

**Corrugated metal (IBR/corrugated iron) is the right roof for harvesting** in this climate: smooth, low absorption, easy to keep clean, and it sheds the first millimetres quickly. Avoid lead flashing, bitumen membranes, treated timber shingles and anything that sheds fibres.

### 1.2 First flush

The first millimetre of runoff carries the dust, bird droppings, insects and ash accumulated during the dry spell — in Okongo that spell can be eight months, so the first storm of the season carries a disproportionate load. Divert **0.4–0.8 L per m² of roof** before the tank inlet. For a 150 m² roof that is **60–120 L**, i.e. two to four 6 m lengths of 110 mm PVC standpipe, or a purpose-made ball-float diverter. The standpipe must drain automatically between events (a drilled pinhole) and must be cleanable.

Also fit: leaf screens at the gutter, a mosquito-proof mesh on every tank opening (a covered tank is a mosquito breeding site otherwise), a calmed inlet to avoid stirring up sediment, and a floating extraction offtake that draws from ~150 mm below the surface rather than off the floor.

### 1.3 Yield-versus-demand: a worked example for Okongo

**Inputs.** Roof 150 m² plan area; `C = 0.85`; monthly rainfall from the NASA POWER 1991–2024 series at 17.566°S 17.216°E; tank 10 m³ starting empty; household demand 200 L/day (four people at 50 L/day).

Monthly mass balance, mean-year rainfall, 10 m³ tank:

| Month | Rain (mm) | Inflow (m³) | Supplied (m³) | Deficit (m³) | Overflow (m³) | Stored end (m³) |
|---|---|---|---|---|---|---|
| Jan | 141 | 18.0 | 6.2 | 0.0 | 13.0 | 3.8 |
| Feb | 122 | 15.6 | 5.7 | 0.0 | 9.4 | 4.3 |
| Mar | 96 | 12.2 | 6.2 | 0.0 | 6.5 | 3.8 |
| Apr | 22 | 2.7 | 6.0 | 0.0 | 0 | 0.5 |
| May | 2 | 0.3 | 0.8 | **5.4** | 0 | 0.0 |
| Jun | 0 | 0.0 | 0.0 | **6.0** | 0 | 0.0 |
| Jul | 0 | 0.0 | 0.0 | **6.2** | 0 | 0.0 |
| Aug | 0 | 0.0 | 0.0 | **6.2** | 0 | 0.0 |
| Sep | 2 | 0.3 | 0.3 | **5.7** | 0 | 0.0 |
| Oct | 15 | 1.9 | 1.9 | **4.3** | 0 | 0.0 |
| Nov | 65 | 8.3 | 6.0 | 0.0 | 0 | 2.3 |
| Dec | 86 | 10.9 | 6.2 | 0.0 | 3.2 | 3.8 |

**Result:** in an *average* year this system meets only **54%** of demand and overflows 32 m³ in the wet months. The binding constraint is not rainfall — it is that a 10 m³ tank cannot carry the wet-season surplus across the dry season.

Reliability against tank size, mean year, same roof and demand:

| Tank | 5 m³ | 10 m³ | 20 m³ | 30 m³ |
|---|---|---|---|---|
| Demand met (mean year) | 41% | 54% | 67% | 81% |
| Demand met (2019-type dry year) | 32% | 42% | 49% | 56% |

**Sensitivity — what actually fixes it.** Reducing demand to a "potable and cooking only" 80 L/day changes the picture completely:

| Roof / tank | Mean year | 2019 dry year |
|---|---|---|
| 100 m² / 20 m³ @ 80 L/d | 100% | 53% |
| 150 m² / 20 m³ @ 80 L/d | **100%** | 75% |
| 200 m² / 20 m³ @ 80 L/d | 100% | **94%** |
| 300 m² / 20 m³ @ 80 L/d | 100% | **100%** |
| 150 m² / 30 m³ @ 120 L/d | 100% | 53% |
| 300 m² / 30 m³ @ 120 L/d | 100% | 94% |

**Design conclusions for Okongo:**
1. Rainwater harvesting is a **quality** supply, not a **volume** supply. Assign it to drinking, cooking and washing-up, and put bulk washing, livestock and irrigation on the borehole.
2. **Catchment area is the more effective lever than tank size** below about 20 m³ — add roof (verandah, carport, shed, a purpose-built collection roof) before adding tank.
3. Size against the **dry year**, not the mean. A system that is 100% reliable in a mean year can be 50% reliable in a 2019.
4. Above ~20–30 m³ the marginal reliability per m³ of tank falls sharply. That is the natural stopping point unless you also add roof.

### 1.4 Storage sizing methods

- **Dry-season demand method** (quick): `V = demand/day × longest dry period`. For 80 L/day × 240 days = **19.2 m³**. This is the number that matches the simulation above and is the right first cut for a Cuvelai homestead.
- **Mass-curve (Rippl) method**: cumulative inflow minus cumulative demand; the required storage is the largest cumulative deficit. Rigorous for a single record; do it on the **driest** observed year, not the mean.
- **Behavioural / daily time-step simulation** (what the tables above are): loop the balance with spill and shortfall, report reliability. This is the modern standard and takes 20 lines of Python.
- **Rule of thumb**: 1–2 months of demand for a supplementary system; 6–8 months for a sole-source system in a monsoonal/unimodal climate.

### 1.5 Tanks

| Type | Typical sizes | Notes |
|---|---|---|
| Polyethylene (rotomoulded) | 500 L – 10,000 L | Cheapest per litre at small sizes; must be UV-stabilised and shaded; the standard choice in Namibia |
| Galvanised/Zincalume corrugated steel with liner | 5–100 m³ | Good large-volume option, shippable flat, erected on site |
| Ferrocement / mortar-plastered wire mesh | 5–50 m³ | Low material cost, local labour, common in African RWH programmes; needs skilled plastering to avoid leaks |
| Reinforced concrete, cast in situ or precast | 10 m³+ | Durable, thermally stable, can be partly buried; most expensive |
| Underground/partially buried | any | Big advantage in this climate — cooler water, no UV, no evaporation, no algae — but needs a pump to draw and must be flood- and contamination-proof |

Always: opaque or shaded (algae), sealed and screened (mosquitoes, WHO risk), an overflow routed away from the foundations, a washout at the base, and a drawoff above the sediment layer.

`needs-verification`: no current Namibian tank prices were obtained; a JoJo-type 5,000 L polyethylene tank and a 10,000 L equivalent should be priced locally in N$ before budgeting.

## 2. Borehole siting

### 2.1 Desk study first
Before any geophysics: the national groundwater database (GROWAS II, held by the Namibian Ministry), existing borehole logs within a few kilometres, the 1:1,000,000 hydrogeological map of Namibia, satellite imagery for lineaments and palaeochannels, and — in the Cuvelai — the known stratigraphy of the Cubango Megafan. In a thick, layered sedimentary basin like Ohangwena the depth-to-target is usually better predicted from neighbouring logs than from any surface survey.

### 2.2 Geophysical methods

| Method | What it detects | Typical use in Ohangwena |
|---|---|---|
| **Electrical resistivity (VES / 2-D ERT)** | Layer resistivities → clay vs sand, fresh vs saline water | The workhorse. Very effective here because fresh sand is resistive and brackish clay is conductive; delineates KOH-0/KOH-1 and the aquitard |
| **Time-domain EM (TEM/TDEM)** | Conductivity vs depth, fast, no long cables | Excellent for mapping the fresh/brackish interface and deep structure; well suited to flat sandy terrain |
| **Frequency-domain EM (e.g. EM34, EM31)** | Bulk conductivity, rapid profiling | Reconnaissance to find where to place a VES/ERT line |
| **Magnetics** | Magnetic contrasts — dykes, basement structure | Little value in a deep sedimentary basin; very useful in hard-rock Namibia for dyke-associated groundwater |
| **Seismic refraction** | Depth to bedrock, weathered-zone thickness | Useful in hard-rock terrain, not in the Kalahari sands |
| **Ground-penetrating radar** | Shallow structure (<10–15 m in dry sand) | Can image shallow palaeochannels; attenuates fast in clay |
| **Airborne EM (e.g. SkyTEM)** | Regional 3-D conductivity | The technique behind much of the deep Ohangwena mapping; scheme-scale, not homestead-scale |

**Dowsing / water divining — the honest status.** Dowsing has been tested repeatedly under controlled conditions and has never demonstrated an ability to locate groundwater beyond chance. It persists partly because in many landscapes *any* borehole finds water, so the hit rate looks respectable. If a dowser has decades of local experience, what is genuinely valuable is their **local knowledge** — where previous boreholes succeeded, where the sand thickens, where the water turned salty — not the rods. Pay for that knowledge if you want it, but commission geophysics for the siting decision, and never let a dowser's siting override a resistivity or TEM result.

## 3. Drilling and completion

**Methods**
- **Air percussion / down-the-hole (DTH) hammer** — fast in hard rock, and the standard for most southern African water wells. Struggles in unconsolidated sand without casing advance.
- **Mud rotary** — the appropriate method for thick unconsolidated sands and clays like the Cuvelai. Drilling fluid holds the hole open. Requires care: mud invasion can plug a productive sand, so a proper development stage is essential.
- **Air-lift / dual rotary with casing advance** — the best option in caving sands; casing follows the bit.
- **Cable tool (percussion)** — slow, but excellent formation samples and very good in unconsolidated ground.
- **Hand augering / jetting / hand drilling** — viable to 20–30 m in soft sand; genuinely relevant for KOH-0 in Ohangwena at a fraction of the cost.

**Completion checklist**
1. **Formation log** kept by the driller, with samples every metre. Insist on this and keep a copy (s. 218 of the Act requires records anyway).
2. **Geophysical borehole log** (gamma, resistivity) if the budget allows — it resolves the sand/clay sequence far better than cuttings.
3. **Casing** — uPVC or steel, sized for the pump. Sand-screen (slotted or wire-wrapped) opposite the productive interval, slot size chosen from a sieve analysis of the formation.
4. **Gravel pack** sized to the formation, placed by tremie, not tipped from surface.
5. **Sanitary seal** — a bentonite/cement grout in the annulus from the top of the pack to surface, at minimum 3–6 m. In Ohangwena this is not a formality: it is what stops brackish or contaminated shallow water from entering, and (for deep wells) what stops KOH-1 water leaking into KOH-2.
6. **Development** — airlifting, surging, jetting until the water clears and sand production stops. An undeveloped borehole can lose half its potential yield.
7. **Test pumping** — a step-drawdown test to find the well loss coefficient and a constant-rate test (typically 8–24 h) plus recovery, analysed by Cooper-Jacob (see `02`). Recommend the sustainable yield from the *recovery* and the long-term drawdown trend, not from the last hour of pumping.
8. **Water sample** taken at the end of the constant-rate test, not the beginning.
9. **Headworks** — raised concrete plinth, sloped apron draining away, lockable cover, and a **dip tube** so you can measure water level for the life of the borehole.

`needs-verification`: current Namibian drilling costs (per metre, by diameter and method), casing prices and test-pumping rates were not obtained. Budget from at least three quotes in N$ and expect mobilisation to a remote site like Okongo to be a significant fixed cost.

## 4. Pump selection

### 4.1 The sizing calculation
Total dynamic head:
```
TDH = static lift + drawdown + delivery head + friction losses + residual pressure
```
Hydraulic power and shaft power:
```
P_hyd (W) = ρ · g · Q · H = 9810 × Q(m³/s) × H(m)
P_shaft   = P_hyd / η_pump ;    P_electrical = P_shaft / η_motor
```

**Worked example (Okongo homestead).** Water level 25 m below ground, drawdown at the design rate 5 m, tank stand 6 m above ground, 80 m of 40 mm pipe, design flow 1.5 m³/h (0.42 L/s).

- Static lift + drawdown + delivery = 25 + 5 + 6 = 36 m
- Friction in 40 mm PE at 0.42 L/s ≈ 0.4 m/s velocity → roughly 2–3 m per 100 m; over 80 m ≈ 2 m
- Residual at outlet: 2 m
- **TDH ≈ 40 m**

```
P_hyd = 9810 × (1.5/3600) × 40 = 163 W
At η_pump = 0.45 and η_motor = 0.85 → P_electrical ≈ 430 W
```
So a nominal **0.55–0.75 kW (0.75–1 hp)** submersible, or a solar pump rated around 300–700 W array. Always check the manufacturer's **pump curve at your TDH**, not the nameplate — a pump rated "50 m max head" delivers very little at 40 m.

### 4.2 Pump types

| Type | Typical range | Notes for Ohangwena |
|---|---|---|
| **Submersible electric (multistage centrifugal)**, e.g. Grundfos SP/SQ, Franklin Electric | 0.37–7.5 kW domestic | Standard mains/generator choice. Needs 3-wire or 2-wire control, dry-run protection and a check valve |
| **Solar-direct submersible**, e.g. Grundfos SQFlex, Lorentz PS2/PSk | 0.2–4 kW array | **The best fit for a remote Namibian homestead**: no batteries, pumps when the sun shines, water stored in the tank instead of in batteries. Sizing is done on daily volume (m³/day at TDH), not on instantaneous flow |
| **Helical rotor / progressive cavity** (in SQFlex and Lorentz ranges) | low flow, high head | Better than centrifugal for deep, low-yield boreholes; tolerates variable input power well |
| **Hand pumps** (Afridev, India Mk II, Bush Pump) | to ~45 m (Afridev ~15–45 m) | The standard community-water-point technology across SADC; simple, repairable with local spares. Afridev is designed for village-level maintenance |
| **Windmill / wind pump** | to ~100 m at low flow | Historically the Namibian farm standard; robust but maintenance-heavy and superseded by solar on cost |
| **Rope pump / treadle** | shallow (<20 m) | Very cheap; suits a hand-dug KOH-0 well |

**Solar sizing rule:** a solar pump's output is expressed as m³/day at a given head for a given array size and a given peak-sun-hours figure. Okongo receives roughly **22 MJ m⁻² day⁻¹** annual mean global horizontal irradiance (NASA POWER climatology), i.e. about **6.1 peak sun hours per day** — an excellent solar resource with a modest seasonal swing (18.6 MJ in June to 24.7 MJ in October). Size the array for the *June* value, not the annual mean.

## 5. Water quality testing and treatment

### 5.1 What to test for, and when
Test **before** you commission a borehole and buy a pump, at the end of the pumping test; then annually, at the **end of the dry season** (the worst case for salinity), and after any flood.

| Parameter | Why it matters here | Typical field/lab method |
|---|---|---|
| **EC / TDS** | The primary salinity screen; the west-to-east gradient in the Cuvelai is steep | Field EC meter, µS/cm |
| **Turbidity** | Ohangwena shallow wells reach 255 NTU; turbidity shields pathogens from disinfection | Field turbidimeter, NTU |
| **Fluoride** | A real and well-documented problem in Namibian groundwater; causes dental and skeletal fluorosis. WHO guideline **1.5 mg/L**. 19% of sampled Omusati hand-dug wells exceeded it | Lab (ion-selective electrode or IC) |
| **Nitrate** | Elevated in Ohangwena deep wells — livestock, pit latrines and natural nitrogen fixation are all sources. WHO guideline **50 mg/L as NO₃⁻**. Causes methaemoglobinaemia in infants | Lab or field test strip (screening only) |
| **Sulphate** | The parameter that renders ~70% of Omusati hand-dug wells unfit | Lab |
| **Potassium** | Above WHO limits in ~50% of Ohangwena shallow-well samples | Lab |
| **Iron and manganese** | Staining, taste, and they foul pumps and filters | Lab |
| **E. coli / total coliforms** | The acute health risk, especially in hand-dug wells and after floods | Membrane filtration or Colilert; field kits exist |
| **pH, alkalinity, major ions** | For the charge balance QA and for treatment design | Lab |

Always insist on a **charge-balance check** (±5%) on any laboratory analysis; a report that does not balance is a report you cannot use.

### 5.2 Treatment

| Problem | Options |
|---|---|
| **Turbidity** | Settling, roughing filter, slow sand filter, or cartridge filtration (20 µm → 5 µm → 1 µm). Essential *before* any disinfection |
| **Bacteriological** | Boiling; chlorination (target 0.2–0.5 mg/L free chlorine after 30 min contact); UV (needs low turbidity and continuous power); SODIS in clear PET bottles; ceramic/silver candle filters |
| **Fluoride** | Bone char, activated alumina, the Nalgonda process (alum + lime), reverse osmosis. All need dosing control and residual management. **There is no simple household filter that reliably removes fluoride** — jug filters and ceramic candles do not |
| **Nitrate** | Ion exchange or reverse osmosis. Boiling **concentrates** nitrate; do not do it. The real fix is source protection: move the pit latrine, fence the kraal, and case the borehole properly |
| **Salinity (TDS/sulphate)** | Reverse osmosis, or blending with rainwater. Both expensive; the cheaper answer is usually a different source |
| **Iron/manganese** | Aeration + settling + filtration; greensand or catalytic media |

**Rule for the Okongo case:** use borehole water for washing, livestock and irrigation and harvested rainwater for drinking and cooking. That combination sidesteps fluoride, nitrate and salinity entirely for the highest-risk uses, and it is why the rainwater system in `1.3` should be sized on an 80 L/day potable demand rather than a full household demand.

## 6. Storage and distribution

- **Elevated tank vs pressure pump.** An elevated tank gives gravity pressure with no electricity and buffers pump outages. Each metre of elevation gives 0.098 bar; a 6 m stand gives ~0.6 bar, adequate for taps and a low-pressure shower but not for a modern instantaneous geyser or most pressurised solar systems. A booster pump with a pressure vessel is the alternative.
- **Two-tank architecture** is the standard robust design: a **raw/bulk tank** fed by the borehole, and a **potable tank** fed by the roof, with no cross-connection. If they must be interconnected, use an air gap, never a check valve.
- **Pipe sizing.** Keep velocity in the 0.6–1.5 m/s band. Below that, sediment settles; above it, friction losses and water hammer rise sharply. In practice 25 mm for a spur, 32–40 mm for a main run to a tank.
- **UV degradation.** Above-ground PE and PVC pipe in Namibian sun has a short life; bury it, or use UV-stabilised pipe and sleeve exposed runs.
- **Thermal management.** A buried or shaded tank delivers water 10–15 °C cooler than a black tank in the sun, which matters for palatability and for suppressing biofilm.

## 7. Greywater reuse

Greywater (bath, shower, basin, laundry — **not** toilet or kitchen sink) is typically 50–70% of household wastewater and is the cheapest incremental water source available.

- **Direct irrigation** is the simplest and safest use: subsurface or mulch-basin distribution to fruit trees and ornamentals, never sprayed and never onto leafy vegetables eaten raw.
- **Do not store untreated greywater** for more than about 24 hours — it turns septic and smells.
- **Soaps matter.** Use low-sodium, low-boron, phosphate-free detergents; sodium is the ingredient that destroys soil structure over years, and this soil is already fragile.
- **Salinity accumulation** is the long-term risk in an arid climate: every irrigation cycle adds salt and evaporation concentrates it. Periodic leaching with rainwater, or rotating irrigated areas, is necessary.
- **Simple treatment train**: grease trap → settling/surge tank → coarse filter → gravity distribution to mulch basins. A constructed reed bed adds treatment if there is space and a reliable flow.
- **Blackwater** in this setting normally goes to a properly sited and lined pit latrine or septic tank with soakaway — **downgradient and at least 30 m from any well or borehole**, and above the seasonal high water table. In the Cuvelai's flat, sandy, shallow-water-table terrain this separation is the single most important thing protecting your own drinking water.

## Sources

- [The Texas Manual on Rainwater Harvesting, 3rd ed.](https://www.twdb.texas.gov/publications/brochures/conservation/doc/RainwaterHarvestingManual_3rdedition.pdf), Texas Water Development Board — collection efficiency, first-flush volumes, roof-washing intensity, and the yield-equation form.
- [Water Resources Management Act 11 of 2013, annotated](https://www.lac.org.na/laws/annoSTAT/Water%20Resources%20Management%20Act%2011%20of%202013.pdf), Legal Assistance Centre — ss. 39, 40, 56, 67, 218.
- Wanke, H. et al. (2018) [*The long road to sustainability*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307) — EC, turbidity, fluoride, nitrate, potassium and sulphate exceedances in Ohangwena and Omusati.
- Nordstrom, D.K., [*Fluoride in Groundwater*](https://gw-project.org/books/fluoride-in-groundwater/), The Groundwater Project (free, 130 pp.).
- Braune, E., [*Managed Aquifer Recharge in Southern Africa*](https://gw-project.org/books/managed-aquifer-recharge-southern-africa/), The Groundwater Project (free, 96 pp., ISBN 978-1-77470-006-8).
- [NASA POWER](https://power.larc.nasa.gov/) — Okongo monthly rainfall 1991–2024 and solar irradiance climatology; the RWH mass balance above was computed from these data.

## Open questions

- **No Namibian prices** (tanks, drilling per metre, pumps, laboratory analyses) were verified. All cost statements are deliberately omitted rather than estimated.
- WHO guideline values for fluoride (1.5 mg/L) and nitrate (50 mg/L) are quoted from general knowledge of the WHO *Guidelines for Drinking-water Quality*; the WHO publication page was reachable but the values were not extracted from it directly — treat as `needs-verification`.
- Namibian drinking-water quality standards (as distinct from WHO guidelines) were not located.
- Hand-pump depth ranges (Afridev, India Mk II) are from general knowledge and need checking against manufacturer/RWSN documentation.
