# CLAUDE_A70_SCRIPT.md — the Fusion lane v2: holes, chamfers, revolves, constraints, joints, exports, drawings

**Owner directive (2026-09-06, verbatim):** *"v2 should add holes, chamfers,
revolves, sketch constraints, joints, drawings or the iges/sat/3mf/usd
exports, each of which is one more verified row and one more emitter."*
Research doc 71 stays the design of record (§3 rows 31–49 and §10 are v2);
this is the plan of record. Written for a cold session.

## Orientation

- Repo root `TokenEfficiencyEngine/`, code in `server/`; branch
  `claude/tee-component-integration-iflsyq` (PR #1, which already carries
  A68 and A69 — the owner directed v2 while it was open, so pushes stay on
  the designated branch). Read `docs/PROGRESS.md` first; real output into it
  per phase; one commit per phase.
- Suite: `cd server && UV_FROZEN=1 uv run pytest -q` (addopts exclude
  dcc/ml/network/llm), `UV_FROZEN=1 make lint`. Surface invariant: **17
  always-loaded tools**, zero wire delta from this lane.
- The lane: `server/src/tee/adapters/fusion/{codegen,adapter,tools,wire}.py`;
  the add-in `adapters/fusion/tee_bridge/TEE/`; the shim
  `server/tests/fixtures_fusion.py` `exec`s every generated script. **Fusion
  has no Linux build and none is on this machine**: nothing is claimed live
  until the Mac smoke (`docs/fusion-lane.md`) has run, and v2 adds steps to
  it (below).
- A69's law holds: **nothing goes into the codegen that is not a
  reference-verified row in doc 71 §3.** Rows 31–49 were read on 2026-09-06
  from `autodeskfusion360.github.io/FusionAPIReference/…/files/`; a call
  that is not there gets its row first.

## Verified facts v2 builds on (doc 71 §3, rows 31–49)

1. Holes: `createSimpleInput(d)`, `createCounterboreInput(d, cbD, cbDepth)`,
   `createCountersinkInput(d, csD, csAngle)`; position by a planar face and a
   Point3D (projected along the normal) or by a sketch point; extent by
   `setDistanceExtent` (**not** retired for holes) or `setAllExtent`;
   `isDefaultDirection` is the flip.
2. Chamfers: `ChamferFeatures.createInput` is **retired**; `createInput2()`
   plus `chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, d, tangent)`.
3. Revolves: `createInput(profile, axis, op)` with a construction axis or a
   sketch line as the axis; `setAngleExtent(isSymmetric, angle)` is current.
4. Sketches: `addByTwoPoints`, `sketchPoints.add`, `originPoint`; the
   eleven `geometricConstraints.add*` calls (`addOffset` retired); four
   `sketchDimensions.add*` calls whose result has a settable
   `parameter.expression`; **`addTwoPointRectangle`'s line order is not
   stated** — sides are named by position.
5. Joints: `joints.createInput(g1, g2)` / `add`; geometry by planar-face
   centre (`createByPlanarFace(face, None, CenterKeyPoint)`) or by a point
   (`createByPoint`); seven `setAs*JointMotion` setters; `angle` / `offset`
   are ValueInputs (write the unit); `RevoluteJointMotion.rotationValue`
   (radians) and `SliderJointMotion.slideValue` (cm) drive a joint.
6. Faces: `surfaceType == PlaneSurfaceType`, the plane's `normal` flipped by
   `isParamReversed`, `centroid`, `edges`; `occ.bRepBodies` yields proxies.
7. Exports: iges / sat / usd take `(filename, geometry=None)` with a
   Component; 3mf takes `(geometry, filename)` with a body, occurrence or
   component; none of the four option objects has a unit property.
8. **Drawings: the API cannot create one.** `DocumentTypes` has only the
   design type, `Drawing` has no sheets or views; an open drawing can be
   exported to PDF. v2's drawings are partkiln's (`pk_import` + `pk_drawing`).

## Laws

Doc 71 §5 and §10.9, plus the inherited ones: measured before/after; Rule 6
refusals; zero new always-loaded tools; every `fu_*` tool tabled
individually; the owner's document is never created, saved, closed or
uploaded; a write-artifacts tool exercises write-scene only through
`registry.require`.

## P0 — rows, design, script, decisions (one commit)

Doc 71 §3 rows 31–49 and §10, §7 and §9 amended; this script; a DECISIONS
entry; the PROGRESS section opened; the `CLAUDE.md` bullet.

## P1 — addressable sketch geometry, constraints, dimensions (one commit)

- `codegen.py`: `lines` / `points` on `create sketch`; the `_subs` map and
  `_sub(sketch, address)` resolver in the prelude; rectangle sides and
  corners classified by midpoint / position after creation; `create
  constraint` and `create dimension` emitters (doc 71 §10.1) plus the inline
  `constraints` / `dims` lists; `dim` ids, kind `dimension`, `_kind_of`
  extended; `set` on a dimension (`expression`); `check_batch` for the new
  shapes (arity per type, address syntax) — refused before the wire.
- `fixtures_fusion.py`: real sketch lines / circles / points with shared
  SketchPoints, `geometricConstraints`, `sketchDimensions` with parameters
  that drive rectangles and circles (Law 10), `isFullyConstrained` where the
  arithmetic can say.
- *Acceptance:* `tests/test_fusion_v2.py` — a rectangle dimensioned by
  `width` / `height` user parameters extrudes to their values, a `param_set`
  re-sizes the body through the dimension, a constraint's arity error is a
  `bad_op` naming the shape, `sk1/r0.bottom` resolves across batches, the
  sketch row carries `constraints` / `constrained`, `test_lane_vocab.py`
  holds `vocab()` equal to the new `KINDS`.

## P2 — holes, chamfers, revolves, faces (one commit)

- Prelude: `_face(body, sel, at)` (doc 71 §10.2), `_edges_of(body, sel)`.
- Emitters: `create hole` (simple / counterbore / countersink; face + `at`
  or sketch `point`; depth or through; flip), `create chamfer` (edge sets;
  the `edges` selector, shared with fillet), `create revolve` (construction
  axis or sketch line; angle; symmetric). Hole summaries in mm.
- Shim: six-face boxes with normals / centroids / edges, hole subtraction,
  chamfers on the timeline only, Pappus revolves.
- *Acceptance:* a 120×80×10 plate with two Ø6.6 through holes reads back
  96,000 − 2·π·3.3²·10 mm³; a counterbore subtracts its ring; a chamfer on
  the `+z` face's edges takes four edges; a revolve of a 10×20 rect whose
  centroid sits 30 mm off the x axis reads 2π·200·30 mm³; the retired
  chamfer `createInput` never appears in a generated script; a face the
  body lacks refuses `fusion_no_face` naming the ones it has.

## P3 — joints (one commit)

- Emitter: `create joint` (doc 71 §10.5) with the seven motions and the
  two geometry forms; `j` ids, kind `joint`, summaries; `set` on a joint
  (`angle`, `offset`, `suppressed`, `flipped`, `rotation`, `slide`);
  joints in the listing and the timeline.
- Shim: `Joints`, `JointGeometry`, `JointInput`, `Joint` with motion
  objects and angle / offset parameters.
- *Acceptance:* two extruded components joined revolute about z read back a
  `j1` row with `between`, `set j1 rotation=45` reads 45 in the row, a
  slider's `slide` in mm round-trips through cm, a joint on a body without
  the named face refuses, rollback deletes the joint.

## P4 — exports and the drawings route (one commit)

- `codegen.EXPORT_FORMATS` gains iges / sat / usd (filename-first,
  component-only, refuse a body id) and 3mf (geometry-first);
  `fu_export` declares `units: null, declares_units: true` for them with a
  note; the shim's ExportManager gains the four constructors.
- `fu_drawing` (write-artifacts, tabled): STEP to the workdir → the served
  partkiln lane's `pk_import` → `pk_drawing`, with `registry.require` on
  the scene write; refuses `partkiln_not_served`.
- *Acceptance:* each format writes the right header through the right
  constructor and argument order; `of=b1` on iges refuses with the fix;
  `fu_drawing` on an app holding fusion + partkiln (FakeKernel) writes a
  sheet and reports partkiln's `agree`, and refuses on a fusion-only app.

## P5 — measure, record, push (one commit)

- `benchmarks/run_benchmarks.py::run_fusion_v2_scenario` on the shim: a
  bracket — a dimensioned sketch bound to user parameters, an extrude, two
  holes, a chamfer, a revolve boss, a joint to a second component — as one
  batch + diff + `fu_measure` against the script a model writes itself and
  the listing it reads back; a RESULTS section.
- Docs: `docs/fusion-lane.md` (the new ops table rows, faces by direction,
  dimensions and parameters, joints, the four exports, `fu_drawing`, smoke
  steps 7–11), troubleshooting rows, README / quickstart mentions,
  CHANGELOG Unreleased, PROGRESS with the numbers, doc 71 §8.
- The Mac smoke gains (numbering continues `docs/fusion-lane.md`):
  7. a rectangle dimensioned to `width` / `height` user parameters; change
     `width`; `fu_measure` follows; record whether `addTwoPointRectangle`
     added constraints of its own (§9 item 7);
  8. one through hole on `+z`; `fu_measure` drops by π·r²·10 — and if it does
     not, `flip` is the answer to §9 item 4; a counterbore;
  9. a chamfer on the `+z` edges; a revolve about `x`;
  10. two components and a revolute joint; note which one moved (§9 item 5);
      `set j1 rotation=45`;
  11. `fu_export` iges, sat, 3mf, usd — open each and record its declared
      unit (§9 item 6); `fu_drawing` with a partkiln lane served.

## Verification

```
cd server
UV_FROZEN=1 uv run pytest -q tests/test_fusion_v2.py tests/test_fusion_adapter.py \
  tests/test_fusion_tools.py tests/test_lane_vocab.py tests/test_lanes_table.py \
  tests/test_lane_routing.py tests/test_trust_kernel.py tests/test_server_lint.py
UV_FROZEN=1 uv run pytest -q
UV_FROZEN=1 make lint
cd ../benchmarks && UV_FROZEN=1 uv run --project ../server python -c \
  "from run_benchmarks import run_fusion_v2_scenario as r; print(r())"
```
