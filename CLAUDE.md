# CLAUDE.md — Token Efficiency Engine

## What this project is

TEE's mission is to help **any AI** optimize its token usage and improve its
work efficiency (A32) — refined by A39 into two pillars: make every exchange
small, and run work on the cheapest capable engine (AI resource management
between metered cloud intelligence and unmetered local intelligence; the
client model remains the only party that ever touches a cloud API). Concretely it is an MCP server + API layer between an
AI model and the tools the model drives; its core metric is **tokens per
completed user task**, and every design decision is judged by that metric
first. Unreal Engine and Blender are the two shipped adapters and the proving
ground where every pattern is implemented and measured — not the boundary of
the product. The kernel (compact state + diffs, checkpointed batches,
budgeted responses, progressive tool disclosure, project memory, extraction,
KB retrieval) is tool-agnostic; all DCC knowledge lives in the adapters.

## How to work in this repo

- The build is driven by `CLAUDE_EXECUTION_SCRIPT.md`. Do not improvise a
  different plan while it exists; amend the script instead, then follow it.
- The self-improvement campaign (A33) is driven by
  `CLAUDE_SELF_IMPROVEMENT_SCRIPT.md` the same way: work its phases from
  where the PROGRESS evidence says they stand, with TEE's own tools as
  co-pilot.
- The A34 build (web_lookup + the TEE-native code model) is driven by
  `CLAUDE_A34_SCRIPT.md`; research docs 49 and 50 are its design of
  record.
- The A35 shrink campaign (smaller, faster, more efficient) is driven
  by `CLAUDE_A35_SCRIPT.md`, inheriting the A33 rules.
- The A37 merged build (gateway/meter/handoff/kit/kb_propose ×
  fabrication: FreeCAD, Home Builder joinery, joinery_check, boards)
  is driven by `CLAUDE_A37_SCRIPT.md`; research docs 51, 52 and 53 are
  its designs of record. `CLAUDE_A36_SCRIPT.md` is superseded — do not
  work it.
- The A38 shrink round two (post-0.5.0: faster, more efficient,
  smaller, leaner) is driven by `CLAUDE_A38_SCRIPT.md`, inheriting the
  A35/A33 rules.
- The A42 grand campaign (router × reality capture × kernel
  scheduler) is driven by `CLAUDE_A42_SCRIPT.md`; research docs 55–59
  are its designs of record. `CLAUDE_A39_SCRIPT.md`,
  `CLAUDE_A40_SCRIPT.md` and `CLAUDE_A41_SCRIPT.md` are superseded —
  do not work them.
- Progress state lives in `docs/PROGRESS.md`. Read it at session start; update
  it (check items off, note blockers) before ending any session.
- Research grounding lives in `docs/research/`. Consult it before designing or
  claiming facts about UE/Blender APIs — both APIs drift between versions, and
  hallucinated calls are the #1 friction point this project exists to fix.
  Verify any API you are unsure of against local docs or a smoke test, never
  from memory.
- `knowledge-base/` is a DIFFERENT thing: a 38-domain reference library the
  owner imported (A30), written elsewhere, never verified by this project.
  It grounds nothing on its own. To use a fact from it, re-check it against
  the source its own frontmatter cites, then carry that citation into
  whatever TEE file you put it in. `confidence: low` and
  `status: needs-verification` mean exactly what they say.
  **Never take a `bpy`/`unreal` API fact from `knowledge-base/13_*`,
  `14_*` or `15_*`** — third-party prose about a drifting API is the exact
  failure mode above. The rule in the previous bullet outranks it, always.

## Hard rules (token-efficiency dogma)

1. **Never return full scene dumps by default.** Tools return compact summaries
   with stable IDs; detail is opt-in via explicit query tools.
2. **Diffs over snapshots.** After a mutation, report what changed, not the new
   world state.
3. **Batch over chatter.** Prefer one macro-command / one code-execution call
   over N single-op tool calls.
4. **Text over pixels.** Screenshots are a last resort; structured text state
   is the default evidence.
5. **Small tool surface, progressive disclosure.** Keep the always-loaded tool
   schemas minimal; expose long-tail capability through a `run_python` /
   `run_console` escape hatch and searchable docs, not hundreds of tools.
6. **Fail loud and cheap.** Validation errors must come back in one short
   message with the exact fix, not a stack-trace novel.

## Conventions

- Python 3.11+, `ruff` for lint/format, `pytest` for tests.
- MCP server uses the official Python SDK (`mcp` package, FastMCP style)
  unless the script says otherwise.
- Type hints everywhere in `server/`; adapters may relax where DCC-embedded
  interpreters (Blender's bundled Python, UE's) constrain versions.
- Commit style: imperative subject, body explains the *why*. Small commits per
  script step.

## Testing

- `pytest` for the server core (runs anywhere, no DCC needed — DCC calls are
  faked behind adapter interfaces).
- Adapter smoke tests require a machine with Blender / Unreal installed; they
  are marked and skipped otherwise (`-m "not dcc"` in CI).
- `benchmarks/` measures tokens-per-task on scripted scenarios; run before and
  after any change to state representation or tool schemas.
