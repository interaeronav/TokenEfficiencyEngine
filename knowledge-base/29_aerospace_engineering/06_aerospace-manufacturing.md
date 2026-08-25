---
id: aerospace.manufacturing
title: Aerospace manufacturing — how aircraft are actually built
domain: 29_aerospace_engineering
tags: [manufacturing, supply-chain, make-buy, outsourcing, 787, machining, sheet-metal, composites, afp, drilling, fastening, final-assembly-line, pulse-line, learning-curve, as9100, nadcap, traceability, production-rate, mro, spacex]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Boeing 787 Dreamliner", url: "https://en.wikipedia.org/wiki/Boeing_787_Dreamliner", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Airbus Orders and Deliveries", url: "https://www.airbus.com/en/products-services/commercial-aircraft/market/orders-and-deliveries", publisher: "Airbus SE", accessed: 2026-08-25}
  - {title: "Competition between Airbus and Boeing", url: "https://en.wikipedia.org/wiki/Competition_between_Airbus_and_Boeing", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Boeing 737 MAX", url: "https://en.wikipedia.org/wiki/Boeing_737_MAX", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "AS9100", url: "https://en.wikipedia.org/wiki/AS9100", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "SpaceX Starship", url: "https://en.wikipedia.org/wiki/SpaceX_Starship", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Boeing 777", url: "https://en.wikipedia.org/wiki/Boeing_777", publisher: "Wikipedia", accessed: 2026-08-25}
related: [aerospace.structures, aerospace.design_process, aerospace.certification, aerospace.overview]
unit_system: SI
---

# Aerospace manufacturing — how aircraft are actually built

**Summary.** Aerospace manufacturing is low-volume, high-mix, extreme-tolerance production under a regulatory regime that requires every part to be traceable to its raw material heat lot. An airliner is roughly 2–4 million parts (a 787 about 2.3 million; a 747 famously "six million"), assembled to tolerances measured in tenths of a millimetre over 60-metre lengths, at rates of a few dozen units per month. The industry's defining current problem is not design — it is **rate**: the ability to build reliably at the volume the order book demands, with a supply chain that spans five continents and cannot be surged. Boeing's 787 outsourcing experiment and its 737 quality-escape crisis are two chapters of the same lesson.

## Key facts

| Item | Value |
|---|---|
| **Airbus 2026 YTD deliveries** | **418 aircraft to 82 customers through end-July 2026**; 67 in July alone; 204 gross orders in July |
| **Airbus cumulative (end-July 2026)** | **26,534 orders / 17,176 deliveries / 14,511 in commercial service** |
| **Airbus 2024 deliveries** | **766** (826 orders) |
| **Airbus 2025 deliveries** | **793** (889 orders) — `needs-verification` against Airbus's own year-end release |
| Announced capacity targets (as of Jan 2024) | Airbus A320neo family **900/yr** (75/month); Boeing 737 MAX **600/yr** (50/month); Airbus A350 **108/yr** (9/month); Boeing 787 **120/yr** (10/month) |
| Boeing 737 MAX production cap | After the **5 January 2024** Alaska 1282 door-plug event the **FAA announced it would not grant any 737 MAX production expansion** until satisfied with Boeing's quality control (the cap was set at 38/month) |
| 787 material composition | 50 % composite, 20 % aluminium, 15 % titanium, 10 % steel, 5 % other; **≈77,000 lb (35 t) of CFRP** per aircraft |
| Quality standard | **AS9100 Rev D** (released **20 September 2016**), incorporating the whole of ISO 9001:2015 plus product safety, counterfeit-parts and human-factors requirements |
| Special-process accreditation | **Nadcap**, administered by the Performance Review Institute for SAE International |
| Learning curve | Typically **80–85 %** for aerospace assembly — unit cost falls by 15–20 % for each doubling of cumulative output |

> ⚠️ Production rate is not a manufacturing decision; it is a *supply chain* decision. The slowest, least-substitutable supplier — a single forging press, a single castings house, one titanium mill — sets the rate for the whole programme.

## 1. The make/buy decision and the global supply chain

Every structural and system item is subject to a make/buy analysis balancing:
- **Strategic**: is this a core competence and a source of competitive advantage? (Wings for Airbus, wing design and final integration for Boeing.)
- **Capacity and capital**: does building it in-house require a press, an autoclave, a five-axis gantry or a new factory?
- **Cost**: labour rate arbitrage, and the supplier's own volume across multiple customers.
- **Risk**: single-source exposure, geopolitical exposure, currency, and — crucially — **whether you retain enough engineering depth to specify, oversee and if necessary rescue the supplier**.
- **Offset and market access**: work placed in a country to win its airlines' orders. This is real, large, and rarely discussed openly; it explains a surprising amount of the industrial map.

The result is a genuinely global network. For a current widebody: wings in the UK and Japan, fuselage sections in Italy, Japan, Korea, Germany, France and the US, landing gear in France, Canada and the UK, engines from the US and UK, avionics from the US and France, interiors from Germany and the US — and the final assembly line in Toulouse, Hamburg, Everett, Charleston, Mobile or Tianjin.

## 2. The Boeing 787 outsourcing lesson

Boeing's 787 model went beyond buying parts: it delegated **design responsibility, capital investment, and integration of entire sections** to Tier 1 partners, who in turn sub-tiered further. Boeing would receive largely complete, systems-installed sections and join them in three days.

What actually happened, per the public record: Japanese firms (**Mitsubishi Heavy Industries** — wing box; **Subaru/Fuji** — centre wing box) and Italian and Korean companies (fuselage sections; **Alenia** at Grottaglie) took major work packages, with European suppliers providing doors and systems. **"Subcontractors had early difficulties procuring needed parts and finishing subassemblies on schedule, leaving remaining assembly work for Boeing to complete as 'traveled work.'"** Alenia's parent company booked roughly **€750 million of losses** on the programme. Boeing ultimately bought Vought's Charleston operation outright to regain control of Section 47/48.

The first flight slipped to **15 December 2009** and the first delivery to **September 2011** — about three years late after **five announced delays** — with programme cost reported around **US$32 bn** and accumulated losses of roughly **US$27 bn by May 2015**. Then in **January 2013** the FAA grounded the entire fleet over lithium-ion battery fires, with a redesigned battery approved in April 2013.

**The transferable lessons, stated without hindsight bias:**
1. **You cannot outsource what you cannot specify.** Boeing gave away detailed design authority for structures it had not itself designed in composite, so it could not judge whether the supplier's answer was right.
2. **Outsourcing integration risk does not reduce it; it hides it.** The risk reappears at final assembly as traveled work, at ten times the cost per hour.
3. **Sub-tier visibility is everything.** Boeing's contractual relationship was with Tier 1; the fastener shortage that stopped the line lived at Tier 3.
4. **Learning curve benefits accrue to whoever does the work.** By outsourcing, Boeing outsourced its own learning.
5. Airbus watched this happen and deliberately **kept more design authority in-house on the A350**, which is a large part of why the A350's execution, though two years late from the XWB relaunch, was comparatively orderly.

The 2024–2026 sequel is the same story in a different register: the **5 January 2024 Alaska Airlines Flight 1282 door-plug departure** on a nearly new 737-9 was traced to a plug reinstalled without its retention bolts after a repair — a **configuration and traveled-work control failure** at the Renton line involving work on a Spirit AeroSystems-built fuselage. The FAA's response was to freeze production expansion. Boeing's response, ultimately, was to move to reacquire Spirit AeroSystems (agreement announced **1 July 2024**, with Airbus taking over the Airbus-related work packages; `needs-verification` on the completion date) — that is, to **re-verticalise**, reversing the 787 philosophy outright.

## 3. Machining of large structures

Modern aerostructures are increasingly **monolithic machined parts** rather than built-up assemblies: a single 7050 or 7085 plate becomes a rib, a frame or a wing spar with integral stiffeners, replacing dozens of parts and hundreds of fasteners.

- **Five-axis gantry mills** with 30–50 m X-travel, 20,000–33,000 rpm spindles and high-pressure through-tool coolant. Aluminium is cut at very high material removal rates (2,000–10,000 cm³/min in high-speed machining); titanium at perhaps 1/20th of that because of its poor thermal conductivity and chemical reactivity with tooling.
- **Buy-to-fly ratio** is the industry's efficiency metric: mass of raw material purchased ÷ mass of the finished part. Machined aluminium wing ribs are often **10:1 to 20:1**; machined titanium fittings frequently **15:1 or worse**. This is the economic driver for near-net-shape forging, for DED/WAAM additive preforms, and for the aluminium chip-recycling economy that quietly funds a lot of machine shops.
- **Distortion control**: residual stress in thick plate, released asymmetrically by machining, warps long parts. Countermeasures: stress-relieved plate tempers (T7451 = stretched), symmetric machining sequences, intermediate stress relief, and adaptive machining that re-probes and re-posts the toolpath.
- **Chemical milling** (masking and etching skins to a variable thickness) is still used for large skin panels, though high-speed mirror milling is replacing it for environmental reasons.

## 4. Sheet metal forming

| Process | Application |
|---|---|
| **Stretch forming** | Fuselage skin panels — the skin is gripped in jaws, stretched past yield and wrapped over a form block, giving accurate, springback-free double curvature |
| **Rubber-pad (Guerin) and hydroforming** | Ribs, clips, small doublers in small batches |
| **Roll forming / stringer rolling** | Long constant-section stringers |
| **Creep-age forming** | Large wing skins: the panel is elastically loaded to shape in an autoclave and the ageing heat treatment relaxes it into permanent shape. Used for A380 and other large wing covers |
| **Shot peen forming** | Wing skin curvature and, separately, fatigue-life improvement via compressive residual surface stress |
| **Superplastic forming / diffusion bonding (SPF/DB)** | Titanium — complex hollow structures formed at 900 °C |
| **Hot forming** | Titanium and hardened aluminium details |

## 5. Composite manufacturing at rate

The composite rate problem is fundamentally about **cycle time in the autoclave** and **layup speed**.

- **AFP/ATL**: automated fibre placement heads lay 16–32 tows at 60 m/min or better; a 787 fuselage barrel is wound on a rotating mandrel in a matter of days. Deposition rate, not analysis, is the binding constraint on programme rate.
- **Autoclave**: a 787 barrel autoclave is on the order of 9 m diameter × 25 m long. Cure cycles of 6–10 hours plus load/unload mean each autoclave supports only a few parts per day, and autoclaves are multi-year lead-time capital items. This is precisely why **out-of-autoclave (VBO)** and **thermoplastic** processes attract so much investment: an oven is cheap, and a stamped thermoplastic clip takes minutes.
- **RTM/HP-RTM**: a dry preform in a matched metal tool with injected resin — cycle times of tens of minutes, excellent repeatability. **CFM's LEAP fan blades are RTM**, which is how a composite blade reached six-figure production volumes.
- **NDT at rate**: every primary composite part needs full-field ultrasonic inspection. Automated squirter or phased-array gantries scanning a whole barrel are themselves rate-limiting.
- **Consumables and waste**: prepreg has an out-time budget (typically 30 days at room temperature) and a freezer shelf life; the material is scrapped when either expires. Scrap rates of 20–30 % on complex layups are normal and are a real cost line.

## 6. Automated drilling and fastening

A large aircraft contains **1–3 million fasteners**. Every hole in primary structure must meet tolerance on diameter, perpendicularity, countersink depth (to a few hundredths of a millimetre — a proud or sunk head is a fatigue initiator), and, in composite, must not delaminate the exit ply.

Technologies:
- **Riveting machines and automated drilling/fastening cells** — C-frame or gantry machines that clamp, drill, deburr, inject sealant, insert and swage in one cycle.
- **Flexible track drilling** — a rail vacuum-attached to the workpiece carrying a small drilling head; the practical answer for large curved panels where a gantry cannot reach.
- **Orbital drilling** — the tool orbits eccentrically, producing lower thrust force and cleaner exits in CFRP/Ti stacks, and generating chips small enough to evacuate.
- **Robotic drilling with metrology feedback** — industrial robots are not accurate enough on their own over a 2 m envelope, so laser trackers or photogrammetry close the loop.
- **One-up assembly (OUA)** — drilling through the stack once, without disassembly for deburr and clean, which requires drilling that leaves no burr and no swarf between layers. This eliminates an enormous amount of labour when it works.
- **Determinate assembly** — parts made accurate enough (with coordination holes machined from the same digital dataset) that they self-locate without hard tooling. Boeing pioneered this on the 777; it is the reason a modern jig looks far lighter than a 1970s one.

Boeing's **Fuselage Automated Upright Build (FAUB)** for the 777 was an attempt to fully automate fuselage panel joining; after years of trouble it was largely abandoned in favour of a flex-track approach — a useful reminder that automation in low-volume, high-variability assembly is not automatically cheaper.

## 7. Final assembly and the moving line

The classic aerospace FAL was a set of fixed positions where an aircraft sat for weeks while crews worked around it. Toyota-influenced reform replaced this with:

- **Pulse lines**: the aircraft moves between stations at a fixed *takt* interval — every 2 days, or 1 day, or 12 hours — and each station has a defined, balanced, standard work package. Missing the takt is visible immediately, which is the point.
- **Moving lines**: continuous slow motion (Boeing's Renton 737 line moves at roughly 5 cm/min), so there is no "the line is stopped" ambiguity.
- **Point-of-use kitting** and **feeder lines** for sub-assemblies, so no one searches for parts.
- **Andon** and stop-the-line authority — culturally the hardest element to import, and the one whose absence shows up in quality escapes.

Typical FAL flow times: a narrowbody, roughly **8–11 days** from join to roll-out; a widebody, **1–3 months** including systems installation and functional test. After roll-out: fuelling, engine runs, gear swings, systems functional tests, a customer acceptance flight of a few hours, paint (3–7 days), cabin fit if not already installed, and delivery.

## 8. Rate ramp-up economics and the learning curve

**Wright's learning curve**: `Y_x = Y_1 · x^{b}` where `b = log(p)/log(2)` and `p` is the learning percentage. Aerospace assembly typically shows **p = 0.80–0.85**, so the 100th aircraft takes roughly 25–35 % of the labour hours of the first, and the 1,000th about half of the 100th.

The programme consequence: **unit cost early in a programme is far above price**, and the programme only becomes profitable after the cumulative curve crosses. This is why Boeing uses **program accounting** (spreading estimated total programme cost over an accounting quantity of several hundred or a thousand units), and why the 787's "deferred production cost" balance grew to about US$27 bn before it began to unwind — an accounting artefact of exactly this curve.

**Ramping rate destroys the curve temporarily**: new hires, new suppliers, new tooling and overtime all push unit hours back up. The observed pattern across programmes is that a rate increase of more than roughly **20–25 % per year** in a supply chain reliably produces quality escapes and shortages. Both Airbus and Boeing have been rate-limited since 2021 by castings, forgings, engines, seats, and — above all — skilled labour, not by their own final assembly capacity.

## 9. Quality systems, traceability and configuration control

**AS9100** is "an international standard for aerospace management systems" developed by SAE in **March 1999**, and it "fully incorporates the entirety of the current version of ISO 9001, while adding requirements relating to quality and safety." The current revision, **AS9100 Rev D (20 September 2016)**, incorporates ISO 9001:2015 and adds explicit requirements for **product safety, prevention of counterfeit parts, and human factors** in nonconformity management. Related standards: **AS9110** (maintenance organisations) and **AS9120** (distributors). Certification is registered through the IAQG's OASIS database and is a precondition for doing business with any prime.

**Nadcap** (administered by the Performance Review Institute on behalf of SAE) accredits **special processes** — those whose result cannot be fully verified by subsequent inspection of the product: heat treatment, chemical processing, coatings, welding, NDT, composites, materials testing, surface enhancement, sealants, elastomer seals, non-conventional machining. A prime will typically require Nadcap accreditation for each specific process at each specific site. Audit failure rates on first audit are high, and re-audit cycles (initially annual, extending with good performance) are a permanent cost of doing aerospace work. (Detailed supplier and audit counts could not be retrieved — `needs-verification`.)

**Traceability** runs from the raw material heat/lot number, through every process, to the serialised part, to the aircraft MSN, and remains retrievable for the life of the aircraft. This is the mechanism that makes an airworthiness directive executable: when a bad heat lot of forgings is discovered, the affected serial numbers can be identified. It is also the mechanism that **counterfeit and unapproved parts** subvert — a live problem, as the AOG Technics falsified-documentation scandal (2023, thousands of engine parts with forged airworthiness release certificates) demonstrated.

**Configuration control** determines, for each MSN, exactly which drawing revision, which service bulletin embodiment and which customer option applies. Its failure modes are expensive: the A380's wiring harness mismatch between design sites running different CATIA versions cost roughly two years, and the Alaska 1282 door plug was, procedurally, a removed-and-reinstalled item whose reinstallation was not documented.

## 10. Supply-chain risk

| Risk | Nature |
|---|---|
| **Titanium** | Concentrated in a handful of mills; VSMPO-AVISMA's position made post-2022 sanctions a structural problem for both primes; sponge and melting capacity has multi-year lead times |
| **Large forgings and castings** | A very small number of presses worldwide can forge a landing-gear beam or a bulkhead. Precision Castparts and a few others dominate structural and turbine castings; a foundry problem propagates instantly to every programme |
| **Engines** | Engine availability has been the binding constraint on narrowbody delivery since 2023, compounded by the **PW1100G powder-metal inspection programme** (1,200 of 3,000 engines called in July 2023, extended to all 3,000 by September 2023) |
| **Fasteners** | Low-value, high-count, long-lead; a fastener shortage stopped the 787 line and has recurred repeatedly |
| **Castings/seats/interiors** | Cabin interiors and seats are a chronic delivery-slipping item because they are customer-specific and certification-heavy |
| **Skilled labour** | The 2020–21 furloughs removed decades of experience; the replacement workforce is the proximate cause of much of the current quality-escape rate |
| **Single-source semiconductors and electronics** | Long qualification tails mean an obsolete part cannot simply be substituted |

## 11. The MRO industry

Roughly a **US$100–120 bn/yr** global market (`needs-verification` for 2026), split approximately: engine overhaul ~40 %, components ~20 %, airframe heavy maintenance ~15 %, line maintenance ~15 %, modifications ~10 %.

Structurally it differs from production in three ways: the work content is discovered rather than planned (a C-check's findings drive half its hours), the parts are used or repaired rather than new (with a whole PMA/USM market and its own approval chain), and the approval regime is **Part 145** rather than Part 21 — a repair station approval, with **AS9110** as the quality standard.

The economics are dominated by the engine OEMs, who sell engines near cost and earn on spares and shop visits, increasingly through **flight-hour agreements** (Rolls-Royce TotalCare, GE OnPoint, P&W EngineWise) that convert maintenance into a per-hour cost for the operator and a long annuity for the OEM. That model is why the independent MRO sector fights hard for licensed access, and why PMA parts are commercially contentious.

**[ZA]/[NA] Regional relevance:** SAA Technical, Denel Aviation and a handful of Part 145 organisations serve southern Africa; heavy checks for regional operators frequently go to Joramco (Amman), Ethiopian MRO, or ST Engineering. Qatar Airways' own Doha technical operation is one of the larger Middle East MROs and does third-party work.

## 12. Current production rate picture (dated)

| Figure | Value | Date |
|---|---|---|
| Airbus deliveries YTD | **418 aircraft to 82 customers** | through end-**July 2026** |
| Airbus deliveries, July alone | **67** to 39 customers | July 2026 |
| Airbus gross orders, July alone | **204** | July 2026 |
| Airbus cumulative orders / deliveries / in service | **26,534 / 17,176 / 14,511** | end-July 2026 |
| Airbus full-year deliveries | **766** | 2024 |
| Airbus full-year deliveries | **793** (`needs-verification`) | 2025 |
| Airbus A320-family rate target | 75/month (900/yr) | announced by Jan 2024 |
| Airbus A350 rate target | 9/month (108/yr) | announced by Jan 2024 |
| Boeing 737 MAX rate target | 50/month (600/yr) | announced by Jan 2024 |
| Boeing 787 rate target | 10/month (120/yr) | announced by Jan 2024 |
| Boeing 737 MAX production cap | FAA declined to approve any production expansion beyond 38/month pending quality-control improvements | announced after **5 January 2024** |
| Boeing 737 MAX 7 and MAX 10 certification | Both pushed into **2026** as of November 2025; anti-ice redesign complete; MAX 10 launch customer WestJet expected 2027 | Nov 2025 |

> ⚠️ Boeing's own 2025 full-year and 2026 year-to-date delivery totals could not be retrieved in this session — boeing.com's orders-and-deliveries page is a JavaScript application that does not render to text. Any Boeing delivery figure quoted from secondary sources should be checked against Boeing's monthly Orders & Deliveries release before use.

## 13. The space manufacturing shift

Traditional space manufacturing is the extreme end of aerospace practice: unit volumes of one to ten, exhaustive documentation, class-S parts, months of environmental testing, and a cost structure in which the paperwork genuinely rivals the hardware. **SpaceX** demonstrated a different model, and it is worth being precise about what actually changed:

1. **Vertical integration.** SpaceX manufactures the great majority of the vehicle in-house — engines, structures, avionics, and even much of the electronics — rather than buying qualified subsystems. That removes supplier margin stacking, removes the interface documentation burden, and, critically, means a design change can be made and flown in weeks.
2. **Design for manufacture from day one.** The Merlin and Raptor engines were designed around producibility; Starlink satellites are designed to be built at a rate of several per day and to stack flat in the fairing.
3. **Material choice driven by process, not by data sheet.** Starship moved from carbon composite to **stainless steel in December 2018**: early prototypes in **301**, later vehicles in **304L** for weldability, and current production in a proprietary **30X** alloy balancing cost and cryogenic performance. Vehicle bodies are "made from stainless steel and are manufactured by stacking and welding stainless steel cylinders," with rings **1.83 m tall and 3.97 mm thick**. Steel is heavier per unit strength at room temperature but gets stronger cryogenically, tolerates re-entry heat far better, costs a fraction of CFRP per kilogram, and can be welded outdoors — which is why Starbase looks like a shipyard rather than a cleanroom.
4. **Iterative, hardware-rich development.** "Development has followed an iterative and incremental approach, involving a high number of test flights and prototype vehicles" — an explicit fail-fast philosophy in which losing a vehicle is an acceptable price for information. Recent Starship flights: **Flight 9 (27 May 2025)** — booster lost, ship broke up during re-entry; **Flight 10 (26 August 2025)** — success, payload deployed and engine relight achieved; **Flight 11 (13 October 2025)** — success, the final Block 2 configuration flight, with Block 3 hardware entering testing thereafter.
5. **Reuse as the cost lever.** Falcon 9 booster reuse turned launch from a consumable into a fleet operation, with the manufacturing implication that production capacity is spent on second stages and payloads rather than boosters.

**What does not transfer.** Crewed commercial aviation cannot adopt fail-fast: a Part 25 aeroplane must be shown safe *before* it carries the public, and the certification regime exists precisely to prevent learning from crashes. What *does* transfer is the rest: vertical integration where design and build must co-evolve, design for manufacture as a first-class requirement, ruthless reduction of part count and interface count, and a bias toward building and testing hardware early rather than analysing longer. Rocket Lab, Relativity, Firefly and the European NewSpace entrants have all adopted variants of the model; the traditional primes have adopted parts of it under duress.

## Sources

- [Airbus Orders and Deliveries](https://www.airbus.com/en/products-services/commercial-aircraft/market/orders-and-deliveries) — Airbus SE
- [Competition between Airbus and Boeing](https://en.wikipedia.org/wiki/Competition_between_Airbus_and_Boeing) — Wikipedia (annual totals, announced rate targets)
- [Boeing 787 Dreamliner](https://en.wikipedia.org/wiki/Boeing_787_Dreamliner) — Wikipedia (outsourcing, traveled work, delays, cost)
- [Boeing 737 MAX](https://en.wikipedia.org/wiki/Boeing_737_MAX) — Wikipedia (FAA production expansion freeze after January 2024; MAX 7/MAX 10 certification status)
- [Boeing 777](https://en.wikipedia.org/wiki/Boeing_777) — Wikipedia (determinate assembly, digital design)
- [AS9100](https://en.wikipedia.org/wiki/AS9100) — Wikipedia
- [SpaceX Starship](https://en.wikipedia.org/wiki/SpaceX_Starship) — Wikipedia (materials, ring stacking, development philosophy, recent flights)

## Open questions

- **Boeing 2025 full-year and 2026 YTD deliveries and current actual monthly rates** — boeing.com's orders-and-deliveries page could not be read; `needs-verification`.
- Whether the FAA 38/month 737 cap has been raised or lifted, and to what, as of August 2026 — `needs-verification`.
- Airbus 2025 full-year delivery total (793 quoted from a secondary source) — `needs-verification` against Airbus's own release.
- Completion date and final work-package allocation of the Boeing/Airbus acquisition of Spirit AeroSystems — `needs-verification`.
- Nadcap supplier and audit volumes — the PRI site returned HTTP 403; `needs-verification`.
- Global MRO market value for 2026 — order-of-magnitude estimate only.

