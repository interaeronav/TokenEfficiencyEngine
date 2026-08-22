# Decision log

Amendments to the settled architecture (A1–A7 in
`docs/research/00-index.md`) or to `CLAUDE_EXECUTION_SCRIPT.md` are recorded
here before being implemented: date, decision, rationale, what it supersedes.

## 2026-08-22 — Phase 9 (TEE Assets) researched; decisions A13–A15

A six-agent deep-research pass (docs/research/20–25) grounded the asset
management + creation module. Three new settled decisions in
`docs/research/00-index.md`:

- **A13 — asset backends & license hygiene:** tier-1 = Poly Haven /
  ambientCG / Poly Pizza / Smithsonian (Sketchfab guarded; Fab
  human-only); server-side store owns catalogs/thumbnails/downloads;
  SPDX allowlist failing closed on NC/ND/unknown; attribution manifests
  with license snapshots travel with the cache.
- **A14 — creation lanes & generation floor:** procedural (measured
  values, Infinigen) → local diffusion (Z-Image/klein/SDXL + Marigold) →
  photo-derived PBR → generated 3D (TRELLIS.2 local, Tripo/Meshy hosted
  behind one wait-polling adapter with cost confirmation); mandatory
  cleanup macro; gated lanes labeled; honest bar stated ("set dressing
  on demand, hero assets curated").
- **A15 — selection & context contract:** Holodeck-shaped server-side
  retrieval with ≤5-row shortlists; relational placement plans validated
  against cited clearance/code rules; four-band scale-envelope policy;
  GPS-true sun; render-free verification, one budgeted render max;
  shipped as the `context-aware-assets` skill.

Load-bearing evidence: the official Blender Lab MCP has no asset tools
(space open); the popular community integration measurably re-fetches a
2.3 MB catalog per search and truncates alphabetically; TRELLIS.2's MIT
release (Dec 2025) makes a clean local 3D lane possible; MobileCLIP's
MIT repo hides research-only weights; Sketchfab changed owners again
(KitBash, 2026-08-10) — platform risk is a design input.

## 2026-08-22 — Phase 8 (context economics) added; decisions A11–A12

A research + simulation pass (docs/research/19) measured where the
remaining per-session spend lives after Phase 7. Two new settled decisions
in `docs/research/00-index.md`:

- **A11 — script lane:** `tee_script` runs bounded, AST-whitelisted
  mini-Python over the existing typed virtual tools, atomic under one
  auto-checkpoint, returning only the final result — the app-side
  equivalent of programmatic tool calling (which excludes MCP tools).
  Simulated: −86% context on the conformance fix loop; −61% session cost
  combined with tool-result eviction.
- **A12 — context-economics floor:** adaptive columnar responses (≥ 20
  homogeneous rows), eviction-safe contract + `tee_status(recap=true)`,
  caption-once media facts. Explicit non-decision: fact search stays
  substring-count — a simulated BM25 swap regressed relevance (9/10 →
  7/10 at 611 facts); recorded so it is not "improved" later without new
  evidence.

## 2026-08-22 — Phase 7 (TEE Extract) added; decisions A8–A10

A deep-research pass (9 agents, docs/research/11–18) grounded the media
extraction module. Three new settled decisions recorded in
`docs/research/00-index.md`:

- **A8 — extraction license floor:** deterministic-first stack (pdfplumber,
  pypdfium2, ezdxf, ifcopenshell-as-dependency, OpenCV headless,
  pytesseract/RapidOCR, Pillow, exifread, ImageHash, PySceneDetect,
  imageio-ffmpeg, faster-whisper, optional pycolmap/MobileSAM; shapely,
  pyproj, pymap3d, rasterio for registration). Hard bans enforced by CI
  lint: PyMuPDF (AGPL), marker, ultralytics/FastSAM, CubiCasa5K and
  DeepFloorplan weights, Depth Anything Base/Large. ffmpeg/exiftool via
  subprocess only. Audio is a first-class modality: Claude has no audio
  input, so local transcription (faster-whisper) is the only channel;
  pyannote diarization is optional (MIT code, HF-gated models requiring a
  user token) and degrades silently to non-diarized transcription.
- **A9 — extraction channel:** MCP sampling is dead (deprecated in the MCP
  2026-07-28 spec, unimplemented in Claude Code/Desktop) — the default VLM
  extraction driver is in-band (host model + `ex_store_facts` writeback);
  an opt-in server-side API-key driver (messages.parse + Batches + Files
  API) runs as async jobs. One Extractor interface, two drivers.
- **A10 — fact model:** content-addressed fact store keyed
  (media_hash, extractor_id, extractor_version); FML v3-derived plan schema
  extended with per-level heights and a parametric roof before freeze;
  every geometric fact carries a frame_id; transforms are first-class facts
  in a single-parent tree anchored at site ENU; tier precedence with
  written-dimensions-govern; conflict facts are the conformance report.

## 2026-08-21 — Build on MCP Python SDK 2.0 (`MCPServer` API)

The research corpus and decision A1 referenced the 1.x SDK's `FastMCP` class.
The current SDK on PyPI is `mcp` 2.0, which renames it to
`mcp.server.mcpserver.MCPServer` (same decorator style), adds an explicit
`structured_output=False` switch (a direct implementation of A6's
no-outputSchema rule), and ships an in-memory `Client(server)` used by the
test suite. Substance of A1 unchanged: official SDK, stdio primary. Pinned
`mcp>=2.0,<3`.
