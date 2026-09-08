# 75 — a flight-dynamics lane: what JSBSim actually is

**Grounding, not a design of record.** No campaign exists for this; no owner
decision has been taken. Written 2026-09-07 after the question *"does TEE
include a flight model"* returned **no** — and the follow-up *"check the JSBSim
licence and API"* returned facts worth keeping whether or not a lane is ever
built. Every number below was produced on the owner's Mac (darwin, Python
3.11.15) on that date by `75-evidence/probe.py` and `75-evidence/licence-probe.sh`;
nothing here is remembered, and the two logs beside those scripts are what they
printed.

## 1. What TEE has, and what it does not

The wind-tunnel lane (A72/A73, `wt_*`) is **steady aerodynamics**: an ISA
atmosphere, Reynolds/Mach/dynamic pressure, and CFD or vortex-lattice solves
returning Cl, Cd, Cm, L/D with a convergence verdict and an uncertainty label.
`wt_sweep` gives a polar over angle of attack.

That is the *aerodynamic data package* a flight model consumes. It is not a
flight model. Nothing anywhere in `server/src/` integrates equations of motion,
trims, models propulsion or mass properties, or produces stability derivatives —
and A72's own non-goals rule out the precursors (moving/dynamic meshes and
transient solvers are explicitly out of v1). Two things that look like hits are
not: `knowledge-base/29_aerospace_engineering/` and
`31_aviation_industry/06_flight-simulation-engineering.md` are the imported
reference library — prose written elsewhere, never verified here, grounding
nothing — and the "6-DOF" in `docs/DECISIONS.md:1165` is partkiln's **assembly
solver**, rigid-body placement in CAD, not aircraft motion.

So the gap is real and it is a specific shape: everything downstream of the
polar.

## 2. The measured facts

### 2.1 The licence is LGPL-2.0-**or-later** — with one GPL-3 file inside the wheel

The headline is LGPL, and the three sources that state it disagree in detail:

| source | says |
|---|---|
| `src/FGFDMExec.cpp` header — the operative grant for the library | *"either version 2 of the License, or (at your option) any later version"* (LGPL) |
| `src/JSBSim.cpp` — the C++ standalone binary | same: **LGPL**-2.0-or-later |
| repo `COPYING` — the text actually shipped | LGPL **2.1**, February 1999 |
| PyPI classifier | `License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)` |
| PyPI `license` / `license_expression` fields | both `None` |

`LICENSE` and `LICENSE.txt` are 404 in the repo; `COPYING` is the file. The
grant in the source headers governs and it is **2-or-later** — the shipped 2.1
text is a packaging choice, not the ceiling.

**And then there is the exception, which is the finding.** The wheel installs a
console script named `jsbsim` — `jsbsim/script.py`, upstream `python/JSBSim.py`
— and that one file is licensed

> *"the terms of the GNU **General** Public License … either **version 3** of the
> License, or (at your option) any later version"*

A single **GPL-3.0-or-later** file sits inside an otherwise-LGPL wheel. Three
consequences, none of them guessable from `COPYING`:

- **The obvious route and the safe-looking route swap places.** Importing the
  library is LGPL. Shelling out to the wheel's `jsbsim` command — the route that
  *looks* more conservative — is invoking a **GPL-3** program. (At arm's length
  that is the OpenFOAM situation TEE already lives with, §3.)
- **The C++ `JSBSim` binary is not the same program as the wheel's `jsbsim`
  command.** The former is LGPL, the latter GPL-3. They share a name and a
  purpose and not a licence.
- **A classifier-checking gate would pass this.** TEE's licence gates read
  installed distributions — the way `foamlib` was caught as GPL-3.0-only on
  PyPI. Here PyPI declares `LGPLv2+` while a GPL-3 file ships in the package. A
  gate for this lane has to assert on the **file header**, not the metadata:
  a declaration is a claim, a measurement is evidence.

The wheel additionally vendors two dependencies with their own licences beside
it: **GeographicLib** (MIT) and **libexpat** (MIT). Neither is copyleft.

### 2.2 The wheel is small, typed, and brings 60 aircraft with it

```
version 1.3.1 | footprint 8.8 MB | 60 aircraft + engine/ systems/ scripts/
requires_python >=3.10 | requires_dist ['numpy>=1.20']
```

`py.typed` and a full `__init__.pyi` ship in the wheel, so every signature is
statically checkable rather than guessed — which is how the two API defects in
§2.6 were found rather than argued about. The bundled aircraft (`737`, `A320`,
`B747`, `C130`, `Concorde`, `f16`, `c172p`, …) are LGPL data files inside the
distribution, and `aircraft/aircraft_template.xml` is the schema for writing
one's own. **TEE's standing law applies unchanged: no upstream case is ever
vendored.** Use the installed root; write our own aircraft.

**Platform gap.** The wheel matrix is macOS `universal2` (×6, so Apple Silicon
is native — that is what ran here), `manylinux2014_x86_64` (×8), `win_amd64`
(×8), plus an sdist. There is **no linux-aarch64 wheel**: on ARM Linux it builds
from source and needs a compiler and CMake.

### 2.3 The API is one class, and the loop is four calls

```python
fdm = jsbsim.FGFDMExec(None)        # None = the bundled data root
fdm.load_model("c172p")             # 0.003 s
fdm.set_property_value("ic/h-sl-ft", 5000); ...
fdm.run_ic()
fdm.do_trim(1)                      # 0.005 s; raises TrimFailureError
while ...: fdm.run()
```

28 top-level names, 65 methods on `FGFDMExec`. The state is a **property tree**:
656 properties for the C172, each carrying its access flag
(`simulation/gravity-model (RW)`, `inertial/sea-level-radius_ft (R)`), reached
through `get_property_value` / `set_property_value`. Subsystems come off the
exec (`get_propulsion`, `get_aerodynamics`, `get_mass_balance`, `get_propagate`,
`get_auxiliary`, `get_ground_reactions`).

`set_aircraft_path` and `load_model_with_paths` take **our** XML. That is the
bridge: `wt_sweep` produces the polar, a generated aircraft file consumes it.

`TrimFailureError` is a typed exception, so a failed trim is an exact cheap
refusal rather than a plausible wrong number — which is hard rule 6 for free.

### 2.4 It flies at ~1,376× real time

C172 at 5,000 ft / 120 KCAS, trimmed level, on the owner's Mac:

| | |
|---|---:|
| cold import (fresh interpreter) | 0.052 s |
| `load_model` | 0.003 s |
| `do_trim(1)` | 0.005 s |
| 7,200 steps (60 s of flight at dt 0.0083 s) | **0.044 s** |
| | **1,376× real time, 165,150 steps/s** |

Run-to-run the rate lands between about 1,300× and 1,400×. The trim **held**:
5001 ft, 120.0 KCAS, Nz 1.00 at t = 60 s. It is not merely running; it is
holding the condition it was trimmed to.

### 2.5 `FGLinearization` hands back the modes, and they are the right ones

```python
lin = jsbsim.FGLinearization(fdm)
A, B = lin.system_matrix, lin.input_matrix      # (13,13) and (13,4)
```

States are named and united: `Vt [ft/s], Alpha [rad], Theta [rad], Q [rad/s],
Rpm0 [rev/min], Beta, Phi, P, Psi, R, Latitude, Longitude, Alt [ft]`. Inputs:
`ThtlCmd, DaCmd, DeCmd, DrCmd`, all `norm`.

The eigenvalues of A, with modal participation factors (right × left
eigenvectors, so the labels are scale-invariant rather than a guess):

| eigenvalue | T (s) | ωn (rad/s) | ζ | participation | that is |
|---|---:|---:|---:|---|---|
| −4.9980 ± 6.5990j | 0.95 | 8.278 | 0.604 | Q 50 %, Alpha 50 % | **short period** |
| −0.5151 ± 2.8387j | 2.21 | 2.885 | 0.179 | Beta 48 %, R 47 % | **Dutch roll** |
| −0.0297 ± 0.2126j | 29.56 | 0.215 | 0.138 | Theta 50 %, Vt 49 % | **phugoid** |

The three classic oscillatory modes fall out unprompted, each named by its own
participation rather than by our expectation. And the slowest cross-checks
against closed form: **Lanchester's phugoid approximation at 120 kt gives 28.0 s
against the measured 29.56 s, +5.7 %**. That is the fact that turns "it runs"
into "it is right" — an independent analytical check the model never saw.

This is also the piece that matters most to TEE: stability derivatives and
handling-qualities numbers come out of A and B directly, so the expensive part
of a flight-dynamics answer is already a small matrix, not a time history.

### 2.6 It can be made quiet, and two calls are not what they look like

`FGFDMExec(None)` prints a **192-byte startup banner to stdout**, and
`set_debug_level(0)` does not stop it. Subclassing `jsbsim.FGLogger` and
installing it with `jsbsim.set_logger()` takes it to **0 bytes** (measured in
child processes, both directions). A lane can be silent.

Two API facts found by the probe failing, both recorded because a lane would hit
them on day one:

- `reset_to_initial_conditions()` **requires** its `mode` argument
  (`.pyi` line 1327: `(self, mode: int) -> None`). Calling it bare raises.
- `get_property_catalog()` returns a **list of names with access flags**, not a
  dict of values.
- `print_property_catalog()` writes at the **C++ level**:
  `contextlib.redirect_stdout` captures exactly 0 bytes of it. Only
  `set_logger` intercepts that stream.

### 2.7 The raw surface is 2,152× the useful answer

The reason a lane would exist, measured on the run above:

| | bytes | ~tokens |
|---|---:|---:|
| the property catalog, dumped | 19,176 | ~4,800 |
| 60 s of **six** states at 120 Hz (7,200 rows) | 439,200 | ~109,800 |
| the digest a lane would return | 213 | ~53 |

*(~tokens at 4 chars/token, an estimate, not a tokenizer run.)*

The digest is **1/2,152** of the raw surface — and the time history above is six
states, not 656 properties, and one minute, not a mission. This is the `wt_*`
shape exactly: the run is a job, the case stays on disk, the model gets the
verdict and the mode table.

## 3. The ruling this would need, which is the owner's

JSBSim is a **library**, not a binary to shell out to, and that is the one way it
differs from every engine the wind-tunnel gate governs.
`test_windtunnel_licences.py` keeps SU2 (LGPL-2.1) at arm's length as a separate
process and bans `pysu2` **by name** — but that ban is about a third-party
wrapper of a solver whose interface is a case directory. JSBSim's wheel is the
upstream project's own binding, and LGPL §6 is written for exactly the
dynamic-linking case an unmodified pip wheel presents.

That is an argument, not a ruling, and this document does not make it. Against
the shippable-MIT posture seamkiln and partkiln set, it deserves the same
explicit owner decision the other engines got, recorded in `DECISIONS.md`.

What §2.1 changes is that the fallback is **not** the free win it looks like:

- **In-process** (`import jsbsim`) is **LGPL**-2.0-or-later, unmodified,
  dynamically linked — and is the only route that gets `FGLinearization`, which
  §2.5 argues is the most valuable thing here.
- **Separate process via the wheel's `jsbsim` command** is **GPL-3**. TEE already
  drives a GPL-3 program at arm's length — OpenFOAM, every `wt_run` — so the
  precedent exists and is clean. But it is a *stronger* copyleft than the route
  it would be retreating from, which inverts the usual instinct.
- **Separate process via the C++ `JSBSim` binary** is **LGPL** again — and is
  neither of the two things a Python developer would reach for by default.

Whichever route, the licence gate gets a new row, a `script.py`-shaped assertion
that reads file headers rather than classifiers, and a never-vendor rule for the
60 bundled aircraft — the way every lane before it did.

## 4. What a lane would and would not be

**Would be** — headless, no DCC, no pixels; a trim/fly/linearise loop where the
run is a job and the reply is a digest; aircraft **generated** from `wt_*` polars
plus mass properties, never downloaded; the mode table and the A/B matrices as
the primary answer; `TrimFailureError` surfaced as a structured refusal.

**Would not be** — a simulator. No visuals, no scenery, no FlightGear, no motion
platform, no real-time loop, no autopilot design suite, no vendored aircraft, no
certification claim of any kind. The measured 1,376× real time exists to make
*batches* cheap, not to fly anything live.

The natural seam is that the two halves already speak: `wt_sweep` ends at a
polar, and a JSBSim `<aerodynamics>` section begins at one.

## 5. Open questions

1. **The licence route** — in-process (LGPL), the wheel's CLI (GPL-3), or the
   C++ binary (LGPL)? §3. Owner's. A gate that asserts on file headers rather
   than PyPI classifiers is a prerequisite either way.
2. ~~Does a generated aircraft round-trip?~~ **Answered by A75 P1**: yes.
   Doc 76 §2.5 has the measurement — and the reason it looked impossible from
   here, which is that JSBSim's `do_trim` blames `qdot` when the axis that
   cannot be trimmed is `udot`, because the turbine has not spooled when the
   trim looks at it.
3. **Mass properties.** partkiln knows mass and inertia of a part. Whether that
   composes into an aircraft's inertia tensor at a useful fidelity is untested.
4. **Where does the ARM-Linux sdist build land?** Untested; the Mac is native.
5. **What is the tool surface?** The current answer is 17 and every campaign has
   held it. A flight lane that adds five tools is a different proposition from
   one that adds `fd_case`/`fd_trim`/`fd_run` and hides the rest behind
   `tee_search_tools`.

## 6. Sources

All read or run 2026-09-07:

- <https://github.com/JSBSim-Team/jsbsim> — `src/FGFDMExec.cpp` and
  `src/JSBSim.cpp` headers (LGPL), `python/JSBSim.py` header (**GPL-3**),
  `COPYING`
- <https://pypi.org/pypi/jsbsim/json> — version, classifiers, wheel matrix
- <https://jsbsim-team.github.io/jsbsim/python/> — the documented Python API
- the installed wheel itself: `__init__.pyi`, `py.typed`, `LICENSE.txt`,
  `GeographicLib-LICENSE.txt`, `libexpat-LICENSE.txt`
- `75-evidence/probe.py` → `jsbsim-probe-2026-09-07.log`, `75-facts.json`
- `75-evidence/licence-probe.sh` → `jsbsim-licence-2026-09-07.log`
