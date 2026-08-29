# Reality capture: photos/video → as-built truth → the owner's decision

The A42 lane (research 56/57/59): capture sets become registered
as-built models and a budgeted deviation report against the design.
**TEE reports; the owner decides** — the report ends in a decision menu
and nothing is ever applied without `capture_apply` carrying an explicit
decision. All tools are virtual (`tee_search_tools` finds them).

## Engines (all probed live 2026-08-29)

| Engine | Role | Install |
|---|---|---|
| Apple PhotogrammetrySession | structure/interior sets → USDZ, quality ladder preview→raw | `make -C helpers/photogrammetry` (macOS SDK only) |
| OpenDroneMap (Docker, arm64) | drone sets → orthophoto, DSM/DTM, point cloud | a Docker runtime + `docker pull opendronemap/odm` (566 MB; colima serves headless — the VM shares $HOME, and 16 GiB OOMs at full res: `colima start --memory 32`) |
| CloudCompare 2.13 | ICP registration + C2M deviation distances | `brew install --cask cloudcompare` |
| QGIS 4.x `qgis_process` | contours, hillshade, DEM difference | `brew install --cask qgis` (binary at `Contents/MacOS/qgis_process`) |
| QGIS MCP plugin | interactive GIS via the gateway (`qgis.*`, fingerprint pinned) | plugin 0.12.0 from the official directory; socket starts via its toggle |

## The flow

1. **`capture_ingest`** — files → the extract store + a set manifest.
   The DJI resolver answers per set from the files' own metadata:
   camera → shutter type → rolling-shutter correction mode (mechanical
   = off; known electronic = matched constant; known-but-no-constant,
   e.g. the Mini 2/FC7303 = off AND NAMED; unknown = off + fly-slow),
   positioning band (RTK claimed only when every file carries parseable
   RtkStd fields), gimbal/AGL priors, per-camera splits.
2. **`capture_reconstruct`** — an async job (poll `tee_job`), gated
   BEFORE submission: disk floor, engine presence, ≥10 images. Drone
   sets run ODM (`--dsm --dtm` always; `[capture] odm_args` adds e.g.
   `--feature-quality ultra` for max resolution — flags verified
   against the image's own `--help`, they drift). Structure sets ride
   the helper at `detail=preview..raw`.
3. **`capture_terrain`** — contours / hillshade / `dem_diff` from the
   DSM/DTM, headless.
4. **`capture_register`** — ICP onto the design export. THE DATUM LAW:
   the target is design truth; the capture transforms into it, never
   the reverse. RMS above the gate (default 0.05 m) REFUSES.
   `adjust_scale=true` runs 7-DOF ICP for video-derived clouds (video
   SfM has no scale) and REPORTS the factor; the ALIGNED cloud is
   saved and is what downstream C2M must consume.
5. **`capture_deviate`** — C2M → budgeted facts: per-region deltas
   with sign, peak, extent, severity (warn ≥ 10 mm, high ≥ 30 mm,
   below the 5 mm floor = measurement noise), element names from the
   design's element boxes, the capture's honesty band verbatim, and
   the menu: accept-as-built / keep-design / flag-for-site. Fact lines
   may be phrased by the routed local engine under the
   numbers-verbatim verifier — a failed phrasing leaves the
   deterministic lines standing.
6. **`capture_apply`** — ONLY on the owner's decision. keep-design /
   flag-for-site are recorded (decisions.jsonl) and mutate nothing;
   accept-as-built moves the named entity through the checkpointed
   batch path in any of the three lanes (blender / unreal /
   fabrication — per-adapter units handled: UE cm, FreeCAD mm; the
   fabrication leg regenerates the TechDraw sheet). Checkpoint id,
   diff and read-back ride every apply.

## Honesty bands (never exceeded)

Consumer GNSS = meters-class absolute. Video-derived = relative only,
scale from 7-DOF ICP, stated. RTK bands appear only when the files
prove the fix. The capture protocol (`docs/okongo-capture-protocol.md`)
is the quality ceiling — reconstruction cannot rescue a bad capture,
and the dry run proved it: a 13 s interior pan does not reconstruct; a
coherent ascent does; **stills beat video frames** (the protocol's
first rule exists because the first real corpus was all video).

## Config (`[capture]`)

`helper`, `docker`, `cloudcompare`, `qgis_process` (explicit wrong
paths refuse loudly), `min_free_gb` (20), `icp_max_rms_m` (0.05),
`align_timeout_s` (180), `odm_args` (list), `noise_floor_m`,
`sev_warn_m`, `sev_high_m`, `cluster_cell_m`.
