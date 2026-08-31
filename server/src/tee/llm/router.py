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
def _ladder() -> tuple[str, ...]:
    """Cheapest-capable first, ORDERED BY THE MEASURED TABLE rather than by
    hand (A46 P3b).

    The hand-written ladder was ("q14b+a2", "q27b-bare"), which on this
    machine leads with a 14B the shim does not serve - a dead first hop -
    and then lands on the 27B at a measured 27.78 s, while the free
    DeepSeek-Flash route answers the same chore in 4.41 s and was not in
    the ladder at all. Deriving the order means registering an engine is
    enough to make it reachable, and a machine that DOES serve a 14B still
    gets it first because its measured cost says so.

    A dead hop is not an error: the router already treats an unreachable
    engine as a failed hop and moves down. Paid engines are absent from
    ENGINES entirely, so no ordering can promote one into the ladder.
    """

    def cost(name: str) -> float:
        c = ENGINES[name].get("cost") or {}
        lat = c.get("latency_s")
        return float(lat[1]) if isinstance(lat, list) and len(lat) > 1 else 1e6

    chore_engines = [
        n
        for n, spec in ENGINES.items()
        if spec.get("kind") == "llm" and "chores" in (spec.get("capability") or [])
    ]
    return tuple(sorted(chore_engines, key=cost))


LADDER = _ladder()
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
    policy: str = "static",
) -> dict[str, Any]:
    """Run `call(hop_cfg)` up the ladder; `call` must invoke the chore with
    refine='local' so a verifier kill surfaces as TeeError and an
    empty-but-valid answer as None - both are deterministic verdicts.

    policy: 'static' = resident-first, today's behavior; 'greedy' = the K2
    cost-aware earliest-finish order from the registry's measured tables -
    live ONLY behind `[scheduler] dispatch = true`, replay-gated first.
    The owner's pin outranks both."""
    cfg = dict(cfg or {})
    started = time.monotonic()
    state = profiles.load_state(cfg)
    resident = _PROFILE_TO_ENGINE.get(state["active"], LADDER[0])
    pinned = bool(state.get("pinned"))
    if pinned:
        ladder = [resident]
        reason = f"pinned: owner holds {resident}"
    elif policy == "greedy":
        choice = shadow.greedy_choice("chore", resident=resident)
        first = choice.get("engine") or resident
        ladder = [first, *[e for e in LADDER if e != first]]
        reason = f"greedy: {first} est {choice.get('estimate_s')}s ({choice.get('reason')})"
    else:
        ladder = [resident, *[e for e in LADDER if e != resident]]
        reason = f"static: resident-first {resident}"
    ledger.record_dispatch("pinned" if pinned else policy, reason)
    ledger.record_task()
    hops: list[dict[str, Any]] = []
    declared = profiles.profiles(cfg)
    for engine in ladder:
        # A rung whose profile this machine has not declared is NOT a failed
        # attempt (A46 P3b). It used to raise llm_unknown_profile inside the
        # call and land in the `except TeeError` arm, which recorded a
        # verification failure against an engine that was never asked
        # anything - inflating the escalation rate with absent hardware.
        # Registering an engine centrally must not defame it on machines
        # that do not serve it.
        if ENGINES[engine]["profile"] not in declared:
            hops.append({"engine": engine, "skipped": "profile not declared here"})
            continue
        if engine != resident:
            capable, reason = ledger.may_swap(engine)
            if not capable:
                hops.append({"engine": engine, "skipped": reason})
                ledger.record_swap(refused=reason)
                continue
            ledger.record_swap(implicit=True)  # mlx loads the model per request
        try:
            result = call(_hop_cfg(cfg, engine))
        except TeeError as exc:
            hops.append({"engine": engine, "verdict": exc.code})
            ledger.record_route(engine, verified=False)
            continue
        if result is None:
            hops.append({"engine": engine, "verdict": "empty_result"})
            ledger.record_route(engine, verified=False)
            continue
        hops.append({"engine": engine, "verdict": "verified"})
        ledger.record_route(engine, verified=True)
        _record(chore, input_pointer, engine, hops, resident, started, "verified", reason)
        return {
            "ok": True,
            "engine": engine,
            "result": result,
            "hops": hops,
            "pinned": pinned,
            "qos": "interactive",
        }
    ledger.record_escalation()
    _record(chore, input_pointer, None, hops, resident, started, "escalated", reason)
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
    reason: str,
) -> None:
    """The K0 shadow trace: what ran vs what greedy WOULD have placed,
    plus the K2 dispatch reason - decisions are data."""
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
            "dispatch": reason,
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
