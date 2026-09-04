# The point-cloud lane (`pc_*`)

Turns a raw scan into a scale-verified, axis-aligned template you can trace —
while the model never sees a single point.

Design of record: `docs/research/69-pointcloud-scan-prep.md`. Plan of record:
`CLAUDE_A67_SCRIPT.md`.

## What it is for

One room scan is 3–15 million XYZ triples. Nothing useful comes from putting
those in a model's context; the useful answer is always a summary — *the floor
is 2.3° off level*, *that wall reads 4.017 m against your 4.000 m tape*. So the
points stay on disk under a `cloud_id` and every tool returns a digest.

The whole sequence below costs **682 tokens** on a 279 K-point room. Reading the
same cloud at one point in forty costs **91,820**.

## Install

```bash
cd server && uv sync --extra pointcloud
```

E57 and `pc_merge` additionally need CloudCompare
(`brew install --cask cloudcompare`); PLY, LAS and LAZ need nothing beyond the
extra. `pc_ortho` needs Pillow, which the extract lane already pulls in.

## The loop

```
pc_open  →  pc_crop  →  pc_clean  →  pc_level  →  pc_control_add ×2
                                                          ↓
                     pc_slice  ←  pc_scale_apply  ←  pc_control_verify
                     pc_section
                     pc_ortho
```

`pc_merge` sits before all of it, when a room took more than one scan.

1. **`pc_open`** — read the file, get a `cloud_id` and a digest. It reports the
   writer, SRS and point spacing it actually finds; it does not assume which
   scanner app made the file.
2. **`pc_stat`** — one topic at a time: `extent`, `density`, `z_histogram`
   (finds floor and ceiling candidates), `plane_census` (how much of this is
   real flat surface versus clutter).
3. **`pc_crop`** — keep or drop a region: a box, a z range, an XY polygon, or
   all three at once. Crop the furniture out **before** fitting and the line
   fits stop chasing clutter. The original is untouched, so an over-tight crop
   costs one `cloud_id` and nothing else.
4. **`pc_clean`** — strip points whose neighbourhood is unusually sparse (the
   strays a scanner throws through a doorway), and optionally thin to a voxel
   grid. The outlier threshold comes from the cloud's own spacing, so the same
   call works on a room scan and a site scan.
5. **`pc_level`** — RANSACs the lowest dominant horizontal plane, drops it to
   z = 0, and removes the dominant wall azimuth. Returns the residual tilt and
   floor RMS, which are the numbers that say whether to trust the result.
6. **`pc_control_add`** — record a tape or DISTO measurement. The picks are
   approximate: aim by eye and the tool snaps each onto its local surface.
   **Measure at least two distances**, as `docs/okongo-capture-protocol.md` §1
   already instructs — one baseline carries the noise of two plane fits.
   Pass **`horizontal: true`** for a room width. A tape is held level, and the
   two clean faces are often at different heights — on the Okongo scan the
   south side is a cabinet front below 930 mm and the north side is a curtain —
   so the straight 3D distance between two picks is a diagonal.
7. **`pc_control_verify`** — compares every baseline against its tape reading
   and suggests one uniform scale. If the baselines disagree by more than their
   tolerance it says **drift**, not scale, and tells you no single factor will
   fix it.
8. **`pc_scale_apply`** — apply that factor (or an explicit one).
9. **`pc_slice`** / **`pc_section`** — a horizontal or vertical cut, fitted to
   line segments, written as DXF (metres, `$INSUNITS = 6`) and SVG (with a 1 m
   reference square). This is the thing you trace over.
10. **`pc_ortho`** — a rectified orthographic PNG of one facade. No perspective,
    so a millimetre is the same length everywhere on the image; the scale bar
    and origin cross are burned into the pixels, so a cropped or re-pasted copy
    still measures. `depth_m` keeps only the near skin of the wall, which is how
    you stop the room behind a doorway bleeding into the elevation.
11. **`pc_export`** — write the cloud back out (ply/las/laz/e57), optionally
   decimated.
12. **`pc_report`** — a one-page QA sheet, and a six-line verdict:
   TRUSTWORTHY / USABLE / SHAPE ONLY / UNRELIABLE / UNVERIFIED / NOT READY.
   File it next to the DXF; it is what tells you whether to trust a drawing
   traced off this cloud.

Every step that changes geometry mints a **new** `cloud_id` and records its
parent, so nothing is destroyed and the lineage is auditable.

A control baseline rides along that lineage, but only where it stays true. A
crop moves no point, so a baseline whose two picks survive it is still exactly
true of the cropped cloud and is carried; one whose pick was cropped away
measures surfaces this cloud no longer has, so it is **dropped with a note**.
That case is the common one, because the usual reason to crop is that the snap
found the wrong face.

## What it deliberately does not do

- **It does not implement registration.** `pc_merge` exists, but it is a
  wrapper: the ICP, the refusing RMS gate and the 7-DOF degeneracy guard are all
  `capture/align.py`'s, driving CloudCompare. What `pc_merge` adds is a frame it
  named itself (both clouds are shifted by the datum's centroid before they are
  written out, so a site cloud in UTM does not get silently re-centred), and a
  **second opinion on the fit**: CloudCompare's RMS is over the correspondences
  it chose, so `pc_merge` also reports how much of each scan actually landed
  within 50 mm of the datum. A 38 mm RMS at 41% overlap is a real merge; the
  same RMS at 4% overlap is two scans of different rooms.
- **It does not decide what is a wall.** `pc_slice` emits line segments. Calling
  them walls is interpretation, and scan-to-BIM is out of scope by decision.
- **It does not produce drawings.** No sheets, title blocks or dimension
  strings — it emits templates to trace on.
- **It does not mesh, and it is not a viewer.** CloudCompare is free and better.

## Three things that will bite you

The first two are measured, silent, and handled inside `pc_export`:

- **PLY vertices are float32.** A cloud on UTM coordinates loses **250 mm**
  through a PLY round trip. `pc_export` always origin-shifts and records the
  offset; add `origin_offset_m` back to recover absolute position.
- **LAS quantises.** The conventional 1 mm scale spends 0.5 mm of your
  tolerance budget for nothing. This lane writes 0.1 mm, which costs no extra
  bytes and still addresses ±214 km.

The third bites in the other direction — it is about **your** numbers, not the
lane's:

- **`pc_crop` works in the cloud's own frame, and a PLY round trip moves it.**
  Because PLY origin-shifts, re-opening an exported cloud puts the floor at
  z ≈ −1.36 rather than 0, so `z_range: [0.05, 2.35]` reads as "floor to
  ceiling" and silently returns the top half of the room. That is not a bug in
  the crop; it is a request in the wrong frame. `pc_crop` now says so in one
  line — `z 0.05..2.35 reaches past this cloud (z is -1.584..1.356)` — and
  `pc_open` reports the bbox, which is where to read the frame from.

## When the answer is "your room has two of that wall"

The lane's most useful refusal is `drift, not scale`, and on a real building it
usually means neither drift nor scale — it means a **face ambiguity**. Room 01
of the Okongo scan presents two parallel north surfaces 90 mm apart at every
height (a full-height curtain and the wall beside it), a south surface 140 mm
broad, and four parallel west surfaces over 460 mm. Depending which pair you
choose it is 3844, 3865, 3929 or 4019 mm across.

No uniform factor repairs that, and `pc_control_verify` says so rather than
returning a number. When it does, the fix is not a better algorithm: it is one
tape reading taken to a **named** face. `pc_ortho` is how you find out what the
faces are — the curtain above was invisible in every number and obvious in the
elevation.

## Accuracy, honestly

Phone LiDAR drifts 6–9 cm over a building. The cloud gives you shape; your tape
gives you dimensions. That is the whole reason `pc_control_*` exists — and it is
the input A42's registration never had, which is why that campaign had to borrow
its scale from the design envelope.

On the synthetic fixture (`server/tests/fixtures_pointcloud.py`, a 4.000 × 3.000
× 2.700 m room at 15 mm sampling with 12 mm noise, tilted 2.3°/1.1°, yawed 37°
and mis-scaled ×1.004):

| | measured | gate |
|---|---|---|
| residual tilt after `pc_level` | 0.0000° | ≤ 0.05° |
| floor-plane RMS | 11.7 mm | 12 mm ± 20% |
| wall azimuth error | 0.031° | ≤ 0.5° |
| interior dimensions from `pc_slice` | +2.1 / −0.8 mm | ± 5 mm |
| scale factor from one tape baseline | 161 ppm | ≤ 500 ppm |
| dimensions after `pc_scale_apply` | +1.4 / −1.3 mm | ± 2 mm |

Those are gates in `server/tests/test_pointcloud_geometry.py`, not claims.

### And on a real scan

The synthetic room is a fixture; the Okongo bedroom is 900,000 real points from
a phone. Measured 2026-09-04, driving the four second-pass tools through the
registry:

| | |
|---|---|
| `pc_crop` to a 2.2 m band | 900,000 → 623,548 in 0.04 s |
| `pc_clean` outliers | 17,728 removed (2.8%) in 0.5 s; spacing 29.9 → 28.8 mm |
| `pc_ortho` of the cabinet wall | 340 × 221 px at 10 mm/px in 0.02 s, 92% covered |
| `pc_merge`, two halves rotated 4° and moved 145 mm apart | ICP RMS 38.9 mm, 41% overlap, 10.0 mm RMS **within** the overlap; the reassembled bbox is within 6 mm of the original in x |

The `pc_clean` number is the one worth reading twice: it removed 2.8% of the
points and the median spacing barely moved (29.9 → 28.8 mm). That is the right
signature — it took sparse strays, not surface.
