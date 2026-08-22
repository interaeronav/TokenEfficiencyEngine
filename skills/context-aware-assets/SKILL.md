---
name: context-aware-assets
description: Furnish and dress a TEE-managed scene with free, license-safe assets that fit the site's real dimensions, style, and sunlight. Use when asked to furnish rooms, dress a scene, find/place assets, or match materials and lighting to site photos and briefs.
version: 1.0
license: MIT
---

# Context-aware assets

You are furnishing a scene whose facts TEE already knows: plan dimensions,
GPS datum, site-photo palette, and the client's spoken brief. Never guess
what these tools can tell you, and never pull raw catalogs into context —
state WHAT you need and let the server rank, gate, and validate.

Hard rules (they are enforced server-side; work with them, not around):
- Licenses are gated fail-closed. If an import answers `license_blocked`,
  pick another hit — there is no override and you must not ask for one.
- Uniform scaling only; doors/windows/appliances/sanitary/seating/humans
  never stretch. A `reject` from the scale policy means the asset is
  wrong, not the policy.
- Code-severity placement rules (door swings, egress widths, toilet
  clearances) never relax. Guideline rules relax only via an explicit
  `relax: ["rule_id"]` on the plan item, which is recorded.
- Text before pixels: verify geometrically (`as_verify`); render at most
  ONE budgeted image per task, only when the report says
  `render_warranted`.

## The 7-step checklist

Follow in order; each step names its exact tool.

1. **Brief** — `as_style_brief()` for the palette (named colors), style
   terms, and avoid-list. `tee_recall()` for project conventions. Note the
   GPS datum and region (US/EU rules) from the extract facts
   (`ex_search("gps")`).
2. **Search** — one `as_search(query=…, asset_class=…, max_tris=…,
   match_style=true)` per furniture class you need. State target
   dimensions from the plan (e.g. the plan's 0.9 m door opening) — do not
   browse. ≤5 rows come back; pick by dims first, tags second. If two
   candidates tie, `as_sheet`/`tee_media` is the tie-breaker, not the
   default.
3. **Fit** — decide target_dims per asset from plan facts (openings,
   wall lengths). Reference: `reference/dimensions.md` for the class
   envelopes you may aim inside.
4. **Plan** — write ONE relational placement plan for the whole room:
   `[{name, class, dims, anchor: "<wall-id>", offset}, …]` (~10
   tokens/object). Anchor wall-backed classes (sofa, bed, wardrobe) to
   walls; leave circulation to the validator.
5. **Validate** — `as_place(plan=…, room=…, region=…)` WITHOUT apply
   first. Fix every violation by editing the plan (the `fix` field says
   how); relax a guideline rule only with a reason you state in your
   reply.
6. **Apply** — imports first (`as_import` with `target_dims` and
   `location` from the solved plan), then `as_place(apply=true)` with the
   entity ids. Then materials: `as_material(id, query)` for measured PBR
   (lane 0) or `as_photo_material` when the surface exists in site
   photos. Sun last: `as_sun(lat, lon, when, apply=true)`.
7. **Verify** — `as_verify(room=…, match_style=true)`. Fix violations and
   re-verify. Only if clean AND a visual question remains, ONE
   `tee_capture(max_kb=32)`. Finish with `as_credits()` so attribution
   ships with the project.

## Judgment room

Selection within a shortlist, grouping (a reading corner vs scattered
chairs), and style calls are yours — the tables bound dimensions and
clearances, not taste. When the brief's avoid-list conflicts with a
search hit (e.g. "no marble"), drop the hit even if it ranks first.

## References (one level deep)

- `reference/dimensions.md` — class envelopes + fit-to-plan targets
- `reference/style-matching.md` — palette/ΔE00 ranking, avoid-lists
- `reference/lighting.md` — sun facts, HDRI bands, world rotation
- `reference/sources-licenses.md` — backend license/ToS matrix
- `evals/scenarios.md` — the three acceptance scenarios for this skill
