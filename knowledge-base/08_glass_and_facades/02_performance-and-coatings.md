---
id: glass.performance_coatings
title: Glass performance and coatings
domain: 08_glass_and_facades
tags: [low-e, solar-control, shgc, g-value, u-value, vlt, lsg, shading-coefficient, igu, double-glazing, argon, acoustic-glass, electrochromic, self-cleaning, hot-climate]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "PFG Laminates brochure (rev 8, October 2016)", url: "http://pfg.co.za/wp-content/uploads/2016/10/PFG-laminates-brochure-rev8-October-2016.pdf", publisher: "PFG Building Glass (PG Group)", accessed: 2026-08-25}
  - {title: "Insulated glazing", url: "https://en.wikipedia.org/wiki/Insulated_glazing", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Low-emissivity", url: "https://en.wikipedia.org/wiki/Low-emissivity", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Solar gain", url: "https://en.wikipedia.org/wiki/Solar_gain", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SAGE Electrochromics", url: "https://en.wikipedia.org/wiki/SAGE_Electrochromics", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Guardian Glass — glass types", url: "https://www.guardianglass.com/us/en/our-glass/glass-types", publisher: "Guardian Glass", accessed: 2026-08-25}
  - {title: "AGC Glass Europe — product brands", url: "https://www.agc-yourglass.com/", publisher: "AGC Glass Europe", accessed: 2026-08-25}
related: [glass.overview, glass.types_manufacture, glass.specifying]
unit_system: SI
---

# Glass performance and coatings

**Summary.** Four numbers describe the performance of a glazing make-up: **U-value** (conduction), **SHGC / g-value** (total solar heat), **VLT** (daylight) and, derived from the last two, the **light-to-solar-gain ratio (LSG)**. This file defines them precisely, explains the coating and IGU technologies that move them, gives the verified PFG performance data for the products actually stocked in southern Africa, and works through glass selection for north- and west-facing glazing at roughly 18°S — where SHGC dominates, U-value is secondary, and the temptation to go dark is the main trap.

## Key facts

| Metric | Definition | Direction |
|---|---|---|
| **VLT** | percentage of visible light (380–780 nm) transmitted, measured perpendicular to the glass | higher = more daylight |
| **SHGC (g-value)** | fraction of total solar energy 300–2 500 nm transmitted to the interior, **including** the absorbed fraction re-radiated inwards; 0–1 | lower = less cooling load |
| **U-value** | W/m²·K; conducted heat flow per unit area per degree of indoor/outdoor difference | lower = better insulation |
| **SC** | shading coefficient; `SC = SHGC ÷ 0.867` — 3 mm clear float has SHGC 0.867 and SC 1.0 | lower = less solar heat |
| **LSG** | `VLT ÷ SHGC`; spectral selectivity | higher = more daylight per unit of heat |
| **Tdw-ISO** | ISO Damage Weighted Transmittance, 300–600 nm; fading potential | lower = less fading |
| **Rw** | weighted sound reduction index, dB | higher = quieter |

| Reference value | Figure | Source |
|---|---|---|
| Emissivity, uncoated glass | **0.91** | Wikipedia |
| Uncoated single laminated glass U-value | **5.8 W/m²·K** | PFG |
| Pyrolytic low-E single laminated U-value | **3.7 W/m²·K** | PFG |
| Argon thermal conductivity | **67%** that of air | Wikipedia |
| Krypton | about **half** the conductivity of argon | Wikipedia |
| Optimum IGU cavity | **16–19 mm** measured at the centre of the unit | Wikipedia |
| Typical SHGC, double glazing | **0.42–0.55**; triple **0.33–0.47** | Wikipedia |
| Typical g-value range | **0.2–0.7**; solar control usually below **0.5** | Wikipedia |

## 1. What the numbers actually mean

**U-value** measures conduction and long-wave radiation exchange. It is what keeps a building warm at night and cool against a hot ambient air temperature. In a Namibian summer, ambient air is hot but the dominant load through glass is *radiation*, not conduction — so U-value is the second-order variable. It becomes first-order in the interior highlands winter, where nights are genuinely cold and heat loss through single glazing is severe, and it is first-order for any air-conditioned space where the outside air is 38 °C.

**SHGC** is the number that determines cooling plant size. It has two components: the directly transmitted solar energy, and the portion the glass *absorbs* and then re-radiates and convects inwards. This second component is why a heavily body-tinted glass is less effective than its dark appearance suggests — it absorbs a lot of energy and hands a good fraction of it to the interior. It is also why tinted glass runs hot and is the main driver of thermal-stress breakage.

**VLT** is daylight and view. Cutting VLT below about 40% starts to make interiors read as gloomy and pushes up artificial lighting, which returns as internal heat gain.

**LSG = VLT ÷ SHGC** is the single most useful selection metric in a hot, bright climate. It separates glasses that reject heat *selectively* (coated, spectrally selective) from glasses that reject heat by simply going dark (deep tints, mirror finishes). A theoretical perfect selective filter would transmit all visible light and no near-infrared; in practice, LSG above about 1.2 is very good, around 1.0 is respectable, and below 0.7 means you are buying darkness rather than performance.

**Shading coefficient** persists in southern African literature. The conversion is exact and worth memorising: **SC = SHGC ÷ 0.867**, equivalently **SHGC ≈ SC × 0.87**.

## 2. Coatings

### Hard coat (pyrolytic, on-line)

Applied at the float line while the ribbon is still hot — a fluorinated tin dioxide layer is deposited pyrolytically and fuses into the glass surface. Properties:

- **Durable.** Can be handled, stored, cut, toughened, bent and used in monolithic (single-glazed) applications exposed to the atmosphere.
- **Moderate performance.** Emissivity typically in the 0.1–0.2 region rather than the 0.03–0.05 of a good soft coat, so U-value improvement is real but limited.
- **Slight haze / colour.** Usually a faint warm cast.

This is the technology behind PFG's **E Range**: a pyrolytic low-E surface combined with tinted interlayers or coated glass, taking a single-glazed laminate from **U 5.8 to U 3.7 W/m²·K** without an IGU. For southern Africa this matters enormously, because it delivers a meaningful thermal improvement in a **single-glazed, monolithic, laminated** product — no sealed unit, no edge seal to fail, no argon to leak, and it can be cut and handled like ordinary glass.

### Soft coat (magnetron sputtered, MSVD, off-line)

Deposited in a vacuum chamber by magnetron sputtering — successive thin layers, typically **5 to 10 or more**, built around one, two or three silver layers with antireflection and barrier layers around them. Properties:

- **Much higher performance.** Very low emissivity, and by tuning the stack, high VLT with low SHGC — genuine spectral selectivity. Double- and triple-silver stacks are how modern facade glass reaches LSG values approaching 2.
- **Fragile.** Most soft coats must be **enclosed in an insulating glass unit or laminated** to survive; exposed soft coats oxidise and degrade.
- **Handling constraints.** Edge deletion is required around the perimeter for sealant adhesion in an IGU; storage life before assembly is limited; "temperable" versions exist but must be specified as such.

Manufacturer families to recognise: Guardian **SunGuard** (commercial) and **ClimaGuard** (residential); AGC **Stopray**, **ipasol**, **Sunergy**, **Planibel**, **iplus**; Saint-Gobain **COOL-LITE** and **PLANITHERM**; Pilkington **Suncool**, **Optitherm**, **Eclipse**. PFG's own coated laminate ranges are **SolarVue** (embedded metallic coating, medium-to-high light transmission, HL and XHL densities) and **Solarshield** (high-performance, high-reflectance, S10/S20/S30 densities).

### Coating surface position

Surfaces are numbered from the outside inwards: **#1** outboard face, **#2** inboard face of the outer lite, **#3** outboard face of the inner lite, **#4** interior face.

- **Solar control coating → surface #2.** Reject radiation before it enters the cavity.
- **Low-E for heating-dominated climates → surface #3.** Keep interior long-wave heat inside.
- In a **cooling-dominated** climate the solar control function on #2 dominates; a combined solar-control low-E on #2 is the standard answer.
- Surface #4 low-E coatings (exposed to room air) exist for U-value improvement on single glazing but are vulnerable to cleaning damage.

## 3. Insulating glass units (IGUs)

An IGU is two (or three) lites separated by a spacer and hermetically sealed.

- **Glass** typically **3–10 mm** per lite.
- **Spacer** — traditionally aluminium (highly conductive, causes an edge cold-bridge and condensation line), now increasingly **warm-edge**: stainless steel, thermoplastic (TPS), or composite/polymer.
- **Desiccant** fills or is contained in the spacer to absorb the moisture trapped at assembly and prevent internal condensation.
- **Primary seal** — **polyisobutylene (PIB)**, the gas and vapour barrier. This is what actually keeps argon in and water vapour out.
- **Secondary seal** — **polysulphide, silicone or polyurethane**, applied around the outside of the spacer to carry the structural load and restrain the primary seal. **Silicone** is mandatory where the unit is structurally glazed or exposed to UV at the edge, because polysulphide and polyurethane degrade under UV.
- **Gas fill** — argon has **67%** the thermal conductivity of air and is cheap; krypton is about **half** the conductivity of argon but expensive, and is used mainly where the cavity must be narrow (10–12 mm).
- **Cavity width** — maximum efficiency at **16–19 mm** at the centre of the unit. Wider cavities lose performance to convection.

Indicative thermal performance: single pane around R-1; standard double glazing with air about **RSI 0.35 m²·K/W**; double glazing with argon around R-3; high-performance triple glazing can reach much higher values.

**EN 1279** is the IGU standard, in six parts: Part 1 generalities and tolerances, Part 2 moisture penetration, Part 3 gas leakage rate and gas concentration tolerances, Part 4 edge seal component test methods, Part 5 product standard, Part 6 factory production control.

> ⚠️ **IGUs are a maintenance liability in a remote hot climate.** Edge seals fail; when they do the unit fogs internally and the only remedy is replacement of the whole unit. Extreme temperature cycling and high UV accelerate this. Before specifying IGUs for a project far from a processor, weigh them against a single-glazed pyrolytic low-E laminate, which gives most of the solar benefit, a real if smaller U-value benefit, and no sealed cavity to fail.

Also watch **altitude**: units assembled at one altitude and installed at a very different one experience cavity pressure differences that bow the glass and stress the seal. Capillary breather tubes (sealed after installation) are the standard mitigation for large altitude changes — relevant for units made at the coast and installed on the Khomas Highland.

## 4. Acoustic glass

Sound reduction through glazing improves with mass, with asymmetry (different thicknesses either side of a cavity), with wide airspaces, and with damping interlayers. PFG's published indicative Rw data:

| Configuration | Make-up | Rw (dB) |
|---|---|---|
| Monolithic float | 3 mm | 28 |
| | 6 mm | 31 |
| | 10 mm | 35 |
| | 19 mm | 40 |
| PVB laminated | 6.38 (3/0.38/3) | 33 |
| | 8.38 (4/0.38/4) | 34 |
| | 12.38 (6/0.38/6) | 37 |
| | 13.52 (6/1.52/6) | 39 |
| Acoustic PVB | 6.50 (3/0.50/3) | 35 |
| | 12.50 (6/0.50/6) | 38 |
| IGU | 14 mm (4/6as/4) | 29 |
| | 24 mm (6/12as/6) | 34 |
| | 31 mm (6/19as/6) | 37 |
| | 28 mm (6/12as/10) | 38 |
| Laminated IGU | 25.52 (7.52/12as/6) | 38 |
| | 28.76 (10.76/12as/6) | 39 |
| Acoustic laminated IGU | 24.50 (6.50A/12as/6) | 41 |
| | 28.50 (8.50A/12as/8) | **44** |

Two lessons stand out. **A plain IGU is a poor acoustic performer for its cost** — 24 mm IGU (Rw 34) barely beats a 8.38 mm laminate (Rw 34) and loses to a 12.38 laminate (Rw 37). **Asymmetry plus an acoustic interlayer is what works**: 8.50A/12as/8 reaches Rw 44.

## 5. Self-cleaning, switchable and other functional glasses

**Self-cleaning** glass (Pilkington Activ, Saint-Gobain Bioclean, AGC Clearsight) carries a pyrolytic titanium dioxide coating on surface #1. It works in two stages: UV light photocatalytically breaks down organic dirt, and the surface is **hydrophilic**, so rain sheets rather than beads and washes the residue away. It needs UV and it needs rain. In a Namibian dust environment with a seven-month dry season, the rain-sheeting stage is unavailable for much of the year and the coating is not a substitute for cleaning access. Specify it, if at all, as a marginal aid — never as a reason to omit facade access provision.

**Electrochromic / switchable glazing** (SageGlass, View) uses a multilayer ceramic stack — SageGlass describes **five layers of ceramic materials** less than 1/50th the thickness of a human hair — through which lithium ions are driven by a **DC voltage of less than 5 V**. The glass darkens; reversing polarity clears it. Absorbed energy is re-radiated outwards from the glass surface. SAGE has been wholly owned by Saint-Gobain since 2012 and manufactures at Faribault, Minnesota. The attraction in a high-glare climate is obvious — dynamic SHGC and glare control without blinds — but cost, control integration, lead time, and the near-total absence of southern African support make it a specialist choice.

**PDLC / privacy glass** (electrically switched liquid-crystal film in a laminate) switches between clear and translucent. It is a **privacy** product, not a solar-control product: it scatters light rather than rejecting energy.

**Applied films** (LLumar, distributed in South Africa within PG Group) retrofit solar control, safety or decorative performance onto existing glazing. **[ZA]** Safety film is covered by **SANS 1263** in the safety-glazing family; film applied to existing annealed glass is a recognised upgrade route but its classification and marking must be checked against the standard — see `05_standards-and-safety.md`.

## 6. Verified PFG performance data (6 mm nominal laminated, single glazed)

All figures below are published by PFG, derived using **NFRC 200-2010** methodology for SHGC and **NFRC 100-2010** for U-value, modelled in LBNL WINDOW/OPTICS from IGDB and South African Glass Data Base (SAGDB) spectral data. **LSG is computed here as VLT ÷ SHGC.**

### Non low-E (U = 5.8 W/m²·K throughout)

| Product | VLT % | SHGC | SC | Tdw-ISO | LSG |
|---|---|---|---|---|---|
| Intruderprufe (clear) | 88 | 0.80 | 0.92 | 63% | 1.10 |
| ColourVue Cool Bronze | 53 | 0.66 | 0.75 | 35% | 0.80 |
| ColourVue Cool Grey | 42 | 0.63 | 0.72 | 32% | 0.67 |
| ColourVue Serene Green | 79 | 0.64 | 0.73 | 56% | **1.23** |
| ColourVue Deep Cool Grey | 20 | 0.53 | 0.60 | 16% | 0.38 |
| ColourVue Shadowlite 10 | 9 | 0.42 | 0.48 | 4% | 0.21 |
| SolarVue HL Neutral | 47 | 0.54 | 0.62 | 35% | 0.87 |
| SolarVue XHL Neutral | 56 | 0.61 | 0.70 | 40% | 0.92 |
| SolarVue HL Serene Green | 42 | 0.47 | 0.54 | 29% | 0.89 |
| SolarVue HL Grey | 24 | 0.47 | 0.54 | 19% | 0.51 |
| Solarshield Silver S10 | 11 | 0.25 | 0.29 | 8% | 0.44 |
| Solarshield Silver S20 | 24 | 0.36 | 0.42 | 18% | 0.67 |
| Solarshield Silver S30 | 35 | 0.45 | 0.52 | 26% | 0.78 |
| Solarshield Grey S10 | 6 | 0.31 | 0.35 | 5% | 0.19 |

### E Range — pyrolytic low-E (U = 3.7 W/m²·K throughout)

| Product | VLT % | SHGC | SC | Tdw-ISO | LSG |
|---|---|---|---|---|---|
| ColourVue Low E Intruderprufe (clear) | 83 | 0.71 | 0.81 | 58% | 1.17 |
| ColourVue Low E Serene Green | 74 | 0.54 | 0.62 | 51% | **1.37** |
| ColourVue Low E Cool Bronze | 52 | 0.56 | 0.64 | 35% | 0.93 |
| ColourVue Low E Cool Grey | 40 | 0.52 | 0.60 | 29% | 0.77 |
| ColourVue Low E Deep Cool Grey | 19 | 0.41 | 0.48 | 14% | 0.46 |
| SolarVue Low E HL Neutral | 43 | 0.43 | 0.49 | 31% | 1.00 |
| SolarVue Low E XHL Neutral | 54 | 0.51 | 0.59 | 38% | 1.06 |
| SolarVue Low E HL Serene Green | 40 | 0.36 | 0.41 | 28% | **1.11** |
| SolarVue Low E XHL Serene Green | 46 | 0.40 | 0.46 | 32% | **1.15** |
| SolarVue Low E HL Bronze | 26 | 0.36 | 0.42 | 18% | 0.72 |
| Solarshield Low E Silver S10 | 9 | 0.19 | 0.21 | 7% | 0.47 |
| Solarshield Low E Silver S20 | 24 | 0.29 | 0.33 | 18% | 0.83 |
| Solarshield Low E Silver S30 | 34 | 0.37 | 0.43 | 25% | 0.92 |
| Solarshield Low E Grey S20 | 13 | 0.27 | 0.31 | 10% | 0.48 |

## 7. Worked selection: north-facing glazing at ~18°S

**Situation.** An air-conditioned office, north elevation, at roughly 18°S. Noon sun altitude ranges from about 48.6° (June) to about 84.6° (December). A horizontal overhang or a projecting slab edge intercepts the near-vertical summer sun very effectively; winter sun at 48.6° penetrates deep, which in an air-conditioned building is an unwanted load rather than a welcome one.

**Step 1 — geometry first.** A 1.0 m overhang above a 2.4 m head height cuts summer noon radiation almost entirely and still admits winter noon sun. If the brief is pure cooling, extend the overhang or add a horizontal louvre blade set; if there is a genuine winter heating season (interior highlands), the seasonal asymmetry is a feature, and the glass should not be so dark that it fights it.

**Step 2 — set the SHGC target.** Behind effective external shading, north glazing does not need extreme solar control. A target SHGC of **0.35–0.50** with VLT above **40%** is the right envelope.

**Step 3 — compare candidates.**

| Candidate | VLT | SHGC | U | LSG | Verdict |
|---|---|---|---|---|---|
| Intruderprufe clear 6.38 | 88 | 0.80 | 5.8 | 1.10 | Too much heat unless shading is very deep |
| ColourVue Low E Serene Green | 74 | 0.54 | 3.7 | 1.37 | Excellent daylight, best selectivity in the range; good with deep shading |
| SolarVue Low E XHL Serene Green | 46 | 0.40 | 3.7 | 1.15 | **Best all-round choice** — hits the SHGC target with usable daylight and the low U |
| SolarVue Low E HL Serene Green | 40 | 0.36 | 3.7 | 1.11 | Choose if shading is shallow or the cooling plant is tight |
| Solarshield Low E Silver S20 | 24 | 0.29 | 3.7 | 0.83 | Lowest SHGC but VLT 24% is gloomy and the mirror finish is a neighbour problem |

**Selection: SolarVue Low E XHL Serene Green** — SHGC 0.40, VLT 46%, U 3.7 W/m²·K, SC 0.46, Tdw-ISO 32%. It is single-glazed, laminated (therefore a safety glass), and has no sealed cavity to fail.

## 8. Worked selection: west-facing glazing at ~18°S

**Situation.** Same building, west elevation. This is the hard case. In midsummer the late-afternoon sun is at low altitude and its azimuth swings *south of due west*, so it strikes a west facade nearly perpendicular at the hottest hour of the day, and horizontal shading is useless against it.

**Step 1 — accept that glass cannot solve this.** The hierarchy is: reduce the glazed area; add **vertical** fins or a deep external screen; only then select glass. If the elevation is fully glazed and unshaded, no product in the PFG range will produce a comfortable, economical result.

**Step 2 — set a harder target.** SHGC **≤ 0.30**, and accept a VLT penalty, but hold VLT above about 20% or the space becomes dependent on artificial light at exactly the wrong time of day.

**Step 3 — compare.**

| Candidate | VLT | SHGC | U | LSG | Verdict |
|---|---|---|---|---|---|
| SolarVue Low E HL Serene Green | 40 | 0.36 | 3.7 | 1.11 | Misses the SHGC target; acceptable only with good vertical shading |
| Solarshield Low E Silver S20 | 24 | 0.29 | 3.7 | 0.83 | **Meets the target**; strong exterior reflectance |
| Solarshield Low E Serene Green S20 | 22 | 0.27 | 3.7 | 0.81 | **Meets the target**, greener and less mirror-like from outside |
| Solarshield Low E Grey S20 | 13 | 0.27 | 3.7 | 0.48 | Same SHGC as above at half the daylight — worse choice |
| Solarshield Low E Silver S10 | 9 | 0.19 | 3.7 | 0.47 | Lowest SHGC available, but VLT 9% is a dark mirror |

**Selection: Solarshield Low E Serene Green S20** — SHGC 0.27, VLT 22%, U 3.7, SC 0.31, Tdw-ISO 16%. Note that its LSG (0.81) is markedly worse than the north-facing choice; that is the honest cost of a west facade and it should appear in the design report rather than being hidden.

**Step 4 — check thermal stress.** Both candidates are strongly absorbing coated laminates on a facade that will see extreme temperature swings and, if there is any vertical shading, shadow lines cutting across panes. That combination requires **heat-strengthened or toughened plies**, ground or polished edges, and a thermal-stress analysis. See `03_structural-glass-and-facades.md`.

**Step 5 — check reflectance.** High-reflectance products throw glare and heat onto neighbours and streets. Check exterior visible reflectance and the sun path against adjacent buildings before committing to an S10 or S20 silver.

## 9. Rules of thumb

1. **SHGC before U-value** in a cooling-dominated climate; **both** if there is a real winter.
2. **LSG above 1.0** unless the elevation genuinely demands darkness.
3. **Green body tint plus pyrolytic low-E** is the best value-for-selectivity combination in the current PFG single-glazed range.
4. **Never solve a west facade with glass alone.**
5. **Every absorbing glass is a thermal-stress candidate** — heat-treat it and finish the edges.
6. **A single-glazed pyrolytic low-E laminate beats an IGU** for remoteness, maintainability and safety compliance in one product; an IGU beats it on absolute thermal and acoustic performance.
7. **Get the data sheet for the exact make-up you are buying.** The tables above are 6 mm nominal, single-glazed centre-of-glass values. Change the thickness, add a second lite, or change the coating surface and the numbers change.

## Sources

- [PFG Laminates brochure rev 8, Oct 2016 (PDF)](http://pfg.co.za/wp-content/uploads/2016/10/PFG-laminates-brochure-rev8-October-2016.pdf) — PFG Building Glass (all PFG performance tables, Rw data, SC definition and NFRC/IGDB/SAGDB methodology)
- [Insulated glazing](https://en.wikipedia.org/wiki/Insulated_glazing) — Wikipedia (IGU construction, spacers, seals, gas fill, cavity optimum)
- [Low-emissivity](https://en.wikipedia.org/wiki/Low-emissivity) — Wikipedia (emissivity of uncoated glass, pyrolytic vs sputtered)
- [Solar gain](https://en.wikipedia.org/wiki/Solar_gain) — Wikipedia (SHGC, g-value, shading coefficient definitions and ranges)
- [SAGE Electrochromics](https://en.wikipedia.org/wiki/SAGE_Electrochromics) — Wikipedia (electrochromic construction, voltage, ownership)
- [Guardian Glass — glass types](https://www.guardianglass.com/us/en/our-glass/glass-types) — Guardian Glass
- [Guardian Glass — Glass Analytics](https://www.guardianglass.com/us/en/tools-and-resources/tools/glass-analytics) — Guardian Glass (performance calculation tool)
- [AGC Glass Europe — brands and configurator](https://www.agc-yourglass.com/) — AGC
- [Pilkington — architectural products](https://www.pilkington.com/en/gbl) — NSG/Pilkington
- [EN 1279 parts, catalogue entries](https://www.en-standard.eu/search/?q=EN+1279) — en-standard.eu

## Open questions

- The PFG performance tables date from the October 2016 brochure. Product availability, coating densities and data may have changed; request current data sheets from PFG technical services before specifying.
- **No verified southern African data was obtained for double-glazed (IGU) make-ups using PFG coated products.** The Rw table includes IGUs, but SHGC/U-value data for IGU make-ups is not reproduced here because it was not sourced. Do not extrapolate single-glazed centre-of-glass values to IGUs.
- Emissivity values for specific pyrolytic and sputtered coatings were not obtained from manufacturer literature; the 0.1–0.2 / 0.03–0.05 ranges given are indicative industry figures and should be verified per product.
- Coating surface conventions (#1–#4) are standard practice but were not verified from a cited document in this pass.
- Self-cleaning coating performance in a high-dust, low-rainfall environment is asserted from first principles, not from tested data.

