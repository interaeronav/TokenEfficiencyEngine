"""A69 P1 - the Fusion bridge add-in and the wire, without Fusion.

The add-in (`adapters/fusion/tee_bridge/TEE/TEE.py`) keeps everything that
is not adsk at module level: the frame protocol, the primary-thread hop and
the socket loop. These tests drive that code as Fusion would - a real
listener on an ephemeral port, a stub "primary thread" that services the
custom event, `FusionWire` on the other end - and the run/stop glue against
a fake adsk.core that speaks the verified names (doc 71 section 3 rows 1-3).
"""

from __future__ import annotations

import importlib.util
import json
import queue
import socket
import sys
import threading
import types
from pathlib import Path

import pytest

from tee.adapters.fusion.wire import FusionWire
from tee.kernel.errors import TeeError

ADDIN = (
    Path(__file__).resolve().parents[2] / "adapters" / "fusion" / "tee_bridge" / "TEE" / "TEE.py"
)


@pytest.fixture(scope="module")
def bridge():
    """The add-in module, imported from the repo without adsk present."""
    assert "adsk" not in sys.modules
    spec = importlib.util.spec_from_file_location("tee_fusion_bridge", ADDIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _reply(raw: bytes) -> dict:
    return json.loads(raw.rstrip(b"\0").decode())


# -- the frame ------------------------------------------------------------------


def test_execute_frame_answers_the_result_dict_and_captures_streams(bridge):
    ns = {"_tee": {}}
    out = _reply(
        bridge.execute_frame(
            json.dumps({"type": "execute", "code": "print('hi'); result = {'x': 1}"}).encode(), ns
        )
    )
    assert out == {"status": "ok", "result": {"x": 1}, "stdout": "hi\n"}


def test_a_persistent_tee_dict_survives_between_frames_and_locals_do_not(bridge):
    ns = {"_tee": {}}
    bridge.execute_frame(
        b'{"type": "execute", "code": "_tee[\'ids\'] = {\'b1\': \'tok\'}; y = 2; result = {}"}', ns
    )
    code = "result = {'ids': _tee['ids'], 'y': 'y' in dir()}"
    out = _reply(bridge.execute_frame(json.dumps({"type": "execute", "code": code}).encode(), ns))
    assert out["result"] == {"ids": {"b1": "tok"}, "y": False}
    assert ns["_tee"]["ids"] == {"b1": "tok"}


@pytest.mark.parametrize(
    ("frame", "needle"),
    [
        (b"not json", "not valid JSON"),
        (b"[1, 2]", "JSON object"),
        (b'{"type": "frobnicate"}', "unsupported request type"),
        (b'{"type": "execute", "code": 7}', "'code' must be a string"),
        (
            b'{"type": "execute", "code": "import sys; sys.exit(0)"}',
            "blocked by the TEE bridge guard",
        ),
        (b'{"type": "execute", "code": "result = 3"}', "must be a dict"),
        (b'{"type": "execute", "code": "1/0"}', "ZeroDivisionError"),
        (b'{"type": "execute", "code": "result = {\'o\': object()}"}', "not JSON-serializable"),
    ],
)
def test_every_bad_frame_is_one_structured_error(bridge, frame, needle):
    out = _reply(bridge.execute_frame(frame, {"_tee": {}}))
    assert out["status"] == "error" and needle in out["message"]


def test_strict_json_off_reprs_what_it_cannot_serialise(bridge):
    frame = json.dumps(
        {"type": "execute", "code": "result = {'o': object()}", "strict_json": False}
    )
    out = _reply(bridge.execute_frame(frame.encode(), {"_tee": {}}))
    assert out["status"] == "ok" and out["result"]["o"].startswith("<object object")


def test_a_ping_is_the_primary_threads_own_answer_not_the_io_threads(bridge):
    """The ping runs PING_CODE, which imports adsk: without Fusion it is an
    honest error, never a fabricated 'up'."""
    out = _reply(bridge.execute_frame(b'{"type": "ping"}', {"_tee": {}}))
    assert out["status"] == "error" and "adsk" in out["message"]
    assert bridge.frame_deadline(b'{"type": "ping"}') == bridge.PING_DEADLINE_S
    assert bridge.frame_deadline(b'{"type": "execute", "code": "x"}') == bridge.CALL_DEADLINE_S


# -- the hop ----------------------------------------------------------------------


class _PrimaryThread:
    """Stands in for Fusion's event loop: fire() queues, a thread services."""

    def __init__(self):
        self.fired: queue.Queue[str] = queue.Queue()
        self.marshaller = None
        self.thread = threading.Thread(target=self._loop, name="fake-primary", daemon=True)
        self.ran_on: list[str] = []
        self._stop = threading.Event()

    def fire(self, task_id: str) -> bool:
        self.fired.put(task_id)
        return True

    def _loop(self):
        while not self._stop.is_set():
            try:
                task_id = self.fired.get(timeout=0.05)
            except queue.Empty:
                continue
            self.ran_on.append(threading.current_thread().name)
            self.marshaller.run(task_id)

    def start(self, marshaller):
        self.marshaller = marshaller
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.thread.join(1)


def test_the_marshaller_runs_the_frame_on_the_primary_thread_and_returns_its_reply(bridge):
    primary = _PrimaryThread()
    marshaller = bridge.Marshaller(primary.fire)
    primary.start(marshaller)
    try:
        code = "import threading; result = {'thread': threading.current_thread().name}"
        out = _reply(marshaller.submit(json.dumps({"type": "execute", "code": code}).encode()))
        assert out["status"] == "ok" and out["result"]["thread"] == "fake-primary"
        assert primary.ran_on == ["fake-primary"] and marshaller.pending() == 0
    finally:
        primary.stop()


def test_a_request_the_primary_thread_never_services_times_out_structurally(bridge):
    marshaller = bridge.Marshaller(lambda task_id: True)  # queued, never run
    out = _reply(marshaller.submit(b'{"type": "execute", "code": "result = {}"}', deadline_s=0.1))
    assert out["status"] == "error" and "did not service" in out["message"]
    assert "modal dialog" in out["message"] and marshaller.pending() == 0
    # a late run of the withdrawn task is a no-op, not a crash
    assert marshaller.run("nope") is False


def test_a_fire_that_fails_is_reported_not_waited_for(bridge):
    marshaller = bridge.Marshaller(lambda task_id: False)
    out = _reply(marshaller.submit(b'{"type": "ping"}'))
    assert out["status"] == "error" and "could not queue" in out["message"]

    def boom(task_id):
        raise RuntimeError("no event registered")

    out = _reply(bridge.Marshaller(boom).submit(b'{"type": "ping"}'))
    assert "RuntimeError: no event registered" in out["message"]


# -- the socket loop + the wire --------------------------------------------------


@pytest.fixture
def served(bridge):
    primary = _PrimaryThread()
    marshaller = bridge.Marshaller(primary.fire)
    primary.start(marshaller)
    listener = bridge.Listener(marshaller, "127.0.0.1", 0)
    listener.start()
    try:
        yield listener, marshaller
    finally:
        listener.close()
        primary.stop()


def test_the_wire_round_trips_over_a_real_socket(served):
    listener, marshaller = served
    wire = FusionWire(port=listener.port)
    assert wire.execute("_tee['ids'] = {'sk1': 'tok'}; result = {'ok': True}") == {"ok": True}
    assert wire.execute("result = {'n': len(_tee['ids'])}") == {"n": 1}
    assert marshaller.namespace["_tee"]["ids"] == {"sk1": "tok"}


def test_the_wire_turns_a_bridge_error_into_one_refusal_with_the_tail(served):
    listener, _ = served
    wire = FusionWire(port=listener.port)
    with pytest.raises(TeeError) as err:
        wire.execute(
            "import sys\nsys.stderr.write('warned')\nraise ValueError('sketch has no profile')"
        )
    assert err.value.code == "fusion_bridge_error"
    assert "ValueError: sketch has no profile" in err.value.message
    assert "stderr: warned" in err.value.message
    assert err.value.fix


def test_a_ping_without_fusion_is_down_and_the_wire_says_so(served):
    """PING_CODE imports adsk; with no Fusion that is a bridge error, so
    probe() is False - the bridge never fakes being up."""
    listener, _ = served
    wire = FusionWire(port=listener.port)
    assert wire.probe() is False
    with pytest.raises(TeeError) as err:
        wire.ping()
    assert err.value.code == "fusion_bridge_error"


def test_a_malformed_and_an_oversize_frame_get_structured_errors(served, bridge):
    listener, _ = served
    with socket.create_connection(("127.0.0.1", listener.port), 2) as conn:
        conn.sendall(b"garbage\0")
        raw = conn.recv(65536)
    assert _reply(raw)["status"] == "error" and "not valid JSON" in _reply(raw)["message"]
    bridge._MAX_REQUEST_BYTES, saved = 64, bridge._MAX_REQUEST_BYTES
    try:
        with socket.create_connection(("127.0.0.1", listener.port), 2) as conn:
            conn.sendall(b"x" * 100)
            raw = conn.recv(65536)
        assert "too large" in _reply(raw)["message"]
    finally:
        bridge._MAX_REQUEST_BYTES = saved


def test_no_bridge_is_one_refusal_with_the_install_fix():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    wire = FusionWire(port=free_port, connect_timeout=0.5)
    assert wire.probe() is False
    with pytest.raises(TeeError) as err:
        wire.execute("result = {}")
    assert err.value.code == "fusion_unreachable"
    assert "Scripts and Add-Ins" in err.value.fix and "--adapter fusion" in err.value.fix


# -- the Fusion glue, against a fake adsk.core that speaks the verified names -----


class _FakeEvent:
    def __init__(self, event_id):
        self.eventId = event_id
        self.handlers = []

    def add(self, handler):
        self.handlers.append(handler)

    def remove(self, handler):
        self.handlers.remove(handler)


class _FakeArgs:
    def __init__(self, info):
        self.additionalInfo = info


class _FakeApp:
    """registerCustomEvent / fireCustomEvent / unregisterCustomEvent / log,
    the four Application members the glue uses (doc 71 rows 1, 2, 4)."""

    def __init__(self):
        self.events: dict[str, _FakeEvent] = {}
        self.logged: list[str] = []
        self.fired: queue.Queue = queue.Queue()

    def registerCustomEvent(self, event_id):
        if event_id in self.events:
            return None
        self.events[event_id] = _FakeEvent(event_id)
        return self.events[event_id]

    def fireCustomEvent(self, event_id, info=""):
        self.fired.put((event_id, info))
        return event_id in self.events

    def unregisterCustomEvent(self, event_id):
        return self.events.pop(event_id, None) is not None

    def log(self, message):
        self.logged.append(str(message))

    def service(self):
        """What Fusion does when idle: deliver the queued event on the primary thread."""
        event_id, info = self.fired.get(timeout=2)
        for handler in self.events[event_id].handlers:
            handler.notify(_FakeArgs(info))


def _fake_core(app):
    core = types.SimpleNamespace()
    core.Application = types.SimpleNamespace(get=lambda: app)

    class CustomEventHandler:
        def __init__(self):
            pass

    core.CustomEventHandler = CustomEventHandler
    return core


def test_start_registers_the_event_serves_and_stop_unwinds_it(bridge):
    app = _FakeApp()
    state = bridge.start(_fake_core(app), port=0, log=app.log)
    try:
        assert bridge.EVENT_ID in app.events and len(app.events[bridge.EVENT_ID].handlers) == 1
        assert app.logged and app.logged[0].startswith("TEE bridge listening on 127.0.0.1:")
        port = state["listener"].port
        # a request from the wire parks a task and fires the event...
        replies: list = []
        wire = FusionWire(port=port)
        client = threading.Thread(
            target=lambda: replies.append(wire.execute("result = {'served': True}"))
        )
        client.start()
        app.service()  # ...which Fusion's primary thread services through notify()
        client.join(2)
        assert replies == [{"served": True}]
        with pytest.raises(RuntimeError):
            bridge.start(_fake_core(app), port=0)  # already running
    finally:
        bridge.shutdown()
    assert bridge.EVENT_ID not in app.events and not bridge._STATE
    assert FusionWire(port=port, connect_timeout=0.3).probe() is False


def test_a_second_bridge_on_the_same_port_fails_with_the_fix_and_unwinds(bridge):
    app = _FakeApp()
    state = bridge.start(_fake_core(app), port=0, log=app.log)
    port = state["listener"].port
    try:
        other = _FakeApp()
        # the module-level _STATE guards one bridge per process; a second
        # process on the same port is what the OSError branch is for
        bridge._STATE.clear()
        try:
            with pytest.raises(RuntimeError) as err:
                bridge.start(_fake_core(other), port=port)
            assert "already in use" in str(err.value) and "--fusion-port" in str(err.value)
            assert bridge.EVENT_ID not in other.events, "the failed start unregistered its event"
        finally:
            bridge._STATE.update(state)
    finally:
        bridge.shutdown()


def test_the_handler_survives_a_bad_task_id(bridge):
    app = _FakeApp()
    marshaller = bridge.Marshaller(lambda tid: True)
    handler = bridge._make_handler(_fake_core(app), marshaller, app.log)
    handler.notify(_FakeArgs("no-such-task"))  # returns False inside, logs nothing
    assert app.logged == []
