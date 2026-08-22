# 23 — Generative 3D landscape (2026-08-22)

Licenses read from LICENSE files/model cards; leaderboard + study evidence.

## Local models

- **TRELLIS.2-4B (Microsoft, Dec 2025) — MIT code AND weights**: the
  license flip that defines the default local lane. Image → GLB with full
  PBR (basecolor/rough/metal/opacity incl. transparency); official floor
  24 GB VRAM, community GGUF builds ~6-9 GB at 512³-1024³. ONE audit item
  before declaring the lane clean: bundled nvdiffrast/nvdiffrec are
  NVIDIA non-commercial — they must be out of the runtime path
  (UNVERIFIED whether the texture-bake step needs them).
- **Hunyuan3D 2.0/2.1/Omni (Tencent)**: community license EXCLUDES
  EU/UK/South Korea and gates >1M MAU; territory clause covers OUTPUTS.
  2.5/3.x weights never released (API only). → geo-labeled opt-in lane
  only, never default. TripoSG MIT (shape-only, needs texturing);
  TripoSR/SF3D below the 2026 bar (SF3D also $1M-revenue-capped);
  InstantMesh NC-contaminated via Zero123++ → excluded.
- In practice "text-to-3D" = text→image→image-to-3D — which gives the
  model a token-cheap review checkpoint on the concept image.

## Hosted APIs (all async submit/poll; commercial rights = paid tiers; no
downstream indemnity anywhere)

- **Tripo** ~$0.30/textured gen (cheapest serious; quad retopo + rigging
  endpoints). **Meshy** ~$0.60 (best format surface incl. BLEND; quad
  Remesh API; the wait-mode polling pattern per digest 22). Rodin Gen-2
  (quality leader, API behind Business tier). Tencent Cloud 3D
  ($0.10-0.50; EU/UK/SK service ToS UNVERIFIED). Dead/avoid: Luma Genie
  (gone), CSM (shutdown risk), Sparc3D (rug-pulled to Hitem3D), Kaedim
  (human-in-loop contracts).

## The cleanup pipeline IS the product

Raw output = dense triangle soup (100K-2M tris), confetti UVs, arbitrary
scale/up-axis/pivot, occasional open surfaces. Headless, license-clean
chain: import GLB → normalize scale/orientation/pivot → Quadriflow remesh
(built into Blender) or decimate to budget → Smart UV / xatlas (MIT) →
Cycles re-bake high→low (decimating WITHOUT re-baking visibly degrades
textures) → export glTF/FBX. Instant Meshes (BSD-3 CLI) for quad-dominant
retopo; trimesh (MIT) for watertight checks. AVOID pymeshlab (GPL,
in-process); Blender's GPL is fine (separate process).

## Honest quality bar

2026 generation delivers **good mid-ground props** — furniture, fixtures,
hard-surface architectural elements — that hold up at 2-5 m after
automated cleanup. It does NOT deliver photographic hero assets: mushy
micro-detail, plausible-not-measured PBR, fictional hidden geometry, text/
logos fail; organic/foliage/characters weak. Controlled study (IJHRSSS):
AI tavern scene 238 min vs 716 min human — but fragmented UVs, texture
loss on decimation, clipping. TEE messaging: "set dressing on demand,
hero assets curated." Leaderboards put local TRELLIS.2 within one tier of
the best hosted (Hunyuan 2.5 API, Rodin Gen-2, Meshy-6, Seed3D).

## IP status

USCO (Jan 2025): purely AI-generated output is not copyrightable in the
US; prompts alone ≠ authorship; human modification/selection adds
protection. Generated props are commercially usable but not exclusively
ownable — TEE's cleanup/curation step is also the authorship step. Provider
ToS: user indemnifies provider, never the reverse; uploading reference
images you don't own voids your position. Generated-asset provenance facts
must carry an "ai-generated" flag + generator + input hash.
