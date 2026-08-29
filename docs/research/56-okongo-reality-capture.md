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

## Addendum (A42 T0 probe table, 2026-08-29 — pass/fail as run)

Free disk 1.0 TiB of 1.8 TiB; suites green at probe time (716 passed
/ 2 skipped, ruff clean). Probes run this session:

- **PhotogrammetrySession helper: PASS.** Built at
  `helpers/photogrammetry/` (~130-line Swift CLI, macOS SDK only,
  Swift 6.3.3) — the compiler served as the API smoke test and caught
  one drifted case from memory (`.skippedSample`, not `.skippedImage`
  — the SDK swiftinterface is the record). Full quality ladder
  exposed (preview→raw), budgeted newline-JSON events (≤10 progress
  lines), refusals name the fix. Live run: 36-view synthetic orbit
  set (headless Blender, textured Suzanne, 960×960) → preview USDZ in
  **16.0 s wall, 833 MB peak RSS, 404 KB model**, exit 0. Per-level
  wall/RAM/tris rows stay a T2 deliverable as scripted.
- **ODM arm64: PASS on availability, blocked on runtime.**
  `opendronemap/odm:latest` ships linux/arm64 — 566,149,680 B
  compressed, pushed 2026-08-21 (Docker Hub API, read live). No
  Docker runtime on this machine → the pull and the 10-image
  end-to-end probe wait on the batched owner ask.
- **Mini-family rolling-shutter coverage: recorded.** ODM
  `opendm/rollingshutter.py` (master, read live) holds exactly four
  Mini-family entries: `dji fc7203` Mavic Mini v1 (19/25 ms by
  aspect), `dji fc3682` Mini 3 (23 ms), `dji fc3582` Mini 3 Pro
  (26/60 ms by MP mode), `dji fc8482` Mini 4 Pro (16/21/43/58 ms by
  mode+aspect). Every other family member (Mini 2 / SE / 2 SE / 4K /
  5 Pro — roster advisory; each set resolves from its own metadata
  anyway) is absent and would take ODM's `DEFAULT_RS_READOUT` 30 ms —
  the lane instead applies its scripted honest fallback (correction
  off, stated in the report, fly-slow guidance). The covered
  constants differ by photo mode exactly as the protocol's
  mode-pinning rule assumes.
- **CloudCompare C2M: blocked on install; fixture staged.**
  `helpers/cloudcompare/c2m_fixture.py` writes the probe pair (design
  plane + capture cloud displaced +38 mm; expected mean ≈ 38 mm,
  near-zero spread); probe command in its docstring. Cask 2.13.2
  confirmed current in brew — matching the version this doc verified.
- **qgis_process / QGIS MCP plugin: blocked on install.** QGIS cask
  4.2.1 current in brew (~1.3 GB class as stated above); the plugin
  probe needs QGIS first.
- **KB hygiene: DONE.** `00_meta/rebuild.py` run;
  `rebuild_verification.py` still carried the corpus author's
  hardcoded ROOT (`/home/claude/kb`) — fixed per the file's own
  header instruction to match `rebuild_index.py`'s computed ROOT.
  INDEX/manifest drift reconciled (word counts only, +16 words in
  00_meta), VERIFICATION.md regenerated (236 flagged files, 399 with
  open questions), 38 domains / 402 files intact, nothing deleted.

## Addendum (A42 T0 completed: owner said "install all of them", 2026-08-29)

All four installs landed and every gated probe closed, same day:

- **Docker runtime: colima 8-CPU/16-GiB/100-GB VM + docker CLI** (brew
  formulas — chosen over Docker Desktop for the headless, no-license-
  dialog path; the ask offered the substitute and the owner approved
  the batch). Server 29.5.2 linux/arm64. Mount law learned and
  encoded: the VM shares $HOME, not the system tmp — the lane stages
  copies under the project's `.tee`.
- **ODM end-to-end: PASS on real site imagery.**
  `opendronemap/odm:latest` pulled (566,157,794 B, arm64). The probe
  set came from the owner's own Dropbox: **the entire existing site
  capture is VIDEO — not one still exists** (the premise the
  protocol's stills-only rule fixes), so frames were extracted with
  the extract lane's own bundled ffmpeg. Three runs, each a lesson:
  13 frames @1 fps of a 13-s interior pan → honest ODM refusal (no
  reconstruction; moving workers + no baseline); 40 frames @3 fps →
  deep failure late in the pipeline (mesh built, then "strange
  values", ODM's message citing its own flying docs — the same rules
  the protocol encodes); **40 frames @2 fps of the ascent window of
  DJI_0108.MOV → exit 0, the FULL pipeline**: 32/40 shots
  reconstructed in one component, 28,383 sparse → 1.27 M dense
  points, 1.48 px reprojection, orthophoto + DEM + textured model +
  report, 5.0 min wall on the VM. **The source video's own metadata
  answered the aircraft: FC7303 = DJI Mini 2** — the exact
  family-gap member the T0 coverage probe recorded in advance; the
  resolver gained the row (`electronic-no-constant`: correction off
  with the aircraft NAMED) and its test.
- **CloudCompare 2.13.2 (cask): C2M probe PASS to the planted
  truth** — `-SILENT` headless on the staged fixture pair: mean
  distance **0.038, σ 5.7e-09** (the +38 mm plant recovered exactly),
  16 threads, 0.03 s compute.
- **QGIS 4.2.1 (cask, `QGIS-final-4_2_1.app`): qgis_process PASS**
  headless — 406 algorithms enumerated (`Contents/MacOS/qgis_process`;
  note: not under `bin/` in the QGIS 4 layout).
- **QGIS MCP plugin 0.12.0 (official directory, Nicolas Karasiak)
  fronted through the gateway: PASS.** Plugin staged into the QGIS4
  default profile + enabled via ini; it loads clean under QGIS 4/Qt6;
  the socket server (localhost:9876) starts via the plugin's
  `toggle_server(True)` (the autostart setting alone did not start it
  headlessly — one-click in the GUI, or the `--code` launch used
  here). Gateway backend = `uvx --from <repo zip> qgis-mcp-server`:
  **118 tools fronted as `qgis.*`, fingerprint pinned
  `Qgis_mcp@/77af5a90950a`**, bad calls refused with the exact
  missing-arg line, and a live read round-trip answered
  `qgis_version 4.2.1-Belém do Pará` from inside the running app.
- Free disk after everything: stated in PROGRESS with the ledger.

The drone lane's `capture_odm_pending` refusal is replaced the same
day by the real ODM invocation (correction flag per the resolver's
verdict, artifacts + provenance returned through tee_job) — tested on
a fake docker and proven live through the registry.
