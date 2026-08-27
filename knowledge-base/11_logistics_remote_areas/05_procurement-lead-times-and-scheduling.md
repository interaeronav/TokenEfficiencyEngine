---
id: logistics.procurement_lead_times
title: Procurement lead times and scheduling for remote projects
domain: 11_logistics_remote_areas
tags: [procurement, lead-times, expediting, stockout, holding-cost, programme, critical-path, long-lead-items, float, namibia, okongo]
jurisdiction: namibia
status: draft
confidence: medium
updated: 2026-08-25
sources:
  - {title: "The Trans-Cunene Corridor — transit times", url: "https://www.wbcg.com.na/the-trans-cunene-corridor/", publisher: "Walvis Bay Corridor Group", accessed: 2026-08-25}
  - {title: "Trans-Kalahari Corridor — transit times", url: "https://www.wbcg.com.na/trans-kalahari-corridor/", publisher: "Walvis Bay Corridor Group", accessed: 2026-08-25}
  - {title: "Port of Walvis Bay — vessel turnaround", url: "https://www.wbcg.com.na/port-of-walvis-bay/", publisher: "Walvis Bay Corridor Group", accessed: 2026-08-25}
  - {title: "Geography of Namibia — rainy seasons", url: "https://en.wikipedia.org/wiki/Geography_of_Namibia", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Logistics Cluster — logistics capacity assessments", url: "https://en.wikipedia.org/wiki/Logistics_Cluster", publisher: "Wikipedia", accessed: 2026-08-25}
related: [logistics.supply_chain_design, logistics.cost_modelling_remote, logistics.risk_contingency, materials.procurement_pricing]
unit_system: SI
---

# Procurement lead times and scheduling for remote projects

**Summary.** A remote project's programme is really a procurement programme with construction attached. The critical path usually runs through a handful of long-lead items — roof structure, joinery, switchgear, specified fittings — and through the delivery calendar, not through the trades. This file covers how to build a procurement schedule from real lead times, why quoted lead times are systematically optimistic, how to expedite effectively, how to compare the cost of a stockout against the cost of holding, and how to bolt procurement onto the construction programme so the two cannot drift apart.

> ⚠️ Lead-time figures in the tables below are **planning estimates** assembled from corridor transit times and general trade practice, not quoted supplier data. Confirm each one with the actual supplier before committing a programme. `needs-verification`

## Key facts

| Component of lead time | Typical duration to northern Namibia | Note |
|---|---|---|
| Enquiry → quotation | 3–10 working days | Longer for fabricated items |
| Quotation → order (internal approval) | 2–15 working days | Usually the least-managed segment |
| Order → deposit cleared / account opened | 1–10 working days | First order to a new supplier is the slow one |
| Manufacture / pick and pack | 0–40 working days | The number suppliers quote |
| Line haul Johannesburg → Windhoek (TKC) | **2 days** transit | Plus consolidation and border |
| Line haul Walvis Bay → Oshikango | **1 day** transit | 1 059 km published |
| Windhoek → Okongo | ~1–2 days | Derived; depends on consolidation |
| Sea freight Far East → Walvis Bay | 30–50 days | Plus port and clearance |
| Vessel turnaround at Walvis Bay | 12–15 h container, 18–20 h break-bulk | WBCG published |
| Customs clearance, SACU (nil duty) | 1–3 days typical | Documentation, not duty |
| Customs clearance, non-SACU import | 3–10 days | Longer if inspection or LOA required |

## 1. Quoted lead time versus actual lead time

A supplier's quoted lead time almost always means **"time from receipt of a clean order to goods available ex-works"**. Your programme needs **"time from the moment I identify a need to the moment the material is usable on site"**. The gap between the two is where remote projects lose weeks.

**The full chain, and who owns each link:**

| Segment | Owner | Typically ignored? |
|---|---|---|
| 1. Need identified → specification written | Design team | Yes — often weeks |
| 2. Specification → enquiry issued | Buyer | Yes |
| 3. Enquiry → quotations received | Suppliers | Partly |
| 4. Quotations → technical approval / sample approval | Design team | **Yes — the biggest hidden delay** |
| 5. Approval → purchase order issued | Client/contractor finance | Yes |
| 6. PO → order acknowledged and deposit paid | Both | Sometimes |
| 7. Acknowledgement → ex-works ready | Supplier | **No — this is the "quoted lead time"** |
| 8. Ex-works → consolidation point | Transport | Partly |
| 9. Consolidation → next scheduled wave departure | You | **Yes — can be up to a full wave interval** |
| 10. Line haul + border + last mile | Transport | Partly |
| 11. Delivery → inspection and acceptance | Site | Yes |
| 12. Acceptance → acclimatisation / preparation | Site | Yes, for timber and joinery |

**Worked example — specified external doors from a Windhoek joiner, for Okongo.**

| Segment | Days |
|---|---|
| Specification and schedule of openings | 5 |
| Enquiry to three joiners; quotes returned | 10 |
| Comparison, sample/finish approval | 10 |
| PO issued, 50 % deposit cleared | 7 |
| **Quoted manufacture lead time** | **25** |
| To consolidation yard | 2 |
| Wait for next wave (mean of a 6-week cycle) | 21 |
| Line haul + last mile | 2 |
| Inspection, acclimatisation before hanging | 7 |
| **Total need-to-usable** | **89 days ≈ 13 weeks** |

The joiner quoted **25 days**. The programme needs **89**. A project manager who plans on the quoted figure is 9 weeks short before anything has gone wrong.

**Rule: multiply quoted lead times by 3 for a first-cut remote programme, then decompose the ones on the critical path properly.**

## 2. Sources of lead-time variance

Variance matters more than length (see the safety-stock arithmetic in `01`). The main contributors, roughly in order:

1. **Internal approval loops.** Sample approval, colour approval, shop-drawing approval. These have no external cause and no natural deadline, so they expand. Fix them by putting a stated approval turnaround (e.g. 5 working days, deemed approved thereafter) into the contract.
2. **The supplier's own supply chain.** A Windhoek fabricator waiting on South African steel inherits the border and the corridor.
3. **Consolidation waiting time.** Self-inflicted but rational — it is the price of cheap freight. Manage it by publishing cut-off dates so suppliers aim at them.
4. **Border and customs.** Duty-free under SACU, but a documentation error still parks a truck.
5. **Weather.** February to April can add weeks to any delivery that has to leave the tar.
6. **Vehicle availability.** Northern Namibia is an empty-return lane; transporters prefer lanes with backloads. Peak agricultural or retail season squeezes capacity.
7. **Rejection and remake.** A rejected consignment resets steps 7–11 entirely. This is why inspection at dispatch matters so much.
8. **Payment.** An unpaid deposit or an exceeded credit limit stops production silently. Nobody phones to tell you.

## 3. Building the procurement schedule

Work backwards from the construction programme.

**Step 1 — identify the long-lead and critical items.** Typically 10–25 items on a small building. Candidates:

| Item | Why it is long lead |
|---|---|
| Roof trusses / structural timber or steel | Design, fabrication, possibly abnormal load |
| Joinery: doors, frames, cabinets | Made to order, finish approval |
| Windows and glazing | Made to opening sizes measured on site |
| Electrical distribution board and switchgear | Made to schedule; sometimes imported |
| Pumps, tanks, solar equipment | Imported; often long |
| Specified sanitaryware and taps | Imported; colour/model substitution risk |
| Floor and wall tiles | Batch/shade matching; must be ordered in one batch |
| Reinforcement cut and bend | Depends on approved bar schedules |
| Precast elements, lintels | Casting and curing time before transport |
| Ironmongery | Long tail of small items with one long pole |

**Step 2 — for each, work out the required-on-site (ROS) date** from the construction programme, then subtract the *full* need-to-usable duration from §1 to get the **latest order date**, then subtract the approval and enquiry segments to get the **latest specification date**.

**Step 3 — add float where the risk is highest**, not uniformly. Float belongs on items where lead-time variance is high and the consequence of lateness is a stopped programme. It does not belong on items that can be bought in Ondangwa in an afternoon.

**Step 4 — mark the seasonal gate.** Draw a vertical line on the programme at the start of February. Every heavy item must be delivered to the left of it.

**Step 5 — align with the delivery calendar.** Snap each ROS date to a wave date. Items whose latest order date has already passed are the project's opening problem — surface them at kick-off, not in month three.

**A procurement schedule row should carry:**

`Item | Spec ref | Supplier | Quantity | Spec-by date | Enquiry date | Approval date | Order-by date | Quoted lead | Ex-works date | Wave | ROS date | Float (days) | Status | Owner`

## 4. Expediting

Expediting is the active management of an order between placement and delivery. On a remote project it is not optional; a placed order is not a delivered order.

**A workable expediting routine:**

- **Acknowledge within 48 hours.** Insist on a written order acknowledgement stating the ex-works date. No acknowledgement means no order.
- **Three touch points per order:** at ~25 % of the lead time (materials secured?), at ~75 % (on schedule? photographs?), and at the ex-works date minus 5 days (ready? packed? documents?).
- **Ask for evidence, not assurances.** "Yes it's on track" costs the supplier nothing. A photograph of the item, a batch number, or a works order number costs them something and is checkable.
- **Escalate on a schedule, not on emotion.** Buyer → supplier's sales manager → supplier's director, at defined intervals.
- **Inspect before dispatch** for anything fabricated. A works inspection, even by photograph against a checklist, prevents a whole wasted freight cycle. For anything of significant value, inspect physically.
- **Confirm packing for the journey.** Specify it in the order: palletised, banded, corner-protected, weatherproofed, labelled with project and wave. A joiner who packs for a 20 km delivery has not packed for 700 km of corrugation.
- **Get the documents ahead of the vehicle.** Delivery note, packing list, certificates, warranties, guarantees, test certificates. Chasing a certificate after handover is a lost cause.

**When expediting fails: the intervention ladder.**
1. Change the wave (accept a later delivery, resequence work).
2. Split the order — take what is ready now by LTL, the rest on the next wave.
3. Change supplier for the balance.
4. Substitute a specification that is locally available.
5. Pay for premium freight (dedicated vehicle, or air to Ondangwa) — expensive but sometimes cheaper than the delay.
6. Resequence the construction programme around the gap.

Rank these by cost *including the cost of delay*, not by cost alone. Which brings us to §5.

## 5. The cost of a stockout versus the cost of holding

**Holding cost** per unit per year, `H`, is roughly:
`H = finance rate + storage cost + insurance + deterioration/obsolescence + shrinkage (theft/damage)`

On a remote Namibian site, plausible components: finance ~10–12 %, storage 1–3 %, insurance 1 %, deterioration 2–10 % (cement much higher than steel), shrinkage 2–5 %. **Total 16–30 % per year**, or roughly **1.3–2.5 % per month** of the value held.

**Stockout cost** is dominated by idle resources:

*Worked example — a cement stockout on a small village site.*

| Cost element | Rate (illustrative) | Days | Cost |
|---|---|---|---|
| Site gang, 12 people, idle | N$350/person/day | 5 | N$21 000 |
| Site supervision (2) | N$1 200/person/day | 5 | N$12 000 |
| Plant standing (mixer, compactor, generator) | N$1 800/day | 5 | N$9 000 |
| Accommodation and subsistence, 14 people | N$220/person/day | 5 | N$15 400 |
| Preliminaries and site establishment (time-related) | N$2 500/day | 5 | N$12 500 |
| Emergency top-up freight (part load, premium) | — | — | N$14 000 |
| **Total for a 5-day stockout** | | | **N$83 900** |

Now compare against holding the buffer that would have prevented it. From `01`, the 95 %-service safety stock was ~400 bags ≈ 20 t. At an illustrative N$110 per bag delivered, that is **N$44 000** of stock. Holding it for six months at 2 %/month costs about **N$5 280**, plus deterioration risk.

**N$5 280 of holding cost against N$83 900 of exposure.** Even at a 20 % annual probability of the stockout occurring, expected loss without the buffer is ~N$16 800 — still three times the holding cost. The buffer is obviously correct.

**The general rule.** Hold buffer stock when:
`(probability of stockout without buffer) × (cost of stockout) > (holding cost of buffer)`

and check the answer against shelf life and theft exposure. For remote sites this inequality is satisfied for almost every bulk, non-perishable, work-stopping material, and fails for perishables, high-value theft targets, and anything that might be varied by the design team.

**The corollary that people forget:** the same arithmetic says **do not** buffer things that will not stop work. A remote site drowning in speculative stock has converted a logistics problem into a cash-flow problem.

## 6. Integrating procurement with the construction programme

Keep procurement and construction in **one** programme, not two documents that are reconciled monthly.

**Mechanisms that work:**

1. **Procurement activities are programme activities.** "Order roof trusses", "Approve joinery sample", "Wave 3 delivery" appear as bars with logic links, not as a separate schedule.
2. **The delivery wave is a milestone with predecessors.** Every order feeding a wave links to it. When one slips, the wave shows it, and you see immediately whether it slips the works or just consumes float.
3. **Site work is linked to acceptance, not delivery.** The predecessor for "fix roof sheeting" is "sheeting inspected and accepted on site", so a damaged delivery shows as a programme event.
4. **A weekly one-page logistics report** to the same distribution as the programme: waves due, orders at risk, stock cover in days for the critical materials, access status, and anything needing a decision this week.
5. **Stock cover in days** as the headline metric, not stock value. "Cement: 11 days cover. Next wave: day 9." tells everyone what they need to know instantly.
6. **A single owner.** One named person owns the delivery calendar and can refuse an off-calendar trip. Without that authority the calendar decays within a month.
7. **Freeze the design before the wave cut-off.** Every late design change either misses a wave or triggers a premium trip. Make that cost visible to the person requesting the change — attach the freight cost to the variation.

**Anti-patterns to watch for:**
- A procurement schedule maintained in a spreadsheet that nobody links to the programme.
- "Order date" recorded as the date the requisition was raised rather than the date the supplier acknowledged.
- Float shown against every item equally, which means it is shown against none meaningfully.
- Delivery dates agreed with suppliers that do not match wave dates, so material sits at the consolidation yard.
- No record of which orders are unacknowledged — the single best early-warning indicator there is.

## Open questions

- Real quoted lead times from named northern Namibian and Windhoek suppliers for the long-lead categories above. `needs-verification`
- Typical customs clearance durations at Namibian entry points for SACU and non-SACU consignments. `needs-verification`
- Current commercial finance rates in Namibia for working-capital purposes (the 10–12 % used above is an assumption). `needs-verification`

## Sources

- [The Trans-Cunene Corridor](https://www.wbcg.com.na/the-trans-cunene-corridor/) — Walvis Bay Corridor Group, accessed 2026-08-25
- [Trans-Kalahari Corridor](https://www.wbcg.com.na/trans-kalahari-corridor/) — Walvis Bay Corridor Group, accessed 2026-08-25
- [Port of Walvis Bay](https://www.wbcg.com.na/port-of-walvis-bay/) — Walvis Bay Corridor Group, accessed 2026-08-25
- [Geography of Namibia](https://en.wikipedia.org/wiki/Geography_of_Namibia) — Wikipedia, accessed 2026-08-25
- [Logistics Cluster](https://en.wikipedia.org/wiki/Logistics_Cluster) — Wikipedia, accessed 2026-08-25
