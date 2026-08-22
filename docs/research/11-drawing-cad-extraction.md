# Architectural Drawing & CAD Extraction

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

For deterministic extraction of architectural source material, the license-clean Python 3.11 stack is: `pdfplumber` 0.11.10 (MIT, built on `pdfminer.six`) for vector PDF lines/rects/text-with-coordinates, `pypdfium2` 5.13.0 (Apache-2.0/BSD-3) for rasterization and fast text, `ezdxf` 1.4.4 (MIT) for DXF including true `DIMENSION` measurements and `$INSUNITS` handling, and `ifcopenshell` 0.8.5 (LGPL-3.0+, pip wheels for py3.10–3.14) for IFC/BIM with world-coordinate meshes and unit scaling. PyMuPDF is AGPL-3.0/commercial dual-licensed and should be excluded from an MIT server.

The scanned-raster-floorplan ML landscape is a licensing minefield: CubiCasa5K is CC BY-NC 4.0 (code and dataset), the DeepFloorplan lineage is GPL-3.0, and nothing is both pip-installable and maintained — so the raster path should be classical OpenCV (Apache-2.0) wall-mask heuristics plus OCR (`pytesseract`/tesseract, Apache-2.0; RapidOCR, Apache-2.0, for rotated dimension text) with scale calibrated from OCR'd dimension strings, falling back to title-block scale plus ISO 216 paper size.

Vector-vs-scanned detection is a cheap deterministic check on pdfplumber's object lists. All of this runs local/offline at zero token cost.

## Findings

### pdfplumber (vector PDF workhorse)

`pdfplumber` 0.11.10, MIT, requires-python `>=3.8`, built on `pdfminer.six`. Per-page object lists with coordinates:

- `page.lines` / `page.rects` / `page.curves` — each dict has `x0`, `x1`, `y0`, `y1`, `top`, `bottom`, `width`, `height`, `linewidth`, `stroking_color`; curves add `pts` and `path`.
- `page.edges` / `rect_edges` / `curve_edges` — decomposed edges.
- `page.chars` — per-char text, `fontname`, `size`, coordinates.
- `page.images` — `x0`/`x1`/`top`/`bottom`, `srcsize`, `colorspace`, `bits`, `name`, raw stream.

Text with boxes: `page.extract_words(x_tolerance, y_tolerance, extra_attrs, return_chars)` returns a list of dicts with bounding boxes; `page.extract_text(layout=True)`; `page.search(regex)` returns matches with coordinates. Explicitly "works best on machine-generated, rather than scanned, PDFs"; no OCR built in. Coordinates are in PDF points (1/72 inch), origin-normalized via `top`/`doctop`.

Source: [github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber); [PyPI pdfplumber JSON](https://pypi.org/pypi/pdfplumber/json)

### pdfminer.six (pdfplumber's foundation)

`pdfminer.six` version 20260107 on PyPI, MIT, requires-python `>=3.10`. Usable directly (`LTPage`/`LTLine`/`LTRect`/`LTTextLine` layout objects) but pdfplumber's API is the ergonomic wrapper; no reason to use both.

Source: [PyPI pdfminer.six JSON](https://pypi.org/pypi/pdfminer.six/json)

### PyMuPDF license trap

PyMuPDF 1.28.2 is "Dual Licensed - GNU AFFERO GPL 3.0 or Artifex Commercial License" (requires-python `>=3.10`). Its API (`page.get_drawings()`, `page.get_text('words')`) is convenient, but AGPL is viral over network use — incompatible with TEE's MIT server unless a commercial license is bought. Recommend hard-excluding it.

Source: [PyPI PyMuPDF JSON](https://pypi.org/pypi/PyMuPDF/json)

### pypdfium2 (AGPL-free renderer/text alternative)

`pypdfium2` 5.13.0, licensed Apache-2.0 OR BSD-3-Clause (PDFium itself is BSD-style); binary wheels bundle Google's PDFium. API:

- `pdf = pdfium.PdfDocument(path)`; `page.render(scale=N)` → `bitmap.to_pil()` / `.to_numpy()` (`scale=1` is 72 dpi, so `scale=4.17` ≈ 300 dpi for OCR).
- `textpage = page.get_textpage()`; `textpage.get_text_bounded(left, bottom, right, top)`, `get_text_range(index, count)`.
- `page.get_objects()` yields objects with `.level`, `.type`, `.get_bounds()` (type + bbox only — full path geometry is pdfplumber's job).

Best used as the rasterizer feeding OCR/OpenCV for scanned pages.

Source: [pypdfium2 readme](https://pypdfium2.readthedocs.io/en/stable/readme.html); [PyPI pypdfium2 JSON](https://pypi.org/pypi/pypdfium2/json)

### Vector vs scanned page detection (deterministic idiom)

Cheap per-page classifier from pdfplumber object counts: a scanned page has `len(page.chars) == 0` (or only OCR-layer text), few/no lines-rects-curves, and one `page.images` entry whose bbox covers roughly the whole mediabox (compare image `x0`/`x1`/`top`/`bottom` area to `page.width * page.height`, threshold ~0.8). A born-vector CAD export has hundreds of lines/rects and real chars. Hybrid pages (vector title block + raster scan) are caught by checking both conditions per region. This costs zero tokens and routes each page to the vector path or the raster/OCR path.

Source: Derived directly from pdfplumber's documented `page.chars`/`page.images`/`page.lines` APIs ([github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber))

### Dimension annotations from vector PDFs

CAD-exported PDFs have no semantic dimension entities — dimensions flatten to text + leader/extension lines. Practical recovery: regex over `page.extract_words()` output for dimension strings (e.g. `r"\d+(?:[.,]\d+)?\s*(?:mm|cm|m)?"` and feet-inches `r"\d+'-?\d+(?:\s*\d+/\d+)?\""`), then associate each matched word bbox with the nearest parallel line in `page.lines` to get (text value, measured segment length in points) pairs — these pairs drive scale inference. pdfplumber's `page.search()` returns regex matches with coordinates in one call.

Source: pdfplumber API ([github.com/jsvine/pdfplumber](https://github.com/jsvine/pdfplumber)); association heuristic is design guidance

### ezdxf core

`ezdxf` 1.4.4, MIT, requires-python `>=3.10` — the canonical pure-Python DXF reader/writer. Idioms:

- `doc = ezdxf.readfile(path)` (catch `ezdxf.DXFStructureError`); `msp = doc.modelspace()`.
- Entity query language: `msp.query('LWPOLYLINE')`, `msp.query('LINE[layer=="construction"]')`, boolean attribute filters; `msp.groupby(dxfattrib='layer')` → `{layer: [entities]}`.
- Attributes via `e.dxf.layer`; safe access `e.dxf.get('attr', default)`, `e.dxf.hasattr()`.
- `ezdxf.bbox.extents(msp)` for drawing extents.

DXF only — DWG is not parsed natively.

Source: [ezdxf getting-data tutorial](https://ezdxf.readthedocs.io/en/stable/tutorials/getting_data.html); [PyPI ezdxf JSON](https://pypi.org/pypi/ezdxf/json)

### ezdxf LWPOLYLINE (wall outlines)

Point access: `pline[0]` → 5-tuple `(x, y, start_width, end_width, bulge)`; `pline.get_points(format)` with format codes `x`, `y`, `s`, `e`, `b`, `v` — common `'xy'`, `'xyb'`; `with pline.points('xyseb') as pts:` context manager for editing; `pline.closed` flag; `pline.vertices_in_wcs()` converts OCS→WCS. Bulge = sagitta/(half chord); 1 = semicircle; sign = curve direction; applies from a vertex to the next. Helper functions exist for bulge-to-arc conversion (`ezdxf.math`).

Source: [ezdxf LWPOLYLINE tutorial](https://ezdxf.readthedocs.io/en/stable/tutorials/lwpolyline.html)

### ezdxf DIMENSION entities (ground-truth measurements)

`DIMENSION` dxf attrs: `defpoint`/`defpoint2`/`defpoint3`/`defpoint4` (WCS); `dxf.text` (`''` or `'<>'` = show measured value, `' '` = suppressed, else manual override — overrides can lie, prefer measured); `dxf.dimtype` codes: 0 linear/rotated, 1 aligned, 2 angular, 3 diameter, 4 radius, 5 angular-3pt, 6 ordinate, 8 arc (plus bit flags 32/64/128); `dxf.angle` for rotated linear.

`dim.get_measurement()` returns the true numeric measurement (float for linear/angular; `Vec3` for ordinate) computed from defpoints — this is the highest-quality dimensional fact in any source format short of IFC. `dim.virtual_entities()` / `get_geometry_block()` expose the rendered TEXT/LINE/ARC primitives if needed.

Source: [ezdxf DIMENSION docs](https://ezdxf.readthedocs.io/en/stable/dxfentities/dimension.html)

### ezdxf units / $INSUNITS

DXF coordinates are inherently unitless; unit meaning comes from the `$INSUNITS` header: read via `doc.header['$INSUNITS']` or `doc.units`. Codes: 0=unitless (very common in the wild — must trigger a fallback/ask), 1=inches, 2=feet, 4=mm, 5=cm, 6=m, 7=km, 10=yd, 14=dm; enums in `ezdxf.units` (`units.MM`, `units.M`, `units.IN`, ...). `units.conversion_factor(source, target)` gives the multiplier; `$MEASUREMENT` (0=English, 1=Metric) is a secondary hint; `$LUNITS` is display-only.

Blocks have their own units attribute and no implicit conversion happens on INSERT — scaling must be applied explicitly (`block_ref.set_scale`). For INSERT/block extraction, `insert.virtual_entities()` yields transformed primitives.

Source: [ezdxf units concepts](https://ezdxf.readthedocs.io/en/stable/concepts/units.html)

### DWG ingestion via ezdxf odafc addon

`ezdxf.addons.odafc` wraps the external, freeware-but-proprietary ODA File Converter (separate install; Win/macOS/Linux): `odafc.readfile('plan.dwg')` converts DWG/DXB → temp DXF → ezdxf document; also `odafc.export_dwg()` and `odafc.convert()`; supports R12 through R2018 (`'AC1032'`). Docs warn executing an external app is a security issue. So: DXF native, DWG only via optional user-installed converter — document as an optional adapter, don't hard-depend.

Source: [ezdxf odafc addon docs](https://ezdxf.readthedocs.io/en/stable/addons/odafc.html)

### ifcopenshell install/license

`ifcopenshell` 0.8.5 on PyPI, `pip install ifcopenshell` with prebuilt wheels; requires-python `>=3.10,<3.15` (3.10–3.14, so a 3.11 server is fine); Linux/Windows/macOS wheels. License: LGPL-3.0-or-later (OSI classifier) — usable as an unmodified pip dependency of an MIT server, but cannot be vendored/statically merged; note in NOTICE file.

Source: [ifcopenshell installation docs](https://docs.ifcopenshell.org/ifcopenshell-python/installation.html); [PyPI ifcopenshell JSON](https://pypi.org/pypi/ifcopenshell/json)

### ifcopenshell extraction API

`model = ifcopenshell.open('x.ifc')`; `model.by_type('IfcWall')` / `'IfcSpace'` / `'IfcDoor'` / `'IfcWindow'` (subtypes included), `by_guid()`, `by_id()`. Geometry:

- `settings = ifcopenshell.geom.settings()`; `shape = ifcopenshell.geom.create_shape(settings, element)`.
- `shape.geometry.verts` (flat `[x, y, z, ...]`), `.edges`, `.faces` (triangles), `.materials`.
- 4x4 placement matrix via `shape.transformation.matrix` or `ifcopenshell.util.shape.get_shape_matrix(shape)` (translation = `matrix[:,3][0:3]`); helpers `ifcopenshell.util.shape.get_vertices`/`get_edges`/`get_faces`.
- Bulk: `ifcopenshell.geom.iterator(settings, model, multiprocessing.cpu_count(), include=walls)` with an `initialize()`/`next()` loop.

Doors/windows carry `OverallHeight`/`OverallWidth` attributes; property sets via `ifcopenshell.util.element.get_psets(element)` (e.g. `Qto_WallBaseQuantities`). This is the richest source format — semantic walls/spaces with true placements; prefer it whenever the user has IFC.

Source: [ifcopenshell geometry processing docs](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html)

### ifcopenshell units

IFC files declare project length units (often mm); normalize everything to meters (Blender's unit) with `unit_scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)` and multiply raw attribute values (e.g. `radius_m = circle.Radius * unit_scale`). Geometry from `create_shape` is already unit-scaled per settings.

Source: [ifcopenshell geometry processing docs](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html)

### Scanned floorplan ML: CubiCasa5K — license blocked

`github.com/CubiCasa/CubiCasa5k`: multi-task PyTorch net (based on Raster-to-Vector) producing wall-junction heatmaps plus room-type and icon (door/window) segmentation, post-processed to polygons; 5000 plans, 80+ object categories, SVG annotations. LICENSE is Creative Commons Attribution-NonCommercial 4.0 (verified from raw LICENSE file) covering the repo — non-commercial, incompatible with an MIT-distributed, commercially usable server. Also effectively unmaintained (13 commits, PyTorch 1.0.0 / Python 3.6.5 / OpenCV 3.1.0 pins), not pip-installable, ~105 GB preprocessed LMDB. Do not vendor; at most an optional user-installed plugin.

Source: [github.com/CubiCasa/CubiCasa5k](https://github.com/CubiCasa/CubiCasa5k); [raw LICENSE file](https://raw.githubusercontent.com/CubiCasa/CubiCasa5k/master/LICENSE)

### Scanned floorplan ML: DeepFloorplan lineage — GPL + stale

`zlzeng/DeepFloorplan` is TensorFlow 1.x, unmaintained. The modern port `zcemycl/TF2DeepFloorplan` (TF2, "Deep Floor Plan Recognition using Room-boundary-Guided Attention") is GPL-3.0 (verified LICENSE) and installs only via `pip install -e .` from a clone, not from PyPI. GPL-3.0 code cannot be linked into an MIT server without relicensing implications. Community consensus (e.g. `mageaustralia/FloorPlanAnalyzer`, which tried traditional CV + YOLOv8 + CubiCasa5K) is that none achieve fully reliable room detection across diverse plan styles. Conclusion: there is no maintained, permissively-licensed, pip-installable floorplan-recognition model as of Aug 2026.

Source: [TF2DeepFloorplan LICENSE](https://github.com/zcemycl/TF2DeepFloorplan/blob/main/LICENSE); [github.com/zlzeng/DeepFloorplan](https://github.com/zlzeng/DeepFloorplan); [github.com/mageaustralia/FloorPlanAnalyzer](https://github.com/mageaustralia/FloorPlanAnalyzer)

### Classical OpenCV raster pipeline (permissive, offline)

`opencv-python-headless` 5.0.0.93 (OpenCV 5.0), Apache-2.0, py `>=3.6` — fully permissive. Proven wall-extraction recipe (as used by FloorplanToBlender3d, GPL-3.0, so reimplement the technique, don't copy code):

1. Grayscale → adaptive/Otsu threshold → morphological close/open (walls are the thickest dark strokes; erode-by-N to isolate them and estimate wall thickness from stroke width).
2. `cv2.findContours` / `cv2.connectedComponents` for rooms as enclosed regions.
3. `cv2.HoughLinesP` or `cv2.createLineSegmentDetector` / ximgproc `FastLineDetector` (opencv-contrib) for wall centerlines.
4. Gaps in wall strokes + arc marks = door/window candidates.

Deterministic, zero-token, and its outputs (wall segments with thickness, room polygons) map directly onto the same compact fact schema as the DXF path.

Source: [PyPI opencv-python-headless JSON](https://pypi.org/pypi/opencv-python-headless/json); [github.com/grebtsew/FloorplanToBlender3d](https://github.com/grebtsew/FloorplanToBlender3d) (GPL-3.0, approach reference only)

### OCR for dimension text: tesseract/pytesseract

`pytesseract` 0.3.13, Apache-2.0, py `>=3.8`; wraps the tesseract-ocr engine (Apache-2.0, `apt-get install tesseract-ocr` on Debian/Ubuntu — fully offline). Key idiom: `pytesseract.image_to_data(img, output_type=Output.DICT)` returns word-level `left`/`top`/`width`/`height` + `conf` for box-anchored dimension strings; restrict charset with `config='-c tessedit_char_whitelist=0123456789.,mx'` for dimension lanes. Weakness: rotated text — dimension labels along vertical walls need 90-degree crop rotation passes or a rotation-aware detector.

Source: [PyPI pytesseract JSON](https://pypi.org/pypi/pytesseract/json)

### OCR alternative: RapidOCR

RapidOCR (`RapidAI/RapidOCR`), Apache-2.0, package `rapidocr` 3.9.2 (`pip install rapidocr onnxruntime`), py `>=3.8`; ONNX conversions of PaddleOCR PP-OCR models (det = DBNet + angle cls + rec), also OpenVINO/MNN/TensorRT/PyTorch backends. API: `from rapidocr import RapidOCR; engine = RapidOCR(); result = engine(img)` → boxes (quadrilaterals, handles rotated text), texts, scores. Actively maintained (7.6k stars). Better than tesseract for rotated/dense drawing annotations at the cost of ~10s of MB of ONNX models; avoids the heavy paddlepaddle dependency of PaddleOCR proper. (Legacy package name `rapidocr-onnxruntime` 1.4.4 is superseded.)

Source: [github.com/RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR); [PyPI rapidocr JSON](https://pypi.org/pypi/rapidocr/json)

### Scale inference ladder

1. **Best: dimension annotations.** DXF: `dim.get_measurement()` vs defpoint distance is exact. Vector PDF/raster: pair OCR'd/extracted dimension strings with their measured segment (points or pixels) and least-squares fit units-per-point across all pairs, rejecting outliers (catches wrong-scale prints).
2. **Title block.** Regex scale notation `r'1\s*[:/]\s*(\d+)'` (1:50, 1:100, 1:200) from words in the page corner region; combine with paper size — PDF user space is exactly 1/72 inch per point (PDF spec), and ISO 216 mediaboxes identify the sheet: A4 = 595x842 pt (210x297 mm), A3 = 842x1191 pt, A2 = 1191x1684 pt, A1 = 1684x2384 pt, A0 = 2384x3370 pt; then `real_mm = points * 25.4/72 * scale_denominator`.
3. **DXF `$INSUNITS`** when nonzero.
4. **Fallback: ask user for one known dimension** (e.g. door = 0.9 m) — one cheap question beats silent wrong geometry.

Always store the inferred scale + method + confidence as an extracted fact so conformance checking can flag scale disagreement between sources.

Source: ISO 216 / PDF 1/72-inch unit are standard specifications; [ezdxf units doc](https://ezdxf.readthedocs.io/en/stable/concepts/units.html); ladder design is synthesis guidance

## Recommendations for TEE

1. Adopt as core deterministic dependencies (all compatible with MIT server): `pdfplumber` 0.11.x (MIT) for vector PDF lines/rects/words-with-coords, `pypdfium2` 5.x (Apache-2.0/BSD-3) for page rasterization feeding the raster path, `ezdxf` 1.4.x (MIT) for DXF, `ifcopenshell` 0.8.x (LGPL-3.0+, pip-dependency only — never vendor) for IFC.
2. Hard-ban PyMuPDF/`fitz` (AGPL-3.0) via a lint/CI check; everything it offers is covered by `pdfplumber` + `pypdfium2`.
3. Route every PDF page through the cheap vector-vs-scanned classifier (`page.chars`/`page.images` coverage test) and emit it as an extracted fact, so the pipeline and the model both know which evidence tier a page belongs to.
4. Rank source formats by fact quality and say so in extracted output: IFC (semantic walls/doors with placements) > DXF (exact geometry + `DIMENSION.get_measurement()` ground truth) > vector PDF (geometry + text, scale inferred) > raster (heuristic). Conformance checking should prefer higher tiers when sources disagree.
5. Do NOT ship any floorplan-recognition neural net: CubiCasa5K is CC BY-NC 4.0, the DeepFloorplan ports are GPL-3.0, none are pip-installable/maintained, and reliability across plan styles is poor. Implement the raster path as classical OpenCV (Apache-2.0) wall-thickness/morphology/contour heuristics — reimplement FloorplanToBlender3d's technique, never its GPL code — and leave an optional plugin seam where a user can bolt on CubiCasa5K under their own license terms.
6. OCR: default to tesseract/`pytesseract` (Apache-2.0, apt-installable, tiny); offer `rapidocr` (Apache-2.0, ONNX) as an opt-in extra for rotated dimension text, which tesseract handles badly; whitelist dimension charsets and always return word boxes + confidence, not plain text.
7. Implement the scale-inference ladder (dimension-annotation least-squares fit > title-block scale x ISO 216 paper size > `$INSUNITS` > ask user one calibration question) and store scale, method, and confidence as first-class extracted facts, since every downstream Blender dimension and conformance check depends on them.
8. Treat DWG as out-of-scope for core: support it only through the optional ezdxf `odafc` adapter requiring the user's own ODA File Converter install, and document the external-executable security caveat.
