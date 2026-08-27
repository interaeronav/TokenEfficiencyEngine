---
id: aviation_industry.economics
title: Airline economics and finance
domain: 31_aviation_industry
tags: [airline-economics, rask, cask, yield-management, load-factor, revenue-management, ancillary, hub-and-spoke, sixth-freedom, leasing, sale-and-leaseback, fuel-hedging, alliances, low-cost-carrier, cargo, subsidy]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Airline Industry Financial Outlook (December 2025)", url: "https://www.iata.org/en/pressroom/2025-releases/2025-12-09-01/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "Global Outlook for Air Transport (June 2025)", url: "https://www.iata.org/en/pressroom/2025-releases/2025-06-02-01/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "Air Passenger Demand Falls 1.7% in June", url: "https://www.iata.org/en/pressroom/2026-releases/07-30-air-passenger-demand-falls-june/", publisher: "IATA", accessed: 2026-08-25}
  - {title: "AerCap", url: "https://en.wikipedia.org/wiki/AerCap", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Qatar Airways Group Delivers Robust Financial Performance Despite Global Economic Instability", url: "https://www.qatarairways.com/press-releases/en-WW/265838-qatar-airways-group-delivers-robust-financial-performance-despite-global-economic-instability/", publisher: "Qatar Airways", accessed: 2026-08-25}
related: [aviation_industry.overview, aviation_industry.operations, aviation_industry.map]
unit_system: SI
---

# Airline economics and finance

**Summary.** Airlines sell a perishable, capacity-constrained, capital-intensive service in a market with low barriers to entry, high barriers to exit, near-perfect price transparency and a cost base they mostly do not control. The consequence is an industry that generates enormous economic value for passengers, airports, manufacturers and lessors, and almost none for its own shareholders: IATA's December 2025 forecast for 2026 is US$1.053 trillion of revenue, US$41 billion of net profit, a 3.9% net margin and a 6.8% return on invested capital — a return that in most years has sat at or below the industry's weighted average cost of capital. This file covers the cost structure, the unit-economics metrics, revenue management, network economics including the sixth-freedom model Qatar Airways runs, fleet financing, the lessors, hedging, alliances, cargo, and the structural reasons for the profitability problem.

## Key facts

| Metric | 2024 | 2025 | 2026 (forecast) |
|---|---|---|---|
| Revenue | ~US$965 bn | US$1.008 trn | US$1.053 trn (+4.5%) |
| Net profit | US$32.4 bn | US$39.5 bn | US$41 bn |
| Net margin | 3.4% | 3.9% | 3.9% |
| Net profit per passenger | — | US$7.90 | US$7.90 |
| ROIC | — | 6.8% | 6.8% |
| Passengers | ~4.8 bn | ~5.0 bn | 5.2 bn (+4.4%) |
| Cargo | — | ~69.9 Mt | 71.6 Mt (+2.4%) |
| Jet fuel price | US$99/bbl | US$90/bbl | US$88/bbl |
| Fuel bill | US$261 bn | US$253 bn | US$252 bn |
| Passenger load factor | — | — | 83.8% (record) |

*Sources: IATA June 2025 release for 2024/2025 estimates; IATA December 2025 outlook for 2025 estimate and 2026 forecast. Note the two releases give slightly different 2025 figures because the December estimate supersedes the June forecast.*

> ⚠️ Demand turned in 2026. IATA's 30 July 2026 release reported global RPK **down 1.7% year on year in June 2026**, ASK down 1.3%, load factor 84.2%. Middle East carriers were down 13.9% with a 76.1% load factor; China domestic −5.2%, Japan −3.8%, US −1.2%. IATA attributed the picture to domestic weakness plus higher fuel prices and regional tensions. Any 2026 full-year forecast made in December 2025 should be treated as stale.

## 1. The cost structure

Cost shares vary hugely by business model, stage length and fuel price. The ranges below are typical for a network carrier at moderate fuel prices; an LCC shifts weight from labour and distribution into ownership and airport charges, and a long-haul operator shifts weight into fuel.

| Cost line | Typical share of operating cost | Notes |
|---|---|---|
| **Fuel** | 20–35% | The single most volatile line. IATA's 2026 forecast has fuel at US$252 bn against US$913–1,010 bn of expenses, ~24–25%. Consumption per ASK is a fleet and network property; price is not controllable. |
| **Labour** | 18–35% | Higher in the US and Western Europe, lower in Asia and the Gulf. Includes flight crew, cabin crew, engineering, ground, admin. Pilot pay is a small share of total cost but the most visible. |
| **Aircraft ownership** | 10–18% | Depreciation plus interest for owned, or lease rentals for leased. IFRS 16 moved operating leases onto the balance sheet from 2019, splitting the rental into depreciation and interest — which flattered EBITDA and changed every historic comparison. |
| **Maintenance and overhaul** | 8–12% | Line, base, engine, components. Engine shop visits dominate; a widebody engine overhaul can run into eight figures. Deferred maintenance is the classic way a distressed airline hides losses. |
| **Airport and ground handling charges** | 6–12% | Landing, parking, passenger service charge, security, ground handling contracts, de-icing. |
| **En-route and terminal navigation charges** | 3–6% | ANSP charges. In Europe a function of √(MTOW/50) × distance/100 × unit rate. |
| **Distribution, sales and reservations** | 3–8% | GDS segment fees, agency commission, credit card merchant fees, own-site technology, loyalty accrual cost. |
| **Passenger services** | 3–6% | Catering, in-flight entertainment content, crew hotels and allowances, disruption costs. |
| **Other/overhead** | 5–10% | Insurance, property, IT, corporate. |

Two structural properties follow:

- **Very high operating leverage.** Around 60–70% of the cost of a departure is committed once the flight is scheduled — the aircraft, the crew, the slot, the fuel to fly it. Marginal cost of the last passenger is close to the cost of the meal plus the fuel to carry the mass. Therefore an airline will sell the last seat at almost any price above marginal cost, and therefore fare structures collapse in a downturn.
- **Cost is stage-length dependent.** Comparing CASK between a short-haul LCC and a long-haul network carrier is meaningless without stage-length adjustment, because fixed per-departure costs (landing fee, turnaround, crew duty) amortise over more ASKs on a longer sector. The standard correction is CASK × √(stage length / reference stage length), or a regression of CASK on stage length across a peer set.

## 2. Unit economics

The vocabulary:

- **ASK / ASM** — Available Seat Kilometre (Mile): one seat flown one kilometre. Capacity.
- **RPK / RPM** — Revenue Passenger Kilometre: one paying passenger flown one kilometre. Traffic.
- **Load factor (LF)** = RPK / ASK. IATA's 2026 forecast: 83.8%, a record.
- **Yield** = passenger revenue / RPK. The average fare per kilometre flown by a paying passenger.
- **RASK / RASM** = total revenue / ASK. Often split into **PRASK** (passenger only) and total RASK including ancillary and cargo.
- **RASK = Yield × Load Factor.** This identity is the whole of airline commercial strategy: you can raise RASK by charging more per passenger, or by filling more seats, and the two trade off against each other.
- **CASK / CASM** = operating cost / ASK. **CASK ex-fuel** is the standard measure of underlying cost discipline, because fuel is exogenous.
- **Break-even load factor (BELF)** = CASK / Yield. The load factor at which revenue equals cost. If BELF is 79% and achieved LF is 84%, the operation makes money; the gap is thin, which is why an airline can go from profit to loss on a 3-point demand move.
- **ATK / RTK / FTK** — the cargo equivalents (Available/Revenue Tonne Kilometre; Freight Tonne Kilometre).
- **Block hours** and **utilisation** (block hours per aircraft per day). LCC narrowbody utilisation of 11–13 h/day versus a legacy 8–9 h is a large part of the LCC cost advantage — the same ownership cost spread over 40% more ASKs.

**Sixth-freedom distortion.** For a carrier like Qatar Airways, RPK counts the *whole* journey, so a Manchester–Doha–Melbourne passenger contributes far more RPK than a point-to-point European passenger paying a similar fare. That makes yield (revenue/RPK) look low and RPK look high relative to a short-haul carrier. Comparing yields across business models without normalising for stage length and connect ratio produces nonsense.

## 3. Revenue management and fare buckets

The problem: a fixed, perishable inventory; a demand curve that shifts over time; and customers with wildly different willingness to pay who are indistinguishable at booking except by the fences you build.

**Fare structure.** Published fares are grouped into **booking classes** (Y, B, M, H, Q, V, W, S, T, L, K, N, O, R, G etc. in economy; J, C, D, I, Z in business; F, A, P in first). Each class carries a **fare basis code** with rules: advance purchase (AP7, AP14, AP21), minimum stay (a Saturday night rule, historically the key business/leisure fence), maximum stay, change and refund penalties, routing restrictions, combinability. The letters are inventory buckets, not products — the same seat is sold in twelve different buckets at twelve prices.

**Seat inventory control.** The RM system decides how many seats to protect for later, higher-yielding bookings.

- **Littlewood's rule** (two-class): accept a low fare booking only if its fare exceeds the higher fare multiplied by the probability that the higher-fare demand will exceed the remaining protected seats. Formally, protect *y* seats for class 1 where P(D₁ > y) = f₂/f₁.
- **EMSR-a / EMSR-b** (Expected Marginal Seat Revenue, Belobaba) — the standard multi-class generalisation. EMSR-b aggregates higher classes into a weighted-average fare and applies Littlewood against it. Still the workhorse in production systems.
- **Bid price control / network RM (O&D control)** — instead of leg-based nested booking limits, the system computes a shadow price (bid price) for each leg from a network linear program and accepts an itinerary only if its fare exceeds the sum of bid prices on the legs it uses. This is what makes hub economics work: it lets the system reject a cheap connecting passenger occupying a seat a high-fare local passenger wants, and accept a connecting passenger who fills an otherwise empty leg.
- **Dynamic pricing / continuous pricing** — the current frontier: abandoning discrete buckets and generating a price per request, informed by willingness-to-pay models and (via NDC) by who is asking. Lufthansa Group and several others have moved substantially to continuous pricing.
- **Overbooking** — sell more seats than exist, based on a forecast of no-shows, trading the cost of denied boarding (EU261 or DOT Part 250) against the cost of a spoiled seat. Overbooking levels have fallen as ticketing became non-refundable and no-show rates dropped.

**Inputs** the system needs: unconstrained demand forecasts by O&D, point of sale, booking class and days-to-departure; a no-show and cancellation forecast; competitive fare feeds (ATPCO fare filings, refreshed multiple times daily); and increasingly a customer-choice model. **Spiral-down** is the classic failure mode: if the forecast treats constrained (turned-away) demand as actual demand, it under-forecasts high-fare demand, opens more cheap inventory, and the error compounds.

## 4. Ancillary revenue

Unbundling turned the fare into a component and everything else into a sale. Categories:

- **À la carte** — checked bags, seat selection, priority boarding, extra legroom, change fees, onboard food and drink, WiFi, lounge access.
- **Commission-based** — hotel, car hire, insurance, ground transport, duty free.
- **Frequent flyer programme (FFP)** — selling miles to banks. This is the most important ancillary line and is frequently the most valuable asset an airline owns: during COVID, several US carriers financed themselves by pledging their loyalty programmes (United's MileagePlus and Delta's SkyMiles raised multi-billion-dollar secured facilities in 2020), and the standalone valuations placed on those programmes exceeded the airlines' own market capitalisations at the time. Air Canada's Aeroplan, Qantas Loyalty and Multiplus/Smiles have similar economics: a co-brand card issuer buys miles at a wholesale rate, the airline books high-margin revenue immediately and a deferred liability for redemption.
- **Fare families / branded fares** — Basic Economy, Economy Light/Classic/Flex. Technically a re-bundling: the point of Basic Economy is not to sell it but to make the next fare up look worth buying (a decoy in the behavioural-economics sense).

For ULCCs ancillary revenue routinely exceeds 40–50% of total revenue; Ryanair and Wizz publish it explicitly. For network carriers the FFP dominates the ancillary line. Specific per-passenger ancillary figures are published annually by IdeaWorks/CarTrawler and should be cited with the year.

## 5. Network economics

### Hub-and-spoke

*n* cities connected point-to-point require n(n−1)/2 routes; through a single hub they require n−1. With 100 spokes, a hub creates 4,950 city pairs from 100 routes. That combinatorial leverage is the entire argument for hubs: it converts thin O&D markets into viable ones by aggregating flows.

Costs of the model: connecting passengers pay less than local passengers for the same seat-kilometres (they have alternatives); hubs require **banks** (waves of arrivals followed by waves of departures) which force peaked infrastructure and idle aircraft and crew between banks; connections generate misconnects, baggage costs and disruption propagation; and a hub is a fixed asset that cannot be redeployed.

**Bank structure** — a hub can run *sharp banks* (short connection windows, high connectivity, poor asset utilisation, fragile to delay) or a *rolling/de-peaked hub* (continuous operation, better utilisation, longer connections, less connectivity). Delta and American de-peaked their hubs in the 2000s to cut cost and then largely re-peaked when RM systems improved. Gulf hubs run very pronounced banks — typically two or three main waves a day at Doha and Dubai, aligned to the Europe–Asia and Europe–Africa/Australasia time geometry.

**Connection quality** is measured by **MCT** (minimum connect time) and by the number of "quality connections" (usually defined as connections between MCT and ~3–4× MCT). Hub connectivity indices (ACI/SEO's NetScan model, IATA's connectivity index) rank hubs on weighted quality connections.

### Point-to-point

The LCC model: fly where the O&D demand exists, at high frequency on dense routes or low frequency on thin ones, without connecting product. Advantages: no bank peaking, no baggage transfer, no misconnect liability, high utilisation, secondary airports with lower charges and faster turns. Ryanair operates a near-pure version; easyJet and Wizz have added some self-connect facilitation; Southwest historically ran a point-to-point network with connecting itineraries sold but no bank structure.

### The Gulf sixth-freedom model

Geography does the work. Doha sits roughly 6–7 hours from most of Europe, the Indian subcontinent, East Africa, Central Asia and Southeast Asia, and within one-stop range of Australia, most of Africa, and eastern North America. A hub there can serve an enormous share of world city pairs with two narrow-to-widebody legs, where the same journey through a European hub would be a longer detour for Asia–Africa or Asia–Europe-South traffic.

The commercial logic:

1. **All-widebody or widebody-heavy fleet** — the legs are 5–8 hours, too long for narrowbodies at acceptable comfort and payload (although the A321LR/XLR now attacks the thinner end of this).
2. **Very high connect ratio** — the majority of passengers are connecting, so the hub's local market size is largely irrelevant. Qatar's local market is a few million people; the network is sized for global flows.
3. **Low unit cost enablers** — a home airport that is state-owned and prices to fill capacity rather than to maximise its own return; no aviation-specific taxes; a labour force on expatriate contracts with no personal income tax, which reduces gross pay for a given net; a young fleet with low maintenance cost and best-in-class fuel burn; and no legacy pension liabilities.
4. **Product-led yield premium** — competing for connecting traffic against European and Asian carriers on service, not just price.
5. **Cargo as a genuine second business**, not a belly by-product.
6. **Equity stakes and franchises to feed the hub** — Qatar Airways holds 25.1% of IAG (Feb 2020), 25% of Virgin Australia (Feb 2025), 49% of RwandAir (Feb 2020), 25% of Airlink (Aug 2024), ~10% of LATAM and ~9.99% of Cathay Pacific. Each is a feed and beyond-rights play as much as a financial investment.

The vulnerabilities are equally structural: the model has no domestic market to fall back on, so it is fully exposed to geopolitics and to any interruption of overflight rights. The June 2026 IATA data showing Middle East RPK down 13.9% year on year with a 76.1% load factor illustrates precisely this exposure.

## 6. Fleet planning and the ownership decision

**Fleet planning** answers: how many aircraft, of what type, when, and how financed. Inputs are the network plan (which drives range, payload and frequency requirements), the retirement schedule, maintenance cost curves, fuel price assumptions, residual value forecasts, and OEM delivery availability — which since 2020 has been the binding constraint more often than money.

Key trade-offs:

- **Commonality vs. right-sizing.** One type (Southwest's 737s, Ryanair's, Wizz's A320 family) minimises crew, training, spares and simulator cost; multiple types let you match capacity to demand precisely. The rule of thumb is that fleet commonality is worth more to a short-haul operator than a long-haul one.
- **Gauge vs. frequency.** More frequency wins business traffic and share disproportionately (the "S-curve": share of frequency maps to share of traffic non-linearly). Larger gauge cuts CASK. Slot-constrained airports force gauge.
- **New vs. mid-life.** A new aircraft costs more in ownership and less in fuel and maintenance; a 12-year-old aircraft is the reverse. The crossover depends heavily on the fuel price and on utilisation.

### Ownership structures

| Structure | Mechanics | Airline effect |
|---|---|---|
| **Cash purchase** | Buy outright | Lowest lifetime cost; heavy capital use; full residual value risk and reward |
| **Secured debt / mortgage** | Bank or capital markets debt secured on the airframe, Cape Town-registered | Airline owns the asset, carries the residual risk, keeps depreciation shield |
| **Finance (capital) lease** | Lessor holds title, airline has substantially all risks and rewards, usually with a bargain purchase option | On balance sheet pre- and post-IFRS 16; economically a purchase |
| **Operating lease** | Lessor keeps residual risk; 6–12 year term typical; return conditions specified in the lease | Fleet flexibility, no residual risk, higher cash cost, restrictive maintenance reserves and return conditions. Post-IFRS 16 it sits on balance sheet as a right-of-use asset and lease liability |
| **Sale-and-leaseback (SLB)** | Airline takes delivery of an aircraft it ordered, sells it to a lessor at delivery, leases it back | Monetises the OEM discount immediately, releases cash, converts capex to opex. A major source of "profit" at some LCCs — the gain on sale is real cash but is not recurring operating performance |
| **JOLCO** | Japanese Operating Lease with Call Option — Japanese equity investors take the tax depreciation | Cheap financing for good-credit airlines |
| **EETC** | Enhanced Equipment Trust Certificate — tranched, rated capital-markets debt secured on a pool of aircraft, relying on US Bankruptcy Code §1110 or Cape Town Alternative A | Very cheap for large investment-grade or near-IG carriers |
| **ECA-supported** | Export credit agency guarantee (US EXIM, UKEF, Bpifrance, Euler Hermes) under the OECD Aircraft Sector Understanding | Historically dominant for emerging-market carriers; largely dormant 2015–2020 when EXIM lost its quorum, since revived |

**Return conditions** are the hidden cost of operating leases: the aircraft must be handed back with specified remaining life on engines, landing gear, APU and airframe checks, in a specified cabin configuration, with complete records. Redelivery disputes are routine and expensive; "maintenance reserves" paid monthly to the lessor may or may not be reimbursable.

### The lessors

Roughly half the global fleet is leased. The lessor's business is **spread plus residual**:

- Buy at a large discount (they order in hundreds; list prices are fiction — actual transaction prices are commonly quoted as 40–55% below list, and no lessor publishes them).
- Fund at investment-grade cost of debt (AerCap, ALC, BOC and Avolon are IG-rated; this is the moat).
- Lease at a **lease rate factor** (monthly rental ÷ aircraft cost) historically around 0.7–0.9% per month for a new narrowbody, rising with interest rates.
- Sell the asset mid-life, or run it to part-out.

Principal players: **AerCap** (largest; revenue US$7.996 bn, net income US$2.099 bn FY2024; total assets US$71.44 bn at 2024; formed by the ILFC acquisition in 2014 and the US$30 bn GECAS acquisition completed November 2021 — US$24 bn cash, US$1 bn notes and ~46% of the combined equity to GE); **Air Lease Corporation** (Steven Udvar-Házy's second company, order-book-led, agreed in 2025 to be acquired by Sumitomo/SMBC — **[needs-verification]** on completion status); **SMBC Aviation Capital**; **BOC Aviation**; **Avolon** (Bohai); **ICBC Financial Leasing**; **Aircastle**; **Carlyle Aviation**; **Nordic Aviation Capital** (regional, restructured twice).

Lessors also provide the industry's shock absorber: in a downturn they repossess and re-lease rather than let capacity exit, which is one reason airline capacity is stickier than it should be, and one reason returns stay depressed.

### Valuation and residual values

Appraisers — **Ascend by Cirium**, **IBA**, **AVITAS**, **mba Aviation**, **Collateral Verifications** — publish **Current Market Value (CMV)**, **Base Value** (an idealised value assuming a balanced market) and **Half-Life** vs **Full-Life** adjusted values (reflecting position in the maintenance cycle). Lenders typically use the average of three appraisals.

Residual value drivers: production status (a type still in production holds value; the moment production ends, values fall), number of operators and geographic spread of the user base, engine variant commonality, freighter conversion potential, and fuel price. The A380 is the canonical residual-value disaster (no secondary market, no freighter conversion, part-out only). The 737-800 and A320ceo are the canonical successes, sustained by a huge operator base and P2F conversion demand.

## 7. Fuel hedging

Airlines hedge to reduce cash-flow volatility, not to make money. Instruments: swaps (fix the price), call options and collars (cap the downside cost while retaining some benefit from falls), and crack-spread or crude proxies where jet fuel derivatives are illiquid — jet is usually hedged with Brent or gasoil, leaving **basis risk**.

Considerations:

- Hedging is only sensible if the airline's revenue does *not* move with fuel. On routes where competitors also hedge similarly, fares adjust and hedging becomes a bet.
- The classic failure is hedging into a collapse: a hedged airline in 2014–15 or 2020 pays above-market for fuel while unhedged rivals cut fares. Several airlines took nine-figure hedging losses in Q1 2020 when the collapse in demand meant the hedged volumes were never burned.
- **Southwest** built a decade of profitability on long-dated hedges in the 2000s and is the standard case study. **Ryanair** hedges heavily and far forward; **Delta** took the unusual step of buying the Trainer refinery (2012) to capture the crack spread directly.
- Gulf carriers historically hedge less, partly because their sovereign owners are net long oil — a natural hedge at the state level.

## 8. Alliances and joint ventures

Three tiers of cooperation, with very different economics:

1. **Interline and codeshare.** Interline is the baseline: ticketing and baggage acceptance between carriers under IATA multilateral agreements, settled through the Clearing House. Codeshare puts one carrier's designator on another's flight, improving display position in GDS and enabling single-ticket sales.
2. **Global alliances.** **Star Alliance** (founded 1997), **oneworld** (1999), **SkyTeam** (2000). They deliver reciprocal frequent flyer earn and burn, lounge access, coordinated schedules and joint procurement. They do **not** allow pricing or capacity coordination — that would be a cartel. Their value has eroded as the real money moved to JVs and as low-cost carriers proved that customers will book two separate tickets.
3. **Metal-neutral joint ventures with antitrust immunity.** This is where the economics actually are. Under an ATI JV the partners pool revenue and cost on defined markets and share the result according to an agreed formula, so each is indifferent to whose aircraft the passenger sits on. They can coordinate schedule, capacity and price. The major transatlantic JVs are Delta/Air France-KLM/Virgin Atlantic, United/Lufthansa Group/Air Canada (A++), and American/IAG/Finnair; transpacific and Europe–Asia equivalents exist. Regulators grant immunity subject to slot remedies and periodic review.

Qatar Airways' approach has been minority equity stakes plus commercial agreements rather than deep metal-neutral JVs, in part because its sixth-freedom flows compete with, rather than complement, its partners' hubs.

## 9. The low-cost model and its variants

Southwest's original recipe (1971 onward): one aircraft type, one cabin, no assigned seats, no interline, no meals, secondary/uncongested airports, high utilisation, point-to-point, direct distribution, high employee productivity, simple fares.

European adaptation (Ryanair, 1990s): all of the above, plus aggressive ancillary unbundling, extreme cost focus (secondary airports paying incentives, single-supplier procurement, sale-and-leaseback and later outright ownership of a very large fleet bought counter-cyclically), and the willingness to close a base overnight if the economics change.

Variants:

- **ULCC** — Wizz Air, Spirit, Frontier, VivaAerobús. Higher seat density, lower base fares, ancillary >50% of revenue.
- **Hybrid / value carrier** — easyJet, JetBlue, Vueling: LCC cost base with assigned seating, primary airports, corporate sales and sometimes a business product.
- **Long-haul low cost** — the graveyard. Laker, People Express, Oasis Hong Kong, Norwegian Long Haul, Primera, WOW, Level (partly). The model fails because the LCC cost advantages (utilisation, turnaround, secondary airports, single fleet) shrink with stage length while the disadvantages (no premium cabin, no cargo, no connecting feed, high fuel exposure per seat) grow. Scoot, AirAsia X and Norse Atlantic continue in modified forms; IndiGo's long-haul ambitions with the A350 are the current test case.
- **LCC subsidiaries of legacy groups** — Transavia (Air France-KLM), Eurowings (Lufthansa), Vueling (IAG), Jetstar (Qantas), Scoot (SIA). Mixed record: the cost base rarely reaches true LCC levels because of group labour agreements.

## 10. Cargo economics

Cargo is roughly 10–15% of industry revenue in a normal year, and was the thing that kept many passenger airlines alive in 2020–21 when yields spiked several-fold.

Structure:

- **Belly capacity** on passenger aircraft — marginal cost is close to zero (the fuel to carry the mass), so belly capacity floods the market whenever passenger networks are healthy and depresses freighter economics.
- **Freighters** — production freighters (777F, 747-8F, A350F from ~2027) and passenger-to-freighter conversions (737-800BCF/BDSF, A321P2F, 767-300BDSF, A330P2F).
- **Integrators** — FedEx, UPS, DHL: door-to-door networks with their own hubs and ground fleets. Different business entirely: a logistics company that owns aircraft.
- **Forwarders** — Kuehne+Nagel, DHL Global Forwarding, DSV, Expeditors — buy capacity in bulk and sell to shippers. Airlines mostly do not sell to shippers directly.

Metrics: **FTK**, **AFTK**, **cargo load factor**, **yield per kg**. Demand is driven by global trade, inventory cycles, and the substitution boundary with ocean freight (about 1% of world trade by weight, ~35% by value moves by air). E-commerce, and specifically the cross-border parcel flows out of China, became a dominant driver in the 2020s; changes to de minimis import thresholds are a direct policy risk to that flow.

Qatar Airways Cargo is one of the largest international cargo carriers, reporting **1.43 million tonnes of chargeable weight and a 12% global cargo market share in FY2025/26** (Qatar Airways, 20 May 2026).

## 11. State ownership and the subsidy dispute

A large share of the world's airlines are state-owned or state-backed: the Gulf carriers, Turkish (49% state), Ethiopian, Singapore Airlines (Temasek), Air India (until 2022), Aeroflot, China's big three, LOT, TAP, and until recently most flag carriers everywhere.

The dispute that defined 2015–2018 was the US "Big Three" (Delta, United, American) and the European legacy groups alleging that Emirates, Qatar Airways and Etihad had received tens of billions of dollars in subsidies contrary to the spirit of Open Skies — interest-free shareholder loans, assumed fuel-hedging losses, below-cost airport charges, and sovereign guarantees. The Gulf carriers responded that their accounts were audited, that European carriers had received far larger historical state aid and continued to benefit from bankruptcy protection and slot grandfathering, and that the complaint was protectionism.

Outcome: in 2018 the US concluded "understandings" with the UAE and Qatar under which the Gulf carriers agreed to publish audited annual accounts to international standards and to disclose significant related-party transactions, with a voluntary expectation of restraint on fifth-freedom flights to the US. No formal finding of subsidy was made and no traffic rights were withdrawn. The COVID state aid wave (Lufthansa's €9 bn, Air France-KLM's €10.4 bn, Alitalia/ITA, TAP, SAS, and the US CARES Act payroll support of tens of billions) largely ended the moral argument.

The economically interesting question is not whether subsidy occurred but whether the Gulf model's cost advantage is *primarily* subsidy or *primarily* structural: no income tax, no legacy pensions, a young fleet, geography, an owner willing to accept a low return on the airport and to take a long view. The evidence points substantially to the latter, which is why the complaint failed.

## 12. The structural profitability problem

Over the whole jet era, the airline industry has destroyed capital: cumulative net profit has been near zero or negative, and ROIC has averaged below WACC in most years. The causes are well identified in the literature (Doganis; Belobaba/Odoni/Barnhart; Michael Porter's five forces applied to airlines):

1. **Perishability plus high fixed costs** drives marginal-cost pricing whenever capacity exceeds demand.
2. **Near-zero product differentiation in economy** and perfect price transparency via metasearch.
3. **Low barriers to entry** — aircraft are available on operating lease within months, crews are trainable, and slots exist at secondary airports.
4. **Very high barriers to exit** — political resistance to job losses, state ownership, Chapter 11 and its equivalents, and lessors who repossess and immediately re-place the aircraft. Capacity does not leave the market.
5. **Powerful suppliers on both sides** — a manufacturer duopoly, monopoly airports, monopoly ANSPs, a concentrated GDS oligopoly, and unionised labour with the ability to shut the operation down.
6. **Cyclicality with a long capacity lag** — orders placed at the peak deliver into the trough.
7. **Exogenous shocks** — 1991, 2001, 2003 SARS, 2008, 2010 ash, 2020 COVID, 2022 fuel and Russian airspace closure, 2025–26 regional conflict.

What has changed, and why margins improved after 2010: consolidation (the US went from nine major network carriers to four; Europe to three groups plus two large LCCs), capacity discipline as a stated management objective, ancillary and loyalty revenue that is structurally higher-margin than the fare, and — since 2020 — a supply-constrained aircraft market that has capped growth. IATA's projected 3.9% net margin and 6.8% ROIC for 2026 are historically strong for this industry and still unimpressive against almost any other capital-intensive sector.

## Sources

- [IATA — Airline Industry Financial Outlook, December 2025](https://www.iata.org/en/pressroom/2025-releases/2025-12-09-01/)
- [IATA — Global Outlook for Air Transport, June 2025](https://www.iata.org/en/pressroom/2025-releases/2025-06-02-01/)
- [IATA — Air Passenger Demand Falls 1.7% in June (30 July 2026)](https://www.iata.org/en/pressroom/2026-releases/07-30-air-passenger-demand-falls-june/)
- [Qatar Airways — FY2025/26 Group results (20 May 2026)](https://www.qatarairways.com/press-releases/en-WW/265838-qatar-airways-group-delivers-robust-financial-performance-despite-global-economic-instability/)
- [Wikipedia — AerCap](https://en.wikipedia.org/wiki/AerCap)
- [Wikipedia — Qatar Airways](https://en.wikipedia.org/wiki/Qatar_Airways)

## Open questions

- **Cost-share percentages** in section 1 are conventional industry ranges from the standard literature (Doganis, Belobaba), not from a single dated source. Any specific airline's split should be taken from its own annual report.
- **Lease rate factors and OEM discount ranges** are market convention, not published data; no lessor or OEM publishes transaction prices.
- **Air Lease Corporation / SMBC transaction** — reported as agreed in 2025; completion status not verified.
- **Leased share of world fleet (~50%)** requires a dated Cirium or IBA citation.
- **Loyalty programme valuations** cited from the 2020 financing round are widely reported but not verified here against the underlying filings.
- IATA's 2026 forecast predates the June 2026 demand contraction; a revised outlook from the June 2026 AGM in Rio de Janeiro was not located and should be sought.
