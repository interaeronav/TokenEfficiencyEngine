"""A42 R3: confidence calibration for the unverifiable chore (triage).

Standalone, model-dependent (the m3 pattern). The question the UCCI
lesson makes mandatory: does the model's OWN confidence field predict
correctness well enough to gate routing decisions? Measured on the
rung-1 validation set (140 labelled cases, reference confidence per
case, run VERBATIM - the cases' own system+user messages, no
re-wrapping, so the distribution matches what the adapter was
validated on; that distribution caveat rides the verdict).

The stated shipping threshold, declared before the run: a confidence
gate may ship ONLY if grounded-precision >= 0.95 AND defer-recall >=
0.95 on >= 100 cases INCLUDING out-of-generator evidence. Anything
less: the chore stays statically routed and the rows are the record.

Usage:
  uv run --project ../server python run_r3_calibration.py --url URL --model NAME
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))

from tee.kernel import local_llm  # noqa: E402
from tee.kernel.errors import TeeError  # noqa: E402

VALID = REPO / "benchmarks" / "rung1" / "data" / "valid.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    cases = [json.loads(line) for line in VALID.read_text().splitlines() if line.strip()]
    if args.limit:
        cases = cases[: args.limit]
    confusion = {"g/g": 0, "g/nv": 0, "nv/g": 0, "nv/nv": 0, "invalid": 0}
    for index, case in enumerate(cases):
        system = case["messages"][0]["content"]
        prompt = case["messages"][1]["content"]
        reference = json.loads(case["messages"][2]["content"])["confidence"]
        try:
            raw = local_llm.complete_json(
                prompt, system=system, url=args.url, model=args.model, max_tokens=220
            )
            predicted = raw.get("confidence")
        except TeeError:
            predicted = None
        if predicted not in ("grounded", "needs_verification"):
            confusion["invalid"] += 1
        else:
            key = ("g" if reference == "grounded" else "nv") + "/"
            key += "g" if predicted == "grounded" else "nv"
            confusion[key] += 1
        if (index + 1) % 20 == 0:
            print(f"{index + 1}/{len(cases)} {confusion}", flush=True)

    grounded_predictions = confusion["g/g"] + confusion["nv/g"]
    grounded_precision = confusion["g/g"] / grounded_predictions if grounded_predictions else 0.0
    defer_cases = confusion["nv/g"] + confusion["nv/nv"]
    defer_recall = confusion["nv/nv"] / defer_cases if defer_cases else 0.0
    total = sum(confusion.values())
    agreement = (confusion["g/g"] + confusion["nv/nv"]) / total if total else 0.0
    result = {
        "model": args.model,
        "cases": total,
        "confusion(ref/pred)": confusion,
        "grounded_precision": round(grounded_precision, 3),
        "defer_recall": round(defer_recall, 3),
        "agreement": round(agreement, 3),
        "threshold": "ship only if precision>=0.95 AND defer-recall>=0.95 "
        "on >=100 cases incl. out-of-generator evidence",
    }
    ships = grounded_precision >= 0.95 and defer_recall >= 0.95 and total >= 100
    result["verdict"] = (
        "threshold met ON-DISTRIBUTION ONLY - the out-of-generator condition "
        "is unmet by construction; stays static"
        if ships
        else "below threshold; stays static"
    )
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
