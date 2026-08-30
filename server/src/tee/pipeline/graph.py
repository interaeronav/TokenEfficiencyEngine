"""Staleness and the DAG (A43 P2): make, but declared, budgeted and honest.

Steps form a graph through what they declare: if step B reads a path step
A writes, B depends on A. Nobody writes that edge - it falls out of the
declaration, which is the whole reason declaring inputs and outputs was
worth the ceremony.

A run asks for a TARGET. TEE hashes the declared inputs, compares them
against the recorded manifest of the last successful run, and executes
only what is stale - reporting every skip WITH ITS REASON, because a
build that silently does nothing is indistinguishable from a build that
silently did the wrong thing. `force` runs anyway and says so in the
report rather than quietly pretending freshness never mattered.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.pipeline import report
from tee.pipeline.schema import Pipeline, Step

MANIFEST = "pipeline-runs.json"


def manifest_path(root: Path) -> Path:
    return Path(root) / ".tee" / MANIFEST


def load_manifest(root: Path) -> dict[str, Any]:
    try:
        return json.loads(manifest_path(root).read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def record_run(
    root: Path,
    step: Step,
    inputs_hash: str,
    argv_hash: str,
    answer: dict[str, Any] | None = None,
) -> None:
    """Only a SUCCESSFUL run is recorded - a failed step stays stale, so a
    retry actually retries.

    A query's answer is recorded WITH the run, because a query has no
    artifact on disk to be fresh about: without this a fresh query would
    be skipped and the caller would get 'nothing to do' in place of the
    answer they asked for. Storing it means an unchanged question is
    answered for free instead of re-run - the whole point of the lane."""
    data = load_manifest(root)
    record: dict[str, Any] = {"inputs_hash": inputs_hash, "argv_hash": argv_hash}
    if answer is not None:
        record["answer"] = answer
        record["answered_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    data[step.name] = record
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(path)


def _safe_patterns(step: Step, values: dict[str, Any], patterns: list[str]) -> list[str]:
    """Resolve a step's declared paths, tolerating steps this run cannot
    parameterise. A step whose outputs need a param we were not given
    simply cannot be part of THIS run's graph - that is an absence, not an
    error, and raising here would make one step's params everyone's
    problem."""
    try:
        return report._resolve_patterns(step, values, patterns)
    except TeeError:
        return []


def _produced_by(pipeline: Pipeline, values: dict[str, Any]) -> dict[str, str]:
    """Which step declares each output path (after param substitution)."""
    owners: dict[str, str] = {}
    for step in pipeline.steps.values():
        for pattern in _safe_patterns(step, values, step.outputs):
            owners[pattern] = step.name
    return owners


def dependencies(pipeline: Pipeline, values: dict[str, Any]) -> dict[str, set[str]]:
    """step -> the steps it depends on, derived from the declarations."""
    owners = _produced_by(pipeline, values)
    edges: dict[str, set[str]] = {name: set() for name in pipeline.steps}
    for step in pipeline.steps.values():
        for pattern in _safe_patterns(step, values, step.inputs):
            producer = owners.get(pattern)
            if producer and producer != step.name:
                edges[step.name].add(producer)
    return edges


def order(pipeline: Pipeline, target: str, values: dict[str, Any]) -> list[Step]:
    """Dependency order for a target, cycles refused by name."""
    edges = dependencies(pipeline, values)
    resolved: list[str] = []
    visiting: set[str] = set()

    def visit(name: str, trail: tuple[str, ...]) -> None:
        if name in resolved:
            return
        if name in visiting:
            cycle = " -> ".join([*trail, name])
            raise TeeError(
                "pipeline_cycle",
                f"The declared steps form a cycle: {cycle}.",
                fix="A step cannot depend on its own output; break the loop in .tee/pipeline.toml.",
            )
        visiting.add(name)
        for parent in sorted(edges.get(name, ())):
            visit(parent, (*trail, name))
        visiting.discard(name)
        resolved.append(name)

    visit(target, ())
    return [pipeline.steps[name] for name in resolved]


def staleness(
    root: Path, step: Step, values: dict[str, Any], manifest: dict[str, Any]
) -> str | None:
    """Why this step must run, or None when it is genuinely fresh."""
    record = manifest.get(step.name)
    if not isinstance(record, dict):
        return "never run here"
    inputs_hash = report.digest_inputs(root, step, values)
    if record.get("inputs_hash") != inputs_hash:
        return "declared inputs changed"
    if step.kind == "produce":
        for pattern in report._resolve_patterns(step, values, step.outputs):
            if not report._expand(Path(root), pattern):
                return f"declared output missing: {pattern}"
    else:
        # A query with no declared inputs has nothing to be fresh ABOUT.
        if not step.inputs:
            return "query step with no declared inputs (nothing to be fresh about)"
        # ...and one whose answer was never stored has nothing to serve.
        if not isinstance(record.get("answer"), dict):
            return "no cached answer for this question"
    return None


def plan(
    root: Path,
    pipeline: Pipeline,
    target: str,
    values: dict[str, Any],
    *,
    force: bool = False,
) -> tuple[list[Step], list[dict[str, str]]]:
    """(steps to run, skips with reasons)."""
    manifest = load_manifest(Path(root))
    edges = dependencies(pipeline, values)
    to_run: list[Step] = []
    skipped: list[dict[str, str]] = []
    scheduled: set[str] = set()
    for step in order(pipeline, target, values):
        if force:
            to_run.append(step)
            scheduled.add(step.name)
            continue
        reason = staleness(Path(root), step, values, manifest)
        if reason is None:
            # A step whose own inputs are unchanged is STILL stale when an
            # upstream step is about to rewrite them - freshness measured
            # before the build would otherwise skip every dependent.
            rebuilt = sorted(edges.get(step.name, set()) & scheduled)
            if rebuilt:
                reason = f"dependency rebuilt: {', '.join(rebuilt)}"
        if reason is None:
            skipped.append({"step": step.name, "reason": "fresh"})
        else:
            to_run.append(step)
            scheduled.add(step.name)
    return to_run, skipped


def cached_answer(root: Path, step: Step) -> dict[str, Any] | None:
    """The answer a fresh query step last gave, if one was recorded."""
    record = load_manifest(root).get(step.name)
    if not isinstance(record, dict):
        return None
    answer = record.get("answer")
    if not isinstance(answer, dict):
        return None
    return {**answer, "answered_at": record.get("answered_at")}
