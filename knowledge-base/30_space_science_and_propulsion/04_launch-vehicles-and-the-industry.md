---
id: space.launch-industry
title: Launch vehicles and the launch industry
domain: 30_space_science_and_propulsion
tags: [launch-vehicles, falcon-9, starship, ariane-6, vulcan, new-glenn, electron, long-march, launch-economics, constellations, reusability]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
unit_system: SI
related: [space.overview, space.chemical-propulsion, space.spacecraft-engineering]
sources:
  - {title: "2025 in spaceflight", url: "https://en.wikipedia.org/wiki/2025_in_spaceflight", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Falcon 9", url: "https://en.wikipedia.org/wiki/Falcon_9", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "SpaceX Starship", url: "https://en.wikipedia.org/wiki/SpaceX_Starship", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Vulcan Centaur", url: "https://en.wikipedia.org/wiki/Vulcan_Centaur", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Ariane 6", url: "https://en.wikipedia.org/wiki/Ariane_6", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "New Glenn", url: "https://en.wikipedia.org/wiki/New_Glenn", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Electron (rocket)", url: "https://en.wikipedia.org/wiki/Electron_(rocket)", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Rocket Lab Neutron", url: "https://en.wikipedia.org/wiki/Rocket_Lab_Neutron", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Starlink", url: "https://en.wikipedia.org/wiki/Starlink", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Kuiper Systems / Amazon Leo", url: "https://en.wikipedia.org/wiki/Kuiper_Systems", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "Guowang", url: "https://en.wikipedia.org/wiki/Guowang", publisher: "Wikipedia", accessed: "2026-08-25"}
  - {title: "LandSpace", url: "https://en.wikipedia.org/wiki/LandSpace", publisher: "Wikipedia", accessed: "2026-08-25"}
---

# Launch vehicles and the launch industry

**Summary.** The launch market between 2015 and 2026 changed more than it had in the preceding forty years. Global orbital launch attempts rose from around 87 in 2015 to **330 in 2025 (317 successes, 13 failures)**. One company flies most of them, and most of what that company flies is its own constellation. This file gives the current vehicles with dated figures, the reuse economics separating what is known from what is claimed, cadence by year, and the constellation demand — Starlink, Amazon Leo (formerly Kuiper), OneWeb, Guowang — that now underwrites the whole market.

> ⚠️ Confidence for this file is **medium**, not high. Launch economics is the least transparent part of the industry: no operator publishes internal cost per flight. Every number below is labelled as either a **list price** (published, verifiable) or an **estimate** (third-party, uncertain).

## Key facts

| Metric | Value | As of |
|---|---|---|
| Global orbital launch attempts, 2025 | 330 (317 success, 13 failure) | 2025 full year |
| Falcon 9 total flights | 587, with 584 full mission successes (99.5%) | 12 Jan 2026 |
| Falcon 9 Block 5 record | 530 of 531 successful (99.8%) | 12 Jan 2026 |
| Booster landings | 542 of 553 attempts | 12 Jan 2026 |
| Single-booster reuse record | 32 flights | 2026 |
| Falcon 9 list price | US$69.85 M | 2025 |
| Falcon 9 payload | ≥17,400 kg LEO reusable / ≥22,800 kg expendable; 5,800 kg GTO reusable | Block 5 |
| Electron list price | ≈US$7.5 M (≈US$25,000/kg) | published |
| Electron flights | 91 total, 87 orbital successes | source date |
| Starlink in orbit | ≈10,413 (10,397 operational) | June 2026 |
| Starlink 2025 financials | US$11.4 bn revenue, US$4.4 bn operating income | end 2025 |
| Starlink subscribers | >12 million | June 2026 |
| Ariane 6 cost per launch | now exceeds €100 M (original targets €75 M / €90 M) | 2024–25 |

## 1. Falcon 9 and Falcon Heavy

**Falcon 9 Block 5** — 70 m tall, 3.66 m diameter, 549 t liftoff mass. Nine Merlin 1D on the first stage (7,600 kN total sea-level thrust), one Merlin Vacuum on the second (934 kN, or 840 kN with the short nozzle). LOX/RP-1 throughout. Payload ≥17,400 kg to LEO with booster recovery, ≥22,800 kg expendable, 5,800 kg to GTO reusable, 8,300 kg expendable, 4,020 kg to Mars. List price **US$69.85 million (2025)**.

The record as of 12 January 2026: **587 flights, 584 full mission successes (99.5%)**; Block 5 alone 530 successes of 531; **542 booster landings from 553 attempts**; individual boosters have flown as many as **32 missions**. This is, by a wide margin, the most-flown and most-reliable orbital-class rocket in history by both measures simultaneously.

**Falcon Heavy** is three Falcon 9 cores. It flies rarely — the highest-energy missions (Psyche, Europa Clipper fully expendable, GOES-U, Dragonfly in 2028) and heavy GEO/direct-inject national security payloads — because Falcon 9 covers most of the market.

### The reuse economics — known versus claimed

**Known (published/verifiable):**
- List price US$69.85 M for a reusable Falcon 9 mission (2025).
- Payload ≥17,400 kg to LEO reusable → **≈US$4,000/kg at list price to LEO**, assuming a full payload, which a commercial customer almost never has.
- To GTO at 5,800 kg reusable → ≈US$12,000/kg.
- Booster reuse to 32 flights is demonstrated. Fairing halves are recovered and reflown routinely.
- Rideshare (Transporter/Bandwagon) is published at roughly **US$6,500/kg to SSO** with a 50 kg minimum, escalating annually.

**Claimed (SpaceX statements, not independently auditable):**
- Marginal cost per Falcon 9 flight around US$15–20 M has been asserted by SpaceX executives at various times. There is no way to check it.
- Refurbishment cost "a few hundred thousand dollars" — likewise unverifiable.

**Estimable:**
- Propellant is genuinely trivial: roughly 400 t of LOX and 120 t of RP-1, at commodity prices, is on the order of US$300,000–500,000 per flight — well under 1% of list price. This confirms the structural point that hardware and operations, not fuel, are the cost.
- Range, insurance and integration costs are real and not small.

**The honest summary:** Falcon 9 has cut the *price* of medium-lift launch by roughly a factor of three to four versus its 2010 competition, and its cadence has cut the *waiting time* by more. Whether its internal *cost* has fallen by ten times, as sometimes claimed, is unknown outside SpaceX. The clearest evidence that reuse works economically is behavioural rather than accounting: SpaceX chose to build Starlink, a business that only closes if internal launch cost is very low.

## 2. Starship

The largest launch vehicle ever built. Block 1 stack 121.3 m tall, 9 m diameter, 4,600 t of propellant (3,400 t booster + 1,200 t ship); Block 4 is planned at 142 m. **33 Raptor engines on Super Heavy**, 6 on the ship (3 sea-level, 3 vacuum). Stated payload to LEO: Block 1 15 t, Block 2 35 t, Block 3 100 t, Block 4 200 t — note these are design targets, not demonstrated figures.

**Flight test record:**

| Flight | Date | Outcome |
|---|---|---|
| IFT-1 | 20 Apr 2023 | Failure, ~4 min |
| IFT-2 | 18 Nov 2023 | Both stages lost |
| IFT-3 | 14 Mar 2024 | Reached space; both stages lost on descent |
| IFT-4 | 6 Jun 2024 | Controlled splashdowns of both stages |
| IFT-5 | 13 Oct 2024 | **First booster catch by the launch tower** |
| IFT-6 | 19 Nov 2024 | In-space engine relight |
| IFT-7 | 16 Jan 2025 | Booster caught; ship lost |
| IFT-8 | 6 Mar 2025 | Ship lost to engine shutdowns |
| IFT-9 | 27 May 2025 | Both vehicles lost |
| IFT-10 | 26 Aug 2025 | Success; payload deployment demonstration and splashdown |
| IFT-11 | 13 Oct 2025 | Success; final Block 2 flight |

Status as of late 2025: **6 successful flights, 5 failures**, still classified as in development. No orbital payload has been delivered to a customer. SpaceX holds a **US$2.89 billion** contract for the Starship HLS lunar lander.

The programme's two unsolved problems as of this writing are (a) reliable ship reuse — the booster has been caught, the ship has not — and (b) **orbital propellant transfer**, which the lunar architecture requires at a scale of many tanker flights per landing. Neither has been demonstrated. Any cost-per-kg figure for Starship is therefore a projection, not a measurement, and should be treated as such regardless of who states it.

## 3. Electron and Neutron

**Electron** (Rocket Lab): 1.2 m diameter, carbon-composite structure, nine electric-pump-fed Rutherford engines on the first stage and one vacuum Rutherford on the second, plus a restartable **Kick Stage** (up to 150 kg). Payload **200–300 kg to 500 km SSO**; list price **≈US$7.5 M, ≈US$25,000/kg**. **91 flights, 87 orbital successes, 4 failures** as of the source date. First orbital success 21 January 2018.

Electron proved the dedicated-small-launch thesis: some customers will pay 6× the rideshare price per kilogram for control of orbit, schedule and integration. Booster recovery was attempted first by helicopter catch, then abandoned in favour of ocean splashdown; the first stage has been recovered twice ("Return to Sender", Flight 16) but Electron boosters are not routinely reflown. **HASTE** is the suborbital hypersonic-testbed variant (700 kg suborbital, first flight 18 June 2023) and is a meaningful revenue line. **Photon** is the Kick-Stage-derived satellite bus, capable of delivering up to 30 kg to lunar orbit (it flew CAPSTONE).

**Neutron** is Rocket Lab's medium-lift answer: 42.8 m tall, 7 m maximum diameter, **15,000 kg to LEO expendable, 13,000 kg with downrange landing, 8,500 kg return-to-launch-site**. Nine **Archimedes** oxygen-rich staged-combustion methalox engines on stage one (6,600 kN total), one on stage two (900 kN). Distinctive architecture: a composite "Hungry Hippo" fairing that stays attached to the first stage and reopens, with the second stage suspended inside — eliminating fairing recovery entirely. First flight expected **no earlier than Q4 2026**, with three launches planned in 2026 and five in 2027.

## 4. Vulcan Centaur

ULA's replacement for Atlas V and Delta IV. 67.3 m tall; two **BE-4** methalox engines (2,400 kN each at ULA's rating) on the booster; **Centaur V** upper stage with two RL10C-1-1 (203.6 kN, 453.8 s each, upgrading to RL10E at 214.6 kN / 460.9 s from late 2025). Configurations VC0/VC2/VC4/VC6 by GEM 63XL solid booster count, with standard (15.5 m) or long (21.3 m) fairing. Up to **27,200 kg to LEO** in the six-booster configuration.

Launch record: **Cert-1, 8 January 2024** (Peregrine lunar lander — vehicle successful, payload failed separately); **Cert-2, 4 October 2024** (mass simulator; successful despite an SRB nozzle anomaly); **USSF-87, 12 February 2026** (successful, but a second SRB issue triggered a launch pause). Vulcan's problem is not capability but cadence — it is contracted for a large share of US national security launch and for 38 Amazon Leo missions, and it has flown three times in two years.

**SMART reuse** (Sensible Modular Autonomous Return Technology) would detach and recover only the BE-4 engine module by parachute and mid-air capture — ULA projects up to 90% reduction in first-stage propulsion cost and 65% of total first-stage cost. It has not been demonstrated.

## 5. Ariane 6

Europe's replacement for Ariane 5. Two configurations: **A62** (two P120C solid boosters) at 10,350 kg LEO / 4,500 kg GTO, ≈530 t liftoff; **A64** (four P120C) at 21,500 kg LEO / 11,500 kg GTO, ≈860 t. **Vulcain 2.1** gas-generator LOX/LH2 core (1,324 kN, 120.8 bar), **Vinci** restartable closed-expander upper stage (180 kN, five restarts, burns to 900 s), P120C boosters at up to 4,650 kN each — shared with Vega-C, which is the programme's genuine industrial win.

First flight **VA262, 9 July 2024** — partial success, with an auxiliary power unit anomaly preventing the planned upper-stage deorbit demonstration. **VA263, 6 March 2025** delivered CSO-3 successfully. Four Ariane 6 launches in 2025.

The economics are the difficulty. Original targets were €75 M (A62) and €90 M (A64); actual cost **now exceeds €100 M per mission**, though cost per kilogram improved roughly 40% over Ariane 5. Arianespace targeted six launches in 2025, eight in 2026, and ten annually from 2027. Ariane 6 is not reusable and was not designed to be; the European response to Falcon 9 is a decade behind, and ESA's Themis/Callisto reusable demonstrators and the European Launcher Challenge (funding Isar Aerospace, Rocket Factory Augsburg, MaiaSpace, PLD Space, Orbex and others) are the belated attempt to catch up.

## 6. H3, Soyuz and Angara

**H3** (JAXA/Mitsubishi Heavy Industries) replaced H-IIA. Two or three **LE-9** expander-bleed engines (1,471 kN each) on the core, plus 0, 2 or 4 SRB-3 solids. First flight **7 March 2023 failed** (second-stage LE-5B-3 ignition); the second flight on **17 February 2024 succeeded**, and H3 has flown regularly since. The design goal was to halve H-IIA's launch price to roughly ¥5 billion for the smallest configuration — achieved partly through automotive-style mass production of LE-9 components.

**Soyuz-2** remains the most-flown launcher family in history in cumulative terms (the R-7 lineage dates to 1957) and Russia conducted **17 launches in 2025 with no failures**. Its commercial market vanished after February 2022: Arianespace's Soyuz operations at Kourou ended, OneWeb's remaining launches moved to SpaceX and NSIL, and 36 OneWeb satellites were impounded at Baikonur. Soyuz now flies Russian state, ISS crew/cargo, and a handful of friendly-nation payloads.

**Angara** is the intended replacement — modular URM-1 cores each with one **RD-191**, in A1.2, A5 and A5M configurations. First flight 2014; cadence has remained very low, and cost has reportedly exceeded Proton's, which was the vehicle it was meant to replace. Proton itself is being retired.

## 7. China

**Long March** is the state family, with **more than 600 launches** cumulative. Active variants and their nominal payloads:

| Variant | LEO | GTO | Propellants |
|---|---|---|---|
| CZ-2C | 4,000 kg | 1,250 kg | N2O4/UDMH |
| CZ-2D | 3,500 kg | — | N2O4/UDMH |
| CZ-2F | 8,800 kg | — | N2O4/UDMH — the crew-rated Shenzhou launcher |
| CZ-3B/E | 11,500 kg | 5,500 kg | N2O4/UDMH |
| CZ-4B/C | 4,200 kg | 1,500 kg (4C) | N2O4/UDMH |
| CZ-5 | — | 14,400 kg | LOX/LH2 core + LOX/RP-1 boosters |
| CZ-5B | 25,000 kg | — | Station module launcher |
| CZ-6 | >1,500 kg | — | LOX/RP-1 |
| CZ-6A | >8,000 kg | — | LOX/RP-1 + solids |
| CZ-7 / 7A | 14,000 kg | 7,800 kg (7A) | LOX/RP-1 |
| CZ-8 / 8A | 8,100 / 9,800 kg | 2,800 / 3,500 kg | LOX/RP-1 — first flight 22 Dec 2020 |
| CZ-11 | 700 kg | — | Solid, road/sea mobile |
| CZ-12 / 12A | 12,000 kg / 9,000 kg reusable | — | LOX/RP-1 (YF-100K) |

The hydrazine-family vehicles (CZ-2/3/4) still fly heavily, which is unusual internationally and reflects a large installed industrial base rather than a technical preference.

**Commercial Chinese entrants** are the more interesting development. **LandSpace's Zhuque-2** became the first methane-fuelled rocket to reach orbit on its second flight, **12 July 2023** (6,000 kg to 200 km LEO, 4,000 kg to 500 km SSO). **Zhuque-3** — 11.8 t LEO expendable, 8 t with first-stage recovery, nine Tianque-12 engines, first stage designed for up to twenty flights — flew on **3 December 2025**, reached orbit, and **failed its first-stage recovery attempt**. The enhanced ZQ-3E is quoted at 21.3 t expendable / 12.5 t with launch-site recovery. iSpace (Hyperbola), Galactic Energy (Ceres, Pallas), Space Pioneer (Tianlong), Orienspace (Gravity) and Deep Blue Aerospace are all pursuing partly-reusable methalox medium-lift vehicles on similar timelines. China is roughly where SpaceX was in 2014–2015, with several companies attempting it simultaneously and state backing.

## 8. New Glenn

Blue Origin's heavy-lift vehicle: 98 m tall, 7 m diameter, **seven BE-4 engines** on the first stage (17,000 kN liftoff thrust, methalox), **two BE-3U** hydrolox engines on the second. **45,000 kg to 51.6° LEO, 13,000 kg to GTO**. First stage designed for a minimum of 25 flights with barge landing.

| Flight | Date | Outcome |
|---|---|---|
| NG-1 | 16 Jan 2025 | Orbital success; booster lost on descent |
| NG-2 | 13 Nov 2025 | Orbital success; **successful booster landing** |
| NG-3 | Apr 2026 | Reached orbit; upper stage malfunction |
| NG-4 | 28 May 2026 | **Destroyed in a static fire test** |

Blue Origin now has a second operator that has landed an orbital-class booster, and a vehicle whose reliability record is four flights with two anomalies. New Glenn's near-term manifest is dominated by Amazon Leo (12 launches with 15 options), Blue Moon lunar landers, and ESCAPADE-class NASA science.

## 9. The small-launch sector and its consolidation

Between roughly 2015 and 2020 something like 150 small launch vehicle programmes were announced worldwide. As of 2026, a single-digit number have reached orbit and fewer still fly regularly.

**Reached orbit and still flying:** Electron (Rocket Lab), Kuaizhou and Jielong (China, state), Ceres-1 (Galactic Energy), Hyperbola-1 (iSpace), SSLV (ISRO), Qased/Qaem (Iran), and Firefly's Alpha (with a mixed record).

**Reached orbit and stopped:** LauncherOne (Virgin Orbit — reached orbit January 2021, failed the Cornwall launch January 2023, bankrupt and liquidated May 2023), Launcher/Astra Rocket 3 (reached orbit November 2021, retired after failures, Astra taken private), Epsilon (Japan, suspended after a 2022 failure and a 2023 test explosion).

**Never reached orbit and folded or pivoted:** a long list including Vector Launch, Bloostar, and dozens of others.

**Still trying:** Isar Aerospace (Spectrum — first flight March 2025 failed shortly after lift-off), Rocket Factory Augsburg, PLD Space (Miura 5), Gilmour Space (Eris), Orbex, Skyrora, Latitude, and Stoke Space (Nova, full reuse).

**Why consolidation happened.** The dedicated small launch price of US$20,000–30,000/kg competes against rideshare at US$6,000–7,000/kg on a vehicle that flies every few weeks. Rideshare wins for any payload that can tolerate a standard SSO drop-off, which is most of them. The surviving business case is the minority that cannot: unusual inclinations, precise timing, national security, responsive launch, and constellation replenishment into specific planes. That is a real market — it is just an order of magnitude smaller than the 2018 projections assumed. The broader lesson is that in launch, **cadence is the moat**: a vehicle that flies twice a year cannot amortise fixed costs or build reliability statistics no matter how clever it is.

## 10. Cadence by year and market structure

Global orbital launch attempts (successes in brackets where known):

| Year | Attempts | Note |
|---|---|---|
| 2015 | ≈87 | Pre-reuse baseline |
| 2020 | ≈114 | Starlink ramp begins |
| 2021 | ≈146 | |
| 2022 | ≈186 | |
| 2023 | ≈223 | |
| 2024 | ≈259 | |
| **2025** | **330 (317 success, 13 failure)** | Record |

The 2015→2025 growth is roughly 3.8×, and essentially all of it is attributable to two things: SpaceX flying Starlink, and China's state plus commercial ramp. Traditional commercial GEO comsat launch — the market that defined the industry from 1990 to 2015 — has *shrunk*, because GEO satellites got more capable, all-electric propulsion made them lighter, and LEO constellations took part of the demand.

> The 2025 per-country breakdown in the fetched source appeared internally inconsistent and is not reproduced here. The global totals (330/317/13) are the figures I am confident in.

## 11. Constellation-driven demand

| Constellation | Operator | Planned | Deployed | Status |
|---|---|---|---|---|
| **Starlink** | SpaceX | ~12,000 approved, up to 42,000 filed | **≈10,413 in orbit, 10,397 operational (June 2026)** | Operational; >12 M subscribers; US$11.4 bn revenue and US$4.4 bn operating income in 2025; ≈75% of all active manoeuvrable satellites |
| **Amazon Leo** (ex-Kuiper) | Amazon | **3,236** in shells at 590/610/630 km | 2 prototypes (Oct 2023) + **367 production satellites through April 2026** | FCC required half by 30 July 2026 — **waived in June 2026** with reduced spectral priority for later satellites; remainder due 30 July 2029. >US$10 bn committed to launch across Atlas V (9), Vulcan (38), Ariane 6 (18), New Glenn (12+15 options), Falcon 9 (13) |
| **OneWeb / Eutelsat** | Eutelsat Group | 648 (Gen 1) | Gen 1 complete | Merged with Eutelsat 2023; Gen 2 planning constrained by capital |
| **Guowang / SatNet** | China SatNet (CASIC) | **>13,000** (~6,000 at 500–600 km, ~7,000 at ~1,145 km) | 27 experimental + 3 HEO + **168 LEO (Oct 2025)** | State constellation, civil and military applications |
| **Qianfan / Thousand Sails** | Shanghai Spacecom (SSST) | ~15,000 filed | Several hundred | Commercial Chinese LEO broadband **[needs-verification for current count]** |

The structural point: **constellations converted launch from a lumpy, low-volume, high-margin business into a high-volume industrial one**. Starlink alone accounts for the majority of mass to orbit each year. That in turn is what makes reusability pay — a booster that flies 32 times only makes sense if there are 32 payloads waiting. Reuse and constellations are not two developments; they are one, and neither closes without the other.

The risk is concentration. One operator flies most launches, owns most satellites, and is its own largest customer. Amazon Leo, Guowang and Qianfan are the only credible counterweights, and two of them are Chinese state-adjacent.

## Open questions

- No operator publishes internal cost per flight. All "cost per kg" here is list price or explicitly labelled estimate.
- Starship payload figures by Block are stated design targets; none has been demonstrated with a customer payload.
- Chinese payload capacities are from state and secondary sources and should be read as nominal.
- Qianfan deployed satellite count as of mid-2026 not verified.
- 2015–2024 launch attempt totals in the cadence table are widely reported round figures and were not each individually verified in this pass.

## Sources

- [2025 in spaceflight](https://en.wikipedia.org/wiki/2025_in_spaceflight) — Wikipedia, accessed 2026-08-25
- [Falcon 9](https://en.wikipedia.org/wiki/Falcon_9) — Wikipedia, accessed 2026-08-25
- [SpaceX Starship](https://en.wikipedia.org/wiki/SpaceX_Starship) — Wikipedia, accessed 2026-08-25
- [Vulcan Centaur](https://en.wikipedia.org/wiki/Vulcan_Centaur) — Wikipedia, accessed 2026-08-25
- [Ariane 6](https://en.wikipedia.org/wiki/Ariane_6) — Wikipedia, accessed 2026-08-25
- [New Glenn](https://en.wikipedia.org/wiki/New_Glenn) — Wikipedia, accessed 2026-08-25
- [Electron (rocket)](https://en.wikipedia.org/wiki/Electron_(rocket)) — Wikipedia, accessed 2026-08-25
- [Rocket Lab Neutron](https://en.wikipedia.org/wiki/Rocket_Lab_Neutron) — Wikipedia, accessed 2026-08-25
- [Long March (rocket family)](https://en.wikipedia.org/wiki/Long_March_(rocket_family)) — Wikipedia, accessed 2026-08-25
- [LandSpace](https://en.wikipedia.org/wiki/LandSpace) — Wikipedia, accessed 2026-08-25
- [Starlink](https://en.wikipedia.org/wiki/Starlink) — Wikipedia, accessed 2026-08-25
- [Kuiper Systems / Amazon Leo](https://en.wikipedia.org/wiki/Kuiper_Systems) — Wikipedia, accessed 2026-08-25
- [Guowang](https://en.wikipedia.org/wiki/Guowang) — Wikipedia, accessed 2026-08-25
- [LE-9](https://en.wikipedia.org/wiki/LE-9) — Wikipedia, accessed 2026-08-25 (H3 flight dates)

