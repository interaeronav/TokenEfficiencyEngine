"""A71 - the second Fusion transport, without Fusion.

The owner's Mac runs the FusionMcpBridge add-in (`adapters/fusion/tee_bridge/
FusionMcpBridge/`, HTTP on 127.0.0.1:8766), not the TEE add-in. Its contract
differs from the TEE bridge's in two ways the lane must survive: every job
runs in a FRESH namespace (`{"adsk": adsk, "result": None}`), and HTTP 504
means the primary thread is still working. These tests stand up that exact
protocol over real HTTP on an ephemeral port, execute the lane's own programs
against the hermetic shim with a new namespace per request, and hold the
wire, the auto wire and the adapter to their refusals.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fixtures_fusion import Application, Design, _modules

from tee.adapters.fusion import codegen
from tee.adapters.fusion.adapter import FusionAdapter
from tee.adapters.fusion.wire import (
    STATE_PRELUDE,
    FusionAutoWire,
    FusionHttpWire,
)
from tee.app import TeeApp
from tee.kernel.errors import TeeError

HANG = "# __hang__"  # a job the fake primary thread never finishes


def _safe(value):
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


class _FakeMcpBridge:
    """The FusionMcpBridge add-in's protocol, verbatim, over the shim."""

    def __init__(self, app: Application):
        self.app = app
        self.jobs: list[str] = []
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _send(self, payload, status=200):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/status":
                    self._send({"ok": True, "app": "Autodesk Fusion", "port": bridge.port})
                else:
                    self._send({"ok": False, "error": "not found"}, 404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length) or b"{}")
                code = data.get("code", "")
                bridge.jobs.append(code)
                if HANG in code:
                    self._send({"ok": False, "error": "timed out waiting for Fusion"}, 504)
                    return
                self._send(bridge.run(code))

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def run(self, code: str) -> dict:
        """The add-in's `_run_code`: a fresh namespace per job, `adsk` in it."""
        shims = _modules(self.app)
        saved = {name: sys.modules.get(name) for name in shims}
        sys.modules.update(shims)
        namespace = {"adsk": shims["adsk"], "result": None}
        try:
            exec(compile(code, "<mcp>", "exec"), namespace)
            return {"ok": True, "result": _safe(namespace.get("result"))}
        except Exception:
            return {"ok": False, "error": traceback.format_exc()}
        finally:
            for name, mod in saved.items():
                if mod is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = mod

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture()
def bridge():
    sys.modules.pop("_tee_fusion_state", None)  # a fresh Fusion process
    fake = _FakeMcpBridge(Application(Design(parametric=True)))
    try:
        yield fake
    finally:
        fake.close()
        sys.modules.pop("_tee_fusion_state", None)


def _dead_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


PLATE = [
    {"op": "create", "kind": "sketch", "props": {"rects": [[0, 0, 120, 80]]}},
    {"op": "create", "kind": "extrude", "props": {"sketch": "sk1", "distance": 10}},
]


# -- the wire -----------------------------------------------------------------------


def test_ping_is_the_primary_threads_own_answer(bridge):
    wire = FusionHttpWire(port=bridge.port)
    ping = wire.ping()
    assert ping["product"] == "Fusion" and ping["document"] == "Untitled"
    assert ping["design"] == "parametric" and ping["ids"] == 0
    assert wire.probe() is True
    assert bridge.jobs[0].startswith(STATE_PRELUDE), "every job carries the state prelude"


def test_the_id_map_survives_a_fresh_namespace_per_job_and_locals_do_not(bridge):
    wire = FusionHttpWire(port=bridge.port)
    wire.execute("_tee['ids'] = {'b1': 'tok'}; y = 2; result = {}")
    out = wire.execute("result = {'ids': _tee['ids'], 'y': 'y' in dir()}")
    assert out == {"ids": {"b1": "tok"}, "y": False}


def test_a_fusion_error_is_one_refusal_with_the_tracebacks_tail(bridge):
    with pytest.raises(TeeError) as err:
        FusionHttpWire(port=bridge.port).execute("1/0")
    assert err.value.code == "fusion_bridge_error" and "ZeroDivisionError" in err.value.message


def test_a_504_says_the_job_is_still_running(bridge):
    with pytest.raises(TeeError) as err:
        FusionHttpWire(port=bridge.port).execute(HANG, timeout=3.0)
    assert err.value.code == "fusion_wire_failed"
    assert "STILL RUNNING" in err.value.message and "3 s" in err.value.message


def test_a_non_dict_result_is_a_bad_reply(bridge):
    with pytest.raises(TeeError) as err:
        FusionHttpWire(port=bridge.port).execute("result = 3")
    assert err.value.code == "fusion_bad_reply"


def test_unreachable_names_both_add_ins():
    with pytest.raises(TeeError) as err:
        FusionHttpWire(port=_dead_port(), connect_timeout=0.5).ping()
    assert err.value.code == "fusion_unreachable"
    assert "FusionMcpBridge" in err.value.fix and "tee_bridge/TEE" in err.value.fix


# -- the auto wire --------------------------------------------------------------------


def test_the_auto_wire_uses_the_add_in_that_answers(bridge):
    wire = FusionAutoWire(port=_dead_port(), http_port=bridge.port, connect_timeout=0.5)
    assert wire.transport is None
    ping = wire.ping()
    assert ping["design"] == "parametric"
    assert wire.transport == "FusionMcpBridge" and wire.port == bridge.port
    assert wire.execute("result = {'ok': 1}") == {"ok": 1}


def test_the_auto_wire_refuses_naming_both_ports_when_nothing_answers():
    dead_tcp, dead_http = _dead_port(), _dead_port()
    wire = FusionAutoWire(port=dead_tcp, http_port=dead_http, connect_timeout=0.5)
    assert wire.probe() is False
    with pytest.raises(TeeError) as err:
        wire.execute("result = {}")
    assert err.value.code == "fusion_unreachable"
    assert f":{dead_tcp}" in err.value.message and f":{dead_http}" in err.value.message
    assert wire.port == dead_tcp, "no transport chosen: port reports the TEE add-in's"


# -- the adapter over the second transport ---------------------------------------------


def test_a_batch_a_measure_and_a_listing_hold_across_jobs(bridge, tmp_path):
    adapter = FusionAdapter(FusionHttpWire(port=bridge.port), workdir=str(tmp_path))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    try:
        info = adapter.info()
        assert info.connected and info.extra["design"] == "parametric"
        diff = app.run_batch("fusion", PLATE)
        assert diff["details"]["b1"]["volume_mm3"] == pytest.approx(96_000.0)
        # the second job resolves an id the first job minted: _tee persisted
        measured = adapter.run(codegen.measure_program("b1"))
        assert measured["volume_mm3"] == pytest.approx(96_000.0)
        ids = {e.id for e in adapter.list_entities()}
        assert {"sk1", "b1"} <= ids
        assert adapter.info().extra["ids"] >= 2
    finally:
        app.shutdown()


def test_rollback_over_http_deletes_what_came_after(bridge, tmp_path):
    adapter = FusionAdapter(FusionHttpWire(port=bridge.port), workdir=str(tmp_path))
    app = TeeApp({"fusion": adapter}, project_root=tmp_path)
    try:
        app.run_batch("fusion", PLATE)
        boss = app.run_batch(
            "fusion",
            [
                {"op": "create", "kind": "sketch", "props": {"circles": [[60, 40, 10]]}},
                {
                    "op": "create",
                    "kind": "extrude",
                    "props": {"sketch": "sk2", "distance": 5, "operation": "join"},
                },
            ],
        )
        assert adapter.run(codegen.measure_program("b1"))["volume_mm3"] > 96_000.0
        assert {"sk2", "f2"} <= {e.id for e in adapter.list_entities()}
        app.rollback("fusion", boss["checkpoint"])  # the auto-checkpoint taken before the boss
        # The restore ran over HTTP: what the boss made is gone and the plate remains.
        # The shim's timeline delete does not un-join a body's volume (it removes the
        # feature only), so the volume itself is the smoke's fact, not this test's.
        ids = {e.id for e in adapter.list_entities()}
        assert ids == {"sk1", "f1", "b1"}, ids
    finally:
        app.shutdown()
