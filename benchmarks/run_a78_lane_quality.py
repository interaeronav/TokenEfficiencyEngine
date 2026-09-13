"""A78: immutable local-model plans plus independently supplied live readback.

Generation never touches an app. Preflight is syntax evidence only. grade()
requires live observations and preservation evidence; escalation is not success.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
# E402: these must follow the sys.path insert above, which is what makes them
# resolvable when this script runs from a checkout rather than an install.
from tee.kernel import local_llm  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.kernel.errors import TeeError  # noqa: E402

FIXTURE = REPO / "benchmarks" / "fixtures" / "a78_lane_quality.json"


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def load_suite(path: Path = FIXTURE) -> dict:
    return json.loads(path.read_text())


def schema_grade(answer: object) -> dict:
    """Shape and honest pre-execution status, never a geometry verdict."""
    issues = []
    if not isinstance(answer, dict):
        return {"valid": False, "issues": ["answer is not an object"]}
    ops = answer.get("ops")
    if not isinstance(ops, list) or not ops:
        issues.append("ops is absent, empty or not a list")
    elif not all(isinstance(op, dict) and isinstance(op.get("op"), str) for op in ops):
        issues.append("each operation needs a string op")
    if not isinstance(answer.get("verification"), list) or not answer["verification"]:
        issues.append("planned verification is absent")
    claims = answer.get("claims")
    if (
        not isinstance(claims, dict)
        or claims.get("executed") is not False
        or claims.get("validated") is not False
    ):
        issues.append("must not claim execution or validation before app readback")
    if answer.get("abstention"):
        issues.append("model abstained")
    return {"valid": not issues, "issues": issues}


def preflight(adapter_name: str, answer: dict) -> dict:
    """Current host validator only; no app/bridge, and no success implication."""
    shape = schema_grade(answer)
    if not shape["valid"]:
        return {"valid": False, "kind": "shape_only", "issues": shape["issues"]}
    try:
        if adapter_name == "blender":
            from tee.adapters.blender.codegen import check_batch
        elif adapter_name == "fusion":
            from tee.adapters.fusion.codegen import check_batch
        else:
            raise ValueError("unknown adapter")
        check_batch(answer["ops"])
    except (TeeError, ValueError, TypeError, KeyError) as exc:
        return {
            "valid": False,
            "kind": "shape_only",
            "code": getattr(exc, "code", type(exc).__name__),
            "issues": [str(exc)[:600]],
        }
    return {"valid": True, "kind": "shape_only", "issues": []}


def _near(actual: object, expected: object, tolerance: float) -> bool:
    if isinstance(expected, bool):
        return actual is expected
    if isinstance(expected, (int, float)):
        return (
            not isinstance(actual, bool)
            and isinstance(actual, (int, float))
            and math.isfinite(actual)
            and abs(actual - expected) <= tolerance
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(_near(a, e, tolerance) for a, e in zip(actual, expected, strict=False))
        )
    return actual == expected


def grade(task: dict, record: dict, evidence: dict | None) -> dict:
    """Grade facts measured by a separate live harness, not answer assertions.

    evidence = {source:'live_blender'|'live_fusion', status:'executed',
      observations:{...expected keys...}, preservation:{before:hash,after:hash}}
    Execution errors, escalations, skips and absent evidence always fail.
    """
    checks = {"answer_schema": schema_grade(record.get("answer"))["valid"]}
    ev = evidence or {}
    checks["live_execution"] = (
        ev.get("source") == f"live_{task['adapter']}"
        and ev.get("status") == "executed"
        and not ev.get("error")
    )
    preserved = ev.get("preservation") or {}
    checks["protected_state_preserved"] = (
        isinstance(preserved.get("before"), str)
        and bool(preserved["before"])
        and preserved["before"] == preserved.get("after")
    )
    checks["no_escalation"] = not bool(record.get("escalated") or ev.get("escalated"))
    expected = dict(task["expected"])
    tolerances = dict(task.get("tolerances", {}))
    if task["id"] == "fu_plate":
        # The already-frozen brief specifies the corner coordinates as well as
        # dimensions. Tighten its independent grading without editing the
        # fixture/model prompt or substituting geometry into a model answer.
        expected.update({"bbox_min_mm": [20, 25, 0], "bbox_max_mm": [157, 108, 7]})
        tolerances.update({"bbox_min_mm": 0.001, "bbox_max_mm": 0.001})
    if "volume_formula" in task:
        f = task["volume_formula"]
        expected["volume_mm3"] = (
            f["width"] * f["height"] - math.pi * (f["hole_diameter"] / 2) ** 2
        ) * f["depth"]
        tolerances["volume_mm3"] = 0.1
    observations = ev.get("observations") or {}
    for key, value in expected.items():
        checks[key] = key in observations and _near(
            observations[key], value, tolerances.get(key, 0)
        )
    return {
        "task": task["id"],
        "success": all(checks.values()),
        "checks": checks,
        "failed": [key for key, passed in checks.items() if not passed],
        "basis": "independent_live_readback",
        "missing_evidence": not bool(evidence),
    }


def _guide(task: dict) -> dict:
    if task["adapter"] == "blender":
        from tee.adapters.blender.guidance import guide
    else:
        from tee.adapters.fusion.guidance import guide
    return guide(task["topic"])


def generate(args: argparse.Namespace) -> None:
    if urlparse(args.url).hostname not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("This benchmark only calls an explicitly selected loopback model.")
    suite = load_suite(args.fixtures)
    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    selected = [t for t in suite["tasks"] if not args.only or t["id"] in args.only]
    fixture_sha = digest(args.fixtures.read_bytes())
    meta_path = output / "manifest.json"
    if meta_path.exists():
        manifest = json.loads(meta_path.read_text())
        if (
            manifest["fixture_sha256"] != fixture_sha
            or manifest["arm"] != args.arm
            or manifest["model_requested"] != args.model
            or manifest["endpoint"] != args.url
            or manifest["max_tokens"] != args.max_tokens
        ):
            raise SystemExit("Existing generation directory has a different frozen experiment.")
    else:
        manifest = {
            "arm": args.arm,
            "fixture_sha256": fixture_sha,
            "fixture_path": str(args.fixtures),
            "model_requested": args.model,
            "endpoint": args.url,
            "max_tokens": args.max_tokens,
            "temperature": 0,
            "inference": "thinking_disabled",
            "cases": [t["id"] for t in suite["tasks"]],
            "claim": (
                "single-turn local model plan generation; no app execution or model parity claim"
            ),
            "baseline_context_sha256": digest(suite["baseline_context"]),
        }
        meta_path.write_text(json.dumps(manifest, indent=2))
    for task in selected:
        path = output / f"{task['id']}.json"
        if path.exists():
            print(
                json.dumps({"task": task["id"], "status": "preserved_existing"}),
                flush=True,
            )
            continue
        guide = _guide(task) if args.arm == "guided" else None
        system = suite["baseline_context"]
        if guide:
            system += "\n\nCurrent verified lane guide:\n" + json.dumps(
                guide, separators=(",", ":")
            )
        calls = []

        def usage(payload: dict, bytes_sent: int, seconds: float, calls=calls) -> None:
            calls.append(
                {
                    "provider_usage": payload.get("usage"),
                    "model_returned": payload.get("model"),
                    "bytes_sent": bytes_sent,
                    "seconds": seconds,
                    "finish_reasons": [c.get("finish_reason") for c in payload.get("choices", [])],
                }
            )

        started = time.monotonic()
        error = None
        raw = ""
        answer = None
        try:
            raw = local_llm.complete(
                task["prompt"],
                system=system,
                url=args.url,
                model=args.model,
                max_tokens=args.max_tokens,
                adapters=None,
                response_format={"type": "json_object"},
                timeout=args.timeout,
                on_usage=usage,
            )
            answer = local_llm._parse_json_object(raw)
            if answer is None:
                error = "invalid_json"
        except (TeeError, ValueError, TypeError, KeyError) as exc:
            error = f"{getattr(exc, 'code', type(exc).__name__)}: {str(exc)[:400]}"
        record = {
            "task": task["id"],
            "arm": args.arm,
            "fixture_sha256": fixture_sha,
            "system": system,
            "prompt": task["prompt"],
            "system_sha256": digest(system),
            "prompt_sha256": digest(task["prompt"]),
            "guide": guide,
            "raw_answer": raw,
            "answer": answer,
            "error": error,
            "wall_seconds": time.monotonic() - started,
            "usage_calls": calls,
            "estimated_context_tokens": estimate_tokens(system) + estimate_tokens(task["prompt"]),
            "estimated_answer_tokens": estimate_tokens(raw),
            "escalated": False,
            "schema": schema_grade(answer),
            "geometry_status": "not_executed",
        }
        # Exclusive create means an accidental repeated run cannot erase a failure.
        with path.open("x") as handle:
            json.dump(record, handle, indent=2)
        print(
            json.dumps(
                {
                    "task": task["id"],
                    "arm": args.arm,
                    "schema": record["schema"],
                    "wall_s": round(record["wall_seconds"], 2),
                    "error": error,
                    "provider_usage": [c["provider_usage"] for c in calls],
                }
            ),
            flush=True,
        )
        if error and error.startswith(("llm_failed:", "llm_unreachable:")):
            # A wrong route or dead endpoint is infrastructure, not six failed
            # model tasks. Keep its evidence and stop before repeating it.
            break


def grade_directory(args: argparse.Namespace) -> None:
    rows = []
    for task in load_suite(args.fixtures)["tasks"]:
        answer_path = args.answers / f"{task['id']}.json"
        evidence_path = args.evidence / f"{task['id']}.json"
        record = json.loads(answer_path.read_text()) if answer_path.exists() else {}
        ev = json.loads(evidence_path.read_text()) if evidence_path.exists() else None
        rows.append(grade(task, record, ev))
    report = {
        "tasks": len(rows),
        "completed": sum(r["success"] for r in rows),
        "rows": rows,
        "note": "No evidence, skips and escalations never count as completed.",
    }
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({"tasks": report["tasks"], "completed": report["completed"]}))


def summarize_generation(directory: Path) -> dict:
    """Keep provider usage separate from TEE's character-based estimator."""
    records = [
        json.loads(path.read_text())
        for path in sorted(directory.glob("*.json"))
        if path.name != "manifest.json"
    ]
    records = [record for record in records if "usage_calls" in record]
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    cached_total = 0
    known = 0
    unknown = 0
    cached_unknown = 0
    for record in records:
        for call in record["usage_calls"]:
            usage = call.get("provider_usage")
            if not isinstance(usage, dict) or not all(key in usage for key in totals):
                unknown += 1
                continue
            known += 1
            for key in totals:
                totals[key] += usage[key]
            cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
            if cached is None:
                cached_unknown += 1
            else:
                cached_total += cached
    return {
        "case_records": len(records),
        "schema_valid": sum(record["schema"]["valid"] for record in records),
        "generation_errors": sum(bool(record["error"]) for record in records),
        "wall_seconds": sum(record["wall_seconds"] for record in records),
        "provider_usage_known_calls": known,
        "provider_usage_unknown_calls": unknown,
        "provider_reported_totals": totals if known else None,
        "provider_cached_prompt_tokens": cached_total if known and not cached_unknown else None,
        "estimated_context_tokens": sum(record["estimated_context_tokens"] for record in records),
        "estimated_answer_tokens": sum(record["estimated_answer_tokens"] for record in records),
        "geometry_successes": None,
        "note": (
            "Generation totals only; schema validity is not task completion. "
            "Cached prompt tokens are a subset of prompt tokens."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--arm", choices=["baseline", "guided"], required=True)
    gen.add_argument("--url", required=True)
    gen.add_argument("--model", required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--max-tokens", type=int, default=1800)
    gen.add_argument("--timeout", type=float, default=120)
    gen.add_argument("--only", nargs="*")
    gen.add_argument("--fixtures", type=Path, default=FIXTURE)
    gen.set_defaults(func=generate)
    grader = sub.add_parser("grade")
    grader.add_argument("--answers", type=Path, required=True)
    grader.add_argument("--evidence", type=Path, required=True)
    grader.add_argument("--out", type=Path, required=True)
    grader.add_argument("--fixtures", type=Path, default=FIXTURE)
    grader.set_defaults(func=grade_directory)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
