# VLM Extraction Channels

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

The MCP-sampling channel is effectively dead: neither Claude Code nor Claude Desktop implements `sampling/createMessage` (feature request anthropics/claude-code#1785 open since June 2025 with no commitment), and the MCP 2026-07-28 spec formally deprecated Sampling (SEP-2577) with the explicit migration path "integrate directly with LLM provider APIs"; the MCP Python SDK v2 now raises `NoBackChannelError` from `ctx.session.create_message` on modern connections.

That leaves two real channels for Phase 7 VLM extraction: (A) a server-owned Anthropic API key calling `messages.parse`/`count_tokens`/Files API directly (all confirmed current API surface), configured via the documented env mechanisms for stdio servers (`claude mcp add --env`, `.mcp.json` `${VAR}` expansion, `claude_desktop_config.json` `"env"`), or (B) in-band extraction by the host model writing back through a `store_facts` tool — which works in every client with zero config, but is billed inside the session (and in Claude Code image tool-results are capped by `MAX_MCP_OUTPUT_TOKENS`, default 25k).

Elicitation, by contrast, is alive: not deprecated, supported by Claude Code (form + URL modes) but NOT by Claude Desktop, and form mode is restricted to flat primitive-typed schemas — sufficient for a numeric/enum calibration question, impossible for point-on-image interactions.

The "zero token cost" claim survives only for local CV/parsing preprocessing; VLM passes cost either off-session dollars (key mode) or one-time in-session tokens amortized by the fact store (in-band mode).

## Findings

### MCP sampling deprecated in spec 2026-07-28

Sampling is Deprecated as of protocol revision 2026-07-28 (SEP-2577). The registry entry gives migration path = "Integrate directly with LLM provider APIs" and earliest removal = first revision released on or after 2027-07-28. The spec page carries the warning: "New implementations SHOULD NOT adopt it; existing implementations SHOULD migrate to integrating directly with LLM provider APIs." Roots and Logging were deprecated in the same SEP; `includeContext` `"thisServer"`/`"allServers"` has been deprecated since 2025-11-25. Elicitation is ABSENT from the deprecated registry — it remains a live feature.

Source: [MCP deprecated registry (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/deprecated); [MCP sampling spec (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)

### Claude Code does not support MCP sampling

The official Claude Code MCP reference (code.claude.com/docs/en/mcp) documents tools, prompts, resources, elicitation, hooks, and output limits but never mentions sampling — it is not implemented. Feature request anthropics/claude-code#1785 ("[Feature Request] Support for MCP Sampling to leverage Claude Max subscriptions", filed 2025-06-08) is still OPEN (labels: `area:cost`, `area:mcp`, `enhancement`; assigned ashwin-ant) with no maintainer commitment. The Claude Code v2 runtime (>=2.1.232) is built on MCP TypeScript SDK 2.0 supporting protocol 2026-07-28 — the revision in which sampling is deprecated — so support is unlikely to ever land.

Source: [Claude Code MCP docs](https://code.claude.com/docs/en/mcp); [anthropics/claude-code#1785](https://github.com/anthropics/claude-code/issues/1785)

### Claude Desktop supports neither sampling nor elicitation

Per the (former) modelcontextprotocol.io client matrix and issue reports, Claude Desktop supports Resources/Prompts/Tools but not Sampling, Roots, or Elicitation. Issue anthropics/claude-code#41110 (filed 2026-03-30, closed as 'invalid'/not-Claude-Code) states: "Claude Code CLI supports MCP elicitation (elicitation/create), but the Claude Desktop app does not"; it references elicitation tracking issue #2799 (151 upvotes). Third-party servers work around Desktop's gap by falling back to native OS dialog boxes. So any TEE feature depending on sampling fails in BOTH first-party clients, and elicitation fails in Desktop.

Source: [anthropics/claude-code#41110](https://github.com/anthropics/claude-code/issues/41110); [MCP client matrix](https://modelcontextprotocol.info/docs/clients/); [mcpverdict.com Claude Desktop entry](https://mcpverdict.com/mcp/clients/claude-desktop/)

### MCP Python SDK v2 killed server-side sampling/elicitation calls

MCP Python SDK v2 (`pip install mcp`, 2.x): "Every server-initiated request is gone at 2026-07-28." `ctx.session.create_message()` and `ctx.elicit()` now raise `NoBackChannelError` on 2026-07-28 connections (they still work for legacy 2025-era clients). The replacement for elicitation is the `Resolve(fn)` parameter annotation returning `Elicit(...)` — "one tool body, both eras" — or manual `InputRequiredResult`/MRTR handling. FastMCP 4 (gofastmcp.com, jlowin/fastmcp) removed `ctx.sample()`/`ctx.sample_step()` entirely; its docs say the server should hold an API key, create a provider client, and await a completion inside the tool. Since TEE targets Python 3.11 + the official `mcp` package (per `CLAUDE.md`), building extraction on `create_message` would code against a dead API.

Source: [MCP Python SDK what's new](https://py.sdk.modelcontextprotocol.io/whats-new/); [FastMCP sampling docs](https://gofastmcp.com/servers/sampling); [Pydantic: MCP Python SDK v2 beta](https://pydantic.dev/articles/mcp-python-sdk-v2-beta)

### What sampling would have offered (for the record)

In clients that do implement it, `sampling/createMessage` supports content types text, image (base64 + `mimeType`), and audio — so image inputs were spec-legal. Params: `messages`, `modelPreferences` (advisory hints + cost/speed/intelligence priorities — the client makes the final model choice), `systemPrompt` (client MAY ignore), `temperature`, `maxTokens` (required, client MUST respect), `stopSequences`, `metadata`, and since 2025-11-25 `tools` + `toolChoice` (requires client `sampling.tools` capability). There is NO structured-output/`json_schema` field in sampling; the only schema-constrained path is forced tool use (`toolChoice {mode:"required"}` with one tool whose `inputSchema` is the output schema). The spec also mandates human-in-the-loop review UI (SHOULD), making it poor for unattended batch extraction even where supported. On 2026-07-28 it is delivered via MRTR `InputRequiredResult` rather than a server-to-client request.

Source: [MCP sampling spec (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)

### Server-owned API key channel: all digest recommendations confirmed current

The Anthropic Messages API surface presumed by the vlm-extraction digest exists and is current (per the bundled claude-api reference, cached 2026-06): structured outputs via `client.messages.parse()` (recommended) or `output_config: {format: {...}}` on `messages.create` (the old `output_format` param is deprecated); token preflight via `POST /v1/messages/count_tokens`; Files API beta `files-api-2025-04-14` (header required on both upload and the `messages.create` referencing the `file_id`; the image content block type must match the MIME type); prompt caching via `cache_control {type:"ephemeral"}` (min ~1024-token prefix, max 4 breakpoints); PDF input as document blocks (32 MB request, 600-page limit); Batches API at 50% cost for non-latency-sensitive extraction. All require a direct API credential. SDK credential resolution order: `ANTHROPIC_API_KEY` -> `ANTHROPIC_AUTH_TOKEN` -> OAuth profile from `ant auth login` -> WIF env vars, so a zero-arg `Anthropic()` in the server picks up inherited user credentials without TEE-specific key plumbing.

Source: Anthropic claude-api skill reference (2026-06 cache); [docs.claude.com API docs](https://docs.claude.com)

### API-key configuration mechanics for a stdio MCP server

Claude Code: `claude mcp add --env ANTHROPIC_API_KEY=... --transport stdio tee -- python -m tee_server` (multiple `KEY=value` pairs; `--` separates server argv); `.mcp.json` supports `${VAR}` environment-variable expansion in command/args/env explicitly "for machine-specific paths and sensitive values like API keys"; Claude Code also sets `CLAUDE_PROJECT_DIR` in the spawned server's env. Claude Desktop: `claude_desktop_config.json` `mcpServers.<name>.env` block (the official quickstart example passes `BRAVE_API_KEY` that way). So key management is a solved config problem in both clients — the cost is that extraction becomes online-only, billed to the server's key outside the host session, and fits TEE's existing async-job pattern (`submit_extract` -> poll job).

Source: [Claude Code MCP docs](https://code.claude.com/docs/en/mcp); [MCP: connect local servers](https://modelcontextprotocol.io/docs/develop/connect-local-servers)

### In-band channel: image tool results work but are capped and re-billed

MCP tool results may contain image content blocks and Claude Code supports them, but: Claude Code warns at 10,000 tokens of MCP tool output and hard-limits at 25,000 tokens by default (the `MAX_MCP_OUTPUT_TOKENS` env var raises it); the per-tool `anthropic/maxResultSizeChars` annotation exempts TEXT only — "The annotation has no effect on tools that return image content; for those, raising MAX_MCP_OUTPUT_TOKENS is the only option." A returned image also stays in session context for subsequent turns (prompt-cache read rates, until compaction). The better in-band design under Claude Code: have the HOST read the media file directly (Claude Code's built-in `Read` tool renders PNG/JPG/PDF natively, no MCP limit involved), then write extracted facts back via a TEE `store_facts` tool — the TEE server never ships image bytes through a tool result at all.

Source: [Claude Code MCP docs (MCP output limits and warnings section)](https://code.claude.com/docs/en/mcp)

### store_facts validation is compatible with decision A6

A6's `structured_output=False` concerns the MCP tool-result surface, not tool inputs. In the in-band channel the schema enforcement point is the `store_facts` tool's `inputSchema`: MCP clients validate tool arguments against it, and the server can reject invalid facts with a one-line fix message (TEE hard rule 6). This reproduces most of what `messages.parse` would give (schema-constrained extraction) without any API key, at the cost of the host model doing the extraction reasoning in-session. Note that MCP spec's own structured-output feature for tools (`outputSchema`/`structuredContent`, added 2025-06-18) remains opt-in and is what A6 already declined — nothing forces revisiting that.

Source: [MCP tools spec (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/server/tools); TEE decision A6 (project context)

### Elicitation: alive, Claude Code-only, primitives-only

Elicitation is NOT deprecated in 2026-07-28. Claude Code supports it end-to-end: form mode (auto-displayed dialog with server-defined fields) and URL mode (browser flow), plus an Elicitation hook for auto-response; the docs state "elicitation dialogs appear automatically when a server requests them." Form-mode `requestedSchema` is restricted to FLAT objects of primitives: string (formats `email`/`uri`/`date`/`date-time`, `min`/`maxLength`), number/integer (`min`/`max`), boolean, single-select enum (`enum` or `oneOf`+`const`/`title`), multi-select enum (array of `enum`/`anyOf`), all with optional defaults — "complex nested structures, arrays of objects ... are intentionally not supported." Servers MUST NOT request API keys/passwords via form mode (URL mode required). Implication for TEE's calibration fallback: "what is this dimension in mm?" or "pick the scale: 1:50/1:100" works in Claude Code; "click two points on the drawing" is impossible; and on Claude Desktop the whole mechanism is absent, so the fallback must degrade to defaults-plus-recorded-assumption.

Source: [MCP elicitation spec (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation); [Claude Code MCP docs](https://code.claude.com/docs/en/mcp)

### Protocol-era detail that keeps legacy elicitation working under Claude Code

Claude Code >=2.1.232 runs the v2 MCP runtime (TS SDK 2.0, protocol 2026-07-28) but negotiates the new revision only with HTTP/claude.ai-connector servers; STDIO servers connect on the legacy revision unless the user sets `MCP_PROTOCOL_NEGOTIATION=auto`. So a stdio TEE server today talks a 2025-era protocol to Claude Code, where elicitation is still a server->client request (Python SDK `ctx.elicit` works). Writing new code, TEE should still use the SDK v2 `Resolve(fn)`/`Elicit(...)` pattern, which the SDK routes correctly on both protocol eras, rather than `ctx.elicit`, which will raise `NoBackChannelError` once a client negotiates 2026-07-28 (MRTR `InputRequiredResult` + `requestState` replaces the back-channel).

Source: [Claude Code MCP docs (MCP client runtimes section)](https://code.claude.com/docs/en/mcp); [MCP Python SDK what's new](https://py.sdk.modelcontextprotocol.io/whats-new/)

### Cost-accounting truth table for the three channels

(1) Sampling: 0 additional user cost in theory (covered by subscription), but unavailable in both Anthropic clients and spec-deprecated — not a real option. (2) Server key: dollars billed to the key owner outside the session; supports Batches (-50%), caching, `count_tokens` preflight; works headless/unattended; requires network — breaks offline preprocessing claims for the VLM step only. (3) In-band host model: extraction tokens billed once inside the user's session (subscription or API, whatever the host runs on); media enters context once, facts persist in TEE's store, and later sessions read facts (tens of tokens) instead of media. An image is roughly `(w*h)/750` tokens on Claude vision, ~1.6k tokens for a 1092x1092 image; a full drawing set is tens of thousands. Only local CV/parsing (OpenCV, pdfplumber, etc.) is genuinely zero-token; Phase 7 language should say "extract once, amortize forever", not "zero token cost" for VLM passes.

Source: channel analysis grounded in the sources above + Anthropic vision token formula ([docs.claude.com vision](https://docs.claude.com))

## Recommendations for TEE

1. Eliminate MCP sampling as a Phase 7 channel now: it is unimplemented in Claude Code (issue #1785 open, no commitment) and Claude Desktop, deprecated in MCP 2026-07-28 with official guidance to "integrate directly with LLM provider APIs", and the Python SDK v2 raises `NoBackChannelError` from `ctx.session.create_message` on modern connections. Do not spend design budget on a sampling adapter.
2. Make in-band host-model extraction the default channel: TEE registers an extraction *prompt/workflow* plus a `store_facts` tool (schema-validated tool INPUT, consistent with A6's `structured_output=False` on results); under Claude Code the host reads the media itself (built-in `Read` tool renders images/PDFs with no MCP output limit), extracts, and calls `store_facts`; the fact store amortizes the one-time in-session cost across all later sessions. Never return image bytes as MCP tool results — they hit the 25k `MAX_MCP_OUTPUT_TOKENS` cap and the `maxResultSizeChars` annotation cannot exempt images.
3. Offer the server-owned API key as an opt-in "batch/offline-of-session" mode, not a requirement: if `ANTHROPIC_API_KEY` (or an ant-auth profile) is present in the server's env — configured via `claude mcp add --env`, `.mcp.json` `${VAR}` expansion, or `claude_desktop_config.json` env — enable a `submit_extraction` async job (reusing TEE's existing async-job pattern) that uses `messages.parse` + `output_config` `json_schema`, `count_tokens` preflight, Files API, Batches (-50%), and `cache_control` exactly as the vlm-extraction digest recommends. Absent a key, the module silently degrades to in-band mode; detect at startup and reflect in tool descriptions.
4. Build the calibration-question fallback on elicitation via the Python SDK v2 `Resolve(fn)`/`Elicit(...)` pattern (works across protocol eras), constrained to what form mode allows: flat primitive fields, numbers, and enums (e.g. "known dimension in mm", "scale 1:50/1:100/1:200"). Gate on the client's elicitation capability: Claude Code renders dialogs; Claude Desktop has none, so fall back to a recorded assumption plus a fact-store flag (`confidence: "assumed"`) the user can correct later. Never design a point-on-image calibration through elicitation — impossible by spec.
5. Rewrite Phase 7 cost claims: "zero token cost" applies only to local deterministic preprocessing (OpenCV, pdfplumber, ezdxf, etc.); VLM passes cost either off-session dollars (key mode) or a one-time in-session spend (in-band mode). Frame the metric as tokens-per-task amortization: media enters a model context exactly once, and every subsequent session queries facts at ~2 orders of magnitude fewer tokens.
6. Keep the module boundary channel-agnostic: a single `Extractor` interface with two drivers (`InBandDriver` = prompts + `store_facts` writeback; `ApiDriver` = async job + `messages.parse`), both writing to the same fact store with provenance (source file hash, extractor, model, confidence). This lets `benchmarks/` compare tokens-per-task across drivers and keeps the MCP tool surface identical regardless of channel.
