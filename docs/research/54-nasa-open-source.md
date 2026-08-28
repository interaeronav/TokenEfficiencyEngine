# 54 — NASA open source worth using (2026-08-28)

Verification basis: open-web discovery 2026-08-28 plus two budgeted
deep-reads performed THROUGH `tee_web_lookup` itself (the A34 tool
doing real research — quotes below are its cited extracts); owner
context: airline pilot, simulator preparation, terrain/basemap work
with owned commercial satellite imagery, UE digital twin, fabrication
lanes per research 52/53.

## The four that matter, dispositioned

### 1. X-Plane Communications Toolbox (XPC) — the strongest new-lane candidate

Verified via tee_web_lookup on github.com/nasa/XPlaneConnect: clients
in **C, C++, Java, MATLAB and Python**; reads and sets **any X-Plane
DataRef**; positions **player and multiplayer aircraft** and control
surfaces; pauses the physics engine; NASA's own listed uses include
"visualize flight paths… simulate an active airspace… generate
out-the-window visuals." For the owner's simulator preparation this
is scenario-staging machinery: brief → aircraft/weather/traffic state
set → recorded states → visuals for boards. Integration shape if
directed (A38 material): a thin `xp_*` lane in the Blender-adapter
image (UDP client, typed state ops, budgeted state reports), or a
gateway-front if a maintained X-Plane MCP server exists (check at
adoption). **Precondition to confirm with the owner: an X-Plane
install he actually uses.**

### 2. Ames Stereo Pipeline (ASP) — terrain from the imagery the owner already buys

Verified via tee_web_lookup on the official docs: produces **DTMs,
ortho-projected images, 3D models and textured meshes**, explicitly
proven for "mass production of DEMs from very high-resolution
commercial stereo satellite imagery" (Shean et al. 2016, cited in the
docs). Direct fit: the terrain-basemap workflow and the UE site twin.
**Honest caveat: it needs STEREO pairs** — single mono acquisitions
(check what the existing SkyFi delivery actually is) won't do;
ordering stereo is a purchasing decision, not a software one.
Integration shape: an OFFLINE pipeline feeding the existing
terrain-basemap tooling — not a TEE runtime dependency.

### 3. OpenVSP — parametric aircraft geometry (research 52's flag, deepened)

NASA-lineage open-source parametric aircraft modeler with an official
"Ground School" tutorial site; exports geometry usable for accurate
airframe visuals in sim-prep boards and UE. Disposition: an asset
SOURCE for the A37 board lane, not an adapter. License note: NOSA
lineage — run the lint before anything ships.

### 4. Open MCT — NASA's web mission-control framework

Actively maintained (nasa/openmct), browser-based telemetry/timeline
dashboards used for real missions. Two owner-relevant uses, both
host-side: an "eye-popping" dashboard shell for simulator-prep or
project telemetry, and — later, if wanted — a front-end consuming
`report_savings` data. Disposition: browse-on-need; NOT a TEE embed.

## Parked, with reasons

- **F´ / cFS / Trick / GMAT**: flight-software frameworks, spacecraft
  sim, astrodynamics — no current owner need.
- **FUN3D / OVERFLOW (CFD)**: NOT actually open — request/export-
  controlled; correcting the "NASA = open" assumption. OpenFOAM
  (research 52) stays the parked CFD answer.
- **GIBS/Earthdata imagery APIs, NASA 3D Resources**: useful free
  data/model sources for boards and terrain — noted as sources, no
  integration needed.

## Dogfooding note (logged to SI_BACKLOG as SI-B10)

Both tee_web_lookup calls returned correct budgeted extracts AND an
off-topic `kb_hint` (a bmesh question hinted at construction case
studies; XPC at SA contractors; ASP at game-dev salaries) — the
hint's relevance ranking needs the kb-rerank chore or a score floor.
Live evidence in this doc's calls; third sighting today.

## Recommendation

No new campaign from this doc alone. The one decision worth putting
to the owner now: **does he run X-Plane?** If yes, the XPC sim lane
is A38-grade and small; if no, park it with the rest. ASP waits on a
stereo-pair check of the owned imagery; OpenVSP and Open MCT are
sources to reach for when the A37 board lane and the savings meter
respectively land.

Sources: github.com/nasa/XPlaneConnect (read via tee_web_lookup),
stereopipeline.readthedocs.io introduction (read via tee_web_lookup),
github.com/nasa/OpenVSP, nasa.gov/software/openvsp-ground-school,
nasa.github.io/openmct, github.com/nasa/openmct,
agupubs.onlinelibrary.wiley.com/doi/10.1029/2018EA000409.
