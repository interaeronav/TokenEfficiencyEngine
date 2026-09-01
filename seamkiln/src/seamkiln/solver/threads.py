"""Sizes numba's thread pool before numba is imported. Import this first.

A53 P0b measured the reason: at garment sizes the fork/join barrier around
each parallel region costs more than the region saves, and the barrier scales
with POOL size. `numba.set_num_threads(1)` on a pool of 18 costs 11.6 ms
where `NUMBA_NUM_THREADS=1` at process start costs 2.3 - it masks threads
without shrinking the barrier - so the pool has to be sized by the
environment, before the first import, which is what this module does.

Four is the measured optimum from ~50k particles up, and never worse than a
couple of milliseconds below it. Eighteen cores never win at any size.
"""

from __future__ import annotations

import os
import sys

DEFAULT_THREADS = "4"

if "numba" in sys.modules:
    POOL_NOTE = (
        " (numba was imported before seamkiln, so NUMBA_NUM_THREADS could not be "
        "set - expect the barrier cost documented in solver/threads.py)"
    )
else:
    os.environ.setdefault("NUMBA_NUM_THREADS", DEFAULT_THREADS)
    POOL_NOTE = ""
