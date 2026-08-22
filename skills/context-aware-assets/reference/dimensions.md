# Dimension envelopes and fit-to-plan targets

Authoritative data: `server/src/tee/assets/data/envelopes.json` (the scale
policy reads it directly). This file is the human view.

## Contents

- [How the four-band policy rules](#policy)
- [Envelope table](#table)
- [Fit-to-plan targets](#targets)

## Policy

`as_import` measures the asset (glTF meters, node scale composed) and
rules: **accept** (fits the class envelope) → **fix** (a power-of-ten or
inch factor explains it; applied + recorded as a `scale_fix` fact) →
**snap** (within ±10% of `target_dims`/typical; uniform) → **reject**
(one line, pick another asset). Non-uniform stretch exists only for
classes listing `stretch_axes` (bed x, table x/y, wardrobe x, …); rigid
classes (door, window, appliance, sanitary, seating, human, plant) never
stretch.

## Table

Meters, [width, depth, height] as placed. Sources: IRC R311.2 (egress
door), ADA 404, NKBA kitchen planning, Neufert Architects' Data 4e,
ISO 7250.

| class | min | typical | max | rigid |
|---|---|---|---|---|
| door | 0.71, 0.03, 1.98 | 0.86, 0.045, 2.03 | 0.97, 0.06, 2.44 | yes |
| window | 0.4, 0.04, 0.4 | 1.2, 0.08, 1.2 | 2.4, 0.12, 2.2 | yes |
| chair | 0.38, 0.38, 0.7 | 0.45, 0.5, 0.85 | 0.7, 0.7, 1.15 | yes |
| armchair | 0.65, 0.65, 0.6 | 0.85, 0.85, 0.95 | 1.15, 1.05, 1.15 | yes |
| sofa | 1.3, 0.75, 0.6 | 2.1, 0.9, 0.8 | 2.8, 1.1, 1.05 | yes |
| bed | 0.9, 1.9, 0.35 | 1.5, 2.0, 0.55 | 2.0, 2.2, 1.3 | x |
| table | 0.6, 0.6, 0.69 | 1.4, 0.9, 0.75 | 2.6, 1.2, 0.78 | x, y |
| desk | 0.9, 0.45, 0.69 | 1.4, 0.7, 0.74 | 2.0, 0.9, 0.78 | x |
| wardrobe | 0.5, 0.5, 1.7 | 1.2, 0.6, 2.0 | 2.6, 0.75, 2.5 | x |
| refrigerator | 0.55, 0.55, 1.2 | 0.75, 0.7, 1.75 | 1.0, 0.85, 2.0 | yes |
| stove | 0.5, 0.55, 0.8 | 0.76, 0.65, 0.91 | 0.95, 0.75, 1.0 | yes |
| toilet | 0.34, 0.6, 0.65 | 0.38, 0.7, 0.76 | 0.52, 0.8, 0.85 | yes |
| sink | 0.35, 0.3, 0.75 | 0.55, 0.45, 0.85 | 0.75, 0.65, 0.95 | yes |
| bathtub | 1.4, 0.7, 0.4 | 1.7, 0.75, 0.55 | 1.9, 0.9, 0.65 | yes |

(Plus: coffee_table, nightstand, bookshelf, kitchen_counter, lamp_floor,
rug, plant_potted, human — see the JSON.)

## Targets

- Door into a plan opening: `target_dims = [opening_w, 0, opening_h]`
  (0 = unconstrained thickness). The snap band tolerates ±10%; a door
  landing at 0.88 m in a 0.9 m opening is correct (operating clearance).
- Furniture against a wall segment: width ≤ 0.9 × segment length.
- Rug under a seating group: ≥ 0.4 m beyond the sofa footprint each side.
