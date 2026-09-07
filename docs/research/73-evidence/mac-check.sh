#!/usr/bin/env bash
# generated-by: tee.windtunnel - the A73 Mac verification script (owner session).
#
# Prints, never asserts. It answers, on the owner's machine, the rows this
# campaign could not answer in a Linux container with an apt ParaView:
#
#   A  which ParaView the lane resolves, and whether pvpython and the GUI
#      come from ONE install (doc 73 open question 1 turns on this)
#   B  the SEAL: does writing a state leave the signed .app intact? The
#      instability that started the replacement hunt was TEE writing .pyc
#      files into the bundle (base commit c082dae); the guard is verified
#      here on the handoff path, which nobody has checked yet
#   C  the handoff on ParaView 6.1: a state written and loaded back, and
#      `view=mesh` on a case with no run - the two P2 defects, on the version
#      this container does not have
#   D  doc 73 open question 2: does `open -a ParaView --args --state=` pass
#      the flag through? A human has to look at the window; the script sets
#      it up and says what to look for
#
# Usage, from the repo root on the campaign branch, on the Mac:
#   bash docs/research/73-evidence/mac-check.sh            # ~2 min, no solver
#   RUN_SOLVE=1 bash docs/research/73-evidence/mac-check.sh  # + a real run, ~3 min
#   OPEN_GUI=1 bash docs/research/73-evidence/mac-check.sh   # + section D (opens a window)
#
# Nothing here installs, downloads or edits the tree. A banner-filtered copy of
# the output lands beside this script as mac-a73-<date>.log so it can be
# committed. bash 3.2 (the macOS default) is the target.

ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
EVID="$ROOT/docs/research/73-evidence"
SERVER="$ROOT/server"
STAMP=$(date +%Y-%m-%d)
WORK=${TMPDIR:-/tmp}/tee-a73-$STAMP
mkdir -p "$WORK"
RAW="$WORK/mac-check.raw.log"
exec > >(tee "$RAW") 2>&1

say() { printf '\n=== %s ===\n' "$*"; }
py() { (cd "$SERVER" && TEE_MACHINE_TOTAL_GB=${TEE_MACHINE_TOTAL_GB:-64} uv run --no-sync python "$@"); }

echo "A73 Mac check - $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "macOS $(sw_vers -productVersion 2>/dev/null) $(uname -m)   repo $ROOT"
echo "branch $(git -C "$ROOT" rev-parse --abbrev-ref HEAD)   head $(git -C "$ROOT" rev-parse --short HEAD)"

# -- A: which install --------------------------------------------------------
say "A. what the lane resolves"
cat > "$WORK/a_resolve.py" <<'PY'
from tee.windtunnel import engines
for name, fn in (("pvpython", engines.find_pvpython), ("paraview app", engines.find_paraview_app)):
    try:
        b = fn({})
        v = b.version or "(not probed: asking ParaView anything without a display aborts it)"
        print(f"{name:12s} {b.path}   via {b.via}   version {v}")
    except Exception as exc:
        print(f"{name:12s} NOT FOUND: {exc}")
PY
py "$WORK/a_resolve.py"
APP=$(py - <<'PY' 2>/dev/null
from pathlib import Path
from tee.windtunnel import engines
try:
    p = Path(engines.find_paraview_app({}).path)
except Exception:
    raise SystemExit(0)
for parent in [p, *p.parents]:
    if parent.suffix == ".app":
        print(parent)
        break
PY
)
echo "bundle: ${APP:-<not a .app - nothing to seal>}"

# -- B: the seal -------------------------------------------------------------
say "B. the signed bundle, before and after a state is written"
if [ -z "$APP" ]; then
  echo "no .app bundle here, so nothing can be unsealed; section B does not apply"
else
  echo "-- before"
  echo "   .pyc inside the bundle: $(find "$APP" -name '*.pyc' 2>/dev/null | wc -l | tr -d ' ')"
  codesign --verify --deep --strict "$APP" >/tmp/a73_cs.$$ 2>&1; cs=$?
  head -3 /tmp/a73_cs.$$; rm -f /tmp/a73_cs.$$
  echo "   codesign rc=$cs"   # $? after a PIPE is head's status, never codesign's
  spctl -a -t exec -vv "$APP" 2>&1 | head -2
fi
cat > "$WORK/b_state.py" <<'PY'
"""Write a state through the lane, exactly as wt_open does."""
import json, os, sys, time
from pathlib import Path
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.windtunnel.tools import register_windtunnel_tools

project = Path(sys.argv[1]) / "project"
app = TeeApp({"fake": FakeAdapter()}, project_root=project)
store = register_windtunnel_tools(app, project)
call = lambda tool, **a: app.registry.call(tool, a)
try:
    cid = call("wt_case", action="create", naca="0012", V_mps=30, aoa_deg=4)["case_id"]
    mesh = call("wt_mesh", case_id=cid, nj=40)
    print("mesh:", {k: mesh.get(k) for k in ("ok", "cells", "kind")})
    if os.environ.get("RUN_SOLVE"):
        t0 = time.time()
        started = call("wt_run", case_id=cid, iters=300)
        job = started["job"]
        for _ in range(600):
            # app.jobs, not registry.call("tee_job"): tee_job is registered on
            # the MCP server (server.py), and this harness only registers the
            # wt_* lane, so the tool name does not exist here. RUN_SOLVE=1
            # raised "No tool named 'tee_job'" and the solve never ran, which
            # left section C vacuous while looking like it had run.
            st = app.jobs.status(job)
            if st.get("state") in ("done", "error", "cancelled"):
                break
            time.sleep(1.0)
        print("run:", st.get("state"), f"{time.time() - t0:.1f} s")
    for view in ("pressure", "mesh"):
        t = time.time()
        out = call("wt_open", case_id=cid, view=view)
        print(
            f"wt_open view={view}:",
            json.dumps({k: out.get(k) for k in ("kind", "bytes", "run_id", "launched")}),
            f"{time.time() - t:.1f} s",
        )
        print("   command:", out.get("command_line"))
        Path(sys.argv[1], f"state_{view}.txt").write_text(out["state"])
finally:
    app.shutdown()
PY
py "$WORK/b_state.py" "$WORK"
if [ -n "$APP" ]; then
  echo "-- after"
  echo "   .pyc inside the bundle: $(find "$APP" -name '*.pyc' 2>/dev/null | wc -l | tr -d ' ')"
  codesign --verify --deep --strict "$APP" >/tmp/a73_cs.$$ 2>&1; cs=$?
  head -3 /tmp/a73_cs.$$; rm -f /tmp/a73_cs.$$
  echo "   codesign rc=$cs"   # $? after a PIPE is head's status, never codesign's
  echo "   (0 .pyc and rc 0 is the pass; PYTHONDONTWRITEBYTECODE=1 in run_script is what does it)"
  echo "   to repair an already-damaged install: find <app> -name __pycache__ -type d -exec rm -rf {} +"
fi

# -- C: the handoff on this ParaView ----------------------------------------
say "C. the state, loaded back in a fresh pvpython (the two P2 defects)"
cat > "$WORK/c_load.py" <<'PY'
import json, sys
from pathlib import Path
from tee.windtunnel import engines, paraview as pv

for view in ("pressure", "mesh"):
    marker = Path(sys.argv[1], f"state_{view}.txt")
    if not marker.is_file():
        print(f"{view}: no state was written, nothing to load")
        continue
    pvsm = marker.read_text().strip()
    script = """
from paraview.simple import *
import json
LoadState(__PVSM__)
src = [v for k, v in GetSources().items()][0]
views = GetViews()
rv = views[0] if views else None
src.UpdatePipeline(rv.ViewTime if rv is not None else 0.0)
f = {'reader': src.__class__.__name__,
     'cells': int(src.GetDataInformation().GetNumberOfCells()),
     'timesteps': [float(t) for t in (src.TimestepValues or [])],
     'scene_time': float(GetAnimationScene().AnimationTime)}
if rv is not None:
    d = GetDisplayProperties(src, rv)
    f['view_time'] = float(rv.ViewTime)
    f['colour'] = [str(x) for x in d.ColorArrayName]
    f['representation'] = str(d.Representation).strip("'")
print('FACTS ' + json.dumps(f))
print('OK')
""".replace("__PVSM__", repr(pvsm))
    try:
        out = pv.run_script(
            engines.find_pvpython({}).path, script, Path(pvsm).parent / "_lb", render=True
        )
        facts = json.loads(next(x for x in out.splitlines() if x.startswith("FACTS "))[6:])
        print(f"{view}: {json.dumps(facts)}")
        last = (facts.get("timesteps") or [0.0])[-1]
        if last <= 0.0:
            print("   time: only t=0 exists on this case, so the check is vacuous "
                  "- RUN_SOLVE=1 gives it a solution to open at")
        elif facts.get("view_time") == last:
            print(f"   time: OPENS AT THE SOLUTION, t={last} (defect 1 fixed on this version)")
        else:
            print(f"   time: OPENS AT {facts.get('view_time')} of {facts['timesteps']} - REGRESSION")
    except Exception as exc:
        print(f"{view}: FAILED - {str(exc)[:300]}")
PY
py "$WORK/c_load.py" "$WORK"
echo "(a mesh-view state that loads at all is defect 2 fixed on this version:"
echo " ColorBy(d, None) raised 'invalid association string NONE' on 5.11.2)"

# -- D: the startup flag -----------------------------------------------------
say "D. does the GUI take --state on macOS? (doc 73 open question 2)"
STATE=$(cat "$WORK/state_pressure.txt" 2>/dev/null)
if [ -z "$STATE" ]; then
  echo "no state file, so nothing to open"
elif [ -z "$OPEN_GUI" ]; then
  echo "skipped (OPEN_GUI=1 to run it - it opens a window)"
  echo "what wt_open would run:  $(py - <<PY
from tee.windtunnel import engines
print(engines.find_paraview_app({}).path, "--state=$STATE")
PY
)"
else
  echo "1) the argv wt_open composes (the binary inside the bundle, no 'open'):"
  py - <<PY
from tee.windtunnel import engines
print("   ", engines.find_paraview_app({}).path, "--state=$STATE")
PY
  echo "2) the macOS idiom, which doc 73 documented but never measured:"
  echo "   open -a ParaView --args --state=$STATE"
  open -a ParaView --args --state="$STATE" 2>&1 | head -3
  sleep 8
  pgrep -fl -i paraview | head -3
  echo ""
  echo "   LOOK AT THE WINDOW and answer two things:"
  echo "     - did the pipeline browser open the case, or is it an empty ParaView?"
  echo "     - is it coloured by p at the last time step, or grey at t=0?"
  echo "   Then quit ParaView. An empty window means the flag did NOT pass through"
  echo "   and the documented macOS idiom is wrong; wt_open's own argv is what matters."
fi

# -- E: what stays open ------------------------------------------------------
say "E. what this run does not settle"
echo "Doc 73 open question 1 - does ParaView 6.1 accept a 5.11-WRITTEN state?"
echo "  Not answerable here: this machine writes with its own pvpython, and"
echo "  section A prints whether that pvpython and the GUI come from one"
echo "  install. If they do, the skew only arises when a state is carried"
echo "  between machines, which nothing in the lane does today."

LOG="$EVID/mac-a73-$STAMP.log"
grep -v -i -E "OpenFOAM Foundation|www\.openfoam|GNU General Public|Copyright \(C\)|SU2 (v[0-9]|Project)|NASA Open Source" "$RAW" > "$LOG"
echo ""
echo "log written: $LOG"
