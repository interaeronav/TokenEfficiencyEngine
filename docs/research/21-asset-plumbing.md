# 21 — DCC asset plumbing: import, libraries, units (2026-08-22)

Verified against Blender 5.2 API docs, developer docs, issue tracker, UE
5.8 docs/Python API, and live PolyHaven/ambientCG probes.

## Blender 5.2 asset system

- Mark + metadata: `ID.asset_mark()`, `asset_data` (author/description/
  license/copyright, `catalog_id` = RFC4122 UUID, `tags.new()`, 5.x
  `preferred_import_method`). Collection assets for kitbash groups
  (object previews exclude children).
- **Headless previews WORK since 3.6** (#93893 fixed: background renders
  synchronously, no job wait). 5.2 required for Collection-asset previews
  surviving `libraries.write()` (PR #157134). Safest universal path:
  render own 256px thumb + `lib_id_load_custom_preview` (needs
  `temp_override`). Avoid `previews_batch_generate` (history of headless
  breakage, #112632).
- Catalogs: NO Python API — write `blender_assets.cats.txt` directly
  (`VERSION 1`, `{uuid}:{path}:{simple name}` lines) and set
  `asset_data.catalog_id`. Standard pipeline practice.
- Library authoring headless: `bpy.data.libraries.write(path, {ids},
  path_remap=...)` (expands indirect deps); pack images first; register
  via `preferences.filepaths.asset_libraries` (5.0 default import method
  = 'PACK': link + embedded).
- **No headless asset-query API in 5.2** (AssetRepresentation only lives
  in browser UI context). TEE indexes itself. Free win: **5.2 Remote
  Asset Libraries** — `blender -c asset_listing generate <library>` emits
  a static queryable JSON listing (asset-index.json + per-asset pages:
  name, id_type, files, thumbnail, meta incl. tags/license/catalog) that
  TEE reads for free and can serve over HTTP so humans see the same
  library in Blender's own Asset Browser.
- Enumeration primitive: `libraries.load(path, assets_only=True)`;
  append/link via `libraries.load` (no operator context needed).

## Import paths headless (all work in --background)

glTF `import_scene.gltf` (best PBR fidelity, KHR extensions, actively
synced) > USD `wm.usd_import` > OBJ `wm.obj_import` (C++) > FBX
`wm.fbx_import` (**native C++ ufbx importer, default since 5.0**; legacy
Python importer deprecated; export still Python). Collada REMOVED in 5.0.
Material wiring: node tree auto-created in 5.x (`use_nodes` deprecated,
gone in 6.0); 4.0+ Principled socket names; Non-Color for data maps;
NormalGL convention (flip green for DX).

## Cheap metadata without a DCC

- **glTF/GLB is the only format with spec-guaranteed cheap metadata**:
  JSON chunk gives counts/materials/extensions, and POSITION accessor
  min/max is REQUIRED by spec → exact extents from pure JSON. Tri count =
  indices count/3. Tools: pygltflib (MIT), glTF-Validator (Apache-2.0,
  report has totalTriangleCount), trimesh (MIT). FBX: ufbx/pyufbx (MIT,
  young — pin) or probe inside the running Blender adapter.
- Map-set regex conventions verified live (PolyHaven `_diff_/_nor_gl_/
  _rough_/_arm_...`; ambientCG `Color/NormalGL/Roughness/...`); packed
  ARM/ORM = R:AO G:Rough B:Metal.

## Unreal 5.8

- Interchange scripted import: `InterchangeManager.import_asset` +
  **`wait_until_all_tasks_done`** (returns before finishing otherwise;
  commandlets crashed on this). Synchronous fallback: `AssetImportTask` +
  `import_asset_tasks`. glTF/USD production paths; **FBX-through-
  Interchange still Experimental in 5.8** — keep legacy FBX importer.
  Cached pipeline settings can silently override scripted ones.
- Asset Registry from Python: `ARFilter` queries, `AssetData.
  get_tag_value` (static meshes publish Triangles/LODs/ApproxSize tags —
  token-cheap without loading), `wait_for_completion()` headless.
- **Fab plugin is not automatable** (UI only; no API). One seam: Launcher
  Fab→DCC export pushes asset JSON to a local TCP socket in the DCC —
  TEE's Blender adapter can listen and auto-ingest what a human exports.

## Units & auto-fit

glTF = meters/+Y-up (importers convert correctly by construction); FBX
`UnitScaleFactor` (cm-based) = the classic 100×/0.01× failure; UE = cm
(Interchange ×100 automatic); OBJ/STL unitless. Source of truth = measured
AABB post-import, never file claims. Fit-to-plan: scale from AABB vs
target (door: width exact, ≤10% height stretch, else flag), then
`transform_apply` so physics/exports see identity; UE prefers import-time
scale over actor scale. glTF header bounds let TEE reject/rescale BEFORE
launching any import — cheapest token path.
