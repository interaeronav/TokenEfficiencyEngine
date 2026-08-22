"""DCC-free tests for the TEE bridge server module (protocol layer only -
the module imports bpy solely inside its GUI entry points)."""

import importlib.util
import json
import socket
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


def test_close_from_another_thread_is_silent_and_frees_the_port(bridge_server):
    """Regression, macOS: tearing the selector down from the caller's thread
    while the I/O thread sits in select() raises OSError(EBADF) out of kqueue
    (Linux epoll tolerates it). stop_gui() runs on Blender's main thread, so
    that path printed a traceback into every user's console on every add-on
    disable. close() must hand teardown to the loop thread instead."""
    caught: list[threading.ExceptHookArgs] = []
    previous_hook = threading.excepthook
    threading.excepthook = caught.append
    try:
        loop = bridge_server._IOLoop("127.0.0.1", 0, lambda sock, data: None)
        port = loop.port
        thread = threading.Thread(target=loop.run, name="tee-bridge-io", daemon=True)
        loop.loop_thread = thread
        thread.start()
        wire = BlenderWire(port=port, connect_timeout=2.0, call_timeout=5.0)
        assert wire.probe() is False  # connects; the null sink never replies
        loop.close()  # <- from the main thread, while the loop is in select()
        thread.join(timeout=5)
        assert not thread.is_alive()
    finally:
        threading.excepthook = previous_hook

    assert caught == [], f"I/O thread raised during shutdown: {caught}"
    assert loop._torn_down.is_set()
    with socket.socket() as probe:  # the listener really is gone
        probe.bind(("127.0.0.1", port))


def test_close_is_idempotent_and_safe_before_the_loop_runs(bridge_server):
    loop = bridge_server._IOLoop("127.0.0.1", 0, lambda sock, data: None)
    loop.close()
    loop.close()
    assert loop._torn_down.is_set()
