"""A42 R0: the routing dataset — input-size sensitivity + the mixed set.

Standalone, model-dependent — NOT part of the default battery (the m3
pattern). Two commands:

  sizes    - the input-size sensitivity ladder: size-scalable chores run at
             S/M/L/XL input rungs against one engine; per rung: median wall
             (of 3), prompt-token estimate (system+user, the meter's own
             estimator, captured at the local_llm seam), answer tokens, and
             the client-brief column (what handing the same evidence to the
             client would cost in input tokens — no cloud call, ever).
  assign   - verifier-assigned difficulty for the R4 mixed set: every
             trap/control fixture runs once per engine; the chore's own
             deterministic verifier decides the outcome; difficulty =
             easy (q14b passes) / medium (q14b fails, q27b passes) /
             hard (both fail -> client tier). Writes routing_dataset.json.

Usage (adapters also honored from TEE_LOCAL_LLM_ADAPTERS):
  uv run --project ../server python run_r0_routing.py sizes \
      --url URL --model NAME --engine q14b+a2
  uv run --project ../server python run_r0_routing.py assign --url URL \
      --q14b-model NAME --q27b-model NAME --adapters PATH
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
sys.path.insert(0, str(REPO / "server" / "tests"))

from fixtures_llm import CONTROLS, TRAPS  # noqa: E402

from tee.kernel import local_llm  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.kernel.errors import TeeError  # noqa: E402
from tee.llm import chores  # noqa: E402

# ---------------------------------------------------------------- fixtures

_PAGE = (REPO / "docs/research/19-context-economics.md").read_text()
_TB_HEAD = 'Traceback (most recent call last):\n  File "populate.py", line 6, in <module>\n'
_TB_ERR = "TypeError: spawn_actor() got an unexpected keyword argument 'transform'\n"
_CTX_LINE = '  File "helpers.py", line %d, in stage_%d\n    result = stage(result, options)\n'


def _triage_input(rung: int) -> tuple[str, str]:
    """A traceback whose middle grows: 0/8/32/128 context frames."""
    frames = (0, 8, 32, 128)[rung]
    middle = "".join(_CTX_LINE % (10 + i, i) for i in range(frames))
    evidence = "line 6: actor = world.spawn_actor(bp, transform=tf)"
    return _TB_HEAD + middle + _TB_ERR, evidence


def _extract_input(rung: int) -> tuple[str, str, int]:
    chars = (2000, 8000, 16000, 32000)[rung]
    text = (_PAGE * 4)[:chars]
    return text, "what does a tool schema cost per conversation?", 120


def _rerank_input(rung: int) -> tuple[str, list[dict[str, str]]]:
    n = (8, 16, 32, 64)[rung]
    cands = [
        {"id": f"tool-{i}", "title": f"sets material parameter {i} on the active object"}
        for i in range(n)
    ]
    cands[n // 2] = {"id": "assign-material", "title": "assign a material to a mesh by name"}
    return "assign a material to a mesh", cands


def _recap_input(rung: int) -> list[str]:
    n = (10, 40, 80, 160)[rung]
    line = "2026-08-{:02d}: step {} measured {} ms and was kept"
    return [line.format((i % 28) + 1, i, i * 3) for i in range(n)]


SIZED_CHORES = ["triage", "refine_extract", "rerank", "compress_recap"]
RUNGS = ["S", "M", "L", "XL"]


def _case(chore: str, rung_index: int, cfg: dict):
    """(callable, client_input) for one chore at one size rung."""
    if chore == "triage":
        tb, evidence = _triage_input(rung_index)

        def call():
            return chores.triage(tb, evidence, refine="local", cfg=cfg)

        return call, tb + evidence
    if chore == "refine_extract":
        text, question, budget = _extract_input(rung_index)

        def call():
            return chores.refine_extract(text, question, budget, refine="local", cfg=cfg)

        return call, text + question
    if chore == "rerank":
        query, cands = _rerank_input(rung_index)

        def call():
            return chores.rerank(query, cands, refine="local", cfg=cfg)

        return call, query + "\n".join(f"{c['id']}: {c['title']}" for c in cands)
    notes = _recap_input(rung_index)

    def call():
        return chores.compress_recap(notes, refine="local", cfg=cfg)

    return call, "\n".join(notes)


# ------------------------------------------------------------- measurement


class _Meter:
    """Captures prompt sizes at the local_llm seam (the meter's estimator)."""

    def __init__(self) -> None:
        self.prompt_tokens = 0
        self._orig = local_llm.complete

    def __enter__(self) -> _Meter:
        def wrapped(prompt: str, *args, **kwargs):
            system = kwargs.get("system") or ""
            self.prompt_tokens = estimate_tokens(system) + estimate_tokens(prompt)
            return self._orig(prompt, *args, **kwargs)

        local_llm.complete = wrapped
        return self

    def __exit__(self, *exc) -> None:
        local_llm.complete = self._orig


def _timed(fn, runs: int = 3):
    times, result = [], None
    for _ in range(runs):
        start = time.time()
        result = fn()
        times.append(time.time() - start)
    return statistics.median(times), result


def cmd_sizes(args) -> None:
    cfg = {"url": args.url, "model": args.model}
    rows = []
    for chore in SIZED_CHORES:
        for rung_index, rung in enumerate(RUNGS):
            call, client_input = _case(chore, rung_index, cfg)
            row = {
                "chore": chore,
                "rung": rung,
                "engine": args.engine,
                "client_brief_tokens": estimate_tokens(client_input),
            }
            try:
                with _Meter() as meter:
                    median_s, result = _timed(call)
                row["median_s"] = round(median_s, 2)
                row["prompt_tokens"] = meter.prompt_tokens
                payload = {k: v for k, v in (result or {}).items() if k != "model"}
                row["answer_tokens"] = estimate_tokens(json.dumps(payload, separators=(",", ":")))
            except (TeeError, AssertionError) as exc:
                row["outcome"] = f"{type(exc).__name__}: {exc}"[:120]
            rows.append(row)
            print(json.dumps(row))
    out = REPO / "benchmarks" / f"r0_sizes_{args.engine.replace('+', '_')}.json"
    out.write_text(json.dumps({"engine": args.engine, "model": args.model, "rows": rows}, indent=1))
    print(f"wrote {out}")


# ------------------------------------------------------- difficulty assign


def _verify_triage(case: dict, result: dict | None) -> bool:
    """The trap suite's own verdict: traps must defer, controls must ground."""
    if result is None:
        return False
    if case.get("expect") == "needs_verification":
        return result.get("confidence") == "needs_verification"
    return result.get("confidence") == "grounded"


def cmd_assign(args) -> None:
    engines = [
        ("q14b+a2", {"url": args.url, "model": args.q14b_model}, args.adapters or None),
        ("q27b-bare", {"url": args.url, "model": args.q27b_model}, None),
    ]
    pool = [dict(c, expect="needs_verification") for c in TRAPS] + [
        dict(c, expect="grounded") for c in CONTROLS
    ]
    outcomes: dict[str, dict[str, bool]] = {}
    for engine_name, cfg, adapters in engines:
        cfg = dict(cfg, adapters=adapters) if adapters else cfg
        for case in pool:
            try:
                result = chores.triage(
                    case["failure"], case["context"], refine="local", cfg=cfg
                )
            except TeeError:
                result = None
            passed = _verify_triage(case, result)
            outcomes.setdefault(case["name"], {})[engine_name] = passed
            print(f"{engine_name} {case['name']}: {'pass' if passed else 'FAIL'}")
    dataset = []
    for case in pool:
        verdicts = outcomes[case["name"]]
        if verdicts.get("q14b+a2"):
            difficulty = "easy"
        elif verdicts.get("q27b-bare"):
            difficulty = "medium"
        else:
            difficulty = "hard"
        dataset.append(
            {
                "name": case["name"],
                "chore": "triage",
                "kind": case["expect"],
                "difficulty": difficulty,
                "verdicts": verdicts,
                "assigned_by": "trap-suite verifier (deterministic), engines live",
            }
        )
    out = REPO / "benchmarks" / "routing_dataset.json"
    note = (
        "difficulty = verifier outcome per engine: "
        "easy q14b-pass, medium q27b-only, hard client-tier"
    )
    out.write_text(json.dumps({"assigned": dataset, "note": note}, indent=1))
    print(f"wrote {out} ({len(dataset)} cases)")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_sizes = sub.add_parser("sizes")
    p_sizes.add_argument("--url", required=True)
    p_sizes.add_argument("--model", required=True)
    p_sizes.add_argument("--engine", required=True)
    p_assign = sub.add_parser("assign")
    p_assign.add_argument("--url", required=True)
    p_assign.add_argument("--q14b-model", required=True)
    p_assign.add_argument("--q27b-model", required=True)
    p_assign.add_argument("--adapters", default=os.environ.get("TEE_LOCAL_LLM_ADAPTERS"))
    args = parser.parse_args()
    {"sizes": cmd_sizes, "assign": cmd_assign}[args.cmd](args)


if __name__ == "__main__":
    main()
