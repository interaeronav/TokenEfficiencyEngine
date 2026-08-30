"""A45 P2 — the stdout guard the whole fleet runs inside.

TEE speaks JSON-RPC over **stdio**. Anything written to file descriptor 1
that is not a protocol frame corrupts the stream and can desynchronise the
client. Solver and CAD libraries are native code and they are chatty:

    >>> s = pywraplp.Solver.CreateSolver("HIGHS"); s.Solve()
    Running HiGHS 1.12.0 (git hash: 755a8e02): Copyright (c) 2025 HiGHS
    under MIT licence terms

92 bytes, unbidden, on every single solve.

**`contextlib.redirect_stdout` does not stop this, and believing it does is
the trap.** That helper rebinds the Python object `sys.stdout`; the banner
is written by C++ straight to fd 1 and never passes through it. Measured
here: under `redirect_stdout` the captured buffer was 0 bytes and the
banner still reached the terminal. The guard has to be `os.dup2` at the
descriptor level, which is what this module does.

Kept in the kernel-adjacent fleet package rather than each adapter because
"a fleet call may never write to stdout" is a property of the SERVER, not
a courtesy each integration remembers - and it has its own test.
"""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
from collections.abc import Iterator


@contextlib.contextmanager
def muted_stdout(capture: bool = True) -> Iterator[str]:
    """Redirect fd 1 for the duration; yield what was swallowed.

    The yielded value is a one-element list-like holder only after exit, so
    callers that want the text use `with muted_stdout() as sink:` and read
    `sink.text` afterwards. Kept deliberately dumb: no threads, no pipes
    (a pipe can deadlock if the child writes more than the buffer), just a
    temp file we read back.
    """
    sink = _Sink()
    sys.stdout.flush()
    saved = os.dup(1)
    with tempfile.TemporaryFile(mode="w+b") as tmp:
        try:
            os.dup2(tmp.fileno(), 1)
            yield sink
        finally:
            with contextlib.suppress(Exception):
                sys.stdout.flush()
            os.dup2(saved, 1)
            os.close(saved)
            if capture:
                with contextlib.suppress(Exception):
                    tmp.seek(0)
                    sink.text = tmp.read().decode("utf-8", errors="replace")


class _Sink:
    """Holder so the caller can read the swallowed text after the block."""

    __slots__ = ("text",)

    def __init__(self) -> None:
        self.text = ""

    def __repr__(self) -> str:  # pragma: no cover - debugging convenience
        return f"<swallowed {len(self.text)} chars>"


def quiet(fn, *args, **kwargs):
    """Call `fn` with fd 1 muted; return (result, swallowed_text).

    Every fleet entry point that can reach native code goes through this.
    The swallowed text is not discarded - it is returned so a diagnose tool
    can show a solver's own log on request, which is the honest place for
    it: available when asked, never on the protocol stream.
    """
    with muted_stdout() as sink:
        result = fn(*args, **kwargs)
    return result, sink.text
