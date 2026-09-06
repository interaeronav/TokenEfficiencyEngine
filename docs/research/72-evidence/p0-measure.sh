#!/usr/bin/env bash
# generated-by: tee.windtunnel - the A72 P0b Mac measurement script (owner session).
#
# Prints, never asserts. Each section is one row of CLAUDE_A72_SCRIPT.md §M
# (M1-M7, C1-C3, S1, plus M8: the app's own airFoil2D tutorial adopted, the
# Linux L13 repeated on v2606). Paste the output verbatim into
# docs/PROGRESS.md under "### A72 P0b - the Mac rows"; only then do the macOS
# lines of docs/setup-windtunnel.md become measured facts. Nothing here
# downloads, installs or edits the tree. A Mac number is never typed in by
# hand: if a probe finds nothing it says so and the row stays open.
#
# Usage, from the repo root on the campaign branch, on the Mac:
#   bash docs/research/72-evidence/p0-measure.sh              # probes only, ~1 min
#   RUN_SOLVES=1 bash docs/research/72-evidence/p0-measure.sh # + the solves, ~10-20 min
#   RUN_CFD=1 RUN_SOLVES=1 bash ...                           # + pytest -m cfd (~5 min)
# SU2 has no default install location: export SU2_RUN=<dir holding SU2_CFD>.
# Everything runs in a temp dir; a banner-filtered copy of this output is
# written next to this script as p0b-mac-<date>.log so it can be committed
# (the licence gate scans this directory for OpenFOAM / SU2 file banners).
#
# bash 3.2 (the macOS default) is the target: no associative arrays, no mapfile.

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
EVID="$ROOT/docs/research/72-evidence"
SERVER="$ROOT/server"
STAMP=$(date +%Y-%m-%d)
WORK=${TMPDIR:-/tmp}/tee-p0b-$STAMP
mkdir -p "$WORK"
RAW="$WORK/p0-measure.raw.log"
exec > >(tee "$RAW") 2>&1

# perl's alarm is the portable timeout (macOS ships no `timeout`).
t() { perl -e 'alarm shift; exec @ARGV' "$@"; }
hr() { printf '\n=== %s\n' "$*"; }
say() { printf '%s\n' "$*"; }
absent() { say "NOT FOUND: $* (row stays open; see docs/setup-windtunnel.md)"; }

OS=$(uname -s)
hr "SYS  ($STAMP, $(hostname), $OS $(uname -m))"
if [ "$OS" = Darwin ]; then
  sw_vers 2>/dev/null | tr '\n' ' '; echo
  say "cores: $(sysctl -n hw.ncpu 2>/dev/null)  ram_gb: $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))"
  [ -z "$TEE_MACHINE_TOTAL_GB" ] && export TEE_MACHINE_TOTAL_GB=$(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 ))
else
  say "cores: $(nproc 2>/dev/null)  ram_gb: $(( $(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0) / 1048576 ))"
fi
say "TEE_MACHINE_TOTAL_GB=${TEE_MACHINE_TOTAL_GB:-unset}  (the ledger keeps a 16 GB reserve; a solve refused with job_refused_admission needs this set to the real total)"
say "repo: $ROOT  branch: $(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)  head: $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)"
say "uv: $(command -v uv || echo NOT FOUND)"
say "server venv python: $("$SERVER/.venv/bin/python" --version 2>&1 || echo 'no server/.venv - run uv sync in server/')"
DESKTOP_PY="$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python"
if [ -x "$DESKTOP_PY" ]; then say "desktop extension python: $("$DESKTOP_PY" --version 2>&1)"; else say "desktop extension venv: not present"; fi

hr "M1  OpenFOAM app: the entry-script route, a case on the normal filesystem, mpirun inside the app"
ENTRY=""
for app in $(ls -d /Applications/OpenFOAM-v*.app 2>/dev/null | sort -r); do
  if [ -f "$app/Contents/Resources/etc/openfoam" ]; then ENTRY="$app/Contents/Resources/etc/openfoam"; break; fi
done
if [ -n "$ENTRY" ]; then
  say "entry script: $ENTRY"
  t 60 "$ENTRY" bash -c 'echo "WM_PROJECT_VERSION=$WM_PROJECT_VERSION"; echo "WM_PROJECT_DIR=$WM_PROJECT_DIR"; echo "FOAM_TUTORIALS=$FOAM_TUTORIALS"; echo "simpleFoam: $(command -v simpleFoam)"; echo "arch: $(file -L "$(command -v simpleFoam)" | sed "s/.*: //")"; echo "mpirun: $(command -v mpirun)"; mpirun --version 2>&1 | head -1'
  say "volume: $(mount | grep -i openfoam | head -1)"
  mkdir -p "$WORK/m1" && t 60 "$ENTRY" bash -c 'touch "$0/probe" && echo "a case dir under \$HOME is writable from inside the entry environment"' "$WORK/m1"
  say "mpirun -np 2 inside the app -> $(t 60 "$ENTRY" bash -c 'mpirun -np 2 hostname 2>&1 | sort -u | tr "\n" " "')"
  say "M1 = route kind 'entry' (TEE composes: $ENTRY <app> <args>)"
else
  absent "/Applications/OpenFOAM-v*.app/Contents/Resources/etc/openfoam"
fi

hr "PROBE  tee doctor + wt_probe through the registry (version probes only)"
if command -v uv >/dev/null 2>&1; then
  (cd "$SERVER" && t 300 uv run --no-sync tee doctor 2>&1 | grep -i -B1 -A8 'wind' | head -30)
  (cd "$SERVER" && t 300 uv run --no-sync python - <<'PY'
import tempfile
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.windtunnel.tools import register_windtunnel_tools

project = Path(tempfile.mkdtemp(prefix="wt_p0b_probe_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
register_windtunnel_tools(app, project)
p = app.registry.call("wt_probe", {})
for name, d in p["engines"].items():
    where = d.get("path") or d.get("kind") or ""
    print(f"wt_probe {name}: found={d.get('found')} version={d.get('version')} via={d.get('via')} {where} {d.get('error', '')}")
print("wt_probe machine:", {k: v for k, v in p.items() if k != "engines"})
app.shutdown()
PY
  )
else
  absent "uv (the probes and solves run through the server venv)"
fi

hr "M2-M3  L2 / L3 / L4 on v2606: TEE's NACA 0012 O-mesh, kOmegaSST, 1 / 2 / 4 cores (RUN_SOLVES=1)"
if [ -z "$ENTRY" ]; then absent "OpenFOAM app (M1)"
elif [ "${RUN_SOLVES:-0}" != 1 ]; then say "skipped: RUN_SOLVES=1 runs it (about 3-6 minutes)"
else
  (cd "$SERVER" && uv run --no-sync python - <<'PY'
import glob, json, os, tempfile, time
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.waiting import wait_until
from tee.windtunnel.tools import register_windtunnel_tools

project = Path(tempfile.mkdtemp(prefix="wt_p0b_foam_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
store = register_windtunnel_tools(app, project)
call = app.registry.call


def done(job):
    wait_until(lambda: app.jobs.status(job)["state"] in ("done", "error", "cancelled"), 1800, max_delay_s=2.0)
    return app.jobs.status(job)


c = call("wt_case", {"action": "create", "naca": "0012", "V_mps": 30, "aoa_deg": 4})
cid = c["case_id"]
print("case", cid, c.get("engine"), json.dumps(c.get("fidelity"), default=str))
m = call("wt_mesh", {"case_id": cid, "nj": 60, "n_surface": 60})
print("mesh", {k: m.get(k) for k in ("cells", "points", "kind", "first_cell_m", "wall_s")}, "checkMesh ok:", (m.get("checkMesh") or {}).get("ok"))
cells = m.get("cells") or 0
for cores, iters in ((1, 600), (2, 400), (4, 400)):
    t0 = time.time()
    try:
        r = call("wt_run", {"case_id": cid, "iters": iters, "cores": cores, "confirm_cost": True})
    except Exception as exc:  # a refusal is a row too
        print(f"L2/L4 cores={cores} refused: {type(exc).__name__}: {str(exc)[:300]}")
        continue
    st = done(r["job"])
    res = st.get("result") or {}
    wall = round(time.time() - t0, 1)
    used = res.get("iters_used") or 0
    k = (wall * cores) / (cells * used) if cells and used else None
    row = {"state": st["state"], "wall_s": wall, "iters": used, "cl": res.get("cl"), "cd": res.get("cd"), "cm": res.get("cm"),
           "verdict": (res.get("verdict") or {}).get("state"), "k_openfoam_s_per_cell_iter_core": (round(k, 10) if k else None),
           "error": (st.get("error") or "")[:200]}
    print(f"L2/L4 cores={cores}", json.dumps(row, default=str))
rec = store.load(cid)
last = rec["runs"][-1]
print("run record: engine_version", last.get("engine_version"), "| argv[:3]", (last.get("argv") or [])[:3], "| mpi_root_override", last.get("mpi_root_override"))
run_dir = last.get("run_dir") or ""
for f in sorted(glob.glob(os.path.join(run_dir, "postProcessing", "**", "*.dat"), recursive=True))[:2]:
    head = [ln.rstrip() for ln in open(f, errors="replace").readlines()[:12] if ln.startswith("#")]
    print("L3", os.path.relpath(f, run_dir), "header:", head[-3:])
app.shutdown()
PY
  )
fi

hr "M4  SU2: binary architecture (arm64 vs Rosetta) and the L5 Euler case (RUN_SOLVES=1)"
SU2=""
for cand in "${SU2_RUN:-/nonexistent}/SU2_CFD" "$HOME/SU2/bin/SU2_CFD" /opt/SU2/bin/SU2_CFD $HOME/Applications/SU2*/bin/SU2_CFD "$(command -v SU2_CFD 2>/dev/null)"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then SU2="$cand"; break; fi
done
if [ -n "$SU2" ]; then
  say "SU2_CFD: $SU2"
  say "arch: $(file -L "$SU2" | sed 's/.*: //')   (an x86_64 binary on Apple silicon runs under Rosetta - record it, do not hide it)"
  say "version line: $(t 30 "$SU2" -h 2>&1 | grep -m1 -E 'v?[0-9]+\.[0-9]+\.[0-9]+')"
  [ -z "$SU2_RUN" ] && export SU2_RUN="$(dirname "$SU2")"
  if [ "${RUN_SOLVES:-0}" = 1 ]; then
    (cd "$SERVER" && t 1800 uv run --no-sync python "$EVID/smoke_registry.py" su2)
  else
    say "L5 skipped: RUN_SOLVES=1 runs smoke_registry.py su2 (the M 0.8 alpha 1.25 Euler case on TEE's O-mesh; compare with the QuickStart figure in verify.py)"
  fi
else
  absent "SU2_CFD (export SU2_RUN=<dir holding SU2_CFD>, or put it in ~/SU2/bin)"
fi

hr "M5  ParaView pvpython: version and an offscreen render with no display"
PV=""
for cand in $(ls -d /Applications/ParaView-*.app 2>/dev/null | sort -r); do
  if [ -x "$cand/Contents/bin/pvpython" ]; then PV="$cand/Contents/bin/pvpython"; break; fi
done
[ -z "$PV" ] && PV="$(command -v pvpython 2>/dev/null)"
if [ -n "$PV" ]; then
  say "pvpython: $PV"
  say "version: $(t 60 "$PV" --version 2>&1 | head -1)"
  mkdir -p "$WORK/m5"
  cat > "$WORK/m5/probe.py" <<'PY'
import os
import sys
from paraview.simple import *  # noqa: F401,F403 - pvpython's own module

s = Sphere()
Show(s)
Render()
SaveScreenshot(sys.argv[1], ImageResolution=[160, 120])
print("png bytes", os.path.getsize(sys.argv[1]))
PY
  # The exit status is the row, so it is taken before anything is piped:
  # rc=0 with a PNG means offscreen works; 139 is the segfault apt ParaView
  # 5.11 gives without xvfb on Linux (P0 row L6).
  (unset DISPLAY; t 180 "$PV" --force-offscreen-rendering "$WORK/m5/probe.py" "$WORK/m5/probe.png" > "$WORK/m5/out.txt" 2>&1; rc=$?; tail -2 "$WORK/m5/out.txt" | cut -c1-160; say "offscreen render rc=$rc  png: $( [ -s "$WORK/m5/probe.png" ] && wc -c < "$WORK/m5/probe.png" | tr -d ' ' || echo none ) bytes")
else
  absent "/Applications/ParaView-*.app/Contents/bin/pvpython"
fi

hr "M6-M7  OpenVSP: bundle paths, architecture, vspaero, the Python API from the 3.11 and 3.13 venvs (import only, recorded, never used), L7 (RUN_SOLVES=1)"
VSP=""
for cand in /Applications/OpenVSP*/vspscript $HOME/OpenVSP*/vspscript "$(command -v vspscript 2>/dev/null)"; do
  if [ -n "$cand" ] && [ -x "$cand" ]; then VSP="$cand"; break; fi
done
if [ -n "$VSP" ]; then
  VSPDIR=$(dirname "$VSP")
  say "vspscript: $VSP"
  say "arch: $(file -L "$VSP" | sed 's/.*: //')"
  say "version: $(t 30 "$VSP" -help 2>&1 | grep -m1 -i 'sketch pad')"
  if [ -x "$VSPDIR/vspaero" ]; then say "vspaero: $VSPDIR/vspaero -> $(t 30 "$VSPDIR/vspaero" 2>&1 | grep -m1 -i 'vspaero')"; else say "vspaero: not next to vspscript ($(command -v vspaero || echo 'not on PATH'))"; fi
  say "python bits in the bundle: $(find "$VSPDIR" -maxdepth 3 \( -iname 'openvsp*' -o -name '*.so' \) 2>/dev/null | head -5 | tr '\n' ' ')"
  for py in "$SERVER/.venv/bin/python" "$DESKTOP_PY"; do
    [ -x "$py" ] || continue
    say "import openvsp under $("$py" -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'): $(PYTHONPATH="$VSPDIR/python:$VSPDIR/python/openvsp:$VSPDIR/python/packages" t 60 "$py" -c 'import openvsp; print("imports:", openvsp.__file__)' 2>&1 | tail -1)"
  done
  if [ "${RUN_SOLVES:-0}" = 1 ]; then
    (cd "$SERVER" && t 900 uv run --no-sync python "$EVID/smoke_registry.py" vsp)
  else
    say "L7 skipped: RUN_SOLVES=1 runs smoke_registry.py vsp (AR 10 wing, four angles; compare cl_alpha with lifting line 5.19/rad)"
  fi
else
  absent "/Applications/OpenVSP*/vspscript (set [windtunnel] openvsp = <its folder> in the project config)"
fi

hr "C1-C3  FreeCAD + CfdOF: presence, version, the headless import (recorded only)"
FC=""
for cand in /Applications/FreeCAD*.app; do
  if [ -x "$cand/Contents/MacOS/FreeCAD" ]; then FC="$cand"; break; fi
done
if [ -n "$FC" ]; then
  say "FreeCAD: $FC -> $(t 60 "$FC/Contents/MacOS/FreeCAD" --version 2>&1 | head -1)"
  CFDOF=""
  for cand in "$HOME/Library/Application Support/FreeCAD/Mod/CfdOF" "$HOME/Library/Preferences/FreeCAD/Mod/CfdOF"; do
    [ -d "$cand" ] && CFDOF="$cand" && break
  done
  if [ -n "$CFDOF" ]; then
    say "CfdOF: $CFDOF -> $(grep -m1 -o '<version>[^<]*</version>' "$CFDOF/package.xml" 2>/dev/null || echo 'no package.xml')"
    FCCMD="$FC/Contents/MacOS/FreeCADCmd"
    [ -x "$FCCMD" ] || FCCMD="$(command -v freecadcmd 2>/dev/null)"
    if [ -n "$FCCMD" ]; then
      say "C1 headless import (cwd /): $(cd / && t 120 "$FCCMD" -c 'import CfdOF; print("CfdOF imports from", CfdOF.__file__)' 2>&1 | tail -1)"
    else
      say "C1: no FreeCADCmd next to the app and none on PATH"
    fi
    say "C2 (the RPC route through FreeCADWire.py_json) needs the GUI open with TEE's bridge: run it from a TEE session, not from here"
    say "C3: write one case with the CfdOF workbench, then: tee_call wt_case action=adopt path=<that case dir> - the adoption report (solver, mesher, patches, Allrun sequence, warnings) is the row"
  else
    say "CfdOF workbench: not installed (FreeCAD Addon Manager -> CfdOF); rows C1-C3 stay open"
  fi
else
  absent "/Applications/FreeCAD*.app (rows C1-C3 stay open)"
fi

hr "S1  SimFlow (a browser row, nothing to run)"
say "record from sim-flow.com in a browser: free-tier limits (cells / cores), platforms, any API, and whether a project saves a standard OpenFOAM case directory; if it does, that directory adopts like any other"

hr "M8  the app's own airFoil2D tutorial adopted and run with forces= (L13 on v2606; RUN_SOLVES=1)"
if [ -z "$ENTRY" ]; then absent "OpenFOAM app (M1)"
elif [ "${RUN_SOLVES:-0}" != 1 ]; then say "skipped: RUN_SOLVES=1 runs it"
else
  TUT=$(t 60 "$ENTRY" bash -c 'echo "$FOAM_TUTORIALS"')/incompressible/simpleFoam/airFoil2D
  if [ -d "$TUT" ]; then
    say "tutorial (read-only volume; adoption copies it): $TUT"
    (cd "$SERVER" && uv run --no-sync python - "$TUT" <<'PY'
import json, sys, tempfile, time
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.waiting import wait_until
from tee.windtunnel.tools import register_windtunnel_tools

tut = Path(sys.argv[1])
project = Path(tempfile.mkdtemp(prefix="wt_p0b_adopt_"))
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
store = register_windtunnel_tools(app, project)
call = app.registry.call


def done(job):
    wait_until(lambda: app.jobs.status(job)["state"] in ("done", "error", "cancelled"), 1800, max_delay_s=2.0)
    return app.jobs.status(job)


try:
    ad = call("wt_case", {"action": "adopt", "path": str(tut)})
    print("adopt", json.dumps({k: ad.get(k) for k in ("case_id", "solver", "mesher", "patches", "inlet_U", "turbulence", "warnings")}, default=str)[:700])
    acid = ad["case_id"]
    m = call("wt_mesh", {"case_id": acid})
    print("mesh", json.dumps(m, default=str)[:300])
    t0 = time.time()
    r = call("wt_run", {"case_id": acid, "confirm_cost": True, "forces": {"patches": ["walls"]}})
    st = done(r["job"])
    res = call("wt_result", {"case_id": acid})
    print("M8", json.dumps({"job": st["state"], "wall_s": round(time.time() - t0, 1), "cl": res.get("cl"), "cd": res.get("cd"), "cm": res.get("cm"),
                            "verdict": res.get("verdict"), "forces": store.load(acid)["runs"][-1].get("forces"), "error": st.get("error")}, default=str)[:900])
except TeeError as exc:
    print("M8 refused:", exc.code, exc.message[:300], "| fix:", exc.fix)
app.shutdown()
PY
    )
  else
    say "no airFoil2D under FOAM_TUTORIALS ($TUT); row stays open"
  fi
fi

hr "CFD TIER  pytest -m cfd tests/test_windtunnel_live.py (RUN_CFD=1)"
if [ "${RUN_CFD:-0}" = 1 ] && command -v uv >/dev/null 2>&1; then
  [ -n "${TUT:-}" ] && [ -d "${TUT:-/nonexistent}" ] && export TEE_WT_TUTORIAL="$TUT"
  (cd "$SERVER" && uv run --no-sync pytest -q -m cfd tests/test_windtunnel_live.py 2>&1 | tail -15)
else
  say "skipped: RUN_CFD=1 runs it (each test skips by name with the install line where an engine is absent)"
fi

hr "DONE"
FILTERED="$EVID/p0b-mac-$STAMP.log"
grep -v -E 'Open Source CFD Toolbox|OpenFOAM Foundation|OpenCFD Ltd|openfoam\.(com|org)|SU2 Foundation|su2foundation|Copyright 2012-20|Christophe Geuzaine' "$RAW" > "$FILTERED"
say "raw log: $RAW"
say "banner-filtered copy for the commit: $FILTERED"
say "next: paste the sections above into docs/PROGRESS.md under '### A72 P0b - the Mac rows ($STAMP, owner session)',"
say "      turn the macOS block of docs/setup-windtunnel.md from a checklist into the measured lines, and fill §M of CLAUDE_A72_SCRIPT.md"
