---
id: glass.overview
title: Glass and facades — domain overview
domain: 08_glass_and_facades
tags: [glass, glazing, facade, curtain-wall, solar-control, shgc, u-value, southern-africa, namibia, sans-10400-n]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "PFG Laminates brochure (rev 8, October 2016)", url: "http://pfg.co.za/wp-content/uploads/2016/10/PFG-laminates-brochure-rev8-October-2016.pdf", publisher: "PFG Building Glass (PG Group)", accessed: 2026-08-25}
  - {title: "PFG — Float Glass product page", url: "https://pfg.co.za/product/float-glass/", publisher: "PFG Building Glass", accessed: 2026-08-25}
  - {title: "Glazing — SANS 10400 Part N", url: "https://sans10400.co.za/glazing/", publisher: "sans10400.co.za (unofficial commentary on the National Building Regulations)", accessed: 2026-08-25}
  - {title: "Key data — the European flat glass sector", url: "https://glassforeurope.com/the-sector/key-data/", publisher: "Glass for Europe", accessed: 2026-08-25}
  - {title: "Solar gain — SHGC, g-value and shading coefficient", url: "https://en.wikipedia.org/wiki/Solar_gain", publisher: "Wikipedia", accessed: 2026-08-25}
related: [glass.types_manufacture, glass.performance_coatings, glass.structural_facades, glass.installation_detailing, glass.standards_safety, glass.projects, glass.suppliers_southern_africa, glass.specifying]
unit_system: SI
---

# Glass and facades — domain overview

**Summary.** This domain covers architectural glass end to end: how it is made, how it is heat-treated and laminated, what its optical and thermal performance numbers mean, how it is carried in facades and structures, how it is installed and detailed, which standards govern it in southern Africa, what the landmark projects teach, and who actually supplies it in South Africa and Namibia. The governing design problem for this knowledge base is a hot, high-solar-radiation, low-humidity climate at roughly 17–23°S, where glass is simultaneously the most desirable and the most expensive-to-run element of the envelope. The central discipline is trading **visible light transmittance (VLT)** against **solar heat gain coefficient (SHGC)** and **U-value** with real, published product data — never with assumed numbers.

## Key facts

| Item | Value | Source |
|---|---|---|
| Dominant regional float glass maker | **PFG Building Glass**, Springs, Gauteng — part of PG Group **[ZA]** | PFG |
| PFG float output | approx. **260 000 tonnes/year**, two float lines running 365 days/year | PFG laminates brochure |
| PFG ClearVue float thickness range | **1.8 mm to 12 mm** | PFG product page |
| PFG standard float stock sheet | **3 660 × 2 440 mm** | PFG product page |
| Standard laminated sheet ceiling | **3 660 × 2 440 mm**; Low-E laminates standardise at **3 210 × 2 250 mm** | PFG laminates brochure |
| Reference glass for shading coefficient | 3 mm clear float, **SHGC 0.867**, therefore SC = SHGC ÷ 0.867 | PFG laminates brochure |
| Single-glazed laminated U-value, no coating | **5.8 W/m²·K** | PFG laminates brochure |
| Single-glazed laminated U-value, pyrolytic low-E | **3.7 W/m²·K** | PFG laminates brochure |
| Best SHGC in PFG single-glazed range | **0.19** (Solarshield Low E S10, Silver / Aquamarine / Blue) at VLT 8–9% | PFG laminates brochure |
| Governing SA glazing code | **SANS 10400-N** (glazing), citing SANS 613, SANS 10137 and SANS 10400-B **[ZA]** | sans10400.co.za |
| SA safety glazing product standard | **SANS 1263 Part 1:2013** (safety glazing materials), **Part 2:2013** (security glazing) **[ZA]** | PFG laminates brochure |
| Fenestration threshold, SANS 10400-XA | up to **15% fenestration area to nett floor area per storey** deemed to comply without calculation **[ZA]** | sans10400.co.za |
| EU flat glass sector, for scale | **10 Mt/yr**, 44 float sites in 12 countries, ~100 000 workers; 80% goes to buildings | Glass for Europe |

> ⚠️ Every performance number in this domain is a *centre-of-glass* figure from a manufacturer's published data unless stated otherwise. Whole-window U-values including frame and edge effects are always worse. Do not quote a centre-of-glass U-value as a window U-value in a compliance submission.

## Files in this domain

| File | Covers |
|---|---|
| `01_glass-types-and-manufacture.md` | Float process, annealed / heat-strengthened / toughened, laminated and interlayers, wired, patterned, low-iron, mirror; thicknesses, sizes, cutting, edgework, nickel sulphide and heat soaking |
| `02_performance-and-coatings.md` | Hard vs soft coat low-E, solar control, IGU construction, acoustic, self-cleaning, electrochromic; U-value / SHGC / VLT / LSG / SC and how to trade them; worked selection examples at ~18°S |
| `03_structural-glass-and-facades.md` | Curtain wall typologies, facade engineering, wind load and thickness, deflection, thermal breakage, movement, floors, stairs, balustrades, fins, bolted fixings |
| `04_glazing-installation-and-detailing.md` | Setting blocks, edge clearance and bite, tapes and gaskets, wet vs dry glazing, silicone selection and compatibility, frame materials, thermal breaks, water management, handling and site method |
| `05_standards-and-safety.md` | SANS 10400-N, SANS 613, SANS 10137, SANS 1263, EN and ASTM equivalents, critical locations, marking, human-impact classification |
| `06_landmark-glass-projects.md` | Instructive projects with verified facts, including South African towers |
| `07_suppliers-southern-africa.md` | PG Group and PFG, processors, aluminium systems houses, and the Namibian reality |
| `08_specifying-glass.md` | Schedule format, what a specification must state, lead times, reusable template |

## How to reason about glass in a hot, high-solar-radiation climate

### 1. Start from the radiation, not from the aesthetic

At roughly 18°S the geometry is unforgiving and it is *not* the northern-hemisphere problem inverted with a sign change. Solar noon altitude is `90° − |latitude − declination|`:

- **June solstice** (declination +23.44°): noon altitude ≈ **48.6°**, sun to the **north**.
- **Equinox** (declination 0°): noon altitude ≈ **72°**, sun to the **north**.
- **December solstice** (declination −23.44°): noon altitude ≈ **84.6°**, and the sun is *south* of the zenith at noon.

Two consequences follow directly and they drive most of the design:

1. **The sun passes overhead twice a year** at this latitude (whenever declination equals −18°, i.e. in the weeks around late November and late January). Summer solar noon is near-vertical. A horizontal overhang is therefore extremely effective on north-facing glass in summer and progressively less so as the sun swings north in winter.
2. **In midsummer the low-altitude morning and afternoon sun swings south of due east and due west.** East, west and south-west glazing receives long, low-angle, high-intensity radiation that no practical horizontal overhang can intercept. This is the opposite of the intuition an architect trained in Europe brings.

The ranking of facade orientations by difficulty at ~18°S is therefore: **west and south-west worst, east next, north manageable with geometry, south easiest.** Vertical fins, deep reveals, screens or an outright reduction in glazed area are the only reliable answers on west elevations. Glass selection alone cannot fix a west facade.

### 2. Shade first, then select glass, then glaze

The correct order of operations is:

1. **Reduce the area.** Glazing is the weakest thermal element in the envelope. SANS 10400-XA's deemed-to-satisfy threshold of 15% fenestration to nett floor area per storey **[ZA]** is a sensible discipline even where it is not being applied for compliance.
2. **Shade externally.** External shading intercepts radiation before it is absorbed; internal blinds re-radiate heat that is already inside, and actively *increase* thermal-stress breakage risk on the glass.
3. **Then select the glass** on SHGC and light-to-solar-gain ratio.
4. **Then detail the glazing** so the unit survives thermal movement, wind and water.

### 3. Understand which number you are actually optimising

- **VLT** — fraction of visible light transmitted (380–780 nm). Drives daylight and view.
- **SHGC (g-value)** — fraction of total solar energy (300–2500 nm) that ends up inside, including the absorbed fraction re-radiated inwards. Drives cooling load. Lower is better in this climate.
- **U-value (W/m²·K)** — conducted heat flow. Matters most at night and in the cold interior highlands winter; matters far less than SHGC for a Namibian summer cooling load.
- **Light-to-solar-gain ratio (LSG = VLT ÷ SHGC)** — the efficiency metric. It tells you how much daylight you buy per unit of heat. A high LSG glass gives a bright, cool building; a low LSG glass gives a dark, hot one.
- **Shading coefficient (SC)** — legacy metric, `SC = SHGC ÷ 0.867`. Still quoted in southern African product literature, so you must be able to convert.

The classic error in this climate is to specify a **dark or heavily mirrored glass**. Deep tints and high-reflectance silver coatings cut SHGC but cut VLT harder, so LSG collapses, the interior goes gloomy, the artificial lighting load rises, and the lighting load reappears as cooling load. The better move is a **spectrally selective coating** — high VLT, low SHGC — which in the PFG single-glazed range means a body-tinted or coated laminate combined with a pyrolytic low-E surface (see `02_performance-and-coatings.md` for the worked comparison, where a green-tinted low-E laminate reaches **LSG 1.37** against **0.44** for a mirror-finish S10).

### 4. Respect the thermal stress problem

Hot climate plus absorbing (tinted or coated) glass plus partial shading is exactly the recipe for **thermal stress breakage**: the sunlit centre of a pane expands while the framed, shaded edge stays cool, and the tensile stress at the edge exceeds the (much weaker) edge strength of annealed glass. Risk factors are cumulative: tinted or spectrally selective glass absorbs more; internal blinds reflect heat back into the pane; a shadow line cutting across the pane creates the worst gradient; heavy framing with high heat capacity holds the edge cold. The remedy is heat-strengthened or toughened glass, clean edgework, and avoiding shadow patterns that cover less than about half a pane. This is dealt with in `03_structural-glass-and-facades.md`.

### 5. Assume the supply chain is long

There is one float glass producer of scale in the region — PFG at Springs, Gauteng. Everything else is processing (toughening, lamination, IGU assembly, coating) or distribution. For a Namibian project this means:

- **Stock sizes govern.** Design to the standard sheet (3 660 × 2 440 mm, or 3 210 × 2 250 mm for low-E laminates) and you buy from stock. Design past it and you buy made-to-order at a lead-time and cost penalty.
- **Toughening and IGU assembly capacity is the constraint,** not the glass itself.
- **Replacement glass is a project risk.** A single broken 12 mm toughened unit in a curtain wall in northern Namibia is a multi-week problem. Specify accordingly, and consider ordering spare panes with the original batch — coating batches vary and a later replacement may not colour-match.
- **Verify local capability before specifying.** Namibian coverage is real but thin; see `07_suppliers-southern-africa.md`.

### 6. Safety is not optional and not discretionary

**[ZA]** SANS 10400-N and SANS 613 make safety glass mandatory in defined critical locations — doors and sidelights, low sills, bathrooms and shower enclosures, balustrades, and low-level partitions. **[NA]** Namibia's regulatory position is dealt with, with its uncertainties flagged, in `05_standards-and-safety.md`. In practice southern African specifiers write to the SANS suite in both countries, and PFG's safety products carry the SABS mark under SANS 1263 Part 1:2013.

## How an agent should use this domain

- For a **material question** ("what is heat-strengthened glass?") go to `01`.
- For a **number** (U-value, SHGC, VLT of a named product) go to `02`, which carries the verified PFG data tables.
- For a **facade system or engineering** question go to `03`.
- For a **site or trade** question go to `04`.
- For a **compliance** question go to `05` — and check the confidence flags, because several SANS clause references in circulation are second-hand.
- For **precedent** go to `06`.
- For **who can actually supply it** go to `07`.
- To **write the specification** go to `08`.

## Sources

- [PFG Laminates brochure, rev 8, October 2016 (PDF)](http://pfg.co.za/wp-content/uploads/2016/10/PFG-laminates-brochure-rev8-October-2016.pdf) — PFG Building Glass
- [PFG — Float Glass](https://pfg.co.za/product/float-glass/) — PFG Building Glass
- [PFG — Manufacturing process](https://pfg.co.za/manufacturing-process/) — PFG Building Glass
- [Glazing (SANS 10400 Part N commentary)](https://sans10400.co.za/glazing/) — sans10400.co.za
- [Energy usage (SANS 10400-XA commentary)](https://www.sans10400.co.za/energy-usage/) — sans10400.co.za
- [Key data, European flat glass sector](https://glassforeurope.com/the-sector/key-data/) — Glass for Europe
- [Solar gain](https://en.wikipedia.org/wiki/Solar_gain) — Wikipedia

## Open questions

- The exact clause numbering of SANS 10400-N:2012 has not been read from the standard itself; the requirements summarised here come from published commentary. Treat clause citations as indicative until the purchased standard is checked.
- Namibia's adoption status of the SANS suite for glazing is not verified — see `05_standards-and-safety.md`.
- Latitude-specific solar geometry above is computed from the standard solar-noon relation, not taken from a published table; verify against site-specific solar data before using it for a shading design.

