# 67 — Garment CAD + drape lane: a Marvelous Designer / CLO3D-class tool (2026-09-01)

Research of record for **A53**. Every licence and platform claim below was
fetched on 2026-09-01 (URLs inline) or measured on this machine. Claims
carried from earlier TEE research are marked `(doc NN)`.

## 1. The parity target — what MD/CLO actually are

One loop, repeated: **2D pattern pieces → sewing relationships → arrange
around a body → simulate → inspect fit → export.** Everything else is
decoration on that loop. Feature inventory, grouped, as the parity
checklist:

| Group | Capability |
| --- | --- |
| A. Pattern (2D) | closed panel outlines (line/arc/Bézier), internal lines, notches, darts, pleats, seam allowance, grain line, fold/mirror, drill holes, grade rules, measurement-driven parametrics |
| B. Sewing | edge→edge and segment→segment seams, N:1 seams, seam direction/flip, gathering ratio, elastic, topstitch |
| C. Avatar | parametric body, measurements, poses, skin offset, morph targets |
| D. Arrangement | placement of panels on arrangement volumes/points around the body **before** the solve |
| E. Simulation | particle distance (mesh resolution), fabric parameters, gravity/wind/pressure, pinning, layers, body collision + self-collision |
| F. Evaluation | stress/strain/pressure fit maps, ease measurement, fabric consumption / marker, tension |
| G. Material & render | texture/print placement, normal + displacement, UV = the 2D panel (free by construction) |
| H. Export | OBJ/FBX/glTF/USD/Alembic; DXF-AAMA/ASTM; SVG + PDF plotter; tech pack |
| I. Animation | pose-sequence draping, cached playback |

**The gap worth building into.** Marvelous Designer *has* a Python API —
but it is an **in-app script editor** (Main Menu → Script → Python) and
it is sold **only on a new Enterprise-tier subscription**, not with
ordinary seats. There is no documented headless/batch mode.
(<https://developer.marvelousdesigner.com/python.html>; API-list page
returns HTTP 403 to non-browser clients; tier per CG Channel's Oct-2025
Linux-launch coverage.) A tool whose **headless surface is the primary
surface, and whose GUI is a client of it**, is therefore not a clone —
it is the inversion of the incumbent's architecture, and it is exactly
what TEE exists to drive.

**IP guardrail.** Feature parity is fine; the proprietary containers are
not. Implement open interchange (DXF-AAMA/ASTM, OBJ/glTF/USD, SVG/PDF).
Do **not** reverse-engineer `.zprj`/`.zpac`, reuse their UI chrome, or
carry their branding.

## 2. The licence minefield — the finding that matters most

This domain is unusually mined. Every attractive component in the
research literature is non-commercial; the permissive equivalents exist
but are not the ones the papers use.

| Component | Licence | Verdict |
| --- | --- | --- |
| **GarmentCode / PyGarment** (ETH) | **MIT** | usable — parametric sewing-pattern DSL, panels/edges/interfaces |
| **its simulator** (`NvidiaWarp-GarmentCode` fork) | **NVIDIA Source Code Licence — non-commercial** | **cannot ship**. The whole GarmentCodeData draping pipeline runs on this fork |
| **NVIDIA Warp** (mainline) | **Apache-2.0** | usable — but see §3, CPU-only on macOS |
| `warp.sim` (its cloth/VBD module) | Apache-2.0 | **deprecating** in favour of Newton — do not build on it |
| **Codim-IPC (C-IPC)** | **Apache-2.0** | usable — accuracy gold standard: thickness, friction, strain limiting, no intersections |
| **SMPL / SMPL-X / STAR** | non-commercial (MPI); commercial only via Meshcapade | **cannot ship** |
| **Anny** (NAVER LABS) | **Apache-2.0**, assets CC0 (MakeHuman/MPFB2) | **usable — this is the avatar answer** |
| Anny's `smplx` topology download | non-commercial only | **do not fetch it** |
| **Triangle** (Shewchuk) + `meshpy`/`triangle` wrappers | "may not be sold or included in commercial products without a licence" | **cannot ship** |
| **CDT** (artem-ogre) | **MPL-2.0** | usable — robust constrained Delaunay, header-only C++ |
| **Seamly2D / Valentina** | GPLv3+ | reference + format target only, not linkable |
| **Patro** (PyValentina) | AGPLv3 | **documentation** is citable; code is not linkable |
| **ArcSim measured cloth data** | non-profit only (doc 34) | **cannot ship** — encode GSM/thickness ranges as cited facts instead |
| **ezdxf** 1.4.4 | MIT | usable, already installed |

Sources: <https://github.com/maria-korosteleva/GarmentCode>,
<https://github.com/maria-korosteleva/GarmentCode/blob/main/docs/Running_data_generation.md>,
<https://github.com/NVIDIA/warp>, <https://github.com/ipc-sim/Codim-IPC>,
<https://github.com/naver/anny>, <https://smpl.is.tue.mpg.de/modellicense.html>,
<https://www.cs.cmu.edu/~quake/triangle.html>,
<https://github.com/artem-ogre/CDT>, <https://github.com/FashionFreedom/Seamly2D>.

**The one-line version:** the best-documented open garment pipeline in
the world (GarmentCodeData) cannot be shipped, because its *simulator*
is non-commercial even though its *patterns* are MIT. Anyone who copies
the paper's stack inherits that, silently.

## 3. The solver landscape, and the Apple Silicon reality

- **NVIDIA Warp is Apache-2.0** and publishes macOS Apple-Silicon wheels
  — but *"The macOS wheels support CPU execution but not Metal
  acceleration."* (README, fetched 2026-09-01). On this machine Warp is
  a CPU library. CUDA acceleration needs an NVIDIA GPU.
- **C-IPC** (Apache-2.0) is the accuracy tier: codimensional IPC with
  controllable thickness, fully coupled strain limiting, accurate
  friction, and non-intersection guaranteed at every timestep. It is
  offline-speed C++/CUDA — a *bake*, not an editor loop.
- **Blender's cloth** is already reachable headlessly from TEE today:
  `modifiers.new('CLOTH')`, synchronous `ptcache.bake`, and a free
  compact health report in `solver_result` (status + avg/max error +
  iterations); its five fabric presets are extractable as plain enums
  (doc 32). This is the zero-new-code baseline every candidate must beat.
- **Metal is reachable from Python two ways today**: `torch` MPS —
  **measured available on this machine, torch 2.13.0, in TEE's own venv**
  — and MLX's custom-kernel escape hatch `mlx.core.fast.metal_kernel`
  (MLX 0.32.2 docs), which JIT-compiles a Metal source string.

**Therefore the design is two-tier, and P0 must measure before choosing:**
an interactive XPBD/VBD tier behind a pluggable backend, and an opt-in
barrier-method bake tier. The premise that "GPU = CUDA" is false here;
the premise that "torch-MPS is fast enough for XPBD" is *unmeasured* and
must not be assumed — A51's law.

## 4. Pattern interchange: DXF AAMA / ASTM

**ASTM D6673-10 — "Standard Practice for Sewn Products Pattern Data
Interchange – Data Format" — was WITHDRAWN in 2019.** It remains the de
facto interchange anyway (Valentina 0.7 added AAMA/ASTM DXF explicitly
for CLO3D and Investronica compatibility). It is based on **AutoCAD DXF
R13**; one style per file; **one DXF block per pattern piece**; detail
assigned to **23 predefined layers**:

| Layer | Holds |
| --- | --- |
| 1 | piece boundary (+ style system text) |
| 2 | turn points (for layers 1, 8, 11, 14) |
| 3 | curve points (for layers 1, 8, 11, 14) |
| 4 | notches — V-notch, slit-notch, alignment |
| 5 | grade reference / alternate grade reference lines |
| 6 | mirror line (fold symmetry) |
| 7 | grain line |
| 8 | internal lines (annotation, not cut) |
| 9 / 10 | stripe / plaid reference lines |
| 11 | internal cutouts (cut inside the outline) |
| 13 | drill holes |
| 82 | check notch |
| 84 / 85 / 86 / 87 | quality-validation curves for layers 1 / 8 / 11 / 14 |

Layer 0 is unused. AAMA and ASTM **assign features to different layer
numbers and use point codes differently** — so this must be a *dialect
table*, not a hardcoded map. Grade-rule tables travel as a separate
formatted ASCII file, not in the DXF.
Source: <https://fabricesalvaire.github.io/Patro/resources/file-format/dxf-astm.html>
(Patro docs, AGPLv3 project — cited, not linked), ASTM store listing for
D6673-04/-10.

**Known gotcha:** ezdxf's default layout blocks make ASTM importers
fail — the standard expects *every* block to be a pattern piece
(ezdxf discussion #789). Write the DXF with only piece blocks.

## 5. Fabric parameters

The measurement vocabulary is standardised and vendor-neutral:
**KES-F** = four instruments — FB1 tensile + shear, FB2 bending, FB3
compression, FB4 surface friction + roughness. CLO's own fabric kit
measures **tensile / bending / shear stiffness, weight, thickness**, with
samples cut in **warp, weft and bias**. Studies report drape coefficient
correlating with bending and shear properties, friction MD, and tensile
linearity, with r ≈ 0.97 between real and KES-driven virtual drape.
IEEE's 3D Body Processing group has a public note on measuring fabric
properties for virtual simulation (PDF).

Schema rule, carried from doc 34: keep an explicit **tier flag** per
value — `measured` (with citation) vs `plausible` (solver constant tuned
to look right). ArcSim's measured cloth set is non-profit-only and must
not be shipped; publishable GSM/thickness ranges are facts and may be.

## 6. What this machine and this repo already have

Measured 2026-09-01 in TEE's own venv (`server/`):

```
Apple M5 Max, 128 GB unified, macOS 26.6.2, os.cpu_count() = 18
torch 2.13.0   mps available=True built=True
shapely 2.1.2  ezdxf 1.4.4  trimesh 5.0.0  numba 0.67.0  numpy 2.4.6
scipy 1.17.1   fpdf2 2.8.8  pypdf 6.16.2   pypdfium2 5.13.0
(absent: mlx, PySide6, warp-lang)
```

`shapely` + `ezdxf` + `trimesh` + `numba` + `torch`-MPS is, almost
exactly, the dependency set a garment kernel needs — already installed,
already licence-audited by this project.

## 7. TEE-side reuse map (why this belongs here)

| Need | Existing TEE lane |
| --- | --- |
| declarative garment ops, one round trip | `tee_batch` + the Adapter protocol (zero new always-loaded tools) |
| "what changed" after an edit | `tee_diff`, the diff discipline |
| pattern edit history | checkpoint / rollback machinery |
| plotter sheets + tech pack | `pdf_compose` (A48) |
| a look at the drape without pixels-by-default | `tee_capture` budgeted, Blender adapter for render |
| fit "does this read as a shirt" second opinion | `sense_*` VLM (A47/A51) — **advice, not measurement** |
| garment reference from a photo | voxkiln |
| fabric facts with citations | `kb` + `tee_web_lookup` |
| cheapest capable engine | the A39 second pillar, applied to *physics* instead of language |

## 8. Defect found while doing this research

`tee_web_lookup` on an `application/pdf` URL returns **raw PDF bytes as
the quote** (`%PDF-1.7 %âãÏÓ 3085 0 obj …`) instead of extracted text or
an honest refusal. `server/src/tee/web/fetch.py` has no content-type
branch, and `web/extract.py:229` even tells the caller to use "the media
lane for images/PDF" — a fix that the code never routes to. TEE already
ships `pypdfium2` and `pypdf`. Standards and textile research live in
PDFs, so this lane is directly on A53's path. Filed as A53 P0.

## 9. P0 answered these (2026-09-01 — measured, see PROGRESS)

1. **The GPU lost.** `numba` CPU XPBD with a **4-thread** pool: 5.2 ms/frame
   at 30k particles, 8.7 at 120k, 24.1 at 500k — against torch-MPS at 13.9 /
   20.1 / 50.3 and Blender's own cloth at 476.7 / 2,052.8 / —. numba-xpbd is
   the default backend.
2. **More threads is slower.** At 5k particles 1 thread beats 18 by **8.7×**
   (2.3 ms vs 20.1). The fork/join barrier around each of a frame's 144
   parallel regions scales with pool size; the work per region does not.
   Four threads is optimal above ~50k; eighteen never wins.
3. **`numba.set_num_threads` cannot fix it** — 11.6 ms on a masked pool of 18
   vs 2.3 ms with `NUMBA_NUM_THREADS=1` at process start. The pool is sized at
   import; the env var is the only lever.
4. **Warp on this Mac is CPU-only, as its README says** — verified, not
   quoted: Warp 1.17.0 reports `CUDA not enabled in this build`, devices
   `"cpu": "arm"`. It wins below ~10k (1.8 ms at 5k) and loses above.
5. **Blender's `solver_result` is None on the modifier** — it exists only on
   the *evaluated* object. Doc 32 called it a free health report without
   saying where to read it; correction recorded there and in PROGRESS.

Still open, for later phases: constrained-Delaunay throughput on real panel
outlines with notches and cutouts (P2), and Anny's cold-start cost (P3).

## 9b. Original open questions (kept for the record)

1. ms/frame for 30k-particle XPBD on: torch-MPS, numba-CPU (18 cores),
   warp-lang CPU, and Blender's own cloth bake — same garment, same
   frame count. **The default backend is whichever number wins**, not
   whichever is fashionable.
2. Does `warp-lang` on this Mac really refuse Metal (README says yes —
   verify, don't quote).
3. Constrained-Delaunay throughput and robustness on real panel outlines
   with notches and internal cutouts.
4. Anny cold-start cost (it parses MakeHuman assets and caches to
   `~/.cache/anny/`; "first instantiation can take a few minutes").
