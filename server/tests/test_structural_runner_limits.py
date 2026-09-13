"""Solver evidence remains bounded even when a process exits between polls."""

import hashlib
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from tee.structural import runner
from tee.structural.examples import cantilever
from tee.structural.model import StructuralError


@pytest.mark.parametrize("sizes_mib", [(65,), (33, 33)])
def test_fast_exit_output_limit_includes_all_final_files(tmp_path, monkeypatch, sizes_mib):
    # The worker waits until after the runner's first size scan. It then writes
    # sparse files and exits before the next poll, deterministically reproducing
    # the bypass without allocating 65 MiB or relying on startup timing.
    command = (
        "from pathlib import Path; import time\n"
        "while not Path('finish').exists(): time.sleep(0.001)\n"
        f"for i,size in enumerate({sizes_mib!r}):\n"
        "    with Path(str(i)+'.out').open('wb') as stream: stream.truncate(size*1024*1024)\n"
    )
    real_popen = subprocess.Popen
    processes = []

    def launch(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        processes.append(process)
        return process

    def finish_before_next_poll(_seconds):
        (tmp_path / "finish").touch()
        processes[0].wait(timeout=5)

    monkeypatch.setattr(runner.subprocess, "Popen", launch)
    monkeypatch.setattr(
        runner,
        "time",
        SimpleNamespace(monotonic=runner.time.monotonic, sleep=finish_before_next_poll),
    )
    with pytest.raises(StructuralError, match="64 MiB run-output limit"):
        runner.execute([sys.executable, "-c", command], tmp_path, threading.Event(), 10)
    assert processes[0].returncode == 0


def test_oofem_result_is_bounded_before_parsing(tmp_path):
    with (tmp_path / "analysis.out").open("wb") as stream:
        stream.write(b"Finishing analysis on:\n")
        stream.truncate(runner.MAX_RESULT_BYTES + 1)
    with pytest.raises(StructuralError, match="exceeds 4 MiB"):
        runner.parse_oofem(tmp_path, cantilever())


def test_result_fifo_is_rejected_without_waiting_for_a_writer(tmp_path):
    path = tmp_path / "analysis.out"
    os.mkfifo(path)
    with pytest.raises(StructuralError, match="regular file"):
        runner.parse_oofem(tmp_path, cantilever())


def test_solver_output_symlink_cannot_bypass_file_budget(tmp_path):
    outside = tmp_path / "outside"
    outside.write_text("not solver output")
    root = tmp_path / "run"
    root.mkdir()
    (root / "analysis.out").symlink_to(outside)
    with pytest.raises(StructuralError, match="regular files"):
        runner.execute([sys.executable, "-c", "pass"], root, threading.Event(), 5)


def test_executable_identity_hash_does_not_read_entire_binary(tmp_path, monkeypatch):
    # A native executable can be much larger than the result-file cap. Hash it
    # incrementally rather than allocating an unbounded bytes object.
    expected = hashlib.sha256()
    with Path(sys.executable).open("rb") as stream:
        while block := stream.read(65536):
            expected.update(block)

    def unbounded_read_forbidden(_path):
        raise AssertionError("Unbounded read_bytes used for solver evidence")

    monkeypatch.setattr(Path, "read_bytes", unbounded_read_forbidden)
    result = runner.execute(
        [sys.executable, "-c", "print('completed')"], tmp_path, threading.Event(), 5
    )
    assert result["executable_sha256"] == expected.hexdigest()


def test_evidence_hash_refuses_oversized_file(tmp_path):
    path = tmp_path / "oversized.out"
    with path.open("wb") as stream:
        stream.truncate(runner.MAX_RUN_BYTES + 1)
    with pytest.raises(StructuralError, match="exceeds 64 MiB"):
        runner._file_sha256(path)
