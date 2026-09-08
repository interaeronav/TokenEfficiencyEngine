# Wind-tunnel setup — the `wt_*` lane (A72)

Four engines, four separate installs, all found by `wt_probe` and `tee doctor`.
TEE runs each as a separate process and downloads none of them: every refusal
names the install line below with its size and the date it was verified.

| engine | licence | what TEE runs | found at |
| --- | --- | --- | --- |
| OpenFOAM (openfoam.com) | GPL-3 | `blockMesh snappyHexMesh checkMesh simpleFoam decomposePar reconstructPar`, and cfMesh's `cartesianMesh surfaceFeatureEdges` where the install carries them, through the install's own environment | `[windtunnel] openfoam`, then `/usr/lib/openfoam/openfoam*`, `/opt/openfoam*`, `~/OpenFOAM/OpenFOAM-*`, `/usr/share/openfoam`; the Mac app under `/Applications/OpenFOAM-v*.app` |
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

**cfMesh needs no install of its own (A74).** `cartesianMesh` and
`surfaceFeatureEdges` ship *inside* openfoam.com's distribution (from v1806),
so the line above already installed them and `wt_mesh` defaults to
`mesher="auto"`, which uses cfMesh wherever it is present. `wt_probe` reports
the binary's path in the `openfoam` row (`cfmesh`), empty on a build that has
none — a Foundation install, or anything older. On such a machine `auto` meshes
with snappyHexMesh and says so in the mesh row; `mesher="cfmesh"` refuses by
name rather than quietly substituting. Nothing is downloaded either way.

**Root containers:** Open MPI refuses to run as root. For a parallel run
(`cores > 1`) started by root, TEE sets `OMPI_ALLOW_RUN_AS_ROOT=1` and its
`_CONFIRM` twin for that process only, and the run record says
`mpi_root_override`. A workstation never sees this.

### macOS (Apple silicon; measured 2026-09-06 on Darwin 26.6.2, 18 cores / 128 GB)

Every line below was run in that session; the evidence is
`docs/research/72-evidence/p0b-mac-2026-09-06.log` and the PROGRESS block
"A72 P0b". All four engines are found with **no `[windtunnel]` config at all** —
the default search paths cover each install location.

```bash
# OpenFOAM v2606 — a cask, ~1 GB, installs /Applications/OpenFOAM-v2606.app
brew install gerlero/openfoam/openfoam

# SU2 8.4.0 — github.com/su2code/SU2/releases -> SU2-v8.4.0-macos64.zip (21 MB).
#   It is a NESTED zip: unpack it, then unpack the macos64.zip inside it, so that
#   ~/SU2/bin/SU2_CFD exists (or export SU2_RUN=<its bin dir>).
#   chmod +x bin/* and clear the quarantine bit: xattr -dr com.apple.quarantine ~/SU2/bin

# OpenVSP 3.51.3 — openvsp.org/download.php -> the macOS-14 ARM64 bundle (61 MB);
#   place the unpacked folder as /Applications/OpenVSP-3.51.3 so /Applications/OpenVSP*/
#   matches, and clear its quarantine bit. TEE uses vspscript, never its Python.

# ParaView 6.1.1 — paraview.org/download -> ParaView-6.1.1-MPI-OSX11.0-Python3.12-arm64.dmg
#   (489 MB; the dmg carries a click-through licence). Copy ParaView-6.1.1.app into
#   /Applications and clear its quarantine bit.
```

**What the Mac does differently from Linux** (each measured, none inferred):

| | macOS v2606 | Linux (the container rows) |
| --- | --- | --- |
| OpenFOAM route | `entry`: `/Applications/OpenFOAM-v2606.app/Contents/Resources/etc/openfoam <app> args`; binaries live on a **read-only** APFS volume `/Volumes/OpenFOAM-v2606`, cases on the normal filesystem | `bashrc`: source `etc/bashrc`, then exec |
| architecture | OpenFOAM, OpenVSP and ParaView **native arm64**; **SU2 is x86_64 and runs under Rosetta 2** (no arm64 asset at 8.4.0) — it costs time, not answers (same iteration count, 40.5 s vs the container's 80 s) | x86_64 throughout |
| `cores > 1` | ships: the app's own `mpirun` (Open MPI 5.0.10) inside the entry environment; `decomposePar` writes real `processor*` dirs. **No root, so no `mpi_root_override`** | ships; Open MPI refuses root, hence the override |
| `k_openfoam` | **2.157e-06** s per cell-iteration-core | 2.36e-06 |
| pvpython offscreen | **works with no display and no xvfb** | the apt build segfaults; needs `xvfb-run` |
| tutorials | the app ships `airFoil2D` with `constant/polyMesh.orig` + `0.orig`, the mesh **gzipped**, and a `controlDict` that already has a `functions` block — adoption materialises and gunzips inside TEE's copy and merges `forceCoeffs` into the existing block | the apt copy ships the mesh and `0/` live, with no `functions` entry |

FreeCAD + CfdOF (optional, rows C1–C3): CfdOF **1.37.3** imports headlessly via
`FreeCAD.app/Contents/MacOS/FreeCAD -c`. Note that FreeCAD 1.1 keeps add-ons in a
**versioned** config dir (`~/Library/Application Support/FreeCAD/v1-1/Mod`) and its
macOS bundle ships **no `FreeCADCmd`** — the main binary with `-c` is the console route.

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

### Pinning a version when several are installed

**A config path is the pin.** Set `[windtunnel] pvpython = "/Applications/ParaView-6.1.1.app/Contents/bin/pvpython"`
(or the equivalent key for any engine) and that install is used, full stop —
`via: "config"` in `wt_probe` says so.

Without a pin, TEE ranks the matches of each known location and takes the
**newest stable** one, reporting the rest in `extra.alternatives` so an
ambiguous machine is visible rather than silent. If the only install found is a
pre-release, it is used and flagged `extra.prerelease: true`.

This ranking is a version comparison, not a string one, which matters more than
it sounds: the previous reverse-lexicographic rule ranked `ParaView-6.1.1` above
`ParaView-10.0.0` (because "6" sorts after "1", so a major-version bump would
have been silently ignored) and ranked `ParaView-6.2.0-RC1` above the stable
`6.1.1` beside it — measured on the owner's Mac, 2026-09-07, with both installed.
**A validation lane must not quietly certify against a release candidate.**

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

## The applications, not just their Python (A73)

`wt_open` hands a case to ParaView or OpenVSP, so it needs the APPLICATIONS -
the same installs the lines above already fetch, since `pvpython` ships inside
ParaView and `vsp` beside `vspscript`. Nothing extra to install.

It finds them beside the binaries the lane already resolves (`paraview` next to
`pvpython`, `vsp` next to `vspscript`), then on PATH; `[windtunnel] paraview =
<path>` overrides. Neither is ever version-probed: ParaView builds its Qt
application before parsing arguments, so on a machine with no display even
`paraview --help` aborts - asking it anything costs a crash.

The panel is separate and optional:

```bash
uv pip install --python server/.venv/bin/python 'tee-engine[gui]'   # PySide6, LGPL-3.0
server/.venv/bin/python -m tee.windtunnel.gui.app --project ~/TEE
```

See `docs/windtunnel-gui.md`. It adds no tool and no console script.
