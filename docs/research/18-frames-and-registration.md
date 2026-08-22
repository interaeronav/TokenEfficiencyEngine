# Frames, Transforms & Cross-Source Registration

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

Cross-source registration should be modeled as a small frame registry plus transforms-as-facts: every geometric fact carries a `frame_id` drawn from seven frame kinds (drawing paper space per layout, drawing model space, raster pixel per image, SfM reconstruction, geographic CRS, a site-local ENU metric frame, Blender world), and inter-frame transforms are stored as first-class facts with type, flat row-major params (STAC `proj:transform` convention), method enum, input-correspondence provenance, residual block (RMSE/max/n/inliers), and an accuracy-in-meters field (precedent: PROJ/pyproj `Transformer.accuracy`, EPSG operations).

The site-local ENU frame (WGS84-anchored local tangent plane, exactly OGC GeoPose Basic's outer `EPSG:4979` + inner LTP-ENU structure, and COLMAP `model_aligner`'s native alignment target) is the single conformance hub; `EPSG:3857` is fetch-only and never a measurement frame.

All required estimators exist as permissively licensed, offline Python: skimage Umeyama / `cv2.estimateAffinePartial2D` (4-DOF similarity with RANSAC inlier mask and LM-refined residual) for drawing-footprint-to-open-footprint fits, rasterio affine/GCP transforms for rasters, exiftool-read DJI XMP/SRT + pymap3d `geodetic2enu` for photo/video GeoPose priors, and COLMAP `model_aligner` for SfM georegistration.

Measured accuracy priors give a natural tier ladder — drawing written dimensions (mm; AEC "figured dimensions govern" rule) >> scan/SfM (±10-30 mm scan-to-BIM practice, USIBD LOA) >> GPS/EXIF (±0.5-1.5 m) >> satellite/footprint data (2-5 m CE90, ~3 m OSM) — and reconciliation follows surveying practice: effective tolerance = RSS of source tolerances plus chain registration residuals; beyond it, tier precedence wins (never cross-tier averaging), same-tier values inverse-variance average, systematic residual patterns demote/refit the transform rather than the facts, and every over-tolerance disagreement is emitted as a compact first-class conflict fact — which is itself the conformance-check deliverable.

This forces registration to be a distinct pipeline stage between per-source extraction and conformance/Blender handoff, and because frame-local facts are immutable under re-registration (only transform facts and derived comparisons re-derive), the satellite/photo/drawing lanes can ship independently before registration exists.

## Findings

### Drawing frames: DXF model space vs paper space units

ezdxf: header var `$INSUNITS` defines modelspace/document units (code 6=meters, 1=inches, 4=mm); paperspace and block layouts carry their own `units` attribute; modelspace and paperspace units are unrelated and can mix imperial/metric in one file. `VIEWPORT` scale is implicit (ratio of viewport size to `view_height`); the viewport view center is stored 2D but represents a WCS point. Entities may be defined in OCS, so extraction must normalize OCS->WCS before any registration. Implication: paper space and model space are distinct frames per document, and the paper->model transform per viewport is itself a stored transform fact. ezdxf is MIT-licensed, pure Python.

Source: [ezdxf units concepts](https://ezdxf.readthedocs.io/en/stable/concepts/units.html); [ezdxf VIEWPORT entity](https://ezdxf.readthedocs.io/en/stable/dxfentities/viewport.html); [ezdxf paperspace concepts](https://ezdxf.readthedocs.io/en/stable/concepts/paperspace.html)

### 2D similarity estimation: scikit-image Umeyama

`skimage.transform.SimilarityTransform.estimate` / `skimage.transform.umeyama` implement Umeyama's least-squares similarity fit (rotation+translation+optional uniform scale) from point correspondences (Umeyama, IEEE PAMI 1991, DOI 10.1109/34.88573). Returns an (N+1)x(N+1) homogeneous matrix; NaN when ill-conditioned (a detectable failure mode). Works N-D, so the same code path serves 2D drawing-to-footprint and 3D recon-to-ENU fits. scikit-image is BSD-3 licensed.

Source: [skimage.transform API](https://scikit-image.org/docs/stable/api/skimage.transform.html)

### Robust similarity with residuals for free: cv2.estimateAffinePartial2D

OpenCV `estimateAffinePartial2D` computes a 4-DOF limited affine (uniform scale, rotation, tx, ty) between 2D point sets; RANSAC is the default method (default reprojection threshold 3.0, configurable `maxIters`/`confidence`), returns an inlier mask vector, refines on inliers with Levenberg-Marquardt, and returns an empty matrix when estimation fails. This directly supplies the transform fact's method, residual (post-LM reprojection error), `n_inliers`/`inlier_ratio`, and a hard failure signal. OpenCV is Apache-2.0 (since 4.5).

Source: [OpenCV calib3d docs](https://docs.opencv.org/3.4.2/d9/d0c/group__calib3d.html); [opencv/opencv#6615](https://github.com/opencv/opencv/pull/6615)

### SfM georegistration: COLMAP model_aligner

COLMAP `model_aligner` aligns a reconstruction to geo coordinates with `--alignment_type ecef|enu`, `--ref_is_gps 1`, and `--alignment_max_error N` (RANSAC error threshold, e.g. 3.0 m); it requires at least 3 referenced images to estimate the 3D similarity transform. ENU mode aligns to the true ENU ground plane at the model's 3D-point centroid (x=East, y=North, z=Up); with ENU coordinates the first image's GPS defines the ENU origin. Older builds use `--robust_alignment` / `--robust_alignment_max_error` flags. This is the exact "DJI flight-path georegistration of keyframes" mechanism: per-image GPS priors -> robust similarity -> metric ENU model, with the RANSAC threshold/inliers as the stored residual. COLMAP is BSD-licensed but is an external binary (heavy dependency; optional lane).

Source: [COLMAP FAQ](https://colmap.github.io/faq.html); [colmap/colmap#1177](https://github.com/colmap/colmap/pull/1177); [colmap/colmap#1683](https://github.com/colmap/colmap/issues/1683)

### DJI photo/video pose priors (offline, zero-token)

DJI writes an XMP namespace `http://www.dji.com/drone-dji/1.0/` (ExifTool group `XMP-drone-dji`, `DJI.pm`) with 30+ per-image fields: GPS lat/lon, `AbsoluteAltitude` (MSL-ish), `RelativeAltitude` (above takeoff), `GimbalRoll/Yaw/PitchDegree`, `FlightRoll/Yaw/PitchDegree`, `DateTimeOriginal`. Batch extraction: `exiftool -csv -n` over a flight folder. DJI videos carry per-moment telemetry (GPS, altitude, speed) as SRT subtitle logs, embedded in the MP4/MOV or as sidecar; `exiftool -ee` (extract embedded) reads the embedded timed metadata; community tools (DJI_GPX_Extractor, `dji-drone-metadata-embedder` on PyPI) convert to GPX/CSV/JSON. So each keyframe gets a GeoPose-style prior (WGS84 position + yaw/pitch/roll) with zero model tokens. ExifTool is Perl Artistic/GPL — call as subprocess, do not vendor into the MIT server.

Source: [ExifTool DJI tag names](https://exiftool.org/TagNames/DJI.html); [ExifTool DJI.pm](https://github.com/exiftool/exiftool/blob/master/lib/Image/ExifTool/DJI.pm); [DJI_GPX_Extractor](https://github.com/djexit/DJI_GPX_Extractor); [dji-drone-metadata-embedder 1.12.0 on PyPI](https://pypi.org/project/dji-drone-metadata-embedder/1.12.0/)

### Accuracy prior for consumer-drone GPS; vertical datum hazard

DJI spec sheets state hovering accuracy with GPS positioning: horizontal ±1.5 m, vertical ±0.5 m (Mavic 2/Air 2/Air/Mini); Mavic 3 improves to ±0.5 m horizontal with its high-precision positioning system. Separately, Agisoft's helpdesk documents that DJI `AbsoluteAltitude` is a known source of large altitude errors (barometric/ellipsoidal/MSL ambiguity across models/firmware). Design consequence: photo-lane priors get `accuracy_m` ≈ 1.5 (horizontal) and the vertical channel is a separate, lower evidence tier — height conformance should come from drawing dimensions and relative measures, not GPS altitude.

Source: [DJI Mavic 2 specs](https://www.dji.com/support/product/mavic-2); [DJI Mavic 3 specs](https://www.dji.com/support/product/mavic-3); [Agisoft helpdesk: DJI altitude errors](https://agisoft.freshdesk.com/support/solutions/articles/31000152491-possible-causes-of-large-altitude-errors-when-working-with-dji-images-in-metashape)

### Geographic frames: EPSG:3857 is fetch-only, never a measurement frame

Web Mercator's scale factor grows as 1/cos(latitude) — at 60°N a map metre is ~0.5 ground metres; distances/areas are inflated everywhere off the equator. Practitioner rule: store/exchange in `EPSG:4326`, display tiles in 3857, measure in neither — use a local projected CRS (UTM/national grid) or local tangent plane for metric work. pymap3d (BSD, pure Python, v3.2.0 Jul 2025, Py>=3.9, no required deps) provides `geodetic2enu`/`enu2geodetic`/`geodetic2ecef` etc. for the ENU hub frame; pyproj (MIT) handles all CRS-to-CRS ops.

Source: [OSM wiki: EPSG:3857](https://wiki.openstreetmap.org/wiki/EPSG:3857); [epsg.io/3857](https://epsg.io/3857); [pymap3d on PyPI](https://pypi.org/project/pymap3d/); [pyproj Transformer API](https://pyproj4.github.io/pyproj/stable/api/transformer.html)

### Precedent for transform accuracy as a stored field: PROJ/pyproj

pyproj `Transformer.from_crs` accepts `accuracy=` (minimum desired accuracy in metres of candidate coordinate operations, PROJ 8+), and `Transformer.accuracy` exposes the expected accuracy of the chosen operation (-1 if unknown) — i.e., the EPSG/ISO-19111 coordinate-operation model already carries per-transform accuracy metadata in meters. TEE's transform facts should mirror this: an `accuracy_m` field populated from PROJ for `crs_op` transforms and from fit residuals for estimated transforms.

Source: [pyproj Transformer API](https://pyproj4.github.io/pyproj/stable/api/transformer.html)

### Raster georeferencing model and storage convention

Raster geo frames are 6-parameter affine transforms (pixel -> CRS). rasterio exposes `Affine` and `rasterio.transform.from_gcps()`, which wraps GDAL's `GDALGCPsToGeoTransform` to derive an approximate affine from ground control points (plus `GCPTransformer` for non-affine GCP interpolation). The STAC projection extension gives a ready serialization: `proj:code` (e.g. `EPSG:3857`, replaces `proj:epsg`), `proj:wkt2`, `proj:projjson`, `proj:shape` `[rows, cols]`, and `proj:transform` as a flat row-major 3x3 (bottom row `[0,0,1]` omissible -> 6 elements), explicitly matching rasterio's ordering and NOT GDAL's. Adopting flat row-major params for all 2D transform facts keeps satellite tiles, scanned PDFs, and drawing rasters uniform. rasterio is BSD-licensed.

Source: [rasterio.transform API](https://rasterio.readthedocs.io/en/stable/api/rasterio.transform.html); [rasterio georeferencing topics](https://rasterio.readthedocs.io/en/stable/topics/georeferencing.html); [STAC projection extension](https://github.com/stac-extensions/projection)

### Open footprint datasets for drawing-to-world anchoring: licenses and scale

Microsoft Global ML Building Footprints: 1.4 B footprints (130 M+ US, 500 M+ Africa) with tens of millions of height estimates, ODbL. Overture Maps buildings theme: ODbL (inherits OSM share-alike). Google Open Buildings: CC BY 4.0 (ODbL-compatible per Overture docs). OSM buildings: ODbL. VIDA's merged Google+Microsoft(+OSM) dataset: 2.58 B footprints. Caveat: ML-derived footprints have lower precision, worst in the Global South. For an MIT server: use footprints as a registration reference at runtime (cache with a license tag and provenance); do not redistribute merged footprint data with the codebase.

Source: [Overture Maps buildings guide](https://docs.overturemaps.org/guides/buildings/); [OSM wiki: Microsoft Building Footprint Data](https://wiki.openstreetmap.org/wiki/Microsoft_Building_Footprint_Data); [VIDA merged dataset on Source Cooperative](https://source.coop/vida/google-microsoft-osm-open-buildings); [Mark Litwintschik on Microsoft footprints](https://tech.marksblogg.com/microsofts-global-ml-building-footprints.html)

### Accuracy priors for the geo lane (sets its evidence tier)

Maxar Vivid imagery basemaps: 5 m CE90 stated accuracy globally, 2 m CE90 in major urban centers, at 30 cm (up to 15 cm HD) resolution — CE90 = 90% of points within that radius of true position. OSM building footprints: average positional deviation below 3 m vs 1:5000 reference maps (MDPI IJGI study, which also proposes footprint comparison via average boundary distance after translation+rotation correction — the same constrained-similarity idea proposed for TEE). Consequence: the geo lane is a meters-class tier, 2-3 orders of magnitude coarser than drawing dimensions; drawing->geo registration anchors location/orientation but must never be allowed to "correct" drawing-internal dimensions.

Source: [Maxar: why stated accuracy matters](https://blog.maxar.com/tech-and-tradecraft/2020/decisions-and-consequences-why-stated-accuracy-matters); [Maxar Vivid on ArcGIS](https://www.arcgis.com/home/item.html?id=94f52ee723a24db880b741f6d8c582a5); [MDPI IJGI 7(8):289](https://www.mdpi.com/2220-9964/7/8/289)

### Polygon comparison primitives for footprint fitting

Shapely 2.x (BSD) provides `shapely.hausdorff_distance` (discrete Hausdorff with a `densify` parameter to refine the vertex-only approximation) and `shapely.minimum_rotated_rectangle` (oriented envelope — gives 4 corner correspondences for a coarse initial similarity fit between a drawing footprint and a map footprint); IoU is `intersection().area/union().area`. These are the fit-quality scores to store alongside the transform residual.

Source: [shapely.hausdorff_distance](https://shapely.readthedocs.io/en/stable/reference/shapely.hausdorff_distance.html); [shapely.minimum_rotated_rectangle](https://shapely.readthedocs.io/en/stable/reference/shapely.minimum_rotated_rectangle.html)

### AEC precedence rule grounding the reconciliation policy

Industry-wide convention: written (figured) dimensions always govern over scaled measurements; drawings carry "Do not scale drawing — work to figured dimensions" disclaimers; when a builder finds a discrepancy the required action is to follow written dimensions and raise an RFI (Request for Information) rather than silently resolve. This maps one-to-one to TEE policy: dimension-text facts outrank geometry-derived facts from the same drawing, cross-tier conflicts resolve by tier precedence, and every over-tolerance conflict is recorded as an explicit conflict fact (the RFI analogue) rather than averaged away.

Source: [AWCI: Architectural Drawings — Gospel or Intent?](https://www.awci.org/media/feature-articles/architectural-drawings-gospel-or-intent/); [LEA Design: Reading architectural drawings 101 part B](https://leadesign.com.au/architect/reading-architectural-drawings-101-part-b/)

### Conformance tolerance bands from scan-to-BIM practice

Scan-vs-BIM dimensional conformance checking (Bosché 2010 lineage: recognizing as-designed model objects in point clouds for dimensional compliance control) typically uses tolerance limits of ±10 mm to ±30 mm for standard architectural/structural elements, ±2-5 mm for heritage/high-precision work. The USIBD Level of Accuracy (LOA) Specification (v3.0, 2019) defines five levels LOA10-LOA50 inspired by DIN 18710's five tolerance ranges, specified via standard deviation at a stated confidence; commercial scan-to-BIM tiers are quoted as ±25 mm / ±12 mm / ±6 mm / ±3 mm / ±1.5 mm. These are the defaults for TEE's per-check tolerance classes.

Source: [USIBD Level of Accuracy](https://usibd.org/level-of-accuracy/); [ScienceDirect S0926580521001370](https://www.sciencedirect.com/science/article/pii/S0926580521001370); [The Future 3D: USIBD LOA](https://www.thefuture3d.com/answers/usibd-level-of-accuracy/); [ViBIM: scan-to-BIM quality control](https://vibimglobal.com/blog/scan-to-bim-quality-control/)

### Frame-graph precedent 1: ROS REP-105 / tf2

REP-105 fixes a single-parent transform TREE (`map` -> `odom` -> `base_link`) with Z-up frames (REP-103: X forward, Y left, Z up); frames and timestamped transforms are data, and the tree constraint (each frame has exactly one parent) is what makes pose composition unambiguous. TEE should copy this: transforms form a spanning tree anchored at the site ENU frame; additional measured edges (e.g. a second independent registration) are stored as evidence facts but only one edge per frame-pair is "active" for composition.

Source: [REP-105](https://github.com/ros-infrastructure/rep/blob/master/rep-0105.rst); [Nav2 transform setup guide](https://docs.nav2.org/setup_guides/transformation/setup_transforms.html)

### Frame-graph precedent 2: OGC GeoPose 1.0 (21-056r11)

GeoPose 1.0 (JSON encoding, media type `application/geopose+json`) defines 8 standardization targets. Basic-YPR and Basic-Quaternion both use an `EPSG:4979` (3D WGS84) outer frame with an LTP-ENU (local tangent plane East-North-Up) inner frame — exactly the site-datum + ENU hub structure proposed for TEE, so photo pose priors and the site anchor can be serialized GeoPose-Basic-compatible. The Advanced target allows a configurable frame specified by authority/id/parameters; the composite targets Chain (linear sequence of frame transforms) and Graph (general linked poses) standardize serializing transform chains/graphs. Useful as the export/interchange shape of TEE's frame registry, at zero token cost until queried.

Source: [OGC GeoPose 1.0 (21-056r11)](https://docs.ogc.org/is/21-056r11/21-056r11.html); [IANA media type application/geopose+json](https://www.iana.org/assignments/media-types/application/geopose+json)

### Blender frame and geo-anchoring precedent

Blender world is right-handed Z-up; Scene > Units > Unit Scale (`scale_length`) sets meters per Blender Unit, default metric 1.0 => 1 BU = 1 m (Blender 5.2 manual, Scene Properties). BlenderGIS's shipped precedent for anchoring: scene-level custom properties storing the CRS (SRS id) plus the scene origin in both projected (`crsx`/`crsy`) and geographic (lon/lat) coordinates; a scene is "correctly georeferenced" when CRS + origin are set. TEE should do the same via its adapter — site datum at Blender origin, meters, Z-up — making `site_enu` -> `blender_world` an identity transform that is still stored as an explicit transform fact for auditability.

Source: [Blender manual: Scene Properties](https://docs.blender.org/manual/en/latest/scene_layout/scene/properties.html); [BlenderGIS wiki: georeferencing management](https://github.com/domlysz/BlenderGIS/wiki/Georeferencing-management); [BlenderGIS geoscene.py](https://github.com/domlysz/BlenderGIS/blob/master/geoscene.py)

### Research support for footprint-fit registration and Gaussian error modeling

OSM footprint accuracy assessment literature uses exactly the proposed mechanism (boundary-distance similarity after translation+rotation correction; map matching against reference footprints). DragOSM (arXiv 2509.17951) models the positional discrepancy between historical footprint labels and updated imagery as a Gaussian distribution and treats alignment as denoising; FlexMap Fusion (arXiv 2404.10879) georeferences HD maps against OSM via rigid transform + Umeyama least-squares before conflation. Together these validate (a) constrained similarity fitting as the drawing/footprint registration method and (b) modeling registration error as a Gaussian whose sigma feeds the tolerance calculation.

Source: [MDPI IJGI 7(8):289](https://www.mdpi.com/2220-9964/7/8/289); [DragOSM (arXiv 2509.17951)](https://arxiv.org/html/2509.17951v1); [FlexMap Fusion (arXiv 2404.10879)](https://arxiv.org/pdf/2404.10879)

## Recommendations for TEE

1. Frame registry as a first-class fact table: `frame_id` (stable, human-readable: e.g. `dwg:{doc}:model`, `dwg:{doc}:paper:{layout}`, `px:{image_id}`, `recon:{model_id}`, `geo:{epsg_code}`, `site:{site_id}:enu`, `blender:{scene}:world`) plus kind, units, axis convention (y-down for pixel frames, Z-up for ENU/Blender), and for camera pixel frames an intrinsics reference. Every geometric fact gets a mandatory `frame_id`, and `frame_id` participates in the content-addressed key — this must land before the schema freeze.
2. Make `site:{site_id}:enu` the single conformance hub: a `site_datum` fact (WGS84 lat/lon/h + optional preferred projected EPSG) anchors a local tangent plane ENU frame (pymap3d `geodetic2enu`; GeoPose-Basic-compatible: `EPSG:4979` outer + LTP-ENU inner). All cross-source comparison and all Blender handoff happen in this frame (identity to Blender world: datum at origin, meters, Z-up, recorded BlenderGIS-style as scene properties). `EPSG:4326` is the exchange format for geographic facts; `EPSG:3857` is permitted only as a tile-acquisition frame and must be rejected by the conformance layer.
3. Transforms are first-class facts, not metadata: `{transform_id (content-addressed over from_frame, to_frame, method, input-ids), from_frame, to_frame, type (similarity2d|similarity3d|affine2d|homography|se3_pose|crs_op), params as flat row-major array (STAC proj:transform convention: 6 elements for 2D affine, 12/16 for 3D), method enum (umeyama|ransac_partial_affine|colmap_model_aligner|gcp_affine|exif_gps_prior|crs_op|viewport|declared_units|manual), inputs (fact-ids of the correspondences/priors used), residual {rmse_m, max_m, n_correspondences, n_inliers}, accuracy_m (fit residual, or PROJ operation accuracy for crs_op, or sensor prior e.g. 1.5 m for non-RTC DJI GPS), tier, created_at}`. Transforms form a REP-105-style single-parent spanning tree anchored at `site:enu`; redundant measured edges are kept as evidence but only one active edge composes.
4. Derived facts must cite their transform chain: any fact re-expressed in a non-native frame stores the `transform_id`s used. Then re-registration invalidates only the derived layer, never per-source extractions — which is what makes registration a separate pipeline stage between per-source extraction and conformance/Blender handoff, and what lets the satellite, photo, and drawings lanes ship independently before registration exists (their native-frame facts are final).
5. Drawing->geo registration: extract the building footprint polygon from DXF model space (OCS->WCS normalized, units from `$INSUNITS`), fetch the reference footprint from OSM/Overture/Microsoft/Google Open Buildings, initialize correspondence via `minimum_rotated_rectangle` corners, fit a CONSTRAINED similarity (rotation+translation free; scale pinned by declared drawing units) with `cv2.estimateAffinePartial2D` (RANSAC, inlier mask, LM-refined) or skimage `umeyama`; store IoU and Hausdorff distance as fit-quality fields. If the freely-fitted scale deviates from the units-implied scale by more than ~2%, emit a units-conflict fact instead of accepting the scale — that is a drawing-units or footprint-identity error, not a calibration.
6. Tier the frames by measured accuracy priors and record the tier on the transform: drawing dimension text (mm-class, governs by AEC convention) > drawing geometry (scale-derived) > SfM/scan geometry (±10-30 mm class) > drone/EXIF GPS priors (±0.5-1.5 m) > satellite basemap / open footprints (2-5 m CE90, ~3 m OSM). Hard rule: a transform can never raise a fact above the tier of the weakest source in its chain — drawing->geo registration places the house on Earth but cannot "correct" drawing-internal dimensions.
7. Photo/video lane: emit one GeoPose-style prior fact per keyframe from EXIF GPS + `XMP-drone-dji` (`RelativeAltitude`, Gimbal/Flight YPR) via exiftool subprocess (Artistic/GPL — never vendor); DJI video keyframes get per-frame GPS from embedded SRT telemetry (`exiftool -ee`). Treat the vertical channel as a separate, lower tier (DJI `AbsoluteAltitude` datum ambiguity). When >=3 georeferenced keyframes exist and an SfM model is built, refine with COLMAP `model_aligner --alignment_type enu --ref_is_gps 1 --alignment_max_error 3.0` and store its RANSAC residual on the recon->`site:enu` transform fact.
8. Reconciliation policy: (1) compare only after composing transform chains into the common frame; (2) effective tolerance for any comparison = RSS (root-sum-square) of each fact's tier tolerance plus `accuracy_m` of every transform on both chains — disagreement below that is registration noise, not a finding; (3) above tolerance, tier precedence decides the value (written dimension governs — the AEC "do not scale"/RFI rule), never cross-tier averaging; (4) same-tier disagreement uses inverse-variance weighted averaging; (5) if residuals are systematic (shared direction across many facts, or scale bias), demote and refit the TRANSFORM rather than overriding facts; (6) every over-tolerance disagreement is emitted as a compact first-class conflict fact `{fact_id_a, fact_id_b, frame, delta_m, tolerance_m, winner, disposition}` — for the driving use case these conflict facts ARE the dimensional-conformance report; (7) unresolved conflicts surface as one short question (fail loud and cheap).
9. License/dependency lane is clean for an MIT server with offline preprocessing: pyproj (MIT), rasterio (BSD), shapely (BSD), scikit-image (BSD-3), pymap3d (BSD, pure Python), ezdxf (MIT), OpenCV (Apache-2.0), COLMAP (BSD, external optional binary), exiftool (Perl Artistic/GPL, subprocess only). Footprint reference data is ODbL (Microsoft/Overture/OSM) or CC BY 4.0 (Google): use at runtime as registration reference with a license+provenance tag on the cached footprint fact; do not redistribute it with the repo, and note that transform parameters derived from it should carry attribution in provenance.
10. Phase ordering consequence for the execution script: insert "Register" as an explicit stage — Stage A per-source extraction (frame-local facts, independent lanes, shippable now) -> Stage B registration (frame registry + transform facts; needs at least the drawings lane plus any one geo-referenced lane) -> Stage C conformance + Blender handoff (consumes A facts through B transforms; blocked on B). Freeze the fact schema only after `frame_id`, the transform-fact table (method/params/residual/`accuracy_m`/tier), and chain-citing provenance are in the content-addressed key design.
