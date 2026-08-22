# 42 — UEFN automation prior art & module design (2026-08-22)

## Prior-art inventory (licenses decide reuse)

**Custom editor bridges are a dead category**: quangdang46's
uefn-verse-mcp (AGPL) was archived 2026-08-17 — three days before Epic
shipped MCP in UEFN. What remains useful: UEFN-TOOLBELT (AGPL + custom
clause — **reference only**, but proves 358 Python tools incl. bulk FBX
import and a 4,698-device catalog work on UEFN Python);
KirChuvakov/uefn-mcp-server (MIT, the two-process tick-callback
pattern); **ADEPT uefn-verse-compiler (MIT)** — compiles by speaking to
UEFN's internal workflow-server loopback TCP (Content-Length-framed
JSON, `compileProject` → structured {severity, message, file, line,
column}); protocol explicitly unstable. uefn-substance-bridge (MIT) is
the live-sync precedent (HTTP POST → in-editor listener → Slate
post-tick main-thread queue; content-hash change detection). Snippet
corpora worth seeding from: uefncentral/uefn-verse-examples (MIT, 395
compiler-verified), OsirionGG (Apache-2.0, stale), VerseMaxxing
(Apache-2.0), pragers (MPL-2.0). **vz-creates/uefn** diffs Verse
digests across every version v24.01→v42.00 — exactly TEE's firewall
shape, but the content is Epic-copyrighted: **generate digests from
the user's local install** (`%LOCALAPPDATA%\UnrealEditorFortnite\
Saved\VerseProject\FortniteGame\Fortnite\`), **never redistribute**.

**No Blender→UEFN addon exists. No CLI, no headless mode, no publish
API.** The AI field (EDA, UEFN Central, Versly) has independently
converged on digest validation as the differentiator; nobody has
published quality evals; Epic's MCP subsumes the
copilot-that-compiles category.

## Blender→UEFN pipeline facts (TEE's wedge)

Formats: FBX (dedicated path), OBJ/glTF/GLB (Interchange); no USD.
Scale: 1 uu = 1 cm (the ×100 Blender unit boundary is the top
friction); player = 192 cm; 512-unit modular grid. Collision:
`UCX_<MeshName>` (case-sensitive, ≤10 meshes); Face-smoothing export.
Budgets (Fortnite-Ready tables): LOD0 tri caps by class S/M/L —
simple 400/900/2,500, medium 700/2,000/6,000, complex
1,200/4,000/9,000 (trees 1,700/5,000/15,000, rocks 600/1,200/2,500,
vehicles 1,200/6,000/9,000; warn > 20k verts); **three LODs required
at −50% steps**; textures ≤ 2K recommended / 4096 hard max,
power-of-two mandatory, 512² preferred for mobile; packed utility map
**Spec=R, Metal=G, Rough=B**; ideally one material section per mesh.
v42.00 defaults imports to mobile-friendly settings and warns on
missing LODs. Island cap: 100k memory units per area. Blender
procedural node graphs never transfer — bake. UNVERIFIED: 256 MB
deploy-cap scope; Nanite-for-custom-imports (forum evidence says
effectively unusable — the LOD path is the real contract).

## The three-shape verdict (A22)

- **(a) Full adapter from scratch: no.** Epic's UEFN MCP closes the
  loop for Verse/devices/entities/sessions; Windows-only, beta, five
  toolsets, live-editor-only, LUF↔XYZ bug, no publish/memory/import
  surface. The community bridge graveyard proves custom listeners
  lose. A **thin proxy** over Epic's toolsets is the A4 pattern again
  (same server name, same `8000/mcp` shape — likely shared plumbing
  with TEE's UE 5.8 proxy).
- **(b) Docs + codegen module: the core.** All inputs exist and are
  license-clean or locally derivable: machine-readable digests in
  every install; the version-diff precedent; an MIT corpus of
  compiler-verified examples; a proven market gap; and a Blender
  export lane nobody has built. Works offline, cross-platform,
  pytest-able — matches every hard rule in CLAUDE.md.
- **(c) Skill-only: insufficient alone** now that a real automation
  surface exists — but the right carrier for judgment (budget
  interpretation, device-vs-Verse-vs-SceneGraph choice, memory
  triage), per A15/A16 packaging conventions.

**Ship (b) as core + (a)-lite proxy behind capability detection + (c)
`uefn` skill.** AGPL code is never reused; MIT/Apache/MPL sources are.

## Scene Graph verdict (A23)

Scene Graph (Beta, publishable) is **confirmed as the UE6 object
model** — the only vocabulary that survives the convergence. Build
TEE's UEFN vocabulary around entity/component ops; wrap Creative
devices as a parallel, eventually-legacy op family (devices are not
directly Scene-Graph-compatible — Verse glue required; the component
catalog is still narrow: no physics-body/collision/UI components yet).

## Build-now vs design-later

Build now (cloud, pytest, no DCC): digest ingestion + version-keyed
facts + digest diff firewall; the Blender `export_for_uefn` op with a
pure-Python budget validator (encoded tables), LOD1/2 autogeneration,
shader baking + Spec/Metal/Rough channel packing, FBX config, and an
exact-fix report; the UEFN adapter interface + fakes with the typed
batch/diff/checkpoint contract and server-side LUF↔XYZ normalization;
Verse template corpus with offline digest-symbol validation; the
Fortnite Data API compact analytics tool. Design later: the live
proxy (after the UE 5.8 proxy lands), Scene Graph ops on Epic's
toolset, the live-compile lane, and the UE6/Blender-6 adapter merge
(~end-2027; keep UE and UEFN behind one interface). Watch: UMG
toolset (docs/notes disagree), publish/memory surface (none today —
likely stays human-gated for moderation; never promise it).
