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

# Hermetic machine capacity: the suite must behave identically on the
# 128 GB M5, a 7 GB CI runner, or anything else. Tests that need a
# SPECIFIC machine construct MachineLedger(total_gb=...) directly and
# are unaffected by this default. (The A42 close shipped with CI red
# for three pushes because app-built tests read the runner's real RAM
# and admission refused the reconstruct lanes - 2026-08-29.)
os.environ.setdefault("TEE_MACHINE_TOTAL_GB", "128")

BLENDER_CANDIDATES = (
    os.environ.get("TEE_BLENDER"),
    shutil.which("blender"),
    "/home/user/blender-5.2.0-linux-x64/blender",
)
TEE_BRIDGE_DIR = Path(__file__).resolve().parents[2] / "adapters" / "blender" / "tee_bridge"

# The official Blender Lab MCP add-on appears in two shapes: a source checkout
# (a `blender_mcp_addon` package inside some directory) and an *installed*
# extension (the package directory itself, named `mcp`, under Blender's
# extensions dir). The cloud container only ever saw the first; the physical
# machine only has the second, and hardcoding the checkout layout silently
# skipped half the live matrix there. Discover both.
_ADDON_ENV = os.environ.get("TEE_BLENDER_MCP_ADDON")
_EXTENSION_GLOBS = (
    "~/Library/Application Support/Blender/*/extensions/*/mcp",  # macOS
    "~/.config/blender/*/extensions/*/mcp",  # Linux
    "~/AppData/Roaming/Blender Foundation/Blender/*/extensions/*/mcp",  # Windows
)


def find_official_addon() -> tuple[str, str] | None:
    """Return (sys.path entry, package name) for the official add-on, or None."""
    if _ADDON_ENV:
        # An explicit override is authoritative: if it is wrong the operator
        # must hear about it, not silently get some other install.
        candidates = [Path(_ADDON_ENV).expanduser()]
    else:
        candidates = [Path("/home/user/blender_mcp_official/addon")]
        for pattern in _EXTENSION_GLOBS:
            expanded = Path(pattern).expanduser()
            anchor = Path(expanded.parts[0]).joinpath()
            candidates.extend(sorted(anchor.glob(str(Path(*expanded.parts[1:])))))
    for candidate in candidates:
        if (candidate / "blender_mcp_addon" / "cli.py").exists():
            return str(candidate), "blender_mcp_addon"  # checkout layout
        if (candidate / "cli.py").exists():
            return str(candidate.parent), candidate.name  # installed extension
    return None


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
    located = find_official_addon()
    assert located is not None  # guarded by the fixture's skip
    path_entry, package = located
    return textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, {path_entry!r})
        from {package} import cli
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
    if request.param == "official" and find_official_addon() is None:
        pytest.skip("official blender_mcp add-on not found (set TEE_BLENDER_MCP_ADDON)")

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


# -- network fixture (Phase 9) -----------------------------------------------


@pytest.fixture(scope="session")
def network():
    """Skip network-marked tests cleanly when offline (acceptance 9.7)."""
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(
            "https://api.polyhaven.com/types", headers={"User-Agent": "TEE-test/0.1"}
        )
        with urllib.request.urlopen(req, timeout=8):
            pass
    except (urllib.error.URLError, TimeoutError, OSError):
        pytest.skip("no outbound network access")
    return True


# -- shared stub bridge (official wire protocol shape) -----------------------

import json as _json  # noqa: E402
import threading as _threading  # noqa: E402


class StubBridge:
    """Minimal null-delimited JSON execute server (official protocol shape)."""

    def __init__(self, responder):
        self.responder = responder
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(2)
        self.thread = _threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            with conn:
                buf = b""
                while not buf.endswith(b"\0"):
                    chunk = conn.recv(65536)
                    if not chunk:
                        break
                    buf += chunk
                if not buf.endswith(b"\0"):
                    continue
                request = _json.loads(buf[:-1])
                reply = self.responder(request)
                if reply is not None:
                    conn.sendall(reply)

    def close(self):
        self.sock.close()


@pytest.fixture(autouse=True)
def _fresh_turn():
    """Each test starts as a fresh, untrusted turn (A43 L2).

    In the server, `_tool` mints the caller class and resets taint per MCP
    call; in-process tests share one thread context, so without this the
    taint one test earns bleeds into the next. The default here is the SAFE
    class - a test that needs live-turn authority says so explicitly."""
    from tee.kernel import trustctx

    caller_token = trustctx.CALLER.set("content-derived")
    taint_token = trustctx.TAINT.set(())
    yield
    trustctx.CALLER.reset(caller_token)
    trustctx.TAINT.reset(taint_token)
    trustctx.clear_for_tests()
