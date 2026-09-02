"""`SidecarKernel` against a real `partkiln.worker` spawned from this venv (A66 D2).

The worker is started with `sys.executable` and `PYTHONPATH=<repo>/partkiln/src`
so no sidecar venv is needed; OCP is never warmed. Every test spawns in
~0.1 s and finishes well inside the suite's 60 s pytest-timeout.
"""

from __future__ import annotations

import os
import stat
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from tee.adapters.partkiln.wire import INSTALL_LINE, SIDECAR_PY, SidecarKernel
from tee.kernel.errors import TeeError

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "partkiln" / "src"
pytestmark = pytest.mark.skipif(not SRC.is_dir(), reason="partkiln/src is not beside server/")

PARAM_SET = {"op": "param_set", "params": {"W": "10mm"}}
SKETCH = {
    "op": "create",
    "kind": "sketch",
    "name": "base",
    "plane": "XY",
    "profile": {"rect": ["W", 6]},
}


def make(tmp_path: Path, **kw: Any) -> SidecarKernel:
    kw.setdefault("timeout_s", 10.0)
    return SidecarKernel(
        python=sys.executable,
        stderr_path=tmp_path / "worker.log",
        env={"PYTHONPATH": str(SRC)},
        **kw,
    )


@pytest.fixture
def kernel(tmp_path: Path) -> Any:
    wire = make(tmp_path)
    wire.start()
    yield wire
    wire.close()


def test_start_reads_the_ready_line_and_never_respawns_a_live_worker(kernel: SidecarKernel) -> None:
    ready = kernel.ready
    assert ready["event"] == "ready"
    assert ready["pid"] == kernel.proc.pid
    assert ready["warm"] is False  # the 26 s cold import is not paid at spawn
    assert isinstance(ready["ocp"], bool)
    assert kernel.spawn_s is not None and kernel.spawn_s < 5
    assert kernel.probe() is True and kernel.alive() is True
    assert kernel.start()["pid"] == ready["pid"]


def test_the_method_set_round_trips(kernel: SidecarKernel, tmp_path: Path) -> None:
    info = kernel.info()
    assert info["mode"] == "sidecar" and info["commands"] == 0
    applied = kernel.apply([PARAM_SET, SKETCH])
    assert applied["commands"] == 2
    assert applied["results"][0]["changed"] == [{"name": "W", "old": None, "new": 10.0}]
    assert applied["results"][1]["id"] == "sk:base"
    taken = kernel.fingerprint()
    assert taken == applied["fingerprint"]
    assert [c["op"] for c in kernel.script()["commands"]] == ["param_set", "create"]
    assert [row["id"] for row in kernel.entities()] == ["sk:base"]
    assert kernel.detail("sk:base")["dof"] == 0
    assert kernel.call("ping", {})["alive"] is True

    payload = kernel.snapshot("edit", tmp_path / "cp")
    assert payload["fingerprint"] == taken and payload["brep"] is False
    assert Path(payload["path"]).is_file()
    kernel.apply([{"op": "param_set", "params": {"W": "12mm"}}])
    assert kernel.fingerprint() != taken
    kernel.restore(payload)
    assert kernel.fingerprint() == taken
    kernel.discard(payload)
    assert not Path(payload["path"]).exists()

    kernel.shutdown()
    assert kernel.alive() is False and kernel.proc is None


def test_error_replies_become_tee_errors(kernel: SidecarKernel) -> None:
    with pytest.raises(TeeError) as caught:
        kernel.call("nope", {})
    assert caught.value.code == "pk_bad_op"
    assert "apply" in caught.value.message and caught.value.fix
    before = kernel.fingerprint()
    with pytest.raises(TeeError) as caught:
        kernel.apply([PARAM_SET, {"op": "nope"}])
    assert caught.value.code == "pk_bad_op"
    assert caught.value.message.startswith("command 1 of 2 (nope)")
    assert kernel.fingerprint() == before  # the worker rolled the batch back
    with pytest.raises(TeeError) as caught:
        kernel.call("boom", {})
    assert caught.value.code == "pk_internal"
    assert kernel.alive() is True


def test_death_names_the_exit_code_and_restart_gives_a_fresh_ready(
    kernel: SidecarKernel, tmp_path: Path
) -> None:
    first = kernel.ready["pid"]
    kernel.proc.kill()
    with pytest.raises(TeeError) as caught:
        kernel.info()
    assert caught.value.code == "pk_worker_dead"
    assert "exit -9" in caught.value.message
    assert str(tmp_path / "worker.log") in caught.value.fix
    assert kernel.alive() is False and kernel.proc is None
    with pytest.raises(TeeError) as caught:
        kernel.fingerprint()
    assert caught.value.code == "pk_worker_down"

    ready = kernel.restart()
    assert ready["event"] == "ready" and ready["pid"] != first
    assert kernel.ready["pid"] == ready["pid"]
    assert kernel.info()["commands"] == 0  # a fresh document: the adapter replays the script


def test_a_timeout_kills_the_worker(tmp_path: Path) -> None:
    kernel = make(tmp_path, timeout_s=1.0)
    kernel.start()
    pid = kernel.proc.pid
    started = time.monotonic()
    with pytest.raises(TeeError) as caught:
        kernel.call("sleep", {"seconds": 5})
    assert time.monotonic() - started < 3
    assert caught.value.code == "pk_worker_timeout"
    assert "sleep" in caught.value.message
    assert caught.value.fix == (
        "the batch was killed after 1 s; it is rolled back by the kernel checkpoint; "
        "split it or pass job=true"
    )
    assert kernel.alive() is False and kernel.proc is None
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_an_absent_interpreter_refuses_with_the_install_line(tmp_path: Path) -> None:
    assert SidecarKernel().python == SIDECAR_PY
    kernel = SidecarKernel(python=tmp_path / "nope" / "bin" / "python")
    with pytest.raises(TeeError) as caught:
        kernel.start()
    assert caught.value.code == "pk_kernel_absent"
    assert INSTALL_LINE in caught.value.fix and "uv venv" in INSTALL_LINE
    with pytest.raises(TeeError) as caught:
        kernel.info()
    assert caught.value.code == "pk_worker_down"


def test_non_json_lines_on_stdout_are_skipped(tmp_path: Path) -> None:
    """An interpreter shim that talks before the worker does: garbage and a
    JSON line that is not the ready line, both skipped."""
    shim = tmp_path / "python-shim"
    shim.write_text(
        "#!/bin/sh\n"
        'echo "shim: banner before the protocol"\n'
        'echo \'{"event": "not-ready"}\'\n'
        f'exec "{sys.executable}" "$@"\n'
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
    kernel = SidecarKernel(python=shim, timeout_s=10.0, env={"PYTHONPATH": str(SRC)})
    try:
        ready = kernel.start()
        assert ready["event"] == "ready"
        assert kernel.call("ping", {})["alive"] is True
    finally:
        kernel.close()


def test_close_is_quiet_and_idempotent(kernel: SidecarKernel, tmp_path: Path) -> None:
    kernel.close()
    assert kernel.alive() is False
    kernel.close()
    assert (tmp_path / "worker.log").exists()
