# 52 — Fabrication drawings, CAD, joinery and presentation lanes (2026-08-28)

Verification basis: live `kb_search` through the installed TEE server
this session (the joinery grounding below); open-web research
2026-08-28 (sources inline); the owner's stated pains verbatim; repo
reads (physical module, extract/IFC, as_import, the Blender adapter).
Owner's suggested starting list dispositioned item by item at the end.

## The pains (owner, 2026-08-28)

1. Producing **usable technical documents and 3D drawings** — accurate,
   fabrication-ready blueprints and 3D diagrams that also feed Unreal.
   Past AI output "not suitable."
2. **Joinery for closets and wardrobes** specifically.
3. **Modern, eye-popping presentations** for simulator preparations.
4. **Autodesk Fusion trial expiring** — wants a headless CAD embedded
   in TEE "just like Blender," with the core features.

## Root cause worth naming (why past output was "not suitable")

Mesh-first tools generate *shapes*; fabrication needs *dimensional
truth* — parametric models whose drawings are DERIVED (projected,
dimensioned, toleranced) rather than drawn. The KB itself states the
discipline (`blender.modelling`: "what makes it CAD-accurate is not in
the mesh tools — it is in typing [dimensions]"). The fix is a
CAD-first lane with checks, which is TEE dogma applied to fabrication:
model → derived drawings → rule-checked → exported, never "draw me a
blueprint" as pixels.

## Pain 4 first, because it is URGENT and it unlocks pain 1

**FreeCAD 1.1 (released 2026-03) is the Fusion replacement**, and it is
adapter-shaped exactly like Blender: LGPL, free for commercial use, a
full parametric modeler (constraint Sketcher, Assembly, BIM, FEM,
TechDraw drawings, 50+ formats incl. STEP/DXF/glTF), a Python API over
everything, and a real headless mode (`FreeCADCmd`) suited to
embedding. Honest gaps vs Fusion — integrated CAM polish, generative
design, Autodesk-cloud collaboration — none of which appear in the
owner's needs. One build-time caveat to verify, not assume: headless
TechDraw page export has documented rough edges (upstream issue
#5710) — the adapter's drawing lane must prove SVG/PDF export in
`FreeCADCmd` on day one, with the GUI-process fallback (Blender-bridge
style) as the recorded plan B.

**Time-critical, outside TEE: export every Fusion design NOW, before
the trial lapses** — STEP (geometry, opens everywhere incl. FreeCAD)
plus F3D archives (full parametric history, Autodesk-only but kept
against a future need). After expiry, exports may be locked behind
read-only limits.

## Pain 1 — the fabrication lane (A37 headline if directed)

A FreeCAD adapter in the Blender adapter's image: bridge or
FreeCADCmd process, typed batch ops (sketch → constraint → pad/pocket
→ assembly), TechDraw pages generated from the model (projections,
dimensions, title block), STEP/DXF out for fabricators, glTF/STEP →
the existing `as_import` path into Unreal (scale-banded, read-back
verified — already shipped). TEE's physical module supplies the
checking culture (watertight ops, plaus_check pattern, py-slvs
sketch_solve already in-tree). Every drawing carries the model's
dimensions by construction — the "not suitable" failure mode is
structurally closed.

## Pain 2 — the joinery lane (closets and wardrobes)

Three pieces, all verified to exist:

- **The knowledge**: live `kb_search` this session hit a full
  `06_joinery_and_woodwork` domain — `joinery.cabinetmaking` ("the
  32 mm system: hole spacing, 37 mm setback, fixed carcass heights",
  confidence high), `joinery.hardware` ("hardware determines carcass
  dimensions, not the other way round"), `joinery.joints` (load-path
  ordered joint catalogue), plus `furnishing.storage` (wardrobe
  systems). 95 files matched. The knowledge was never the gap.
- **The tool**: **Home Builder 5.1** — open-source Blender add-on,
  rebuilt for Blender 5+ (matches the installed 5.2), closets and
  cabinets with parametric prompts, dimensioned 2D plan/elevation
  layouts, geometry-nodes **cut-part reporting** and CNC-oriented
  export. Runs inside Blender ⇒ **TEE's existing adapter drives it
  today** — no new adapter needed, only a lane: batch ops over HB's
  operators/prompts, layout/cut-list export wired into tee_media/
  extract.
- **The check**: a `joinery_check` rule table in the plaus_check
  pattern — 32 mm system conformance, hinge-boring geometry, setbacks,
  carcass-vs-hardware consistency — each rule lifted from the KB and
  re-verified at its cited source per A30 before it judges anything.

## Pain 3 — presentations, scoped honestly

Split the need: **technical boards** (diagram sheets, annotated
renders, part-in-context 3D views) are TEE's kind of work — the
Blender document-render pipeline already proven on the owner's house
project becomes a small "board" lane (templated, styled, budgeted).
**Slide decks** ("eye-popping") are a host-side job — the host's
deck/artifact tooling does polish better than an MCP server should
try to; TEE's contribution is supplying the boards, renders and facts
those decks embed. One aviation-specific gem from the owner's NASA
pointer: **OpenVSP** (NASA open source) generates parametric aircraft
geometry — a credible source of accurate airframe visuals for
sim-prep boards; worth a look when that lane is built, not a
dependency.

## The owner's research list, dispositioned

- **FreeCAD** — ADOPT: the Fusion replacement and the A37 adapter.
- **Home Builder 5.1** — ADOPT via the existing Blender adapter.
- **LibreCAD** — SKIP: 2D DXF drafting only; TechDraw covers it from
  the real model.
- **OpenFOAM** — PARK: industrial CFD; heavy, specialist, no current
  need named; TEE's sim_fluid already covers visual fluids. Revisit
  only for a real airflow-engineering task.
- **code.nasa.gov** — BROWSE-ON-NEED; OpenVSP flagged above as the
  relevant find for a pilot.
- **QGIS.org** — research 51's verdict stands: front the existing
  QGIS MCP through the A36 gateway; no first-party adapter.

## Recommendation

One campaign (A37 if directed), after A35/A36 or jumped ahead if
fabrication is time-critical — the scripts are independent: **the
fabrication lane** = FreeCAD adapter + Home Builder joinery lane +
`joinery_check` + the board lane, benchmarked like everything else
(tokens per completed drawing set; a closet goes brief → checked
model → cut list + dimensioned elevations + UE import in one
session). Urgent regardless of any decision: the Fusion STEP/F3D
export, this week.

Sources: FreeCAD 1.1 release and headless docs
(neowin.net/amp/freecad-110, reqrefusion.github.io Headless_FreeCAD,
github.com/FreeCAD/FreeCAD/issues/5710, en.wikipedia.org/wiki/FreeCAD),
Fusion comparisons 2026 (freecad-app.com/blog/freecad-vs-fusion-360,
gaugehow.com/cad/fusion-360-vs-freecad, in3dtec.com), Home Builder 5
(extensions.blender.org/add-ons/home-builder-5, creativedesigner3d.com,
creativedesigner3d.github.io/home_builder_docs,
hackster.io "Home Builder 5.1 Is Open Source Software for DIY Cabinet
Projects", github.com/CreativeDesigner3D/home_builder_5).
