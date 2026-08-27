---
id: paving.fundamentals
title: Pavement engineering fundamentals — how a pavement carries load
domain: 17_paving_and_roads
tags: [pavement-design, cbr, e80, esal, subgrade, subbase, base-course, trh4, trh14, samdm, flexible-pavement, rigid-pavement, block-pavement, failure-modes, drainage]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Pavement analysis and design software (PADS) based on the South African mechanistic-empirical design method (Theyse & Muthen, SATC 2000)", url: "https://repository.up.ac.za/server/api/core/bitstreams/892f7909-5ee9-4d95-9e6d-4ac069b9cc55/content", publisher: "CSIR Transportek / University of Pretoria repository", accessed: 2026-08-25}
  - {title: "Concrete Block Paving Book 2 — Design Aspects", url: "https://www.cma.org.za/publications/paving/", publisher: "Concrete Manufacturers Association of Southern Africa", accessed: 2026-08-25}
  - {title: "Some aspects of the structural design of segmental block pavements in Southern Africa (Clifford, D.Ing thesis, 1984)", url: "https://repository.up.ac.za/server/api/core/bitstreams/3827905e-d65f-4ab8-b185-81a362ec7849/content", publisher: "University of Pretoria", accessed: 2026-08-25}
  - {title: "California bearing ratio", url: "https://en.wikipedia.org/wiki/California_bearing_ratio", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "The use of gravel loss predicting models for effective management of gravel roads (Mwaipungu, SATC 2012)", url: "https://repository.up.ac.za/server/api/core/bitstreams/485fb687-4ce6-4a00-b9b6-59f28e18cddc/content", publisher: "University of Pretoria repository", accessed: 2026-08-25}
  - {title: "Gypsum in saline and non-saline road bases (Netterberg, SATC 2021)", url: "https://repository.up.ac.za/server/api/core/bitstreams/913edaa5-b899-4e16-bb0d-a3df23312e1f/content", publisher: "University of Pretoria repository", accessed: 2026-08-25}
  - {title: "Drainage of Concrete Block Paving (CMA technical note)", url: "https://www.cma.org.za/publications/paving/", publisher: "Concrete Manufacturers Association", accessed: 2026-08-25}
related: [paving.overview, paving.standards, paving.block_paving, paving.namibia_roads]
paywalled: false
unit_system: SI
---

# Pavement engineering fundamentals — how a pavement carries load

**Summary.** A pavement is a load-spreading machine. A wheel applies roughly 500–800 kPa over a contact patch the size of a dinner plate; the subgrade underneath can usually tolerate 20–100 kPa. The pavement's whole job is to reduce the stress by a factor of ten or more over 300–800 mm of depth, and to keep doing it for 10⁵ to 10⁸ load repetitions without accumulating unacceptable permanent deformation. It does this with a layered structure in which each layer is stiffer than the one below and stresses spread through it in a cone. Everything else in pavement engineering — CBR, E80s, material classes, catalogues, mechanistic analysis — is bookkeeping around that one idea. And in practice, the thing that kills pavements is not under-design of the layers: it is water.

## Key facts

| Quantity | Typical value | Note |
|---|---|---|
| Tyre contact pressure, standard design wheel | ~520 kPa | 40 kN dual wheel, 80 kN axle = 1 E80 |
| Standard axle | 80 kN (8,2 t) | The E80; all traffic converted to E80s |
| Damage law exponent | ~4 | Doubling axle load ≈ 16× the damage |
| Stress at top of subgrade under a designed pavement | 20–80 kPa | Down from ~520 kPa at the surface |
| Depth to which heavy traffic is felt | up to ~1 m | CMA Book 2 |
| Elastic deflection, block pavement under truck | up to 2 mm or more | Tolerable because the surface is jointed |
| Minimum crossfall, block paving | 2 % in any direction | CMA / SANS 1200 MJ |
| Minimum longitudinal fall, top of subbase | 1 % | SANS 1200 MJ 5.1.1.3 |
| Design reliability by road category | A 95 %, B 90 %, C 80 %, D 50 % | TRH 4 (1996) |

> ⚠️ **Most pavement failures are water failures.** The CMA states it plainly: "Most failures of pavements are due to ingress of water into the pavement layerwork." Between 30 % and 35 % of rainfall penetrates newly laid, untrafficked, unsealed block paving. A pavement that is 20 % thin but perfectly drained will usually outlive one that is correctly designed and ponds.

## The layer system

From the bottom up, with the names used in southern Africa:

1. **In-situ subgrade** — the natural ground, prepared and compacted. Characterised by soaked CBR. Classed G7 (CBR ≥ 15) through G10 (CBR ≥ 3).
2. **Selected layer(s)** — imported or improved material placed to raise the effective bearing capacity of poor subgrade, usually 150 mm layers of G7/G9.
3. **Subbase** — the main load-spreading course; G5/G6 natural gravel or C3/C4 lightly cemented gravel, 100–200 mm.
4. **Base** — the stiffest unbound or bound course, carrying the highest stresses below the surface: G1/G2 crushed stone, C1/C2 cemented, or bituminous. **In a block pavement the blocks themselves are the base course** — the CMA is explicit that blocks "form the base course as well as the surface wearing course".
5. **Surfacing** — the wearing course and the waterproofing layer: a surface seal (single/double/Cape/slurry), asphalt, concrete, or in block paving the blocks plus jointing sand.

Load spreads through this stack in an approximate cone. That is why layer *order* is non-negotiable: a stiff layer over a weak one bends and cracks; a weak layer over a stiff one is punched. It is also why the **balance** of the structure matters more than any single thickness. A 150 mm G1 base over a soft subgrade is worse than 125 mm G2 over a properly built selected layer.

## Flexible, rigid and block pavements

- **Flexible.** Granular or bituminous layers; load spread by particle interlock and layer stiffness; deflects under load and recovers. Fails by rutting (permanent shear deformation in the layers) and by fatigue cracking of bound layers. This is the dominant pavement type in southern Africa.
- **Rigid.** A concrete slab whose flexural stiffness carries the load in bending over a wide area; the subbase mostly prevents pumping and provides uniform support. Fails by slab cracking, joint faulting and pumping of fines through joints. Expensive to build, cheap to maintain, unforgiving of poor jointing.
- **Block (segmental).** Discrete units on 25 mm of sand. Behaves like a flexible pavement but with two peculiarities: it tolerates very large transient deflections without cracking, because a jointed surface cannot crack; and it **stiffens under traffic** as the joints fill and the blocks rotate into contact — the "lock-up" or progressive stiffening effect. Clifford (1984) distinguishes true geometric interlock in the horizontal plane (which requires an edge restraint) from lock-up, which is a whole-pavement stiffening phenomenon and is contingent on construction quality and on the subbase being stiff enough to let the block layer develop confinement.

## Traffic: E80s and traffic classes

All traffic is converted to **equivalent standard 80 kN axles (E80s)** using a fourth-power damage law, and summed over the structural design period (usually 20 years) for the design lane. TRH 4 road categories carry an approximate design reliability:

| Category | Description | Reliability |
|---|---|---|
| A | Interurban freeways and major interurban roads | 95 % |
| B | Interurban collectors and major rural roads | 90 % |
| C | Rural roads | 80 % |
| D | Lightly trafficked rural roads | 50 % |

Traffic classes used in the block-paving catalogue (UTG 2), cumulative E80s per lane over the structural design period:

| Class | E80s |
|---|---|
| E0 | < 0,2 × 10⁶ |
| E1 | 0,2–0,8 × 10⁶ |
| E2 | 0,8–3 × 10⁶ |
| E3 | 2–12 × 10⁶ |
| E4 | 12–50 × 10⁶ |

A residential driveway is far below E0 — typically a few thousand E80s over its life, and it is the ready-mix truck during construction, not the family car, that governs. This is why residential design is essentially "make it 50–60 mm on 25 mm sand on something firm and drain it".

## CBR and its use

The **California Bearing Ratio** is the load required to push a 50 mm plunger into the compacted, usually 4-day-soaked, specimen at 1,25 mm/min, expressed as a percentage of the load on a standard crushed stone (13,44 kN at 2,5 mm; 20,15 kN at 5,0 mm penetration). It is crude, empirical and correlates only loosely with elastic modulus — and it remains the single most useful number in southern African pavement design because every catalogue is indexed on it.

Indicative CBR by soil type: clay ~2 %; poorly to well-graded sand 7–10 %; well-graded sandy gravel ~15 %; clayey sand 5–20 %; silty gravel 20–60 %; gravel 30–80 %.

For a Kalahari-sand subgrade of the kind found across Ohangwena, expect a soaked CBR in the single digits to low teens depending on fines content and density — comfortably a G9/G8 rather than a G7. The UTG 2 catalogue only accommodates subgrades of CBR 10 % or 15 %, which is exactly the case where a designer must either improve the subgrade with a selected layer or step outside the catalogue.

## Material classifications (TRH 14)

The standard southern African material codes, as tabulated in the SAMDM/PADS documentation:

| Code | Material | Abbreviated specification |
|---|---|---|
| G1 | Graded crushed stone | Dense-graded unweathered crushed stone; max 37,5 mm; 88 % apparent density; PI < 4 |
| G2 | Graded crushed stone | Max 37,5 mm; 100–102 % mod. AASHTO or 85 % bulk density; PI < 6 |
| G3 | Crushed stone + soil binder | Max 37,5 mm; 98–100 % mod. AASHTO; PI < 6 |
| G4 | Natural gravel | CBR ≥ 80; max 53 mm; 98–100 % mod. AASHTO; PI < 6; swell 0,2 % |
| G5 | Natural gravel | CBR ≥ 45; max 63 mm; PI < 10; swell 0,5 % |
| G6 | Natural gravel (subbase quality) | CBR ≥ 25; max 63 mm; PI < 12 or 2(GM)+10; swell 1,0 % |
| G7 | Gravel-soil | CBR ≥ 15 |
| G8 | Gravel-soil | CBR ≥ 10 at in-situ density |
| G9 | Gravel-soil | CBR ≥ 7 at in-situ density |
| G10 | Gravel-soil | CBR ≥ 3 at in-situ density; 90 % mod. AASHTO |
| C1 | Cemented crushed stone | UCS 6–12 MPa at 100 % mod. AASHTO; at least G2 before treatment |
| C2 | Cemented crushed stone | UCS 3–6 MPa; at least G2/G4 before treatment |
| C3 | Cemented natural gravel | UCS 1,5–3,0 MPa, ITS ≥ 250 kPa; max 63 mm; PI ≤ 6 after treatment |
| C4 | Cemented natural gravel | UCS 0,75–1,5 MPa, ITS ≥ 200 kPa; max 63 mm; PI ≤ 6 after treatment |
| BC1/BC2/BC3 | Hot-mix asphalt base | Continuously graded; max 53 / 37,5 / 26,5 mm |
| BS | Hot-mix asphalt base | Semi-gap graded; max 37,5 mm |
| EBM / EBS | Bitumen-emulsion modified/stabilised gravel | 0,6–1,5 % / 1,5–5,0 % residual bitumen |
| S1–S9 | Surface seals | Single, multiple, sand, Cape, slurry (fine/medium/coarse), rejuvenator, diluted emulsion |
| WM1/WM2 | Waterbound macadam | Max 75 mm, PI ≤ 6, 88–90 % / 86–88 % apparent density |
| PPC | Portland cement concrete | Modulus of rupture ≥ 4,5 MPa |

Suggested elastic moduli (MPa) used in mechanistic analysis show how much support state matters: a G1 base is 250–1000 MPa (expected 450) over a cemented layer in slab state, but only 40–200 MPa (expected 200) in a wet condition with poor support. Subgrade moduli run from 30–200 MPa dry for G7 down to 10–45 MPa wet for G10. Poisson's ratio is taken as 0,35 for granular, cemented and subgrade materials.

**[NA]** Namibian materials frequently break these limits. Netterberg's Lüderitz and Haalenberg long-term experiments (1976–2012) showed that gypsum contents up to **10 % in a G3 crushed-stone base and at least 5 % in a G4 calcrete base** can be tolerated for a 30-year, 1,0 × 10⁶ E80 design under a 19 mm Cape seal in an arid environment — against the historical limit of 1,0 % sulfate (1,8 % gypsum) borrowed from concrete practice, later raised to 2,0 % sulfate. Highly soluble salts (NaCl) are a different matter: above ~0,2 % they cause surface disintegration of primed bases and blistering of bituminous surfacings.

## Design methods

1. **Catalogue design (TRH 4, UTG 2).** Classify the road by category, traffic class and climate; read the layer structure off a table. Fast, conservative, and the only method most jobs justify. Its weakness for block paving is that UTG 2 accommodates only CBR 10 % or 15 % subgrades.
2. **Equivalent-thickness substitution.** Treat blocks + bedding sand as equivalent to a thickness of conventional material. Published equivalences vary widely: Argentina 2,5× thickness of granular subbase; Australia 2,1–2,9× crushed rock base and 1,1–1,5× dense-graded asphalt; US Corps of Engineers 165 mm cover or 2–2,85× granular base; UK 225 mm soil-cement or 160 mm rolled asphalt. Useful as a sanity check, not as a design.
3. **Research-based (accelerated trafficking).** Shackel's method, developed at UNSW for the Cement and Concrete Association of Australia (1978, revised 1982 after South African trafficking tests), relating subgrade CBR, block thickness and base thickness to rut depth. Typical tolerable deformations: bus stop 5 mm; city street 5–10 mm; collector street 7–12 mm; rural road 10 mm; residential street 10–15 mm.
4. **The South African Mechanistic-Empirical Design Method (SAMDM).** Model the pavement as a static, linear-elastic multi-layer system; compute critical stresses and strains (maximum horizontal tensile strain at the bottom of asphalt and cemented layers; vertical compressive strain at the top of the subgrade; shear in granular layers); feed them into empirical transfer functions to get a life for each layer; the shortest life governs. Implemented in **PADS** (CSIR Transportek). Approximate design reliability was retrofitted into the distress models so the four TRH 4 road categories could be produced consistently. A known artefact: linear-elastic analysis develops tensile stress in unbound granular layers, which the method suppresses by setting tensile minor principal stress to zero.
5. **Lockpave / Permpave.** Shackel's mechanistic block-pavement design software, distributed in South Africa through the CMA. It analyses an axle-load spectrum rather than using load equivalency, which matters for industrial pavements with mixed wheel loads.

## Failure modes

| Mode | Mechanism | Where it shows |
|---|---|---|
| **Rutting** | Accumulated permanent shear deformation in one or more layers, or densification | Wheel paths; a rut with heave at the edges is a shear failure, a rut without heave is densification |
| **Fatigue cracking** | Repeated tensile strain at the bottom of a bound layer; crocodile/alligator pattern | Wheel paths, working upward |
| **Block/shrinkage cracking** | Thermal and moisture movement in cemented layers reflecting through | Large polygons unrelated to wheel paths |
| **Potholing** | Water enters a crack, base saturates, traffic pumps out fines, the surfacing loses support and punches through | Anywhere water can enter — always secondary to a crack or joint |
| **Pumping** | Free water under a rigid slab or block pavement ejected under load, carrying fines; leads to voids and faulting | Slab joints, manhole surrounds, kerb lines; grey slurry staining |
| **Shoving** | Horizontal displacement of the surface under braking, turning or acceleration | Intersections, gradients, gate approaches; in block paving, creep of blocks downslope |
| **Ravelling / gravel loss** | Loss of surface particles through deficient fines, poor grading or erosion | Unsealed roads; also seals losing chippings |
| **Dishing / settlement** | Local subsidence from a soft spot, a trench, or bedding sand used as a levelling course | Around services, trenches, manholes |

For unsealed roads the controlling parameters are the **Shrinkage Product** (linear shrinkage × % passing 0,425 mm) and the **Grading Coefficient**. Southern African specifications derived from a 1989 performance study of 110 gravel-road sections; the Tanzanian calibration gives max size ≤ 37,5 mm, SP 120–400, GC 16–34, CBR ≥ 25 % at 95 % MDD. Material with GC below 16 is particularly erosion-prone. Traffic compaction alone can consume up to 30 % of the constructed wearing-course thickness soon after construction.

## Drainage, in the detail that matters

- Minimum 2 % fall in any direction on block paving; minimum 1 % longitudinal and 2 % transverse on top of subbase.
- Lay the paving **5–10 mm proud** of channels, gully gratings and manhole covers — it will settle.
- If permissible surface tolerances are allowed, the design fall must be steeper than 1 in 50 or ponding is arithmetically inevitable.
- Where an unbound granular subbase sits under block paving and early-life water ingress is a risk, spray a low-durability bitumen emulsion at ~0,2 ℓ/m² on the subbase surface. The problem is temporary: joints clog with detritus and become effectively impermeable.
- Subsoil drainage is required where the water table is high, and at the low point of any slope where water will collect in the bedding sand.
- Increasing crossfall increases runoff and reduces infiltration; joint permeability can be halved with a water-based acrylic sealer, or inhibited with 10 % lime or 6 % bentonite in the jointing sand.

## Sources

- [PADS and the South African Mechanistic-Empirical Design Method (Theyse & Muthen, SATC 2000)](https://repository.up.ac.za/server/api/core/bitstreams/892f7909-5ee9-4d95-9e6d-4ac069b9cc55/content)
- [Some aspects of the structural design of segmental block pavements in Southern Africa (Clifford, 1984)](https://repository.up.ac.za/server/api/core/bitstreams/3827905e-d65f-4ab8-b185-81a362ec7849/content)
- [CMA Concrete Block Paving Books and technical notes](https://www.cma.org.za/publications/paving/)
- [California bearing ratio](https://en.wikipedia.org/wiki/California_bearing_ratio) — Wikipedia
- [Gravel loss predicting models (Mwaipungu, SATC 2012)](https://repository.up.ac.za/server/api/core/bitstreams/485fb687-4ce6-4a00-b9b6-59f28e18cddc/content)
- [Gypsum in saline and non-saline road bases: Namibian long-term experiments (Netterberg, SATC 2021)](https://repository.up.ac.za/server/api/core/bitstreams/913edaa5-b899-4e16-bb0d-a3df23312e1f/content)

## Open questions

- The full TRH 4 (1996) design catalogue tables could not be retrieved; only the road-category/reliability framework and the UTG 2 block-paving extract were verified. Specific TRH 4 layer thicknesses quoted anywhere should be checked against the document itself.
- SAMDM transfer functions (the actual distress equations and their coefficients) were not obtained and are **needs-verification**.
- Tyre contact pressure of ~520 kPa is the conventional design assumption; the exact value used in current SANRAL practice was not verified.
