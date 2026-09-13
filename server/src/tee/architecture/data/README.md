# Architectural reference and rule-pack contracts

These formats belong to archkiln's original headless model. No verified national
or municipal building-code corpus is bundled. Examples below and the test suite
use **synthetic rules, not legislation**. Format validation, IFC schema/EXPRESS,
IDS information checking, geometric checks and legal assessment remain distinct.

## Reference geometry

`inspect_source(path, units=..., transform=..., max_points=200000)` reads OBJ,
STL, GLB, XYZ/ASC/TXT, LAS/LAZ or the Unreal manifest below. Units are explicitly
`mm`, `cm`, `m`, `in` or `ft`. The optional invertible affine 4x4 matrix acts on
coordinates **after conversion to millimetres**; its translation is therefore
millimetres. The destination frame is right-handed, Z-up. Declare an axis change
in the matrix; the reader does not guess scanner or application axes.

The source remains unchanged. The result records its SHA-256, sampling policy,
sampled bounds, original unit/frame transform, numerical resolution and an origin
shift used for fitting. LAS quantisation bounds come from its header scales;
unknown source quantisation stays unknown. XYZ and LAS are read in bounded
streams; meshes are limited to 32 MiB and 4 million instanced source vertices.
Other sources are limited to 512 MiB, manifests to 1 MiB/128 instances. Meshes
use deterministic local-area surface samples; point clouds use evenly spaced
row indices. These samples are not a guarantee of complete physical coverage.

`propose(source, tolerance_mm=...)` verifies the source again, fits up to 12
planes using at most 20,000 sample points, and returns compact candidates with
residual RMS, P95/max error, sample-support fraction and world-space bounds.
These fractions describe sampled support, not wall completeness or an accuracy
certification. Sparse points, lines and unsupported geometry stay unclassified.
Inclined surfaces are not silently straightened into vertical authored walls.

Wall promotion requires a storey, height, thickness and **centreline_offset_mm**.
The offset is signed along the candidate's reported horizontal plane normal;
zero means the reviewer deliberately accepts the observed surface as the wall
centreline. A measured face does not reveal concealed thickness or material,
load-bearing role, fire rating, occupancy or legal use. `promotion` checks the
primary source and all manifest dependency hashes again and returns one atomic
model `create` operation. It does not apply that operation itself.
The promoted entity retains the reviewed fit statistics, tolerance, sampled
support, observed plane/bounds and uncertainty with the source hash and precision
record; this evidence travels with the exported architectural document.

## Unreal interchange manifest

This is a supported interchange format, **not a live-verified Unreal exporter**.
Export selected static mesh assets using the Editor and measure the export's
units/axis basis before composing each mesh-to-world transform. A component or
instance has its own transform. Do not assume an OBJ export has the same basis
as the actor's raw Unreal transform.

```json
{
  "schema": "tee-unreal-geometry/1",
  "frame": "right-handed-z-up",
  "transform_units": "mm",
  "instances": [{
    "actor": "OwnedHouse",
    "component": "WallMesh",
    "instance": "0",
    "mesh": "meshes/wall.obj",
    "units": "m",
    "transform": [[1,0,0,4000],[0,1,0,0],[0,0,1,0],[0,0,0,1]]
  }]
}
```

Call `inspect_source(manifest_path, units="mm")`; each instance declares its own
mesh units. Mesh paths must be relative and stay inside the manifest directory.
External material/buffer resolvers are not supplied. Supported mesh files are
OBJ/STL/GLB. The reader preserves actor/component/instance identity plus each
dependency hash in reference metadata; a compact aggregate dependency identity
travels with promoted entities. Procedural, skeletal, landscape, deformed,
Nanite-detail and cooked-game extraction are not claimed by this contract.

Primary sources checked 2026-09-11: Epic's [Editor Python execution
boundary](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python),
[AssetExportTask](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetExportTask?application_version=5.6),
[StaticMeshExporterOBJ](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshExporterOBJ?application_version=5.6),
[InstancedStaticMeshComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InstancedStaticMeshComponent?application_version=5.6),
and [LiDAR plugin formats and units](https://dev.epicgames.com/documentation/unreal-engine/lidar-point-cloud-plugin-overview-in-unreal-engine).
The cited class contracts do not establish the OBJ exporter's axis mapping.
Original scan files are preferable to a game-engine visualisation when available.

The optional `tee.architecture.unreal_export.export_selected` helper runs only
when explicitly invoked inside Unreal Editor. It imports no Unreal module at
normal TEE startup. It supports exact static mesh, instanced static mesh and
hierarchical instanced static mesh components; deformed subclasses refuse.
It writes into a new directory, exports each referenced asset once, and records
individual world transforms without moving, selecting, saving or editing actors.
Existing output directories are never overwritten.

The helper requires `mesh_units`, `mesh_to_unreal_mm`,
`unreal_world_to_target_mm`, four measured noncoplanar `basis_controls`, and a
`basis_evidence` reference. A control pair is
`{"mesh":[x,y,z],"unreal_mm":[x,y,z]}`. Both matrices act on millimetres;
the first maps the exporter's mesh basis to Unreal asset-local coordinates,
the second maps Unreal world coordinates to the chosen right-handed Z-up project
frame. There is no identity/axis default. Controls must agree with the supplied
mesh frame within `tolerance_mm` (default 0.1 mm). The check measures consistency
of supplied controls; it does not authenticate their origin or substitute for a
live exporter calibration. The helper reconstructs component transforms by
transforming origin/basis positions through Epic's documented API, avoiding an
assumption about Matrix storage. Unreal positions are converted from cm to mm.
Partial export failures leave files for inspection without a success manifest.

Additional primary class contracts checked against Python 5.6:
[EditorActorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorActorSubsystem?application_version=5.6),
[Actor](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Actor?application_version=5.6),
[StaticMeshComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StaticMeshComponent?application_version=5.6),
[SceneComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/SceneComponent?application_version=5.6),
[Transform](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Transform?application_version=5.6),
and [Exporter](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Exporter?application_version=5.6).
Epic documents the native frame in [Coordinate System and Spaces](https://dev.epicgames.com/documentation/en-us/unreal-engine/coordinate-system-and-spaces-in-unreal-engine).
The regression uses a stub Editor contract and real exported/imported OBJ files;
**live Unreal acceptance remains pending**.

## Worldwide rule packs

`rule-pack.schema.json` documents the wire format. `validate_pack` is the
authoritative bounded semantic validator and supplies a canonical SHA-256.
Canonical bytes are UTF-8 JSON sorted by key, with separators `,` and `:`, finite
values only, excluding the optional top-level `sha256` field. Rewriting a
threshold changes the identity and invalidates a supplied checksum/dependency.

```json
{
  "schema": "tee-architecture-rulepack/1",
  "id": "synthetic-door-fixture",
  "version": "1",
  "kind": "synthetic",
  "edition": "TEST ONLY 2026",
  "authority": "Owned synthetic fixture, not a building authority",
  "jurisdiction": {"country":"ZA","region":null,"municipality":null},
  "effective_from": "2026-01-01",
  "effective_until": "2026-12-31",
  "rules": [{
    "id":"fixture-width","clause":"SYNTHETIC-1",
    "fact":"entities.*.width","entity_kind":"opening","where":{"fill":"door"},
    "op":"gte","value":800,"unit":"mm",
    "applicability":[{"fact":"project.facts.occupancy","op":"eq","value":"dwelling"}]
  }]
}
```

There is no implicit default country. Matching proceeds through explicit country,
region and municipality; a missing required location is `not_verified`, a
different location is `not_applicable`. Pack authority identifies its issuer;
authority-dependent selection uses an explicit applicability condition on
`project.facts.authority`. Both effective-date endpoints are inclusive.

Regulatory evaluation additionally requires these supplied provenance records:

- `source`: `kind: "primary"`, HTTPS `url`, `title`, source-document `sha256`,
  `accessed_on`, and a `clauses` list containing every implemented rule's clause.
- `review`: `status: "reviewed"`, named `reviewer`, `reviewed_on`.
- `adoption`: named `instrument`, `url`, `effective_on`.
- Exact parent dependencies in `requires: [{id, version, sha256}]`. Amendments
  replace only explicitly named parent rules via each rule's
  `overrides: [{pack_id, rule_id}]`; missing parents, changed identities, cycles
  and ambiguous editions produce `not_verified`.

These records are not fetched or independently authenticated. Source access,
licensing, local adoption, translation and reviewed interpretation must be
established by the party preparing a real pack. Draft metadata can be loaded
but cannot produce a verified regulatory rule result. Different thresholds for
the same target are conservatively treated as a conflict without an exact
parent override; a complex interaction needs a reviewed dedicated rule design.

Rules use finite numeric `gt/gte/lt/lte/eq` comparisons. No Python, expressions,
network lookups or executable callbacks are accepted. Units are explicit;
mm/metres and square-mm/square-metres convert, other incompatible units refuse.
Entity facts address explicit authored millimetre dimensions through
`entities.<id|*>.<dimension>`; `entity_kind` and up to eight literal `where`
filters select their scope. Project measurements use bounded paths below
`project.facts` and a record `{value, unit, evidence:{kind,source}}`; evidence kind
is `measurement` or `model`. Applicability uses literal `eq/in` predicates on
project facts. Missing measurements, provenance, applicability or implementations
produce `not_verified`, and an empty entity selection never produces a vacuous
pass. No absent values, dimensions or source facts are invented.

A measurement may declare `uncertainty` as a nonnegative half-width in its own
unit. The evaluator converts and checks the whole interval. If it crosses a
threshold, the result is `not_verified`; uncertain equality never passes from
the centre value alone. Missing uncertainty means the rule compares only the
supplied exact value, not that the physical measurement has zero error. An
unrecognised uncertainty field or malformed error value is not silently ignored.

Limits: 64 packs per pure assessment, 256 rules/pack, 1 MiB/pack, 4096 emitted
checks. The TEE service may impose tighter caller budgets. Synthetic passes are
labelled `synthetic_fixture_only`. A reviewed subset can pass individual rules,
but overall coverage stays `not_verified` because a complete applicable-law
inventory has not been established. Learning can rank geometry methods; this
module exposes no learning or threshold mutation operation.

The need for adoption/edition/amendment scope is grounded in [ICC's adoption
resources](https://www.iccsafe.org/advocacy/code-adoption-resources/); country-specific
parameters are illustrated by the European Commission's [Nationally Determined
Parameters](https://eurocodes.jrc.ec.europa.eu/en-eurocodes-implementation/nationally-determined-parameters).
Neither source supplies a worldwide executable building-code corpus.
