# CADAgent architecture in TEE — A83 development

CADAgent's TEE lesson library now reaches the headless architectural core. The
client can build and revise typed roof/stair studies, inspect the existing BIM
dwelling and cabinetry, and generate drawings, IFC and GLB. The optional GUI
edits the same model. These changes are in isolated A83 development; accepted
HF2 remains installed on the actual clients.

## Visible Okongo roofs — development checkpoint, 2026-09-11

The missing roof correction is complete in isolated A83 development.
[Roof-visible 03](/Users/john/TokenEfficiencyEngine/output/architecture/okongo-benchmark/roof-visible-03/REPORT.md) passes **17 of 17 measured checks**.
The native model now contains 14 roofs: three gables, six sheet roofs and five
concrete cores, exported as 17 independently verified physical roof bodies.
The central gable keeps its off-centre ridge and unequal eaves. The 248 native
entities retain the earlier one-storey/25-room correction and source opening levels.

The [40-page review set](/Users/john/TokenEfficiencyEngine/output/architecture/okongo-benchmark/roof-visible-03/project/output/archkiln/building_d692fa24855144b4/20260911T135357Z-76430a72/review-set.pdf) adds a roof plan, a
[3D roof view](/Users/john/TokenEfficiencyEngine/output/architecture/okongo-benchmark/roof-visible-03/visual-review/page-05.png) and two roof-register pages. All 81 annotation IDs are
covered with no font substitutions. Thirteen changed/new pages were directly
inspected; the other 27 drawing bodies match previously inspected pixels after
normalizing only changed sheet/drawing-reference glyphs. Additional spot checks
cover eight unchanged pages. The measured height-number/level-leader collision
is fixed through shared PDF/SVG/DXF/GUI text placement; dimension endpoints and
physical level ticks remain exact. These remain scoped review drawings, with
construction setting-out and full operating details still incomplete.

Independent source-to-IFC/GLB checks verify all top/bottom vertices, footprints,
normal thicknesses and signed volumes, plus 14 IFC roof identities and 12
aggregated plane children. The largest GLB corner error is 0.000364 mm or less.
An initial benchmark bug ignored GLB node transforms; its failed evidence is
retained and the reader now measures positioned mesh instances.

Validation: **963 regression tests pass**, two browser-gated skips; both actual
Chrome workflows pass separately with 14 A83 checks each and eight delayed-response
checks on the delayed run. Ruff passes. The final run used 43 semantic MCP calls,
45,301 estimated semantic tokens and 13,732 polling tokens in 6.40 s. This is one
incomplete-shell observation during concurrent validation, not completed-house
performance or competitor parity. Matched tool composition remains 17 core tools,
2,129 core tokens, 225 discoverable tools and 35,069 flattened tokens, unchanged.
Actual installed TEE status separately confirms Q14B active and 261 virtual tools.

The source generator's 60 mm sheet shell is a nominal preview envelope. The three
gable covering records specify 0.47 mm metal; flat-sheet gauges are unknown. Level
source surfaces remain level because falls are assumptions. The open pergola is
not converted to a closed roof and its member geometry remains unimplemented.
Source weather-coverage gaps remain explicit: passage_8 2.886822 m² and master
bedroom 0.103050 m². Gable closures, structural framing, insulation, drainage,
flashings and full opening assemblies remain incomplete. Cabinet production,
independent BIM/jurisdiction and full-building acceptance remain open.

Development payload: `c7e17f018040718b87ead9c1d1e7bef10620d1c95bdd70911c1bd2efa435bea0` (307 files / 3,837,644 bytes).
Installed Claude filesystem remains HF2 `c0f95e836b4207f3fa8bfe45f3d9c8781e622025d8027841d0b27bcac096811e`. During this slice
the separate checkout advanced to commit `eb711465fab08d4e8179ee183090402d470e6354`
(doctor --emit launch fix); main payload is now `12bff7832f62da51e3ef3f0431a8861a591c84ece8799cca691614aaec9292a2`. Only doctor.py
differs between current main and installed HF2. That concurrent change has not
been ported into isolated A83 and must be reconciled before a release freeze.
These are filesystem identities, not new two-client runtime acceptance receipts.

[Machine checkpoint](/Users/john/TokenEfficiencyEngine/output/updates/TEE-20260911-A83-01/evidence/okongo-roof-checkpoint.json), SHA-256 `00bc7edd6c843e8dc590bee490be20091dd5ff041b3ae5fa4eaa5c1707ef5552`. Original OkongoSim inputs and cached
build files are unchanged. No A83 package was frozen or installed and no DCC
scene was modified. The owner-requested TEE/Q14B selection is active separately.

## Previous checkpoint before the roof correction

The previous Okongo correction checkpoint is
[corrected 03](../output/architecture/okongo-benchmark/corrected-03/result.json):
14 of 14 measured benchmark checks pass. It preserves 25 room identities on one
real building storey, uses element base offsets, and removes the zero-solid IFC
host through an explicitly nonphysical reference. Drawing export produces 36
scoped review sheets, with plotted review complete. The current
kitchen now has a traceable 137-panel construction candidate. These are
development corrections; they do not establish complete-house, fabrication or
installed-client acceptance.

Final corrected-03 validation: **912 regression tests pass** (2 browser-gated
skips, 41.23 s); the two actual headless Chrome workflows pass separately
(12.76 s), including delayed responses and shared level-label alignment. Ruff
passes. The final Okongo run passes all 14 measured checks in 43 semantic MCP
calls: 4.85 s, 40,768 estimated semantic tokens and 11,924 polling tokens. This
is one incomplete-shell workflow observation, with no completed-house or
competitor speedup claim.

All 36 plotted pages were inspected through exact rendered images and verified
page-identity transfer after the final fixes. Crowded height labels now use
separated leaders or a complete reference key. Levels outside a section retain
their values in explicit Outside view notes, with no invented visible ticks.
Schedule dimensions are labelled authored apertures, not manufacturer/order
sizes. The two roof/stair export regressions caught by the combined suite are
fixed; failed intermediate evidence is retained.

Development payload: `a7493681f4f46d61be403b6c7b45efe3b5464cd93edca691a5022dcf792a0300`
(307 files / 3,812,915 bytes, complete non-cache runtime).
Main and installed Claude filesystem payloads remain HF2 `c0f95e83…6811e`.
These are filesystem observations, not new actual-client installation receipts.
See the [checkpoint](../output/updates/TEE-20260911-A83-01/evidence/okongo-corrections-checkpoint.json),
[independent review](../output/architecture/okongo-benchmark/corrected-03/independent-review.md)
and [review PDF](/Users/john/TokenEfficiencyEngine/output/architecture/okongo-benchmark/corrected-03/project/output/archkiln/building_7c4ec99c102a42e7/20260911T125840Z-ea07d1e3/review-set.pdf).

The source-room overlap between master bedroom and ensuite remains exactly
0.111818 m²; source geometry was preserved. Checked room volumes are constant-height
source prism envelopes, not finished raked-room volumes. Construction drawings,
complete building systems, manufacturing acceptance and coordinated A83 delivery
remain open.

Discover with `tee_search_tools(query="CADAgent architecture")`, then call:

```json
{"name":"ak_guide","args":{}}
```

The existing Fusion and Blender `lane_guide` indexes also expose
`cadagent_architecture`, directing the client to this interface. No separate
upstream CADAgent backend or model training is introduced.

| Topic passed to `ak_guide` | Workflow |
|---|---|
| `cadagent_roof_stair.build` | Create two levels, a typed gable roof, straight monolithic stair and upper landing. |
| `cadagent_roof_stair.revise` | Atomically raise the upper level and revise roof pitch and riser count. |
| `cadagent_roof_stair.inspect` | Read quantities/issues and export revision-bound IFC, drawings and GLB. |
| `cadagent_stair_clearance.block` | Add an upper floor to the initial study and report the stair obstruction. |
| `cadagent_stair_clearance.open` | Cut a hosted floor opening and remeasure headroom. |
| `cadagent_stair_clearance.inspect` | Read slab/opening quantities, clearance witness and coordinated exports. |
| `cadagent_bim.build` | Create the typed compact dwelling with four kitchen cabinets. |
| `cadagent_bim.inspect` | Inspect types, opening sill/head levels, cabinetry and design issues. |

Each card returns ordered `calls`, acceptance checks and an undo call. Substitute
actual returned `$model_id` and `$revision` values, then execute through
`tee_call`. Requesting a guide alone performs no authoring. Exports return `job`;
pass it as `job_id` to `tee_job` and inspect the completed result and files.
Existing TEE-wide learning observes the tool outcomes without extra model calls;
execution success alone is not design quality.

The retained [initial model](../output/architecture/a83-roof-stair/initial/document.json)
has a 3000 mm rise, 16 risers at 187.5 mm, a 4160 mm flight run and a 30° roof.
The [revised model](../output/architecture/a83-roof-stair/revised/document.json)
has a 3600 mm rise, 20 risers at 180 mm, a 5200 mm flight run and a 45° roof.
Both keep a 1000 mm wide stair, 1000 mm upper landing and 48 m² roof footprint.

The [revised drawing study](../output/architecture/a83-roof-stair/revised/review-set.pdf)
contains two plans, a section through the actual stair, a roof section and four
elevations. This is a system geometry study, not a complete house/construction set.
The [IFC](../output/architecture/a83-roof-stair/revised/building.ifc) and
[GLB](../output/architecture/a83-roof-stair/revised/building.glb) were reopened and
measured against model-derived quantities and bounds. Both revisions are retained
in the [replay evidence](../output/architecture/a83-roof-stair/cadagent-replay.json).

Legacy roof forms are `flat`, `mono` and `gable`. Mono/gable roofs require a rectangle in
boundary order; edge 0→1 defines the slope direction, with a gable ridge halfway
along that edge. The footprint includes eaves. `base_height` locates the eave
underside above its storey, and `thickness` is normal to the slope. Vertical cuts
meet at the ridge without overlapping volumes. Pitch is greater than 0° and
below 80°. Flat roofs retain supported arbitrary polygons.

The Okongo correction adds `form: "planes"` for explicit, asymmetric roof
geometry. Each patch has an `id`, a polygon of XY millimetres and matching
`elevations` for its **top** vertices above storey elevation plus `base_height`.
The patches must be planar, meet without gaps/overlaps and cover the parent
footprint. Shared top edges must agree. `thickness` is measured normal to each
plane; vertical edge cuts preserve the exact source footprint. Scalar
`pitch_deg` is zero or omitted; actual pitches derive from the vertices. The
legacy underside datum is unchanged. The GUI accepts the same patch JSON,
offers roof-plan/roof-axonometric views and supports undo. IFC keeps one
`IfcRoof` identity with physical roof-slab children, without a duplicate parent
solid. A nominal preview envelope must not be reported as manufactured sheet
metal volume or mass.

Stairs use `storey`, `top_storey`, `start`, `direction_deg`, `width`, `riser_count`,
`going`, `waist_thickness` and `landing_depth`. Rise derives from both storey
elevations. There is one tread per riser; the last tread meets the upper level.
A zero landing depth omits the extra landing. Waist thickness is normal to the
underside; the lower connection extends below its level and needs bearing design.
The 2–64 riser bound is an implementation limit, not a regulatory allowance.

IFC exports preserve the roof form and actual solids. An `IfcStair` contains an
`IfcStairFlight` and optional `IfcSlab` landing, with native counts/heights,
containment on the lower storey and a reference to the upper storey.

The initial roof/stair slice passed 40 focused system checks, actual card replay
through MCP, a broader 786-check regression and two real Chrome workflows. The browser
checks cover roof pitch overrides, destination-level edits, schedules, native
stair creation and undo. The 17 core tools/schemas remain unchanged; `ak_guide`
is one additional discoverable tool.

Complete roof/stair systems remain open: automatic hip/intersection solving, drainage,
weathering/junctions, layered pitched roofs, multiple flights/winders, railings,
clearance against other obstacle classes and structural design. Hosted floor
openings and slab/roof headroom are now implemented as described below. Pitched roofs refuse layer
bindings until material usage can be represented per plane. Worldwide legal
approval, full competitor parity and commissioned CNC remain unverified.
Deployment follows A83's coordinated release and both actual-client receipts.

## Hosted floor openings and headroom — development continuation

Use `cadagent_roof_stair.build` in a fresh study, followed by the clearance cards
`block`, `open` and `inspect`. The separate `roof_stair.revise` card changes the
flight length; its opening must then be redesigned and checked rather than
assuming the original study dimensions still fit.

A `slab_opening` has `slab` (host ID) and `polygon` (project XY in mm), in addition
to the ordinary ID/name fields. It cuts the complete current host thickness and
follows the host level. Polygons must lie strictly inside the slab; overlapping,
touching and edge-notch openings are refused. Multiple separate concave openings
and concave slab boundaries are supported. Host removal needs corresponding
opening deletion in the same atomic batch.

The stair's optional `headroom_target_mm` is an explicit design input. Omit it
or set it to null for unset; the GUI leaves this optional field blank. Existing
`ak_query` schedules collections now include `slabs` and `slab_openings`;
`stairs` includes headroom, a limiting obstacle/point and support contacts.
Slab schedules distinguish gross, removed and net area/volume. Drawing CSV uses
net `area_m2` for slabs and also supplies explicit gross/net columns.

Headroom measures vertical distance above the full-width nosing pitch line,
then the horizontal upper tread and landing. It finds polygon/plane extrema
against authored slab and roof solids, including floor holes, sloped surfaces
and narrow edge obstructions. It does not sample a centreline or grid. Solid
penetration gives zero clearance and an interior witness; slab-top support
contact is separate. `target_unset` and `no_overhead_in_scope` never imply a pass.
Walls, beams, services, railings, other stairs and imported references are outside
this check. Bearing, guard design and jurisdictional requirements remain unverified.

The retained [blocked study](../output/architecture/a83-stair-clearance/blocked/document.json)
reports 0 mm clearance. Its [corrected study](../output/architecture/a83-stair-clearance/corrected/document.json)
has a 4460 × 1100 mm opening meeting the landing end: 4.906 m² removed,
43.094 m² net floor area and 8.6188 m³ slab volume at 200 mm thickness.
Minimum scoped headroom is 2107.692 mm against the study's explicit 2100 mm
target; that target is not a local-code assertion.

The [ten-sheet corrected study](../output/architecture/a83-stair-clearance/corrected/review-set.pdf)
includes floor-void marks/dimensions and a coordinated schedule. Actual IFC/GLB
readback agrees with the net quantities; IFC retains the host/opening relationship
and existing product GUIDs. The [MCP replay](../output/architecture/a83-stair-clearance/cadagent-replay.json)
also records stale-edit refusal and undo. This remains a system study, not a
complete house construction set. The 21 new focused checks and two real browser
workflows cover this continuation. No additional virtual or core tool was added.
That continuation's combined architecture/cabinet/CADAgent regression passed 807 checks,
with the two browser gates run separately. The complete evidence is in
[the development checkpoint](../output/updates/TEE-20260911-A83-01/evidence/stair-clearance-checkpoint.json).

## Okongo benchmark and architectural knowledge

The [Okongo benchmark guide](okongo-architecture-benchmark.md) now supplies a real
project alongside the CADAgent studies. Its repeatable shell runner uses actual
MCP calls, independent source comparisons, IFC/GLB readback and an intentionally
incorrect window sill followed by undo. The separate current-kitchen audit calls
the native cabinet kernel against the actual nine-strip production definitions.

The retained baseline 04 preserves the original failures: crowded drawing
annotations, an empty IFC gap host and fragmented room/storey identities. Its
`9f0ad893…82da1` development payload is historical. It must not be used to identify
the corrected runtime or to describe which measured checks still fail.

Corrected 03 preserves 25 source footprint areas as 25 native/IFC spaces,
including multipart rooms, on one actual storey. `base_offset` distinguishes an
element's local vertical placement from building storeys. All 125 specified
wall volumes still match independent IFC and GLB readback. The 42 rectangular
source comparisons now comprise 41 physical-host apertures and one virtual
reference. The virtual boundary represents the location of the unmodelled
specialist frosted-glass partition `o01_master_ensuite_open`: it is neither a physical filling nor an empty
traversable passage. IFC schema, solid and spatial identity checks pass.

Room scope views now preserve clipped model geometry and place readable labels
and leaders, with crop locators and coverage of 67 unique annotation IDs across the set. Full
opening labels use the host base offset when reporting sill height above FFL.
The 36-sheet output remains a scoped shell-review set, **not a dimensioned
working set**: room setting-out, detailed assemblies, fixture/operation
clearances and repeated or cross-referenced opening marks remain incomplete.
All-set label coverage cannot certify the independent usability of each sheet.

The existing `ak_edit` interface accepts the new spatial fields; no additional
always-loaded tool is required:

| Field | Meaning |
|---|---|
| `base_offset` on wall, space or slab | Signed millimetres relative to its storey; omitted means zero. Changing it leaves the storey elevation unchanged. |
| `additional_polygons` on a space | Additional exterior footprint rings belonging to the same room identity. |
| `kind: "virtual_boundary"` | An explicit nonphysical reference with storey, start/end, height and optional base offset. It has no physical thickness. |
| `space_ids` on a virtual boundary | Up to two explicitly established adjacent spaces on the same storey; connectivity is never inferred from the reference alone. |
| `project.facts.drawing.plan_scope_mode: "rooms"` | A whole-plan overview and named enlarged room scopes, shared by exports and the GUI. |

The GUI exposes offsets, multipart footprints and virtual references directly.
Imported candidate promotion accepts an explicit base offset and records whether
it came from authored override, declared dimensions or the zero default; scan
bounds alone do not establish a building datum.

The current [kitchen reconciliation](../output/architecture/okongo-benchmark/kitchen-reconciliation-01/findings.md)
produces a [canonical candidate](../output/architecture/okongo-benchmark/kitchen-reconciliation-01/canonical-candidate.json)
with 137 individual board panels and two separately recorded stone worktops.
Physical roles/dimensions resolve 130 manual quantities plus six drawer parts
and one bin bottom; the PDF's 119-panel verification claim is not the current
part total. Rev C matt-white fronts and 1 mm white ABS remain the finish intent.
Six positive-volume drawer-bottom/end overlaps are measured in the source
geometry. Joint alternatives are explicit and unselected, and manufacturing
blanks remain unset. Native recipes still cover 14 of 16 modules, with full-back,
drawer-joint, continuous-plinth, top-box, pull-out and hardware work outstanding.

Remaining acceptance targets include dimensioned construction documentation,
complete roof/envelope and opening systems, usable-space and physical-performance
checks, independent BIM receiving-tool tests, verified applicable jurisdiction
rules and commissioned CNC output. The whole Okongo building and fabrication
package are not accepted. A83 still needs a coordinated package and receipts
from both actual clients before deployment can be called complete.

[Research 86](research/86-architectural-knowledge-and-bim-cases.md),
[research 87](research/87-building-practice-and-fabrication-cases.md) and
[research 88](research/88-global-code-source-map.md) connect six real projects,
BIM information standards, building science, fabrication and jurisdictional
sources to proposed checks. Source conditions and applicability accompany each
lesson. These notes add research and test proposals; they do not add installed
CADAgent cards, train a model or activate global compliance rules.


The autonomous A83 candidate adds `cadagent_circulation.build` and
`cadagent_circulation.inspect` to `ak_guide`. The first creates an isolated exterior
space and an oriented column, with explicit geometric clearance targets; the
second reads route witnesses, BIM information gaps and member quantities through
paged reports. Optional GUI edits use that same document. It distinguishes real
openings, reference footprints, physical objects and unknown operation envelopes.
No lesson grants itself permissions, starts model training or approves a design.

The next development candidate, A83-02, adds three executable service lessons:
`cadagent_services.build`, `.inspect` and `.repair`. Build creates a separate
rotated, hollow-duct study with a 25 mm gap. Inspect reads paged connection,
port and system reports. Repair moves the second duct onto its measured mate,
then exports IFC4 with fixed nested ports, system membership and one verified
connection. Both outer ends stay explicitly unconnected. The lesson is synthetic;
it does not add an invented service layout to Okongo.

Read `ak_query` with `detail="distribution"` and collection `systems`, `ports`
or `connections`. Author the same definitions in the optional GUI under Building
services. A proposed link may remain in an editable model while checks fail; IFC
export refuses to assert it as connected. Endpoints, mating sections, normals,
profile orientation, service membership and explicit source/sink pairing must
agree within the declared tolerance. Fittings, terminals, seals, support, system
sizing and authority acceptance are separate unfinished requirements.

These lessons passed the actual MCP client/server harness, including independent
IFC readback, stale-revision rejection and undo. They are in isolated development,
not either installed client. RC1 and its Downloads delivery remain frozen.

`cadagent_thermal.inspect` reads the next candidate's sourced assemblies, selected
surface calculations, zone subtotals and space classifications. Use
`ak_query detail="thermal"` with `assemblies`, `surfaces`, `zones` or `spaces` for
individual pages. The optional GUI edits `project.facts.thermal` in the same model.
Missing physical values stay unknown; walls exclude aperture areas and window
inputs must describe the whole product. Exterior spaces cannot be assigned to
conditioned zones. Signed negative outward heat flow is heat gain. The report
does not supply a whole-building load, annual energy or equipment sizing.

The separate Okongo thermal comparison passes 11 checks, including aperture area
measured from reopened IFC and refusal of a conditioned Passage 12. Its 24/35 °C
temperatures and 2.8/1.4 W/(m² K) window values are illustrative inputs. They do
not establish actual weather or product ratings. See research 91 and
output/architecture/okongo-benchmark/thermal-comparison-02/review.md.
