# archkiln: architectural models, cabinetry and reference conversion

archkiln adds an original headless architectural model to TEE. The same model
drives its tools, optional local workbench, IFC and mesh exchange, drawings and
cabinet schedules. Blender, Unreal and a desktop BIM application are optional
clients or sources; ordinary architectural authoring does not start them.

The initial authoring vocabulary is storeys, straight walls, hosted doors and
windows, room polygons, slabs, explicitly flat roofs and rectangular cabinet
assemblies. Dimensions are millimetres. Every document has its own identity,
stable entity IDs and monotonic revisions. Atomic batches reject invalid host
references or openings that do not fit. Undo uses the same model and persistence
as ordinary edits.

## Start a model

Discover the `architecture`/`archkiln` tools through TEE's progressive tool
registry. They add no always-loaded tool schemas.

```json
{"name":"Compact house","preset":"compact-house"}
```

Pass this to `ak_create`. Retain the returned `model_id` and current revision.
The example includes two rooms, external walls and a partition, hosted openings,
a floor slab, a flat roof and a base cabinet. Its sizes are explicit example
parameters; it is not a pre-approved building or a manufacturer design.

| Tool | Purpose |
|---|---|
| `ak_status` | List model summaries and headless/workbench readiness. |
| `ak_create` | Create an empty model or the compact-house example. |
| `ak_query` | List entity IDs or inspect one entity; request cabinet schedules/nesting. |
| `ak_edit` | Apply a validated atomic create/update/delete/project batch. |
| `ak_undo` | Undo the latest transaction, advancing the revision. |
| `ak_import` | Inspect a contained source and propose measured candidates as a job. |
| `ak_candidates` | Inspect source identity, candidate geometry and uncertainty. |
| `ak_promote` | Turn one reviewed candidate into an authored wall. |
| `ak_export` | Generate revision-bound deliverables as a job. |
| `ak_check` | Check the model and supplied jurisdiction rule packs. |
| `ak_open` | Prepare or explicitly start the optional local workbench. |

`ak_edit` takes `operations`. For example, after querying the model's current
revision, change one wall thickness:

```json
{
  "model_id":"<returned model_id>",
  "expected_revision":1,
  "operations":[{"op":"update","id":"south","changes":{"thickness":240}}]
}
```

Use the actual current revision rather than copying `1` blindly. Concurrent
clients share file locks and atomic persistence; an expected-revision mismatch
refuses a stale edit. Project files live under `.tee/architecture/<model_id>/`.
Exports are separate, revision-bound artifacts under `output/archkiln/`.

## Cabinet design and deliverables

Cabinets have explicit width, depth, height, panel/back thickness, shelf/door
counts, plinth, material, grain and edge-band dimensions. A cabinet with doors
requires `properties.door_gap_mm`; the sample's 2 mm gap is a declared design
parameter. Query `detail:"cabinet"` for the panel/cut schedule. Optional `stock`
requires `sheet_width`, `sheet_height` and `kerf`; rotation is explicit.

The cabinet lane produces original panel geometry and a sheet layout with
declared kerf and grain constraints. Hardware and machining requirements remain
separate decisions. Generic cutlists do not establish joinery strength, a
manufacturer drilling pattern, CNC postprocessor compatibility or production
approval.

`ak_export` accepts `all`, `ifc`, `drawings`, `glb` or `json`. Poll its returned
job through `tee_job`. A successful result names the output directory and the
evidence/artifacts that were actually produced. Semantic IFC carries storeys,
walls, hosted openings/fillings, spaces, slabs, roofs and cabinets. Drawings and
schedules derive from the same revision; GLB supplies geometry for downstream
viewers. IFC validation and drawing checks are distinct from regulatory review.

Import/export job cancellation is cooperative: a native reader or export stage
already running finishes its bounded step. Cancellation is checked before an
import is published and between export stages/before the final success manifest.
Partial owned export files may remain for inspection; cancellation does not turn
them into an accepted export or modify the authored model.

The initial building vocabulary and drawing set are deliberately explicit about
their scope. Curved or sloped walls, pitched roof systems, a complete MEP/structure
authoring system, detailed specifications and jurisdiction-complete construction
documents are not established by these initial primitives.

## Convert meshes, scans and Unreal references

Place an owned source file inside the connected project. `ak_import` requires its
project-relative path, explicit units (`mm`, `cm`, `m`, `in`, `ft`) and
`tolerance_mm`. OBJ/STL/GLB meshes and XYZ/LAS/LAZ point clouds are supported.
The optional 4x4 affine transform applies after conversion to millimetres; its
translation is in millimetres and its result must use the project's Z-up frame.
Source files are read without modification. Symlinks, hard links and paths
outside the project are refused at the TEE boundary.

The import job retains hashes, sampled bounds, precision information and measured
plane/wall proposals. `ak_candidates` shows residuals, sampled support and
uncertainty. A sparse or occluded surface does not reveal concealed thickness,
structural role, fire rating or legal use. Unsupported geometry stays a reference.
The workflow does not silently turn every mesh into a semantic building.

To promote a wall candidate, use `ak_promote` with its candidate/import IDs,
destination storey, expected revision, and explicit overrides:

```json
{"height":2800,"thickness":200,"centreline_offset_mm":-100,"name":"Reviewed wall"}
```

The offset is signed along the candidate's reported plane normal. A scan usually
measures a face, while the authored wall uses a centreline; review this offset
instead of assuming those are the same. Promotion rechecks the source and all
referenced mesh identities before creating the wall.

Unreal interchange uses a documented actor/component/instance manifest with
relative mesh paths and explicit transforms. The optional selected-static-mesh
Editor export helper requires measured basis controls and explicit mesh-to-Unreal
and Unreal-to-project frames. It has source-reviewed API contracts and a stub
regression; an actual live Unreal exporter calibration/acceptance remains pending.
See the [reference and rule-pack contract](../server/src/tee/architecture/data/README.md)
for formats, limits, primary API sources and the helper's exact requirements.

## Worldwide rules and the meaning of a check

Set `project.jurisdiction` with an explicit country code, region and municipality;
there is no default country. `ak_check` accepts project-relative `pack_paths` and
an optional ISO `assessment_date`. The selection engine supports worldwide
jurisdiction hierarchies, editions, effective dates, authority-dependent
applicability, exact parent dependencies and reviewed amendments.

No verified worldwide legislation corpus ships with this implementation. Real
packs require source-document hashes, primary URLs, clauses, adoption instruments
and named/date-stamped interpretation reviews. Synthetic examples exist only to
exercise the engine. The evaluator validates supplied provenance records; it
does not authenticate or purchase the underlying legal sources.

Individual checks return `pass`, `fail`, `not_applicable` or `not_verified`.
Missing facts, location, reviewed sources, implemented rule support or amendment
precedence stay unknown. Even when every supplied rule passes, complete applicable
law coverage remains `not_verified`. IFC schema/EXPRESS, IDS information,
geometric checks and building approval are separate results. Learning can improve
modelling and conversion methods; it cannot edit versioned legal thresholds.

The [pack contract and schema](../server/src/tee/architecture/data/README.md)
document how reviewed jurisdiction modules can be added without guessing laws.

## Optional workbench

`ak_open` prepares the GUI information; `ak_open {"launch":true}` starts the
local workbench and returns its full session URL. Open that URL to edit models,
review candidates, inspect cabinetry and request exports/checks using the same
service as the headless tools. The workbench uses no remote assets or alternate
authoring model. It binds to loopback, requires the session token and checks
current project authority before operations. Keep the full session URL private.

Source implementation and tests are not an installation receipt. Extension
delivery follows the shared [upgrade coordination protocol](upgrade-coordination-protocol.md),
and completion on both clients still requires receipts from those actual clients.

## Supported wall junction policy

The compact-house example explicitly selects
`project.facts.wall_join_policy="orthogonal_butt_v1"`. Equal-base/top orthogonal
L/T junctions have deterministic through/abutting walls and shared derived
extents in IFC, preview and drawings; authored centrelines/opening offsets stay
unchanged. Unsupported, consumed or opening-conflicting junctions refuse before
an edit commits. Without a policy, unjoined geometry and overlaps are reported
explicitly. `ak_check` distinguishes these named checks from overall geometric
and legal coverage, which remain incomplete.

Plan sheets include room names and measured polygon areas, explicit opening
width/height/sill and cabinet dimensions. Labels use the same measured placement
in SVG, DXF and PDF; overcrowded sheets refuse rather than silently omit labels.
The 12-page example is a review set, with true sections and labelled wire
elevations. It is not a complete permit/construction-document package.
