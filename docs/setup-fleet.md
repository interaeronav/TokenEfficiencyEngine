# The headless fleet — setup (A45 P2)

Sixteen open resources reachable from TEE. **Nothing here is installed by
default and nothing is bundled.** Every group is an optional extra or a
service you run; TEE's always-loaded surface stays at **17 tools / 2,028
tokens** whether you install all of it or none of it.

Everything below was installed and run on this machine on 2026-08-30/31.
Where something is *not* wired, this page says so rather than implying it.

---

## Read this before you upgrade TEE

**Installing a new `.mcpb` deletes everything on this page.** Claude Desktop
provisions the bundle with `uv sync`, which rebuilds the extension venv
strictly from `uv.lock` and discards anything installed on top of it. The
extras *are* installed on top, deliberately — A46 P1 cut the base venv from
2.2 GB to 586 MB by keeping them out of it.

Measured going 0.9.0 -> 0.10.0 on 2026-08-31: the venv fell from **586 MB to
34 MB**, taking numpy, pandas, scipy, pydicom, nibabel, skfolio, pypfopt,
highspy and ortools with it.

The failure is quiet rather than loud. The tools do not error — they report
`{"installed": false}` and suggest an install command, which reads as *you
never set this up* rather than *your upgrade removed it*. So check on
purpose; do not wait to notice.

After any upgrade, restore with:

```bash
uv pip install --python "$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python" \
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]'
```

`cad` is **not** in that list on purpose: A46 P1b moved CadQuery to a
sidecar at `~/TEE/.tee/sidecars/cad`, which an upgrade does not touch.

To confirm it worked, ask TEE rather than trusting the install log — a
backend probe reports the libraries it can actually import:

```
med_backends  -> "numpy": {"installed": true, "version": "2.5.2"}
```

---

## The one-line version

| you want to | install | then call |
|---|---|---|
| solve an LP/MIP, schedule, allocate | `uv pip install 'tee-engine[solve]'` | `solve_program` |
| optimise a portfolio | `uv pip install 'tee-engine[quant]'` | `quant_optimize` |
| read a DICOM archive | run Orthanc (below) | `med_find_studies` |
| measure a medical volume | `uv pip install 'tee-engine[medimg]'` | `med_volume_stats` |
| build/measure CAD | `brew install --cask openscad` + `[cad]` | `cad_scad_build` |
| query a semantic layer | run Cube (below) | `bi_query` |
| backtest a rule | already works (pandas) | `trade_backtest` |

Every tool is found through `tee_search_tools` and called through
`tee_call`. If a library is missing you get one short error naming the
exact command — never an ImportError traceback.

---

## solve — HiGHS, SCIP, COIN-OR Cbc, OR-Tools

```bash
uv pip install 'tee-engine[solve]'
```

~255 MB. All permissive (HiGHS MIT, OR-Tools Apache-2.0, PySCIPOpt MIT
over a separately-licensed SCIP build, Cbc EPL-2.0).

- `solve_program` — LP or MILP; variable types decide which. Backends
  `highs` (default), `scip`, `cbc`.
- `solve_cpsat` — constraint programming, a different paradigm.
- `solve_detail` — the full solution vector, or the engine's own log.
- `solve_backends` — what is installed.

**Answers are compact by design.** A 400-variable model returns the
objective, the binding constraints and the twelve largest non-zero
variables plus a `solution_id`. The rest is `solve_detail`.

> **Why CP-SAT runs in a subprocess.** `ortools` and `highspy` each bundle
> their own build of HiGHS and the dynamic linker binds to whichever loaded
> first, so `import highspy` then `import ortools` raises ImportError.
> Import ORDER decided whether CP-SAT worked. It now runs in its own
> interpreter. Do not "simplify" that away.

## quant — PyPortfolioOpt, skfolio

```bash
uv pip install 'tee-engine[quant]'
```

~420 MB. PyPortfolioOpt MIT, skfolio BSD-3-Clause.

- `quant_optimize` — `max_sharpe`, `min_volatility`, `hrp`, `mean_risk`.
- `quant_detail` — the full weight vector.

**TEE computes the performance metrics itself**, on one annualisation and
one risk-free rate for every method, because the libraries' own numbers
are not comparable (HRPOpt defaults to rf=0 and an arithmetic mean;
EfficientFrontier reports against the geometric mu with rf=0.02). Every
payload states the basis and says plainly that it is not investment advice.

## med — Orthanc (a service) + MONAI

```bash
# the archive: a server YOU run. GPLv3, never bundled.
docker run -d --name orthanc -p 8042:8042 \
  -e ORTHANC_PASSWORD=change-me \
  -e DICOM_WEB_PLUGIN_ENABLED=true \
  orthancteam/orthanc:latest

# the volume maths (optional, only for med_volume_stats)
uv pip install 'tee-engine[medimg]'
```

- `med_archive`, `med_find_studies`, `med_study_tree`, `med_instance_tags`
- `med_volume_stats` — shape, intensity range, spacing, non-zero fraction

Orthanc needs **zero Python dependencies** — TEE speaks HTTP to it with
the standard library.

> **Patient identifiers are withheld by default.** Pass `phi=true` when the
> task genuinely needs them. Pixel data is never returned.

> `DICOM_WEB_PLUGIN_ENABLED=true` matters: without it the default image
> does not load DICOMweb at all. Orthanc 1.13+ also refuses to start unless
> a password or `ORTHANC__AUTHENTICATION_ENABLED=false` is given.

> MONAI on its own reads **neither DICOM nor NIfTI** — its base install
> registers only Numpy and PIL readers. The `[medimg]` extra adds `pydicom`
> and `nibabel`, which is what makes it useful.

## cad — OpenSCAD + CadQuery

```bash
brew install --cask openscad          # GPL-2.0-or-later, run as a program
uv pip install 'tee-engine[cad]'      # CadQuery, for STEP measurement
```

- `cad_scad_build` — build and export STL / 3MF / SVG / DXF / OFF / AMF / CSG
- `cad_measure` — volume, area, bbox, validity
- `cad_probe`

**Parameters go through OpenSCAD's customizer JSON, and `-D` is not
exposed.** `-D` prepends arbitrary *statements* to the script, so a
caller-supplied `-D` is code execution wearing the costume of a parameter.
Parameter names are validated and values must be scalars.

Binary STL is measured directly by TEE (signed-tetrahedron volume, exact
for a closed mesh) with no dependency at all — so `cad_measure` works on
STL even without CadQuery installed.

> CadQuery is ~1.3 GB and its **first** import takes ~140 s while Python
> compiles OCP's bytecode. Warm imports are ~1.1 s. Nothing loads until you
> call a `cad_*` tool.

## bi — Cube

```bash
docker run -d --name cube -p 4100:4000 \
  -v ~/TEE/.tee/cube:/cube/conf \
  -e CUBEJS_DEV_MODE=true -e CUBEJS_DB_TYPE=duckdb \
  cubejs/cube:latest
```

Then pass `url='http://127.0.0.1:4100'` (or set `[bi] url` in
`.tee/config.toml`).

- `bi_catalogue` — what can be asked
- `bi_query` — compact table: `cols` header + arrays-of-arrays
- `bi_detail`, `bi_probe`

Zero Python dependencies.

> **Two traps that cost real time here.** Docker Desktop does **not** share
> `/private/tmp` — keep the Cube config under your home directory or the
> model directory will silently appear empty. And Cube's default port 4000
> is already the **LiteLLM shim** on this machine (the qmax endpoint), so
> Cube must go elsewhere — 4100 above.

## trade — backtesting only

Works with no extra install (uses pandas).

- `trade_backtest` — declarative rules: `sma_cross`, `threshold`, `buy_hold`
- `trade_detail` — the equity curve, resampled
- `trade_probe` — what is and is not wired

**TEE places no orders, moves no funds, controls no live strategy, and does
not read a live broker account.** That last one is deliberate too: on
OpenAlgo the same API key that reads an account also reaches
`/api/v1/analyzer/toggle`, which flips paper mode to live. The credential
is the hazard, not the verb.

The guard is **absence**, not refusal — no such tool exists to be called,
argued with or retried. `place-order` is a reserved capability that no
config can grant and no tool requests.

Jesse (MIT) and NautilusTrader (LGPL-3.0-only) can back-test properly and
would each need their **own** interpreter — Jesse pins `mcp==1.28.1`
against TEE's `mcp>=2`, and NautilusTrader needs Python ≥3.12 while TEE
runs 3.11. `trade_probe` reports this rather than pretending.

---

## Not built

| resource | why |
|---|---|
| **Hummingbot** | exists to place orders continuously; no read-only shape worth wiring |
| **OpenAlgo** | one API key spans reads and the live toggle, so TEE holds none |
| **Jesse / NautilusTrader** | sidecars, not in TEE's interpreter (see above); reported by `trade_probe`, not wired |
| **Qiber3D** | 859 MB, PyPI release broken (needs a git SHA), and it transitively imports GPL `nd2reader`. Lowest value of the sixteen. |

---

## Checking what you have

```
tee_call solve_backends {}
tee_call med_backends {}
tee_call cad_probe {}
tee_call bi_probe {}
tee_call trade_probe {}
```

Each answers what is present, what is not, and the exact command to fix it.
