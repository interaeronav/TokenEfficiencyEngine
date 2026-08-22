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
