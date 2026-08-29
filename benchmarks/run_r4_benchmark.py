"""A42 R4: the four-arm benchmark the router must win — or revert.

Arms over the mixed-difficulty set (routing_dataset.json + any T6 field
cases appended): all-q14b, all-q27b (its one swap-in counted in the
arm's wall), all-client (the cost model: input tokens the client would
read; quality by construction — it is the reference tier), and routed
(the real cascade, swap seconds inside its wall, the ledger respected).

Per arm: verified quality, wall seconds, server-side tokens, client
tokens. Run on a QUIET machine — contention pollutes the adoption row.

Usage:
  uv run --project ../server python run_r4_benchmark.py --url URL \
      [--q14b NAME --q27b NAME --adapters PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
sys.path.insert(0, str(REPO / "server" / "tests"))

from fixtures_llm import CONTROLS, TRAPS  # noqa: E402
from run_r0_routing import RUNGS, _case  # noqa: E402

from tee.kernel import local_llm  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.kernel.errors import TeeError  # noqa: E402
from tee.kernel.machine import MachineLedger  # noqa: E402
from tee.llm import chores, router  # noqa: E402

Q14B_DEFAULT = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
Q27B_DEFAULT = "mlx-community/Qwen3.8-27B-bf16"
A2_DEFAULT = str(REPO / "benchmarks" / "rung1" / "adapters" / "tee-triage-a2")


def _triage_case(fixture: dict, expect: str):
    def call(cfg):
        return chores.triage(fixture["failure"], fixture["context"], refine="local", cfg=cfg)

    def verify(result):
        if result is None:
            return False
        return result.get("confidence") == expect

    tokens = estimate_tokens(fixture["failure"] + fixture["context"])
    return call, verify, tokens


def build_cases() -> list[dict]:
    cases = []
    for fixture in TRAPS:
        call, verify, tokens = _triage_case(fixture, "needs_verification")
        cases.append({"name": fixture["name"], "call": call, "verify": verify,
                      "client_tokens": tokens})
    for fixture in CONTROLS:
        call, verify, tokens = _triage_case(fixture, "grounded")
        cases.append({"name": fixture["name"], "call": call, "verify": verify,
                      "client_tokens": tokens})
    dataset = json.loads((REPO / "benchmarks" / "routing_dataset.json").read_text())
    ladder_names = {c["name"] for c in dataset["assigned"] if c["kind"] == "size-ladder"}
    for chore in ("triage", "refine_extract", "rerank", "compress_recap"):
        for rung_index, rung in enumerate(RUNGS):
            if f"{chore}_{rung}" not in ladder_names:
                continue

            def make(chore=chore, rung_index=rung_index):
                def call(cfg):
                    fn, client_input = _case(chore, rung_index, cfg)
                    return fn()

                _, client_input = _case(chore, rung_index, {})
                return call, estimate_tokens(client_input)

            call, tokens = make()
            cases.append({"name": f"{chore}_{rung}", "call": call,
                          "verify": lambda r: r is not None, "client_tokens": tokens})
    field = REPO / "benchmarks" / "r4_field_cases.json"
    if field.is_file():
        for row in json.loads(field.read_text()):
            facts = row["facts"]

            def call(cfg, facts=facts):
                return chores.phrase_deviation(facts, refine="local", cfg=cfg)

            cases.append({"name": row["name"], "call": call,
                          "verify": lambda r: r is not None,
                          "client_tokens": estimate_tokens("\n".join(facts))})
    return cases


def run_local_arm(name: str, cases, cfg) -> dict:
    verified = 0
    wall = 0.0
    server_tokens = 0
    for case in cases:
        original = local_llm.complete
        sizes = {"n": 0}

        def wrapped(prompt, *a, **kw):
            sizes["n"] += estimate_tokens((kw.get("system") or "")) + estimate_tokens(prompt)
            return original(prompt, *a, **kw)

        local_llm.complete = wrapped
        started = time.time()
        try:
            result = case["call"](cfg)
        except TeeError:
            result = None
        finally:
            local_llm.complete = original
        wall += time.time() - started
        server_tokens += sizes["n"]
        if case["verify"](result):
            verified += 1
    return {"arm": name, "verified": f"{verified}/{len(cases)}",
            "wall_s": round(wall, 1), "server_tokens": server_tokens, "client_tokens": 0}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--q14b", default=Q14B_DEFAULT)
    parser.add_argument("--q27b", default=Q27B_DEFAULT)
    parser.add_argument("--adapters", default=A2_DEFAULT)
    args = parser.parse_args()
    cases = build_cases()
    print(f"{len(cases)} cases", flush=True)
    arms = []

    warm14 = {"url": args.url, "model": args.q14b, "adapters": args.adapters}
    local_llm.complete("warm", url=args.url, model=args.q14b,
                       adapters=args.adapters, max_tokens=3)  # fmt: skip
    arms.append(run_local_arm("all-q14b", cases, warm14))
    print(json.dumps(arms[-1]), flush=True)

    ledger = MachineLedger()
    routed_cfg = {
        "url": args.url,
        "_state_dir": str(REPO / "benchmarks" / ".r4-state"),
        "profiles": {
            "q14b": {"model": args.q14b, "adapters": args.adapters},
            "q27b": {"model": args.q27b, "adapters": ""},
        },
    }
    (REPO / "benchmarks" / ".r4-state").mkdir(exist_ok=True)
    verified = 0
    wall = 0.0
    client_tokens = 0
    escalations = 0
    started_arm = time.time()
    for case in cases:
        routed = router.route(
            case["name"], case["call"], cfg=routed_cfg, ledger=ledger,
            input_pointer=f"case:{case['name']}",
        )  # fmt: skip
        if routed["ok"] and case["verify"](routed["result"]):
            verified += 1
        if not routed["ok"]:
            escalations += 1
            client_tokens += estimate_tokens(json.dumps(routed["escalate"]))
            client_tokens += case["client_tokens"]  # the client then reads the input
    wall = time.time() - started_arm
    block = ledger.meter_block()
    arms.append({
        "arm": "routed", "verified": f"{verified + escalations}/{len(cases)}",
        "verified_note": f"{verified} local + {escalations} escalated-to-reference",
        "wall_s": round(wall, 1),
        "server_tokens": "(per-engine in meter)", "client_tokens": client_tokens,
        "meter": {"engines": block["engines"], "swaps": block["swaps"],
                  "escalation_rate": block["escalation_rate"]},
    })  # fmt: skip
    print(json.dumps(arms[-1]), flush=True)

    swap_started = time.time()
    local_llm.complete("warm", url=args.url, model=args.q27b, max_tokens=3)
    swap_s = time.time() - swap_started
    arm27 = run_local_arm("all-q27b", cases, {"url": args.url, "model": args.q27b})
    arm27["wall_s"] = round(arm27["wall_s"] + swap_s, 1)
    arm27["swap_in_s"] = round(swap_s, 1)
    arms.append(arm27)
    print(json.dumps(arms[-1]), flush=True)

    client_total = sum(c["client_tokens"] for c in cases)
    arms.append({"arm": "all-client", "verified": f"{len(cases)}/{len(cases)} (by construction)",
                 "wall_s": None, "server_tokens": 0, "client_tokens": client_total})
    print(json.dumps(arms[-1]), flush=True)
    print(json.dumps({"summary": arms}, indent=1))


if __name__ == "__main__":
    main()
