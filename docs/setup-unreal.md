# Unreal setup (physical machine)

The Unreal adapter (build Phase 3) requires a machine with UE 5.8+ — the
editor cannot run in a cloud container, so this page documents the
sanctioned route it will wire against.

## Primary route: Epic's first-party MCP plugin (UE 5.8+)

Decision A4: TEE proxies and extends the official `ModelContextProtocol`
plugin rather than shipping a custom C++ bridge (Epic named MCP a UE6
pillar; a from-scratch bridge is a dead end).

1. Enable the **ModelContextProtocol** and **AllToolsets** plugins in
   the project.
2. Auto-start the server: `bAutoStartServer=True` (project settings) or
   launch with `-ModelContextProtocolStartServer`.
3. The endpoint is loopback HTTP at `127.0.0.1:8000/mcp` — no
   authentication exists; never port-forward it
   ([security.md](security.md)).
4. `tee doctor` reports the endpoint when it is up.

TEE's proxy layer adds what the official surface lacks: typed batches,
diff responses, response budgets, TEE-owned checkpointing (5.8.1
disabled transaction bundling during tool scripts — Epic's undo cannot
be relied on), and version-gated toolset probing keyed on the engine
version + toolset catalog hash.

## Fallback route: UE 5.3–5.7

Remote Control API (HTTP :30010 / WS :30020) + Python remote execution
(UDP multicast 239.0.0.1:6766, TCP 6776) — pluginless and documented;
commandlets for headless work.

## UEFN (Fortnite)

UEFN is Windows-only, GUI-only, and its MCP toolsets are beta (enable
**Python Editor Scripting** + **UEFN MCP Toolsets** under Beta Access in
Project Settings). TEE's offline UEFN lanes (Verse digest facts +
linting, templates, export preflight) work everywhere today —
`uefn_status` reports the exact mode and remediation. See the `uefn`
skill.

## What lands with Phase 3 (build script §6)

The UE adapter over the proxy, `ue_*` virtual tools, UE scenarios in the
benchmark suite, and the UE content-plugin zip. Until then, `tee serve
--adapter unreal` answers that the adapter arrives in Phase 3.
