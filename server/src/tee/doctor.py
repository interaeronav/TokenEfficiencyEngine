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
                fix="Check nothing else holds that port, and that the "
                "ModelContextProtocol plugin is enabled in the open project.",
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


def run_checks(bridge_port: int = BRIDGE_PORT) -> list[Check]:
    return [
        check_python(),
        check_uv(),
        check_blender_binary(),
        check_blender_bridge(bridge_port),
        check_bpy_wheel_abi(),
        check_unreal(),
        check_voxkiln(),
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
