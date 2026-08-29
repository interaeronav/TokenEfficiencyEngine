# 56 — The Okongo reality-capture lane: photos → as-built truth → drawings, UE, Blender (2026-08-29)

Verification basis: live `kb_search` through the installed co-pilot
(the corpus holds an end-to-end Namibian site-mapping playbook —
grounding below); open-web verification 2026-08-29 (sources inline);
the owner's use case verbatim: next Okongo visit, iPhone 17 Pro Max
photos of the structure inside and out plus drone images, run through
TEE so it updates the architectural drawings with the reality on the
ground and updates the landscape and house in Unreal, plus any
Blender work needed.

## KB grounding (A30: every rule lifted gets re-verified at its source)

The corpus was written for this mission: `cartography.namibia` ("how
to map a construction site and its surroundings in Namibia end to
end — GNSS control, drone flight, orthomosaic, contours"),
`envasset.reference_scanning` (capture for "a site in Ohangwena"),
`cartography.terrain` (the which-surface DSM/DTM discipline),
`equipment.survey` (instrument classes vs tolerance),
`vision.construction` (honest accuracy per application). 370 files
matched. Hygiene note: kb_search flagged the mirror stale against its
manifest — run `00_meta/rebuild.py` per its own tooling early in the
campaign (the drift check working, likely from recent staging
activity).

## Tool dispositions (the honest hardware answer first)

- **Meshroom: CUDA-blocked on this machine.** Meshroom's dense
  reconstruction hard-requires an NVIDIA CUDA GPU; no Apple Silicon
  path exists (the OpenCL fork ships Windows-only). Disposition: the
  pipeline's reconstruct stage is engine-pluggable, and Meshroom is
  recorded as the CUDA-box slot for a future machine — not installed,
  not pretended.
- **Apple PhotogrammetrySession (Object Capture): the native
  structure engine.** Built into macOS, M-series-optimized, matched
  to the owner's iPhone (LiDAR-assisted capture). Needs only a small
  Swift CLI helper around the API — built and probed in V0. Scope
  honesty: object-to-room scale; not a site mapper.
- **OpenDroneMap (ODM): the drone site engine.** The open standard
  for exactly this: georeferenced orthophoto, DSM/DTM, dense point
  cloud from drone imagery. Runs in Docker; arm64 image availability
  is a V0 probe, not an assumption. WebODM UI optional; TEE drives
  NodeODM/CLI.
- **COLMAP/OpenMVS: recorded fallback** (sparse fine on CPU; dense on
  CPU is slow — stated, not hidden).
- **CloudCompare: the deviation engine — ADOPT.** Universal arm64
  macOS binary (2.13.2+, brew cask), full command-line mode, and
  cloud-to-mesh (C2M) distance IS the as-built-vs-design operation;
  ICP registration aligns capture to design. Driven headless via the
  CLI as a TEE lane with the jobs pattern.
- **QGIS: per research 51/52** — gateway-front the existing QGIS MCP
  plugin for interactive work AND a thin `qgis_process` CLI lane for
  headless processing (CRS transforms, DEM merge/diff, contours,
  hillshade); the V0 probe decides which transport serves which op.

## The pipeline (capture → truth → updates)

1. **Capture, done right** — the quality ceiling is set on site, not
   in software. Deliverable BEFORE the visit: a one-page
   `docs/okongo-capture-protocol.md` distilled from the KB playbook
   (re-verified per A30): overlap targets, interior loop closure,
   scale references/markers where GNSS control is absent, drone
   altitude/overlap pattern, iPhone settings, a coverage checklist
   per room and facade.
2. **Ingest**: photos/scans → the extract store (content-addressed,
   EXIF GPS preserved) — the machinery exists.
3. **Reconstruct** (jobs, disk-gated): structure sets →
   PhotogrammetrySession; drone set → ODM (orthophoto + DSM/DTM +
   cloud).
4. **Georeference and align**: QGIS lane for CRS/DEM work;
   CloudCompare ICP registers clouds to the design model on the
   LOCKED OkongoSim site datum (blue structure −21.0, +20.7 — the
   datum law is inherited, never re-derived).
5. **The deviation report — the product of the whole lane**:
   CloudCompare C2M → compact, budgeted facts ("north wall: as-built
   +38 mm of design plane between 0.4–2.1 m; window W3 sill +22 mm"),
   plaus_check-style severities, honest accuracy bands per source
   (drone-with-references vs interior-relative). THE OWNER DECIDES
   what becomes design truth — TEE reports, never silently redraws.
6. **Apply, on approval**: drawing updates through the A37
   fabrication lane (TechDraw sheets regenerate from the corrected
   model); Blender fixes through the existing adapter; UE landscape
   refreshed from the new DTM through the terrain path and the house
   via the proven import lane (checkpointed; the import_house
   pass-order gotcha respected).

## Risks, named

- **Capture quality** (the biggest): mitigated by the protocol doc +
  an on-site 10-minute validation pass (reconstruct a single room's
  quick set at low res before leaving the site, if connectivity/time
  allows — else the checklist stands alone).
- **Absolute accuracy without survey control**: phone/drone GPS is
  meters-class; scale references and the KB's control guidance close
  it to what the deviation report honestly labels. No millimetre
  claims where the source cannot support them.
- **Compute/disk**: reconstructions are tens of GB — jobs pattern,
  disk gates, `.tee` state caps inherited from A38.
- **Destructive updates**: every apply step checkpointed; the UE
  landscape/house updates follow the recorded pass order; the site
  datum is immutable.

## Verdict

Build it (A40): every stage has a verified engine on this hardware,
the KB carries the domain playbook, and the highest-value deliverable
— the capture protocol — must exist BEFORE the site visit. The
campaign's proof: a full dry run of the entire pipeline on the
EXISTING site imagery in Dropbox (08 Site Progress + drone footage)
before any new capture happens — the trip must not be the first test.

Sources: Meshroom CUDA requirement and Mac alternatives
(peterfalkingham.com/2021/09/26/meshroom-cl, alternativeto.net/
software/meshroom/?platform=mac, github.com/openphotogrammetry/
meshroomcl); CloudCompare CLI + C2M + arm64 (cloudcompare.org/doc/
wiki Command_line_mode, cloudcompare forum C2M threads,
formulae.brew.sh/cask/cloudcompare, openfields macOS binaries);
research 51/52 for the QGIS stance; the KB files named above.

## Addendum (owner, 2026-08-29): DJI Mini specifics + PhotogrammetrySession optimization

The owner confirmed the engine choices and named the aircraft: a
**DJI Mini**. Facts that change the protocol and the ODM defaults
(sources: the ODM rolling-shutter database and community threads, the
Litchi/Dronelink ecosystem):

- **Electronic shutter only** — rolling-shutter distortion is the
  Mini's photogrammetry enemy. ODM ships correction with per-model
  readout constants, and the readout DIFFERS BY PHOTO MODE (Mini 3
  Pro: ~26 ms at 12 MP vs ~60 ms at 48 MP; Mini 4 Pro varies by
  mode/aspect). Consequences: the protocol PINS one photo mode for
  the whole survey; the ODM lane sets rolling-shutter correction with
  the constant matching the owner's exact model+mode (recorded at V0
  when the owner names the model); flight speed capped, stop-and-
  shoot for facades.
- **Automated grids exist for the Mini** via third-party mission apps
  (Litchi and Dronelink support the Mini 3/4 Pro; free grid planners
  export Litchi missions). The protocol prescribes a planned grid
  with fixed overlap over manual flying; manual technique stays as
  the no-app fallback with the checklist's overlap discipline.
- **Stills, never video frames**, for the mapping set; GPS EXIF is
  meters-class absolute (no RTK on Minis) — the honesty bands stand;
  scale references close relative accuracy.
- **The Mini's SRT telemetry already has a home**: the extract lane
  parses DJI SRT into flight-path facts (Phase 7) — flight logs
  ingest alongside the imagery for provenance.

**"Optimized with TEE" for PhotogrammetrySession, made concrete**: the
V0 helper exposes the API's quality ladder (preview → reduced →
medium → full → raw) and V2 benchmarks it on this M5 Max — wall time,
peak RAM, output tris per level on a fixture set — so the lane's
DEFAULTS are evidence rows, not guesses; long runs ride tee_job with
budgeted progress; every artifact carries engine+version+inputs-hash
provenance; preview quality serves the on-site 10-minute validation
pass, full/raw the final reconstruction.

**Owner allowance (same day): all drones.** The lane is
aircraft-agnostic by design: camera resolved per set from EXIF, ODM's
camera/rolling-shutter database supplies constants for every model it
knows, per-aircraft profiles override where defined — the DJI Mini
profile is the owner's default, not the architecture. Unknown cameras
degrade honestly (correction off, stated in the report, fly-slow
guidance). The protocol doc gains a per-aircraft appendix: Mini
filled in, a blank template for any future aircraft.

**Owner refinement (same day): the full DJI spectrum, from media
metadata.** DJI writes a rich XMP block (`drone-dji` namespace) into
every image beyond EXIF: aircraft/camera codes, gimbal attitude,
relative altitude, and on RTK models the fix quality and std-dev
fields. The ingest resolver therefore works metadata-first across the
whole DJI range: camera code → (cited model table) → shutter type —
mechanical-shutter cameras (Mavic 3 wide class, Phantom 4 Pro) need
NO rolling-shutter correction and run with it off; electronic-shutter
models get their model+mode constant from ODM's database; positioning
class comes from the data itself — the deviation report's honesty
band tightens to RTK levels ONLY when the files carry a valid RTK
fix; gimbal/AGL become prior facts; multi-camera aircraft split sets
per camera code; SRT video telemetry stays on the extract lane.
Unknown codes → the generic honest fallback. The DJI Mini remains the
owner's default profile within this spectrum.

**Owner adjustment (same day): all Minis, no model question.** The
owner flies the whole DJI Mini family; the plan must not fixate on
one model. The metadata resolver already makes this natural — every
set answers for itself — so the V0 model ask is DELETED and replaced
by a family-coverage probe: verify ODM's rolling-shutter database
against the Mini range and record in advance any member that would
fall to the honest fallback. The protocol's mode-pinning and
speed-cap rules are family-universal and stand unchanged; the
"default profile" is the Mini family as a class, not a model.
