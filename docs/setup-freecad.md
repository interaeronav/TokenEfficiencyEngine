# FreeCAD setup — the fabrication lane (A37)

TEE drives FreeCAD 1.1+ through **one bridge**: the
`neka-nat/freecad-mcp` RPC addon running inside the FreeCAD GUI process
(the P0 probe's decision — page SVG/PDF export is GUI-bound upstream,
[#5710], so the GUI process must exist anyway; TEE ships no second
bridge). `freecadcmd` remains the headless vehicle for CI and plain
DXF/STEP work.

## Install (once)

1. **FreeCAD 1.1.3+** (1.1.3 carries security fixes for malicious
   FCStd files). The headless binary moved in 1.1.x to
   `FreeCAD.app/Contents/Resources/bin/freecadcmd`.
2. **The RPC addon**: copy `addon/FreeCADMCP` from
   `github.com/neka-nat/freecad-mcp` (MIT) into
   `~/Library/Application Support/FreeCAD/v1-1/Mod/`, restart FreeCAD,
   pick the **MCP Addon** workbench → **Start RPC Server** (or check
   its **Auto-Start Server** setting). The server listens on
   `127.0.0.1:9875`.

## Serve

```bash
tee serve --adapter freecad
```

The adapter works one document (default `TEE`). Everything kernel-side
comes free: `tee_batch` (auto-checkpointed via document save-copies),
`tee_scene_summary`, `tee_diff`, `tee_rollback`, budgeted
`tee_capture`. **Units are millimetres end to end.**

## The typed ops

- Primitives: `{"op": "create", "kind": "box|cylinder|sphere|cone",
  "name": ..., "props": {"Length": 600, "Width": 400, "Height": 18,
  "at": [x, y, z]}}` — props are FreeCAD property names.
- **Sketches are solved before FreeCAD sees them**: `kind: "sketch"`
  takes the `sketch_solve` contract (points as guesses, lines,
  constraints — distance/horizontal/vertical/angle/parallel/…); py-slvs
  closes the geometry server-side and the script places FINAL
  coordinates. Convergence is never FreeCAD's problem.
- Solids: `kind: "pad"` (`{"sketch": id, "length": mm}`) and
  `kind: "pocket"` (`{"sketch": id, "target": id, "depth": mm}`) —
  Part-workbench objects (Extrusion/Cut): the stabler scripting
  surface. Not PartDesign bodies (v1 limitation, recorded); the
  in-FreeCAD sketch carries solved geometry without re-declared
  constraints — parametric truth lives in TEE's op history and the
  feature properties (pad length, pocket depth stay editable).
- Any other `kind` word creates a generic metadata object
  (FeaturePython with dynamic properties).

## Drawings and exports (virtual tools)

- `fc_drawing {objects, views: ["front","top","iso"...], dimensions,
  formats: ["svg","pdf","dxf"], name, out_dir}` — a TechDraw sheet
  derived FROM the model. Dimensions: `{"type": "ExtentX"|"ExtentY"}`
  (overall size, no edge refs) or
  `{"type": "DistanceX", "refs": ["Edge0"]}`. **Every dimension's
  value is read back from the document** — the sheet's numbers are the
  model's numbers by construction, asserted from data. (Implementation
  note the hard way: a dimension created in the same GUI dispatch as
  its view caches 0.0; the read-back is a second dispatch that touches
  and recomputes — handled inside the tool, pinned by test.)
- `fc_export {objects, format: "step"|"glb", path, into?}` — STEP for
  fabricators; a GLB lands in a served scene lane with `into=<lane|auto>`
  (one checkpointed `import_file` batch, read-back verdict — A68), or
  feeds `as_ingest` → `as_import` for the asset library with scale bands.
  A STEP with `into=` is refused (`handoff_import_unsupported`): no scene
  lane imports it — export the GLB.

## The recorded acceptance (2026-08-29)

A wardrobe side panel (600 × 400 × 18 mm, 100 × 60 × 5 mm hardware
slot) went brief → solved sketches → pad/pocket (volume exactly
4,290,000 mm³) → dimensioned sheet (SVG+PDF+DXF; document read-back
[600.0, 400.0, 18.0]) → STEP + GLB → live Unreal import
(`scale_band: accept`, read-back [0.6, 0.4, 0.018] m, verify ok) in
one session, batches 0.02–0.10 s each.
