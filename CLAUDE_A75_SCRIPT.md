# CLAUDE_A75_SCRIPT.md — the flight-dynamics lane: `fd_*` on JSBSim

**Owner directive (2026-09-07):** *"does TEE include a flight model"* → it does
not; then *"check the JSBSim licence and API"* → research doc **75**; then
*"research a lane for an open source model"* with *doc + campaign script*,
**flight first**. This is that campaign.

Campaign **A75**; research doc **76** the design of record, doc **75** the
grounding it rests on; server **0.26.0 → 0.27.0**; pytest marker **`fdm`**.
Check both series are still free before the first commit — A72 was built as A68
and renumbered before merge, and this branch already carries an untracked doc 75.
Phases are independently shippable: stopping at a boundary must leave the tree
green and the feature honest about what it does not do.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, branch
  **`claude/wind-tunnel-aerodynamic-integration-hcsa7u`**. Read `docs/PROGRESS.md`
  first (the A73 block is at the tail); paste real command output into it per
  phase; commit per item; **stage only this campaign's own paths, never
  `git add -A`** — another session edits this repo in parallel.
- Suites: `cd server && uv run --no-sync pytest -q` (hermetic) · `-m fdm` (the
  real-JSBSim tier) · `make lint`. **Never `uv sync` in `server/`** — it drops
  the pip-installed extras.
- **Surface invariant: 17 always-loaded tools.** A75 adds **ZERO**. Every `fd_*`
  is a `VirtualTool` reached through `tee_search_tools` / `tee_describe_tool` /
  `tee_call`. `server/src/tee/server.py` and `kernel/lanes.py` stay untouched —
  that is what the invariant means for a headless lane.
- The lane lives at `server/src/tee/flightdyn/`. Registration is
  **unconditional**: a tool that vanishes when its engine is missing is
  indistinguishable from one that never existed.

## Measured facts (2026-09-07, the owner's Mac — build ON them)

1. **`FGLinearization` on an aircraft with an empty `<propulsion>` kills the
   process.** `rc=-11`, SIGSEGV, no exception, nothing to catch; one engine and
   the same call returns a 12-state model. The bundled `c172p`, untrimmed and
   with its engine off, survives — so this is about the aircraft, not the state.
   `76-evidence/bridge.py`.
2. **A TEE-generated aircraft loads and reads back exactly**: `Sw` 174.3753 ft²
   against 174.3753 expected, `cbar` 4.8885 ft, `emptywt` 1873.9292 lb, `iyy`
   1342.2423 slug-ft² against 1342.3630.
3. **SI units are accepted on the wire** — `M2`, `M`, `KG*M2`, `KG` are read and
   converted. The generator writes metres and kilogrammes, the units `wt_*` and
   partkiln already speak, and never converts. The unit is always written.
4. **`inertia/*-slugs_ft2` is 0.0 until `run_ic()`** — on the bundled `c172p`
   (0.0 → 1384.26) as much as on ours. JSBSim's lifecycle, not a defect; it cost
   two wrong diagnoses before it was measured.
5. **The linearised state vector is propulsion-dependent** — 13 states with
   `c172p`'s piston (`Rpm0` among them), 12 with an electric motor. Read
   `x_names`; never assume a layout.
6. **The generated aircraft does NOT yet trim**: *"qdot doesn't appear to be
   trimmable"*. The pitch axis carries only `Cm_alpha` and a crude `Cm_de` with
   the aero reference point on the CG. **This is P3's acceptance criterion** and
   the premise of the whole lane — if it cannot be closed, say so and stop.
7. **The licence is not what the metadata says.** The library is
   LGPL-2.0-or-later; the wheel's `jsbsim` console script (`jsbsim/script.py`,
   upstream `python/JSBSim.py`) is **GPL-3.0-or-later**. PyPI declares
   `LGPLv2+`. Doc 74 §2.1.
8. **The raw surface is 2,152× the digest** — catalog 19,176 B plus 60 s of six
   states at 120 Hz 439,200 B, against a 213 B digest. Doc 74 §2.7.
9. **No linux-aarch64 wheel exists.** macOS universal2, manylinux x86_64,
   win_amd64, sdist. The Mac is native; an ARM Linux box builds from source.
10. `do_trim` modes, from the wheel's own stub: `0` tLongitudinal, `1` tFull,
    `2` tGround, `3` tPullup, `4` tCustom, `5` tTurn, `6` tNone.

## Prior art in this repo (copy these, do not reinvent)

- **`windtunnel/tools.py:64-692`** — `register_windtunnel_tools(app, project_root)`,
  a `specs` list, one `reg.register(VirtualTool(...))` loop.
  `pointcloud/tools.py:825` is the same loop byte-for-byte. Attach with
  `_attach_flightdyn` beside `cli.py:204`.
- **`kernel/jobs.py:112`** `submit(..., qos=, engine=, on_cancel=)`, the hook
  fired outside the lock at `:280`; the lane-side pattern at
  `windtunnel/tools.py:1368` with `machine.register_job` / `release_job`, and
  `windtunnel/runner.py:116` — `start_new_session=True` is the load-bearing bit
  that makes `killpg` reach children.
- **`tests/test_windtunnel_licences.py`** — seven assertions, ~190 lines. Copy
  and change `LANE`/`DATA`/`EVIDENCE`, `BANNED`, `EXTRA_ONLY`,
  `ALLOWED_EXTRA_SITES`, `UPSTREAM_BANNERS`, the marker, and the docstring
  keywords. **Add the eighth** (P1).
- **`kernel/registry.py:277`** `require(capability, name=…)` — the escalation
  `wt_open` uses, if any `fd_*` grows a stronger optional mode.
- **`wt_probe`'s missing-engine reply** is the refusal shape: name the install
  line, do not stack-trace.
- **`windtunnel/verdict.py`** — the verdict vocabulary and the absolute floor it
  learned (Cm ≈ 5e-4 makes a relative stationarity test meaningless). A held
  trim needs the same treatment.

## Phases

- **P0** — the ruling and the paperwork. `docs/DECISIONS.md` entry taking doc 75
  §3's three licence routes and recording the owner's choice **with both
  refusals stated**; doc 76 finalised; this script; doc 75 + `75-evidence/` and
  doc 76 + `76-evidence/` committed; `00-index.md` rows for **74 and 75**.
  *Acceptance:* every fact carries the command that produced it; the ruling names
  the chosen route and why the other two were refused.

- **P1** — the deterministic half, hermetic. `server/src/tee/flightdyn/`:
  `__init__.py` whose docstring states the arm's-length rule (the gate asserts
  its keywords), `aircraft.py` (the generator), `probe.py`, `fd_probe`,
  `fd_aircraft`, `_attach_flightdyn`, the trust rows with the
  `# DELIBERATELY NO ("fd_", ...) FAMILY ROW` comment, and
  `test_flightdyn_licences.py`.
  *Acceptance:* the whole surface exercised with **JSBSim absent**; a missing
  engine returns its install line; `len(_DESC) == 17` and no `fd_` leaked onto
  the surface; an untabled `fd_*` is a **startup** error; the eighth licence
  assertion reads real file headers and fails if `script.py`'s grant moves.

- **P2** — the engine, out of process. `fd_trim`, `fd_run` and `fd_modes` as
  jobs with a working `on_cancel`, `fd_result`, `fd_series`; an `ENGINES` row for
  the job class; **`fd_modes` refuses an engineless aircraft by name before it
  calls the library** (fact 1).
  *Acceptance:* a real run cancelled inside two seconds; a hermetic test proves
  the engineless refusal happens in TEE's code, and a `-m fdm` test proves the
  unguarded call really does SIGSEGV — the guard is only worth what the crash
  costs; no array over 64 elements, no string over 2 KB.

- **P3** — **the premise.** `fd_aircraft` generating from a real `wt_sweep`
  polar, and the pitch axis completed until the thing trims (fact 6): an aero
  reference point off the CG, `Cm_q`, and a `Cm_de` with real control power.
  *Acceptance:* a **generated** aircraft trims, and its phugoid lands within a
  stated band of the Lanchester approximation — doc 75's cross-check applied to
  our own XML. If it will not trim, P3 fails loudly, the lane ships as
  adopt-only, and doc 76 §2.5 becomes the record of why.

- **P4** — the close. `docs/flightdyn-lane.md`, `docs/setup-flightdyn.md`,
  a `benchmarks/RESULTS.md` section on the A72 template (naive: catalog + history
  ≈ 114,600 tokens; TEE: digests), the `CLAUDE.md` bullet after A73's, CHANGELOG
  0.26.0, PROGRESS block with numbered gaps and the `**Suites at close:**` line,
  `test_search_budget.py` cases and the **re-measured** recall table, version ×3
  (`server/pyproject.toml`, `server/Makefile`, `packaging/mcpb_manifest.json`;
  `tools[]` untouched), `make mcpb` + clean-unzip verify (handshake 0.26.0;
  17 tools; `search 'flight dynamics' reaches fd_*`; `fd_probe` answers;
  `fd_run` from the bundle refuses by naming its install).

## Laws

1. **The model never sees a time history.** The answer is the trim state, the
   verdict and the mode table; the history is on disk behind `fd_series`.
2. **A declaration is a claim and a measurement is evidence** — the licence gate
   reads **file headers**, never PyPI classifiers.
3. **Nothing upstream is vendored**, the 60 bundled aircraft included.
4. **A library that can SIGSEGV does not share the server's address space.**
   Validate first, and run it out-of-process anyway.
5. **Trim failure is a refusal, not a number**, and it names the axis JSBSim
   blamed.
6. **SI on the wire, and the unit is always written.**
7. **Read `x_names`; never assume the state layout.**
8. Zero always-loaded tools; every `fd_*` tabled individually; no family row.
9. **Headless, no pixels, no viewer, no simulator.**

## Non-goals

A simulator · visuals, scenery, FlightGear, a motion platform · a real-time loop
· an autopilot design suite · vendored aircraft · any download by the lane · any
certification claim · a GUI (A67 stands: TEE builds no viewer).

## Amendments learned while building

*(Append here as the build teaches; the script is amended, not improvised
around.)*
