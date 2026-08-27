---
id: ue.python_automation
title: Python, Remote Control and MCP automation in Unreal Engine
domain: software_unreal_engine
tags: [python, unreal-module, editor-scripting, editor-asset-library, editor-actor-subsystem, asset-import-task, datasmith-python, editor-utility-widget, commandlet, headless, remote-control, websocket, mcp, agent, automation]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8. Python API is marked Experimental by Epic but has been stable in practice since 4.20. Unreal MCP plugin is 5.8+ and Experimental."
sources:
  - {title: "Scripting the Unreal Editor Using Python", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Unreal MCP", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Remote Control API HTTP Reference", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Remote Control Quick Start", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-quick-start-for-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Customizing the Datasmith Import Process", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/customizing-the-datasmith-import-process-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
related: [ue.core_concepts, ue.project_setup, ue.archviz_workflow, ue.cpp_extension]
---

# Python, Remote Control and MCP automation in Unreal Engine

**Summary.** This is the operational file for driving Unreal from an AI agent. Unreal embeds **Python 3.11.8** in the editor; the `unreal` module reflects essentially everything exposed to Blueprint, so enabling a plugin instantly widens the Python surface. Scripts run from the console, the File menu, a startup list, `init_unreal.py`, an Editor Utility Widget, or headlessly via a commandlet. On top of that sit two network control planes: the **Remote Control API** (HTTP on port 30010, WebSocket on 30020) and, new in **UE 5.8**, an **official Model Context Protocol server** (`ModelContextProtocol` plugin, HTTP on port 8000) that Claude Code connects to directly. Every code example below uses API signatures verified against the 5.8 Python API reference.

## Key facts

| Item | Value |
|---|---|
| Embedded Python | **3.11.8**, aligned to the VFX Reference Platform |
| Change Python version | Set `UE_PYTHON_DIR` env var, then rebuild the engine from source |
| Required plugins | **Python Editor Script Plugin** (Scripting) + **Editor Scripting Utilities** (Scripting) |
| Enabled per | Project (must be enabled separately for each project) |
| Availability | **Editor only.** Not in PIE, Standalone, or cooked builds |
| Auto-discovered script paths | `<Project>/Content/Python`, `<Engine>/Content/Python`, each enabled plugin's `Content/Python`, `~/Documents/UnrealEngine/Python` |
| Extra paths | `Project Settings > Plugins > Python > Additional Paths`, or `UE_PYTHONPATH` env var |
| Auto-run file | `init_unreal.py` in any of the above paths |
| Startup scripts list | `Project Settings > Plugins > Python > Startup scripts` |
| Console command | `py "C:\path\script.py"` (Cmd mode) or switch the console to Python mode |
| Full-editor CLI | `UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript="<file>"` |
| Headless commandlet | `UnrealEditor-Cmd.exe <uproject> -run=pythonscript -script="<file or code>"` |
| Remote Control HTTP port | **30010** (`Project Settings > Plugins > Web Remote Control`) |
| Remote Control WebSocket port | **30020** (`Project Settings > Plugins > Remote Control`) |
| Remote Control server commands | `WebControl.StartServer`, `WebControl.StopServer`, `WebControl.EnableServerOnStartup` |
| MCP server address | `http://127.0.0.1:8000/mcp` (Streamable HTTP; loopback only) |
| MCP console commands | `ModelContextProtocol.StartServer [port]`, `.StopServer`, `.RefreshTools`, `.GenerateClientConfig <Client\|All>` |

> ⚠️ Never expose the Remote Control or MCP ports beyond the local machine. Epic states plainly that Remote Control should be used only within a LAN or over a VPN, and that the MCP server binds to loopback, rejects non-loopback `Origin` headers, and **has no authentication layer**. Opening either to the internet exposes arbitrary function execution on your workstation.

## Setup

1. `Edit > Plugins` → Scripting → enable **Python Editor Script Plugin** and **Editor Scripting Utilities**. Restart.
2. Create `<Project>/Content/Python/` — it is on `sys.path` automatically.
3. Add `<Project>/Content/Python/init_unreal.py` for anything that must run at every editor start.
4. `Window > Developer Tools > Output Log` — the Python console lives in its input bar. Switch the bar from **Cmd** to **Python** to type Python directly. `print()` output is redirected to the Output Log.

By default the embedded interpreter runs in **isolated mode**. Turn that off with `Project Settings > Plugins > Python > Isolate Interpreter Environment` if you need the host system's `PYTHONPATH`. `UE_PYTHONPATH` is always parsed and added to `sys.path` regardless of isolation mode — it exists so third-party software cannot break Unreal by editing `PYTHONPATH`.

## The six ways to run Python

| Method | Where | Use it for |
|---|---|---|
| Python console (Output Log input bar) | Editor | Interactive exploration, one-liners. The only line-by-line mode |
| `py` console command | Editor | `py "C:\scripts\fix_materials.py"` from Cmd mode |
| `File > Execute Python Script` / `Recent Python scripts` | Editor | Re-running a script; the file is re-read from disk each time |
| `init_unreal.py` | Editor startup | Team-wide initialisation shipped with the project or a plugin |
| `Project Settings > Plugins > Python > Startup scripts` | Editor startup | Per-project scripts, run **after** the default level finishes loading |
| Commandlet / `-ExecutePythonScript` | CLI, optionally headless | Batch jobs, CI, render farms, agent-driven work |

Epic explicitly warns **against** putting `py` inside the `ExecCmd` command-line parameter: it runs before the editor environment is ready, before the startup level is loaded.

### Command-line, full editor

Launches the editor, opens the project, loads the default startup level, then runs the script. The editor shuts down immediately afterwards. Requires the Editor Scripting Utilities plugin.

```
UnrealEditor-Cmd.exe "D:\Okongo\Okongo.uproject" -ExecutePythonScript="D:\scripts\build_scene.py"
```

### Commandlet, headless

Much faster, and can run without the editor UI. **It does not load a level for you** — Epic's documented first line for such a script is:

```python
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level("/Game/Maps/L_Main.L_Main")
```

```
UnrealEditor-Cmd.exe "D:\Okongo\Okongo.uproject" -run=pythonscript -script="D:\\scripts\\batch.py"
```

Inline code also works, with `\n` escaping line breaks:

```
UnrealEditor-Cmd.exe "D:\Okongo\Okongo.uproject" -run=pythonscript ^
  -script="import unreal \nunreal.log(unreal.SystemLibrary.get_engine_version())"
```

Useful companion flags: `-unattended` (suppress modal dialogs), `-nosplash`, `-nopause`, `-NullRHI` (no rendering at all — fastest, but breaks anything needing a GPU), `-stdout`, `-log`, `-LOG=Build.txt`.

## The `unreal` module

```python
import unreal
```

The module exposes nearly everything exposed from C++ to Blueprint in your editor environment. It is **not pre-generated** — it reflects whatever is currently available. Enable a plugin and its Blueprint-exposed API appears. Add a `UFUNCTION(BlueprintCallable)` in your project's C++ and it appears.

Naming translation, applied automatically:

| C++ | Python |
|---|---|
| `UStaticMesh` | `unreal.StaticMesh` |
| `AActor` | `unreal.Actor` |
| `FVector` | `unreal.Vector` |
| `SetActorLocation` | `set_actor_location` |
| `bAutoExposure` | `auto_exposure` |
| `EDatasmithImportScene::NewLevel` | `unreal.DatasmithImportScene.NEW_LEVEL` |

Properties not exposed as first-class Python attributes are reachable with `get_editor_property(name)` / `set_editor_property(name, value)`. Logging: `unreal.log()`, `unreal.log_warning()`, `unreal.log_error()`. Introspection at the console: `help(unreal.EditorActorSubsystem)` and `dir(obj)` are your friends and are faster than searching the docs.

**Subsystems** are the modern entry points:

```python
actor_sub  = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_sub  = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_sub  = unreal.get_editor_subsystem(unreal.EditorAssetSubsystem)
mesh_sub   = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
util_sub   = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
mrq_sub    = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
```

`unreal.EditorLevelLibrary` and much of `unreal.EditorAssetLibrary` predate the subsystems. They still work; prefer `EditorActorSubsystem` / `LevelEditorSubsystem` / `EditorAssetSubsystem` in new code.

## Asset operations — `EditorAssetLibrary`

From the `EditorScriptingUtilities` plugin, module `EditorScriptingUtilities`, file `EditorAssetLibrary.h`. Epic's own note: *all operations can be slow; the editor should not be in Play In Editor mode; it will not work on assets of type level.*

Verified signatures:

```python
import unreal
EAL = unreal.EditorAssetLibrary

EAL.list_assets(directory_path, recursive=True, include_folder=False)  # -> [str]
EAL.load_asset(asset_path)                                            # -> Object
EAL.load_blueprint_class(asset_path)                                  # -> Class
EAL.does_asset_exist(asset_path)                                      # -> bool
EAL.do_assets_exist(asset_paths)                                      # -> bool
EAL.duplicate_asset(source_asset_path, destination_asset_path)        # -> Object
EAL.rename_asset(source_asset_path, destination_asset_path)           # -> bool  (a move)
EAL.save_asset(asset_to_save, only_if_is_dirty=True)                  # -> bool
EAL.save_directory(directory_path, only_if_is_dirty=True, recursive=True)
EAL.delete_asset(asset_path_to_delete)                                # FORCE delete
EAL.delete_directory(directory_path)                                  # FORCE delete, recursive
EAL.consolidate_assets(asset_to_consolidate_to, assets_to_consolidate)
EAL.set_metadata_tag(object, tag, value)
EAL.checkout_asset(asset_to_checkout)
EAL.checkout_directory(directory_path, recursive=True)
EAL.sync_browser_to_objects(asset_paths)
```

`delete_asset` and `delete_directory` are **Force Deletes**: they do not check for references in other levels or by Actors, they close asset editors, and they may clear the Undo History. Do not point one at `/Game`.

### Example — audit and rename to the naming convention

```python
import unreal

EAL = unreal.EditorAssetLibrary
PREFIX_FOR = {
    unreal.StaticMesh: "SM_",
    unreal.Material: "M_",
    unreal.MaterialInstanceConstant: "MI_",
    unreal.Texture2D: "T_",
    unreal.Blueprint: "BP_",
}

def enforce_prefixes(root="/Game/_Project", dry_run=True):
    renamed, skipped = 0, 0
    for path in EAL.list_assets(root, recursive=True, include_folder=False):
        asset = EAL.load_asset(path)
        if asset is None:
            continue
        prefix = next((p for cls, p in PREFIX_FOR.items()
                       if isinstance(asset, cls)), None)
        if prefix is None:
            skipped += 1
            continue
        pkg, _, obj = path.partition(".")
        folder, _, name = pkg.rpartition("/")
        if name.startswith(prefix):
            continue
        new_pkg = "{}/{}{}".format(folder, prefix, name)
        unreal.log("{}  ->  {}".format(pkg, new_pkg))
        if not dry_run:
            EAL.rename_asset(pkg, new_pkg)
        renamed += 1
    unreal.log("renamed={}  skipped={}  dry_run={}".format(renamed, skipped, dry_run))

enforce_prefixes(dry_run=True)
```

Always write the dry-run branch first. A rename pass over a 4 000-asset Datasmith import that goes wrong is not undoable in any practical sense.

## Actor operations — `EditorActorSubsystem`

Module `UnrealEd`, file `EditorActorSubsystem.h`. Verified signatures:

```python
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

sub.get_all_level_actors()                       # -> [Actor], excludes pending-kill / PIE
sub.get_selected_level_actors()                  # -> [Actor]
sub.set_actor_selection_state(actor, should_be_selected)
sub.clear_actor_selection_set()
sub.spawn_actor_from_class(actor_class, location, rotation=[0,0,0], transient=False)
sub.spawn_actor_from_object(object_to_use, location, rotation=[0,0,0], transient=False)
sub.duplicate_actor(actor_to_duplicate, to_world=None, offset=[0,0,0])
sub.duplicate_actors(actors_to_duplicate, to_world=None, offset=[0,0,0])
sub.destroy_actor(actor_to_destroy)
sub.destroy_actors(actors_to_destroy)
sub.convert_actors(actors, actor_class, static_mesh_package_path)
sub.set_actor_transform(actor, world_transform)
sub.set_component_transform(scene_component, world_transform)
sub.get_actor_reference(path_to_actor)           # e.g. "PersistentLevel.PlayerStart"
```

### Example — place the SunSky Actor for Okongo

```python
import unreal

def place_okongo_sun(latitude=-17.4, longitude=17.6, time_zone=2.0,
                     month=12, day=21, solar_time=12.5):
    """Place and configure a SunSky Actor for Okongo, Ohangwena, Namibia.
    Requires the Sun Position Calculator plugin to be enabled."""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    sunsky_class = unreal.EditorAssetLibrary.load_blueprint_class(
        "/SunPosition/BP_Sky_Sphere_SunSky.BP_Sky_Sphere_SunSky")   # verify path
    sun = actors.spawn_actor_from_class(sunsky_class,
                                        unreal.Vector(0.0, 0.0, 0.0))
    sun.set_actor_label("SunSky_Okongo")

    for prop, value in (
        ("Latitude",  latitude),
        ("Longitude", longitude),
        ("TimeZone",  time_zone),
        ("NorthOffset", 0.0),
        ("Month", month),
        ("Day", day),
        ("SolarTime", solar_time),
        ("UseDaylightSavingTime", False),   # Namibia does not observe DST
    ):
        try:
            sun.set_editor_property(prop, value)
        except Exception as exc:
            unreal.log_warning("SunSky property {} not set: {}".format(prop, exc))
    return sun
```

The Blueprint asset path for the SunSky Actor is **not** confirmed in the documentation fetched for this file. Discover it once in your install with:

```python
for p in unreal.EditorAssetLibrary.list_assets("/SunPosition", True, False):
    unreal.log(p)
```

and hard-code the result. This is flagged as **needs-verification** rather than guessed.

### Example — batch-enable Nanite on architectural meshes

```python
import unreal

def enable_nanite(root="/Game/_Imports", exclude_tokens=("glass", "glazing", "window_pane")):
    mesh_sub = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    EAL = unreal.EditorAssetLibrary
    changed = 0
    for path in EAL.list_assets(root, recursive=True, include_folder=False):
        asset = EAL.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        lowered = path.lower()
        if any(tok in lowered for tok in exclude_tokens):
            unreal.log("skip (translucent): " + path)
            continue
        settings = mesh_sub.get_nanite_settings(asset)
        if settings.enabled:
            continue
        settings.enabled = True
        mesh_sub.set_nanite_settings(asset, settings, apply_changes=True)
        EAL.save_asset(path, only_if_is_dirty=True)
        changed += 1
    unreal.log("Nanite enabled on {} meshes".format(changed))
```

Nanite supports Opaque and Masked blend modes only, so translucent glazing must be excluded — see file `03`.

## Asset import automation — `AssetImportTask`

`unreal.AssetImportTask` (module `UnrealEd`, `AssetImportTask.h`) carries the data for one import. Verified properties: `filename`, `destination_path`, `destination_name`, `factory`, `options`, `automated`, `replace_existing`, `replace_existing_settings`, `save`, `async_`; methods `get_objects()` and `is_async_import_complete()`.

```python
import unreal, os, glob

def import_fbx_folder(source_dir, dest_path="/Game/_Project/Meshes/Furniture"):
    tasks = []
    for fbx in glob.glob(os.path.join(source_dir, "*.fbx")):
        opts = unreal.FbxImportUI()
        opts.set_editor_property("import_mesh", True)
        opts.set_editor_property("import_textures", True)
        opts.set_editor_property("import_materials", True)
        opts.set_editor_property("import_as_skeletal", False)
        opts.static_mesh_import_data.set_editor_property("combine_meshes", True)
        opts.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", False)
        opts.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
        opts.static_mesh_import_data.set_editor_property(
            "normal_import_method",
            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)

        task = unreal.AssetImportTask()
        task.filename = fbx
        task.destination_path = dest_path
        task.automated = True          # no dialogs
        task.replace_existing = True
        task.save = True
        task.options = opts
        tasks.append(task)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for t in tasks:
        for obj in t.get_objects():
            unreal.log("imported: " + obj.get_path_name())
```

`generate_lightmap_u_vs=False` is deliberate — under Lumen you do not bake, and Epic advises disabling it when building Nanite meshes because it adds a UV channel and significant data on dense geometry.

## Datasmith from Python

Epic's documented API for taking control of the two-stage Datasmith import. Reproduced with corrected Python 3 syntax (the documentation example uses Python 2 `print` statements):

```python
import unreal

ds_file_on_disk = r"C:\scenes\okongo_house.udatasmith"
scene = unreal.DatasmithSceneElement.construct_datasmith_scene_from_file(ds_file_on_disk)
if scene is None:
    unreal.log_error("Scene loading failed.")
else:
    # --- filter the in-memory Datasmith Scene before it becomes assets ---
    remove_keyword = "site_context"
    meshes_to_skip = set()

    for mesh_actor in scene.get_all_mesh_actors():
        label = mesh_actor.get_label()
        if remove_keyword in label:
            unreal.log("removing actor: " + label)
            meshes_to_skip.add(mesh_actor.get_mesh_element())
            scene.remove_mesh_actor(mesh_actor)

    for mesh in meshes_to_skip:
        unreal.log("removing mesh: " + mesh.get_element_name())
        scene.remove_mesh(mesh)

    # --- import options ---
    import_options = scene.get_options(unreal.DatasmithImportOptions)
    import_options.base_options.scene_handling = unreal.DatasmithImportScene.NEW_LEVEL

    # --- finalise: destination MUST start with /Game/ ---
    result = scene.import_scene("/Game/_Imports/Okongo_Revit")
    if not result.import_succeed:
        unreal.log_error("Importing failed.")
    scene.destroy_scene()          # always release the in-memory scene
    unreal.log("Custom import process complete.")
```

Epic's own recommendation is worth heeding: **prefer post-import modification**. Filtering during import bypasses the reimport path, so filtered objects reappear as "new" on the next reimport. Modify the scene during import only to prevent asset creation you never want.

Datasmith carries source-application metadata into Unreal, which is the real automation lever. Read it and act on it after import.

## Batch material assignment

The single highest-value archviz automation: replace hundreds of flat Datasmith materials with your own instances, by name or by metadata.

```python
import unreal

def create_instance(parent_path, dest_folder, name, scalars=None, vectors=None, textures=None):
    """Create a MaterialInstanceConstant under dest_folder from parent_path."""
    parent = unreal.EditorAssetLibrary.load_asset(parent_path)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    factory.set_editor_property("initial_parent", parent)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi = tools.create_asset(name, dest_folder,
                            unreal.MaterialInstanceConstant, factory)
    MEL = unreal.MaterialEditingLibrary
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(mi, k, v)
    for k, v in (textures or {}).items():
        MEL.set_material_instance_texture_parameter_value(
            mi, k, unreal.EditorAssetLibrary.load_asset(v))
    unreal.EditorAssetLibrary.save_asset(mi.get_path_name())
    return mi


RULES = [
    ("brick",    "/Game/_Project/Materials/Instances/MI_Brick_Facebrick"),
    ("plaster",  "/Game/_Project/Materials/Instances/MI_Plaster_White"),
    ("screed",   "/Game/_Project/Materials/Instances/MI_Concrete_Screed"),
    ("timber",   "/Game/_Project/Materials/Instances/MI_Timber_Meranti"),
    ("ibr",      "/Game/_Project/Materials/Instances/MI_Metal_IBRSheet"),
]

def assign_by_name():
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    EAL = unreal.EditorAssetLibrary
    cache = {}
    hits = 0
    for actor in actors.get_all_level_actors():
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            if mesh is None:
                continue
            for slot, mat in enumerate(comp.get_materials()):
                current = (mat.get_name() if mat else "").lower()
                for token, mi_path in RULES:
                    if token in current:
                        if mi_path not in cache:
                            cache[mi_path] = EAL.load_asset(mi_path)
                        comp.set_material(slot, cache[mi_path])
                        hits += 1
                        break
    unreal.log("assigned {} material slots".format(hits))
```

The Datasmith-metadata variant is better where the source model is disciplined: read the Revit `Type Name` or IFC property, look it up in a CSV or Data Table, and assign. That is a specification-driven pipeline rather than a name-matching heuristic.

## Level generation from data

Placing a residential scheme from a schedule — plot positions, house types, orientations — is the case that repays automation most.

```python
import unreal, csv

def place_units(csv_path, blueprint_folder="/Game/_Project/Blueprints/HouseTypes"):
    """CSV columns: plot_id, type, x_m, y_m, z_m, yaw_deg"""
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    EAL = unreal.EditorAssetLibrary
    classes = {}
    placed = 0

    with unreal.ScopedSlowTask(sum(1 for _ in open(csv_path)) - 1,
                               "Placing units") as task:
        task.make_dialog(True)
        with open(csv_path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if task.should_cancel():
                    break
                task.enter_progress_frame(1, "Plot " + row["plot_id"])

                type_name = row["type"]
                if type_name not in classes:
                    path = "{}/BP_{}.BP_{}".format(blueprint_folder, type_name, type_name)
                    classes[type_name] = EAL.load_blueprint_class(path)
                if classes[type_name] is None:
                    unreal.log_warning("missing house type: " + type_name)
                    continue

                loc = unreal.Vector(float(row["x_m"]) * 100.0,   # metres -> uu
                                    float(row["y_m"]) * 100.0,
                                    float(row["z_m"]) * 100.0)
                rot = unreal.Rotator(0.0, 0.0, float(row["yaw_deg"]))
                actor = actors.spawn_actor_from_class(classes[type_name], loc, rot)
                actor.set_actor_label("Plot_{}_{}".format(row["plot_id"], type_name))
                actor.tags = [unreal.Name("Plot"), unreal.Name(type_name)]
                placed += 1

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log("placed {} units".format(placed))
```

Note the `unreal.ScopedSlowTask` context manager — it gives a cancellable progress dialog and keeps the editor responsive. Use it for anything touching more than a few dozen assets.

For very large repeated scatter (boundary walls, paving units, plant stock), spawn a single Actor holding a `HierarchicalInstancedStaticMeshComponent` and call `add_instance(transform)` in a loop instead of spawning thousands of Actors. See file `08`.

## Undo, transactions and performance

```python
with unreal.ScopedEditorTransaction("Assign archviz materials") as trans:
    ...   # everything here becomes one undoable entry
```

Other practicalities: turn off viewport realtime during a long batch (`LevelEditorSubsystem.editor_set_viewport_realtime(False)`); batch saves at the end rather than per asset; and remember that `EditorAssetLibrary` loads assets before operating on them, so a pass over 10 000 assets loads 10 000 assets into memory.

## Editor Utility Widgets as the front end

Create with right-click in the Content Browser → *Editor Utilities > Editor Utility Widget*. Run with right-click → **Run Editor Utility Widget**; it then appears in the Level Editor's **Tools** dropdown under *Editor Utility Widgets*, and docks with Level Editor tabs.

The `Execute Python Script` node is Epic's **recommended** way to call Python from Blueprint, and it supersedes creating a `BlueprintFunctionLibrary` type in Python (which caused save/load problems because Python-generated types are transient and is no longer officially supported). It:

- executes literal Python code typed into the node (Shift+Return for new lines)
- supports **custom input and output pins**, exposed as variables inside the script — inputs are set before the script runs, outputs are read after
- returns a `Success?` boolean; errors go to the Output Log
- **cannot run files** — only literal code. Use it to `import` your module and call one function:

```
import my_tools
my_tools.assign_by_name()
```

`Execute Python Command` and `Execute Python Command (Advanced)` can run files. The Advanced node adds *Execution Mode* (Execute File / Execute Script / **Evaluate Script**, which returns a value in `Command Result`), *File Execution Scope* (Public — shares the global scope; Private — sandboxed), a `Log Output` array of every message the script wrote, and richer error reporting.

Python execution nodes are available **only in editor-only Blueprint classes**. They do not exist in an Actor-derived Blueprint.

Driving a widget from Python:

```python
util = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
bp = unreal.EditorAssetLibrary.load_asset("/Game/_Project/Tools/EUW_ArchvizTools")
tab_id = util.register_tab_and_get_id(bp)
util.spawn_and_register_tab(bp)          # verify exact method name in your build
```

`EditorUtilitySubsystem` also offers `can_run(asset)`, `find_utility_widget_from_blueprint(bp)`, `get_tab_id_from_blueprint(bp)`, `does_tab_exist(tab_id)`, `close_tab_by_id(tab_id)` and `register_and_execute_task(task, parent=None)`.

`unreal.EditorUtilityLibrary.get_selected_assets()`, `.get_selected_asset_data()`, `.get_selected_assets_of_class(cls)`, `.get_selection_set()` (selected Actors) and `.get_selected_folder_paths()` are how a widget knows what the user picked.

## Rendering from Python

```python
import unreal

def queue_and_render(sequence_path, map_path, config_path):
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    queue = subsystem.get_queue()
    queue.delete_all_jobs()

    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.job_name = "Okongo_Exterior"
    job.map = unreal.SoftObjectPath(map_path)
    job.sequence = unreal.SoftObjectPath(sequence_path)
    job.set_configuration(unreal.EditorAssetLibrary.load_asset(config_path))

    subsystem.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
```

For a farm or for CI, drive it from the command line instead (file `04`), or subclass `MoviePipelinePythonHostExecutor` and pass it with `-MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor -ExecutorPythonClass=...`. Epic's architectural note bears repeating: **the smallest distributable unit of render work is one camera cut**, not one frame.

## The Remote Control API

A web server inside the engine serving WebSocket messages and HTTP requests through a REST-like API. It offers roughly the same level of control over the editor and project content as Blueprint and Python: your client can call any function exposed to Blueprint or Python, and read or write any exposed property or Remote Control Preset field.

**Setup:** `Edit > Plugins` → Messaging → **Remote Control API** (Beta) → enable → restart. Then in the Output Log's Cmd bar:

| Command | Effect |
|---|---|
| `WebControl.StartServer` | Start the web server, listening on **port 30010** |
| `WebControl.StopServer` | Stop it |
| `WebControl.EnableServerOnStartup` | Start automatically whenever the project opens (editor, PIE or `-game`) |

Change the port at `Project Settings > Web Remote Control > Remote Control HTTP Server Port`, and the WebSocket port at `Project Settings > Plugins > Remote Control > Remote Control WebSocket Server Port` (default **30020**).

**Key HTTP endpoints:**

| Route | Verb | Purpose |
|---|---|---|
| `/remote/info` | GET | Lists every available route with descriptions |
| `/remote` | OPTIONS | Allows cross-origin requests |
| `/remote/batch` | PUT | Batch several calls into one request |
| `/remote/object/call` | PUT | Call a Blueprint-callable function on a `UObject` |
| `/remote/object/property` | PUT | Read or write a property |

Calling a function:

```json
{
  "objectPath": "/Game/Maps/L_Main.L_Main:PersistentLevel.SunSky_Okongo",
  "functionName": "SetActorLocation",
  "parameters": { "NewLocation": {"X": 100, "Y": 0, "Z": 30}, "bSweep": true },
  "generateTransaction": true
}
```

Notes that matter: if the function is defined in C++, use the **C++ names** for the function and its parameters, not the Blueprint display names (Epic's own example: `bSweep`, not `Sweep`). Omitted parameters get default-constructed objects. `generateTransaction: true` makes the change undoable (it appears in Undo History as *Remote Call Transaction Wrap*) and replicates it in a Multi-User Editing session.

Reading a property over WebSocket (`ws://127.0.0.1:30020`):

```json
{
  "MessageName": "http",
  "Parameters": {
    "Url": "/remote/object/property",
    "Verb": "PUT",
    "Body": {
      "ObjectPath": "/Game/Maps/L_Main.L_Main:PersistentLevel.StaticMeshActor_1.StaticMeshComponent0",
      "propertyName": "StreamingDistanceMultiplier",
      "access": "READ_ACCESS"
    }
  }
}
```

WebSocket message types are `HTTP`, `Preset.Register` and `Preset.Unregister`. Registering to a **Remote Control Preset** subscribes you to `PresetFieldsChanged`, `PresetFieldsAdded`, `PresetFieldsRemoved` and `PresetFieldsRenamed` events — the mechanism for keeping an external UI in sync with the editor. Presets (`RCP_`) let you expose a curated set of properties and functions without writing code.

Some routes are gated behind an experimental flag; add to `DefaultEngine.ini`:

```ini
[Console Variables]
WebControl.EnableExperimentalRoutes = 1
```

In packaged projects and `-game`, Remote Control is disabled by default (a virtual-production accommodation). Enable with command-line flags:

```
-RCWebControlEnable -RCWebInterfaceEnable
```

## Unreal MCP — the official 5.8 plugin

UE 5.8 embeds an MCP server **inside the editor process** so any MCP-compatible agent — Claude Code, Cursor, the MCP Inspector — can drive the editor over a local HTTP connection. The plugin identifier throughout the source tree, `.uplugin` files, C++ symbols and console commands is `ModelContextProtocol`; the friendly name in the Plugin Browser is **Unreal MCP**.

### Setup

1. `Edit > Plugins` → enable **Unreal MCP** *and* **All Toolsets**. Both depend on **Toolset Registry**, which enables automatically. Restart.
2. `Edit > Editor Preferences > General > Model Context Protocol` → enable **Auto Start Server**. The server binds to `http://127.0.0.1:8000/mcp`. The same panel exposes *Server Port Number* (8000) and *Server URL Path* (`/mcp`). The `serverInfo.name` advertised is always `unreal-mcp`.
   To start on demand instead, leave auto-start off and run `ModelContextProtocol.StartServer` (optionally `ModelContextProtocol.StartServer 8000`) in the editor console.
3. Generate a client config from the editor console:

```
ModelContextProtocol.GenerateClientConfig ClaudeCode
```

   This writes `.mcp.json` to the project root:

```json
{
  "mcpServers": {
    "unreal-mcp": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

   Supported client names: `ClaudeCode`, `Cursor`, `VSCode`, `Gemini`, `Codex`, `All`. JSON configs (Claude Code, Cursor, VS Code, Gemini) are **merged** with existing entries, so re-running is safe; the Codex TOML config is write-once and refuses to overwrite.

4. **Launch the agent CLI from the project root** where `.mcp.json` was written. If the agent does not find the server, that is almost always why. Start the editor first, then the agent.

Optionally, the **Terminal** plugin embeds a terminal panel inside the editor with startup commands, keeping the whole loop in one window. Epic's recipe, in order: set `TERM` (`set TERM=xterm-256color` on Windows `cmd.exe`, `export TERM=xterm-256color` on bash/zsh — without this, `claude` and similar CLIs emit raw escape sequences), then `cd` to the directory holding `.mcp.json` (the Terminal panel starts in `FPaths::RootDir()`, which is the *engine installation directory* in installed builds, not the project root), then launch `claude`.

### What it exposes

Tools come from the **Toolset Registry**, a subsystem in a sibling plugin. A **Toolset** is a class deriving from `UToolsetDefinition` (C++) or `unreal.ToolsetDefinition` (Python) exposing functions marked as Tool calls. The registry collects them at startup and Unreal MCP wraps each as an MCP Tool. Shipped toolsets include `SceneTools`, `ActorTools`, `MaterialInstanceTools` and `ObjectTools` — **most of which are authored in Python**, under `Engine/Plugins/Experimental/ToolsetRegistry/Content/Python/toolset_registry/toolsets/core/`.

Documented capabilities include spawning actors, configuring lighting, creating material instances, inspecting Slate widgets and running automation tests.

By default the plugin runs in **tool-search mode** (`Enable Tool Search`, default true). `tools/list` then returns three discovery meta-tools rather than every schema:

| Meta-tool | Purpose |
|---|---|
| `list_toolsets` | Available toolset names and descriptions |
| `describe_toolset` | Schemas for a named toolset |
| `call_tool` | Dispatch a named toolset's Tool and return the result on the same turn |

This keeps the initial payload small even with hundreds of tools. Setting it false advertises everything eagerly. **Tool authors must not assume eager advertisement** — tool search is what a connecting agent sees by default.

### Authoring your own tools in Python

The documented conventions, and a toolset written to them:

```python
import unreal
import toolset_registry


@unreal.uclass()
class ArchvizTools(unreal.ToolsetDefinition):
    """Tools for a residential architectural visualisation project:
    sun positioning, finish assignment and camera placement."""

    @toolset_registry.tool_call
    @staticmethod
    def set_sun_time(solar_time: float) -> bool:
        """Set the time of day on the level's SunSky Actor.

        Args:
            solar_time: Time of day as a float in military time (12.5 == 12:30).

        Returns:
            True if a SunSky Actor was found and updated.
        """
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in actors.get_all_level_actors():
            if "SunSky" in actor.get_actor_label():
                actor.set_editor_property("SolarTime", solar_time)
                return True
        return False

    @toolset_registry.tool_call
    @staticmethod
    def list_material_slots(actor_label: str) -> list[str]:
        """List the material slot names on a named Actor's static meshes.

        Args:
            actor_label: The Actor label as shown in the World Outliner.

        Returns:
            A list of "component.slot: material" strings.
        """
        out = []
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        for actor in actors.get_all_level_actors():
            if actor.get_actor_label() != actor_label:
                continue
            for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
                for i, mat in enumerate(comp.get_materials()):
                    out.append("{}.{}: {}".format(
                        comp.get_name(), i, mat.get_name() if mat else "None"))
        return out
```

The rules Epic documents:

- `@unreal.uclass()` exposes the class to reflection; it must inherit `unreal.ToolsetDefinition`.
- The **class docstring** becomes the toolset's grouping description.
- Every Tool function carries `@toolset_registry.tool_call` **and** is declared `@staticmethod`. Functions without the decorator are not advertised.
- **Parameter and return type hints** (`unreal.Actor`, `str`, `bool`, `list[str]`, dataclasses) drive the JSON Schema the Tool advertises.
- The function docstring uses **Google style** with `Args:` and `Returns:` blocks; the text and per-argument descriptions are reflected into the schema. Write them with the care you would give a public API.
- To exclude a function inside a toolset, simply omit `@toolset_registry.tool_call` (Python) or add `meta = (AIIgnore)` (C++).
- Keep Tools small and single-purpose; **prefer structured return types to free-form strings**, because structured types serialise to schema with field-level types and descriptions.

Python toolsets live as `.py` modules under any plugin's `Content/Python/` directory and are discovered at startup. Run `ModelContextProtocol.RefreshTools` after authoring or hot-reloading. Claude Code users can scaffold one with the `create-toolset` skill from the `unreal-mcp` Claude Code plugin.

C++ toolsets derive from `UToolsetDefinition`, are marked `UCLASS(BlueprintType, Hidden)`, and expose static `UFUNCTION(meta = (AICallable))` methods; doc comments reflect into the schema the same way. Reach for C++ when a Tool needs engine functionality not exposed to Python, uses `USTRUCT` types not expressible via Python hints, or is hot enough that the Python-to-engine boundary cost matters. **Live Coding does not propagate new `UFUNCTION` declarations — adding a C++ Tool requires an editor restart.**

For tools whose schemas are determined at runtime, implement `IModelContextProtocolTool` and register directly:

```cpp
TSharedRef<IModelContextProtocolTool> Tool = MakeShared<FMyDynamicTool>();
IModelContextProtocolModule::GetChecked().AddTool(Tool);
```

The caller is then responsible for deregistration. Interface methods are invoked on the game thread, like registry-discovered Tools.

### Configuration reference

| Editor Preference | Default | Meaning |
|---|---|---|
| Auto Start Server | `false` | Start on editor startup |
| Server Port Number | `8000` | Bound on `127.0.0.1` |
| Server URL Path | `/mcp` | |
| Enable Tool Search | `true` | Meta-tools instead of full schemas |

| Console variable | Type | Default |
|---|---|---|
| `ModelContextProtocol.WrapPODToolResultsInObject` | bool | `true` |
| `ModelContextProtocol.AudioResultOggFormat` | bool | `false` |
| `ModelContextProtocol.ProgressIntervalSeconds` | float | `1.0` |
| `ModelContextProtocol.PaginationPageSize` | int32 | `0` (disabled) |
| `ModelContextProtocol.EnableAnalytics` | bool | `true` |

Command-line flags: `-ModelContextProtocolStartServer` (starts during editor or commandlet startup regardless of the preference) and `-ModelContextProtocolPort=N`.

### Limitations

- **HTTP and Server-Sent Events only.** `stdio` and WebSocket transports are not supported.
- **Loopback only.** Binds per `[HTTPServer.Listeners] DefaultBindAddress` (default `localhost`) and rejects non-loopback `Origin` headers. **No authentication layer.**
- MCP **Resources and Prompts are not advertised** by any shipping toolset — Tools only.
- The Toolset Registry adapter is **editor-only**. Cooked builds can host a server via `IModelContextProtocolModule::StartServer()` but must register Tools explicitly with `AddTool()`.
- Tool invocations are executed **on the game thread, serially** — clients must not issue overlapping Tool calls.

### Debugging

- The server logs its bind address, port and URL path to the Output Log at editor initialisation. A bind failure (port in use, missing dependency) surfaces there first.
- Raise verbosity with `Log LogModelContextProtocol Verbose`.
- Use the official MCP Inspector — `npx @modelcontextprotocol/inspector` — pointed at `http://127.0.0.1:8000/mcp` over Streamable HTTP. It lists every advertised Tool with its declared schema and gives a form-style invocation surface that bypasses the agent's interpretation entirely. This is the fastest way to tell "my tool is broken" from "the model called it wrong".
- After Live Coding a toolset method, run `RefreshTools` **and reconnect the client** — it may still hold the old schema.

## Community MCP servers

Before Epic shipped the official plugin, several community projects filled the gap and remain useful — particularly on 5.5–5.7 where the official plugin does not exist. The common architecture: a C++ or Blueprint plugin runs a **TCP socket server inside the editor**; a Python MCP server (usually FastMCP) accepts MCP calls from the agent, serialises them to JSON over that socket, and parses responses. For example, `chongdashu/unreal-mcp` (MIT, UE 5.5+) uses a C++ plugin listening on TCP **55557** with a FastMCP Python front end, exposing actor management, Blueprint creation, Blueprint node graph editing and editor viewport control. Treat all of them as experimental.

**Recommendation for this user:** on UE 5.8 use Epic's official `ModelContextProtocol` plugin as the primary control plane, keep the **Remote Control API** available for property-level control and for driving a packaged build, and keep a `Content/Python` module of project-specific functions that both the MCP toolsets and an Editor Utility Widget can call. That gives three layers — agent, network, and direct script — over one shared body of Python.

## Open questions

- The exact asset path of the SunSky Blueprint under `/SunPosition/` — **needs verification** by listing that folder in your install.
- `EditorUtilitySubsystem.spawn_and_register_tab` was written from the documented pattern rather than read from the API page — **needs verification**.
- `unreal.MoviePipelinePIEExecutor` as the executor class name for in-editor rendering was not confirmed on the pages fetched — **needs verification** against your build's `MoviePipelineQueueSubsystem` / executor classes.
- UE 5.8's official MCP plugin is Experimental; API and data formats may change without notice.

## Sources

- [Scripting the Unreal Editor Using Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python) — Epic Games, accessed 2026-08-25
- [Scripting and Automating the Unreal Editor](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-and-automating-the-unreal-editor) — Epic Games, accessed 2026-08-25
- [unreal.EditorAssetLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary.html) — Epic Games, accessed 2026-08-25
- [unreal.EditorActorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem.html) — Epic Games, accessed 2026-08-25
- [unreal.LevelEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/LevelEditorSubsystem.html) — Epic Games, accessed 2026-08-25
- [unreal.AssetImportTask](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetImportTask.html) — Epic Games, accessed 2026-08-25
- [unreal.AssetTools](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetTools.html) — Epic Games, accessed 2026-08-25
- [unreal.AssetToolsHelpers](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetToolsHelpers.html) — Epic Games, accessed 2026-08-25
- [unreal.MaterialEditingLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MaterialEditingLibrary.html) — Epic Games, accessed 2026-08-25
- [unreal.StaticMeshEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshEditorSubsystem.html) — Epic Games, accessed 2026-08-25
- [unreal.EditorUtilitySubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorUtilitySubsystem.html) — Epic Games, accessed 2026-08-25
- [unreal.EditorUtilityLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorUtilityLibrary.html) — Epic Games, accessed 2026-08-25
- [unreal.MoviePipelineQueueSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MoviePipelineQueueSubsystem.html) — Epic Games, accessed 2026-08-25
- [unreal.MoviePipelineQueue](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MoviePipelineQueue.html) — Epic Games, accessed 2026-08-25
- [Customizing the Datasmith Import Process](https://dev.epicgames.com/documentation/en-us/unreal-engine/customizing-the-datasmith-import-process-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Editor Utility Widgets](https://dev.epicgames.com/documentation/en-us/unreal-engine/editor-utility-widgets-in-unreal-engine) — Epic Games, accessed 2026-08-25
- [Remote Control](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Remote Control Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-quick-start-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Remote Control API HTTP Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Remote Control API WebSocket Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-websocket-reference-for-unreal-engine) — Epic Games, accessed 2026-08-25
- [Unreal MCP](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor) — Epic Games, accessed 2026-08-25
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) — community MCP server, accessed 2026-08-25
- [Using Command Line Rendering with Movie Render Queue](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-command-line-rendering-with-move-render-queue-in-unreal-engine) — Epic Games, accessed 2026-08-25
