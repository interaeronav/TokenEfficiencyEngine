# 75-evidence — what produced the numbers in research doc 75

Produced on the **owner's Mac** on 2026-09-07 (darwin, Apple Silicon, Python
3.11.15) against `jsbsim` 1.3.1 installed from PyPI into a throwaway venv —
never the server venv, which an upgrade would rebuild from the lock anyway.
Nothing here is an upstream file: the two scripts are TEE's own probes and the
numbers they printed are what doc 75 quotes.

Make the interpreter they need:

```bash
uv venv --python 3.11 jsb-venv && uv pip install --python jsb-venv/bin/python jsbsim
jsb-venv/bin/python probe.py          # writes 75-facts.json beside itself
./licence-probe.sh                    # needs network, no jsbsim
```

| file | what |
|---|---|
| `probe.py` | the whole measurement in six sections: the wheel (8.8 MB, 60 aircraft, cold import 0.052 s), the API surface (28 names, 65 methods), load/trim/fly (7,200 steps of 60 s flight in 0.044 s = 1,376× real time, trim held at 5001 ft / 120.0 KCAS / Nz 1.00), `FGLinearization` (A 13×13, the three modes by participation factor, phugoid 29.56 s vs Lanchester 28.0 s), the startup banner (192 bytes default → 0 with `set_logger`), and the raw-surface cost (1/2,152) |
| `licence-probe.sh` | where the licence is actually stated: the library header (LGPL-2-or-later), the C++ standalone (LGPL), **the wheel's `jsbsim` CLI (GPL-3)**, the shipped `COPYING` (LGPL 2.1 text), and PyPI's classifier + wheel matrix (no linux-aarch64) |
| `jsbsim-probe-2026-09-07.log` | what `probe.py` printed |
| `jsbsim-licence-2026-09-07.log` | what `licence-probe.sh` printed |
| `75-facts.json` | the machine-readable form, written by `probe.py` |

Three of these numbers exist because a probe was **wrong first** and the fix is
kept in the script: a `reload()` that measured 0.000 s and became a fresh-
interpreter subprocess; a mode label from a scale-dependent metric that called
the phugoid "Latitude" and became a proper participation factor; and a
`redirect_stdout` that captured 0 bytes of `print_property_catalog()` because
that call writes at the C++ level. The last one is a comment in `probe.py` now,
because a lane would hit it on day one.

The fact these were written to settle: **the licence question does not have one
answer.** The library is LGPL and the CLI shipped in the same wheel is GPL-3,
which no reading of `COPYING` reveals.
