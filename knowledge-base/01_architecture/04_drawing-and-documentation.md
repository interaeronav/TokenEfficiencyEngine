---
id: arch.drawing_documentation
title: Drawing types, scales, conventions and the construction set
domain: architecture
tags: [drawings, scales, line-weights, dimensioning, revision-control, drawing-numbering, schedules, tender, construction-set, as-built, sans-10143, iso-19650]
jurisdiction: southern-africa
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "SANS 10143 (SABS 0143) Code of practice: Building drawing practice, Edition 1, 1980", url: "https://www.studocu.com/en-za/document/cape-peninsula-university-of-technology/technical-drafting/tcd150x-sans-10143-complete-building-drawing-guideline/28039413", publisher: "SABS (via Studocu transcription)", accessed: 2026-08-25}
  - {title: "AMP 010 — Engineering Drawing Standards Rev 00", url: "https://publishedetenders.blob.core.windows.net/publishedetenderscontainer/84527/AMP%20010%20-%20Engineering%20Drawing%20Standards_Rev%2000_BI.pdf", publisher: "South African public tender document", accessed: 2026-08-25}
  - {title: "City of Windhoek — Submission form for building plans", url: "https://www.windhoekcc.org.na/wp-content/uploads/2023/11/Submission-Form-For-Building-Plans_0.pdf", publisher: "City of Windhoek", accessed: 2026-08-25}
  - {title: "City of Windhoek — Urban planning application submission requirements", url: "https://www.windhoekcc.org.na/wp-content/uploads/2026/02/Application-Submission-Requirements.pdf", publisher: "City of Windhoek", accessed: 2026-08-25}
  - {title: "ISO 19650 naming convention guide", url: "https://www.cde19650.com/blog/iso-19650-naming-convention-guide/", publisher: "CDE 19650", accessed: 2026-08-25}
related: [arch.design_fundamentals, arch.professional_practice]
unit_system: metric
---

# Drawing types, scales, conventions and the construction set

**Summary.** Drawings are the architect's legal instrument: they instruct the contractor, define the contract works, and are the primary evidence in any dispute. This file sets out the drawing hierarchy and its scales, the graphic conventions (line weight, annotation, dimensioning, north point), drawing numbering and revision control, the five successive states of a drawing set (concept → municipal submission → tender → construction → as-built), the standard schedules, and a checklist of what a complete construction set contains. **[ZA]** conventions derive from **SANS 10143 (SABS 0143), *Code of practice: Building drawing practice*, Edition 1, 1980**; **[NA]** practice follows the same conventions with local-authority variations.

## Key facts — scales

| Drawing type | Preferred scale(s) | What it shows |
|---|---|---|
| Locality / block plan | **1:1000, 1:500** | The erf in its street context; adjoining erven; north |
| Site plan | **1:500, 1:200** | Boundaries, building lines, levels, contours, access, services, coverage |
| General arrangement (GA) plans, sections, elevations | **1:100, 1:50** | Layout, grid, room names/numbers, doors/windows, levels, dimensions |
| Enlarged plans (kitchens, bathrooms, cores, stairs) | 1:50, 1:20 | Setting-out of fittings and finishes |
| Assembly / component details | **1:20, 1:10, 1:5** | Junctions, build-ups, waterproofing, fixings |
| Full-size details | **1:1, 1:2** | Profiles, mouldings, joinery sections, seals |
| Reflected ceiling plans | 1:100, 1:50 | Ceiling grid, luminaires, diffusers, access panels |
| Schedules and diagrams | n/a | Door, window, finishes, ironmongery, sanitaryware |

Preferred scale series (engineering practice): **1:1, 1:2, 1:5, 1:10, 1:20, 1:25, 1:50, 1:100, 1:200, 1:500, 1:1000**, extending upward. Never invent a scale — 1:75 and 1:150 are unreadable with a standard scale rule.

## Key facts — sheets and text

| Sheet | Size (mm) |
|---|---|
| A0 | 841 × 1189 |
| A1 | 594 × 841 |
| A2 | 420 × 594 |
| A3 | 297 × 420 |
| A4 | 210 × 297 |

A1 and A2 are the standard architectural/engineering plot sizes; A3 is the standard reduced set for site and meetings. Text heights on the plotted sheet: **titles 5 mm; grid references 3,5 mm; dimensions and general notes 2,5 mm.** Use a single narrow sans-serif face (Arial Narrow, ISOCPEUR) throughout a set.

## Line weights

Line weight is the primary carrier of information in a drawing; a set with one line weight is unreadable regardless of how much is drawn.

| Weight | Typical pen (mm) | Use |
|---|---|---|
| Very heavy | 0,70–1,00 | Section cut through primary structure/ground; drawing border |
| Heavy | 0,50 | Section cut through secondary elements; building outline in plan |
| Medium | 0,35 | Elements in elevation beyond the cut; door/window frames |
| Light | 0,25 | Elements further beyond; fittings, sanitaryware, furniture |
| Very light | 0,18 | Hatching, surface texture, grid lines, extension lines |
| Dashed | 0,25 | Anything above or below the cut plane (overhangs, beams over, foundations under) |
| Chain (long-dash dot) | 0,25 | Grid lines, centrelines, section marks |
| Chain double-dot | 0,25 | Adjacent/existing elements not in the contract |

Convention: **the cut is black, the beyond is grey.** In a 1:50 wall section, the cut masonry gets the heaviest line and a hatch; the tiles and skirtings get the lightest.

## Annotation and dimensioning

- **Dimensions in millimetres**, without unit suffix, on building drawings; **metres to three decimals** on site plans and levels.
- Three dimension chains minimum on a GA plan: **overall**, **grid to grid**, **opening/setting-out**. Never require the contractor to add or subtract to find a dimension.
- Dimension to **structure**, not to finishes, unless the finish is the setting-out datum (then say so).
- Levels: shown as **+3.250** style, referenced to a stated datum. Give the datum explicitly on the site plan (mean sea level or an assumed site datum with a described benchmark). **FFL** = finished floor level; **SSL** = structural slab level; **NGL** = natural ground level.
- Never scale a drawing: print `DO NOT SCALE. WORK TO FIGURED DIMENSIONS.` in the title block.
- **North point** on every plan **[ZA]** SANS 10143; **[NA]** City of Windhoek requires a north arrow, scale, erf boundaries, existing buildings and contours at ≥ 1 m intervals on planning application drawings.
- Room names **and** numbers on GA plans; the number is the key into the finishes schedule.
- Hatching: use SANS 10143 material conventions, and **always add a descriptive note stating type and thickness** — the standard warns to use symbols "only where confusion is likely to occur" and to avoid colouring, which is "costly, laborious, and conducive to error."
- Section and detail markers: a bubble with detail number over sheet number, plus a direction of view. Every marker must have a target; audit for orphans before issue.

## Drawing numbering and revision control

Two live systems in Southern Africa:

**1. Traditional discipline-series numbering.** Prefix by discipline and series:

| Prefix | Discipline | Series |
|---|---|---|
| A | Architectural | A-000 general/notes; A-100 site; A-200 plans; A-300 elevations; A-400 sections; A-500 details; A-600 schedules; A-700 interiors |
| S / C | Structural / Civil | |
| E | Electrical | |
| M | Mechanical | |
| P / W | Plumbing / Wet services | |
| F | Fire | |
| L | Landscape | |

**2. ISO 19650 (BIM/CDE projects).** Seven mandatory fields:
`Project_Originator_Volume_Level_Type_Role_Number`
e.g. `OFFICES-A_HEXC_A_01_DR_AR_0001` — where Volume `ZZ` = whole project, Level `00` = ground / `ZZ` = all / `XX` = not applicable, Type `DR` = drawing / `MO` = model / `SP` = specification, Role `AR` = architecture / `ST` = structure.

**Revisions.**
- Preliminary/design issues use a **P-series** (P01, P02 …); construction issues use a **C-series** (C01, C02 …). A common alternative in SA practice: **letters A, B, C… for pre-tender revisions and numbers 1, 2, 3… after construction issue**, with `ZZ` denoting as-built.
- Every revision needs: revision code, date, a one-line description, and the initials of the author and checker, listed in a revision table on the sheet.
- Changed areas are **clouded** with a triangular revision tag carrying the revision code. Clouds from superseded revisions are removed at the next issue.
- Maintain a **drawing register / issue sheet** recording every drawing, its current revision, the date issued, and to whom. In a dispute this register is the first document requested.

> ⚠️ Superseded drawings must be recalled or clearly marked SUPERSEDED. Construction built to a stale revision is one of the most common and most expensive causes of professional-indemnity claims.

## The five states of a drawing set

| Set | Purpose | Typical scales | Characteristic content |
|---|---|---|---|
| **Concept / design** | Client approval of the idea | 1:200, 1:100 | Diagrams, massing, indicative plans/sections/elevations, area schedule, 3D views. No dimensions to build from. |
| **Municipal / statutory submission** | Statutory approval | 1:500 site, 1:100 GA | Site plan with boundaries, building lines, coverage and bulk calculations; GA plans, all elevations, at least one section; drainage layout; north; owner's and professional's signature and registration number; area schedule. **[NA]** City of Windhoek requires the submission form completed in block letters, owner's signature, designer's profession and registration number, and payment of the applicable fee before plans are accepted. |
| **Tender** | Pricing and procurement | 1:100, 1:50, key 1:20 details | Complete GA set, principal details, all schedules, specification/preambles, bills of quantities (QS). Sufficient for a contractor to price without assumption. |
| **Construction** | Building | 1:100, 1:50, 1:20, 1:10, 1:5, 1:1 | The tender set plus full detail packages, setting-out drawings, coordinated services, shop-drawing review record. Issued under a formal issue sheet. |
| **As-built / record** | Handover and facilities management | as constructed | Marked-up construction set reflecting actual construction, incorporating variations, RFI answers and shop drawings; plus O&M manuals, warranties, certificates. **[ZA]** produced in PROCSA Stage 6 Close-out. |

## Schedules

Schedules move repetitive data out of the drawings, where it would be repeated and would drift.

**Door schedule** — one row per door number (which matches the plan tag). Columns: door number; room from/to; leaf size (W × H × thickness); frame type/section/material; leaf material and finish both faces; glazing type; fire rating and smoke seal; acoustic rating; hand and swing direction; ironmongery set reference; threshold detail; lock/access-control type; remarks.

**Window schedule** — window number; type reference; overall structural opening size; frame material, system and finish; glass specification (thickness, type, low-E, safety glass where required); opening type (casement/awning/sliding/fixed) and which panes open; openable area (for **[ZA]** SANS 10400-O compliance); sill and head details; burglar bar / insect screen; sill level relative to FFL.

**Finishes schedule** — one row per room number. Columns: floor, skirting, walls (each of four, if they differ), ceiling, ceiling height, cornice, special notes. Cross-reference a materials legend giving product, manufacturer, colour and reference.

**Ironmongery schedule** — set number; contents (hinges — quantity/size/grade; lockset and cylinder; lever handles; closer; flush bolts; door stop; kick plate; signage); finish; keying/suite reference. Assign sets to doors in the door schedule, not the other way round.

**Sanitaryware and fittings schedule** — item code, product, manufacturer, size, mounting height, connection requirement.

**Room data sheets** (larger/technical projects) — per room: area, occupancy, finishes, environmental criteria (temperature, air changes, lux level, acoustic criterion), power and data outlets, medical/specialist gases, equipment list.

## What a complete construction set contains

1. **A-000 series** — cover sheet and drawing list; general notes; abbreviations and symbols legend; materials legend; statutory compliance notes; demolition drawings where applicable.
2. **A-100 series** — site plan (boundaries, levels, building lines, coverage/bulk table, access, external works, stormwater); site sections; setting-out plan with coordinates or dimensioned offsets from two boundaries.
3. **A-200 series** — floor plans at 1:100 (and 1:50 for complex areas), one per level, including roof plan; enlarged plans for cores, kitchens, ablutions, stairs.
4. **A-300 series** — all elevations, with materials, levels and any statutory height envelope shown.
5. **A-400 series** — sections: at minimum one longitudinal and one transverse through the most complex condition; a typical bay wall section at 1:20 from foundation to parapet.
6. **A-500 series** — details: eaves/verge/parapet; window and door head, jamb, sill; floor and wall junction, DPC and DPM; roof/wall junction; balustrade fixing; movement joints; waterproofing at wet areas and thresholds; skylights and penetrations.
7. **A-600 series** — door, window, finishes, ironmongery, sanitaryware schedules.
8. **A-700 series** — reflected ceiling plans; joinery and built-in furniture drawings; signage.
9. **Specification / preambles** — materials, workmanship, standards referenced, testing and sample requirements.
10. **Coordinated consultant drawings** — structural, civil, electrical, mechanical, wet services, fire.

**Pre-issue audit checklist:** every room numbered; every door and window tagged and scheduled; every section and detail marker targeted; every level annotated; north on every plan; scale bar and stated scale on every sheet; title block complete; revision table updated; drawing list matches the sheets actually issued; consultant drawings coordinated (clash-checked if modelled); statutory notes present.

## Sources

- [SANS 10143 (SABS 0143) Building drawing practice — transcription](https://www.studocu.com/en-za/document/cape-peninsula-university-of-technology/technical-drafting/tcd150x-sans-10143-complete-building-drawing-guideline/28039413) — SABS via Studocu
- [SANS 10143 material representation — transcription](https://www.studocu.com/en-za/document/university-of-pretoria/civil-engineering/sans-guidelines/121497317) — SABS via Studocu
- [AMP 010 — Engineering Drawing Standards](https://publishedetenders.blob.core.windows.net/publishedetenderscontainer/84527/AMP%20010%20-%20Engineering%20Drawing%20Standards_Rev%2000_BI.pdf) — SA public tender document
- [City of Windhoek — Submission form for building plans](https://www.windhoekcc.org.na/wp-content/uploads/2023/11/Submission-Form-For-Building-Plans_0.pdf) — City of Windhoek
- [City of Windhoek — Urban planning application submission requirements](https://www.windhoekcc.org.na/wp-content/uploads/2026/02/Application-Submission-Requirements.pdf) — City of Windhoek
- [City of Windhoek — Building Control](https://www.windhoekcc.org.na/building-control/) — City of Windhoek
- [ISO 19650 naming convention guide](https://www.cde19650.com/blog/iso-19650-naming-convention-guide/) — CDE 19650

## Open questions

- SANS 10143 is a 1980 edition and was accessed only via third-party transcriptions, not from SABS directly; clause numbers are therefore **not** cited in this file and the scale/line-weight tables should be treated as practice convention corroborated by the standard rather than verbatim quotation. Marked `confidence: medium` for that reason.
- The line-weight table is industry practice; SANS 10143 specifies graduated weights but the specific millimetre values above are conventional, not quoted from the standard.
- **[NA]** The City of Windhoek does not publish required drawing scales or copy counts for *building plan* (as distinct from urban planning) submissions; confirm with Building Control before issue.
- Whether **[NA]** requires plans to be submitted by a registered architectural professional (as opposed to merely recording their registration number) is not stated on the submission form; note that urban planning applications *must* be submitted by a registered town planner.
