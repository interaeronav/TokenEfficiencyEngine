---
id: joinery.joints
title: Joint catalogue and techniques
domain: 06_joinery_and_woodwork
tags: [joints, mortise-and-tenon, dovetail, dowel, biscuit, domino, lamello, housing, dado, mitre, scarf, frame-and-panel, drawer-construction, tolerances]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Wood joint strength testing", url: "https://woodgears.ca/joint_strength/", publisher: "Woodgears.ca (Matthias Wandel)", accessed: 2026-08-25}
  - {title: "P-System brochure", url: "https://lamello.com/fileadmin/Downloads/Broschueren/P-System/PDF/P-System_Broschuere_EN.pdf", publisher: "Lamello AG", accessed: 2026-08-25}
  - {title: "Lamello original biscuits", url: "https://www.csaw.com/lamello/lamello-system/original-biscuits/", publisher: "Colonial Saw", accessed: 2026-08-25}
  - {title: "DOMINO Joiner DF 700 EQ-Set", url: "https://www.festoolusa.com/products/domino-joining-system/domino-joining-machines/576431---df-700-eq-set-us", publisher: "Festool USA", accessed: 2026-08-25}
  - {title: "Festool DOMINO — tenon dimension and mortise width options", url: "http://web.hypersurf.com/~charlie2/DOMINO/DOMINO_TenonsMortiseWidth.html", publisher: "hypersurf.com", accessed: 2026-08-25}
  - {title: "Confirmat screw assembly", url: "https://woodweb.com/knowledge_base/Confirmat_screw_assembly.html", publisher: "WOODWEB", accessed: 2026-08-25}
related: [joinery.wood_science, joinery.machinery, joinery.cabinetmaking, joinery.finishes]
unit_system: SI
---

# Joint catalogue and techniques

**Summary.** A joint is chosen for four reasons in this order: the load path, the material, the shop's capability, and the time available. Long-grain-to-long-grain glue joints are stronger than the wood; every other joint exists to create mechanical interlock or to convert an end-grain glue surface into a long-grain one. Comparative testing (Wandel) on spruce rails gives mortise-and-tenon **~172 lb (~78 kg)** average failure load, three-dowel joints **~135 lb (~61 kg)**, pocket screws **~122 lb (~55 kg)** and plain end-grain screws **~85 lb (~39 kg)**; in maple the same order holds at roughly double the values. Tolerances matter more than joint type: a sloppy mortise and tenon is weaker than a well-fitted dowel joint.

## Key facts

| Joint | Relative strength | Typical use | Working tolerance |
|---|---|---|---|
| Glued long-grain edge joint | stronger than the wood | panel glue-ups | gap ≤0.1 mm, no light through |
| Mortise and tenon | reference (100 %) | frames, doors, tables, chairs | tenon 0.05–0.1 mm press fit |
| Loose tenon (Domino) | ~85–100 % of integral M&T | frames, carcasses, mitres | one mortise tight, one wide |
| Dowel (3 × Ø8 mm) | ~75–80 % | carcass, frames, KD furniture | ±0.1 mm on hole position |
| Biscuit #20 | alignment + modest strength | panel alignment, carcass | ±0.5 mm lateral float by design |
| Pocket screw | ~70 % but deflects early | face frames, jigs, site fixes | n/a |
| Confirmat 7 × 50 | high pull-out in PB | melamine carcasses | Ø5 + Ø7 pilot, exact |
| Through dovetail | very high in tension | drawers, boxes | 0.1 mm; fit off the saw |
| Housing/dado, glued | moderate; excellent in shear | shelves, carcass divisions | ±0.1 mm on width |

## 1. Butt joints

The baseline. **Edge butt** (long grain to long grain, glued) is stronger than the surrounding wood and needs no reinforcement — a well-jointed, well-clamped edge joint in dry timber will break in the wood, not the glue line. **End butt** (end grain to long grain) is worth almost nothing: end grain absorbs glue into the vessel ends and starves the joint. Every "reinforced butt joint" in the catalogue below exists to fix that.

In panel-board carcasses, the butt joint plus a mechanical fastener (confirmat, dowel, Lamello) *is* the standard construction. Board has no grain direction, so the objection above does not apply in the same way — but board edge is weak and friable, so the fastener is doing all the work.

## 2. Dowels

Two or more Ø6, Ø8 or Ø10 mm fluted dowels, glued into drilled holes. Still the dominant industrial carcass joint because a line-boring machine or CNC produces the holes in the same operation as the system holes.

- **Rule of proportion:** dowel diameter ≈ ⅓ to ½ material thickness; embedment ≈ 2.5–3 × diameter in each member. For 18 mm board: Ø8 mm × 30 mm long, 12–14 mm into the edge, 15 mm into the face.
- **Spacing:** first dowel 32–50 mm from each end, then at 96 or 128 mm centres (multiples of 32 keep them on the system grid).
- **Fluted, not smooth.** Flutes vent hydraulic pressure and carry glue; a smooth dowel in a tight hole will split the board.
- **Failure mode is hole position, not dowel strength.** Use a dowelling jig referenced off the *same* face on both parts, or a CNC. Cumulative error over five dowels in a 600 mm carcass will make the joint impossible to close.
- **Choose when:** repeatable production, knock-down not required, glued assembly, board or solid.

## 3. Biscuits

Compressed beech ovals in an arc-shaped slot cut by a 100 mm blade. Sizes: **#0 = 47 × 15 × 4 mm, #10 = 53 × 19 × 4 mm, #20 = 56 × 23 × 4 mm, H-9 = 38 × 12 × 3 mm**.

- The slot is deliberately longer than the biscuit, giving ~±2 mm of lateral adjustment. Biscuits **align**; they add only modest strength.
- The biscuit swells on contact with water-based glue, which is what locks it — so it must be glued, and stored dry. A damp biscuit that has already swollen will not fit.
- **Choose when:** aligning panel glue-ups, registering carcass parts, mitre alignment, quick shop fixtures. **Do not choose when:** the joint carries racking load in a frame.

## 4. Loose tenon — Festool Domino and Lamello P-System

**Domino DF 500:** cutters Ø5, 6, 8, 10 mm; tenons 30, 40 and 50 mm long in matching thicknesses. Three mortise-width presets give bit-centre-to-centre travel of **13, 19 and 23 mm** — add the cutter diameter for the finished slot width. Practice is: cut the first mortise of each pair on the narrow setting (tight) and its partner on a wider setting (float), so cumulative error absorbs.

**Domino DF 700 XL:** cutters Ø8, 10, 12, 14 mm, routing depth **10–50 mm**, tenons up to ~140 mm long. This is door, gate and heavy-frame territory.

**Lamello P-System** (Zeta P2 machine) cuts a T-shaped, **form-locking** groove rather than a plain slot, which is what allows knock-down connectors to anchor mechanically:

| Connector | Size (mm) | Groove depth | Min. material thickness | Strength |
|---|---|---|---|---|
| Clamex P-14 | 64 × 27 × 9.7 | 14 mm | 18 mm butt / 15 mm mitre | up to 1210 N (MDF), 1070 N (PB), 1870 N (beech) |
| Clamex P-10 | 52 × 19 × 9.7 | 10 mm | 12 mm butt / 15 mm mitre | up to 700 N (MDF), 540 N (PB), 900 N (beech) |
| Tenso P-14 | 66 × 27 × 9.7 | 14 mm | 15 mm butt / 18 mm mitre | self-clamping ~15 kg (30 lb) |
| Bisco P-14 | 65 × 27 × 7 | 7 mm | — | alignment only, ±2 mm float |
| Divario P-18 | — | 18 mm | 12 mm butt / 18 mm shelf | up to 600 N; limits 740 N (MDF), 590 N (PB), 1820 N (beech) |

Clamex requires a **Ø6 mm access hole** for the hex key. Tenso self-clamps and holds the assembly for a maximum ~30-minute glue set — it replaces clamps, not glue.

**Choose loose tenon when:** you want mortise-and-tenon behaviour without cutting integral tenons; mitred carcasses; site-assembled or knock-down work (Clamex); glue-ups where clamping is impossible (Tenso).

## 5. Mortise and tenon and its variants

The reference frame joint. Proportions:

- **Tenon thickness** ≈ ⅓ of stock thickness, rounded to the nearest chisel/cutter size. In 22 mm stock use a 7 or 8 mm tenon.
- **Tenon width** ≤ 5–6 × its thickness; wider tenons must be **twin tenons** with a central haunch, or they will shrink and loosen.
- **Length:** through, or ⅔–¾ of the stile width for a stopped tenon.
- **Shoulders do the work in compression**; the cheeks do the work in glue. Perfect shoulders matter more than perfect cheeks.

**Variants:** *haunched* (haunch fills the panel groove at a corner and resists twist); *through wedged* (kerfed tenon, wedges driven from outside, self-tightening); *draw-bored* (peg hole offset 1–1.5 mm toward the shoulder so the peg pulls the joint closed — no clamps needed); *bare-faced* (one shoulder, where rail is thinner than stile); *twin/double* (wide rails, thick stock); *loose/floating* (see §4); *slot mortise or bridle* (open-ended, easy on a table saw, visible end grain).

**Cutting methods:** hollow-chisel mortiser (needs 0.4–0.8 mm bit-to-chisel clearance); slot mortiser or horizontal borer (round-ended — pair with a round-edged tenon); router and jig; or mortise chisel by hand. Tenons: table saw with dado or tenoning jig, bandsaw plus shoulder plane, spindle moulder with tenoning block, or tenon saw.

## 6. Dovetails

Mechanically interlocked against tension in one direction. Used where a joint must not pull apart: drawer fronts, box corners, carcass corners.

- **Through dovetail** — visible both faces; boxes, carcasses, drawer backs.
- **Half-blind (lapped)** — hidden from the front; the correct drawer-front joint, since the front resists handle pull purely through the dovetail.
- **Secret mitred (full-blind)** — invisible; plinths and mitred carcasses.
- **Sliding dovetail** — a tapered dovetail housing; shelves into carcass sides, breadboard ends.

**Angles:** 1:8 for hardwood, 1:6 for softwood (i.e. ~7° and ~9.5°). **Pin spacing** is an aesthetic decision, not a structural one, above a minimum of ~2 pins on a 100 mm board. Cut tails first or pins first — be consistent; the second member is marked from the first, so absolute accuracy is only needed once.

**Machine dovetails:** through and half-blind jigs (Leigh, Porter-Cable) produce uniform, strong joints fast; CNC and dedicated dovetailers do the same in production. Machine dovetails are *stronger* than most hand dovetails because the fit is uniform.

## 7. Finger (box/comb) joints

Square interlocking fingers. Enormous glue area, easy to machine on a table saw with a dado stack and a sled or on a spindle moulder with a finger-joint block. Weaker in tension than dovetails (nothing mechanically resists pull-apart) but stronger in racking and much faster to cut. Use for utility boxes, drawer boxes in plywood, and jigs.

**Structural finger-jointing** (long shallow end-to-end fingers) is what makes finger-jointed pine: sound for painted joinery, but the joints telegraph through a clear finish.

## 8. Rebates (rabbets), housings (dados) and grooves

- **Rebate:** an L-section along an edge. Cabinet backs, glazing rebates, door rebates, shiplap. Cut on a table saw (two passes), spindle moulder with a rebate block, or router.
- **Housing/dado:** a square channel across the grain. The standard shelf-into-side joint. **Through housing** runs edge to edge; **stopped housing** stops short of the front edge so it does not show. **Dovetailed housing** resists pull-out.
- **Groove:** a channel with the grain — panel grooves in frame-and-panel, drawer bottom grooves.
- **Tolerance:** the shelf must be a firm push fit. Board thickness varies: nominal 18 mm melamine is often 17.8–18.2 mm, so use an undersized dado cutter plus a second pass, or an adjustable groover, rather than an "18 mm" cutter.
- **Depth:** one-third of the material thickness is the usual rule; 6 mm into 18 mm board.

## 9. Mitres, keys and splines

Mitres hide end grain but glue end-grain to end-grain and are therefore weak. Reinforce with **splines** (a cross-grain solid tongue beats a long-grain one), **keys/feathers** (kerfs sawn across the assembled corner, filled with contrasting slips), **biscuits or Dominos** set back from the show face, **Lamello Clamex P-14** for large mitred panels (15 mm minimum material), or a **lock mitre** cutter — self-aligning with a large glue area, but fussy to set and only worth it for runs.

**Setting-out rule:** a 45° mitre on a 90° corner is only correct if the corner is 90°. On site, measure the actual angle and bisect it.

## 10. Scarf joints

For lengthening timber. A plain **slope scarf** at 1:8 to 1:12 gives adequate glue area for non-structural mouldings and skirtings; on site a **45° splayed scarf** on skirting and cornice hides shrinkage far better than a butt. Structural scarfs (tabled, bolted, keyed) belong to carpentry; for joinery lengthening, prefer a finger joint or a loose-tenon butt.

## 11. Frame-and-panel construction

The oldest solution to wood movement: a stable frame of narrow members (which barely move in length) capturing a wide panel that is free to move in a groove.

- Groove depth **8 mm minimum**, 10–12 mm for panels over 400 mm wide.
- Panel width = opening width + 2 × groove depth − movement allowance. Calculate the allowance from `01_wood-science.md`; in dry inland southern Africa a 400 mm solid panel needs ~1.5–3 mm total free play depending on species and cut.
- **Never glue the panel.** Centre it with space balls or two small dabs of silicone at the mid-point of the top and bottom rails.
- **Finish the panel before assembly**, or an unfinished line will appear when it shrinks.
- **Cope-and-stick** (a matched pair of spindle/router cutters producing a moulded stile edge and a matching coped rail end) is the production version; it is a stub tenon and is weaker than a true M&T, so use it for cabinet doors, not for entrance doors.
- MDF or veneered-board panels can be glued in — they do not move — which is why painted "shaker" doors are usually MDF panels in solid or MDF frames.

## 12. Drawer construction methods

Ranked by cost and by quality:

1. **Metal drawer box systems** (Blum LEGRABOX/TANDEMBOX, Hettich InnoTech Atira/AvanTech YOU, Grass Nova Pro Scala) — the sides *are* the runners. Default for kitchen work; see `07_hardware-systems.md`.
2. **Board box with dowels or confirmats** — 16 mm melamine sides, 12 mm grooved-in bottom, side-mounted or undermount runners. The commodity solution.
3. **Plywood box, finger-jointed or Domino'd** — 12–15 mm birch ply sides, 6 mm ply bottom in a groove 10–12 mm up. The workshop default for quality work.
4. **Solid-timber box** — half-blind dovetailed front, through-dovetailed back, 12–16 mm sides, 6 mm solid bottom in a groove with a slot-screwed rear fixing.

**Common rules regardless of method:**
- Drawer bottom grain runs **side to side**, so the bottom expands front-to-back where the slot can absorb it.
- The back is set above the bottom groove so the bottom can slide out to the rear.
- Drawer sides against undermount runners must be square and parallel to within ~0.5 mm over their length or the runner will bind.
- For hand-fitted (runner-less) drawers, the classic fit is a 0.3–0.5 mm reveal all round with the sides waxed, and the drawer must be fitted after finishing, in the season it will live in.

## 13. Choosing a joint — decision order

1. **What is the load?** Tension → dovetail or wedged tenon. Racking → M&T or loose tenon. Shear → housing or dowel. Alignment only → biscuit or Bisco P.
2. **What is the material?** Board → mechanical fastener or P-System. Solid timber → glue-based joinery. Veneered board → nothing that breaks the face.
3. **Must it come apart?** Yes → Clamex, cam-and-dowel, knock-down fittings. No → glue.
4. **What does the shop own, and how many are needed?** A joint you cannot cut accurately is weaker than a simpler joint you can; one-off favours hand or router jig, fifty favours dedicated tooling or CNC.

## Sources

- [Wood joint strength testing](https://woodgears.ca/joint_strength/) — Woodgears.ca
- [Lamello P-System brochure](https://lamello.com/fileadmin/Downloads/Broschueren/P-System/PDF/P-System_Broschuere_EN.pdf) — Lamello AG
- [Lamello original biscuits](https://www.csaw.com/lamello/lamello-system/original-biscuits/) — Colonial Saw
- [DOMINO Joiner DF 700 EQ-Set](https://www.festoolusa.com/products/domino-joining-system/domino-joining-machines/576431---df-700-eq-set-us) — Festool USA
- [Festool DOMINO tenon dimension and mortise width options](http://web.hypersurf.com/~charlie2/DOMINO/DOMINO_TenonsMortiseWidth.html)
- [Confirmat screw assembly](https://woodweb.com/knowledge_base/Confirmat_screw_assembly.html) — WOODWEB

## Open questions

- The Wandel joint-strength tests are a single well-documented amateur test series, not a standards-based programme; treat the ordering as reliable and the absolute values as indicative.
- Published comparative strength data for Domino loose tenons versus integral mortise and tenon is contested; no peer-reviewed source was located.
- Dovetail slope conventions (1:6 / 1:8) are traditional practice rather than a sourced standard.
