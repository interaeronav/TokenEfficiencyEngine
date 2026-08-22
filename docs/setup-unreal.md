# Unreal setup

Verified end to end on 2026-08-22 against **UE 5.8.1**
(`5.8.1-56057345+++UE5+Release-5.8`) on macOS 26.6 / Apple Silicon.

## Route: Epic's first-party MCP plugin (UE 5.8+)

Decision A4: TEE **proxies and extends** the official `ModelContextProtocol`
plugin rather than shipping a custom C++ bridge. Epic named MCP a UE6 pillar;
a from-scratch bridge is a dead end, and Epic already dispatches ~830 tools
server-side.

1. Enable the **ModelContextProtocol** and **AllToolsets** plugins in the
   project. `AllToolsets` is **off by default** and without it the server
   answers with an empty catalog.
2. Start the server: launch with `-ModelContextProtocolStartServer`
   (add `-ModelContextProtocolPort=N` to move it), or set
   `bAutoStartServer=True` under
   `[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]` in
   `Saved/Config/<Platform>Editor/EditorPerProjectUserSettings.ini` —
   **not** `DefaultEngine.ini`.
3. The endpoint is loopback HTTP at `127.0.0.1:8000/mcp` with **no
   authentication**. Never port-forward it ([security.md](security.md)).
4. Point TEE at it: `tee serve --adapter unreal` (add `--unreal-port N` if
   you moved it).

Check it with `tee doctor`, which does the handshake rather than just testing
the port:

```
OK   unreal: MCP on 127.0.0.1:8000, 56 toolsets + TEE toolset
```

A minimal Blueprint-only `.uproject` is enough — no C++, no compilation.

## Optional: TEE's content plugin

`releases/v0.1.0/TeeToolset-0.1.0.zip` (source in `adapters/unreal/TeeToolset`)
is **content-only** — Python, no C++ module, nothing to compile.

Unzip into `<YourProject>/Plugins/`, enable **TeeToolset** and
**PythonScriptPlugin** in the `.uproject`, restart the editor.

It adds exactly one capability Epic's toolsets lack: **unsandboxed editor
Python** with the full `unreal` module, wrapped in a named
`ScopedEditorTransaction` so the user can Ctrl+Z it. Epic's own
`execute_tool_script` is sandboxed to tool orchestration plus
`{json, math, datetime, copy, re, time}` and cannot import `unreal` at all.

It is opt-in twice: the plugin ships disabled, and TEE refuses to call it
unless the server allows code execution. **Everything else in the Unreal
adapter works without it** — skip it unless you need the long tail.

## What TEE adds over calling Epic's server directly

Measured on the live editor (see [../benchmarks/RESULTS.md](../benchmarks/RESULTS.md)):
level population + Blueprint function costs **38,334 tokens / 32 round-trips**
following Epic's own prescribed workflow, versus **2,349 / 4** through TEE —
**93.9% saved**.

- **Toolset summaries instead of schema dumps.** One
  `describe_toolset(BlueprintTools)` is ~18,000 tokens — over six times TEE's
  entire always-loaded surface. `ue_toolset` returns compact signatures
  (`!` marks required); `ue_describe_tool` expands exactly one tool.
- **One round-trip per batch** through `execute_tool_script`.
- **Short session ids** (`u1`, `u2`), with refPaths kept server-side.
- **Blueprint authoring that is verified.** `write_graph_dsl` silently drops
  statements it cannot resolve, and the Blueprint then compiles *clean* — a
  wrong node id looks like success from every signal Epic exposes.
  `ue_blueprint_function` reads the graph back and fails loudly instead.
- **TEE-owned checkpoints.** 5.8.1 disabled transaction bundling during tool
  scripts, so the editor's undo stack cannot unwind a batch.
- **Text before pixels.** `ue_scene_checks` answers "what is in view" in ~70
  tokens; `ue_capture` re-encodes to a byte-budgeted JPEG because
  `CaptureViewport` has no resolution parameter and returns whatever the
  viewport is.

## Performance note that shapes usage

Every in-editor tool dispatch costs **~0.37 s**, serialized on the game
thread. Minimising *dispatches* matters as much as minimising HTTP calls:
scene listings are one dispatch regardless of scene size, and labels and
transforms are opt-in detail (`ue_entity_detail`, max 25 actors).

## Gotchas found by running it

These contradict the documentation, so TEE handles them for you:

- Object-typed parameters described as **optional are required**; the server
  answers `input param "X" needs a default value`. TEE builds the missing
  value from that parameter's schema and retries.
- A tool failure inside `execute_tool_script` is **not catchable** — neither
  `except RuntimeError` nor `except Exception`; the sandbox aborts the whole
  script. Scripts must check before acting.
- Tool results are `_StrictDict`: use `d["k"]`, never `d.get("k", default)`.
- `serverInfo.name` is **empty** on 5.8.1, so nothing may identify the server
  by name.
- `tools/call` answered **plain JSON**, not SSE, on every call measured. TEE
  parses both.

## Fallback route: UE 5.3–5.7

Remote Control API (HTTP `:30010` / WS `:30020`) + Python remote execution,
behind the same `ue_*` tool schemas with a capability probe choosing the
backend. **Status: `n/a`** — no 5.3–5.7 engine is installed on the build
machine, so this tier is unimplemented and untested rather than merely
unverified.

## UEFN

UEFN has no macOS build; the live UEFN lanes need a Windows machine. The
offline lanes (digest parsing, Verse lint, templates, export preflight) work
everywhere — see the `uefn` skill.
