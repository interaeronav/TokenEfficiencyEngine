# MCP Client Compatibility Matrix

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Research question

Which MCP protocol features that TEE's token-efficiency design depends on are actually honored by target clients (Claude Code, Claude Desktop, Cursor, the Claude API MCP connector): `notifications/tools/list_changed` for dynamic tool catalogs, `resource_link` results (are linked images fetched/rendered or ignored?), `structuredContent` + `outputSchema` handling (Claude Code issue #25081 shows `outputSchema` can cause ALL tools from a server to be silently dropped), elicitation, and whether API-side Tool Search Tool / `defer_loading` and Programmatic Tool Calling apply to MCP-server-provided tools or only to API-defined tools?

Several load-bearing recommendations (lazy/toggleable tool catalog, out-of-band screenshots via resource links, structured results for PTC-style filtering, 85% definition-token savings via `defer_loading`) are only real if the client implements them; the `outputSchema` bug proves these assumptions can fail catastrophically. The answer determines whether TEE's progressive-disclosure layer is built on protocol features (`list_changed`, resource links) or on client-agnostic meta-tools (`search_tools`/`get_tool_detail`, inline downscaled images) — two different architectures and test matrices.

## Summary

TEE's progressive-disclosure layer cannot be built on MCP protocol features alone: of the four target clients, only Claude Code honors `notifications/tools/list_changed` (Claude Desktop parses and discards it, Cursor requires a manual refresh, and the API MCP connector supports only tool calls — no notifications, resources, prompts, or elicitation). `resource_link` tool results are silently ignored by Claude Code (issue #53453, closed not-planned) and explicitly unsupported by the Anthropic SDK's MCP conversion helpers, so out-of-band screenshots via resource links are dead on arrival; inline base64 images are the only portable path, and they are capped by Claude Code's `MAX_MCP_OUTPUT_TOKENS` (default 25k).

The `outputSchema`/`structuredContent` surface is actively hazardous: beyond issue #25081 (all tools silently dropped), open 2026 issues show Claude Code dropping text blocks when `structuredContent` is present (#79944), Claude Desktop silently failing to dispatch calls for tools with `outputSchema` (#80105), and one malformed `inputSchema` still dropping every tool from a server (#88049, #82949).

On the API side, `defer_loading` DOES apply to MCP-connector tools (via `mcp_toolset` `default_config`/`configs`) with an officially claimed 85%+ definition-token reduction, but Programmatic Tool Calling explicitly excludes MCP-connector tools — PTC works only if TEE registers its UE/Blender operations as first-party custom tools in its own harness.

Net: TEE should be architected on client-agnostic meta-tools (`search_tools`/`get_tool_detail`, inline downscaled images, text-duplicated structured results), treating protocol features as per-client enhancements — with the note that Claude Code already ships its own client-side ToolSearch that defers all MCP tools by default, which TEE's catalog design should cooperate with (names + ≤2KB descriptions/server-instructions are what get indexed).

## Findings

### tools/list_changed — Claude Code

Officially supported: "Claude Code supports MCP list_changed notifications, allowing MCP servers to dynamically update their available tools, prompts, and resources without requiring you to disconnect and reconnect." Since v2.1.214 a failed refresh keeps the previous tool list (before that, a transient error replaced the server's tools with an empty list). On the v2 runtime (v2.1.232+, MCP TS SDK 2.0, protocol rev `2026-07-28`) `list_changed` arrives over a held-open stream with reconnect limits: 3 reopens if the stream dies within 10s, and after 5 reopens/hour a ~6-hour backoff — during backoff the tool list is stale until manual `/mcp` reconnect.

Source: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Dynamic tool updates, Notification streams on the v2 runtime)

### tools/list_changed — Claude Desktop

NOT honored. Issue #50339 (verified on v1.2773.0 and v1.3109.0): Desktop's bundled `directMcpHost.js` passes empty client capabilities at all 5 MCP client construction sites, never wires the SDK's `list_changed` handler, and captures the tools array in a frozen `const` — the notification is parsed and discarded; catalog stays stale until full app restart. Closed as not planned/invalid (filed against the claude-code repo). Feature request #39901 (refresh without restart) confirms the pain point.

Source: [github.com/anthropics/claude-code/issues/50339](https://github.com/anthropics/claude-code/issues/50339); [github.com/anthropics/claude-code/issues/39901](https://github.com/anthropics/claude-code/issues/39901)

### tools/list_changed — Cursor

Not acted on mid-session. Cursor forum threads report `notifications/tools/list_changed` is ignored and users must click the manual refresh button in MCP settings; Cursor's official MCP docs list tools/prompts/resources/roots/elicitation but never claim `list_changed` support. Cursor also has a ~40-tool practical limit across all MCP servers (docs: "performs optimally within 40"; community reports only the first 40 tools are sent to the model), still in place per July 2026 reports.

Source: [forum.cursor.com/t/mcp-notifications-tools-list-changed-not-acted-on-mid-session/161459](https://forum.cursor.com/t/mcp-notifications-tools-list-changed-not-acted-on-mid-session/161459); [forum.cursor.com/t/mcp-client-update-tools/77294](https://forum.cursor.com/t/mcp-client-update-tools/77294); [github.com/cursor/cursor/issues/3369](https://github.com/cursor/cursor/issues/3369); [cursor.com/docs/context/mcp](https://cursor.com/docs/context/mcp)

### tools/list_changed — Claude API MCP connector

N/A by design: the connector is stateless per request; "Of the feature set of the MCP specification, only tool calls are currently supported." Tool list is re-fetched per Messages API request, and the validation rules explicitly tolerate dynamic availability ("If a tool name in configs doesn't exist on the MCP server, a backend warning is logged but no error is returned — MCP servers may have dynamic tool availability"). No notifications, resources, prompts, sampling, or elicitation. HTTP/SSE only; no stdio. Beta header `mcp-client-2025-11-20`; not ZDR-eligible; not on Bedrock or Google Cloud.

Source: [platform.claude.com/docs/en/agents-and-tools/mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (Limitations, Validation rules)

### tools/list_changed — spec status

The spec makes `list_changed` a SHOULD for servers that declared `listChanged`, and in protocol rev `2026-07-28` it is delivered only to clients that opened a `subscriptions/listen` stream with `toolsListChanged: true` — clients are never REQUIRED to refresh. Ignoring it is spec-legal, which is why TEE cannot assume it.

Source: [modelcontextprotocol.io/specification/2026-07-28/server/tools.md](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md) (List Changed Notification)

### resource_link — Claude Code

Silently ignored. Issue #53453 (v2.1.117, closed as not planned, no maintainer response): `resource_link` items in tool results are dropped with no fetch, no display, no error; base64 PDF blobs and Office-document embedded resources are also not processed; only `image/png` and `image/jpeg` confirmed working among binary types. Companion issue #72271 (forward `EmbeddedResource` blob to API content blocks) also closed not-planned. Server authors' workaround in the wild: sniff `user-agent: Claude-User` and return plain HTTP URLs as text instead. Only mitigation: Claude Code auto-provides `ListMcpResourcesTool`/`ReadMcpResourceTool`, so the MODEL can choose to read a URI via `resources/read` — model-initiated, never automatic, and the spec notes tool-returned links are not guaranteed to be listed in `resources/list`.

Source: [github.com/anthropics/claude-code/issues/53453](https://github.com/anthropics/claude-code/issues/53453); [github.com/anthropics/claude-code/issues/72271](https://github.com/anthropics/claude-code/issues/72271); [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Use MCP resources)

### resource_link — Claude API side

The Anthropic SDK MCP helpers (`mcpResourceToContent` etc.) "throw UnsupportedMCPValueError if an MCP value isn't supported by the Claude API… This can happen with unsupported content types, MIME types, or resource links (resolve resource links with your MCP client before converting)." The MCP connector itself supports tool calls only, so a `resource_link` inside an `mcp_tool_result` is at best inert text. Spec language is permissive anyway: a tool MAY return links whose URI "can be subscribed to or fetched by the client" — no client obligation exists.

Source: [platform.claude.com/docs/en/agents-and-tools/mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (Client-side MCP helpers → Error handling); [modelcontextprotocol.io/specification/2026-07-28/server/tools.md](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md) (Resource Links)

### Images in MCP tool results — token behavior

Inline base64 `ImageContent` is the working path but has sharp edges. Claude Code caps MCP tool output at `MAX_MCP_OUTPUT_TOKENS` (default 25,000 tokens, warning at 10,000); the `_meta['anthropic/maxResultSizeChars']` annotation (up to 500,000 chars) raises the limit for TEXT only — "The annotation has no effect on tools that return image content; for those, raising MAX_MCP_OUTPUT_TOKENS is the only option." Oversized results are persisted to disk and replaced with a file reference. Issue #31208 (closed not planned, Mar 2026, Jupyter server) reported `ImageContent` being treated as base64 text (~15k–25k tokens/image vs ~1.6k as a native image block, 10–20x waste) in at least some paths; #88298 (open, Aug 2026) reports screenshots intermittently dropped from multi-block results; #53256 shows claude.ai/Desktop render tool-result images collapsed behind a manual expander (model sees them, user doesn't). Cursor docs explicitly support base64 images in tool responses ("MCP servers can return images — screenshots, diagrams, etc.").

Source: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (MCP output limits); [github.com/anthropics/claude-code/issues/31208](https://github.com/anthropics/claude-code/issues/31208); [github.com/anthropics/claude-code/issues/88298](https://github.com/anthropics/claude-code/issues/88298); [github.com/anthropics/claude-code/issues/53256](https://github.com/anthropics/claude-code/issues/53256); [cursor.com/docs/context/mcp](https://cursor.com/docs/context/mcp)

### outputSchema — the drop-all-tools failure (issue #25081)

Claude Code 2.1.38: `tools/list` entries carrying the MCP 2025-11-25 fields `outputSchema`, `title`, or `toolAnnotations` caused ALL tools from the server to silently fail registration (server shows connected, resources work, zero tools, no error). Closed as not planned. Related: #24742 (`claude mcp serve` outputSchema), #10031 (outputSchema missing `type` field), #2682 (tools unavailable despite connection). Workaround was removing the new fields server-side; `structuredContent` in RESPONSES could stay enabled.

Source: [github.com/anthropics/claude-code/issues/25081](https://github.com/anthropics/claude-code/issues/25081)

### Silent drop-all-tools failure class is still alive (Aug 2026)

The parser-fragility class behind #25081 persists in current Claude Code: #88049 (open, Aug 19 2026) — ONE non-object tool `inputSchema` silently drops ALL tools from an HTTP server, no error on either side; #82949 (open, Jul 31 2026) — a boolean JSON Schema at a named property breaks MCP proxy construction, all of the server's tools dropped (notes #50194 "still reproduces, wrong root cause"). Separately, tools whose input schema has a ROOT-level `anyOf`/`oneOf`/`allOf` are now flattened with description rewriting (v2.1.195+); before v2.1.195 every such tool was skipped. Design consequence: TEE must treat its `tools/list` payload as running on a brittle parser — plain object schemas, no root combinators, and schema-validity CI against Claude Code specifically.

Source: [github.com/anthropics/claude-code/issues/88049](https://github.com/anthropics/claude-code/issues/88049); [github.com/anthropics/claude-code/issues/82949](https://github.com/anthropics/claude-code/issues/82949); [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Tool input schemas with a root-level combinator)

### structuredContent handling — Claude Code

Claude Code surfaces `structuredContent` to the model, but issue #79944 (open, Jul 2026): when a tool result contains BOTH a text block and `structuredContent`, the text block is silently dropped and only `structuredContent` reaches the model (the same server response works fully in Cursor). #86032 (open): on error results (`isError:true`) `structuredContent` is dropped, leaving the model an unactionable string. The spec's backwards-compat rule (server SHOULD duplicate `structuredContent` as serialized JSON in a `TextContent` block) therefore does NOT protect you in Claude Code — the `structuredContent` object itself must carry the complete payload.

Source: [github.com/anthropics/claude-code/issues/79944](https://github.com/anthropics/claude-code/issues/79944); [github.com/anthropics/claude-code/issues/86032](https://github.com/anthropics/claude-code/issues/86032); [modelcontextprotocol.io/specification/2026-07-28/server/tools.md](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md) (Structured Content)

### outputSchema — Claude Desktop call-time failure

Issue #80105 (open, Jul 2026, Claude Desktop 1.24012.1): MCP tool calls for tools that declare `outputSchema` fail silently CLIENT-side — the `tools/call` request is never dispatched to the server. So on Desktop, `outputSchema` is hazardous at call time, not just at list time.

Source: [github.com/anthropics/claude-code/issues/80105](https://github.com/anthropics/claude-code/issues/80105)

### Elicitation support matrix

Claude Code CLI: supported since v2.1.76 (released Mar 14 2026) — form mode (dialog with server-defined fields) and URL mode (browser flow), plus an Elicitation hook for scripted auto-response; a call waiting on an open elicitation dialog is exempted from auto-backgrounding. Known open bug #85442: remote Streamable-HTTP form elicitation never reaches the client in some setups (no dialog, server times out at -32001) despite `elicitation.form` advertised at initialize. Claude Desktop: NOT supported — open feature request #41110 and claude-ai-mcp #153. Cursor: docs list elicitation as supported ("Server-initiated requests for additional information from users"). API MCP connector: not supported (tool calls only).

Source: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Respond to MCP elicitation requests); [claudelab.net/en/articles/claude-code/mcp-elicitation-support](https://claudelab.net/en/articles/claude-code/mcp-elicitation-support); [github.com/anthropics/claude-code/issues/85442](https://github.com/anthropics/claude-code/issues/85442); [github.com/anthropics/claude-code/issues/41110](https://github.com/anthropics/claude-code/issues/41110); [cursor.com/docs/context/mcp](https://cursor.com/docs/context/mcp)

### Tool Search Tool (API) — scope and savings

GA on the Claude API (no beta header). Two server-side variants: `tool_search_tool_regex_20251119` (Python `re.search` patterns, ≤200 chars) and `tool_search_tool_bm25_20251119` (natural language, ≤500 chars). Models: Sonnet 4.5, Haiku 4.5, Opus 4.5 and everything later (Opus 4.6–5, Sonnet 4.6, Fable 5, Mythos 5); Opus 4.1 and earlier unsupported. Official savings claim: a typical 5-server setup consumes ~55k tokens of definitions; "Tool search typically reduces this by over 85 percent, loading only the 3–5 tools Claude needs"; selection accuracy degrades past 30–50 upfront tools. Mechanics: full definitions still sent server-side every request; deferred tools excluded from the system-prompt prefix; discovered tools appended as `tool_reference` blocks (cache-preserving). Limits: ≥1 tool must stay non-deferred (400 "All tools have defer_loading set" otherwise); max 10,000 deferred tools; default 5 results, limit 1–10,000; `defer_loading` + `cache_control` on the same tool = 400. Search is not separately metered.

Source: [platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)

### defer_loading DOES apply to MCP-connector tools

Explicit in both docs: "If your tools come from MCP servers through the MCP connector, you don't set defer_loading on individual tool definitions. Instead, set it once on the mcp_toolset entry's default_config for the whole server, or per tool in its configs." The `mcp_toolset` config object supports `enabled` (default true) and `defer_loading` (default false) per tool with precedence `configs` > `default_config` > system defaults. So API-side progressive disclosure covers MCP-served tools fully — TEE's 85% `defer_loading` saving is real on the API path.

Source: [platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) (MCP integration); [platform.claude.com/docs/en/agents-and-tools/mcp-connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (MCP toolset configuration)

### Custom client-side tool search (portable API pattern)

The API also supports a client-implemented search path: any custom tool may return `tool_reference` content blocks (`{type:'tool_reference', tool_name:'…'}`) inside a standard `tool_result`, and the API expands them into full definitions, provided every referenced tool exists in the top-level `tools` array (normally with `defer_loading:true`). This lets TEE implement embedding/semantic search server-side while keeping API-managed expansion and cache preservation — the exact meta-tool (`search_tools`) architecture, but with first-class API support.

Source: [platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) (Custom tool search implementation)

### Programmatic Tool Calling excludes MCP tools

PTC docs, Tool restrictions: "The following tools cannot be called programmatically: Tools provided by an MCP connector; the computer use and browser use toolsets…". PTC requires `code_execution_20260120` (Opus 4.5+/Sonnet 4.5+/Sonnet 4.6/5, Opus 4.6–5, Fable 5, Mythos 5 — no Haiku); enabled per tool via `allowed_callers:['code_execution_20260120']`; incompatible with `strict:true`, forced `tool_choice`, `disable_parallel_tool_use`, and recursive `$ref` schemas (400 "Circular $ref detected"); responses to pending programmatic calls must contain ONLY `tool_result` blocks; `allowed_callers` is guidance, not a security boundary. Measured gains: +11% avg on BrowseComp/DeepSearchQA with 24% fewer input tokens. Not available on Amazon Bedrock or Google Cloud; Foundry requires Hosted-on-Anthropic. Consequence for TEE: PTC-style filtering over UE/Blender results only works if TEE's harness registers operations as first-party custom tools (its own bridge executing them), not via `mcp_servers`/`mcp_toolset`.

Source: [platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) (Model compatibility, The allowed_callers field, Constraints and limitations)

### Claude Code's built-in client-side ToolSearch (default-on MCP deferral)

Claude Code already implements TEE-style progressive disclosure for ALL MCP servers: tool search is enabled by default; only tool NAMES and server instructions load at session start; Claude discovers definitions via a `ToolSearch` meta-tool. Tool descriptions and server instructions are truncated at 2KB each. Opt-outs/opt-ins: `ENABLE_TOOL_SEARCH=false` (all upfront), `auto` / `auto:N` (defer once definitions exceed N% of context, default 10%), per-server `alwaysLoad:true` in config, per-tool `_meta['anthropic/alwaysLoad']:true`. Disabled automatically on non-first-party `ANTHROPIC_BASE_URL` proxies (`tool_reference` blocks not forwarded), Azure-hosted Foundry deployments (server-side rejection), and pre-4.5-generation models. Failed server connections and needs-auth states are reported to Claude through ToolSearch results. No fixed per-server tool cap — "the practical limit is your context window budget."

Source: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Scale with MCP tool search, Configure tool search, Exempt a server from deferral)

### MCP connector schema fidelity bugs (API path)

Two open issues show the API MCP connector intermittently corrupting typed parameters: #86933 (Aug 2026) — structured array params delivered as JSON-encoded strings, strict servers reject with `-32602` despite a typed `inputSchema`; #83772 (Aug 2026) — connector publishes an array param intermittently as string, then constrained sampling makes writes impossible. TEE servers behind the connector should accept both encodings defensively (parse string-encoded JSON for array/object params) rather than hard-rejecting.

Source: [github.com/anthropics/claude-code/issues/86933](https://github.com/anthropics/claude-code/issues/86933); [github.com/anthropics/claude-code/issues/83772](https://github.com/anthropics/claude-code/issues/83772)

### Claude Desktop feature surface (for the matrix)

Desktop supports MCP tools, prompts (prompts menu), and resources (attach/reference UI) via local stdio config and Desktop Extensions, plus claude.ai connectors — but not `list_changed` (#50339), not elicitation (#41110), and has the open `outputSchema` call-dispatch bug (#80105). Tool-result images render collapsed by default in Desktop/claude.ai (#53256). The old modelcontextprotocol.io/clients feature matrix page no longer exists (redirects to the homepage); per-client capability claims now have to come from each vendor's docs and issue trackers.

Source: [github.com/anthropics/claude-code/issues/50339](https://github.com/anthropics/claude-code/issues/50339); [github.com/anthropics/claude-code/issues/41110](https://github.com/anthropics/claude-code/issues/41110); [github.com/anthropics/claude-code/issues/80105](https://github.com/anthropics/claude-code/issues/80105); [github.com/anthropics/claude-code/issues/53256](https://github.com/anthropics/claude-code/issues/53256); [modelcontextprotocol.io/clients](https://modelcontextprotocol.io/clients) (now redirects)

### Spec ground truth on the contested features

Per the `2026-07-28` spec: (1) `resource_link` — tools MAY return links; client fetch is optional; links not guaranteed to appear in `resources/list`; (2) `structuredContent` — "For backwards compatibility, a tool that returns structured content SHOULD also return the serialized JSON in a TextContent block"; servers MUST make structured results conform to `outputSchema`, clients only SHOULD validate; (3) `outputSchema` is optional metadata — nothing in the spec licenses dropping tools that carry it (Claude Code's behavior was a client bug, not spec ambiguity); (4) new in 2026-07-28: `InputRequiredResult` / multi-round-trip tool calls embedding elicitation inside `tools/call` — client support across the ecosystem is not yet established; (5) servers SHOULD return tools in deterministic order explicitly to enable client caching and LLM prompt-cache hits.

Source: [modelcontextprotocol.io/specification/2026-07-28/server/tools.md](https://modelcontextprotocol.io/specification/2026-07-28/server/tools.md)

### Claude Code misc constraints relevant to TEE tool/result design

MCP tool timeouts: per-server `timeout` field (ms) or `MCP_TOOL_TIMEOUT` (default ~28h wall clock); separate 60s per-request first-byte timer for HTTP servers (raised only by setting `timeout` ≥60s); idle timeout 5 min HTTP / 30 min stdio (`CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`); main-conversation MCP calls still running at 2 min auto-move to background tasks (v2.1.212+). `_meta['anthropic/requiresUserInteraction']:true` forces a permission prompt on every call (v2.1.199+). Discovery cache (v2.1.221+, `MCP_DISCOVERY_CACHE`) can serve a server's tool list from a previous session without connecting — another reason server-pushed catalog changes may not be seen at startup. Claude Code v2 runtime negotiates protocol `2026-07-28` with servers that support it (v2.1.232+).

Source: [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) (Tips, Automatic backgrounding, Require approval for a specific tool, Server status detail, MCP client runtimes)

## Recommendations for TEE

1. Build TEE's progressive-disclosure layer on client-agnostic meta-tools (`search_tools` / `get_tool_detail` / `invoke_tool` with a small always-visible core), not on `notifications/tools/list_changed`: of the four targets only Claude Code honors `list_changed` (Desktop discards it, Cursor needs a manual refresh, the API connector has no notification concept). A stable tool catalog whose CONTENT is dynamic (meta-tool dispatch) works identically everywhere and also survives Claude Code's discovery cache and stream-backoff windows.
2. Ship two deployment profiles because the API path and the client path have different winning mechanisms: (a) MCP-server profile for Claude Code/Desktop/Cursor — rely on Claude Code's built-in default-on ToolSearch (names + server instructions only in context) and TEE meta-tools for the others; (b) first-party harness profile for the Claude API — register UE/Blender operations as plain custom tools with `defer_loading:true` + `tool_search_tool_bm25_20251119` (85%+ definition-token savings, GA) AND `allowed_callers:['code_execution_20260120']` for PTC-style batch/filtered execution, which is impossible for MCP-connector tools.
3. Do not use `resource_link` for screenshots or any payload: Claude Code silently drops it (issue #53453, closed not-planned) and the Anthropic SDK helpers throw on it. Return screenshots as inline base64 `ImageContent`, downscaled server-side (target well under Claude Code's 25k-token `MAX_MCP_OUTPUT_TOKENS` since `anthropic/maxResultSizeChars` does not apply to images; ~1080p JPEG ≈ 1.6k tokens as a native image block). Optionally ALSO expose the full-resolution capture as an MCP resource URI in text so the model can pull it via `ReadMcpResourceTool` on demand — model-initiated, never assumed.
4. Treat `outputSchema` as radioactive in the default build: omit `outputSchema`, `title`, and `toolAnnotations` from `tools/list` (Claude Code #25081 drop-all history; Claude Desktop #80105 still silently fails to dispatch calls for `outputSchema`-bearing tools). Keep `structuredContent` in RESPONSES (that part is safe and preferred by Claude Code), but make the `structuredContent` object fully self-sufficient — Claude Code currently drops the sibling text block when `structuredContent` is present (#79944) and drops `structuredContent` on `isError` results (#86032), so put error detail in text and success detail in `structuredContent`, never split one payload across both.
5. Lint TEE's `tools/list` output against the drop-all-tools failure class before every release: every `inputSchema` must be a plain JSON object (`type:'object'`), no boolean schemas at named properties (#82949), no non-object schemas (#88049 — one bad tool kills the whole server's catalog with no error), no root-level `anyOf`/`oneOf`/`allOf` (only flattened since Claude Code v2.1.195). Add an integration test that connects real Claude Code and asserts the expected tool COUNT, since this failure mode is silent by nature.
6. Keep the exposed tool surface small and searchable: ≤40 tools for Cursor's hard practical limit, tool descriptions and server instructions ≤2KB each (Claude Code truncates beyond that), front-load key search terms, use a consistent name prefix (e.g. `ue_`, `bl_`) so one regex/BM25 search retrieves the whole group, and write server instructions as "when to search for these tools" guidance — Claude Code indexes exactly names + instructions when tools are deferred.
7. Make elicitation strictly optional sugar (confirmation of destructive UE/Blender operations on Claude Code CLI and Cursor only); provide a parameter-based fallback (e.g. `confirm:true`) because Claude Desktop and the API connector have no elicitation, and remote-HTTP form elicitation has an open delivery bug even in Claude Code (#85442). For must-confirm operations in Claude Code, `_meta['anthropic/requiresUserInteraction']:true` (v2.1.199+) is the more reliable primitive.
8. If TEE is ever driven through the API MCP connector, parse defensively: accept array/object parameters that arrive as JSON-encoded strings (#86933/#83772) instead of rejecting with `-32602`, keep to Streamable HTTP (stdio unsupported, SSE deprecated), and remember the connector is not ZDR-eligible and unavailable on Bedrock/Google Cloud.
9. Define the test matrix as client × {catalog visibility after server-side change, `resource_link` handling, image round-trip within token limits, `structuredContent`+text both present, `outputSchema` present, elicitation, `defer_loading`/PTC} with Claude Code CLI (v2 runtime), Claude Desktop, Cursor, and a raw Messages API harness as the four columns — the research shows every one of these cells has at least one client-specific surprise, and the silent failure modes (tool drops, content drops) can only be caught by asserting on observed tool counts and model-visible content, not on server logs.
