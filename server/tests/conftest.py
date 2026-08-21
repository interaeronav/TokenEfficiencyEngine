"""Shared fixtures. The `blender_bridge` fixture launches a real headless
Blender running a bridge server and is parametrized over both protocol
implementations - the official Blender Lab MCP add-on and TEE's own bridge -
so every dcc-marked test proves the adapter works identically against both.
Skipped when the Blender binary (or, for the official flavor, its checkout)
is absent."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import textwrap
import time
from pathlib import Path

import pytest

BLENDER_CANDIDATES = (
    os.environ.get("TEE_BLENDER"),
    shutil.which("blender"),
    "/home/user/blender-5.2.0-linux-x64/blender",
)
ADDON_DIR = os.environ.get("TEE_BLENDER_MCP_ADDON", "/home/user/blender_mcp_official/addon")
TEE_BRIDGE_DIR = Path(__file__).resolve().parents[2] / "adapters" / "blender" / "tee_bridge"


def find_blender() -> str | None:
    for candidate in BLENDER_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _official_boot(port: int) -> str:
    return textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {ADDON_DIR!r})
        from blender_mcp_addon import cli
        sys.exit(cli.cli_execute(["--port", "{port}"]))
        """
    )


def _tee_boot(port: int) -> str:
    return textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {str(TEE_BRIDGE_DIR)!r})
        import bridge_server
        bridge_server.run_blocking("127.0.0.1", {port})
        """
    )


@pytest.fixture(scope="session", params=["official", "tee"])
def blender_bridge(request, tmp_path_factory):
    """Port of a live headless Blender bridge (both protocol flavors)."""
    blender = find_blender()
    if blender is None:
        pytest.skip("no Blender binary (set TEE_BLENDER)")
    if request.param == "official" and not Path(ADDON_DIR, "blender_mcp_addon").exists():
        pytest.skip(f"official blender_mcp add-on not found at {ADDON_DIR}")

    port = free_port()
    boot = tmp_path_factory.mktemp("bridge") / f"boot_{request.param}.py"
    boot.write_text(_official_boot(port) if request.param == "official" else _tee_boot(port))
    proc = subprocess.Popen(
        [blender, "--background", "--factory-startup", "--python", str(boot)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    from tee.adapters.blender.wire import BlenderWire

    wire = BlenderWire(port=port)
    deadline = time.time() + 60
    while time.time() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"Blender ({request.param}) exited early with rc={proc.returncode}")
        if wire.probe():
            break
        time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail(f"Blender bridge ({request.param}) never came up within 60s")

    yield port

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
