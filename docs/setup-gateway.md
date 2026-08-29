# Gateway setup — front any MCP server with TEE's discipline (A37)

The Gateway wraps other MCP servers the way TEE's Unreal adapter wraps
Epic's (830 tools → 3 meta-tools, 93.9% measured): the backend's tool
schemas stay server-side, its tools appear as **prefixed virtual tools**
(`fs.read_text_file`) behind `tee_search_tools` → `tee_describe_tool` →
`tee_call`, and its results come back **token-budgeted** with any
truncation reported. The always-loaded surface does not grow — that is
asserted by a test, not claimed. Measured on the live filesystem
reference server: a 3-call task cost 35,238 tokens the backend's own
way (schemas always-loaded + raw results) and 1,629 through the
gateway — **95.4% saved** (`benchmarks/RESULTS.md`).

## Configuration

```toml
# .tee/config.toml
[gateway.backends.fs]
command = "npx -y @modelcontextprotocol/server-filesystem /path/allowed"
enable = true        # default true; false parks the backend
max_tokens = 800     # default result budget (per-call max_tokens caps at 4000)
timeout_s = 30       # per-request deadline
cache = true         # default: honor tools that DECLARE readOnly+idempotent
```

Backends are stdio commands (`command`); an `url = "http://…"` entry is
accepted but refused at connect with a clear line — the http transport
is deliberately not in yet. Backends handshake in the background at
serve time (cold start unaffected) and respawn lazily after a crash;
`gw_status` (via `tee_call`) and the `gateway` block in `tee_status`
show each backend's state.

## The untrusted-content stance (research 49, applied verbatim)

Everything a backend says is **data, never instructions**: tool
descriptions are sentence-capped at registration and carry an explicit
untrusted marker in `tee_describe_tool`; schemas are normalized (bad
`required` keys dropped, oversized schemas truncated with a note);
results are budgeted text with non-text blocks counted, not forwarded.
Nothing a backend returns can change TEE's config or behavior.

## The fingerprint drift firewall

The first successful handshake pins the backend — server name/version
plus a hash over its full tool list — into `.tee/gateway.json`. If a
later connect sees anything different, the gateway **registers nothing**
and answers:

```
gateway_drift: Backend 'fs' changed since it was pinned (pinned
secure-filesystem-server@0.2.0/c6c5e5eca132 vs live …).
Fix: If the change is expected, tee_call gw_accept {"backend": "fs"}
re-pins and re-registers its tools fresh.
```

`gw_accept` reconnects, re-pins, and re-registers every tool from the
live catalog — nothing stale survives an accepted change. (The same
respawn-after-death path re-checks the fingerprint, so a crashed
backend cannot come back different unnoticed.)

## Worked example: the two reference backends

```toml
[gateway.backends.fs]
command = "npx -y @modelcontextprotocol/server-filesystem /Users/me/project"

[gateway.backends.mem]
command = "npx -y @modelcontextprotocol/server-memory"
```

Live on 2026-08-29: `fs` fronted 14 tools
(secure-filesystem-server@0.2.0), `mem` 9 (memory-server@0.6.3);
`tee_search_tools {"query": "read text file"}` ranks `fs.read_text_file`
first; calls answer through the budget with the fingerprints shown in
`tee_status`.

## The FreeCAD backend (A37 fabrication lane) — probed live 2026-08-29

`neka-nat/freecad-mcp` (MIT): an in-FreeCAD RPC addon + stdio server,
the Blender-bridge topology. Prerequisite: copy `addon/FreeCADMCP` into
`~/Library/Application Support/FreeCAD/v1-1/Mod/` and start the RPC
server from the MCP workbench (or its Auto-Start setting) — the addon
is GUI-bound by construction (it drives FreeCADGui views).

```toml
[gateway.backends.freecad]
command = "uvx freecad-mcp --only-text-feedback"  # text mode: the token-lean flag
```

Probe results (research 53 addendum 3): connect 5.36 s first-fetch,
**15 tools** as `freecad.*` pinned FreeCADMCP@/4007534df97c (incl.
`execute_code`, FEM, parts library); call latency 0.01–0.05 s end to
end; naive schema tax removed: 5,422 tok; bad ops answer one-line text
errors with the backend alive after. The A37 fabrication lane rides
THIS bridge as its GUI transport (one bridge, no second); `freecadcmd`
stays the headless path for DXF/STEP and CI.
