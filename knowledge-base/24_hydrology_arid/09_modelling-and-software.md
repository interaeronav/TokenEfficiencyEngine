---
id: hydrology.modelling
title: Hydrological modelling and software
domain: 24_hydrology_arid
tags: [modflow, flopy, feflow, seawat, mt3d, hec-hms, hec-ras, swat, mike-she, topmodel, weap, swmm, hydrus, pest, calibration, uncertainty, qgis, python]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "MODFLOW 6 — USGS Modular Hydrologic Model", url: "https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model", publisher: "USGS", accessed: 2026-08-25}
  - {title: "HEC-HMS", url: "https://www.hec.usace.army.mil/software/hec-hms/", publisher: "USACE Hydrologic Engineering Center", accessed: 2026-08-25}
  - {title: "HEC-RAS", url: "https://www.hec.usace.army.mil/software/hec-ras/", publisher: "USACE HEC", accessed: 2026-08-25}
  - {title: "EPA Storm Water Management Model (SWMM)", url: "https://www.epa.gov/water-research/storm-water-management-model-swmm", publisher: "US EPA", accessed: 2026-08-25}
  - {title: "HYDRUS", url: "https://www.pc-progress.com/en/Default.aspx?hydrus-1d", publisher: "PC-Progress", accessed: 2026-08-25}
  - {title: "SWAT", url: "https://swat.tamu.edu/", publisher: "Texas A&M", accessed: 2026-08-25}
  - {title: "WEAP", url: "https://www.weap21.org/", publisher: "Stockholm Environment Institute", accessed: 2026-08-25}
  - {title: "PEST and PEST++", url: "https://pesthomepage.org/", publisher: "Watermark Numerical Computing", accessed: 2026-08-25}
  - {title: "FloPy documentation", url: "https://flopy.readthedocs.io/", publisher: "USGS / FloPy developers", accessed: 2026-08-25}
  - {title: "Pastas", url: "https://pastas.dev/", publisher: "Pastas developers", accessed: 2026-08-25}
related: [hydrology.coursework, hydrology.arid_zone, hydrology.tech_trends]
---

# Hydrological modelling and software

**Summary.** The practical modelling stack: groundwater, surface water and catchment, unsaturated zone, water quality, GIS, the Python ecosystem, and calibration and uncertainty. Version numbers and URLs were tested on 2026-08-25 where stated. The file closes with the question that matters most and is asked least — whether a model is worth building at all.

## Key facts

| Tool | What it is | Licence | URL (tested 2026-08-25) |
|---|---|---|---|
| **MODFLOW 6** | The USGS modular groundwater flow and transport model | Public domain, free | [usgs.gov](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model) (200) |
| **FloPy** | Python API to build, run and post-process MODFLOW | Free, open source; PyPI **3.10.0** | [flopy.readthedocs.io](https://flopy.readthedocs.io/) (200) |
| **HEC-HMS** | Rainfall-runoff and catchment simulation; current **4.14** | Free | [hec.usace.army.mil](https://www.hec.usace.army.mil/software/hec-hms/) (200) |
| **HEC-RAS** | 1-D and 2-D hydraulics; a 2025 release stream is current | Free | [hec.usace.army.mil](https://www.hec.usace.army.mil/software/hec-ras/) (200) |
| **EPA SWMM** | Urban/plot stormwater; current **5.2.4** | Public domain, free | [epa.gov](https://www.epa.gov/water-research/storm-water-management-model-swmm) (200) |
| **HYDRUS-1D** | Unsaturated-zone Richards-equation model | 1D free, 2D/3D commercial | [pc-progress.com](https://www.pc-progress.com/en/Default.aspx?hydrus-1d) (200) |
| **SWAT / SWAT+** | Agricultural catchment water, sediment and nutrients | Free | [swat.tamu.edu](https://swat.tamu.edu/) (200) |
| **WEAP** | Water allocation and planning | Free for developing-country academic/NGO use | [weap21.org](https://www.weap21.org/) (200) |
| **PEST / PEST++** | Model-independent calibration and uncertainty | Free | [pesthomepage.org](https://pesthomepage.org/) (200) |
| **Pastas** | Time-series analysis of groundwater heads; PyPI **1.14.0** | Free, open source | [pastas.dev](https://pastas.dev/) (200) |

## 1. Groundwater modelling

### MODFLOW 6 and its ecosystem
MODFLOW 6 is the current-generation USGS code and the object-oriented rewrite of the MODFLOW family. Key architectural changes from MODFLOW-2005: multiple models can be coupled in a single simulation (Groundwater Flow, Groundwater Transport, Groundwater Energy, and now surface-water components), a flexible unstructured **DISV/DISU** discretisation alongside the classic structured **DIS** grid, and Newton-Raphson formulation for robust wetting and drying — which matters greatly in dryland models where cells go dry.

Packages you will use: **NPF** (node property flow, replacing LPF/BCF), **STO** (storage), **CHD/WEL/DRN/RIV/GHB** (boundary conditions), **RCH** and **EVT** (recharge and evapotranspiration), **UZF** (unsaturated zone flow — essential where the water table is deep), **SFR** (streamflow routing — the package that can represent transmission losses in an ephemeral channel), **LAK**, **MAW** (multi-aquifer well), and **OBS** for observations.

- **ModelMuse** — the free USGS graphical pre- and post-processor for MODFLOW 6, PHAST and SUTRA. The right entry point if you are not scripting.
- **FloPy** — the Python package for building, running and post-processing MODFLOW models. This is now the mainstream professional workflow: your model is a script, which means it is version-controllable, reproducible and scriptable for scenario runs. `pip install flopy` (3.10.0).
- **GMS (Aquaveo)** — a commercial integrated environment with strong 3-D geological model building; excellent for turning borehole logs into a layered conceptual model, which is exactly the Ohangwena problem. <https://www.aquaveo.com/software/gms-groundwater-modeling-system-introduction>
- **Visual MODFLOW Flex (Waterloo Hydrogeologic)** — the other main commercial GUI, strong on workflow and reporting for consultancy deliverables.
- **FEFLOW (DHI)** — finite-element, unstructured meshes, and the strongest of the mainstream codes for density-dependent flow, heat transport and complex geometry. Commercial.
- **SEAWAT** — variable-density groundwater flow, coupling MODFLOW and MT3DMS. The code for saline intrusion and for evaporative-concentration problems; in a Cuvelai context it is the right tool if you want to model why the brackish/fresh interface sits where it does.
- **MT3D-USGS / MT3DMS** — solute transport on a MODFLOW flow field. MODFLOW 6's own **GWT** model increasingly supersedes it for new work.
- **PHREEQC / PHT3D** — geochemical speciation and reactive transport. PHREEQC is essential for anything involving saturation indices, mineral dissolution or ion exchange — including interpreting a Cuvelai hydrochemistry dataset.
- **AnAqSim / TTim / analytical element methods** — for problems where a full numerical model is overkill; extremely useful for well-interference and capture-zone questions.

### Practical MODFLOW cautions in a dryland
- Use **UZF**, not simple RCH, wherever the unsaturated zone is more than a few metres thick — otherwise you are asserting that this year's rain reaches the water table this year, which in 30 m of Kalahari sand is false.
- Use **SFR with streambed conductance** if you want to represent an ephemeral channel; expect the calibration to be dominated by that conductance.
- Newton-Raphson (`NEWTON` option) plus the `UNDER_RELAXATION` settings, or you will spend your life on dry-cell convergence failures.
- Recharge should be spatially distributed by **landform**, not uniformly (see `03`).

## 2. Surface water and catchment models

| Model | Character | Where it fits |
|---|---|---|
| **HEC-HMS** (4.14, free) | Event and continuous rainfall-runoff; loss methods include SCS-CN, Green-Ampt, deficit-and-constant, and soil moisture accounting; transform by unit hydrograph, Clark, ModClark or kinematic wave | The default for design floods on small to medium catchments. **Use Green-Ampt, not SCS-CN, for dryland infiltration-excess** |
| **HEC-RAS** (2025 release stream, free) | 1-D steady and unsteady, 2-D unsteady (full and diffusion-wave shallow water), sediment transport, water quality; RAS Mapper for terrain and results | Culvert and bridge hydraulics, channel design, floodplain mapping. 2-D is excellent but demands a good DEM — a serious constraint in the flat Cuvelai |
| **SWAT / SWAT+** (free) | Semi-distributed, HRU-based, continuous, daily; water, sediment, nutrients, crop growth | Catchment-scale land-management scenarios. SWAT+ is the restructured successor with better landscape routing and a QGIS interface (QSWAT+) |
| **MIKE SHE** (DHI, commercial) | Fully integrated, physically based, distributed surface–subsurface | The most complete representation of coupled processes, and the only mainstream code that handles overland flow, unsaturated zone and groundwater properly in one system. Expensive and data-hungry |
| **TOPMODEL** | Conceptual, topographic index, saturation-excess | Elegant and instructive, but its core assumption (runoff from saturated near-stream areas) is the **wrong mechanism** for drylands. Use it to learn, not to design |
| **VIC** | Macro-scale land-surface model, grid-based | Regional and climate-impact studies, not site work |
| **WEAP** (SEI) | Water allocation, demand, supply, priorities, scenarios, economics | The right tool for a basin-scale allocation question — and it has been applied to the Cuvelai-Etosha Basin specifically for water availability and allocation planning |
| **EPA SWMM** (5.2.4, free) | Urban hydrology and hydraulics, subcatchments, conduits, storage, LID/SuDS controls | Plot- and settlement-scale stormwater, including green-infrastructure sizing |
| **PCSWMM** (CHI, commercial) | SWMM engine with a full GIS interface, 2-D, and design tools | The professional stormwater workflow when SWMM's own interface is too limited |
| **Pitman model / SPATSIM** (Rhodes IWR) | Monthly conceptual rainfall-runoff | **The southern African standard for regional water-resources assessment** and the model behind most South African and Namibian basin studies. If you are doing catchment yield work in this region, this is the model your reviewers will expect |

## 3. Unsaturated zone

**HYDRUS-1D** solves the Richards equation (plus heat and solute transport) in one dimension, with van Genuchten-Mualem or Brooks-Corey hydraulic functions, root-water uptake, and inverse parameter estimation from observed profiles. It is **free**, and it is the right tool for: estimating how deep a wetting front penetrates after a given storm, testing whether a given rainfall regime can produce recharge through 30 m of sand, and interpreting a soil-moisture or chloride profile. HYDRUS-2D/3D adds dimensions and is commercial.

Alternatives: **SWAP** (Wageningen), **UNSAT-H**, **STOMP**, and MODFLOW 6's own **UZF** package for the coarse-resolution case.

The practical warning: in deep sandy profiles the model output is dominated by the hydraulic parameters, and literature (Carsel & Parrish) class values for "sand" span a wide range. **Measure your own retention curve** (HYPROP/WP4C, see `08`) before believing a HYDRUS recharge estimate.

## 4. Water quality

- **PHREEQC** (USGS, free) — aqueous speciation, saturation indices, mineral equilibria, ion exchange, inverse modelling of two waters and a mineral assemblage. Indispensable for interpreting Cuvelai hydrochemistry.
- **MT3D-USGS**, **MODFLOW 6 GWT**, **PHT3D**, **SEAWAT** — transport, reactive transport and density coupling.
- **QUAL2K**, **WASP**, **CE-QUAL-W2** — surface-water quality.
- **AQUACHEM / GW Chart / Piper-plot tools** — routine hydrochemical data plotting.

## 5. GIS integration

- **QGIS** — the free GIS that now does everything ArcGIS does for hydrology. Key plugins and toolsets: **GRASS** `r.watershed` and `r.stream.*`, **SAGA** terrain analysis, **QSWAT+**, **FREEWAT** (a QGIS-based MODFLOW environment), **Serval** and the raster calculator for DEM conditioning.
- **ArcHydro** (Esri) — the classic geoprocessing framework for catchment delineation, stream networks and the HEC-GeoHMS/HEC-GeoRAS lineage.
- **TauDEM** (Utah State, free) — parallel terrain analysis: pit filling, D8 and D-infinity flow directions, contributing area, stream networks, and wetness index. <https://hydrology.usu.edu/taudem/taudem5/>
- **WhiteboxTools** (free, with a commercial Whitebox Workflows tier) — a very fast, dependency-free geospatial analysis library with an exceptional hydrological toolset, callable from Python and QGIS. <https://www.whiteboxgeo.com/>
- **DEM sources**: Copernicus GLO-30 and GLO-90, SRTM, ASTER GDEM, NASADEM, and — where you can get it — FABDEM (bare-earth corrected). **In the Cuvelai, all of these have vertical errors comparable to the entire flood depth.** For site work, fly a drone and process with RTK ground control.

## 6. The Python ecosystem

| Package | Purpose |
|---|---|
| **FloPy** (3.10.0) | Build, run and post-process MODFLOW 6 and earlier |
| **pyEMU** | Environmental model uncertainty analysis; the Python front end to PEST++ workflows |
| **Pastas** (1.14.0) | Transfer-function-noise time-series models of groundwater heads — fit heads against rainfall and evaporation, decompose the response, detect trends. **Ideal for a single borehole with a few years of logger data**, which is the common dryland situation, and far more honest than a numerical model on the same data |
| **hydroeval** (0.1.0) | Efficiency metrics — NSE, KGE, and their decompositions |
| **HydroFunctions** | Convenient access to USGS NWIS streamflow data (US-only, but useful for teaching) |
| **xarray** + **rioxarray** + **dask** | The standard stack for gridded climate and remote-sensing data (NetCDF, Zarr, GeoTIFF) at scale |
| **rasterio**, **geopandas**, **shapely**, **pyproj** | Raster and vector geospatial work |
| **pyet** | Reference and potential ET by many formulations, including Penman-Monteith, Hargreaves and Priestley-Taylor |
| **SciPy** + **statsmodels** + **lmoments3** | Distribution fitting, extreme-value analysis, trend tests |
| **MetPy**, **climate-indices** | Meteorological calculations and drought indices (SPI, SPEI) |
| **PyMODFLOW / modflow-devtools** | Supporting tooling for MODFLOW workflows |

A realistic modern workflow: pull climate data with `xarray`, compute ET₀ with `pyet`, build the groundwater model with `FloPy`, calibrate with `PEST++` driven by `pyEMU`, and evaluate with `hydroeval` — all in a version-controlled repository with a notebook that regenerates every figure.

## 7. Calibration and uncertainty

**PEST and PEST++** (<https://pesthomepage.org/>) are model-independent: they wrap any model that reads text input and writes text output, adjust parameters, and minimise an objective function. Core concepts you must understand before using them:

- **Regularisation** — Tikhonov regularisation and singular value decomposition (SVD) prevent over-fitting when you have more parameters than information. Highly-parameterised inversion with regularisation is the modern standard; hand-tuning five zone values is not.
- **Pilot points** — spatially distributed parameters interpolated from a set of estimated points, rather than blocky zones.
- **PEST++ tools**: `pestpp-glm` (gradient-based with FOSM uncertainty), `pestpp-ies` (iterative ensemble smoother — the current best-practice approach for uncertainty in large models), `pestpp-sen` (global sensitivity), `pestpp-opt` and `pestpp-mou` (optimisation under uncertainty).
- **FOSM / linear uncertainty analysis** — cheap first-order estimates of parameter and prediction uncertainty from the Jacobian.
- **GLUE (Generalised Likelihood Uncertainty Estimation)** — the Monte-Carlo, "many behavioural models" approach. Philosophically contested but honest about **equifinality**, and well suited to sparse-data dryland problems where a single "best" parameter set is not defensible.
- **Monte Carlo and Latin hypercube sampling** — the general-purpose approach; the Ohangwena KOH-2 study effectively did a structured version of this by running 143 physically realistic boundary-condition realisations and keeping those consistent with heads, gradients and ¹⁴C ages.

**Objective functions.** For intermittent dryland flow series, do not report NSE alone. Report KGE and its decomposition (correlation, bias, variability), a log-transformed NSE, percent bias, and — crucially — the model's skill at reproducing **zero-flow days**, which a squared-error metric ignores entirely.

## 8. When is a model worth building at all?

This is the section most modelling guides omit. Before you build anything:

**A model is probably worth it when:**
- You need to test scenarios that cannot be observed (abstraction 20 years hence, a new wellfield, a climate projection).
- You have enough data to constrain the parameters that control the answer.
- The decision at stake is large enough to justify the effort, and reversible if the model is wrong.
- You need to force a rigorous conceptual model — often the *real* value of a modelling exercise is the conceptualisation, not the output.

**A model is probably not worth it when:**
- You have fewer observations than parameters and no independent constraints. The model will fit, and it will fit anything.
- The question can be answered by a spreadsheet water balance, an analytical solution (Theis, Thiem, Ogata-Banks) or a chloride mass balance.
- The decision does not change with the answer.
- The DEM, the rainfall record or the geology are so uncertain that a sophisticated model produces confident nonsense — the flat Cuvelai floodplain on a 30 m global DEM is exactly this case.

**A hierarchy to work up, not down:**
1. **Water balance on paper.** Does the water even exist? This is what `00`'s table does.
2. **Analytical solution.** Theis for drawdown, Ogata-Banks for a plume, a Rippl mass curve for a tank.
3. **Lumped conceptual or time-series model.** Pastas on a borehole hydrograph; HEC-HMS on a small catchment.
4. **Distributed numerical model.** Only when 1–3 cannot answer the question.

**Always** state the conceptual model in words before writing a single input file, and **always** report what the model cannot do. A calibrated model in a data-poor dryland basin is a hypothesis with a graphical interface, and it should be presented as such.

## Sources

All URLs HTTP-tested on 2026-08-25.

- [MODFLOW 6](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model), USGS (200) · [MODFLOW-2005](https://www.usgs.gov/software/modflow-2005-usgs-three-dimensional-finite-difference-ground-water-model) (200)
- [HEC-HMS](https://www.hec.usace.army.mil/software/hec-hms/) (200) — download listing shows current release **4.14**; [HEC-RAS](https://www.hec.usace.army.mil/software/hec-ras/) (200)
- [EPA SWMM](https://www.epa.gov/water-research/storm-water-management-model-swmm) (200) — page lists **SWMM 5.2.4** downloads
- [HYDRUS-1D](https://www.pc-progress.com/en/Default.aspx?hydrus-1d) (200) · [SWAT](https://swat.tamu.edu/) (200) · [SWAT+ docs](https://swatplus.gitbook.io/docs) (200) · [MIKE Powered by DHI](https://www.mikepoweredbydhi.com/) (200)
- [WEAP](https://www.weap21.org/) (200) · [PEST / PEST++](https://pesthomepage.org/) (200)
- [FloPy](https://flopy.readthedocs.io/) (200) — PyPI version 3.10.0 · [Pastas](https://pastas.dev/) (200) — PyPI version 1.14.0 · hydroeval PyPI version 0.1.0
- [Aquaveo GMS](https://www.aquaveo.com/software/gms-groundwater-modeling-system-introduction) (200) · [Visual MODFLOW Flex](https://www.waterloohydrogeologic.com/visual-modflow-flex/) (202)
- [TauDEM](https://hydrology.usu.edu/taudem/taudem5/) (200) · [WhiteboxTools](https://www.whiteboxgeo.com/) (200) · [PCSWMM](https://www.pcswmm.com/) (200)
- Kandjinga, L. & Bharati, L. (2026) *Assessment of Current Water Use and Future Water Availability for Planning and Allocation in the Cuvelai-Etosha Basin, Namibia*, EGU abstract, doi:10.5194/egusphere-egu26-1328 — the WEAP application to this basin.

## Open questions

- **MODFLOW 6's current version number was not extracted** — the USGS page blocked automated content retrieval (CloudFront 403) although the URL resolves. Check the version before quoting it.
- HEC-RAS's current release number is described as a "2025" stream from the download listing; the exact version was not confirmed.
- ModelMuse's current USGS landing URL was not confirmed (two candidate URLs returned 404); search usgs.gov directly.
- Package versions are those on PyPI on 2026-08-25 and will move.

