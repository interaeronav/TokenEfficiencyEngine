# Voxkiln benchmarks

Append-only. Never overwrite a dated section; every "improved over stock"
claim must trace to a row here (research 48).

---

## 2026-08-22 — Mac battery: ATTEMPTED, NO ROWS MEASURED

```yaml
voxkiln_commit:  f8a0857
upstream_commit: 75fbf0183001ed9876c8dbb35de6b68552ee08bd
torch:           2.13.0
macos:           26.6.2
machine:         Apple M5 Max, 128 GB unified memory
backend:         mps (SPARSE_ATTN_BACKEND=sdpa, SPARSE_CONV_BACKEND=none)
pipelines:       512, 1024_cascade   (planned)
seeds:           [0, 42, 1234]       (planned)
thermal_protocol: cool start, median-of-3 timings, geometry from run 1
status:          BLOCKED - zero rows measured
```

### Why there are no numbers

The battery could not run. The image-conditioning tower named by the
pipeline config — `facebook/dinov3-vitl16-pretrain-lvd1689m` — is **gated
on Hugging Face with manual approval**, and this machine's account is not
on the authorized list:

```
GatedRepoError: 403 Client Error.
Access to model facebook/dinov3-vitl16-pretrain-lvd1689m is restricted
and you are not in the authorized list.
```

This is an access-control blocker, not a code one. Nothing about the
parameters, the backend or the machine changes it.

**To unblock:** request access at
<https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m>, wait for
manual approval, then `hf auth login`. `voxkiln doctor` reports the state
under `gated_weights`, and `tee doctor` shows it on the `voxkiln` line.

### What *was* established on this machine

Not benchmarks — preconditions. Recorded so the next session starts here:

| Item | Result |
|---|---|
| Weights cached (`microsoft/TRELLIS.2-4B`) | **15.12 GB**, `voxkiln doctor` confirms |
| Frozen eval inputs | 9/9 verify against `eval_images/SHA256SUMS` |
| Backend selected | `mps`, attn `sdpa`, conv `none` |
| TRELLIS pipeline models loaded | **8/8 in 68 s** (cold, all resident) |
| Point of failure | image-conditioning tower only (gated) |
| Thermal state at run | no warnings recorded (`pmset -g therm`) |

The 68 s cold load of all eight models is a real measurement and a useful
anchor for the "pipeline load" stage that research 48 wants tabulated
(trellis-mac reported 103 s on an M4 Pro for the equivalent step), but it
is a *load* timing only — no generation, no geometry, no defect metrics.

### Rows to fill once unblocked

Per research 48: one row per input × pipeline × seed, two runs each
(stock = upstream defect-fixes-off, ours = product path), columns =
watertightness, boundary loops, non-manifold edges, degenerates,
per-component Euler, UV overlap %, texel-density CV, silhouette IoU, stage
timings, peak memory. Same-seed ×3 determinism measured, never assumed.

---

## 2026-08-27 — Mac battery, first measured rows (M5 Max, MPS)

```yaml
voxkiln_commit:  15e78e2 (incl. the two live-lane fixes e906b97, 48082c2)
upstream_commit: 75fbf0183001ed9876c8dbb35de6b68552ee08bd
torch:           2.13.0
macos:           26.6.2
machine:         Apple M5 Max, 128 GB unified memory
backend:         mps (SPARSE_ATTN_BACKEND=sdpa, SPARSE_CONV_BACKEND=none)
pipelines:       512
seeds:           [42]
images:          T.png, 154c8867…webp   (2 of 9 frozen inputs)
arms:            ours, stock            (fresh subprocess per run, --no-cache)
thermal:         no warnings recorded (pmset -g therm), quiet machine
status:          4/4 rows OK — see the no-delta finding below
scope_note:      deliberately a first tranche, not the full research-48
                 matrix (9 images × {512,1024_cascade} × 3 seeds); nothing
                 else was run, nothing is sampled silently
```

### Determinism (measured, not assumed — research 48)

Two full same-seed runs, fresh subprocess each (`benchmarks/determinism.py`,
seed 42, pipeline 512): both produced **mesh_hash 52b60b5bf50b3502**,
491,888 tris / 390,301 verts — `deterministic: true` on this device.
Rows in `benchmarks/local_out/determinism.json`.

### Rows (`benchmarks/local_out/battery_rows.json`)

| image | arm | ok | wall s | tris | watertight | boundary loops | non-manifold edges | degen | components | mesh hash |
|---|---|---|---|---|---|---|---|---|---|---|
| T.png | ours  | ✓ | 839.5 | 491,888 | false | 5,017 | 14,846 | 0 | 1,066 | 52b60b5bf50b3502 |
| T.png | stock | ✓ | 848.7 | 491,888 | false | 5,017 | 14,846 | 0 | 1,066 | 52b60b5bf50b3502 |
| 154c8867…webp | ours  | ✓ | 286.9 | 454,552 | false | 2,881 | 10,660 | 1 | 5,405 | 9ea1c833820180b5 |
| 154c8867…webp | stock | ✓ | 284.6 | 454,552 | false | 2,881 | 10,660 | 1 | 5,405 | 9ea1c833820180b5 |

Stage timings (determinism run 0, representative): pipeline 51 s, export
718 s of which unwrap 442 s, stats 142 s, repair 71 s, simplify 44 s.
UV unwrap dominates end-to-end wall time on this machine.

### Finding: no stock-vs-ours delta on this backend (measured)

Per image, both arms produced **identical mesh hashes** — the fp32
threshold fixes changed nothing here. The switch wiring was verified live
(`VOXKILN_STOCK` reaches the subprocess; both gated sites import `STOCK`).
Hypothesis, deliberately labelled UNVERIFIED: on the MPS path the gated
tensors are already fp32, so the `.float()` upcasts are no-ops — the
defect the fixes target is fp16 rounding (research 44), a CUDA-fp16
phenomenon. Next session: probe the runtime dtype at the two gated sites,
and if fp32 is confirmed, the "ours improves over stock" claim must be
scoped to fp16 backends — no row here supports it on MPS.

### Live-lane fixes the battery is standing on (this session)

- `repair.py` `_winding_for_fill` rebuilt the full directed-edge dict per
  hole — quadratic; 'fast' repair ran for hours at 100% CPU with no output
  (both early stalls dumped exactly there). Edge set now built once per
  fill pass (e906b97).
- `jobs._execute` forwarded the CLI's `None` params over `export_glb`
  defaults — default CLI runs crashed at simplify (48082c2).

### Addendum (same day, later session): the no-delta finding is RESOLVED

The runtime dtype at the gated decode-threshold site was probed during a
real stock-mode generation (F.sigmoid wrapper on the decode head):

```
[PROBE] gated decode-head tensor dtype: torch.float32
```

On MPS the vendored port keeps the decode head in fp32 (fp16 torso, fp32
primitives — 76 fp32 / 216 fp16 params in shape_slat_decoder), so the
ours-arm `.float()` upcasts are no-ops and the arms are hash-identical *by
construction* on this backend. The "ours improves over stock" claim is
hereby scoped to fp16 backends (CUDA); no MPS row can support or refute
it, and the earlier UNVERIFIED label is lifted.

## 2026-08-27 — SI-2 stats-stage fixes (A33 campaign)

Profiled on `ours_T_512_42` (491,888 tris, 22,108 components):
`mesh_stats` spent 189 s in `trimesh.split()` (a Trimesh per component,
for a count) and 67 s in `outline()` (path traversals, for a loop
count). Both now count graph components directly: **275.8 s → 13.7 s on
the same mesh under the same load** (commit cb7e377). Component counts
are unchanged; `boundary_loops` moves to a CC-of-boundary-edges
definition (this mesh: 22,892 new vs 27,593 traversal-entity count) —
rows above this section used the old definition. `battery_rows_t2.json`
(tranche 2, started before the change) also carries old-definition
boundary loops; mesh hashes are unaffected by metrics.

**Correction (2026-08-28):** the SI-2 note above measured its component
census on the exported GLB — post-unwrap, where xatlas seam-splitting
fragments connectivity to 22,108 pieces. The decode meshes have
~1,066–1,081 components (see rows). The timing fixes are unaffected
(measured on the same mesh before/after); the export pipeline's own
stats stages run pre-unwrap, so their in-pipeline delta comes from the
next battery export.

### Tranche 2 (2026-08-28, A33 SI-2.2): two more images, single-arm

Per the fp32 finding, stock≡ours on MPS by construction, so remaining
configs run one arm. `benchmarks/local_out/battery_rows_t2.json`
(seed 42, pipeline 512, ours):

| image | ok | wall s | tris | watertight | components | mesh hash |
|---|---|---|---|---|---|---|
| 1c359e94…webp | ✓ | 978.0 | 491,139 | false | 1,081 | 1fa684bf32e5f720 |
| 3903b879…webp | ✓ | 456.4 | 494,685 | false | 2,042 | cf848d25296f9a41 |

Caveat: the boundary_loops column of these rows may mix the old and new
definitions (the metrics change landed mid-tranche); hashes and every
other field are unaffected. Covered so far: 4 of 9 images at seed 42 /
pipeline 512. Remaining: 5 images × this config + the other pipeline ×
3 seeds ≈ 5–8 h single-arm, staged for future sessions or an
owner-scheduled window.

## 2026-08-28 — repair-stage fix (the queued SI-2 follow-through)

Profiled on the T-machine mesh (491,888 tris; the pass twice killed by
memory pressure under concurrent generation finally ran on a quiet
machine): `repair(level="fast")` spent 302.8 s of 326.8 s inside
`_cull_small_components` — `trimesh.split()` built a Trimesh per
component (~30K on this mesh; 167 s of pure cache hashing) and
`concatenate` rebuilt the survivors for another 112 s. Now the same
face-graph labeling `mesh_stats` uses (cb7e377) plus one boolean face
mask: **326.8 s → 9.5 s on the same mesh** (34×), voxkiln suite green.

Definition note (the SI-2 boundary-loop precedent): component area is
now the sum of the component's own face areas on the actual mesh.
`split()`'s reprocessed parts carried ~0.4% duplicated faces (494,060
part-faces vs the mesh's true 491,888 on this input), so 36
borderline-tiny components the inflated measure kept (2,174 faces,
0.32% of area) now correctly fall under the negligible-share threshold.
Grouping itself is identical (21,894 components both ways, verified).

## 2026-08-28 — tranche 3: the seed-42 sweep completes (9/9 images)

Five remaining eval images run single-arm (ours; stock≡ours by
construction on MPS per the 38c1672 fp32 finding), seed 42, pipeline
512 → `battery_rows_t3.json`, all ok. Wall 270–1,593 s per config —
the repair-stage fix (326.8 → 9.5 s, this file, above) is inside these
numbers. Coverage after tranche 3: all 9 eval images at seed 42;
remaining matrix (extra seeds) stays open as future tranches. Rows
carry the current component-cull and boundary-loop definitions.

## 2026-08-29 — unwrap-stage fix + a byte-deterministic artifact (A35 P2.3)

Profiled on a frozen fixture captured from a REAL run (T.png, seed 42,
pipeline 512: 3,049,618-face decode → repair → staged simplify →
488,002-face unwrap input), quiet machine. Native-stack sampling put the
whole cost in `xatlas::ComputeCharts`; the full lever matrix confirmed
it — every pack-side option (blockAlign, rotate_charts, resolution,
normal-seam) landed within noise of the 895.4 s baseline, weld was a
no-op (repair already merges vertices), and **`ChartOptions.max_iterations
= 0` — skipping xatlas's single chart-optimization pass — took the same
unwrap to 12.4 s (72×)**. Cost of the trade, measured on the same
fixture: charts 20,360 → 26,217 (+29%), unwrapped verts 386,889 →
406,781 (+5% seam duplication), atlas 1259² → 1272² (~equal), full UV
span both ways; the bake already inpaints chart seams. In the pipeline:
**export 1,037 s → 151 s, full generation 1,168 s → 277 s** on the
same image/seed/machine. (The older "unwrap 442 s" row was measured
under CPU contention on an earlier decode; tonight's baseline for the
same config is 895 s solo — both are honest numbers for their day, the
72× is like-for-like within one session.)

**Found while verifying, then fixed: the shipped artifact was never
run-stable.** Same-seed decode meshes are array-identical (re-verified
three ways tonight — the determinism contract holds), but two exports
of the SAME decode differed in 52% of covered texels (~2/255 mean
channel delta, occasional large seam deltas): `_project_to_reference`
sampled the reference surface with an UNSEEDED `sample_surface`, so
every bake projected against a different 2M-point cloud. Seeded
(seed=0, same approximation bound by construction). After both changes,
two independent full generations produce **byte-identical GLBs**
(sha256 822b58de…, 17,454,048 bytes) — decode-hash determinism is now
artifact-byte determinism. Suite 48 passed / 1 skipped throughout.
