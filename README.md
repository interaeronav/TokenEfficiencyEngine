# Token Efficiency Engine (TEE)

An AI token-efficiency engine for **Unreal Engine** and **Blender**.

TEE is an MCP server and API layer that sits between AI models (Claude) and the
two DCC tools, with one overriding design goal: **let the AI drive Unreal and
Blender with the fewest tokens possible** — compact scene state, diff-based
updates, batched macro-commands, and progressive disclosure of tool surface —
while mitigating the friction points users hit when pairing AI with these tools.

## Why

AI models interfacing with Unreal Engine and Blender burn tokens on:

- verbose scene dumps re-sent every turn,
- screenshots where structured text would do,
- chatty one-op-per-call tool traffic,
- hallucinated APIs that force retry loops,
- lost context that makes users re-describe their scene every session.

TEE attacks each of these at the protocol layer, so any MCP-capable model gets
the benefit without prompt engineering.

**Measured** (real headless Blender 5.2, same wire, TEE interface vs the
naive per-op-code + full-scene-dump pattern of existing bridges —
[benchmarks/RESULTS.md](benchmarks/RESULTS.md)):

| Scenario | Naive | TEE | Saving |
|---|---|---|---|
| donut-class modelling | 4,431 tok / 9 calls | 349 tok / 3 calls | 92.1% |
| 100 objects + what-changed | 49,283 tok / 23 calls | 6,585 tok / 3 calls | 86.6% |
| material pass, 10 objects | 11,590 tok / 22 calls | 1,420 tok / 2 calls | 87.7% |
| layout verification | 2,926 tok / 2 calls | 36 tok / 1 call | 98.8% |
| **total** | **68,230** | **8,390** | **87.7%** |

Later phases added an extraction module (92.6% saved vs re-attaching media),
an app-side script lane (63–76% saved on fix loops), an asset module (93.5%
saved on find-select-place), plus design, physics/modeling, and UEFN/Verse
modules — see [benchmarks/RESULTS.md](benchmarks/RESULTS.md) for all measured
rows.

The always-loaded MCP surface (16 tools) costs ~2.8K tokens of definitions —
about the price of 4 typical MCP tools in the wild; ~68 further virtual tools
load progressively through `tee_search_tools`.

## Scope

| Surface | Languages | Interfacing targets |
|---|---|---|
| Unreal Engine | C++, Blueprints, Python (editor), Verse | Python Editor Scripting, Remote Control API, commandlets |
| Blender | Python 3, OSL, GLSL, physics solvers | bpy, headless `--background`, live-session bridge add-on |

## Repository layout

```
CLAUDE.md                     Guidance for Claude Code sessions in this repo
CLAUDE_EXECUTION_SCRIPT.md    The master script Claude executes to build TEE
docs/research/                Deep-research findings that ground the build plan
server/                       MCP server + token-efficiency core (built by the script)
adapters/blender/             Blender-side bridge add-on (built by the script)
adapters/unreal/              Unreal-side bridge plugin/scripts (built by the script)
benchmarks/                   Token-consumption benchmarks (built by the script)
testbeds/                     Throwaway UE/Blender test projects (gitignored builds)
```

## Getting started (use TEE)

See **[docs/quickstart.md](docs/quickstart.md)**. Short version:

```bash
cd server
uv sync --extra extract --extra assets --extra physical
uv run tee doctor                    # diagnostics, every failure with a fix
uv run tee doctor --emit claude-code # ready-to-paste MCP client config
uv run tee serve --adapter fake      # explore with no DCC attached
```

Blender: [docs/setup-blender.md](docs/setup-blender.md) ·
Unreal: [docs/setup-unreal.md](docs/setup-unreal.md) ·
Problems: [docs/troubleshooting.md](docs/troubleshooting.md) ·
Security model: [docs/security.md](docs/security.md)

Packaged artifacts (`make -C server dist`): a pip/uv-installable wheel
(`tee-engine`; the CLI and module stay `tee`) and the Blender bridge
extension zip. Skills for Claude live under `skills/` (`tee-usage`,
`context-aware-assets`, `game-design`, `uefn`).

## Modules

| Module | Tools | What it does |
|---|---|---|
| kernel | `tee_*` | batches+diffs, checkpoints, script lane, budgets, memory, progressive disclosure |
| extract | `ex_*` | plans/photos/video/audio → content-addressed facts; ingest once, query forever |
| assets | `as_*` | license-gated free-asset search/import, scale policy, placement + sun, verification |
| design | `gd_*` | tee-design/1 spec, evidence tables, economy sim, ethics gates |
| physical | `sim_*`, `wall_*`… | tier-2 modeling ops, material facts, settle physics, plausibility findings |
| uefn | `uefn_*` | Verse digest facts + lint, Scene Graph vocabulary, Blender→UEFN export lane |

## Continuing the build (Claude)

The project is built *by Claude, in Claude Code*, driven by
`CLAUDE_EXECUTION_SCRIPT.md`. On the physical machine with Unreal/Blender:

1. Clone this repo and open it in Claude Code.
2. Tell Claude:

   > Read `CLAUDE_EXECUTION_SCRIPT.md` and execute it. Start from the first
   > phase that is not yet checked off in `docs/PROGRESS.md`.

The script is phased, resumable, and records progress, so sessions can stop and
continue without losing state — that is itself one of the friction points TEE
exists to fix. `docs/PROGRESS.md` carries the physical-machine ledger (Unreal
adapter, GPU generation lanes, GUI Blender validation, live UEFN proxy).
