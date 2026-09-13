# Completing lane work with local models and ChatGPT

Use the same small loop with either model: retrieve one relevant operation card, draft a batch, check its syntax, execute it, and measure the result. TEE supplies the application-specific operations and checks; the model supplies the user's intent and judges whether the evidence meets it. A fluent explanation or a successful tool call does not establish design quality.

The guides are deterministic and call no language model. They are available to any client connected to this TEE server, including a local model host with MCP tool execution or a ChatGPT/Codex task where TEE tools are connected. A local completion endpoint by itself is not an MCP agent. TEE's local triage, extraction and repair chores are separate from the model driving a whole task.

## Start with one operation card

Call `tee_recall` for project facts and `tee_status` for served lanes and connection state. Reuse scene stamps and known IDs. Read only the entities the current step needs with a filtered `tee_scene_summary`; fetch individual details rather than dumping a scene.

The guidance tools live behind the existing progressive surface. These are argument objects for `tee_call`:

```json
{"name":"lane_guide","args":{"adapter":"fusion"}}
```

The first response is a compact topic index. Request one topic next:

```json
{"name":"lane_guide","args":{"adapter":"fusion","topic":"sketch_extrude"}}
```

| Lane | Current detailed topics | Units to preserve |
| --- | --- | --- |
| Blender | `create`, `material`, `camera`, `render` | Geometry in metres; `rotation_euler` in radians; camera `lens` in millimetres; +Z up |
| Autodesk Fusion | `sketch_extrude`, `hole_fillet`, `parameters`, `export` | Length in millimetres; angle in degrees; volume in mm³; TEE converts Fusion's internal centimetres |

Other adapters return their declared vocabulary when they have no detailed guide. Discover their specific tools with `tee_search_tools`, then read the chosen schema with `tee_describe_tool`. A live API index documents the application API; it does not imply that every API call is available as a typed TEE operation.

For a small model, send the current user constraints, one guide card, relevant entity IDs and expected checks. Keep unrelated lane documentation and old tool outputs out of the prompt. A reusable instruction is:

> Draft the next small batch for the stated lane using only the supplied contract. Preserve every requested dimension, material and output requirement. Use returned IDs or documented same-batch aliases. Do not invent unsupported properties or treat a name as an ID. Include the measurements that will determine success. The draft has not been executed or validated. If the contract cannot express a requirement, identify that requirement explicitly.

## Draft, preflight, then execute

For example, a Fusion batch can construct a plate without guessing which sketch ID will be created:

```json
[
  {"op":"create","kind":"sketch","name":"Plate profile","as":"profile",
   "props":{"plane":"XY","rects":[[0,0,120,80]]}},
  {"op":"create","kind":"extrude","name":"Plate","as":"plate",
   "props":{"sketch":"@profile","distance":10,"operation":"new_body"}}
]
```

Pass that list unchanged as `ops` to `tee_call`:

```json
{"name":"lane_preflight","args":{"adapter":"fusion","ops":[...]}}
```

Here `[...]` means substitute the actual operation list, not a literal JSON ellipsis. A successful preflight reports `live_state_checked:false`. It checks adapter syntax when supported, or only the outer shape for older adapters. It does not prove that IDs exist, features fit the live geometry, permissions allow a write, or the result meets the user's brief.

Apply the same operations using `tee_batch(adapter="fusion", ops=...)`. The kernel also runs available preflight before connection warming and checkpointing. This avoids saving and restoring an application merely to discover a malformed property. For further operations, retain the returned IDs and `(epoch, revision)` stamps. Query a diff after changes rather than repeatedly reading the whole document.

Fusion aliases are local to one batch. `as:"profile"` binds the actual newly created sketch; `@profile` can be used only in later operations of that batch. An extrusion alias binds its single body as `@plate` and the feature as `@plate.feature`. Multi-body alias results are refused as ambiguous. Sketch addresses such as `@profile/r0.bl` work for dimensions and constraints. In the next batch, use the actual returned IDs. Blender currently uses returned IDs and has no equivalent batch aliases.

## Make parameters and appearances real

A Fusion user parameter does not drive geometry just because it exists. Bind it to the relevant sketch dimension or feature expression. After creating a parameter named `plate_thickness` and the aliased plate above, this operation connects the extrusion distance to that parameter:

```json
{"op":"set","id":"@plate.feature","props":{"expression":"plate_thickness"}}
```

A later update has top-level `name` and `expression`:

```json
{"op":"param_set","name":"plate_thickness","expression":"12 mm"}
```

Read the parameter and measure the resulting body's thickness after the change. `fu_measure(of=<new body id>)` reads Fusion's actual geometry; a whole-design measurement includes pre-existing bodies. An explicitly named extrusion names its single newly created body; changing a feature name or cutting an existing body need not rename that existing body.

Blender geometry and materials use separate typed operations. Assign a material with `assign_material`, supplying the actual mesh ID and material properties in `props`. The `material` guide supplies both that batch form and a `tee_script` that captures a newly created ID before assigning its material. Check the material assignment in entity detail, then inspect a rendered view for appearance.

A camera accepts `lens`, `target` and `active`. `target` is a world-space point in metres and sets its orientation once; it is not a tracking constraint. The camera must be unparented for this operation. Use either `target` or `rotation_euler`. Check `lens_mm`, `active` and orientation in the returned camera detail, then verify framing in the image. Unsupported properties fail instead of silently becoming a successful no-op.

## Verify the requested output

Run deterministic checks before visual review, but retain visual review when the brief concerns quality or realism.

| Requirement | Evidence to collect |
| --- | --- |
| Dimensions and fit | Measured bounding box, relevant distances and clearances, using explicit units and the intended entity IDs |
| Native CAD | Solid-body count and validity, feature/parameter history, parameter changes that recompute the intended geometry |
| Material and camera | Actual assignments and focal length/active camera, followed by an inspected render |
| Export | Returned path, bytes and units; reopen or independently measure the exported artifact and compare against the source |
| PDF/video | Open the actual output, inspect representative pages/frames, check dimensions, captions and required content |
| Engineering claim | A suitable solved and verified analysis; preserve insufficient, unresolved and unvalidated verdicts |

`bl_render` is asynchronous: it returns a job ID. Poll `tee_job` and inspect the final file after `state=done`. Use an absolute output path with an existing parent directory. A completed rendering job proves that an image was written, not that it is well framed or photorealistic. Camera changes for several views should reuse the existing camera and known object IDs.

`fu_export` supports the formats documented in its schema. STEP/F3D exports take a component or the whole design, not a body. OBJ is centimetres; STL follows the design's length unit; use the returned units rather than assuming. `fu_drawing` routes through partkiln because the Fusion API does not create drawing documents. Typed Fusion still does not provide general loft/freeform surfacing or visual mesh import. Report such gaps instead of claiming an empty component is the requested geometry.

## Keep retries useful and model selection honest

On a syntax refusal, change only the fields identified by the error and preflight again. When the Python escape hatch is authorized, stale-API errors name bounded source-line locations and the total number of occurrences. Correct every occurrence; prefer a small, checked patch over repeatedly regenerating the whole program. The API check precedes the scene checkpoint, although discovering the connected version may require a read-only probe. Do not remove a user's required feature merely to obtain a green result. A refusal about unknown live IDs needs a refreshed scoped query; a trust denial needs its stated authorized route, not another engine or an escape hatch. A returned repair draft is a proposal, not an executed or validated repair.

Use `tee_script` for bounded sequences whose intermediate results need no further judgment. It provides `batch`, `call`, `detail`, `summary` and `diff` helpers; it is a restricted Python subset, not arbitrary application Python. Do not convert an uncertain modeling decision into an unattended retry loop.

For local Qwen, inspect `eng_scan`/`eng_reconcile` and confirm the exact endpoint/model produces nonempty output with `eng_ask`. A profile name, `/v1/models` listing or HTTP 200 is not sufficient evidence. A78 measured an installed `Qwen3.8-27B-8bit` route while an older configured q27b model name was stale; those are session observations, not permanent defaults. Preserve the user's chosen profile and paid-model ceiling. Measuring a local candidate must explicitly target its known local endpoint; it must not silently use an active paid profile.

The same cards and checks help ChatGPT without requiring it to load every application's documentation. More capable models can handle the unresolved design decisions while bounded, verified work is assigned to a capable local model. Record actual completions, failures, latency and token usage separately; a failed task with fewer tokens is not an efficiency gain.

The AETHER car remains a demanding reference artifact, not a shortcut benchmark. Passing a primitive or small CAD task does not demonstrate equal cockpit detail, surface quality, documentation, video or aerodynamic analysis. Compare new work on a frozen brief with independent measurements and image inspection; do not score replay of the completed AETHER scripts as independent local-model creation.
