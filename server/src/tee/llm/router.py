"""Verifier-gated cascade router (A42 R1 = A39 R1 + the A41 guard seam).

Chores WITH deterministic verifiers ride the ladder: the resident local
engine first -> the chore's own deterministic verdict -> the bigger local
engine, used directly when resident and reached by swap ONLY when the one
machine ledger says the machine is capable -> the budgeted client brief
as the final tier. The owner's explicit TEE/Q pin suspends roaming
entirely. Chores without a deterministic verifier stay static until R3's
calibration rows say otherwise - uncalibrated confidence gates nothing.

Every hop is recorded (engine, verdict, why a rung was skipped) and the
whole trace rides the return value - provenance and meter columns join in
R2. The escalation brief is a budgeted TEE response: the task, the input
POINTER and the named failures - never the raw content re-dumped. QoS is
a LABEL here (seam 3); K1 makes it law.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from tee.kernel import shadow
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.kernel.machine import ENGINES, MachineLedger
from tee.llm import profiles

# Ladder order among local engines; the resident engine is always tried
# first (it costs nothing to use what is already loaded).
LADDER = ("q14b+a2", "q27b-bare")
BRIEF_TOKEN_CAP = 200

_PROFILE_TO_ENGINE = {
    spec["profile"]: name for name, spec in ENGINES.items() if spec.get("profile")
}


def _hop_cfg(cfg: dict[str, Any], engine: str) -> dict[str, Any]:
    return dict(cfg, _profile=ENGINES[engine]["profile"])


def route(
    chore: str,
    call: Callable[[dict[str, Any]], dict[str, Any] | None],
    *,
    cfg: dict[str, Any] | None,
    ledger: MachineLedger,
    input_pointer: str,
) -> dict[str, Any]:
    """Run `call(hop_cfg)` up the ladder; `call` must invoke the chore with
    refine='local' so a verifier kill surfaces as TeeError and an
    empty-but-valid answer as None - both are deterministic verdicts."""
    cfg = dict(cfg or {})
    started = time.monotonic()
    state = profiles.load_state(cfg)
    resident = _PROFILE_TO_ENGINE.get(state["active"], LADDER[0])
    pinned = bool(state.get("pinned"))
    ladder = [resident] if pinned else [resident, *[e for e in LADDER if e != resident]]
    hops: list[dict[str, Any]] = []
    for engine in ladder:
        if engine != resident:
            capable, reason = ledger.may_swap(engine)
            if not capable:
                hops.append({"engine": engine, "skipped": reason})
                continue
        try:
            result = call(_hop_cfg(cfg, engine))
        except TeeError as exc:
            hops.append({"engine": engine, "verdict": exc.code})
            continue
        if result is None:
            hops.append({"engine": engine, "verdict": "empty_result"})
            continue
        hops.append({"engine": engine, "verdict": "verified"})
        _record(chore, input_pointer, engine, hops, resident, started, "verified")
        return {
            "ok": True,
            "engine": engine,
            "result": result,
            "hops": hops,
            "pinned": pinned,
            "qos": "interactive",
        }
    _record(chore, input_pointer, None, hops, resident, started, "escalated")
    return {
        "ok": False,
        "escalate": _brief(chore, input_pointer, hops, pinned),
        "hops": hops,
        "pinned": pinned,
        "qos": "interactive",
    }


def _record(
    chore: str,
    pointer: str,
    engine: str | None,
    hops: list[dict[str, Any]],
    resident: str,
    started: float,
    outcome: str,
) -> None:
    """The K0 shadow trace: what ran vs what greedy WOULD have placed."""
    shadow.record(
        shadow.TaskDescriptor(
            id=f"chore:{chore}",
            kind="chore",
            qos="interactive",
            engine=engine,
            verifier="deterministic",
            inputs=[pointer],
        ),
        {
            "outcome": outcome,
            "wall_s": round(time.monotonic() - started, 2),
            "hops": len(hops),
            "_resident": resident,
        },
    )


def _brief(
    chore: str, input_pointer: str, hops: list[dict[str, Any]], pinned: bool
) -> dict[str, Any]:
    """The client tier's hand-back: budgeted, pointer-only, failures named."""
    failures = []
    for hop in hops:
        if "verdict" in hop:
            failures.append(f"{hop['engine']}: {hop['verdict']}")
        else:
            failures.append(f"{hop['engine']}: skipped ({hop['skipped']})")
    brief = {
        "task": chore,
        "input": input_pointer,
        "local_attempts": failures,
        "next": "the client answers directly from the pointed input",
    }
    if pinned:
        brief["note"] = "roaming suspended by the owner's TEE/Q pin"
    while estimate_tokens(str(brief)) > BRIEF_TOKEN_CAP and brief["local_attempts"]:
        brief["local_attempts"] = [*brief["local_attempts"][:-1], "..."]
        if brief["local_attempts"] == ["..."]:
            break
    return brief
