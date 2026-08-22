---
name: uefn
description: Build for Fortnite/UEFN through TEE - digest-grounded Verse, Scene-Graph-first world building, budget-conformant Blender exports, and honest automation boundaries. Use when asked to make a Fortnite island, write Verse, export assets to UEFN, or plan for UE6.
version: 1.0
license: MIT
---

# UEFN

You build for a platform whose API surface CHANGES monthly and whose
editor is the only compiler. TEE's lanes keep you honest: the digest is
the API truth, the budget tables are the import truth, and what you
cannot automate you say out loud.

Hard rules:
- The digest decides what exists. Load it (`uefn_digest_load`) from the
  user's install before writing any Verse; lint EVERY snippet
  (`uefn_lint`) before it goes anywhere near a compile. A lint finding
  is stale/hallucinated API — fix it, don't argue with it.
- Digests are Epic-copyrighted and per-install: never paste digest text
  into files, commits, or replies. Facts about it (names, effects) are
  fine; the text is not.
- Positions are UE XYZ everywhere in TEE; the LUF translation happens
  once, server-side (`uefn_coords` if you must inspect it). Never
  hand-convert.
- Never promise publish/cook/memory automation: those are human-gated
  (Creator Portal, IARC, moderation). Say so when asked.
- Scene Graph entities are the FUTURE (the UE6 object model); Creative
  devices are the parallel legacy family. Prefer entity/component
  vocabulary for new work; wrap devices when the gameplay needs them.

## Workflows

**Write Verse:**
1. `uefn_status` — know your mode (offline / gated / live).
2. `uefn_digest_load` from the install; on a version bump,
   `uefn_digest_diff` first — drift facts tell you what broke
   (the 23.20 / 30.00 / 42.00 precedents).
3. Start from `uefn_template` when one fits (digest-validated by
   construction); otherwise write, then `uefn_lint`.
4. Live editor: compile via `uefn_compile`; map terse errors with
   `uefn_error` (know the stale-validation false-positive class).

**Ship a Blender asset:**
1. Describe the asset and run `export_preflight` — fix every violation
   (the fixes are exact: decimate targets, power-of-two sizes, UCX
   names, bake-first for procedural materials).
2. `export_for_uefn(ids=…)` — LOD1/2 autogenerate at −50% steps, FBX
   comes out cm-scaled with Face smoothing.
3. Pack utility maps with `uefn_pack_channels` (Spec=R/Metal=G/Rough=B).
4. Remember the island ceiling: 100k memory units per area — budget
   before beauty.

**Build a world:** `uefn_entity_batch` for Scene Graph
(create_entity/set_transform/add_component), `uefn_devices` +
`uefn_place_device` for the device layer. The device catalog is a local
index — search it, never ask for a dump.

**Measure:** `uefn_analytics(island=…)` — public Data API, minutes
played and per-player, no auth. Engagement payouts follow these curves;
only ever-paying players count since Nov 2025.

## Judgment

Device vs Verse vs Scene Graph: devices for standard mechanics (fast,
tested, memory-cheap), Verse for logic between them, Scene Graph
components for anything you want to survive the UE6 convergence.
Genre reality from the design tables applies here too: islands are
single-genre by rule; discovery favors sustained engagement over spikes.
Verse idioms worth internalizing: failure is control flow (`if` binds
and decides), `<transacts>` is the default effect, structured
concurrency (`sync`/`race`/`rush`/`branch`) over ad-hoc spawns, and
persistable types are permanent schemas — version them from day one.
