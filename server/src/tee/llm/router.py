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

import hashlib
import json
import marshal
import time
import uuid
from collections.abc import Callable
from contextlib import suppress
from functools import lru_cache
from typing import Any

from tee.kernel import shadow
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.kernel.machine import ENGINES, MachineLedger
from tee.llm import profiles


# Ladder order among local engines; the resident engine is always tried
# first (it costs nothing to use what is already loaded).
def _ladder(measured: dict[str, Any] | None = None) -> tuple[str, ...]:
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

    # A76 P3: a MEASURED row outranks the literal. The registry's latency is a
    # hand-copied number stamped with the date of the session that produced it;
    # a row written by eng_audition is evidence. The literal stays as the
    # fallback, so a machine that has never auditioned behaves exactly as
    # before, and `LADDER` below remains importable for the tests that pin it.
    def cost(name: str) -> float:
        row = (measured or {}).get(name) or {}
        warm = row.get("latency_warm_s")
        if isinstance(warm, list) and len(warm) > 1:
            return float(warm[1])
        if isinstance(warm, (int, float)):
            return float(warm)
        c = ENGINES.get(name, {}).get("cost") or {}
        lat = c.get("latency_s")
        return float(lat[1]) if isinstance(lat, list) and len(lat) > 1 else 1e6

    chore_engines = [
        n
        for n, spec in ENGINES.items()
        # `ladder: False` opts a row OUT of the cascade without denying what it
        # can do. q27b-bare is the case: it runs chores perfectly well when the
        # owner pins TEE/Q27B, but it was measured to fail on the identical
        # tasks as q27b-think (rho = 1.00, same weights on two backends), so as
        # a RUNG it could recover nothing the rung above it had not already got
        # wrong. Capability and cascade membership are different questions.
        if (
            spec.get("kind") == "llm"
            and "chores" in (spec.get("capability") or [])
            and spec.get("ladder", True)
        )
    ]
    return tuple(sorted(chore_engines, key=cost))


def measured_rows(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Rows eng_adopt has written, or {} - the router never requires the lane."""
    try:
        from tee.engines.table import load_measured

        return load_measured((cfg or {}).get("_state_dir"))
    except Exception:  # pragma: no cover - the router must never fail on this
        return {}


LADDER = _ladder()
BRIEF_TOKEN_CAP = 200

#: Codes meaning the engine was never reached, so nothing about the MODEL was
#: learned. Anything else from the call is a verdict on what it answered.
UNREACHABLE_CODES = frozenset({"llm_unreachable"})
# A80 labels only the EXISTING chore validator's acceptance. For triage this
# is a schema check; it is never evidence that a diagnosis or CAD model is right.
VERIFIER_FAILURE_CODES = frozenset({"llm_bad_shape", "llm_bad_json"})
_CHORE_NAMES = frozenset(
    {
        "triage",
        "repair_script",
        "explain_lint",
        "refine_extract",
        "structure_facts",
        "compress_recap",
        "rerank",
        "phrase_deviation",
    }
)

_PROFILE_TO_ENGINE = {
    spec["profile"]: name for name, spec in ENGINES.items() if spec.get("profile")
}


def _finish_s(engine: str, measured: dict[str, Any] | None = None) -> float:
    """When a NON-RESIDENT rung would finish: its latency plus its load cost.

    A cold model is not free. `cost()` in `_ladder` compares latency only,
    which is the right question for a table that cannot know what is resident
    and the wrong one for a live ladder that can.
    """
    row = ENGINES.get(engine, {})
    warm = (measured or {}).get(engine, {}).get("latency_warm_s")
    if isinstance(warm, list) and len(warm) > 1:
        latency = float(warm[1])
    elif isinstance(warm, (int, float)):
        latency = float(warm)
    else:
        band = (row.get("cost") or {}).get("latency_s")
        latency = float(band[1]) if isinstance(band, list) and len(band) > 1 else 1e6
    try:
        return latency + float(row.get("eta_s") or 0.0)
    except (TypeError, ValueError):
        return latency


def _hop_cfg(cfg: dict[str, Any], engine: str) -> dict[str, Any]:
    return dict(cfg, _profile=ENGINES.get(engine, {}).get("profile"))


@lru_cache(maxsize=128)
def _code_version(codes: tuple[Any, ...]) -> str:
    return hashlib.sha256(marshal.dumps(codes)).hexdigest()


def _learning_context(chore: str) -> str:
    # Only fixed built-in identifiers are retained; unknown caller text does
    # not enter the store or model even as a hash of that text.
    return "chore:" + (chore if chore in _CHORE_NAMES else "unknown")


def _learning_version(chore: str, call: Callable, cfg: dict[str, Any], engine: str) -> str:
    from tee.kernel import local_llm
    from tee.llm import chores

    # Hash the compiled validator (including nested validate), shared runner,
    # string normalizer, and actual callback. Neither source nor URLs leave here.
    functions = (
        getattr(chores, chore, None) if chore in _CHORE_NAMES else None,
        chores._run,
        chores._line,
        local_llm.complete_json,
        local_llm._parse_json_object,
        call,
    )
    codes = tuple(getattr(fn, "__code__", None) for fn in functions)
    code = _code_version((chores.REVISION, *codes))
    profile = ENGINES.get(engine, {}).get("profile")
    if profile in profiles.profiles(cfg):
        resolved = profiles.resolve(_hop_cfg(cfg, engine))
        # `thinking` is part of the engine's identity for learning: the same
        # weights with reasoning on and off are two different behaviours -
        # measured 6/6 vs 5/6 on the trap suite - so evidence gathered under
        # one must not be reused under the other.
        identity = {
            k: resolved.get(k) for k in ("profile", "model", "url", "adapters", "paid", "thinking")
        }
    else:
        identity = {"profile": profile, "undeclared": True}
    payload = json.dumps(["route_v1", code, identity], sort_keys=True, separators=(",", ":"))
    return "route_v1:" + hashlib.sha256(payload.encode()).hexdigest()


def _local_candidate(cfg: dict[str, Any], engine: str) -> bool:
    spec = ENGINES.get(engine, {})
    if spec.get("kind") != "llm" or "chores" not in spec.get("capability", []):
        return False
    declared = profiles.profiles(cfg)
    if spec.get("profile") not in declared or declared[spec["profile"]].get("enabled") is False:
        return False
    resolved = profiles.resolve(_hop_cfg(cfg, engine))
    return bool(resolved.get("ready")) and not resolved.get("paid", False)


def _learned_order(
    service: Any,
    context: str,
    chore: str,
    call: Callable,
    cfg: dict[str, Any],
    ladder: list[str],
    resident: str,
    ledger: MachineLedger,
) -> tuple[list[str], bool]:
    """A recommendation can only permute the current eligible local choices."""
    try:
        candidates = [
            {"choice": engine, "version": _learning_version(chore, call, cfg, engine)}
            for engine in ladder
            if _local_candidate(cfg, engine) and (engine == resident or ledger.may_swap(engine)[0])
        ]
        if len(candidates) < 2:
            return ladder, False
        expected = {row["choice"]: row["version"] for row in candidates}
        result = service.recommend(domain="verified", context=context, candidates=candidates)
        if not isinstance(result, dict) or result.get("applied") is not True:
            return ladder, False
        items = result.get("items")
        if not isinstance(items, list) or len(items) != len(candidates):
            return ladder, False
        choices = [row["choice"] for row in items]
        if len(set(choices)) != len(choices) or set(choices) != set(expected):
            return ladder, False
        if any(row.get("version") != expected[row["choice"]] for row in items):
            return ladder, False
        if any(
            _learning_version(chore, call, cfg, e) != version for e, version in expected.items()
        ):
            return ladder, False  # The resolved model changed during recommendation.
        ranked = iter(choices)
        return [next(ranked) if engine in expected else engine for engine in ladder], True
    except Exception:
        # Learning is optional; damaged state/service output cannot stop a chore.
        return ladder, False


def _observe_hop(
    service: Any,
    context: str,
    chore: str,
    call: Callable,
    cfg: dict[str, Any],
    engine: str,
    group_id: str,
    success: bool | None,
    elapsed_ms: float,
    category: str = "completed",
    version: str | None = None,
) -> None:
    if service is None:
        return
    # A "verified" label is only worth learning from if the verifier that
    # produced it can tell right from wrong. `success=True` here means exactly
    # one thing - "this chore's validate() accepted" - and that is SCHEMA
    # ACCEPTANCE, never a semantic correctness label. It is recorded as such.
    #
    # For triage, explain_lint and compress_recap the seeded fault sets in
    # test_a85_verifier_coverage.py were accepted in full (eps = 1.0 over 3
    # seeds each), so acceptance there carries no information about
    # correctness at all, and a learner fed labels uncorrelated with
    # correctness does not merely fail to improve - it acquires confident
    # wrong orderings. Those positives are withheld.
    #
    # THE RESIDUAL, stated rather than implied (external review, 2026-09-13):
    # the positives that DO survive are not thereby correct. repair_script
    # measured eps = 0.20 over 5 seeds, so roughly one accepted answer in five
    # of the seeded wrong kinds is wrong and labelled a success. Those figures
    # are coverage of a stated fault set, not population rates, and this
    # threshold is a conservative default rather than a proof about what any
    # verifier could achieve.
    #
    # The observation is still RECORDED - latency and coverage are real - but
    # the success label is withheld. A80 already has this idiom: an unlabelled
    # row carries a category and a NULL success (the A76 lesson that an
    # unreachable engine supplies no quality label).
    from tee.llm.chores import widening_ceiling

    # ASYMMETRY, and the tests taught it: eps counts FALSE ACCEPTS. A blind
    # verifier's acceptance is uninformative, but its REJECTION is a true
    # rejection - it caught something so malformed that even a shape check
    # saw it. So negative labels survive; only the positive one is withheld.
    # (A false REJECTION is a separate quantity this suite does not measure;
    # the true-accept controls only show the correct answer is not rejected.)
    if success is True and widening_ceiling(chore) <= 0.0:
        success, category = None, "unverifiable"
    # Telemetry failures never change a result, refusal, or fallback.
    with suppress(Exception):
        service.observe(
            domain="verified",
            context=context,
            choice=engine,
            version=version or _learning_version(chore, call, cfg, engine),
            success=success,
            elapsed_ms=elapsed_ms,
            group_id=group_id,
            category=category,
        )


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
    learning = cfg.get("_learning")
    context = _learning_context(chore) if learning is not None else ""
    group_id = uuid.uuid4().hex if learning is not None else ""
    state = profiles.load_state(cfg)
    # Ordered at CALL time so a row written since boot is honoured; LADDER
    # stays the import-time fallback and the name five test modules import.
    measured = measured_rows(cfg)
    order = _ladder(measured) or LADDER
    resident = _PROFILE_TO_ENGINE.get(state["active"], order[0])
    pinned = bool(state.get("pinned"))
    if pinned:
        ladder = [resident]
        reason = f"pinned: owner holds {resident}"
    elif policy == "greedy":
        choice = shadow.greedy_choice("chore", resident=resident)
        first = choice.get("engine") or resident
        ladder = [first, *[e for e in order if e != first]]
        reason = f"greedy: {first} est {choice.get('estimate_s')}s ({choice.get('reason')})"
    else:
        # The resident goes first because it costs no swap. The TAIL, though,
        # was ordered on latency alone - so a rung measured cheap per token
        # could be tried ahead of one that finishes sooner, because a cold load
        # is not in the comparison. q27b-think is the live example: a [2.29,
        # 7.66] s band and a measured 46 s to load. Order the tail by when it
        # would actually FINISH, which is shadow.greedy_choice's formula
        # (shadow.py:74) finally applied on the live path rather than only in
        # the shadow scheduler.
        #
        # Deliberately not pushed into _ladder(): that function's import-time
        # result is LADDER, which five test modules pin, and residency is not
        # knowable there. Ordering is a property of THIS call, not of the table.
        tail = sorted(
            (engine for engine in order if engine != resident),
            key=lambda engine: _finish_s(engine, measured),
        )
        ladder = [resident, *tail]
        reason = f"static: resident-first {resident}"
    learned = False
    if learning is not None and not pinned:
        ladder, learned = _learned_order(
            learning, context, chore, call, cfg, ladder, resident, ledger
        )
        if learned:
            reason += "; learned: evaluated validator reliability/cost prediction"
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
        if ENGINES.get(engine, {}).get("profile") not in declared:
            hops.append({"engine": engine, "skipped": "profile not declared here"})
            _observe_hop(learning, context, chore, call, cfg, engine, group_id, None, 0, "skipped")
            continue
        # A profile/capability may change after recommendation or between hops.
        # An applied model never carries authorization past this live boundary.
        if learned and not _local_candidate(cfg, engine):
            hops.append({"engine": engine, "skipped": "not an eligible local learning candidate"})
            _observe_hop(learning, context, chore, call, cfg, engine, group_id, None, 0, "skipped")
            continue
        if engine != resident:
            capable, swap_reason = ledger.may_swap(engine)
            if not capable:
                hops.append({"engine": engine, "skipped": swap_reason})
                ledger.record_swap(refused=swap_reason)
                _observe_hop(
                    learning, context, chore, call, cfg, engine, group_id, None, 0, "skipped"
                )
                continue
            ledger.record_swap(implicit=True)  # mlx loads the model per request
        hop_version = None
        if learning is not None:
            with suppress(Exception):
                hop_version = _learning_version(chore, call, cfg, engine)
        hop_started = time.perf_counter()
        try:
            result = call(_hop_cfg(cfg, engine))
        except TeeError as exc:
            # A76 P3: nothing listening is not a failed verification. Both used
            # to increment the same counter, so on a machine whose backend was
            # down every chore inflated the escalation rate with the network.
            unreachable = exc.code in UNREACHABLE_CODES
            hops.append(
                {
                    "engine": engine,
                    "verdict": exc.code,
                    **({"unreachable": True} if unreachable else {}),
                }
            )
            ledger.record_route(engine, verified=False, unreachable=unreachable)
            _observe_hop(
                learning,
                context,
                chore,
                call,
                cfg,
                engine,
                group_id,
                False if exc.code in VERIFIER_FAILURE_CODES else None,
                (time.perf_counter() - hop_started) * 1000,
                "unreachable"
                if unreachable
                else ("completed" if exc.code in VERIFIER_FAILURE_CODES else "unknown"),
                version=hop_version,
            )
            continue
        if result is None:
            hops.append({"engine": engine, "verdict": "empty_result"})
            ledger.record_route(engine, verified=False)
            _observe_hop(
                learning,
                context,
                chore,
                call,
                cfg,
                engine,
                group_id,
                False,
                (time.perf_counter() - hop_started) * 1000,
                version=hop_version,
            )
            continue
        hops.append({"engine": engine, "verdict": "verified"})
        ledger.record_route(engine, verified=True)
        _observe_hop(
            learning,
            context,
            chore,
            call,
            cfg,
            engine,
            group_id,
            True,
            (time.perf_counter() - hop_started) * 1000,
            version=hop_version,
        )
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
