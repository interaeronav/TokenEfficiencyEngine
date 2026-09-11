# A82 foundation research — architectural core, imports and global rule coverage

Research date: **2026-09-11, Asia/Qatar** (2026-09-10 UTC during this session).
Status: **architecture implementation and P2 exchange/drawing evidence measured**.
The foundation sections below preserve the initial pre-build research chronology;
the implementation, explicit join policy and measured results are recorded in the
P2 section at the end. No dependency installation or legal certification is
claimed. The owner's scope is worldwide, with verified rule coverage reported
separately from the working jurisdiction-independent architectural core.

## Recommended foundation

Build an original, headless architectural model and command layer with stable
element IDs, explicit units, dependency-aware edits, reversible transactions and
compact diffs. Use the existing IfcOpenShell library as the semantic IFC and
geometry backend. Rooms, storeys, walls, openings, assemblies, materials and
dimensions must remain model objects; a rendered mesh is a derived view. An
optional GUI should submit the same commands and consume the same state/diffs
as TEE, with no second geometry or rule implementation.

Archicad can inform the desired workflow (model, document, schedule, coordinate),
while the implementation and interface remain original. This research does not
assume access to Archicad source, a compatible native project writer or its
commercial object libraries.

### Installed foundation, measured read-only

The shared server interpreter is
`/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`. Distribution metadata
reported these versions; no environment was changed:

| Distribution | Installed version | Relevant role |
| --- | --- | --- |
| ifcopenshell | 0.8.5 | IFC parsing, semantic authoring, geometry and validation |
| ifctester | 0.8.5 | Explicit IDS information checks |
| numpy | 2.4.6 | Existing numeric foundation |
| scipy | 1.17.1 | Existing fitting/spatial algorithms |
| trimesh | 5.1.0 | Existing mesh handling |
| laspy | 2.7.0 | Existing LAS/LAZ lane |
| lazrs | 0.8.2 | Existing LAZ codec |
| ezdxf | 1.4.4 | Existing DXF output |
| PySide6 | absent from this interpreter | Do not make a GUI a core import requirement |

The installed `ifcopenshell/__init__.py` and `ifctester/__init__.py` headers and
their metadata both identify LGPL version 3 or later. Upstream separately lists
IfcOpenShell-Python and IfcTester as LGPL-3.0-or-later, and **Bonsai as
GPL-3.0-or-later**. Therefore use the existing libraries through their public
interfaces and keep any optional Bonsai integration an external IFC client;
do not copy Bonsai implementation into the original core. Record redistribution
notices and the exact dependency build separately. A process boundary alone is
not a blanket licensing conclusion. [Upstream component licence table](https://github.com/IfcOpenShell/IfcOpenShell#contents)

The official documentation inspected is labelled **IfcOpenShell 0.8.5**, matching
the installed version. The repository's current default branch presents newer
development; do not silently replace the installed API target with that branch.

## Semantic authoring and four different kinds of checks

The official high-level authoring interface creates rooted entities, including
projects, storeys, walls and spaces, while handling GUIDs and defaults. Reuse its
project → site → building → storey hierarchy and spatial containment. Define
project units and representation contexts before creating geometry. IFC geometry
is optional, so entity presence alone does not prove a visible or usable solid.
[Rooted entity API](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/root/create_entity/index.html),
[official project example](https://docs.ifcopenshell.org/ifcopenshell-python/code_examples.html)

For wall-like bodies, the documented local axis is +X, with thickness along Y;
placement determines world position and orientation. IFC coordinates use project
units, while high-level geometry APIs may accept SI values. Verify each API's
unit contract rather than assuming one convention covers all attributes.
[Geometry and units](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)

Openings and their infill have explicit relationships: use `feature.add_feature`
for the opening-to-host association and `feature.add_filling` for the door/window
occupying it. A door-shaped mesh placed on a wall does not establish either
relationship. [Opening relationship](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/feature/add_feature/index.html),
[filling relationship](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/feature/add_filling/index.html)

Read-only introspection confirmed these installed 0.8.5 callable shapes:

```text
project.create_file(version='IFC4')
root.create_entity(file, ifc_class=..., predefined_type=None, name=None)
geometry.add_wall_representation(file, context, length, height, ..., thickness)
geometry.edit_object_placement(file, product, matrix=None, is_si=True,
                               should_transform_children=False)
feature.add_feature(file, feature, element)
feature.add_filling(file, opening, element)
validate.validate(file_or_path, logger, express_rules=False)
```

This confirms availability and signatures, not a completed architecture smoke.

Keep four independent result fields:

| Check family | Evidence it can provide | Evidence it cannot provide by itself |
| --- | --- | --- |
| IFC schema/EXPRESS | Attributes, entity types and executed schema rules | Correct constructed geometry, local permission to build |
| IDS | Required entity/property/material/classification information for specified applicable objects | Independent measurement of a claimed property, universal geometry or legal compliance |
| Geometry/coordination | Measured clearances, intersections, enclosure, dimensions for named geometry and tolerances | Applicability or legal authority of the numerical threshold |
| Jurisdiction rule pack | Result of an implemented, applicable, versioned rule with supplied evidence | Unimplemented rules, missing evidence or authority approval |

IfcOpenShell exposes schema validation with optional EXPRESS rules; its CLI uses
`--rules` to enable the latter. IfcTester authors/reads IDS, audits IFC and reports
results. The buildingSMART IDS manual defines applicability and requirements
using information facets. **Design consequence:** an IDS pass means the declared
information specification passed, not that the building complies with every
applicable regulation. [Schema validation](https://docs.ifcopenshell.org/autoapi/ifcopenshell/validate/index.html),
[IfcTester](https://docs.ifcopenshell.org/ifctester.html),
[buildingSMART IDS manual](https://github.com/buildingSMART/IDS/blob/development/Documentation/UserManual/README.md)

### Existing TEE reuse and a measured unit defect

Reuse candidates found in the checkout: `server/src/tee/extract/ifc.py` already
authors walls and storeys; `pointcloud/` already handles scan preparation and
scale controls; `capture/align.py` owns registration; `adapters/blender/homebuilder.py`
owns the existing Blender/Home Builder cabinetry bridge. Reuse their contracts,
but verify their assumptions before making them the new kernel.

**Measured acceptance debt, not fixed in the frozen A81 payload:** an owned
temporary fixture passed a storey elevation of **3.0 m** to the existing
`export_ifc`. Reopening its IFC with installed 0.8.5 gave:

```text
project length scale to metres: 0.001
IfcBuildingStorey.Elevation:    3.0 project units = 0.003 m
wall world placement Z:        3000.0 project units = 3.0 m
```

The writer uses millimetre project units but assigns the elevation attribute
directly from a metre-valued input. This is a concrete first-slice regression:
semantic elevations and geometric placements must agree after serialization.
No user IFC/design was edited; the temporary test was removed automatically.

## Unreal, mesh and LiDAR import boundaries

Epic's documentation inspected is labelled **Unreal Engine 5.8**. It describes
Python as an Editor facility, unavailable in a packaged game/runtime. It also
documents a headless Python commandlet (`-run=pythonscript -script=...`), which
requires the project plugin and does not automatically load a level. Thus an
Unreal import bridge can run an Editor automation process without its UI, but
it is still an Unreal Editor dependency. Actual installed project/version and
exporter behavior must be probed before a live-support claim.
[Epic Python execution modes](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python)

Epic lists FBX and OBJ among Static Mesh asset exports. Asset export operates on
the selected object/exporter; it is not a promise that every world actor,
procedural mesh, landscape, instanced component or cooked asset exports with
identical semantics. **Recommended bridge contract:** export selected supported
meshes plus a sidecar containing source asset/actor IDs, transforms, instance
identity, units, axis convention and exporter/version. Refuse unsupported object
classes explicitly and keep the source untouched.
[Asset export formats](https://dev.epicgames.com/documentation/en-us/unreal-engine/working-with-assets-in-unreal-engine),
[export-task operation](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Miscellaneous/RunAssetExportTask?lang=en-US)

Epic's LiDAR plugin imports XYZ/PTS/TXT, LAS/LAZ and E57. Its documented export
surface is ASCII or LAS, with metre-to-centimetre conversion on import and the
reverse on export unless the project changes scale settings. Its displayed point
budget controls a view, not an accuracy certificate. Prefer the original scan
file for geometric work when available; if importing from Unreal, record its
actual scale settings and exported coordinates. [LiDAR formats and scaling](https://dev.epicgames.com/documentation/unreal-engine/lidar-point-cloud-plugin-overview-in-unreal-engine)

**Design inference:** neither triangles nor point coordinates inherently supply
wall construction, concealed layers, room use, fire rating, load-bearing status
or planning permission. Import them as reference evidence first. Propose fitted
planes, boundaries and candidate BIM elements with visible uncertainty; promote
them to authored elements through a recorded decision. Do not convert every
vertical mesh into a wall or fill occluded openings with invented certainty.

For every fitted element retain source hashes, source coordinate reference,
transform chain, original versus inferred status, method/version, contributing
region, residual distribution, coverage, tolerance and approval/revision links.
Keep registration error, sampling error and representation error distinct.
USIBD's current LOA page identifies **version 3.1** and stresses specifying
tolerances and their statistical interpretation; the full specification was not
obtained, so no LOA class or numerical compliance threshold is asserted here.
W3C PROV supplies an established entity/activity/agent and derivation model for
the provenance graph. [USIBD LOA](https://usibd.org/level-of-accuracy/),
[W3C PROV-O, Recommendation 30 April 2013](https://www.w3.org/TR/prov-o/)

## Worldwide coverage through explicit rule packs

Worldwide support should mean one extensible applicability and evidence engine,
with visible coverage for any project location. It must not mean that a single
international code is presented as binding everywhere.

Two primary-source examples establish why the distinction is necessary: ICC
describes adoption by a jurisdiction's law and incorporation of local amendments;
the European Commission JRC describes country-specific Nationally Determined
Parameters and National Annexes for Eurocode use. These sources justify a
versioned applicability mechanism, not a claim to have encoded either body of
requirements completely. [ICC adoption resources](https://www.iccsafe.org/advocacy/code-adoption-resources/),
[JRC Nationally Determined Parameters](https://eurocodes.jrc.ec.europa.eu/en-eurocodes-implementation/nationally-determined-parameters)

Recommended pack contract:

- Identity: pack ID/version/hash, issuing authority, country and subordinate
  jurisdiction coverage, language, source URL/document hash, edition and clause.
- Applicability: effective and superseded dates; adoption instrument; occupancy,
  use, building class/height, new work versus alteration, and applicable overlays.
- Dependencies: exact parent edition, national parameters, local amendments and
  referenced standards. Conflicting precedence is `not_verified` until resolved.
- Rule: supported deterministic operation, required model evidence and units,
  explicit tolerances and exceptions; no arbitrary downloaded executable code.
- Assurance: human-reviewed interpretation, positive/negative/boundary fixtures,
  evidence provenance, limitations, last source verification and change history.
- Rights: record access/redistribution conditions; do not bundle purchased or
  restricted standards merely because their title or online viewer is public.

For each rule use `pass`, `fail`, `not_applicable` or `not_verified`, with the
reason, evaluated inputs and evidence links. Missing rule pack, unknown location,
unknown adoption date, missing authoritative text, unimplemented rule, missing
measurement or unresolved exception must produce **`not_verified`**, not a pass.
The global result cannot be "compliant" while required scope remains unknown.
Show implemented coverage separately from the number of rules that passed.

Country/region indexes can be introduced worldwide immediately; an empty index
entry is explicitly unsupported coverage. Add verified packs independently over
time, pin each assessment to exact source/rule versions, and preserve old results
for reproducibility. Do not learn or silently update legal thresholds from user
feedback or generated prose. Learning may help rank modelling strategies, while
rule changes go through source verification and review.

## First slice that can be proved

Implement a small, original one-storey model with two enclosed rooms, a slab,
four perimeter walls plus a partition, hosted door/window openings, a simple
roof and one parameterized cabinet. The cabinet core owns panel dimensions,
material thickness, grain direction, edge treatment and an explicit hardware
schedule; IFC initially receives the furnishing occurrence/type. Detailed
fabrication output should reuse or hand off to the existing joinery/part lane
after its mapping is verified. No proprietary manufacturer geometry is needed.

Acceptance should establish:

1. Create, save, reopen, edit a wall/opening, undo and replay while preserving
   stable model IDs/IFC GUIDs; dependent dimensions, quantities and views update.
2. Compare reopened IFC storey elevations, placements, host/fill relationships,
   room areas and cabinet sizes against independently computed fixture values.
   Include the measured metre/millimetre defect above as a failing control.
3. Report schema/EXPRESS, a small explicitly authored IDS, geometry checks and
   rule-pack applicability as separate outcomes. Use a clearly labelled test
   pack to prove worldwide selection/unknown behavior; never call it a law pack.
4. Import a deliberately incomplete scan/mesh of that same fixture, recover the
   known coordinate transform and measured surfaces, and leave occluded facts
   unknown. Verify both an acceptable fit and rejected ambiguous/degenerate fits.
5. Produce IFC, compact schedules and 2D drawings from the same model. An optional
   GUI edits it through the same command API. Opening an external viewer is a
   separate opt-in handoff and never a prerequisite for headless operations.

Live Unreal export and a second application's IFC round trip are later explicit
acceptance rows, each naming the actual product version and observed limits.
This foundation supports the requested worldwide scope while retaining honest,
testable boundaries for geometry, inference, documentation and regulation.

## P2 implementation and measured exchange evidence — 2026-09-11

The preceding foundation proposal is now followed by a measured implementation
in `tee.architecture.exchange` and `tee.architecture.drawings`. The original
pre-build observations remain historical evidence, not the current release
status. No dependency was installed or changed for P2. IFC operations lazily
import the existing IfcOpenShell 0.8.5; GLB uses the existing Trimesh, DXF uses
ezdxf, and the PDF review set uses fpdf2.

The owned full workflow is reproducible through
[`benchmarks/run_a82_architecture_smoke.py`](../../benchmarks/run_a82_architecture_smoke.py).
Its completed run at `20260910T231204Z` recorded **1.443 seconds**, with no model,
paid inference or DCC calls. The smoke creates the compact house, edits its
cabinet width, undoes that edit, reopens revision 3 with the original entities
and document identity, exports it, and separately proposes/promotes an owned
reference scan. This is a local measurement, not a cross-machine performance
promise. [Full smoke evidence](../../output/architecture/house-example/20260910T231204Z/evidence.json)
(SHA-256 `4deb6bc7ea061c6849617fc82024f6a5a045584fc3424296c6d43758b91aed62`).

A separate read-only review reopened those already-written IFC, GLB, DXF and PDF
artifacts and checked all 27 drawing-artifact hashes against their manifest:

| Measured item | Result |
| --- | --- |
| IFC project length scale | 0.001 metres per unit: explicit millimetres |
| House semantic contents | Five walls, two spaces, four hosted openings and four filling relationships, one slab, one flat roof, one cabinet |
| Joined wall material volume | **22.846 m³** after actual opening subtraction; south 5.160, east 4.160, north 5.600, west 3.936, partition 3.990 m³ |
| Wall junctions | Four L plus two T junctions; zero wall-wall material overlap in the bounded authoring check |
| Cabinet | Nine actual finished panel envelopes; IFC volume **0.062211888 m³**, not a solid cabinet-sized box |
| Drawing delivery | 12 SVG views, 12 millimetre DXFs, two CSV schedules, one 12-page PDF; drawing manifest is the 28th file |
| GLB | 28 semantic geometry nodes, in metres; reopened bounds approximately `[-0.3,-0.3,-0.15]` to `[10.3,8.3,3.0]` m, with ordinary glTF floating-point rounding |
| Information/regulatory assurance | Schema/EXPRESS passed; represented geometry measured; no IDS supplied and regulatory coverage remains `not_verified` |

The 12 views are one plan, one vertical section, one wire elevation and nine
cabinet cut-blank sheets. They carry the document revision; DXF dimensions are
real dimension entities in model millimetres, with revision metadata. The CSV
cutlist separates blank dimensions from finished dimensions, grain, material and
edge-band allowances. The PDF for this fixture required zero font substitutions.
These are review drawings; they do not assert a local authority's sheet standard.

### Explicit wall joining, retained authoring coordinates

`project.facts.wall_join_policy="orthogonal_butt_v1"` is the explicit opt-in.
Absence preserves unjoined authored wall prisms and reports their overlaps.
V1 joins orthogonal L/T centreline junctions only where the wall base and top
levels agree. At an L, the lexicographically lower stable wall ID is the through
wall: extend its end by half the other wall thickness, and trim the abutting wall
by half the through-wall thickness. At a T, the continuous wall is through,
regardless of ID. Source centrelines, IDs and hosted opening offsets do not move;
the same derived body ranges feed IFC, preview, GLB and drawing cuts.

This extension matters: merely subtracting overlapping original wall boxes
removes duplicate volume but leaves the outer quarter of an L corner missing.
The verified butt construction closes that corner. Independent IFC tests with
unequal wall thicknesses measured **5.10 m³ for L** and **5.01 m³ for T**, unchanged
when rotated 37 degrees. Other controls verify real wall/window/door subtraction,
a concave L slab rather than its bounding box, and the finished panel volume of a
separate 600 mm cabinet fixture. Deleting a real IFC void relationship increases
the independently measured wall volume, proving the check is not reading only a
claimed quantity property.

Nonorthogonal, X, multiway, parallel-overlap and unequal-height junctions refuse;
so do consumed wall lengths, openings in a trim or junction, and remaining
derived wall overlap. The overlap check is bounded at 100,000 part pairs and
reports up to 50 overlap details; the join report returns up to 128 details with
the full count. It checks wall-wall material after openings. It does not establish
all-class clash freedom, structural adequacy, concealed construction or net
material quantities obtained by adding rooms, walls, slabs and furnishings.

### Federation identity and the corrected unit boundary

Each native document now has a persistent canonical UUID `document_id`, created
once and retained through edits, renaming, undo, save and reopen. Missing or
inconsistent saved identity refuses. IFC GUIDs derive from that document's UUID
namespace and the semantic entity identity. Project/site/building GUIDs also use
stable names within that namespace, rather than the project's editable display
name. Tests prove that separate documents both containing ordinary IDs such as
`level` and `alpha` have disjoint IFC identities, while renaming one project
preserves its project/site/building/storey/wall GUIDs.

The earlier existing-exporter elevation defect is now fixed narrowly in
`tee.extract.ifc`: convert the metre-valued `elevation_z` through the actual IFC
project-unit scale before assigning `IfcBuildingStorey.Elevation`. A real reopen
regression confirms that a **3.0 m** source level becomes an attribute of
**3000 mm**, matching the wall's **3000 mm** world Z placement. New architecture
geometry and placements are explicitly authored in mm throughout.

### What real dependency execution taught

Keep the `shape` returned by `ifcopenshell.geom.create_shape` alive while reading
its SWIG-owned geometry buffers. The initial full-smoke harness used a temporary
owner through `create_shape(...).geometry`, producing invalid volume readings.
Holding `shape` in a variable repaired the harness; the production validator
already retained it. The corrected independent house measurement is 22.846 m³.

IfcOpenShell 0.8.5's EXPRESS executor also reads its generated rule source through
an unclosed `open(...).read()` at `express/rule_executor.py:95`. Strict warning
checks exposed this dependency warning. The validator captures only that
module's `ResourceWarning` locally and reports it under `dependency_warnings`;
it still executes EXPRESS rules, serializes the checker while its global IFC
setting is changed, restores that setting, and preserves other warning policies.
No installed dependency file was patched. The focused exchange/drawing suite
finished **23 passed with `-W error` in 6.90 s**, with Ruff clean.

Door/window fillings currently preserve hosted IFC semantics and nominal opening
dimensions but intentionally omit leaf/frame/glazing construction geometry, whose
thicknesses and assembly details were not supplied. Flat roofs are explicitly
flat. Cabinet panels use finished envelopes, with separate cut-blank schedules;
edge bands are not separate material solids, and hardware, machining, strength
and CNC readiness remain unverified. Sections/plans are actual mesh-plane cuts;
the elevation is explicitly a wire projection without hidden-line removal.
World-wide rule selection remains a coverage framework, not a library of all
verified legislation. Actual live Unreal export, a second vendor application's
IFC acceptance, and the two actual recipient-client upgrade receipts require
separate evidence.

### Final review annotations and commit-time geometry gate

The later full smoke at `20260910T232517Z` passed in **1.460 seconds** after the
annotation pass and the commit-time join-policy validation landed. It retains
the same independently measured **22.846 m³** of joined wall material and zero
wall-wall overlap. [Final smoke evidence](../../output/architecture/house-example/20260910T232517Z/evidence.json)
has SHA-256 `99ed8347d456ec7b36f6c03dcb9f2a7a048ad63bf3361a13cfe5e2824004a135`.

Plans now share one bounded annotation record across SVG, DXF and PDF. Each
record carries the entity ID, document revision, text, paper-space bounds and
any leader. Room labels show the authored name and true polygon area; the house
has **45.24 m²** and **29.64 m²** rooms. Four opening labels state width and height,
and both windows state their **900 mm** sill. The cabinet callout states its
**900 × 600 × 900 mm** envelope. These are authored opening dimensions, without
invented frame details or door swings. The cabinet is below this plan's 1400 mm
cut plane, so its callout identifies its location without adding a false cut.

Room placement checks the entire text rectangle against the actual polygon by
triangle/rectangle intersection area, including concave rooms whose bounding-box
centre or polygon centroid can lie outside. Opening and cabinet labels search
bounded offset positions with leaders. Labels avoid drawing segments, previous
labels and leaders, and the overall-dimension regions. An overcrowded view,
overlong label or more than 80 annotations refuses explicitly before drawing
files are written; labels are never silently omitted. This bounded placement is
not an optimal layout solver. The same-revision tests include a U-shaped room,
cross-format text/metadata controls and a refusal that leaves no output folder.

An independent read reopened the final files, checked all **27 artifact hashes**,
all seven labels in SVG/DXF/PDF, exact SVG annotation metadata, DXF millimetres
and the 12-page PDF. Both the implementation agent and coordinator inspected the
rendered plan: labels and leaders are readable and separated, the room names
lie inside their polygons, and the overall dimensions and review-set note remain
legible. [Drawing review evidence](../../output/architecture/house-example/20260910T232517Z/drawing-review.json)
and [rendered plan](../../output/architecture/house-example/20260910T232517Z/annotated-plan.png)
retain that inspection. The focused exchange/drawing suite then passed **27 tests
with `-W error` in 7.42 s**; Ruff is clean. These facts supersede the earlier
23-test count while preserving its measurement chronology.

The selected wall policy is now a core model invariant: unsupported joins refuse
during create/edit/reopen validation, before an atomic command can commit. In
particular, changing one wall's height in the joined house can no longer create
a revision that passes model checking but later fails export. Regression checks
assert that rejected changes preserve both the prior revision and complete
document state. `ak_check` reports the named join and bounded wall-overlap checks
while retaining overall geometry status `not_verified`: room enclosure,
other-element clashes, structural/service design and approval remain outside
those checks.
