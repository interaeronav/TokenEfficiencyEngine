# Extraction Prior Art & Blender Handoff

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

Prior-art research for TEE Extract (Phase 7). Document pipelines: docling (MIT, IBM / LF AI) is the strongest permissive extractor for PDFs/tables/layout; unstructured (Apache-2.0) is lighter but weaker and increasingly platform-focused; marker is effectively unusable for TEE (GPL-3.0 code + revenue-capped model-weight license, 2–4 GB weights). None of the three understand architectural drawings — drawing vectorization is a separate ML niche (CubiCasa5K / Raster-to-Vector lineage) whose flagship dataset is CC BY-NC, so TEE should treat floor-plan raster recognition as an optional heavy lane and lean on vector sources (DXF via ezdxf, MIT) where possible.

Media MCP prior art converges on exactly TEE's thesis: extract-once to transcript/keyframes/OCR text, offer text-only tools with "no per-frame token cost".

The best Blender handoff is a two-tier path: (A) generate IFC offline with ifcopenshell (LGPL-3, pip-installable) from floor-plan JSON and open it in Bonsai (fka BlenderBIM, actively maintained on extensions.blender.org, works with Blender 4.0+ through 5.x, has a native walls-from-polylines tool), giving real BIM entities plus quantities for dimensional conformance; (B) a dependency-free fallback that extrudes wall polylines + Solidify in vanilla Blender (the FloorplanToBlender3d pattern).

For the floor-plan JSON schema, Floorplanner's FML v3 (open JSON: walls as centerline endpoints `a`/`b` + thickness + balance, openings parameterized by `t` ∈ 0–1 along the wall) is the closest precedent worth adopting rather than inventing a schema; export to IFC for interop. Content-addressed dedupe precedents beyond Flamenco Shaman: Unreal Cloud DDC, DVC's `files/md5/xx/rest` cache, and Sweet Home 3D's in-archive ContentDigests.

## Findings

### Docling (IBM) — capability and license

MIT license, IBM Research / LF AI & Data project. Extracts page layout, reading order, table structure (TableFormer model), code, formulas, image classification. Input formats: PDF, DOCX, PPTX, XLSX, HTML, EPUB, images (PNG/TIFF/JPEG), audio (WAV/MP3), email, LaTeX. Ships local models including the Granite-Docling VLM (258M params) — runs offline. Best-in-class permissive option for the PDF/document lane of TEE Extract.

Source: [docling GitHub](https://github.com/docling-project/docling) ; [docling.org](https://docling.org/) ; [arXiv:2408.09869v5](https://arxiv.org/html/2408.09869v5)

### Docling — architectural drawings

No evidence of architectural/technical-drawing understanding: the pipeline targets text documents (blocks = titles, paragraphs, tables, figures, footnotes); figures are exported/classified as images, not vectorized. A targeted search for docling + floor-plan support returned nothing. Conclusion: docling handles the "spec sheet PDF" lane, not the "drawing sheet" lane.

Source: [docling docs](https://docling.org/doc/) ; search returned no docling drawing-support results

### unstructured (Unstructured-IO) — capability, license, trajectory

Apache-2.0. Partitions PDFs/HTML/Word/images into typed elements (text, tables, metadata) with strategies `auto`/`fast`/`hi_res`/`ocr_only`; the user must self-manage Poppler/Tesseract system deps. The company is steering toward its paid platform: the open-source lib is documented as "not designed for production scenarios" with "significantly decreased performance on document and table extraction" vs the API, and no access to their latest VLM models. Usable but second choice to docling.

Source: [unstructured GitHub](https://github.com/Unstructured-IO/unstructured) ; [unstructured open-source docs](https://docs.unstructured.io/open-source/introduction/overview)

### marker (Datalab) — license blocker

Code is GPL-3.0 AND the surya model weights use a modified OpenRAIL-M license: free only for research/personal use and startups under $2M revenue; larger commercial use needs a paid datalab.to license. Weights are ~2–4 GB, downloaded on first run. Converts PDF/DOCX/PPTX/XLSX/EPUB/HTML/images to markdown+JSON via layout + reading-order + table models. Verdict for MIT-licensed TEE: exclude, or at most document as an optional user-installed backend.

Source: [marker GitHub](https://github.com/datalab-to/marker) ; [PyPI marker-pdf](https://pypi.org/project/marker-pdf/)

### Media/video MCP servers — existing landscape

Multiple servers already implement "extract once, return text":

- media-mcp (woosal1337): local Whisper transcription + frame extraction at configurable FPS, 29 tools.
- video-vision-mcp (OAMaestro): scene-change detection to extract only frames that matter, timestamps burned into frames, CPU Whisper.
- mcp-video-analyzer (guimatheus92): transcripts, key frames, OCR text, metadata — explicitly advertises text-only tools with "no frame images and no per-frame token cost".
- video-watch-mcp (Modal cloud): yt-dlp + ffmpeg + whisper.
- mcpVideoParser: 14 tools — frames, motion analysis, scene detection, annotation, transcription.

Lesson: the convergent design = transcript + sparse keyframes + OCR + metadata, with text-first defaults; TEE's contribution is persisting these as content-addressed facts rather than re-running per conversation.

Source: [media-mcp](https://github.com/woosal1337/media-mcp) ; [video-vision-mcp](https://github.com/OAMaestro/video-vision-mcp) ; [mcp-video-analyzer](https://github.com/guimatheus92/mcp-video-analyzer) ; [video-watch-mcp](https://github.com/codependentai/video-watch-mcp) ; [mcpVideoParser](https://github.com/michaelbaker-dev/mcpVideoParser)

### OCR / document MCP servers

OCR MCPs are thin engine wrappers: mcp-ocr (rjn32s; Tesseract; two tools: `perform_ocr` + `get_supported_languages`), dangvinh/mcp-ocr-server (native C++ Tesseract via Node), sandraschi/ocr-mcp (multi-backend GOT-OCR2.0/Tesseract/EasyOCR with layout-preservation modes), labeveryday/mcp_pdf_reader (FastMCP; text + image extraction + OCR). Microsoft's MarkItDown MCP server (MIT, library + server) converts 29+ formats to markdown fully locally — the closest existing "convert once for LLM" MCP, but stateless: it re-converts per call and has no fact store or media beyond documents. Gap TEE fills: persistence + dedupe + domain-specific (dimensional) extraction.

Source: [mcp-ocr](https://github.com/rjn32s/mcp-ocr) ; [mcp-ocr-server](https://github.com/dangvinh/mcp-ocr-server) ; [ocr-mcp on LobeHub](https://lobehub.com/mcp/sandraschi-ocr-mcp) ; [MarkItDown on PulseMCP](https://www.pulsemcp.com/servers/markitdown)

### Photogrammetry / scan-to-BIM commercial landscape (positioning)

Polycam: LiDAR + photogrammetry capture, ~0.5 inch tolerance on interior scans, one-pass scan → 2D floor plan ("Space Mode"), 12+ export formats (OBJ/FBX/GLTF/PDF); scan-to-BIM via a Transform Engine partnership — human-in-the-loop conversion, AutoCAD layouts from $95, Revit models from $200. Luma AI: NeRF/gaussian-splat 3D from ordinary photos/video only (no LiDAR), oriented to visuals not BIM. Open-source photogrammetry (COLMAP ~BSD, Meshroom/AliceVision MPL-2.0 — from general knowledge) produces meshes/point clouds, not semantic walls. Positioning: nobody in this market converts drawings + photos into compact structured FACTS for an LLM; they produce heavy geometry. TEE Extract should claim "facts, not meshes" and explicitly not compete on reality capture.

Source: [AEC Magazine on Polycam](https://aecmag.com/reality-capture-modelling/polycam-for-aec/) ; [Polycam floor plan pipeline](https://poly.cam/blog/how-we-turn-raw-spatial-data-into-a-floor-plan-you-can-build-from-inside-polycams-floor-plan-pipeline) ; [Luma AI overview](https://www.thefuture3d.com/software/luma-ai/)

### Bonsai (fka BlenderBIM) — status and compatibility

Renamed BlenderBIM → Bonsai. Distributed on extensions.blender.org; current v0.8.5-post1 (docs at docs.bonsaibim.org 0.8.5, unstable 0.8.6); v0.8.4+ requires Blender 4.0+ and works with Blender 5.0. GPL licensed, IFC-native (edits IFC data directly via ifcopenshell inside Blender). Recent feature: "walls from polylines" — draw wall axes as polylines and Bonsai generates IFC walls with layer-offset baseline cycling (Exterior → Centreline → Interior). This is the premium handoff target for TEE floor-plan JSON.

Source: [Bonsai on extensions.blender.org](https://extensions.blender.org/add-ons/bonsai/) ; [docs.bonsaibim.org](https://docs.bonsaibim.org/) ; [creating walls guide](https://docs.bonsaibim.org/guides/authoring/basic_modeling/creating_walls.html) ; [walls-from-polylines demo video](https://www.youtube.com/watch?v=2Uqj2sORVcg)

### Programmatic IFC wall creation (offline, no Blender needed)

ifcopenshell python (LGPL-3.0+, `pip install ifcopenshell`, Python 3.9–3.12) can build walls headlessly: `ifcopenshell.api.root.create_entity(model, ifc_class='IfcWall')` + an axis polyline representation (`createIfcPolyLine` over 2D points, ShapeRepresentation `'Axis'`/`'Curve2D'`) + `ifcopenshell.api.geometry.add_footprint_representation` / `assign_representation` for the body. LGPL is compatible with an MIT server using it as a dependency (and Bonsai's GPL never touches TEE since Blender runs in a separate process). This enables: extracted floor-plan JSON → IFC file written offline at zero token cost → imported/opened in Bonsai as real BIM with Qto quantities for dimensional conformance checking.

Source: [ifcopenshell geometry creation](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html) ; [ifcopenshell.api.geometry](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/index.html) ; [PyPI ifcopenshell](https://pypi.org/project/ifcopenshell/) ; [IfcOpenShell Academy: simple wall](https://academy.ifcopenshell.org/posts/creating-a-simple-wall-with-property-set-and-quantity-information/)

### LLM-driven Bonsai prior art (directly relevant)

1. Bonsai_mcp (JotaDeRodriguez, MIT): a fork of BlenderMCP adding 14+ IFC tools (entity listing, property/spatial queries, relationship analysis, JSON/CSV export, object placement, 2D/3D drawing export) via a JSON-over-TCP socket to a Blender addon, leveraging Bonsai's ifcopenshell — validates TEE's socket + escape-hatch architecture.
2. ProfRino/bonsai-bim-skills (GPL-3.0, Blender 5.1+ / Bonsai 0.8.5+): 7 Claude Code skills for programmatic IFC authoring (walls with mitered corners, openings via `IfcRelVoidsElement`/`IfcRelFillsElement`, roofs via `IfcBooleanClippingResult`/`IfcHalfSpaceSolid`, stairs, `IfcSpace`/`IfcGrid`, project setup with IDS validation, SVG drawings) using `bpy.ops.bim.*` — "~50 hard-won rules" in `docs/lessons-learned.md`; tiny/early (0 stars, 10 commits) but the closest thing to TEE's wall-authoring lane.

Source: [Bonsai_mcp](https://github.com/JotaDeRodriguez/Bonsai_mcp) ; [bonsai-bim-skills](https://github.com/ProfRino/bonsai-bim-skills)

### Blender DXF import status

The bundled `io_import_dxf` add-on was removed from core in Blender 4.2 (bundled only through 4.1) and now lives on extensions.blender.org as a community-maintained extension ("offered as is... no support expected"), with multiple open bug reports in 4.2+. Implication: TEE should NOT depend on Blender's DXF importer; instead parse DXF server-side with ezdxf (MIT, pure Python 3.9+, OS-independent, headless, read/write DXF R12–R2018, entity query API `modelspace.query('LINE[layer=="walls"]')`, `groupby(layer)`) and emit floor-plan JSON / IFC.

Source: [DXF extension on extensions.blender.org](https://extensions.blender.org/add-ons/import-autocad-dxf-format-dxf/) ; [Blender issue #125166](https://projects.blender.org/blender/blender/issues/125166) ; [ezdxf.mozman.at](https://ezdxf.mozman.at/) ; [ezdxf docs](https://ezdxf.readthedocs.io/)

### Parametric-wall add-ons (Archipack, Sverchok) — assessment

Archipack: parametric wall/roof/window primitives with a preset system; the free 1.2.8x branch is GPL-3, the current 2.x branch is commercial (€49) supporting Blender 3.x/4.x/5.x — commercial licensing + UI-oriented operators make it a poor scripted-handoff target. Sverchok: powerful GPL node-based parametric geometry add-on, supports Blender 2.8/3.6/4.5/5.1 but has a history of breakage across 4.x releases (crash issues #5160, #5175) — too fragile as a dependency. Verdict: prefer Bonsai/IFC (semantic) or vanilla-Blender polyline-extrude + Solidify (zero add-on deps); Geometry Nodes curve-to-mesh is a middle option using only core Blender.

Source: [Archipack features](https://blender-archipack.org/features) ; [Archipack wiki](https://github.com/s-leger/archipack/wiki) ; [Sverchok](https://github.com/nortikin/sverchok) ; [Sverchok issue #5160](https://github.com/nortikin/sverchok/issues/5160)

### FloorplanToBlender3d — wall-from-image precedent

grebtsew/FloorplanToBlender3d (GPL-3.0 per the repo) detects walls/floors/rooms from floor-plan images with OpenCV (contour detection in `detect_walls.py`), writes intermediate data files (`generate.py`: "temporary storage of calculated data and a way to transfer data to the blender script"), then a Blender-side script builds meshes — i.e., it already uses TEE's pattern of a serialized intermediate between detection and Blender, but its intermediate is ad-hoc verts/faces, not semantic walls with thickness/openings, and detection is classical CV (brittle on real drawings). Related: Moni-King-Dev/3DFloorplanner uses Gemini Vision → structured JSON blueprint (walls + rooms) → Three.js — evidence the VLM-to-JSON lane works but is per-call token-priced, which is exactly what TEE amortizes. Also daviddemeij/fml2blender converts Floorplanner FML → Blender scenes.

Source: [FloorplanToBlender3d](https://github.com/grebtsew/FloorplanToBlender3d) ; [3DFloorplanner](https://github.com/Moni-King-Dev/3DFloorplanner) ; [fml2blender](https://github.com/daviddemeij/fml2blender)

### Content-addressed store precedents beyond Flamenco Shaman

1. Unreal Cloud DDC: derived data keyed by content hash in a "content-addressable store that can be replicated across the world"; a hierarchy of caches fast → slow consulted in order; stores expensive-to-recompute derivations (shader compiles, texture compressions) — the exact analogue of TEE storing expensive extractions keyed by source-media hash.
2. DVC: `.dvc/cache/files/md5/<first-2-chars>/<remaining-30>`, flat 2-char fanout, one depth level; directories stored as `.dir` manifest objects.
3. Sweet Home 3D `.sh3d` archives embed a ContentDigests entry holding SHA-1 hashes of contained images/models — content digests inside a project container for integrity/dedupe.
4. git-lfs/git-annex use the same sha256 2-level fanout pattern (general knowledge).

Pattern to copy: hash source media once → key both the blob and every derived fact-set by `(source_hash, extractor_id, extractor_version)` so re-extraction is a cache hit.

Source: [Unreal DDC docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-derived-data-cache-in-unreal-engine) ; [DVC internal files](https://doc.dvc.org/user-guide/project-structure/internal-files) ; [SH3D on Just Solve](http://justsolve.archiveteam.org/wiki/SH3D)

### Floor-plan JSON schema precedent #1 — Floorplanner FML v3 (recommended base)

Open JSON format ("FML is an open format... to exchange data between Floorplanner and other software"). Hierarchy: Project → Floor → Design (floorplan); units centimeters, screen-style Y-down. Wall = centerline endpoints `a`/`b` `{x,y}` + `az`/`bz` `{z: bottom, h: top elevation}` + `thickness` + `balance` (0–1 split of thickness left/right of the centerline) + optional quadratic-bezier control `c` + an `openings` array. Opening (door/window) = `refid` (asset id), `width`, `z`, `z_height`, `t` (0–1 parametric position along the wall) — parametric position on a wall is exactly the right representation for dimensional conformance. Areas/rooms = `poly` point array on wall edges + `name`. This is the most adoption-worthy schema shape for TEE's `floor_plan.json`; tooling exists (fml2blender).

Source: [FML v3.0 specification](https://floorplanner.readme.io/reference/v30-specification) ; [floorplanner.com/fml](https://floorplanner.com/fml) ; [Floorplanner FML help article](https://help.floorplanner.com/en/articles/8435278-what-is-fml-how-to-use-fml)

### Floor-plan schema precedent #2 — CubiCasa5K (license-poisoned for models, useful as taxonomy)

5000 floor plans annotated as SVG polygons across 80+ categories (rooms, icons including windows/doors/fixtures, structural: walls/railings/stairs); annotation order walls → rooms → icons. The dataset license is CC BY-NC 4.0 (non-commercial) — models trained on it carry NC taint, so TEE cannot ship such weights under MIT; its category taxonomy and wall-polygon-first convention are still worth borrowing. The baseline model follows Raster-to-Vector (junction detection + integer programming) with a multi-task uncertainty loss, outputting segmentation tensors + junction heatmaps.

Source: [CubiCasa5K](https://github.com/CubiCasa/CubiCasa5k) ; [CubiCasa5K LICENSE](https://github.com/CubiCasa/CubiCasa5k/blob/master/LICENSE) ; [CubiCasa5K paper](https://dl.acm.org/doi/10.1007/978-3-030-20205-7_3)

### Floor-plan schema precedent #3 — Sweet Home 3D and IFC

Sweet Home 3D `.sh3d` = a ZIP containing `Home.xml` (since v5.3, DTD `SweetHome3D.dtd`; walls with start/end points, thickness, height in an XML home description) plus numbered OBJ/MTL/JPEG resources and ContentDigests — a complete, GPL-ecosystem home-description format but XML/desktop-app-centric. IFC (via ifcopenshell) remains the only interop-grade target: walls as `IfcWall` with Axis (`Curve2D` polyline) + Body representations, openings via `IfcRelVoidsElement`/`IfcRelFillsElement`, quantities in `Qto_WallBaseQuantities`. Recommended stance: FML-shaped internal JSON, IFC as the export/conformance layer, don't invent a third geometry vocabulary.

Source: [SH3D on Just Solve](http://justsolve.archiveteam.org/wiki/SH3D) ; [Sweet Home 3D 5.3 blog](https://www.sweethome3d.com/blog/sweet-home-3d-5-3/) ; [ifcopenshell geometry creation](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)

### Raster floor-plan recognition research lane (if TEE ever adds an ML drawing lane)

Lineage: Raster-to-Vector (junction heatmaps + integer programming; 870 vector annotations), DeepFloorplan (multi-task net with room-boundary-guided attention, arXiv:1908.11025), CVPR 2021 Residential Floor Plan Recognition and Reconstruction, GNN line-segment parsing (arXiv:2303.03851), YOLOv5+DRN+OCR hybrid pipelines (arXiv:2408.01526). Common architecture: split into wall segmentation + symbol detection + OCR of dimension text, then combinatorial post-processing to vectors. No permissively-licensed, production-grade open model emerged from search; most repos are research code with unclear/NC data. This supports making the raster-drawing lane a pluggable optional extractor, with the VLM-assisted path (structured JSON out, like 3DFloorplanner) as the pragmatic default for one-time extraction.

Source: [arXiv:1908.11025](https://arxiv.org/pdf/1908.11025) ; [CVPR 2021 paper](https://openaccess.thecvf.com/content/CVPR2021/papers/Lv_Residential_Floor_Plan_Recognition_and_Reconstruction_CVPR_2021_paper.pdf) ; [arXiv:2408.01526](https://arxiv.org/html/2408.01526v1) ; [FloorPlanParser](https://github.com/TINY-KE/FloorPlanParser)

## Recommendations for TEE

1. Document lane: adopt docling (MIT) as the primary PDF/document extractor; skip unstructured (weaker, platform-drifting) and exclude marker entirely (GPL-3 code + revenue-capped OpenRAIL-M weights conflict with TEE's MIT posture).
2. CAD lane: parse DXF server-side with ezdxf (MIT, headless, R12–R2018) and never rely on Blender's DXF importer, which was unbundled in 4.2 and is community-maintained with open bugs.
3. Blender handoff, tier 1: floor-plan JSON → generate IFC offline with ifcopenshell (LGPL, pip; `IfcWall` with Axis polyline + body, openings via `IfcRelVoidsElement`/`IfcRelFillsElement`) → open in Bonsai (works Blender 4.0–5.x). This yields semantic walls plus Qto quantities for dimensional conformance checking at zero token cost; study ProfRino/bonsai-bim-skills for the ~50 IFC authoring pitfalls and Bonsai_mcp (MIT) for the socket/tool architecture.
4. Blender handoff, tier 2 (no add-ons): wall-centerline polyline → curve/mesh extrude + Solidify (or Geometry Nodes curve-to-mesh) in vanilla Blender via TEE's existing `run_python` escape hatch — the FloorplanToBlender3d pattern, but driven from semantic JSON instead of raw CV contours. Avoid Archipack (commercial 2.x) and Sverchok (fragile across Blender releases) as dependencies.
5. Schema: do not invent a floor-plan JSON schema. Base it on Floorplanner FML v3 wall semantics (centerline `a`/`b`, thickness, balance, openings with parametric `t` along the wall, rooms as polygons) — this maps 1:1 onto both Bonsai's walls-from-polylines tool and `IfcWall` axis representations; keep IFC as the export/interop layer and borrow CubiCasa5K's category taxonomy (but never its NC-licensed data/weights).
6. Fact store: key extractions by `(source_media_hash, extractor_id, extractor_version)` with a 2-char fanout directory layout (DVC `files/md5` pattern); model it as a derived-data cache in the Unreal DDC sense (source hash → expensive derivation cached forever), which also gives free dedupe when the same drawing arrives via multiple paths.
7. MCP design: mirror the convergent video-MCP pattern — text-first tools (facts, transcript, dimensions) as defaults, image/frame retrieval as explicit opt-in — and position TEE Extract against MarkItDown-style stateless converters as "extract once, persist facts, never re-bill the media"; against Polycam/Luma as "facts and BIM entities, not meshes" (photogrammetry is out of scope, IFC import of their exports is the integration point).
8. Raster drawing recognition: make it a pluggable optional lane. Default to one-time VLM-assisted extraction into the FML-shaped JSON (amortized by the fact store); treat CubiCasa/DeepFloorplan-class local models as future optional extractors since no permissive production-grade open model exists today.
