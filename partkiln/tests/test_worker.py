"""The worker (`python -m partkiln.worker`) and the `LocalKernel` it wraps (A66 D2).

Driven through a raw NDJSON client written here - no `tee`, no
`SidecarKernel` - so this is the protocol itself under test: the ready line
first, one JSON line per request, stdout carrying nothing else even when a
method prints, refusals as error replies with a fix, a clean exit on
`shutdown`, EOF and SIGTERM. OCP is never warmed here (the 26 s cold import
is exactly what the worker keeps OUT of a spawn).
"""

from __future__ import annotations

import json
import os
import re
import select
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

import partkiln
from partkiln.client import (
    KERNEL_METHODS,
    KernelClient,
    LocalKernel,
    known_methods,
    register_method,
)
from partkiln.document import CommandError, Document

SRC = Path(__file__).resolve().parents[1] / "src"
ENV = {"PYTHONPATH": str(SRC), "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
HEX16 = re.compile(r"^[0-9a-f]{16}$")

PARAM_SET = {"op": "param_set", "params": {"W": "10mm"}}
SKETCH = {
    "op": "create",
    "kind": "sketch",
    "name": "base",
    "plane": "XY",
    "profile": {"rect": ["W", 6]},
}


class Wire:
    """A raw NDJSON client over a spawned worker; keeps every byte stdout carried."""

    def __init__(self, *args: str, stderr: Any = None, timeout_s: float = 10.0) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "partkiln.worker", *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL if stderr is None else stderr,
            env=ENV,
            bufsize=0,
        )
        self.timeout_s = timeout_s
        self.raw = b""
        self._buffer = b""
        self._id = 0
        started = time.perf_counter()
        self.ready = self.read_line()
        self.spawn_s = time.perf_counter() - started

    def read_line(self) -> dict[str, Any]:
        deadline = time.monotonic() + self.timeout_s
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                line, self._buffer = self._buffer[:newline], self._buffer[newline + 1 :]
                return json.loads(line)  # a non-JSON line here IS the failure under test
            remaining = deadline - time.monotonic()
            assert remaining > 0, "the worker gave no line before the deadline"
            ready, _, _ = select.select([self.proc.stdout], [], [], min(remaining, 1.0))
            if not ready:
                assert self.proc.poll() is None, f"the worker died (exit {self.proc.returncode})"
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            assert chunk, f"EOF from the worker (exit {self.proc.poll()})"
            self.raw += chunk
            self._buffer += chunk

    def send_raw(self, data: bytes) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        line = {"id": self._id, "method": method, "params": params or {}}
        self.send_raw(json.dumps(line).encode() + b"\n")
        reply = self.read_line()
        assert reply["id"] == self._id, reply
        assert set(reply["meta"]) == {"rss_mb", "wall_ms"}, reply
        return reply

    def result(self, method: str, params: dict[str, Any] | None = None) -> Any:
        reply = self.request(method, params)
        assert "result" in reply, reply
        return reply["result"]

    def error(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        reply = self.request(method, params)
        assert "error" in reply, reply
        return reply["error"]

    def lines(self) -> list[bytes]:
        return [line for line in self.raw.split(b"\n") if line.strip()]

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
        self.proc.wait(timeout=5)
        for stream in (self.proc.stdin, self.proc.stdout):
            if stream is not None:
                stream.close()


@pytest.fixture
def worker() -> Any:
    wire = Wire()
    yield wire
    wire.close()


# --- the protocol --------------------------------------------------------------------


def test_the_ready_line_comes_first_without_ocp(worker: Wire) -> None:
    ready = worker.ready
    assert ready["event"] == "ready"
    assert ready["pid"] == worker.proc.pid
    assert ready["python"].startswith("3.")
    assert ready["partkiln"] == partkiln.__version__
    assert isinstance(ready["ocp"], bool)
    assert ready["warm"] is False  # no --warm: the 26 s cold import is not paid here
    assert 0 < ready["import_s"] < 5
    assert ready["rss_mb"] > 0
    assert worker.spawn_s < 5


def test_one_json_line_per_request_through_the_method_set(worker: Wire) -> None:
    assert worker.result("ping") == {"alive": True, "pid": worker.proc.pid}
    info = worker.result("info")
    assert info["mode"] == "sidecar"
    assert info["commands"] == 0
    assert info["warm"] is False

    applied = worker.result("apply", {"commands": [PARAM_SET]})
    assert applied["results"] == [
        {"changed": [{"name": "W", "old": None, "new": 10.0}], "unchanged": 0}
    ]
    assert applied["commands"] == 1
    assert HEX16.match(applied["fingerprint"])
    assert worker.result("fingerprint") == applied["fingerprint"]

    script = worker.result("script")
    assert script["partkiln_script"] == 1
    assert [c["op"] for c in script["commands"]] == ["param_set"]

    assert worker.result("shutdown") == {"shutdown": True}
    assert worker.proc.wait(timeout=5) == 0

    lines = worker.lines()
    assert len(lines) == 1 + 6  # the ready line and one reply per request
    assert all(isinstance(json.loads(line), dict) for line in lines)


def test_stdout_carries_only_json_even_when_a_method_prints(tmp_path: Path) -> None:
    log = tmp_path / "worker.err"
    with log.open("wb") as handle:
        wire = Wire(stderr=handle)
    try:
        assert wire.result("echo_stdout", {"text": "chatter-7f3a"}) == {"echoed": "chatter-7f3a"}
        assert wire.result("ping")["alive"] is True
        # the reply carries the text; the raw writes to fd 1 must not
        assert b"native:" not in wire.raw and b"python:" not in wire.raw
        lines = wire.lines()
        assert len(lines) == 1 + 2
        assert all(isinstance(json.loads(line), dict) for line in lines)
        wire.result("shutdown")
        assert wire.proc.wait(timeout=5) == 0
    finally:
        wire.close()
    forwarded = log.read_text()  # to stderr, not lost
    assert "native:chatter-7f3a" in forwarded and "python:chatter-7f3a" in forwarded


def test_a_bad_method_is_an_error_reply_with_a_fix(worker: Wire) -> None:
    error = worker.error("nope")
    assert error["code"] == "pk_bad_op"
    assert "apply" in error["message"] and "fingerprint" in error["message"]
    assert "echo_stdout" not in error["message"]  # hidden test hooks stay hidden
    assert error["fix"]
    assert worker.result("ping")["alive"] is True


def test_nothing_on_stdin_is_skipped_except_blank_lines(worker: Wire) -> None:
    worker.send_raw(b"not json\n")
    reply = worker.read_line()
    assert reply["id"] is None
    assert reply["error"]["code"] == "pk_bad_request"
    worker.send_raw(b"[1, 2]\n")
    assert worker.read_line()["error"]["code"] == "pk_bad_request"
    worker.send_raw(b'{"id": 9, "params": {}}\n')
    reply = worker.read_line()
    assert reply["id"] == 9 and reply["error"]["code"] == "pk_bad_request"
    worker.send_raw(b'{"id": 10, "method": "ping", "params": [1]}\n')
    assert worker.read_line()["error"]["code"] == "pk_bad_request"
    worker.send_raw(b"\n\n   \n")  # blank lines: no reply at all
    assert worker.result("ping")["alive"] is True
    assert len(worker.lines()) == 1 + 5


def test_an_unhandled_exception_is_an_error_reply_never_a_crash(worker: Wire) -> None:
    error = worker.error("boom", {"text": "kaboom"})
    assert error["code"] == "pk_internal"
    assert error["message"] == "RuntimeError: kaboom"
    assert error["fix"]
    assert worker.proc.poll() is None
    assert worker.result("ping")["alive"] is True


def test_a_refusing_batch_rolls_back_and_names_the_command(worker: Wire) -> None:
    before = worker.result("fingerprint")
    error = worker.error("apply", {"commands": [PARAM_SET, {"op": "nope"}]})
    assert error["code"] == "pk_bad_op"
    assert error["message"].startswith("command 1 of 2 (nope): unknown op 'nope'")
    assert "rolled back" in error["message"]
    assert worker.result("fingerprint") == before
    assert worker.result("script")["commands"] == []


def test_eof_on_stdin_exits_zero(worker: Wire) -> None:
    assert worker.proc.stdin is not None
    worker.proc.stdin.close()
    assert worker.proc.wait(timeout=5) == 0


def test_sigterm_exits_cleanly(worker: Wire) -> None:
    worker.proc.send_signal(signal.SIGTERM)
    assert worker.proc.wait(timeout=5) == 0


def test_a_round_trip_costs_about_a_millisecond(worker: Wire) -> None:
    worker.result("ping")
    started = time.perf_counter()
    for _ in range(100):
        worker.result("ping")
    per_call = (time.perf_counter() - started) / 100
    assert per_call < 0.03, f"{per_call * 1000:.1f} ms per round trip"


def test_client_and_worker_import_no_ocp_and_no_tee() -> None:
    code = (
        "import sys\n"
        "import partkiln.client, partkiln.worker\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in "
        "('OCP', 'tee', 'cadquery', 'casadi', 'vtkmodules', 'fpdf', 'PySide6')]\n"
        "print(sorted(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=ENV, check=True
    )
    assert out.stdout.strip() == "[]", out.stdout


# --- the kernel behind it, in-process ------------------------------------------------


def test_local_kernel_is_a_kernel_client() -> None:
    kernel = LocalKernel()
    assert isinstance(kernel, KernelClient)
    assert kernel.probe() is True
    assert kernel.mode == "local"
    info = kernel.info()
    assert info["mode"] == "local" and info["pid"] == os.getpid()
    assert set(info) >= {"ocp", "occt", "warm", "commands", "fingerprint", "parts"}


def test_apply_is_atomic_across_the_batch() -> None:
    kernel = LocalKernel()
    kernel.apply([PARAM_SET])
    before = kernel.fingerprint()
    with pytest.raises(CommandError) as caught:
        kernel.apply([SKETCH, {"op": "create", "kind": "widget"}])
    assert caught.value.code == "pk_bad_op"
    assert str(caught.value).startswith("command 1 of 2 (create): unknown create kind 'widget'")
    assert kernel.fingerprint() == before
    assert len(kernel.document.history) == 1
    # The rolled-back sketch left no row; the parameter that survived has one
    # (D7: everything a batch can change is an entity), and so does the doc.
    assert [row["id"] for row in kernel.entities()] == ["doc", "param:W"]
    with pytest.raises(CommandError) as caught:
        kernel.apply({"op": "param_set"})  # type: ignore[arg-type]
    assert caught.value.code == "pk_bad_op"


def test_entities_and_detail_come_from_the_document_now_that_it_has_them() -> None:
    """P3/P4 gave `Document` its own `entities()`/`detail()` (D7), so the
    kernel delegates and the rows carry the doc, the parameters and the
    sketch; the summary-derived fallback below it is the path a document
    without them still takes."""
    kernel = LocalKernel()
    kernel.apply([PARAM_SET, SKETCH])
    rows = {row["id"]: row for row in kernel.entities()}
    assert set(rows) == {"doc", "param:W", "sk:base"}
    assert rows["sk:base"]["plane"] == "XY"
    assert rows["sk:base"]["dof"] == 0 and rows["sk:base"]["status"] == "ok"
    assert rows["param:W"]["value"] == 10.0 and rows["param:W"]["unit"] == "mm"
    assert rows["doc"]["sketches"] == 1 and rows["doc"]["script_commands"] == 2

    detail = kernel.detail("sk:base")
    assert detail["id"] == "sk:base" and detail["dof"] == 0
    assert detail["dims"] and "coordinates" not in detail  # scalars only (hard rule 1)
    assert kernel.detail("doc")["fingerprint"] == kernel.fingerprint()
    with pytest.raises(CommandError) as caught:
        kernel.detail("sk:nope")
    assert caught.value.code == "pk_ref_unknown"
    assert "sk:base" in str(caught.value)


def test_a_document_that_grows_its_own_entities_is_delegated_to() -> None:
    class Grown(Document):
        def entities(self) -> list[dict[str, Any]]:
            return [{"id": "part:grown", "kind": "part"}]

        def detail(self, entity_id: str) -> dict[str, Any]:
            return {"id": entity_id, "from": "document"}

    kernel = LocalKernel(Grown())
    assert kernel.entities() == [{"id": "part:grown", "kind": "part"}]
    assert kernel.detail("part:grown") == {"id": "part:grown", "from": "document"}


def test_call_dispatches_the_registry_and_hides_hidden_methods() -> None:
    kernel = LocalKernel()
    assert kernel.call("ping", {})["alive"] is True
    assert kernel.call("fingerprint", {}) == kernel.fingerprint()
    assert kernel.call("apply", {"commands": [PARAM_SET]})["commands"] == 1
    with pytest.raises(CommandError) as caught:
        kernel.call("apply", {})
    assert caught.value.code == "pk_needs"

    @register_method("zz_secret", hidden=True)
    def _secret(k: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
        return {"secret": params.get("x")}

    try:
        assert kernel.call("zz_secret", {"x": 1}) == {"secret": 1}
        assert "zz_secret" not in known_methods()
        with pytest.raises(CommandError) as caught:
            kernel.call("zz_nope", {})
        assert caught.value.code == "pk_bad_op"
        assert "zz_secret" not in str(caught.value) and "apply" in str(caught.value)
        assert caught.value.fix  # type: ignore[attr-defined]
    finally:
        KERNEL_METHODS.pop("zz_secret", None)


def test_snapshot_restore_discard_keep_the_document_handle(tmp_path: Path) -> None:
    kernel = LocalKernel()
    document = kernel.document
    kernel.apply([PARAM_SET, SKETCH])
    taken = kernel.fingerprint()
    payload = kernel.snapshot("before edit", tmp_path / "cp")
    path = Path(payload["path"])
    assert path.is_file() and path.parent == tmp_path / "cp"
    assert path.name.startswith("before_edit-")
    assert payload == {
        "label": "before edit",
        "path": str(path),
        "commands": 2,
        "fingerprint": taken,
        "brep": False,
        # no part, so no cache to name - `caches` is always there, so a
        # `discard()` never has to open the json to find what to unlink.
        "caches": [],
    }

    kernel.apply([{"op": "param_set", "params": {"W": "12mm"}}])
    assert kernel.fingerprint() != taken
    kernel.restore(payload)
    assert kernel.fingerprint() == taken
    assert len(kernel.document.history) == 2
    assert kernel.document is document  # the live handle survives a restore

    kernel.discard(payload)
    assert not path.exists()
    kernel.discard(payload)  # twice is fine
    with pytest.raises(CommandError) as caught:
        kernel.restore(payload)
    assert caught.value.code == "pk_checkpoint_missing"
    with pytest.raises(CommandError) as caught:
        kernel.restore({})
    assert caught.value.code == "pk_needs"


def test_restore_reports_a_fingerprint_that_no_longer_matches(tmp_path: Path) -> None:
    kernel = LocalKernel()
    kernel.apply([PARAM_SET])
    payload = kernel.snapshot("cp", tmp_path)
    path = Path(payload["path"])
    data = json.loads(path.read_text())
    data["fingerprint"] = "0" * 16
    path.write_text(json.dumps(data))
    with pytest.raises(CommandError) as caught:
        kernel.restore(payload)
    assert caught.value.code == "pk_checkpoint_mismatch"
    assert kernel.fingerprint() == payload["fingerprint"]  # the script still won


def test_warm_reports_without_refusing_when_ocp_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    import partkiln.brep as brep

    monkeypatch.setattr(brep, "_ocp_present", False)
    kernel = LocalKernel()
    report = kernel.warm()
    assert report["ocp"] is False and report["occt"] is None
    assert report["mode"] == "local"
    assert 0 <= report["import_s"] < 1 and report["rss_mb"] > 0
    assert kernel.warm()["cached"] is True
