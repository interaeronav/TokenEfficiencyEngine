# CLAUDE_A45_SCRIPT.md — unblock, meter the money, land the headless fleet

**Owner directive (2026-08-30):** (1) enable `exec-code` when it means the
job is done better; (2) build metrics for payments and cost from the paid
models; (3) fix the permission friction blocking product work; (4) add
fifteen headless open resources. Then, asked whether TEE is ever
distributed: *"its just for me, keep it simple."* Then: *"execute the
script once completed, i give my express permission to download the
required apps and software."*

This version supersedes the pre-research draft. Every size, licence,
version and entry point below was researched AND adversarially verified
against primary sources; 13 of 15 verifiers actually installed and ran the
thing on this machine. Where a claim did not survive, the correction is in
the table, not buried.

---

## Status

- **P0 — permissions stop blocking. DONE** (commit `A45 P0`). Grants
  reload on config change (no restart); `[trust] profile` presets;
  refusals name file + line + covering profile; fleet families pre-tabled.
  Taint law asserted unchanged. 901 tests.
- **P1 — the money meter. DONE** (commit `A45 P1`). `kernel/spend.py`:
  exact tokens/egress/endpoint, cost estimated ONLY from an owner-declared
  rate. Verified on a live paid call. SI-B16 + SI-B18 closed. 914 tests.
- **P2 — the fleet. THIS DOCUMENT.**

---

## The law for P2

1. **Nothing is claimed working that was not run.** Each resource lands
   with a smoke test that asserts a *known answer* (a solved objective, a
   volume, a study count), not "it imported".
2. **Zero always-loaded growth.** 17 tools / ~2,028 tokens is the ceiling.
   Everything here is a virtual tool behind `tee_search_tools`.
3. **Lazy imports, honest refusal.** Absent library ⇒ one `TeeError`
   naming the exact install command — the `web/media.py:153` pattern.
   Never an ImportError traceback.
4. **Compact by construction.** A solver returns status + objective + the
   few binding facts, never the full solution vector. Detail is a second,
   explicit call against a stable id.
5. **No live order execution. Ever.** Not a config flag, not an env var,
   not a "paper mode" that can be toggled. See "The trading line".
6. **Licence is no longer the architecture** (owner's decision, recorded
   in `docs/DECISIONS.md`), but copyleft resources stay optional extras,
   never vendored, never hard dependencies — which costs nothing and keeps
   the revisit cheap if TEE is ever shared.

---

## Verified resource table

Sizes measured on this machine by the verifiers, not estimated.

| # | resource | licence | seam | TEE-side size | notes |
|---|---|---|---|---|---|
| 1 | **HiGHS** (highspy 1.15.1) | MIT | in-process | 46 MB | cleanest of the three solvers |
| 2 | **OR-Tools** 9.15 | Apache-2.0 | in-process | 183 MB | ⚠ stdout pollution, see below |
| 3 | **SCIP** (PySCIPOpt 6.2.1) | MIT wrapper, bundled SCIP separate | in-process | 26 MB | licence of the bundle is NOT MIT |
| 4 | **Cbc** (PuLP 3.3.2) | EPL-2.0 solver | in-process | small | x86_64 binary under Rosetta on PuLP 3.x |
| 5 | **PyPortfolioOpt** 1.6.0 | MIT | in-process | 195 MB | needs explicit `packaging` |
| 6 | **skfolio** 1.0.2 | BSD-3-Clause | in-process | 223 MB | smoke test reproduced byte-identical |
| 7 | **MONAI Core** 1.6.0 | Apache-2.0 | in-process | 1.6 MB | torch already present; MPS works |
| 8 | **Orthanc** | GPL-3.0-or-later | HTTP client | **0 bytes** | Docker arm64 verified live |
| 9 | **Cube Core** 1.7.30 | Apache-2.0 AND MIT | HTTP client | **0 bytes** | Docker arm64 verified live |
| 10 | **OpenAlgo** | AGPL-3.0-only | HTTP client | **0 bytes** | ⚠ see the trading line |
| 11 | **Hummingbot** | Apache-2.0 (api MIT) | HTTP client | 20 MB | read-only only; engine not integrated |
| 12 | **OpenSCAD** | GPL-2.0-or-later + CGAL exception | subprocess | 73 MB app | ⚠ `-D` is code injection |
| 13 | **CadQuery** 2.8.0 | Apache-2.0 (+LGPL-3.0 dep) | subprocess venv | **1.3 GB** | heaviest single item |
| 14 | **Jesse** 3.0.7 | MIT | separate venv | 888 MB | ⚠ `mcp` pin conflicts with TEE |
| 15 | **Qiber3D** | MIT | separate venv | 859 MB | PyPI 0.7.x broken; pin a git SHA |
| 16 | **NautilusTrader** 2.0.0rc3 | LGPL-3.0-only | separate venv | 135 MB | ⚠ needs Python ≥3.12; TEE is 3.11 |

**Never installed into TEE's own venv:** Jesse (its `mcp==1.28.1` pin
would fight TEE's `mcp>=2`), NautilusTrader (3.12+), Qiber3D and CadQuery
(size). Those get their own venv and are driven as subprocesses returning
JSON on stdout.

---

## Three findings that change the code

**1. OR-Tools corrupts the MCP stream.** Its pywraplp HiGHS backend writes
92 bytes to **stdout** on every solve (`Running HiGHS 1.12.0 ... under MIT
licence terms`). TEE is a JSON-RPC-over-stdio server: that is protocol
corruption, not noise. Every fleet call that can reach native code runs
inside a stdout redirect to stderr/devnull. This is a general rule for the
whole fleet, not an OR-Tools special case, and it gets its own test.

**2. OpenSCAD `-D` is arbitrary code, not a parameter.** It prepends
commandline *statements* to the script. A caller-supplied `-D` is remote
code execution against the owner's machine. Parameters are therefore
passed **only** as a generated, validated JSON parameter file, values
type-checked and never interpolated into source. `-D` is not exposed.

**3. OpenAlgo: allow-list, never deny-list.** The verifier found the
dangerous-endpoint list wrong in both directions, and named the worst
omission: `POST /api/v1/analyzer/toggle` flips analyzer (simulated) mode —
i.e. it can turn a paper account live. `/api/v1/strategy/{start,stop,
close_all}` was also missed. So TEE ships a hard **allow-list of read-only
paths**; anything not on it is refused by construction, and a test asserts
the allow-list contains no verb that can create, amend, cancel or toggle.

---

## The trading line

Four resources touch money: NautilusTrader, Jesse, Hummingbot, OpenAlgo.

- **Built:** backtesting, research, and read-only inspection. Historical
  candles, portfolio maths, backtest metrics, account/position *reads*.
- **Not built, and structurally impossible:** placing, amending or
  cancelling an order; moving funds; starting or stopping a live strategy;
  toggling simulated/live mode.
- **How, not just whether.** The `place-order` capability exists in the
  kernel and **no tool requests it** (asserted by a test since P0). The
  OpenAlgo client carries a path allow-list. Hummingbot integrates only
  the read endpoints of its MIT API service, never the engine. Nothing
  reads an env var or config flag that could widen this.
- Live trading is a decision the owner takes in his broker's own
  interface. An autonomous tool that a model drives is the wrong place for
  it, and no amount of confirmation prompting changes that.

---

## Build order

Ordered by (value × certainty) ÷ risk. Each phase: build → smoke test with
a known answer → full suite → ruff → commit → PROGRESS entry.

**P2a — `solve` (HiGHS, SCIP, Cbc, OR-Tools).** Pure maths, permissive,
verified smoke tests, no service. Establishes the stdout-guard, the lazy
probe, and the compact answer shape the rest reuse. Tools: `solve_lp`,
`solve_mip`, `solve_status`, `solve_detail`, `solve_probe`.
*Compact shape:* status, objective, gap, wall, binding constraints, and
the top-N non-zero variables with a stable `solution_id` — never the full
vector; `solve_detail` pages it.

**P2b — `quant` (PyPortfolioOpt, skfolio).** In-process, no service.
Tools: `quant_optimize`, `quant_frontier`, `quant_metrics`,
`quant_detail`. *Compact shape:* weights above a threshold, rounded, plus
expected return / volatility / Sharpe — never a full covariance matrix.

**P2c — `med` (Orthanc + MONAI).** Orthanc is zero-dependency HTTP and
Docker-verified; MONAI is 1.6 MB on the torch already installed. Tools:
`med_studies`, `med_study_tree`, `med_series_meta`, `med_volume_stats`,
`med_transform`. *Compact shape:* counts and stable Orthanc IDs, never
pixel data; metadata by explicit tag list.

**P2d — `bi` (Cube).** Zero-dependency HTTP, Docker-verified. Tools:
`bi_catalogue`, `bi_members`, `bi_query`, `bi_explain`. *Compact shape:*
cube/measure/dimension names first; a query returns row count + first N
rows + a `result_id`.

**P2e — `cad` (OpenSCAD, CadQuery).** OpenSCAD via subprocess with the
JSON-parameter discipline; CadQuery in its own venv. Tools: `cad_build`,
`cad_measure`, `cad_export`, `cad_probe`. *Compact shape:* volume, area,
bbox, validity, output path — never geometry.

**P2f — `trade` (Jesse, NautilusTrader, Hummingbot, OpenAlgo).** Separate
venvs, subprocess JSON, allow-listed HTTP. Tools: `trade_backtest`,
`trade_backtest_detail`, `trade_account`, `trade_quote`, `trade_probe`.
*Compact shape:* headline metrics only (net profit %, max drawdown, Sharpe,
trade count) plus a `run_id`; the trade list is a paged detail call.

**P2g — `fiber` (Qiber3D).** Separate venv, git-SHA pinned. Lowest value
of the fifteen and the least certain; built last, dropped without
ceremony if the pinned SHA does not install.

---

## Acceptance

- Every group: a smoke test asserting a **known answer**, skipped cleanly
  with an actionable reason when the library or service is absent.
- `docs/setup-fleet.md`: one page, what each needs, the exact install line.
- Always-loaded surface **still 17 tools / ~2,028 tok** — measured before
  and after, in PROGRESS, and the campaign fails if it moved.
- A stdout-pollution test proving no fleet call can write to stdout.
- The trading-safety assertions above, as tests.
- `benchmarks/RESULTS.md` gains a fleet row only where a naive baseline
  can be honestly measured; where it cannot, the row says so rather than
  inventing one.

## Not built, and why

- **Hummingbot's engine.** It exists to place orders continuously. Only
  its read-only API service is integrated. Wiring the engine would mean
  building the thing this script forbids.
- **Any `place-order` path** for any of the four. Reserved capability, no
  requester, test-enforced.
- **OpenSCAD `-D`.** Code injection surface; JSON parameter files instead.
- **Cube Store** in production shape (no arm64 image); dev mode only,
  which is what a single-user machine needs anyway.
