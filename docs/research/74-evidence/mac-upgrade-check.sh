#!/usr/bin/env bash
# generated-by: tee.windtunnel - the A74/A77 upgrade check (owner session).
#
# Prints, never asserts. Run it on the Mac AFTER installing a new .mcpb, to
# answer the four things a Linux container cannot:
#
#   A  which extension is installed, and which venv it runs in
#   B  the FLEET EXTRAS: installing a bundle rebuilds the venv from its lock
#      and drops anything pip-installed on top. The failure is quiet - tools
#      report {"installed": false}, which reads as "you never set this up"
#      rather than "your upgrade removed it" - so check on purpose
#   C  does THIS machine's OpenFOAM carry cfMesh? Open since A74 P0 as doc 74
#      section 5 question 3; wt_probe now answers it in the openfoam row
#   D  A74's new default, end to end: a bare wt_mesh on a 3-D body should pick
#      cfMesh, run surfaceFeatureEdges -> cartesianMesh -> checkMesh, and pass
#      the check CLEAN. Skipped without OpenFOAM; ~30 s with it
#
# Usage, from the repo root on the campaign branch:
#   bash docs/research/74-evidence/mac-upgrade-check.sh          # A-C, seconds
#   RUN_MESH=1 bash docs/research/74-evidence/mac-upgrade-check.sh   # + D
#
# Nothing here installs, downloads, or edits the tree or your config. It prints
# the restore command when something is missing; it does not run it. bash 3.2
# (the macOS default) is the target, and `uv run` is always --no-sync, because
# a bare `uv run` re-syncs the venv and drops the very extras section B checks.

set -u
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
SERVER="$ROOT/server"
STAMP=$(date +%Y-%m-%d)
WORK=${TMPDIR:-/tmp}/tee-a74-upgrade-$STAMP
mkdir -p "$WORK"
EXT="$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine"

say() { printf '\n=== %s ===\n' "$*"; }
py() { (cd "$SERVER" && TEE_MACHINE_TOTAL_GB=${TEE_MACHINE_TOTAL_GB:-64} uv run --no-sync python "$@"); }

echo "A74/A77 upgrade check - $(date -u +%Y-%m-%dT%H:%M:%SZ)"
MACOS=$(sw_vers -productVersion 2>/dev/null)
echo "host    $(uname -s) $(uname -m)${MACOS:+ macOS $MACOS}"
echo "repo    $ROOT"
echo "branch  $(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)  head $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null)"
echo "declared version (repo): $(grep -m1 '^version' "$SERVER/pyproject.toml" | cut -d'"' -f2)"

# -- A: the installed extension ---------------------------------------------
say "A. the installed extension"
if [ -d "$EXT" ]; then
  MAN="$EXT/manifest.json"
  if [ -f "$MAN" ]; then
    echo "installed version: $(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['version'])" "$MAN" 2>/dev/null || echo '(unreadable)')"
  else
    echo "no manifest.json under the extension dir"
  fi
  VENV_PY="$EXT/.venv/bin/python"
  if [ -x "$VENV_PY" ]; then
    echo "venv python      : $VENV_PY"
    echo "                   $("$VENV_PY" -V 2>&1)"
  else
    echo "venv python      : NOT FOUND at $VENV_PY"
  fi
else
  echo "no Claude extension dir here - section A is macOS/Desktop only."
  echo "  looked in: $EXT"
  VENV_PY=""
fi

# -- B: the fleet extras -----------------------------------------------------
say "B. fleet extras (the quiet casualty of every upgrade)"
cat > "$WORK/b_extras.py" <<'PY'
import sys
from importlib.util import find_spec
# the same witness map the doctor uses, read from the package rather than
# retyped - a hand-copied list is how this check goes stale
from tee.kernel.extras import NOT_IN_TEE_VENV, WITNESS

here, gone = [], []
for group, module in sorted(WITNESS.items()):
    (here if find_spec(module) else gone).append((group, module))
print(f"interpreter: {sys.executable}")
for group, module in here:
    print(f"  present  {group:11s} (witness {module})")
for group, module in gone:
    tail = "  - sidecar by design, never in this venv" if group in NOT_IN_TEE_VENV else ""
    print(f"  MISSING  {group:11s} (witness {module}){tail}")
wanted = [g for g, _ in gone if g not in NOT_IN_TEE_VENV]
if wanted:
    print("\nrestore with:")
    print(f"  uv pip install --python '{sys.executable}' \\")
    print("    " + " ".join(f"'tee-engine[{g}]'" for g in wanted))
else:
    print("\nnothing to restore.")
PY
py "$WORK/b_extras.py"

echo
echo "-- and what the product's own check says (it remembers what it last saw):"
if [ -n "${VENV_PY:-}" ] && [ -x "$EXT/.venv/bin/tee" ]; then
  "$EXT/.venv/bin/tee" doctor 2>&1 | awk '/fleet extras/{p=1;print;next} p&&/^[[:space:]]/{print;next} p{exit}' || echo "  (no 'fleet extras' row in the doctor output)"
else
  (cd "$SERVER" && uv run --no-sync tee doctor 2>&1 | awk '/fleet extras/{p=1;print;next} p&&/^[[:space:]]/{print;next} p{exit}') \
    || echo "  (repo doctor: no 'fleet extras' row)"
  echo "  NOTE: that is the REPO's venv, not the extension's. On the Mac the"
  echo "        extension's own 'tee doctor' is the one that matters."
fi

# -- C: cfMesh on this machine ----------------------------------------------
say "C. does this OpenFOAM carry cfMesh? (doc 74 section 5, question 3)"
cat > "$WORK/c_probe.py" <<'PY'
import tempfile
from pathlib import Path

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.windtunnel.tools import register_windtunnel_tools

app = TeeApp({"fake": FakeAdapter()}, project_root=Path(tempfile.mkdtemp()))
register_windtunnel_tools(app, Path(tempfile.mkdtemp()))
row = app.registry.call("wt_probe", {})["engines"]["openfoam"]
print("openfoam:", {k: row.get(k) for k in ("found", "version", "fork", "via", "cfmesh")})
if not row.get("found"):
    print("  -> no OpenFOAM here; section D will skip. Install line:", row.get("fix"))
elif row.get("cfmesh"):
    print("  -> cfMesh IS in this install. A74's mesher=auto will use it.")
else:
    print("  -> cfMesh is NOT here: auto falls back to snappyHexMesh and says so,")
    print("     and mesher=cfmesh refuses by name. openfoam.com's build has it")
    print("     from v1806; nothing is downloaded for you.")
app.shutdown()
PY
py "$WORK/c_probe.py"

# -- D: A74's default, end to end -------------------------------------------
say "D. a bare wt_mesh on a 3-D body (set RUN_MESH=1 to run it)"
if [ "${RUN_MESH:-0}" != "1" ]; then
  echo "skipped. RUN_MESH=1 to mesh a small prism with the real binaries (~30 s)."
else
  cat > "$WORK/d_mesh.py" <<'PY'
import tempfile
import time
from pathlib import Path

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.waiting import wait_until
from tee.windtunnel import airfoil
from tee.windtunnel.tools import register_windtunnel_tools

root = Path(tempfile.mkdtemp())
app = TeeApp({"fake": FakeAdapter()}, project_root=root)
register_windtunnel_tools(app, root)
if not app.registry.call("wt_probe", {})["engines"]["openfoam"].get("found"):
    print("no OpenFOAM: nothing to mesh with.")
    raise SystemExit
stl = root / "prism.stl"
airfoil.extrude_stl(stl, airfoil.naca4("0012", 24), span=0.4, chord=0.3, name="section")
cid = app.registry.call(
    "wt_case", {"action": "create", "stl": str(stl), "V_mps": 20}
)["case_id"]
t0 = time.time()
started = app.registry.call("wt_mesh", {"case_id": cid, "base_cell_m": 0.15, "layers": 2})
print("sequence:", started.get("sequence") or "(a job; see below)")
job = started.get("job")
if job:
    # the job's status comes from app.jobs, NOT registry.call("tee_job"): that
    # is an always-loaded MCP tool and is not in the registry (A73 P2 defect)
    wait_until(lambda: app.jobs.status(job)["state"] in ("done", "error", "cancelled"), 900,
               max_delay_s=0.5)
    st = app.jobs.status(job)
    mesh = st.get("result") or {}
    print("state:", st["state"], f"in {round(time.time() - t0, 1)} s")
else:
    mesh = started
failed = mesh.get("failed") or []
print(f"mesher   : {mesh.get('kind')}   feature_angle {mesh.get('feature_angle')}")
print(f"chose    : {(mesh.get('chose') or '(named by the caller)')[:100]}")
print(f"cells    : {mesh.get('cells')}   ok {mesh.get('ok')}   checkMesh failed: {failed or 'NONE'}")
print(f"repeatable: threads {mesh.get('threads')}  reproducible {mesh.get('reproducible')}")
if mesh.get("kind") == "cfmesh" and not failed:
    print("  -> A74 works here: auto picked cfMesh and checkMesh passed clean.")
elif mesh.get("kind") == "snappy":
    print("  -> auto fell back to snappyHexMesh; section C says why.")
elif failed:
    print("  -> checkMesh flagged something. The log is in the case's engine dir.")
app.shutdown()
PY
  py "$WORK/d_mesh.py"
fi

say "done"
echo "Nothing was installed, downloaded or changed. Raw scratch: $WORK"
