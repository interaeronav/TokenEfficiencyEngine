# The flight-dynamics lane (`fd_*`)

Turns a polar and a mass into an aircraft that flies, trims it, and reports the
dynamic modes — while the model never sees a trajectory.

Design of record: `docs/research/76-flight-dynamics-lane.md`. Grounding:
`docs/research/75-flight-dynamics.md`. Plan of record: `CLAUDE_A75_SCRIPT.md`.
Install: `docs/setup-flightdyn.md`.

## What it is for

The wind-tunnel lane ends at a polar: Cl, Cd and Cm over angle of attack. That
is the *aerodynamic data package* a flight model consumes, and until now nothing
consumed it. A JSBSim `<aerodynamics>` axis is a one-dimensional table over
`aero/alpha-rad` — the same object in another notation — so this lane is the
translation, plus the mass properties partkiln already knows.

The useful answer is never the trajectory. Sixty seconds of six states at 120 Hz
is 439,200 bytes; the property catalogue is another 19,176; the digest below is
213. Everything stays on disk under an aircraft id, and the reply carries the
trim state, the verdict and the mode table.

## The loop

```
fd_probe → fd_aircraft (create) → fd_trim → fd_modes
                                         ↘ fd_fly
```

1. **`fd_probe`** — is JSBSim here, at what version, with how many bundled
   aircraft, and which licence route the lane uses. Never flies anything;
   absent, it answers with its install line.
2. **`fd_aircraft action=create`** — from `polar={alpha_deg,cl,cd}`,
   `mass={mass_kg,ixx,iyy,izz}` and `geometry={wing_area_m2,span_m,chord_m}`.
   **SI throughout**, and the unit is written on the wire; JSBSim converts.
   Thrust is sized from the polar — the drag at the design point times a margin
   — because an aeroplane that cannot out-thrust its own drag will not trim, and
   one with a hundred times too much will not trim either, and both look
   identical from the outside. `action=show` and `action=list` read back.
3. **`fd_trim`** — the lane's own Newton over angle of attack, elevator and
   throttle. A failure names the axis that would not converge and by how much.
4. **`fd_modes`** — A and B at the trim point, then every oscillatory mode with
   its period, damping and **modal participation**, so the modes name
   themselves rather than being labelled by expectation. Includes a closed-form
   cross-check with its basis stated.
5. **`fd_fly`** — trim, then fly it and report whether it stayed there:
   altitude drift, speed, load factor.

## What a reply looks like

```
fd_modes aircraft_id=demo
  trim    converged in 7   alpha 1.408 deg  elevator -0.035  throttle 0.610
  modes   T  2.03 s  zeta 0.699   Alpha 50%, Q 50%     <- short period
          T 31.53 s  zeta 0.028   Theta 49%, Vt 48%    <- phugoid
  check   Lanchester 22.59 s (+39.6%); zeta theory 0.0230 vs 0.0282; L/D 30.7
```

No array over 64 elements, no string over 2 KB, and the whole reply under 4 KB —
asserted by a test, not by intention.

**The cross-check is a witness, not a tolerance.** Lanchester's phugoid period
(`T = π√2·V/g`, on *true* airspeed) and the damping approximation
(`ζ ≈ 1/(√2·L/D)`) both neglect thrust. They are worth roughly a factor, not a
percent, and the lane says so rather than implying precision it has not earned.

## Two things it will not do

**It refuses an aircraft with no engine** before calling the library, because
`FGLinearization` on one does not raise — it SIGSEGVs, and takes the process
with it. Everything that flies therefore runs **out of process** as well; when
the child dies, the reply says the server survived because the call was not
in-process.

**It is not a simulator.** No visuals, no scenery, no FlightGear, no real-time
loop, no autopilot design suite, no vendored aircraft, and no certification
claim of any kind. The speed exists to make batches cheap.

## The engine it generates

A flat-rated `<turbine_engine>` behind a `<direct>` thruster — the combination
the bundled 737 uses. Flat means thrust is Mach- and altitude-independent, which
is honest for a lane whose subject is the polar rather than the powerplant. Its
`IdleThrust` and `MilThrust` tables are **not optional**: a turbine without them
segfaults at `run_ic()` rather than reporting a problem.

## Licence

JSBSim is **LGPL-2.0-or-later**, used as a library, in-process, unmodified and
dynamically linked — ruled in `docs/DECISIONS.md` (2026-09-07). The wheel also
ships one **GPL-3.0-or-later** file, `jsbsim/script.py`, installed as the
`jsbsim` console script; this lane never invokes it. PyPI declares `LGPLv2+` for
the whole distribution, so `server/tests/test_flightdyn_licences.py` asserts on
the grant in each installed file's own header instead. Nothing upstream is
vendored — the wheel ships 60 aircraft and the lane writes its own.
