"""`tee doctor`: environment diagnostics with one-line fixes (Phase 4).

Setup friction dominates the issue trackers of every surveyed bridge, so
every failed check names its exact fix. Checks are pure functions returning
Check records; the CLI renders them (or JSON with --json) and exits non-zero
only when a REQUIRED check fails - absent DCCs are warnings, not errors,
because TEE serves single-DCC setups too.
"""

from __future__ import annotations

import json
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tee import __version__

BLENDER_COMMON_PATHS = (
    "/home/user/blender-5.2.0-linux-x64/blender",
    "/usr/bin/blender",
    "/snap/bin/blender",
    "/Applications/Blender.app/Contents/MacOS/Blender",
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe",
)
UNREAL_COMMON_PATHS = (
    "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe",
    "/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor",
)
EPIC_MCP_PORT = 8000
BRIDGE_PORT = 9876


@dataclass
class Check:
    name: str
    status: str  # ok | warn | fail
    detail: str
    fix: str | None = None
    required: bool = False

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }
        if self.fix:
            payload["fix"] = self.fix
        return payload


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_python() -> Check:
    # requires-python >=3.11 already gates installation; this reports what runs
    version = platform.python_version()
    return Check("python", "ok", f"{version} on {platform.system().lower()}", required=True)


def check_uv() -> Check:
    path = shutil.which("uv")
    if path:
        return Check("uv", "ok", path)
    return Check(
        "uv",
        "warn",
        "not on PATH",
        fix="Install uv: https://docs.astral.sh/uv/ (used for envs and the bpy batch backend).",
    )


def find_blender(env: dict[str, str] | None = None) -> str | None:
    import os

    env = env if env is not None else dict(os.environ)
    candidates = [env.get("TEE_BLENDER"), shutil.which("blender"), *BLENDER_COMMON_PATHS]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def check_blender_binary() -> Check:
    binary = find_blender()
    if binary is None:
        return Check(
            "blender",
            "warn",
            "no Blender binary found",
            fix="Install Blender 5.2 LTS (or set TEE_BLENDER=/path/to/blender).",
        )
    try:
        out = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
        first = out.stdout.splitlines()[0] if out.stdout else "unknown version"
    except (subprocess.TimeoutExpired, OSError) as exc:
        return Check(
            "blender",
            "fail",
            f"{binary} did not answer --version ({type(exc).__name__})",
            fix="Reinstall Blender or fix the TEE_BLENDER path.",
        )
    version = first.replace("Blender ", "").split()[0] if "Blender" in first else ""
    if version and tuple(int(x) for x in version.split(".")[:2]) < (5, 1):
        return Check(
            "blender",
            "warn",
            f"{first} at {binary}",
            fix="TEE's baseline is Blender 5.1+ (5.2 LTS primary); older versions "
            "are unsupported by the official MCP add-on.",
        )
    return Check("blender", "ok", f"{first} at {binary}")


def check_blender_bridge(port: int = BRIDGE_PORT) -> Check:
    if not _port_open("127.0.0.1", port):
        return Check(
            "blender-bridge",
            "warn",
            f"nothing listening on 127.0.0.1:{port}",
            fix=(
                "Start Blender with the official MCP add-on enabled, or run "
                "headless: blender --background --python "
                "adapters/blender/tee_bridge/boot_background.py -- --port "
                f"{port}"
            ),
        )
    from tee.adapters.blender.wire import BlenderWire

    wire = BlenderWire(port=port)
    try:
        response = wire.execute(
            "import bpy\nresult = {'v': bpy.app.version_string, 'bg': bpy.app.background}",
            timeout=10.0,
        )
    except Exception as exc:
        return Check(
            "blender-bridge",
            "fail",
            f"port {port} is open but not speaking the bridge protocol ({exc})",
            fix="Another program may hold the port; change it in the add-on "
            "preferences and pass --blender-port to tee serve.",
        )
    if response.get("status") != "ok":
        return Check(
            "blender-bridge",
            "fail",
            f"bridge answered with an error: {str(response)[:120]}",
            fix="Restart the bridge add-on inside Blender.",
        )
    result = response.get("result", {})
    mode = "background" if result.get("bg") else "GUI"
    return Check("blender-bridge", "ok", f"Blender {result.get('v')} ({mode}) on :{port}")


def check_bpy_wheel_abi() -> Check:
    minor = sys.version_info.minor
    if minor == 11:
        match = "bpy 4.2-5.0 wheels (cp311)"
    elif minor == 13:
        match = "bpy 5.1+ wheels (cp313)"
    else:
        return Check(
            "bpy-wheel",
            "warn",
            f"python 3.{minor} matches NO bpy wheel",
            fix="The pip bpy batch backend needs exactly 3.11 (bpy<=5.0) or "
            "3.13 (bpy>=5.1); use `uv venv --python 3.13` for that backend. "
            "The live-bridge path is unaffected.",
        )
    return Check("bpy-wheel", "ok", f"python 3.{minor} matches {match}")


def find_unreal() -> str | None:
    for name in ("UnrealEditor", "UnrealEditor-Cmd"):
        path = shutil.which(name)
        if path:
            return path
    for candidate in UNREAL_COMMON_PATHS:
        if Path(candidate).exists():
            return candidate
    return None


def check_unreal() -> Check:
    binary = find_unreal()
    epic_mcp = _port_open("127.0.0.1", EPIC_MCP_PORT)
    if binary is None and not epic_mcp:
        return Check(
            "unreal",
            "warn",
            "no Unreal Editor found and no MCP server on :8000",
            fix="For UE 5.8+: enable the ModelContextProtocol + AllToolsets "
            "plugins and set bAutoStartServer=True (Phase 3 docs).",
        )
    if epic_mcp:
        # A listening port is not proof the endpoint is Unreal's, so do the
        # handshake and count the catalog - the same probe the adapter runs.
        try:
            from tee.adapters.unreal.catalog import ToolsetCatalog
            from tee.adapters.unreal.wire import UnrealWire

            wire = UnrealWire(port=EPIC_MCP_PORT, connect_timeout=3.0, call_timeout=30.0)
            wire.connect()
            catalog = ToolsetCatalog(wire)
            toolsets = catalog.load_toolsets()
        except Exception as exc:  # any failure is one actionable line
            return Check(
                "unreal",
                "warn",
                f"something is listening on :{EPIC_MCP_PORT} but it did not "
                f"answer as Unreal's MCP server ({type(exc).__name__})",
                fix="A just-launched editor needs ~2-3 minutes before MCP "
                "dispatches - retry first. If it persists: check nothing "
                "else holds that port (CrashReportClient is known to squat "
                "it) and that the ModelContextProtocol plugin is enabled "
                "in the open project.",
            )
        if not toolsets:
            return Check(
                "unreal",
                "warn",
                "Unreal MCP answered but advertises no toolsets",
                fix="Enable the AllToolsets plugin in the project (it is off "
                "by default) and restart the editor.",
            )
        extra = " + TEE toolset" if "TeeEditorTools" in toolsets else ""
        return Check(
            "unreal",
            "ok",
            f"MCP on 127.0.0.1:{EPIC_MCP_PORT}, {len(toolsets)} toolsets{extra}",
        )
    return Check(
        "unreal",
        "warn",
        f"editor found ({binary}) but no MCP server on :{EPIC_MCP_PORT}",
        fix="Open the project with the ModelContextProtocol plugin enabled, "
        "or add -ModelContextProtocolStartServer to the launch args.",
    )


def check_voxkiln() -> Check:
    """Local 3D generation (Phase 13). Reports the gated-weights state too:
    having the 15 GB of TRELLIS weights cached is NOT sufficient, because the
    image-conditioning tower is gated and approved manually."""
    try:
        import voxkiln
        from voxkiln.engine import doctor as voxkiln_doctor
    except ImportError:
        return Check(
            "voxkiln",
            "warn",
            "not installed - local image-to-3D unavailable",
            fix="pip install 'voxkiln[model]' (see docs/setup-voxkiln.md); "
            "hosted Tripo/Meshy stay available with keys",
        )
    report = voxkiln_doctor()
    backend = (report.get("probe") or {}).get("backend")
    if backend is None:
        return Check(
            "voxkiln",
            "warn",
            f"{voxkiln.__version__} installed but no CUDA/MPS backend",
            fix=(report.get("probe") or {}).get("fix", "needs Apple Silicon or CUDA"),
        )
    gated = report.get("gated_weights") or {}
    weights = report.get("weights_cached_gb")
    if gated.get("accessible") is False:
        return Check(
            "voxkiln",
            "warn",
            f"{voxkiln.__version__} on {backend}, weights {weights} GB, but the "
            f"gated image model is not accessible ({gated.get('reason')})",
            fix=gated.get("fix", ""),
        )
    if not weights:
        return Check(
            "voxkiln",
            "warn",
            f"{voxkiln.__version__} on {backend} but no weights cached",
            fix="run `voxkiln fetch-weights` (~16 GB, once)",
        )
    return Check(
        "voxkiln",
        "ok",
        f"{voxkiln.__version__} on {backend}, weights {weights} GB, gated model OK",
    )


def check_partkiln() -> Check:
    """The mechanical CAD lane (A66). Two routes reach the kernel and they
    fail differently, so the check names BOTH interpreters: the server's own
    (a dev checkout with OCP already in it) and the sidecar venv under
    `~/TEE/.tee/sidecars/partkiln`, which is the production route precisely
    because it survives an extension upgrade and `tee_purge`. Reporting only
    "installed" would hide the case this lane exists for - the extension
    runtime is Python 3.13 with no OCP, so an in-process yes there is a no."""
    import subprocess
    import sys
    from importlib.util import find_spec

    from tee.adapters.partkiln.adapter import INSTALL_HINT, SIDECAR_INSTALL
    from tee.adapters.partkiln.wire import SIDECAR_PY

    here = f"server python {sys.version.split()[0]}"
    try:
        kernel_here = find_spec("partkiln") is not None
        ocp_here = find_spec("OCP") is not None
    except (ImportError, ValueError):
        kernel_here = ocp_here = False

    # The kernel version the lane will actually run. `occt_version()` reads the
    # carrier wheel's metadata, so naming it here costs no `import OCP` - which
    # is 26 s on a cold venv and must never be paid by a diagnostic (Law 17).
    occt_here = None
    if kernel_here:
        try:
            from partkiln.client import occt_version

            occt_here = occt_version()
        except ImportError:  # a half-installed kernel is a warn, not a crash
            kernel_here = False

    sidecar = ""
    if SIDECAR_PY.is_file():
        try:
            probe = subprocess.run(
                [
                    str(SIDECAR_PY),
                    "-c",
                    "import platform,importlib.util as u;"
                    "from importlib.metadata import packages_distributions,version;"
                    "d=(packages_distributions().get('OCP') or [None])[0];"
                    "print(platform.python_version(),"
                    "u.find_spec('partkiln') is not None,"
                    "u.find_spec('OCP') is not None,"
                    "'.'.join(version(d).split('.')[:3]) if d else '?')",
                ],
                capture_output=True,
                text=True,
                timeout=20,
            )
            sidecar = probe.stdout.strip() or probe.stderr.strip()[:80]
        except (OSError, subprocess.SubprocessError) as exc:
            sidecar = f"unreadable ({type(exc).__name__})"

    fields = sidecar.split()
    sidecar_ok = fields[1:3] == ["True", "True"] if sidecar else False
    if sidecar_ok:
        sidecar_occt = fields[3] if len(fields) > 3 else "?"
        return Check(
            "partkiln",
            "ok",
            f"mode sidecar - {SIDECAR_PY} python {fields[0]} with OCCT {sidecar_occt}; {here}"
            + (f", kernel + OCCT {occt_here or '?'} here too" if kernel_here and ocp_here else ""),
        )
    if kernel_here and ocp_here:
        return Check(
            "partkiln",
            "ok",
            f"mode in-process - kernel and OCCT {occt_here or '?'} importable in the {here}"
            + (f"; sidecar present but incomplete ({sidecar})" if sidecar else "; no sidecar venv"),
            fix="The sidecar venv is the production route (it survives an .mcpb upgrade "
            f"and tee_purge, which wipe an editable install): {SIDECAR_INSTALL}",
        )
    detail = f"kernel absent - {here}, partkiln {kernel_here}, OCP {ocp_here}"
    if sidecar:
        detail += f"; sidecar {SIDECAR_PY} reports {sidecar}"
    return Check("partkiln", "warn", detail + " - mechanical CAD unavailable", fix=INSTALL_HINT)


def check_kb() -> Check:
    """Expert Knowledge Base corpus: root resolvable, manifest readable,
    drift count. Inactive is a plain state, not a failure."""
    from tee.config import ProjectConfig
    from tee.kb.index import KbIndex, resolve_root

    config = ProjectConfig.load(".")
    root = resolve_root(".", config.kb.get("root"))
    if root is None:
        return Check(
            "kb",
            "ok",
            "inactive (no corpus configured or discoverable)",
            fix="set [kb] root in .tee/config.toml to activate kb_* tools",
        )
    try:
        index = KbIndex(root, ".")
        data = index.load()
        drift = data.get("drift", {})
        totals = data.get("totals", {})
        detail = (
            f"{totals.get('files', '?')} files / {totals.get('domains', '?')} domains at {root}"
        )
        if drift.get("stale"):
            n = drift.get("missing_count", 0) + drift.get("changed_count", 0)
            return Check(
                "kb",
                "warn",
                f"{detail}; {n} file(s) drifted from the manifest",
                fix="run the corpus's 00_meta/rebuild.py to regenerate manifest.json",
            )
        return Check("kb", "ok", detail)
    except Exception as exc:
        return Check(
            "kb",
            "warn",
            f"corpus at {root} unusable: {exc}",
            fix="point [kb] root at the folder holding manifest.json",
        )


def check_web() -> Check:
    """Web lane: config posture + cache state. Offline-safe - no fetch."""
    from pathlib import Path as _Path

    from tee.config import ProjectConfig

    web = ProjectConfig.load(".").web
    cache = _Path(".") / ".tee" / "web" / "cache"
    cached = len(list(cache.glob("*.body"))) if cache.is_dir() else 0
    bits = [f"{cached} cached page(s)"]
    if web.get("allow_local"):
        bits.append("allow_local=TRUE - private addresses reachable")
    if web.get("ports"):
        bits.append(f"ports={web['ports']}")
    if web.get("search"):
        bits.append(f"search backend: {web['search']}")
    return Check("web", "ok", "tee_web_lookup ready; " + "; ".join(bits))


def check_rooted(project_root: Any = None) -> Check:
    """First contact: is this session rooted where its grants are?

    A47 P0.5. `serve --project` defaults to the launching client's cwd, so
    a terminal host that omits it boots from an ungranted root, keeps the
    read tiers, and loses every mutation tier. That reads as "TEE denies
    everything" when it is really "TEE is standing in the wrong room".
    Reporting only - never grants.
    """
    from pathlib import Path as _Path

    from tee.app import TeeApp

    root = _Path(project_root) if project_root else _Path.cwd()
    try:
        rooted = TeeApp({}, project_root=root).status()["rooted_at"]
    except Exception as exc:  # a diagnostic must not be the thing that breaks
        return Check(name="project root", status="warn", detail=f"unreadable: {exc}"[:120])
    denied = rooted.get("denied_tiers") or []
    if not rooted.get("granted"):
        return Check(
            name="project root",
            status="warn",
            detail=f"{rooted['project_root']} has no grants ({rooted['grants_file']}); "
            f"reads work, {len(denied)} mutation tier(s) denied: {', '.join(denied)}",
            fix=rooted.get("fix"),
        )
    return Check(
        name="project root",
        status="ok",
        detail=f"{rooted['project_root']} grants {', '.join(rooted['granted'])}"
        + (f"; still denied: {', '.join(denied)}" if denied else ""),
    )


def check_senses() -> Check:
    """What this machine can see and hear, and with what.

    A47 P0. A host model that lacks a sense cannot discover whether TEE can
    lend it one by trying and failing - the providers are services, not
    imports, so absence looks identical to misconfiguration. State it.
    """
    from tee.kernel import local_vlm
    from tee.kernel.machine import ENGINES

    rows = []
    vision_up = local_vlm.available(timeout=1.5)
    qvl = ENGINES.get("qvl", {})
    rows.append(
        f"vision {'UP' if vision_up else 'down'} "
        f"({qvl.get('profile', '?')}, {qvl.get('footprint_gb', '?')} GB, "
        f"{qvl.get('cost', {}).get('latency_s', ['?'])[-1]}s measured)"
    )
    try:
        from importlib.util import find_spec

        audio_up = find_spec("faster_whisper") is not None
    except (ImportError, ValueError):
        audio_up = False
    wh = ENGINES.get("whisper", {})
    rows.append(
        f"audio {'UP' if audio_up else 'down'} "
        f"(faster-whisper, {wh.get('footprint_gb', '?')} GB, "
        f"{wh.get('cost', {}).get('latency_s', ['?'])[0]}s measured)"
    )
    # The cost that is invisible today and must not stay invisible.
    evicts = qvl.get("evicts") or []
    if vision_up and evicts:
        rows.append(
            f"vision evicts {', '.join(evicts)} "
            f"(~{qvl.get('cost', {}).get('swap_s', '?')}s reload on the next text turn)"
        )
    both = vision_up and audio_up
    return Check(
        name="senses",
        status="ok" if both else "warn",
        detail="; ".join(rows),
        fix=None
        if both
        else (
            "vision: point [senses] vision_url at any OpenAI-style "
            "endpoint serving a vision model (or set TEE_LOCAL_VLM_URL). "
            "audio: uv pip install 'tee-engine[extract]'."
        ),
    )


def check_extras(project_root: Any = None) -> Check:
    """Did an upgrade quietly delete the optional extras?

    Installing a bundle rebuilds the venv from its lock and drops anything
    added on top; the fleet extras live on top by design. This is where
    someone looks when a tool says "not installed" and they know they
    installed it.
    """
    from pathlib import Path as _Path

    from tee.kernel import extras as _extras

    state = _Path(project_root or _Path.home() / "TEE") / ".tee"
    gone = _extras.lost(state)
    here = sorted(_extras.present())
    if gone:
        names = ", ".join(f"{g} (last seen {d})" for g, d in sorted(gone.items()))
        return Check(
            name="fleet extras",
            status="warn",
            detail=f"MISSING after an upgrade: {names}. Present: {', '.join(here) or 'none'}.",
            # sys.executable IS the venv that lost them - TEE is running
            # inside it. A placeholder path turns a copy-pasteable command
            # into a puzzle, which is the difference between a fix and a hint.
            fix=f"uv pip install --python '{sys.executable}' "
            + " ".join(f"'tee-engine[{g}]'" for g in sorted(gone)),
        )
    return Check(
        name="fleet extras",
        status="ok",
        detail=f"{len(here)} group(s) installed: {', '.join(here) or 'none'}"
        + " (cad lives in its own sidecar by design)",
    )


def check_state() -> Check:
    """`.tee/` on-disk state (A38 S3.2): sizes per store, the web-cache caps
    in effect, pending kb-staging drafts, project-memory weight. Growth is a
    plain state; only an unbounded-looking pile warns."""
    import tempfile as _tempfile
    from pathlib import Path as _Path

    from tee.config import ProjectConfig

    tee_dir = _Path(".") / ".tee"
    if not tee_dir.is_dir():
        return Check("state", "ok", "no .tee/ yet (nothing stored)")

    def dir_kb(path: _Path) -> int:
        total = 0
        for child in path.rglob("*"):
            try:
                if child.is_file():
                    total += child.stat().st_size
            except OSError:
                continue
        return total // 1024

    sizes = sorted(
        ((dir_kb(child), child.name) for child in tee_dir.iterdir() if child.is_dir()),
        reverse=True,
    )
    total_kb = sum(kb for kb, _ in sizes) + sum(
        f.stat().st_size // 1024 for f in tee_dir.iterdir() if f.is_file()
    )
    web = ProjectConfig.load(".").web
    caps = (
        f"web cache capped {web.get('cache_max_mb', 50)} MB / {web.get('cache_max_age_days', 14)} d"
    )
    staged = len(list((tee_dir / "kb-staging").glob("*.md")))
    orphans = len(list(_Path(_tempfile.gettempdir()).glob("tee-freecad-cp-*")))
    top = ", ".join(f"{name} {kb / 1024:.1f} MB" for kb, name in sizes[:3] if kb)
    detail = f"{total_kb / 1024:.1f} MB in .tee/ ({top or 'empty'}); {caps}"
    if staged:
        detail += f"; {staged} kb-staging draft(s) awaiting owner review"
    if orphans:
        detail += f"; {orphans} freecad checkpoint dir(s) in TMPDIR (OS-purged)"
    if total_kb > 1024 * 1024:
        return Check(
            "state",
            "warn",
            detail,
            fix="lower [web] cache_max_mb / cache_max_age_days in "
            ".tee/config.toml; review kb-staging per docs/setup-kb.md",
        )
    return Check("state", "ok", detail)


def check_llm() -> Check:
    """Local model endpoints (chores + vision): a 1.5 s localhost probe
    each. Down is a plain state - every chore degrades deterministically."""
    from tee.config import ProjectConfig
    from tee.kernel import local_llm, local_vlm

    llm_cfg = ProjectConfig.load(".").llm
    url = str(llm_cfg.get("url") or local_llm.DEFAULT_URL)
    model = str(llm_cfg.get("model") or local_llm.DEFAULT_MODEL)
    llm_up = local_llm.available(url=url, timeout=1.5, model=model)
    vlm_up = local_vlm.available(timeout=1.5)
    detail = (
        f"chores {'UP' if llm_up else 'down'} at {url} ({model}); "
        f"vision {'UP' if vlm_up else 'down'} at {local_vlm.DEFAULT_URL}"
    )
    if llm_up or vlm_up:
        return Check("local models", "ok", detail)
    return Check(
        "local models",
        "ok",
        detail + " - chores degrade to their deterministic paths",
        fix="see docs/setup-local-llm.md to enable chores and captions",
    )


def run_checks(bridge_port: int = BRIDGE_PORT) -> list[Check]:
    return [
        check_python(),
        check_uv(),
        check_blender_binary(),
        check_blender_bridge(bridge_port),
        check_bpy_wheel_abi(),
        check_unreal(),
        check_voxkiln(),
        check_partkiln(),
        check_kb(),
        check_web(),
        check_state(),
        check_extras(),
        check_senses(),
        check_rooted(),
        check_llm(),
    ]


# -- client config emission --------------------------------------------------


def server_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _dev_checkout() -> bool:
    """True when running from the repo (uv sync layout: src/tee under a
    directory holding pyproject.toml); False for an installed wheel."""
    return (server_dir() / "pyproject.toml").exists()


def serve_command(*, adapter: str = "blender", port: int = BRIDGE_PORT) -> list[str]:
    """The command a client config should launch: the installed `tee`
    binary when this is an installed package, the uv-run form for a dev
    checkout."""
    tail = ["serve", "--adapter", adapter]
    if adapter == "blender" and port != BRIDGE_PORT:
        tail += ["--blender-port", str(port)]
    if _dev_checkout():
        return ["uv", "--directory", str(server_dir()), "run", "tee", *tail]
    # a plain `tee` on PATH is usually coreutils tee - only trust a
    # sibling of this interpreter (venv/pipx layout; no resolve(): the
    # venv python is a symlink out of the venv)
    candidate = Path(sys.executable).parent / "tee"
    if candidate.exists():
        return [str(candidate), *tail]
    return ["uvx", "--from", "tee-engine", "tee", *tail]


def emit_config(client: str, *, adapter: str = "blender", port: int = BRIDGE_PORT) -> str:
    command = serve_command(adapter=adapter, port=port)
    entry = {"command": command[0], "args": command[1:]}
    if client == "claude-code":
        return (
            "# add to Claude Code:\n"
            f"claude mcp add tee -- {' '.join(command)}\n"
            "# or in .mcp.json:\n" + json.dumps({"mcpServers": {"tee": entry}}, indent=2)
        )
    if client in ("claude-desktop", "cursor", "qwen-code"):
        where = {
            "claude-desktop": "claude_desktop_config.json",
            "cursor": "~/.cursor/mcp.json",
            "qwen-code": "~/.qwen/settings.json (or .qwen/settings.json for project scope)",
        }[client]
        return f"// add to {where}:\n" + json.dumps({"mcpServers": {"tee": entry}}, indent=2)
    raise ValueError(
        f"unknown client '{client}' (use claude-code, claude-desktop, cursor or qwen-code)"
    )


def render(checks: list[Check]) -> tuple[str, int]:
    lines = [f"tee {__version__} doctor"]
    failed_required = False
    for check in checks:
        mark = {"ok": "OK  ", "warn": "WARN", "fail": "FAIL"}[check.status]
        lines.append(f"{mark} {check.name}: {check.detail}")
        if check.fix:
            lines.append(f"     fix: {check.fix}")
        if check.status == "fail" and check.required:
            failed_required = True
    return "\n".join(lines), (1 if failed_required else 0)
