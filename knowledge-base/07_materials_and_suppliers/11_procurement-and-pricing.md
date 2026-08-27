---
id: materials.procurement_pricing
title: Procurement, pricing and quote comparison
domain: 07_materials_and_suppliers
tags: [procurement, specification, rfq, quote-comparison, trade-accounts, vat, sacu, import-duty, delivery-terms, lead-times, incoterms, namibia, south-africa]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "Namibia, Republic of — Corporate — Other taxes", url: "https://taxsummaries.pwc.com/republic-of-namibia/corporate/other-taxes", publisher: "PwC Worldwide Tax Summaries", accessed: 2026-08-25}
  - {title: "South African Cement Grid — NRCS Letter of Authority verification", url: "https://www.concretesocietysa.org.za/wp-content/uploads/leaflets/Cement-grid-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Steel Force Namibia — price list and credit application", url: "https://www.steelforcenam.com/", publisher: "Steel Force cc", accessed: 2026-08-25}
  - {title: "Pupkewitz Megabuild — account types", url: "https://www.megabuild.com.na/main/branches/", publisher: "Pupkewitz Megabuild", accessed: 2026-08-25}
  - {title: "Chamberlain — delivery threshold", url: "https://www.chamberlains.co.za/", publisher: "Chamberlains", accessed: 2026-08-25}
related: [materials.suppliers.namibia, materials.suppliers.south_africa, materials.selection_principles]
unit_system: SI
---

# Procurement, pricing and quote comparison

**Summary.** Good material procurement is mostly specification discipline: if the specification is unambiguous, quotes become comparable, substitutions become visible, and price negotiation becomes possible. This file covers how to write a specification a merchant can price, how to run a request for quotation, how to compare quotes like-for-like, how trade accounts and discounts work in southern Africa, the VAT and SACU position for NA↔ZA movement, delivery terms, lead times by material category, and a reusable quote-comparison template.

## Key facts

| Item | Namibia | South Africa |
|---|---|---|
| Standard VAT rate | **15 %** | **15 %** |
| Customs duty on NA↔ZA movement | **Nil** (SACU) | **Nil** (SACU) |
| Import VAT basis | Greater of **FOB + 10 %** or market value | — |
| Import VAT deferment | To the **20th** of the month following importation, via a NamRA import VAT account | — |
| Compulsory VAT registration threshold | **N$1 000 000** taxable supplies in any 12 months | R1 000 000 (unverified in this pass) |
| Voluntary VAT registration threshold | **N$200 000** | — |
| VAT return due | Within **25 days** following the month | — |
| Late VAT penalty | **10 % per month or part month**, plus interest at prime | — |

## 1. Specification writing

A specification exists to make three things true at once: the right thing gets built, competing quotes are comparable, and a substitution is detectable.

### The four-part clause

Write every material clause as:

1. **Performance requirement** — the property that actually matters, with a number and a standard. *"Cementitious tile adhesive, classification C2S1 minimum."*
2. **Reference product** — a named product from a named manufacturer that meets it, so the merchant can price something. *"TAL Goldstar 6 gauged with TAL Keycoat as total water replacement."*
3. **Equivalence clause** — *"or approved equivalent, equivalence to be demonstrated against the performance requirement above by submission of the manufacturer's current technical data sheet."*
4. **Application requirement** where the performance depends on it. *"Gauging liquid as specified; substitution of water invalidates the classification."*

A clause with only (1) cannot be priced. A clause with only (2) cannot be substituted safely and invites a "we'll use something similar". A clause with (1) and (2) but not (3) forces a single source.

### Things a specification must always state

| For | State |
|---|---|
| Cement | Type notation (e.g. CEM II/B-V), strength class (42,5N), and that a valid NRCS Letter of Authority must be shown |
| Concrete | Characteristic strength, aggregate nominal size, slump, exposure class, and whether ready-mix or site-batched is permitted |
| Masonry units | Standard (SANS 227 / SANS 1215), class or nominal compressive strength, work size, and exposure zone |
| Reinforcement | Grade (Y / R), diameter, standard (SANS 920), bending schedule standard (SANS 282), and whether cut-and-bend is required |
| Structural steel | Grade (S355JR to SANS 50025 / EN 10025), section designation, and protective treatment (galvanising to SANS 121) |
| Sheet steel | **BMT** (not TCT), coating class (Z275 / AZ150 / AZ200), paint system, colour, profile name and manufacturer |
| Timber | Species, stress grade (S5/S7/S10), standard (SANS 1783-2), **H class**, and cross-section |
| Insulation | R-value (and whether product or system R), thickness, density, and reaction-to-fire classification |
| Sealants | ISO 11600 type and class (e.g. F 25 LM), chemistry, and joint dimensions |
| Paint | The full system: preparation, primer, number of coats, dry film thickness, manufacturer |

### Things that always cause disputes if left out

- Whether the price includes **delivery to site** and **offloading**.
- Whether the price includes **VAT**.
- **Wastage allowance** — whose risk it is.
- **Who supplies fixings and accessories** (ridges, flashings, closures, clips, fasteners are a substantial fraction of a roof price and are frequently omitted from a "roof sheeting" quote).
- **Cutting to length** and who takes the offcuts.
- **Packaging and protection** for the journey and for site storage.
- **Guarantee and warranty**, and whether it depends on installation by an approved installer.

## 2. Running a request for quotation

1. **Assemble a bill of quantities** with an item number, description (the four-part clause, abbreviated), unit, and quantity for every item.
2. **Send an identical document to every bidder**, with a stated closing date and a stated basis of comparison.
3. **State the required commercial terms up front**: currency, VAT treatment, delivery point (Incoterm or plain-language equivalent), payment terms, validity period, and the required lead time.
4. **Require the bidder to state exceptions explicitly.** "Alternative offered" must be a labelled column, not a footnote.
5. **Require a lead time per line item**, not one overall figure. A single long-lead item can hold up a load.
6. **Ask for the manufacturer's data sheet** for every alternative offered.
7. **Set a validity period** — 30 days is typical in a stable market, shorter for steel and cement, which reprice frequently.
8. **Get at least three quotes** for anything material. Two is a comparison; three is a market.

> ⚠️ Do not send a quantity-only enquiry ("100 sheets of IBR"). You will get three prices for three different products and no way to compare them.

## 3. Comparing quotes like-for-like

Comparing quotes means normalising them onto one basis before you look at the totals. The normalisation steps, in order:

1. **Strip VAT** from everything and compare ex-VAT. Some merchants quote inclusive, some exclusive; mixing them produces a 15 % error.
2. **Normalise the delivery point.** Add freight to site to any quote that is ex-works. Add offloading if it is not included. Add the last-leg cost from Windhoek or Oshakati where relevant.
3. **Normalise the quantity and unit.** Convert everything to a common unit — per m², per tonne, per m³, per unit. Watch for m² of *cover* versus m² of *sheet* on roofing, and for linear metre versus per-length pricing on timber and steel.
4. **Normalise the specification.** Where an alternative is offered, either accept it (and note the specification change) or price the compliant product from that bidder. Do not compare a 0,47 mm BMT sheet against a 0,53 mm one on price per m².
5. **Add the omissions.** Accessories, fixings, cutting, wastage.
6. **Add wastage** at a rate appropriate to the material and the geometry — typically 5 % for sheet goods on simple rectangles, 10 % on complex roofs, 10–20 % for mortar and plaster.
7. **Cost the lead time.** A quote that is 4 % cheaper but 5 weeks later may cost more than the saving in preliminaries and standing time.
8. **Cost the payment terms.** 30 days on account versus cash on collection is real working capital.
9. **Weight the non-price factors** — technical support, whether the branch will actually deliver to your site, whether they can supply a replacement in a hurry, and whether they will stand behind a warranty.

Only then compare totals.

## 4. Trade accounts and discount structures

### Account types

Namibian and South African merchants typically offer:

| Type | Terms |
|---|---|
| **Cash account** | Payment on collection or delivery; sometimes a small settlement discount |
| **30-day account** | The standard trade credit — invoice by month end, payment by the 30th of the following month. Requires a credit application, trade references, and often a personal surety from directors |
| **Professional / trade card** | A registered-professional or trade card giving a standing discount at point of sale without a full credit facility |
| **Project account** | Negotiated for a specific project with agreed rates for the duration |

Pupkewitz Megabuild publishes a 30-day account, a cash account, a Professional Card and a gift card. Steel Force Namibia publishes a credit application form and notes "strict policies when opening accounts". Chamberlains publishes free delivery on orders over R1 000.

### How discount actually works in this market

- **List price is a starting point**, particularly for cement, steel and sheeting. Steel Force explicitly states that its published price list "serves as a guideline and prices are negotiable upon request".
- **Volume matters more than loyalty.** A single large order at one branch will get a better rate than the same volume trickled out.
- **The discount is usually per category, not overall.** You may get 20 % on sheeting and 5 % on hardware.
- **Ask for the project rate, in writing, with a validity period.** A verbal "we'll look after you" is not a rate.
- **Structural steel, rebar and cement reprice frequently** — steel and cement prices in southern Africa move with input costs and exchange rates. Fix the rate or accept the exposure explicitly.
- **Rebate on delivery** is negotiable: many merchants will absorb delivery on an order above a threshold.

### Open the account before you need it

Credit applications take days to weeks. On a remote project, a supplier who will not release goods because the account is not open is a programme risk. Open the account, and open it at the branch that will actually serve the site, not only at head office.

## 5. VAT, duty and SACU — the practical rules

### Within Namibia **[NA]**

- Standard VAT **15 %** on taxable supplies.
- Register if taxable supplies exceed **N$1 million** in any 12 months; voluntary registration possible above **N$200 000** with a fixed place of business and acceptable records.
- Input tax is deductible only against a valid **tax invoice**. Insist on tax invoices that meet the VAT Act criteria — NamRA audits focus on exactly this.
- VAT returns due within **25 days** after the month.
- Late payment attracts **10 % per month or part month** plus interest at prime. This penalty is severe enough to make VAT administration a project risk, not a bookkeeping detail.

### Within South Africa **[ZA]**

- Standard VAT **15 %**.

### Moving goods NA ↔ ZA

- **No customs duty** — both are SACU members and customs duties are not levied on intra-SACU trade.
- **Namibian import VAT at 15 %** on the greater of **FOB + 10 %** or market value.
- **Deferment** to the 20th of the following month via a registered NamRA import VAT account — a meaningful cash-flow benefit on a project importing regularly.
- **Input tax recovery on import VAT requires stamped customs entries.** Keep them. Without them the 15 % is a cost, not a recoverable.
- **Third-country goods** entering Namibia via South Africa pay the **SACU Common External Tariff**.
- **Temporary imports** (plant, scaffolding, formwork systems) require **surety** — provisional payment, bank or insurance guarantee — to cover import VAT and duty.
- **Excise** applies to fuel, alcohol and tobacco under duty-at-source procedures across SACU.
- **Environmental levies** apply in Namibia to certain imported or locally manufactured products including light bulbs, lubricants, tyres, disposable batteries and certain plastic bags.
- **AEO status** (Namibia Customs, under the Customs and Excise Act 1998) gives reduced security requirements, bonded warehouse and temporary import benefits, and faster clearing including pre-clearing on AsycudaWorld. Worth pursuing for a project importing continuously.

## 6. Delivery terms

For domestic supply, agree a plain-language term and write it into the order:

| Term | Meaning |
|---|---|
| **Ex works / collect** | You collect from the branch. You bear all transport, handling and risk |
| **Delivered to site, offloading excluded** | They put it at the gate; you provide the labour or plant to offload |
| **Delivered and offloaded** | They offload — specify whether by crane, hiab, or hand |
| **Delivered, offloaded and stacked** | Rare, but worth asking for on sheeting and board |

For cross-border, use Incoterms 2020 explicitly:

| Incoterm | Who does what |
|---|---|
| **EXW** | Buyer does everything from the seller's door — including export clearance. Rarely sensible cross-border |
| **FCA** | Seller delivers to a named place and handles export clearance; buyer takes it from there |
| **CPT / CIP** | Seller pays carriage (and, for CIP, insurance) to a named destination; risk transfers earlier, at first carrier |
| **DAP** | Seller delivers to the named place, ready for unloading; **buyer handles import clearance and import VAT** |
| **DDP** | Seller delivers cleared for import, duties and taxes paid. Convenient, but you may lose the ability to recover Namibian import VAT because you are not the importer of record |

**For a Namibian project, DAP to a named Namibian address with you as importer of record is usually the right default** — you keep the stamped customs entry and the input-tax recovery, and you control the clearing agent.

Always specify: delivery address (with GPS coordinates for a rural site), the access constraints (road condition, turning circle, whether a 22 m interlink can reach the site), the offloading arrangement, and the acceptable delivery window.

## 7. Lead times by material category

Indicative planning figures for a site in northern Namibia. **These are planning assumptions, not verified supplier commitments** — no Namibian merchant published lead times, and every one must be confirmed per branch.

| Category | Local (northern branch) | Regional (Windhoek/Oshakati) | Cross-border (ZA) |
|---|---|---|---|
| Cement, sand, stone, blocks | Same day – 3 days | 3–7 days | Not economic |
| General hardware, fixings, consumables | Same day – 3 days | 3–7 days | 3–5 weeks |
| Standard timber | 2–7 days | 1–2 weeks | 3–5 weeks |
| Treated timber, specific H class | 1–2 weeks | 2–3 weeks | 4–6 weeks |
| Roof sheeting, standard profiles and stock lengths | 3–10 days | 1–2 weeks | 3–5 weeks |
| Roof sheeting, cut to length / special colour | — | 2–4 weeks | 4–8 weeks |
| Roof trusses (designed and fabricated) | — | 3–6 weeks | 5–8 weeks |
| Reinforcement, straight bar and mesh | 3–7 days | 1–2 weeks | 3–5 weeks |
| Reinforcement, cut and bend to schedule | 1–2 weeks (Ondangwa) | 2–3 weeks | 4–6 weeks |
| Structural steel, stock sections | — | 1–3 weeks | 3–5 weeks |
| Structural steel, fabricated and galvanised | — | 4–8 weeks | 6–10 weeks |
| Steel windows and door frames | 2–4 weeks (Wispeco Ondangwa) | 3–5 weeks | 5–8 weeks |
| Aluminium windows and doors, made to order | — | 4–8 weeks | 6–10 weeks |
| Glass and IGUs | — | 3–6 weeks | 5–10 weeks |
| Board products, standard decors | 1–2 weeks | 1–2 weeks | 4–6 weeks |
| Board products, special decors | — | 3–5 weeks | 6–10 weeks |
| Paint, standard and tinted | Same day – 1 week | 1 week | 4–6 weeks |
| Paint, two-pack and specialist systems | — | 2–4 weeks | 5–8 weeks |
| Tiles and sanitaryware | — | 2–5 weeks | 5–10 weeks |
| Joinery and architectural hardware | — | 2–4 weeks (if stocked) | **6–12 weeks** |
| Technical membranes, specialist chemicals | — | 2–4 weeks | 5–8 weeks |
| Anything imported from outside SACU | — | — | **10–20 weeks** |

**Programme rule:** identify every item with a lead time longer than the time between now and its required-on-site date, and order those first. This list is almost always: joinery hardware, glazing, made-to-order aluminium, roof trusses, and any imported fitting.

## 8. Reusable quote-comparison template

Use one row per bill item, one block of columns per supplier. Compare only after normalisation.

### Header block

| Field | Entry |
|---|---|
| Project | |
| Package | e.g. "Roof covering and rainwater goods" |
| RFQ issued | date |
| Closing date | date |
| Comparison basis | Ex-VAT, delivered to site, offloaded |
| Currency | N$ |
| Prepared by / date | |

### Line comparison

| # | Description (spec clause) | Unit | Qty | **Supplier A** rate | A: alt offered? | A: line total | **Supplier B** rate | B: alt offered? | B: line total | **Supplier C** rate | C: alt offered? | C: line total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0,53 mm BMT AZ150 Colorplus IBR sheeting, colour X, cut to length | m² | | | | | | | | | | |
| 2 | Ridge, barge and side flashings, matching material | m | | | | | | | | | | |
| 3 | Fixtite Class 3 fasteners, #12 × 65 hex head | no. | | | | | | | | | | |
| … | | | | | | | | | | | | |

### Normalisation block (below the line items)

| Adjustment | Supplier A | Supplier B | Supplier C |
|---|---|---|---|
| Sub-total, as quoted | | | |
| Less VAT if quoted inclusive | | | |
| **Sub-total ex-VAT** | | | |
| Add: freight to site (if ex-works) | | | |
| Add: last-leg freight (Windhoek/Oshakati → site) | | | |
| Add: offloading | | | |
| Add: items omitted from quote (list) | | | |
| Add: wastage allowance @ __ % | | | |
| Add: cost of specification shortfall (to bring alternative up to spec) | | | |
| **Normalised total, ex-VAT, delivered and offloaded** | | | |
| VAT @ 15 % | | | |
| **Normalised total, incl. VAT** | | | |

### Non-price comparison

| Factor | Supplier A | Supplier B | Supplier C |
|---|---|---|---|
| Longest line-item lead time (weeks) | | | |
| Delivers to site? (confirmed, not implied) | | | |
| Payment terms | | | |
| Quote validity | | | |
| Compliance: fully / with alternatives / non-compliant | | | |
| Manufacturer data sheets supplied? | | | |
| Warranty and any installer conditions | | | |
| Technical support available | | | |
| Ability to resupply quickly if damaged | | | |
| **Recommendation and reason** | | | |

### Award record

| Field | Entry |
|---|---|
| Supplier selected | |
| Normalised price | |
| Reason (if not lowest) | |
| Specification variations accepted | |
| Agreed lead time and delivery date | |
| Agreed delivery terms | |
| Approved by / date | |

## 9. Practical anti-patterns

| Anti-pattern | Why it costs money |
|---|---|
| Quoting quantities without specification | Three incomparable prices |
| Comparing inclusive and exclusive prices | A silent 15 % error |
| Accepting "or similar" without a data sheet | Uncontrolled substitution discovered on site |
| Ordering roof sheeting without accessories | A 15–25 % under-estimate and a second delivery |
| Leaving a long-lead item unordered because its detail is not finalised | The programme is already late; order the long-lead item on an approved outline and finalise details later |
| Buying bulk material cross-border to save 8 % | Freight and clearance eat the saving and add weeks |
| Not opening the trade account until the first delivery | Goods held at the counter |
| Not keeping stamped customs entries | Import VAT becomes an unrecoverable cost |
| Accepting cement without checking the NRCS LoA | Non-compliant, possibly counterfeit, cement in the structure |
| One consolidated site delivery of everything | Materials degrading on site for months; theft; double handling |
| Five reactive deliveries instead of one planned load | Freight cost exceeds any discount you negotiated |

## Sources

- [Namibia — Corporate — Other taxes](https://taxsummaries.pwc.com/republic-of-namibia/corporate/other-taxes) — PwC: VAT rate and thresholds, import VAT basis and deferment, SACU duty position, return deadlines, penalties, temporary import surety, AEO scheme, environmental levies
- [South African Cement Grid](https://www.concretesocietysa.org.za/wp-content/uploads/leaflets/Cement-grid-2024.pdf) — Cement & Concrete SA: NRCS Letter of Authority verification requirement and NRCS contact details
- [Steel Force Namibia](https://www.steelforcenam.com/) — published price list dated 08.01.2024, "guideline, prices negotiable", credit application policy
- [Pupkewitz Megabuild](https://www.megabuild.com.na/main/branches/) — 30-day account, cash account, Professional Card, gift card
- [Chamberlain](https://www.chamberlains.co.za/) — free delivery threshold R1 000
- [Cashbuild Oshakati](https://locations.cashbuild.co.za/Retail-Oshakati-CashbuildOshakati) — free local delivery, online and in-store quotes

## Open questions

- **The lead-time table is a planning estimate, not sourced data.** No Namibian or South African supplier consulted in this research published lead times. Every figure must be replaced with a supplier commitment before it is used to build a programme.
- **No current prices are quoted anywhere in this domain.** The only dated price reference found was Steel Force Namibia's price list dated 08.01.2024, which is described by the supplier as a negotiable guideline and was not retrieved.
- **The South African compulsory VAT registration threshold (R1 million) is stated from general knowledge and was not verified** against SARS in this pass.
- **Discount structures and typical trade discount percentages are not published by any merchant** and are described qualitatively only.
- **Delivery radius, delivery charge and minimum order value for the northern Namibian branches are unknown** and are the single most important commercial fact a project in Ohangwena Region needs to establish.
- Whether Namibian merchants will hold a project rate against steel and cement price movement, and for how long, is unverified.
