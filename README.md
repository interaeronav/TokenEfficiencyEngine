# Token Efficiency Engine (TEE)

An engine that helps **any AI** optimize its token usage and improve its work
efficiency.

TEE is an MCP server and API layer that sits between an AI model and the tools
it drives, with one overriding design goal: **complete the user's task with the
fewest tokens possible** — compact state, diff-based updates, batched
macro-commands, budgeted responses, and progressive disclosure of tool surface.
It ships today with two production adapters, **Unreal Engine** and **Blender**:
the proving ground where every pattern below is implemented and measured. The
kernel is tool-agnostic (see [docs/DECISIONS.md](docs/DECISIONS.md), A32); the
DCC knowledge lives entirely in the adapters.

## Why

AI models driving heavyweight tools (Unreal Engine and Blender are TEE's
proving ground) burn tokens on:

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
| donut-class modelling | 4,431 tok / 9 calls | 295 tok / 3 calls | 93.3% |
| 100 objects + what-changed | 49,283 tok / 23 calls | 5,311 tok / 3 calls | 89.2% |
| material pass, 10 objects | 11,590 tok / 22 calls | 980 tok / 2 calls | 91.5% |
| layout verification | 2,926 tok / 2 calls | 36 tok / 1 call | 98.8% |
| **total** | **68,230** | **6,622** | **90.3%** |

**Unreal** (live UE 5.8.1 editor, Epic's official MCP server; the naive side
is the workflow Epic's own `unreal-mcp` skill prescribes — `describe_toolset`
per toolset, then one `call_tool` per operation):

| Scenario | Naive | TEE | Saving |
|---|---|---|---|
| level population + Blueprint function | 38,331 tok / 32 calls | 2,346 tok / 4 calls | **93.9%** |

One `describe_toolset(BlueprintTools)` alone is ~18,000 tokens — more than six
times TEE's entire always-loaded tool surface.

Later phases added an extraction module (93.1% saved vs re-attaching media),
an app-side script lane (flat cost in loop length: 48% saved on a 5-round
fix loop, and the shaved per-round responses narrowed this from 63%), an
asset module (94.0% saved on find-select-place), plus design,
physics/modeling, and UEFN/Verse modules — see
[benchmarks/RESULTS.md](benchmarks/RESULTS.md) for all measured rows.

The always-loaded MCP surface (17 tools, including `tee_web_lookup`) costs
~2.0K tokens of definitions on the wire — under the price of 3 typical MCP
tools in the wild; 75+ further virtual tools (on the fake adapter;
adapter-specific lanes add more) load progressively through
`tee_search_tools`.

The same discipline now reaches beyond the DCCs: the **Gateway** fronts
any MCP stdio server through the existing meta-tools (95.4% measured on
the filesystem reference server), the **FreeCAD fabrication lane** turns
briefs into checked models, dimensioned drawing sheets and STEP/GLB
(92.4% per completed drawing-set), the **Home Builder joinery lane**
produces cut lists and dimensioned layouts with `joinery_check`'s
source-cited rules over the result, and every session can answer for
itself with the savings meter (`report_savings`) and a portable
`handoff` brief.

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
Local models: [docs/setup-local-llm.md](docs/setup-local-llm.md) ·
Problems: [docs/troubleshooting.md](docs/troubleshooting.md) ·
Security model: [docs/security.md](docs/security.md)

> Pre-release: support is best-effort via GitHub issues. The `tee`
> binary shares its name with coreutils `tee` — in shell pipelines the
> coreutils one wins your PATH; `tee doctor --emit` already accounts
> for this when generating client configs.

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
| pins | `pin_*` | marker actors carrying their own record (Unreal actor tags), filled from free asset sources, export/import across level rebuilds |
| kb | `kb_*` | read-only, budgeted queries over the Expert Knowledge Base mirror; every answer carries the corpus's own confidence/jurisdiction flags and its Sources block |

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
