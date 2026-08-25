---
id: aviation_weather.nwp
title: How the forecast is made — observations, NWP, ensembles and machine learning
domain: 32_aviation_weather
tags: [nwp, data-assimilation, ecmwf, ifs, gfs, icon, unified-model, arpege, harmonie, ensemble, eps, predictability, forecast-skill, nowcasting, graphcast, pangu-weather, fourcastnet, aifs, gencast, taf-production]
jurisdiction: global
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Changes to the ECMWF forecasting system", url: "https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model", publisher: "ECMWF", accessed: 2026-08-25}
  - {title: "ECMWF's AI forecasts become operational", url: "https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational", publisher: "ECMWF", accessed: 2026-08-25}
  - {title: "GenCast predicts weather and the risks of extreme conditions with SOTA accuracy", url: "https://deepmind.google/discover/blog/gencast-predicts-weather-and-the-risks-of-extreme-conditions-with-sota-accuracy/", publisher: "Google DeepMind", accessed: 2026-08-25}
  - {title: "Aviation Weather Center — GFA help / product list", url: "https://aviationweather.gov/gfa/help", publisher: "NOAA/NWS Aviation Weather Center", accessed: 2026-08-25}
  - {title: "Clear-air turbulence", url: "https://en.wikipedia.org/wiki/Clear-air_turbulence", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aviation_weather.products, aviation_weather.operations, aviation_weather.study]
unit_system: SI
---

# How the forecast is made — observations, NWP, ensembles and machine learning

**Summary.** A TAF is the last two per cent of a chain that begins with a few million observations and passes through a set of partial differential equations integrated on a rotating sphere. Knowing where in that chain the uncertainty enters tells you which parts of a forecast to believe. This file covers the observing system, data assimilation, the operational global and regional models with their real resolutions, ensembles and probabilistic products, what a model can and cannot resolve, forecast skill and the predictability limit, nowcasting, and the machine-learning models that have — genuinely, and within the last three years — changed the field. It closes with how a human forecaster actually builds a TAF.

## Key facts

| Item | Value |
|---|---|
| ECMWF IFS Cycle 48r1 | **27 June 2023** — unified medium-range resolutions |
| ECMWF IFS Cycle 49r1 | **12 November 2024** — improved wind and temperature |
| ECMWF IFS Cycle 50r1 | **12 May 2026** — major update to both IFS and AIFS |
| ECMWF **AIFS Single v1** operational | **25 February 2025**, grid spacing **28 km**, gains **up to 20 %** on some measures including tropical cyclone tracks |
| ECMWF AIFS **ensemble** operational | **July 2025** |
| **GenCast** (Google DeepMind) | Published **4 December 2024** in *Nature*; **0.25°**, **≥50-member** ensemble, **15-day** lead; diffusion model on a spherical geometry; more accurate than ECMWF ENS on **97.2 %** of tested targets and **99.8 %** beyond 36 h lead; a full 15-day forecast in **8 minutes on one TPU v5** |
| Deterministic predictability limit | ~**2 weeks** for synoptic scales; ~**hours** for individual convective cells |
| CAT climate trend | transatlantic winter CAT **+60 % light / +95 % moderate / +150 % severe** at CO₂ doubling |

> ⚠️ This file is `draft`/`confidence: medium` because the machine-learning section is a fast-moving area and several model specifications below could not be verified from a primary source in this session. Every unverified item is flagged inline and listed in `## Open questions`.

## 1. The observing system

Numerical weather prediction is an initial-value problem. Its accuracy is bounded by how well you know the current state.

### 1.1 Conventional in-situ

- **Surface synoptic stations** — pressure, temperature, humidity, wind, precipitation. Roughly 10 000 land stations reporting at least 3-hourly. The pressure observations matter far more than their number suggests, because surface pressure constrains the whole column mass.
- **Radiosondes** — the only routine direct measurement of the vertical profile of temperature, humidity and wind. Roughly 800 stations globally, launched at **0000 and 1200 UTC** with a smaller set at 0600/1800. Coverage is dense over Europe, North America, China and Japan; sparse over Africa, South America, the Southern Ocean and much of the Middle East. That asymmetry is directly visible in forecast skill.
- **Ships and drifting/moored buoys** — VOS reports and the global drifter array; the only in-situ surface data over most of the ocean.
- **Aircraft (AMDAR/ADS-C/Mode-S EHS)** — pressure altitude, temperature and wind derived from the aircraft's own systems, downlinked automatically. By observation count this is now the **largest single source of upper-air data**, and the ascent/descent profiles at busy airports act as high-frequency radiosondes. Some fleets add humidity (WVSS-II) and **EDR turbulence**.
- **Wind profilers and radar wind profilers** — continuous vertical wind profiles at fixed sites.

### 1.2 Remote sensing

- **Geostationary satellites** — Meteosat (MTG), GOES-R series, Himawari, FY-4, INSAT, Elektro-L. Imagery, **atmospheric motion vectors** (winds derived from tracking cloud and water-vapour features), and hyperspectral sounding on the newest platforms.
- **Polar-orbiting satellites** — microwave and infrared **sounders** (AMSU/ATMS, IASI, CrIS, AIRS) that supply the bulk of the *information content* in a modern assimilation. Roughly 80–90 % of the observations assimilated at ECMWF, by count, are satellite radiances.
- **GNSS radio occultation** — GPS/Galileo signals refracted through the limb of the atmosphere give exceptionally accurate, bias-free temperature profiles. Cheap, global, and disproportionately valuable; the commercial smallsat constellations have multiplied the count.
- **Scatterometers** (ASCAT) — ocean surface wind vectors.
- **Doppler wind lidar (Aeolus)** — the first space-based direct wind profile mission, which demonstrated a measurable forecast improvement; a follow-on is planned.
- **Ground-based GNSS** — total column water vapour from signal delay, useful for fog and convection.
- **Weather radar** — reflectivity and radial velocity assimilated directly in convection-permitting models.
- **Lightning networks** — increasingly assimilated as a proxy for convective heating.

### 1.3 The gaps that matter to a Gulf-based long-haul operator

Radiosonde and surface coverage over the Sahara, the Arabian interior, the Sahel, central Africa, the tropical Indian Ocean and the Southern Ocean is thin. That is precisely where the ITCZ, the monsoon onset, dust generation and tropical cyclogenesis live. It is a substantial part of why forecasts of dust events, ITCZ convection and monsoon onset are weaker than forecasts of an Atlantic depression.

## 2. Data assimilation

The analysis is not the observations. It is a **statistically optimal blend** of a short-range forecast (the *background*, typically +6 to +12 h) and the observations, weighted by their respective error covariances. The forecast carries information forward from all previous observations, which is why a model is far better than the observations alone.

- **3D-Var** — minimises a cost function combining background and observation departures at a single analysis time.
- **4D-Var** — does the same over a time window (typically 6–12 h), using the model itself (and its adjoint) to propagate information, so an observation is used at the time it was actually made. Computationally brutal and, for two decades, the reason ECMWF led the field.
- **EnKF / hybrid EnVar** — uses an ensemble to estimate a **flow-dependent** background error covariance, which is much more realistic than a static one. Most centres now run a hybrid: ensemble-derived covariances inside a variational solver.
- **Bias correction** — satellite radiances have instrument and radiative-transfer biases larger than the signal; variational bias correction estimates and removes them inside the analysis.
- **Quality control** — the step that decides which observations to reject. A famous failure mode is rejecting the one correct observation because it disagrees with a wrong background.

Two practical consequences for a pilot:
1. **The analysis is smoothed.** Sharp features — a front, a squall line, a fog edge — are represented more diffusely than reality.
2. **Analysis error is not zero.** The best global analyses have RMS errors of order 0.5 K in temperature and 1–2 m/s in wind in data-rich regions, and considerably more in data-sparse ones. Chaos amplifies those errors.

## 3. The operational models

| Model | Centre | Type | Notes |
|---|---|---|---|
| **IFS** (Integrated Forecasting System) | **ECMWF** | Global spectral, semi-Lagrangian, hybrid EnVar/4D-Var | The reference standard for medium-range skill. Deterministic **HRES** plus the **ENS** ensemble. Cycle 48r1 (27 Jun 2023) unified the medium-range resolutions; 49r1 (12 Nov 2024) improved wind and temperature; **50r1 (12 May 2026)** was a significant update to both IFS and AIFS |
| **GFS** (Global Forecast System) | **NOAA/NCEP** | Global, FV3 dynamical core, hybrid 4DEnVar | Free and open, which is why almost every consumer weather app and many EFB apps use it. Runs 4×/day to 16 days. Paired with **GEFS** ensemble |
| **ICON** | **DWD** (Germany) | Global icosahedral non-hydrostatic, with two-way nests (ICON-EU, ICON-D2) | Excellent and freely available; ICON-D2 is convection-permitting over central Europe |
| **UM** (Unified Model) | **Met Office** (UK) | Global and regional with the same dynamical core; **UKV** at convection-permitting resolution over the UK | Also **WAFC London**'s source model |
| **ARPEGE** / **AROME** | **Météo-France** | Global stretched-grid (higher resolution over France) / convection-permitting regional | AROME is a leading convective-scale model |
| **GEM** | **ECCC** (Canada) | Global and regional | Strong in high-latitude and winter-storm applications |
| **GSM/MSM** | **JMA** (Japan) | Global and mesoscale | Typhoon expertise |
| **HRRR** | **NOAA** | 3 km convection-allowing over CONUS, hourly, with radar assimilation | The US nowcasting workhorse |
| **HARMONIE-AROME** | Nordic/Baltic consortium | Convection-permitting | — |

> ⚠️ **Specific horizontal resolutions and ensemble member counts change with almost every model cycle** and are deliberately not quoted here except where verified. The ECMWF cycle page confirmed the cycle dates above but not the resolutions. `needs-verification`

## 4. Ensembles and probabilistic forecasting

### 4.1 Why

The atmosphere is chaotic: infinitesimal differences in initial state grow. Lorenz's 1963 result means a single deterministic forecast is a sample from a distribution, not the answer. Ensembles sample the distribution.

Two sources of uncertainty are perturbed:
- **Initial condition uncertainty** — via singular vectors (fastest-growing perturbations), ensemble-of-data-assimilations perturbations, or bred vectors.
- **Model uncertainty** — via **stochastic physics** (SPPT — stochastically perturbed parameterisation tendencies; SKEB — stochastic kinetic energy backscatter) or **multi-model/multi-physics** approaches.

### 4.2 Products a pilot might actually see

- **Probability of exceedance** — "probability of visibility below 600 m at 0600 UTC", which is exactly what a `PROB30 TEMPO` line is trying to express.
- **Ensemble mean and spread** — the mean is smoother and usually more skilful in the medium range; the **spread is the forecast of forecast uncertainty**. Large spread = low confidence, and that is a *fuel* decision.
- **Plumes / meteograms** — the ensemble distribution at a point through time; the standard tool for deciding whether a TAF's PROB group is a serious threat.
- **EFI (Extreme Forecast Index)** — how unusual the forecast distribution is relative to the model's own climate. Very useful for flagging "this will be an exceptional wind/rain/heat event".
- **Tropical cyclone track spaghetti and strike probability**.
- **Clustering / weather regimes** — grouping members into scenarios in the medium range.

### 4.3 Reading probability honestly

A well-calibrated 30 % forecast should verify 30 % of the time. Two failure modes to guard against:
- **Under-dispersion** — the ensemble is over-confident, so extreme outcomes occur more often than the ensemble suggests. Historically a systematic problem, improved but not eliminated.
- **Interpreting the ensemble mean as a forecast of the weather** — the mean of two possible fog scenarios is a hazy compromise that will never actually occur.

## 5. Resolution — what a model can and cannot resolve

A model's **effective resolution** is roughly **4–8 times its grid spacing**: features smaller than that are damped by numerical diffusion. So a 9 km global model does not resolve 9 km features; it resolves maybe 40–70 km features.

| Phenomenon | Scale | Resolved by |
|---|---|---|
| Synoptic depression, jet stream, ridge/trough | 1000–4000 km | Any global model, days ahead |
| Front | 50–200 km across | Global model, but the sharpness is underestimated |
| Sea breeze, urban heat island, valley flow | 5–50 km | Regional model at ≤ 4 km |
| MCS | 100–500 km | Global model gets the envelope, not the structure |
| Individual thunderstorm cell | 1–10 km | **Convection-permitting model only** (≤ 3–4 km), and even then only statistically |
| Microburst | ≤ 4 km, minutes | **Not forecastable deterministically**. Only environment-based probability and nowcasting |
| Radiation fog edge, exact onset time | 100s of metres, minutes | Barely; this is why TAF fog groups are probabilistic |
| Mountain wave | Depends on terrain resolution | Needs high-resolution terrain; global models systematically under-represent it |
| CAT | ~100 m billows | **Never resolved**; diagnosed from resolved shear and stability (Ellrode index, Ri, EDR diagnostics) |

**Parameterisation** is what a model does with everything it cannot resolve: convection, cloud microphysics, radiation, boundary-layer turbulence, gravity-wave drag, land surface. These are the largest source of systematic model error, and the reason two models with identical resolution give different answers.

**Key implication for the flight deck**: WAFS turbulence, icing and CB fields are *diagnostics computed from a coarse model*, not observations. They tell you where the environment favours the hazard. They cannot tell you that a specific cell will be at a specific place at a specific time. Only radar, satellite and lightning can do that, and only for the next hour or two.

## 6. Forecast skill and predictability

### 6.1 The scores

| Score | What it measures |
|---|---|
| **RMSE** | Root mean square error of a continuous field |
| **Anomaly correlation coefficient (ACC)** | Correlation between forecast and analysed anomalies from climatology. **ACC = 0.6** is the conventional threshold for "useful"; **0.5** for "no better than climatology in practice" |
| **Bias / mean error** | Systematic offset |
| **CRPS** (continuous ranked probability score) | The standard probabilistic score for ensembles |
| **Brier score / reliability diagram** | Calibration of probability forecasts |
| **POD, FAR, CSI, Heidke skill score** | Categorical scores for yes/no events (fog, thunderstorms, ceiling below minima) |
| **Ensemble spread–skill relationship** | Whether the spread actually predicts the error |

### 6.2 Where skill stands

The headline: **500 hPa geopotential ACC now reaches 0.6 at roughly 9–10 days in the northern hemisphere for the best global model**, up from about 5 days in 1980 — a gain of roughly one day of lead time per decade, driven by satellite data, assimilation and resolution. Southern hemisphere skill, once far behind, is now close to northern hemisphere skill because satellite data dominates there.

But skill is **variable-dependent**:
- **Upper-level flow**: excellent, many days.
- **Surface temperature**: good, several days.
- **Precipitation location and amount**: much weaker; useful to ~3–5 days for the envelope, ~1 day for detail.
- **Ceiling and visibility**: the weakest of all, and the most operationally important for a TAF. Fog onset/clearance times remain a hard problem at 6 hours, let alone 24.
- **Convection timing and placement**: environment predictable days ahead; individual cells only nowcastable.
- **Dust**: dependent on both wind forecast and source-region soil state; convective dust is essentially unforecastable at synoptic lead.

**The predictability limit.** Theory and recent modelling put the intrinsic limit for synoptic-scale flow at roughly **two weeks**; some studies suggest a few days more is recoverable with a perfect model and perfect observations. Below that, upscale error growth from unresolved convection contaminates the larger scales within days — which is why a 3 km model does not stay better than a global model for long.

**Regimes matter.** A blocked, stationary pattern can be predictable for 10 days. A rapidly cycling, highly baroclinic Atlantic regime with a bomb developing can be uncertain at 48 hours in a way that changes your fuel figure. Look at ensemble spread, not just the deterministic run.

## 7. Nowcasting

For 0–6 hours the model is not the best tool; **extrapolation of observations** is.

- **Radar echo extrapolation / optical flow** — advecting the current radar field with the observed motion, blended into the NWP forecast over 1–3 hours. This blending (e.g. STEPS, INCA, Rainymotion-type approaches) is the core of every modern nowcast.
- **Satellite-based convective initiation** — cooling rate of cloud tops, overshooting-top detection.
- **Lightning trends** — a lightning jump precedes intensification.
- **Rapid-update models** with radar assimilation (HRRR, ICON-D2, AROME rapid update, UKV) — hourly cycling, useful from about 1–2 hours out to 12.
- **Machine learning nowcasting** — deep-learning radar extrapolation (DGMR, MetNet-3 and successors) has demonstrably beaten optical-flow methods on precipitation nowcasting benchmarks, and is being deployed operationally in several services.

**For the flight deck**, nowcasting is what your own radar, the airport radar picture on the EFB, satellite loop and lightning overlay give you. In the terminal area on a convective day, nothing else is relevant.

## 8. The machine-learning revolution

This is genuinely new and it is not marketing. Between 2022 and 2026 data-driven models moved from research curiosity to operational deployment at a major centre.

### 8.1 The models

| Model | Origin | Publication | Character |
|---|---|---|---|
| **FourCastNet** | NVIDIA and collaborators | 2022 | The first credible global data-driven forecast at 0.25°, based on adaptive Fourier neural operators. Demonstrated that a trained network could produce a plausible global forecast orders of magnitude faster than NWP |
| **Pangu-Weather** | Huawei Cloud | 2023, *Nature* | 3-D Earth-specific transformer at 0.25°; the first to claim it beat ECMWF HRES on a broad set of deterministic scores |
| **GraphCast** | Google DeepMind | 2023, *Science* | Graph neural network on a multi-mesh, 0.25°, 10-day forecasts, trained on ERA5; reported to beat HRES on the large majority of evaluated variable/lead-time targets and to run in about a minute on a TPU |
| **AIFS Single v1** | **ECMWF** | **Operational 25 February 2025** | The first data-driven model run **operationally by a major NWP centre**; **28 km grid spacing**; gains of **up to 20 %** on some measures including tropical cyclone tracks; covers wind, temperature, precipitation type, and surface solar/wind parameters for energy applications. An **AIFS ensemble became operational in July 2025**, and **Cycle 50r1 (12 May 2026)** updated both IFS and AIFS |
| **GenCast** | Google DeepMind | **4 December 2024, *Nature*** | **Diffusion** model producing a **≥50-member probabilistic ensemble** at **0.25°** out to **15 days**; more accurate than ECMWF **ENS** on **97.2 %** of tested targets, **99.8 %** beyond 36 h; a full 15-day forecast in **8 minutes on a single Cloud TPU v5** |
| **NeuralGCM**, **Aurora**, **FuXi**, **FengWu**, **Stormer**, **WeatherNext** | Various | 2024–2026 | A crowded and fast-moving field including hybrid physics/ML models and ML models trained on observations rather than reanalysis |

### 8.2 What they are good at, and what they are not

**Strengths.**
- **Cost**: inference in seconds to minutes on one accelerator, versus an hour on tens of thousands of supercomputer cores. This makes **large ensembles cheap**, which is the real prize.
- **Skill**: competitive with or better than the best physics models on many upper-air deterministic scores and on tropical cyclone tracks.
- **Ensembles**: GenCast's ENS-beating result changed the argument, because probabilistic skill was the last redoubt of physics-based systems.

**Limitations you should hold onto.**
- **They still need an analysis**, which still comes from conventional data assimilation on a physics model. They are forecast engines, not end-to-end systems — although observation-trained and end-to-end systems are an active research direction.
- **Physical consistency and conservation** are not guaranteed. Fields can be smoother than reality; extremes can be under-represented (a known criticism of deterministic ML models trained on MSE-type losses, which is precisely why diffusion/probabilistic approaches like GenCast were developed).
- **Out-of-distribution behaviour** is unknown. They are trained on the historical record (ERA5). Their behaviour in an unprecedented event, or in a changed climate, is not guaranteed.
- **Resolution and variables**: most operate at 0.25° (~28 km) on a limited variable set. They do not do convection-permitting scales, and they do not yet produce the full suite of aviation-relevant diagnostics (icing, turbulence EDR, CB tops) that the WAFS requires.
- **Verification against the products you actually use** — TAF-relevant ceiling and visibility — remains weak for all global models, ML or physical.

### 8.3 What this means for aviation

Realistically, over the next few years: cheaper and larger ensembles, better tropical cyclone track guidance, faster refresh cycles, and eventually ML-derived aviation hazard fields. The WAFS is a conservative, ICAO-specified system and will not change quickly. Expect the change to arrive first in **airline flight-planning and EFB products** (which are commercially free to use whatever verifies best) and only later in the regulated ICAO product set.

> ⚠️ **The FourCastNet, Pangu-Weather and GraphCast entries above could not be verified from a fetched source in this session** (Wikipedia pages were unavailable and the WebSearch budget was exhausted). Publication venues, dates and skill claims are stated from working knowledge and should be checked against the original papers before citation. The **AIFS and GenCast entries were verified** from ECMWF and DeepMind pages. `needs-verification`

## 9. How a forecaster actually builds a TAF

The TAF is not model output. It is a human product, and understanding the process tells you how to read it.

1. **Situational awareness first.** The forecaster looks at the synoptic situation, the satellite loop, the radar, the current observations and their trends, and the previous TAF and how it has verified so far. What air mass is over the field, and what is coming?
2. **Model guidance.** Several deterministic models plus the ensemble. Where they agree, confidence is high; where they diverge, the divergence goes into a `TEMPO` or `PROB` group.
3. **Model output statistics / direct model output** for the specific site — statistically corrected point forecasts of wind, temperature, cloud and visibility that remove known local model biases.
4. **Local knowledge.** This is the irreplaceable part. Every aerodrome has behaviours a model does not know: which wind direction brings sea fog; the exact temperature at which the runway ices; the wind speed above which fog will not form; the drainage flow off a nearby ridge at 0400; that convection always dies as it crosses a particular ridge. A forecaster with ten years at a station beats a global model comprehensively on the things that matter for a TAF.
5. **Construct the base state**, then add change groups in order of confidence:
   - `FM` where a distinct, confident, permanent change is expected (front, sea-breeze onset).
   - `BECMG` where the change is confident but the timing is not.
   - `TEMPO` where the condition will occur but intermittently.
   - `PROB30`/`PROB40` where the condition is genuinely uncertain.
6. **Apply amendment criteria.** The TAF must be amended when the actual or expected conditions cross defined thresholds (wind, visibility, cloud amount/base, weather onset/cessation). This is why a TAF that has been standing for five hours may be about to change abruptly.
7. **Verification feedback.** Forecasters are scored, and the scoring drives behaviour. Over-forecasting fog costs the airline fuel; under-forecasting it costs diversions. A conservative forecaster tends to include the `PROB` group; a bolder one does not. **Learn the local forecast office's habits at your regular destinations** — it is a real and legitimate operational skill.

**How to read the result.** A `TEMPO` group is a statement that the condition *will* occur, briefly. A `PROB30` is a statement that the forecaster genuinely does not know. A TAF with no change groups at all in a marginal season is either a very confident forecast or a very lazy one, and it is worth checking the ensemble meteogram to tell which.

## Sources

- [Changes to the ECMWF forecasting system](https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model) — ECMWF (cycle dates 48r1, 49r1, 50r1; AIFS operational February 2025 and ensemble July 2025)
- [ECMWF's AI forecasts become operational](https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational) — ECMWF (AIFS Single operational 25 February 2025; 28 km; up to 20 % gains; variables)
- [GenCast — Google DeepMind](https://deepmind.google/discover/blog/gencast-predicts-weather-and-the-risks-of-extreme-conditions-with-sota-accuracy/) — DeepMind (4 December 2024, *Nature*; 0.25°; ≥50 members; 15 days; 97.2 %/99.8 % vs ENS; 8 minutes on one TPU v5)
- [Aviation Weather Center product list](https://aviationweather.gov/gfa/help) — NOAA/NWS (operational forecast product suite, extended-range wind/temperature)
- [Clear-air turbulence](https://en.wikipedia.org/wiki/Clear-air_turbulence) — Wikipedia (CAT climate trend; detection limits)

## Open questions

- **FourCastNet, Pangu-Weather and GraphCast** — venue, date and skill claims not verified this session. `needs-verification`
- **Model resolutions and ensemble member counts** for IFS/HRES/ENS, GFS/GEFS, ICON, UM, ARPEGE — deliberately omitted because they change per cycle and could not be verified. `needs-verification`
- The **"one day of lead time per decade"** and **"ACC 0.6 at 9–10 days"** figures are well-established in the NWP literature but were not fetched from a primary source here. `needs-verification`
- **Effective resolution as 4–8× grid spacing** is a standard rule of thumb, not a fetched figure.
- **Percentage of assimilated observations that are satellite radiances (80–90 %)** is indicative.
- **TAF amendment criteria** are State- and service-specific; verify per AIP MET section.
