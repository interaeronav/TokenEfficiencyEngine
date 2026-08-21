# Studio Pipeline Techniques

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Summary

Professional UE/Blender automation converges on a small set of patterns directly relevant to a token-efficient AI bridge:

(1) persistent local daemons with lightweight JSON-over-TCP or WebSocket protocols (UE Remote Control on ports `30010`/`30020`, UE Python remote execution via UDP multicast `239.0.0.1:6766` discovery + TCP command channel, Quixel Bridge socket export, blender-mcp's addon on port `9876`);

(2) curated exposure surfaces instead of raw API access (UE Remote Control Presets expose only chosen properties/functions and push change events by subscription);

(3) delta/incremental sync instead of full re-export (Datasmith Direct Link incremental scene updates, Omniverse Nucleus delta-change tracking with sequence numbers, Flamenco Shaman SHA256-based dedup so clients upload only new/changed files);

(4) declarative job graphs compiled server-side (BuildGraph XML nodes/tasks, Flamenco JavaScript job compilers that expand a small job spec into many worker tasks) so the caller sends intent, not steps;

and (5) out-of-process RPC sessions to heavyweight engines (Houdini HAPI Thrift sessions over TCP/named-pipe/shared-memory to a HARS server process) that keep the DCC alive between calls.

Blender-side, all `bpy` calls must be marshalled onto the main thread via a queue drained by `bpy.app.timers`, and headless work uses `blender --background --python`. These map cleanly onto TEE: a persistent in-engine agent, a terse verb+params JSON protocol, content-addressed asset transfer, subscription-based state diffs, and high-level compiled "job types" as MCP tools.

## Findings

### UE Remote Control API (HTTP)

UE ships a web server inside the engine: a REST-like HTTP API on default port `30010` (configurable in Project Settings > Web Remote Control). Core routes like `PUT /remote/object/property` and `/remote/object/call` take JSON payloads with `objectPath` + `propertyName`/`functionName`; access mode (read/write) is set via an `access` parameter in the body. Supported UE 4.27 through 5.8.

Source: [dev.epicgames.com — Remote Control API HTTP reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine)

### UE Remote Control API (WebSocket)

WebSocket server on default port `30020` (`ws://127.0.0.1:30020`). Messages are JSON with `MessageName`, `Parameters`, and optional `Id` for deferred responses. Message types: `http` (proxies any HTTP route through the socket with `Url`/`Verb`/`Body`; the response carries `RequestId`/`ResponseCode`/`ResponseBody`), and `preset.register`/`preset.unregister` (subscribe to a named Remote Control Preset). Subscription events: `PresetFieldsChanged` (`PropertyLabel`, `ObjectPath`, `PropertyValue`), `PresetFieldsAdded` (`ExposedProperties`/`ExposedFunctions`), `PresetFieldsRemoved`, `PresetFieldsRenamed` (`OldFieldLabel` -> `NewFieldLabel`). No batching or compression documented. Presets are a curated allowlist surface: only explicitly exposed properties/functions are remotely visible — an access-control and payload-minimization pattern.

Source: [dev.epicgames.com — Remote Control API WebSocket reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine)

### UE Python remote execution protocol

The Python plugin's remote execution (`Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py`) uses UDP multicast discovery on group `239.0.0.1:6766` (magic `ue_py`, protocol version 1), PING/PONG every 1s with a 5s node timeout, then `OPEN_CONNECTION` to establish a dedicated TCP command channel. `COMMAND`/`COMMAND_RESULT` messages over TCP support three exec modes: `ExecuteFile`, `ExecuteStatement`, `EvaluateStatement`. `run_command()` returns `{success, command, result, output}`. Wrapped by `upyrc` (PyPI), nils-soderman/unreal-remote-execution (NodeJS), and radial-hks/MCP-Unreal-Server (an MCP server with auto multicast node discovery, attended/unattended modes).

Source: [github.com/nils-soderman/unreal-remote-execution](https://github.com/nils-soderman/unreal-remote-execution) ; [pypi.org/project/upyrc](https://pypi.org/project/upyrc/) ; [github.com/radial-hks/mcp-unreal-server](https://github.com/radial-hks/mcp-unreal-server) ; [tianc377.github.io — Remote Execution Between Unreal and DCC](https://tianc377.github.io/posts/RemoteExecutionBetweenUnrealandDCC/)

### UE headless automation (commandlets)

`UnrealEditor-Cmd.exe "proj.uproject" -run=pythonscript -script="c:\my_script.py"` runs Python headless with no editor UI (fast startup, no level auto-load, full `unreal` python module). `-ExecutePythonScript` is the alternative full-editor path. Epic explicitly warns against putting Python in `ExecCmds` since it runs before the editor environment/startup level is ready — a race-condition pattern an AI bridge must avoid.

Source: [dev.epicgames.com — Scripting the Unreal Editor using Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python) ; [xingyulei.com — UE command-line Python](https://www.xingyulei.com/post/ue-commandline-python/index.html)

### UE headless rendering (Movie Render Queue)

MRQ command-line render: `UnrealEditor-Cmd.exe project.uproject Map_P -game -MoviePipelineConfig="/Game/.../BigTestQueue.BigTestQueue" -windowed -resx=1280 -resy=720 -log -notexturestreaming`. Custom render-farm control is done by subclassing a Python executor and passing `-MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor` — i.e., render jobs are asset-referenced presets plus a pluggable executor, not long CLI arg lists. Open-source prototype render farm using this: leixingyu/unrealRenderFarm.

Source: [dev.epicgames.com — Command-line rendering with Movie Render Queue](https://dev.epicgames.com/documentation/unreal-engine/using-command-line-rendering-with-move-render-queue-in-unreal-engine) ; [github.com/leixingyu/unrealRenderFarm](https://github.com/leixingyu/unrealRenderFarm)

### BuildGraph / UAT / Horde CI

BuildGraph is Epic's XML-scripted build automation: a graph of user-defined nodes with dependencies, each node a sequence of tasks; invoked via `RunUAT` (`Engine/Build/BatchFiles`); integrates UnrealBuildTool, AutomationTool, and the Editor. Epic uses it internally for UE and Fortnite builds. Horde (shipped with UE5) runs BuildGraph as a first-class citizen with distributed/parallel execution and automatic tracking + transfer of intermediate build artifacts between agents; other Horde services: remote execution/compute offload (including C++ compilation via UBA), CI for large Perforce repos, test automation (Gauntlet), device farm management, and editor telemetry analytics. Pattern: a declarative graph submitted once, expanded and scheduled server-side.

Source: [dev.epicgames.com — BuildGraph](https://dev.epicgames.com/documentation/en-us/unreal-engine/buildgraph) ; [dev.epicgames.com — Horde in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/horde-in-unreal-engine)

### Houdini Engine (HAPI) session architecture

HAPI supports in-process sessions (Houdini libs loaded into the host process) and out-of-process Thrift RPC sessions: the client `libHARC` connects to a HARS console server process that links `libHAPI`. Three transports: TCP socket (`HAPI_CreateThriftSocketSession`), named pipe / Unix domain socket (`HAPI_CreateThriftNamedPipeSession`), and shared memory (`HAPI_CreateThriftSharedMemorySession`, local only, with a fixed-length buffer mode [faster, size-capped] or ring buffer mode [unbounded, slower]). HARS supports a single client at a time; an auto-close option kills the server when the last session closes (license return). Each session is mutex-protected; true parallelism requires multiple sessions/HARS processes. SessionSync runs a HARS inside an interactive Houdini so external clients drive a live GUI instance. The Unreal plugin (HoudiniEngineForUnreal-v2) keeps all HAPI logic editor-only in one module.

Source: [sidefx.com — HAPI Sessions docs](https://www.sidefx.com/docs/hengine/_h_a_p_i__sessions.html) ; [github.com/sideeffects/HoudiniEngineForUnreal-v2](https://github.com/sideeffects/HoudiniEngineForUnreal-v2)

### Quixel Bridge export mechanism

Bridge pushes assets to engines by sending JSON metadata over a local TCP socket to a listener inside the engine plugin ("Custom Export" lets any third-party tool register a custom local socket port to receive the same JSON). UE LiveLink errors reference port `13428`; a Substance Painter integration uses `24981`. The engine-side plugin then performs import/material assembly from the JSON descriptor — i.e., heavy data moves via disk paths, only a compact JSON descriptor crosses the socket.

Source: [dev.epicgames.com — Quixel Bridge plugin for Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/quixel-bridge-plugin-for-unreal-engine) ; [github.com/Raider-Arts/painter-megascan-link](https://github.com/Raider-Arts/painter-megascan-link) ; [polycount.com — Unreal and Bridge LiveLink error](https://polycount.com/discussion/204029/answered-unreal-and-bridge-livelink-error)

### Datasmith Direct Link (incremental sync)

Direct Link maintains a persistent link between DCC/CAD sources and UE-based destinations (many-to-many), pushing incremental scene updates so users never re-export full `.udatasmith` files; sync is user-triggered (AutoSync = push-without-intervention was on Epic's roadmap). Packaged UE apps need UDP messaging enabled via the `-messaging` command-line parameter for Direct Link discovery. Pattern: keep a persistent scene-graph session and transmit diffs, not whole scenes.

Source: [dev.epicgames.com — Using Datasmith Direct Link in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-datasmith-direct-link-in-unreal-engine) ; [unrealengine.com — Where Datasmith goes next](https://www.unrealengine.com/en-US/blog/where-datasmith-goes-next-fast-synchronized-updates)

### OpenUSD as studio interchange

USD (invented at Pixar after 2012's Brave to tame pipeline complexity, open-sourced 2016) provides a common scenegraph with non-destructive layered composition: multiple contributors sparsely override a shared scene in separate layers; composition arcs assemble assets into scenes with instancing. UE's USD Stage workflow (USD Importer plugin) works natively with USD data instead of converting to UE assets, gives faster load, preserves source structure, and applies live updates when the source `.usd` file changes on disk.

Source: [openusd.org — introduction](https://openusd.org/release/intro.html) ; [pixar.com/openusd](https://www.pixar.com/openusd) ; [dev.epicgames.com — Universal Scene Description in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/universal-scene-description-in-unreal-engine)

### Omniverse Nucleus delta protocol

Nucleus keeps live USD links by tracking per-asset delta changes and communicating only those deltas to clients. The server includes a sequence number with each update (updates may arrive out of order), and an `ObjectId` uniquely identifies each live layer so deltas survive moves/renames. Client "live" functions send pending deltas and apply received deltas, and must run when no other thread is touching USD (a main-thread marshalling requirement, the same constraint class as Blender's `bpy`).

Source: [docs.omniverse.nvidia.com — omni-client-live](https://docs.omniverse.nvidia.com/kit/docs/usd_resolver/latest/docs/omni-client-live.html) ; [innoactive.io — Why USD and how it integrates into Omniverse](https://innoactive.io/resources/portal/why-usd-and-how-it-integrates-into-omniverse)

### glTF as delivery format

glTF 2.0 (Khronos) is the API-neutral runtime transmission format: a compact JSON scene description + binary buffers (single-file `.glb`), designed for minimal unpack/processing at load, explicitly contrasted with authoring formats. Studios use USD for authoring/assembly and glTF for lightweight delivery; USD->glTF conversion is lossy but standard.

Source: [registry.khronos.org — glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) ; [khronos.org/gltf](https://www.khronos.org/gltf/)

### Asset naming conventions (UE)

De-facto standard (Allar ue5-style-guide, echoed by Epic and Tom Looman): `Prefix_BaseAssetName_Variant_Suffix`, with type acronym prefixes (`T_` texture, `M_` material, `SM_` static mesh, `BP_` blueprint, etc.) and modifier tables for suffixes. Rationale stated in the guide: a conforming project can have assets "managed, searched, parsed, and maintained with incredible ease"; folders organize by logical grouping since type is already encoded in the name. For an AI bridge this makes asset type inferable from the name alone — no extra metadata queries.

Source: [github.com/Allar/ue5-style-guide](https://github.com/Allar/ue5-style-guide) ; [tomlooman.com — Unreal Engine naming convention guide](https://tomlooman.com/unreal-engine-naming-convention-guide/)

### Switchboard / virtual production control

Switchboard is a Python app that launches and monitors fleets of UE instances, nDisplay cluster nodes, and stage devices from one machine. The control channel is OSC (Open Sound Control): Switchboard's OSC client talks to the Virtual Production Utilities plugin's OSC server in each UE instance; a SwitchboardListener runs on every machine to launch processes; all editors join a Multi-User (concert) session for synchronized state. Extensible via custom device plugins. Pattern: one orchestrator + tiny per-host listener daemons + a low-overhead message protocol.

Source: [dev.epicgames.com — Switchboard overview (4.27)](https://dev.epicgames.com/documentation/en-us/unreal-engine/switchboard-overview?application_version=4.27)

### Flamenco architecture (Blender Studio render farm)

Three components: Blender add-on (submitter), Manager, Workers. The core is Go + SQLite (via sqlc); the entire surface — web UI, worker protocol, add-on submission — is one OpenAPI 3 spec on a single port, with generated clients for Go, Python, and JavaScript. Job types are JavaScript "job compiler" scripts on the Manager that take a small job spec (settings) and expand it into concrete per-frame tasks for workers; users customize the farm by editing/writing job compiler scripts rather than modifying the farm (SIGGRAPH 2025 lab: "Please Don't Write a New Render Farm, Customize Flamenco").

Source: [flamenco.blender.org — Flamenco API](https://flamenco.blender.org/development/flamenco-api/) ; [flamenco.blender.org — job types](https://flamenco.blender.org/usage/job-types/) ; [dl.acm.org/doi/full/10.1145/3721251.3734064](https://dl.acm.org/doi/full/10.1145/3721251.3734064)

### Flamenco Shaman content-addressed storage

The add-on computes an identifier (SHA256 + byte length) for every file a render job needs; the Manager replies with which identifiers are already stored, and the client uploads only new/changed files. The Manager builds job "checkouts" as directory trees of symlinks into the SHA256-keyed store, so one stored blob serves many jobs simultaneously. Separate bins exist for in-flight uploads vs fully-stored files.

Source: [flamenco.blender.org — Shaman shared storage](https://flamenco.blender.org/usage/shared-storage/shaman/) ; [pkg.go.dev — flamenco/pkg/shaman](https://pkg.go.dev/projects.blender.org/studio/flamenco/pkg/shaman)

### Blender Studio pipeline tooling

Blender Studio's pipeline (blender-studio-tools repo, docs at studio.blender.org/tools/) is a set of focused add-ons plus CLI tools: blender-kitsu (two-way integration with the Kitsu production tracker from inside Blender), asset-pipeline (Asset Builder + Asset Updater managing push/pull of shared assets), cache-manager (streamlined Alembic cache workflow), render-review (review renders in the sequence editor), anim-setup (automates animation scene setup), contactsheet, and blender-purge (a command-line tool to purge orphan data). Pattern: many small single-purpose automations wired to a central tracker, not one monolith.

Source: [github.com/paulgolter/blender-studio-tools](https://github.com/paulgolter/blender-studio-tools) ; [studio.blender.org — blender_kitsu](https://studio.blender.org/tools/addons/blender_kitsu)

### Blender headless automation

`blender --background file.blend --python script.py` runs Blender with no GUI for farms/CI; argument order matters (file before script). `bpy` is also available as a pip-installable standalone module for pure-Python processes; wrappers like `blenderless` exist because raw `bpy` in headless environments is awkward. This is the fallback execution mode when no persistent session exists.

Source: [docs.blender.org/api](https://docs.blender.org/api/) ; [pypi.org/project/blenderless/0.1.7](https://pypi.org/project/blenderless/0.1.7/) ; [renderday.com — Mastering the Blender CLI](https://renderday.com/blog/mastering-the-blender-cli)

### Blender in-process bridge pattern (thread safety)

`bpy` is not thread-safe: touching `bpy.data` from a socket thread causes crashes (`EXCEPTION_ACCESS_VIOLATION`) or silent corruption. The proven addon pattern (used by blender-mcp and derivatives): a TCP socket server thread accepts connections and pushes commands onto a queue; a single `bpy.app.timers` callback on the main thread drains the queue and executes `bpy` calls, returning an interval to reschedule. Registering one timer per command is unreliable (callbacks silently dropped, especially on Windows), so one persistent draining timer + queue is the correct design.

Source: [docs.blender.org — bpy.app.timers (2.8)](https://docs.blender.org/api/blender2.8/bpy.app.timers.html) ; [github.com/ahujasid/blender-mcp addon.py](https://github.com/ahujasid/blender-mcp/blob/main/addon.py) ; [github.com/glonorce/Blender_mcp](https://github.com/glonorce/Blender_mcp)

### blender-mcp (existing AI bridge, prior art)

Three-tier: MCP server (`src/blender_mcp/server.py`) <-> Blender addon socket server (`addon.py`) on `localhost:9876` (`BLENDER_HOST`/`BLENDER_PORT` overridable), JSON commands `{type, params}` -> responses `{status, result|message}` over TCP (length-prefixed frames). Tools: scene/object inspection, object create/delete/modify, materials, arbitrary `execute_blender_code` (documented as dangerous — "ALWAYS save your work"), plus asset acquisition via Poly Haven, Sketchfab, Hyper3D Rodin, Hunyuan3D. The README notes complex operations must be broken into smaller steps and only one MCP client instance may connect at a time.

Source: [github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)

### unreal-mcp (existing AI bridge, prior art)

chongdashu/unreal-mcp: a UE 5.5+ C++ editor plugin runs a TCP server on port `55557`; a Python FastMCP server connects as TCP client and exposes tools for actor create/delete/transform/property query, Blueprint class creation, Blueprint graph editing, component configuration, input mappings, and editor viewport control. Experimental status. The alternative runreal/unreal-mcp exposes an `editor_run_python` tool over the same idea.

Source: [github.com/chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp)

## Recommendations for TEE

1. Run a persistent in-engine agent, never per-call process spawns: copy HAPI's session model (long-lived server process, sessions opened over TCP/named pipe/shared memory) and blender-mcp/unreal-mcp's resident socket servers. Editor boot costs (UE cold start, Blender file load) are paid once; every AI round-trip is then a milliseconds-scale local RPC.
2. Use terse JSON verb+params framing over local TCP/WebSocket (Quixel Bridge, blender-mcp `{type, params}` -> `{status, result}`, UE Remote Control `{MessageName, Parameters, Id}`). Include a request `Id` for async/deferred responses like UE's WebSocket API so long operations don't block the channel.
3. In Blender, marshal every `bpy` call to the main thread via one persistent `bpy.app.timers` callback draining a thread-safe queue — never a timer per command (silently dropped on Windows) and never `bpy` from the socket thread (crashes). This is the single most important correctness constraint for the Blender side of TEE.
4. For UE, layer three transports by task: (a) Remote Control HTTP/WS (ports `30010`/`30020`) for structured property get/set and function calls; (b) Python remote execution (multicast `239.0.0.1:6766` discovery + TCP command channel, `EvaluateStatement` mode) for arbitrary editor scripting into a live editor; (c) `UnrealEditor-Cmd -run=pythonscript` for headless batch. TEE should auto-discover live editors via the multicast PING/PONG and fall back to headless commandlets.
5. Copy the Remote Control Preset pattern for token efficiency: expose a curated, named subset of properties/functions to the AI instead of the raw reflection surface, and use `preset.register`-style subscriptions so the bridge receives compact change events (`PropertyLabel` + new value) instead of re-polling scene state.
6. Return diffs, not dumps: mirror Datasmith Direct Link and Omniverse Nucleus — keep a scene-graph snapshot server-side, respond to AI queries with deltas since the last known state, tag updates with sequence numbers, and use stable object IDs so references survive renames/moves. Full scene dumps should be an explicit, rarely-used tool.
7. Move bulk data out of band: only compact JSON descriptors and file paths/handles cross the AI channel (Quixel Bridge pattern); meshes/textures move via the filesystem or a content-addressed store. Never inline geometry or pixel data into tool results.
8. Adopt Shaman-style content addressing (SHA256+size identifiers, server reports which blobs it already has, client sends only missing ones, symlink checkouts) for any asset transfer between TEE, Blender, and UE — it eliminates redundant uploads and gives cheap idempotency.
9. Offer high-level "job compiler" tools, not micro-steps: like Flamenco's JavaScript job types and BuildGraph's XML node graphs, let the AI submit a small declarative spec (e.g. "turntable render, 64 frames, asset X") that server-side code expands into the many concrete engine operations. This collapses dozens of tool round-trips (each costing tokens) into one call, and matches blender-mcp's observed failure mode ("complex operations must be broken into smaller steps").
10. Encode type/context in names: enforce `Prefix_BaseAssetName_Variant_Suffix` (`T_`, `M_`, `SM_`, `BP_`) so the AI can infer asset type, variant, and role from listings alone, avoiding per-asset metadata queries.
11. Use USD/glTF at the interchange boundary: USD layers for non-destructive AI edits over studio scenes (sparse override files are tiny and reviewable, and UE's USD Stage live-reloads them from disk); glTF/`.glb` for compact one-shot geometry handoff.
12. For fleet/scale-out (multiple editors, render nodes), copy Switchboard/Flamenco topology: one orchestrator, a tiny listener daemon per host, a single OpenAPI-defined surface for all clients (Flamenco generates Go/Python/JS clients from one spec — TEE could generate its MCP tool schemas and REST clients from the same source of truth), and MRQ's `-MoviePipelineConfig` preset + Python executor for headless renders.
13. Sandbox the escape hatch: keep an `execute_python` tool (both engines) for the long tail, but follow blender-mcp's warning — gate it, snapshot/save before running, and prefer structured tools; arbitrary code is also the most token-expensive and error-prone path (a failed script means a full retry round-trip).
