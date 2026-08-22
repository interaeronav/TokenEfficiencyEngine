# 41 — Blender trajectory 5.3 → 6.0 (2026-08-22)

## Timeline

4.5 LTS dies Jul 2027; 5.2 LTS is the primary target to Jul 2028; 5.3
is in alpha now, ships Nov 2026; 6.0 ships Nov 2027 (LTS status
UNVERIFIED). The 5.0 file-format break remains the deepest firewall
line (4.5 ↔ 5.x). bpy wheels are healthy on PyPI (cp313 for 5.1+,
cp311 for 4.x, win_arm64 added) — per-shim-row real-bpy smoke tests
are pip-installable.

## 5.3 landed content (alpha, verify at beta)

- `wm.undo_stack` read-only access — cheap what-changed bracketing for
  TEE diffs (watch-lane).
- **`bpy.data.all_ids` iteration order changed and is documented
  internal** — never derive stable IDs from iteration order. TEE
  already keys `session_uid` (A-series decision); add a shuffle
  regression test.
- Asset system: **access-token auth for remote libraries + `@b5_3`
  per-version asset replacement naming** — the listing schema grows
  version windows, so the Phase 9 listing generator must emit
  per-version entries and carry min/max compatibility.
- **Vulkan becomes the default backend on Windows/Linux** — headless
  CI needs drivers; probe and fall back via `--gpu-backend opengl`.
- Project system (`.blender_project` roots); Python stays 3.13. Jolt
  v5.6 requested as a bundled lib + a Jolt Solver node PR is WIP (5.3
  shipping UNVERIFIED).

## 6.0 removal list (milestone 37)

**`use_nodes` removal for Scene/World/Material is a HARD TARGET
(#140111)** — ban `use_nodes` writes in TEE codegen NOW (harmless on
≥5.0, fatal on 6.0). Also: VSE strip time props, asset-prefs API
moves, Spline→Curve renames (#102607), indexed BHeads (asset listing
gets faster). No OpenGL-removal date announced; the 6.0 Python
version is unannounced.

## Physics arc — Phase 11's bet validated

Legacy Bullet rigid-body / cloth / Mantaflow / particles have **no
deprecation signals anywhere** (absent from the 6.0 milestone; devs:
"long way to go before replacing the legacy particle system"). Risk
horizon is 6.0+ at the earliest. The churn is on the NEW side: XPBD
asset names/sockets/bundle schemas may shift 5.2→5.3
(self-collision/sewing still missing); Jolt is "mainly for rigid
bodies"; solvers combine via substepping in one loop. Phase 11 ops
declare `backend: legacy | gn_physics` so the swap is a config, not a
rewrite.

## Asset arc — Phase 9's path is the stable one

Remote Asset Libraries are being extended, not replaced —
`asset_listing generate` remains the stable official path. Asset
libraries as EXTENSIONS are actively built (`blender_manifest`
`[asset_library]` section; commercial libraries proposed). No
write/upload support (publish = generate + copy); an asset-system
Python API is "planned".

## Strategic overlap

**Blender Lab's first 2026 experiment is an MCP server for Blender**
(natural-language input via the Python API) — direct overlap with
TEE's niche and the likely future first-party surface to interop with
or benchmark against (implementation UNVERIFIED). Same posture as
Epic's MCP: proxy/extend when real, never compete on transport.

## Risk register distilled to shims

Single `set_gn_input()` chokepoint (never raw dict access) tested
against bpy 4.5/5.2 wheels; a central enum-translation table with
`bl_rna` pre-flight (the FAST→FLOAT class of silent renames);
session_uid-only IDs + shuffle test; Vulkan backend probe; the asset
listing JSON treated as a versioned artifact; float32 mathutils (5.0)
→ 1e-5 tolerances and never hashing float bytes; context-logging
(`temp_override().logging_set`) in the adapter error path to
auto-generate exact-fix messages.
