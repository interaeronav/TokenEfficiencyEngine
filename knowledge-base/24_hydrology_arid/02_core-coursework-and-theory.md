---
id: hydrology.coursework
title: Core hydrology coursework and theory
domain: 24_hydrology_arid
tags: [water-balance, evapotranspiration, penman-monteith, infiltration, green-ampt, richards, van-genuchten, unit-hydrograph, flood-frequency, manning, darcy, theis, cooper-jacob, advection-dispersion]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "FAO Irrigation and Drainage Paper 56 — Crop evapotranspiration", url: "https://www.fao.org/4/x0490e/x0490e00.htm", publisher: "FAO", accessed: 2026-08-25}
  - {title: "Groundwater (Freeze & Cherry, free full text)", url: "https://gw-project.org/books/groundwater/", publisher: "The Groundwater Project", accessed: 2026-08-25}
  - {title: "Analysis and Evaluation of Pumping Test Data (Kruseman & de Ridder, 2nd ed., free)", url: "https://gw-project.org/books/analysis-and-evaluation-of-pumping-test-data/", publisher: "The Groundwater Project / ILRI / Wageningen UR", accessed: 2026-08-25}
  - {title: "Runoff curve number", url: "https://en.wikipedia.org/wiki/Runoff_curve_number", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Manning formula", url: "https://en.wikipedia.org/wiki/Manning_formula", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Water retention curve (van Genuchten)", url: "https://en.wikipedia.org/wiki/Water_retention_curve", publisher: "Wikipedia", accessed: 2026-08-25}
related: [hydrology.overview, hydrology.arid_zone, hydrology.modelling]
unit_system: SI
---

# Core hydrology coursework and theory

**Summary.** This is the content of a standard hydrology and hydrogeology curriculum, module by module, with the working equations written out. It is deliberately equation-first: these are the relationships you will actually apply when sizing a tank, a culvert or a borehole. Symbols are SI throughout. Where a method is known to behave badly in drylands, that is flagged inline and taken up properly in `03`.

## Key facts — the equations you will use most

| Purpose | Equation | Notes |
|---|---|---|
| Water balance | `P = ET + Q + R + ΔS` | over any control volume and period |
| Reference ET | FAO-56 Penman-Monteith | the international standard |
| Infiltration | Green-Ampt or Horton | intensity-limited in drylands |
| Peak flow, small catchment | `Q = C·i·A / 3.6` (SI) | rational method, A ≤ ~50–200 ha |
| Open channel | `V = (1/n)·R^(2/3)·S^(1/2)` | Manning, SI |
| Groundwater flow | `q = −K·dh/dl` | Darcy |
| Pumping test | Theis / Cooper-Jacob | T and S from drawdown |

## 1. The hydrologic cycle and the water balance

Every hydrologic calculation is a bookkeeping exercise over a chosen control volume and period:

```
P + Q_in = ET + Q_out + R + ΔS
```

Closing a water balance requires that you can measure or estimate every term to a tolerance smaller than the term you are solving for. In humid catchments you solve for runoff (large); in drylands you solve for recharge (tiny) as the residual of P and ET (both large). This is why arid-zone recharge estimation is done with tracers rather than by subtraction.

Time scales matter: an annual balance may close while every individual month is badly wrong, because storage absorbs the error.

## 2. Precipitation measurement and analysis

- **Depth, intensity, duration, frequency, areal extent** are the five descriptors. A storm is characterised by its depth-duration relationship, not by a single number.
- **Gauge errors**: wind-induced undercatch (5–20% for rain, much worse for snow), evaporation loss from the funnel, wetting loss, and splash. Tipping-bucket gauges systematically *under*-read at high intensity because of the tip time — precisely the intensities that matter for dryland design. Calibrate dynamically, not just volumetrically.
- **Areal averaging**: Thiessen polygons, isohyetal method, inverse-distance and kriging. Areal reduction factors (ARF) convert point rainfall to catchment-average rainfall; ARFs derived from temperate frontal storms overestimate areal rainfall for convective cells.
- **Double-mass curves** detect inhomogeneity in a record (a gauge moved, a tree grew).
- **Missing data**: normal-ratio method, inverse-distance weighting, or regression against a nearby homogeneous station.

## 3. Evaporation and evapotranspiration

The **FAO-56 Penman-Monteith** reference evapotranspiration for a hypothetical 0.12 m grass crop, albedo 0.23, surface resistance 70 s m⁻¹:

```
        0.408·Δ·(Rn − G) + γ · (900/(T+273)) · u2 · (es − ea)
ET0 = ─────────────────────────────────────────────────────────
                  Δ + γ·(1 + 0.34·u2)
```

- `ET0` mm day⁻¹; `Rn` net radiation MJ m⁻² day⁻¹; `G` soil heat flux (≈0 for daily); `T` mean air temperature °C; `u2` wind speed at 2 m, m s⁻¹; `es`, `ea` saturation and actual vapour pressure kPa; `Δ` slope of the saturation vapour-pressure curve kPa °C⁻¹; `γ` psychrometric constant kPa °C⁻¹.

Supporting relationships (all FAO-56):
```
es(T)  = 0.6108 · exp(17.27·T / (T + 237.3))
Δ      = 4098 · es(T) / (T + 237.3)²
P_atm  = 101.3 · ((293 − 0.0065·z)/293)^5.26        [kPa, z in m]
γ      = 0.000665 · P_atm
Rns    = (1 − α)·Rs,           α = 0.23
Rnl    = σ·((Tmax,K⁴ + Tmin,K⁴)/2)·(0.34 − 0.14·√ea)·(1.35·Rs/Rso − 0.35)
Rso    = (0.75 + 2×10⁻⁵·z)·Ra
σ      = 4.903×10⁻⁹ MJ K⁻⁴ m⁻² day⁻¹
```

**Hargreaves-Samani**, when only temperature is available:
```
ET0 = 0.0023 · Ra · (Tmean + 17.8) · (Tmax − Tmin)^0.5     [Ra expressed in mm day⁻¹]
```

**Priestley-Taylor**, for energy-limited (wet) surfaces:
```
ET = α_PT · (Δ/(Δ + γ)) · (Rn − G)/λ,      α_PT ≈ 1.26
```
Priestley-Taylor is the wrong tool in a dryland: it deliberately drops the aerodynamic term that dominates when hot dry air advects over a moist surface. Use it for open-water or fully-wet canopies only.

**Pan coefficients.** Class A pan evaporation `Epan` converts to ET₀ via `ET0 = Kp · Epan`, with `Kp` typically 0.55–0.85 depending on upwind fetch, relative humidity and wind. Namibian A-pan records are often the only long evaporation series available, so the pan coefficient is a real practical concern; a sunken (Colorado) pan needs a different coefficient again.

**Worked value for Okongo** (17.566°S, 17.216°E, 1160 m): using NASA POWER 2001–2020 climatology, FAO-56 PM gives **ET₀ ≈ 2430 mm yr⁻¹** and Hargreaves gives **≈ 2670 mm yr⁻¹** against P ≈ 588 mm yr⁻¹ — an aridity index P/ET₀ ≈ 0.24. The two methods differ by ~10%, which is normal, and both dwarf rainfall.

**Actual ET** is not reference ET. `ETc = Kc · ET0` applies a crop coefficient; under water stress `ETa = Ks · Kc · ET0` with a stress coefficient `Ks ≤ 1`. In drylands `ETa` is almost always far below `ET0` because there is no water to evaporate — which is precisely why "PET exceeds rainfall" does not mean the landscape is a net exporter of vapour beyond what falls.

## 4. Infiltration theory

**Horton (1940)** — empirical exponential decay of infiltration capacity:
```
f(t) = f_c + (f_0 − f_c)·e^(−k t)
```
`f_0` initial capacity, `f_c` final (≈ saturated conductivity), `k` decay constant.

**Philip (1957)** — two-term series solution of the Richards equation for a semi-infinite column:
```
F(t) = S·t^(1/2) + A·t          →    f(t) = ½·S·t^(−1/2) + A
```
`S` is sorptivity (capillary uptake, dominant early); `A` approaches `K_s` (gravity, dominant late).

**Green-Ampt (1911)** — piston-flow wetting front, physically based and the one embedded in most models:
```
f = K_s · (1 + (ψ_f · Δθ)/F)
```
`ψ_f` wetting-front suction head, `Δθ = θ_s − θ_i` the moisture deficit, `F` cumulative infiltration. For ponded conditions the implicit cumulative form is
```
F − ψ_f·Δθ·ln(1 + F/(ψ_f·Δθ)) = K_s·t
```
solved iteratively. Green-Ampt handles the intensity-limited case correctly: if rainfall intensity `i < f`, all rain infiltrates and ponding has not begun; ponding starts at `F_p = ψ_f·Δθ / (i/K_s − 1)`.

> In deep Kalahari sands `K_s` is high (often 10⁻⁵–10⁻⁴ m s⁻¹, i.e. 36–360 mm h⁻¹), so infiltration-excess runoff is rare on the sands themselves and common on crusted, calcrete-floored or compacted surfaces — which is exactly where the iishana and pans sit.

## 5. Soil physics and unsaturated flow

**Richards equation** (mixed form, 1-D vertical, z positive downward):
```
∂θ/∂t = ∂/∂z [ K(θ) · (∂ψ/∂z − 1) ]
```
or in head form `C(ψ)·∂ψ/∂t = ∂/∂z[K(ψ)(∂ψ/∂z − 1)]` with `C = dθ/dψ` the specific moisture capacity. It is a strongly non-linear parabolic PDE; convergence problems near saturation and in dry soils are a fact of life.

**van Genuchten (1980)** retention curve:
```
θ(ψ) = θ_r + (θ_s − θ_r) / [1 + (α|ψ|)^n]^m ,        m = 1 − 1/n
```
with the Mualem conductivity model:
```
K(S_e) = K_s · S_e^L · [1 − (1 − S_e^(1/m))^m]²,     S_e = (θ − θ_r)/(θ_s − θ_r),  L ≈ 0.5
```
Typical sand parameters: `θ_r ≈ 0.045`, `θ_s ≈ 0.43`, `α ≈ 14.5 m⁻¹`, `n ≈ 2.68`, `K_s ≈ 7.1 m day⁻¹` (Carsel & Parrish class values, as shipped with HYDRUS; verify against local samples before design use).

**Brooks-Corey** is the older alternative with an explicit air-entry pressure — sometimes better behaved for coarse sands.

Related concepts you need: field capacity (≈ −33 kPa) and permanent wilting point (−1500 kPa), plant-available water, hysteresis between wetting and drying curves, and preferential flow through macropores and root channels — which in dryland sands (termite galleries, old root casts) can short-circuit the matrix entirely and is a major reason chloride-profile recharge estimates and lysimeter estimates disagree.

## 6. Runoff generation

- **Hortonian (infiltration-excess) overland flow**: rainfall intensity exceeds infiltration capacity. Controlled by intensity and surface condition. Dominant in drylands, on crusted soils, on roads and roofs.
- **Saturation-excess (Dunne) overland flow**: the soil profile fills from below and rain on a saturated area runs off regardless of intensity. Dominant in humid catchments, and in drylands only in the pans, iishana floors and clay depressions.
- **Subsurface stormflow / interflow**, **return flow**, and the **variable source area** concept.
- **Partial-area** and **runon-runoff** patterning: in drylands, runoff generated on bare interpatch areas infiltrates on vegetated patches downslope. Total catchment yield falls as the patch structure works properly, and rises sharply when it is degraded by overgrazing.

## 7. The unit hydrograph

The unit hydrograph `U(t)` is the direct-runoff response to 1 unit (usually 1 mm or 1 cm) of effective rainfall applied uniformly over the catchment in a specified duration. It assumes linearity and time-invariance. Direct runoff from a storm is then the convolution:
```
Q_n = Σ_{m=1}^{n} P_m · U_{n−m+1}
```
Synthetic unit hydrographs (Snyder, SCS dimensionless, Clark) parameterise `U` from catchment characteristics when no gauged storm data exist. The **SCS dimensionless UH** uses a peak rate factor (484 in US customary practice, ~2.08 in SI form of `q_p = 2.08·A/T_p`) — that factor drops to ~300 or lower for flat, sandy, high-storage catchments, and the Cuvelai's flat iishana landscape is at the extreme flat end. Using the default 484 in an oshana catchment overestimates the peak substantially.

## 8. Flood frequency analysis and return periods

Fit an extreme-value distribution to annual maximum series (AMS) or to a partial-duration/peaks-over-threshold (POT) series. Common distributions: Gumbel (EV1), Generalised Extreme Value (GEV), Log-Pearson Type III (US federal standard), Log-Normal.

Return period and risk:
```
T = 1/p ;   risk of at least one exceedance in n years = 1 − (1 − 1/T)^n
```
A 1-in-100-year flood has a **26%** chance of occurring at least once in 30 years, and a 1-in-50-year event has **45%** in 30 years. Quote this to clients; "100-year flood" is routinely misunderstood as "once per century".

Plotting positions: Weibull `p = m/(N+1)`, Cunnane `p = (m − 0.4)/(N + 0.2)`, Gringorten. Regional frequency analysis (index-flood, L-moments) pools short records from hydrologically similar sites — essential in drylands where single-site records are far too short.

> ⚠️ In arid catchments the annual maximum series contains zeros in dry years, which violates the assumptions of every standard distribution. Use a mixed distribution (probability of a zero year, plus a distribution conditional on flow occurring), or POT. Ignoring this biases design floods low.

## 9. Open-channel hydraulics

**Manning's equation** (SI):
```
V = (1/n) · R^(2/3) · S^(1/2)      ;      Q = A·V = (1/n)·A·R^(2/3)·S^(1/2)
```
`R = A/P` hydraulic radius (m), `S` energy slope (m/m), `n` Manning roughness (s m^−1/3). Representative `n`: smooth concrete 0.012–0.014; earth channel, clean 0.022–0.025; earth channel with grass 0.030–0.035; natural sandy channel with some brush 0.040–0.070; floodplain with dense bush 0.10+.

**Specific energy** `E = y + V²/2g`; **Froude number** `Fr = V/√(g·D)` with `D` hydraulic depth. `Fr < 1` subcritical, `Fr > 1` supercritical, `Fr = 1` critical. Critical depth in a rectangular channel: `y_c = (q²/g)^(1/3)`.

**Gradually varied flow** — the backwater equation:
```
dy/dx = (S_0 − S_f) / (1 − Fr²)
```
integrated by the standard-step or direct-step method to produce M1/M2/S1 etc. profiles. This is what HEC-RAS does in 1-D.

**Hydraulic jump** (rectangular): `y2/y1 = ½(√(1 + 8·Fr1²) − 1)`, with energy loss `ΔE = (y2 − y1)³/(4·y1·y2)` — the basis of stilling-basin design.

## 10. Groundwater flow

**Darcy's law**:
```
q = −K · dh/dl        [m s⁻¹, specific discharge]
Q = −K·A·dh/dl        [m³ s⁻¹]
v = q/n_e             [actual pore velocity]
```
`K` hydraulic conductivity (m s⁻¹ or m day⁻¹), `n_e` effective porosity. Intrinsic permeability `k = K·μ/(ρ·g)` separates the fluid from the medium — needed for density-dependent (saline) problems.

Representative `K` (m s⁻¹): clay 10⁻¹¹–10⁻⁹; silt 10⁻⁹–10⁻⁷; fine sand 10⁻⁵–10⁻⁴; coarse sand/gravel 10⁻⁴–10⁻². The Ohangwena aquitard was measured at ~10⁻⁹ m s⁻¹ under confining pressure (swelling clays), while the KOH-2 aquifer sands sit at 10⁻⁶–10⁻⁵ m s⁻¹ — a four-orders-of-magnitude contrast, which is why the deep freshwater stays fresh beneath the brackish water above it.

**Transmissivity and storage**:
```
T = K·b                     [m² day⁻¹]
S = S_s·b   (confined)      dimensionless, typically 10⁻⁵–10⁻³
S ≈ S_y     (unconfined)    specific yield, typically 0.05–0.30
```

**Groundwater flow equation** (transient, saturated, heterogeneous, anisotropic):
```
∂/∂x(K_x ∂h/∂x) + ∂/∂y(K_y ∂h/∂y) + ∂/∂z(K_z ∂h/∂z) + W = S_s ∂h/∂t
```
which reduces to the Laplace equation `∇²h = 0` for steady state in a homogeneous isotropic medium. Two-dimensional confined form: `∂²h/∂x² + ∂²h/∂y² = (S/T)·∂h/∂t`. This is the equation MODFLOW discretises.

**Dupuit-Forchheimer** assumptions (horizontal flow, hydraulic gradient = water-table slope) linearise the unconfined problem and underpin most well formulas.

## 11. Well hydraulics and pumping-test analysis

**Thiem (steady state, confined)**:
```
Q = 2π·T·(h2 − h1) / ln(r2/r1)
```

**Theis (transient, confined)**:
```
s = (Q/4πT) · W(u),        u = r²S/(4T t)
```
`W(u)` is the exponential integral (well function). Analysis by curve-matching `s` vs `t` against `W(u)` vs `1/u`.

**Cooper-Jacob straight-line approximation**, valid for `u < 0.01` (large `t`, small `r`):
```
s = (2.30·Q / 4πT) · log10(2.25·T·t / (r²·S))
```
Plot `s` against `log t`. Then, with `Δs` the drawdown change per log cycle and `t0` the intercept at `s = 0`:
```
T = 2.30·Q / (4π·Δs)          S = 2.25·T·t0 / r²
```
This is the everyday field method and should be the first thing you do to any pumping-test dataset.

**Hantush-Jacob** handles leaky confined aquifers; **Neuman** handles unconfined delayed yield; **Papadopulos-Cooper** corrects for large-diameter wells; **Cooper-Bredehoeft-Papadopulos** covers slug tests; **Hvorslev** is the simple slug-test alternative.

**Step-drawdown test** separates aquifer loss from well loss:
```
s_w = B·Q + C·Q^n         (n ≈ 2)
```
`B·Q` is formation (laminar) loss, `C·Q²` is well (turbulent) loss. **Well efficiency** = `BQ/(BQ + CQ²)`. A poorly developed borehole shows a large `C`; this is the number that tells you whether to re-develop or to accept a lower yield.

For a full treatment use Kruseman & de Ridder, *Analysis and Evaluation of Pumping Test Data*, 2nd edition (1991, 377 pp., ISBN 90 70754 207) — **free** from the Groundwater Project.

## 12. Water quality and contaminant transport

**Advection-dispersion equation** (1-D, with linear sorption and first-order decay):
```
R · ∂C/∂t = D_L · ∂²C/∂x² − v · ∂C/∂x − λ·R·C
```
`R = 1 + ρ_b·K_d/n` retardation factor; `D_L = α_L·v + D*` longitudinal dispersion coefficient with `α_L` dispersivity and `D*` effective molecular diffusion; `λ` decay constant. The Ogata-Banks solution for a step input in a semi-infinite column:
```
C/C0 = ½·[ erfc((x − vt)/(2√(D_L t))) + exp(vx/D_L)·erfc((x + vt)/(2√(D_L t))) ]
```

Practical water-quality content: major-ion chemistry and the Piper and Stiff diagrams; total dissolved solids vs electrical conductivity (rule of thumb `TDS (mg/L) ≈ 0.55–0.75 × EC (µS/cm)` for typical groundwater — always calibrate locally); charge-balance error as a QA check on a laboratory analysis (should be within ±5%); saturation indices from PHREEQC; and the health-based parameters that matter in northern Namibia — fluoride, nitrate, sulphate, and bacteriological indicators (see `05`).

## 13. Hydrologic statistics

Descriptive statistics of skewed hydrologic series (log transformation, L-moments), correlation and regression, autocorrelation and persistence, trend tests (Mann-Kendall, Sen's slope), homogeneity tests (Pettitt, standard normal homogeneity test), stochastic generation of synthetic series (AR(1), Thomas-Fiering), and Monte Carlo propagation of parameter uncertainty. Goodness-of-fit measures for models: Nash-Sutcliffe efficiency `NSE = 1 − Σ(Qo − Qs)²/Σ(Qo − Q̄o)²`, Kling-Gupta efficiency (KGE), percent bias, RMSE. NSE is dominated by high flows; for intermittent dryland series report KGE and a log-transformed NSE as well, and state the fraction of zero-flow days the model got right.

## Sources

- [FAO Irrigation and Drainage Paper 56 — *Crop evapotranspiration*](https://www.fao.org/4/x0490e/x0490e00.htm), Allen, Pereira, Raes & Smith (1998). Source for all ET₀ equations above.
- Freeze, R.A. & Cherry, J.A., *Groundwater* (Prentice-Hall 1979, 604 pp., ISBN 0-13-365312-9) — [free full text](https://gw-project.org/books/groundwater/).
- Kruseman, G.P. & de Ridder, N.A., *Analysis and Evaluation of Pumping Test Data*, 2nd ed. — [free](https://gw-project.org/books/analysis-and-evaluation-of-pumping-test-data/).
- [Runoff curve number](https://en.wikipedia.org/wiki/Runoff_curve_number), [Manning formula](https://en.wikipedia.org/wiki/Manning_formula), [Water retention curve](https://en.wikipedia.org/wiki/Water_retention_curve) — Wikipedia, used for cross-checking standard formulations.
- ET₀ values for Okongo computed from [NASA POWER](https://power.larc.nasa.gov/) climatology, 2026-08-25.

## Open questions

- Carsel & Parrish van Genuchten class parameters are quoted from standard HYDRUS documentation but were not re-verified against the original 1988 paper — treat as indicative.
- Manning `n` values are standard textbook ranges (Chow 1959 lineage) and were not re-verified against a primary source in this pass.
