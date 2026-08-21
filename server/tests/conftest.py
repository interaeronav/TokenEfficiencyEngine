"""Shared fixtures. The `blender_bridge` fixture launches a real headless
Blender running the official Blender Lab MCP add-on's background server, so
dcc-marked tests exercise the exact production wire path. Skipped when the
Blender binary or the add-on checkout is absent."""

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


def find_blender() -> str | None:
    for candidate in BLENDER_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def blender_bridge(tmp_path_factory):
    """(port, process) for a live headless Blender bridge, official add-on."""
    blender = find_blender()
    if blender is None:
        pytest.skip("no Blender binary (set TEE_BLENDER)")
    if not Path(ADDON_DIR, "blender_mcp_addon").exists():
        pytest.skip(f"official blender_mcp add-on not found at {ADDON_DIR}")

    port = free_port()
    boot = tmp_path_factory.mktemp("bridge") / "boot.py"
    boot.write_text(
        textwrap.dedent(
            f"""
            import sys
            sys.path.insert(0, {ADDON_DIR!r})
            from blender_mcp_addon import cli
            sys.exit(cli.cli_execute(["--port", "{port}"]))
            """
        )
    )
    proc = subprocess.Popen(
        [blender, "--background", "--factory-startup", "--python", str(boot)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # wait for the socket
    from tee.adapters.blender.wire import BlenderWire

    wire = BlenderWire(port=port)
    deadline = time.time() + 60
    while time.time() < deadline:
        if proc.poll() is not None:
            pytest.fail(f"Blender exited early with rc={proc.returncode}")
        if wire.probe():
            break
        time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("Blender bridge never came up within 60s")

    yield port

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
