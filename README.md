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

## Getting started

The project is built *by Claude, in Claude Code*, on the physical machine where
Unreal Engine and/or Blender are installed. To start (or resume) the build:

1. Clone this repo on the target machine and open it in Claude Code.
2. Tell Claude:

   > Read `CLAUDE_EXECUTION_SCRIPT.md` and execute it. Start from the first
   > phase that is not yet checked off in `docs/PROGRESS.md`.

The script is phased, resumable, and records progress, so sessions can stop and
continue without losing state — that is itself one of the friction points TEE
exists to fix.
