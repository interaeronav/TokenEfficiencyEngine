# 73-evidence — what produced the numbers in research doc 73

Produced in the Linux build container on 2026-09-07 (Ubuntu 24.04 x86_64, no
display) against ParaView 5.11.2 and OpenVSP 3.51.3, both from this machine's
own installs. Nothing here is an upstream file: the scripts are TEE's own
probes and the numbers they printed are quoted in doc 73 §2.

| file | what |
|---|---|
| `pvsm_probe.py` | builds a real case through the registry, runs it, exports the `.foam` stub and saves a one-reader state over it; printed 177,402 bytes and "mentions the absolute case path: True / how many times: 1" |
| `pvsm_rich.py` | the realistic state - reader, `p` colouring, scalar bar, camera, last time step; printed 203,042 bytes |
| `pvsm_load.py` | loads that state in a FRESH pvpython and prints what came back: the reader and its file, view time 0.0, camera `[0.5, 0.0, 273.224]`, coloured by `['POINTS', 'p']` — and that `view time: 0.0` is the defect P2 found, recorded here as a success |
| `mac-check.sh` | the OWNER-SESSION script for the rows a Linux container cannot answer: which ParaView the lane resolves, whether writing a state leaves the signed `.app` sealed (`.pyc` count + `codesign`, the fault of base commit `c082dae`), the state round trip on ParaView 6.1, and whether `open -a ParaView --args --state=` passes the flag through. Prints, never asserts; writes `mac-a73-<date>.log` beside itself |

The two facts these were written to settle: a state file is a disk artefact
that never belongs in a tool reply, and it survives being written by one
process and read by another - which is the whole mechanism the handoff needs.

`mac-check.sh` is the only file here not produced in the container: it is the
script the owner's session runs, and its log lands beside it when it does.
