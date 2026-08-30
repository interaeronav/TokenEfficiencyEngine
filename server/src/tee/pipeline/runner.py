"""The argv runner (A43 P0b/P1): the only place the pipeline executes.

One function runs a command, and it can only ever run an ARGV LIST with
`shell=False`. There is no code path here that accepts a command string,
because the moment one exists every other guarantee in the lane becomes a
promise instead of a property. A fixture asserts this against the AST.

What the runner contributes beyond `subprocess.run`:

* **bounded capture** - output is tail-trimmed, so a failing step returns
  one honest line plus the tail, never a log flood;
* **a wall clock and an exit code**, which are the two facts a report
  actually needs;
* **a touched-file observation** - what the run created or modified under
  the project root, which is what makes the adopt flow able to propose
  `outputs` the owner can check rather than guess.
"""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from tee.kernel.errors import TeeError

DEFAULT_TIMEOUT_S = 900.0
TAIL_CHARS = 2000
# Directories a build legitimately churns; scanning them would drown the
# adopt proposal in noise rather than naming the artifacts.
_SKIP_DIRS = {".git", ".tee", "__pycache__", ".venv", "node_modules", ".mypy_cache"}
_MAX_SCAN = 20_000


@dataclass
class RunResult:
    argv: list[str]
    exit_code: int
    wall_s: float
    stdout_tail: str = ""
    stderr_tail: str = ""
    created: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    def failure_line(self, step: str) -> str:
        """Rule 6: one short message naming the step, not a stack novel."""
        tail = (self.stderr_tail or self.stdout_tail or "").strip().splitlines()
        last = tail[-1] if tail else "(no output)"
        return f"step '{step}' exited {self.exit_code}: {last[:200]}"


def _tail(text: str) -> str:
    if len(text) <= TAIL_CHARS:
        return text
    return "…" + text[-TAIL_CHARS:]


def _snapshot(root: Path) -> dict[str, float]:
    """Cheap mtime map of the project tree, bounded so a huge repo cannot
    turn an adopt proposal into a stall."""
    seen: dict[str, float] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        for filename in filenames:
            path = Path(dirpath) / filename
            try:
                seen[str(path.relative_to(root))] = path.stat().st_mtime
            except OSError:
                continue
            if len(seen) >= _MAX_SCAN:
                return seen
    return seen


def run(
    argv: list[str],
    *,
    cwd: Path,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    observe: bool = False,
    env: dict[str, str] | None = None,
) -> RunResult:
    """Execute one argv list. No shell, ever - the list IS the boundary."""
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise TeeError(
            "pipeline_bad_argv",
            "argv must be a non-empty list of strings.",
            fix='Pass argv = ["python", "build.py"] - never a command string.',
        )
    cwd = Path(cwd)
    if not cwd.is_dir():
        raise TeeError(
            "pipeline_bad_cwd",
            f"The project root {cwd} does not exist.",
            fix="Run from a real project directory.",
        )
    before = _snapshot(cwd) if observe else {}
    started = time.time()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            # The declared environment is an OVERLAY, not a replacement: the
            # owner's scripts need the shell they were written for (HOME,
            # PATH, a conda prefix), and a scrubbed environment would only
            # move the breakage somewhere less legible.
            env={**os.environ, **env} if env else None,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        raise TeeError(
            "pipeline_command_missing",
            f"'{argv[0]}' is not on PATH.",
            fix='Install it, or declare the interpreter explicitly (argv = ["python3", ...]).',
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise TeeError(
            "pipeline_timeout",
            f"'{argv[0]}' exceeded {timeout_s:.0f}s and was stopped.",
            fix="Raise the step's timeout, or make the step smaller.",
        ) from exc
    wall = time.time() - started
    result = RunResult(
        argv=list(argv),
        exit_code=completed.returncode,
        wall_s=round(wall, 2),
        stdout_tail=_tail(completed.stdout or ""),
        stderr_tail=_tail(completed.stderr or ""),
    )
    if observe:
        after = _snapshot(cwd)
        result.created = sorted(k for k in after if k not in before)[:20]
        result.modified = sorted(k for k, m in after.items() if k in before and m > before[k])[:20]
    return result
