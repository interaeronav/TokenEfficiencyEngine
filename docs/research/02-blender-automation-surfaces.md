# Blender Automation Surfaces

*Deep-research digest, 2026-08-21. Part of the TEE research corpus — see [00-index.md](00-index.md).*

## Summary

Blender exposes one programmatic surface — the embedded Python `bpy` API — with two distinct layers: direct datablock access (`bpy.data`, no context needed, deterministic) and UI-oriented operators (`bpy.ops`, which depend on `bpy.context`, can fail `poll()` with opaque `RuntimeError`s, and since 4.0 require `Context.temp_override()` instead of override dicts). The API is strictly main-thread: Python threads crash Blender unless joined before script end, so every live-bridge implementation (e.g. `ahujasid/blender-mcp`) runs a TCP socket server in an add-on thread and drains a `queue.Queue` from a single persistent `bpy.app.timers` callback on the main thread.

Headless automation is via `blender --background --python script.py` (rich CLI: `--python-expr`, `--factory-startup`, `--addons`, `--python-exit-code`) or the pip-installable `bpy` module (4.2–4.5 wheels pinned to Python 3.11), which behaves like background mode with one `.blend` open at a time. Blender 4.2 LTS introduced the extensions platform (`blender_manifest.toml` replaces `bl_info`, with wheels bundling and declared network/files permissions) — the correct packaging for a TEE bridge add-on.

Geometry Nodes and material node graphs are fully constructible via Python (4.0 moved group sockets to `NodeTree.interface.new_socket`; 4.0 renamed Principled BSDF sockets; 4.2 renamed EEVEE to `BLENDER_EEVEE_NEXT`), OSL shaders load via `ShaderNodeScript` (Cycles, CPU + OptiX-only GPU), GLSL exists only for viewport/offscreen drawing via the `gpu` module, and all physics (rigid body, cloth, Mantaflow fluids) are automatable via modifier settings plus bake operators (`bpy.ops.ptcache.*`, `bpy.ops.fluid.*`).

## Findings

### bpy architecture: data vs ops vs context

Blender embeds a persistent Python interpreter loaded at startup; the same API drives its own UI. `bpy.data` gives direct access to internal datablocks (e.g. `bpy.data.objects["Cube"].data.vertices[0].co.x += 1.0` modifies internal data directly and updates the viewport). `bpy.ops` calls operators (user tools); `bpy.context` reflects the active object/mode/area. Python class integration is deliberately limited to `bpy.types.Panel`, `Menu`, `Operator`, `PropertyGroup`, `KeyingSet`, `RenderEngine` — custom mesh modifiers, object types, or shader nodes require C/C++. On startup Blender imports all modules in `scripts/startup/`.

Source: [https://docs.blender.org/api/current/info_overview.html](https://docs.blender.org/api/current/info_overview.html)

### bpy.ops limitations (why bridges should prefer bpy.data)

Documented operator limits: (1) cannot pass data such as objects/meshes/materials as arguments — operators read the context instead; (2) the return value is only success/cancel status, not the operation result; (3) `poll()` can fail with `RuntimeError: Operator bpy.ops.X.poll() failed, context is incorrect` with no detail (`poll_message_set` exists but is rarely used); (4) some operators only work in specific editors (e.g. `bpy.ops.texture.slot_move`, `bpy.ops.constraint.limitdistance_reset`, `bpy.ops.object.modifier_copy`, `bpy.ops.buttons.file_browse` are properties-editor-only). `bpy.types.Context.temp_override` is the mechanism for supplying operator context.

Source: [https://docs.blender.org/api/current/info_gotchas_operators.html](https://docs.blender.org/api/current/info_gotchas_operators.html)

### 4.0 breaking change: context overrides

Blender 4.0 removed the context-override dict argument to `bpy.ops` calls in favor of `context.temp_override(...)` (commit `ac263a9bce`). Any bridge targeting 4.0–4.5 must use `with bpy.context.temp_override(**ctx): bpy.ops.x.y()`.

Source: [https://developer.blender.org/docs/release_notes/4.0/python_api/](https://developer.blender.org/docs/release_notes/4.0/python_api/)

### Thread safety

Official docs: "Python threads cause Blender to crash in hard to diagnose ways"; no work has been done to make the Python integration thread-safe. Threads work only if they finish before the script does (`threading.Thread.join()`), i.e. only while the main Blender thread is blocked; while any thread runs, no code including the main thread may use `bpy` or any Blender API. Even stdlib modules that use threads internally (e.g. `multiprocessing.Queue`) can crash Blender. A `threading.Timer` left running after script end causes "random crashes or errors in Blender's own drawing code". The recommended alternative for independent work is the `multiprocessing` module.

Source: [https://docs.blender.org/api/current/info_gotchas_threading.html](https://docs.blender.org/api/current/info_gotchas_threading.html)

### bpy.app.timers (main-thread scheduling)

`bpy.app.timers.register(function, *, first_interval=0, persistent=False)`: the function takes no args and returns `None` (unregister) or a float (seconds until next call); `persistent=True` keeps the timer across file loads. Also `is_registered(function)` and `unregister(function)`. `functools.partial` is the documented way to bind arguments. Timers run on Blender's main thread, making them the standard mechanism for marshalling work from external connections into the `bpy` API.

Source: [https://docs.blender.org/api/current/bpy.app.timers.html](https://docs.blender.org/api/current/bpy.app.timers.html)

### Live-session bridge reference implementation (BlenderMCP)

`ahujasid/blender-mcp` has two components — a Blender add-on (`addon.py`) running a TCP socket server (class `BlenderMCPServer`, default `localhost:9876`, JSON request/response over the socket, started from the N-panel "Start MCP Server" button) and an MCP server run via `uvx blender-mcp` (requires-python `>=3.10`). Threading model: client handler threads only parse JSON and push commands to a `queue.Queue`; a SINGLE persistent `bpy.app.timers` timer (`_drain_command_queue`) registered once at server start drains the queue on the main thread. In-code comment: "bpy.app.timers is not thread-safe, so registering a timer per command (the previous approach) could silently drop the callback - on Windows especially". The command set includes `get_scene_info`, `get_object_info`, `get_viewport_screenshot`, `execute_code` (arbitrary Python).

Source: [https://github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) (`addon.py`, `README.md`)

### Headless CLI surface

`blender -b`/`--background` runs UI-less (audio device disabled; re-enable with `-setaudio Default`). Python flags: `-P`/`--python <file>`, `--python-text <textblock>`, `--python-expr <expression>`, `--python-console` (interactive), `--python-exit-code <0..255>` (exit code on uncaught Python exception), `--python-use-system-env` (honor `PYTHONPATH`/user site-packages), `-y`/`--enable-autoexec`, `--addons <comma,list>`, `--factory-startup`, `--online-mode`. Arguments after `--` are passed unchanged and read via `sys.argv`. The CLI is order-sensitive: `blender --background test.blend --render-output /tmp --render-frame 1` works; putting `--render-frame` before `--render-output` does not apply the output path.

Source: [https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html](https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html)

### Background-mode depsgraph caveat

`--disable-depsgraph-on-file-load` skips building/evaluating ViewLayer dependency graphs when loading a blend in background mode; scripts then must call `depsgraph = context.evaluated_depsgraph_get()` explicitly. Docs note: "this is a temporary option, in the future depsgraph will never be automatically generated on file load in background mode" — bridges reading evaluated (modifier/geometry-nodes-applied) data should always go through `evaluated_depsgraph_get()`.

Source: [https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html](https://docs.blender.org/manual/en/4.5/advanced/command_line/arguments.html)

### bpy as a pip module (out-of-process automation)

`pip install bpy` gives an import-able Blender equivalent to `--background` mode. Specifics: `bpy.app.binary_path` defaults to an empty string; internal modules (`gpu`, `mathutils`) must be imported AFTER `bpy`; on load it contains the DEFAULT STARTUP SCENE (default cube, camera, light) — use `bpy.ops.wm.read_factory_settings(use_empty=True)` for an empty file; it behaves as if `--factory-startup` (user prefs ignored; load them via `bpy.ops.wm.read_userpref()`/`read_homefile()`). Limitations: `importlib.reload(bpy)` raises (reset state with `bpy.ops.wm.read_factory_settings()`); only ONE `.blend` is editable at a time — use `multiprocessing` for parallel instances; `bpy.types.BlendDataLibraries.load()`/`write()` and `bpy.types.BlendData.temp_data()` allow reading/writing ID datablocks without switching files; Blender's signal handlers are not installed; some CLI-only functionality (`--threads`, `--log`) has no API equivalent.

Source: [https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html](https://docs.blender.org/api/current/info_advanced_blender_as_bpy.html)

### bpy PyPI version/Python pinning

`bpy` wheels on PyPI: versions 4.2.0–4.2.23, 4.3.0, 4.4.0, 4.5.0–4.5.12, 5.0.x, 5.1.x, 5.2.0. All 4.2–5.0 releases require Python `==3.11.*` (cp311 wheels); `bpy` 5.2.0 requires `==3.13.*`. Platforms: `macosx_11_0` x86_64/arm64, `manylinux_2_28_x86_64`, `win_amd64` (`win_arm64` added by 5.2). So a TEE bridge embedding `bpy` for Blender 4.2–4.5 must run under Python 3.11 exactly.

Source: [https://pypi.org/pypi/bpy/json](https://pypi.org/pypi/bpy/json)

### Extensions platform (Blender 4.2+)

Extensions (add-ons, themes) shipped in Blender 4.2 LTS with the official platform [extensions.blender.org](https://extensions.blender.org); an extension is a `.zip` containing files plus `blender_manifest.toml`. Required manifest fields: `schema_version="1.0.0"`, `id`, `version`, `name`, `tagline`, `maintainer`, `type` (`"add-on"`|`"theme"`), `blender_version_min` (>= `"4.2.0"`), `license` (SPDX list e.g. `"SPDX:GPL-3.0-or-later"`). Optional: `blender_version_max`, `tags`, `platforms` (`["windows-x64","windows-arm64","macos-x64","macos-arm64","linux-x64"]`), `wheels` (list of bundled `.whl` paths for third-party Python deps), `[permissions]` with keys `files`/`network`/`clipboard`/`camera`/`microphone` each mapping to a short reason string (<=64 chars), `[build]` `paths_exclude_pattern`. Extensions can be built/validated/installed from the command line.

Source: [https://docs.blender.org/manual/en/4.5/advanced/extensions/getting_started.html](https://docs.blender.org/manual/en/4.5/advanced/extensions/getting_started.html) and [https://developer.blender.org/docs/release_notes/4.2/extensions/](https://developer.blender.org/docs/release_notes/4.2/extensions/)

### Legacy add-on vs extension differences

Converting a legacy add-on to an extension: remove `bl_info` (metadata moves to the manifest), replace module-name references with `__package__`, make all imports relative, pack external Python dependencies as wheels. Legacy add-ons remain supported via the "Install legacy Add-on" button. Add-ons needing internet must check read-only `bpy.app.online_access` (and `bpy.app.online_access_overriden` for better errors) — network access is user-controllable and off in some configurations; per-extension user files go under `bpy.utils.extension_path_user(__package__, path="", create=True)`. Add-ons are "typically distributed as extensions" in 4.2+; the only structural difference from built-in modules is the required `blender_manifest.toml`.

Source: [https://docs.blender.org/manual/en/4.5/advanced/extensions/addons.html](https://docs.blender.org/manual/en/4.5/advanced/extensions/addons.html)

### Geometry Nodes: 4.0 interface API (breaking)

The node group socket API moved from `NodeTree.inputs`/`.outputs` to `NodeTree.interface` in 4.0: `tree.interface.new_socket(name, *, description='', in_out='INPUT'|'OUTPUT', socket_type='DEFAULT', parent=None) -> NodeTreeInterfaceSocket`; `socket_type` accepts only base socket type names (e.g. `'NodeSocketFloat'`, NOT `'NodeSocketFloatFactor'`); `tree.interface.new_panel(name)`, `.copy(item)`, `.remove(item)`, `.move(socket, to_index)`, `.move_to_parent(socket, panel, to_index)`; iterate `tree.interface.items_tree` checking `item.item_type` (`'SOCKET'`|`'PANEL'`) and `item.in_out`. Old `tree.inputs.new()`/`outputs.new()` code from <=3.6 is broken in 4.0+.

Source: [https://developer.blender.org/docs/release_notes/4.0/python_api/](https://developer.blender.org/docs/release_notes/4.0/python_api/) and [https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html](https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html)

### Geometry Nodes: programmatic construction workflow

Create a tree: `bpy.data.node_groups.new(name, 'GeometryNodeTree')`; add nodes with `tree.nodes.new('GeometryNodeXxx')` and wire with `tree.links.new(out_socket, in_socket)`; attach with `obj.modifiers.new(name, type='NODES')` and `mod.node_group = tree`; set group inputs on the modifier by subscripting with the socket's auto-generated read-only identifier (`NodeTreeInterfaceSocket.identifier`, form `'Socket_N'` in 4.x) rather than its display name. Since 4.0, `node.inputs[x]`/`node.outputs[x]` lookups take socket identifiers and availability status into account (commit `e4ad58114b`).

Source: [https://developer.blender.org/docs/release_notes/4.0/python_api/](https://developer.blender.org/docs/release_notes/4.0/python_api/) ; [https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html](https://docs.blender.org/api/current/bpy.types.NodeTreeInterface.html)

### Material node graphs via Python + 4.0 Principled BSDF renames

Materials use node trees (`mat.use_nodes=True`; `mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')`). Blender 4.0 revamped the Principled BSDF toward OpenPBR and RENAMED sockets (breaks scripts that set inputs by name): Subsurface → `'Subsurface Weight'`; `'Subsurface Color'` removed (use Base Color); Specular → `'Specular IOR Level'`; `'Specular Tint'` changed float → color; Transmission → `'Transmission Weight'`; Coat → `'Coat Weight'`; Sheen → `'Sheen Weight'`; Emission → `'Emission Color'`. Also 4.0 merged the Glossy+Anisotropic BSDF into `ShaderNodeBsdfAnisotropic` (`'ShaderNodeBsdfGlossy'` still accepted as a creation alias). `NodeItem`/`NodeCategory` definitions were removed for shader and compositor nodes; extend add-menus via `NODE_MT_shader_node_add_all` / `NODE_MT_compositor_node_add_all`.

Source: [https://developer.blender.org/docs/release_notes/4.0/python_api/](https://developer.blender.org/docs/release_notes/4.0/python_api/)

### EEVEE engine identifier change in 4.2

Blender 4.2 replaced EEVEE with EEVEE Next; the render engine identifier changed to `'BLENDER_EEVEE_NEXT'` (`scene.render.engine`). Motion blur settings were de-duplicated and moved: `scene.eevee.use_motion_blur` → `scene.render.use_motion_blur`, `scene.eevee.motion_blur_position`/`motion_blur_shutter` → `scene.render.*`; EEVEE Bloom deprecated (#123059). Also 4.2 added `bpy.app.python_args` for spawning a Python subprocess matching Blender's environment.

Source: [https://developer.blender.org/docs/release_notes/4.2/python_api/](https://developer.blender.org/docs/release_notes/4.2/python_api/)

### OSL authoring surface

OSL works within Cycles only, for custom surface/volume/displacement shaders. Enable "Open Shading Language" in Render Properties (`scene.cycles.shading_system`), then add a Script Node (`bpy.types.ShaderNodeScript`) in the material node tree with Mode=Internal (Blender text datablock) or External (`.osl` source or precompiled `.oso` from disk); Blender auto-compiles `.osl` to `.oso`, with compile errors printed to the system console; node outputs are generated from the shader's output parameters and connect to the rest of the node graph. UI metadata via parameter attributes like `[[ string label = "My Label" ]]`, `[[ string widget = "null"|"boolean"|"checkbox" ]]`.

Source: [https://docs.blender.org/manual/en/4.5/render/shader_nodes/osl.html](https://docs.blender.org/manual/en/4.5/render/shader_nodes/osl.html)

### OSL GPU limitations (4.x)

Manual (4.5): "OSL is not supported with GPU rendering unless using the OptiX backend" (OptiX OSL support landed in Blender 3.5: "OSL can now be used with OptiX on the GPU, in addition to existing support with CPU rendering"). OptiX-backend limitations: no on-demand texture loading/mip-mapping memory savings; texture lookups need a constant image path per call; Cell/Simplex/Gabor noise unavailable; `trace()` non-functional, so Ambient Occlusion and Bevel nodes do not work. `trace(point,vector,...)` itself is CPU-only, for probing nearby geometry (`getmessage("trace",..)`), not lighting.

Source: [https://docs.blender.org/manual/en/4.5/render/shader_nodes/osl.html](https://docs.blender.org/manual/en/4.5/render/shader_nodes/osl.html) and [https://developer.blender.org/docs/release_notes/3.5/cycles/](https://developer.blender.org/docs/release_notes/3.5/cycles/)

### GLSL surface = gpu module (viewport/offscreen only, not materials)

GLSL in Blender is exposed through the `gpu` module for drawing, not material authoring (EEVEE materials are node-only; custom shader nodes require C/C++). `gpu.types.GPUShader` = vertex + fragment (+ optional geometry) shader program; built-ins via `gpu.shader.from_builtin('UNIFORM_COLOR', 'FLAT_COLOR', ...)`; the recommended modern path is `gpu.types.GPUShaderCreateInfo` (`vertex_in`/`vertex_out`/`sampler`/`push_constant` + `vertex_source`/`fragment_source`), plus `gpu_extras.batch.batch_for_shader` for batches and `gpu.types.GPUOffScreen(w,h)` for offscreen rendering to texture/image. GLSL sources are reinterpreted to MSL on Apple platforms via a partial compatibility layer (matrix-constructor restrictions; `vertex`/`fragment`/`kernel` are reserved words). Blender 4.5 deprecates the raw `GPUShader` constructor (removal in 5.0) and `shader.program` now returns `-1` — future-proof bridges must use `GPUShaderCreateInfo`.

Source: [https://docs.blender.org/api/current/gpu.html](https://docs.blender.org/api/current/gpu.html) and [https://developer.blender.org/docs/release_notes/4.5/python_api/](https://developer.blender.org/docs/release_notes/4.5/python_api/)

### Rigid body automation

Operators: `bpy.ops.rigidbody.object_add(type='ACTIVE')` / `objects_add` / `object_remove` / `world_add` / `world_remove` / `constraint_add(type='FIXED')` / `connect(con_type='FIXED', pivot_type='CENTER', connection_pattern='SELECTED_TO_ACTIVE')` / `mass_calculate(material='DEFAULT', density=1.0)` / `shape_change(type='MESH')` / `bake_to_keyframes(frame_start=1, frame_end=250, step=1)`. Simulation state lives in `scene.rigidbody_world` (`bpy.types.RigidBodyWorld`) and per-object `obj.rigid_body` settings; `bake_to_keyframes` converts sim results to keyframes for deterministic export.

Source: [https://docs.blender.org/api/current/bpy.ops.rigidbody.html](https://docs.blender.org/api/current/bpy.ops.rigidbody.html)

### Point-cache baking (rigid body, cloth, particles, softbody)

`bpy.ops.ptcache.bake(bake=False)`, `bpy.ops.ptcache.bake_all(bake=True)`, `bake_from_cache()`, `free_bake()`, `free_bake_all()` ("Delete all baked caches of all objects in the current scene"). The single-cache operators are context-dependent (they need a `point_cache` in context — supply via `bpy.types.Context.temp_override` in scripts); `bake_all` operates scene-wide and is the simplest headless path. Cloth is a modifier: `obj.modifiers.new(name, type='CLOTH')` -> `bpy.types.ClothModifier` with `.settings` (`ClothSettings`) and `.point_cache`.

Source: [https://docs.blender.org/api/current/bpy.ops.ptcache.html](https://docs.blender.org/api/current/bpy.ops.ptcache.html) ; [https://docs.blender.org/api/current/bpy.types.ClothModifier.html](https://docs.blender.org/api/current/bpy.types.ClothModifier.html)

### Fluid (Mantaflow) automation

Fluid is a modifier: `obj.modifiers.new(name, type='FLUID')`; `modifier.fluid_type` in `{'DOMAIN','FLOW','EFFECTOR'}`. `bpy.types.FluidDomainSettings`: `domain_type` Literal `['GAS','LIQUID']` (default `'GAS'`); `cache_type` Literal `['REPLAY','MODULAR','ALL']` (default `'REPLAY'` — timeline-driven; `'MODULAR'` bakes stages separately; `'ALL'` bakes everything at once); `resolution_max` int [6,10000] default 32 (voxels on longest domain side); `cache_directory`, `cache_frame_start`/`end`/`offset`, per-stage pause frames; read-only `has_cache_baked_data` etc. for bake-state polling. Bake operators: `bpy.ops.fluid.bake_all`/`bake_data`/`bake_mesh`/`bake_noise`/`bake_particles`/`bake_guides` and matching `free_*`, plus `pause_bake` — these are context-dependent operators (they need the domain object active).

Source: [https://docs.blender.org/api/current/bpy.types.FluidDomainSettings.html](https://docs.blender.org/api/current/bpy.types.FluidDomainSettings.html) and [https://docs.blender.org/api/current/bpy.ops.fluid.html](https://docs.blender.org/api/current/bpy.ops.fluid.html)

### Mesh data access modes and bulk APIs

Edit-Mode keeps its own mesh copy, written back only on mode exit — `obj.data` is stale in Edit-Mode; use `bmesh.from_edit_mesh()` (and `bmesh.types.BMesh.to_mesh()`) or exit Edit-Mode first. Three face representations: `mesh.polygons` (`MeshPolygon`, object mode), `mesh.loop_triangles` (`MeshLoopTriangle`, tessellation), bmesh `BMFace` (edit mode). Bulk geometry creation without operators: `bpy.types.Mesh.from_pydata(vertices, edges, faces, shade_flat=True)`; bulk attribute I/O via `bpy_prop_collection.foreach_get`/`foreach_set` (flat sequences/NumPy buffers) avoids per-element Python overhead.

Source: [https://docs.blender.org/api/current/info_gotchas_meshes.html](https://docs.blender.org/api/current/info_gotchas_meshes.html) ; [https://docs.blender.org/api/current/bpy.types.Mesh.html](https://docs.blender.org/api/current/bpy.types.Mesh.html) ; [https://docs.blender.org/api/current/bpy.types.bpy_prop_collection.html](https://docs.blender.org/api/current/bpy.types.bpy_prop_collection.html)

### Script loading models

Ways to run code: text editor Run Script, interactive console, `blender --python /path/script.py`, `--python-expr`; run as modules via `import`, a text datablock with the Register flag, files in `scripts/startup/` (auto-imported), or add-on enable (loads as a Python module). Direct execution leaves registered classes hard to unregister later — docs recommend module import for anything registering classes. 4.0 armature API break relevant to rigging automation: bone layers/groups were removed, replaced by bone collections; `edit_bones.new()` no longer auto-assigns to a collection.

Source: [https://docs.blender.org/api/current/info_overview.html](https://docs.blender.org/api/current/info_overview.html) ; [https://developer.blender.org/docs/release_notes/4.0/python_api/](https://developer.blender.org/docs/release_notes/4.0/python_api/)

## Recommendations for TEE

1. Route all bridge commands through `bpy.data` / `bmesh` / `from_pydata` / `foreach_set` direct-data paths instead of `bpy.ops` wherever possible: `bpy.ops` cannot take datablock arguments, returns only success/cancel, and fails `poll()` with uninformative "context is incorrect" `RuntimeError`s — each such failure costs an AI round trip. Reserve `bpy.ops` for the few things with no data API (bakes, some file I/O) and wrap those with server-side `bpy.context.temp_override()` plus pre-validated context so the model never sees a poll failure.
2. For the live-session transport, copy the proven BlenderMCP pattern but harden it: add-on TCP socket server on localhost, client threads that ONLY parse JSON and enqueue to `queue.Queue`, and one persistent `bpy.app.timers` timer (registered once at server start, `persistent=True`) draining the queue on the main thread. Never call any `bpy` API — including `bpy.app.timers.register` — from a worker thread; Blender's Python is not thread-safe and per-command timer registration silently drops callbacks on Windows.
3. Offer two execution backends behind the same tool schema: (a) live GUI Blender via the add-on socket for interactive work, and (b) the pip `bpy` module or `blender --background --python` subprocess for batch/render jobs. For 4.2–4.5 pin the bridge's Python to exactly 3.11 (`bpy` wheels are `==3.11.*`); in bpy-module mode call `bpy.ops.wm.read_factory_settings(use_empty=True)` first (the default scene contains a cube), and remember only one `.blend` can be open per process (use `multiprocessing` for parallelism).
4. Package the Blender-side component as a 4.2+ extension: `blender_manifest.toml` with `schema_version` 1.0.0, `blender_version_min` `"4.2.0"`, `[permissions]` `network = "..."` declared, third-party deps bundled as wheels, relative imports and `__package__` (no `bl_info`). Gate any outbound connection on `bpy.app.online_access`.
5. Token efficiency — responses: never dump full scene graphs. Return compact structured summaries (object name, type, counts, bbox), paginate/filter server-side, and expose an explicit `get_object_info(name)` for drill-down. For visual verification return a downscaled viewport screenshot (BlenderMCP's `get_viewport_screenshot` precedent) or a `GPUOffScreen` render rather than textual geometry.
6. Token efficiency — requests: expose high-level macro tools (`create_object`, `assign_pbr_material`, `add_geometry_nodes_setup`, `bake_simulation`) that expand to many `bpy` calls server-side, plus one `execute_code` escape hatch. Embed a version-aware compatibility shim so the model never burns tokens on 4.x API drift: 4.0 `NodeTree.interface.new_socket` vs old `tree.inputs.new`, 4.0 Principled BSDF socket renames (`Subsurface Weight`, `Specular IOR Level`, `Transmission Weight`, `Emission Color`), 4.0 `temp_override` replacing override dicts, 4.2 `'BLENDER_EEVEE_NEXT'` engine id, 4.5 `GPUShaderCreateInfo` replacing the `GPUShader` constructor.
7. For Geometry Nodes tools, resolve sockets server-side: build trees via `bpy.data.node_groups.new(name,'GeometryNodeTree')` + `interface.new_socket` (base socket types only, e.g. `NodeSocketFloat`), attach via `modifiers.new(type='NODES')`, and map human-readable input names to the auto-generated `NodeTreeInterfaceSocket.identifier` (`'Socket_N'`) so the AI addresses inputs by name, never by identifier bookkeeping.
8. Run simulations and renders as asynchronous jobs: trigger `bpy.ops.ptcache.bake_all` / `bpy.ops.fluid.bake_all` (context-overridden), return a job id immediately, and let the AI poll a cheap status tool backed by read-only cache flags like `FluidDomainSettings.has_cache_baked_data` — this avoids long blocking calls and streamed progress noise. Convert finished rigid-body sims with `bake_to_keyframes` when deterministic downstream export is needed.
9. Shader support: expose OSL as a first-class text-in tool (write a text datablock, create `ShaderNodeScript` in Internal mode, enable `scene.cycles.shading_system`, surface compile errors from the console back as structured errors), but constrain generation when the user renders on GPU (OptiX-only, no `trace`/AO/Bevel, missing Cell/Simplex/Gabor noise). Treat GLSL strictly as a viewport/offscreen drawing surface via `gpu.types.GPUShaderCreateInfo` — do not advertise GLSL material authoring, which Blender does not support.
10. In background/batch mode, always fetch evaluated data via `context.evaluated_depsgraph_get()` (Blender is moving toward never auto-building the depsgraph on file load in background mode), use `--python-exit-code` for reliable failure detection in subprocess mode, and pass job parameters after `--` via `sys.argv`.
