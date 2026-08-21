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

## Headline numbers worth remembering

- Tool definitions can eat 20–40% of a 200K context (~710 tokens/tool);
  deferred loading cuts definition tokens ~85%; code-execution-with-MCP
  measured up to 98.7% total reduction. (04)
- A 1920×1080 screenshot ≈ 2,691 tokens; a budgeted ~1024×576 JPEG ≈ 777;
  geometric text assertions cost a few dozen. (04)
- Raw scene dumps stop scaling around ~120 objects; a real user burned 60% of
  a $200/mo plan in 2 hours on one donut scene without these mitigations. (04, 05)
