# Decision log

Amendments to the settled architecture (A1–A7 in
`docs/research/00-index.md`) or to `CLAUDE_EXECUTION_SCRIPT.md` are recorded
here before being implemented: date, decision, rationale, what it supersedes.

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
