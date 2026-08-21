# Blender Version Baseline & 5.x Breaking Changes

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Research question

What is the correct Blender version baseline for TEE given Blender 5.x is current: the concrete 4.5→5.0/5.1 breaking changes affecting the bridge (official release notes list ID-property access removal e.g. `scene['cycles']`, GreasePencil→Annotation datablock renames, full BGL removal, plus any extensions-manifest or socket/node API changes), the Python version and availability/pinning of pip `bpy` wheels for 5.0/5.1 (4.2–4.5 wheels are `==3.11.*`), and whether the official Blender Lab MCP extension (5.1+, read-only) exposes an extension point TEE can register write tools into versus running as a separate add-on alongside it?

Every Blender finding in the digest targets 4.2–4.5 while the official Blender MCP requires 5.1+ — TEE must pick a minimum supported version before Phase 1. The answer sets the contents of the version-aware compatibility shim (the top defense against the most-documented friction point, LLM API drift), the Python interpreter pinning for the out-of-process batch backend, the `blender_manifest` packaging targets, and whether the Blender adapter is architected as a standalone bridge or as a write-capable companion to the official inspection-first extension.

## Summary

Blender's current line as of Aug 2026 is 5.2 LTS (released July 14, 2026, supported to July 2028), with 4.5 LTS supported to July 2027 and 4.2 LTS now EOL (final 4.2.23, July 2026), so a 4.2-based digest baseline is already unsupported.

The bridge-breaking changes cluster in 5.0 (removal of dict-like ID-property access such as `scene['cycles']`, full BGL removal, GreasePencil-to-Annotation RNA renames, `scene.node_tree` removal, legacy Action API removal, compositor-node type replacements), in 5.1 (Python 3.11 to 3.13 jump per VFX Platform 2026, user-site-packages no longer loaded by default), and in 5.2 LTS (geometry-nodes modifier inputs move from `modifier["Socket_x"]` ID-properties to real RNA at `modifier.properties.inputs.<id>.value`). pip `bpy` wheels are pinned `==3.11.*` (cp311) for 4.2.x–5.0.x and `==3.13.*` (cp313) for 5.1.0+, so an out-of-process batch backend spanning both sides of 5.1 needs two interpreters.

The official Blender Lab MCP ([projects.blender.org/lab/blender_mcp](https://projects.blender.org/lab/blender_mcp), add-on manifest `blender_version_min=5.1.0`) is not strictly read-only — it ships `execute_blender_code` plus ~25 inspection-first tools — and offers no third-party tool-registration extension point (tools are pkgutil-discovered only inside its own `blmcp.tools` package); however, its add-on runs a multi-client TCP bridge (`localhost:9876`, null-delimited JSON `{"type":"execute","code":...}`) that executes arbitrary Python, so TEE can attach as a second client of the official add-on or ship as a separate add-on/extension alongside it. The extensions manifest schema is still 1.0.0 (unchanged since 4.2), so packaging differences across versions are limited to `blender_version_min` and bundled-wheel Python tags.

## Findings

### Current Blender version landscape (Aug 2026)

Published releases per official compatibility index: 5.0 (Nov 2025), 5.1 (Mar 2026), 5.2 LTS (July 2026 – July 2028). Upcoming: 5.3 Nov 2026 (alpha now), 6.0 Nov 2027. LTS page: "Blender 5.2 LTS Released July 14, 2026, supported until July 2028"; 4.5 LTS still maintained (last 4.5.12 on 2026-07-21, supported July 2025 – July 2027); 4.2 LTS moved to "Previous LTS Releases" = EOL (last update 4.2.23, July 2026). So 5.2 is simultaneously the current stable AND an LTS.

Source: [https://developer.blender.org/docs/release_notes/compatibility/](https://developer.blender.org/docs/release_notes/compatibility/) and [https://www.blender.org/download/lts/](https://www.blender.org/download/lts/)

### 5.0 breaking: dict-like ID-property access removed

Properties defined via `bpy.props` are no longer stored in the same container as user Custom Properties; Python dict-like access to them is removed. `bpy.context.scene['cycles']` no longer returns Cycles settings (must use `scene.cycles`). New `READ_ONLY` options flag; new `get_transform`/`set_transform` accessors; set-without-get is now an error; `obj.bl_system_properties_get()` is the escape hatch for reading old system IDProperties. Blendfiles from <=4.5 get their IDProperties DUPLICATED into system storage on load (perf/side-effect caveat; cleanup tooling deferred to 5.1).

Source: [https://developer.blender.org/docs/release_notes/5.0/python_api/](https://developer.blender.org/docs/release_notes/5.0/python_api/)

### 5.0 breaking: BGL fully removed

"Remove deprecated BGL API" (commit `decd88f67e`). Also removed: `Image.bindcode` (use `gpu.texture.from_image` + `gpu.types.GPUTexture`), creating shaders directly from GLSL source files (`11063b5b90`). Textures drawn in Python draw handlers may need `draw_texture_2d(is_scene_linear_with_rec709_srgb_target=True)` or `IMAGE_SCENE_LINEAR_TO_REC709_SRGB` shader. Any legacy add-on code importing `bgl` hard-fails on 5.0+.

Source: [https://developer.blender.org/docs/release_notes/5.0/python_api/](https://developer.blender.org/docs/release_notes/5.0/python_api/)

### 5.0 breaking: GreasePencil → Annotation renames

Annotation RNA renames: `bpy.types.GPencilStroke`→`AnnotationStroke`, `GPencilStrokePoint`→`AnnotationStrokePoint`, `GPencilFrame(s)`→`AnnotationFrame(s)`, `GPencilLayer(s)`→`AnnotationLayer(s)`, `bpy.types.GreasePencil`→`bpy.types.Annotation`, `BlendDataGreasePencils`→`BlendDataAnnotations`. Property renames: `Scene.grease_pencil`→`Scene.annotation` (same for `MovieClip`, `NodeTree`, `SpaceImageEditor`, `SpaceSequenceEditor`, `MovieTrackingTrack`); release notes print `bpy.data.grease_pencils -> bpy.types.annotations` (likely `bpy.data.annotations` intended). Simultaneously, GPv3 types drop their suffix: `bpy.types.GreasePencilv3` → `bpy.types.GreasePencil` and `bpy.data.grease_pencils_v3` → `bpy.data.grease_pencils`. So `bpy.data.grease_pencils` EXISTS in both 4.x and 5.x but refers to DIFFERENT data (annotations in 4.x, GPv3 in 5.0+) — a silent-semantics trap for LLM-generated code.

Source: [https://developer.blender.org/docs/release_notes/5.0/python_api/](https://developer.blender.org/docs/release_notes/5.0/python_api/)

### 5.0 breaking: compositor/node API

`scene.node_tree` removed → use `scene.compositing_node_group` (create via `bpy.data.node_groups.new(name, 'CompositorNodeTree')`). `scene.use_nodes`, `material.use_nodes`, `world.use_nodes` deprecated no-ops (always True; removal slated for 6.0) — materials/worlds now get default node trees at creation. Many compositor nodes replaced by ShaderNode counterparts (e.g. `CompositorNodeGamma` → `ShaderNodeGamma`). `CompositorNodeOutputFile`: `file_slots`/`layer_slots`/`base_path` removed → `directory`, `file_name`, `file_output_items`. Compositing Color node output socket renamed `'RGBA'` → `'Color'`. Deprecated compositor + combine/separate nodes and Point Density texture node removed. Node tree interface items now lookupable by identifier (`6f2988f0af`).

Source: [https://developer.blender.org/docs/release_notes/5.0/python_api/](https://developer.blender.org/docs/release_notes/5.0/python_api/)

### 5.0 breaking: other API changes relevant to a code-executing bridge

EEVEE engine identifier changed `BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE` (`4fe75da973`) — inverse of the 4.2 rename, classic LLM drift trap. Legacy Action API removed (`action.fcurves`/`action.groups`/`action.id_root` → slot/channelbag API via `bpy_extras.anim_utils`). Brush enum props renamed `*_tool` → `*_brush_type` (`brush.sculpt_tool` → `brush.sculpt_brush_type`). `unified_paint_settings` moved under mode-specific `Paint` struct. `bpy.types.AssetHandle` removed → `AssetRepresentation`. `mathutils` types gained buffer protocol; `Vector` now float32-backed (was float64). `ImageFormatSettings` requires `media_type` set before `file_format`. Render passes renamed (`'Z'` → `'Depth'`, `'DiffCol'` → `'Diffuse Color'`). VSE gains separate `context.sequencer_scene`. Bundled modules made private: `rna_info`, `rna_xml`, `console_python`, `bl_console_utils` etc. Logging output format changed (parsers of background render progress break). Data-block name max length 63 → 255 bytes; 5.0 blendfiles only open in >=4.5; Collada I/O removed; big-endian and Intel-Mac builds dropped.

Source: [https://developer.blender.org/docs/release_notes/5.0/python_api/](https://developer.blender.org/docs/release_notes/5.0/python_api/) and [https://developer.blender.org/docs/release_notes/compatibility/](https://developer.blender.org/docs/release_notes/compatibility/)

### 5.1 changes

Python upgraded 3.11 → 3.13 (VFX Reference Platform 2026; also OpenColorIO 2.5, OpenEXR 3.4, OpenVDB 13.0, C++17→C++20). Python user-site-directory NO LONGER loaded by default ("preventing user-installed modules from overriding Blender's bundled modules"; restore with `--python-use-user-env`, commit `9d302ccb0a`) — breaks add-ons relying on `pip --user` installs; extensions must bundle wheels. `sculpt.sample_color` operator removed (merged into `paint.sample_color`). Brush stroke booleans (`use_airbrush`/`use_anchor`/`use_space`/`use_line`/`use_curve`/`use_restore_mesh`) folded into enum `brush.stroke_method`. VSE strip time properties renamed (`frame_final_start` → `left_handle` etc.; old names deprecated, removal in 6.0). Node Tools gained a globally-unique idname requirement. New: `bpy.app.cachedir`, `bpy.app.handlers` `exit_pre`.

Source: [https://developer.blender.org/docs/release_notes/5.1/python_api/](https://developer.blender.org/docs/release_notes/5.1/python_api/) and [https://developer.blender.org/docs/release_notes/5.1/core/](https://developer.blender.org/docs/release_notes/5.1/core/)

### 5.2 LTS breaking: geometry-nodes modifier inputs become real RNA

Landed in 5.2 LTS (commit `1561c1ea4a`), not 5.1: "The modifier now has proper RNA properties rather than using custom properties". Before: `modifier["identifier"]=5.0`, `modifier["identifier_use_attribute"]=True`, `modifier["identifier_attribute_name"]=...` After: `modifier.properties.inputs.identifier.value=5.0`, `.type="ATTRIBUTE"`, `.attribute_name=...`, and `modifier.properties.outputs.identifier.attribute_name=...` Compatibility index: "will break all RNA paths to these properties" (e.g. `object.modifiers["geonode_mod"]["socket_1"][1]` → `object.modifiers["geonode_mod"].socket_1.y`). Also 5.2: Compare and Random Value node socket identifiers changed (`3a5cd7862b`); `gpu.init()` added to init GPU backend in `--background` mode (`a6f60f8657`); annotation stroke/point editing functions added (`frame.strokes.new`, `stroke.points.add`/`remove`); node panels open/close from Python; `bpy.data.all_ids` iterator; IDProperties nesting capped at 1024 levels; sculpt automasking props moved to `MeshAutomaskingSettings`.

Source: [https://developer.blender.org/docs/release_notes/5.2/python_api/](https://developer.blender.org/docs/release_notes/5.2/python_api/) and [https://developer.blender.org/docs/release_notes/compatibility/](https://developer.blender.org/docs/release_notes/compatibility/)

### bpy PyPI wheel matrix (verified from PyPI JSON, Aug 2026)

`requires_python` pins per release: 4.2.0–4.2.23 `==3.11.*` (cp311); 4.3.0, 4.4.0 `==3.11.*`; 4.5.0–4.5.12 `==3.11.*` (cp311; 4.5.12 uploaded 2026-07-21); 5.0.0 (2025-11-18) and 5.0.1 (2025-12-16) STILL `==3.11.*` (cp311); 5.1.0 (2026-03-17), 5.1.1, 5.1.2 `==3.13.*` (cp313); 5.2.0 (2026-07-14) `==3.13.*` (cp313, latest). The 3.11→3.13 interpreter break is exactly at 5.0→5.1. No 3.12 wheels ever existed. LTS corrective wheels keep shipping monthly for 4.5.x; the 4.2.x stream ended July 2026.

Source: [https://pypi.org/pypi/bpy/json](https://pypi.org/pypi/bpy/json)

### Official Blender Lab MCP: identity and requirements

Official page [blender.org/lab/mcp-server/](https://www.blender.org/lab/mcp-server/); source at [https://projects.blender.org/lab/blender_mcp](https://projects.blender.org/lab/blender_mcp) (GPL-3.0-or-later, "2026 Blender Authors", maintainer "Blender Lab"). Requires Blender 5.1 or newer. Two components over a TCP socket: a Blender add-on extension (`addon/blender_mcp_addon`, distributed from repository lab.blender.org, download URL carries `blender_version_min=5.1.0`, v1.0.0) and an out-of-process MCP server pip package `blender-mcp` (`mcp/blmcp`, entry point `blender-mcp`, `requires-python >=3.10`, deps: `mcp[cli]>=1.2.0`, `pyyaml`, `docutils`; FastMCP; stdio transport plus optional streamable-HTTP on `127.0.0.1:8000` for llama.cpp web UI; also distributed as an `.mcpb` MCP Bundle on the releases page). Data flow: MCP Client ←stdio→ `blender-mcp` ←TCP→ Blender add-on. Official security warning: "The MCP server will execute LLM generated code in Blender without any guards".

Source: [https://www.blender.org/lab/mcp-server/](https://www.blender.org/lab/mcp-server/) and [https://projects.blender.org/lab/blender_mcp](https://projects.blender.org/lab/blender_mcp)

### Official Blender Lab MCP: NOT read-only; tool inventory

Tool list (auto-generated `readme_tools.rst`): `execute_blender_code` and `execute_blender_code_for_cli` (arbitrary Python in interactive or background Blender) plus inspection-first tools: `get_blendfile_summary_{datablocks,missing_files,of_linked_libraries,path_info,usage_guess}` (each with `_for_cli` background variant), `get_objects_summary`, `get_object_detail_summary`, `get_python_api_docs`, `search_api_docs`, `search_manual_docs` (full-text over bundled RST API reference and manual excerpts in `mcp/blmcp/data/`), `get_screenshot_of_{area,window}_as_image`, `get_screenshot_of_window_as_json`, `jump_to_tab_*`, `jump_to_view3d_*`, `render_thumbnail_to_path`, `render_viewport_to_path`. So the "read-only" framing is wrong: it is inspection-first but includes unrestricted code execution. A `weak_sandbox` module blocks only `sys.exit` and a tiny `bpy.ops` denylist (`wm.quit_blender`, `wm.read_factory_settings`) and is explicitly documented as "not really a sandbox".

Source: [https://projects.blender.org/lab/blender_mcp/raw/branch/main/readme_tools.rst](https://projects.blender.org/lab/blender_mcp/raw/branch/main/readme_tools.rst) and `.../addon/blender_mcp_addon/weak_sandbox.py`

### Official Blender Lab MCP: no formal tool-registration extension point

`blmcp/__init__.py` `main()`: tools are auto-discovered via `pkgutil.iter_modules(blmcp.tools.__path__)`, importing `blmcp.tools.<modname>` and calling `mod.register(mcp)`; modules ending `_toolcode` or starting `_template_` are skipped; "they are never un-registered". `blmcp.tools` is a regular package (has `__init__.py`, not a namespace package), and there is no entry-point group, env var, or config for external tool directories — so third parties cannot register write tools into the official server without forking it or writing into its installed package dir. The design doc states "The project is deliberately small, maintainable, and does no more than necessary."

Source: [https://projects.blender.org/lab/blender_mcp/raw/branch/main/mcp/blmcp/__init__.py](https://projects.blender.org/lab/blender_mcp/raw/branch/main/mcp/blmcp/__init__.py)

### Official add-on TCP bridge is the de facto integration point

`addon/blender_mcp_addon/mcp_to_blender_server.py`: listens on `DEFAULT_HOST='localhost'`, `DEFAULT_PORT=9876` (configurable in preferences, port 1024–65535, optional auto-start), `_LISTEN_BACKLOG=5`, maintains `clients: list[_Client]` (multiple concurrent clients supported), 10s client timeout eviction. Protocol: null-byte-delimited JSON requests `{'type':'execute','code':'<python>','strict_json':bool}`; the add-on `exec()`s the code and returns JSON (the `strict_json=False` path uses `json.dumps(default=repr)` for LLM code). No authentication token. "All tools send code to the add-on to run" — every official MCP tool is just Python source shipped over this socket (the `*_toolcode.py` modules). Therefore TEE can drive Blender as a second client of the OFFICIAL add-on socket, sending its own toolcode, without modifying the official server. Background/headless mode: `blender --background file.blend --command blender_mcp [--host --port]` (`cli.py` registers the CLI command); background mode rejects deferred responses — requests must complete synchronously. Manifest declares `[permissions] network = 'Runs a local TCP socket server for MCP client communication'`.

Source: [https://projects.blender.org/lab/blender_mcp/raw/branch/main/addon/blender_mcp_addon/mcp_to_blender_server.py](https://projects.blender.org/lab/blender_mcp/raw/branch/main/addon/blender_mcp_addon/mcp_to_blender_server.py), `.../cli.py`, `.../blender_manifest.toml`

### Extensions manifest / packaging targets

The `blender_manifest.toml` schema is still `schema_version` 1.0.0 — the official schema-versions table lists exactly one row: version 1.0.0, "Blender Version Initial" 4.2.0, "Blender Version Final" "-" (i.e. no schema break through 5.2). The official MCP add-on's own manifest uses `schema_version='1.0.0'`, `blender_version_min='5.1.0'`, `type='add-on'`, `[permissions] network`. So one manifest schema serves 4.2–5.2; version gating is purely `blender_version_min`/`blender_version_max`. Caveat for bundled Python wheels in extensions: wheel ABI must match Blender's interpreter (cp311 for <=5.0, cp313 for >=5.1), and 5.1's removal of user-site loading means pip-into-user-site workarounds silently stop working.

Source: [https://developer.blender.org/docs/features/extensions/schema/](https://developer.blender.org/docs/features/extensions/schema/) and [https://projects.blender.org/lab/blender_mcp/raw/branch/main/addon/blender_mcp_addon/blender_manifest.toml](https://projects.blender.org/lab/blender_mcp/raw/branch/main/addon/blender_mcp_addon/blender_manifest.toml)

### Blendfile-level compatibility floor

5.0 changed the low-level blendfile format: files saved by 5.0+ can only be opened by Blender >=4.5 (older versions report them invalid). Data-block names lengthened 63 → 255 bytes with only partial 4.5 forward-compat (4.5 cannot link long-named datablocks from 5.x files). Blendfile compression on save is now default-on in 5.0. 5.1 Grease Pencil fills revamp auto-converts files; 5.1 Node Tools require open+resave for unique idnames; 5.2 Node Tools asset metadata requires open+resave again.

Source: [https://developer.blender.org/docs/release_notes/compatibility/](https://developer.blender.org/docs/release_notes/compatibility/)

## Recommendations for TEE

1. Set TEE's Blender baseline to 5.1 minimum / 5.2 LTS primary. Rationale: the official Blender Lab MCP add-on hard-requires 5.1.0 (`blender_version_min` in its manifest); 5.2 is BOTH current stable and an LTS supported to July 2028; 4.2 (the digest's floor) went EOL July 2026. Treat 4.5 LTS (supported to July 2027) as an optional legacy tier behind the compatibility shim only if user demand exists — never 4.2.
2. Architect the Blender adapter as a write-capable companion, not a fork: the official `blmcp` server has no tool-registration extension point (pkgutil scan of its own `blmcp.tools` package only), but its add-on's TCP bridge (`localhost:9876`, null-delimited JSON `{'type':'execute','code':...,'strict_json':...}`, multi-client, no auth) executes arbitrary Python. Ship TEE either as (a) a second MCP server process that is a client of the official add-on's socket — zero extra Blender-side install for users who already run the official extension — with TEE's own add-on as fallback when the official one is absent, or (b) contribute tools upstream (GPL-3.0-or-later applies to anything derived from their toolcode modules; keep TEE's server code independently licensed by speaking only the wire protocol).
3. Build the version-aware shim around these exact 5.x fault lines (highest LLM-drift risk first): (1) geometry-nodes modifier inputs: `modifier['Socket_2']=v` (<=5.1) vs `modifier.properties.inputs.<identifier>.value=v` (>=5.2); (2) `scene['cycles']`/dict-access to `bpy.props` storage removed in 5.0 → always emit attribute access (`scene.cycles.samples`); (3) EEVEE id flip `BLENDER_EEVEE_NEXT` (4.2–4.5) vs `BLENDER_EEVEE` (5.0+); (4) `scene.node_tree` (<=4.5) vs `scene.compositing_node_group` (5.0+), and `use_nodes` as no-op on 5.x; (5) `bpy.data.grease_pencils` semantic swap (annotations in 4.x vs GPv3 in 5.x) plus `GPencil*`→`Annotation*` type renames; (6) `bgl` import → hard error on 5.0+, route all drawing through `gpu`; (7) legacy Action API (`action.fcurves`) vs slot/channelbag API; (8) brush `.sculpt_tool` vs `.sculpt_brush_type`; (9) `CompositorNodeOutputFile` `file_slots`/`base_path` vs `directory`/`file_name`/`file_output_items`; (10) VSE strip time property renames in 5.1 (old names alive until 6.0 — normalize to new names now).
4. Pin the out-of-process `bpy` batch backend per target: Python 3.11 interpreter + `bpy==4.5.*` for any 4.5-LTS tier, Python 3.13 + `bpy==5.2.*` (or `5.1.*`) for the primary tier; there are no cp312 wheels and `requires_python` is exact (`==3.11.*` / `==3.13.*`), so a single-interpreter design cannot span the 5.0→5.1 boundary — use uv/venv-per-target or subprocess dispatch keyed by target version.
5. Package the TEE Blender add-on with `blender_manifest.toml` `schema_version='1.0.0'` (unchanged since 4.2 — no schema migration needed), `blender_version_min='5.1.0'` (or two builds: one 4.5-floor, one 5.1-floor), declare `[permissions] network` for the socket, and vendor all Python deps as wheels tagged cp313 (cp311 for a 4.5 build); do NOT rely on user site-packages — 5.1 stopped loading them by default (`--python-use-user-env` is the opt-in escape).
6. Steal the official server's token-efficiency patterns rather than reinventing: compact structured summaries (`get_objects_summary` / `get_blendfile_summary_*` return counts and hierarchies, not dumps), screenshot-as-JSON for UI state, bundled RST API/manual corpora with local full-text search (`search_api_docs`/`get_python_api_docs`) so the model looks up current-API signatures instead of hallucinating pre-5.0 ones, and the `*_toolcode` module split (server-side tool schema, Blender-side code payload) which keeps tool definitions small; add version-stamped API doc retrieval as TEE's primary anti-drift defense on top of the shim.
7. For headless/batch use, support both official-style `blender --background file.blend --command blender_mcp` (synchronous-only; no deferred responses in background mode) and direct `bpy`-wheel execution; on 5.2+ call `gpu.init()` when GPU features are needed in `--background`; mirror the `weak_sandbox` denylist (block `wm.quit_blender`, `wm.read_factory_settings`, `sys.exit`) since Blender itself ships no real sandbox and documents VM isolation as the mitigation.
8. Budget for the next breaks now: 6.0 (Nov 2027) will remove the deprecated no-op `use_nodes` properties and the deprecated VSE strip time names, and 5.3 lands Nov 2026 — keep the shim table keyed by `bpy.app.version` tuples and gate every emitted code template on it.
