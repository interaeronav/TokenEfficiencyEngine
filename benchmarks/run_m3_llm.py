"""A34 M3: the benchmarks that decide chore adoption (research 50).

Standalone, model-dependent - NOT part of the default battery. Every row
is appended to RESULTS.md as a dated section by the caller; verdicts go
to PROGRESS. Three measurements:

  latency  - per-chore wall time + answer tokens against a served model
             (median of 3; the 105 tok/s / 5.3 GB Qwen3.5-9B row from
             research 50 is the reference).
  quality  - extract-refinement (chore 4) graded on fixtures built from
             TEE's OWN docs (copyright-clean, documentation-class text):
             dumb parser vs model-refined, each scored by a separate
             grader model (labeled in the row - the big local teacher).
  traps    - delegated to pytest (tests/test_llm_traps.py, llm marker):
             the M2 acceptance, not re-implemented here.

Usage:
  uv run --project ../server python run_m3_llm.py latency --url URL --model NAME
  uv run --project ../server python run_m3_llm.py quality --url URL --model NAME \
      [--grade-url URL --grade-model NAME]   # omit grading to only generate
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))

from tee.kernel import local_llm  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.llm import chores  # noqa: E402
from tee.web.extract import focus_extract  # noqa: E402

# --------------------------------------------------------------------------
# Fixtures: (doc, question) pairs over TEE's own corpus. The answers exist
# in the named files; budgets are chore-realistic.
# --------------------------------------------------------------------------

QUALITY_CASES = [
    ("docs/research/19-context-economics.md", "what does re-viewing a frame cost in tokens compared to a stored caption?"),
    ("docs/research/04-token-efficiency-techniques.md", "how should mutations report their results?"),
    ("docs/research/49-web-lookup-multimodal.md", "what did the live vision measurement show about cost and latency?"),
    ("CLAUDE.md", "what do TEE tools return by default instead of full scene dumps?"),
    ("docs/security.md", "which schemes and ports does the web lane allow?"),
    ("docs/quickstart.md", "how should loops be run to keep intermediate results out of context?"),
]  # fmt: skip
QUALITY_BUDGET = 200

TRACEBACK_FIXTURE = (
    "Traceback (most recent call last):\n"
    '  File "build.py", line 7, in <module>\n'
    "    bm.free()\n"
    "AttributeError: 'NoneType' object has no attribute 'free'"
)
SCRIPT_FIXTURE = ("import os\nresult = call('bl_demo_tool', {'n': 1})", "Line 1: Import is not allowed.")
LINT_FIXTURE = "plaus_check: wall_02 overlaps door_01 by 0.18 m on the x axis (code: overlap)"
FACTS_FIXTURE = "The client wants the boundary wall 2.4 m high in face brick, and hates gloss finishes."
RECAP_FIXTURE = {"adapters": {"blender": {"entities": 14, "kinds": {"mesh": 9, "light": 3, "camera": 2}}}, "checkpoints": ["cp1", "cp2"]}  # fmt: skip
RERANK_FIXTURE = ("bedding sand thickness for block paving", [
    {"id": "03-concrete-block-paving", "title": "Concrete block paving"},
    {"id": "01-earthworks", "title": "Earthworks and compaction"},
    {"id": "07-drainage", "title": "Drainage falls"},
])  # fmt: skip


def _cfg(args) -> dict:
    return {"url": args.url, "model": args.model}


def _timed(fn, *fn_args, runs: int = 3, **fn_kwargs):
    """(median_seconds, last_result); every run must succeed."""
    times = []
    result = None
    for _ in range(runs):
        start = time.time()
        result = fn(*fn_args, **fn_kwargs)
        times.append(time.time() - start)
        assert result is not None, f"{getattr(fn, '__name__', fn)} returned None under refine=local"
    return statistics.median(times), result


def cmd_latency(args) -> None:
    cfg = _cfg(args)
    page_text = (REPO / "docs/research/19-context-economics.md").read_text()[:8000]
    rows = []
    for name, call in [
        ("triage", lambda: chores.triage(TRACEBACK_FIXTURE, "line 6: bm = existing.get(name)", refine="local", cfg=cfg)),
        ("repair_script", lambda: chores.repair_script(*SCRIPT_FIXTURE, refine="local", cfg=cfg)),
        ("explain_lint", lambda: chores.explain_lint(LINT_FIXTURE, refine="local", cfg=cfg)),
        ("refine_extract", lambda: chores.refine_extract(page_text, QUALITY_CASES[0][1], QUALITY_BUDGET, refine="local", cfg=cfg)),
        ("structure_facts", lambda: chores.structure_facts(FACTS_FIXTURE, refine="local", cfg=cfg)),
        ("compress_recap", lambda: chores.compress_recap(RECAP_FIXTURE, refine="local", cfg=cfg)),
        ("rerank", lambda: chores.rerank(*RERANK_FIXTURE, refine="local", cfg=cfg)),
    ]:  # fmt: skip
        try:
            median_s, result = _timed(call)
        except Exception as exc:  # an abstention/refusal is a row, not a crash
            rows.append({"chore": name, "outcome": f"{type(exc).__name__}: {exc}"[:120]})
            print(f"{name}: NO ROW ({rows[-1]['outcome']})")
            continue
        payload = {k: v for k, v in result.items() if k != "model"}
        rows.append({"chore": name, "median_s": round(median_s, 2),
                     "answer_tokens": estimate_tokens(json.dumps(payload, separators=(",", ":")))})
        print(f"{name}: {median_s:.2f}s median, {rows[-1]['answer_tokens']} tok")
    print(json.dumps({"model": args.model, "rows": rows}))


def cmd_quality(args) -> None:
    cfg = _cfg(args)
    cases = []
    from tee.kernel.errors import TeeError

    for rel_path, question in QUALITY_CASES:
        text = (REPO / rel_path).read_text()[:16000]
        dumb_quote, _ = focus_extract(text, question, QUALITY_BUDGET)
        why = None
        try:
            refined = chores.refine_extract(text, question, QUALITY_BUDGET, refine="local", cfg=cfg)
            if refined is None:
                why = "empty selection"
        except TeeError as exc:  # verification/schema kill - the quality signal itself
            refined, why = None, exc.code
        cases.append({
            "file": rel_path, "question": question, "source": text,
            "dumb": dumb_quote, "refined": None if refined is None else refined["quote"],
            "abstained": why,
        })  # fmt: skip
        state = f"abstained ({why})" if refined is None else f"{estimate_tokens(refined['quote'])} tok"
        print(f"{rel_path}: dumb {estimate_tokens(dumb_quote)} tok, refined {state}")

    out = Path(args.out)
    out.write_text(json.dumps(cases))
    if not args.grade_url:
        print(f"generated only (no --grade-url); cases in {out}")
        return

    grader_cfg = {"url": args.grade_url, "model": args.grade_model}
    graded = []
    for case in cases:
        scores = {}
        for arm in ("dumb", "refined"):
            quote = case[arm]
            if quote is None:
                scores[arm] = None
                continue
            reply = local_llm.complete_json(
                "Source document:\n---\n" + case["source"][:12000] + "\n---\n"
                f"Question: {case['question']}\n"
                f"Candidate extract:\n---\n{quote}\n---\n"
                "Score the extract: answers_question 0-2 (2 = the answer is "
                "plainly in the extract), faithful 0-2 (2 = nothing in the "
                "extract contradicts or embellishes the source). "
                'STRICT JSON {"answers_question": n, "faithful": n}.',
                system="You are a strict extract grader. JSON only.",
                url=grader_cfg["url"],
                model=grader_cfg["model"],
                max_tokens=60,
            )
            scores[arm] = {
                "answers_question": int(reply.get("answers_question", -1)),
                "faithful": int(reply.get("faithful", -1)),
            }
        graded.append({"file": case["file"], **scores})
        print(f"{case['file']}: dumb {scores['dumb']} refined {scores['refined']}")

    def total(arm: str) -> int:
        return sum(sum(g[arm].values()) for g in graded if g[arm] is not None)

    result = {
        "subject_model": args.model,
        "grader_model": args.grade_model,
        "cases": len(graded),
        "abstained": sum(1 for c in cases if c["abstained"]),
        "dumb_total": total("dumb"),
        "refined_total": total("refined"),
        "detail": graded,
    }
    print(json.dumps(result))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("latency", "quality"):
        p = sub.add_parser(name)
        p.add_argument("--url", required=True)
        p.add_argument("--model", required=True)
        if name == "quality":
            p.add_argument("--grade-url", default=None)
            p.add_argument("--grade-model", default=None)
            p.add_argument("--out", default="/tmp/m3_quality_cases.json")
    args = parser.parse_args()
    {"latency": cmd_latency, "quality": cmd_quality}[args.cmd](args)


if __name__ == "__main__":
    main()
