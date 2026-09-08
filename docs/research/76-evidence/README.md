# 76-evidence — what produced the numbers in research doc 76

Produced on the **owner's Mac** on 2026-09-07 (darwin, Apple Silicon, Python
3.11.15) against `jsbsim` 1.3.1 from PyPI in a throwaway venv — never the server
venv. Nothing here is an upstream file: `bridge.py` writes its own aircraft, its
own engine and its own thruster, and reads no bundled aircraft at all.

```bash
uv venv --python 3.11 jsb-venv && uv pip install --python jsb-venv/bin/python jsbsim
jsb-venv/bin/python bridge.py              # SI units on the wire
jsb-venv/bin/python bridge.py --imperial   # the same aircraft, converted by us
```

| file | what |
|---|---|
| `bridge.py` | writes a complete aircraft from a `wt_sweep`-shaped polar plus mass properties, loads it, reads its metrics and inertia back, attempts a trim, and runs `FGLinearization` twice in fresh interpreters — with and without an engine |
| `bridge-2026-09-07.log` | what it printed |

**The finding the file exists for:** `FGLinearization` on an aircraft whose
`<propulsion>` is empty **kills the process** — `rc=-11`, SIGSEGV, no exception,
nothing to catch. With one engine it returns a 12-state model. `fd_modes` must
therefore refuse an engineless aircraft *before* it calls the library, and the
lane runs the call out-of-process regardless.

**Three smaller ones.** SI units are accepted and converted correctly in
`metrics` (`Sw` 174.3753 ft² against 174.3753 expected, `cbar` 4.8885 ft against
4.8885) — the generator may write metres. `inertia/*-slugs_ft2` reads **0.0
until `run_ic()`**, on the bundled `c172p` as much as on ours, so a generator
that checks its own output must check it after the IC, not after the load. And
the linearised state vector is **propulsion-dependent** — 13 states with
`c172p`'s piston (`Rpm0` among them), 12 with an electric motor.

**What this does NOT show, deliberately.** The generated aircraft does not yet
trim: `do_trim(0)` returns *"qdot doesn't appear to be trimmable"* because the
pitch axis carries only `Cm_alpha` and a crude `Cm_de` with the aero reference
point on the CG. Closing that is A75 **P3's acceptance criterion**, and it is
left open here rather than papered over. Doc 74 §5 asked whether a generated
aircraft round-trips; this answers *loads and reads back exactly, trim still
open* — which is further than doc 75 got and less than the lane needs.
