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
- A **partially specified transform is not "unchanged", it is ZERO.** Epic's
  xform converter documents every field as optional; a rotation-only
  `set_actor_transform` teleported an imported chair to the world origin
  (5.8.1). TEE's batch interpreter reads the current transform back and fills
  the gaps before writing, so `tee_batch` `set` ops mean what they say.
- `MaterialEditingLibrary.connect_material_property` returns **True while
  changing nothing**: an authored Constant3Vector -> Emissive material kept the
  default graph (95 pixel-shader instructions) and rendered black. Parametrise
  a shipped material through a `MaterialInstanceConstant` instead and read the
  value back — `set_material_instance_vector_parameter_value` returns False
  even when it *does* apply, so trust the read-back, not the return value.
- `Actor.add_component_by_class` is **absent** from the 5.8.1 Python API, so a
  marker cannot grow a text label at runtime; use the actor label and tags.
- Entity ids (`u1`, `u2`, …) are **per session**. They are assigned in listing
  order, so replaying a saved `tee_batch` from an earlier session can resolve
  the same id to a DIFFERENT actor. Re-read ids with `tee_scene_summary` in the
  session you act in; never hard-code them into a script you rerun.

## Required for simulation: let the editor tick in the background

`ue_settle` runs Simulate-In-Editor. **A backgrounded editor does not tick at
all**, and the failure is silent: the play world reports
`is_in_play_in_editor() == True` and bodies report
`is_simulating_physics() == True`, while the world clock stays pinned at 0.0
and nothing moves. Polling that looks exactly like "the scene settled
instantly".

Fix it once per project — add to
`Saved/Config/<Platform>Editor/EditorPerProjectUserSettings.ini` and restart:

```ini
[/Script/UnrealEd.EditorPerformanceSettings]
bThrottleCPUWhenNotForeground=False
```

(Equivalently: Editor Preferences → Performance → uncheck "Use Less CPU when
in Background".) Keeping the editor window in the foreground also works.

TEE does not rely on you remembering: `ue_settle` asserts that simulation time
actually advances and fails with this exact remedy rather than returning a
confident wrong answer.

## Pins: markers that carry their own record

`pin_set` / `pin_list` / `pin_show` / `pin_fill` / `pin_remove` put a small
editor-only marker where something should eventually go and keep its record —
id, display name, category, notes, wishlist, and what finally filled it — in
the actor's own **tags**, so it survives a level reload and reads back without
opening the editor (decision A29).

They need the content plugin above and code execution, because Epic's toolsets
expose no way to read or write an actor's Tags array.

The tag prefix is per project, in `.tee/config.toml`:

```toml
[pins]
namespace = "okongo_pin"   # default: tee_pin
```

so pins join a project's existing tag family rather than starting a second one.
Markers are `is_editor_only_actor` with collision off — an authoring aid must
never ship inside, or block, the walkable build. `pin_fill` with no `pick`
searches the pin's wishlist and answers with a shortlist; with
`pick='source:id'` it imports at the pin through `as_import` (same four-band
scale policy, same checkpoint), faces it along the pin's yaw, replaces whatever
stood there, and writes the chosen key back onto the pin.

## Fallback route: UE 5.3–5.7

Remote Control API (HTTP `:30010` / WS `:30020`) + Python remote execution,
behind the same `ue_*` tool schemas with a capability probe choosing the
backend. **Status: `n/a`** — no 5.3–5.7 engine is installed on the build
machine, so this tier is unimplemented and untested rather than merely
unverified.

## UEFN

UEFN is Windows-only and live-editor integration is OUT OF SCOPE for this
project (owner decision, 2026-08-22 — no Windows machine). TEE's offline
UEFN lanes (Verse digest facts + linting, templates, export preflight,
analytics) work everywhere and are fully supported — `uefn_status` reports
the mode. See the `uefn` skill.
