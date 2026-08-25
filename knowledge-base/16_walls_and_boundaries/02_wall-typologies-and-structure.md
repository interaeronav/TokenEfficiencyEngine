---
id: walls.typology
title: Wall typologies and structural behaviour
domain: 16_walls_and_boundaries
tags: [typology, loadbearing, cavity-wall, collar-jointed, diaphragm-wall, retaining-wall, gabion, crib, rammed-earth, adobe, precast-panel, palisade, hedge, lifespan, maintenance]
jurisdiction: southern-africa
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "SANS 10400-K:2011 The application of the National Building Regulations Part K: Walls", url: "https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html", publisher: "SABS / Internet Archive", accessed: 2026-08-25}
  - {title: "Quantities for ordering building materials", url: "https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf", publisher: "Cement & Concrete SA", accessed: 2026-08-25}
  - {title: "Gabion", url: "https://en.wikipedia.org/wiki/Gabion", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Mechanically stabilized earth", url: "https://en.wikipedia.org/wiki/Mechanically_stabilized_earth", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Rammed earth", url: "https://en.wikipedia.org/wiki/Rammed_earth", publisher: "Wikipedia", accessed: 2026-08-25}
  - {title: "Geolok earth retainers", url: "https://www.corobrik.co.za/geolok-earth-retainers", publisher: "Corobrik", accessed: 2026-08-25}
  - {title: "Enviro Wall", url: "https://www.technicrete.co.za/products/enviro-wall/", publisher: "Technicrete (ISG)", accessed: 2026-08-25}
  - {title: "Dry stone", url: "https://en.wikipedia.org/wiki/Dry_stone", publisher: "Wikipedia", accessed: 2026-08-25}
related: [walls.boundary_design, walls.construction, walls.companies]
unit_system: SI
---

# Wall typologies and structural behaviour

**Summary.** Wall types are distinguished by how they get their stability: from vertical load (loadbearing), from section (thick freestanding), from geometry (Z-plan, diaphragm, buttressed), from mass (gravity retaining, gabion, crib), from reinforcement (cantilever RC, reinforced masonry, reinforced soil), or from framing (panel-and-post, palisade, mesh). This file is a systematic typology; for each type it gives structural behaviour, typical dimensions, foundation requirement, relative cost band, lifespan and maintenance. All masonry dimensions and pier rules are from **SANS 10400-K:2011**, clause 4.2.4 and Tables 16–19.

## Key facts

| Type | Typical thickness | Typical max height (freestanding) | Foundation | Lifespan (design) |
|---|---|---|---|---|
| Single-leaf solid masonry, no piers | 90 / 110 / 140 / 190 / 220 / 290 mm | 0,8 / 1,0 / 1,3 / 1,5 / 1,8 / 2,2 m | Concrete strip | 40–60 yr |
| Single-leaf hollow masonry, no piers | 90 / 140 / 190 mm | 0,8 / 1,2 / 1,4 m | Concrete strip | 40–60 yr |
| Z-shaped (staggered) solid wall | 110 mm with 440 × 110 piers @ 1,5 m | **2,1 m** | Continuous strip incl. piers | 40–60 yr |
| Piers projecting one side, solid | 220 mm with 660 × 440 piers @ 3,2 m | **2,3 m** | Strip, widened at piers | 40–60 yr |
| Diaphragm wall, solid units | 90 mm leaves, ribs 390 × 190 @ 1,4 m | **2,7 m** | Strip under both leaves | 40–60 yr |
| Cavity wall | 2 leaves, cavity ≥ 50 ≤ 110 mm | Not a DTS freestanding type | Strip | 60+ yr |
| Precast concrete panel-and-post | panel ~50–75 mm thick | 1,8–2,4 m typical | Post footings only | 20–40 yr |
| Steel palisade fence | pales 40–50 mm | 1,8–2,4 m (electrified 2,4 m) | Post footings | 15–30 yr |
| Gabion (box) | 0,5 / 1,0 m basket width | Gravity: base ≈ 0,5–0,7 × height | Levelled bearing layer | PVC-coated galv. est. 60 yr |
| Rammed earth | 150 mm (non-LB) – 600 mm (LB) | Governed by slenderness | Concrete plinth | Centuries if protected |
| Segmental retaining block (dry-stacked) | 300 / 400 / 500 mm deep units | ~2 m unreinforced; more with geogrid | Compacted base + levelling pad | 50+ yr |
| Hedge / living boundary | 0,4–1,5 m spread | 1,0–3,0 m | None | Indefinite with management |

> ⚠️ Freestanding-wall heights in the table above are **deemed-to-satisfy maxima from SANS 10400-K Tables 17 and 18**, valid only where the wall retains no earth, piers run full height without reduction, the wall terminates in a pier or return, hollow pier cores are solidly filled, and the ground level difference *x* on the two sides does not exceed 0,3 m. Exceed any of those and the tables no longer apply — you need an engineer.

## 1. Loadbearing versus non-loadbearing

**Loadbearing** walls carry roof, floor and wall loads above. Their design is dominated by slenderness ratio (effective height ÷ effective thickness), eccentricity of load, and unit strength; SANS 10400-K's DTS rules for single- and double-storey buildings require unit strengths of **3,0 MPa hollow / 4,0 MPa solid** for a single storey and **7,0 MPa hollow / 10 MPa solid** for the lower storey of a double storey, roof mass ≤ 80 kg/m², and Class II mortar.

**Non-loadbearing** walls — infill panels, partitions, screens — carry only their own weight plus lateral load. For infill panels in framed buildings of four storeys or less, the wall must be cavity construction or ≥ 140 mm nominal thickness, with 0,4 m minimum masonry over openings and storey height ≤ 3,3 m.

**Freestanding** is the hardest case and is treated separately in the code because it has neither: no vertical load to pre-compress the bed joints, and no lateral restraint at the top. All of its resistance to overturning comes from self-weight acting about the toe of the base, plus the flexural bond of the mortar — and mortar bond in tension is the least reliable property in masonry. Design freestanding walls as if the bond strength were zero (see file `03`).

## 2. Single-leaf, collar-jointed, cavity, composite

**Single-leaf** — one unit width, units overlapping to bond. Simplest and cheapest. The whole section acts together.

**Collar-jointed** — two leaves laid tight against each other with the vertical "collar" joint solidly filled with mortar, so the two leaves act compositely. SANS 10400-K's retaining-wall table (Table 16) is built almost entirely around collar-jointed walls: 190 mm collar-jointed retains 1,3 m with 600 × 300 piers at 2,5 m; 220 mm collar-jointed retains up to 1,8 m with 880 × 440 piers at 3,1 m.

**Cavity** — two leaves separated by a **cavity not less than 50 mm and not more than 110 mm** (cl. 4.2.1.3), tied with metal wall ties. Excellent for rain resistance and thermal performance in buildings, but a poor freestanding boundary type: the cavity has to be capped, the ties corrode, and the two leaves have half the flexural stiffness of a solid section of the same overall thickness. **[ZA]/[NA]** Within 30 km of the coast, ties need ≥ 750 g/m² galvanizing; in tidal splash zones, stainless steel. Not a coastal issue at Okongo, but relevant for coastal Namibian work.

**Composite / faced** — a structural backing with a facing skin: brick-faced blockwork, stone-faced concrete, brick over rammed earth. The Roman *opus testaceum* idea. Structurally the backing does the work; the facing must be tied and must be free to move differentially.

> ⚠️ Never build a wall of mixed clay and concrete units. Clay masonry expands irreversibly on moisture uptake (up to 0,20 % under SANS 227); concrete masonry shrinks reversibly, 3–6 mm per 10 m against clay's ~1 mm per 10 m. The two move in opposite directions and the wall cracks.

## 3. Geometric stabilisation: Z-walls, piered walls, diaphragm walls

This is where boundary-wall design gets clever, and it is under-used in southern African practice.

**Z-shaped (staggered / serpentine / "crinkle-crankle") walls.** The wall is set out in a stepped or zig-zag plan so that the *effective* section resisting overturning is the full offset depth, not the wall thickness. SANS 10400-K Table 17 is emphatic about the efficiency gain: a **90 mm** solid wall with a 490 × 90 mm Z-offset at 1,4 m centres reaches **2,0 m high** — against 0,8 m for the same 90 mm wall with no piers. A **110 mm** Z-wall with 440 × 110 offsets at 1,5 m reaches **2,1 m**. A 220 mm Z-wall with 550 × 220 offsets at 4,0 m reaches **2,8 m**. Z-walls use less material than piered walls for the same height and are architecturally interesting; they cost more in setting-out and cutting.

**Piers projecting one side.** The conventional solution. Table 17: 110 mm wall with **550 × 330 mm** piers at **2,0 m** centres → 1,9 m high; 220 mm wall with **660 × 440 mm** piers at **3,2 m** centres → 2,3 m high.

**Piers projecting both sides.** Slightly *less* efficient per unit of masonry than one-sided piers of the same overall depth, because the section's neutral axis sits at mid-thickness: a 220 mm wall with 660 × 440 piers at 3,2 m reaches 2,1 m both sides versus 2,3 m one side. Choose two-sided piers for symmetry and appearance, not for structure.

**Diaphragm walls.** Two thin leaves joined by evenly spaced vertical ribs to form a hollow box section (cl. 3.18). Structurally the most efficient masonry form there is, because the material is concentrated at the extreme fibres. Table 17: **90 mm** leaves with 390 × 190 mm ribs at 1,4 m centres reach **2,7 m** — the tallest DTS freestanding solid-unit wall in the code, and it does it in 90 mm units. Hollow-unit diaphragm walls at 90 mm reach 2,3 m. The catch is bricklaying complexity and the need to keep the cavity clean and capped.

## 4. Retaining walls

A retaining wall resists lateral displacement of material (cl. 3.37). Four families:

**Gravity.** Resists overturning and sliding by its own weight. Mass concrete, mass masonry, or dry-stacked stone. The classic proportioning rule of thumb is a base width of **0,5–0,7 × retained height**, with the stem battered into the fill. SANS 10400-K Table 16 gives DTS masonry gravity/piered retaining walls: 140 mm single-leaf retains **1,3 m** with 600 × 300 piers at 1,8 m; 290 mm collar-jointed retains **1,0 m** with no piers; 300 mm collar-jointed retains **1,2 m** with no piers.

**Cantilever (reinforced concrete).** An L or inverted-T of reinforced concrete; the weight of soil on the heel provides most of the stabilising moment. Economic up to roughly 6–8 m. Needs designed reinforcement — outside DTS rules.

**Reinforced soil / MSE.** Horizontal layers of geogrid or steel strip in compacted granular fill, with a facing of precast panels, segmental blocks or wrapped geotextile. Invented in its modern form by **Henri Vidal** in the 1960s (*terre armée*); first geosynthetic-reinforced walls in France 1970–71, first US MSE wall 1971 on State Route 39 near Los Angeles. Advantages: no formwork or curing, each layer structurally sound as laid, tolerant of differential settlement, and shown on shaking-table tests at Japan's National Institute of Agricultural Engineering to withstand large deformation without loss of integrity. Reinforcement length is typically **0,7 × wall height** as a first estimate.

**Segmental / dry-stacked concrete retaining blocks.** The southern African workhorse. Named systems and real dimensions:
- **Corobrik Geolok** (SANS 508:2020): Geolok 300 = 400 × 300 × 200 mm, ±37 kg; Geolok 400 = 400 × 400 × 200 mm, ±47 kg; Geolok 500 = 400 × 500 × 200 mm, ±54 kg. About **7 blocks/m²** in a straight run. Geolok 300 suits walls up to 2 m; Geolok 400 above 2 m; Geolok 500 for face angles of **70° or steeper**.
- **Technicrete Enviro Wall**: standard face 275 × 300 mm, effective vertical height **136 mm** at 70° slope, ±23 kg, length ±2 000 mm of wall per... (see file `08`); **Rocenviro Wall** 240/300 mm, 136 mm effective at 70°, ±20 kg; **Florawall** 300/410/250 mm and 410/355/250 mm, ±29 kg, 10–13,3 units/m²; **Earthform** ±23 kg, 10 units/m² open.

**Drainage is not optional.** SANS 10400-K 4.2.4.1 requires, for DTS masonry retaining walls: control joints at not more than **10 m**; no surcharge within a distance equal to the retained height; and **subsoil drainage by weepholes of 50 mm diameter plastic pipe, geofabric-covered on the buried end, at not more than 300 mm above the lower ground level and at not more than 1,5 m centres**. Piers must project on the **opposite side to the fill**.

## 5. Freestanding boundary walls

Covered fully in file `03`. Structurally: a vertical cantilever from the foundation, loaded by wind pressure on one face and suction on the other, resisted by self-weight and (unreliably) by flexural bond. Two governing checks — **overturning about the toe** and **flexural tension in the bed joint at the base**. The code's response is to fix maximum height for a given thickness and pier arrangement, which is a proxy for both.

## 6. Screen walls and perforated walling

A screen wall trades wind resistance and privacy for light, air and cost. Perforation reduces the wind load coefficient markedly — this is exactly why the **Galloway dyke** is built porous in high-wind country. Products: clay breeze block (Corobrik's breezeblock is **222 × 73 × 106 mm**, **37 units/m²**, 2,2 kg each, **>10 MPa**, 24-hour water absorption 9,1, FBX classification, eight satin colours, 500 per pallet, made to order); concrete screen block; and the Brazilian ***cobogó***, named for the Recife engineers **Amadeu Oliveira Coimbra, Ernst August Boeckmann and Antônio de Góis**, conceived in 1929–30, originally cement-only and now also clay and glass.

Screen walling is **not** a security wall and is not a DTS freestanding type. Perforated panels normally need a framing structure: piers or a reinforced concrete frame at close centres, with the screen units as infill.

## 7. Gabion walls

A gabion is a wire cage filled with rock. Standard box gabions are supplied in 1 m and 0,5 m widths and heights with lengths in 1 m increments; the wire is galvanized, PVC-coated or stainless. **Life expectancy tracks the wire**: PVC-coated galvanized gabions are estimated at **60 years**, and some manufacturers guarantee 50 years' structural integrity. Maccaferri produced sack gabions from 1893 and patented the box-shaped erosion-control gabion in the early 20th century.

Structural behaviour: a gravity wall that is **flexible** — it deforms rather than cracks, tolerates settlement, and is free-draining. Its failure modes are undermining and **wire abrasion/corrosion**: early US Forest Service installations from 1957 largely failed because bedload movement abraded the wire, the baskets sagged and collapsed, and tree growth on revetments levered them over. Gabions also make good architecture — the **Dominus Estate winery** (Herzog & de Meuron, Yountville, Napa, 1996–97, ~4 600 m²) is faced entirely in modular wire-mesh gabions of locally quarried basalt, which lets air move through and moderates internal temperature.

For a boundary wall, gabions give: no formwork, no curing, tolerance of poor ground, a strong contemporary aesthetic, complete acoustic transparency (they do **not** attenuate noise well unless the voids are filled), and a security weakness — a gabion face is a climbing frame.

## 8. Crib walls

Interlocking precast concrete or timber headers and stretchers forming open cells filled with granular material — a gravity wall built as a crate of soil. Efficient in material, tolerant of movement, plantable, and buildable without skilled masons. Typical face batter 1:4 to 1:6. Depth of the crib (front-to-back) is roughly 0,5–0,6 × height for a single-depth crib, increasing to double-depth above about 4 m. `needs-verification` on those specific proportions against a manufacturer's design manual.

## 9. Rammed earth

Structural behaviour: a monolithic gravity wall in compression; weak in tension and in flexure, so freestanding heights are governed by the same slenderness logic as masonry but with lower material strength unless stabilised. **Unstabilised** rammed earth relies on clay cohesion; **cement-stabilised rammed earth (CSRE)** at 5–10 % cement reaches 5–18 MPa, and well-made Australian CSRE up to 40 MPa. Thickness 150 mm (non-loadbearing) to 600 mm (loadbearing). Lifts 100–250 mm loose, compacted to ~50 %.

Requirements that decide whether it will work: a **concrete or stone plinth** lifting the wall clear of splash — the 1714 Argentine ordinance requiring foundations of stone to *una vara* (86,6 cm) above natural ground before continuing in adobe or *tapia* is the historic version of this rule; a **generous coping or overhang** to keep rain off the face; and a **vapour-permeable finish** — cement render traps moisture and destroys the wall's ability to desorb.

Carbon caution: a **300 mm rammed-earth wall at 5 % cement produces slightly more emissions than a 100 mm concrete wall**. Rammed earth is only low-carbon if the cement content is low and the soil is local.

## 10. Adobe and compressed earth block

Sun-dried units laid in earth or lime mortar. Cheap, local, high thermal mass, but vulnerable at the base and to driven rain. **Compressed earth block (CEB)** — pressed, usually stabilised with 5–8 % cement, cured not fired — is the modern industrialised form and is a serious option in northern Namibia where the sand-clay balance can be corrected with imported clay or with cement. Same detailing rules as rammed earth: plinth, coping, breathable finish.

## 11. Precast concrete panel-and-post walling

The dominant southern African boundary product (file `08`). Slotted or grooved **posts** are set in concrete footings at fixed centres; horizontal **panels** — commonly around 300–350 mm high and spanning the post centres, often with a moulded pattern on one or both faces — drop into the grooves and stack to height. A **capping** finishes the top.

Structural behaviour is fundamentally different from masonry: the **posts are cantilevers** and the panels are one-way spanning slabs that transfer wind load to the posts. Almost all the structural demand is at the post base. That is where the failures occur — undersized or shallow post footings in loose sand. The panels themselves are usually thin (~50–75 mm) and lightly reinforced or unreinforced; they crack readily under impact and are individually replaceable, which is the system's main virtue.

Advantages: very fast, no wet trade on the wall itself, no curing water except in the footings, dimensionally consistent, and repairable panel-by-panel. Disadvantages: bland, easy to lever a bottom panel out and crawl through unless the panels are set below ground level, poor acoustic performance because of gaps, and low residual value.

## 12. Palisade and welded mesh fencing

**Steel palisade**: vertical pales (typically 40–50 mm channel or D-section) bolted to horizontal rails between posts. Electrified palisade fences are typically **2,4 m tall** with a 1 Hz pulse and are mechanically stronger than cable electric fences, resisting impact from wildlife, small falling trees and wildfires. Sees through; hard to climb if the pale tops are splayed or spiked; poor privacy; no acoustic benefit.

**Welded mesh (e.g. 358 "anti-climb" mesh)**: 76,2 × 12,7 mm apertures in 4 mm wire — too small for fingers or a bolt-cutter jaw. Superior to palisade for climb resistance; higher cost. `needs-verification` on the specific 358 mesh dimensions against a manufacturer datasheet.

**Diamond mesh / chain link**: the cheapest permanent boundary; easy to cut and lift; suitable for demarcation only.

**Concrete palisade**: precast concrete pales in precast posts; common in South Africa as a low-cost see-through boundary.

## 13. Timber walls, screens and slat fences

Vertical or horizontal timber slats on a steel or timber frame. Structural behaviour: a framed screen; the frame does everything. Key numbers: post embedment of at least **1/3 of the above-ground height** in concrete for a timber fence; slat gap sized for privacy angle. In Ohangwena the binding constraint is **termites and rot** — untreated timber in ground contact has a short life; use CCA/creosote-treated poles to the correct hazard class (H4/H5 for in-ground) or set timber on steel shoes above ground.

## 14. Hedges and living boundaries

The oldest boundary in Britain and still the cheapest at scale. Structural behaviour: none — it is a filter, not a barrier, until it is laid or interwoven. **Hedge-laying** (part-cutting stems and bending them near-horizontally so they re-shoot) produces a stock-proof living fence in 5–10 years. The **ha-ha** — a sunken wall in a ditch — achieves boundary without visual interruption and is worth knowing about wherever a view matters more than security.

In northern Namibia the equivalents are living euphorbia, sisal and thorn hedges, and the *omuzile*-type brush enclosure. Cost is essentially labour and time; maintenance is annual; lifespan is indefinite with management and zero without it.

## 15. Hybrid walls

Most good boundary walls in practice are hybrids, and the hybrid is usually the right answer:

- **Masonry plinth + palisade or mesh above** — puts mass where impact and dirt are, transparency where surveillance and cost matter. Typical split: 900 mm plinth + 1 200 mm fence.
- **Piers in masonry + infill panels** in timber, screen block, mesh or precast — the *opus africanum* idea; reduces wind load and cost per metre.
- **Precast panel wall + electric fence topping** — the standard southern African security assembly.
- **Gabion base + timber or steel screen above.**
- **Hedge in front of a mesh fence** — the mesh does security, the hedge does appearance and dust.

## Comparative table — cost band, lifespan, maintenance

Cost bands are **relative indices** (1 = cheapest permanent option), not prices. Absolute rates must be obtained by quotation; see file `10`. `needs-verification` on all absolute costs.

| Type | Relative cost band | Design life | Maintenance cycle | Main failure mode |
|---|---|---|---|---|
| Diamond mesh on steel posts | 1,0 | 10–20 yr | Re-tension 3–5 yr | Cutting; post corrosion at ground line |
| Timber slat / pole fence | 1,2–1,8 | 5–15 yr untreated, 15–25 treated | Re-treat 3–5 yr | Termite and rot at ground line |
| Precast panel-and-post | 1,5–2,5 | 20–40 yr | Repaint/repoint 5–10 yr | Post footing rotation; panel impact |
| Concrete block, plastered | 2,5–4,0 | 40–60 yr | Repaint 5–8 yr; repoint 15–20 yr | Cracking at movement joints; base overturning |
| Face brick masonry | 3,5–6,0 | 60–100 yr | Repoint 25–40 yr | Efflorescence; coping failure |
| Steel palisade | 3,0–5,0 | 15–30 yr | Repaint 5–7 yr | Corrosion at welds and ground line |
| Welded mesh (anti-climb) | 4,0–6,5 | 25–40 yr | Inspect annually | Coating breach then corrosion |
| Gabion | 3,0–5,0 | 50–60 yr (PVC-coated) | Inspect 5 yr | Wire abrasion; undermining |
| Segmental retaining block | 3,5–6,0 | 50+ yr | Clear drains annually | Drainage blockage; global slip |
| Rammed earth | 4,0–8,0 | Centuries if capped | Re-limewash 5–10 yr | Base erosion; rain on unprotected top |
| Hedge | 0,5 + time | Indefinite | Annual | Neglect |

## Sources

- [SANS 10400-K:2011 — Part K: Walls](https://archive.org/download/za.sans.10400.k.2011/za.sans.10400.k.2011.html) — SABS, via Internet Archive
- [Quantities for ordering building materials](https://concretesocietysa.org.za/wp-content/uploads/leaflets/Quantities-for-ordering-building-materials-2024.pdf) — Cement & Concrete SA
- [Gabion](https://en.wikipedia.org/wiki/Gabion) — Wikipedia
- [Mechanically stabilized earth](https://en.wikipedia.org/wiki/Mechanically_stabilized_earth) — Wikipedia
- [Rammed earth](https://en.wikipedia.org/wiki/Rammed_earth) — Wikipedia
- [Dry stone](https://en.wikipedia.org/wiki/Dry_stone) — Wikipedia
- [Cobogó](https://en.wikipedia.org/wiki/Cobog%C3%B3) — Wikipedia
- [Corobrik Geolok earth retainers](https://www.corobrik.co.za/geolok-earth-retainers) — Corobrik
- [Corobrik breezeblock](https://www.corobrik.co.za/breezeblock) — Corobrik
- [Technicrete Enviro Wall](https://www.technicrete.co.za/products/enviro-wall/) — Technicrete (ISG)
- [Technicrete Florawall](https://www.technicrete.co.za/products/florawall/) — Technicrete (ISG)
- [Dominus Estate](https://en.wikipedia.org/wiki/Dominus_Estate) — Wikipedia

## Open questions

- Crib-wall proportioning rules (depth ÷ height, batter) are given from general practice, not from a manufacturer's manual. `needs-verification`
- 358 anti-climb mesh aperture and wire dimensions need confirmation from a manufacturer datasheet. `needs-verification`
- All relative cost indices are judgement, not quotations; replace with local quotes per file `10`. `needs-verification`
- Precast panel thicknesses (~50–75 mm) and standard panel heights vary by manufacturer and were not confirmed from a published datasheet in this pass. `needs-verification`
