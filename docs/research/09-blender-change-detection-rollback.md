# Blender Change Detection & Rollback Mechanisms

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Research question

What is the Blender-side mechanism for change detection and rollback that TEE's differential scene cache and checkpoint tools would build on: granularity/reliability/re-entrancy of `bpy.msgbus.subscribe_rna` and `bpy.app.handlers` (`depsgraph_update_post`, `undo_post`) for detecting scene mutations (including ones made by the user in the GUI while the agent works), scripted checkpoint semantics (`bpy.ops.ed.undo_push`, undo step limits, what undo does NOT cover such as node-tree/ID management edge cases), and the fact that background/pip-`bpy` mode has no undo system at all (what snapshot strategy — temp `.blend` saves, library overrides — is viable there and at what cost)?

"Return diffs, not dumps" and "transactional execution with rollback" are two of TEE's core pillars, and the research specifies concrete mechanisms only for UE (Remote Control preset.register change events, `ScopedEditorTransaction`) — the Blender side is unspecified. Whether Blender supports reliable event-driven change notification versus requiring poll-and-snapshot-hash diffing changes the bridge add-on's design, its main-thread timer load, and cache-invalidation correctness when the human edits concurrently; the absence of undo in background mode changes the rollback story for the entire batch backend (temp-file snapshots vs undo pushes).

## Summary

Blender has no single reliable event-driven change feed, so TEE's Blender bridge must be a hybrid: `bpy.msgbus.subscribe_rna` gives property-level events but only for edits made through RNA (Python API and UI widgets — it provably never fires for viewport transform drags, the most common concurrent human edit), while `bpy.app.handlers.depsgraph_update_post` fires for virtually every change including selection, but only at datablock granularity with three coarse flags (`is_updated_geometry`/`transform`/`shading`); a core developer (brecht) confirmed sub-datablock change info "is not tracked by Blender, so it's also not available in the Python API", so property/component-level diffs require poll-and-hash of the IDs flagged in `depsgraph.updates`.

Checkpointing in GUI mode is `bpy.ops.ed.undo_push(message=...)` + `bpy.ops.ed.undo()`/`undo_history` against a fully-relative in-memory memfile undo stack (default 32 steps, max 256, whole-file-in-memory per Global Undo), and pushing an undo step after every scripted datablock add/remove is not optional — since 2.83's incremental undo, mutations without an undo step crash Blender on the user's next Ctrl+Z (issue #77557, closed by documenting the rule).

In background mode the undo stack is simply not created at startup (`wm_files.cc` gates creation on `!G.background`) but `bpy.ops.ed.undo_push()` lazily initializes it as an explicit exception (#60934), enabling in-memory rollback with caveats (no automatic per-operator steps; a 5.0 regression #149890 shows the path is fragile). The robust batch-backend rollback is temp-file snapshots via `bpy.ops.wm.save_as_mainfile(copy=True, compress=True)` (Zstandard level 3 since 3.0: saving ~90% faster, loading ~60% faster than gzip) plus `bpy.ops.wm.open_mainfile` to restore, with `bpy.data.libraries.write` for partial datablock checkpoints; library overrides are a linked-data editing system, not a snapshot mechanism.

All events, timers, and msgbus callbacks run on the main thread and undo/redo invalidates Python references, so the cache must be keyed by `ID.session_uid` (stable across renames, internal reallocations, and file reload) and rebuilt on `undo_post`/`load_post`.

## Findings

### msgbus subscription granularity

`bpy.msgbus.subscribe_rna(key, owner, args, notify, options)` accepts three key forms: a specific property instance (obtained via `datablock.path_resolve('prop_name', False)` to avoid Python-converted values), a struct type (`bpy.types.X`), or a `(bpy.types.X, 'prop_name')` tuple which subscribes to that property on ALL instances of the type. The callback receives only the static `args` tuple fixed at subscribe time — no payload identifying which datablock or what value changed. `owner` is any Python object compared by identity; `clear_by_owner(owner)` unsubscribes. `publish_rna(key)` can synthesize notifications.

Source: [https://docs.blender.org/api/current/bpy.msgbus.html](https://docs.blender.org/api/current/bpy.msgbus.html)

### msgbus trigger conditions (official limitations)

Notifications fire ONLY for updates that go through the RNA system: (1) Python API changes (e.g. `some_object.location.x += 3`) and (2) UI sliders/fields/buttons. They do NOT fire for: moving objects in the 3D Viewport (transform drags), and changes performed by the animation system. Callbacks are postponed until all operators have finished executing, and per property the callback triggers only once per update cycle even if the property changed multiple times (built-in coalescing). Changes made from inside msgbus callbacks are not included in related undo steps, so Undo followed by Redo silently skips their effects.

Source: [https://docs.blender.org/api/current/bpy.msgbus.html](https://docs.blender.org/api/current/bpy.msgbus.html) (Limitations section)

### msgbus viewport-transform blind spot confirmed as permanent Known Issue

Issue #72109 "bpy.msgbus.subscribe_rna doesnt trigger with the transform system" is still OPEN, classified as Known Issue not a bug. Dev lichtwerk: "The transform system doesnt really go through RNA iirc, so subscribing wont succeed here." Campbell Barton (ideasman42): "this is a general issue for operators that access struct members directly, not via RNA." Consequence: msgbus alone cannot detect the most common concurrent human GUI edit (grab/rotate/scale in viewport).

Source: [https://projects.blender.org/blender/blender/issues/72109](https://projects.blender.org/blender/blender/issues/72109) (via projects.blender.org API)

### msgbus lifetime / re-registration burden

All msgbus subscribers are cleared on file load ("It will be cleared when another blend file is loaded"); docs explicitly direct re-registering in `bpy.app.handlers.load_post`. The `options={'PERSISTENT'}` flag only keeps the subscriber when remapping ID data — it does not survive file load. Any rollback implemented as file reload (`open_mainfile`/`revert_mainfile`) therefore destroys all subscriptions and they must be rebuilt.

Source: [https://docs.blender.org/api/current/bpy.msgbus.html](https://docs.blender.org/api/current/bpy.msgbus.html)

### bpy.app.handlers signatures relevant to TEE

`depsgraph_update_pre`/`post`: callable with `(scene)` or `(scene, depsgraph)` — the depsgraph being updated is passed as optional 2nd arg. `undo_pre`/`undo_post` and `redo_pre`/`redo_post`: receive only `(scene)`, no depsgraph. `save_pre`/`save_post`/`save_post_fail`: receive the filepath string (empty for startup file). `load_post` fires after file load. By default ALL handlers are freed when a new file is loaded; the `@bpy.app.handlers.persistent` decorator is required to survive loads. Official warning: altering data from handlers must be done carefully — during rendering `frame_change` handlers run on a different thread than viewport updates and can crash Blender unless the interface is locked (`use_lock_interface`).

Source: [https://docs.blender.org/api/current/bpy.app.handlers.html](https://docs.blender.org/api/current/bpy.app.handlers.html)

### Depsgraph change-event granularity ceiling

Inside `depsgraph_update_post`, `depsgraph.updates` yields `DepsgraphUpdate` objects with exactly four fields: `id` (the updated data-block), `is_updated_geometry`, `is_updated_shading`, `is_updated_transform` (all read-only bools). `depsgraph.id_type_updated('OBJECT'|'MESH'|...)` reports whether any datablock of a type was added, updated or removed. There is no per-property, per-vertex, or old-value information. Access originals via `update.id.original`; never modify evaluated IDs.

Source: [https://docs.blender.org/api/current/bpy.types.DepsgraphUpdate.html](https://docs.blender.org/api/current/bpy.types.DepsgraphUpdate.html) and [https://docs.blender.org/api/current/bpy.types.Depsgraph.html](https://docs.blender.org/api/current/bpy.types.Depsgraph.html)

### Core dev confirmation: sub-datablock diffs require app-side hashing

Brecht Van Lommel (2020, devtalk thread "Being notified when subparts of a mesh change"): "This information is not tracked by Blender, so it's also not available in the Python API." Same thread, user testure: "the depsgraph callback is triggered on virtually every change, no matter how insignificant (selection change triggers it for example)" — uncontested by brecht, who adds that even selecting a different shape key is tagged as an update because it has a visible effect. So `depsgraph_update_post` is a high-frequency, coarse-grained signal: TEE must use it only to mark IDs dirty, then poll-and-snapshot-hash those IDs to produce property-level diffs.

Source: [https://devtalk.blender.org/t/being-notified-when-subparts-of-a-mesh-change-vertices-faces-shape-keys-etc/12373](https://devtalk.blender.org/t/being-notified-when-subparts-of-a-mesh-change-vertices-faces-shape-keys-etc/12373)

### depsgraph_update_post re-entrancy hazard

Modifying scene data (or anything that tags the depsgraph) inside `depsgraph_update_post` retriggers the handler; issue #65155 "Dependency graph update_post handler trigger maximum recursion depth error" documents recursion crashes, and even text output to the Python Console has been reported to raise the depsgraph_update event causing infinite recursion. Established mitigations: guard/dirty flags, do no work in the handler beyond recording update ids, and defer processing to `bpy.app.timers`. Also 2.8-era crash calling `bpy.context.evaluated_depsgraph_get()` inside the handler — use the depsgraph argument passed to the handler instead (devtalk 7467 pattern: `for update in depsgraph.updates: if update.id.original == obj and (update.is_updated_geometry or update.is_updated_transform)`).

Source: [https://projects.blender.org/blender/blender/issues/65155](https://projects.blender.org/blender/blender/issues/65155) ; [https://devtalk.blender.org/t/detect-changes-in-object/7467](https://devtalk.blender.org/t/detect-changes-in-object/7467)

### Handler-side data mutation is unsafe (ID add/remove)

In issue #77557 core dev mont29 (Bastien Montagne): "adding or removing objects (or any other datablock) in handlers is not a good idea nor practice, not at all... very likely to cause problems one way or the other." The accepted safe pattern (stated by the reporter and matching official docs): "Using application timers, execution queues and custom ops to react to events on main thread appears to be the acceptable solution." TEE's bridge add-on should therefore drain its command queue from a `bpy.app.timers` callback and execute mutations via operators, not directly inside msgbus/depsgraph handlers.

Source: [https://projects.blender.org/blender/blender/issues/77557](https://projects.blender.org/blender/blender/issues/77557) (comments)

### Threading model: everything on main thread

Official gotcha "Python Threads are Not Supported": "no work has been done to make Blender's Python integration thread safe"; threads may only run while the main thread is blocked, and "While threads are running, no code (including the main thread) may use bpy or any Blender API". `bpy.app.timers.register(fn, first_interval=0, persistent=False)` runs `fn` on the main thread; returning a float reschedules after that many seconds, `None` unregisters; `persistent=True` survives file load. This dictates TEE's architecture: MCP server socket I/O in a background thread or separate process, all `bpy` access marshalled through a timer — and every timer tick is main-thread load that competes with the user's interactive session, which is the direct cost of any poll-and-hash diffing strategy.

Source: [https://docs.blender.org/api/current/info_gotchas_threading.html](https://docs.blender.org/api/current/info_gotchas_threading.html) ; [https://docs.blender.org/api/current/bpy.app.timers.html](https://docs.blender.org/api/current/bpy.app.timers.html)

### Scripted checkpoint semantics: undo_push

`bpy.ops.ed.undo_push(message='...')` — "Add an undo state (internal use only)" — is the scripted checkpoint primitive; `message` labels the step for `undo_history` navigation. `bpy.ops.ed.undo()`, `bpy.ops.ed.redo()`, `bpy.ops.ed.undo_history(item=N)` navigate the stack. In source, `ED_undo_push` clamps to `U.undosteps` and `ED_OT_undo_push` has `poll=ED_operator_screenactive` with the comment "Unlike others undo operators this initializes undo stack." Note from issue #149890 (Nov 2025): "just running operators inside a script doesn't produce undo steps" — scripted batches need explicit pushes (or a py operator with `bl_options={'REGISTER','UNDO'}` returning `FINISHED`).

Source: [https://docs.blender.org/api/current/bpy.ops.ed.html](https://docs.blender.org/api/current/bpy.ops.ed.html) ; [https://github.com/blender/blender/blob/main/source/blender/editors/undo/ed_undo.cc](https://github.com/blender/blender/blob/main/source/blender/editors/undo/ed_undo.cc)

### Undo step limits and memory cost

`PreferencesEdit.undo_steps`: "Number of undo steps available" — range [0, 256], default 32. `PreferencesEdit.undo_memory_limit`: MB, default 0 = unlimited. `PreferencesEdit.use_global_undo` (default True): "Global undo works by keeping a full copy of the file itself in memory, so takes extra memory". Disabling Global Undo breaks the Adjust Last Operation panel. TEE checkpoints consume the same 32-step budget as the user's own undo history, and can silently push the user's older steps off the stack.

Source: [https://docs.blender.org/api/current/bpy.types.PreferencesEdit.html](https://docs.blender.org/api/current/bpy.types.PreferencesEdit.html) ; [https://docs.blender.org/manual/en/latest/editors/preferences/system.html](https://docs.blender.org/manual/en/latest/editors/preferences/system.html)

### Undo architecture: fully-relative typed step stack

Official developer docs: a single undo stack gathers steps of different types (global/memfile undo, edit-mode undo, sculpt/paint undo, image undo, etc.); "Currently, Blender undo stack is fully relative" — reaching a target step requires sequentially loading all in-between steps; "Typically, only data is stored and managed in undo, UI changes are not." Memfile undo uses the `.blend` read/write code (BLO) against an in-memory file; the crash stack in #77557 shows undo decode literally runs `BKE_blendfile_read_from_memfile` → `setup_app_data` → `BKE_scene_set_background`. `BKE_undo_system.hh` defines `BKE_UNDOSYS_TYPE_IS_MEMFILE_SKIP(ty) = ELEM(ty, BKE_UNDOSYS_TYPE_IMAGE)` — image-editing undo steps are excluded from memfile handling (separate image undo).

Source: [https://developer.blender.org/docs/features/core/undo/](https://developer.blender.org/docs/features/core/undo/) ; [https://github.com/blender/blender/blob/main/source/blender/blenkernel/BKE_undo_system.hh](https://github.com/blender/blender/blob/main/source/blender/blenkernel/BKE_undo_system.hh)

### What undo does NOT cover / edge cases

(1) Linked library data: "undo can skip checking changes in library data since it is assumed to be static"; Python CAN modify library data anyway, and making library data point to newly created local data will "likely crash" on undo. (2) Data changed without an undo step: "when Blender data is modified, there should always be an undo step created for it. Otherwise, there will be issues, ranging from invalid/broken undo stack, to crashes on undo/redo." (3) Custom/ID properties changed without a push: reported in #77557 that `obj['test']='string'` without undo push doesn't crash but undo "won't restore the original values" — silent non-coverage. (4) Changes made from msgbus callbacks are excluded from the related undo step. (5) UI state is never stored. (6) RNA property update callbacks doing complex work can corrupt the undo history ("most operators store a history step, and editing an RNA property does so as well").

Source: [https://docs.blender.org/api/current/info_gotchas_crashes.html](https://docs.blender.org/api/current/info_gotchas_crashes.html) ; [https://projects.blender.org/blender/blender/issues/77557](https://projects.blender.org/blender/blender/issues/77557)

### ID add/remove without undo push = guaranteed crash since 2.83

Issue #77557 "Python Operators that add/remove ID data without an undo step crash Blender" (broken 2.83+, worked 2.8.0) accumulated 9+ duplicates (#65681, #80759, #81346, #81883, #82379, #92094, ...). mont29: "This is cost of new speedy undo code, it expect current datablocks to match those of current undo step, otherwise... bad things will happen"; ideasman42: "Operators that don't set the undo flag but add/remove library data are going to crash." Resolution was documentation (commit `69a7948575` adding the gotcha), not a code fix — the constraint is permanent. For TEE this is a hard rule: every agent batch that creates/deletes datablocks in a GUI-attached session MUST end with an undo push, both to create the checkpoint and to prevent crashing the host when the human presses Ctrl+Z.

Source: [https://projects.blender.org/blender/blender/issues/77557](https://projects.blender.org/blender/blender/issues/77557)

### Undo/redo invalidates cached Python references; session_uid is the stable key

Official gotcha: "you should assume that undo and redo always invalidates all bpy.types.ID instances" (demonstrated by `hash(bpy.context.object)` changing across undo); the modern system keeps most unchanged datablock pointers valid but with "no guarantee of any kind... Use it at your own risk." The safe cross-undo identity is `bpy.types.ID.session_uid`: "A session-wide unique identifier for the data block that remains the same across renames and internal reallocations, unchanged when reloading the file." TEE's differential cache should key on `session_uid`, never on names (renameable) or object identity/pointers.

Source: [https://docs.blender.org/api/current/info_gotchas_crashes.html](https://docs.blender.org/api/current/info_gotchas_crashes.html) ; [https://docs.blender.org/api/current/bpy.types.ID.html](https://docs.blender.org/api/current/bpy.types.ID.html)

### Background mode has no undo stack by default (source-level)

`wm_files.cc` creates the undo stack only when not headless: `if (use_data) { if (!G.background) { wm->runtime->undo_stack = BKE_undosys_stack_create(); ...`. `ed_undo.cc`'s init poll sets the operator error: "Undo disabled at startup in background-mode (call `ed.undo_push()` to explicitly initialize the undo-system)". `ED_undo_push` returns early in background if the stack is nullptr. So in `blender --background` and in the pip `bpy` module, `bpy.ops.ed.undo()` raises until the stack is explicitly initialized, and no operator ever auto-pushes steps.

Source: [https://github.com/blender/blender/blob/main/source/blender/windowmanager/intern/wm_files.cc](https://github.com/blender/blender/blob/main/source/blender/windowmanager/intern/wm_files.cc) ; `source/blender/editors/undo/ed_undo.cc`

### Background undo CAN be opted into via ed.undo_push (deliberate exception)

`ed_undo_push_exec` in `ed_undo.cc`: "Exception for background mode, see: #60934. NOTE: since the undo stack isn't initialized on startup, background mode behavior won't match regular usage, this is just for scripts to do explicit undo pushes." — it lazily runs `BKE_undosys_stack_create()` when `G.background`. History: `undo_push`/`undo_history` worked in background in 2.79, segfaulted in 2.80 beta (devtalk thread 5217, Jan 2019; brecht: "if undo work in the background in 2.7 I see no reason it should not in 2.8"), and was restored via #60934. So an in-memory (memfile) checkpoint/rollback loop — `ed.undo_push(message=...)` per batch, `ed.undo()`/`undo_history` to roll back — is viable in the batch backend without touching disk.

Source: [https://github.com/blender/blender/blob/main/source/blender/editors/undo/ed_undo.cc](https://github.com/blender/blender/blob/main/source/blender/editors/undo/ed_undo.cc) ; [https://devtalk.blender.org/t/bpy-ops-ed-undo-push-causes-segfault-in-background-mode/5217](https://devtalk.blender.org/t/bpy-ops-ed-undo-push-causes-segfault-in-background-mode/5217)

### Background undo path is fragile across versions

Issue #149890 "Blender 5.0 undo system related crash" (filed 2025-11-14, now closed): a script driving `blender --background --python test_crash.py` using `bpy.ops.ed.undo_push(message=...)` + `bpy.ops.ed.undo()` crashed with `EXCEPTION_ACCESS_VIOLATION` in 5.0/5.1-alpha; worked in 4.5. Demonstrates the background-undo exception is exercised by real pipelines (Bonsai/IfcOpenShell) but regresses; TEE should version-gate and integration-test it per Blender release rather than assume it.

Source: [https://projects.blender.org/blender/blender/issues/149890](https://projects.blender.org/blender/blender/issues/149890)

### pip bpy module constraints for the batch backend

Official "Blender as a Python Module" page: loads the default startup scene (cube/camera/light) and behaves as if `--factory-startup`; reset state with `bpy.ops.wm.read_factory_settings(use_empty=True)`; `importlib.reload` of `bpy` raises; "Only a single .blend file can be edited at a time" — parallel isolated states require multiple processes (`multiprocessing` recommended); `bpy.types.BlendDataLibraries.load()`/`write()` and `bpy.data.temp_data()` ("a temporary data-context to avoid manipulating the current .blend file") are the in-process alternatives to full file loads. Python threads remain unsupported.

Source: [https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html](https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html)

### Temp-file snapshot primitive and its cost profile

`bpy.ops.wm.save_as_mainfile(filepath=..., copy=True, compress=True)`: the `copy` param = "Save a copy of the actual working state but does not make saved file active" (`bpy.data.filepath` unchanged); rollback via `bpy.ops.wm.open_mainfile(filepath=...)` or `bpy.ops.wm.revert_mainfile()`. Cost mitigation: since Blender 3.0, compressed `.blend` files use Zstandard level 3 instead of gzip — per the author (Lukas Stockner, bf-committers, Aug 2021) saving is roughly 90% faster and loading roughly 60% faster than gzip at similar file size, with multithreaded compression, and a skippable-frame index enables efficient partial reading of linked files. Hidden cost of reload-based rollback: file load clears all msgbus subscriptions and all non-`@persistent` handlers and invalidates every cached Python reference (`session_uid` survives reload).

Source: [https://docs.blender.org/api/current/bpy.ops.wm.html](https://docs.blender.org/api/current/bpy.ops.wm.html) ; [https://archive.blender.org/lists/bf-committers/2021-August/051124.html](https://archive.blender.org/lists/bf-committers/2021-August/051124.html)

### Partial snapshot primitive: libraries.write

`bpy.data.libraries.write(filepath, datablocks: set[bpy.types.ID], path_remap='NONE'|'RELATIVE'|'RELATIVE_ALL'|'ABSOLUTE', fake_user=False, compress=False)` writes only the chosen datablocks to a `.blend`, and "Indirectly referenced data-blocks will be expanded and written too." Restore via `bpy.data.libraries.load(filepath)` (link or append). This gives TEE per-datablock-set checkpoints (e.g. just the materials/node_groups an agent batch will touch) far cheaper than whole-file snapshots — but restore-by-append creates new IDs (name collisions get `.001` suffixes) rather than in-place rollback, so it suits "restore lost originals" more than transactional revert.

Source: [https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html](https://docs.blender.org/api/current/bpy.types.BlendDataLibraries.html)

### Library overrides are not a snapshot/rollback mechanism

Manual definition: "Library Overrides is a system designed to allow editing linked data, while keeping it in sync with the original library data... When the library data changes, unmodified properties of the overridden one will be updated accordingly." It is a linked-data editing layer, not a state-capture facility; additionally the undo gotcha notes tools must not modify library data and Python doing so risks crashes on undo. A link-base-file + override-layer architecture could theoretically isolate agent edits, but it changes the whole document model and is far costlier than temp-file snapshots.

Source: [https://docs.blender.org/manual/en/latest/files/linked_libraries/library_overrides.html](https://docs.blender.org/manual/en/latest/files/linked_libraries/library_overrides.html) ; [https://docs.blender.org/api/current/info_gotchas_crashes.html](https://docs.blender.org/api/current/info_gotchas_crashes.html)

### Edit-mode boundary invalidates references (affects diff cache and checkpoints)

Official gotcha: switching modes (`bpy.ops.object.mode_set(mode='EDIT'/'OBJECT')`) re-allocates object data — references to mesh vertices/polygons/UVs, bones, curve points cannot be accessed across a mode switch (crash). Edit-mode changes also live in a separate undo step type from Global (memfile) undo. TEE's hasher must re-fetch data per access and be mode-aware; #65681 (undo after `bpy.data.objects.remove()` in edit mode crashed) shows deletion+mode+undo interactions were a real crash class, folded into #77557.

Source: [https://docs.blender.org/api/current/info_gotchas_crashes.html](https://docs.blender.org/api/current/info_gotchas_crashes.html) ; [https://projects.blender.org/blender/blender/issues/77557](https://projects.blender.org/blender/blender/issues/77557)

## Recommendations for TEE

1. Use a two-channel change detector in GUI-attached Blender: `msgbus.subscribe_rna` for cheap property-level attribution of UI/Python edits (it self-coalesces to one callback per property per update cycle), plus a `@persistent` `depsgraph_update_post` handler as the catch-all that msgbus misses (viewport transforms, adds/removes via `depsgraph.id_type_updated`). Neither channel gives old values or sub-datablock detail, so the handler should only mark `session_uid`s dirty (with the 3 coarse flags as hints) and a `bpy.app.timers` callback should do the actual poll-and-hash diff against TEE's cached snapshot — never compute diffs inside the handler (re-entrancy: modifying data or even console printing inside `depsgraph_update_post` recurses, issue #65155).
2. Key the differential scene cache by `ID.session_uid` (stable across renames, undo reallocation, and file reload), never by name or Python object identity; treat `undo_post`, `redo_post`, and `load_post` as full cache-epoch invalidations because undo restores values without firing msgbus, and re-register all msgbus subscriptions in a `@persistent` `load_post` handler since file load clears them.
3. Make "end every mutation batch with an undo checkpoint" a hard invariant of the bridge in GUI mode: execute agent commands from a timer-drained queue inside a custom operator with `bl_options={'REGISTER','UNDO'}` returning `FINISHED`, or follow raw executemany batches with `bpy.ops.ed.undo_push(message='TEE: <batch-id>')`. This is simultaneously the transaction checkpoint and a crash-prevention requirement — since Blender 2.83, adding/removing datablocks without an undo step crashes Blender on the user's next Ctrl+Z (#77557, resolved by documentation, i.e. permanent).
4. Implement GUI-mode rollback as `bpy.ops.ed.undo()` (or `bpy.ops.ed.undo_history(item=N)` to a labeled TEE checkpoint), but budget-check first: checkpoints share the user's `undo_steps` preference (default 32, max 256) and Global Undo keeps a full in-memory copy of the file per step; warn or raise the preference when a transaction needs more steps, never modify library-linked data (undo skips it), and drop every cached reference after any undo — pointer survival is explicitly "no guarantee of any kind".
5. For the background/pip-`bpy` batch backend, default to temp `.blend` snapshots as the transaction mechanism: `bpy.ops.wm.save_as_mainfile(filepath=scratch, copy=True, compress=True)` before each risky batch (Zstd level 3 since 3.0 makes compressed saving ~90% faster than the old gzip) and `bpy.ops.wm.open_mainfile(filepath=scratch)` to roll back, followed by full re-registration of handlers/subscriptions and cache rebuild from `session_uid`s.
6. Offer an opt-in fast path for background rollback using the deliberate #60934 exception — `bpy.ops.ed.undo_push()` lazily creates the undo stack in background, after which `ed.undo()`/`undo_history` work as in-memory memfile snapshots with no disk I/O — but gate it behind per-Blender-version integration tests, since this path regressed as recently as Blender 5.0 (#149890) and "background mode behavior won't match regular usage" (no automatic operator pushes).
7. Use `bpy.data.libraries.write(filepath, {ids}, compress=True)` for cheap partial checkpoints when a batch's write-set is known (it auto-expands indirect references), treating it as "recover lost originals" rather than in-place revert (append-restore creates renamed copies); do not build rollback on library overrides — they are a linked-data editing system, not state capture.
8. Architect the bridge as: MCP server socket in a separate thread/process, command queue, single `bpy.app.timers` pump on the main thread (`persistent=True`) — Blender's Python is not thread-safe and every handler/timer/msgbus callback runs on the main thread, so tune the pump interval and per-tick hash budget explicitly: the poll-and-hash load is the price of Blender's missing fine-grained change tracking, and it directly competes with the user's interactive frame rate.
9. For token efficiency, exploit the granularity facts: report diffs at the level Blender can actually attest (which IDs changed + geometry/transform/shading flags + hashed property deltas TEE computes itself), include the batch's undo checkpoint label/id in every mutation response so the model can request rollback by name, and mark diffs that occurred outside agent batches as "user edits" detected via the depsgraph channel (msgbus silence during a depsgraph-flagged transform is the signature of a viewport drag).
