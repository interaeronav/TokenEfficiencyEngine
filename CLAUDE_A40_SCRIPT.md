# A40 build script — the Okongo reality-capture lane

**SUPERSEDED — do not work this script.** A41 (owner directive,
2026-08-29) merged this campaign with its sibling; the merged build is
driven by `CLAUDE_A41_SCRIPT.md` (research 57 is the integration map).
This file stays as the design record its phases are referenced from.


**What this builds** (owner directive, 2026-08-29): the capture →
as-built truth → updates pipeline from
`docs/research/56-okongo-reality-capture.md` — the design of record;
read it first. Purpose: the owner's next Okongo site visit produces
iPhone photos (inside + outside) and drone imagery; TEE turns them
into a registered as-built model, a deviation report against the
design, and — on the owner's approval — updated drawings (A37
fabrication lane), Blender fixes, and a refreshed UE landscape and
house. Inherits every standing law by reference (A33 rules; surface
LAW 2,028/17 — everything here ships as virtual tools and lanes;
bars as the floor; A30/A31; fakes/probes first; jobs pattern for
long work; checkpoints before applies; owner-only decisions; >2 GB
gate; never concurrent with another campaign).

A one-paste prompt for a fresh session:

> Read CLAUDE.md, then CLAUDE_A40_SCRIPT.md, then research doc 56,
> then the last dated entries of docs/PROGRESS.md. Call tee_status and
> tee_recall first and use TEE's own tools as co-pilot throughout.
> Work the phases in order from where the evidence says they stand —
> probes before lanes, the capture protocol before the site visit,
> the dry run before any new capture matters. Stop and report if any
> phase's premise no longer holds.

## Campaign laws (from research 56)

- **TEE reports deviations; the OWNER decides what becomes design
  truth.** No silent redraw of drawings, scenes, or terrain — every
  apply step is explicit, checkpointed, and named in the report.
- The OkongoSim site datum is IMMUTABLE (blue structure −21.0, +20.7;
  the locked-datum record). Everything registers TO it.
- Accuracy claims carry their source's honesty band (drone-with-
  references vs interior-relative); no millimetre language where the
  capture cannot support it.
- Engine slots are pluggable: Meshroom stays a recorded CUDA-box slot
  — never installed here, never faked.

## V0 — Probes and installs (one batched owner ask)

1. Installs, sizes stated: CloudCompare (brew cask, arm64), QGIS
   (~1.3 GB class — state exact + free disk), ODM Docker image
   (arm64 probe FIRST — pull size stated; Docker Desktop presence
   checked), the PhotogrammetrySession Swift CLI helper (built from
   a ~100-line tool, macOS SDK only), the QGIS MCP plugin (for the
   gateway front).
2. Probes, pass/fail recorded as a dated addendum to research 56:
   CloudCompare `-SILENT` C2M on a fixture pair; `qgis_process` runs
   headless; QGIS MCP plugin fronted through the gateway (fingerprint
   pinned); ODM arm64 end-to-end on a 10-image mini-set WITH
   rolling-shutter correction resolved from the set's own metadata
   (owner adjustment 2026-08-29: NO model interrogation — the owner
   flies the whole Mini family; the resolver answers per set, and the
   V0 probe instead verifies ODM's rolling-shutter database coverage
   ACROSS the Mini family, recording any family member it lacks so
   the honest fallback is known in advance); PhotogrammetrySession
   helper reconstructs a small object set and exposes the full
   quality ladder (preview→raw).
3. KB hygiene: the mirror is flagged stale — run the corpus's own
   `00_meta/rebuild.py` and reconcile (owner data: report, don't
   delete).
4. Suites green; disk/free stated (reconstructions are tens of GB).

## V1 — The capture protocol (BEFORE the site visit — the deadline deliverable)

`docs/okongo-capture-protocol.md`, one page the owner takes to site,
distilled from `cartography.namibia` + `envasset.reference_scanning`
+ `cartography.terrain` with every lifted rule re-verified at its
cited source (A30): per-room and per-facade coverage checklist,
overlap targets, interior loop-closure habits, scale
references/markers where GNSS control is absent, drone
altitude/overlap pattern, iPhone capture settings, file-handling
rules (originals, no re-compression), and a 10-minute on-site
validation pass if time allows. DJI-Mini section (research 56
addendum): ONE photo mode pinned for the whole survey (the
rolling-shutter constant depends on it), flight speed capped with
stop-and-shoot for facades, a planned grid mission via
Litchi/Dronelink (free grid planners export Litchi missions) with
the manual-grid fallback, stills never video, SRT flight logs kept
for the extract lane. Acceptance: the owner has the doc and can
follow it without this repo open.

## V2 — Ingest + reconstruct lanes

Capture sets → the extract store (content-addressed, EXIF preserved,
set manifests). Reconstruct as jobs, disk-gated: structure sets →
the PhotogrammetrySession helper (quality ladder benchmarked on this
machine — wall/RAM/tris per level — so defaults are evidence rows:
preview for on-site validation, full/raw for finals); drone sets →
ODM. **The drone lane is aircraft-agnostic (owner allowance,
2026-08-29)**: the camera is resolved per set from EXIF, ODM's own
camera and rolling-shutter database supplies the constants for every
model it knows, and per-aircraft profiles (mode-pinned readout,
speed notes) override where one exists — the owner's default is the
DJI MINI FAMILY as a class (owner adjustment 2026-08-29: any Mini,
resolved per set from its own metadata; no single model assumed
anywhere). An unknown camera degrades
honestly: reconstruction proceeds with correction off and the report
says so, plus the fly-slow guidance line.

**The full DJI spectrum, resolved from media metadata (owner,
2026-08-29):** ingest gains a DJI metadata resolver — EXIF plus the
DJI XMP block (`drone-dji` namespace) parsed into facts per set:
aircraft and camera identified from the maker's camera codes (a
small cited model table maps code → marketing name → shutter type;
ODM's database remains the constants source); **shutter type decides
correction** (mechanical-shutter DJI cameras — Mavic 3 wide class,
Phantom 4 Pro — run with correction OFF because they need none;
electronic-shutter models get their matched constant); **positioning
class decides the honesty band from the data itself** (consumer GNSS
= meters-class; when the XMP carries a valid RTK fix, the band
tightens to what the RTK std-dev fields support — claimed only when
the files prove it); gimbal angles and relative altitude ingest as
orientation/AGL prior facts; multi-camera aircraft (tri/dual-camera
Mavic 3 / Air 3 class) split sets per camera code before
reconstruction; video-with-SRT keeps riding the existing extract
lane. Unknown DJI codes fall through to the generic honest fallback.

Every artifact lands with provenance (engine, version, inputs hash,
camera profile used, positioning class). Acceptance: fixture sets
reconstruct end to end via tee_job with compact progress, refusals
name fixes (no Docker, no disk, too few images); resolver fixtures
cover an electronic-shutter code, a mechanical-shutter code, an
RTK-stamped set (band tightens) and an unknown code (honest
fallback).

## V3 — Georeference + align

The QGIS lane (`qgis_process` headless; gateway front for
interactive ops): CRS discipline, DEM merge/diff against the existing
terrain base, contours/hillshade products. CloudCompare ICP registers
capture clouds/meshes to the design model on the locked datum;
registration quality reported (RMS, overlap %) — a bad registration
REFUSES rather than produces confident nonsense. Acceptance: fixture
registration lands within stated tolerance and the refusal fires on
a deliberately-wrong pair.

## V4 — The deviation engine (the lane's product)

CloudCompare C2M through the CLI lane → budgeted deviation FACTS:
per-element deltas with sign, extent and the source's honesty band,
plaus_check-style severities, compact summary first with drill-down
by id. The report ends with the decision menu (accept-as-built /
keep-design / flag-for-site), never an auto-apply. Acceptance: a
seeded-deviation fixture (design mesh vs displaced capture) yields
the exact planted deltas; the summary fits its token budget.

## V5 — Apply lanes (on approval only, checkpointed)

Owner-approved deviations flow to: the A37 fabrication lane (model
corrected → TechDraw sheets regenerate → the drawing-set row
re-proves), the Blender adapter (mesh/scene fixes via typed batches),
and UE: landscape refresh from the new DTM via the terrain path and
the house via the proven import lane — pass-order respected
(import_house wipes /Game/House; materials LAST), checkpoint before,
diff after. Acceptance: one full fixture round trip — deviation
report → one accepted item → drawing + Blender + UE all updated and
read back — recorded.

## V6 — The dry run (the trip must not be the first test)

The ENTIRE pipeline on existing Okongo imagery from Dropbox
("08 Site Progress" photos + any drone footage): ingest →
reconstruct → register → deviation report against the current design
model → a rehearsal apply on a throwaway branch of the scene.
Whatever breaks here is the campaign's real finding list. Acceptance:
the dry-run deviation report delivered to the owner as the campaign's
show-piece, with its honesty bands and the capture-protocol lessons
it taught folded back into V1's doc.

## V7 — Close-out

Benchmark row: tokens per delivered deviation report (naive =
attaching reconstruction outputs/screenshots to the conversation) —
research-48 style. Full battery: every bar holds. Suites + CI green;
docs (setup-reality-capture.md; the protocol doc final); artifacts
rebuilt + rehearsed; campaign ledger with wrong-way numbers explained;
report_savings quoted on the closing session; `tee_remember` the
close-out incl. the pre-visit checklist state. Version by semver
(expected 0.6.0 if A39 has not landed, else 0.7.0); the owner tags.
