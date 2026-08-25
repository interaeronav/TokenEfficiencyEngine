---
id: hydrology.arid_zone
title: Arid and semi-arid zone hydrology
domain: 24_hydrology_arid
tags: [arid, dryland, ephemeral-rivers, transmission-losses, recharge, chloride-mass-balance, palaeowater, endorheic, flash-flood, fog, salinity, groundwater-dependent-ecosystems, namibia]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Deep, semi-fossil aquifers in southern Africa (Himmelsbach et al. 2018)", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00306", publisher: "Biodiversity & Ecology 6", accessed: 2026-08-25}
  - {title: "The long road to sustainability: Cuvelai-Etosha Basin (Wanke et al. 2018)", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307", publisher: "Biodiversity & Ecology 6", accessed: 2026-08-25}
  - {title: "Spatio-temporal variations of hydrochemical and isotopic patterns of groundwater in hand-dug wells: the Cuvelai-Etosha Basin", url: "https://piahs.copernicus.org/articles/378/29/2018/", publisher: "Proc. IAHS 378 (Copernicus, open access)", accessed: 2026-08-25}
  - {title: "Identifying hydro-meteorological events from precipitation extremes indices over northern Namibia, Cuvelai Basin (Persendt et al. 2015)", url: "https://jamba.org.za/index.php/jamba/article/view/177", publisher: "Jàmbá: Journal of Disaster Risk Studies", accessed: 2026-08-25}
  - {title: "Sand, salt and water in the Stampriet Basin, Namibia: chloride mass balance recharge (Stone & Edmunds 2012)", url: "https://doi.org/10.4314/wsa.v38i3.2", publisher: "Water SA 38(3)", accessed: 2026-08-25}
  - {title: "Monitoring the Dynamics of Ephemeral Rivers from Space: the Kuiseb River, Namibia", url: "https://doi.org/10.3390/w14193142", publisher: "Water 14(19):3142 (MDPI, open access)", accessed: 2026-08-25}
  - {title: "NASA POWER monthly data, Okongo point", url: "https://power.larc.nasa.gov/", publisher: "NASA LaRC", accessed: 2026-08-25}
related: [hydrology.overview, hydrology.namibia_cuvelai, hydrology.coursework]
unit_system: SI
---

# Arid and semi-arid zone hydrology

**Summary.** Drylands are not simply humid catchments with the rainfall turned down. The dominant fluxes, the dominant processes and the dominant uncertainties are all different, and most of the standard hydrological toolkit was built for the other case. This file sets out what actually changes: rainfall variability and intermittency, the overwhelming dominance of evaporation, transmission losses that make discharge decrease downstream, focused rather than diffuse recharge, the difficulty of measuring recharge at all, fossil and semi-fossil groundwater, endorheic drainage, ephemeral rivers, flash floods, salinity, and groundwater-dependent ecosystems — with Namibian numbers throughout.

## Key facts

| Property | Dryland value | Where measured |
|---|---|---|
| Aridity index P/ET₀ (hyper-arid / arid / semi-arid / dry sub-humid) | <0.05 / 0.05–0.20 / 0.20–0.50 / 0.50–0.65 | UNEP classification |
| Okongo P/ET₀ | **0.24** (semi-arid) | computed, NASA POWER + FAO-56 |
| Interannual rainfall CV, Okongo | **0.40** | computed, POWER 1991–2024 |
| Direct recharge, vegetated deep sheet sands, Ohangwena | **9–20 mm yr⁻¹** | Wanke et al. 2018 |
| Direct recharge, bare deep sheet sands | **11 mm yr⁻¹** (mean); one site **5 mm yr⁻¹** | Wanke et al. 2018 |
| Indirect recharge, depressions on calcrete, single season | **12.5–67 mm** | Wanke et al. 2018 |
| Recharge to the deep KOH-2 aquifer | **<1% of MAP**, a few million m³ yr⁻¹ basin-wide | Himmelsbach et al. 2018 |
| Shallow groundwater EC, Ohangwena | 50–1,200 µS/cm | Wanke et al. 2018 |
| Shallow groundwater EC, Omusati (100 km west) | 140–**11,450** µS/cm; ~70% unfit (sulphate) | Wanke et al. 2018 |
| Aquitard K, Ohangwena (swelling clays, confined) | ~10⁻⁹ m s⁻¹ | Dill et al. 2013 in Himmelsbach et al. 2018 |
| KOH-2 aquifer K | 10⁻⁶–10⁻⁵ m s⁻¹ | Himmelsbach et al. 2018 |

## 1. Rainfall variability, intermittency and spatial structure

The defining statistic of dryland rainfall is not the mean but the **coefficient of variation**. As a rough global rule, CV ≈ 1.5 × (1/√MAP in mm) — dryness and variability are two views of the same thing. At Okongo the modelled CV is 0.40; the driest and wettest years in a 34-year reanalysis series differ by a factor of six (212 mm in 2019, 1330 mm in 2007). That range straddles a drought emergency at one end and regional flooding at the other, and both are *normal*. Planning against the mean is therefore planning against a value that rarely occurs.

Beyond interannual variability:

- **Seasonality is extreme.** At Okongo, ~90% of annual rainfall falls December–March; June, July and August are effectively zero. Any storage system has to bridge eight dry months, not a few weeks.
- **Intermittency within the wet season.** A "rainy season" in the Cuvelai is a sequence of a few dozen rain days, of which perhaps five to ten deliver most of the depth.
- **Convective spatial structure.** Storm cells are typically 5–20 km across with sharp gradients. Two farms 15 km apart can record 60 mm and 0 mm on the same afternoon. The consequences: (i) a single rain gauge is a poor estimator of areal rainfall; (ii) catchment-average rainfall is systematically *over*estimated if you apply a point value across an area; (iii) satellite products (CHIRPS, IMERG) capture the pattern better than a sparse gauge network but under-resolve the peaks.
- **Decadal clustering.** Northern Namibia alternates between multi-year dry phases and wet phases on roughly a 10–15 year rhythm; 1992–93 was severely arid, 2008–2011 produced repeated regional flooding, and 2015–2016 and 2019 were droughts. Short records inherit whichever phase they sampled.

## 2. Evaporation dominance

With ET₀ around 2400 mm yr⁻¹ against ~550 mm of rain, potential evaporative demand exceeds supply by roughly 4.4:1 at Okongo and by 20:1 or more in the Namib. Consequences that matter in practice:

- **Open water is a liability.** An uncovered tank or a farm dam loses on the order of 5–8 mm day⁻¹ in the hot months. A 2 m deep open pond in Ohangwena will lose more than its full depth in a year. Covered tanks, sand dams and aquifer storage exist for this reason.
- **Canals bleed.** The Calueque–Oshakati open canal system loses water continuously to seepage and evaporation; isotope work has been used specifically to quantify that loss (Koeniger et al. 2020).
- **Soil evaporation intercepts most infiltration.** Rain that wets only the top 0.2–0.5 m of a sandy profile is returned to the atmosphere within weeks. Only events large enough to push the wetting front below the evaporation-influenced zone contribute to recharge — which is why recharge correlates with the number of large events, not with annual total.
- **The evaporation term dwarfs the residual.** Recharge in Ohangwena is 1–4% of rainfall. A 5% error in ET is larger than the entire recharge signal. This is the structural reason that recharge cannot be obtained by difference in a dryland.

## 3. Transmission losses in ephemeral channels

In a humid catchment discharge grows downstream as tributaries and baseflow contribute. In a dryland sand-bed channel, discharge *shrinks* downstream through **transmission losses** — infiltration into the bed and banks, plus evaporation from the wetted perimeter and from residual pools.

- Losses are commonly 10–50% of flow volume per 10–20 km of channel, and a flood wave frequently ends in the sand without ever reaching the basin outlet. The observable signature is a **drying front** that advances down-channel after the flood peak has passed.
- Losses depend on bed material, antecedent bed moisture, flood duration and wetted area — not simply on channel length. The first flood of a season loses far more than the third.
- Consequence for measurement: two gauging stations on the same ephemeral river are not measuring "the same water", and a rating curve calibrated in one reach does not transfer.
- Consequence for water supply: transmission loss *is* the recharge mechanism for alluvial aquifers. Along the Kuiseb the losses recharge the delta aquifer that supplies Walvis Bay and Swakopmund; the "loss" is the resource.
- Modelling approaches: empirical loss functions (a fixed depth of loss per unit wetted area per event), Green-Ampt applied to the bed, or coupled surface–groundwater codes (MODFLOW SFR/UZF, MIKE SHE). All need event data that rarely exist.

## 4. Focused vs diffuse recharge

**Diffuse (direct) recharge** is areally distributed percolation through the soil profile. **Focused (indirect, localised) recharge** occurs beneath channels, depressions, pans, dune slacks, and macropores — anywhere water concentrates before infiltrating.

In drylands the focused component usually dominates, and the SASSCAL Cuvelai measurements show it plainly. On vegetated deep sheet sands direct recharge was 9–20 mm yr⁻¹ (one bare-soil site 11 mm yr⁻¹, another only 5 mm yr⁻¹); under depressions underlain by calcrete a single 2016/17 season delivered 12.5–67 mm; dune-sand sites returned 9–14 and 17–25 mm yr⁻¹, and a specific 2013/14 year gave 31 mm. The spread within a single landscape is larger than the difference between a wet and a dry year at a single site.

Practical implications:
- A uniform "recharge = 2% of rainfall" applied across a model domain gets both the total and the spatial pattern wrong.
- Recharge maps should be built from landform, not from rainfall isohyets.
- Interventions that create ponding (contour bunds, sand dams, recharge basins, even a badly-drained road embankment) can materially increase local recharge. This is the physical basis for managed aquifer recharge in drylands.
- Conversely, clearing vegetation or crusting the surface shifts water from recharge to runoff and evaporation.

## 5. Estimating recharge — the methods and their honest limits

No single method is trustworthy alone. Standard practice is to apply at least three and to look at whether they agree in order of magnitude.

**Chloride mass balance (CMB).** Chloride is conservative, arrives in rainfall and dry deposition, and concentrates by evapotranspiration.
```
R = P · (Cl_p / Cl_sw)
```
`R` recharge (mm yr⁻¹), `P` precipitation, `Cl_p` chloride concentration in bulk precipitation, `Cl_sw` chloride in soil water below the root zone (or in groundwater). Strengths: cheap, integrates decades to millennia, ideal for deep sandy profiles. Weaknesses: needs a good `Cl_p` estimate (rarely measured, and dry deposition can exceed wet); assumes piston flow, so preferential flow through root channels and termite galleries biases it; fails where there is a chloride source in the aquifer matrix; and gives a long-term average, not this year's value. Stone & Edmunds applied it to the Kalahari dunefield above the Stampriet aquifer in Namibia and it remains the reference method for the region.

**Water-table fluctuation (WTF).**
```
R = S_y · Δh / Δt
```
Simple and appealing, but `S_y` is usually the least well-known parameter in the whole system, and the method attributes every rise to recharge — pumping cessation, barometric effects and lateral flow all masquerade as recharge. The Cuvelai team drilled six shallow boreholes at Omboloka (23 and 20 m), Ohameva (26 m), Okamanya (31 m), Epumbalondjaba (10 m) and Oshanashiwa (30 m), logged them daily with Solinst Leveloggers through the 2016/17 season, and multiplied water-level rise by independently-derived effective porosity — and were explicit that the result is a conservative estimate because abstraction was not deducted.

**Environmental and applied isotopes.** δ¹⁸O and δ²H distinguish evaporated from non-evaporated water and identify recharge source elevation and season; tritium dates water at the decadal scale; ¹⁴C dates it at the 10³–10⁴ year scale; ³⁶Cl and ⁴He extend to 10⁵–10⁶ years. Applied tracers (deuterated water injected in a profile and tracked as a peak shift) give an event-scale recharge measurement. Radiocarbon age was one of the three calibration targets in the KOH-2 groundwater model.

**Lysimeters and soil-water balance.** Direct, physically unambiguous, and almost never representative — a 1 m² lysimeter cannot sample focused recharge, and installation disturbs the profile.

**Numerical modelling and inverse estimation.** Calibrate a groundwater model against heads, gradients and ages; recharge emerges as the parameter that makes the system work. Wallner et al. (2017) did exactly this for KOH-2 with a heuristic set of 143 physically plausible boundary conditions, achieving an RMSE of 0.82 m on groundwater levels and concluding recharge is <1% of MAP. The weakness is equifinality: recharge and transmissivity trade off against each other, so the inverse problem is under-determined unless ages or fluxes constrain it.

**GRACE / GRACE-FO satellite gravimetry** gives total water-storage change at ~150,000 km² and monthly resolution — too coarse for a wellfield but the right scale for a basin, and the Cuvelai team used it to cross-check point recharge estimates against basin storage change.

## 6. Palaeowater and fossil aquifers

Large volumes of dryland groundwater were recharged under wetter Pleistocene or early Holocene climates and receive negligible modern replenishment: the Nubian Sandstone Aquifer System, the North-Western Sahara Aquifer System, parts of the Great Artesian Basin, and much of the deep Kalahari.

The distinction that matters for management is **fossil** (no modern recharge — any abstraction is mining, with a finite life) versus **semi-fossil** (very slow modern recharge — a small sustainable yield exists on top of a large non-renewable store). Getting this wrong is the central error in dryland groundwater development, because storage volume is large and seductive while sustainable yield is small and unglamorous.

The Ohangwena II (KOH-2) case is the model answer: the aquifer is **not** fossil — recharge is active from the foothills of the Angolan highlands — but recharge is less than 1% of mean annual precipitation, yielding only a few million cubic metres per year across the whole system, and *that* is the maximum sustainable yield. The authors state plainly that the aquifer could sustainably supply local drinking water if managed carefully, but that using it for large-scale irrigation or a long-distance transfer to Windhoek "should be considered with a great deal of scepticism". Groundwater residence times in the slow eastern part of the system may be 100,000 years or more.

## 7. Endorheic basins and pans

An endorheic basin has no outlet to the sea; water leaves only as evaporation or deep seepage. The Cuvelai-Etosha Basin is exactly this: a sedimentary, intracontinental endorheic basin whose lowest point is the Etosha Pan and its salt lakes. Other examples: the Okavango Delta, Lake Chad, the Aral basin, the Great Basin, the Chott systems of North Africa.

Hydrological consequences:
- Salts accumulate. There is no export path, so the terminal sink becomes a saline pan and the groundwater grades from fresh at the margins to brine near the centre.
- Water levels are extremely sensitive to inflow, because area–volume relationships in a flat pan are very shallow: a small depth change floods or exposes an enormous area.
- Pans are focused recharge sites *and* focused evaporation sites simultaneously; which dominates depends on the clay content of the floor. Calcrete- and sand-floored depressions recharge; clay-floored pans evaporate.
- Remote sensing (Sentinel-1 SAR, MODIS, Landsat) is the practical way to map inundation extent, because the ground is flat, roadless and seasonally impassable.

## 8. Ephemeral rivers — the Namibian systems

Namibia is the type locality for ephemeral river hydrology. Apart from the perennial border rivers, essentially every Namibian river is ephemeral, flowing for days to a few weeks per year, and many in only some years.

**The westward-flowing systems** rise on the interior escarpment and cross the Namib to the Atlantic — few of them reaching it in most years. From south to north the major ones include the **Koichab**, **Tsauchab** (endorheic, terminating at Sossusvlei in the dunes), **Tsondab** (also endorheic), **Kuiseb**, **Swakop**, **Omaruru**, **Ugab**, **Huab**, **Uniab**, **Hoanib**, **Hoarusib** and **Khumib**. The **Fish River** drains south to the Orange. In the Kalahari east, the **Nossob** and **Auob** drain south-east toward the Molopo and effectively never reach it.

Their hydrology:
- **Flow is event-driven and brief.** A flood at Gobabeb on the Kuiseb may last days; some years there is no flow at all. Downstream reaches only flow when the upstream event is large enough to overcome cumulative transmission losses.
- **The alluvial aquifer is the resource.** Sand-filled channels store water that is protected from evaporation below about 1–2 m depth, is recharged by each flood, and supports riparian woodland (*Faidherbia albida*, *Acacia erioloba*, *Ficus sycomorus*) and the wildlife and settlements along the "linear oases".
- **The Kuiseb** is the best-studied: it sets the northern boundary of the Namib Sand Sea, its delta aquifer supplies Walvis Bay and Swakopmund, and it has been mapped with ALOS-2 and Sentinel-1 radar to reveal a buried palaeo-channel system beneath the dunes. Sentinel-1 backscatter and interferometry now detect flow events and vegetation response without any ground station.
- **They are ecologically disproportionate.** A few percent of the land area carries most of the biological productivity of the western Namib.
- **They are legally and institutionally awkward.** Basin management committees for ephemeral rivers (the Kuiseb committee is the pioneering Namibian example) have to allocate a resource that is absent most of the time.

In the north, the **Cuvelai** system is a different animal again — not a single channel but a braided network of shallow, grassy, interlinked channels (**iishana**, singular *oshana*) that only becomes a connected drainage during large floods. It is covered in `04`.

## 9. Flash floods and the forecasting problem

Flash flooding is the dominant flood hazard in steep dryland catchments, and it is the hardest thing in operational hydrology to forecast.

- **Lead times are minutes to a couple of hours** because the causative rainfall is convective and the catchment response time is short. There is no useful "rain now, flood tomorrow" window.
- **The rainfall is the unknown.** Rain gauges miss storm cores; radar coverage in most of Africa is absent or unmaintained; satellite QPE (IMERG) has ~30 min latency and coarse resolution.
- **Antecedent conditions matter less** than in humid catchments (infiltration-excess dominates), which is one small simplification — but surface crusting and sealing after a dry spell can *increase* runoff, inverting the usual intuition.
- **Rating curves are unreliable** because channels scour and fill during the event; the cross-section at the peak is not the one you surveyed.
- **Practical approach**: flash-flood guidance (a threshold rainfall depth-duration that would produce bankfull flow), nowcasting from satellite cloud-top temperatures, and — increasingly — machine-learning forecasts (see `10`). For a homestead, the operational answer is not forecasting but freeboard: build above the flood level and accept that you will not get a warning.

The flat Cuvelai is the opposite case: floods there are slow, broad and arrive over days to weeks, so warning *is* feasible, and satellite-based flood mapping and upstream gauge readings from Angola give genuine lead time.

## 10. Dune and sand-sea hydrology

Deep aeolian sand behaves very differently from a soil profile:
- Very high infiltration capacity means Hortonian runoff is essentially absent on dunes; almost all rain infiltrates.
- But almost all of it is then returned by evaporation from the upper metre unless an event is large.
- Once below the evaporation zone, water in dune sand is well protected; dune fields can be significant recharge areas, and the Stampriet aquifer beneath the Kalahari dunefield is recharged this way.
- Interdune corridors and slacks concentrate flow and are preferential recharge sites.
- Sand is also a *store*: the water content of a deep unsaturated sand column is small per metre but large in total, and travel times from surface to water table can be decades to millennia, meaning today's recharge signal reflects a wetter past.

## 11. Fog as a water source

Along the Namib coast, advective fog driven by the cold Benguela Current is a real and ecologically decisive water input — the classic case in dryland hydrology. Fog supports lichen fields, *Welwitschia*, and the fog-basking beetles whose shell microstructure has been copied in fog-harvesting materials research.

For water supply, honest limits apply: fog collection works only where fog is frequent and wind carries it through a mesh — a narrow coastal belt, on ridges, typically within tens of kilometres of the coast. Standard large fog collectors are ~40 m² of double-layer Raschel mesh. Yields are highly site-specific and seasonal. **Okongo is roughly 900 km inland and fog collection is not a water option there** — it belongs in this file as dryland process hydrology, not as a supply technology for the Cuvelai.

## 12. Salinity and evaporative concentration

Where the water table is within the capillary reach of the surface (typically <2–3 m in fine sediment), evaporation draws water up and leaves salt behind. Over centuries this produces the saline shallow groundwater and salt-crusted pans characteristic of dryland closed basins.

The Cuvelai shows the gradient starkly: shallow groundwater in the eastern (Ohangwena) part of the basin runs 50–1,200 µS/cm and is broadly drinkable, while 100 km west in Omusati the same shallow aquifers run 140–11,450 µS/cm, show a clear dry-season salinity increase, are dominated by Ca–SO₄ chemistry, and roughly 70% of sampled hand-dug wells are unfit for human consumption on sulphate alone, with additional exceedances for chloride (12%), fluoride (19%) and manganese (13%).

Two operational corollaries:
- **Salinity is a spatial and a seasonal variable.** Sample at the end of the dry season, not after rain, if you want the worst case.
- **Irrigation with marginal water accelerates the problem**, because irrigation is itself an evaporative concentrator. Leaching fractions and drainage are not optional in dryland irrigation.

## 13. Groundwater-dependent ecosystems

In drylands, a disproportionate share of biodiversity depends on groundwater or on the shallow alluvial store: riparian woodland along ephemeral rivers, springs and seeps, pan-fringe vegetation, and phreatophytes whose roots reach 20–50 m. Abstraction that lowers the water table by a few metres can kill a woodland that took two centuries to establish, with no visible effect on the borehole's yield. Environmental water requirements for groundwater are far less developed than for rivers, and in practice the protection mechanism is a drawdown limit rather than an ecological flow.

## 14. Why temperate models fail — a checklist

When importing any model or method into a dryland, interrogate it against this list:

1. Does it assume saturation-excess runoff generation? (Curve number, TOPMODEL, VIC in default configuration — yes.)
2. Does it conserve discharge along a channel? (Most routing schemes — yes. Wrong.)
3. Does it apply recharge as a uniform fraction of rainfall? (Most regional groundwater models — yes. Wrong.)
4. Does it use daily rainfall as the input time step? (Then it cannot represent intensity-driven infiltration excess; sub-hourly data are needed.)
5. Does its calibration objective function (NSE) reward high flows only, in a series that is mostly zeros?
6. Does it assume the phreatic surface is a subdued replica of topography? (True in humid terrain; frequently false in drylands with deep water tables and disconnected streams.)
7. Does it treat evaporation as a residual or a minor term?
8. Does it assume a stationary climate and a record long enough to characterise it?

If the answer to several of these is yes, either reconfigure the model explicitly for arid conditions or use a simpler water-balance approach whose assumptions you can see.

## Sources

- Himmelsbach, T. et al. (2018) [*Deep, semi-fossil aquifers in southern Africa*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00306), Biodiversity & Ecology 6: 66–74, doi:10.7809/b-e.00306.
- Wanke, H. et al. (2018) [*The long road to sustainability*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307), Biodiversity & Ecology 6: 75–83, doi:10.7809/b-e.00307.
- Hamutoko, J.T. et al. (2018) [*Spatio-temporal variations of hydrochemical and isotopic patterns of groundwater in hand-dug wells*](https://piahs.copernicus.org/articles/378/29/2018/), Proc. IAHS 378: 29–34.
- Persendt, F.C., Gomez, C. & Zawar-Reza, P. (2015) [*Identifying hydro-meteorological events from precipitation extremes indices over northern Namibia, Cuvelai Basin*](https://jamba.org.za/index.php/jamba/article/view/177), Jàmbá 7(1), doi:10.4102/jamba.v7i1.177.
- Stone, A. & Edmunds, W.M. (2012) *Sand, salt and water in the Stampriet Basin, Namibia: chloride mass balance*, Water SA 38(3), [doi:10.4314/wsa.v38i3.2](https://doi.org/10.4314/wsa.v38i3.2).
- Normandin, C., Paillou, P., Lopez, S. et al. (2022) [*Monitoring the Dynamics of Ephemeral Rivers from Space: the Kuiseb, Namibia*](https://doi.org/10.3390/w14193142), Water 14:3142.
- Paillou, P. et al. (2020) [*Mapping Paleohydrology of the Ephemeral Kuiseb River from Radar Remote Sensing*](https://doi.org/10.3390/w12051441), Water 12:1441.
- Koeniger, P. et al. (2020) *Evaporation loss along the Calueque-Oshakati Canal*, Isotopes in Environmental and Health Studies, doi:10.1080/10256016.2020.1830082.
- [NASA POWER](https://power.larc.nasa.gov/) monthly and climatology data for 17.566°S 17.216°E, accessed 2026-08-25.

## Open questions

- The list of Namibian westward-flowing ephemeral rivers is compiled from general knowledge and has **not** been checked against a Namibian hydrological authority list; the set of rivers is confident, the completeness is `needs-verification`.
- Typical transmission-loss percentages (10–50% per 10–20 km) are indicative ranges from the general literature, not a Namibian measurement — no site-specific Namibian transmission-loss figure was verified in this pass.
- Namib fog deposition rates and fog-collector yields were not verified to a primary source and are deliberately not quantified above.

