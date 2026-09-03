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

E57 additionally needs CloudCompare (`brew install --cask cloudcompare`); PLY,
LAS and LAZ need nothing beyond the extra.

## The loop

```
pc_open  →  pc_level  →  pc_control_add ×2  →  pc_control_verify  →  pc_slice
                                                      ↓
                                             pc_scale_apply (if needed)
```

1. **`pc_open`** — read the file, get a `cloud_id` and a digest. It reports the
   writer, SRS and point spacing it actually finds; it does not assume which
   scanner app made the file.
2. **`pc_stat`** — one topic at a time: `extent`, `density`, `z_histogram`
   (finds floor and ceiling candidates), `plane_census` (how much of this is
   real flat surface versus clutter).
3. **`pc_level`** — RANSACs the lowest dominant horizontal plane, drops it to
   z = 0, and removes the dominant wall azimuth. Returns the residual tilt and
   floor RMS, which are the numbers that say whether to trust the result.
4. **`pc_control_add`** — record a tape or DISTO measurement. The picks are
   approximate: aim by eye and the tool snaps each onto its local surface.
   **Measure at least two distances**, as `docs/okongo-capture-protocol.md` §1
   already instructs — one baseline carries the noise of two plane fits.
5. **`pc_control_verify`** — compares every baseline against its tape reading
   and suggests one uniform scale. If the baselines disagree by more than their
   tolerance it says **drift**, not scale, and tells you no single factor will
   fix it.
6. **`pc_scale_apply`** — apply that factor (or an explicit one).
7. **`pc_slice`** / **`pc_section`** — a horizontal or vertical cut, fitted to
   line segments, written as DXF (metres, `$INSUNITS = 6`) and SVG (with a 1 m
   reference square). This is the thing you trace over.
8. **`pc_export`** — write the cloud back out (ply/las/laz/e57), optionally
   decimated.
9. **`pc_report`** — a one-page QA sheet, and a six-line verdict:
   TRUSTWORTHY / USABLE / SHAPE ONLY / UNRELIABLE / UNVERIFIED / NOT READY.
   File it next to the DXF; it is what tells you whether to trust a drawing
   traced off this cloud.

Every step that changes geometry mints a **new** `cloud_id` and records its
parent, so nothing is destroyed and the lineage is auditable.

## What it deliberately does not do

- **It does not register clouds.** `capture_register` already does that, through
  CloudCompare, with a refusing RMS gate and a 7-DOF degeneracy guard. Register
  there, then `pc_open` the aligned result.
- **It does not decide what is a wall.** `pc_slice` emits line segments. Calling
  them walls is interpretation, and scan-to-BIM is out of scope by decision.
- **It does not produce drawings.** No sheets, title blocks or dimension
  strings — it emits templates to trace on.
- **It does not mesh, and it is not a viewer.** CloudCompare is free and better.

## Two things that will bite you if you work around the lane

Both are measured, both are silent, and both are handled inside `pc_export`:

- **PLY vertices are float32.** A cloud on UTM coordinates loses **250 mm**
  through a PLY round trip. `pc_export` always origin-shifts and records the
  offset; add `origin_offset_m` back to recover absolute position.
- **LAS quantises.** The conventional 1 mm scale spends 0.5 mm of your
  tolerance budget for nothing. This lane writes 0.1 mm, which costs no extra
  bytes and still addresses ±214 km.

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
