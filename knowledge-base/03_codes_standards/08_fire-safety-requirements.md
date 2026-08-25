---
id: codes.fire_safety
title: Fire safety — SANS 10400-T and SANS 10400-W in practice
domain: 03_codes_standards
tags: [sans-10400-t, sans-10400-w, fire-protection, escape-routes, travel-distance, fire-resistance, occupancy-classification, hose-reels, sprinklers, sans-10287, residential-fire]
jurisdiction: south-africa
status: stable
confidence: high
updated: 2026-08-25
paywalled: true
sources:
  - {title: "SANS 10400-T:2020 Edition 4, Fire protection (archived)", url: "https://archive.org/details/sans-10400-t-2020-ed-4_20201029", publisher: "SABS", accessed: 2026-08-25}
  - {title: "SABS Webstore — SANS 10400-T and -W listings", url: "https://store.sabs.co.za/catalogsearch/result/?q=SANS%2010400", publisher: "SABS", accessed: 2026-08-25}
  - {title: "Regulation A20 — Classification and designation of occupancies", url: "https://source.acts.co.za/national-building-regulations-and-building-standards-act-1977/r2378_a20__classification_and_.php", publisher: "Acts Online (Source)", accessed: 2026-08-25}
  - {title: "National Building Regulations (consolidated, 2008 reprint)", url: "https://resource.capetown.gov.za/documentcentre/Documents/Procedures,%20guidelines%20and%20regulations/NATIONAL%20BUILDING%20REGULATIONS%202008.pdf", publisher: "City of Cape Town", accessed: 2026-08-25}
related: [codes.za.sans10400_register, codes.za.nbr_act, codes.compliance_checklists]
unit_system: SI
---

# Fire safety — SANS 10400-T and SANS 10400-W in practice

**Summary.** **[ZA]** NBR Part T (regulations T1 and T2) is the fire protection functional regulation; Part W (W1–W4) governs the fire installation — the water supply for fire fighting. SANS 10400-T is the deemed-to-satisfy standard for Part T and is by far the largest part of the series; SANS 10400-W is its water-supply companion. Everything in fire design flows from the **occupancy classification** in Regulation A20 and the **population** in Regulation A21. **[NA]** Neither has legal force in Namibia, but Namibian councils review plans against "Fire" standards (the City of Windhoek names Fire explicitly as one of the four review heads) and SANS 10400-T is the reference in practice.

**Values below are verified from SANS 10400-T:2020 Edition 4.** The current edition is **SANS 10400-T:2024 (Ed. 5.01)** (R1 373,10 on the SABS webstore, 2026-08-25). Re-verify before design use.

## Key facts — the numbers that govern most buildings

| Requirement | Value | Clause (Ed. 4, 2020) |
|---|---|---|
| Maximum travel distance to the nearest escape door | **45 m** | 4.16.2, 4.16.3 |
| Travel distance with a SANS 10287 life-safety sprinkler system | **60 m** (walls adjacent to the escape route to be separating elements with ≥ 30 min fire resistance, all openings protected) | 4.16.4(a) |
| Maximum total common path of travel | **35 m** | 4.16.6(b) |
| Maximum dead-end corridor | **10 m** (includes 10 m in and 10 m out) | 4.16.7 |
| Two escape routes required | Where travel distance > 45 m; a 2-storey building with > 25 persons on the upper storey; any 3-storey building; any building over 3 storeys | 4.16.2(b), 4.16.2(c), 4.16.3 |
| Emergency route required | Any building over 3 storeys; wherever travel distance > 45 m | 4.16.2(c), 4.16.3 |
| Clear width, exit/escape door from a room with ≤ 25 persons | **750 mm** | 4.20.1 |
| Clear vertical headroom throughout an escape route | **2 m** | 4.20.3 |
| Minimum room height in a lobby, foyer or vestibule | **2,4 m** | 4.20.3 |
| Maximum population per individual escape route | **190 persons** | 4.21.2(a) |
| Escape route illuminance while occupied | Minimum average **50 lux** on a horizontal plane 100 mm above the floor | 4.30.1 |
| Occupancy-separating element fire resistance | **60 / 90 / 120 min** per Table 4 | 4.6.1 |
| Hose reels required | Buildings of 2 or more storeys, or single-storey buildings > **250 m²**, at **one per 500 m²** or part thereof per storey | 4.34.1 |
| Hose reels not required | H4 occupancies; H3 dwelling units with independent access to ground level | 4.34.1 |
| Refuge fire resistance | **≥ 30 min**, one per stairway per storey | 4.16.8 |

## Occupancy classification is the master key

Every fire requirement is indexed on the Regulation A20 occupancy class (A1–J4 — see `01_south-africa-nbr-act.md` for the full table). The class determines:

- external wall fire resistance and boundary safety distances (Table 1, Table 2);
- occupancy-separating element ratings (Table 4);
- escape route provision and width (Table 9);
- fire detection and alarm requirements (Table 10);
- portable fire extinguisher provision (Table 10 in the extinguisher clause);
- hose reel, hydrant and sprinkler triggers.

Where a building contains more than one occupancy, clause 4.3 governs how they are treated and clause 4.6 requires occupancy-separating elements between them.

**Population (Regulation A21)** is the actual number of persons during normal use; where unknown, it is calculated from the A21 criteria — e.g. **1 person per 10 m²** for C1, E2, F1 and F2; **1 person per 15 m²** for B1, B2, B3, D1, D2 and D3.

## Safety distances and external walls (clause 4.2)

External walls (excluding carports) are classified into four types, tested to **SANS 10177-2**:

| Type | Definition |
|---|---|
| **FR** | Fire resistance equal to or exceeding Table 1 for the occupancy, complying with **stability, integrity and insulation** for that period |
| **F** | Fire resistance less than Table 1, but with **non-combustible external cladding**, complying with **stability and integrity** for the Table 1 period |
| **N** (combustible with full fire resistance) | Combustible wall complying with stability, integrity and insulation for the Table 1 period |
| **N** | Fire resistance less than Table 1, with combustible external cladding, **or** non-combustible cladding that failed stability or integrity for the Table 1 period |

**Clause 4.2.2:** where an external wall is type FR and contains **no window or other opening**, there is **no restriction on the safety distance** for that wall. This is the rule that permits building on the boundary.

> ⚠️ Attaching combustible cladding to a type FR or type F wall converts it to a **type N wall** for safety-distance purposes, unless the composite has been tested to SANS 10177-2, in which case the tested resistance applies. This is the post-Grenfell provision and it is the trap in any rainscreen or timber-clad facade.

## Fire resistance of occupancy-separating elements — Table 4 (clause 4.6)

Table 4 gives the required fire resistance in minutes between occupancy groups. The structure of the table:

- **Any separation involving B1, D1, B2, D2, J1, A1, A2, A4, F1, F3 or D4 requires 120 min** against everything else.
- **E1, E2, E3, E4 (institutional and healthcare)** require **120 min** against the high-risk group above, and **90 min** against everything else.
- The remaining groups — **A3, J2, F2, G1, J3, J4, H1, H2, H3, H4, H5, A5, C1, C2, B3, D3** — require **120 min** against the high-risk group, **90 min** against E1–E4, and **60 min** against each other.

So for ordinary residential and commercial work the number to remember is **60 minutes between different low-risk occupancies, 90 minutes against institutional, 120 minutes against high-risk or assembly.**

Clause 4.6.2 deals with movement joints in separating elements. Related clauses: 4.7 fire stability of structural elements, 4.8 tenancy-separating elements, 4.9 partition walls, 4.10 protection of openings (fire doors and dampers), 4.39 fire-stopping of inaccessible concealed spaces, 4.40 protection in service shafts, 4.41 services penetrating structural or separating elements.

## Escape routes (clause 4.16 onwards)

### The three components

1. **Escape route** — the entire route from any point in the building to a street or public place.
2. **Feeder route** — the horizontal circulation portion leading to access doors and escape doors. A feeder route must lead **in two different directions** to two or more independent emergency routes or escape doors (4.16.4(c)).
3. **Emergency route** — the fire-protected portion, including a stairway forming part of the escape route and the part of the route from the lower end of that stairway to any escape door (4.16.2(c)(2)).

### When each is required

**Travel distance ≤ 45 m** (4.16.2):

- **(a)** In a single-storey building, in a dwelling unit with an escape door at ground level, or from a first-storey dwelling unit served by its own individual stairway to ground level — **no emergency route required**, and for a dwelling unit the escape route need not comply with clauses 4.17 to 4.30 inclusive, **except 4.23.1**.
- **(b)** In a building of two or three storeys — no emergency route required, **provided that** a two-storey building where the upper storey population exceeds **25 persons**, or any three-storey building, has **not fewer than two escape routes**.
- **(c)** Any building over three storeys — **not fewer than two escape routes**, and an **emergency route must form part of each**.

**Travel distance > 45 m** (4.16.3): not fewer than two escape routes, each including an emergency route.

**Where emergency routes are required** (4.16.4): travel distance to the nearest access door or escape door **≤ 45 m** (or 60 m with a SANS 10287 life-safety sprinkler system and 30-min separating walls with protected openings); the path of travel to access and escape doors must be along a feeder route; and the feeder route must lead in two directions to two or more independent emergency routes or escape doors.

**Other limits:**
- Exit door from any room leads directly into a feeder route or common path of travel; it may lead into another room within the same tenancy if that room's exit door leads into a feeder route and the distance limits are not exceeded. **Total common path of travel ≤ 35 m** (4.16.6).
- **Dead-end corridor ≤ 10 m** (4.16.7) — the note clarifies this includes 10 m in and 10 m out.

### Accessibility interface

Clause 4.16.5: all doorways and circulation spaces, obstructions in the path of travel, stairways, ramps, handrails and warning signals along escape routes must comply with **SANS 10400-S**. The standard's note asks the competent person (fire engineering) and the competent person (environmental access) to co-ordinate their designs.

**Refuges** (4.16.8) must be provided in buildings containing emergency routes that must satisfy NBR Part S: at least one per stairway per storey; **fire resistance ≥ 30 min**; sized to accommodate a wheelchair user and a companion; located so as not to adversely affect escape routes.

### Locking devices

**Clause 4.16.9:** every locking device on an access or escape door in an escape route must be of a type approved by the local authority; electronic locking devices must be **failsafe** and provided with a **manual release**. The standard states that keys in break-glass boxes are unacceptable.

### Width of escape routes (clause 4.21)

- Population is the actual number in normal use; if unknown, calculated per Regulation A21.
- Where multiple escape routes discharge into a common component, the width of that component and all subsequent components is calculated on the combined population — **except** that for a stairway only the population of the **most heavily populated storey** served is deemed to discharge into it.
- Width per Table 9 for the population concerned, provided that:
  - **(a)** no individual escape route may be designed for a population of more than **190 persons**; and
  - **(b)** where there are two or more escape routes, **one route is discounted** when determining the widths required for the remainder (the classic "loss of one exit" rule).
- Aggregate width must be distributed so individual route widths are as nearly equal as practicable.

## Emergency lighting, detection and alarm

**Emergency lighting (4.30):**
- Escape routes must have artificial lighting giving a minimum average **50 lux** on a horizontal plane **100 mm above the floor** whenever the building is occupied, including above the exit door at the discharge of an emergency stairway or leading to external stairs.
- Buildings with emergency routes require emergency light sources along the escape routes to the point of discharge into a street or public place, on a power supply **independent of the mains** and capable of supplying them for not less than the periods in Table 5 on failure of the normal lighting.
- Emergency light sources, minimum levels and design must comply with **SANS 10114-2** and **SANS 1464-22**.
- Required in any basement escape route, in occupancies **A1, A2, A3, A4, C1, C2, E2, E3, E4, F1, F3, H1 or H5**, and in any building **excluding H4** that may be occupied during hours of darkness.

**Fire detection and alarm (4.31):** provided per Table 10 by occupancy class, with columns for buildings of any size, buildings with a floor area of **500 m² or more**, buildings over **4 storeys**, and further triggers. The standard's guidance note sets out the escalation: in small premises, people detect fire and a simple manual call point with bell, battery and charger suffices; in larger premises an electrically operated fire warning system with manual call points adjacent to exit doors and adequate sounders; in larger complex buildings **or buildings in which people sleep, an automatic fire detection system with alarms throughout is necessary**; where occupants may not respond quickly or are unfamiliar with the arrangements, a voice evacuation system should be considered.

## Fire installation and water supply — SANS 10400-W

NBR Part W (W1–W4) covers installations, water supply, design and deemed-to-satisfy. **SANS 10400-T clause 4.33** defers entirely: "Installations, which convey water solely for fire-fighting purposes, shall be in accordance with SANS 10400-W." Current edition **SANS 10400-W:2026 (Ed. 3.01)**, R523,25.

Part W governs fire mains and reticulation, hydrant provision and spacing, static water storage where the municipal supply is inadequate, pumps and boosters, and the water supply to hose reels. Regulation W4 rational design is a Regulation A19 competent person trigger.

*Hydrant spacing, flow rates, pressures and static storage volumes were not verified from a public source — consult the purchased SANS 10400-W and, critically, the local fire department's own requirements, which frequently exceed the standard.*

### Hose reels (SANS 10400-T 4.34)

- **Required** in any building of **two or more storeys**, or any single-storey building of more than **250 m²** floor area.
- **Rate: one hose reel per 500 m²** or part thereof of floor area in any storey.
- **Not required** in any building classified **H4**, or in any dwelling unit in an **H3** occupancy where each unit has independent access to ground level.
- Must comply with **SANS 543**, installed per **SANS 10105-2** and **SANS 10400-W**.
- Positioned so the hose end reaches any point in the protected area — measured as physical reach of hose and nozzle, in the same manner as travel distances, **not** a hypothetical arc of water. Allowable hose length should not be less than **28 m** before replacement (SANS 1475-2).
- **Where no water supply is available: two 9 kg DCP extinguishers or equivalent** (4.34.4).

### Extinguishers (4.37, 4.38)

- Provided per Table 10 for the relevant occupancy and floor area, in readily accessible and unobstructed positions approved by the local authority.
- The local authority may specify the type and may require more than the table indicates where hazards warrant.
- Must comply with **SANS 1910** and be installed, maintained and serviced by competent persons per **SANS 1475-1** and **SANS 10105-1**.
- A mobile fire extinguisher may replace **half** the required portable extinguishers, subject to capacity conditions (4.38.2).

### Sprinklers

**SANS 10287** is the sprinkler standard. Its most-cited role in Part T is clause 4.16.4(a): a sprinkler system designed, installed, maintained and configured by competent persons as a **life-safety installation** in accordance with SANS 10287 permits the travel distance to increase from **45 m to 60 m**, provided walls adjacent to the escape route are separating elements with at least **30 min** fire resistance and all openings are protected. Current edition **SANS 10287:2025 (Ed. 2.00)**, R2 150,50.

## Typical residential obligations

### H4 dwelling house — the simple case

A single detached house on its own erf, single storey, is the least regulated case:

- **No hose reels** (4.34.1 excludes H4).
- **No emergency lighting** requirement (4.30.4 excludes H4).
- **Escape route:** a single-storey building or a dwelling unit with an escape door at ground level needs no emergency route, and the escape route need not comply with clauses 4.17 to 4.30 except **4.23.1** (stairways and changes of level) — 4.16.2(a).
- Travel distance ≤ 45 m — trivially satisfied in almost any house.
- The substantive requirements are **boundary safety distances** and **separation from the neighbour**.

### Category 1 single-storey H3 and H4 buildings — clause 4.57

A *category 1 building* is occupancy A3, A4, F2, G1, H2, H3 or H4; no basement; maximum **6,0 m** between intersecting walls or members providing lateral support; floor area **≤ 80 m²**. In SANS 10400-T it is additionally restricted to a **single storey**.

**Minimum distance from an external wall to the lateral and rear boundary (4.57.1):**

| Wall condition | Minimum boundary distance |
|---|---|
| (a) No openings, fire resistance (stability, integrity **and** insulation) ≥ 30 min | **0 m** |
| (b) No openings, non-combustible external cladding, surface area ≤ 7,5 m², fire resistance < 30 min but tested to comply with stability and integrity for ≥ 30 min | **0,5 m** |
| (c) As (b) but surface area > 7,5 m² | **1,0 m** |
| (d) Walls as (a), (b) or (c) **with openings** | Per Table 18 below, provided openings in walls at right angles to the boundary are at least **500 mm** from the boundary |
| (e) Combustible external cladding, or non-combustible cladding without a 30 min stability or integrity rating | **4,5 m** — the entire facade is treated as an opening, and the minimum boundary is at least that in Table 2 column 2 (low fire load) |

**Table 18 — Minimum boundary distances where the wall has openings:**

| Area of openings in elevation (m²) | Minimum boundary distance (m) |
|---|---|
| < 5 | **1,0** |
| 5 | **1,5** |
| 7,5 | **2,0** |
| 10 | **2,4** |

**Combustible roof cladding (4.57.2):** the distance from the boundary to the edge of the combustible material follows the requirements for combustible roofs, **unless the roofing system is the subject of an Agrément certificate**, in which case the assessed safety distances apply.

**Detached category 1 H3/H4 with internal walls lacking 20 min fire resistance (4.57.3):** external doors must be located so an occupant does not have to move through **more than one room** to reach an external door or escape route; boundary distances must suit the roof and wall cladding type.

**Attached category 1 H3/H4 buildings (4.57.4)** — semi-detached and row housing — must have one of:

- **(a)** external walls with 30 min fire resistance (stability and integrity) **and** a separation wall with 30 min (stability, integrity and insulation) between buildings, extending to the underside of a non-combustible roof covering; or
- **(b)** combustible external walls (or non-combustible with < 30 min), **and** a 30 min separation wall extending to the underside of a non-combustible roof covering with **projections of at least 500 mm** beyond the faces of the external walls; or
- **(c)** combustible external walls (or non-combustible with < 30 min), **and** a 30 min separation wall extending **500 mm above a combustible roof covering** with projections extending at least 500 mm beyond the external wall faces.

> ⚠️ In row and semi-detached housing, the party wall must go **all the way up** — to the underside of a non-combustible roof covering, or 500 mm above a combustible one. A party wall stopped at ceiling level with a continuous roof void over it is one of the most common and most dangerous defects in South African and Namibian townhouse construction.

### H5 guest houses and bed and breakfast (4.58)

A building with occupancy H5 has additional requirements over and above the general provisions. **The specific requirements of 4.58 were not extracted and are not verified** — consult the purchased standard. Note that H5 is defined as transient room rental **within a dwelling for a maximum of 16 persons**; above that the occupancy becomes H1 (hotel), with materially heavier obligations including emergency lighting.

### H3 domestic residence — multiple dwelling units on one site

Once a development has multiple units on a single site it becomes H3, which brings in:

- **Hose reels** unless each unit has independent access to ground level (4.34.1);
- **Occupancy-separating elements** at 60 min between H3 and other low-risk occupancies (Table 4);
- **Party wall continuity** per 4.57.4 where the units are attached category 1 buildings;
- **Access for fire-fighting and rescue** (4.54) — the fire department must be able to reach the buildings;
- **Fire detection** per Table 10, and emergency lighting where the building may be occupied during hours of darkness (H3 is not excluded from 4.30.4 in the same way H4 is — check the current edition's Table 5 and 4.30.4 list carefully).

## The rational design route for fire

**Annex B (normative)** of SANS 10400-T deals with rational designs. NBR Regulation **T1(2)** is a Regulation A19 trigger: a fire engineering rational design must be prepared by an approved competent person (fire engineering), who then assumes responsibility for satisfying regulation T1 **in its entirety** and certifies the fire protection system on **Form 4** under s 14(2A) of the Act. Annex C of the 2020 edition deals with the appointment of the competent person.

Fire engineering rational design is the normal route for shopping centres, warehouses, atria, large-volume industrial buildings, heritage buildings and anything where the prescriptive travel distances or compartment sizes cannot be met.

## Sources

- [SANS 10400-T:2020 Edition 4 (archived)](https://archive.org/details/sans-10400-t-2020-ed-4_20201029) — all clause numbers and values above
- [SABS Webstore](https://store.sabs.co.za/catalogsearch/result/?q=SANS%2010400) — SANS 10400-T:2024 (Ed. 5.01), SANS 10400-W:2026 (Ed. 3.01), SANS 10287:2025 (Ed. 2.00), accessed 2026-08-25
- [Regulation A20 occupancy classification](https://source.acts.co.za/national-building-regulations-and-building-standards-act-1977/r2378_a20__classification_and_.php) — Acts Online Source
- [National Building Regulations, consolidated 2008 reprint](https://resource.capetown.gov.za/documentcentre/Documents/Procedures,%20guidelines%20and%20regulations/NATIONAL%20BUILDING%20REGULATIONS%202008.pdf) — NBR Parts T and W regulation numbering

## Open questions

- **All values above are from Edition 4 (2020). The current edition is SANS 10400-T:2024 (Ed. 5.01)** and its changes are unverified. Re-verify travel distances, Table 4, Table 18 and the category 1 provisions.
- **Table 1 and Table 2** (fire resistance of external walls, and boundary distances by fire load) — the numeric contents were not extracted and are not verified.
- **Table 9** (width of escape routes by population) — not verified.
- **Table 10** (fire detection requirements by occupancy; and the portable extinguisher table) — not verified.
- **Table 5** (emergency power supply duration) — not verified.
- **Clause 4.58** requirements for H5 guest houses and B&Bs — not verified.
- **SANS 10400-W** hydrant spacing, flow, pressure and static storage requirements — not verified. Local fire department requirements typically exceed the standard and must be obtained separately.
- **Clause 4.55** (presumed fire resistance of building materials and components) — the tables giving presumed ratings for common masonry, concrete and plasterboard constructions were not extracted. These are the tables a designer actually uses to demonstrate a 30, 60, 90 or 120 minute rating without testing.
- **[NA]** What fire requirements Namibian local authorities apply. The City of Windhoek names "Fire" as one of four plan-review heads but publishes no fire standard. Obtain the fire brigade's requirements directly.

