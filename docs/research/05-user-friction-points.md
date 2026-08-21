# User Friction Points

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Summary

User friction with AI-driven Blender/Unreal falls into four hard clusters, all well-documented in primary sources.

(1) Generated code fails constantly from version drift: LLMs emit `bpy` calls removed in Blender 4.x/5.0 (`use_auto_smooth`, `version_char`, `scene.node_tree`) and hallucinate UE functions by name-pattern analogy ("They assume `GetActorVelocityNormalized()` exists because `GetActorLocation()` does"), while Blueprints are effectively invisible to text models except via pasted T3D serialization.

(2) Workflow friction is dominated by token economics and blindness: a real test burned 60% of a $200/mo Claude Max plan in 2 hours on one donut scene, MCP tool schemas alone cost 15-20K tokens/turn, a single 640x480 PNG viewport capture costs ~20x more than a budgeted JPEG, and agents execute "fifty geometrically valid operations" producing garbage while every call returns success — with no rollback when things break.

(3) Setup friction (Windows stdio corruption, `uv`/node path issues, UE plugin recompiles per engine version, truncated JSON, 5-minute stalls, `-32001` timeouts) fills the majority of blender-mcp's and unreal-mcp's issue trackers.

(4) Users explicitly ask for: disabling unwanted tools, structured scene/Blueprint text representations, read-back verification against real project files, checkpoints/undo, local-LLM support, and persistent context across sessions.

Competitors (StraySpark v3, Epic's official UE 5.8 MCP, Blender's official add-on) are already shipping partial fixes — catalog-mode tool loading (~95% token cut), 200KB-budget JPEG vision, and transaction scopes — which validates TEE's thesis but raises the bar.

## Findings

### bpy API version drift breaks LLM-generated scripts

Concrete breaking changes LLMs trip on: `Mesh.use_auto_smooth` removed in Blender 4.1 (users resolved by downgrading to 3.6); `bpy.app.version_char` deprecated in 4.0, gone in 4.3.2; passing context dicts to operators removed in 4.0 (must use `context.temp_override()`). Blender 5.0 removed `scene.node_tree`, replaced the Action API, and restructured Grease Pencil — breaking "whole categories: compositing, Grease Pencil, animation, rendering, geometry nodes, rigging" in MCP servers that used inline version branching.

Source: [community.adobe.com Mixamo discussion](https://community.adobe.com/t5/mixamo-discussions/blender-plugin-not-working-due-to-deprecated-bpy-app-version-char-attribute-in-blender-api/td-p/15196754) ; [StraySpark blog — Blender MCP server v3 / Blender 5.x rewrite / 404 tools](https://www.strayspark.studio/blog/blender-mcp-server-v3-blender-5x-rewrite-404-tools)

### Root cause of bad AI Blender code per community

Blender Artists thread on ChatGPT script failures: "It's pulling from all the existing, human-written, open-source Blender Python code on GitHub — 80% of which is riddled with errors, outdated, half complete." A working script required 5 revision iterations; the AI forgot prerequisite steps (creating an armature before adding bones); long scripts truncated mid-generation.

Source: [blenderartists.org — "ChatGPT AI failed to generate a supposedly simple script"](https://blenderartists.org/t/chatgpt-ai-failed-to-generate-a-supposedly-simple-script/1422685)

### Hallucinated Unreal Engine APIs

Epic forum users: "Chatgpt makes sh*t up and gives you function call to stuff that doesn't exist" (MostHost_LA); "They assume `GetActorVelocityNormalized()` exists because `GetActorLocation()` does" (anirudhak101); Claude suggested nodes incompatible with UE 5.5 because its knowledge was stuck at 5.4 (Herkyn). Users' stated wish: agents that verify code against actual project files rather than guessing APIs.

Source: [forums.unrealengine.com — "What's the best AI to help with coding C++ in Unreal"](https://forums.unrealengine.com/t/whats-the-best-ai-to-help-with-coding-c-in-unreal-chatgpt-or/1307271)

### Four recurring UE C++ failure modes and mitigations

TechnicallyArtist catalogs: (1) hallucinated/renamed APIs from model memory lagging the installed UE version; (2) generated code compiles but is invisible to Blueprint due to missing `UFUNCTION(BlueprintCallable)`/`UCLASS()`/`GENERATED_BODY()` reflection macros; (3) linker errors from modules absent in `.Build.cs` `PublicDependencyModuleNames`; (4) over-contextualization — pasting 800-line files makes the model anchor on wrong details and wastes tokens. Recommended: send only the class slice needed, name reflection intent explicitly.

Source: [technicallyartist.com — Claude/ChatGPT C++ Unreal Engine](https://technicallyartist.com/blog/claude-chatgpt-cpp-unreal-engine/)

### UE Python is a low-resource language for LLMs

The kvick-games/UnrealMCP README states plainly: "Claude makes a lot of errors with unreal python as I believe there aren't a ton of examples for it." The same README warns "AI agents may make unexpected changes to your project. Files could be accidentally deleted or modified" and mandates source control + backups. Only tested on UE 5.5, Windows-only, "VERY WIP REPO".

Source: [github.com/kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP)

### Blueprint inaccessibility to text models

Epic forum consensus: ChatGPT "only knows nodes from how people talk about them instead of them exactly so it has a significantly higher error rate than syntax for text based code" (SupportiveEntity); "it will act and seem like it knows blueprint but It always gives wrong instructions" (TheKJ). LLMs "could explain the steps quite nicely, however they couldn't form diagrams." Community workaround: Ctrl+C on BP nodes yields serialized ASCII (T3D) text that ChatGPT can read; users propose BP Graph -> ASCII -> JSON -> LLM -> JSON -> ASCII round-trips; the third-party plugin BP2AI sells Blueprint-to-text export for AI analysis; user gouderadrian proposed UE generate textual hierarchies of blueprints for AI comprehension.

Source: [forums.unrealengine.com — ChatGPT and Blueprint comprehension](https://forums.unrealengine.com/t/chatgpt-and-blueprint-comprehension/1172660) ; [forums.unrealengine.com — Using LLMs to learn Blueprints](https://forums.unrealengine.com/t/using-llms-to-learn-blueprints/1973345) ; [forums.unrealengine.com — Training GenAI to script with Blueprints ASCII text](https://forums.unrealengine.com/t/training-genai-to-script-with-blueprints-ascii-text/2236668) ; [a-maze.games — Blueprint to Text (BP2AI) export-to-AI Unreal plugin](https://www.a-maze.games/blog/blueprint-to-text-bp2ai-export-to-ai-unreal-plugin)

### Real-world token burn benchmark (Blender MCP donut test)

A 2-hour session consumed 60% of a $200/month Claude Max 5x plan's session tokens for one donut scene; the final render still had sprinkles clipping through the plate, a coffee cup clipping into the donut (scale miscalibration), an unprompted redesigned "Bavarian pretzel" cup handle, an overexposed macro camera, and a magenta color wash appearing "right as the context window gave out." Token sinks: screenshot analysis iterations, command corrections after errors, texture loading, repeated camera adjustments. Verdict: not production-viable; "context accumulates fast when you're doing iterative creative work."

Source: [mindstudio.ai — Claude Blender MCP 60% tokens donut test results](https://www.mindstudio.ai/blog/claude-blender-mcp-60-percent-tokens-donut-test-results)

### MCP tool-definition overhead baseline

MCP tool definitions load into EVERY message: 100-500 tokens per tool; a practical multi-server dev setup carries 15,000-20,000 tokens of overhead (~10% of Claude's 200K context) before conversation begins. Recommended reductions: remove unused servers, project-level configs, trim verbose descriptions, tool filtering, per-task agent tool sets.

Source: [mindstudio.ai — Claude Code MCP server token overhead](https://www.mindstudio.ai/blog/claude-code-mcp-server-token-overhead)

### Screenshot/vision cost — 20x reduction precedent

StraySpark Blender MCP v2 always returned PNG: a 640x480 viewport render = 178,507 bytes. v3 defaults to JPEG under a "200 KB budget" = 8,420 bytes for the same render (~20x cheaper), making per-change visual verification economical. Core claim: "3D work fails silently without eyes — an agent can execute fifty geometrically valid operations and produce a mesh that looks like a melted shopping cart, and every tool call will have returned success." The vision feedback loop is called "the single most important capability" in a Blender MCP server.

Source: [StraySpark blog — Blender MCP server v3](https://www.strayspark.studio/blog/blender-mcp-server-v3-blender-5x-rewrite-404-tools) ; [StraySpark blog — Unreal vs Blender vs Godot MCP comparison 2026](https://www.strayspark.studio/blog/unreal-vs-blender-vs-godot-mcp-comparison-2026)

### Tool-count vs context bloat — catalog mode precedent

StraySpark: "a server that exposes hundreds of tools naively dumps tens of thousands of tokens of schema into every session." Their Unreal server's catalog mode cuts fresh-session tool-definition cost ~95% (≈3K tokens instead of ≈60K). Blender v3 registers 404 tools but exposes only 131 by default, with `describe_tools(query=)`, `enable_tool_category()`, and `set_tool_profile()` for on-demand discovery; showing all tools at once also "degraded the model's ability to select appropriate ones."

Source: [StraySpark — Unreal MCP server product page](https://www.strayspark.studio/products/unreal-mcp-server) ; [StraySpark blog — Blender MCP server v3](https://www.strayspark.studio/blog/blender-mcp-server-v3-blender-5x-rewrite-404-tools)

### No rollback/undo — half-applied changes

Pre-v3 agents "had no mechanism to undo sequences of operations when intermediate steps failed, leaving users to repair half-applied changes manually"; v3 added a session category with checkpoints/rollback. The ahujasid/blender-mcp README warns: `execute_blender_code` is "potentially dangerous... ALWAYS save your work before using it." Unreal contrast: "real transaction system" with per-tool undo and Read/Scene/Destructive tool scopes.

Source: [StraySpark blog — Blender MCP server v3](https://www.strayspark.studio/blog/blender-mcp-server-v3-blender-5x-rewrite-404-tools) ; [github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) ; [StraySpark blog — Unreal vs Blender vs Godot MCP comparison 2026](https://www.strayspark.studio/blog/unreal-vs-blender-vs-godot-mcp-comparison-2026)

### Arbitrary exec() security/prompt-injection exposure

Issue #207: `execute_blender_code` runs LLM-supplied Python via `exec()` with "no sandboxing, validation, or restriction"; prompt injection can be embedded in `.blend` files or scene descriptions; `get_viewport_screenshot` reads arbitrary file paths and deletes files; `generate_hyper3d_model_via_images` reads arbitrary local files for upload to external APIs. Separately, the blender-mcp maintainer's GitHub account was hacked (HN story, 24 points) — supply-chain trust friction.

Source: [github.com/ahujasid/blender-mcp/issues/207](https://github.com/ahujasid/blender-mcp/issues/207) ; [news.ycombinator.com/item?id=49238028](https://news.ycombinator.com/item?id=49238028)

### Transport reliability failures (blender-mcp issue tracker)

Dominant issue classes: "Incomplete JSON response received" — 51-byte truncated payloads then 40s timeout, MCP error `-32001` (issues #219, #256); "Consistent ~5 minute delay on every tools/call" — persistent-connection recv logic stalling until internal timeout before falling back to a fresh connection (#279); Claude Desktop no longer connecting (#144, #137, #2, #15, #73); `FastMCP.__init__()` unexpected keyword `description` — dependency version mismatch (#142); Windows-specific: "invalid trailing data" from stdio text mode, the Blender subprocess inheriting the MCP server's stdio pipe causing timeouts, and "spawn node ENOENT" with `fnm`/`nvm`/`asdf`.

Source: [github.com/ahujasid/blender-mcp/issues/219](https://github.com/ahujasid/blender-mcp/issues/219) ; [github.com/ahujasid/blender-mcp/issues/279](https://github.com/ahujasid/blender-mcp/issues/279) ; [glama.ai — claudekit-blender-mcp TROUBLESHOOTING.md](https://glama.ai/mcp/servers/@olbboy/claudekit-blender-mcp/blob/e9ba0b47fccae95e42a1145d1909df47e1d0c792/docs/TROUBLESHOOTING.md)

### unreal-mcp setup/version friction

chongdashu/unreal-mcp is marked "EXPERIMENTAL... breaking changes without notice, incomplete features, outdated documentation, production use not recommended"; it requires a C++ plugin (TCP server on port `55557`) plus a Python MCP server. Issues: #43 "modules missing or built with a different engine version: UnrealMCP... cannot be compiled while the engine is running" (no resolution posted); #31 UE 5.6 compatibility; #48 `FindObject` must become `FindFirstObjectSafe` for UE 5.5+; #27 users sharing precompiled binaries for 5.6; #35 Linux unsupported question; #32 "Unable to start."

Source: [github.com/chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) ; [github.com/chongdashu/unreal-mcp/issues/43](https://github.com/chongdashu/unreal-mcp/issues/43)

### Session/context loss and scene re-description

3daistudio review: "Long sessions on a busy file get slow and expensive, and the assistant starts losing track of what it already did"; every operation and scene inspection consumes context. The community built compensating MCP servers: Claude Continuity (persistent memory in `~/.claude_states` to survive token-limit resets) and Context Travel (save/restore agent context). A Blender crash requires manual reconnection of the whole chain.

Source: [3daistudio.com — Blender MCP comparison guide](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/blender-mcp) ; [glama.ai — claude-continuity](https://glama.ai/mcp/servers/@donthemannn/claude-continuity) ; [mindstudio.ai — Claude Blender MCP real-world performance](https://www.mindstudio.ai/blog/claude-blender-mcp-real-world-performance)

### Quality ceiling complaints (output not usable)

Most common disappointment: organic subjects "come out as an assembly of stretched spheres and cubes... not a prompting problem, a limit of building geometry through scripted operators." HN (deng): generated models are tri-based instead of quads — "a showstopper" for refinement/UV-unwrapping/subdivision. No baked PBR maps or sensible UV layout; boolean-heavy output has n-gons, poles, uneven density; Geometry Nodes workflows are "brittle"; spatial placement needs multiple correction rounds. Works acceptably: hard-surface/architectural primitives, batch renaming/exports, material application.

Source: [3daistudio.com — Blender MCP comparison guide](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/blender-mcp) ; [news.ycombinator.com/item?id=44622374](https://news.ycombinator.com/item?id=44622374) ; [mindstudio.ai — Claude Blender MCP real-world performance](https://www.mindstudio.ai/blog/claude-blender-mcp-real-world-performance)

### Long-operation stalls

StraySpark: Blender "main-thread freezes" occur with naive MCP implementations; operator context quirks fail depending on active object state; in UE, long operations (lighting builds, remeshing) stall agents without background-task support; "anything without a scriptable API stays off-limits" (e.g., UE 5.8 Mesh Terrain). Hermes Agent's blender-mcp skill doc advises: one logical step per `execute_blender_code` call because "large monolithic scripts hit the bridge timeout," write large extractions (full hierarchy, animation data) to `/tmp/*.json` instead of returning through MCP, keep 2 KiB headroom on images vs the response size limit, and always call `get_scene_info` first — "never assume the scene is empty."

Source: [StraySpark blog — Unreal vs Blender vs Godot MCP comparison 2026](https://www.strayspark.studio/blog/unreal-vs-blender-vs-godot-mcp-comparison-2026) ; [hermes-agent.nousresearch.com — creative-blender-mcp skill doc](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/creative/creative-blender-mcp)

### Users' explicit wishes (feature requests)

blender-mcp #111: a user cannot disable PolyHaven/Hyper3D tools — "it somehow always tries to use both of those features" despite prompting (the LLM over-triggers on exposed tools; no per-tool disable). #14: use with any LLM API instead of Claude's website; #69 Cline support; #7 Cursor support; BlenderGPT #73: local models (Ollama). unreal-mcp #28: convert Blueprints to C++ via MCP; #26 UMG widget tools; #38 runtime project manipulation. Epic forum: auto-translate between Blueprints and C++; agents verifying against actual project files; LLM output rendered as visual BP diagrams. HN (mattigames): fatigue with "half-way-there automations," wants full autonomy.

Source: [github.com/ahujasid/blender-mcp/issues/111](https://github.com/ahujasid/blender-mcp/issues/111) ; [github.com/chongdashu/unreal-mcp/issues](https://github.com/chongdashu/unreal-mcp/issues) ; [forums.unrealengine.com — Using LLMs to learn Blueprints](https://forums.unrealengine.com/t/using-llms-to-learn-blueprints/1973345)

### Official first-party MCP servers now exist (landscape shift)

Epic ships "Unreal MCP in Unreal Editor" in UE 5.8: Experimental, HTTP/SSE only at `http://127.0.0.1:8000/mcp`, loopback-only, no auth, "many features are incomplete or missing. APIs and data formats are subject to change"; tools via a Toolset Registry (actor spawn/inspect, transforms, lighting, material instances, Slate inspection, automation tests, custom Python/C++ tools); Live Coding cannot add new `UFUNCTION`s (full editor restart required). Blender now has an official MCP add-on (`projects.blender.org/lab/blender_mcp`, `blender.org/lab/mcp-server`), causing migration churn from ahujasid's community version and documentation drift ("exact commands differ between the original community project and Blender's own official server").

Source: [dev.epicgames.com — Unreal MCP in Unreal Editor](https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor) ; [hydroxide.dev — Blender MCP + Claude Code](https://hydroxide.dev/articles/blender-mcp-claude-code/) ; [3daistudio.com — Blender MCP comparison guide](https://www.3daistudio.com/3d-generator-ai-comparison-alternatives-guide/blender-mcp)

### Alternative architectures already exploring the space

runreal/unreal-mcp uses UE's built-in Python Remote Execution protocol (UE 5.4+) — no C++ plugin, no engine-version recompiles, ~16 tools, full UE Python API access, but it grants "full access to your Editor." The 6xvl/blender-mcp fork advertises "~270 direct-dispatch tools, hang detection, forced auto-update." tahooki/unreal-blender-mcp offers a single server controlling both apps. Godot contrast (StraySpark): text-based `.tscn` files allow meaningful project editing without the editor running — a structural advantage UE/Blender lack.

Source: [github.com/runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) ; [github.com/6xvl/blender-mcp](https://github.com/6xvl/blender-mcp) ; [github.com/tahooki/unreal-blender-mcp](https://github.com/tahooki/unreal-blender-mcp) ; [StraySpark blog — Unreal vs Blender vs Godot MCP comparison 2026](https://www.strayspark.studio/blog/unreal-vs-blender-vs-godot-mcp-comparison-2026)

### Setup friction summary (community MCP bridges)

Two-part installs (DCC add-on + separate MCP server process) with client-specific config files per AI client; blender-mcp requires `uv` installed via the official installer (not pip), Blender 3.0+, Python 3.10+; 15-30 min typical setup; "do not run multiple MCP server instances simultaneously"; telemetry is on by default (`DISABLE_TELEMETRY=true` to opt out); the Poly Haven integration "may be unreliable"; troubleshooting advice amounts to "restart both Claude and Blender."

Source: [github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) ; [mindstudio.ai — Claude Blender MCP real-world performance](https://www.mindstudio.ai/blog/claude-blender-mcp-real-world-performance)

## Recommendations for TEE

1. Version-aware API firewall: at handshake, introspect the live Blender/UE version and validate every generated `bpy`/`unreal` call against the actual runtime API (`hasattr`/`dir`/reflection) BEFORE execution; on mismatch, return a one-line fix hint from a curated version-diff table (e.g. "`use_auto_smooth` removed in 4.1 -> use Smooth by Angle modifier") instead of a raw traceback — this converts multi-round retry loops (the top token sink) into single-shot corrections.
2. Transactional execution with automatic checkpoints: wrap every mutating call in Blender undo-push/temp-file snapshot and UE `FScopedTransaction`; expose checkpoint/rollback tools so agents can revert half-applied multi-step sequences (StraySpark v3 and UE's transaction scopes prove feasibility; blender-mcp's "ALWAYS save your work" shows the gap).
3. Replace raw `exec()` as the primary interface with a curated set of typed, parameterized tools (create/modify/query with schemas), keeping exec behind an explicit opt-in with AST validation, import/path allowlists, and no file-system reach — this addresses both the hallucination surface and blender-mcp issue #207's injection/exfiltration findings.
4. Lazy tool catalog: expose ~20-40 core tool schemas plus a `search_tools`/`enable_category` mechanism for the rest; precedent shows ~95% reduction in per-session tool-definition cost (3K vs 60K tokens) and better tool-selection accuracy than dumping 100+ schemas.
5. Differential scene state: maintain a server-side scene graph with stable object IDs; return only deltas since the last query, with depth/field filters and pagination; spill full dumps (hierarchies, animation data) to disk files and return path + compact summary — never stream large JSON through the MCP response (fixes the truncated-JSON/timeout classes #219/#256 and "assistant loses track of what it already did").
6. Cheap programmatic "eyes" before pixels: server-side geometric assertions returning text (bounding-box overlap/clipping detection, watertightness, poly counts, camera-frustum containment, name-position tables) so the agent only requests images when geometry checks pass — directly targets the donut-test failure modes (clipping, scale, framing) that burned 60% of a Max plan.
7. Budgeted vision when images are needed: JPEG under a fixed byte budget (~8-16KB for 640x480, the proven 20x saving vs PNG), region-of-interest crops, optional multi-view low-res contact sheets, and a diff-image mode (highlight what changed since the last capture).
8. Blueprint text codec: bidirectional compact-JSON <-> UE Blueprint serialization (T3D clipboard format) with a `describe_graph` read-back tool so agents verify every graph edit ("an agent that can read a Blueprint back after editing catches its own mistakes; one that can't is editing blind"); this is the most-requested and least-served UE capability.
9. Persistent cross-session project memory: an on-disk state file (scene fingerprint, naming conventions, engine version, done/todo log) auto-injected as a compact preamble on reconnect, so users never re-describe the scene after a crash, context compaction, or new chat — community demand is proven by the Claude Continuity / Context Travel servers.
10. Async job API for long operations: submit/poll/cancel semantics for renders, bakes, lighting builds, remeshing, plus heartbeats — eliminates the `-32001` timeout and 5-minute-stall class (#279, #50) and main-thread freeze complaints.
11. Bulletproof transport: length-prefixed binary-safe framing (fixes Windows stdio "invalid trailing data" and 51-byte truncated JSON), no stdio inheritance by DCC subprocesses, auto-reconnect with state resync, single-instance locking, and a one-command doctor/install (avoid the `uv`/node/`fnm` ENOENT and two-part-install failure modes that dominate issue trackers).
12. Ship per-project tool profiles and hard tool disables (users cannot currently stop Claude from over-invoking PolyHaven/Hyper3D — issue #111), plus client-agnostic operation (any MCP client, LLM-API and local-model use), which are explicit standing requests.
13. Track the first-party servers as moving targets: design TEE as a token-efficiency layer that can front Epic's UE 5.8 MCP (HTTP/SSE, incomplete toolsets) and Blender's official add-on rather than competing on raw tool count — the differentiators users actually lack are token economy, verification loops, rollback, and session persistence.
