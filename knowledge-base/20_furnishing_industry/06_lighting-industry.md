---
id: furnishing.lighting
title: The lighting industry — LED technology, control protocols, specification data and manufacturers
domain: 20_furnishing_industry
tags: [lighting, led, binning, driver, triac, 0-10v, dali, casambi, zigbee, matter, lumens, efficacy, cri, tm-30, macadam, beam-angle, ip-rating, ik-rating, l70, erco, iguzzini, flos, delta-light, zumtobel, artemide, louis-poulsen, eurolux, klight, radiant, regent]
jurisdiction: southern-africa
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Digital Addressable Lighting Interface", url: "https://en.wikipedia.org/wiki/Digital_Addressable_Lighting_Interface", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Color rendering index", url: "https://en.wikipedia.org/wiki/Color_rendering_index", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "IP code", url: "https://en.wikipedia.org/wiki/IP_code", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "ERCO", url: "https://www.erco.com/en/", publisher: "ERCO", accessed: 2026-08-25}
  - {title: "Zumtobel", url: "https://en.wikipedia.org/wiki/Zumtobel", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Artemide", url: "https://en.wikipedia.org/wiki/Artemide", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Louis Poulsen", url: "https://en.wikipedia.org/wiki/Louis_Poulsen", publisher: "Wikipedia", accessed: 2026-08-25}
related: [furnishing.overview, furnishing.appliances, building.electrical]
unit_system: SI
---

# The lighting industry — LED technology, control protocols, specification data and manufacturers

**Summary.** Lighting is the only furnishing category that is simultaneously an electrical installation, an optical instrument and a piece of furniture. A luminaire specification that omits **driver type, dimming protocol, colour temperature, CRI, beam angle and IP rating** is not a specification — it is a picture. The industry splits cleanly into **architectural manufacturers** (who publish photometric files and sell light), **decorative houses** (who sell objects that also emit light), and **importers/distributors** (who sell availability). Southern Africa is served almost entirely by the third group, with the first two reached through agents.

## Key facts

- **DALI** is standardised as **IEC 62386** (previously IEC 60929): typically **16 V DC** bus, current-limited to **250 mA**, **up to 64 control gear** with short addresses 0–63, **16 groups** per device, single twisted pair carrying signal and power, **max ~300 m** cable run. **DALI-2** added standardised control devices (sensors, application controllers), allowing 64 control devices alongside 64 control gear.
- **CRI (Ra)** averages the special rendering indices of **eight moderately saturated test colours (R1–R8)**; **R9 (strong red)** is excluded from Ra but is critical for skin tones and textiles. Standard white LEDs are typically **CRI ≥ 80**; high-CRI variants are claimed to 98. CRI is criticised for spiky LED spectra, and **IES TM-30** (Rf fidelity, Rg gamut) is replacing it among professionals.
- **IP code = IEC 60529**. First digit: 5 = dust-protected, 6 = dust-tight. Second digit: **IPX4** splashing, **IPX5** water jets (6.3 mm nozzle, 12.5 l/min at 30 kPa), **IPX7** immersion. **IK impact ratings are a separate standard, EN 62262.**
- ERCO (Germany) positions itself as "the specialist for LED architectural lighting" — spotlights, downlights, wallwashers, track and 48 V systems, with Casambi Bluetooth control and published lighting design data.
- Zumtobel Group (Dornbirn, Austria) owns **Zumtobel, Thorn and Tridonic**; sales **€1,148.3 m in FY2021/22**; 10 production sites on three continents, sales in ~90 countries.

## 1. LED technology

### The chain
**Die → package (chip) → module/array → luminaire.** Efficacy losses occur at every stage: a chip rated 200 lm/W at the die may deliver **90–130 lm/W at the luminaire** after optics, thermal derating and driver losses. **Always specify luminaire lumens (LOR-inclusive), never chip lumens.**

### Binning
LED chips vary in flux, forward voltage and chromaticity as manufactured, and are sorted into "bins". For interiors what matters is **chromaticity binning**, expressed in **MacAdam ellipses (SDCM — standard deviation of colour matching)**:

| SDCM | Perception | Use |
|---|---|---|
| 1–2 step | Colour difference invisible to almost everyone | Museum, retail, high-end residential, anywhere luminaires sit side by side |
| 3 step | Just perceptible on a white wall wash | Good residential/architectural standard |
| 5 step | Visibly different between fittings | Utility, industrial, budget |
| 7 step+ | Obviously mismatched | Avoid in any visible application |

> ⚠️ Specify **≤ 3 SDCM** for anything wall-washing or in a continuous run, and **buy the whole job from one production batch**. Two "3000 K" downlights from different batches or brands will not match, and there is no fixing it after installation.

### Drivers
| Driver type | Description | Notes |
|---|---|---|
| **Constant current (CC)** | Fixed mA output (350, 500, 700, 1050 mA), variable voltage | Standard for spotlights and modules; the module dictates the current |
| **Constant voltage (CV)** | Fixed 12 V or 24 V, variable current | Standard for LED tape; current regulated on the strip |
| **Integral vs. remote** | Driver inside the luminaire or in a separate enclosure | **Remote drivers are strongly preferred in hot climates** — the driver is the shortest-lived component and needs to be accessible |
| **Programmable / multi-current** | Output set by NFC or DIP | Reduces stockholding |

**Driver life is the real life of the fitting.** Electrolytic capacitors degrade with heat: a typical driver is rated **50,000 h at 25 °C ambient** but far less at 45 °C. **[NA]** In a Namibian ceiling void that reaches 45–55 °C in summer, plan on driver replacement, and therefore on **access**.

### Dimming protocols

| Protocol | Wiring | Where used | Strengths | Weaknesses |
|---|---|---|---|---|
| **TRIAC / leading edge (phase-cut)** | Existing 2-core switch wiring | Retrofit residential | No extra cable; cheap | Flicker, buzz, poor low-end, driver/dimmer compatibility lottery, minimum load issues |
| **Trailing edge (ELV)** | As above | Residential LED | Smoother and quieter than TRIAC | Still compatibility-dependent |
| **0-10 V / 1-10 V analogue** | 2 extra control cores | Commercial | Simple, robust, cheap | No addressing; polarity matters; long runs drop voltage; **1-10 V does not switch off — needs a relay** |
| **DALI / DALI-2 (IEC 62386)** | 2-core polarity-free bus | Commercial and serious residential | Individual addressing, groups, scenes, feedback, sensors (DALI-2), commissioning data | Requires commissioning; 64-device limit per line; needs a competent installer |
| **DALI DT8** | As DALI | Tunable white and RGBW | Colour control within DALI | Gear must support DT8 |
| **DMX512 / RDM** | 5-core or 3-core | Entertainment, façade, colour | Fast, high channel counts | Not designed for building lighting maintenance |
| **Casambi** | Bluetooth mesh, no control wiring | Retrofit and residential architectural | **No control cabling**, phone commissioning, works with ERCO and many others | Proprietary ecosystem; commissioning lives on a device/cloud; mesh range limits |
| **Zigbee** | 2.4 GHz mesh | Philips Hue, smart home | Mature, interoperable within profiles | Hub-dependent, consumer-grade |
| **Matter (over Thread/Wi-Fi)** | IP-based | Smart home convergence | Cross-vendor interoperability, local control | Young; architectural gear support still limited |
| **KNX** | Twisted pair bus | Whole-building European integration | One system for lighting, blinds, HVAC | Expensive, requires certified integrator |

**Selection guidance for a house:**
- Small project, retrofit, no ceiling access: **trailing-edge dimming with tested driver/dimmer pairs**, or **Casambi**.
- New build, architectural lighting, multiple scenes: **DALI-2** (or DALI + KNX if the whole house is integrated).
- Feature/colour work: DMX or DALI DT8.
- Never mix protocols within one circuit, and **never assume compatibility — get the manufacturer's tested dimmer list in writing**.

## 2. Specification data — what a luminaire schedule must contain

| Field | Unit / values | Why it matters |
|---|---|---|
| Luminaire lumen output | lm | The only meaningful output figure |
| Circuit watts | W (including driver) | For load and energy calculations |
| Efficacy | lm/W | 90–130 lm/W typical for good architectural LED |
| Colour temperature (CCT) | 2700 / 3000 / 3500 / 4000 K | **2700 K warm residential; 3000 K the usual architectural default; 4000 K task/utility** |
| Colour consistency | SDCM / MacAdam step | ≤ 3 for visible work |
| CRI / TM-30 | Ra ≥ 90 recommended; **R9 ≥ 50**; TM-30 Rf/Rg | Skin, timber, textiles and food all depend on R9 |
| Beam angle | ° (e.g. 10° spot, 24° narrow flood, 36° flood, 60° wide) | Determines pool size and overlap |
| Photometric file | IES or LDT | Required for any calculation (DIALux, Relux, AGi32) |
| UGR | ≤ 19 for offices | Glare control |
| IP rating | IEC 60529 | IP20 dry interior, **IP44 bathroom zone 2**, IP65 external/wash-down, IP67/68 in-ground |
| IK rating | EN 62262, IK02–IK10 | Public and external areas |
| L70/L80 at Ta | e.g. **L80B10 50,000 h at 25 °C** | Lumen maintenance, not "lifetime" |
| Ambient temperature rating (Ta) | °C | **Critical in Namibia — check Ta 40 °C or 45 °C ratings** |
| Dimming protocol | See table above | |
| Mounting and cut-out | mm | Coordinate with ceiling build-up |
| Finish/RAL | | |
| Emergency/backup | Where required | |

**L70/L80/L90 explained:** L70 = the point at which output has fallen to 70 % of initial. Bxx is the failure fraction (B10 = 10 % of units below the L-value). "50,000 hours" alone is marketing; "**L80B10 50,000 h at Ta 40 °C**" is a specification.

**Lighting levels (indicative design targets, `needs-verification` against SANS 10114 / EN 12464):**

| Space | Maintained illuminance (lux) |
|---|---|
| Living room general | 100–200 (plus task) |
| Kitchen worktop | 300–500 |
| Dining table | 150–300 (dimmable) |
| Bathroom mirror (vertical on face) | 300–500 |
| Dressing room / wardrobe | 300, CRI ≥ 90 |
| Study/home office task | 500 |
| Corridors/stairs | 100–150 |
| External path | 20–50 |

## 3. Luminaire types

| Type | Purpose | Notes |
|---|---|---|
| **Downlight** | General/ambient from the ceiling | Beware "downlight-only" schemes: they light floors and heads, not faces or walls |
| **Wallwasher** | Even vertical illumination of a wall | **The single highest-value architectural fitting** — makes a room feel bright at low power |
| **Spotlight / track spot** | Accent, art, objects | Aim at 30° from vertical to avoid reflected glare |
| **Track systems (mains, 48 V low-voltage)** | Reconfigurable accent | ERCO, Flos and Delta Light all offer 48 V magnetic systems |
| **Linear / profile (recessed, surface, suspended)** | Continuous lines, cove | Specify diffuser type and joint detail |
| **LED tape in profile** | Cove, under-cabinet, shelf | **Always in an aluminium profile** (heat sink) with a diffuser; specify tape density (≥ 120 LED/m to avoid dotting) and CRI |
| **Pendant / suspension** | Decorative + task over tables | Bottom of shade ~750–850 mm above a dining table |
| **Wall light / sconce** | Vertical accent, corridors | |
| **Floor and table lamps** | Layer 3 — the human-scale layer | Often forgotten in specification and left to the client |
| **Step/marker/in-ground** | External and stairs | IP67 minimum in ground; drainage matters more than IP |
| **Bollard / façade / landscape** | External | IK rating and light-pollution control (upward light ratio) |

## 4. The architectural manufacturers

| Maker | Country | Known for |
|---|---|---|
| **ERCO** | Germany | Optical precision, wallwashing, museum/gallery lighting, 48 V track, Casambi integration, exhaustive design data |
| **iGuzzini** | Italy | Architectural and urban lighting, museum work |
| **Flos Architectural** (formerly Antares/Ilti Luce) | Italy | Architectural arm of Flos; recessed and minimal |
| **Delta Light** | Belgium | Design-forward architectural range |
| **Zumtobel** | Austria | Professional indoor/outdoor systems; group includes Thorn (outdoor/utility) and Tridonic (drivers and components) |
| **Reggiani** | Italy | Retail and museum spotlights |
| **Bega** | Germany | Outdoor and architectural, built to last |
| **Occhio** | Germany | Premium residential architectural/decorative hybrid |
| **XAL** | Austria | Architectural linear and profile |
| **Lucent / Luctra / regional specialists** | Various | `needs-verification` |
| **Simes, Linea Light, Modular Lighting, Kreon, Wever & Ducré** | IT/BE | Further architectural specialists |

## 5. The decorative houses

| Maker | Country | Signature |
|---|---|---|
| **Flos** | Italy | Castiglioni (Arco, Toio), Starck (Miss Sissi), Gino Sarfatti reissues; part of the Flos B&B Italia group with Investindustrial/Carlyle backing |
| **Artemide** | Italy, founded **1960** by Ernesto Gismondi and Sergio Mazza, Pregnana Milanese | **Tizio** (Richard Sapper, 1972), **Tolomeo** (De Lucchi/Fassina, 1986); Compasso d'Oro 1995; MoMA and Met collections |
| **Louis Poulsen** | Denmark, founded **1874** | **PH lamps** (Poul Henningsen) — the glare-free multi-shade principle; also Arne Jacobsen (AJ) |
| **&Tradition** | Denmark | Reissues plus contemporary (Flowerpot, Bellevue) |
| **Gubi** | Denmark | Reissues (Grossman Grasshopper, Multi-Lite) |
| **Tom Dixon** | UK | Metallic/industrial decorative |
| **Moooi** | Netherlands | Statement and oversized pieces |
| **Vibia** | Spain | Modular decorative-architectural |
| **Santa & Cole** | Spain | Understated, textile shades, urban lighting |
| **Marset** | Spain | Warm decorative (Discocó, Ginger) |
| **Foscarini, Nemo, Oluce, Astep, Anglepoise, Serge Mouille** | Various | Further decorative names |

## 6. Southern African suppliers and importers

| Supplier | Base | Role |
|---|---|---|
| **Eurolux** | South Africa (Cape Town) | Large importer/distributor: lamps, luminaires, fans, outdoor and smart products; supplies the retail and electrical trade. `needs-verification` — site blocked |
| **Radiant Lighting** | South Africa | Long-established importer and brand, decorative and technical ranges |
| **K.Light Import** | South Africa | Importer/distributor to the trade, broad decorative and technical catalogue |
| **Streamlight** | South Africa | Importer/distributor |
| **Hellocandle** | South Africa | Decorative lighting supplier |
| **The Lighting Warehouse** | South Africa | National retail chain |
| **Regent Lighting Solutions** | South Africa | Local **manufacturer** and supplier of commercial/industrial luminaires — one of the few genuinely manufacturing operations in the region |
| **Beka Schréder** | South Africa | Local manufacture of roadway/area lighting (Schréder JV) |
| **[NA] Namibian suppliers** | Windhoek electrical wholesalers and lighting shops | Mostly stock SA-sourced ranges; architectural brands ordered in |

**[NA] Practical note.** Architectural European brands (ERCO, Delta Light, Flos Architectural) are specified into Namibian projects through South African agents. Lead times of **8–16 weeks** are normal, and there is effectively no local stock of drivers or spares — **order 5–10 % spares of every driver and lamp type with the original consignment**.

## 7. Specifying lighting for a hot, dry, high-UV climate

1. **Ambient temperature.** Ceiling voids under a metal roof in Namibia routinely exceed 50 °C. Specify Ta 40/45 °C rated gear; derate output accordingly; prefer remote drivers in ventilated, accessible locations.
2. **Access.** Every driver, transformer and control device must be reachable without breaking a ceiling. This is a design decision, not an afterthought.
3. **UV.** External polycarbonate diffusers yellow. Prefer glass, anodised aluminium and UV-stable materials outdoors.
4. **Dust and insects.** IP65 externally, and gasketed, even where IP44 would legally do. Insects entering a warm luminaire are a common failure.
5. **Surge.** Rural and peri-urban supply is surge-prone. Specify **surge protection (SPD) on lighting circuits** and drivers with adequate surge immunity (e.g. 4–10 kV) for external and exposed circuits.
6. **Glare and daylight.** With very high ambient daylight, interior lighting must be about **contrast and modelling**, not raw lux. Wallwashing and layered light beat more downlights.
7. **Colour temperature discipline.** Pick one CCT for the house (typically 2700 K residential, 3000 K where art or timber dominates) and hold it, including in appliance and cabinet lighting.

## Sources

- [DALI (Wikipedia)](https://en.wikipedia.org/wiki/Digital_Addressable_Lighting_Interface)
- [Color rendering index (Wikipedia)](https://en.wikipedia.org/wiki/Color_rendering_index)
- [IP code (Wikipedia)](https://en.wikipedia.org/wiki/IP_code)
- [ERCO](https://www.erco.com/en/)
- [Zumtobel (Wikipedia)](https://en.wikipedia.org/wiki/Zumtobel)
- [Artemide (Wikipedia)](https://en.wikipedia.org/wiki/Artemide)
- [Louis Poulsen (Wikipedia)](https://en.wikipedia.org/wiki/Louis_Poulsen)

## Open questions

- **Flos** could not be verified — the Wikipedia URL resolves to a butterfly genus and the corporate page was not reachable. Founding year, designers and ownership are from general knowledge. `needs-verification`.
- **Southern African suppliers (Eurolux, Radiant, K.Light, Streamlight, Hellocandle, Lighting Warehouse, Regent, Beka Schréder)** could not be fetched — sites were blocked, TLS-broken or JS-gated. Their described roles are `needs-verification`.
- **TM-30 Rf/Rg definitions** were not obtained in detail; the source consulted mentions TM-30 only as an alternative to CRI.
- **Lux level targets** are design practice; verify against **SANS 10114-1** (interior lighting) and EN 12464-1 before use in a compliant design.
- Efficacy ranges (90–130 lm/W), driver life figures and SDCM guidance are industry practice, not manufacturer data.
- MacAdam ellipse / SDCM definitions were not read from a primary source.
