"""Where the engines are, how each is invoked, and what version answered.

Discovery is the capture lane's rule (`capture/align.py`): an explicit
`[windtunnel]` config entry wins and refuses LOUDLY when it is wrong (a
wrong path must never fall through to whatever PATH holds), then the known
install locations per platform, then `shutil.which`. Every refusal names the
install line, its size and the date it was verified.

OpenFOAM is special: its binaries need the environment its own `etc/bashrc`
sets, and the macOS app additionally mounts a read-only volume from its
`etc/openfoam` entry script. So an OpenFOAM install is a *route*, not a
binary: `FoamInstall.argv("simpleFoam", "-case", x)` composes the argv that
works for the route found - measured 2026-09-06 on apt v1912 (bashrc) and
documented for OpenFOAM-v2606.app (entry script).
"""

from __future__ import annotations

import glob
import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

INSTALL = {
    "openfoam": {
        "Darwin": (
            "brew install gerlero/openfoam/openfoam  "
            "(OpenFOAM-v2606.app, native Apple silicon; verified 2026-09-06)"
        ),
        "Linux": (
            "sudo apt-get install openfoam  "
            "(openfoam.com v1912, 128 MB; verified 2026-09-06 on Ubuntu 24.04)"
        ),
    },
    "su2": {
        "Darwin": (
            "download SU2-v8.4.0-macos64.zip from github.com/su2code/SU2/releases "
            "and set [windtunnel] su2 = <its bin dir>"
        ),
        "Linux": (
            "download SU2-v8.4.0-linux64.zip (31 MB, static binaries; verified 2026-09-06) "
            "from github.com/su2code/SU2/releases and set [windtunnel] su2 = <its bin dir>"
        ),
    },
    "openvsp": {
        "Darwin": (
            "download OpenVSP-3.51.3-macos-14-ARM64-Python3.11.zip from openvsp.org/download.php "
            "and set [windtunnel] openvsp = <its folder>"
        ),
        "Linux": (
            "download OpenVSP-3.51.3-Ubuntu-24.04_amd64.deb (64 MB; verified 2026-09-06) "
            "from openvsp.org/download.php; sudo apt-get install ./OpenVSP-*.deb"
        ),
    },
    "pvpython": {
        "Darwin": (
            "download ParaView 6.1.1 (arm64 dmg) from paraview.org/download and set "
            "[windtunnel] pvpython = /Applications/ParaView-6.1.1.app/Contents/bin/pvpython"
        ),
        "Linux": (
            "sudo apt-get install paraview python3-paraview xvfb  "
            "(5.11.2; renders only under xvfb-run - verified 2026-09-06)"
        ),
    },
}


def _install_line(engine: str) -> str:
    return INSTALL[engine].get(platform.system(), INSTALL[engine]["Linux"])


# ---------------------------------------------------------------------------
# OpenFOAM: a route, not a binary
# ---------------------------------------------------------------------------


@dataclass
class FoamInstall:
    kind: str  # "bashrc" | "entry" | "bindir"
    path: str
    version: str = ""
    fork: str = ""
    via: str = ""
    mpirun: str = ""

    def argv(self, app: str, *args: str) -> list[str]:
        if self.kind == "bashrc":
            return ["bash", "-c", 'source "$0" >/dev/null 2>&1; exec "$@"', self.path, app, *args]
        if self.kind == "entry":
            return [self.path, app, *args]
        return [str(Path(self.path) / app), *args]

    def parallel_argv(self, app: str, cores: int, *args: str) -> list[str]:
        """mpirun inside the same environment (the app's own mpirun on the Mac)."""
        inner = f"mpirun -np {cores} {app} -parallel " + " ".join(args)
        if self.kind == "bashrc":
            return [
                "bash",
                "-c",
                'source "$0" >/dev/null 2>&1; exec bash -c "$1"',
                self.path,
                inner,
            ]
        if self.kind == "entry":
            return [self.path, "bash", "-c", inner]
        return ["mpirun", "-np", str(cores), str(Path(self.path) / app), "-parallel", *args]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _foam_route_for(root: Path) -> FoamInstall | None:
    """A directory that is an OpenFOAM project dir (has etc/bashrc), or the
    Mac app's Resources dir (has etc/openfoam)."""
    entry = root / "etc" / "openfoam"
    bashrc = root / "etc" / "bashrc"
    if platform.system() == "Darwin" and entry.is_file():
        return FoamInstall("entry", str(entry))
    if bashrc.is_file():
        return FoamInstall("bashrc", str(bashrc))
    if entry.is_file():
        return FoamInstall("entry", str(entry))
    return None


def _foam_candidates() -> list[Path]:
    if platform.system() == "Darwin":
        apps = sorted(glob.glob("/Applications/OpenFOAM-v*.app/Contents/Resources"), reverse=True)
        return [Path(a) for a in apps]
    # openfoam.com's own packages first (newest first), then the Foundation's,
    # then a source build; Ubuntu's apt `openfoam` (v1912 under
    # /usr/share/openfoam) LAST: measured 2026-09-06, every function object
    # in that build dies with an IOstream "sha1" error, so it can mesh and
    # solve but never report a force.
    roots = sorted(glob.glob("/usr/lib/openfoam/openfoam*"), reverse=True)
    roots += sorted(glob.glob("/opt/openfoam*"), reverse=True)
    roots += sorted(glob.glob(str(Path.home() / "OpenFOAM" / "OpenFOAM-*")), reverse=True)
    roots.append("/usr/share/openfoam")
    return [Path(r) for r in roots]


def find_openfoam(cfg: dict[str, Any], *, probe_version: bool = True) -> FoamInstall:
    configured = str(cfg.get("openfoam") or "")
    if configured:
        p = Path(configured).expanduser()
        route: FoamInstall | None = None
        if p.is_file() and p.name == "bashrc":
            route = FoamInstall("bashrc", str(p))
        elif p.is_file() and p.name == "openfoam":
            route = FoamInstall("entry", str(p))
        elif p.is_dir():
            route = _foam_route_for(p)
            if route is None and (p / "simpleFoam").is_file():
                route = FoamInstall("bindir", str(p))
        if route is None:
            raise TeeError(
                "wt_bad_config",
                f"[windtunnel] openfoam = {configured} is not an OpenFOAM install "
                "(expected a project dir with etc/bashrc, the app's etc/openfoam entry "
                "script, or a bin dir).",
                fix="Fix the path or remove the key to search the known locations.",
            )
        route.via = "config"
    else:
        route = None
        for root in _foam_candidates():
            route = _foam_route_for(root)
            if route is not None:
                route.via = "default"
                break
        if route is None:
            exe = shutil.which("simpleFoam")
            if exe:
                route = FoamInstall("bindir", str(Path(exe).parent), via="PATH")
    if route is None:
        raise TeeError(
            "wt_openfoam_missing",
            "No OpenFOAM install found (looked for etc/bashrc under the known locations "
            "and simpleFoam on PATH).",
            fix=_install_line("openfoam"),
        )
    if probe_version:
        _probe_foam_version(route)
    return route


def _probe_foam_version(route: FoamInstall) -> None:
    from tee.windtunnel.foam import fork_of

    try:
        if route.kind == "bindir":
            route.version, route.fork = "unknown", "unknown"
        else:
            out = subprocess.run(
                route.argv("bash", "-c", "echo $WM_PROJECT_VERSION; command -v mpirun"),
                capture_output=True,
                text=True,
                timeout=30,
            )
            lines = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
            route.version = lines[0] if lines else "unknown"
            route.fork = fork_of(route.version)[0]
            route.mpirun = lines[1] if len(lines) > 1 else ""
    except (OSError, subprocess.SubprocessError):
        route.version, route.fork = "unknown", "unknown"


# ---------------------------------------------------------------------------
# Plain binaries
# ---------------------------------------------------------------------------


@dataclass
class Binary:
    name: str
    path: str
    version: str = ""
    via: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"found": True, **asdict(self)}


def _binary(
    cfg: dict[str, Any], key: str, exe: str, defaults: list[str], install_fix: str
) -> Binary:
    """Explicit config -> known locations -> PATH; a wrong explicit path refuses."""
    configured = str(cfg.get(key) or "")
    if configured:
        p = Path(configured).expanduser()
        if p.is_dir():
            p = p / exe
        if p.is_file():
            return Binary(exe, str(p), via="config")
        raise TeeError(
            "wt_bad_config",
            f"[windtunnel] {key} = {configured} does not contain {exe}.",
            fix="Fix the path or remove the key to use the known locations / PATH.",
        )
    for cand in defaults:
        for path in sorted(glob.glob(cand), reverse=True):
            if Path(path).is_file():
                return Binary(exe, path, via="default")
    found = shutil.which(exe)
    if found:
        return Binary(exe, found, via="PATH")
    raise TeeError(
        f"wt_{key}_missing", f"No {exe} found (known locations and PATH).", fix=install_fix
    )


def find_su2(cfg: dict[str, Any], *, probe_version: bool = True) -> Binary:
    home = str(Path.home())
    defaults = [
        f"{home}/SU2/bin/SU2_CFD",
        "/opt/SU2/bin/SU2_CFD",
        f"{home}/Applications/SU2*/bin/SU2_CFD",
    ]
    run = os.environ.get("SU2_RUN")
    if run:
        defaults.insert(0, str(Path(run) / "SU2_CFD"))
    b = _binary(cfg, "su2", "SU2_CFD", defaults, _install_line("su2"))
    if probe_version:
        b.version = _version_of([b.path, "-h"], r"v?(\d+\.\d+\.\d+)")
        if b.version == "unknown":
            b.version = _version_of([b.path, "--version"], r"v?(\d+\.\d+\.\d+)")
    b.extra["bin_dir"] = str(Path(b.path).parent)
    return b


def find_openvsp(cfg: dict[str, Any], *, probe_version: bool = True) -> Binary:
    defaults = [
        "/opt/OpenVSP/vspscript",
        "/usr/local/bin/vspscript",
        "/Applications/OpenVSP*/vspscript",
        str(Path.home() / "OpenVSP*" / "vspscript"),
    ]
    b = _binary(cfg, "openvsp", "vspscript", defaults, _install_line("openvsp"))
    folder = Path(b.path).parent
    aero = folder / "vspaero"
    if not aero.is_file():
        which = shutil.which("vspaero")
        aero = Path(which) if which else aero
    b.extra["vspaero"] = str(aero) if aero.is_file() else ""
    if probe_version:
        b.version = _version_of([b.path, "-help"], r"Vehicle Sketch Pad\s+(\d+\.\d+\.\d+)")
        if b.extra["vspaero"]:
            b.extra["vspaero_version"] = _version_of(
                [b.extra["vspaero"]], r"VSPAERO v\.?(\d+\.\d+\.\d+)"
            )
    return b


def find_pvpython(cfg: dict[str, Any], *, probe_version: bool = True) -> Binary:
    defaults = [
        "/Applications/ParaView-*.app/Contents/bin/pvpython",
        "/opt/paraview*/bin/pvpython",
        "/usr/bin/pvpython",
    ]
    b = _binary(cfg, "pvpython", "pvpython", defaults, _install_line("pvpython"))
    if probe_version:
        b.version = _version_of([b.path, "--version"], r"paraview version\s+(\d+\.\d+\.\d+)")
    b.extra["xvfb"] = shutil.which("xvfb-run") or ""
    b.extra["display"] = bool(os.environ.get("DISPLAY")) or platform.system() == "Darwin"
    return b


def _version_of(argv: list[str], pattern: str, timeout: float = 20.0) -> str:
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        text = out.stdout + out.stderr
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    m = re.search(pattern, text)
    return m.group(1) if m else "unknown"


# ---------------------------------------------------------------------------
# The probe wt_probe and the doctor share
# ---------------------------------------------------------------------------

ENGINE_FINDERS = {
    "openfoam": find_openfoam,
    "su2": find_su2,
    "vspaero": find_openvsp,
    "pvpython": find_pvpython,
}


def probe(cfg: dict[str, Any]) -> dict[str, Any]:
    """Every engine: found or the refusal that names its install. Never runs
    a solve; version probes only."""
    engines: dict[str, Any] = {}
    for name, finder in ENGINE_FINDERS.items():
        try:
            found = finder(cfg)
            engines[name] = (
                found.to_dict() if isinstance(found, Binary) else {"found": True, **found.to_dict()}
            )
        except TeeError as exc:
            engines[name] = {"found": False, "error": exc.code, "fix": exc.fix}
    try:
        import importlib.util

        meshio_ok = importlib.util.find_spec("meshio") is not None
    except (ImportError, ValueError):
        meshio_ok = False
    return {
        "platform": platform.system(),
        "cores": os.cpu_count() or 1,
        "engines": engines,
        "extra": {"meshio": meshio_ok},
        "probed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
