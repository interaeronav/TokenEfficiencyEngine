"""Is JSBSim here, by which route, and at what version.

Three routes exist and carry three different licences (doc 75 section 2.1);
the ruling is in-process, so that is what this probes for. The other two are
reported when present because a machine that has them can still be told what
they are.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

INSTALL = "pip install jsbsim  (or: uv pip install --project server jsbsim)"

#: Files whose licence grant the gate asserts on. Paths are relative to the
#: installed package. `script.py` is the GPL-3 one; see the module docstring.
LICENCE_FILES = ("__init__.py", "script.py")


def _module_spec():
    try:
        return importlib.util.find_spec("jsbsim")
    except (ImportError, ValueError):
        return None


def probe() -> dict[str, Any]:
    """What this machine can do, without importing JSBSim into this process."""
    spec = _module_spec()
    out: dict[str, Any] = {"route": "in-process", "present": spec is not None}
    if spec is None:
        out["fix"] = INSTALL
        out["reason"] = "the jsbsim wheel is not importable here"
        return out

    # Ask in a child: importing the extension into the server is what the
    # SIGSEGV finding says not to do casually.
    code = (
        "import jsbsim,os,json;"
        "print(json.dumps({'version':jsbsim.__version__,"
        "'root':jsbsim.get_default_root_dir()}))"
    )
    try:
        # sys.executable, NOT a bare "python": under a bundled venv the PATH
        # python is a different interpreter, and the probe would report the
        # wheel absent on a machine that has it.
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:  # pragma: no cover - defensive
        out["present"] = False
        out["reason"] = f"jsbsim is installed but would not import: {exc}"
        out["fix"] = INSTALL
        return out
    if r.returncode != 0:
        out["present"] = False
        out["reason"] = (r.stderr or "").strip()[:400] or "import failed"
        out["fix"] = INSTALL
        return out

    import json

    got = json.loads(r.stdout.strip().splitlines()[-1])
    out["version"] = got["version"]
    out["data_root"] = got["root"]
    root = Path(got["root"])
    ac = root / "aircraft"
    out["bundled_aircraft"] = sum(1 for p in ac.iterdir() if p.is_dir()) if ac.is_dir() else 0
    # The other two routes, reported but never used by this lane.
    cli = shutil.which("JSBSim")
    out["other_routes"] = {
        "wheel_cli": {"present": (root / "script.py").exists(), "licence": "GPL-3.0-or-later"},
        "cpp_binary": {"present": bool(cli), "licence": "LGPL-2.0-or-later"},
    }
    return out
