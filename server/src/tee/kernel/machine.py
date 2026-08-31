"""ONE machine-load ledger + registry-form engine facts (A42 R1, seams 1+3).

Research 58's K-layer registry schema, authored NOW so the K-phases
inherit rows instead of migrating them: every engine carries capability,
measured cost references, footprint and a default QoS class. QoS classes
are LABELS at this stage (seam 3) - K1 turns them into law.

The ledger is the single arbiter of heavyweight residency (the A41 guard
seam): reconstruction jobs register here, a routed engine swap is refused
with the honest line while any registered job runs, and a job launch can
ask what is resident. Capability math is deterministic bookkeeping
(total RAM - reserve - registered jobs vs the target footprint);
measured swap-cost constants arrive in R2, not here.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from tee.kernel.errors import TeeError

QOS = ("interactive", "standard", "batch", "maintenance")

# A46 P3a. Below this, the local reasoning models return a truncated
# scratchpad instead of an answer - and q27b returns an EMPTY string,
# which reads as "the model had nothing to say" rather than "the
# budget ran out". Measured, both engines, 2026-08-31.
MIN_CHORE_TOKENS = 256


def min_chore_tokens(profile: str | None) -> int:
    """The output floor for one engine, not for all of them.

    A46 set a single global 256 from two models that both cleared it. Adding
    Qwen3.6-35B broke that assumption immediately: warm and at temperature 0
    it returns an EMPTY answer 3/3 at 256, because its reasoning pass alone
    is ~974 tokens. A floor is a property of a model's appetite for thinking,
    so it belongs on the model's row. `MIN_CHORE_TOKENS` remains the default
    for engines that have not been measured.
    """
    for spec in ENGINES.values():
        if spec.get("profile") == profile and spec.get("min_chore_tokens"):
            return int(spec["min_chore_tokens"])
    return MIN_CHORE_TOKENS


# The client stack + OS headroom the machine always keeps. A stated
# placeholder until R2 measures the real constant.
RESERVE_GB = 16.0

# name -> registry-form facts. "profile" binds an llm row to its switch
# profile; footprints are spec values with the measured number cited.
ENGINES: dict[str, dict[str, Any]] = {
    "q14b+a2": {
        "kind": "llm",
        "profile": "q14b",
        # Not served on this machine (the shim has no 14B route), so nothing
        # on disk to read. Unclaimed rather than asserted blind.
        "senses_source": "not present on this machine - unverified",
        "capability": ["chores"],
        "senses": [],  # A47 P0: blind and deaf, declared
        "footprint_gb": 9.0,  # 8.0 measured R0 2026-08-29
        "eta_s": 1.1,  # measured swap cost R2 2026-08-29 (spec said 30)
        "qos_default": "interactive",
        "cost": {"latency_s": [0.74, 1.74], "measured": "R0 2026-08-29"},
    },
    "q27b-bare": {
        "kind": "llm",
        "profile": "q27b",
        "capability": ["chores"],
        # A49 P0 correction. A47 declared this blind. It is not: the model's
        # own config.json on disk says architectures
        # ["Qwen3_5ForConditionalGeneration"] and carries a `vision_config`
        # plus image/vision token ids. The owner said so and the file agreed.
        #
        # The METHOD matters more than the row. The original claim came from
        # watching the LiteLLM shim, which reroutes any image-bearing request
        # to a dedicated VL server - so EVERY model appears to see through it,
        # and no model's own sight can be observed that way. Senses are read
        # from the model's config on disk. DeepSeek checked the same way is
        # genuinely blind (DeepseekV4ForCausalLM, no vision_config), so A47's
        # premise holds for the model it was built for.
        "senses": ["vision"],
        "senses_source": "config.json architectures/vision_config, read 2026-08-31",
        "footprint_gb": 55.0,  # 43.7 measured R0 2026-08-29
        "eta_s": 18.0,  # measured swap cost R2 2026-08-29 (spec said 90)
        "qos_default": "interactive",
        "cost": {
            "latency_s": [3.07, 9.69],
            "measured": "R0 2026-08-29",
            # A46 P3a re-measured this engine through the owner's LiteLLM
            # shim on a reasoning-heavy chore at max_tokens=256 and saw
            # 27.78 s, with 50.4 GB resident on :8080. NOT written over the
            # R0 figure above: different prompt, different budget, different
            # path, so the two are not comparable and averaging them would
            # invent a number neither run produced.
            "a46_shim_observation_s": 27.78,
        },
    },
    # -- A46 P3a: the engines this machine ACTUALLY serves ---------------
    # Until now the table described q14b/q27b generically while
    # .tee/config.toml declared only the PAID qmax, so no chore could
    # reach a free engine. These two are measured, live, on the owner's
    # LiteLLM shim (127.0.0.1:4000 -> 127.0.0.1 backends; nothing here
    # leaves the machine).
    #
    # BOTH ARE REASONING MODELS. Measured 2026-08-31 on one chore
    # (snake_case rename, temperature 0), sweeping max_tokens:
    #
    #                 64 tok        256 tok             1024 tok
    #   dsflash    truncated     4.41 s, usable      4.41 s, usable
    #   q27b       EMPTY         27.78 s, usable     27.77 s, usable
    #
    # At 64 the reasoning pass eats the whole budget: dsflash leaks its
    # scratchpad into `content`, and q27b returns content="" with the
    # text in `reasoning_content`. Neither is a failure the caller can
    # see without checking - it looks like a model that answered badly.
    # Hence MIN_CHORE_TOKENS below, which is a correctness floor, not a
    # tuning knob.
    "dsflash": {
        "kind": "llm",
        "profile": "dsflash",
        "capability": ["chores"],
        "senses": [],
        "senses_source": "config.json DeepseekV4ForCausalLM, no vision_config, read 2026-08-31",
        # No resident process observed across a live 900-token generation
        # (polled 15 s at 0.7 s). Served on demand and not held, so there
        # is no steady footprint to charge the ledger for. NOT a measured
        # zero for a loaded model - it is an absence of one.
        "footprint_gb": 0.0,
        "eta_s": 3.0,  # 2.27 s first call vs 1.49 s warm, measured
        "qos_default": "interactive",
        "cost": {"latency_s": [4.41, 4.41], "measured": "A46 P3a 2026-08-31"},
    },
    # -- A47 P0: sense providers. A model that cannot see borrows an eye.
    #
    # These are not chore engines: nothing routes work here for reasoning.
    # They convert media the asking model cannot read into text it can, and
    # they are declared so the ledger can PRICE that conversion instead of
    # it happening invisibly (which is what the owner's shim does today).
    "qvl": {
        "kind": "sense",
        "profile": "qvl",
        "capability": ["sense-vision"],
        "senses": ["vision"],
        "footprint_gb": 17.0,  # measured on disk: the 4-bit 30B-A3B weights
        # The fact the shim knows and TEE did not: on a 128 GB machine an
        # 84 GB session model and this cannot both be resident (the owner's
        # hook proved it - 90 GB swap, pressure critical), so an image
        # request EVICTS the host's model and its next turn pays a reload.
        "evicts": ["dsflash"],
        "qos_default": "interactive",
        "cost": {
            "latency_s": [4.0, 7.5],  # gable-vs-spec 4.0, 4K site frame 7.5
            "swap_s": 10.0,  # measured alternation penalty vs 0.67-0.82 warm
            "measured": "A47 P0 2026-08-31",
        },
    },
    "whisper": {
        "kind": "sense",
        "capability": ["sense-audio"],
        "senses": ["audio"],
        "footprint_gb": 0.5,  # faster-whisper base, int8 on CPU
        "evicts": [],  # small enough to coexist with anything here
        "qos_default": "interactive",
        "cost": {
            "latency_s": [0.62, 1.36],  # base / tiny on a spoken fixture
            "load_s": 0.8,  # per-call model load; no sidecar needed
            "measured": "A47 P0 2026-08-31",
        },
    },
    "q35b": {
        "kind": "llm",
        "profile": "q35b",
        "capability": ["chores"],
        # Qwen3_5MoeForConditionalGeneration WITH a vision_config - it sees,
        # read from the model's own config on disk (the A49 method: never
        # inferred from shim behaviour, which reroutes images and hides it).
        "senses": ["vision"],
        "senses_source": (
            "config.json Qwen3_5MoeForConditionalGeneration + vision_config, 2026-08-31"
        ),
        "footprint_gb": 65.0,  # measured on disk: Qwen3.6-35B-A3B bf16
        "qos_default": "batch",  # ~16 s a chore; not an interactive latency
        # THE number that matters. Measured warm, temperature 0, one
        # snake_case rename:
        #     256   3/3 EMPTY   (the global floor silently breaks this model)
        #     512   inconsistent - usable in one run of three, empty in another
        #     1024  4/4 usable, stopping naturally at 974 tokens
        # 512 is not merely tight, it is UNRELIABLE: this MoE's reasoning
        # length varies between identical calls at temperature 0, so the
        # floor has to clear the thinking pass with room, not merely touch it.
        "min_chore_tokens": 1024,
        "cost": {
            "latency_s": [15.9, 16.7],  # at the 1024 floor, 4 runs
            "measured": "A50 2026-08-31",
        },
    },
    "client": {
        "kind": "client",
        "capability": ["everything"],
        "footprint_gb": 0.0,
        "qos_default": "interactive",
        "cost": {"tokens": "input grows unbounded by any window (R0)"},
    },
    "reconstruct-photogrammetry": {
        "kind": "job",
        "capability": ["structure-sets"],
        "footprint_gb": 1.0,  # 0.88 peak measured T0 2026-08-29
        "qos_default": "batch",
        "cost": {"wall_s": [6, 18], "measured": "T0 ladder, 36-view fixture"},
    },
    "pipeline-step": {
        "kind": "job",
        "capability": ["declared-steps"],
        "footprint_gb": 2.0,  # default; a declaration's own cost hint overrides
        "qos_default": "batch",
        "cost": {"wall_s": "declared per step (A43 P1)"},
    },
    "reconstruct-odm": {
        "kind": "job",
        "capability": ["drone-sets"],
        "footprint_gb": 16.0,  # the colima VM allocation
        "qos_default": "batch",
        "cost": {"wall_s": [210, 310], "measured": "T0/T2 live runs 2026-08-29"},
    },
}


def _total_ram_gb() -> float:
    # TEE_MACHINE_TOTAL_GB declares capacity where the host's physical
    # RAM is not the truth: CI runners, containers/VMs (the colima ODM
    # allocation), and hermetic tests. Unset -> the host's real memory.
    declared = os.environ.get("TEE_MACHINE_TOTAL_GB")
    if declared:
        try:
            return float(declared)
        except ValueError:
            raise TeeError(
                "machine_bad_capacity",
                f"TEE_MACHINE_TOTAL_GB={declared!r} is not a number.",
                fix="Set it to the machine's usable RAM in GB, e.g. 128.",
            ) from None
    try:
        return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1e9
    except (ValueError, OSError):  # pragma: no cover - exotic platforms
        return 8.0


class MachineLedger:
    """The one ledger. Register long-running work; ask before swapping."""

    def __init__(self, total_gb: float | None = None):
        self.total_gb = float(total_gb if total_gb is not None else _total_ram_gb())
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        # the merged meter's routing counters (A42 R2, seam 2)
        self._tasks = 0
        self._escalations = 0
        self._routes: dict[str, dict[str, int]] = {}
        self._swaps = {"explicit": 0, "implicit": 0, "refused": 0, "seconds_known": 0.0}
        self._last_refusal: str | None = None
        self._queue_probe = None  # installed by the app (K1): () -> {queued, max_s}
        self._dispatch = {"static": 0, "greedy": 0, "pinned": 0}
        self._last_dispatch: str | None = None
        # A43 P3: declared steps are task-graph nodes like any other work,
        # so they are metered beside chores and reconstructions rather than
        # in a lane of their own.
        self._pipeline: dict[str, Any] = {"steps_run": 0, "skipped_fresh": 0, "wall_s": 0.0}

    def register_job(
        self, key: str, engine: str, footprint_gb: float | None = None
    ) -> dict[str, Any]:
        spec = ENGINES.get(engine)
        if spec is None or spec["kind"] != "job":
            known = sorted(n for n, s in ENGINES.items() if s["kind"] == "job")
            raise TeeError(
                "machine_unknown_engine",
                f"'{engine}' is not a registered job engine.",
                fix=f"Job engines: {', '.join(known)}.",
            )
        row = {
            "key": str(key),
            "engine": engine,
            "footprint_gb": float(
                footprint_gb if footprint_gb is not None else spec["footprint_gb"]
            ),
            "qos": str(spec["qos_default"]),
        }
        with self._lock:
            self._jobs[row["key"]] = row
        return dict(row)

    def release_job(self, key: str) -> None:
        with self._lock:
            self._jobs.pop(str(key), None)

    def active_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self._jobs.values()]

    def jobs_footprint_gb(self) -> float:
        with self._lock:
            return sum(row["footprint_gb"] for row in self._jobs.values())

    def may_swap(self, engine: str) -> tuple[bool, str]:
        """May the machine take on `engine`'s footprint right now?

        Single occupancy means the current resident leaves first, so the
        question is target vs (total - reserve - registered jobs)."""
        spec = ENGINES.get(engine)
        if spec is None:
            return False, f"unknown engine '{engine}' - not in the registry"
        active = self.active_jobs()
        if active:
            held = ", ".join(f"{row['key']} ({row['engine']}, {row['qos']})" for row in active)
            return False, (
                f"swap deferred: {len(active)} registered job(s) hold the machine - {held}"
            )
        target = float(spec["footprint_gb"])
        available = self.total_gb - RESERVE_GB
        if target > available:
            return False, (
                f"{engine} needs {target:.0f} GB; {available:.0f} GB available "
                f"({self.total_gb:.0f} total - {RESERVE_GB:.0f} reserve)"
            )
        return True, f"capable: {target:.0f} GB fits in {available:.0f} GB available"

    def may_admit(self, engine: str) -> tuple[bool, str]:
        """K1 admission: refuse only work the machine can NEVER place -
        queueing behind current residents stays legal."""
        spec = ENGINES.get(engine)
        if spec is None:
            return True, "no registry row - admitted"
        target = float(spec["footprint_gb"])
        available = self.total_gb - RESERVE_GB
        if target > available:
            return False, (
                f"{engine} needs {target:.0f} GB and the machine can never "
                f"place it ({available:.0f} GB after the {RESERVE_GB:.0f} GB reserve)"
            )
        return True, "placeable"

    def set_queue_probe(self, probe) -> None:
        self._queue_probe = probe

    # -- the merged meter (A42 R2; ONE meter, seam 2) ----------------------

    def record_task(self) -> None:
        with self._lock:
            self._tasks += 1

    def record_route(self, engine: str, verified: bool) -> None:
        with self._lock:
            row = self._routes.setdefault(engine, {"calls": 0, "verified": 0})
            row["calls"] += 1
            if verified:
                row["verified"] += 1

    def record_escalation(self) -> None:
        with self._lock:
            self._escalations += 1

    def record_pipeline(self, *, ran: int = 0, skipped: int = 0, wall_s: float = 0.0) -> None:
        with self._lock:
            self._pipeline["steps_run"] += ran
            self._pipeline["skipped_fresh"] += skipped
            self._pipeline["wall_s"] = round(self._pipeline["wall_s"] + wall_s, 1)

    def record_dispatch(self, mode: str, reason: str) -> None:
        with self._lock:
            self._dispatch[mode] = self._dispatch.get(mode, 0) + 1
            self._last_dispatch = reason

    def record_swap(
        self, *, implicit: bool = False, refused: str | None = None, seconds: float | None = None
    ) -> None:
        with self._lock:
            if refused is not None:
                self._swaps["refused"] += 1
                self._last_refusal = refused
                return
            self._swaps["implicit" if implicit else "explicit"] += 1
            if seconds is not None:
                self._swaps["seconds_known"] += float(seconds)

    def meter_block(self) -> dict[str, Any]:
        """Escalation, swap and job-class columns TOGETHER, with the
        scheduler's columns reserved in the same schema (research 59
        seam 2 - no later migration)."""
        with self._lock:
            block: dict[str, Any] = {
                "routed_tasks": self._tasks,
                "engines": {name: dict(row) for name, row in self._routes.items()},
                "escalations": self._escalations,
                "escalation_rate": round(self._escalations / self._tasks, 3)
                if self._tasks
                else 0.0,
                "swaps": {
                    key: (round(value, 1) if isinstance(value, float) else value)
                    for key, value in self._swaps.items()
                },
                "pipeline": dict(self._pipeline),
                "jobs": {
                    "active": len(self._jobs),
                    "batch_footprint_gb": round(
                        sum(row["footprint_gb"] for row in self._jobs.values()), 1
                    ),
                },
                "scheduler": {
                    "queue_age_s": (self._queue_probe() if self._queue_probe else "reserved (K1)"),
                    "dispatch_reason": (
                        {"last": self._last_dispatch, **self._dispatch}
                        if self._last_dispatch
                        else "reserved (K2)"
                    ),
                    "shadow_delta": "reserved (K2; recorder live since K0)",
                },
            }
            if self._last_refusal:
                block["swaps"]["last_refusal"] = self._last_refusal
            return block
