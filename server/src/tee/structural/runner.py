"""Local executable discovery and bounded, cancellable external solver runs."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

from . import decks
from .model import fail

ENGINES = ("openseespy", "oofem", "code_aster")
MAX_RUN_BYTES = 64 * 1024 * 1024
MAX_RESULT_BYTES = 4 * 1024 * 1024
HASH_CHUNK_BYTES = 64 * 1024


def _check_output_limit(root: Path) -> None:
    total = 0
    for path in root.rglob("*"):
        try:
            info = path.lstat()
        except FileNotFoundError:
            # A running solver may remove a temporary file between discovery
            # and stat. The final scan runs after owned processes are stopped.
            continue
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            fail("Structural solver output must contain regular files and directories only.")
        total += info.st_size
        if total > MAX_RUN_BYTES:
            fail("Structural solver exceeded the 64 MiB run-output limit.")


@contextlib.contextmanager
def _regular_file(path: Path, maximum: int | None) -> Iterator[BinaryIO]:
    # NONBLOCK prevents a malformed FIFO result from blocking before fstat;
    # NOFOLLOW prevents a result symlink from escaping the run's file budget.
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            fail("Structural solver evidence must be a regular file.")
        if maximum is not None and info.st_size > maximum:
            fail(f"Structural solver evidence {path.name} exceeds {maximum // (1024 * 1024)} MiB.")
        yield stream


def _result_text(path: Path) -> str:
    with _regular_file(path, MAX_RESULT_BYTES) as stream:
        data = stream.read(MAX_RESULT_BYTES + 1)
    if len(data) > MAX_RESULT_BYTES:
        fail("Structural solver result exceeded the 4 MiB result-file limit while reading.")
    return data.decode("utf-8")


def _file_sha256(path: Path, maximum: int | None = MAX_RUN_BYTES) -> str:
    digest = hashlib.sha256()
    total = 0
    with _regular_file(path, maximum) as stream:
        while block := stream.read(HASH_CHUNK_BYTES):
            total += len(block)
            if maximum is not None and total > maximum:
                fail("Structural solver evidence exceeded its size limit while hashing.")
            digest.update(block)
    return digest.hexdigest()


def executable(engine: str, cfg: dict) -> tuple[str | None, str]:
    if engine not in ENGINES:
        fail("Choose openseespy, oofem or code_aster.")
    home = Path.home() / ".local/share/tee/structural"
    default = {
        "openseespy": str(home / "opensees-env/bin/python"),
        "oofem": str(home / "oofem-3.0-build/oofem"),
        "code_aster": "run_aster",
    }
    key = {"openseespy": "opensees_python", "oofem": "oofem", "code_aster": "code_aster"}[engine]
    name = cfg.get(key, default[engine])
    if not isinstance(name, str) or not name or "\x00" in name:
        fail(f"[structural] {key} must name an executable path, not a command.")
    launcher = cfg.get("aster_launcher", "run_aster")
    if launcher not in ("as_run", "run_aster"):
        fail("aster_launcher must be as_run or run_aster.")
    found = shutil.which(name)
    if found is None and key not in cfg:
        found = (
            shutil.which(
                {"openseespy": "python3", "oofem": "oofem", "code_aster": launcher}[engine]
            )
            if engine != "openseespy"
            else None
        )
    return found, launcher


def scan(cfg: dict) -> dict:
    return {
        "engines": [
            {
                "engine": e,
                "executable": executable(e, cfg)[0],
                "state": "found_unprobed" if executable(e, cfg)[0] else "missing",
            }
            for e in ENGINES
        ],
        "execution": "separate local processes",
        "scope": "planar linear elastic Timoshenko frames",
        "code_aster_validation": "generated-deck only until an actual solver run passes",
        "openseespy_distribution": (
            "internal owner use; commercial redistribution requires separate licence review"
        ),
    }


def execute(command: list[str], root: Path, cancelled: Any, timeout: float) -> dict:
    log = root / "solver.log"
    started = time.monotonic()
    if cancelled.is_set():
        fail("Structural job cancelled before launch.")
    with log.open("xb") as stream:
        env = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
        p = subprocess.Popen(
            command,
            cwd=root,
            stdout=stream,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            env=env,
            start_new_session=True,
        )
        try:
            while p.poll() is None:
                reason = None
                if cancelled.is_set():
                    reason = "cancelled"
                elif time.monotonic() - started > timeout:
                    reason = "timed out"
                if reason:
                    fail("Structural solver " + reason + ".")
                _check_output_limit(root)
                time.sleep(0.05)
        finally:
            # Always stop surviving descendants, including a launcher that exited
            # before its children. These processes belong to this run only.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(p.pid, signal.SIGTERM)
            if p.poll() is None:
                with contextlib.suppress(subprocess.TimeoutExpired):
                    p.wait(timeout=0.2)
            # A descendant can survive after its parent exits or ignore TERM.
            with contextlib.suppress(ProcessLookupError):
                os.killpg(p.pid, signal.SIGKILL)
            p.wait(timeout=2)
        if cancelled.is_set():
            fail("Structural job cancelled.")
        if p.returncode:
            fail(f"Solver exited {p.returncode}; inspect {log}.")
    # A solver may finish between polls, including before the first poll. Check
    # its final files before any parser or evidence hashing can read them.
    _check_output_limit(root)
    return {
        "seconds": round(time.monotonic() - started, 4),
        "returncode": p.returncode,
        "executable": command[0],
        "executable_sha256": _file_sha256(Path(command[0]).resolve(), maximum=None),
    }


def parse_oofem(root: Path, m: dict) -> dict:
    text = _result_text(root / "analysis.out")
    if "Finishing analysis on:" not in text:
        fail("OOFEM output has no completion marker.")
    number = r"[-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?"
    disp = {}
    reactions = {n["id"]: [0.0, 0.0, 0.0] for n in m["nodes"]}
    forces = {}
    for tag, body in re.findall(r"Node\s+(\d+)\s+\(\s*\d+\):\s*(.*?)(?=\nNode|\n\n)", text, re.S):
        found = {
            int(d): float(v) for d, v in re.findall(r"dof\s+(\d+)\s+d\s+(" + number + ")", body)
        }
        if set(found) != {1, 3, 5}:
            fail("Incomplete OOFEM node displacement row.")
        idx = int(tag) - 1
        if idx < 0 or idx >= len(m["nodes"]):
            fail("Unexpected OOFEM node.")
        ident = m["nodes"][idx]["id"]
        if ident in disp:
            fail("Repeated OOFEM solution; expected one step.")
        disp[ident] = [found[1], found[3], -found[5]]
    seen = set()
    for tag, dof, v in re.findall(
        r"Node\s+(\d+)\s+iDof\s+(\d+)\s+reaction\s+(" + number + ")", text
    ):
        i, d = int(tag) - 1, int(dof)
        if not 0 <= i < len(m["nodes"]) or d not in (1, 3, 5) or (i, d) in seen:
            fail("Unexpected/repeated OOFEM reaction.")
        seen.add((i, d))
        j = {1: 0, 3: 1, 5: 2}[d]
        reactions[m["nodes"][i]["id"]][j] = float(v) * (-1 if j == 2 else 1)
    ni = {n["id"]: i for i, n in enumerate(m["nodes"])}
    expected = {
        (ni[s["node"]], d)
        for s in m["supports"]
        for d, f in zip((1, 3, 5), s["fixed"], strict=True)
        if f
    }
    if seen != expected:
        fail("Incomplete OOFEM support reactions.")
    for tag, line in re.findall(
        r"beam element\s+(\d+)\s+\(.*?local end forces\s+([^\n]+)", text, re.S
    ):
        i = int(tag) - 1
        if not 0 <= i < len(m["elements"]):
            fail("Unexpected OOFEM member.")
        ident = m["elements"][i]["id"]
        if ident in forces:
            fail("Repeated OOFEM member result.")
        v = [float(x) for x in line.split()]
        if len(v) != 6:
            fail("Incomplete OOFEM member force vector.")
        forces[ident] = [v[0], v[1], -v[2], v[3], v[4], -v[5]]
    return {
        "engine_version": text.split("Starting analysis on:")[0][-500:].strip(),
        "convergence_code": 0,
        "displacements": disp,
        "reactions": reactions,
        "element_forces": forces,
    }


def solve(root: Path, m: dict, loads: dict, engine: str, cfg: dict, cancelled: Any) -> dict:
    path, launcher = executable(engine, cfg)
    if path is None:
        fail(
            f"{engine} is not installed/configured; set its executable in [structural]. "
            "No substitute result was calculated."
        )
    timeout = cfg.get("timeout_s", 120)
    if type(timeout) not in (int, float) or not 1 <= timeout <= 600:
        fail("structural timeout_s must be between 1 and 600.")
    if engine == "openseespy":
        files = decks.write_opensees(root, m, loads)
        command = [path, "analysis.py"]
    elif engine == "oofem":
        files = decks.write_oofem(root, m, loads)
        command = [path, "-f", "analysis.in"]
    else:
        files = decks.write_aster(root, m, loads, launcher)
        command = [path] + (["--run"] if launcher == "as_run" else []) + ["analysis.export"]
    before = {f: _file_sha256(root / f) for f in files}
    (root / "deck-manifest-before.json").write_text(json.dumps(before, indent=2))
    identity = execute(command, root, cancelled, float(timeout))
    if engine == "oofem":
        raw = parse_oofem(root, m)
    else:
        p = root / "solver-result.json"
        raw = json.loads(_result_text(p))
    if not isinstance(raw, dict):
        fail("Solver result must be an object.")
    if raw.get("convergence_code") != 0:
        fail("Solver did not converge.")
    identity.update(
        {
            "engine": engine,
            "engine_version": raw.get("engine_version"),
            "native_output_files": {
                str(p.relative_to(root)): _file_sha256(p)
                for p in root.iterdir()
                if p.is_file() and p.name not in files
            },
            "decks_before": before,
            "decks_after": {f: _file_sha256(root / f) for f in files},
        }
    )
    return {"raw": raw, "identity": identity}
