"""DCC-free tests for the TEE bridge server module (protocol layer only -
the module imports bpy solely inside its GUI entry points)."""

import importlib.util
import json
import sys
import threading
from pathlib import Path

import pytest

from tee.adapters.blender.wire import BlenderWire

BRIDGE = Path(__file__).resolve().parents[2] / "adapters" / "blender" / "tee_bridge"


@pytest.fixture(scope="module")
def bridge_server():
    spec = importlib.util.spec_from_file_location("tee_bridge_server", BRIDGE / "bridge_server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def frame(module, request: dict) -> dict:
    raw = module.execute_frame(json.dumps(request).encode())
    assert raw.endswith(b"\0")
    return json.loads(raw[:-1])


def test_execute_ok_and_result_contract(bridge_server):
    out = frame(
        bridge_server,
        {"type": "execute", "code": "result = {'x': 1 + 1}", "strict_json": True},
    )
    assert out == {"status": "ok", "result": {"x": 2}}


def test_stdout_captured(bridge_server):
    out = frame(
        bridge_server,
        {"type": "execute", "code": "print('hello')\nresult = {}", "strict_json": True},
    )
    assert out["stdout"] == "hello\n"


def test_error_returns_traceback(bridge_server):
    out = frame(
        bridge_server,
        {"type": "execute", "code": "raise RuntimeError('nope')", "strict_json": True},
    )
    assert out["status"] == "error"
    assert "RuntimeError: nope" in out["message"]


def test_non_dict_result_rejected(bridge_server):
    out = frame(bridge_server, {"type": "execute", "code": "result = 42", "strict_json": True})
    assert out["status"] == "error"
    assert "must be a dict" in out["message"]


def test_strict_json_rejects_unserializable(bridge_server):
    out = frame(
        bridge_server,
        {"type": "execute", "code": "result = {'f': object()}", "strict_json": True},
    )
    assert out["status"] == "error"
    assert "not JSON-serializable" in out["message"]


def test_lenient_mode_reprs_unserializable(bridge_server):
    out = frame(
        bridge_server,
        {"type": "execute", "code": "result = {'f': object()}", "strict_json": False},
    )
    assert out["status"] == "ok"
    assert "object object" in out["result"]["f"]


def test_denylist_blocks_dangerous_calls(bridge_server):
    for code in ("import bpy\nbpy.ops.wm.quit_blender()", "import sys\nsys.exit(1)"):
        out = frame(bridge_server, {"type": "execute", "code": code, "strict_json": True})
        assert out["status"] == "error"
        assert "blocked" in out["message"]


def test_bad_json_and_bad_type_are_errors(bridge_server):
    raw = bridge_server.execute_frame(b"{broken")
    assert json.loads(raw[:-1])["status"] == "error"
    out = frame(bridge_server, {"type": "banana", "code": "", "strict_json": True})
    assert out["status"] == "error"


def test_io_loop_end_to_end_with_wire_client(bridge_server):
    """Full socket path: TEE wire client against the bridge's I/O loop."""
    loop = bridge_server._IOLoop(
        "127.0.0.1",
        0,
        lambda sock, data: bridge_server._send_response(sock, bridge_server.execute_frame(data)),
    )
    thread = threading.Thread(target=loop.run, daemon=True)
    thread.start()
    try:
        wire = BlenderWire(port=loop.port, connect_timeout=2.0, call_timeout=5.0)
        out = wire.execute("result = {'n': sum(range(10))}")
        assert out == {"status": "ok", "result": {"n": 45}}
        assert wire.probe() is True
    finally:
        loop.close()
        thread.join(timeout=5)
