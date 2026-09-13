"""Numeric observations at execution boundaries; no tool payload is retained."""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import marshal
import time
from collections.abc import Callable
from typing import Any

from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.kernel.lanes import ADAPTER_ARG

_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar("learning_depth", default=0)
_VALIDATION = frozenset(
    {
        "missing_argument",
        "unknown_argument",
        "bad_argument_type",
        "bad_argument_value",
        "bad_batch",
        "bad_op",
    }
)
_REFUSED = frozenset(
    {
        "tool_disabled",
        "unknown_tool",
        "capability_denied",
        "trust_denied",
        "code_exec_disabled",
        "permission_denied",
        "trust_missing_grant",
        "refused",
        "job_refused_admission",
        "job_backpressure",
        "shutting_down",
    }
)


def _cached_version(app: Any, lane: str | None) -> str:
    if lane == ADAPTER_ARG:
        # Routed tools may serve several adapters. Conservatively invalidate
        # their aggregate execution evidence when any served version changes.
        return hashlib.sha256(
            json.dumps(
                {name: _cached_version(app, name) for name in sorted(app.adapters)}, sort_keys=True
            ).encode()
        ).hexdigest()
    adapter = app.adapters.get(lane)
    value = getattr(adapter, "_version", None)
    # Never probe an application to label bookkeeping. Only built-in scalar
    # version representations enter the hash, not an object's repr or state.
    if isinstance(value, (str, int)):
        return str(value)[:80]
    if isinstance(value, tuple) and all(isinstance(x, int) for x in value):
        return ".".join(map(str, value))
    return "unprobed"


def tool_version(app: Any, tool: Any) -> str:
    if tool is None:
        return "execution-v1-unknown"
    function = getattr(tool.handler, "__code__", None)
    code = marshal.dumps(function) if function is not None else type(tool.handler).__name__.encode()
    schema = json.dumps(tool.schema, sort_keys=True, separators=(",", ":")).encode()
    # Hash code/schema identities, never the caller's arguments or output.
    digest = hashlib.sha256(code + schema).hexdigest()[:24]
    return (
        "execution-v1-"
        + digest
        + "-"
        + hashlib.sha256(_cached_version(app, tool.lane).encode()).hexdigest()[:12]
    )


def tool_context(tool: Any) -> str:
    return "tool:" + (tool.capability if tool is not None else "unknown")


def _classification(exc: Exception) -> tuple[bool | None, str]:
    if isinstance(exc, TeeError):
        if exc.code in _REFUSED or exc.code.startswith("trust_"):
            return None, "refused"
        if "unavailable" in exc.code or "unreachable" in exc.code:
            return None, "unreachable"
        if exc.code in _VALIDATION:
            return False, "validation"
    return False, "error"


def result_outcome(result: Any) -> tuple[bool | None, str]:
    if isinstance(result, dict):
        if result.get("ok") is False or result.get("error"):
            return False, "failed"
        if result.get("job") and result.get("state") not in ("done", "error", "cancelled"):
            return None, "queued"
        if result.get("state") == "error":
            return False, "error"
        if result.get("state") == "cancelled":
            return None, "cancelled"
    return True, "completed"


def observe(
    app: Any,
    *,
    context: str,
    choice: str,
    version: Callable[[], str],
    invoke: Callable[[], Any],
) -> Any:
    """Observe one outer execution boundary; nested batch wrappers are free."""
    if _DEPTH.get():
        return invoke()
    token = _DEPTH.set(1)
    started = time.perf_counter()
    success: bool | None = None
    category = "error"
    size = None
    try:
        result = invoke()
        success, category = result_outcome(result)
        # Numeric response estimate only: never a completed-task token claim.
        try:
            size = estimate_tokens(result)
        except Exception:
            size = None  # bookkeeping cannot change the handler's return
        return result
    except Exception as exc:
        success, category = _classification(exc)
        raise
    finally:
        elapsed = (time.perf_counter() - started) * 1000
        _DEPTH.reset(token)
        # Observation is never an authority or an execution dependency.
        # The service exposes its storage health through learn_status.
        with contextlib.suppress(Exception):
            app.learning.observe(
                domain="execution",
                context=context,
                choice=choice,
                version=version(),
                success=success,
                elapsed_ms=elapsed,
                tokens=size,
                category=category,
            )


def install(app: Any) -> None:
    def virtual(tool: Any, invoke: Callable[[], Any]) -> Any:
        if tool is not None and tool.name.startswith("learn_"):
            return invoke()  # reporting/training must not recursively train itself
        return observe(
            app,
            context=tool_context(tool),
            choice=tool.name if tool is not None else "unknown",
            version=lambda: tool_version(app, tool),
            invoke=invoke,
        )

    app.registry.observer = virtual

    def completed(
        engine: str | None,
        elapsed_ms: float,
        implementation: str | None,
        success: bool | None,
        category: str,
    ) -> None:
        from tee.kernel.machine import ENGINES

        choice = engine if engine in ENGINES else "other"
        app.learning.observe(
            domain="execution",
            context="job",
            choice=choice,
            version="job-v1-"
            + hashlib.sha256(
                ((implementation or "unidentified") + _cached_version(app, ADAPTER_ARG)).encode()
            ).hexdigest(),
            success=success if implementation else None,
            elapsed_ms=elapsed_ms,
            category=category if implementation else "unknown",
        )

    app.jobs.completion_observer = completed
