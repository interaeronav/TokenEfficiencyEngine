# 46 — Mesh repair + post-processing toolchain (2026-08-22)

Source claims verified against local clones (microsoft/trellis.2 @75fbf01,
shivampkumar/trellis-mac @d58628f); license/wheel claims against PyPI/repo
pages on 2026-08-22.

## Upstream TRELLIS.2: what cumesh actually does, and where

- `cumesh` is JeffreyXiang/CuMesh — MIT-licensed but **CUDA-exclusive** (CUDA >= 12.4, PyTorch CUDA); installed from git in `o-voxel/pyproject.toml:32` (`cumesh @ git+https://github.com/JeffreyXiang/CuMesh.git`). License/ops verified at https://github.com/JeffreyXiang/CuMesh (MIT; cleaning, hole filling by boundary-loop triangulation, GPU decimation, DC remeshing, xatlas-backed UV unwrap with GPU chart clustering).
- **Decode-time use** — `trellis2/pipelines/trellis2_image_to_3d.py:474` calls `m.fill_holes()` on every decoded mesh before wrapping it in `MeshWithVoxel`. That method (`trellis2/representations/mesh/base.py:35-57`) is pure cumesh: boundary detection + `mesh.fill_holes(max_hole_perimeter=3e-2)` — fill only boundary loops whose perimeter is under 3% of the unit-normalized scene. `base.py:71-81` also wraps `cumesh.simplify` (used e.g. `example.py:26` to get under the 16.7M-face nvdiffrast limit).
- **Export-time use** — `o_voxel.postprocess.to_glb` (`o-voxel/o_voxel/postprocess.py:14-331`) is the whole post-processing pipeline. Sequence (file:line):
  - fill holes on the raw full-res mesh (`postprocess.py:110`), then **build a cuBVH over that full-res hole-filled mesh** (`postprocess.py:122`);
  - non-remesh branch: simplify to 3x target → `remove_duplicate_faces` / `repair_non_manifold_edges` / `remove_small_connected_components(1e-5)` / `fill_holes` again → simplify to target → same cleanup loop again → `unify_face_orientations` (`postprocess.py:134-162`);
  - remesh branch: narrow-band Dual Contouring rebuild + simplify (`postprocess.py:165-187`);
  - cumesh `uv_unwrap` with GPU chart clustering (`postprocess.py:201-210`); vertex normals via cumesh (`postprocess.py:215-216`);
  - **texture bake**: nvdiffrast rasterizes the mesh in UV space (`postprocess.py:230-243`), each texel's 3D position is **projected back onto the original full-res mesh via the BVH** (`postprocess.py:252-256`, comment: "corrects geometric errors introduced by simplification/remeshing"), then PBR attributes are trilinearly sampled from the sparse **voxel attribute volume** (`postprocess.py:259-266`), cv2-inpainted at chart seams (`postprocess.py:287-292`), packed into a trimesh `PBRMaterial` GLB (`postprocess.py:296-323`).
- Key architectural fact: **textures do not exist as images until `to_glb` runs**. The pipeline output (`MeshWithVoxel`, `trellis2_image_to_3d.py:475-485`) carries geometry + a sparse voxel PBR attribute volume (`attrs`/`coords`/`layout`). The texturing pipeline (`trellis2/pipelines/trellis2_texturing.py:287-334, 407`) likewise bakes from a PBR voxel and only uses cumesh `uv_unwrap` when the input mesh has no UVs (`trellis2_texturing.py:304-306`).

## What trellis-mac substitutes (and the defects it creates)

- Stubs out cumesh entirely (`backends/stubs.py:20-29`); `patches/mps_compat.py:234-296` patches `mesh/base.py` so `fill_holes`, `remove_faces`, and `simplify` **unconditionally `return`** — "Metal cumesh segfaults on large decode meshes" (`mps_compat.py:263-272`). README confirms: "Hole filling disabled … Output meshes may have small holes" (`README.md:150`) and "`cumesh` | Skipped during decode … replaced with `fast_simplification` before baking" (`README.md:107`).
- The Metal port in question is pedronaugusto's `mtlmesh`/`mtlbvh`/`mtldiffrast`/`mtlgemm` stack (`setup.sh:40-43,101-108`); its BVH "builder is unstable on 800K+ face inputs" (`README.md:120`), so `generate.py:206-217` pre-simplifies 800K→200K faces with `fast_simplification` **before** calling `to_glb` — meaning the bake's BVH reference is the *simplified* mesh, not the original. Upstream projects texels onto the full-res mesh (`postprocess.py:117-122, 252-256`); trellis-mac has thrown that surface away. This is the "quality loss from naive pre-simplification" defect: it is not decimation per se, it is **losing the full-res reference surface for the bake**.
- Fallback path (`generate.py:243-277`, `backends/texture_baker.py`): xatlas UV unwrap + numpy UV rasterizer + scipy cKDTree inverse-distance sampling of the voxel grid — a fully CPU, license-clean bake, but with no hole fill and no cleanup at all.

## Candidate library survey (license/wheels verified on PyPI/repos, 2026-08-22)

- **trimesh** — MIT, v5.0.0 (2026-08-01), pure-Python `py3-none-any` wheel; repair: winding/normals fixes, fan-based `fill_holes` ("may result in bad answers if the holes are non convex"), `stitch`, `broken_faces`, merge/dedup, watertight checks. https://pypi.org/project/trimesh/ — **in-process core, approved license**.
- **manifold3d** — Apache-2.0, v3.5.2 (2026-06-27), `macosx_11_0_arm64` + universal2 wheels, py3.9-3.14, active. Guaranteed-manifold booleans, `Merge` for "slightly non-manifold" input (errors on truly non-manifold import), SDF `level_set` meshing. https://pypi.org/project/manifold3d/ — **in-process, approved**.
- **fast-simplification** — MIT, v0.2.0 (2026-08-12), macosx arm64 wheels py3.10-3.14; wraps Fast-Quadric-Mesh-Simplification; no documented UV/attribute preservation (acceptable — we decimate before UVs exist). https://pypi.org/project/fast-simplification/ — **in-process, approved**.
- **xatlas** (xatlas-python, mworchel) — MIT, v0.0.11 (2025-07-04), arm64 wheels cp38-cp313. https://pypi.org/project/xatlas/ — **in-process, approved** (same underlying library cumesh wraps for UVs).
- **libigl** python bindings — PyPI classifier MPL-2.0, v2.6.2 (2026-03-05), arm64 wheels; but the repo shows "GPL-3.0, MPL-2.0 licenses found" without documenting whether copyleft modules are compiled in (https://github.com/libigl/libigl-python-bindings). `fast_winding_number_for_meshes` went missing from the 2.6.0/2.6.1 PyPI wheels (libigl issue #2477); `topological_hole_fill` adds only one vertex per hole. **MPL-2.0 is off the MIT/BSD/Apache whitelist → excluded in-process by policy.**
- **Open3D** — MIT, but v0.19.0 (2025-01-08) still current (~19 months, no 0.20); wheels 72-103 MB, py3.8-3.12 only. License-clean but **heavy and slow-moving**; only justified if screened Poisson is needed.
- **pymeshlab** — GPL-3, v2025.7.post1 (2026-01-30), arm64 wheels, active. **Out-of-process only.**
- **pymeshfix** (MeshFix/Attene: watertighting, self-intersection + singularity repair) — GPL-3 (dual commercial), v0.18.1 (2026-04-23), arm64 wheels, PyVista-maintained. A Python import is in-process GPL linkage → **forbidden in-process; subprocess CLI only**.
- **VTK** — BSD-3, v9.7.0 (2026-08-15), arm64 wheels ~103 MB — license-clean but the weight buys nothing trimesh+manifold3d don't cover.
- **meshoptimizer** (PyPI) — MIT, but v0.2.30a0 pre-release (2026-02-27), **sdist only, no arm64 wheels**, published by "openorion" (not zeux). Not production-ready; its C++ `simplifyWithAttributes` stays attractive later but is UNVERIFIED in the Python binding.
- **MikkTSpace** — canonical C header is **zlib-licensed** (verified: https://github.com/mmikk/MikkTSpace/blob/master/mikktspace.h); the only Python wrapper found (`mikktpy`, unindexed-triangles-only) has no verified PyPI wheel. zlib is permissive but off-whitelist → vendoring needs one-line owner sign-off, or reimplement.
- **Blender** — GPL; blender.org/license confirms program output is not GPL-covered, while scripts using bpy must be GPL-compatible — one more reason the Blender lane stays a **separate out-of-process** service (as TEE already does). The PyPI `bpy` module is likewise GPL → never import in-process.
- **PoissonRecon** (Kazhdan screened Poisson) — MIT (https://github.com/mkazhdan/PoissonRecon); Open3D ships an implementation.

## Hole filling: algorithm options and tradeoffs

- **Boundary-loop triangulation (what cumesh does)** — detect open boundary loops, fill loops under a perimeter threshold (upstream: 3e-2 of the unit cube). Preserves existing geometry; new triangles get colors "for free" because the bake samples the voxel volume near the fill surface. Best fit: extraction holes are numerous but small. No permissive off-the-shelf Python does this well (trimesh's fan fill is convex-only; libigl's is policy-blocked and geometrically naive) → implement it: trimesh boundary-edge graph → loops → centroid-fan or ear-clip triangulation → local Laplacian smoothing of new vertices only. Small, MIT-clean, CPU-fast at these hole sizes.
- **Advancing-front fill** — best patch quality, but available implementations are GPL (MeshLab/pymeshlab, MeshFix). Out-of-process fallback only.
- **Voxel/SDF rebuild (manifold3d `level_set`, analogous to upstream's `remesh=True` DC branch)** — guaranteed watertight+manifold, resolves self-intersections and non-manifoldness in one op; destroys topology and any existing UVs and quantizes detail to voxel resolution. Acceptable **only before** UV unwrap/bake; the big-hammer path for badly broken meshes.
- **Screened Poisson (Open3D / PoissonRecon, MIT)** — global watertight rebuild from oriented points; needs normals; smooths sharp features; heaviest dependency. Last-resort fallback, not the default.
- **Winding-number repair** — the natural inside/outside oracle for voxel rebuilds; the maintained Python route is libigl (policy-blocked, and the function regressed out of recent wheels). manifold3d's SDF path avoids needing it. Skip for v1.

## Defect-class → repair-op mapping (recommended)

- Small open boundary loops (perimeter < ~3% bbox): in-house boundary-loop fill (MIT) — run pre-simplify, exactly like upstream `postprocess.py:110`.
- Duplicate/degenerate faces, unreferenced verts: trimesh `merge_vertices` + `update_faces(unique_faces/nondegenerate_faces)`.
- Small disconnected components: trimesh `split(only_watertight=False)` + cull below a relative-size threshold (mirror upstream's `remove_small_connected_components(1e-5)`).
- Inconsistent winding/normals: trimesh `fix_winding`/`fix_normals` (mirrors `unify_face_orientations`, `postprocess.py:162`).
- Slightly non-manifold edges: attempt manifold3d `Merge`; on failure either ship-with-warning (game engines tolerate it) or escalate to voxel rebuild.
- Large holes / self-intersections / hopeless topology: manifold3d `level_set` SDF rebuild at the generation resolution (512/1024), then continue the normal chain; report `repair_level: rebuilt` to the caller.
- Fragmented UVs: don't repair — regenerate with xatlas on the simplified mesh (tune `ChartOptions`/`PackOptions`); charts fragment far less at 200K-1M faces than on raw soup (trellis-mac already found xatlas "very slow on 800K+ vertex meshes", `generate.py:252`).
- Missing tangents for GLB normal-mapped workflows: MikkTSpace-conformant generation (vendored zlib C, pending sign-off) — UNVERIFIED: no maintained PyPI wheel found.

## Order of operations: repair BEFORE bake (the pipeline makes this natural)

- Because PBR data lives in the voxel attribute volume until export, **any mesh repair done before the `to_glb`-equivalent stage gets textures baked onto the repaired mesh automatically** — including hole-fill triangles, which sample plausible colors from the adjacent volume. There is no "repair after export" texture problem unless you bake first. Never repair post-GLB.
- Correct chain (mirrors upstream, with the two trellis-mac defects fixed): raw mesh → **(1) repair** (loop fill + cleanup, full res) → **(2) freeze full-res reference** (BVH/KD-tree on the repaired full-res mesh — what trellis-mac dropped) → **(3) simplify** working copy (fast-simplification, staged 3x-then-target like `postprocess.py:136-149`) → **(4) re-clean + fill** (decimation can open holes) → **(5) xatlas UV** → **(6) bake**: rasterize UV space (CPU numpy rasterizer as in `backends/texture_baker.py`, optional Metal/CUDA acceleration later), project texels to the full-res reference, trilinear-sample the attr volume (scipy cKDTree IDW is the proven CPU stand-in for `flex_gemm.grid_sample_3d`) → **(7) seam inpaint** (cv2 TELEA, as `postprocess.py:289-292`) → **(8) normals/tangents → GLB**.
- Decode-time `fill_holes` (`trellis2_image_to_3d.py:474`) can stay disabled on non-CUDA platforms; folding hole fill into step (1) of the export chain covers it with one implementation.

## In-process (product) vs TEE Blender lane

- In-process (MIT/BSD/Apache only): trimesh + manifold3d + fast-simplification + xatlas + scipy/numpy/opencv bake — the mesh stack adds a few MB of wheels (vs 70-103 MB for Open3D/VTK, which add no unique required capability).
- Out-of-process, existing TEE Blender lane keeps: Quadriflow retopology, Cycles mesh-to-mesh re-bake, artist-grade remesh/cleanup, anything GPL (pymeshlab filters, MeshFix CLI as an optional "deep repair" escalation). Do not duplicate these in-process.
- Boundary rule: the product's repair stage must make meshes *valid and bakeable*; the Blender lane makes them *pretty*. Validation/reporting (watertight, manifold, component count, hole count/perimeters — cheap with trimesh) belongs in-process and returns the compact diff-style summary TEE tools require.

## Implications for the build

- Adopt the dependency set: **trimesh (MIT) + manifold3d (Apache-2.0) + fast-simplification (MIT) + xatlas (MIT) + scipy/numpy/opencv**; all have verified arm64-macOS wheels (or are pure Python) and 2026 releases. Reject in-process: libigl (MPL-2.0 off-whitelist + GPL files in repo), pymeshfix/pymeshlab/bpy (GPL), Open3D/VTK (weight, no unique need), meshoptimizer PyPI (pre-release, no wheels).
- Implement one module, `repair.py`, exposing `repair(mesh, level=...) -> (mesh, report)` with three escalating levels: `fast` (dedup/degenerate/components/winding + boundary-loop fill, in-house MIT implementation with upstream's 3e-2 perimeter default), `manifold` (adds manifold3d Merge attempt + validation), `rebuild` (manifold3d SDF `level_set` at generation resolution — UV-destroying, so only ever pre-UV).
- Re-implement `to_glb` as the product's export pipeline in the order above, keeping upstream's two crucial structural ideas: repair-then-freeze the **full-res reference surface** for texel projection (fixes trellis-mac's naive pre-simplification defect), and staged simplify-clean-simplify (fixes decimation-opened holes).
- Bake path v1 is CPU (numpy UV rasterizer + cKDTree IDW volume sampling, already proven in trellis-mac's fallback); Metal/CUDA acceleration is an optimization slot, not a dependency — this is what makes the product platform-independent where upstream is CUDA-locked and trellis-mac is Metal-flaky.
- Tangents: vendor MikkTSpace C (zlib) behind a tiny cffi/pybind shim after a one-line license sign-off; until then export GLB without tangents (importers regenerate) and mark it in the repair report.
- Escalation hook: when in-process validation still fails after `rebuild`, emit a structured handoff to TEE's Blender lane rather than retrying — keeps tokens-per-task low and the GPL boundary clean.
