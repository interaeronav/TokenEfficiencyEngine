# Okongo capture protocol — one page for the site visit

*Print this. It works without the repo, the software, or a signal.*
*Rule of thumb everywhere: 70–80% overlap, every point in 3+ photos
(5 is better), move in slow arcs, never zoom mid-set. Storage is
cheap; a missed angle costs a return trip.*

## 0 · Before you leave

- [ ] Batteries: drone ×3+ charged, phone full, power bank.
- [ ] microSD + phone storage: ≥ 3× the space you think you need.
- [ ] Confirm current NCAA (Namibia CAA) rules for your drone class —
      registration, altitude cap, insurance. Rules drift; check the
      week of the trip, not from memory.
- [ ] Print this page. Charge the laser distance meter if you have it.
- [ ] Tape measure or DISTO; chalk/tape for floor marks; 4–6
      high-contrast markers (A4 sheets with bold X work) + stones to
      pin them.

## 1 · Drone — the site survey (DJI Mini family)

**Camera discipline (family-universal):**
- **Pin ONE photo mode now** (12 MP, 4:3) and never change it
  mid-survey — the rolling-shutter correction constant depends on the
  mode. Stills only, never video frames, for mapping.
- Fly slow; **stop-and-shoot** for facades. Electronic shutters smear
  when moving.
- Keep the SRT flight logs and bring them home with the photos.

**Flight 1 — nadir grid (the map):** camera straight down,
**80% front / 70% side overlap**, one even altitude (60–80 m AGL if
rules allow), lawn-mower pattern extending **≥ 50 m beyond the site
boundary** on all sides. Prefer a planned grid mission (Litchi /
Dronelink, or a free grid planner exporting a Litchi mission); manual
flight is the fallback — then watch the overlap discipline yourself.
Over bare sand, MORE overlap, not less: uniform sandveld starves
feature matching.

**Flight 2 — structure cross-grid (the 3D):** gimbal at ~45°, two
perpendicular grid passes over the house at lower altitude, then a
slow **orbit of the whole structure** at two heights, lens toward the
building. 70–80% overlap between frames.

**Light:** fly near midday, low wind, stable light. Never while cloud
shadows are marching across the site.

**Markers:** lay the 4–6 markers before the first flight — near the
corners + one central, 10–30 m in from the survey edge, flat, pinned.
Each must be visible in several frames. **Measure at least two
inter-marker distances** with the tape/DISTO and write them on this
page: absolute GPS here is meters-class; your measured distances are
what give the model true scale.

## 2 · iPhone — every facade, outside

Per facade: stand back far enough to frame it whole, then walk a slow
arc: one frame every ~1 m sideways (70–80% overlap), one pass level,
one pass from low, plus **angled frames from both ends** of the
facade. Step closer for one detail pass along openings (windows,
doors, junctions). Corners of the building are connective tissue —
shoot extra frames wrapping each corner so adjacent facades link.

- Main (1×) lens only; never zoom, never switch lenses mid-set.
- Lock exposure/focus (long-press) per facade; re-lock when light
  changes. Lowest motion blur wins: brace, don't rush.
- Keep the sun behind or above you; avoid your own hard shadow in
  frame.

## 3 · iPhone — every room, inside

Per room, two channels:
1. **LiDAR room scan** (Polycam / RealityScan Mobile app): one slow
   sweep — this is the scale-true rough proxy (trustworthy to ~5 m
   range, coarse detail).
2. **Photo loop:** walk the perimeter shooting inward-ish along the
   walls, a frame every step (70–80% overlap), **end exactly where
   you started** so the loop closes. Add a second pass at a different
   height for tall rooms. Then doorway frames looking BOTH ways
   through every door — these stitch rooms together.
- Even, diffuse light: curtains open, lights on, no torch hot-spots.
  Hard shadows bake into the model.
- **One measured distance per room** (tape/DISTO wall-to-wall), noted
  against the room name.

## 4 · Room / facade checklist

Tick as captured — a hole found at home is a return trip:

| Space | LiDAR | Photo loop | Measure | Facade | Arc | Details |
|---|---|---|---|---|---|---|
| …every room, one row each… | ☐ | ☐ | ☐ | N/E/S/W | ☐ | ☐ |

## 5 · Files — originals or nothing

- Copy card + phone originals UNTOUCHED (no re-export, no
  compression, no editing app in between). HEIC/DNG/JPG as shot;
  keep folder = one capture set; keep the SRT logs with the drone
  set. Do not delete anything in the field, even "bad" frames.
- Note per set: date, weather, what it covers, your measured
  distances.

## 6 · Ten-minute check before leaving site (if the Mac is along)

Copy ONE room's photo set → run the preview reconstruction
(`helpers/photogrammetry`, preview level — takes well under a minute
per small set on the studio Mac, measured). If it aligns: pack up. If
it's holey: reshoot that room now with tighter spacing. No Mac on
site: recount frames per room against the checklist instead (a
40 m² room wants 40+ frames, not 12).

## A · Per-aircraft appendix

**DJI Mini family (the default).** Resolved per set from the files'
own metadata — fly any Mini. Known rolling-shutter constants (ODM
database, read 2026-08-29): Mavic Mini v1, Mini 3, Mini 3 Pro,
Mini 4 Pro — these correct automatically at the pinned mode. Any
other Mini (2 / SE / 2 SE / 4K / 5 Pro …): reconstruction still
works; correction is off and the report says so — fly SLOWER and
stop-and-shoot everywhere, not just facades.

**Any other aircraft (blank template — fill before the flight):**
model ______ · photo mode pinned ______ · shutter type (mech/elec)
______ · grid app used ______ · RTK? ______ (only an RTK fix in the
files tightens the accuracy claim — otherwise assume meters-class
GPS and rely on measured distances).

---
*Grounding: KB `cartography.namibia` §2 + `envasset.reference_scanning`
§2–3 (A30: rules re-verified 2026-08-29 at docs.opendronemap.org/flying
+ /gcp — overlap 70–83% by scene, 60% nadir + 45° cross-grid for full
3D, ≥5 GCPs in 3–5+ images, 10–30 m inside perimeter); ODM
rollingshutter.py (read live 2026-08-29); Litchi/Dronelink Mini support
per research 56 addendum; Apple's Object Capture guide is JS-walled —
its capture rules stand here via the KB/ODM convergence and the T0
live helper probe. Absolute accuracy without survey control is
meters-class; measured distances carry the scale — no millimetre
claims in the field.*

## B · Lessons from the dry run (2026-08-29 — video-era capture, why these rules exist)

The existing site footage (all video, no stills) was pushed through the
full pipeline. What reconstruction itself taught:

- **One coherent flight per product; never mix clips.** The merged
  corpus and the room-by-room nadir clip both failed reconstruction;
  the single continuous ascent succeeded and carried the whole report.
- **Fly the survey with the site clear of moving people** — workers in
  frame poison feature matching.
- **Straight-down pans room-to-room do not reconstruct** (disconnected
  views); the grid + orbit patterns in §1 are the working shapes.
- **Without scale references, scale had to be borrowed from the design
  envelope** — the markers + measured distances in §1/§4 are what make
  the report's numbers absolute instead of relative.
