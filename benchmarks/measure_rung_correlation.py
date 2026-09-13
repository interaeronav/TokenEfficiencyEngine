"""Measure q and rho for the router cascade's rungs, instead of assuming them.

`simulate_cascade_threshold.py` takes three inputs from measurement - verifier
coverage, latency and load - and two on faith: the per-rung error rate q, and
the correlation rho between rung failures. Its structural conclusions hold for
any q and rho, but its percentages do not, and rho is the precondition the
cascade is suspected of violating: q27b-think and q27b-bare are the same
Qwen3.8-27B weights, so a prompt that defeats one should defeat the other.

This runs ONE labelled task set through EVERY reachable rung and correlates
their failures.

  q_i   = the share of tasks rung i gets wrong
  rho   = the phi coefficient between two rungs' failure indicators, which for
          binary variables is Pearson's r. rho = 0 means independent failures,
          which is what a cascade assumes; rho = 1 means the second rung is
          the first one wearing a different name.

Tasks come from benchmarks/rung1/gen_distill.py, whose labels are known BY
CONSTRUCTION - a drift family must be answered `needs_verification` and a
grounded family `grounded` - so grading needs no judge and no teacher.

Serialized on purpose: every rung shares one local model server, so concurrent
requests would contend for the GPU and corrupt both the latency and the
independence signal. Rungs are also visited one at a time, all tasks each, so
a model is loaded once rather than swapped per task.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
sys.path.insert(0, str(REPO / "benchmarks" / "rung1"))
sys.path.insert(0, str(REPO / "benchmarks"))

# Reachable rungs, measured 2026-09-13. The last two are the SAME WEIGHTS on
# different backends - the pair whose independence the cascade assumes.
RUNGS = [
    ("14B-coder", "http://127.0.0.1:8082/v1", "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"),
    ("9B-general", "http://127.0.0.1:8082/v1", "mlx-community/Qwen3.5-9B-MLX-4bit"),
    ("27B-mlx", "http://127.0.0.1:8082/v1", "Youssofal/Qwen3.8-27B-MTPLX-Optimized-Quality"),
    ("27B-vllm", "http://127.0.0.1:8087/v1", "mtplx-qwen38-27b-optimized-quality"),
]


def tasks(count: int, seed: int) -> list[dict]:
    """Labelled triage cases: the expected `confidence` is known by construction."""
    import gen_distill as gen

    # A family returns gen._example(...) - {"messages": [system, user,
    # assistant]} - so the prompt AND the correct answer come straight from the
    # generator, against the very system prompt it built them for.
    rng = random.Random(seed)
    out = []
    for index in range(count):
        family = gen.FAMILIES[index % len(gen.FAMILIES)]
        system, user, answer = family(rng)["messages"]
        out.append(
            {
                "system": system["content"],
                "prompt": user["content"],
                "expect": json.loads(answer["content"])["confidence"],
                "family": family.__name__.lstrip("_"),
            }
        )
    return out


def ask(url: str, model: str, task: dict, timeout: float) -> str | None:
    body = {
        "model": model,
        "max_tokens": 400,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": task["system"]},
            {"role": "user", "content": task["prompt"]},
        ],
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        f"{url}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (urllib.error.URLError, OSError, ValueError):
        return None
    text = (payload["choices"][0]["message"].get("content") or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1]).get("confidence")
    except json.JSONDecodeError:
        return None


def phi(a: list[int], b: list[int]) -> float | None:
    """Pearson's r on two binary vectors. None when either has no variance -
    a rung that never fails carries no correlation information."""
    n = len(a)
    sa, sb = sum(a), sum(b)
    if sa in (0, n) or sb in (0, n):
        return None
    both = sum(x and y for x, y in zip(a, b, strict=True))
    num = both * n - sa * sb
    den = (sa * (n - sa) * sb * (n - sb)) ** 0.5
    return num / den if den else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, default=35)
    parser.add_argument(
        "--hard",
        action="store_true",
        help="use hard_triage_tasks instead of gen_distill: seductive-but-"
        "insufficient and sufficient-but-buried cases, built because both 27B "
        "rungs scored 35/35 on the generated families and a rung with no "
        "variance yields no correlation.",
    )
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    if args.hard:
        import hard_triage_tasks

        suite = hard_triage_tasks.tasks(args.tasks, args.seed)
    else:
        suite = tasks(args.tasks, args.seed)
    kind = "HARD" if args.hard else "generated"
    print(f"{len(suite)} {kind} labelled tasks, {len(RUNGS)} rungs, seed {args.seed}\n")

    fails: dict[str, list[int]] = {}
    for name, url, model in RUNGS:
        started = time.time()
        row, unreachable = [], 0
        for task in suite:
            got = ask(url, model, task, args.timeout)
            if got is None:
                unreachable += 1
                row.append(0)  # cannot be scored as a quality failure (A76)
            else:
                row.append(int(got != task["expect"]))
        fails[name] = row
        q = sum(row) / len(row)
        note = (
            f"  ({unreachable} unreachable/unparsed, not scored as failure)" if unreachable else ""
        )
        print(
            f"  {name:<11} q = {q:>5.1%}   {sum(row):>2}/{len(row)} wrong   "
            f"{time.time() - started:>6.1f}s{note}"
        )

    print("\n  pairwise rho (phi coefficient on failure indicators):")
    names = [n for n, _, _ in RUNGS]
    print(f"    {'':<12}" + "".join(f"{n:>12}" for n in names))
    for a in names:
        cells = ""
        for b in names:
            if a == b:
                cells += f"{'-':>12}"
            else:
                r = phi(fails[a], fails[b])
                cells += f"{'n/a':>12}" if r is None else f"{r:>12.2f}"
        print(f"    {a:<12}{cells}")

    same = phi(fails["27B-mlx"], fails["27B-vllm"])
    print("\n  THE PAIR THE CASCADE ASSUMES IS INDEPENDENT:")
    print("    27B-mlx vs 27B-vllm - the same weights, two backends")
    if same is None:
        print("    rho = n/a (one rung never failed, so there is nothing to correlate)")
    else:
        print(f"    rho = {same:.2f}")
    print("\n  A cascade rung only pays for itself on failures the rung above did")
    print("  NOT make. At rho = 1 there are none.")


if __name__ == "__main__":
    main()
