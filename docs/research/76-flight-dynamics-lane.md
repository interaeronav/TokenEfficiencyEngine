# 76 — the flight-dynamics lane: `fd_*` on JSBSim

Design of record for **A75** (`CLAUDE_A75_SCRIPT.md` is the plan). Written
2026-09-07. Doc **75** is the grounding pass this builds on — its licence and API
findings are not repeated here, only used. Every number below was measured on the
owner's Mac on that date by `75-evidence/probe.py` or `76-evidence/bridge.py`;
nothing here is remembered.

## 1. What is being built, and why here

TEE has aerodynamics and no flight dynamics. `wt_sweep` returns a polar — Cl, Cd,
Cm over angle of attack, with a convergence verdict and an uncertainty label —
and nothing consumes it. partkiln knows a part's mass and inertia, and nothing
consumes that either. A flight model is the thing that consumes both.

The seam is not a metaphor. A JSBSim `<aerodynamics>` axis is, verbatim:

```xml
<axis name="LIFT">
  <function name="aero/coefficient/CLwbh">
    <product>
      <property>aero/qbar-psf</property>
      <property>metrics/Sw-sqft</property>
      <table>
        <independentVar lookup="row">aero/alpha-rad</independentVar>
        <tableData> ... </tableData>
```

A one-dimensional table over `aero/alpha-rad`. That **is** a polar. The lane's
central claim is that `wt_sweep`'s output and JSBSim's input are the same object
in two notations, and the generator is the translation.

## 2. The measured facts this design rests on

### 2.1 A generated aircraft loads, and its numbers come back exactly

`76-evidence/bridge.py` writes all six sections JSBSim's schema wants —
`fileheader, metrics, mass_balance, ground_reactions, propulsion, flight_control,
aerodynamics` — plus its own engine and thruster, referencing no bundled file.

```
load_model     True
  Sw     174.3753 ft2   expected   174.3753
  cbar     4.8885 ft    expected     4.8885
  wt    1873.9292 lb    expected  1873.9292
  iyy   1342.2423 slug-ft2  expected  1342.3630  [after run_ic]
```

**SI units are accepted on the wire.** `unit="M2"`, `unit="M"`, `unit="KG*M2"`,
`unit="KG"` are read and converted correctly, so the generator writes metres and
kilogrammes — the units `wt_*` and partkiln already speak — and never performs a
conversion of its own. The Fusion lane's law transfers unchanged: **the unit is
always written**.

### 2.2 `FGLinearization` on an engineless aircraft kills the process

The finding that shapes the lane:

```
FGLinearization vs propulsion (each in a FRESH interpreter):
  <propulsion> with one engine  -> SURVIVED 12
  <propulsion> with NO engine   -> DIED rc=-11 (SIGSEGV)
```

Not an exception. Not a `TrimFailureError`. The interpreter is gone, and a
server that called it in-process goes with it. The same call on the bundled
`c172p` — untrimmed, engine not even started — returns normally, so this is
about the *aircraft*, not about the state.

Two consequences, and both are structural rather than defensive:

- **`fd_modes` validates before it calls.** An aircraft with no engine is
  refused by name, cheaply, in TEE's own code.
- **`fd_run` and `fd_modes` execute out-of-process anyway**, as jobs. A library
  that can SIGSEGV on a legal-looking input does not get to share an address
  space with the MCP server. This is the same posture the wind-tunnel lane takes
  toward its solvers, arrived at for a different reason.

### 2.3 The state vector is propulsion-dependent

`c172p` linearises to **13** states — `Vt, Alpha, Theta, Q, Rpm0, Beta, Phi, P,
Psi, R, Latitude, Longitude, Alt` — where `Rpm0` is the piston's. The generated
aircraft, on an electric motor, linearises to **12**: no `Rpm0`. So the mode
table's shape is not a constant, and `fd_modes` reads `x_names` rather than
assuming a layout.

### 2.4 Inertia is zero until the initial condition runs

`inertia/ixx|iyy|izz-slugs_ft2` all read **0.0** after `load_model` and carry
their real values only after `run_ic()` — measured on the bundled `c172p`
(0.0 → 1384.26) as much as on the generated aircraft. It is JSBSim's lifecycle,
not a defect and not a units problem, and it cost this session two wrong
diagnoses before it was measured. A generator that verifies its own output must
verify it after the IC.

### 2.5 The premise, proven during P1

Doc 75 could not trim a generated aircraft and said so. It is trimmed now, and
what stood in the way was never the pitch axis JSBSim blamed.

**`do_trim` reports the wrong axis.** `Sorry, qdot doesn't appear to be
trimmable` is what it says; bracketing each axis by hand shows `qdot` swinging
cleanly through zero (elevator -1/0/+1 gives +6.69 / -0.02 / -6.73 rad/s^2) and
`wdot` likewise, while **`udot` never brackets zero at all** - 1.72, 1.64, 1.68
ft/s^2 across the whole throttle range. The un-trimmable axis was the one it did
not name.

**Because a turbine has not spooled when the trim looks at it.**
`propulsion/set-running` leaves N1/N2 near 100 %, and a `<turbine_engine>`
follows its spool state rather than its throttle for about a second of sim
time: at the first frame it made 193.6 lb of a 200 lb rating whatever the
throttle said. Once spooled it is exactly right - 4.00 / 53.00 / 200.00 lb at
throttle 0 / 0.5 / 1.0. Spooling before `do_trim` does not help, because the
trim resets what it evaluates.

**And a turbine without `IdleThrust` and `MilThrust` function tables segfaults
at `run_ic()`** rather than reporting a problem - the third SIGSEGV this lane
has measured, and the reason `aircraft.py` writes flat-rated tables. (An
`<electric_engine>` behind a `<direct>` thruster does load, and made **88,507
lbf** on an 1,874 lb aeroplane; `<direct>` is right for a turbine, which is what
the bundled 737 uses.)

So the lane trims the aircraft itself: a 3x3 Newton over angle of attack,
elevator and throttle, with JSBSim as the force calculator. It rests on one more
measured fact - **`run_ic()` does NOT reset the spool** - so the engine is
spooled once and the initial condition re-set freely per iteration.

The result, on a generated aircraft at 5,000 ft and 90 KCAS:

```
trim      converged in 7 iterations   alpha 1.408 deg  elevator -0.035  throttle 0.610
modes     T  2.03 s  zeta 0.699   Alpha 50%, Q 50%      <- short period
          T 31.53 s  zeta 0.028   Theta 49%, Vt 48%     <- phugoid
check     Lanchester 22.59 s (+39.6%) - zeta 0.0230 theory vs 0.0282 (+23%) - L/D 30.7
hold 60s  altitude drift 1.5 ft   KCAS 89.88   Nz 0.9965
```

The two classic longitudinal modes fall out and name themselves by
participation; the lateral pair comes back degenerate, which is correct - a
polar carries no `Cl_beta` or `Cn_beta`, and the lane drops it rather than
reporting a mode it has no data for. Both closed-form checks are approximations
that neglect thrust, so `fd_modes` reports the comparison **with its basis
stated** and the tests assert a band those approximations are worth, not a
tolerance they cannot support.

Two traps found while proving it, both now guarded in code: `FGLinearization`
**perturbs the model and leaves it perturbed** (read L/D afterwards and it comes
back 125 instead of 30.7), and it **leaves `dt` at 0**, so a later `run()` loop
divides by zero.

## 3. The tool surface

Prefix **`fd_`**, verified unused. **Zero always-loaded tools** — the surface
stays at 17 `tee_*`, asserted in nine places. Every `fd_*` is a `VirtualTool`
reached through `tee_search_tools` / `tee_describe_tool` / `tee_call`, and each
is tabled **individually** in `kernel/trust.py::_EXPLICIT` under a
`# DELIBERATELY NO ("fd_", ...) FAMILY ROW` comment — the `cad_`/`trade_`/`pc_`/
`wt_` lesson, and it applies with force here because half these tools write.

| tool | what it does | trust row | job |
|---|---|---|---|
| `fd_probe` | is JSBSim importable, by which route, what version; caches `probe.json` | `read-compute` | no |
| `fd_aircraft` | **the generator** — `<aerodynamics>` from a `wt_sweep` polar, `<mass_balance>` from partkiln or given, `<metrics>` from the case's reference values; or `adopt` a path | `write-artifacts` | no |
| `fd_trim` | trim at a condition; a `TrimFailureError` becomes a named refusal carrying the axis JSBSim blamed | `write-artifacts` | no |
| `fd_run` | integrate, out-of-process, as a `tee_job` with an `on_cancel` hook | `call-engine` | **yes** |
| `fd_modes` | the linearisation: A/B, eigenvalues, ζ, T, participation factors. Refuses an engineless aircraft first | `call-engine` | **yes** |
| `fd_result` | the digest of a run: verdict, trim state, mode table, uncertainty label | `read-compute` | no |
| `fd_series` | ≤64 bounded samples of a time history | `read-compute` | no |
| `fd_export` | the aircraft XML or a CSV to disk | `write-artifacts` | no |

Lane in `kernel/lanes.py`: **`None`**. Nothing here touches a scene, so the
`LEGEND`'s existing *"and the rest are headless"* covers it and the 2 KB
instructions cap argues against spending bytes to name it.

## 4. The digest, and the token argument

Doc 74 §2.7 measured the raw surface: the property catalog is **19,176 bytes**
and sixty seconds of *six* states at 120 Hz is **439,200** — against a **213-byte**
digest, a ratio of **1/2,152**. And that is one minute of six states, not a
mission of 656 properties.

So the reply is always the same shape, and never the history:

```
fd_result run=fd_9c1e40
  trimmed  5000 ft / 120 KCAS   alpha -0.81 deg  elevator 0.000  throttle 0.84
  verdict  held        60.0 s   alt 5001 ft  KCAS 120.0  Nz 1.00
  modes    short period T 0.95 s  zeta 0.60   (Q 50%, Alpha 50%)
           dutch roll   T 2.21 s  zeta 0.18   (Beta 48%, R 47%)
           phugoid      T 29.6 s  zeta 0.14   (Theta 50%, Vt 49%)
  label    comparative — generated aircraft, polar from wt_sweep wt_3f2a
```

Every number carries its engine, its aircraft's provenance and an uncertainty
label, exactly as `wt_result` does. No array over 64 elements, no string over
2 KB. A time history exists only on disk and is reached by `fd_series`, bounded.

The mode table is the reason the lane is cheap: **the expensive part of a
flight-dynamics answer is a small matrix, not a trajectory.** A/B at a trim point
is where stability derivatives, handling qualities and control design all start,
and it is a few hundred tokens.

## 5. The licence gate

Doc 74 §2.1's finding is load-bearing and unusual enough to state as a rule:
**the gate asserts on file headers, not on metadata.** PyPI declares
`LGPLv2+`; the wheel ships `jsbsim/script.py` under **GPL-3.0-or-later**. A gate
of the shape TEE already has — `foamlib is GPL-3.0-only on PyPI today` — passes
this package while a GPL-3 file sits inside it.

`server/tests/test_flightdyn_licences.py` therefore carries the seven
`test_windtunnel_licences.py` assertions plus an eighth: for every JSBSim file
the lane could execute or import, read its first 40 lines and assert which
licence it grants, so a wheel that moves a file between the two licences fails
the suite rather than shipping. The banned-vendoring rule covers the **60 bundled
aircraft**: the lane uses the installed root or generates its own, and
`tests/data/flightdyn/` goldens carry `generated-by`.

The route itself — in-process (LGPL, and the only one that gets
`FGLinearization`), the wheel's CLI (GPL-3), or the C++ binary (LGPL) — is the
owner's ruling, taken in P0 and recorded in `DECISIONS.md` with the two refusals
stated. This document assumes in-process and does not decide it.

## 6. Non-goals

No simulator. No visuals, no scenery, no FlightGear, no motion platform, no
real-time loop, no autopilot design suite, no certification claim of any kind,
no vendored aircraft, and no download by the lane — ever. The measured 1,376×
real time exists to make *batches* cheap, not to fly anything live. TEE builds no
viewer (A67), and a flight model is not an exception.

## 7. Open questions

1. **The licence route** (§5). The owner's, in P0.
2. ~~Does a generated aircraft trim?~~ **Answered in P1** (§2.5): yes, in seven
   Newton iterations, with both longitudinal modes physical and the trim
   holding for a minute. JSBSim's own `do_trim` cannot do it and names the
   wrong axis; the lane trims itself.
3. **Do partkiln's inertias compose into an aircraft's tensor** at a useful
   fidelity? Untested; `pk_*` knows a part, not an assembly's flight mass.
4. **Where does the ARM-Linux sdist build land?** No linux-aarch64 wheel exists
   (doc 75 §2.2); the Mac is native and the build container is not.
5. **How many tools?** Eight are sketched in §3. `fd_series` and `fd_export`
   are the two most likely to be cut.

## 8. Sources

- research doc **75** and `75-evidence/` — licence, API, timings, the 2,152× row
- `76-evidence/bridge.py` → `bridge-2026-09-07.log` — everything in §2
- the installed wheel: `__init__.pyi`, `aircraft/c172p/c172p.xml`,
  `aircraft/aircraft_template.xml`
- <https://jsbsim-team.github.io/jsbsim/python/> — the documented Python API
