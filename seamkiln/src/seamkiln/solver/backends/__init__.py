"""Solver backends. Each exposes `available() -> (bool, why)` and `simulate()`.

`available` never raises and never lies about the device it got: a backend
that reports "warp cpu" on this Mac is telling the truth that matters.
"""
