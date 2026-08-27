---
id: envasset.pipeline
title: Asset pipeline and studio standards
domain: 25_environmental_asset_creation
tags: [pipeline, naming-conventions, folder-structure, version-control, git-lfs, lod, budgets, texel-density, uv, lightmap, pivot, collision, material-instances, usd, gltf, python, automation, validation, checklist]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
applies_to: "Unreal Engine 5.8, Blender 5.2 LTS, Autodesk Fusion (May 2026). Python 3.11 (UE) / 3.13 (Blender)."
unit_system: SI
sources:
  - {title: "unreal.AssetImportTask", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetImportTask.html", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "unreal.EditorAssetLibrary", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary.html", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Creating and Using LODs in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Nanite Virtualized Geometry in Unreal Engine", url: "https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine", publisher: "Epic Games", accessed: 2026-08-25}
  - {title: "Blender Python API", url: "https://docs.blender.org/api/current/", publisher: "Blender Foundation", accessed: 2026-08-25}
related: [envasset.overview, envasset.rocks_surfaces, envasset.hardsurface_fusion, ue.python_automation, ue.project_setup, blender.python_api, fusion.api]
---

# Asset pipeline and studio standards

**Summary.** A one-person environment project accumulates a few thousand files. Without conventions it becomes unnavigable at about the six-week mark, and by then retrofitting them costs more than the work remaining. This file sets the conventions: naming, folder structure, source-versus-derived separation, version control for binaries, LOD and budget targets, texel density and UV rules, pivots, collision, material instancing, USD and glTF as interchange backbones, and runnable Blender and Unreal Python for batch export/import and validation. It closes with a reusable asset checklist that every asset must pass before it enters the scene.

## Key facts

| Item | Value | Source |
|---|---|---|
| `unreal.AssetImportTask` properties | `filename`, `destination_path`, `destination_name`, `factory`, `options`, `automated`, `replace_existing`, `replace_existing_settings`, `save`, `async_`; methods `get_objects()`, `is_async_import_complete()` | Epic Python API |
| Import entry point | `unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)` | Epic Python API |
| `EditorAssetLibrary` caveat | Operations can be slow; editor must not be in PIE; does not work on Level assets | Epic Python API |
| Unreal auto-LOD screen size | Divides screen-size percentage equally across LODs | Epic LOD docs |
| Nanite blend modes | Opaque and Masked only | Epic Nanite docs |
| Unreal embedded Python | 3.11 | domain 13 |
| Blender embedded Python | 3.13 (5.x series) | domain 14 |
| Blender unit | 1 BU = 1 m; Unreal 1 uu = 1 cm; Fusion API cm/radians | domains 13/14/15 |

> ⚠️ **Source assets never live inside the Unreal project.** `Content/` holds only `.uasset`/`.umap`. The `.blend`, `.f3d`, `.spp`, `.sbs`, raw scans, HDRIs and reference photographs live in a sibling `_Source/` tree. Mixing them makes the Unreal project enormous, breaks the Derived Data Cache, and makes it impossible to hand over cleanly.

---

## 1. Folder structure

```
OkongoHouse/
├── _Source/                          # never opened by Unreal
│   ├── 00_Reference/
│   │   ├── Site_2026-08-14/          # site visit, dated
│   │   ├── ColourCharts/
│   │   └── PureRef/
│   ├── 01_Scans/
│   │   ├── Raw/                      # the photographs
│   │   ├── Projects/                 # .rcproj / .psx
│   │   └── Output/                   # OBJ + textures straight from the solver
│   ├── 02_Blender/
│   │   ├── Foliage/
│   │   ├── Props/
│   │   ├── Terrain/
│   │   └── _Lib/                     # linked library .blend files
│   ├── 03_Fusion/                    # .f3z, STEP, drawings
│   ├── 04_Substance/                 # .sbs, .spp
│   ├── 05_Textures/                  # working PSD/TIF; exported PNG/TGA
│   ├── 06_HDRI/
│   ├── 07_GIS/                       # DEM tiles, satellite imagery, QGIS project
│   └── 08_Export/                    # FBX/glTF/USD staged for import
│
├── OkongoHouse.uproject
├── Config/
├── Content/
│   ├── _Project/                     # everything we authored
│   │   ├── Maps/
│   │   ├── Materials/
│   │   │   ├── Master/
│   │   │   ├── Instances/
│   │   │   └── Functions/
│   │   ├── Textures/
│   │   ├── Meshes/
│   │   │   ├── Architecture/
│   │   │   ├── Hardware/             # Fusion-derived
│   │   │   ├── Nature/
│   │   │   └── Props/
│   │   ├── Foliage/
│   │   ├── Landscape/
│   │   ├── Blueprints/
│   │   ├── Sequences/
│   │   └── Tools/                    # Editor Utility Widgets, Python
│   ├── _ThirdParty/                  # purchased/downloaded, untouched
│   │   ├── Megascans/
│   │   ├── PolyHaven/
│   │   └── ambientCG/
│   └── Developer/                    # scratch, never referenced by shipped maps
│
├── Scripts/                          # Python for both applications
│   ├── blender/
│   └── unreal/
├── ASSET_REGISTER.csv                # every third-party asset + its licence
├── CREDITS.md                        # attributions required by licences
└── README.md
```

**Rules:**
1. `_ThirdParty/` content is **never edited**. Make a Material Instance or a derived mesh in `_Project/` instead. This keeps re-downloads and licence audits simple.
2. `Developer/` is excluded from cook and from any delivery.
3. Every folder that contains third-party content has a `LICENCE.txt` naming the source, the licence and the download date.
4. `ASSET_REGISTER.csv` columns: `asset_path, source, url, licence, cost, date_acquired, redistributable_y_n`.

---

## 2. Naming conventions

Prefix by type, then a category, then the specific name, then a variant/index. `PascalCase` throughout, no spaces, no hyphens inside the name.

| Prefix | Type | Example |
|---|---|---|
| `SM_` | Static Mesh | `SM_Nature_Mopane_Mature_01` |
| `SK_` | Skeletal Mesh | `SK_Char_Adult_01` |
| `M_` | Material (master) | `M_Master_Ground_Layered` |
| `MI_` | Material Instance | `MI_Ground_Okongo_Yard` |
| `MF_` | Material Function | `MF_HeightLerp` |
| `MPC_` | Material Parameter Collection | `MPC_Weather` |
| `T_` | Texture | `T_Sand_Fine_BC`, `T_Sand_Fine_N`, `T_Sand_Fine_ORDp` |
| `RVT_` | Runtime Virtual Texture | `RVT_Landscape_BCNR` |
| `BP_` | Blueprint | `BP_GateSwing` |
| `L_` | Level / Map | `L_Site_Ext_1400_Aug` |
| `FT_` | Foliage Type | `FT_Grass_DryTussock_01` |
| `LG_` | Landscape Grass Type | `LG_Sandveld` |
| `PP_` | Post Process | `PP_Base` |
| `NS_` / `NE_` | Niagara System / Emitter | `NS_DustHaze` |
| `HDRI_` | HDRI | `HDRI_Okongo_1200_2026-08-14_x1.34` |

**Texture suffixes** (fixed, never varied):

| Suffix | Content | Colour space | Compression |
|---|---|---|---|
| `_BC` | Base Colour | sRGB | Default (DXT1/BC1 or BC7) |
| `_N` | Normal (OpenGL +Y up in Blender; **Unreal expects DirectX −Y**, flip green on export) | Linear | Normalmap (BC5) |
| `_ORDp` | R=AO, G=Roughness, B=Displacement/Height, A=Packed extra | **Linear, sRGB OFF** | Masks (BC7) |
| `_M` | Metallic (only if not packed) | Linear | Masks |
| `_E` | Emissive | sRGB | Default |
| `_A` | Opacity / alpha mask | Linear | Alpha or Masks |
| `_ID` | Material ID / mask set | Linear | Masks |
| `_FM` | Flow map | Linear | Masks |

> The single most common texture bug is an `_ORDp` or `_N` map left with **sRGB on**. It makes roughness subtly wrong everywhere and is invisible until you compare against reference. Validate it (§8).

**Variants and LODs:** `_01`, `_02` for mesh variants; LODs are internal to the Unreal asset, not separate names.

**Fusion-derived assets carry the CAD version:** `SM_Hardware_Gate_Entrance_L_v007`.

---

## 3. Source versus derived, and version control

**Derived assets can always be rebuilt from source.** Textures baked from a `.blend`, FBX exported from a `.blend`, `.uasset` imported from an FBX — all derived. The `.blend`, the `.f3z`, the `.sbs`, the raw photographs — source.

**Version control.** Use **Git with Git LFS** for `_Source/` and `Scripts/`, and either Git LFS or Perforce for `Content/`.

`.gitattributes`:

```
*.blend    filter=lfs diff=lfs merge=lfs -text
*.blend1   filter=lfs diff=lfs merge=lfs -text
*.uasset   filter=lfs diff=lfs merge=lfs -text
*.umap     filter=lfs diff=lfs merge=lfs -text
*.fbx      filter=lfs diff=lfs merge=lfs -text
*.exr      filter=lfs diff=lfs merge=lfs -text
*.hdr      filter=lfs diff=lfs merge=lfs -text
*.png      filter=lfs diff=lfs merge=lfs -text
*.tga      filter=lfs diff=lfs merge=lfs -text
*.psd      filter=lfs diff=lfs merge=lfs -text
*.tif      filter=lfs diff=lfs merge=lfs -text
*.f3z      filter=lfs diff=lfs merge=lfs -text
*.step     filter=lfs diff=lfs merge=lfs -text
*.spp      filter=lfs diff=lfs merge=lfs -text
*.sbs      filter=lfs diff=lfs merge=lfs -text
*.sbsar    filter=lfs diff=lfs merge=lfs -text
```

`.gitignore` for an Unreal project: `Binaries/`, `Build/`, `DerivedDataCache/`, `Intermediate/`, `Saved/`, `.vs/`, `*.sln`.

**Binary files do not merge.** With one person this is fine. With two, adopt a lock-based workflow (`git lfs lock`) or Perforce. Unreal's own Revision Control panel integrates with both.

**Commit discipline:** one asset or one coherent change per commit; message format `[area] what changed` — e.g. `[foliage] mopane LOD screen sizes tuned, dithered transition on`.

---

## 4. Budgets

These are targets for a *still-image and pre-rendered-sequence* archviz project on a workstation GPU. A real-time walkthrough on modest hardware needs roughly half of everything.

### 4.1 Triangles

| Asset class | Nanite | Non-Nanite LOD0 |
|---|---|---|
| Hero architectural element (gate, door, window assembly) | 0.5–3 M | 15 000–40 000 |
| Building shell | 1–5 M | 50 000–200 000 |
| Hero tree | 1–4 M | 60 000–150 000 |
| Background tree | 200 k–1 M | 15 000–40 000 |
| Grass clump | n/a (use non-Nanite for grass) | 200–800 |
| Rock / termite mound | 500 k–2 M | 3 000–8 000 |
| Prop (bucket, tool, chair) | 100–500 k | 2 000–10 000 |
| Landscape | — | fixed by component config |

**Scene totals**: a still frame under Nanite can carry billions of source triangles; the meaningful budget is **instance count and material count**, not triangles.

### 4.2 Draw calls

| Target | Draw calls |
|---|---|
| Real-time walkthrough, 60 fps on a mid GPU | < 3 000 |
| Real-time, high-end GPU | < 6 000 |
| Pre-rendered stills | not a constraint, but > 15 000 signals a structural problem |

**How to keep them down**: instanced static meshes (the Foliage tool and `HISM` components do this automatically), fewer unique materials (material instances of one master share the same shader), merged actors for distant clusters, and `Level Instances` for repeated structures.

### 4.3 Texture memory

| Target | Budget |
|---|---|
| Total streaming pool, workstation | 4–8 GB |
| Total streaming pool, modest GPU | 2 GB |
| Per hero asset | ≤ 60 MB |
| Per background asset | ≤ 8 MB |

Check with `r.Streaming.PoolSize` and the `Statistics` window (Window → Statistics → Texture Statistics), or the console command `stat streaming`.

**Texture resolution ceilings:** 4096 for a hero surface; 2048 for standard architecture; 1024 for props; 512 for background. **8192 only** for a landscape macro-variation map or a captured HDRI. A 4K BC7 texture with mips is ~21 MB; ten of them is 210 MB. This adds up faster than anyone expects.

### 4.4 LOD screen sizes

Unreal's Auto Compute divides screen size equally across LODs. Turn it off and use:

| LOD | Screen size |
|---|---|
| 0 | 1.0 |
| 1 | 0.45 |
| 2 | 0.18 |
| 3 | 0.06 |
| 4 (imposter) | 0.02 |

Foliage wants the more aggressive schedule in `04 §5`.

---

## 5. Texel density, UVs and lightmaps

**Texel density standard** — repeated from `05 §6` because it belongs in the standards file too:

| Class | px/m |
|---|---|
| Hero close-up | 2048 |
| Primary architecture and ground | 1024 |
| Secondary props | 512 |
| Background | 256 |

**UV rules:**
1. **UV0** is always the texturing channel.
2. **UV1** is the lightmap channel *if lighting is baked*. Under Lumen, omit it — Epic advises disabling `generate_lightmap_u_vs` on Nanite meshes because it adds a channel and significant data on dense geometry.
3. No UVs outside 0–1 unless the material deliberately tiles.
4. No overlapping UVs in UV0 unless the material is a pure tiling material with no baked maps.
5. Island margin ≥ **0.02** normalised (about 8 px on a 512 texture) so mip-mapping does not bleed.
6. **Average Islands Scale** then **Pack Islands** so texel density is uniform within an asset.
7. Mirrored UVs are acceptable for symmetric hard-surface parts but forbidden for anything with directional weathering or a decal.
8. Lightmap UVs (when used) must be non-overlapping, with a margin sized for the lightmap resolution: at least 2 texels of padding — so for a 64 lightmap, ≥ 0.03 normalised.

---

## 6. Pivots, origins and collision

**Pivot rules:**

| Asset type | Pivot |
|---|---|
| Anything that sits on the ground | Base centre, at the contact plane, Z = 0 |
| Anything that hangs from a wall | At the wall face, at the fixing height |
| Anything that rotates | **On the axis of rotation** — hinge line for a gate, spindle for a handle |
| Modular pieces | At a grid-aligned corner so they snap |
| Foliage | Base centre, at the trunk/soil interface |

Rotation: **+X forward, +Z up** in Unreal; **+Y forward, +Z up** in Blender. Export FBX with Forward `-Z`, Up `+Y` (Blender's FBX exporter defaults) and Unreal reconstructs it correctly.

Always **apply transforms** in Blender (`Ctrl+A → All Transforms`) before export. An unapplied scale is the source of most "why is my normal map inverted" and "why is my collision wrong" bugs.

**Collision:**

| Asset | Collision |
|---|---|
| Wall, floor, slab | Box simplified collision (`UBX_`) |
| Cylinder-ish prop | Capsule (`UCP_`) or sphere (`USP_`) |
| Gate, complex frame | Convex decomposition, 4–8 hulls |
| Rock, termite mound | Convex decomposition, 4–8 hulls, from a decimated copy |
| Foliage | **None** on grass; a simple capsule on trees only if the visitor can walk into them |
| Landscape | Built in |

Name collision meshes in Blender with the `UBX_`/`UCP_`/`USP_`/`UCX_` prefix plus the render mesh's name (`UCX_SM_Rock_01_01`) and export them in the same FBX — Unreal picks them up automatically. Never use per-triangle collision on a scanned or Nanite mesh.

---

## 7. Material instancing strategy

**One master material per shading *category*, many instances.**

| Master | Covers | Key exposed parameters |
|---|---|---|
| `M_Master_Standard` | Most opaque surfaces | BC/N/ORDp textures, tiling, colour tint, roughness min/max, detail normal scale, dust amount |
| `M_Master_Ground_Layered` | Landscape | Per-layer textures and scales, macro variation, distance blend, RVT output |
| `M_Master_Foliage` | Leaves, grass | Two Sided Foliage, subsurface colour, wind params, per-instance colour variation |
| `M_Master_Metal` | Steelwork | Metallic, base tint, rust mask amount, edge-wear amount, dust |
| `M_Master_Glass` | Glazing | IOR, tint, dirt amount, roughness |
| `M_Master_Water` | Water bodies | Single Layer Water inputs |
| `M_Master_Blend_RVT` | Anything blending into terrain | Blend height, blend sharpness |

**Why this matters beyond tidiness:** every unique master material is a unique shader permutation to compile, and shader compilation is the single largest cause of editor stalls in a texture-heavy archviz project. Twenty instances of one master compile once. Twenty separate materials compile twenty times, and again for every quality level and platform.

**Use a Material Parameter Collection** (`MPC_Weather`) for global values — wind intensity, wetness, dust amount, season — so one slider changes the whole scene.

---

## 8. USD as a pipeline backbone

USD (Universal Scene Description) solves the problem that FBX cannot: **non-destructive layering and referencing across applications**.

- Fusion exports USD (`USDExportOptions`).
- Blender imports and exports USD natively.
- Unreal has a USD Stage importer/editor.
- USD carries `metersPerUnit`, so the scale problem in `07 §3` largely disappears.

**Where it earns its keep here:**
1. **Layering.** The building geometry is one layer, the landscape another, the foliage placement another, the lighting another. Each can be updated independently and re-composed.
2. **Referencing.** One `Mopane_Mature.usd` referenced 40 times, updated once.
3. **Variants.** A `season` variant set switching dry/wet foliage and ground; a `phase` variant set switching as-built/proposed.
4. **Round-trip with the CAD master.** Re-export the gate from Fusion as USD over the same layer path and the scene picks it up.

**Where it does not yet earn it:** Unreal's USD support does not fully replace the native asset pipeline, materials do not translate losslessly (use USD for structure and re-author materials natively), and Nanite/foliage settings live in the `.uasset`, not in USD. Treat USD as the **structural** backbone, not as the material or engine-settings backbone.

**glTF 2.0** is the right choice for a different job: a lightweight, self-contained, web- or client-viewable deliverable. It carries PBR metallic-roughness materials well, is well-supported by Blender and by Unreal's glTF exporter, and is the correct format for handing a client a model they can open without any software. Its limitations: no layering, no variants, and a single PBR model.

---

## 9. Automation — runnable code

### 9.1 Blender: batch export FBX with conventions

```python
"""
batch_export_fbx.py  -  Blender 5.2
Exports every mesh object in a named collection to _Source/08_Export/<Category>/,
one FBX per object, named to the project convention, transforms applied,
collision meshes exported alongside.

Run:  blender file.blend --background --python batch_export_fbx.py -- Nature Foliage
      (argv after '--' : <CollectionName> <Category>)
"""
import bpy, os, sys, math

def argv_after_dashes():
    a = sys.argv
    return a[a.index("--") + 1:] if "--" in a else []

ARGS       = argv_after_dashes()
COLLECTION = ARGS[0] if ARGS else "Export"
CATEGORY   = ARGS[1] if len(ARGS) > 1 else "Props"
OUT_DIR    = bpy.path.abspath(f"//../../08_Export/{CATEGORY}")
COLLISION_PREFIXES = ("UBX_", "UCX_", "UCP_", "USP_")

os.makedirs(OUT_DIR, exist_ok=True)

def collision_children(obj):
    """Collision meshes are children named UCX_<parent> etc."""
    return [c for c in bpy.data.objects
            if c.parent == obj and c.name.startswith(COLLISION_PREFIXES)]

def prepare(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

def export_one(obj):
    prepare(obj)
    for c in collision_children(obj):
        c.select_set(True)

    # Move to world origin for export, remember where it was.
    loc = obj.location.copy()
    obj.location = (0.0, 0.0, 0.0)

    path = os.path.join(OUT_DIR, f"{obj.name}.fbx")
    bpy.ops.export_scene.fbx(
        filepath           = path,
        use_selection      = True,
        global_scale       = 1.0,
        apply_unit_scale   = True,
        apply_scale_options= 'FBX_SCALE_ALL',
        axis_forward       = '-Z',
        axis_up            = 'Y',
        object_types       = {'MESH'},
        use_mesh_modifiers = True,
        mesh_smooth_type   = 'FACE',
        use_tspace         = True,          # export tangents for normal maps
        add_leaf_bones     = False,
        bake_anim          = False,
        path_mode          = 'COPY',
        embed_textures     = False,
    )
    obj.location = loc
    return path

def main():
    coll = bpy.data.collections.get(COLLECTION)
    if coll is None:
        print(f"ERROR: collection '{COLLECTION}' not found")
        return
    exported = []
    for obj in coll.objects:
        if obj.type != 'MESH':
            continue
        if obj.name.startswith(COLLISION_PREFIXES):
            continue
        exported.append(export_one(obj))
    print(f"\nExported {len(exported)} FBX to {OUT_DIR}")
    for p in exported:
        print("  " + os.path.basename(p))

if __name__ == "__main__":
    main()
```

### 9.2 Blender: pre-export validation

```python
"""
validate_assets.py  -  Blender 5.2
Checks every mesh object against the project standards and prints a report.
Run inside Blender (Scripting workspace) or with --background --python.
"""
import bpy, math

MAX_TRIS_NON_NANITE = 40000
MIN_UV_MARGIN       = 0.02

def tri_count(ob):
    me = ob.data
    return sum(len(p.vertices) - 2 for p in me.polygons)

def check(ob):
    issues = []
    if ob.type != 'MESH':
        return issues

    # transforms applied?
    if tuple(round(s, 5) for s in ob.scale) != (1.0, 1.0, 1.0):
        issues.append(f"scale not applied: {tuple(round(s,3) for s in ob.scale)}")
    if any(abs(r) > 1e-5 for r in ob.rotation_euler):
        issues.append("rotation not applied")

    # naming
    if not ob.name.startswith(("SM_", "SK_", "UBX_", "UCX_", "UCP_", "USP_")):
        issues.append(f"name has no type prefix: {ob.name}")

    # UVs
    if len(ob.data.uv_layers) == 0:
        issues.append("no UV layer")
    elif len(ob.data.uv_layers) > 2:
        issues.append(f"{len(ob.data.uv_layers)} UV layers (expected 1 or 2)")

    # geometry health
    me = ob.data
    loose = [v for v in me.vertices if not any(v.index in p.vertices for p in me.polygons)]
    if loose:
        issues.append(f"{len(loose)} loose vertices")
    ngons = [p for p in me.polygons if len(p.vertices) > 4]
    if ngons:
        issues.append(f"{len(ngons)} n-gons")

    # triangle budget
    t = tri_count(ob)
    if t > MAX_TRIS_NON_NANITE:
        issues.append(f"{t} triangles - Nanite required or retopologise")

    # materials
    if len(ob.data.materials) == 0:
        issues.append("no material assigned")
    if len(ob.data.materials) > 4:
        issues.append(f"{len(ob.data.materials)} material slots (target <= 4)")

    # origin at base?
    zmin = min((ob.matrix_world @ v.co).z for v in me.vertices)
    if abs(zmin - ob.location.z) > 0.05 and abs(zmin) > 0.05:
        issues.append(f"origin not at base (lowest z = {zmin:.3f} m)")

    return issues

def main():
    total = 0
    for ob in bpy.data.objects:
        iss = check(ob)
        if iss:
            total += len(iss)
            print(f"\n{ob.name}")
            for i in iss:
                print(f"   - {i}")
    print(f"\n{'PASS' if total == 0 else f'{total} issue(s) found'}")

if __name__ == "__main__":
    main()
```

### 9.3 Unreal: batch import with the project conventions

Built on the verified `AssetImportTask` API (see domain `13` file `06` for the base pattern).

```python
"""
batch_import.py  -  Unreal Engine 5.8, embedded Python 3.11
Imports FBX from _Source/08_Export into /Game/_Project/Meshes/<Category>,
enables Nanite where appropriate, and reports.

Run from the Output Log:  py "D:/OkongoHouse/Scripts/unreal/batch_import.py"
"""
import unreal, os, glob

SOURCE_ROOT = r"D:/OkongoHouse/_Source/08_Export"
DEST_ROOT   = "/Game/_Project/Meshes"

# Categories that should NOT get Nanite (translucent, or foliage using cards + WPO)
NO_NANITE = {"Glass", "GrassCards"}


def make_fbx_options(is_foliage: bool) -> unreal.FbxImportUI:
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_textures", False)     # we assign our own
    opts.set_editor_property("import_materials", False)
    opts.set_editor_property("import_as_skeletal", False)
    smd = opts.static_mesh_import_data
    smd.set_editor_property("combine_meshes", False)       # one asset per object
    smd.set_editor_property("generate_lightmap_u_vs", False)   # Lumen: no bake
    smd.set_editor_property("auto_generate_collision", False)  # we author UCX_
    smd.set_editor_property("remove_degenerates", True)
    smd.set_editor_property("build_reversed_index_buffer", True)
    smd.set_editor_property(
        "normal_import_method",
        unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    smd.set_editor_property("import_uniform_scale", 100.0)  # metres -> centimetres
    return opts


def build_tasks():
    tasks = []
    for category in sorted(os.listdir(SOURCE_ROOT)):
        cat_dir = os.path.join(SOURCE_ROOT, category)
        if not os.path.isdir(cat_dir):
            continue
        for fbx in sorted(glob.glob(os.path.join(cat_dir, "*.fbx"))):
            task = unreal.AssetImportTask()
            task.filename          = fbx
            task.destination_path  = f"{DEST_ROOT}/{category}"
            task.automated         = True
            task.replace_existing  = True
            task.replace_existing_settings = False   # keep artist-set Nanite etc.
            task.save              = True
            task.options           = make_fbx_options(category == "Foliage")
            tasks.append((task, category))
    return tasks


def apply_nanite(mesh: unreal.StaticMesh, category: str):
    if category in NO_NANITE:
        return
    settings = mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", settings)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)


def main():
    pairs = build_tasks()
    if not pairs:
        unreal.log_warning(f"No FBX found under {SOURCE_ROOT}")
        return

    tasks = [t for t, _ in pairs]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    imported = 0
    for task, category in pairs:
        for obj in task.get_objects():
            if isinstance(obj, unreal.StaticMesh):
                apply_nanite(obj, category)
            unreal.log(f"imported [{category}] {obj.get_path_name()}")
            imported += 1
    unreal.log(f"=== {imported} asset(s) imported ===")


if __name__ == "__main__":
    main()
```

> `needs-verification`: the exact editor-property path for Nanite (`nanite_settings` on `StaticMesh`, with an `enabled` sub-property) — confirm against `unreal.StaticMesh` and `unreal.MeshNaniteSettings` in the version you are running, and adjust if the property name differs. The `AssetImportTask` and `FbxImportUI` usage above is on the verified path documented in domain `13`.

### 9.4 Unreal: texture settings validation

```python
"""
validate_textures.py  -  Unreal Engine 5.8
Checks that normal maps and packed masks have the right sRGB and compression
settings, and reports anything oversized.
"""
import unreal

ROOT = "/Game/_Project/Textures"
MAX_DIM = {"_BC": 4096, "_N": 4096, "_ORDp": 4096, "_A": 2048, "_E": 2048}

EAL = unreal.EditorAssetLibrary

def main():
    problems = 0
    for path in EAL.list_assets(ROOT, recursive=True, include_folder=False):
        tex = EAL.load_asset(path)
        if not isinstance(tex, unreal.Texture2D):
            continue
        name = tex.get_name()
        srgb = tex.get_editor_property("srgb")
        comp = tex.get_editor_property("compression_settings")
        w = tex.blueprint_get_size_x()
        h = tex.blueprint_get_size_y()

        msgs = []
        if name.endswith("_N"):
            if srgb:
                msgs.append("sRGB should be OFF on a normal map")
            if comp != unreal.TextureCompressionSettings.TC_NORMALMAP:
                msgs.append(f"compression should be TC_NORMALMAP, is {comp}")
        elif name.endswith(("_ORDp", "_M", "_A", "_ID", "_FM")):
            if srgb:
                msgs.append("sRGB should be OFF on a data/mask texture")
            if comp not in (unreal.TextureCompressionSettings.TC_MASKS,
                            unreal.TextureCompressionSettings.TC_BC7):
                msgs.append(f"compression should be TC_MASKS or TC_BC7, is {comp}")
        elif name.endswith(("_BC", "_E")):
            if not srgb:
                msgs.append("sRGB should be ON on a colour texture")

        for suf, cap in MAX_DIM.items():
            if name.endswith(suf) and (w > cap or h > cap):
                msgs.append(f"{w}x{h} exceeds the {cap} cap for {suf}")

        if (w & (w - 1)) or (h & (h - 1)):
            msgs.append(f"{w}x{h} is not power-of-two - no mips, no streaming")

        if msgs:
            problems += len(msgs)
            unreal.log_warning(f"{name}:")
            for m in msgs:
                unreal.log_warning(f"    - {m}")

    unreal.log(f"=== texture validation: {problems} problem(s) ===")

if __name__ == "__main__":
    main()
```

> `needs-verification`: `Texture2D.blueprint_get_size_x()` / `blueprint_get_size_y()` are the Blueprint-exposed accessors; if they are unavailable in your build, use `tex.get_editor_property("imported_size")` and read `.x` / `.y`.

---

## 10. The reusable asset checklist

Print it. Every asset passes it before it enters a level.

**Geometry**
- [ ] Real-world scale, verified against a known dimension
- [ ] Transforms applied (scale 1,1,1; rotation zeroed)
- [ ] Origin at the correct functional point (base / hinge / grid corner)
- [ ] No loose vertices, no n-gons, no non-manifold geometry
- [ ] Normals recalculated outward; sharp edges marked; Weighted Normal where CAD-derived
- [ ] Every edge has a bevel or a shader bevel — nothing perfectly sharp
- [ ] Triangle count within budget for its class, or Nanite enabled

**UVs and textures**
- [ ] UV0 present, non-overlapping (unless a pure tiling material), island margin ≥ 0.02
- [ ] Texel density matches the class standard, checked with a grid material
- [ ] Lightmap UV present only if lighting is baked
- [ ] Texture names carry the correct suffix
- [ ] `_N` and `_ORDp` have sRGB **off** and the correct compression
- [ ] Textures power-of-two and within the resolution cap
- [ ] Albedo clamped 0.03–0.90; roughness textured and clamped 0.03–0.97

**Material**
- [ ] It is a Material *Instance* of a project master, not a unique material
- [ ] Specular left at 0.5 for dielectrics
- [ ] Surface history present (dust, wear, staining) — nothing factory-new
- [ ] Per-instance variation wired (`PerInstanceRandom`)

**Engine**
- [ ] Nanite on (unless translucent or grass cards)
- [ ] LOD screen sizes set manually where non-Nanite; dithered transition on
- [ ] Collision simplified and named with the correct prefix
- [ ] Base blends into terrain (RVT) where it meets the ground
- [ ] Placed with random rotation/scale/Z-offset if instanced

**Project**
- [ ] Named to convention
- [ ] In the correct folder
- [ ] Source file committed with LFS
- [ ] If third-party: recorded in `ASSET_REGISTER.csv` with its licence
- [ ] Passes `validate_assets.py` and `validate_textures.py`

## Sources

- [unreal.AssetImportTask](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetImportTask.html) — Epic Games
- [unreal.EditorAssetLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary.html) — Epic Games
- [Creating and Using LODs in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-and-using-lods-in-unreal-engine) — Epic Games
- [Nanite Virtualized Geometry in Unreal Engine](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine) — Epic Games
- [Blender Python API](https://docs.blender.org/api/current/) — Blender Foundation
- Internal: `13_software_unreal_engine/06_python-and-automation.md`, `14_software_blender/06_python-api-and-automation.md`, `15_software_autodesk_fusion/09_api-and-automation.md`

## Open questions

- **Nanite editor-property path** on `unreal.StaticMesh` in 5.8 (`nanite_settings` → `enabled`). `needs-verification`.
- **`Texture2D` size accessors** in Python for 5.8. `needs-verification`.
- Whether **`bpy.ops.export_scene.fbx`** in Blender 5.2 still accepts all the keyword arguments used in §9.1 — Blender's FBX exporter was rewritten in C++ for import in 5.0 and the export operator's signature may have shifted. `needs-verification` — run it once.
- Whether Unreal's **USD Stage** workflow in 5.8 can carry Nanite and foliage settings, which would change the recommendation in §8. `needs-verification`.
