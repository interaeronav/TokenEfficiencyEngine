"""Wire client tests against a stub bridge speaking the official protocol."""

import json
import socket
import threading

import pytest

from tee.adapters.blender.wire import BlenderWire
from tee.kernel.errors import TeeError


class StubBridge:
    """Minimal null-delimited JSON execute server (official protocol shape)."""

    def __init__(self, responder):
        self.responder = responder
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(2)
        self.thread = threading.Thread(target=self._serve, daemon=True)
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
                request = json.loads(buf[:-1])
                reply = self.responder(request)
                if reply is not None:
                    conn.sendall(reply)

    def close(self):
        self.sock.close()


def make_bridge(responder):
    bridge = StubBridge(responder)
    wire = BlenderWire(port=bridge.port, connect_timeout=1.0, call_timeout=2.0)
    return bridge, wire


def ok_responder(request):
    assert request["type"] == "execute"
    assert isinstance(request["strict_json"], bool)
    return (json.dumps({"status": "ok", "result": {"echo": len(request["code"])}}) + "\0").encode()


def test_roundtrip_and_request_shape():
    bridge, wire = make_bridge(ok_responder)
    try:
        out = wire.execute("result = {}")
        assert out["status"] == "ok"
        assert out["result"]["echo"] == len("result = {}")
    finally:
        bridge.close()


def test_connection_refused_is_fast_structured_error():
    wire = BlenderWire(port=1, connect_timeout=0.5)  # nothing listens on port 1
    with pytest.raises(TeeError) as err:
        wire.execute("result = {}")
    assert err.value.code == "blender_unreachable"
    assert wire.probe() is False


def test_mid_response_disconnect():
    def cut(request):
        return None  # close without answering

    bridge, wire = make_bridge(cut)
    try:
        with pytest.raises(TeeError) as err:
            wire.execute("result = {}")
        assert err.value.code == "blender_disconnected"
    finally:
        bridge.close()


def test_garbage_frame_is_structured_error():
    bridge, wire = make_bridge(lambda r: b"not json at all\0")
    try:
        with pytest.raises(TeeError) as err:
            wire.execute("result = {}")
        assert err.value.code == "blender_bad_response"
    finally:
        bridge.close()


def test_chunked_frame_reassembly():
    payload = (json.dumps({"status": "ok", "result": {"x": "y" * 200_000}}) + "\0").encode()

    def chunked(request):
        return payload  # sendall may fragment; client must reassemble to the \0

    bridge, wire = make_bridge(chunked)
    try:
        out = wire.execute("result = {}")
        assert len(out["result"]["x"]) == 200_000
    finally:
        bridge.close()
