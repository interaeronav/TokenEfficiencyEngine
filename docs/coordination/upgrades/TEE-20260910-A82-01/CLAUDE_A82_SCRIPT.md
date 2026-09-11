# A82 — archkiln, headless architecture and cabinetry inside TEE

Owner request: original Archicad-inspired architectural software inside TEE,
with cabinet making, conversion from Unreal scenes/meshes/LiDAR, professional
architectural deliverables, worldwide jurisdiction coverage, and a GUI used
when needed. The owner has asked work to continue quietly until completion
while asleep. Use judgment for reversible implementation choices; preserve
existing authorization, QMAX, dirty work and the shared upgrade protocol.

`archkiln` is the working product name; the module is `tee.architecture`, with
progressively disclosed `ak_*` tools. It uses one headless command/state model
for TEE, exports and the optional GUI. No copied Archicad or Bonsai code/assets.
Research 83 and the existing-capability map are the design of record.

## P0 — grounding and continuity

- [x] Map existing IFC, point-cloud, CAD, cabinetry, drafting and Unreal seams.
- [x] Verify installed IfcOpenShell/IfcTester 0.8.5 and primary API/licence facts.
- [x] Record worldwide country/region/municipality scope and optional same-core
  GUI; do not ask for one city as a prerequisite to building the common engine.
- [x] Preserve A81's frozen packets and record its runtime rollout held for the
  combined successor before editing runtime. A82 requires a new frozen manifest;
  do not mutate or reuse A81's delivered artifact identities.
- [x] Measure baseline using the canonical served fixture before schema changes:
  17 core / 2,129 wire tokens, 209 virtual / 32,427 flattened tokens; evidence
  `output/architecture/surface-before.json`.

## P1 — one authoritative architectural document

- [x] Implement explicit millimetre units, stable IDs, versioned project data,
  atomic validated batch edits, dependent-object constraints, undo and save/reopen.
- [x] Author storeys, wall centrelines, hosted door/window openings, room polygons,
  slabs, simple roofs and cabinet assemblies. Required dimensions stay explicit;
  missing heights/material/fire/structural facts must not be guessed.
- [x] Generate headless cabinet panel geometry, cutlist, grain and edge schedules,
  explicit hardware/machining requirements and sheet layout with kerf. Do not
  claim manufacturer or CNC readiness from generic geometry.

## Shared implementation contract

`Document` in `model.py` provides `create(name)`, `from_dict(data)`, `to_dict()`,
`apply(operations, expected_revision=None)`, `undo(expected_revision=None)`,
`summary()` and `validate()` (raises `ArchitectureError` with concise fix).
`to_dict()` is a copy. A document has `schema="tee-architecture/1"`, `units="mm"`,
`revision`, required immutable `document_id` (canonical UUID generated at create),
`project={name,jurisdiction:{country,region,municipality},facts:{}}`,
and `entities`, a map keyed by stable entity IDs. History is persisted separately
or in a bounded field and never sent by default. All numbers must be finite.

Operations are `create` with `entity={id?,kind,...}`, `update` with `id,changes`,
`delete` with `id`, or `project` with `changes`. Batches are atomic. Client-supplied
IDs use safe alphanumeric/underscore/hyphen strings; generated IDs start `ak_`.
Entity fields, all dimensions in mm:

- storey: `name,elevation,height`.
- wall: `name,storey,start:[x,y],end:[x,y],thickness,height`; centreline in world XY.
- opening: `name,wall,offset,width,height,sill,fill:"door"|"window"|"void"`;
  offset is along wall from start, sill above storey; intervals must fit host.
- space: `name,storey,polygon:[[x,y],...],height`; simple polygon, no repeated end.
- slab: `name,storey,polygon,thickness`; top at storey elevation.
- roof: `name,storey,polygon,thickness,base_height`; flat initial representation,
  explicitly recorded, not an approximation presented as a pitched roof.
- cabinet: `name,storey,origin:[x,y,z],width,depth,height,panel_thickness,
  back_thickness,shelves,doors,plinth_height,grain,edge_band_mm,material`.
  Origin is world mm, width+X/depth+Y/up+Z; no silent hardware catalogue defaults.
  A cabinet with doors requires explicit `properties.door_gap_mm` for its
  construction clearance; the example uses a declared 2 mm design parameter.

Optional `properties` and `provenance` are bounded JSON data. Unknown construction
attributes stay absent. Exchange, rules, GUI and imports consume this dictionary
contract and return compact structured evidence. They do not implement another
authoring state. Core modules are dependency-light; IFC/mesh libraries import
only inside the relevant operation.

## P2 — architectural and shop deliverables

Implementation amendment from measured geometry: centreline wall prisms overlap
at L/T junctions and their corner union leaves an outer notch. Add explicit
`project.facts.wall_join_policy="orthogonal_butt_v1"`. Equal-base/top orthogonal
L junctions choose the lexicographically lower stable wall ID as the through
wall, extend it by half the other thickness and trim the abutting wall by half
the through thickness. At T junctions the continuous wall is through. Keep
authored centrelines/opening offsets unchanged and share derived extents across
IFC, mesh and drawing outputs. Refuse unsupported intersections, ambiguity,
consumed lengths and openings conflicting with adjusted junctions. An absent
policy retains explicitly unjoined geometry and its overlap evidence. The
compact-house example opts into the declared policy.

- [x] Produce semantic IFC4 with stable GUIDs, correct storey/placement units,
  containment, spaces, slab/roof geometry, hosted openings/fillings and cabinets.
  Independently reopen and measure both attributes and generated geometry.
- [x] Generate plan/elevation/section and cabinet panel SVG/DXF plus schedules,
  CSV cutlists and a reviewable PDF set when existing libraries support it.
  Bind dimensions and quantities to the current document revision.
- [x] Separate IFC schema/EXPRESS, IDS information, geometric and regulatory
  checks. Never equate an information or schema pass with building approval.
- [x] Fix the measured existing IFC exporter metre/mm Storey.Elevation defect
  with a regression. No unrelated export rewrite.

## P3 — conversion with measured provenance

- [x] Accept meshes and original LiDAR through existing installed readers with
  explicit units, axis/frame and retained source hashes. Bound processing and
  require project-contained input/output paths at the TEE boundary.
- [x] Accept a documented Unreal actor/instance/mesh manifest with transforms;
  include a source-verified export helper for supported Editor objects. Distinguish
  this format support from an actual live Unreal exporter verification.
- [x] Produce measurable planar/wall candidates from geometry, with fit residuals,
  contributing region, coverage and uncertainty. Review/promote explicit candidates
  to authored entities; preserve unclassified/occluded geometry as reference.
  Do not infer concealed thickness, fire rating, structural role or legal use.
- [x] Verify unit/frame round trips, labelled conversion and ambiguous/degenerate
  negative cases on owned fixtures. Actual unavailable DCC acceptance stays open.

## P4 — worldwide rule-pack framework

- [x] Implement country → region → municipality/authority selection, explicit
  effective dates, source editions/clauses, adoption/amendment dependencies and
  coverage. No implicit US or other default jurisdiction.
- [x] Evaluate only bounded declarative rule operations on supplied/measured
  model facts. Missing location, verified sources, applicability, measurements
  or rule support produces `not_verified`; conflicts fail closed.
- [x] Include positive/negative/boundary fixtures using labelled synthetic rules,
  plus available primary-source grounding. Do not call synthetic rules law.
  Licensed, unreviewed or unimplemented worldwide rules remain explicit coverage
  debt. A country selector is not proof all its legislation is encoded.
- [x] Legal thresholds are version-controlled source interpretations; learning
  may rank modelling/conversion methods but may not change legal thresholds.

## P5 — optional GUI and TEE integration

- [x] Provide a local optional GUI with project/storey/entity selection, plan/3D
  preview, parameter editing, undo, imports/candidate review, cabinet schedules,
  export and jurisdiction/coverage results using the same service operations.
  The GUI stays absent from ordinary headless startup and has no remote assets.
- [x] Keep the GUI server loopback-only with per-session authorization, request
  limits and same-origin controls. Preserve atomic persistence across clients.
- [x] Register individual `ak_*` trust rows and canonical attach_all wiring,
  bounded responses and job handling where appropriate. Add zero always-loaded
  tools. Reuse existing capabilities; do not grant new authority silently.
- [x] Test a complete two-room house with openings/roof and a cabinet, edit and
  undo it through both headless and GUI APIs, and verify all derived artifacts.

## P6 — delivery and honest acceptance

- [x] Run relevant tests/lint, measure the canonical before/after tool surface,
  and record outcomes/limitations in PROGRESS, research and user docs.
- [ ] Prepare a combined successor package containing A81 documentation workers
  and A82 architecture, with complete common payload, matching client deliveries,
  rollback and private continuity. Preserve all prior immutable deliveries.
- [x] Leave owner-only Desktop operations, still-unapproved execution permission
  and actual-client receipts pending while the owner sleeps. Do not wake him or
  send external messages. No real paid inference is needed for validation.
- [x] Do not claim universal regulatory coverage, professional certification,
  live Unreal support, or both-client installation without the specific evidence.

Full worldwide verified law coverage depends on jurisdiction-by-jurisdiction
source access, adoption mapping and reviewed implementation. Continue the useful
software work independently; record that external dependency rather than invent
legislation or block the entire headless/GUI/cabinet system on it.

Validation evidence (2026-09-10 UTC): 674 affected tests passed, 4 intentionally
deselected by the existing suite markers; warnings treated as errors and Ruff
clean. Two real isolated headless Chrome cases include eight delayed-response
race controls. Full owned house/scan/cabinet/export workflow passes in 1.460 s;
real IFC wall volume 22.846 m³, six supported joins, 12 PDF pages and seven
revision-bound annotations independently checked across formats. The current
served benchmark is 17 core / 2,129 wire tokens and 220 virtual / 33,947 flat
tokens (93.7% saving); actual five-adapter package context is measured separately.
See output/architecture/ and research 83. Full worldwide law, live Unreal
calibration, expanded construction systems, CNC/authority approval and actual
client rollout remain explicit external or later-scope requirements.
