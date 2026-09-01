"""A51 P0 — waiting for a service without sleeping through its answer.

Measured before this existed: headless Blender boots in 0.42-0.75 s, or
0.55 s with a 3.8 MB scene loaded, and its bridge answers in ~0.30 s. But
every launcher polled on a fixed 0.5 s interval, so a bridge ready at
0.30 s was not noticed until 0.50 s. `GodotAdapter` did the same at 0.4 s.

Nobody was waiting on an engine. They were waiting on a `sleep`.

The fix is not a shorter fixed interval, which would spin the CPU on a
service that is genuinely slow to start. It is a backoff: check almost
immediately, then ease off, so a fast start is caught at once and a slow
one is not hammered.
"""

from __future__ import annotations

import time
from collections.abc import Callable

# Tuned from measurement, not taste. A failed `probe()` costs 0.1 ms, and
# the Blender bridge is genuinely ready at 0.422 s. A 0.25 s cap put late
# probes further apart than the thing being waited for, so the first
# attempt at this was SLOWER than the fixed 0.5 s tick it replaced
# (0.553 s vs 0.506 s) - overshooting by luck rather than by design.
# At 0.1 ms a probe, a 50 ms cap costs ~20 probes a second and catches a
# 0.422 s start within 50 ms of the truth.
FIRST_DELAY_S = 0.01
MAX_DELAY_S = 0.05
GROWTH = 1.6


def wait_until(
    ready: Callable[[], bool],
    timeout_s: float,
    *,
    first_delay_s: float = FIRST_DELAY_S,
    max_delay_s: float = MAX_DELAY_S,
) -> float | None:
    """Poll `ready` with backoff. Returns seconds waited, or None on timeout.

    The first check happens before any sleep: a service that is already up -
    the common case when something else launched it - costs one call and no
    delay at all.
    """
    started = time.monotonic()
    delay = first_delay_s
    while True:
        if ready():
            return time.monotonic() - started
        if time.monotonic() - started >= timeout_s:
            return None
        time.sleep(min(delay, max_delay_s, max(0.0, timeout_s - (time.monotonic() - started))))
        delay *= GROWTH
