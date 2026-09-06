# Wind-tunnel setup — the `wt_*` lane (A68)

Four engines, four separate installs, all found by `wt_probe` and `tee doctor`.
TEE runs each as a separate process and downloads none of them: every refusal
names the install line below with its size and the date it was verified.

| engine | licence | what TEE runs | found at |
| --- | --- | --- | --- |
| OpenFOAM (openfoam.com) | GPL-3 | `blockMesh snappyHexMesh checkMesh simpleFoam decomposePar reconstructPar` through the install's own environment | `[windtunnel] openfoam`, then `/usr/lib/openfoam/openfoam*`, `/opt/openfoam*`, `~/OpenFOAM/OpenFOAM-*`, `/usr/share/openfoam`; the Mac app under `/Applications/OpenFOAM-v*.app` |
| SU2 | LGPL-2.1 | `SU2_CFD` | `[windtunnel] su2`, `$SU2_RUN`, `~/SU2/bin`, `/opt/SU2/bin`, PATH |
| OpenVSP / VSPAERO | NOSA-1.3 | `vspscript` (with `vspaero` beside it) | `[windtunnel] openvsp`, `/opt/OpenVSP`, `/usr/local/bin`, `/Applications/OpenVSP*`, PATH |
| ParaView | BSD-3 | `pvpython` | `[windtunnel] pvpython`, `/Applications/ParaView-*.app/Contents/bin`, `/opt/paraview*/bin`, `/usr/bin`, PATH |

## Install once per platform

### Linux (Ubuntu 24.04; measured 2026-09-06 in the build container)

```bash
# OpenFOAM: openfoam.com's own repository, NOT Ubuntu's `openfoam` package
curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
sudo apt-get install openfoam2606-default            # 340 MB under /usr/lib/openfoam/openfoam2606

# SU2 8.4.0: static binaries from the GitHub release (31 MB); set the bin dir
#   github.com/su2code/SU2/releases -> SU2-v8.4.0-linux64.zip (a nested linux64.zip inside)
#   then either export SU2_RUN=<bin dir> or set [windtunnel] su2 = "<bin dir>"

# OpenVSP 3.51.3 (64 MB): openvsp.org/download.php -> OpenVSP-3.51.3-Ubuntu-24.04_amd64.deb
sudo apt-get install ./OpenVSP-3.51.3-Ubuntu-24.04_amd64.deb   # its post-install exits 127; the binaries are fine

# ParaView + the offscreen shim the apt build needs
sudo apt-get install paraview python3-paraview xvfb
```

**Why not Ubuntu's `openfoam` package:** measured, apt's 1912 build dies at
"Starting time loop" with `FOAM FATAL IO ERROR: error in IOstream "sha1"` the
moment any function object is on — so it can mesh and solve but never report
a force. TEE searches `/usr/lib/openfoam/openfoam*` first and `/usr/share/openfoam`
last for that reason.

**Root containers:** Open MPI refuses to run as root. For a parallel run
(`cores > 1`) started by root, TEE sets `OMPI_ALLOW_RUN_AS_ROOT=1` and its
`_CONFIRM` twin for that process only, and the run record says
`mpi_root_override`. A workstation never sees this.

### macOS (Apple silicon) — an owner-session checklist, not measured numbers

```bash
brew install gerlero/openfoam/openfoam          # OpenFOAM-v2606.app; the entry script is
#   /Applications/OpenFOAM-v2606.app/Contents/Resources/etc/openfoam and TEE composes
#   `<entry> <app> args` for it; cases live on the normal filesystem
# SU2: github.com/su2code/SU2/releases -> the macOS zip; set [windtunnel] su2
# OpenVSP: openvsp.org/download.php -> the macOS-14 ARM64 bundle (pinned to Python 3.11 or 3.13);
#   set [windtunnel] openvsp = "<its folder>" (TEE uses vspscript, never its Python)
# ParaView 6.1.1: paraview.org/download -> the arm64 dmg;
#   set [windtunnel] pvpython = "/Applications/ParaView-6.1.1.app/Contents/bin/pvpython"
```

The Mac rows M1–M7 of `CLAUDE_A68_SCRIPT.md` §M are the measurements still
owed there (invocation form, goldens on v2606, SU2 arm64 vs Rosetta, ParaView
offscreen, the OpenVSP bundle paths).

## Serve

```bash
cd server && uv run tee serve --adapter blender      # the lane registers on every serve
```

`wt_*` are virtual tools: `tee_search_tools "wind tunnel"` reaches them and the
always-loaded surface stays at 17 tools.

## Configuration (`<project>/.tee/config.toml`)

```toml
[windtunnel]
openfoam = "/usr/lib/openfoam/openfoam2606"   # a project dir with etc/bashrc, the app's etc/openfoam, or a bin dir
su2 = "/opt/SU2/bin"                            # a dir or the SU2_CFD binary
openvsp = "/opt/OpenVSP"                        # a dir holding vspscript and vspaero
pvpython = "/usr/bin/pvpython"
cores = 4                                       # default for wt_run / wt_mesh
confirm_above_s = 300                           # the cost gate: above this wt_run asks once
max_wall_s = 14400                              # a solver is terminated past this
```

An explicit path that is not the engine refuses loudly (`wt_bad_config`); it
never falls through to whatever PATH holds.

## The machine ledger

Every solve and every snappyHexMesh is a job on the machine ledger (`cfd-solve`
4 GB floor, `cfd-mesh` 2 GB, `aero-panel` 0.5 GB). With the QoS law on (the
default) a machine under 16 GB + floor refuses every job engine at the door:
*"cfd-solve needs 4 GB and the machine can never place it"*. That is the
kernel's reserve for the resident model, not the lane's; declare the capacity
you actually have with `TEE_MACHINE_TOTAL_GB=32` (what the kernel's own tests
do) or set `[scheduler] qos = false`. A registered solve defers LLM engine
swaps until it releases — documented, never bypassed.

## Verifying

```bash
cd server
uv run tee doctor                                  # one `windtunnel` row: versions found, install lines for the rest
uv run pytest -q tests/test_windtunnel_*.py        # hermetic: fakes, ~150 tests, no engine needed
uv run pytest -q -m cfd tests/test_windtunnel_live.py -o addopts=""   # the real engines, ~4 min; skips by name
```

`wt_verify case=all confirm_cost=true` runs the two references verified at
source (lifting line, the SU2 QuickStart figure) and refuses the two that are
not yet.

## Tests

| tier | file | needs |
| --- | --- | --- |
| hermetic | `test_windtunnel_{physics,writers,readers,runner,tools,licences}.py` | nothing (the fakes in `fixtures_windtunnel.py`) |
| `cfd` | `test_windtunnel_live.py` | whichever engines are installed; `TEE_WT_TUTORIAL` for the adoption smoke |
