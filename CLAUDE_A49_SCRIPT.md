# CLAUDE_A49_SCRIPT.md — Godot, headlessly, as a first-class TEE adapter

**Owner directive (2026-08-31, verbatim):** *"integrate godot with TEE
headlessy (godot is used for game designs)"*. Written for a fresh Opus
session with no memory of the one that researched it.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, code in `server/`. Branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md`
  first; real command output into it per phase; commit+push per item.
- Suite `uv run pytest -q -m "not dcc"` from `server/` — expect ~1,136
  passing, ruff clean. Surface invariant: **17 always-loaded tools,
  2,034 tok** on the wire (`surface:` line of
  `uv run --project server python benchmarks/run_benchmarks.py`), budget
  ±10 around 2,028.
- **Upgrade trap:** every `.mcpb` install wipes the extension venv's
  extras; restore with
  `uv pip install --python "<extension venv>/bin/python"
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]'
  'tee-engine[extract]' 'tee-engine[pdf]'`.
- Godot **4.7.2** is installed: `/Applications/Godot.app`, CLI `godot` on
  PATH (`/opt/homebrew/bin/godot`). Licence MIT — record in DECISIONS.md.
- Probe artifacts from the research live at scratchpad `godot/`
  (`bridge.gd`, `tree.gd`, `from_tee.tscn`) — reference, do not ship.

## Measured facts (2026-08-31 — build ON these, do not re-litigate)

1. **The first-launch hang.** A project that has never been imported can
   hang `godot --headless -s script.gd` indefinitely with NO output. Run
   `godot --headless --path <proj> --import` once first (measured: exits 0,
   then scripts run). The adapter must do this automatically on first
   contact with a project.
2. **A socket bridge works headlessly.** `extends SceneTree` +
   `TCPServer` polled in `_process()` served a JSON request and replied —
   round-trip proven on 127.0.0.1:9878. `--headless -s bridge.gd --path
   <proj>` is the launch shape (a bare `extends MainLoop` script also runs
   with no project at all).
3. **Scene building and saving work.** Nodes added live; `PackedScene` +
   `ResourceSaver` wrote a valid 238-byte `.tscn` (children must have
   `owner` set to pack).
4. **Headless rendering does NOT work.** `DisplayServer` is `headless`,
   the rasterizer is the dummy (`ERROR: Parameter "t" is null ...
   rendering/dummy/storage/texture_storage.h`), `get_texture().get_image()`
   returns nothing. `capture()` must REFUSE with this reason — never a
   black rectangle. (P4 holds one bounded attempt at an alternative;
   default is the honest refusal.)
5. **GDScript gotchas that cost real probe time:** typed inference
   (`var x := expr`) hard-fails the parse when the type is unknowable —
   prefer untyped locals in generated code; in a `SceneTree` script `root`
   IS the viewport/Window (there is no `root.root`); `put_data` needs a
   `poll()` and a beat before `quit()` or the reply is lost; GDScript is
   indentation-strict.
6. **Model-table corrections found during research, carried here:**
   `machine.ENGINES["q27b-bare"].senses = []` is FALSE — the on-disk
   config is `Qwen3_5ForConditionalGeneration` with `vision_config`, so
   the 27B natively sees. DeepSeek was verified the same way and is
   genuinely blind (`DeepseekV4ForCausalLM`, no vision_config). Fix the
   row (senses: ["vision"]), keep dsflash as-is, and note the METHOD:
   senses are read from the model's own config on disk, never inferred
   from shim behaviour — the shim reroutes image requests, which masks
   the truth.

## Laws (inherited, plus Godot-specific)

1. Measured before/after; nothing claimed working that was not run.
2. Surface invariant holds. The whole POINT of the Adapter protocol is
   that `tee_scene_summary`, `tee_batch`, `tee_diff`, checkpoints and the
   rest drive Godot with **zero new always-loaded tools**.
3. Commands are declarative and enumerable (the trade-rule lesson).
   Arbitrary GDScript execution is a SEPARATE door behind `exec-code`,
   named honestly, never the default path.
4. A refusal names its reason and the fix. The render refusal carries the
   measured dummy-rasterizer fact, not "unsupported".
5. Trust: any `gd_*` virtual tools are tabled EXPLICITLY. The bridge
   binds 127.0.0.1 only.
6. The scene on disk is the owner's document: writes go through the
   checkpoint machinery like Blender's, and `.tscn` saves never target an
   existing file without the same overwrite discipline the PDF lane has.

## P0 — carried corrections (small, first)

Fix `q27b-bare` senses per fact 6 with a comment carrying the method;
extend the A47 declaration test so a senses claim must cite its source
(config-on-disk), not a guess. Suite green, commit.

## P1 — the bridge (`adapters/godot/tee_bridge/bridge.gd`)

Persistent version of the probe: `extends SceneTree`, TCPServer on a
`--port` arg (default 9879 — 9876/9877 are Blender's), `_process` pump,
**\0-framed JSON identical to the Blender wire** (`{"type": "execute",
...}` request, `{"status": "ok", "result": ...}` reply) so
`BlenderWire`'s framing generalizes. Instead of Python code, the request
carries `{"type": "commands", "ops": [...]}` — the declarative set:

- `add_node {type, name, parent, props}` (typed Node3D/MeshInstance3D/
  Camera3D/Light3D/... — enumerate what v1 supports, refuse the rest by
  name), `set_props {path, props}`, `remove_node {path}`
- `instance_scene {res, parent}` , `save_scene {out, root}` (overwrite
  discipline), `load_scene {res}`
- `list {}` -> compact node tree with stable paths, types, child counts
- `run_scene {res, frames}` -> run N frames headless, collect
  `print()` output (this is the game-design payoff: logic runs without a
  window)

Plus `{"type": "gd", "code": ...}`: compile via `GDScript.new()` +
`source_code` + `reload()`, call a `run(root)` entry point, return its
dict — the escape hatch, gated in P2 behind exec-code.
*Acceptance:* bridge boots headless on a fresh project (auto `--import`),
survives 50 sequential ops, malformed JSON gets a structured error not a
crash, and Ctrl-C/idle-timeout exits clean.

## P2 — `GodotAdapter` (server side)

`server/src/tee/adapters/godot/` honoring the `Adapter` protocol:
`info()` (version from `godot --version`), `probe()`, `list_entities()`
(from `list`), `execute(batch)` -> Diff (the existing diff discipline:
report what changed), `snapshot/restore` (save/load a checkpoint `.tscn`
under the workdir), `capture()` -> the measured refusal (fact 4).
Launch management: find/spawn the bridge like Blender's launcher does,
with the `--import` guard. CLI: `tee serve --adapter godot --project X`.
Trust: whatever `gd_*` virtual tools exist are explicit entries;
`gd_execute` requires exec-code.
*Acceptance:* against a real headless Godot: `tee_scene_summary` lists
nodes, `tee_batch` adds a MeshInstance3D and the DIFF names it,
checkpoint/rollback round-trips, `tee_capture` refuses with the dummy-
rasterizer reason. Suite green with the fake-adapter tests (a
`FakeGodotWire` mirroring `fixtures_llm` style, so CI needs no Godot).

## P3 — the game-design lane

`run_scene` as a declared pipeline step (the P3c pattern): a game
project's `.tee/pipeline.toml` declares "run main scene N frames, assert
no script errors, collect prints" — pinned, hash-approved. Adopt ONE real
sample project (create `~/GodotProjects/tee-sample` with a trivial scene
+ a script that prints) and run the lane end to end.
*Acceptance:* pipeline_run executes the scene headless via the adapter,
job result carries frames run + captured output + script-error count.

## P4 — seeing Godot (bounded)

Default: `sense_viewport`/`sense_camera` refuse for godot, naming fact 4
and pointing at `run_scene` output as the headless evidence channel.
Bounded attempt (timebox ~30 min): can a NON-headless windowed Godot on
this Mac render offscreen for capture (`--write-movie`, or a hidden
window + `get_image()`)? If yes, wire it as an OPT-IN visible-window
capture with the honest note that it is not headless; if no, record the
attempt and stop. Do not let this phase grow.

## P5 — ship

DECISIONS.md (Godot MIT; the declarative-commands-vs-exec split;
the render refusal), `docs/godot-lane.md`, tool search ranks
("godot scene", "run a game headless", "add a node") top-3, version
0.17.0, bundle, clean-unzip MCP verify (17 tools), extras note incl
`[pdf]`, PROGRESS throughout.

## Out of scope

Editor/GUI automation, the asset import pipeline beyond `--import`,
C#/Mono builds, export templates and packaging games, multiplayer, and
any rendering workaround beyond P4's timebox. Blender/Unreal lanes are
untouched.
