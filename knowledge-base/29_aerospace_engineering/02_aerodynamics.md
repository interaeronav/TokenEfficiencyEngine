---
id: aerospace.aerodynamics
title: Aerodynamics — the technical core
domain: 29_aerospace_engineering
tags: [aerodynamics, potential-flow, thin-airfoil-theory, lifting-line, boundary-layer, transition, turbulence, drag, naca, supercritical, high-lift, transonic, shock-waves, hypersonic, sweep, winglets, cfd, xfoil]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "16.100 Aerodynamics, Fall 2005", url: "https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/", publisher: "MIT OpenCourseWare", accessed: 2026-08-25}
  - {title: "XFOIL Subsonic Airfoil Development System", url: "https://web.mit.edu/drela/Public/web/xfoil/", publisher: "M. Drela, MIT", accessed: 2026-08-25}
  - {title: "SU2 Multiphysics Simulation and Design Software", url: "https://su2code.github.io/", publisher: "SU2 Foundation", accessed: 2026-08-25}
  - {title: "OpenVSP", url: "https://openvsp.org/", publisher: "NASA / OpenVSP community", accessed: 2026-08-25}
  - {title: "MIT Course 16 subject listing", url: "http://student.mit.edu/catalog/m16a.html", publisher: "MIT", accessed: 2026-08-25}
related: [aerospace.curriculum, aerospace.design_process, aerospace.propulsion, aerospace.practicals]
unit_system: SI
---

# Aerodynamics — the technical core

**Summary.** Aerodynamics is the study of how a body and a moving fluid exchange momentum. Almost all of practical aerodynamics is the management of a single embarrassment: the flow is very nearly inviscid almost everywhere, and the tiny region where it is not — the boundary layer — determines drag, stall, and whether the aircraft flies at all. The discipline is therefore organised as a set of nested approximations: potential flow gives lift, boundary-layer theory gives friction and separation, compressible theory gives shocks and wave drag, and CFD nominally gives everything at once while quietly failing at exactly the cases (separation, transition, buffet) that matter most.

## Key facts

| Quantity | Relation | Note |
|---|---|---|
| Lift per unit span (2-D) | `L' = ρ_∞ V_∞ Γ` | Kutta–Joukowski |
| Thin airfoil lift slope | `dc_l/dα = 2π` per radian (≈ 0.11 /deg) | Symmetric or cambered; zero-lift angle shifts with camber |
| Quarter-chord moment | `c_{m,c/4}` independent of α | Aerodynamic centre at c/4 in subsonic thin-airfoil theory; moves to ≈ c/2 supersonically |
| Finite-wing lift slope | `a = a₀ / (1 + a₀/(π AR e))` | `a₀` = 2-D slope |
| Induced drag | `C_{Di} = C_L² / (π AR e)` | `e` ≈ 0.7–0.9 typical; = 1 for elliptical loading |
| Prandtl–Glauert | `c_p = c_{p,0}/√(1−M∞²)` | Fails as M → M_crit |
| Blasius laminar BL | `δ/x = 5.0/√Re_x`, `c_f = 0.664/√Re_x` | Flat plate, zero pressure gradient |
| Turbulent flat plate | `δ/x ≈ 0.37/Re_x^{1/5}`, `c_f ≈ 0.0592/Re_x^{1/5}` | 1/7-power law, `Re_x < 10⁷` |
| Transition Reynolds number | `Re_x ≈ 5×10⁵` (flat plate, moderate disturbance) | Real wings: 10⁶–10⁷ with `e^N`, N ≈ 9 |
| Normal shock | `M₂² = (1 + ((γ−1)/2)M₁²)/(γM₁² − (γ−1)/2)` | Total pressure always drops |
| Prandtl relation | `M₁* M₂* = 1` | Characteristic Mach numbers |
| Critical Mach for transport wing | `M_crit ≈ 0.70–0.78`; `M_DD` ≈ 0.02–0.04 above | Supercritical sections push `M_DD` to ≈ 0.86–0.89 |
| Korn equation | `M_DD + C_L/10 + t/c = κ_A` | `κ_A` = 0.87 conventional, 0.95 supercritical; divide `M_DD` by cos Λ terms for sweep |
| Sweep effect | `M_eff = M_∞ cos Λ` (simple sweep theory) | Λ measured at the quarter or half chord depending on convention |
| Oswald efficiency for a jet transport | 0.75–0.85 | Winglets add roughly 0.02–0.06 |

> ⚠️ Every one of these is an approximation with a stated domain of validity. Prandtl–Glauert is a *linearised* correction and is meaningless above `M_crit`. Lifting-line theory assumes high aspect ratio and unswept quarter chord. Applying either outside its range is the most common error in student and consultant work alike.

## 1. Potential flow — the inviscid skeleton

For steady, incompressible, irrotational flow the velocity field is the gradient of a potential, `V = ∇φ`, and continuity reduces to **Laplace's equation** `∇²φ = 0`. Laplace is linear, so elementary solutions superpose. The four elementary flows in 2-D:

| Flow | Potential φ | Stream function ψ |
|---|---|---|
| Uniform | `V_∞ x` | `V_∞ y` |
| Source (strength Λ) | `(Λ/2π) ln r` | `(Λ/2π) θ` |
| Doublet (strength κ) | `(κ/2π)(cos θ)/r` | `−(κ/2π)(sin θ)/r` |
| Vortex (circulation Γ) | `−(Γ/2π) θ` | `(Γ/2π) ln r` |

Uniform + doublet = flow over a cylinder. Add a vortex and the cylinder produces lift `L' = ρV_∞Γ` — the Kutta–Joukowski theorem, the single most important result in aerodynamics. Conformal mapping (the **Joukowski transformation** `z = ζ + b²/ζ`) turns the circle into an airfoil-like shape, which is how the field solved airfoil flow before computers.

**Circulation is not arbitrary.** The **Kutta condition** — the flow leaves the sharp trailing edge smoothly — fixes Γ to one physically realised value. Kelvin's circulation theorem explains where it comes from: the starting vortex shed at the beginning of motion carries equal and opposite circulation.

### Thin airfoil theory

Represent the camber line by a vortex sheet of strength `γ(x)`. Enforcing flow tangency along the camber line yields the fundamental equation of thin airfoil theory; with the substitution `x = (c/2)(1 − cos θ)` and a Fourier expansion of γ:

```
c_l = 2π (α − α_{L=0})
α_{L=0} = −(1/π) ∫₀^π (dz/dx)(cos θ₀ − 1) dθ₀
c_{m,c/4} = (π/4)(A₂ − A₁)
```

Consequences a pilot recognises immediately: a symmetric section makes no lift at zero α; camber shifts the zero-lift angle negative (that is what a deployed flap does, plus an area change); and the aerodynamic centre sits at quarter chord, which is why the CG limits are quoted in %MAC around that point.

### Lifting-line theory (Prandtl, 1918)

A finite wing sheds trailing vorticity because the bound circulation must vary spanwise and vortex lines cannot end in the fluid (Helmholtz). The trailing sheet induces a **downwash** `w(y)`, which tilts the local lift vector rearward and creates **induced drag** — drag with no viscosity in it at all.

```
α_eff = α − α_i,   α_i = w/V_∞
C_Di = C_L²/(π AR e)
```

Elliptical spanwise loading gives `e = 1` and the minimum possible induced drag for a given lift and span. Real wings approximate it with taper (`λ ≈ 0.3–0.45` unswept, higher swept) plus washout. Lifting-line breaks down for `AR < ~4`, for strongly swept wings, and near stall.

The extension to arbitrary planform is the **vortex-lattice method** (VLM) and then the 3-D **panel method** (source/doublet distributions on the actual surface), which is what AVL, XFLR5 in 3-D mode, VSPAERO and PANAIR do. MIT's 16.100 explicitly teaches "subsonic potential flows, including source/vortex panel methods" as its first block.

## 2. Boundary layers, transition and turbulence

Prandtl's 1904 insight: at high Reynolds number the viscous effects are confined to a thin layer, and within it the normal momentum equation collapses to `∂p/∂y ≈ 0` — the outer inviscid pressure is *impressed* on the boundary layer. This decoupling is the reason aerodynamics is tractable.

**Key thicknesses:**
```
δ*  = ∫₀^δ (1 − u/U) dy          (displacement thickness — the streamline shift the outer flow sees)
θ   = ∫₀^δ (u/U)(1 − u/U) dy     (momentum thickness — proportional to drag)
H   = δ*/θ                        (shape factor: 2.59 Blasius, ≈1.3–1.4 turbulent, ≈3.5–4 at separation)
```

**Von Kármán momentum integral** (the workhorse of fast methods, and the core of XFOIL):
```
dθ/dx + (2 + H)(θ/U)(dU/dx) = c_f/2
```

**Separation** occurs when the wall shear vanishes, `(∂u/∂y)_{y=0} = 0`, which an adverse pressure gradient makes inevitable if it is strong or long enough. Turbulent boundary layers resist separation because turbulent mixing transports high-momentum fluid to the wall — hence vortex generators, and hence the counter-intuitive fact that a *rougher* golf ball flies further.

**Transition** is the hardest unsolved practical problem in the field. Mechanisms:
- **Tollmien–Schlichting waves** — 2-D viscous instability, dominant on unswept wings at low turbulence.
- **Crossflow instability** — dominant on swept wings; the inflectional crossflow profile is inviscidly unstable, which is why natural laminar flow is so hard beyond about 20° sweep.
- **Attachment-line contamination** — turbulence propagating along the leading-edge attachment line from the root; governed by `R̄ ≈ 245` criterion.
- **Bypass transition** — high freestream turbulence (turbomachinery) skips the linear stage entirely.
- **Separation bubbles** — laminar separation, transition in the shear layer, turbulent reattachment. Dominant at `Re_c < 5×10⁵`, i.e. all model aircraft, sailplane tips and UAVs, and the reason low-Reynolds airfoil design is its own art.

The engineering method is the **e^N envelope method**: track the integrated amplification of the most unstable disturbance and declare transition at `N ≈ 9` (wind tunnel) or `N ≈ 11–14` (flight, quieter air). XFOIL implements exactly this.

**Turbulence** itself: energy cascade from integral scale `L` to Kolmogorov scale `η = (ν³/ε)^{1/4}`, with `L/η ~ Re^{3/4}`. This scaling is why DNS of a full aircraft at flight Reynolds number remains out of reach — the cell count scales roughly `Re^{9/4}` and the time steps with `Re^{3/4}`.

## 3. Drag decomposition — the accountant's view

The only honest way to design is to know where each drag count (1 count = `ΔC_D` of 0.0001) goes. For a large subsonic transport at cruise, a representative split:

| Component | Share of total drag | Physics |
|---|---|---|
| **Skin friction** | 45–50 % | Viscous shear; scales with wetted area and `Re^{-1/5}` turbulent |
| **Induced (lift-dependent) drag** | 35–40 % | Trailing vorticity; `C_L²/(π AR e)`; grows as the square of `C_L`, so worst at high altitude/heavy/slow |
| **Pressure (form) drag** | 5–8 % | Boundary-layer displacement altering the pressure distribution |
| **Wave drag** | 3–8 % | Shock total-pressure loss; near-zero below `M_crit`, rises violently above `M_DD` |
| **Interference drag** | 3–6 % | Wing–body, pylon–wing, fairing junctions |
| **Excrescence / roughness / leakage** | 3–5 % | Rivets, gaps, antennae, ECS outflow, door seals |
| **Trim drag** | 1–3 % | Download on the tail requiring extra wing lift |

Two vocabularies coexist. The **classical** split is parasite + induced. The **modern (Van der Vooren/Destarac) far-field** split is viscous + induced (vortex) + wave + spurious — obtained by integrating entropy and vorticity in the wake, and it is the only decomposition that is meaningful in a CFD solution, because near-field pressure integration cannot separate wave from viscous drag.

The practical form used in conceptual design is the **drag polar** `C_D = C_{D0} + K C_L²` with `K = 1/(π AR e)`. `C_{D0}` is built up by the **component build-up method**: for each component, `C_{D,c} = C_{f,c} · FF_c · Q_c · S_{wet,c} / S_ref`, where `C_f` is flat-plate friction at the component Reynolds number, `FF` is a form factor from thickness ratio and sweep, and `Q` is an interference factor (1.0 for a well-faired wing, 1.3–1.5 for a poor nacelle installation). Raymer and Gudmundsson both tabulate these. For a clean jet transport, `C_{D0} ≈ 0.018–0.022`; a fixed-gear light aircraft is 0.030–0.040; a bizjet 0.017–0.020.

`L/D_max` follows directly: `L/D_max = ½ √(π AR e / C_{D0})`, attained at `C_L = √(C_{D0} π AR e)`. For an A350 at long-range cruise, `L/D` in the high teens (≈ 18–20) is the right order; a sailplane reaches 50–70; a Cessna 172 about 12.

## 4. Airfoil families and their design

| Family | Era / origin | Character |
|---|---|---|
| **NACA 4-digit** (e.g. 2412) | 1932 | Digit 1 = max camber %c, digit 2 = its position in tenths, digits 3–4 = thickness %c. Benign stall, forgiving; still ubiquitous in GA (2412 on the C172). |
| **NACA 5-digit** (e.g. 23012) | 1935 | Forward camber for higher `c_lmax` at low `c_m`; sharper stall. Widely used on 1940s–60s transports. |
| **NACA 6-series** (e.g. 63₂-615, 64A010) | 1940s | Designed for extended favourable pressure gradient → **laminar flow**. First digit = series, second = position of minimum pressure in tenths chord, subscript = low-drag `c_l` range, last two = thickness. The famous "drag bucket". In practice manufacturing roughness and insects destroyed most of the benefit on production aircraft. |
| **Supercritical (Whitcomb, ~1967)** | NASA Langley | Flattened upper surface producing a weak, aft-positioned shock; large aft camber; blunt nose; thick trailing edge. Raises `M_DD` by ~0.05–0.10 at equal thickness, or permits ~30 % more thickness at equal `M_DD` — which buys structural depth and fuel volume. Every transport wing since the 1980s is supercritical. |
| **Peaky sections** (Pearcey, ~1962) | UK | Predecessor of supercritical; a sharp leading-edge suction peak with isentropic recompression. Used on the VC10, Trident, early 747. |
| **Natural Laminar Flow (NLF) and Laminar Flow Control (LFC/HLFC)** | 1980s– | NLF: shaping alone (Cirrus SR22, some sailplanes, business-jet wings). HLFC: suction through a perforated leading edge — flown on the B757 HLFC glove, the A320 BLADE demonstrator (Clean Sky), and in production on the 787-9 vertical fin and nacelles. |
| **Wortmann FX / Eppler / Selig** | 1960s– | Sailplane and low-Reynolds sections designed with bubble control; Selig's S12xx/SD70xx series dominate UAV and DBF-class design. |
| **Rotorcraft sections (VR-x, OA-x, SC10xx)** | | Must work at both high `c_lmax` (retreating blade) and high `M_DD` (advancing blade) — a genuinely brutal multi-point problem. |

Airfoil design today is **inverse or optimisation-driven**: prescribe the target pressure distribution (or an objective functional) and let the code find the geometry. XFOIL includes a full-inverse and a mixed-inverse mode for precisely this.

## 5. High-lift devices

Take-off and landing field length is set by `C_{Lmax}`, and `C_{Lmax}` is bought with mechanical complexity. Typical increments:

| Device | Δ`c_lmax` (2-D) | Mechanism |
|---|---|---|
| Plain flap (60°) | +0.9 | Effective camber increase |
| Split flap | +0.9 | Camber plus base pressure change |
| Slotted flap | +1.3 | Camber + fresh boundary layer energised through the slot |
| Double-slotted | +1.6 | As above, twice; plus chord extension (Fowler motion) |
| Triple-slotted (747, 727) | +1.9 | Maximum, at heavy weight/cost/maintenance penalty |
| Fowler motion | proportional to `c'/c` | Area increase — often the largest single contribution |
| Leading-edge slat | +0.4 to +0.6 | Delays leading-edge separation by reducing the suction peak; extends stall α by 8–12° |
| Krueger flap | +0.3 to +0.5 | Leading-edge camber; used where a slat's slot would spoil laminar flow (787 inboard) |
| Drooped leading edge | +0.2 to +0.3 | Simplest, lightest |

Whole-aircraft `C_{Lmax}` values: clean transport wing 1.2–1.5; take-off configuration 1.8–2.2; landing configuration 2.6–3.2. Note the 3-D value is always *lower* than the 2-D sectional maximum by sweep effects (roughly `cos Λ` on the increment) and spanwise flow.

The modern trend is **fewer slots, more Fowler motion**: the 787 and A350 use single-slotted trailing-edge flaps with advanced dropped-hinge or link-track kinematics rather than the 747's triple-slotted arrangement, trading a little `C_{Lmax}` for large reductions in weight, cost, cruise excrescence drag and noise.

## 6. Compressibility and the transonic regime

Below `M ≈ 0.3`, density change is under 5 % and incompressible theory is adequate. Above it, **Prandtl–Glauert** `c_p = c_{p0}/β`, `β = √(1−M∞²)`, corrects linearly; **Karman–Tsien** and **Laitone** do slightly better. All of them go singular at `M = 1` and are meaningless once local flow is supersonic.

**Critical Mach number `M_crit`** is the freestream Mach at which the flow somewhere on the surface first reaches `M = 1`. It is found by intersecting the Prandtl–Glauert-corrected minimum `c_p` with the isentropic critical-pressure relation:
```
c_{p,crit} = (2/(γM∞²)) · [ ((1 + ((γ−1)/2)M∞²)/(1 + (γ−1)/2))^{γ/(γ−1)} − 1 ]
```
**Drag-divergence Mach `M_DD`** is where `dC_D/dM = 0.1` (Boeing definition) or where `ΔC_D` = 20 counts (Douglas definition) — typically 0.02–0.04 above `M_crit`. The **Korn equation** `M_DD = κ_A − t/c − C_L/10` with `κ_A ≈ 0.87` (conventional) or `0.95` (supercritical) is the conceptual-design shortcut; the swept form divides thickness and `C_L` terms by powers of `cos Λ`.

Above `M_DD` a **shock** terminates the supersonic pocket. Total pressure falls across it (`p₀₂/p₀₁ < 1` always), which is wave drag; and the adverse gradient at the shock foot thickens or separates the boundary layer — **shock-induced separation**, which produces **buffet** and sets the aircraft's cruise ceiling. The buffet boundary the pilot sees on the cruise chart is exactly this phenomenon.

**Area rule** (Whitcomb, 1952): near `M = 1`, wave drag depends primarily on the *longitudinal distribution of total cross-sectional area*, which should follow a smooth Sears–Haack body. Hence coke-bottled fuselages (F-102, Convair 990's anti-shock bodies, the 747 upper deck fairing, the DC-9's tail). The Sears–Haack minimum wave drag is
```
D_wave = 9π/2 · (A_max²/ L²) · q      →      C_{Dw} = 24 A_max/(L²) · ... (form varies by reference)
```
the operative point being wave drag scales as `(A_max/L)²` — slenderness is everything.

## 7. Supersonic and hypersonic flow

Supersonic flow is **hyperbolic**: information travels along Mach lines (`μ = arcsin(1/M)`) and cannot propagate upstream. Consequences:
- **Oblique shocks**: `tan θ = 2 cot β · (M₁² sin²β − 1)/(M₁²(γ + cos 2β) + 2)`. For a given θ and `M₁` there are two β solutions (weak and strong); above a maximum θ the shock detaches.
- **Prandtl–Meyer expansion**: `ν(M) = √((γ+1)/(γ−1)) arctan√((γ−1)(M²−1)/(γ+1)) − arctan√(M²−1)`; isentropic, so no total pressure loss.
- **Linearised supersonic airfoil theory (Ackeret)**: `c_l = 4α/√(M²−1)`, `c_d = 4(α² + ᾱ_c² + ᾱ_t²)/√(M²−1)`. Lift slope *falls* with Mach; drag exists at zero lift purely from thickness. The aerodynamic centre moves from c/4 to ≈ c/2 — the source of the Concorde's fuel-transfer trim system and of the "Mach tuck" that requires a Mach trim function on subsonic jets approaching `M_MO`.
- **Sonic boom**: the near-field pressure signature coalesces into an N-wave; overpressure scales roughly with `W/(L^{3/2} h^{3/4})`. NASA's **X-59 QueSST** is the current low-boom demonstrator, targeting ~75 PLdB instead of ~105 for Concorde.

**Hypersonics** (`M > 5`) is qualitatively different: shock layers are thin and hot, real-gas effects (vibrational excitation, dissociation, ionisation) invalidate the calorically perfect gas assumption, viscous interaction couples the boundary layer to the outer shock, and heating dominates design. Newtonian impact theory `c_p = 2 sin²θ` becomes a surprisingly useful first estimate. Stagnation heating follows the **Fay–Riddell** relation, `q̇_s ∝ √(ρ_∞/R_n) V_∞³` — hence blunt noses on re-entry vehicles (Allen and Eggers, 1953): a blunt body puts most of the energy into the shock layer rather than the wall. MIT covers this in **16.122 Aerothermodynamics**.

## 8. Wing planform effects

| Parameter | Typical values | Effect |
|---|---|---|
| **Aspect ratio** `AR = b²/S` | Sailplane 25–40; transport 9–11 (787 ≈ 11.0, A350 ≈ 9.5); fighter 2.5–4 | Induced drag `∝ 1/AR`; structural weight and root bending moment rise with `AR`; gate span limits (ICAO Code E = 65 m, Code F = 80 m) cap it — the 777X folding wingtip exists precisely to break that constraint |
| **Sweep** Λ | Transport 25–35° (737 = 25°, 787 ≈ 32.2°, A350 ≈ 31.9°); fighters up to 60° | Raises `M_crit` via `M_eff ≈ M cos Λ`; costs `C_Lmax`, adds tip-stall tendency, aeroelastic wash-out/in coupling, crossflow transition |
| **Taper ratio** `λ = c_t/c_r` | 0.2–0.45 | Approximates elliptical loading; too low provokes tip stall (low local Re, high local `c_l`) |
| **Twist / washout** | −2° to −5° | Unloads the tip, protects against tip stall, tunes span loading; aeroelastic washout on a swept wing adds to it |
| **Dihedral** Γ | Low-wing jets +5 to +7°; high-wing +0 to −3° (anhedral) | Sets `C_{lβ}` (roll due to sideslip) and therefore spiral/Dutch-roll balance. Sweep contributes an effective dihedral of roughly 1° per 10° of sweep at typical `C_L` |
| **Winglets / raked tips** | 737 blended (~2.4 m), 737 MAX split-scimitar-style "AT winglet", 787 raked tip, A350 curved tip | Reduce induced drag by increasing effective span and by producing a forward thrust component from the sidewash; typical block-fuel benefit 2–5 % on long sectors. A raked tip is often lighter for the same benefit; a winglet is retrofit-friendly and gate-span-friendly |

**Ground effect**: within about one span of the surface, the image vortex system reduces downwash, cutting induced drag and increasing lift slope. A standard approximation (Wieselsberger):
```
Φ = ( (16 h/b)² ) / ( 1 + (16 h/b)² )    with C_Di,ground = Φ · C_Di,free
```
At `h/b = 0.1`, Φ ≈ 0.72 — a 28 % induced drag reduction; at `h/b = 0.5`, Φ ≈ 0.98, essentially nothing. Practically: the float in the flare, the reduced pitch-up authority needed at touchdown, and the tendency to balloon. It also changes the pitching moment (nose-down for most configurations as the tail leaves ground effect last).

## 9. The modern toolchain — and an honest assessment of CFD

**Panel and integral-boundary-layer methods** remain in daily use because they are fast, robust, and validated to death over 40 years:
- **XFOIL** (Mark Drela, MIT; current release **6.99, 23 December 2013; GPL**) — interactive design and analysis of subsonic isolated airfoils; panel method coupled with an integral boundary layer and an `e^N` transition model, handling forced or free transition, transitional separation bubbles and trailing-edge separation. It remains the single most useful piece of aerodynamic software a student can learn, and it runs in seconds.
- **XFLR2/XFLR5** — GUI wrapper adding LLT, VLM and 3-D panel analysis of complete aircraft.
- **AVL** (also Drela) — vortex-lattice with a full rigid-body dynamics and trim solver; produces stability derivatives directly.
- **OpenVSP** (NASA-originated, open source; version **3.51.3 released 17 August 2026**) — parametric geometry with VSPAERO (VLM/panel), mass properties and parasite-drag build-up. The bridge between a sketch and an analysis.

**RANS CFD** is the industrial workhorse. Solvers: ANSYS Fluent, Siemens Star-CCM+, Cadence Fidelity, and in-house codes (Boeing's, Airbus's elsA/CODA with ONERA/DLR); open source: **SU2** (LGPL 2.1, SU2 Foundation — unstructured, compressible and incompressible, discrete adjoint and shape optimisation, NICFD) and **OpenFOAM**. Turbulence models in practice: **Spalart–Allmaras** (one equation, robust, external aero) and **Menter k-ω SST** (two equation, better in adverse gradients and separation onset).

**The honest state of validation.** The AIAA **Drag Prediction Workshop** series (six workshops, DPW-I in 2001 through DPW-VI/VII on the NASA Common Research Model) is the field's own audit and its results are sobering:
- For **attached, cruise-condition flow**, well-run RANS on a well-converged grid predicts drag within roughly **±1–3 %** — but the *scatter between competent participants* on the same geometry and the same nominal conditions has historically been of the order of **10–20 drag counts**, comparable to or larger than the benefit being designed for.
- Grid convergence is the dominant error source; the workshops repeatedly showed that many submissions were not grid-converged, and that Richardson extrapolation across a family of systematically refined grids changes the answer by more than the modelling difference between turbulence models.
- For **separated flow, buffet onset, `C_Lmax`, and high-lift configurations**, RANS is not predictive. The AIAA **High-Lift Prediction Workshop** series shows `C_Lmax` scatter of several tenths and stall angle scatter of several degrees. High-lift design still ends in the wind tunnel.
- **Transition prediction** in general-purpose RANS is either absent (fully turbulent assumption) or a correlation-based add-on (γ–Re_θ, Langtry–Menter; or amplification-factor transport). None of these are reliable for crossflow-dominated swept wings without calibration.
- **LES/DES/hybrid RANS-LES** predicts separated flow far better but costs 2–4 orders of magnitude more. Wall-modelled LES of a full aircraft at flight Reynolds number is a current research frontier; wall-resolved LES is not feasible and will not be for decades on general hardware.

The correct professional posture, and the one industry actually takes: **CFD is a comparative tool of high value and an absolute tool of limited value.** Deltas between two similar configurations computed on the same grid topology with the same solver settings are trustworthy to a few counts. Absolute drag numbers used for performance guarantees come from wind tunnel testing corrected for Reynolds number and model support, and are finally confirmed in flight test. NASA's Turbulence Modeling Resource and the DPW/HiLiftPW databases exist so that anyone can check their own solver against the same cases — and running one of those cases yourself is the single best way to acquire calibrated scepticism.

## Sources

- [MIT OCW 16.100 Aerodynamics (Fall 2005)](https://ocw.mit.edu/courses/16-100-aerodynamics-fall-2005/) — MIT OpenCourseWare
- [XFOIL — Subsonic Airfoil Development System](https://web.mit.edu/drela/Public/web/xfoil/) — Mark Drela, MIT
- [SU2](https://su2code.github.io/) — SU2 Foundation
- [OpenVSP](https://openvsp.org/) — NASA / OpenVSP community
- [MIT Course 16 subject listing](http://student.mit.edu/catalog/m16a.html) — MIT (16.100, 16.110, 16.13, 16.18, 16.120, 16.122 descriptions and prerequisites)

## Open questions

- The specific drag-count scatter figures quoted for the AIAA Drag Prediction Workshops are from the workshop literature but were not re-fetched for this file — treat the exact numbers as `needs-verification`; the qualitative conclusion is robust and repeatedly published.
- Exact quarter-chord sweep angles for the 787 (≈32.2°) and A350 (≈31.9°) are widely published but not verified against manufacturer documentation here — `needs-verification`.
- Δ`c_lmax` values for high-lift devices are the classic Raymer/Torenbeek table values; they are design-guidance figures, not measurements for any specific aircraft.

