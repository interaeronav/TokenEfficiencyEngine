"""Measure an engine by making it do TEE's own work, graded by TEE's own judge.

This is the part of the lane that cannot be read out of any file. The registry's
`cost.latency_s`, `min_chore_tokens` and `footprint_gb` are hand-copied literals
stamped with the date of the session that produced them; an audition produces
them again, on this machine, against this endpoint, with the chore's own
deterministic validator as the grader.

Two rules the numbers carry with them:

* **A latency without a warm/cold label is a lie.** The first call to an mlx
  endpoint loads the weights; every one after that does not. Both are reported,
  and the ladder sorts on warm.
* **A row is about an ENDPOINT serving a MODEL**, not about the weights. A
  proxy in front adds its own latency, so the row records the url and the
  server fingerprint beside the number.
"""

from __future__ import annotations

import statistics
import time
from typing import Any

from tee.kernel.errors import TeeError

#: A real failure, so the chore is doing its real work rather than a toy.
FAILURE = (
    "Traceback (most recent call last):\n"
    '  File "populate.py", line 6, in <module>\n'
    "TypeError: spawn_actor() got an unexpected keyword argument 'transform'"
)
CONTEXT = "line 6: actor = world.spawn_actor(bp, transform=tf)"

#: Descending, so the sweep FINDS the floor rather than confirming a guess.
TOKEN_RUNGS = (1024, 512, 384, 256, 192, 128, 96, 64)
WARM_SAMPLES = 3


def _chore(cfg: dict[str, Any], max_tokens: int | None = None):
    """One triage against this endpoint, graded by triage's own validator.

    `max_tokens` reaches for the chore's shared `_run` seam because `triage`
    fixes it at 220 - the sweep needs to vary exactly that. The system prompt
    and the validator are the chore's, so a pass here is a pass at the real bar.
    """
    from tee.llm import chores

    if max_tokens is None:
        return chores.triage(FAILURE, CONTEXT, refine="local", cfg=cfg)

    def validate(raw: dict[str, Any]):
        diagnosis = chores._line(raw.get("diagnosis"), 220)
        fix = chores._line(raw.get("fix"), 300)
        if not diagnosis or not fix:
            return None
        if raw.get("confidence") not in ("grounded", "needs_verification"):
            return None
        return {"diagnosis": diagnosis, "fix": fix}

    evidence = f"Failure evidence:\n{FAILURE}\n\nContext (source/op):\n{CONTEXT}"
    return chores._run(
        chores._TRIAGE_SYSTEM,
        evidence,
        refine="local",
        cfg=cfg,
        max_tokens=max_tokens,
        validate=validate,
    )


def _timed(cfg: dict[str, Any], max_tokens: int | None = None):
    t0 = time.perf_counter()
    try:
        out = _chore(cfg, max_tokens)
        return out, round(time.perf_counter() - t0, 3), None
    except TeeError as exc:
        return None, round(time.perf_counter() - t0, 3), exc.code


def token_floor(cfg: dict[str, Any]) -> dict[str, Any]:
    """The smallest budget at which this model still passes the chore's judge.

    Descending until it fails, so the answer is found and not assumed. The
    registry's only non-default floor was written by hand and belongs to a
    profile this machine does not declare - it has never once been reached.
    """
    passed: list[int] = []
    failed: list[int] = []
    for rung in TOKEN_RUNGS:
        out, _wall, _code = _timed(cfg, rung)
        if out:
            passed.append(rung)
        else:
            failed.append(rung)
            break  # below the floor it will only get worse
    lowest = min(passed) if passed else None
    out = {
        "min_chore_tokens": lowest,
        "passed": passed,
        "first_failure": failed[0] if failed else None,
        "method": f"descending sweep over {list(TOKEN_RUNGS)}, chore's own validator",
    }
    if passed and not failed:
        # It never failed, so the floor is AT OR BELOW the lowest rung tried.
        # Reporting `lowest` as the floor would be a declaration dressed as a
        # measurement - the exact thing this lane exists to stop.
        out["bound"] = "at-or-below"
        out["note"] = (
            f"passed every rung down to {lowest}; the sweep bottomed out without "
            f"finding a failure, so {lowest} is an upper bound on the floor, not the floor"
        )
    elif passed:
        out["bound"] = "exact"
    return out


def audition(
    cfg: dict[str, Any], *, engine: str, url: str, model: str, samples: int = WARM_SAMPLES
) -> dict[str, Any]:
    """A candidate engine row, measured. Never called for a paid profile."""
    hop = dict(cfg, url=url, model=model)
    row: dict[str, Any] = {
        "engine": engine,
        "url": url,
        "model": model,
        "measured_at": time.time(),
    }

    cold, cold_wall, cold_code = _timed(hop)
    row["latency_cold_s"] = cold_wall
    row["cold_verified"] = bool(cold)
    if cold is None and cold_code:
        row["cold_verdict"] = cold_code

    walls: list[float] = []
    verified = 0
    for _ in range(max(1, samples)):
        out, wall, _ = _timed(hop)
        walls.append(wall)
        verified += 1 if out else 0
    row["latency_warm_s"] = [round(min(walls), 3), round(statistics.median(walls), 3)]
    row["verified_rate"] = round(verified / len(walls), 3)
    row["samples"] = len(walls)

    if verified:
        row |= {"floor": token_floor(hop)}
        row["min_chore_tokens"] = row["floor"].get("min_chore_tokens")
    else:
        row["unmeasured"] = (
            "the engine never passed the chore's validator, so no floor was "
            "swept and no latency here is a statement about its quality"
        )
    return row
