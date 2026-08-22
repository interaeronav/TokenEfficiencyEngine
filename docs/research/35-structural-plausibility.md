# 35 — Structural & physical plausibility rules (2026-08-22)

## The framing (the legal deliverable)

Exposure lies in APPROVING or SIZING, never in FLAGGING against cited
prescriptive tables. The IRC is prescriptive by design — R301.1.3
requires engineered design only OUTSIDE its tables — so "modeled span
exceeds the prescriptive envelope of [table]; verify with a licensed
engineer" restates the code (what plans examiners do daily). Product
rules: findings only, never a green "passes" state (report "no
plausibility conflicts detected (N rules evaluated)"); never emit a
member size — emit the table row and the delta; every fact carries
source + edition + jurisdiction + severity. Autodesk ("tools… not a
substitute for professional judgment") and Solibri ("QA/coordination",
never compliance) are the framing precedents. Disclaimer pattern text
drafted in the research transcript for counsel review.

## Severity taxonomy for conflict facts

**CODE** (adopted prescriptive table, jurisdiction-tagged) / **STD**
(engineering-standard bound) / **HEUR** (published rule-of-thumb, wide
tolerance) / **CONV** (practice convention, informational). Model may
relax HEUR/CONV with a note, never CODE.

## Rule tables (cited; values in the module's reference files)

Joist spans per IRC R502.3.1 — use the WORST-CASE grade column as the
flag threshold (zero false positives for any legal build); ACI 318
slab h ≥ l/20-28, beams l/16-21, cantilevers l/8-10; steel depth ≈
span/20 (Ruddy/AISC; flag < span/30); headers REQUIRED over bearing-
wall openings (R602.7 — existence check, no sizing); lintel bearing
≥ 100/150/200 mm by span; EC6 masonry slenderness ≤ 27; US empirical
masonry 6"/8" minima; footing width ≥ wall and soil < 1500 psf ⇒
engineered (itself a flag); rafters R802.4.1 + the topology check
(rafters without ties or a structural ridge); roof pitch minima per
covering (asphalt 2:12; concrete tile ≥ 30°, plain tile 35° per BS
5534 — the killer Okongo check); stairs (riser ≤ 196 mm, tread ≥ 254,
2R+G 550-700 Blondel, headroom 2032, width ≥ 914); ceiling ≥ 2134 mm;
head + lintel + structure ≤ floor-to-floor (pure geometry); window
fall-protection sill rule; wet-wall stacking + drain-offset rules.

## The load-path graph check (code-anchored)

IRC R301.1 requires a "complete load path… to the foundation" — TEE
checks GRAPH REACHABILITY on modeled geometry: directed support graph
(footing → wall → beam → joist → rafter; edges = vertical projection
overlap + elevation adjacency), every bearing node must reach a
foundation node (LOAD_PATH_BROKEN), openings need header nodes,
cantilever > depth or > back-span/4 flags, stacking offset > joist
depth flags, point loads must land on posts that reach footings. All
Eastman Class 1-2 rules — automatable without analysis.

## Prior art & jurisdiction

Solibri runs NO span/load-path rules — TEE's layer has no commercial
equivalent. **IDS 1.0 (buildingSMART, June 2024) + ifcopenshell's
ifctester** (TEE already ships ifcopenshell) covers the
data-completeness tier out of the box; custom geometric rules emit
findings in the same conflict-fact shape. Region-parameterize like the
Phase 9 placement rules; **follow-up: SANS 10400 (South Africa,
deemed-to-satisfy) is the likely Okongo-relevant prescriptive path —
research before hard-coding jurisdiction defaults.**
