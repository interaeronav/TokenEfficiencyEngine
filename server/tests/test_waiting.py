"""A51 P0 — the wait must not be the slow part.

Measured before this module existed: the Blender bridge answered in ~0.30 s
and TEE noticed at 0.50 s, because every launcher polled on a fixed 0.5 s
tick. Nobody was waiting on an engine; they were waiting on a sleep.
"""

from __future__ import annotations

import time

from tee.kernel.waiting import wait_until


def test_something_already_up_costs_no_delay_at_all():
    """The common case - another session left the bridge running."""
    started = time.monotonic()
    waited = wait_until(lambda: True, 5.0)
    assert waited is not None and waited < 0.01
    assert time.monotonic() - started < 0.05


def test_a_fast_start_is_noticed_fast():
    """The defect in one assertion: a service ready at 0.10 s must be seen
    at ~0.10 s, not at the next multiple of a fixed tick."""
    ready_at = time.monotonic() + 0.10
    waited = wait_until(lambda: time.monotonic() >= ready_at, 5.0)
    assert waited is not None
    assert waited < 0.18, f"noticed after {waited:.3f}s - the poll is quantised again"


def test_it_gives_up_and_says_so():
    waited = wait_until(lambda: False, 0.3)
    assert waited is None


def test_a_slow_start_is_not_hammered():
    """Backoff, not a tight spin: a service taking a while must not be
    polled hundreds of times a second."""
    calls = []

    def never():
        calls.append(time.monotonic())
        return False

    wait_until(never, 0.8)
    assert len(calls) < 25, f"{len(calls)} probes in 0.8 s is a spin, not a wait"


def test_the_launchers_use_it():
    """Asserted on source: a fixed-interval sleep in a launch wait is the
    defect, and it should not creep back."""
    import inspect
    import pathlib

    from tee.adapters.godot import adapter as godot

    godot_src = inspect.getsource(godot.GodotAdapter.ensure_bridge)
    assert "time.sleep(0.4)" not in godot_src
    assert "MAX_DELAY_S" in godot_src

    bench = pathlib.Path(__file__).resolve().parents[2] / "benchmarks/run_benchmarks.py"
    text = bench.read_text()
    assert "wait_until(wire.probe" in text
    assert "while time.time() < deadline and not wire.probe():" not in text
