# Token Efficiency Techniques

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Summary

Token efficiency in LLM-to-tool workflows is now well-quantified: MCP tool definitions routinely eat 20-40% of context (measured: 82K tokens / 41% of a 200K window from a handful of servers; ~710 tokens/tool average), and Anthropic's three published mitigations are the Tool Search Tool (`defer_loading`: 85% definition-token reduction, 72K → 8.7K), Programmatic Tool Calling (intermediate results stay in a sandbox: 37% reduction, 43,588 → 27,297 tokens), and the "code execution with MCP" pattern (tools as code APIs on a filesystem with progressive disclosure: 98.7% reduction, 150K → 2K tokens).

On the results side, Claude Code caps MCP tool output at 25,000 tokens by default and Anthropic's tool-writing guidance prescribes pagination/filtering/truncation, semantic IDs over UUIDs, and a `response_format` concise/detailed enum (measured 206 → 72 tokens on a Slack example). Claude API levers with hard numbers: prompt caching (0.1x reads, 1.25x/2x writes, 4 breakpoints, 512-4096 token minimum prefix), context editing (`clear_tool_uses_20250919`: 84% token reduction in a 100-turn web-search eval; +39% task performance combined with the memory tool), server-side compaction (`compact-2026-01-12`, 150K default trigger), and `count_tokens` for measurement.

For scene state, screenshots are expensive (⌈w/28⌉×⌈h/28⌉ visual tokens; a 1920x1080 screenshot is ~2,691 tokens on high-res-tier models) versus compact JSON scene-graph summaries, and existing Blender/UE MCP servers (blender-mcp; chongdashu/sam-david/runreal unreal-mcp) already converge on "send Python code once" (`execute_blender_code` / UE Python Remote Execution) as the macro-command channel, with research (SceneCraft, 3DGraphLLM) showing scene-graph-as-blueprint plus code generation scales to ~100-asset scenes where raw dumps hit context limits around 120 objects.

## Findings

### Code execution with MCP (progressive disclosure)

Anthropic engineering blog (November 2025, Adam Jones & Conor Kelly): presenting MCP servers as code APIs on a filesystem (e.g. `./servers/google-drive/getDocument.ts`) instead of direct tool calls cut a workflow from ~150,000 tokens to ~2,000 tokens (98.7% reduction). Agents read tool definitions on-demand by exploring the filesystem; a `search_tools` function can take a detail-level parameter (name only / name+description / full schema). Intermediate data (e.g. a 50,000-token meeting transcript that would otherwise pass through context twice) is filtered/transformed in the execution environment; only final output reaches the model. The pattern also enables state persistence to files, a `./skills/` directory of reusable functions, and PII tokenization so sensitive data never transits the model.

Source: [https://www.anthropic.com/engineering/code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Tool definition context cost (quantified)

Anthropic "advanced tool use" post: a five-server setup (GitHub, Slack, Sentry, Grafana, Splunk) consumes ~55K tokens before the conversation starts; Anthropic's internal tool definitions were 134K tokens pre-optimization; 50+ MCP tools ≈ 72K tokens loaded traditionally vs ~8.7K with the Tool Search Tool (85% reduction, preserving 95% of context). Independent measurement (Scott Spence, Claude Code): multiple MCP servers consumed 82.0K tokens = 41% of a 200K window on a blank conversation; one 20-tool server was 14,114 tokens (~710 tokens/tool average).

Source: [https://www.anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use); [https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)

### Tool Search Tool (Claude API)

Server tools `tool_search_tool_regex_20251119` / `tool_search_tool_bm25_20251119`: mark other tools `defer_loading: true` and Claude discovers/loads schemas on demand. Deferred tools are excluded from the initial prompt and appended (not swapped) on discovery, preserving the prompt cache. Accuracy on MCP-heavy evals improved: Opus 4 49% → 74%, Opus 4.5 79.5% → 88.1%. Anthropic recommends it when tool definitions exceed ~10K tokens or with 10+ tools. Constraint: the search tool itself must not be deferred and at least one tool must be non-deferred (else 400).

Source: [https://www.anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use); claude-api skill (bundled Anthropic reference)

### Programmatic Tool Calling (PTC)

Claude writes Python in the `code_execution` container that calls your tools as functions; results return to the running script, not to model context — only the script's final output hits context. Measured: 37% token reduction on complex research tasks (43,588 → 27,297 tokens average) plus accuracy gains (internal knowledge retrieval 25.6% → 28.5%; GIA 46.5% → 51.2%). Enable by declaring `code_execution_20260120` and setting `allowed_callers: ["code_execution_20260120"]` on custom tools (older beta form: `code_execution_20250825` + `advanced-tool-use-2025-11-20` header). Best for 3+ dependent calls, parallel ops, or large intermediate datasets. Incompatible with `strict:true`, forced `tool_choice`, and MCP-connector tools.

Source: [https://www.anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use); claude-api skill

### Tool result size guidance + Claude Code default cap

Anthropic "writing tools for agents": implement pagination, range selection, filtering, and truncation with sensible defaults for any tool that could return large responses. Claude Code restricts tool responses to 25,000 tokens by default; the cap is configurable via the `MAX_MCP_OUTPUT_TOKENS` env var (warning displayed at 10,000 tokens; error text: "MCP tool response exceeds maximum allowed tokens (25000). Please use pagination, filtering, or limit parameters"). Per-tool override annotation: `anthropic/maxResultSizeChars`. Truncation messages should steer the agent toward token-efficient strategies (many small targeted queries instead of one broad one).

Source: [https://www.anthropic.com/engineering/writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents); [https://code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp)

### Response format design (quantified)

The same Slack thread returned as "detailed" = 206 tokens vs "concise" = 72 tokens (~1/3) by dropping technical identifiers (`thread_ts`, `channel_id`, `user_id`). Recommendation: expose a `response_format` enum on tools ("concise" ~500 tokens vs "detailed" ~2000 tokens). Resolving opaque UUIDs to semantically meaningful names significantly improves retrieval precision — return names/paths, not raw GUIDs. There is no universal best serialization (JSON/XML/Markdown) — evaluate per task. Consolidate multi-call workflows into single tools (`schedule_event` instead of `list_users` + `list_events` + `create_event`).

Source: [https://www.anthropic.com/engineering/writing-tools-for-agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

### Tool use examples (`input_examples`)

Providing realistic `input_examples` arrays on tool definitions (minimal, partial, and full parameter variants) improved accuracy from 72% to 90% on complex parameter handling in Anthropic's evals — a cheap way to reduce failed/retried tool calls (each retry re-bills the whole context).

Source: [https://www.anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use)

### MCP spec: tool results and resource links

MCP 2025-06-18 tool results support content types: text, image (base64 + `mimeType`), audio, `resource_link` (`type: "resource_link"` with `uri`/`name`/`description`/`mimeType` — returns a URI the client can fetch or subscribe to instead of inlining data), and embedded resource. `resource_link` is the spec-native mechanism for "return a pointer, not the payload". Results also support annotations (`audience: [user|assistant]`, `priority` 0-1, `lastModified`), letting servers mark content as user-display-only so clients can keep it out of model context.

Source: [https://modelcontextprotocol.io/specification/2025-06-18/server/tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

### MCP spec: structured output and pagination

Tools may declare `outputSchema` (JSON Schema); servers MUST return conforming `structuredContent` (a JSON object field alongside `content`; for backwards compat it is also serialized into a `TextContent` block — note this doubles bytes on the wire unless the client dedupes). `tools/list` supports cursor-based pagination (`params.cursor` / `result.nextCursor`) plus `listChanged` notifications, enabling incremental tool disclosure. Tool errors are in-band: `isError: true` with `content`, not JSON-RPC errors.

Source: [https://modelcontextprotocol.io/specification/2025-06-18/server/tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

### Prompt caching economics (Claude API)

`cache_control {type: "ephemeral"}`: reads cost ~0.1x the base input price; writes 1.25x (5-min TTL) or 2x (1-hour TTL, `ttl: "1h"`). Max 4 breakpoints per request; caching is a strict byte-prefix match over tools → system → messages, so tool-set changes or a timestamp in the system prompt invalidate everything downstream. The minimum cacheable prefix is model-dependent: 512 tokens (Opus 5/Fable 5), 1024 (Opus 4.8/Sonnet 5/Sonnet 4.6), up to 4096 (Opus 4.6/Haiku 4.5). Breakpoints look back a maximum of 20 content blocks — long agentic turns need intermediate breakpoints (~every 15 blocks). Verify via `usage.cache_read_input_tokens` / `cache_creation_input_tokens`. `max_tokens: 0` requests pre-warm the cache. For agents: put stable content (system prompt, deterministic sorted tool list) first, volatile state last; append per-turn breakpoints on the last message block.

Source: claude-api skill `shared/prompt-caching.md` (bundled Anthropic reference)

### Context editing / tool-result clearing (Claude API)

Beta `context-management-2025-06-27`, `context_management.edits` on `client.beta.messages`. `clear_tool_uses_20250919` defaults: trigger `{type:'input_tokens', value:100000}`, keep `{type:'tool_uses', value:3}`, `clear_at_least` null, `exclude_tools` `[]`, `clear_tool_inputs` false; cleared results are replaced with a placeholder the model can see. `clear_thinking_20251015` clears thinking blocks (must be listed first when combining). The response reports `applied_edits` with `cleared_input_tokens`; `count_tokens` can preview post-clearing size (`context_management.original_input_tokens` vs `input_tokens`). Caveat: clearing invalidates the prompt-cache prefix at the clearing point — use `clear_at_least` to make each invalidation worthwhile. Anthropic-measured: 84% token reduction on a 100-turn web-search eval; memory tool + context editing = +39% agent performance vs baseline.

Source: [https://platform.claude.com/docs/en/build-with-claude/context-editing](https://platform.claude.com/docs/en/build-with-claude/context-editing); [https://claude.com/blog/context-management](https://claude.com/blog/context-management)

### Server-side compaction (Claude API)

Beta `compact-2026-01-12` (Fable 5, Opus 5/4.8/4.7/4.6, Sonnet 5/4.6): the API auto-summarizes earlier context when approaching a trigger threshold (default 150K tokens) into a compaction block. The client must append the full `response.content` (including compaction blocks) back into `messages` — extracting only text silently loses compaction state. Distinct from context editing (clearing) — compaction summarizes, editing deletes.

Source: claude-api skill (bundled Anthropic reference)

### Other Claude API cost levers

- Message Batches API: async processing at 50% of standard cost (`POST /v1/messages/batches`).
- Token Counting: `POST /v1/messages/count_tokens` is a free pre-flight measurement endpoint (use it, not tiktoken — Claude has its own tokenizer).
- Files API (beta `files-api-2025-04-14`): upload once, reference by `file_id` so image/PDF bytes aren't re-sent in every request payload of a multi-turn conversation.
- `output_config.effort` (low/medium/high/xhigh/max, GA): lower effort = fewer, more consolidated tool calls and terser output — a direct token-spend knob for agentic loops.
- Structured outputs: `output_config.format` constrains response shape; `strict: true` on tool definitions guarantees schema-valid `tool_use.input` (eliminates malformed-call retries).
- Current models (Fable 5, Opus 5, Sonnet 5, etc.) have 1M-token context windows; mid-conversation `{role:'system'}` messages (Opus 5/4.8/Fable 5) inject instructions without invalidating the cached prefix.

Source: claude-api skill (bundled Anthropic reference, cached 2026-06)

### Image/screenshot token cost (quantified)

Claude counts images as 28x28-pixel patches: tokens = ⌈width/28⌉ × ⌈height/28⌉ (legacy rule of thumb: width*height/750). Two tiers: high-resolution (Claude 4.7+ models) max long edge 2576px / 4784 visual tokens; standard (older) 1568px / 1568 tokens. Concrete costs: a 1920x1080 screenshot = 2,691 tokens on the high-res tier (1,560 on standard after downscale); 3840x2160 = 4,784 tokens (high-res) — i.e. one 1080p viewport screenshot ≈ 2.7K tokens vs a ~100-500-token JSON scene summary. High-res can be ~3x the visual tokens of standard for the same image; Anthropic advises downsampling before sending when fidelity isn't needed. Max 8000x8000px; more than 20 images per request triggers a stricter ~2000px per-image limit; computer-use `tool_result` images are rejected (not downscaled) if oversized. The API supports up to 600 images/request, but base64 in history bloats every turn — use the Files API `file_id`.

Source: [https://platform.claude.com/docs/en/build-with-claude/vision](https://platform.claude.com/docs/en/build-with-claude/vision)

### blender-mcp (ahujasid) architecture

The de-facto standard Blender MCP integration (community plugin, works with Claude Desktop/Cursor): a Blender addon (`addon.py`) runs a socket server inside Blender on TCP `9876`; a Python MCP server (`src/blender_mcp/server.py`, FastMCP) translates MCP calls into socket commands. Core tools: `get_scene_info` (scene summary), `get_object_info(name)` (per-object detail on demand — a two-level progressive disclosure of scene state), `get_viewport_screenshot`, `execute_blender_code` (arbitrary `bpy` Python — the macro-command channel, unsandboxed), plus Poly Haven asset tools. Pattern: coarse scene summary + per-object drill-down + code execution, verified by `get_scene_info` after build steps.

Source: [https://github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)

### Unreal Engine MCP servers (survey)

- chongdashu/unreal-mcp: UE 5.5+ C++ editor plugin exposing actions over TCP port `55557` + external Python FastMCP server; tools for actors, Blueprint creation/editing, Blueprint node graphs, viewport control.
- sam-david/unreal-mcp: 127 tools across 16 subsystems (actor 10, asset 16, blueprint 12, material 13, sequencer 8, niagara 8, testing 8, etc.) over 4 transports — UE built-in Python Remote Execution (UDP multicast + TCP, port `6776`), Remote Control HTTP REST (port `30010`), optional C++ plugin bridge (TCP `55557`, auto-fallback to Python), and UAT/UBT subprocess; ~95% of functionality needs no custom C++ plugin (UE 5.3+; note 5.3+ requires Multicast Bind Address `0.0.0.0`).
- runreal/unreal-mcp: pure Python-Remote-Execution based.
- ChiR24/Unreal_mcp: TypeScript + native C++ automation bridge.

Source: [https://github.com/chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp); [https://github.com/sam-david/unreal-mcp](https://github.com/sam-david/unreal-mcp); [https://github.com/runreal/unreal-mcp](https://github.com/runreal/unreal-mcp)

### UE native remote surfaces (no-plugin control planes)

Unreal's built-in Remote Control plugin serves HTTP on port `30010` (`/remote/object/call` to invoke UFunctions, property get/set via JSON; also WebSockets; LAN-only per Epic security guidance). The built-in Python Editor Script Plugin provides Python Remote Execution over UDP multicast + TCP — the send-a-script-once channel equivalent to Blender's `execute_blender_code`. These two built-ins are what lets an MCP bridge run arbitrary batched editor operations with one round trip instead of N tool calls.

Source: [https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine); [https://github.com/sam-david/unreal-mcp](https://github.com/sam-david/unreal-mcp)

### Scene-state representation research

SceneCraft (arXiv 2403.01248): an LLM agent synthesizes Blender scenes up to ~100 assets by first building a scene graph blueprint (spatial relations as a relational graph), then emitting Blender Python that translates relations into numerical layout constraints; dual-loop refinement uses rendered-image critique by a VLM; a library-learning mechanism compiles recurring script functions into a reusable library (45.1%/40.9% CLIP-score improvement over BlenderGPT on synthetic/real sets). 3DGraphLLM (ICCV 2025) and SceneGPT (arXiv 2408.06926): 3D scene graphs serialized as JSON lists (per-object: id, bounding-box center/extent, semantic tag, caption) are the compact LLM-consumable scene encoding; documented failure mode: scenes with >~120 object nodes exceeded GPT-4-class context limits — motivating summarization/IDs/drill-down instead of full dumps.

Source: [https://www.emergentmind.com/papers/2403.01248](https://www.emergentmind.com/papers/2403.01248); [https://arxiv.org/html/2408.06926v1](https://arxiv.org/html/2408.06926v1); [3DGraphLLM (ICCV 2025 paper)](https://openaccess.thecvf.com/content/ICCV2025/papers/Zemskova_3DGraphLLM_Combining_Semantic_Graphs_and_Large_Language_Models_for_3D_ICCV_2025_paper.pdf)

### Tool consolidation results (real-world)

Scott Spence (mcp-omnisearch, Claude Code): consolidating 20 tools into 8 parameterized tools, trimming descriptions, and standardizing parameter names (`query`/`limit`/`provider`) cut definition cost 14,214 → 5,663 tokens (~60%) with identical functionality. Confirms Anthropic guidance that fewer, parameterized, well-named tools beat many granular ones.

Source: [https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)

### Agent context-management pattern taxonomy (Anthropic)

Anthropic's agent-design guidance distinguishes: context editing (prune stale tool results within a session), compaction (summarize when nearing the window), and the memory tool (`memory_20250818` — cross-session persistence via a client-implemented `/memories` directory). Long-running agents use all three. Cache-safe dynamic behavior: use tool search (appends, doesn't swap, tool schemas), mid-conversation system messages, and subagents on cheaper models for reading-heavy subtasks rather than mid-session model/tool-set changes (which invalidate the cache).

Source: claude-api skill `shared/agent-design.md` (bundled Anthropic reference)

## Recommendations for TEE

1. Make server-side code execution the primary channel: expose one `execute_python`-style macro tool per host (Blender `bpy` via TCP addon like blender-mcp:`9876`; UE via built-in Python Remote Execution / Remote Control HTTP:`30010`) so N editor operations cost one round trip. Anthropic's measured precedent: PTC saves 37%, code-execution-with-MCP saves 98.7% vs chatty per-op tool calls.
2. Keep the always-loaded tool surface tiny (roughly 8-15 consolidated, parameterized tools, not 100+). Budget: each tool ~300-700 tokens; 50+ tools ≈ 72K tokens. Use Claude's Tool Search Tool with `defer_loading: true` for the long tail (85% definition-token reduction, cache-preserving), or TEE's own two-level catalog (`list_capabilities` → `get_tool_detail`) for non-Claude clients — mirroring MCP cursor pagination and the code-execution filesystem pattern.
3. Represent scene state as a compact JSON scene-graph summary with progressive disclosure: `get_scene_summary` returns counts + object IDs/names/types/bounds (target <500 tokens); `get_object_detail(id)` drills down; return semantically meaningful names, never raw UUIDs/GUID paths (Anthropic-measured precision gain). Never dump full scenes — research shows raw scene graphs blow context around ~120 objects.
4. Return diffs, not dumps, after mutations: every write tool should respond with only what changed (created/modified/deleted IDs + new transforms), plus a monotonically increasing scene revision number so the model knows its cached mental model's freshness. Give every read tool `limit`/`offset`/`filter` parameters with small defaults, and cap responses ~25K tokens (Claude Code's default) with truncation messages that instruct the model to narrow the query.
5. Add a `response_format` (`'concise'|'detailed'`) enum on read tools — concise ~500 tokens, detailed ~2000, per Anthropic guidance (their Slack example: 206 → 72 tokens by dropping internal identifiers).
6. Treat screenshots as a last resort priced explicitly: a 1920x1080 viewport screenshot ≈ 2,691 tokens on Claude 4.7+ (⌈w/28⌉×⌈h/28⌉ patches). Have TEE downsample viewport captures (e.g. 1024x576 ≈ 777 tokens) by default, offer resolution as a parameter, and prefer text-based scene verification (bounds checks, raycast queries, object counts) over render-and-look loops. Use MCP `resource_link` (or Files API `file_id`) to pass full-resolution images by reference instead of inline base64.
7. Design the request prefix for prompt caching: frozen system prompt + deterministically sorted tool list first, volatile scene state and per-turn data after the last `cache_control` breakpoint; never inject timestamps/session IDs early. Economics: 0.1x reads vs 1.25x writes, breakeven at 2 requests; place a breakpoint on the newest turn each request and add intermediate breakpoints every ~15 content blocks in tool-heavy turns (20-block lookback limit).
8. For long editing sessions on the Claude API, enable context editing (beta `context-management-2025-06-27`, `clear_tool_uses_20250919`) tuned for TEE: trigger ~30-50K `input_tokens`, keep 3-5 tool uses, `exclude_tools` for the scene-summary tool, `clear_at_least` ~5K to amortize cache invalidation — Anthropic measured 84% token reduction on 100-turn tool loops. Add compaction (`compact-2026-01-12`) as the fallback near the window; expose scene revision + a `get_full_state` tool so the model can resync after clearing.
9. Implement MCP `structuredContent` + `outputSchema` for machine-readable results (enables strict client-side validation and PTC-style in-code filtering), and set `isError: true` with actionable, token-efficient error text that names the fix ("use limit=20" rather than stack traces).
10. Ship `input_examples` on every tool (72% → 90% accuracy on complex parameters in Anthropic evals) — failed tool calls are the most expensive tokens because the entire context is re-billed on retry.
11. Instrument token spend from day one: use `POST /v1/messages/count_tokens` (free) to measure TEE's tool schemas and typical responses; track `usage.cache_read_input_tokens` to verify caching; log per-tool response sizes and alert when any tool's median response exceeds ~2K tokens.
12. Support macro/batch semantics even for non-code clients: a `batch_execute` tool accepting an array of typed operations (create/transform/material ops) executed atomically server-side, returning one aggregate diff — the middle ground between chatty single ops and raw Python for gated/auditable actions (per Anthropic's bash-vs-dedicated-tools guidance: promote to dedicated tools what needs gating, keep code execution for breadth).
