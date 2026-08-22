# 22 — Prior art: agent asset workflows (2026-08-22)

Source-level reading of the integrations + live API measurements.

## The field

- **Official Blender Lab MCP has NO asset tools** (27 tools; docs search;
  execute-code-as-last-resort; budgets responses incl. JSON envelope).
  Closest project to TEE's dogma — and it deliberately leaves the asset
  space open.
- **ahujasid/blender-mcp** (community; the PolyHaven/Sketchfab/Rodin/
  Hunyuan integration) — measured pathologies:
  - PolyHaven "search" fetches the ENTIRE catalog per call (524 KB models,
    2.34 MB all types), no cache, truncates to the alphabetically-first
    20; model sees ~540 tokens with tags/dimensions/polycount DROPPED.
  - Sketchfab search: 86 KB raw for 20 results → ~745 tokens; per-UID
    inline previews ~400-550 vision tokens each.
  - Model-driven polling loops for Rodin/Hunyuan generation (a poll per
    tool round-trip over multi-minute jobs).
  - A verbatim `user_prompt` echo parameter on EVERY tool (telemetry paid
    in model tokens); 4 per-provider status round-trips before any work;
    ~1.4k-token strategy prompt mandating before/after screenshots;
    25-tool schema ≈ 4-6k tokens. "Find and place one asset" ≈ 2-5k
    tokens before schemas.
  - Bug classes: unframed socket JSON (parse-per-chunk, timeout-as-EOF
    #219/#256); silent rotation no-op (quaternion mode vs rotation_euler
    #56); duplicate PBR node wiring (#190); zip-slip + path traversal in
    the asset download path (#257/#306, patched).
- **BlenderKit add-on** (GPL v2 — concepts only): resident client DAEMON
  owns search/thumb-cache/downloads off-thread, shared across instances;
  faceted `term:value` query grammar, page_size=15, `dict_parameters=1`
  "to make results smaller"; quality-score ordering; `asset_in_scene()`
  reuse check before any network; per-resolution variants with later swap;
  license as a first-class search facet.
- Other MCPs: **Meshy official = the polling pattern to copy** (wait=true
  server-side auto-poll, 5→30 s backoff, 300 s cap, one call returns the
  finished result; upfront credit-cost tables; confirm-before-paid-call
  rule). Tripo MCP = the anti-pattern (boilerplate re-sent every poll).
  gregkop/sketchfab omits license from search results. Poly.Pizza Unity
  MCP is the ONLY surveyed integration that auto-writes CC-BY attribution
  files. Fab/UE: no public API — local-cache-import story only.

## Selection literature

- **Holodeck (CVPR 2024)** is the pattern: LLM emits {description, target
  dimensions, constraints}; an embedding retriever (CLIP visual + SBERT
  text + bbox size match) selects OUTSIDE the LLM context — near-zero
  tokens per selection; 59.8% human preference.
- Embedding-only retrieval degrades over large noisy catalogs
  (arXiv:2403.09675) → re-rank; SceneSmith documents residual VLM failure
  modes (semantically-close-but-wrong, orientation errors, small-render
  misperception).
- Contact-sheet grids convey scale/orientation to VLMs; tiles below
  ~200-300 px effective resolution get unreliable. No rigorous published
  eval of VLM thumbnail-sheet asset selection found.

## Distilled: mistakes to avoid / ideas to steal

Avoid: catalog-fetch-per-query; search-without-search; per-provider status
chatter; prompt-echo params; model-driven polling; per-candidate inline
previews (or URL-only "previews" the model cannot see); unframed sockets;
reporting from cache without scene read-back; license-as-decoration;
non-idempotent PBR wiring; trusting remote paths/archives; tool-count
explosion; making the model guess physical size when the catalog has
dimensions.

Steal: daemon-owned bulk I/O with the model seeing only summaries;
reuse-before-download; faceted grammar + small pages + quality ordering;
Meshy wait-mode + cost confirmation; Holodeck-shaped selection with one
≥256 px-tile contact sheet as tie-breaker; compact per-result rows
(name/id/license/tris/dims); import reports as diffs; attribution files
written at import time; PolyHaven as the keyless friction-free default.
