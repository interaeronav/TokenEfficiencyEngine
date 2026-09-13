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


# What `_chore` below asks for on the wire. It calls the chore layer without a
# `thinking` argument, so it inherits the chore default: OFF. The audition row
# records the mode measured, and this is the one place that says what it is.
_CHORE_REQUESTS_THINKING: bool | None = None


def _chore(cfg: dict[str, Any], max_tokens: int | None = None):
    """One triage against this endpoint, graded by triage's own validator.

    `max_tokens` reaches for the chore's shared `_run` seam because `triage`
    fixes it at 220 - the sweep needs to vary exactly that. The system prompt
    and the validator are the chore's, so a pass here is a pass at the real bar.
    """
    from tee.llm import chores, profiles

    # The helper is also used by direct-module floor probes. The engine lane
    # never spends, even when a caller's ordinary chore grants permit it.
    if profiles.resolve(cfg).get("paid"):
        raise TeeError(
            "eng_paid_refused",
            "The engine lane cannot probe a paid profile.",
            fix="Select an explicit local candidate for this measurement.",
        )

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
        _measure_exact_budget=True,
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
        "budget_mode": "exact-wire",
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


def _candidate_cfg(cfg: dict[str, Any], *, engine: str, url: str, model: str) -> dict[str, Any]:
    """Resolve the requested candidate independently of the owner's live pin.

    Top-level url/model lose to a named profile. Copy an explicit candidate
    profile instead, after preserving the lane's refusal of paid models. No
    persisted profile, loading state, adopted floor or model lifecycle changes
    belong to this measurement.
    """
    from tee.kernel import local_llm, machine
    from tee.llm import profiles

    url, model = url.strip().rstrip("/"), model.strip()
    if not url or not model:
        raise TeeError(
            "eng_needs_endpoint",
            "An audition needs an explicit nonempty endpoint and model.",
            fix="Use eng_scan to identify the local candidate to measure.",
        )
    declared = profiles.profiles(cfg)
    for spec in declared.values():
        named = spec.get("model") or cfg.get("model") or local_llm.DEFAULT_MODEL
        if spec.get("paid") and named == model:
            raise TeeError(
                "eng_paid_refused",
                f"{model!r} is declared paid; the engine lane never measures it.",
                fix="Audition a local model that is not marked paid.",
            )

    profile = machine.ENGINES.get(engine, {}).get("profile") or "__tee_audition__"
    old = declared.get(profile, {})
    # Never attach the owner's 14B LoRA to an unrelated candidate model.
    adapters = ""
    if old.get("model") == model:
        adapters = old.get("adapters") or ""
    elif cfg.get("model") == model:
        adapters = cfg.get("adapters") or ""
    candidate = {"url": url, "model": model, "adapters": adapters, "paid": False}
    # Carry the engine's own thinking / json_mode, or the audition measures a
    # DIFFERENT engine than the one the router will use: a thinking profile
    # auditioned thinking-off yields a token floor and a latency band that
    # nothing in production will ever reproduce.
    for key in ("thinking", "json_mode"):
        if key in old:
            candidate[key] = old[key]
    hop = dict(cfg, _profile=profile, profiles={**declared, profile: candidate})
    hop.pop("_state_dir", None)
    return hop


def audition(
    cfg: dict[str, Any], *, engine: str, url: str, model: str, samples: int = WARM_SAMPLES
) -> dict[str, Any]:
    """A candidate engine row, measured. Never called for a paid profile."""
    from tee.llm import chores, profiles

    hop = _candidate_cfg(cfg, engine=engine, url=url, model=model)
    resolved = profiles.resolve(hop)
    row: dict[str, Any] = {
        "engine": engine,
        "url": resolved["url"],
        "model": resolved["model"],
        "adapters": resolved["adapters"],
        # The mode this measurement is MEASURED AT, derived the same way the
        # request derives it - not the profile's capability flag. `_chore`
        # below passes no `thinking`, so this is off today even on a
        # thinking-capable profile; if `_chore` ever opts in, change
        # _CHORE_REQUESTS_THINKING beside it and the row follows.
        #
        # Omitting this key entirely was the bug: `matching_floors` read a
        # missing key as False and compared it to the profile's True, so
        # q27b-think discarded its own floor forever. Found by review.
        "thinking": chores.wire_thinking(
            "triage", requested=_CHORE_REQUESTS_THINKING, resolved=resolved
        ),
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
