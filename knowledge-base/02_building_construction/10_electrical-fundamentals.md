---
id: building.electrical
title: Electrical fundamentals for builders
domain: 02_building_construction
tags: [electrical, distribution-board, circuits, cable-sizing, earthing, bonding, conduit, chasing, coc, sans-10142, solar-pv, battery, generator, off-grid]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SANS 10142-1 The wiring of premises — Part 1: Low-voltage installations (full text, Ed 1.5/Amdt 5)", url: "https://offgriddiy.co.za/upload/SANS10142-1_06-05-12.pdf", publisher: "SABS", accessed: 2026-08-25}
  - {title: "Electrical Installation Regulations, 2009 (consolidated)", url: "https://www.saflii.org/za/legis/consol_reg/eir342/", publisher: "SAFLII / Department of Employment and Labour", accessed: 2026-08-25}
  - {title: "SANS 10142-1:2012 Edition 1.8 (front matter and table of changes)", url: "https://ndlambe.gov.za/wp-content/uploads/2023/07/SANS-10142-Electrical-installation.pdf", publisher: "SABS", accessed: 2026-08-25}
related: [building.plumbing, building.finishes, building.programme, building.health_safety]
---

# Electrical fundamentals for builders

**Summary.** A builder must never do electrical work — but must know enough to coordinate it, to build the fabric that receives it, and to refuse work that will not pass. In South Africa the wiring code is **SANS 10142-1** and the law is the **Electrical Installation Regulations, 2009** under the OHS Act: only a *registered person* may issue a **Certificate of Compliance**, and a CoC older than **two years** blocks a change of ownership. The numbers a builder needs are the ones that shape the building: chase and conduit routes fixed before plastering, earth leakage at **30 mA**, maximum **5 % voltage drop**, earth continuity resistance limits, and the bathroom zones that decide where a socket may not go. Off-grid, the builder is usually also the person sizing the PV array, battery and generator.

## Key facts

| Item | Value | Source |
|---|---|---|
| Wiring code **[ZA]** | **SANS 10142-1**, The wiring of premises — Part 1: Low-voltage installations | SANS |
| Standard supply | 230 V single phase / 400 V three phase, 50 Hz | SANS 10142-1 |
| Maximum voltage drop, a.c. | **5 %** of standard/declared voltage — **11,5 V** single phase; **20 V** three phase | SANS 10142-1 6.2.7.1.1 |
| Maximum voltage drop, d.c. | 5 % of circuit nominal voltage | SANS 10142-1 6.2.7.1.2 |
| Earth leakage tripping current | **≤ 30 mA** rated residual current; must not be possible to desensitise in service | SANS 10142-1 6.7.5.4 |
| Earth leakage required | On circuits supplying SANS 164-1/164-2 socket-outlets in a new installation; and on socket circuits in an existing installation when rewired or extended | SANS 10142-1 6.7.5.1 |
| Earth leakage must disconnect | Both phase and neutral (single phase); all three phases (three phase) | SANS 10142-1 6.7.5.3 |
| Max earth continuity resistance, 16 A protective device | **0,70 Ω** | SANS 10142-1 Table 8.1 |
| Max earth continuity resistance, 20 A | 0,55 Ω | Table 8.1 |
| Max earth continuity resistance, 32 A | 0,41 Ω | Table 8.1 |
| Max earth continuity resistance, 63 A | 0,24 Ω | Table 8.1 |
| Metallic roofs, gutters, downpipes and waste pipes | earth continuity path **≤ 0,2 Ω** | Table 8.1 NOTE |
| Cables buried in the ground | depth **0,5 m**; below 0,5 m they must be in conduit or otherwise protected; backfill must not contain sharp objects | SANS 10142-1 |
| Bathroom IP ratings | zone 0 IPX7; zone 1 IPX5; zone 2 IPX4; zone 3 IP21 | SANS 10142-1 7.1.4.1 |
| Bathroom fixed equipment | zone 0 none; zone 1 water heaters only; zone 2 water heaters and class II luminaires only | SANS 10142-1 7.1.4.4.1 |
| Junction boxes in bathroom zones 0, 1, 2 | **Not permitted** | SANS 10142-1 7.1.4.2.2 |
| Switches/socket-outlets from a prefab shower cabinet door | **≥ 0,60 m** | SANS 10142-1 7.1.4.3.4 |
| Distribution board in a room with a bath or shower | outside zone 3, enclosure **IPX5** | SANS 10142-1 7.1.4.3.6 |
| **[ZA]** CoC issuer | Only a **registered person** (electrical tester single phase, installation electrician, or master installation electrician) | Electrical Installation Regs 2009 reg 9 |
| **[ZA]** CoC and change of ownership | May not allow a change of ownership if the CoC is **older than two years** | EIR 2009 reg 7(5) |
| **[ZA]** CoC accompaniment | Must be accompanied by a **test report** in the format approved by the chief inspector | EIR 2009 |
| **[ZA]** Penalty | Fine or imprisonment up to **12 months**, plus additional daily fines for continuing offences | EIR 2009 |

## 1. The supply and the distribution board

**Point of supply → main switch → distribution board (DB) → circuits.**

A domestic DB contains:
- **Main switch-disconnector** — isolates the whole installation. Its position must be indicated.
- **Earth leakage protection unit** — an earth leakage circuit-breaker (ELCB/RCD) with a rated residual current **not exceeding 30 mA**, protecting all socket-outlet circuits. It must break both phase and neutral.
- **Circuit-breakers** — one per circuit, sized to the cable and the load.
- **Earth bar and neutral bar** — the earth bar is the **main earthing terminal**, to which the consumer's earth electrode/earth continuity conductor and all bonding conductors connect.
- **Circuit chart and warning labels**, including the warning label required where a series-connected (cascaded) breaker system is used.

Builder's responsibilities around the DB:
- Provide a recess or surface position that is accessible, not in a bathroom zone, not behind a door, not above a sink, at a workable height.
- Never build a DB into a position where it becomes inaccessible after finishing.
- Provide the conduit entries and a sleeve for the incoming supply before plastering.
- Where the DB is concealed, its position must be recorded (SANS 10142-1 5.2.8(f)).

## 2. Circuit types in a house

| Circuit | Typical breaker | Typical cable (copper, PVC insulated, in conduit) | Notes |
|---|---|---|---|
| Lighting | 10 A (sometimes 6 A) | 1,5 mm² | Two or more lighting circuits so a single trip does not black out the house |
| Socket outlets (radial) | 20 A | 2,5 mm² | Earth leakage protected |
| Socket outlets (ring) | 30 A | 2,5 mm² | Ring circuits must be identified (SANS 10142-1 6.6.1.13) |
| Geyser | 20 A | 2,5 mm² (short run) or 4 mm² | Dedicated circuit; isolator within reach |
| Stove / hob | 30–40 A | 4–6 mm² | Dedicated circuit and stove isolator |
| Air conditioner | per manufacturer | 2,5–4 mm² | Dedicated circuit |
| Borehole / pressure pump | per motor | 2,5–4 mm² | Motor protection required |
| Outbuilding submain | per load | 4–16 mm² SWA | Buried at 0,5 m, own DB and earth arrangement |

> ⚠️ These cable/breaker pairings are common South African domestic practice, **not** a SANS table. SANS 10142-1 requires cable selection from the current-carrying-capacity tables (6.2 to 6.9) with correction factors for grouping, ambient temperature, installation method and harmonics, and then a **voltage drop check**. At Okongo, high ambient temperatures push the correction factors the wrong way — a cable that is fine in Windhoek may need to go up a size in a hot ceiling void. Flagged `needs-verification`.

**Voltage drop.** The 5 % rule bites on long runs — a common problem on rural plots where the DB is at the house and the borehole is 200 m away. Rule of thumb: check the drop, and if it exceeds the limit, increase the cable size rather than accept it. SANS 10142-1 tables give voltage drop per ampere per metre for each cable size.

**Harmonics.** Where significant third-harmonic content is present (LED drivers, inverters, VSDs), a correction factor applies and the neutral may become the sizing conductor. The standard's worked example: a 39 A design load in a 6 mm² cable becomes a 10 mm² cable at 20 % third harmonic and a 16 mm² cable at 50 %.

## 3. Earthing and bonding

- The **main earthing terminal** is the earth bar in the DB. Everything protective connects there.
- The **earth continuity conductor** must be connected to every point of consumption and every switch, and its resistance measured back to the consumer's earth terminal must not exceed the Table 8.1 values (e.g. 0,70 Ω for a 16 A protective device, 0,41 Ω at 32 A).
- **All socket-outlets must be tested by inserting a plug** and including the resistance of the earth pin in the measurement.
- **Bonding.** Extraneous conductive parts must be bonded: metallic water and waste pipework, metallic roof sheeting, gutters and downpipes (path resistance ≤ 0,2 Ω), structural steelwork, and the common bonding network of any information-technology installation, which must be bonded to the main earthing terminal.
- **Supplementary equipotential bonding** in a bathroom: a local bonding conductor must connect all extraneous conductive parts in zones 1, 2 and 3 with the protective conductors of all exposed conductive parts in those zones. In practice: bond the metal bath, the metal pipework, the towel rail and the shower tray.

Builder's contribution: leave the bonding accessible. A bonded bath that is then tiled in with no access point cannot be inspected or repaired.

## 4. Bathroom zones — where things may not go

| Zone | Definition (simplified) | Minimum IP | Fixed equipment permitted |
|---|---|---|---|
| 0 | Inside the bath or shower basin | IPX7 | None; only SELV ≤ 12 V, source outside zone 0 |
| 1 | Above the bath/shower up to 2,25 m | IPX5 | Water heaters only |
| 2 | 0,6 m horizontally beyond zone 1 | IPX4 | Water heaters and class II luminaires only |
| 3 | 2,4 m beyond zone 2 | IP21 | Socket-outlets only if individually isolated by transformer, or SELV, or protected by 30 mA earth leakage |

**No junction boxes in zones 0, 1 and 2.** No switchgear or accessories in zones 0, 1 and 2 except emergency push buttons at SELV ≤ 12 V in zones 1 and 2. Insulated pull-cord switches are permitted in zones 1 and 2. Switches and socket-outlets must be at least **0,60 m** from the door opening of a prefabricated shower cabinet.

This is a builder's problem as much as an electrician's: the position of the shower decides which wall can carry a socket.

## 5. Conduit, chasing and coordination

There is no SANS 10142-1 clause that a builder can quote for chase geometry — the structural constraint comes from the masonry standards, and the wiring constraint is that cables must be protected. Practical rules that keep both trades and the building inspector satisfied:

1. **Conduit before plaster, always.** Once the wall is plastered the cost of a chase is the plaster plus the paint plus the argument.
2. **Run chases vertically or horizontally**, in line with the outlet, never diagonally. A diagonal chase cannot be predicted by anyone drilling later.
3. **Depth**: cut only as deep as the conduit needs. Do not cut through more than about one third of the thickness of a single-leaf wall, and never chase both faces of a 90/110 mm wall at the same height.
4. **Never chase a control joint, a lintel, or the leaf of a cavity wall below DPC.**
5. Use a chase cutter, not a hammer and chisel, on hollow blockwork — percussion cracks the webs.
6. Fill chases with mortar or plaster in two passes with a scrim/mesh over the conduit if the chase is wide, so the shrinkage crack does not telegraph.
7. **Conduit standards**: PVC rigid conduit to SANS 950; metal conduit 20–50 mm dia. to SANS 1065-1; conduit systems generally to SANS 61386.
8. Cables **buried in the ground** are laid at 0,5 m depth; where the depth is less than 0,5 m they must be in conduit or otherwise protected, and where 0,5 m or deeper the backfill must not contain sharp objects.
9. Coordinate with plumbing: never run a conduit in the same chase as a water pipe, and never within 1 m of a water tap or valve in the same room where SANS 10142-1 restricts equipment.
10. Draw wires only after the plaster is dry and the conduit has been rodded through — a conduit full of mortar droppings is a rewire.

## 6. Certificate of compliance

**[ZA]** Under the Electrical Installation Regulations, 2009:
- Only a **registered person** — an electrical tester for single phase, an installation electrician or a master installation electrician — may issue a Certificate of Compliance.
- A CoC must be accompanied by a **test report** in the format approved by the chief inspector.
- The user or lessor **may not allow a change of ownership if the CoC is older than two years**.
- Where an addition or alteration is made, the user or lessor must obtain a CoC **for at least the addition or alteration**. Where the existing installation predates October 1992 with no ownership change before March 1994, adding work can trigger a CoC for the whole installation.
- An **electrical contractor** must employ a registered person full time or be registered themselves, keep a fixed address and telephone, and register annually.
- Contravention carries a fine or imprisonment up to 12 months, plus daily fines for continuing offences.

**[NA]** Namibia regulates electricity supply under the Electricity Act 4 of 2007 with the **Electricity Control Board (ECB)** as regulator, and Namibian practice follows SANS 10142-1 in most private and commercial work. Confirm the current Namibian requirement for a certificate of compliance and the registration route for electricians with the ECB and the Ministry of Mines and Energy before relying on it — this is `needs-verification`.

> ⚠️ A builder who wires a house and asks an electrician to "just sign the CoC" is asking that person to commit an offence. The registered person must have done or supervised the work and must test it. Budget the electrician into the programme at first fix, not at handover.

## 7. Off-grid: solar PV, batteries and generators

At Okongo, grid supply may be present but unreliable, or absent. The sizing method below is standard practice; the specific product data must come from the equipment manufacturer.

### Step 1 — Load assessment

Build an honest daily energy table:

| Load | Power (W) | Hours/day | Wh/day |
|---|---|---|---|
| LED lighting (10 × 8 W) | 80 | 5 | 400 |
| Fridge/freezer (inverter type) | 90 average | 24 | 2 160 |
| TV + decoder | 120 | 5 | 600 |
| Laptop / phone charging | 100 | 4 | 400 |
| Water pressure pump | 750 | 1 | 750 |
| Washing machine | 500 | 0,7 | 350 |
| Microwave | 1 000 | 0,3 | 300 |
| **Daily total** | | | **≈ 4 960 Wh** |

Deliberately exclude resistive heating (geyser, kettle, stove, iron, heater) from PV — solve hot water with a **solar water heater** (see file 09) and cooking with **gas**. Electric water heating alone will double or triple the array.

### Step 2 — PV array

`Array kWp ≈ daily load (kWh) ÷ (peak sun hours × system efficiency)`

- Northern Namibia has a very high solar resource. Use a conservative design figure of about **5,0–5,5 peak sun hours/day** for a fixed north-facing array at latitude tilt in the worst month, and confirm against a solar resource dataset for the actual site.
- System efficiency (inverter, charge controller, cabling, temperature derating, soiling): **0,70–0,75**. Dust in Ohangwena makes soiling losses material — plan for cleaning access.
- Example: 5,0 kWh ÷ (5,25 × 0,72) ≈ **1,3 kWp**. Add margin for cloudy days and future load growth: specify **2,0–2,5 kWp**.

### Step 3 — Battery bank

`Usable battery kWh = daily load × days of autonomy ÷ depth of discharge`

- Days of autonomy: 1 day with a generator backup; 2 days without.
- Depth of discharge: **~50 %** for lead-acid (flooded or AGM), **~80–90 %** for LiFePO₄.
- Example, 5,0 kWh/day, 1 day autonomy, LiFePO₄ at 80 % DoD: **6,25 kWh** nominal. Same case with lead-acid at 50 %: **10 kWh** nominal.
- Heat is the enemy: battery life falls sharply above 25 °C. Put the battery in a shaded, ventilated, insulated space — **not** in a roof void, **not** on an unshaded west wall.

### Step 4 — Inverter

Size on **simultaneous peak demand**, not on daily energy. Add the largest motor's starting surge. A 750 W pressure pump can draw 3–5 × running current for a second on start. For the example house, a **3–5 kW** inverter with a surge rating of at least 2× continuous is typical. Verify the inverter is d.c.-coupled or a.c.-coupled to match the array and charge controller.

### Step 5 — Generator

Generator sizing for backup and for construction:
- **Continuous (prime) rating**, not the "maximum" sticker rating; derate by roughly **10 %** for the site altitude and ambient temperature at Okongo.
- Allow for motor starting: a 2,2 kW (3 hp) concrete mixer needs a generator of roughly 5–7 kVA on direct-on-line start.
- Common site sizes: **5 kVA** for hand tools and lights; **8–10 kVA** for a mixer plus tools; **15–20 kVA** where a vibrating poker, bar bender and welder run together.
- Wire generator supply through a **changeover switch** — never back-feed a socket. Earth the generator frame and provide earth leakage protection on the outlets.
- On a battery system, size the generator to charge the battery **and** carry the house at once, at 60–80 % of its rating for good fuel efficiency and engine health.

### d.c. side rules the builder must respect

- Voltage drop limit on the d.c. side is also **5 %** — and at 48 V that means very few millivolts to play with, so d.c. cable runs must be short and fat.
- All d.c. wiring, isolators, fuses and combiner boxes are part of the electrical installation and fall under SANS 10142-1 (and its PV-specific clauses); they are the electrician's work, not the roofer's.
- **PV mounting penetrations through a waterproofed roof void most waterproofing guarantees.** Coordinate PV mounting before the membrane or the sheeting goes down (see file 08).
- Provide a lockable, ventilated, shaded plant room or cupboard for inverter, charge controller and battery. Plan it at design stage; it is typically 1,5–2,5 m² and must not be a bathroom, a bedroom cupboard or a roof void.

## Sources

- [SANS 10142-1 The wiring of premises, Part 1: Low-voltage installations (full text)](https://offgriddiy.co.za/upload/SANS10142-1_06-05-12.pdf)
- [Electrical Installation Regulations, 2009 (consolidated) — CoC, registered persons, penalties](https://www.saflii.org/za/legis/consol_reg/eir342/)
- [SANS 10142-1:2012 Edition 1.8 — front matter and table of changes](https://ndlambe.gov.za/wp-content/uploads/2023/07/SANS-10142-Electrical-installation.pdf)

## Open questions

- Cable size / breaker pairings for domestic circuits are common practice, not a SANS table; SANS 10142-1 requires selection from tables 6.2–6.9 with correction factors. `needs-verification`.
- The full-text SANS 10142-1 available is an older edition (Ed 1.5, Amdt 5 / 2006 base) — clause numbering and some requirements have changed in the 2017 (Ed 2) and 2024 (Ed 3.2) editions. Verify clause numbers against the current edition.
- Chasing geometry rules are trade practice; no SANS clause was located that specifies maximum chase depth in masonry.
- **[NA]** Namibian certificate-of-compliance requirements, the registration route for electricians, and whether SANS 10142-1 is legally incorporated could not be confirmed from a primary Namibian source.
- Peak sun hours (5,0–5,5) for Okongo is an engineering estimate, not a sourced figure; confirm against a solar resource dataset for the exact site.
