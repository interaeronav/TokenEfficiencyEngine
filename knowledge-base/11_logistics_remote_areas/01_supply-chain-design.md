---
id: logistics.supply_chain_design
title: Designing a supply chain for a remote construction site
domain: 11_logistics_remote_areas
tags: [supply-chain, consolidation, just-in-time, order-batching, safety-stock, ftl, ltl, buffer, staging-depot, eoq, lead-time-variance, namibia, okongo]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "The Trans-Cunene Corridor", url: "https://www.wbcg.com.na/the-trans-cunene-corridor/", publisher: "Walvis Bay Corridor Group", accessed: 2026-08-25}
  - {title: "Weighbridges and legal load limits", url: "https://www.ra.org.na/weighbridge", publisher: "Roads Authority of Namibia", accessed: 2026-08-25}
  - {title: "Okongo", url: "https://en.wikipedia.org/wiki/Okongo", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Humanitarian logistics — pre-positioning and warehousing", url: "https://en.wikipedia.org/wiki/Humanitarian_logistics", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Geography of Namibia — rainy seasons", url: "https://en.wikipedia.org/wiki/Geography_of_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
related: [logistics.overview, logistics.cost_modelling_remote, logistics.procurement_lead_times, logistics.risk_contingency]
unit_system: SI
---

# Designing a supply chain for a remote construction site

**Summary.** Remote-site supply chain design is the deliberate choice of **how many times material will travel to site, how big each consignment is, and how much stock sits between the site and its next delivery**. Urban construction defaults to just-in-time because replenishment is cheap and fast; at 600–1 000 km from the source with an unsealed last mile, that default is wrong and expensive. This file sets out the consolidation-versus-JIT trade-off, order batching and full-truckload economics, safety stock sized against lead-time *variance* rather than average demand, staging depots, and a decision framework with worked numbers for a hypothetical 400 m² institutional building at Okongo.

> ⚠️ All monetary rates in this file are **illustrative planning assumptions**, not quoted prices. No verified published Namibian road-freight tariff was obtainable in this pass. Replace every rate with a real quotation before using the arithmetic for a tender. `needs-verification`

## Key facts

| Planning parameter | Assumed value | Basis |
|---|---|---|
| Interlink / superlink payload | **30–34 t** | Within the 56 000 kg Namibian permissible GVM |
| Tri-axle rigid + drawbar payload | **~28 t** | — |
| 8–10 m rigid flatbed payload | **8–10 t** | — |
| 4×4 LDV payload | **~1 t** | Last-mile / emergency only |
| Assumed line-haul rate, Windhoek → Okongo, FTL | **N$28 000** per trip | Illustrative |
| Assumed line-haul rate, Oshakati → Okongo, FTL | **N$7 500** per trip | Illustrative |
| Assumed part-load (LTL) rate | **N$1.45 per kg** min. 1 000 kg | Illustrative |
| Cement bags per 30 t load | **600 bags** at 50 kg | Arithmetic |
| Stock-standard bricks per 30 t load | **~9 000** at 3.3 kg each | Arithmetic |

## 1. The fundamental trade-off

Every supply chain balances two cost families:

- **Ordering / transport cost** — falls as consignments get larger and fewer.
- **Holding cost** — rises as consignments get larger, because more stock sits on site longer: tied-up cash, storage, deterioration, damage and theft.

In a city the transport cost per order is small, so the optimum sits at many small orders — just-in-time. On a remote site the transport cost per order is large and *lumpy* (a truck is a truck), so the optimum shifts hard toward **consolidation**.

There is a third family that urban models usually ignore and remote sites cannot: **stockout cost**. On a village site a stockout does not mean a 2-hour delay, it means an idle crew and possibly a demobilisation. This pushes the optimum further toward larger consignments *and* toward buffer stock.

### The economic order quantity, adapted

The textbook EOQ is `Q* = √(2DS/H)` where `D` is annual demand, `S` is cost per order and `H` is holding cost per unit per year. For remote construction, use it as a *sanity check*, not a rule, because:

- `D` is not steady — it is a construction programme with peaks.
- `S` is not constant — it steps at each vehicle capacity.
- The real constraint is usually **truck capacity**, not the EOQ.

The practical version: **round every order up to a whole vehicle unless the material is perishable, fragile or cash-critical.**

## 2. Full truckload versus part loads — the economics

Take the illustrative Windhoek → Okongo FTL rate of N$28 000 for 30 t payload.

| Consignment | Freight cost | Freight per tonne | Freight per tonne vs FTL |
|---|---|---|---|
| 30 t (full) | N$28 000 | **N$933/t** | baseline |
| 20 t (FTL vehicle, part-filled) | N$28 000 | N$1 400/t | +50 % |
| 10 t (FTL vehicle, part-filled) | N$28 000 | N$2 800/t | +200 % |
| 10 t as LTL at N$1.45/kg | N$14 500 | N$1 450/t | +55 % |
| 3 t as LTL at N$1.45/kg | N$4 350 | N$1 450/t | +55 % |

Two lessons fall out immediately.

1. **Never hire a full vehicle and part-fill it.** If you cannot fill it, buy groupage (LTL) instead. The LTL rate is worse per tonne than a *full* FTL but far better than a *half-empty* FTL.
2. **The FTL break-even against LTL** is where `FTL cost = LTL rate × mass`. Here: N$28 000 ÷ N$1.45/kg = **19 310 kg**. Above ~19.3 t, book the truck; below it, use groupage. Compute this number once for each lane on the project and put it on the buying office wall.

### The volume-versus-mass trap

A truck fills up two ways: it reaches its **payload mass** or it reaches its **deck volume**. Dense goods (cement, steel, sand) mass out; bulky light goods (insulation, roof sheeting, empty tanks, timber) cube out. A 13.6 m tri-axle trailer offers roughly 33–34 standard pallet positions.

The practical consequence: **plan mixed loads deliberately**. A load of cement alone will mass out at ~30 t on half the deck, leaving volume unused. Pair it with something light — insulation, sheeting bundles, formwork ply — and you have effectively moved the light goods for free. This is the single easiest saving on a remote project and it requires only that the buying office schedules two suppliers to deliver into the same consolidation window.

## 3. Consolidation policy: the delivery calendar

Rather than ordering material when each trade needs it, remote projects should run a **fixed delivery calendar**: a small number of pre-declared dates on which a vehicle will arrive, publicised to every supplier and every trade at the start of the job.

A workable calendar for a 9-month village building:

| Wave | Timing | Contents | Vehicles |
|---|---|---|---|
| **W0 — Enabling** | Week −2 | Site accommodation, fencing, container stores, water tanks, first fuel, hand tools, setting-out equipment | 1 × 30 t |
| **W1 — Substructure** | Week 1 | Cement, reinforcement (cut and bent), DPC, formwork ply, hardcore binder, blockmaking mould/machine | 1–2 × 30 t |
| **W2 — Superstructure** | Week 8 | Cement, lintels, remaining rebar, scaffold, door and window frames (build-in), fixings | 2 × 30 t |
| **W3 — Roof** | Week 16 | Trusses or timber, sheeting, purlins, insulation, flashings, fixings, gutters | 2 × 30 t (one cubes out) |
| **W4 — Envelope and services** | Week 22 | Glazing, doors, plumbing, conduit, cable, sanitaryware, tanks | 1 × 30 t + 1 LTL |
| **W5 — Finishes** | Week 30 | Plaster and screed materials, tiles, paint, ironmongery, joinery | 1 × 30 t |
| **W6 — Snag and handover** | Week 36 | Snag list items, spares, landscaping, signage | 1 LTL |

Seven to nine vehicle movements for a whole building, against perhaps forty if each trade ordered independently. At the illustrative N$28 000 per FTL, the difference between 8 and 20 deliveries is roughly **N$336 000** — often more than the entire preliminaries budget of a small village project.

Rules that make a delivery calendar hold:
- **Cut-off discipline.** Anything not on the requisition list by the cut-off date (typically 3 weeks before a wave, driven by supplier lead times) waits for the next wave. Publish the cut-offs.
- **One consolidation point.** All suppliers deliver to a single yard, where the load is checked, packed and dispatched as one.
- **No exceptions without a signed variance.** The moment ad-hoc trips are allowed, the calendar collapses.
- **Seasonal weighting.** Front-load the calendar so the heaviest waves land **before February** (see the rainy season note below).

## 4. Where just-in-time still applies

Consolidation is the default, not a religion. Keep JIT for:

- **Ready-mixed concrete** — perishable within roughly 2 hours of batching; it either comes JIT or it is site-batched.
- **Fresh-dated cement** — see below; do not buy 9 months of cement in month 1.
- **Fuel** — subject to storage licensing and fire risk; deliver against consumption.
- **High-value, theft-prone finishes** — taps, ironmongery, cable, solar equipment. Bring these in the last waves, and only when there is a lockable, alarmed store.
- **Anything measured off the actual structure** — glazing cut to opening size, worktops, some joinery. Ordering these early guarantees a remake.

## 5. Safety stock: size against variance, not average

The classic formula for safety stock under variable demand and variable lead time is:

```
SS = z × √( LT × σ_d²  +  d² × σ_LT² )
```

where `z` is the service-factor for the desired service level (z = 1.65 for 95 %, 2.33 for 99 %), `LT` is mean lead time, `σ_d` is the standard deviation of demand per period, `d` is mean demand per period, and `σ_LT` is the standard deviation of lead time.

On a remote construction site, `σ_LT` usually dominates. Worked example, cement for a blockmaking operation:

- Mean consumption `d` = **40 bags/day**, `σ_d` = **12 bags/day**
- Mean replenishment lead time `LT` = **14 days**, `σ_LT` = **6 days**
- Target service level 95 %, so `z` = **1.65**

```
LT × σ_d²      = 14 × 144        = 2 016
d² × σ_LT²     = 1 600 × 36      = 57 600
√(2 016 + 57 600) = √59 616      ≈ 244
SS = 1.65 × 244                  ≈ 403 bags
```

Roughly **400 bags** — about 20 tonnes, two thirds of a truck. Note that lead-time variance contributes **96 %** of the variance term. Halving `σ_LT` from 6 days to 3 days:

```
d² × σ_LT² = 1 600 × 9 = 14 400
√(2 016 + 14 400) = √16 416 ≈ 128
SS = 1.65 × 128 ≈ 212 bags
```

**Cutting lead-time variance in half nearly halves the required buffer.** That is why a reliable supplier at a 5 % premium is usually cheaper than an unreliable one at list price — the premium is paid back in released working capital and reduced spoilage.

### Reorder point

```
ROP = d × LT + SS = 40 × 14 + 403 ≈ 963 bags
```

So the site places a cement order whenever stock falls to about 960 bags. In practice on a wave calendar this becomes a *check*: at each cut-off date, does projected stock at the next wave date fall below the ROP? If yes, that wave must carry cement.

### The cement caveat

Bagged cement does not keep indefinitely — in a humid northern Namibian summer, air-set lumps and strength loss appear in months, not years. So the safety-stock answer must be capped by shelf life: hold no more cement than can be consumed within a conservative storage window (see `04_site-logistics-and-storage.md`). Where the calculated buffer exceeds the shelf-life cap, the correct response is not to hold more cement but to **reduce lead-time variance** or **shift to more frequent, smaller cement deliveries within a mixed load**.

## 6. Staging depots

A staging depot is an intermediate stock point between the long haul and the site — typically rented yard or container space in the nearest real town. For Okongo, the candidates are **Ondangwa, Oshakati or Eenhana**.

**What a depot buys you:**
- It decouples the long haul from the last mile. A 34 t interlink from Windhoek can reach a tarred-road town reliably; from there a smaller, more agile vehicle serves the site.
- It converts a long, high-variance lead time into a short, low-variance one. In the safety-stock arithmetic above, moving replenishment from Windhoek (`LT` 14 ± 6 days) to a depot 130 km away (`LT` 2 ± 1 days) collapses the buffer to a few days' cover.
- It provides a rain-season hedge: material can be pushed to the depot before February even if the site cannot receive it.
- It gives you somewhere to reject to. Damaged goods are refused at the depot, not carried to site and back.

**What it costs:** rent, a storekeeper, double handling (every item is loaded and unloaded one extra time — budget 2–4 % additional damage), and additional last-mile freight.

**Decision rule.** A depot is justified when *either* the last mile is unreliable (seasonal, weight-restricted, or requiring different vehicles) *or* the project value is large enough that the depot's fixed cost is small against the buffer it releases. As a rough test: if annualised depot cost is less than the finance and spoilage cost of the safety stock it eliminates, plus the value of avoided delay, take the depot.

*Worked comparison, illustrative:*

| | No depot | Ondangwa depot |
|---|---|---|
| Long-haul freight, 8 × FTL Windhoek→site | 8 × N$28 000 = N$224 000 | 8 × N$24 000 (Windhoek→Ondangwa) = N$192 000 |
| Last-mile freight | — | 14 × N$6 500 (Ondangwa→Okongo) = N$91 000 |
| Depot rent, 9 months | — | N$4 500 × 9 = N$40 500 |
| Storekeeper, 9 months | — | N$6 000 × 9 = N$54 000 |
| Additional handling damage @ 3 % on N$1.8 m of goods | — | N$54 000 |
| Safety stock held on site | N$620 000 tied up | N$180 000 tied up |
| Finance on stock @ 11 %/yr over 9 months | N$51 150 | N$14 850 |
| **Total logistics cost** | **N$275 150** | **N$446 350** |

On these illustrative numbers, the depot **loses** by about N$171 000 — which is the usual answer for a single small building on a tarred approach. The depot wins when (a) the last mile is genuinely unsealed and seasonal, (b) several projects share it, or (c) the programme value of avoided delay exceeds the gap. Run the arithmetic; do not assume either answer.

## 7. Decision framework

Work through in order. Each step constrains the next.

1. **Classify every material by value density and criticality.**
   - Low value density + non-critical → source locally or make on site.
   - Low value density + critical (cement) → consolidate, buffer, protect.
   - High value density + non-critical → LTL whenever convenient.
   - High value density + critical (switchgear, pumps, specified joinery) → order early, expedite, carry spares.
2. **Compute the FTL/LTL break-even mass for each lane.** (`FTL price ÷ LTL rate per kg`.)
3. **Fix the delivery calendar** from the construction programme, weighted before the rains.
4. **Test each wave for mass and volume.** Fill light goods around heavy ones.
5. **Size safety stock from lead-time variance** for the three or four materials that would stop work.
6. **Cap buffers by shelf life and theft exposure.**
7. **Test the staging-depot case explicitly** with the arithmetic above.
8. **Write the cut-off dates into the subcontract documents** so trades cannot demand ad-hoc trips.
9. **Nominate one person** who owns the calendar and has authority to refuse an off-calendar trip.

## Open questions

- All freight rates here are illustrative. Obtain real Windhoek→Okongo and Oshakati→Okongo FTL and LTL quotations. `needs-verification`
- Realistic bagged-cement shelf life under Ohangwena summer humidity has not been sourced; the 3-month working assumption in `04` needs manufacturer confirmation.
- Yard rental rates in Ondangwa/Oshakati are assumed, not quoted.

## Sources

- [The Trans-Cunene Corridor](https://www.wbcg.com.na/the-trans-cunene-corridor/) — Walvis Bay Corridor Group, accessed 2026-08-25
- [Weighbridges and legal load limits](https://www.ra.org.na/weighbridge) — Roads Authority of Namibia, accessed 2026-08-25
- [Okongo](https://en.wikipedia.org/wiki/Okongo) — Wikipedia, accessed 2026-08-25
- [Humanitarian logistics](https://en.wikipedia.org/wiki/Humanitarian_logistics) — Wikipedia, accessed 2026-08-25 (pre-positioning and warehouse typology)
- [Geography of Namibia](https://en.wikipedia.org/wiki/Geography_of_Namibia) — Wikipedia, accessed 2026-08-25 (rainy seasons)
