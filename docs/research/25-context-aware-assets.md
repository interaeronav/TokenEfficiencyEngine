# 25 — Context-aware asset skill design (2026-08-22)

Design recommendations R1-R24 with cited dimension/clearance sources
(IRC, ADA, NKBA, Neufert, Panero & Zelnik, Merrell SIGGRAPH 2011). The
full envelope/clearance tables ship in the skill's reference files, not
here.

## Auto-scale & fit (R1-R4)

measured_size = format units (glTF=m normative; FBX UnitScaleFactor/cm;
USD metersPerUnit default 0.01; OBJ/STL unknown) × composed node scale ×
bbox. **Four-band envelope policy** per semantic class: accept in-envelope
/ silent power-of-ten-or-inch correction (recorded as a fact) /
snap-to-catalogue within ±10% (1.95 m door → 1.981) / reject >35% off
with a one-line reason. Uniform scaling only by default; per-asset
`stretch_axes` metadata is the sole gate for non-uniform; forbidden
outright for doors, windows, appliances, sanitary ware, seating, humans,
plants; flag negative-determinant (mirror) transforms — they invert
normals. Prefer glTF-sourced assets (normative units).

## Style (R5-R9)

Palette: k-means in CIELAB (k=6) + named colors — the NAME LIST is the
token-cheap form that enters context; numeric Lab swatches stay
server-side. `style_brief` structured fact auto-derived: palette from
site photos, style terms/materials from the caption pass, avoid-list from
the audio brief; user-overridable. Ranking: tags first (~80% of the job,
zero model cost), ΔE00 palette distance second, thumbnail embeddings
third — computed at INDEX time, cached by thumbnail hash, zero query
tokens; NumPy dot product suffices at library scale. Embedder: **SigLIP 2
base (Apache-2.0)** preferred, CLIP ViT-B/32 (MIT) fallback;
**MobileCLIP/2 weights are apple-amlr research-only — banned** (the MIT
repo license is a trap). Model sees ≤5-row shortlists, never full tables.

## Placement (R10-R14)

Model emits a RELATIONAL placement plan (asset → anchor type +
wall-segment id + offset + rotation + relations; ~10 tokens/object);
server solves and validates — never model-emitted raw transforms.
Merrell-2011 cost terms implemented as HARD VALIDATORS v1: clearance
polygons, circulation path (shapely erosion corridor ≥760/914 mm between
doors), door-swing keep-outs, back-to-wall, pairwise relations
(sofa-faces-TV, nightstand-touches-bed). Rules consume PLAN FACTS (the
conformance system stays authoritative). Machine-readable rule table with
`code` vs `guideline` severity — the model may relax guideline rows with
a note, never code rows. Region-parameterized (US IRC/NKBA vs EU Neufert)
from the GPS datum. Infinigen Indoors (BSD) is the legal reference
implementation for a later stochastic auto-layout. Learned placement
models (ATISS, 3D-FRONT/FUTURE-trained) are NC — never shipped.

## Lighting (R15-R17)

Sun az/el computed server-side: astral (Apache-2.0) default, pvlib SPA
(BSD-3) precision mode; **pysolar is GPL — excluded**; timezone via
zoneinfo + timezonefinder (MIT) from the GPS datum (tz bugs = sun on the
wrong side of the house). Drive Blender sun/Nishita sky and UE
directional light directly through the adapters — no add-on dependency.
HDRI: Poly Haven keyless CC0 API by sun-elevation band + weather; detect
each HDRI's in-image sun azimuth ONCE (brightest-pixel) and cache as a
fact; world rotation = computed azimuth − HDRI sun azimuth. Physical sky
= solar accuracy default; HDRI = mood.

## Skill packaging (R18-R21)

Agent Skills standard: six spec-portable frontmatter fields; SKILL.md
<500 lines; three-level progressive disclosure; reference files one level
deep with TOCs; scripts are EXECUTED, not read. Shape:
`context-aware-assets/` with reference/{dimensions, style-matching,
lighting, sources-licenses}.md + scripts/{measure_asset, extract_palette,
rank_assets, sun_position, validate_placement}.py. Body = a 7-step
copyable checklist (brief → search → fit → plan → validate → apply →
verify) using the documented plan-validate-execute pattern; build 3+
evals before polishing.

## Verification (R22-R24)

Render-free battery: scale sanity vs envelopes; BVH collision (tolerate
≤5 mm contact); support raycast (floor ±5 mm or declared mount);
clearance/corridor checks; code checks through the existing conformance
machinery; texture-palette ΔE00 vs the brief. At most ONE budgeted render
per task, gated on geometric pass + a genuinely visual question, ~768×512
≈ 520 vision tokens, auto camera at door position/eye height. License
hygiene runs in-pipeline: CC0 auto-approved; per-asset license fact
required before caching; NC/ND never enter the cache.
