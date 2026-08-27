---
id: hydrology.instrumentation
title: Hydrological measurement and instrumentation
domain: 24_hydrology_arid
tags: [rain-gauge, evaporation-pan, eddy-covariance, streamgauging, adcp, weir, flume, rating-curve, dilution-gauging, pressure-transducer, barometric-compensation, tdr, fdr, neutron-probe, cosmic-ray, water-quality-sonde, isotopes, geophysics, telemetry]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "OTT HydroMet", url: "https://www.otthydromet.com/", publisher: "OTT HydroMet", accessed: 2026-08-25}
  - {title: "Campbell Scientific data loggers", url: "https://www.campbellsci.com/data-loggers", publisher: "Campbell Scientific", accessed: 2026-08-25}
  - {title: "Campbell Scientific soil moisture sensors", url: "https://www.campbellsci.com/soil-moisture-sensors", publisher: "Campbell Scientific", accessed: 2026-08-25}
  - {title: "Van Essen Instruments Diver product range", url: "https://www.vanessen.com/", publisher: "Van Essen Instruments", accessed: 2026-08-25}
  - {title: "Solinst 3001 Levelogger series", url: "https://www.solinst.com/instruments/dataloggers-and-telemetry-systems/3001-levelogger/", publisher: "Solinst", accessed: 2026-08-25}
  - {title: "The long road to sustainability: Cuvelai-Etosha Basin (Wanke et al. 2018)", url: "https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307", publisher: "Biodiversity & Ecology 6", accessed: 2026-08-25}
  - {title: "FAO Irrigation and Drainage Paper 56", url: "https://www.fao.org/4/x0490e/x0490e00.htm", publisher: "FAO", accessed: 2026-08-25}
related: [hydrology.equipment, hydrology.arid_zone, hydrology.tech_trends]
unit_system: SI
---

# Hydrological measurement and instrumentation

**Summary.** How hydrological data actually get collected, what each instrument's real error sources are, and what changes in a dryland. The recurring lesson is that the instrument is the easy part: siting, calibration, maintenance and metadata determine whether a record is worth anything. In arid regions the additional problems are heat, dust, UV, livestock, theft, and the fact that the most important events happen when nobody is there.

## Key facts

| Measurement | Typical instrument | Typical achievable accuracy | Main dryland failure mode |
|---|---|---|---|
| Rainfall | Tipping bucket, 0.2 mm | ±3–5% (worse at high intensity) | Under-reads intense convective bursts; blocked by dust, insects, bird nests |
| Evaporation | Class A pan | ±10% | Animals drinking; pan dries out completely |
| Water level (borehole) | Vented or non-vented pressure transducer | ±0.05% FS | Barometric error if uncompensated; cable theft |
| Streamflow | ADCP, current meter, weir/flume | ±5% (good conditions) | Channel scours and fills during the event |
| Soil moisture | TDR / FDR / CRNS | ±0.02–0.03 m³/m³ | Needs soil-specific calibration in sand |
| Water quality | Multiparameter sonde | varies by parameter | Fouling, drift, calibration in extreme heat |

## 1. Rain gauges

**Tipping bucket** — the workhorse. A funnel of known orifice (typically 200 mm or 400 cm² collecting area) feeds a pivoting twin-bucket; each tip is a fixed depth (0.1, 0.2 or 0.5 mm) recorded as a pulse. Errors:
- **Under-catch at high intensity** — water continues to enter during the tip, so the gauge reads low. This is a systematic, intensity-dependent error of 5–15% at intensities above ~50 mm/h, and it is worst exactly when the data matter (design storms, flash floods). **Dynamic calibration** — pumping known flow rates through the gauge across the intensity range — is the fix, and is very rarely done.
- **Wind-induced under-catch** — the gauge orifice disturbs the airflow and deflects droplets. 3–10% for rain in moderate wind. Mitigation: a wind shield, siting away from turbulence, or setting the orifice at ground level in a pit with an anti-splash grid (the reference configuration).
- **Evaporation and wetting losses** — the residual water in the funnel and buckets between events evaporates. In hot, dry conditions a small event can be entirely lost. This is a real bias in drylands.
- **Blockage** — dust, insects, spider webs, bird droppings. In the Cuvelai, seasonal termite alate flights and dust will block an unmaintained gauge. Fit a mesh, inspect monthly.

**Weighing gauge** — a load cell weighs the accumulating catch; records intensity continuously, works with snow, and does not suffer the tipping under-catch. More expensive, and needs careful thermal and wind compensation. The OTT Pluvio² is the standard research-grade instrument.

**Optical / disdrometer** — measures droplet size distribution and derives rate, with no moving parts and no orifice. Useful for intensity and for radar calibration; less accurate for total depth.

**Manual standard gauge** — a simple graduated cylinder read daily. Do not dismiss it: a manual gauge read reliably every day at 08:00 is a better record than an automatic gauge nobody services. Almost every long rainfall record in southern Africa is manual.

**Siting rules**: level orifice, above ground splash height (usually 0.3–1.2 m depending on standard), clear of obstructions by at least twice their height, not on a roof, secure from livestock and theft, with the height and any relocation recorded in the metadata.

## 2. Evaporation measurement

**Class A pan** — 1.21 m diameter, 255 mm deep, galvanised or stainless, on a slatted timber platform, water kept 50–75 mm below the rim; daily change in level measured in a stilling well with a hook gauge, corrected for rainfall. Convert to reference ET with a pan coefficient `Kp` (0.55–0.85; see `02`). Errors: heat exchange through the pan walls, birds and animals drinking, and — in the dry season in Namibia — the pan simply running dry between readings.

**Eddy covariance** — measures the actual turbulent flux of water vapour by fast (10–20 Hz) simultaneous sampling of vertical wind speed (sonic anemometer) and water-vapour density (infrared gas analyser), giving `LE = λ·ρ·w'q'`. The reference method for actual ET over a footprint of hundreds of metres. Expensive, power-hungry, needs skilled processing (coordinate rotation, spectral corrections, gap filling), and suffers the well-known **energy-balance closure** problem (typically 10–30% short). In drylands the additional problem is advection: hot dry air blowing over a small irrigated or riparian patch produces ET above net radiation, which the standard assumptions do not allow for.

**Bowen ratio energy balance** and **scintillometry** are the intermediate options. **Lysimeters** (weighing or drainage) give a direct point measurement and remain the calibration standard.

## 3. Streamflow gauging

**Velocity–area method.** Divide the section into panels, measure depth and mean velocity in each, sum `Σ(v_i · a_i)`. Mean velocity in a vertical is taken at 0.6 × depth from the surface, or the average of readings at 0.2 and 0.8 for deeper sections.

- **Mechanical current meters** (Price AA, pygmy, Ott C31/C2) — rotating cup or propeller, calibrated rating `v = a·N + b`. Robust, cheap, still standard for wading measurements.
- **Electromagnetic current meters** — no moving parts, good in weedy or debris-laden water.
- **ADCP (acoustic Doppler current profiler)** — measures a velocity profile across the section from a boat, tethered float or from the bank (side-looking). The modern standard for anything not waddable; a full discharge measurement in minutes. Bottom-tracking fails over a moving sand bed — a real problem in Namibian sand-bed channels, where you must use a GPS reference instead.
- **Acoustic Doppler velocimeter (ADV)** — point measurement, high frequency, used for research and for shallow flows.

**Weirs and flumes** — a fixed structure with a known head–discharge relationship.
- Thin-plate V-notch (90°): `Q = 1.38·H^2.5` (m³/s, H in m) — excellent for small, low flows.
- Rectangular sharp-crested (Kindsvater-Carter form): `Q = C_d · (2/3)·√(2g) · b_e · h_e^1.5`.
- Broad-crested weirs and **Parshall / cut-throat flumes** pass sediment far better than sharp-crested weirs, which matters enormously in a sandy ephemeral channel where a V-notch will silt up in one event.

**Stage–discharge rating curves.** Measure stage continuously and discharge occasionally, then fit `Q = a(h − h₀)^b`. The practical difficulties in drylands are severe: few opportunities to gauge (flow lasts days), high flows almost never measured directly (so the curve is extrapolated exactly where design depends on it), and **unstable control** — a sand-bed channel scours during the rising limb and fills on the falling limb, so a single-valued rating is fiction. Hysteresis loops and shifting controls are the norm. Document every rating shift with a date.

**Dilution gauging** — inject a tracer (salt, or Rhodamine WT for fluorometry) and measure downstream concentration. Two variants: constant-rate injection (`Q = q·(C₁ − C₂)/(C₂ − C₀)`) and slug injection (integrating the concentration–time curve, `Q = M / ∫C dt`). Ideal for turbulent, rocky, steep channels where velocity–area fails, and for very small flows. In a sandy channel, tracer losses to the bed break the mass-balance assumption; use with care and check recovery.

## 4. Water level

- **Vented (gauge-pressure) transducer** — a capillary tube in the cable vents the sensor to atmosphere, so the reading is water depth directly. No barometric correction needed. The vent tube must be kept dry: fit a desiccant cartridge and change it, or condensation will ruin the record. Solinst LevelVent/AquaVent and In-Situ vented Level TROLLs are of this type.
- **Non-vented (absolute) transducer** — measures total pressure; you must subtract barometric pressure recorded by a separate barometric logger at the site (Solinst Barologger, Van Essen Baro-Diver, In-Situ BaroTROLL). **This is the single most common source of error in groundwater level records.** A 1 hPa barometric change is ~1 cm of water; daily barometric swings of 5–10 hPa are routine, and a synoptic passage can be 20 hPa. One barologger per site (within ~30 km and 300 m elevation) covers all loggers at that site.
- **Radar / non-contact level** — sits above the water, no fouling, no maintenance in the water column, and survives floods that would destroy a submerged sensor. The right choice for an ephemeral river where the sensor would otherwise be buried in sand or washed away.
- **Bubbler** — a small compressor forces air down a tube; back-pressure equals water depth. Robust in sediment-laden water; the orifice can block.
- **Float and counterweight in a stilling well** — the classical mechanical gauge, still the reference in many networks; needs a well that does not silt up.
- **Staff gauge** — a painted board. **Always install one**, whatever else you fit. It is the independent check on every automatic record, and it is what a passer-by can read and photograph.

## 5. Groundwater monitoring

- **Dip meter / water level meter** — a graduated tape with a probe that beeps at the water surface. The fundamental manual measurement. Accuracy depends on the tape being kept clean and on measuring from a marked, surveyed datum point on the casing. Mark that datum and record its elevation.
- **Interface meter** — distinguishes a floating hydrocarbon layer from water; needed on contaminated sites.
- **Automatic loggers in boreholes** — the SASSCAL Cuvelai programme equipped six shallow Ohangwena boreholes (10–31 m deep) with **Solinst Leveloggers** recording daily through the 2016/17 season, and this is exactly the right pattern for a homestead: one logger, one barologger, one manual dip per visit for verification.
- **Barometric compensation** — see above. Also correct for **loading efficiency** in confined aquifers, where a barometric change is partly borne by the aquifer skeleton; the borehole water level responds by only a fraction of the barometric change. Regress water level against barometric pressure to obtain the barometric efficiency before applying a correction.
- **Deployment practicalities**: hang the logger on stainless wire or Kevlar cord (not nylon, which creeps), well below the lowest expected water level and above the pump intake; record the exact hang depth; retrieve and download at a fixed interval; and never leave a logger's only copy of the data in the logger.

## 6. Soil moisture

| Method | Principle | Accuracy | Notes |
|---|---|---|---|
| **Gravimetric** | Oven-dry a sample at 105 °C | reference | Destructive; the calibration standard for everything else |
| **TDR (time domain reflectometry)** | Travel time of an EM pulse along waveguides → dielectric permittivity → θ via Topp's equation | ±0.02 m³/m³ | Least soil-specific of the electromagnetic methods; Campbell TDR200 with CS6xx probes |
| **FDR / capacitance** | Resonant frequency of a capacitor formed with the soil | ±0.03 m³/m³ after calibration | Cheaper; **needs soil-specific calibration**, and is sensitive to bulk EC — a real issue in saline dryland soils |
| **Neutron probe** | Fast neutrons thermalised by hydrogen | ±0.01 m³/m³ | Excellent depth profiles through an access tube; but a radioactive source, with licensing, transport and personnel constraints that have made it rare |
| **Cosmic-ray neutron sensing (CRNS)** | Ambient fast-neutron count is inversely related to hydrogen in the footprint | ±0.03 m³/m³ | **Footprint of ~200–250 m radius and ~15–70 cm depth** — the only method that measures at the scale models actually need. See `10` |
| **Heat pulse / thermal** | Heat dissipation vs water content | moderate | Also gives matric potential with the right probe |
| **Tensiometers / matric potential sensors** | Direct suction measurement | — | Measure *potential*, not content — what plants and Richards' equation actually respond to. Conventional tensiometers only work to about −80 kPa, far too wet for dryland use; use gypsum blocks, heat-dissipation or MPS-type sensors for the dry range |

**Topp's equation** (mineral soils): `θ = −5.3×10⁻² + 2.92×10⁻²·εr − 5.5×10⁻⁴·εr² + 4.3×10⁻⁶·εr³`. It works well for loams and adequately for clean sand, but in soils with high EC or high organic content, calibrate.

## 7. Water quality sondes

A multiparameter sonde carries some combination of: temperature, pressure/depth, electrical conductivity, pH, ORP, dissolved oxygen (optical/luminescent is now standard and far more stable than membrane), turbidity (nephelometric, 90° scatter), chlorophyll-a and blue-green algae fluorescence, ammonium/nitrate ion-selective electrodes, and rhodamine for tracer work.

Practical realities:
- **Calibrate before every deployment and check after.** Report the post-deployment drift — a record without a drift check is uninterpretable.
- **Fouling** is the limiting factor for long deployments. Central wipers, copper anti-fouling guards and shorter service intervals are the countermeasures.
- **ISE sensors (nitrate, ammonium) drift fast** and are screening tools, not analytical ones.
- **Turbidity units matter.** NTU (nephelometric, white light, EPA 180.1), FNU (860 nm, ISO 7027) and FAU (attenuation) are different measurements; the Cuvelai surface-water study reported FAU, and those numbers are not interchangeable with NTU.
- **Temperature compensation** for EC is to 25 °C by convention; check the compensation coefficient used, because in a dryland with 30 °C diurnal swings it materially changes reported values.

## 8. Isotopes and tracers

- **Stable water isotopes δ¹⁸O and δ²H** — the workhorses of dryland hydrology. Plotted in dual-isotope space against the Local Meteoric Water Line, they distinguish evaporated from unevaporated water, identify recharge season and source elevation, and quantify mixing. Field sampling is simple: a full, unheadspaced glass vial with a tight cap, kept cool. Analysis by laser spectroscopy (Picarro, LGR) is now cheap enough to run hundreds of samples.
- **Deuterium as an applied tracer** — inject ²H₂O into a soil profile and track the downward displacement of the peak over a season to get a direct recharge estimate. Used in the Cuvelai SASSCAL programme.
- **Tritium (³H)** — dates water on a decadal scale; the bomb peak is now largely decayed but ³H/³He dating still works.
- **Radiocarbon (¹⁴C)** on dissolved inorganic carbon — the 10³–10⁴ year dating tool, and one of the three constraints used in the Ohangwena II flow model. Requires correction for carbonate dissolution (Pearson, Fontes-Garnier or geochemical modelling); uncorrected ¹⁴C ages are systematically too old.
- **CFCs and SF₆** — date water recharged since roughly 1950.
- **Chloride** — the conservative tracer behind the chloride mass balance method (see `03`).
- **Fluorescent dyes** (uranine, Rhodamine WT) for connection tests and dilution gauging; note that uranine degrades in sunlight and sorbs to organic matter.

## 9. Geophysical surveying

Covered from the siting perspective in `05`. From the instrumentation perspective:
- **Resistivity / IP** — a multi-electrode cable system with a switching resistivity meter (ABEM Terrameter LS 2, IRIS Syscal Pro), inverted with RES2DINV or equivalent. Wenner, Schlumberger, dipole-dipole and gradient arrays trade depth, resolution and speed.
- **TEM/TDEM** — a transmitter loop and a receiver coil measuring the decay of the secondary field (ABEM WalkTEM 2, GroundTEM). Depth of investigation of 100–300 m with a modest loop, and excellent at resolving conductive (saline) layers — the right tool for the Cuvelai's fresh/brackish structure.
- **Magnetics** — proton precession or optically-pumped caesium magnetometers (Geometrics G-859, MagArrow for drone deployment) for dyke and basement mapping.
- **Seismic refraction** — a seismograph (Geometrics Geode) with a geophone spread and a sledgehammer or weight-drop source.
- **Borehole geophysics** — natural gamma (clay content), electrical resistivity/induction (formation and water salinity), caliper, temperature and fluid conductivity, and flowmeter logs. A gamma log in a Cuvelai borehole resolves the sand/clay sequence far better than the driller's cuttings description.
- **GPR** — 100–500 MHz antennas for shallow stratigraphy; penetration in dry clean sand can be 10–15 m, but collapses to under a metre in clay.

## 10. Telemetry and data logging

- **Loggers**: Campbell Scientific CR300/CR310/CR350 and CR1000X-series for full weather and hydrology stations; OTT and Sutron loggers in hydrometric networks; standalone loggers (Solinst, Van Essen) for boreholes.
- **Sensor interfaces**: SDI-12 is the dominant standard for smart environmental sensors (a single 3-wire bus, addressable, low power); Modbus RTU over RS-485 for industrial devices; analogue 4–20 mA and pulse counting for legacy sensors.
- **Communications**: GSM/GPRS/LTE-M and NB-IoT where there is coverage (Okongo has mobile coverage); satellite (Iridium SBD, or GOES/Meteosat DCP in official networks) where there is not; LoRaWAN for local sensor clusters back to a single gateway with a wider-area uplink.
- **Power**: a small PV panel and a sealed lead-acid or LiFePO₄ battery. Size for the worst month — for Okongo that is June (18.6 MJ m⁻² day⁻¹ vs 24.7 in October, from NASA POWER) — plus five days of autonomy. Overheating kills batteries faster than cold; put the enclosure in shade and ventilate it.
- **Data management discipline** (the part that actually determines whether the record survives):
  1. Local logging **and** telemetry — never telemetry alone.
  2. Automated backup off the logger on every visit.
  3. A **station metadata file**: coordinates, datum, sensor serial numbers, install heights, every calibration, every service visit, every relocation.
  4. **Quality flags** on every value, not corrections applied silently.
  5. Regular manual check readings (staff gauge, dip meter, manual rain gauge) as the independent reference.

## 11. What actually fails in the field, in a dryland

- Dust in and on everything; solar panels lose output rapidly without cleaning.
- UV degrades cable insulation, cable ties, enclosures and pipe within a couple of seasons unless UV-stabilised.
- Heat: enclosure interiors reach 60–70 °C in the sun, above the rated range of many loggers and batteries.
- Livestock rub on, chew and knock over anything at animal height; termites eat cable insulation and wooden posts.
- Theft of solar panels, batteries and copper cable is the leading cause of station loss in southern African networks. Design for it: caged panels, in-ground anchors, minimal visible copper, and a community relationship with the nearest homestead.
- The event you most need to measure will happen during the one week you cannot reach the site because the road is under water.

## Sources

- [OTT HydroMet](https://www.otthydromet.com/) — Pluvio² weighing gauge and hydrometric instrumentation.
- [Campbell Scientific data loggers](https://www.campbellsci.com/data-loggers) — CR310, CR350, CR1000Xe verified on the current product listing; [soil moisture sensors](https://www.campbellsci.com/soil-moisture-sensors) — CS616, CS650, CS655, TDR200 verified.
- [Van Essen Instruments](https://www.vanessen.com/) — TD-Diver, Baro-Diver, Cera-Diver, CTD-Diver, Micro-Diver product pages verified in the site sitemap.
- [Solinst 3001 Levelogger series](https://www.solinst.com/instruments/dataloggers-and-telemetry-systems/3001-levelogger/).
- Wanke, H. et al. (2018) [*The long road to sustainability*](https://www.biodiversity-plants.de/biodivers_ecol/article_meta.php?DOI=10.7809/b-e.00307) — the Ohangwena shallow-borehole Levelogger monitoring design and the use of Hach portable field instruments and FAU turbidity units.
- [FAO Irrigation and Drainage Paper 56](https://www.fao.org/4/x0490e/x0490e00.htm) — Class A pan configuration and pan coefficients.

## Open questions

- Instrument accuracy figures in the Key facts table are typical manufacturer/practice values, not extracted from specific datasheets — `needs-verification` against the datasheet of any instrument you actually buy.
- V-notch and rectangular weir coefficients quoted are standard forms; check against ISO 1438 before building a structure.
- Topp's equation coefficients are quoted from memory of the standard formulation and should be checked against Topp, Davis & Annan (1980) before use in analysis.
