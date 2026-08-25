---
id: fusion.licensing
title: Fusion licensing, editions, extensions and pricing
domain: 15_software_autodesk_fusion
tags: [fusion, licensing, pricing, personal-use, subscription, extensions, education, startup, flex, tokens]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
applies_to: "Autodesk Fusion as sold on autodesk.com on 2026-08-25. Pricing is volatile — re-verify before quoting."
sources:
  - {title: "Fusion for personal use", url: "https://www.autodesk.com/products/fusion-360/personal", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Fusion pricing", url: "https://www.autodesk.com/products/fusion-360/pricing", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Fusion extensions", url: "https://www.autodesk.com/products/fusion-360/extensions", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Fusion Manufacturing Extension", url: "https://www.autodesk.com/products/fusion-360/manufacturing-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Nesting & Fabrication Extension", url: "https://www.autodesk.com/products/fusion-360/nesting-fabrication-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Fusion Simulation Extension", url: "https://www.autodesk.com/products/fusion-360/simulation-extension", publisher: "Autodesk", accessed: 2026-08-25}
  - {title: "Autodesk Education plan overview", url: "https://www.autodesk.com/education/edu-software/overview", publisher: "Autodesk", accessed: 2026-08-25}
related: [fusion.overview, fusion.alternatives]
---

# Fusion licensing, editions, extensions and pricing

**Summary.** Fusion is sold only as a subscription. There is one commercial base product at a headline **US$57 per month billed annually** (checked 2026-08-25), a free **Personal Use** licence for people earning under **US$1,000 a year** from their designs, a free one-year **Education** licence, and a set of paid **extensions** that were consolidated during 2024–26 so that Machining, Nesting & Fabrication and Additive now sit inside a single **Manufacturing Extension**. Autodesk's pricing pages are JavaScript-rendered and several figures below could not be scraped; every price in this file carries the date it was checked and must be re-verified before it goes into a quote.

> ⚠️ **Pricing changes without notice and varies by territory.** Autodesk lists prices in USD on autodesk.com; a Namibian or South African buyer will typically transact through a reseller in ZAR or USD with VAT and FX on top. Treat every number here as an anchor, not a quotation. **Re-verify before you commit.**

## Key facts

| Licence | Cost (checked 2026-08-25) | Term | Commercial use |
|---|---|---|---|
| Autodesk Fusion (commercial) | **US$57/month, billed annually** | 1 month / 1 year / 3 years | Yes |
| Fusion for Personal Use | **Free** | **3 years**, renewable | **No** — hobby only, < US$1,000/yr |
| Autodesk Education | **Free** | 1 year, renewable while eligible | **No** — educational purposes only |
| Fusion for Design (tier) | Not published on the page | — | Yes |
| Fusion for Manufacturing (tier) | Not published on the page | — | Yes |
| Manufacturing Extension | "per month, paid annually" — figure not rendered | Annual | Yes |
| Simulation Extension | Figure not rendered | Annual | Yes |
| Design Extension | Figure not rendered | Annual | Yes |
| Fusion Manage (PLM) | Figure not rendered | Annual | Yes |

## The commercial subscription

The base product is simply "Autodesk Fusion". One subscription is one named user, assigned through Autodesk Account, and may be used on multiple machines by that person (not simultaneously by different people). It includes:

- Design workspace in full: parametric solid, surface, mesh, sheet metal, plastic, form/T-Spline modelling, assemblies and joints.
- Drawing workspace with multi-sheet drawings and unrestricted export.
- Manufacture workspace with 2-, 2.5- and 3-axis milling, turning, and 2D cutting (waterjet/laser/plasma), plus 3+2 positional machining. Full 4/5-axis simultaneous strategies and the advanced automation are extension territory.
- Simulation: a subset of study types (see below and `08_simulation-and-analysis.md`).
- Render, Animation, Electronics.
- Full API and add-in access with no scripting restrictions.
- Data management on an Autodesk hub, with version history and named-user collaboration.

Billing terms are monthly, annual and three-year. Annual is materially cheaper per month than monthly; three-year locks a price against increases, which given Autodesk's recent history is worth real money.

**Autodesk Flex** — a token pool bought up front and consumed per day of use of a given product — exists across the Autodesk portfolio for occasional users. Fusion's inclusion and the per-day token cost for Fusion could not be confirmed on the rendered pricing page on 2026-08-25 and is `needs-verification`. Flex only makes sense if a product is used a handful of days per year; for a working joinery shop it does not.

## Fusion for Personal Use — the honest version

This is the licence most independent makers actually run on, so its limits deserve precision.

**What Autodesk states on the Personal Use page (quoted, accessed 2026-08-25):**

- "Limited to individuals generating less than $1,000 USD annually"
- "For personal, non-commercial projects only"
- "not for use in primary employment, company environments, or commercial training"
- Free for **3 years**, then re-apply
- "basic functionality for home-based projects"
- "Single user data management"
- "Limited CAM functionality"
- "Limited electronics and PCB designs"
- "Limited 2D documentation and drawings"
- "Limited import/export file types"
- "Forum support only"
- Users exceeding the revenue threshold must "convert to a subscription to Autodesk Fusion"

**What "limited" has historically meant in practice.** Autodesk's detailed restriction article could not be retrieved on 2026-08-25 (the URLs tried returned 404), so the specifics below are drawn from long-standing community knowledge and are marked `needs-verification` as a block. Do not put them in a contract without checking.

- A cap on the number of **active/editable documents** — other documents must be set read-only in the Data Panel before you can edit more. Widely reported as 10.
- **CAM restricted to 2- and 2.5-axis milling, turning and 2D cutting.** 3-axis and adaptive strategies are not available.
- **Rapid (G0) moves are posted as feed (G1) moves.** This is the restriction that bites hardest: a personal-use post produces safe but slow programs, and on a long nested sheet the added air time is real money.
- **No automated multi-sheet drawings**; drawing output is limited.
- **A reduced export list** — STEP/IGES/SAT and some others are typically unavailable; STL, 3MF, DXF and the Fusion archive generally are.
- **No simulation, no generative design.**
- **No custom (local) post-processor library in some periods** — check before relying on a machine-specific post.
- **Sheet metal and the API are available**, which is why the automation workflows in `09_api-and-automation.md` are still worth building on a personal licence.

> ⚠️ **The revenue test is about the work, not the file.** If you sell one wardrobe designed in Fusion for N$40,000, you are over the US$1,000 threshold and you need a commercial subscription. For a Namibian residential/joinery project that is billed to a client, Personal Use is not a lawful option. Budget for the commercial seat.

## Education licence

Autodesk's education plan gives "free, one-year, single-user access to Autodesk software" to eligible students, educators and qualified institutions; Fusion is explicitly included. Renewal opens 30 days before expiry and "access is renewable annually as long as you're eligible", i.e. annual re-verification (accessed 2026-08-25).

Education licences are for educational purposes only. Education-licensed CAD files also carry an educational flag that propagates into some outputs; do not use an education seat to produce commercial shop drawings.

**[NA]** Namibian institutions (NUST, UNAM, the VTCs) qualify in principle; eligibility verification is via SheerID-style document checks and can be awkward with non-standard institutional email domains. Allow time.

## Startup programme

Autodesk has run a startup programme for Fusion (historically "Fusion 360 for Startups", latterly folded into broader Autodesk startup/technology-impact programmes). The dedicated campaign URL returned 404 on 2026-08-25, so the current programme name, eligibility criteria (typical historic criteria: hardware product company, under a funding ceiling in the low millions USD, under three years old) and duration are **`needs-verification`**. If a startup route matters to you, contact an Autodesk reseller directly rather than relying on a stale web page.

## Extensions — the 2024–26 consolidation

This is the single most-misreported area of Fusion licensing, because the extension line-up changed materially.

**As listed on autodesk.com on 2026-08-25**, the current extensions are:

1. **Autodesk Fusion Manufacturing Extension.** Autodesk states it "has the same capabilities as the previous Fusion 360 Machining Extension" **plus** nesting & fabrication and additive manufacturing. It adds:
   - 3-, 4- and 5-axis milling and turning strategies, steep & shallow, deburr, automatic hole recognition, rotary strategies
   - toolpath modification without full recalculation
   - CAD-based probing strategies and spindle-mounted probe support
   - **associative and multi-sheet true-shape nesting**, which "convert[s] 3D assemblies into precise 2D nested solutions ready for CAM programming, and automatically update[s] nests if your original 3D design changes", grouping parts "based on thickness and other material-specific parameters giving instant insights for costing, quoting, and ordering"
   - metal additive with automatic orientation and associative supports

   **For a sheet-goods joinery shop this is the extension that matters**, and it matters for the nesting, not the 5-axis. See `05_sheet-goods-and-joinery-workflow.md`.

2. **Autodesk Fusion Simulation Extension.** Adds "advanced simulation study types and unlimited cloud-based solving for those studies". The page lists nonlinear static stress, structural buckling, event simulation, modal frequencies, injection moulding, electronics cooling, thermal (steady-state and thermal stress) and generative design as within the extension's scope (accessed 2026-08-25). Which studies remain in the base product is not stated on that page and is `needs-verification`; see `08_simulation-and-analysis.md`.

3. **Autodesk Fusion Design Extension.** "Advanced 3D design and modeling tools that simplify the product development process and enable an automated approach to creating complex product designs." Historically the Product Design Extension: volumetric lattices, automated modelling, advanced sheet-metal and plastic-part tooling.

4. **Autodesk Fusion Manage.** The PLM layer — "configurable PLM processes to manage new product introductions, requirements, change and release, bills of materials, suppliers, quality". Enterprise territory; not relevant to a two-person joinery practice.

The page metadata also still references **Nesting & Fabrication**, **Generative Design**, **Additive Build**, **Signal Integrity** and **Product Design** as names, but the Nesting & Fabrication page itself now redirects the reader to the Manufacturing Extension. **Treat "Machining Extension", "Nesting & Fabrication Extension" and "Additive Build Extension" as legacy names for what is now the Manufacturing Extension** when reading tutorials or forum posts written before 2025.

Autodesk also sells **higher tiers** — "Fusion for Design" and "Fusion for Manufacturing" — which bundle base Fusion with the corresponding extension(s) at a package price. Neither price rendered on the pricing page on 2026-08-25.

### Extension pricing

None of the extension prices rendered as text on autodesk.com on 2026-08-25 — the pages say things like "available for per month, paid annually" with the number injected by JavaScript. For historical scale, extensions have typically been priced in the **US$1,200–1,600 per year** band each, i.e. **substantially more than base Fusion itself**. That ratio is the important planning fact: adding the Manufacturing Extension roughly triples your annual Fusion cost.

> ⚠️ **Do the arithmetic before buying the Manufacturing Extension for nesting alone.** Base Fusion at US$57/mo ≈ US$684/yr. If the extension is ~US$1,500/yr, you are paying ~US$2,200/yr for a nesting engine. Dedicated nesting software, a cabinet-specific package such as Polyboard, or a well-written Python nesting script against the Fusion API (see `09_api-and-automation.md`) may all be cheaper. Extensions can be bought monthly, so a common pattern is to subscribe for the months in which you have production runs.

## Token- and credit-based usage

Historically Fusion consumed **cloud credits** for cloud rendering, cloud simulation solves and generative design outcomes. The 2024–26 restructuring moved "unlimited cloud-based solving" for advanced simulation into the Simulation Extension, which strongly implies credits are no longer the mechanism for simulation. Whether credits persist for rendering or generative design as of 2026-08-25 could not be confirmed from the rendered pages and is `needs-verification`.

Separately, **Autodesk Flex** tokens are the portfolio-wide pay-per-day mechanism. Confirm with a reseller whether Fusion is Flex-eligible and at what daily token rate before planning around it.

## What this means for a Namibian joinery practice

A defensible baseline, priced 2026-08-25:

| Line | Cost/yr (USD, indicative) | Note |
|---|---|---|
| 1 × Autodesk Fusion commercial, annual | ~684 | US$57/mo × 12 |
| Manufacturing Extension, only in production months | ~125/month when active | Verify price; subscribe monthly |
| Total, light use | ~700–1,100 | Plus reseller margin, VAT and FX |

Against that, note that **the base subscription already gives you 2.5D CAM with full rapid moves, unlimited drawings, all export formats and full API access** — which is the complete pipeline for a flat-pack joinery shop with a 3-axis router. The extension buys nesting automation and time, not capability you cannot otherwise reach.

**[NA]** There is no Autodesk direct-sales entity in Namibia; buy through a South African or international reseller. Expect ZAR invoicing, 15 % VAT **[ZA]**, and to be treated as an export customer. Confirm whether Namibian VAT/import treatment applies to a downloaded software subscription with your accountant before assuming the invoice is clean.

## Sources

- [Fusion for personal use](https://www.autodesk.com/products/fusion-360/personal) — Autodesk, accessed 2026-08-25
- [Autodesk Fusion pricing](https://www.autodesk.com/products/fusion-360/pricing) — Autodesk, accessed 2026-08-25
- [Fusion extensions](https://www.autodesk.com/products/fusion-360/extensions) — Autodesk, accessed 2026-08-25
- [Autodesk Fusion Manufacturing Extension](https://www.autodesk.com/products/fusion-360/manufacturing-extension) — Autodesk, accessed 2026-08-25
- [Nesting & Fabrication Extension](https://www.autodesk.com/products/fusion-360/nesting-fabrication-extension) — Autodesk, accessed 2026-08-25
- [Autodesk Fusion Simulation Extension](https://www.autodesk.com/products/fusion-360/simulation-extension) — Autodesk, accessed 2026-08-25
- [Autodesk Education plan overview](https://www.autodesk.com/education/edu-software/overview) — Autodesk, accessed 2026-08-25
- [Autodesk certification overview](https://www.autodesk.com/certification/overview) — Autodesk, accessed 2026-08-25

## Open questions

- **All extension prices.** Not rendered as text on any Autodesk page fetched on 2026-08-25. `needs-verification`.
- **Fusion for Design / Fusion for Manufacturing tier prices.** Same.
- **The detailed Personal Use restriction matrix.** Autodesk's article URLs returned 404; the document limit, CAM axis limit, rapid-as-feed behaviour and export list above are community knowledge, not quoted source. `needs-verification`.
- **Current startup programme** name, eligibility and duration.
- **Whether cloud credits still exist** for rendering or generative design, and Fusion's Flex token rate.

