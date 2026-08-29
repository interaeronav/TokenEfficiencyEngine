# Troubleshooting

`tee doctor` is the first move — every check names its one-line fix, and
`--json` gives the machine-readable form. This page maps the common
failures beyond it.

## Server

| Symptom | Cause / fix |
|---|---|
| `tee: command not found` after pip install | The venv's bin dir is not on PATH — call the binary by path or `pipx install tee-engine` |
| `/usr/bin/tee` runs instead of TEE | That's coreutils `tee`. Use the venv binary path (what `tee doctor --emit` prints) |
| tool answers `…_extra_missing` | Install the named extra: `uv sync --extra extract` / `assets` / `physical` |
| tool answers `tool_disabled` | It's in `[tools].disabled` in `.tee/config.toml` (deliberate per-project profile) |
| "another tee server (pid N) already serves this project" | Two clients on one project is legal; they share `.tee/` memory and checkpoints — expect shared state, not corruption |
| responses look truncated with a `narrow` hint | The response budgeter fired; follow the hint (page, filter, or query the detail tool) — that is the design, not a bug |

## Blender bridge

| Symptom | Cause / fix |
|---|---|
| `adapter_unavailable` | Nothing listening on :9876 — start a bridge ([setup-blender.md](setup-blender.md)); if a long job is running, the serial bridge is just busy (tee_status names the job) |
| port open but "not speaking the bridge protocol" | Another program holds the port — change it in the add-on prefs and pass `--blender-port` |
| `stale_api` refusals on bl_execute_python | The version firewall caught an idiom invalid on the CONNECTED Blender (e.g. `use_auto_smooth`, `use_nodes =` writes) — the hint names the replacement |
| batch failed and rolled back | Mid-batch failures restore the auto-checkpoint so the DCC and cache never diverge silently; fix the op the error names and resend |
| `resync_required` from tee_diff | History broke (rollback/reload/user undo) — run `tee_scene_summary(refresh=true)` and continue from the new stamp |
| GUI Blender freezes during a fluid bake | Bakes are synchronous in Blender; the bridge is busy until done — that is why `sim_fluid` is job-gated and capped at res 64 |

## Context / cost

| Symptom | Cause / fix |
|---|---|
| host evicted old tool results | `tee_status(recap=true)` rebuilds a ≤500-token project recap from server state in one call |
| a loop of tool calls is burning context | Move it into ONE `tee_script` call — intermediate results never enter context (measured 63–76% savings on fix loops) |
| median response size alert in tee_status | A tool is answering fat; page/filter it, and file it — every response is size-logged per tool by design |

## Assets / network

| Symptom | Cause / fix |
|---|---|
| `license_blocked` | Working as intended: NC/ND/GPL/unknown licenses never enter the cache; pick another hit (SA needs `[assets] allow_sa=true`) |
| `backend_unreachable` with no cache | First search needs the network once to seed the ETag/TTL catalog cache; afterwards searches run from disk |
| `cost_confirmation_required` | Paid generation (Tripo/Meshy) and fluid bakes require `confirm_cost=true` after showing the estimate |
| `no_backend` from voxkiln | Local 3D generation needs Apple Silicon or an NVIDIA GPU plus `pip install 'voxkiln[model]'` ([setup-voxkiln.md](setup-voxkiln.md)); hosted fallback: tripo/meshy with keys |
| `image_required` from voxkiln | Voxkiln is image-to-3D only: render/pick a concept image (lane 1) and re-call with `kind="image_to_model"`, `prompt=<image path>` |

## Unreal: `ue_settle` reports `ue_editor_not_ticking`

Simulate-In-Editor started, but the world clock never advanced, so nothing
was simulated. The editor does not tick while it is in the background.

Add to `Saved/Config/<Platform>Editor/EditorPerProjectUserSettings.ini` and
restart the editor:

```ini
[/Script/UnrealEd.EditorPerformanceSettings]
bThrottleCPUWhenNotForeground=False
```

This error exists because the failure is otherwise invisible: the play world
reports itself running and the bodies report themselves simulating, so a
poll loop would conclude the scene settled instantly and adopt unmoved poses.

## Unreal: a Blueprint compiled clean but the function does nothing

`write_graph_dsl` silently drops statements it cannot resolve, and the
Blueprint then compiles clean, so a wrong node type id looks like success.
Use `ue_blueprint_function`, which reads the graph back and fails with the
unresolved id, rather than calling `write_graph_dsl` directly. Node type ids
can be checked with `ue_call BlueprintTools find_node_types`.

## Unreal: a tool call fails with `input param "X" needs a default value`

Object-typed parameters are required even when their own description calls
them optional. TEE builds the missing value from the parameter's schema and
retries automatically; if you are calling the engine directly, pass an
explicit value. Note that a zero-filled transform is not always harmless —
a defaulted `captureTransform`, for instance, photographs the world origin
rather than the viewport.

## FreeCAD: RPC hangs {#freecad-rpc-hangs}

Symptom: port 9875 accepts connections but `execute_code` (and every
TEE call over it) times out — "accepted the connection but never ran
the request".

The RPC addon queues work to FreeCAD's GUI thread; if that thread is
parked in a **modal dialog**, nothing dispatches. The usual culprit is
the document-recovery dialog after a crashed or killed FreeCAD (proven
by stack sample: `DocumentRecoveryFinder::showRecoveryDialogIfNeeded`
→ `QDialog::exec`). Fix: bring the FreeCAD window forward and dismiss
the dialog — or, for a headless-ish restart, quit FreeCAD and clear
the stale autosaves before relaunching:

```bash
rm -rf ~/Library/Caches/FreeCAD/v1-1/Cache/FreeCAD_Doc_* ~/Library/Caches/FreeCAD/v1-1/Cache/FreeCAD_*.lock
```

(macOS path shown; on Linux/Windows the equivalents live under
FreeCAD's user cache directory.) The benchmark battery probes for this
state and skips the fabrication scenario with this page's fix instead
of hanging.
