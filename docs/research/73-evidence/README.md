# 73-evidence — what produced the numbers in research doc 73

Produced in the Linux build container on 2026-09-07 (Ubuntu 24.04 x86_64, no
display) against ParaView 5.11.2 and OpenVSP 3.51.3, both from this machine's
own installs. Nothing here is an upstream file: the scripts are TEE's own
probes and the numbers they printed are quoted in doc 73 §2.

| file | what |
|---|---|
| `pvsm_probe.py` | builds a real case through the registry, runs it, exports the `.foam` stub and saves a one-reader state over it; printed 177,402 bytes and "mentions the absolute case path: True / how many times: 1" |
| `pvsm_rich.py` | the realistic state - reader, `p` colouring, scalar bar, camera, last time step; printed 203,042 bytes |
| `pvsm_load.py` | loads that state in a FRESH pvpython and prints what came back: the reader and its file, view time 0.0, camera `[0.5, 0.0, 273.224]`, coloured by `['POINTS', 'p']` |

The two facts these were written to settle: a state file is a disk artefact
that never belongs in a tool reply, and it survives being written by one
process and read by another - which is the whole mechanism the handoff needs.
