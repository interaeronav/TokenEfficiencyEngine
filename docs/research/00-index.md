# TEE Research Corpus — Index & Architecture Decision Record

*Produced by a deep-research pass on 2026-08-21 (11 parallel research agents,
primary sources: official Epic/Blender/Anthropic docs, project repos, issue
trackers). These digests ground the build plan in `CLAUDE_EXECUTION_SCRIPT.md`.
Facts are version-stamped; where an installed version differs, verify
empirically and record it in `docs/PROGRESS.md`.*

## Corpus

| Doc | Covers |
|---|---|
| [01-unreal-automation-surfaces.md](01-unreal-automation-surfaces.md) | UE5 Python Editor Scripting, remote execution channel, Remote Control HTTP/WS, commandlets, Blueprint reachability, Verse/UEFN, Live Coding |
| [02-blender-automation-surfaces.md](02-blender-automation-surfaces.md) | bpy architecture (`bpy.data` vs `bpy.ops`), main-thread rules, headless/bpy-wheel modes, extensions platform, geometry nodes, OSL/GLSL, physics |
| [03-existing-mcp-bridges.md](03-existing-mcp-bridges.md) | blender-mcp, unreal-mcp family, Maya/Houdini/Unity MCPs, failure modes from issue trackers, second-generation typed-tool designs |
| [04-token-efficiency-techniques.md](04-token-efficiency-techniques.md) | Quantified token costs & mitigations: tool-definition budgets, Tool Search Tool, PTC, code-execution-with-MCP, prompt caching, context editing, image token math, scene-graph representations |
| [05-user-friction-points.md](05-user-friction-points.md) | Catalogued user complaints (version drift, token burn, setup pain, no rollback/persistence) + mitigation per point |
| [06-studio-pipeline-techniques.md](06-studio-pipeline-techniques.md) | Professional patterns: persistent daemons, Remote Control presets, Datasmith/Omniverse deltas, Flamenco/Shaman content addressing, job compilers, USD/glTF |
| [07-epic-official-unreal-mcp.md](07-epic-official-unreal-mcp.md) | Epic's UE 5.8 `ModelContextProtocol` plugin: 830 tools/52 toolsets behind 3 meta-tools, BlueprintTools graph DSL, extension APIs, measured payload costs, setup facts |
| [08-mcp-client-compatibility.md](08-mcp-client-compatibility.md) | What Claude Code/Desktop/Cursor/API connector actually honor: list_changed, resource_link, outputSchema hazards, image paths, defer_loading/PTC, lint rules |
| [09-blender-change-detection-rollback.md](09-blender-change-detection-rollback.md) | msgbus vs depsgraph handlers, `session_uid` keying, undo-push invariants (#77557), background undo (#60934), snapshot rollback |
| [10-blender-version-baseline.md](10-blender-version-baseline.md) | Blender 5.x baseline decision, 4.5→5.2 breaking-change fault lines, bpy wheel matrix, official Blender Lab MCP internals & wire protocol |
| [11-drawing-cad-extraction.md](11-drawing-cad-extraction.md) | Deterministic drawing/CAD extraction: pdfplumber, ezdxf DIMENSION ground truth, ifcopenshell, raster/OCR fallback, scale-inference ladder, license traps (PyMuPDF AGPL, CubiCasa NC) |
| [12-photo-satellite-pipeline.md](12-photo-satellite-pipeline.md) | Local photo/satellite preprocessing: EXIF/GPS, phash dedupe, token-budget-first crops & contact sheets, web-mercator math, footprint datasets & licenses |
| [13-video-pipeline.md](13-video-pipeline.md) | Zero-token video pipeline: PySceneDetect keyframes, sharpness/dedupe, imageio-ffmpeg, faster-whisper, DJI SRT telemetry, sparse-only pycolmap SfM boundary |
| [14-claude-vision-extraction.md](14-claude-vision-extraction.md) | Claude vision mechanics: patch token formula & caps, image caching, PDF handling, coordinate grounding limits, measured VLM accuracy bands, structured-output extraction |
| [15-extraction-prior-art.md](15-extraction-prior-art.md) | Prior art: docling/unstructured/marker, media MCPs, FML v3 schema precedent, Bonsai/IFC Blender handoff, content-addressed cache patterns |
| [16-extraction-channels.md](16-extraction-channels.md) | VLM extraction channels: MCP sampling post-mortem, in-band vs API-key drivers, elicitation limits, honest cost framing |
| [17-sheets-heights-roof-schema.md](17-sheets-heights-roof-schema.md) | Sheet classification (NCS metadata-first), elevation/section Z-extraction, FML height/roof schema extension before freeze |
| [18-frames-and-registration.md](18-frames-and-registration.md) | Frame registry, transforms-as-facts, site ENU hub, tier ladder, footprint-fit registration, conformance tolerance math (USIBD LOA) |
| [19-context-economics.md](19-context-economics.md) | Phase 8 grounding: app-side script lane (PTC pattern), tool-result eviction economics, columnar encodings, caption-once, the BM25 negative result |

## Architecture decisions (ADR)

Settled by this corpus; change only with a new entry in `docs/DECISIONS.md`.

- **A1 — Server:** Python 3.11+, official `mcp` SDK, stdio primary transport.
  *Why:* every surveyed bridge that works uses it; matches Claude Code/Desktop
  expectations; Streamable HTTP optional later. (03, 08)
- **A2 — Blender baseline:** 5.1 minimum, 5.2 LTS primary, 4.5 LTS optional
  legacy tier, never 4.2 (EOL July 2026). *Why:* official add-on requires
  5.1; 5.2 is current LTS to July 2028; the 5.0/5.1/5.2 breaking-change
  clusters make older support a shim-tier concern. (10)
- **A3 — Blender transport:** act as a client of the official Blender Lab
  add-on socket (`localhost:9876`, null-delimited JSON execute protocol);
  ship a same-protocol TEE fallback add-on. *Why:* zero-install for official
  users; the official server has no extension point, but its add-on socket is
  multi-client by design. (10, 09)
- **A4 — Unreal primary:** proxy + extend Epic's official UE 5.8 MCP
  (`127.0.0.1:8000/mcp`); register TEE toolsets via the documented Python
  extension API; **no custom C++ Blueprint plugin.** *Why:* 830-tool official
  surface incl. full Blueprint K2 graph DSL makes a from-scratch bridge
  redundant; the measured token sinks (describe_toolset 74–127K chars,
  unpaginated lists) are exactly what a proxy fixes. (07)
- **A5 — Unreal fallback:** Remote Control (30010/30020) + Python remote
  execution (UDP 239.0.0.1:6766 / TCP 6776) for 5.3–5.7; commandlets for
  headless. *Why:* pluginless, documented, used by existing bridges. (01, 06)
- **A6 — Client compat floor:** no `outputSchema`; self-sufficient
  `structuredContent`; inline base64 images only (no `resource_link`); plain
  object `inputSchema`s; ≤ 40 tools, ≤ 2 KB descriptions; progressive
  disclosure via TEE meta-tools, not protocol notifications. *Why:* verified
  client-by-client failure modes, several silent. (08)
- **A7 — Security floor:** localhost binds; gated + AST-screened +
  auto-checkpointed code-exec tools; never expose DCC sockets off-machine.
  *Why:* none of the DCC-side sockets have auth; official docs say VM
  isolation is the mitigation. (10, 03)
- **A8 — Extraction license floor:** deterministic-first extraction stack
  (pdfplumber, pypdfium2, ezdxf, ifcopenshell-as-dependency, OpenCV,
  pytesseract/RapidOCR, Pillow, ImageHash, PySceneDetect, imageio-ffmpeg,
  faster-whisper; shapely/pyproj/pymap3d/rasterio for registration); CI
  lint bans PyMuPDF (AGPL), marker, ultralytics/FastSAM, CubiCasa5K and
  DeepFloorplan weights; ffmpeg/exiftool subprocess-only. Speaker
  diarization (pyannote.audio) is optional-only: MIT code but HF-gated
  models needing a user token — degrade to non-diarized, never require. *Why:* the
  floor-plan ML landscape is a licensing minefield and everything needed is
  achievable with permissive tools. (11, 12, 13, 15)
- **A9 — Extraction channel:** in-band host-model extraction is the default
  (prepared tiles + `ex_store_facts` writeback); server-side API-key driver
  optional as async jobs; MCP sampling ruled out (deprecated 2026-07-28,
  unimplemented in Claude Code/Desktop). *Why:* verified client reality;
  channel-agnostic Extractor keeps the tool surface identical. (16)
- **A10 — Fact model:** content-addressed facts keyed (media_hash,
  extractor_id, extractor_version); FML v3-derived plan schema extended
  with per-level heights + parametric roof before freeze; frame_id on every
  geometric fact; transforms as first-class facts in a single-parent tree
  anchored at site ENU; tier precedence (dimension text > drawing geometry
  > SfM > GPS prior > satellite/footprint); conflict facts ARE the
  conformance report; EPSG:3857 fetch-only. *Why:* the AEC
  written-dimensions-govern rule, REP-105/GeoPose precedent, and scan-to-BIM
  tolerance practice all converge on this shape. (17, 18, 15)

- **A11 — Script lane:** chatty tool loops run app-side as one
  `tee_script` call: an AST-whitelisted mini-Python executor over the SAME
  typed virtual tools (call/batch/facts helpers), auto-checkpointed and
  atomic, hard-bounded (calls/nodes/wall-clock), returning only the final
  result. *Why:* programmatic tool calling is the API-native shape for this
  but excludes MCP tools; simulated 86% context cut on the conformance fix
  loop and −61% session cost with eviction. Adds no capability beyond the
  typed tools, so it is not code-exec-gated. (19)
- **A12 — Context-economics floor:** adaptive columnar encoding in the
  budgeter (list-of-dicts ≥ 20 rows, ≥ 60% shared keys → cols/rows, marked);
  eviction-safe response contract + `tee_status(recap=true)` one-call
  resume (≤ 500 tokens); caption-once media pass (`kind: "caption"` facts
  gate re-attachment). Fact search stays substring-count: BM25 was
  simulated and regressed (9/10 → 7/10 at 611 facts). (19)

## Headline numbers worth remembering

- Tool definitions can eat 20–40% of a 200K context (~710 tokens/tool);
  deferred loading cuts definition tokens ~85%; code-execution-with-MCP
  measured up to 98.7% total reduction. (04)
- A 1920×1080 screenshot ≈ 2,691 tokens; a budgeted ~1024×576 JPEG ≈ 777;
  geometric text assertions cost a few dozen. (04)
- Raw scene dumps stop scaling around ~120 objects; a real user burned 60% of
  a $200/mo plan in 2 hours on one donut scene without these mitigations. (04, 05)
