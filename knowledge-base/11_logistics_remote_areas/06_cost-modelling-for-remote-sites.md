---
id: logistics.cost_modelling_remote
title: Cost modelling for remote sites — landed cost and make-or-buy
domain: 11_logistics_remote_areas
tags: [landed-cost, cost-model, freight-cost, wastage, risk-premium, break-even, blockmaking, cement, bricks, roof-sheeting, joinery, okongo, oshakati, windhoek, namibia]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Weighbridges and legal load limits", url: "https://www.ra.org.na/weighbridge", publisher: "Roads Authority of Namibia", accessed: 2026-08-25}
  - {title: "Southern African Customs Union", url: "https://en.wikipedia.org/wiki/Southern_African_Customs_Union", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Ohorongo Cement", url: "https://en.wikipedia.org/wiki/Ohorongo_Cement", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "The Trans-Cunene Corridor", url: "https://www.wbcg.com.na/the-trans-cunene-corridor/", publisher: "Walvis Bay Corridor Group", accessed: 2026-08-25}
  - {title: "Okongo", url: "https://en.wikipedia.org/wiki/Okongo", publisher: "Wikipedia", accessed: 2026-08-25}
related: [logistics.supply_chain_design, logistics.transport_freight.southern_africa, logistics.local_sourcing_community, materials.procurement_pricing]
unit_system: SI
---

# Cost modelling for remote sites — landed cost and make-or-buy

**Summary.** The only price that matters on a remote site is the **landed, installed, wastage-adjusted cost per unit of finished work**. Ex-works price is a component of it and frequently a misleading one — the cheapest ex-works supplier is routinely the most expensive delivered. This file sets out a landed-cost model, applies it to four representative materials moving to Okongo (cement, bricks, roof sheeting, joinery), and works the break-even for making concrete blocks on site against buying them in.

> ⚠️ **Every monetary figure in this file is an illustrative planning assumption, not a quoted price.** No verified Namibian material or freight price list was obtainable in this pass. The arithmetic and the structure are the content; substitute real quotations before using any number. `needs-verification`

## Key facts

| Model input | Assumed value |
|---|---|
| Freight, Windhoek → Okongo, FTL 30 t | **N$28 000** per trip (N$933/t) |
| Freight, Oshakati → Okongo, FTL 30 t | **N$7 500** per trip (N$250/t) |
| Freight, LTL groupage | **N$1.45/kg** |
| Working capital finance rate | **11 % per annum** |
| Customs duty, RSA → Namibia | **Nil** (SACU common customs area) |
| VAT | **15 %**, recoverable by a registered vendor — excluded from all figures below |
| Cement bag | **50 kg**, 20 bags/tonne |
| Stock brick mass | **3.3 kg** |
| 390 × 190 × 190 hollow block | **~18 kg**, **12.5 blocks/m²** of wall |

## 1. The landed cost model

```
LANDED COST per unit
  =  Ex-works price
   +  Freight (allocated)
   +  Handling (loading, offloading, double handling, on-site movement)
   +  Duty and non-recoverable taxes
   +  Finance (cost of capital over the days held)
   +  Risk premium (expected loss from damage, rejection, theft in transit)

EFFECTIVE COST per unit installed
  =  Landed cost  ÷  (1 − wastage fraction)
```

**Component notes.**

- **Freight allocation.** Allocate by the constraint that actually filled the vehicle: by **mass** when the load massed out, by **volume (or deck metres)** when it cubed out. Allocating a mixed load pro-rata by value is the common error and it systematically over-charges the light, valuable goods and under-charges the heavy ones — exactly backwards.
- **Handling.** Include every touch. A depot adds two touches; a hand offload adds labour and breakage; a truck-mounted crane adds a line item but removes both.
- **Duty.** **Nil within SACU** (Botswana, Eswatini, Lesotho, Namibia, South Africa share a common external tariff and free interchange of goods). For non-SACU imports, duty is charged at the first point of entry into the union. Do not confuse "no duty" with "no paperwork" or "no import VAT".
- **Finance.** `value × rate × days held ÷ 365`. Days held runs from payment (often a deposit at order) to the day the material is built in — which on a wave-based remote project is a long time.
- **Risk premium.** The expected value of loss in transit: `probability × loss`. It rises with distance, unsealed road, fragility and theft appeal. Handle it as an explicit percentage rather than pretending it is zero.
- **Wastage.** The divisor, not an addition. 8 % wastage on a N$7.58 brick makes the installed brick N$8.24, not N$8.19.

## 2. Worked example — cement to Okongo

Three sourcing options for 50 kg bagged cement. Namibian cement is domestically produced (Ohorongo at Otavi, ~0.7 Mt/yr since December 2010; plus Cheetah Cement), so this is a domestic distribution problem, not an import one.

| Component | **A: Windhoek merchant, FTL** | **B: Oshakati merchant, FTL** | **C: Okongo retail** |
|---|---|---|---|
| Ex-works per bag | N$95.00 | N$112.00 | N$135.00 |
| Freight per bag | N$46.67 (28 000 ÷ 600) | N$12.50 (7 500 ÷ 600) | N$3.00 |
| Handling per bag | N$1.80 | N$1.80 | N$1.00 |
| Duty | 0 | 0 | 0 |
| **Subtotal** | **N$143.47** | **N$126.30** | **N$139.00** |
| Finance (days held) | 60 d → N$2.59 | 30 d → N$1.14 | 7 d → N$0.29 |
| Risk premium | 3 % → N$4.30 | 2 % → N$2.53 | 1 % → N$1.39 |
| **Landed per bag** | **N$150.36** | **N$129.97** | **N$140.68** |
| Wastage | 4 % | 3 % | 2 % |
| **Effective per bag** | **N$156.63** | **N$133.99** | **N$143.55** |

**Result.** The **cheapest ex-works option (A) is 17 % more expensive delivered than option B**, and even the village retail price (C) beats it. Freight alone adds **49 %** to the Windhoek ex-works price.

**Reading.** For a low-value-density commodity over 660 km, freight dominates and the correct answer is to buy as close to site as the supply chain permits, accepting a materially higher shelf price. The Windhoek option only becomes competitive if the truck was going anyway with spare payload — in which case the *marginal* freight is near zero and A wins comfortably. This is the whole argument for consolidation.

## 3. Worked example — bricks to Okongo

Stock bricks at 3.3 kg. One 30 t load ≈ **9 000 bricks**.

| Component | Value |
|---|---|
| Ex-works, Windhoek | N$3.80 / brick |
| Freight | N$28 000 ÷ 9 000 = **N$3.11 / brick** |
| Handling (truck-mounted crane, N$2 500) | N$0.28 |
| **Subtotal** | N$7.19 |
| Finance, 45 days @ 11 % | N$0.10 |
| Risk premium 4 % | N$0.29 |
| **Landed** | **N$7.58** |
| Wastage 8 % (breakage on corrugation and hand-stacking) | ÷ 0.92 |
| **Effective per brick** | **N$8.24** |

**Freight is 82 % of the ex-works price.** At roughly 52 bricks per m² of single-skin brickwork, that is **N$428/m²** in masonry units alone before mortar or labour.

**Reading.** Fired brick freighted 660 km is close to indefensible for a village project. It is the textbook case for local production (see §6) or for a locally available alternative. The same arithmetic explains why Namibian rural construction is overwhelmingly cement-block, not brick.

## 4. Worked example — roof sheeting to Okongo

0.5 mm IBR profile, coated steel, roughly **4.6 kg per m² of cover**. Sheeting **cubes out** long before it masses out: a 13.6 m trailer will practically take about **2 000 m² ≈ 9.2 t** in bundles — i.e. **69 % of the payload capacity is unused**.

| Component | **A: dedicated vehicle** | **B: shared with 20 t of cement** |
|---|---|---|
| Ex-works per m² | N$185.00 | N$185.00 |
| Freight per m² | N$28 000 ÷ 2 000 = **N$14.00** | mass-allocated: (9.2 ÷ 29.2) × 28 000 = N$8 822 → **N$4.41** |
| Handling per m² | N$1.50 | N$1.50 |
| **Subtotal** | N$200.50 | N$190.91 |
| Finance, 30 d | N$1.81 | N$1.72 |
| Risk premium 3 % | N$6.02 | N$5.73 |
| **Landed per m²** | **N$208.33** | **N$198.36** |
| Wastage 7 % (cutting, edge damage, wind loss) | ÷ 0.93 | ÷ 0.93 |
| **Effective per m²** | **N$224.01** | **N$213.29** |

The cement in load B carries (20 ÷ 29.2) × N$28 000 = N$19 178, i.e. **N$47.95/bag** for 400 bags — only N$1.28 worse than the dedicated cement load's N$46.67. So combining the two:

- Two dedicated vehicles (600 bags + 2 000 m²) = **N$56 000** of freight.
- One combined vehicle (400 bags + 2 000 m²) = **N$28 000**, with 200 bags deferred to the next wave.

**Reading.** Where one material masses out and another cubes out, pairing them halves the freight bill for that wave. This requires only that the buying office schedules two suppliers into the same consolidation window — the cheapest saving available on a remote project.

## 5. Worked example — joinery from a Windhoek joiner

12 solid external doors with frames, ~55 kg each, N$6 500 each ex-works. **High value density: freight is trivial; packaging and damage risk are not.**

| Component | **A: crated** | **B: loose on the deck** |
|---|---|---|
| Ex-works | N$6 500.00 | N$6 500.00 |
| Freight, LTL 55 kg × N$1.45 | N$79.75 | N$79.75 |
| Crating / protection | N$450.00 | N$0.00 |
| Handling | N$40.00 | N$40.00 |
| **Subtotal** | N$7 069.75 | N$6 619.75 |
| Finance, 60 d @ 11 % | N$127.82 | N$119.68 |
| Risk premium | 2 % → N$141.40 | 6 % → N$397.19 |
| **Landed** | **N$7 338.97** | **N$7 136.62** |
| Damage/rework allowance | 1 % → ÷0.99 | 5 % → ÷0.95 |
| **Effective per door** | **N$7 413** | **N$7 512** |

**Reading.** Freight is **1.2 %** of the ex-works value — irrelevant. Crating costs 7 % and *saves* money because it collapses the damage probability. The general rule for high-value-density goods: **buy from the best supplier regardless of distance, and spend on protection, not on freight optimisation.** A damaged door 700 km from its maker is a 13-week problem (see `05`), and no freight saving covers that.

## 6. Break-even — making concrete blocks on site

The most consequential make-or-buy decision on a rural Namibian project.

### 6.1 Cost to make one 390 × 190 × 190 hollow block on site

| Input | Quantity | Rate | Cost |
|---|---|---|---|
| Cement (1 bag ≈ 30 blocks) | 1.67 kg | N$133.99 / 50 kg bag (option B above) | N$4.47 |
| Sand and aggregate | ~0.012 m³ | N$220 / m³ delivered from a local pit | N$2.64 |
| Water | ~4 L incl. curing | — | N$0.10 |
| Labour (team of 5, 800 blocks/day @ N$350/day) | — | N$1 750 ÷ 800 | N$2.19 |
| Curing, handling, stacking | — | — | N$0.30 |
| **Variable cost before rejects** | | | **N$9.70** |
| Rejects and breakage 6 % | ÷ 0.94 | | **N$10.32** |

### 6.2 Cost to buy one block delivered from a regional block yard

| Component | Value |
|---|---|
| Ex-yard, Eenhana / Ondangwa | N$14.50 |
| Freight and handling to site | included |
| Wastage 5 % | ÷ 0.95 |
| **Effective per block** | **N$15.26** |

**Saving per block by making on site: N$15.26 − N$10.32 = N$4.94.**

### 6.3 Fixed costs of setting up production

| Item | Purchase route | Hire route |
|---|---|---|
| Egg-layer block machine (800 blocks/day) | N$85 000 capital | N$450/day hire → N$0.56/block |
| Casting slab, curing area, water tank, moulds, covers | N$25 000 | N$25 000 |
| **Fixed total** | **N$110 000** | **N$25 000** |
| Variable cost per block | N$10.32 | N$10.88 |
| Saving per block | N$4.94 | N$4.38 |
| **Break-even quantity** | **110 000 ÷ 4.94 = 22 267 blocks** | **25 000 ÷ 4.38 = 5 708 blocks** |
| Equivalent wall area at 12.5 blocks/m² | **~1 781 m²** | **~457 m²** |

### 6.4 Reading the result

- **Below ~5 700 blocks (~460 m² of wall): buy them in.** Setting up production does not pay.
- **Between ~5 700 and ~22 300 blocks: hire the machine.** This is the range most single village buildings fall into.
- **Above ~22 300 blocks (~1 780 m² of wall, or a multi-building programme): buy the machine**, and treat it as an asset with residual or community value at the end.

### 6.5 Sensitivity

The result is most sensitive to the landed cement price and to labour productivity.

| Change | Effect |
|---|---|
| Cement landed at N$156.63 (Windhoek option A) instead of N$133.99 | Variable cost rises to **N$11.05**; saving falls to N$4.21; purchase break-even rises to **26 128 blocks** |
| Production drops from 800 to 500 blocks/day | Labour rises to N$3.50/block; variable cost N$11.71; saving falls to N$3.55; purchase break-even **30 986 blocks** |
| Reject rate rises from 6 % to 15 % | Variable cost rises to **N$11.41**; saving N$3.85; purchase break-even **28 571 blocks** |
| Bought-in block price rises to N$17.00 | Saving rises to N$7.58; purchase break-even falls to **14 512 blocks** |

### 6.6 The costs the arithmetic does not show

Make-or-buy is not only an arithmetic question. Making blocks on site adds:

- **Quality risk.** Site-made blocks vary. Without cube or block-crushing testing, mix discipline and consistent curing, strength can fall well below specification — and the failure appears in the wall, not in the yard. Budget for testing and reject ruthlessly.
- **Curing water demand.** Curing consumes more water than mixing. On a site with a marginal water supply this can be the binding constraint (see `04`).
- **Programme dependency.** Blocks need **7–28 days** of curing before use. Production must start weeks before the walls do, and a cement stockout now stops block production *and*, three weeks later, stops bricklaying.
- **Space.** A production and curing yard for 800 blocks/day needs meaningful laydown area and a level, drained slab.
- **Supervision.** An unsupervised block yard produces under-cemented blocks, because the person mixing has no incentive to use the full bag.
- **Community benefit.** On the other side of the ledger, on-site production creates local employment and a transferable skill, which has real value on a village project (see `07`).

## 7. Applying the model — a checklist

1. **Compute value density** (N$ per tonne ex-works) for every significant material. Sort the bill of quantities by it.
2. **For the bottom decile (heavy, cheap): find the nearest source, or make it.** Freight will dominate.
3. **For the top decile (light, valuable): buy the best, protect it, ignore freight.**
4. **Allocate freight by the binding constraint**, not by value.
5. **Deliberately pair a mass-out material with a cube-out material** in every wave.
6. **Carry finance cost explicitly.** On a wave-based project, material may be paid for 60–90 days before it is built in.
7. **Set the risk premium by lane and by fragility,** and review it against actual losses each month.
8. **Treat wastage as a divisor** and set it higher than urban norms — 8 % on brick, 7 % on sheeting, 3–4 % on cement is a reasonable starting point for a 660 km haul with an unsealed last mile.
9. **Test make-or-buy for every low-value-density item**, not just blocks: aggregate crushing, sand winning, on-site trussing, on-site bending of reinforcement.
10. **Re-run the model when any rate moves by more than 10 %.** The break-evens shift fast.

## Open questions

- Real ex-works prices for cement, blocks, brick, IBR sheeting and joinery in Windhoek, Oshakati and Okongo. `needs-verification`
- Real FTL and LTL freight quotations for the Windhoek→Okongo and Oshakati→Okongo lanes. `needs-verification`
- Block machine purchase and daily hire rates available in northern Namibia. `needs-verification`
- Local pit sand and aggregate delivered rates in the Okongo area, and their suitability for structural blockwork. `needs-verification`
- Current Namibian commercial working-capital finance rates. `needs-verification`

## Sources

- [Weighbridges and legal load limits](https://www.ra.org.na/weighbridge) — Roads Authority of Namibia, accessed 2026-08-25
- [Southern African Customs Union](https://en.wikipedia.org/wiki/Southern_African_Customs_Union) — Wikipedia, accessed 2026-08-25
- [Ohorongo Cement](https://en.wikipedia.org/wiki/Ohorongo_Cement) — Wikipedia, accessed 2026-08-25
- [The Trans-Cunene Corridor](https://www.wbcg.com.na/the-trans-cunene-corridor/) — Walvis Bay Corridor Group, accessed 2026-08-25
- [Okongo](https://en.wikipedia.org/wiki/Okongo) — Wikipedia, accessed 2026-08-25

