# The Godot lane (A49)

Godot 4 as a first-class TEE adapter, headlessly. Because it honours the
`Adapter` protocol, it arrives with **no new always-loaded tools** —
`tee_scene_summary`, `tee_batch`, `tee_diff`, `tee_checkpoint` and
`tee_rollback` already know this shape.

```bash
tee serve --adapter godot --project ~/GodotProjects/my-game
```

## The one rule that will bite you first

**A project that has never been imported hangs `godot --headless -s` with
no output at all.** Not slow — silent, indefinitely. The adapter runs
`--import` for you on first contact, which is why that is a duty in the
code rather than a line in a README. If you launch Godot yourself, import
first.

## Building scenes

Commands are declarative and enumerable, driven through `tee_batch`:

```json
{"op": "add_node", "type": "MeshInstance3D", "name": "Player",
 "props": {"mesh": "capsule", "position": [0, 1, 0]}}
```

`add_node`, `set_props`, `remove_node`, `save_scene`, `load_scene`. An
unknown node type or op is refused **with the allowed list**, not a generic
error. Arbitrary GDScript exists as a separate `{"type": "gd"}` door and is
gated on `exec-code` — never the default path.

Checkpoints write to `user://`, outside your project: a rollback must not
leave debris in your game. **Honest limit:** a restored scene comes back
nested one level deeper (`/Root/Player`, not `/Player`), because
`PackedScene` cannot pack the SceneTree's Window and the bridge wraps the
children to pack them. Content and properties round-trip; re-list after a
rollback rather than reusing old paths.

## Running the game — the actual payoff

```python
adapter.run_scene(frames=120)
```

Runs your game's real logic headless: `_ready` fires, `_process` advances,
and the game's own `print()` output comes back as the observation.

```json
{"ok": true, "frames": 120, "script_errors": 0, "wall_s": 0.58,
 "output": ["TEE_SAMPLE ready: spawning props", "TEE_SAMPLE spawned=3"]}
```

**Script errors are counted, not inferred from the exit code.** Measured: a
game whose `_ready` raises still exits **0**. A lane that trusted the exit
code would call a broken game a pass, so `ok` requires zero `SCRIPT ERROR`
lines as well as a clean exit.

This is also a pipeline step — see `~/GodotProjects/tee-sample/.tee/
pipeline.toml` for a declared, hash-pinned `smoke_run`.

## Seeing it

**Headless Godot cannot render.** Not "poorly" — at all. Measured across
`--rendering-driver vulkan`, `opengl3` and `dummy`: the viewport texture
yields no image (`Parameter "t" is null`). So `tee_capture` **refuses**,
and says exactly that. A black rectangle would be worse than a refusal
because it looks like an answer.

Text is the evidence channel: the node tree from `tee_scene_summary`, and
`run_scene` output from the game actually running.

If you genuinely need pixels, `GodotAdapter.capture_windowed()` renders
with a real display server — which **opens a window on your screen** for a
moment. That trade is yours to make, so it is opt-in and never automatic,
and it will not work over SSH or in CI.

It also adds a framing camera when the scene has none. That was found the
right way: the first version rendered `main.tscn`, which is authored for
gameplay and has no `Camera3D`, and produced a correct empty grey frame.
TEE's own vision model reported "0 objects" — which was true, and is how
the gap surfaced. With framing, the same scene reads back "3 cubes", which
is exactly what the game's `_ready` spawns.
