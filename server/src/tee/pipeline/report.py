"""Answers, not logs (A43 P1).

A produce step's answer is an artifact DIFF - which declared outputs
changed, how big they are now, what they hash to - because dumping a
build log into the conversation is the exact cost this project exists to
remove. A query step's answer is its own structured output, budgeted to
what the declaration asked for and stamped with enough provenance to be
re-derivable: which step, which argv, which inputs, when.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tee.kernel.budget import estimate_tokens
from tee.pipeline.schema import Step, substitute


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def _resolve_patterns(step: Step, values: dict[str, Any], patterns: list[str]) -> list[str]:
    """Substitute declared params into path patterns, reusing the SAME
    validation the argv path uses - a value that cannot reach argv cannot
    reach a path either."""
    if not patterns:
        return []
    probe = Step(name=step.name, kind=step.kind, argv=list(patterns), params=step.params)
    return substitute(probe, values)


def snapshot_outputs(root: Path, step: Step, values: dict[str, Any]) -> dict[str, Any]:
    """State of the declared outputs before a run."""
    state: dict[str, Any] = {}
    for pattern in _resolve_patterns(step, values, step.outputs):
        for path in _expand(root, pattern):
            key = str(path.relative_to(root))
            state[key] = {"size": path.stat().st_size, "hash": _hash_file(path)}
    return state


def _expand(root: Path, pattern: str) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        return sorted(p for p in root.glob(pattern) if p.is_file())
    candidate = root / pattern
    return [candidate] if candidate.is_file() else []


def artifact_diff(
    root: Path, step: Step, values: dict[str, Any], before: dict[str, Any]
) -> dict[str, Any]:
    """What the run actually did to the DECLARED outputs."""
    created: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    unchanged: list[str] = []
    missing: list[str] = []
    for pattern in _resolve_patterns(step, values, step.outputs):
        found = _expand(root, pattern)
        if not found:
            missing.append(pattern)
            continue
        for path in found:
            key = str(path.relative_to(root))
            now = {"size": path.stat().st_size, "hash": _hash_file(path)}
            was = before.get(key)
            if was is None:
                created.append({"path": key, **now})
            elif was["hash"] != now["hash"]:
                changed.append({"path": key, "size": now["size"], "was": was["size"]})
            else:
                unchanged.append(key)
    diff: dict[str, Any] = {}
    if created:
        diff["created"] = created
    if changed:
        diff["changed"] = changed
    if unchanged:
        diff["unchanged"] = unchanged
    if missing:
        # A produce step that did not produce what it declared is news, not
        # an error to bury: the declaration and reality disagree.
        diff["declared_but_absent"] = missing
    return diff


def query_answer(step: Step, stdout: str) -> dict[str, Any]:
    """A query step's own output, in the format it declared, budgeted."""
    budget = int(step.answer.get("max_tokens") or 400)
    fmt = str(step.answer.get("format") or "text")
    text = (stdout or "").strip()
    if fmt == "json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {
                "format": "text",
                "answer": _budget_text(text, budget),
                "note": "declared format=json but the step did not print JSON",
            }
        payload = {"format": "json", "answer": parsed}
        if estimate_tokens(payload) > budget:
            payload["answer"] = _budget_text(json.dumps(parsed, separators=(",", ":")), budget)
            payload["format"] = "text"
            payload["note"] = f"answer trimmed to the declared {budget}-token budget"
        return payload
    return {"format": "text", "answer": _budget_text(text, budget)}


def _budget_text(text: str, budget: int) -> str:
    if estimate_tokens(text) <= budget:
        return text
    keep = budget * 4  # the estimator's chars-per-token working rule
    return text[:keep].rstrip() + f"… (trimmed to the declared {budget}-token budget)"


def provenance(step: Step, argv: list[str], inputs_digest: str, started: str, wall_s: float):
    """Enough to re-derive the answer, and no more."""
    return {
        "step": step.name,
        "argv_hash": hashlib.sha256(" ".join(argv).encode()).hexdigest()[:12],
        "inputs_hash": inputs_digest,
        "started": started,
        "wall_s": wall_s,
    }


def digest_inputs(root: Path, step: Step, values: dict[str, Any]) -> str:
    """One hash over the declared inputs - the staleness test P2 builds on."""
    digest = hashlib.sha256()
    for pattern in sorted(_resolve_patterns(step, values, step.inputs)):
        for path in _expand(root, pattern):
            digest.update(str(path.relative_to(root)).encode())
            digest.update(_hash_file(path).encode())
    return digest.hexdigest()[:16]
