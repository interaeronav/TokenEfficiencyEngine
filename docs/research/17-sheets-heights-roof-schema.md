# Sheet Classification, Heights & Roof Schema

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

Sheet/view classification is a solved, cheap problem when approached metadata-first: US National CAD Standard sheet numbers encode the view type in one digit (A-1xx plans, A-2xx elevations, A-3xx sections, A-5xx details), and production tools (Procore) classify sheets exactly this way via title-block OCR; a small CC0 CNN (DrawingClassifiers) exists as a visual fallback for plan/elevation/section.

Extraction of vertical facts from elevations/sections is proven in research (ALCM, Automation in Construction 2020: near-100% floor-level detection, 88% of members measured from CAD-layer elevations) but there is no off-the-shelf open-source extractor for raster elevations — a one-time VLM pass reading vertical dimension strings, level markers, and pitch triangles is the pragmatic route (VLM OCR on drawings hits ~0.95 accuracy while symbol/geometry reasoning is 0.40-0.55, so extract text/dimensions, not measured pixels).

The classic literature (Yin/Wonka/Razdan 2009 survey) confirms every prior automated system extrudes plans with assumed heights and none fuse elevations, so plan+elevation fusion must be designed in TEE: anchor via facade orientation labels, shared grid lines, and section-cut callouts (e.g. "3/A-301") that already cross-reference plans to sections.

FML v3 does represent per-level heights (`Floor.level`, `Floor.height`, per-endpoint wall `az`/`bz` `{z,h}`, opening `z`/`z_height`) and can encode roof planes only as baked-geometry surfaces with `isRoof:true` — it has no parametric roof (no pitch, ridge, overhang, type) and no explicit storey elevation datum, and even Hover, whose business is roof measurement, exports FML for interiors only. Conclusion: the schema needs extension before freezing — additive per-level height/datum fields and a parametric roof object (aligned to `IfcRoofTypeEnum`'s 15 types and `Pset_BuildingStoreyCommon` elevations) that compiles down to FML surfaces and wall endpoint heights.

## Findings

### Sheet classification prior #1: US NCS sheet numbering encodes view type

US National CAD Standard sheet number format is `[Discipline][SheetType][Sequence]`. Sheet type designator digits: 0=General (legends/notes), 1=Plans, 2=Elevations, 3=Sections, 4=Large-Scale Views (plans/elevations/sections, not details), 5=Details, 6=Schedules and Diagrams, 7/8=User Defined, 9=3D representations. Discipline letters include A (Architectural), S (Structural), C (Civil), etc. So A-101=floor plan, A-201=exterior elevations, A-301=building section, A-501=details. Parsing the sheet number alone classifies most professionally-produced sheets with zero ML; a cover-sheet "Sheet Index" table classifies the whole set in one pass.

Source: [Archtoolbox: construction document sheet numbers](https://www.archtoolbox.com/construction-document-sheet-numbers/); [National CAD Standard v6 FAQs](https://www.nationalcadstandard.org/ncs6/faqs.php)

### Sheet classification prior #2: production practice is title-block OCR

Procore's drawing upload auto-populates Drawing Number (from sheet number), Drawing Title (from title block), and Drawing Discipline (inferred from the number's letter prefix) using OCR; their accuracy guidance assumes the number is in the bottom-right corner, sans-serif, vector PDF. This validates a metadata-first classifier stage: crop the title-block region (bottom-right strip), OCR, regex the sheet number, map digit->view type. For vector PDFs no OCR is needed — text with coordinates can be extracted offline (pdfplumber is MIT; pypdf BSD-3; note PyMuPDF is AGPL-3.0/commercial dual-licensed, a conflict with TEE's MIT server).

Source: [Procore: auto-populated drawing fields](https://support.procore.com/faq/which-fields-can-procore-automatically-populate-when-uploading-drawings); [Procore: improving OCR accuracy on drawings](https://support.procore.com/faq/how-can-i-improve-the-accuracy-of-ocr-on-my-drawings)

### Sheet classification fallback: visual CNN classifier exists, CC0

DrawingClassifiers (Paulinos739, FID BAUdigital / TU Darmstadt) is a Python 3 + CNN API that classifies architectural drawings into floor plan / elevation / section (plus floor-plan design-pattern subclasses). License CC0-1.0 (public domain), Docker-deployable. No published accuracy/dataset size. No large public multi-sheet drawing-set dataset with per-sheet view labels exists; public datasets (CubiCasa5K, RPLAN, MLSTRUCT-FP with 954 multi-unit plan images, ResBIM with 1027 paired BIM/plan samples) are plan-view only — a view classifier for TEE would need either the NCS-metadata route, few-shot VLM classification, or fine-tuning on a small self-labeled set.

Source: [Paulinos739/DrawingClassifiers](https://github.com/Paulinos739/DrawingClassifiers); [MLSTRUCT-FP (ScienceDirect S0926580523003928)](https://www.sciencedirect.com/science/article/abs/pii/S0926580523003928)

### VLM capability envelope on drawings (what to delegate to the one-time VLM pass)

AECV-Bench (Kondratenko et al., arXiv 2601.04819, Jan 2026; 120 floor plans + 192 QA pairs): state-of-the-art multimodal models reach up to 0.95 accuracy on OCR/text-centric QA but only ~0.40-0.55 on symbol-centric counting (doors/windows) — "document assistants but lack robust drawing literacy". DrawingVQA (Jung, Fu, Golparvar-Fard, arXiv 2607.15418, Jul 2026; 33 issued-for-construction structural sheets, 92 expert QA): Gemini-2.5-Pro 71.7%, Claude-4.5-Sonnet 57.6%, GPT-4o 48.9%, vs human professionals 94.9%; failure modes are visual grounding in dense sheets, symbol/cross-reference interpretation, and quantity takeoff (top model 41.7%). Implication: have the VLM READ stated dimension text, level-marker values, pitch annotations, and title blocks (OCR-strength tasks) and avoid asking it to measure geometry from pixels.

Source: [AECV-Bench (arXiv 2601.04819)](https://arxiv.org/abs/2601.04819); [DrawingVQA (arXiv 2607.15418)](https://arxiv.org/html/2607.15418v1)

### Elevation/section extraction is proven for CAD input (ALCM paper)

Yin M., Tang L., Zhou T., Wen Y., Xu R., Deng W., "Automatic layer classification method-based elevation recognition in architectural drawings for reconstruction of 3D BIM models", Automation in Construction vol. 113, May 2020. It classifies the semantic meaning of CAD layers (ALCM), detects which drawing is an elevation and its orientation, extracts floor level heights, and segments window/door openings with their offset (horizontal) and height (vertical) dimensions. Results on 94 sample drawings: "nearly all floor levels detected", 88% of members visible in elevation drawings "measured perfectly"; the output populates a facade BIM with openings at correct coordinates. Practical hook for TEE: when the source is DXF/DWG, ezdxf (MIT, pure Python) reads layers/text/dimension entities offline, enabling this layer-name+geometry approach at zero token cost (DWG first converted to DXF via ODA File Converter, freeware).

Source: [University of Nottingham Ningbo publication page](https://research.nottingham.edu.cn/en/publications/automatic-layer-classification-method-based-elevation-recognition/); [ScienceDirect S0926580519303735](https://www.sciencedirect.com/science/article/abs/pii/S0926580519303735)

### Drafting conventions that carry the Z facts (what the elevation/section extractor must parse)

(1) Roof pitch: a small right-triangle symbol on the sloped roof line annotated rise/run with run fixed at 12 in US practice (e.g. 6:12 or 6/12; 12:12 ≈ 45°). (2) Level markers: dashed horizontal datum lines across elevations marking finished-floor and top-of-plate lines per level, usually with elevation values or labels (T.O. PLATE, FIN. FLR., RIDGE). (3) Vertical dimension strings on sections give floor-to-floor and floor-to-ceiling heights; wall sections give plate heights. (4) Cross-referencing: plans carry section-cut symbols (e.g. detail 3 / sheet A-301) and elevations are named by facade orientation (North/South/East/West Elevation) — these callouts are the native join keys between plan-view and vertical-view facts.

Source: [Advanced House Plans: how to read elevations](https://advancedhouseplans.com/blogs/how-to-read-house-plans-elevations); [Wikipedia: Roof pitch](https://en.wikipedia.org/wiki/Roof_pitch); [InterNACHI: roof slope and pitch](https://www.nachi.org/roof-slope-pitch.htm); [Blueprint Primer: understanding building elevations](https://blueprintprimer.com/posts/understanding-building-elevations)

### Classic literature confirms the fusion gap: everything extrudes plans with assumed heights

Yin, Wonka, Razdan, "Generating 3D Building Models from Architectural Drawings: A Survey", IEEE CG&A 29(1), Jan/Feb 2009. All surveyed systems (Lewis & Séquin/Berkeley 1998; So et al./HKUST 1998; Lu et al./Nanjing 2005 & 2007; Dosch et al./Loria 2000; Or et al./CUHK 2005) parse floor PLANS, extrude walls to a nominal height, and stack floors; adjacent-floor registration uses building outlines (CUHK) or intrusion structures like elevator wells (Loria). Elevations/sections appear only as "other kinds of drawings"; none extract heights or roof geometry from them. Listed open problems include multi-floor assembly with differing scales/orientations and differing footprints. Conclusion: plan+elevation fusion is not an off-the-shelf capability — TEE must implement it as fact-level fusion (per-level height facts keyed to level ids + roof facts keyed to roof planes), not as an existing algorithm.

Source: [Yin/Wonka/Razdan 2009 survey (PDF)](https://peterwonka.net/Publications/pdfs/2009.CGA.Yin.FloorplanExtrusionSurvey.IEEEDigitalLibrary.pdf)

### FML v3 vertical representation: heights YES (3 mechanisms), parametric roof NO

FML v3.0 spec (Floorplanner, floorplanner.readme.io; units are cm): `Floor {id, name, level, height, designs[]}` where `height` is the floor's default wall height and `level` orders storeys — no explicit absolute storey elevation; the Z datum per level is only derivable by cumulatively stacking lower floors' heights, and slab thickness is not modeled. `Wall {a, b, az: {z, h}, bz: {z, h}, thickness, balance}` — per-endpoint bottom (`z`) and top (`h`) elevations, so gable-end walls with sloped tops ARE representable. Openings `{z (sill elevation), z_height (opening height), t (position along wall)}`. Surfaces `{poly: (Point3D | BezierPoint)[], isRoof?: boolean}` — a roof is only a 3D polygon flagged `isRoof:true` with pitch baked into per-vertex z; there is NO roof entity, NO pitch/ridge/eave/overhang/roof-type fields. Items have `z` and `z_height`. Dimension entities are 2D annotation lines only.

Source: [FML v3.0 specification](https://floorplanner.readme.io/reference/v30-specification)

### FML-in-practice evidence: even photo-to-3D vendor Hover excludes roofs from FML

Hover (photo-based home 3D reconstruction whose core product measures roof pitch/area) exposes a "Get FML Export" API endpoint whose docs state it "returns the FML file for Interior models only"; the sample response shows walls with `az`/`bz` (e.g. `az: {z: 0, h: 246.500001}`) but no roof surfaces. Roof/exterior data is delivered through Hover's other formats, not FML. This corroborates that FML v3 is not used as a roof-geometry carrier in the wild, and that an FML-v3-based fact schema needs a roof extension for TEE's house use case.

Source: [Hover developer docs: Get FML Export](https://developers.hover.to/reference/get-fml-export)

### IFC mapping targets for the schema extension (so extended facts stay exportable)

IFC 4.3: `IfcRoofTypeEnum` has 15 values — `FLAT_ROOF`, `SHED_ROOF`, `GABLE_ROOF`, `HIP_ROOF`, `HIPPED_GABLE_ROOF`, `GAMBREL_ROOF`, `MANSARD_ROOF`, `BARREL_ROOF`, `RAINBOW_ROOF`, `BUTTERFLY_ROOF`, `PAVILION_ROOF`, `DOME_ROOF`, `FREEFORM`, `USERDEFINED`, `NOTDEFINED` — a ready-made controlled vocabulary for a fact-schema `roof.type` field. Storey heights: `IfcBuildingStorey.Elevation` ("elevation of the base of this storey relative to the building's 0,00") is deprecated in IFC4.3 in favor of `Pset_BuildingStoreyCommon.ElevationOfSSLRelative` (structural slab level) and `ElevationOfFFLRelative` (finished floor level); `Qto_BuildingStoreyBaseQuantities` provides `GrossHeight` (top of slab to top of slab above = floor-to-floor) and `NetHeight` (top of slab to bottom of slab above). These give exact, standard names to the per-level fields the schema is missing: elevation datum, floor-to-floor (gross), floor-to-ceiling (net).

Source: [IFC 4.3 IfcRoofTypeEnum](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcRoofTypeEnum.htm); [IFC 4.3 IfcBuildingStorey](https://ifc43-docs.standards.buildingsmart.org/IFC/RELEASE/IFC4x3/HTML/lexical/IfcBuildingStorey.htm)

### Adjacent modalities: satellite/photos cannot substitute for elevation sheets on pitch, and aerial pitch estimation is patent-heavy

Deep-learning roof analysis from aerial imagery exists (roof type classification from VHR aerial imagery; eave/ridge/hip line prediction plus nDSM from single RGB images), but nadir satellite imagery cannot directly yield pitch without height data, and the commercial space (EagleView) holds multiple US patents on "systems and methods for analyzing remote sensing imagery" covering CNN-based roof pitch estimation from monocular images (e.g. US 12,243,301; 10,366,288; 11,568,639) — a reason to keep satellite-derived facts to footprint/orientation/roof-outline and take pitch/ridge heights from the elevation sheets. Recent MLLM-era work (Sketch2BIM, arXiv 2510.20838, a multi-agent VLM pipeline with human feedback and schema validation converting hand-drawn floor plans to 3D BIM) validates TEE's pattern of schema-constrained VLM extraction but remains plan-only, again leaving vertical facts to the elevation/section route.

Source: [Sketch2BIM (arXiv 2510.20838)](https://arxiv.org/pdf/2510.20838); [ResearchGate 352829968](https://www.researchgate.net/publication/352829968); [US Patent 12,243,301](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12243301)

### Fusion design implied by the evidence (no existing algorithm to adopt)

Fact-level fusion, not geometric image registration: (1) classify sheets; (2) from plans extract footprint/walls/openings keyed by level and facade orientation; (3) from elevations extract per-level datum lines (finished floor, top of plate, ridge) and opening sill/head heights keyed by facade orientation (North/South/East/West) — ALCM shows orientation is recoverable; (4) from sections extract floor-to-floor and ceiling heights keyed by the section-cut callout that names the plan location and sheet (e.g. 3/A-301); (5) join on level ids + facade orientation + grid lines; (6) conformance in Z = compare stated dimension strings across sheets (plan wall lengths vs elevation widths; elevation level values vs section dimension strings), flagging disagreements — preferring stated text over pixel measurement matches the VLM capability envelope (OCR 0.95 vs geometry 0.4-0.55) and drafting practice (stated dimensions govern over scaled measurement).

Source: synthesis of ALCM 2020, Yin/Wonka/Razdan 2009, AECV-Bench 2026, NCS conventions

## Recommendations for TEE

1. Add a sheet-classifier stage as pipeline step 1, before any view-specific extractor: tier 1 = zero/near-zero-cost metadata (parse the sheet number from the title-block region + NCS digit mapping 1=plan/2=elevation/3=section/5=detail, read the cover-sheet Sheet Index; pdfplumber for vector PDFs, OCR crop for raster); tier 2 = visual fallback (few-shot VLM call on a downscaled thumbnail, or the CC0 DrawingClassifiers CNN locally). Route each sheet to a plan-extractor, elevation-extractor, section-extractor, or skip (details/schedules/general notes) accordingly.
2. Extend the FML v3-based fact schema BEFORE freezing — retrofit would invalidate caches. Add (a) per-level: `{level_index, name, elevation_z (FFL, project datum), floor_to_floor (gross), ceiling_height (net), plate_height, slab_thickness?, provenance: sheet_id+dimension_string}` — names aligned to `Pset_BuildingStoreyCommon.ElevationOfFFLRelative` and `Qto_BuildingStoreyBaseQuantities` `GrossHeight`/`NetHeight`; (b) a parametric roof object: `{type: IfcRoofTypeEnum subset (flat/shed/gable/hip/hipped_gable/gambrel/mansard), pitch: {rise, run:12, degrees}, ridge_lines and eave_lines in plan coordinates, ridge_height, eave_height, overhang, per-plane list for complex roofs}`; (c) opening `sill_height`/`head_height` (maps 1:1 to FML `z`/`z_height`).
3. Keep FML v3 as a compile TARGET, not the fact model: per-level heights compile to `Floor.height` + Wall `az`/`bz` `{z,h}` (gable walls via unequal endpoint `h`), openings to `z`/`z_height`, and the parametric roof compiles to Surfaces with `isRoof:true` and per-vertex z computed from pitch+ridge — while Blender/IFC exporters consume the parametric form directly (`IfcRoof` + `IfcBuildingStorey`). This preserves compatibility with the FML ecosystem without losing pitch/ridge semantics.
4. For the one-time elevation/section extraction pass, direct the VLM at its proven strengths: transcribe vertical dimension strings, level-marker labels/values (FIN. FLR., T.O. PLATE, RIDGE), pitch triangles (n/12), and facade orientation from the sheet title — as structured output against the frozen schema. Do not ask it to measure pixels or count symbols (0.40-0.55 accuracy band). For DXF/DWG sources, do it fully offline with ezdxf (MIT) using the ALCM layer-classification approach; avoid PyMuPDF (AGPL) in the MIT server.
5. Implement fusion as fact-level joins keyed on `{level_index, facade_orientation, grid_line, callout reference like 3/A-301}`, and implement Z-conformance as cross-sheet consistency checks over stated dimensions (elevation level values vs section dim strings vs plan+assumed heights), emitting a short discrepancy fact when sheets disagree — this doubles as the dimensional conformance feature in Z.
6. Treat satellite/aerial imagery as a source of footprint, orientation, and roof outline only; take pitch, ridge heights, and per-level heights from elevation/section sheets (nadir imagery cannot give pitch without height data, and monocular-image pitch estimation is covered by EagleView patents).
7. Bump `extractor_version` and freeze only after the Z extension lands; note in the schema doc that per-media-type frozen schemas are keyed into prompt caches and stored extraction records, so the roof/heights fields must ship in the first frozen revision even if early extractors leave them null (nullable-but-present fields keep cache keys stable while extractor coverage grows).
