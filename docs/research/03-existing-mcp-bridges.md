# Existing MCP Bridges

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Summary

The dominant open-source pattern for AI-to-DCC bridges is a local MCP server (Python/FastMCP or Node, stdio to the client) relaying JSON commands over a localhost TCP socket to an in-app addon/plugin, with an escape-hatch "execute arbitrary Python" tool (blender-mcp, chongdashu/unreal-mcp, and capoomgit/houdini-mcp all follow it). The recurring failure modes are timeouts on long DCC operations, server hangs when the DCC isn't running, incomplete/oversized JSON responses, editor crashes from malformed inputs, and LLMs hallucinating DCC Python APIs.

Second-generation projects respond with large typed direct-dispatch tool surfaces instead of code-gen (6xvl/blender-mcp with ~276 tools, GG_MayaMCP with 71 typed no-code-exec tools, CoplayDev/unity-mcp with 47 toggleable tool groups), bundled current API documentation to fight hallucination (official Blender Lab MCP ships RST API refs in-server), and read-first/approval-gated write designs.

Officially, Blender Lab now ships an official MCP extension (Blender 5.1+, inspection-first, 19 read-only tools) and Epic shipped an Experimental MCP plugin in UE 5.8 exposing Blueprints, assets, levels, materials, and meshes, naming MCP a pillar of UE6. For token efficiency specifically, Anthropic's own engineering guidance (code execution with MCP, progressive tool disclosure) reports up to 98.7% token reduction versus loading all tool definitions and piping intermediate results through context.

## Findings

### blender-mcp (ahujasid) — architecture

The MCP server is a Python process launched by the client via `uvx` (stdio to Claude Desktop/Cursor/VS Code); it relays JSON commands over a TCP socket to a Blender addon (`blender_mcp.py`) that runs a socket server on `localhost:9876`. Requires Python 3.10+ and Blender 3.0+. 26.1k stars, 2.5k forks.

Tools: scene inspection/object queries, object create/modify/delete, materials, `execute_blender_code` (arbitrary Python in Blender), and asset downloads. Integrations: Poly Haven, Sketchfab (API key), Hyper3D Rodin, Hunyuan3D. The README warns that `execute_blender_code` is dangerous ("ALWAYS save your work"), that complex operations should be broken into smaller steps, and that the Poly Haven integration can be erratic.

Source: [https://github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)

### blender-mcp — known failure modes (issues)

- Issue #275: if Blender isn't running, the MCP server hangs during the MCP handshake instead of failing fast, causing "context deadline exceeded" in the host and blocking ALL other MCP servers from loading.
- Issue #219: incomplete 51-byte JSON responses from the addon despite a live connection on `localhost:9876`.
- Issue #50: MCP error `-32001` request timeouts on complex operations, with work silently lost; the documented mitigation is to split requests into smaller sequential prompts.

Source: [blender-mcp #275](https://github.com/ahujasid/blender-mcp/issues/275), [#219](https://github.com/ahujasid/blender-mcp/issues/219), [#50](https://github.com/ahujasid/blender-mcp/issues/50)

### 6xvl/blender-mcp fork — direct-dispatch alternative

A fork replacing code-generation with ~276 direct-dispatch typed tools (each an `@mcp.tool` in `server.py`) across 9 categories (Inspect, Transform, Mesh Edit, Rig+Skin, Animate, Materials/UV, Modifiers, Export, Maintenance), avoiding per-call Python compilation. Adds hang mitigation (`bm_force_mode_set` for `bpy` ops blocking the main thread) and forced auto-update (the addon checks the repo `VERSION` file at Blender startup and atomically replaces addon+server). Same `localhost:9876` socket transport. Limitation: context-sensitive ops needing `VIEW_3D` context require workarounds.

Source: [https://github.com/6xvl/blender-mcp](https://github.com/6xvl/blender-mcp)

### BlenderGPT (gd3kr) — pre-MCP baseline

A 2023 Blender addon (no MCP): a natural-language box in Blender's sidebar calls the OpenAI GPT-4/3.5 API directly, generates a `bpy` Python script, and executes it in-process. No structured tools, no scene-state feedback loop; reliability depends entirely on one-shot code generation quality. Historically significant as the pattern all MCP servers improved on (adding bidirectional state inspection).

Source: [https://github.com/gd3kr/BlenderGPT](https://github.com/gd3kr/BlenderGPT)

### Official Blender MCP (Blender Lab)

The Blender Foundation's Blender Lab develops an official MCP server + add-on, distributed as a Blender Extension on the official Extensions platform (`blender.org/lab/mcp-server`; repo `projects.blender.org/lab/blender_mcp`). Packaged as an `.mcpb` (MCP Bundle) for drag-and-drop install into Claude. Requires Blender 5.1+ and Python 3.13 (needs `bpy.app.handler.exit_pre` and new cache-dir APIs).

The design is "inspection and analysis first": 19 read-only tools, write operations require explicit approval. It bundles the full Blender Python API reference and user manual in RST format inside the server so the model reads current docs instead of hallucinating from stale training data (important given breaking API changes in Blender 5.0). No external asset integrations. Blender Lab is explicitly outside the Blender roadmap with no release target; the policy stance is that no generative AI is integrated into Blender itself. Anthropic joined the Blender Dev Fund as Corporate Patron (April 2026), amended to a one-time donation on 2026-05-01 pending an updated AI policy.

Source: [https://note.com/yaoyoroztech/n/n2c1f2ff3cabe](https://note.com/yaoyoroztech/n/n2c1f2ff3cabe); [https://projects.blender.org/lab/blender_mcp](https://projects.blender.org/lab/blender_mcp); [https://www.blender.org/news/upcoming-blender-development-fund-and-ai-policies/](https://www.blender.org/news/upcoming-blender-development-fund-and-ai-policies/)

### chongdashu/unreal-mcp — architecture

A Python MCP server (FastMCP, Python 3.12+) speaks MCP to the client and connects over TCP to a C++ `UnrealMCP` plugin running a native TCP server on port `55557` inside the UE editor. UE 5.5+. Tool categories: Actor management (create/delete/transform/query/list), Blueprint development (create classes, add components, set properties, compile, spawn), Blueprint node graph (add events, function-call nodes, connect nodes, variables), and Editor control (viewport focus, camera). README: "EXPERIMENTAL", production use discouraged.

Source: [https://github.com/chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp)

### chongdashu/unreal-mcp — failure modes

Editor crashes (fatal error) from double-slash package paths when creating components. Common setup failures: blocked port `55557`, missing VS workload, absolute-vs-relative config paths, plugin build failures. An Epic forums analysis (Unreal MCP + Codex) concludes it lacks reliable readiness/state APIs, structured error reporting, and safe Blueprint-editing tools for fully autonomous work; humans must manually move Blueprint nodes for visibility and split struct pins.

Source: [chongdashu/unreal-mcp #2](https://github.com/chongdashu/unreal-mcp/issues/2); [https://forums.unrealengine.com/t/unreal-mcp-codex-issue-analysis-report/2730883](https://forums.unrealengine.com/t/unreal-mcp-codex-issue-analysis-report/2730883)

### kvick-games/UnrealMCP — architecture

Inverts the common layout: the TCP server (JSON command protocol, port `13377`) runs inside the UE plugin itself; a thin Python companion layer is the MCP side. Tools: `get_scene_info`, `create_object`, `delete_object`, `modify_object`, `execute_python`, transforms. UE 5.5 only tested, Windows-only-ish, "VERY WIP", ~71 commits, last meaningful activity March 2025. The author's key lesson: "Claude makes a lot of errors with unreal python" due to sparse UE-Python training data — materials/Blueprints/Niagara never completed.

Source: [https://github.com/kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP)

### runreal/unreal-mcp — pluginless architecture

A TypeScript/Node MCP server that requires NO custom UE plugin: it uses UE's built-in Python remote execution protocol (enable Python Editor Script Plugin + the "Remote Execution" project setting). 20+ tools: asset listing/export/search, Python exec in editor, console commands, level/world query and manipulation, actor create/modify, screenshots, camera control, project/map info. UE 5.4+. Caveat in the README: agents get "full access to your Editor"; not an official Epic project. ~113 stars, active.

Source: [https://github.com/runreal/unreal-mcp](https://github.com/runreal/unreal-mcp)

### flopperam/unreal-engine-mcp — open-source + hosted commercial split

An MIT repo now owned by Aura (tryaura.dev). Open-source local variant: stdio MCP server (`unreal_mcp_server_advanced.py`, Python 3.12+) -> TCP socket -> bundled `UnrealMCP` C++ plugin; 23+ Blueprint node types, actor management, physics/materials, and prefab "world building" macro-tools (castles, bridges, mazes, towns) that build whole structures from one call.

Hosted "Flop MCP": Streamable HTTP/WebSocket to `agent.flopperam.com/mcp` with API key, FlopAI plugin, 50+ tools across 9 domains (Blueprint authoring/inspection, scene, materials, Niagara/Chaos VFX, animation, UMG, behavior trees/GAS, landscape/foliage, cinematics, procedural gen, diagnostics, runtime verification, Python exec) — 64 tools marketed, 46 free. Supports UE 5.5/5.6/5.7. A Deep Blueprint Analysis tool inspects variables, functions, event dispatchers, and interfaces.

Source: [https://github.com/flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp); [https://www.flopperam.com/mcp](https://www.flopperam.com/mcp)

### Epic official — Developer Assistant and UE 5.8 MCP plugin

Epic Developer Assistant: beta June 2025 for UEFN, expanded September 2025 to UE 5.6 (doc queries, C++ codegen), integrated in-editor in UE 5.7 (November 2025) as Experimental with F1 contextual help. At State of Unreal 2026, UE 5.8 (the last major UE5 release) introduced an Experimental first-party Model Context Protocol plugin letting models like Claude and Gemini connect to UE projects and exposing core systems: Blueprints, assets, levels, materials, meshes.

Epic named MCP/AI-model integrations one of three UE6 pillars (with Verse and open content standards); UE6 Early Access is targeted for end of 2027, and Blueprints are to be eventually deprecated in favor of Verse. Aura (which acquired flopperam's MCP) launched January 2, 2026 as a commercial in-editor UE agent (scene lighting, post-processing config, mass Blueprint edits).

Source: [https://grokipedia.com/page/Epic_Developer_Assistant](https://grokipedia.com/page/Epic_Developer_Assistant); [https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show](https://www.unrealengine.com/news/state-of-unreal-2026-top-news-from-the-show); [https://80.lv/articles/state-of-unreal-ue6-reactions-hype-skepticism-and-what-it-means-for-game-devs](https://80.lv/articles/state-of-unreal-ue6-reactions-hype-skepticism-and-what-it-means-for-game-devs); [https://www.prnewswire.com/news-releases/aura-ai-assistant-for-unreal-engine-launches-vr-studio-ships-game-in-half-the-time-with-new-agent-capabilities-302651608.html](https://www.prnewswire.com/news-releases/aura-ai-assistant-for-unreal-engine-launches-vr-studio-ships-game-in-half-the-time-with-new-agent-capabilities-302651608.html)

### CoplayDev/unity-mcp (ex justinpbarnett) — most mature DCC MCP

Three-layer architecture: MCP clients -> Python FastMCP server + WebSocket hub (auto-discovers tool registrations, per-session routing via `client_id`, hot-reloadable, multi-Unity-instance routing) -> C# editor plugin (`MCPForUnity`). 47-48 focused tool entrypoints plus ~25 MCP resources; tool groups (VFX, animation, UI, testing) can be toggled independently to shrink the exposed surface. Roslyn runtime compilation validates generated C# before editor execution. Unity 2021.3 LTS-6.x, Python 3.10+/`uv`, 22 auto-configured clients, optional remote hosted server with auth. The project was sold by the original author to Coplay.

Source: [https://github.com/CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp); [https://coplaydev.github.io/unity-mcp/](https://coplaydev.github.io/unity-mcp/)

### Maya MCP landscape — typed tools + no in-app install

PatrickPalmer/MayaMCP and GG_MayaMCP need NOTHING installed in Maya: they drive Maya's built-in `commandPort` (MEL/Python over TCP) from a standalone local Python MCP server, so a crash on either side doesn't kill the other. GG_MayaMCP: 71 typed tools, explicitly NO arbitrary code execution — "The AI can't just run any arbitrary string. It has to use the tools that exist, with the parameters those tools accept"; it positions AI for exploration/iteration/debugging, not batch scripting. abrahamADSK/maya-mcp adds RAG search over docs, "anti-hallucination safety", and self-learning. dcc-mcp/dcc-mcp-maya runs a Rust sidecar server so HTTP/gateway traffic stays off Maya's UI thread, routing API work through Maya-safe dispatchers.

Source: [https://github.com/PatrickPalmer/MayaMCP](https://github.com/PatrickPalmer/MayaMCP); [https://gimbalgoats.com/blog/what-is-maya-mcp](https://gimbalgoats.com/blog/what-is-maya-mcp); [https://github.com/abrahamADSK/maya-mcp](https://github.com/abrahamADSK/maya-mcp); [https://github.com/dcc-mcp/dcc-mcp-maya](https://github.com/dcc-mcp/dcc-mcp-maya)

### Houdini MCPs

capoomgit/houdini-mcp (the first full-featured one, explicitly modeled on ahujasid/blender-mcp): a Houdini `addon.py` socket server + external MCP server, JSON-over-TCP `{type, params}` -> `{status, result|message}`; covers node-graph creation, sim setup, and rendering; third-party, not SideFX. Variants: lecopivo/another-houdini-mcp runs the MCP server directly inside Houdini over stdio (zero network config); oculairmedia/houdini-mcp uses Houdini's `hrpyc` (built-in RPC) instead of a custom addon; kleer001/houdini-mcp markets "Every Node. Every Parameter." full-surface coverage.

Source: [https://github.com/capoomgit/houdini-mcp](https://github.com/capoomgit/houdini-mcp); [https://github.com/lecopivo/another-houdini-mcp](https://github.com/lecopivo/another-houdini-mcp); [https://github.com/oculairmedia/houdini-mcp](https://github.com/oculairmedia/houdini-mcp)

### Token-efficiency guidance directly applicable to TEE

Anthropic engineering (November 2025, "Code execution with MCP"): loading all tool definitions upfront and passing intermediate results through the context window is the dominant token cost as tool count grows. Presenting MCP servers as code APIs in a filesystem structure with progressive/on-demand tool discovery, and processing intermediate results inside a code-execution environment instead of round-tripping them through the model, cut token usage by up to 98.7% in their example. Community implementations exist (e.g. elusznik/mcp-server-code-execution-mode: "Zero-Context Discovery for 100+ MCP Tools").

This directly tensions with the 276-tool direct-dispatch approach: big typed surfaces cost definition tokens unless disclosure is progressive or tools are grouped/toggleable (Unity MCP's tool groups) or wrapped as callable code APIs.

Source: [https://www.anthropic.com/engineering/code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Cross-project failure-mode summary (lessons)

Recurring documented problems across all surveyed bridges:

1. Long DCC operations exceed MCP client timeouts (~60s) with no progress/async mechanism — work lost (blender-mcp #50/#219).
2. No fail-fast when the DCC isn't running — server hangs break the whole MCP client config (blender-mcp #275).
3. Unvalidated string inputs crash the editor (chongdashu #2 double-slash paths — UE fatal error).
4. LLMs hallucinate DCC Python APIs (kvick README; Blender 5.0 breaking changes) — fixed by bundling docs (official Blender MCP RST refs, abrahamADSK RAG) or typed tools.
5. Verbose scene dumps flood context — mitigations are typed narrow queries and summarized scene info.
6. Arbitrary code-exec tools are simultaneously the most-used escape hatch and the top safety complaint (both the official Blender comparison and community versions execute LLM code unsandboxed — prompt-injection = RCE).
7. Main-thread blocking in the DCC requires dispatch to the UI/main thread with watchdogs (6xvl hang detection, dcc-mcp Rust sidecar).

Source: aggregate of repos/issues cited above

## Recommendations for TEE

1. Use the proven two-piece topology (stdio MCP server outside the DCC + thin in-DCC listener over localhost TCP/named pipe) but make the bridge fail fast: complete the MCP handshake even when the DCC is down and return a structured "DCC not connected" error — blender-mcp's hang-on-startup (#275) breaks entire client configs.
2. Design for MCP client timeouts from day one: every potentially long DCC operation (bake, compile, import, render) should be async — return a job id immediately, poll with a cheap status tool — and length-frame/chunk socket responses so partial JSON can never reach the model (blender-mcp #219/#50).
3. Prefer typed direct-dispatch tools over "execute arbitrary Python" for the common 80% of operations (GG_MayaMCP, 6xvl, official Blender MCP pattern): they eliminate API hallucination, cost fewer tokens than emitting `bpy`/UE Python source, validate inputs before they crash the editor (chongdashu #2), and give deterministic, compact results. Keep code-exec as a gated escape hatch.
4. Do NOT ship a flat 200+ tool surface — that trades code-gen tokens for tool-definition tokens. Use progressive disclosure: toggleable tool groups (Unity MCP), a search/describe-tools meta-tool, or Anthropic's code-execution-with-MCP pattern (tools as filesystem code APIs, intermediate results processed outside the context window; up to 98.7% token reduction).
5. Make every read tool return summarized, budgeted output by default (counts, bounding boxes, hierarchies truncated with "N more…") with explicit verbosity/detail parameters — verbose scene dumps are the biggest per-call token sink in existing bridges.
6. Bundle or RAG-index current API documentation server-side (official Blender MCP ships RST API refs; abrahamADSK/maya-mcp uses RAG) so the model queries ground truth instead of hallucinating from stale training data — critical for Blender 5.x breaking changes and sparsely-trained UE Python.
7. Provide macro/composite tools for common multi-step intents (flopperam's one-call structure builders, spawn-and-wire Blueprint helpers): one semantic call replaces dozens of primitive calls and their round-tripped results — the single largest practical token saver observed in the wild.
8. Add readiness/state and structured-error APIs the Epic-forums analysis found missing in chongdashu: machine-readable error codes, current-mode/context reporting, and post-write verification (Unity MCP's Roslyn validation is the model) so the agent doesn't burn tokens on blind retry loops.
9. Keep DCC-side execution off the main thread where possible, with a watchdog/hang-detector and a force-recover tool (6xvl's `bm_force_mode_set`; dcc-mcp's Rust sidecar keeping HTTP off Maya's UI thread).
10. For Unreal specifically, track Epic's official Experimental MCP plugin in UE 5.8 (exposes Blueprints, assets, levels, materials, meshes; MCP is a stated UE6 pillar) — position TEE as the token-efficiency/orchestration layer on top of or compatible with it rather than competing on raw engine bindings; also consider runreal's pluginless approach (UE built-in Python remote execution) to eliminate C++ plugin build/version friction for read-heavy tools.
11. Adopt read-first safety semantics like the official Blender MCP (free read-only inspection tools, write ops gated/approved) — it lowers user risk and lets you cache/replay reads aggressively.
12. Follow the `.mcpb`/one-click install trend (official Blender MCP drag-and-drop bundle) — setup friction (ports, `uv`, plugin builds, config paths) is the top category of GitHub issues across every surveyed project.
