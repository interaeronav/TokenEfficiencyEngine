# CLAUDE_A46_SCRIPT.md — leaner, faster, and fitted to this machine

**Owner directive (2026-08-31):** *"create a script to improve, and optimize
the TEE, make it leaner and faster and optimize to work with the local
engines and the projects that I have in claude."* Then: *"once script is
complete, run and execute it without my prompt. I will be at work."*

So: autonomous execution, and every claim measured before and after.

---

## What the measurements actually say

Taken on this machine, 2026-08-31, before any change.

**Leaner — the weight is NOT where it looks.**

| | size | pulled in by | what TEE uses it for |
|---|---|---|---|
| `vtkmodules` | **592 MB** | cadquery-ocp | **nothing** — it is a rendering toolkit |
| `torch` | **505 MB** | monai | min / max / mean of an array |
| `OCP` | 224 MB | cadquery | the real CAD kernel (legitimate) |
| `casadi` | 158 MB | cadquery | its assembly solver — TEE never assembles |
| `llvmlite` | 129 MB | numba ← cadquery, pandas | JIT TEE never triggers |
| scipy / ortools / pandas | 197 MB | solve, quant | genuinely used |

**Installed extension venv: 2.2 GB.** Roughly **1.4 GB of that is bought by
two features TEE uses shallowly**: reading a STEP file's volume, and taking
scalar statistics of an image.

**Faster — the core is already fast, so do not "optimise" it.**

```
TeeApp import + construct : 0.02 s        <- not the problem
tee.app import cost       : 12.8 ms
CadQuery FIRST import     : 140 s         <- the problem
MONAI/torch FIRST import  : > 60 s (timed out a live tool call)
```

The bundle is 882 KB, of which **`uv.lock` is 1.0 MB uncompressed** — the
single largest item, and it grows with every extra even though extras are
never installed from the bundle.

**Fitted — TEE cannot currently reach the owner's local models.**
`kernel/machine.py` knows `q14b+a2` / `q27b-bare` (profiles `q14b`,
`q27b`). The owner's LiteLLM shim actually serves:

```
claude-qwen-27b        Qwen3.8-27B bf16          local
claude-qwen-small      Qwen3.5-9B 4bit           local, cheap
claude-deepseek-flash  DeepSeek-V4-Flash         local
claude-qwen-vl         Qwen3-VL-30B              local, vision
claude-qwen-uncensored Qwen-3.8-27B              local
claude-qwen-max        qwen3.8-max via DashScope PAID
```

Only `qmax` is declared in `.tee/config.toml`. **Every chore either runs on
the paid engine or falls back to the deterministic path** — the free local
models are unreachable. That is the single biggest efficiency defect on
this machine and it is a config/registration problem, not a code one.

**Projects:** `DiversionPlanner-BaseMap` and `OkongoSim` are adopted into
the pipeline lane. `cosm-inspired-chair` — the chair built this week, with
a real render/export workflow — is not.

---

## The law for A46

1. **Measure before and after, in the same units, in PROGRESS.** A phase
   that cannot show a number did not happen.
2. **No capability may be lost to save space.** Weight moves to a sidecar
   or is replaced by a lighter equal; it is not simply deleted.
3. **The surface invariant holds**: 17 always-loaded tools / ~2,028 tok.
4. **Nothing is claimed working that was not run**, against the live
   installed server where that is what changed.
5. Local-first: a chore belongs on the cheapest engine that can do it. The
   paid engine stays **pin-only** and never an automatic target.

---

## P1 — cut the fat (target: 2.2 GB → under 700 MB)

- **P1a — `med_` without MONAI or torch.** MONAI's `LoadImage` is a reader
  dispatcher; TEE uses it to get an array and take scalar stats. Dispatch
  directly instead: `.dcm` → pydicom, `.nii/.nii.gz` → nibabel, `.npy/.npz`
  → numpy, images → pillow. Drops **monai + torch ≈ 505 MB**, and removes
  the >60 s first-import that already timed out a live call. MONAI stays
  supported if present (bundles, transforms) but is no longer required.
  *Acceptance:* the same known-volume test passes with torch absent.

- **P1b — CadQuery becomes a sidecar.** STEP volume genuinely needs a BREP
  kernel, so the capability stays — but in its own venv, driven as a
  subprocess exactly like `_cpsat_worker.py`. Drops **vtk + casadi +
  llvmlite + OCP ≈ 1.1 GB** from TEE's interpreter. Binary STL already
  measures natively with zero dependencies and is untouched.
  *Acceptance:* `cad_measure` on a STEP file returns the same volume it
  does today, with `cadquery` absent from TEE's own venv.

- **P1c — a bundle that does not carry what it cannot install.** Strip
  `[project.optional-dependencies]` from the bundle's pyproject before
  locking, so `uv.lock` covers base deps only.
  *Acceptance:* `.mcpb` shrinks; `uv sync` + `tee --version` still green.

## P2 — faster, and honest about state

- **P2a — `tee_status` contradicts `tee_trust`.** It reports
  `code_exec_enabled: false` from the pre-A43 `allow_code_exec` flag while
  `tee_trust` says `exec-code` is granted and `tee_script` actually runs.
  Two sources of truth for one question, disagreeing in the status output.
  Report the capability, not the legacy flag.

- **P2b — no tool call may block on a first import.** A cold `med_` or
  `cad_` call paid 60–140 s of bytecode compilation and timed out. Warm on
  first use with a bounded, reported wait, or hand the work to the sidecar.

- **P2c — tool search at 133 virtual tools.** Measure `tee_search_tools`
  latency and result quality at the current surface; fix only if measured
  to be a problem. **Do not optimise what is not slow** — that is what the
  0.02 s startup above is there to prevent.

## P3 — fit this machine

- **P3a — declare the owner's real local engines.** Add `q27b`, `qsmall`,
  `qvl`, `dsflash` profiles to `.tee/config.toml` pointing at the shim's
  actual route names, and register them in `kernel/machine.py` so the
  router can select them. *Acceptance:* a chore runs on a LOCAL engine and
  `report_spend` shows `off_machine_calls: 0` for it.

- **P3b — cheapest-capable routing.** Chores default to `qsmall`, escalate
  to `q27b` on failure, and never reach `qmax` automatically. Measured on
  the existing routing benchmark.

- **P3c — adopt `cosm-inspired-chair`.** Declare its real steps (render,
  export STL/GLB, the CAD measure loop) in `.tee/pipeline.toml`, pinned.

## Out of scope

Rewriting the kernel, new adapters, and anything that trades the surface
invariant for speed. A46 removes weight and wires what is already here to
what this machine actually runs.
